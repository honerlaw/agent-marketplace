"""Microsoft identity platform access tokens, refreshed on demand from a refresh token.

The client secret and refresh token are only ever sent to the token URL (fixed host,
configured tenant); the access token only to the Microsoft Advertising hosts (api.py).
Microsoft returns a new refresh token with every refresh. It is kept in memory and used
next; after a restart the configured one is used again (see the README).
"""

import time

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp.config import Settings

# Refresh this many seconds before Microsoft says the token expires.
EXPIRY_MARGIN_SECONDS = 60
DEFAULT_EXPIRES_IN = 3600
# A token this young was not rejected for its age: 105 then means the account or the
# developer token, and a refresh would not help.
FRESH_SECONDS = 60

# The clock is module-level so tests can move time forward.
now = time.monotonic


class AccessTokens:
    """Hands out a valid access token, refreshing it when it is missing or expired."""

    def __init__(self, settings: Settings, client: httpx2.AsyncClient) -> None:
        """Remember the credentials; nothing is fetched until a token is needed."""
        self._credentials = settings.credentials
        self._refresh_token = settings.credentials.refresh_token or ""
        self._token_url = settings.token_url
        self._scope = settings.scope
        self._client = client
        self._token: str | None = None
        self._expires_at = 0.0
        self._issued_at = 0.0
        # The scrubber covers every rotated refresh token (Microsoft does not revoke the old
        # ones, and there is one per refresh) and every access token until it expires.
        self._refresh_tokens: list[str] = []
        self._access_tokens: list[tuple[str, float]] = []
        self._lock = anyio.Lock()

    def secrets(self) -> list[str]:
        """Every credential the scrubber must remove, including the tokens issued so far."""
        credentials = self._credentials
        configured = [
            credentials.client_secret,
            credentials.refresh_token,
            credentials.developer_token,
        ]
        issued = [token for token, _ in self._access_tokens] + self._refresh_tokens
        return [secret for secret in configured if secret] + issued

    async def get(self) -> str:
        """Return a cached access token that has not expired, refreshing if needed."""
        missing = self._credentials.missing()
        if missing:
            message = f"set {', '.join(missing)} to call the Microsoft Advertising API"
            raise ToolError(message)
        async with self._lock:
            if self._token is None or now() >= self._expires_at:
                self._token = await self._refresh()
            return self._token

    def invalidate(self, rejected: str) -> bool:
        """Drop `rejected` so the next `get` refreshes; tell whether a retry can help.

        A token another caller already replaced is left alone (retry with the new one). A
        token issued under a minute ago is kept, and no retry is worth making.
        """
        if self._token != rejected:
            return True
        if now() - self._issued_at < FRESH_SECONDS:
            return False
        self._token = None
        return True

    async def _refresh(self) -> str:
        try:
            response = await self._client.post(self._token_url, data=self._form())
        except httpx2.HTTPError as error:
            message = f"could not reach the Microsoft token endpoint: {type(error).__name__}"
            raise ToolError(message) from error
        payload = _token_payload(response)
        token = str(payload["access_token"])
        expires_in = _expires_in(payload)
        self._issued_at = now()
        self._expires_at = self._issued_at + _reuse_for(expires_in)
        self._remember_access(token, self._issued_at + expires_in)
        rotated = payload.get("refresh_token")
        if isinstance(rotated, str) and rotated:
            self._refresh_tokens.append(rotated)
            self._refresh_token = rotated
        return token

    def _remember_access(self, token: str, expires_at: float) -> None:
        live = [(old, end) for old, end in self._access_tokens if end > self._issued_at]
        self._access_tokens = [*live, (token, expires_at)]

    def _form(self) -> dict[str, str]:
        form = {
            "client_id": self._credentials.client_id or "",
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "scope": self._scope,
        }
        if self._credentials.client_secret:
            form["client_secret"] = self._credentials.client_secret
        return form


def _token_payload(response: httpx2.Response) -> dict[str, object]:
    """Return the token response, or explain the failure without echoing any secret."""
    try:
        payload = response.json()
    except ValueError:
        payload = None
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if isinstance(payload, dict) and isinstance(token, str) and token:
        return payload
    reason = payload.get("error") if isinstance(payload, dict) else None
    message = (
        f"Microsoft refused to refresh the access token (HTTP {response.status_code}, "
        f"error {reason!r}); {_hint(response.status_code, reason)}"
    )
    raise ToolError(message)


def _hint(status: int, reason: object) -> str:
    if reason == "invalid_grant":
        return (
            "the refresh token is expired or revoked: get a new one with the consent flow "
            "in the README and set MICROSOFT_ADS_REFRESH_TOKEN"
        )
    if status == httpx2.codes.TOO_MANY_REQUESTS or status >= httpx2.codes.INTERNAL_SERVER_ERROR:
        return "Microsoft is rate-limiting or unavailable; retry later"
    return (
        "check MICROSOFT_ADS_CLIENT_ID, MICROSOFT_ADS_CLIENT_SECRET (Web apps only), "
        "MICROSOFT_ADS_TENANT and MICROSOFT_ADS_ENVIRONMENT"
    )


def _expires_in(payload: dict[str, object]) -> float:
    """Seconds until the token expires, as Microsoft states it (an hour if it does not)."""
    value = payload.get("expires_in")
    return float(value) if isinstance(value, int | float) else DEFAULT_EXPIRES_IN


def _reuse_for(expires_in: float) -> float:
    """Seconds to reuse a token: its lifetime less the margin, but at least half of it."""
    return max(expires_in - EXPIRY_MARGIN_SECONDS, expires_in / 2)
