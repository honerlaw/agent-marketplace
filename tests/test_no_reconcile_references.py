"""No live instruction may still describe the knowledge reconciliation removed in 3.0.

minerva 3.0 derives the knowledge catalog, backlinks and supersession on read, so
`minerva:cleanup` reconciles nothing, `minerva:synthesize` and `minerva:lint-fix` are gone,
and `index.md` / `overview.md` no longer exist. A skill that still tells an agent to read
the overview, refresh it, or reconcile the index would send it after a file that is not
there — or, worse, recreate one (`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`).

The allowlist is per file, and each entry says why the mention is legitimate: migration
docs that must name the legacy files to migrate them, and back-compat code that must still
read them. A new mention anywhere else fails here.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

SCANNED = [REPO / "plugins" / "minerva", REPO / "README.md", REPO / "pages",
           REPO / "CLAUDE.md", REPO / "AGENTS.md", REPO / ".minerva" / "reference"]

STALE_RE = re.compile(
    r"reconciliation|minerva/reconcile|reconciles?\s+the\s+knowledge|minerva:synthesize"
    r"|synthesis_status|overview\.md|index\.md|index-watermark|synthesis-watermark"
    r"|lint-fix|knowledge_fix|knowledge_edits", re.IGNORECASE)

# path (relative to the repo) -> why it may still mention the legacy machinery.
ALLOWED = {
    "plugins/minerva/COMPATIBILITY.md": "the 'Upgrading to 3.0' section names what was removed",
    "plugins/minerva/scripts/knowledge_fix.py": "the tombstone that tells a stale caller to migrate",
    "plugins/minerva/scripts/minerva_runtime.py":
        "still reads a 2.x checkpoint's legacy `reconciliation` phase, and requires the tombstone",
    "plugins/minerva/scripts/knowledge_backfill.py": "the migration that folds the legacy files in",
    "plugins/minerva/scripts/knowledge_catalog.py": "documents what it replaced and ignores legacy files",
    "plugins/minerva/scripts/knowledge_lint.py": "warns when a legacy aggregate is still present",
    "plugins/minerva/scripts/knowledge_rename.py":
        "retargets legacy index/overview/watermark lines when renaming a pre-3.0 corpus",
    "plugins/minerva/scripts/migration_status.py": "reports legacy aggregates and stale routing",
    "plugins/minerva/skills/migrate/SKILL.md": "reports the legacy aggregates a corpus still has",
    "plugins/minerva/skills/migrate-fix/SKILL.md": "runs the backfill that removes them",
    "plugins/minerva/skills/migrate-fix/references/upgrading.md": "the upgrade procedure",
    "plugins/minerva/skills/lint/SKILL.md": "documents the legacy-aggregate warning",
    "plugins/minerva/skills/init/references/steps.md":
        "tells init never to create the legacy files and how stale routing is detected",
    "plugins/minerva/skills/cleanup/SKILL.md":
        "states that cleanup no longer reconciles, and how to treat a 2.x checkpoint/branch",
    "plugins/minerva/skills/using-minerva/references/runtime.md":
        "a 2.x checkpoint's legacy `reconciliation` phase is still read",
}


def scanned_files():
    for root in SCANNED:
        if root.is_file():
            yield root
        elif root.is_dir():
            yield from (p for p in sorted(root.rglob("*"))
                        if p.is_file() and p.suffix in {".md", ".py", ".json"}
                        and "__pycache__" not in p.parts)


def test_no_unallowed_mention_of_removed_reconciliation():
    offenders = []
    for path in scanned_files():
        rel = str(path.relative_to(REPO))
        if rel in ALLOWED:
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if STALE_RE.search(line):
                offenders.append(f"{rel}:{n}: {line.strip()[:120]}")
    assert not offenders, (
        "These lines still describe the knowledge reconciliation removed in 3.0 (or the "
        "index.md/overview.md it maintained). Rewrite them for the derived catalog, or add "
        "the file to ALLOWED with the reason it must keep the mention:\n" + "\n".join(offenders))


@pytest.mark.parametrize("rel", sorted(ALLOWED))
def test_every_allowlisted_file_still_exists_and_still_mentions_it(rel):
    """A stale allowlist entry is a hole: a file deleted and recreated later would inherit an
    exemption it never earned."""
    path = REPO / rel
    assert path.is_file(), f"{rel} is allowlisted but does not exist"
    assert STALE_RE.search(path.read_text()), f"{rel} is allowlisted but no longer needs it"
