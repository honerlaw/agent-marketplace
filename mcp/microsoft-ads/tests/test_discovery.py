"""The committed catalog, and the three discovery tools that read it."""

import json
from collections import Counter
from dataclasses import replace
from importlib import resources

import pytest

from microsoft_ads_mcp import catalog_build
from microsoft_ads_mcp.catalog import OperationCatalog, _subtype_view, load_catalog
from microsoft_ads_mcp.config import Settings
from tests.conftest import FakeMicrosoft, call, error_text, structured

pytestmark = pytest.mark.anyio

# A test budget for describe output, well below the 2 MiB default product cap.
DESCRIBE_BUDGET = 50_000
PINNED_COUNTS = {
    "CampaignManagement": 195,
    "CustomerManagement": 39,
    "AdInsight": 33,
    "CustomerBilling": 16,
    "Bulk": 6,
    "Reporting": 2,
}


def test_the_catalog_records_the_pinned_sdist() -> None:
    assert load_catalog()["source"] == {
        "package": catalog_build.PACKAGE,
        "version": catalog_build.VERSION,
        "sdist_sha256": catalog_build.SDIST_SHA256,
    }


def test_the_catalog_holds_the_pinned_operation_counts() -> None:
    operations = load_catalog()["operations"]
    assert Counter(entry["service"] for entry in operations.values()) == PINNED_COUNTS
    assert len(operations) == sum(PINNED_COUNTS.values())


@pytest.mark.parametrize(
    ("name", "method", "path"),
    [
        ("AddCampaigns", "POST", "/CampaignManagement/v13/Campaigns"),
        ("DeleteCampaigns", "DELETE", "/CampaignManagement/v13/Campaigns"),
        ("GetCampaignsByAccountId", "POST", "/CampaignManagement/v13/Campaigns/QueryByAccountId"),
        ("SubmitGenerateReport", "POST", "/Reporting/v13/GenerateReport/Submit"),
    ],
)
def test_named_operations_have_their_method_and_path(name: str, method: str, path: str) -> None:
    entry = load_catalog()["operations"][name]
    assert (entry["method"], entry["path"]) == (method, path)


def test_responsive_search_ads_use_the_documented_type_value() -> None:
    ad = load_catalog()["types"]["CampaignManagement"]["Ad"]
    assert ad["subtypes"]["ResponsiveSearchAd"] == {
        "values": ["ResponsiveSearch", "ResponsiveSearchAd"],
        "documented": "ResponsiveSearch",
    }


def test_the_sdk_license_ships_beside_the_catalog() -> None:
    text = resources.files("microsoft_ads_mcp").joinpath("catalog.LICENSE").read_text()
    assert "MIT License" in text
    assert "Copyright (c) Microsoft Corporation" in text


async def test_list_operations_unfiltered_fits_the_default_cap(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    result = await call(settings, fake, "microsoft_ads_list_operations", {})
    lines = structured(result)["result"]
    assert isinstance(lines, list)
    assert len(lines) == sum(PINNED_COUNTS.values())
    assert len(json.dumps(lines)) < settings.max_response_bytes
    assert (
        "CampaignManagement.AddCampaigns — POST /CampaignManagement/v13/Campaigns"
        " → AddCampaignsRequest"
    ) in lines


async def test_list_operations_filters_case_insensitively(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    result = await call(settings, fake, "microsoft_ads_list_operations", {"text_filter": "REPORT"})
    lines = structured(result)["result"]
    assert isinstance(lines, list)
    assert any("SubmitGenerateReport" in line for line in lines)
    assert all("report" in line.lower() for line in lines)


async def test_describe_operation_reaches_one_named_type_down(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    arguments = {"operation": "add_campaigns"}
    result = await call(settings, fake, "microsoft_ads_describe_operation", arguments)
    described = structured(result)
    assert described["operation"] == "AddCampaigns"
    assert described["request_fields"] == {"AccountId": "string", "Campaigns": "list[Campaign]"}
    campaign = described["types"]["Campaign"]
    assert "DailyBudget" in campaign["fields"]
    assert "BudgetType" in campaign["fields"]
    assert "Paused" in described["enums"]["CampaignStatus"]["values"]
    assert len(json.dumps(described)) < DESCRIBE_BUDGET


async def test_describe_operation_without_a_request_model(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    arguments = {"operation": "CampaignManagement.GetBSCCountries"}
    result = await call(settings, fake, "microsoft_ads_describe_operation", arguments)
    described = structured(result)
    assert described["request"] == "object"
    assert described["request_fields"] == {}


async def test_describe_type_lists_subtypes_with_their_type_value(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    result = await call(settings, fake, "microsoft_ads_describe_type", {"name": "Ad"})
    described = structured(result)
    assert described["subtypes"]["ResponsiveSearchAd"] == {
        "Type": "ResponsiveSearch",
        "sdk_aliases": ["ResponsiveSearchAd"],
        "documented": True,
    }
    assert "Type" in str(described["note"])
    assert len(json.dumps(described)) < DESCRIBE_BUDGET


async def test_describe_type_includes_inherited_fields_and_enums(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    arguments = {"name": "ResponsiveSearchAd"}
    result = await call(settings, fake, "microsoft_ads_describe_type", arguments)
    described = structured(result)
    assert described["base"] == "Ad"
    assert "Headlines" in described["fields"]
    assert "ResponsiveSearch" in described["enums"]["AdType"]["values"]


async def test_describe_type_resolves_an_enum_and_marks_flags(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    status = await call(settings, fake, "microsoft_ads_describe_type", {"name": "CampaignStatus"})
    flags = await call(settings, fake, "microsoft_ads_describe_type", {"name": "AdAdditionalField"})
    assert "Paused" in structured(status)["values"]
    assert "flags" not in structured(status)
    assert "combine" in str(structured(flags)["flags"])


async def test_an_ambiguous_type_name_names_its_services(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    ambiguous = await call(settings, fake, "microsoft_ads_describe_type", {"name": "Keyword"})
    message = error_text(ambiguous)
    assert "CampaignManagement" in message
    assert "AdInsight" in message
    arguments = {"name": "Keyword", "service": "CampaignManagement"}
    chosen = await call(settings, fake, "microsoft_ads_describe_type", arguments)
    assert structured(chosen)["service"] == "CampaignManagement"


async def test_an_unknown_type_or_operation_is_a_clear_error(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    no_type = await call(settings, fake, "microsoft_ads_describe_type", {"name": "Nope"})
    no_operation = await call(
        settings, fake, "microsoft_ads_describe_operation", {"operation": "Nope"}
    )
    assert "check the spelling" in error_text(no_type)
    assert "microsoft_ads_list_operations" in error_text(no_operation)


async def test_output_over_the_cap_is_refused_not_truncated(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    small = replace(settings, max_response_bytes=1000)
    result = await call(small, fake, "microsoft_ads_list_operations", {})
    assert "narrow the filter" in error_text(result)


def test_an_undocumented_subtype_offers_its_first_value() -> None:
    view = _subtype_view({"values": ["A", "B"], "documented": None})
    assert view == {"Type": "A", "sdk_aliases": ["B"], "documented": False}


def test_every_operation_describes_within_budget() -> None:
    catalog = OperationCatalog(load_catalog(), 2 * 1024 * 1024)
    names = load_catalog()["operations"]
    sizes = [len(json.dumps(catalog.describe_operation(name))) for name in names]
    assert max(sizes) < DESCRIBE_BUDGET
