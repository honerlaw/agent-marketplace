# Proposal: cleanup-stands-down-for-ci

**Date**: 2026-08-14
**Status**: Shipped (2026-08-14)
**Base**: `main`

## Goal

`minerva:cleanup` reconciles the knowledge wiki on every invocation. When a repo has
installed a CI job that already does that, cleanup must recognise it and stand down
instead of racing it.

## Why

The seekless repo now reconciles on merge in CI. Cleanup does not know, and the two are
not merely redundant — they are **unserialised**.

Cleanup's own documented mutual exclusion is the non-forced push to a fixed ref:

> The actual mutual exclusion is the remote ref update in Step 3.3: a non-forced push to
> `minerva/reconcile` is atomic, so exactly one of the two wins and the loser is rejected.

That argument holds only between two cleanups, because it depends on both pushing the
**same** ref. The CI job pushes a unique `minerva/reconcile-ci/<run_id>` branch per run,
so there is no contended ref and nothing rejects the loser. Both writers can open a PR
editing `index.md`, which is the concurrent-writer collision the whole add-only design
exists to prevent.

The early-out that would have caught it cannot see the CI job either:

```bash
gh pr list --head minerva/reconcile --state open   # exact head match
```

`--head` is an exact branch name, so an open `minerva/reconcile-ci/31727177896` is
invisible to it. Cleanup concludes nothing is outstanding and proceeds.

This was observed on 2026-08-13. It stayed quiet only because the operator checked the CI
run by hand before letting cleanup reconcile — which is not a mechanism.

## Approach

Two changes to `skills/cleanup/references/reconciliation.md`, both in Step 1/Step 2.

1. **Detect a repo-local CI reconciler and stand down.** Before the pending signal, check
   whether any file under `.github/workflows/` invokes `knowledge_fix.py`. That is a sound
   anchor rather than a heuristic: the pinned fixer is the deterministic half of
   reconciliation, so a workflow calling it *is* a CI reconciler, and one that does not is
   not. On a hit, report that CI owns reconciliation, name any pending entries so the run
   is not silently trusting something it did not verify, and skip to the final report.

2. **Widen the outstanding-PR probe to the prefix.** `--head minerva/reconcile` becomes a
   prefix match over open PRs, so a CI-authored reconcile PR is visible to the
   at-most-one rule even if detection is bypassed or a future CI job is named differently.
   Defence in depth: (1) is the intended path, (2) is what keeps the failure safe.

Rejected — a marker file in `.minerva/` declaring CI ownership: it is explicit, but needs
per-repo setup, and a repo that installs the workflow and forgets the marker gets exactly
today's silent race. Detection from the workflow itself cannot drift out of sync with the
thing it describes.

Rejected — widening the probe alone, letting cleanup wait for the CI PR then reconcile
what remains: not wrong, but it leaves cleanup opening PRs a CI job would have opened
seconds later, and the waiting path is written around a PR that cleanup itself created.

## Success criteria

1. `reconciliation.md` states the stand-down rule before its Step 1 signal, with the
   detection command written out.
2. The stated rationale names why the existing push-based exclusion does not cover a CI
   reconciler, so the next reader does not re-derive it as "merely redundant".
3. The outstanding-PR probe matches the `minerva/reconcile` prefix, and the text says why
   an exact `--head` match was insufficient.
4. The stand-down path still names pending entries rather than reporting a bare success —
   the file's existing "never end a run leaving entries uncatalogued without naming them"
   rule is not weakened by it.
5. `SKILL.md`'s Knowledge-reconciliation section agrees with the reference; no surviving
   sentence claims reconciliation runs on *every* invocation without qualification.
6. Repos with no such workflow are unaffected: the detection is a no-op there and every
   existing instruction still applies.

## Open Questions

None. The detection anchor and both call sites are known.
