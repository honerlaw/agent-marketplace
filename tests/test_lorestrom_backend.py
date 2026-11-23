"""The deterministic half of the lorestrom plugin (`plugins/lorestrom/scripts/lorestrom_backend.py`).

Lorestrom's limits and result shapes here are vendored from its public MCP schemas. No test
talks to a Lorestrom server. In-process tests load lorestrom's own copies of its imports
(`tests/lorestrom_scripts.py`); CLI tests run the script, which imports from its own
directory.
"""
import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from knowledge_catalog import load_entries, superseded_by
from tests import lorestrom_scripts

backend = lorestrom_scripts.backend()

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".minerva" / "knowledge"
SCRIPT = lorestrom_scripts.SCRIPTS / "lorestrom_backend.py"

ORG = "11111111-1111-4111-8111-111111111111"
SPACE = "22222222-2222-4222-8222-222222222222"
PROJECT = "33333333-3333-4333-8333-333333333333"
OTHER = "44444444-4444-4444-8444-444444444444"
LINK = {"orgId": ORG, "workspaceId": SPACE, "projectId": PROJECT}
STEM = "2026-11-22-decision-example"
LABEL = "example.com/acme/api"
ENTRY = f".minerva/knowledge/{STEM}.md"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout


def commit(root, message="change"):
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    # The developer's global excludes must not decide what these tests see.
    git(root, "config", "core.excludesFile", str(tmp_path / "no-global-excludes"))
    (root / "README.md").write_text("project\n")
    commit(root, "init")
    git(root, "remote", "add", "origin", "git@example.com:Acme/API.git")
    return root


def share(root, value=LINK):
    path = root / ".lorestrom" / "config.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value))


def cache(root, value=LINK):
    path = backend.cache_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value))


def linked(source):
    return {"state": "linked", "link": LINK, "source": source, "remote": LABEL}


def project(doc_id, remotes, kind="minerva:project"):
    """A `find_docs` result, as Lorestrom's doc detail has it."""
    return {"id": doc_id, "workspaceId": SPACE, "folderId": None, "kind": kind,
            "title": "API", "inherits": True, "role": "edit", "key": None,
            "status": "current", "tags": [], "properties": {"minerva:remotes": remotes}}


def entry(related="", summary="A short summary", title="Example", extra=""):
    return (f"# {title}\n\n**Date**: 2026-11-22\n**Type**: decision\n**Theme**: lifecycle\n"
            f"**Summary**: {summary}\n**Context**: .minerva/work/2026-11-22-example\n\n"
            f"## Finding\n\nThe finding.\n{extra}" + (f"\n## Related\n\n{related}" if related else ""))


def add_file(root, relative=ENTRY, text=None):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(entry() if text is None else text)
    return path


def run(root, *args, stdin=None, env=None):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--cwd", str(root), *args],
                          input=stdin, capture_output=True, text=True, env=env)


# --- the loader ------------------------------------------------------------------


def test_in_process_tests_exercise_lorestroms_own_copies():
    for function in (backend.parse_entry, backend.unfenced, backend.entry_payload):
        assert Path(function.__code__.co_filename).resolve().parent == lorestrom_scripts.SCRIPTS


# --- resolution ---------------------------------------------------------------


def test_a_repo_with_an_origin_and_no_link_asks_for_discovery(repo):
    assert backend.resolve(repo) == {"state": "discover", "link": None, "source": None,
                                     "remote": LABEL}


def test_no_origin_is_unlinked(repo):
    git(repo, "remote", "remove", "origin")
    assert backend.resolve(repo)["state"] == "unlinked"


def test_no_git_repository_is_unlinked(tmp_path):
    assert backend.resolve(tmp_path) == {"state": "unlinked", "link": None, "source": None,
                                         "remote": None}


def test_the_committed_marker_links(repo):
    share(repo)
    assert backend.resolve(repo) == linked("shared")


def test_the_clones_cache_beats_the_marker(repo):
    share(repo)
    cache(repo, {**LINK, "projectId": OTHER})
    assert backend.resolve(repo)["link"]["projectId"] == OTHER


def test_the_cache_is_lorestroms_own_and_not_minervas(repo):
    assert backend.cache_path(repo) == (repo / ".git" / "lorestrom" / "config.json").resolve()


def test_linked_worktrees_share_the_cache(repo, tmp_path):
    cache(repo)
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    assert backend.resolve(tree) == linked("cache")


@pytest.mark.parametrize("place", [share, cache])
@pytest.mark.parametrize("value", [
    "", "{not json", "[]", "null", "{}", {"orgId": ORG, "workspaceId": SPACE},
    {**LINK, "projectId": "../elsewhere"}, {**LINK, "orgId": "AAAAAAAA-1111-4111-8111-111111111111"},
])
def test_a_malformed_link_raises_and_is_never_unlinked(repo, place, value):
    place(repo, value)
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_a_dangling_config_link_raises(repo):
    (repo / ".lorestrom").mkdir()
    (repo / ".lorestrom" / "config.json").symlink_to(repo / "missing.json")
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_minervas_marker_is_not_a_link(repo):
    (repo / ".minerva").mkdir()
    (repo / ".minerva" / "config.json").write_text(json.dumps(
        {"backend": "lorestrom", "lorestrom": LINK}))
    assert backend.resolve(repo)["state"] == "discover"


# --- remote labels and discovery ----------------------------------------------


@pytest.mark.parametrize("url", [
    "git@example.com:Acme/API.git",
    "example.com:acme/api",
    "https://example.com/acme/api",
    "https://example.com/acme/api.git/",
    "https://someone:secret-token@example.com/acme/api.git",
    "https://example.com/acme/api.git?access_token=secret-token#main",
    "git@example.com:acme/api.git?access_token=secret-token",
    "ssh://git@example.com:2222/acme/api.git",
])
def test_every_spelling_of_a_remote_is_one_label_without_credentials(url):
    assert backend.repo_label(url) == LABEL


@pytest.mark.parametrize("url", [
    None, "", "/Users/someone/code/api", "../api", "file:///Users/someone/code/api",
    "C:/code/api", "https://example.com/", "https://example.com/acme/a pi",
    "user:TOKEN@example.com/acme/api.git",
    "https:/user:TOKEN@example.com/acme/api",
    "https://user:pa/ss@example.com/acme/api",
    "hg::/Users/someone/private/repo",
    "file:/Users/someone/private/repo",
    "localhost:/Users/someone/private/repo",
    "localhost:private/repo",
    "git@example.com:/Users/someone/private/repo",
    "https://example.com/acme/../api",
    "https://exam\tple.com/acme/api",
])
def test_a_local_unusable_or_unknown_remote_has_no_label(url):
    assert backend.repo_label(url) is None


def test_a_web_port_is_another_server_and_a_default_one_is_not():
    assert backend.repo_label("https://example.com:8443/acme/api") == "example.com:8443/acme/api"
    assert backend.repo_label("https://example.com:443/acme/api") == LABEL
    backend.project_key("example.com:8443/acme/api")


def test_the_label_is_the_url_git_fetches_from(repo):
    git(repo, "remote", "set-url", "--add", "origin", "git@mirror.example:me/mirror.git")
    assert backend.origin_label(repo) == LABEL


def test_instead_of_is_applied_to_the_label(repo):
    git(repo, "config", "url.git@example.com:.insteadOf", "gh:")
    git(repo, "remote", "set-url", "origin", "gh:acme/api.git")
    assert backend.origin_label(repo) == LABEL


def test_one_holder_of_the_label_links():
    found = backend.match_project(LABEL, [
        project(OTHER, "example.com/acme/web"), project(PROJECT, LABEL)])
    assert found == {"action": "link",
                     "holders": 1, "candidates": [{"projectId": PROJECT, "workspaceId": SPACE}]}


def test_an_alias_links():
    docs = [project(PROJECT, f"old.example/acme/api {LABEL}")]
    assert backend.match_project(LABEL, docs)["action"] == "link"


def test_two_holders_of_the_label_ask():
    docs = [project(PROJECT, LABEL), project(OTHER, LABEL)]
    found = backend.match_project(LABEL, docs)
    assert found["action"] == "ask" and len(found["candidates"]) == 2


def test_the_same_name_under_another_owner_asks():
    """A transfer, a rename of the owner, or a fork: only the user knows which."""
    docs = [project(PROJECT, "example.com/oldco/api")]
    assert backend.match_project(LABEL, docs)["action"] == "ask"


@pytest.mark.parametrize("label,docs", [
    (LABEL, []),
    (LABEL, [project(PROJECT, "example.com/acme/api-docs")]),
    (LABEL, [project(PROJECT, LABEL, kind="note")]),
    (None, [project(PROJECT, LABEL)]),
])
def test_no_holder_is_none(label, docs):
    assert backend.match_project(label, docs)["action"] == "none"


@pytest.mark.parametrize("docs", [{"error": "unavailable"}, None, [{"id": PROJECT}], ["text"]])
def test_a_failed_lookup_is_never_read_as_no_project(docs):
    with pytest.raises(backend.BackendError):
        backend.match_project(LABEL, docs)


@pytest.mark.parametrize("status", ["archived", "deprecated", "superseded"])
def test_a_retired_project_does_not_link(status):
    doc = {**project(PROJECT, LABEL), "status": status}
    assert backend.match_project(LABEL, [doc])["action"] == "none"


def test_holders_are_counted_for_the_sum_over_servers():
    two = [project(PROJECT, LABEL), project(OTHER, LABEL)]
    assert backend.match_project(LABEL, two)["holders"] == 2
    assert backend.match_project(LABEL, [project(OTHER, "example.com/old/api")])["holders"] == 0


# --- keys and properties ------------------------------------------------------


def test_keys():
    assert backend.knowledge_key(PROJECT, STEM) == f"minerva:k/{PROJECT}/{STEM}"
    assert backend.project_key(LABEL) == f"minerva:p/{LABEL}"


@pytest.mark.parametrize("key", [
    "minerva", "Minerva:x", "minerva:", "minerva:a b", "minerva:a\nb", "minerva:a\x07b",
    "minerva:" + "x" * 201,
])
def test_a_key_lorestrom_would_refuse_is_refused(key):
    with pytest.raises(backend.BackendError):
        backend.check_key(key)


@pytest.mark.parametrize("bad", ["../elsewhere", "33333333", PROJECT.upper() + "x"])
def test_a_project_id_is_a_uuid(bad):
    with pytest.raises(backend.BackendError):
        backend.knowledge_key(bad, STEM)


def test_merge_keeps_what_it_was_not_given():
    assert backend.merge_properties({"a": 1, "b": "old"}, {"b": "new"}) == {"a": 1, "b": "new"}


@pytest.mark.parametrize("changes", [
    {"nested": {"a": 1}},
    {" padded": 1},
    {"k" * 65: 1},
    {"long": "x" * 1001},
    {"emoji": "\U0001F600" * 501},  # 1002 UTF-16 code units
    {"nul": "a\x00b"},
    {"bad": "\ud800"},
    {f"k{i}": i for i in range(65)},
    {f"k{i}": "x" * 1000 for i in range(17)},
])
def test_properties_lorestrom_would_refuse_are_refused(changes):
    with pytest.raises(backend.BackendError):
        backend.merge_properties({}, changes)


# --- entry payloads -----------------------------------------------------------


def test_payload_fields():
    unit = f"minerva:u/{PROJECT}/2026-11-22-example"
    got = backend.entry_payload(STEM, entry(), PROJECT, unit)
    assert got["key"] == f"minerva:k/{PROJECT}/{STEM}"
    assert (got["kind"], got["title"], got["edges"]) == ("minerva:knowledge", "Example", [])
    props = dict(got["properties"])
    assert len(props.pop("minerva:digest")) == 64
    assert props == {"minerva:id": STEM, "minerva:project": PROJECT, "minerva:type": "decision",
                     "minerva:theme": "lifecycle", "minerva:summary": "A short summary",
                     "minerva:date": "2026-11-22", "minerva:context": unit}
    assert got["markdown"] == entry()


def test_the_digest_follows_the_file():
    first = backend.entry_payload(STEM, entry(), PROJECT)["properties"]["minerva:digest"]
    second = backend.entry_payload(STEM, entry(extra="More.\n"), PROJECT)["properties"]["minerva:digest"]
    assert first != second


def test_edges_follow_the_catalogs_rules():
    older, peer, newer = ("2026-11-01-decision-older", "2026-11-22-pattern-peer",
                          "2026-12-01-decision-newer")
    got = backend.entry_payload(STEM, entry(
        f"- [[{older}]] — supersedes: replaced\n- [[{peer}]] — builds on\n"
        f"- [[{newer}]] — supersedes\n"), PROJECT)
    assert {(e["source"], e["relation"], e["target"]) for e in got["edges"]} == {
        (STEM, "supersedes", older), (STEM, "relates_to", peer),
        (STEM, "relates_to", newer),  # an entry cannot retire a newer one
    }


def test_superseded_by_and_a_banner_become_the_successors_edge():
    by_label, by_banner = "2026-12-01-decision-label", "2026-12-02-decision-banner"
    text = entry(f"- [[{by_label}]] — superseded by\n").replace(
        "# Example\n", f"# Example\n\n<!-- superseded-by: {by_banner} -->\n", 1)
    edges = backend.entry_payload(STEM, text, PROJECT)["edges"]
    assert {(e["source"], e["relation"], e["target"]) for e in edges} == {
        (by_label, "supersedes", STEM), (by_banner, "supersedes", STEM)}


def test_the_other_end_never_labels_an_edge():
    edges = backend.entry_payload(
        STEM, entry("- [[2026-12-01-decision-new]] — superseded by\n"), PROJECT)["edges"]
    assert edges[0]["properties"] == {}


@pytest.mark.parametrize("extra", ["Prose about the links.\n", "```\nan example\n```\n"])
def test_content_under_related_is_kept(extra):
    related = f"- [[2026-11-01-decision-older]] — builds on\n{extra}"
    markdown = backend.entry_payload(STEM, entry(related), PROJECT)["markdown"]
    assert "## Related" in markdown and extra.splitlines()[-1] in markdown


def test_a_fenced_example_is_neither_metadata_nor_an_edge():
    fence = "```\n**Summary**: not this\n## Related\n- [[2026-01-01-bug-fake]] — supersedes\n```\n"
    got = backend.entry_payload(STEM, entry(extra=fence), PROJECT)
    assert got["edges"] == [] and fence.strip() in got["markdown"]


def test_a_long_title_is_shortened_and_kept_whole_in_the_body():
    long_title = "T" * 250
    got = backend.entry_payload(STEM, entry(title=long_title), PROJECT)
    assert len(got["title"]) == 200 and f"# {long_title}" in got["markdown"]


def test_a_blank_title_is_the_stem():
    assert backend.entry_payload("001-bug-blank", "#    \n\nbody\n", PROJECT)["title"] == "001-bug-blank"


@pytest.mark.parametrize("stem,text", [
    ("not-an-entry", entry()),
    ("2026-13-45-decision-bad-date", entry()),
    ("../2026-11-22-decision-escape", entry()),
    (STEM, entry().replace("**Theme**: lifecycle\n", "")),
    (STEM, entry().replace("**Summary**: A short summary\n", "")),
    (STEM, entry(summary="x" * 1001)),
    (STEM, entry(extra="x" * 100_001)),
    (STEM, entry(extra="a\x00b")),
    ("001-bug-blanks", "# a" + " " * 1001 + "b\n"),
])
def test_an_entry_lint_or_lorestrom_would_refuse_is_refused(stem, text):
    with pytest.raises(backend.BackendError):
        backend.entry_payload(stem, text, PROJECT)


@pytest.mark.parametrize("stem", [
    "001-bug-x$(id)", "001-bug-`id`", "001-bug-a b", "001-bug-a;b", "001-bug-a'b", "001-bug-a\nb",
])
def test_a_stem_that_is_not_shell_safe_is_refused(stem):
    with pytest.raises(backend.BackendError):
        backend.entry_payload(stem, entry(), PROJECT)


OLD, OLDER = "2026-11-01-bug-old", "2026-10-30-bug-older"


@pytest.mark.parametrize("related", [
    f"- [[{OLD}]] — see also [[{OLDER}]] because both leak\n",
    f"- [[{OLD}]] — builds on\n- [[{OLD}]] — and corrects it\n",
    f"- [[{OLD}]] — builds on\n  the second line of the label\n",
    "- [[2026-12-01-decision-new]] — superseded by: THE REASON\n",
    f"- [[{STEM}]] — a self-link, whose edge is refused\n",
])
def test_the_body_is_the_entry_verbatim(related):
    """An edge can be refused, unresolved or unlabelled: no line of text depends on one."""
    text = entry(related).replace("**Type**: decision", "**Type**: decision (revisit if slow)")
    assert backend.entry_payload(STEM, text, PROJECT)["markdown"] == text


def test_every_entry_in_this_repo_converts_with_the_catalogs_supersession():
    """Refused entries only where an independent measure shows Lorestrom's limit is crossed."""
    entries = load_entries(CORPUS)
    derived, converted = {}, 0
    for stem, parsed in entries.items():
        text = (CORPUS / f"{stem}.md").read_text(encoding="utf-8")
        try:
            got = backend.entry_payload(stem, text, PROJECT)
        except backend.BackendError as error:
            assert len(parsed["summary"] or "") > 1000 or len(text) > 100_000, f"{stem}: {error}"
            continue
        converted += 1
        for edge in got["edges"]:
            if edge["relation"] == "supersedes":
                derived.setdefault(edge["target"], set()).add(edge["source"])
        linked_stems = {edge["source"] for edge in got["edges"]} | {edge["target"] for edge in got["edges"]}
        assert {target for target, _ in parsed["edges"]} <= linked_stems, stem
    assert converted > 100
    assert derived == {stem: set(by) for stem, by in superseded_by(entries).items()}


def test_every_label_in_this_repo_reaches_its_edge():
    for stem, parsed in load_entries(CORPUS).items():
        try:
            got = backend.entry_payload(stem, (CORPUS / f"{stem}.md").read_text(encoding="utf-8"), PROJECT)
        except backend.BackendError:
            continue
        labels = {edge["properties"].get("minerva:label") for edge in got["edges"]}
        for _, label in parsed["edges"]:
            if label and not backend.SUPERSEDED_BY_LABEL_RE.match(label):
                assert label in labels, (stem, label)


@pytest.mark.parametrize("text,lossy", [
    ("Use <date-slug> dirs.\n", True), ("<!-- note -->\n", True), ("![shot](a.png)\n", True),
    ("Use `<date-slug>` dirs.\n", False), ("```\n<tag>\n```\n", False), ("a < b\n", False),
])
def test_markup_the_parser_drops_is_reported(repo, text, lossy):
    add_file(repo, text=entry(extra=text))
    assert backend.import_list(repo, PROJECT)["entries"][0]["lossy"] is lossy


# --- UTF-8, whatever the locale -------------------------------------------------


NON_UTF8 = {"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}


def non_utf8_env():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("LC_", "PYTHON")) and key != "LANG"}
    env.update(NON_UTF8)
    probe = subprocess.run([sys.executable, "-c",
                            "import locale, sys; print(sys.flags.utf8_mode, locale.getpreferredencoding(False))"],
                           env=env, capture_output=True, text=True).stdout.split()
    if probe[0] != "0" or probe[1].lower().replace("-", "") == "utf8":
        pytest.skip(f"this platform gives no non-UTF-8 default here: {probe}")
    return env


def test_an_entry_keeps_its_text_under_a_non_utf8_locale(repo):
    env = non_utf8_env()
    add_file(repo, text=entry(title="Café"))
    listed = run(repo, "import-list", "--project", PROJECT, env=env)
    assert listed.returncode == 0, listed.stderr
    row = json.loads(listed.stdout)["entries"][0]
    got = run(repo, "entry-payload", str(repo / ENTRY), "--project", PROJECT,
              "--digest", row["digest"], env=env)
    assert got.returncode == 0, got.stderr
    payload = json.loads(got.stdout)
    assert payload["title"] == "Café" and "# Café" in payload["markdown"]


def test_the_re_exec_runs_once_and_never_loops(repo):
    env = {**non_utf8_env(), backend.REEXEC_ENV: "1"}
    result = run(repo, "label", env=env)
    assert result.returncode != 0 and "UTF-8 mode" in result.stderr


def test_in_process_a_non_utf8_default_is_refused_not_guessed(monkeypatch):
    if sys.flags.utf8_mode:
        pytest.skip("this test process runs in UTF-8 mode")
    monkeypatch.setattr(backend.locale, "getpreferredencoding", lambda do_setlocale=True: "latin-1")
    with pytest.raises(backend.BackendError, match="UTF-8"):
        backend.entry_payload(STEM, entry(), PROJECT)


def test_a_non_utf8_entry_is_refused(repo):
    path = add_file(repo)
    path.write_bytes(b"# caf\xe9\n\nbody\n")
    got = backend.import_list(repo, PROJECT)
    assert got["entries"] == [] and "not UTF-8" in got["refused"][0]["reason"]
    assert run(repo, "entry-payload", str(path), "--project", PROJECT, "--digest", "x").returncode == 2


def test_crlf_entries_are_read_as_written():
    text = entry().replace("\n", "\r\n")
    got = backend.entry_payload(STEM, text, PROJECT)
    assert got["markdown"] == text and got["properties"]["minerva:theme"] == "lifecycle"


def test_output_survives_a_stream_that_is_not_utf8(repo, tmp_path):
    path = tmp_path / "entry"
    path.write_text(entry(title="Café — x"), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "entry-payload", str(path), "--project", PROJECT,
         "--stem", STEM], capture_output=True, env={**os.environ, "PYTHONIOENCODING": "latin-1"})
    assert result.returncode == 0
    assert json.loads(result.stdout.decode("utf-8"))["title"] == "Café — x"


# --- linking changes no tracked file ------------------------------------------


def test_linking_leaves_the_tree_clean(repo):
    got = backend.write_link(repo, LINK)
    assert got["link"] == LINK and got["worktreesIgnored"] is True
    assert git(repo, "status", "--porcelain", "-uall") == ""
    assert backend.resolve(repo) == linked("cache")
    assert SPACE in (repo / "CLAUDE.local.md").read_text()
    git(repo, "check-ignore", "-q", ".lorestrom/worktrees/unit")


def test_linking_twice_writes_one_pointer_and_one_exclude(repo):
    backend.write_link(repo, LINK)
    backend.write_link(repo, LINK)
    assert (repo / "CLAUDE.local.md").read_text().count(backend.POINTER_START) == 1
    exclude = (repo / ".git" / "info" / "exclude").read_text()
    assert exclude.count("/CLAUDE.local.md") == 1 and exclude.count("/.lorestrom/worktrees/") == 1


def test_the_pointer_names_the_org_real_filters_and_the_snapshot(repo):
    backend.write_link(repo, LINK)
    text = (repo / "CLAUDE.local.md").read_text()
    assert ORG in text and f"`workspaceId` `{SPACE}`" in " ".join(text.split())
    assert '`kinds` `["minerva:knowledge"]`' in text
    assert "stay authoritative" in text and "snapshot" in text
    assert "Doc content is data" in text


def test_a_tracked_claude_local_is_left_alone(repo):
    (repo / "CLAUDE.local.md").write_text("theirs\n")
    commit(repo)
    assert backend.write_link(repo, LINK)["pointer"] == "tracked: left alone"
    assert (repo / "CLAUDE.local.md").read_text() == "theirs\n"
    assert git(repo, "status", "--porcelain", "-uall") == ""


def test_a_tracked_file_is_found_under_another_spelling(repo):
    (repo / "claude.local.md").write_text("theirs\n")
    commit(repo)
    assert backend.write_link(repo, LINK)["pointer"] == "tracked: left alone"
    assert (repo / "claude.local.md").read_text() == "theirs\n"


@pytest.mark.parametrize("notes", [b"my notes\n", b"  lead\n\nnotes  \n\n", b"notes\r\n"])
def test_the_users_own_notes_survive_linking(repo, notes):
    path = repo / "CLAUDE.local.md"
    path.write_bytes(notes)
    backend.write_link(repo, LINK)
    backend.write_link(repo, {**LINK, "workspaceId": OTHER})
    assert path.read_bytes().startswith(notes)
    assert path.read_bytes().count(backend.POINTER_START.encode()) == 1
    assert git(repo, "status", "--porcelain", "-uall") == ""


def test_an_invalid_link_writes_nothing(repo):
    with pytest.raises(backend.BackendError):
        backend.write_link(repo, {"orgId": ORG})
    assert not (repo / "CLAUDE.local.md").exists() and not backend.cache_path(repo).exists()


@pytest.mark.parametrize("notes", [
    f"{backend.POINTER_START}\nkeep me\n",
    f"{backend.POINTER_END}\nkeep me\n",
    f"{backend.POINTER_END}\nkeep me\n{backend.POINTER_START}\n",
])
def test_damaged_markers_never_cost_a_note(repo, notes):
    path = repo / "CLAUDE.local.md"
    path.write_text(notes)
    for _ in range(2):
        assert backend.write_link(repo, LINK)["pointer"] == "damaged markers: left alone"
    assert path.read_text() == notes


def test_a_users_bytes_and_line_endings_survive(repo):
    path = repo / "CLAUDE.local.md"
    path.write_bytes(b"caf\xe9\r\nnotes\r\n")
    exclude = repo / ".git" / "info" / "exclude"
    exclude.write_bytes(b"# caf\xe9\n")
    backend.write_link(repo, LINK)
    written = path.read_bytes()
    assert written.startswith(b"caf\xe9\r\nnotes\r\n")
    assert written.count(b"\n") == written.count(b"\r\n")
    assert exclude.read_bytes().startswith(b"# caf\xe9\n")


def test_a_pointer_that_cannot_be_ignored_is_not_written(repo):
    (repo / ".gitignore").write_text("!*.md\n")
    commit(repo)
    for _ in range(2):
        assert backend.write_link(repo, LINK)["pointer"] == "not ignorable: left alone"
    assert not (repo / "CLAUDE.local.md").exists()
    assert git(repo, "status", "--porcelain", "-uall") == ""
    assert (repo / ".git" / "info" / "exclude").read_text().count("/CLAUDE.local.md") == 1


def test_a_symlinked_pointer_is_left_alone_with_its_target(repo, tmp_path):
    target = tmp_path / "outside.md"
    target.write_text("theirs\n")
    (repo / "CLAUDE.local.md").symlink_to(target)
    assert backend.write_link(repo, LINK)["pointer"] == "symlink: left alone"
    assert target.read_text() == "theirs\n"


def test_a_directory_named_like_the_pointer_is_left_alone(repo):
    (repo / "CLAUDE.local.md").mkdir()
    assert backend.write_link(repo, LINK)["pointer"] == "not a file: left alone"


def test_linking_alone_repairs_a_broken_link(repo):
    share(repo, "{broken")
    cache(repo, "{broken")
    backend.write_link(repo, LINK)
    assert backend.resolve(repo)["state"] == "linked"


def test_only_pointers_already_written_are_updated(repo, tmp_path):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    assert backend.write_link(repo, LINK)["otherPointers"] == {}
    assert not (tree / "CLAUDE.local.md").exists()


def test_relinking_moves_every_worktrees_pointer(repo, tmp_path):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    backend.write_link(tree, LINK)
    backend.write_link(repo, {**LINK, "workspaceId": OTHER})
    text = (tree / "CLAUDE.local.md").read_text()
    assert OTHER in text and SPACE not in text


def test_relinking_never_edits_another_clone_at_a_stale_worktree_path(repo, tmp_path):
    stale = tmp_path / "stale"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(stale))
    backend.write_link(stale, LINK)
    stale.rename(tmp_path / "moved")
    stale.mkdir()
    git(stale, "init", "-q", "-b", "main")
    backend.write_link(stale, LINK)
    before = (stale / "CLAUDE.local.md").read_bytes()
    backend.write_link(repo, {**LINK, "workspaceId": OTHER})
    assert (stale / "CLAUDE.local.md").read_bytes() == before


def test_one_unwritable_worktree_does_not_fail_the_relink(repo, tmp_path, monkeypatch):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    backend.write_link(tree, LINK)
    real = backend._set_pointer

    def refuse(top, block):
        if top.resolve() == tree.resolve():
            raise PermissionError("denied")
        return real(top, block)

    monkeypatch.setattr(backend, "_set_pointer", refuse)
    got = backend.write_link(repo, LINK)
    assert list(got["otherPointers"].values()) == ["failed: denied"]


def test_a_worktree_that_cannot_be_checked_is_reported(repo, tmp_path):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    backend.write_link(tree, LINK)
    (tree / ".git").write_text("gitdir: gone\n")
    got = backend.write_link(repo, LINK)
    assert [value.split(":")[0] for value in got["otherPointers"].values()] == ["failed"]


def test_under_git_dir_unchecked_pointers_are_reported(repo, monkeypatch):
    monkeypatch.setenv("GIT_DIR", str(repo / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repo))
    assert backend.write_link(repo, LINK)["otherPointers"] == {"*": "not checked: GIT_DIR is set"}


# --- untrusted repositories and the failure paths -----------------------------


@pytest.mark.parametrize("broken", [".git/config", ".git/HEAD"])
def test_a_git_failure_is_never_unlinked(repo, broken):
    cache(repo)
    (repo / broken).write_text("[broken")
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_a_git_failure_raises(repo):
    with pytest.raises(backend.BackendError):
        backend._git(repo, "rev-parse", "--verify", "-q", "refs/heads/absent")


def test_a_directory_that_is_not_there_raises(tmp_path):
    with pytest.raises(backend.BackendError):
        backend.resolve(tmp_path / "missing")


def test_a_worktree_older_than_the_marker_is_still_bound(repo, tmp_path):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    share(repo)
    assert backend.resolve(tree)["state"] == "linked"


def test_a_branch_older_than_a_committed_marker_is_still_bound(repo):
    git(repo, "update-ref", "refs/remotes/origin/main", "main")
    git(repo, "branch", "old")
    share(repo)
    commit(repo)
    git(repo, "update-ref", "refs/remotes/origin/main", "main")
    git(repo, "checkout", "-q", "old")
    assert not (repo / ".lorestrom").exists()
    assert backend.resolve(repo) == linked("shared")


def test_a_symlinked_marker_is_refused(repo, tmp_path):
    other = tmp_path / "other.json"
    other.write_text(json.dumps(LINK))
    (repo / ".lorestrom").mkdir()
    (repo / ".lorestrom" / "config.json").symlink_to(other)
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_a_symlinked_config_directory_is_refused(repo, tmp_path):
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / "elsewhere" / "config.json").write_text(json.dumps(LINK))
    (repo / ".lorestrom").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_a_dangling_lorestrom_directory_is_broken(repo, tmp_path):
    (repo / ".lorestrom").symlink_to(tmp_path / "gone")
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


def test_a_committed_symlink_marker_is_refused(repo):
    (repo / ".lorestrom").mkdir()
    # The link's own blob is valid config text, so only the mode check can refuse it.
    (repo / ".lorestrom" / "config.json").symlink_to(json.dumps(LINK, separators=(",", ":")))
    commit(repo)
    (repo / ".lorestrom" / "config.json").unlink()
    with pytest.raises(backend.BackendError):
        backend.resolve(repo)


@pytest.mark.parametrize("depth", [("pkg",), ("pkg", "src")])
def test_a_marker_below_the_root_is_never_unlinked(repo, depth):
    marker = repo / "pkg" / ".lorestrom"
    marker.mkdir(parents=True)
    (marker / "config.json").write_text(json.dumps(LINK))
    here = repo.joinpath(*depth)
    here.mkdir(exist_ok=True)
    with pytest.raises(backend.BackendError):
        backend.resolve(here)


@pytest.mark.skipif(getattr(os, "geteuid", lambda: 1)() == 0, reason="root reads anything")
def test_an_unreadable_cache_is_never_unlinked(repo):
    cache(repo)
    directory = backend.cache_path(repo).parent
    directory.chmod(0)
    try:
        with pytest.raises(backend.BackendError):
            backend.resolve(repo)
    finally:
        directory.chmod(0o700)


def test_a_repository_named_by_git_dir_is_still_linked(tmp_path, monkeypatch):
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("GIT_WORK_TREE", str(work))
    git(work, "init", "-q", "-b", "main")
    cache(work)
    assert backend.resolve(work)["state"] == "linked"


def test_a_git_dir_git_cannot_read_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "missing"))
    with pytest.raises(backend.BackendError):
        backend.resolve(tmp_path)


def test_an_empty_dot_git_above_is_no_repository(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "project").mkdir()
    assert backend.resolve(tmp_path / "project")["state"] == "unlinked"


def test_junk_named_dot_git_is_no_repository(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "notes.txt").write_text("not a repository\n")
    assert backend.resolve(tmp_path)["state"] == "unlinked"


@pytest.mark.parametrize("claim", ["file", "symlink", "HEAD"])
def test_a_claimed_repository_git_cannot_read_raises(tmp_path, claim):
    marker = tmp_path / ".git"
    if claim == "file":
        marker.write_text("gitdir: gone\n")
    elif claim == "symlink":
        marker.symlink_to(tmp_path / "gone")
    else:
        marker.mkdir()
        (marker / "HEAD").write_text("broken")
    with pytest.raises(backend.BackendError):
        backend.resolve(tmp_path)


@pytest.mark.parametrize("member", ["objects", "lorestrom"])
def test_each_repository_member_is_a_claim(tmp_path, member):
    (tmp_path / ".git" / member).mkdir(parents=True)
    with pytest.raises(backend.BackendError):
        backend.resolve(tmp_path)


def test_a_bare_container_resolves_and_cannot_be_linked(tmp_path):
    git(tmp_path, "init", "-q", "--bare", "box/.bare")
    (tmp_path / "box" / ".git").write_text("gitdir: ./.bare\n")
    assert backend.resolve(tmp_path / "box")["state"] == "unlinked"
    with pytest.raises(backend.BackendError):
        backend.write_link(tmp_path / "box", LINK)


def test_a_separate_git_dirs_old_worktree_is_bound_by_the_committed_marker(tmp_path):
    main, tree = tmp_path / "main", tmp_path / "linked"
    main.mkdir()
    git(main, "init", "-q", "-b", "main", "--separate-git-dir", str(tmp_path / "store"))
    for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid"),
                       ("commit.gpgsign", "false")):
        git(main, "config", key, value)
    git(main, "commit", "-q", "--allow-empty", "-m", "init")
    git(main, "worktree", "add", "-q", "-b", "unit", str(tree))
    share(main)
    commit(main)
    assert backend.resolve(tree)["state"] == "linked"


def test_a_submodules_old_worktree_sees_its_primary_checkout(repo, tmp_path):
    outer, tree = tmp_path / "outer", tmp_path / "linked"
    outer.mkdir()
    git(outer, "init", "-q", "-b", "main")
    git(outer, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(repo), "inner")
    git(outer / "inner", "worktree", "add", "-q", "-b", "unit", str(tree))
    share(outer / "inner")
    assert backend.resolve(tree)["state"] == "linked"


def test_a_tag_cannot_stand_in_for_the_default_branch(repo):
    git(repo, "update-ref", "refs/remotes/origin/main", "main")
    share(repo)
    commit(repo)
    git(repo, "tag", "origin/main")
    assert backend._default_branch(repo) == "refs/remotes/origin/main"
    git(repo, "checkout", "-q", "-b", "old", "refs/remotes/origin/main")
    assert backend.resolve(repo)["state"] == "discover"


def test_a_tag_spelled_like_a_branch_ref_is_no_branch(repo):
    git(repo, "branch", "-m", "main", "trunk")
    git(repo, "tag", "refs/heads/main")
    assert backend._default_branch(repo) is None


def test_the_remotes_default_is_preferred_to_a_local_main(repo):
    git(repo, "update-ref", "refs/remotes/origin/trunk", "main")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    assert backend._default_branch(repo) == "refs/remotes/origin/trunk"


def test_a_hostile_default_branch_name_needs_no_command_line(repo):
    name = "main$(touch${IFS}pwned)"
    git(repo, "update-ref", f"refs/remotes/origin/{name}", "main")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{name}")
    add_file(repo)
    result = run(repo, "import-list", "--project", PROJECT)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["entries"][0]["unmerged"] is True
    assert not (repo / "pwned").exists()


# --- import ---------------------------------------------------------------------


def test_import_neither_follows_nor_lists_a_symlink(repo, tmp_path):
    secret = tmp_path / "secret"
    secret.write_text("FAKE_SECRET=abc\n")
    link = repo / ".minerva" / "knowledge" / "001-bug-setup.md"
    link.parent.mkdir(parents=True)
    link.symlink_to(secret)
    for args in (["entry-payload", str(link)],
                 ["entry-payload", str(link), "--stem", "001-bug-setup"]):
        result = run(repo, *args, "--project", PROJECT)
        assert result.returncode == 2 and "FAKE_SECRET" not in result.stdout
    got = backend.import_list(repo, PROJECT)
    assert got["entries"] == [] and len(got["refused"]) == 1


@pytest.mark.parametrize("linked_dir", [".minerva/knowledge", ".minerva"])
def test_import_refuses_a_symlinked_directory(repo, tmp_path, linked_dir):
    outside = tmp_path / "outside" / "knowledge"
    outside.mkdir(parents=True)
    (outside / "001-bug-setup.md").write_text("FAKE_SECRET=abc\n")
    target = outside if linked_dir.endswith("knowledge") else outside.parent
    (repo / linked_dir).parent.mkdir(exist_ok=True)
    (repo / linked_dir).symlink_to(target)
    with pytest.raises(backend.BackendError):
        backend.import_list(repo, PROJECT)


def test_a_payload_is_only_read_from_the_knowledge_directory(repo):
    path = repo / f"{STEM}.md"
    path.write_text(entry())
    digest = backend.entry_payload(STEM, entry(), PROJECT)["properties"]["minerva:digest"]
    result = run(repo, "entry-payload", str(path), "--project", PROJECT, "--digest", digest)
    assert result.returncode == 2 and "is not in" in result.stderr


def test_import_list_reports_without_bodies(repo):
    add_file(repo)
    add_file(repo, ".minerva/knowledge/001-bug-x$(id).md")
    got = backend.import_list(repo, PROJECT)
    assert [row["stem"] for row in got["entries"]] == [STEM]
    assert "markdown" not in got["entries"][0] and "The finding." not in json.dumps(got)
    assert len(got["refused"]) == 1
    assert (got["branch"], got["entries"][0]["unmerged"]) == ("main", True)
    commit(repo)
    git(repo, "checkout", "-q", "-b", "unit")
    got = backend.import_list(repo, PROJECT)
    assert (got["branch"], got["entries"][0]["unmerged"]) == ("unit", False)


def test_import_writes_nothing(repo):
    add_file(repo)
    commit(repo)
    backend.import_list(repo, PROJECT)
    assert git(repo, "status", "--porcelain", "-uall") == ""


def test_one_edge_declared_from_both_ends_is_sent_once_with_its_sources_label(repo):
    old, new = "2026-11-01-decision-old", "2026-11-02-decision-new"
    add_file(repo, f".minerva/knowledge/{old}.md", entry(f"- [[{new}]] — superseded by\n"))
    add_file(repo, f".minerva/knowledge/{new}.md", entry(f"- [[{old}]] — supersedes: replaced\n"))
    assert backend.import_list(repo, PROJECT)["edges"] == [{
        "source": new, "relation": "supersedes", "target": old, "declaredBy": [old, new],
        "properties": {"minerva:label": "supersedes: replaced"}}]


def test_a_cycle_and_a_self_link_are_refused_edges(repo):
    one, two, own = ("2026-11-01-decision-one", "2026-11-01-decision-two",
                     "2026-11-03-decision-own")
    add_file(repo, f".minerva/knowledge/{one}.md", entry(f"- [[{two}]] — supersedes\n"))
    add_file(repo, f".minerva/knowledge/{two}.md", entry(f"- [[{one}]] — supersedes\n"))
    add_file(repo, f".minerva/knowledge/{own}.md", entry(f"- [[{own}]] — see also\n"))
    got = backend.import_list(repo, PROJECT)
    assert got["edges"] == [] and len(got["refusedEdges"]) == 3


@pytest.mark.parametrize("hidden", ["untracked-off", "ignored", "ahead-of-origin"])
def test_an_unmerged_entry_is_marked_however_git_hides_it(repo, hidden):
    git(repo, "update-ref", "refs/remotes/origin/main", "main")
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    if hidden == "untracked-off":
        git(repo, "config", "status.showUntrackedFiles", "no")
    if hidden == "ignored":
        (repo / ".gitignore").write_text(".minerva/\n")
    add_file(repo)
    if hidden == "ahead-of-origin":
        commit(repo)
    assert backend.import_list(repo, PROJECT)["entries"][0]["unmerged"] is True


def test_with_no_default_branch_every_entry_is_unmerged(repo):
    add_file(repo)
    commit(repo)
    git(repo, "branch", "-m", "main", "trunk")
    assert backend.import_list(repo, PROJECT)["entries"][0]["unmerged"] is True


def test_a_payload_must_be_what_was_confirmed(repo):
    path = add_file(repo)
    digest = backend.import_list(repo, PROJECT)["entries"][0]["digest"]
    args = ("entry-payload", str(path), "--project", PROJECT)
    assert run(repo, *args, "--digest", digest).returncode == 0
    assert run(repo, *args).returncode == 2
    path.write_text(entry(extra="UNCONFIRMED\n"))
    changed = run(repo, *args, "--digest", digest)
    assert changed.returncode == 2 and "UNCONFIRMED" not in changed.stdout


def respelled(path):
    """The same directory in another case, where the file system allows one."""
    other = path.parent / path.name.upper()
    if other.name == path.name or not other.exists():
        pytest.skip("needs a case-insensitive file system")
    return other


@pytest.mark.parametrize("below", [".", "src"])
def test_another_spelling_of_the_root_is_the_root(repo, below):
    share(repo)
    (repo / "src").mkdir()
    assert backend.resolve(respelled(repo) / below)["state"] == "linked"


def test_another_spelling_still_updates_the_other_pointers(repo, tmp_path):
    tree = tmp_path / "linked"
    git(repo, "worktree", "add", "-q", "-b", "unit", str(tree))
    backend.write_link(tree, LINK)
    backend.write_link(respelled(repo), {**LINK, "workspaceId": OTHER})
    assert OTHER in (tree / "CLAUDE.local.md").read_text()


def test_another_spelling_can_still_send_an_entry(repo):
    add_file(repo)
    assert backend.read_repo_entry(respelled(repo), ENTRY) == entry()


# --- the CLI ------------------------------------------------------------------


def test_cli_exit_codes(repo):
    assert json.loads(run(repo, "resolve").stdout)["state"] == "discover"
    assert run(repo, "match", stdin="not json").returncode == 2
    assert run(repo, "link", stdin=json.dumps(LINK)).returncode == 0
    assert json.loads(run(repo, "resolve").stdout)["state"] == "linked"
    cache(repo, "{broken")
    broken = run(repo, "resolve")
    assert broken.returncode == 2 and broken.stdout == ""


def test_cli_has_no_files_mode_commands():
    commands = {"resolve", "label", "match", "link", "merge-properties", "entry-payload",
                "import-list"}
    help_text = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True,
                               text=True).stdout
    assert all(name in help_text for name in commands)
    for gone in ("opt-out", "check-tree"):
        assert gone not in help_text


@pytest.mark.parametrize("place", [share, cache])
def test_the_label_needs_no_link_and_writes_nothing(repo, place):
    place(repo, "{broken")
    cached = backend.cache_path(repo)
    before = cached.read_bytes() if cached.exists() else None
    assert json.loads(run(repo, "label").stdout) == {"remote": LABEL}
    assert (cached.read_bytes() if cached.exists() else None) == before
    assert run(repo, "resolve").returncode == 2


def test_cli_entry_payload_reads_a_temp_file(repo, tmp_path):
    path = tmp_path / "tmp.XXXX"
    path.write_text(entry())
    result = run(repo, "entry-payload", str(path), "--project", PROJECT, "--stem", STEM)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["key"].endswith(STEM)


def test_cli_match(repo):
    got = run(repo, "match", stdin=json.dumps([project(PROJECT, LABEL)]))
    assert json.loads(got.stdout)["action"] == "link"


def test_cli_import_list(repo):
    add_file(repo)
    got = run(repo, "import-list", "--project", PROJECT)
    assert [row["stem"] for row in json.loads(got.stdout)["entries"]] == [STEM]


def test_cli_merge_properties(repo):
    got = run(repo, "merge-properties",
              stdin=json.dumps({"existing": {"a": 1}, "changes": {"b": 2}}))
    assert json.loads(got.stdout) == {"a": 1, "b": 2}


# --- Python 3.9 -----------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(lorestrom_scripts.SCRIPTS.glob("*.py")), ids=lambda path: path.stem)
def test_no_annotation_is_evaluated_as_a_union(path):
    """`X | None` evaluated at import stops every caller on macOS's stock Python 3.9."""
    tree = ast.parse(path.read_text())
    if any(isinstance(node, ast.ImportFrom) and node.module == "__future__"
           and any(name.name == "annotations" for name in node.names) for node in tree.body):
        return
    for node in ast.walk(tree):
        for field in ("annotation", "returns"):
            found = getattr(node, field, None)
            if found is not None:
                assert not any(isinstance(part, ast.BinOp) and isinstance(part.op, ast.BitOr)
                               for part in ast.walk(found)), f"{path.name}:{found.lineno}"


def test_zip_takes_no_keywords():
    """`zip(strict=True)` raises on macOS's stock Python 3.9."""
    for node in ast.walk(ast.parse(SCRIPT.read_text())):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "zip":
            assert not node.keywords, node.lineno


STOCK_PYTHON = "/usr/bin/python3"


@pytest.mark.skipif(not os.access(STOCK_PYTHON, os.X_OK), reason="no stock Python")
def test_the_stock_python_imports_and_runs_every_script(repo):
    names = sorted(path.stem for path in lorestrom_scripts.SCRIPTS.glob("*.py"))
    imported = subprocess.run(
        [STOCK_PYTHON, "-B", "-c", "import importlib, sys; [importlib.import_module(n) for n in sys.argv[1:]]",
         *names], cwd=lorestrom_scripts.SCRIPTS, capture_output=True, text=True)
    assert imported.returncode == 0, imported.stderr
    add_file(repo)
    result = subprocess.run([STOCK_PYTHON, "-B", str(SCRIPT), "--cwd", str(repo), "import-list",
                             "--project", PROJECT], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["entries"][0]["stem"] == STEM
    if shutil.which("git"):
        assert json.loads(subprocess.run(
            [STOCK_PYTHON, "-B", str(SCRIPT), "--cwd", str(repo), "label"],
            capture_output=True, text=True).stdout) == {"remote": LABEL}
