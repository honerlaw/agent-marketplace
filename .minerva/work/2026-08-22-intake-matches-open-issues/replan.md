# Replan: intake-matches-open-issues

## Replan 2026-08-22 — a pre-written `**Closes**` field is a claim, not a fact

**Original plan.** Intake adoption writes `**Closes**: #NN` into `proposal.md` at creation. The
proposal's eight Approach steps touched only `propose/`, `explore/`, the three orchestrators'
`phases.md`, and `tests/test_skill_budget.py`; `## Why` treated the close-half of the loop as
already built and working end to end, so neither `minerva:promote` nor `minerva:ship` was in scope.

**What changed.** The plumbing does still exist and still works — but a precondition implicit in it
changed underneath. Until now `**Closes**` could only be authored at end-of-work, by whoever wrote
the diff, so every consumer could treat a present field as already verified against real code.
Adoption at intake creates a field that **predates the diff**, and review surfaced three holes:

- (a) If the work drifts — a replan, a narrowed scope, an abandoned half — nothing re-checks the
  pre-written claim. `minerva:promote`'s Closes step ("author the field if this unit's diff resolves
  any open issues") was written for an empty field, not a pre-filled one.
- (b) `minerva:ship` reads the field mechanically and by design never inspects the diff, and it
  explicitly permits shipping without promote ("the user can ship and skip — strict ordering is not
  enforced"). So `propose(adopt #NN)` → `work` → `ship` closes #NN on merge with the claim never
  checked by anyone. This bites hardest in the autonomous orchestrators, which auto-accept ship's
  PR-body gate — the one place a human would otherwise have seen the `Closes` line.
- (c) The "proceed as asked, link #NN" branch told the executor to record the issue for promote to
  judge later, but named no field and no file — so nothing reaches promote and the linked issue
  stays open, which is the problem this unit exists to close.

**New plan.** Scope grows by two files, and the record for (c) becomes a proposal field rather than
a scratchpad line.

1. **`proposal.md` gains an optional `**Linked**` field**, documented in `on-approval.md` beside
   `**Closes**`: `**Linked**: #NN — <title> (not adopted)`. A scratchpad line was the first draft
   and was rejected — `minerva:promote` Mode A runs every scratchpad entry through a
   PROMOTE/MERGE/DISCARD/TODO partition whose only documented exemption is the `→ promoted to`
   marker, so a bare link line reads as partition fodder and is most naturally DISCARDed before the
   Closes step ever sees it. A proposal field is read directly, is written at the moment
   `on-approval.md` already creates the file, and mirrors the convention `**Closes**` set.
2. **`issue-match.md`'s "proceed as asked" branch names that field** instead of "record the issue".
3. **`promote/references/modes.md`** — two rules, and they are deliberately not symmetric: a
   **pre-existing `**Closes**` value is a claim to re-verify against the diff** (amend it, or drop
   it, when the diff no longer resolves the issue — amend-or-drop), while a **`**Linked**` value is
   a candidate to promote into `**Closes**` only if the diff did resolve it (add-if-warranted).
4. **`ship/references/protocol.md`** — before emitting the `Closes #N` lines, confirm each listed
   issue is actually resolved by the diff being shipped; drop the ones that are not and say so in
   the report. This is the only fix that covers the ship-without-promote path. It does **not**
   contradict the field's "authored, never inferred" rule: inferring means *adding* issues the
   author did not list, which stays forbidden. Dropping an unsupported claim runs the other way, in
   the direction the field's own asymmetry already points — a stale-open issue is cheap, a wrong
   auto-close destroys a real record.

**Success criteria gained.**
- `on-approval.md` documents the `**Linked**` field beside `**Closes**`, and `issue-match.md`'s
  "proceed as asked" branch writes it.
- `promote/references/modes.md` states both rules and their asymmetry (amend-or-drop vs.
  add-if-warranted).
- `ship/references/protocol.md` re-verifies each `Closes` entry against the diff before emitting it,
  drops unsupported entries, and reports the drop.
