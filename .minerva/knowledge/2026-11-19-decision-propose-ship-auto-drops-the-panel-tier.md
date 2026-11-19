---
name: propose-ship-auto-drops-the-panel-tier
description: Use when tempted to add a multi-agent panel, vote or debate to a minerva gate, or when reading the propose-ship-auto reviewer ladder — panels were removed in 4.0 on external evidence plus this repo's logs; an unsettled critique goes to a narrow Adjudicator, then the user.
metadata:
  type: decision
---

# propose-ship-auto drops the panel tier; an unsettled critique goes to a narrow Adjudicator, then the user

**Date**: 2026-11-19
**Type**: decision
**Theme**: lifecycle
**Summary**: no panels in minerva 4.0 — Skeptic → fold-audit → narrow Adjudicator → user; round-table deleted
**Context**: .minerva/work/2026-11-19-remove-round-table-tier (see git history if the worktree has been cleaned up)

## Context

`minerva:propose-ship-auto` routed each decision solo / reviewer / panel, the panel being a
Proponent/Skeptic/Arbiter vote delegated to `minerva:round-table`. A 2023–2026 literature pass
(`research.md` in the unit) found that at matched compute multi-agent debate ties or loses to
independent sampling plus a vote (Huang et al., ICLR 2024; Choi, Zhu & Li, NeurIPS 2025), that
assigned personas add no accuracy, that role-locked votes are not independent samples (a 2/3
quorum reduces to the Arbiter, a 3/3 quorum gives the Skeptic a veto), and that an Arbiter inherits
LLM-judge persuasion / position / self-preference biases. This repo's own logs agreed: after
round-table gained `accept with fixes`, every panel but one returned 3/3 accept whose only output
was the fixes one Skeptic also produces; only 3 decisions ever moved reviewer → panel.

## Finding

The panel tier and `minerva:round-table` are deleted (minerva **4.0.0**, breaking). Two tiers
remain, solo and reviewer. Every Skeptic gate runs one ladder, each rung only when the one before
could not settle the decision, at most **three dispatches**:

1. **Skeptic** — evidence-cited concerns marked blocking / non-blocking; when CONTEXT names a
   *scrutiny clause* (the four former panel clauses: ambiguity, blast radius, existing interface
   change, knowledge tension) it tests exactly that clause. The clauses now only deny solo.
2. **Fold-audit** — after a fold, unchanged from 2026-09-05.
3. **Adjudicator** — after a failed fold-audit or the anti-circularity escape. It rules only on
   the disputed items, labelled `C<n>` (critique) / `F<n>` (fold-audit new concern):
   `resolved | unresolved | critique mistaken — <evidence>`. It raises **no new concerns**, so it
   is not the open-ended re-critique 2026-09-05 rejected. **The rulings decide**, not its verdict
   line; a ruling with no evidence, or a disputed item left unruled, counts as `unresolved`.
4. **User** — any `unresolved` item. On the escape path a Skeptic ruled right also goes to the
   user: adopting a materially different decision with the budget spent would ship an unaudited
   rewrite.

Former panel floors (divergence confirmation, new-plan acceptance, replan-vs-FIX) are reviewer
floors; completion is always the Verifier, which also fails a diff that changes an existing
interface beyond what the proposal approved. Logs gain `[adjudicated — proceed | escalated]`,
written right after the escalation that triggered it. `decision_telemetry.py` pairs them, flags an
orphan adjudication, and flags a *skipped rung* (an Auto escalation dated ≥ 2026-11-19 with neither
an adjudication nor a legacy panel line after it); `run_trace.py` has an `adjudicator` role.

## Implications

- Do not reintroduce a vote or debate tier to buy confidence. More scrutiny means a sharper
  single brief, execution-grounded verification, or the user — not more agents arguing.
- The Adjudicator's narrowness is load-bearing: a brief that lets it raise new concerns turns it
  into a second Skeptic with no budget left to audit what it says.
- Legacy `[panel — …]` lines and `## Panel decisions` headers stay readable in telemetry and the
  trace; archived runs are evidence for the Re-measure section in `governance.md`, which compares
  the Adjudicator trigger rate and user-escalation rate against the panel era.
- One orchestrator still picks each decision's tier; this changed the tiers, not the routing.

## Related
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — supersedes: round-table and the panel delegation it described are deleted
- [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]] — builds on: keeps one orchestrator and per-decision routing, removes its panel tier
- [[2026-09-05-decision-balanced-rechecks-its-folds]] — builds on: the fold-audit stays; the Adjudicator is bounded so it is not the re-critique this entry rejected
- [[2026-09-23-pattern-a-unanimous-quorum-deadlocks-on-write-up-fixes]] — evidence: unanimous panels escalated decisions everyone agreed on, one of the observations behind removing panels
- [[2026-09-26-decision-parallel-gate-waves-and-existing-interface-clause]] — refines: the gate wave remains; its existing-interface clause now seeds a reviewer instead of convening a panel
