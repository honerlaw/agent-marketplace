# init — step protocols 1–5

## Step 1 — scaffold `.minerva/`

If `.minerva/` doesn't exist, create:

- `.minerva/work/`
- `.minerva/work/.gitkeep` (empty file, so git tracks the empty directory)
- `.minerva/knowledge/`
- `.minerva/knowledge/index.md` — the knowledge catalog, written with the canonical
  skeleton below (watermark `000`). A non-empty `index.md` already makes the
  directory tracked by git, so **only** create `.minerva/knowledge/.gitkeep` when
  `index.md` is absent (and never both).
- `.minerva/reference/` — the present-tense operational-doc tier.
- `.minerva/reference/.gitkeep` (empty file, so git tracks the empty directory)

**Canonical `index.md` skeleton** — `minerva:init` and `minerva:promote` are the two
creators of this file; both emit this **exact** content so they cannot diverge:

```markdown
# Knowledge index
<!-- index-watermark: 000 -->

## Decisions

## Bugs

## Patterns

## Constraints
```

The `index-watermark` is the highest knowledge-entry NNN the catalog reflects
(`000` for a fresh scaffold); it is a content freshness signal preferred over file
mtime (mtime is unreliable across git checkouts and worktrees).

If `.minerva/` already exists, skip whichever pieces are already in place. Don't
overwrite an existing `index.md`, `.gitkeep`, or `.minerva/reference/`.

### Step 1b — index backfill offer (idempotent mode)

If `.minerva/knowledge/` already holds entries (`NNN-<type>-<slug>.md` files) but
`index.md` is missing or empty, **offer** to backfill it:

> "`.minerva/knowledge/` has N entries but no populated `index.md`. Generate the
> catalog from the existing entries now?"

On acceptance, write `index.md` from the canonical skeleton, add one
`- [[NNN-type-slug]] — <≤15-word summary>` line per entry under its Type section
(title from the entry H1, summary condensed from its Finding), and set the watermark
to the max NNN on disk. **Cross-reference backfill** (adding `## Related` blocks
across existing entries) is a separate, judgment-heavy pass — offer it only if the
user asks; it is not part of the index backfill.

## Step 2 — gitignore check

(Skip in a non-git repo.)

Read `.gitignore` at the project root and any nested `.gitignore` files that would apply to `.minerva/`. The check has two parts:

**Part A — flag patterns that would exclude committed dirs.** Look for patterns that would exclude `.minerva` or `.minerva/` or `.*` (the common dotfile-catchall). `.minerva/knowledge/` and `.minerva/work/` are intended to be committed.

- If a matching pattern is found, report the offending file path, line number, and the offending pattern. **Do not auto-edit** `.gitignore` to remove user-authored patterns — that file is user territory. Suggest the user remove or narrow the pattern.
- If none found, report `gitignore ✓ (committed dirs)`.

**Part B — install `.minerva/worktrees/` if missing.** Every worktree created by `minerva:propose` lives under `.minerva/worktrees/` and must be ignored on the default branch (the ignore entry must exist before any worktree is created, or git status breaks inside every worktree). Init installs this entry up front so propose doesn't have to modify `.gitignore` from inside a worktree later.

- If `.gitignore` does not already contain a line matching `.minerva/worktrees/` (exact match, or a parent pattern like `.minerva/` — both effectively ignore the path), append `.minerva/worktrees/` to the end of the project-root `.gitignore` (create the file if it doesn't exist). Report `gitignore: added .minerva/worktrees/`.
- If already present, report `gitignore ✓ (worktrees ignored)`.

Unlike Part A, this entry is appended automatically — it's part of init's idempotent scaffold, not user territory.

## Step 3 — agent-file detection + Routing

Check for the canonical agent files at the project root, in this order: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`.

- For **each file that exists**, add a `## minerva` Routing section if one isn't already present. If the section is already present, check it for **staleness** (see "Refreshing a stale Routing section" below): if stale, offer a gated refresh; if current, leave the file alone and report `<file> ✓`.
- If **none of the three exist**, ask the user which to create:
  - `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or **Other** (the user supplies a filename).
  - For **Other**, the user provides a filename; the same Routing section is appended to that file (created empty first). The user can flesh out the rest later.
  - Wait for the answer before creating anything.

### Routing section content

Use this exact template (verbatim, with the appended blank line at the end for readability):

```markdown
## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/overview.md` — theme-grouped synthesis of everything known. Read first to orient (absent until `minerva:synthesize` first runs — fall back to the index).
- `.minerva/knowledge/index.md` — the catalog, one line per entry. Look up specifics here; drill into entries via their `[[NNN-type-slug]]` links only when a theme bears on your task.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill (via the `Skill` tool) for the full methodology.
```

Append the Routing section at the end of the file (don't try to find a "right" spot — end is fine and is easy to detect on re-runs).

### Detecting existing Routing section

A re-run is detected by checking the file for a line matching the exact heading `## minerva`, followed within the **next 6 lines** by either the literal substring `.minerva/knowledge/` or `.minerva/decisions/` (the old name, kept for projects initialized before the rename). Both signals are required — the heading alone is too generic.

If the heading appears multiple times in the file, only the first occurrence is checked. (Unlikely in practice; if a user has multiple `## minerva` headings, the file is hand-managed and `init` should not touch it — surface a warning instead of writing.)

### Refreshing a stale Routing section

Detection (above) deliberately checks *presence, not exact match*, so hand-edited
sections survive re-runs. But that also means a section written from an **older
template** is never revisited. The refresh offer closes that gap — **gated, never
automatic**:

1. **Staleness check (generic, disjunctive).** For each `.minerva/...` path that appears
   as a bullet in the **current template above** (today: `.minerva/knowledge/overview.md`,
   `.minerva/knowledge/index.md`, `.minerva/reference/`, `.minerva/work/`), check whether
   the detected section contains that substring. If **any** is missing, the section is
   a refresh candidate. (Derive the markers from the template-of-record above, never from a hardcoded list.)
2. **Gate.** Show the full before/after diff of the section and ask:
   > "Your `## minerva` section doesn't match the current template — it may be from an
   > older template, or **you may have customized it**. Refreshing replaces the whole
   > section, so anything custom inside it will be removed. Refresh `<file>`?"
   Proceed only on explicit confirmation; on decline, leave the file alone and report
   `<file> ✓ (older template kept)`.
3. **Replacement boundary.** Replace from the `## minerva` heading line up to but **not**
   including the next line matching `^## ` (exactly two hashes followed by a space — a
   `### ` subsection does **not** terminate the section), or to EOF if no such line
   exists. Worked example — in the file below, only the marked span is replaced:

   ```
   ## minerva          ← replacement starts here
   ...section body, including any ### subsections...
                       ← replacement ends here (line above the next ## heading)
   ## Contributing     ← untouched
   ```

Splice-preserving refresh (keeping unrecognized custom lines while updating the
canonical bullets) is future hardening — v1 replaces the whole section behind the gate,
and the diff makes the cost visible before anything is written.

## Step 4 — commit offer

(Skip in a non-git repo.)

If any files were newly created **or refreshed** in steps 1–3 (a Routing-section refresh
modifies an existing agent file — it must be offered for commit too, or a refresh-only
run leaves the change dangling uncommitted), offer to commit them:

> "Created/updated `.minerva/{work,knowledge,reference}` (incl. `knowledge/index.md`) + Routing section in `<files>`. Stage and commit now?"

If the user agrees:
```
git add .minerva/ <agent files modified>
git commit -m "chore: scaffold minerva and routing section"
```

Use specific paths only — never `-A` or `.`. If the user declines, leave the changes in the working tree.

## Step 5 — report

Print a status block:

```
.minerva/ layout       ✓ created (or: already present)
.minerva/knowledge/index.md  ✓ scaffolded (or: ✓ backfilled from N entries; or: ✓ already present)
.minerva/reference/    ✓ created (or: ✓ already present)
.gitignore             ✓ ok       (or: skipped — not a git repo; or: ⚠ <pattern at file:line> would exclude .minerva/)
.minerva/worktrees/    ✓ added to .gitignore (or: ✓ already ignored; or: — not a git repo)
CLAUDE.md              ✓ Routing section added (or: ✓ already present; or: ✓ Routing section refreshed; or: ✓ older template kept; or: — not present)
AGENTS.md              ✓ Routing section added (or: ✓ already present; or: ✓ Routing section refreshed; or: ✓ older template kept; or: — not present)
GEMINI.md              ✓ Routing section added (or: ✓ already present; or: ✓ Routing section refreshed; or: ✓ older template kept; or: — not present)
flat layout            — none detected (or: ⚠ work/ and/or decisions/ at root — see message above)
legacy decisions/      — none detected (or: ⚠ .minerva/decisions/ — see message above)
commit                 ✓ committed (or: declined; or: — nothing to commit)
```

Suggest `minerva:propose` as the next step if no work units exist yet.

