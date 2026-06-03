"""Span-confined editors for knowledge-entry files.

The two machine-managed mutations promote (and the Phase-B.3 fixer) are allowed to
make to an existing knowledge entry, plus the `body_complement` guard that proves
they touch nothing else. These were originally defined inline in
`tests/test_promote_invariant.py`; work unit 023 extracted them here so the
invariant guard AND the fixer (`scripts/knowledge_fix.py`) share one editor
implementation rather than re-deriving it (single-source rule, knowledge 019).

These editors operate on **entry** files only — the `## Related` block and the
supersession-banner span (knowledge 016). They know nothing about `index.md`; index
edits have their own skeleton-preserving logic in `scripts/knowledge_fix.py`.

The span constants live in `scripts/knowledge_spans.py`; these editors import them.
`conftest.py` puts `scripts/` on `sys.path`.
"""
from knowledge_spans import (
    BANNER_MARKER_RE,
    BANNER_QUOTE_RE,
    FENCE_RE,
    RELATED_HEADER,
    SECTION_RE,
)


def _fence_flags(lines):
    """Per-line flags: True when the line is inside a ``` fence (delimiters included).

    Fence-aware **header location** (knowledge 023): a fenced `## Related` example —
    e.g. the convention illustration in entry 015 — is body content, not structure.
    These flags are used ONLY to decide which lines count as real structure (the
    `## Related` header, the terminal-section assert, the banner marker). They are
    NEVER used to drop fenced lines from `body_complement`'s output — fenced content
    stays under the byte-identity guard (this is deliberately NOT a `_strip_fences`
    content filter).
    """
    flags = []
    in_fence = False
    for ln in lines:
        if FENCE_RE.match(ln):
            flags.append(True)  # delimiter lines are never body structure
            in_fence = not in_fence
        else:
            flags.append(in_fence)
    return flags


def add_related_link(text: str, target: str, relationship: str) -> str:
    """Ensure a ``- [[target]] — relationship`` line exists in the ``## Related``
    block. Insert-iff-absent, keyed on the target stem (set semantics). Idempotent.
    """
    line = f"- [[{target}]] — {relationship}"
    if _related_has_target(text, target):
        return text  # already linked -> byte-level no-op
    body = text.rstrip("\n")
    lines = text.splitlines()
    flags = _fence_flags(lines)
    # Only a NON-fenced header counts (a fenced `## Related` example is body content);
    # without this, an entry carrying only a fenced example would get a bare,
    # header-less line appended at EOF.
    if any(ln.strip() == RELATED_HEADER and not fenced for ln, fenced in zip(lines, flags)):
        # append under the existing (always-last) real Related section
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


def _related_has_target(text: str, target: str) -> bool:
    lines = text.splitlines()
    flags = _fence_flags(lines)
    in_related = False
    for ln, fenced in zip(lines, flags):
        # Only a NON-fenced header opens the Related span, and only NON-fenced lines
        # count as links — else a fenced `## Related` example (entry 015) makes prose
        # `[[…]]` mentions after it silently false-dedupe a genuinely-needed edge.
        if fenced:
            continue
        if ln.strip() == RELATED_HEADER:
            in_related = True
            continue
        if in_related and f"[[{target}]]" in ln:
            return True
    return False


def body_complement(text: str) -> str:
    """Return the entry with both machine-managed spans removed — the surface the
    never-overwrite invariant says promote (and the fixer) must never touch.
    """
    lines = text.splitlines()
    flags = _fence_flags(lines)
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        # Fenced lines are body CONTENT (e.g. entry 015's fenced `## Related`
        # convention example): never structure, never dropped — emit verbatim so they
        # stay under the byte-identity guard (knowledge 023: header LOCATION is
        # fence-aware; the complement is not a content filter).
        if flags[i]:
            out.append(ln)
            i += 1
            continue
        # drop the Related span: (real, non-fenced) header -> EOF, plus one preceding
        # blank line. Contract (spec of record): ``## Related`` is the terminal
        # section, so the span runs cleanly to EOF. Assert it on NON-fenced lines, so
        # a future entry that puts a body section *after* ``## Related`` can't make
        # the byte-identity check vacuous (a fenced `## ` example is not a section).
        if ln.strip() == RELATED_HEADER:
            assert not any(
                SECTION_RE.match(later) and not later_fenced
                for later, later_fenced in zip(lines[i + 1:], flags[i + 1:])
            ), "## Related must be the last section — the cross-ref span runs to EOF"
            if out and out[-1] == "":
                out.pop()
            break
        # drop the banner span: (real, non-fenced) marker + quote + one trailing blank
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
