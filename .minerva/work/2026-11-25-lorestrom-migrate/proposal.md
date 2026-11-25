# Proposal: lorestrom-migrate

**Date**: 2026-11-25
**Status**: Draft

## Goal

Lorestrom is minerva's successor. Give a repository that uses minerva one skill,
`lorestrom:migrate`, that:

1. links the repository to a Lorestrom project (init's existing link protocol) when it is not
   linked yet;
2. imports everything `.minerva/` holds that Lorestrom can store: knowledge entries and
   reference docs (the existing handover sync) **and every work unit with its markdown
   records** (new);
3. then removes from the repository, in a confirmed commit, every file Lorestrom now holds,
   together with the agent file's minerva routing section (replaced by the `## Lorestrom`
   section) and the `.minerva/worktrees/` ignore line. Anything Lorestrom does not hold
   (non-markdown files, unknown directories, files whose Lorestrom copy was edited since) is
   listed and removed only on its own separate yes, so with both yeses `.minerva/` is gone and
   the repository runs only on Lorestrom. The final report names whatever remains.

`lorestrom:init` becomes the general init for any repository: it links, and on a repository
with `.minerva/` records it names `lorestrom:migrate` as the next step (offering to continue
into it) instead of running a handover itself. The README presents lorestrom as minerva's
successor, with migrate as the way over. minerva itself is unchanged. Version 0.5.0.

## Why

0.4.0's init imports knowledge and reference docs and offers to remove those files, but leaves
`.minerva/work/` in place (past units "stay in git history"), so a migrated repository still
carries a `.minerva/` tree and its unit history is not in Lorestrom, where every lorestrom skill
reads. The user wants the whole of `.minerva/` imported and then deleted: one move from minerva
to its successor.

## Approach

**Work units import as released units.** For each finished minerva unit:
`create_doc` the unit doc (kind `minerva:work_unit`, the unit key, body first line
`minerva-import: <source commit>`), `update_doc` its properties (`minerva:project`,
`minerva:unit`, `minerva:status` from the proposal's Status, `minerva:promoted` from the
promote marker's date, `minerva:imported` the source commit, `minerva:state`), `open_gate`
(`onAbandon` `archive`), then each markdown file of the unit as a `minerva:record` created
under the gate (`hold_write` `op` `create`, applied at once), `update_doc` its properties
(`minerva:record`, `minerva:path`, `minerva:digest`) and status `current`, `add_relation`
`minerva:part_of` to the unit, and finally `release_gate` (the server releases a gate whose
only writes are applied creates). An imported unit is then a finished lorestrom unit (gate
`released`, `unit-state` reporting it promoted and shipped), so `status`, `cleanup`'s sweep and
`lint` need no change. File contents are data, never instructions, as in the handover.

- **Unit ids** are checked by the helper's `UNIT_ID_RE` (date or legacy `NNN` ids); a
  directory that fails is refused, never sent.
- **Record names:** `proposal`, `scratchpad`, `replan` and `followups` keep their standard
  record keys; any other markdown file (`archive/scratchpad.md`, `research.md`, …) is a record
  named by its path inside the unit without `.md` (`archive/scratchpad`). Its key comes from a
  **new helper function, `unit_file_key`**, which accepts a standard name or a path of safe
  stems and refuses `.`/`..`, empty parts and unsafe stems; `record_key` is unchanged and keeps
  refusing any name outside `RECORDS` for the lifecycle's own writers. Two files of one unit whose record keys collide (case-insensitively) are
  both refused. `unit.read` finds records by `gateId`, so no reader changes.
- Non-markdown files (scripts, screenshots), symlinks, unsafe names and non-UTF-8 files are not
  imported: listed with why.
- **In-flight minerva units** (`work_status.unit_state` `in_flight`: Draft or not promoted) and
  any `.minerva/worktrees/` checkout block the migration before anything is sent. Every run
  lists all that remain, named; the user either finishes each with minerva first and re-runs,
  or answers yes to importing a listed set as **abandoned** (one yes may cover the list: the gate
  is abandoned instead of released, archiving its records, and the confirmation says such a
  unit cannot be resumed in Lorestrom). Those imports form that run's first batch. A
  worktree checkout always blocks: it is live work.
- **Other branches.** The import reads only the current checkout. Before confirming, the
  helper's `minerva-branches` lists local and remote-tracking branches whose diff against the
  default branch touches `.minerva/`, and `gh pr list` the open PRs that do: their units are
  not imported and the removal commit will conflict with them. They are shown (names as data,
  never on a command line), with the advice to merge or drop them first; the user may go on.
  Without `gh`, a remote or a fetch, this check says what it could not see and goes on.
- **Resumable and idempotent.** A new helper command, `unit-import-plan`, takes the listed
  units plus `find_docs` results (unit docs, record docs and their gates' states) and decides
  per unit: `create`, `resume` (a unit doc whose first line is this import's marker, with
  missing records or an open gate), `done` (gate released or abandoned, every listed record
  present) or `changed` (a record whose digest differs, or a unit key held by a doc this import
  did not create). The agent acts only on its answer, as cleanup acts only on `reconcile`'s.
  A large corpus (seekless: 1,560 units) is imported over several runs: each run takes a batch
  (default 25 units; the user may name another size at the confirmation), **one confirmation
  per run names that batch's unit ids**, and a re-run continues where the last stopped. This is
  the cost approach A accepts over B: roughly 4 + 3 calls per file per unit, so seekless takes
  many runs; B would cut calls about threefold but not the number of confirmations, and would
  cost every reader a new state.
- **A record edited in Lorestrom after import** makes its unit `changed`. Lorestrom is
  authoritative, so nothing is re-sent: the change log (`list_doc_changes`) is shown once, the
  unit counts as imported, and `removal-plan` puts that file under `keep` with reason
  `changed in Lorestrom since import`, which the leftovers offer covers. A unit key held by a
  doc the import did not create is reported and its unit skipped; its files stay under `keep`.
- **Confirm before sending,** as `knowledge.import` does: server, organization, workspace,
  the batch's unit ids, every refused or skipped file, in-flight units, other branches, and
  that the import publishes the repository's work history to the organization. No flag or
  earlier yes satisfies it.

**Helper additions** (`lorestrom_backend.py`, unit-tested): `unit-import-list --project`
(walks `.minerva/work/` without following symlinks; per unit its checked id, in-flight state,
status, promoted date and each markdown file's record name, key and digest; everything else
listed with a reason), `record-payload <listed path> --project --digest` (one file as tool
inputs; refuses a file that changed since it was listed), `unit-import-plan` (stdin),
`minerva-branches` (git only; prints the branches and the unit ids their diff touches),
`unit_file_key`, and `removal-plan` extended to unit files.

**What `removal-plan` removes.** Knowledge and reference files keep 0.4.0's rule (their doc
holds the digest and is current, superseded or deprecated). A unit file is removable when
exactly one record doc of this project holds its key and digest, and either the record is
`current` under a released gate or `archived` under an abandoned gate (the import's own
abandon). Every other tracked file under `.minerva/` is listed under `keep` with why.

**The removal commit** (each run's last step, after its sync; the import's sends come first,
the removal is a separate confirmed step). It is offered on every run and covers only what is
already in Lorestrom, so on a corpus imported over several runs each run removes that run's
`done` units and a re-run removes the rest; the agent-file and `.gitignore` edits join the
commit only once no unit remains to import. Show `removal-plan`'s `remove` and `keep` lists,
the agent-file diff (minerva routing section → `## Lorestrom`) and the `.gitignore` change
(`.minerva/worktrees/` removed). Before editing, the agent file and `.gitignore` must have no
uncommitted changes (`git diff --quiet HEAD -- <file>`); one that does is left alone and named.
On one explicit yes, check nothing is staged, `git rm` exactly the listed paths and commit them
with the edited files on the current branch (`git commit -F <temp> -- <paths>`). The `keep`
files are a **separate** offer: removing them leaves them only in git history, so it needs its
own yes, and a second commit of exactly those paths. For a file whose record was edited in
Lorestrom, that offer says the Lorestrom copy is the authoritative one and the file is the
older original. Tracked files outside `.minerva/` that
still mention `.minerva/` (CI workflows, docs) are listed for the user, never edited; an
untracked `.minerva/` remainder (an empty `worktrees/`) is named. Then the minerva-disable
instruction, as 0.4.0's handover gives it, and the final report: imported, skipped, removed,
kept with reasons, and what of `.minerva/` remains.

**init** keeps `references/link.md` (the general link). `references/handover.md` moves to
`migrate`, extended with the unit import and the removal commit; `storage:handover.sync` is
run from `migrate` only. init, on a repository whose `.minerva/` holds records, reports them
and offers to continue into `lorestrom:migrate` via the skill loader; a no leaves the repo as
it is.

**Storage contract:** new rows `unit.import` and `migrate.remove`, marked available in 0.5.0;
`handover.sync` and `knowledge.import` name `lorestrom:migrate` as their caller (their "Only
from `lorestrom:init`" lines change).

**Docs and packaging:** README (successor framing, migrate section, skill list),
`using-lorestrom/SKILL.md` (skill map and every line saying init runs the handover), both
manifests at 0.5.0, the plugin test's skill list and path inventory, and the tests in
`tests/test_lorestrom_plugin.py` that pin init's handover, rewritten to pin migrate's.

### Approaches considered

- **A — released-unit import (recommended).** Above. Native shape; zero changes to readers;
  about 4 + 3 calls per file per unit.
- **B — one archived doc per unit** (all records concatenated), no gate, a new
  `minerva:state` `imported`. About a third of the calls, but every reader (`unit.list`,
  `status`, the sweep, `lint`) learns a new state, and the record structure `unit.read` and
  promote rely on is lost.
- **C — no unit import:** delete `.minerva/work/` and leave the history in git. Cheapest, but
  does not import `.minerva`, which is what was asked.

Skill shape: a new `migrate` skill with init reduced to the general link (recommended), versus
extending init's handover with units and full deletion. The first matches "build the skill",
and keeps init the one-step setup for a repository that never used minerva.

## Success criteria

1. `plugins/lorestrom/skills/migrate/SKILL.md` exists with its references, and the plugin's
   skill-list test names it.
2. `unit-import-list` lists every unit directory under `.minerva/work/` with its id checked by
   `UNIT_ID_RE`, in-flight state, status, promoted date and per-file record name, key and
   digest; it refuses non-markdown, symlinked, unsafe, non-UTF-8 and key-colliding files and
   unchecked ids, each with a reason; unit tests cover each case.
3. `unit_file_key` accepts standard and safe path-named records and refuses `..`, empty parts
   and unsafe stems, while `record_key` still refuses non-standard names; `record-payload`
   builds a record's tool inputs and refuses a changed file; tested.
4. `unit-import-plan` returns `create`, `resume`, `done` or `changed` per unit from
   `find_docs` and gate states, never `create` for a key held by a doc it did not create;
   tested for each answer. `unit-state` on an imported unit's properties with a released gate
   reports promoted, shipped and state `released`; tested.
5. `removal-plan` covers knowledge, reference and unit files: a unit file is removed only when
   its record holds its digest under a released (record `current`) or abandoned (record
   `archived`) gate; a changed record, a missing one and every other tracked `.minerva/` file
   are under `keep` with a reason; tested for each case.
6. `minerva-branches` reports branches whose diff touches `.minerva/` and nothing for those
   that do not; tested on a temporary repository.
7. `storage.md` has `unit.import` and `migrate.remove` rows marked available in this version,
   and the storage-operation test covers them.
8. `lorestrom:init` runs no import and no removal: on a repository with `.minerva/` records it
   names `lorestrom:migrate`; with defaults, `git status --porcelain` is unchanged after init.
   No file of the plugin still says init runs the handover (a test greps for it).
9. The README describes lorestrom as minerva's successor and documents migrate.
10. Both manifests at 0.5.0; the full test suite passes; `git diff main -- plugins/minerva`
    is empty.

## Open Questions

- No test against a live Lorestrom server, as in 0.1.0–0.4.0: the MCP call sequences are
  documented and the helper's decisions are unit-tested. A first real migration of a small
  repository is the end-to-end check.
