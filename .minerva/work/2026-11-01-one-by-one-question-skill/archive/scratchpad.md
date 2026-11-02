# Scratchpad: one-by-one-question-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-01
- [reviewed — clean] scope check: one unit, one PR; Skeptic noted the fallback anchor, the budget and step-7 acting scope, all taken into the whole-proposal fold (tier: reviewer — adds a new public skill surface, fails solo; no panel clause; parallel wave)
- [reviewed — clean] approach: option A, question operation when it fits, direct message otherwise; rejected B (plain text only, departs from the adapter's preference) and C (tool only, cannot carry five options); Skeptic hardening notes applied, none load-bearing (tier: reviewer — new skill surface; parallel wave)
- [reviewed — folded] whole-proposal: added the compatibility-eval scenario surface, named the fallback anchor, stated the deletion-pass mechanism; also hand back instead of resuming work (tier: reviewer; parallel wave)
- [rechecked — residual folded] whole-proposal: item 7 not addressed, low severity, folded into criterion 1 (trigger separated from grill-plan); fold-audit new-concern 2 folded into Files changed
- [reviewed — clean] completion verification: Verifier reproduced all 6 criteria (tier: reviewer floor; no interface change beyond the proposal)
- [solo] review triage: 19 FIX / 0 SUGGEST / 2 IGNORE (tier: default-solo row — no finding had two defensible dispositions; every writable failure scenario was small enough to absorb)
- [solo] promote partition: 2 PROMOTE / 3 MERGE / rest DISCARD / 0 TODO (tier: default-solo row — no entry had two defensible buckets)

## Work notes
- Deletion pass (criterion 2): all 10 contract anchors and the run() wiring call each failed the tests when removed; baseline green. Script used `python -B`.
- Live eval (criterion 6): `run_compatibility_evals.py --host claude --scenario one-by-one` passed, cost about $0.29, 27 s. AskUserQuestion is unavailable in `-p`, so the run exercised the direct-message path; the dialog path has no live evidence. Codex not run.
- First test of `one_by_one_checks` over-asserted: with the marker missing every check that reads the question text fails too, which is correct.
- Deletion pass rerun after review: all 12 anchors and the wiring caught. The first rerun reported the wiring as caught while the compat test file failed to collect (rc 2 on the baseline); that result was void, so the pass was repeated after the fix.
- Live eval rerun on the final skill passed, about $0.32.

## Review triage 2026-11-01
- FIX: batching check, option-block scan, heading hyphen, other option markup, 3-5 bound, exactly one mark, lowercase mark, marker reuse in the topic list, step 7 contradiction, argument scope, add-a-question row, second unclear reply, `back` targets, Open Questions call-out, `skip` dependents, reply words in the dialog, multi-answer row, dropped state, `recommended, unseen`, silence row, "second line" wording, README fresh prose, passing-run wiring test, reply-table anchors, COMPATIBILITY.md scenario list.
- IGNORE: dialog-invisible check (host-transcript extension that `claude -p` cannot reach; recorded under Known gaps). Recommended-option-first check (parsing cost exceeds value).
