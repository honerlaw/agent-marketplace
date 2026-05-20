# minerva plugin

Durable record discipline for software work. Encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — concrete, past-tense knowledge (decisions made, bugs fixed, patterns discovered) becomes `.minerva/knowledge/` entries; proposals get rewritten to describe what shipped; raw scratchpads are archived.

## The hierarchy

| Tier | Files | When read |
|------|-------|-----------|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` | Loaded for every new piece of work |
| Searchable-on-demand | `.minerva/work/NNN-slug/proposal.md`, `.minerva/work/NNN-slug/replan.md` | Grep when relevant |
| Ephemeral | `.minerva/work/NNN-slug/scratchpad.md` | Gone after `minerva:promote` |

The heuristic for what to keep: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep it. If no, summarize and discard.

## Skills

| Skill | Description |
|-------|-------------|
| `minerva:init` | One-time scaffolding for a project. Creates `.minerva/work/` and `.minerva/knowledge/` with `.gitkeep`s, checks `.gitignore` for exclusions, and adds a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md). Idempotent. |
| `minerva:propose ["description"]` | Brainstorm-style proposal authoring for a new work unit. Infers intent from context or asks; derives slug from the agreed goal; writes `.minerva/work/NNN-slug/proposal.md` once approved. |
| `minerva:replan` | Same brainstorm flow, but appends a dated divergence entry to `.minerva/work/NNN-slug/replan.md` for the current (context-inferred) work unit. |
| `minerva:work` | Enter implementation mode. Reads the proposal + replans, maintains `scratchpad.md`, auto-triggers `minerva:replan` on load-bearing divergence. |
| `minerva:promote [item]` | No-arg: end-of-work full pass (promote concrete past-tense knowledge → `.minerva/knowledge/`, rewrite proposal to match reality, archive scratchpad). With arg: single-item mid-work promote. Idempotent. |
| `minerva:review` | Audit the implementation against the proposal (and `.minerva/knowledge/` invariants) by reviewing the branch-vs-default-branch diff, or the uncommitted diff if the working tree isn't clean. Interactive triage: fix / suggest / ignore. Runs after `minerva:work` and may cycle with `minerva:promote`. |
| `minerva:ship` | Close the lifecycle: commit outstanding work to a branch (creating one if on the default branch), open a PR titled and described from `proposal.md`, watch CI with a bounded auto-fix loop (3 iterations), and enable auto-merge when repo permissions allow. Falls back to bare mode for routine work outside a tracked unit. |
| `minerva:using-minerva` | Context-aware orientation skill — explains when to invoke each skill, gives common scenarios, and lists anti-patterns. Auto-triggers in projects with a `.minerva/` directory, or when the user describes starting/continuing/finishing a meaningful unit of work. |

## Typical flow

```text
minerva:init                              # one-time: scaffold .minerva/ + agent-file Routing section
minerva:propose "add payments flow"       # .minerva/work/001-add-payments-flow/ + proposal.md
minerva:work                              # implementation begins, scratchpad live
   → minerva:replan triggers on drift    # .minerva/work/001-add-payments-flow/replan.md appended
minerva:review                            # audit shipped code vs proposal (fix / suggest / ignore)
minerva:promote                           # end-of-work: knowledge/, proposal rewritten, scratchpad archived
   ↺ minerva:review → minerva:promote    # cycle as needed if review surfaces durable knowledge
minerva:ship                              # commit → branch → PR → CI watch + auto-fix → auto-merge
```

## File layout produced

```
<project-root>/
├── CLAUDE.md (or AGENTS.md)            (gets a "## minerva" Routing section)
└── .minerva/
    ├── knowledge/
    │   └── NNN-<type>-<slug>.md        (written by minerva:promote)
    └── work/
        └── NNN-<slug>/
            ├── proposal.md             (written by minerva:propose, rewritten by minerva:promote)
            ├── replan.md               (written by minerva:replan when needed)
            ├── scratchpad.md           (live during minerva:work, replaced by a one-line marker at minerva:promote)
            └── archive/
                └── scratchpad.md       (raw scratchpad moved here by minerva:promote)
```

Numbering for `.minerva/work/` and `.minerva/knowledge/` is independent — each layer grows at its own pace. Knowledge files link back to their work unit via a `Context:` field in the body.

## Setup

This plugin is pure markdown — no Python dependencies, no Playwright. The standard installer handles registration:

```bash
./install.sh minerva
```

Restart Claude Code (or run `/reload-plugins`). Then in any project you want to track with minerva, run `minerva:init` once to scaffold the directory layout and wire the Routing section.
