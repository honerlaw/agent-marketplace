# Scratchpad: close-open-issue-backlog

## Panel decisions 2026-08-22
- [3/3 accept] scope check: single work unit covering the 13-issue backlog (Skeptic accepted with 7 concerns; all folded into the proposal — #71 bootstrap resolved as an end-of-work authored field, thematic coherence owned as thin for 4/10 items, #76 named as a third disposition category, blast radius stated, execution order fixed, exclusions to be reported prominently, 3-unit alternative rebutted in-document)
- [3/3 accept] approach selection: 1A normalized-diff (#77), 2A authored Closes field (#71), 3A record-and-leave-open (#76). Skeptic's high-severity concern carried forward: pin 1A's normalization or it becomes the green lie it rejects 3B for.

## Divergence 2026-08-22 — #77 approach revised post-vote
Inspecting all six target-resolution blocks after the approach vote disproved 1A's premise:
they are NOT copies. cleanup has 3 steps with different semantics; review and ship have
materially different step 5s (no-minerva-context vs bare mode); promote carries an extra
Mode B paragraph; work is verbose where replan is terse. Byte-identity after normalization
is unreachable without erasing what the test checks — exactly the Skeptic's concern.
Revised to a shared-invariant test (sibling enumeration exact + both-locations and
both-id-forms clauses present). Verified all six currently satisfy both. Carried into the
whole-proposal-acceptance panel's artifact rather than re-running the approach panel, which
has spent its one vote.
- [consensus failure — 1 revise at 3/3] whole-proposal acceptance, vote 1: Proponent accept (verified every factual claim against the repo); Skeptic revise on a HIGH finding they reproduced — #81's gate inferred hardness from "index unchanged AND refusals present", which is the STEADY STATE, not a hard refusal. Reproduced independently before revising: plan_index on a canonical corpus returns new==old with a benign per-entry refusal present. Revised to an explicit `hard: bool` returned by plan_index. Four lesser edits folded in (the #77-closes/#76-open asymmetry, softened #85-first ordering, softened Hard-gate framing, rewritten criterion 7).
- [3/3 accept] whole-proposal acceptance, vote 2 (revision round): all three verified the corrected #81 explicit-`hard`-flag design against knowledge_fix.py directly. Arbiter accepted with an implementation note on #78 (prefix heading matching; Hard-gate citations exempt).

## Panel concerns 2026-08-22 — carried into the work phase
- [#78, medium — from acceptance vote 2] The heading-citation test must match on PREFIX, not
  equality. Verified against the live corpus: 9 quoted-heading citations exist, 7 resolve
  exactly, 2 are prefixes — `minerva:propose`'s "On approval — worktree setup" (real heading
  `... + file writes`) and `minerva:work`'s "Implementation protocol" (real heading
  `... — apply throughout the session`). An equality test reds CI against already-correct
  prose on day one.
  Also: `Hard gate #1/#2` are bold lead-ins inside numbered list items under
  `## Commit outstanding changes`, NOT headings. They are left as-is rather than converted
  into a form that cannot resolve; success criterion 10 covers the step-number citations only.
- [#81, low] `plan_reciprocals` may still be invoked when `hard` is true — correctness-neutral,
  since `plan()` performs no writes. Gate the returned `entries`, not the computation.
- [#81, low] `plan_index`'s docstring documents a 3-tuple; update it with the signature.

## Progress 2026-08-22
- #85 done — `QUALIFIED_MENTION_RE` + `reference_mentions()`; qualified mentions stripped
  before the bare pass so a sibling's file cannot be mis-attributed to the citing skill.
  `backfill-followups` now cites `plugins/minerva/skills/promote/references/github-issues.md`
  by real path. 5 new tests.
- #79 done — `description_overflow()` predicate + parametrized ceiling check. Negative case
  exercises the SAME predicate rather than restating the arithmetic; a negative case that
  re-derives the rule cannot prove the rule is enforced.
- #70 done — `assert_read_only()` called from INSIDE `fenced_blocks()`, so every extraction
  inherits it. A test asserts the guard stays inside the extractor (inspect.getsource), so a
  refactor cannot quietly move it out to the call sites.
- #75 done — Pages URL (confirmed live via `gh api .../pages`) linked from both READMEs.
- #81 done — explicit `hard: bool` as plan_index's 4th return; `plan()` gates on it alone.
  The steady-state case is the negative test and it asserts precisely the trap:
  `new2 == old2` AND `refusals2` truthy AND `hard2 is False`. First draft of that test hit
  the missing-index hard path instead of the per-entry path; fixed by seeding a catalog that
  already lists the odd entry under a known section.
- Suite: 571 passed.
- #71 done — optional `**Closes**: #N, #M` documented in propose's on-approval template;
  promote authors it when rewriting proposal.md; ship emits ONE `Closes #N` line per entry
  (GitHub only honours the keyword per-reference — `Closes #12, #34` closes just #12).
  Bare mode explicitly emits none: no proposal to read the field from.
- #80 done — propose-ship split into references/phases.md. SKILL.md 8691 -> 3846 bytes.
  Added the Phase 7 constant-delay rationale its siblings carry and it lacked (the wait is
  on auto-merge landing, which does not track CI duration, so there is no completion signal
  to subscribe to and a constant is the honest shape).
- #78 done — 16 step-number citations across the three orchestrators converted to the
  quoted-heading form already in live use. Contract test matches by PREFIX, not equality:
  2 of 9 pre-existing correct citations name the stable head of a heading with a trailing
  clarifier, so equality would have reded CI on correct prose. First draft of the
  step-number check false-positived on "invoke `minerva:replan`, return to step 3" — a
  self-reference, not a citation; fixed by excluding commas from the gap, with coverage.
  `Hard gate #1/#2` left alone as decided: they name bold list lead-ins, not headings.
- #77 done — NOT the byte-diff the approach panel approved. The six blocks are deliberately
  different (see the proposal's table), so the shared invariant is asserted instead: each
  block names exactly its five siblings, and each states both lookup rules. All six already
  satisfied both; cleanup's extra paragraph is intentional divergence, not drift.
- #76 done as designed — evidence appended to the bug entry; issue stays open, to be
  commented and retitled. NOT in the Closes list.
- Suite: 636 passed.
- CORRECTION: the completion checklist's first draft cited a `main` baseline of 571 tests.
  Wrong — 571 is this branch's count after its own first commit. Re-measured on 7f56ce4:
  535. Net new is +101, not +65. Caught by the completion Skeptic, verified directly.
- [3/3 accept] completion verification: all three independently reproduced mutations against
  the live worktree; the #81 inferred-gate revert failed the steady-state test for every
  reviewer. Skeptic caught the 571-vs-535 baseline error (corrected above); Arbiter re-measured
  535 on 7f56ce4 and judged the correction handled transparently.

## Review triage 2026-08-22
- [2/3 accept] triage panel over 7 findings (6 code-quality, 1 minerva audit).
  FIX C1, C2, C3, M1 · SUGGEST C5 · IGNORE C4, C6. Both voters verified every premise
  against the live worktree; no finding revealed a load-bearing divergence, so no replan.

Applied:
- C1 FIX — `step_number_citations()` hoisted to module scope so the negative cases exercise
  the same predicate the check runs. The first draft had defined the regex twice, which is
  the presence-assertion rot this unit's own #79 item extracted a predicate to avoid.
- C2 FIX — blanket comma ban replaced by a self-reference-marker exclusion scoped to the GAP
  between the skill mention and the step reference. The Skeptic raised a mirror defect
  ("re-run `minerva:promote`'s step 3" excluded by a marker in a different clause); gap
  scoping already prevents it, and it now has an explicit regression test, as they asked.
- C3 FIX — `gh` guard inverted from denylist to ALLOWLIST of read-only verbs. A denylist of
  the commands its author recalled fails open on every subcommand not thought of; an
  allowlist fails closed. `gh api` judged separately (plain GET legal; -X/--method/GraphQL
  mutation not). Regression test enumerates the 10 commands the denylist missed —
  `gh pr comment` was verified caught after the change and not before.
- M1 FIX — duplicated `## Out of scope` removed from references/phases.md.

Not applied:
- C5 SUGGEST — `_unfenced_lines` / `_unfenced` duplicated across two test modules. Needs a
  shared tests/ support module that does not exist; file as a followup issue in promote.
- C4 IGNORE — substring guard could reject prose mentioning a command. No corpus instance,
  and the fix would trade a harmless false positive for a false NEGATIVE on a safety guard.
- C6 IGNORE — prefix heading matching is the documented deliberate tradeoff; two live
  citations depend on it.

Suite: 641 passed. Mutations re-verified after the rewrites.

## Panel decisions 2026-08-22 (promote)
- [skipped — small] TODO disposition: a single unambiguous entry (T1, the `_unfenced`
  duplication) with one disposition — file as a low-priority GitHub issue. Predicate
  evidence: additive (opens one issue, changes no file); objectively verifiable (the issue
  exists or it does not); single-surface (one issue); no new public interface; violates no
  `.minerva/knowledge/` constraint. The taxonomy makes TODO disposition skippable when there
  is a single unambiguous disposition, which is the case here.
