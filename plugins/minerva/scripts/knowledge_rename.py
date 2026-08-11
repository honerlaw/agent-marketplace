#!/usr/bin/env python3
"""Rename `NNN`-prefixed knowledge entries and work units to `YYYY-MM-DD` ids.

The one-time migration behind the switch from an allocated sequential id to a date.
It is a WRITER, which is why it lives here and not in `minerva:migrate` — that skill is
read-only by contract (knowledge 020/026), and its companion `minerva:migrate-fix`
wraps this module the way `minerva:lint-fix` wraps the fixer.

Two namespaces move together:

  `.minerva/knowledge/NNN-type-slug.md`  ->  `YYYY-MM-DD-type-slug.md`
  `.minerva/work/NNN-slug/`             ->  `YYYY-MM-DD-slug/`

and every reference to them is retargeted: `[[wikilinks]]` in entry bodies, `index.md`
and `overview.md`; the `<!-- superseded-by: -->` marker and its visible banner line; and
the `**Context**: .minerva/work/...` field each entry carries.

Git branches are deliberately NOT renamed. `minerva:cleanup`'s merge detection matches a
branch by its literal name, and a merged PR's head ref is immutable state on the forge —
renaming would break both for no gain, since a branch name is not corpus content.

## The date

`landing_date` takes the OLDEST commit touching a path, following renames:

    git log --follow --reverse --format=%cs -- <path>

`--reverse` with the first line, never `-1`: git orders reverse-chronologically, so a
bare `-1` returns the NEWEST commit — wrong for any path touched more than once.

There is deliberately **no `--diff-filter=A`**, though "the add commit" is what we want.
The two flags are incompatible: under `--follow` git reports a path's original creation
as a rename rather than an add, so pairing them filters every commit away and the path
comes back undated — which `plan` then SKIPS, leaving a silently half-migrated corpus.
On this repo the pairing dropped 5 of 102 paths, every one touched by the historical
`git mv` that moved `.minerva/decisions/` to `.minerva/knowledge/`.

Following renames without the filter is both safer and more accurate: the oldest commit
that touches a path IS its creation. Verified against the narrower
`--diff-filter=A` form across all 58 entries — identical dates, zero disagreements.

A work unit is anchored on its `proposal.md` rather than the directory pathspec, so a
unit whose files landed across several commits still resolves to when the unit began.

What this yields is the LANDING date — when the change reached the branch being scanned.
Under squash-merge that is the ship date; `minerva:ship` prefers `--squash` but falls
back to `--merge`/`--rebase`, and a consumer repo may differ, in which case it is the
original commit date. The imprecision is accepted deliberately: a date carries no
identity and no ordering weight beyond sort, so nothing downstream depends on which of
the two it is.

An entry's date and its work unit's date are derived INDEPENDENTLY and may legitimately
differ — an entry promoted in a later PR than its proposal is normal — so `## Context`
rewriting goes through the directory map by lookup, never by assuming they agree.

A filename date may also disagree with the entry's own `**Date**:` field, and that is
left alone. The filename records when the entry landed; the body records when it was
authored. Rewriting the body to agree would overwrite authored metadata with a derived
value, the inversion knowledge 058 warns against.

## Collisions

`plan` computes the ENTIRE target-stem set before anything moves, and `apply` refuses the
whole batch if any target is claimed twice. Checking per-file as you go is too late: the
first half of a batch would already be renamed with no clean way back.

A collision means two entries share a date, a type and a slug — which makes them the same
entry, wanting a merge rather than a rename. Sharing only a date is not a collision and is
never treated as one.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_lint import (DATE_ID_RE, ENTRY_RE, ID_RE_SRC,  # noqa: E402
                            WIKILINK_STEM_RE, _strip_fences, is_date_id)
from knowledge_spans import FENCE_RE  # noqa: E402

# The SHARED id grammar, date arm first — not a bare `\d{3,}`. Against an already
# migrated `2026-08-07-foo` a bare-NNN pattern captures `2026` as the id and
# `08-07-foo` as the slug, so the tool re-dates a directory it already dated and
# yields `2026-08-10-08-07-foo`. The entry branch never had this bug because
# `ENTRY_RE` embeds the same alternation; this pattern was the codebase's one
# outlier, which is what made the migration non-idempotent for work dirs.
WORK_DIR_RE = re.compile(rf"^({ID_RE_SRC})-(.+)$")
# What terminates a path reference written in prose. `,.;:` are excluded alongside
# whitespace and the bracket/backtick delimiters, because a trailing separator used to
# be captured INTO the lookup key: `**Context**: .minerva/work/111-foo, .minerva/work/…`
# yielded the key `111-foo,`, which missed the map, so that path was silently left
# behind while its neighbour on the same line was rewritten.
_PATH_CHARS = r"[^\s/`)\],.;:]+"
CONTEXT_PATH_RE = re.compile(rf"(\.minerva/work/)({_PATH_CHARS})")
# An entry referenced by PATH rather than by wikilink — in prose, in backticks, or as
# the target of a markdown link. Renaming the file without retargeting these leaves a
# dead path that no tool here reports: the linter's edge model only knows `[[wikilinks]]`,
# so a corpus can lose every one of these and still lint clean, before AND after.
KNOWLEDGE_PATH_RE = re.compile(rf"(\.minerva/knowledge/)({_PATH_CHARS})\.md")
# A markdown link to a sibling entry: `[text](stem.md)` or `[text](./stem.md)`. The
# `.minerva/knowledge/`-prefixed form is already covered by KNOWLEDGE_PATH_RE above.
MD_LINK_RE = re.compile(rf"(\]\((?:\./)?)({_PATH_CHARS})\.md\)")
# `[[139]]` — an entry named by bare id, with no slug. Counted, never rewritten: see
# `plan`'s docstring for why resolving it is unsafe.
BARE_SHORTHAND_RE = re.compile(r"\[\[(\d{3,})\]\]")
WATERMARK_LINE_RE = re.compile(r"^\s*<!--\s*(?:index|synthesis)-watermark:[^>]*-->\s*$")


class CollisionError(Exception):
    """Raised before any move when two sources want one target."""


def _git(args, cwd):
    try:
        proc = subprocess.run(["git"] + args, cwd=str(cwd),
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def landing_date(repo_root, rel_path):
    """The oldest add-commit date for `rel_path`, as `YYYY-MM-DD`, or None."""
    # `--follow` WITHOUT `--diff-filter=A`. The two are incompatible: under `--follow`
    # git reports a path's original creation as a rename (R) rather than an add (A), so
    # combining them filters every commit away and the path returns undated — silently
    # skipped, leaving a half-migrated corpus. Measured on this repo: the combination
    # dropped 5 of 102 paths, all of them ones a historical `git mv` had touched.
    # The oldest commit that touches the path, following renames, IS its creation.
    out = _git(["log", "--follow", "--reverse", "--format=%cs",
                "--", str(rel_path)], repo_root)
    if not out:
        return None
    for line in out.splitlines():
        if line.strip():
            return line.strip()
    return None


def _corpus_md(root: Path):
    """Yield `(path, text)` for every readable markdown file in the corpus.

    Shared by `plan` (which only reads) and `apply` (which rewrites), so the set of
    files scanned for references is by construction the set of files rewritten.

    Paths are tested RELATIVE to the repo root, never absolutely. minerva runs its own
    work inside `.minerva/worktrees/<unit>/`, so when this executes in a worktree the
    absolute path of EVERY file contains that segment — an absolute test silently skips
    the entire corpus and reports "0 files rewritten" while the renames succeed, leaving
    every link dangling.
    """
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if ".git" in rel.parts or rel.parts[:2] == (".minerva", "worktrees"):
            continue
        try:
            yield p, p.read_text()
        except (OSError, UnicodeDecodeError):
            continue


def _resolve_shorthand(ids, by_entry_id, by_work_id, entries, already_migrated):
    """Resolve bare `[[NNN]]` ids to new stems. Returns ({id: new_stem}, [(id, reason)]).

    Refuses by default and resolves only what is provably unambiguous, because a wrong
    rewrite here is invisible where an unresolved reference is not. The rules come from
    measured failure data, not intuition: across 23 references where a bare number named
    exactly ONE entry, about 6 meant something else — usually the same-numbered WORK UNIT,
    one of them annotated "(work unit)" in the prose beside it.

    **The whole-corpus precondition.** This is sound only within a single pass over a
    corpus that is still entirely legacy. The work-unit guard below can only see units
    that still carry a legacy id; once a unit is renamed its number leaves the filesystem,
    so a reference that meant that unit stops colliding with anything and would resolve
    "safely" to whatever entry still holds the number — the exact failure the guard
    exists to prevent, reintroduced silently. So a partially-migrated corpus refuses
    EVERYTHING. That also means resolution has one usable window, the first full
    migration; afterwards the information needed to be safe is simply gone, and the
    honest output is a refusal a human resolves.
    """
    if already_migrated:
        return {}, [(i, f"corpus is partially migrated ({len(already_migrated)} paths "
                       f"already carry a date id), so the id -> work-unit collision map "
                       f"is incomplete and no resolution here can be trusted")
                    for i in ids]
    resolved, refusals = {}, []
    for i in ids:
        if i in by_work_id:
            refusals.append((i, f"ambiguous: work unit "
                                f"'{by_work_id[i][0]}' also has id {i}"))
        elif i not in by_entry_id:
            refusals.append((i, f"no entry has id {i} (it may be undated, or refer to "
                                f"something outside this corpus)"))
        elif len(by_entry_id[i]) > 1:
            refusals.append((i, f"{len(by_entry_id[i])} entries share id {i}: "
                                f"{', '.join(by_entry_id[i])}"))
        elif by_entry_id[i][0] not in entries:
            refusals.append((i, f"entry '{by_entry_id[i][0]}' has id {i} but git could not "
                                f"date it, so there is no target stem to resolve to"))
        else:
            resolved[i] = entries[by_entry_id[i][0]]
    return resolved, refusals


def plan(repo_root, knowledge_dir=None, work_dir=None, resolve_shorthand=False):
    """Compute the full rename plan without touching anything.

    Returns {entries: {old_stem: new_stem}, work: {old_name: new_name},
             undated: [...], collisions: [(target, [sources])],
             shorthand_refs: {id: count}}.

    `undated` holds paths git could not date — an uncommitted file, or a corpus with no
    history. They are reported and SKIPPED rather than guessed at: inventing a date would
    silently mint an id that does not correspond to anything.

    `shorthand_refs` counts `[[139]]`-style references — an entry named by bare id, with
    no slug. They are COUNTED and never rewritten. Not rewriting is defensible: there is
    no slug to match on, and resolving by number alone is wrong often enough to refuse.
    In one 637-entry corpus, of 23 cases where a number named exactly one entry, ~6
    meant something else — usually the same-numbered WORK UNIT, one of them literally
    annotated "(work unit)" in the prose. Doing it SILENTLY is what is not defensible:
    before the rename a reader could resolve `[[139]]` with `ls .minerva/knowledge/139-*`,
    and after it the number appears in no filename at all, so an unreported one is a
    reference that quietly stops resolving.
    """
    root = Path(repo_root)
    kd = Path(knowledge_dir) if knowledge_dir else root / ".minerva" / "knowledge"
    wd = Path(work_dir) if work_dir else root / ".minerva" / "work"

    entries, work, undated = {}, {}, []
    # What the scan SKIPPED or silently reshaped, so the caller can report it instead of
    # leaving the operator to spot it. A peer's 637-entry migration produced three
    # corrupted rows among 552 correct ones and they were missed on the dry run — a plan
    # is a control only when its anomalies are separable at the output's real size.
    already_migrated, invalid_date_ids = [], []
    # Legacy id -> [old stem]. Keyed on the BARE id, which `entries`/`work` are not: they
    # key on the full stem. Two entries can share a legacy id — this repo's own history
    # has `001-gitignore-before-worktree` and `001-review-lens-ownership` — so this is a
    # grouping, and treating it as a dict lookup would silently miss exactly that case.
    by_entry_id, by_work_id = {}, {}

    if kd.is_dir():
        for p in sorted(kd.glob("*.md")):
            m = ENTRY_RE.match(p.name)
            if not m:
                continue  # not an entry
            if is_date_id(m.group(1)):
                already_migrated.append(str(p.relative_to(root)))
                continue
            if DATE_ID_RE.match(m.group(1)):
                # Date-SHAPED but not a real date (`2026-13-45`). It is re-dated like a
                # legacy id, which is defensible; doing it without saying so is not.
                invalid_date_ids.append(str(p.relative_to(root)))
            # Record the id BEFORE the date lookup. The grouping exists to detect
            # collisions, and an entry git cannot date still HOLDS that id — recording it
            # only on the dated path makes a real collision invisible, and resolution
            # then picks the surviving entry with false confidence.
            by_entry_id.setdefault(m.group(1), []).append(p.name[:-3])
            d = landing_date(root, p.relative_to(root))
            if not d:
                undated.append(str(p.relative_to(root)))
                continue
            rest = p.name[len(m.group(1)) + 1:-3]  # strip "<id>-" and ".md"
            entries[p.name[:-3]] = f"{d}-{rest}"

    if wd.is_dir():
        for p in sorted(x for x in wd.iterdir() if x.is_dir()):
            m = WORK_DIR_RE.match(p.name)
            if not m:
                continue  # not a work unit
            if is_date_id(m.group(1)):
                already_migrated.append(str(p.relative_to(root)))
                continue
            if DATE_ID_RE.match(m.group(1)):
                invalid_date_ids.append(str(p.relative_to(root)))
            by_work_id.setdefault(m.group(1), []).append(p.name)  # before dating: see above
            anchor = p / "proposal.md"
            d = landing_date(root, (anchor if anchor.exists() else p).relative_to(root))
            if not d:
                undated.append(str(p.relative_to(root)))
                continue
            work[p.name] = f"{d}-{m.group(2)}"

    collisions = []
    for mapping in (entries, work):
        seen = {}
        for old, new in mapping.items():
            seen.setdefault(new, []).append(old)
        collisions.extend((t, s) for t, s in sorted(seen.items()) if len(s) > 1)

    # Fence-aware, like every other scan in this plugin: a `[[139]]` inside a fenced
    # block is documentation showing what the old syntax looked like, not a live
    # reference, and counting it would report work that does not exist. Same rule as
    # `rewrite_links` below and `knowledge_lint.related_edges`.
    shorthand_refs, shorthand_sites = {}, []
    for path, text in _corpus_md(root):
        rel = str(path.relative_to(root))
        for i, line in _strip_fences(text.splitlines()):
            for m in BARE_SHORTHAND_RE.finditer(line):
                shorthand_refs[m.group(1)] = shorthand_refs.get(m.group(1), 0) + 1
                # Per-occurrence, because every refusal below is resolved BY HAND and a
                # report without file+line makes that needlessly expensive.
                shorthand_sites.append((rel, i + 1, m.group(1)))

    resolved, refusals = _resolve_shorthand(
        sorted(shorthand_refs), by_entry_id, by_work_id, entries,
        already_migrated) if resolve_shorthand else ({}, [])

    return {"entries": entries, "work": work,
            "undated": undated, "collisions": collisions,
            "shorthand_refs": shorthand_refs, "shorthand_sites": shorthand_sites,
            "already_migrated": already_migrated,
            "invalid_date_ids": invalid_date_ids,
            "shorthand_resolved": resolved, "shorthand_refusals": refusals}


def rewrite_links(text, stem_map, dir_map=None, shorthand_map=None):
    """Retarget wikilinks, banner markers and Context paths OUTSIDE code fences.

    Fence-awareness is the whole safety property (knowledge 023, and 028 recording it
    violated a third time): a `[[...]]` inside a fenced block is documentation showing
    what a link looks like, not an edge. Rewriting it corrupts the example — and every
    skill that documents the convention contains one.

    A target absent from the map is left exactly as it was. There is no fuzzy matching:
    a link this migration cannot resolve is reported by the caller, never guessed at.
    """
    out, fenced = [], False
    for line in text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            fenced = not fenced
            out.append(line)
            continue
        if fenced:
            out.append(line)
            continue
        # Drop the retired scalar watermarks. They are inert once nothing reads them,
        # but leaving them invites the next reader to restore the floor they encoded —
        # and a floor cannot work over date ids at all, since same-day ties mean the
        # ids are not totally ordered.
        if WATERMARK_LINE_RE.match(line):
            continue
        line = WIKILINK_STEM_RE.sub(
            lambda m: f"[[{stem_map.get(m.group(1), m.group(1))}]]", line)
        line = re.sub(
            r"(<!-- superseded-by: )([^\s]+)( -->)",
            lambda m: m.group(1) + stem_map.get(m.group(2), m.group(2)) + m.group(3),
            line)
        # Entries referenced by PATH, not by wikilink. Map-lookup-only, exactly like
        # every other form here: a stem absent from the map is left byte-identical, so
        # these patterns can only retarget a file this migration is already moving.
        line = KNOWLEDGE_PATH_RE.sub(
            lambda m: m.group(1) + stem_map.get(m.group(2), m.group(2)) + ".md", line)
        line = MD_LINK_RE.sub(
            lambda m: m.group(1) + stem_map.get(m.group(2), m.group(2)) + ".md)", line)
        if dir_map:
            line = CONTEXT_PATH_RE.sub(
                lambda m: m.group(1) + dir_map.get(m.group(2), m.group(2)), line)
        if shorthand_map:
            # Bare `[[139]]` -> the full stem. Map-lookup-only like the rest: an id absent
            # from the map is left byte-identical, and the map holds only what
            # `_resolve_shorthand` proved unambiguous. Empty/None by default, so the
            # default rewrite is byte-for-byte what it was before this existed.
            line = BARE_SHORTHAND_RE.sub(
                lambda m: (f"[[{shorthand_map[m.group(1)]}]]"
                           if m.group(1) in shorthand_map else m.group(0)), line)
        out.append(line)
    return "".join(out)


def apply(repo_root, plan_result, knowledge_dir=None, work_dir=None):
    """Perform the renames and rewrite every reference. Refuses on any collision."""
    if plan_result["collisions"]:
        raise CollisionError(
            "refusing the whole batch — these targets are claimed twice: "
            + "; ".join(f"{t} <- {', '.join(s)}" for t, s in plan_result["collisions"]))

    root = Path(repo_root)
    kd = Path(knowledge_dir) if knowledge_dir else root / ".minerva" / "knowledge"
    wd = Path(work_dir) if work_dir else root / ".minerva" / "work"
    stem_map, dir_map = plan_result["entries"], plan_result["work"]

    # Rewrite references BEFORE moving, so every path in the map still resolves.
    touched = 0
    shorthand_map = plan_result.get("shorthand_resolved") or None
    for p, text in _corpus_md(root):
        new = rewrite_links(text, stem_map, dir_map, shorthand_map)
        if new != text:
            p.write_text(new)
            touched += 1

    for old, new in sorted(stem_map.items()):
        _git(["mv", str((kd / f"{old}.md").relative_to(root)),
              str((kd / f"{new}.md").relative_to(root))], root)
    for old, new in sorted(dir_map.items()):
        _git(["mv", str((wd / old).relative_to(root)),
              str((wd / new).relative_to(root))], root)

    return {"entries_renamed": len(stem_map), "work_renamed": len(dir_map),
            "files_rewritten": touched, "undated": plan_result["undated"],
            "shorthand_refs": plan_result.get("shorthand_refs", {})}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(_git(["rev-parse", "--show-toplevel"], Path.cwd()).strip())
    result = plan(root, resolve_shorthand="--resolve-shorthand" in argv)
    if result["collisions"]:
        for target, sources in result["collisions"]:
            print(f"COLLISION {target} <- {', '.join(sources)}", file=sys.stderr)
        return 1
    for path in result["undated"]:
        print(f"UNDATED (skipped) {path}", file=sys.stderr)
    # Say what was skipped and what was reshaped. A run that reports only what it DID
    # leaves the operator to find the rest by reading every row, which does not scale:
    # three corrupted rows among 552 were missed on a real dry run.
    if result.get("already_migrated"):
        print(f"ALREADY MIGRATED (skipped) {len(result['already_migrated'])} path(s)",
              file=sys.stderr)
    for path in result.get("invalid_date_ids", []):
        print(f"INVALID DATE ID (re-dated) {path} — date-shaped but not a real date",
              file=sys.stderr)

    shorthand = result.get("shorthand_refs", {})
    resolved = result.get("shorthand_resolved", {})
    refusals = result.get("shorthand_refusals", [])
    if shorthand:
        total = sum(shorthand.values())
        verb = "resolved where provably safe" if resolved or refusals else "not rewritten"
        print(f"SHORTHAND ({verb}) {total} bare [[NNN]] reference(s) across "
              f"{len(shorthand)} id(s): "
              + ", ".join(f"[[{k}]]x{v}" for k, v in sorted(shorthand.items())),
              file=sys.stderr)
        for i, new_stem in sorted(resolved.items()):
            print(f"  RESOLVE [[{i}]] -> [[{new_stem}]]", file=sys.stderr)
        for i, reason in refusals:
            print(f"  REFUSED [[{i}]] — {reason}", file=sys.stderr)
        if refusals:
            # Where, so hand-resolution is cheap. This is the path the peer actually took.
            refused_ids = {i for i, _ in refusals}
            for rel, lineno, i in result.get("shorthand_sites", []):
                if i in refused_ids:
                    print(f"    [[{i}]] {rel}:{lineno}", file=sys.stderr)
        if not resolved and not refusals:
            print("  (pass --resolve-shorthand to attempt resolution)", file=sys.stderr)
    if "--apply" not in argv:
        print(f"plan: {len(result['entries'])} entries, {len(result['work'])} work dirs")
        for old, new in sorted(result["entries"].items()):
            print(f"  {old}.md -> {new}.md")
        for old, new in sorted(result["work"].items()):
            print(f"  {old}/ -> {new}/")
        return 0
    summary = apply(root, result)
    print(f"renamed {summary['entries_renamed']} entries, "
          f"{summary['work_renamed']} work dirs, "
          f"rewrote {summary['files_rewritten']} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
