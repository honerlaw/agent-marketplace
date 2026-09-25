"""Reddit OAuth access tokens: a static token, or one refreshed on demand.

The client secret and refresh token are only ever sent to the token URL; the
access token this returns is only ever sent to the Ads API base URL (see api.py).
"""

import time

import anyio
import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from reddit_ads_mcp.config import Settings

# Refresh this many seconds before Reddit says the token expires.
EXPIRY_MARGIN_SECONDS = 60
DEFAULT_EXPIRES_IN = 3600

# The clock is module-level so tests can move time forward.
now = time.monotonic


class AccessTokens:
    """Hands out a valid access token, refreshing it when it is missing or expired."""

    def __init__(self, settings: Settings, client: httpx2.AsyncClient) -> None:
        """Remember the credentials; nothing is fetched until a token is needed."""
        credentials = settings.credentials
        self._static = credentials.access_token
        self._client_auth = (credentials.client_id or "", credentials.client_secret or "")
        self._refresh_token = credentials.refresh_token or ""
        self._token_url = settings.token_url
        self._client = client
        self._token: str | None = None
        self._expires_at = 0.0
        self._lock = anyio.Lock()

    @property
    def refreshable(self) -> bool:
        """Whether a rejected token can be replaced by refreshing."""
        return self._static is None

    async def get(self) -> str:
        """Return the static token, or a cached token that has not expired."""
        if self._static is not None:
            return self._static
        async with self._lock:
            if self._token is None or now() >= self._expires_at:
                self._token = await self._refresh()
            return self._token

    def invalidate(self, rejected: str) -> None:
        """Drop `rejected` so the next `get` refreshes, unless it was already replaced."""
        if self._token == rejected:
            self._token = None

    async def _refresh(self) -> str:
        form = {"grant_type": "refresh_token", "refresh_token": self._refresh_token}
        try:
            response = await self._client.post(self._token_url, data=form, auth=self._client_auth)
        except httpx2.HTTPError as error:
            message = f"could not reach the Reddit token endpoint: {type(error).__name__}"
            raise ToolError(message) from error
        payload = _token_payload(response)
        self._expires_at = now() + _lifetime(payload)
        rotated = payload.get("refresh_token")
        if isinstance(rotated, str) and rotated:
            self._refresh_token = rotated
        return str(payload["access_token"])


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
    status = response.status_code
    hint = (
        "Reddit is rate-limiting or unavailable; retry later"
        if status == httpx2.codes.TOO_MANY_REQUESTS or status >= httpx2.codes.INTERNAL_SERVER_ERROR
        else "check REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET and REDDIT_REFRESH_TOKEN"
    )
    message = (
        f"Reddit refused to refresh the access token (HTTP {status}, error {reason!r}); {hint}"
    )
    raise ToolError(message)


def _lifetime(payload: dict[str, object]) -> float:
    """Seconds to reuse a token: its lifetime less the margin, but at least half of it."""
    value = payload.get("expires_in")
    expires_in = float(value) if isinstance(value, int | float) else DEFAULT_EXPIRES_IN
    return max(expires_in - EXPIRY_MARGIN_SECONDS, expires_in / 2)
