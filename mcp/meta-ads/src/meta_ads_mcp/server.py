"""The MCP server: six generic tools that together reach the Meta Marketing (Graph) API."""

from collections.abc import Awaitable
from typing import Literal, TypeVar

import httpx2
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from meta_ads_mcp.api import BodyFormat, GraphRequest, JsonObject, MetaAdsApi, QueryValue
from meta_ads_mcp.config import Settings
from meta_ads_mcp.scrub import Scrubber
from meta_ads_mcp.spec_catalog import SpecCatalog
from meta_ads_mcp.spec_fetch import SPEC_CONTENT_HASH
from meta_ads_mcp.token_status import token_status

INSTRUCTIONS = """\
Full access to Meta's Marketing API (Graph API) with the operator's system-user token.
Paths are relative to the versioned base URL: "/me/adaccounts", "/act_<id>/campaigns",
"/<object id>". An ad account id is written act_<digits>. Read with GET and choose fields
with the `fields` query parameter; follow paging.next with meta_ads_follow_page. Create
with POST to an edge (POST /act_<id>/campaigns), update with POST to the object
(POST /<id>), delete with DELETE /<id>. Writes change live campaigns and can spend real
money: create with status=PAUSED and confirm spending changes with the user.
Unsure how to call something? meta_ads_list_endpoints finds templates like
"POST /{AdAccount}/campaigns", meta_ads_describe_endpoint lists their parameters and enum
values, and meta_ads_describe_type lists an object's readable fields.
"""

HttpMethod = Literal["GET", "POST", "DELETE"]
Result = TypeVar("Result")


def build_server(
    settings: Settings,
    transport: httpx2.AsyncBaseTransport | None = None,
    spec_hash: str = SPEC_CONTENT_HASH,
) -> MCPServer:
    """Create the server; `transport` and `spec_hash` replace the network and pin in tests."""
    server = MCPServer(name="meta-ads", instructions=INSTRUCTIONS)
    api = MetaAdsApi(settings, transport)
    _add_api_tools(server, api, settings)
    _add_discovery_tools(server, SpecCatalog(settings, transport, spec_hash), api.scrubber)
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


async def scrubbed(scrubber: Scrubber, call: Awaitable[Result]) -> Result:
    """Run a tool body, removing any credential from the error a failure reports."""
    try:
        return await call
    except ToolError as error:
        raise ToolError(scrubber.text(str(error))) from None


def _add_api_tools(server: MCPServer, api: MetaAdsApi, settings: Settings) -> None:
    @server.tool()
    async def meta_ads_request(
        method: HttpMethod,
        path: str,
        query: dict[str, QueryValue] | None = None,
        body: JsonObject | None = None,
        body_format: BodyFormat = "json",
    ) -> JsonObject:
        """Call any Graph API endpoint the token can reach.

        `path` is relative to the versioned base URL with real ids filled in, e.g.
        "/act_1234567890/campaigns" or "/120200000000000000". Choose read fields with
        query {"fields": "name,status,daily_budget"} and page with meta_ads_follow_page.
        List and object query values are sent as JSON, as Graph expects, e.g.
        {"effective_status": ["ACTIVE"], "time_range": {"since": "2026-10-01",
        "until": "2026-10-18"}}.
        Writes are POST (create on an edge, update on the object) or DELETE. Writes change
        live campaigns and SPEND REAL MONEY: create campaigns, ad sets and ads with
        "status": "PAUSED" and confirm activation and budget changes with the user first.
        Budgets are in the account currency's minor units (cents). `body_format` "form"
        sends form fields (nested values as JSON), needed to upload an image to
        /act_<id>/adimages as base64 "bytes". Rate limits come back as Graph errors 4,
        17, 613 or 80000-80014; wait before retrying. Batch requests and the
        access_token, appsecret_proof, batch, adbatch, method, suppress_http_code and
        callback parameters are refused. Returns the status, Meta's trace and usage headers, and
        the body; credentials never appear in it.
        """
        request = GraphRequest(method, path, query, body, body_format)
        return await scrubbed(api.scrubber, api.send(request))

    @server.tool()
    async def meta_ads_follow_page(url: str) -> JsonObject:
        """Fetch the next or previous page: pass `paging.next` / `paging.previous` as returned."""
        return await scrubbed(api.scrubber, api.follow_page(url))

    @server.tool()
    async def meta_ads_token_status() -> JsonObject:
        """Report whether the token is valid, its type and scopes, and when it expires.

        "never" means it does not expire. A 60-day token must be refreshed before then.
        """
        configured = settings.app_id is not None
        return await scrubbed(api.scrubber, token_status(api, app_configured=configured))


def _add_discovery_tools(server: MCPServer, catalog: SpecCatalog, scrubber: Scrubber) -> None:
    @server.tool()
    async def meta_ads_list_endpoints(text_filter: str | None = None) -> list[str]:
        """List Graph operations as "METHOD /{Node}/edge → Return", filtered by substring.

        Templates name the node type in braces: call "/{AdAccount}/campaigns" as
        "/act_<id>/campaigns"; "/me" is a User.
        """
        return await scrubbed(scrubber, catalog.list_endpoints(text_filter))

    @server.tool()
    async def meta_ads_describe_endpoint(method: HttpMethod, path: str) -> JsonObject:
        """Describe one operation's parameters, with enum values.

        `path` is the template exactly as meta_ads_list_endpoints prints it, e.g.
        "/{AdAccount}/campaigns", not a concrete path with ids.
        """
        return await scrubbed(scrubber, catalog.describe_endpoint(method, path))

    @server.tool()
    async def meta_ads_describe_type(name: str) -> JsonObject:
        """Describe a node type such as Campaign or AdsInsights: its fields and endpoints."""
        return await scrubbed(scrubber, catalog.describe_type(name))
