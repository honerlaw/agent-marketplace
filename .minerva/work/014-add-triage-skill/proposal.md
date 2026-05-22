# Proposal: add-triage-skill

**Date**: 2026-05-22
**Status**: Draft

## Goal

Add `minerva:triage` — a project-agnostic skill that investigates bugs end-to-end, from "something is broken" through "here is the root cause and recommended fix." Spans live production incidents (locate failing layer, gather evidence from logs/metrics, stay read-only against prod) and code-level root-causing (reproduce, trace failure through code, identify offending lines). Designed to subsume `superpowers:systematic-debugging`'s responsibilities so that skill can eventually be deprecated.

## Why

Production triage and code root-causing are halves of the same investigation: locate the failing component, then figure out why. Splitting them across two skills creates artificial handoff friction. The user intends to remove the `superpowers` plugin eventually, so `minerva:triage` needs to own the full bug-investigation lifecycle.

The proven workflow already exists in the seekless project's bespoke `debug-seekless` skill. Extracting it into a minerva skill — with project-specific operational refs moved out of the skill body and into a new `.minerva/reference/` directory — gives any minerva project the same value without each project maintaining its own debug skill.

This also formalizes a new `.minerva/reference/` tier in the minerva directory layout, alongside the existing `.minerva/knowledge/` tier:

- **`.minerva/knowledge/`** — atomic, past-tense, durable learnings (decisions / bugs / patterns / constraints). Named `NNN-<type>-<slug>.md`. Append-only, low churn. Always-read.
- **`.minerva/reference/`** — thematic, present-tense, operational facts about how the project is configured right now (topology, observability conventions, CLI recipes, bug-pattern catalogs). Named by topic. Replace-on-change, higher churn. Read on demand by skills that need them.

The load-bearing distinction is **time-shape**: knowledge accumulates over the project's life; reference is a snapshot that gets rewritten as the system evolves. This work unit doesn't migrate any existing project's docs into `.minerva/reference/` — it just defines the tier and the skill that consumes it. The first consumer (seekless) migrates as a follow-up.

## Approach

### Skill location and shape

New skill at `plugins/minerva/skills/triage/SKILL.md`. Project-agnostic — no specific tool names (no "Loki," "doctl," "kubectl") in the description. Tool details live in each project's `.minerva/reference/` files.

### Trigger phrasing

Description triggers on bug-investigation phrasing across both surfaces:

- **Live-incident framing**: "users are reporting," "X is broken in prod," "the cron didn't run," "500s," "queue is backed up," "we had an outage," past-tense incident phrasing.
- **Dev-bug framing**: "this test fails," "function returns wrong value," "unexpected error," "regression."

### Two-phase workflow

1. **Locate.** Restate the symptom in one sentence. Identify the failing component (which layer / subsystem / call site). Load relevant `.minerva/reference/` files via the discovery mechanism below. Cross-reference `.minerva/knowledge/` for past bugs / patterns / constraints matching the symptom. Pull evidence from the appropriate source — logs/metrics for live, repro/tests for dev.
2. **Root-cause.** Trace the failure through the code. Read call sites the evidence references. Form a hypothesis. Confirm with targeted reads or a focused repro. Identify offending lines and recommend a fix.

### Report structure

Final reply is structured as: **Symptom** / **Evidence** (with the exact queries/commands run) / **Root cause** (mapped to a known pattern if applicable) / **Recommended fix** / **What I did not check** (ruled-out vs. ran-out-of-time, to avoid false confidence).

### `.minerva/reference/` discovery mechanism

The skill cannot bake in project-specific filenames. The mechanism is dynamic:

1. `ls .minerva/reference/` to discover what files exist in this project.
2. Select 1-3 files for full read based on filenames + the symptom restatement. Filenames in this folder are descriptive by convention (e.g., `topology.md`, `observability.md`, `database.md`), so filename + symptom is enough to pick relevance without reading contents.
3. Always load any pattern-catalog-shaped file (matching names like `bug-patterns.md`, `incidents.md`, `patterns.md`) regardless of symptom-based selection. This is cheap insurance against re-discovering known bugs.
4. Also skim `.minerva/knowledge/` for atomic past learnings that match the symptom or hypothesis.

### Mutation discipline

Decision rule: **"Would this change persist in a system other users depend on?"**

- **Forbidden by default** (require per-turn explicit confirmation): production DB writes (DDL/DML), infrastructure changes (restart/redeploy/scale/rebuild/delete), sending messages on the user's behalf (Slack, email, PR comments), secret rotation, mutating CI/CD or feature flags, deploys, mutation CLI subcommands.
- **Always fine**: read-only operations anywhere (`SELECT`, `list`, `get`, `describe`, tailing logs); editing your own dev branch; running tests; adding logging in dev; writing repro scripts; reading code; calling read-only MCP tools.
- **The past-tense test**: if you'd describe the operation in past tense after running it ("I deleted…", "I restarted…", "I posted…"), it needs explicit confirmation. If you'd describe it as evidence ("I saw…", "I found…"), it's fine. When in doubt, prefer the read-only variant or ask.

### Knowledge-vs-reference callout

The skill body includes a short paragraph explaining the two `.minerva/` directories and how the skill uses them differently. This both teaches the convention and tells the skill's user where to look up the dual structure if confused.

### Catalog sync (per `010-constraint-minerva-skill-catalog-sync.md`)

Three surfaces updated in the same commit:

- `plugins/minerva/skills/using-minerva/SKILL.md` — add a row to the decision matrix. Situation phrasing covers both incident and dev-bug surfaces.
- `plugins/minerva/README.md` — add a row to the Skills table, lifecycle-positioned appropriately (likely near `using-minerva` since triage is orientation/diagnostic, not part of the propose→ship lifecycle).
- `README.md` (repo root) — append `minerva:triage` to the minerva row's Skills cell.

### Out-of-scope: seekless migration

The seekless project's `debug-seekless` skill and its references migrate to `~/Development/seekless/.minerva/reference/` as a follow-up, performed manually in that repo. It is not part of this work unit's diff or success criteria. Validation that the new skill works end-to-end happens organically when seekless adopts it — if `minerva:triage` produces a useful report against a real incident, the skill is right; if it doesn't, that triggers a `replan` or follow-up fix.

## Success criteria

- `plugins/minerva/skills/triage/SKILL.md` exists with project-agnostic frontmatter.
- Frontmatter description triggers on both live-incident framing AND dev-bug framing, stack-agnostic (no specific tool names).
- Skill instructions encode the two-phase Locate → Root-cause workflow.
- Skill instructions articulate the mutation discipline using the "persists in a system others depend on?" decision rule, with the past-tense test.
- Skill instructions specify the discovery mechanism (list `.minerva/reference/`, filename-driven selection, always-load pattern catalog; cross-reference `.minerva/knowledge/`).
- Skill body includes the knowledge-vs-reference callout paragraph.
- `plugins/minerva/skills/using-minerva/SKILL.md` decision matrix includes a `minerva:triage` row.
- `plugins/minerva/README.md` Skills table includes a `triage` row.
- Repo-root `README.md` Plugins table's minerva row lists `minerva:triage`.

## Open Questions

None remaining. The seekless migration and `superpowers` deprecation strategy are out of scope for this work unit and will be addressed separately.
