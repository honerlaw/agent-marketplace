---
name: using-minerva
description: Use when starting work in a project that uses minerva (a `.minerva/` directory exists at the project root, or the user has invoked any `minerva:` skill in this session), or when the user describes starting / continuing / finishing a meaningful unit of work — features, refactors, investigations, spikes. Explains when to invoke each minerva skill and gives common scenarios. Skip for routine bugfixes, trivial edits, and one-shot Q&A.
---

# Using minerva

minerva is the durable-record discipline for software work in this project. It encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — concrete, past-tense knowledge items become `.minerva/knowledge/` entries, proposals get rewritten to describe what shipped, and raw scratchpads are archived.

The heuristic: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep. If no, summarize and discard.

## Detecting a minerva project

You're in a minerva project if any of these are true:

- A `.minerva/` directory exists at the project root.
- The user invoked any `minerva:` skill earlier in the session.
- `CLAUDE.md`, `AGENTS.md`, or similar has a `## minerva` Routing section pointing at `.minerva/`.

If none are true, the project isn't using minerva. Don't reach for these skills unsolicited — but if the user is clearly starting durable work that would benefit from the discipline, suggest `minerva:init` as the entry point (it scaffolds the directory and adds a Routing section to the agent file).

## Skill decision matrix

<!-- Source of truth: each row's skill text comes from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too (unless self-referencing this skill). -->

| Situation | Skill |
|---|---|
| First time using minerva in this project | `minerva:init` |
| Starting a new unit of work (feature, refactor, investigation, spike) | `minerva:propose` |
| Resuming work on an existing unit | `minerva:work` (or `minerva:work <slug>` to target a specific unit) |
| The plan still holds — keep going | (no skill — continue work normally) |
| Reality has diverged from the plan in a load-bearing way | `minerva:replan` |
| Just drafted a plan and want to stress-test it before approving | `minerva:grill-plan` (auto-invoked by `minerva:propose` and `minerva:replan`; usable standalone on any drafted plan) |
| Approved a proposal but want to tweak it before coding starts | `minerva:replan` (pre-work amendment mode) |
| Just hit something that's clearly a durable decision, mid-work | `minerva:promote "<short description>"` |
| Want to audit shipped code against the proposal | `minerva:review` |
| Implementation is done — finalize the record | `minerva:promote` (no argument) |
| Ready to commit, open a PR, watch CI, and merge | `minerva:ship` |
| PR merged — tidy up the worktree and branch | `minerva:cleanup` |
| Something is broken — investigate a live incident or a dev bug end-to-end | `minerva:debug` |
| Run the whole lifecycle end-to-end from scratch | `minerva:propose-ship` |
| Run the whole lifecycle end-to-end without human gates (consensus panels replace decisions; small low-risk decisions skip the panel via a fail-closed skip predicate) | `minerva:propose-ship-auto` |

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

## The persistence hierarchy (quick reference)

| Tier | Files | Read by Claude |
|---|---|---|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` (start from `index.md`, the catalog) | Every conversation in this project — decisions, bugs, patterns |
| Reference (read on demand) | `.minerva/reference/<topic>.md` | Present-tense operational docs — architecture, glossary, conventions: how the system works now |
| Searchable-on-demand | `.minerva/work/NNN-<slug>/proposal.md`, `.minerva/work/NNN-<slug>/replan.md`, `followups.md` if present | Grep when relevant |
| Ephemeral | `.minerva/work/NNN-<slug>/scratchpad.md` | Live during `minerva:work`, archived by `minerva:promote` |

The two LLM-owned wiki tiers differ in **time-shape** (see `.minerva/knowledge/011-decision-minerva-reference-tier.md`): `.minerva/knowledge/` is atomic, past-tense, append-only "what we learned"; `.minerva/reference/` is thematic, present-tense, replace-on-change "how the system works now."

**The knowledge wiki is navigable, not a flat pile.** `.minerva/knowledge/index.md` is the maintained catalog — one line per entry (link + one-line summary), grouped by type, carrying an `index-watermark` of the highest entry it reflects. Entries cross-reference each other in a trailing `## Related` block using `[[NNN-type-slug]]` wiki-links keyed on the stable NNN, with a closed relationship vocabulary (`builds on` / `supersedes` / `superseded by` / `contradicts` / `see also`); superseded entries keep a `<!-- superseded-by: NNN -->` banner rather than being deleted. `minerva:promote` maintains the index and these cross-references (including the reciprocal links on neighbor entries) through its existing confirmation gate. Inline `[[…]]` mentions in entry prose remain valid and are not migrated — the `## Related` block is the structured, machine-maintained surface; inline mentions are free prose.

When in doubt about whether something belongs in a knowledge file vs. a scratchpad note, apply the new-engineer-in-a-year heuristic above.

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

## Common scenarios

**"This is a fresh project — let's start using minerva."**
→ `minerva:init`. Scaffolds `.minerva/work/` and `.minerva/knowledge/`, checks `.gitignore`, warns about any legacy `.minerva/decisions/`, adds a Routing section to the agent file, and offers to commit.

**"Let's add a payments flow."**
→ `minerva:propose "add payments flow"` (or just `minerva:propose` — the skill infers your intent from context). Brainstorm the design through the skill's flow. After you approve every section, propose creates the `NNN-add-payments` branch and worktree at `.minerva/worktrees/NNN-add-payments/`, enters the worktree, writes `proposal.md` + `scratchpad.md` inside it, and commits the initial docs. Don't start coding until the proposal is written, self-reviewed, and you've approved the file directly.

**"Where were we on the payments thing?"**
→ `minerva:work` (or `minerva:work 005-add-payments` to be explicit). The skill enters the existing worktree at `.minerva/worktrees/005-add-payments/`, reads `proposal.md`, the latest `replan.md`, surfaces any unresolved Open Questions, and skims `scratchpad.md` to figure out where to pick up.

**"It turns out we can't use Stripe's hosted checkout — we need our own form."**
→ Load-bearing divergence. Inside `minerva:work`, the protocol auto-triggers `minerva:replan`. Outside `minerva:work` (coming back from a tangent), invoke `minerva:replan` directly.

**"I want to tweak the proposal before we start."**
→ `minerva:replan` works here too — it's the same divergence flow, framed for a pre-work tweak. The replan entry's "What changed" is "user requested adjustment before implementation."

**"We just decided the queue retry policy should be exponential backoff capped at 5 minutes."**
→ Mid-work durable decision. Run `minerva:promote "exponential backoff capped at 5 minutes for queue retries"`. The scratchpad entry gets marked so the end-of-work pass doesn't re-promote it.

**"Before I open the PR, let's check the code actually matches what we designed."**
→ `minerva:review`. The skill reads the proposal + replans, audits the branch-vs-default diff (or the uncommitted diff if the tree is dirty), runs `code-review:code-review` (or a structured inline check if no PR exists yet), and walks you through each finding. Triage state is persisted to scratchpad so re-runs pre-fill prior dispositions. Run review **before** promote so review-derived notes flow through promote's partition.

**"Tests pass, the feature works, success criteria are met."**
→ `minerva:promote` (no argument). Partitions the scratchpad into promote / merge / discard / TODO. TODOs aren't silently dropped — you decide per-item whether to keep them in `followups.md`, seed a new proposal, or discard.

**"OK, ship it — commit, PR, watch CI, and merge if it goes green."**
→ `minerva:ship`. Commits outstanding changes (creating a branch if you're on the default), opens a PR titled and described from `proposal.md`, schedules a ScheduleWakeup-based CI watch (~270s intervals, no blocking), runs a bounded auto-fix loop on CI failures, and enables auto-merge when permissions allow.

**"PR is merged — let's clean up."**
→ `minerva:cleanup`. Removes worktrees whose branches have been merged into the default branch, and prunes the local branches. Idempotent and conservative — never touches unmerged work without explicit override.

## Anti-patterns — when NOT to use minerva

Skip the workflow entirely for:

- **Trivial edits** — typo fixes, renames, single-line tweaks.
- **Routine bugfixes** — straightforward bugs with no architectural implications.
- **One-shot Q&A** — "what does this function do?", "why is this slow?".
- **Exploratory reads** — scanning code to understand it without changing anything.
- **Quick refactors** — small, mechanical changes contained within a function or file.

The ceremony only pays off when the work is substantial enough that future readers will need the context. Don't impose it on work that ships in a single commit.

## Working in a minerva project without invoking skills

Even when you don't run a `minerva:` skill this session, respect the hierarchy:

- Treat `CLAUDE.md` / `AGENTS.md` and `.minerva/knowledge/` as authoritative — read them when starting work in the project. These contain decisions, fixed bugs, and discovered patterns, not just architecture.
- Grep `.minerva/work/` when you need historical context for a feature. Active work lives at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`; shipped work lives at `.minerva/work/<NNN-slug>/` on the default branch.
- Don't create `scratchpad.md` files directly outside of `minerva:work`. If you need scratch space, use a TodoWrite or notes in conversation instead.
- If a project has a leftover `.minerva/decisions/` directory, that's the legacy location — `minerva:init` will report it; either migrate to `.minerva/knowledge/` or treat both as authoritative until you do.
