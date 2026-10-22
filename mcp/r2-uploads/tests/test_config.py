"""Settings are read from the environment and refuse unsafe combinations."""

import pytest

from r2_uploads_mcp.config import ConfigError, load_settings
from tests.conftest import ACCOUNT_ID, ENDPOINT

REQUIRED = {
    "R2_ACCOUNT_ID": ACCOUNT_ID,
    "R2_ACCESS_KEY_ID": "key-id",
    "R2_SECRET_ACCESS_KEY": "secret",
    "R2_BUCKET": "ad-uploads",
}


def test_defaults_need_only_the_bucket() -> None:
    settings = load_settings(REQUIRED)
    assert (settings.account_id, settings.bucket) == (ACCOUNT_ID, "ad-uploads")
    assert settings.endpoint_host == ENDPOINT
    assert (settings.upload_expires_seconds, settings.download_expires_seconds) == (900, 86400)
    assert settings.transport == "stdio"
    assert (settings.host, settings.port) == ("127.0.0.1", 8000)
    assert settings.max_request_bytes == 4 * 1024 * 1024
    assert not settings.stateless


def test_every_variable_is_read() -> None:
    settings = load_settings(
        {
            **REQUIRED,
            "R2_UPLOAD_EXPIRES_SECONDS": "60",
            "R2_DOWNLOAD_EXPIRES_SECONDS": "604800",
            "R2_TIMEOUT_SECONDS": "5",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",  # noqa: S104 - a value under test, not a bind
            "MCP_PORT": "9000",
            "MCP_AUTH_TOKEN": "token",
            "MCP_MAX_REQUEST_BYTES": "100",
            "MCP_STATELESS": "yes",
        }
    )
    assert (settings.upload_expires_seconds, settings.download_expires_seconds) == (60, 604800)
    assert settings.timeout_seconds == 5.0
    assert (settings.host, settings.port, settings.auth_token) == ("0.0.0.0", 9000, "token")  # noqa: S104
    assert settings.max_request_bytes == 100
    assert settings.stateless


def test_missing_required_variables_are_all_named() -> None:
    with pytest.raises(ConfigError, match="R2_ACCESS_KEY_ID, R2_BUCKET"):
        load_settings({"R2_ACCOUNT_ID": ACCOUNT_ID, "R2_SECRET_ACCESS_KEY": "s"})


@pytest.mark.parametrize("account_id", ["evil.example/x", ACCOUNT_ID.upper(), ACCOUNT_ID[:-1]])
def test_account_id_must_be_an_id(account_id: str) -> None:
    with pytest.raises(ConfigError, match="R2_ACCOUNT_ID"):
        load_settings({**REQUIRED, "R2_ACCOUNT_ID": account_id})


@pytest.mark.parametrize("bucket", ["Ad-Uploads", "a", "../x", "-uploads"])
def test_bucket_must_be_a_bucket_name(bucket: str) -> None:
    with pytest.raises(ConfigError, match="R2_BUCKET"):
        load_settings({**REQUIRED, "R2_BUCKET": bucket})


@pytest.mark.parametrize("seconds", ["0", "604801"])
def test_expiry_must_be_within_seven_days(seconds: str) -> None:
    with pytest.raises(ConfigError, match="R2_DOWNLOAD_EXPIRES_SECONDS must be between"):
        load_settings({**REQUIRED, "R2_DOWNLOAD_EXPIRES_SECONDS": seconds})


def test_unknown_transport_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_TRANSPORT"):
        load_settings({**REQUIRED, "MCP_TRANSPORT": "carrier-pigeon"})


def test_http_without_token_is_refused() -> None:
    with pytest.raises(ConfigError, match="MCP_AUTH_TOKEN"):
        load_settings({**REQUIRED, "MCP_TRANSPORT": "http"})


def test_http_without_token_needs_explicit_opt_out() -> None:
    env = {**REQUIRED, "MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "TRUE"}
    settings = load_settings(env)
    assert settings.allow_unauthenticated
    assert settings.auth_token is None


def test_blank_optional_values_fall_back_to_defaults() -> None:
    settings = load_settings({**REQUIRED, "MCP_PORT": "", "MCP_TRANSPORT": ""})
    assert (settings.port, settings.transport) == (8000, "stdio")


def test_non_numeric_values_are_a_config_error() -> None:
    with pytest.raises(ConfigError, match="MCP_PORT must be a number"):
        load_settings({**REQUIRED, "MCP_PORT": "eighty"})


def test_secrets_are_not_in_the_settings_repr() -> None:
    settings = load_settings({**REQUIRED, "MCP_AUTH_TOKEN": "bearer-value"})
    assert "secret" not in repr(settings)
    assert "bearer-value" not in repr(settings)


def test_no_public_base_url_by_default() -> None:
    assert load_settings(REQUIRED).public_base_url is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://files.example.com", "https://files.example.com"),
        ("https://files.example.com/", "https://files.example.com"),
        ("https://files.example.com:8443", "https://files.example.com:8443"),
    ],
)
def test_public_base_url_is_a_bare_https_host(value: str, expected: str) -> None:
    settings = load_settings({**REQUIRED, "R2_PUBLIC_BASE_URL": value})
    assert settings.public_base_url == expected


@pytest.mark.parametrize(
    "value",
    [
        "http://files.example.com",
        "files.example.com",
        "https://",
        "https://files.example.com/uploads",
        "https://files.example.com?x=1",
        "https://files.example.com#top",
        "https://user:pass@files.example.com",
    ],
)
def test_public_base_url_refuses_anything_but_a_host(value: str) -> None:
    with pytest.raises(ConfigError, match="R2_PUBLIC_BASE_URL must be https://<host>"):
        load_settings({**REQUIRED, "R2_PUBLIC_BASE_URL": value})


def test_blank_public_base_url_means_none() -> None:
    assert load_settings({**REQUIRED, "R2_PUBLIC_BASE_URL": ""}).public_base_url is None
