---
name: synthesize
description: Refreshes the knowledge-wiki overview — first reports the deterministic un-synthesized-scope signal (entries added since the last synthesis, plus broken overview wikilinks) so the caller decides IF resynthesis is warranted; if so, drafts a theme-grouped `overview.md` (narratives + `[[NNN-type-slug]]` wikilinks) and, behind a confirmation gate, writes it and bumps the synthesis watermark. Use after `minerva:promote` adds knowledge entries and `overview.md` hasn't been refreshed, when the overview is missing or has broken wikilinks, when the user wants a theme-grouped summary across `.minerva/knowledge/`, or when they invoke `minerva:synthesize`. The overview is advisory (never CI-gated); only the mechanical link-rot signal is deterministic.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
  - Write
  - Edit
---

Build or refresh the knowledge-wiki **synthesis layer** — a theme-grouped
`.minerva/knowledge/overview.md` that reads *across* entries to surface themes, the way
Karpathy's LLM-wiki keeps concept/overview pages over raw sources. This skill is
**read-mostly with a gated write**: it reports a deterministic signal, lets *you* decide
IF synthesis is warranted, and writes `overview.md` only after you confirm.

> This skill **changes a file** (`overview.md`) when you choose to synthesize. It is not
> read-only. The overview's content is **advisory** — only ever a navigation aid,
> never a CI-gated artifact (knowledge 013).

## Target

The `.minerva/knowledge/` corpus of the **current working tree**, resolved from
`git rev-parse --show-toplevel` — the same per-branch semantics as the unit-021 CI
drift gate, `minerva:lint`, and `minerva:lint-fix`. `overview.md` is a **separate file**
that does not match the entry regex, so the frozen detector (`scripts/knowledge_lint.py`)
and the fixer (`scripts/knowledge_fix.py`) never touch it.

## Step 1 — Read the deterministic signal

Run the importable status helper (it never writes):

```bash
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); SCRIPTS_ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)/scripts"; KNOWLEDGE="$(git rev-parse --show-toplevel)/.minerva/knowledge"; python3 -c "import sys, json; sys.path.insert(0, '${PLUGIN_SCRIPTS:-$SCRIPTS_ROOT}'); from synthesis_status import synthesis_status; print(json.dumps(synthesis_status('$KNOWLEDGE'), indent=2))"
```

**Script resolution:** `PLUGIN_SCRIPTS` uses `find -L` (follow symlinks) to locate `scripts/` in the local plugin install (`~/.claude/plugins/minerva` → symlink to the development checkout) first, then in the versioned plugin cache. The `-L` flag is required because the local install path is a symlink; without it, `find` stops at the symlink without descending. `SCRIPTS_ROOT` via `--git-common-dir` is a last-resort fallback that only works inside the agent-marketplace repo itself — it resolves to the wrong path in any other project. `--show-toplevel` still resolves to the current working tree's root, so the knowledge corpus is the worktree-local `.minerva/knowledge/` (correct per-branch semantics).

**Failure fallback:** If the command exits non-zero for any reason (Python unavailable,
`synthesis_status` module missing, permission error), treat the result as if it were
`{"unsynthesized": [], "link_rot": []}` — a no-op signal. Report the error and stop at
Step 2 with "no-op: signal unavailable." Do not retry; do not stall.

The JSON reports:

- `synthesis_watermark` — the max entry NNN the current `overview.md` reflects (`-1` if
  there is no overview yet, or it carries no `synthesis-watermark` comment);
- `corpus_max_nnn` — the highest entry NNN in the corpus;
- `unsynthesized` — entry NNNs added since the last synthesis (`NNN > watermark`);
- `link_rot` — any `[[NNN-type-slug]]` wikilink in the existing `overview.md` that no
  longer resolves to a live entry (a fence-aware scan — fenced example links are not
  flagged, knowledge 023).

## Step 2 — Decide IF to (re)synthesize (your call)

Present the signal to the user, then **judge whether synthesis is warranted**:

- **No overview yet** (`synthesis_watermark == -1`, `overview_exists` false) and the
  corpus has a meaningful number of entries → synthesizing the first overview is
  warranted.
- **Several un-synthesized entries** accumulated (`unsynthesized` is non-trivial) → a
  refresh is warranted.
- **Little or no new scope** (`unsynthesized` empty or just one minor entry) → say so
  and **stop**; re-synthesizing churns the file for no navigational gain.
- **`link_rot` present** → a refresh is warranted *regardless* of the count, to repair
  the dead links.

The watermark is a **new-scope-only floor**: it counts *added* entries, not in-place
`## Related` / banner / body edits to already-synthesized entries. If you know the
corpus was substantially re-shaped in place since the last synthesis (e.g. a
supersession rewired several `## Related` blocks), weigh that by judgment too — the
signal will not show it.

If you decide **not** to synthesize, report the signal and the reason, and stop here.

## Step 3 — Draft the theme-grouped overview

If you decide to synthesize, read the entries (`unsynthesized` first, plus the existing
overview for continuity) and draft `overview.md`:

- a `# Knowledge overview` H1 and the `<!-- synthesis-watermark: NNN -->` comment, where
  `NNN` is `corpus_max_nnn` (zero-padded to 3 digits) at synthesis time;
- one `## <Theme>` section per cross-cutting theme, each a short narrative that links
  the relevant entries as `[[NNN-type-slug]]` **full-stem** wikilinks (there is no bare
  `[[NNN]]` form). Author links **outside** code fences so they count as real edges
  (knowledge 023);
- a `## Limitations` section stating that the watermark is a new-scope-only floor
  (it attests synthesis **intent**, not body **content** — a watermark at corpus-max
  with a stale body is not detectable), and that new entries promoted after this
  synthesis will show as `unsynthesized` until the next refresh.

Every `[[NNN-type-slug]]` you write must resolve to a live entry. Confirm **by
inspection** that each link's NNN (and ideally its full stem, to keep navigation honest)
matches a real entry filename in `.minerva/knowledge/` before you gate — the Step-1
helper reads the *committed* `overview.md`, so it can only confirm `link_rot` is empty
*after* the write, not validate an un-written draft.

## Step 4 — Gate, then write

Show the drafted `overview.md` to the user and **wait for explicit confirmation** before
writing. (When invoked by an autonomous orchestrator, its adjudication mechanism
provides this confirmation.) On confirmation, `Write` the file to `$ROOT/.minerva/knowledge/overview.md` and
report the new watermark and the themes.

## Advisory, not gated

Overview content and its link-rot are deliberately advisory, never CI-gated — the
frozen detector/fixer cannot see this file. Broken overview wikilinks surface via
the Step-1 signal and are repaired at the next synthesis.
