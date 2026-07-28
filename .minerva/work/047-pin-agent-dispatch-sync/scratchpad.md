# Scratchpad: 047-pin-agent-dispatch-sync

## Balanced decisions 2026-07-27
- [reviewed — folded] scope check: single unit — Skeptic `revise`; folded the missed fifth surface (`propose-ship-balanced/SKILL.md:33` restates the dispatch params) and its 8960/9216 byte-budget constraint; folded the scope cut of the ship ScheduleWakeup TTL rationale (orthogonal defect class) → followups.md
- [reviewed — folded] approach: A (inline pin + enumerating test) — Skeptic `revise`; confirmed A dominant over B (no recurrence mechanism) and C (per-skill reference-pointer integrity blocks a shared file); folded the concrete conjunctive detector spec (verb AND token, fence-stripped) after the reviewer showed both naive heuristics fail in opposite directions; folded the correction that site 5 pins no params today
- [reviewed — folded] completion verification: Verifier `accept` on all 6 criteria (independently re-ran both negative tests, swept all 21 SKILL.md byte budgets); folded its non-blocking observation as load-bearing (b) — detector verbs were `spawn|dispatch` only, so a future site using `launch` (the Agent tool's own canonical verb) would slip the guarantee; widened to `spawn|dispatch|launch|invoke|create`, precision re-verified (still exactly 5 sites; `Skill`-tool handoff prose still excluded)
- [decided] review triage (solo gate): 3 medium + 3 low + 2 informational from the local-diff reviewer — 4 FIXed, 2 IGNOREd with rationale, 1 carried to promote

## Review triage 2026-07-27
- **F1 [medium] FIX** — `` `Agent` tool `` token required the exact backtick split; site 5 (`review/references/protocol.md`) rests on that token alone, so a cosmetic reformat would silently drop it. Token now tolerant of all three markdown forms + case-insensitive (subsumes F5).
- **F2 [medium] FIX** — fence handling was a bare toggle: an unclosed fence hid every following line, and a `~~~` inside a ``` block closed it early. Replaced with delimiter-aware pairing (built on `FENCE_RE`, per [[037]]) plus `has_unclosed_fence` and a corpus-wide guard test.
- **F3 [medium] FIX** — `test_detector_excludes_prose` exercised only one axis (verb, no token). Added synthetic `test_detector_recall` / `test_detector_precision` covering both axes, plus fence-pairing and unclosed-fence unit tests, matching `test_skill_budget.py`'s rigor.
- **F6 [low] FIX** — reworded the `review/references/protocol.md` pin so it no longer interrupts the "dispatch … to perform" clause.
- **F4 [low] IGNORE** — `_unfenced_lines` duplication with `test_skill_budget.py`: the two implementations now legitimately differ (this one pairs delimiters and reports unclosed fences), so sharing would couple a stricter parser to a module that doesn't need it.
- **F7 [low] IGNORE** — `docs/superpowers/specs/` and prior `.minerva/work/*/proposal.md` describe the old mechanism; those are frozen point-in-time records, not living docs.
- **F8 [informational] → promote** — knowledge entry `045-decision-propose-ship-balanced-single-reviewer.md` states the reviewer dispatch params without the pin; cross-link it when promoting 047.
- [decided] whole-proposal soundness: sound (solo gate) — skill prose + one test, no public interface, contract anchors untouched, aligns with [[007]]/[[030]]/[[049]]
