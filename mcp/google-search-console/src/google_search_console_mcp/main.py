"""Command-line entry point: `google-search-console-mcp` or `python -m <package>`."""

import os

import uvicorn

from google_search_console_mcp.config import load_settings
from google_search_console_mcp.http_app import build_http_app
from google_search_console_mcp.server import build_server


def main() -> None:
    """Start the server on the transport chosen by MCP_TRANSPORT."""
    settings = load_settings(os.environ)
    server = build_server(settings)
    if settings.transport == "stdio":
        server.run("stdio")
        return
    uvicorn.run(build_http_app(server, settings), host=settings.host, port=settings.port)
