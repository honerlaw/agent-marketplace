"""The HTTP transport, served by a real uvicorn server on a local port."""

import base64
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import replace

import httpx2
import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from openai_mcp.config import Settings
from openai_mcp.http_app import build_http_app
from openai_mcp.server import build_server
from tests.conftest import FakeOpenAI

TOKEN = "test-token"  # noqa: S105 - a fixture value, not a secret


def free_port() -> int:
    """Ask the OS for a port nobody is listening on."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def serve(settings: Settings, fake: FakeOpenAI) -> Iterator[str]:
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
def guarded_url(settings: Settings, fake: FakeOpenAI) -> Iterator[str]:
    """Run a server that requires the bearer token."""
    yield from serve(replace(settings, auth_token=TOKEN, port=free_port()), fake)


@pytest.fixture
def open_url(settings: Settings, fake: FakeOpenAI) -> Iterator[str]:
    """Run a server started with authentication explicitly disabled."""
    yield from serve(replace(settings, allow_unauthenticated=True, port=free_port()), fake)


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
async def test_authenticated_multipart_call_over_http(guarded_url: str, fake: FakeOpenAI) -> None:
    files = [{"filename": "a.jsonl", "content_base64": base64.b64encode(b"{}").decode()}]
    auth = httpx2.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"})
    async with Client(streamable_http_client(f"{guarded_url}/mcp", http_client=auth)) as client:
        result = await client.call_tool(
            "openai_multipart_request", {"path": "/files", "files": files}
        )
    assert not result.is_error
    assert b'filename="a.jsonl"' in fake.last.content


@pytest.mark.anyio
async def test_unauthenticated_mode_serves_without_a_token(open_url: str) -> None:
    async with Client(f"{open_url}/mcp") as client:
        listed = await client.list_tools()
    assert len(listed.tools) == 5
