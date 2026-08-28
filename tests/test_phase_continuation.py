"""Every phase of an autonomous orchestrator must name the phase that follows it.

A phase whose protocol simply ends is a place the run stops. There is no error and no signal —
the model finishes the last numbered step, has nothing telling it what comes next, and yields to
the user. This is the shape `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption`
describes ("the next run will pick it up" is only true if something SCHEDULES a next run) and the
one `2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces` hit at the cleanup gate:
a run that stalls while reporting success.

It has recurred. `propose-ship-quick` and `propose-ship-balanced` shipped with Phase 2 — the
implementation phase, and the longest — ending at completion verification with no continuation,
while Phases 1, 3 and 4 all had one. Phases 5 and 6 named no successor in any of the three.

Scope is the three autonomous orchestrators. `minerva:propose-ship` is excluded deliberately: it
delegates wholesale rather than inlining phases 1-6 (its `phases.md` documents only the cleanup
gate), and a human drives each of its transitions, so a missing continuation cannot silently
strand a run. That exclusion is asserted below so it cannot quietly become a blind spot.
"""

import pytest

from tests.skills_corpus import (
    AUTONOMOUS_ORCHESTRATORS as AUTONOMOUS,
    PHASE_HEADER_RE,
    SKILLS,
    phase_sections,
)


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_the_orchestrator_documents_a_full_phase_sequence(orch):
    """Guards the check itself: if the headers stop matching, every test below passes vacuously."""
    labels = [l for l, _ in phase_sections(orch)]
    assert labels, f"{orch} exposes no `## Phase N` sections — the parser has gone blind"
    for expected in ["1", "2", "3", "4", "5", "6", "7"]:
        assert expected in labels, f"{orch} is missing `## Phase {expected}`"


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_every_integer_phase_names_its_successor(orch):
    sections = phase_sections(orch)
    labels = {l for l, _ in sections}
    missing = []
    for label, body in sections:
        if "." in label:
            continue  # conditional side-branches are checked below
        successor = str(int(label) + 1)
        if successor not in labels:
            continue  # terminal phase
        if f"Phase {successor}" not in body:
            missing.append(f"Phase {label} never names Phase {successor}")
    assert not missing, f"{orch} has a phase that stops instead of continuing:\n  " + "\n  ".join(missing)


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_conditional_phases_name_a_return_target(orch):
    """A side-branch such as Phase 2.5 must say where control goes back to."""
    bad = []
    for label, body in phase_sections(orch):
        if "." not in label:
            continue
        base = label.split(".")[0]
        if f"Phase {base}" not in body:
            bad.append(f"Phase {label} names no return target")
    assert not bad, f"{orch}:\n  " + "\n  ".join(bad)


def test_the_human_gated_orchestrator_is_out_of_scope_for_a_reason():
    """Asserted, not assumed: propose-ship really does document only the cleanup gate.

    If it ever grows the full inlined 1-7 sequence it becomes subject to this contract, and this
    test fails to say so rather than leaving it silently unchecked
    (`2026-08-11-pattern-a-gate-blind-to-what-it-checks`).
    """
    text = (SKILLS / "propose-ship" / "references" / "phases.md").read_text()
    labels = [m.group(1) for m in PHASE_HEADER_RE.finditer(text)]
    assert labels == ["7"], (
        f"propose-ship now documents phases {labels} — it inlines a phase sequence and must be "
        "added to AUTONOMOUS in this module"
    )
