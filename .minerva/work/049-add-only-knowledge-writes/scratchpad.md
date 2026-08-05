# Scratchpad: add-only-knowledge-writes

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Notes 2026-08-05

- **The NNN-blindness was in the fixer too, not just the linter.** The proposal named
  `knowledge_lint.py:126/:135`; `knowledge_fix.py:61` had the identical dict-keyed
  `_entries`. That one is worse because it *mutates*: on a duplicate, `plan_index`
  collects both catalog lines (both match the single surviving entry) and buckets
  both under the winner's declared type, misfiling the loser's line. On a corpus with
  65 legacy duplicate groups that is 65 misfiled lines on the first automatic run.
  The quarantine deliberately mirrors the shape already in the file for unrecognized
  types — "left where it is, never dropped, recorded as a refusal" — rather than
  inventing a new failure mode.

- **The reciprocal check would have turned every work-unit branch red**, and grilling
  missed it; it surfaced in propose's self-review. Making the watermark a lagging
  floor fixes the *missing catalog line* error, but an add-only promote also emits
  forward `## Related` links whose reverse direction doesn't exist yet — and
  `knowledge_lint`'s missing-reciprocal check is an error. The carve-out is keyed on
  the **source** entry's NNN vs the floor, which is the same rule, applied twice.

- **The backfill really was unnecessary** (dropped during grilling, now verified by
  `test_mixed_corpus_needs_no_backfill`). `plan_index` collects surviving catalog
  lines *verbatim* and only needs a `**Summary**` for entries that have **no** line.
  So a legacy entry keeps its hand-written line forever while new entries generate
  theirs. The mixed state is stable, not transitional — which is what makes this
  land on a 550-entry consumer repo with zero migration.

- **Allocator uses `git log --all --diff-filter=A`, not per-ref `git ls-tree`.** One
  path-limited command instead of N, and the semantics are strictly safer: "every NNN
  ever added on any ref" also catches numbers used by commits that were amended or
  rebased away. Over-allocating (skipping a number) costs nothing; reusing one is the
  entire bug. Verified against a git fixture that a number visible only on an
  unmerged branch, and only on an unfetched remote branch (with `--fetch`), is seen.

## Panel decisions 2026-08-05

- [3/3 accept] completion verification: all 9 success criteria honestly met; 410 CI-enumerated tests green, knowledge_lint clean. Panel independently reproduced the suite, the lint exit code, the byte caps and the Phase-4.5 excision rather than trusting the checklist.

## Panel concerns 2026-08-05

Logged despite the 3/3 accept — two were acted on in-run rather than deferred.

- **[medium, FIXED IN RUN] Reconciliation's skip-if-open was a check-then-act race.**
  `gh pr list --head minerva/reconcile` is a read followed by an act, so two concurrent
  cleanups (a manual run racing a `propose-ship-auto` wake-up) could both pass it and
  both push the same branch — reintroducing the conflict class this unit exists to
  remove, just on a rarer path. Fixed by making the **non-forced push** the lock (git's
  ref update is atomic; exactly one wins, the loser reports and exits 0) and demoting
  the `gh pr list` check to an early-out. Guarded by a new contract anchor. The Skeptic
  also noted this was the one piece of new coordination logic not wrapped in a tested
  script, contra knowledge 021 — recorded in `followups.md`.

- **[low-medium, MITIGATED] `using-minerva/SKILL.md` byte margin.** This unit's edit had
  pushed it 9157 → 9209 of 9216. Reworded that row to give the bytes back (now ~60 free)
  and recorded the compaction need in `followups.md`.

- **[medium, deferred by design] Criterion 1's second clause is unverifiable.** No harness
  in this repo executes a skill end-to-end, so "a promote run leaves only additions" can
  only be guarded by prose inspection. Promote rewrites the criterion to what is actually
  guaranteed; recorded in `followups.md`.

- **[low, accepted] Contract JSON reflow noise.** Two `evals/*/contract.json` diffs reflow
  every anchor to multi-line JSON for a one-token removal, inflating the diff stat.
  Cosmetic; not churned further.
