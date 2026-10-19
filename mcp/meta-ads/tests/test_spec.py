"""Endpoint discovery: the catalog over the fixture, and fetching the pinned archive."""

import io
import json
import tarfile
from dataclasses import replace
from pathlib import Path

import anyio
import httpx2
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from meta_ads_mcp import spec_fetch
from meta_ads_mcp.config import Settings
from meta_ads_mcp.spec_catalog import SpecCatalog
from meta_ads_mcp.spec_fetch import (
    LICENSE_NAME,
    SPEC_URL,
    SpecArchive,
    content_hash,
    fetch_archive,
    read_archive,
    verified,
    write_specs,
)
from tests.conftest import FIXTURE_HASH, FIXTURE_SPECS, FakeGraph, call, error_text

ROOT = "facebook-business-sdk-codegen-abc"


def rows(value: object) -> dict[str, dict[str, object]]:
    """Index a described list of fields or params by name."""
    assert isinstance(value, list)
    return {str(row["name"]): row for row in value if isinstance(row, dict)}


def values(value: object) -> list[object]:
    """Return a described enum's values."""
    assert isinstance(value, list)
    return value


def fixture_files() -> dict[str, bytes]:
    """Return the fixture's spec files, as the catalog reads them."""
    return {path.name: path.read_bytes() for path in FIXTURE_SPECS.glob("*.json")}


def tarball(members: dict[str, bytes], extra: tuple[tarfile.TarInfo, ...] = ()) -> bytes:
    """Build a gzipped tarball of `members` (paths under ROOT) plus `extra` entries."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for info in extra:
            tar.addfile(info)
        for name, content in members.items():
            info = tarfile.TarInfo(f"{ROOT}/{name}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def archive_of(files: dict[str, bytes], license_text: bytes = b"License text") -> bytes:
    """Build an archive laid out like the codegen repository."""
    members = {f"api_specs/specs/{name}": content for name, content in files.items()}
    members[LICENSE_NAME] = license_text
    members["api_specs/specs/README.md"] = b"not a spec"
    members["api_specs/specs/deeper/Nested.json"] = b"{}"
    members["templates/Other.json"] = b"{}"
    return tarball(members)


@pytest.fixture
def catalog(settings: Settings) -> SpecCatalog:
    """Return a catalog over the fixture, pinned to the fixture's hash."""
    return SpecCatalog(settings, expected_hash=FIXTURE_HASH)


@pytest.mark.anyio
async def test_list_and_filter(catalog: SpecCatalog) -> None:
    every = await catalog.list_endpoints(None)
    assert "POST /{AdAccount}/campaigns → Campaign" in every
    assert "GET /{Campaign} → Campaign" in every
    assert "DELETE /{Campaign} → Object" in every
    assert any(line.startswith("GET /integrity/appeals/ads/eligibility") for line in every)
    filtered = await catalog.list_endpoints("ADSETS")
    assert filtered
    assert all("adsets" in line.lower() for line in filtered)


@pytest.mark.anyio
async def test_describe_endpoint_expands_enums(catalog: SpecCatalog) -> None:
    described = await catalog.describe_endpoint("post", "/{AdAccount}/campaigns")
    assert (described["method"], described["node"], described["returns"]) == (
        "POST",
        "AdAccount",
        "Campaign",
    )
    params = rows(described["params"])
    assert "OUTCOME_TRAFFIC" in values(params["objective"]["enum"])
    assert "enum" not in params["name"]
    assert len(json.dumps(described)) < 50_000


@pytest.mark.anyio
async def test_a_shared_template_returns_every_match(catalog: SpecCatalog) -> None:
    described = await catalog.describe_endpoint("GET", "/integrity/appeals/ads/eligibility")
    operations = described["operations"]
    assert isinstance(operations, list)
    assert len(operations) > 1


@pytest.mark.anyio
async def test_a_concrete_path_is_not_a_template(catalog: SpecCatalog) -> None:
    with pytest.raises(ToolError, match="exactly as meta_ads_list_endpoints"):
        await catalog.describe_endpoint("GET", "/act_1/campaigns")


@pytest.mark.anyio
async def test_describe_type(catalog: SpecCatalog) -> None:
    campaign = await catalog.describe_type("Campaign")
    fields = rows(campaign["fields"])
    assert "daily_budget" in fields
    assert "PAUSED" in values(fields["status"]["enum"])
    assert "POST /{Campaign} → Campaign" in values(campaign["endpoints"])
    insights = await catalog.describe_type("AdsInsights")
    assert "spend" in rows(insights["fields"])
    assert insights["endpoints"] == []
    assert len(json.dumps(insights)) < 50_000
    with pytest.raises(ToolError, match="no node type"):
        await catalog.describe_type("Nope")


@pytest.mark.anyio
async def test_an_oversized_output_is_refused(settings: Settings) -> None:
    small = SpecCatalog(replace(settings, max_response_bytes=500), expected_hash=FIXTURE_HASH)
    with pytest.raises(ToolError, match="narrow the filter"):
        await small.list_endpoints(None)


@pytest.mark.anyio
async def test_the_wrong_hash_is_refused(settings: Settings) -> None:
    with pytest.raises(ToolError, match="pinned content hash"):
        await SpecCatalog(settings, expected_hash="0" * 64).list_endpoints(None)


@pytest.mark.anyio
async def test_an_unreadable_directory_is_a_tool_error(settings: Settings, tmp_path: Path) -> None:
    missing = tmp_path / "file"
    missing.write_text("not a directory")
    catalog = SpecCatalog(replace(settings, spec_path=str(missing / "x")), expected_hash="")
    with pytest.raises(ToolError, match="pinned content hash"):
        await catalog.list_endpoints(None)
    blocked = tmp_path / "blocked"
    (blocked / "a.json").mkdir(parents=True)
    unreadable = SpecCatalog(replace(settings, spec_path=str(blocked)), expected_hash="")
    with pytest.raises(ToolError, match="could not read"):
        await unreadable.list_endpoints(None)


@pytest.mark.anyio
async def test_without_a_spec_path_the_archive_is_fetched_once(settings: Settings) -> None:
    archive = archive_of(fixture_files())
    requests: list[httpx2.Request] = []

    async def slow(request: httpx2.Request) -> httpx2.Response:
        # Yield while "downloading", so concurrent callers really overlap: a handler that
        # never yields would serialize them and pass without the lock.
        requests.append(request)
        await anyio.sleep(0.05)
        return httpx2.Response(200, content=archive)

    transport = httpx2.MockTransport(slow)
    catalog = SpecCatalog(replace(settings, spec_path=None), transport, FIXTURE_HASH)
    async with anyio.create_task_group() as group:
        for _ in range(3):
            group.start_soon(catalog.list_endpoints, "campaigns")
    assert len(requests) == 1
    assert str(requests[0].url) == SPEC_URL
    assert "authorization" not in requests[0].headers


@pytest.mark.anyio
async def test_a_failed_download_is_a_tool_error() -> None:
    fake = FakeGraph(lambda _request: httpx2.Response(404))
    with pytest.raises(ToolError, match="could not download"):
        await fetch_archive(fake.transport)


def test_read_archive_keeps_only_specs_and_the_license() -> None:
    files = {"Campaign.json": b"{}", "enum_types.json": b"[]"}
    special = tarfile.TarInfo(f"{ROOT}/api_specs/specs/Link.json")
    special.type = tarfile.SYMTYPE
    special.linkname = "/etc/passwd"
    archive = tarball(
        {
            **{f"api_specs/specs/{name}": content for name, content in files.items()},
            LICENSE_NAME: b"License",
        },
        extra=(special,),
    )
    read = read_archive(archive)
    assert read.files == files
    assert read.license_text == b"License"


def test_read_archive_caps_its_size(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(spec_fetch, "MAX_SPEC_BYTES", 10)
    with pytest.raises(ToolError, match="larger than 10 bytes"):
        read_archive(archive_of({"Big.json": b"x" * 20}))


@pytest.mark.parametrize("archive", [b"not a tarball", b"\x1f\x8b\x08\x00" + b"\xff" * 64])
def test_a_corrupt_archive_is_a_tool_error(archive: bytes) -> None:
    with pytest.raises(ToolError, match="could not be read"):
        read_archive(archive)


@pytest.mark.anyio
async def test_an_oversized_download_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(spec_fetch, "MAX_ARCHIVE_BYTES", 10)
    fake = FakeGraph(lambda _request: httpx2.Response(200, content=b"x" * 20))
    with pytest.raises(ToolError, match="larger than 10 bytes"):
        await fetch_archive(fake.transport)


def test_content_hash_and_verified() -> None:
    files = {"b.json": b"2", "a.json": b"1"}
    assert content_hash(files) == content_hash(dict(reversed(files.items())))
    assert verified(files, content_hash(files)) is files
    with pytest.raises(ToolError):
        verified(files, content_hash({"a.json": b"1"}))


def test_write_specs(tmp_path: Path) -> None:
    files = fixture_files()
    count = write_specs(SpecArchive(files, b"License"), tmp_path / "specs", FIXTURE_HASH)
    assert count == len(files)
    assert (tmp_path / "specs" / LICENSE_NAME).read_bytes() == b"License"
    assert (tmp_path / "specs" / "Campaign.json").read_bytes() == files["Campaign.json"]
    with pytest.raises(ToolError, match="no LICENSE"):
        write_specs(SpecArchive(files, b"  "), tmp_path / "other", FIXTURE_HASH)


def test_the_command_writes_the_specs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    files = fixture_files()

    async def fetched() -> SpecArchive:
        return SpecArchive(files, b"License")

    monkeypatch.setattr(spec_fetch, "fetch_archive", fetched)
    monkeypatch.setattr(spec_fetch, "SPEC_CONTENT_HASH", FIXTURE_HASH)
    spec_fetch.main([str(tmp_path)])
    assert f"wrote {len(files)} Meta API spec files" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="usage"):
        spec_fetch.main([])


@pytest.mark.anyio
async def test_discovery_tools_through_the_server(settings: Settings, fake: FakeGraph) -> None:
    listed = await call(settings, fake, "meta_ads_list_endpoints", {"text_filter": "/{Campaign}"})
    assert listed.structured_content is not None
    assert "GET /{Campaign} → Campaign" in listed.structured_content["result"]
    endpoint = {"method": "POST", "path": "/{AdAccount}/campaigns"}
    described = await call(settings, fake, "meta_ads_describe_endpoint", endpoint)
    assert not described.is_error
    missing = await call(settings, fake, "meta_ads_describe_type", {"name": "Nope"})
    assert "no node type" in error_text(missing)
    assert fake.requests == []
