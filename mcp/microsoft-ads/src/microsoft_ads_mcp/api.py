"""Thin async client for the Microsoft Advertising REST API.

A call names an operation; method, host and path come from the catalog and the fixed
host table, so the caller never supplies a URL, a path or a header.
"""

import json
from dataclasses import dataclass

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp.auth import AccessTokens
from microsoft_ads_mcp.catalog import OperationCatalog
from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.safety import check_id
from microsoft_ads_mcp.transfer import USER_AGENT, JsonObject, read_bounded

TRACKING_HEADER = "x-ms-trackingid"
# AdApiFaultDetail codes meaning the access token was not accepted: 105
# InvalidCredentials and 109 (the token expired). One refresh and retry is worth it, unless
# the token is brand new: 105 also means an inactive account, which no refresh fixes.
TOKEN_REJECTED_CODES = frozenset({105, 109})


@dataclass(frozen=True)
class ApiRequest:
    """A call as the `microsoft_ads_request` tool receives it."""

    operation: str
    body: JsonObject | None = None
    customer_id: str | None = None
    account_id: str | None = None


class MicrosoftAdsApi:
    """Sends catalog operations to their service host with a current access token."""

    def __init__(
        self,
        settings: Settings,
        catalog: OperationCatalog,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._settings = settings
        self._catalog = catalog
        self._client = httpx2.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=settings.timeout_seconds,
            transport=transport,
        )
        self.tokens = AccessTokens(settings, self._client)

    async def call(self, request: ApiRequest) -> JsonObject:
        """Send one operation and describe the response; retry once on a rejected token."""
        _, entry = self._catalog.operation(request.operation)
        url = self._settings.service_url(entry["service"]) + entry["path"]
        headers = self._identity(request)
        token = await self.tokens.get()
        response, body = await self._send(entry["method"], url, headers, request.body, token)
        if _token_rejected(response, body) and self.tokens.invalidate(token):
            token = await self.tokens.get()
            response, body = await self._send(entry["method"], url, headers, request.body, token)
        return describe_response(response, body)

    def _identity(self, request: ApiRequest) -> dict[str, str]:
        """DeveloperToken plus CustomerId / CustomerAccountId, each omitted when unknown."""
        customer = request.customer_id or self._settings.customer_id
        account = request.account_id or self._settings.account_id
        headers = {"DeveloperToken": self._settings.credentials.developer_token or ""}
        if customer is not None:
            headers["CustomerId"] = check_id("customer_id", customer)
        if account is not None:
            headers["CustomerAccountId"] = check_id("account_id", account)
        return headers

    async def _send(
        self, method: str, url: str, headers: dict[str, str], body: JsonObject | None, token: str
    ) -> tuple[httpx2.Response, bytes]:
        # Every verb carries a JSON body, DELETE included (Microsoft's deletes take ids in it).
        try:
            async with self._client.stream(
                method,
                url,
                json=body if body is not None else {},
                headers={**headers, "Authorization": f"Bearer {token}"},
            ) as response:
                limit = self._settings.max_response_bytes
                return response, await read_bounded(response, limit, lambda: _too_large(limit))
        except httpx2.HTTPError as error:
            message = f"request to Microsoft Advertising failed: {type(error).__name__}: {error}"
            raise ToolError(message) from error


def describe_response(response: httpx2.Response, body: bytes) -> JsonObject:
    """Turn an HTTP response into a JSON-friendly result for the model."""
    result: JsonObject = {"status": response.status_code}
    tracking = response.headers.get(TRACKING_HEADER)
    if tracking is not None:
        result["tracking_id"] = tracking
    text = body.decode("utf-8", errors="replace")
    parsed = _json_or_none(text)
    if parsed is not None:
        result["json"] = parsed
    else:
        result["text"] = text
    return result


def _token_rejected(response: httpx2.Response, body: bytes) -> bool:
    """Tell whether a 401's AdApiFaultDetail says the access token was not accepted."""
    if response.status_code != httpx2.codes.UNAUTHORIZED:
        return False
    fault = _json_or_none(body.decode("utf-8", errors="replace"))
    errors = fault.get("Errors") if isinstance(fault, dict) else None
    first = errors[0] if isinstance(errors, list) and errors else None
    return isinstance(first, dict) and first.get("Code") in TOKEN_REJECTED_CODES


def _json_or_none(text: str) -> object:
    try:
        parsed: object = json.loads(text)
    except ValueError:
        return None
    return parsed


def _too_large(limit: int) -> ToolError:
    message = (
        f"the response was larger than {limit} bytes (MICROSOFT_ADS_MAX_RESPONSE_BYTES), so "
        "it was not returned. Ask for fewer ids per call. For a large account, use Bulk's "
        "DownloadCampaignsByCampaignIds for a few campaigns at a time with only the "
        "DownloadEntities you need, and read the file with microsoft_ads_download_file "
        "(the same limit applies to the unpacked file); or raise the limit."
    )
    return ToolError(message)
