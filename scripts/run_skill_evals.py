#!/usr/bin/env python3
"""Behavioral skill-value runner — the Tier-2 (does-this-skill-add-value) eval.

For each declarative behavioral case in ``evals/<skill>/behavioral.json``, this
runner executes the task **with** the skill available (treatment) and **without**
it (control), judges both transcripts against the case rubric with an
LLM-as-judge, and reports the ``treatment - control`` "value-added" delta.

CONTROL IS NOW REAL; THE DELTA IS STILL UNVALIDATED. The blocking half of the
validation spike has returned "go": a single skill CAN be suppressed cleanly, by
pointing ``--plugin-dir`` at a copy of this plugin with that one skill directory
removed. Verified live 2026-08-22 — the treatment arm reports the skill present
and the control arm reports it absent, reproducibly.

The previous control was a **no-op**: it ran the identical ``claude -p`` command
for both arms and only printed a warning, so ``treatment - control`` compared a
configuration against itself and every reported delta was pure run-to-run noise.
That is why no backfill was permitted against it.

Still open: whether the delta, now that it measures something, is separable from
run-to-run variance. Until that is answered, treat magnitudes as experimental and
do not CI-gate. The cited prior art (skill-creator) does skill *triggering* and
*variant-vs-variant* comparison, NOT present-vs-absent suppression.

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
import shutil
import subprocess
import sys
import tempfile
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
# The minerva plugin tree the arms are built from. This runner is a repo-only script
# (`<repo>/scripts/`), NOT shipped inside the plugin, so the plugin root is a sibling
# path rather than this file's parent — getting that wrong silently produced a control
# arm with nothing removed, which the `arm_plugin_dir` guard caught on first live run.
PLUGIN_ROOT = REPO_ROOT / "plugins" / "minerva"

# Cache of materialised arm plugin dirs, keyed by (skill, skill_available), so a
# multi-case run copies the plugin tree once per arm rather than once per call.
_ARM_DIRS: dict = {}


def arm_plugin_dir(skill: str, skill_available: bool) -> Path:
    """A plugin directory for one arm: the full plugin, or it minus ``skill``.

    THE control mechanism. `--plugin-dir` makes the nested run load exactly this
    tree, so removing one skill directory from the copy removes exactly that skill
    from the arm — the clean single-skill suppression the validation spike was
    blocked on. Verified live 2026-08-22: probing for the skill's presence returns
    true under the treatment dir and false under the control dir, reproducibly.

    Do NOT add `--bare` to "isolate harder". It skips credential resolution, so a
    nested run under it fails with "Not logged in" — measured, not assumed. The
    plugin-dir override alone is sufficient: the control probe reports the skill
    absent without it.
    """
    key = (skill, skill_available)
    if key not in _ARM_DIRS:
        dest = Path(tempfile.mkdtemp(prefix=f"skilleval-{skill}-")) / "plugin"
        shutil.copytree(PLUGIN_ROOT, dest)
        if not skill_available:
            target = dest / "skills" / skill
            if not target.is_dir():
                raise RuntimeError(
                    f"cannot build a control arm for {skill!r}: no skills/{skill} "
                    f"directory in {PLUGIN_ROOT} — suppressing nothing would make the "
                    "delta meaningless rather than merely noisy")
            shutil.rmtree(target)
        _ARM_DIRS[key] = dest
    return _ARM_DIRS[key]


def claude_invoke(prompt: str, skill_available: bool, skill: str) -> str:
    """Default real invocation: shell out to `claude -p` with an arm-specific plugin dir.

    The two arms differ in exactly one thing — whether ``skills/<skill>/`` exists in
    the plugin tree the nested run loads. Everything else (model, tools, prompt,
    environment) is identical.

    The previous implementation ran the SAME command for both arms and only printed
    a warning, so the reported delta compared a configuration against itself.
    Tests never reach this function — they inject a stub.
    """
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # allow nesting claude -p (mirrors skill-creator)
    result = subprocess.run(
        ["claude", "-p", "--plugin-dir", str(arm_plugin_dir(skill, skill_available)),
         prompt],
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
