# minerva plugin

Durable record discipline for software work. Encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — significant scratchpad items become `.minerva/decisions/` entries; proposals get rewritten to describe what shipped; raw scratchpads are archived.

## The hierarchy

| Tier | Files | When read |
|------|-------|-----------|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/decisions/` | Loaded for every new piece of work |
| Searchable-on-demand | `.minerva/work/NNN-slug/proposal.md`, `.minerva/work/NNN-slug/replan.md` | Grep when relevant |
| Ephemeral | `.minerva/work/NNN-slug/scratchpad.md` | Gone after `/promote` |

The heuristic for what to keep: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep it. If no, summarize and discard.

## Commands

| Skill | Description |
|-------|-------------|
| `/init` | One-time scaffolding for a project. Creates `.minerva/work/` and `.minerva/decisions/` with `.gitkeep`s, checks `.gitignore` for exclusions, and adds a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md). Idempotent. |
| `/propose <slug>` | Brainstorm-style proposal authoring for a new work unit. Asks clarifying questions, proposes approaches, writes `.minerva/work/NNN-slug/proposal.md` once approved. |
| `/replan [target]` | Same brainstorm flow, but appends a dated divergence entry to `.minerva/work/NNN-slug/replan.md` for an in-flight work unit. |
| `/work [target]` | Enter implementation mode. Reads the proposal + replans, maintains `scratchpad.md`, auto-triggers `/replan` on load-bearing divergence. |
| `/promote [item]` | No-arg: end-of-work full pass (promote significant items → `.minerva/decisions/`, rewrite proposal to match reality, archive scratchpad). With arg: single-item mid-work promote. Idempotent. |

## Skills

| Skill | Description |
|-------|-------------|
| `minerva:using-minerva` | Context-aware orientation skill — explains when to invoke each command, gives common scenarios, and lists anti-patterns. Auto-triggers in projects with a `.minerva/` directory, or when the user describes starting/continuing/finishing a meaningful unit of work. |

## Typical flow

```text
/init                              # one-time: scaffold .minerva/ + agent-file Routing section
/propose add-payments              # .minerva/work/001-add-payments/ + proposal.md
/work                              # implementation begins, scratchpad live
   → /replan triggers on real     # .minerva/work/001-add-payments/replan.md appended
/promote                           # end-of-work: decisions/, proposal rewritten, scratchpad archived
```

## File layout produced

```
<project-root>/
├── CLAUDE.md (or AGENTS.md)            (gets a "## minerva" Routing section)
└── .minerva/
    ├── decisions/
    │   └── NNN-<slug>.md               (written by /promote)
    └── work/
        └── NNN-<slug>/
            ├── proposal.md             (written by /propose, rewritten by /promote)
            ├── replan.md               (written by /replan when needed)
            ├── scratchpad.md           (live during /work, replaced by a one-line marker at /promote)
            └── archive/
                └── scratchpad.md       (raw scratchpad moved here by /promote)
```

Numbering for `.minerva/work/` and `.minerva/decisions/` is independent — each layer grows at its own pace. Decision files link back to their work unit via a `Context:` field in the body.

## Setup

This plugin is pure markdown — no Python dependencies, no Playwright. The standard installer handles registration:

```bash
./install.sh minerva
```

Restart Claude Code (or run `/reload-plugins`). Then in any project you want to track with minerva, run `/init` once to scaffold the directory layout and wire the Routing section.
