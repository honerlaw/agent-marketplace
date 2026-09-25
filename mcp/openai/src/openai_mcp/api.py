"""Thin async client for the OpenAI REST API, and conversion of its responses."""

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from openai_mcp.config import Settings
from openai_mcp.safety import check_headers, check_local_file, check_path

JsonObject = dict[str, object]
FormValue = str | int | float | bool | list[str]

FORWARDED_HEADERS = frozenset(
    {
        "content-type",
        "x-request-id",
        "openai-processing-ms",
        "openai-organization",
        "openai-version",
    }
)
TEXT_CONTENT_TYPES = ("text/", "application/xml", "application/x-ndjson")


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
    """A JSON request as the `openai_request` tool receives it."""

    method: str
    path: str
    query: dict[str, FormValue] | None = None
    body: JsonObject | None = None
    headers: dict[str, str] | None = None


class OpenAIApi:
    """Sends requests to the configured base URL with the server's credentials."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Create the client; `transport` is injectable for tests."""
        self._max_binary_bytes = settings.max_binary_bytes
        self._local_files = settings.transport == "stdio"
        self._client = httpx2.AsyncClient(
            base_url=settings.base_url,
            headers=_auth_headers(settings),
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
        return describe_response(response, self._max_binary_bytes)

    async def send_multipart(
        self, path: str, fields: dict[str, FormValue], files: list[FileInput]
    ) -> JsonObject:
        """POST a multipart/form-data request and describe the response."""
        for item in files:
            check_local_file(item.local_path, allowed=self._local_files)
        parts = [(item.field, (item.filename, item.read(), item.content_type)) for item in files]
        response = await self._client.post(check_path(path), data=fields, files=parts)
        return describe_response(response, self._max_binary_bytes)

    async def download(self, path: str, save_to: str | None) -> JsonObject:
        """GET binary content, returning it inline or writing it to a server-local file."""
        check_local_file(save_to, allowed=self._local_files)
        if save_to is None:
            response = await self._client.get(check_path(path))
            return describe_response(response, self._max_binary_bytes)
        async with self._client.stream("GET", check_path(path)) as response:
            if response.is_error:
                await response.aread()
                return describe_response(response, self._max_binary_bytes)
            return await _save_stream(response, Path(save_to))


def describe_response(response: httpx2.Response, max_binary_bytes: int) -> JsonObject:
    """Turn an HTTP response into a JSON-friendly result for the model."""
    result: JsonObject = {"status": response.status_code, "headers": _forwarded(response)}
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        result["json"] = _json_or_text(response)
    elif content_type.startswith(TEXT_CONTENT_TYPES) or not response.content:
        result["text"] = response.text
    else:
        result["base64"] = _encode_capped(response.content, max_binary_bytes)
    return result


def _auth_headers(settings: Settings) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    if settings.organization:
        headers["OpenAI-Organization"] = settings.organization
    if settings.project:
        headers["OpenAI-Project"] = settings.project
    return headers


def _forwarded(response: httpx2.Response) -> dict[str, str]:
    return {
        name: value
        for name, value in response.headers.items()
        if name in FORWARDED_HEADERS or name.startswith("x-ratelimit-")
    }


def _json_or_text(response: httpx2.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return response.text


def _encode_capped(content: bytes, max_binary_bytes: int) -> str:
    if len(content) > max_binary_bytes:
        message = (
            f"binary response is {len(content)} bytes, over the {max_binary_bytes}-byte limit; "
            "for GET endpoints use openai_download with save_to (stdio only); "
            "otherwise raise OPENAI_MCP_MAX_BINARY_BYTES"
        )
        raise ToolError(message)
    return base64.b64encode(content).decode("ascii")


def _decode_base64(content: str, filename: str) -> bytes:
    try:
        return base64.b64decode(content, validate=True)
    except binascii.Error as error:
        message = f"file {filename!r}: content_base64 is not valid base64"
        raise ToolError(message) from error


async def _save_stream(response: httpx2.Response, target: Path) -> JsonObject:
    await anyio.Path(target.parent).mkdir(parents=True, exist_ok=True)
    written = 0
    async with await anyio.open_file(target, "wb") as handle:
        async for chunk in response.aiter_bytes():
            written += await handle.write(chunk)
    return {"status": response.status_code, "saved_to": str(target), "bytes": written}
