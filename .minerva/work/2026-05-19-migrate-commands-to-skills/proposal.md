# Proposal: migrate-commands-to-skills

**Date**: 2026-05-18
**Status**: Shipped (2026-05-19)

## Goal

Convert the five `commands/*.md` files (init, propose, replan, work, promote) into the skills format used by `using-minerva`, so all minerva functionality lives under `skills/*/SKILL.md`. Delete the `commands/` directory. Update `install.sh`, tests, README, and internal cross-references to use `minerva:<name>` invocation style.

## Why

- **Commands are a legacy format.** The Claude Code plugin system has moved to skills as the canonical extension point. Keeping `commands/` creates confusion about which format is authoritative.
- **Skills have a richer activation model.** The `description:` frontmatter in a skill is a trigger condition, not just documentation — it lets Claude auto-invoke the skill in appropriate contexts, not only on explicit user request.
- **Consistency.** `using-minerva` is already a skill. Having the five core actions live in a different format than the orientation skill is an internal inconsistency.
- **Invocation style.** `minerva:propose` is already how this session invokes these skills. Formalizing the layout matches the de-facto usage.

## Approach

1. **Create `skills/<name>/SKILL.md`** for each of the five commands. Each file:
   - Adds `name: <name>` to the existing frontmatter.
   - Updates `description:` from "what this does" to a trigger condition (e.g. "Use when the user invokes `minerva:propose` or asks to start a new minerva work unit").
   - Internal invocation references updated throughout (e.g. `/propose` → `minerva:propose`, `/replan` → `minerva:replan`).

2. **Delete `commands/`** directory entirely.

3. **Update `install.sh`** — replace the final listing loop from `commands/*.md` to `skills/*/SKILL.md`, and update the echo from "Commands available" to "Skills available". Format: `minerva:<name>` for each skill.

4. **Update `using-minerva/SKILL.md`** — the command decision matrix and scenario text currently references `/propose`, `/replan`, etc. Update all to `minerva:propose`, `minerva:replan`, etc.

5. **Update `README.md`** (plugin) — the Commands table becomes a Skills table; invocation style changes from `/propose` to `minerva:propose` throughout.

6. **Update `tests/test_minerva.py`** — the `_read_command()` helper and all `test_*_command_exists_with_frontmatter` tests need to read from `skills/<name>/SKILL.md` instead of `commands/<name>.md`. Also assert `name:` is present in frontmatter.

7. **Update root `README.md`** — the skills column currently lists `/init` etc.; update to `minerva:init` etc.

## Open Questions

- The `financials` plugin also uses `commands/*.md`. Migrating it is a future work unit.
