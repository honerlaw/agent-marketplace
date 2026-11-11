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


@pytest.mark.parametrize(
    "value",
    ["", "pk_live_abc", "abc", "sk_", "sk_prod_abc", "sk_live_", "sk_live_a\nb", "sk_live_a b"],
)
def test_secret_key_must_have_the_clerk_shape(value: str) -> None:
    with pytest.raises(ConfigError, match="CLERK_SECRET_KEY"):
        load_settings({"CLERK_SECRET_KEY": value})


def test_a_refused_key_is_never_echoed() -> None:
    with pytest.raises(ConfigError) as raised:
        load_settings({"CLERK_SECRET_KEY": "sk_live_Real9Value!"})
    assert "Real9Value" not in str(raised.value)


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


@pytest.mark.parametrize("raw", ["sk_live_abc\n", "sk_live_abc\r\n", " sk_live_abc\t"])
def test_surrounding_whitespace_is_stripped_from_the_key(raw: str) -> None:
    assert load_settings({"CLERK_SECRET_KEY": raw}).secret_key == "sk_live_abc"  # noqa: S105


@pytest.mark.parametrize(
    ("value", "expected"),
    [("on", True), ("TRUE\n", True), ("1", True), ("off", False), ("No", False), ("", False)],
)
def test_switches_read_true_and_false(value: str, expected: bool) -> None:  # noqa: FBT001
    settings = load_settings({"CLERK_SECRET_KEY": KEY, "CLERK_READ_ONLY": value})
    assert settings.read_only is expected


@pytest.mark.parametrize("name", ["CLERK_READ_ONLY", "MCP_ALLOW_UNAUTHENTICATED", "MCP_STATELESS"])
@pytest.mark.parametrize("value", ["enabled", "y", "2"])
def test_an_unrecognized_switch_value_stops_startup(name: str, value: str) -> None:
    with pytest.raises(ConfigError, match=f"{name} must be true or false"):
        load_settings({"CLERK_SECRET_KEY": KEY, name: value})


def test_settings_repr_hides_the_key_and_the_token() -> None:
    env = {"CLERK_SECRET_KEY": "sk_live_hidden1", "MCP_AUTH_TOKEN": "tok_hidden2"}
    shown = repr(load_settings(env))
    assert "hidden1" not in shown
    assert "hidden2" not in shown
