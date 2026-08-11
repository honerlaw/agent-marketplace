#!/usr/bin/env python3
"""Read a work unit's lifecycle state from its own records, tolerantly.

`minerva:promote` archives a unit's scratchpad and replaces it with a one-line marker.
Its idempotency check then reads that marker to decide "already promoted, stop". The
check matched **one exact string** — the current spelling — and one 51-unit corpus
contains eight, across 16 of its units. So on a unit written by any older promote, the check fails open: the pass
re-runs and can duplicate `.minerva/knowledge/` entries.

This was reported in May 2026 (knowledge `2026-05-19-bug-promote-idempotency-check-misses-old-marker`),
which recommended "accept either marker string (preferred — forward-compatible)". That
was never applied, and the affected set grew from 3 units to 16 of 51 while the marker
kept being reworded. Enumerating spellings in prose is what failed; a predicate that
reads the declaration wherever and however it was written is the fix, mirroring how
`knowledge_lint.parse_entry` resolves an entry's type across three spellings plus two
fallbacks (knowledge `2026-08-09-pattern-read-authored-metadata-from-where-it-is`).

The eight shapes present in that corpus, all of which must read as promoted. Counting them
took three attempts, two of them wrong — one produced a spelling that exists NOWHERE, an
artifact of `head -1` over a file with no trailing newline splicing two units' markers into
one phantom line. Enumerating by eye is the thing that keeps failing here; the live-corpus
test is what actually holds:

    Summarized at minerva:promote on 2026-08-09 — see archive/.     (35 — canonical)
    Summarized at /promote on 2026-05-19 — see archive/.            (2 — pre-rename)
    promoted 2026-07-28 — durable knowledge in .minerva/knowledge/051; see archive/…
    promoted 2026-08-10 — durable knowledge in .minerva/knowledge/ (4 entries…)
    Promoted 2026-06-13. Scratchpad archived.
    promoted 2026-05-27
    <!-- post-promote -->
    ## Promote 2026-08-09          (a section appended to a still-live scratchpad)
    > **PROMOTED 2026-08-07** — durable item is knowledge 057; this file is the archived…

Writers should still emit the canonical form; this only governs READING.
"""
import re
from pathlib import Path

# The canonical marker new promotions write. Reading is tolerant; writing is not.
CANONICAL_MARKER = "Summarized at minerva:promote on {date} — see archive/."

# A line that DECLARES promote has run, in any spelling the corpus contains. Anchored at
# line start so a mid-sentence mention ("we promoted the finding") cannot trip it, and the
# `promoted`/`## Promote` arms additionally require a DATE right after the word — without
# that, ordinary prose OPENING a line ("Promoted entries are listed below") reads as a
# marker, and a false positive here makes promote skip real work silently.
_PROMOTED_LINE_RE = re.compile(
    r"""^\s*
        (?:>\s*)*                             # a blockquote-styled marker
        (?:\*\*)?                             # ...and/or a bold-wrapped one
        (?:
          summarized\s+at\s+\S*promote\b     # "Summarized at minerva:promote" / "at /promote"
        | promoted\b\D{0,4}\d{4}-\d{2}-\d{2}   # "promoted 2026-05-27", "Promoted 2026-06-13. …"
        | <!--\s*post-promote\s*-->           # a bare HTML marker
        | \#{1,6}\s*promote(?:d)?\b\D{0,4}\d{4}-\d{2}-\d{2}   # "## Promote <date>" section
    )""",
    re.IGNORECASE | re.VERBOSE)


def is_post_promote(text: str) -> bool:
    """True iff this scratchpad declares that `minerva:promote` has already run.

    Deliberately NOT "equals the canonical marker". The question the caller is really
    asking is "has promote run on this unit", and a unit answers that in whatever words
    the promote of its day used. A false negative here re-runs a mutating pass; a false
    positive only skips one, so the tolerant reading is also the safer failure direction.
    """
    return any(_PROMOTED_LINE_RE.match(line) for line in text.splitlines())


# The canonical Status field, used by 52 of 53 units. Written by `minerva:promote`.
_STATUS_FIELD_RE = re.compile(r"^\*\*Status\*\*:\s*(.+?)\s*$", re.M)
# A `## Status` heading — one unit predates the inline field. Matched with its section
# BOUNDARY, not "the next non-blank line": an empty `## Status` followed by
# `## Goal\nShipped code already exists…` would otherwise yield "Shipped code already
# exists…", classifying a live draft as done. That is a false negative on the one check
# that stops two agents colliding on a unit, so the parse stops at the next `#` line.
_STATUS_HEADING_RE = re.compile(r"^##\s+Status\s*$", re.M)


def read_status(proposal_text: str):
    """The unit's declared Status, from the inline field or an anchored `## Status`.

    Inline first: it is what `minerva:promote` writes and what 52 of 53 units carry, so
    the heading fallback can only ever fill a gap, never override the canonical field
    (the ordering rule from knowledge `2026-08-09-pattern-read-authored-metadata-from-where-it-is`).

    Deliberately narrower than `is_post_promote`'s tolerance. That marker has eight
    actively-recurring spellings and nothing preventing a ninth; `## Status` has exactly
    one instance and the prose that produced it has been corrected, so a permissive
    walker would exist forever to serve one frozen file while adding misread risk.
    """
    m = _STATUS_FIELD_RE.search(proposal_text)
    if m:
        return m.group(1)
    h = _STATUS_HEADING_RE.search(proposal_text)
    if not h:
        return None
    for line in proposal_text[h.end():].splitlines():
        if line.startswith("#"):
            return None          # section ended before any value: Status is absent
        if line.strip():
            return line.strip()  # the single value line inside the section
    return None


def unit_state(unit_dir) -> dict:
    """Classify one `.minerva/work/<date-slug>/` directory.

    Returns `{promoted, status, scratchpad_exists, archived, in_flight}`. `promoted` is
    true if the scratchpad declares it OR the scratchpad is gone but an `archive/`
    remains — the latter is a real shape in the corpus (a unit whose live scratchpad was
    removed rather than replaced), and it is unambiguously post-promote.

    **`in_flight` is a POLICY predicate, not raw state.** It is the orchestrators'
    pre-flight collision rule — `Status is Draft` **OR** not promoted — living here so
    four SKILL.md files stop restating it in prose. A skill wanting a different notion of
    "in progress" should fork it deliberately rather than quietly widen this one.

    The `OR` is what makes the rule safe across its own writer's non-atomic steps.
    `minerva:promote` rewrites Status and archives the scratchpad separately, so an
    interrupted run leaves one of two partial states — `Shipped` with an unarchived
    scratchpad, or `Draft` with a marker written. Each trips the opposite limb, so both
    read as in-flight: an extra confirmation, never silent adoption of half-promoted work.
    """
    d = Path(unit_dir)
    sp = d / "scratchpad.md"
    archived = (d / "archive").is_dir()
    text = sp.read_text() if sp.is_file() else None
    proposal = d / "proposal.md"
    status = read_status(proposal.read_text()) if proposal.is_file() else None
    promoted = is_post_promote(text) if text is not None else archived
    return {
        "promoted": promoted,
        "status": status,
        "scratchpad_exists": text is not None,
        "archived": archived,
        "in_flight": (status or "").startswith("Draft") or not promoted,
    }
