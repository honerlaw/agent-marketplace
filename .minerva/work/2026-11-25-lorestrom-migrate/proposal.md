# Proposal: lorestrom-migrate

**Date**: 2026-11-25
**Status**: Shipped (2026-11-25)

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

What was built (lorestrom 0.5.0). A new skill, `lorestrom:migrate`, runs eight steps:

1. link (init's `references/link.md`) when the repository is not linked;
2. settle live minerva work;
3. sync knowledge and reference docs (`references/handover.md`, `storage:handover.sync`);
4. import one batch of units (`storage:unit.import`);
5. remove what that run finished (`storage:migrate.remove`, `references/removal.md`);
6. offer the next batch;
7. disable minerva once no unit remains;
8. report.

`lorestrom:init` only links. When `.minerva/` holds files, init names migrate and offers to
continue into it.

**Units import as released lorestrom units.** Each unit is a unit doc (kind
`minerva:work_unit`, the unit key, body first line `minerva-import: <source commit>`, property
`minerva:imported`) with its own gate. Each markdown file becomes a `minerva:record` created
under that gate (`hold_write` op `create`) with its digest, status `current` and a
`minerva:part_of` edge. The gate is then released, or abandoned for an in-flight unit the user
said yes to giving up, which archives its records.

- **Record keys.** `proposal`, `scratchpad`, `replan` and `followups` keep their standard
  keys. Any other markdown file is named by its path, through the new `unit_file_key`.
  `record_key` is unchanged.
- **Refusals.** Non-markdown files, symlinks, unsafe names, non-UTF-8 files, oversize files
  and record names that differ only in case are refused with a reason.
- **Effect on other skills.** An imported unit reads as promoted and shipped, so `status`,
  `cleanup` and `lint` need no change.

**Helper commands** (`lorestrom_backend.py`):

- **`unit-import-list`** reads every unit's state but prints files for one batch only
  (`--batch`, default 25; `--after <id>`). It also prints `inFlight`, the minerva worktrees
  still on disk and the refusals. A unit is in flight when its `proposal.md` is present and is
  Draft, never promoted, or refused (its state is then unknown). A unit whose proposal the
  removal already took is not live work.
- **`record-payload`** builds one file's tool inputs and refuses a file that changed since it
  was listed.
- **`unit-import-plan`** decides each unit from what the agent read in Lorestrom:
  - `create`, `resume`, `done`, `changed`, `taken` or `blocked`;
  - with the rows `send`, `finish` (created, never finished: the body is rewritten with
    `write_doc_body`, then the properties are set), `relate` (finished on an open gate: add any
    missing edge), `changed` and `removable`.
  - Once the import's gate is released or abandoned, the unit is decided from Lorestrom alone,
    so the removal's own deletions never make it blocked again.
  - A `marker` must come with the unit doc it was read from.
- **`removal-plan`** accepts `{docs, units}` beside its old list input, which is unchanged.
  - **A unit file is removed** only when its record holds its exact digest, `current` under a
    released gate or `archived` under an abandoned one, and git can remove it: tracked, no
    uncommitted edits, a UTF-8 name, and a first commit already made.
  - **Every other file under `.minerva/` is kept** with a reason and a `removable` flag. A
    `taken` unit's files are kept for good. A unit an earlier batch's commit removed is
    skipped.
  - `--write-remove` and `--write-keep` write the paths to temp files for
    `git --literal-pathspecs rm/commit --pathspec-from-file`, so no path is typed or placed on
    a command line.
- **`minerva-branches`** lists the branches holding `.minerva/` content that the checkout's
  history never held. A squash-merged branch is not listed, even after the removal commit.

**Confirmations.**

- Every batch's sends wait for one explicit yes, which names the server, organization,
  workspace, units by action, refusals, in-flight units and other branches.
- Each run's removal is its own yes. Only when no unit remains does that commit also replace
  (or, if a `## Lorestrom` section exists already, delete) the agent file's minerva section
  and drop the `.minerva/worktrees/` ignore line.
- What Lorestrom does not hold goes only on a third, separate yes.
- Files outside `.minerva/` that mention it are listed, never edited.

**Storage contract:** new rows `unit.import` and `migrate.remove`. `handover.sync` and
`knowledge.import` are called only from migrate. The incomplete-import remedies in lint,
status and the helper name migrate.

**Docs and packaging:** the plugin README and root README frame lorestrom as minerva's
successor, with a "Migrating from minerva" section. Both manifests and `COMPATIBILITY.md` are
at 0.5.0, and the marketplace description was updated. The plugin tests pin migrate's safety
clauses in place of init's handover. minerva is unchanged.

### Approaches considered

- **A — released-unit import (chosen).** Native shape, no reader changes; about 4 + 3 calls
  per file per unit.
- **B — one archived doc per unit.** About a third of the calls, but every reader would have
  to learn a new state, and the record structure would be lost.
- **C — no unit import.** Does not import `.minerva`, which is what was asked.

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
