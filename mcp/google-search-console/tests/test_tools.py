"""The tools, exercised end to end through an in-process MCP client."""

import json
from dataclasses import replace

import httpx2
import pytest
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from mcp import Client

from google_search_console_mcp.config import Settings
from google_search_console_mcp.server import build_server
from tests.conftest import FakeCredentials, FakeSearchConsole, call, error_text

pytestmark = pytest.mark.anyio

READ_TOOLS = {
    "gsc_list_sites",
    "gsc_get_site",
    "gsc_list_sitemaps",
    "gsc_get_sitemap",
    "gsc_query_search_analytics",
    "gsc_inspect_url",
}
WRITE_TOOLS = {"gsc_add_site", "gsc_delete_site", "gsc_submit_sitemap", "gsc_delete_sitemap"}
SITE = "https://www.example.com/"
ENCODED_SITE = "https%3A%2F%2Fwww.example.com%2F"
V3 = "https://searchconsole.googleapis.com/webmasters/v3/sites"


async def tool_names(settings: Settings, fake: FakeSearchConsole) -> set[str]:
    """Return the names of the tools a server built from `settings` lists."""
    async with Client(build_server(settings, fake.transport, FakeCredentials)) as client:
        listed = await client.list_tools()
    return {tool.name for tool in listed.tools}


async def test_all_ten_tools_are_listed(settings: Settings, fake: FakeSearchConsole) -> None:
    assert await tool_names(settings, fake) == READ_TOOLS | WRITE_TOOLS


async def test_read_only_mode_omits_the_write_tools(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    assert await tool_names(replace(settings, read_only=True), fake) == READ_TOOLS


@pytest.mark.parametrize(
    ("tool", "arguments", "expected"),
    [
        ("gsc_list_sites", {}, ("GET", V3)),
        ("gsc_get_site", {"site_url": SITE}, ("GET", f"{V3}/{ENCODED_SITE}")),
        ("gsc_add_site", {"site_url": SITE}, ("PUT", f"{V3}/{ENCODED_SITE}")),
        ("gsc_delete_site", {"site_url": SITE}, ("DELETE", f"{V3}/{ENCODED_SITE}")),
        ("gsc_list_sitemaps", {"site_url": SITE}, ("GET", f"{V3}/{ENCODED_SITE}/sitemaps")),
        (
            "gsc_list_sitemaps",
            {"site_url": SITE, "sitemap_index": f"{SITE}index.xml"},
            (
                "GET",
                f"{V3}/{ENCODED_SITE}/sitemaps?sitemapIndex=https%3A%2F%2Fwww.example.com%2Findex.xml",
            ),
        ),
        (
            "gsc_get_sitemap",
            {"site_url": "sc-domain:example.com", "feedpath": f"{SITE}sitemap.xml"},
            ("GET", f"{V3}/sc-domain%3Aexample.com/sitemaps/{ENCODED_SITE}sitemap.xml"),
        ),
        (
            "gsc_submit_sitemap",
            {"site_url": SITE, "feedpath": "../../sites?x=1"},
            ("PUT", f"{V3}/{ENCODED_SITE}/sitemaps/..%2F..%2Fsites%3Fx%3D1"),
        ),
        (
            "gsc_delete_sitemap",
            {"site_url": SITE, "feedpath": f"{SITE}sitemap.xml"},
            ("DELETE", f"{V3}/{ENCODED_SITE}/sitemaps/{ENCODED_SITE}sitemap.xml"),
        ),
    ],
)
async def test_each_tool_builds_its_own_encoded_url(
    settings: Settings,
    fake: FakeSearchConsole,
    tool: str,
    arguments: dict[str, object],
    expected: tuple[str, str],
) -> None:
    result = await call(settings, fake, tool, arguments)
    assert result.structured_content == {"ok": True}
    assert (fake.last.method, str(fake.last.url)) == expected
    assert fake.last.headers["authorization"] == "Bearer token-1"


async def test_search_analytics_sends_the_api_body(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    query = {
        "start_date": "2026-09-01",
        "endDate": "2026-09-07",
        "dimensions": ["QUERY", "PAGE"],
        "type": "WEB",
        "dimension_filter_groups": [
            {"filters": [{"dimension": "QUERY", "operator": "CONTAINS", "expression": "shoes"}]}
        ],
        "row_limit": 10,
    }
    result = await call(
        settings, fake, "gsc_query_search_analytics", {"site_url": SITE, "query": query}
    )
    assert not result.is_error
    assert str(fake.last.url) == f"{V3}/{ENCODED_SITE}/searchAnalytics/query"
    assert json.loads(fake.last.content) == {
        "startDate": "2026-09-01",
        "endDate": "2026-09-07",
        "dimensions": ["QUERY", "PAGE"],
        "type": "WEB",
        "dimensionFilterGroups": [
            {
                "groupType": "AND",
                "filters": [{"dimension": "QUERY", "operator": "CONTAINS", "expression": "shoes"}],
            }
        ],
        "rowLimit": 10,
    }


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("gsc_delete_sitemap", {"site_url": SITE, "feedpath": ".."}),
        ("gsc_submit_sitemap", {"site_url": SITE, "feedpath": "."}),
        ("gsc_get_site", {"site_url": ".."}),
        (
            "gsc_query_search_analytics",
            {"site_url": ".", "query": {"startDate": "a", "endDate": "b"}},
        ),
    ],
)
async def test_dot_segments_never_reach_another_endpoint(
    settings: Settings, fake: FakeSearchConsole, tool: str, arguments: dict[str, object]
) -> None:
    result = await call(settings, fake, tool, arguments)
    assert "is not a site URL or sitemap URL" in error_text(result)
    assert fake.requests == []


async def test_search_analytics_accepts_the_deprecated_search_type_name(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    query = {"startDate": "2026-09-01", "endDate": "2026-09-07", "searchType": "IMAGE"}
    await call(settings, fake, "gsc_query_search_analytics", {"site_url": SITE, "query": query})
    assert json.loads(fake.last.content)["type"] == "IMAGE"


async def test_search_analytics_refuses_unknown_fields(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    query = {"startDate": "2026-09-01", "endDate": "2026-09-07", "rowlimit": 5}
    result = await call(
        settings, fake, "gsc_query_search_analytics", {"site_url": SITE, "query": query}
    )
    assert "query.rowlimit" in error_text(result)
    assert fake.requests == []


async def test_search_analytics_rejects_an_out_of_range_row_limit(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    query = {"start_date": "2026-09-01", "end_date": "2026-09-07", "row_limit": 25001}
    result = await call(
        settings, fake, "gsc_query_search_analytics", {"site_url": SITE, "query": query}
    )
    assert "query.row_limit" in error_text(result)
    assert fake.requests == []


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (None, {"siteUrl": SITE, "inspectionUrl": f"{SITE}page"}),
        ("en-US", {"siteUrl": SITE, "inspectionUrl": f"{SITE}page", "languageCode": "en-US"}),
    ],
)
async def test_inspect_url_posts_a_v1_body(
    settings: Settings, fake: FakeSearchConsole, language: str | None, expected: dict[str, str]
) -> None:
    arguments: dict[str, object] = {"site_url": SITE, "inspection_url": f"{SITE}page"}
    if language:
        arguments["language_code"] = language
    await call(settings, fake, "gsc_inspect_url", arguments)
    assert fake.last.method == "POST"
    assert (
        str(fake.last.url) == "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
    )
    assert json.loads(fake.last.content) == expected


async def test_api_errors_come_back_as_tool_errors(settings: Settings) -> None:
    fake = FakeSearchConsole(
        handler=lambda _request: httpx2.Response(403, json={"error": {"message": "No access"}})
    )
    result = await call(settings, fake, "gsc_get_site", {"site_url": SITE})
    assert error_text(result).endswith("Search Console API returned 403: No access")


async def test_network_failures_come_back_as_tool_errors(settings: Settings) -> None:
    def unreachable(request: httpx2.Request) -> httpx2.Response:
        message = "timed out"
        raise httpx2.ConnectTimeout(message, request=request)

    fake = FakeSearchConsole(handler=unreachable)
    result = await call(settings, fake, "gsc_list_sites", {})
    assert "could not reach the Search Console API: ConnectTimeout" in error_text(result)


async def test_missing_credentials_are_reported_without_a_request(
    settings: Settings, fake: FakeSearchConsole
) -> None:
    def no_credentials() -> Credentials:
        message = "no ADC"
        # google-auth leaves its exception constructors unannotated.
        raise DefaultCredentialsError(message)  # type: ignore[no-untyped-call]

    async with Client(build_server(settings, fake.transport, no_credentials)) as client:
        result = await client.call_tool("gsc_list_sites", {})
    assert "Google credentials are unavailable" in error_text(result)
    assert fake.requests == []


async def test_read_only_mode_tells_the_model(settings: Settings, fake: FakeSearchConsole) -> None:
    server = build_server(replace(settings, read_only=True), fake.transport, FakeCredentials)
    async with Client(server) as client:
        instructions = client.instructions
    assert instructions is not None
    assert "read-only" in instructions
