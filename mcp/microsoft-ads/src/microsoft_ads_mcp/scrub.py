"""Keeps the operator's credentials out of everything the model sees.

Every tool result and every error message has each credential literal replaced, wherever
it appears: the client secret, the developer token, the configured refresh token, and
every access and refresh token Microsoft has issued since the server started. The set is
read at the moment of scrubbing, so a token rotated a second ago is covered.
"""

from collections.abc import Callable, Iterable

REDACTED = "[redacted]"


class Scrubber:
    """Removes the current set of credential literals from values and text."""

    def __init__(self, secrets: Callable[[], Iterable[str]]) -> None:
        """Remember where to read the current secrets from."""
        self._secrets = secrets

    def text(self, text: str) -> str:
        """Return `text` with every credential literal replaced."""
        for literal in self._literals():
            text = text.replace(literal, REDACTED)
        return text

    def value(self, value: object) -> object:
        """Return a JSON-like value with every string, key or value, scrubbed."""
        if isinstance(value, dict):
            return {self.value(key): self.value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value

    def mapping(self, value: dict[str, object]) -> dict[str, object]:
        """Return a JSON object, keys and values scrubbed."""
        return {self.text(key): self.value(item) for key, item in value.items()}

    def _literals(self) -> list[str]:
        """Non-empty secrets, longest first so a secret containing another goes whole."""
        return sorted({secret for secret in self._secrets() if secret}, key=len, reverse=True)
