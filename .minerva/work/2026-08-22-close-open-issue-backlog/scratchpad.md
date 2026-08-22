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
