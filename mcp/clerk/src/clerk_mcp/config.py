"""Server settings, read once from environment variables."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
FALSE_VALUES = frozenset({"", "0", "false", "no", "off"})
# The structure of a Clerk secret key. Anything else is refused at startup, so the key the
# scrubber looks for is exactly the bytes sent: a stray newline cannot reach an HTTP error.
SECRET_KEY_SHAPE = re.compile(r"sk_(live|test)_[A-Za-z0-9]+")


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults."""

    secret_key: str = field(repr=False)
    read_only: bool = False
    timeout_seconds: float = 60.0
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    auth_token: str | None = field(default=None, repr=False)
    allow_unauthenticated: bool = False
    max_request_bytes: int = 4 * MIB
    stateless: bool = False


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        secret_key=_secret_key(env),
        read_only=_flag(env, "CLERK_READ_ONLY"),
        timeout_seconds=_number(env, "CLERK_TIMEOUT_SECONDS", 60),
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


def _secret_key(env: Mapping[str, str]) -> str:
    value = env.get("CLERK_SECRET_KEY", "").strip()
    if not SECRET_KEY_SHAPE.fullmatch(value):
        # Never echo the value: it may be a real key with a typo or in the wrong variable.
        message = (
            "CLERK_SECRET_KEY must be a Clerk secret key: sk_live_ or sk_test_ "
            "followed by letters and digits"
        )
        raise ConfigError(message)
    return value


def _flag(env: Mapping[str, str], name: str) -> bool:
    """Read a true/false switch strictly: an unrecognized value must not mean "off"."""
    value = env.get(name, "").strip().lower()
    if value not in TRUE_VALUES | FALSE_VALUES:
        message = f"{name} must be true or false, got {value!r}"
        raise ConfigError(message)
    return value in TRUE_VALUES


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
