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

from knowledge_lint import ENTRY_RE, WIKILINK_STEM_RE, is_date_id  # noqa: E402
from knowledge_spans import FENCE_RE  # noqa: E402

WORK_DIR_RE = re.compile(r"^(\d{3,})-(.+)$")
CONTEXT_PATH_RE = re.compile(r"(\.minerva/work/)([^\s/`)\]]+)")


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


def plan(repo_root, knowledge_dir=None, work_dir=None):
    """Compute the full rename plan without touching anything.

    Returns {entries: {old_stem: new_stem}, work: {old_name: new_name},
             undated: [...], collisions: [(target, [sources])]}.

    `undated` holds paths git could not date — an uncommitted file, or a corpus with no
    history. They are reported and SKIPPED rather than guessed at: inventing a date would
    silently mint an id that does not correspond to anything.
    """
    root = Path(repo_root)
    kd = Path(knowledge_dir) if knowledge_dir else root / ".minerva" / "knowledge"
    wd = Path(work_dir) if work_dir else root / ".minerva" / "work"

    entries, work, undated = {}, {}, []

    if kd.is_dir():
        for p in sorted(kd.glob("*.md")):
            m = ENTRY_RE.match(p.name)
            if not m or is_date_id(m.group(1)):
                continue  # not an entry, or already migrated
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
                continue
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

    return {"entries": entries, "work": work,
            "undated": undated, "collisions": collisions}


def rewrite_links(text, stem_map, dir_map=None):
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
        line = WIKILINK_STEM_RE.sub(
            lambda m: f"[[{stem_map.get(m.group(1), m.group(1))}]]", line)
        line = re.sub(
            r"(<!-- superseded-by: )([^\s]+)( -->)",
            lambda m: m.group(1) + stem_map.get(m.group(2), m.group(2)) + m.group(3),
            line)
        if dir_map:
            line = CONTEXT_PATH_RE.sub(
                lambda m: m.group(1) + dir_map.get(m.group(2), m.group(2)), line)
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
    for p in sorted(root.rglob("*.md")):
        # Test the path RELATIVE to the repo root, never the absolute one. minerva runs
        # its own work inside `.minerva/worktrees/<unit>/`, so when this executes in a
        # worktree the absolute path of EVERY file contains that segment — an absolute
        # test silently skips the entire corpus and reports "0 files rewritten" while
        # the renames succeed, leaving every link dangling.
        rel = p.relative_to(root)
        if ".git" in rel.parts or rel.parts[:2] == (".minerva", "worktrees"):
            continue
        try:
            text = p.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        new = rewrite_links(text, stem_map, dir_map)
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
            "files_rewritten": touched, "undated": plan_result["undated"]}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path(_git(["rev-parse", "--show-toplevel"], Path.cwd()).strip())
    result = plan(root)
    if result["collisions"]:
        for target, sources in result["collisions"]:
            print(f"COLLISION {target} <- {', '.join(sources)}", file=sys.stderr)
        return 1
    for path in result["undated"]:
        print(f"UNDATED (skipped) {path}", file=sys.stderr)
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
