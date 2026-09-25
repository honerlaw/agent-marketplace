"""The five tools, exercised end to end through an in-process MCP client."""

import base64
from collections.abc import Mapping
from pathlib import Path

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from openai_mcp.config import Settings
from openai_mcp.server import build_server
from tests.conftest import FakeOpenAI

pytestmark = pytest.mark.anyio

TOOL_NAMES = {
    "openai_request",
    "openai_multipart_request",
    "openai_download",
    "openai_list_endpoints",
    "openai_describe_endpoint",
}
PATH_TOOLS = [
    ("openai_request", {"method": "GET"}),
    ("openai_multipart_request", {"files": []}),
    ("openai_download", {}),
]


async def call(
    settings: Settings, fake: FakeOpenAI, tool: str, arguments: Mapping[str, object]
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


async def test_exactly_five_tools_are_listed(settings: Settings, fake: FakeOpenAI) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == TOOL_NAMES


async def test_json_request_carries_credentials_and_body(fake: FakeOpenAI) -> None:
    settings = Settings(api_key="sk-test", organization="org-1", project="proj-1")
    arguments = {
        "method": "POST",
        "path": "/responses",
        "query": {"include": "usage"},
        "body": {"model": "gpt-test", "input": "hi"},
        "headers": {"OpenAI-Beta": "assistants=v2"},
    }
    result = await call(settings, fake, "openai_request", arguments)
    assert result.structured_content == {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "json": {"ok": True},
    }
    sent = fake.last
    assert str(sent.url) == "https://api.openai.com/v1/responses?include=usage"
    assert sent.headers["authorization"] == "Bearer sk-test"
    assert sent.headers["openai-organization"] == "org-1"
    assert sent.headers["openai-project"] == "proj-1"
    assert sent.headers["openai-beta"] == "assistants=v2"
    assert sent.content == b'{"model":"gpt-test","input":"hi"}'


async def test_only_allowlisted_response_headers_are_returned(
    settings: Settings, fake: FakeOpenAI
) -> None:
    headers = {"x-request-id": "req-1", "x-ratelimit-remaining-tokens": "9", "set-cookie": "s=1"}
    fake.handler = lambda _request: httpx2.Response(200, headers=headers, text="plain")
    result = await call(settings, fake, "openai_request", {"method": "GET", "path": "/models"})
    assert result.structured_content == {
        "status": 200,
        "headers": {
            "content-type": "text/plain; charset=utf-8",
            "x-request-id": "req-1",
            "x-ratelimit-remaining-tokens": "9",
        },
        "text": "plain",
    }


async def test_error_responses_are_returned_not_raised(
    settings: Settings, fake: FakeOpenAI
) -> None:
    fake.handler = lambda _request: httpx2.Response(404, json={"error": {"message": "nope"}})
    result = await call(settings, fake, "openai_request", {"method": "GET", "path": "/models/x"})
    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["status"] == 404


async def test_invalid_json_body_falls_back_to_text(settings: Settings, fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "application/json"}, content=b"{broken"
    )
    result = await call(settings, fake, "openai_request", {"method": "GET", "path": "/models"})
    assert result.structured_content is not None
    assert result.structured_content["json"] == "{broken"


async def test_empty_body_is_empty_text(settings: Settings, fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(204)
    result = await call(settings, fake, "openai_request", {"method": "DELETE", "path": "/files/f"})
    assert result.structured_content == {"status": 204, "headers": {}, "text": ""}


async def test_streamed_events_are_returned_buffered(settings: Settings, fake: FakeOpenAI) -> None:
    events = 'data: {"delta": "hi"}\n\ndata: [DONE]\n\n'
    fake.handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "text/event-stream"}, text=events
    )
    arguments = {"method": "POST", "path": "/chat/completions", "body": {"stream": True}}
    result = await call(settings, fake, "openai_request", arguments)
    assert result.structured_content is not None
    assert result.structured_content["text"] == events


async def test_small_binary_is_base64(settings: Settings, fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "audio/mpeg"}, content=b"\x00\x01"
    )
    arguments = {"method": "POST", "path": "/audio/speech", "body": {"input": "hi"}}
    result = await call(settings, fake, "openai_request", arguments)
    assert result.structured_content is not None
    assert result.structured_content["base64"] == base64.b64encode(b"\x00\x01").decode()


async def test_binary_over_the_cap_is_refused(settings: Settings, fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(
        200, headers={"content-type": "audio/mpeg"}, content=b"x" * 17
    )
    result = await call(settings, fake, "openai_request", {"method": "GET", "path": "/big"})
    assert "over the 16-byte limit" in error_text(result)


@pytest.mark.parametrize(("tool", "arguments"), PATH_TOOLS)
@pytest.mark.parametrize("path", ["https://evil.test/v1", "/files/../admin", "//evil.test"])
async def test_every_path_tool_refuses_unsafe_paths(
    settings: Settings, fake: FakeOpenAI, tool: str, arguments: dict[str, object], path: str
) -> None:
    result = await call(settings, fake, tool, {**arguments, "path": path})
    assert "path must" in error_text(result)
    assert fake.requests == []


async def test_protected_header_override_is_refused(settings: Settings, fake: FakeOpenAI) -> None:
    arguments = {"method": "GET", "path": "/models", "headers": {"Authorization": "Bearer other"}}
    result = await call(settings, fake, "openai_request", arguments)
    assert "cannot be overridden" in error_text(result)
    assert fake.requests == []


async def test_multipart_upload_from_base64_and_local_path(
    settings: Settings, fake: FakeOpenAI, tmp_path: Path
) -> None:
    local = tmp_path / "notes.txt"
    local.write_bytes(b"from disk")
    files = [
        {"filename": "batch.jsonl", "content_base64": base64.b64encode(b"{}\n").decode()},
        {"field": "extra", "filename": "notes.txt", "local_path": str(local)},
    ]
    arguments = {"path": "/files", "fields": {"purpose": "batch"}, "files": files}
    result = await call(settings, fake, "openai_multipart_request", arguments)
    assert not result.is_error
    body = fake.last.content
    assert fake.last.headers["content-type"].startswith("multipart/form-data")
    for fragment in (b'name="purpose"', b"batch", b'filename="batch.jsonl"', b"{}\n", b"from disk"):
        assert fragment in body


@pytest.mark.parametrize(
    "file_input",
    [
        {"filename": "a.txt"},
        {"filename": "a.txt", "content_base64": "eA==", "local_path": "/tmp/a"},  # noqa: S108
        {"filename": "a.txt", "content_base64": "not base64!"},
    ],
)
async def test_bad_file_inputs_are_refused(
    settings: Settings, fake: FakeOpenAI, file_input: dict[str, str]
) -> None:
    arguments = {"path": "/files", "files": [file_input]}
    result = await call(settings, fake, "openai_multipart_request", arguments)
    assert "a.txt" in error_text(result)
    assert fake.requests == []


async def test_download_inline(settings: Settings, fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(200, content=b"\x89PNG")
    result = await call(settings, fake, "openai_download", {"path": "/files/f/content"})
    assert result.structured_content is not None
    assert result.structured_content["base64"] == base64.b64encode(b"\x89PNG").decode()


async def test_download_to_file_streams_past_the_cap(
    settings: Settings, fake: FakeOpenAI, tmp_path: Path
) -> None:
    fake.handler = lambda _request: httpx2.Response(200, content=b"y" * 100)
    target = tmp_path / "nested" / "out.bin"
    arguments = {"path": "/files/f/content", "save_to": str(target)}
    result = await call(settings, fake, "openai_download", arguments)
    assert result.structured_content == {"status": 200, "saved_to": str(target), "bytes": 100}
    assert target.read_bytes() == b"y" * 100


async def test_download_error_is_described_not_saved(
    settings: Settings, fake: FakeOpenAI, tmp_path: Path
) -> None:
    fake.handler = lambda _request: httpx2.Response(404, json={"error": "missing"})
    target = tmp_path / "out.bin"
    arguments = {"path": "/files/f/content", "save_to": str(target)}
    result = await call(settings, fake, "openai_download", arguments)
    assert result.structured_content is not None
    assert result.structured_content["status"] == 404
    assert not target.exists()
