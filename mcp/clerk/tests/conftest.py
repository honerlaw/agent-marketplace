"""Shared fixtures: settings, the fixture spec, and a recording fake of the Clerk API."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import httpx2
import pytest

from clerk_mcp.config import Settings
from clerk_mcp.spec import Spec, SpecCatalog

FIXTURE_SPEC = Path(__file__).parent / "fixtures" / "spec.json"
SECRET = "sk_test_fixture_secret"  # noqa: S105 - a fixture value, not a secret

Handler = Callable[[httpx2.Request], httpx2.Response]


@dataclass
class FakeClerk:
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


def fixture_spec() -> Spec:
    """Return the small fixture spec."""
    spec: Spec = json.loads(FIXTURE_SPEC.read_text("utf-8"))
    return spec


@pytest.fixture
def settings() -> Settings:
    """Return settings with a fake secret key."""
    return Settings(secret_key=SECRET)


@pytest.fixture
def catalog() -> SpecCatalog:
    """Return a catalog over the fixture spec."""
    return SpecCatalog(fixture_spec())


@pytest.fixture
def fake() -> FakeClerk:
    """Return a fresh fake Clerk API."""
    return FakeClerk()
