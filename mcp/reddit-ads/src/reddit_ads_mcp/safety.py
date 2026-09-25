"""Guards that keep Reddit credentials pointed at the configured Ads API base URL.

Every tool that takes a `path` passes it through `check_path`, every pagination
URL through `check_page_url`, and every caller-supplied header set through
`check_headers`. Keep this module small: it is the security boundary of the
server.
"""

from collections.abc import Mapping
from urllib.parse import unquote, urlsplit

from mcp.server.mcpserver.exceptions import ToolError

PROTECTED_HEADERS = frozenset({"authorization", "host", "user-agent"})
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


def check_page_url(url: str, base_url: str) -> str:
    """Return `url` if it is a pagination URL under `base_url`, else raise ToolError.

    Scheme and host (with any userinfo or port) must equal the base URL's exactly,
    the path must sit under the base path and pass `check_path`, and there may be
    no fragment. The query string is Reddit's and is kept as-is.
    """
    target, base = urlsplit(url), urlsplit(base_url)
    base_path = base.path.rstrip("/")
    same_origin = (target.scheme, target.netloc) == (base.scheme, base.netloc)
    if not same_origin or not target.path.startswith(f"{base_path}/") or "#" in url:
        message = f"url must be a pagination URL under {base_url}, got {url!r}"
        raise ToolError(message)
    check_path(target.path.removeprefix(base_path))
    return url


def check_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Return caller headers, refusing any that would override credentials or identity."""
    supplied = dict(headers or {})
    blocked = sorted(name for name in supplied if name.lower() in PROTECTED_HEADERS)
    if blocked:
        message = f"these headers are set by the server and cannot be overridden: {blocked}"
        raise ToolError(message)
    return supplied
