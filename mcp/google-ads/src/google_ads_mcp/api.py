"""Thin async client for the Google Ads REST API, and conversion of its responses."""

import json
from dataclasses import dataclass

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from google_ads_mcp.config import Settings
from google_ads_mcp.credentials import TokenSource
from google_ads_mcp.safety import check_headers, check_path

JsonObject = dict[str, object]
FormValue = str | int | float | bool | list[str]

FORWARDED_HEADERS = frozenset({"content-type", "request-id"})
USER_AGENT = "google-ads-mcp/0.1.0"


@dataclass(frozen=True)
class JsonRequest:
    """A JSON request as the `google_ads_request` tool receives it."""

    method: str
    path: str
    query: dict[str, FormValue] | None = None
    body: JsonObject | None = None
    headers: dict[str, str] | None = None


class GoogleAdsApi:
    """Sends requests to the versioned Google Ads base URL with a current access token."""

    def __init__(
        self,
        settings: Settings,
        tokens: TokenSource,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._base_url = settings.base_url
        self._default_headers = _default_headers(settings)
        self._max_response_bytes = settings.max_response_bytes
        self._tokens = tokens
        self._client = httpx2.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def send_json(self, request: JsonRequest) -> JsonObject:
        """Send a JSON request and describe the response."""
        headers = {**self._default_headers, **check_headers(request.headers)}
        # Joined as text, not by httpx's base_url: a version-level method is `v26:verb`,
        # which `base_url` joining would turn into `v26/:verb`. The host is a fixed prefix.
        url = self._base_url + check_path(request.path)
        token = await self._tokens.token()
        try:
            async with self._client.stream(
                request.method,
                url,
                params=request.query,
                json=request.body,
                headers={**headers, "Authorization": f"Bearer {token}"},
            ) as response:
                body = await self._read_bounded(response)
        except httpx2.HTTPError as error:
            message = f"request to the Google Ads API failed: {type(error).__name__}: {error}"
            raise ToolError(message) from error
        return describe_response(response, body)

    async def _read_bounded(self, response: httpx2.Response) -> bytes:
        """Read the body, giving up as soon as it passes the configured limit."""
        chunks: list[bytes] = []
        size = 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > self._max_response_bytes:
                raise _too_large(self._max_response_bytes)
            chunks.append(chunk)
        return b"".join(chunks)


def describe_response(response: httpx2.Response, body: bytes) -> JsonObject:
    """Turn an HTTP response into a JSON-friendly result for the model."""
    result: JsonObject = {"status": response.status_code, "headers": _forwarded(response)}
    text = body.decode("utf-8", errors="replace")
    if "json" in response.headers.get("content-type", ""):
        result["json"] = _json_or_text(text)
    else:
        result["text"] = text
    return result


def _default_headers(settings: Settings) -> dict[str, str]:
    if settings.login_customer_id is None:
        return {}
    return {"login-customer-id": settings.login_customer_id}


def _too_large(limit: int) -> ToolError:
    message = (
        f"the response was larger than {limit} bytes (GOOGLE_ADS_MAX_RESPONSE_BYTES), so it "
        "was not returned. Use POST /customers/{customerId}/googleAds:search with a smaller "
        "pageSize and follow nextPageToken, select fewer fields, or narrow the WHERE clause; "
        "prefer googleAds:search over googleAds:searchStream."
    )
    return ToolError(message)


def _forwarded(response: httpx2.Response) -> dict[str, str]:
    return {name: value for name, value in response.headers.items() if name in FORWARDED_HEADERS}


def _json_or_text(text: str) -> object:
    try:
        parsed: object = json.loads(text)
    except ValueError:
        return text
    return parsed
