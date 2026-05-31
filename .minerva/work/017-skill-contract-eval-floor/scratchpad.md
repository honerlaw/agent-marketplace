# Scratchpad: skill-contract-eval-floor

Running log for the work unit. Promoted/archived at `minerva:promote`.

## Panel decisions 2026-05-31

- [escalated to user] scope check: panel split 1/3 accept (Proponent accept / Skeptic + Arbiter reject → decompose). Escalated per scope-decomposition routing. **User chose "Unit 1 first (floor)"** — build the structural contract floor now, seed the behavioral value-runner as Unit 2. (Global escalation #1.)
- [3/3 accept, vote 2] approach selection: Approach 1 (externalized per-skill `evals/<skill>/contract.json` + generic parametrized `tests/test_skill_contracts.py`). Vote 1 was 1/3 (Proponent revise / Skeptic revise / Arbiter accept-if-folded); revision folded in: any-of+ignore_case anchors, no-vacuous-pass enumeration of all 13, parity proof before deletion, opaque reserved `behavioral` namespace, pyyaml frontmatter parsing. Vote 2 = 3/3 accept.
- [3/3 accept] whole-proposal acceptance: Proponent accept / Skeptic accept (concerns folded) / Arbiter accept. Folded before writing: (1) `using-minerva` cross_surface self-exclusion, (2) criterion 6 mechanical no-loss verification, (3) root enumeration at `PLUGIN_DIR` + frame cross_surface as expanding to all 13.

## Panel concerns 2026-05-31

(Logged for the work phase to honor — all already reflected in proposal Approach/Success criteria.)
- using-minerva contract must OMIT the `using-minerva` body surface (self-reference circular).
- Parity must be mechanically verified, not eyeballed: suite green after deletion + anchors shown to carry load.
- Enumeration must root at repo `plugins/minerva/skills/` (no `.minerva/worktrees/` copies).

## Implementation log

(work begins below)
