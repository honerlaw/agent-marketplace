"""The guards on their own; test_tools.py proves each one stops a request going out."""

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from clerk_mcp.safety import check_method, check_path, check_query


@pytest.mark.parametrize("method", ["GET", "get", "Post", "put", "PATCH", "delete"])
def test_allowed_methods_come_back_upper_cased(method: str) -> None:
    assert check_method(method, read_only=False) == method.upper()


@pytest.mark.parametrize("method", ["HEAD", "OPTIONS", "TRACE", "CONNECT", ""])
def test_other_methods_are_refused(method: str) -> None:
    with pytest.raises(ToolError, match="method must be one of"):
        check_method(method, read_only=False)


def test_read_only_allows_get_in_any_case() -> None:
    assert check_method("get", read_only=True) == "GET"


@pytest.mark.parametrize("method", ["POST", "put", "PATCH", "delete"])
def test_read_only_refuses_writes(method: str) -> None:
    with pytest.raises(ToolError, match="read-only"):
        check_method(method, read_only=True)


@pytest.mark.parametrize(
    "path", ["/users", "/users/user_2abc/ban", "/logs/1776207110588:3f2a-uuid", "/v1-ish"]
)
def test_plain_paths_pass(path: str) -> None:
    assert check_path(path) == path


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("users", "start with '/'"),
        ("https://evil.test/x", "start with '/'"),
        ("/x/https://evil.test", "relative to /v1"),
        ("/users?limit=1", "must not contain"),
        ("/users#x", "must not contain"),
        ("/users\\x", "must not contain"),
        ("/users/%2e%2e", "must not contain"),
        ("/users/%2E%2E/x", "must not contain"),
        ("/users%2fx", "must not contain"),
        ("/users%5cx", "must not contain"),
        ("/users/%252e%252e", "must not contain"),
        ("/users/ x", "must not contain"),
        ("/users/\tx", "must not contain"),
        ("/users/\nx", "must not contain"),
        ("/users/" + chr(0xE9), "must not contain"),
        ("/users/" + chr(0xFF0E) * 2, "must not contain"),
        ("//evil.test/x", "segments"),
        ("/users/..", "segments"),
        ("/users/../instance", "segments"),
        ("/users/.", "segments"),
        ("/users/", "segments"),
        ("/users//x", "segments"),
        ("/", "segments"),
    ],
)
def test_unsafe_paths_are_refused(path: str, reason: str) -> None:
    with pytest.raises(ToolError, match=reason):
        check_path(path)


def test_query_passes_through() -> None:
    assert check_query({"limit": 20, "order_by": "-created_at"}) == {
        "limit": 20,
        "order_by": "-created_at",
    }
    assert check_query(None) == {}


@pytest.mark.parametrize("key", ["__clerk_api_version", "__Clerk_API_Version"])
def test_version_query_key_is_refused_in_any_case(key: str) -> None:
    with pytest.raises(ToolError, match="pins the API version"):
        check_query({key: "2021-02-05"})
