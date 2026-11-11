"""Guards that keep the secret key pointed at the Clerk Backend API, and only there.

`clerk_request` passes its method through `check_method`, its path through `check_path`
and its query through `check_query` before anything is sent. Keep this module small: it
is the security boundary of the server.
"""

from collections.abc import Mapping
from string import ascii_letters, digits

from mcp.server.mcpserver.exceptions import ToolError

METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
READ_METHOD = "GET"
# Clerk's path templates and ids use letters, digits and these; `%` is left out on purpose
# so no encoded form (`%2e`, `%2f`, `%252e`) can reach the HTTP client.
PATH_CHARACTERS = frozenset(ascii_letters + digits + "/-._~:@!$&'()*+,;=")
DOT_SEGMENTS = frozenset({"", ".", ".."})
VERSION_QUERY_KEY = "__clerk_api_version"

QueryValue = str | int | float | bool | list[str]


def check_method(method: str, *, read_only: bool) -> str:
    """Return `method` upper-cased if it is allowed, else raise ToolError."""
    upper = method.upper()
    if upper not in METHODS:
        message = f"method must be one of {sorted(METHODS)}, got {method!r}"
        raise ToolError(message)
    if read_only and upper != READ_METHOD:
        message = f"this server is read-only (CLERK_READ_ONLY): only GET is allowed, got {upper}"
        raise ToolError(message)
    return upper


def check_path(path: str) -> str:
    """Return `path` if it is a plain path under /v1, else raise ToolError."""
    if not path.startswith("/") or "://" in path:
        message = f"path must start with '/' and be relative to /v1, got {path!r}"
        raise ToolError(message)
    refused = sorted(set(path) - PATH_CHARACTERS)
    if refused:
        message = f"path must not contain {refused} (no query, fragment or encoding): {path!r}"
        raise ToolError(message)
    if any(segment in DOT_SEGMENTS for segment in path.split("/")[1:]):
        message = f"path must not contain empty, '.' or '..' segments, got {path!r}"
        raise ToolError(message)
    return path


def check_query(query: Mapping[str, QueryValue] | None) -> dict[str, QueryValue]:
    """Return the query, refusing a key that would override the pinned API version."""
    supplied = dict(query or {})
    if any(key.lower() == VERSION_QUERY_KEY for key in supplied):
        message = f"the server pins the API version; {VERSION_QUERY_KEY!r} cannot be set"
        raise ToolError(message)
    return supplied
