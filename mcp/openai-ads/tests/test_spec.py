"""Endpoint discovery against a small fixture spec."""

import httpx2
import pytest
from mcp import Client

from openai_ads_mcp.config import Settings
from openai_ads_mcp.server import build_server
from openai_ads_mcp.spec import SpecCatalog, resolve_refs
from tests.conftest import FIXTURE_SPEC, FakeAdsApi

pytestmark = pytest.mark.anyio


async def test_list_endpoints_names_every_operation(settings: Settings) -> None:
    lines = await SpecCatalog(settings).list_endpoints(None)
    assert lines == [
        "GET /campaigns — List Campaigns",
        "POST /campaigns — Create Campaign",
        "POST /upload — UploadImageMethod",
        "GET /lead_sync_subscriptions/{subscription_id} — Get Lead Sync Subscription",
        "DELETE /lead_sync_subscriptions/{subscription_id} — Delete Lead Sync Subscription",
    ]


async def test_list_endpoints_filters_case_insensitively(settings: Settings) -> None:
    assert await SpecCatalog(settings).list_endpoints("DELETE") == [
        "DELETE /lead_sync_subscriptions/{subscription_id} — Delete Lead Sync Subscription"
    ]


async def test_describe_resolves_refs_and_keeps_success_responses(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("post", "/campaigns", 2)
    assert (described["method"], described["summary"]) == ("POST", "Create Campaign")
    assert list(described["responses"]) == ["200"]  # type: ignore[call-overload]
    assert described["requestBody"] == {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["name", "status", "budget"],
                    "properties": {
                        "name": {"type": "string"},
                        "status": {"enum": ["active", "paused"]},
                        "budget": {
                            "type": "object",
                            "properties": {"daily_spend_limit_micros": {"type": "integer"}},
                        },
                    },
                }
            }
        }
    }


async def test_describe_unknown_operation_is_an_error(settings: Settings, fake: FakeAdsApi) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        result = await client.call_tool(
            "openai_ads_describe_endpoint", {"method": "PATCH", "path": "/campaigns"}
        )
    assert result.is_error


async def test_describe_depth_is_clamped_to_its_bounds(settings: Settings) -> None:
    catalog = SpecCatalog(settings)
    assert await catalog.describe("get", "/campaigns", 0) == await catalog.describe(
        "get", "/campaigns", 1
    )
    assert await catalog.describe("get", "/campaigns", 99) == await catalog.describe(
        "get", "/campaigns", 6
    )
    assert await catalog.describe("get", "/campaigns", 6) != await catalog.describe(
        "get", "/campaigns", 5
    )


async def test_shallow_describe_leaves_ref_markers(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("get", "/campaigns", 1)
    assert "#/components/schemas/Campaign" in str(described["responses"])


def test_recursive_refs_stop_at_the_depth_bound() -> None:
    spec: dict[str, object] = {"a": {"next": {"$ref": "#/a"}}}
    resolved = resolve_refs({"$ref": "#/a"}, spec, 2)
    assert resolved == {"next": {"next": {"$ref": "#/a"}}}


async def test_spec_is_fetched_once_from_the_url(fake: FakeAdsApi) -> None:
    fake.handler = lambda _request: httpx2.Response(200, text=FIXTURE_SPEC.read_text())
    catalog = SpecCatalog(
        Settings(api_key="k", openapi_url="https://spec.test/o.json"), fake.transport
    )
    await catalog.list_endpoints(None)
    await catalog.list_endpoints("ads")
    assert [str(request.url) for request in fake.requests] == ["https://spec.test/o.json"]


async def test_unreachable_spec_is_a_clear_tool_error(fake: FakeAdsApi) -> None:
    fake.handler = lambda _request: httpx2.Response(503)
    server = build_server(Settings(api_key="k"), fake.transport)
    async with Client(server) as client:
        result = await client.call_tool("openai_ads_list_endpoints", {})
    assert result.is_error
    assert "could not load the OpenAPI spec" in str(result.content[0])
