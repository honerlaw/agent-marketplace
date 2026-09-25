"""Settings are read from the environment and refuse unsafe or ambiguous combinations."""

import pytest

from reddit_ads_mcp.config import (
    DEFAULT_BASE_URL,
    DEFAULT_TOKEN_URL,
    DEFAULT_USER_AGENT,
    ConfigError,
    Credentials,
    load_settings,
)

REFRESH_ENV = {
    "REDDIT_CLIENT_ID": "id",
    "REDDIT_CLIENT_SECRET": "secret",
    "REDDIT_REFRESH_TOKEN": "refresh",
}


def test_refresh_mode_defaults() -> None:
    settings = load_settings(REFRESH_ENV)
    assert settings.credentials == Credentials("id", "secret", "refresh", None)
    assert (settings.base_url, settings.token_url) == (DEFAULT_BASE_URL, DEFAULT_TOKEN_URL)
    assert settings.user_agent == DEFAULT_USER_AGENT
    assert "(by /u/" in settings.user_agent
    assert settings.transport == "stdio"
    assert settings.max_request_bytes == 4 * 1024 * 1024
    assert not settings.stateless


def test_static_mode_needs_only_an_access_token() -> None:
    settings = load_settings({"REDDIT_ACCESS_TOKEN": "static"})
    assert settings.credentials == Credentials(access_token="static")  # noqa: S106 - a fixture value, not a secret


def test_every_variable_is_read() -> None:
    settings = load_settings(
        {
            **REFRESH_ENV,
            "REDDIT_USER_AGENT": "web:app:1.0 (by /u/someone)",
            "REDDIT_ADS_BASE_URL": "https://ads.test/api/v3",
            "REDDIT_TOKEN_URL": "https://auth.test/token",
            "REDDIT_TIMEOUT_SECONDS": "5",
            "REDDIT_ADS_OPENAPI_PATH": "/spec.json",
            "REDDIT_ADS_OPENAPI_URL": "https://ads.test/spec.json",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",  # noqa: S104 - a value under test, not a bind
            "MCP_PORT": "9000",
            "MCP_AUTH_TOKEN": "secret",
            "MCP_MAX_REQUEST_BYTES": "100",
            "MCP_STATELESS": "yes",
        }
    )
    assert settings.user_agent == "web:app:1.0 (by /u/someone)"
    assert (settings.base_url, settings.token_url) == (
        "https://ads.test/api/v3",
        "https://auth.test/token",
    )
    assert settings.timeout_seconds == 5.0
    assert settings.openapi_path == "/spec.json"
    assert settings.openapi_url == "https://ads.test/spec.json"
    assert (settings.host, settings.port, settings.auth_token) == ("0.0.0.0", 9000, "secret")  # noqa: S104
    assert settings.max_request_bytes == 100
    assert settings.stateless


def test_no_credentials_are_refused() -> None:
    with pytest.raises(ConfigError, match="REDDIT_REFRESH_TOKEN"):
        load_settings({})


@pytest.mark.parametrize("missing", sorted(REFRESH_ENV))
def test_incomplete_refresh_credentials_are_refused(missing: str) -> None:
    env = {name: value for name, value in REFRESH_ENV.items() if name != missing}
    with pytest.raises(ConfigError, match="set all of"):
        load_settings(env)


def test_both_modes_at_once_are_refused() -> None:
    with pytest.raises(ConfigError, match="not both"):
        load_settings({**REFRESH_ENV, "REDDIT_ACCESS_TOKEN": "static"})


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({**REFRESH_ENV, "MCP_TRANSPORT": "carrier-pigeon"})


def test_http_without_token_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN"):
        load_settings({**REFRESH_ENV, "MCP_TRANSPORT": "http"})


def test_http_without_token_needs_explicit_opt_out() -> None:
    settings = load_settings(
        {**REFRESH_ENV, "MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "TRUE"}
    )
    assert settings.allow_unauthenticated
    assert settings.auth_token is None


def test_blank_optional_values_fall_back_to_defaults() -> None:
    settings = load_settings(
        {**REFRESH_ENV, "REDDIT_ADS_BASE_URL": "", "MCP_PORT": "", "REDDIT_ACCESS_TOKEN": ""}
    )
    assert (settings.base_url, settings.port) == (DEFAULT_BASE_URL, 8000)
    assert settings.credentials.access_token is None


def test_non_numeric_values_are_a_config_error() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({**REFRESH_ENV, "MCP_PORT": "eighty"})
