"""Server settings, read once from environment variables."""

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

MIB = 1024 * 1024
TRUE_VALUES = frozenset({"1", "true", "yes"})
ENVIRONMENTS = frozenset({"production", "sandbox"})
NAMED_TENANTS = frozenset({"common", "organizations", "consumers"})
TENANT_ID_SHAPE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
DOMAIN_SHAPE = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)+")
ID_SHAPE = re.compile(r"[0-9]+")
CREDENTIAL_SHAPE = re.compile(r"[!-~]+")
DEFAULT_DOWNLOAD_HOSTS = ("blob.core.windows.net", "bingads.microsoft.com")
TOKEN_HOST = "https://login.microsoftonline.com"  # noqa: S105 - a URL, not a secret
# The first label of each service's API host; Customer Management and Billing share one.
SERVICE_HOSTS = {
    "AdInsight": "adinsight",
    "Bulk": "bulk",
    "CampaignManagement": "campaign",
    "CustomerBilling": "clientcenter",
    "CustomerManagement": "clientcenter",
    "Reporting": "reporting",
}
SCOPES = {
    "production": "https://ads.microsoft.com/msads.manage offline_access",
    "sandbox": "https://si.ads.microsoft.com/msads.manage offline_access",
}
CREDENTIAL_VARIABLES = {
    "client_id": "MICROSOFT_ADS_CLIENT_ID",
    "client_secret": "MICROSOFT_ADS_CLIENT_SECRET",
    "refresh_token": "MICROSOFT_ADS_REFRESH_TOKEN",
    "developer_token": "MICROSOFT_ADS_DEVELOPER_TOKEN",
}


class ConfigError(ValueError):
    """Raised when the environment does not describe a valid configuration."""


@dataclass(frozen=True)
class Credentials:
    """The operator's OAuth app, refresh token and developer token.

    All but the client secret are needed for an API call; none are needed to start, so
    discovery works and the image starts without them. A public (native) app has no
    secret and must not send one.
    """

    client_id: str | None = None
    client_secret: str | None = None
    refresh_token: str | None = None
    developer_token: str | None = None

    def missing(self) -> list[str]:
        """Return the environment variables an API call still needs."""
        required = ("client_id", "refresh_token", "developer_token")
        return [CREDENTIAL_VARIABLES[name] for name in required if not getattr(self, name)]


@dataclass(frozen=True)
class Settings:
    """Everything the server needs to know, with safe defaults.

    Requests go only to the fixed Microsoft hosts for the configured environment and
    tokens only to Microsoft's identity platform: there is no base-URL or token-URL knob.
    """

    credentials: Credentials = Credentials()
    tenant: str = "common"
    environment: str = "production"
    customer_id: str | None = None
    account_id: str | None = None
    download_hosts: tuple[str, ...] = DEFAULT_DOWNLOAD_HOSTS
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
    def token_url(self) -> str:
        """Microsoft's OAuth token endpoint for the configured tenant."""
        return f"{TOKEN_HOST}/{self.tenant}/oauth2/v2.0/token"

    @property
    def scope(self) -> str:
        """The OAuth scope for the configured environment."""
        return SCOPES[self.environment]

    def service_url(self, service: str) -> str:
        """Return the API host for `service` in the configured environment."""
        sandbox = ".sandbox" if self.environment == "sandbox" else ""
        return f"https://{SERVICE_HOSTS[service]}.api{sandbox}.bingads.microsoft.com"


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build settings from an environment mapping, validating as we go."""
    settings = Settings(
        credentials=_credentials(env),
        tenant=_tenant(env.get("MICROSOFT_ADS_TENANT") or "common"),
        environment=_environment(env.get("MICROSOFT_ADS_ENVIRONMENT") or "production"),
        customer_id=_id(env, "MICROSOFT_ADS_CUSTOMER_ID"),
        account_id=_id(env, "MICROSOFT_ADS_ACCOUNT_ID"),
        download_hosts=_download_hosts(env.get("MICROSOFT_ADS_DOWNLOAD_HOSTS")),
        timeout_seconds=_number(env, "MICROSOFT_ADS_TIMEOUT_SECONDS", 120),
        max_response_bytes=int(_number(env, "MICROSOFT_ADS_MAX_RESPONSE_BYTES", 2 * MIB)),
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


def normalize_id(value: str) -> str | None:
    """Return a customer or account id as bare digits, or None if it is not one."""
    digits = value.strip()
    return digits if ID_SHAPE.fullmatch(digits) else None


def _credentials(env: Mapping[str, str]) -> Credentials:
    values = {name: env.get(variable) or None for name, variable in CREDENTIAL_VARIABLES.items()}
    for name, value in values.items():
        if value is not None and not CREDENTIAL_SHAPE.fullmatch(value):
            variable = CREDENTIAL_VARIABLES[name]
            message = f"{variable} must be printable ASCII without spaces"
            raise ConfigError(message)
    return Credentials(**values)


def _tenant(raw: str) -> str:
    tenant = raw.strip().lower()
    known = tenant in NAMED_TENANTS or TENANT_ID_SHAPE.fullmatch(tenant)
    if not known and not DOMAIN_SHAPE.fullmatch(tenant):
        message = (
            "MICROSOFT_ADS_TENANT must be common, organizations, consumers, a tenant GUID "
            f"or a domain like contoso.onmicrosoft.com, got {raw!r}"
        )
        raise ConfigError(message)
    return tenant


def _environment(raw: str) -> str:
    environment = raw.strip().lower()
    if environment not in ENVIRONMENTS:
        message = f"MICROSOFT_ADS_ENVIRONMENT must be 'production' or 'sandbox', got {raw!r}"
        raise ConfigError(message)
    return environment


def _id(env: Mapping[str, str], name: str) -> str | None:
    raw = env.get(name) or None
    if raw is None:
        return None
    normalized = normalize_id(raw)
    if normalized is None:
        message = f"{name} must be digits, got {raw!r}"
        raise ConfigError(message)
    return normalized


def _download_hosts(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return DEFAULT_DOWNLOAD_HOSTS
    hosts = tuple(part.strip().lower().lstrip(".") for part in raw.split(",") if part.strip())
    bad = [host for host in hosts if not DOMAIN_SHAPE.fullmatch(host)]
    if bad:
        message = f"MICROSOFT_ADS_DOWNLOAD_HOSTS must be domain names, got {bad}"
        raise ConfigError(message)
    return hosts


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
