#!/usr/bin/env python3
"""Aggregate the whole minerva workstream into one deterministic status signal.

Five records already answer "where does this project stand" — every unit's `**Status**`
field, the promote marker, the phase topology, the knowledge wiki's health, and the branch
/ PR state. Each has an owner module. Nothing joins them, so the one question a resuming
agent actually asks — *what should I do next?* — is the one question the corpus cannot
answer directly, and answering it by hand means five reads whose join exists only in
someone's head.

**This module is a pure reader.** No subprocess, no network, no git. Everything it needs
from git arrives as the `merged_branches` argument, exactly as `work_status.phase_progress`
takes it — that is what lets these tests run with no repo, no auth and no fixtures, and it
is the established split in this package (`minerva:status` prose does the `git`/`gh`
enrichment and passes the result in).

Every lifecycle predicate here is IMPORTED from `work_status`, never restated. The
in-flight rule already had four prose copies before it was single-sourced, and the promote
marker it reads grew eight spellings while a one-string check misread 16 of 51 units
(`2026-08-11-pattern-the-enumeration-is-what-fails`). A status table that restates any of
them is a sixth copy that drifts silently — and its failure direction is the worst one
available here, because an under-reported workstream renders as "nothing in flight".
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_lint import ENTRY_RE, lint_knowledge, parse_entry  # noqa: E402
from knowledge_spans import unfenced  # noqa: E402
from synthesis_status import synthesis_status  # noqa: E402
from work_status import (  # noqa: E402
    phase_branch,
    phase_progress,
    read_phases,
    unit_state,
)

# The two roots a unit's record can live under, relative to the PRIMARY checkout. Order
# matters: `.minerva/work/` is scanned first so its record wins the dedupe below.
MAIN_WORK_GLOB = ".minerva/work/*"
WORKTREE_WORK_GLOB = ".minerva/worktrees/*/.minerva/work/*"


def _has_scratchpad_body(text: str) -> bool:
    """True iff a scratchpad carries content past the header `minerva:propose` writes.

    This is the discriminator between a unit that was proposed and one somebody actually
    started, and it is the only stage boundary the corpus does not already declare
    outright: `**Status**` distinguishes Draft from Shipped, and the promote marker
    declares promotion, but nothing anywhere says "work began". `minerva:propose` writes a
    header-only scratchpad (an H1 plus one blockquote) and `minerva:work` appends to it, so
    "has a body" is an authored signal rather than a guess about one.

    Only the H1, blockquote lines and blanks are header. **Fenced content counts as
    body** — a pasted traceback is work — so the fence grammar is used INVERTED here
    relative to every other reader in this package. Those ask "is this line a
    declaration", and a fenced example is not one. This one asks "is there anything here
    at all", and for that question a fence is content like any other. The grammar is still
    imported rather than re-derived, per
    `2026-06-11-constraint-fence-scans-import-fence-re`; it is the CONCLUSION drawn from
    it that differs, which is why the difference is written down instead of left to look
    like a mistake.

    What the fence awareness buys is the one case where the two readings diverge: a fenced
    example OF a scratchpad header, pasted into a real scratchpad. Skipping it as header
    would hide the body under it and report a unit somebody is working in as an untouched
    draft.

    Deliberately reached ONLY after `unit_state()["promoted"]` says no. A post-promote
    scratchpad is a marker line, which is a body by this rule; ordering the stage ladder
    promoted-first is what keeps that from reading as live work.
    """
    lines = text.splitlines()
    outside = {i for i, _ in unfenced(lines)}
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if i not in outside:
            return True
        if s.startswith(">") or s.startswith("# "):
            continue
        return True
    return False


def unit_record(unit_dir, merged_branches=()) -> dict:
    """One unit's full status record: lifecycle state, stage, and phase progress.

    `unit_dir`'s basename is the `<date-slug>` — the identity every other surface uses
    (the branch name, the worktree directory, the wikilink `**Context**` path).
    """
    d = Path(unit_dir)
    slug = d.name
    state = dict(unit_state(d))

    proposal = d / "proposal.md"
    proposal_text = proposal.read_text() if proposal.is_file() else ""
    phases = read_phases(proposal_text)

    scratchpad = d / "scratchpad.md"
    has_body = _has_scratchpad_body(scratchpad.read_text()) if scratchpad.is_file() else False

    return {
        "slug": slug,
        **state,
        "stage": _stage(state, has_body),
        "phases": [{"position": pos, "title": title, "branch": phase_branch(slug, pos)}
                   for pos, (_written, title) in enumerate(phases, start=1)],
        "progress": phase_progress(phases, merged_branches, slug),
        "worktree_present": False,
    }


def _stage(state: dict, has_scratchpad_body: bool) -> str:
    """The unit's coarse lifecycle stage, from filesystem records alone.

    A ladder, not a lookup, and the rung order is load-bearing: `shipped` before
    `promoted` because a shipped unit is also promoted, and `promoted` before the
    scratchpad test because a post-promote scratchpad holds a marker that would otherwise
    read as a body. Reordering these silently reclassifies finished work as live.
    """
    if (state.get("status") or "").startswith("Shipped"):
        return "shipped"
    if state.get("promoted"):
        return "promoted"
    return "in-progress" if has_scratchpad_body else "draft"


def _knowledge(kd: Path) -> dict:
    """Wiki health, entirely via the owner modules' importable APIs.

    A knowledge dir that does not exist is reported as absent rather than as a clean
    corpus of zero entries — `2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state`:
    an empty result and a missing target look identical downstream, and only one of them
    is good news.
    """
    if not kd.is_dir():
        return {"exists": False}

    by_type = {}
    for p in sorted(kd.glob("*.md")):
        if not ENTRY_RE.match(p.name):
            continue
        declared = parse_entry(p)["declared_type"] or "unknown"
        by_type[declared] = by_type.get(declared, 0) + 1

    findings = lint_knowledge(kd)
    synth = synthesis_status(kd)
    return {
        "exists": True,
        "entries": sum(by_type.values()),
        "by_type": by_type,
        "lint_errors": sum(1 for f in findings if f.severity == "error"),
        "lint_warnings": sum(1 for f in findings if f.severity == "warning"),
        "overview_exists": synth["overview_exists"],
        "unsynthesized": len(synth["unsynthesized"]),
        "link_rot": len(synth["link_rot"]),
    }


def workstream_status(root, merged_branches=()) -> dict:
    """The whole workstream's status for the checkout rooted at `root`.

    `root` must be the **primary checkout**, not the current working tree. A linked
    worktree contains no `.minerva/worktrees/` directory at all, so resolving `root` with
    `git rev-parse --show-toplevel` — which every other minerva skill uses, correctly, for
    its own per-branch target — reports every sibling unit as absent when this runs from
    inside a worktree. That is where `minerva:work` sessions live. The caller resolves the
    primary checkout with `--git-common-dir`; see `minerva:status`.

    Returns `{units, counts, knowledge}`. `units` is sorted by slug, which sorts by date
    first because a slug is `<YYYY-MM-DD>-<name>`.
    """
    root = Path(root)

    records = {}
    for pattern in (MAIN_WORK_GLOB, WORKTREE_WORK_GLOB):
        for d in sorted(root.glob(pattern)):
            if not d.is_dir() or not (d / "proposal.md").is_file():
                continue
            # A slug reachable from both roots is one unit seen twice, not two units. The
            # main-tree record wins because it is the authoritative post-merge copy, which
            # is what the glob ORDER above encodes; the guard is what makes that order the
            # rule rather than a comment about it. The second glob still has to run: a
            # unit created in a worktree and not yet merged exists ONLY there.
            if d.name not in records:
                records[d.name] = unit_record(d, merged_branches)

    # `worktree_present` asks whether `.minerva/worktrees/<slug>/` is on disk — NOT whether
    # the slug was reachable through the worktree glob above. Those are not the same
    # question, and conflating them is a live-corpus bug this had before the first smoke
    # run: every worktree carries the whole COMMITTED `.minerva/work/` history, so the
    # glob sees all 65 units through any one worktree and the flag read true for every
    # unit in the project. The directory test is the one that means what the reader thinks.
    for slug, rec in records.items():
        rec["worktree_present"] = (root / ".minerva" / "worktrees" / slug).is_dir()

    units = [records[k] for k in sorted(records)]
    return {
        "units": units,
        "counts": _counts(units),
        "knowledge": _knowledge(root / ".minerva" / "knowledge"),
    }


def _counts(units: list) -> dict:
    """Rollup totals. `in_flight` is the imported policy predicate, never a stage test."""
    stages = {}
    for u in units:
        stages[u["stage"]] = stages.get(u["stage"], 0) + 1
    return {
        "total": len(units),
        "in_flight": sum(1 for u in units if u["in_flight"]),
        "worktrees_present": sum(1 for u in units if u["worktree_present"]),
        "phased_incomplete": sum(1 for u in units
                                 if u["progress"]["phased"] and not u["progress"]["complete"]),
        "by_stage": stages,
    }


def main(argv=None) -> int:
    """`workstream_status.py [root] [merged-branch ...]` -> JSON on stdout."""
    argv = argv if argv is not None else sys.argv[1:]
    root = argv[0] if argv else "."
    print(json.dumps(workstream_status(root, argv[1:]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
