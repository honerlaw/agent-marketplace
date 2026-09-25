"""Google OAuth credentials, resolved on first use and refreshed off the event loop."""

from collections.abc import Callable

import anyio
import google.auth
from google.auth.credentials import Credentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import credentials as user_credentials
from google.oauth2 import service_account
from mcp.server.mcpserver.exceptions import ToolError

from google_search_console_mcp.config import CredentialsInfo, Settings

READ_WRITE_SCOPE = "https://www.googleapis.com/auth/webmasters"
READ_ONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
SERVICE_ACCOUNT = "service_account"
AUTHORIZED_USER = "authorized_user"

CredentialsLoader = Callable[[], Credentials]


def scopes_for(settings: Settings) -> list[str]:
    """Return the single OAuth scope this server asks for."""
    return [READ_ONLY_SCOPE if settings.read_only else READ_WRITE_SCOPE]


def default_loader(settings: Settings) -> CredentialsLoader:
    """Return a loader for GSC_CREDENTIALS_JSON, else Application Default Credentials."""
    scopes = scopes_for(settings)
    info = settings.credentials_info

    def load() -> Credentials:
        if info is None:
            return google.auth.default(scopes=scopes)[0]
        return credentials_from_info(info, scopes)

    return load


def credentials_from_info(info: CredentialsInfo, scopes: list[str]) -> Credentials:
    """Build service-account or authorized-user credentials from parsed JSON.

    Only these two types are accepted. google-auth's generic loader also takes
    `external_account` configurations, which can make the server fetch arbitrary URLs
    or run executables, so they are refused rather than trusted.
    """
    kind = info.get("type")
    # google-auth ships py.typed but leaves these two constructors unannotated.
    try:
        loaded: Credentials
        if kind == SERVICE_ACCOUNT:
            loaded = service_account.Credentials.from_service_account_info(info, scopes=scopes)  # type: ignore[no-untyped-call]
            return loaded
        if kind == AUTHORIZED_USER:
            loaded = user_credentials.Credentials.from_authorized_user_info(info, scopes=scopes)  # type: ignore[no-untyped-call]
            return loaded
    except ValueError as error:
        message = f"GSC_CREDENTIALS_JSON is not valid {kind} credentials: {error}"
        raise ToolError(message) from error
    message = f"GSC_CREDENTIALS_JSON type must be {SERVICE_ACCOUNT!r} or {AUTHORIZED_USER!r}"
    raise ToolError(message)


class TokenSource:
    """Hands out a valid access token, loading and refreshing credentials as needed."""

    def __init__(self, loader: CredentialsLoader) -> None:
        """Remember how to load credentials; nothing is loaded until a token is needed."""
        self._loader = loader
        self._credentials: Credentials | None = None
        self._lock = anyio.Lock()

    async def token(self) -> str:
        """Return a bearer token, raising ToolError when credentials are missing or bad."""
        async with self._lock:
            try:
                return await anyio.to_thread.run_sync(self._valid_token)
            except GoogleAuthError as error:
                message = (
                    f"Google credentials are unavailable: {error}. Set GSC_CREDENTIALS_JSON or "
                    "GOOGLE_APPLICATION_CREDENTIALS, or run `gcloud auth application-default login`"
                )
                raise ToolError(message) from error

    def _valid_token(self) -> str:
        if self._credentials is None:
            self._credentials = self._loader()
        if not self._credentials.valid:
            # google-auth ships py.typed but leaves `refresh` unannotated.
            self._credentials.refresh(Request())  # type: ignore[no-untyped-call]
        return str(self._credentials.token)
