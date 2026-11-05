"""Guards on the two values a caller can supply that reach the network.

API calls take no path, host or header from the caller at all: the operation name picks a
fixed method, host and path from the catalog (api.py). What is left is the per-call
customer and account ids, which become headers, and the result-file URL that
`download_file` fetches without credentials. Keep this module small: it is the security
boundary of the server.
"""

from urllib.parse import urlsplit

from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp.config import normalize_id


def check_id(name: str, value: str) -> str:
    """Return a customer or account id as bare digits, else raise ToolError."""
    normalized = normalize_id(value)
    if normalized is None:
        message = f"{name} must be digits, got {value!r}"
        raise ToolError(message)
    return normalized


def check_download_url(url: str, allowed: tuple[str, ...]) -> str:
    """Return `url` if it is an https URL on an allowlisted domain, else raise ToolError.

    The host must equal an allowed domain or end in "." plus one, so neither
    `evilbingads.microsoft.com` nor `x.blob.core.windows.net.evil.com` passes. The
    authority must be the bare host: no userinfo and no port. No fragment either.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    plain = parts.scheme == "https" and parts.netloc.lower() == host and not parts.fragment
    on_list = any(host == domain or host.endswith(f".{domain}") for domain in allowed)
    if not (host and plain and on_list):
        message = (
            f"url must be an https result-file URL on {list(allowed)} "
            f"(MICROSOFT_ADS_DOWNLOAD_HOSTS), got {url!r}"
        )
        raise ToolError(message)
    return url
