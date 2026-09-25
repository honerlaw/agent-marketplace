"""Settings are read from the environment and refuse unsafe combinations."""

import pytest

from openai_mcp.config import DEFAULT_BASE_URL, ConfigError, load_settings


def test_defaults_need_only_an_api_key() -> None:
    settings = load_settings({"OPENAI_API_KEY": "sk-test"})
    assert settings.api_key == "sk-test"
    assert settings.base_url == DEFAULT_BASE_URL
    assert settings.transport == "stdio"
    assert settings.organization is None
    assert settings.max_request_bytes == 64 * 1024 * 1024
    assert not settings.stateless


def test_every_variable_is_read() -> None:
    settings = load_settings(
        {
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://example.test/v1",
            "OPENAI_ORG_ID": "org",
            "OPENAI_PROJECT_ID": "proj",
            "OPENAI_TIMEOUT_SECONDS": "5",
            "OPENAI_MCP_MAX_BINARY_BYTES": "10",
            "OPENAI_OPENAPI_PATH": "/spec.yaml",
            "OPENAI_OPENAPI_URL": "https://example.test/spec.yaml",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",  # noqa: S104 - a value under test, not a bind
            "MCP_PORT": "9000",
            "MCP_AUTH_TOKEN": "secret",
            "MCP_MAX_REQUEST_BYTES": "100",
            "MCP_STATELESS": "yes",
        }
    )
    assert settings.base_url == "https://example.test/v1"
    assert (settings.organization, settings.project) == ("org", "proj")
    assert (settings.timeout_seconds, settings.max_binary_bytes) == (5.0, 10)
    assert settings.openapi_path == "/spec.yaml"
    assert settings.openapi_url == "https://example.test/spec.yaml"
    assert (settings.host, settings.port, settings.auth_token) == ("0.0.0.0", 9000, "secret")  # noqa: S104
    assert settings.max_request_bytes == 100
    assert settings.stateless


def test_missing_api_key_is_refused() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        load_settings({})


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({"OPENAI_API_KEY": "sk-test", "MCP_TRANSPORT": "carrier-pigeon"})


def test_http_without_token_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN"):
        load_settings({"OPENAI_API_KEY": "sk-test", "MCP_TRANSPORT": "http"})


def test_http_without_token_needs_explicit_opt_out() -> None:
    settings = load_settings(
        {"OPENAI_API_KEY": "sk-test", "MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "TRUE"}
    )
    assert settings.allow_unauthenticated
    assert settings.auth_token is None


def test_blank_optional_values_fall_back_to_defaults() -> None:
    settings = load_settings(
        {"OPENAI_API_KEY": "sk-test", "OPENAI_BASE_URL": "", "MCP_PORT": "", "MCP_TRANSPORT": ""}
    )
    assert (settings.base_url, settings.port, settings.transport) == (
        DEFAULT_BASE_URL,
        8000,
        "stdio",
    )


def test_non_numeric_values_are_a_config_error() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({"OPENAI_API_KEY": "sk-test", "MCP_PORT": "eighty"})
