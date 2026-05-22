# minerva plugin

Durable record discipline for software work. Encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — concrete, past-tense knowledge (decisions made, bugs fixed, patterns discovered) becomes `.minerva/knowledge/` entries; proposals get rewritten to describe what shipped; raw scratchpads are archived.

## The hierarchy

| Tier | Files | When read |
|------|-------|-----------|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` | Loaded for every new piece of work |
| Searchable-on-demand | `.minerva/work/NNN-slug/proposal.md`, `.minerva/work/NNN-slug/replan.md`, `followups.md` | Grep when relevant |
| Ephemeral | `.minerva/work/NNN-slug/scratchpad.md` | Gone after `minerva:promote` |

The heuristic for what to keep: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep it. If no, summarize and discard.

## Skills

<!-- Source of truth: each row's text is excerpted from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too. -->

| Skill | Description |
|-------|-------------|
| `minerva:init` | One-time scaffolding for a project. Creates `.minerva/work/` and `.minerva/knowledge/` with `.gitkeep`s, checks `.gitignore`, warns about any legacy `.minerva/decisions/`, adds a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md), and offers to commit. Idempotent. |
| `minerva:propose ["description"]` | Brainstorm-style proposal authoring for a new work unit. Infers intent from context or asks; derives slug from the agreed goal; scans local + remote branches and `.minerva/work/` to avoid NNN collisions; writes `.minerva/work/NNN-<slug>/proposal.md` (with a Success criteria section); self-reviews the written file; then gates on user re-read. |
| `minerva:replan` | Same brainstorm flow, but appends a dated divergence entry to `.minerva/work/NNN-<slug>/replan.md`. Used for mid-work divergence (auto-triggered by `minerva:work`) and for pre-work proposal amendments. |
| `minerva:grill-plan` | Interviews the user relentlessly about a drafted plan, one question at a time, with the LLM's recommended answer leading each question, until shared understanding is reached. Invoked by `minerva:propose` after approach selection and by `minerva:replan` after the new-plan brainstorm; also usable standalone on any drafted plan. |
| `minerva:work` | Enter implementation mode in an isolated git worktree. Reads the proposal + replans, surfaces any unresolved Open Questions, maintains `scratchpad.md`, auto-triggers `minerva:replan` on load-bearing divergence, and verifies Success criteria before suggesting promote. |
| `minerva:promote [item]` | No-arg: end-of-work full pass (promote concrete past-tense knowledge → `.minerva/knowledge/`, rewrite proposal to match reality, archive scratchpad, dispose of TODOs explicitly via `followups.md` / new proposal / discard). With arg: single-item mid-work promote. Idempotent. |
| `minerva:review` | Audit the implementation against the proposal (and `.minerva/knowledge/` invariants) by reviewing the local diff. Runs `code-review:code-review` when a PR exists, else does a structured inline check using the same finding format. Triage state persisted to scratchpad for resume. Runs **before** `minerva:promote` so findings flow through the partition. |
| `minerva:ship` | Close the lifecycle: commit outstanding work to a branch (creating one if on the default branch), open a PR titled and described from `proposal.md`, watch CI via ScheduleWakeup polling (no agent blocking), bounded auto-fix loop (3 iterations), enable auto-merge when permissions allow. Bare mode for routine work outside a tracked unit. |
| `minerva:cleanup [slug]` | Remove `.minerva/worktrees/NNN-slug/` directories whose branches have been merged into the default branch, and prune the matching local branches. Conservative — never touches unmerged work without explicit override. Idempotent. |
| `minerva:propose-ship ["description"]` | Thin conductor that runs the full lifecycle end-to-end (propose → work → review → promote → ship → cleanup). Refuses to start if in-flight work would collide; advances out of the work phase on explicit user trigger words; gates on user confirmation before shipping; runs cleanup only after the PR actually merges (ScheduleWakeup-polled for up to ~1 hour while auto-merge is pending). |
| `minerva:propose-ship-auto ["description"]` | Same lifecycle as `minerva:propose-ship`, but replaces each human-facing decision gate with a 3-agent Proponent/Skeptic/Arbiter consensus panel of fresh-context subagents. Human input is only a fallback when the panel fails to agree after one revision round. Strategic decisions need 3/3 consensus; tactical decisions need 2/3; operational decisions (commit messages, PR bodies) bypass the panel. Bails to manual mode on consensus failures (≥3 user escalations or 2 of 3 propose-phase escalations). |
| `minerva:triage` | Investigate a bug end-to-end — first locate the failing component (in a live system or in dev code), then trace through the code to root-cause and recommend a fix. Project-agnostic; loads project-specific operational facts from `.minerva/reference/` at runtime and cross-references past learnings in `.minerva/knowledge/`. Stays read-only against any system other users depend on; mutations require explicit per-turn confirmation. Triggers on both live-incident framing ("users are reporting", "the cron didn't run") and dev-bug framing ("this test fails", "TypeError"). |
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
    │   └── NNN-<type>-<slug>.md        (written by minerva:promote)
    ├── work/
    │   └── NNN-<slug>/
    │       ├── proposal.md             (written by minerva:propose, rewritten by minerva:promote)
    │       ├── replan.md               (written by minerva:replan when needed)
    │       ├── scratchpad.md           (live during minerva:work, replaced by a one-line marker at minerva:promote)
    │       ├── followups.md            (optional — TODOs that survived minerva:promote's TODO gate)
    │       └── archive/
    │           └── scratchpad.md       (raw scratchpad moved here by minerva:promote)
    └── worktrees/                      (gitignored — created by minerva:work, removed by minerva:cleanup)
        └── NNN-<slug>/                 (isolated git worktree per work unit)
```

Numbering for `.minerva/work/` and `.minerva/knowledge/` is independent — each layer grows at its own pace. `minerva:propose` scans `.minerva/work/`, local branches, AND remote branches matching `NNN-*` so parallel work in worktrees doesn't produce NNN collisions. Knowledge files link back to their work unit via a `Context:` field that remains a stable pointer even after `minerva:cleanup` removes the worktree.

## Setup

This plugin is pure markdown — no Python dependencies, no Playwright. The standard installer handles registration:

```bash
./install.sh minerva
```

Restart Claude Code (or run `/reload-plugins`). Then in any project you want to track with minerva, run `minerva:init` once to scaffold the directory layout and wire the Routing section.
