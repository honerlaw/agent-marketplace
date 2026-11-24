#!/usr/bin/env python3
"""Installed-script resolution and versioned, untracked lifecycle checkpoints for lorestrom.

`resolve` validates that a skill file belongs to a lorestrom package, that its scripts
directory holds every shipped module, and that it is not a stale copy of the scripts being
edited. Checkpoints live under `<git-common-dir>/lorestrom/runtime/<unit>/run.json`, apart
from minerva's. Read/resolve never create files. Writes use revision checks under a per-unit
lock and atomic replacement. A checkpoint is evidence of progress, not authorization.
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

PLUGIN = "lorestrom"
STATE_DIR = "lorestrom"
REQUIRED_MODULES = {
    "knowledge_lint.py", "knowledge_spans.py", "lorestrom_backend.py",
    "lorestrom_runtime.py", "plugin_guard.py", "work_status.py",
}
VERSION = 1
COUNTERS = ("fix_iteration", "cleanup_retry", "escalations", "decisions", "reviewers")
PHASES = {"ship", "cleanup", "done"}
FIELDS = {"version", "repository", "unit", "revision", "branch", "caller", "phase",
          "pr", "cleanup_deadline", "status", *COUNTERS}
# The orchestrators arrive in 0.3.0; until then every checkpoint's caller is null.
CALLERS = {None, "propose-ship", "propose-ship-auto"}


def canonical_caller(caller):
    return caller


def resolve_scripts(skill_file: Path, override=None) -> Path:
    skill_file = skill_file.expanduser().resolve(strict=True)
    if skill_file.name != "SKILL.md" or skill_file.parent.parent.name != "skills":
        raise ValueError("expected an installed skills/<name>/SKILL.md")
    root = skill_file.parents[2]
    manifests = [root / d / "plugin.json" for d in (".claude-plugin", ".codex-plugin")]
    values = [json.loads(p.read_text(encoding="utf-8")) for p in manifests if p.is_file()]
    if not any(isinstance(value, dict) and value.get("name") == PLUGIN for value in values):
        raise ValueError("skill is not inside a lorestrom plugin package")
    choice = override if override is not None else os.environ.get("LORESTROM_SCRIPTS")
    scripts = Path(choice).expanduser().resolve(strict=True) if choice else root / "scripts"
    missing = sorted(name for name in REQUIRED_MODULES if not (scripts / name).is_file())
    if missing:
        raise ValueError(f"incomplete scripts directory {scripts}: missing {', '.join(missing)}")
    if not choice and divergence(scripts, working_tree_root()):
        raise ValueError("stale installed scripts; update lorestrom or explicitly set LORESTROM_SCRIPTS")
    return scripts.resolve()


def common_dir(cwd: Path | None = None) -> Path:
    cwd = (cwd or Path.cwd()).resolve()
    result = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=cwd,
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError("lifecycle checkpoints require a Git repository")
    return (cwd / result.stdout.strip()).resolve()


# A unit id is also a branch name and a directory name, and the repository it comes from may
# not be the user's, so only ids of this shape are ever used (`units`, `state_path`).
UNIT_ID_RE = re.compile(r"(?:\d{4}-\d{2}-\d{2}|\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*")
BARE_KEY_RE = re.compile(r"bare-[0-9a-f]{64}")
UNIT_BRANCH_RE = re.compile(r"(?:\d{4}-\d{2}-\d{2}|\d{3})-")
PHASE_BRANCH_RE = re.compile(r"-phase-\d+$")


def is_unit_id(name: str) -> bool:
    """The helper's unit-id shape (`lorestrom_backend.UNIT_ID_RE`), so both agree on a name."""
    return isinstance(name, str) and UNIT_ID_RE.fullmatch(name) is not None


def is_checkpoint_key(name: str) -> bool:
    return is_unit_id(name) or (isinstance(name, str) and BARE_KEY_RE.fullmatch(name) is not None)


def state_path(unit: str, cwd: Path | None = None) -> Path:
    if not is_checkpoint_key(unit):
        raise ValueError("unit must be a work-unit id or a bare-ship key, not a path")
    return common_dir(cwd) / STATE_DIR / "runtime" / unit / "run.json"


def unit_ids(cwd: Path | None = None) -> dict:
    """Every work-unit id this project holds that is safe to use, and how many were refused.

    Reads names only: the `.lorestrom/worktrees` directory of the primary checkout and of this
    working tree (or of `cwd` outside Git), and local branches shaped like a unit id
    (`YYYY-MM-DD-…` or `NNN-…`, not a `-phase-N` branch), so a unit whose worktree is gone can
    still be cleaned up. Records live in Lorestrom: an id read from a unit doc is checked by
    the helper's `unit-ids`. A refused name is counted, never printed; a directory that cannot
    be read is counted as unreadable.
    """
    cwd = (cwd or Path.cwd()).resolve()
    try:
        common = common_dir(cwd)
    except ValueError:
        common = None
    roots = {cwd} if common is None else set()
    if common is not None:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd,
                             capture_output=True, text=True).stdout.strip()
        roots |= {Path(top)} if top else set()
        if common.name == ".git":
            roots.add(common.parent)
    found, refused, unreadable = set(), set(), 0

    def entries(directory: Path) -> list:
        nonlocal unreadable
        try:
            return sorted(directory.iterdir()) if directory.is_dir() else []
        except OSError:
            unreadable += 1
            return []

    for root in sorted(roots):
        worktrees = entries(root / ".lorestrom" / "worktrees")
        for entry in worktrees:
            if entry.is_dir():
                (found if is_unit_id(entry.name) else refused).add(entry.name)
    if common is not None:
        branches = subprocess.run(["git", "for-each-ref", "--format=%(refname:lstrip=2)", "refs/heads/"],
                                  cwd=cwd, capture_output=True, text=True).stdout.split()  # ref names hold no whitespace
        for name in branches:
            if UNIT_BRANCH_RE.match(name) and not PHASE_BRANCH_RE.search(name):
                (found if is_unit_id(name) else refused).add(name)
    return {"units": sorted(found), "refused": len(refused), "unreadable": unreadable}


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
            if canonical_caller(state["caller"]) != canonical_caller(previous["caller"]):
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


def unit_token(unit: str, cwd: Path | None = None, new: bool = False) -> str:
    """The operation token a unit doc carries, so a half-created unit is recognised as ours.

    Saved before the unit doc is created, under the unit's runtime directory; `new` refuses
    to replace a token that exists, so a retry reads the same one.
    """
    path = state_path(unit, cwd).parent / "token"
    if path.exists():
        if new:
            raise ValueError("this unit already has an operation token; read it instead")
        token = path.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            raise ValueError("this unit's operation token is damaged: recover with the user")
        return token
    if not new:
        raise ValueError("no operation token for this unit")
    import secrets
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(16)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(token + "\n")
    return token


def resume_prompt(state: dict, host: str) -> str:
    validate(state, state["unit"], state["repository"])
    if host not in {"claude", "codex"}:
        raise ValueError("unknown host")
    if state["status"] == "completed":
        return "completed — no resume required"
    prefix = "/" if host == "claude" else "$"
    unit = "" if state["unit"].startswith("bare-") else state["unit"]
    resume_caller = canonical_caller(state["caller"])
    if state["phase"] in {"cleanup", "done"}:
        if resume_caller:
            return f"{prefix}lorestrom:{resume_caller} --cleanup-only {unit} --retry={state['cleanup_retry']}"
        return f"{prefix}lorestrom:cleanup {unit}"  # never invent --yes authorization
    caller = f" --auto={resume_caller}" if resume_caller else ""
    target = f" {unit}" if unit else ""
    return f"{prefix}lorestrom:ship{target} --watch-iteration={state['fix_iteration']}{caller}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--skill-file", type=Path, required=True)
    resolve.add_argument("--scripts")
    units = sub.add_parser("units", help="the safe work-unit ids in this project")
    units.add_argument("--cwd", type=Path)
    token = sub.add_parser("token", help="a unit's operation token (--new creates it)")
    token.add_argument("--unit", required=True)
    token.add_argument("--cwd", type=Path)
    token.add_argument("--new", action="store_true")
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
        elif args.operation == "token":
            print(unit_token(args.unit, args.cwd, args.new))
        elif args.operation == "units":
            print(json.dumps(unit_ids(args.cwd), indent=2))
        elif args.operation == "clear":
            clear_state(args.unit, args.revision, args.cwd)
        else:
            state = read_state(args.unit, args.cwd)
            print(resume_prompt(state, args.host) if args.host and state else json.dumps(state, indent=2))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(f"lorestrom-runtime: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
