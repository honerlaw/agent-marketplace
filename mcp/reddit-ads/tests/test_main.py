"""The entry point, including a real stdio subprocess."""

import os
import runpy
import sys

import pytest
import uvicorn
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import MCPServer

from reddit_ads_mcp import main as main_module
from tests.conftest import FIXTURE_SPEC


def test_stdio_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(os, "environ", {"REDDIT_ACCESS_TOKEN": "t"})
    monkeypatch.setattr(MCPServer, "run", lambda _self, transport: started.append(transport))
    main_module.main()
    assert started == ["stdio"]


def test_http_mode_serves_with_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    served: list[tuple[str, int]] = []
    env = {"REDDIT_ACCESS_TOKEN": "t", "MCP_TRANSPORT": "http", "MCP_AUTH_TOKEN": "t"}
    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(uvicorn, "run", lambda _app, host, port: served.append((host, port)))
    main_module.main()
    assert served == [("127.0.0.1", 8000)]


def test_module_entry_point_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(main_module, "main", lambda: calls.append(True))
    runpy.run_module("reddit_ads_mcp", run_name="__main__")
    assert calls == [True]


@pytest.mark.anyio
async def test_stdio_subprocess_speaks_clean_mcp() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "reddit_ads_mcp"],
        env={"REDDIT_ACCESS_TOKEN": "t", "REDDIT_ADS_OPENAPI_PATH": str(FIXTURE_SPEC)},
    )
    async with Client(parameters) as client:
        listed = await client.list_tools()
        endpoints = await client.call_tool("reddit_ads_list_endpoints", {"text_filter": "me"})
    assert len(listed.tools) == 4
    assert endpoints.structured_content == {"result": ["GET /me — Get Me"]}
