"""The bucket: object keys, presigned URLs, and the server's one network call (listing).

Callers never name a host or a bucket. Every URL is built here for the configured account's
R2 endpoint and the configured bucket, and a key or prefix is percent-encoded into it, so a
tool argument can't reach anything outside that bucket.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import quote
from xml.etree.ElementTree import Element

import httpx2
from defusedxml import ElementTree
from mcp.server.mcpserver.exceptions import ToolError

from r2_uploads_mcp.config import Settings
from r2_uploads_mcp.presign import Credentials, S3Request, presign

REGION = "auto"
LIST_URL_SECONDS = 60
MAX_FILENAME_CHARS = 100
UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

Clock = Callable[[], datetime]


def safe_filename(name: str) -> str:
    """Return the base name of a local path, reduced to characters safe in a URL and a shell."""
    base = PurePosixPath(name.replace("\\", "/")).name
    cleaned = UNSAFE_FILENAME_CHARS.sub("-", base).strip("-.")[:MAX_FILENAME_CHARS]
    return cleaned or "upload"


def object_key(filename: str, now: datetime, token: str) -> str:
    """Return `<date>/<token>/<filename>`: sorted by day, and never overwriting another upload."""
    return f"{now:%Y-%m-%d}/{token}/{safe_filename(filename)}"


def public_url(base_url: str, key: str) -> str:
    """Return the object's unsigned URL on the bucket's public hostname (`base_url`)."""
    return f"{base_url}/{quote(key, safe='/')}"


@dataclass(frozen=True)
class StoredObject:
    """One object in the bucket, as a listing describes it."""

    key: str
    size_bytes: int
    last_modified: str


@dataclass(frozen=True)
class Listing:
    """The objects one listing returned, and whether more were left out."""

    objects: list[StoredObject]
    truncated: bool


class Bucket:
    """Signs URLs for the configured bucket and lists its contents."""

    def __init__(
        self, settings: Settings, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Remember the bucket and key pair; `transport` is injectable for tests."""
        self._host = settings.endpoint_host
        self._bucket = settings.bucket
        self._credentials = Credentials(settings.access_key_id, settings.secret_access_key, REGION)
        self._client = httpx2.AsyncClient(timeout=settings.timeout_seconds, transport=transport)

    def url(self, method: str, key: str, now: datetime, expires_seconds: int) -> str:
        """Return a presigned URL for `method` on one object."""
        request = S3Request(method, self._host, f"/{self._bucket}/{key}")
        return presign(request, self._credentials, now, expires_seconds)

    async def list_objects(self, prefix: str, now: datetime) -> Listing:
        """List up to 1,000 objects whose keys start with `prefix`, oldest day first."""
        query = {"list-type": "2", "prefix": prefix}
        request = S3Request("GET", self._host, f"/{self._bucket}", query)
        url = presign(request, self._credentials, now, LIST_URL_SECONDS)
        try:
            response = await self._client.get(url)
        except httpx2.HTTPError as error:
            message = f"could not reach R2: {error!r}"
            raise ToolError(message) from error
        if response.is_error:
            message = f"R2 returned {response.status_code}: {_error_message(response)}"
            raise ToolError(message)
        return parse_listing(response.content)


def parse_listing(body: bytes) -> Listing:
    """Read a ListObjectsV2 response body."""
    root = ElementTree.fromstring(body)
    objects = [_stored_object(item) for item in root.findall("{*}Contents")]
    return Listing(objects, root.findtext("{*}IsTruncated") == "true")


def _stored_object(item: Element) -> StoredObject:
    return StoredObject(
        key=item.findtext("{*}Key", ""),
        size_bytes=int(item.findtext("{*}Size", "0")),
        last_modified=item.findtext("{*}LastModified", ""),
    )


def _error_message(response: httpx2.Response) -> str:
    try:
        root = ElementTree.fromstring(response.content)
    except ElementTree.ParseError:
        return response.text
    return f"{root.findtext('{*}Code')}: {root.findtext('{*}Message')}"
