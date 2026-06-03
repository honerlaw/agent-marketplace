# Proposal: wire-synthesize-into-orchestrators

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> Follow-up to unit 024 (Phase C — the `minerva:synthesize` capability). Discharges the
> deferred orchestrator wiring named in [[024-decision-synthesis-layer-separate-file-advisory]].

## Goal

Wire the existing `minerva:synthesize` skill into both lifecycle orchestrators
(`minerva:propose-ship`, `minerva:propose-ship-auto`) as an optional, self-gating
**post-promote / pre-ship** step. After promote lands knowledge entries, the orchestrator
considers refreshing the wiki `overview.md`; the LLM decides **IF** to run, using
synthesize's own deterministic `synthesis_status` self-gate. The refreshed `overview.md`
rides the same PR.

## Why

Unit 024 shipped `minerva:synthesize` as a manually-invoked maintenance skill and
explicitly deferred orchestrator wiring to a follow-up. The user asked to wire it into
both orchestrators while "allow[ing] the LLM to decide IF it should run." Post-promote is
the natural seam: promote adds entries (pushing corpus-max past the synthesis-watermark),
creating un-synthesized scope; synthesizing before ship lets the overview refresh ride
the same PR rather than dangling or trailing in a later PR.

## Approach

The two orchestrators have different shapes, so the wiring takes the idiomatic form in
each, but it is the **same feature at the same seam** — kept consistent in one change.

### `minerva:propose-ship` (user-gated) — fold into the existing promote→ship gate

propose-ship is a thin delegating orchestrator whose `## Out of scope` minimalism clause
says it "does not add checkpoints, summaries, or status messages between phases beyond
the explicit work → review trigger words, the promote → ship gate, and the cleanup gate."
To avoid adding a new inter-phase interaction, the synthesis offer is **folded into the
existing promote→ship gate** rather than added as a separate nudge. The gate's
sub-sequence is made explicit:

1. summarize what promote did;
2. if promote added knowledge entries, **offer** to refresh the wiki overview via
   `minerva:synthesize` (it self-gates on whether enough new scope accumulated);
3. if the user accepts, invoke `minerva:synthesize` via the `Skill` tool — including its
   own Step-4 write confirmation — **before** ship is invoked;
4. **then** await the existing ship confirmation;
5. invoke `minerva:ship`.

The `## Out of scope` minimalism sentence is edited to admit the in-gate synthesis offer
while **preserving all three enumerated triggers** (work→review, promote→ship, cleanup).

### `minerva:propose-ship-auto` (panel-gated) — new Phase 4.5

Insert **Phase 4.5 — Synthesis (delegated, self-gating)** between Phase 4 (Promote) and
Phase 5 (Ship gate). The orchestrator **always invokes** `minerva:synthesize` in
auto-mode via the `Skill` tool, leading with an auto-mode instruction **mirroring the
Phase 6 ship pattern**:

> "You are running inside `minerva:propose-ship-auto`. When `minerva:synthesize` reaches
> its Step-4 write-confirmation gate, accept the drafted `overview.md` without prompting.
> Its Step-2 'decide IF to synthesize' self-gate is unchanged — if there is too little
> new scope it correctly no-ops."

synthesize self-gates **internally** (reads the deterministic `synthesis_status` signal;
the LLM decides IF). Phase 4.5 logs **one** outcome line under the existing
`## Panel decisions YYYY-MM-DD` header using a **distinct `[synthesis]` prefix** (not a
vote / not a `[skipped — small]` line):

- wrote → `[synthesis] refreshed overview.md (watermark NNN→MMM; K entries synthesized)`
- no-op → `[synthesis] no-op (K un-synthesized below threshold / overview current)`

Phase 4.5 **terminates with "Continue to Phase 5"** so the `4 → 4.5 → 5 → 6 → 7` chain is
unbroken. Phase 4's two "continue to Phase 5" handoffs (step 2 idempotency short-circuit
and step 8) are **re-pointed to Phase 4.5** so synthesis runs even on an idempotent
re-entry. (`--cleanup-only` re-entry still says "skip phases 1–6"; Phase 4.5 is inside
that span, so it is correctly skipped there — no conflict.) This is **delegation, not a
panel decision**: a new Decision-taxonomy row records it as
`| Promote→Ship | Synthesis refresh (Phase 4.5) | Operational | No panel (synthesize self-gates) | n/a — delegated, self-gating |`,
and a one-line note in the Per-decision-logging section states a `[synthesis]` line is an
operational observability line, NOT a vote (promote-invisible, like a skip). **No new
panel** is added.

### Both orchestrators

- **PR boundary:** synthesize writes `overview.md` to repo-root `.minerva/knowledge/`
  before `minerva:ship` stages. Because ship stages **specific paths** (never `-A`/`.`),
  the orchestrator's ship handoff **explicitly names `overview.md`** in the staging set
  and **requests** a PR-body line "overview.md refreshed (advisory navigation)". In
  human-mode propose-ship the PR body passes ship's user gate #2, so the line is
  *requested*, not guaranteed (advisory — acceptable per
  [[024-decision-synthesis-layer-separate-file-advisory]] / 013).
- **Catalog:** the lifecycle one-liner in propose-ship-auto's description / phase-sequence
  reads `promote → synthesize → ship`. (The three `minerva:synthesize` catalog surfaces —
  010 — already list the skill from unit 024; unchanged here.)
- **Contracts (012):** add a `minerva:synthesize` anchor to **both**
  `evals/propose-ship/contract.json` and `evals/propose-ship-auto/contract.json` in
  lockstep; the literal token `minerva:synthesize` must appear in **both** SKILL.md bodies
  (it is a safe positive substring — trailing-boundary match, not a prefix of any other
  token).
- **Synthesize's own doc:** retire the `## Out of scope` wiring bullet in
  `plugins/minerva/skills/synthesize/SKILL.md` (the index.md / log.md bullets stay).
- **Knowledge (016):** entry 024's body is **not** edited; a new entry 025 records the
  wiring and carries `builds on [[024-decision-synthesis-layer-separate-file-advisory]]`
  in its `## Related` — the forward breadcrumb that discharges 024's "deferred" line.

## Success criteria

1. **propose-ship:** the promote→ship gate offers synthesis when promote added entries,
   with the explicit ordering (synthesis resolves **before** ship is invoked); the
   `## Out of scope` minimalism sentence is edited to admit the in-gate offer while
   preserving all three enumerated triggers.
2. **propose-ship-auto:** Phase 4.5 exists, always invokes `minerva:synthesize` in
   auto-mode (auto-accepting only synthesize's Step-4 write gate), terminates with
   "Continue to Phase 5", and Phase 4's step-2 + step-8 handoffs are re-pointed to Phase
   4.5; it logs a `[synthesis]` outcome line on **both** wrote and no-op outcomes; a
   Decision-taxonomy row + a Per-decision-logging note record it as delegation, **no new
   panel**.
3. **Both:** the ship handoff names `overview.md` in the staging set and requests the
   PR-body refresh line (criterion asserts the **handoff instruction exists**, not that
   the line lands through a user gate).
4. **Contracts:** both orchestrator SKILL.md bodies contain the literal token
   `minerva:synthesize`; both `evals/<orch>/contract.json` gain a `minerva:synthesize`
   anchor; `tests/test_skill_contracts.py` passes.
5. **Synthesize doc + knowledge:** synthesize's own `## Out of scope` wiring bullet is
   retired (index.md / log.md bullets stay); entry 024 is untouched; new entry 025 records
   the wiring and `builds on [[024-...]]`.
6. **Behavior note:** a single-entry promote → Phase 4.5 typically **no-ops** (synthesize
   Step-2 threshold) — expected, not a bug.
7. The full enumerated CI suite stays green; the live corpus stays detector- and
   fixer-clean.

## Open Questions

- None load-bearing.

## Out of scope

- Changing `minerva:ship`'s own logic — only its handoff instruction (staging set +
  PR-body request) is used, exactly as Phase 6 already instructs ship.
- CI-gating the overview's content (advisory per 013 /
  [[024-decision-synthesis-layer-separate-file-advisory]]).
- A `log.md` running changelog (a possible later Phase-C increment).
