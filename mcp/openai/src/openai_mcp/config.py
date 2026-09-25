"""Server settings, read once from environment variables."""

from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAPI_URL = (
    "https://raw.githubusercontent.com/openai/openai-openapi/manual_spec/openapi.yaml"
)
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


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        api_key=_required(env, "OPENAI_API_KEY"),
        base_url=env.get("OPENAI_BASE_URL", DEFAULT_BASE_URL),
        organization=env.get("OPENAI_ORG_ID") or None,
        project=env.get("OPENAI_PROJECT_ID") or None,
        timeout_seconds=float(env.get("OPENAI_TIMEOUT_SECONDS", "600")),
        max_binary_bytes=int(env.get("OPENAI_MCP_MAX_BINARY_BYTES", str(20 * MIB))),
        openapi_path=env.get("OPENAI_OPENAPI_PATH") or None,
        openapi_url=env.get("OPENAI_OPENAPI_URL", DEFAULT_OPENAPI_URL),
        transport=env.get("MCP_TRANSPORT", "stdio"),
        host=env.get("MCP_HOST", "127.0.0.1"),
        port=int(env.get("MCP_PORT", "8000")),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=env.get("MCP_ALLOW_UNAUTHENTICATED", "").lower() in TRUE_VALUES,
        max_request_bytes=int(env.get("MCP_MAX_REQUEST_BYTES", str(64 * MIB))),
    )
    _check_transport(settings)
    return settings


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name, "")
    if not value:
        message = f"{name} must be set"
        raise ConfigError(message)
    return value


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
