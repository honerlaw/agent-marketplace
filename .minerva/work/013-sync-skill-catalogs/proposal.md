# 013 — sync skill catalogs

## Status
Draft

## Goal
Update minerva plugin orientation surfaces so every skill under `plugins/minerva/skills/` is referenced in catalog-style enumerations.

## Why
Three catalog-style surfaces have drifted from the actual skill directory (`plugins/minerva/skills/`, the runtime source of truth per `.minerva/knowledge/004-constraint-plugin-skills-auto-discovered-from-directory.md`):

- `plugins/minerva/README.md` skills table → missing `grill-plan` (11/12).
- `plugins/minerva/skills/using-minerva/SKILL.md` skill decision matrix → missing `grill-plan` and `propose-ship-auto`.
- Top-level `README.md` plugins-table cell for `minerva` → missing `cleanup`, `grill-plan`, `using-minerva` (9/12).

These surfaces orient humans browsing the repo and Claude itself (`using-minerva` auto-loads in minerva projects). Missing entries make those skills effectively invisible to anyone relying on these surfaces.

## Approach

1. **`plugins/minerva/README.md` skills table.** Insert a single new row for `minerva:grill-plan` between the existing `minerva:replan` and `minerva:work` rows. The existing table order is lifecycle order (`init → propose → replan → work → promote → review → ship → cleanup → propose-ship → propose-ship-auto → using-minerva`); `grill-plan` belongs in the plan-drafting cluster since it is invoked by both `propose` and `replan`. Placing it after `replan` and before `work` preserves the planning-vs-execution boundary.

2. **`plugins/minerva/skills/using-minerva/SKILL.md` skill decision matrix.** Add two rows:
   - `grill-plan` row, slotted between the existing "Reality has diverged…" `minerva:replan` row and the "Approved a proposal but want to tweak it…" row. Situation phrasing: *"Just drafted a plan and want to stress-test it before approving"* → `minerva:grill-plan` (auto-invoked by `minerva:propose` and `minerva:replan`; usable standalone on any drafted plan).
   - `propose-ship-auto` row, immediately after the existing `propose-ship` row. Situation phrasing: *"Run the whole lifecycle end-to-end without human gates (consensus panels replace decisions)"* → `minerva:propose-ship-auto`. Phrasing is deliberately distinct from `propose-ship`'s existing "Run the whole lifecycle end-to-end from scratch" so readers wanting gates pick `propose-ship` and readers wanting full automation pick `propose-ship-auto`.

3. **Top-level `README.md` plugins-table.** In the row for `minerva`, edit the "Skills" cell to include `minerva:cleanup`, `minerva:grill-plan`, `minerva:using-minerva` alongside the existing 9. Use the same space-separated backtick-wrapped format as the existing list. If the cell becomes visually unwieldy after the edit, the implementer may insert `<br>` between logical groupings — judged at write-time.

4. **Text-sourcing rule for new rows.** Each new row's description is a verbatim or lightly-trimmed excerpt of the corresponding skill's `SKILL.md` `description:` frontmatter. If the frontmatter begins with a `"Use when…"` trigger, trim that prefix and take the next descriptive clause. No paraphrasing or fresh-writing. This rule applies to NEW rows only — existing rows keep their current rich-prose style. Retroactive rewrite is out of scope.

5. **HTML-comment convention reminder above each catalog table.** Add a single `<!-- ... -->` line above each of the three catalog surfaces noting: *"Source of truth: each row's text is excerpted from the skill's SKILL.md `description:` frontmatter. When you add a skill to `plugins/minerva/skills/`, add a row here too."* This is a **zero-infrastructure write-time convention** — qualitatively distinct from CI/script drift-prevention automation (which was deliberately scoped out by the scope-check panel). It costs one line per catalog, adds zero ongoing maintenance burden, and degrades gracefully — an author who ignores it produces the same drift we are fixing today, no worse.

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
