#!/usr/bin/env python3
"""Installed-script resolution and versioned, untracked lifecycle checkpoints.

Read/resolve never create files. Writes use revision checks under a per-unit lock
and atomic replacement. A checkpoint is evidence of progress, not authorization.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from plugin_guard import divergence, working_tree_root

VERSION = 1
COUNTERS = ("fix_iteration", "cleanup_retry", "escalations", "decisions", "reviewers")
PHASES = {"ship", "cleanup", "reconciliation", "done"}
FIELDS = {"version", "repository", "unit", "revision", "branch", "caller", "phase",
          "pr", "cleanup_deadline", "status", *COUNTERS}
# `propose-ship-quick` and `propose-ship-balanced` were folded into `propose-ship-auto`
# (2026-09-23). A checkpoint written by either before then is still valid state — its caller
# cannot change on resume — but it must resume through a skill that still exists.
LEGACY_CALLERS = {"propose-ship-quick": "propose-ship-auto",
                  "propose-ship-balanced": "propose-ship-auto"}
CALLERS = {None, "propose-ship", "propose-ship-auto", *LEGACY_CALLERS}
REQUIRED_MODULES = {
    "decision_telemetry.py", "knowledge_fix.py", "knowledge_lint.py",
    "knowledge_rename.py", "knowledge_edits.py", "knowledge_spans.py",
    "minerva_runtime.py", "migration_status.py", "plugin_guard.py",
    "synthesis_status.py", "work_status.py", "workstream_status.py",
}


def resolve_scripts(skill_file: Path, override: str | None = None) -> Path:
    skill_file = skill_file.expanduser().resolve(strict=True)
    if skill_file.name != "SKILL.md" or skill_file.parent.parent.name != "skills":
        raise ValueError("expected an installed skills/<name>/SKILL.md")
    root = skill_file.parents[2]
    manifests = [root / d / "plugin.json" for d in (".claude-plugin", ".codex-plugin")]
    values = [json.loads(p.read_text()) for p in manifests if p.is_file()]
    if not any(isinstance(value, dict) and value.get("name") == "minerva" for value in values):
        raise ValueError("skill is not inside a Minerva plugin package")
    choice = override if override is not None else os.environ.get("MINERVA_SCRIPTS")
    scripts = Path(choice).expanduser().resolve(strict=True) if choice else root / "scripts"
    missing = sorted(name for name in REQUIRED_MODULES if not (scripts / name).is_file())
    if missing:
        raise ValueError(f"incomplete scripts directory {scripts}: missing {', '.join(missing)}")
    if not choice and divergence(scripts, working_tree_root()):
        raise ValueError("stale installed scripts; update Minerva or explicitly set MINERVA_SCRIPTS")
    return scripts.resolve()


def common_dir(cwd: Path | None = None) -> Path:
    cwd = (cwd or Path.cwd()).resolve()
    result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=cwd,
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError("lifecycle checkpoints require a Git repository")
    return (cwd / result.stdout.strip()).resolve()


def state_path(unit: str, cwd: Path | None = None) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", unit) or ".." in unit:
        raise ValueError("unit must be a slug, not a path")
    return common_dir(cwd) / "minerva" / "runtime" / unit / "run.json"


def validate(state: dict, unit: str, repository: str) -> dict:
    if not isinstance(state, dict) or set(state) != FIELDS:
        raise ValueError("checkpoint has missing or unknown fields")
    if type(state["version"]) is not int or state["version"] != VERSION:
        raise ValueError("unsupported checkpoint version")
    if state["unit"] != unit or state["repository"] != repository:
        raise ValueError("checkpoint repository/unit mismatch")
    if not isinstance(state["branch"], str) or not state["branch"]:
        raise ValueError("checkpoint needs a branch")
    if state["caller"] not in CALLERS or state["phase"] not in PHASES:
        raise ValueError("invalid checkpoint caller/phase")
    if state["status"] not in {"pending", "blocked", "completed"}:
        raise ValueError("invalid checkpoint status")
    if (state["phase"] == "done") != (state["status"] == "completed"):
        raise ValueError("only a done checkpoint can be completed")
    for field in ("revision", *COUNTERS):
        if type(state[field]) is not int or state[field] < 0:
            raise ValueError(f"invalid checkpoint {field}")
    if state["fix_iteration"] > 3 or state["cleanup_retry"] > 12:
        raise ValueError("checkpoint retry budget exceeded")
    if state["pr"] is not None and (type(state["pr"]) is not int or state["pr"] < 1):
        raise ValueError("invalid checkpoint PR")
    deadline = state["cleanup_deadline"]
    if deadline is not None and (type(deadline) not in (int, float) or deadline <= 0
                                 or not math.isfinite(deadline)):
        raise ValueError("invalid cleanup deadline")
    return state


def read_state(unit: str, cwd: Path | None = None) -> dict | None:
    path = state_path(unit, cwd)
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text())
        return validate(state, unit, str(common_dir(cwd)))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid checkpoint {path}: {exc}") from exc


@contextlib.contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def write_state(unit: str, payload: dict, cwd: Path | None = None, start_phase=False) -> dict:
    if not isinstance(payload, dict) or set(payload) - FIELDS:
        raise ValueError("checkpoint input must be an object with known fields")
    path = state_path(unit, cwd)
    with locked(path):
        previous = read_state(unit, cwd)
        if start_phase and (not previous or previous["status"] != "completed"):
            raise ValueError("a new phase requires completed prior progress")
        expected = previous["revision"] if previous else 0
        if type(payload.get("revision")) is not int or payload["revision"] != expected:
            raise ValueError("stale checkpoint revision; reread progress before advancing")
        initial = dict(version=VERSION, repository=str(common_dir(cwd)), unit=unit,
                       revision=0, branch="", caller=None, phase="ship", pr=None,
                       cleanup_deadline=None, status="pending",
                       **dict.fromkeys(COUNTERS, 0))
        phase_defaults = dict(phase="ship", status="pending", pr=None,
                              fix_iteration=0, cleanup_retry=0, cleanup_deadline=None) if start_phase else {}
        state = {**(previous or initial), **phase_defaults, **payload}
        state["revision"] = expected + 1
        validate(state, unit, str(common_dir(cwd)))
        if previous:
            if previous["status"] == "completed" and not start_phase:
                raise ValueError("clear completed progress before starting a new run")
            if start_phase and (state["branch"] == previous["branch"] or state["phase"] != "ship"
                                or state["status"] != "pending" or state["pr"] is not None):
                raise ValueError("a new phase requires a new branch with no recorded PR")
            if not start_phase and state["branch"] != previous["branch"]:
                raise ValueError("resume cannot change the original branch")
            if not start_phase and previous["pr"] is not None and state["pr"] != previous["pr"]:
                raise ValueError("resume cannot change the original work PR")
            monotonic = COUNTERS[2:] if start_phase else COUNTERS
            if any(state[k] < previous[k] for k in monotonic):
                raise ValueError("resume cannot reset checkpoint counters")
            if state["caller"] != previous["caller"]:
                raise ValueError("resume cannot change the original caller")
            if not start_phase and previous["cleanup_deadline"] is not None and state["cleanup_deadline"] != previous["cleanup_deadline"]:
                raise ValueError("resume cannot extend or remove the cleanup deadline")
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".run-", suffix=".json")
        try:
            with os.fdopen(descriptor, "w") as output:
                json.dump(state, output, indent=2, allow_nan=False)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return state


def clear_state(unit: str, revision: int, cwd: Path | None = None) -> None:
    if type(revision) is not int or revision < 1:
        raise ValueError("invalid checkpoint revision")
    path = state_path(unit, cwd)
    if not path.exists():
        return
    with locked(path):
        state = read_state(unit, cwd)
        if state and state["revision"] != revision:
            raise ValueError("stale checkpoint revision")
        if state and state["status"] != "completed":
            raise ValueError("cannot clear unfinished progress")
        path.unlink(missing_ok=True)


def resume_prompt(state: dict, host: str) -> str:
    validate(state, state["unit"], state["repository"])
    if host not in {"claude", "codex"}:
        raise ValueError("unknown host")
    if state["status"] == "completed":
        return "completed — no resume required"
    prefix = "/" if host == "claude" else "$"
    unit = "" if state["unit"].startswith("bare-") else state["unit"]
    resume_caller = LEGACY_CALLERS.get(state["caller"], state["caller"])
    if state["phase"] in {"cleanup", "reconciliation", "done"}:
        if resume_caller:
            return f"{prefix}minerva:{resume_caller} --cleanup-only {unit} --retry={state['cleanup_retry']}"
        return f"{prefix}minerva:cleanup {unit}"  # never invent --yes authorization
    caller = f" --auto={resume_caller}" if resume_caller else ""
    target = f" {unit}" if unit else ""
    return f"{prefix}minerva:ship{target} --watch-iteration={state['fix_iteration']}{caller}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--skill-file", type=Path, required=True)
    resolve.add_argument("--scripts")
    for operation in ("read", "write", "clear"):
        command = sub.add_parser(operation)
        command.add_argument("--unit", required=True)
        command.add_argument("--cwd", type=Path)
        if operation == "read":
            command.add_argument("--host", choices=("claude", "codex"))
        if operation == "clear":
            command.add_argument("--revision", type=int, required=True)
        if operation == "write":
            command.add_argument("--start-phase", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.operation == "resolve":
            print(resolve_scripts(args.skill_file, args.scripts))
        elif args.operation == "write":
            print(json.dumps(write_state(args.unit, json.load(sys.stdin), args.cwd, args.start_phase), indent=2))
        elif args.operation == "clear":
            clear_state(args.unit, args.revision, args.cwd)
        else:
            state = read_state(args.unit, args.cwd)
            print(resume_prompt(state, args.host) if args.host and state else json.dumps(state, indent=2))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(f"minerva-runtime: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
