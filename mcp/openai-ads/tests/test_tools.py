"""The four tools, exercised end to end through an in-process MCP client."""

import base64
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from openai_ads_mcp.config import Settings
from openai_ads_mcp.server import INSTRUCTIONS, build_server
from tests.conftest import FakeAdsApi

pytestmark = pytest.mark.anyio

TOOL_NAMES = {
    "openai_ads_request",
    "openai_ads_multipart_request",
    "openai_ads_list_endpoints",
    "openai_ads_describe_endpoint",
}
PATH_TOOLS = [
    ("openai_ads_request", {"method": "GET"}),
    ("openai_ads_multipart_request", {"files": [{"filename": "a", "content_base64": "eA=="}]}),
]


async def call(
    settings: Settings, fake: FakeAdsApi, tool: str, arguments: Mapping[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake API."""
    async with Client(build_server(settings, fake.transport)) as client:
        return await client.call_tool(tool, dict(arguments))


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def test_exactly_four_tools_are_listed(settings: Settings, fake: FakeAdsApi) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == TOOL_NAMES


@pytest.mark.parametrize(
    "guidance",
    [
        "ad account > campaign > ad group > ad",
        "micros",
        'status "paused"',
        '"Idempotency-Key" header on create',
        "Confirm with the user before activating anything or changing a budget",
    ],
)
async def test_instructions_carry_the_spending_guidance(
    settings: Settings, fake: FakeAdsApi, guidance: str
) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        instructions = client.instructions
    assert instructions == INSTRUCTIONS
    assert guidance in " ".join(INSTRUCTIONS.split())


async def test_json_request_carries_credentials_body_and_idempotency_key(
    fake: FakeAdsApi,
) -> None:
    arguments = {
        "method": "POST",
        "path": "/campaigns",
        "query": {"include": "reviews"},
        "body": {"name": "Spring launch", "status": "paused"},
        "headers": {"Idempotency-Key": "spring-001"},
    }
    result = await call(Settings(api_key="sk-test"), fake, "openai_ads_request", arguments)
    assert result.structured_content == {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "json": {"ok": True},
    }
    sent = fake.last
    assert str(sent.url) == "https://api.ads.openai.com/v1/campaigns?include=reviews"
    assert sent.headers["authorization"] == "Bearer sk-test"
    assert sent.headers["idempotency-key"] == "spring-001"
    assert sent.content == b'{"name":"Spring launch","status":"paused"}'


async def test_only_allowlisted_response_headers_are_returned(
    settings: Settings, fake: FakeAdsApi
) -> None:
    headers = {
        "x-request-id": "req-1",
        "openai-version": "2020-10-01",
        "retry-after": "12",
        "x-ratelimit-remaining-requests": "9",
        "ratelimit-policy": "600;w=60",
        "set-cookie": "s=1",
        "server": "cloudflare",
    }
    fake.handler = lambda _request: httpx2.Response(429, headers=headers, text="slow down")
    result = await call(settings, fake, "openai_ads_request", {"method": "GET", "path": "/ads"})
    assert result.structured_content == {
        "status": 429,
        "headers": {
            "content-type": "text/plain; charset=utf-8",
            "x-request-id": "req-1",
            "openai-version": "2020-10-01",
            "retry-after": "12",
            "x-ratelimit-remaining-requests": "9",
            "ratelimit-policy": "600;w=60",
        },
        "text": "slow down",
    }


async def test_error_responses_are_returned_not_raised(
    settings: Settings, fake: FakeAdsApi
) -> None:
    fake.handler = lambda _request: httpx2.Response(404, json={"error": {"message": "nope"}})
    arguments = {"method": "GET", "path": "/campaigns/cmpn_x"}
    result = await call(settings, fake, "openai_ads_request", arguments)
    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["status"] == 404


async def test_invalid_json_body_falls_back_to_text(settings: Settings, fake: FakeAdsApi) -> None:
    fake.handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "application/json"}, content=b"{broken"
    )
    result = await call(settings, fake, "openai_ads_request", {"method": "GET", "path": "/ads"})
    assert result.structured_content is not None
    assert result.structured_content["json"] == "{broken"


async def test_empty_body_is_empty_text(settings: Settings, fake: FakeAdsApi) -> None:
    fake.handler = lambda _request: httpx2.Response(204)
    arguments = {"method": "DELETE", "path": "/lead_sync_subscriptions/sub_1"}
    result = await call(settings, fake, "openai_ads_request", arguments)
    assert result.structured_content == {"status": 204, "headers": {}, "text": ""}


@pytest.mark.parametrize(("tool", "arguments"), PATH_TOOLS)
@pytest.mark.parametrize("path", ["https://evil.test/v1", "/ads/../api_keys", "//evil.test"])
async def test_every_path_tool_refuses_unsafe_paths(
    settings: Settings, fake: FakeAdsApi, tool: str, arguments: dict[str, object], path: str
) -> None:
    result = await call(settings, fake, tool, {**arguments, "path": path})
    assert "path must" in error_text(result)
    assert fake.requests == []


@pytest.mark.parametrize("name", ["Authorization", "Host"])
async def test_protected_header_override_is_refused(
    settings: Settings, fake: FakeAdsApi, name: str
) -> None:
    arguments = {"method": "GET", "path": "/ad_account", "headers": {name: "other"}}
    result = await call(settings, fake, "openai_ads_request", arguments)
    assert "cannot be overridden" in error_text(result)
    assert fake.requests == []


async def test_multipart_upload_from_base64_and_local_path(
    settings: Settings, fake: FakeAdsApi, tmp_path: Path
) -> None:
    local = tmp_path / "card.png"
    local.write_bytes(b"from disk")
    files = [
        {
            "filename": "shoe.png",
            "content_base64": base64.b64encode(b"png bytes").decode(),
            "content_type": "image/png",
        },
        {"field": "extra", "filename": "card.png", "local_path": str(local)},
    ]
    arguments = {"path": "/uploads", "fields": {"purpose": "custom_audience"}, "files": files}
    result = await call(settings, fake, "openai_ads_multipart_request", arguments)
    assert not result.is_error
    body = fake.last.content
    assert fake.last.headers["content-type"].startswith("multipart/form-data")
    fragments = (
        b'name="purpose"',
        b"custom_audience",
        b'filename="shoe.png"',
        b"png bytes",
        b"from disk",
    )
    for fragment in fragments:
        assert fragment in body


@pytest.mark.parametrize(
    "file_input",
    [
        {"filename": "a.png"},
        {"filename": "a.png", "content_base64": "eA==", "local_path": "/tmp/a"},  # noqa: S108
        {"filename": "a.png", "content_base64": "not base64!"},
    ],
)
async def test_bad_file_inputs_are_refused(
    settings: Settings, fake: FakeAdsApi, file_input: dict[str, str]
) -> None:
    arguments = {"path": "/upload", "files": [file_input]}
    result = await call(settings, fake, "openai_ads_multipart_request", arguments)
    assert "a.png" in error_text(result)
    assert fake.requests == []


async def test_query_accepts_numbers_booleans_and_lists(
    settings: Settings, fake: FakeAdsApi
) -> None:
    query = {"limit": 10, "is_active": False, "include": ["serving_issues", "reviews"]}
    await call(
        settings, fake, "openai_ads_request", {"method": "GET", "path": "/x", "query": query}
    )
    assert fake.last.url.query == (
        b"limit=10&is_active=false&include=serving_issues&include=reviews"
    )


async def test_multipart_without_files_is_refused(settings: Settings, fake: FakeAdsApi) -> None:
    arguments = {"path": "/upload", "files": [], "fields": {"image_url": "https://x.test/a.png"}}
    result = await call(settings, fake, "openai_ads_multipart_request", arguments)
    assert "at least one file" in error_text(result)
    assert fake.requests == []


async def test_http_mode_refuses_server_local_files(settings: Settings, fake: FakeAdsApi) -> None:
    http_settings = replace(settings, transport="http")
    files = [{"filename": "e", "local_path": "/proc/self/environ"}]
    arguments = {"path": "/upload", "files": files}
    result = await call(http_settings, fake, "openai_ads_multipart_request", arguments)
    assert "disabled over HTTP" in error_text(result)
    assert fake.requests == []
