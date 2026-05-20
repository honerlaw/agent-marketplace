---
name: review
description: Use when the user invokes `minerva:review`, asks to review or audit a changeset, or wants to verify shipped code matches what was designed. With a minerva work unit in context, runs a spec/knowledge audit alongside a code quality review, presenting both result sets in parallel before unified triage. Without minerva context, runs a code quality review directly. If a GitHub PR exists for the current branch, delegates the code quality pass to `code-review:code-review`; otherwise performs it inline against the local diff.
---

Review the active changeset for both design compliance and code quality. Works against the local diff — no PR required. When a minerva work unit is found, runs a spec/knowledge audit alongside the code quality review and presents both result sets in parallel before triage. When no minerva context exists, runs the code quality review alone.

## Usage

- `minerva:review` — audits the work unit inferred from current-session context, or the most-recently-modified if context is ambiguous; falls back to a plain code review if no work unit is found

## Target resolution

1. Check current-session chat history for a mentioned work unit. If one is clearly referenced, use it.
2. Fall back to the most-recently-modified `.minerva/work/NNN-*/` by directory mtime.
3. If multiple candidates exist and context is ambiguous, list them and ask the user which to target.
4. `.minerva/work/` missing or empty → **no minerva context**. Skip to [Code review invocation](#code-review-invocation) — do not stop.

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
3. Current `scratchpad.md` — so review doesn't re-raise items already noted there.
4. `.minerva/knowledge/` — at minimum entries with `Type: pattern` and `Type: constraint`, since these encode invariants the diff may violate. Skim `Type: decision` and `Type: bug` entries too if the diff touches areas they describe.

### Finding generation

Audit the diff through two lenses:

- **Spec fidelity** — does the code do what `## Goal` and `## Approach` (as superseded by the latest replan) promised? Flag missing pieces, scope creep, and approach drift.
- **Knowledge compliance** — does the change violate any documented pattern, constraint, or decision in `.minerva/knowledge/`? Cite the specific knowledge file in the finding.

Tag each finding with severity (`high` / `medium` / `low`) and a one-line description. Reference specific files and line numbers.

### Load-bearing divergence

If a finding reveals that the implementation diverged from the proposal in a way that's a different approach (not just a bug), suggest `minerva:replan` instead of (or alongside) a FIX. Same heuristic as `minerva:work`:

- Core assumption from the proposal turned out to be wrong → replan.
- The approach itself changed → replan.
- Scope shifted in or out → replan.
- Routine implementation choice or small edge case → just FIX.

If the user agrees, exit review, run the `minerva:replan` protocol, then re-enter `minerva:review` once the new plan is in place.

## Code review invocation

This always runs — with or without minerva context — on the same diff resolved above.

**Check for an existing PR first:** run `gh pr view --json url,number,state 2>/dev/null`.

- **PR exists and is OPEN** → invoke the `code-review:code-review` skill (via the Skill tool). It will fetch the PR and run its full review flow.
- **No PR (or PR is closed/merged)** → perform the code quality review inline: read the diff directly and check for bugs, CLAUDE.md compliance, and code quality issues. Apply the same severity tagging (`high` / `medium` / `low`) and cite specific files and line numbers. Do not invoke `code-review:code-review` — it requires a live PR and will not work against a local diff.

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

## On approval — file writes

- **FIX items** → make the code edits directly using the editor tools. After each fix, append a one-line entry to `scratchpad.md` so `minerva:promote` can pick it up (e.g. `- Review fix: <file> — <one-line summary>`).
- **SUGGEST items** → append to `scratchpad.md` under a single `## Review finding YYYY-MM-DD` header so they're distinguishable from regular scratchpad noise. One bullet per suggestion.
- **IGNORE items** → optional scratchpad entry only if the rationale is non-obvious (e.g. "intentionally skipped tests for X because Y"). Usually skip — silence is the default for ignored findings.

## Report

After writes complete, print a summary:

```
Findings:        N total  (minerva: N, code-review: N)
  Fixed:         N (files: <list>)
  Suggested:     N (logged to scratchpad)
  Ignored:       N
Next:            <recommendation>
```

The recommendation:

- **Any FIX or SUGGEST items applied** → recommend `minerva:promote` so the new scratchpad entries get folded into durable knowledge / the proposal.
- **Replan triggered** → recommend `minerva:work` to resume implementation under the new plan, then re-run `minerva:review` afterward.
- **All ignored or zero findings** → recommend `minerva:promote` if not already run, otherwise nothing.

## Idempotency

Review is stateless — it does not write its own metadata file. Re-running on the same diff produces the same findings. Safe to cycle:

```
minerva:review  →  fixes applied  →  minerva:promote  →  minerva:review  →  zero findings  →  done
```

## Out of scope

- **Writing to `.minerva/knowledge/` directly.** All durable knowledge goes through `minerva:promote` — one writer, one set of conventions.
- **A `review.md` log file.** FIX outcomes are visible in git; SUGGEST and IGNORE outcomes flow through scratchpad → promote. A standalone log duplicates what those already capture.
- **Scoped review** (e.g. `minerva:review src/api/`). Deferred until the no-scope default proves noisy.
