"""Runtime behavior against consumer repos and installed copies, never live state."""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import minerva_runtime as runtime
from tests.test_skill_snippets import fenced_blocks

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "minerva"
UNIT = "2026-09-12-example"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def consumer(tmp_path):
    repo = tmp_path / "consumer project ' $literal"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "commit.gpgSign", "false")
    (repo / "README.md").write_text("fixture\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "fixture")
    knowledge = repo / ".minerva" / "knowledge"
    knowledge.mkdir(parents=True)
    (knowledge / "index.md").write_text("# Knowledge index\n\n## Decisions\n\n## Bugs\n\n## Patterns\n\n## Constraints\n\n## References\n")
    return repo


@pytest.fixture
def installed(tmp_path):
    dest = tmp_path / "installed plugin ' $literal"
    shutil.copytree(PLUGIN, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts}


def initial(**values):
    return dict(revision=0, branch=UNIT, caller="propose-ship-balanced", **values)


def test_missing_read_does_not_create_checkpoint_files(consumer):
    before = list(runtime.common_dir(consumer).rglob("*"))
    assert runtime.read_state(UNIT, consumer) is None
    assert list(runtime.common_dir(consumer).rglob("*")) == before


def test_write_read_and_complete_clear(consumer):
    before = snapshot(consumer)
    state = runtime.write_state(UNIT, initial(pr=12), consumer)
    assert state["revision"] == 1
    assert runtime.read_state(UNIT, consumer) == state
    assert runtime.state_path(UNIT, consumer).is_relative_to(runtime.common_dir(consumer))
    with pytest.raises(ValueError, match="unfinished"):
        runtime.clear_state(UNIT, 1, consumer)
    done = runtime.write_state(UNIT, dict(revision=1, phase="done", status="completed"), consumer)
    runtime.clear_state(UNIT, done["revision"], consumer)
    runtime.clear_state(UNIT, done["revision"], consumer)
    assert runtime.read_state(UNIT, consumer) is None
    assert snapshot(consumer) == before


def test_completed_checkpoint_requires_explicit_clear_before_new_run(consumer):
    state = runtime.write_state(UNIT, initial(phase="done", status="completed"), consumer)
    with pytest.raises(ValueError, match="clear completed"):
        runtime.write_state(UNIT, dict(revision=state["revision"], phase="ship", status="pending"), consumer)
    assert runtime.read_state(UNIT, consumer) == state


def test_next_phase_retains_aggregate_governance_and_renews_only_phase_budgets(consumer):
    done = runtime.write_state(UNIT, initial(phase="done", status="completed", pr=12,
                               fix_iteration=3, cleanup_retry=12, cleanup_deadline=1,
                               escalations=2, decisions=8, reviewers=4), consumer)
    assert runtime.resume_prompt(done, "codex") == "completed — no resume required"
    state = runtime.write_state(UNIT, dict(revision=1, branch=UNIT + "-phase-2"), consumer, start_phase=True)
    assert state["revision"] == 2
    assert state["caller"] == "propose-ship-balanced"
    assert (state["escalations"], state["decisions"], state["reviewers"]) == (2, 8, 4)
    assert (state["fix_iteration"], state["cleanup_retry"], state["cleanup_deadline"], state["pr"]) == (0, 0, None, None)


@pytest.mark.parametrize("update", [{}, {"branch": UNIT}, {"branch": UNIT + "-phase-2", "escalations": 0}])
def test_next_phase_cannot_reuse_branch_or_reset_global_budget(consumer, update):
    done = runtime.write_state(UNIT, initial(phase="done", status="completed", escalations=2), consumer)
    with pytest.raises(ValueError):
        runtime.write_state(UNIT, dict(revision=1, **update), consumer, start_phase=True)
    assert runtime.read_state(UNIT, consumer) == done


def test_new_phase_cannot_restart_unfinished_checkpoint(consumer):
    state = runtime.write_state(UNIT, initial(fix_iteration=3, cleanup_retry=12), consumer)
    with pytest.raises(ValueError, match="completed prior"):
        runtime.write_state(UNIT, dict(revision=1, branch=UNIT + "-phase-2"), consumer, start_phase=True)
    assert runtime.read_state(UNIT, consumer) == state


def test_unfinished_checkpoint_cannot_change_branch(consumer):
    state = runtime.write_state(UNIT, initial(), consumer)
    with pytest.raises(ValueError, match="original branch"):
        runtime.write_state(UNIT, dict(revision=state["revision"], branch="unrelated"), consumer)
    assert runtime.read_state(UNIT, consumer) == state


@pytest.mark.parametrize("revision", [True, 0, -1, "1"])
def test_clear_requires_integer_positive_revision(consumer, revision):
    runtime.write_state(UNIT, initial(phase="done", status="completed"), consumer)
    with pytest.raises(ValueError, match="invalid checkpoint revision"):
        runtime.clear_state(UNIT, revision, consumer)
    assert runtime.read_state(UNIT, consumer) is not None


def test_resolver_rejects_another_plugins_manifest(installed):
    for relative in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
        (installed / relative).write_text('{"name": "other"}')
    with pytest.raises(ValueError, match="Minerva plugin package"):
        runtime.resolve_scripts(installed / "skills/status/SKILL.md")


def test_required_module_inventory_matches_shipped_package():
    assert runtime.REQUIRED_MODULES == {p.name for p in (PLUGIN / "scripts").glob("*.py")}


def test_incomplete_installed_package_cannot_validate_itself(consumer, installed):
    (installed / "scripts/knowledge_lint.py").unlink()
    result = subprocess.run([sys.executable, str(installed / "scripts/minerva_runtime.py"),
                             "resolve", "--skill-file", str(installed / "skills/lint/SKILL.md")],
                            cwd=consumer, capture_output=True, text=True)
    assert result.returncode == 1
    assert "knowledge_lint.py" in result.stderr


def test_checkpoint_is_shared_across_linked_worktrees_and_survives_removal(consumer, tmp_path):
    worktree = tmp_path / "linked tree"
    git(consumer, "worktree", "add", "-b", UNIT, str(worktree))
    state = runtime.write_state(UNIT, initial(), worktree)
    assert runtime.read_state(UNIT, consumer) == state
    nested = worktree / "subdirectory"
    nested.mkdir()
    assert runtime.read_state(UNIT, nested) == state
    git(consumer, "worktree", "remove", "--force", str(worktree))
    assert runtime.read_state(UNIT, consumer) == state


@pytest.mark.parametrize("field,value", [
    ("fix_iteration", -1), ("fix_iteration", 4), ("cleanup_retry", 13),
    ("revision", True), ("decisions", 1.5), ("pr", 0), ("pr", True),
    ("phase", "invented"), ("status", "success"), ("caller", "someone-else"),
    ("cleanup_deadline", float("inf")), ("cleanup_deadline", float("nan")),
    ("cleanup_deadline", True), ("version", 2), ("version", True),
    ("repository", "/other/repo"), ("unit", "other-unit"), ("branch", ""),
    ("phase", "done"), ("status", "completed"),
])
def test_invalid_state_is_rejected(consumer, field, value):
    payload = initial()
    payload[field] = value
    with pytest.raises(ValueError):
        runtime.write_state(UNIT, payload, consumer)
    assert not runtime.state_path(UNIT, consumer).exists()


@pytest.mark.parametrize("unit", ["../escape", "foo/bar", "..", "foo..bar", "", "$(pwd)"])
def test_unit_cannot_escape_checkpoint_root(consumer, unit):
    with pytest.raises(ValueError):
        runtime.state_path(unit, consumer)


@pytest.mark.parametrize("update", [
    {"fix_iteration": 1}, {"cleanup_retry": 1}, {"escalations": 1},
    {"decisions": 1}, {"reviewers": 1}, {"caller": "propose-ship-quick"},
    {"cleanup_deadline": 9000}, {"cleanup_deadline": None},
])
def test_resume_preserves_counters_caller_and_deadline(consumer, update):
    runtime.write_state(UNIT, initial(fix_iteration=2, cleanup_retry=2, escalations=2,
                                    decisions=2, reviewers=2, cleanup_deadline=8000), consumer)
    original = runtime.state_path(UNIT, consumer).read_bytes()
    with pytest.raises(ValueError):
        runtime.write_state(UNIT, dict(revision=1, **update), consumer)
    assert runtime.state_path(UNIT, consumer).read_bytes() == original


def test_concurrent_checkpoint_writers_cannot_lose_progress(consumer):
    runtime.write_state(UNIT, initial(), consumer)
    def advance():
        try:
            return runtime.write_state(UNIT, dict(revision=1, decisions=1), consumer)
        except ValueError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: advance(), range(2)))
    assert sum(result is not None for result in results) == 1
    assert runtime.read_state(UNIT, consumer)["revision"] == 2


def test_corrupt_state_is_not_silently_reset(consumer):
    runtime.write_state(UNIT, initial(), consumer)
    runtime.state_path(UNIT, consumer).write_text("{invalid")
    with pytest.raises(ValueError, match="invalid checkpoint"):
        runtime.read_state(UNIT, consumer)
    with pytest.raises(ValueError):
        runtime.write_state(UNIT, initial(), consumer)


@pytest.mark.parametrize("host,prefix", [("claude", "/"), ("codex", "$")])
@pytest.mark.parametrize("phase", ["ship", "cleanup", "reconciliation"])
def test_resume_prompts_preserve_caller_and_budgets(consumer, host, prefix, phase):
    state = runtime.write_state(UNIT, initial(phase=phase, fix_iteration=2, cleanup_retry=5), consumer)
    prompt = runtime.resume_prompt(state, host)
    assert prompt.startswith(prefix + "minerva:")
    if phase == "ship":
        assert "--watch-iteration=2 --auto=propose-ship-balanced" in prompt
    else:
        assert f"propose-ship-balanced --cleanup-only {UNIT} --retry=5" in prompt
    assert "--yes" not in prompt


def test_standalone_cleanup_does_not_invent_authorization(consumer):
    state = runtime.write_state(UNIT, dict(revision=0, branch=UNIT, caller=None, phase="cleanup"), consumer)
    assert runtime.resume_prompt(state, "codex") == f"$minerva:cleanup {UNIT}"


def test_bare_shipping_key_is_not_rendered_as_a_work_unit(consumer):
    key = "bare-" + "a" * 64
    state = runtime.write_state(key, dict(revision=0, branch="user/feature", fix_iteration=2), consumer)
    assert runtime.resume_prompt(state, "codex") == "$minerva:ship --watch-iteration=2"


def test_resolves_installed_and_symlinked_skill_paths(consumer, installed, tmp_path, monkeypatch):
    monkeypatch.chdir(consumer)
    monkeypatch.delenv("MINERVA_SCRIPTS", raising=False)
    skill = installed / "skills" / "lint" / "SKILL.md"
    assert runtime.resolve_scripts(skill) == installed / "scripts"
    alias = tmp_path / "plugin symlink"
    alias.symlink_to(installed, target_is_directory=True)
    assert runtime.resolve_scripts(alias / "skills" / "lint" / "SKILL.md") == installed / "scripts"


def test_stale_install_requires_complete_explicit_override(consumer, installed, monkeypatch):
    monkeypatch.delenv("MINERVA_SCRIPTS", raising=False)
    local = consumer / "plugins" / "minerva" / "scripts"
    shutil.copytree(installed / "scripts", local)
    (local / "work_status.py").write_text("# deliberately different\n")
    monkeypatch.chdir(consumer)
    skill = installed / "skills" / "lint" / "SKILL.md"
    with pytest.raises(ValueError, match="stale"):
        runtime.resolve_scripts(skill)
    monkeypatch.setenv("MINERVA_SCRIPTS", str(local))
    assert runtime.resolve_scripts(skill) == local
    (local / "knowledge_spans.py").unlink()
    with pytest.raises(ValueError, match="incomplete"):
        runtime.resolve_scripts(skill)


@pytest.mark.parametrize("skill,signal", [
    ("lint", "severity"), ("migrate", "index_present"), ("synthesize", "unsynthesized"),
])
def test_shipped_read_only_signal_snippets_run_in_consumer_project(consumer, installed, skill, signal):
    knowledge = consumer / ".minerva" / "knowledge"
    (knowledge / "2026-09-12-decision-orphan.md").write_text(
        "# Orphan\n\n**Type**: decision\n\n**Summary**: fixture\n\n## Finding\n\nfixture\n")
    before = snapshot(consumer)
    document = installed / "skills" / skill / "SKILL.md"
    block = next(b for b in fenced_blocks(document, "bash") if "python3 -c" in b)
    env = {**os.environ, "MINERVA_PLUGIN_ROOT": str(installed), "MINERVA_SKILL_FILE": str(document)}
    env.pop("MINERVA_SCRIPTS", None)
    nested = consumer / "nested"
    nested.mkdir()
    result = subprocess.run(["bash", "-c", block], cwd=nested, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert signal in result.stdout
    assert snapshot(consumer) == before


def test_cli_stdin_checkpoint_and_resume(consumer, installed):
    script = installed / "scripts" / "minerva_runtime.py"
    result = subprocess.run([sys.executable, str(script), "write", "--unit", UNIT],
                            input=json.dumps(initial()), cwd=consumer, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["revision"] == 1
    result = subprocess.run([sys.executable, str(script), "read", "--unit", UNIT, "--host", "codex"],
                            cwd=consumer, capture_output=True, text=True)
    assert result.stdout.strip() == f"$minerva:ship {UNIT} --watch-iteration=0 --auto=propose-ship-balanced"


@pytest.mark.parametrize("location", ["root", "nested", "linked"])
@pytest.mark.parametrize("skill", ["ship", "cleanup", "propose"])
def test_shipped_phase_snippets_resolve_installed_code_and_primary_unit_paths(
        consumer, installed, location, skill):
    worktree = consumer / ".minerva/worktrees" / UNIT
    git(consumer, "worktree", "add", "-b", UNIT, str(worktree))
    unit = worktree / ".minerva/work" / UNIT
    unit.mkdir(parents=True)
    (unit / "proposal.md").write_text("# Proposal\n\n## Phases\n\n1. **Addition** — Fix addition.\n2. **Docs** — Document operators.\n")
    document = installed / "skills" / skill / "references" / {
        "ship": "protocol.md", "cleanup": "phased-units.md", "propose": "on-approval.md"}[skill]
    blocks = fenced_blocks(document, "bash", contains="from work_status import read_phases")
    assert len(blocks) == 1
    block = blocks[0].replace("<date-slug>", UNIT).replace("<default-branch>", "main").replace("<default>", "main")
    cwd = consumer if location == "root" else worktree if location == "linked" else consumer / "nested"
    cwd.mkdir(exist_ok=True)
    env = {**os.environ, "MINERVA_PLUGIN_ROOT": str(installed),
           "MINERVA_SKILL_FILE": str(installed / "skills" / skill / "SKILL.md")}
    env.pop("MINERVA_SCRIPTS", None)
    before = snapshot(consumer)
    result = subprocess.run(["bash", "-c", block], cwd=cwd, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Addition" in result.stdout if skill == "propose" else UNIT in result.stdout
    assert snapshot(consumer) == before


@pytest.mark.parametrize("location", ["root", "nested", "linked"])
def test_shipped_status_fragments_aggregate_primary_checkout_from_each_location(
        consumer, installed, tmp_path, location):
    unit = consumer / ".minerva/work" / UNIT
    unit.mkdir(parents=True)
    (unit / "proposal.md").write_text("# Proposal\n\n**Status**: Draft\n\n## Goal\n\nFixture.\n")
    worktree = consumer / ".minerva/worktrees" / UNIT
    git(consumer, "worktree", "add", "-b", UNIT, str(worktree))
    git(consumer, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    document = installed / "skills/status/SKILL.md"
    blocks = fenced_blocks(document, "bash")
    setup = next(b for b in blocks if "WORK_ROOT=" in b)
    merged = next(b for b in blocks if "MERGED=" in b)
    aggregate = next(b for b in blocks if "from workstream_status" in b)
    binary = tmp_path / "bin"
    binary.mkdir()
    shutil.copyfile(PLUGIN.parents[1] / "evals/compatibility/gh_stub.py", binary / "gh")
    (binary / "gh").chmod(0o755)
    env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
           "MINERVA_FIXTURE_ROOT": str(consumer), "MINERVA_PLUGIN_ROOT": str(installed),
           "MINERVA_SKILL_FILE": str(document)}
    env.pop("MINERVA_SCRIPTS", None)
    cwd = consumer if location == "root" else worktree if location == "linked" else consumer / "nested"
    cwd.mkdir(exist_ok=True)
    before = snapshot(consumer)
    result = subprocess.run(["bash", "-c", "\n".join((setup, merged, aggregate))],
                            cwd=cwd, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert len(report["units"]) == 1
    assert report["units"][0]["slug"] == UNIT
    assert snapshot(consumer) == before
    assert not (runtime.common_dir(consumer) / "minerva/runtime").exists()


@pytest.mark.parametrize("pr", [None, 99])
def test_recorded_work_pr_cannot_be_replaced_during_reconciliation(consumer, pr):
    state = runtime.write_state(UNIT, initial(pr=12), consumer)
    with pytest.raises(ValueError, match="original work PR"):
        runtime.write_state(UNIT, dict(revision=1, pr=pr, phase="reconciliation"), consumer)
    assert runtime.read_state(UNIT, consumer) == state
