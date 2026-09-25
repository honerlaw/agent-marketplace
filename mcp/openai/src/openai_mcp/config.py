"""Server settings, read once from environment variables."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAPI_URL = "https://raw.githubusercontent.com/openai/openai-openapi/main/openapi.yaml"
MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    organization: str | None = None
    project: str | None = None
    timeout_seconds: float = 600.0
    max_binary_bytes: int = 20 * MIB
    openapi_path: str | None = None
    openapi_url: str = DEFAULT_OPENAPI_URL
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    auth_token: str | None = None
    allow_unauthenticated: bool = False
    max_request_bytes: int = 64 * MIB
    stateless: bool = False


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        api_key=_required(env, "OPENAI_API_KEY"),
        base_url=env.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL,
        organization=env.get("OPENAI_ORG_ID") or None,
        project=env.get("OPENAI_PROJECT_ID") or None,
        timeout_seconds=_number(env, "OPENAI_TIMEOUT_SECONDS", 600),
        max_binary_bytes=int(_number(env, "OPENAI_MCP_MAX_BINARY_BYTES", 20 * MIB)),
        openapi_path=env.get("OPENAI_OPENAPI_PATH") or None,
        openapi_url=env.get("OPENAI_OPENAPI_URL") or DEFAULT_OPENAPI_URL,
        transport=env.get("MCP_TRANSPORT") or "stdio",
        host=env.get("MCP_HOST") or "127.0.0.1",
        port=int(_number(env, "MCP_PORT", 8000)),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=env.get("MCP_ALLOW_UNAUTHENTICATED", "").lower() in TRUE_VALUES,
        max_request_bytes=int(_number(env, "MCP_MAX_REQUEST_BYTES", 64 * MIB)),
        stateless=env.get("MCP_STATELESS", "").lower() in TRUE_VALUES,
    )
    _check_transport(settings)
    return settings


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        message = f"{name} must be set"
        raise ConfigError(message)
    return value


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
