---
description: Enter implementation mode for a work unit. Reads its proposal and any replans, maintains a live scratchpad, watches for divergence from the plan, and auto-invokes the /replan protocol when reality drifts in a load-bearing way.
---

Implement the active work unit while maintaining the scratchpad and honoring the persistence hierarchy.

## Usage

- `/work` — resume the most-recently-modified `.minerva/work/NNN-*/`
- `/work 003-add-payments` — explicit work directory
- `/work add-payments` — substring match

## Target resolution

Identical to `/replan`:
1. Exact directory match: `.minerva/work/<arg>/`.
2. Substring match against `.minerva/work/NNN-*/`; single match wins, multiple → list and ask.
3. No argument → most-recently-modified `.minerva/work/NNN-*/` by mtime.
4. `.minerva/work/` missing or empty → report "no work units found — run `/propose <slug>` first" and stop.

## Setup (run at the start of every `/work` invocation)

1. Read `proposal.md`.
2. Read **all** `replan.md` entries chronologically. When the latest replan conflicts with the original proposal, the replan wins.
3. Read `scratchpad.md` to figure out where work left off.
4. Glance at `git status` and the last 3 commits to corroborate.
5. **Summarize the resumption point** to the user in one short paragraph before doing anything else: what the goal is, what's been done, what's next. Confirm before proceeding.

## Implementation protocol — apply throughout the session

### Scratchpad maintenance

As you work, log to `scratchpad.md`. The bar for an entry is: **a future-self might want to see this**. Examples:

- An approach that was tried and dropped (with why)
- A surprising constraint or gotcha
- A decision that might be durable but isn't yet certain
- A breadcrumb pointing at code you'll return to

**Do not** log:
- A transcript of every action
- Tactical implementation details that the diff already shows
- Routine debugging steps

The scratchpad is **ephemeral working memory**. `/promote` will later partition it into "promote / merge into proposal / discard." Keep signal-to-noise high.

### Divergence detection

Continuously check: does the approach I'm taking still match `proposal.md` (as superseded by the latest `replan.md`)?

**Auto-trigger the `/replan` protocol** when reality diverges in a load-bearing way:
- A core assumption from the proposal turns out to be wrong.
- The approach itself is changing (not just an implementation detail within the approach).
- Scope is shifting (in or out of the work unit).

**Do not trigger** for:
- Routine implementation choices (which library, which helper to extract, how to structure a function).
- Small refactors along the way.
- Edge-case handling that wasn't in the proposal but doesn't change the approach.

**On trigger:** pause implementation. Tell the user "this looks like a load-bearing divergence — running the replan protocol." Then read `plugins/minerva/commands/replan.md` and follow its protocol inline (it's just instructions — there's no separate tool invocation). Once the replan entry is written, resume implementation with the new plan in context.

### Completion signal

When you believe implementation is done (the proposal's success criteria are met, any tests pass, the visible scope is delivered), surface `/promote` as the next step. Do not run it automatically — that's the user's call.

## Out of scope

`/work` is a setup-and-protocol command, not a one-shot operation. After the initial resumption summary it hands control back to normal conversation; the protocols above apply for the rest of the session.
