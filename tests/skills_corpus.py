"""Shared locators for the minerva skill corpus.

Three test modules independently hard-coded the autonomous-orchestrator list and two of them
hand-rolled "find a phase's section in phases.md" — one carefully, one not. Two derivations plus
the hope that they agree is the shape `2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant`
is about, and a fifth rung on the orchestrator ladder would have needed three lockstep edits with
nothing tying them together.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "minerva" / "skills"

# The orchestrators that replace human gates with their own adjudication. `propose-ship` is
# deliberately absent: a human decides at each of its transitions.
AUTONOMOUS_ORCHESTRATORS = ["propose-ship-quick", "propose-ship-balanced", "propose-ship-auto"]

PHASE_HEADER_RE = re.compile(r"^## Phase (\d+(?:\.\d+)?)\s*[—-].*$", re.M)


def phases_text(orch: str) -> str:
    return (SKILLS / orch / "references" / "phases.md").read_text()


def phase_sections(orch: str) -> list[tuple[str, str]]:
    """[(label, body)] for each `## Phase X` section, in document order."""
    text = phases_text(orch)
    hits = [(m.group(1), m.start()) for m in PHASE_HEADER_RE.finditer(text)]
    out = []
    for i, (label, start) in enumerate(hits):
        end = hits[i + 1][1] if i + 1 < len(hits) else len(text)
        out.append((label, text[start:end]))
    return out


def phase_body(orch: str, label: str) -> str:
    """One phase's section. Asserts rather than raising ValueError from a bare .index(),
    so a reworded heading fails with a readable message instead of a stack trace."""
    for got, body in phase_sections(orch):
        if got == label:
            return body
    raise AssertionError(f"{orch} has no `## Phase {label}` section")


def slice_between(text: str, start_anchor: str, end_anchor: str, what: str) -> str:
    """Text from `start_anchor` up to the next `end_anchor`, with both anchors asserted."""
    assert start_anchor in text, f"{what}: anchor {start_anchor!r} not found"
    start = text.index(start_anchor)
    end = text.find(end_anchor, start + len(start_anchor))
    return text[start:] if end == -1 else text[start:end]
