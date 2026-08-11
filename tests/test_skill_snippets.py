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


def fenced_blocks(md: Path, lang: str) -> list:
    """Every ```<lang> fenced block in `md`, dedented, as a list of block bodies.

    Fences are matched with a leading-whitespace allowance because a snippet nested in a
    list item is indented, and its body is dedented by the fence's own indent so the
    extracted program is runnable as-is.
    """
    blocks = re.findall(rf"^([ \t]*)```{lang}\n(.*?)^[ \t]*```",
                        md.read_text(), re.S | re.M)
    return [textwrap.dedent(body) if not indent else
            "".join(ln[len(indent):] if ln.startswith(indent) else ln
                    for ln in body.splitlines(keepends=True))
            for indent, body in blocks]


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
