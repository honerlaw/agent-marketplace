"""Drift checks for the static site's skills catalog (``site/index.html``).

The site is a fourth skill-catalog surface (alongside the three from
``010-constraint-minerva-skill-catalog-sync``), deliberately enforced by this
bespoke bidirectional test instead of per-skill ``cross_surface`` contract
clauses: adding the site there would mean editing every ``contract.json``,
and this test is stronger anyway (it also catches orphaned entries).

Both directions scan only the region between two pinned markers, so skill
names mentioned elsewhere on the page (the flow narrative, the bias ledger)
can never mask a missing or orphaned catalog entry. Token matching reuses
``_present`` from ``test_skill_contracts`` — hyphen-aware boundaries, so
``minerva:propose`` is not satisfied by ``minerva:propose-ship``.
"""
import re
from pathlib import Path

from tests.test_skill_contracts import _present

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_HTML = REPO_ROOT / "site" / "index.html"
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

OPEN_MARKER = (
    "<!-- skills-catalog: source of truth is each skill's SKILL.md description "
    "frontmatter; when adding a skill, add an entry here — "
    "tests/test_site_catalog.py enforces presence -->"
)
CLOSE_MARKER = "<!-- end skills-catalog -->"

# Greedy, so a longer token like ``minerva:propose-ship-auto`` is consumed
# whole — consistent with ``_present``'s ``(?![\w-])`` boundary semantics.
TOKEN_RE = re.compile(r"minerva:[a-z0-9-]+")


def _catalog_section() -> str:
    """The delimited catalog region; fails loudly if either marker is gone."""
    html = SITE_HTML.read_text(encoding="utf-8")
    assert OPEN_MARKER in html, (
        f"opening marker missing from {SITE_HTML}; the catalog test cannot "
        f"locate its section. Expected exactly: {OPEN_MARKER!r}"
    )
    assert CLOSE_MARKER in html, (
        f"closing marker missing from {SITE_HTML}; expected exactly: "
        f"{CLOSE_MARKER!r}"
    )
    start = html.index(OPEN_MARKER) + len(OPEN_MARKER)
    end = html.index(CLOSE_MARKER)
    assert start < end, "catalog markers are out of order"
    return html[start:end]


def _skill_names() -> list[str]:
    return sorted(
        d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()
    )


def test_markers_present_and_ordered():
    assert _catalog_section().strip()


def test_every_skill_listed_on_site():
    section = _catalog_section()
    missing = [
        name for name in _skill_names()
        if not _present(f"minerva:{name}", section)
    ]
    assert not missing, (
        f"skills missing from the site catalog section: {missing} — add an "
        f"entry to site/index.html between the skills-catalog markers"
    )


def test_no_orphaned_site_entries():
    section = _catalog_section()
    known = set(_skill_names())
    listed = {tok.split(":", 1)[1] for tok in TOKEN_RE.findall(section)}
    orphans = sorted(listed - known)
    assert not orphans, (
        f"site catalog section names skills that no longer exist: {orphans} — "
        f"remove their entries from site/index.html"
    )


def test_extraction_agrees_with_present_boundaries():
    # Hyphens are token characters for both mechanisms: extraction must take
    # the longest token, and _present must refuse prefix matches.
    text = "see minerva:propose-ship-auto here"
    assert TOKEN_RE.findall(text) == ["minerva:propose-ship-auto"]
    assert _present("minerva:propose-ship-auto", text)
    assert not _present("minerva:propose", text)
    assert not _present("minerva:propose-ship", text)
