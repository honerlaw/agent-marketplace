# Proposal: lorestrom-backend

**Date**: 2026-11-22
**Status**: Draft

## Goal

An opt-in **Lorestrom backend** for minerva. A project linked to Lorestrom keeps its knowledge entries and work-unit records (proposal, scratchpad, replan, followups) as docs in one Lorestrom workspace, reached through the Lorestrom MCP tools, so several repos, people and agents share one body of lore.

- **Nothing has to be committed to the project's repo.** The link lives in Lorestrom, and a clone with the Lorestrom MCP server connected discovers it. A team may opt in to a committed marker.
- **Live, but labelled.** New lore is visible before merge, marked pending. Changes to existing lore wait for the merge.
- **Release on merge, observed by minerva.** Lorestrom never talks to git or GitHub. The author's clone (push) or any teammate's (pull) reports the merge, so self-hosted GitHub works.
- **The `files` backend is the default and does not change.** An unlinked project, this repo included, behaves as 4.0.0. Worktrees, branches, PRs and runtime checkpoints stay local and in git under both backends.

## Why

The user, exploring this on 2026-11-21: "cross repo and cross user / cross agent usage. I want to be able to at least store context around my changes / my stuff even if folks dont want me to check it in … Imagine a team using it type of deal across branches". On setup: "Ideally, we can wire this up in such a way that people dont need to do anything in their github repo, and only in lorestrom (or even better, set it up entirely through skills / mcp for lorestrom)". The user also chose "live, but labelled", hosted Lorestrom, and storing knowledge and work units.

Lorestrom now has the primitives: kinds, namespaced properties, keys, find, gates with held writes, release and abandon.

## Approach

A backend adapter, resolved once per skill like the host adapter, with mechanical guards so a skill that misses it fails loudly instead of writing files.

### 1. The project node and discovery

The user chose discovery on 2026-11-22.

- **Project node.** A doc of kind `minerva:project` in the linked workspace, keyed `minerva:p/<first remote label>`. Its doc id is the **project id**: stable across renames, and the scope of every other key. Its `minerva:remotes` property lists the repo's remote labels (aliases). A repo with no remote is linked by asking at init.
- **Resolution order:**
  1. The clone's link cache, `<git-common-dir>/minerva/config.json` (never committed). It may also record an explicit `files` opt-out (`minerva:init --backend files`).
  2. A committed `.minerva/config.json`, present only after `minerva:init --backend lorestrom --shared`.
  3. Discovery: for each connected Lorestrom server, `find_docs` kind `minerva:project`, matched on the normalised `origin`. One match is the link, and a skill allowed to write caches it. Several matches are an ask.
  4. Otherwise `files`.
- **Fail closed once known.** A linked or marked clone whose server is missing or failing stops with an error. So does a malformed config, and so does a failed lookup on a connected server. None of these falls back to `files`.
- **Renames, transfers, forks.** A linked clone whose `origin` is not an alias offers to add it. An unlinked clone whose repo name matches a project under another owner or host asks whether it is that project. A fork is a separate project unless the user links it.
- **Agents outside skills.** Init, and the first discovery by a writing skill, put a short pointer in `CLAUDE.local.md` and list it in `info/exclude`. A tracked `CLAUDE.local.md` is left alone. `.minerva/worktrees/` is excluded the same way, and the lorestrom branch of propose's pre-flight accepts it through `git check-ignore`. `--shared` writes the committed marker and an AGENTS.md routing section instead.
- **Accepted gap.** Without a marker, a clone with no Lorestrom MCP connection uses files, and Codex finds the lore only through skills. Init says both.

### 2. One pure module, for small deterministic inputs

`plugins/minerva/scripts/minerva_backend.py` (root symlink, in `REQUIRED_MODULES`):

- `load_config` and CLI `resolve` (`files | lorestrom | discover`), `repo_label`, `match_project`.
- Keys: `minerva:k/<project id>/<stem>` (entry), `minerva:u/<project id>/<unit>` (unit), `<unit key>/<record>` (record), checked against Lorestrom's `NodeKey` rule.
- `entry_payload(stem, text, project, context)`: today's entry markdown to key, title, kind `minerva:knowledge`, namespaced properties (id, type, theme, summary, date, context, project), body and related edges. It imports the `knowledge_lint` and `knowledge_spans` grammar. It refuses what lint refuses and what Lorestrom would: a property value over 1000 characters, over 64 keys or 16 KiB of properties, a body over 100,000 characters. The agent writes the entry to a `mktemp` file and passes the small payload on.
- `merge_properties(existing, changes)`: `update_doc` replaces the whole map, so every property write reads first and merges.
- `stray_records` and CLI `check-tree`: under lorestrom, record paths added or modified on the branch give a non-zero exit.
- `unit_state`, `reconcile_action`, `repair_flips`.

There is no catalog renderer: `find_docs` results stay in the model's context. The contract gives the line format (`theme | id | summary`, plus the project when it is another one, `(superseded)` and `(pending: <unit>)`) and the paging rule.

### 3. One storage contract, with a tested inventory

`runtime.md`, which every skill reads, gains "Storage backend". Under `files` the skill text applies as it is. Under `lorestrom` the skill reads `skills/using-minerva/references/lorestrom.md`, whose table maps each record operation to Lorestrom tools. A preamble does not bind a write step, so:

- `BACKEND_SITES` classes every skill file naming a `.minerva/work` or `.minerva/knowledge` path as `branched` (names its operation at that step), `read`, or `not-applicable` (lint, migrate, migrate-fix). A test finds the sites by scanning. It fails on an unregistered site, a branched file naming no operation, an operation absent from the table, or a table tool absent from the vendored tool list.
- propose, promote and ship run `check-tree` before committing.

### 4. Writes

`upsert_doc` and held upserts are never used: on an existing key they overwrite, or queue an overwrite.

- **Keyed create, then update.** Create carries key, kind, title and markdown, and the key is the atomic backstop. `update_doc` then sets properties. Key, status and properties are read back with `find_docs` (`get_doc` over MCP returns none of them). Whether a doc is a gate, and its state, comes from `get_gate`.
- **Unit.** Before creating, save an operation token in the unit's runtime directory and put it in the unit doc's markdown. Then `create_doc` kind `minerva:work_unit`; properties (`minerva:state`, `project`, `branch`, `base`); `open_gate` with `archive`. **A half-created unit resumes:** on a taken key, a matching token means finish the missing steps; any other holder is a duplicate slug, shown to the user.
- **Records.** `hold_write` op `create` under the gate (live), linked `minerva:part_of`, then written live with `write_doc_body`.
- **Entry.** `hold_write` op `create` (live, `draft`), `update_doc` properties, then a held `set_status current`. A retry recognises its own doc by key among `find_docs({gateId})` and finishes the missing steps; otherwise the slug is taken.
- **Edges.** Between entries new in this unit, live. Touching an existing entry, held. `supersedes` is the core relation; any other label is `relates_to` with `minerva:label`. `[[stem]]` resolves in this project, then uniquely in the workspace; an ambiguous one is reported.
- **Promote.**
  - New entries and edges as above.
  - The proposal body is replaced.
  - The scratchpad doc's status becomes `archived`.
  - The unit gets `minerva:status` (`Shipped (YYYY-MM-DD)`) and `minerva:promoted` (the date), which is what `unit_state` reads.
  - Followups go to the followups record wherever files mode would write `followups.md`.
- **Import.** Outside any gate: keyed create, `current`, edges last. It resumes incomplete entries and never rewrites complete ones, so a re-run un-supersedes nothing. An entry whose file differs from its doc is reported as changed, not overwritten. Import sends project content to an external service, so it first shows destination, count and paths and waits for explicit confirmation. No orchestrator flag satisfies that.

### 5. Pending and unit state

- Pending is status `draft` plus `minerva:context` (the unit key). Release applies the held `set_status current`; abandon archives.
- After a release, `repair_flips` lists failed flips whose entry is **still `draft`**, never one superseded or changed meanwhile. Cleanup sets those current and reports each repair and each it cannot make.
- Lorestrom refuses held writes to a gate's own doc, so `minerva:state` is a live property, confirmed with `get_gate` before any action (one call per unit acted on) and refreshed when stale.

### 6. Merge evidence

Records are not committed, so a fresh unit's branch equals the default branch and `git branch --merged` reads it as merged. Therefore:

- ship records branch, PR and head commit per phase (`minerva:branch_<n>`, `pr_<n>`, `head_<n>`, all namespaced). No recorded head, or a head equal to the base, is always `wait`: nothing is released and that worktree is not removed.
- `release`: every declared phase has a recorded head and either a MERGED PR or a head that is an ancestor of the fetched default branch. The unit gets `minerva:merge_commit`, then the gate is released.
- `confirm`: no PR evidence, but merging the head changes nothing. The tree from `git merge-tree --write-tree <default> <head>` equals the default branch's tree, and the head's tree differs from the base's. The user confirms, or names the commit with `minerva:cleanup <unit> --merged <sha>` (checked to be on the default branch). `--yes` never confirms it. A conflict, or git older than 2.38, is `wait`.
- `abandon`: a PR observed CLOSED unmerged, or an explicit `minerva:cleanup <unit> --abandon`.
- Anything else is `wait`. status lists open units with age and action, and flags one with no recorded head after 14 days as stale. Staleness never abandons. Pending can lag a merge until a cleanup runs, and the docs say so.
- Releasing needs `edit` on the unit. Failed held writes are reported. A CONFLICT that `get_gate` confirms as released is success.
- `2026-10-01-decision-knowledge-aggregates-are-derived-on-read` still holds for `files`. Cleanup's text scopes its no-post-merge rule to that backend, and promote records the narrowing as a new entry linking the old one.

### 7. Host-neutral naming and pinned facts

Skills name Lorestrom tools and the host adapters map them. Vendored tool names, `NodeKey`, statuses, limits, and the `Gate`, `HeldWrite` and find-result shapes are pinned to the Lorestrom version they were checked against, named in the test module.

### Rejected

- **Mirror** (files canonical, synced after merge): records must be committed, and there is no pre-merge view.
- **Lorestrom only:** breaks every existing project and this repo's CI.
- **A direct client:** needs a Lorestrom change (no API tokens; pre-registered OAuth clients only).
- **An always-committed marker, or local-only setup:** the user chose discovery over both.

## Success criteria

1. An unlinked project behaves as 4.0.0: `pytest tests/ -q` and the dry-run evals pass with no existing assertion weakened or deleted, and the only added step is the discovery read when a Lorestrom server is connected.
2. `tests/test_minerva_backend.py` covers, as each phase lands:
   - resolution: every step, opt-out, malformed config, failing server;
   - `match_project`: alias, several matches, renamed repo, no remote;
   - keys and repo labels;
   - `entry_payload` over every entry in this repo, with edges matching `knowledge_catalog`'s, and each size refusal;
   - `merge_properties` and `check-tree`;
   - `unit_state` from promote's properties, and half-created unit resume;
   - `repair_flips`, including an entry no longer draft;
   - a table-driven `reconcile_action`: fresh branch, squash without `gh`, conflict, closed PR, stale, phased units.
3. The inventory test exists, and a deletion pass shows it fails for each of the four cases in Approach 3.
4. A test in a temporary git repo shows that default lorestrom setup and first discovery leave `git status --porcelain` empty.
5. Each phase bumps the version (both plugin.json files, pinned tests, COMPATIBILITY, README, pages/index.md) and keeps the catalog surfaces in sync.
6. Every SKILL.md stays at or under 9216 bytes.

## Phases

1. **Setup and read path (4.1.0)** — project node, discovery and its cache and pointer; the module's setup and read parts and `check-tree`; the runtime section; the contract's read and import operations; the inventory; init (local, `--shared`, `--backend files`, confirmed import); knowledge reads in explore, propose, grill-plan, review, debug and status; lint and the migrate skills say not applicable. Until 4.2.0 every other record write stops with one sentence in runtime.md ("the Lorestrom backend is read-only until minerva 4.2.0; run minerva:init --backend files to keep using files in this clone"), and init says so before linking. Criteria: 1–6 as far as they apply, and a test anchoring the refusal and the write sites' route to it.
2. **Work units, promotion and release (4.2.0)** — Approach 4–6 for a unit's own lifecycle: propose and both orchestrators, work, replan, review, decision logs, promote, ship, and cleanup's release, confirm, abandon and repair; the refusal is removed. Criteria: 1–6, including double release; the six Target-resolution blocks name the lorestrom lookup and stay in sync; cleanup's scoping is in place.
3. **Pull reconciliation (4.3.0)** — cleanup's sweep finds this project's open units with `find_docs` and applies `reconcile_action` from the sweeper's own evidence; status lists them with age and action. It is separate because it acts on other people's units from another clone. Criteria: the table-driven test carries the safety rules; the prose test checks only that the sweep calls `reconcile_action`.

## Open Questions

- No live end-to-end check is possible in the authoring session, which has no Lorestrom MCP connection. Verification uses vendored shapes, contract tests and temporary git repos; the user can run init against www.lorestrom.com once phase 1 merges.
