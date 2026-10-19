"""Shared fixtures: settings, fake Google credentials and a recording fake of the Ads API."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest
from google.auth.credentials import Credentials
from mcp import Client
from mcp.types import CallToolResult, TextContent

from google_ads_mcp.config import Settings
from google_ads_mcp.server import build_server

FIXTURE_DISCOVERY = Path(__file__).parent / "fixtures" / "discovery.json"
API_HOST = "googleads.googleapis.com"

Handler = Callable[[httpx2.Request], httpx2.Response]


class FakeCredentials(Credentials):
    """Credentials whose refresh mints a numbered token without touching the network."""

    def __init__(self) -> None:
        """Start with no token, so the first use must refresh."""
        # untyped_calls_exclude does not reach a `super()` call into google-auth.
        super().__init__()  # type: ignore[no-untyped-call]
        self.refreshes = 0

    def refresh(self, request: object) -> None:
        """Mint the next token; `request` is the google-auth transport, unused here."""
        del request
        self.refreshes += 1
        self.token = f"token-{self.refreshes}"


def answer_ok(_request: httpx2.Request) -> httpx2.Response:
    """Answer an API call with an empty JSON object."""
    return httpx2.Response(200, json={}, headers={"request-id": "req-1"})


@dataclass
class FakeGoogleAds:
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
    """Return default settings with discovery pointed at the local fixture."""
    return Settings(discovery_path=str(FIXTURE_DISCOVERY))


@pytest.fixture
def fake() -> FakeGoogleAds:
    """Return a fresh fake Google Ads API."""
    return FakeGoogleAds()


async def call(
    settings: Settings,
    fake: FakeGoogleAds,
    tool: str,
    arguments: Mapping[str, object],
    credentials: Credentials | None = None,
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake API and fake credentials."""
    creds = credentials or FakeCredentials()
    server = build_server(settings, fake.transport, lambda: creds)
    async with Client(server) as client:
        return await client.call_tool(tool, dict(arguments))


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text
