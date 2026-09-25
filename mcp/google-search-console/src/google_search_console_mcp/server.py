"""The MCP server: one typed tool per live Search Console API operation."""

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from google_search_console_mcp.api import (
    INSPECT_PATH,
    SITES,
    JsonObject,
    SearchConsoleApi,
    site_path,
)
from google_search_console_mcp.config import Settings
from google_search_console_mcp.credentials import CredentialsLoader, TokenSource, default_loader
from google_search_console_mcp.models import SearchAnalyticsQuery

INSTRUCTIONS = """\
Google Search Console with the operator's Google credentials.
A site_url is a property exactly as Search Console lists it: a URL-prefix property such as
"https://www.example.com/" (with the trailing slash) or a domain property such as
"sc-domain:example.com". Call gsc_list_sites first to see which properties you can use.
Search Analytics dates are YYYY-MM-DD in Pacific time; recent days may be incomplete.
"""
READ_ONLY_NOTE = "This server is read-only: it cannot add or remove sites or sitemaps.\n"


def build_server(
    settings: Settings,
    transport: httpx2.AsyncBaseTransport | None = None,
    loader: CredentialsLoader | None = None,
) -> MCPServer:
    """Create the server; `transport` and `loader` replace the network in tests."""
    instructions = INSTRUCTIONS + (READ_ONLY_NOTE if settings.read_only else "")
    server = MCPServer(name="google-search-console", instructions=instructions)
    tokens = TokenSource(loader or default_loader(settings))
    api = SearchConsoleApi(settings, tokens, transport)
    _add_site_tools(server, api)
    _add_sitemap_tools(server, api)
    _add_report_tools(server, api)
    if not settings.read_only:
        _add_write_tools(server, api)
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def _add_site_tools(server: MCPServer, api: SearchConsoleApi) -> None:
    @server.tool()
    async def gsc_list_sites() -> JsonObject:
        """List the properties these credentials can access, with their permission level."""
        return await api.call("GET", SITES)

    @server.tool()
    async def gsc_get_site(site_url: str) -> JsonObject:
        """Get one property's URL and the credentials' permission level on it."""
        return await api.call("GET", site_path(site_url))


def _add_sitemap_tools(server: MCPServer, api: SearchConsoleApi) -> None:
    @server.tool()
    async def gsc_list_sitemaps(site_url: str, sitemap_index: str | None = None) -> JsonObject:
        """List sitemaps submitted for a property, or those inside one sitemap index."""
        params = {"sitemapIndex": sitemap_index} if sitemap_index else None
        return await api.call("GET", site_path(site_url, "sitemaps"), params=params)

    @server.tool()
    async def gsc_get_sitemap(site_url: str, feedpath: str) -> JsonObject:
        """Get one sitemap's status, errors, warnings and indexed counts.

        `feedpath` is the sitemap's full URL, e.g. "https://www.example.com/sitemap.xml".
        """
        return await api.call("GET", site_path(site_url, "sitemaps", feedpath))


def _add_report_tools(server: MCPServer, api: SearchConsoleApi) -> None:
    @server.tool()
    async def gsc_query_search_analytics(site_url: str, query: SearchAnalyticsQuery) -> JsonObject:
        """Query clicks, impressions, CTR and position, grouped by dimensions and filtered.

        Returns up to row_limit rows (API default 1000, max 25000); page with start_row.
        With no dimensions, one row totals the whole date range.
        """
        path = site_path(site_url, "searchAnalytics", "query")
        return await api.call("POST", path, body=query.to_api())

    @server.tool()
    async def gsc_inspect_url(
        site_url: str, inspection_url: str, language_code: str | None = None
    ) -> JsonObject:
        """Inspect how Google indexes one URL: coverage, crawl, canonical, rich results.

        `inspection_url` must belong to `site_url`. `language_code` (e.g. "en-US")
        localizes the issue messages. Quota is roughly 2,000 inspections a day per property.
        """
        body: JsonObject = {"siteUrl": site_url, "inspectionUrl": inspection_url}
        if language_code:
            body["languageCode"] = language_code
        return await api.call("POST", INSPECT_PATH, body=body)


def _add_write_tools(server: MCPServer, api: SearchConsoleApi) -> None:
    @server.tool()
    async def gsc_add_site(site_url: str) -> JsonObject:
        """Add a property to the account. It still has to be verified before data appears."""
        return await api.call("PUT", site_path(site_url))

    @server.tool()
    async def gsc_delete_site(site_url: str) -> JsonObject:
        """Remove a property from the account. Confirm with the user first."""
        return await api.call("DELETE", site_path(site_url))

    @server.tool()
    async def gsc_submit_sitemap(site_url: str, feedpath: str) -> JsonObject:
        """Submit (or resubmit) a sitemap by its full URL."""
        return await api.call("PUT", site_path(site_url, "sitemaps", feedpath))

    @server.tool()
    async def gsc_delete_sitemap(site_url: str, feedpath: str) -> JsonObject:
        """Remove a sitemap from the Sitemaps report; Google may still crawl it."""
        return await api.call("DELETE", site_path(site_url, "sitemaps", feedpath))
