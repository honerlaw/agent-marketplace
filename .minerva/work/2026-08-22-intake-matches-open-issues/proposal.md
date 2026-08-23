# Proposal: intake-matches-open-issues

**Date**: 2026-08-22
**Status**: Shipped (2026-08-22)

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

One canonical protocol file, cited by every intake surface — no duplicated `gh` prose, no new skill.
Review then pulled two more files into scope; see `replan.md` for why.

1. **`plugins/minerva/skills/propose/references/issue-match.md`** holds the whole protocol: a skip
   clause (an inline argument already naming `#NN` means the decision is made — an
   `explore` → `propose` handoff must not ask twice); a capability probe delegated to
   `minerva:promote`'s, which silently skips the check where no issue tracker is reachable; the
   query (`gh issue list --state open`, bodies read only for plausible candidates, a `--search`
   pass when the list hits the cap); a behavioral match bar; the response shapes; and what
   adoption records.
2. **The match bar is stated behaviorally.** A **match** is an issue the user's request would
   resolve with substantially the same change; same subsystem or theme is *not* a match, and
   unsure resolves to **adjacent** — one informational line, no question. The asymmetry is the
   point: a false offer derails an intake and makes the user re-litigate a settled request, while
   a missed match costs a duplicate that promote can still close at end-of-work.
3. **The response is graded by surface.** `propose` and the three orchestrators put a real
   `AskUserQuestion` gate on a match (execute the issue instead / proceed as asked and link it /
   adopt and extend, with several matches offered together). `explore` gets information only —
   its protocol says to resist jumping to solutions, so an adoption gate mid-exploration would
   force a commitment before any direction was weighed. Explore defers to the handoff, passing
   `"<direction> (adopting #NN)"`, which the skip clause detects.
4. **In the autonomous orchestrators the ask is hardcoded** — it fires regardless of the run's own
   skip or verify predicates, like the in-flight-work collision — and it **increments the run's
   escalation counter**, like every other escalation those skills count. An early draft exempted
   it on the belief that the in-flight precedent was exempt; it is not. Each orchestrator's
   decision taxonomy and hardcoded-trigger list now names this decision point, so the
   enumerations do not lag what `phases.md` asserts.
5. **Adoption writes `**Closes**: #NN` at creation**, and a match the user declined to adopt writes
   the new sibling field `**Linked**: #NN — <title> (not adopted)`. Both are documented in
   `on-approval.md`. `**Linked**` replaced a first draft that recorded the issue as a scratchpad
   line: promote Mode A runs every scratchpad entry through a four-way partition whose only
   documented exemption is the `→ promoted to` marker, so a bare link line would most naturally
   have been discarded before anything read it.
6. **Both consumers of `**Closes**` re-verify it**, because moving the authoring point to intake
   turned the field into a claim that predates its evidence. `promote/references/modes.md` gains
   amend-or-drop for `**Closes**` and add-if-warranted for `**Linked**`;
   `ship/references/protocol.md` re-checks each entry against the diff before emitting it and
   reports what it dropped. Ship is not optional cover: it documents that a user may ship without
   promote, and the autonomous orchestrators auto-accept its PR-body gate.
7. **`tests/test_skill_budget.py`'s pointer-integrity scan widened** from `SKILL.md` to
   `SKILL.md` + `references/*.md`, since this unit's own cross-skill citations live in `phases.md`
   (the orchestrator cores have no byte headroom) and were otherwise unguarded against a rename.
   Widening it immediately caught **four pre-existing dangling pointers** — three orchestrators
   citing `references/github-issues.md` and one citing `references/briefs.md` unqualified, all of
   which resolved against the citing skill, where no such file exists — now written in the
   qualified form. Both widened checks read unfenced text, and a new test pins the scan's scope so
   narrowing `skill_docs` back to the core cannot pass silently.
8. **Five `evals/*/contract.json` files gained anchors** for the new prose, so the wiring cannot rot
   silently.

**Rejected alternatives.** *Restating the check inline at all five surfaces* — five copies of one
`gh` protocol drift. *A dedicated `minerva:match-issue` skill* — a new skill costs four catalog
surfaces, a contract, evals and an invocation hop, for one bounded protocol whose consumer set is
fixed and internal.

## Deferred work

- Match a reported bug against open issues in `minerva:debug` — filed as
  [#94](https://github.com/honerlaw/agent-marketplace/issues/94) (`priority: medium`).

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
