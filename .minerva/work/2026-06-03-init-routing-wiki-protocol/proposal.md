# Proposal: init-routing-wiki-protocol

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> Make the agent-file Routing section teach the LLM the wiki **reading protocol** — what
> to look at on session start and recover from after compaction — and give existing
> repos a **gated refresh** path, discharging init's recorded "`--refresh` mode out of
> scope for v1" deferral.

## Goal

1. Update `minerva:init`'s Routing-section template to the wiki reading protocol:
   `overview.md` first (theme synthesis; absent until `minerva:synthesize` first runs →
   fall back to the index), `index.md` for catalog lookup, entries on demand via
   `[[NNN-type-slug]]` links, `.minerva/reference/` for present-tense operational docs,
   `.minerva/work/` for historical reasoning.
2. Add a **gated refresh offer** in idempotent mode so existing repos (whose Routing
   sections predate the wiki) can adopt the protocol — never auto.
3. Dogfood: refresh **this repo's** pre-020 CLAUDE.md via the new flow.

## Why

The wiki's layered structure (overview → index → entries; reference tier) was built to
give an LLM a cheap, structured entry point — but the Routing section that *directs* the
LLM predates it. init's idempotent detection (correctly lenient per
[[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]]) never revisits an
existing section, so every initialized repo — including this one — is permanently stale
without a refresh path. init's own out-of-scope explicitly deferred that path
("a `minerva:init --refresh` mode … out of scope for v1"); this unit pays that debt.

## Approach (panel-confirmed; template and anchors pinned byte-for-byte)

### 1. The pinned Routing template

```markdown
## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/overview.md` — theme-grouped synthesis of everything known. Read first to orient (absent until `minerva:synthesize` first runs — fall back to the index).
- `.minerva/knowledge/index.md` — the catalog, one line per entry. Look up specifics here; drill into entries via their `[[NNN-type-slug]]` links only when a theme bears on your task.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/NNN-<slug>/`. Invoke the `minerva:using-minerva` skill (via the `Skill` tool) for the full methodology.
```

**Detection arithmetic** (keeps [[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]]
satisfied): lines after `## minerva` = blank(1), prose(2), blank(3), overview bullet(4)
— whose path `.minerva/knowledge/overview.md` contains the required `.minerva/knowledge/`
substring → inside the existing 6-line window; **no widening**. All legacy path tokens
(`.minerva/knowledge/`, `.minerva/reference/`, `.minerva/work/`, `index.md`) remain in
the template, so every existing contract anchor keeps passing. No `overview.md` stub is
ever scaffolded ([[2026-06-03-decision-synthesis-layer-separate-file-advisory]]: synthesize owns
that file) — the bullet's parenthetical handles the fresh-scaffold case.

### 2. Gated refresh offer (idempotent mode, per detected agent file)

Inside Step 3's existing per-file loop (CLAUDE.md / AGENTS.md / GEMINI.md): when the
`## minerva` section is **detected** but **stale**, offer a refresh.

- **Staleness (generic, disjunctive):** the section is stale if it is missing **any** of
  the **current template's** `.minerva/...` path-bullet substrings — derived from the
  template-of-record, never a hardcoded list (so the mechanism cannot rot the way the
  template did). Note the deliberate quantifier asymmetry: *detection* requires both
  signals (conjunction); *staleness* fires on any missing marker (disjunction).
- **Gate:** show the full before/after diff with: "This section may be from an older
  template, or **you may have customized it** — refreshing replaces the whole section, so
  anything custom inside it will be removed." Proceed only on explicit confirmation.
  Never auto-refresh.
- **Boundary:** replace from the `## minerva` heading line up to but **not** including
  the next line matching `^## ` (exactly two hashes + a space — a `### ` subsection does
  **not** terminate the section), or EOF. A worked example lives in the SKILL text.
- Splice-preserving refresh (keeping unrecognized custom lines) is recorded as **future
  hardening**, not v1.

### 3. Plumbing

- **Step 4 commit offer:** trigger widened from "newly created" to "newly created **or
  refreshed**"; refreshed files included in the `git add` paths.
- **Step 5 report:** agent-file lines gain a `✓ Routing section refreshed` variant.
- **Out of scope list:** the "`--refresh` mode … out of scope for v1" bullet is deleted
  (discharged — refresh ships as the idempotent-mode offer, not a flag); bullets added
  for "auto-refreshing without the gate" and "splice-preserving refresh (future
  hardening)".
- **Contract ([[2026-05-31-constraint-skill-structural-contracts]]):** `evals/init/contract.json`
  gains the exact literals `overview.md` and `you may have customized it`.

### 4. Dogfood

Refresh this repo's CLAUDE.md (currently the pre-020 two-bullet form) to the pinned
template via the new flow. This exercises the EOF boundary branch (the section is the
whole file's tail); the next-`^## ` branch is covered by the worked example and is
honestly noted as not dogfood-exercised.

## Success criteria

1. init's Routing template equals the pinned text above, byte-for-byte; the detection
   note records the new arithmetic (overview bullet at line 4 after the heading; 6-line
   window unchanged).
2. The refresh offer exists in Step 3's per-file loop with: generic disjunctive staleness
   markers (derived from the current template), the gate text containing the literal
   "you may have customized it" + the removal warning + the full diff, the `^## `-or-EOF
   boundary rule with a worked example, and never-auto.
3. Step 4's trigger says "newly created or refreshed" (refreshed files in `git add`);
   Step 5 has the `refreshed` report variant; the old `--refresh` out-of-scope bullet is
   gone; the two new out-of-scope bullets are present.
4. `evals/init/contract.json` gains the anchors `overview.md` and
   `you may have customized it`; `tests/test_skill_contracts.py` passes.
5. **Idempotency round-trip (by inspection — init is LLM-executed prose, no binary):**
   applying the detection rule to the refreshed CLAUDE.md shows (a) the section
   re-detects as present (heading + `.minerva/knowledge/` within 6 lines → no
   re-append), and (b) the staleness disjunction finds zero missing markers (→ no second
   offer).
6. This repo's CLAUDE.md is refreshed to the pinned template (the dogfood; diff visible
   in the PR — the PR review is the gate evidence).
7. Full enumerated CI suite green; no frozen file touched; no `.minerva/knowledge/`
   writes before promote.

## Open Questions

- None load-bearing.

## Out of scope

- Splice-preserving refresh (future hardening — preserve unrecognized lines).
- Auto-refreshing without the gate (agent files are user territory).
- Creating AGENTS.md / GEMINI.md in this repo (init only writes Routing into files that
  already exist).
- Changing `minerva:using-minerva` (the methodology doc — Routing routes, it doesn't
  teach).
- Scaffolding an `overview.md` stub (synthesize-owned, per 024).
