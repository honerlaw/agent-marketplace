"""Shared fixtures: settings and a recording fake of the OpenAI Ads API."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest

from openai_ads_mcp.config import Settings

FIXTURE_SPEC = Path(__file__).parent / "fixtures" / "openapi.json"

Handler = Callable[[httpx2.Request], httpx2.Response]


@dataclass
class FakeAdsApi:
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
    """Return settings pointing discovery at the local fixture spec."""
    return Settings(api_key="sk-test", openapi_path=str(FIXTURE_SPEC))


@pytest.fixture
def fake() -> FakeAdsApi:
    """Return a fresh fake Ads API."""
    return FakeAdsApi()
