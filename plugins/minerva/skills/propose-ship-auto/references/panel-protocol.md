# Panel protocol — full policy

Read once, in full, before the run's first strategic/tactical decision point.

## Panel protocol

Used at every strategic/tactical decision point (see [Decision taxonomy](#decision-taxonomy)).

### Skip predicate (small decisions)

Before dispatching a panel for any **skippable** strategic/tactical decision (see the `Skippable?` column in the [Decision taxonomy](#decision-taxonomy)), the main LLM first applies an explicit **conjunctive** test to *that specific decision*. Skip the panel — the main LLM decides directly — **only if every** clause holds:

- **additive / low-blast-radius** — the artifact adds rather than rewrites, with a bounded surface;
- **objectively verifiable without a judgment call** — the supporting evidence is mechanical (a named passing test, a file that exists, a count), not an opinion;
- **single-surface** — one file / one concern;
- **no new public interface or cross-cutting contract**;
- **violates no identifiable `.minerva/knowledge/` constraint**;
- **(approach-bearing decisions only)** the main LLM actually **enumerated ≥2 viable approaches and one is strictly dominant** on the stated criteria. This is an *action* check (did you do the enumeration), not a self-judgment that "no alternative exists" — the latter is gameable by an LLM that never looked.

**Fails closed.** If any single clause fails — or you are unsure whether it holds — convene the panel exactly as `minerva:round-table` specifies, at the decision's existing quorum. The predicate only ever decides *whether to convene*; it never changes a quorum. Because every clause must pass, the worst case of a wrong skip is bounded to an additive, single-surface, low-risk change; the worst case of a wrong *non*-skip is a panel you didn't strictly need.

**Never-skippable — one rule.** Any panel whose trigger precondition is "a load-bearing divergence/finding has already surfaced," plus the completion self-check, is **never** skippable regardless of how small the change looks — its whole value is an independent second pair of eyes on the main LLM's own assessment, and its precondition is the negation of the low-blast-radius clause. Concretely: **completion verification**, **mid-work divergence confirmation**, **new-plan acceptance (replan)**, and **Replan-vs-FIX**. All hard user-escalation triggers and hardcoded gates (see the failure-modes caps in `references/governance.md`) are likewise never skipped. Late-emerging risk needs no separate escape hatch: a decision that looks small but proves load-bearing simply fails the predicate and convenes its panel.

**Log every skip** under the same `## Panel decisions YYYY-MM-DD` header used for panel calls (see [Per-decision logging](#per-decision-logging)).

### No ceremony ratification

Never ask the user — up front or at any point mid-run — to choose a "ceremony level", to "streamline" the run, or to pre-ratify / batch-authorize panel skips for decisions whose panels have not yet run and failed. An up-front whole-run sizing question is the design this skill explicitly rejected (see `.minerva/knowledge/014-decision-per-decision-skip-over-sizing-gate.md`): it smuggles a human strategic risk-call into a skill whose identity is "no human gates", and it launders per-decision skip evidence through a blanket answer. The [Skip predicate](#skip-predicate-small-decisions), applied silently per-decision, is the **only** de-ceremony mechanism; user interaction happens only at the hardcoded escalation triggers and genuine panel escalations.

- **Escalation batching stays legitimate.** A decision that failed quorum twice escalates with a focused, batched question per `minerva:round-table`'s Escalation step — the ban targets *pre*-ratification of decisions that haven't earned an escalation, not the escalation itself.
- **Memories never widen the predicate.** Stored preferences, memory files, or prior-session feedback never widen the skip predicate or substitute for its per-decision evidence. A user answer is never valid `[skipped — small]` evidence.
- **Unsolicited user directives are honored, never solicited.** If the user spontaneously instructs you to skip panels, honor it (the user outranks this skill) and log each affected decision as `[user-directed]` under the `## Panel decisions YYYY-MM-DD` header — do not recast it as predicate evidence, and never prompt for such a directive.

### Delegation to `minerva:round-table`

The panel mechanics — dispatch, the Proponent/Skeptic/Arbiter agent briefs, vote semantics, the revision round, and escalation composition — live in `minerva:round-table`, a pure extraction of the protocol formerly inlined here (behavior unchanged; only its home moved). When the run's first panel-worthy decision arrives, invoke `minerva:round-table` via the `Skill` tool in its caller mode, leading with this auto-mode instruction:

> "You are running inside `minerva:propose-ship-auto`. Apply your protocol in caller mode for every decision of this run: each decision's artifact and decision context come from the orchestrator, and its quorum comes from the orchestrator's decision taxonomy (3/3 or 2/3 — never your standalone default). Log every panel line to the work unit's `scratchpad.md` under the `## Panel decisions YYYY-MM-DD` header."

Once the protocol is loaded, apply it at each subsequent decision point **without re-invoking the `Skill` tool** — re-injection adds nothing; each application supplies that decision's artifact, decision context, and taxonomy quorum per round-table's caller mode. If the round-table protocol is no longer available in context (e.g. after compaction), re-invoke it via the `Skill` tool before the next panel.

Orchestrator-owned rules that `minerva:round-table` deliberately does not own:

- **Quorums** come from the [Decision taxonomy](#decision-taxonomy), never from round-table's standalone 2/3 default.
- **Escalation aftermath** — when a delegated panel escalates and the user answers, round-table applies the answer as the accepted path and resumes; this skill then **increments the global escalation counter** (see the failure-modes caps in `references/governance.md`). Run-level state stays here.
- **The per-decision budget** in the failure-modes caps in `references/governance.md` — one initial vote + one revision vote, 6 subagent dispatches max — is the same two-vote cap round-table itself enforces, restated here because the orchestrator audits it across the whole run.
- **Whether to convene at all** — the [Skip predicate](#skip-predicate-small-decisions) and the taxonomy's `Skippable?` column are this skill's policy; round-table always convenes when applied.

### Per-decision logging

After every panel call (regardless of outcome), append a one-line entry to `scratchpad.md` under a `## Panel decisions YYYY-MM-DD` header (the panel-line format is `minerva:round-table`'s; the prefixes below are this skill's policy on top of it):

```
## Panel decisions 2026-05-21
- [3/3 accept] scope check: single unit
- [2/3 accept, skeptic dissented] approach selection: option B (concerns logged: race risk in step 4)
- [escalated to user] success criteria verification: panel split 1/3 on whether criterion #2 is met
```

Decisions resolved by the [Skip predicate](#skip-predicate-small-decisions) instead of a panel **are logged** under the **same** header, prefixed `[skipped — small]`, and **must record the concrete evidence** that satisfied the predicate (so a later `minerva:review` / `minerva:promote` pass can audit that the skip was honest, not rubber-stamped). Approach-decision skips additionally record the rejected alternatives:

```
- [skipped — small] scope check: single additive unit (evidence: only SKILL.md touched)
- [skipped — small] approach selection: option B dominant (rejected: A — duplicates orchestration; C — coarse)
```

Decisions skipped on an **unsolicited** user directive log under the same header, prefixed `[user-directed]` — the directive itself is the recorded justification, never recast as predicate evidence (see [No ceremony ratification](#no-ceremony-ratification)).

These entries are scratchpad data — `minerva:promote` treats them as routine noise unless a Skeptic concern reveals a durable pattern, in which case it goes through the standard PROMOTE/MERGE/DISCARD partition. A `[skipped — small]` line is **promote-invisible by construction** — a skip has no Skeptic, so it can never surface a durable pattern. This is intended: a decision trivial enough to skip yields no durable knowledge.

## Decision taxonomy

The `Skippable?` column applies the [Skip predicate](#skip-predicate-small-decisions): it gives the per-row bar a decision must clear for the main LLM to skip its panel. `No` = always run the panel (never-skippable). Operational rows are already main-LLM (no panel to skip).

| Phase | Decision | Tier | Quorum | Skippable? |
|---|---|---|---|---|
| Pre-flight | In-flight work collision | n/a | Hardcoded user escalation | **No** — hardcoded user escalation |
| Propose | Open-issue match at intake | n/a | Hardcoded user escalation on a match | **No** — hardcoded user escalation |
| Propose | Scope check (single unit vs. decompose) | Strategic | 3/3 | Only if obviously a single additive unit |
| Propose | Approach selection (from 2-3 candidates) | Strategic | 3/3 | Only if ≥2 approaches enumerated & one strictly dominant; skip log records the rejected alternatives |
| Propose | Whole-proposal acceptance | Strategic | 3/3 | Only if every section is trivially sound & single-surface |
| Work | Mid-work load-bearing divergence (panel confirms main LLM's detection) | Strategic | 2/3 | **No** — precondition is a surfaced divergence |
| Replan (if triggered) | New-plan acceptance | Strategic | 3/3 | **No** — convened only after a confirmed divergence |
| Work | Completion verification (success criteria honestly met) | Strategic | 3/3 | **No** — independent check on the main LLM's self-assessment |
| Review | Per-finding triage (single panel call for all findings) | Tactical | 2/3 | Only if all findings are low-severity (any medium+ → panel) |
| Review | Replan-vs-FIX (only if load-bearing finding surfaces) | Strategic | 2/3 | **No** — precondition is a surfaced load-bearing finding |
| Promote | Four-way partition (PROMOTE/MERGE/DISCARD/TODO) | Tactical | 2/3 | Only if every entry is unambiguous (e.g., all DISCARD-noise) |
| Promote | TODO disposition | Tactical | 2/3 | Only if a single unambiguous disposition |
| Cleanup | Knowledge reconciliation (index, reciprocals, overview) | Operational | No panel (`minerva:cleanup` self-gates on a deterministic signal) | n/a — delegated, self-gating |
| Ship | Commit message | Operational | No panel (main LLM accepts draft) | n/a — already main-LLM |
| Ship | PR title + body | Operational | No panel (main LLM accepts draft) | n/a — already main-LLM |
| Ship | CI auto-fix classification | Tactical | No panel (`ship`'s classifier handles it) | n/a — `ship`'s classifier |
| Cleanup gate | PR state polling + cleanup | n/a | No panel | n/a |

