# minerva plugin — design

**Date**: 2026-05-18
**Status**: Approved for implementation planning

## Motivation

The `~/Downloads/IMG_3776.HEIC` writeup describes a persistence hierarchy for software work:

- **Always-read** — `CLAUDE.md`, `decisions/`. Loaded into context for every new piece of work.
- **Searchable-on-demand** — old `proposal.md` and `replan.md` files under `work/NNN-slug/`. Not in context by default; grep when relevant.
- **Ephemeral** — `scratchpad.md`. Gone after the summarization step at feature completion.

The load-bearing operations are **promotion** (significant scratchpad items become durable `decisions/` entries) and **summarization** (proposal.md gets rewritten so it describes what shipped, not just what was planned). The heuristic: *would a new engineer (or new agent) joining the project in a year benefit from reading this?*

`minerva` encodes this discipline as four slash commands and the file layout they operate on.

## Scope

Applies to **any meaningful unit of work** — features, bug investigations, refactors, spikes — not just new functionality.

Out of scope:

- Routine bugfixes and small refactors that don't warrant a proposal.
- Cross-project memory or knowledge management.
- Automation of decision quality (the heuristic remains a judgment call surfaced to the user).

## File layout

```
<project-root>/
├── CLAUDE.md
├── decisions/
│   └── NNN-<slug>.md
└── work/
    └── NNN-<slug>/
        ├── proposal.md
        ├── replan.md          (created lazily by /replan)
        ├── scratchpad.md      (one-line "Summarized at..." marker after /promote)
        └── archive/
            └── scratchpad.md  (raw scratchpad moved here by /promote)
```

Numbering for `work/` and `decisions/` is **independent**. Each layer grows at its own pace; a work unit may produce zero, one, or many decisions. The link from decision to origin lives in the decision's `Context:` field, not in the number.

## Commands

Four commands, plain verbs, scoped to the `minerva` plugin namespace.

### `/propose <slug>`

Brainstorm-style proposal authoring for a **new** work unit. Mirrors the superpowers `brainstorming` skill's flow.

Behavior:

1. Normalize slug: lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.
2. Refuse if `work/NNN-<slug>/` already exists for that slug — direct the user to `/replan` instead.
3. Explore project context (read CLAUDE.md, `decisions/`, recent `work/` entries) so questions are informed.
4. Ask clarifying questions **one at a time** — purpose, constraints, success criteria.
5. Propose 2–3 approaches with tradeoffs and a recommendation. Iterate.
6. Present the design in sections, getting approval per section.
7. Once approved, allocate the next NNN under `work/` (3-digit, max+1), create `work/NNN-<slug>/`, and write:
    - `proposal.md` — the approved design
    - `scratchpad.md` — empty body with the ephemeral-warning header

Output: path to the new work directory.

### `/replan [target]`

Same brainstorming flow as `/propose`, but for **capturing divergence** in an active work unit.

Behavior:

1. Resolve the target work directory:
    - With argument: `work/<target>/` (substring match against existing entries is fine).
    - Without argument: most-recently-modified `work/NNN-*/`.
2. Read the existing `proposal.md`, any prior `replan.md` entries, and the current `scratchpad.md` so the brainstorming flow is grounded in what actually happened.
3. Frame the brainstorm around three pieces: original plan → what changed → new plan.
4. Run questions / approach proposals / sectioned design, same pattern as `/propose`.
5. Append a dated entry to `replan.md` (create the file with a `# Replan log: <slug>` header if it doesn't exist).

Output: path to the replan file and the title of the appended entry.

### `/work [target]`

Enter implementation mode for a work unit. This is a setup-and-protocol command — the slash command primes Claude with the work unit's context and the working protocols; the user then collaborates in normal conversation while Claude follows them.

Behavior:

1. Resolve target (most-recently-modified by default; argument override).
2. Read `proposal.md` and **all** `replan.md` entries. If both exist, the latest replan supersedes earlier plans where they conflict.
3. Smart resume: skim `scratchpad.md` to figure out where work left off. Skim git status / recent commits for the same. Summarize the resumption point to the user in one paragraph before doing anything.
4. While working:
    - Log significant moves to `scratchpad.md` as they happen — what was tried, what worked, surprises. Not a transcript; only items a future-self might want.
    - Continuously check whether the approach being taken still matches the plan (proposal + active replans).
5. **Auto-trigger the `/replan` protocol** when reality diverges from the plan in a load-bearing way:
    - A core assumption is wrong, the approach itself is changing, or scope is shifting.
    - Routine implementation choices (which library, small refactors, edge-case handling) do **not** trigger.
    - On trigger: pause implementation, follow the `/replan` protocol inline (Claude reads `plugins/minerva/commands/replan.md` and executes it — questions, brainstorm, append the dated replan entry), then resume `/work` with the updated plan in context. There is no separate tool invocation — the slash-command body is just instructions Claude follows.
6. When implementation appears complete (tests pass, the proposal's success criteria are met), surface `/promote` as the next step.

Output: a one-paragraph resumption summary, then normal implementation collaboration.

### `/promote [item]`

Extract durable decisions and finalize the work unit. Two modes based on whether an argument is supplied.

#### No argument — end-of-work full pass

1. Resolve target (most-recently-modified).
2. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
3. Propose a three-way partition of `scratchpad.md` entries:
    - **PROMOTE** → durable architectural/design choices, surprising constraints, tradeoffs worth recording.
    - **MERGE INTO PROPOSAL** → anything where the actual approach diverged from the original. The proposal's Approach section must end up describing what got built.
    - **DISCARD** → dead ends, momentary confusion, debugging digressions.
4. Show the partition to the user. Wait for confirmation or edits ("move 3 and 5 to discard").
5. On confirmation:
    - For each PROMOTE item: write `decisions/NNN-<slug>.md` (auto-increment NNN across the whole `decisions/` directory). Each entry stands alone.
    - Rewrite `proposal.md` so its Approach section describes reality. Don't preserve obsolete planning prose.
    - Move `scratchpad.md` to `work/<target>/archive/scratchpad.md`. Leave a one-line `scratchpad.md` saying `Summarized at /promote on YYYY-MM-DD — see archive/.` so future readers aren't confused by its absence.
6. Report: items promoted (with paths), whether the proposal was updated, scratchpad disposition.

#### With argument — mid-work single-item promote

`/promote "use postgres listen/notify for cache invalidation"`

1. Resolve target.
2. Read `scratchpad.md`. Locate the block matching the argument (substring or fuzzy match). If multiple candidates, list them and ask which.
3. If the matched block is already marked as promoted (see step 5), report the existing decision file path and stop.
4. Write the single `decisions/NNN-<slug>.md`.
5. In `scratchpad.md`, append `→ promoted to decisions/NNN-<slug>.md` on the matched block so end-of-work `/promote` won't re-promote it.

#### Idempotency

Both modes are safe to re-run:

- End-of-work pass: if `scratchpad.md` is already the one-line "Summarized at..." marker, exit early and report "already promoted."
- Single-item: if the matched scratchpad block already has the `→ promoted` marker, report the existing decision file and exit.
- Promoted decision files are never overwritten — auto-incremented NNN guarantees uniqueness, and the single-item mode never reaches the write step on a re-run.

### Decision entry template

Used by both promote modes.

```markdown
# <Short, declarative title — what was decided>

**Date**: YYYY-MM-DD
**Context**: work/NNN-<slug>

## Context
The situation that forced this choice. Constraints, prior state, or the
problem we hit. Enough that a reader cold to the project understands why
this was even a question.

## Decision
What we chose. Stated as a declarative.

## Consequences
What this implies going forward — invariants other code now relies on,
things future work has to honor, tradeoffs we accepted.
```

### Proposal template

Written by `/propose` from the brainstormed design.

```markdown
# Proposal: <slug>

**Date**: YYYY-MM-DD
**Status**: Draft

## Goal
What this work unit is trying to accomplish.

## Why
The motivation. Problem solved or opportunity captured.

## Approach
The planned approach. Rewritten by /promote to describe what shipped.

## Open Questions
- Things we don't know yet.
```

### Scratchpad template

```markdown
# Scratchpad: <slug>

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `decisions/`, `proposal.md` gets updated to match reality, and the raw
> scratchpad is archived.

```

### Replan entry template

Appended by `/replan` to `replan.md`.

```markdown
## YYYY-MM-DD — <short, declarative title>

**Original plan**: <one or two sentences>
**What changed**: <what was discovered, what broke, what assumption was wrong>
**New plan**: <one or two sentences>
```

## Plugin layout

```
plugins/minerva/
├── .claude-plugin/
│   └── plugin.json
├── README.md
└── commands/
    ├── propose.md
    ├── replan.md
    ├── work.md
    └── promote.md
```

`plugin.json`:

```json
{
  "name": "minerva",
  "description": "Durable record discipline for software work — promotion, not accumulation. Implements a persistence hierarchy of proposals, replans, scratchpads, and decisions.",
  "author": {
    "name": "Derek Honerlaw"
  }
}
```

Marketplace registration (`.claude-plugin/marketplace.json` at the repo root) adds an entry pointing at `./plugins/minerva`.

The existing `plugins/feature-cycle/` directory from the earlier iteration is removed; nothing else depended on it.

## Numbering rules

For both `work/` and `decisions/`:

1. Scan entries matching `NNN-*` where `NNN` is a 3-digit integer.
2. Pick `max + 1`, pad to 3 digits.
3. If the directory doesn't exist yet, create it and start at `001`.

Numbering is per-directory and **never shared across `work/` and `decisions/`** — they grow at independent rates.

## Behaviors that span commands

### Target resolution

`/replan`, `/work`, `/promote` all accept an optional target argument. Resolution order:

1. Exact directory match: `work/<arg>/`.
2. Substring match against existing `work/NNN-*/` entries; if exactly one match, use it; if multiple, list and prompt.
3. With no argument: pick the most-recently-modified `work/NNN-*/` by `mtime` of the directory.

If no `work/` directory exists, all three commands report "no work units found — run `/propose <slug>` first" and exit.

### Brainstorm flow shared by `/propose` and `/replan`

Both commands run the same interactive pattern (mirroring `superpowers:brainstorming`):

1. Explore project context first.
2. Ask clarifying questions one at a time (multiple-choice preferred, open-ended fine).
3. Propose 2–3 approaches with tradeoffs; recommend one.
4. Present the design in sections; get approval per section.
5. Once approved, write the file (proposal.md or replan.md entry).
6. Do **not** invoke any implementation skill from inside these commands. They terminate at the file write.

The difference is the file destination, the framing of questions (greenfield for `/propose`, divergence-shaped for `/replan`), and the context preloaded (none vs. existing proposal + scratchpad).

## Non-goals

- No init command. The first `/propose` creates `work/`; the first `/promote` creates `decisions/`. CLAUDE.md is the user's responsibility.
- No grep/search command. Standard tools (`grep -r work/`, `ls decisions/`) are sufficient and don't warrant wrapping.
- No automatic CLAUDE.md generation. The user writes their own constitution.
- No cross-work-unit reasoning. Each work unit is treated independently; cross-unit lessons land in `decisions/` and become part of the always-read layer.

## Risks and open considerations

- **`/work` auto-triggering `/replan` is a judgment call.** Calibration matters: too eager and the user resents the interruption; too lax and the methodology breaks. The threshold is "load-bearing divergence" — a changing assumption, approach, or scope, not a tactical choice. This will likely need refinement after real use.
- **Scratchpad signal-to-noise** depends on Claude maintaining discipline during `/work`. If the scratchpad becomes a transcript, `/promote` becomes slow and the heuristic gets harder to apply. The `/work` prompt must keep this explicit.
- **Substring target matching** could be ambiguous. The chosen behavior (list and prompt on multiple matches) is safe but adds a beat. Acceptable.
- **Idempotency of `/promote`** relies on the `→ promoted to decisions/...` marker in `scratchpad.md`. If a user manually edits the scratchpad to remove markers, re-running `/promote` could duplicate entries. Not worth defending against — it's a clear footgun.

## Implementation notes

- All four commands are pure-markdown slash commands; no Python scripts required. The financials plugin uses scripts for browser automation; minerva is text-and-files only.
- `/propose` and `/replan` rely on Claude's brainstorming behavior, not a separate scripted flow. The command body describes the protocol; Claude executes it interactively.
- `/work` does not run continuously; it primes the agent with context and protocols, then implementation happens in normal conversation. Claude is responsible for honoring the scratchpad-maintenance and divergence-detection protocols throughout.
- All file paths are project-relative (anchored at the current working directory), not plugin-install-relative.
