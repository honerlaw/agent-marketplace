"""The MCP server: one tool to start an upload, one to list what is there."""

import mimetypes
import secrets
import shlex
from datetime import UTC, datetime, timedelta

import httpx2
from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from r2_uploads_mcp.bucket import Bucket, Clock, object_key, public_url
from r2_uploads_mcp.config import Settings

INSTRUCTIONS = """\
Temporary file hosting in a Cloudflare R2 bucket, for services that fetch a file by URL
(e.g. an ad platform's upload-by-URL endpoint). This server never receives file bytes:
1. Call r2_create_upload with the local file's path.
2. Run the returned upload_command in a shell on the machine that has the file.
   It exits non-zero if the upload failed.
3. Give the service that needs the file a link to it. download_url is a presigned GET: it
   expires at the time given and answers GET only (a HEAD request is refused). When the
   deployment configures a public hostname, results also carry public_url: an unsigned link
   that answers HEAD and GET until the bucket's own lifecycle rule deletes the object. Use
   public_url for a service that fetches later or checks the link with HEAD first.
r2_list_uploads shows what is in the bucket, each with a fresh download_url (and public_url).
The bucket deletes old objects on its own.
"""

JsonObject = dict[str, object]


def build_server(
    settings: Settings,
    transport: httpx2.AsyncBaseTransport | None = None,
    clock: Clock | None = None,
) -> MCPServer:
    """Create the server; `transport` and `clock` replace the network and time in tests."""
    server = MCPServer(name="r2-uploads", instructions=INSTRUCTIONS)
    bucket = Bucket(settings, transport)
    _add_tools(server, bucket, settings, clock or _utc_now)
    server.custom_route("/healthz", methods=["GET"])(healthz)
    return server


async def healthz(_request: Request) -> PlainTextResponse:
    """Unauthenticated liveness check for container orchestrators."""
    return PlainTextResponse("ok")


def upload_command(path: str, url: str) -> str:
    """Return a shell command that uploads the file at `path` to `url`."""
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return shlex.join(
        ["curl", "--fail", "--upload-file", path, "--header", f"Content-Type: {content_type}", url]
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _expires_at(now: datetime, seconds: int) -> str:
    return (now + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def _public(settings: Settings, key: str) -> JsonObject:
    """`{"public_url": …}` when the deployment configures a public hostname, else nothing."""
    if settings.public_base_url is None:
        return {}
    return {"public_url": public_url(settings.public_base_url, key)}


def _add_tools(server: MCPServer, bucket: Bucket, settings: Settings, clock: Clock) -> None:
    @server.tool()
    async def r2_create_upload(path: str) -> JsonObject:
        """Reserve a new object for a local file and return a presigned upload URL.

        `path` is the file's local path; only its base name is kept in the object key. Run
        `upload_command` in a shell where that path exists, then share a link: `download_url`
        (presigned GET, expires, refuses HEAD) or, when present, `public_url` (unsigned, answers
        HEAD and GET until the bucket deletes the object).
        """
        now = clock()
        key = object_key(path, now, secrets.token_hex(8))
        upload_url = bucket.url("PUT", key, now, settings.upload_expires_seconds)
        return {
            "key": key,
            "upload_url": upload_url,
            "upload_expires_at": _expires_at(now, settings.upload_expires_seconds),
            "upload_command": upload_command(path, upload_url),
            "download_url": bucket.url("GET", key, now, settings.download_expires_seconds),
            "download_expires_at": _expires_at(now, settings.download_expires_seconds),
            **_public(settings, key),
        }

    @server.tool()
    async def r2_list_uploads(prefix: str = "") -> JsonObject:
        """List objects in the bucket (up to 1,000), each with a fresh presigned download URL.

        Each object also carries `public_url` when the deployment configures a public hostname.

        `prefix` narrows the listing, e.g. "2026-10-19/" for one day's uploads.
        """
        now = clock()
        listing = await bucket.list_objects(prefix, now)
        expires = settings.download_expires_seconds
        objects = [
            {
                "key": item.key,
                "size_bytes": item.size_bytes,
                "last_modified": item.last_modified,
                "download_url": bucket.url("GET", item.key, now, expires),
                **_public(settings, item.key),
            }
            for item in listing.objects
        ]
        return {
            "objects": objects,
            "truncated": listing.truncated,
            "download_urls_expire_at": _expires_at(now, expires),
        }
