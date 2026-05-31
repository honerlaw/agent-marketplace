# Proposal: skill-contract-eval-floor

**Date**: 2026-05-31
**Status**: Draft

> **Unit 1 of 2.** The user's request — "a mechanism to define and run evals against the
> skills to ensure they do not regress and are actually adding value" — was decomposed by a
> consensus panel into two sequenced units. This is Unit 1: the deterministic structural
> regression floor (the *do-not-regress* half) plus the shared `evals/` definition format.
> Unit 2 (the behavioral *adds-value* runner) is a seeded follow-up; see `followups.md`.

## Goal

Add a deterministic, declarative mechanism that defines each minerva skill's structural
**contract** and verifies it in pytest:

- required **frontmatter** keys (and select value constraints, e.g. `name` equals the skill
  directory name),
- required **body anchors** — substrings the `SKILL.md` body must contain, with `any_of`
  (disjunction) and `ignore_case` support so existing OR / `.lower()` checks survive intact,
- **cross-surface** catalog references — which catalogs (root `README.md`,
  `plugins/minerva/README.md`, `using-minerva` body) must list each skill, per knowledge
  constraint `010-constraint-minerva-skill-catalog-sync`.

Generalize the currently-hardcoded per-skill asserts in `tests/test_minerva.py` into this
mechanism with **no loss of coverage**, and **define the shared `evals/` eval-definition
format** that the sequenced follow-up behavioral value-runner (Unit 2) will consume.

## Why

minerva is 13 skills with intricate cross-references: catalog sync across three surfaces,
body anchors that encode each skill's load-bearing protocol, and frontmatter every skill must
carry. The only automated guard today is `tests/test_minerva.py` — per-skill **hardcoded**
assert functions. Two problems:

1. Adding a skill means hand-writing a new test function. Only **8 of 13** skills actually
   have one today; `cleanup`, `debug`, `grill-plan`, `propose-ship`, and `propose-ship-auto`
   have **none**, so structural coverage silently lags the skill set.
2. Cross-skill invariants are duplicated per function instead of expressed once.

A declarative per-skill contract plus a generic runner that **enumerates all 13 skills and
fails when any lacks a contract** makes the floor uniform, extensible, and impossible to leave
vacant for a new skill. It catches the "skill edited, required anchor deleted" regression for
every skill at once — the *do-not-regress* half of the request. It is also the foundation
Unit 2 builds on: the behavioral runner consumes the same `evals/<skill>/` layout and
eval-definition format established here.

## Approach

### Eval-definition format (`evals/`)

- New top-level `evals/` directory. Each skill gets `evals/<skill>/contract.json`.
- A `contract.json` declares:
  - `frontmatter` — required keys, with optional value constraints (e.g. `name` must equal
    the skill directory name; `description` must be non-empty).
  - `anchors` — a list of body anchors. An anchor is **either** a plain string (must-contain,
    case-sensitive) **or** an object `{"any_of": ["...", "..."], "ignore_case": true}` that
    faithfully encodes the existing OR-disjunction / `.lower()` asserts (e.g.
    `"most-recently-modified"` OR `"most recently modified"`; the three-way ORs in `init` /
    `promote`).
  - `cross_surface` — the catalogs this skill must appear in. Modeled **per-skill** so
    exceptions are expressible. **Note the `using-minerva` self-exclusion:** the
    `using-minerva` body lists every *other* skill but not itself (self-reference is circular,
    per constraint 010), so its contract must **omit the `using-minerva` body surface** while
    still requiring presence in the root and plugin READMEs.
- `evals/README.md` documents this structural format **and reserves a single opaque
  `behavioral` namespace** — a key Unit 2 owns wholesale. No behavioral fields are designed
  now; reserving the namespace (not its contents) is the minimal honest seam to Unit 2 and
  avoids freezing an interface against a consumer that does not yet exist.

### Runner (`tests/test_skill_contracts.py`)

- **Enumerates all 13 skill dirs** under the repo's `plugins/minerva/skills/` (anchored via
  `REPO_ROOT`/`PLUGIN_DIR` exactly as `test_minerva.py` does — **not** a loose glob, so it
  never picks up `.minerva/worktrees/` copies). **Fails if any skill dir lacks a
  `contract.json`** (no vacuous pass).
- Parses each `SKILL.md` frontmatter with `yaml.safe_load` (pyyaml 6.0.3 is already installed)
  instead of the hand-rolled colon-split parser.
- Parametrized per skill (one clean failure per skill). For each: validates required
  frontmatter keys/values, every anchor (honoring `any_of` + `ignore_case`), and the declared
  `cross_surface` references.

Because the enumeration covers all 13 skills, `cross_surface` is **expanded** to the 5
previously-untested skills as well (today only 6–7 skills per surface are checked). All 13 are
in fact present in the catalogs today, so this is a net coverage increase that stays green.

### Migration with parity proof

- Before deleting any per-skill assert from `tests/test_minerva.py`, record a reviewable
  **parity mapping**: every existing per-skill assert → the contract clause that subsumes it.
  Keep this mapping in `scratchpad.md` (and surface it in the PR body) so a reviewer can
  confirm no-loss.
- **Mechanically verify** the parity, not just by eyeball: after the migrated asserts are
  deleted, the full suite must stay green, **and** each new contract clause must be shown to
  actually carry load (spot-check that removing an anchor from a `SKILL.md` makes its contract
  test fail) so a typo'd / always-true anchor cannot pass vacuously.
- After parity is shown, remove the migrated per-skill asserts from `test_minerva.py`.
  **Non-per-skill checks stay** in `test_minerva.py`: `marketplace.json` validity, the
  minerva-registered check, and the feature-cycle-absence guards.

### Scope guard

Ship the mechanism + `contract.json` for all 13 skills + `evals/README.md`. **Do not** build
the behavioral runner — Unit 2 (behavioral with-vs-without value measurement via `claude -p` +
LLM-as-judge) is seeded as a follow-up.

## Success criteria

1. `evals/<skill>/contract.json` exists for **all 13** minerva skills; `tests/test_skill_contracts.py`
   enumerates all 13 and **fails if any contract is missing**.
2. The anchor schema supports `any_of` groups + `ignore_case`; every per-skill assert currently
   in `test_minerva.py` is represented by a contract clause (faithful, no loss).
3. A reviewable parity mapping (assert → contract clause) is recorded in `scratchpad.md` before
   the migrated asserts are deleted, and parity is **mechanically verified** (suite green after
   deletion; anchors shown to carry load, not pass vacuously).
4. `test_skill_contracts.py` parses frontmatter via pyyaml and passes for all 13 skills; the
   full pytest suite is green.
5. `evals/README.md` documents the structural contract format and reserves an opaque
   `behavioral` namespace (no named fields) for Unit 2.
6. The `using-minerva` self-exclusion is honored (its contract omits the `using-minerva` body
   surface); non-per-skill checks remain in `test_minerva.py`; no coverage is lost in the
   migration.
7. Unit 2 (behavioral value runner) is recorded in `followups.md`.

## Open Questions

- **Cross-surface granularity** — assert exact `using-minerva` table-row situation phrasing, or
  just skill-token presence? *Lean: presence only (matches what the current tests do;
  exact-phrasing is brittle).* Non-load-bearing; resolved during work.
- **Orchestrator anchors** — `propose-ship` / `propose-ship-auto` currently have no body
  anchors. *Lean: give each a minimal, non-tautological anchor set — e.g. each must reference
  the skills it orchestrates (`minerva:ship`, `minerva:cleanup`, etc.) — so the contract is not
  vacuous.* Non-load-bearing; resolved during work.
