"""The request and pagination tools, exercised end to end through an in-process MCP client."""

import json
from collections.abc import Mapping

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from reddit_ads_mcp.config import Settings
from reddit_ads_mcp.server import build_server
from tests.conftest import FakeReddit

pytestmark = pytest.mark.anyio

TOOL_NAMES = {
    "reddit_ads_request",
    "reddit_ads_follow_page",
    "reddit_ads_list_endpoints",
    "reddit_ads_describe_endpoint",
}
NEXT_URL = "https://ads-api.reddit.com/api/v3/ad_accounts/a1/campaigns?page.token=t%3D2&page.size=5"


async def call(
    settings: Settings, fake: FakeReddit, tool: str, arguments: Mapping[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake Reddit."""
    async with Client(build_server(settings, fake.transport)) as client:
        return await client.call_tool(tool, dict(arguments))


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def test_exactly_four_tools_are_listed(settings: Settings, fake: FakeReddit) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == TOOL_NAMES


async def test_json_request_carries_credentials_identity_and_body(
    settings: Settings, fake: FakeReddit
) -> None:
    arguments = {
        "method": "POST",
        "path": "/ad_accounts/a1/campaigns",
        "query": {"page.size": 10, "include_deleted": False},
        "body": {"data": {"name": "Launch", "objective": "CLICKS"}},
        "headers": {"X-Trace": "t-1"},
    }
    result = await call(settings, fake, "reddit_ads_request", arguments)
    assert result.structured_content == {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "json": {"data": {}},
    }
    sent = fake.last
    assert str(sent.url) == (
        "https://ads-api.reddit.com/api/v3/ad_accounts/a1/campaigns"
        "?page.size=10&include_deleted=false"
    )
    assert sent.headers["authorization"] == "Bearer access-1"
    assert sent.headers["user-agent"] == settings.user_agent
    assert sent.headers["x-trace"] == "t-1"
    assert json.loads(sent.content) == {"data": {"name": "Launch", "objective": "CLICKS"}}


async def test_only_rate_limit_headers_are_returned(settings: Settings, fake: FakeReddit) -> None:
    headers = {
        "ratelimit": '"read";r=399;t=60',
        "ratelimit-policy": '"read";q=400;w=60',
        "retry-after": "5",
        "set-cookie": "s=1",
    }
    fake.api_handler = lambda _request: httpx2.Response(429, headers=headers, text="slow down")
    result = await call(settings, fake, "reddit_ads_request", {"method": "GET", "path": "/me"})
    assert result.structured_content == {
        "status": 429,
        "headers": {
            "content-type": "text/plain; charset=utf-8",
            "ratelimit": '"read";r=399;t=60',
            "ratelimit-policy": '"read";q=400;w=60',
            "retry-after": "5",
        },
        "text": "slow down",
    }


async def test_error_responses_are_returned_not_raised(
    settings: Settings, fake: FakeReddit
) -> None:
    fake.api_handler = lambda _request: httpx2.Response(404, json={"error": {"message": "nope"}})
    arguments = {"method": "GET", "path": "/campaigns/x"}
    result = await call(settings, fake, "reddit_ads_request", arguments)
    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["status"] == 404


async def test_invalid_json_body_falls_back_to_text(settings: Settings, fake: FakeReddit) -> None:
    fake.api_handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "application/json"}, content=b"{broken"
    )
    result = await call(settings, fake, "reddit_ads_request", {"method": "GET", "path": "/me"})
    assert result.structured_content is not None
    assert result.structured_content["json"] == "{broken"


async def test_empty_body_is_empty_text(settings: Settings, fake: FakeReddit) -> None:
    fake.api_handler = lambda _request: httpx2.Response(204)
    arguments = {"method": "DELETE", "path": "/ads/ad-1"}
    result = await call(settings, fake, "reddit_ads_request", arguments)
    assert result.structured_content == {"status": 204, "headers": {}, "text": ""}


async def test_query_accepts_lists(settings: Settings, fake: FakeReddit) -> None:
    query = {"ids": ["a", "b"]}
    await call(
        settings, fake, "reddit_ads_request", {"method": "GET", "path": "/x", "query": query}
    )
    assert fake.last.url.query == b"ids=a&ids=b"


@pytest.mark.parametrize("path", ["https://evil.test/api/v3", "/campaigns/../admin", "//evil.test"])
async def test_request_refuses_unsafe_paths(
    settings: Settings, fake: FakeReddit, path: str
) -> None:
    result = await call(settings, fake, "reddit_ads_request", {"method": "GET", "path": path})
    assert "path must" in error_text(result)
    assert fake.requests == []


@pytest.mark.parametrize("name", ["Authorization", "User-Agent", "Host"])
async def test_protected_header_override_is_refused(
    settings: Settings, fake: FakeReddit, name: str
) -> None:
    arguments = {"method": "GET", "path": "/me", "headers": {name: "other"}}
    result = await call(settings, fake, "reddit_ads_request", arguments)
    assert "cannot be overridden" in error_text(result)
    assert fake.requests == []


async def test_follow_page_gets_the_url_verbatim(settings: Settings, fake: FakeReddit) -> None:
    result = await call(settings, fake, "reddit_ads_follow_page", {"url": NEXT_URL})
    assert not result.is_error
    sent = fake.last
    assert sent.method == "GET"
    assert str(sent.url) == NEXT_URL
    assert sent.headers["authorization"] == "Bearer access-1"
    assert sent.content == b""


async def test_follow_page_can_repost_the_original_body(
    settings: Settings, fake: FakeReddit
) -> None:
    body = {"data": {"fields": ["impressions"], "starts_at": "2026-09-01T00:00:00Z"}}
    url = "https://ads-api.reddit.com/api/v3/ad_accounts/a1/reports?page.token=abc"
    arguments = {"url": url, "method": "POST", "body": body}
    await call(settings, fake, "reddit_ads_follow_page", arguments)
    sent = fake.last
    assert (sent.method, str(sent.url)) == ("POST", url)
    assert json.loads(sent.content) == body


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/api/v3/ad_accounts/a1/campaigns?page.token=x",
        "https://user@ads-api.reddit.com/api/v3/campaigns",
        "https://ads-api.reddit.com/api/v3/campaigns/../../../x",
        "https://ads-api.reddit.com/other/campaigns",
    ],
)
async def test_follow_page_refuses_urls_off_the_base(
    settings: Settings, fake: FakeReddit, url: str
) -> None:
    result = await call(settings, fake, "reddit_ads_follow_page", {"url": url})
    assert result.is_error
    assert fake.requests == []
