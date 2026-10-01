#!/usr/bin/env python3
"""Deterministic, read-only health-check for the `.minerva/knowledge/` wiki.

Detects *mechanical* coherence defects only — no content judgment (contradiction /
staleness / orphan detection belongs to the `minerva:lint` skill's judged pass).

The wiki stores entries and nothing else. Its catalog, backlinks and supersession are
derived on read by `knowledge_catalog.py` from two metadata lines on each entry
(`**Theme**`, `**Summary**`) and from forward `## Related` links, so there is no
`index.md`, no watermark and no stored reciprocal to drift — and nothing for a
post-merge pass to reconcile (`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`).

Checks:
  0. non-conforming id — a date-shaped id that is not a real calendar date.
  1. broken links      — every [[stem]] in an entry's ## Related block resolves to a real
                         entry. Links read ONLY from the ## Related block, fence-aware.
  2. metadata          — a missing `**Theme**` or `**Summary**`. An ERROR for an entry whose
                         id is a date on/after `METADATA_REQUIRED_FROM`, a WARNING for an
                         older one. Keyed on the entry's own id, never on whether a legacy
                         `index.md` exists: a stale tool can recreate that file, and the
                         rule must not flip with it. Legacy NNN ids count as older.
  3. legacy aggregate  — `index.md` / `overview.md` still present: a warning pointing at
                         `minerva:migrate-fix`, which folds them into the entries.
  4. singleton theme   — a theme used by exactly one entry. Advisory drift signal only: a
                         freshly coined theme legitimately starts at one.

CLI: `python3 scripts/knowledge_lint.py <knowledge-dir>` — prints findings grouped
by family and exits non-zero iff any error-severity finding is present.
"""
import re
from datetime import date as _date
import sys
from collections import namedtuple
from pathlib import Path

from knowledge_spans import (
    unfenced,
    BANNER_MARKER_RE,
    RELATED_HEADER,
    SECTION_RE,
)

Finding = namedtuple("Finding", ["family", "severity", "message"])  # severity: error|warning

# The entry-id prefix has TWO accepted forms, and both must stay matchable forever.
#
#   date   `YYYY-MM-DD` — the current convention. Not allocated: it is read off the
#          clock, so concurrent branches never negotiate for it.
#   legacy `\d{3,}` — the retired sequential NNN. Still accepted because a consumer
#          corpus migrates on its own schedule, and a prefix form that stops matching
#          `ENTRY_RE` goes invisible to EVERY wiki tool at once (knowledge 026) — a
#          false clean, which is the exact failure `minerva:migrate` exists to catch.
#          Legacy is `\d{3,}` not `\d{3}`: the old allocator widened past 999.
#
# Shape alone is not conformance: `2026-13-45` matches the date arm. `is_conforming_id`
# validates the date arm against the calendar; callers deciding "is this a real entry"
# must use it rather than trusting the regex.
ID_RE_SRC = r"(?:\d{4}-\d{2}-\d{2}|\d{3,})"
ENTRY_RE = re.compile(rf"^({ID_RE_SRC})-([a-z]+)-.+\.md$")
DATE_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_date_id(token: str) -> bool:
    """True iff `token` is a calendar-valid `YYYY-MM-DD`."""
    if not DATE_ID_RE.match(token):
        return False
    try:
        _date.fromisoformat(token)
    except ValueError:
        return False
    return True


def is_conforming_id(token: str) -> bool:
    """True iff `token` is a real entry id — a valid date, or a legacy NNN."""
    return is_date_id(token) or bool(re.fullmatch(r"\d{3,}", token))


def id_sort_key(token: str, width: int = 12):
    """Order ids deterministically across BOTH forms.

    Legacy first (chronologically right — every NNN predates the switch), then dates.
    Legacy is zero-padded rather than `int()`-cast so the two forms share one key type;
    `width` must exceed the longest legacy token in the corpus, because `"1000" < "999"`
    lexically and a too-narrow pad reintroduces exactly the bug `int()` was guarding.
    """
    return (1, token) if is_date_id(token) else (0, token.zfill(width))


def corpus_id_width(tokens) -> int:
    """The pad width for `id_sort_key` over a specific corpus: never hardcode 3."""
    legacy = [t for t in tokens if not is_date_id(t)]
    return max((len(t) for t in legacy), default=3)
# The entry's own type field. Three spellings, because all three appear in real
# corpora and all three are the author stating the field — only the punctuation
# drifted: `**Type**: x` (canonical), `**Type:** x` (colon inside the bold markers),
# and a plain `Type: x`. Matching only the canonical one made 29 entries read as
# having no type at all (of 42 unresolvable in that corpus; the rest are covered by
# the two fallbacks below), which the catalog's `--by-type` view could not place.
TYPE_RE = re.compile(r"^(?:\*\*Type\*\*:|\*\*Type:\*\*|Type:)\s*([a-z]+)")
# The template's machine-readable half, for an entry that carries frontmatter but no
# body field. Matched in TWO steps on purpose: the leading `---` block is isolated
# first, then `type:` is looked for INSIDE it. A single pattern spanning both would
# need a DOTALL wildcard between them, which happily reaches past the closing `---`
# and picks up a `type:` line from the body or a fenced example.
FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n(.*?)\n---\s*$", re.DOTALL | re.MULTILINE)
FRONTMATTER_TYPE_RE = re.compile(r"^\s*type:\s*([a-z]+)\s*$", re.MULTILINE)
# The entry's own one-line catalog summary. Its presence is what lets the catalog be
# derived mechanically instead of needing an LLM to re-condense the Finding.
SUMMARY_RE = re.compile(r"^\*\*Summary\*\*:\s*(.+?)\s*$")
# The entry's theme: the single-valued, lowercase kebab-case grouping the derived
# catalog (`knowledge_catalog.py`) sorts entries under. It replaced `overview.md`'s
# hand-written theme sections, so the grouping lives on the entry and no shared file
# has to change when one is added.
THEME_RE = re.compile(r"^\*\*Theme\*\*:\s*(.+?)\s*$")
# The entry's H1 — the catalog's fallback line for an entry with no `**Summary**`.
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
WIKILINK_RE = re.compile(rf"\[\[({ID_RE_SRC})-[a-z]+-[^\]]+\]\]")
# A legacy `index.md` catalog line (read only by `knowledge_backfill`).
# group(1) = the full stem, group(2) = its NNN.
CATALOG_LINE_RE = re.compile(rf"^-\s+\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]")
# The VISIBLE half of a supersession banner. The `<!-- superseded-by: NNN -->` marker
# above it identifies the superseding entry by NNN, which is ambiguous when an NNN is
# shared; this line carries the full stem, so a stem-keyed reader can resolve it.
BANNER_TARGET_STEM_RE = re.compile(
    rf"^>\s+\*\*Superseded by \[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]\*\*")
# EVERY wikilink in a line, not just a line-initial one. `CATALOG_LINE_RE` anchors at
# `- [[…]]`, so it sees only the first target of a line like
# `- [[a]] / [[b]] — both unchanged` and nothing on a wrapped continuation line, which
# would drop real edges from the derived backlinks.
WIKILINK_STEM_RE = re.compile(rf"\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]")
# A stem's own leading id, for callers holding a stem and needing the id half of it.
ID_PREFIX_RE = re.compile(rf"^({ID_RE_SRC})-")
# A `## Related` line, with its relationship label: group(3), or None when the line
# carries no separator+label. The separator is an em dash by convention, matched
# permissively because real corpora drifted to `–` and `-`.
RELATED_LINE_RE = re.compile(
    rf"^-\s+\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\](?:\s*[—–-]\s*(.+?))?\s*$")

# `_strip_fences` is the shared `knowledge_spans.unfenced` primitive under its
# historical name — kept because the backfill imports it from here and the
# fence-awareness gate recognises the name. One implementation, two names, no drift.
_strip_fences = unfenced


def related_edges(text: str) -> list:
    """Every `## Related` edge in `text`, as `[(target_stem, label_or_None)]`.

    THE edge model. The linter (`parse_entry`) and the derived catalog
    (`knowledge_catalog`'s backlinks and supersession) both read edges through this, so
    a link the linter accepts is exactly a link the catalog reverses.

    EVERY wikilink in the block is an edge. A label is carried only when the line is
    unambiguously one target and one label; otherwise it is None. A multi-target line
    has no single label, and inventing one from the line's tail would misstate the
    relationship — the catalog lists such an edge as a backlink with no label.

    Block selection is the LAST non-fenced `## Related` header, span to EOF. Fenced
    blocks are excluded: a `[[...]]` inside a fence is documentation showing what a link
    looks like, not an edge (knowledge 2026-06-03).
    """
    nonfenced = list(_strip_fences(text.splitlines()))
    start = None
    for i, line in nonfenced:
        if line.strip() == RELATED_HEADER:
            start = i  # keep the last one
    if start is None:
        return []
    edges = {}
    for i, line in nonfenced:
        if i <= start:
            continue
        targets = [m.group(1) for m in WIKILINK_STEM_RE.finditer(line)]
        if not targets:
            continue
        label = None
        if len(targets) == 1:
            m = RELATED_LINE_RE.match(line.strip())
            if m and m.group(3):
                label = m.group(3).strip()
        for target in targets:
            # First occurrence wins, except that a labelled edge upgrades an unlabelled
            # one — otherwise a stray earlier mention would refuse a reciprocal the
            # entry does state properly further down.
            if target not in edges or (edges[target] is None and label is not None):
                edges[target] = label
    return list(edges.items())


def parse_entry(path: Path):
    """Parse one knowledge entry into its id, type, metadata, title and `## Related` edges."""
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
    theme = None
    for _, line in nonfenced:
        m = THEME_RE.match(line)
        if m:
            theme = m.group(1)
            break
    title = None
    for _, line in nonfenced:
        m = TITLE_RE.match(line)
        if m:
            title = m.group(1)
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

    # Forward edges come from the SHARED model (`related_edges`).
    edges = related_edges(text)
    edge_stems = {target for target, _ in edges}
    related_out = {ID_PREFIX_RE.match(s).group(1) for s in edge_stems}
    return {
        "nnn": ENTRY_RE.match(path.name).group(1),
        "stem": path.name[:-3],
        "declared_type": declared_type,
        "summary": summary,
        "theme": theme,
        "title": title,
        "edges": edges,
        # Every successor a stored banner names (marker and visible line), for the
        # catalog's supersession union. Legacy only: entries are write-once now, so no
        # new banner is ever written — supersession is derived from `supersedes` edges.
        "banner_stems": sorted(banner_targets | banner_target_stems),
        "related_out": related_out,
        # STEM-keyed twin of `related_out` above. An NNN shared by several entries
        # cannot say WHICH entry an edge points at; a stem always can.
        "related_out_stems": edge_stems,
    }


# Entries dated on or after this must carry `**Theme**` and `**Summary**`; older ones are
# only warned about, so a consumer corpus that has not yet run `minerva:migrate-fix` stays
# green. The date minerva 3.0 started deriving the catalog from those two lines.
METADATA_REQUIRED_FROM = "2026-10-01"

# Files a pre-3.0 corpus kept beside its entries. Their content now lives on the entries.
LEGACY_AGGREGATES = ("index.md", "overview.md")


def lint_knowledge(knowledge_dir) -> list:
    """Return a list of Finding for the knowledge dir. Read-only."""
    kd = Path(knowledge_dir)
    findings = []

    entry_paths = sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name))

    # Keyed on the full STEM — the identity every wikilink already writes, and the one
    # the filesystem itself enforces. Two entries sharing a date are ordinary and
    # independent; a duplicate stem cannot exist, because it would be the same path.
    entries = {p.name[:-3]: (p, parse_entry(p)) for p in entry_paths}
    entry_stems = set(entries)
    width = corpus_id_width(e[1]["nnn"] for e in entries.values())

    def by_id(stem):
        return id_sort_key(entries[stem][1]["nnn"], width)

    ordered = sorted(entry_stems, key=by_id)

    # --- 0. non-conforming id -------------------------------------------------
    # `ENTRY_RE` is shape-only: `2026-13-45-pattern-x.md` matches it. Reporting the
    # impossible date here is what keeps migrate's shape check honest rather than
    # letting a typo pass as a valid entry forever.
    for stem in ordered:
        entry_id = entries[stem][1]["nnn"]
        if not is_conforming_id(entry_id):
            findings.append(Finding(
                "id", "error",
                f"entry '{stem}' has a date-shaped but invalid id '{entry_id}'"))

    # --- 1. broken ## Related links -----------------------------------------
    for stem in ordered:
        for target in sorted(entries[stem][1]["related_out_stems"]):
            if target not in entry_stems:
                findings.append(Finding(
                    "broken-link", "error",
                    f"entry {stem} '## Related' links [[{target}]] which has no entry"))

    # --- 2. metadata ----------------------------------------------------------
    for stem in ordered:
        entry = entries[stem][1]
        entry_id = entry["nnn"]
        required = is_date_id(entry_id) and entry_id >= METADATA_REQUIRED_FROM
        for field in ("theme", "summary"):
            if entry[field]:
                continue
            findings.append(Finding(
                "metadata", "error" if required else "warning",
                f"entry {stem} has no **{field.title()}** line — the derived catalog "
                f"reads it" + ("" if required else
                               " (run minerva:migrate-fix to backfill a legacy corpus)")))

    # --- 3. legacy aggregates -------------------------------------------------
    for name in LEGACY_AGGREGATES:
        if (kd / name).exists():
            findings.append(Finding(
                "legacy", "warning",
                f"{name} is a pre-3.0 aggregate nothing maintains any more — run "
                f"minerva:migrate-fix to fold it into the entries and delete it"))

    # --- 4. singleton themes --------------------------------------------------
    themes = {}
    for stem in ordered:
        theme = entries[stem][1]["theme"]
        if theme:
            themes.setdefault(theme, []).append(stem)
    for theme, stems in sorted(themes.items()):
        if len(stems) == 1:
            findings.append(Finding(
                "theme", "warning",
                f"theme '{theme}' is used only by {stems[0]} — fine for a new theme, "
                f"otherwise reuse an existing one (knowledge_catalog.py --themes)"))
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
