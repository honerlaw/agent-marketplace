"""URL building and response handling."""

import httpx2
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from google_search_console_mcp.api import describe_response, segment, site_path


@pytest.mark.parametrize(
    ("value", "encoded"),
    [
        ("https://www.example.com/", "https%3A%2F%2Fwww.example.com%2F"),
        ("sc-domain:example.com", "sc-domain%3Aexample.com"),
        ("../../x?y#z", "..%2F..%2Fx%3Fy%23z"),
    ],
)
def test_segment_keeps_a_value_in_one_segment(value: str, encoded: str) -> None:
    assert segment(value) == encoded


def test_site_path_encodes_every_part() -> None:
    path = site_path("sc-domain:example.com", "sitemaps", "https://example.com/a.xml")
    assert path == (
        "/webmasters/v3/sites/sc-domain%3Aexample.com/sitemaps/https%3A%2F%2Fexample.com%2Fa.xml"
    )


def test_success_returns_the_json_object() -> None:
    assert describe_response(httpx2.Response(200, json={"rows": []})) == {"rows": []}


def test_empty_success_reports_the_status() -> None:
    assert describe_response(httpx2.Response(204)) == {"status": 204}


def test_non_object_json_is_wrapped() -> None:
    assert describe_response(httpx2.Response(200, json=[1])) == {"result": [1]}


def test_google_error_message_is_surfaced() -> None:
    response = httpx2.Response(403, json={"error": {"code": 403, "message": "No access"}})
    with pytest.raises(ToolError, match="returned 403: No access"):
        describe_response(response)


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(502, text="Bad gateway"),
        httpx2.Response(502, json={"unexpected": "Bad gateway"}),
        httpx2.Response(502, json=["Bad gateway"]),
    ],
)
def test_unstructured_errors_fall_back_to_the_body(response: httpx2.Response) -> None:
    with pytest.raises(ToolError, match=r"returned 502: .*Bad gateway"):
        describe_response(response)
