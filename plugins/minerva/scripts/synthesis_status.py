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
from `index.md`'s `index-watermark` (which records how far the catalog has actually
been reconciled, and may lag the corpus); the synthesis watermark also *lags*, and its lag is the
un-synthesized-scope signal.

This module reuses the frozen detector's primitives (`_strip_fences`, `ENTRY_RE`,
`WIKILINK_RE`) rather than re-deriving them (knowledge entries 019 / 021 / 023). Live
entries are enumerated via the `ENTRY_RE` glob — NOT `parse_index`, which only reads
`index.md`'s fixed Type-section catalog and would report a *false* clean against a
theme-grouped overview. Both the link scan AND the watermark read are fence-aware
(knowledge entry 023): a fenced example link is never flagged as rot, and a
`synthesis-watermark` comment inside a code fence is never honored. Link-rot resolution
is by NNN only — a wikilink whose NNN matches no live entry is rot — mirroring the frozen
detector's `## Related` broken-link family (slug-accuracy is out of scope here).

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

from knowledge_lint import ENTRY_RE, WIKILINK_STEM_RE, _strip_fences

# There is no synthesis watermark any more. It was a scalar floor — an entry counted as
# synthesized iff its id exceeded the mark — which knowledge 053 established cannot
# express reconciliation state, because records merge out of order: unit A takes 050 and
# B takes 051, B merges and advances the mark, then A merges and sits BELOW it, silently
# counting as done. 053 fixed that for the index and left this copy live.
#
# A date id cannot support a floor even in principle: same-day ties are ordinary, so the
# ids are not totally ordered. The signal is now per-record and derived from the artifact
# itself — an entry is synthesized iff the overview actually links it, which is both
# stronger than the floor (it survives an overview rewrite that drops an entry) and
# self-healing.

OVERVIEW_NAME = "overview.md"


def _entry_stems(kd: Path) -> set:
    """The set of live entry stems, via the ENTRY_RE glob."""
    return {p.name[:-3] for p in kd.glob("*.md") if ENTRY_RE.match(p.name)}


def synthesis_status(knowledge_dir) -> dict:
    """Return the deterministic synthesis-status signal for `knowledge_dir`.

    Keys:
      overview_exists  bool
      unsynthesized    sorted list[str] of entry stems the overview does not link
      link_rot         sorted list[str] of stems the overview links that have no entry

    Both signals resolve on the full STEM. Resolving on the leading id alone would let a
    link to one same-day entry read as satisfied by its sibling.
    """
    kd = Path(knowledge_dir)
    entry_stems = _entry_stems(kd)

    overview = kd / OVERVIEW_NAME
    if not overview.exists():
        return {
            "overview_exists": False,
            "unsynthesized": sorted(entry_stems),
            "link_rot": [],
        }

    lines = overview.read_text().splitlines()
    nonfenced = list(_strip_fences(lines))

    # Fence-aware wikilink scan (knowledge entry 023): only links OUTSIDE code fences.
    linked = set()
    for _, line in nonfenced:
        linked.update(m.group(1) for m in WIKILINK_STEM_RE.finditer(line))

    return {
        "overview_exists": True,
        "unsynthesized": sorted(entry_stems - linked),
        "link_rot": sorted(linked - entry_stems),
    }


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    print(json.dumps(synthesis_status(knowledge_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
