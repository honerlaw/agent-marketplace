#!/usr/bin/env python3
"""Repeatable **context-usage benchmark** for a Claude Code run.

Drives a fixed canned task through ``claude -p "<task>" --output-format json``,
runs ``run_analyzer`` over the produced session transcript, cross-checks the
derived cost against Claude Code's own ``total_cost_usd``, and appends one
comparable record to a tracked baseline (``benchmarks/baseline.jsonl``) keyed by
git SHA + task id. Re-running on a later commit and diffing the two records
answers the only question the per-file ``test_skill_budget.py`` floor can't:
*did this change improve or worsen what a full run loads and costs?*

A full ``minerva:propose-ship-auto`` run is non-deterministic, costs real money,
and has side effects (worktrees, commits, and — in its ship phase — a real PR /
push). So this is **not** a per-PR CI gate; it is a deliberately-triggered
benchmark (schedule / manual dispatch). Seed and re-run it against a throwaway
target, never one whose ship phase would push to a real repo.

Three subcommands:
  run     — drive ``claude -p`` for the canned task, then record. Needs auth and
            spends real money.
  record  — build a baseline record from an already-captured result.json +
            transcript.jsonl. Decouples the expensive run from the plumbing, so
            a careful manual run (e.g. in an isolated repo) can still be recorded.
  diff    — report the delta between the two most recent records for a task id.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from run_analyzer import analyze_transcript

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = REPO_ROOT / "benchmarks" / "baseline.jsonl"

# The canned task. Small, single-unit, additive — exercises the auto lifecycle
# (including the consensus panels) without a large diff. Run it against a
# throwaway target whose ship phase cannot push to a real repo.
DEFAULT_TASK_ID = "psa-add-docstring"
DEFAULT_TASK = (
    "Run minerva:propose-ship-auto to add a one-line module docstring to a "
    "small script in this repo. Keep it a single additive work unit."
)

# Cross-check tolerance: our independently-derived cost vs Claude Code's own
# total_cost_usd. A larger gap means the pricing table drifted or parsing broke.
COST_TOLERANCE_FRAC = 0.05


def _transcript_for_session(session_id: str, cwd: Path) -> "Path | None":
    """Locate the JSONL transcript Claude Code wrote for ``session_id``.

    Claude Code stores transcripts under
    ``~/.claude/projects/<encoded-cwd>/<session_id>.jsonl`` where the encoding
    replaces path separators with ``-``. We resolve by session-id filename
    across project dirs rather than reconstructing the encoding, so a quirk in
    the encoder can't make us miss it.
    """
    root = Path.home() / ".claude" / "projects"
    hits = sorted(root.glob(f"*/{session_id}.jsonl"))
    return hits[0] if hits else None


def build_record(
    result: dict,
    transcript_path,
    task_id: str,
    git_sha: str,
    subagent_paths=None,
) -> dict:
    """Assemble one baseline record from a ``claude -p`` result + its transcript.

    ``subagent_paths`` accepts additional transcript JSONL files for Agent-spawned
    subagent sessions (written to separate files by Claude Code, not isSidechain
    in the main transcript). Their costs are summed into ``subagent_cost_usd`` and
    merged into ``by_model``, making panel spend visible in the baseline. Paths
    are provided manually — Agent-spawned transcripts live in
    ``~/.claude/projects/<encoded-cwd>/`` alongside the main transcript.
    The ``cost_crosscheck_ok`` cross-check is against the main transcript only,
    since Claude's ``total_cost_usd`` does not include separate subagent sessions.
    """
    report = analyze_transcript(transcript_path)
    claude_cost = result.get("total_cost_usd")
    derived = report["total_cost_usd"]
    # Cross-check main transcript only (subagent sessions excluded from claude_cost).
    cost_ok = (
        claude_cost is not None
        and claude_cost > 0
        and abs(derived - claude_cost) / claude_cost <= COST_TOLERANCE_FRAC
    )

    # Aggregate Agent-spawned subagent sessions from separate JSONL files.
    sub_cost = report["by_scope"]["subagent"]["cost_usd"]
    sub_messages = report["by_scope"]["subagent"]["messages"]
    by_model = {m: v["cost_usd"] for m, v in report["by_model"].items()}
    for sp in subagent_paths or []:
        sub_report = analyze_transcript(sp)
        sub_cost = round(sub_cost + sub_report["total_cost_usd"], 6)
        sub_messages += sub_report["assistant_messages"]
        for m, v in sub_report["by_model"].items():
            by_model[m] = round(by_model.get(m, 0.0) + v["cost_usd"], 6)

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git_sha,
        "task_id": task_id,
        "session_id": result.get("session_id"),
        "num_turns": result.get("num_turns"),
        "claude_total_cost_usd": claude_cost,
        "derived_cost_usd": derived,
        "cost_crosscheck_ok": cost_ok,
        "unpriced_models": report["unpriced_models"],
        "assistant_messages": report["assistant_messages"],
        "num_subagent_messages": sub_messages,
        "main_cost_usd": report["by_scope"]["main"]["cost_usd"],
        "subagent_cost_usd": sub_cost,
        "totals": report["totals"],
        "by_model": by_model,
        "by_tool": report["by_tool"],
    }


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def append_record(record: dict, baseline=DEFAULT_BASELINE) -> None:
    baseline = Path(baseline)
    baseline.parent.mkdir(parents=True, exist_ok=True)
    with baseline.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def load_records(baseline=DEFAULT_BASELINE) -> list:
    baseline = Path(baseline)
    if not baseline.exists():
        return []
    return [json.loads(l) for l in baseline.read_text().splitlines() if l.strip()]


def diff_last_two(task_id: str, baseline=DEFAULT_BASELINE) -> dict:
    """Delta between the two most recent records for ``task_id`` (older -> newer)."""
    recs = [r for r in load_records(baseline) if r.get("task_id") == task_id]
    if len(recs) < 2:
        return {"task_id": task_id, "error": f"need >=2 records, have {len(recs)}"}
    old, new = recs[-2], recs[-1]

    def delta(key):
        a, b = old.get(key), new.get(key)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return {"from": a, "to": b, "delta": round(b - a, 6)}
        return {"from": a, "to": b}

    out = {
        "task_id": task_id,
        "from_sha": old.get("git_sha"),
        "to_sha": new.get("git_sha"),
        "derived_cost_usd": delta("derived_cost_usd"),
        "claude_total_cost_usd": delta("claude_total_cost_usd"),
        "num_turns": delta("num_turns"),
        "num_subagent_messages": delta("num_subagent_messages"),
    }
    out["totals"] = {
        k: {"from": old["totals"].get(k), "to": new["totals"].get(k),
            "delta": new["totals"].get(k, 0) - old["totals"].get(k, 0)}
        for k in new.get("totals", {})
    }
    return out


def cmd_run(args) -> int:
    task = args.get("task", DEFAULT_TASK)
    task_id = args.get("task_id", DEFAULT_TASK_ID)
    cwd = Path(args.get("cwd", ".")).resolve()
    cmd = ["claude", "-p", task, "--output-format", "json"]
    if args.get("max_turns"):
        cmd += ["--max-turns", str(args["max_turns"])]
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode
    result = json.loads(proc.stdout)
    transcript = _transcript_for_session(result.get("session_id", ""), cwd)
    if transcript is None:
        sys.stderr.write(f"could not locate transcript for {result.get('session_id')}\n")
        return 1
    record = build_record(result, transcript, task_id, args.get("git_sha") or _git_sha())
    append_record(record, args.get("baseline", DEFAULT_BASELINE))
    print(json.dumps(record, indent=2))
    return 0 if record["cost_crosscheck_ok"] else 0  # crosscheck is advisory


def cmd_record(args) -> int:
    result = json.loads(Path(args["result"]).read_text())
    record = build_record(
        result, args["transcript"],
        args.get("task_id", DEFAULT_TASK_ID),
        args.get("git_sha") or _git_sha(),
        subagent_paths=args.get("subagent") or [],
    )
    append_record(record, args.get("baseline", DEFAULT_BASELINE))
    print(json.dumps(record, indent=2))
    return 0


def cmd_diff(args) -> int:
    print(json.dumps(diff_last_two(
        args.get("task_id", DEFAULT_TASK_ID), args.get("baseline", DEFAULT_BASELINE)
    ), indent=2))
    return 0


def _parse(argv):
    """Tiny flag parser (kept dependency-free, matching the other scripts).

    ``--subagent <path>`` may be repeated; its values accumulate as a list.
    All other flags use last-wins semantics.
    """
    if not argv:
        return None, {}
    sub, rest, args = argv[0], argv[1:], {}
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok.startswith("--"):
            key = tok[2:].replace("-", "_")
            if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                val = rest[i + 1]
                if key == "subagent":
                    args.setdefault("subagent", []).append(val)
                else:
                    args[key] = val
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    return sub, args


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    sub, args = _parse(argv)
    if sub == "run":
        return cmd_run(args)
    if sub == "record":
        if "result" not in args or "transcript" not in args:
            print("record needs --result <json> --transcript <jsonl>", file=sys.stderr)
            return 2
        return cmd_record(args)
    if sub == "diff":
        return cmd_diff(args)
    print("usage: run_benchmark.py {run|record|diff} [--flags]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
