"""Guards that keep Google credentials pointed at the Google Ads API.

Every tool that takes a `path` passes it through `check_path`, and every caller-supplied
header set through `check_headers`. Keep this module small: it is the security boundary
of the server.
"""

from collections.abc import Mapping
from urllib.parse import unquote

from mcp.server.mcpserver.exceptions import ToolError

from google_ads_mcp.config import normalize_customer_id

PROTECTED_HEADERS = frozenset({"authorization", "host", "user-agent"})
CUSTOMER_ID_HEADERS = frozenset({"login-customer-id", "linked-customer-id"})
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


def check_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Return caller headers with names lower-cased and customer ids as bare digits.

    Headers that would override credentials or identity are refused, as is a customer-id
    header that is not a customer id.
    """
    supplied = {name.lower(): value for name, value in (headers or {}).items()}
    blocked = sorted(name for name in supplied if name in PROTECTED_HEADERS)
    if blocked:
        message = f"these headers are set by the server and cannot be overridden: {blocked}"
        raise ToolError(message)
    return {name: _customer_id(name, value) for name, value in supplied.items()}


def _customer_id(name: str, value: str) -> str:
    if name not in CUSTOMER_ID_HEADERS:
        return value
    normalized = normalize_customer_id(value)
    if normalized is None:
        message = f"{name} must be a customer id like 123-456-7890, got {value!r}"
        raise ToolError(message)
    return normalized
