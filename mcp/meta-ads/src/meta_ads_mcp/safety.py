"""Guards that keep Meta credentials pointed at the Graph API and under the server's control.

Every tool that takes a `path` passes it through `check_path`, every caller-supplied
`query` and `body` through `check_params`, and every pagination URL through
`check_page_url`. Keep this module small: it is the security boundary of the server.
"""

import re
from collections.abc import Callable, Iterable, Mapping
from urllib.parse import parse_qsl, unquote, urlsplit

from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp.config import API_HOST

# Parameters the server owns, or that would bypass the guards: credentials (the server
# sets them), `batch` (each item carries its own unguarded relative URL), `method` (Graph
# turns a request into another verb), and `suppress_http_code` / `callback` (they change
# what a response means). Graph reads them as top-level names, also with a `[...]` suffix.
REFUSED_PARAMS = frozenset(
    {"access_token", "appsecret_proof", "batch", "method", "suppress_http_code", "callback"}
)
# Meta writes its own credentials into pagination URLs; they are dropped and re-added.
CREDENTIAL_PARAMS = frozenset({"access_token", "appsecret_proof"})
FORBIDDEN_PATH_CHARACTERS = ("?", "#", "\\")
DOT_SEGMENTS = frozenset({".", ".."})
PRINTABLE_ASCII = re.compile(r"[!-~]+")
PATH_RULES: tuple[tuple[Callable[[str], bool], str], ...] = (
    (lambda path: PRINTABLE_ASCII.fullmatch(path) is not None, "path must be printable ASCII"),
    (
        lambda path: path.startswith("/") and not path.startswith("//"),
        "path must start with a single '/'",
    ),
    (lambda path: path != "/", "path must name a node or edge; batch requests are not supported"),
    (
        lambda path: "://" not in path and not any(c in path for c in FORBIDDEN_PATH_CHARACTERS),
        "path must be a relative API path without query or fragment",
    ),
    (lambda path: DOT_SEGMENTS.isdisjoint(path.split("/")), "path must not contain . or .."),
)
QueryPairs = list[tuple[str, str]]


def check_path(path: str) -> str:
    """Return `path` if it is a plain relative Graph path, else raise ToolError.

    The rules run on the path decoded once and decoded twice, so `%2e%2e` and
    `%252e%252e` are refused like `..`.
    """
    for decoded in (unquote(path), unquote(unquote(path))):
        for allowed, message in PATH_RULES:
            if not allowed(decoded):
                refusal = f"{message}, got {path!r}"
                raise ToolError(refusal)
    return path


def check_params(names: Iterable[str], where: str) -> None:
    """Refuse any parameter name the server owns or that would bypass a guard."""
    refused = sorted({name for name in names if _base_name(name) in REFUSED_PARAMS})
    if refused:
        message = (
            f"{where} may not set {refused}: credentials are the server's, and batch, "
            "method, suppress_http_code and callback are not supported"
        )
        raise ToolError(message)


def check_page_url(url: str, base_url: str) -> tuple[str, QueryPairs]:
    """Split a pagination URL under `base_url` into a checked path and query.

    The URL must be https on the Graph host with no userinfo, port or fragment, under the
    configured version. Meta's own `access_token` / `appsecret_proof` are dropped (the
    server adds its own); every other parameter must pass `check_params`.
    """
    target = urlsplit(url)
    base_path = urlsplit(base_url).path
    origin_ok = target.scheme == "https" and target.netloc.lower() == API_HOST
    if not origin_ok or "#" in url or not target.path.startswith(f"{base_path}/"):
        message = f"url must be a Graph pagination URL under {base_url}, got {url!r}"
        raise ToolError(message)
    query = [
        (name, value)
        for name, value in parse_qsl(target.query, keep_blank_values=True)
        if _base_name(name) not in CREDENTIAL_PARAMS
    ]
    check_params((name for name, _ in query), "url")
    return check_path(target.path.removeprefix(base_path)), query


def param_names(params: Mapping[str, object] | None) -> list[str]:
    """Return the top-level names of a query or body mapping."""
    return list((params or {}).keys())


def _base_name(name: str) -> str:
    return name.split("[", 1)[0].strip().lower()
