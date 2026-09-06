#!/usr/bin/env python3
"""Tally the autonomous orchestrators' decision logs across a project's work units.

`minerva:propose-ship-quick`, `-balanced` and `-auto` each append one line per decision to
the unit's `scratchpad.md` under `## Quick decisions`, `## Balanced decisions` and
`## Panel decisions` headers. Those lines are the only evidence of what each rung's
adjudication actually did — how often a reviewer's critique was folded, how often a panel
went to a revision round, how often anything reached the user — and the reviewer-gate
taxonomy is documented as "the load-bearing, revisable knob" that this evidence is
supposed to tune.

Re-tuning it cost an afternoon. The pass that motivated this module was hand-rolled grep
and awk over the archived scratchpads, and it broke twice on format drift (a header regex
that missed one spelling, a bullet regex that missed another) before producing numbers
anyone trusted. A reader that already knows the grammar, is fence-aware, and reports what
it could NOT classify is what makes the next re-tune a one-command check.

Three rules, each traceable to a knowledge entry:

- **Scan `.minerva/work/` only, never through `.minerva/worktrees/`.** A worktree glob
  sees every unit in the project through each worktree, so counting through it counts each
  unit once per worktree (`2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project`).
- **Fence-aware via the single-sourced primitive.** A fenced example of a decision line is
  an illustration, not a record; `knowledge_spans.unfenced` is imported, never re-derived
  (`2026-06-11-constraint-fence-scans-import-fence-re`).
- **Unknown is a reported outcome, not a dropped line.** Balanced and Quick tags are a
  closed vocabulary and classify exactly; Panel tags are `minerva:round-table`'s free-form
  vote strings and classify heuristically. Anything neither recognises is kept, tagged
  `unknown`, and printed with its `path:lineno`, because a tally that silently drops what
  it cannot read is a false reading (`2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`).

Re-check lines (`[rechecked — …]`) pair with the `[reviewed — folded]` line immediately
before them, by adjacency and same gate. An orphan — a re-check with no fold in front of it —
is reported as a problem rather than counted as a fold.
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_spans import unfenced  # noqa: E402

ORCHESTRATORS = ("Balanced", "Panel", "Quick")

HEADER_RE = re.compile(
    r"^##\s+(?P<orch>Balanced|Panel|Quick)\s+decisions\b(?:\s+(?P<date>\d{4}-\d{2}-\d{2}))?",
    re.IGNORECASE,
)
SECTION_END_RE = re.compile(r"^##\s")
LINE_RE = re.compile(r"^\s*[-*]\s+\[(?P<tag>[^\]]+)\]\s*(?P<rest>.*)$")
# The gate is the text before the first ':' , ' — ', ' – ' or '(' — whatever the author used
# to separate the decision's name from its rationale.
GATE_SPLIT_RE = re.compile(r"\s*(?::|\s[—–]\s|\()")

UNKNOWN = "unknown"

# Balanced / Quick: a closed vocabulary. Keys are dash- and whitespace-normalised.
EXACT_TAGS = {
    "decided": "decided",
    "reviewed - clean": "reviewed-clean",
    "reviewed - folded": "reviewed-folded",
    "rechecked - clean": "rechecked-clean",
    "rechecked - residual folded": "rechecked-residual-folded",
    "rechecked - escalated": "rechecked-escalated",
    "escalated to user": "escalated",
    "process note": "process-note",
    "synthesis": "synthesis",
}

RECHECK_OUTCOMES = {"rechecked-clean", "rechecked-residual-folded", "rechecked-escalated"}

# Ordered: the first matching keyword wins, so "replan-vs-fix" is tested before "replan".
GATE_RULES = (
    ("whole-proposal", ("whole-proposal", "whole proposal")),
    ("approach", ("approach",)),
    ("scope", ("scope",)),
    ("completion", ("completion", "success criteria", "success-criteria")),
    ("divergence", ("divergence",)),
    ("replan-vs-fix", ("replan-vs-fix", "replan vs fix", "replan vs. fix")),
    ("replan-acceptance", ("new-plan", "new plan", "replan acceptance", "replan-acceptance")),
    ("triage", ("triage",)),
    ("partition", ("partition",)),
    ("todo", ("todo",)),
    ("synthesis", ("synthesis",)),
    ("preflight", ("pre-flight", "preflight", "in-flight", "issue match", "issue-match")),
)

PANEL_REVISION_RE = re.compile(r"revis|→|vote\s*2|rev\s*2|round\s*2", re.IGNORECASE)
PANEL_VOTE_RE = re.compile(r"\b\d\s*/\s*3\b")


@dataclass
class Record:
    unit: str
    orchestrator: str
    date: str | None
    tag: str
    gate_raw: str
    gate: str
    outcome: str
    rest: str
    path: str
    lineno: int
    paired_with: int | None = None  # index into the same section's records, for re-checks
    rechecked: str | None = None    # set on a folded record when a re-check paired with it
    problems: list[str] = field(default_factory=list)

    @property
    def where(self) -> str:
        return f"{self.path}:{self.lineno}"


def normalize_tag(tag: str) -> str:
    key = tag.strip().lower()
    key = re.sub(r"\s*[—–-]+\s*", " - ", key)
    return re.sub(r"\s+", " ", key).strip()


def normalize_gate(raw: str) -> str:
    low = raw.strip().lower()
    for canonical, needles in GATE_RULES:
        if any(n in low for n in needles):
            return canonical
    return f"other:{raw.strip()}" if raw.strip() else "other:"


def classify_tag(orchestrator: str, tag: str) -> str:
    """The outcome class of one `[tag]`, or `unknown`.

    Balanced and Quick share one closed vocabulary. Panel tags are round-table's free-form
    vote strings, so they classify by markers: an escalation, a skip, a user directive, a
    revision marker, or a bare `N/3 accept`.
    """
    orch = orchestrator.capitalize()
    if orch in ("Balanced", "Quick"):
        return EXACT_TAGS.get(normalize_tag(tag), UNKNOWN)
    if orch == "Panel":
        low = tag.lower()
        if "escalat" in low:
            return "escalated"
        if "skipped" in low:
            return "skipped"
        if "user-directed" in low or "user-decided" in low:
            return "user-directed"
        if "synthesis" in low:
            return "synthesis"
        if PANEL_REVISION_RE.search(tag):
            return "panel-revised"
        if PANEL_VOTE_RE.search(tag) or "accept" in low:
            return "panel-accept"
        return UNKNOWN
    return UNKNOWN


def split_gate(rest: str) -> str:
    m = GATE_SPLIT_RE.search(rest)
    return rest[: m.start()] if m else rest


def parse_scratchpad(text: str, unit: str, path: str) -> list[Record]:
    """Every decision record in one scratchpad, in file order, outside code fences."""
    records: list[Record] = []
    section: list[Record] = []
    orch = date = None
    for idx, line in unfenced(text.splitlines()):
        lineno = idx + 1
        h = HEADER_RE.match(line)
        if h:
            _pair_rechecks(section)
            section = []
            orch = h.group("orch").capitalize()
            date = h.group("date")
            continue
        if SECTION_END_RE.match(line):
            _pair_rechecks(section)
            section = []
            orch = None
            continue
        if orch is None:
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        tag, rest = m.group("tag"), m.group("rest")
        gate_raw = split_gate(rest)
        rec = Record(
            unit=unit, orchestrator=orch, date=date, tag=tag, gate_raw=gate_raw,
            gate=normalize_gate(gate_raw), outcome=classify_tag(orch, tag), rest=rest,
            path=path, lineno=lineno,
        )
        if rec.outcome == UNKNOWN:
            rec.problems.append(f"unknown tag [{tag}]")
        section.append(rec)
        records.append(rec)
    _pair_rechecks(section)
    return records


def _pair_rechecks(section: list[Record]) -> None:
    for i, rec in enumerate(section):
        if rec.outcome not in RECHECK_OUTCOMES:
            continue
        prev = section[i - 1] if i else None
        if prev is not None and prev.outcome == "reviewed-folded" and prev.gate == rec.gate:
            rec.paired_with = i - 1
            prev.rechecked = rec.outcome
        else:
            rec.problems.append("orphan re-check: no [reviewed — folded] line for the same gate immediately before it")


def scratchpad_files(root: Path) -> list[Path]:
    """Live and archived scratchpads under `<root>/.minerva/work/`, never via worktrees."""
    work = root / ".minerva" / "work"
    if not work.is_dir():
        return []
    files: list[Path] = []
    for unit_dir in sorted(p for p in work.iterdir() if p.is_dir()):
        live = unit_dir / "scratchpad.md"
        if live.is_file():
            files.append(live)
        archive = unit_dir / "archive"
        if archive.is_dir():
            files.extend(sorted(p for p in archive.glob("*.md") if p.is_file()))
    return files


def collect(root: Path) -> list[Record]:
    root = Path(root)
    out: list[Record] = []
    for f in scratchpad_files(root):
        unit = f.parent.name if f.parent.name != "archive" else f.parent.parent.name
        out.extend(parse_scratchpad(f.read_text(encoding="utf-8"), unit, str(f.relative_to(root))))
    return out


def tally(records: list[Record]) -> dict[str, dict[str, Counter]]:
    """`{orchestrator: {gate: Counter(outcome)}}`."""
    out: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for r in records:
        out[r.orchestrator][r.gate][r.outcome] += 1
    return out


def outcome_totals(records: list[Record]) -> dict[str, Counter]:
    out: dict[str, Counter] = defaultdict(Counter)
    for r in records:
        out[r.orchestrator][r.outcome] += 1
    return out


def recheck_summary(records: list[Record]) -> dict[str, int]:
    folded = [r for r in records if r.outcome == "reviewed-folded"]
    return {
        "folded": len(folded),
        "folded-and-rechecked": sum(1 for r in folded if r.rechecked),
        "folded-unchecked": sum(1 for r in folded if not r.rechecked),
        **{o: sum(1 for r in records if r.outcome == o) for o in sorted(RECHECK_OUTCOMES)},
    }


def problems(records: list[Record]) -> list[str]:
    return [f"{r.where}: {p}" for r in records for p in r.problems]


def units_with(records: list[Record], orchestrator: str) -> set[str]:
    return {r.unit for r in records if r.orchestrator == orchestrator}


def render(records: list[Record]) -> str:
    lines: list[str] = []
    by_orch = tally(records)
    totals = outcome_totals(records)
    for orch in ORCHESTRATORS:
        if orch not in by_orch:
            continue
        n_units = len(units_with(records, orch))
        n = sum(totals[orch].values())
        lines.append(f"== {orch} decisions — {n} lines across {n_units} units ==")
        lines.append("  totals: " + ", ".join(f"{o} {c}" for o, c in totals[orch].most_common()))
        for gate in sorted(by_orch[orch], key=lambda g: (g.startswith("other:"), g)):
            row = ", ".join(f"{o} {c}" for o, c in by_orch[orch][gate].most_common())
            lines.append(f"  {gate:<22} {row}")
        if orch == "Balanced":
            rs = recheck_summary([r for r in records if r.orchestrator == orch])
            lines.append("  re-checks: " + ", ".join(f"{k} {v}" for k, v in rs.items()))
        lines.append("")
    probs = problems(records)
    lines.append(f"== Problems — {len(probs)} ==")
    lines.extend(f"  {p}" for p in probs)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    print(render(collect(root)))
    return 0  # a reader, not a gate


if __name__ == "__main__":
    sys.exit(main(sys.argv))
