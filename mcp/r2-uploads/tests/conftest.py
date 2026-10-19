"""Shared fixtures: settings, a fixed clock and a recording fake of R2's S3 API."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from r2_uploads_mcp.config import Settings
from r2_uploads_mcp.server import build_server

Handler = Callable[[httpx2.Request], httpx2.Response]

ACCOUNT_ID = "0123456789abcdef0123456789abcdef"
ENDPOINT = f"{ACCOUNT_ID}.r2.cloudflarestorage.com"
NOW = datetime(2026, 10, 19, 12, 0, 0, tzinfo=UTC)
EMPTY_LISTING = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>ad-uploads</Name><IsTruncated>false</IsTruncated>
</ListBucketResult>"""


@dataclass
class FakeR2:
    """A mock transport that records requests and answers with `handler`."""

    handler: Handler = field(default=lambda _request: httpx2.Response(200, content=EMPTY_LISTING))
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
        self.requests.append(request)
        return self.handler(request)


@pytest.fixture
def settings() -> Settings:
    """Return settings for a dummy account and bucket (stdio)."""
    return Settings(
        account_id=ACCOUNT_ID,
        access_key_id="test-key-id",
        secret_access_key="test-secret",  # noqa: S106 - a fixture value, not a secret
        bucket="ad-uploads",
    )


@pytest.fixture
def fake() -> FakeR2:
    """Return a fresh fake R2."""
    return FakeR2()


async def call(
    settings: Settings, fake: FakeR2, tool: str, arguments: dict[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake R2 and the fixed clock."""
    server = build_server(settings, fake.transport, lambda: NOW)
    async with Client(server) as client:
        return await client.call_tool(tool, arguments)


def error_text(result: CallToolResult) -> str:
    """Return the error message of a failed tool call."""
    assert result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text
