"""Thin async client for the Graph API: credentials in, scrubbed descriptions out."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp.config import Settings
from meta_ads_mcp.safety import check_page_url, check_params, check_path, param_names
from meta_ads_mcp.scrub import Scrubber, appsecret_proof

JsonObject = dict[str, object]
QueryValue = str | int | float | bool | list[object] | dict[str, object]
BodyFormat = Literal["json", "form"]

FORWARDED_HEADERS = frozenset(
    {
        "content-type",
        "x-fb-trace-id",
        "x-fb-request-id",
        "x-business-use-case-usage",
        "x-ad-account-usage",
        "x-app-usage",
    }
)
USER_AGENT = "meta-ads-mcp/0.1.0"


@dataclass(frozen=True)
class GraphRequest:
    """A request as the `meta_ads_request` tool receives it."""

    method: str
    path: str
    query: Mapping[str, QueryValue] | None = None
    body: JsonObject | None = None
    body_format: BodyFormat = "json"


@dataclass(frozen=True)
class _Outgoing:
    method: str
    path: str
    params: list[tuple[str, str]]
    body: JsonObject | None = None
    body_format: BodyFormat = "json"


class MetaAdsApi:
    """Sends requests to the versioned Graph API with the configured system-user token."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._settings = settings
        self._base_url = settings.base_url
        self._max_response_bytes = settings.max_response_bytes
        proof = _proof(settings)
        self.scrubber = Scrubber((*settings.secrets, proof or ""))
        self._proof = proof
        self._client = httpx2.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def send(self, request: GraphRequest) -> JsonObject:
        """Check and send a caller's request, and describe the response."""
        check_params(param_names(request.query), "query")
        check_params(param_names(request.body), "body")
        path = check_path(request.path)
        params = _pairs(request.query)
        outgoing = _Outgoing(request.method, path, params, request.body, request.body_format)
        return await self._send(outgoing, self._token())

    async def follow_page(self, url: str) -> JsonObject:
        """Request a `paging.next` / `previous` URL from an earlier response."""
        path, query = check_page_url(url, self._base_url)
        return await self._send(_Outgoing("GET", path, query), self._token())

    async def debug_token(self) -> JsonObject:
        """Ask Graph about the configured token, authenticated as the app itself."""
        app_id, app_secret = self._settings.app_id, self._settings.app_secret
        if app_id is None or app_secret is None:
            message = "set META_APP_ID and META_APP_SECRET"
            raise ToolError(message)
        query = [("input_token", self._token())]
        return await self._send(_Outgoing("GET", "/debug_token", query), f"{app_id}|{app_secret}")

    async def _send(self, outgoing: _Outgoing, bearer: str) -> JsonObject:
        try:
            body, response = await self._request(outgoing, bearer)
        except httpx2.HTTPError as error:
            message = f"request to the Graph API failed: {type(error).__name__}: {error}"
            raise ToolError(self.scrubber.text(message)) from error
        return self.scrubber.mapping(describe_response(response, body))

    async def _request(self, outgoing: _Outgoing, bearer: str) -> tuple[bytes, httpx2.Response]:
        params = httpx2.QueryParams([*outgoing.params, *self._proof_param(bearer)])
        json_body, form = _body_parts(outgoing)
        async with self._client.stream(
            outgoing.method,
            self._base_url + outgoing.path,
            params=params,
            headers={"Authorization": f"Bearer {bearer}"},
            json=json_body,
            data=form,
        ) as response:
            return await self._read_bounded(response), response

    def _proof_param(self, bearer: str) -> list[tuple[str, str]]:
        """Return the proof parameter: it belongs to the system-user token, not an app token."""
        if self._proof is None or bearer != self._settings.access_token:
            return []
        return [("appsecret_proof", self._proof)]

    def _token(self) -> str:
        if self._settings.access_token is None:
            message = "META_ADS_ACCESS_TOKEN is not set: the server has no Meta credentials"
            raise ToolError(message)
        return self._settings.access_token

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
    """Turn an HTTP response into a JSON-friendly result for the model.

    A body that parses as a JSON object or array is returned as `json` whatever its
    content type, so the scrub's key-level redaction always sees its structure.
    """
    result: JsonObject = {"status": response.status_code, "headers": _forwarded(response)}
    text = body.decode("utf-8", errors="replace")
    parsed = _json_or_text(text)
    declared = "json" in response.headers.get("content-type", "")
    result["json" if declared or isinstance(parsed, (dict, list)) else "text"] = parsed
    return result


def form_fields(body: JsonObject) -> dict[str, str]:
    """Graph's form convention: scalars as text, nested values as JSON."""
    return {name: _form_value(value) for name, value in body.items()}


def _body_parts(outgoing: _Outgoing) -> tuple[JsonObject | None, dict[str, str] | None]:
    if outgoing.body is None:
        return None, None
    if outgoing.body_format == "form":
        return None, form_fields(outgoing.body)
    return outgoing.body, None


def _form_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _pairs(query: Mapping[str, QueryValue] | None) -> list[tuple[str, str]]:
    return [(name, _query_value(value)) for name, value in (query or {}).items()]


def _query_value(value: object) -> str:
    """Graph's query convention: text as is, everything else (lists, objects) as JSON."""
    return value if isinstance(value, str) else json.dumps(value)


def _proof(settings: Settings) -> str | None:
    if settings.access_token is None or settings.app_secret is None:
        return None
    return appsecret_proof(settings.access_token, settings.app_secret)


def _too_large(limit: int) -> ToolError:
    message = (
        f"the response was larger than {limit} bytes (META_ADS_MAX_RESPONSE_BYTES), so it was "
        "not returned. Ask for fewer fields with `fields=`, a smaller `limit`, and follow "
        "paging.next with meta_ads_follow_page."
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
