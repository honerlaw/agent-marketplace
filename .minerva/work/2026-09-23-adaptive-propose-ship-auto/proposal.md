# Proposal: adaptive-propose-ship-auto

**Date**: 2026-09-23
**Status**: Shipped (2026-09-23)

## Goal

`minerva:propose-ship-auto` becomes the single autonomous orchestrator. At **each** decision it picks
the adjudication tier the decision earns — **solo** (main model decides), **reviewer** (one
fresh-context Skeptic/Verifier + one fold-audit re-check, balanced's mechanism), or **panel** (3-agent
`minerva:round-table`) — and moves **up a tier** instead of stopping the run. `propose-ship-quick` and
`propose-ship-balanced` are deleted outright (user decision: no aliases). `propose-ship` (human gates)
is unchanged. The skill name `propose-ship-auto` is kept (user decision).

## Why

The user asks for balanced work and the run keeps stopping to recommend switching to
`propose-ship-auto`. That comes from balanced's (and quick's) **scope-fit escape**: when a change looks
bigger than the rung, the only move the skill has is to bail and recommend a sibling. Three skills with
near-identical lifecycles (~1,000 lines across SKILL.md + governance/phases/protocol refs) also force
the user to pre-classify every task, which is exactly the whole-run sizing call
`2026-05-31-decision-per-decision-skip-over-sizing-gate` rejected — just made by a human at skill-pick
time instead of by the model.

`2026-09-05-decision-balanced-rechecks-its-folds` named this collapse as "cleanest end state, largest
blast radius; revisit once telemetry makes the case measurable." The user has now asked for it.

## Approach (recommended: A)

**Tier selection is per decision, fail-closed upward. No whole-run size estimate.**
(An intake size estimate was floated in chat; it is dropped because it is the up-front classifier
`2026-05-31` rejected — it judges on the seed, blind to the load-bearing decision that emerges
mid-run.)

**Decide first, then route.** The main model drafts the decision (scope cut, chosen approach,
checklist, dispositions) exactly as it would solo, then selects the tier for *that drafted decision*,
in order. Tier selection reads the draft, so ambiguity that only surfaces while deciding is caught;
a reviewer reads the committed decision with no confirmation bias (balanced's decide-first rationale):

1. **Hardcoded triggers → user** (unchanged: in-flight collision, open-issue match, worktree failure,
   ship `other`/push/auth failures, counter at 3).
2. **Panel predicate → panel** (or the row's ceiling, if lower — see below). If any clause holds, or the model is unsure whether it holds:
   genuine ambiguity (≥2 viable options enumerated, none dominant), high blast-radius / irreversible,
   new or changed public interface / cross-cutting contract, tension with a `.minerva/knowledge/`
   constraint. (This is quick/balanced's former *user*-escalation predicate, re-pointed at the panel.)
3. **Solo predicate → solo**, only on a row whose floor allows it: auto's existing conjunctive
   fail-closed skip predicate (additive, mechanically verifiable, single-surface, no new interface, no
   knowledge conflict, and for approach decisions ≥2 enumerated with one strictly dominant).
4. **Otherwise → reviewer.** This is the default middle.

**Per-row floors and ceilings (taxonomy columns).** The floor and ceiling bound whatever steps 2–4
select: a row's ceiling **overrides** step 2 (on a row capped at reviewer, a holding panel predicate
routes to reviewer), and its floor overrides step 3 (on a row floored at reviewer, a holding solo
predicate still routes to reviewer).
- **Divergence confirmation, new-plan acceptance, replan-vs-FIX** — floor **panel**, exactly as
  auto runs them today (`Skippable? No`). Their precondition is an already-surfaced load-bearing
  divergence or finding, they fire rarely, and there is no evidence to justify lowering them.
- **Completion verification** — floor **reviewer** (the Verifier brief), panel when the panel
  predicate holds. This is the one never-elide row lowered from auto's panel, on evidence: 0 of 18 auto
  completion panels went to a revision round (`2026-09-05`); its value is independent *reproduction*
  of each criterion, which a single Verifier does (`2026-06-29`).
- **Review triage, promote partition, TODO disposition** — these rows do **not** run steps 3–4.
  A disposition is a judgment call by nature, so the strict solo predicate (which demands mechanical
  evidence) would never pass and every item would fall to reviewer. Instead: **solo** unless the
  panel predicate holds, then **reviewer** (the ceiling). On these rows the clause that realistically fires is
  ambiguity: an item with two defensible dispositions and none dominant (FIX vs SUGGEST on a finding,
  PROMOTE vs DISCARD on an entry); the knowledge-conflict clause fires when a disposition would
  contradict an entry. They never fall
  through to a reviewer by default and never convene a panel: balanced ran them solo on cost grounds,
  and triage already has an independent finding set from code review.
- **Scope, approach, whole-proposal** — the full ladder: solo only when the strict solo predicate holds;
  reviewer otherwise; panel when the panel predicate holds. The revision evidence (auto: approach
  17/25, whole-proposal 13/27, scope 7/22 panel calls went to a revision round) was measured on panels
  that had **already failed** auto's skip predicate — it supports "reviewer whenever the solo predicate
  fails", which is exactly this row, not "reviewer even on a provably trivial decision".

**The Verifier gate is asymmetric, as in balanced (`2026-09-05`).** At completion the reviewer is a
Verifier: one dispatch, **no** fold-audit re-check and **no** anti-circularity escape. A Verifier
`revise`/`reject` naming an unmet criterion is a success-criteria divergence and goes to Phase 2.5
(replan), whose new-plan acceptance has a panel floor. That loop is its re-check. The upward moves
and the ≤2-dispatch reviewer budget below apply to **Skeptic** gates only.

**Upward moves within a decision (never sideways to another skill):**
- reviewer's anti-circularity escape (a load-bearing critique the main model can't confidently
  adjudicate) → **panel** (was: user)
- fold-audit re-check finds a load-bearing item unaddressed/regressed → **panel** (was: user)
- panel fails quorum after its one revision round → **user** (unchanged round-table escalation)
- on a row whose **ceiling is reviewer** (triage, partition, TODO), an upward move that would reach a
  panel goes to the **user** instead. The ceiling wins; these rows never convene a panel.

This does **not** revive the arm `2026-09-05` rejected ("decide → Skeptic → round-table", no honest
trigger): the up-arm keys only on the two events that previously went to the user — never on a Skeptic
`revise` (30/35 rate) — so it replaces a user question with a panel, it does not add dispatches to the
common path.

**What a panel receives on an upward move.** ARTIFACT = the decision as it now stands (the revised
decision after a fold). CONTEXT adds, as enumerated items beyond round-table's usual list, the
original decision, the reviewer's critique verbatim, and the fold-audit disposition if one ran. The
panel is judging whether the current decision is sound given that history, not re-deriving it from a
blank page, and the history is evidence a fail-closed design keeps.

**Scope-fit escape deleted.** A change that grows mid-run makes its later decisions fail the solo
predicate and hit the panel predicate on blast radius; nothing needs to switch skills.

**Parked dispatches.** Per `2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch`, a
reviewer or panel dispatch may run in the background regardless of the synchronous pin. Every tier's
protocol is written to survive that: dispatch, end the turn if the result is not back, resume on the
completion notification, then arbitrate. Never skip a tier to avoid a park.

**Budget per decision:** reviewer ≤2 dispatches; + panel ≤6 if escalated; hard max 8. Global escalation
counter (user escalations) halts at 3, unchanged. Propose-phase abort keeps auto's existing trigger:
when 2 of the 3 propose decisions reach the user. Because most former user escalations now route
through a panel first, this should fire *less* often than in quick/balanced — re-measure, below.

**Re-measure.** The up-arm's trigger rates are not yet measured (anti-circularity fired 0 times in 13
balanced runs; fold-audit escalations have ~3 weeks of history). The claim "the up-arm adds no
dispatches to the common path" is therefore a prediction. `decision_telemetry.py` reports tier ×
gate × outcome, and the taxonomy is revisited via `minerva:replan` once ~10 runs have logged. That revisit also checks
whether the propose-phase abort has gone inert; if it has, it is re-keyed (e.g. to panel quorum
failures) rather than left as dead text.

**Summary table.** `decision-protocol.md` carries the taxonomy as one table, row × default ×
floor × ceiling × reviewer brief, so cross-row interactions are read off it rather than reconstructed
from prose. Every carve-out above is a column value there.

**Logging:** one header `## Decisions YYYY-MM-DD`; each line starts with the tier and outcome and ends
with why that tier:
`[solo] …`, `[reviewed — clean|folded] …`, `[rechecked — clean|residual folded|escalated] …`,
`[panel — 3/3 accept|2/3 accept, …] …` (a vote counted from `accept with fixes` renders as
`[panel — 3/3 accept, 1 with fixes]`, with each folded fix on an indented line beneath), `[escalated to user] …`, `[user-directed] …` — plus a
`(tier: <why>)` suffix. A `[solo]` line on a row that could have gone higher must record the
**concrete evidence** that satisfied the solo predicate, exactly as auto's `[skipped — small]` does
today, so review/promote can audit that it was honest. A `[solo]` line on a default-solo row
(triage, partition, TODO) has no predicate to cite; it records the disposition counts and why no
item met the ambiguity clause. `decision_telemetry.py` gains this header with a closed vocabulary and keeps
parsing the legacy `Panel/Balanced/Quick` headers for historical units.

**Panels vote on the decision, not the write-up (user-approved addition).** Both propose panels of
the run that designed this unit deadlocked at a 3/3 quorum although every panelist agreed on the
decision: the `revise` votes asked for a corrected citation, a relabelled count and clarifying
sentences. `minerva:round-table` gains a fourth verdict, **`accept with fixes`**: *the decision is
right; these listed write-up fixes are needed.* It counts as `accept` toward quorum. The main model
folds the listed fixes without a re-vote and logs each under the panel line. `revise` is reserved for
*the decision should change*. A listed fix that would change the decision is a `revise`: if the main
model finds one — **or is unsure whether it would** — it counts that vote as `revise` (fail-closed,
like every other predicate here). Each folded fix is logged verbatim under the panel line so review can
audit that none changed the decision.

The reviewer tier's Skeptic brief keeps its three verdicts on purpose. There is no quorum to protect
there: the main model already arbitrates each critique item as load-bearing or not, which is the same
distinction `accept with fixes` draws for a vote. This applies in both caller mode and standalone.

**Files:**
- `propose-ship-auto/SKILL.md` + description rewritten; `references/panel-protocol.md` replaced by
  `references/decision-protocol.md` (tier selection, predicates, floors, reviewer mechanism + Skeptic /
  Verifier / fold-audit briefs moved from balanced, round-table delegation, logging, taxonomy);
  `phases.md` + `governance.md` updated per gate.
- `round-table/SKILL.md` vote semantics + `references/briefs.md` (the three verdict lines) for
  `accept with fixes`.
- Delete `skills/propose-ship-quick/`, `skills/propose-ship-balanced/`, `evals/propose-ship-quick/`,
  `evals/propose-ship-balanced/`.
- Update references: `using-minerva/SKILL.md` routing rows, `propose-ship/SKILL.md` ladder prose,
  `propose/references/issue-match.md`, `ship/references/protocol.md` example, `README.md`,
  `plugins/minerva/README.md`, `pages/index.md`, `minerva_runtime.py` CALLERS (legacy callers kept
  readable so an in-flight checkpoint still resumes, rendered as `propose-ship-auto`),
  `scripts/run_compatibility_evals.py` scenarios, and the tests that enumerate orchestrators
  (`skills_corpus.py`, `test_skill_contracts.py`, `test_skill_dispatch.py`,
  `test_decision_telemetry.py`, `test_cross_session_contract.py`, `test_minerva_runtime.py`,
  `test_compatibility_evals.py`, `test_deferral_bar.py`, `test_phase_continuation.py`).
  Balanced-specific invariants (re-check cap, no one-dispatch cap) are ported to auto, not dropped.

**Scope (decided — user, after a deadlocked 3/3 panel): one unit, one PR, no phases.** Size: of
1,158 current orchestrator lines, 573 are deleted outright (quick's 338 + balanced minus
`verify-protocol.md`); 585 (auto's 380 + balanced's 205-line `verify-protocol.md`) merge into auto's
rewritten files. The review burden is `decision-protocol.md`. Two non-mechanical pockets beyond it:
- `tests/test_cross_session_contract.py`'s shared 9,216-byte pointer-SKILL.md budget — balanced was
  the binding file (51 bytes headroom); the rewritten auto `SKILL.md` must be re-checked against it
  and the docstring naming balanced updated.
- `evals/propose-ship-auto/contract.json` anchors must gain the migrated concepts (Verifier,
  fold-audit, tier selection), not merely lose sibling names.

**As built — additions from review.**
- The anti-circularity escape logs `[reviewed — escalated]`. Round-table's vote line under
  `## Decisions` is prefixed `panel — `, and telemetry also reads the bare form.
- `minerva_runtime.canonical_caller()` treats legacy `propose-ship-quick` / `-balanced` checkpoint
  callers as `propose-ship-auto` both when rendering the resume prompt and in the "caller cannot
  change" check. New progress can no longer be started with a legacy caller.
- The completion panel's pre-existing "2/3 proceeds with dissent logged" behavior is stated as an
  explicit exception to its 3/3 quorum.
- Host adapters pin `model: sonnet` for reviewer-tier agents (Skeptic, fold-audit, Verifier).
- `evals/propose-ship-auto/contract.json` anchors tier selection, the Verifier asymmetry, the
  fold-audit and no-whole-run-sizing.
- The compatibility evals replace `quick` with `auto-small` and drop `balanced`. Both auto scenarios
  require ≥1 independent dispatch (the Verifier floor). That the evals reach no reviewer-default or
  panel-tier decision is recorded as a standing fact, not filed.
- minerva is now 2.0.0, since two public skills were removed.

## Candidate approaches considered

- **A (recommended) — reviewer-default router** as above: solo when provably small, panel when the
  panel predicate holds, reviewer otherwise.
- **B — panel-default with a reviewer skip.** Keep auto's panel as default and add "reviewer" as an
  intermediate skip. Smallest diff to auto, but the common medium decision still convenes a panel
  (~11–22 dispatches/run per 2026-09-05), which is the cost balanced existed to avoid.
- **C — solo-default ladder (quick's engine).** Decide solo unless quick's *escalation* predicate
  trips (ambiguity, blast radius, interface, knowledge conflict), and only then add a reviewer.
  Quick's escalation predicate and auto's skip predicate test largely the same properties from
  opposite defaults (interface, knowledge conflict, blast radius / additivity), so a decision that
  clears quick's predicate but fails auto's is one that is unambiguous yet not provably small.
  The difference from A is the default for a decision that is **non-trivial but unambiguous**: C
  decides it alone, A reviews it. That is precisely the population where the evidence says independent
  review changes outcomes (the 17/25 and 13/27 revision rounds, 30/35 balanced folds), so C is
  rejected. A reaches solo only through the strict conjunctive predicate.

## Success criteria

1. `skills/propose-ship-quick/`, `skills/propose-ship-balanced/` and their `evals/` fixtures are gone;
   no plugin skill, README, docs page or script names them except explicitly-marked legacy
   compatibility (telemetry legacy headers, runtime legacy caller mapping).
2. `propose-ship-auto`'s references define per-decision tier selection (hardcoded → panel predicate →
   solo predicate → reviewer), the per-row floors/ceilings (panel floor on divergence / new-plan /
   replan-vs-FIX, reviewer floor on completion, reviewer ceiling on triage / partition / TODO), and
   the upward moves reviewer → panel → user; no skill prose recommends switching to another orchestrator mid-run.
3. No whole-run sizing step exists; tier is chosen per decision.
4. One `## Decisions` header; `decision_telemetry.py` classifies every tag in auto's fenced logging
   example and still parses legacy headers.
5. `using-minerva` routing names one autonomous orchestrator. The skill-budget tests
   (`tests/test_skill_budget.py`) and the shared 9,216-byte pointer budget
   (`tests/test_cross_session_contract.py`) pass with auto's rewritten `SKILL.md`.
6. `minerva:round-table` accepts `accept with fixes` as a quorum-counting verdict with its fixes folded
   and logged, and reserves `revise` for decision-changing objections.
7. `pytest` passes.

## Open questions

None blocking. Deliberately deferred to telemetry (see Re-measure): the up-arm's real trigger rate,
and whether the propose-phase abort stays live.
