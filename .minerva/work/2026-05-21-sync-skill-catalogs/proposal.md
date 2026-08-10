# 013 — sync skill catalogs

## Status
Shipped (2026-05-21)

## Goal
Update minerva plugin orientation surfaces so every skill under `plugins/minerva/skills/` is referenced in catalog-style enumerations.

## Why
Three catalog-style surfaces have drifted from the actual skill directory (`plugins/minerva/skills/`, the runtime source of truth per `.minerva/knowledge/004-constraint-plugin-skills-auto-discovered-from-directory.md`):

- `plugins/minerva/README.md` skills table → missing `grill-plan` (11/12).
- `plugins/minerva/skills/using-minerva/SKILL.md` skill decision matrix → missing `grill-plan` and `propose-ship-auto`.
- Top-level `README.md` plugins-table cell for `minerva` → missing `cleanup`, `grill-plan`, `using-minerva` (9/12).

These surfaces orient humans browsing the repo and Claude itself (`using-minerva` auto-loads in minerva projects). Missing entries make those skills effectively invisible to anyone relying on these surfaces.

## Approach

1. **`plugins/minerva/README.md` skills table.** Added a single new row for `minerva:grill-plan` between the existing `minerva:replan` and `minerva:work` rows. The existing table order was lifecycle order (`init → propose → replan → work → promote → review → ship → cleanup → propose-ship → propose-ship-auto → using-minerva`); `grill-plan` was placed in the plan-drafting cluster since it is invoked by both `propose` and `replan`, preserving the planning-vs-execution boundary.

2. **`plugins/minerva/skills/using-minerva/SKILL.md` skill decision matrix.** Added two rows:
   - `grill-plan` row, slotted between the existing "Reality has diverged…" `minerva:replan` row and the "Approved a proposal but want to tweak it…" row. Situation phrasing: *"Just drafted a plan and want to stress-test it before approving"* → `minerva:grill-plan` (auto-invoked by `minerva:propose` and `minerva:replan`; usable standalone on any drafted plan).
   - `propose-ship-auto` row, immediately after the existing `propose-ship` row. Situation phrasing: *"Run the whole lifecycle end-to-end without human gates (consensus panels replace decisions)"* → `minerva:propose-ship-auto`. The phrasing was made deliberately distinct from `propose-ship`'s existing "Run the whole lifecycle end-to-end from scratch" so readers wanting gates pick `propose-ship` and readers wanting full automation pick `propose-ship-auto`.

3. **Top-level `README.md` plugins-table.** In the row for `minerva`, edited the "Skills" cell to include `minerva:cleanup`, `minerva:grill-plan`, `minerva:using-minerva` alongside the existing 9 — bringing the cell to all 12 skills. Same space-separated backtick-wrapped format. Cell remained visually fine without `<br>` groupings.

4. **Text-sourcing rule for new rows.** Each new row's description text is a verbatim or lightly-trimmed excerpt of the corresponding skill's `SKILL.md` `description:` frontmatter. `"Use when…"` trigger prose was trimmed off the front; the next descriptive clause carried into the row. No paraphrasing. The rule applies to NEW rows only — existing rows kept their rich-prose style (retroactive rewrite was out of scope). The Phase-2 completion-verification panel caught a paraphrase in the first draft of the `grill-plan` row; the commit was amended to use a faithful excerpt before promote.

5. **HTML-comment convention reminder above each catalog table.** Added a single `<!-- ... -->` line above each of the three catalog surfaces noting: *"Source of truth: each row's text is excerpted from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too."* This is a **zero-infrastructure write-time convention** — distinct from CI/script drift-prevention automation (deferred to a follow-up; see `followups.md`).

## Success criteria

- For each of the 12 skill subdirectories under `plugins/minerva/skills/`, the literal string `minerva:<skill>` appears at least once inside the `## Skills` table in `plugins/minerva/README.md`.
- For each of the 12 skills, `minerva:<skill>` appears at least once inside the `## Plugins` table cell for `minerva` in the top-level `README.md`.
- For each of the 11 skills excluding `using-minerva` (self-reference in its own matrix would be circular), `minerva:<skill>` appears at least once inside the `## Skill decision matrix` section of `plugins/minerva/skills/using-minerva/SKILL.md`.
- An `<!-- ... -->` HTML comment naming "SKILL.md frontmatter" as the source of truth appears immediately above each of the three catalog tables/cells.
- Verification commands: `grep -c 'minerva:<skill>' <file>` ≥ 1 for each pair, plus visual confirmation that each match is inside the relevant section (not anywhere in the file).

## Out of scope

- Root `CLAUDE.md` Routing section and `init/SKILL.md` Routing template — both intentionally name only `using-minerva` as the entry point; they are routing, not catalogs.
- `.claude-plugin/marketplace.json` — describes plugins, not individual skills.
- Cross-references inside other SKILL.md files where one skill mentions another in workflow narration (e.g., `propose.md` mentioning `grill-plan`). Not enumeration catalogs.
- Drift-prevention automation (CI check, pre-commit hook, generator script) — different shape of work; surfaced as a follow-up suggestion if drift recurs after this fix lands.
- Retroactive rewrite of existing catalog rows to match the new text-sourcing rule.

## Open Questions

None remaining; scope, approach, placement, phrasing, and count semantics were resolved by the scope / approach / whole-proposal panels.
