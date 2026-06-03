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
import re

# --- span delimiters (must match promote/SKILL.md) ---------------------------
BANNER_MARKER_RE = re.compile(r"^<!-- superseded-by: (\d{3}) -->$")
BANNER_QUOTE_RE = re.compile(r"^> \*\*Superseded by ")
RELATED_HEADER = "## Related"
SECTION_RE = re.compile(r"^## ")


# --- the two allowed mutations -----------------------------------------------
def add_related_link(text: str, target: str, relationship: str) -> str:
    """Ensure a ``- [[target]] — relationship`` line exists in the ``## Related``
    block. Insert-iff-absent, keyed on the target stem (set semantics). Idempotent.
    """
    line = f"- [[{target}]] — {relationship}"
    if _related_has_target(text, target):
        return text  # already linked -> byte-level no-op
    body = text.rstrip("\n")
    if RELATED_HEADER in text.splitlines():
        # append under the existing (always-last) Related section
        return body + "\n" + line + "\n"
    # create the section at EOF
    return body + "\n\n" + RELATED_HEADER + "\n" + line + "\n"


def add_supersede_banner(text: str, nnn: str, target: str, date: str) -> str:
    """Insert a supersession banner between the metadata block and the first
    ``## `` header. Idempotent on the superseding NNN.

    Real knowledge entries always carry at least a ``## Context`` section, so the
    banner lands before it. The degenerate "entry with no ``## `` section at all"
    case (banner appended directly after metadata) is out of scope — the template
    guarantees the sections exist.
    """
    if any(BANNER_MARKER_RE.match(ln) and ln.endswith(f"{nnn} -->") for ln in text.splitlines()):
        return text  # banner for this NNN already present -> no-op
    lines = text.splitlines()
    insert_at = next((i for i, ln in enumerate(lines) if SECTION_RE.match(ln)), len(lines))
    banner = [
        f"<!-- superseded-by: {nnn} -->",
        f"> **Superseded by [[{target}]]** ({date})",
        "",
    ]
    new_lines = lines[:insert_at] + banner + lines[insert_at:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")


# --- helpers -----------------------------------------------------------------
def _related_has_target(text: str, target: str) -> bool:
    in_related = False
    for ln in text.splitlines():
        if ln.strip() == RELATED_HEADER:
            in_related = True
            continue
        if in_related and f"[[{target}]]" in ln:
            return True
    return False


def body_complement(text: str) -> str:
    """Return the entry with both machine-managed spans removed — the surface the
    invariant says promote must never touch.
    """
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        # drop the Related span: header -> EOF, plus one preceding blank line.
        # Contract (spec of record): ``## Related`` is the terminal section, so the
        # span runs cleanly to EOF. Assert it, so a future entry that puts a body
        # section *after* ``## Related`` can't make the byte-identity check vacuous.
        if ln.strip() == RELATED_HEADER:
            assert not any(SECTION_RE.match(later) for later in lines[i + 1:]), (
                "## Related must be the last section — the cross-ref span runs to EOF"
            )
            if out and out[-1] == "":
                out.pop()
            break
        # drop the banner span: marker + quote + one trailing blank
        if BANNER_MARKER_RE.match(ln):
            i += 1
            if i < len(lines) and BANNER_QUOTE_RE.match(lines[i]):
                i += 1
            if i < len(lines) and lines[i] == "":
                i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out).rstrip("\n")


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
