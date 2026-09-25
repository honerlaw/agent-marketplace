"""Endpoint discovery against a small fixture spec."""

import httpx2
import pytest
from mcp import Client

from reddit_ads_mcp.config import Credentials, Settings
from reddit_ads_mcp.server import build_server
from reddit_ads_mcp.spec import SpecCatalog, required_scopes, resolve_refs, strip_html
from tests.conftest import FIXTURE_SPEC, FakeReddit

pytestmark = pytest.mark.anyio

STATIC = Credentials(access_token="t")  # noqa: S106 - a fixture value, not a secret


async def test_list_endpoints_names_every_operation(settings: Settings) -> None:
    lines = await SpecCatalog(settings).list_endpoints(None)
    assert lines == [
        "GET /me — Get Me",
        "GET /ad_accounts/{ad_account_id}/campaigns — List Campaigns",
        "POST /ad_accounts/{ad_account_id}/campaigns — Create Campaign",
        "GET /targeting/communities/suggestions — suggestCommunities",
        "POST /ad_accounts/{ad_account_id}/reports — Get a Report",
    ]


async def test_list_endpoints_filters_case_insensitively(settings: Settings) -> None:
    assert await SpecCatalog(settings).list_endpoints("CAMPAIGN") == [
        "GET /ad_accounts/{ad_account_id}/campaigns — List Campaigns",
        "POST /ad_accounts/{ad_account_id}/campaigns — Create Campaign",
    ]


async def test_describe_reports_scope_body_and_success_responses(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe(
        "post", "/ad_accounts/{ad_account_id}/campaigns", 2
    )
    assert described["method"] == "POST"
    assert described["scopes"] == ["adsedit"]
    assert list(described["responses"]) == ["200"]  # type: ignore[call-overload]
    schema = described["requestBody"]["content"]["application/json"]["schema"]  # type: ignore[index]
    assert schema["properties"]["data"]["description"] == "A campaign ."


async def test_describe_strips_html_from_descriptions(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe(
        "post", "/ad_accounts/{ad_account_id}/campaigns", 1
    )
    assert described["description"] == "Create a campaign.\nRate Limit\nSee the write limits"


async def test_describe_scopes_are_null_when_undeclared(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("get", "/targeting/communities/suggestions", 1)
    assert described["scopes"] is None


@pytest.mark.parametrize(
    "security",
    [None, [], [{}], [{"RedditAPIKey": []}], "junk", [{"RedditAPIKey": "adsread"}]],
)
def test_malformed_or_empty_security_means_no_scopes(security: object) -> None:
    assert required_scopes({"security": security}) is None


def test_scopes_from_several_requirements_are_combined() -> None:
    security = [{"RedditAPIKey": ["adsread"]}, {"Other": ["adsedit"]}]
    assert required_scopes({"security": security}) == ["adsread", "adsedit"]


def test_non_string_descriptions_are_walked_not_stripped() -> None:
    node = {"description": {"description": "<b>x</b>"}, "items": [{"description": "<i>y</i>"}]}
    assert strip_html(node) == {
        "description": {"description": "x"},
        "items": [{"description": "y"}],
    }


async def test_describe_unknown_operation_is_an_error(settings: Settings, fake: FakeReddit) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        result = await client.call_tool(
            "reddit_ads_describe_endpoint", {"method": "PATCH", "path": "/me"}
        )
    assert result.is_error
    assert "reddit_ads_list_endpoints" in str(result.content[0])


async def test_describe_depth_is_clamped_to_its_bounds(settings: Settings) -> None:
    catalog = SpecCatalog(settings)
    assert await catalog.describe("get", "/me", 0) == await catalog.describe("get", "/me", 1)
    assert await catalog.describe("get", "/me", 99) == await catalog.describe("get", "/me", 6)
    assert await catalog.describe("get", "/me", 2) != await catalog.describe("get", "/me", 1)


async def test_shallow_describe_leaves_ref_markers(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("get", "/me", 1)
    assert "#/components/schemas/User" in str(described["responses"])


def test_recursive_refs_stop_at_the_depth_bound() -> None:
    spec: dict[str, object] = {"a": {"next": {"$ref": "#/a"}}}
    resolved = resolve_refs({"$ref": "#/a"}, spec, 2)
    assert resolved == {"next": {"next": {"$ref": "#/a"}}}


async def test_spec_is_fetched_once_from_the_url(fake: FakeReddit) -> None:
    fake.api_handler = lambda _request: httpx2.Response(200, text=FIXTURE_SPEC.read_text())
    url = "https://ads-api.reddit.com/api/v3/openapi.json"
    catalog = SpecCatalog(Settings(credentials=STATIC, openapi_url=url), fake.transport)
    await catalog.list_endpoints(None)
    await catalog.list_endpoints("me")
    assert [str(request.url) for request in fake.requests] == [url]
    assert "authorization" not in fake.requests[0].headers


async def test_unreachable_spec_is_a_clear_tool_error(fake: FakeReddit) -> None:
    fake.api_handler = lambda _request: httpx2.Response(503)
    server = build_server(Settings(credentials=STATIC), fake.transport)
    async with Client(server) as client:
        result = await client.call_tool("reddit_ads_list_endpoints", {})
    assert result.is_error
    assert "could not load the OpenAPI spec" in str(result.content[0])
