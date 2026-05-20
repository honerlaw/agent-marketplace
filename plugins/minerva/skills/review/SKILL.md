---
name: review
description: Use when the user invokes `minerva:review`, asks to review or audit a changeset, or wants to verify shipped code matches what was designed. With a minerva work unit in context, runs a spec/knowledge audit alongside a code quality review, presenting both result sets in parallel before unified triage. Without minerva context, runs a code quality review directly. If a GitHub PR exists for the current branch, delegates the code quality pass to `code-review:code-review`; otherwise performs a structured inline check using the same finding format. Triage state is persisted to scratchpad so re-runs can pre-fill prior dispositions.
---

Review the active changeset for both design compliance and code quality. Works against the local diff — no PR required. When a minerva work unit is found, runs a spec/knowledge audit alongside the code quality review and presents both result sets in parallel before triage. When no minerva context exists, runs the code quality review alone.

## Usage

- `minerva:review` — audits the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous; falls back to a plain code review if no work unit is found
- `minerva:review 005-add-payments` — audit the named unit explicitly

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/` by directory mtime.
4. **Ambiguity** → list candidates, ask.
5. **None found** → **no minerva context**. Skip to [Code review invocation](#code-review-invocation) — do not stop.

## Worktree entry

After resolving the target and before reading docs or running git commands:

- If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/` and the current session is **not** already in that worktree, call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`.
- If the docs live only on the default branch (a shipped unit being reviewed retrospectively), operate on the parent repo without entering a worktree.
- If the session is already in the matching worktree, do nothing.
- If target resolution returned no minerva context, skip this step — the code review pass runs in whatever working tree the user invoked the skill from.

Diff resolution, file reads, and `code-review:code-review` all run inside the resolved working tree.

## Diff resolution

Decide what to review:

1. Run `git status --porcelain`.
   - **Non-empty** → review the working-tree diff (`git diff HEAD` for tracked changes, plus the contents of untracked files).
   - **Empty** → review the branch diff against the default branch.
2. Default-branch detection (only needed when the working tree is clean):
   - Try `git symbolic-ref refs/remotes/origin/HEAD` (parse out `refs/remotes/origin/<name>`).
   - Fall back to `main`, then `master`.
   - Compute the diff as `git diff $(git merge-base <default> HEAD)...HEAD`.
3. **Empty diff** (clean tree, no commits ahead of default) → report "nothing to review" and stop.
4. **Non-git repo** → report and stop.

## Minerva audit (only when minerva context exists)

### Context read

Before generating findings, read:

1. `proposal.md` — the original design.
2. **All** `replan.md` entries chronologically. On conflict, the latest replan wins.
3. Current `scratchpad.md` — so review doesn't re-raise items already noted there. **Check for prior triage state** under `## Review triage YYYY-MM-DD` headers (see [Triage persistence](#triage-persistence)) and pre-fill dispositions from the most recent block when the underlying finding is re-surfaced.
4. `followups.md` if present — items already deferred.
5. `.minerva/knowledge/` — at minimum entries with `Type: pattern` and `Type: constraint`, since these encode invariants the diff may violate. Skim `Type: decision` and `Type: bug` entries too if the diff touches areas they describe.

### Finding generation

Audit the diff through two lenses (general code quality is owned by `code-review:code-review` — not duplicated here):

- **Spec fidelity** — does the code do what `## Goal`, `## Approach`, and `## Success criteria` (as superseded by the latest replan) promised? Flag missing pieces, scope creep, and approach drift. Treat unmet success criteria as `high` severity.
- **Knowledge compliance** — does the change violate any documented pattern, constraint, or decision in `.minerva/knowledge/`? Cite the specific knowledge file in the finding.

Tag each finding with severity (`high` / `medium` / `low`) and a one-line description. Reference specific files and line numbers.

### Load-bearing divergence

If a finding reveals that the implementation diverged from the proposal in a way that's a different approach (not just a bug), suggest `minerva:replan` instead of (or alongside) a FIX. Same heuristic as `minerva:work`:

- Core assumption from the proposal turned out to be wrong → replan.
- The approach itself changed → replan.
- Scope shifted in or out → replan.
- Routine implementation choice or small edge case → just FIX.

If the user agrees, **persist the in-progress triage first** (see [Triage persistence](#triage-persistence) — flush pending dispositions to scratchpad so they survive the round trip), then exit review and run the `minerva:replan` protocol. Re-enter `minerva:review` once the new plan is in place; prior dispositions will be pre-filled where the same findings re-surface.

## Code review invocation

This always runs — with or without minerva context — on the same diff resolved above.

**Check for an existing PR first:** run `gh pr view --json url,number,state 2>/dev/null`.

- **PR exists and is OPEN** → invoke the `code-review:code-review` skill (via the Skill tool). It will fetch the PR and run its full review flow.
- **No PR (or PR is closed/merged)** → perform a structured inline code quality review using the same finding format the minerva audit uses (severity tag + file:line + one-line description). Inline scope covers, at minimum:
  1. **Bugs** — logic errors, off-by-one, null/undefined handling, race conditions visible in the diff.
  2. **CLAUDE.md / AGENTS.md compliance** — read the agent file once and check the diff against any explicit rules it states (style, security, prohibited patterns).
  3. **Test coverage** — does the diff touch behavior without adding or updating tests? Flag, don't assume.
  4. **Obvious quality** — duplicated logic, dead code introduced, missing error handling at boundaries.

  Do **not** invoke `code-review:code-review` inline — it requires a live PR and will not work against a local diff. Note in the report header that inline mode was used so the user knows the depth is shallower than the PR-mode pass.

## Parallel presentation (when both ran)

When minerva context exists, present findings in two labeled sections before any triage begins:

```
## Minerva audit
[spec fidelity + knowledge compliance findings, numbered starting at 1]

## Code review
[code-review:code-review findings, numbered continuing from minerva audit]
```

Then run a single unified triage pass across all numbered findings from both sections.

When no minerva context exists, the code quality review output is the only result — present and triage it directly.

## Interactive triage

Present findings as a numbered list. For each finding, propose a default disposition and let the user redirect:

- **FIX** — apply a concrete code change. Show the proposed change (file + diff) before writing.
- **SUGGEST** — append a note to `scratchpad.md` so the next `minerva:promote` decides whether it's durable knowledge.
- **IGNORE** — explicitly accept. Optionally log rationale to scratchpad as a `→ accepted` line.

The user can batch ("fix 1-3, ignore 4, suggest 5") or go one at a time. **Hard gate:** do not write any files until the user has confirmed dispositions.

## Triage persistence

Before any disposition is applied — and again any time the triage is interrupted (replan exit, user pause, mid-review crash) — flush the current state to `scratchpad.md` under a `## Review triage YYYY-MM-DD` header:

```markdown
## Review triage YYYY-MM-DD
- [PENDING] #1 high src/foo.ts:42 — missing rate-limit per proposal
- [FIX]     #2 med  src/bar.ts:88 — duplicate validation block
- [IGNORE]  #3 low  src/baz.ts:12 — pre-existing style
```

On re-run, read the **most recent** such block and pre-fill the matching findings' dispositions. Pre-filled items still go through user confirmation (the user can override) but don't have to be re-triaged from scratch. Pending items stay pending — the new run resumes where the old one stopped.

The triage block is a normal scratchpad entry from `minerva:promote`'s point of view (it's neither a `→ promoted` marker nor protected); `promote` will decide whether to discard it as routine noise or merge any FIX summaries into the proposal.

## On approval — file writes

- **FIX items** → make the code edits directly using the editor tools. After each fix, append a one-line entry to `scratchpad.md` so `minerva:promote` can pick it up (e.g. `- Review fix: <file> — <one-line summary>`).
- **SUGGEST items** → append to `scratchpad.md` under a single `## Review finding YYYY-MM-DD` header so they're distinguishable from regular scratchpad noise. One bullet per suggestion. `promote` treats these as MERGE-INTO-PROPOSAL by default (see promote/SKILL.md).
- **IGNORE items** → optional scratchpad entry only if the rationale is non-obvious (e.g. "intentionally skipped tests for X because Y"). Usually skip — silence is the default for ignored findings.

After all dispositions are applied, update the `## Review triage YYYY-MM-DD` block to mark items as `[FIXED]` / `[SUGGESTED]` / `[IGNORED]` so a subsequent re-run can distinguish completed work from pending.

## Report

After writes complete, print a summary:

```
Findings:        N total  (minerva: N, code-review: N)
  Fixed:         N (files: <list>)
  Suggested:     N (logged to scratchpad)
  Ignored:       N
Mode:            PR-driven (code-review:code-review) | inline
Next:            <recommendation>
```

The recommendation:

- **Any FIX or SUGGEST items applied** → recommend `minerva:promote` so the new scratchpad entries get folded into durable knowledge / the proposal.
- **Replan triggered** → recommend `minerva:work` to resume implementation under the new plan, then re-run `minerva:review` afterward.
- **All ignored or zero findings** → recommend `minerva:ship` if implementation is complete, otherwise nothing.

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
