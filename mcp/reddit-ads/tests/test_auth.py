"""Access tokens: fetched on first use, cached, refreshed on expiry or 401, never leaked."""

import base64
from dataclasses import replace
from urllib.parse import parse_qs

import anyio
import httpx2
import pytest
from mcp import Client
from mcp.types import CallToolResult

from reddit_ads_mcp import auth
from reddit_ads_mcp.config import Credentials, Settings
from reddit_ads_mcp.server import build_server
from tests.conftest import FakeReddit

pytestmark = pytest.mark.anyio

ME = {"method": "GET", "path": "/me"}


class Clock:
    """A controllable stand-in for time.monotonic."""

    def __init__(self) -> None:
        """Start at zero."""
        self.now = 0.0

    def __call__(self) -> float:
        """Return the current fake time."""
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    """Replace the token manager's clock."""
    fake_clock = Clock()
    monkeypatch.setattr(auth, "now", fake_clock)
    return fake_clock


async def call_many(
    settings: Settings, fake: FakeReddit, count: int, clock: Clock | None = None
) -> list[CallToolResult]:
    """Call /me `count` times on one server, advancing the clock an hour between calls."""
    results = []
    async with Client(build_server(settings, fake.transport)) as client:
        for _ in range(count):
            results.append(await client.call_tool("reddit_ads_request", ME))
            if clock is not None:
                clock.now += 3600
    return results


def form(request: httpx2.Request) -> dict[str, list[str]]:
    """Decode a form-encoded request body."""
    return parse_qs(request.content.decode())


async def test_first_call_fetches_a_token_with_client_credentials(
    settings: Settings, fake: FakeReddit
) -> None:
    await call_many(settings, fake, 1)
    [token_request] = fake.token_requests
    assert str(token_request.url) == "https://www.reddit.com/api/v1/access_token"
    basic = base64.b64encode(b"client-id:client-secret").decode()
    assert token_request.headers["authorization"] == f"Basic {basic}"
    assert form(token_request) == {"grant_type": ["refresh_token"], "refresh_token": ["refresh-1"]}
    assert token_request.headers["user-agent"] == settings.user_agent
    assert fake.last.headers["authorization"] == "Bearer access-1"


async def test_token_is_reused_until_near_expiry(
    settings: Settings, fake: FakeReddit, clock: Clock
) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool("reddit_ads_request", ME)
        clock.now = 3600 - auth.EXPIRY_MARGIN_SECONDS - 1
        await client.call_tool("reddit_ads_request", ME)
        clock.now = 3600 - auth.EXPIRY_MARGIN_SECONDS
        await client.call_tool("reddit_ads_request", ME)
    assert len(fake.token_requests) == 2
    assert len(fake.api_requests) == 3


async def test_missing_expiry_defaults_to_an_hour(
    settings: Settings, fake: FakeReddit, clock: Clock
) -> None:
    fake.token_handler = lambda _request: httpx2.Response(200, json={"access_token": "a"})
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool("reddit_ads_request", ME)
        clock.now = auth.DEFAULT_EXPIRES_IN - auth.EXPIRY_MARGIN_SECONDS - 1
        await client.call_tool("reddit_ads_request", ME)
    assert len(fake.token_requests) == 1


async def test_rotated_refresh_token_is_used_next_time(
    settings: Settings, fake: FakeReddit, clock: Clock
) -> None:
    issued = iter(["refresh-2", ""])
    fake.token_handler = lambda _request: httpx2.Response(
        200, json={"access_token": "a", "expires_in": 60, "refresh_token": next(issued)}
    )
    await call_many(settings, fake, 3, clock)
    sent = [form(request)["refresh_token"] for request in fake.token_requests]
    assert sent == [["refresh-1"], ["refresh-2"], ["refresh-2"]]


async def test_a_401_refreshes_and_retries_exactly_once(
    settings: Settings, fake: FakeReddit
) -> None:
    tokens = iter(["stale", "fresh"])
    fake.token_handler = lambda _request: httpx2.Response(
        200, json={"access_token": next(tokens), "expires_in": 3600}
    )
    fake.api_handler = lambda request: httpx2.Response(
        401 if request.headers["authorization"] == "Bearer stale" else 200, json={}
    )
    [result] = await call_many(settings, fake, 1)
    assert result.structured_content is not None
    assert result.structured_content["status"] == 200
    assert [r.headers["authorization"] for r in fake.api_requests] == [
        "Bearer stale",
        "Bearer fresh",
    ]


async def test_a_second_401_is_returned_not_looped(settings: Settings, fake: FakeReddit) -> None:
    fake.api_handler = lambda _request: httpx2.Response(401, json={"error": "unauthorized"})
    [result] = await call_many(settings, fake, 1)
    assert result.structured_content is not None
    assert result.structured_content["status"] == 401
    assert len(fake.api_requests) == 2
    assert len(fake.token_requests) == 2


async def test_invalidate_drops_only_the_rejected_token(
    settings: Settings, fake: FakeReddit
) -> None:
    issued = iter(["access-1", "access-2"])
    fake.token_handler = lambda _request: httpx2.Response(
        200, json={"access_token": next(issued), "expires_in": 3600}
    )
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    assert await tokens.get() == "access-1"
    tokens.invalidate("an-older-token")
    assert await tokens.get() == "access-1"
    tokens.invalidate("access-1")
    assert await tokens.get() == "access-2"
    assert len(fake.token_requests) == 2


async def test_concurrent_calls_share_one_refresh(settings: Settings) -> None:
    refreshes: list[httpx2.Request] = []

    async def slow_token_endpoint(request: httpx2.Request) -> httpx2.Response:
        refreshes.append(request)
        await anyio.sleep(0.01)  # let every caller reach the lock while this one is in flight
        return httpx2.Response(200, json={"access_token": "access-1", "expires_in": 3600})

    transport = httpx2.MockTransport(slow_token_endpoint)
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=transport))
    results: list[str] = []

    async def fetch() -> None:
        results.append(await tokens.get())

    async with anyio.create_task_group() as group:
        for _ in range(10):
            group.start_soon(fetch)
    assert results == ["access-1"] * 10
    assert len(refreshes) == 1


async def test_a_short_lived_token_is_still_reused_for_half_its_life(
    settings: Settings, fake: FakeReddit, clock: Clock
) -> None:
    fake.token_handler = lambda _request: httpx2.Response(
        200, json={"access_token": "a", "expires_in": 60}
    )
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool("reddit_ads_request", ME)
        clock.now = 29
        await client.call_tool("reddit_ads_request", ME)
        clock.now = 30
        await client.call_tool("reddit_ads_request", ME)
    assert len(fake.token_requests) == 2


def refuse_connection(request: httpx2.Request) -> httpx2.Response:
    """Fail the way an unreachable host does."""
    message = "timed out"
    raise httpx2.ConnectTimeout(message, request=request)


async def test_an_unreachable_token_endpoint_is_a_clear_error(
    settings: Settings, fake: FakeReddit
) -> None:
    fake.token_handler = refuse_connection
    [result] = await call_many(settings, fake, 1)
    assert result.is_error
    assert "could not reach the Reddit token endpoint: ConnectTimeout" in str(result.content[0])
    assert fake.api_requests == []


@pytest.mark.parametrize(
    ("status", "hint"),
    [(400, "check REDDIT_CLIENT_ID"), (429, "retry later"), (503, "retry later")],
)
async def test_a_failed_refresh_hint_depends_on_the_status(
    settings: Settings, fake: FakeReddit, status: int, hint: str
) -> None:
    fake.token_handler = lambda _request: httpx2.Response(status, json={"error": "x"})
    [result] = await call_many(settings, fake, 1)
    assert hint in str(result.content[0])


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(401, json={"error": "invalid_grant"}),
        httpx2.Response(200, json={"error": "invalid_grant"}),
        httpx2.Response(502, text="<html>bad gateway</html>"),
        httpx2.Response(200, json=["not", "an", "object"]),
        httpx2.Response(200, json={"access_token": "", "expires_in": 3600}),
    ],
)
async def test_a_failed_refresh_is_a_clear_error_without_secrets(
    settings: Settings, fake: FakeReddit, response: httpx2.Response
) -> None:
    fake.token_handler = lambda _request: response
    [result] = await call_many(settings, fake, 1)
    assert result.is_error
    text = str(result.content[0])
    assert "Reddit refused to refresh the access token" in text
    assert "client-secret" not in text
    assert "refresh-1" not in text
    assert fake.api_requests == []


async def test_secrets_only_go_to_the_token_url(settings: Settings, fake: FakeReddit) -> None:
    await call_many(settings, fake, 1)
    for request in fake.api_requests:
        sent = f"{request.headers}{request.url}{request.content!r}"
        assert "client-secret" not in sent
        assert "refresh-1" not in sent
        assert "Basic" not in request.headers["authorization"]
    for request in fake.token_requests:
        assert "access-1" not in f"{request.headers}{request.content!r}"


async def test_static_token_is_sent_without_refreshing(
    settings: Settings, fake: FakeReddit
) -> None:
    static = replace(settings, credentials=Credentials(access_token="static-token"))  # noqa: S106 - a fixture value, not a secret
    fake.api_handler = lambda _request: httpx2.Response(401, json={})
    [result] = await call_many(static, fake, 1)
    assert result.structured_content is not None
    assert result.structured_content["status"] == 401
    assert fake.token_requests == []
    assert [r.headers["authorization"] for r in fake.api_requests] == ["Bearer static-token"]
