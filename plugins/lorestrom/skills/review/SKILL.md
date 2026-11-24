---
name: review
description: Reviews a changeset against both the spec/knowledge lenses of a work unit kept in Lorestrom and code quality. With a work unit in context it runs a spec/knowledge audit alongside the code quality review, presenting both result sets before unified triage; if a GitHub PR exists and the optional `code-review:code-review` skill is installed it delegates code quality there, otherwise it performs a check via a fresh-context subagent in the same finding format. Triage state persists to the unit's scratchpad record so re-runs pre-fill prior dispositions. Use when implementation on a work unit has just finished and the diff is unreviewed, when the user asks to review or audit a changeset or to verify shipped code matches what was designed, or when they invoke `lorestrom:review`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Review the active changeset for both design compliance and code quality. Works against the local diff — no PR required. When a work unit is found, runs a spec/knowledge audit alongside the code quality review and presents both result sets in parallel before triage. When no unit context exists (none found, or the repository is not linked), runs the code quality review alone.

## Usage

- `lorestrom:review` — audits the work unit inferred from current-session context, or the only open one; falls back to a plain code review if no work unit is found
- `lorestrom:review 005-add-payments` — audit the named unit explicitly
- `lorestrom:review <date-slug> --auto=<orchestrator>` — orchestrated mode; see **Orchestrated mode** below

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator has
substituted its own adjudication for this skill's user gates. Act on the argument — never on a
judgment about who is calling. Absent it, every gate behaves exactly as written. `lorestrom:propose-ship-auto` passes it (its `## Delegated skills` table).

It satisfies the triage hard gate in `references/protocol.md`.

## Protocol

The full step protocols live verbatim in `references/protocol.md` — **read it now, before executing**: **Target resolution** → **Worktree entry** → **Diff resolution** → **Unit audit** (spec fidelity + knowledge compliance; only when unit context exists) → **Code review invocation** (delegates to installed `code-review:code-review` when a PR exists, fresh-context subagent check otherwise) → **Parallel presentation** → **Interactive triage** (FIX / SUGGEST / IGNORE) → **Triage persistence** (scratchpad pre-fill for re-runs) → **On approval — code and record writes** → **Report**.

## Lifecycle ordering

Canonical order: `lorestrom:work → lorestrom:review → lorestrom:promote → lorestrom:ship`. Review runs **before** promote so review-derived scratchpad notes flow through the promote partition. If review surfaces durable knowledge that promote already ran on, run promote again. The skills are idempotent — cycle as needed.

## Idempotency

Review is stateless across runs except for the `## Review triage YYYY-MM-DD` blocks it writes to the scratchpad record for resume. Re-running on the same diff produces the same findings; dispositions are pre-filled from the most recent triage block.

```
lorestrom:review  →  fixes applied  →  lorestrom:promote  →  lorestrom:review  →  zero findings  →  lorestrom:ship
```

## Out of scope

- **Writing knowledge entries directly.** All durable knowledge goes through `lorestrom:promote` — one writer, one set of conventions.
- **A `review.md` log file.** FIX outcomes are visible in git; SUGGEST and IGNORE outcomes flow through the scratchpad record → promote. Triage state lives in the scratchpad record. A standalone log duplicates what those already capture.
- **Scoped review** (e.g. `lorestrom:review src/api/`). Deferred until the no-scope default proves noisy.
