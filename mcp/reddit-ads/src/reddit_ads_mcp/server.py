"""The MCP server: four generic tools that together reach the whole Reddit Ads API."""

from typing import Literal

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from reddit_ads_mcp.api import FormValue, JsonObject, JsonRequest, RedditAdsApi
from reddit_ads_mcp.config import Settings
from reddit_ads_mcp.spec import SpecCatalog

INSTRUCTIONS = """\
Full access to the Reddit Ads API (v3) with the operator's Reddit credentials.
Paths are relative to the API base URL, e.g. "/me", "/ad_accounts/{ad_account_id}/campaigns".
Request bodies use Reddit's envelope: {"data": {...}}. Updates are PATCH.
Unsure how to call an endpoint? Use reddit_ads_list_endpoints to find it and
reddit_ads_describe_endpoint to read its parameters, body schema and required OAuth scope,
then call it with reddit_ads_request. To get the next page of a list, pass the response's
pagination.next_url to reddit_ads_follow_page. Creating or changing campaigns, ad groups
and ads can spend money; confirm those actions with the user.
"""

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
PageMethod = Literal["GET", "POST"]


def build_server(
    settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
) -> MCPServer:
    """Create the server; `transport` replaces the network in tests."""
    server = MCPServer(name="reddit-ads", instructions=INSTRUCTIONS)
    _add_api_tools(server, RedditAdsApi(settings, transport))
    _add_discovery_tools(server, SpecCatalog(settings, transport))
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def _add_api_tools(server: MCPServer, api: RedditAdsApi) -> None:
    @server.tool()
    async def reddit_ads_request(
        method: HttpMethod,
        path: str,
        query: dict[str, FormValue] | None = None,
        body: JsonObject | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonObject:
        """Call any Reddit Ads API endpoint with an optional JSON body.

        `path` is relative to the base URL, e.g. "/ad_accounts/{ad_account_id}/campaigns".
        Bodies use Reddit's envelope, e.g. {"data": {"name": "..."}}. Returns the status,
        rate-limit headers, and the body as json or text.
        """
        return await api.send_json(JsonRequest(method, path, query, body, headers))

    @server.tool()
    async def reddit_ads_follow_page(
        url: str, method: PageMethod = "GET", body: JsonObject | None = None
    ) -> JsonObject:
        """Fetch another page: pass `pagination.next_url` (or previous_url) exactly as returned.

        For a list that came from a POST (reports, history, the /query endpoints), use
        method "POST" and send the same `body` as the original request. That the body must
        be re-sent is inferred from the spec's shape, not confirmed by Reddit.
        """
        return await api.follow_page(url, method, body)


def _add_discovery_tools(server: MCPServer, catalog: SpecCatalog) -> None:
    @server.tool()
    async def reddit_ads_list_endpoints(text_filter: str | None = None) -> list[str]:
        """List API operations as "METHOD /path — summary", filtered by substring."""
        return await catalog.list_endpoints(text_filter)

    @server.tool()
    async def reddit_ads_describe_endpoint(
        method: HttpMethod, path: str, depth: int = 1
    ) -> JsonObject:
        """Describe one operation: OAuth scopes, parameters, body schema and success responses.

        `path` is the templated spec path exactly as listed, e.g. "/campaigns/{campaign_id}".
        Schema `$ref`s are expanded `depth` levels (1-6); unexpanded ones stay as "$ref"
        markers. `scopes` is null when the operation declares none.
        """
        return await catalog.describe(method, path, depth)
