"""Fetches report and bulk result files, which Microsoft serves from self-authorizing URLs.

No credential is ever sent here: the URL is the authorization. The host must be on the
operator's allowlist (safety.py), redirects are not followed, and both the download and
the decompressed text are capped.
"""

import gzip
import io
import zipfile
import zlib

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.safety import check_download_url

JsonObject = dict[str, object]
ZIP_MAGIC = b"PK\x03\x04"
GZIP_MAGIC = b"\x1f\x8b"
USER_AGENT = "microsoft-ads-mcp/0.1.0"


class Downloader:
    """Downloads one result file and returns it as text."""

    def __init__(self, settings: Settings, transport: httpx2.AsyncBaseTransport | None) -> None:
        """Create a client that carries no credentials and follows no redirects."""
        self._allowed = settings.download_hosts
        self._limit = settings.max_response_bytes
        self._client = httpx2.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=settings.timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    async def fetch(self, url: str) -> JsonObject:
        """Return the file's status, member name and text (zip and gzip are unpacked)."""
        check_download_url(url, self._allowed)
        try:
            async with self._client.stream("GET", url) as response:
                body = await self._read_bounded(response)
        except httpx2.HTTPError as error:
            message = f"downloading the file failed: {type(error).__name__}: {error}"
            raise ToolError(message) from error
        if response.status_code != httpx2.codes.OK:
            text = body.decode("utf-8", errors="replace")
            return {"status": response.status_code, "text": text}
        name, raw = self._unpack(body)
        return {"status": response.status_code, "file": name, "text": self._text(raw)}

    async def _read_bounded(self, response: httpx2.Response) -> bytes:
        chunks: list[bytes] = []
        size = 0
        async for chunk in response.aiter_bytes():
            size += len(chunk)
            if size > self._limit:
                raise self._too_large()
            chunks.append(chunk)
        return b"".join(chunks)

    def _unpack(self, body: bytes) -> tuple[str | None, bytes]:
        try:
            if body.startswith(ZIP_MAGIC):
                return self._unzip(body)
            if body.startswith(GZIP_MAGIC):
                with gzip.GzipFile(fileobj=io.BytesIO(body)) as packed:
                    return None, self._bounded(packed.read(self._limit + 1))
        except (zipfile.BadZipFile, OSError, EOFError, zlib.error) as error:
            message = f"the file could not be unpacked: {type(error).__name__}"
            raise ToolError(message) from error
        return None, body

    def _unzip(self, body: bytes) -> tuple[str, bytes]:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            members = archive.infolist()
            if len(members) != 1:
                message = f"expected a zip with one file, found {len(members)}"
                raise ToolError(message)
            with archive.open(members[0]) as member:
                return members[0].filename, self._bounded(member.read(self._limit + 1))

    def _bounded(self, raw: bytes) -> bytes:
        if len(raw) > self._limit:
            raise self._too_large()
        return raw

    def _text(self, raw: bytes) -> str:
        # utf-8-sig drops the byte-order mark Microsoft puts at the start of its CSVs.
        return raw.decode("utf-8-sig", errors="replace")

    def _too_large(self) -> ToolError:
        message = (
            f"the file is larger than {self._limit} bytes (MICROSOFT_ADS_MAX_RESPONSE_BYTES) "
            "once unpacked, so it was not returned. Ask for fewer columns, a shorter date "
            "range or a coarser aggregation."
        )
        return ToolError(message)
