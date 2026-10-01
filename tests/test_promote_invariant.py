"""Guard for promote's add-only, write-once rule.

``minerva:promote`` writes new knowledge entry files and touches nothing else: no
catalog, no neighbour entry, no supersession banner. A branch's ``.minerva/`` footprint
is therefore purely additions, and concurrent PRs cannot conflict on it. Nothing is left
for a post-merge pass either, because every aggregate the wiki used to store — the
``index.md`` catalog, reciprocal ``## Related`` links, banners, ``overview.md`` — is now
derived on read by ``knowledge_catalog.py`` from the entries' own ``**Theme**`` /
``**Summary**`` lines and forward links.

minerva skills are prose executed by an LLM, so these guard the prose: a revert that
re-adds an aggregate write to promote would bring the conflicts back.
"""
from pathlib import Path

PROMOTE_DIR = Path(__file__).resolve().parent.parent / "plugins/minerva/skills/promote"


def _promote_prose() -> str:
    return "\n".join(p.read_text() for p in sorted(PROMOTE_DIR.rglob("*.md")))


def test_promote_prose_declares_itself_add_only():
    assert "add-only" in _promote_prose()


# The exact instructions promote carried before it became add-only. A keyword tripwire
# ("watermark bump") can't work here — the prose now says "no watermark bump", which is
# the same keyword meaning the opposite. These are the literal strings a revert would
# reintroduce. This catches a regression, not every possible novel rephrasing of one;
# the positive `add-only` assertion above is the other half of the guard.
LEGACY_AGGREGATE_INSTRUCTIONS = [
    "the `index.md` line(s) + watermark bump",
    "index line + watermark bump",
    "apply the approved `## Related` cross-links (bidirectional)",
    "Edit neighbor entries only within their `## Related` block",
]


def test_promote_prose_carries_no_legacy_aggregate_instruction():
    prose = _promote_prose()
    for banned in LEGACY_AGGREGATE_INSTRUCTIONS:
        assert banned not in prose, (
            f"promote prose instructs an aggregate/neighbor write ({banned!r}). Promote "
            f"must be add-only: entries are write-once, and the catalog, backlinks and "
            f"supersession are derived on read by knowledge_catalog.py. Restoring this "
            f"makes every concurrent pair of work units conflict again."
        )


def test_promote_prose_has_no_allocator():
    """The cross-branch allocator is gone, and promote must not still point at it.

    This assertion is deliberately INVERTED from the one it replaces. The old form was
    `assert "knowledge_next_nnn.py" in _promote_prose()` — a bare string-presence check,
    which would have stayed GREEN after the script was deleted while promote went on
    instructing a call to a file that no longer exists. A passing test attesting to a
    broken instruction is worse than no test, so the invariant now pins the absence.
    """
    prose = _promote_prose()
    assert "knowledge_next_nnn" not in prose


def test_promote_prose_names_the_date_id():
    """Absence alone would also pass if promote simply stopped saying how to name an
    entry. Pin the replacement too, so the pair brackets the real behaviour."""
    prose = _promote_prose()
    assert "date +%F" in prose


def test_entry_template_requires_theme_and_summary_fields():
    """The derived catalog groups entries by `**Theme**` and prints their `**Summary**`;
    an entry without them is invisible to orientation."""
    template = (PROMOTE_DIR / "references/wiki-maintenance.md").read_text()
    assert "**Summary**" in template and "**Theme**" in template
    assert "knowledge_catalog.py --themes" in template
