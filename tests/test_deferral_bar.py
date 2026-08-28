"""The deferral bar's structural guarantees.

`minerva:promote` used to file a GitHub issue for any forward-looking scratchpad line a user
chose to keep, and nothing anywhere stated a bar. On this repo that produced ~150 bullets across
24 ``followups.md`` files plus 18 tracker issues — 15 of them filed in a single backfill batch —
and an entire skill written to excavate the result after it rotted. The old ``low`` priority
tier was defined as "It does not matter whether we do it" and filed an issue anyway.

The bar now admits an item only if a concrete **failure scenario** can be written for it. These
tests hold the two halves of that rule which are mechanically checkable: the priority vocabulary
really has three levels, and the documented ``gh issue create`` command really demands the field.

Everything here is hermetic — no network, no ``gh``, no repo state. The live-tracker half of the
enforcement deliberately does NOT live in CI: it rides the ``gh issue list`` call
``minerva:promote`` already makes, so the suite never depends on an external backlog, on auth, or
on a rate limit.
"""
import re
from pathlib import Path

import pytest

from knowledge_spans import unfenced_lines

REPO = Path(__file__).resolve().parent.parent
PROMOTE = REPO / "plugins" / "minerva" / "skills" / "promote" / "references"
GH_ISSUES = PROMOTE / "github-issues.md"
BAR = PROMOTE / "deferral-bar.md"

# A markdown table row: starts and ends with a pipe, and is not the ``|---|---|`` separator.
_ROW_RE = re.compile(r"^\s*\|(?!\s*[-: |]+\|\s*$).*\|\s*$")
_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _priority_table_rows():
    """Body rows of the priority table in github-issues.md.

    Located by its header row rather than by a line number, and read as a TABLE rather than
    grepped for the word ``low``. Searching prose for that string cannot work: it is a substring
    of "follow", "below" and "allow", all of which appear in this very file. Counting the rows
    asks the document what its vocabulary is, instead of asking a human to recall it — the
    discipline `2026-08-11-pattern-the-enumeration-is-what-fails` exists to enforce.
    """
    lines = GH_ISSUES.read_text().splitlines()
    for i, line in enumerate(lines):
        if _ROW_RE.match(line) and "Level" in line and "Meaning" in line:
            rows = []
            for nxt in lines[i + 1:]:
                if _SEP_RE.match(nxt):
                    continue
                if not _ROW_RE.match(nxt):
                    break
                rows.append(nxt)
            return rows
    pytest.fail("no priority table found in github-issues.md — it is the vocabulary of record")


def test_the_priority_vocabulary_has_exactly_three_levels():
    """`low` retired: once every filed item is a defect, "it does not matter whether we do it"
    describes an item that should never have been filed."""
    rows = _priority_table_rows()
    assert len(rows) == 3, f"expected 3 priority levels, found {len(rows)}: {rows}"


def test_the_retired_level_is_absent_from_the_vocabulary():
    """Asserted against the TABLE, not against the file's prose — see `_priority_table_rows`."""
    levels = {r.split("|")[1].strip().strip("`") for r in _priority_table_rows()}
    assert levels == {"critical", "high", "medium"}, levels


def test_the_issue_template_demands_a_failure_scenario():
    """The bar made structural: an item whose failure scenario cannot be written cannot be filed
    by the documented command. Without the field the bar is advice, and this corpus is explicit
    that an unenforced constraint is aspirational
    (`2026-08-11-pattern-an-unenforced-constraint-is-aspirational`)."""
    assert "**Failure scenario**:" in GH_ISSUES.read_text(), (
        "the gh issue create body template lost its required Failure scenario line"
    )


def test_the_failure_scenario_line_is_inside_the_create_command():
    """Not merely mentioned somewhere in the file — present in the heredoc body that is actually
    passed to `gh issue create`. A requirement documented beside the command but absent from it
    is one the command will never enforce."""
    text = GH_ISSUES.read_text()
    start = text.index("gh issue create")
    end = text.index("MINERVA_ISSUE_BODY\n)", start)
    assert "**Failure scenario**:" in text[start:end]


def test_the_bar_states_all_three_outlets():
    """The rule is only complete if every item has somewhere to go. Two outlets plus an implicit
    "leave it in the scratchpad" is how the backlog grew in the first place."""
    body = BAR.read_text()
    for outlet in ("tracker issue", "reference", "Documentation"):
        assert outlet in body, f"deferral-bar.md does not name the {outlet!r} outlet"


def test_the_bar_is_stated_in_exactly_one_place():
    """Single-sourced. Six copies of a block kept in sync by a plea is a shape this project
    already carries once, and the copies had silently diverged by the time anyone checked
    (`2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`).

    The predicate is the bar's own defining sentence; consumers must POINT at the file rather
    than restate it.
    """
    skills = REPO / "plugins" / "minerva" / "skills"
    sentence = "may become a tracker issue only if"
    restaters = [
        p.relative_to(skills)
        for p in sorted(skills.rglob("*.md"))
        if p != BAR and sentence in p.read_text()
    ]
    assert restaters == [], f"the bar is restated instead of referenced in: {restaters}"


CONSUMERS = [
    "review/references/protocol.md",
    "promote/references/modes.md",
    "promote/SKILL.md",
    "propose-ship-auto/references/phases.md",
    "propose-ship-quick/references/phases.md",
    "propose-ship-balanced/references/phases.md",
]


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_every_consumer_points_at_the_bar(consumer):
    """Each place that disposes of a forward-looking item must reach the rule.

    Asserted on the required POINTER, never on how the surrounding sentence is worded. Verifying
    this by grepping for remembered phrasings false-negatived on two of these six files while
    this unit was being written — prose has variants, a required reference does not.
    """
    doc = REPO / "plugins" / "minerva" / "skills" / consumer
    text = "\n".join(unfenced_lines(doc.read_text()))
    assert "deferral-bar.md" in text, (
        f"{consumer} disposes of deferred work but never points at the bar"
    )


_PRIORITY_MENTION_RE = re.compile(r"priority:\s*`?([a-z]+)`?", re.IGNORECASE)


def test_no_skill_prose_uses_a_priority_level_the_table_does_not_define():
    """Catches a retired level surviving in an example, which the table test cannot see.

    Removing `low` from the vocabulary left two live mentions behind — a label colour and a
    `## Deferred work` sample — because the table assertion only ever looks at the table. Both
    were found by hand, which is the unreliable way.

    The legal set is DERIVED from the table rather than written here, so this test cannot drift
    out of agreement with the vocabulary it enforces, and adding a level needs no edit to it.
    Prose that *discusses* the retired tier is fine: the pattern matches a level being USED
    (`priority: low`), not the word appearing in a sentence.
    """
    legal = {r.split("|")[1].strip().strip("`") for r in _priority_table_rows()}
    skills = REPO / "plugins" / "minerva" / "skills"
    offenders = []
    for doc in sorted(skills.rglob("*.md")):
        for line in doc.read_text().splitlines():
            for used in _PRIORITY_MENTION_RE.findall(line):
                if used.lower() not in legal:
                    offenders.append(f"{doc.relative_to(skills)}: {line.strip()}")
    assert offenders == [], (
        f"priority levels used but not defined in the table (legal: {sorted(legal)}):\n"
        + "\n".join(offenders)
    )
