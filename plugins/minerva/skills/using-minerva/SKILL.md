---
name: using-minerva
description: Use when starting work in a project that uses minerva (has work/ or decisions/ directories at the project root, or where the user has invoked any minerva: command in this session), or when the user describes starting / continuing / finishing a meaningful unit of work — features, refactors, investigations, spikes. Explains when to invoke /propose, /replan, /work, /promote and gives common scenarios. Skip for routine bugfixes, trivial edits, and one-shot Q&A.
---

# Using minerva

minerva is the durable-record discipline for software work in this project. It encodes a persistence hierarchy where **artifacts get promoted, not just accumulated** — significant scratchpad items become `decisions/` entries, proposals get rewritten to describe what shipped, and raw scratchpads are archived.

The heuristic: **would a new engineer (or new agent) joining the project in a year benefit from reading this?** If yes, keep. If no, summarize and discard.

## Detecting a minerva project

You're in a minerva project if any of these are true:

- A `work/` directory exists at the project root with `NNN-<slug>/` subdirectories.
- A `decisions/` directory exists with `NNN-<slug>.md` files.
- The user invoked any `minerva:` command (`/propose`, `/replan`, `/work`, `/promote`) earlier in the session.
- `CLAUDE.md` references the persistence hierarchy or the `work/` + `decisions/` layout.

If none of these are true, the project isn't using minerva — don't reach for these commands unsolicited. Suggest `/propose` only when the user is clearly starting durable work that would benefit from the discipline.

## Command decision matrix

| Situation | Command |
|---|---|
| Starting a new unit of work (feature, refactor, investigation, spike) | `/propose <slug>` |
| Resuming work on an existing unit | `/work [target]` |
| The plan still holds — keep going | (no command — continue work normally) |
| Reality has diverged from the plan in a load-bearing way | `/replan [target]` |
| Just hit something that's clearly a durable decision, mid-work | `/promote "<short description>"` |
| Implementation is done — finalize the record | `/promote` (no argument) |

The four commands cover the full lifecycle. Most of the time you stay in `/work` and don't touch the others.

## The persistence hierarchy (quick reference)

| Tier | Files | Read by Claude |
|---|---|---|
| Always-read | `CLAUDE.md`, `decisions/` | Every conversation in this project |
| Searchable-on-demand | `work/NNN-<slug>/proposal.md`, `work/NNN-<slug>/replan.md` | Grep when relevant |
| Ephemeral | `work/NNN-<slug>/scratchpad.md` | Live during `/work`, archived by `/promote` |

When in doubt about whether something belongs in a decision file vs. a scratchpad note, apply the new-engineer-in-a-year heuristic above.

## Common scenarios

**"Let's add a payments flow."**
→ `/propose add-payments`. Brainstorm the design through the command's flow. Don't start coding until the proposal is written.

**"Where were we on the payments thing?"**
→ `/work payments`. The command reads `proposal.md`, the latest `replan.md`, and skims `scratchpad.md` to figure out where to pick up.

**"It turns out we can't use Stripe's hosted checkout — we need our own form."**
→ This is load-bearing divergence. While inside `/work`, the protocol auto-triggers `/replan`. If you're outside `/work` (e.g. coming back from a tangent), invoke `/replan` directly.

**"We just decided the queue retry policy should be exponential backoff capped at 5 minutes."**
→ Mid-work durable decision. Run `/promote "exponential backoff capped at 5 minutes for queue retries"`. The scratchpad entry gets marked so the end-of-work pass doesn't re-promote it.

**"Tests pass and the feature is shipped. Ready to clean up."**
→ `/promote` with no argument. The end-of-work pass partitions the scratchpad into promote/merge/discard, rewrites `proposal.md` to match what shipped, and archives the raw scratchpad.

## Anti-patterns — when NOT to use minerva

Skip the workflow entirely for:

- **Trivial edits** — typo fixes, renames, single-line tweaks.
- **Routine bugfixes** — straightforward bugs with no architectural implications.
- **One-shot Q&A** — "what does this function do?", "why is this slow?".
- **Exploratory reads** — scanning code to understand it without changing anything.
- **Quick refactors** — small, mechanical changes contained within a function or file.

The ceremony only pays off when the work is substantial enough that future readers will need the context. Don't impose it on work that ships in a single commit.

## Working in a minerva project without invoking commands

Even when you don't run a `minerva:` command this session, respect the hierarchy:

- Treat `CLAUDE.md` and `decisions/` as authoritative — read them when starting work in the project.
- Grep `work/` when you need historical context for a feature.
- Don't create `scratchpad.md` files directly outside of `/work`. If you need scratch space, use a TodoWrite or notes in conversation instead.
