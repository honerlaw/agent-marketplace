# init — step protocols 1–5

## Step 1 — scaffold `.minerva/`

If `.minerva/` doesn't exist, create:

- `.minerva/work/`
- `.minerva/work/.gitkeep` (empty file, so git tracks the empty directory)
- `.minerva/knowledge/`
- `.minerva/knowledge/.gitkeep` (empty file, so git tracks the empty directory)
- `.minerva/reference/` — the present-tense operational-doc tier.
- `.minerva/reference/.gitkeep` (empty file, so git tracks the empty directory)

**No `index.md`, no `overview.md`.** The knowledge catalog is derived on read from each
entry's `**Theme**` and `**Summary**` lines (the Routing section's one-liner, or
`knowledge_catalog.py`), so there is no shared file to scaffold, maintain or reconcile.
Never create either file. A corpus that still has them is a pre-3.0 corpus:
`minerva:migrate` reports it and `minerva:migrate-fix` folds them into the entries.

If `.minerva/` already exists, skip whichever pieces are already in place. Don't
overwrite an existing `.gitkeep` or `.minerva/reference/`.

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

With explicit `--host claude`, `--host codex`, or `--host both`, create missing
`CLAUDE.md`, `AGENTS.md`, or both respectively and append the Routing section.
Do not replace existing content. Without the selector preserve the detection
and choice behavior below; when files exist but the active host's instruction
file is absent, offer creation of that missing file and wait for the answer.
An existing customized Routing section still uses the gated refresh below.

- For **each file that exists**, add a `## minerva` Routing section if one isn't already present. If the section is already present, check it for **staleness** (see "Refreshing a stale Routing section" below): if stale, offer a gated refresh; if current, leave the file alone and report `<file> ✓`.
- If **none of the three exist**, ask the user which to create:
  - `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or **Other** (the user supplies a filename).
  - For **Other**, the user provides a filename; the same Routing section is appended to that file (created empty first). The user can flesh out the rest later.
  - Wait for the answer before creating anything.

### Routing section content

Use this exact template (verbatim, with the appended blank line at the end for readability). It is fenced with `~~~` because it contains a ` ``` ` block of its own:

~~~markdown
## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/` — write-once entries (decisions, bugs, patterns, constraints, references), each tagged with a `**Theme**` and a one-line `**Summary**`. Orient by listing the catalog — one `theme | entry | summary` line per entry, grouped by theme, with `(superseded)` on an entry a newer one has retired — then open only the entries whose theme bears on your task:

  ```sh
  find .minerva/knowledge -name '[0-9]*.md' -exec awk 'function p(){if(f!=""){n=f;sub(/.*\//,"",n);sub(/\.md$/,"",n);N[++c]=n;T[n]=(t==""?"(unthemed)":t);S[n]=s;if(b)X[n]=1};f=FILENAME;t="";s="";q=0;r=0;h=0;b=0} function id(x){sub(/.*\//,"",x);sub(/-[a-z]+-.*/,"",x);return x} function tgt(x){sub(/^- \[\[/,"",x);sub(/\]\].*/,"",x);return x} FNR==1{p()} {sub(/\r$/,"")} /^[ \t]*(```|~~~)/{q=!q;next} q{next} /^## /{h=1;r=($0=="## Related")} !h&&/^<!-- superseded-by: /{b=1} /^\*\*Theme\*\*:/&&t==""{sub(/^\*\*Theme\*\*:[ \t]*/,"");sub(/[ \t]+$/,"");t=$0} /^\*\*Summary\*\*:/&&s==""{sub(/^\*\*Summary\*\*:[ \t]*/,"");sub(/[ \t]+$/,"");s=$0} r&&/^- \[\[[^]]*\]\][ \t]*(—|–|-)[ \t]*/&&!/\]\].*\[\[/{l=tolower($0);sub(/^- \[\[[^]]*\]\][ \t]*(—|–|-)[ \t]*/,"",l);x=tgt($0);if(l~/^superseded by([ \t]*(:|;|,|—|–|-)|[ \t]*$)/)b=1;else if(l~/^supersedes([ \t]*(:|;|,|—|–|-)|[ \t]*$)/&&id(f)>=id(x))Y[x]=1} END{p();for(i=1;i<=c;i++){n=N[i];print T[n]" | "n" | "S[n]((n in X)||(n in Y)?" (superseded)":"")}}' {} + | sort
  ```

  Links between entries are forward-only `## Related` lines; find what links *to* an entry with `grep -l '\[\[<entry>\]\]' .minerva/knowledge/*.md`.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/<date-slug>/`. Load the installed `minerva:using-minerva` skill for the full methodology using your host's skill loader. In Claude Code use `/minerva:using-minerva`; in Codex select `$minerva:using-minerva`. Follow the loaded plugin's runtime contract for tools and installed paths.
~~~

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
   in the **current template above** (today: `.minerva/knowledge/`,
   `find .minerva/knowledge -name` — the catalog one-liner — `.minerva/reference/`,
   `.minerva/work/`), check whether the detected section contains that substring. A
   pre-3.0 section routes to `overview.md` / `index.md` and lacks the catalog one-liner, so it
   is always a candidate — which is how an upgraded consumer learns its routing points at
   files that no longer exist. If **any** is missing, the section is
   a refresh candidate. (Derive the markers from the template-of-record above, never from a hardcoded list.)
   Also offer this gated refresh when the routing still requires the Claude-only
   `Skill` tool or omits the current runtime-contract guidance. Preserve custom
   routing on decline.
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

> "Created/updated `.minerva/{work,knowledge,reference}` + Routing section in `<files>`. Stage and commit now?"

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
