"""Command-line entry point: `r2-uploads-mcp` or `python -m <package>`."""

import logging
import os

import uvicorn

from r2_uploads_mcp.config import load_settings
from r2_uploads_mcp.http_app import build_http_app
from r2_uploads_mcp.server import build_server

# These log every request's full URL at INFO, and the listing URL is presigned (it carries the
# access key id and a signature that lists the bucket until it expires), so they stay at WARNING.
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
