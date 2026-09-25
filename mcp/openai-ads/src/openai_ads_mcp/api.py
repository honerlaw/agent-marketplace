"""Thin async client for the OpenAI Ads API, and conversion of its responses."""

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path

import httpx2
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from openai_ads_mcp.config import Settings
from openai_ads_mcp.safety import check_headers, check_local_file, check_path

JsonObject = dict[str, object]
FormValue = str | int | float | bool | list[str]

FORWARDED_HEADERS = frozenset(
    {
        "content-type",
        "x-request-id",
        "openai-processing-ms",
        "openai-version",
        "retry-after",
    }
)
# The Ads API does not document its rate-limit header names, so forward both
# common spellings: OpenAI's `x-ratelimit-*` and the IETF draft's `ratelimit*`.
RATE_LIMIT_PREFIXES = ("x-ratelimit-", "ratelimit")


class FileInput(BaseModel):
    """One file part of a multipart request: base64 content or a server-local path."""

    field: str = "file"
    filename: str
    content_base64: str | None = None
    local_path: str | None = None
    content_type: str = "application/octet-stream"

    def read(self) -> bytes:
        """Return the file bytes from whichever source was given."""
        if (self.content_base64 is None) == (self.local_path is None):
            message = f"file {self.filename!r}: give exactly one of content_base64 or local_path"
            raise ToolError(message)
        if self.local_path is not None:
            return Path(self.local_path).read_bytes()
        return _decode_base64(self.content_base64 or "", self.filename)


@dataclass(frozen=True)
class JsonRequest:
    """A JSON request as the `openai_ads_request` tool receives it."""

    method: str
    path: str
    query: dict[str, FormValue] | None = None
    body: JsonObject | None = None
    headers: dict[str, str] | None = None


class AdsApi:
    """Sends requests to the configured base URL with the server's API key."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._local_files = settings.transport == "stdio"
        self._client = httpx2.AsyncClient(
            base_url=settings.base_url,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    async def send_json(self, request: JsonRequest) -> JsonObject:
        """Send a JSON request and describe the response."""
        response = await self._client.request(
            request.method,
            check_path(request.path),
            params=request.query,
            json=request.body,
            headers=check_headers(request.headers),
        )
        return describe_response(response)

    async def send_multipart(
        self, path: str, fields: dict[str, FormValue], files: list[FileInput]
    ) -> JsonObject:
        """POST a multipart/form-data request and describe the response."""
        for item in files:
            check_local_file(item.local_path, allowed=self._local_files)
        parts = [(item.field, (item.filename, item.read(), item.content_type)) for item in files]
        response = await self._client.post(check_path(path), data=fields, files=parts)
        return describe_response(response)


def describe_response(response: httpx2.Response) -> JsonObject:
    """Turn an HTTP response into a JSON-friendly result for the model.

    Every documented Ads API response is JSON; anything else comes back as text.
    """
    result: JsonObject = {"status": response.status_code, "headers": _forwarded(response)}
    if "json" in response.headers.get("content-type", ""):
        result["json"] = _json_or_text(response)
    else:
        result["text"] = response.text
    return result


def _forwarded(response: httpx2.Response) -> dict[str, str]:
    return {
        name: value
        for name, value in response.headers.items()
        if name in FORWARDED_HEADERS or name.startswith(RATE_LIMIT_PREFIXES)
    }


def _json_or_text(response: httpx2.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return response.text


def _decode_base64(content: str, filename: str) -> bytes:
    try:
        return base64.b64decode(content, validate=True)
    except binascii.Error as error:
        message = f"file {filename!r}: content_base64 is not valid base64"
        raise ToolError(message) from error
