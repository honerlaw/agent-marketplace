"""Endpoint discovery against a small fixture spec."""

import httpx2
import pytest
from mcp import Client

from openai_mcp.config import Settings
from openai_mcp.server import build_server
from openai_mcp.spec import SpecCatalog, resolve_refs
from tests.conftest import FIXTURE_SPEC, FakeOpenAI

pytestmark = pytest.mark.anyio


async def test_list_endpoints_names_every_operation(settings: Settings) -> None:
    lines = await SpecCatalog(settings).list_endpoints(None)
    assert lines == [
        "GET /models — Lists the currently available models.",
        "POST /files — createFile",
        "GET /files/{file_id} — Returns information about a specific file.",
        "DELETE /files/{file_id} — Delete a file.",
    ]


async def test_list_endpoints_filters_case_insensitively(settings: Settings) -> None:
    assert await SpecCatalog(settings).list_endpoints("DELETE") == [
        "DELETE /files/{file_id} — Delete a file."
    ]


async def test_describe_resolves_refs_and_keeps_success_responses(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("post", "/files", 2)
    assert described["method"] == "POST"
    assert list(described["responses"]) == ["200"]  # type: ignore[call-overload]
    assert described["requestBody"] == {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "purpose": {"type": "string"},
                    },
                }
            }
        }
    }


async def test_describe_unknown_operation_is_an_error(settings: Settings, fake: FakeOpenAI) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        result = await client.call_tool(
            "openai_describe_endpoint", {"method": "PATCH", "path": "/models"}
        )
    assert result.is_error


async def test_describe_depth_is_clamped_to_its_bounds(settings: Settings) -> None:
    catalog = SpecCatalog(settings)
    assert await catalog.describe("get", "/models", 0) == await catalog.describe(
        "get", "/models", 1
    )
    assert await catalog.describe("get", "/models", 99) == await catalog.describe(
        "get", "/models", 6
    )
    assert await catalog.describe("get", "/models", 6) != await catalog.describe(
        "get", "/models", 5
    )


async def test_shallow_describe_leaves_ref_markers(settings: Settings) -> None:
    described = await SpecCatalog(settings).describe("get", "/models", 1)
    assert "#/components/schemas/Model" in str(described["responses"])


def test_recursive_refs_stop_at_the_depth_bound() -> None:
    spec: dict[str, object] = {"a": {"next": {"$ref": "#/a"}}}
    resolved = resolve_refs({"$ref": "#/a"}, spec, 2)
    assert resolved == {"next": {"next": {"$ref": "#/a"}}}


async def test_spec_is_fetched_once_from_the_url(fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(200, text=FIXTURE_SPEC.read_text())
    catalog = SpecCatalog(
        Settings(api_key="k", openapi_url="https://spec.test/o.yaml"), fake.transport
    )
    await catalog.list_endpoints(None)
    await catalog.list_endpoints("files")
    assert [str(request.url) for request in fake.requests] == ["https://spec.test/o.yaml"]


async def test_unreachable_spec_is_a_clear_tool_error(fake: FakeOpenAI) -> None:
    fake.handler = lambda _request: httpx2.Response(503)
    server = build_server(Settings(api_key="k"), fake.transport)
    async with Client(server) as client:
        result = await client.call_tool("openai_list_endpoints", {})
    assert result.is_error
    assert "could not load the OpenAPI spec" in str(result.content[0])
