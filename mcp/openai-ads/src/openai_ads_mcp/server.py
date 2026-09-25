"""The MCP server: four generic tools that together reach the whole OpenAI Ads API."""

from typing import Literal

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from openai_ads_mcp.api import AdsApi, FileInput, FormValue, JsonObject, JsonRequest
from openai_ads_mcp.config import Settings
from openai_ads_mcp.spec import SpecCatalog

INSTRUCTIONS = """\
Manage ChatGPT advertising through the OpenAI Ads (Advertiser) API with the operator's
ad-account API key. The hierarchy is ad account > campaign > ad group > ad: campaigns hold
the objective, budget, schedule and targeting; ad groups hold bidding, context hints and
product sets; ads hold the creative and destination URL.
Paths are relative to the API base URL, e.g. "/campaigns", "/ad_groups/{ad_group_id}".
Unsure how to call an endpoint? Use openai_ads_list_endpoints to find it and
openai_ads_describe_endpoint to read its parameters and body schema, then call it with
openai_ads_request (JSON) or openai_ads_multipart_request (file uploads: creative images to
"/upload", custom-audience files to "/uploads" with purpose "custom_audience").
Lists page with the `limit`, `after` and `before` query parameters.
Money is in micros of the ad account's currency: 50000000 is 50.00.
This API spends real money. Create campaigns, ad groups and ads with status "paused",
and send an "Idempotency-Key" header on create requests so a retry cannot duplicate them.
Confirm with the user before activating anything or changing a budget, bid or spend limit.
"""

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]


def build_server(
    settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
) -> MCPServer:
    """Create the server; `transport` replaces the network in tests."""
    server = MCPServer(name="openai-ads", instructions=INSTRUCTIONS)
    _add_api_tools(server, AdsApi(settings, transport))
    _add_discovery_tools(server, SpecCatalog(settings, transport))
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def _add_api_tools(server: MCPServer, api: AdsApi) -> None:
    @server.tool()
    async def openai_ads_request(
        method: HttpMethod,
        path: str,
        query: dict[str, FormValue] | None = None,
        body: JsonObject | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonObject:
        """Call any OpenAI Ads API endpoint with an optional JSON body.

        `path` is relative to the base URL, e.g. "/campaigns" or
        "/campaigns/{campaign_id}/pause". Returns the status, key response headers
        and the body as json or text. Pass "Idempotency-Key" in `headers` on creates.
        """
        return await api.send_json(JsonRequest(method, path, query, body, headers))

    @server.tool()
    async def openai_ads_multipart_request(
        path: str, files: list[FileInput], fields: dict[str, FormValue] | None = None
    ) -> JsonObject:
        """POST a multipart/form-data upload: an image to "/upload" or a file to "/uploads".

        Each file gives either `content_base64` or `local_path`. A local path is read
        on the server's filesystem and is only allowed over stdio; over HTTP send base64.
        `fields` holds the other form fields. To upload an image that is already
        online, use openai_ads_request with body {"image_url": ...} instead.
        """
        return await api.send_multipart(path, fields or {}, files)


def _add_discovery_tools(server: MCPServer, catalog: SpecCatalog) -> None:
    @server.tool()
    async def openai_ads_list_endpoints(text_filter: str | None = None) -> list[str]:
        """List API operations as "METHOD /path — summary", filtered by substring."""
        return await catalog.list_endpoints(text_filter)

    @server.tool()
    async def openai_ads_describe_endpoint(
        method: HttpMethod, path: str, depth: int = 1
    ) -> JsonObject:
        """Describe one operation: parameters, request body schema and success responses.

        `path` is the templated spec path exactly as listed, e.g. "/ads/{ad_id}".
        Schema `$ref`s are expanded `depth` levels (1-6); unexpanded ones stay as
        "$ref" markers. Start at 1 and go deeper only when a schema is still a marker.
        """
        return await catalog.describe(method, path, depth)
