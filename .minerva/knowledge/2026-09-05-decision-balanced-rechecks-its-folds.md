---
name: balanced-rechecks-its-folds
description: Use when tuning an orchestrator's reviewer gates or tempted to add a panel to propose-ship-balanced — the rung's single Skeptic folded 30 of 35 critiques with nothing checking the fold, so it gained one fold-audit re-check (never a third dispatch, never a panel) and a whole-proposal Skeptic gate; decision_telemetry.py is how the taxonomy is re-measured.
metadata:
  type: decision
---

# propose-ship-balanced re-checks its folds with one more single reviewer — not a panel

**Date**: 2026-09-05
**Type**: decision
**Summary**: a folded Skeptic critique now gets one fold-audit re-check, arbitrated strictly; whole-proposal soundness became a Skeptic gate; `decision_telemetry.py` measures the gate taxonomy
**Context**: .minerva/work/2026-09-05-balanced-rechecks-folds

## Context

The ask that opened this unit was "can `propose-ship-balanced` fall back to the full round table
when a decision warrants it?" — because `propose-ship-auto` is slow enough that balanced gets
picked for almost everything, and some decisions feel bigger than one Sonnet Skeptic. That is the
failure [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] predicted: the four-rung ladder
is an up-front whole-run sizing choice, made by a human before the risky decision exists.

Instead of adding a panel arm, the archived scratchpads were read for what the panel actually buys
over a single Skeptic. Thirteen balanced runs had logged 74 decisions: 37 `[decided]`,
**30 `[reviewed — folded]`**, 5 `[reviewed — clean]`, 2 `[escalated to user]`. The anti-circularity
escape — "cannot confidently adjudicate the critique → ask the user" — had fired **zero** times. In
26 auto runs (~130 panel lines), revision rounds were driven by the Skeptic nearly every time; the
Proponent almost always accepted, and the Arbiter overruled the Skeptic as *mistaken* once.

## Finding

**The panel's marginal value over one Skeptic, in this corpus, is round-2 re-verification of the
revised artifact — not the three-agent shape.** Balanced folded ~85% of critiques and nothing
independently checked the fold: the self-confirmation gap that
[[2026-06-29-decision-propose-ship-balanced-single-reviewer]] bounded behaviorally (the
"load-bearing critique" definition) and could not bound structurally.

Two changes, both inside the rung's identity:

1. **A fold-audit re-check.** After the main model folds a Skeptic `revise` at any Skeptic gate, it
   dispatches **one** more fresh Sonnet reviewer with a narrow brief — disposition each original
   critique item `addressed | partially | not addressed | regressed`, flag only concerns the
   revision *introduced*, verdict `accept | revise` — and arbitrates it **strictly**: `accept` →
   proceed; a non-load-bearing residual → fold it; anything load-bearing unaddressed → escalate,
   with **no** self-confirmation path and **no third dispatch**. The cap "one dispatch per gate,
   no revision-round re-dispatch" became "one review dispatch plus one re-check only after a fold —
   never a third, never a Proponent/Arbiter/vote". Not at the Verifier gate: a completion `revise`
   already loops through replan → new-plan acceptance → a second Verifier pass.
2. **Whole-proposal soundness became a Skeptic gate.** By `decision_telemetry.py`'s count, auto's
   revision rounds rank approach 17/25, **whole-proposal 13/27**, scope 7/22, completion 0/18.
   Whole-proposal was the only heavy-revision gate balanced ran solo; completion at 0/18 vindicates
   the 06-29 Verifier choice. (A hand `grep revis` count had ranked whole-proposal first; the
   reproducible reader corrected its own motivation — the first thing it did.)

Cost: ~+4 Sonnet dispatches per run (2.7 → ~6.7 sequential), still 2–3× under auto's ~11–22 with a
sequential Arbiter in each. Every added dispatch lands exactly where the logs say a fold happened.

**Rejected alternatives**, so they are not re-invented at runtime
([[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]]):

- **A per-decision panel-escalation arm** (decide → Skeptic → round-table → user). No honest
  trigger exists: the anti-circularity escape never fires (the arm would be inert) and Skeptic
  `revise` fires on 30/35 dispatches (keying on it would turn balanced into auto). It would also
  erase the rung's distinction from auto, which the 06-29 entry names as the thing not to do.
- **Re-running the Skeptic brief on the revised artifact.** A fresh Skeptic cannot say whether item
  3 was addressed; it re-critiques, surfaces new concerns, and invites a third dispatch or a silent
  dismissal.
- **A mechanical-evidence exception to strict escalation.** "What counts as mechanical" is a
  judgment, and the re-check's value is that the second look is not the main model's. Strict costs
  ~1% extra escalations by auto's Arbiter-overrule rate.
- **Collapsing balanced and auto into one skill** with a per-decision solo / one-reviewer / panel
  selector. Cleanest end state, largest blast radius; not needed to close the two gaps. Revisit
  once the telemetry makes the case measurable.

## Implications

- Balanced still never convenes a `minerva:round-table` panel. Its independent review is one
  advisory reviewer plus, after a fold, one more single reviewer auditing that fold. Reintroducing
  a Proponent, an Arbiter, a vote, or a third dispatch erases the rung.
- The `[rechecked — clean | residual folded | escalated]` line is written **immediately after** its
  `[reviewed — folded]` line, naming the same gate; the tally pairs them by adjacency and reports an
  orphan as a problem. `[rechecked — escalated]` is the only escalation line for that gate.
- **Re-measure before re-tuning.** `python3 plugins/minerva/scripts/decision_telemetry.py <root>`
  tallies `## Balanced/Panel/Quick decisions` lines by orchestrator × gate × outcome across
  `.minerva/work/` (never through worktrees), fence-aware, reporting every unknown tag verbatim.
  `tests/test_decision_telemetry.py` reads each orchestrator's fenced logging example and fails if
  a documented tag does not classify — a tag added to prose but not to the script goes red.
- The dispatch-parking risk in [[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]]
  now applies to ~2.5× as many dispatches per balanced run; this unit did not address it (#113).

## Related
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — refines
- [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] — builds on
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] — see also
- [[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]] — see also
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also
