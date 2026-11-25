"""The lorestrom helper's migration commands: listing, planning and removing minerva's units.

Pure functions run in-process through `tests/lorestrom_scripts.py`, so minerva's copies of the
shared modules never stand in; the CLI runs as a subprocess from the plugin's own directory.
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

from tests import lorestrom_scripts

backend = lorestrom_scripts.backend()
SCRIPT = lorestrom_scripts.SCRIPTS / "lorestrom_backend.py"

PROJECT = "33333333-3333-4333-8333-333333333333"
DONE = "2026-01-02-shipped-thing"
DRAFT = "2026-01-03-draft-thing"
UNIT_DOC = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
RECORD_DOC = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

PROPOSAL = "# Proposal: shipped-thing\n\n**Date**: 2026-01-02\n**Status**: Shipped (2026-01-05)\n"
SCRATCHPAD = "# Scratchpad\n\nSummarized at minerva:promote on 2026-01-04 — see archive/.\n"


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


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "config", "core.excludesFile", str(tmp_path / "no-global-excludes"))
    work = f".minerva/work/{DONE}"
    write(root, f"{work}/proposal.md", PROPOSAL)
    write(root, f"{work}/scratchpad.md", SCRATCHPAD)
    write(root, f"{work}/archive/scratchpad.md", "# Scratchpad\n\nnotes\n")
    write(root, f"{work}/spike.py", "print(1)\n")
    write(root, f".minerva/work/{DRAFT}/proposal.md", "# Proposal: draft\n\n**Status**: Draft\n")
    write(root, ".minerva/adrs/001-x.md", "# ADR\n")
    commit(root, "init")
    return root


def listed(root, unit):
    return next(row for row in backend.unit_import_list(root, PROJECT, batch=100)["batch"]
                if row["id"] == unit)


# --- keys ----------------------------------------------------------------------------------


def test_a_unit_file_key_takes_standard_and_path_named_records():
    unit = backend.unit_key(PROJECT, DONE)
    assert backend.unit_file_key(unit, "proposal") == f"{unit}/proposal"
    assert backend.unit_file_key(unit, "archive/scratchpad") == f"{unit}/archive/scratchpad"


@pytest.mark.parametrize("name", ["", "../proposal", "archive/../x", "a//b", "/a", "a/",
                                  ".hidden", "a b", "x;rm", "archive/.."])
def test_a_unit_file_key_refuses_unsafe_paths(name):
    with pytest.raises(backend.BackendError):
        backend.unit_file_key(backend.unit_key(PROJECT, DONE), name)


def test_a_unit_file_key_needs_a_unit_key():
    with pytest.raises(backend.BackendError):
        backend.unit_file_key(f"minerva:k/{PROJECT}/x", "proposal")


def test_record_key_still_takes_only_the_standard_records():
    with pytest.raises(backend.BackendError):
        backend.record_key(backend.unit_key(PROJECT, DONE), "archive/scratchpad")


def test_records_differing_only_in_case_are_both_refused():
    rows = [{"path": "a/Notes.md", "record": "Notes"}, {"path": "a/notes.md", "record": "notes"},
            {"path": "a/proposal.md", "record": "proposal"}]
    kept, refused = backend.distinct_records(rows)
    assert [row["record"] for row in kept] == ["proposal"]
    assert sorted(row["record"] for row in refused) == ["Notes", "notes"]


# --- listing -------------------------------------------------------------------------------


def test_the_listing_reads_a_finished_unit(repo):
    row = listed(repo, DONE)
    assert row["inFlight"] is False
    assert row["status"] == "Shipped (2026-01-05)"
    assert row["promoted"] == "2026-01-04"
    assert row["doc"]["title"] == "Proposal: shipped-thing"
    assert row["doc"]["markdown"].startswith("minerva-import: ")
    props = row["doc"]["properties"]
    assert props["minerva:unit"] == DONE and props["minerva:project"] == PROJECT
    assert props["minerva:imported"] == git(repo, "rev-parse", "HEAD")
    assert [f["record"] for f in row["files"]] == ["archive/scratchpad", "proposal", "scratchpad"]
    assert row["files"][1]["digest"] == digest(PROPOSAL)
    assert row["files"][1]["key"] == f"minerva:u/{PROJECT}/{DONE}/proposal"
    assert [r["reason"] for r in row["refused"]] == ["not markdown: Lorestrom stores markdown only"]


def test_the_listing_marks_a_draft_unit_in_flight(repo):
    assert backend.unit_import_list(repo, PROJECT)["inFlight"] == [DRAFT]


def test_the_listing_refuses_what_it_cannot_send(repo):
    work = repo / ".minerva" / "work"
    write(repo, f".minerva/work/{DONE}/latin1.md", "x")
    (work / DONE / "latin1.md").write_bytes(b"caf\xe9\n")
    os.symlink(repo / "outside.md", work / DONE / "link.md")
    write(repo, "outside.md", "secret\n")
    (work / "notes").mkdir()
    write(repo, ".minerva/work/followups.md", "x\n")
    os.symlink(work / DONE, work / "2026-01-09-linked")
    out = backend.unit_import_list(repo, PROJECT)
    assert {row["file"]: row["reason"] for row in out["refused"]} == {
        ".minerva/work/2026-01-09-linked": "a symlink: the import does not follow it",
        ".minerva/work/followups.md": "not a unit directory",
        ".minerva/work/notes": "not a work-unit id",
    }
    reasons = {r["file"].rsplit("/", 1)[-1]: r["reason"] for r in listed(repo, DONE)["refused"]}
    assert reasons["latin1.md"] == "'latin1.md' is not UTF-8 text"
    assert reasons["link.md"].startswith("a symlink")


def test_the_listing_reports_minerva_worktrees(repo):
    (repo / ".minerva" / "worktrees" / DRAFT).mkdir(parents=True)
    assert backend.unit_import_list(repo, PROJECT)["worktrees"] == [DRAFT]


def test_the_listing_batches_in_id_order(repo):
    for day in range(10, 14):
        write(repo, f".minerva/work/2026-01-{day}-more/proposal.md", PROPOSAL)
    first = backend.unit_import_list(repo, PROJECT, batch=2)
    assert [row["id"] for row in first["batch"]] == [DONE, DRAFT]
    assert first["units"] == 6 and first["next"] == "2026-01-10-more"
    second = backend.unit_import_list(repo, PROJECT, batch=2, after=DRAFT)
    assert [row["id"] for row in second["batch"]] == ["2026-01-10-more", "2026-01-11-more"]
    last = backend.unit_import_list(repo, PROJECT, batch=10, after="2026-01-12-more")
    assert [row["id"] for row in last["batch"]] == ["2026-01-13-more"] and last["next"] is None


@pytest.mark.parametrize("after", ["../x", "x y"])
def test_the_listing_takes_only_a_unit_id_to_start_after(repo, after):
    with pytest.raises(backend.BackendError):
        backend.unit_import_list(repo, PROJECT, after=after)


def test_a_promoted_date_falls_back_to_the_status_then_the_id():
    assert backend._promoted_date("Summarized at minerva:promote — see archive/.\n",
                                  "Shipped (2026-02-03)", DONE) == "2026-02-03"
    assert backend._promoted_date(None, "Shipped", DONE) == "2026-01-02"
    assert backend._promoted_date(None, None, "001-legacy") is None


# --- record payloads -----------------------------------------------------------------------


def test_record_payload_builds_a_records_inputs(repo):
    out = run(repo, "record-payload", f".minerva/work/{DONE}/archive/scratchpad.md",
              "--project", PROJECT, "--digest", digest("# Scratchpad\n\nnotes\n"))
    assert out.returncode == 0, out.stderr
    payload = json.loads(out.stdout)
    assert payload["key"] == f"minerva:u/{PROJECT}/{DONE}/archive/scratchpad"
    assert payload["kind"] == "minerva:record"
    assert payload["unit"] == f"minerva:u/{PROJECT}/{DONE}"
    assert payload["properties"]["minerva:record"] == "archive/scratchpad"
    assert payload["properties"]["minerva:path"] == f".minerva/work/{DONE}/archive/scratchpad.md"
    assert payload["markdown"] == "# Scratchpad\n\nnotes\n"


def test_record_payload_refuses_a_file_changed_since_listing(repo):
    out = run(repo, "record-payload", f".minerva/work/{DONE}/proposal.md",
              "--project", PROJECT, "--digest", "0" * 64)
    assert out.returncode == 2 and "not what was listed" in out.stderr


@pytest.mark.parametrize("file", ["outside.md", ".minerva/adrs/001-x.md",
                                  f".minerva/work/{DONE}/spike.py",
                                  f".minerva/work/{DONE}/../{DRAFT}/../../../outside.md"])
def test_record_payload_reads_only_unit_markdown(repo, file):
    write(repo, "outside.md", "x\n")
    out = run(repo, "record-payload", file, "--project", PROJECT, "--digest", digest("x\n"))
    assert out.returncode == 2


def test_record_payload_does_not_follow_a_symlinked_directory(repo):
    os.symlink(repo / ".minerva" / "adrs", repo / ".minerva" / "work" / DONE / "linked")
    out = run(repo, "record-payload", f".minerva/work/{DONE}/linked/001-x.md",
              "--project", PROJECT, "--digest", digest("# ADR\n"))
    assert out.returncode == 2 and "symlinks" in out.stderr


# --- planning ------------------------------------------------------------------------------


def unit_doc(imported=True, doc_id=UNIT_DOC, unit=DONE):
    props = {"minerva:unit": unit, "minerva:project": PROJECT}
    if imported:
        props["minerva:imported"] = "f" * 40
    return {"id": doc_id, "key": f"minerva:u/{PROJECT}/{unit}", "kind": "minerva:work_unit",
            "status": "draft", "properties": props}


def records(repo, unit=DONE, status="current", skip=(), digests=None):
    rows = []
    for row in listed(repo, unit)["files"]:
        if row["record"] in skip:
            continue
        props = {"minerva:record": row["record"]}
        value = (digests or {}).get(row["record"], row["digest"])
        if value is not None:
            props["minerva:digest"] = value
        rows.append({"id": RECORD_DOC, "key": row["key"], "kind": "minerva:record",
                     "status": status, "properties": props})
    return rows


def plan(repo, units, abandon=()):
    return {row["id"]: row for row in backend.unit_import_plan(
        repo, PROJECT, {"units": units, "abandon": list(abandon)})["units"]}


def test_a_unit_with_no_doc_is_created(repo):
    row = plan(repo, [{"id": DONE, "docs": [], "gate": None, "records": []}])[DONE]
    assert row["action"] == "create" and row["close"] == "release" and row["openGate"]
    assert [f["record"] for f in row["send"]] == ["archive/scratchpad", "proposal", "scratchpad"]
    assert row["doc"]["key"] == f"minerva:u/{PROJECT}/{DONE}"


def test_an_in_flight_unit_is_blocked_until_the_user_says_abandon(repo):
    lookup = [{"id": DRAFT, "docs": [], "gate": None, "records": []}]
    assert plan(repo, lookup)[DRAFT]["action"] == "blocked"
    row = plan(repo, lookup, abandon=[DRAFT])[DRAFT]
    assert row["action"] == "create" and row["close"] == "abandon"


def test_a_key_held_by_a_unit_the_import_did_not_create_is_taken(repo):
    row = plan(repo, [{"id": DONE, "docs": [unit_doc(imported=False)], "gate": "open",
                       "records": []}])[DONE]
    assert row["action"] == "taken" and not row["send"] and not row["removable"]


def test_the_body_marker_proves_an_interrupted_create_is_ours(repo):
    row = plan(repo, [{"id": DONE, "docs": [unit_doc(imported=False)], "gate": None,
                       "records": [], "marker": "minerva-import: " + "f" * 40}])[DONE]
    assert row["action"] == "resume" and row["properties"] and row["openGate"]
    assert len(row["send"]) == 3


def test_resume_sends_missing_records_and_finishes_unpropertied_ones(repo):
    found = records(repo, skip=("proposal",), digests={"scratchpad": None})
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": {"state": "open"},
                       "records": found}])[DONE]
    assert row["action"] == "resume" and not row["openGate"] and row["close"] == "release"
    assert [f["record"] for f in row["send"]] == ["proposal"]
    assert [f["record"] for f in row["finish"]] == ["scratchpad"]


def test_a_released_import_with_every_record_is_done_and_removable(repo):
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released",
                       "records": records(repo)}])[DONE]
    assert row["action"] == "done" and row["doc"] is None
    assert row["removable"] == [f".minerva/work/{DONE}/archive/scratchpad.md",
                                f".minerva/work/{DONE}/proposal.md",
                                f".minerva/work/{DONE}/scratchpad.md"]


def test_a_record_edited_in_lorestrom_is_changed_never_resent(repo):
    found = records(repo, digests={"proposal": "e" * 64})
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released",
                       "records": found}])[DONE]
    assert row["action"] == "changed" and not row["send"]
    assert [(f["record"], f["reason"]) for f in row["changed"]] == [
        ("proposal", "changed in Lorestrom since import")]
    assert f".minerva/work/{DONE}/proposal.md" not in row["removable"]


def test_a_record_missing_after_release_is_changed(repo):
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released",
                       "records": records(repo, skip=("proposal",))}])[DONE]
    assert row["action"] == "changed"
    assert [f["reason"] for f in row["changed"]] == ["no record holds it"]


def test_an_abandoned_import_is_done_with_archived_records(repo):
    lookup = [{"id": DRAFT, "docs": [unit_doc(unit=DRAFT)], "gate": "abandoned",
               "records": records(repo, unit=DRAFT, status="archived")}]
    row = plan(repo, lookup, abandon=[DRAFT])[DRAFT]
    assert row["action"] == "done"
    assert row["removable"] == [f".minerva/work/{DRAFT}/proposal.md"]


def test_a_released_record_not_current_is_changed_with_its_status(repo):
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released",
                       "records": records(repo, status="draft")}])[DONE]
    assert row["action"] == "changed" and row["removable"] == []
    assert {f["reason"] for f in row["changed"]} == {"its record is draft"}


def test_an_imported_in_flight_unit_is_decided_without_a_new_yes(repo):
    """Removal reads the plan with no `abandon` list: a closed import is still done."""
    lookup = [{"id": DRAFT, "docs": [unit_doc(unit=DRAFT)], "gate": "abandoned",
               "records": records(repo, unit=DRAFT, status="archived")}]
    assert plan(repo, lookup)[DRAFT]["action"] == "done"
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    assert f".minerva/work/{DRAFT}/proposal.md" in result["remove"]


def test_an_open_import_of_an_in_flight_unit_stays_blocked_without_the_yes(repo):
    lookup = [{"id": DRAFT, "docs": [unit_doc(unit=DRAFT)], "gate": "open",
               "records": []}]
    row = plan(repo, lookup)[DRAFT]
    assert row["action"] == "blocked" and row["send"] == [] and row["unitDoc"] == UNIT_DOC


def test_what_a_removal_leaves_of_a_unit_is_not_live_work(repo):
    work = f".minerva/work/{DONE}"
    git(repo, "rm", "-q", "-r", f"{work}/proposal.md", f"{work}/scratchpad.md", f"{work}/archive")
    commit(repo, "remove")
    listing = backend.unit_import_list(repo, PROJECT, batch=100)
    assert DONE not in listing["inFlight"]
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released", "records": []}])
    assert row[DONE]["action"] == "done"


def test_an_unfinished_record_is_finished_and_a_finished_one_on_an_open_gate_is_related(repo):
    found = records(repo, digests={"scratchpad": None})
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "open", "records": found}])[DONE]
    assert [f["record"] for f in row["finish"]] == ["scratchpad"]
    assert [f["record"] for f in row["relate"]] == ["archive/scratchpad", "proposal"]
    assert all(f["docId"] == RECORD_DOC for f in row["finish"] + row["relate"])


def test_an_unfinished_record_after_the_gate_closed_is_changed(repo):
    found = records(repo, digests={"scratchpad": None})
    row = plan(repo, [{"id": DONE, "docs": [unit_doc()], "gate": "released",
                       "records": found}])[DONE]
    reasons = {f["record"]: f["reason"] for f in row["changed"]}
    assert reasons == {"scratchpad": "its record was never finished"}


def test_a_marker_needs_the_unit_doc_it_came_from(repo):
    with pytest.raises(backend.BackendError):
        plan(repo, [{"id": DONE, "docs": [], "gate": None, "records": [],
                     "marker": "minerva-import: " + "f" * 40}])


@pytest.mark.parametrize("value", [{"units": [{"id": "../x"}]}, {"units": "x"},
                                   {"units": [], "abandon": ["x y"]},
                                   {"units": [{"id": "2026-01-01-absent"}]},
                                   {"units": [{"id": DONE, "gate": "merged"}]}])
def test_the_plan_refuses_bad_input(repo, value):
    with pytest.raises(backend.BackendError):
        backend.unit_import_plan(repo, PROJECT, value)


def test_an_imported_unit_reads_as_finished():
    props = {"minerva:status": "Shipped (2026-01-05)", "minerva:promoted": "2026-01-04",
             "minerva:state": "open"}
    state = backend.unit_state(props, "released")
    assert state["promoted"] and state["shipped"] and state["state"] == "released"
    assert not state["stale"] and state["refresh"] == "released"


# --- removal -------------------------------------------------------------------------------


def test_removal_takes_done_units_and_keeps_everything_else(repo):
    lookup = [{"id": DONE, "docs": [unit_doc()], "gate": "released", "records": records(repo)}]
    out = run(repo, "removal-plan", "--project", PROJECT,
              stdin=json.dumps({"docs": [], "units": lookup}))
    assert out.returncode == 0, out.stderr
    result = json.loads(out.stdout)
    assert result["remove"] == [f".minerva/work/{DONE}/archive/scratchpad.md",
                                f".minerva/work/{DONE}/proposal.md",
                                f".minerva/work/{DONE}/scratchpad.md"]
    assert {row["path"] for row in result["keep"]} == {f".minerva/work/{DONE}/spike.py",
                                                      ".minerva/adrs/001-x.md"}
    assert result["notChecked"] == {"units": 1, "files": 1}
    assert result["unitsRemaining"] == 1


def test_removal_keeps_a_changed_records_file_with_its_reason(repo):
    lookup = [{"id": DONE, "docs": [unit_doc()], "gate": "released",
               "records": records(repo, digests={"proposal": "e" * 64})}]
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    reasons = {row["path"]: row["reason"] for row in result["keep"]}
    assert reasons[f".minerva/work/{DONE}/proposal.md"] == "changed in Lorestrom since import"
    assert f".minerva/work/{DONE}/proposal.md" not in result["remove"]


def test_removal_of_an_unimported_unit_removes_nothing(repo):
    lookup = [{"id": DONE, "docs": [], "gate": None, "records": []}]
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    assert result["remove"] == [] and result["unitsRemaining"] == 2


def test_removal_keeps_untracked_and_edited_files_out_of_the_commit(repo):
    write(repo, f".minerva/work/{DONE}/notes.md", "# Notes\n")
    lookup = [{"id": DONE, "docs": [unit_doc()], "gate": "released", "records": records(repo)}]
    write(repo, f".minerva/work/{DONE}/proposal.md", PROPOSAL + "\nedit\n")
    lookup[0]["records"] = records(repo)
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    reasons = {row["path"]: row["reason"] for row in result["keep"]}
    assert reasons[f".minerva/work/{DONE}/notes.md"].startswith("untracked")
    assert reasons[f".minerva/work/{DONE}/proposal.md"].startswith("uncommitted edits")
    assert result["remove"] == [f".minerva/work/{DONE}/archive/scratchpad.md",
                                f".minerva/work/{DONE}/scratchpad.md"]
    removable = {row["path"]: row["removable"] for row in result["keep"]}
    assert not removable[f".minerva/work/{DONE}/notes.md"]
    assert removable[f".minerva/work/{DONE}/spike.py"]


def test_a_later_batch_skips_units_an_earlier_commit_removed(repo):
    lookup = [{"id": DONE, "docs": [unit_doc()], "gate": "released", "records": records(repo)}]
    git(repo, "rm", "-q", "-r", f".minerva/work/{DONE}")
    commit(repo, "batch 1")
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    assert result["remove"] == [] and result["unitsRemaining"] == 1


def test_a_taken_unit_is_final_and_its_files_are_kept(repo):
    lookup = [{"id": DONE, "docs": [unit_doc(imported=False)], "gate": "open", "records": []},
              {"id": DRAFT, "docs": [unit_doc(unit=DRAFT)], "gate": "abandoned",
               "records": records(repo, unit=DRAFT, status="archived")}]
    result = backend.migration_removal_plan(repo, PROJECT, [], lookup)
    reasons = {row["path"]: row["reason"] for row in result["keep"]}
    assert reasons[f".minerva/work/{DONE}/proposal.md"] == backend.TAKEN_REASON
    assert result["unitsRemaining"] == 0


def test_the_old_removal_plan_input_is_unchanged(repo):
    out = run(repo, "removal-plan", "--project", PROJECT, stdin="[]")
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == {"remove": [], "keep": []}


# --- other branches ------------------------------------------------------------------------


def test_branches_holding_minerva_changes_are_listed(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    write(repo, ".minerva/work/2026-02-01-elsewhere/proposal.md", "# P\n")
    commit(repo, "unit")
    git(repo, "checkout", "-q", "-b", "code-only", "main")
    write(repo, "app.py", "x\n")
    commit(repo, "code")
    git(repo, "checkout", "-q", "-b", "merged", "main")
    git(repo, "checkout", "-q", "main")
    out = run(repo, "minerva-branches")
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == {"branches": [
        {"branch": "feature", "units": ["2026-02-01-elsewhere"], "files": 1}], "unchecked": None}


def test_the_current_branch_is_not_listed(repo):
    git(repo, "checkout", "-q", "-b", "feature")
    write(repo, ".minerva/work/2026-02-01-elsewhere/proposal.md", "# P\n")
    commit(repo, "unit")
    assert backend.minerva_branches(repo)["branches"] == []


def test_a_squash_merged_branch_is_not_listed(repo):
    git(repo, "checkout", "-q", "-b", "squashed")
    write(repo, ".minerva/work/2026-02-01-elsewhere/proposal.md", "# P\n")
    commit(repo, "unit")
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--squash", "squashed")
    commit(repo, "squash")
    assert backend.minerva_branches(repo)["branches"] == []


def test_branches_outside_a_repository_are_unchecked(tmp_path):
    assert backend.minerva_branches(tmp_path)["unchecked"] == "not a git working tree"


def test_removal_writes_its_paths_for_git(repo, tmp_path):
    lookup = [{"id": DONE, "docs": [unit_doc()], "gate": "released", "records": records(repo)}]
    remove, keep = tmp_path / "remove", tmp_path / "keep"
    out = run(repo, "removal-plan", "--project", PROJECT, "--write-remove", str(remove),
              "--write-keep", str(keep), stdin=json.dumps({"docs": [], "units": lookup}))
    assert out.returncode == 0, out.stderr
    assert remove.read_text().splitlines() == json.loads(out.stdout)["remove"]
    assert keep.read_text().splitlines() == [".minerva/adrs/001-x.md",
                                             f".minerva/work/{DONE}/spike.py"]


def test_a_path_with_a_line_break_is_never_written(tmp_path):
    with pytest.raises(backend.BackendError):
        backend.write_paths(tmp_path / "out", ["a\nb"])
