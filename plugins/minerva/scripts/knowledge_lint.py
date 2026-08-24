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
WIKILINK_RE = re.compile(rf"\[\[({ID_RE_SRC})-[a-z]+-[^\]]+\]\]")
# group(1) = the full stem, group(2) = its NNN.
CATALOG_LINE_RE = re.compile(rf"^-\s+\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]")
# The VISIBLE half of a supersession banner. The `<!-- superseded-by: NNN -->` marker
# above it identifies the superseding entry by NNN, which is ambiguous when an NNN is
# shared; this line carries the full stem, so a stem-keyed reader can resolve it.
BANNER_TARGET_STEM_RE = re.compile(
    rf"^>\s+\*\*Superseded by \[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]\*\*")
# EVERY wikilink in a line, not just a line-initial one. `CATALOG_LINE_RE` anchors at
# `- [[…]]`, so it sees only the first target of a line like
# `- [[a]] / [[b]] — both unchanged` and nothing on a wrapped continuation line. The
# EDITOR (`add_related_link._related_has_target`) scans the whole span, so anchoring
# the detector made the two disagree: the detector reported a back-link missing, the
# editor found it present and no-opped, and the entry was re-planned as "changed"
# forever. Used for back-link DETECTION only, where matching the editor is the point.
WIKILINK_STEM_RE = re.compile(rf"\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\]")
# A stem's own leading id, for callers holding a stem and needing the id half of it.
ID_PREFIX_RE = re.compile(rf"^({ID_RE_SRC})-")
# A `## Related` line, with its relationship label: group(3), or None when the line
# carries no separator+label. Single-sourced so `knowledge_fix` cannot recognise a
# narrower set of edges than this linter reports on — a line the linter counts as an
# edge but the fixer skips is a permanent error nothing repairs and nothing refuses.
# The separator is an em dash by convention, matched permissively for the same reason.
RELATED_LINE_RE = re.compile(
    rf"^-\s+\[\[(({ID_RE_SRC})-[a-z]+-[^\]]+)\]\](?:\s*[—–-]\s*(.+?))?\s*$")

# index.md section header -> singular Type token
SECTION_TO_TYPE = {
    "## Decisions": "decision",
    "## Bugs": "bug",
    "## Patterns": "pattern",
    "## Constraints": "constraint",
    # `reference` is a fifth type, added once authors had written four of them without
    # one existing (unit 052). It is the standing-fact register — what a subsystem IS
    # and how it is operated — where the other four are things LEARNED. Distinct from a
    # `.minerva/reference/` doc in the way every entry is: atomic, numbered,
    # cross-linked and catalogued, rather than a maintained operational page.
    "## References": "reference",
}


# `_strip_fences` is the shared `knowledge_spans.unfenced` primitive under its
# historical name — kept because `knowledge_fix` imports it from here and the
# fence-awareness gate recognises the name. One implementation, two names, no drift.
_strip_fences = unfenced


def related_edges(text: str) -> list:
    """Every `## Related` edge in `text`, as `[(target_stem, label_or_None)]`.

    THE edge model. Both the detector (`parse_entry`) and the editor
    (`knowledge_fix._forward_related`) call this, so neither can recognise a set of
    edges the other does not. That is a correctness property, not tidiness: an edge the
    linter counts but the fixer skips is a permanent finding nothing repairs and nothing
    refuses, so a convergence loop runs forever while the fixer reports the corpus
    clean. It was previously asserted by a comment on `RELATED_LINE_RE` and violated by
    the code — `parse_entry` derived its own edges from the start-anchored
    `CATALOG_LINE_RE`, which sees `- [[a]] / [[b]] — label` and `- [[a]] /` where the
    end-anchored `RELATED_LINE_RE` sees nothing at all.

    EVERY wikilink in the block is an edge, matching the editor's own whole-line scan
    (`add_related_link._related_has_target`) and the back-link detector. A label is
    carried only when the line is unambiguously one target and one label; otherwise it
    is None, which `knowledge_fix.plan_reciprocals` already handles by REFUSING the
    reciprocal. Refusing is the point: a multi-target line has no single label to
    reciprocate, and the alternative — inventing one from the line's tail — would write
    a wrong edge into a neighbouring entry.

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

    # Forward edges come from the SHARED model, so this detector and `knowledge_fix`'s
    # editor read the same block the same way. `related_mention_stems` is the same set
    # of targets — the whole-line scan that used to be kept separately for back-link
    # detection is now what `related_edges` itself does.
    edges = related_edges(text)
    edge_stems = {target for target, _ in edges}
    related_out = {ID_PREFIX_RE.match(s).group(1) for s in edge_stems}
    # Targets reached ONLY by a line `related_edges` could not attach a single
    # label to - a multi-target bullet, or one whose prose is not `- [[x]] - label`.
    # `knowledge_fix.plan_reciprocals` REFUSES these by design (a multi-target line
    # has no single label to reciprocate, and inventing one would write a wrong edge
    # into a neighbouring entry), so a finding on them is one no tool will ever clear.
    # Labelled-elsewhere wins: an entry may reach the same target from two lines.
    labelled = {target for target, label in edges if label is not None}
    unlabelled_out_stems = {target for target, label in edges if label is None} - labelled
    return {
        "nnn": ENTRY_RE.match(path.name).group(1),
        "stem": path.name[:-3],
        "declared_type": declared_type,
        "summary": summary,
        "related_out": related_out,
        "backlinks": related_out | banner_targets,
        "unlabelled_out_stems": unlabelled_out_stems,
        # STEM-keyed twin of `related_out` above. An NNN shared by several entries
        # cannot say WHICH entry an edge points at; a stem always can. Kept alongside
        # rather than replacing it so this linter's own NNN-shaped checks are untouched
        # by the fixer's move to stems.
        #
        # Outbound and inbound now derive from ONE set. They used to differ — outbound
        # read only a line's first wikilink while inbound scanned the whole line — and
        # that asymmetry is precisely the defect `related_edges` closes: a target could
        # be counted as linked-to without being counted as linked-from.
        "related_out_stems": edge_stems,
        "backlink_stems": edge_stems | banner_target_stems,
    }


def parse_index(path: Path):
    """Parse index.md -> {catalog: {stem: {'section_type','id'}}, exists}.

    Keyed on the full STEM, not the id. Two entries can legitimately share a date —
    dates are read off the clock, never allocated — so an id-keyed catalog would make
    one of them unrepresentable, the exact defect knowledge 054 documents.

    The `index-watermark` comment is no longer read. Reconciliation state is per-record
    (an entry is pending iff it has no catalog line) because records merge out of order
    and a scalar floor misclassifies them; knowledge 053 established that for the index,
    and a date id — which is not even totally ordered, since ties are ordinary — cannot
    support a floor at all.
    """
    catalog = {}
    current_type = None
    if not path.exists():
        return {"catalog": {}, "exists": False}
    for _, line in _strip_fences(path.read_text().splitlines()):
        header = line.strip()
        if header in SECTION_TO_TYPE:
            current_type = SECTION_TO_TYPE[header]
            continue
        cm = CATALOG_LINE_RE.match(line.strip())
        if cm:
            catalog[cm.group(1)] = {"section_type": current_type, "id": cm.group(2)}
    return {"catalog": catalog, "exists": True}


def lint_knowledge(knowledge_dir) -> list:
    """Return a list of Finding for the knowledge dir. Read-only."""
    kd = Path(knowledge_dir)
    findings = []

    entry_paths = sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name))

    # Keyed on the full STEM — the identity every wikilink already writes, and the one
    # the filesystem itself enforces. The previous id-keyed dict could not represent two
    # entries sharing an id (knowledge 054), which is why a duplicate check and a blanket
    # quarantine had to exist beside it. Under date ids that pairing would be actively
    # WRONG: same-day entries are ordinary and independent, so grouping them would report
    # each as a duplicate AND exclude it from every per-entry check below. Stem identity
    # removes the failure mode instead of policing it — a duplicate stem cannot exist,
    # because it would be the same path, which git refuses to merge.
    entries = {p.name[:-3]: (p, parse_entry(p)) for p in entry_paths}
    entry_stems = set(entries)
    width = corpus_id_width(e[1]["nnn"] for e in entries.values())

    def by_id(stem):
        return id_sort_key(entries[stem][1]["nnn"], width)

    # --- 0. non-conforming id -------------------------------------------------
    # `ENTRY_RE` is shape-only: `2026-13-45-pattern-x.md` matches it. Reporting the
    # impossible date here is what keeps migrate's shape check honest rather than
    # letting a typo pass as a valid entry forever.
    for stem in sorted(entry_stems, key=by_id):
        entry_id = entries[stem][1]["nnn"]
        if not is_conforming_id(entry_id):
            findings.append(Finding(
                "id", "error",
                f"entry '{stem}' has a date-shaped but invalid id '{entry_id}'"))

    # --- 1. index drift ------------------------------------------------------
    idx = parse_index(kd / "index.md")
    if not idx["exists"]:
        findings.append(Finding("index", "error", "index.md is missing"))
    else:
        catalog = idx["catalog"]
        # An uncatalogued entry is ALWAYS pending, never drift. No promote-driven path
        # can drift (promote never writes catalog lines), and reconciliation repairs
        # whatever it finds — including a line lost to a hand-edit or a bad merge, which
        # is therefore self-healed silently rather than reported.
        for stem in sorted(entry_stems - set(catalog), key=by_id):
            findings.append(Finding(
                "index", "warning",
                f"entry {stem} has no catalog line in index.md — pending reconciliation"))
        for stem in sorted(set(catalog) - entry_stems):
            findings.append(Finding("index", "error",
                                    f"catalog line {stem} has no entry file"))
        for stem in sorted(set(catalog) & entry_stems, key=by_id):
            entry = entries[stem][1]
            sect_type = catalog[stem]["section_type"]
            if sect_type != entry["declared_type"]:
                findings.append(Finding(
                    "index", "error",
                    f"entry {stem} is type '{entry['declared_type']}' but catalogued "
                    f"under a '{sect_type}' section"))

    # --- 2. broken ## Related links -----------------------------------------
    for stem in sorted(entry_stems, key=by_id):
        for target in sorted(entries[stem][1]["related_out_stems"]):
            if target not in entry_stems:
                findings.append(Finding(
                    "broken-link", "error",
                    f"entry {stem} '## Related' links [[{target}]] which has no entry"))

    # --- 3. missing reciprocals ---------------------------------------------
    # Always pending, never drift — same reasoning as the uncatalogued-entry check.
    for stem in sorted(entry_stems, key=by_id):
        for target in sorted(entries[stem][1]["related_out_stems"]):
            if target not in entry_stems:
                continue  # broken link, already reported above
            if stem in entries[target][1]["backlink_stems"]:
                continue
            if target in entries[stem][1]["unlabelled_out_stems"]:
                # Deliberately NOT worded "pending reconciliation". That phrase is
                # the signal `minerva:cleanup` reads to decide pending work exists,
                # so using it here would describe a reconcile that can never settle:
                # the fixer refuses this edge on every run, by design, forever.
                # Still reported rather than suppressed - the relationship really is
                # unrecorded on the target side, and silence would be its own lie.
                findings.append(Finding(
                    "reciprocal-manual", "warning",
                    f"entry {stem} links {target} from a line with no single "
                    f"relationship label (multi-target or unlabelled), so no "
                    f"reciprocal can be derived — write the back-link on {target} "
                    f"by hand, or split the line into one target and one label"))
                continue
            findings.append(Finding(
                "reciprocal", "warning",
                f"entry {stem} links {target} but {target} has no back-link to "
                f"{stem} — pending reconciliation"))
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
