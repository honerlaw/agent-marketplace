# Scratchpad: cross-session-preflight

## Balanced decisions 2026-08-24
- [decided] pre-flight in-flight collision: no unit reports `in_flight`, no worktrees — clear (hardcoded gate, no collision to escalate)
- [decided] open-issue match at intake: #94 (`minerva:debug` issue matching) is adjacent, not a match — one informational line, no ask
- [reviewed — folded] scope check: single unit. Skeptic proposed splitting the live-session query into its own unit (least precedented piece) — REJECTED, it is the piece the seed asked for; splitting would ship everything except the request. Folded its other points: fail-soft when the harness lacks ListAgents/SendMessage, self-describing reply contract for protocol-illiterate peers, and the trigger-enumeration surface corrected from "possibly governance.md" to a verified six locations (two per autonomous orchestrator).
- [reviewed — folded] approach: option B (one canonical shared reference, five citing surfaces). Skeptic surfaced no dominant alternative but four load-bearing corrections, all folded: (1) HIGH — the ref-lock backstop binds only writers sharing the ref, per `2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref`; the resource protected is the SLUG not the GOAL, so the pre-worktree same-goal race has no atomic backstop at all, now stated outright; (2) the four pre-flight blocks carry deliberate per-surface divergence per `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`, so each keeps its own qualifier and a test pins them; (3) unscoped SendMessage fan-out; (4) no staleness bound on remote branches. Also adopted its finding that `propose/SKILL.md` has no pre-flight block at all, which is an argument for B beyond the stated criteria.
- [decided] sibling-session fan-out scope: resolved empirically rather than by escalation. `ListAgents` on this repo returned 32 peers — 5 live local, 18 offline Remote Control, 10 idle cloud. Filter on liveness (offline cannot process), reply capability (cloud cannot reply), and project-name prefix (`agent-marketplace-*`), which reduced 32 candidates to 0 on the authoring repo. With the fan-out bounded to near-zero in the common case, the escalation predicate no longer fires — no user escalation spent.
- [decided] whole-proposal soundness (solo gate): internally consistent, no placeholders, every criterion checkable. The `MINERVA-BUSY`/`MINERVA-IDLE` reply contract is the one new cross-session convention, but it is self-describing per message, unpersisted, and nothing depends on it — not an unfamiliar public interface requiring escalation.

## Run counters
- Reviewer gates fired: 2 (scope, approach) — both `revise`, both folded
- Escalations to user: 0

## Review finding 2026-08-24
Minerva audit: no spec-fidelity or knowledge-compliance findings. (`2026-06-11-constraint-ci-test-enumeration-explicit` would have applied but is already marked superseded by `2026-08-11-decision-ci-runs-the-whole-suite`; CI runs `pytest tests/` wholesale, confirmed independently.)

Code review returned 6 findings, all triaged FIX (none a load-bearing divergence, so no replan gate fired):
1. [MEDIUM] negative-coverage test asserted on a fabricated literal — would still pass if the real check were gutted. Both now route through one `block_keeps_qualifier` predicate.
2. [LOW] section locator required a following `## ` heading; a block placed last in its file would fail with a message blaming the heading for being absent. Regex now tolerates EOF.
3. [MEDIUM-HIGH] Step 4's skip condition said "steps 1-3 came back silent", so an ADJACENT hit would suppress the only source that sees the pre-worktree window — silencing the step exactly when it is doing its job. Now scoped to "surfaced no collision", with adjacent/stale explicitly non-suppressing.
4. [MEDIUM] the 14-day staleness bound covered branches but not open PRs, unexplained. The asymmetry is now stated: an open PR is standing human intent, a pushed branch is residue.
5. [MEDIUM] "not in flight when its PR is merged or closed" had no runnable command — step 3's `--state open` query cannot answer it. Added `gh pr list --state all --head <branch>` and `git log -1 --format=%cI`.
6. [MEDIUM] the four orchestrator blocks share a verbatim summary with nothing pinning it — a fifth evidence source would leave four stale copies. Added byte-identity across the three autonomous rungs, a marker check on all four, and a check tying "four evidence sources" to the protocol file's actual step run.

All three new guards mutation-tested: drifting a summary, adding a fifth source step, and flattening a qualifier each turn CI red.
