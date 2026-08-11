# Proposal: broaden-promote-knowledge-artifacts

**Date**: 2026-05-18
**Status**: Shipped (2026-05-18)

## Goal

Update `minerva:promote` to broaden what gets captured in `.minerva/knowledge/` (renamed from `.minerva/decisions/`) beyond purely architectural decisions. Specifically:

1. The PROMOTE partition explicitly includes bugs fixed and discovered bug/failure patterns — anything concrete and repeatable that helps a future LLM understand or diagnose problems.
2. Forward-looking items (future TODOs, "we should investigate X," planned fixes) are explicitly classified as DISCARD.
3. The knowledge entry template gains a `Type:` field (`decision` / `bug` / `pattern` / `constraint`) and renames its body sections to work for all types.
4. Knowledge filenames use a type prefix (e.g. `001-decision-use-postgres.md`, `002-bug-empty-queue-crash.md`).
5. The directory is renamed from `.minerva/decisions/` to `.minerva/knowledge/` throughout all commands, skills, and docs.

## Why

- **The old heuristic was too narrow.** "Architectural decisions" captures maybe 20% of what's actually worth recording. Bugs with non-obvious root causes, failure patterns, surprising constraints — these are exactly what a future LLM will hit again and waste time rediscovering.
- **Forward-looking items create noise.** A decisions file full of "we should eventually X" is worse than useless — it signals intent that may never happen, which misleads future readers. Concrete, past-tense facts only.
- **Type prefixes make the knowledge directory scannable.** When an LLM is triaging a bug, it can grep for `bug-*` entries first. When it's making a design choice, `decision-*` entries are the signal. Without prefixes, everything looks the same.
- **One flexible template is lower friction than per-type templates.** The shape (Context → Finding → Implications) works universally. The `Type:` field provides the classification without requiring a different workflow per artifact.

## Approach

1. **Update `promote.md` — partition criteria (Mode A).**
   - PROMOTE list gains explicit entries: bugs fixed (if the fix is non-obvious or the root cause could recur), discovered failure patterns, surprising constraints.
   - DISCARD list gains explicit entries: forward-looking TODOs, future investigation notes, "we should do X later" items regardless of how valuable they sound.
   - The heuristic line changes from "decisions almost always pass" to "concrete past-tense facts almost always pass."

2. **Update `promote.md` — knowledge entry template.**
   - Add `**Type**: decision | bug | pattern | constraint` field.
   - Rename `## Decision` → `## Finding`.
   - Rename `## Consequences` → `## Implications`.
   - Update field descriptions to be type-agnostic.

3. **Update `promote.md` — filename convention.**
   - Slugs gain a type prefix: `NNN-<type>-<slug>.md` (e.g. `001-decision-use-postgres.md`).
   - Update both Mode A and Mode B file-write instructions.

4. **Update `promote.md` — directory references.**
   - Replace `.minerva/decisions/` with `.minerva/knowledge/` throughout.

5. **Rename `.minerva/decisions/` → `.minerva/knowledge/` in all other files:**
   - `commands/init.md` — scaffolds the directory
   - `skills/using-minerva/SKILL.md` — hierarchy table and scenarios
   - `README.md` — hierarchy table and file layout diagram

6. **Update tests** in `tests/test_minerva.py` — assertions checking `.minerva/decisions/` updated to `.minerva/knowledge/`.

