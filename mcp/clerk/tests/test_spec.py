"""Discovery over the fixture spec, and the facts the vendored spec must keep true."""

import hashlib
from importlib import resources

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from clerk_mcp.safety import check_path
from clerk_mcp.spec import CLERK_API_VERSION, MULTIPART_NOTE, SpecCatalog, load_spec

VENDORED_OPERATIONS = 264
VENDORED_MULTIPART = 3
VENDORED_SHA256 = "3b4996ebb952098cb9d95eb05b9478e3dbd27ee780d6478ac671f4d477473569"


def test_listing_marks_multipart_and_filters(catalog: SpecCatalog) -> None:
    assert catalog.list_endpoints(None) == [
        "GET /users — List all users",
        "POST /users — CreateUser",
        f"POST /users/{{user_id}}/profile_image — Set user profile image ({MULTIPART_NOTE})",
    ]
    assert catalog.list_endpoints("PROFILE") == [
        f"POST /users/{{user_id}}/profile_image — Set user profile image ({MULTIPART_NOTE})"
    ]


def test_describe_inlines_refs_to_the_asked_depth(catalog: SpecCatalog) -> None:
    shallow = catalog.describe("get", "/users", 1)
    assert shallow["method"] == "GET"
    assert shallow["summary"] == "List all users"
    assert shallow["parameters"] == [
        {"name": "limit", "in": "query", "schema": {"type": "integer"}}
    ]
    assert list(shallow["responses"]) == ["200"]  # type: ignore[call-overload]
    schema = shallow["responses"]["200"]["content"]["application/json"]["schema"]  # type: ignore[index]
    assert schema == {"type": "array", "items": {"$ref": "#/components/schemas/User"}}
    deep = catalog.describe("GET", "/users", 99)
    deep_schema = deep["responses"]["200"]["content"]["application/json"]["schema"]  # type: ignore[index]
    assert deep_schema["items"] == {"type": "object", "properties": {"id": {"type": "string"}}}
    assert "note" not in shallow


def test_describe_notes_a_multipart_operation(catalog: SpecCatalog) -> None:
    described = catalog.describe("post", "/users/{user_id}/profile_image", 0)
    assert described["note"] == MULTIPART_NOTE


def test_describe_refuses_an_unknown_operation(catalog: SpecCatalog) -> None:
    with pytest.raises(ToolError, match="see clerk_list_endpoints"):
        catalog.describe("DELETE", "/users", 1)


def test_vendored_spec_is_the_pinned_version() -> None:
    catalog = SpecCatalog()
    assert catalog.version() == CLERK_API_VERSION
    lines = catalog.list_endpoints(None)
    assert len(lines) == VENDORED_OPERATIONS
    assert sum(MULTIPART_NOTE in line for line in lines) == VENDORED_MULTIPART


def test_no_vendored_path_template_trips_the_guard() -> None:
    paths = load_spec()["paths"]
    assert isinstance(paths, dict)
    for path in paths:
        filled = path.replace("{", "x").replace("}", "x")
        assert check_path(filled) == filled


def test_license_records_the_source() -> None:
    notice = resources.files("clerk_mcp").joinpath("bapi.LICENSE").read_text("utf-8")
    assert "af85fe9443c550f6de08634ab26abe95d78e6f7e" in notice
    assert "c57d7c310abdda048583ae536692f872988f6c04" in notice
    assert "952872280f03c096952687098bf91925669488d662324ffea27d4efb415ab4e0" in notice
    assert "Copyright (c) 2025 Clerk" in notice
    assert "bapi/2026-08-20.yml" in notice


def test_vendored_spec_bytes_are_pinned() -> None:
    # Any edit to bapi.json fails here; a re-pin updates this hash (README, "To re-pin").
    vendored = resources.files("clerk_mcp").joinpath("bapi.json").read_bytes()
    assert hashlib.sha256(vendored).hexdigest() == VENDORED_SHA256
