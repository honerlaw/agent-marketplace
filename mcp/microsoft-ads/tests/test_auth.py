"""Access tokens from Microsoft's identity platform: refresh, rotation, caching, errors."""

from dataclasses import replace
from urllib.parse import parse_qs

import anyio
import httpx2
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp import auth
from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.server import build_server
from tests.conftest import (
    CLIENT_ID,
    CLIENT_SECRET,
    ISSUED_ACCESS,
    ISSUED_REFRESH,
    REFRESH_TOKEN,
    Clock,
    FakeMicrosoft,
    call,
    error_text,
)

pytestmark = pytest.mark.anyio

GET_USER = {"operation": "GetUser"}


def form(request: httpx2.Request) -> dict[str, str]:
    """Decode a token request's form body."""
    return {name: values[0] for name, values in parse_qs(request.content.decode()).items()}


@pytest.mark.parametrize(
    ("environment", "scope"),
    [
        ("production", "https://ads.microsoft.com/msads.manage offline_access"),
        ("sandbox", "https://si.ads.microsoft.com/msads.manage offline_access"),
    ],
)
async def test_the_refresh_goes_to_the_tenant_token_url_with_the_scope(
    settings: Settings, fake: FakeMicrosoft, environment: str, scope: str
) -> None:
    configured = replace(settings, tenant="contoso.onmicrosoft.com", environment=environment)
    await call(configured, fake, "microsoft_ads_request", GET_USER)
    request = fake.token_requests[0]
    assert str(request.url) == (
        "https://login.microsoftonline.com/contoso.onmicrosoft.com/oauth2/v2.0/token"
    )
    assert form(request) == {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": scope,
    }
    assert "Authorization" not in request.headers


async def test_a_token_is_reused_until_near_expiry(
    settings: Settings, fake: FakeMicrosoft, clock: Clock
) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        await client.call_tool("microsoft_ads_request", GET_USER)
        clock.now = 3539
        await client.call_tool("microsoft_ads_request", GET_USER)
        clock.now = 3540
        await client.call_tool("microsoft_ads_request", GET_USER)
    assert len(fake.token_requests) == 2


async def test_the_rotated_refresh_token_is_used_next(settings: Settings) -> None:
    fake = FakeMicrosoft()
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    first = await tokens.get()
    tokens.invalidate(first)
    await tokens.get()
    assert [form(request)["refresh_token"] for request in fake.token_requests] == [
        REFRESH_TOKEN,
        f"{ISSUED_REFRESH}1",
    ]
    assert f"{ISSUED_ACCESS}1" in tokens.secrets()
    assert f"{ISSUED_REFRESH}1" in tokens.secrets()


async def test_a_response_without_a_new_refresh_token_keeps_the_old_one(
    settings: Settings,
) -> None:
    fake = FakeMicrosoft(token_handler=lambda _r: httpx2.Response(200, json={"access_token": "a"}))
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    tokens.invalidate(await tokens.get())
    await tokens.get()
    assert [form(r)["refresh_token"] for r in fake.token_requests] == [REFRESH_TOKEN] * 2


async def test_invalidate_drops_only_the_rejected_token(settings: Settings) -> None:
    fake = FakeMicrosoft()
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    current = await tokens.get()
    tokens.invalidate("an older token")
    assert await tokens.get() == current
    assert len(fake.token_requests) == 1


async def test_concurrent_first_calls_share_one_refresh(settings: Settings) -> None:
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
    settings: Settings, clock: Clock
) -> None:
    fake = FakeMicrosoft(
        token_handler=lambda _r: httpx2.Response(200, json={"access_token": "a", "expires_in": 60})
    )
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    await tokens.get()
    clock.now = 29
    await tokens.get()
    clock.now = 30
    await tokens.get()
    assert len(fake.token_requests) == 2


async def test_a_missing_expiry_defaults_to_an_hour(settings: Settings, clock: Clock) -> None:
    fake = FakeMicrosoft(token_handler=lambda _r: httpx2.Response(200, json={"access_token": "a"}))
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    await tokens.get()
    clock.now = 3539
    await tokens.get()
    assert len(fake.token_requests) == 1


@pytest.mark.parametrize(
    ("response", "hint"),
    [
        (httpx2.Response(400, json={"error": "invalid_grant"}), "consent flow in the README"),
        (httpx2.Response(429, json={"error": "throttled"}), "retry later"),
        (httpx2.Response(503, text="down"), "retry later"),
        (httpx2.Response(401, json={"error": "invalid_client"}), "MICROSOFT_ADS_CLIENT_ID"),
        (httpx2.Response(200, json={"access_token": ""}), "MICROSOFT_ADS_CLIENT_ID"),
        (httpx2.Response(200, json=["x"]), "MICROSOFT_ADS_CLIENT_ID"),
    ],
)
async def test_a_failed_refresh_explains_itself(
    settings: Settings, response: httpx2.Response, hint: str
) -> None:
    fake = FakeMicrosoft(token_handler=lambda _r: response)
    tokens = auth.AccessTokens(settings, httpx2.AsyncClient(transport=fake.transport))
    with pytest.raises(ToolError, match="refused to refresh") as caught:
        await tokens.get()
    assert hint in str(caught.value)


async def test_an_unreachable_token_endpoint_is_a_clear_error(
    settings: Settings, fake: FakeMicrosoft
) -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        message = f"timed out sending {request.content!r}"
        raise httpx2.ConnectTimeout(message, request=request)

    fake.token_handler = refuse
    result = await call(settings, fake, "microsoft_ads_request", GET_USER)
    message = error_text(result)
    assert "could not reach the Microsoft token endpoint: ConnectTimeout" in message
    assert REFRESH_TOKEN not in message
