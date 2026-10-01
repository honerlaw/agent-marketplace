#!/usr/bin/env python3
"""Fold a legacy corpus's `index.md` and `overview.md` into its entries, then delete them.

minerva 3.0 derives the catalog on read (`knowledge_catalog.py`) from two metadata lines
every entry carries — `**Theme**` and `**Summary**` — instead of storing `index.md` and
`overview.md` beside the entries. A corpus written before 3.0 holds that data in the two
legacy files instead, so this one-time migration moves it onto the entries:

- a missing `**Summary**` is filled from the entry's `index.md` catalog line;
- a missing `**Theme**` is filled from the `overview.md` `## ` section that links the entry
  — single-valued, so the FIRST linking section wins — normalised to kebab-case from the
  heading text before its first `:` with a leading article dropped
  (`## The knowledge wiki: a navigable corpus` -> `knowledge-wiki`);
- then both legacy files are deleted.

**It inserts metadata lines and changes no other byte.** Each line goes directly after the
entry's `**Type**` line (else `**Date**`, else the H1), Theme before Summary, matching the
template order. Entry bodies, `## Related` blocks and legacy banners are untouched — the
catalog still reads stored back-links and banners.

What it cannot fill it reports rather than invents: an entry with no catalog line keeps no
Summary, and an entry the overview never linked stays unthemed. Both are named in the
output for hand-writing. A corpus with neither legacy file is a no-op, so re-running is safe.

CLI: `python3 knowledge_backfill.py <knowledge-dir> [--dry-run]`. `minerva:migrate-fix`
runs `--dry-run` first and applies only behind its confirmation gate.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_lint import (  # noqa: E402
    CATALOG_LINE_RE, ENTRY_RE, SUMMARY_RE, THEME_RE, TYPE_RE, WIKILINK_STEM_RE, _strip_fences)
from knowledge_spans import SECTION_RE  # noqa: E402

LEGACY_FILES = ("index.md", "overview.md")
DATE_LINE_RE = re.compile(r"^\*\*Date\*\*:")
H1_RE = re.compile(r"^#\s")
LEADING_ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)


def theme_slug(heading: str) -> str:
    """`The knowledge wiki: a navigable corpus` -> `knowledge-wiki`."""
    head = LEADING_ARTICLE_RE.sub("", heading.split(":", 1)[0].strip())
    return re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-")


def index_summaries(index_text: str) -> dict:
    """`{stem: catalog text}` from a legacy `index.md`, fence-aware."""
    out = {}
    for _, line in _strip_fences(index_text.splitlines()):
        m = CATALOG_LINE_RE.match(line.strip())
        if not m:
            continue
        rest = line.strip()[m.end():]
        text = re.sub(r"^\s*[—–-]\s*", "", rest).strip()
        if text:
            out.setdefault(m.group(1), text)
    return out


def _overview_sections(overview_text: str):
    """Yield `(heading, line)` for each non-fenced line of a legacy `overview.md`, with the
    `## ` section it sits in (None before the first). A header is a `## ` line at the start
    of the file or after a blank line: a prose line that wraps onto `## ` mid-paragraph is
    not a section."""
    heading, prev = None, ""
    for _, line in _strip_fences(overview_text.splitlines()):
        if SECTION_RE.match(line) and not prev.strip():
            heading = line[3:].strip()
        yield heading, line
        prev = line


def overview_themes(overview_text: str) -> dict:
    """`{stem: theme}` — the first `## ` section of a legacy `overview.md` linking each stem."""
    out = {}
    for heading, line in _overview_sections(overview_text):
        if heading is None:
            continue
        for m in WIKILINK_STEM_RE.finditer(line):
            out.setdefault(m.group(1), theme_slug(heading))
    return out


def overview_headings(overview_text: str) -> dict:
    """`{heading: theme}` for every `## ` section of a legacy `overview.md` — what the
    confirmation gate shows, so the theme names are reviewed as the script derives them."""
    return {h: theme_slug(h) for h, _ in _overview_sections(overview_text) if h is not None}


def insert_metadata(text: str, theme=None, summary=None) -> str:
    """Insert `**Theme**` / `**Summary**` lines into `text`, changing no other byte."""
    new = [f"**Theme**: {theme}"] * bool(theme) + [f"**Summary**: {summary}"] * bool(summary)
    if not new:
        return text
    lines = text.splitlines(keepends=True)
    nonfenced = list(_strip_fences([ln.rstrip("\r\n") for ln in lines]))
    head = []
    for i, line in nonfenced:
        if SECTION_RE.match(line):
            break
        head.append((i, line))
    anchor = None
    for pattern in (TYPE_RE, DATE_LINE_RE, H1_RE):
        anchor = next((i for i, line in head if pattern.match(line)), None)
        if anchor is not None:
            break
    if anchor is None:
        # No Type/Date/H1 in the metadata block: go after a leading frontmatter block, never
        # above its opening `---`, which would stop it parsing as frontmatter at all.
        anchor = -1
        if lines and lines[0].rstrip("\r\n") == "---":
            anchor = next((i for i in range(1, len(lines))
                           if lines[i].rstrip("\r\n") == "---"), -1)
    # Match the file's own line ending, so a CRLF entry stays CRLF throughout.
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    if anchor >= 0 and not lines[anchor].endswith("\n"):
        lines[anchor] += eol
    insert = [ln + eol for ln in new]
    if anchor >= 0 and H1_RE.match(lines[anchor]):
        insert = [eol] + insert  # keep the H1 separated from the metadata block
    return "".join(lines[:anchor + 1] + insert + lines[anchor + 1:])


def _has(pattern, text) -> bool:
    return any(pattern.match(line) for _, line in _strip_fences(text.splitlines()))


def plan(knowledge_dir) -> dict:
    """What a backfill would do, without writing anything."""
    kd = Path(knowledge_dir)
    legacy = [name for name in LEGACY_FILES if (kd / name).exists()]
    summaries = index_summaries((kd / "index.md").read_text()) if "index.md" in legacy else {}
    themes = overview_themes((kd / "overview.md").read_text()) if "overview.md" in legacy else {}
    edits, no_summary, no_theme = {}, [], []
    for path in sorted(p for p in kd.glob("*.md") if ENTRY_RE.match(p.name)):
        # newline="" on read and write: universal-newline mode would rewrite every CRLF.
        stem, text = path.name[:-3], path.read_text(newline="")
        theme = summary = None
        if not _has(THEME_RE, text):
            theme = themes.get(stem)
            if theme is None:
                no_theme.append(stem)
        if not _has(SUMMARY_RE, text):
            summary = summaries.get(stem)
            if summary is None:
                no_summary.append(stem)
        if theme or summary:
            edits[path] = insert_metadata(text, theme, summary)
    headings = overview_headings((kd / "overview.md").read_text()) if "overview.md" in legacy else {}
    return {"legacy": legacy, "edits": edits, "themes": headings,
            "no_summary": no_summary if legacy else [], "no_theme": no_theme if legacy else []}


def backfill(knowledge_dir, dry_run: bool = False) -> dict:
    """Apply `plan`: write the edits, then delete the legacy files. No-op without them."""
    result = plan(knowledge_dir)
    if not result["legacy"]:
        result["edits"] = {}
        return result
    if not dry_run:
        for path, text in result["edits"].items():
            with open(path, "w", newline="") as f:
                f.write(text)
        for name in result["legacy"]:
            (Path(knowledge_dir) / name).unlink()
    return result


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    dry_run = "--dry-run" in argv
    argv = [a for a in argv if a != "--dry-run"]
    knowledge_dir = argv[0] if argv else ".minerva/knowledge"
    result = backfill(knowledge_dir, dry_run=dry_run)
    if not result["legacy"]:
        print(f"knowledge-backfill: {knowledge_dir} has no index.md/overview.md — already migrated.")
        return 0
    verb = "would update" if dry_run else "updated"
    if result["themes"]:
        print("[themes derived from overview.md sections]")
        for heading, theme in result["themes"].items():
            print(f"  {theme}  <-  ## {heading}")
    print(f"knowledge-backfill: {verb} {len(result['edits'])} entr(ies); "
          f"{'would delete' if dry_run else 'deleted'} {', '.join(result['legacy'])}.")
    for label, stems in (("no Summary (write by hand)", result["no_summary"]),
                         ("no Theme (assign by hand)", result["no_theme"])):
        if stems:
            print(f"[{label}]")
            for stem in stems:
                print(f"  {stem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
