"""Settings are read from the environment and refuse unsafe combinations."""

import pytest

from google_search_console_mcp.config import ConfigError, load_settings


def test_defaults_need_nothing() -> None:
    settings = load_settings({})
    assert settings.credentials_info is None
    assert not settings.read_only
    assert settings.transport == "stdio"
    assert (settings.host, settings.port) == ("127.0.0.1", 8000)
    assert settings.max_request_bytes == 4 * 1024 * 1024
    assert not settings.stateless


def test_every_variable_is_read() -> None:
    settings = load_settings(
        {
            "GSC_CREDENTIALS_JSON": '{"type": "authorized_user"}',
            "GSC_READ_ONLY": "true",
            "GSC_TIMEOUT_SECONDS": "5",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",  # noqa: S104 - a value under test, not a bind
            "MCP_PORT": "9000",
            "MCP_AUTH_TOKEN": "secret",
            "MCP_MAX_REQUEST_BYTES": "100",
            "MCP_STATELESS": "yes",
        }
    )
    assert settings.credentials_info == {"type": "authorized_user"}
    assert settings.read_only
    assert settings.timeout_seconds == 5.0
    assert (settings.host, settings.port, settings.auth_token) == ("0.0.0.0", 9000, "secret")  # noqa: S104
    assert settings.max_request_bytes == 100
    assert settings.stateless


@pytest.mark.parametrize("raw", ["not json", "[1, 2]", '"a string"'])
def test_credentials_json_must_be_an_object(raw: str) -> None:
    with pytest.raises(ConfigError, match="GSC_CREDENTIALS_JSON"):
        load_settings({"GSC_CREDENTIALS_JSON": raw})


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({"MCP_TRANSPORT": "carrier-pigeon"})


def test_http_without_token_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN"):
        load_settings({"MCP_TRANSPORT": "http"})


def test_http_without_token_needs_explicit_opt_out() -> None:
    settings = load_settings({"MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "TRUE"})
    assert settings.allow_unauthenticated
    assert settings.auth_token is None


def test_blank_optional_values_fall_back_to_defaults() -> None:
    settings = load_settings({"GSC_CREDENTIALS_JSON": "", "MCP_PORT": "", "MCP_TRANSPORT": ""})
    assert (settings.credentials_info, settings.port, settings.transport) == (None, 8000, "stdio")


def test_non_numeric_values_are_a_config_error() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({"MCP_PORT": "eighty"})
