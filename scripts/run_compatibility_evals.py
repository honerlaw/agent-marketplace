#!/usr/bin/env python3
"""Opt-in host conformance runs in isolated local fixtures; no live GitHub mutations.

This is artifact/action acceptance, not the provisional skill-value delta runner.
The local CLI still uses the user's normal authentication and may incur model cost.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "minerva"
SCENARIOS = {
    "read-only": ("Use minerva:status, minerva:lint, minerva:migrate, minerva:debug and minerva:explore to inspect this fixture. Explain the calculator behavior and wiki shape. Do not fix anything, write files, or hand off to proposal authoring.", False),
    "quick": ("Use minerva:propose-ship-quick to correct calculator.add and ship the full lifecycle. The goal and approach are approved: add returns a+b; tests must pass. No open questions. Local commits, local pushes, fixture PRs, merge and single-unit cleanup are authorized. Do not ask for routine confirmations.", True),
    "balanced": ("Use minerva:propose-ship-balanced to correct calculator.add and ship the full lifecycle. The goal and approach are approved: add returns a+b; tests must pass. Use its independent reviewer gates. Local commits, local pushes, fixture PRs, merge and single-unit cleanup are authorized.", True),
    "auto": ("Use minerva:propose-ship-auto to correct calculator.add. Goal, local commits/pushes/fixture PRs/merge/cleanup are authorized. Preserve the strategic and completion panel gates; do not treat preapproval as permission to skip independent verification.", True),
    "human": ("Use minerva:propose-ship to design an addition fix. Before writing a proposal, present the next unresolved decision using its user gate and stop to await the answer. No implementation or shipping is authorized yet.", False),
    "init": ("Use minerva:init --host both to scaffold missing directories and routing in both host instruction files. Those changes are approved; do not commit them, replace unrelated content, or create duplicate routing sections.", True),
    "replan": ("Use minerva:replan to inspect the fixture proposal. The new direction is not decided: the caller needs a choice between a strict integer-only API and Python operator-compatible addition. Present the next user question and stop before writing a divergence entry.", False),
    "grill": ("Use minerva:grill-plan on the fixture proposal. Present one unresolved design question with your recommended answer and stop for the user; do not write anything or fabricate their answer.", False),
    "phased": ("Use minerva:ship 2026-09-12-fixture to ship the implemented first phase, then invoke cleanup only after its PR merges. Local commit/push/fixture PR/merge/cleanup are approved. Phase 2 is outstanding and must not ship or be marked complete. Keep the worktree for phase 2 and name its resume trigger.", True),
    "reconciliation": ("Use minerva:cleanup 2026-09-12-fixture --yes. The work PR is already merged and the scratchpad promoted. Remove only its merged worktree, reconcile the pending knowledge entry via its separate fixture PR, and preserve the proposal. Local commits/pushes/fixture PRs/merge and cleanup are approved.", True),
    "cancelled-ci": ("Use minerva:ship 2026-09-12-fixture --watch-iteration=3 --auto=propose-ship-quick. Checks are cancelled: checkpoint blocked, report recovery, do not begin another fix, merge, or mark CI green. All prior fix attempts were consumed.", False),
    "exhausted-cleanup": ("Use minerva:propose-ship-quick --cleanup-only 2026-09-12-fixture --retry=12. The work PR is still open with auto-merge enabled. The saved deadline has expired. Report exhaustion and manual recovery without scheduling or deleting the worktree. Do not reset the saved budgets.", False),
    "panel": ("Use minerva:round-table to decide whether calculator.add should return a+b, supported by the supplied test. Convene its independent panel and report the vote. Do not modify any files.", False),
    "review": ("Use minerva:review to review the current calculator implementation and test as a local changeset. Report findings and suggest dispositions, but do not apply fixes or write triage files without further approval.", False),
    "manual-resume": ("Use minerva:ship to resume the already-open fixture PR, --watch-iteration=2 --auto=propose-ship-quick. CI is pending. Scheduling is unavailable; checkpoint progress and return pending with an exact Codex/Claude resume prompt. Do not fix, merge, or claim a wake is scheduled.", False),
}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def snapshot(repo):
    return {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob("*")
            if p.is_file() and not {".git", "__pycache__"}.intersection(p.relative_to(repo).parts)}


def fixture(directory: Path, scenario: str):
    repo = directory / "consumer project"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Minerva Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "commit.gpgSign", "false")
    (repo / "calculator.py").write_text("def add(a, b):\n    return a - b\n")
    (repo / "test_calculator.py").write_text("import unittest\nfrom calculator import add\n\nclass Addition(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n")
    (repo / ".gitignore").write_text(".minerva/worktrees/\n__pycache__/\n")
    knowledge = repo / ".minerva" / "knowledge"
    knowledge.mkdir(parents=True)
    (knowledge / "index.md").write_text("# Knowledge index\n\n## Decisions\n\n## Bugs\n\n## Patterns\n\n## Constraints\n\n## References\n")
    (repo / ".minerva/work").mkdir()
    (repo / ".minerva/reference").mkdir()
    for name in ("CLAUDE.md", "AGENTS.md"):
        (repo / name).write_text("This is an isolated Minerva compatibility fixture. Only this repository and its local remote may be mutated.\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture")
    remote = directory / "local remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], capture_output=True, check=True)
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    installed = directory / "installed minerva"
    shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))
    binary = directory / "bin"
    binary.mkdir()
    shutil.copyfile(REPO / "evals/compatibility/gh_stub.py", binary / "gh")
    (binary / "gh").chmod(0o755)
    env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
           "MINERVA_FIXTURE_ROOT": str(repo)}
    env.pop("MINERVA_SCRIPTS", None)
    if scenario in {"review", "manual-resume", "replan", "grill", "cancelled-ci", "exhausted-cleanup", "phased", "reconciliation"}:
        git(repo, "switch", "-c", "2026-09-12-fixture")
        (repo / "calculator.py").write_text("def add(a, b):\n    return a + b\n")
        git(repo, "add", "calculator.py")
        git(repo, "commit", "-m", "fix addition")
    if scenario in {"manual-resume", "replan", "grill", "cancelled-ci", "exhausted-cleanup", "phased", "reconciliation"}:
        unit = repo / ".minerva/work/2026-09-12-fixture"
        unit.mkdir()
        (unit / "proposal.md").write_text("# Proposal: fixture\n\n**Status**: Draft\n\n## Goal\n\nCorrect addition.\n\n## Success criteria\n\n- Addition tests pass.\n")
        git(repo, "add", ".minerva/work/2026-09-12-fixture/proposal.md")
        git(repo, "commit", "-m", "record fixture work unit")
        git(repo, "push", "-u", "origin", "2026-09-12-fixture")
        subprocess.run([str(binary / "gh"), "pr", "create", "--title", "Fixture"],
                       cwd=repo, env=env, capture_output=True, check=True)
        if scenario in {"manual-resume", "exhausted-cleanup"}:
            env["MINERVA_FIXTURE_CHECK_BUCKET"] = "pending"
        if scenario == "cancelled-ci":
            env["MINERVA_FIXTURE_CHECK_BUCKET"] = "cancel"
        if scenario == "exhausted-cleanup":
            sys.path.insert(0, str(PLUGIN / "scripts"))
            from minerva_runtime import write_state
            write_state("2026-09-12-fixture", dict(revision=0, branch="2026-09-12-fixture",
                        caller="propose-ship-quick", phase="cleanup", pr=1, cleanup_retry=12,
                        cleanup_deadline=1), repo)
            state_path = repo / ".git/fixture-github.json"
            state = json.loads(state_path.read_text())
            state["prs"][0]["autoMergeRequest"] = {"enabled": True}
            state_path.write_text(json.dumps(state))
        if scenario in {"phased", "reconciliation"}:
            git(repo, "switch", "main")
            worktree = repo / ".minerva/worktrees/2026-09-12-fixture"
            git(repo, "worktree", "add", str(worktree), "2026-09-12-fixture")
            proposal = worktree / ".minerva/work/2026-09-12-fixture/proposal.md"
            if scenario == "phased":
                proposal.write_text(proposal.read_text() + "\n## Phases\n\n1. **Addition** — Implement addition.\n2. **Documentation** — Document supported operators. Not implemented yet.\n")
            else:
                entry = worktree / ".minerva/knowledge/2026-09-12-bug-addition.md"
                entry.write_text("# Addition uses addition\n\n**Date**: 2026-09-12\n**Type**: Bug\n**Summary**: Addition was corrected to use the plus operator.\n**Context**: .minerva/work/2026-09-12-fixture/proposal.md\n\n## Finding\n\nThe addition function returned subtraction; it now returns a+b.\n\n## Related\n\n")
                (proposal.parent / "scratchpad.md").write_text("Promoted.\n")
            git(worktree, "add", ".minerva")
            git(worktree, "commit", "-m", "record phase or promoted entry")
            if scenario == "reconciliation":
                subprocess.run([str(binary / "gh"), "pr", "merge", "--auto", "--squash", "1"],
                               cwd=worktree, env=env, check=True, capture_output=True)
    return repo, installed, env


def transcript_output(host: str, output: str):
    """Extract final text and actual tool events; narration is not dispatch proof."""
    events = []
    final = []
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if not isinstance(value, dict):
            continue
        events.append(value)
        if value.get("type") == "result" and isinstance(value.get("result"), str):
            final.append(value["result"])
        item = value.get("item", {})
        if isinstance(item, dict) and item.get("type") == "agent_message":
            final.append(item.get("text", ""))
    def dispatches(value):
        if isinstance(value, list):
            return sum(dispatches(item) for item in value)
        if not isinstance(value, dict):
            return 0
        if value.get("type") == "tool_use" and value.get("name") in {"Agent", "spawn_agent", "collaboration.spawn_agent"}:
            return 1
        if value.get("type") in {"collab_agent_tool_call", "collab_tool_call"} and value.get("tool") == "spawn_agent" and value.get("status") == "completed":
            return 1
        return sum(dispatches(item) for item in value.values() if isinstance(item, (dict, list)))
    return "\n".join(final), sum(dispatches(event) for event in events)


def codex_dispatch_evidence(output: str, repo: Path, sessions: Path | None = None):
    """Read only this fixture's raw tool records when JSON stdout omits dispatches.

    Some CLI builds emit collaboration waits but omit collaboration.spawn_agent.
    Export only call identities/settings, never prompts or unrelated session data.
    """
    thread = None
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "thread.started":
            thread = event.get("thread_id")
            break
    if not isinstance(thread, str) or not re.fullmatch(r"[0-9a-f-]{36}", thread):
        return []
    sessions = sessions or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions"
    paths = list(sessions.rglob(f"*-{thread}.jsonl"))
    if len(paths) != 1:
        return []
    records = [json.loads(line) for line in paths[0].read_text().splitlines()]
    metadata = next((r.get("payload", {}) for r in records if r.get("type") == "session_meta"), {})
    if metadata.get("id") != thread or Path(metadata.get("cwd", "/")).resolve() != repo.resolve():
        return []
    results = {r.get("payload", {}).get("call_id") for r in records
               if r.get("payload", {}).get("type") == "function_call_output"}
    evidence = []
    for record in records:
        call = record.get("payload", {})
        if call.get("type") != "function_call" or call.get("name") != "spawn_agent":
            continue
        arguments = json.loads(call.get("arguments", "{}"))
        if call.get("call_id") not in results or arguments.get("fork_turns") != "none":
            continue
        if arguments.get("model") is not None or arguments.get("reasoning_effort") is not None:
            continue
        evidence.append(dict(call_id=call["call_id"], fork_turns="none", model="inherited", tool_result=True))
    return evidence


def resume_fixture(directory: Path, host: str, scenario: str):
    """Continue only a runner-owned local fixture with an existing checkpoint."""
    directory = directory.resolve()
    if not directory.name.startswith(f"minerva-{host}-{scenario}-"):
        raise ValueError("resume path must be a matching runner fixture")
    if Path(tempfile.gettempdir()).resolve() not in directory.parents:
        raise ValueError("resume fixture must be under the temporary directory")
    repo, installed = directory / "consumer project", directory / "installed minerva"
    if Path(git(repo, "remote", "get-url", "origin")).resolve() != directory / "local remote.git":
        raise ValueError("resume fixture must use its own local bare remote")
    if not (repo / ".git/fixture-github.json").is_file():
        raise ValueError("resume fixture has no recorded fixture PR")
    checkpoints = list((repo / ".git/minerva/runtime").glob("*/run.json"))
    if len(checkpoints) != 1:
        raise ValueError("resume fixture requires exactly one lifecycle checkpoint")
    sys.path.insert(0, str(PLUGIN / "scripts"))
    from minerva_runtime import read_state, resume_prompt
    state = read_state(checkpoints[0].parent.name, repo)
    if state["status"] == "completed":
        raise ValueError("fixture is already completed")
    # Always use the shipped stub, including when a previous run used an older copy.
    shutil.copyfile(REPO / "evals/compatibility/gh_stub.py", directory / "bin/gh")
    (directory / "bin/gh").chmod(0o755)
    env = {**os.environ, "PATH": str(directory / "bin") + os.pathsep + os.environ["PATH"],
           "MINERVA_FIXTURE_ROOT": str(repo)}
    env.pop("MINERVA_SCRIPTS", None)
    request = (f"Resume this existing lifecycle with {resume_prompt(state, host)}. "
               "The original goal and local commits, pushes, fixture PRs, merge, and single-unit cleanup remain authorized. "
               "Preserve all saved budgets. Do not restart intake or create another work unit. "
               "Complete the orchestrator handback and reconciliation, then report the final result.")
    return repo, installed, env, request


def run(host: str, scenario: str, timeout: int = 600, resume_directory: Path | None = None):
    if not shutil.which(host):
        raise ValueError(f"{host} CLI is unavailable")
    request, mutating = SCENARIOS[scenario]
    if resume_directory:
        if scenario not in {"quick", "balanced", "auto", "reconciliation"}:
            raise ValueError("fixture continuation is supported for lifecycle scenarios only")
        directory = resume_directory.resolve()
        repo, installed, env, request = resume_fixture(directory, host, scenario)
    else:
        directory = Path(tempfile.mkdtemp(prefix=f"minerva-{host}-{scenario}-"))
        repo, installed, env = fixture(directory, scenario)
    before = snapshot(repo)
    installed_before = snapshot(installed)
    refs_before = git(repo, "show-ref")
    head_before = git(repo, "rev-parse", "HEAD")
    prompt = f"""{request}

The installed Minerva plugin is at {installed}. Read its requested SKILL.md and
required runtime/host references from this package before executing. Use the
{host} adapter. Do not use a different installed Minerva copy. When loading a
skill, preserve its arguments. Available gh is a local fixture CLI: all changes
stay in this disposable Git repository; origin is a disposable local bare repo.
No external GitHub requests, installs, user-config edits, or deployments are
authorized. Use python3 -m unittest for tests. Return concrete findings/results.
Scheduling is unavailable in this fixture. Do not modify the installed plugin.
Login shells may reset PATH. For EVERY shell call using gh, prepend
PATH={shlex.quote(str(directory / 'bin'))}:"$PATH"; alternatively invoke
{shlex.quote(str(directory / 'bin/gh'))} by absolute path. Never call system gh.
This local fixture authorizes independent subagents wherever the requested
skill explicitly requires delegation. Stop with recovery if no such API exists.
"""
    if host == "codex":
        command = ["codex", "exec", "--json", "--cd", str(repo), "--approve-for-me", "--add-dir", str(directory / "local remote.git"), "-"]
    else:
        command = ["claude", "-p", "--plugin-dir", str(installed), "--output-format", "stream-json", "--verbose", prompt]
        env.pop("CLAUDECODE", None)
    prefix = "resume-" if resume_directory else ""
    try:
        result = subprocess.run(command, input=prompt if host == "codex" else None,
                                cwd=repo, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        for name, content in (("stdout.txt", exc.stdout), ("stderr.txt", exc.stderr)):
            (directory / f"{prefix}{name}").write_text(content.decode(errors="replace") if isinstance(content, bytes) else content or "")
        raise ValueError(f"{host} timed out after {timeout}s; artifacts: {directory}") from exc
    (directory / f"{prefix}stdout.txt").write_text(result.stdout)
    (directory / f"{prefix}stderr.txt").write_text(result.stderr)
    if result.returncode:
        raise ValueError(f"{host} failed ({result.returncode}); artifacts: {directory}; {result.stderr[-500:]}")
    final, dispatches = transcript_output(host, result.stdout)
    if host == "codex" and scenario in {"panel", "review", "balanced", "auto"}:
        evidence = codex_dispatch_evidence(result.stdout, repo)
        (directory / "dispatch-evidence.json").write_text(json.dumps(evidence, indent=2))
        dispatches = max(dispatches, len(evidence))
    if resume_directory and scenario in {"balanced", "auto"} and (directory / "stdout.txt").exists():
        previous_output = (directory / "stdout.txt").read_text()
        _, previous_dispatches = transcript_output(host, previous_output)
        if host == "codex":
            previous_dispatches = max(previous_dispatches, len(codex_dispatch_evidence(previous_output, repo)))
        dispatches += previous_dispatches
    after = snapshot(repo)
    actions_path = repo / ".git/fixture-github.json"
    actions = json.loads(actions_path.read_text()) if actions_path.exists() else {"prs": [], "actions": []}
    checks = {}
    checks["nonempty_final_response"] = bool(final.strip())
    checks["installed_package_unchanged"] = snapshot(installed) == installed_before
    calls_path = repo / ".git/fixture-gh-calls.jsonl"
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()] if calls_path.exists() else []
    if scenario in {"read-only", "quick", "balanced", "auto", "manual-resume", "phased", "reconciliation", "cancelled-ci", "exhausted-cleanup"}:
        checks["fixture_gh_observed"] = len(calls) > (1 if scenario in {"manual-resume", "cancelled-ci", "exhausted-cleanup", "phased", "reconciliation"} else 0)
    if not mutating:
        checks["working_tree_unchanged"] = before == after
        checks["git_refs_unchanged"] = git(repo, "show-ref") == refs_before and git(repo, "rev-parse", "HEAD") == head_before
        checks["no_remote_mutations"] = len(actions["actions"]) == (1 if scenario in {"manual-resume", "cancelled-ci", "exhausted-cleanup", "replan", "grill"} else 0)
    if mutating and scenario != "init":
        tests = subprocess.run([sys.executable, "-m", "unittest"], cwd=repo, capture_output=True)
        checks["tests_pass"] = tests.returncode == 0
        checks["one_pr_per_branch"] = len({p["headRefName"] for p in actions["prs"]}) == len(actions["prs"])
        checks["work_pr_merged"] = any(p["state"] == "MERGED" and p["headRefName"] != "minerva/reconcile" for p in actions["prs"])
        checks["proposal_preserved"] = bool(list((repo / ".minerva/work").glob("*/proposal.md")))
    if scenario == "manual-resume":
        checkpoints = list((repo / ".git/minerva/runtime").glob("*/run.json"))
        states = [json.loads(p.read_text()) for p in checkpoints]
        checks["pending_checkpoint"] = any(s["status"] == "pending" and s["fix_iteration"] == 2 and s["caller"] == "propose-ship-quick" for s in states)
        checks["manual_resume_reported"] = "manual resume" in final.lower() or "manual resumption" in final.lower()
    if scenario == "init":
        checks["both_routing_sections"] = all((repo / name).read_text().count("## minerva") == 1 for name in ("CLAUDE.md", "AGENTS.md"))
        checks["canonical_index_preserved"] = (repo / ".minerva/knowledge/index.md").read_bytes() == before[".minerva/knowledge/index.md"]
        checks["original_host_instructions_preserved"] = all(before[name] in (repo / name).read_bytes() for name in ("CLAUDE.md", "AGENTS.md"))
    if scenario == "phased":
        checks["worktree_retained"] = (repo / ".minerva/worktrees/2026-09-12-fixture").is_dir()
        checks["phase_2_not_shipped"] = not any("phase-2" in p["headRefName"] for p in actions["prs"])
        checks["outstanding_phase_reported"] = "phase 2" in final.lower() or "documentation" in final.lower()
    if scenario == "reconciliation":
        checks["pending_entry_catalogued"] = "[[2026-09-12-bug-addition]]" in (repo / ".minerva/knowledge/index.md").read_text()
        checks["reconciliation_pr_merged"] = any(p["state"] == "MERGED" and p["headRefName"] == "minerva/reconcile" for p in actions["prs"])
    if scenario in {"cancelled-ci", "exhausted-cleanup"}:
        states = [json.loads(p.read_text()) for p in (repo / ".git/minerva/runtime").glob("*/run.json")]
        checks["budget_preserved"] = any(s["fix_iteration"] == 3 if scenario == "cancelled-ci" else s["cleanup_retry"] == 12 and s["cleanup_deadline"] == 1 for s in states)
        checks["manual_recovery_reported"] = any(word in final.lower() for word in ("manual", "blocked", "exhausted"))
    if scenario in {"human", "replan", "grill"}:
        checks["user_decision_pending"] = "?" in final and not list((repo / ".minerva/work").glob("*/replan.md"))
    if scenario in {"panel", "review", "balanced", "auto"}:
        checks["independent_dispatches_observed"] = dispatches >= {"panel": 3, "review": 1, "balanced": 4, "auto": 3}[scenario]
    report = dict(host=host, scenario=scenario, passed=all(checks.values()), checks=checks, artifacts=str(directory))
    (directory / f"{prefix}report.json").write_text(json.dumps(report, indent=2))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), required=True)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="read-only")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume-fixture", type=Path, help="Continue a timed-out local lifecycle fixture from its checkpoint")
    args = parser.parse_args(argv)
    hosts = ["claude", "codex"] if args.host == "both" else [args.host]
    try:
        if args.timeout < 1:
            raise ValueError("timeout must be positive")
        if args.dry_run:
            print(json.dumps([dict(host=h, scenario=args.scenario, request=SCENARIOS[args.scenario][0]) for h in hosts], indent=2))
            return 0
        if args.resume_fixture and len(hosts) != 1:
            raise ValueError("fixture continuation requires one explicit host")
        reports = [run(h, args.scenario, args.timeout, args.resume_fixture) for h in hosts]
        print(json.dumps(reports, indent=2))
        return 0 if all(r["passed"] for r in reports) else 1
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"compatibility-evals: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
