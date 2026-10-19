"""Shared fixtures: settings with sentinel credentials and a recording fake of the Graph API."""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from meta_ads_mcp.config import Settings
from meta_ads_mcp.scrub import appsecret_proof
from meta_ads_mcp.server import build_server

FIXTURE_SPECS = Path(__file__).parent / "fixtures" / "specs"
FIXTURE_HASH = (Path(__file__).parent / "fixtures" / "specs.sha256").read_text().strip()
GRAPH_HOST = "graph.facebook.com"
# Sentinels: if any of these strings shows up in a tool result, error or log, it leaked.
TOKEN = "EAAtokenSENTINEL0123456789"  # noqa: S105 - a fixture value, not a secret
APP_ID = "1818"
APP_SECRET = "appsecretSENTINEL"  # noqa: S105 - a fixture value, not a secret
PROOF = appsecret_proof(TOKEN, APP_SECRET)
SECRETS = (TOKEN, APP_SECRET, PROOF)

Handler = Callable[[httpx2.Request], httpx2.Response]


def answer_ok(_request: httpx2.Request) -> httpx2.Response:
    """Answer an API call with an empty JSON object."""
    return httpx2.Response(200, json={}, headers={"x-fb-trace-id": "trace-1"})


@dataclass
class FakeGraph:
    """A mock transport that records requests and answers with `handler`."""

    handler: Handler = answer_ok
    requests: list[httpx2.Request] = field(default_factory=list)

    @property
    def transport(self) -> httpx2.MockTransport:
        """The transport to inject into the code under test."""
        return httpx2.MockTransport(self._record)

    @property
    def last(self) -> httpx2.Request:
        """The most recent request the fake received."""
        return self.requests[-1]

    def _record(self, request: httpx2.Request) -> httpx2.Response:
        request.read()
        self.requests.append(request)
        return self.handler(request)


@pytest.fixture
def settings() -> Settings:
    """Return settings with sentinel credentials and specs from the local fixture."""
    return Settings(
        access_token=TOKEN, app_id=APP_ID, app_secret=APP_SECRET, spec_path=str(FIXTURE_SPECS)
    )


@pytest.fixture
def fake() -> FakeGraph:
    """Return a fresh fake Graph API."""
    return FakeGraph()


async def call(
    settings: Settings, fake: FakeGraph, tool: str, arguments: Mapping[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake API and the fixture specs."""
    server = build_server(settings, fake.transport, FIXTURE_HASH)
    async with Client(server) as client:
        return await client.call_tool(tool, dict(arguments))


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


def leaked(*values: object) -> list[str]:
    """Return every sentinel secret found in the JSON of `values`."""
    blob = json.dumps([_dumpable(value) for value in values])
    return [secret for secret in SECRETS if secret in blob]


def _dumpable(value: object) -> object:
    if isinstance(value, CallToolResult):
        return value.model_dump(mode="json")
    return value if isinstance(value, (dict, list, str)) else str(value)
