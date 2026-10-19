"""Settings are read from the environment and validated."""

import pytest

from google_ads_mcp.config import ConfigError, Settings, load_settings, normalize_customer_id


def test_defaults() -> None:
    settings = load_settings({})
    assert settings == Settings()
    assert settings.base_url == "https://googleads.googleapis.com/v26"
    assert settings.discovery_url == "https://googleads.googleapis.com/$discovery/rest?version=v26"


def test_the_version_moves_both_urls() -> None:
    settings = load_settings({"GOOGLE_ADS_API_VERSION": "v27"})
    assert settings.base_url == "https://googleads.googleapis.com/v27"
    assert settings.discovery_url.endswith("?version=v27")


@pytest.mark.parametrize("version", ["26", "v26/../x", "latest", "v"])
def test_a_malformed_version_is_refused(version: str) -> None:
    with pytest.raises(ConfigError, match="GOOGLE_ADS_API_VERSION"):
        load_settings({"GOOGLE_ADS_API_VERSION": version})


def test_every_variable_is_read() -> None:
    env = {
        "GOOGLE_ADS_CREDENTIALS_JSON": '{"type": "authorized_user"}',
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": "123-456-7890",
        "GOOGLE_ADS_DISCOVERY_PATH": "discovery.json",
        "GOOGLE_ADS_TIMEOUT_SECONDS": "5",
        "GOOGLE_ADS_MAX_RESPONSE_BYTES": "1000",
        "MCP_TRANSPORT": "http",
        "MCP_HOST": "0.0.0.0",  # noqa: S104 - a config value under test, not a bind
        "MCP_PORT": "9000",
        "MCP_AUTH_TOKEN": "t",
        "MCP_MAX_REQUEST_BYTES": "10",
        "MCP_STATELESS": "true",
    }
    settings = load_settings(env)
    assert settings.credentials_info == {"type": "authorized_user"}
    assert settings.login_customer_id == "1234567890"
    assert (settings.discovery_path, settings.timeout_seconds) == ("discovery.json", 5)
    assert (settings.max_response_bytes, settings.max_request_bytes) == (1000, 10)
    assert (settings.transport, settings.host, settings.port) == ("http", "0.0.0.0", 9000)  # noqa: S104
    assert (settings.auth_token, settings.stateless) == ("t", True)


def test_a_malformed_login_customer_id_is_refused() -> None:
    with pytest.raises(ConfigError, match="GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
        load_settings({"GOOGLE_ADS_LOGIN_CUSTOMER_ID": "manager"})


@pytest.mark.parametrize(
    ("raw", "expected"), [("123-456-7890", "1234567890"), ("42", "42"), ("4 2", None)]
)
def test_customer_ids_are_normalized(raw: str, expected: str | None) -> None:
    assert normalize_customer_id(raw) == expected


@pytest.mark.parametrize(("raw", "match"), [("{", "JSON credentials"), ("[1]", "JSON object")])
def test_bad_credentials_json_is_refused(raw: str, match: str) -> None:
    with pytest.raises(ConfigError, match=match):
        load_settings({"GOOGLE_ADS_CREDENTIALS_JSON": raw})


def test_a_non_number_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({"MCP_PORT": "eighty"})


@pytest.mark.parametrize("value", ["inf", "1e400", "nan", "0", "-5"])
def test_a_number_must_be_positive_and_finite(value: str) -> None:
    with pytest.raises(ConfigError, match="GOOGLE_ADS_MAX_RESPONSE_BYTES must be a positive"):
        load_settings({"GOOGLE_ADS_MAX_RESPONSE_BYTES": value})


def test_an_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({"MCP_TRANSPORT": "sse"})


def test_http_needs_a_token_unless_explicitly_open() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN must be set"):
        load_settings({"MCP_TRANSPORT": "http"})
    opened = load_settings({"MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "yes"})
    assert opened.allow_unauthenticated
