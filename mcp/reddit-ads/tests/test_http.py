"""The HTTP transport, served by a real uvicorn server on a local port."""

import json
import socket
import threading
import time
from collections.abc import Iterator, Mapping
from dataclasses import replace

import httpx2
import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from reddit_ads_mcp.config import Settings
from reddit_ads_mcp.http_app import build_http_app
from reddit_ads_mcp.server import build_server
from tests.conftest import FakeReddit

TOKEN = "test-token"  # noqa: S105 - a fixture value, not a secret


def free_port() -> int:
    """Ask the OS for a port nobody is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def serve(settings: Settings, fake: FakeReddit) -> Iterator[str]:
    """Run the HTTP app in a background thread and yield its base URL."""
    app = build_http_app(build_server(settings, fake.transport), settings)
    server = uvicorn.Server(uvicorn.Config(app, port=settings.port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://127.0.0.1:{settings.port}"
    server.should_exit = True
    thread.join()


@pytest.fixture
def guarded_url(settings: Settings, fake: FakeReddit) -> Iterator[str]:
    """Run a server that requires the bearer token."""
    yield from serve(replace(settings, auth_token=TOKEN, port=free_port()), fake)


@pytest.fixture
def open_url(settings: Settings, fake: FakeReddit) -> Iterator[str]:
    """Run a server started with authentication explicitly disabled."""
    yield from serve(replace(settings, allow_unauthenticated=True, port=free_port()), fake)


@pytest.fixture
def stateless_url(settings: Settings, fake: FakeReddit) -> Iterator[str]:
    """Run a guarded server in stateless mode."""
    yield from serve(replace(settings, auth_token=TOKEN, stateless=True, port=free_port()), fake)


# The last protocol version with `initialize` handshakes and HTTP sessions; the
# stateless switch matters only to clients speaking it (or an earlier one).
SESSION_PROTOCOL = "2025-11-25"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": SESSION_PROTOCOL,
}
INITIALIZE = {
    "protocolVersion": SESSION_PROTOCOL,
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "0"},
}


def rpc(url: str, method: str, params: Mapping[str, object]) -> httpx2.Response:
    """POST one JSON-RPC request with no session header."""
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return httpx2.post(f"{url}/mcp", headers=HEADERS, json=body)


def result_of(response: httpx2.Response) -> dict[str, object]:
    """Pull the JSON-RPC result out of an SSE response body."""
    data = next(line for line in response.text.splitlines() if line.startswith("data:"))
    result: dict[str, object] = json.loads(data.removeprefix("data:"))["result"]
    return result


def test_stateless_mode_serves_every_request_without_a_session(
    stateless_url: str, fake: FakeReddit
) -> None:
    call = {"name": "reddit_ads_request", "arguments": {"method": "GET", "path": "/me"}}
    initialized = rpc(stateless_url, "initialize", INITIALIZE)
    listed = rpc(stateless_url, "tools/list", {})
    called = rpc(stateless_url, "tools/call", call)
    responses = (initialized, listed, called)
    assert [r.status_code for r in responses] == [200, 200, 200]
    assert all("mcp-session-id" not in r.headers for r in responses)
    assert len(result_of(listed)["tools"]) == 4  # type: ignore[arg-type]
    assert result_of(called)["isError"] is False
    assert fake.last.url.path == "/api/v3/me"


def test_default_mode_issues_a_session_and_requires_it(guarded_url: str) -> None:
    initialized = rpc(guarded_url, "initialize", INITIALIZE)
    sessionless = rpc(guarded_url, "tools/list", {})
    assert initialized.status_code == 200
    assert initialized.headers["mcp-session-id"]
    assert sessionless.status_code == 400


def test_health_check_needs_no_token(guarded_url: str) -> None:
    response = httpx2.get(f"{guarded_url}/healthz")
    assert (response.status_code, response.text) == (200, "ok")


@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": TOKEN}]
)
def test_mcp_endpoint_rejects_bad_tokens(guarded_url: str, headers: dict[str, str]) -> None:
    response = httpx2.post(f"{guarded_url}/mcp", headers=headers, json={})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_authenticated_tool_call_over_http(guarded_url: str, fake: FakeReddit) -> None:
    auth = httpx2.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"})
    async with Client(streamable_http_client(f"{guarded_url}/mcp", http_client=auth)) as client:
        result = await client.call_tool(
            "reddit_ads_request", {"method": "GET", "path": "/ad_accounts/a1"}
        )
    assert not result.is_error
    assert fake.last.url.path == "/api/v3/ad_accounts/a1"


@pytest.mark.anyio
def test_bearer_scheme_is_case_insensitive(guarded_url: str) -> None:
    response = httpx2.get(f"{guarded_url}/mcp", headers={"Authorization": f"bearer {TOKEN}"})
    assert response.status_code != 401


@pytest.mark.anyio
async def test_unauthenticated_mode_serves_without_a_token(open_url: str) -> None:
    async with Client(f"{open_url}/mcp") as client:
        listed = await client.list_tools()
    assert len(listed.tools) == 4
