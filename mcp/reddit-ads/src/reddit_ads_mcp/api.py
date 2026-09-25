"""Thin async client for the Reddit Ads API, and conversion of its responses."""

from dataclasses import dataclass, field

import httpx2

from reddit_ads_mcp.auth import AccessTokens
from reddit_ads_mcp.config import Settings
from reddit_ads_mcp.safety import check_headers, check_page_url, check_path

JsonObject = dict[str, object]
FormValue = str | int | float | bool | list[str]

FORWARDED_HEADERS = frozenset({"content-type", "ratelimit", "ratelimit-policy", "retry-after"})


@dataclass(frozen=True)
class JsonRequest:
    """A JSON request as the `reddit_ads_request` tool receives it."""

    method: str
    path: str
    query: dict[str, FormValue] | None = None
    body: JsonObject | None = None
    headers: dict[str, str] | None = None


@dataclass(frozen=True)
class _Outgoing:
    method: str
    url: str
    query: dict[str, FormValue] | None = None
    body: JsonObject | None = None
    headers: dict[str, str] = field(default_factory=dict)


class RedditAdsApi:
    """Sends requests to the configured base URL with a current access token."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._base_url = settings.base_url
        self._client = httpx2.AsyncClient(
            base_url=settings.base_url,
            headers={"User-Agent": settings.user_agent},
            timeout=settings.timeout_seconds,
            transport=transport,
        )
        self._tokens = AccessTokens(settings, self._client)

    async def send_json(self, request: JsonRequest) -> JsonObject:
        """Send a JSON request and describe the response."""
        headers = check_headers(request.headers)
        path = check_path(request.path)
        return await self._send(
            _Outgoing(request.method, path, request.query, request.body, headers)
        )

    async def follow_page(self, url: str, method: str, body: JsonObject | None) -> JsonObject:
        """Request a pagination URL from an earlier response, exactly as Reddit gave it."""
        return await self._send(_Outgoing(method, check_page_url(url, self._base_url), body=body))

    async def _send(self, outgoing: _Outgoing) -> JsonObject:
        """Send once; on a 401 with a refreshable token, refresh and send exactly once more."""
        token = await self._tokens.get()
        response = await self._request(outgoing, token)
        if response.status_code == httpx2.codes.UNAUTHORIZED and self._tokens.refreshable:
            self._tokens.invalidate(token)
            response = await self._request(outgoing, await self._tokens.get())
        return describe_response(response)

    async def _request(self, outgoing: _Outgoing, token: str) -> httpx2.Response:
        return await self._client.request(
            outgoing.method,
            outgoing.url,
            params=outgoing.query,
            json=outgoing.body,
            headers={**outgoing.headers, "Authorization": f"Bearer {token}"},
        )


def describe_response(response: httpx2.Response) -> JsonObject:
    """Turn an HTTP response into a JSON-friendly result for the model."""
    result: JsonObject = {"status": response.status_code, "headers": _forwarded(response)}
    if "json" in response.headers.get("content-type", ""):
        result["json"] = _json_or_text(response)
    else:
        result["text"] = response.text
    return result


def _forwarded(response: httpx2.Response) -> dict[str, str]:
    return {name: value for name, value in response.headers.items() if name in FORWARDED_HEADERS}


def _json_or_text(response: httpx2.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return response.text
