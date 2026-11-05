"""Builds `catalog.json` from the pinned msads sdist: `microsoft-ads-build-catalog`.

`make catalog` downloads the sdist from PyPI and runs this. PyPI files never change once
uploaded, so the sdist's sha256 pins the exact bytes; a re-pin changes the three
constants below and regenerates the committed catalog, whose `source` records them.
"""

import argparse
import hashlib
import io
import json
import tarfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import TypedDict

from microsoft_ads_mcp.catalog_extract import (
    CatalogError,
    EnumType,
    ObjectType,
    Operation,
    documented_subtypes,
    extract_models,
    extract_operations,
)

PACKAGE = "msads"
VERSION = "13.0.30.1"
SDIST_SHA256 = "6d3c0fd82595750bd19d1ea4cb91f6bf31775f31b9cdcee75028428ba7ff801d"
SDIST_URL = (
    "https://files.pythonhosted.org/packages/6b/10/"
    "3cbbcb6ad545c5a06685dc97d2a4c6476c93e27bca6d747c35793149da82/msads-13.0.30.1.tar.gz"
)
CATALOG_FILE = "catalog.json"
LICENSE_FILE = "catalog.LICENSE"
API_MODULES = {
    "ad_insight_service_api.py": "AdInsight",
    "bulk_service_api.py": "Bulk",
    "campaign_management_service_api.py": "CampaignManagement",
    "customer_billing_service_api.py": "CustomerBilling",
    "customer_management_service_api.py": "CustomerManagement",
    "reporting_service_api.py": "Reporting",
}
MODEL_PACKAGES = {
    "adinsight": "AdInsight",
    "billing": "CustomerBilling",
    "bulk": "Bulk",
    "campaign": "CampaignManagement",
    "customer": "CustomerManagement",
    "reporting": "Reporting",
}


class Source(TypedDict):
    """Which sdist a catalog was built from."""

    package: str
    version: str
    sdist_sha256: str


class Catalog(TypedDict):
    """The whole catalog as written to `catalog.json`."""

    source: Source
    operations: dict[str, Operation]
    types: dict[str, dict[str, ObjectType]]
    enums: dict[str, dict[str, EnumType]]


def build(sdist: bytes, expected_sha256: str = SDIST_SHA256) -> tuple[Catalog, str]:
    """Return the catalog and the SDK licence text, refusing an sdist with another hash."""
    actual = hashlib.sha256(sdist).hexdigest()
    if actual != expected_sha256:
        message = f"sdist sha256 is {actual}, expected {expected_sha256}"
        raise CatalogError(message)
    members = _members(sdist)
    catalog: Catalog = {
        "source": {"package": PACKAGE, "version": VERSION, "sdist_sha256": actual},
        "operations": _operations(members),
        "types": {},
        "enums": {},
    }
    for service in sorted(set(MODEL_PACKAGES.values())):
        types, enums = _service_models(members, service)
        catalog["types"][service] = types
        catalog["enums"][service] = enums
    return catalog, _license(members)


def normalize(name: str) -> str:
    """Return the lookup key for an operation name: lower case, without `_`."""
    return name.replace("_", "").lower()


def _members(sdist: bytes) -> dict[PurePosixPath, str]:
    """Read every file below the sdist's top-level directory, keyed by its relative path."""
    with tarfile.open(fileobj=io.BytesIO(sdist), mode="r:gz") as archive:
        files = [member for member in archive.getmembers() if member.isfile()]
        return {
            PurePosixPath(*PurePosixPath(member.name).parts[1:]): _read(archive, member)
            for member in files
        }


def _read(archive: tarfile.TarFile, member: tarfile.TarInfo) -> str:
    # extractfile returns None only for non-files, which _members has already dropped.
    handle = archive.extractfile(member) or io.BytesIO()
    return handle.read().decode("utf-8")


def _operations(members: Mapping[PurePosixPath, str]) -> dict[str, Operation]:
    found: dict[str, Operation] = {}
    for module, service in API_MODULES.items():
        source = _member(members, PurePosixPath("openapi_client", "api", module))
        for operation in extract_operations(service, source):
            _add_operation(found, operation)
    return dict(sorted(found.items()))


def _add_operation(found: dict[str, Operation], operation: Operation) -> None:
    clash = [name for name in found if normalize(name) == normalize(operation["name"])]
    if clash:
        message = f"operation names collide once normalized: {clash[0]}, {operation['name']}"
        raise CatalogError(message)
    found[operation.pop("name")] = operation


def _service_models(
    members: Mapping[PurePosixPath, str], service: str
) -> tuple[dict[str, ObjectType], dict[str, EnumType]]:
    package = next(name for name, owner in MODEL_PACKAGES.items() if owner == service)
    folder = PurePosixPath("openapi_client", "models", package)
    types: dict[str, ObjectType] = {}
    enums: dict[str, EnumType] = {}
    for path in sorted(members):
        if path.parent == folder and path.suffix == ".py" and path.name != "__init__.py":
            module_types, module_enums = extract_models(members[path])
            types.update(module_types)
            enums.update(module_enums)
    for name, entry in types.items():
        if "discriminator" in entry:
            entry["subtypes"] = documented_subtypes(types, enums, name)
            del entry["discriminator"]
    return dict(sorted(types.items())), dict(sorted(enums.items()))


def _license(members: Mapping[PurePosixPath, str]) -> str:
    return _member(members, PurePosixPath("LICENSE"))


def _member(members: Mapping[PurePosixPath, str], path: PurePosixPath) -> str:
    if path not in members:
        message = f"the sdist has no {path}"
        raise CatalogError(message)
    return members[path]


def write(catalog: Catalog, license_text: str, directory: Path) -> None:
    """Write `catalog.json` (one entry per line, sorted) and the SDK licence beside it."""
    text = json.dumps(catalog, indent=1, sort_keys=True, ensure_ascii=False)
    (directory / CATALOG_FILE).write_text(f"{text}\n", encoding="utf-8")
    (directory / LICENSE_FILE).write_text(license_text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> None:
    """Build the catalog from a downloaded sdist into a directory."""
    parser = argparse.ArgumentParser(description="Build catalog.json from the msads sdist.")
    parser.add_argument("sdist", type=Path, help=f"the downloaded {PACKAGE}-{VERSION}.tar.gz")
    parser.add_argument("directory", type=Path, help="where to write the catalog")
    arguments = parser.parse_args(argv)
    catalog, license_text = build(arguments.sdist.read_bytes(), SDIST_SHA256)
    write(catalog, license_text, arguments.directory)
