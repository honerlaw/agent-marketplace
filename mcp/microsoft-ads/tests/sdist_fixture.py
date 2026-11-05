"""A tiny msads sdist, built in memory from trimmed copies of the SDK's generated code.

Each source below keeps the exact shapes `catalog_extract` reads in the real SDK: the
public method's annotations, the `_serialize` method's `method=` / `resource_path=`
literals, `Field(alias=...)` model fields, `str, Enum` and `Flag` enums, and a base's
`from_dict` that dispatches on `type`.
"""

import hashlib
import io
import tarfile
from collections.abc import Mapping

ROOT = "msads-13.0.30.1"

CAMPAIGN_API = """
from typing import Any, Dict


class CampaignManagementServiceApi:
    def add_campaigns(
        self, add_campaigns_request: AddCampaignsRequest, _request_timeout=None,
    ) -> AddCampaignsResponse:
        return self._add_campaigns_serialize(add_campaigns_request)

    def add_campaigns_with_http_info(self, add_campaigns_request: AddCampaignsRequest):
        pass

    def _add_campaigns_serialize(self, add_campaigns_request):
        return self.api_client.param_serialize(
            method='POST', resource_path='/CampaignManagement/v13/Campaigns', body=None,
        )

    def delete_campaigns(
        self, delete_campaigns_request: DeleteCampaignsRequest,
    ) -> DeleteCampaignsResponse:
        pass

    def _delete_campaigns_serialize(self, delete_campaigns_request):
        return self.api_client.param_serialize(
            method='DELETE', resource_path='/CampaignManagement/v13/Campaigns',
        )

    def get_bsc_countries(self, body: Dict[str, Any]) -> GetBSCCountriesResponse:
        pass

    def _get_bsc_countries_serialize(self, body):
        return self.api_client.param_serialize(
            method='POST', resource_path='/CampaignManagement/v13/BSCCountries/Query',
        )

    def set_account_properties(
        self, set_account_properties_request: SetAccountPropertiesRequest,
    ) -> object:
        pass

    def _set_account_properties_serialize(self, set_account_properties_request):
        return self.api_client.param_serialize(
            method='POST', resource_path='/CampaignManagement/v13/AccountProperties/Set',
        )
"""

REPORTING_API = """
class ReportingServiceApi:
    def submit_generate_report(
        self, submit_generate_report_request: SubmitGenerateReportRequest,
    ) -> SubmitGenerateReportResponse:
        pass

    def _submit_generate_report_serialize(self, submit_generate_report_request):
        return self.api_client.param_serialize(
            method='POST', resource_path='/Reporting/v13/GenerateReport/Submit',
        )
"""

EMPTY_API = """
class SomeServiceApi:
    def __init__(self, api_client=None) -> None:
        self.api_client = api_client
"""

ADD_CAMPAIGNS_REQUEST = """
from pydantic import BaseModel, Field

class AddCampaignsRequest(BaseModel):
    account_id: Optional[StrictStr] = Field(default=None, alias="AccountId")
    campaigns: Optional[List[Optional[Campaign]]] = Field(default=None, alias="Campaigns")
    __properties: ClassVar[List[str]] = ["AccountId", "Campaigns"]
    model_config = ConfigDict(populate_by_name=True)
"""

CAMPAIGN = """
class Campaign(BaseModel):
    id: Optional[StrictStr] = Field(default=None, alias="Id")
    status: Optional[CampaignStatus] = Field(default=None, alias="Status")
    daily_budget: Optional[StrictFloat] = Field(default=None, alias="DailyBudget")
    bid_adjustment: Optional[StrictInt] = Field(default=None, alias="BidAdjustment")
    multimedia_ads_enabled: Optional[StrictBool] = Field(default=None, alias="MultimediaAdsEnabled")
    start_date: Optional[datetime] = Field(default=None, alias="StartDate")
    details: Optional[StrictDict[str, Str]] = Field(default=None, alias="Details")
    grid: Optional[List[Optional[List[StrictStr]]]] = Field(default=None, alias="Grid")
"""

CAMPAIGN_STATUS = """
from enum import Enum

class CampaignStatus(str, Enum):
    ACTIVE = 'Active'
    ACTIVE = 'Active'

    PAUSED = 'Paused'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        return cls(json.loads(json_str))
"""

AD = """
class Ad(BaseModel):
    @classmethod
    def from_dict(cls, obj):
        type = obj.get("Type")
        if type == "ResponsiveSearch":
            from openapi_client.models.campaign.responsive_search_ad import ResponsiveSearchAd
            return ResponsiveSearchAd.from_dict(obj)
        if type == "ResponsiveSearchAd":
            from openapi_client.models.campaign.responsive_search_ad import ResponsiveSearchAd
            return ResponsiveSearchAd.from_dict(obj)
        if type == "Mystery":
            from openapi_client.models.campaign.mystery_ad import MysteryAd
            return MysteryAd.from_dict(obj)
        if obj is None:
            return None
        return cls.model_validate(obj)
"""

RESPONSIVE_SEARCH_AD = """
class ResponsiveSearchAd(Ad):
    type: Optional[AdType] = Field(default=None, alias="Type")
    path1: Optional[StrictStr] = Field(default=None, alias="Path1")
"""

MYSTERY_AD = """
class MysteryAd(Ad):
    type: Optional[StrictStr] = Field(default=None, alias="Type")
"""

AD_TYPE = """
class AdType(str, Enum):
    RESPONSIVESEARCH = 'ResponsiveSearch'
"""

AD_ADDITIONAL_FIELD = """
from enum import Flag, auto

class AdAdditionalField(Flag):
    NONE = auto()
    VIDEOS = auto()

    def _to_str(self) -> str:
        _NAME_MAPPING = {
            AdAdditionalField.NONE: 'None',
            AdAdditionalField.VIDEOS: 'Videos',
        }
        return ", ".join(_NAME_MAPPING[flag] for flag in AdAdditionalField if flag & self)
"""

LICENSE = "Bing Ads Python SDK\n\nCopyright (c) Microsoft Corporation\n\nMIT License\n"

API_FILES = {
    "ad_insight_service_api.py": EMPTY_API,
    "bulk_service_api.py": EMPTY_API,
    "campaign_management_service_api.py": CAMPAIGN_API,
    "customer_billing_service_api.py": EMPTY_API,
    "customer_management_service_api.py": EMPTY_API,
    "reporting_service_api.py": REPORTING_API,
}
CAMPAIGN_MODELS = {
    "__init__.py": "from openapi_client.models.campaign.ad import Ad\n",
    "add_campaigns_request.py": ADD_CAMPAIGNS_REQUEST,
    "campaign.py": CAMPAIGN,
    "campaign_status.py": CAMPAIGN_STATUS,
    "ad.py": AD,
    "responsive_search_ad.py": RESPONSIVE_SEARCH_AD,
    "mystery_ad.py": MYSTERY_AD,
    "ad_type.py": AD_TYPE,
    "ad_additional_field.py": AD_ADDITIONAL_FIELD,
    "README.md": "not a module",
}


def fixture_files() -> dict[str, str]:
    """Every file of the fixture sdist, keyed by its path below the top directory."""
    files = {f"openapi_client/api/{name}": source for name, source in API_FILES.items()}
    files.update(
        {f"openapi_client/models/campaign/{name}": text for name, text in CAMPAIGN_MODELS.items()}
    )
    files["openapi_client/models/bulk/campaign.py"] = "class Campaign(BaseModel):\n    pass\n"
    files["LICENSE"] = LICENSE
    return files


def make_sdist(changes: Mapping[str, str | None] | None = None) -> bytes:
    """Return a .tar.gz of the fixture; `changes` replaces (or, with None, drops) files."""
    files: dict[str, str | None] = {**fixture_files(), **(changes or {})}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        archive.addfile(_directory(ROOT))
        for path, text in sorted(files.items()):
            if text is not None:
                data = text.encode()
                info = tarfile.TarInfo(f"{ROOT}/{path}")
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def sha256(data: bytes) -> str:
    """Return the hex sha256 of `data`."""
    return hashlib.sha256(data).hexdigest()


def _directory(name: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE
    return info
