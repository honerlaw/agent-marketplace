"""The path and header guards that keep credentials on the Google Ads API."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from google_ads_mcp.safety import check_headers, check_path

UNSAFE_PATHS = [
    "customers",
    "https://evil.test/v26/customers",
    "//evil.test/customers",
    "/%2Fevil.test/customers",
    "/customers/../../admin",
    "/customers/%2e%2e/admin",
    "/customers/1/googleAds:search?alt=json",
    "/customers#top",
    "/customers\\x",
    "/redirect/https://evil.test",
    "https:/customers",
    "/a b",
    "/a\tb",
    "/a%0Ab",
    "/café",
    ":listPlannableLocations/x",
    ":@evil.test",
    ":",
]
SAFE_PATHS = [
    "/customers:listAccessibleCustomers",
    "/customers/1/googleAds:search",
    "/customers/1/adGroups:mutate",
    "/customers/1/operations/2",
    ":listPlannableLocations",
]


@pytest.mark.parametrize("path", SAFE_PATHS)
def test_plain_paths_pass(path: str) -> None:
    assert check_path(path) == path


@pytest.mark.parametrize("path", UNSAFE_PATHS)
def test_unsafe_paths_are_refused(path: str) -> None:
    with pytest.raises(ToolError, match="path must"):
        check_path(path)


def test_no_headers_is_fine() -> None:
    assert check_headers(None) == {}


@pytest.mark.parametrize("name", ["Login-Customer-Id", "linked-customer-id"])
def test_customer_id_headers_are_normalized(name: str) -> None:
    assert check_headers({name: " 123-456-7890 "}) == {name.lower(): "1234567890"}


@pytest.mark.parametrize("value", ["abc", "12 34", "", "123-456-789x", "١٢"])
def test_customer_id_headers_must_be_ids(value: str) -> None:
    with pytest.raises(ToolError, match="must be a customer id"):
        check_headers({"login-customer-id": value})


@pytest.mark.parametrize(
    "name",
    [
        "Authorization",
        "Host",
        "User-Agent",
        "Accept-Encoding",
        "Content-Length",
        "X-HTTP-Method-Override",
        "X-Trace",
    ],
)
def test_every_other_header_is_refused(name: str) -> None:
    with pytest.raises(ToolError, match="only \\['linked-customer-id', 'login-customer-id'\\]"):
        check_headers({name: "x", "login-customer-id": "1"})
