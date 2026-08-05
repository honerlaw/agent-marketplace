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
    ENTRY_RE,
    SECTION_TO_TYPE,
    _strip_fences,
    lint_knowledge,
    parse_entry,
    parse_index,
)
from knowledge_edits import add_related_link, add_supersede_banner, body_complement

# index.md catalog line: `- [[NNN-type-slug]] — summary`
_CATALOG_LINE_RE = re.compile(r"^-\s+\[\[(\d{3})-[a-z]+-[^\]]+\]\]")
# A forward `## Related` line, capturing target NNN + relationship label.
_RELATED_LINE_RE = re.compile(r"^-\s+\[\[(\d{3})-[a-z]+-[^\]]+\]\]\s+—\s+(.+?)\s*$")

# section header -> type and back. Order is the canonical skeleton order.
TYPE_TO_SECTION = {v: k for k, v in SECTION_TO_TYPE.items()}
SECTION_ORDER = ["## Decisions", "## Bugs", "## Patterns", "## Constraints"]

# Reciprocal-label table (knowledge 015). `builds on` has no inverse term — its
# reciprocal is rendered `see also`. Anything outside this table → refuse.
RECIPROCAL = {
    "supersedes": "superseded by",
    "superseded by": "supersedes",
    "contradicts": "contradicts",
    "see also": "see also",
    "builds on": "see also",
}


def _entry_groups(kd: Path) -> dict:
    """nnn -> [path, ...] in filename order. A group with >1 member is a duplicate."""
    groups = {}
    for p in sorted(kd.glob("*.md")):
        m = ENTRY_RE.match(p.name)
        if m:
            groups.setdefault(m.group(1), []).append(p)
    return groups


def _entries(kd: Path) -> dict:
    """nnn -> {path, parsed}, excluding index.md.

    On a duplicate NNN the deterministic first-by-filename member represents the
    group. That winner is arbitrary with respect to *intent*, so every caller must
    consult `_duplicate_nnns()` and quarantine those ids rather than acting on it —
    see the quarantine comments in `plan_index` / `plan_reciprocals`.
    """
    return {nnn: {"path": g[0], "parsed": parse_entry(g[0])}
            for nnn, g in _entry_groups(kd).items()}


def _duplicate_nnns(kd: Path) -> set:
    """Ids shared by more than one entry file. Quarantined from every edit."""
    return {nnn for nnn, g in _entry_groups(kd).items() if len(g) > 1}


# --- INDEX fix (watermark / stale line / wrong Type section) ------------------
def plan_index(kd: Path) -> tuple:
    """Return (new_index_text, old_index_text, refusals) — a canonical,
    skeleton-preserving serialization that fixes watermark, removes stale catalog
    lines, relocates wrong-Type lines, and ADDS a catalog line for any entry that
    lacks one and carries its own `**Summary**`. Preserves each surviving catalog
    line verbatim and ascending-NNN order; never DROPS a line it can't confidently
    place, and never fabricates a summary for an entry that has none.

    Duplicate-NNN groups are quarantined: their lines are left exactly where they
    are and no line is added for them (see `_duplicate_nnns`).
    """
    index_path = kd / "index.md"
    old = index_path.read_text() if index_path.exists() else ""
    entries = _entries(kd)
    dups = _duplicate_nnns(kd)
    max_nnn = max(entries) if entries else "000"

    # A missing/empty index can't be mechanically rebuilt (the fixer has no
    # summaries to author) — refuse rather than write a hollow skeleton.
    if not old.strip():
        return old, old, [("index", "—", "index.md is missing/empty — run minerva:init "
                                          "or author the catalog by hand (fixer won't fabricate summaries)")]

    refusals = []
    # Collect surviving catalog lines verbatim, with the section they're under, from
    # the existing index. Stale lines (NNN with no entry file) are dropped.
    parsed = []  # (nnn, verbatim_line, current_section)
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
    for nnn, line, cur in parsed:
        # QUARANTINE: with two entries sharing this id, `entries[nnn]` resolved to an
        # arbitrary one of them, so its declared type cannot be trusted to place this
        # line — relocating on it would misfile the other entry's line. Leave it where
        # it sits, exactly as the unrecognized-type case does below.
        if nnn in dups:
            if cur in buckets:
                buckets[cur].append((nnn, line))
                refusals.append((nnn, "—", f"NNN {nnn} is shared by multiple entries; "
                                           f"catalog line left under {cur}, not relocated"))
                continue
            return old, old, [(nnn, "—", f"NNN {nnn} is shared by multiple entries and "
                                         f"its catalog line is in an unknown section; "
                                         f"index left unchanged")]
        target = TYPE_TO_SECTION.get(entries[nnn]["parsed"]["declared_type"])
        if target in buckets:
            buckets[target].append((nnn, line))
        elif cur in buckets:
            buckets[cur].append((nnn, line))
            refusals.append((nnn, "—", f"entry {nnn} has an unrecognized type; left under "
                                       f"{cur}, not relocated"))
        else:
            # Can't place safely — refuse the whole index rewrite, leave index.md as-is.
            return old, old, [(nnn, "—", f"entry {nnn} has an unrecognized type and is in "
                                         f"an unknown section; index left unchanged")]

    # ADD a line for any entry that has none. This is the operation that makes an
    # add-only promote possible: promote writes the entry file carrying its own
    # `**Summary**` and never touches index.md, so reconciliation is what catalogues
    # it. The fixer still refuses to *fabricate* a summary — it only relocates one
    # the entry already states about itself.
    catalogued = {nnn for nnn, _, _ in parsed}
    for nnn in sorted(set(entries) - catalogued):
        if nnn in dups:
            refusals.append((nnn, "—", f"NNN {nnn} is shared by multiple entries; no "
                                       f"catalog line added (which entry would it name?)"))
            continue
        summary = entries[nnn]["parsed"]["summary"]
        if not summary:
            refusals.append((nnn, "—", f"entry {nnn} has no catalog line and no "
                                       f"`**Summary**` field — author the line by hand "
                                       f"(fixer won't fabricate summaries)"))
            continue
        target = TYPE_TO_SECTION.get(entries[nnn]["parsed"]["declared_type"])
        if target not in buckets:
            refusals.append((nnn, "—", f"entry {nnn} has an unrecognized type; no "
                                       f"catalog line added"))
            continue
        stem = entries[nnn]["path"].name[:-3]
        buckets[target].append((nnn, f"- [[{stem}]] — {summary}"))

    # Canonical skeleton: each section is its header, then (blank + entries) only if
    # non-empty; sections separated by one blank line. An empty section (e.g.
    # `## Patterns`) is just its header — no trailing blank — so it renders as
    # `## Patterns\n\n## Constraints`, matching the init/promote skeleton.
    blocks = []
    for sec in SECTION_ORDER:
        block = [sec]
        rows = [line for _, line in sorted(buckets[sec], key=lambda t: t[0])]
        if rows:
            block.append("")
            block.extend(rows)
        blocks.append("\n".join(block))
    new = (
        "# Knowledge index\n"
        f"<!-- index-watermark: {max_nnn} -->\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )
    return new, old, refusals


# --- ENTRY fix (missing reciprocal) ------------------------------------------
def _forward_related(parsed_text: str) -> list:
    """Parse an entry's `## Related` block -> [(target_nnn, label)].

    Fence-aware, matching the detector's edge model (knowledge_lint is fence-aware
    and a fenced `## Related` example — e.g. in a convention doc — must NOT be read
    as a real edge). Uses the LAST non-fenced `## Related` header (the canonical
    terminal block), per the detector's own block-selection rule.
    """
    nonfenced = [ln for _, ln in _strip_fences(parsed_text.splitlines())]
    start = None
    for i, ln in enumerate(nonfenced):
        if ln.strip() == "## Related":
            start = i  # keep the last one
    if start is None:
        return []
    out = []
    for ln in nonfenced[start + 1:]:
        m = _RELATED_LINE_RE.match(ln.strip())
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


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
    texts = {nnn: e["path"].read_text() for nnn, e in entries.items()}
    edits = {}  # nnn -> new text (accumulated)
    refusals = []
    for a, e in entries.items():
        # QUARANTINE (source side): `entries[a]` is an arbitrary member of the group,
        # so its forward edges cannot be attributed to a specific entry.
        if a in dups:
            refusals.append((a, "—", f"NNN {a} is shared by multiple entries; its "
                                     f"forward links are not reciprocated"))
            continue
        a_stem = e["path"].name[:-3]
        for b, label in _forward_related(texts[a]):
            if b not in entries:
                continue  # broken link — not auto-fixed
            # QUARANTINE (target side): writing the back-link would land it in
            # whichever member of the group won the lookup — possibly the wrong entry.
            if b in dups:
                refusals.append((a, b, f"NNN {b} is shared by multiple entries; "
                                       f"back-link not written"))
                continue
            # already reciprocated? (B's Related targets A, or B's banner targets A)
            if a in entries[b]["parsed"]["backlinks"]:
                continue
            if label not in RECIPROCAL:
                refusals.append((a, b, f"forward label '{label}' not in closed vocab"))
                continue
            recip = RECIPROCAL[label]
            cur = edits.get(b, texts[b])
            new = add_related_link(cur, a_stem, recip)
            if label == "supersedes":  # B is superseded by A -> banner too (015/016)
                new = add_supersede_banner(new, a, a_stem, date)
            edits[b] = new
    return edits, refusals


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
    for nnn, new_text in batch["entries"].items():
        _assert_body_preserved(entries[nnn]["path"].read_text(), new_text)
    # Apply.
    if batch["index"] is not None:
        (kd / "index.md").write_text(batch["index"])
    for nnn, new_text in batch["entries"].items():
        entries[nnn]["path"].write_text(new_text)
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
