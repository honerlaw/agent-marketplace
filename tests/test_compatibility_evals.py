"""Exercise isolated host fixtures and acceptance gates without model calls."""
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_compatibility_evals as runner
import minerva_runtime as runtime
from work_status import read_phases, phase_progress


def gh(repo, env, *args):
    binary = Path(env["PATH"].split(":")[0]) / "gh"
    return subprocess.run([str(binary), *args], cwd=repo, env=env,
                          capture_output=True, text=True)


@pytest.mark.parametrize("scenario", runner.SCENARIOS)
def test_each_fixture_is_local_and_uses_complete_installed_package(tmp_path, scenario):
    repo, installed, env = runner.fixture(tmp_path, scenario)
    assert runner.git(repo, "remote", "get-url", "origin") == str(tmp_path / "local remote.git")
    assert runtime.resolve_scripts(installed / "skills/status/SKILL.md") == installed / "scripts"
    assert repo not in installed.parents
    assert gh(repo, env, "repo", "view").returncode == 0
    assert json.loads(gh(repo, env, "repo", "view").stdout)["hasIssuesEnabled"] is False


def test_phased_fixture_uses_real_phase_parser_and_keeps_second_phase_unimplemented(tmp_path):
    repo, _, _ = runner.fixture(tmp_path, "phased")
    proposal = repo / ".minerva/worktrees/2026-09-12-fixture/.minerva/work/2026-09-12-fixture/proposal.md"
    phases = read_phases(proposal.read_text())
    assert len(phases) == 2
    progress = phase_progress(phases, ["main"], "2026-09-12-fixture")
    assert progress["next_branch"] == "2026-09-12-fixture"
    assert not progress["complete"]


def test_reconciliation_fixture_has_merged_work_pr_and_uncatalogued_entry(tmp_path):
    repo, _, env = runner.fixture(tmp_path, "reconciliation")
    assert json.loads(gh(repo, env, "pr", "view", "1").stdout)["state"] == "MERGED"
    assert (repo / ".minerva/knowledge/2026-09-12-bug-addition.md").is_file()
    assert "[[2026-09-12-bug-addition]]" not in (repo / ".minerva/knowledge/index.md").read_text()


@pytest.mark.parametrize("bucket,code", [("pending", 8), ("cancel", 1), ("fail", 1), ("unknown", 1)])
def test_fixture_never_merges_non_green_ci(tmp_path, bucket, code):
    repo, _, env = runner.fixture(tmp_path, "manual-resume")
    env["MINERVA_FIXTURE_CHECK_BUCKET"] = bucket
    assert gh(repo, env, "pr", "checks", "1", "--json", "name,bucket,state").returncode == code
    assert gh(repo, env, "pr", "merge", "--auto", "--squash", "1").returncode == 1
    assert json.loads(gh(repo, env, "pr", "view", "1").stdout)["state"] == "OPEN"


def test_fixture_duplicate_pr_and_repeated_merge_are_idempotent(tmp_path):
    repo, _, env = runner.fixture(tmp_path, "manual-resume")
    assert gh(repo, env, "pr", "create", "--title", "Duplicate").returncode == 1
    runner.git(repo, "switch", "main")
    env["MINERVA_FIXTURE_CHECK_BUCKET"] = "pass"
    for _ in range(2):
        assert gh(repo, env, "pr", "merge", "--auto", "--squash", "1").returncode == 0
    state = json.loads((repo / ".git/fixture-github.json").read_text())
    assert len(state["prs"]) == 1
    assert [a["action"] for a in state["actions"]] == ["create", "merge"]


def test_unknown_fixture_commands_fail_closed(tmp_path):
    repo, _, env = runner.fixture(tmp_path, "read-only")
    assert gh(repo, env, "issue", "create", "--title", "Unexpected").returncode == 2
    assert not (repo / ".git/fixture-github.json").exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_plain_narration_cannot_prove_independent_dispatch(host):
    event = {"type": "result", "result": "I dispatched three independent agents using spawn_agent."}
    assert runner.transcript_output(host, json.dumps(event)) == (event["result"], 0)
    assert runner.transcript_output(host, "not JSON") == ("", 0)


def test_transcripts_count_real_host_dispatches_and_final_output():
    claude = json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Agent", "input": {"model": "sonnet"}}]}})
    assert runner.transcript_output("claude", claude)[1] == 1
    codex = json.dumps({"type": "item.completed", "item": {
        "type": "collab_agent_tool_call", "tool": "spawn_agent", "status": "completed"}})
    assert runner.transcript_output("codex", codex)[1] == 1
    pending = codex.replace('"completed"}', '"in_progress"}')
    assert runner.transcript_output("codex", pending)[1] == 0


@pytest.mark.parametrize("output", ["", json.dumps({"type": "result", "result": "Done"})])
def test_empty_or_tool_free_host_run_cannot_pass_read_only_acceptance(tmp_path, monkeypatch, output):
    monkeypatch.setattr(runner.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path))
    monkeypatch.setattr(runner.shutil, "which", lambda tool: "/fixture/" + tool)
    actual_run = runner.subprocess.run
    def stub(command, **kwargs):
        if command[0] in {"codex", "claude"}:
            assert "--dangerously-bypass-approvals-and-sandbox" not in command
            return SimpleNamespace(returncode=0, stdout=output, stderr="")
        return actual_run(command, **kwargs)
    monkeypatch.setattr(runner.subprocess, "run", stub)
    report = runner.run("codex", "read-only")
    assert not report["passed"]
    assert not report["checks"]["fixture_gh_observed"]
    assert (tmp_path / "report.json").is_file()


def test_timeout_keeps_diagnostic_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path))
    monkeypatch.setattr(runner.shutil, "which", lambda tool: "/fixture/" + tool)
    actual_run = runner.subprocess.run
    def stub(command, **kwargs):
        if command[0] == "codex":
            raise subprocess.TimeoutExpired(command, 1, output=b"partial output", stderr=b"diagnostic")
        return actual_run(command, **kwargs)
    monkeypatch.setattr(runner.subprocess, "run", stub)
    with pytest.raises(ValueError, match="artifacts"):
        runner.run("codex", "read-only", timeout=1)
    assert (tmp_path / "stdout.txt").read_text() == "partial output"
    assert (tmp_path / "stderr.txt").read_text() == "diagnostic"


def test_dry_run_does_not_launch_hosts_or_make_fixtures(monkeypatch, capsys):
    monkeypatch.setattr(runner, "run", lambda *args: pytest.fail("host launched"))
    assert runner.main(["--host", "both", "--scenario", "auto", "--dry-run"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2


@pytest.mark.parametrize("fork,model,has_result,expected", [
    ("none", None, True, 1), ("all", None, True, 0),
    ("none", "sonnet", True, 0), ("none", None, False, 0),
])
def test_codex_raw_evidence_requires_fresh_inherited_dispatch_and_tool_result(
        tmp_path, fork, model, has_result, expected):
    thread = "01a0985e-bffc-7542-90db-e47d901c211c"
    repo = tmp_path / "consumer"
    repo.mkdir()
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    args = dict(fork_turns=fork, message="Do not export this prompt")
    if model:
        args["model"] = model
    records = [
        dict(type="session_meta", payload=dict(id=thread, cwd=str(repo))),
        dict(type="response_item", payload=dict(type="function_call", name="spawn_agent",
             namespace="collaboration", arguments=json.dumps(args), call_id="fixture-call")),
    ]
    if has_result:
        records.append(dict(type="response_item", payload=dict(type="function_call_output", call_id="fixture-call", output="opaque")))
    path = sessions / f"rollout-{thread}.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records))
    output = json.dumps(dict(type="thread.started", thread_id=thread))
    evidence = runner.codex_dispatch_evidence(output, repo, sessions)
    assert len(evidence) == expected
    assert "Do not export this prompt" not in json.dumps(evidence)
    assert runner.codex_dispatch_evidence(output, tmp_path / "other", sessions) == []


def test_missing_raw_session_or_invalid_thread_never_counts_dispatch(tmp_path):
    for thread in ("../escape", "01a0985e-bffc-7542-90db-e47d901c211c"):
        assert runner.codex_dispatch_evidence(json.dumps(dict(type="thread.started", thread_id=thread)), tmp_path, tmp_path) == []


def test_resume_fixture_retains_identity_budgets_and_local_only_remote(tmp_path):
    directory = tmp_path / "minerva-codex-auto-small-fixture"
    directory.mkdir()
    repo, _, _ = runner.fixture(directory, "manual-resume")
    runtime.write_state("2026-09-12-fixture", dict(revision=0,
                        branch="2026-09-12-fixture", caller="propose-ship-auto",
                        pr=1, fix_iteration=2, escalations=2), repo)
    before = runner.snapshot(repo)
    resumed, _, env, request = runner.resume_fixture(directory, "codex", "auto-small")
    assert resumed == repo.resolve()
    assert "--watch-iteration=2 --auto=propose-ship-auto" in request
    assert "Do not restart intake" in request
    assert runner.snapshot(repo) == before
    assert runtime.read_state("2026-09-12-fixture", repo)["escalations"] == 2
    runner.git(repo, "remote", "set-url", "origin", "https://example.invalid/unapproved")
    with pytest.raises(ValueError, match="local bare remote"):
        runner.resume_fixture(directory, "codex", "auto-small")


def test_resume_fixture_rejects_other_host_or_missing_checkpoint(tmp_path):
    directory = tmp_path / "minerva-codex-auto-small-fixture"
    directory.mkdir()
    runner.fixture(directory, "manual-resume")
    with pytest.raises(ValueError, match="matching runner fixture"):
        runner.resume_fixture(directory, "claude", "auto-small")
    with pytest.raises(ValueError, match="exactly one"):
        runner.resume_fixture(directory, "codex", "auto-small")
