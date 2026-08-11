#!/usr/bin/env python3
"""Deterministic, idempotent, gated fixer for the `.minerva/knowledge/` wiki (Phase B.3).

Applies the *mechanically-repairable* findings the read-only detector
(`scripts/knowledge_lint.py`) surfaces. Every edit is re-derived from the detector's
structured `parse_index` / `parse_entry` output — never from the human-readable
`Finding.message` string.

Two object types, two safety models:
  * ENTRY edits (missing reciprocal) — guarded by `body_complement` byte-identity
    (only the `## Related` block / banner span may change; knowledge 016). The span
    editors come from `scripts/knowledge_edits.py` (single-sourced, knowledge 019).
  * INDEX edits (watermark / stale catalog line / wrong Type section / MISSING catalog
    line) — `index.md` has no span model; guarded instead by a skeleton-preserving
    canonical serializer (preserve the `# Knowledge index` H1, the four Type headers
    incl. the empty `## Patterns`, and ascending-NNN order; never touch an entry file).

A missing catalog line is auto-fixed **iff** the entry states its own `**Summary**`.
That is what makes `minerva:promote` add-only: promote writes entry files carrying
their summaries and touches no aggregate, and this fixer — run on the default branch
by `minerva:cleanup` — catalogues them. The fixer still never *fabricates* a summary;
an entry without one is refused exactly as before.

Duplicate-NNN groups are QUARANTINED throughout: their catalog lines are left where
they sit and their links are not reciprocated. Every lookup here is NNN-keyed, so on
a duplicate the "winning" entry is arbitrary — acting on it would misfile the other's
line or write a back-link into the wrong file.

NOT auto-fixed (left to the human / advisory): a missing catalog line for an entry
with no `**Summary**`, anything touching a duplicate NNN, broken `## Related` links,
and the judged dimensions (orphans / contradictions / staleness; advisory per
knowledge 013).

CLI: `python3 scripts/knowledge_fix.py [--dry-run] [knowledge-dir]`
  --dry-run prints the planned edits and writes nothing. apply (default) recomputes
  once, applies the batch atomically, and verifies the corpus is clean afterward.
  Exit 0 = clean or fixed; 1 = findings remain that this fixer cannot repair.
"""
import re
import sys
from pathlib import Path

from knowledge_lint import (
    corpus_id_width,
    id_sort_key,
    ENTRY_RE,
    SECTION_TO_TYPE,
    related_edges,
    lint_knowledge,
    parse_entry,
    parse_index,
)
from knowledge_edits import add_related_link, add_supersede_banner, body_complement

# index.md catalog line: `- [[NNN-type-slug]] — summary`
_CATALOG_LINE_RE = re.compile(r"^-\s+\[\[((?:\d{4}-\d{2}-\d{2}|\d{3,})-[a-z]+-[^\]]+)\]\]")

# section header -> type and back. Order is the canonical skeleton order.
TYPE_TO_SECTION = {v: k for k, v in SECTION_TO_TYPE.items()}
# Canonical skeleton order. `## References` is APPENDED, never interleaved: every index
# in every consumer repo already renders the first four in this order, and appending is
# the only position that leaves their existing line order byte-identical.
SECTION_ORDER = ["## Decisions", "## Bugs", "## Patterns", "## Constraints",
                 "## References"]

# Reciprocal-label table (knowledge 015). `builds on` has no inverse term — its
# reciprocal is rendered `see also`.
RECIPROCAL = {
    "supersedes": "superseded by",
    "superseded by": "supersedes",
    "contradicts": "contradicts",
    "see also": "see also",
    "builds on": "see also",
}

# Terms whose reciprocal is a CLAIM, not a pointer: `supersedes` retires the other
# entry and stamps a banner on it, `contradicts` asserts the two disagree. A prose
# label that mentions one of these is refused rather than softened — guessing the
# direction of a retirement from prose is exactly the edit a human must make.
DIRECTIONAL_TERMS = ("supersede", "contradict")

# What a label that is not in RECIPROCAL reciprocates as.
#
# The closed table above assumed `## Related` labels come from a five-term vocabulary.
# They do not: the practiced convention across the corpora this runs on — including
# every recently authored entry — is a descriptive sentence explaining the edge, which
# is far more useful to a reader than `see also`. Refusing those meant ~400 back-links
# were never written, so half of every cross-reference in the wiki was missing.
#
# A prose label cannot be mechanically inverted (the sentence describes the edge from
# ONE side), so the back-link gets the neutral term. That is strictly better than the
# no-link-at-all it replaces, and a human is free to write a better sentence over it —
# `add_related_link` dedupes on the target stem, so an enriched label survives re-runs.
DEFAULT_RECIPROCAL = "see also"


def _entry_groups(kd: Path) -> dict:
    """nnn -> [path, ...] in filename order. A group with >1 member is a duplicate."""
    groups = {}
    for p in sorted(kd.glob("*.md")):
        m = ENTRY_RE.match(p.name)
        if m:
            groups.setdefault(m.group(1), []).append(p)
    return groups


def _entries(kd: Path) -> dict:
    """stem -> {path, parsed, nnn}, excluding index.md.

    Keyed on the full `NNN-type-slug` STEM, which is the identity every wikilink
    already writes (`[[NNN-type-slug]]`) and the identity `add_related_link` already
    dedupes on. NNN alone is not an identity: it is assigned per work unit, so one
    unit promoting several entries and two units racing for the next free number both
    mint collisions — 63 of them across 629 entries in the corpus this was found in.
    Keying on NNN collapsed those groups onto an arbitrary first-by-filename member,
    which is why every caller used to have to quarantine them.

    NNN survives as a SORT KEY and as the watermark, which is all it was ever fit for.
    """
    return {p.name[:-3]: {"path": p, "parsed": parse_entry(p), "nnn": nnn}
            for nnn, g in _entry_groups(kd).items() for p in g}


def _duplicate_nnns(kd: Path) -> set:
    """Ids shared by more than one entry file.

    No longer a blanket quarantine — stem keying makes catalog lines and reciprocal
    links unambiguous. It survives for the ONE edit that is genuinely NNN-shaped: a
    supersession banner's `<!-- superseded-by: NNN -->` marker, which cannot name
    which member of a shared group superseded the entry.
    """
    return {nnn for nnn, g in _entry_groups(kd).items() if len(g) > 1}


# --- INDEX fix (watermark / stale line / wrong Type section) ------------------
def plan_index(kd: Path) -> tuple:
    """Return (new_index_text, old_index_text, refusals) — a canonical,
    skeleton-preserving serialization that fixes watermark, removes stale catalog
    lines, relocates wrong-Type lines, and ADDS a catalog line for any entry that
    lacks one and carries its own `**Summary**`. Preserves each surviving catalog
    line verbatim and ascending-NNN order; never DROPS a line it can't confidently
    place, and never fabricates a summary for an entry that has none.

    Entries are identified by STEM, so several entries sharing an NNN each get their
    own catalog line, placed under their own declared type (see `_entries`).
    """
    index_path = kd / "index.md"
    old = index_path.read_text() if index_path.exists() else ""
    entries = _entries(kd)
    dups = _duplicate_nnns(kd)

    # A missing/empty index can't be mechanically rebuilt (the fixer has no
    # summaries to author) — refuse rather than write a hollow skeleton.
    if not old.strip():
        return old, old, [("index", "—", "index.md is missing/empty — run minerva:init "
                                          "or author the catalog by hand (fixer won't fabricate summaries)")]

    refusals = []
    # Collect surviving catalog lines verbatim, with the section they're under, from
    # the existing index. Stale lines (NNN with no entry file) are dropped.
    parsed = []  # (stem, verbatim_line, current_section)
    cur_sec = None
    for ln in old.splitlines():
        s = ln.strip()
        if s in SECTION_TO_TYPE:  # a `## Type` header
            cur_sec = s
            continue
        m = _CATALOG_LINE_RE.match(s)
        if m and m.group(1) in entries:
            parsed.append((m.group(1), ln.rstrip(), cur_sec))

    # Bucket each surviving line under the entry's DECLARED type (relocates wrong-Type).
    # An entry whose declared type isn't one of the four known types is LEFT where it
    # is (never dropped — that would delete its summary) and recorded as a refusal.
    buckets = {sec: [] for sec in SECTION_ORDER}
    for stem, line, cur in parsed:
        nnn = entries[stem]["nnn"]
        target = TYPE_TO_SECTION.get(entries[stem]["parsed"]["declared_type"])
        if target in buckets:
            buckets[target].append((nnn, stem, line))
        elif cur in buckets:
            buckets[cur].append((nnn, stem, line))
            refusals.append((stem, "—", f"entry {stem} has an unrecognized type; left "
                                        f"under {cur}, not relocated"))
        else:
            # Can't place safely — refuse the whole index rewrite, leave index.md as-is.
            return old, old, refusals + [(stem, "—", f"entry {stem} has an unrecognized "
                                          f"type and is in an unknown section; index "
                                          f"left unchanged")]

    # ADD a line for any entry that has none. This is the operation that makes an
    # add-only promote possible: promote writes the entry file carrying its own
    # `**Summary**` and never touches index.md, so reconciliation is what catalogues
    # it. The fixer still refuses to *fabricate* a summary — it only relocates one
    # the entry already states about itself.
    catalogued = {stem for stem, _, _ in parsed}
    for stem in sorted(set(entries) - catalogued):
        nnn = entries[stem]["nnn"]
        summary = entries[stem]["parsed"]["summary"]
        if not summary:
            refusals.append((stem, "—", f"entry {stem} has no catalog line and no "
                                        f"`**Summary**` field — author the line by hand "
                                        f"(fixer won't fabricate summaries)"))
            continue
        target = TYPE_TO_SECTION.get(entries[stem]["parsed"]["declared_type"])
        if target not in buckets:
            refusals.append((stem, "—", f"entry {stem} has an unrecognized type; no "
                                        f"catalog line added"))
            continue
        buckets[target].append((nnn, stem, f"- [[{stem}]] — {summary}"))

    # Canonical skeleton: each section is its header, then (blank + entries) only if
    # non-empty; sections separated by one blank line. An empty section (e.g.
    # `## Patterns`) is just its header — no trailing blank — so it renders as
    # `## Patterns\n\n## Constraints`, matching the init/promote skeleton.
    width = corpus_id_width(nnn for rows in buckets.values() for nnn, _, _ in rows)
    blocks = []
    for sec in SECTION_ORDER:
        block = [sec]
        # Composite key, never int(): ids are dates now, and int("2026-05-19")
        # raises. Legacy ids still sort first and numerically-correctly via the
        # shared helper, which zero-pads to the corpus's own widest token.
        rows = [line for _, _, line in
                sorted(buckets[sec], key=lambda t: (id_sort_key(t[0], width), t[1]))]
        if rows:
            block.append("")
            block.extend(rows)
        blocks.append("\n".join(block))

    # The watermark is the highest NNN this catalog ACTUALLY lists — not the corpus
    # max. Advancing it past an entry we just refused (no `**Summary**`, unrecognized
    # type, duplicate id) would assert the index reflects an entry it does not, and
    # bury the refusal: the refusal is printed once, by the run that caused it, while
    # the watermark is permanent.
    # No watermark line. A scalar floor cannot express which records are reconciled —
    # they merge out of order (knowledge 053) — and a date id is not even totally
    # ordered, since same-day ties are ordinary. Pending state is per-record: an entry
    # is uncatalogued iff it has no catalog line here.
    new = (
        "# Knowledge index\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )
    return new, old, refusals


# --- ENTRY fix (missing reciprocal) ------------------------------------------
def _forward_related(parsed_text: str) -> list:
    """An entry's `## Related` edges -> `[(target_stem, label_or_None)]`.

    A thin alias for `knowledge_lint.related_edges` — the SINGLE edge model this fixer
    and the detector share. It is kept as a name because the surrounding code and its
    tests read in terms of "forward related", but it must never grow a second
    implementation: a fixer that recognises fewer edges than the linter reports leaves
    findings nothing repairs and nothing refuses.
    """
    return related_edges(parsed_text)


def plan_reciprocals(kd: Path, date: str) -> tuple:
    """Return (edits, refusals). edits: {nnn: new_text}. refusals: [(a,b,reason)].

    For every forward edge A->B whose back-link B->A is absent (in B's `## Related`
    OR banner), compute the reciprocal edit on B. Validate the whole set BEFORE
    returning any edit; a forward label outside the closed vocab is refused (no
    partial write). A `supersedes` forward edge gives B both the banner and the
    `superseded by` line (knowledge 015/016).
    """
    entries = _entries(kd)
    dups = _duplicate_nnns(kd)
    texts = {stem: e["path"].read_text() for stem, e in entries.items()}
    edits = {}  # stem -> new text (accumulated)
    refusals = []
    for a_stem, e in entries.items():
        for b_stem, label in _forward_related(texts[a_stem]):
            if b_stem not in entries:
                continue  # broken link — not auto-fixed
            # already reciprocated? (B's Related targets A, or B's banner targets A)
            if a_stem in entries[b_stem]["parsed"]["backlink_stems"]:
                continue
            if not _editable(texts[b_stem]):
                refusals.append((a_stem, b_stem, f"entry {b_stem} has `## Related` "
                                                 f"before another section, so its "
                                                 f"cross-ref span cannot be located; "
                                                 f"back-link not written"))
                continue
            if label is None:
                refusals.append((a_stem, b_stem, "forward `## Related` line has no "
                                                 "relationship label; cannot derive the "
                                                 "reciprocal"))
                continue
            if label in RECIPROCAL:
                recip = RECIPROCAL[label]
            elif any(t in label.lower() for t in DIRECTIONAL_TERMS):
                refusals.append((a_stem, b_stem, f"forward label '{label}' reads as a "
                                                 f"supersession/contradiction claim but is "
                                                 f"not the exact term; write the reciprocal "
                                                 f"by hand"))
                continue
            else:
                recip = DEFAULT_RECIPROCAL
            cur = edits.get(b_stem, texts[b_stem])
            new = add_related_link(cur, a_stem, recip)
            if label == "supersedes":  # B is superseded by A -> banner too (015/016)
                # The banner marker now carries A's full STEM, so it can always name
                # which entry retired B. This used to be refused whenever A's id was
                # shared, because a marker holding a bare id could not say which of the
                # sharers was meant — the one place a shared id genuinely degraded the
                # output. Stem identity removes the ambiguity, so the banner is always
                # stamped and the refusal is gone.
                new = add_supersede_banner(new, entries[a_stem]["nnn"], a_stem, date)
            edits[b_stem] = new
    return edits, refusals


def _editable(text: str) -> bool:
    """Whether the machine-managed spans can be located in this entry at all.

    `body_complement` asserts the entry's shape (notably that `## Related` is the last
    section, since the cross-ref span runs to EOF). An entry that violates it cannot be
    edited safely — but that is a property of the TARGET, not of the edit, so it is a
    per-entry refusal like every other one here. Letting it reach the batch validation
    instead would abort the whole run: two malformed entries out of 632 blocked 342
    unrelated back-links in the corpus this was found in.
    """
    try:
        body_complement(text)
        return True
    except AssertionError:
        return False


def _assert_body_preserved(before: str, after: str):
    """ENTRY safety: bytes outside the `## Related`/banner spans are unchanged."""
    if body_complement(before) != body_complement(after):
        raise AssertionError("fix would modify entry body outside the machine-managed spans")


# --- orchestration -----------------------------------------------------------
def plan(kd: Path, date: str) -> dict:
    """Compute the full fix batch from one recompute. No writes."""
    new_index, old_index, index_refusals = plan_index(kd)
    recip_edits, recip_refusals = plan_reciprocals(kd, date)
    index_change = new_index if new_index != old_index else None
    return {"index": index_change, "entries": recip_edits,
            "refusals": index_refusals + recip_refusals}


def apply(kd: Path, date: str) -> dict:
    """Recompute once, validate, then write the batch.

    Validation is all-or-nothing and pre-write: every entry edit is checked against
    the `body_complement` byte-identity invariant BEFORE any file is written, so a
    bad edit aborts the whole run with nothing on disk. (Note: this guards against
    *bad edits*, not against an OS-level write failure mid-batch — there is no
    temp-file/rename rollback. On a local filesystem with a validated, deterministic
    plan that residual window is negligible; it is documented here, not engineered
    away, given the low severity.)
    """
    batch = plan(kd, date)
    entries = _entries(kd)
    # Validate every entry edit preserves the body BEFORE writing anything.
    for stem, new_text in batch["entries"].items():
        _assert_body_preserved(entries[stem]["path"].read_text(), new_text)
    # Apply.
    if batch["index"] is not None:
        (kd / "index.md").write_text(batch["index"])
    for stem, new_text in batch["entries"].items():
        entries[stem]["path"].write_text(new_text)
    return batch


def _format_plan(batch: dict) -> str:
    out = []
    if batch["index"] is not None:
        out.append("index.md: rewrite (watermark / stale-line / Type-section / order)")
    for nnn in sorted(batch["entries"]):
        out.append(f"entry {nnn}: add reciprocal `## Related` link / banner")
    for a, b, reason in batch["refusals"]:
        out.append(f"REFUSED {a}->{b}: {reason}")
    return "\n".join(out) if out else "no mechanical fixes needed"


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    dry_run = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    # `date` stamps any supersession banner the fixer writes. It's injectable via
    # --date for deterministic tests; the CLI default is the real current date so a
    # banner written interactively carries today's date.
    import datetime
    date = datetime.date.today().isoformat()
    if "--date" in argv:
        i = argv.index("--date")
        date = argv[i + 1]
        del argv[i:i + 2]  # pop the flag + its value by index (don't strip a path == date)
    if argv:
        kd = Path(argv[0])
    else:
        import subprocess
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True).stdout.strip()
        kd = Path(root) / ".minerva" / "knowledge"

    if dry_run:
        print(_format_plan(plan(kd, date)))
        return 0

    batch = apply(kd, date)
    print(_format_plan(batch))
    # Final verify: recompute and report any remaining (non-auto-fixable) findings.
    remaining = [f for f in lint_knowledge(kd) if f.severity == "error"]
    if remaining:
        print(f"knowledge-fix: {len(remaining)} finding(s) remain (not auto-fixable):")
        for f in remaining:
            print(f"  {f.family}: {f.message}")
        return 1
    print("knowledge-fix: corpus clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
