"""Shared fixtures: settings with sentinel credentials and a recording fake of Microsoft."""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from microsoft_ads_mcp import auth
from microsoft_ads_mcp.config import Credentials, Settings
from microsoft_ads_mcp.server import build_server

TOKEN_HOST = "login.microsoftonline.com"  # noqa: S105 - a host name, not a secret
# Sentinels: if any of these strings shows up in a tool result, error or log, it leaked.
CLIENT_ID = "client-id-1"
CLIENT_SECRET = "clientsecretSENTINEL"  # noqa: S105 - a fixture value, not a secret
REFRESH_TOKEN = "refreshtokenSENTINEL"  # noqa: S105 - a fixture value, not a secret
DEVELOPER_TOKEN = "developertokenSENTINEL"  # noqa: S105 - a fixture value, not a secret
ISSUED_ACCESS = "accesstokenSENTINEL"
ISSUED_REFRESH = "rotatedrefreshSENTINEL"
SECRETS = (CLIENT_SECRET, REFRESH_TOKEN, DEVELOPER_TOKEN, ISSUED_ACCESS, ISSUED_REFRESH)

Handler = Callable[[httpx2.Request], httpx2.Response]


def issued(number: int) -> httpx2.Response:
    """Answer refresh `number` like Microsoft: a new access token and a rotated refresh token."""
    return httpx2.Response(
        200,
        json={
            "access_token": f"{ISSUED_ACCESS}{number}",
            "refresh_token": f"{ISSUED_REFRESH}{number}",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )


def answer_ok(_request: httpx2.Request) -> httpx2.Response:
    """Answer an API call with an empty success body and a tracking id."""
    return httpx2.Response(
        200, json={"TrackingId": "track-1"}, headers={"x-ms-trackingid": "track-1"}
    )


@dataclass
class FakeMicrosoft:
    """A mock transport for the token endpoint and every API host, recording requests."""

    api_handler: Handler = answer_ok
    token_handler: Handler | None = None
    token_requests: list[httpx2.Request] = field(default_factory=list)
    api_requests: list[httpx2.Request] = field(default_factory=list)

    @property
    def transport(self) -> httpx2.MockTransport:
        """The transport to inject into the code under test."""
        return httpx2.MockTransport(self._record)

    @property
    def last(self) -> httpx2.Request:
        """The most recent API (not token) request."""
        return self.api_requests[-1]

    def _record(self, request: httpx2.Request) -> httpx2.Response:
        request.read()
        if request.url.host == TOKEN_HOST:
            self.token_requests.append(request)
            if self.token_handler is None:
                return issued(len(self.token_requests))
            return self.token_handler(request)
        self.api_requests.append(request)
        return self.api_handler(request)


@dataclass
class Clock:
    """A settable stand-in for `time.monotonic`."""

    now: float = 0.0


@pytest.fixture(autouse=True)
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    """Freeze the token cache's clock at zero; tests move it forward by hand."""
    frozen = Clock()
    monkeypatch.setattr(auth, "now", lambda: frozen.now)
    return frozen


@pytest.fixture
def settings() -> Settings:
    """Return settings with sentinel credentials and default customer and account ids."""
    credentials = Credentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        refresh_token=REFRESH_TOKEN,
        developer_token=DEVELOPER_TOKEN,
    )
    return Settings(credentials=credentials, customer_id="111", account_id="222")


@pytest.fixture
def fake() -> FakeMicrosoft:
    """Return a fresh fake Microsoft."""
    return FakeMicrosoft()


async def call(
    settings: Settings, fake: FakeMicrosoft, tool: str, arguments: Mapping[str, object]
) -> CallToolResult:
    """Call one tool on a fresh server wired to the fake."""
    async with Client(build_server(settings, fake.transport)) as client:
        return await client.call_tool(tool, dict(arguments))


def structured(result: CallToolResult) -> dict[str, Any]:
    """Return a successful tool call's structured result."""
    assert not result.is_error, result.content
    assert result.structured_content is not None
    return dict(result.structured_content)


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
