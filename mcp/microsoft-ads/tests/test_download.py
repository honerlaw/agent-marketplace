"""Result-file downloads: the host allowlist, no credentials, unpacking and caps."""

import gzip
import io
import zipfile
from collections.abc import AsyncIterator, Callable
from dataclasses import replace

import httpx2
import pytest

from microsoft_ads_mcp.config import Settings
from microsoft_ads_mcp.safety import check_download_url
from tests.conftest import FakeMicrosoft, call, error_text, structured

pytestmark = pytest.mark.anyio

DOWNLOAD = "microsoft_ads_download_file"
BLOB = "https://bingadsstore.blob.core.windows.net/reports/r.zip?sig=abc&se=2026"
CSV = '\ufeff"Report Name: Campaigns"\nCampaignId,Clicks\n1,10\n'


def zipped(*members: tuple[str, bytes]) -> bytes:
    """Return a zip of `members`."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members:
            archive.writestr(name, data)
    return buffer.getvalue()


def patched(archive: bytes, flag: int = 0, method: int | None = None) -> bytes:
    """Set general-purpose `flag` bits and, optionally, the compression method in both headers."""
    data = bytearray(archive)
    for signature, at in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        start = data.index(signature) + at
        data[start] |= flag
        if method is not None:
            data[start + 2 : start + 4] = method.to_bytes(2, "little")
    return bytes(data)


def serving(body: bytes, status: int = 200) -> FakeMicrosoft:
    """Return a fake that answers every API-host request with `body`."""
    return FakeMicrosoft(api_handler=lambda _request: httpx2.Response(status, content=body))


@pytest.mark.parametrize(
    "url",
    [
        "http://bingadsstore.blob.core.windows.net/r.zip",
        "https://user:pw@bingadsstore.blob.core.windows.net/r.zip",
        "https://bingadsstore.blob.core.windows.net:8443/r.zip",
        "https://bingadsstore.blob.core.windows.net/r.zip#frag",
        "https://example.com/r.zip",
        "https://evilbingads.microsoft.com/r.zip",
        "https://x.blob.core.windows.net.evil.com/r.zip",
        "https://bingadsstore.blob.core.windows.net./r.zip",
        "https://[::1]/r.zip",
        "https:///r.zip",
        "/relative/r.zip",
        "https://ev\til.blob.core.windows.net/r.zip",
        "https://bingadsstore.blob.core.windows.net/r\n.zip",
        "https://bingadsstore.blob.core.windows.net/r .zip",
        "https://b\u00fccher.blob.core.windows.net/r.zip",
    ],
)
def test_urls_off_the_allowlist_are_refused(url: str) -> None:
    with pytest.raises(Exception, match="MICROSOFT_ADS_DOWNLOAD_HOSTS"):
        check_download_url(url, ("blob.core.windows.net", "bingads.microsoft.com"))


@pytest.mark.parametrize(
    "url",
    [
        BLOB,
        "https://bingads.microsoft.com/r.zip",
        "https://DOWNLOAD.API.BINGADS.MICROSOFT.COM/r.zip",
    ],
)
def test_allowlisted_domains_and_subdomains_pass(url: str) -> None:
    assert check_download_url(url, ("blob.core.windows.net", "bingads.microsoft.com")) == url


async def test_a_zipped_report_comes_back_as_text_without_credentials(
    settings: Settings,
) -> None:
    fake = serving(zipped(("report.csv", CSV.encode())))
    result = await call(settings, fake, DOWNLOAD, {"url": BLOB})
    assert structured(result) == {
        "status": 200,
        "file": "report.csv",
        "text": CSV.removeprefix("﻿"),
    }
    request = fake.last
    assert str(request.url) == BLOB
    assert "Authorization" not in request.headers
    assert "DeveloperToken" not in request.headers
    assert fake.token_requests == []


async def test_gzip_and_plain_files_are_read(settings: Settings) -> None:
    packed = await call(settings, serving(gzip.compress(b"a,b\n")), DOWNLOAD, {"url": BLOB})
    plain = await call(settings, serving(b"a,b\n"), DOWNLOAD, {"url": BLOB})
    assert structured(packed) == {"status": 200, "file": None, "text": "a,b\n"}
    assert structured(plain) == {"status": 200, "file": None, "text": "a,b\n"}


async def test_an_expired_link_returns_the_storage_error(settings: Settings) -> None:
    fake = serving(b"<Error><Code>AuthenticationFailed</Code></Error>", status=403)
    result = await call(settings, fake, DOWNLOAD, {"url": BLOB})
    assert structured(result)["status"] == 403
    assert "AuthenticationFailed" in str(structured(result)["text"])


async def test_redirects_are_not_followed(settings: Settings) -> None:
    redirect = httpx2.Response(302, headers={"Location": "https://example.com/x"})
    fake = FakeMicrosoft(api_handler=lambda _request: redirect)
    result = await call(settings, fake, DOWNLOAD, {"url": BLOB})
    assert structured(result)["status"] == 302
    assert len(fake.api_requests) == 1


async def test_a_zip_with_several_files_is_refused(settings: Settings) -> None:
    body = zipped(("a.csv", b"a"), ("b.csv", b"b"))
    result = await call(settings, serving(body), DOWNLOAD, {"url": BLOB})
    assert "one file, found 2" in error_text(result)


@pytest.mark.parametrize(
    "body",
    [
        zipped(("big.csv", b"x" * 5000)),
        gzip.compress(b"x" * 5000),
        b"x" * 5000,
    ],
)
async def test_over_cap_content_is_refused(settings: Settings, body: bytes) -> None:
    small = replace(settings, max_response_bytes=1000)
    result = await call(small, serving(body), DOWNLOAD, {"url": BLOB})
    assert "MICROSOFT_ADS_MAX_RESPONSE_BYTES" in error_text(result)


@pytest.mark.parametrize(
    "body",
    [
        b"PK\x03\x04broken",
        b"\x1f\x8bbroken",
        patched(zipped(("r.csv", b"x" * 100)), flag=1),  # encrypted
        patched(zipped(("r.csv", b"x" * 100)), method=99),  # an unsupported method
    ],
)
async def test_a_corrupt_archive_is_a_clear_error(settings: Settings, body: bytes) -> None:
    result = await call(settings, serving(body), DOWNLOAD, {"url": BLOB})
    assert "could not be unpacked" in error_text(result)


async def test_a_download_stops_reading_at_the_cap(settings: Settings) -> None:
    sent: list[int] = []

    async def endless() -> AsyncIterator[bytes]:
        for _ in range(1000):
            sent.append(1)
            yield b"x" * 500

    fake = FakeMicrosoft(api_handler=lambda _r: httpx2.Response(200, content=endless()))
    small = replace(settings, max_response_bytes=1000)
    result = await call(small, fake, DOWNLOAD, {"url": BLOB})
    assert "MICROSOFT_ADS_MAX_RESPONSE_BYTES" in error_text(result)
    assert len(sent) <= 3  # 3 chunks of 500 pass the 1000-byte cap


@pytest.mark.parametrize(
    ("body", "reader"),
    [
        (zipped(("big.csv", b"x" * 1_000_000)), zipfile.ZipExtFile),
        (gzip.compress(b"x" * 1_000_000), gzip.GzipFile),
    ],
)
async def test_an_archive_is_unpacked_only_up_to_the_cap(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
    reader: type[io.BufferedIOBase],
) -> None:
    sizes: list[int] = []
    original: Callable[..., bytes] = reader.read

    def spy(self: object, size: int = -1) -> bytes:
        sizes.append(size)
        return original(self, size)

    monkeypatch.setattr(reader, "read", spy)
    small = replace(settings, max_response_bytes=5000)  # the packed file fits; its content does not
    result = await call(small, serving(body), DOWNLOAD, {"url": BLOB})
    assert "MICROSOFT_ADS_MAX_RESPONSE_BYTES" in error_text(result)
    assert sizes == [5001]


async def test_a_failed_download_is_a_clear_error(settings: Settings) -> None:
    def refuse(request: httpx2.Request) -> httpx2.Response:
        message = "connection reset"
        raise httpx2.ReadError(message, request=request)

    result = await call(settings, FakeMicrosoft(api_handler=refuse), DOWNLOAD, {"url": BLOB})
    assert "downloading the file failed: ReadError" in error_text(result)


async def test_the_operator_can_widen_the_allowlist(settings: Settings) -> None:
    widened = replace(settings, download_hosts=("reports.example.net",))
    url = "https://cdn.reports.example.net/r.csv"
    result = await call(widened, serving(b"ok"), DOWNLOAD, {"url": url})
    assert structured(result)["text"] == "ok"
