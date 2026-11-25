"""Skills never type a branch or ref name into a command, or anything into Python source.

Branch and ref names come from the repository, which may not be the user's, so the runtime
contract's "Names are data" has the shell obtain them and pass them quoted. This guard reads
every code span and fenced block of every skill file and fails closed
(`2026-08-22-pattern-a-denylist-safety-guard-fails-open`): each `<placeholder>` must be
classified below, and each `$variable` must be one this module names. A new placeholder or
variable fails until someone decides what it holds.

It never executes what it reads, so it does not use `fenced_blocks`, whose read-only guard
exists for extractors that run their snippets. Fences are found with the shared grammar
(`knowledge_spans.FENCE_RE`).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from knowledge_spans import FENCE_RE
from tests.test_minerva_runtime import default_branch_snippet
from tests.test_skill_snippets import fenced_blocks

SKILLS = Path(__file__).resolve().parents[1] / "plugins" / "minerva" / "skills"
RUNTIME = SKILLS / "using-minerva" / "references" / "runtime.md"

# A checked unit id (runtime contract, "Names are data"): the only name a command may hold
# as a placeholder, and never inside Python source.
UNIT = {"date-slug", "slug"}
# Branch and ref names. Never in any span.
REF = {"default-branch", "default", "branch", "branch name", "next branch", "git-user",
       "strategy"}
# Placeholders that hold no branch or ref name: counts, numbers from `gh --json`, paths the
# agent makes, naming patterns, and fields of report templates and reviewer briefs.
INERT = {
    # numbers read from `gh ... --json`
    "pr", "pr-number", "run-id", "N",
    # paths and files the agent makes or a helper printed
    "absolute-body-file", "absolute-title-file", "file", "files", "unit-dir",
    "scripts", "topic", "stem", "old-stem",
    # naming patterns and skill or host names, never a branch
    "YYYY-MM-DD", "type", "date", "orchestrator", "project", "suffix",
    # report templates, briefs and prose fields
    "list", "list with branch names", "list — needs manual review", "message",
    "apparent conflict", "level", "that level's definition from step 2",
    "failure scenario it closes", "relationship", "direction", "title", "recommendation",
    "url", "timestamp", "short description", "topic or list", "why", "evidence",
    "one-sentence reason", "one line", "one-line summary", "accept | revise | reject",
    "accept | revise", "proceed | escalate", "the converged direction, in one phrase",
    "the converged direction", "agent files modified", "pattern at file:line",
    "nameWithOwner", "the todo", "repo", "seed", "slug-or-one-line-goal",
    "2-4 content words from the request", "paths", "approved goal", "approved motivation",
    "concrete, checkable item 1", "concrete, checkable item 2", "any remaining items",
    "short, declarative title", "one or two sentences",
    "what was discovered, what broke, what assumption was wrong",
    "the item's full prose, verbatim from the scratchpad",
    "specific inputs or state → wrong output, crash, data loss, or exposure",
    "Short, declarative title — what was decided, fixed, or discovered",
    "≤15-word condensation of the Finding — the entry's catalog line",
    "approved approach — will be rewritten by minerva:promote to describe what shipped",
    "each item must be objectively answerable yes/no when implementation is \"done\"",
    "omit this section entirely for a unit that fits one PR — which is most units",
    "bullets derived from proposal's ## Why and scratchpad highlights",
}
# Generic names that could hold anything, a branch included: allowed in prose and templates,
# never in a git or gh command.
AMBIGUOUS = {"name", "target", "x", "X", "unit", "path", "entry", "n"}
GIT_COMMAND = re.compile(r"(?:^|[;&|(]\s*|\$\(\s*)(?:git|gh)\s")
# Variables a span may expand. The ones that can hold a name must always be double-quoted.
NAME_VARS = {"BASE", "BASE_NAME", "b", "UNIT", "U", "u", "s", "D", "BR", "KEY"}
OTHER_VARS = {
    "PLUGIN_SCRIPTS", "ROOT", "WT", "MINERVA_PLUGIN_ROOT", "MINERVA_SKILL_FILE",
    "MINERVA_SCRIPTS", "WORK_ROOT", "MERGED", "PWD", "HOME", "1", "2", "3", "n", "sha", "ref",
    "LEVEL", "COLOUR", "DEFINITION", "USABLE", "headline",  # promote's issue filing
    "minerva",  # Codex's `$minerva:<name>` skill prefix, not a shell variable
}
PLACEHOLDER = re.compile(r"<([^<>!/\s`][^<>\n`]{0,80})>")
REF_CONTEXT = re.compile(r"(?:refs/heads/|refs/remotes/origin/|origin/)<([^<>\n]+)>")
VARIABLE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*|[0-9@*])")
PYTHON_C = re.compile(r"python3?\s+(?:-[A-Za-z]+\s+)*-c\s+(\S)")
PYTHON_HEREDOC = re.compile(r"python3?\s[^\n]*?<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)^\s*\1\s*$", re.S | re.M)
BRANCH_CUT = re.compile(r"worktree\s+add\b|checkout\b[^\n|;&]*\s-[bB]\b|switch\b[^\n|;&]*\s-[cC]\b"
                        r"|\bbranch\s+(?:-\S+\s+)*[^-\s\"]\S*\s+\"?\$\{BASE")
# The lorestrom plugin's skills are scanned by the same rules, with its own classifications.
# None holds a branch or ref name: ids from Lorestrom's tools, paths and digests
# `import-list` printed, the helper's normalized remote label, and template fields.
LORESTROM_SKILLS = SKILLS.parents[1] / "lorestrom" / "skills"
LORESTROM_RUNTIME = LORESTROM_SKILLS / "using-lorestrom" / "references" / "runtime.md"
LORESTROM_INERT = {
    "org id", "workspace id", "client id", "projectId", "listed path", "listed digest",
    "label", "server", "tool", "operation", "git-common-dir",
    "minerva:theme", "minerva:id", "minerva:summary",
    # 0.2.0: Lorestrom ids and keys, a commit the helper checks as 40 hex digits (never a ref),
    # a phase number, a temp file the agent made, and report and template fields
    "project id", "unit key", "record", "path without .md", "token", "temp file", "sha",
    "phase", "entry id", "markdown", "the draft", "the proposal record",
    "head names of MERGED PRs", "value", "list with reason", "unit — doc — code",
    # 0.5.0: the migration's temp files, holding paths `removal-plan` wrote and a message
    "remove file", "message file",
}
LORESTROM_VARS = {
    "LORESTROM_PLUGIN_ROOT", "LORESTROM_SKILL_FILE", "LORESTROM_SCRIPTS",
    "F",  # a mktemp file the agent made
    "T", "B",  # promote's issue title and body mktemp files
    "lorestrom",  # Codex's `$lorestrom:<name>` skill prefix, not a shell variable
}
# Lines that name a ref placeholder in prose or in a report the user reads, never in a
# command: (file, the exact line or inline span) -> why.
PROSE_EXEMPT = {
    ("ship/references/protocol.md", "Branch:        <branch name>"): "final report template",
    ("ship/references/protocol.md", "<next branch>"): "next step named in prose",
    ("status/SKILL.md", "origin/<default>"): "prose: what the table prints",
    ("status/references/tables.md", "origin/<default>"): "prose: what the table prints",
}


def spans(md: Path):
    """(kind, text, line) for every fenced block and every inline code span in `md`.

    kind is the fence's info string ("" for none) or "inline".
    """
    lines = md.read_text().splitlines()
    fence, body, start, marker = None, [], 0, ""
    for number, line in enumerate(lines, 1):
        if FENCE_RE.match(line):
            run = re.match(r"\s*(`+|~+)", line).group(1)
            if fence is None:
                fence, body, start, marker = line.strip()[len(run):].strip(), [], number, run
                continue
            # Only a fence of the same character, at least as long, with no info string closes.
            if run[0] == marker[0] and len(run) >= len(marker) and not line.strip()[len(run):]:
                yield fence, "\n".join(body), start
                fence = None
                continue
        if fence is not None:
            body.append(line)
            continue
        for match in re.finditer(r"``(.+?)``|`([^`\n]+)`", line):
            yield "inline", match.group(1) or match.group(2), number


def python_sources(kind: str, text: str):
    """Every piece of Python source in a span: a python block, or a `python3 -c` argument."""
    if kind == "python":
        yield text, None
        return
    for match in PYTHON_HEREDOC.finditer(text):
        yield match.group(2), None
    for match in PYTHON_C.finditer(text):
        quote = match.group(1)
        rest = text[match.end():]
        closing = re.search(r"(?<!\\)'" if quote == "'" else r'(?<!\\)"', rest)
        yield (rest[:closing.start()] if closing else rest), quote


def quoting(text: str, index: int) -> str:
    """'single', 'double' or '' for the quoting around `index`.

    Scans its line, tracking `$(...)`, which opens a fresh quoting level, and backslashes.
    """
    levels, single, i = [False], False, text.rfind("\n", 0, index) + 1
    while i < index:
        char = text[i]
        if single:
            single = char != "'"
        elif char == "\\":
            i += 1
        elif char == "'" and not levels[-1]:
            single = True
        elif char == '"':
            levels[-1] = not levels[-1]
        elif text.startswith("$(", i):
            levels.append(False)
            i += 1
        elif char == ")" and len(levels) > 1 and not levels[-1]:
            levels.pop()
        i += 1
    return "single" if single else "double" if levels[-1] else ""


def subshell_depth(text: str, index: int) -> int:
    """How many `$(...)` levels enclose `index` on its line."""
    depth, i = 0, text.rfind("\n", 0, index) + 1
    while i < index:
        if text.startswith("$(", i):
            depth, i = depth + 1, i + 1
        elif text[i] == ")" and depth:
            depth -= 1
        i += 1
    return depth


def violations(where: str, kind: str, text: str, runtime_snippet: bool = False,
               rel: str = "", extra_inert=frozenset(), extra_vars=frozenset()) -> list:
    found = []
    text = re.sub(r"\\\n\s*", " ", text)  # a command continued across lines is one line
    for line in text.splitlines():
        exempt = (rel, line.strip()) in PROSE_EXEMPT
        for name in PLACEHOLDER.findall(line):
            if name not in UNIT | REF | INERT | AMBIGUOUS | extra_inert:
                found.append(f"{where}: unclassified placeholder <{name}>")
            elif name in REF and not exempt:
                found.append(f"{where}: branch or ref placeholder <{name}>")
            elif name in AMBIGUOUS and GIT_COMMAND.search(line):
                found.append(f"{where}: generic placeholder <{name}> in a git or gh command")
        for name in REF_CONTEXT.findall(line):
            if name not in UNIT and not exempt:
                found.append(f"{where}: a placeholder used as a ref name: <{name}>")
    for source, quote in python_sources(kind, text):
        if quote == '"' and re.search(r"[$`]", source):
            found.append(f"{where}: Python source in double quotes takes shell text")
        if PLACEHOLDER.search(source):
            found.append(f"{where}: placeholder inside Python source")
    for match in VARIABLE.finditer(text):
        name = match.group(1)
        quote = quoting(text, match.start())
        if quote == "single":
            continue  # literal text, e.g. an awk field or Python inside single quotes
        if name not in NAME_VARS | OTHER_VARS | extra_vars:
            found.append(f"{where}: unknown variable ${name}")
        elif name in NAME_VARS and not runtime_snippet and quote != "double":
            found.append(f"{where}: ${name} is not double-quoted")
        elif name in {"BASE", "BASE_NAME"} and not runtime_snippet \
                and not text.startswith(":?}", match.end()):
            found.append(f"{where}: ${name} without :? (a skipped snippet would go unnoticed)")
        elif name in {"BASE", "BASE_NAME"} and not runtime_snippet \
                and subshell_depth(text, match.start()):
            found.append(f"{where}: ${name} inside $(...), where :? cannot stop the call")
    for line in text.splitlines():
        if "${BASE:?}" in line and BRANCH_CUT.search(line) and "--no-track" not in line:
            found.append(f"{where}: a branch cut from BASE without --no-track")
        piped = re.search(r"(?<![|])\|(?![|])", line)
        if piped and re.search(r"\$\{BASE(?:_NAME)?:\?\}", line) and not runtime_snippet \
                and not re.match(r'\s*:\s+"\$\{BASE(?:_NAME)?:\?\}"\s*&&', line):
            found.append(f"{where}: BASE in a pipeline without a leading : \"${{BASE:?}}\" &&")
    return found


def corpus_violations(skills=SKILLS, runtime=RUNTIME, extra_inert=frozenset(),
                      extra_vars=frozenset()) -> list:
    found = []
    for md in sorted(skills.rglob("*.md")):
        for kind, text, line in spans(md):
            where = f"{md.relative_to(skills)}:{line}"
            snippet = md == runtime and "unset BASE BASE_NAME" in text
            found += violations(where, kind, text, runtime_snippet=snippet,
                                rel=str(md.relative_to(skills)), extra_inert=extra_inert,
                                extra_vars=extra_vars)
    return found


def test_no_skill_types_a_name_into_a_command_or_python_source():
    assert corpus_violations() == []


def test_no_lorestrom_skill_types_a_name_into_a_command_or_python_source():
    assert list(LORESTROM_SKILLS.rglob("*.md"))
    assert corpus_violations(LORESTROM_SKILLS, LORESTROM_RUNTIME, frozenset(LORESTROM_INERT),
                             frozenset(LORESTROM_VARS)) == []


def test_lorestroms_classifications_do_not_widen_minervas():
    assert not LORESTROM_INERT & (UNIT | REF | AMBIGUOUS)
    assert not LORESTROM_VARS & NAME_VARS


@pytest.mark.parametrize("text", ["git log <name>", "gh pr view <a-new-placeholder>",
                                  "git push origin <branch>", 'echo "$UNKNOWN"'])
def test_the_lorestrom_scan_still_fails_closed(text):
    assert violations("sample", "inline", text, extra_inert=frozenset(LORESTROM_INERT),
                      extra_vars=frozenset(LORESTROM_VARS))


@pytest.mark.parametrize("kind,text", [
    ("inline", "git show <default-branch>:.gitignore"),
    ("inline", "git branch --merged <default>"),
    ("inline", "gh pr view <branch> --json state"),
    ("inline", "git checkout -b x origin/<name>"),
    ("inline", "gh pr merge --auto <strategy> <pr-number>"),
    ("bash", "python3 -c \"import sys; print('<date-slug>')\""),
    ("bash", "python3 -c 'print(\"<date-slug>\")'"),
    ("python", "slug = '<date-slug>'"),
    ("bash", 'python3 -c "import sys; print(\'$UNIT\')"'),
    ("inline", "git worktree add -b <date-slug> p \"${BASE:?}\""),
    ("inline", "git diff ${BASE:?}...HEAD"),
    ("inline", "git diff \"$BASE\"...HEAD"),
    ("inline", "gh pr list --head $b"),
    ("inline", "git log -1 \"$BRANCH\""),
    ("inline", "git log <a-new-placeholder>"),
    ("inline", "git push origin <name>"),
    ("inline", "gh pr view <target> --json state"),
    ("inline", "git log <x>"),
    ("inline", "git checkout -B x \"${BASE:?}\""),
    ("inline", "git checkout -q -b x \"${BASE:?}\""),
    ("inline", "git branch x \"${BASE:?}\""),
    ("bash", "git worktree add -b x \\\n  p \"${BASE:?}\""),
    ("inline", "git diff \"$(git merge-base \"${BASE:?}\" HEAD)\"...HEAD"),
    ("inline", "git show \"${BASE:?}:.gitignore\" | grep -q x"),
    ("bash", "python3 - \"$PLUGIN_SCRIPTS\" <<'PY'\nprint('<date-slug>')\nPY"),
    ("inline", "git log $@"),
])
def test_the_guard_fails_on_each_shape_it_exists_to_catch(kind, text):
    assert violations("sample", kind, text)


def test_the_rule_and_the_listing_are_in_the_runtime_contract():
    text = RUNTIME.read_text()
    assert "## Names are data" in text
    assert 'minerva_runtime.py" units' in text
    assert "unset BASE BASE_NAME" in text


UNIT_COMMAND = re.compile(r"^(?:(?:git|gh|python3|cd)\b|U=|UNIT=).*<(?:date-slug|slug)>", re.S)


def test_every_skill_file_running_a_unit_id_command_points_at_the_rule():
    missing = sorted({str(md.relative_to(SKILLS)) for md in SKILLS.rglob("*.md")
                      for kind, text, _ in spans(md)
                      if any(UNIT_COMMAND.match(line.strip()) for line in text.splitlines())
                      and "Names are data" not in md.read_text()})
    assert missing == []


# --- The default-branch snippet, executed (read-only) in scratch repositories ---------------

def _git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=f@example.invalid",
                           "-c", "commit.gpgSign=false", "-C", str(repo), *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def _repo(tmp_path, branch, origin=False, local=True):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "fixture")
    if origin:
        _git(repo, "update-ref", f"refs/remotes/origin/{branch}", "HEAD")
        _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", f"refs/remotes/origin/{branch}")
    if not local:
        _git(repo, "checkout", "-q", "--detach")
        _git(repo, "branch", "-q", "-D", branch)
    return repo


def _base(repo, shell="bash"):
    snippet = default_branch_snippet()
    probe = snippet + '\nprintf "%s\\n%s\\n" "${BASE:?}" "${BASE_NAME:?}"\n'
    result = subprocess.run([shell, "-c", probe], cwd=repo, capture_output=True, text=True,
                            env={**os.environ, "BASE": "refs/heads/inherited", "BASE_NAME": "x"})
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


@pytest.mark.parametrize("branch,origin,local,expected", [
    ("main", True, True, "refs/heads/main"),
    ("master", False, True, "refs/heads/master"),
    ("main", True, False, "refs/remotes/origin/main"),
    ("rel/odd'name$x", True, True, "refs/heads/rel/odd'name$x"),
])
@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_the_default_branch_snippet_resolves_each_layout(tmp_path, branch, origin, local,
                                                         expected, shell):
    if not shutil.which(shell):
        pytest.skip(f"{shell} not installed")
    assert _base(_repo(tmp_path, branch, origin, local), shell) == [expected, branch]


def test_the_snippet_stops_a_call_when_nothing_resolves(tmp_path):
    repo = _repo(tmp_path, "trunk")
    result = subprocess.run(["bash", "-c", default_branch_snippet() + '\ngit rev-parse "${BASE:?}"'],
                            cwd=repo, capture_output=True, text=True,
                            env={**os.environ, "BASE": "refs/heads/trunk"})
    assert result.returncode != 0


def test_an_origin_only_cut_lands_on_the_new_branch_with_no_upstream(tmp_path):
    # The test's own command, in its own scratch repository: skill text is never executed here.
    repo = _repo(tmp_path, "main", origin=True, local=False)
    base, _ = _base(repo)
    worktree = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "--no-track", "-b", "2026-09-12-unit", str(worktree), base)
    assert _git(worktree, "branch", "--show-current") == "2026-09-12-unit"
    assert _git(worktree, "rev-parse", "HEAD") == _git(repo, "rev-parse", base)
    upstream = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--abbrev-ref", "@{upstream}"],
                              capture_output=True, text=True)
    assert upstream.returncode != 0
    assert subprocess.run(["git", "-C", str(repo), "show-ref", "--verify", "--quiet",
                           "refs/heads/main"]).returncode != 0


@pytest.mark.parametrize("skill,document", [("ship", "protocol.md"), ("cleanup", "phased-units.md")])
def test_phase_snippets_read_merges_against_the_resolved_default_branch(tmp_path, skill, document):
    """A default branch not named main: the snippets must use BASE, not a name of their own."""
    unit = "2026-09-12-example"
    repo = _repo(tmp_path, "trunk", origin=True)   # origin/HEAD names the default branch
    _git(repo, "branch", unit)
    worktree = repo / ".minerva" / "worktrees" / unit
    _git(repo, "worktree", "add", "-q", str(worktree), unit)
    proposal = worktree / ".minerva" / "work" / unit / "proposal.md"
    proposal.parent.mkdir(parents=True)
    proposal.write_text("# P\n\n## Phases\n\n1. **One** — a.\n2. **Two** — b.\n")
    blocks = fenced_blocks(SKILLS / skill / "references" / document, "bash",
                           contains="from work_status import read_phases")
    assert len(blocks) == 1
    plugin = SKILLS.parent
    block = default_branch_snippet() + "\n" + blocks[0].replace("<date-slug>", unit)
    env = {**os.environ, "MINERVA_PLUGIN_ROOT": str(plugin),
           "MINERVA_SKILL_FILE": str(SKILLS / skill / "SKILL.md"), "MINERVA_SCRIPTS": str(plugin / "scripts")}
    result = subprocess.run(["bash", "-c", block], cwd=repo, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "'merged': 1" in result.stdout and f"'next_branch': '{unit}-phase-2'" in result.stdout


def _block(md: Path, needle: str) -> str:
    found = [text for kind, text, _ in spans(md) if kind == "bash" and needle in text]
    assert len(found) == 1
    return textwrap.dedent(found[0])


def test_the_bare_checkpoint_snippet_records_the_branch_it_reads(tmp_path):
    # In the test's own scratch repository; the snippet writes only an untracked checkpoint.
    odd = "user/odd'name$x"
    repo = _repo(tmp_path, odd)
    env = {**os.environ, "PLUGIN_SCRIPTS": str(SKILLS.parent / "scripts")}
    result = subprocess.run(["bash", "-c", _block(RUNTIME, "hashlib.sha256")], cwd=repo, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    state = json.loads(result.stdout)
    assert state["branch"] == odd
    assert state["unit"] == "bare-" + hashlib.sha256(odd.encode()).hexdigest()


def test_the_in_flight_loop_bounds_local_and_pushed_unit_branches(tmp_path):
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    repo = _repo(tmp_path, "main")
    _git(repo, "remote", "add", "origin", str(origin))
    for name in ("2026-01-02-pushed", "2026-01-03-odd'name$x", "feature/other"):
        _git(repo, "push", "-q", "origin", f"HEAD:refs/heads/{name}")
    _git(repo, "branch", "005-local-only")
    stub = tmp_path / "bin"
    stub.mkdir()
    (stub / "gh").write_text('#!/bin/sh\nprintf "[%s]" "$@"; echo\n')
    (stub / "gh").chmod(0o755)
    block = _block(SKILLS / "propose" / "references" / "in-flight-check.md", "while read")
    env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}"}
    for shell in ("bash", "zsh"):
        if not shutil.which(shell):
            continue
        result = subprocess.run([shell, "-c", block], cwd=repo, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        rows = {line.split("\t")[0]: line for line in result.stdout.splitlines()}
        assert set(rows) == {"2026-01-02-pushed", "2026-01-03-odd'name$x", "005-local-only"}
        assert "[--head][2026-01-03-odd'name$x]" in rows["2026-01-03-odd'name$x"]
