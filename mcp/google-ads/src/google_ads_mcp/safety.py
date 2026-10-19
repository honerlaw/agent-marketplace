"""Guards that keep Google credentials pointed at the Google Ads API.

Every tool that takes a `path` passes it through `check_path`, and every caller-supplied
header set through `check_headers`. Keep this module small: it is the security boundary
of the server.
"""

import re
from collections.abc import Callable, Mapping
from urllib.parse import unquote

from mcp.server.mcpserver.exceptions import ToolError

from google_ads_mcp.config import normalize_customer_id

ALLOWED_HEADERS = frozenset({"login-customer-id", "linked-customer-id"})
FORBIDDEN_PATH_CHARACTERS = ("?", "#", "\\")
VERSION_LEVEL_METHOD = re.compile(r":[A-Za-z]+")
PRINTABLE_ASCII = re.compile(r"[!-~]+")
PATH_RULES: tuple[tuple[Callable[[str], bool], str], ...] = (
    (lambda path: PRINTABLE_ASCII.fullmatch(path) is not None, "path must be printable ASCII"),
    (
        lambda path: path.startswith("/") and not path.startswith("//"),
        "path must start with a single '/' (or be a method like ':listPlannableLocations')",
    ),
    (
        lambda path: "://" not in path and not any(c in path for c in FORBIDDEN_PATH_CHARACTERS),
        "path must be a relative API path without query or fragment",
    ),
    (lambda path: ".." not in path.split("/"), "path must not contain '..' segments"),
)


def check_path(path: str) -> str:
    """Return `path` if it is a plain relative API path, else raise ToolError.

    A path is either `/...` under the versioned base URL or a bare version-level method
    such as `:listPlannableLocations` (sent as `.../v26:listPlannableLocations`).
    """
    if VERSION_LEVEL_METHOD.fullmatch(path):
        return path
    decoded = unquote(path)
    for allowed, message in PATH_RULES:
        if not allowed(decoded):
            refusal = f"{message}, got {path!r}"
            raise ToolError(refusal)
    return path


def check_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    """Return caller headers with names lower-cased and customer ids as bare digits.

    Only the two customer-id headers may be set, an allowlist: every other header is the
    server's (credentials, identity, framing, encoding), and each value must be an id.
    """
    supplied = {name.lower(): value for name, value in (headers or {}).items()}
    refused = sorted(name for name in supplied if name not in ALLOWED_HEADERS)
    if refused:
        allowed = sorted(ALLOWED_HEADERS)
        message = f"only {allowed} may be set; these are the server's: {refused}"
        raise ToolError(message)
    return {name: _customer_id(name, value) for name, value in supplied.items()}


def _customer_id(name: str, value: str) -> str:
    normalized = normalize_customer_id(value)
    if normalized is None:
        message = f"{name} must be a customer id like 123-456-7890, got {value!r}"
        raise ToolError(message)
    return normalized
