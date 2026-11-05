"""The MCP server: five generic tools that together reach the Microsoft Advertising API."""

from collections.abc import Awaitable
from typing import TypeVar

import httpx2
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from microsoft_ads_mcp.api import ApiRequest, JsonObject, MicrosoftAdsApi
from microsoft_ads_mcp.catalog import OperationCatalog, load_catalog
from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.download import Downloader
from microsoft_ads_mcp.scrub import Scrubber

INSTRUCTIONS = """\
Full access to the Microsoft Advertising API (Bing Ads API v13, REST) with the operator's
OAuth credentials. Call an operation by name with microsoft_ads_request, e.g.
operation "GetCampaignsByAccountId" with body {"AccountId": "123", "CampaignType":
"Search"}. Find operations with microsoft_ads_list_operations and read their request
fields with microsoft_ads_describe_operation; open nested types and enums with
microsoft_ads_describe_type. Ids are JSON strings; money is in the account currency
(10.5 means 10.50), not micros; polymorphic objects need their "Type" (e.g. an ad with
"Type": "ResponsiveSearch"). Reports: SubmitGenerateReport, PollGenerateReport until
Status is "Success", then microsoft_ads_download_file on ReportDownloadUrl within five
minutes. Writes change live campaigns and can spend real money: create campaigns, ad
groups and ads with "Status": "Paused" and confirm enabling and budget changes with the
user.
"""

Result = TypeVar("Result")


def build_server(
    settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
) -> MCPServer:
    """Create the server; `transport` replaces the network in tests."""
    server = MCPServer(name="microsoft-ads", instructions=INSTRUCTIONS)
    catalog = OperationCatalog(load_catalog(), settings.max_response_bytes)
    api = MicrosoftAdsApi(settings, catalog, transport)
    scrubber = Scrubber(api.tokens.secrets)
    _add_api_tools(server, api, Downloader(settings, transport), scrubber)
    _add_discovery_tools(server, catalog)
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


async def scrubbed(scrubber: Scrubber, call: Awaitable[JsonObject]) -> JsonObject:
    """Run a tool body, removing every credential from its result or its error."""
    try:
        result = await call
    except ToolError as error:
        raise ToolError(scrubber.text(str(error))) from None
    return scrubber.mapping(result)


def _add_api_tools(
    server: MCPServer, api: MicrosoftAdsApi, downloader: Downloader, scrubber: Scrubber
) -> None:
    @server.tool()
    async def microsoft_ads_request(
        operation: str,
        body: JsonObject | None = None,
        customer_id: str | None = None,
        account_id: str | None = None,
    ) -> JsonObject:
        """Call one Microsoft Advertising API operation by name with a JSON body.

        `operation` is a name from microsoft_ads_list_operations, e.g. "AddCampaigns" or
        "GetAdGroupsByCampaignId" (case and underscores do not matter). `body` uses the wire
        names microsoft_ads_describe_operation lists, e.g. {"AccountId": "123",
        "Campaigns": [{"Name": "Spring", "BudgetType": "DailyBudgetStandard",
        "DailyBudget": 25, "Status": "Paused"}]}. Ids are strings; money is in the account
        currency, not micros; polymorphic objects need their "Type".
        `customer_id` and `account_id` override the configured CustomerId and
        CustomerAccountId headers for this call (digits only).
        Writes change live campaigns and SPEND REAL MONEY: create campaigns, ad groups and
        ads with "Status": "Paused" and confirm enabling them, and budget or bid increases,
        with the user first. Per call: at most 100 campaigns, 1,000 ad groups, 50 ads or
        1,000 keywords. Add, Update and Delete can partly succeed: check for null ids and
        PartialErrors in the response. Throttling comes back as error 117
        (CallRateExceeded), 207 (Reporting) or 4204 (Bulk): wait before retrying. Returns
        the status, Microsoft's tracking id and the body; credentials never appear in it.
        """
        request = ApiRequest(operation, body, customer_id, account_id)
        return await scrubbed(scrubber, api.call(request))

    @server.tool()
    async def microsoft_ads_download_file(url: str) -> JsonObject:
        """Download a report or bulk result file and return its text (CSV or TSV).

        Pass ReportDownloadUrl from PollGenerateReport, or ResultFileUrl from
        GetBulkDownloadStatus, exactly as returned; they expire after a few minutes, so poll
        again for a fresh one. Zip and gzip files are unpacked. No credentials are sent.
        """
        return await scrubbed(scrubber, downloader.fetch(url))


def _add_discovery_tools(server: MCPServer, catalog: OperationCatalog) -> None:
    @server.tool()
    def microsoft_ads_list_operations(text_filter: str | None = None) -> list[str]:
        """List operations as "Service.Name — METHOD /path → RequestType".

        `text_filter` is a case-insensitive substring, e.g. "Campaigns", "Keyword",
        "Report" or "Budget".
        """
        return catalog.list_operations(text_filter)

    @server.tool()
    def microsoft_ads_describe_operation(operation: str) -> JsonObject:
        """Describe an operation's request and response fields, by wire name.

        Also lists the fields of each type they name and the values of every enum involved.
        """
        return catalog.describe_operation(operation)

    @server.tool()
    def microsoft_ads_describe_type(name: str, service: str | None = None) -> JsonObject:
        """Describe a type (its fields, and subtypes with their "Type") or an enum.

        A type's inherited fields are included.
        `service` (e.g. "CampaignManagement") is needed only when several services define
        the name; the error says which.
        """
        return catalog.describe_type(name, service)
