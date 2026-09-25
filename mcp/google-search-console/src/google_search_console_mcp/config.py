"""Server settings, read once from environment variables."""

import json
from collections.abc import Mapping
from dataclasses import dataclass

MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
CredentialsInfo = dict[str, object]


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults.

    Google credentials are not resolved here: `credentials_info` is only parsed, and
    Application Default Credentials are looked up on the first tool call, so the server
    starts (and answers /healthz) before credentials exist.
    """

    credentials_info: CredentialsInfo | None = None
    read_only: bool = False
    timeout_seconds: float = 120.0
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
        credentials_info=_credentials_info(env.get("GSC_CREDENTIALS_JSON") or None),
        read_only=_flag(env, "GSC_READ_ONLY"),
        timeout_seconds=_number(env, "GSC_TIMEOUT_SECONDS", 120),
        transport=env.get("MCP_TRANSPORT") or "stdio",
        host=env.get("MCP_HOST") or "127.0.0.1",
        port=int(_number(env, "MCP_PORT", 8000)),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=_flag(env, "MCP_ALLOW_UNAUTHENTICATED"),
        max_request_bytes=int(_number(env, "MCP_MAX_REQUEST_BYTES", 4 * MIB)),
        stateless=_flag(env, "MCP_STATELESS"),
    )
    _check_transport(settings)
    return settings


def _credentials_info(raw: str | None) -> CredentialsInfo | None:
    if raw is None:
        return None
    try:
        info = json.loads(raw)
    except ValueError as error:
        message = "GSC_CREDENTIALS_JSON must be a JSON credentials object"
        raise ConfigError(message) from error
    if not isinstance(info, dict):
        message = "GSC_CREDENTIALS_JSON must be a JSON object, not a list or scalar"
        raise ConfigError(message)
    return info


def _flag(env: Mapping[str, str], name: str) -> bool:
    return env.get(name, "").lower() in TRUE_VALUES


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
