"""Tests for the tolerant post-promote marker reader (`scripts/work_status.py`).

The failure this exists to prevent: `minerva:promote`'s idempotency check matched ONE
exact marker string while the corpus contained at least eight spellings, so on 15 of 50
units it failed open — re-running a mutating pass that can duplicate knowledge entries.
Every spelling below was taken from a real unit, not invented — including the last,
which the live-corpus test below caught after the first eight had been enumerated.
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
    "promoted 2026-06-13<!-- post-promote -->",
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
