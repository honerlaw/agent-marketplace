---
name: using-minerva
description: Use when starting work in a project that uses minerva (a `.minerva/` directory exists at the project root, or the user has invoked any `minerva:` skill in this session), or when the user describes starting / continuing / finishing a meaningful unit of work — features, refactors, investigations, spikes. Explains when to invoke each minerva skill and gives common scenarios. Skip for routine bugfixes, trivial edits, and one-shot Q&A.
---

# Using minerva

minerva is the durable-record discipline for software work in this project: **artifacts get promoted, not just accumulated** — past-tense knowledge items become `.minerva/knowledge/` entries, proposals get rewritten to describe what shipped, and raw scratchpads are archived.

The heuristic: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep. If no, summarize and discard.

## Detecting a minerva project

You're in a minerva project if any of these are true:

- A `.minerva/` directory exists at the project root.
- The user invoked any `minerva:` skill earlier in the session.
- `CLAUDE.md`, `AGENTS.md`, or similar has a `## minerva` Routing section pointing at `.minerva/`.

If none are true, the project isn't using minerva; don't reach for these skills unsolicited. If the user is clearly starting durable work that would benefit, suggest `minerva:init` as the entry point.

## Skill decision matrix

<!-- Source of truth: each row's skill text comes from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too (unless self-referencing this skill). -->

| Situation | Skill |
|---|---|
| First time using minerva in this project | `minerva:init` |
| Exploring a fuzzy idea before committing — not yet sure whether, or what, to build | `minerva:explore` (divergent, writes nothing; hands off to `minerva:propose` once a direction is chosen) |
| Starting a new unit of work (feature, refactor, investigation, spike) — you know what you want to build | `minerva:propose` |
| Resuming work on an existing unit | `minerva:work` (or `minerva:work <slug>` to target a specific unit) |
| The plan still holds — keep going | (no skill — continue work normally) |
| Reality has diverged from the plan in a load-bearing way | `minerva:replan` |
| Just drafted a plan and want to stress-test it before approving | `minerva:grill-plan` (auto-invoked by `minerva:propose` and `minerva:replan`; usable standalone on any drafted plan) |
| Want an independent multi-agent verdict on a decision or drafted artifact — agents argue it out rather than interviewing you | `minerva:round-table` (delegated to by `minerva:propose-ship-auto` for its panel decisions; usable standalone, default quorum 2/3) |
| Approved a proposal but want to tweak it before coding starts | `minerva:replan` (pre-work amendment mode) |
| Just hit something that's clearly a durable decision, mid-work | `minerva:promote "<short description>"` |
| Want to audit shipped code against the proposal | `minerva:review` |
| Implementation is done — finalize the record | `minerva:promote` (no argument) |
| Ready to commit, open a PR, watch CI, and merge | `minerva:ship` |
| PR merged — tidy up the worktree and branch | `minerva:cleanup` |
| Something is broken — investigate a live incident or a dev bug end-to-end | `minerva:debug` |
| Health-check the `.minerva/knowledge/` wiki (index drift, broken links, orphans, contradictions, stale claims) | `minerva:lint` (read-only — reports; repairs by hand or the gated path) |
| Apply the mechanical wiki fixes `minerva:lint` reported (stale/misfiled catalog lines, missing reciprocals) | `minerva:lint-fix` (mutating — gated; deterministic fixes only) |
| Migrate an existing project's `followups.md` backlog into GitHub issues, triaging each item for whether it is still relevant | `minerva:backfill-followups` |
| Corpus still has `NNN-` filenames and should move to date ids | `minerva:migrate-fix` (mutating — gated; `minerva:migrate` reports whether it is needed) |
| On the **default branch**, build a theme-grouped overview of the knowledge corpus | `minerva:synthesize` (read-mostly; `minerva:cleanup` runs it during reconciliation) |
| A one-time check when adopting minerva on an already-populated, pre-conventions `.minerva/knowledge/` corpus — assess what's non-conforming (legacy filenames, missing index/overview, entries without cross-refs) and what to run to migrate it (a shape audit, not a recurring health-check) | `minerva:migrate` (read-only — reports a migration checklist; renames + cross-ref authoring are judgment calls done by hand) |
| Run the whole lifecycle end-to-end from scratch | `minerva:propose-ship` |
| Run the whole lifecycle end-to-end without human gates (consensus panels — delegated to `minerva:round-table` — replace decisions; small low-risk decisions skip the panel via a fail-closed skip predicate) | `minerva:propose-ship-auto` |
| Run the whole lifecycle end-to-end quickly for a small, low-risk change (small UI fix, bug fix) — the main model decides each point directly instead of a panel, escalating to the user only when it genuinely can't decide | `minerva:propose-ship-quick` |
| Run the whole lifecycle end-to-end for a **medium** change (a multi-file refactor, a feature with 2-3 plausible designs) — the main model decides each point but dispatches one reviewer at the high-signal gates: scope, approach, and "is it really done" | `minerva:propose-ship-balanced` |

The skills cover the full lifecycle. Most of the time you stay in `minerva:work` and don't touch the others.

### Explicit work-unit targeting

Every lifecycle skill accepts an optional slug or path argument to disambiguate when context is unclear:

```
minerva:work 005-add-payments
minerva:replan 005-add-payments
minerva:promote 005-add-payments
minerva:review 005-add-payments
minerva:ship 005-add-payments
minerva:cleanup 005-add-payments
```

When omitted, the skill infers the target from current-session chat history, then falls back to the most-recently-modified work unit across both `.minerva/work/` and `.minerva/worktrees/`. If multiple recent units exist and the choice is ambiguous, the skill lists them and asks.

## Canonical lifecycle order

```
minerva:init                              # one-time: scaffold + agent-file Routing + .gitignore for worktrees
minerva:propose                           # design + branch + worktree + proposal.md (all writes inside the worktree)
minerva:work                              # enter the existing worktree and implement
   ↺ minerva:replan when scope shifts    # appends to replan.md (inside the worktree)
minerva:review                            # audit shipped code vs. proposal + run code quality review
   ↺ minerva:replan if review finds drift
minerva:promote                           # promote knowledge, rewrite proposal, archive scratchpad
   ↺ minerva:review → minerva:promote    # cycle if review surfaces new durable knowledge
minerva:ship                              # push the work-unit branch → PR → CI watch (polled) → auto-merge
minerva:cleanup                           # remove merged worktree + local branch (runs from the parent repo)
```

Worktree ownership: **`minerva:propose` creates** the branch + worktree and enters it. Every downstream lifecycle skill (`work`, `replan`, `review`, `promote`, `ship`) enters the existing worktree on invocation if the session is not already in it. `minerva:cleanup` is the only skill that stays outside — it removes worktrees, so it must run from the parent repo.

Review runs **before** promote so review-derived scratchpad notes flow through the promote partition. Re-cycle review/promote as many times as the work requires.

## Going deeper

`references/guide.md` holds, verbatim: **The persistence hierarchy (quick reference)** — which tier (scratchpad / work-unit docs / knowledge / reference) holds what and for how long; **Common scenarios** — worked walkthroughs mapping situations to skill sequences; and **Working in a minerva project without invoking skills** — the floor discipline when no skill fires. Read it whenever routing stays ambiguous after the decision matrix, or before advising on where a record belongs.

## Anti-patterns — when NOT to use minerva

Skip the workflow entirely for:

- **Trivial edits** — typo fixes, renames, single-line tweaks.
- **Routine bugfixes** — straightforward bugs with no architectural implications.
- **One-shot Q&A**.
- **Exploratory reads** — understanding code without changing it.
- **Quick refactors** — small, mechanical changes contained within a function or file.

The ceremony only pays off when the work is substantial enough that future readers will need the context. Don't impose it on work that ships in a single commit.

When a scenario here names a minerva skill as the next step, invoke it yourself
via the `Skill` tool (with any argument shown); only suggest the command when
the decision is the user's.
