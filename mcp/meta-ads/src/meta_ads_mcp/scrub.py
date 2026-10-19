"""Keeps the operator's credentials out of everything the model sees.

Three layers, applied to every tool result and every error message:

1. Every string has each credential literal (the access token, the app secret and the
   `appsecret_proof` derived from them) replaced, wherever it appears, including inside
   JSON that Meta returns as a string.
2. URLs under a `paging` object lose their `access_token` and `appsecret_proof`
   parameters, which Meta writes into `next` / `previous`; other strings are never
   rewritten, so ad data such as a creative's link comes back as it was.
3. The value of any JSON key named `access_token` is replaced: page tokens and minted
   tokens are credentials too, and the system user already holds the assets.
"""

import hashlib
import hmac
from collections.abc import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit

REDACTED = "[redacted]"
TOKEN_KEY = "access_token"  # noqa: S105 - the JSON key name, not a credential
PAGING_KEY = "paging"
PAGING_CREDENTIALS = frozenset({"access_token", "appsecret_proof"})


def appsecret_proof(access_token: str, app_secret: str) -> str:
    """Meta's proof: HMAC-SHA256 with key = app secret, message = access token, hex."""
    return hmac.new(app_secret.encode(), access_token.encode(), hashlib.sha256).hexdigest()


class Scrubber:
    """Removes a fixed set of credential literals from values and text."""

    def __init__(self, literals: Iterable[str]) -> None:
        """Remember the literals; empty ones are ignored, longest are replaced first."""
        self._literals = sorted({value for value in literals if value}, key=len, reverse=True)

    def text(self, text: str) -> str:
        """Return `text` with every credential literal replaced."""
        for literal in self._literals:
            text = text.replace(literal, REDACTED)
        return text

    def value(self, value: object) -> object:
        """Return a JSON-like value with all three layers applied."""
        return self._walk(value, in_paging=False)

    def _walk(self, value: object, *, in_paging: bool) -> object:
        if isinstance(value, dict):
            return {key: self._entry(key, item, in_paging=in_paging) for key, item in value.items()}
        if isinstance(value, list):
            return [self._walk(item, in_paging=in_paging) for item in value]
        if isinstance(value, str):
            return self.text(_without_credentials(value) if in_paging else value)
        return value

    def _entry(self, key: object, item: object, *, in_paging: bool) -> object:
        if isinstance(key, str) and key.lower() == TOKEN_KEY:
            return REDACTED
        return self._walk(item, in_paging=in_paging or key == PAGING_KEY)


def _without_credentials(text: str) -> str:
    """Drop credential parameters from a URL; leave anything that is not a URL alone."""
    parts = urlsplit(text)
    if not parts.scheme or not parts.query:
        return text
    kept = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if name.lower() not in PAGING_CREDENTIALS
    ]
    return parts._replace(query=urlencode(kept)).geturl()
