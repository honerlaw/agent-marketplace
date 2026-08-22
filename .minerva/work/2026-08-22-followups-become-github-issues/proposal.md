# Proposal: followups-become-github-issues

**Date**: 2026-08-22
**Status**: Shipped (2026-08-22)
**Base**: `origin/main`

## Goal

When `minerva:promote` disposes forward-looking TODO items and the project is a GitHub
repo whose issues we can create, each **keep** item becomes a GitHub issue carrying an
explicit priority (`critical` / `high` / `medium` / `low`). When it is not — no `gh`, not
authenticated, no GitHub remote, issues disabled, or creation itself fails — that item
falls back to today's `followups.md` path, unchanged.

## Why

`followups.md` is a write-only surface. The repo holds 22 of them with roughly 60 items,
and `.minerva/work/2026-08-11-close-the-followups/followups.md` records the reason it
rots: **nothing marks a followup as done**, so every scoping pass re-reads all 22 files to
re-derive which items already shipped. A GitHub issue has the state the file lacks — it
closes, it is assignable, it is filterable — and a priority label makes "what should we do
next" answerable without reading prose.

The fallback is not a concession; it is what keeps minerva project-agnostic. A repo with
no GitHub remote must behave exactly as it does today.

## Approach

**Issue-first, with a deterministic capability probe and per-item fail-soft.**

1. **Capability probe (once, before the disposition gate).**
   `gh repo view --json nameWithOwner,hasIssuesEnabled`. A non-zero exit (no `gh`, not
   authenticated, no GitHub remote) or `hasIssuesEnabled: false` sends the whole gate down
   the `followups.md` path. `viewerPermission` is deliberately **not** consulted: on GitHub
   anyone with read access can open an issue when issues are enabled, so gating on
   `WRITE`+ would wrongly force capable outside contributors onto the file path. The real
   permission check is the creation attempt itself, caught by fail-soft below.

2. **Priority.** The model **proposes** a level per item; the levels are defined verbatim
   in the skill so assignment is consistent, and the proposal is shown at Mode A's existing
   step-6 hard gate where it can be corrected before anything is created:
   - `critical` — should be done before anything else.
   - `high` — should be done as soon as possible.
   - `medium` — should be done eventually.
   - `low` — does not matter whether it is done.

3. **Issue shape.** Title = the item's one-line headline. Body = the item's full prose, a
   `**Priority**: <level>` line with that level's definition, and a back-link to the source
   work unit `.minerva/work/<date-slug>/`. Labels = `priority: <level>` plus the marker
   label `minerva:followup`, each created on demand if absent.

4. **Idempotency, in three sources.** Issue creation is the only externally-visible side
   effect promote has, and a duplicate is a notification on someone's repo. The check reads
   the run's own record first, then the unit's `proposal.md` `## Deferred work` section,
   and only then a repository search. The search cannot be the authority: GitHub's search
   index is not synchronous with creation, so it is blindest in exactly the
   retry-after-partial-failure window the check exists for — see
   [[2026-08-22-pattern-a-just-written-index-is-not-a-read-back-guarantee]].

5. **Fail-soft, expressed in the code.** `ensure_label` returns non-zero when a label is
   unusable and the caller builds a `USABLE` flag array from what succeeded, so a repo
   where the caller can open issues but not manage labels degrades to the body
   `**Priority**:` line alone rather than depending on the executor's shell settings. Any
   `gh issue create` failure drops **that item** to `followups.md` verbatim. Nothing is
   ever lost.

6. **Durable record.** Created issue URLs are written to the unit's `proposal.md` under a
   `## Deferred work` section. This is a historical fact ("this unit deferred X to #12")
   that cannot go stale the way `followups.md`'s "here is open work" does.

7. **Read path.** Deferred work only stays discoverable if its consumers can see it, so the
   skills that read `followups.md` today learn to also read
   `gh issue list --label minerva:followup --state open`. Grep establishes who those
   actually are: `minerva:review` and the three `propose-ship-*` orchestrators (each at
   both its *Assemble/Read context* step and its TODO-disposition step). Plain
   `minerva:propose` does **not** read `followups.md`, despite `modes.md` claiming it does
   — that stale claim is corrected here.

### Rejected alternatives

- **`followups.md` as a receipt index** (one pointer line per created issue). Keeps the
  existing grep surface untouched, but re-creates the staleness it is meant to fix: the
  pointer says "open work" forever, including after the issue closes.
- **Priority in the title only, no labels.** Simpler and side-effect-free, but the marker
  label is exactly what makes the read path cheap. Approach 1 already degrades to roughly
  this when label creation fails.
- **Defer the read path to a fast-follow.** Would ship a create path whose output no
  consumer reads — the blind spot the scope review independently flagged.

### Known tradeoff

Issues are created on the work-unit branch, before the PR merges. If the PR is abandoned,
the issues outlive it, where a `followups.md` would have vanished with the branch. Accepted:
an orphaned issue naming its source unit is a better failure than silently losing the item.

## Success criteria

1. `plugins/minerva/skills/promote/references/github-issues.md` exists and contains the
   concrete capability probe, the `gh issue create` invocation, the four priority
   definitions verbatim, on-demand label creation with its fallback, the pre-create
   duplicate search, and the per-item fail-soft — commands, not prose descriptions of
   commands (`2026-05-19-constraint-skills-must-call-tools-not-prose`).
2. `promote/references/modes.md` step 5 offers the issue path as the default when the probe
   says capable, still offers keep/seed/discard, and no longer claims `minerva:propose`
   scans `followups.md`. Steps 7 and 8 record issue URLs in `proposal.md` under
   `## Deferred work` and report them.
3. All three `propose-ship-*/references/phases.md` name the issue path at **both** their
   context-read steps and their TODO-disposition step.
4. `review/references/protocol.md`'s context read includes open `minerva:followup` issues.
5. Catalog surfaces carry the two-path behavior: `plugins/minerva/README.md` (rows 10, 28,
   72), `using-minerva/references/guide.md` (rows 9, 45), `pages/index.md` (row 40). No
   surviving surface describes `followups.md` as the only sink for TODOs.
6. Structural-contract anchors are added for `promote`, `review`, and the three
   orchestrators, so the behavior is test-enforced rather than aspirational
   (`2026-08-11-pattern-an-unenforced-constraint-is-aspirational`).
7. The full test suite passes.

## Open questions

None outstanding. The two propose-phase reviewer gates resolved the priority-authorship
gap, the `viewerPermission` mis-gate, the idempotency gap, and the consumer list.

## Deferred work

Filed by this unit's own promote run — the feature's first live exercise, on
`honerlaw/agent-marketplace`:

- #69 — Triage the existing followups.md backlog and file the survivors as issues (priority: medium)
- #70 — Guard tests/test_skill_snippets.py against extracting mutating gh blocks (priority: medium)
- #71 — Have minerva:cleanup close minerva:followup issues whose work has shipped (priority: low)
