# Proposal: minerva-static-site

**Date**: 2026-06-10
**Status**: Shipped (2026-06-10)

## Goal
Build a simple, self-contained static site (`site/index.html` + `site/style.css`; no build step, no SSG, no external/CDN dependencies; viewable via `file://` with in-page anchor navigation) that presents the minerva plugin to a newcomer: the problems it solves, the full skill catalog, the lifecycle flow to use the skills in, and the bias deliberately built into the system. Includes one enumerating drift test for the catalog section.

## Why
minerva's existing surfaces (READMEs, SKILL.md frontmatter, the knowledge wiki) are reference-shaped; discovery work ([[032-pattern-plugin-discovery-mostly-auto-crawl]]) made the plugin findable, but nothing explains it narratively to someone deciding whether to adopt it. A "built-in bias" section makes the system's opinions explicit instead of leaving them implicit in skill prose.

## Approach
Panel-selected A′ (approach panel: second-vote 3/3; whole-proposal panel: second-vote 3/3):

1. **Hand-authored single-page site** under `site/` — `index.html` + `style.css` only, zero JS, semantic HTML, anchor nav, parchment/ledger editorial design on system font stacks (web fonts are impossible under the no-external-resources criterion). Three alternatives were rejected: a **generator** (not drift-proof without a CI regeneration check, and adds codegen to a no-build repo), an **SSG toolchain** (foreign dependency surface), and a **comment-nudge-only surface** with no test (repeats the mitigation [[010-constraint-minerva-skill-catalog-sync]] already records as insufficient — "a mitigation, not a guarantee").
2. **Skills-catalog section**: one entry per skill dir under `plugins/minerva/skills/`, each named with a token-boundary `minerva:<name>` and a description excerpted from that skill's `description:` frontmatter per [[010-constraint-minerva-skill-catalog-sync]] (verbatim or lightly trimmed; no fresh paraphrase). The section is delimited by pinned markers the test hard-codes:
   - opening: `<!-- skills-catalog: source of truth is each skill's SKILL.md description frontmatter; when adding a skill, add an entry here — tests/test_site_catalog.py enforces presence -->`
   - closing: `<!-- end skills-catalog -->`
3. **Drift detection, not generation**: new enumerating pytest `tests/test_site_catalog.py`, bidirectional — (a) every SKILL.md-bearing dir under `plugins/minerva/skills/` has its `minerva:<name>` token inside the delimited section; (b) every `minerva:<name>` token in the section maps to an existing skill dir (orphan check). It imports `_present` from `tests/test_skill_contracts.py` (hyphen-boundary token semantics; never reimplemented), includes a self-test that the orphan-direction extraction regex (`minerva:[a-z0-9-]+`) agrees with `_present`, and fails loudly if either marker is absent. Dependencies: pytest + pyyaml (already required by the CI test job via the `_present` import); no new dependencies. The file is added to the explicit pytest list in `.github/workflows/evals.yml` (an unlisted test never runs).
4. **Content sections**: (a) problems minerva solves (context loss across sessions, knowledge living only in chat, plans drifting silently from reality, unaudited AI judgment); (b) the lifecycle flow (explore → propose [grill-plan] → work [replan] → review → promote → synthesize → ship → cleanup; orchestrators propose-ship / propose-ship-auto; utilities round-table, debug, lint, lint-fix, migrate, init, using-minerva); (c) built-in bias, each claim traced on-page to its source: fail-closed skip predicate (propose-ship-auto; [[014-decision-per-decision-skip-over-sizing-gate]]), adversarial Proponent/Skeptic/Arbiter panels (round-table; [[033-decision-panel-mechanics-extracted-to-round-table]]), relentless plan interrogation (grill-plan), confirmation gates before mutation (lint-fix, synthesize, promote), observable signals over self-judgment ([[031-decision-phase-handoff-rides-observable-intake]], [[014-decision-per-decision-skip-over-sizing-gate]]), durable records over chat memory (promote + the knowledge tier), append-only knowledge bodies ([[016-constraint-promote-narrowed-never-overwrite]]).
5. **Honest on-page footer**: catalog *presence* is test-enforced; narrative content reflects the repo as of the authoring date; description text is excerpted at authoring time (no drift-proof claim). No hardcoded skill count anywhere in prose.
6. **Promote plan** (016-compliant; executed): knowledge entry [[034-constraint-site-fourth-catalog-surface]] records the site as a fourth test-enforced catalog surface — extending [[010-constraint-minerva-skill-catalog-sync]], bidirectionality scoped to the site surface only — and why it is deliberately NOT a `SURFACE_FILES` / `cross_surface` surface (editing all 19 `contract.json` files would have violated this unit's file-touch criterion; the bespoke enumerating test self-covers future skills). Reciprocal `## Related` links added on 010 and [[012-constraint-skill-structural-contracts]] (Related-span edits only; bodies are byte-identity-guarded).
7. **Deployment out of scope.** A future GitHub Pages deploy would use an Actions workflow (`docs/` already holds internal specs, so the no-Actions `/docs` mode is not a clean option). Linking the site from the READMEs is a named follow-up, not part of this unit.

## Success criteria
All verified at completion (3/3 panel) and re-verified after review fixes:

- ✓ `site/index.html` and `site/style.css` exist. Files created/modified outside `site/` are limited to: `tests/test_site_catalog.py` (new), one added line in `.github/workflows/evals.yml`, and `.minerva/` lifecycle artifacts (this unit's proposal/scratchpad/archive/followups, the new knowledge entry plus `index.md`/`overview.md` updates, and `## Related`-span edits to existing entries per [[016-constraint-promote-narrowed-never-overwrite]]). No README or other catalog-surface edits.
- ✓ (single http(s) occurrence = the permitted navigational repo link) Zero external resource loads: no `http(s)` reference in any resource-loading position — `<script src>`, `<link href>`, `<img src/srcset>`, `<iframe src>`, `<video/audio/source>`, CSS `@import`/`url(...)` in `site/style.css` or any inline `style`/`<style>` block. Navigational `<a href>` links to the project's GitHub repo are permitted. Verified by grepping every `http(s)` occurrence in both files.
- ✓ (4/4 tests; fault-injection verified loud failure) The delimited catalog section lists every current skill under `plugins/minerva/skills/` and nothing else; `tests/test_site_catalog.py` passes in both directions and fails loudly when either pinned marker is absent.
- ✓ The CI-scoped pytest suite (now 9 files) is green locally — 179 passed.
- ✓ (8 ledger entries, each with a src line) The bias section names a concrete source (skill or knowledge entry) on-page for every claim it makes.
- ✓ The footer carries the presence-test-enforced / point-in-time caveat; no hardcoded skill count in prose.

## Open Questions
- None.
