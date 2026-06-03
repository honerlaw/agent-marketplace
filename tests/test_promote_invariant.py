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


# --- fence-aware header location (knowledge 023; bug found in unit 027) -------
# Entry 015 carries a FENCED ``## Related`` convention example as body content.
# Header LOCATION must be fence-aware; the complement must still EMIT fenced lines
# (they are body content under the byte-identity guard — not a content filter).
FENCED_ENTRY = """# A convention entry with a fenced ## Related example

**Date**: 2026-06-03
**Type**: constraint
**Context**: .minerva/work/027-related-backfill

## Context
The convention is illustrated with a fenced example:

```
## Related
- [[NNN-type-slug]] — <relationship>
```

## Finding
Prose may mention [[016-constraint-promote-narrowed-never-overwrite]] inline.

## Related
- [[023-constraint-wiki-edge-derivation-fence-aware]] — builds on
"""


def test_fenced_related_example_does_not_crash_body_complement():
    # Pre-fix: the fenced header tripped the terminal-section assert (real sections
    # follow the fenced line). The complement must keep the fenced example verbatim
    # and drop only the real terminal Related span.
    comp = body_complement(FENCED_ENTRY)
    assert "- [[NNN-type-slug]] — <relationship>" in comp  # fenced content preserved
    assert "023-constraint-wiki-edge-derivation-fence-aware" not in comp  # real span dropped
    # round-trip: adding a reciprocal preserves the complement byte-identically
    mutated = add_related_link(FENCED_ENTRY, "027-decision-x", "see also")
    assert body_complement(mutated) == comp


def test_fenced_header_does_not_false_dedupe():
    # Pre-fix: the fenced header flipped in_related, so the prose [[016...]] mention
    # after it silently no-op'd a genuinely-needed edge (the silent half of the bug).
    mutated = add_related_link(
        FENCED_ENTRY, "016-constraint-promote-narrowed-never-overwrite", "see also")
    assert mutated != FENCED_ENTRY, "prose mention after a fenced header must not dedupe"
    assert mutated.rstrip("\n").endswith(
        "- [[016-constraint-promote-narrowed-never-overwrite]] — see also")


def test_fenced_only_header_creates_real_block():
    # An entry whose ONLY ``## Related`` line is the fenced example has no real block:
    # add_related_link must create one at EOF, not append a bare header-less line.
    fenced_only = """# Entry with only a fenced example

**Date**: 2026-06-03
**Type**: constraint
**Context**: .minerva/work/x

## Context
Example:

```
## Related
- [[NNN-type-slug]] — <relationship>
```

## Finding
Standalone so far.
"""
    mutated = add_related_link(fenced_only, "001-decision-x", "see also")
    tail = mutated.rstrip("\n").splitlines()[-2:]
    assert tail == ["## Related", "- [[001-decision-x]] — see also"], tail
    assert body_complement(mutated) == body_complement(fenced_only)
