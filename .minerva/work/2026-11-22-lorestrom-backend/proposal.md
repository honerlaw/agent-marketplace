# Proposal: lorestrom-backend

**Date**: 2026-11-22
**Status**: Shipped (2026-11-23)

## Goal

A plugin named **`lorestrom`**, in this marketplace, that runs minerva's lifecycle with every record stored in **Lorestrom** instead of the repository: knowledge entries, reference docs and work-unit records (proposal, scratchpad, replans, followups) are docs in one Lorestrom workspace, reached through the Lorestrom MCP tools, so several repos, people and agents share one body of lore.

- **Nothing record-shaped is committed to the project's repo.** Code still moves through a git worktree, branch and PR per unit.
- **Live, but labelled.** New lore is visible before merge, marked pending on the unit's gate. It becomes current when the merge is observed.
- **Release on merge, observed by the plugin.** Lorestrom never talks to git or GitHub; any clone's cleanup reports the merge, so self-hosted GitHub works.
- **minerva is unchanged and stays files-only.** No file under `plugins/minerva/` changed in any phase.

## Why

The user, exploring this on 2026-11-21: "cross repo and cross user / cross agent usage. I want to be able to at least store context around my changes / my stuff even if folks dont want me to check it in … Imagine a team using it type of deal across branches". On setup: "Ideally, we can wire this up in such a way that people dont need to do anything in their github repo, and only in lorestrom (or even better, set it up entirely through skills / mcp for lorestrom)". The user also chose "live, but labelled", hosted Lorestrom, and storing knowledge and work units.

Lorestrom has the primitives: kinds, namespaced properties, keys, find, gates with held writes, release and abandon.

The unit began as an opt-in backend inside minerva. On 2026-11-23 the user chose a separate Lorestrom-only plugin instead (`replan.md`): most of phase 1's complexity came from holding two backends in one plugin, and a separate plugin breaks neither existing projects nor this repo's CI.

## Approach

What was built, in `plugins/lorestrom/` (0.1.0 → 0.4.0).

### 1. Packaging and local state

- Plugin `lorestrom`, listed in both marketplace files, with both host manifests, a README and COMPATIBILITY. Seventeen skills: `init`, `using-lorestrom`, the twelve lifecycle skills ported from minerva (propose, work, replan, review, promote, ship, cleanup, status, grill-plan, explore, one-by-one, debug), `lint`, and the two orchestrators.
- Local state uses lorestrom's own names, never where minerva looks: worktrees in `.lorestrom/worktrees/`, the link cache in `<git-common-dir>/lorestrom/config.json`, checkpoints under `<git-common-dir>/lorestrom/runtime/`. `--shared` commits `.lorestrom/config.json`.
- Kinds, keys and properties keep the `minerva:` namespace: it names the record format, not the storage, and an import keeps an entry's identity. The GitHub follow-up label and the cross-session markers are kept too, so peers of both plugins interoperate.

### 2. Linking a repository

- **Project node.** A doc of kind `minerva:project`, keyed `minerva:p/<first remote label>`; its doc id scopes every other key. A remote label strips user, token, port and query; an SSH path under a home directory, and a local path, get none. Reusing an existing project always asks.
- **Discovery.** For each connected server, `find_docs` kind `minerva:project` matched on the normalised `origin`; several matches are an ask. A broken link raises; it never reads as unlinked.
- **Unlinked repositories.** Read-side skills carry on without lore and say so in one line; only init and record writes stop, naming `lorestrom:init`.
- `init` puts a short pointer in `CLAUDE.local.md` (excluded locally) and leaves `git status --porcelain` empty by default.

### 3. Helper and storage contract

- `scripts/lorestrom_backend.py` holds the deterministic parts: link resolution and keys, `entry_payload` and `reference_payload`, `merge_properties`, `unit_state`, `release_outcome`, `repair_flips`, `reconcile_action` and `merge_evidence`, `removal_plan`, `lint_docs`. Doc text reaches it through a `mktemp` file on stdin, never a command line or Python source; only 40-hex shas reach git. It re-execs itself in UTF-8 mode and runs on Python 3.9.
- `knowledge_lint.py`, `knowledge_spans.py` and `work_status.py` are byte-identical copies of minerva's, with a drift test; a minerva PR touching one syncs the copy and bumps lorestrom's patch version. `lorestrom_runtime.py` and `plugin_guard.py` are adapted copies.
- `skills/using-lorestrom/references/storage.md` maps every `storage:<op>` a skill names to Lorestrom tools and helper commands (link, discover, list, read, import, handover, unit create/read/list/ship/finish/release/confirm/abandon/repair, record, knowledge and reference writes, lint). A test fails on an operation with no row, a row tool outside the vendored tool list, or a tool a row's section uses but its row omits.

### 4. Writes and pending state

- `upsert_doc` and held upserts are never used. Writes are a keyed create, then `update_doc` with merged properties; key, status and properties are read back with `find_docs`, a gate's state with `get_gate`.
- **Unit.** A `minerva:work_unit` doc carrying an operation token, with its own gate (`archive` on abandon); records are created under the gate. A half-created unit resumes when the token matches.
- **Knowledge.** A new entry is `draft` plus a held `set_status current` on the unit's gate; edges between new entries are live, edges onto existing entries held. After a release, `repair_flips` repairs a failed flip only on an entry still `draft`.
- **Reference docs** (`minerva:reference`, keyed by path) change in place: inside a unit, a held `write_body` replace built from a read in the same step; debug's confirmed live update outside any unit checks open gates first. A held replace on a doc changed after the hold fails STALE, so a live edit is never silently overwritten.
- **Promote** replaces the proposal body, archives the scratchpad record and sets `minerva:status` and `minerva:promoted` (`unit.finish`) as its last step. On a phased unit, Mode A waits for the final phase; earlier phases use Mode B.

### 5. Release on observed merge

Records are not committed, so a fresh unit branch equals the default branch. ship records each phase's branch, PR and pushed head (again after every later push). `reconcile` answers from that record plus live git evidence:

- `release`: every phase has a MERGED PR or a recorded head that is an ancestor of the default branch (a fast-forward merge included).
- `confirm`: no PR evidence, but merging the head changes nothing (a squash merge `gh` cannot see). The user's yes travels in the request (`userConfirmed`), counts only for phases it lists in `phasesToConfirm`, and carries through to the release. `--yes` never confirms. `--merged <sha>` names the commit instead.
- `abandon`: a CLOSED PR whose head is not merged, or `--abandon`. A head this clone lacks is fetched first.
- otherwise `wait`; a unit with no recorded head after 14 days is flagged stale, never acted on.

A CONFLICT on release that `get_gate` shows as released is success.

### 6. Handover from minerva files

From 0.2.0 Lorestrom is authoritative for a linked repo. `init` runs one confirmed sync (new entries, confirmed replaces of changed ones, reference docs, and anything edited in Lorestrom since its import shown, never overwritten), then separate offers, each kept unless the user says yes: replace the AGENTS.md minerva section, and one commit removing the imported files (a file whose digest no longer matches is skipped and named). It says how to disable minerva in that repository and never edits host settings.

### 7. Orchestrators, sweep, status and lint

- **`propose-ship` and `propose-ship-auto`** keep their records and decision logs in Lorestrom and invoke only `lorestrom:` skills. A phased unit loops back through work, review, promote and ship for each later phase, checked against that phase's own criteria. At merge they run `lorestrom:cleanup <unit> --yes`, which acts only on the run's own unit; an unproven merge or a unit not the run's own is a user question (counted in the autonomous run), and neither orchestrator abandons a gate.
- **Cleanup's sweep** (no argument) covers this project's open units in Lorestrom, including other clones'. It fetches a missing head by its recorded PR number, releases only on `reconcile`'s answer, needs a yes naming the unit to act on one someone else opened or to abandon, and removes only this clone's worktrees.
- **Status** lists units with phase progress, gate state and age (stale, worked on elsewhere, opened by someone else), read-only.
- **Lint** runs `lint-docs` over the project's knowledge docs (ids and keys, Theme and Summary, broken or drifted edges, supersession, pending entries on closed gates, orphans) plus minerva's judged advisories, read-only. A finding names a doc only by its checked stem or id.

### Rejected

- **A backend inside minerva** (the original plan): two backends in one plugin carried most of phase 1's complexity.
- **A fork repository, or renaming minerva:** the user chose a new plugin in this marketplace.
- **Mirror** (files canonical, synced after merge): records must be committed, and there is no pre-merge view.
- **A direct client:** needs a Lorestrom change (no API tokens; pre-registered OAuth clients only).

## Success criteria

As the replan of 2026-11-23 states them, met in every phase:

1. minerva unchanged: no diff under `plugins/minerva/`; its tests and dry-run evals pass with no assertion weakened.
2. Helper tests, including names-as-data, the Python 3.9 import check, and a subprocess locale test that keeps "Café" under a non-UTF-8 locale.
3. The inventory, drift and parametrized guards exist, and a deletion pass shows each fails.
4. Default init leaves `git status --porcelain` empty.
5. Each phase bumps lorestrom's version everywhere it is pinned.
6. Every SKILL.md in both plugins at or under 9216 bytes.

## Phases

As replanned on 2026-11-23 (a separate Lorestrom-only plugin) and 2026-11-24 (the lifecycle split); `replan.md` holds the plans these replace.

1. **Connect and publish (lorestrom 0.1.0)** — plugin skeleton, helper, `using-lorestrom` with the storage contract, `init` with a confirmed knowledge import; the repo's minerva files stay authoritative. PR #152.
2. **Lifecycle and handover (lorestrom 0.2.0)** — every skill that writes records, checkpoints, the contract's write rows, and init's handover; Lorestrom becomes authoritative. PR #153.
3. **Orchestrators (lorestrom 0.3.0)** — propose-ship and propose-ship-auto; the `--auto` hooks become live. PR #154.
4. **Sweep and lint (lorestrom 0.4.0)** — cleanup's sweep of other clones' units, status ages, and lint over Lorestrom docs.

## Known limits

- No live Lorestrom server was reachable from the authoring session: verification used vendored tool shapes, contract tests and temporary git repositories. lorestrom has no behaviour evals yet.
- Pending knowledge can lag a merge until some clone runs cleanup.
- Status judges staleness from recorded heads; cleanup's `reconcile` also treats a head whose tree equals the base's as headless, which status cannot see.

## Deferred work

- #155 — minerva phased units: the orchestrators' phase loop never runs work for phases 2..N (priority: high). Found while porting the orchestrators; fixed in lorestrom's copies.
