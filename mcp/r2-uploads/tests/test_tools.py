"""The tools, exercised end to end through an in-process MCP client."""

import re
import shlex
from urllib.parse import parse_qs, urlsplit

import httpx2
import pytest
from mcp import Client

from r2_uploads_mcp.bucket import Bucket, object_key, parse_listing, safe_filename
from r2_uploads_mcp.config import Settings
from r2_uploads_mcp.presign import Credentials, S3Request, presign
from r2_uploads_mcp.server import build_server
from tests.conftest import ENDPOINT, NOW, FakeR2, call, error_text

pytestmark = pytest.mark.anyio

KEY = re.compile(r"2026-10-19/[0-9a-f]{16}/brand-b\.mp4")
LISTING = b"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>ad-uploads</Name><IsTruncated>true</IsTruncated>
  <Contents><Key>2026-10-19/abc/brand-b.mp4</Key><Size>1048576</Size>
    <LastModified>2026-10-19T11:58:00.000Z</LastModified></Contents>
  <Contents><Key>2026-10-19/def/poster.png</Key><Size>2048</Size>
    <LastModified>2026-10-19T11:59:00.000Z</LastModified></Contents>
</ListBucketResult>"""


def query_of(url: str) -> dict[str, list[str]]:
    """Parse a URL's query string."""
    return parse_qs(urlsplit(url).query)


async def test_two_tools_are_listed(settings: Settings, fake: FakeR2) -> None:
    async with Client(build_server(settings, fake.transport)) as client:
        listed = await client.list_tools()
    assert {tool.name for tool in listed.tools} == {"r2_create_upload", "r2_list_uploads"}


async def test_create_upload_signs_a_put_and_a_get_for_one_new_key(
    settings: Settings, fake: FakeR2
) -> None:
    result = await call(settings, fake, "r2_create_upload", {"path": "/renders/brand-b.mp4"})
    assert not result.is_error
    upload = result.structured_content
    assert upload is not None
    assert KEY.fullmatch(str(upload["key"]))
    put, get = urlsplit(str(upload["upload_url"])), urlsplit(str(upload["download_url"]))
    assert (put.netloc, get.netloc) == (ENDPOINT, ENDPOINT)
    assert put.path == get.path == f"/ad-uploads/{upload['key']}"
    assert query_of(str(upload["upload_url"]))["X-Amz-Expires"] == ["900"]
    assert query_of(str(upload["download_url"]))["X-Amz-Expires"] == ["86400"]
    assert upload["upload_expires_at"] == "2026-10-19T12:15:00+00:00"
    assert upload["download_expires_at"] == "2026-10-20T12:00:00+00:00"
    assert fake.requests == []


async def test_the_upload_url_is_signed_for_put(settings: Settings, fake: FakeR2) -> None:
    result = await call(settings, fake, "r2_create_upload", {"path": "brand-b.mp4"})
    upload = result.structured_content
    assert upload is not None
    credentials = Credentials("test-key-id", "test-secret", "auto")
    request = S3Request("PUT", ENDPOINT, f"/ad-uploads/{upload['key']}")
    assert upload["upload_url"] == presign(request, credentials, NOW, 900)


async def test_upload_command_is_a_safe_curl_put(settings: Settings, fake: FakeR2) -> None:
    path = "/tmp/it's a video.mp4"  # noqa: S108 - a path under test, never opened
    result = await call(settings, fake, "r2_create_upload", {"path": path})
    upload = result.structured_content
    assert upload is not None
    argv = shlex.split(str(upload["upload_command"]))
    assert argv == [
        "curl",
        "--fail",
        "--upload-file",
        path,
        "--header",
        "Content-Type: video/mp4",
        str(upload["upload_url"]),
    ]
    assert str(upload["key"]).endswith("/it-s-a-video.mp4")


async def test_unknown_file_types_upload_as_octet_stream(settings: Settings, fake: FakeR2) -> None:
    result = await call(settings, fake, "r2_create_upload", {"path": "notes.unknownext"})
    upload = result.structured_content
    assert upload is not None
    assert "Content-Type: application/octet-stream" in str(upload["upload_command"])


async def test_list_uploads_returns_each_object_with_a_download_url(
    settings: Settings, fake: FakeR2
) -> None:
    fake.handler = lambda _request: httpx2.Response(200, content=LISTING)
    result = await call(settings, fake, "r2_list_uploads", {})
    listing = result.structured_content
    assert listing is not None
    objects = listing["objects"]
    assert isinstance(objects, list)
    assert [item["key"] for item in objects] == [
        "2026-10-19/abc/brand-b.mp4",
        "2026-10-19/def/poster.png",
    ]
    assert objects[0]["size_bytes"] == 1048576
    assert objects[0]["last_modified"] == "2026-10-19T11:58:00.000Z"
    assert urlsplit(objects[1]["download_url"]).path == "/ad-uploads/2026-10-19/def/poster.png"
    assert listing["truncated"] is True
    assert listing["download_urls_expire_at"] == "2026-10-20T12:00:00+00:00"


async def test_list_request_is_a_signed_list_objects_v2(settings: Settings, fake: FakeR2) -> None:
    await call(settings, fake, "r2_list_uploads", {"prefix": "2026-10-19/"})
    request = fake.last
    credentials = Credentials("test-key-id", "test-secret", "auto")
    query = {"list-type": "2", "prefix": "2026-10-19/"}
    expected = presign(S3Request("GET", ENDPOINT, "/ad-uploads", query), credentials, NOW, 60)
    assert request.method == "GET"
    assert str(request.url) == expected


async def test_an_empty_bucket_lists_nothing(settings: Settings, fake: FakeR2) -> None:
    result = await call(settings, fake, "r2_list_uploads", {})
    assert result.structured_content is not None
    assert result.structured_content["objects"] == []
    assert result.structured_content["truncated"] is False


async def test_r2_errors_name_the_code_and_message(settings: Settings, fake: FakeR2) -> None:
    body = b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>"
    fake.handler = lambda _request: httpx2.Response(403, content=body)
    result = await call(settings, fake, "r2_list_uploads", {})
    assert error_text(result).endswith(": R2 returned 403: AccessDenied: Access Denied")


async def test_non_xml_errors_come_back_as_text(settings: Settings, fake: FakeR2) -> None:
    fake.handler = lambda _request: httpx2.Response(502, text="bad gateway")
    result = await call(settings, fake, "r2_list_uploads", {})
    assert error_text(result).endswith(": R2 returned 502: bad gateway")


async def test_network_failures_are_tool_errors(settings: Settings, fake: FakeR2) -> None:
    def fail(request: httpx2.Request) -> httpx2.Response:
        msg = "refused"
        raise httpx2.ConnectError(msg, request=request)

    fake.handler = fail
    result = await call(settings, fake, "r2_list_uploads", {})
    assert "could not reach R2: ConnectError" in error_text(result)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/Users/me/renders/brand-b.mp4", "brand-b.mp4"),
        ("C:\\renders\\Brand B (final).mp4", "Brand-B-final-.mp4"),
        ("../../etc/passwd", "passwd"),
        ("$(rm -rf ~).mp4", "rm--rf-.mp4"),
        ("..", "upload"),
        ("", "upload"),
        ("a" * 300, "a" * 100),
    ],
)
async def test_safe_filename(path: str, expected: str) -> None:
    assert safe_filename(path) == expected


async def test_object_key_is_dated_and_tokened() -> None:
    assert object_key("x/brand-b.mp4", NOW, "abc") == "2026-10-19/abc/brand-b.mp4"


async def test_listing_without_a_namespace_or_fields_still_parses() -> None:
    listing = parse_listing(b"<ListBucketResult><Contents/></ListBucketResult>")
    assert [(o.key, o.size_bytes, o.last_modified) for o in listing.objects] == [("", 0, "")]
    assert listing.truncated is False


async def test_bucket_signs_any_method(settings: Settings) -> None:
    url = Bucket(settings).url("HEAD", "k", NOW, 5)
    assert url.startswith(f"https://{ENDPOINT}/ad-uploads/k?")
