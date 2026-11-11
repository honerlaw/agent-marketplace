"""Command-line entry point: `clerk-mcp` or `python -m clerk_mcp`."""

import os

import uvicorn

from clerk_mcp.config import load_settings
from clerk_mcp.http_app import build_http_app
from clerk_mcp.server import build_server


def main() -> None:
    """Start the server on the transport chosen by MCP_TRANSPORT."""
    settings = load_settings(os.environ)
    server = build_server(settings)
    if settings.transport == "stdio":
        server.run("stdio")
        return
    uvicorn.run(build_http_app(server, settings), host=settings.host, port=settings.port)
