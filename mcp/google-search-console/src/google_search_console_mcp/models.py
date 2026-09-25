"""Typed request bodies, mirroring the API's schemas with snake_case field names."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Dimension = Literal["DATE", "QUERY", "PAGE", "COUNTRY", "DEVICE", "SEARCH_APPEARANCE", "HOUR"]
FilterDimension = Literal["QUERY", "PAGE", "COUNTRY", "DEVICE", "SEARCH_APPEARANCE"]
FilterOperator = Literal[
    "EQUALS", "NOT_EQUALS", "CONTAINS", "NOT_CONTAINS", "INCLUDING_REGEX", "EXCLUDING_REGEX"
]
SearchType = Literal["WEB", "IMAGE", "VIDEO", "NEWS", "DISCOVER", "GOOGLE_NEWS"]
AggregationType = Literal["AUTO", "BY_PROPERTY", "BY_PAGE", "BY_NEWS_SHOWCASE_PANEL"]
DataState = Literal["FINAL", "ALL", "HOURLY_ALL"]


class ApiModel(BaseModel):
    """Serializes to the API's camelCase names; accepts either spelling as input."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def to_api(self) -> dict[str, object]:
        """Return the JSON body the API expects, leaving out unset fields."""
        return self.model_dump(by_alias=True, exclude_none=True)


class DimensionFilter(ApiModel):
    """One filter, e.g. query CONTAINS "shoes"."""

    dimension: FilterDimension
    operator: FilterOperator = "EQUALS"
    expression: str


class DimensionFilterGroup(ApiModel):
    """Filters that must all match (the API only supports AND groups)."""

    group_type: Literal["AND"] = "AND"
    filters: list[DimensionFilter]


class SearchAnalyticsQuery(ApiModel):
    """The body of a Search Analytics query; dates are YYYY-MM-DD in Pacific time."""

    start_date: str = Field(description="First day, inclusive, YYYY-MM-DD")
    end_date: str = Field(description="Last day, inclusive, YYYY-MM-DD")
    dimensions: list[Dimension] | None = Field(default=None, description="Group-by dimensions")
    search_type: SearchType | None = Field(
        default=None, alias="type", description="Search type; the API default is WEB"
    )
    dimension_filter_groups: list[DimensionFilterGroup] | None = None
    aggregation_type: AggregationType | None = None
    row_limit: int | None = Field(default=None, ge=1, le=25000, description="API default 1000")
    start_row: int | None = Field(default=None, ge=0, description="Zero-based offset for paging")
    data_state: DataState | None = Field(
        default=None, description="FINAL (default), ALL (include fresh data) or HOURLY_ALL"
    )
