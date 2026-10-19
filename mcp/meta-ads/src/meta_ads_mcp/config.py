"""Server settings, read once from environment variables."""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

API_HOST = "graph.facebook.com"
DEFAULT_API_VERSION = "v26.0"
MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
API_VERSION_SHAPE = re.compile(r"v[0-9]+\.[0-9]+")


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults.

    The access token is only checked when a tool needs it, so the server starts (and
    answers /healthz) before credentials exist. The API version is the only knob for
    where requests go: the base URL derives from it, so the token can only be sent to
    Meta's Graph API host.
    """

    access_token: str | None = None
    app_id: str | None = None
    app_secret: str | None = None
    api_version: str = DEFAULT_API_VERSION
    spec_path: str | None = None
    timeout_seconds: float = 120.0
    max_response_bytes: int = 2 * MIB
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    auth_token: str | None = None
    allow_unauthenticated: bool = False
    max_request_bytes: int = 4 * MIB
    stateless: bool = False

    @property
    def base_url(self) -> str:
        """The versioned API root every request goes to."""
        return f"https://{API_HOST}/{self.api_version}"

    @property
    def secrets(self) -> tuple[str, ...]:
        """Every configured credential value, for the output scrub."""
        return tuple(value for value in (self.access_token, self.app_secret) if value)


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        access_token=env.get("META_ADS_ACCESS_TOKEN") or None,
        app_id=env.get("META_APP_ID") or None,
        app_secret=env.get("META_APP_SECRET") or None,
        api_version=_api_version(env.get("META_ADS_API_VERSION") or DEFAULT_API_VERSION),
        spec_path=env.get("META_ADS_SPEC_PATH") or None,
        timeout_seconds=_number(env, "META_ADS_TIMEOUT_SECONDS", 120),
        max_response_bytes=int(_number(env, "META_ADS_MAX_RESPONSE_BYTES", 2 * MIB)),
        transport=env.get("MCP_TRANSPORT") or "stdio",
        host=env.get("MCP_HOST") or "127.0.0.1",
        port=int(_number(env, "MCP_PORT", 8000)),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=_flag(env, "MCP_ALLOW_UNAUTHENTICATED"),
        max_request_bytes=int(_number(env, "MCP_MAX_REQUEST_BYTES", 4 * MIB)),
        stateless=_flag(env, "MCP_STATELESS"),
    )
    _check_app(settings)
    _check_transport(settings)
    return settings


def _api_version(raw: str) -> str:
    if not API_VERSION_SHAPE.fullmatch(raw):
        message = f"META_ADS_API_VERSION must look like 'v26.0', got {raw!r}"
        raise ConfigError(message)
    return raw


def _flag(env: Mapping[str, str], name: str) -> bool:
    return env.get(name, "").lower() in TRUE_VALUES


def _number(env: Mapping[str, str], name: str, default: float) -> float:
    value = env.get(name) or str(default)
    try:
        number = float(value)
    except ValueError as error:
        message = f"{name} must be a number, got {value!r}"
        raise ConfigError(message) from error
    if not math.isfinite(number) or number <= 0:
        message = f"{name} must be a positive number, got {value!r}"
        raise ConfigError(message)
    return number


def _check_app(settings: Settings) -> None:
    if (settings.app_id is None) != (settings.app_secret is None):
        message = "set META_APP_ID and META_APP_SECRET together, or neither"
        raise ConfigError(message)


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
