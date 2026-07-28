# Scratchpad: 047-pin-agent-dispatch-sync

## Balanced decisions 2026-07-27
- [reviewed — folded] scope check: single unit — Skeptic `revise`; folded the missed fifth surface (`propose-ship-balanced/SKILL.md:33` restates the dispatch params) and its 8960/9216 byte-budget constraint; folded the scope cut of the ship ScheduleWakeup TTL rationale (orthogonal defect class) → followups.md
- [reviewed — folded] approach: A (inline pin + enumerating test) — Skeptic `revise`; confirmed A dominant over B (no recurrence mechanism) and C (per-skill reference-pointer integrity blocks a shared file); folded the concrete conjunctive detector spec (verb AND token, fence-stripped) after the reviewer showed both naive heuristics fail in opposite directions; folded the correction that site 5 pins no params today
- [decided] whole-proposal soundness: sound (solo gate) — skill prose + one test, no public interface, contract anchors untouched, aligns with [[007]]/[[030]]/[[049]]
