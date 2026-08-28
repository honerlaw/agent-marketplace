"""The orchestrated-mode contract.

A minerva skill that an autonomous orchestrator runs must have its user gates bypassed by an
**observable argument**, never by the skill judging for itself whether an orchestrator is calling.
That rule is `2026-06-07-decision-phase-handoff-rides-observable-intake`: *"'An inline argument was
passed' is observable; 'the prior phase converged' is an opinion."*

Before this contract existed the rule was prose, applied unevenly — `review`, `promote` and `ship`
carried a carve-out clause, `cleanup` used an observable `--yes`, and `work` and `replan` had
nothing at all. `work` governs the longest phase of every run, so an autonomous run reaching its
divergence trigger followed `work` -> `minerva:replan` -> `minerva:grill-plan` into a
one-question-at-a-time user interview.

Two halves, because either alone reads clean while the other rots:

* **Declaration** — each skill states its mode argument in a machine-readable form.
* **Coverage + use** — each orchestrator inventories the skills it runs, the inventory is checked
  against the corpus rather than hand-maintained, and every `Skill`-tool invocation carries the
  argument.

The coverage half is what keeps this from being a presence assertion
(`2026-08-10-pattern-presence-assertions-rot-into-green-lies`): a newly inlined gated skill fails
the suite until it is inventoried.
"""

import re
from pathlib import Path

import pytest

from tests.skills_corpus import (
    AUTONOMOUS_ORCHESTRATORS as AUTONOMOUS,
    SKILLS,
    phase_body,
    phases_text,
    slice_between,
)

# ``**Mode argument**: `--auto` `` — the skill's own declaration of how it is put into
# orchestrated mode. Read the declaration; never assume a spelling. `cleanup` declares
# `--yes`, and a test that assumed `--auto` would fail the one skill that already got this right.
MODE_DECL_RE = re.compile(r"^\*\*Mode argument\*\*:\s*`(--[a-z-]+)`\s*$", re.M)

# A row of an orchestrator's `## Delegated skills` table.
# `invoked` = run through the Skill tool. `inlined` = its own prose is executed from within a
# phase. `cited` = only a section is referenced for format, so no mode applies.
INVENTORY_ROW_RE = re.compile(
    r"^\|\s*`minerva:([a-z-]+)`\s*\|\s*(inlined|invoked|cited)\s*\|\s*([^|]*?)\s*\|", re.M
)
FLAG_RE = re.compile(r"`(--[a-z-]+)")
INVENTORY_HEADING = "## Delegated skills"

# Opening backtick + name, with NO closing-backtick requirement. An invocation is written
# ``Invoke `minerva:ship <date-slug> --auto=X` via the `Skill` tool``, so the skill name is not
# followed by a backtick — a regex demanding one silently matched nothing on the single line the
# use-half exists to check, and the test passed while the argument was absent. Found by deleting
# the argument and watching the suite stay green, which is the only way this class of blindness
# surfaces (`2026-08-11-pattern-a-gate-blind-to-what-it-checks`).
SKILL_MENTION_RE = re.compile(r"`minerva:([a-z-]+)")

# A line that runs another skill through the Skill tool. This is the ONLY mention shape that
# must carry the argument. A citation — "Same as `minerva:review`'s Diff resolution", "Mirrors
# `minerva:replan`" — names a section as the source of a format and must NOT be required to
# carry it; requiring it everywhere would force nonsense edits, and the predictable response is
# to weaken the check until it passes (`2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`).
INVOCATION_MARKER = "via the `Skill` tool"


def declared_mode_argument(skill: str) -> str | None:
    p = SKILLS / skill / "SKILL.md"
    if not p.is_file():
        return None
    m = MODE_DECL_RE.search(p.read_text())
    return m.group(1) if m else None


def inventory(orch: str) -> dict[str, tuple[str, str]]:
    """skill -> (how, flag) from the orchestrator's `## Delegated skills` table."""
    out = {}
    for m in INVENTORY_ROW_RE.finditer(phases_text(orch)):
        flag = FLAG_RE.search(m.group(3))
        out[m.group(1)] = (m.group(2), flag.group(1) if flag else None)
    return out


def phases_text_outside_inventory(orch: str) -> str:
    """Everything but the `## Delegated skills` table.

    The table lists each skill's mode argument, so a check that scans the whole file is satisfied
    by the table itself and can never fail — the table is the claim, not evidence for it. Found by
    a Verifier that blanked a phase body's mode mention and watched the suite stay green.
    """
    text = phases_text(orch)
    table = slice_between(text, INVENTORY_HEADING, "\n## ", f"{orch} delegated-skills table")
    return text.replace(table, "")


def invocation_lines(text: str) -> list[str]:
    return [l for l in text.splitlines() if INVOCATION_MARKER in l]


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_orchestrator_declares_a_delegated_skills_inventory(orch):
    inv = inventory(orch)
    assert inv, f"{orch}/references/phases.md has no `## Delegated skills` table"


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_every_inventoried_skill_declares_the_same_mode_argument(orch):
    """The orchestrator's claim and the skill's own declaration must agree.

    Two derivations of one fact plus a comment asserting they match will drift
    (`2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant`); this asserts it.
    """
    mismatches = []
    for skill, (_how, flag) in sorted(inventory(orch).items()):
        if flag is None:
            continue  # `cited` rows carry no mode
        declared = declared_mode_argument(skill)
        if declared != flag:
            mismatches.append(f"{skill}: orchestrator passes {flag}, skill declares {declared!r}")
    assert not mismatches, f"{orch} inventory disagrees with the skills:\n  " + "\n  ".join(mismatches)


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_inventory_covers_every_gated_skill_the_orchestrator_mentions(orch):
    """Ask the corpus which skills are in play, rather than trusting a hand-kept list.

    Any `minerva:<skill>` named in the phase protocols that declares a mode argument is a gated
    skill this orchestrator touches, and must appear in the inventory. Inlining a gated skill
    without inventorying it fails here — which is the whole point
    (`2026-08-11-pattern-the-enumeration-is-what-fails`: the assertion that holds asks the corpus).
    """
    text = phases_text(orch)
    inv = inventory(orch)
    missing = sorted(
        {
            s
            for s in SKILL_MENTION_RE.findall(text)
            if declared_mode_argument(s) is not None and s not in inv
        }
    )
    assert not missing, (
        f"{orch} mentions gated skill(s) absent from its `## Delegated skills` table: {missing}"
    )


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_every_skill_tool_invocation_carries_its_mode_argument(orch):
    """The use half: a skill run through the Skill tool must receive its argument on that line."""
    inv = inventory(orch)
    bad = []
    for line in invocation_lines(phases_text(orch)):
        for skill in SKILL_MENTION_RE.findall(line):
            how_flag = inv.get(skill)
            if how_flag is None or how_flag[0] != "invoked":
                continue
            if how_flag[1] not in line:
                bad.append(f"{skill} ({how_flag[1]} missing): {line.strip()[:110]}")
    assert not bad, f"{orch} invokes a skill without its mode argument:\n  " + "\n  ".join(bad)


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_inlined_skills_name_their_mode_argument_somewhere(orch):
    """An inlined skill's protocol is restated in the phases, so the mode must still be stated
    there — otherwise the orchestrator reads the skill's interactive gate text with nothing
    signalling otherwise, which is the original defect."""
    # Per skill, not per file: `--auto=<orch>` is the SAME string for every inlined skill, so a
    # bare "does it appear anywhere" check is satisfied for all three by any one of them. The
    # mention has to sit on the same line as the skill it applies to, or it is evidence for
    # nothing (`2026-08-11-pattern-a-gate-blind-to-what-it-checks`).
    lines = phases_text_outside_inventory(orch).splitlines()
    bad = [
        skill
        for skill, (how, flag) in sorted(inventory(orch).items())
        if how == "inlined"
        and not any(f"`minerva:{skill}`" in l and f"{flag}={orch}" in l for l in lines)
    ]
    assert not bad, f"{orch} inlines {bad} without naming its mode argument in the phase protocols"


def test_the_human_gated_orchestrator_passes_no_mode_argument():
    """`propose-ship`'s identity is a human decision at every phase transition. If it ever grows a
    mode argument, the ladder has collapsed and this contract is being applied where it must not be."""
    p = SKILLS / "propose-ship" / "references" / "phases.md"
    text = p.read_text()
    assert "--auto=" not in text, "propose-ship must not pass an orchestrated-mode argument"


def test_a_citation_is_not_treated_as_an_invocation():
    """The boundary, asserted in the green direction.

    Naming a skill to cite its format must not trip the invocation check. Without this, the
    natural fix for a false positive is to weaken the check until the suite passes.
    """
    citation = 'Append the entry to `replan.md` per `minerva:replan`\'s "On approval — file write".'
    assert INVOCATION_MARKER not in citation
    assert invocation_lines(citation) == []


# --- The ship -> Phase 7 hand-back: exactly one path, never both ---------------------
#
# `minerva:ship` ends its turn on the CI watch, so an orchestrator that delegated to it loses
# control flow. Ship therefore re-enters the orchestrator's cleanup gate itself via
# `--cleanup-only`. But the orchestrator's Phase 6 ALSO continues to Phase 7 when ship returns in
# the same turn. Both claims shipped unconditionally at first, which would run the cleanup gate
# twice — a second `minerva:cleanup` and potentially a second reconciliation PR.
#
# There is no code here to test; it is an instruction to a model. What IS testable is that the two
# halves stay mutually exclusive: a hand-back with no exclusion clause is the defect returning.

SHIP_PROTOCOL = SKILLS / "ship" / "references" / "protocol.md"


def hand_back_block() -> str:
    """Just the `--auto` hand-back block.

    Scoped deliberately: asserting against the whole file passes on words that happen to occur
    elsewhere in 22KB of prose, which is how the first version of this test read clean while the
    exclusion clause was deleted.
    """
    return slice_between(
        SHIP_PROTOCOL.read_text(),
        "**Under `--auto=<orchestrator>`",
        "\n## ",
        "ship hand-back block",
    )


def test_ship_hand_back_states_the_synchronous_exclusion():
    block = hand_back_block()
    assert "--cleanup-only" in block, "ship no longer documents the orchestrator hand-back"
    assert "--watch-iteration" in block, (
        "ship's hand-back must key off an observable fact (did this run resume from a wake-up), "
        "not a guess about whether the orchestrator is still live"
    )
    assert "twice" in block, (
        "ship documents the `--cleanup-only` hand-back without the synchronous-path exclusion — "
        "Phase 6 also continues to Phase 7, so both firing runs the cleanup gate twice"
    )


@pytest.mark.parametrize("orch", AUTONOMOUS)
def test_phase_six_states_that_exactly_one_path_runs(orch):
    body = phase_body(orch, "6")
    assert "same turn" in body and "never both" in body, (
        f"{orch} Phase 6 continues to Phase 7 without excluding ship's own `--cleanup-only` "
        "re-entry; on the wake-up path both would run the cleanup gate"
    )


# --- No self-judgment carve-out survives anywhere in the corpus ----------------------
#
# The inventory checks above derive their set from the orchestrators' phase protocols, so they
# see one hop. `minerva:synthesize` sat two hops out — an orchestrator invokes `minerva:cleanup
# --yes`, which invokes synthesize during reconciliation — and kept a prose carve-out reading
# "(When invoked by an autonomous orchestrator, its adjudication mechanism provides this
# confirmation.)" long after the one-hop skills were migrated. The suite reported full coverage
# the whole time, because its model of "a gated skill" was narrower than the corpus's
# (`2026-08-11-pattern-a-gate-blind-to-what-it-checks`).
#
# This check is hop-independent by construction: it asks the corpus for the *construction* the
# migration removed, rather than for a list of skills someone remembered to enumerate
# (`2026-08-11-pattern-the-enumeration-is-what-fails`).

SELF_JUDGMENT_RE = re.compile(
    r"[Ww]hen (?:an? |the )?invok(?:ed|ing)(?: by)? (?:an? )?(?:autonomous )?(?:orchestrator|skill)"
)


def all_skill_prose() -> list[tuple[Path, str]]:
    return [(p, p.read_text()) for p in sorted(SKILLS.rglob("*.md"))]


def test_no_skill_gates_on_a_judgment_about_its_caller():
    """A gate must be bypassed by an argument that was passed, never by the skill deciding for
    itself who is calling. "An inline argument was passed" is observable; "an orchestrator is
    calling me" is an opinion (`2026-06-07-decision-phase-handoff-rides-observable-intake`)."""
    offenders = []
    for path, text in all_skill_prose():
        for m in SELF_JUDGMENT_RE.finditer(text):
            line = text[: m.start()].count("\n") + 1
            offenders.append(f"{path.relative_to(SKILLS)}:{line}: {m.group(0)!r}")
    assert not offenders, (
        "skill prose gates on a judgment about the caller instead of an observable argument:\n  "
        + "\n  ".join(offenders)
    )


def test_every_skill_declaring_a_mode_argument_is_reachable_from_an_orchestrator():
    """Guards the check above from the opposite direction: a declaration nobody passes is dead
    prose, and would let a skill claim orchestrated support it never receives."""
    corpus = "\n".join(t for _p, t in all_skill_prose())
    unreachable = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        skill = path.parent.name
        flag = declared_mode_argument(skill)
        if flag is None:
            continue
        # The skill's OWN flag, not "either known flag". Accepting --auto or --yes for every
        # skill let a line naming minerva:synthesize alongside an unrelated --yes satisfy
        # synthesize, whose flag is --auto — the same assume-a-spelling defect this module
        # exists to prevent, caught by deleting the argument and watching the check stay green.
        passed = re.escape(flag) + ("=" if flag == "--auto" else r"\b")
        if not re.search(
            rf"`minerva:{re.escape(skill)}[` ][^\n]*{passed}"
            rf"|{passed}[^\n]*`minerva:{re.escape(skill)}`",
            corpus,
        ):
            unreachable.append(skill)
    assert not unreachable, (
        f"these skills declare a mode argument that nothing ever passes: {unreachable}"
    )
