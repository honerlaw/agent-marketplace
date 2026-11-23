# Replan: lorestrom-backend

## 2026-11-23 — A separate Lorestrom-only plugin

### Original plan

An opt-in Lorestrom backend inside minerva: `files` stays the default; a clone links to a
Lorestrom project by a per-clone cache, a committed marker or discovery; every skill resolves
its backend and follows a `storage:` note at each record step. Three phases: 4.1.0 setup and
read (every other record write refused), 4.2.0 work units, promotion and release, 4.3.0 pull
reconciliation. Phase 1 was built and reviewed ("ready") on an unpushed branch.

### What changed

The user chose (2026-11-23), over keeping the plan, a fork repo or a separate repo: a **new
plugin named `lorestrom`, in this marketplace, backed by Lorestrom only, with no local file
mode**. minerva stays files-only and unchanged.

- Most of phase 1's complexity, and many of its four review passes' findings, came from two
  backends in one plugin: resolution order, opt-out, never falling back, the read-only
  refusal, `check-tree` and stray records, the committed-marker rules, and a `storage:` note
  in 30+ skill files.
- The proposal rejected "Lorestrom only" because it "breaks every existing project and this
  repo's CI". A separate plugin breaks neither: minerva is untouched.

### New plan

**1. Packaging.** `plugins/lorestrom/`, plugin `lorestrom`, versions from 0.1.0, listed in
`.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`, with both host
manifests, a README and COMPATIBILITY. No file under `plugins/minerva/` changes in any phase.

**2. Lorestrom only, with its own local state.** From 0.2.0, knowledge entries, reference docs
and work-unit records are Lorestrom docs and the repo gets no record file. Code work uses a git
worktree, branch and PR per unit, under lorestrom's own names: worktrees in
`.lorestrom/worktrees/`, checkpoints in `<git-common-dir>/lorestrom/runtime/`, the link cache in
`<git-common-dir>/lorestrom/config.json`. Nothing lorestrom creates lives where minerva's
cleanup, status or runtime looks (a lorestrom unit's branch equals the default branch until it
has commits, so minerva's cleanup would remove it from `.minerva/worktrees/`). There is no
files fallback, opt-out or read-only state.

**3. Unlinked repositories.** A link is a per-clone cache, invisible to skill descriptions, so:
- read-side skills in a repo with no reachable server or no project carry on without lore and
  say so in one line; only init and record writes stop, naming `lorestrom:init`;
- descriptions and `using-lorestrom` key on what is visible: the `CLAUDE.local.md` pointer, a
  committed `.lorestrom/config.json`, or `.lorestrom/`.

**4. Data model.** Unchanged from the original Approach 1, 2 and 4–6, keeping the `minerva:`
namespace for kinds, keys and properties: it names the record format, not the storage, and an
import keeps an entry's identity. Added: kind `minerva:reference` for `.minerva/reference/`
docs, key `minerva:r/<project id>/<path under reference/, without .md>` (subdirectories kept
with `/`), title from the first H1 or the file name, properties `minerva:path` and
`minerva:digest`, no edges. A `reference_payload` builds it, with its own tests (phase 2).
Reference docs are present tense and change in place, so a copy would go stale: they are not
imported until 0.2.0, and from then on are updated only under a unit's gate (a held
`write_body` replace), never superseded.

**5. Living beside minerva.**
- 0.1.0 is a publishing bridge: **the repo's minerva files stay authoritative**. Lorestrom holds
  an imported copy of the knowledge entries, readable by other repos, people and agents;
  re-running `lorestrom:init` imports new entries and reports changed ones, never overwriting.
  The pointer and init's report say the copy is a snapshot that can lag this repo's files until
  0.2.0. No removal is offered. minerva keeps the lifecycle, and in-flight minerva units finish
  on minerva.
- From 0.2.0 Lorestrom is authoritative for a linked repo. Before handing authority over, init
  runs one confirmed sync: it imports new entries, offers a confirmed replace for each changed
  entry, and creates or replaces `.minerva/reference/` docs. For any doc a person or agent
  changed in Lorestrom since its import (`list_doc_changes`), it shows the change and never
  overwrites it silently. Then it offers, each separately confirmed and kept by default:
  replacing the AGENTS.md minerva routing section with the lorestrom one, and one commit removing
  the imported `.minerva/knowledge/` and `.minerva/reference/` files. That commit skips, and
  names, any file whose digest still differs from its doc's `minerva:digest`. Init tells the user
  how to disable the minerva plugin for that repository in their host; it never edits host
  settings. Historical `.minerva/work/` units stay in git and are not imported in this unit.
- Skill descriptions say lorestrom skills are for a repository linked to Lorestrom, and
  `using-lorestrom` says that there only `lorestrom:` skills write records.

**6. Code.** `plugins/lorestrom/scripts/lorestrom_backend.py` is the branch's
`minerva_backend.py` without the files backend (resolution to `files`, opt-out, `check-tree`,
stray records). Import parses entries with **byte-identical** copies of minerva's
`knowledge_lint.py` and `knowledge_spans.py`. The helper handles encoding itself, so the
branch's `parse_entry(encoding=)` change is dropped. Skills run it as `python3 -X utf8`. It
re-execs itself in UTF-8 mode when `sys.flags.utf8_mode` is 0, and that works on Python 3.9
(no `sys.orig_argv`) without looping. `entry_payload` raises when not in UTF-8 mode, so an
in-process caller fails loudly instead of guessing. An entry that is not valid UTF-8 is refused
and reported; CRLF handling stays as built. A drift test fails when a
copy differs; the rule, written in both READMEs' maintainer notes and the test's message: a
minerva PR touching either file syncs the copy and bumps lorestrom's patch version.
`lorestrom_runtime.py` and `plugin_guard.py` are adapted copies of minerva's (host adapter,
checkpoints under lorestrom's names, names-are-data rules).

**7. Tests.**
- The helper tests carry over minus the files-backend cases, run against lorestrom's scripts
  through subprocesses from its own directory or `importlib` under unique module names, so the
  root `scripts/` symlinks to minerva never shadow them. Python 3.9 import is checked.
- The scanning and contract checks of the repo's skill guards are parametrized over both
  plugins' skill trees; their minerva-pinned assertions (skill count, version, `RUNTIME`) stay
  exactly as they are, and lorestrom's equivalents are new assertions. The guards: names are data
  (`test_untrusted_names.py`), mutating-`gh` snippets (`test_skill_snippets.py`), the runtime
  pointer (`test_host_adapters.py`), plugin-guard sites (`test_plugin_guard_sites.py`), the
  SKILL.md budget (`test_skill_budget.py`), and the install fixture (`test_install_plugin.py`).
  These shared guards are how copied lifecycle prose keeps up with later minerva fixes.
- New: manifest and marketplace versions in sync; a path inventory that no lorestrom skill
  names `.minerva/work`, `.minerva/worktrees` or minerva's runtime path, and names
  `.minerva/knowledge` or `.minerva/reference` only as init's import source; every `storage:`
  operation is a contract row whose tools are in the vendored tool list; `reference_payload`
  (phase 2).
- minerva's skill and compatibility evals stay minerva-only. lorestrom has no behaviour evals
  until a Lorestrom test server is reachable: a stated gap.

**8. Publishing.** The branch is rebuilt from `main` as fresh commits with no private Lorestrom
reference (commit hashes, PR and ADR numbers, source paths); the proposal and scratchpad are
scrubbed the same way. The old local branch is kept, renamed, until phase 1 merges.

**Phases** (one PR each; the user merges):

1. **Connect and publish (0.1.0)** — skeleton; helper; `using-lorestrom` with the storage
   contract (link, discover, list, read, import); `init` (connection check, link or create the
   project, `--shared`, confirmed import of knowledge entries, re-run to import new ones); the
   guards parametrized. No lifecycle or read-side skills yet: minerva keeps them.
2. **Lifecycle (0.2.0)** — propose, work, replan, review, promote, ship, cleanup (release,
   confirm, abandon, repair), status, explore, grill-plan, one-by-one, debug, propose-ship and
   propose-ship-auto, per the original Approach 4–6; `reference_payload`; init's handover sync,
   then its section-replacement and removal offers; Lorestrom becomes authoritative.
3. **Sweep and lint (0.3.0)** — cleanup's sweep of other clones' units, status ages, and lint
   over Lorestrom docs.

**Success criteria** replace the original's:
1. minerva unchanged: no diff under `plugins/minerva/`; its tests and dry-run evals pass with no
   assertion weakened.
2. The helper tests above, including names-as-data (no doc content or ref name reaches a
   command line or Python source), the Python 3.9 import check, and the locale test rewritten as
   a subprocess run with `PYTHONUTF8=0` and a non-UTF-8 locale that keeps "Café".
3. The inventory, drift and parametrized guards exist, and a deletion pass shows each fails.
   A deletion pass measures only the mutations its author chose; the shared guards are the
   backstop.
4. Default init leaves `git status --porcelain` empty.
5. Each phase bumps lorestrom's version everywhere it is pinned.
6. Every SKILL.md in both plugins at or under 9216 bytes.

## 2026-11-24 — Split the lifecycle phase

### Original plan

The replan of 2026-11-23 has three phases: 0.1.0 connect and publish (merged), 0.2.0 the whole
lifecycle (14 skills ported from minerva, the write rows of the storage contract, checkpoints,
`reference_payload`, init's handover sync and offers, and Lorestrom becoming authoritative),
0.3.0 the sweep and lint.

### What changed

Building 0.2.0 showed it is too large for one reviewable PR. The 14 skills are 35 files and
about 4,000 lines of minerva text (propose 850, promote 648, propose-ship-auto 595, ship 417,
cleanup 249, status 246, review 217, debug 200, work 147, propose-ship 128, one-by-one 99,
replan 98, explore 58, grill-plan 47), much of it shell snippets under the names-are-data rules.
Phase 1's PR was about 4,250 lines and needed review fixes; 0.2.0 whole would pass 7,000.
The pure functions every split needs are already built and tested on the phase 2 branch
(`unit_state`, `release_outcome`, `repair_flips`, `reconcile_action`, `merge_evidence`,
`reference_payload`, their CLI commands; 104 tests).

### New plan

Four phases. The rule that orders them: **authority over a linked repo's records moves in the
same release as every skill that writes them, or hands off to one that does**, so no release
writes records to Lorestrom while the repo's files are authoritative, and none leaves minerva's
auto-triggered skills writing files Lorestrom ignores.

1. **Connect and publish (0.1.0)** — merged, unchanged.
2. **Lifecycle and handover (0.2.0)** — checkpoints under `<git-common-dir>/lorestrom/runtime/`;
   the storage contract's write rows (unit, records, knowledge, reference, release, confirm,
   abandon, repair); propose, work, replan, review, promote, ship, cleanup (release, confirm,
   abandon, repair), status, grill-plan, explore, one-by-one and debug, on the foundation
   already built; init's handover sync, then its separately confirmed, default-keep offers
   (replace the AGENTS.md section, remove the imported files) and its instruction for disabling
   minerva in that repository, which says the orchestrators arrive in 0.3.0 and that until then
   the lifecycle runs skill by skill; Lorestrom becomes authoritative.
   - Why these skills together: propose and replan load grill-plan before they write; explore
     hands off to propose; debug writes reference docs and hands findings to promote; review and
     status read unit records that from 0.2.0 exist only in Lorestrom.
   - Reference docs: inside a unit, a reference update is a held `write_body` replace on the
     unit's gate, as the 2026-11-23 replan says, built from the doc's body read in the same step
     as its `hold_write`; the contract states that the remaining window between that read and the
     hold is not detected. debug updates one outside any unit, as minerva's debug overwrites the
     file: a live `write_doc_body` replace after the user confirms the new text, which Lorestrom
     snapshots and attributes, and which also updates the doc's `minerva:digest` (read,
     `merge-properties`, `update_doc`). Before writing, debug reads this project's open units'
     gates with `get_gate`; if one holds a write on that doc, debug shows the unit and asks
     whether to hold the update on that gate instead or write live knowing the unit's replace
     will fail STALE at release, and never proceeds without that answer. Lorestrom's release
     fails a held replace STALE when the body changed after it was held, so a live edit is never
     silently overwritten; cleanup reports a STALE reference replace with its unit and doc, and
     it is re-applied only deliberately. The contract has a row for each path.
   - **Amendment:** debug's confirmed live update outside any unit amends both the proposal's
     "changes to existing lore wait for the merge" and the 2026-11-23 replan's "updated only
     under a unit's gate", for that case only, matching minerva's debug, which edits reference
     files outside any unit.
   - The core skills' `--auto` hooks (ship, work, replan, review, promote) are ported as they
     are and documented as inert until 0.3.0.
   - Size: about 3,270 lines of source skills plus the handover, contract rows, checkpoints and
     tests; roughly 5,000–6,000 lines. No split by skills keeps the authority rule (units need
     promote, ship and cleanup; knowledge needs promote), so the PR is made reviewable by its
     commits: first a commit that copies minerva's files verbatim (checked mechanically), then
     the adaptation commits, which are what review reads.
   - Until 0.3.0, minerva's orchestrators must not run in a linked repository: `using-lorestrom`
     and init's handover say so, and the orchestrators run only when invoked.
3. **Orchestrators (0.3.0)** — propose-ship and propose-ship-auto; the `--auto` hooks become live.
4. **Sweep and lint (0.4.0)** — the old phase 3, unchanged.

**Why four, past the soft ceiling of about three:** the authority rule puts every writer into
0.2.0, which is already the largest PR this unit can review, so the orchestrators cannot join it;
and the sweep stays separate, as the original proposal argued, because it acts on other people's
units from another clone. Merging 0.3.0 into 0.4.0 would only lengthen the window in which
minerva's orchestrators must not run.

**Criteria,** as the replan of 2026-11-23 states them, applied per phase, and explicitly:
- the parametrized guards and the path inventory cover each ported skill in the phase it lands;
- in 0.2.0, criterion 4 (default init leaves `git status --porcelain` empty) holds because every
  handover offer defaults to keep;
- the verbatim-copy commit is checked against minerva's files at that commit.

The phase 2 branch keeps its foundation commit and continues as phase 2.

### Rejected

- **The builder's split** (0.2.0 core lifecycle without review, status or handover; 0.3.0 the
  rest with the handover): 0.2.0's promote would write knowledge to Lorestrom while the repo's
  files were still authoritative, and review and status could not read units that exist only in
  Lorestrom.
- **Holding explore, debug and grill-plan for 0.3.0:** propose and replan would call a missing
  skill, and minerva's explore and debug would keep writing files after the handover.
- **Handover first, writers later:** minerva's promote would keep writing files that Lorestrom
  then ignores.
- **One large PR:** over 7,000 lines, beyond what one review can check.
