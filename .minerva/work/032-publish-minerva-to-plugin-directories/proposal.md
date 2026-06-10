# Proposal: publish-minerva-to-plugin-directories

**Date**: 2026-06-10
**Status**: Draft

## Goal
Make minerva discoverable on the low-gatekeeping Claude Code plugin discovery
channels — tier-2 auto-indexing aggregators and tier-3 curated "awesome" lists —
so developers who aren't handed the repo URL can find it. **Excludes** the
official `anthropics/claude-plugins-official` directory and any README/narrative
rebuild.

**Targeted channel inventory (fixed for this unit):**
- Tier-2 aggregators: `claude-plugins.dev` (Kamalnrf/claude-plugins, GitHub-crawling), `claudemarketplaces.com`, `claudepluginhub.com`, `aitmpl.com`.
- Tier-3 awesome-lists: `GiladShoham/awesome-claude-plugins`, `ananddtyagi/cc-marketplace`.

Phase 2 may *confirm* or *drop* members of this set on eligibility, but the set
above is what "every channel" in the success criteria ranges over.

## Why
The repo (`github.com/honerlaw/agent-marketplace`) is already a valid, **public**
Claude Code marketplace — `.claude-plugin/marketplace.json` lists minerva — so it
is mechanically addable as a marketplace, **though the repo README currently
documents only the `git clone` + `./install.sh` install path**. The gap is reach,
not mechanics: minerva is findable only by people who already have the URL.

The cheapest, lowest-rejection-risk discovery channels (GitHub-crawling
aggregators + curated lists) generally require (a) an OSS license, which the repo
**lacks** (verified: `licenseInfo: null`), and (b) discovery-friendly GitHub
topics, currently **unset** (verified: `repositoryTopics: null`). Closing those
two gaps plus submitting to the channels converts "installable if you know about
it" into "findable."

## Approach
**Approach A — precondition-gated, verify-then-submit.**

- **Phase 1 — Preconditions (committable, this repo).** Add `LICENSE` (MIT,
  "Derek Honerlaw", 2026). Set GitHub repo topics via `gh repo edit --add-topic`
  (`claude-code`, `claude-code-plugin`, `claude-plugin`, `claude-code-marketplace`,
  `agent-skills`, `ai-agents`), then read them back via
  `gh repo view --json repositoryTopics` to confirm GitHub accepted them (GitHub
  silently drops invalid topics).

- **Phase 2 — Per-channel discovery (verify-then-prepare).** For **each** targeted
  channel, read its README/CONTRIBUTING and record: (i) current indexing state
  (already lists minerva or not); (ii) inclusion criteria + unit-of-submission
  (does it scope *plugins* or whole *marketplaces*? minerva is a plugin inside a
  marketplace repo); (iii) submission mechanism (auto-crawl / GitHub PR / web
  form). This resolves existence, eligibility, and mechanics before any outward
  action.

- **Phase 3 — Produce a channel-conformant submission artifact for every eligible
  channel, then submit per mechanism:**
  - *auto-crawl* (`claude-plugins.dev`): confirm pickup; nudge only if a submit
    path exists.
  - *GitHub PR* (`awesome-claude-plugins`, `cc-marketplace`): produce the **exact
    diff** — target file, entry line in the list's mandated format
    (e.g. `- [name](url) — description.`), correct alphabetical/category
    placement, and PR title/body per the list's CONTRIBUTING — then open via fork
    + `gh pr create` **upon user confirmation** (outward-facing). A user decline
    is recorded as a decision; the conformant artifact must still have been
    produced.
  - *web form* (`claudemarketplaces.com`, `claudepluginhub.com`, `aitmpl.com` if
    it accepts submissions): produce a complete, **submission-ready checklist
    entry** (exact URL + every required field value incl. blurb); the user submits
    or records a decision.

- **Lean footprint.** The only committed diff to this repo is the `LICENSE` file.
  Repo topics are applied out-of-band via the `gh` API (not part of the PR diff).
  Per-channel state lives in `scratchpad.md` during the run; on `minerva:promote`,
  a single knowledge entry records the per-channel outcome so the discovery record
  survives scratchpad archival.

**Rejected alternatives:**
- **B — "fire everything," skip verification.** Risks duplicate submissions and
  PRs to lists that already contain minerva (maintainers reject dupes); violates
  the verify-first discipline.
- **C — only the top-2 channels, drop the awesome-lists.** Contradicts the chosen
  tier-2 **and** tier-3 scope.

## Success criteria
1. `LICENSE` file exists at repo root with MIT license text, correct copyright
   holder + year; committed.
2. GitHub repo topics include at least `claude-code`, `claude-code-plugin`,
   `claude-code-marketplace`, confirmed by a `gh repo view --json repositoryTopics`
   readback (proves GitHub accepted them, not merely that the command ran).
3. For **every** targeted channel (the fixed inventory in **Goal**): its indexing
   state + inclusion criteria + unit-of-submission + submission mechanism are
   recorded.
4. For each tier-3 awesome-list that does **not** already list minerva and whose
   criteria minerva meets: a channel-conformant PR artifact (exact file, mandated
   entry line, placement, PR title/body) is **produced**; the PR is opened upon
   user confirmation (decline = recorded user decision, but the artifact must
   exist).
5. For each web-form aggregator not already listing minerva and accepting
   submissions: a complete, submission-ready checklist entry (URL + all required
   fields + blurb) is **produced**; the user submits or records a decision.
6. The `LICENSE` file is shipped via PR to this repo (topics are applied
   out-of-band via `gh repo edit`, verified by criterion 2's readback rather than
   the PR diff).
7. On `minerva:promote`, a single knowledge entry records the per-channel outcome
   (submitted / already-listed / ineligible / user-declined).

**Binding note:** a channel is "addressed" when a channel-conformant submission
artifact has been **produced** (and submitted wherever submission needs no third
party). Public listing appearance is async / outside our control and is **not** a
criterion. User-decline gates only the outward **send** — it never zeroes the
artifact-production bar, so declining cannot hollow out the unit's discovery work.

## Open Questions
- Exact topic set beyond the core three (cosmetic; default list proposed).
- Whether `aitmpl.com` accepts submissions or is purely curated (resolved at
  Phase-2 verify-time).
