"""Cut the test fixture from the pinned Meta API specs.

Run once, by hand, when the pin changes:

    python -m tests.cut_specs <directory written by `python -m meta_ads_mcp.spec_fetch`>

It keeps a few node types whole (the ones the tests and the README's worked sequence use,
plus `IntegrityAppeal`, whose operations have a `basePath`), only the enums they refer to,
and writes the fixture's own content hash beside it, which the tests pin instead of the
real one.
"""

import json
import re
import sys
from pathlib import Path

from meta_ads_mcp.spec_fetch import content_hash

KEPT_NODES = ("AdAccount", "Campaign", "AdsInsights", "IntegrityAppeal", "User")
ENUMS_FILE = "enum_types.json"
FIXTURE = Path(__file__).parent / "fixtures" / "specs"
HASH_FILE = Path(__file__).parent / "fixtures" / "specs.sha256"
TYPE_NAME = re.compile(r"[A-Za-z0-9_]+")


def cut(source: Path) -> dict[str, bytes]:
    """Return the fixture files cut from a directory of real spec files."""
    files = {f"{name}.json": (source / f"{name}.json").read_bytes() for name in KEPT_NODES}
    used = {word for content in files.values() for word in TYPE_NAME.findall(content.decode())}
    enums = json.loads((source / ENUMS_FILE).read_bytes())
    kept = [entry for entry in enums if entry["name"] in used]
    files[ENUMS_FILE] = json.dumps(kept, indent=1).encode()
    return files


def main() -> None:
    """Write the fixture and its hash."""
    files = cut(Path(sys.argv[1]))
    FIXTURE.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (FIXTURE / name).write_bytes(content)
    HASH_FILE.write_text(content_hash(files) + "\n")


if __name__ == "__main__":
    main()
