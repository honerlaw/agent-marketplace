"""Command-line entry point: `microsoft-ads-mcp` or `python -m microsoft_ads_mcp`."""

import logging
import os

import uvicorn

from microsoft_ads_mcp.config import load_settings
from microsoft_ads_mcp.http_app import build_http_app
from microsoft_ads_mcp.server import build_server

# These log every request URL at INFO. No credential travels in a Microsoft URL, but they
# stay at WARNING so a future one cannot leak through a log line.
QUIET_LOGGERS = ("httpx", "httpx2", "httpcore", "httpcore2")


def quiet_http_loggers() -> None:
    """Keep the HTTP client libraries from logging request URLs."""
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def main() -> None:
    """Start the server on the transport chosen by MCP_TRANSPORT."""
    quiet_http_loggers()
    settings = load_settings(os.environ)
    server = build_server(settings)
    if settings.transport == "stdio":
        server.run("stdio")
        return
    uvicorn.run(build_http_app(server, settings), host=settings.host, port=settings.port)
