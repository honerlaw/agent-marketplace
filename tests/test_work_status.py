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
