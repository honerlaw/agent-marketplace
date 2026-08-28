"""Tests for the tolerant post-promote marker reader (`scripts/work_status.py`).

The failure this exists to prevent: `minerva:promote`'s idempotency check matched ONE
exact marker string while the corpus contained at least eight spellings, so on 15 of 50
units it failed open — re-running a mutating pass that can duplicate knowledge entries.
Every spelling below is verified present in a real unit. An earlier draft of this list
carried a tenth entry, `promoted <date><!-- post-promote -->`, that exists nowhere: it was
an artifact of `head -1` over a file with no trailing newline, which concatenated two
units' markers into one phantom line. Enumerating by eye is exactly what keeps failing
here — `test_no_live_unit_is_misread_as_unpromoted` below is the assertion that actually
holds, because it asks the corpus instead of a human.
"""
import re
from pathlib import Path

import pytest

from work_status import CANONICAL_MARKER, is_post_promote, unit_state

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / ".minerva" / "work"

REAL_MARKERS = [
    "Summarized at minerva:promote on 2026-08-09 — see archive/.",
    "Summarized at /promote on 2026-05-19 — see archive/.",
    "promoted 2026-07-28 — durable knowledge in .minerva/knowledge/051; see archive/ for the working scratchpad.",
    "promoted 2026-08-10 — durable knowledge in .minerva/knowledge/ (4 entries dated 2026-08-10); see archive/ for the working scratchpad.",
    "Promoted 2026-06-13. Scratchpad archived.",
    "promoted 2026-05-27",
    "<!-- post-promote -->",
    "> **PROMOTED 2026-08-07** — durable item is knowledge 057; this file is the archived one.",
]


@pytest.mark.parametrize("marker", REAL_MARKERS)
def test_every_marker_spelling_in_the_corpus_reads_as_promoted(marker):
    assert is_post_promote(marker)


def test_an_appended_promote_section_reads_as_promoted():
    """Some units keep a live scratchpad and append `## Promote <date>` instead."""
    assert is_post_promote("# Scratchpad: x\n\n## Notes\nstuff\n\n## Promote 2026-08-09\nPromoted.\n")


def test_a_working_scratchpad_does_not_read_as_promoted():
    assert not is_post_promote("# Scratchpad: x\n\n## Quick decisions\n- [decided] a thing\n")


def test_a_passing_mention_of_promotion_does_not_trip_it():
    """Anchored at line start, so prose discussing promotion is not a marker."""
    assert not is_post_promote("# Scratchpad: x\n\nWe promoted the finding to knowledge later.\n")
    assert not is_post_promote("The plan is that promoted entries get catalogued.\n")


def test_canonical_marker_is_itself_recognized():
    assert is_post_promote(CANONICAL_MARKER.format(date="2026-08-11"))


def test_no_live_unit_is_misread_as_unpromoted():
    """Against the real corpus: every unit whose proposal says Shipped must read as
    promoted. A Shipped unit that reads unpromoted is one `minerva:promote` invocation
    away from duplicating its knowledge entries."""
    missed = []
    for d in sorted(WORK.iterdir()):
        if not d.is_dir():
            continue
        st = unit_state(d)
        if st["status"] and st["status"].startswith("Shipped") and not st["promoted"]:
            missed.append(d.name)
    assert missed == [], f"Shipped but reads unpromoted: {missed}"


@pytest.mark.parametrize("prose", [
    "Promoted entries are listed below in the index.",
    "Promoted knowledge items should never be edited directly.",
    "## Promoted work",
])
def test_prose_opening_with_promoted_is_not_a_marker(prose):
    """A false positive makes `minerva:promote` skip real work silently, so the
    `promoted` arm requires a date right after the word — every real marker has one."""
    assert not is_post_promote(prose)


# --- Status resolution: inline field first, `## Status` section as an anchored fallback ---
from work_status import read_status  # noqa: E402


def test_inline_status_field_is_read():
    assert read_status("# P\n\n**Status**: Shipped (2026-08-11)\n") == "Shipped (2026-08-11)"


def test_status_heading_is_read_when_there_is_no_inline_field():
    """One unit predates the inline field (`2026-05-21-sync-skill-catalogs`)."""
    assert read_status("# P\n\n## Status\nShipped (2026-05-21)\n\n## Goal\nx\n") \
        == "Shipped (2026-05-21)"


def test_inline_field_wins_over_a_heading():
    """The fallback may only fill a gap, never override the canonical field."""
    t = "# P\n\n**Status**: Draft\n\n## Status\nShipped (2026-01-01)\n"
    assert read_status(t) == "Draft"


def test_an_empty_status_section_does_not_leak_the_next_section():
    """The constructed false negative that a naive "next non-blank line" parse produces:
    an unfilled `## Status` followed by prose beginning "Shipped ..." would classify a
    LIVE DRAFT as done, and `in_flight` would stop protecting it."""
    t = "# P\n\n## Status\n\n## Goal\nShipped code already exists for the export path.\n"
    assert read_status(t) is None


def test_a_near_miss_heading_is_not_a_status_section():
    assert read_status("# P\n\n## Status quo\nShipped (2026-01-01)\n") is None
    assert read_status("# P\n\n### Status\nShipped (2026-01-01)\n") is None


def test_no_status_anywhere_reads_as_absent():
    assert read_status("# P\n\n## Goal\nbuild a thing\n") is None


# --- in_flight: the orchestrators' pre-flight predicate, single-sourced ---
def _unit(tmp_path, status_line, scratchpad):
    (tmp_path / "proposal.md").write_text(f"# P\n\n{status_line}\n")
    (tmp_path / "scratchpad.md").write_text(scratchpad)
    return unit_state(tmp_path)


def test_in_flight_true_while_draft_and_unpromoted(tmp_path):
    assert _unit(tmp_path, "**Status**: Draft", "# Scratchpad\n\nworking\n")["in_flight"]


def test_in_flight_false_once_shipped_and_promoted(tmp_path):
    st = _unit(tmp_path, "**Status**: Shipped (2026-08-11)",
               "Summarized at minerva:promote on 2026-08-11 — see archive/.\n")
    assert not st["in_flight"]


@pytest.mark.parametrize("status_line,scratchpad", [
    # promote rewrites Status and archives the scratchpad as SEPARATE steps, so an
    # interrupted run leaves one of these. Each trips the opposite limb of the OR.
    ("**Status**: Shipped (2026-08-11)", "# Scratchpad\n\nstill working\n"),
    ("**Status**: Draft", "Summarized at minerva:promote on 2026-08-11 — see archive/.\n"),
])
def test_both_partial_promote_states_read_as_in_flight(tmp_path, status_line, scratchpad):
    """The OR is why the predicate is safe across its own writer's non-atomic steps:
    a half-promoted unit is never silently adopted as finished."""
    assert _unit(tmp_path, status_line, scratchpad)["in_flight"]


def test_no_promoted_unit_in_the_live_corpus_reads_as_in_flight():
    """The invariant that catches the stale-record class, stated so it survives live work.

    A unit that is genuinely unfinished SHOULD read as in-flight — including whichever
    unit is being worked when this runs. What must never happen is a unit that has been
    promoted still tripping the collision check, which is what made the check noisy
    enough for `2026-07-29-right-size-lifecycle-waits` to log it weeks ago.
    """
    flagged = [d.name for d in sorted(WORK.iterdir())
               if d.is_dir() and unit_state(d)["promoted"] and unit_state(d)["in_flight"]]
    assert flagged == [], f"promoted units still reading as in-flight: {flagged}"


# --- fence-awareness: a fenced example is documentation, not a declaration ---
def test_a_fenced_status_field_does_not_shadow_the_real_one():
    """The dangerous direction. A convention doc or template showing
    `**Status**: Shipped` ahead of the unit's real `**Status**: Draft` would otherwise
    read a LIVE unit as finished, and `in_flight` would stop protecting it."""
    t = ("# P\n\n```\n**Status**: Shipped (2020-01-01)\n```\n\n**Status**: Draft\n")
    assert read_status(t) == "Draft"


def test_a_fenced_status_heading_is_not_a_status_section():
    t = "# P\n\n```\n## Status\nShipped (2020-01-01)\n```\n\n## Goal\nx\n"
    assert read_status(t) is None


def test_a_fenced_promote_marker_does_not_read_as_promoted():
    """Symmetric hole in the marker reader: every skill documenting the convention
    contains a fenced example of the marker."""
    t = ("# Scratchpad: x\n\nHere is what promote writes:\n\n```\n"
         "Summarized at minerva:promote on 2026-08-11 — see archive/.\n```\n\n"
         "## Notes\nstill working\n")
    assert not is_post_promote(t)


def test_a_real_marker_outside_a_fence_still_reads_as_promoted():
    t = ("# Scratchpad: x\n\n```\nexample: <!-- post-promote -->\n```\n\n"
         "Summarized at minerva:promote on 2026-08-11 — see archive/.\n")
    assert is_post_promote(t)


# --- Phases -------------------------------------------------------------------

from work_status import (  # noqa: E402
    phase_branch, phase_name, phase_numbering_gaps, phase_progress, read_phases,
)

SLUG = "2026-08-27-example-unit"

PHASED = """# Proposal: example

**Status**: Draft

## Phases

1. **First thing** — does the first thing.
   A continuation line that is not a phase.
2. **Second thing** — does the second thing.

## Open Questions

1. Not a phase — this list lives in another section.
"""


def test_an_unphased_proposal_declares_no_phases():
    assert read_phases("# Proposal: x\n\n## Goal\nDo a thing.\n") == []


def test_a_phased_proposal_reads_its_phases_in_order():
    assert [phase_name(t) for _, t in read_phases(PHASED)] == ["First thing", "Second thing"]


def test_a_wrapped_phase_description_is_kept_whole():
    """The continuation line belongs to the phase above, not to nobody.

    Reading only the first physical line truncated every non-trivial phase title
    mid-sentence — both phases of the unit that introduced this parser wrapped. Since
    `minerva:ship` must NAME outstanding phases in its report, the truncation reached a
    human as a sentence fragment.
    """
    first = read_phases(PHASED)[0][1]
    assert first.endswith("A continuation line that is not a phase.")
    assert "does the first thing." in first


def test_phase_name_prefers_the_authors_bolded_name():
    assert phase_name("**Plan-level phasing** — a long description that wraps on and on") \
        == "Plan-level phasing"


def test_phase_name_falls_back_when_the_convention_is_skipped():
    """Never return something unusable: a missing phase name in a report is the failure
    the report exists to prevent, so a clumsy name beats none."""
    assert phase_name("do the thing — with details") == "do the thing"
    assert phase_name("y" * 80).endswith("\u2026")


def test_an_indented_continuation_line_is_not_a_phase():
    """A wrapped phase description must not read as another phase — a miscount here
    produces a wrong branch name, and nothing downstream would notice."""
    assert len(read_phases(PHASED)) == 2


def test_the_section_ends_at_the_next_heading():
    """The numbered list under `## Open Questions` belongs to that section, not Phases."""
    assert all("Not a phase" not in t for _, t in read_phases(PHASED))


def test_an_empty_phases_section_yields_no_phases():
    assert read_phases("## Phases\n\n## Open Questions\n\n1. a\n2. b\n") == []


def test_a_fenced_phases_example_is_not_a_declaration():
    """Template and skill prose both SHOW `## Phases`; reading one as real would phase a
    unit that never asked to be phased."""
    fenced = "# Proposal: x\n\n```markdown\n## Phases\n\n1. Example phase\n```\n"
    assert read_phases(fenced) == []


def test_phase_one_keeps_the_bare_slug_branch():
    """The property that makes phasing inert for every existing consumer: a phased unit's
    first phase uses exactly the branch an unphased unit would."""
    assert phase_branch(SLUG, 1) == SLUG


def test_later_phases_get_a_suffixed_branch():
    assert phase_branch(SLUG, 2) == f"{SLUG}-phase-2"
    assert phase_branch(SLUG, 3) == f"{SLUG}-phase-3"


def test_phase_positions_are_one_based():
    with pytest.raises(ValueError):
        phase_branch(SLUG, 0)


def test_an_unphased_unit_has_no_phase_progress():
    state = phase_progress([], [], SLUG)
    assert state["phased"] is False and state["next_branch"] is None


def test_progress_starts_at_phase_one():
    state = phase_progress(read_phases(PHASED), [], SLUG)
    assert (state["next_position"], state["next_branch"]) == (1, SLUG)
    assert state["complete"] is False


def test_progress_advances_when_phase_one_merges():
    state = phase_progress(read_phases(PHASED), [SLUG], SLUG)
    assert (state["merged"], state["next_position"]) == (1, 2)
    assert state["next_branch"] == f"{SLUG}-phase-2"


def test_a_unit_is_complete_only_when_every_phase_merged():
    state = phase_progress(read_phases(PHASED), [SLUG, f"{SLUG}-phase-2"], SLUG)
    assert state["complete"] is True and state["next_position"] is None


THREE_PHASED = """# Proposal: example

## Phases

1. **First thing** — does the first thing.
2. **Second thing** — does the second thing,
   and its description wraps.
3. **Third thing** — does the third thing.

## Open Questions

1. Not a phase.
"""


def test_a_gap_resolves_to_the_earliest_unmerged_phase():
    """Phase 3 merged out of order must not report the unit as being on phase 4 — phases
    ship in order, so the earliest unmerged one is always next.

    Parsed from a real three-item `## Phases` section rather than a hand-built list. An
    earlier version of this test constructed the list literally, so the combination that
    actually runs in production — `read_phases` over real markdown feeding
    `phase_progress` — was never exercised end-to-end; each half was tested alone.
    """
    three = read_phases(THREE_PHASED)
    assert [n for n, _ in three] == [1, 2, 3]
    state = phase_progress(three, [SLUG, f"{SLUG}-phase-3"], SLUG)
    assert state["next_position"] == 2
    assert state["next_branch"] == f"{SLUG}-phase-2"
    assert state["complete"] is False


def test_mistyped_ordinals_are_reported_not_silently_normalised():
    """A duplicated `2.` renders fine in markdown and would point two phases at one
    branch. Position wins downstream; the disagreement still has to be visible."""
    assert phase_numbering_gaps([(1, "a"), (2, "b"), (2, "c")]) == [(3, 2)]
    assert phase_numbering_gaps([(1, "a"), (2, "b")]) == []


def test_only_units_that_actually_declare_phases_read_as_phased():
    """The inertness guarantee, asked of the corpus rather than enumerated by eye.

    Phasing is safe to add to every consumer at once ONLY because a unit that does not
    declare `## Phases` is untouched by it. Stated one-directionally — no heading implies
    no phases — because that IS the inertness claim. The converse does not hold and must
    not be asserted: an empty `## Phases` section legitimately yields nothing
    (`test_an_empty_phases_section_yields_no_phases`).

    Written against the corpus rather than as "no unit is phased", which was true only
    until this feature's own unit existed and would otherwise have needed a hardcoded
    exclusion list that rots with every phased unit added. Same reason
    `test_no_live_unit_is_misread_as_unpromoted` above asks the corpus instead of a
    human: 52 real proposals contain more prose shapes than anyone enumerates correctly,
    and a false positive here phases a unit that never asked to be.
    """
    proposals = sorted(WORK.glob("*/proposal.md"))
    assert proposals, "no work units found — the guarantee would be vacuous"
    heading = re.compile(r"^##\s+Phases\s*$", re.IGNORECASE)
    for p in proposals:
        text = p.read_text()
        if any(heading.match(line) for line in text.splitlines()):
            continue
        assert read_phases(text) == [], (
            f"{p.parent.name} declares no `## Phases` heading but read_phases found some")
