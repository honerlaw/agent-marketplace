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
import re
from pathlib import Path

import pytest

from tests.skills_corpus import AUTONOMOUS_ORCHESTRATORS as ORCHESTRATORS, PLUGIN_SKILLS, PLUGINS

by_plugin = pytest.mark.parametrize("plugin", PLUGINS)

# The predicate that re-derives phase progress, as each plugin's skills name it: minerva calls
# `work_status.phase_progress`, lorestrom its helper's `phases` command, which wraps it.
PROGRESS = {"minerva": "phase_progress", "lorestrom": "helper's `phases`"}


def _phasing(plugin):
    return PLUGIN_SKILLS[plugin] / "propose" / "references" / "phasing.md"


def _cleanup_gate(skill, plugin="minerva"):
    """The text of an orchestrator's Phase 7 (cleanup gate), located by its heading."""
    text = (PLUGIN_SKILLS[plugin] / skill / "references" / "phases.md").read_text()
    assert "## Phase 7" in text, f"{skill} has no Phase 7 section"
    return text[text.index("## Phase 7"):]


@by_plugin
@pytest.mark.parametrize("skill", ORCHESTRATORS)
def test_the_cleanup_gate_knows_a_phased_unit_is_not_finished(skill, plugin):
    """Every orchestrator must loop rather than exit while phases remain.

    Asserted on the required pointer to the loop rules, not on prose wording — the three
    orchestrators phrase their gates differently on purpose, and a wording assertion would either
    force them to converge or false-negative. A required reference has no variants.
    """
    gate = _cleanup_gate(skill, plugin)
    assert "phasing.md" in gate, (
        f"{skill}'s cleanup gate never reaches the phase-loop rules — a phased unit will ship "
        "its first phase and then report success while the rest never ship"
    )


@by_plugin
@pytest.mark.parametrize("skill", ORCHESTRATORS)
def test_the_cleanup_gate_names_the_loop_target(skill, plugin):
    """The pointer alone is not enough: the gate must say to go BACK to the ship phase.

    Without this, a reader who does not follow the pointer still exits. `phase_progress` is the
    predicate that decides, so requiring both names keeps the instruction actionable in place.
    """
    gate = _cleanup_gate(skill, plugin)
    assert PROGRESS[plugin] in gate, f"{skill}'s cleanup gate does not re-derive phase progress"
    assert "Phase 6" in gate, f"{skill}'s cleanup gate does not name the phase to loop back to"


@by_plugin
def test_the_loop_rules_live_in_exactly_one_place(plugin):
    """Single-sourced, like the deferral bar. Three orchestrators restating a loop protocol is
    the six-copies shape (`2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`)."""
    sentence = "loop back to the ship phase"
    skills = PLUGIN_SKILLS[plugin]
    holders = [
        p.relative_to(skills) for p in sorted(skills.rglob("*.md"))
        if sentence in p.read_text()
    ]
    assert holders == [_phasing(plugin).relative_to(skills)], (
        f"the loop protocol should live only in phasing.md, found in: {holders}"
    )


@by_plugin
def test_promote_mode_a_is_documented_as_waiting_for_the_final_phase(plugin):
    """The ordering rule that makes one-record-per-unit work: Mode A's output belongs in the last
    PR. Getting this wrong archives the scratchpad while later phases still need it.

    Asserted as a RELATION between the two modes, not as the presence of two substrings. The
    first version of this test checked only that "Mode B" and "final phase" both appeared
    somewhere in the file — which would have passed with the rule stated backwards ("Mode A runs
    every phase; Mode B is for the final phase"), because both phrases still occur. That is the
    presence-over-prose trap (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`), and
    it was caught by an independent reviewer rather than by the test.
    """
    body = " ".join(_phasing(plugin).read_text().split())      # normalise wrapping and emphasis spacing

    def _near(anchor, target, window=140):
        """True iff `target` appears within `window` chars after some `anchor` occurrence."""
        return any(
            re.search(target, body[m.end():m.end() + window], re.IGNORECASE)
            for m in re.finditer(anchor, body, re.IGNORECASE)
        )

    assert _near(r"Mode A", r"final phase"), (
        "phasing.md does not tie Mode A to the final phase"
    )
    # Mode B is the DURING-the-unit mechanism. If IT is the one bound to the final phase, the
    # ordering has been stated backwards — which the substring version of this test allowed.
    assert not _near(r"Mode B", r"only .{0,40}final phase"), (
        "phasing.md states the Mode A / Mode B ordering backwards"
    )
    assert re.search(r"\bMode B\b", body), "phasing.md never names the mid-unit mechanism"
