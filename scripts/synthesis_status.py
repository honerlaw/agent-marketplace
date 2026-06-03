#!/usr/bin/env python3
"""Deterministic, read-only **synthesis-status** signal for the knowledge wiki.

Phase C of the LLM-wiki effort. Answers the one mechanical question the
`minerva:synthesize` skill needs to decide IF it should (re)synthesize:
*how much scope has been added to `.minerva/knowledge/` since the last synthesis,
and do the existing overview's wikilinks still resolve?*

The synthesis layer is `.minerva/knowledge/overview.md` — a SEPARATE file (it does not
match `ENTRY_RE`, so the frozen detector `knowledge_lint.py` and the fixer
`knowledge_fix.py` ignore it). It carries a single state token:

    <!-- synthesis-watermark: NNN -->

`NNN` = the max entry NNN reflected by the last synthesis. This is a DIFFERENT marker
from `index.md`'s `index-watermark` (which must always equal max NNN — an integrity
invariant); the synthesis watermark deliberately *lags*, and the lag is the
un-synthesized-scope signal.

This module reuses the frozen detector's primitives (`_strip_fences`, `ENTRY_RE`,
`WIKILINK_RE`) rather than re-deriving them (knowledge entries 019 / 021 / 023). Live
entries are enumerated via the `ENTRY_RE` glob — NOT `parse_index`, which only reads
`index.md`'s fixed Type-section catalog and would report a *false* clean against a
theme-grouped overview. The overview link scan is fence-aware (knowledge entry 023), so
a fenced example link is never flagged as rot.

Limitations (the watermark is a NEW-SCOPE-ONLY floor):
  * detects ADDED entries (NNN > watermark), NOT in-place `## Related` / banner / body
    edits to already-synthesized entries — that drift is a judgment call for the skill.
  * attests synthesis INTENT, not body CONTENT — a watermark >= corpus-max with a stale
    overview body is not detectable here.

CLI: `python3 scripts/synthesis_status.py <knowledge-dir>` — prints the signal as JSON.
Read-only; never writes.
"""
import json
import re
import sys
from pathlib import Path

from knowledge_lint import ENTRY_RE, WIKILINK_RE, _strip_fences

# Distinct from knowledge_lint.WATERMARK_RE (`index-watermark`). New marker, new regex,
# single-sourced here (it lives only in overview.md).
SYNTH_WATERMARK_RE = re.compile(r"<!--\s*synthesis-watermark:\s*(\d{3})\s*-->")

OVERVIEW_NAME = "overview.md"


def _entry_nnns(kd: Path) -> set:
    """The set of live entry NNNs (3-digit strings), via the ENTRY_RE glob."""
    return {ENTRY_RE.match(p.name).group(1) for p in kd.glob("*.md")
            if ENTRY_RE.match(p.name)}


def synthesis_status(knowledge_dir) -> dict:
    """Return the deterministic synthesis-status signal for `knowledge_dir`.

    Keys:
      overview_exists      bool
      synthesis_watermark  int  (-1 if no overview / no watermark comment)
      corpus_max_nnn       int  (-1 if the corpus has no entries)
      unsynthesized        sorted list[str] of entry NNNs with NNN > watermark
      link_rot             sorted list[str] of [[NNN-type-slug]] stems in the overview
                           that do not resolve to a live entry
    """
    kd = Path(knowledge_dir)
    entry_nnns = _entry_nnns(kd)
    corpus_max = max((int(n) for n in entry_nnns), default=-1)

    overview = kd / OVERVIEW_NAME
    if not overview.exists():
        return {
            "overview_exists": False,
            "synthesis_watermark": -1,
            "corpus_max_nnn": corpus_max,
            "unsynthesized": sorted(entry_nnns),
            "link_rot": [],
        }

    lines = overview.read_text().splitlines()
    nonfenced = list(_strip_fences(lines))

    watermark = -1
    for _, line in nonfenced:
        m = SYNTH_WATERMARK_RE.search(line)
        if m:
            watermark = int(m.group(1))
            break

    # Fence-aware wikilink scan (knowledge entry 023): only links OUTSIDE code fences.
    link_rot = set()
    for _, line in nonfenced:
        for m in WIKILINK_RE.finditer(line):
            stem = m.group(0)[2:-2]  # strip the surrounding [[ ]]
            if m.group(1) not in entry_nnns:
                link_rot.add(stem)

    unsynthesized = sorted(n for n in entry_nnns if int(n) > watermark)

    return {
        "overview_exists": True,
        "synthesis_watermark": watermark,
        "corpus_max_nnn": corpus_max,
        "unsynthesized": unsynthesized,
        "link_rot": sorted(link_rot),
    }


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    print(json.dumps(synthesis_status(knowledge_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
