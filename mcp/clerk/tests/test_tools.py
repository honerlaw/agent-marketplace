"""The three tools, exercised end to end through an in-process MCP client."""

import json
from collections.abc import Mapping
from dataclasses import replace

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from clerk_mcp.api import MAX_BODY_CHARS
from clerk_mcp.config import Settings
from clerk_mcp.scrub import REDACTED
from clerk_mcp.server import INSTRUCTIONS, build_server
from clerk_mcp.spec import SpecCatalog
from tests.conftest import SECRET, FakeClerk

pytestmark = pytest.mark.anyio

TOOL_NAMES = {"clerk_request", "clerk_list_endpoints", "clerk_describe_endpoint"}


async def call(
    settings: Settings, fake: FakeClerk, tool: str, arguments: Mapping[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake API and the fixture spec."""
    server = build_server(settings, fake.transport, SpecCatalog({"paths": {}}))
    async with Client(server) as client:
        return await client.call_tool(tool, dict(arguments))


async def request(settings: Settings, fake: FakeClerk, **arguments: object) -> dict[str, object]:
    """Call clerk_request and return its structured result."""
    result = await call(settings, fake, "clerk_request", arguments)
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def test_exactly_three_tools_are_listed(settings: Settings, fake: FakeClerk) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        listed = await client.list_tools()
        instructions = client.instructions
    assert {tool.name for tool in listed.tools} == TOOL_NAMES
    assert instructions == INSTRUCTIONS
    assert '"order_by": "-created_at"' in INSTRUCTIONS


async def test_request_carries_the_key_and_the_pinned_version(
    settings: Settings, fake: FakeClerk
) -> None:
    query = {"order_by": "-created_at", "limit": 20}
    result = await request(settings, fake, method="get", path="/users", query=query)
    sent = fake.last
    assert sent.method == "GET"
    assert str(sent.url) == "https://api.clerk.com/v1/users?order_by=-created_at&limit=20"
    assert sent.headers["authorization"] == f"Bearer {SECRET}"
    assert sent.headers["clerk-api-version"] == "2026-08-20"
    assert result == {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "json": {"ok": True},
    }


async def test_json_body_is_sent(settings: Settings, fake: FakeClerk) -> None:
    body = {"email_address": ["a@example.test"]}
    await request(settings, fake, method="POST", path="/users", body=body)
    assert fake.last.method == "POST"
    assert json.loads(fake.last.content) == body


@pytest.mark.parametrize(
    ("arguments", "reason"),
    [
        ({"method": "GET", "path": "/users/.."}, "segments"),
        ({"method": "GET", "path": "/users/%2e%2e"}, "must not contain"),
        ({"method": "GET", "path": "/users/%252e%252e/instance"}, "must not contain"),
        ({"method": "GET", "path": "/users%2f..%2finstance"}, "must not contain"),
        ({"method": "GET", "path": "/users%5c..%5cinstance"}, "must not contain"),
        ({"method": "GET", "path": "/users/."}, "segments"),
        ({"method": "GET", "path": "//evil.test/users"}, "segments"),
        ({"method": "GET", "path": "https://evil.test/users"}, "start with '/'"),
        ({"method": "GET", "path": "/users?limit=1"}, "must not contain"),
        ({"method": "GET", "path": "/users#x"}, "must not contain"),
        ({"method": "GET", "path": "/users\\x"}, "must not contain"),
        ({"method": "GET", "path": "/users/ x"}, "must not contain"),
        (
            {"method": "GET", "path": "/users", "query": {"__clerk_api_version": "2021-02-05"}},
            "pins the API version",
        ),
        (
            {"method": "GET", "path": "/users", "query": {"__CLERK_API_VERSION": "2021-02-05"}},
            "pins the API version",
        ),
        ({"method": "HEAD", "path": "/users"}, "method must be one of"),
        ({"method": "TRACE", "path": "/users"}, "method must be one of"),
    ],
)
async def test_refused_requests_never_go_out(
    settings: Settings, fake: FakeClerk, arguments: dict[str, object], reason: str
) -> None:
    result = await call(settings, fake, "clerk_request", arguments)
    assert reason in error_text(result)
    assert fake.requests == []


@pytest.mark.parametrize("method", ["POST", "put", "PATCH", "delete"])
async def test_read_only_refuses_writes_before_sending(
    settings: Settings, fake: FakeClerk, method: str
) -> None:
    result = await call(
        replace(settings, read_only=True),
        fake,
        "clerk_request",
        {"method": method, "path": "/users/user_1"},
    )
    assert "read-only" in error_text(result)
    assert fake.requests == []


async def test_read_only_still_sends_a_lower_case_get(settings: Settings, fake: FakeClerk) -> None:
    await request(replace(settings, read_only=True), fake, method="get", path="/users/count")
    assert (fake.last.method, fake.last.url.path) == ("GET", "/v1/users/count")


async def test_redirects_are_returned_not_followed(settings: Settings) -> None:
    fake = FakeClerk(lambda _r: httpx2.Response(302, headers={"location": "https://evil.test/"}))
    result = await request(settings, fake, method="GET", path="/users")
    assert result["status"] == 302
    assert len(fake.requests) == 1


async def test_only_listed_headers_are_forwarded(settings: Settings) -> None:
    headers = {
        "content-type": "application/json",
        "retry-after": "3",
        "x-ratelimit-remaining": "0",
        "ratelimit-reset": "9",
        "set-cookie": "session=abc",
        "x-other": "no",
    }
    fake = FakeClerk(lambda _r: httpx2.Response(429, headers=headers, content=b"{}"))
    result = await request(settings, fake, method="GET", path="/users")
    assert result["status"] == 429
    assert result["headers"] == {
        "content-type": "application/json",
        "retry-after": "3",
        "x-ratelimit-remaining": "0",
        "ratelimit-reset": "9",
    }
    assert len(fake.requests) == 1


async def test_text_and_bad_json_come_back_as_text(settings: Settings) -> None:
    plain = FakeClerk(lambda _r: httpx2.Response(500, text="boom"))
    bad = FakeClerk(
        lambda _r: httpx2.Response(200, headers={"content-type": "application/json"}, content=b"{")
    )
    assert (await request(settings, plain, method="GET", path="/users"))["text"] == "boom"
    assert (await request(settings, bad, method="GET", path="/users"))["text"] == "{"


async def test_the_secret_is_scrubbed_from_keys_values_headers_and_text(
    settings: Settings,
) -> None:
    echoed = {SECRET: [f"key {SECRET}", 1, None]}
    headers = {"content-type": "application/json", "retry-after": SECRET}
    json_fake = FakeClerk(lambda _r: httpx2.Response(400, headers=headers, json=echoed))
    text_fake = FakeClerk(lambda _r: httpx2.Response(400, text=f"bad key {SECRET}"))
    as_json = await request(settings, json_fake, method="GET", path="/users")
    as_text = await request(settings, text_fake, method="GET", path="/users")
    assert as_json["json"] == {REDACTED: [f"key {REDACTED}", 1, None]}
    assert as_json["headers"] == {"content-type": "application/json", "retry-after": REDACTED}
    assert as_text["text"] == f"bad key {REDACTED}"


async def test_a_transport_error_is_scrubbed(settings: Settings) -> None:
    def fail(_request: httpx2.Request) -> httpx2.Response:
        message = f"cannot connect with {SECRET}"
        raise httpx2.ConnectError(message)

    result = await call(
        settings, FakeClerk(fail), "clerk_request", {"method": "GET", "path": "/users"}
    )
    message = error_text(result)
    assert SECRET not in message
    assert f"request failed: cannot connect with {REDACTED}" in message


async def test_a_large_json_body_is_cut_after_scrubbing(settings: Settings) -> None:
    # The secret straddles the cut point: scrubbing first means no fragment of it survives.
    padding = "x" * (MAX_BODY_CHARS - 20)
    users = [{"note": padding + SECRET + "tail"}]
    fake = FakeClerk(lambda _r: httpx2.Response(200, json=users))
    result = await request(settings, fake, method="GET", path="/users")
    text = result["text"]
    assert isinstance(text, str)
    assert len(text) == MAX_BODY_CHARS
    assert "sk_test" not in text
    assert result["total_chars"] == len(
        json.dumps([{"note": padding + REDACTED + "tail"}], separators=(",", ":"))
    )
    assert "body cut at" in str(result["truncated"])
    assert "json" not in result


async def test_a_large_text_body_is_cut(settings: Settings) -> None:
    fake = FakeClerk(lambda _r: httpx2.Response(200, text="y" * (MAX_BODY_CHARS + 5)))
    result = await request(settings, fake, method="GET", path="/users")
    assert result["total_chars"] == MAX_BODY_CHARS + 5
    assert len(str(result["text"])) == MAX_BODY_CHARS


async def test_discovery_tools_read_the_catalog(
    settings: Settings, fake: FakeClerk, catalog: SpecCatalog
) -> None:
    async with Client(build_server(settings, fake.transport, catalog)) as client:
        listed = await client.call_tool("clerk_list_endpoints", {"text_filter": "users"})
        described = await client.call_tool(
            "clerk_describe_endpoint", {"method": "get", "path": "/users"}
        )
    assert listed.structured_content is not None
    assert "GET /users — List all users" in listed.structured_content["result"]
    assert described.structured_content is not None
    assert described.structured_content["method"] == "GET"
    assert fake.requests == []
