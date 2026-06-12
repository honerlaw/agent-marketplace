---
name: review
description: Use when the user invokes `minerva:review`, asks to review or audit a changeset, or wants to verify shipped code matches what was designed. With a minerva work unit in context, runs a spec/knowledge audit alongside a code quality review, presenting both result sets in parallel before unified triage. Without minerva context, runs a code quality review directly. If a GitHub PR exists for the current branch, delegates the code quality pass to `code-review:code-review`; otherwise performs a structured inline check using the same finding format. Triage state is persisted to scratchpad so re-runs can pre-fill prior dispositions.
---

Review the active changeset for both design compliance and code quality. Works against the local diff — no PR required. When a minerva work unit is found, runs a spec/knowledge audit alongside the code quality review and presents both result sets in parallel before triage. When no minerva context exists, runs the code quality review alone.

## Usage

- `minerva:review` — audits the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous; falls back to a plain code review if no work unit is found
- `minerva:review 005-add-payments` — audit the named unit explicitly

## Protocol

The full step protocols live verbatim in `references/protocol.md` — **read it now, before executing**: **Target resolution** → **Worktree entry** → **Diff resolution** → **Minerva audit** (spec fidelity + knowledge compliance; only when minerva context exists) → **Code review invocation** (delegates to `code-review:code-review` when a PR exists, inline structured check otherwise) → **Parallel presentation** → **Interactive triage** (FIX / SUGGEST / IGNORE) → **Triage persistence** (scratchpad pre-fill for re-runs) → **On approval — file writes** → **Report**.

## Lifecycle ordering

Canonical order: `minerva:work → minerva:review → minerva:promote → minerva:ship`. Review runs **before** promote so review-derived scratchpad notes flow through the promote partition. If review surfaces durable knowledge that promote already ran on, run promote again. The skills are idempotent — cycle as needed.

## Idempotency

Review is stateless across runs except for the `## Review triage YYYY-MM-DD` blocks it writes to scratchpad for resume. Re-running on the same diff produces the same findings; dispositions are pre-filled from the most recent triage block.

```
minerva:review  →  fixes applied  →  minerva:promote  →  minerva:review  →  zero findings  →  minerva:ship
```

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote` — one writer, one set of conventions.
- **A `review.md` log file.** FIX outcomes are visible in git; SUGGEST and IGNORE outcomes flow through scratchpad → promote. Triage state lives in scratchpad. A standalone log duplicates what those already capture.
- **Scoped review** (e.g. `minerva:review src/api/`). Deferred until the no-scope default proves noisy.
