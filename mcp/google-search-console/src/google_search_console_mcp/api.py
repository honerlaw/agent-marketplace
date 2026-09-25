"""Thin async client for the Search Console API.

Callers never supply a path. Every URL is built here from a fixed template, and each
caller value that lands in a path (`site_url`, `feedpath`) becomes exactly one segment:
it is percent-encoded, so "/", "?" and "#" cannot split it, and the three values that
encoding leaves special ("", "." and "..", which URL resolution collapses into a
different path) are refused. That is the server's security boundary on the Google side.
"""

from urllib.parse import quote

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from google_search_console_mcp.config import Settings
from google_search_console_mcp.credentials import TokenSource

BASE_URL = "https://searchconsole.googleapis.com"
UNSAFE_SEGMENTS = frozenset({"", ".", ".."})
SITES = "/webmasters/v3/sites"
INSPECT_PATH = "/v1/urlInspection/index:inspect"

JsonObject = dict[str, object]


def segment(value: str) -> str:
    """Percent-encode `value` so it is exactly one path segment, refusing dot segments."""
    if value in UNSAFE_SEGMENTS:
        message = f"{value!r} is not a site URL or sitemap URL"
        raise ToolError(message)
    return quote(value, safe="")


def site_path(site_url: str, *rest: str) -> str:
    """Return `/webmasters/v3/sites/{site_url}/...` with every part encoded."""
    return "/".join([SITES, segment(site_url), *(segment(part) for part in rest)])


class SearchConsoleApi:
    """Sends requests to the Search Console API with a fresh OAuth access token."""

    def __init__(
        self,
        settings: Settings,
        tokens: TokenSource,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._tokens = tokens
        self._client = httpx2.AsyncClient(
            base_url=BASE_URL, timeout=settings.timeout_seconds, transport=transport
        )

    async def call(
        self,
        method: str,
        path: str,
        body: JsonObject | None = None,
        params: dict[str, str] | None = None,
    ) -> JsonObject:
        """Send one request and return its JSON body, raising ToolError on failure."""
        headers = {"Authorization": f"Bearer {await self._tokens.token()}"}
        try:
            response = await self._client.request(
                method, path, json=body, params=params, headers=headers
            )
        except httpx2.HTTPError as error:
            message = f"could not reach the Search Console API: {error!r}"
            raise ToolError(message) from error
        return describe_response(response)


def describe_response(response: httpx2.Response) -> JsonObject:
    """Return a successful response's JSON object, or raise ToolError with Google's message."""
    if response.is_error:
        message = f"Search Console API returned {response.status_code}: {_error_message(response)}"
        raise ToolError(message)
    if not response.content:
        return {"status": response.status_code}
    try:
        payload = response.json()
    except ValueError:
        return {"status": response.status_code, "text": response.text}
    return payload if isinstance(payload, dict) else {"result": payload}


def _error_message(response: httpx2.Response) -> str:
    try:
        error = response.json()["error"]
        return str(error["message"])
    except (ValueError, KeyError, TypeError):
        return response.text
