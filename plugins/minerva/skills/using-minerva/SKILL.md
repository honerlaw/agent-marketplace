---
name: using-minerva
description: Use when starting work in a project that uses minerva (a `.minerva/` directory exists at the project root, or the user has invoked any `minerva:` skill in this session), or when the user describes starting / continuing / finishing a meaningful unit of work — features, refactors, investigations, spikes. Explains when to invoke minerva:propose, minerva:replan, minerva:work, minerva:promote, minerva:init and gives common scenarios. Skip for routine bugfixes, trivial edits, and one-shot Q&A.
---

# Using minerva

minerva is the durable-record discipline for software work in this project. It encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — concrete, past-tense knowledge items become `.minerva/knowledge/` entries, proposals get rewritten to describe what shipped, and raw scratchpads are archived.

The heuristic: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep. If no, summarize and discard.

## Detecting a minerva project

You're in a minerva project if any of these are true:

- A `.minerva/` directory exists at the project root.
- The user invoked any `minerva:` skill (`minerva:init`, `minerva:propose`, `minerva:replan`, `minerva:work`, `minerva:promote`) earlier in the session.
- `CLAUDE.md`, `AGENTS.md`, or similar has a `## minerva` Routing section pointing at `.minerva/`.

If none are true, the project isn't using minerva. Don't reach for these skills unsolicited — but if the user is clearly starting durable work that would benefit from the discipline, suggest `minerva:init` as the entry point (it scaffolds the directory and adds a Routing section to the agent file).

## Skill decision matrix

| Situation | Skill |
|---|---|
| First time using minerva in this project | `minerva:init` |
| Starting a new unit of work (feature, refactor, investigation, spike) | `minerva:propose` |
| Resuming work on an existing unit | `minerva:work` |
| The plan still holds — keep going | (no skill — continue work normally) |
| Reality has diverged from the plan in a load-bearing way | `minerva:replan` |
| Just hit something that's clearly a durable decision, mid-work | `minerva:promote "<short description>"` |
| Implementation is done — finalize the record | `minerva:promote` (no argument) |

The five skills cover the full lifecycle. Most of the time you stay in `minerva:work` and don't touch the others.

## The persistence hierarchy (quick reference)

| Tier | Files | Read by Claude |
|---|---|---|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` | Every conversation in this project — decisions, bugs, patterns |
| Searchable-on-demand | `.minerva/work/NNN-<slug>/proposal.md`, `.minerva/work/NNN-<slug>/replan.md` | Grep when relevant |
| Ephemeral | `.minerva/work/NNN-<slug>/scratchpad.md` | Live during `minerva:work`, archived by `minerva:promote` |

When in doubt about whether something belongs in a knowledge file vs. a scratchpad note, apply the new-engineer-in-a-year heuristic above.

## Common scenarios

**"This is a fresh project — let's start using minerva."**
→ `minerva:init`. Scaffolds `.minerva/work/` and `.minerva/knowledge/`, checks `.gitignore` for exclusions, and adds a Routing section to the agent file (CLAUDE.md / AGENTS.md / GEMINI.md).

**"Let's add a payments flow."**
→ `minerva:propose "add payments flow"` (or just `minerva:propose` — the skill infers your intent from context). Brainstorm the design through the skill's flow. Don't start coding until the proposal is written.

**"Where were we on the payments thing?"**
→ `minerva:work`. The skill reads `proposal.md`, the latest `replan.md`, and skims `scratchpad.md` to figure out where to pick up.

**"It turns out we can't use Stripe's hosted checkout — we need our own form."**
→ This is load-bearing divergence. While inside `minerva:work`, the protocol auto-triggers `minerva:replan`. If you're outside `minerva:work` (e.g. coming back from a tangent), invoke `minerva:replan` directly.

**"We just decided the queue retry policy should be exponential backoff capped at 5 minutes."**
→ Mid-work durable decision. Run `minerva:promote "exponential backoff capped at 5 minutes for queue retries"`. The scratchpad entry gets marked so the end-of-work pass doesn't re-promote it.

**"Tests pass and the feature is shipped. Ready to clean up."**
→ `minerva:promote` with no argument. The end-of-work pass partitions the scratchpad into promote/merge/discard, rewrites `proposal.md` to match what shipped, and archives the raw scratchpad.

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
- Grep `.minerva/work/` when you need historical context for a feature.
- Don't create `scratchpad.md` files directly outside of `minerva:work`. If you need scratch space, use a TodoWrite or notes in conversation instead.
