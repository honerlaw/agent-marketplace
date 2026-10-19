"""The entry point, including a real stdio subprocess."""

import os
import runpy
import sys

import pytest
import uvicorn
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import MCPServer

from r2_uploads_mcp import main as main_module
from tests.conftest import ACCOUNT_ID

REQUIRED = {
    "R2_ACCOUNT_ID": ACCOUNT_ID,
    "R2_ACCESS_KEY_ID": "key-id",
    "R2_SECRET_ACCESS_KEY": "secret",
    "R2_BUCKET": "ad-uploads",
}


def test_stdio_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(os, "environ", REQUIRED)
    monkeypatch.setattr(MCPServer, "run", lambda _self, transport: started.append(transport))
    main_module.main()
    assert started == ["stdio"]


def test_http_mode_serves_with_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    served: list[tuple[str, int]] = []
    env = {**REQUIRED, "MCP_TRANSPORT": "http", "MCP_AUTH_TOKEN": "t"}
    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(uvicorn, "run", lambda _app, host, port: served.append((host, port)))
    main_module.main()
    assert served == [("127.0.0.1", 8000)]


def test_module_entry_point_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(main_module, "main", lambda: calls.append(True))
    runpy.run_module("r2_uploads_mcp", run_name="__main__")
    assert calls == [True]


@pytest.mark.anyio
async def test_stdio_subprocess_signs_without_touching_the_network() -> None:
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "r2_uploads_mcp"], env=REQUIRED
    )
    async with Client(parameters) as client:
        listed = await client.list_tools()
        created = await client.call_tool("r2_create_upload", {"path": "brand-b.mp4"})
    assert len(listed.tools) == 2
    assert not created.is_error
