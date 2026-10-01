"""Shared span definitions for the `.minerva/knowledge/` wiki format.

These constants are the single source of truth for the two machine-managed spans
of a knowledge entry — the supersession-banner span and the trailing ``## Related``
block — described in ``plugins/minerva/skills/promote/SKILL.md`` and recorded as the
spec of record in knowledge entry 016. Both the promote-invariant guard
(``tests/test_promote_invariant.py``) and the knowledge linter
(``scripts/knowledge_lint.py``) import from here so the span model is defined once
and cannot drift.

Alongside the constants, this module owns the one *fence-scan primitive*
(`unfenced` / `unfenced_lines`) that every "lines outside code fences" reader derives
from. The grammar was already single-sourced here; the loop around it was not, and four
independent copies of it had accumulated. See `unfenced`'s docstring for which readers
converged on it and — just as importantly — which deliberately did not.

Nothing edits these spans any more: entries are write-once, and back-links and
supersession are derived on read (`knowledge_catalog.py`). The banner grammar stays because
legacy entries still carry banners, and the catalog reads them.
"""
import re

# A supersession banner: a marker comment sitting above the first ``## `` header.
# Position+form anchored — never matched as a loose substring (entries may mention
# the literal string in prose).
# The marker names the superseding entry by FULL STEM. It used to carry the bare id,
# which could not say WHICH entry superseded this one whenever an id was shared — and
# under date ids, sharing is ordinary rather than a defect.
BANNER_MARKER_RE = re.compile(r"^<!-- superseded-by: ((?:\d{4}-\d{2}-\d{2}|\d{3,})-[a-z]+-[^ ]+) -->$")
BANNER_QUOTE_RE = re.compile(r"^> \*\*Superseded by ")

# The trailing, machine-managed cross-reference block. By convention it is the
# entry's terminal section (the span runs to EOF).
RELATED_HEADER = "## Related"

# Any second-level section header.
SECTION_RE = re.compile(r"^## ")

# A code-fence toggle line (``` or ~~~, optionally indented, with optional info string).
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def unfenced(lines):
    """Yield ``(index, line)`` for lines OUTSIDE code fences. Fence delimiters are
    dropped along with the fenced content.

    **The** fence-scan primitive. `FENCE_RE` above was already single-sourced, but the
    six-line toggle loop around it was not: four independent copies had accumulated —
    `knowledge_lint._strip_fences`, `work_status._nonfenced`, and one in each of
    `tests/test_skill_budget.py` and `tests/test_skill_contracts.py`. All four now
    derive from this.

    **Other `FENCE_RE` readers deliberately do NOT, and must not be "finished".**
    They look like the same loop and are not:

    - `knowledge_rename` *keeps* fence delimiters and fenced content in its output — it
      rewrites text rather than filtering it, so dropping lines would corrupt the file.
    - `tests/test_skill_dispatch._fence_of` measures the fence's run length for
      pairing, which the shared regex does not expose.

    That distinction is the point of
    `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`:
    unify the copies that are copies, and leave the ones that differ on purpose.
    """
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


def unfenced_lines(body: str) -> list:
    """Lines of ``body`` outside code fences, as a list. Convenience over `unfenced`."""
    return [line for _, line in unfenced(body.splitlines())]
