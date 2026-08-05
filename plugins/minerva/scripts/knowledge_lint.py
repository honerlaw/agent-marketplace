#!/usr/bin/env python3
"""Deterministic, read-only health-check for the `.minerva/knowledge/` wiki.

Detects *mechanical* coherence defects only — no content judgment (contradiction /
staleness / orphan detection and any fixing belong to the deferred `minerva:lint`
skill, Phase B.2). The corpus is the source of truth; `index.md` is never assumed
authoritative — index problems are reported as the defect (knowledge entry 017).

Checks:
  0. duplicate NNN   — two entry files sharing a number. Reported FIRST because every
                       other check is NNN-keyed: before this existed, the second entry
                       of a pair silently overwrote the first in the lookup map, so a
                       duplicate was invisible by construction.
  1. index drift     — watermark vs max NNN; NNN-keyed catalog<->file bijection
                       (slug mismatch = warning, not error); Type-section grouping
                       vs each entry's declared **Type**.
  2. broken links    — every [[NNN-...]] in an entry's ## Related block resolves
                       (by NNN) to a real entry. Links read ONLY from the ## Related
                       block, fence-aware.
  3. missing recips  — if A's ## Related links B, B links back to A (presence keyed
                       on NNN, NOT label-match; back-link counts in B's ## Related
                       block OR B's supersession banner).

`minerva:promote` is add-only: on a work-unit branch it writes entry files and leaves
every aggregate/cross-entry write to the reconciliation pass `minerva:cleanup` runs on
the default branch. So the two conditions a not-yet-reconciled entry trips — no catalog
line, and no reverse link for the forward links it declares — are **always warnings**,
never errors, and reconciliation repairs them.

They are deliberately NOT gated on the `index-watermark`. A scalar floor would assume
entries reconcile in NNN order, and they do not: units merge whenever their PRs land.
Unit A takes 050 and unit B takes 051; B merges and reconciles the watermark to 051;
then A merges, and its 050 sits *below* the floor. A floor-based rule calls that drift
— reddening A's branch — and emits no pending warning, which is the signal cleanup
gates reconciliation on, so the entry would never be catalogued at all.

The watermark therefore records only how far the catalog has actually been brought,
and the one thing still checked about it is that it never exceeds max NNN (an index
claiming entries that do not exist is real drift).

CLI: `python3 scripts/knowledge_lint.py <knowledge-dir>` — prints findings grouped
by family and exits non-zero iff any error-severity finding is present.
"""
import re
import sys
from collections import namedtuple
from pathlib import Path

from knowledge_spans import (
    BANNER_MARKER_RE,
    FENCE_RE,
    RELATED_HEADER,
    SECTION_RE,
)

Finding = namedtuple("Finding", ["family", "severity", "message"])  # severity: error|warning

# NNN is `\d{3,}`, not `\d{3}`: the allocator pads to three digits but widens rather
# than wrapping past 999 (wrapping would hand out a guaranteed duplicate). A fixed
# `\d{3}` silently fails to match a 4-digit stem, which would make the 1000th entry
# invisible to BOTH the allocator and the duplicate detector at once. Every NNN is
# captured as its own group — never sliced off a stem with `[:3]`, which breaks at the
# same boundary — and compared with `int()`, since `"1000" < "999"` lexically.
ENTRY_RE = re.compile(r"^(\d{3,})-([a-z]+)-.+\.md$")
WATERMARK_RE = re.compile(r"^<!--\s*index-watermark:\s*(\d{3,})\s*-->")
TYPE_RE = re.compile(r"^\*\*Type\*\*:\s*([a-z]+)")
# The entry's own one-line catalog summary. Its presence is what lets the index be
# rebuilt mechanically instead of needing an LLM to re-condense the Finding.
SUMMARY_RE = re.compile(r"^\*\*Summary\*\*:\s*(.+?)\s*$")
WIKILINK_RE = re.compile(r"\[\[(\d{3,})-[a-z]+-[^\]]+\]\]")
# group(1) = the full stem, group(2) = its NNN.
CATALOG_LINE_RE = re.compile(r"^-\s+\[\[((\d{3,})-[a-z]+-[^\]]+)\]\]")
# A `## Related` line, with its relationship label: group(3), or None when the line
# carries no separator+label. Single-sourced so `knowledge_fix` cannot recognise a
# narrower set of edges than this linter reports on — a line the linter counts as an
# edge but the fixer skips is a permanent error nothing repairs and nothing refuses.
# The separator is an em dash by convention, matched permissively for the same reason.
RELATED_LINE_RE = re.compile(
    r"^-\s+\[\[((\d{3,})-[a-z]+-[^\]]+)\]\](?:\s*[—–-]\s*(.+?))?\s*$")

# index.md section header -> singular Type token
SECTION_TO_TYPE = {
    "## Decisions": "decision",
    "## Bugs": "bug",
    "## Patterns": "pattern",
    "## Constraints": "constraint",
}


def _strip_fences(lines):
    """Yield (index, line) for lines OUTSIDE code fences."""
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield i, line


def parse_entry(path: Path):
    """Parse one knowledge entry into {nnn, declared_type, related_out, backlinks}."""
    text = path.read_text()
    lines = text.splitlines()
    nonfenced = list(_strip_fences(lines))

    declared_type = None
    for _, line in nonfenced:
        m = TYPE_RE.match(line)
        if m:
            declared_type = m.group(1)
            break

    summary = None
    for _, line in nonfenced:
        m = SUMMARY_RE.match(line)
        if m:
            summary = m.group(1)
            break

    # Banner back-links: anchored markers ABOVE the first non-fenced `## ` header.
    first_section_idx = next((i for i, ln in nonfenced if SECTION_RE.match(ln)), None)
    banner_targets = set()
    for i, line in nonfenced:
        if first_section_idx is not None and i >= first_section_idx:
            break
        m = BANNER_MARKER_RE.match(line)
        if m:
            banner_targets.add(m.group(1))

    # The ## Related block = the LAST non-fenced `## Related` header, span to EOF.
    related_header_idx = None
    for i, line in nonfenced:
        if line.strip() == RELATED_HEADER:
            related_header_idx = i
    related_out = set()
    if related_header_idx is not None:
        for i, line in nonfenced:
            if i <= related_header_idx:
                continue
            m = CATALOG_LINE_RE.match(line.strip())
            if m:
                related_out.add(m.group(2))
    return {
        "nnn": ENTRY_RE.match(path.name).group(1),
        "declared_type": declared_type,
        "summary": summary,
        "related_out": related_out,
        "backlinks": related_out | banner_targets,
    }


def parse_index(path: Path):
    """Parse index.md -> {watermark, catalog: {nnn: {'section_type','stem'}}}."""
    watermark = None
    catalog = {}
    current_type = None
    if not path.exists():
        return {"watermark": None, "catalog": {}, "exists": False}
    for _, line in _strip_fences(path.read_text().splitlines()):
        m = WATERMARK_RE.match(line.strip())
        if m:
            watermark = m.group(1)
            continue
        header = line.strip()
        if header in SECTION_TO_TYPE:
            current_type = SECTION_TO_TYPE[header]
            continue
        cm = CATALOG_LINE_RE.match(line.strip())
        if cm:
            stem, nnn = cm.group(1), cm.group(2)
            catalog[nnn] = {"section_type": current_type, "stem": stem}
    return {"watermark": watermark, "catalog": catalog, "exists": True}


def lint_knowledge(knowledge_dir) -> list:
    """Return a list of Finding for the knowledge dir. Read-only."""
    kd = Path(knowledge_dir)
    findings = []

    entry_paths = sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name))

    # Group by NNN FIRST. Keying a dict directly on NNN (as this did) makes a
    # duplicate silently unrepresentable: the later file overwrites the earlier and
    # the lint reports a clean bijection over a corpus that has two entries sharing
    # an id. Downstream checks still need one entry per NNN, so they use the
    # deterministic first-by-filename member of each group.
    by_nnn = {}
    for p in entry_paths:
        by_nnn.setdefault(ENTRY_RE.match(p.name).group(1), []).append(p)
    entries = {nnn: (group[0], parse_entry(group[0])) for nnn, group in by_nnn.items()}
    entry_nnns = set(entries)

    # --- 0. duplicate NNN ----------------------------------------------------
    # Also quarantines those ids from the per-entry checks below: `entries[nnn]` is an
    # arbitrary member of the group, so a type/slug/link finding derived from it names
    # the wrong file and points the reader at the wrong problem.
    duplicate_nnns = {nnn for nnn, g in by_nnn.items() if len(g) > 1}
    for nnn, group in sorted(by_nnn.items(), key=lambda kv: int(kv[0])):
        if len(group) > 1:
            findings.append(Finding(
                "duplicate", "error",
                f"NNN {nnn} is shared by {len(group)} entries: "
                f"{', '.join(p.name for p in group)}"))

    # --- 1. index drift ------------------------------------------------------
    idx = parse_index(kd / "index.md")
    if not idx["exists"]:
        findings.append(Finding("index", "error", "index.md is missing"))
    else:
        max_nnn = max(entry_nnns, key=int) if entry_nnns else "000"
        watermark = idx["watermark"]
        if watermark is None:
            findings.append(Finding(
                "index", "error", "index.md has no `index-watermark` comment"))
        elif int(watermark) > int(max_nnn):
            findings.append(Finding(
                "index", "error",
                f"watermark {watermark} is above max entry NNN {max_nnn} — the index "
                f"claims entries that do not exist"))
        catalog = idx["catalog"]
        # An uncatalogued entry is ALWAYS pending, never drift. Promote no longer
        # writes catalog lines at all, so nothing can produce a genuinely-drifted
        # uncatalogued entry — and reconciliation repairs whatever it finds.
        #
        # This deliberately does NOT compare against the watermark. A scalar floor
        # assumes entries reconcile in NNN order, and they do not: units merge in
        # whatever order their PRs land. Unit A takes 050, unit B takes 051, B merges
        # and reconciles to watermark 051 — then A merges and its 050 is *below* the
        # floor, so a floor-based rule calls it drift, reddens A's branch, and (worse)
        # emits no pending warning, which is the very signal cleanup gates
        # reconciliation on. The entry would then never be catalogued at all.
        for nnn in sorted(entry_nnns - set(catalog), key=int):
            findings.append(Finding(
                "index", "warning",
                f"entry {nnn} has no catalog line in index.md — pending reconciliation"))
        for nnn in sorted(set(catalog) - entry_nnns, key=int):
            findings.append(Finding("index", "error",
                                    f"catalog line {nnn} has no entry file"))
        for nnn in sorted(set(catalog) & entry_nnns, key=int):
            if nnn in duplicate_nnns:
                continue  # quarantined: `entries[nnn]` is an arbitrary group member,
                          # so its type/stem would indict the wrong file
            entry = entries[nnn][1]
            sect_type = catalog[nnn]["section_type"]
            if sect_type != entry["declared_type"]:
                findings.append(Finding(
                    "index", "error",
                    f"entry {nnn} is type '{entry['declared_type']}' but catalogued "
                    f"under a '{sect_type}' section"))
            # slug cosmetic: NNN matches but stem differs -> warning, not error
            cat_stem = catalog[nnn]["stem"]
            file_stem = entries[nnn][0].name[:-3]
            if cat_stem != file_stem:
                findings.append(Finding(
                    "index", "warning",
                    f"entry {nnn} catalog slug '{cat_stem}' != filename '{file_stem}'"))

    # --- 2. broken ## Related links -----------------------------------------
    for nnn, (path, entry) in sorted(entries.items(), key=lambda kv: int(kv[0])):
        if nnn in duplicate_nnns:
            continue  # quarantined — only one group member's block was even read
        for target in sorted(entry["related_out"], key=int):
            if target not in entry_nnns:
                findings.append(Finding(
                    "broken-link", "error",
                    f"entry {nnn} '## Related' links [[{target}-...]] which has no entry"))

    # --- 3. missing reciprocals ---------------------------------------------
    # Always pending, never drift — same reasoning as the uncatalogued-entry check.
    # An add-only promote writes forward links in the NEW entry only; reconciliation
    # derives every reverse link and banner. So a missing back-link means "not
    # reconciled yet", which reconciliation itself repairs, and gating it on a scalar
    # watermark would misclassify out-of-order merges exactly as described above.
    for nnn, (path, entry) in sorted(entries.items(), key=lambda kv: int(kv[0])):
        if nnn in duplicate_nnns:
            continue  # quarantined
        for target in sorted(entry["related_out"], key=int):
            if target not in entry_nnns or target in duplicate_nnns:
                continue  # broken link (already reported), or quarantined target
            if nnn not in entries[target][1]["backlinks"]:
                findings.append(Finding(
                    "reciprocal", "warning",
                    f"entry {nnn} links {target} but {target} has no back-link to "
                    f"{nnn} — pending reconciliation"))
    return findings


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    findings = lint_knowledge(knowledge_dir)
    errors = [f for f in findings if f.severity == "error"]
    if not findings:
        print(f"knowledge-lint: {knowledge_dir} is clean.")
        return 0
    by_family = {}
    for f in findings:
        by_family.setdefault(f.family, []).append(f)
    for family in sorted(by_family):
        print(f"[{family}]")
        for f in by_family[family]:
            print(f"  {f.severity}: {f.message}")
    print(f"knowledge-lint: {len(errors)} error(s), "
          f"{len(findings) - len(errors)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
