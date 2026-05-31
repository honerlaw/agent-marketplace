# Scratchpad: skill-contract-eval-floor

Running log for the work unit. Promoted/archived at `minerva:promote`.

## Panel decisions 2026-05-31

- [escalated to user] scope check: panel split 1/3 accept (Proponent accept / Skeptic + Arbiter reject → decompose). Escalated per scope-decomposition routing. **User chose "Unit 1 first (floor)"** — build the structural contract floor now, seed the behavioral value-runner as Unit 2. (Global escalation #1.)
- [3/3 accept, vote 2] approach selection: Approach 1 (externalized per-skill `evals/<skill>/contract.json` + generic parametrized `tests/test_skill_contracts.py`). Vote 1 was 1/3 (Proponent revise / Skeptic revise / Arbiter accept-if-folded); revision folded in: any-of+ignore_case anchors, no-vacuous-pass enumeration of all 13, parity proof before deletion, opaque reserved `behavioral` namespace, pyyaml frontmatter parsing. Vote 2 = 3/3 accept.
- [3/3 accept] whole-proposal acceptance: Proponent accept / Skeptic accept (concerns folded) / Arbiter accept. Folded before writing: (1) `using-minerva` cross_surface self-exclusion, (2) criterion 6 mechanical no-loss verification, (3) root enumeration at `PLUGIN_DIR` + frame cross_surface as expanding to all 13.

## Panel decisions 2026-05-31 (cont.)

- [3/3 accept] completion verification: Proponent / Skeptic / Arbiter all independently verified by running commands — missing contract reds the suite (`git mv` probe), 89/89 anchors non-vacuous, `lib` collection errors byte-identical to main (pre-existing, out of scope), parity faithful + widening-only. All 7 success criteria honestly met.

## Panel concerns 2026-05-31

(Logged for the work phase to honor — all already reflected in proposal Approach/Success criteria.)
- using-minerva contract must OMIT the `using-minerva` body surface (self-reference circular).
- Parity must be mechanically verified, not eyeballed: suite green after deletion + anchors shown to carry load.
- Enumeration must root at repo `plugins/minerva/skills/` (no `.minerva/worktrees/` copies).

## Review triage 2026-05-31

- [2/2 accept — tactical 2/3 quorum met] triage panel on review findings. Skeptic verified the boundary regex non-breaking on all 3 real surfaces; only one prefix family exists (`propose` ⊂ `propose-ship` ⊂ `propose-ship-auto`).
- **Finding 1 [correctness, low/latent] → FIX**: cross_surface + `minerva:`-prefixed anchor matching was plain substring, so `minerva:propose` could be satisfied by `minerva:propose-ship` (blunts catalog-sync detection for the propose family). Fixed via a centralized `_present()` helper applying a token-boundary regex `minerva:<skill>(?![\w-])` to BOTH code paths (`_anchor_satisfied` + `test_cross_surface`). Added `test_token_match_is_boundary_aware` as a regression guard.
- **Finding 3 [simplicity, low] → FIX**: deleted dead `SKILLS_DIR` binding in `test_minerva.py` (its only consumers migrated out).
- **Finding 6 [maintainability, low] → FIX**: documented the 1-element `any_of` idiom (case-insensitive single anchor) + the token-boundary behavior in `evals/README.md`.
- Findings 2, 4, 5 clean (correctness/spec/knowledge) — no disposition. No load-bearing divergence → no replan.
- Post-fix: minerva suite 74 passed; all 89 anchors re-verified load-bearing under the new boundary-aware matcher.

## Implementation log

**2026-05-31 — built the mechanism.**
- `tests/test_skill_contracts.py`: enumerates all skill dirs under `plugins/minerva/skills/`, fails if any lacks `evals/<skill>/contract.json`, parses frontmatter via `yaml.safe_load`, validates frontmatter / anchors (string or `{any_of, ignore_case}`) / cross_surface per skill. 67 tests, all green.
- `evals/<skill>/contract.json` for all 13 skills (the 5 previously-untested — cleanup, debug, grill-plan, propose-ship, propose-ship-auto — now have contracts → net coverage increase).
- `evals/README.md`: documents the format; reserves opaque `behavioral` namespace for Unit 2.
- Verified all 13 frontmatters parse with `yaml.safe_load`; verified all 13 skills present in root README + plugin README; all present in using-minerva body **except using-minerva itself** (self-exclusion honored: its contract sets `using_minerva_body: false`).

**Mechanical no-loss verification (criterion 3):** a one-off script removed each matched anchor (all alternatives, case-folded where applicable) from the body in-memory and confirmed the check then fails. **89/89 anchors carry load** — none is vacuous/always-true.

### Parity mapping — every per-skill assert in old `test_minerva.py` → subsuming contract clause

Migrated (deleted from `test_minerva.py`, now enforced by `evals/<skill>/contract.json` via `test_skill_contracts.py`):

- **propose**: name=="propose" → `frontmatter.values.name`; description truthy → `frontmatter.non_empty`; `"proposal.md"` / `".minerva/work/"` / `"scratchpad.md"` → anchors (strings); `brainstorm` OR `questions one at a time` (.lower) → anchor `any_of ignore_case`.
- **replan**: name; description; `"replan.md"` / `".minerva/work/"` / `"Original plan"` / `"What changed"` / `"New plan"` → string anchors; `most-recently-modified` OR `most recently modified` (.lower) → `any_of ignore_case`.
- **work**: name; description; `"scratchpad.md"` / `"proposal.md"` / `"replan.md"` / `".minerva/work/"` / `"minerva:replan"` → string anchors; `diverge`/`divergence` (.lower) → `any_of ignore_case`; `resume`/`left off` (.lower) → `any_of ignore_case`.
- **init**: name; description; `.minerva/work/` `.minerva/knowledge/` `.gitkeep` `.gitignore` `CLAUDE.md` `AGENTS.md` → string anchors; `Routing` OR `## minerva` (case-sensitive) → `any_of`; idempotent/idempotency/already-initialized (.lower) → `any_of ignore_case`; flat-layout/`mv work`/pre-existing (.lower) → `any_of ignore_case`.
- **promote**: name; description; end-of-work/end of work (.lower) → `any_of ignore_case`; single-item/single item/with argument (.lower) → `any_of ignore_case`; `PROMOTE` / `DISCARD` → string anchors; idempotent/idempotency (.lower) → `any_of ignore_case`; `.minerva/knowledge/` `.minerva/work/` → string anchors; new-engineer/year (.lower) → `any_of ignore_case`.
- **review**: name; description; `.minerva/work/` `proposal.md` `scratchpad.md` → strings; `git diff` OR `git status` → `any_of`; `FIX` `SUGGEST` `IGNORE` `minerva:promote` `minerva:replan` → strings; most-recently-modified (.lower) → `any_of ignore_case`.
- **ship**: name; description; `.minerva/work/` `proposal.md` `gh pr create` `gh pr merge --auto` `git checkout -b` → strings; `bare mode` (.lower) → `any_of ignore_case`; 3-iteration/three-iteration (.lower) → `any_of ignore_case`; auto-merge/auto merge (.lower) → `any_of ignore_case`; `minerva:promote` `minerva:review` → strings; most-recently-modified (.lower) → `any_of ignore_case`; `gh pr view` → string; Default-branch-detection (mixed-case) → `any_of ignore_case`; post-promote/`post-\`minerva:promote\`` → `any_of ignore_case`.
- **using-minerva**: `name: using-minerva` → `frontmatter.values.name`; `description:` → `frontmatter.required_keys`; `.minerva` in frontmatter → `frontmatter.contains`; body lists the 6 core `minerva:<skill>` tokens / `.minerva/work/` / `.minerva/knowledge/` → string anchors; anti-pattern/when not to use/NOT to use → `any_of ignore_case`.
- **cross-surface (root README per-skill loop, plugin README per-skill loop)**: each `minerva:<skill>` presence → that skill's `cross_surface.root_readme` / `cross_surface.plugin_readme`. **Expanded** from the legacy 6–7 skills to all 13 (all present today; net gain).

Kept in `test_minerva.py` (non-per-skill): `test_plugin_json_exists_and_parses`, `test_marketplace_lists_minerva`, `test_marketplace_does_not_list_feature_cycle`, `test_root_readme_mentions_minerva` (general "minerva" presence only), `test_root_readme_does_not_mention_feature_cycle`, `test_plugin_readme_structure` (README doc-structure: decisions/scratchpad/layout). Dead `_read_skill` helper removed.

**Mixed-case OR note:** a few legacy ORs mixed `.lower()` and case-sensitive alternatives (init `mv work`; ship `Default-branch detection`; using-minerva `NOT to use`). Encoded as `ignore_case: true` for the whole group — this only *widens* matching vs. the original, never narrows, so no coverage is lost; mechanical verification confirms each group still carries load.
