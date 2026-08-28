"""Phasing is known at every surface that consumes it, not just where it is decided.

A phased work unit ships one PR per phase. Teaching the orchestrators about phases at the
**scope check** — where phases are decided — left their **cleanup gate** untouched, where phases
are executed. The result was silent: ship phase 1, poll, see MERGED, run cleanup (which correctly
defers teardown, being phase-aware), then report success and exit. Phases 2..N never shipped, and
the report said the run finished.

That is `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` — the next phase had
no trigger, and the report omitted what it skipped. It was caught by hand while running an
orchestrator against the very unit that introduced phasing.

The generalisation these tests encode: **a decider and an executor are different surfaces**, and
adding a concept to one says nothing about the other.
"""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "minerva" / "skills"
PHASING = SKILLS / "propose" / "references" / "phasing.md"

ORCHESTRATORS = ["propose-ship-quick", "propose-ship-balanced", "propose-ship-auto"]


def _cleanup_gate(skill):
    """The text of an orchestrator's Phase 7 (cleanup gate), located by its heading."""
    text = (SKILLS / skill / "references" / "phases.md").read_text()
    assert "## Phase 7" in text, f"{skill} has no Phase 7 section"
    return text[text.index("## Phase 7"):]


@pytest.mark.parametrize("skill", ORCHESTRATORS)
def test_the_cleanup_gate_knows_a_phased_unit_is_not_finished(skill):
    """Every orchestrator must loop rather than exit while phases remain.

    Asserted on the required pointer to the loop rules, not on prose wording — the three
    orchestrators phrase their gates differently on purpose, and a wording assertion would either
    force them to converge or false-negative. A required reference has no variants.
    """
    gate = _cleanup_gate(skill)
    assert "phasing.md" in gate, (
        f"{skill}'s cleanup gate never reaches the phase-loop rules — a phased unit will ship "
        "its first phase and then report success while the rest never ship"
    )


@pytest.mark.parametrize("skill", ORCHESTRATORS)
def test_the_cleanup_gate_names_the_loop_target(skill):
    """The pointer alone is not enough: the gate must say to go BACK to the ship phase.

    Without this, a reader who does not follow the pointer still exits. `phase_progress` is the
    predicate that decides, so requiring both names keeps the instruction actionable in place.
    """
    gate = _cleanup_gate(skill)
    assert "phase_progress" in gate, f"{skill}'s cleanup gate does not re-derive phase progress"
    assert "Phase 6" in gate, f"{skill}'s cleanup gate does not name the phase to loop back to"


def test_the_loop_rules_live_in_exactly_one_place():
    """Single-sourced, like the deferral bar. Three orchestrators restating a loop protocol is
    the six-copies shape (`2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`)."""
    sentence = "loop back to the ship phase"
    holders = [
        p.relative_to(SKILLS) for p in sorted(SKILLS.rglob("*.md"))
        if sentence in p.read_text()
    ]
    assert holders == [PHASING.relative_to(SKILLS)], (
        f"the loop protocol should live only in phasing.md, found in: {holders}"
    )


def test_promote_mode_a_is_documented_as_waiting_for_the_final_phase():
    """The ordering rule that makes one-record-per-unit work: Mode A's output belongs in the last
    PR. Getting this wrong archives the scratchpad while later phases still need it."""
    body = PHASING.read_text()
    assert "Mode B" in body and "final phase" in body
