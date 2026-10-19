"""The API tools, exercised end to end through an in-process MCP client."""

import json
from dataclasses import replace
from urllib.parse import parse_qsl

import httpx2
import pytest
from mcp import Client

from meta_ads_mcp.config import Settings
from meta_ads_mcp.server import build_server
from tests.conftest import (
    APP_ID,
    APP_SECRET,
    FIXTURE_HASH,
    GRAPH_HOST,
    PROOF,
    TOKEN,
    FakeGraph,
    call,
    error_text,
)

pytestmark = pytest.mark.anyio

TOOLS = {
    "meta_ads_request",
    "meta_ads_follow_page",
    "meta_ads_token_status",
    "meta_ads_list_endpoints",
    "meta_ads_describe_endpoint",
    "meta_ads_describe_type",
}


def query_of(request: httpx2.Request) -> list[tuple[str, str]]:
    """Return the request's query as ordered pairs."""
    return parse_qsl(request.url.query.decode(), keep_blank_values=True)


async def test_six_tools_and_the_spend_warning(settings: Settings, fake: FakeGraph) -> None:
    async with Client(build_server(settings, fake.transport, FIXTURE_HASH)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == TOOLS
    request_tool = next(tool for tool in listed.tools if tool.name == "meta_ads_request")
    description = request_tool.description or ""
    assert "SPEND REAL MONEY" in description
    assert '"status": "PAUSED"' in description
    assert "headers" not in request_tool.input_schema["properties"]


async def test_a_read_goes_to_graph_with_the_token_in_the_header(
    settings: Settings, fake: FakeGraph
) -> None:
    arguments = {
        "method": "GET",
        "path": "/act_1/campaigns",
        "query": {"fields": "name,status", "limit": 2, "effective_status": ["ACTIVE", "PAUSED"]},
    }
    result = await call(settings, fake, "meta_ads_request", arguments)
    assert result.structured_content == {
        "status": 200,
        "headers": {"content-type": "application/json", "x-fb-trace-id": "trace-1"},
        "json": {},
    }
    request = fake.last
    assert (request.method, request.url.host, request.url.path) == (
        "GET",
        GRAPH_HOST,
        "/v26.0/act_1/campaigns",
    )
    assert request.headers["authorization"] == f"Bearer {TOKEN}"
    assert query_of(request) == [
        ("fields", "name,status"),
        ("limit", "2"),
        ("effective_status", "ACTIVE"),
        ("effective_status", "PAUSED"),
        ("appsecret_proof", PROOF),
    ]
    assert TOKEN not in str(request.url)


async def test_without_an_app_secret_no_proof_is_sent(settings: Settings, fake: FakeGraph) -> None:
    plain = replace(settings, app_id=None, app_secret=None)
    await call(plain, fake, "meta_ads_request", {"method": "GET", "path": "/me"})
    assert query_of(fake.last) == []


async def test_a_json_write(settings: Settings, fake: FakeGraph) -> None:
    body = {"name": "Launch", "objective": "OUTCOME_TRAFFIC", "status": "PAUSED", "flag": True}
    arguments = {"method": "POST", "path": "/act_1/campaigns", "body": body}
    await call(settings, fake, "meta_ads_request", arguments)
    assert fake.last.headers["content-type"] == "application/json"
    assert json.loads(fake.last.content) == body


async def test_a_form_write_json_encodes_nested_values(settings: Settings, fake: FakeGraph) -> None:
    body = {
        "name": "Set",
        "targeting": {"geo_locations": {"countries": ["US"]}},
        "daily_budget": 500,
    }
    arguments = {"method": "POST", "path": "/act_1/adsets", "body": body, "body_format": "form"}
    await call(settings, fake, "meta_ads_request", arguments)
    assert fake.last.headers["content-type"] == "application/x-www-form-urlencoded"
    assert dict(parse_qsl(fake.last.content.decode())) == {
        "name": "Set",
        "targeting": '{"geo_locations": {"countries": ["US"]}}',
        "daily_budget": "500",
    }


async def test_query_booleans_are_lowercase(settings: Settings, fake: FakeGraph) -> None:
    arguments = {"method": "DELETE", "path": "/123", "query": {"async": True, "x": False}}
    await call(settings, fake, "meta_ads_request", arguments)
    assert query_of(fake.last)[:2] == [("async", "true"), ("x", "false")]


@pytest.mark.parametrize("where", ["query", "body"])
@pytest.mark.parametrize("name", ["access_token", "Batch", "method", "callback[0]"])
async def test_refused_parameters_are_refused_in_query_and_body(
    settings: Settings, fake: FakeGraph, where: str, name: str
) -> None:
    arguments = {"method": "POST", "path": "/act_1/campaigns", where: {name: "x"}}
    result = await call(settings, fake, "meta_ads_request", arguments)
    assert "may not set" in error_text(result)
    assert fake.requests == []


async def test_nested_keys_ids_and_include_headers_pass(
    settings: Settings, fake: FakeGraph
) -> None:
    arguments = {
        "method": "GET",
        "path": "/act_1",
        "query": {"ids": "1,2", "include_headers": "false"},
        "body": None,
    }
    result = await call(settings, fake, "meta_ads_request", arguments)
    assert not result.is_error
    nested = {"method": "POST", "path": "/act_1/adsets", "body": {"fields": {"access_token": 1}}}
    assert not (await call(settings, fake, "meta_ads_request", nested)).is_error


async def test_a_bad_path_never_reaches_meta(settings: Settings, fake: FakeGraph) -> None:
    result = await call(settings, fake, "meta_ads_request", {"method": "POST", "path": "/"})
    assert "batch requests are not supported" in error_text(result)
    assert fake.requests == []


async def test_no_token_is_a_clear_error(settings: Settings, fake: FakeGraph) -> None:
    empty = replace(settings, access_token=None, app_id=None, app_secret=None)
    result = await call(empty, fake, "meta_ads_request", {"method": "GET", "path": "/me"})
    assert "META_ADS_ACCESS_TOKEN is not set" in error_text(result)


async def test_errors_and_text_bodies_pass_through(settings: Settings) -> None:
    def answer(request: httpx2.Request) -> httpx2.Response:
        if request.url.path.endswith("/error"):
            error = {"error": {"message": "Invalid parameter", "code": 100}}
            return httpx2.Response(400, json=error)
        return httpx2.Response(200, text="plain", headers={"content-type": "text/plain"})

    fake = FakeGraph(answer)
    failed = await call(settings, fake, "meta_ads_request", {"method": "GET", "path": "/error"})
    assert failed.structured_content is not None
    assert failed.structured_content["status"] == 400
    assert failed.structured_content["json"]["error"]["code"] == 100
    text = await call(settings, fake, "meta_ads_request", {"method": "GET", "path": "/text"})
    assert text.structured_content is not None
    assert text.structured_content["text"] == "plain"


async def test_a_body_that_is_not_json_comes_back_as_text(settings: Settings) -> None:
    fake = FakeGraph(lambda _r: httpx2.Response(200, text="{bad", headers={"content-type": "json"}))
    result = await call(settings, fake, "meta_ads_request", {"method": "GET", "path": "/me"})
    assert result.structured_content is not None
    assert result.structured_content["json"] == "{bad"


async def test_an_oversized_response_is_refused(settings: Settings) -> None:
    fake = FakeGraph(lambda _r: httpx2.Response(200, json={"data": "x" * 200}))
    small = replace(settings, max_response_bytes=100)
    result = await call(small, fake, "meta_ads_request", {"method": "GET", "path": "/me"})
    assert "META_ADS_MAX_RESPONSE_BYTES" in error_text(result)


async def test_follow_page_re_adds_credentials(settings: Settings, fake: FakeGraph) -> None:
    url = "https://graph.facebook.com/v26.0/act_1/campaigns?limit=2&after=abc"
    await call(settings, fake, "meta_ads_follow_page", {"url": url})
    assert fake.last.url.path == "/v26.0/act_1/campaigns"
    assert query_of(fake.last) == [("limit", "2"), ("after", "abc"), ("appsecret_proof", PROOF)]
    assert fake.last.headers["authorization"] == f"Bearer {TOKEN}"


async def test_follow_page_refuses_another_host(settings: Settings, fake: FakeGraph) -> None:
    url = "https://evil.example/v26.0/act_1/campaigns"
    result = await call(settings, fake, "meta_ads_follow_page", {"url": url})
    assert "Graph pagination URL" in error_text(result)
    assert fake.requests == []


async def test_token_status_reports_expiry_without_the_token(settings: Settings) -> None:
    data = {
        "data": {
            "is_valid": True,
            "type": "SYSTEM_USER",
            "app_id": APP_ID,
            "expires_at": 0,
            "data_access_expires_at": 1_800_000_000,
            "scopes": ["ads_management"],
            "granular_scopes": [{"scope": "ads_management", "target_ids": ["1"]}],
            "user_id": "42",
        }
    }
    fake = FakeGraph(lambda _r: httpx2.Response(200, json=data))
    result = await call(settings, fake, "meta_ads_token_status", {})
    assert result.structured_content == {
        "available": True,
        "is_valid": True,
        "type": "SYSTEM_USER",
        "app_id": APP_ID,
        "scopes": ["ads_management"],
        "granular_scopes": [{"scope": "ads_management", "target_ids": ["1"]}],
        "expires_at": "never",
        "data_access_expires_at": "2027-01-15T08:00:00+00:00",
    }
    request = fake.last
    assert request.url.path == "/v26.0/debug_token"
    assert request.headers["authorization"] == f"Bearer {APP_ID}|{APP_SECRET}"
    assert query_of(request) == [("input_token", TOKEN)]


async def test_token_status_passes_an_unexpected_answer_through(settings: Settings) -> None:
    error = {"error": {"message": "bad app token"}}
    fake = FakeGraph(lambda _r: httpx2.Response(400, json=error))
    result = await call(settings, fake, "meta_ads_token_status", {})
    assert result.structured_content == {"available": True, "status": 400, "response": error}


async def test_token_status_keeps_an_unusual_timestamp(settings: Settings) -> None:
    fake = FakeGraph(lambda _r: httpx2.Response(200, json={"data": {"expires_at": "soon"}}))
    result = await call(settings, fake, "meta_ads_token_status", {})
    assert result.structured_content == {"available": True, "expires_at": "soon"}


async def test_token_status_without_app_credentials(settings: Settings, fake: FakeGraph) -> None:
    plain = replace(settings, app_id=None, app_secret=None)
    result = await call(plain, fake, "meta_ads_token_status", {})
    assert result.structured_content == {
        "available": False,
        "reason": "set META_APP_ID and META_APP_SECRET to inspect the token",
    }
    assert fake.requests == []
