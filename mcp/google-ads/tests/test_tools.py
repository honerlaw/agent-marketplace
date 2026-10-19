"""The request tool, exercised end to end through an in-process MCP client."""

import json
from dataclasses import replace

import httpx2
import pytest
from mcp import Client

from google_ads_mcp.config import Settings
from google_ads_mcp.server import build_server
from tests.conftest import API_HOST, FakeCredentials, FakeGoogleAds, call, error_text

pytestmark = pytest.mark.anyio

TOOLS = {
    "google_ads_request",
    "google_ads_list_endpoints",
    "google_ads_describe_endpoint",
    "google_ads_describe_schema",
}
SEARCH = "/customers/1234567890/googleAds:search"


async def test_four_tools_are_listed(settings: Settings, fake: FakeGoogleAds) -> None:
    async with Client(build_server(settings, fake.transport, FakeCredentials)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == TOOLS


async def test_a_search_goes_to_google_with_the_token(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    body = {"query": "SELECT campaign.id FROM campaign", "pageSize": 100}
    arguments = {"method": "POST", "path": SEARCH, "body": body}
    result = await call(settings, fake, "google_ads_request", arguments)
    assert result.structured_content == {
        "status": 200,
        "headers": {"content-type": "application/json", "request-id": "req-1"},
        "json": {},
    }
    sent = fake.last
    assert (sent.method, sent.url.scheme, sent.url.host) == ("POST", "https", API_HOST)
    assert sent.url.path == f"/v26{SEARCH}"
    assert sent.headers["authorization"] == "Bearer token-1"
    assert sent.headers["user-agent"].startswith("google-ads-mcp/")
    assert "login-customer-id" not in sent.headers
    assert json.loads(sent.content) == body


async def test_the_configured_manager_id_is_sent(settings: Settings, fake: FakeGoogleAds) -> None:
    managed = replace(settings, login_customer_id="1112223333")
    await call(managed, fake, "google_ads_request", {"method": "GET", "path": "/customers/1"})
    assert fake.last.headers["login-customer-id"] == "1112223333"


async def test_a_caller_manager_id_replaces_the_default(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    managed = replace(settings, login_customer_id="1112223333")
    headers = {"Login-Customer-Id": "444-555-6666", "Linked-Customer-Id": "7-8"}
    arguments = {"method": "GET", "path": "/customers/1", "headers": headers}
    await call(managed, fake, "google_ads_request", arguments)
    sent = fake.last.headers
    assert (sent["login-customer-id"], sent["linked-customer-id"]) == ("4445556666", "78")
    assert sent.get_list("login-customer-id") == ["4445556666"]


async def test_query_parameters_are_sent(settings: Settings, fake: FakeGoogleAds) -> None:
    arguments = {"method": "GET", "path": "/customers:listAccessibleCustomers", "query": {"a": 1}}
    await call(settings, fake, "google_ads_request", arguments)
    assert fake.last.url.params["a"] == "1"


@pytest.mark.parametrize(
    "arguments",
    [
        {"method": "GET", "path": "https://evil.test/customers"},
        {"method": "GET", "path": "/customers", "headers": {"Authorization": "Bearer x"}},
        {"method": "GET", "path": "/customers", "headers": {"login-customer-id": "boss"}},
    ],
)
async def test_unsafe_requests_never_reach_the_network(
    settings: Settings, fake: FakeGoogleAds, arguments: dict[str, object]
) -> None:
    result = await call(settings, fake, "google_ads_request", arguments)
    assert result.is_error
    assert fake.requests == []


async def test_google_errors_are_returned_as_results(settings: Settings) -> None:
    error = {"error": {"code": 403, "status": "PERMISSION_DENIED"}}
    fake = FakeGoogleAds(handler=lambda _request: httpx2.Response(403, json=error))
    result = await call(settings, fake, "google_ads_request", {"method": "POST", "path": SEARCH})
    assert result.structured_content == {
        "status": 403,
        "headers": {"content-type": "application/json"},
        "json": error,
    }


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (httpx2.Response(200, text="plain"), {"text": "plain"}),
        (
            httpx2.Response(200, text="{oops", headers={"content-type": "application/json"}),
            {"json": "{oops"},
        ),
    ],
)
async def test_non_json_bodies_come_back_as_text(
    settings: Settings, response: httpx2.Response, expected: dict[str, object]
) -> None:
    fake = FakeGoogleAds(handler=lambda _request: response)
    result = await call(settings, fake, "google_ads_request", {"method": "GET", "path": "/x"})
    assert result.structured_content is not None
    assert {key: result.structured_content[key] for key in expected} == expected


async def test_an_oversized_response_is_refused_not_truncated(settings: Settings) -> None:
    small = replace(settings, max_response_bytes=10)
    fake = FakeGoogleAds(handler=lambda _request: httpx2.Response(200, json={"rows": "x" * 50}))
    result = await call(small, fake, "google_ads_request", {"method": "POST", "path": SEARCH})
    message = error_text(result)
    assert "larger than 10 bytes" in message
    assert "googleAds:search" in message


async def test_a_response_at_the_limit_is_returned(settings: Settings) -> None:
    exact = replace(settings, max_response_bytes=len(b'{"a":1}'))
    fake = FakeGoogleAds(handler=lambda _request: httpx2.Response(200, json={"a": 1}))
    result = await call(exact, fake, "google_ads_request", {"method": "GET", "path": "/x"})
    assert result.structured_content is not None
    assert result.structured_content["json"] == {"a": 1}


async def test_a_network_failure_becomes_a_tool_error(settings: Settings) -> None:
    def fail(request: httpx2.Request) -> httpx2.Response:
        message = "connection refused"
        raise httpx2.ConnectError(message, request=request)

    fake = FakeGoogleAds(handler=fail)
    result = await call(settings, fake, "google_ads_request", {"method": "GET", "path": "/x"})
    assert "request to the Google Ads API failed: ConnectError" in error_text(result)
