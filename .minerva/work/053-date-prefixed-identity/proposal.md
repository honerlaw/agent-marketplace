# Proposal: date-prefixed identity for knowledge entries and work units

**Status**: Approved
**Date**: 2026-08-09

## Goal

Replace minerva's sequential `NNN` prefix with a date prefix across both namespaces:
`.minerva/knowledge/NNN-type-slug.md` → `YYYY-MM-DD-type-slug.md`, and
`.minerva/work/NNN-slug/` → `.minerva/work/YYYY-MM-DD-slug/`. Identity is the **full
stem**; dates are free to repeat and are never checked for uniqueness. A new
`minerva:migrate-fix` skill performs the historical rename, deriving each date from git.

## Why

`NNN` is a scarce, globally-ordered resource, so allocating it correctly is a
distributed-consensus problem — which is why `knowledge_next_nnn.py` exists at all,
scanning `git log --all --diff-filter=A` across local and remote branches with an
optional `--fetch`. That machinery buys nothing the slug doesn't already provide, and it
fails in the worst possible direction: two branches picking the same `NNN` produce two
*different* filenames, so git merges both cleanly and the duplicate ships silently
(knowledge `055`). PR #51 measured the result — 63 collisions across 629 entries,
838 refused back-links.

A date prefix is not allocated, so there is nothing to coordinate. And because identity
collapses into the path, an identical-stem collision becomes a git add/add conflict:
loud where it used to be silent.

## Approach

### 1. Dual-accepting grammar (never a false clean)

Every entry/wikilink/banner/catalog regex accepts `(?:\d{4}-\d{2}-\d{2})|(?:\d{3,})`.
The shape regex is **not sufficient on its own** — `2026-13-45` matches it — so conformance
in `migration_status` additionally validates the date arm with `datetime.date.fromisoformat`.
Without that, criterion 5 is unachievable and migrate's shape check silently weakens.
A non-conforming filename is invisible to *every* wiki tool at once (knowledge `026`), and
one consumer corpus of ~629 entries will not migrate at the same time as this repo, so a
date-only regex would silently blind the whole toolchain. Precedent: knowledge `001`.

The same alternation extends to the **prose globs** that drive bulk scans, which are easy
to miss because they are not in `ENTRY_RE`:

- `cleanup/SKILL.md:19` — "scan all `.minerva/worktrees/NNN-*/` directories"
- `ship/references/protocol.md:9` — "scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/`"
- `propose/references/on-approval.md:11` — the duplicate-slug check's path arms
  (its `git branch --list "*-<slug>"` arm is already slug-anchored and date-safe)

Without these, the *first* work unit created under the new convention is invisible to
`cleanup`'s bulk scan and `ship`'s auto-detection.

### 2. Full-stem identity

Re-key `knowledge_lint.py` and `knowledge_edits.py` from leading-token to full-stem
identity, mirroring what `knowledge_fix.py` already does since PR #51. The
duplicate-leading-token check and its quarantine retire: under dates they would report
every same-day pair as an error *and* exclude those entries from all per-entry checks,
recreating knowledge `054`'s blind spot at scale.

`knowledge_edits.py::add_supersede_banner`'s idempotency guard moves from
`ln.endswith(f"{nnn} -->")` to a full-stem match; the marker becomes
`<!-- superseded-by: <stem> -->`.

### 3. Ordering

Replace every `int()` cast with a normalized composite key — `(0, nnn.zfill(width))` for
legacy, `(1, date)` for dated, where `width = max(len(t) for t in legacy_tokens)` computed
per corpus (never a hardcoded 3 — a 4-digit corpus would silently reintroduce the bug).
**Not** plain lexicographic: `knowledge_lint.py:71`
documents that `int()` was chosen precisely because `"1000" < "999"` lexically and the
allocator widens past 999. Affected: `~270`, `~282`, `~285`, `~306`, `~310`, `~313`.

### 4. Watermarks removed outright

Both `<!-- index-watermark: NNN -->` and `<!-- synthesis-watermark: NNN -->` comment lines
are deleted, not reformatted. `knowledge_fix.py::plan_index:237` stops emitting the
comment; `WATERMARK_RE` and `SYNTH_WATERMARK_RE` are deleted; the "no watermark comment"
and "watermark above max NNN" findings retire. State is per-record: un-catalogued iff the
entry has no catalog line; un-synthesized iff its stem is not wikilinked from
`overview.md`. This finishes knowledge `053`, which fixed `index-watermark`'s comparison
but left `synthesis_status.py:102`'s `int(n) > watermark` floor intact — a live instance
of the same bug. `migrate-fix` strips both comments, so no separate template migration.

### 5. Collision guard is structural

`knowledge_next_nnn.py` and propose's three-source NNN scan are deleted. The replacement
is not another check — it is the path. Two branches producing an identical stem produce
the *same path*, which is an add/add conflict git refuses to merge. Pinned by a test that
creates two branches in a scratch repo and asserts the merge conflicts (a git-subprocess
test, unlike the suite's pure-Python assertions — `knowledge_next_nnn.py` already sets
that precedent).

**Residual exposure, stated:** same `(type, slug)` on *different* dates yields different
paths and merges cleanly. That is a duplicate-*slug* condition, unchanged from today —
the allocator only ever guarded numbers. No regression; out of scope.

### 6. Wikilink rewrite — the largest edit, and it must be fence-aware

532 `[[NNN-type-slug]]` occurrences across entry bodies, `index.md` and `overview.md` must
be retargeted. `knowledge_fix.py` keys on stems but has no rename or bulk-rewrite
capability, so this is new code.

Mechanism: `migrate-fix` builds one **stem → stem map** from the rename plan, then
rewrites `[[old-stem]]` → `[[new-stem]]` wherever it appears. The rewrite **must import
the span model from `scripts/knowledge_spans.py`** rather than re-deriving it (knowledge
`019`, `021`), and must be **fence-aware** — a wikilink inside a fenced example is
documentation, not an edge, and editing it corrupts the doc. Knowledge `023` states the
rule and `028` records it being violated a third time; `037` requires importing the
shared fence regex. A link whose target is not in the map is left untouched and reported,
never guessed at.

### 7. `minerva:migrate-fix` — a new skill

Not a mode on `minerva:migrate`, preserving the read-only/applier split that knowledge
`020` establishes for `lint`/`lint-fix` and that `026`/`027` document for migrate.
Registered across all four catalog surfaces — noting that knowledge `038` supersedes
`034` on the fourth: it is `pages/index.md` (the MkDocs source), not `site/index.html`,
which is now gitignored build output.

It computes the **full target-stem set up front** and refuses the entire batch on any
collision **before** any `git mv`.

**Date derivation** is the **oldest** add-commit for the path:

```
git log --follow --diff-filter=A --reverse --format=%cs -- <path> | head -1
```

`--follow` because `9f40272` renamed `.minerva/work/005-work-in-git-worktree/` to `008-…`
via `git mv`; without it a renamed path resolves to its rename commit, not its creation.
`--reverse | head -1`, *not* `-1`: git returns reverse-chronological order by default, so
a bare `-1` yields the **newest** add event, which is wrong for any path added more than
once (a delete-then-re-add, or a directory whose files landed across several commits).
For a **work-unit directory** the path is anchored on `<dir>/proposal.md`, not the
directory pathspec, so a unit whose files landed across multiple commits still resolves to
its creation date.

This yields the **landing-commit date**. Under squash-merge (this repo's history has zero
merge commits) that is the ship date; `ship/references/protocol.md:165` prefers `--squash`
but falls back to `--merge` then `--rebase`, and consumer repos may differ, so under those
fallbacks it is the original commit date. Known imprecision, deliberately accepted: dates
carry no identity or ordering weight beyond sort.

**Filename date vs body `**Date**:` may diverge, and that is tolerated.** Entry `001`
carries `**Date**: 2026-05-18` but landed on `2026-05-19`; after migration its filename
reads `2026-05-19-…`. The filename records when the entry *landed*; the body field records
when it was *authored*. `migrate-fix` never rewrites the body field to match — doing so
would destroy authored metadata in favour of a derived value, which is exactly the
inversion knowledge `058` warns against.

**Context fields:** the 56 `**Context**: .minerva/work/NNN-slug` fields (one in each of 56
entries) are rewritten via an explicit old→new dirname **lookup map**, never by assuming an
entry shares its work unit's date — an entry promoted in a later PR legitimately differs.

### 8. `propose` AND `promote` allocation procedures are rewritten, not patched

`propose/references/on-approval.md` steps 3–8 are a *procedure* built around allocating a
number: scan three sources, compute max+1, name the branch and worktree from it. Deleting
the allocator means rewriting those steps to "take today's date", not editing a glob. The
duplicate-slug check (step 2) survives and gains the date alternation on its path arms.

**`minerva:promote` is the bigger one, and is easy to miss.** It is the skill that names
every *new* knowledge entry, and it points at the allocator in four places:
`promote/SKILL.md:36` and `:42`, `promote/references/wiki-maintenance.md:66` (a full shell
invocation), and `promote/references/modes.md:24` and `:43`. All become "the entry takes
today's date".

The trap: `tests/test_promote_invariant.py:234` pins this with
`assert "knowledge_next_nnn.py" in _promote_prose()` — a bare string-presence check. Delete
the script and leave promote's prose alone and **that test still passes** while promote
instructs a call to a file that no longer exists. `pytest` green (criterion 1) cannot catch
it. The assertion is inverted to pin the new state: the allocator must be *absent* from
promote's prose, and the prose must instruct date-stamping.

### 9. Branches exempt

Historical branches keep `NNN-slug`; only newly created branches take the date form
(`git worktree add -b YYYY-MM-DD-slug .minerva/worktrees/YYYY-MM-DD-slug`). This is not
A2's tradeoff: `cleanup`'s merge detection keys on the *literal* branch name
(`git rev-parse --verify`, `gh pr list --head`, `git branch --merged | grep`), and
merged-PR head refs are immutable GitHub state. Work-unit *directories* have no external
referent, so migrating them is safe where migrating branches is not.

### 10. Prose sweep, enumerated by grep

Not by a prior count: root `CLAUDE.md`, the Routing/`CLAUDE.md` template `minerva:init`
writes into consumer repos, `plugins/minerva/README.md`, `init/references/steps.md`,
`cleanup/references/reconciliation.md`, and every skill file matching the convention.

### 11. Knowledge

Supersede `026`, `027`, `055`; amend `054`.

## Success criteria

1. `pytest` green, with any new test module appended to CI's enumerated list (knowledge `035`).
2. `knowledge_lint.py` reports zero errors on this repo's migrated corpus.
3. `knowledge_lint.py` reports zero *new* errors on an unmigrated (all-`NNN`) fixture corpus — proving dual-acceptance and no false clean.
4. A same-day fixture pair (two entries sharing a date, differing in slug) produces **no** duplicate finding and is **not** quarantined from per-entry checks.
5. A fixture stem `2026-13-45-pattern-x.md` is still classified non-conforming by `migration_status`.
6. The two-branch identical-stem merge test asserts a real add/add conflict.
7. Composite ordering test: a corpus mixing `999-`, `1000-` and dated entries sorts deterministically and correctly.
8. This repo's 56 entries and ~52 work dirs are renamed, and `grep -rE '\[\[[0-9]{3,}-' --include='*.md' .` returns hits **only** inside fenced code examples and inside superseded entries' own historical prose (i.e. text recounting an old number, not a live link). Every live wikilink resolves.
9. A fenced `[[NNN-…]]` example in a test fixture is **byte-identical** after `migrate-fix` runs — the fence-awareness guarantee.
10. `minerva:migrate-fix` exists and is registered on all four catalog surfaces (including `pages/index.md` per knowledge `038`); `minerva:migrate` remains read-only (its `allowed-tools` still omits Edit/Write).
11. `migrate-fix` refuses a fixture batch containing a target-stem collision **without performing any `git mv`** — verified by asserting the tree is unchanged after the refusal.
12. A dated work-unit fixture (`.minerva/work/2026-08-09-example/`) is detected by `cleanup`'s bulk scan and `ship`'s mtime scan — the proposal's own named worst case.
13. A newly created work unit gets a date-named branch and worktree; existing `NNN-slug` branches still resolve for merge detection.
14. `grep -rn 'NNN' plugins/minerva/ README.md CLAUDE.md` returns only intentional references (superseded-entry prose, legacy-form documentation), no stale instructions.
15. Knowledge `026`, `027`, `055` carry supersession banners; `054` is amended.
15b. The banner marker is written as `<!-- superseded-by: <full-stem> -->`, and
    `add_supersede_banner` is idempotent on it — running it twice against two *same-day*
    entries adds two distinct banners, not one (the old `ln.endswith(f"{nnn} -->")` guard
    false-no-ops here).
15c. `knowledge_next_nnn.py` is deleted, and no skill prose anywhere references it —
    `grep -rn 'knowledge_next_nnn' plugins/ tests/` returns only the inverted invariant test.
16. No `int()` cast remains on a prefix token; no watermark comment remains in `index.md`/`overview.md`.

## Open Questions

- Whether consumer repos should get a one-shot migration announcement; out of scope here.
