"""Execution-mode discipline for subagent dispatches in the minerva skills.

Work unit 047. The ``Agent`` tool runs subagents in the **background by
default**, returning only a handle rather than the agent's output. Every
minerva protocol that dispatches an agent needs that output *in the same turn*
— ``round-table`` counts votes then dispatches an Arbiter, ``propose-ship-
balanced`` arbitrates its reviewer's critique inline, ``review``'s local-diff
mode presents findings in the same turn. A backgrounded dispatch leaves the
next protocol step unexecutable, so the run ends the turn announcing that it is
waiting. Measured across 105 real orchestrator runs before this unit, 562 of
1047 dispatches were backgrounded and 95 runs parked at least once.

The instructions pinned ``subagent_type`` and ``model`` but not the execution
mode, so the model guessed per dispatch. This module makes the pin structural:
any skill prose that *instructs* a dispatch must also pin ``run_in_background``.

**The detector is conjunctive**, because neither single signal works on this
corpus:

* matching ``subagent`` alone false-positives on frontmatter descriptions and
  prose framing (``round-table``'s own description "Dispatches a 3-agent …
  panel of fresh-context subagents" instructs nothing);
* matching the literal ```Agent``` tool phrase alone misses
  ``propose-ship-balanced/references/phases.md``, which restates the dispatch
  parameters without naming the tool.

So a line counts as a dispatch instruction iff it carries **both** a dispatch
verb and a dispatch-parameter token. That combination selects exactly the five
real sites and excludes every near-miss — budget statements ("6 subagent
dispatches max"), delegation prose, and descriptions.

Detection is **line-based**: this corpus writes one paragraph or list item per
line (no hard wrapping), so a line is the natural instruction unit and gives
the tightest scope for the "must also pin the mode" check. Fenced regions are
stripped first, using the single-sourced ``FENCE_RE`` grammar rather than a
re-derived one (knowledge 023 / 037).

Like ``test_skill_contracts.py`` and ``test_skill_budget.py``, this module
enumerates the skill tree, so a newly added skill is covered automatically.
"""
import re
from pathlib import Path

import pytest

from knowledge_spans import FENCE_RE

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

# A dispatch verb: the imperative that actually spawns an agent. The list is
# deliberately wider than the phrasings currently in the corpus (which only use
# spawn/dispatch) — "launch" is the Agent tool's own canonical verb, so a future
# author is at least as likely to reach for it. Widening costs no precision
# here: a verb only matters when a dispatch-parameter token appears on the same
# line, and `test_detector_excludes_prose` guards that boundary.
DISPATCH_VERB_RE = re.compile(r"\b(spawn|dispatch|launch|invoke|create)", re.IGNORECASE)

# A dispatch-parameter token: evidence the line is configuring a real call
# rather than describing one. Any of the three is enough. The tool reference is
# tolerant of how the markdown happens to fall (``` `Agent` tool ```,
# ``` `Agent tool` ```, or unbackticked) — one site rests on this token alone,
# so a cosmetic reformat there must not drop it out of detection.
DISPATCH_TOKEN_RE = re.compile(
    r"`?Agent`?\s+tool`?|subagent_type|model:\s*\"?sonnet", re.IGNORECASE
)

# The pin this module exists to enforce.
EXECUTION_MODE_KEY = "run_in_background"

# The registered dispatch sites: skill-relative path -> number of dispatch
# instructions in it. Pinning the set (not just the pins) means a NEW dispatch
# site is a deliberate registration rather than a silent pass — the failure
# mode this unit is closing is precisely a site nobody noticed. Paths, not line
# numbers: line numbers churn whenever text is added above a site.
REGISTERED_SITES = {
    "propose-ship-balanced/SKILL.md": 1,
    "propose-ship-balanced/references/phases.md": 1,
    # 2: the Skeptic/Verifier review, and the fold-audit re-check after a fold.
    "propose-ship-balanced/references/verify-protocol.md": 2,
    "review/references/protocol.md": 1,
    "round-table/SKILL.md": 1,
}

# Prose that must NOT be detected, as (skill-relative path, distinctive
# substring). Guards the detector's precision: loosening it to a bare
# `subagent` match reds these.
PROSE_NEAR_MISSES = [
    ("round-table/SKILL.md", "Dispatches a 3-agent Proponent/Skeptic/Arbiter panel"),
    ("propose-ship-auto/SKILL.md", "6 subagent dispatches max"),
    ("propose-ship-balanced/references/governance.md", "Each reviewer gate dispatches"),
]


def _fence_delimiter(line: str) -> tuple[str, int] | None:
    """The (character, run-length) of the fence on ``line``, or None.

    ``FENCE_RE`` stays the single source of truth for *whether* a line is a
    fence (knowledge 019 / 023 / 037 — import the grammar, never re-derive it);
    the run length is measured here because pairing needs it and the shared
    regex does not expose it. This is the sanctioned "parser built on it" form.
    """
    match = FENCE_RE.match(line)
    if match is None:
        return None
    char = match.group(1)[0]
    stripped = line.strip()
    return char, len(stripped) - len(stripped.lstrip(char))


def _scan(body: str) -> tuple[list[tuple[int, str]], bool]:
    """``(lines outside fences, ends-inside-a-fence)``.

    Fences are **paired** rather than toggled: a fence closes only on the same
    character at the same-or-greater run length, so a ``~~~`` line inside a
    ```` ``` ```` block is literal content, not a close. A bare toggle gets that
    wrong, and the failure is silent in the direction that matters here —
    content wrongly treated as fenced is content this module never inspects.

    Both results come from one walk because they are the same walk; computing
    them separately is how the two drift apart.
    """
    out: list[tuple[int, str]] = []
    open_delim: tuple[str, int] | None = None
    for lineno, line in enumerate(body.splitlines(), 1):
        delim = _fence_delimiter(line)
        if delim is not None:
            if open_delim is None:
                open_delim = delim
                continue
            if delim[0] == open_delim[0] and delim[1] >= open_delim[1]:
                open_delim = None
                continue
        if open_delim is None:
            out.append((lineno, line))
    return out, open_delim is not None


def _unfenced_lines(body: str) -> list[tuple[int, str]]:
    """1-indexed lines outside fenced code blocks.

    A fenced example is an illustration, not an instruction the model executes
    — the same reasoning as knowledge 023's fence-aware edge derivation.
    """
    return _scan(body)[0]


def has_unclosed_fence(body: str) -> bool:
    """True if ``body`` ends inside a fence.

    An unclosed fence makes every line after it invisible to this module, which
    would silently hide a real dispatch instruction. Cheaper to reject the
    malformed file outright than to reason about what it hid.
    """
    return _scan(body)[1]


def is_dispatch_instruction(line: str) -> bool:
    """True iff ``line`` instructs an ``Agent`` dispatch (verb AND token)."""
    return bool(DISPATCH_VERB_RE.search(line)) and bool(DISPATCH_TOKEN_RE.search(line))


def dispatch_instructions(path: Path) -> list[tuple[int, str]]:
    """Dispatch-instruction lines in ``path``, as (lineno, line)."""
    return [
        (lineno, line)
        for lineno, line in _unfenced_lines(path.read_text(encoding="utf-8"))
        if is_dispatch_instruction(line)
    ]


def _discover_sites() -> dict[str, list[tuple[int, str]]]:
    """Enumerate dispatch instructions across the skill tree.

    Rooted at the repo's own ``plugins/minerva/skills`` — never a loose glob,
    so worktree copies under ``.minerva/worktrees/`` can't be picked up.
    """
    found = {}
    for md in sorted(SKILLS_DIR.rglob("*.md")):
        hits = dispatch_instructions(md)
        if hits:
            found[md.relative_to(SKILLS_DIR).as_posix()] = hits
    return found


SITES = _discover_sites()


def test_sites_discovered():
    # Guards the enumeration itself: if discovery silently returns nothing,
    # every per-site check below would vacuously pass.
    assert SITES, f"no dispatch instructions found under {SKILLS_DIR}"


@pytest.mark.parametrize("relpath", sorted(REGISTERED_SITES))
def test_registered_site_still_dispatches(relpath):
    """A registered site that stopped dispatching is stale registration."""
    assert relpath in SITES, (
        f"{relpath} is registered as a dispatch site but no longer contains a "
        f"dispatch instruction — drop it from REGISTERED_SITES if intentional"
    )
    assert len(SITES[relpath]) == REGISTERED_SITES[relpath], (
        f"{relpath} has {len(SITES[relpath])} dispatch instructions, "
        f"expected {REGISTERED_SITES[relpath]} — update REGISTERED_SITES "
        f"deliberately when adding one"
    )


def test_no_unregistered_dispatch_sites():
    """A new dispatch site must be registered, not silently added."""
    unregistered = sorted(set(SITES) - set(REGISTERED_SITES))
    assert not unregistered, (
        "unregistered dispatch site(s): "
        + ", ".join(unregistered)
        + " — add to REGISTERED_SITES and pin run_in_background"
    )


@pytest.mark.parametrize("relpath", sorted(REGISTERED_SITES))
def test_dispatch_instructions_pin_execution_mode(relpath):
    """The unit's core invariant: every dispatch instruction pins the mode."""
    unpinned = [
        lineno
        for lineno, line in SITES.get(relpath, [])
        if EXECUTION_MODE_KEY not in line
    ]
    assert not unpinned, (
        f"{relpath}: dispatch instruction(s) on line(s) "
        f"{', '.join(map(str, unpinned))} do not pin {EXECUTION_MODE_KEY} — "
        f"a backgrounded dispatch returns only a handle and strands the run"
    )


@pytest.mark.parametrize(
    "line",
    [
        "Spawn 3 subagents via the `Agent` tool with fresh context.",
        "Launch a fresh-context subagent via the `Agent` tool.",
        "the main model dispatches one agent (`subagent_type: general-purpose`)",
        "Dispatch one reviewer, `model: sonnet`, and arbitrate inline.",
        'Spawn a reviewer with `model: "sonnet"`.',
        "spawn a subagent via the `Agent tool` (backticks fall differently)",
        "Dispatch a subagent via the Agent tool with no backticks at all.",
    ],
)
def test_detector_recall(line):
    """Positive axis: phrasings that DO instruct a dispatch."""
    assert is_dispatch_instruction(line)


@pytest.mark.parametrize(
    "line",
    [
        # Verb, no dispatch token — prose about dispatching.
        "Each reviewer gate dispatches one subagent and the main model arbitrates.",
        "6 subagent dispatches max per decision point.",
        # Dispatch token, no verb — describing the parameters, not calling.
        "The `subagent_type` default is general-purpose and `model: sonnet` is standard.",
        # Neither — the Skill-tool handoff form, which must never be caught.
        "invoke `minerva:ship` via the `Skill` tool with its auto-mode instruction",
    ],
)
def test_detector_precision(line):
    """Negative axis: both halves of the conjunction must be required."""
    assert not is_dispatch_instruction(line)


def test_fence_pairing_semantics():
    """A non-matching fence inside a block is content, not a close."""
    body = "\n".join(
        [
            "outside-before",
            "```",
            "~~~",  # different char: literal content, must not close
            "``",  # too short to be a fence at all
            "```",  # the real close
            "outside-after",
        ]
    )
    assert [line for _, line in _unfenced_lines(body)] == [
        "outside-before",
        "outside-after",
    ]
    assert not has_unclosed_fence(body)


def test_unclosed_fence_detected():
    """A file ending inside a fence hides everything after it."""
    body = "outside\n```\nswallowed\n"
    assert has_unclosed_fence(body)
    assert [line for _, line in _unfenced_lines(body)] == ["outside"]


@pytest.mark.parametrize(
    "relpath",
    sorted(p.relative_to(SKILLS_DIR).as_posix() for p in SKILLS_DIR.rglob("*.md")),
)
def test_no_unclosed_fences_in_corpus(relpath):
    """Corpus-wide guard: no skill file may hide content behind a stray fence."""
    body = (SKILLS_DIR / relpath).read_text(encoding="utf-8")
    assert not has_unclosed_fence(body), (
        f"{relpath} ends inside a fenced block — every line after the stray "
        f"fence is invisible to the dispatch detector"
    )


@pytest.mark.parametrize("relpath,needle", PROSE_NEAR_MISSES)
def test_detector_excludes_prose(relpath, needle):
    """Precision guard: descriptions and budget statements are not dispatches."""
    path = SKILLS_DIR / relpath
    matching = [
        line for _, line in _unfenced_lines(path.read_text(encoding="utf-8"))
        if needle in line
    ]
    assert matching, f"{relpath}: fixture line not found — update PROSE_NEAR_MISSES"
    for line in matching:
        assert not is_dispatch_instruction(line), (
            f"{relpath}: prose matched the dispatch detector — it is too loose:\n{line}"
        )
