#!/usr/bin/env python3
"""Derive the `.minerva/knowledge/` catalog on read — nothing here is ever committed.

The wiki used to store three aggregates beside its entries: an `index.md` catalog, the
reverse direction of every `## Related` link plus supersession banners, and a hand-written
`overview.md`. Each was a cache of data the entries already hold, and each was a file
concurrent PRs fought over, which is why a post-merge reconciliation pass existed at all
(`2026-08-05-decision-promote-add-only-reconcile-on-default`). This module computes all
three from the entries instead, so entries are write-once and nothing is reconciled:

- **catalog**: every entry grouped by its `**Theme**`, one line each —
  `[[<stem>]] (<type>) — <**Summary**>`. An entry with no theme is grouped under
  `(unthemed)`; one with no summary falls back to its H1 title.
- **backlinks** (`--links-to <stem>`): every entry whose `## Related` block links the
  stem, with that entry's label. The reverse of a forward link is a grep, not a write.
- **supersession**: an entry is superseded by the UNION of three sources, each successor
  listed once — another entry's `supersedes` edge to it, its own legacy `superseded by`
  edge, and its own legacy `<!-- superseded-by: -->` banner. A union rather than a
  precedence order, so a stored banner and a derived edge can never contradict or
  double-mark: they only ever name successors.

`index.md` and `overview.md` are ignored if a legacy corpus still has them
(`knowledge_backfill.py` folds them into the entries and deletes them).

CLI:
  python3 knowledge_catalog.py <knowledge-dir>                  # grouped by theme
  python3 knowledge_catalog.py <knowledge-dir> --by-type        # grouped by type
  python3 knowledge_catalog.py <knowledge-dir> --themes         # theme names + counts
  python3 knowledge_catalog.py <knowledge-dir> --links-to STEM  # computed backlinks
Read-only; never writes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_lint import (  # noqa: E402
    ENTRY_RE, SUPERSEDED_BY_LABEL_RE, SUPERSEDES_LABEL_RE, corpus_id_width, id_sort_key,
    parse_entry)

UNTHEMED = "(unthemed)"



def load_entries(knowledge_dir) -> dict:
    """`{stem: parsed_entry}` for every conforming entry file, in id order."""
    kd = Path(knowledge_dir)
    paths = sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name))
    parsed = {p.name[:-3]: parse_entry(p) for p in paths}
    width = corpus_id_width(e["nnn"] for e in parsed.values())
    return dict(sorted(parsed.items(),
                       key=lambda kv: (id_sort_key(kv[1]["nnn"], width), kv[0])))


def _older(entries: dict, a: str, b: str) -> bool:
    """True iff entry `a` is strictly older than entry `b` (by id; same-day is not older)."""
    width = corpus_id_width(e["nnn"] for e in entries.values())
    return id_sort_key(entries[a]["nnn"], width) < id_sort_key(entries[b]["nnn"], width)


def inverted_supersedes(entries: dict) -> list:
    """`[(stem, target)]` where an entry claims to supersede a NEWER one.

    An entry cannot retire one written after it; such an edge is a mislabelled
    `superseded by` (a real one, written as a reciprocal, survives in a legacy corpus).
    `superseded_by` ignores it rather than mark the live entry retired, and
    `knowledge_lint` warns about the same edge.
    """
    return [(stem, target) for stem, e in entries.items() for target, label in e["edges"]
            if label and SUPERSEDES_LABEL_RE.match(label) and target in entries
            and _older(entries, stem, target)]


def superseded_by(entries: dict) -> dict:
    """`{stem: [successor stems]}` — the union of all three supersession sources."""
    inverted = set(inverted_supersedes(entries))
    out = {stem: set() for stem in entries}
    for stem, e in entries.items():
        for target, label in e["edges"]:
            if not label:
                continue
            if (SUPERSEDES_LABEL_RE.match(label) and target in out
                    and (stem, target) not in inverted):
                out[target].add(stem)
            elif SUPERSEDED_BY_LABEL_RE.match(label):
                out[stem].add(target)
        out[stem] |= set(e["banner_stems"])
    return {stem: sorted(s) for stem, s in out.items() if s}


def backlinks(entries: dict, stem: str) -> list:
    """`[(source_stem, label_or_None)]` for every entry whose `## Related` links `stem`."""
    return [(src, label) for src, e in entries.items()
            for target, label in e["edges"] if target == stem]


def catalog_line(stem: str, e: dict, successors) -> str:
    text = e["summary"] or e["title"] or stem
    line = f"- [[{stem}]] ({e['declared_type']}) — {text}"
    if successors:
        line += " (superseded by " + ", ".join(f"[[{s}]]" for s in successors) + ")"
    return line


def grouped(entries: dict, key) -> dict:
    """`{group: [stem]}`, groups sorted by name with `(unthemed)` last."""
    groups = {}
    for stem, e in entries.items():
        groups.setdefault(key(e) or UNTHEMED, []).append(stem)
    return dict(sorted(groups.items(), key=lambda kv: (kv[0] == UNTHEMED, kv[0])))


def render_catalog(entries: dict, by_type: bool = False) -> str:
    sup = superseded_by(entries)
    groups = grouped(entries, (lambda e: e["declared_type"]) if by_type
                     else (lambda e: e["theme"]))
    out = [f"# Knowledge catalog — {len(entries)} entries, {len(groups)} "
           f"{'types' if by_type else 'themes'}"]
    for name, stems in groups.items():
        out.append(f"\n## {name} ({len(stems)})")
        out.extend(catalog_line(s, entries[s], sup.get(s)) for s in stems)
    return "\n".join(out) + "\n"


def theme_counts(entries: dict) -> dict:
    return {name: len(stems) for name, stems in grouped(entries, lambda e: e["theme"]).items()}


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    knowledge_dir = ".minerva/knowledge"
    if argv and not argv[0].startswith("--"):
        knowledge_dir = argv.pop(0)
    if not Path(knowledge_dir).is_dir():
        print(f"knowledge-catalog: {knowledge_dir} does not exist", file=sys.stderr)
        return 2
    entries = load_entries(knowledge_dir)
    if argv[:1] == ["--themes"]:
        for name, n in theme_counts(entries).items():
            print(f"{name}\t{n}")
    elif argv[:1] == ["--links-to"] and len(argv) == 2:
        for src, label in backlinks(entries, argv[1]):
            print(f"- [[{src}]]" + (f" — {label}" if label else ""))
    elif argv[:1] == ["--by-type"]:
        sys.stdout.write(render_catalog(entries, by_type=True))
    elif not argv:
        sys.stdout.write(render_catalog(entries))
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
