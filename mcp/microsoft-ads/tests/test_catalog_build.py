"""The catalog builder, over a small fixture sdist; every unknown shape fails loudly."""

import json
from pathlib import Path

import pytest

from microsoft_ads_mcp import catalog_build
from microsoft_ads_mcp.catalog_build import Catalog, build, main, write
from microsoft_ads_mcp.catalog_extract import CatalogError
from tests.sdist_fixture import CAMPAIGN_API, LICENSE, make_sdist, sha256


def built(changes: dict[str, str | None] | None = None) -> Catalog:
    """Build the fixture catalog, with `changes` applied to the fixture's files."""
    sdist = make_sdist(changes)
    catalog, _ = build(sdist, sha256(sdist))
    return catalog


def refusal(changes: dict[str, str | None]) -> str:
    """Return the CatalogError message building the changed fixture raises."""
    sdist = make_sdist(changes)
    with pytest.raises(CatalogError) as caught:
        build(sdist, sha256(sdist))
    return str(caught.value)


CAMPAIGN_API_PATH = "openapi_client/api/campaign_management_service_api.py"
CAMPAIGN_MODEL = "openapi_client/models/campaign/campaign.py"


def test_operations_carry_method_path_and_models() -> None:
    operations = built()["operations"]
    assert sorted(operations) == [
        "AddCampaigns",
        "DeleteCampaigns",
        "GetBSCCountries",
        "SetAccountProperties",
        "SubmitGenerateReport",
    ]
    assert operations["AddCampaigns"] == {
        "service": "CampaignManagement",
        "method": "POST",
        "path": "/CampaignManagement/v13/Campaigns",
        "request": "AddCampaignsRequest",
        "response": "AddCampaignsResponse",
    }
    assert operations["DeleteCampaigns"]["method"] == "DELETE"
    assert operations["SubmitGenerateReport"]["service"] == "Reporting"


def test_an_operation_without_a_request_or_response_model_is_still_named() -> None:
    operations = built()["operations"]
    assert operations["GetBSCCountries"]["request"] == "object"
    assert operations["SetAccountProperties"]["response"] == "object"


def test_fields_are_wire_names_with_readable_types() -> None:
    fields = dict(built()["types"]["CampaignManagement"]["Campaign"]["fields"])
    assert fields == {
        "Id": "string",
        "Status": "CampaignStatus",
        "DailyBudget": "number",
        "BidAdjustment": "integer",
        "MultimediaAdsEnabled": "boolean",
        "StartDate": "datetime",
        "Details": "object",
        "Grid": "list[list[string]]",
    }
    request = built()["types"]["CampaignManagement"]["AddCampaignsRequest"]
    assert request["fields"] == [["AccountId", "string"], ["Campaigns", "list[Campaign]"]]


def test_enums_and_flags_keep_their_wire_values_once() -> None:
    enums = built()["enums"]["CampaignManagement"]
    assert enums["CampaignStatus"] == {"values": ["Active", "Paused"]}
    assert enums["AdAdditionalField"] == {"values": ["None", "Videos"], "flags": True}


def test_subtypes_name_the_documented_type_value() -> None:
    ad = built()["types"]["CampaignManagement"]["Ad"]
    assert ad["base"] is None
    assert "discriminator" not in ad
    assert ad["subtypes"] == {
        "ResponsiveSearchAd": {
            "values": ["ResponsiveSearch", "ResponsiveSearchAd"],
            "documented": "ResponsiveSearch",
        },
        "MysteryAd": {"values": ["Mystery"], "documented": None},
    }
    subtype = built()["types"]["CampaignManagement"]["ResponsiveSearchAd"]
    assert subtype["base"] == "Ad"


def test_a_subtype_missing_from_the_models_has_no_documented_value() -> None:
    catalog = built({"openapi_client/models/campaign/mystery_ad.py": None})
    subtypes = catalog["types"]["CampaignManagement"]["Ad"]["subtypes"]
    assert subtypes["MysteryAd"] == {"values": ["Mystery"], "documented": None}


def test_each_service_gets_its_own_types() -> None:
    catalog = built()
    assert "Campaign" in catalog["types"]["Bulk"]
    assert sorted(catalog["types"]) == sorted(catalog["enums"])
    assert len(catalog["types"]) == 6


def test_source_records_the_pin_and_the_license_is_returned() -> None:
    sdist = make_sdist()
    catalog, license_text = build(sdist, sha256(sdist))
    assert catalog["source"] == {
        "package": "msads",
        "version": catalog_build.VERSION,
        "sdist_sha256": sha256(sdist),
    }
    assert license_text == LICENSE


def test_a_wrong_sha256_is_refused() -> None:
    with pytest.raises(CatalogError, match="sha256"):
        build(make_sdist(), "0" * 64)


def test_a_missing_file_is_refused() -> None:
    assert "LICENSE" in refusal({"LICENSE": None})
    reporting = "openapi_client/api/reporting_service_api.py"
    assert "reporting_service_api.py" in refusal({reporting: None})


def test_an_operation_without_a_literal_path_is_refused() -> None:
    source = CAMPAIGN_API.replace(
        "resource_path='/CampaignManagement/v13/Campaigns', body=None", "resource_path=path"
    )
    assert "literal resource_path" in refusal({CAMPAIGN_API_PATH: source})


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (
            "method='POST', resource_path='/CampaignManagement",
            "method='HEAD', resource_path='/CampaignManagement",
        ),
        ("/CampaignManagement/v13/Campaigns', body", "/Reporting/v13/Campaigns', body"),
    ],
)
def test_an_unexpected_method_or_service_path_is_refused(old: str, new: str) -> None:
    assert "unexpected" in refusal({CAMPAIGN_API_PATH: CAMPAIGN_API.replace(old, new)})


def test_colliding_operation_names_are_refused() -> None:
    source = CAMPAIGN_API + (
        "class Again:\n"
        "    def add_copy(self, request: ADDCAMPAIGNSRequest) -> X:\n"
        "        pass\n"
        "    def _add_copy_serialize(self, request):\n"
        "        return f(method='POST', resource_path='/CampaignManagement/v13/Copy')\n"
    )
    assert "collide" in refusal({CAMPAIGN_API_PATH: source})


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("-> AddCampaignsResponse", "-> Optional[AddCampaignsResponse]", "not a plain name"),
        (
            "self, add_campaigns_request: AddCampaignsRequest, _request_timeout=None,",
            "self",
            "no annotated request parameter",
        ),
        (
            "self, add_campaigns_request: AddCampaignsRequest, _request_timeout=None,",
            "self, request",
            "no annotated request parameter",
        ),
        (
            "add_campaigns_request: AddCampaignsRequest, _request_timeout=None,",
            "add_campaigns_request: AddCampaigns, _request_timeout=None,",
            "names the operation",
        ),
    ],
)
def test_unexpected_operation_signatures_are_refused(old: str, new: str, expected: str) -> None:
    source = CAMPAIGN_API.replace(old, new)
    if expected == "names the operation":
        source = source.replace("-> AddCampaignsResponse", "-> object")
    assert expected in refusal({CAMPAIGN_API_PATH: source})


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("class C(BaseModel):\n    x: Optional[StrictStr] = Field(default=None)\n", "no alias"),
        ("class C(BaseModel):\n    x: Optional[StrictStr]\n", "no alias"),
        ("class C(BaseModel):\n    x: Optional[StrictStr] = Field(alias=NAME)\n", "string literal"),
        ("class C(BaseModel):\n    x: Union[A, B] = Field(alias='X')\n", "unsupported"),
        ("class C(BaseModel):\n    x: Tuple[A] = Field(alias='X')\n", "unsupported"),
        ("class C(BaseModel):\n    x: 'A' = Field(alias='X')\n", "unsupported"),
        ("class F(Flag):\n    A = auto()\n", "one name mapping"),
        ("class F(Flag):\n    def _to_str(self):\n        m = {F.A: NAME}\n", "string literal"),
        (
            (
                "class B(BaseModel):\n    def from_dict(cls, obj):\n"
                "        if type == 'X':\n            return None\n"
            ),
            "imports no subclass",
        ),
    ],
)
def test_unexpected_model_shapes_are_refused(source: str, expected: str) -> None:
    assert expected in refusal({CAMPAIGN_MODEL: source})


def test_unrelated_comparisons_in_from_dict_are_ignored() -> None:
    source = (
        "class B(BaseModel):\n    def from_dict(cls, obj):\n"
        "        if obj is None:\n            return None\n"
        "        if kind == 'X':\n            return None\n"
        "        if type == 'X' == other:\n            return None\n"
    )
    entry = built({CAMPAIGN_MODEL: source})["types"]["CampaignManagement"]["B"]
    assert "subtypes" not in entry


def test_write_and_main_produce_sorted_json_and_the_license(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sdist = make_sdist()
    (tmp_path / "msads.tar.gz").write_bytes(sdist)
    monkeypatch.setattr(catalog_build, "SDIST_SHA256", sha256(sdist))
    main([str(tmp_path / "msads.tar.gz"), str(tmp_path)])
    text = (tmp_path / "catalog.json").read_text()
    assert json.loads(text) == built()
    assert text.endswith("}\n")
    assert (tmp_path / "catalog.LICENSE").read_text() == LICENSE
    write(built(), "L", tmp_path)
    assert (tmp_path / "catalog.LICENSE").read_text() == "L"
