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

Be precise about what that costs. No *promote-driven* path can produce a genuinely
drifted uncatalogued entry, because promote never writes catalog lines at all. But a
hand-edit or a bad merge that drops an already-reconciled catalog line is no longer
reported loudly — it is silently self-healed by the next reconciliation instead. That
trade is deliberate: `index.md` is machine-generated content now, and the alternative
(a scalar floor) misclassified the out-of-order merges this design exists to support,
which is a far more frequent and more damaging failure. A test in
`tests/test_knowledge_lint.py` pins the trade so it is not "fixed" back unwittingly.

That alternative — gating on the `index-watermark` — assumes entries reconcile in NNN
order, and they do not: units merge whenever their PRs land.
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
# The entry's own type field. Three spellings, because all three appear in real
# corpora and all three are the author stating the field — only the punctuation
# drifted: `**Type**: x` (canonical), `**Type:** x` (colon inside the bold markers),
# and a plain `Type: x`. Matching only the canonical one made 29 entries read as
# having no type at all (of 42 unresolvable in that corpus; the rest are covered by
# the two fallbacks below), which `plan_index` cannot place and the linter reports as
# a mismatch the entry does not have.
TYPE_RE = re.compile(r"^(?:\*\*Type\*\*:|\*\*Type:\*\*|Type:)\s*([a-z]+)")
# The template's machine-readable half, for an entry that carries frontmatter but no
# body field. Matched in TWO steps on purpose: the leading `---` block is isolated
# first, then `type:` is looked for INSIDE it. A single pattern spanning both would
# need a DOTALL wildcard between them, which happily reaches past the closing `---`
# and picks up a `type:` line from the body or a fenced example.
FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n(.*?)\n---\s*$", re.DOTALL | re.MULTILINE)
FRONTMATTER_TYPE_RE = re.compile(r"^\s*type:\s*([a-z]+)\s*$", re.MULTILINE)
# The entry's own one-line catalog summary. Its presence is what lets the index be
# rebuilt mechanically instead of needing an LLM to re-condense the Finding.
SUMMARY_RE = re.compile(r"^\*\*Summary\*\*:\s*(.+?)\s*$")
WIKILINK_RE = re.compile(r"\[\[(\d{3,})-[a-z]+-[^\]]+\]\]")
# group(1) = the full stem, group(2) = its NNN.
CATALOG_LINE_RE = re.compile(r"^-\s+\[\[((\d{3,})-[a-z]+-[^\]]+)\]\]")
# The VISIBLE half of a supersession banner. The `<!-- superseded-by: NNN -->` marker
# above it identifies the superseding entry by NNN, which is ambiguous when an NNN is
# shared; this line carries the full stem, so a stem-keyed reader can resolve it.
BANNER_TARGET_STEM_RE = re.compile(
    r"^>\s+\*\*Superseded by \[\[((\d{3,})-[a-z]+-[^\]]+)\]\]\*\*")
# EVERY wikilink in a line, not just a line-initial one. `CATALOG_LINE_RE` anchors at
# `- [[…]]`, so it sees only the first target of a line like
# `- [[a]] / [[b]] — both unchanged` and nothing on a wrapped continuation line. The
# EDITOR (`add_related_link._related_has_target`) scans the whole span, so anchoring
# the detector made the two disagree: the detector reported a back-link missing, the
# editor found it present and no-opped, and the entry was re-planned as "changed"
# forever. Used for back-link DETECTION only, where matching the editor is the point.
WIKILINK_STEM_RE = re.compile(r"\[\[((\d{3,})-[a-z]+-[^\]]+)\]\]")
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

    # Resolve the type from wherever the entry declares it, most-deliberate first.
    declared_type = None
    for _, line in nonfenced:
        m = TYPE_RE.match(line)
        if m:
            declared_type = m.group(1)
            break
    if declared_type is None:
        block = FRONTMATTER_BLOCK_RE.match(text)
        if block:
            m = FRONTMATTER_TYPE_RE.search(block.group(1))
            if m:
                declared_type = m.group(1)
    if declared_type is None:
        # Last resort, and a trustworthy one: the filename's own type segment. It is
        # the only source that ALWAYS exists (ENTRY_RE has already matched to get
        # here), and across 642 entries in two corpora it never once disagreed with a
        # declared type. Ordered last so an author's explicit field always wins — this
        # can only ever fill a gap, never override a statement.
        declared_type = ENTRY_RE.match(path.name).group(2)

    summary = None
    for _, line in nonfenced:
        m = SUMMARY_RE.match(line)
        if m:
            summary = m.group(1)
            break

    # Banner back-links: anchored markers ABOVE the first non-fenced `## ` header.
    first_section_idx = next((i for i, ln in nonfenced if SECTION_RE.match(ln)), None)
    banner_targets = set()
    banner_target_stems = set()
    for i, line in nonfenced:
        if first_section_idx is not None and i >= first_section_idx:
            break
        m = BANNER_MARKER_RE.match(line)
        if m:
            banner_targets.add(m.group(1))
        m = BANNER_TARGET_STEM_RE.match(line)
        if m:
            banner_target_stems.add(m.group(1))

    # The ## Related block = the LAST non-fenced `## Related` header, span to EOF.
    related_header_idx = None
    for i, line in nonfenced:
        if line.strip() == RELATED_HEADER:
            related_header_idx = i
    related_out = set()
    related_out_stems = set()
    related_mention_stems = set()
    if related_header_idx is not None:
        for i, line in nonfenced:
            if i <= related_header_idx:
                continue
            m = CATALOG_LINE_RE.match(line.strip())
            if m:
                related_out.add(m.group(2))
                related_out_stems.add(m.group(1))
            related_mention_stems.update(m.group(1) for m in WIKILINK_STEM_RE.finditer(line))
    return {
        "nnn": ENTRY_RE.match(path.name).group(1),
        "stem": path.name[:-3],
        "declared_type": declared_type,
        "summary": summary,
        "related_out": related_out,
        "backlinks": related_out | banner_targets,
        # STEM-keyed twins of the two sets above. An NNN shared by several entries
        # cannot say WHICH entry an edge points at; a stem always can. Kept alongside
        # rather than replacing them so this linter's own NNN-shaped checks are
        # untouched by the fixer's move to stems.
        "related_out_stems": related_out_stems,
        "backlink_stems": related_mention_stems | banner_target_stems,
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
        # An uncatalogued entry is ALWAYS pending. No promote-driven path can drift
        # (promote never writes catalog lines), and reconciliation repairs whatever it
        # finds — including a line lost to a hand-edit or a bad merge, which is
        # therefore self-healed silently rather than reported. See the module
        # docstring: that cost is deliberate and pinned by a test.
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
