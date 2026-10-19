"""AWS Signature Version 4 query signing (presigned URLs), as R2's S3 API accepts it.

Only the `host` header is signed and the payload is `UNSIGNED-PAYLOAD`, so a URL works with
any client that sends the request as given, e.g. `curl -T file '<url>'` for an upload. Signing
is pure computation: nothing here touches the network.
"""

import hashlib
import hmac
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

ALGORITHM = "AWS4-HMAC-SHA256"
SERVICE = "s3"
UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"
MAX_EXPIRES_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class Credentials:
    """An S3 access key pair and the region it signs for (`auto` on R2)."""

    access_key_id: str
    secret_access_key: str = field(repr=False)
    region: str


@dataclass(frozen=True)
class S3Request:
    """One request to sign; `path` starts with "/" and is not yet percent-encoded."""

    method: str
    host: str
    path: str
    query: Mapping[str, str] = field(default_factory=dict)


def presign(
    request: S3Request, credentials: Credentials, now: datetime, expires_seconds: int
) -> str:
    """Return an https URL that performs `request` until `expires_seconds` after `now` (UTC)."""
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    scope = f"{amz_date[:8]}/{credentials.region}/{SERVICE}/aws4_request"
    params = {
        **request.query,
        "X-Amz-Algorithm": ALGORITHM,
        "X-Amz-Credential": f"{credentials.access_key_id}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires_seconds),
        "X-Amz-SignedHeaders": "host",
    }
    query = "&".join(f"{_encode(k)}={_encode(v)}" for k, v in sorted(params.items()))
    path = _encode(request.path, safe="/")
    canonical = "\n".join(
        [request.method, path, query, f"host:{request.host}\n", "host", UNSIGNED_PAYLOAD]
    )
    string_to_sign = "\n".join([ALGORITHM, amz_date, scope, _sha256(canonical)])
    key = _signing_key(credentials.secret_access_key, scope)
    signature = hmac.new(key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    return f"https://{request.host}{path}?{query}&X-Amz-Signature={signature}"


def _encode(value: str, safe: str = "") -> str:
    """Percent-encode everything but RFC 3986 unreserved characters (and `safe`)."""
    return quote(value, safe=safe)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _signing_key(secret: str, scope: str) -> bytes:
    key = f"AWS4{secret}".encode()
    for part in scope.split("/"):
        key = hmac.new(key, part.encode(), hashlib.sha256).digest()
    return key
