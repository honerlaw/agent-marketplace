"""Credentials load lazily, from inline JSON or ADC, and refresh only when needed."""

import google.auth
import google.oauth2.credentials
import pytest
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from mcp.server.mcpserver.exceptions import ToolError

from google_search_console_mcp.config import Settings
from google_search_console_mcp.credentials import (
    READ_ONLY_SCOPE,
    READ_WRITE_SCOPE,
    TokenSource,
    default_loader,
    scopes_for,
)
from tests.conftest import FakeCredentials

pytestmark = pytest.mark.anyio

AUTHORIZED_USER: dict[str, object] = {
    "type": "authorized_user",
    "client_id": "client.apps.googleusercontent.com",
    "client_secret": "not-a-secret",
    "refresh_token": "refresh",
}


def test_scope_follows_read_only() -> None:
    assert scopes_for(Settings()) == [READ_WRITE_SCOPE]
    assert scopes_for(Settings(read_only=True)) == [READ_ONLY_SCOPE]


def test_inline_json_is_loaded_with_the_scope() -> None:
    loaded = default_loader(Settings(credentials_info=AUTHORIZED_USER, read_only=True))()
    assert isinstance(loaded, google.oauth2.credentials.Credentials)
    assert loaded.scopes == [READ_ONLY_SCOPE]
    assert loaded.refresh_token == "refresh"  # noqa: S105 - a fixture value, not a secret


def test_without_inline_json_adc_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    adc = FakeCredentials()
    asked: list[list[str]] = []

    def fake_default(scopes: list[str]) -> tuple[Credentials, str]:
        asked.append(scopes)
        return adc, "project"

    monkeypatch.setattr(google.auth, "default", fake_default)
    assert default_loader(Settings())() is adc
    assert asked == [[READ_WRITE_SCOPE]]


async def test_token_loads_once_and_refreshes_only_when_invalid() -> None:
    credentials = FakeCredentials()
    loads: list[bool] = []

    def loader() -> Credentials:
        loads.append(True)
        return credentials

    tokens = TokenSource(loader)
    assert await tokens.token() == "token-1"
    assert await tokens.token() == "token-1"
    credentials.token = None
    assert await tokens.token() == "token-2"
    assert (len(loads), credentials.refreshes) == (1, 2)


def test_service_account_json_uses_the_service_account_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built = FakeCredentials()
    seen: list[tuple[object, object]] = []

    def from_info(info: object, scopes: object) -> Credentials:
        seen.append((info, scopes))
        return built

    monkeypatch.setattr(service_account.Credentials, "from_service_account_info", from_info)
    info: dict[str, object] = {"type": "service_account", "client_email": "a@b"}
    assert default_loader(Settings(credentials_info=info))() is built
    assert seen == [(info, [READ_WRITE_SCOPE])]


async def test_other_credential_types_are_refused() -> None:
    info: dict[str, object] = {"type": "external_account", "credential_source": {"url": "x"}}
    loader = default_loader(Settings(credentials_info=info))
    with pytest.raises(ToolError, match="must be 'service_account' or 'authorized_user'"):
        await TokenSource(loader).token()


async def test_missing_credentials_become_a_tool_error() -> None:
    def loader() -> Credentials:
        message = "no ADC"
        # google-auth leaves its exception constructors unannotated.
        raise DefaultCredentialsError(message)  # type: ignore[no-untyped-call]

    with pytest.raises(ToolError, match="GSC_CREDENTIALS_JSON"):
        await TokenSource(loader).token()


async def test_malformed_inline_json_becomes_a_tool_error() -> None:
    loader = default_loader(Settings(credentials_info={"type": "authorized_user"}))
    with pytest.raises(ToolError, match="not valid authorized_user credentials"):
        await TokenSource(loader).token()
