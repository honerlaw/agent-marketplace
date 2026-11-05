"""Secret containment: no tool result, error or log line carries a credential."""

import json
import logging
from dataclasses import replace

import httpx2
import pytest
from mcp import Client

from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.main import quiet_http_loggers
from microsoft_ads_mcp.scrub import REDACTED, Scrubber
from microsoft_ads_mcp.server import build_server
from tests.conftest import (
    CLIENT_SECRET,
    DEVELOPER_TOKEN,
    ISSUED_ACCESS,
    ISSUED_REFRESH,
    REFRESH_TOKEN,
    SECRETS,
    FakeMicrosoft,
    call,
    leaked,
    structured,
)

pytestmark = pytest.mark.anyio

BLOB = "https://bingadsstore.blob.core.windows.net/r.csv?sig=1"
ECHOES = {
    "success": {"CampaignIds": ["1"], "note": f"token {ISSUED_ACCESS}1"},
    "api-fault": {
        "Type": "ApiFaultDetail",
        "OperationErrors": [{"Code": 1, "Message": f"bad developer token {DEVELOPER_TOKEN}"}],
        "BatchErrors": [],
    },
    "auth-fault": {
        "Type": "AdApiFaultDetail",
        "Errors": [{"Code": 106, "Message": f"refresh {REFRESH_TOKEN} {ISSUED_REFRESH}1"}],
    },
    "nested": {"a": [{f"key{CLIENT_SECRET}": json.dumps({"echo": CLIENT_SECRET})}]},
}
TOOL_CALLS: tuple[tuple[str, dict[str, object]], ...] = (
    ("microsoft_ads_request", {"operation": "GetUser"}),
    ("microsoft_ads_download_file", {"url": BLOB}),
)


def answering(body: object, status: int = 200) -> FakeMicrosoft:
    """Return a fake that answers every API-host call with `body` as JSON."""
    return FakeMicrosoft(api_handler=lambda _request: httpx2.Response(status, json=body))


@pytest.mark.parametrize("shape", sorted(ECHOES))
@pytest.mark.parametrize(("tool", "arguments"), TOOL_CALLS)
async def test_no_tool_returns_a_credential(
    settings: Settings, shape: str, tool: str, arguments: dict[str, object]
) -> None:
    fake = answering(ECHOES[shape])
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool("microsoft_ads_request", {"operation": "GetUser"})  # issue tokens
        result = await client.call_tool(tool, arguments)
    assert not result.is_error
    assert leaked(result) == []
    assert REDACTED in json.dumps(result.model_dump(mode="json"))


async def test_a_token_endpoint_error_does_not_leak(settings: Settings) -> None:
    echo = {"error": "invalid_client", "error_description": f"bad secret {CLIENT_SECRET}"}
    fake = FakeMicrosoft(token_handler=lambda _request: httpx2.Response(401, json=echo))
    result = await call(settings, fake, *TOOL_CALLS[0])
    assert result.is_error
    assert leaked(result) == []


@pytest.mark.parametrize(("tool", "arguments"), TOOL_CALLS)
async def test_a_transport_error_naming_secrets_does_not_leak(
    settings: Settings, tool: str, arguments: dict[str, object]
) -> None:
    def failing(request: httpx2.Request) -> httpx2.Response:
        message = f"reset while sending {request.headers.get('Authorization')} {DEVELOPER_TOKEN}"
        raise httpx2.ConnectError(message, request=request)

    fake = FakeMicrosoft(api_handler=failing)
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool(*TOOL_CALLS[0])  # issues a token, then fails
        result = await client.call_tool(tool, arguments)
    assert result.is_error
    assert "ConnectError" in json.dumps(result.model_dump(mode="json"))
    assert leaked(result) == []


async def test_without_a_client_secret_nothing_extra_is_redacted(settings: Settings) -> None:
    public = replace(settings, credentials=replace(settings.credentials, client_secret=None))
    body = {"Name": "", "Notes": "plain text with no secrets"}
    result = await call(public, answering(body), *TOOL_CALLS[0])
    assert structured(result)["json"] == body


def test_empty_secrets_are_ignored_and_longer_ones_win() -> None:
    scrubber = Scrubber(lambda: ["", "abc", "abcdef"])
    assert scrubber.text("x abcdef y abc") == f"x {REDACTED} y {REDACTED}"
    assert scrubber.value({"k": [1, None, "abc"]}) == {"k": [1, None, REDACTED]}


async def test_logs_carry_no_credential(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    quiet_http_loggers()
    caplog.set_level(logging.DEBUG)
    for name in ("httpx", "httpx2", "httpcore", "httpcore2"):
        caplog.set_level(logging.WARNING, logger=name)
    fake = answering(ECHOES["auth-fault"], status=401)
    for tool, arguments in TOOL_CALLS:
        await call(settings, fake, tool, arguments)
    assert [secret for secret in SECRETS if secret in caplog.text] == []
