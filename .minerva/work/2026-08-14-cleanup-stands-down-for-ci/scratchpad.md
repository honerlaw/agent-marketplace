# Scratchpad: cleanup-stands-down-for-ci

## Quick decisions 2026-08-14

- [decided] scope: single unit — one reference file plus a paragraph in SKILL.md; no script,
  no new phase, no public interface change.
- [decided] approach: detect a CI reconciler by grepping `.github/workflows/` for
  `knowledge_fix.py` and stand down, plus widen the outstanding-PR probe to a prefix match.
  Dominant over a declared marker file (needs per-repo setup; forgetting it reproduces the
  bug) and over widening the probe alone (leaves cleanup opening PRs CI would open anyway).
- [decided] soundness: behaviour change is gated on the presence of the workflow, so repos
  without a CI reconciler are untouched. The reference's "why cleanup owns this" rationale
  argues from "no CI workflow to install in each consumer repo" — a reason for the default,
  not a prohibition, and inapplicable once a repo has installed one.

## Completion verification 2026-08-14

All six criteria checked against the diff, mechanically where possible:

1. Step 0 precedes Step 1 and writes the detection command out — PASS
2. names why the push-based exclusion does not cover a CI writer ("unserialised",
   "no contended ref") rather than calling it redundancy — PASS
3. probe is a `startswith` prefix match and says why `--head` was insufficient — PASS
4. the stand-down still names pending entries — PASS
5. `SKILL.md` agrees; `promote/SKILL.md`'s claim that aggregates are derived "by
   `minerva:cleanup`'s reconciliation" was qualified too, since it is equally wrong in a
   CI repo — PASS
6. detection is a no-op where no such workflow exists — PASS

Verified both commands against real repos rather than reasoning about them: the grep finds
`reconcile-knowledge.yml` in seekless and finds nothing in agent-marketplace, so this
change is inert in its own repo. The prefix probe runs and returns empty against seekless,
which currently has no reconcile PR open.

Also checked the eval contract at `evals/cleanup/contract.json`: all nine anchors still
resolve, including the `The push is the lock` anchor whose surrounding text this unit
qualifies. Added `owned by CI (<workflow>)` to the reconciliation line of the final report
so a stand-down is visible rather than reported as "nothing pending".

## Promoted 2026-08-14

- `2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref` — an
  atomic-push lock excludes only the writers that push that ref. Written as a constraint
  building on [[2026-08-05-pattern-read-then-act-is-not-a-lock]] rather than as a
  correction to it: that entry already names "a fixed branch name" as its precondition, and
  is not wrong. What it does not say is what happens when a second writer, for good
  reasons, does not use it — which is that the exclusion vanishes and produces no error.

`knowledge_lint`: 0 errors. The 4 warnings are `pending reconciliation` back-links, which
is what an add-only promote is supposed to leave for the default branch.

## CI triage 2026-08-14

`structural` failed: `cleanup/SKILL.md is 9354 bytes, over the 9216-byte budget`. A gate I
did not know existed, and its assertion message states the remedy — keep detail prose in
`references/*.md` rather than growing the core. My SKILL.md sentence carried the whole
argument (unserialised vs redundant) when the core only needs the exception to exist and a
pointer; the reference already carries the reasoning.

Trimmed to `Exception: a repo that reconciles in CI (Step 0).` — 9204 bytes, 12 to spare.
Measured each candidate rather than estimating, after the first two rewrites came in 45 and
2 bytes over. Full suite green locally: 522 passed.

Note for whoever is next: 12 bytes of headroom is not much. The right move if it overflows
again is to move prose out, not to trim the exception further — it is already minimal.

Also worth recording: `gh pr checks --watch --fail-fast` exited **0** on this failing
check, the third falsely-green signal of the session. Verify `bucket` values, never the
watcher's exit code.
