"""Guards that keep the API key pointed at the configured OpenAI base URL.

Every tool that takes a `path` passes it through `check_path`, every
caller-supplied header set through `check_headers`, and every server-local file
path through `check_local_file`. Keep this module small:
it is the security boundary of the server.
"""

from collections.abc import Mapping
from urllib.parse import unquote

from mcp.server.mcpserver.exceptions import ToolError

PROTECTED_HEADERS = frozenset({"authorization", "host", "openai-organization", "openai-project"})
FORBIDDEN_PATH_CHARACTERS = ("?", "#", "\\")


def check_path(path: str) -> str:
    """Return `path` if it is a plain relative API path, else raise ToolError."""
    decoded = unquote(path)
    if not decoded.startswith("/") or decoded.startswith("//"):
        message = f"path must start with a single '/', got {path!r}"
        raise ToolError(message)
    if "://" in decoded or any(char in decoded for char in FORBIDDEN_PATH_CHARACTERS):
        message = f"path must be a relative API path without query or fragment, got {path!r}"
        raise ToolError(message)
    if ".." in decoded.split("/"):
        message = f"path must not contain '..' segments, got {path!r}"
        raise ToolError(message)
    return path


def check_local_file(path: str | None, *, allowed: bool) -> str | None:
    """Return `path` unless server-local file access is disabled (http mode)."""
    if path is not None and not allowed:
        message = (
            "server-local file paths are disabled over HTTP; "
            "send content_base64 instead of local_path, and omit save_to"
        )
        raise ToolError(message)
    return path


def check_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Return caller headers, refusing any that would override credentials or routing."""
    supplied = dict(headers or {})
    blocked = sorted(name for name in supplied if name.lower() in PROTECTED_HEADERS)
    if blocked:
        message = f"these headers are set by the server and cannot be overridden: {blocked}"
        raise ToolError(message)
    return supplied
