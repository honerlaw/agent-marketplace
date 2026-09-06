# Proposal: balanced-rechecks-folds

**Date**: 2026-09-05
**Status**: Draft

## Goal

`minerva:propose-ship-balanced` closes its two evidence-backed independence gaps **without
convening a panel**:

1. **A post-fold re-check.** After the main model folds a Skeptic `revise` at any Skeptic
   reviewer gate — scope check, approach selection, whole-proposal soundness, mid-work
   divergence, new-plan acceptance, replan-vs-FIX — it dispatches **one** fresh Sonnet reviewer
   with a narrow **fold-audit brief** against the revised decision, and arbitrates that once,
   strictly.
2. **Whole-proposal soundness becomes a Skeptic reviewer gate**, every run. It is solo today.

The reviewer cap changes from "one dispatch per gate, no re-dispatch" to **"one review dispatch,
plus one re-check only after a fold — never a third, never a Proponent/Arbiter, never a
`minerva:round-table`."** The rung's distinction from `minerva:propose-ship-auto` holds: the
independent review is still a single advisory reviewer the main model arbitrates.

Re-check outcomes get their own scratchpad log lines, and a new
`plugins/minerva/scripts/decision_telemetry.py` tallies `## Balanced decisions` /
`## Panel decisions` / `## Quick decisions` logs across a project's work units, so the gate
taxonomy — documented as "the load-bearing, revisable knob" — can be re-tuned in one command
instead of an afternoon of grep.

## Why

The direction came out of `minerva:explore` on the question "can balanced fall back to the full
round table when a decision warrants it?" The scratchpad archives answered a sharper question:
what does the panel actually buy over balanced's single Skeptic?

- **13 balanced runs** (2026-07-27 → 2026-08-30) logged 74 decisions: 37 `[decided]`,
  **30 `[reviewed — folded]`**, 5 `[reviewed — clean]`, 2 `[escalated to user]`. The Skeptic
  returned load-bearing critique in ~85% of dispatches (approach 11, scope 10, completion 4,
  never-elide gates 5). Both escalations were seed ambiguity. The anti-circularity escape —
  "cannot confidently adjudicate the critique → ask the user" — fired **zero** times. So the main
  model folds almost every critique and **nothing independently checks the fold**. That is the
  self-confirmation gap `2026-06-29-decision-propose-ship-balanced-single-reviewer` bounded
  behaviorally (the "load-bearing critique" definition) and cannot bound structurally.
- **26 auto runs** (~96 panel calls, 19 skips): roughly half went to a revision round, and the
  revision is driven by the **Skeptic** nearly every time. The Proponent accepts almost always;
  the Arbiter overruled the Skeptic as *mistaken* once in 96. **Whole-proposal acceptance is the only
  heavy-revision gate balanced runs solo** — 13 of its 27 panel calls went to a revision round,
  second only to approach selection (17 of 25, which balanced already reviews) and far ahead of
  scope (7 of 22) and completion (0 of 18; the Verifier choice holds) — including HIGH gaps
  ("a 532-occurrence rewrite with no documented mechanism", "an unsatisfiable success
  criterion"). The 06-29 entry's telemetry justified completion-as-Verifier and never
  examined this gate. (A hand `grep revis` count had ranked whole-proposal first; the
  reproducible reader corrected it.)
- So the panel's marginal value over one Skeptic, in this corpus, is **round-2 re-verification
  of the revised artifact** — not the three-agent shape. One extra Sonnet dispatch after a fold
  buys most of that at a third of the cost: ~+4 dispatches per run (2.7 → ~6.7 sequential),
  still 2–3× under auto's ~11–22 with a sequential Arbiter in each.
- The telemetry pass that produced these numbers was hand-rolled grep/awk over archived
  scratchpads and broke twice on format drift before it worked. The taxonomy cannot be honestly
  re-tuned if measuring it costs that much.

**Rejected alternatives**, recorded so they are not re-invented at runtime
(`2026-06-06-pattern-rejected-alternative-reinvented-at-runtime`):

- **A per-decision panel-escalation arm in balanced** (decide → Skeptic → round-table → user),
  the literal ask. It collides with the 06-29 constraint that balanced never convenes a panel,
  and the data gives it no honest trigger: the anti-circularity escape never fires (so the arm
  would be inert), while Skeptic `revise` fires on 30/35 dispatches (so keying on it would turn
  balanced into auto).
- **Re-running the Skeptic brief on the revised artifact** instead of a fold-audit brief. A fresh
  Skeptic has no memory of the first critique, cannot say whether item 3 was addressed, and
  tends to surface *new* concerns — which tempts a third dispatch or a silent dismissal, and is
  indistinguishable in the log from the first review.
- **A mechanical-evidence exception to strict escalation** (proceed past a re-check `revise` when
  a cited file/line refutes it). Auditable, but "what counts as mechanical" is itself a judgment,
  and the whole point of the re-check is to remove the main model's discretion over the second
  look. Strict costs ~1% extra escalations by auto's Arbiter-overrule rate.
- **Collapsing balanced and auto into one skill** with a per-decision solo / one-reviewer / panel
  selector. Cleanest end state, largest blast radius (two skills, knowledge entries, four catalog
  surfaces, contract tests). Not needed to close the two gaps; may be revisited once the
  telemetry script makes the case measurable.

## Approach

### 1. Protocol changes in `plugins/minerva/skills/propose-ship-balanced/`

**`references/verify-protocol.md`**

- *The reviewer gates*: whole-proposal soundness joins the **fire on every run** list (scope
  check, approach selection, whole-proposal soundness, completion-verification). The taxonomy
  table row flips to `**Yes — Skeptic**`. The evidence sentence cites auto's revision telemetry.
- *Single-reviewer mechanism* gains step 4, **Re-check after a fold**: when step 3 folds a
  load-bearing critique at a Skeptic gate, dispatch **one** fresh reviewer (`Agent`,
  `subagent_type: general-purpose`, `model: sonnet`, `run_in_background: false`) with the
  fold-audit brief. ARTIFACT = the original decision, the Skeptic's critique verbatim, and the
  revised decision; CONTEXT = the same CONTEXT the gate gave the Skeptic. Not at the Verifier
  gate — a completion `revise` already loops through Phase 2.5 → new-plan acceptance → a second
  Verifier pass, which is its re-check.
- **Fold-audit brief** (new, alongside the Skeptic and Verifier briefs): for each numbered
  concern in the original critique, `addressed | partially | not addressed | regressed` with one
  line of evidence; a `## New concerns` section bounded to the load-bearing categories (a)–(e)
  and to concerns *introduced by the revision*; verdict `accept | revise`. The brief must not
  re-open the decision — it audits the fold.
- **Arbitrating the re-check — strict**: `accept` → proceed. `partially` where the residual is
  *not* load-bearing (outside (a)–(e)) → fold the residual, proceed. Anything else — a
  load-bearing item `partially` / `not addressed` / `regressed`, or a new load-bearing concern —
  → **escalate** via the anti-circularity escape. There is **no** self-confirmation path (the
  main model may not decide the re-check is mistaken) and **no third dispatch**. The escalation
  counts toward the global escalation counter like every other.
- *Per-decision logging*: a `[rechecked — clean]` / `[rechecked — residual folded]` /
  `[rechecked — escalated]` line written **immediately after** its `[reviewed — folded]` line.
  `[rechecked — escalated]` records what was asked and the user's answer on that same line; no
  separate `[escalated to user]` line, so escalations are not double-counted. The worked example
  block gains the three lines.
- The "at most one dispatch per gate / no revision-round re-dispatch" wording is replaced
  everywhere it occurs by the new cap.

**`references/phases.md`**

- Phase 1 step 6 becomes **Whole-proposal soundness — reviewer gate**: the main model reviews the
  full draft, then dispatches a Skeptic. ARTIFACT = the complete draft proposal; CONTEXT = the
  seed plus the knowledge entries cited this session. Arbitrate per verify-protocol.
- Every Skeptic gate step (Phase 1 steps 4–6, Phase 2 step 3, Phase 2.5 step 3, Phase 3 step 5)
  gains "on a fold, re-check per verify-protocol". The opening dispatch paragraph states the new
  cap.

**`references/governance.md`** — the *Reviewer budget* paragraph states the new cap; the
*Observability* bullet lists the `[rechecked — …]` prefixes; the *Convening a round-table* bullet
is unchanged.

**`SKILL.md`** — the frontmatter description drops "no panel, no revision round" for "no panel;
one fold re-check, never a third dispatch"; the binding-floor bullets and the *Binding caps*
sentence state the new cap; the reviewer-gate list names whole-proposal soundness.

### 2. Tests and contracts

- `tests/test_skill_dispatch.py` `REGISTERED_SITES`: `propose-ship-balanced/references/verify-protocol.md`
  rises to 2 (the re-check dispatch instruction). Whether the per-gate "re-check per
  verify-protocol" notes in `phases.md` register as dispatch sites is decided by running the
  detector, not by eye; the registry is updated to whatever it reports, and every registered
  instruction pins `run_in_background: false`.
- `evals/propose-ship-balanced/contract.json`: anchors `Fold-audit brief` and `rechecked` in
  `references/verify-protocol.md`.
- `tests/test_skill_contracts.py`: an **inverted** presence assertion — the phrase
  `no revision-round re-dispatch` appears in **no** file under `propose-ship-balanced/`
  (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).
- Catalog surfaces re-synced to the new description: `plugins/minerva/README.md`,
  `pages/index.md`, the `using-minerva` decision matrix. Root `README.md` lists skill names only.
  `test_site_catalog.py` and the contract's `cross_surface` checks guard the sync.

### 3. `plugins/minerva/scripts/decision_telemetry.py`

Importable API plus a CLI, following `work_status.py`'s conventions (module docstring stating the
failure it exists for; `sys.path` anchored to its own directory).

- **Scan scope**: `<root>/.minerva/work/*/scratchpad.md` and
  `<root>/.minerva/work/*/archive/*.md`. Never through `.minerva/worktrees/` — a worktree glob
  sees every unit in the project through each worktree
  (`2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project`).
- **Fence-aware** via `knowledge_spans.unfenced_lines` — imported, never re-derived
  (`2026-06-11-constraint-fence-scans-import-fence-re`). A fenced example of a decision line
  inside a scratchpad is not a record.
- **Grammar**: a section opens at `^## (Balanced|Panel|Quick) decisions (YYYY-MM-DD)` and closes
  at the next `^## `. Inside it a record is `^\s*[-*]\s*\[<tag>\]\s*<gate>[:(—-]…`.
- **Record**: `(unit, orchestrator, date, tag, gate_raw, gate, outcome, rest, path, lineno)`.
- **Gate normalization** to a canonical set (`scope`, `approach`, `whole-proposal`,
  `completion`, `divergence`, `replan-acceptance`, `replan-vs-fix`, `triage`, `partition`,
  `todo`, `synthesis`, `preflight`) via ordered keyword rules; anything else keeps its raw text
  as `other:<raw>`.
- **Tag classification**: exact (dash- and whitespace-normalized) for Balanced/Quick tags —
  `decided`, `reviewed — clean`, `reviewed — folded`, `rechecked — clean`,
  `rechecked — residual folded`, `rechecked — escalated`, `escalated to user`, `process note`,
  `synthesis`; heuristic for Panel vote strings (`escalat` → escalated; `skipped` → skipped;
  `user-directed` / `user-decided` → user-directed; a revision marker — `revis`, `→`, `vote 2`,
  `rev2`, `round 2` — → panel-revised; a leading `N/3 accept` → panel-accept). Anything else is
  `unknown`, **reported verbatim with `path:lineno`, never dropped**
  (`2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`).
- **Re-check pairing** by adjacency: a `[rechecked — …]` record attaches to the immediately
  preceding `[reviewed — folded]` record of the same section. An orphan is reported as unknown.
- **CLI**: `python3 plugins/minerva/scripts/decision_telemetry.py <root>` prints, per
  orchestrator, a `gate × outcome` count table, the fold→re-check pairing counts, and the
  unknown list. Exit 0 always — it is a reader, not a gate.

**`tests/test_decision_telemetry.py`**

- Synthetic-corpus tests for the grammar, gate normalization, adjacency pairing, and orphan
  reporting.
- **Tag-vocabulary test**: extract every `[tag]` from the fenced logging examples in
  `propose-ship-balanced/references/verify-protocol.md`,
  `propose-ship-quick/references/solo-decision-protocol.md`, and
  `propose-ship-auto/references/panel-protocol.md`, and assert each classifies to a non-`unknown`
  outcome — so a tag added to prose but not to the script goes red
  (`2026-08-11-pattern-the-enumeration-is-what-fails`).
- **Fence-awareness test**: a scratchpad whose only decision lines sit inside a code fence yields
  zero records.
- **Live-corpus test** on this repository: ≥13 units with a Balanced section are parsed, and the
  unknown list is empty for Balanced and Quick sections. Panel sections are free-form
  round-table output; their unknowns are reported, not asserted.

### 4. Knowledge

`.minerva/knowledge/2026-09-05-decision-balanced-rechecks-its-folds.md` (`Type: decision`):
records the telemetry above, the fold-audit design, the strict arbitration rule and the rejected
alternatives; `## Related` links `2026-06-29-decision-propose-ship-balanced-single-reviewer` as
`refines`, plus `2026-05-31-decision-per-decision-skip-over-sizing-gate`,
`2026-06-10-decision-panel-mechanics-extracted-to-round-table` and
`2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch` as `see also`. Written
add-only; the index, reciprocals and overview reconcile on the default branch via
`minerva:cleanup` (`2026-08-05-decision-promote-add-only-reconcile-on-default`).

## Success criteria

1. `references/verify-protocol.md` contains a `Fold-audit brief` section and a *Re-check after a
   fold* step; the phrase `no revision-round re-dispatch` appears in no file under
   `plugins/minerva/skills/propose-ship-balanced/` — asserted by an inverted presence test.
2. The decision taxonomy marks whole-proposal soundness `**Yes — Skeptic**`, and `phases.md`
   Phase 1 step 6 dispatches a Skeptic with a stated ARTIFACT and CONTEXT.
3. `python -m pytest tests/ -q` is green, including `test_registered_site_still_dispatches`,
   `test_no_unregistered_dispatch_sites` and `test_dispatch_instructions_pin_execution_mode` for
   the balanced files.
4. `python3 plugins/minerva/scripts/decision_telemetry.py .` on this repository reports zero
   unknown records in Balanced and Quick sections, and — verified once during work and recorded
   in the scratchpad — reproduces today's balanced tally (37 decided / 30 folded / 5 clean /
   2 escalated). The live-corpus test asserts the properties, not the numbers.
5. Every `[tag]` in the three orchestrators' fenced logging examples classifies to a
   non-`unknown` outcome (tag-vocabulary test).
6. A scratchpad whose decision lines are all inside a code fence yields zero records
   (fence-awareness test).
7. `plugins/minerva/README.md`, `pages/index.md` and the `using-minerva` matrix carry the new
   balanced description; `test_site_catalog.py` and the contract's `cross_surface` checks are
   green; the description is ≤1024 characters.
8. `.minerva/knowledge/2026-09-05-decision-balanced-rechecks-its-folds.md` exists with a
   `## Related` entry linking `2026-06-29-decision-propose-ship-balanced-single-reviewer` as
   `refines`; `python scripts/knowledge_lint.py .minerva/knowledge` is clean.

## Open Questions

- None blocking. For the record: the dispatch-parking risk in
  `2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch` (#113) now applies to
  ~2.5× as many dispatches per balanced run. This unit does not address it; #113 does.
