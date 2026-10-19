"""Server settings, read once from environment variables."""

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

API_HOST = "https://googleads.googleapis.com"
DEFAULT_API_VERSION = "v26"
MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
API_VERSION_SHAPE = re.compile(r"v[0-9]+")
CUSTOMER_ID_SHAPE = re.compile(r"[0-9]+")
CredentialsInfo = dict[str, object]


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults.

    Google credentials are not resolved here: `credentials_info` is only parsed, and
    Application Default Credentials are looked up on the first tool call, so the server
    starts (and answers /healthz) before credentials exist. The API version is the only
    knob for where requests go: the base URL and the Discovery URL both derive from it,
    so the access token can only ever be sent to Google.
    """

    credentials_info: CredentialsInfo | None = None
    login_customer_id: str | None = None
    api_version: str = DEFAULT_API_VERSION
    discovery_path: str | None = None
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
        return f"{API_HOST}/{self.api_version}"

    @property
    def discovery_url(self) -> str:
        """Google's Discovery document for the configured version."""
        return f"{API_HOST}/$discovery/rest?version={self.api_version}"


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        credentials_info=_credentials_info(env.get("GOOGLE_ADS_CREDENTIALS_JSON") or None),
        login_customer_id=_login_customer_id(env.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or None),
        api_version=_api_version(env.get("GOOGLE_ADS_API_VERSION") or DEFAULT_API_VERSION),
        discovery_path=env.get("GOOGLE_ADS_DISCOVERY_PATH") or None,
        timeout_seconds=_number(env, "GOOGLE_ADS_TIMEOUT_SECONDS", 120),
        max_response_bytes=int(_number(env, "GOOGLE_ADS_MAX_RESPONSE_BYTES", 2 * MIB)),
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


def normalize_customer_id(value: str) -> str | None:
    """Return a customer id as bare digits ("123-456-7890" -> "1234567890"), or None."""
    digits = value.strip().replace("-", "")
    return digits if CUSTOMER_ID_SHAPE.fullmatch(digits) else None


def _credentials_info(raw: str | None) -> CredentialsInfo | None:
    if raw is None:
        return None
    try:
        info = json.loads(raw)
    except ValueError as error:
        message = "GOOGLE_ADS_CREDENTIALS_JSON must be a JSON credentials object"
        raise ConfigError(message) from error
    if not isinstance(info, dict):
        message = "GOOGLE_ADS_CREDENTIALS_JSON must be a JSON object, not a list or scalar"
        raise ConfigError(message)
    return info


def _login_customer_id(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = normalize_customer_id(raw)
    if normalized is None:
        message = f"GOOGLE_ADS_LOGIN_CUSTOMER_ID must look like 123-456-7890, got {raw!r}"
        raise ConfigError(message)
    return normalized


def _api_version(raw: str) -> str:
    if not API_VERSION_SHAPE.fullmatch(raw):
        message = f"GOOGLE_ADS_API_VERSION must look like 'v26', got {raw!r}"
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
