"""Settings are read from the environment and refuse unsafe combinations."""

import pytest

from clerk_mcp.config import ConfigError, load_settings

KEY = "sk_test_abc"


def test_defaults_need_only_a_secret_key() -> None:
    settings = load_settings({"CLERK_SECRET_KEY": KEY})
    assert settings.secret_key == KEY
    assert not settings.read_only
    assert settings.transport == "stdio"
    assert settings.timeout_seconds == 60
    assert settings.max_request_bytes == 4 * 1024 * 1024
    assert not settings.stateless


def test_every_variable_is_read() -> None:
    settings = load_settings(
        {
            "CLERK_SECRET_KEY": KEY,
            "CLERK_READ_ONLY": "true",
            "CLERK_TIMEOUT_SECONDS": "5",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",  # noqa: S104 - a value under test, not a bind
            "MCP_PORT": "9000",
            "MCP_AUTH_TOKEN": "secret",
            "MCP_MAX_REQUEST_BYTES": "100",
            "MCP_STATELESS": "yes",
        }
    )
    assert settings.read_only
    assert settings.timeout_seconds == 5
    assert (settings.transport, settings.host, settings.port) == ("http", "0.0.0.0", 9000)  # noqa: S104
    assert settings.auth_token == "secret"  # noqa: S105 - a value under test
    assert settings.max_request_bytes == 100
    assert settings.stateless


@pytest.mark.parametrize("value", ["", "pk_live_abc", "abc"])
def test_secret_key_must_look_like_one_and_is_never_echoed(value: str) -> None:
    with pytest.raises(ConfigError, match="CLERK_SECRET_KEY") as raised:
        load_settings({"CLERK_SECRET_KEY": value})
    assert not value or value not in str(raised.value)


def test_missing_secret_key_is_refused() -> None:
    with pytest.raises(ConfigError, match="CLERK_SECRET_KEY"):
        load_settings({})


def test_numbers_are_validated() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({"CLERK_SECRET_KEY": KEY, "MCP_PORT": "eighty"})


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({"CLERK_SECRET_KEY": KEY, "MCP_TRANSPORT": "sse"})


def test_http_mode_requires_a_token() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN"):
        load_settings({"CLERK_SECRET_KEY": KEY, "MCP_TRANSPORT": "http"})


def test_http_mode_may_run_unauthenticated_when_asked() -> None:
    env = {"CLERK_SECRET_KEY": KEY, "MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "1"}
    assert load_settings(env).allow_unauthenticated
