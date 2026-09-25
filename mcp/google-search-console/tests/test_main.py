"""The entry point, including a real stdio subprocess."""

import os
import runpy
import sys

import pytest
import uvicorn
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import MCPServer

from google_search_console_mcp import main as main_module


def test_stdio_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setattr(MCPServer, "run", lambda _self, transport: started.append(transport))
    main_module.main()
    assert started == ["stdio"]


def test_http_mode_serves_with_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    served: list[tuple[str, int]] = []
    env = {"MCP_TRANSPORT": "http", "MCP_AUTH_TOKEN": "t"}
    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(uvicorn, "run", lambda _app, host, port: served.append((host, port)))
    main_module.main()
    assert served == [("127.0.0.1", 8000)]


def test_module_entry_point_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(main_module, "main", lambda: calls.append(True))
    runpy.run_module("google_search_console_mcp", run_name="__main__")
    assert calls == [True]


@pytest.mark.anyio
async def test_stdio_subprocess_starts_without_google_credentials() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "google_search_console_mcp"],
        env={"GSC_READ_ONLY": "true", "GSC_CREDENTIALS_JSON": '{"type": "external_account"}'},
    )
    async with Client(parameters) as client:
        listed = await client.list_tools()
        refused = await client.call_tool("gsc_list_sites", {})
    assert len(listed.tools) == 6
    assert refused.is_error
