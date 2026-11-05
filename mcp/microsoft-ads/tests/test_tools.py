"""The request tool: operation-name dispatch, identity headers, retries and limits."""

import json
from collections.abc import AsyncIterator
from dataclasses import replace

import anyio
import httpx2
import pytest
from mcp import Client

from microsoft_ads_mcp.api import ApiRequest, MicrosoftAdsApi
from microsoft_ads_mcp.auth import FRESH_SECONDS
from microsoft_ads_mcp.catalog import OperationCatalog, load_catalog
from microsoft_ads_mcp.config import Credentials, Settings
from microsoft_ads_mcp.server import build_server
from tests.conftest import (
    DEVELOPER_TOKEN,
    ISSUED_ACCESS,
    TOKEN_HOST,
    Clock,
    FakeMicrosoft,
    call,
    error_text,
    structured,
)

pytestmark = pytest.mark.anyio

REQUEST = "microsoft_ads_request"
HOSTS = {
    "AddCampaigns": "campaign",
    "DownloadCampaignsByAccountIds": "bulk",
    "SubmitGenerateReport": "reporting",
    "GetKeywordIdeas": "adinsight",
    "GetUser": "clientcenter",
    "SearchInsertionOrders": "clientcenter",
}


@pytest.mark.parametrize(("operation", "label"), sorted(HOSTS.items()))
@pytest.mark.parametrize("environment", ["production", "sandbox"])
async def test_each_operation_goes_to_its_service_host(
    settings: Settings, fake: FakeMicrosoft, operation: str, label: str, environment: str
) -> None:
    configured = replace(settings, environment=environment)
    await call(configured, fake, REQUEST, {"operation": operation, "body": {}})
    sandbox = ".sandbox" if environment == "sandbox" else ""
    assert fake.last.url.scheme == "https"
    assert fake.last.url.host == f"{label}.api{sandbox}.bingads.microsoft.com"


async def test_method_and_path_come_from_the_catalog(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    body = {"AccountId": "222", "Campaigns": [{"Name": "Spring", "Status": "Paused"}]}
    result = await call(settings, fake, REQUEST, {"operation": "AddCampaigns", "body": body})
    assert fake.last.method == "POST"
    assert fake.last.url.path == "/CampaignManagement/v13/Campaigns"
    assert json.loads(fake.last.content) == body
    assert structured(result) == {
        "status": 200,
        "tracking_id": "track-1",
        "json": {"TrackingId": "track-1"},
    }


async def test_a_delete_carries_its_json_body(settings: Settings, fake: FakeMicrosoft) -> None:
    body = {"AccountId": "222", "CampaignIds": ["9"]}
    await call(settings, fake, REQUEST, {"operation": "DeleteCampaigns", "body": body})
    assert fake.last.method == "DELETE"
    assert json.loads(fake.last.content) == body


async def test_no_body_sends_an_empty_object(settings: Settings, fake: FakeMicrosoft) -> None:
    await call(settings, fake, REQUEST, {"operation": "GetCurrentUser"})
    assert json.loads(fake.last.content) == {}


@pytest.mark.parametrize(
    "spelling",
    [
        "get_campaigns_by_account_id",
        "GETCAMPAIGNSBYACCOUNTID",
        "CampaignManagement.GetCampaignsByAccountId",
    ],
)
async def test_operation_names_ignore_case_underscores_and_service(
    settings: Settings, fake: FakeMicrosoft, spelling: str
) -> None:
    result = await call(settings, fake, REQUEST, {"operation": spelling})
    assert not result.is_error
    assert fake.last.url.path == "/CampaignManagement/v13/Campaigns/QueryByAccountId"


async def test_an_unknown_operation_is_refused(settings: Settings, fake: FakeMicrosoft) -> None:
    result = await call(settings, fake, REQUEST, {"operation": "LaunchRockets"})
    assert "microsoft_ads_list_operations" in error_text(result)
    assert fake.api_requests == []


async def test_identity_headers_come_from_config(settings: Settings, fake: FakeMicrosoft) -> None:
    await call(settings, fake, REQUEST, {"operation": "GetUser"})
    headers = fake.last.headers
    assert headers["Authorization"] == f"Bearer {ISSUED_ACCESS}1"
    assert headers["DeveloperToken"] == DEVELOPER_TOKEN
    assert (headers["CustomerId"], headers["CustomerAccountId"]) == ("111", "222")


async def test_per_call_ids_override_config(settings: Settings, fake: FakeMicrosoft) -> None:
    arguments = {"operation": "GetUser", "customer_id": " 333 ", "account_id": "444"}
    await call(settings, fake, REQUEST, arguments)
    assert (fake.last.headers["CustomerId"], fake.last.headers["CustomerAccountId"]) == (
        "333",
        "444",
    )


async def test_unset_ids_are_omitted(settings: Settings, fake: FakeMicrosoft) -> None:
    bare = replace(settings, customer_id=None, account_id=None)
    await call(bare, fake, REQUEST, {"operation": "GetUser"})
    assert "CustomerId" not in fake.last.headers
    assert "CustomerAccountId" not in fake.last.headers


@pytest.mark.parametrize("field", ["customer_id", "account_id"])
async def test_a_non_digit_id_is_refused(
    settings: Settings, fake: FakeMicrosoft, field: str
) -> None:
    result = await call(settings, fake, REQUEST, {"operation": "GetUser", field: "12-ab"})
    assert f"{field} must be digits" in error_text(result)
    assert fake.api_requests == []


async def test_missing_credentials_name_the_variables(fake: FakeMicrosoft) -> None:
    result = await call(Settings(), fake, REQUEST, {"operation": "GetUser"})
    message = error_text(result)
    for variable in (
        "MICROSOFT_ADS_CLIENT_ID",
        "MICROSOFT_ADS_REFRESH_TOKEN",
        "MICROSOFT_ADS_DEVELOPER_TOKEN",
    ):
        assert variable in message
    assert "CLIENT_SECRET" not in message
    assert fake.token_requests == []


def fault(code: int) -> httpx2.Response:
    """Answer like Microsoft's 401 AdApiFaultDetail with error `code`."""
    body = {
        "Errors": [{"Code": code, "ErrorCode": "InvalidCredentials", "Message": "no"}],
        "Type": "AdApiFaultDetail",
    }
    return httpx2.Response(401, json=body)


def aged_fault(clock: Clock, code: int) -> httpx2.Response:
    """Reject the token after it has been in use for longer than a minute."""
    clock.now += FRESH_SECONDS
    return fault(code)


@pytest.mark.parametrize("code", [105, 109])
async def test_a_rejected_token_is_refreshed_and_retried_once(
    settings: Settings, fake: FakeMicrosoft, clock: Clock, code: int
) -> None:
    answers = [lambda: aged_fault(clock, code), lambda: httpx2.Response(200, json={"ok": True})]
    fake.api_handler = lambda _request: answers.pop(0)()
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert structured(result)["status"] == 200
    assert len(fake.token_requests) == 2
    tokens = [request.headers["Authorization"] for request in fake.api_requests]
    assert tokens == [f"Bearer {ISSUED_ACCESS}1", f"Bearer {ISSUED_ACCESS}2"]


async def test_a_second_rejection_is_returned_not_looped(
    settings: Settings, fake: FakeMicrosoft, clock: Clock
) -> None:
    fake.api_handler = lambda _request: aged_fault(clock, 109)
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert structured(result)["status"] == 401
    assert len(fake.api_requests) == 2


async def test_a_brand_new_token_that_is_rejected_is_not_refreshed(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    # 105 also means an inactive account or developer token; a new token would not help.
    fake.api_handler = lambda _request: fault(105)
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert structured(result)["status"] == 401
    assert len(fake.api_requests) == 1
    assert len(fake.token_requests) == 1


async def test_concurrent_rejections_share_one_refresh(settings: Settings, clock: Clock) -> None:
    refreshes: list[int] = []

    async def microsoft(request: httpx2.Request) -> httpx2.Response:
        if request.url.host == TOKEN_HOST:
            refreshes.append(1)
            return httpx2.Response(200, json={"access_token": f"access-{len(refreshes)}"})
        if request.headers["Authorization"] == "Bearer access-1":
            clock.now = 2 * FRESH_SECONDS
            await anyio.sleep(0.01)  # both calls are rejected before either refreshes
            return fault(109)
        return httpx2.Response(200, json={"ok": True})

    catalog = OperationCatalog(load_catalog(), settings.max_response_bytes)
    api = MicrosoftAdsApi(settings, catalog, httpx2.MockTransport(microsoft))
    statuses: list[object] = []

    async def get_user() -> None:
        statuses.append((await api.call(ApiRequest("GetUser")))["status"])

    async with anyio.create_task_group() as group:
        group.start_soon(get_user)
        group.start_soon(get_user)
    assert statuses == [200, 200]
    assert len(refreshes) == 2  # the first token, then one shared refresh


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(401, json={"Errors": [{"Code": 106}]}),
        httpx2.Response(401, json={"Errors": []}),
        httpx2.Response(401, json={"Errors": ["x"]}),
        httpx2.Response(401, json=["not", "a", "fault"]),
        httpx2.Response(401, text="Unauthorized"),
        httpx2.Response(400, json={"Errors": [{"Code": 105}]}),
    ],
)
async def test_other_failures_are_returned_without_a_retry(
    settings: Settings, fake: FakeMicrosoft, response: httpx2.Response
) -> None:
    fake.api_handler = lambda _request: response
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert structured(result)["status"] == response.status_code
    assert len(fake.api_requests) == 1


async def test_a_non_json_body_comes_back_as_text(settings: Settings, fake: FakeMicrosoft) -> None:
    fake.api_handler = lambda _request: httpx2.Response(502, text="Bad gateway")
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert structured(result) == {"status": 502, "text": "Bad gateway"}


async def test_an_over_limit_body_stops_reading_at_the_cap(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    sent: list[int] = []

    async def endless() -> AsyncIterator[bytes]:
        for _ in range(1000):
            sent.append(1)
            yield b"x" * 500

    fake.api_handler = lambda _request: httpx2.Response(200, content=endless())
    small = replace(settings, max_response_bytes=1000)
    result = await call(small, fake, REQUEST, {"operation": "GetUser"})
    assert "MICROSOFT_ADS_MAX_RESPONSE_BYTES" in error_text(result)
    assert len(sent) <= 3  # 3 chunks of 500 pass the 1000-byte cap


async def test_an_over_limit_body_is_refused(settings: Settings, fake: FakeMicrosoft) -> None:
    fake.api_handler = lambda _request: httpx2.Response(200, json={"x": "y" * 2000})
    small = replace(settings, max_response_bytes=1000)
    result = await call(small, fake, REQUEST, {"operation": "GetUser"})
    assert "DownloadCampaignsByCampaignIds" in error_text(result)


async def test_an_unreachable_api_is_a_clear_error(settings: Settings, fake: FakeMicrosoft) -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        message = "connection refused"
        raise httpx2.ConnectError(message, request=request)

    fake.api_handler = refuse
    result = await call(settings, fake, REQUEST, {"operation": "GetUser"})
    assert "ConnectError" in error_text(result)


async def test_a_public_client_sends_no_secret(fake: FakeMicrosoft, settings: Settings) -> None:
    public = replace(settings, credentials=replace(settings.credentials, client_secret=None))
    await call(public, fake, REQUEST, {"operation": "GetUser"})
    assert b"client_secret" not in fake.token_requests[0].content


async def test_tool_arguments_reach_nothing_but_the_catalog() -> None:
    async with Client(build_server(Settings(credentials=Credentials()))) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
    assert sorted(tools) == [
        "microsoft_ads_describe_operation",
        "microsoft_ads_describe_type",
        "microsoft_ads_download_file",
        "microsoft_ads_list_operations",
        "microsoft_ads_request",
    ]
    arguments = {name: set(tool.input_schema["properties"]) for name, tool in tools.items()}
    assert arguments["microsoft_ads_request"] == {"operation", "body", "customer_id", "account_id"}
    assert arguments["microsoft_ads_download_file"] == {"url"}
    forbidden = {"path", "host", "headers", "header", "file", "filename", "directory"}
    assert all(not names & forbidden for names in arguments.values())
    assert not any("url" in names for name, names in arguments.items() if "download" not in name)
    description = tools["microsoft_ads_request"].description or ""
    assert "SPEND REAL MONEY" in description
    assert '"Status": "Paused"' in description
