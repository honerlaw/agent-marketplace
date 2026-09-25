"""The MCP server: five generic tools that together reach the whole OpenAI API."""

from typing import Literal

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from openai_mcp.api import FileInput, JsonObject, JsonRequest, OpenAIApi
from openai_mcp.config import Settings
from openai_mcp.spec import SpecCatalog

INSTRUCTIONS = """\
Full access to the OpenAI REST API with the operator's API key.
Paths are relative to the API base URL, e.g. "/responses", "/models", "/files/{file_id}".
Unsure how to call an endpoint? Use openai_list_endpoints to find it and
openai_describe_endpoint to read its parameters and body schema, then call it with
openai_request (JSON), openai_multipart_request (file uploads) or openai_download
(binary content). Many operations cost money; confirm expensive actions with the user.
"""

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


def build_server(
    settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
) -> MCPServer:
    """Create the server; `transport` replaces the network in tests."""
    server = MCPServer(name="openai", instructions=INSTRUCTIONS)
    _add_api_tools(server, OpenAIApi(settings, transport))
    _add_discovery_tools(server, SpecCatalog(settings, transport))
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def _add_api_tools(server: MCPServer, api: OpenAIApi) -> None:
    @server.tool()
    async def openai_request(
        method: HttpMethod,
        path: str,
        query: dict[str, str] | None = None,
        body: JsonObject | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonObject:
        """Call any OpenAI API endpoint with an optional JSON body.

        `path` is relative to the base URL, e.g. "/chat/completions". Returns the
        status, key response headers, and the body as json, text or base64. With
        `"stream": true` in the body, the raw server-sent events are returned once
        the stream finishes. Extra headers such as "OpenAI-Beta" may be passed.
        """
        return await api.send_json(JsonRequest(method, path, query, body, headers))

    @server.tool()
    async def openai_multipart_request(
        path: str, files: list[FileInput], fields: dict[str, str] | None = None
    ) -> JsonObject:
        """POST a multipart/form-data upload, e.g. "/files" or "/audio/transcriptions".

        Each file gives either `content_base64` or `local_path`. A local path is read
        on the server's filesystem, so remote clients should send base64.
        `fields` holds the other form fields, e.g. {"purpose": "batch"}.
        """
        return await api.send_multipart(path, fields or {}, files)

    @server.tool()
    async def openai_download(path: str, save_to: str | None = None) -> JsonObject:
        """GET binary content, e.g. "/files/{file_id}/content".

        Without `save_to` the content is returned as base64 (up to the size limit).
        With `save_to` it is streamed to that path on the server's filesystem.
        """
        return await api.download(path, save_to)


def _add_discovery_tools(server: MCPServer, catalog: SpecCatalog) -> None:
    @server.tool()
    async def openai_list_endpoints(text_filter: str | None = None) -> list[str]:
        """List API operations as "METHOD /path — summary", filtered by substring."""
        return await catalog.list_endpoints(text_filter)

    @server.tool()
    async def openai_describe_endpoint(method: HttpMethod, path: str, depth: int = 1) -> JsonObject:
        """Describe one operation: parameters, request body schema and success responses.

        `path` is the templated spec path exactly as listed, e.g. "/files/{file_id}".
        Schema `$ref`s are expanded `depth` levels (1-6); unexpanded ones stay as
        "$ref" markers. Large operations such as POST /responses grow quickly with
        depth, so start at 1 and go deeper only when needed.
        """
        return await catalog.describe(method, path, depth)
