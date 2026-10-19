"""The guards: paths, refused parameters and pagination URLs."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp.safety import check_page_url, check_params, check_path, param_names

BASE = "https://graph.facebook.com/v26.0"


@pytest.mark.parametrize("path", ["/act_1/campaigns", "/123", "/me/adaccounts", "/me"])
def test_graph_paths_pass(path: str) -> None:
    assert check_path(path) == path


@pytest.mark.parametrize(
    "path",
    [
        "act_1/campaigns",
        "//evil.example/x",
        "/",
        "/x?access_token=1",
        "/x#frag",
        "/x\\y",
        "https://evil.example/x",
        "/a/../b",
        "/a/./b",
        "/a/%2e%2e/b",
        "/a/%252e%252e/b",
        "/a/%2E/b",
        "/café",
        "/a b",
    ],
)
def test_other_paths_are_refused(path: str) -> None:
    with pytest.raises(ToolError):
        check_path(path)


@pytest.mark.parametrize(
    "name",
    [
        "access_token",
        "ACCESS_TOKEN",
        "appsecret_proof",
        "batch",
        "method",
        "Method",
        "suppress_http_code",
        "callback",
        "access_token[0]",
        " batch",
        "adbatch",
        "access.token",
        "access token",
        "access[token",
        "suppress.http.code",
    ],
)
def test_refused_parameters(name: str) -> None:
    with pytest.raises(ToolError, match="may not set"):
        check_params([name], "query")


def test_other_parameters_pass() -> None:
    check_params(["fields", "limit", "ids", "include_headers", "status"], "body")


def test_param_names_reads_top_level_keys_only() -> None:
    assert param_names({"fields": {"access_token": 1}}) == ["fields"]
    assert param_names(None) == []


def test_a_pagination_url_is_split_and_meta_credentials_dropped() -> None:
    url = f"{BASE}/act_1/campaigns?limit=25&access_token=TOKEN&appsecret_proof=P&after=abc"
    assert check_page_url(url, BASE) == ("/act_1/campaigns", [("limit", "25"), ("after", "abc")])


@pytest.mark.parametrize(
    "url",
    [
        "http://graph.facebook.com/v26.0/act_1/campaigns",
        "https://evil.example/v26.0/act_1/campaigns",
        "https://graph.facebook.com.evil.example/v26.0/x",
        "https://user@graph.facebook.com/v26.0/x",
        "https://graph.facebook.com:8443/v26.0/x",
        "https://graph.facebook.com/v25.0/act_1/campaigns",
        "https://graph.facebook.com/v26.0/act_1/campaigns#x",
        "https://graph.facebook.com/v26.0/a/../b",
        "https://graph.facebook.com/v26.0/",
    ],
)
def test_other_pagination_urls_are_refused(url: str) -> None:
    with pytest.raises(ToolError):
        check_page_url(url, BASE)


@pytest.mark.parametrize("query", ["method=delete", "batch=%5B%5D", "callback=x"])
def test_a_pagination_url_cannot_smuggle_refused_parameters(query: str) -> None:
    with pytest.raises(ToolError, match="may not set"):
        check_page_url(f"{BASE}/act_1/campaigns?{query}", BASE)
