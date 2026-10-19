"""Meta's endpoint specs: fetched from the pinned codegen commit and checked by content hash.

Meta publishes no OpenAPI document. `facebook/facebook-business-sdk-codegen` keeps one JSON
file per Graph node type under `api_specs/specs/`, which is what the discovery tools read.
GitHub builds archives on demand, so their bytes are not stable; the extracted content is,
and `content_hash` is what is pinned. A re-pin changes `SPEC_COMMIT` and `SPEC_CONTENT_HASH`
together, here and nowhere else.

`meta-ads-fetch-specs <dir>` writes the verified files (and the codegen
LICENSE) to a directory; the Docker image is built that way, so it never fetches at run time.
"""

import hashlib
import io
import sys
import tarfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath

import httpx2
from mcp.server.mcpserver.exceptions import ToolError

SPEC_REPO = "facebook/facebook-business-sdk-codegen"
SPEC_COMMIT = "8420be6d5752c568a4f01dd608fa3cce6b2db960"
SPEC_CONTENT_HASH = "618ff17fe424d41c681e0a92ace962fac839413c0e9a837aedf601f78f0970f4"
SPEC_URL = f"https://codeload.github.com/{SPEC_REPO}/tar.gz/{SPEC_COMMIT}"
SPEC_DIRECTORY = ("api_specs", "specs")
MAX_SPEC_BYTES = 16 * 1024 * 1024
FETCH_TIMEOUT_SECONDS = 120
LICENSE_NAME = "LICENSE"
SpecFiles = dict[str, bytes]


class SpecArchive:
    """The spec files and the codegen LICENSE read from one archive."""

    def __init__(self, files: SpecFiles, license_text: bytes) -> None:
        """Hold already-extracted content."""
        self.files = files
        self.license_text = license_text


def content_hash(files: Mapping[str, bytes]) -> str:
    """Hash spec files as pinned: sha256 over `basename NUL bytes NUL`, basenames sorted."""
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8") + b"\0" + files[name] + b"\0")
    return digest.hexdigest()


def verified(files: SpecFiles, expected_hash: str) -> SpecFiles:
    """Return `files` if their content hash is `expected_hash`, else raise ToolError."""
    actual = content_hash(files)
    if actual != expected_hash:
        message = f"the Meta API specs do not match the pinned content hash (got {actual})"
        raise ToolError(message)
    return files


async def fetch_archive(transport: httpx2.AsyncBaseTransport | None = None) -> SpecArchive:
    """Download the pinned archive and read the specs from it, without any credential."""
    try:
        async with httpx2.AsyncClient(transport=transport, timeout=FETCH_TIMEOUT_SECONDS) as client:
            response = await client.get(SPEC_URL, follow_redirects=True)
            response.raise_for_status()
    except httpx2.HTTPError as error:
        message = f"could not download the Meta API specs from {SPEC_URL}: {error}"
        raise ToolError(message) from error
    return read_archive(response.content)


def read_archive(archive: bytes) -> SpecArchive:
    """Read `api_specs/specs/*.json` and the LICENSE from a gzipped tarball, in memory.

    Nothing is written to disk and member names are only matched, never used as paths.
    The total size read is capped, so a hostile archive cannot exhaust memory.
    """
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            return _collect(tar)
    except (tarfile.TarError, OSError, EOFError) as error:
        message = f"the Meta API spec archive could not be read: {error}"
        raise ToolError(message) from error


def write_specs(archive: SpecArchive, directory: Path, expected_hash: str) -> int:
    """Verify `archive` and write its files and LICENSE to `directory`; return the count."""
    files = verified(archive.files, expected_hash)
    if not archive.license_text.strip():
        message = "the Meta API spec archive has no LICENSE"
        raise ToolError(message)
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (directory / name).write_bytes(content)
    (directory / LICENSE_NAME).write_bytes(archive.license_text)
    return len(files)


def _collect(tar: tarfile.TarFile) -> SpecArchive:
    files: SpecFiles = {}
    license_text = b""
    budget = MAX_SPEC_BYTES
    for member in tar:
        kind = _member_kind(member)
        if kind is None:
            continue
        budget -= member.size
        if budget < 0:
            message = f"the Meta API specs are larger than {MAX_SPEC_BYTES} bytes"
            raise ToolError(message)
        content = _read_member(tar, member)
        if kind == LICENSE_NAME:
            license_text = content
        else:
            files[kind] = content
    return SpecArchive(files, license_text)


def _member_kind(member: tarfile.TarInfo) -> str | None:
    """Return the spec basename, LICENSE_NAME, or None for any member that is neither."""
    if not member.isfile():
        return None
    parts = PurePosixPath(member.name).parts
    if parts[1:] == (LICENSE_NAME,):
        return LICENSE_NAME
    in_specs = len(parts) == len(SPEC_DIRECTORY) + 2 and parts[1:-1] == SPEC_DIRECTORY
    return parts[-1] if in_specs and parts[-1].endswith(".json") else None


def _read_member(tar: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    # extractfile() returns None only for non-files, which _member_kind already skipped.
    return (tar.extractfile(member) or io.BytesIO()).read()


def main(argv: list[str] | None = None) -> None:
    """Write the verified specs to the directory named on the command line."""
    import anyio  # noqa: PLC0415 - only the command needs an event loop

    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        message = "usage: meta-ads-fetch-specs <directory>"
        raise SystemExit(message)
    archive = anyio.run(fetch_archive)
    count = write_specs(archive, Path(arguments[0]), SPEC_CONTENT_HASH)
    sys.stdout.write(f"wrote {count} Meta API spec files to {arguments[0]}\n")
