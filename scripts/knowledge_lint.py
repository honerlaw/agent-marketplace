#!/usr/bin/env python3
"""Deterministic, read-only health-check for the `.minerva/knowledge/` wiki.

Detects *mechanical* coherence defects only — no content judgment (contradiction /
staleness / orphan detection and any fixing belong to the deferred `minerva:lint`
skill, Phase B.2). The corpus is the source of truth; `index.md` is never assumed
authoritative — index problems are reported as the defect (knowledge entry 017).

Checks:
  1. index drift     — watermark vs max NNN; NNN-keyed catalog<->file bijection
                       (slug mismatch = warning, not error); Type-section grouping
                       vs each entry's declared **Type**.
  2. broken links    — every [[NNN-...]] in an entry's ## Related block resolves
                       (by NNN) to a real entry. Links read ONLY from the ## Related
                       block, fence-aware.
  3. missing recips  — if A's ## Related links B, B links back to A (presence keyed
                       on NNN, NOT label-match; back-link counts in B's ## Related
                       block OR B's supersession banner).

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

ENTRY_RE = re.compile(r"^(\d{3})-([a-z]+)-.+\.md$")
WATERMARK_RE = re.compile(r"^<!--\s*index-watermark:\s*(\d{3})\s*-->")
TYPE_RE = re.compile(r"^\*\*Type\*\*:\s*([a-z]+)")
WIKILINK_RE = re.compile(r"\[\[(\d{3})-[a-z]+-[^\]]+\]\]")
CATALOG_LINE_RE = re.compile(r"^-\s+\[\[(\d{3}-[a-z]+-[^\]]+)\]\]")

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
            m = CATALOG_LINE_RE.match(line.strip()) or re.match(
                r"^-\s+\[\[(\d{3}-[a-z]+-[^\]]+)\]\]", line.strip()
            )
            if m:
                related_out.add(m.group(1)[:3])
    return {
        "nnn": ENTRY_RE.match(path.name).group(1),
        "declared_type": declared_type,
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
            stem = cm.group(1)
            catalog[stem[:3]] = {"section_type": current_type, "stem": stem}
    return {"watermark": watermark, "catalog": catalog, "exists": True}


def lint_knowledge(knowledge_dir) -> list:
    """Return a list of Finding for the knowledge dir. Read-only."""
    kd = Path(knowledge_dir)
    findings = []

    entry_paths = sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name))
    entries = {ENTRY_RE.match(p.name).group(1): (p, parse_entry(p)) for p in entry_paths}
    entry_nnns = set(entries)

    # --- 1. index drift ------------------------------------------------------
    idx = parse_index(kd / "index.md")
    if not idx["exists"]:
        findings.append(Finding("index", "error", "index.md is missing"))
    else:
        max_nnn = max(entry_nnns) if entry_nnns else "000"
        if idx["watermark"] != max_nnn:
            findings.append(Finding(
                "index", "error",
                f"watermark {idx['watermark']} != max entry NNN {max_nnn}"))
        catalog = idx["catalog"]
        for nnn in sorted(entry_nnns - set(catalog)):
            findings.append(Finding("index", "error",
                                    f"entry {nnn} has no catalog line in index.md"))
        for nnn in sorted(set(catalog) - entry_nnns):
            findings.append(Finding("index", "error",
                                    f"catalog line {nnn} has no entry file"))
        for nnn in sorted(set(catalog) & entry_nnns):
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
    for nnn, (path, entry) in sorted(entries.items()):
        for target in sorted(entry["related_out"]):
            if target not in entry_nnns:
                findings.append(Finding(
                    "broken-link", "error",
                    f"entry {nnn} '## Related' links [[{target}-...]] which has no entry"))

    # --- 3. missing reciprocals ---------------------------------------------
    for nnn, (path, entry) in sorted(entries.items()):
        for target in sorted(entry["related_out"]):
            if target not in entry_nnns:
                continue  # already reported as broken-link
            if nnn not in entries[target][1]["backlinks"]:
                findings.append(Finding(
                    "reciprocal", "error",
                    f"entry {nnn} links {target} but {target} has no back-link to {nnn}"))
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
