# Scratchpad: followups-become-github-issues

## Balanced decisions 2026-08-22

- [reviewed — folded] scope check: single unit (Skeptic revise). Folded: `plugins/minerva/README.md:10` and `using-minerva/references/guide.md:9` carry a second `followups.md` mention; all three `propose-ship-*/references/phases.md` mention it twice more (Assemble context + Read context on resume), not just the disposition line — same blind spot flagged for the consumer skills. Folded: the integration gets its own `promote/references/github-issues.md` rather than three inline bullets in an already-6.7KB `modes.md` (call-tools-not-prose + progressive disclosure). Folded: idempotency — a partial step-7 failure then a re-run would duplicate issues, so a pre-create duplicate search mirrors ship's `gh pr view`-before-`gh pr create`, and created URLs are recorded in `proposal.md`. Folded: failed `priority:*` label creation degrades to the body line. NOT folded: the priority mechanism (already designed in the approach artifact this reviewer could not see); deferring the read path to a fast-follow (re-weighting — would ship the blind spot the same review flagged). Escalation question answered explicitly: staying on `balanced` — ~15 prose/JSON files, no Python, fully reversible.
- [reviewed — folded] approach: option A, issue-first with capability probe + per-item fail-soft (Skeptic revise). Folded: priority authorship/definitions were undefined — the model now proposes a level, the four definitions are stated verbatim in the skill, and the step-6 hard gate is where they are corrected. Folded: `viewerPermission` was fetched but unused and would have mis-gated public-repo outside contributors who *can* open issues — dropped from the gate; the creation attempt is the real permission check. Folded: consumer list was wrong — verified by grep that `minerva:propose` has ZERO `followups.md` mentions and `modes.md:25`'s claim it scans the file is stale; real consumers are `minerva:review` + the three orchestrators. Folded: the "fixes the stale-backlog complaint" framing is prospective-only; the 22 existing files stay as they are. Folded: a line that `gh` resolves the right remote from inside a worktree (remotes are shared). Rejected alternatives recorded in the proposal.
- [decided] whole-proposal soundness (solo gate): sound. Concrete `gh` invocations satisfy call-tools-not-prose; the new reference file satisfies progressive disclosure; all four catalog surfaces are in scope. Known tradeoff recorded — issues outlive an abandoned branch where a `followups.md` would not.

## Review finding 2026-08-22

Code-quality review returned 0 high / 2 medium / 4 low; its two mediums independently
matched the two the minerva audit had surfaced. All six triaged FIX (small, concrete, and
this is bash an agent runs verbatim against a real repo); none changed the approach, so the
replan-vs-FIX gate did not trigger.

- `ensure_label` returned non-zero on a failed create, so the documented fail-soft depended
  on the executor's shell settings rather than the code. Now returns 1 explicitly, builds a
  `USABLE` flag array, and the block says do not run it under `set -e`/`set -u`.
- The duplicate check relied on `gh issue list --search ... in:body`, but GitHub's search
  index is not synchronous with creation — precisely the window a retry-after-partial-failure
  lands in. Now checks the run's own record, then `proposal.md`'s `## Deferred work`, and
  only then the search.
- Heredoc delimiter `BODY` → `MINERVA_ISSUE_BODY` (verbatim item prose could contain a line
  that is exactly `BODY` and truncate the issue silently).
- `--title` needed an escaping rule; it now goes through a `$headline` variable.
- Conditional labels are expressed in the snippet (`"${USABLE[@]}"`) instead of only in
  prose after it.
- Dropped a dangling "whose entries could be adjacent" clause left in
  `propose-ship-auto/references/phases.md`, which had made the three orchestrators
  inconsistent.

Verified after fixing: `bash -n` over both extracted snippets passes, and `ensure_label`
was exercised against the real `gh`. **That exercise created a stray label on the repo
(`definitely-not-a-real-label-zzz`); it was deleted immediately and the label list
confirmed back to its original 9.** Testing side-effecting `gh` snippets against the live
repo is the wrong instinct — a scratch repo or a stubbed `gh` on PATH is the right one.
