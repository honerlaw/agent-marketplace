# Proposal: auto-skip-predicate

**Date**: 2026-05-31
**Status**: Shipped (2026-05-31)

## Goal

Add a per-decision **skip predicate** to `minerva:propose-ship-auto` so that genuinely small,
low-risk decisions bypass their 3-agent Proponent/Skeptic/Arbiter consensus panel and the main
LLM decides directly. Net effect: a genuinely small task runs effectively panel-free — answering
the user's ask ("a version of the auto command that, when the task is small enough, skips the
round table for each decision") — while every hard user-escalation valve and the four
self-assessment / post-divergence panels remain **non-skippable**. The change is a behavior added
to the existing **Panel protocol** section, not a new mode, phase, or flag.

## Why

`minerva:propose-ship-auto` dispatches a 3-agent panel at ~8 strategic/tactical decision points
per run. For trivial decisions — an obviously-single-unit scope check, an all-DISCARD-noise
promote partition, a single-followup TODO disposition — that is three subagent dispatches of pure
overhead with negligible marginal safety. A per-decision predicate cuts overhead exactly where it
is wasteful, **fails closed** to the existing panel on any uncertainty, and composes up to the
user's whole-task intent: when every decision in a small task clears the predicate, the whole run
is panel-free; when a mostly-small task contains one risky decision, only that one decision keeps
its panel.

A whole-task "sizing gate" was considered and rejected during proposal (see Approach): classifying
the task up front is both coarse (blind to a risky decision that only emerges mid-run) and
self-defeating (it spends a panel to decide whether to skip panels). The per-decision predicate
re-evaluates at each point, so late-emerging risk is handled **structurally** — a decision that
looks small but proves load-bearing simply fails the predicate and convenes its panel. There is no
separate escape-hatch mechanism, and therefore no "the same LLM is both detector and suspect"
problem.

## Approach (A′ — in-skill per-decision skip predicate)

Edits are confined to `plugins/minerva/skills/propose-ship-auto/SKILL.md`.

### 1. Skip predicate (added to the Panel protocol section)

Before dispatching any **strategic/tactical** panel, the main LLM applies an explicit
**conjunctive** test to *that specific decision*. It may skip the panel only if **all** clauses
hold:

- **additive / low-blast-radius** — the decision's artifact adds rather than rewrites, with a
  bounded surface;
- **objectively verifiable without a judgment call** — the supporting evidence is mechanical (a
  named passing test, a file that exists, a count), not an opinion;
- **single-surface** — one file / one concern;
- **no new public interface or cross-cutting contract**;
- **violates no identifiable `.minerva/knowledge/` constraint**;
- **for approach-bearing decisions only** — the main LLM actually **enumerated ≥2 viable
  approaches and one is strictly dominant** on the stated criteria. This is an *action* check
  (did I do the enumeration), not a self-judgment that "no alternative exists."

**Fails closed**: if any single clause fails, run the panel exactly as today, at its existing
quorum. The predicate only ever decides *whether to convene* a panel; it never changes a panel's
quorum.

### 2. Never-skippable carve-outs (binding), unified by one rule

**Any panel whose trigger precondition is "a load-bearing divergence/finding already surfaced,"
plus the completion self-check, is never skippable** — because that precondition is the negation
of the predicate's low-blast-radius clause. Concretely, four panels:

| Panel | Quorum | Why never-skippable |
|---|---|---|
| Completion verification | 3/3 | Independent second pair of eyes on the main LLM's own "criteria met" claim |
| Mid-work load-bearing-divergence confirmation | 2/3 | Fires only once a divergence is detected |
| New-plan acceptance (replan) | 3/3 | Convened only because a load-bearing divergence was already confirmed |
| Replan-vs-FIX (review) | 2/3 | Fires only when a load-bearing finding has surfaced |

All existing **hard user-escalation triggers and hardcoded gates** likewise never skip: in-flight
work collision (pre-flight), worktree creation failure, ship-phase `other`/push-rejection/`gh`-auth
failure, CI bail, and the global escalation counter reaching 3.

### 3. Decision taxonomy gains a "Skippable?" column — a value for EVERY row

The per-row value states the operative bar (which clauses gate that decision type), not a bare
yes/no:

| Phase / Decision | Tier | Quorum | Skippable? |
|---|---|---|---|
| Pre-flight — In-flight collision | n/a | Hardcoded | **No** (hardcoded user escalation) |
| Propose — Scope check | Strategic | 3/3 | Only if obviously a single additive unit |
| Propose — Approach selection | Strategic | 3/3 | Only if ≥2 approaches enumerated & one strictly dominant; skip log records the rejected alternatives |
| Propose — Whole-proposal acceptance | Strategic | 3/3 | Only if every section is trivially sound & single-surface |
| Work — Mid-work divergence confirmation | Strategic | 2/3 | **No** |
| Replan — New-plan acceptance | Strategic | 3/3 | **No** |
| Work — Completion verification | Strategic | 3/3 | **No** |
| Review — Per-finding triage | Tactical | 2/3 | Only if all findings are low-severity (any medium+ → panel) |
| Review — Replan-vs-FIX | Strategic | 2/3 | **No** |
| Promote — Three-way partition | Tactical | 2/3 | Only if every entry is unambiguous (e.g., all DISCARD-noise) |
| Promote — TODO disposition | Tactical | 2/3 | Only if a single unambiguous disposition |
| Ship — commit / PR / CI classify | Operational | No panel | Already main-LLM (no change) |
| Cleanup gate | n/a | No panel | No change |

### 4. Logging — reuse the existing header

Each skip writes one line under the **existing** `## Panel decisions YYYY-MM-DD` header:

```
- [skipped — small] scope check: single additive unit (evidence: only SKILL.md touched)
- [skipped — small] approach selection: option B dominant (rejected: A — duplicates orchestration; C — coarse)
```

Each skip line **records its concrete evidence string** (per the panel's logged work-phase note)
so a later `minerva:review` / `minerva:promote` pass can audit whether the predicate was honored
in practice rather than rubber-stamped. Reusing the existing header means `minerva:promote` needs
**no new handling**. By construction these lines are **promote-invisible** — a skip has no Skeptic,
so it can never surface a durable pattern through the existing PROMOTE/MERGE/DISCARD channel. This
is intended: a decision trivial enough to skip yields no durable knowledge.

### 5. Housekeeping

- The six `contract.json` anchors (`Proponent`, `Skeptic`, `Arbiter`, `minerva:ship`,
  `minerva:cleanup`, `panel`) all survive — the skip predicate lives under the existing "Panel
  protocol" heading and the panels still exist for non-small decisions — so
  `evals/propose-ship-auto/contract.json` needs **no change**; `tests/test_skill_contracts.py`
  stays green.
- Catalog rows (`plugins/minerva/README.md`, `using-minerva` decision matrix, root `README.md`)
  change **only if** the `description:` frontmatter changes. Per the open question below, a light
  description touch is likely — if so, refresh all three surfaces per the catalog-sync constraint.

## Success criteria

1. `SKILL.md`'s Panel protocol section documents the conjunctive skip predicate, including the
   action-form approach clause (≥2 enumerated, one strictly dominant).
2. The Decision taxonomy table has a "Skippable?" column with an explicit value for **every** row.
3. **Binding** — the four never-skippable panels (completion-verification, mid-work
   divergence-confirmation, new-plan acceptance, Replan-vs-FIX) are marked never-skippable in
   **both** the table and prose, justified by the unified post-divergence / self-check rule; all
   hard escalation triggers are explicitly stated as non-skippable.
4. Skips are specified to log under the **existing** `## Panel decisions` header as
   `[skipped — small] <decision>: <reason> (evidence: ...)`; approach-decision skips additionally
   record the rejected alternatives. The promote-invisible-by-design property is stated.
5. The predicate fails closed: the prose states that any single unmet clause convenes the panel at
   its existing quorum.
6. `tests/test_skill_contracts.py` passes (the six anchors, incl. `panel`, are still present);
   `contract.json` is changed only if a required anchor changed.
7. The change is confined to `propose-ship-auto` (plus the three catalogs **only if** the
   `description:` frontmatter changed); no other minerva skill is modified.

## Open Questions (resolved)

- **Advertise in `description:`?** **Resolved: yes — light touch.** The `propose-ship-auto`
  frontmatter `description:` gained one sentence about the skip predicate, and all three catalog
  surfaces (`plugins/minerva/README.md`, `using-minerva` decision matrix, root `README.md`) were
  synced in the same change per the catalog-sync constraint.
- **Triage skip bar.** **Resolved: any medium+ forces the panel** (the stricter, fail-closed
  reading), encoded directly in the Decision-taxonomy `Skippable?` row for per-finding triage.
