# minerva plugin

Durable record discipline for software work. Encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — concrete, past-tense knowledge (decisions made, bugs fixed, patterns discovered) becomes `.minerva/knowledge/` entries; proposals get rewritten to describe what shipped; raw scratchpads are archived.

📖 **[Documentation site](https://honerlaw.github.io/agent-marketplace/)** — the same material as a browsable site.

## The hierarchy

| Tier | Files | When read |
|------|-------|-----------|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` | Loaded for every new piece of work |
| Searchable-on-demand | `.minerva/work/<date-slug>/proposal.md`, `.minerva/work/<date-slug>/replan.md`, `followups.md`, plus open `minerva:followup` GitHub issues | Grep the files; `gh issue list --label "minerva:followup" --state open` for the rest |
| Ephemeral | `.minerva/work/<date-slug>/scratchpad.md` | Gone after `minerva:promote` |

The heuristic for what to keep: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep it. If no, summarize and discard.

## Skills

<!-- Source of truth: each row's text is excerpted from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too. -->

| Skill | Description |
|-------|-------------|
| `minerva:init` | One-time scaffolding for a project. Creates `.minerva/work/` and `.minerva/knowledge/` with `.gitkeep`s, checks `.gitignore`, warns about any legacy `.minerva/decisions/`, adds a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md), and offers to commit. Idempotent. |
| `minerva:explore` | Divergent, commitment-free brainstorming — the minerva analog of `superpowers:brainstorming`, the optional phase *before* `minerva:propose`. Turns a fuzzy idea into clarity through one-question-at-a-time dialogue, weighing multiple high-level directions; writes no file, allocates no work unit, creates no branch/worktree. May legitimately end in "don't build this" or "reframe"; on a chosen direction, hands off to `minerva:propose` (inline-arg) to design it. |
| `minerva:propose ["description"]` | Brainstorm-style proposal authoring for a new work unit. Infers intent from context or asks; derives slug from the agreed goal; checks local + remote branches and `.minerva/work/` for a duplicate slug; writes `.minerva/work/<date-slug>/proposal.md` (with a Success criteria section); self-reviews the written file; then gates on user re-read. |
| `minerva:replan` | Same brainstorm flow, but appends a dated divergence entry to `.minerva/work/<date-slug>/replan.md`. Used for mid-work divergence (auto-triggered by `minerva:work`) and for pre-work proposal amendments. |
| `minerva:grill-plan` | Interviews the user relentlessly about a drafted plan, one question at a time, with the LLM's recommended answer leading each question, until shared understanding is reached. Invoked by `minerva:propose` after approach selection and by `minerva:replan` after the new-plan brainstorm; also usable standalone on any drafted plan. |
| `minerva:round-table ["decision"]` | Convene a 3-agent Proponent/Skeptic/Arbiter consensus panel of fresh-context subagents over a decision or drafted artifact: accept votes are counted against a caller-specified quorum (default 2/3), with at most one revision round, then escalation to the user when consensus fails twice. A pure extraction of the panel protocol formerly inlined in `minerva:propose-ship-auto`, which now delegates its panel calls here; usable standalone for any decision. |
| `minerva:work` | Enter implementation mode in an isolated git worktree. Reads the proposal + replans, surfaces any unresolved Open Questions, maintains `scratchpad.md`, auto-triggers `minerva:replan` on load-bearing divergence, and verifies Success criteria before suggesting promote. |
| `minerva:promote [item]` | No-arg: end-of-work full pass (promote concrete past-tense knowledge → `.minerva/knowledge/`, rewrite proposal to match reality, archive scratchpad, dispose of TODOs explicitly — kept ones filed as prioritized GitHub issues where the repo can host them, else `followups.md`; or new proposal; or discard). With arg: single-item mid-work promote. Idempotent. |
| `minerva:review` | Audit the implementation against the proposal and knowledge invariants through an independent reviewer. Uses optional `code-review:code-review` for an OPEN PR when installed; otherwise reviews fetched PR or local diffs through the host adapter. Preserves finding format and triage state for resume. Runs before promote. |
| `minerva:ship` | Commit outstanding work, open or reuse a PR, observe CI through a tracked watcher, attempt at most 3 fixes, and enable auto-merge when permissions allow. Checkpointed scheduled re-entry is used only when available; otherwise reports pending with an exact manual resume prompt. Also supports bare shipping. |
| `minerva:cleanup [slug]` | Remove `.minerva/worktrees/<date-slug>/` directories whose branches have been merged into the default branch, and prune the matching local branches. Conservative — never touches unmerged work without explicit override. Idempotent. |
| `minerva:propose-ship ["description"]` | Thin conductor that runs the full lifecycle with user gates and collision checks. Runs cleanup only after the PR merges; merge waits retain a 12-retry / one-hour bound across supported scheduled or manual resumes. |
| `minerva:propose-ship-auto ["description"]` | Same lifecycle as `minerva:propose-ship`, with no scheduled human gates and for any size of change. Each decision gets the adjudication tier it earns, chosen per decision: the **main model alone** when a strict fail-closed predicate proves it small; **one fresh-context reviewer** by default (a Skeptic, or a Verifier at completion; a folded critique gets one fold-audit re-check); a **3-agent `minerva:round-table` panel** when the decision is ambiguous, high-blast-radius, changes an existing public interface (introducing a new one gets a reviewer), or is in tension with knowledge. Independent gates are dispatched together as waves. An unadjudicable critique, a failed fold-audit or a reviewer's evidenced "panel warranted" moves the decision up to a panel; a panel that fails quorum twice goes to the user. Divergence, replan and replan-vs-FIX are always panels; completion is always at least a Verifier. There is no up-front sizing and no recommendation to switch orchestrators. Halts at 3 user escalations. |
| `minerva:debug` | Investigate a bug end-to-end — gather evidence first, then diagnose root cause grounded in that evidence, and report with a mechanically-derived confidence score. Project-agnostic; loads project-specific operational facts from `.minerva/reference/` at runtime and cross-references past learnings in `.minerva/knowledge/`. Stays read-only against any system other users depend on; mutations require explicit per-turn confirmation. Triggers on both live-incident framing ("users are reporting", "the cron didn't run") and dev-bug framing ("this test fails", "TypeError"). |
| `minerva:lint` | Read-only health-check for the `.minerva/knowledge/` wiki. Runs the deterministic detector for mechanical defects (index drift, broken `## Related` links, missing reciprocals) and adds LLM-judged advisory findings (orphans, contradictions, stale/superseded claims), presenting everything in `minerva:review`'s finding format. Never edits files; it reports. Deterministic repairs are applied via `minerva:lint-fix`; judgment-call repairs by hand. |
| `minerva:lint-fix` | **Mutating** companion to `minerva:lint`. Behind a confirmation gate, applies the deterministically-repairable findings (stale catalog lines, wrong Type-section placement, missing reciprocal `## Related` links) via the unit-tested `scripts/knowledge_fix.py`. Never touches entry bodies; does not auto-fix judgment calls (missing catalog summaries, broken links, contradictions/staleness) — those it surfaces. |
| `minerva:synthesize` | Builds / refreshes the knowledge-wiki synthesis layer — a theme-grouped `overview.md` over `.minerva/knowledge/`. First reports a deterministic un-synthesized-scope signal (entries added since the last synthesis, via `scripts/synthesis_status.py`, plus any broken overview wikilinks) so the LLM decides IF there is enough new scope to (re)synthesize; if so, drafts theme narratives + `[[YYYY-MM-DD-type-slug]]` links and, behind a confirmation gate, writes `overview.md` and bumps the synthesis watermark. The overview is advisory (its content is never CI-gated); only the mechanical link-rot signal is deterministic. |
| `minerva:migrate` | Read-only **migration check** for adopting minerva on a pre-conventions `.minerva/knowledge/` corpus. Runs `scripts/migration_status.py` — the one signal that globs the *complement* of `ENTRY_RE` to inventory non-conforming files invisible to every other wiki tool (detector / fixer / synthesis), plus index/overview presence and entries lacking `## Related` cross-refs — and emits a migration checklist naming the skill that closes each gap (`minerva:init` backfill, `minerva:synthesize`, `minerva:lint`/`lint-fix`). A **shape** audit, not a health check; it mutates nothing — the rename it recommends is applied by `minerva:migrate-fix`. |
| `minerva:migrate-fix` | **Mutating** companion to `minerva:migrate`. Behind a confirmation gate, renames legacy `NNN-`prefixed entries and work units to date ids (`YYYY-MM-DD-type-slug`) via the unit-tested `scripts/knowledge_rename.py`, deriving each date from the git history of the path itself and retargeting every wikilink, supersession marker and `**Context**` path. Computes the whole target set first and refuses the entire batch if two entries would land on one name. Never renames git branches, and never rewrites an entry's body `**Date**` field. |
| `minerva:status` | Read-only **status check** for the whole workstream. Runs `scripts/workstream_status.py` — a pure reader that walks both `.minerva/work/` and every `.minerva/worktrees/*/`, dedupes by slug, and derives each unit's lifecycle stage (`draft` / `in-progress` / `promoted` / `shipped`) plus its phase progress, importing every predicate from `work_status` rather than restating it — then joins branch and PR state and renders three tables: active units with the **next lifecycle step** to run, a rollup, and knowledge-wiki health. Anchors on the PRIMARY checkout (`--git-common-dir`), not `--show-toplevel`, so it still sees every sibling unit when invoked from inside a worktree. Mutates nothing and advances nothing; it names the next skill and stops. |
| `minerva:using-minerva` | Context-aware orientation skill — explains when to invoke each skill, gives common scenarios, and lists anti-patterns. Auto-triggers in projects with a `.minerva/` directory, or when the user describes starting/continuing/finishing a meaningful unit of work. |

## Typical flow

```text
minerva:init                              # one-time: scaffold .minerva/ + agent-file Routing
minerva:propose "add payments flow"       # writes .minerva/work/001-add-payments-flow/proposal.md
minerva:work                              # creates .minerva/worktrees/001-add-payments-flow/, implementation begins
   ↺ minerva:replan when scope shifts
minerva:review                            # audit shipped code vs proposal (runs before promote)
   ↺ minerva:replan if review finds drift
minerva:promote                           # promote knowledge, rewrite proposal, archive scratchpad
   ↺ minerva:review → minerva:promote    # cycle as needed if review surfaces durable knowledge
minerva:ship                              # commit → branch → PR → CI watch (polled) → auto-merge
minerva:cleanup                           # remove the merged worktree + local branch
```

## File layout produced

```
<project-root>/
├── CLAUDE.md (or AGENTS.md)            (gets a "## minerva" Routing section)
└── .minerva/
    ├── knowledge/
    │   └── <YYYY-MM-DD>-<type>-<slug>.md        (written by minerva:promote)
    ├── work/
    │   └── <YYYY-MM-DD>-<slug>/
    │       ├── proposal.md             (written by minerva:propose, rewritten by minerva:promote)
    │       ├── replan.md               (written by minerva:replan when needed)
    │       ├── scratchpad.md           (live during minerva:work, replaced by a one-line marker at minerva:promote)
    │       ├── followups.md            (optional — kept TODOs, when the repo can't host GitHub issues)
    │       └── archive/
    │           └── scratchpad.md       (raw scratchpad moved here by minerva:promote)
    └── worktrees/                      (gitignored — created by minerva:work, removed by minerva:cleanup)
        └── <YYYY-MM-DD>-<slug>/        (isolated git worktree per work unit)
```

Both layers are named `<YYYY-MM-DD>-<slug>`, dated independently — a knowledge entry promoted in a later PR than its proposal legitimately carries a different date from its work unit. Nothing is allocated: a date is read off the clock, so parallel work never coordinates, and **several units or entries sharing a date is normal** because identity is the whole stem. `minerva:propose` checks only for a duplicate *slug*; a duplicate stem is the same path, so git conflicts on it rather than merging it silently. Knowledge files link back to their work unit via a `Context:` field that remains a stable pointer even after `minerva:cleanup` removes the worktree.

## Setup

Both hosts load the same Markdown skills and standard-library Python helpers.
Minerva requires Git, Python 3.11+, and a POSIX shell; no pip packages or Playwright
are required. PR workflows also need authenticated `gh` and permissions. Install
for one or both hosts:

```bash
./install.sh minerva --host both
```

Reload Claude Code with `/reload-plugins` and start a new Codex conversation.
Run `minerva:init --host both` in a consumer project to scaffold `.minerva/` and
append routing to `CLAUDE.md` and `AGENTS.md`, preserving existing content. A
customized existing routing section is refreshed only after an approved diff.

Read [compatibility and validation](COMPATIBILITY.md) for capability fallbacks,
durable resume state, and the required regression checks.

### Wire Codex manually

From the cloned repository, register the local marketplace and install Minerva:

```bash
codex plugin marketplace add /absolute/path/to/agent-marketplace
codex plugin add minerva@agent-marketplace
```

Start a new Codex app, CLI, or IDE conversation and select `$minerva:using-minerva` (or invoke a specific skill such as `$minerva:init`). In the consumer project, run `minerva:init --host both` once to create `.minerva/` and add shared `CLAUDE.md`/`AGENTS.md` routing. The repository installer performs these same registration commands with `./install.sh minerva --host codex` or `--host both`.
