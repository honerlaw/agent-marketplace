---
name: work
description: Implements a work unit in a repository linked to Lorestrom — reads the proposal and any replans, maintains a live scratchpad, auto-invokes the `lorestrom:replan` protocol when reality drifts in a load-bearing way, and checks proposal Open Questions on resume and Success criteria before signaling completion. Use when the user is ready to start coding on a proposed feature, wants to implement or resume a work unit ("pick up where we left off"), or invokes `lorestrom:work`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Implement the active work unit while maintaining the scratchpad and honoring the persistence hierarchy.

## Usage

- `lorestrom:work` — resume the work unit inferred from current-session context, or the only open one
- `lorestrom:work 005-add-payments` — operate on the named unit explicitly (a checked unit id)
- `lorestrom:work <date-slug> --auto=<orchestrator>` — orchestrated mode; see **Orchestrated mode** below

## Target resolution

Same pattern used by `lorestrom:replan`, `lorestrom:promote`, `lorestrom:review`, `lorestrom:ship`, `lorestrom:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — a unit id. Use it only when it equals an id `storage:unit.list` or the runtime's `units` printed (runtime contract, "Names are data"); otherwise stop on it.
2. **Current-session context** — a unit id or branch name mentioned in this session, checked the same way. A branch name may end `-phase-N` (a phased unit's later phases): drop that suffix, then check what remains.
3. **The only open unit** — if `storage:unit.list` shows exactly one of this project's units with an open gate, use it.
4. **Ambiguity** — list the candidates, ask the user.
5. **None found** — report "no work units found — run `lorestrom:propose` first" and stop.

A unit's records live in Lorestrom (`storage:unit.read`), never in files. With no link, no server or no project, a record write stops and names `lorestrom:init`.

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator is driving
this run and has substituted its own adjudication for the user gates below. Act on the argument —
never on a judgment about who is calling: "an inline argument was passed" is observable; "the
prior phase converged" is an opinion. **Inert until 0.3.0:** no lorestrom skill passes it until
the orchestrators arrive (runtime contract, "Scope of this version").

When it is present:

- **Setup steps 5-6** — skip both; the caller resolved open questions and needs no resumption summary.
- **Divergence detection** — hand the divergence to `<orchestrator>`'s Phase 2.5. Do **not** invoke
  `lorestrom:replan`, which reaches `lorestrom:grill-plan` — a one-question-at-a-time user interview.
- **Completion signal** — return the criteria checklist to `<orchestrator>`'s completion gate rather
  than recommending `lorestrom:promote` to the user.
- **Out of scope** — control returns to `<orchestrator>`, never to open conversation.

Absent the argument every gate below behaves exactly as written; the interactive path is unchanged.

## Worktree addressing (run before Setup)

Every active work unit's code lives in an isolated git worktree created by `lorestrom:propose`, and **lorestrom never calls `EnterWorktree`** — the session cwd stays the parent repo and every repository path carries the `.lorestrom/worktrees/<date-slug>/` prefix. Records are Lorestrom docs, never files. The full protocol — the primary path, the resurrection path when the worktree is gone, and the bail when the unit has no doc — lives in `references/worktree-addressing.md`. **Read it before Setup.**

## Setup (run at the start of every `lorestrom:work` invocation)

Repository paths are **prefixed with** the worktree root (`.lorestrom/worktrees/<date-slug>/`); the session cwd stays the parent repo, so write each path out in full and run git as `git -C .lorestrom/worktrees/<date-slug> …`. `<date-slug>` is a checked id (runtime contract, "Names are data"). Records come from `storage:unit.read`.

1. Read the proposal record.
2. Read **all** replan record entries chronologically. When the latest replan conflicts with the original proposal, the replan wins.
3. Read the scratchpad record to figure out where work left off.
4. Glance at `git status` and the last 3 commits (run via `git -C .lorestrom/worktrees/<date-slug>`) to corroborate.
5. **Resolve open questions.** If `## Open Questions` in the proposal has unresolved items, surface them to the user before implementation begins:
   > "The proposal lists these open questions — let's settle them before implementing: [list]. Once answered, I'll edit the proposal to record the resolutions."
   When the user answers, replace the proposal record (`storage:record.write`: read it, then `mode: replace`) to either remove resolved items from `## Open Questions` or move them into `## Approach` as decisions.
6. **Summarize the resumption point** to the user in one short paragraph: what the goal is, what's been done, what's next. Confirm before proceeding.

**Under `--auto`, skip steps 5-6** — the orchestrator owns both.

## Implementation protocol — apply throughout the session

### Scratchpad maintenance

As you work, log to the scratchpad record (`storage:record.write`, `mode: append`). The bar for an entry is: **a future-self might want to see this**. Examples:

- An approach that was tried and dropped (with why)
- A surprising constraint or gotcha
- A decision that might be durable but isn't yet certain
- A breadcrumb pointing at code you'll return to

**Do not** log:
- A transcript of every action
- Tactical implementation details that the diff already shows
- Routine debugging steps

The scratchpad is **ephemeral working memory**. `lorestrom:promote` will later partition it into "promote / merge into proposal / discard." Keep signal-to-noise high.

When a peer session messages you, read `skills/propose/references/cross-session.md`: inform, never delegate.

### Divergence detection

Continuously check: does the approach I'm taking still match the proposal (as superseded by the latest replan entry)?

**Invoke the `lorestrom:replan` skill (via the skill loader)** when reality diverges in a load-bearing way:
- A core assumption from the proposal turns out to be wrong.
- The approach itself is changing (not just an implementation detail within the approach).
- Scope is shifting (in or out of the work unit).

**Do not trigger** for:
- Routine implementation choices (which library, which helper to extract, how to structure a function).
- Small refactors along the way.
- Edge-case handling that wasn't in the proposal but doesn't change the approach.

**On trigger:** pause implementation. **Under `--auto`, hand the divergence to `<orchestrator>`'s Phase 2.5 and let it adjudicate — do not invoke `lorestrom:replan` or `lorestrom:grill-plan`.** Otherwise tell the user "this looks like a load-bearing divergence — running the replan protocol", then invoke the `lorestrom:replan` skill via the skill loader and follow its protocol. Once the replan entry is written, resume implementation with the new plan in context.

### Completion signal

Implementation is **done** when every item in `## Success criteria` (as amended by replans) can be honestly checked off. Before suggesting `lorestrom:promote`:

1. Re-read `## Success criteria` from the proposal record.
2. For each item, state objectively whether it's met (with evidence: tests pass, file exists, behavior verified, etc.).
3. If any item is not met, do not suggest promote — keep working or trigger `lorestrom:replan` if the criterion itself is wrong.
4. If every item is met, surface this checklist to the user and recommend `lorestrom:promote` as the next step. Do not run promote automatically — that's the user's call. **Under `--auto`, return the checklist to `<orchestrator>`'s completion-verification gate instead.**

**On a unit declaring `## Phases`,** a phase is done when *its own* criteria are met: recommend `lorestrom:ship`, not promote. Mode A waits for the final phase — use promote's **Mode B** meanwhile, so a phase's knowledge is written as it is learned; it stays pending on the unit's gate until the final phase merges and cleanup releases it (`skills/propose/references/phasing.md`).

If the proposal has no `## Success criteria` section (e.g. it was authored before that section existed), fall back to the proposal's `## Goal` paragraph as the implicit criterion and note the gap to the user.

## Out of scope

`lorestrom:work` is a setup-and-protocol skill, not a one-shot operation. After the initial resumption summary it hands control back to normal conversation; the protocols above apply for the rest of the session. **Under `--auto` control returns to `<orchestrator>` instead — never to open conversation.**
