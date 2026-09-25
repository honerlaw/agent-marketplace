"""Shared fixtures: settings, fake Google credentials and a recording fake of the API."""

from collections.abc import Callable
from dataclasses import dataclass, field

import httpx2
import pytest
from google.auth.credentials import Credentials
from mcp import Client
from mcp.types import CallToolResult, TextContent

from google_search_console_mcp.config import Settings
from google_search_console_mcp.server import build_server

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


@dataclass
class FakeSearchConsole:
    """A mock transport that records requests and answers with `handler`."""

    handler: Handler = field(default=lambda _request: httpx2.Response(200, json={"ok": True}))
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
    """Return default settings (read-write, stdio)."""
    return Settings()


@pytest.fixture
def credentials() -> FakeCredentials:
    """Return fresh fake credentials."""
    return FakeCredentials()


@pytest.fixture
def fake() -> FakeSearchConsole:
    """Return a fresh fake Search Console API."""
    return FakeSearchConsole()


async def call(
    settings: Settings,
    fake: FakeSearchConsole,
    tool: str,
    arguments: dict[str, object],
    credentials: Credentials | None = None,
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake API and fake credentials."""
    creds = credentials or FakeCredentials()
    server = build_server(settings, fake.transport, lambda: creds)
    async with Client(server) as client:
        return await client.call_tool(tool, arguments)


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text
