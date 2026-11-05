"""Settings parsing and validation."""

import pytest

from microsoft_ads_mcp.config import (
    DEFAULT_DOWNLOAD_HOSTS,
    ConfigError,
    Credentials,
    Settings,
    load_settings,
)


def test_defaults_need_no_credentials() -> None:
    settings = load_settings({})
    assert settings == Settings()
    assert settings.credentials.missing() == [
        "MICROSOFT_ADS_CLIENT_ID",
        "MICROSOFT_ADS_REFRESH_TOKEN",
        "MICROSOFT_ADS_DEVELOPER_TOKEN",
    ]
    expected = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    assert settings.token_url == expected
    assert settings.download_hosts == DEFAULT_DOWNLOAD_HOSTS


def test_everything_can_be_set() -> None:
    env = {
        "MICROSOFT_ADS_CLIENT_ID": "id",
        "MICROSOFT_ADS_CLIENT_SECRET": "secret",
        "MICROSOFT_ADS_REFRESH_TOKEN": "refresh",
        "MICROSOFT_ADS_DEVELOPER_TOKEN": "BBD37VB98",
        "MICROSOFT_ADS_TENANT": " Organizations ",
        "MICROSOFT_ADS_ENVIRONMENT": "Sandbox",
        "MICROSOFT_ADS_CUSTOMER_ID": "123",
        "MICROSOFT_ADS_ACCOUNT_ID": " 456 ",
        "MICROSOFT_ADS_DOWNLOAD_HOSTS": " .Store.blob.core.windows.net, ,bingads.microsoft.com",
        "MICROSOFT_ADS_TIMEOUT_SECONDS": "30",
        "MICROSOFT_ADS_MAX_RESPONSE_BYTES": "1000",
        "MCP_TRANSPORT": "http",
        "MCP_AUTH_TOKEN": "t",
        "MCP_STATELESS": "true",
    }
    settings = load_settings(env)
    assert settings.credentials == Credentials("id", "secret", "refresh", "BBD37VB98")
    assert settings.credentials.missing() == []
    assert (settings.tenant, settings.environment) == ("organizations", "sandbox")
    assert (settings.customer_id, settings.account_id) == ("123", "456")
    assert settings.download_hosts == ("store.blob.core.windows.net", "bingads.microsoft.com")
    assert (settings.timeout_seconds, settings.max_response_bytes) == (30, 1000)
    assert settings.stateless
    assert settings.service_url("Bulk") == "https://bulk.api.sandbox.bingads.microsoft.com"


@pytest.mark.parametrize(
    "tenant",
    ["common", "consumers", "contoso.onmicrosoft.com", "0b9d8f3e-1c2a-4b5d-8e7f-123456789abc"],
)
def test_valid_tenants(tenant: str) -> None:
    assert load_settings({"MICROSOFT_ADS_TENANT": tenant}).tenant == tenant


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"MICROSOFT_ADS_TENANT": "evil.com/x"}, "MICROSOFT_ADS_TENANT"),
        ({"MICROSOFT_ADS_TENANT": "localhost"}, "MICROSOFT_ADS_TENANT"),
        ({"MICROSOFT_ADS_ENVIRONMENT": "staging"}, "MICROSOFT_ADS_ENVIRONMENT"),
        ({"MICROSOFT_ADS_CUSTOMER_ID": "12-34"}, "MICROSOFT_ADS_CUSTOMER_ID"),
        ({"MICROSOFT_ADS_ACCOUNT_ID": "abc"}, "MICROSOFT_ADS_ACCOUNT_ID"),
        ({"MICROSOFT_ADS_DEVELOPER_TOKEN": "has space"}, "MICROSOFT_ADS_DEVELOPER_TOKEN"),
        ({"MICROSOFT_ADS_REFRESH_TOKEN": "line\nbreak"}, "MICROSOFT_ADS_REFRESH_TOKEN"),
        ({"MICROSOFT_ADS_DOWNLOAD_HOSTS": "https://x.com"}, "MICROSOFT_ADS_DOWNLOAD_HOSTS"),
        ({"MICROSOFT_ADS_TIMEOUT_SECONDS": "soon"}, "must be a number"),
        ({"MICROSOFT_ADS_MAX_RESPONSE_BYTES": "-1"}, "positive"),
        ({"MCP_PORT": "inf"}, "positive"),
        ({"MCP_TRANSPORT": "sse"}, "MCP_TRANSPORT"),
        ({"MCP_TRANSPORT": "http"}, "MCP_AUTH_TOKEN"),
    ],
)
def test_bad_values_are_refused(env: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        load_settings(env)


def test_http_without_auth_must_be_explicit() -> None:
    env = {"MCP_TRANSPORT": "http", "MCP_ALLOW_UNAUTHENTICATED": "yes"}
    assert load_settings(env).allow_unauthenticated


def test_a_blank_download_hosts_value_keeps_the_default() -> None:
    settings = load_settings({"MICROSOFT_ADS_DOWNLOAD_HOSTS": "  "})
    assert settings.download_hosts == DEFAULT_DOWNLOAD_HOSTS
