"""Shared fixtures: settings and a recording fake of Reddit's token endpoint and Ads API."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest

from reddit_ads_mcp.config import Credentials, Settings

FIXTURE_SPEC = Path(__file__).parent / "fixtures" / "openapi.json"
TOKEN_HOST = "www.reddit.com"  # noqa: S105 - a hostname, not a secret
API_HOST = "ads-api.reddit.com"
REFRESH_CREDENTIALS = Credentials(
    client_id="client-id",
    client_secret="client-secret",  # noqa: S106 - a fixture value, not a secret
    refresh_token="refresh-1",  # noqa: S106 - a fixture value, not a secret
)

Handler = Callable[[httpx2.Request], httpx2.Response]


def issue_token(_request: httpx2.Request) -> httpx2.Response:
    """Answer a refresh like Reddit does."""
    return httpx2.Response(200, json={"access_token": "access-1", "expires_in": 3600})


def answer_ok(_request: httpx2.Request) -> httpx2.Response:
    """Answer an API call with an empty data envelope."""
    return httpx2.Response(200, json={"data": {}})


@dataclass
class FakeReddit:
    """A mock transport that records requests and routes them by host."""

    token_handler: Handler = issue_token
    api_handler: Handler = answer_ok
    requests: list[httpx2.Request] = field(default_factory=list)

    @property
    def transport(self) -> httpx2.MockTransport:
        """The transport to inject into the code under test."""
        return httpx2.MockTransport(self._record)

    @property
    def token_requests(self) -> list[httpx2.Request]:
        """Requests the fake token endpoint received."""
        return [request for request in self.requests if request.url.host == TOKEN_HOST]

    @property
    def api_requests(self) -> list[httpx2.Request]:
        """Requests the fake Ads API received."""
        return [request for request in self.requests if request.url.host == API_HOST]

    @property
    def last(self) -> httpx2.Request:
        """The most recent request the fake Ads API received."""
        return self.api_requests[-1]

    def _record(self, request: httpx2.Request) -> httpx2.Response:
        request.read()
        self.requests.append(request)
        handler = self.token_handler if request.url.host == TOKEN_HOST else self.api_handler
        return handler(request)


@pytest.fixture
def settings() -> Settings:
    """Return refresh-mode settings pointing discovery at the local fixture spec."""
    return Settings(credentials=REFRESH_CREDENTIALS, openapi_path=str(FIXTURE_SPEC))


@pytest.fixture
def fake() -> FakeReddit:
    """Return a fresh fake Reddit."""
    return FakeReddit()
