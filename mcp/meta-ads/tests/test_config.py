"""Settings are read from the environment and validated."""

import pytest

from meta_ads_mcp.config import ConfigError, Settings, load_settings


def test_defaults() -> None:
    settings = load_settings({})
    assert settings == Settings()
    assert settings.base_url == "https://graph.facebook.com/v26.0"
    assert settings.secrets == ()


def test_the_version_moves_the_base_url() -> None:
    assert load_settings({"META_ADS_API_VERSION": "v27.0"}).base_url.endswith("/v27.0")


@pytest.mark.parametrize("version", ["26.0", "v26", "v26.0/../x", "latest", "v26.0.1"])
def test_a_malformed_version_is_refused(version: str) -> None:
    with pytest.raises(ConfigError, match="META_ADS_API_VERSION"):
        load_settings({"META_ADS_API_VERSION": version})


def test_every_variable_is_read() -> None:
    env = {
        "META_ADS_ACCESS_TOKEN": "tok",
        "META_APP_ID": "1",
        "META_APP_SECRET": "sec",
        "META_ADS_SPEC_PATH": "/app/specs",
        "META_ADS_TIMEOUT_SECONDS": "5",
        "META_ADS_MAX_RESPONSE_BYTES": "1000",
        "MCP_TRANSPORT": "http",
        "MCP_HOST": "0.0.0.0",  # noqa: S104 - a config value under test, not a bind
        "MCP_PORT": "9000",
        "MCP_AUTH_TOKEN": "t",
        "MCP_MAX_REQUEST_BYTES": "10",
        "MCP_STATELESS": "true",
    }
    settings = load_settings(env)
    assert (settings.access_token, settings.app_id, settings.app_secret) == ("tok", "1", "sec")
    assert settings.secrets == ("tok", "sec")
    assert (settings.spec_path, settings.timeout_seconds) == ("/app/specs", 5)
    assert (settings.max_response_bytes, settings.max_request_bytes) == (1000, 10)
    assert (settings.transport, settings.host, settings.port) == ("http", "0.0.0.0", 9000)  # noqa: S104
    assert (settings.auth_token, settings.stateless) == ("t", True)


@pytest.mark.parametrize("env", [{"META_APP_ID": "1"}, {"META_APP_SECRET": "s"}])
def test_app_id_and_secret_come_together(env: dict[str, str]) -> None:
    with pytest.raises(ConfigError, match="together"):
        load_settings(env)


def test_a_non_number_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({"MCP_PORT": "eighty"})


@pytest.mark.parametrize("value", ["inf", "1e400", "nan", "0", "-5"])
def test_a_number_must_be_positive_and_finite(value: str) -> None:
    with pytest.raises(ConfigError, match="META_ADS_MAX_RESPONSE_BYTES must be a positive"):
        load_settings({"META_ADS_MAX_RESPONSE_BYTES": value})


def test_an_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({"MCP_TRANSPORT": "sse"})


def test_http_needs_a_token_unless_explicitly_open() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN must be set"):
        load_settings({"MCP_TRANSPORT": "http"})
    opened = load_settings({"MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "yes"})
    assert opened.allow_unauthenticated
