"""Keeps the configured secret key out of everything the model sees.

A reduced copy of `mcp/microsoft-ads`'s `Scrubber`: here there is one fixed literal,
the Clerk secret key the server was started with. Credentials Clerk returns by design
(sign-in tokens, API key secrets and the like) are not this server's to hide.
"""

REDACTED = "[redacted]"


class Scrubber:
    """Replaces the secret key wherever it appears in text or a JSON-like value."""

    def __init__(self, secret: str) -> None:
        """Remember the literal to remove."""
        self._secret = secret

    def text(self, text: str) -> str:
        """Return `text` with the secret replaced."""
        return text.replace(self._secret, REDACTED)

    def value(self, value: object) -> object:
        """Return a JSON-like value with every string, key or value, scrubbed."""
        if isinstance(value, dict):
            return {self.value(key): self.value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value
