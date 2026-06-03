"""Guard for the narrowed never-overwrite invariant.

Work unit ``020-knowledge-wiki-navigability`` lets ``minerva:promote`` edit
*existing* knowledge entries to add bidirectional ``## Related`` cross-links and
supersession banners. To keep that safe, ``promote/SKILL.md`` narrows the
"knowledge files are never overwritten" invariant to: the **body** of an entry
(its ``# H1``/metadata block and the ``## Context`` / ``## Finding`` /
``## Implications`` sections) stays append-only and is never rewritten; the *only*
machine-managed mutable surfaces are the delimited ``## Related`` block and the
supersession-banner span.

minerva skills are prose executed by an LLM, not Python, so this is **not** a unit
test of a ``promote()`` function. It is the canonical *reference implementation* of
the two allowed mutations the skill describes, plus property tests proving the
invariant the skill must honor:

* the **complement** of the banner span and the ``## Related`` span is byte-identical
  before and after either mutation; and
* both mutations are idempotent (re-applying is a byte-level no-op), which is what
  makes a later Mode A full pass a no-op over a Mode-B-touched entry.

The SKILL.md prose mirrors these exact span definitions; if the two drift, this
file is the spec of record.
"""
# --- span editors (single source of truth: scripts/knowledge_edits.py) --------
# Originally defined inline here; work unit 023 moved them to scripts/knowledge_edits.py
# so the fixer (scripts/knowledge_fix.py) and this guard share one editor
# implementation (single-source rule, knowledge 019). This file remains the
# reference-implementation spec of record for promote's two allowed mutations
# (knowledge 016) — its property tests below exercise the moved editors. conftest.py
# puts scripts/ on sys.path.
from knowledge_edits import (  # noqa: E402
    add_related_link,
    add_supersede_banner,
    body_complement,
)


# --- fixture -----------------------------------------------------------------
ENTRY = """# A representative knowledge entry

**Date**: 2026-06-02
**Type**: decision
**Context**: .minerva/work/020-knowledge-wiki-navigability

## Context
The situation that led to this entry.

## Finding
What was decided.

## Implications
What it means going forward.
"""


# --- property tests ----------------------------------------------------------
def test_related_link_preserves_body():
    mutated = add_related_link(ENTRY, "010-constraint-minerva-skill-catalog-sync", "builds on")
    assert "## Related" in mutated
    assert body_complement(mutated) == body_complement(ENTRY)


def test_related_link_idempotent():
    once = add_related_link(ENTRY, "010-constraint-minerva-skill-catalog-sync", "builds on")
    twice = add_related_link(once, "010-constraint-minerva-skill-catalog-sync", "builds on")
    assert twice == once  # byte-level no-op on re-apply


def test_already_linked_pair_zero_diff():
    """Mode A over an already-linked pair must produce a zero-byte diff."""
    linked = add_related_link(ENTRY, "004-constraint-plugin-skills-auto-discovered-from-directory", "see also")
    assert add_related_link(linked, "004-constraint-plugin-skills-auto-discovered-from-directory", "see also") == linked


def test_banner_preserves_body():
    mutated = add_supersede_banner(ENTRY, "021", "021-decision-some-newer-call", "2026-07-01")
    assert "<!-- superseded-by: 021 -->" in mutated
    assert body_complement(mutated) == body_complement(ENTRY)


def test_banner_idempotent():
    once = add_supersede_banner(ENTRY, "021", "021-decision-some-newer-call", "2026-07-01")
    twice = add_supersede_banner(once, "021", "021-decision-some-newer-call", "2026-07-01")
    assert twice == once


def test_related_must_be_terminal_section():
    """body_complement is the span spec of record: a body section after
    ``## Related`` violates the contract and must be caught, not silently dropped.
    """
    import pytest
    malformed = ENTRY.rstrip("\n") + "\n\n## Related\n- [[001-decision-x]] — see also\n\n## Sneaky\nbody text\n"
    with pytest.raises(AssertionError):
        body_complement(malformed)


def test_banner_and_related_together_preserve_body():
    step1 = add_supersede_banner(ENTRY, "021", "021-decision-some-newer-call", "2026-07-01")
    step2 = add_related_link(step1, "021-decision-some-newer-call", "superseded by")
    assert body_complement(step2) == body_complement(ENTRY)
    # both spans present, body untouched
    assert "<!-- superseded-by: 021 -->" in step2 and "## Related" in step2
