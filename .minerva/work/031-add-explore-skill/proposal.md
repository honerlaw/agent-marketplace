# Proposal: add-explore-skill

**Date**: 2026-06-07
**Status**: Draft

## Goal
Add a new minerva skill, `minerva:explore` — a divergent, commitment-free brainstorming skill that turns a fuzzy idea into clarity through collaborative, one-question-at-a-time dialogue, **without** writing any file, allocating a work unit, or creating a branch/worktree. It is the minerva analog of `superpowers:brainstorming`: the optional *divergent* phase **before** `minerva:propose`. It explores the problem space (including whether to build at all) and, when a direction is chosen, hands off to `minerva:propose` to design it.

## Why
`minerva:propose` already runs a brainstorm-style intake, but it is **convergent**: its telos is always the `proposal.md` artifact (plus slug, NNN, branch, worktree). There is no lightweight, zero-commitment mode for genuinely *exploring* an idea — weighing high-level directions, surfacing unknowns, and deciding whether the work is even worth a proposal — before that machinery engages.

`superpowers:brainstorming` is exactly that divergent exploration, and the user asked for "the same thing as superpower brainstorming but in minerva … not building an exact plan yet, just exploring things." superpowers deliberately keeps brainstorming as a skill **separate** from its planning skill; minerva should mirror that separation with an `explore` skill whose terminal state is handing off to `minerva:propose`.

## Approach
Add a pure-prose skill `plugins/minerva/skills/explore/SKILL.md` modeled on `superpowers:brainstorming`, plus a **bounded boundary edit** to `minerva:propose` and the standard skill scaffolding.

**`minerva:explore` (new skill):**
- **Divergent dialogue on the problem axis.** Explore project context first (`CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/`, recent work), then ask questions **one at a time** (multiple-choice preferred), focused on the problem / purpose / constraints / high-level directions — *not* locking an implementation. Weigh multiple directions with tradeoffs.
- **Commitment-free by construction** — the load-bearing identity. The skill explicitly **writes no file**, allocates no work unit (no slug/NNN), and creates no branch or worktree. Exploration lives in the conversation. Stated as guardrail prose in the body.
- **Three legitimate terminal outcomes:** (a) *drop* — "this isn't worth building"; (b) *reframe* — "the real problem is Y"; (c) *ready* — a direction is chosen.
- **Handoff on outcome (c) only**, via an explicit `Skill`-tool invocation of `minerva:propose "<converged direction>"`, passing the converged direction as the **inline argument** (a tool call, not narrated prose — per [[007-constraint-skills-must-call-tools-not-prose]]).

**Bounded boundary edit to `minerva:propose`:**
- Add a short convergent/divergent boundary note referencing `minerva:explore`: `propose` is the convergent design step that always produces the proposal; `explore` is the optional upstream divergent phase that may end in don't-build. When a direction arrives **inline** (propose's *existing, tested* step-1 inline-arg intake path), propose confirms/refines it and does **not** re-litigate whether/what to build — it proceeds to design (its normal clarifying questions + 2–3 *implementation* approaches).
- This deliberately uses **no session-scan and no self-judged "did exploration converge?" predicate** — the handoff rides propose's existing inline-arg behavior (an observable: an inline arg was passed or it wasn't), avoiding the gameable-skip failure mode of [[014-decision-per-decision-skip-over-sizing-gate]] / [[030-pattern-rejected-alternative-reinvented-at-runtime]].
- Anchor the boundary clause in `evals/propose/contract.json` (a must-contain anchor on the literal `minerva:explore`) so the boundary note can't be silently deleted (per 030). The anchor is additive and safe for propose's existing tests **provided the literal is written into `propose/SKILL.md` in the same change**.

**Why explore and propose don't overlap:** `explore` diverges on the *problem/direction* axis (what / whether to build); `propose` diverges on the *implementation-approach* axis (how to build the chosen direction — its existing "propose 2–3 approaches" step). Different axes — they compose, not duplicate.

**Scaffolding (mandatory per project conventions):**
- `evals/explore/contract.json` — `skill: "explore"`, frontmatter required keys, body anchors covering the load-bearing behaviors, and `cross_surface` requiring all three surfaces ([[012-constraint-skill-structural-contracts]]). Evals live at **repo-root `evals/<skill>/`**, not under `plugins/minerva/`.
- `evals/explore/behavioral.json` — ≥1 case with a rubric (advisory per [[013-decision-behavioral-evals-provisional]]).
- Three catalog edits ([[010-constraint-minerva-skill-catalog-sync]]): root `README.md` minerva row, `plugins/minerva/README.md` Skills table, and `using-minerva/SKILL.md` (decision matrix — placing `explore` **before** `propose` on the commitment axis — plus a Common-scenarios entry). The using-minerva row text is copied from `explore`'s `description:` frontmatter (per the matrix source-of-truth comment).

**Name resolved to `explore`** (not `brainstorm`): `superpowers:brainstorming` already exists in this environment and `propose` already "mirrors the superpowers:brainstorming flow", so `brainstorm` invites confusion; `explore` names the divergent pre-commitment phase distinctly. The name is the dir name, the `contract.skill` field, the `name:` frontmatter, the eval-dir name, and the `minerva:explore` catalog token.

**Committed anchor literals** (so the contract is mechanically checkable):
- `explore/SKILL.md` body must contain the must-contain anchors `one at a time`, `writes no file`, and `minerva:propose` (a **bare** token — the inline-arg handoff line supplies it; boundary-aware matching means it is *not* satisfied by `minerva:propose-ship`/`-auto`), plus an `any_of` anchor over the three-outcome / commitment-free language.
- `evals/propose/contract.json` gains a must-contain anchor on the literal `minerva:explore` (absent from `propose/SKILL.md` today, so the anchor is genuinely load-bearing).

**Rejected candidates:**
- **B — persist exploration notes to a durable location** (e.g. `.minerva/explore/<slug>.md`): rejected — manufactures the commitment `explore` disclaims and introduces an untracked location that fights minerva's NNN/work-unit model (would require `minerva:init` + persistence-hierarchy changes).
- **C — an `--explore` flag on `minerva:propose`** instead of a new skill: rejected — muddies propose's one-skill-one-contract convergent identity, and the user asked for a separate skill mirroring superpowers' brainstorming/planning split.

## Success criteria
1. `plugins/minerva/skills/explore/SKILL.md` exists with frontmatter `name: explore` and a non-empty `description`.
2. `explore/SKILL.md` body contains the literal strings `one at a time`, `writes no file`, and (a bare) `minerva:propose`.
3. `evals/explore/contract.json` exists and is well-formed: `skill == "explore"`, only the allowed keys, `frontmatter.values.name == "explore"`, `anchors` include the literals from (2) plus an `any_of` outcomes anchor, and `cross_surface` sets `root_readme` / `plugin_readme` / `using_minerva_body` all `true`.
4. `evals/explore/behavioral.json` exists with `skill == "explore"` and ≥1 case (each with `id`, `prompt`, and a non-empty `rubric`).
5. The `minerva:explore` token appears in all three catalog surfaces: root `README.md`, `plugins/minerva/README.md`, and `using-minerva/SKILL.md`.
6. `minerva:propose`'s `SKILL.md` body contains the convergent/divergent boundary note referencing `minerva:explore` and describing the inline-arg handoff; `evals/propose/contract.json` includes a must-contain anchor on the literal `minerva:explore`.
7. `python -m pytest` passes (`tests/test_skill_contracts.py` and the rest of the suite).

## Open Questions
- None.

## Design constraints (not mechanically checkable — recorded for the implementer)
- `explore` (divergent, pre-draft) and `minerva:grill-plan` (convergent stress-test of an already-*drafted* plan) operate on different phases and do not overlap; no boundary edit to grill-plan is owed.
- No durable exploration-note persistence (YAGNI — deferred to a future unit if demand emerges).
- Atomicity: the `explore` skill dir and its `evals/explore/contract.json` must land together, and the `propose` body edit and its new contract anchor must land together — otherwise the enumerating contract suite reds mid-commit.
