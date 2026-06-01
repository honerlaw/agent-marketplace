#!/usr/bin/env python3
"""Behavioral skill-value runner — the Tier-2 (does-this-skill-add-value) eval.

For each declarative behavioral case in ``evals/<skill>/behavioral.json``, this
runner executes the task **with** the skill available (treatment) and **without**
it (control), judges both transcripts against the case rubric with an
LLM-as-judge, and reports the ``treatment - control`` "value-added" delta.

PROVISIONAL — the methodology is not validated. Whether the with-minus-without
delta is a stable, meaningful per-skill signal is an open question; cleanly
suppressing ONE auto-discovered skill as a control is itself unsolved (see the
work unit's followups.md — the mandatory validation spike). The cited prior art
(skill-creator) does skill *triggering* and *variant-vs-variant* comparison, NOT
present-vs-absent suppression. Treat reported deltas as experimental.

This is on-demand tooling — NOT a CI gate (non-deterministic, costs API).

Design: the runner is layered so the deterministic parts are testable without any
API. ``load_cases`` / ``build_plan`` / ``score_case`` / ``render_markdown`` are
pure; the only non-deterministic steps are funneled through the INJECTABLE
``invoke`` and ``judge`` callables, which tests replace with stubs and which
``--dry-run`` never calls.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Case:
    id: str
    prompt: str
    rubric: list[str]
    # Reserved — parsed and validated but NOT yet threaded into invoke(); the
    # validation spike (followups.md) wires file fixtures into the task prompt.
    files: list[str] = field(default_factory=list)


@dataclass
class Step:
    """One planned invocation. ``arm`` is 'treatment' | 'control' | 'judge'."""
    arm: str
    skill_available: bool | None  # None for the judge step
    prompt: str


@dataclass
class CasePlan:
    case_id: str
    steps: list[Step]


# --------------------------------------------------------------------------- #
# Layer 1 — parse (pure, deterministic)
# --------------------------------------------------------------------------- #
def load_cases(skill: str, evals_dir: Path = EVALS_DIR) -> list[Case]:
    """Load and validate ``evals/<skill>/behavioral.json``.

    Note: ``baseline`` is intentionally NOT part of the schema yet — live
    baseline recording is deferred to the validation spike.
    """
    path = evals_dir / skill / "behavioral.json"
    if not path.is_file():
        raise FileNotFoundError(f"no behavioral cases for {skill!r}: {path}")
    doc = json.loads(path.read_text())
    if doc.get("skill") != skill:
        raise ValueError(f"{path}: 'skill' is {doc.get('skill')!r}, expected {skill!r}")
    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{path}: 'cases' must be a non-empty list")
    out: list[Case] = []
    seen: set[str] = set()
    for i, c in enumerate(cases):
        cid = c.get("id")
        if not cid:
            raise ValueError(f"{path}: case #{i} missing 'id'")
        if cid in seen:
            raise ValueError(f"{path}: duplicate case id {cid!r}")
        seen.add(cid)
        if not c.get("prompt"):
            raise ValueError(f"{path}: case {cid!r} missing 'prompt'")
        rubric = c.get("rubric")
        if not isinstance(rubric, list) or not rubric:
            raise ValueError(f"{path}: case {cid!r} 'rubric' must be a non-empty list")
        out.append(Case(id=cid, prompt=c["prompt"], rubric=rubric,
                        files=c.get("files", [])))
    return out


def discover_skills(evals_dir: Path = EVALS_DIR) -> list[str]:
    return sorted(p.parent.name for p in evals_dir.glob("*/behavioral.json"))


# --------------------------------------------------------------------------- #
# Layer 2 — plan (pure, deterministic; what --dry-run prints)
# --------------------------------------------------------------------------- #
def build_plan(case: Case) -> CasePlan:
    """A case always plans exactly three steps: treatment, control, judge.

    The control step is always present (never silently dropped) so a value-delta
    is always defined as treatment - control.
    """
    return CasePlan(case_id=case.id, steps=[
        Step(arm="treatment", skill_available=True, prompt=case.prompt),
        Step(arm="control", skill_available=False, prompt=case.prompt),
        Step(arm="judge", skill_available=None, prompt=case.prompt),
    ])


# --------------------------------------------------------------------------- #
# Layer 3 — execute (the ONLY non-deterministic layer; injectable)
# --------------------------------------------------------------------------- #
def claude_invoke(prompt: str, skill_available: bool, skill: str) -> str:
    """Default real invocation: shell out to `claude -p`.

    PROVISIONAL CONTROL: when ``skill_available`` is False we want the task run
    WITHOUT this one skill in scope, but cleanly suppressing a single
    auto-discovered skill is unsolved. This default is a best-effort placeholder
    (it runs the prompt in a nested `claude -p` and does NOT yet guarantee the
    skill is absent) and emits a warning. The validation spike must replace it.
    Tests never reach this function — they inject a stub.
    """
    if not skill_available:
        print(f"WARNING: control arm for {skill!r} uses a provisional, unvalidated "
              "suppression — the delta is experimental (see followups.md spike).",
              file=sys.stderr)
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # allow nesting claude -p (mirrors skill-creator)
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True, text=True, env=env, timeout=600,
    )
    # Fail loud: an empty transcript silently scored would fabricate a value-delta —
    # exactly the false signal this runner exists to avoid.
    if result.returncode != 0:
        raise RuntimeError(
            f"`claude -p` failed (rc={result.returncode}) for {skill!r}: "
            f"{result.stderr.strip()[:500]}")
    return result.stdout


def claude_judge(prompt: str, transcript: str, rubric: list[str]) -> dict:
    """Default real judge: an LLM-as-judge `claude -p` call returning a score.

    Returns {"score": float, "notes": str}. Tests inject a stub instead.
    """
    rubric_block = "\n".join(f"- {c}" for c in rubric)
    judge_prompt = (
        "You are scoring how well an assistant TRANSCRIPT answers a TASK against a "
        f"rubric. Award one point per rubric item fully satisfied (max {len(rubric)}). "
        'Reply with ONLY a JSON object: {"score": <number>, "notes": "<one line>"}.\n\n'
        f"TASK:\n{prompt}\n\nRUBRIC:\n{rubric_block}\n\nTRANSCRIPT:\n{transcript}\n"
    )
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    result = subprocess.run(
        ["claude", "-p", judge_prompt],
        capture_output=True, text=True, env=env, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"judge `claude -p` failed (rc={result.returncode}): "
            f"{result.stderr.strip()[:500]}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"judge did not return JSON: {result.stdout.strip()[:300]!r}") from e
    if not isinstance(data.get("score"), (int, float)):
        raise ValueError(f"judge 'score' is not numeric: {data!r}")
    return data


# --------------------------------------------------------------------------- #
# Layer 4 — score (pure given invoke/judge results)
# --------------------------------------------------------------------------- #
def score_case(case: Case, invoke, judge) -> dict:
    """Run one case end-to-end through the injected invoke/judge callables."""
    treatment = invoke(case.prompt, True, case.id)
    control = invoke(case.prompt, False, case.id)
    t_score = float(judge(case.prompt, treatment, case.rubric)["score"])
    c_score = float(judge(case.prompt, control, case.rubric)["score"])
    return {
        "id": case.id,
        "rubric_max": len(case.rubric),
        "treatment_score": t_score,
        "control_score": c_score,
        "delta": t_score - c_score,
    }


def run_skill(skill: str, invoke=claude_invoke, judge=claude_judge,
              evals_dir: Path = EVALS_DIR) -> dict:
    cases = load_cases(skill, evals_dir)
    results = [score_case(c, invoke, judge) for c in cases]
    deltas = [r["delta"] for r in results]
    return {
        "skill": skill,
        "provisional": True,
        "cases": results,
        "summary": {
            "n_cases": len(results),
            "mean_delta": sum(deltas) / len(deltas) if deltas else 0.0,
        },
    }


# --------------------------------------------------------------------------- #
# Layer 5 — report (pure)
# --------------------------------------------------------------------------- #
def render_markdown(report: dict) -> str:
    lines = [
        f"# Behavioral eval — `{report['skill']}` (PROVISIONAL)",
        "",
        "> Value-delta methodology is unvalidated; treat deltas as experimental.",
        "",
        "| case | treatment | control | delta (value added) |",
        "|------|-----------|---------|---------------------|",
    ]
    for c in report["cases"]:
        lines.append(
            f"| {c['id']} | {c['treatment_score']:.1f}/{c['rubric_max']} "
            f"| {c['control_score']:.1f}/{c['rubric_max']} | {c['delta']:+.1f} |"
        )
    lines += ["", f"**mean delta:** {report['summary']['mean_delta']:+.2f} "
                  f"over {report['summary']['n_cases']} case(s)"]
    return "\n".join(lines) + "\n"


def render_dry_run(skill: str, plans: list[CasePlan]) -> dict:
    return {
        "skill": skill,
        "dry_run": True,
        "cases": [
            {"id": p.case_id,
             "steps": [{"arm": s.arm, "skill_available": s.skill_available}
                       for s in p.steps]}
            for p in plans
        ],
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run behavioral skill-value evals.")
    ap.add_argument("--skill", help="skill to eval (default: all with behavioral.json)")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate cases + print the run plan; no API calls")
    ap.add_argument("--out", type=Path, help="write JSON report to this path")
    args = ap.parse_args(argv)

    skills = [args.skill] if args.skill else discover_skills()
    if not skills:
        print("no skills with evals/<skill>/behavioral.json found", file=sys.stderr)
        return 1

    if args.dry_run:
        plans = {s: [build_plan(c) for c in load_cases(s)] for s in skills}
        out = [render_dry_run(s, p) for s, p in plans.items()]
        print(json.dumps(out, indent=2))
        return 0

    reports = [run_skill(s) for s in skills]
    for r in reports:
        print(render_markdown(r))
    if args.out:
        args.out.write_text(json.dumps(reports, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
