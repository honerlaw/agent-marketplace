"""The lorestrom helper's work-unit, merge-evidence and reference functions (phase 2 foundation).

Pure functions are tested in-process through `tests/lorestrom_scripts.py`, so minerva's copies
of the shared modules never stand in; merge evidence runs real git in temporary repositories,
and the CLI is run as a subprocess from the plugin's own directory.
"""
import hashlib
import json
import subprocess
import sys

import pytest

from tests import lorestrom_scripts

backend = lorestrom_scripts.backend()
SCRIPT = lorestrom_scripts.SCRIPTS / "lorestrom_backend.py"

PROJECT = "33333333-3333-4333-8333-333333333333"
UNIT = "2026-11-23-add-thing"
DOC_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
DOC_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
DOC_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def commit(root, message="change"):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def run(root, *args, stdin=None):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--cwd", str(root), *args],
                          input=stdin, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "config", "core.excludesFile", str(tmp_path / "no-global-excludes"))
    (root / "app.py").write_text("one\n")
    commit(root, "init")
    return root


# --- keys ----------------------------------------------------------------------------------


def test_unit_and_record_keys_extend_the_project():
    key = backend.unit_key(PROJECT, UNIT)
    assert key == f"minerva:u/{PROJECT}/{UNIT}"
    assert backend.record_key(key, "proposal") == f"{key}/proposal"


@pytest.mark.parametrize("unit", ["", "add-thing", "2026-11-23-Add", "2026-11-23-a b",
                                  "2026-11-23-x;rm", "../2026-11-23-x", "2026-11-23-"])
def test_a_unit_key_takes_only_a_unit_id(unit):
    with pytest.raises(backend.BackendError):
        backend.unit_key(PROJECT, unit)


@pytest.mark.parametrize("record", ["notes", "../proposal", "Proposal", ""])
def test_a_record_key_takes_only_a_unit_record(record):
    with pytest.raises(backend.BackendError):
        backend.record_key(backend.unit_key(PROJECT, UNIT), record)


def test_a_record_key_needs_a_unit_key():
    with pytest.raises(backend.BackendError):
        backend.record_key(f"minerva:k/{PROJECT}/x", "proposal")


# --- unit state ----------------------------------------------------------------------------


def test_unit_state_reads_promotes_properties():
    got = backend.unit_state({"minerva:status": "Shipped (2026-11-23)",
                              "minerva:promoted": "2026-11-23", "minerva:state": "open"})
    assert got == {"promoted": True, "shipped": True, "state": "open", "refresh": None}


def test_the_gate_is_the_authority_and_a_stale_property_is_refreshed():
    got = backend.unit_state({"minerva:state": "open"}, "released")
    assert got["state"] == "released" and got["refresh"] == "released"
    assert backend.unit_state({"minerva:state": "released"}, "released")["refresh"] is None


@pytest.mark.parametrize("promoted", ["yes", "2026-11", True, 20261123])
def test_only_a_date_marks_a_unit_promoted(promoted):
    assert backend.unit_state({"minerva:promoted": promoted})["promoted"] is False


def test_an_unknown_gate_state_is_refused():
    with pytest.raises(backend.BackendError):
        backend.unit_state({}, "merged")


# --- release ---------------------------------------------------------------------------------


def test_a_release_call_that_returned_released():
    assert backend.release_outcome(None, None)["released"] is True


def test_a_double_release_is_success_once_get_gate_shows_it_released():
    assert backend.release_outcome("CONFLICT", "released") == {"released": True,
                                                               "by": "an earlier release"}


@pytest.mark.parametrize("code,gate", [("CONFLICT", "open"), ("CONFLICT", "abandoned"),
                                       ("CONFLICT", "releasing"), ("FORBIDDEN", "released"),
                                       ("NOT_FOUND", None)])
def test_any_other_refusal_is_a_failure_to_report(code, gate):
    assert backend.release_outcome(code, gate)["released"] is False


# --- repair ----------------------------------------------------------------------------------


def flip(doc, state="failed", code="STALE", status="current"):
    return {"write": {"op": "set_status", "id": doc, "status": status}, "state": state,
            "outcome": {"code": code} if code else None}


def test_repair_lists_only_failed_flips_whose_entry_is_still_draft():
    gate = {"state": "released", "writes": [
        flip(DOC_A),                                   # still draft: repair
        flip(DOC_B),                                   # superseded meanwhile: skip
        flip(DOC_C, state="applied", code=None),       # applied: nothing to do
        {"write": {"op": "set_title", "id": DOC_A, "title": "x"}, "state": "failed",
         "outcome": {"code": "STALE"}},                # not a flip
        flip(DOC_A, status="archived"),                # not a flip to current
    ]}
    docs = [{"id": DOC_A, "status": "draft"}, {"id": DOC_B, "status": "superseded"},
            {"id": DOC_C, "status": "current"}]
    got = backend.repair_flips(gate, docs)
    assert got["repair"] == [{"id": DOC_A, "code": "STALE"}]
    assert got["skipped"] == [{"id": DOC_B, "reason": "now superseded, not draft", "code": "STALE"}]


def test_repair_skips_an_entry_it_cannot_see():
    got = backend.repair_flips({"state": "released", "writes": [flip(DOC_A)]}, [])
    assert got["repair"] == [] and got["skipped"][0]["id"] == DOC_A


@pytest.mark.parametrize("state", ["open", "releasing", "abandoned"])
def test_repair_runs_only_after_release(state):
    with pytest.raises(backend.BackendError):
        backend.repair_flips({"state": state, "writes": [flip(DOC_A)]},
                             [{"id": DOC_A, "status": "draft"}])


# --- reconcile_action: the safety table ----------------------------------------------------

H1, H2 = "1" * 40, "2" * 40


def ev(phases=1, **kw):
    base = {"phases": phases, "heads": {}, "prs": {}, "ancestors": {}, "differs": {},
            "merge_tree": {}, "confirmed": {}, "abandon": False, "age_days": 0}
    base.update(kw)
    return base


def one(head=H1, **kw):
    return ev(heads={"1": head} if head else {}, differs={"1": True} if head else {}, **kw)


CASES = [
    # (name, evidence, action)
    ("fresh branch: no recorded head", ev(), "wait"),
    ("head equal to the base", ev(heads={"1": H1}, differs={"1": False}), "wait"),
    ("merged PR", one(prs={"1": "MERGED"}), "release"),
    ("head on the default branch, no gh", one(ancestors={"1": True}), "release"),
    ("squash merge without gh: merging changes nothing", one(merge_tree={"1": "noop"}), "confirm"),
    ("user named the merge commit", one(merge_tree={"1": "changes"}, confirmed={"1": True}), "release"),
    ("unmerged changes", one(merge_tree={"1": "changes"}), "wait"),
    ("conflict", one(merge_tree={"1": "conflict"}), "wait"),
    ("old git", one(merge_tree={"1": "unsupported"}), "wait"),
    ("head missing from this clone", one(merge_tree={"1": "missing"}), "wait"),
    ("open PR, even when merging changes nothing", one(prs={"1": "OPEN"}, merge_tree={"1": "noop"}), "wait"),
    ("closed PR", one(prs={"1": "CLOSED"}), "abandon"),
    ("closed PR with no head", ev(prs={"1": "CLOSED"}), "abandon"),
    ("explicit --abandon", one(prs={"1": "MERGED"}, abandon=True), "abandon"),
    ("stale: no head after 14 days still waits", ev(age_days=30), "wait"),
    ("phase 1 merged, phase 2 not started",
     ev(2, heads={"1": H1}, differs={"1": True}, prs={"1": "MERGED"}), "wait"),
    ("phase 1 merged, phase 2 open",
     ev(2, heads={"1": H1, "2": H2}, differs={"1": True, "2": True},
        prs={"1": "MERGED", "2": "OPEN"}), "wait"),
    ("every phase merged",
     ev(2, heads={"1": H1, "2": H2}, differs={"1": True, "2": True},
        prs={"1": "MERGED"}, ancestors={"2": True}), "release"),
    ("phase 2 squash-merged without gh",
     ev(2, heads={"1": H1, "2": H2}, differs={"1": True, "2": True},
        prs={"1": "MERGED"}, merge_tree={"2": "noop"}), "confirm"),
    ("a merged later phase does not release an unmerged earlier one",
     ev(2, heads={"1": H1, "2": H2}, differs={"1": True, "2": True},
        prs={"2": "MERGED"}, merge_tree={"1": "changes"}), "wait"),
]


@pytest.mark.parametrize("evidence,action", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_reconcile_action(evidence, action):
    assert backend.reconcile_action(evidence)["action"] == action


def test_staleness_is_flagged_and_never_abandons():
    got = backend.reconcile_action(ev(age_days=backend.STALE_DAYS))
    assert got["stale"] is True and got["action"] == "wait"
    assert backend.reconcile_action(ev(age_days=backend.STALE_DAYS - 1))["stale"] is False


def test_confirm_names_the_phases_to_confirm():
    got = backend.reconcile_action(one(merge_tree={"1": "noop"}))
    assert got["phasesToConfirm"] == ["1"]


@pytest.mark.parametrize("phases", [0, -1, "1", None, 21, 1.0])
def test_reconcile_needs_the_declared_phase_count(phases):
    with pytest.raises(backend.BackendError):
        backend.reconcile_action(ev(phases=phases))


# --- merge evidence from real git ------------------------------------------------------------


def branch_with_change(root, name, text="two\n"):
    git(root, "checkout", "-q", "-b", name)
    (root / "app.py").write_text(text)
    head = commit(root, f"change on {name}")
    git(root, "checkout", "-q", "main")
    return head


def evidence(root, **request):
    request.setdefault("phases", 1)
    return backend.merge_evidence(root, request)


def test_a_fresh_branch_waits(repo):
    base = git(repo, "rev-parse", "HEAD")
    got = evidence(repo, heads={"1": base}, base=base)
    assert got["decision"]["action"] == "wait"


def test_a_fast_forwarded_head_releases(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    git(repo, "merge", "-q", "--ff-only", "unit")
    assert evidence(repo, heads={"1": head}, base=base)["decision"]["action"] == "release"


def test_a_squash_merge_without_gh_asks_for_confirmation(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    git(repo, "merge", "-q", "--squash", "unit")
    commit(repo, "squash")
    got = evidence(repo, heads={"1": head}, base=base)
    assert got["evidence"]["merge_tree"]["1"] == "noop"
    assert got["decision"]["action"] == "confirm"


def test_the_user_naming_the_squash_commit_releases(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    git(repo, "merge", "-q", "--squash", "unit")
    squash = commit(repo, "squash")
    got = evidence(repo, heads={"1": head}, base=base, merged={"1": squash})
    assert got["decision"]["action"] == "release"


def test_a_named_commit_off_the_default_branch_confirms_nothing(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    got = evidence(repo, heads={"1": head}, base=base, merged={"1": head})
    assert got["evidence"]["confirmed"]["1"] is False
    assert got["decision"]["action"] == "wait"


def test_unmerged_changes_wait(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    got = evidence(repo, heads={"1": head}, base=base)
    assert got["evidence"]["merge_tree"]["1"] == "changes"
    assert got["decision"]["action"] == "wait"


def test_a_conflict_waits(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit", "theirs\n")
    (repo / "app.py").write_text("ours\n")
    commit(repo, "main moves on")
    got = evidence(repo, heads={"1": head}, base=base)
    assert got["evidence"]["merge_tree"]["1"] == "conflict"
    assert got["decision"]["action"] == "wait"


def test_a_head_this_clone_lacks_waits(repo):
    base = git(repo, "rev-parse", "HEAD")
    got = evidence(repo, heads={"1": "f" * 40}, base=base)
    assert got["evidence"]["merge_tree"]["1"] == "missing"
    assert got["decision"]["action"] == "wait"


@pytest.mark.parametrize("head", ["HEAD", "main", "--output=/tmp/x", "1" * 39, "G" * 40,
                                  "1" * 40 + "\n", None, 7])
def test_only_a_full_sha_reaches_git(repo, head):
    base = git(repo, "rev-parse", "HEAD")
    got = evidence(repo, heads={"1": head}, base=base)
    assert got["evidence"]["heads"] == {} and got["decision"]["action"] == "wait"


@pytest.mark.parametrize("base", ["HEAD", "main", "0" * 40, None])
def test_the_base_must_be_a_commit_here(repo, base):
    with pytest.raises(backend.BackendError):
        evidence(repo, heads={}, base=base)


def test_an_unknown_pr_state_counts_as_none(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    got = evidence(repo, heads={"1": head}, base=base, prs={"1": "merged; rm -rf"})
    assert got["evidence"]["prs"]["1"] is None


def test_the_default_branch_is_found_not_taken_from_input(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    git(repo, "merge", "-q", "--ff-only", "unit")
    got = evidence(repo, heads={"1": head}, base=base, default="refs/heads/unit")
    assert got["default"] == "refs/heads/main"


def test_reconcile_cli(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = branch_with_change(repo, "unit")
    git(repo, "merge", "-q", "--ff-only", "unit")
    request = {"phases": 1, "heads": {"1": head}, "base": base}
    result = run(repo, "reconcile", stdin=json.dumps(request))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"]["action"] == "release"


# --- reference docs --------------------------------------------------------------------------


def add_reference(root, rel, text):
    path = root / ".minerva" / "reference" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return path


def test_a_reference_payload_keeps_nested_paths_and_bytes():
    text = "# Architecture\r\n\r\nNow.\r\n"
    got = backend.reference_payload("ops/architecture.md", text, PROJECT)
    assert got["key"] == f"minerva:r/{PROJECT}/ops/architecture"
    assert got["kind"] == "minerva:reference" and got["title"] == "Architecture"
    assert got["markdown"] == text
    assert got["properties"]["minerva:digest"] == hashlib.sha256(text.encode()).hexdigest()
    assert got["properties"]["minerva:path"] == "ops/architecture.md"
    assert "edges" not in got


def test_a_reference_without_an_h1_is_titled_by_its_file_name():
    text = "```\n# not a title\n```\nbody\n"
    assert backend.reference_payload("glossary.md", text, PROJECT)["title"] == "glossary"


@pytest.mark.parametrize("rel", ["../x.md", "a/../b.md", "a b.md", "x.txt", "/abs.md",
                                 "a//b.md", "-x.md", "x;y.md"])
def test_a_reference_path_is_an_allowlist(rel):
    with pytest.raises(backend.BackendError):
        backend.reference_payload(rel, "# x\n", PROJECT)


def test_the_reference_list_walks_nested_docs_and_refuses_symlinks(repo, tmp_path):
    add_reference(repo, "architecture.md", "# Architecture\n")
    add_reference(repo, "ops/runbook.md", "# Runbook\r\n")
    outside = tmp_path / "secret"
    outside.mkdir()
    (outside / "leak.md").write_text("# Leak\n")
    (repo / ".minerva" / "reference" / "linked").symlink_to(outside, target_is_directory=True)
    (repo / ".minerva" / "reference" / "file.md").symlink_to(outside / "leak.md")
    add_reference(repo, "bad name.md", "# x\n")
    got = backend.reference_list(repo, PROJECT)
    assert [d["path"] for d in got["docs"]] == [".minerva/reference/architecture.md",
                                                ".minerva/reference/ops/runbook.md"]
    refused = {r["file"].strip("'") for r in got["refused"]}
    assert refused == {"bad name.md", "file.md", "linked"}


def test_a_symlinked_reference_directory_is_refused(repo, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (repo / ".minerva").mkdir()
    (repo / ".minerva" / "reference").symlink_to(outside, target_is_directory=True)
    with pytest.raises(backend.BackendError):
        backend.reference_list(repo, PROJECT)


def test_reference_payload_cli_checks_the_confirmed_digest(repo):
    text = "# Runbook\r\nsteps\r\n"
    add_reference(repo, "ops/runbook.md", text)
    digest = hashlib.sha256(text.encode()).hexdigest()
    ok = run(repo, "reference-payload", ".minerva/reference/ops/runbook.md",
             "--project", PROJECT, "--digest", digest)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["markdown"].encode() == text.encode()
    changed = run(repo, "reference-payload", ".minerva/reference/ops/runbook.md",
                  "--project", PROJECT, "--digest", "0" * 64)
    assert changed.returncode == 2 and "not what was confirmed" in changed.stderr


@pytest.mark.parametrize("file", ["app.py", ".minerva/reference/../../app.py",
                                  ".minerva/knowledge/x.md"])
def test_reference_payload_cli_reads_only_reference_docs(repo, file):
    add_reference(repo, "a.md", "# a\n")
    result = run(repo, "reference-payload", file, "--project", PROJECT, "--digest", "0" * 64)
    assert result.returncode == 2


def test_reference_payload_cli_refuses_a_symlinked_subdirectory(repo, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "x.md").write_text("# x\n")
    add_reference(repo, "a.md", "# a\n")
    (repo / ".minerva" / "reference" / "sub").symlink_to(outside, target_is_directory=True)
    digest = hashlib.sha256(b"# x\n").hexdigest()
    result = run(repo, "reference-payload", ".minerva/reference/sub/x.md",
                 "--project", PROJECT, "--digest", digest)
    assert result.returncode == 2 and "symlink" in result.stderr


@pytest.mark.parametrize("command,stdin,key", [
    ("unit-state", {"properties": {"minerva:state": "open"}, "gate": "released"}, "refresh"),
    ("release-outcome", {"code": "CONFLICT", "gate": "released"}, "released"),
    ("repair-flips", {"gate": {"state": "released", "writes": []}, "docs": []}, "repair"),
])
def test_unit_cli_commands(repo, command, stdin, key):
    result = run(repo, command, stdin=json.dumps(stdin))
    assert result.returncode == 0, result.stderr
    assert key in json.loads(result.stdout)


def test_reference_payload_cli_refuses_a_markdown_file_outside_the_directory(repo):
    add_reference(repo, "a.md", "# a\n")
    (repo / "notes.md").write_text("# private notes\n")
    digest = hashlib.sha256(b"# private notes\n").hexdigest()
    result = run(repo, "reference-payload", "notes.md", "--project", PROJECT, "--digest", digest)
    assert result.returncode == 2 and "is not in" in result.stderr
