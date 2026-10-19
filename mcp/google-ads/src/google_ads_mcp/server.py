"""The MCP server: four generic tools that together reach the whole Google Ads API."""

from typing import Literal

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from google_ads_mcp.api import FormValue, GoogleAdsApi, JsonObject, JsonRequest
from google_ads_mcp.config import Settings
from google_ads_mcp.credentials import CredentialsLoader, TokenSource, default_loader
from google_ads_mcp.spec import SpecCatalog

INSTRUCTIONS = """\
Full access to the Google Ads API (REST) with the operator's Google credentials.
Paths are relative to the versioned base URL, e.g. "/customers:listAccessibleCustomers" or
"/customers/1234567890/googleAds:search". Customer ids are digits without dashes.
Read with GAQL: POST /customers/{customerId}/googleAds:search with {"query": "SELECT ..."},
then pass the response's nextPageToken back as "pageToken" for the next page. Prefer
googleAds:search over googleAds:searchStream, which returns every row at once.
Change things with the */mutate endpoints. Send a mutate with "validateOnly": true first:
Google checks it without applying it. Acting on a client account through a manager
account needs the manager's id in a "login-customer-id" header.
Unsure how to call an endpoint? Use google_ads_list_endpoints to find it,
google_ads_describe_endpoint to read its parameters and request schema, and
google_ads_describe_schema to open any nested schema it names. Creating or enabling
campaigns, ad groups and ads, and raising budgets or bids, can spend money; confirm those
actions with the user.
"""

HttpMethod = Literal["GET", "POST", "PATCH", "DELETE"]


def build_server(
    settings: Settings,
    transport: httpx2.AsyncBaseTransport | None = None,
    loader: CredentialsLoader | None = None,
) -> MCPServer:
    """Create the server; `transport` and `loader` replace the network in tests."""
    server = MCPServer(name="google-ads", instructions=INSTRUCTIONS)
    tokens = TokenSource(loader or default_loader(settings))
    _add_api_tools(server, GoogleAdsApi(settings, tokens, transport))
    _add_discovery_tools(server, SpecCatalog(settings, transport))
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def _add_api_tools(server: MCPServer, api: GoogleAdsApi) -> None:
    @server.tool()
    async def google_ads_request(
        method: HttpMethod,
        path: str,
        query: dict[str, FormValue] | None = None,
        body: JsonObject | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonObject:
        """Call any Google Ads API endpoint with an optional JSON body.

        `path` is relative to the versioned base URL with real ids filled in, e.g.
        "/customers/1234567890/campaigns:mutate". For GAQL reads POST
        "/customers/<id>/googleAds:search" with {"query": "...", "pageSize": 1000}.
        Add "validateOnly": true to a mutate body to check it without applying it.
        `headers` may set "login-customer-id" (a manager account id). Returns the status,
        the request-id header, and the body as json or text.
        """
        return await api.send_json(JsonRequest(method, path, query, body, headers))


def _add_discovery_tools(server: MCPServer, catalog: SpecCatalog) -> None:
    @server.tool()
    async def google_ads_list_endpoints(text_filter: str | None = None) -> list[str]:
        """List API operations as "METHOD /template — summary", filtered by substring."""
        return await catalog.list_endpoints(text_filter)

    @server.tool()
    async def google_ads_describe_endpoint(
        method: HttpMethod, path: str, depth: int = 1
    ) -> JsonObject:
        """Describe one operation: its parameters, request schema and response schema.

        `path` is the template exactly as google_ads_list_endpoints prints it, e.g.
        "/customers/{customerId}/adGroups:mutate". Schema `$ref`s are expanded `depth`
        levels (1-6); an unexpanded one stays as {"$ref": "<schema name>"}, which
        google_ads_describe_schema opens.
        """
        return await catalog.describe(method, path, depth)

    @server.tool()
    async def google_ads_describe_schema(name: str, depth: int = 1) -> JsonObject:
        """Describe one schema by the name a `$ref` marker gives, e.g. a nested message type.

        Its own `$ref`s are expanded `depth` levels (1-6). Open nested types one at a
        time rather than raising `depth`: Google Ads messages nest deeply.
        """
        return await catalog.describe_schema(name, depth)
