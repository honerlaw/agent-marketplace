# migrate — removing `.minerva/` (`storage:migrate.remove`)

The last step of each run, after that run's sends. It is its own confirmed step: a yes to an
import is never a yes to a removal. No earlier yes, flag or argument answers one. Follow
`skills/using-lorestrom/references/storage.md`'s `migrate.remove` row for the reads and the
plan.

## 1. The plan

`removal-plan` prints:

- `remove` — every file whose content Lorestrom now holds: a knowledge entry or reference
  doc whose doc holds its exact `minerva:digest` and is current, superseded or deprecated,
  and a unit file whose record holds its exact digest under the import's own closed gate.
- `keep` — every other tracked file under `.minerva/`, with why: not markdown, in a
  directory the import does not read, refused, changed in Lorestrom since import, or a doc
  the user kept. A file whose digest differs from its doc's is never removed by this commit.
- `notChecked` — units not looked up this run, counted. Later batches cover them.
- `unitsRemaining` — units not yet imported. At 0 the migration's import is complete.

Write the plan's paths with `--write-remove` and `--write-keep` (two `mktemp` files, one path
per line): the commits below take their paths only from those files, never typed.

## 2. The removal commit

Show the count of `remove` paths and the paths themselves (grouped by directory when there are
many), and every `keep` path with its reason. When `unitsRemaining` is 0, also show:

- **The agent file.** When `AGENTS.md` (or `CLAUDE.md`) has a minerva routing section, the
  diff that replaces it with the `## Lorestrom` section from `skills/init/references/link.md`.
- **`.gitignore`.** The diff that drops its `.minerva/worktrees/` line, when it has one.

Either file with uncommitted changes (`git diff --quiet HEAD -- <file>` fails) is left alone
and named: the commit would sweep the user's edits in.

Then ask once. On an explicit yes, and only then:

1. Check `git diff --cached --quiet`: anything already staged stops the removal, and the user
   is told why.
2. Make the two edits, when shown.
3. `git --literal-pathspecs rm -q --pathspec-from-file=<remove file>`.
4. Write a message naming the counts to a `mktemp` file, add the edited files' names to the
   remove file, and `git --literal-pathspecs commit -q -F <message file>
   --pathspec-from-file=<remove file>`, so the commit holds exactly those paths, on the
   current branch.

A no keeps everything: `git status --porcelain` is unchanged.

## 3. The leftovers offer

Only when `unitsRemaining` is 0 and `keep` is not empty. Say that these files are not in
Lorestrom as they are here, and that removing them leaves them only in git history. A file
changed in Lorestrom since import is named as such: Lorestrom's copy is the authoritative one
and the file is the older original. Ask for a yes to the whole list, or the paths to leave.
On a yes, remove exactly the agreed paths in a second commit, as in steps 1, 3 and 4 above,
using the keep file (less any path the user named).

## 4. What remains

List tracked files outside `.minerva/` that still mention it (`git grep -l -F .minerva/ --
':!.minerva'`), such as CI workflows and docs: the user edits those, never this skill. Name an
untracked `.minerva/` remainder (an empty `worktrees/`, say). Report both in the final report.
