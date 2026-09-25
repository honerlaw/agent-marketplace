"""The path, pagination-URL and header guards that keep credentials on the configured host."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from reddit_ads_mcp.config import DEFAULT_BASE_URL
from reddit_ads_mcp.safety import check_headers, check_page_url, check_path

UNSAFE_PATHS = [
    "me",
    "https://evil.test/api/v3/me",
    "//evil.test/me",
    "/%2Fevil.test/me",
    "/campaigns/../../admin",
    "/campaigns/%2e%2e/admin",
    "/campaigns?page.token=x",
    "/campaigns#top",
    "/campaigns\\x",
    "/redirect/https://evil.test",
]

BASE = DEFAULT_BASE_URL
SAFE_PAGE_URLS = [
    f"{BASE}/ad_accounts/a1/campaigns?page.token=abc&page.size=100",
    f"{BASE}/ad_accounts/a1/reports",
    "HTTPS://Ads-Api.Reddit.com/api/v3/ad_accounts/a1/campaigns",
]
UNSAFE_PAGE_URLS = [
    "https://evil.test/api/v3/ad_accounts/a1/campaigns?page.token=abc",
    "http://ads-api.reddit.com/api/v3/campaigns",
    "https://ads-api.reddit.com:8443/api/v3/campaigns",
    "https://user@ads-api.reddit.com/api/v3/campaigns",
    "https://ads-api.reddit.com.evil.test/api/v3/campaigns",
    "https://ads-api.reddit.com/api/v2.0/campaigns",
    "https://ads-api.reddit.com/api/v3",
    "https://ads-api.reddit.com/api/v30/campaigns",
    f"{BASE}/campaigns/../../../admin",
    f"{BASE}/campaigns/%2e%2e/%2e%2e/admin",
    f"{BASE}/campaigns#frag",
    f"{BASE}/campaigns?page.token=x#",
    "/api/v3/campaigns",
    "ads-api.reddit.com/api/v3/campaigns",
]


@pytest.mark.parametrize("path", ["/me", "/ad_accounts/a1/campaigns", "/v1..beta/x"])
def test_plain_paths_pass(path: str) -> None:
    assert check_path(path) == path


@pytest.mark.parametrize("path", UNSAFE_PATHS)
def test_unsafe_paths_are_refused(path: str) -> None:
    with pytest.raises(ToolError):
        check_path(path)


@pytest.mark.parametrize("url", SAFE_PAGE_URLS)
def test_pagination_urls_under_the_base_pass(url: str) -> None:
    assert check_page_url(url, BASE) == url


def test_a_trailing_slash_on_the_base_url_is_ignored() -> None:
    assert check_page_url(SAFE_PAGE_URLS[0], f"{BASE}/") == SAFE_PAGE_URLS[0]


@pytest.mark.parametrize("url", UNSAFE_PAGE_URLS)
def test_pagination_urls_elsewhere_are_refused(url: str) -> None:
    with pytest.raises(ToolError):
        check_page_url(url, BASE)


def test_ordinary_headers_pass() -> None:
    assert check_headers({"X-Trace": "1"}) == {"X-Trace": "1"}
    assert check_headers(None) == {}


@pytest.mark.parametrize("name", ["Authorization", "authorization", "Host", "User-Agent"])
def test_protected_headers_are_refused(name: str) -> None:
    with pytest.raises(ToolError, match="cannot be overridden"):
        check_headers({name: "x"})
