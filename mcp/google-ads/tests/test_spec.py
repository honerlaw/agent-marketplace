"""Discovery: listing and describing operations and schemas from the Discovery document."""

import json
from dataclasses import replace
from pathlib import Path

import httpx2
import pytest
from mcp import Client

from google_ads_mcp.config import Settings
from google_ads_mcp.server import build_server
from google_ads_mcp.spec import display_template, resolve_refs
from tests.conftest import FIXTURE_DISCOVERY, FakeCredentials, FakeGoogleAds, call, error_text

pytestmark = pytest.mark.anyio

PREFIX = "GoogleAdsGoogleadsV26"
AD_GROUP_MUTATE = "/customers/{customerId}/adGroups:mutate"
LIST = "google_ads_list_endpoints"
SELECTED_CHANNELS = (
    f"{PREFIX}Resources_AdGroupDemandGenAdGroupSettingsDemandGenChannelControls"
    "_DemandGenSelectedChannels"
)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "v26/customers/{+customerId}/googleAds:search",
            "/customers/{customerId}/googleAds:search",
        ),
        ("v26/customers:listAccessibleCustomers", "/customers:listAccessibleCustomers"),
        ("v26/{+name}", "/{name}"),
        ("v27/{+resourceName}", "/{resourceName}"),
        ("v26:listPlannableLocations", ":listPlannableLocations"),
    ],
)
def test_templates_drop_the_version_and_reserved_expansion(path: str, expected: str) -> None:
    assert display_template(path) == expected


async def test_endpoints_are_listed_in_one_spelling(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    result = await call(settings, fake, "google_ads_list_endpoints", {})
    assert result.structured_content is not None
    lines = result.structured_content["result"]
    assert isinstance(lines, list)
    assert len(lines) == 10
    assert (
        "GET /customers:listAccessibleCustomers — Returns resource names of customers "
        in (lines[0])
    )
    assert any(line.startswith(f"POST {AD_GROUP_MUTATE} — ") for line in lines)
    plannable = "POST :listPlannableLocations — Returns the list of plannable locations"
    assert any(line.startswith(plannable) for line in lines)
    assert not any("{+" in line or "v26" in line for line in lines)
    assert fake.requests == []


async def test_summaries_are_one_short_sentence(
    settings: Settings, fake: FakeGoogleAds, tmp_path: Path
) -> None:
    methods = {
        "long": {"httpMethod": "GET", "path": "v26/long", "description": "word " * 40},
        "two": {"httpMethod": "GET", "path": "v26/two", "description": "First.  Second."},
        "bare": {"httpMethod": "GET", "path": "v26/bare", "id": "googleads.bare"},
    }
    document = tmp_path / "discovery.json"
    document.write_text(json.dumps({"resources": {"r": {"methods": methods}}}), encoding="utf-8")
    result = await call(replace(settings, discovery_path=str(document)), fake, LIST, {})
    assert result.structured_content is not None
    long_line, two_line, bare_line = result.structured_content["result"]
    assert long_line == "GET /long — " + ("word " * 20).strip() + "…"
    assert two_line == "GET /two — First."
    assert bare_line == "GET /bare — googleads.bare"


async def test_the_filter_is_a_case_insensitive_substring(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    result = await call(settings, fake, "google_ads_list_endpoints", {"text_filter": "ADGROUPS"})
    assert result.structured_content == {
        "result": [f"POST {AD_GROUP_MUTATE} — Creates, updates, or removes ad groups."]
    }


async def test_describe_expands_one_level_by_default(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    arguments = {"method": "POST", "path": AD_GROUP_MUTATE}
    result = await call(settings, fake, "google_ads_describe_endpoint", arguments)
    described = result.structured_content
    assert described is not None
    assert (described["id"], described["path"]) == (
        "googleads.customers.adGroups.mutate",
        AD_GROUP_MUTATE,
    )
    assert "customerId" in described["parameters"]
    request = described["request"]
    assert isinstance(request, dict)
    operations = request["properties"]["operations"]["items"]
    assert operations == {"$ref": f"{PREFIX}Services__AdGroupOperation"}


async def test_the_shorts_flag_is_reached_one_schema_at_a_time(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    chain = [
        (f"{PREFIX}Services__AdGroupOperation", "create"),
        (f"{PREFIX}Resources__AdGroup", "demandGenAdGroupSettings"),
        (f"{PREFIX}Resources_AdGroup_DemandGenAdGroupSettings", "channelControls"),
        (
            f"{PREFIX}Resources_AdGroupDemandGenAdGroupSettings_DemandGenChannelControls",
            "selectedChannels",
        ),
    ]
    for name, field in chain:
        result = await call(settings, fake, "google_ads_describe_schema", {"name": name})
        assert result.structured_content is not None
        assert "$ref" in result.structured_content["properties"][field]
    last = await call(settings, fake, "google_ads_describe_schema", {"name": SELECTED_CHANNELS})
    assert last.structured_content is not None
    assert "youtubeShorts" in last.structured_content["properties"]


async def test_depth_expands_nested_refs(settings: Settings, fake: FakeGoogleAds) -> None:
    arguments = {"name": f"{PREFIX}Services__AdGroupOperation", "depth": 2}
    result = await call(settings, fake, "google_ads_describe_schema", arguments)
    assert result.structured_content is not None
    create = result.structured_content["properties"]["create"]
    assert "demandGenAdGroupSettings" in create["properties"]


async def test_a_shared_catch_all_template_returns_every_match(
    settings: Settings, fake: FakeGoogleAds
) -> None:
    arguments = {"method": "GET", "path": "/{name}"}
    result = await call(settings, fake, "google_ads_describe_endpoint", arguments)
    described = result.structured_content
    assert described is not None
    ids = {operation["id"] for operation in described["operations"]}
    assert ids == {"googleads.customers.operations.get", "googleads.customers.operations.list"}


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        (
            "google_ads_describe_endpoint",
            {"method": "GET", "path": "/customers/1/adGroups:mutate"},
            "copy the template exactly",
        ),
        ("google_ads_describe_schema", {"name": "Nope"}, "no schema 'Nope'"),
    ],
)
async def test_unknown_names_are_tool_errors(
    settings: Settings, fake: FakeGoogleAds, tool: str, arguments: dict[str, object], message: str
) -> None:
    result = await call(settings, fake, tool, arguments)
    assert message in error_text(result)


def test_a_property_keeps_its_own_description_when_expanded() -> None:
    node = {"$ref": "Known", "description": "How this field is used."}
    schemas: dict[str, object] = {"Known": {"type": "object", "description": "Generic."}}
    assert resolve_refs(node, schemas, 1) == {
        "type": "object",
        "description": "How this field is used.",
    }


async def test_an_oversized_description_is_refused(settings: Settings, fake: FakeGoogleAds) -> None:
    small = replace(settings, max_response_bytes=100)
    arguments = {"method": "POST", "path": AD_GROUP_MUTATE}
    result = await call(small, fake, "google_ads_describe_endpoint", arguments)
    assert "over 100 (GOOGLE_ADS_MAX_RESPONSE_BYTES)" in error_text(result)


def test_refs_to_unknown_schemas_stay_as_markers() -> None:
    node = {"a": [{"$ref": "Missing"}], "b": {"$ref": "Known"}}
    resolved = resolve_refs(node, {"Known": {"type": "string"}}, 1)
    assert resolved == {"a": [{"$ref": "Missing"}], "b": {"type": "string"}}


async def test_the_document_is_fetched_from_google_once(settings: Settings) -> None:
    text = FIXTURE_DISCOVERY.read_text(encoding="utf-8")
    fake = FakeGoogleAds(handler=lambda _request: httpx2.Response(200, text=text))
    remote = replace(settings, discovery_path=None)
    async with Client(build_server(remote, fake.transport, FakeCredentials)) as client:
        first = await client.call_tool(LIST, {"text_filter": "requested field"})
        second = await client.call_tool(LIST, {"text_filter": "requested field"})
    assert first.structured_content == second.structured_content
    assert first.structured_content == {
        "result": ["GET /{resourceName} — Returns just the requested field."]
    }
    (request,) = fake.requests
    assert str(request.url) == "https://googleads.googleapis.com/$discovery/rest?version=v26"
    assert "authorization" not in request.headers


async def test_an_unreachable_document_is_a_tool_error(settings: Settings) -> None:
    fake = FakeGoogleAds(handler=lambda _request: httpx2.Response(503))
    remote = replace(settings, discovery_path=None)
    result = await call(remote, fake, "google_ads_list_endpoints", {})
    assert "could not load the Discovery document" in error_text(result)


async def test_an_unreadable_file_is_a_tool_error(
    settings: Settings, fake: FakeGoogleAds, tmp_path: Path
) -> None:
    missing = replace(settings, discovery_path=str(tmp_path / "missing.json"))
    result = await call(missing, fake, "google_ads_list_endpoints", {})
    assert "could not read the Discovery document" in error_text(result)


async def test_a_corrupt_file_is_a_tool_error(
    settings: Settings, fake: FakeGoogleAds, tmp_path: Path
) -> None:
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{", encoding="utf-8")
    result = await call(
        replace(settings, discovery_path=str(corrupt)), fake, "google_ads_list_endpoints", {}
    )
    assert "not valid JSON" in error_text(result)
