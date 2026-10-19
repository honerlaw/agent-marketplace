"""The entry point, including a real stdio subprocess."""

import logging
import os
import runpy
import sys

import pytest
import uvicorn
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import MCPServer

from meta_ads_mcp import main as main_module


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
    runpy.run_module("meta_ads_mcp", run_name="__main__")
    assert calls == [True]


def test_main_quiets_the_http_loggers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setattr(MCPServer, "run", lambda _self, _transport: None)
    for name in main_module.QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.DEBUG)
    main_module.main()
    assert all(
        logging.getLogger(name).level == logging.WARNING for name in main_module.QUIET_LOGGERS
    )


@pytest.mark.anyio
async def test_stdio_subprocess_speaks_clean_mcp() -> None:
    # The subprocess pins the real spec hash, so it calls a tool that needs no specs.
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "meta_ads_mcp"], env={})
    async with Client(parameters) as client:
        listed = await client.list_tools()
        status = await client.call_tool("meta_ads_token_status", {})
    assert len(listed.tools) == 6
    assert status.structured_content is not None
    assert status.structured_content["available"] is False
