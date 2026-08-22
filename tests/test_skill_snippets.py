"""Executable regression tests for the shell/python snippets embedded in SKILL.md files.

These snippets are runnable code that happens to live in markdown, and until now nothing
ran them. The declarative contract layer (`tests/test_skill_contracts.py`) checks
`anchors`, which are substring-PRESENCE assertions — the exact shape
`2026-08-10-pattern-presence-assertions-rot-into-green-lies` warns rots into a green lie:
an assertion that a snippet contains some string cannot fail when the snippet's LOGIC is
wrong, and both defects covered here shipped under passing anchors.

So each test EXTRACTS the snippet from the SKILL.md it ships in and RUNS it against a
fixture. A rewrite that reintroduces the bug fails CI; a rewrite that keeps the behaviour
while changing the wording still passes.
"""
import re
import subprocess
import textwrap
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "minerva" / "skills"
SCRIPTS = REPO / "plugins" / "minerva" / "scripts"


# This module EXECUTES what it extracts, so a block carrying a mutating command would
# have CI creating labels, opening issues, or pushing branches against whatever repo the
# runner is authenticated to — which has already cost a real label that had to be deleted
# by hand (`2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state`).
#
# `gh` is checked by ALLOWLIST, not denylist. A denylist of the commands its author
# happened to recall is the wrong shape for a safety guard: `gh` grows subcommands, and
# every one not thought of fails open. An allowlist fails closed — a new read-only verb
# has to be added deliberately, and the cost of that is a red test, not a mutated repo.
GH_READ_ONLY_VERBS = {
    "list", "view", "status", "diff", "log", "checks", "search", "browse",
}
GH_COMMAND_RE = re.compile(r"\bgh\s+([a-z-]+)\s+([a-z-]+)")

# `gh api` takes no resource/verb pair, so it is judged separately: a plain GET is
# read-only, anything carrying a method flag or a GraphQL mutation is not.
GH_API_RE = re.compile(r"\bgh\s+api\b")
GH_API_MUTATING_RE = re.compile(r"--method\s+(?!GET\b)|-X\s+(?!GET\b)|mutation\s*[({]")

# git has a small, stable mutating surface — enumerating it is honest here in a way it
# is not for `gh`.
MUTATING_GIT_RE = re.compile(
    r"\bgit\s+(push|commit|merge|rebase|reset|clean|rm|mv|tag|checkout|switch|branch\s+-[dD]|"
    r"worktree\s+(add|remove)|cherry-pick|revert|stash|apply|am|filter-branch)\b"
)

# Non-git, non-gh commands that destroy state.
MUTATING_SHELL_RE = re.compile(r"\brm\s+-[rf]|\bmv\s+|\btruncate\b|>\s*/dev/sd")


def mutating_commands(body: str) -> list:
    """Every command in `body` that would change state outside the test process."""
    found = []
    for resource, verb in GH_COMMAND_RE.findall(body):
        if resource == "api":
            continue  # judged by GH_API_RE below
        if verb not in GH_READ_ONLY_VERBS:
            found.append(f"gh {resource} {verb}")
    if GH_API_RE.search(body) and GH_API_MUTATING_RE.search(body):
        found.append("gh api (non-GET / GraphQL mutation)")
    found += [f"git {m}" for m in
              (mm.group(1) for mm in MUTATING_GIT_RE.finditer(body))]
    found += [m.group(0).strip() for m in MUTATING_SHELL_RE.finditer(body)]
    return found


def assert_read_only(body: str, where: str) -> None:
    """Refuse to hand back a snippet that would mutate state if executed.

    This lives INSIDE `fenced_blocks` rather than beside it deliberately. A guard a
    future author must remember to call is the same defect shape as a comment asking
    six files to stay in sync — it protects only the call sites someone thought of.
    Guarding the extractor covers every extraction, present and future.
    """
    bad = mutating_commands(body)
    assert not bad, (
        f"{where} extracts a fenced block containing {bad}, and this module EXECUTES "
        "what it extracts — CI would mutate real state. Assert on the snippet's text "
        "instead of running it, or stub the command."
    )


def fenced_blocks(md: Path, lang: str) -> list:
    """Every ```<lang> fenced block in `md`, dedented, as a list of block bodies.

    Fences are matched with a leading-whitespace allowance because a snippet nested in a
    list item is indented, and its body is dedented by the fence's own indent so the
    extracted program is runnable as-is.

    Every returned block is checked read-only first — see `assert_read_only`.
    """
    blocks = re.findall(rf"^([ \t]*)```{lang}\n(.*?)^[ \t]*```",
                        md.read_text(), re.S | re.M)
    bodies = [textwrap.dedent(body) if not indent else
              "".join(ln[len(indent):] if ln.startswith(indent) else ln
                      for ln in body.splitlines(keepends=True))
              for indent, body in blocks]
    for body in bodies:
        assert_read_only(body, str(md))
    return bodies


# --- migrate-fix Step 4: the legacy-link verification grep ------------------------

def legacy_link_grep() -> str:
    """The Step 4 verification pipeline, lifted out of migrate-fix/SKILL.md."""
    blocks = [b for b in fenced_blocks(SKILLS / "migrate-fix" / "SKILL.md", "bash")
              if b.lstrip().startswith("grep")]
    assert len(blocks) == 1, f"expected exactly one grep block, found {len(blocks)}"
    return blocks[0]


@pytest.fixture
def corpus(tmp_path):
    """A corpus holding one already-migrated link and one genuine legacy link."""
    (tmp_path / "migrated.md").write_text("see [[2026-05-19-decision-foo]]\n")
    (tmp_path / "legacy.md").write_text("see [[015-decision-legacy]]\n")
    return tmp_path


def test_verification_grep_finds_the_legacy_link(corpus):
    out = subprocess.run(["bash", "-c", legacy_link_grep()], cwd=corpus,
                         capture_output=True, text=True).stdout
    assert "015-decision-legacy" in out


def test_verification_grep_ignores_migrated_date_ids(corpus):
    """The defect: `[[0-9]{3,}-` matches the `2026` of every migrated link.

    On the corpus this was caught in that turned 26 real leftovers into 6,005 hits, so
    the check that confirms a migration worked reported catastrophic failure every time.
    """
    out = subprocess.run(["bash", "-c", legacy_link_grep()], cwd=corpus,
                         capture_output=True, text=True).stdout
    assert "2026-05-19-decision-foo" not in out
    assert len(out.strip().splitlines()) == 1


# --- lint Step 2: the orphan-detection one-liner ----------------------------------

def orphan_program() -> str:
    """The python program out of lint/SKILL.md's orphan snippet.

    Only the two shell interpolations are substituted (the scripts dir and the corpus
    dir); the program's own logic is executed exactly as it ships.
    """
    blocks = [b for b in fenced_blocks(SKILLS / "lint" / "SKILL.md", "bash")
              if "inbound=" in b]
    assert len(blocks) == 1, f"expected exactly one orphan block, found {len(blocks)}"
    m = re.search(r'python3 -c "(.*)"\s*$', blocks[0], re.S)
    assert m, "could not locate the python3 -c program in the orphan snippet"
    return m.group(1).replace('\\\n', '\n')


def run_orphan_query(knowledge_dir: Path) -> list:
    prog = orphan_program()
    prog = prog.replace("'${PLUGIN_SCRIPTS:-$ROOT/scripts}'", repr(str(SCRIPTS)))
    prog = prog.replace("'$ROOT/.minerva/knowledge'", repr(str(knowledge_dir)))
    assert "$ROOT" not in prog, "an unsubstituted shell interpolation survived"
    out = subprocess.run([sys.executable, "-c", prog],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    import json
    return json.loads(out.stdout)


def entry(kd: Path, stem: str, related=()) -> None:
    body = f"# {stem}\n\n**Type**: decision\n\n**Summary**: s\n\n## Related\n"
    body += "".join(f"- [[{t}]] — refines\n" for t in related)
    (kd / f"{stem}.md").write_text(body)


def test_orphan_query_finds_an_orphan_among_same_day_entries(tmp_path):
    """The defect: `inbound` was keyed on `nnn`, which under date ids IS the date.

    Every entry landing on one day collapsed into a single bucket, so a linked entry
    made its same-day neighbours look linked too — 0 orphans reported against 14 real
    ones. All three entries here share a date, which is ordinary: dates are read off the
    clock, never allocated.
    """
    entry(tmp_path, "2026-01-01-decision-a", related=["2026-01-01-decision-b"])
    entry(tmp_path, "2026-01-01-decision-b", related=["2026-01-01-decision-a"])
    entry(tmp_path, "2026-01-01-decision-lonely")
    assert run_orphan_query(tmp_path) == ["2026-01-01-decision-lonely"]


def test_orphan_query_counts_an_inbound_only_entry_as_linked(tmp_path):
    """An entry with no outbound edges is not an orphan if something links TO it."""
    entry(tmp_path, "2026-02-01-decision-src", related=["2026-02-02-pattern-dst"])
    entry(tmp_path, "2026-02-02-pattern-dst")
    assert run_orphan_query(tmp_path) == []


def test_verification_grep_ignores_a_number_narrower_than_a_legacy_id(corpus):
    """`{3,}` is the legacy id's own width (`ID_RE_SRC`). Loosening it to `+` would make
    the check report any bracketed number — a narrower rerun of the imprecision the
    date-shape exclusion was added to fix."""
    (corpus / "prose.md").write_text("see [[42-not-an-id]] here\n")
    out = subprocess.run(["bash", "-c", legacy_link_grep()], cwd=corpus,
                         capture_output=True, text=True).stdout
    assert "42-not-an-id" not in out
    assert "015-decision-legacy" in out


# --- The guard itself (issue #70) -------------------------------------------------

def test_guard_rejects_a_mutating_gh_block(tmp_path):
    """The defect this guards: an extraction added for a flow that mutates remote state.

    `minerva:promote`'s references/github-issues.md documents exactly these commands, so
    this is not hypothetical — it is the next extraction someone would plausibly add.
    """
    md = tmp_path / "SKILL.md"
    md.write_text("```bash\ngh label create 'minerva:followup' --color 5319E7\n```\n")
    with pytest.raises(AssertionError, match="gh label create"):
        fenced_blocks(md, "bash")


def test_guard_rejects_a_pushing_block(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("```bash\ngit push -u origin my-branch\n```\n")
    with pytest.raises(AssertionError, match="git push"):
        fenced_blocks(md, "bash")


def test_guard_allows_read_only_blocks(tmp_path):
    md = tmp_path / "SKILL.md"
    md.write_text("```bash\ngh issue list --state open\ngrep -rn foo .\n```\n")
    assert fenced_blocks(md, "bash") == [
        "gh issue list --state open\ngrep -rn foo .\n"]


def test_guard_covers_every_extraction_not_just_remembered_call_sites():
    """The guard is inside `fenced_blocks`, so the live extractors inherit it.

    Asserting this explicitly stops a refactor from moving the check out to the
    call sites, where it would only protect the ones someone thought of.
    """
    import inspect
    src = inspect.getsource(fenced_blocks)
    assert "assert_read_only" in src, (
        "the read-only guard must run inside fenced_blocks — a guard the caller "
        "must remember to invoke protects only the call sites someone thought of"
    )


def test_guard_catches_the_commands_a_denylist_missed():
    """Regression for the gaps a hand-enumerated denylist left open.

    Every command below was absent from the first version of this guard. Under an
    allowlist they are caught by construction rather than by having been recalled.
    """
    for cmd in [
        "gh issue reopen 12",
        "gh pr edit 3 --title x",
        "gh pr comment 3 --body hi",
        "gh pr review 3 --approve",
        "gh workflow run deploy.yml",
        "gh label delete stale",
        "git rm -r src",
        "git reset --hard origin/main",
        "git clean -fd",
        "git tag -d v1",
    ]:
        assert mutating_commands(cmd), f"{cmd!r} slipped past the guard"


def test_guard_catches_a_graphql_mutation_that_bypasses_method_flags():
    """`gh api graphql -f query='mutation {...}'` carries no -X/--method flag."""
    assert mutating_commands("gh api graphql -f query='mutation { addComment }'")
    # a plain GET through gh api stays legal
    assert not mutating_commands("gh api repos/o/r/pages")


def test_guard_still_allows_every_read_only_gh_command_in_the_corpus():
    """The allowlist must not red CI on the read-only commands skills actually document."""
    for cmd in [
        "gh pr list --state open",
        "gh pr view 3 --json state",
        "gh pr checks 3 --json name,state,bucket",
        "gh issue list --label 'minerva:followup' --state open",
        "gh issue view 76",
        "gh label list",
        "gh repo view --json defaultBranchRef",
        "gh run view 12",
        "gh auth status",
    ]:
        assert not mutating_commands(cmd), f"{cmd!r} wrongly rejected as mutating"
