"""Command-line entry point: `openai-ads-mcp` or `python -m openai_ads_mcp`."""

import os

import uvicorn

from openai_ads_mcp.config import load_settings
from openai_ads_mcp.http_app import build_http_app
from openai_ads_mcp.server import build_server


def main() -> None:
    """Start the server on the transport chosen by MCP_TRANSPORT."""
    settings = load_settings(os.environ)
    server = build_server(settings)
    if settings.transport == "stdio":
        server.run("stdio")
        return
    uvicorn.run(build_http_app(server, settings), host=settings.host, port=settings.port)
