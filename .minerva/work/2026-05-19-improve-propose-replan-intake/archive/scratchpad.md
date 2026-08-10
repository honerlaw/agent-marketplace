# Scratchpad: improve-propose-replan-intake

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `.minerva/decisions/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## 2026-05-18 — implementation notes

- Proposal does not currently test that `/propose <slug>` syntax is absent — tests are behavior/presence-based, not negative assertions. Acceptable since the command's text is the source of truth.
- `replan.md` usage section fully removed the explicit `NNN-slug` / substring-match forms. The "Identical to /replan:" text in `work.md` now diverges slightly from `/replan`'s actual resolution logic (work.md kept the explicit-arg forms). Leaving this for now — `/work` target resolution is out of scope for this work unit; it was not in the proposal.
- All six files updated: `propose.md`, `replan.md`, `work.md` (error message only), `init.md` (error message only), `README.md` (two lines), `using-minerva/SKILL.md` (two lines). All 12 tests pass.
