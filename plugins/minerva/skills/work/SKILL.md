---
name: work
description: Implements a minerva work unit — reads the proposal and any replans, maintains a live scratchpad, auto-invokes the `minerva:replan` protocol when reality drifts in a load-bearing way, and checks proposal Open Questions on resume and Success criteria before signaling completion. Use when the user is ready to start coding on a proposed feature, wants to implement or resume a work unit ("pick up where we left off"), or invokes `minerva:work`.
---

Implement the active work unit while maintaining the scratchpad and honoring the persistence hierarchy.

## Usage

- `minerva:work` — resume the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous
- `minerva:work 005-add-payments` — operate on the named unit explicitly (slug or path accepted)
- `minerva:work <date-slug> --auto=<orchestrator>` — orchestrated mode; see **Orchestrated mode** below

## Target resolution

Same pattern used by `minerva:replan`, `minerva:promote`, `minerva:review`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — if the user passed a slug or path (`minerva:work 005-foo` or a full `.minerva/work/...` path), resolve it directly. Look in both `.minerva/work/<date-slug>/` and `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/` — whichever exists wins.
2. **Current-session context** — if a unit slug, path, or branch name has been mentioned in this session, use it.
3. **Most-recently-modified across both locations** — list candidates from `.minerva/work/*/` AND `.minerva/worktrees/*/.minerva/work/*/` (both id forms), take the most-recently-modified by directory mtime. Active work units (created by `minerva:propose`) live in worktrees; shipped + merged units live in `.minerva/work/` on the default branch — both locations must be scanned every time.
4. **Ambiguity** — if multiple recent candidates exist and context can't pick, list them and ask the user.
5. **None found** — report "no work units found — run `minerva:propose` first" and stop.

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator
(`minerva:propose-ship-auto`, `-balanced`, `-quick`) is driving this run and has substituted its
own adjudication for the user gates below. Act on the argument — never on a judgment about who
is calling. Per `2026-06-07-decision-phase-handoff-rides-observable-intake`, *"'An inline
argument was passed' is observable; 'the prior phase converged' is an opinion."*

When it is present:

- **Setup steps 5-6** — skip both; the caller resolved open questions and needs no resumption summary.
- **Divergence detection** — hand the divergence to `<orchestrator>`'s Phase 2.5. Do **not** invoke
  `minerva:replan`, which reaches `minerva:grill-plan` — a one-question-at-a-time user interview.
- **Completion signal** — return the criteria checklist to `<orchestrator>`'s completion gate rather
  than recommending `minerva:promote` to the user.
- **Out of scope** — control returns to `<orchestrator>`, never to open conversation.

Absent the argument every gate below behaves exactly as written; the interactive path is unchanged.

## Worktree addressing (run before Setup)

Every active work unit lives in an isolated git worktree created by `minerva:propose`, and **minerva never calls `EnterWorktree`** — the session cwd stays the parent repo and every path carries the `.minerva/worktrees/<date-slug>/` prefix. The full protocol — the primary path, the resurrection path when the worktree is gone, and the bail when neither location has the unit — lives in `references/worktree-addressing.md`. **Read it before Setup.**

## Setup (run at the start of every `minerva:work` invocation)

All paths below are **prefixed with** the worktree root (`.minerva/worktrees/<date-slug>/`); the session cwd stays the parent repo, so write each path out in full and run git as `git -C .minerva/worktrees/<date-slug> …`.

1. Read `.minerva/work/<date-slug>/proposal.md`.
2. Read **all** `.minerva/work/<date-slug>/replan.md` entries chronologically. When the latest replan conflicts with the original proposal, the replan wins.
3. Read `.minerva/work/<date-slug>/scratchpad.md` to figure out where work left off.
4. Glance at `git status` and the last 3 commits (run via `git -C .minerva/worktrees/<date-slug>`) to corroborate.
5. **Resolve open questions.** If `## Open Questions` in `proposal.md` has unresolved items, surface them to the user before implementation begins:
   > "The proposal lists these open questions — let's settle them before implementing: [list]. Once answered, I'll edit the proposal to record the resolutions."
   When the user answers, edit `proposal.md` to either remove resolved items from `## Open Questions` or move them into `## Approach` as decisions.
6. **Summarize the resumption point** to the user in one short paragraph: what the goal is, what's been done, what's next. Confirm before proceeding.

**Under `--auto`, skip steps 5-6** — the orchestrator owns both.

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

The scratchpad is **ephemeral working memory**. `minerva:promote` will later partition it into "promote / merge into proposal / discard." Keep signal-to-noise high.

When a peer session messages you, read `plugins/minerva/skills/propose/references/cross-session.md`: inform, never delegate.

### Divergence detection

Continuously check: does the approach I'm taking still match `proposal.md` (as superseded by the latest `replan.md`)?

**Invoke the `minerva:replan` skill (via the `Skill` tool)** when reality diverges in a load-bearing way:
- A core assumption from the proposal turns out to be wrong.
- The approach itself is changing (not just an implementation detail within the approach).
- Scope is shifting (in or out of the work unit).

**Do not trigger** for:
- Routine implementation choices (which library, which helper to extract, how to structure a function).
- Small refactors along the way.
- Edge-case handling that wasn't in the proposal but doesn't change the approach.

**On trigger:** pause implementation. **Under `--auto`, hand the divergence to `<orchestrator>`'s Phase 2.5 and let it adjudicate — do not invoke `minerva:replan` or `minerva:grill-plan`.** Otherwise tell the user "this looks like a load-bearing divergence — running the replan protocol", then invoke the `minerva:replan` skill via the `Skill` tool and follow its protocol. Once the replan entry is written, resume implementation with the new plan in context.

### Completion signal

Implementation is **done** when every item in `## Success criteria` (as amended by replans) can be honestly checked off. Before suggesting `minerva:promote`:

1. Re-read `## Success criteria` from `proposal.md`.
2. For each item, state objectively whether it's met (with evidence: tests pass, file exists, behavior verified, etc.).
3. If any item is not met, do not suggest promote — keep working or trigger `minerva:replan` if the criterion itself is wrong.
4. If every item is met, surface this checklist to the user and recommend `minerva:promote` as the next step. Do not run promote automatically — that's the user's call. **Under `--auto`, return the checklist to `<orchestrator>`'s completion-verification gate instead.**

**On a unit declaring `## Phases`,** a phase is done when *its own* criteria are met: recommend `minerva:ship`, not promote. Mode A waits for the final phase — use promote's **Mode B** meanwhile, so each phase's PR carries its own knowledge instead of stranding it if the unit stalls (`plugins/minerva/skills/propose/references/phasing.md`).

If the proposal has no `## Success criteria` section (e.g. it was authored before that section existed), fall back to the proposal's `## Goal` paragraph as the implicit criterion and note the gap to the user.

## Out of scope

`minerva:work` is a setup-and-protocol skill, not a one-shot operation. After the initial resumption summary it hands control back to normal conversation; the protocols above apply for the rest of the session. **Under `--auto` control returns to `<orchestrator>` instead — never to open conversation.**
