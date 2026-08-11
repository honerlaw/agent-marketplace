# Proposal: add-review-skill

**Date**: 2026-05-19
**Status**: Shipped (2026-05-19) — record closed retroactively 2026-08-11

## Goal

Add a new `minerva:review` skill that audits the implementation of a work unit against its `proposal.md` (and any `replan.md` entries). It operates on either the current-branch-vs-default-branch diff (when the working tree is clean) or the uncommitted diff (when there are local changes). The skill runs an interactive triage: each finding gets classified as **fix**, **suggest**, or **ignore** via a Q&A flow modeled on `minerva:propose` and `minerva:replan`. The skill is expected to run after `minerva:work` and may cycle with `minerva:promote` (review → promote → review → promote) since findings can change what becomes durable knowledge.

## Why

- `minerva:work` builds what was proposed; `minerva:promote` finalizes durable knowledge. Neither validates that the shipped code actually matches the proposal, honors the latest replan, or respects entries in `.minerva/knowledge/`.
- A dedicated review skill closes the loop **design → implement → audit → promote** and gives the cycle a name so it doesn't get skipped.
- An interactive triage preserves user control: not every finding warrants action, but every finding deserves an explicit disposition (fix / suggest / ignore).
- Findings that become durable (e.g. "we accepted X tradeoff and here's why") flow into the scratchpad and get picked up by the next `minerva:promote` — review naturally produces knowledge artifacts without inventing its own file format.

## Approach

1. **Target resolution** — same pattern as `replan` / `promote` / `work`:
   - Infer the work unit from current-session context; fall back to the most-recently-modified `.minerva/work/NNN-*/` by mtime.
   - Ambiguous → list candidates, ask the user.
   - `.minerva/work/` missing or empty → report and stop.

2. **Diff resolution** — pick what to review:
   - Run `git status --porcelain`. If non-empty → review the working-tree diff (`git diff HEAD` plus untracked files).
   - Else → review the branch diff against the default branch: `git diff $(git merge-base origin/HEAD HEAD)...HEAD`. Detect default branch via `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `main` then `master`.
   - Empty diff (clean tree, on default branch with nothing ahead) → report "nothing to review" and stop.
   - Non-git repo → report and stop.

3. **Context read** — before generating findings:
   - `proposal.md`
   - All `replan.md` entries chronologically (latest replan supersedes proposal on conflict).
   - Current `scratchpad.md` so review doesn't re-raise items the user has already noted.
   - `.minerva/knowledge/` — at minimum entries with `Type: pattern` and `Type: constraint`, which encode invariants the diff may violate.

4. **Finding generation** — audit the diff against three lenses:
   - **Spec fidelity** — does the code do what `## Goal` / `## Approach` (as superseded by the latest replan) promised?
   - **Knowledge compliance** — does the change violate any documented pattern, constraint, or decision in `.minerva/knowledge/`?
   - **General quality** — bugs, missing tests, unhandled edges. Scoped narrow — this isn't a full code review skill; it complements one, not replaces it.

5. **Interactive triage** — present findings as a numbered list, each tagged with severity (high / medium / low) and a one-line description. For each, propose a default disposition and let the user redirect:
   - **FIX** — apply a concrete code change (skill shows the proposed change before writing).
   - **SUGGEST** — append a note to `scratchpad.md` so the next `minerva:promote` decides if it's durable.
   - **IGNORE** — explicitly accept; optionally log rationale to scratchpad as a `→ accepted` entry.

   User can batch ("fix 1-3, ignore 4, suggest 5") or go one at a time. **Hard gate before any writes.**

6. **On approval:**
   - FIX items → make the code edits directly. Log a one-line scratchpad entry per fix so promote can pick it up.
   - SUGGEST items → append to `scratchpad.md` under a `## Review finding YYYY-MM-DD` header so they're distinguishable from regular scratchpad noise.
   - IGNORE items → optional scratchpad entry (only if the rationale is non-obvious — usually skip).
   - Report: counts by disposition, files changed, suggested next step.

7. **Cycle with promote** — if FIX items were applied or SUGGEST notes were added, recommend `minerva:promote` next to fold them into durable knowledge / rewrite the proposal. The user can then re-run `minerva:review` to verify nothing new surfaced after the changes. Review is stateless — no review-specific log file — so re-running is safe.

8. **Load-bearing divergence** — if a finding reveals that what shipped diverged from the proposal in a way that's a different approach (not just a bug), the skill suggests `minerva:replan` instead of (or alongside) a FIX. Mirrors how `minerva:work` handles divergence mid-implementation.

9. **Documentation updates** — part of the work unit, not the skill itself:
   - `plugins/minerva/README.md` — add `minerva:review` to the skills table and the typical-flow diagram.
   - `plugins/minerva/skills/using-minerva/SKILL.md` — add review to the skill decision matrix and at least one common scenario.
   - Root README if it lists minerva skills.
   - `tests/test_minerva.py` — add an existence/frontmatter test for the new skill.

## Open Questions

- **Review log file?** Current plan is stateless. Alternative would be writing `.minerva/work/NNN-<slug>/review.md` with a dated entry per audit pass — like `replan.md` but for audits. Recommendation in this proposal: skip it. Fix outcomes are visible in git; suggest/ignore outcomes flow through scratchpad → promote.
- **Direct writes to `.minerva/knowledge/`?** Could let high-confidence findings short-circuit through review. Recommendation: no — keep `minerva:promote` as the single writer for one set of conventions.
- **Scope flag?** E.g. `minerva:review src/api/` to limit the audit surface. Deferred; ship without it and add if the no-scope default proves noisy.
