"""Shared span definitions for the `.minerva/knowledge/` wiki format.

These constants are the single source of truth for the two machine-managed spans
of a knowledge entry — the supersession-banner span and the trailing ``## Related``
block — described in ``plugins/minerva/skills/promote/SKILL.md`` and recorded as the
spec of record in knowledge entry 016. Both the promote-invariant guard
(``tests/test_promote_invariant.py``) and the knowledge linter
(``scripts/knowledge_lint.py``) import from here so the span model is defined once
and cannot drift.

Only the *constants* live here. The span *editors* (add_related_link,
add_supersede_banner, body_complement) live in `scripts/knowledge_edits.py` (moved
there in work unit 023 so the fixer and the invariant guard share one
implementation); the read-only linter builds its own fence-aware parser on top of
these primitives and imports no editors.
"""
import re

# A supersession banner: a marker comment sitting above the first ``## `` header.
# Position+form anchored — never matched as a loose substring (entries may mention
# the literal string in prose).
BANNER_MARKER_RE = re.compile(r"^<!-- superseded-by: (\d{3,}) -->$")
BANNER_QUOTE_RE = re.compile(r"^> \*\*Superseded by ")

# The trailing, machine-managed cross-reference block. By convention it is the
# entry's terminal section (the span runs to EOF).
RELATED_HEADER = "## Related"

# Any second-level section header.
SECTION_RE = re.compile(r"^## ")

# A code-fence toggle line (``` or ~~~, optionally indented, with optional info string).
FENCE_RE = re.compile(r"^\s*(```|~~~)")
