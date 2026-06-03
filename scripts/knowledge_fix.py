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
  * INDEX edits (watermark / stale catalog line / wrong Type section) — `index.md`
    has no span model; guarded instead by a skeleton-preserving canonical serializer
    (preserve the `# Knowledge index` H1, the four Type headers incl. the empty
    `## Patterns`, and ascending-NNN order; never touch an entry file).

NOT auto-fixed (left to the human / advisory): missing catalog line (needs a
summary), broken `## Related` link, and the judged dimensions (orphans /
contradictions / staleness; advisory per knowledge 013).

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


def _entries(kd: Path) -> dict:
    """nnn -> {path, parsed}, excluding index.md."""
    out = {}
    for p in sorted(kd.glob("*.md")):
        if ENTRY_RE.match(p.name):
            out[ENTRY_RE.match(p.name).group(1)] = {"path": p, "parsed": parse_entry(p)}
    return out


# --- INDEX fix (watermark / stale line / wrong Type section) ------------------
def plan_index(kd: Path) -> tuple:
    """Return (new_index_text, old_index_text) — a canonical, skeleton-preserving
    serialization that fixes watermark, removes stale catalog lines, and relocates
    wrong-Type lines. Preserves each surviving catalog line verbatim (summary intact)
    and ascending-NNN order. Does NOT add missing catalog lines (needs a summary).
    """
    index_path = kd / "index.md"
    old = index_path.read_text() if index_path.exists() else ""
    entries = _entries(kd)
    max_nnn = max(entries) if entries else "000"

    # Collect surviving catalog lines verbatim, keyed by NNN, from the existing index.
    catalog = {}  # nnn -> verbatim line
    for ln in old.splitlines():
        m = _CATALOG_LINE_RE.match(ln.strip())
        if m and m.group(1) in entries:  # drop stale lines (NNN with no entry file)
            catalog[m.group(1)] = ln.rstrip()

    # Bucket each surviving line under the entry's DECLARED type (relocates wrong-Type).
    buckets = {sec: [] for sec in SECTION_ORDER}
    for nnn, line in catalog.items():
        sec = TYPE_TO_SECTION.get(entries[nnn]["parsed"]["declared_type"])
        if sec in buckets:
            buckets[sec].append((nnn, line))

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
    return new, old


# --- ENTRY fix (missing reciprocal) ------------------------------------------
def _forward_related(parsed_text: str) -> list:
    """Parse an entry's `## Related` block -> [(target_nnn, label)]."""
    out = []
    in_related = False
    for ln in parsed_text.splitlines():
        if ln.strip() == "## Related":
            in_related = True
            continue
        if in_related:
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
    texts = {nnn: e["path"].read_text() for nnn, e in entries.items()}
    edits = {}  # nnn -> new text (accumulated)
    refusals = []
    for a, e in entries.items():
        a_stem = e["path"].name[:-3]
        for b, label in _forward_related(texts[a]):
            if b not in entries:
                continue  # broken link — not auto-fixed
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
    new_index, old_index = plan_index(kd)
    recip_edits, refusals = plan_reciprocals(kd, date)
    index_change = new_index if new_index != old_index else None
    return {"index": index_change, "entries": recip_edits, "refusals": refusals}


def apply(kd: Path, date: str) -> dict:
    """Recompute once, validate, then write the batch atomically."""
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
        date = argv[argv.index("--date") + 1]
        argv = [a for i, a in enumerate(argv) if a not in ("--date", date)]
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
