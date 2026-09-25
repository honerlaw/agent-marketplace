"""The streamable-HTTP app, guarded by a bearer token.

Together with the path encoding in `api.py` this is the server's security boundary: every HTTP
request except the health check must carry `Authorization: Bearer <token>`.
"""

import hmac

from mcp.server.mcpserver import MCPServer
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from google_search_console_mcp.config import Settings

OPEN_PATHS = frozenset({"/healthz"})


class BearerAuth:
    """ASGI middleware rejecting HTTP requests without the expected bearer token."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        """Wrap `app`, requiring `token` on every non-health-check request."""
        self._app = app
        self._expected = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass authorized requests through; answer the rest with 401."""
        if scope["type"] == "lifespan" or scope["path"] in OPEN_PATHS or self._authorized(scope):
            await self._app(scope, receive, send)
            return
        response = JSONResponse({"error": "unauthorized"}, status_code=401)
        await response(scope, receive, send)

    def _authorized(self, scope: Scope) -> bool:
        header = dict(scope["headers"]).get(b"authorization", b"")
        scheme, _, token = header.partition(b" ")
        return scheme.lower() == b"bearer" and hmac.compare_digest(token, self._expected)


def build_http_app(server: MCPServer, settings: Settings) -> ASGIApp:
    """Return the ASGI app to serve, wrapped in bearer auth unless explicitly disabled.

    In stateless mode the SDK keeps no sessions: each request gets a fresh transport
    and no `mcp-session-id`, so any instance can answer any request.
    """
    app = server.streamable_http_app(
        host=settings.host,
        max_request_body_size=settings.max_request_bytes,
        stateless_http=settings.stateless,
    )
    if settings.auth_token is None:
        return app
    return BearerAuth(app, settings.auth_token)
