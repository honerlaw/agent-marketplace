"""Server settings, read once from environment variables."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://ads-api.reddit.com/api/v3"
DEFAULT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"  # noqa: S105 - a URL, not a secret
DEFAULT_OPENAPI_URL = "https://ads-api.reddit.com/api/v3/openapi.json"
DEFAULT_USER_AGENT = "python:reddit-ads-mcp:0.1.0 (by /u/unset)"
MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
REFRESH_VARIABLES = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_REFRESH_TOKEN")


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Credentials:
    """Either an OAuth app plus refresh token, or a ready-made access token."""

    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None
    access_token: str | None = None


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults."""

    credentials: Credentials
    user_agent: str = DEFAULT_USER_AGENT
    base_url: str = DEFAULT_BASE_URL
    token_url: str = DEFAULT_TOKEN_URL
    timeout_seconds: float = 120.0
    openapi_path: str | None = None
    openapi_url: str = DEFAULT_OPENAPI_URL
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    auth_token: str | None = None
    allow_unauthenticated: bool = False
    max_request_bytes: int = 4 * MIB
    stateless: bool = False


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        credentials=_credentials(env),
        user_agent=env.get("REDDIT_USER_AGENT") or DEFAULT_USER_AGENT,
        base_url=env.get("REDDIT_ADS_BASE_URL") or DEFAULT_BASE_URL,
        token_url=env.get("REDDIT_TOKEN_URL") or DEFAULT_TOKEN_URL,
        timeout_seconds=_number(env, "REDDIT_TIMEOUT_SECONDS", 120),
        openapi_path=env.get("REDDIT_ADS_OPENAPI_PATH") or None,
        openapi_url=env.get("REDDIT_ADS_OPENAPI_URL") or DEFAULT_OPENAPI_URL,
        transport=env.get("MCP_TRANSPORT") or "stdio",
        host=env.get("MCP_HOST") or "127.0.0.1",
        port=int(_number(env, "MCP_PORT", 8000)),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=env.get("MCP_ALLOW_UNAUTHENTICATED", "").lower() in TRUE_VALUES,
        max_request_bytes=int(_number(env, "MCP_MAX_REQUEST_BYTES", 4 * MIB)),
        stateless=env.get("MCP_STATELESS", "").lower() in TRUE_VALUES,
    )
    _check_transport(settings)
    return settings


def _credentials(env: Mapping[str, str]) -> Credentials:
    """Accept exactly one auth mode: a static access token, or all three refresh values."""
    refresh = [env.get(name) or None for name in REFRESH_VARIABLES]
    access_token = env.get("REDDIT_ACCESS_TOKEN") or None
    if access_token is not None and any(refresh):
        message = "set either REDDIT_ACCESS_TOKEN or the refresh-token credentials, not both"
        raise ConfigError(message)
    if access_token is None and not all(refresh):
        message = f"set all of {', '.join(REFRESH_VARIABLES)} (or REDDIT_ACCESS_TOKEN instead)"
        raise ConfigError(message)
    client_id, client_secret, refresh_token = refresh
    return Credentials(client_id, client_secret, refresh_token, access_token)


def _number(env: Mapping[str, str], name: str, default: float) -> float:
    value = env.get(name) or str(default)
    try:
        return float(value)
    except ValueError as error:
        message = f"{name} must be a number, got {value!r}"
        raise ConfigError(message) from error


def _check_transport(settings: Settings) -> None:
    if settings.transport not in {"stdio", "http"}:
        message = f"MCP_TRANSPORT must be 'stdio' or 'http', got {settings.transport!r}"
        raise ConfigError(message)
    unguarded = not settings.auth_token and not settings.allow_unauthenticated
    if settings.transport == "http" and unguarded:
        message = (
            "MCP_AUTH_TOKEN must be set in http mode "
            "(or set MCP_ALLOW_UNAUTHENTICATED=true to run without auth)"
        )
        raise ConfigError(message)
