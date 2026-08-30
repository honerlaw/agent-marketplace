# Scratchpad: cross-session-inform-only

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-08-30

- [decided] scope check: one work unit, one PR, no `## Phases` — four files plus two eval
  manifests, single subsystem (user adjudicated at intake; a human gate dominates the Skeptic
  gate it substitutes for, so no reviewer dispatched)
- [decided] approach: new canonical `propose/references/cross-session.md` (user adjudicated).
  Rejected: folding into `in-flight-check.md` (an intake-pre-flight home for a rule that fires
  outside intake — misleading to the reader who needs it most); a `minerva:peer-message` skill
  (no better reach, and a catalog row does not fit `using-minerva`'s 178-byte headroom)
- [decided] whole-proposal soundness: internally consistent; no public interface changes; the
  one cross-cutting contract touched is the step-4b message template, which is additive (solo)
- [reviewed — clean] completion verification: Verifier accept — reproduced all 6 criteria
  independently, including re-running the three anchor-removal negative tests and a fresh
  `pytest tests/` (826 passed). Noted-not-defect: proposal prose says "adds to the peer's
  workstream", the file's heading says "adds to their workstream" — same meaning, and the
  heading is what the anchor pins

## Review triage 2026-08-30

Mode: local-diff (fresh-context subagent) — no PR existed at review time.
Minerva audit: 2 findings (M1-M2). Code review: 12 findings (#1-#12).

- [FIXED]   M1  med  evals/propose/contract.json — marker anchor is whole-file, not scoped to
            the fenced template that does the work (2026-08-28-pattern-a-presence-assertion-
            must-be-scoped-to-what-it-guards)
- [IGNORE]  M2  low  cross-session.md — contract is unenforced prose; inherent to an
            instruction-prose deliverable, and ## Residual risk states the limit
- [FIXED]   #1  high in-flight-check.md:132 — bare pointer dangles for the four orchestrators
            that read this file by qualified path; mirror defect in cross-session.md
- [ESCALATED→FIXED] #2  high cross-session.md:9-12 — receive half declares an audience (plain
            minerva:work) with no route to the file — escalated to user
- [FIXED]   #3  high cross-session.md:57-64 — second classifier for pre-flight replies with no
            stated precedence over in-flight-check Step 5/6
- [FIXED]   #4  med  cross-session.md:70-76 — orchestrator branch reuses intake-only options
            ("start fresh anyway") for messages arriving mid-work
- [FIXED]   #5  med  contract.json — boundary anchor pins only the heading; the carve-out body
            is deletable while green
- [FIXED]   #6  med  contract.json — dispositions table, escalation forms and relayed rule are
            all unanchored despite being named success criteria (first fix covered only ONE of
            the two escalation forms — the intake form stayed unanchored until the second
            completion gate caught it; see the note below)
- [FIXED]   #7  med  cross-session.md:81-91 — relayed-request rule has no defined behavior in
            an autonomous run (no user in loop; counter semantics unstated)
- [ESCALATED→FIXED] #8  med  using-minerva/SKILL.md:94 — pointer leaves 52 bytes; line 24's standing
            "add a row" instruction is now unsatisfiable — escalated to user
- [FIXED]   #9  med  cross-session.md:44-49 — restates in-flight-check §4a/4b instead of
            pointing (2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves)
- [FIXED]   #10 low  cross-session.md:44 — "per run" undefined for a session in no lifecycle run
- [FIXED]   #11 low  cross-session.md:100 — exemption names the Agent tool, not the SendMessage
            channel, so messaging one's own subagent reads as banned
- [IGNORE]  #12 low  scratchpad staged-vs-modified — staging artifact, not a defect

- [escalated to user] review findings #2 (reach) + #8 (headroom) — both revisited decisions the
  user had already made, and the reviewer added facts they did not have (using-minerva's own
  description tells sessions to skip it; line 24's "add a row" directive is unsatisfiable at 52
  bytes). User chose the wider option in each: pointers in work + all four orchestrators, and
  adopt #107. Escalation counter: 1
- [reviewed — folded] replan acceptance: Skeptic `revise` — folded both load-bearing points.
  (1) anchor all six pointer copies in their contract.json, mirroring the in-flight-check anchors
  those files already carry; (2) pin the wording to one verbatim sentence with 239 bytes
  (propose-ship-balanced's headroom) as the binding ceiling, and explicitly do NOT imitate the
  ~500-byte in-flight-check block sitting beside it. Skeptic's points 3-5 were informational
- [decided] review triage: 10 FIX, 2 IGNORE, 2 escalated (solo gate). Replan-vs-FIX considered
  and declined for #4/#7 — they refine the contract's contents, they do not change the approach,
  so they are FIX not replan. #2/#8 DID change the plan and went through Phase 2.5

## Review finding 2026-08-30

- The pointer count is now six surfaces. `2026-08-24-pattern-extracted-copies-split-into-shared-
  and-divergent-halves` predicts the next failure precisely: an anchor catches a DELETED copy but
  never a DRIFTED one. Byte-identity across the six is the invariant that covers the second case,
  and it is now a test rather than a convention
- [reviewed — folded] completion verification (2nd pass, on the replan-added criteria): Verifier
  `revise`. N1/N2/N3/N5/N6 reproduced clean; **N4 falsified** — I claimed "either escalation form"
  was anchored, but only the mid-lifecycle form was. Deleting the whole "At intake, before a work
  unit exists" bullet left `test_body_anchors[propose]` green. Closed with two anchors and
  mutation-tested with the Verifier's own deletion
- [decided] did NOT trigger Phase 2.5 for that N4 gap, despite the letter of the completion-gate
  rule ("a revise naming an unmet criterion → replan"). The criterion was correct and simply
  unmet — the plan did not change, the work lagged it. Phase 2.5 exists for when reality
  contradicts the plan; a replan entry reading "we missed an anchor, then added it" is noise in a
  durable record. Finished the work instead and re-verified with the exact mutation

## Review finding 2026-08-30 (2)

- Two independent verification passes each caught an anchor that pinned the framing while leaving
  the operative clause deletable — review finding #5 (heading anchored, carve-out body not) and
  gate finding N4 (one escalation form anchored, the other not). Same mistake twice in one unit,
  by different mechanisms. The lesson is narrower than "write anchors": when a clause is added
  *because* it is load-bearing, the anchor belongs on the clause that does the work, and the only
  way to know which one that is, is to delete it and watch
