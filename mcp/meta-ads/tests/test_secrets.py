"""Secret containment: no tool result, error or log line carries a credential."""

import json
import logging

import httpx2
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp.api import MetaAdsApi
from meta_ads_mcp.config import Settings
from meta_ads_mcp.main import quiet_http_loggers
from meta_ads_mcp.scrub import REDACTED
from meta_ads_mcp.server import scrubbed
from tests.conftest import APP_ID, APP_SECRET, PROOF, TOKEN, FakeGraph, call, leaked

pytestmark = pytest.mark.anyio

PAGE = "https://graph.facebook.com/v26.0/act_1/campaigns"
ECHOES = {
    "paging": {
        "data": [{"id": "1", "name": "c"}],
        "paging": {
            "cursors": {"before": "b", "after": "a"},
            "next": f"{PAGE}?access_token={TOKEN}&appsecret_proof={PROOF}&after=a",
        },
    },
    "error": {"error": {"message": f"Invalid OAuth access token {TOKEN}", "code": 190}},
    "nested": {"data": {"note": f"proof {PROOF}", "deep": [{"s": f"x{APP_SECRET}y"}]}},
    "json-string": {"body": json.dumps({"echo": TOKEN, "url": f"/x?t={TOKEN}"})},
    "page-tokens": {"data": [{"id": "9", "access_token": "EAApagetoken", "name": "Page"}]},
    "aliased-token": {"id": "9", "tok": "EAAB" + "Zx9" * 20},
}
TOOL_CALLS: tuple[tuple[str, dict[str, object]], ...] = (
    ("meta_ads_request", {"method": "GET", "path": "/act_1/campaigns"}),
    ("meta_ads_follow_page", {"url": f"{PAGE}?after=a"}),
    ("meta_ads_token_status", {}),
)


def answering(body: object) -> FakeGraph:
    """Return a fake Graph that answers every call with `body`."""
    return FakeGraph(lambda _request: httpx2.Response(200, json=body))


def failing(request: httpx2.Request) -> httpx2.Response:
    """Fail like a dropped connection, naming the full URL (proof and all)."""
    message = f"connection reset while fetching {request.url}"
    raise httpx2.ConnectError(message, request=request)


@pytest.mark.parametrize("shape", sorted(ECHOES))
@pytest.mark.parametrize(("tool", "arguments"), TOOL_CALLS)
async def test_no_tool_returns_a_credential(
    settings: Settings, shape: str, tool: str, arguments: dict[str, object]
) -> None:
    result = await call(settings, answering(ECHOES[shape]), tool, arguments)
    assert leaked(result) == []


async def test_paging_keeps_cursors_and_other_parameters(settings: Settings) -> None:
    result = await call(settings, answering(ECHOES["paging"]), *TOOL_CALLS[0])
    assert result.structured_content is not None
    paging = result.structured_content["json"]["paging"]
    assert paging == {"cursors": {"before": "b", "after": "a"}, "next": f"{PAGE}?after=a"}


async def test_page_tokens_are_redacted(settings: Settings) -> None:
    result = await call(settings, answering(ECHOES["page-tokens"]), *TOOL_CALLS[0])
    assert result.structured_content is not None
    assert result.structured_content["json"]["data"][0]["access_token"] == REDACTED


@pytest.mark.parametrize(("tool", "arguments"), TOOL_CALLS)
async def test_a_transport_error_does_not_leak(
    settings: Settings, tool: str, arguments: dict[str, object]
) -> None:
    result = await call(settings, FakeGraph(failing), tool, arguments)
    assert result.is_error
    assert "ConnectError" in json.dumps(result.model_dump(mode="json"))
    assert leaked(result) == []


async def test_any_tool_error_is_scrubbed(settings: Settings) -> None:
    api = MetaAdsApi(settings)

    async def fail() -> None:
        message = f"bad {TOKEN} and {APP_ID}|{APP_SECRET}"
        raise ToolError(message)

    with pytest.raises(ToolError) as raised:
        await scrubbed(api.scrubber, fail())
    assert leaked(str(raised.value)) == []


async def test_debug_token_needs_app_credentials(settings: Settings) -> None:
    from dataclasses import replace  # noqa: PLC0415 - local to the one test using it

    api = MetaAdsApi(replace(settings, app_id=None, app_secret=None))
    with pytest.raises(ToolError, match="META_APP_ID"):
        await api.debug_token()


async def test_the_http_client_logs_carry_no_credential(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    quiet_http_loggers()
    for tool, arguments in TOOL_CALLS:
        await call(settings, answering(ECHOES["paging"]), tool, arguments)
    assert leaked(caplog.text) == []


async def test_without_quieting_the_client_would_log_the_proof(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    """The negative control: the loggers really do print URLs at INFO."""
    caplog.set_level(logging.DEBUG)
    names = ("httpx", "httpx2", "httpcore", "httpcore2")
    levels = {name: logging.getLogger(name).level for name in names}
    try:
        for name in names:
            logging.getLogger(name).setLevel(logging.DEBUG)
        await call(settings, answering({}), *TOOL_CALLS[0])
    finally:
        for name, level in levels.items():
            logging.getLogger(name).setLevel(level)
    assert PROOF in caplog.text
