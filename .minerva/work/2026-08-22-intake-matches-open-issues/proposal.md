# Proposal: intake-matches-open-issues

**Date**: 2026-08-22
**Status**: Draft

## Goal

At work-unit intake, minerva checks the repo's **open** GitHub issues for one that would be
satisfied by the change the user just asked for, and — when it finds one — asks whether to
execute that issue instead. On adoption the unit records `**Closes**: #NN` in its
`proposal.md`, so the PR that ships the work closes the issue.

## Why

`minerva:promote` files kept TODOs as prioritized GitHub issues, and `minerva:backfill-followups`
migrated the historical `followups.md` backlog into the same tracker. That backlog is now real,
and nothing reads it at **intake**. A user who asks for X, unaware that issue #NN already tracks
X, gets a duplicate work unit — and #NN stays open forever, because nothing but an authored
`**Closes**` field ever closes a `minerva:followup` issue.

The gap is narrow and specific. The three inline orchestrators already *read* open followup
issues in their Phase 1 "assemble context" step, but only as background colour: there is no
matching step, no offer, and no path from "this request is issue #NN" to the durable record.
The close-half of the loop was built by unit `2026-08-22-close-open-issue-backlog` and works
end to end (`proposal.md`'s `**Closes**` field → `minerva:ship`'s per-entry `Closes #N` lines).
This unit builds the open-half: the intake match-and-offer that feeds it.

## Approach

One canonical protocol file, cited by every intake surface — no duplicated `gh` prose, no new
skill.

1. **New `plugins/minerva/skills/propose/references/issue-match.md`** — the whole protocol:
   - **Skip clause (idempotency).** If the incoming inline argument already names an adopted
     issue (`#NN`), skip the query — an `explore` → `propose` handoff must not ask twice.
   - **Capability probe.** Delegated to `minerva:promote`'s "Step 1 — Capability probe (once per
     promote run)"; a non-zero exit or `hasIssuesEnabled: false` **silently skips** the whole
     check. No `gh` is the common case elsewhere and must never block a proposal.
   - **Query.** `gh issue list --state open --limit 100 --json number,title,labels,updatedAt`,
     reading a body with `gh issue view` only for plausible candidates, plus a
     `--search`-keyword pass when the list hits the cap.
   - **Match bar, stated behaviorally.** A **match** is an issue whose stated outcome and the
     user's request would be satisfied by substantially the same change. Same subsystem or same
     theme is *not* a match. Unsure resolves to **adjacent** — surfaced in one line, never
     offered. The asymmetry is deliberate: a false offer derails an intake and re-litigates a
     settled request, while a missed match costs a duplicate that `minerva:promote` can still
     close by authoring `**Closes**` at end-of-work.
   - **Response shape, graded by surface.** At the convergent surfaces (`propose` and the three
     orchestrators) a match is a real `AskUserQuestion` offer — execute #NN instead / proceed as
     asked and link #NN / adopt #NN and extend it. At `explore` it is **information in the
     dialogue only**: explore's own protocol says "resist jumping to solutions", so an adoption
     gate there would convert a commitment-free exploration into a premature commitment. Explore
     defers adoption to the handoff, passing `"<direction> (adopting #NN)"` as the inline
     argument — the pinned format the skip clause detects.
   - **What adoption records.** The issue's title and body seed `## Goal`/`## Why`, and
     `**Closes**: #NN` is written into `proposal.md` at creation.
2. **`propose/SKILL.md`** — the intake step points at the reference with a read directive.
3. **`propose/references/on-approval.md`** — the `**Closes**` paragraph currently says the field
   is "normally absent at propose time"; an adopted issue is the documented exception.
4. **`explore/SKILL.md`** — the check fires where directions are weighed, not at first context
   read: a fuzzy idea has nothing concrete to match against, and a semantic match judged against
   a half-formed problem statement is exactly the false positive the match bar exists to avoid.
5. **The three orchestrators' `references/phases.md`** — Phase 1 gains the intake step, citing
   the protocol by the qualified path form. The ask **increments the run's escalation counter**,
   like every other hardcoded escalation those skills define; it is not exempt.
6. **`tests/test_skill_budget.py`** — the pointer-resolution and malformed-pointer checks read
   only `SKILL.md`, so a qualified pointer written inside a `references/*.md` file is invisible
   to them. Since this unit's own orchestrator citations live in `phases.md` (their cores have
   no byte headroom), the guard is extended to scan reference files too — otherwise the wiring
   this unit adds is unprotected against a later rename.
7. **Four pre-existing dangling pointers** that the extended guard immediately catches — three
   `phases.md` files and one `verify-protocol.md` citing `references/github-issues.md` /
   `references/briefs.md` unqualified, which resolve under the *citing* skill and do not exist
   there — are rewritten in the qualified form.
8. **Five `evals/*/contract.json` files** gain anchors for the new prose, so the wiring cannot
   rot silently.

**Rejected alternatives.** *Restating the check inline at all five surfaces* — five copies of one
`gh` protocol drift, the failure `2026-07-21-pattern-catalog-semantic-drift-recurs` and
`2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant` both describe. *A dedicated
`minerva:match-issue` skill* — a new skill costs four catalog surfaces, a contract, evals and an
invocation hop, for one bounded protocol whose consumer set is fixed and internal;
`minerva:backfill-followups` makes this same argument against splitting a tool whose only
consumer is its own caller.

## Success criteria

- `plugins/minerva/skills/propose/references/issue-match.md` exists and specifies, each in its
  own section: the skip clause, the capability probe (by citation, not restatement), the query,
  the match/adjacent bar, both response shapes, and what adoption records.
- `propose/SKILL.md` mentions `references/issue-match.md` on a line carrying a read directive.
- `explore/SKILL.md` and all three of `propose-ship-quick`/`-balanced`/`-auto`'s
  `references/phases.md` cite the protocol by the qualified
  `plugins/minerva/skills/propose/references/issue-match.md` form.
- `propose/references/on-approval.md`'s `**Closes**` paragraph states the adopted-issue exception.
- Each orchestrator's `phases.md` states that the ask increments the escalation counter.
- `tests/test_skill_budget.py` resolves reference pointers inside `references/*.md` files as well
  as `SKILL.md`, and carries negative coverage that fires on a dangling pointer written in a
  reference file.
- The four pre-existing unqualified cross-skill pointers are qualified; the extended check passes
  across the whole corpus.
- The five updated `evals/*/contract.json` anchors pass `tests/test_skill_contracts.py`.
- `propose/references/on-approval.md` documents the `**Linked**` field beside `**Closes**`, and
  `issue-match.md`'s "proceed as asked" branch writes it (see `replan.md`).
- `promote/references/modes.md` states both rules and their asymmetry: a pre-existing `**Closes**`
  entry is re-verified and amended-or-dropped; a `**Linked**` entry is added only if warranted.
- `ship/references/protocol.md` re-verifies each `Closes` entry against the diff before emitting it,
  drops unsupported entries, and reports the drop.
- Each orchestrator's decision taxonomy and hardcoded-trigger list names the intake open-issue match.
- The full pytest suite passes.

## Open Questions

- None blocking. `minerva:debug` is deliberately excluded (it never ships a diff, so it cannot
  close an issue); whether a bug report should be matched against open issues is filed as a TODO
  at promote time rather than decided here.
