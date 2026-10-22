"""Server settings, read once from environment variables.

Nothing about the bucket is built in: the account, bucket, key pair, URL lifetimes and any
public hostname all come from the deployment's environment.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from r2_uploads_mcp.presign import MAX_EXPIRES_SECONDS

MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
REQUIRED = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")
# The account id becomes part of the endpoint's hostname, so it must be exactly an id.
ACCOUNT_ID = re.compile(r"[0-9a-f]{32}")
BUCKET_NAME = re.compile(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]")


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults for the optional parts."""

    account_id: str
    access_key_id: str
    secret_access_key: str = field(repr=False)
    bucket: str
    upload_expires_seconds: int = 15 * 60
    download_expires_seconds: int = 24 * 60 * 60
    timeout_seconds: float = 30.0
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    auth_token: str | None = field(default=None, repr=False)
    allow_unauthenticated: bool = False
    max_request_bytes: int = 4 * MIB
    stateless: bool = False
    public_base_url: str | None = None

    @property
    def endpoint_host(self) -> str:
        """The account's S3-compatible R2 endpoint."""
        return f"{self.account_id}.r2.cloudflarestorage.com"


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    missing = [name for name in REQUIRED if not env.get(name)]
    if missing:
        message = f"missing required environment variables: {', '.join(missing)}"
        raise ConfigError(message)
    settings = Settings(
        account_id=env["R2_ACCOUNT_ID"],
        access_key_id=env["R2_ACCESS_KEY_ID"],
        secret_access_key=env["R2_SECRET_ACCESS_KEY"],
        bucket=env["R2_BUCKET"],
        upload_expires_seconds=_expiry(env, "R2_UPLOAD_EXPIRES_SECONDS", 15 * 60),
        download_expires_seconds=_expiry(env, "R2_DOWNLOAD_EXPIRES_SECONDS", 24 * 60 * 60),
        timeout_seconds=_number(env, "R2_TIMEOUT_SECONDS", 30),
        transport=env.get("MCP_TRANSPORT") or "stdio",
        host=env.get("MCP_HOST") or "127.0.0.1",
        port=int(_number(env, "MCP_PORT", 8000)),
        auth_token=env.get("MCP_AUTH_TOKEN") or None,
        allow_unauthenticated=_flag(env, "MCP_ALLOW_UNAUTHENTICATED"),
        max_request_bytes=int(_number(env, "MCP_MAX_REQUEST_BYTES", 4 * MIB)),
        stateless=_flag(env, "MCP_STATELESS"),
        public_base_url=_public_base_url(env.get("R2_PUBLIC_BASE_URL") or None),
    )
    _check_bucket(settings)
    _check_transport(settings)
    return settings


def _flag(env: Mapping[str, str], name: str) -> bool:
    return env.get(name, "").lower() in TRUE_VALUES


def _number(env: Mapping[str, str], name: str, default: float) -> float:
    value = env.get(name) or str(default)
    try:
        return float(value)
    except ValueError as error:
        message = f"{name} must be a number, got {value!r}"
        raise ConfigError(message) from error


def _expiry(env: Mapping[str, str], name: str, default: int) -> int:
    seconds = int(_number(env, name, default))
    if not 1 <= seconds <= MAX_EXPIRES_SECONDS:
        message = f"{name} must be between 1 and {MAX_EXPIRES_SECONDS} seconds (7 days)"
        raise ConfigError(message)
    return seconds


def _public_base_url(value: str | None) -> str | None:
    """Return `https://<host>` from R2_PUBLIC_BASE_URL, refusing anything more than a host."""
    if value is None:
        return None
    parts = urlsplit(value)
    bare = parts.scheme == "https" and parts.hostname and "@" not in parts.netloc
    if not bare or parts.path not in {"", "/"} or parts.query or parts.fragment:
        message = f"R2_PUBLIC_BASE_URL must be https://<host> and nothing else, got {value!r}"
        raise ConfigError(message)
    return f"https://{parts.netloc}"


def _check_bucket(settings: Settings) -> None:
    if not ACCOUNT_ID.fullmatch(settings.account_id):
        message = "R2_ACCOUNT_ID must be the 32-character hex Cloudflare account id"
        raise ConfigError(message)
    if not BUCKET_NAME.fullmatch(settings.bucket):
        message = f"R2_BUCKET is not a valid bucket name: {settings.bucket!r}"
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
