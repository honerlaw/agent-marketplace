# cleanup — releasing a unit's gate

A unit's knowledge, reference changes and edges onto existing entries are held on its
Lorestrom gate. They become current only when cleanup releases that gate on live merge
evidence, and they are discarded only when it abandons the gate. This runs **before** any
worktree or branch is removed, because the evidence is the unit's branches.

`<date-slug>` is a checked id (runtime contract, "Names are data"). Every operation named here
is a row of `skills/using-lorestrom/references/storage.md`.

## Decide: `reconcile`

1. Read the unit doc (`storage:unit.read`): its recorded `minerva:base` and, for each phase,
   `minerva:head_<n>` and `minerva:pr_<n>`. The phase count comes from the proposal's
   `## Phases` (1 when unphased). A phase with no recorded head has not shipped: it waits.
2. For each recorded PR, read its state with `gh pr view <n> --json state` (the number comes
   from the unit doc, written there by `lorestrom:ship` from `gh` output). Never type a state.
3. Write `{"phases", "heads", "base", "prs", "abandon", "merged", "age_days"}` to a `mktemp`
   file and run the helper's `reconcile`. It validates every commit, finds the default branch
   itself, gathers the git evidence, and returns `release`, `confirm`, `abandon` or `wait`.
   `--abandon` sets `abandon`; `--merged <sha>` sets `merged` to `{"<phase>": "<sha>"}` for the
   earliest unmerged phase. `age_days` is whole days since the unit doc was created, or 0 when
   that is unknown; it only marks a headless unit stale. The sha is written into the file, never
   onto a command line, and the helper checks it is a commit on the default branch.
4. **Act only on its answer.** Never release on a judgment that a unit "looks merged".

| Answer | Do |
|---|---|
| `release` | `storage:unit.release`, then `storage:unit.repair` |
| `confirm` | `storage:unit.confirm`: show the named phases and ask; `--yes` never confirms |
| `abandon` | `storage:unit.abandon`, after showing what the gate created |
| `wait` | keep the gate; report the reason, and `stale` when it is |

Releasing needs `edit` on the unit doc; a `FORBIDDEN` refusal is reported with the unit, and
the gate stays open for someone who has it.

## After a release

- `get_gate` the unit and report every held write that did not apply: its unit, the target
  doc's title and id, and the code. A **STALE reference replace** — a reference doc changed
  after the unit's hold, usually by `lorestrom:debug`'s live update — is reported with its unit
  and doc, and is **never re-applied automatically**: the user re-applies it deliberately, with
  `lorestrom:debug`'s live update or a new unit, after reading both versions.
- Refresh `minerva:state` with `unit-state`.
- Then, and only then, worktree and branch teardown proceeds.

## Units with no worktree

A unit whose worktree was removed by hand, or that was cleaned up by an older run, can still
hold an open gate. The no-argument sweep lists this project's units with open gates
(`storage:unit.list`) alongside the worktrees, and runs the same decision for each. With no
link or no server, the sweep removes merged worktrees as before and says in one line that no
gate was checked.
