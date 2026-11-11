"""Thin async client for the Clerk Backend API, and conversion of its responses."""

import json
from dataclasses import dataclass

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from clerk_mcp.config import Settings
from clerk_mcp.safety import QueryValue, check_method, check_path, check_query
from clerk_mcp.scrub import Scrubber
from clerk_mcp.spec import CLERK_API_VERSION

BASE_URL = "https://api.clerk.com/v1"
MAX_BODY_CHARS = 256 * 1024
JsonObject = dict[str, object]

FORWARDED_HEADERS = frozenset({"content-type", "retry-after"})
RATE_LIMIT_PREFIXES = ("x-ratelimit-", "ratelimit")


@dataclass(frozen=True)
class ClerkRequest:
    """A request as the `clerk_request` tool receives it."""

    method: str
    path: str
    query: dict[str, QueryValue] | None = None
    body: JsonObject | None = None


class ClerkApi:
    """Sends requests to the Clerk Backend API with the server's secret key."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._read_only = settings.read_only
        self._scrub = Scrubber(settings.secret_key)
        self._client = httpx2.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.secret_key}",
                "Clerk-API-Version": CLERK_API_VERSION,
            },
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            transport=transport,
        )

    async def send(self, request: ClerkRequest) -> JsonObject:
        """Check, send and describe one request; nothing is sent if a check fails."""
        method = check_method(request.method, read_only=self._read_only)
        path = check_path(request.path)
        query = check_query(request.query)
        try:
            response = await self._client.request(method, path, params=query, json=request.body)
        except httpx2.HTTPError as error:
            message = self._scrub.text(f"request failed: {error}")
            raise ToolError(message) from None
        return describe_response(response, self._scrub)


def describe_response(response: httpx2.Response, scrub: Scrubber) -> JsonObject:
    """Turn an HTTP response into a scrubbed, size-capped result for the model."""
    headers = {
        name: scrub.text(value)
        for name, value in response.headers.items()
        if name in FORWARDED_HEADERS or name.startswith(RATE_LIMIT_PREFIXES)
    }
    return {"status": response.status_code, "headers": headers, **_body(response, scrub)}


def _body(response: httpx2.Response, scrub: Scrubber) -> JsonObject:
    if "json" in response.headers.get("content-type", ""):
        try:
            parsed = response.json()
        except ValueError:
            return _capped_text(scrub.text(response.text))
        return _capped_json(scrub.value(parsed))
    return _capped_text(scrub.text(response.text))


def _capped_json(value: object) -> JsonObject:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) <= MAX_BODY_CHARS:
        return {"json": value}
    return _capped_text(serialized)


def _capped_text(text: str) -> JsonObject:
    """Cut already-scrubbed text at MAX_BODY_CHARS and say so."""
    if len(text) <= MAX_BODY_CHARS:
        return {"text": text}
    note = (
        f"body cut at {MAX_BODY_CHARS} of {len(text)} characters; ask for less (a smaller `limit`)"
    )
    return {"text": text[:MAX_BODY_CHARS], "truncated": note, "total_chars": len(text)}
