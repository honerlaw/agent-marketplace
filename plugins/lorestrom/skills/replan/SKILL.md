---
name: replan
description: Records a course-correction for the current work unit in a repository linked to Lorestrom — drafts Original plan / What changed / New plan, stress-tests it via `lorestrom:grill-plan`, then appends a dated divergence entry to the unit's replan record in Lorestrom. Use when work has diverged from the proposal in a load-bearing way — a core assumption was wrong, the approach is changing, or scope is shifting — or to amend an approved proposal before `lorestrom:work` starts (pre-work tweaks), or when the user invokes `lorestrom:replan`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Append a dated replan entry to the current work unit when reality has diverged from the proposal, OR amend an approved proposal pre-work.

## Usage

- `lorestrom:replan` — operates on the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous
- `lorestrom:replan 005-add-payments` — operate on the named unit explicitly (slug or path)
- `lorestrom:replan <date-slug> --auto=<orchestrator>` — orchestrated mode; see **Orchestrated mode** below

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator has
substituted its own adjudication for this skill's user gates. Act on the argument — never on a
judgment about who is calling. Absent it, every gate behaves exactly as written. **Inert until 0.3.0:**
no lorestrom skill passes it until the orchestrators arrive (runtime contract, "Scope of this version").

It satisfies steps 3, 5 and 7 below: the orchestrator supplies the clarifying answers,
`lorestrom:grill-plan` is **not** invoked (it is a one-question-at-a-time user interview), and the
orchestrator's acceptance stands in for the hard gate.

## When to use

- **Mid-work divergence** (most common): a core assumption broke, the approach is shifting, scope changed. `lorestrom:work` auto-triggers this protocol.
- **Pre-work amendment**: the proposal was approved but the user wants to tweak it before implementation starts. Same protocol — the replan entry's `Original plan` is just the freshly written proposal, and `What changed` is "before implementation: user wants to adjust X".

## Target resolution

Same pattern used by `lorestrom:work`, `lorestrom:promote`, `lorestrom:review`, `lorestrom:ship`, `lorestrom:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — a unit id. Use it only when it equals an id `storage:unit.list` or the runtime's `units` printed (runtime contract, "Names are data"); otherwise stop on it.
2. **Current-session context** — a unit id or branch name mentioned in this session, checked the same way.
3. **The only open unit** — if `storage:unit.list` shows exactly one of this project's units with an open gate, use it.
4. **Ambiguity** — list the candidates, ask the user.
5. **None found** — report "no work units found — run `lorestrom:propose` first" and stop.

A unit's records live in Lorestrom (`storage:unit.read`), never in files. With no link, no server or no project, a record write stops and names `lorestrom:init`.

## Worktree addressing

After resolving the target and before reading or writing any files:

- `<date-slug>` is a checked id (runtime contract, "Names are data").
- **Do not call `EnterWorktree`** — lorestrom worktrees live under `.lorestrom/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- Code lives in the worktree: prefix every repository file path this skill reads or writes with `.lorestrom/worktrees/<date-slug>/`, and run every git command as `git -C .lorestrom/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch.
- The unit's records (proposal, scratchpad, replan, followups) are Lorestrom docs read and written through `storage:` operations, never files in either tree.

This keeps the skill correct regardless of where it's invoked from — every file path it touches names the right working tree explicitly.

## Protocol

Same brainstorming pattern as `lorestrom:propose`, but framed around divergence:

1. **Read the existing context first.** Read the proposal, any prior replan entries, and the current scratchpad (`storage:unit.read`). The brainstorm must be grounded in what actually happened.
2. **Frame the replan around three pieces:**
   - **Original plan** — what the proposal (or latest prior replan) said the approach was
   - **What changed** — what was discovered, what broke, what assumption was wrong (for pre-work amendments: "user requested adjustment before implementation")
   - **New plan** — the revised approach
3. **Ask clarifying questions one at a time** to fill in any of the three pieces that aren't already obvious from the conversation or files.
4. **Propose 2–3 alternative new plans** if the path forward isn't already settled. Iterate.
5. **Draft the replan entry internally**, then **stress-test it before showing it for approval.** Assemble the Original plan / What changed / New plan triple in conversation (do not write it yet) and invoke the `lorestrom:grill-plan` skill via the skill loader against it (no argument needed — it reads the draft from conversation). Let grill-plan walk the decision tree, edit affected pieces in place as answers surface, and return only once shared understanding is reached. The entry that exits grilling is what step 6 presents.
6. **Present the resulting entry** for approval before writing.
7. **Hard gate:** do not append to the replan record until the user — or, under `--auto=<orchestrator>`, that
   orchestrator's new-plan acceptance — has approved the entry.

## On approval — record write

1. If the unit has no replan record yet, create it (`storage:record.write`, record `replan`) with this header:

   ```markdown
   # Replan log: <slug>

   ```

2. Append a new entry (`storage:record.write`, `mode: append`) using this exact template (today's date in `YYYY-MM-DD`):

   ```markdown
   ## YYYY-MM-DD — <short, declarative title>

   **Original plan**: <one or two sentences>
   **What changed**: <what was discovered, what broke, what assumption was wrong>
   **New plan**: <one or two sentences>
   ```

3. **Update Success criteria if the new plan changes them.** If the replan changes what "done" looks like, also replace the proposal record's `## Success criteria` section to reflect the new bar (`storage:record.write`: read the proposal, then `mode: replace`). Otherwise leave it alone — the replan entry will still supersede the proposal on conflict.

4. Report the unit and the title of the appended entry. Suggest resuming `lorestrom:work` next.

## Out of scope

This skill stops at appending to the replan record (and optionally editing the proposal's Success criteria). It does **not** invoke implementation — return control to `lorestrom:work` (or its in-progress session) after writing.
