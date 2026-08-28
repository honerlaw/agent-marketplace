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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_spans import unfenced  # noqa: E402


def _nonfenced(text: str):
    """Lines of `text` outside code fences.

    Both readers below scan for a declared value, and a fenced block is documentation
    SHOWING what that value looks like — a convention doc, a template, this module's own
    docstring. Reading one as the real declaration is the failure knowledge
    `2026-06-11-constraint-fence-scans-import-fence-re` exists to prevent, which is why
    the scan is imported rather than re-derived. The direction matters here: a fenced
    example `**Status**: Shipped` shadowing a real `**Status**: Draft` reads a LIVE unit
    as finished, which is the dangerous way for the in-flight check to be wrong.
    """
    for _, line in unfenced(text.splitlines()):
        yield line

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
    return any(_PROMOTED_LINE_RE.match(line) for line in _nonfenced(text))


# The canonical Status field, used by 52 of 53 units. Written by `minerva:promote`.
_STATUS_FIELD_RE = re.compile(r"^\*\*Status\*\*:\s*(.+?)\s*$")
# A `## Status` heading — one unit predates the inline field. Matched with its section
# BOUNDARY, not "the next non-blank line": an empty `## Status` followed by
# `## Goal\nShipped code already exists…` would otherwise yield "Shipped code already
# exists…", classifying a live draft as done. That is a false negative on the one check
# that stops two agents colliding on a unit, so the parse stops at the next `#` line.
_STATUS_HEADING_RE = re.compile(r"^##\s+Status\s*$")


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
    lines = list(_nonfenced(proposal_text))
    for line in lines:
        m = _STATUS_FIELD_RE.match(line)
        if m:
            return m.group(1)
    for i, line in enumerate(lines):
        if not _STATUS_HEADING_RE.match(line):
            continue
        for nxt in lines[i + 1:]:
            if nxt.startswith("#"):
                return None          # section ended before any value: Status is absent
            if nxt.strip():
                return nxt.strip()   # the single value line inside the section
        return None
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


# --- Phases ------------------------------------------------------------------
#
# A work unit that is too big for one PR declares an ordered `## Phases` section and
# ships as one PR per phase, keeping a SINGLE record — one proposal, one scratchpad, one
# promote. The alternative minerva used before this was to decompose into N work units,
# which multiplies every per-unit cost (proposal, worktree, review, promote, knowledge
# reconciliation) by N and was judged one-sidedly: the prose stated a cost of NOT
# splitting and none for splitting.
#
# **A unit with no `## Phases` section is unphased and nothing here applies to it.** That
# inertness is the property that made this safe to add to every consumer at once, the
# same argument `2026-08-09-decision-reference-is-a-fifth-entry-type` made for appending
# an empty index section.

_PHASES_HEADING_RE = re.compile(r"^##\s+Phases\s*$", re.IGNORECASE)
# A top-level ordered-list item inside that section. Anchored with NO leading whitespace
# so an indented continuation line under a phase cannot read as another phase — the same
# boundary discipline `_STATUS_HEADING_RE`'s reader uses, and for the same reason: a
# miscounted phase list produces a wrong branch name, which is silent.
_PHASE_ITEM_RE = re.compile(r"^(\d+)\.\s+(.*\S)\s*$")


def read_phases(proposal_text: str) -> list:
    """The unit's declared phases, in order, as `(written_ordinal, title)` pairs.

    Empty list for an unphased unit — the common case, and the one every existing unit
    is in. The scan is fence-aware via `_nonfenced` because the proposal TEMPLATE and
    this project's own skill prose both show fenced `## Phases` examples; reading one as
    a real declaration would phase a unit that never asked to be phased
    (`2026-06-11-constraint-fence-scans-import-fence-re`).

    The section ends at the next `#` line, not at the first blank — an empty `## Phases`
    followed by `## Open Questions` must yield no phases rather than swallowing the next
    section's bullets.
    """
    lines = list(_nonfenced(proposal_text))
    for i, line in enumerate(lines):
        if not _PHASES_HEADING_RE.match(line):
            continue
        phases = []
        for nxt in lines[i + 1:]:
            if nxt.startswith("#"):
                break
            m = _PHASE_ITEM_RE.match(nxt)
            if m:
                phases.append([int(m.group(1)), m.group(2)])
            elif phases and nxt.strip():
                # A CONTINUATION of the phase above, not a new phase. Any phase
                # description longer than one line wraps, and every non-trivial one does
                # — including both phases of the unit that introduced this parser. Taking
                # only the first physical line silently truncates the title mid-sentence,
                # and `minerva:ship` is required to NAME the outstanding phases in its
                # report, so the truncation surfaces to a human as a sentence fragment.
                phases[-1][1] += " " + nxt.strip()
        return [(n, t) for n, t in phases]
    return []


# The conventional `**Name** — description` opening of a phase item. The name is what a
# report shows; the description is context nobody wants in a one-line status.
_PHASE_NAME_RE = re.compile(r"^\*\*(.+?)\*\*")


def phase_name(title: str, limit: int = 60) -> str:
    """A phase's short name, for reports and branch-adjacent prose.

    Prefers the bolded prefix the template asks authors to write (`**Plan-level phasing**
    — …`), because that is the author's own name for the phase rather than a guess. Falls
    back to a truncated first clause when an author skipped the convention, so this never
    returns something unusable — a report that omits a pending phase is the failure this
    whole reporting path exists to prevent, and a clumsy name beats a missing one.
    """
    m = _PHASE_NAME_RE.match(title.strip())
    if m:
        return m.group(1).strip()
    head = title.strip().split(" — ")[0].split(". ")[0]
    return head if len(head) <= limit else head[:limit - 1].rstrip() + "…"


def phase_numbering_gaps(phases: list) -> list:
    """Written ordinals that disagree with position, as `(position, written)` pairs.

    Position is what everything downstream uses — a branch name is derived from where a
    phase SITS in the list, never from a hand-typed digit, because a duplicated `2.` in
    markdown renders fine and would silently point two phases at one branch. But a
    disagreement is still worth reporting rather than quietly normalising: the author
    typed something, and the concordance between the two is exactly what
    `2026-08-09-pattern-read-authored-metadata-from-where-it-is` says to MEASURE before
    trusting the derived value as a stand-in for the declared one.
    """
    return [(pos, written) for pos, (written, _) in enumerate(phases, start=1) if pos != written]


def phase_branch(date_slug: str, position: int) -> str:
    """The branch name for a phase, single-sourced.

    Phase 1 keeps the BARE `<date-slug>` branch that every unphased unit uses. That is
    not cosmetic: it leaves the worktree directory and the phase-1 branch matched, so all
    six `Target resolution` blocks, the duplicate-slug check, and `minerva:cleanup`'s
    merge detection keep working on a phased unit's first phase with no change at all.
    Only phases 2+ introduce a new name.

    Callers must not rebuild this string. Two derivations plus a comment asking them to
    agree is the shape `2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant`
    is about — `ship`, `cleanup` and the tests all resolve names through here.
    """
    if position < 1:
        raise ValueError(f"phase positions are 1-based, got {position}")
    return date_slug if position == 1 else f"{date_slug}-phase-{position}"


def phase_progress(phases: list, merged_branches, date_slug: str) -> dict:
    """Derive how far a phased unit has got, from which of its branches have merged.

    Deliberately takes the merged set as an ARGUMENT rather than shelling out to git.
    This module is a pure reader of declarations, which is what lets its tests run with
    no repo, no network and no fixtures; the caller (`minerva:ship`, `minerva:cleanup`)
    already has the `git branch --merged` / `gh pr list` result in hand.

    Derived, never written. A phased unit records its phases ONCE, in the proposal, and
    its progress is read off the merge history — there is no checkbox to update and
    therefore none to drift. The marker this module already exists to work around grew
    eight spellings and misread 16 of 51 units; a second hand-maintained progress marker
    would be the same bug with a new name
    (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).

    Returns `{phased, total, merged, next_position, next_branch, complete}`.
    `next_position` is the first phase whose branch has NOT merged, so a gap (phase 3
    merged while 2 is open) resolves to 2 — phases ship in order, and the earliest
    unmerged one is always what comes next.
    """
    merged = set(merged_branches)
    if not phases:
        return {"phased": False, "total": 0, "merged": 0, "next_position": None,
                "next_branch": None, "complete": False}
    done = [p for p in range(1, len(phases) + 1) if phase_branch(date_slug, p) in merged]
    pending = [p for p in range(1, len(phases) + 1) if phase_branch(date_slug, p) not in merged]
    nxt = pending[0] if pending else None
    return {
        "phased": True,
        "total": len(phases),
        "merged": len(done),
        "next_position": nxt,
        "next_branch": phase_branch(date_slug, nxt) if nxt else None,
        "complete": not pending,
    }
