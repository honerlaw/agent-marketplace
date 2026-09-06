"""Tests for `scripts/decision_telemetry.py` — the decision-log tally.

Three guards beyond the grammar itself:

- **The tag vocabulary is read from the skills, not restated here.** Each orchestrator's
  logging reference carries a fenced example block of decision lines; every `[tag]` in
  those blocks must classify to a non-`unknown` outcome. A tag added to a skill's prose but
  not to the script goes red (`2026-08-11-pattern-the-enumeration-is-what-fails`).
- **Fenced examples are not records** — the same fence-aware rule every corpus reader here
  follows, via the single-sourced `knowledge_spans` primitive.
- **The live corpus** is asserted for properties, not for today's counts, which would rot
  the moment this unit's own run logs a line
  (`2026-08-28-pattern-a-corpus-assertion-must-survive-its-own-first-instance`).
"""
import re
from pathlib import Path

import pytest

from decision_telemetry import (
    LINE_RE,
    UNKNOWN,
    classify_tag,
    collect,
    main,
    outcome_totals,
    split_gate,
    normalize_gate,
    parse_scratchpad,
    problems,
    recheck_summary,
    render,
    scratchpad_files,
    tally,
    units_with,
)
from knowledge_spans import unfenced

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

# (skill file carrying the fenced logging example, the orchestrator its lines belong to)
LOGGING_EXAMPLES = {
    "propose-ship-balanced/references/verify-protocol.md": "Balanced",
    "propose-ship-quick/references/solo-decision-protocol.md": "Quick",
    "propose-ship-auto/references/panel-protocol.md": "Panel",
    "round-table/SKILL.md": "Panel",
}

BALANCED = """# Scratchpad: x

## Balanced decisions 2026-09-05
- [decided] whole-proposal soundness: fine (solo)
- [reviewed — clean] scope check: single unit (Skeptic accept)
- [reviewed — folded] approach: option B (Skeptic surfaced C)
- [rechecked — clean] approach: fold-audit confirmed
- [reviewed — folded] scope check: missed README
- [rechecked — escalated] scope check: item 1 not addressed — user chose include
- [escalated to user] scope of the seed: ambiguous
- [process note] resumed after context reset

## Review triage 2026-09-05
- [reviewed — folded] this is NOT a decision line, wrong section
"""


def test_parses_balanced_section_and_stops_at_next_heading():
    recs = parse_scratchpad(BALANCED, "u", "u/scratchpad.md")
    assert [r.outcome for r in recs] == [
        "decided", "reviewed-clean", "reviewed-folded", "rechecked-clean",
        "reviewed-folded", "rechecked-escalated", "escalated", "process-note",
    ]
    assert all(r.orchestrator == "Balanced" and r.date == "2026-09-05" for r in recs)
    assert [r.gate for r in recs][:3] == ["whole-proposal", "scope", "approach"]
    assert recs[6].gate == "scope"  # "scope of the seed" normalises to scope


def test_rechecks_pair_by_adjacency_and_same_gate():
    recs = parse_scratchpad(BALANCED, "u", "u/scratchpad.md")
    assert recs[3].paired_with_lineno == recs[2].lineno and recs[2].rechecked == "rechecked-clean"
    assert recs[5].paired_with_lineno == recs[4].lineno and recs[4].rechecked == "rechecked-escalated"
    assert problems(recs) == []
    summary = recheck_summary(recs)
    assert summary["folded"] == 2 and summary["folded-and-rechecked"] == 2
    assert summary["folded-unchecked"] == 0


def test_orphan_recheck_is_a_problem_not_a_fold():
    text = "## Balanced decisions 2026-09-05\n- [rechecked — clean] approach: nothing before me\n"
    recs = parse_scratchpad(text, "u", "p")
    assert recs[0].outcome == "rechecked-clean"
    assert problems(recs) == ["p:2: orphan re-check: no [reviewed — folded] line for the same gate immediately before it"]
    text2 = ("## Balanced decisions 2026-09-05\n- [reviewed — folded] approach: x\n"
             "- [rechecked — clean] scope check: different gate\n")
    assert len(problems(parse_scratchpad(text2, "u", "p"))) == 1


def test_unknown_tag_is_kept_and_reported():
    text = "## Balanced decisions 2026-09-05\n- [rubber-stamped] approach: nope\n"
    recs = parse_scratchpad(text, "u", "p")
    assert recs[0].outcome == UNKNOWN
    assert problems(recs) == ["p:2: unknown tag [rubber-stamped]"]


def test_fenced_examples_are_not_records():
    text = ("## Balanced decisions 2026-09-05\n```\n- [decided] approach: fenced example\n"
            "- [reviewed — folded] scope check: also fenced\n```\n")
    assert parse_scratchpad(text, "u", "p") == []


def test_dash_and_case_variants_of_a_tag_classify_identically():
    for tag in ("reviewed — folded", "reviewed - folded", "Reviewed – Folded", "reviewed—folded"):
        assert classify_tag("Balanced", tag) == "reviewed-folded", tag


@pytest.mark.parametrize("raw,expected", [
    ("scope check", "scope"), ("scope of the seed", "scope"), ("approach selection", "approach"),
    ("approach r2 (X′)", "approach"), ("whole-proposal acceptance, round 1", "whole-proposal"),
    ("completion verification", "completion"), ("success criteria verification", "completion"),
    ("mid-work divergence", "divergence"), ("replan-vs-FIX", "replan-vs-fix"),
    ("new-plan acceptance", "replan-acceptance"), ("replan acceptance", "replan-acceptance"),
    ("review triage", "triage"), ("promote partition", "partition"), ("TODO disposition", "todo"),
    ("pre-flight + scope", "scope"),  # scope wins over preflight: it is earlier in the rules
    ("something bespoke", "other:something bespoke"),
])
def test_gate_normalization(raw, expected):
    assert normalize_gate(raw) == expected


@pytest.mark.parametrize("tag,expected", [
    ("3/3 accept", "panel-accept"), ("2/3 accept, skeptic dissented", "panel-accept"),
    ("2/3 accept → revise → 3/3 accept", "panel-revised"), ("1/3 accept — REVISE", "panel-revised"),
    ("3/3 accept, vote 2", "panel-revised"), ("0/3 accept → revised", "panel-revised"),
    ("skipped — small", "skipped"), ("user-directed", "user-directed"),
    ("escalated to user", "escalated"), ("escalated/panel", "escalated"),
    ("banana", UNKNOWN),
])
def test_panel_tag_heuristics(tag, expected):
    assert classify_tag("Panel", tag) == expected


def _fenced_decision_tags(text: str) -> list[str]:
    """`[tag]`s of decision lines INSIDE code fences — the inverse of `unfenced`, derived as
    its complement so the fence grammar stays single-sourced (no fence loop of our own).
    Delimiter lines land in the complement too; none of them matches `LINE_RE`."""
    lines = text.splitlines()
    outside = {i for i, _ in unfenced(lines)}
    return [m.group("tag") for i, line in enumerate(lines)
            if i not in outside and (m := LINE_RE.match(line))]


@pytest.mark.parametrize("rel,orch", sorted(LOGGING_EXAMPLES.items()))
def test_every_documented_tag_classifies(rel, orch):
    text = (SKILLS_DIR / rel).read_text(encoding="utf-8")
    tags = _fenced_decision_tags(text)
    assert tags, f"{rel}: no fenced decision-line examples found — the extractor is vacuous"
    unknown = [t for t in tags if classify_tag(orch, t) == UNKNOWN]
    assert not unknown, f"{rel}: documented tags the script cannot classify: {unknown}"


def test_balanced_examples_document_every_recheck_outcome():
    """The fold-audit vocabulary is three tags; the skill's own example must show all three,
    or the vocabulary test above passes without ever exercising them."""
    text = (SKILLS_DIR / "propose-ship-balanced/references/verify-protocol.md").read_text()
    tags = {classify_tag("Balanced", tag) for tag in _fenced_decision_tags(text)}
    assert {"rechecked-clean", "rechecked-residual-folded", "rechecked-escalated"} <= tags


def test_scan_scope_excludes_worktrees(tmp_path):
    (tmp_path / ".minerva/work/u1").mkdir(parents=True)
    (tmp_path / ".minerva/work/u1/scratchpad.md").write_text("## Quick decisions 2026-01-01\n- [decided] approach: a\n")
    (tmp_path / ".minerva/work/u1/archive").mkdir()
    (tmp_path / ".minerva/work/u1/archive/scratchpad-old.md").write_text("## Quick decisions 2026-01-01\n- [decided] scope check: b\n")
    (tmp_path / ".minerva/worktrees/u2/.minerva/work/u2").mkdir(parents=True)
    (tmp_path / ".minerva/worktrees/u2/.minerva/work/u2/scratchpad.md").write_text("## Quick decisions 2026-01-01\n- [decided] approach: c\n")
    files = scratchpad_files(tmp_path)
    assert [str(f.relative_to(tmp_path)) for f in files] == [
        ".minerva/work/u1/scratchpad.md", ".minerva/work/u1/archive/scratchpad-old.md"]
    recs = collect(tmp_path)
    assert len(recs) == 2 and units_with(recs, "Quick") == {"u1"}


def test_render_lists_problems_and_totals():
    with_weird = BALANCED.replace("- [process note]", "- [weird] gate: x\n- [process note]")
    recs = parse_scratchpad(with_weird, "u", "p")
    out = render(recs)
    assert "== Balanced decisions" in out and "re-checks:" in out
    assert "== Problems — 1 ==" in out and "unknown tag [weird]" in out
    assert tally(recs)["Balanced"]["approach"]["reviewed-folded"] == 1


def test_pairing_is_by_line_across_multiple_sections():
    """`paired_with_lineno` names the partner by line, not by index into a per-section list
    that the caller never sees — the second section's re-check must not point at the first
    section's first line."""
    text = ("## Balanced decisions 2026-01-01\n- [decided] scope check: a\n- [decided] approach: b\n"
            "## Balanced decisions 2026-01-02\n- [reviewed — folded] approach: c\n- [rechecked — clean] approach: d\n")
    recs = parse_scratchpad(text, "u", "p")
    assert recs[3].paired_with_lineno == recs[2].lineno == 5
    assert recs[2].rechecked == "rechecked-clean" and problems(recs) == []
    assert [r.date for r in recs] == ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02"]


def test_header_without_a_date_still_opens_a_section():
    recs = parse_scratchpad("## Quick decisions\n- [decided] approach: x\n", "u", "p")
    assert len(recs) == 1 and recs[0].date is None and recs[0].orchestrator == "Quick"


def test_rechecked_with_the_prose_hyphen_classifies():
    assert classify_tag("Balanced", "re-checked — clean") == "rechecked-clean"
    assert classify_tag("Balanced", "Re-checked - residual folded") == "rechecked-residual-folded"


def test_bare_below_quorum_vote_is_a_revision():
    assert classify_tag("Panel", "1/3 accept") == "panel-revised"
    assert classify_tag("Panel", "0/3 accept") == "panel-revised"
    assert classify_tag("Panel", "3/3 reject") == "panel-revised"
    assert classify_tag("Panel", "2/3 accept") == "panel-accept"


def test_gate_split_ignores_colons_inside_backticks():
    assert split_gate("`minerva:ship` mode: pass --auto") == "`minerva:ship` mode"
    assert split_gate("scope check: single unit") == "scope check"
    assert split_gate("approach r2 (X′): rationale") == "approach r2"
    assert split_gate("whole-proposal — folded") == "whole-proposal"
    assert split_gate("a sentence with no separator at all") == "a sentence with no separator at all"


def test_bespoke_gate_pairs_case_insensitively():
    text = "## Balanced decisions 2026-01-01\n- [reviewed — folded] Foo Gate: a\n- [rechecked — clean] foo gate: b\n"
    recs = parse_scratchpad(text, "u", "p")
    assert recs[0].gate == recs[1].gate == "other:foo gate" and recs[0].gate_raw == "Foo Gate"
    assert problems(recs) == []


def test_unreadable_file_is_reported_not_fatal(tmp_path):
    (tmp_path / ".minerva/work/u1").mkdir(parents=True)
    (tmp_path / ".minerva/work/u1/scratchpad.md").write_bytes(b"## Quick decisions 2026-01-01\n- [decided] approach: \xff\xfe\n")
    (tmp_path / ".minerva/work/u2").mkdir()
    (tmp_path / ".minerva/work/u2/scratchpad.md").write_text("## Quick decisions 2026-01-01\n- [decided] approach: ok\n")
    file_problems: list = []
    recs = collect(tmp_path, file_problems)
    assert [r.unit for r in recs] == ["u2"]
    assert file_problems == [".minerva/work/u1/scratchpad.md: unreadable (UnicodeDecodeError) — skipped"]
    assert "unreadable (UnicodeDecodeError)" in render(recs, file_problems)


def test_outcome_totals_and_main(tmp_path, capsys):
    recs = parse_scratchpad(BALANCED, "u", "p")
    assert outcome_totals(recs)["Balanced"]["reviewed-folded"] == 2
    (tmp_path / ".minerva/work/u").mkdir(parents=True)
    (tmp_path / ".minerva/work/u/scratchpad.md").write_text(BALANCED)
    assert main(["decision_telemetry.py", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "== Balanced decisions — 8 lines across 1 units ==" in out and "== Problems — 0 ==" in out


def test_long_other_gates_are_truncated_for_display():
    text = "## Quick decisions 2026-01-01\n- [decided] " + "x" * 80 + "\n"
    out = render(parse_scratchpad(text, "u", "p"))
    assert "other:" + "x" * 33 + "…" in out and "x" * 60 not in out  # 40 chars total, incl. "other:"


# --- live corpus -----------------------------------------------------------------------
def test_live_corpus_properties():
    recs = collect(REPO_ROOT)
    assert len(units_with(recs, "Balanced")) >= 13, "the corpus that motivated this unit had 13 balanced runs"
    assert len(units_with(recs, "Panel")) >= 20
    closed = [r for r in recs if r.orchestrator in ("Balanced", "Quick") and r.problems]
    assert not closed, "Balanced/Quick lines the script could not classify or pair:\n" + "\n".join(
        f"{r.where}: {r.problems} [{r.tag}]" for r in closed)
