---
name: a-skill-snippet-runs-the-primary-checkouts-code
description: Use when editing a `scripts/` module or skill prose inside a minerva worktree, or when a change appears to have no effect — PLUGIN_SCRIPTS resolves through a symlink to the PRIMARY checkout, so snippets run that branch's code, not yours. Carries the boundary against the anchor-to-primary-checkout rule, which points the opposite way.
metadata:
  type: constraint
---

# A skill snippet runs the primary checkout's code, not the worktree you are editing

**Date**: 2026-08-28
**Type**: constraint
**Summary**: PLUGIN_SCRIPTS symlinks to the primary checkout, so a worktree's edits are not what runs
**Context**: .minerva/work/2026-08-28-guard-stale-script-resolution (see git history if the worktree has been cleaned up)

## The mechanism

On a self-hosting install `~/.claude/plugins/minerva` is a **symlink** to `<repo>/plugins/minerva`
— the primary checkout. Every snippet resolves through it:

```bash
PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
```

minerva develops itself in linked worktrees under `.minerva/worktrees/<date-slug>/`, each holding
its own `plugins/minerva/scripts/` at a realpath that resolution never reaches. So a snippet run
against a work-unit branch executes **whatever branch the primary checkout is on**.

- **Adding** a function → `ImportError`. Loud, and survivable.
- **Modifying** one → imports fine, runs the old behavior, no error. You verify a change against
  code you did not write. This is the case that matters.

The same symlink is how the harness loads `SKILL.md`, so prose edits in a worktree are equally
inactive. Demonstrated 2026-08-28: a concurrent session's worktree differed from the primary
checkout in seven skill files, none of them in force in that session.

## The boundary against the anchor-to-primary rule

`2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout` says to resolve
paths with `cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd` rather than
`--show-toplevel`. **That rule does not apply here, and the two are not in conflict** — they answer
different questions:

| Question | Anchor |
|---|---|
| *Where is the shared thing I must reach across worktrees to find?* (`.minerva/worktrees/…`, the primary `.minerva/work/`) | primary checkout — `--git-common-dir` |
| *Which code am I editing right now?* (this entry) | current tree — `--show-toplevel` |

`plugin_guard.py` therefore uses `--show-toplevel` **deliberately**. Using the primary-checkout
form there would compare the resolved copy against itself and never fire — the guard would be
inert while reporting success. That other entry's own Scope section already carves this out
("whether the path reaches across worktrees or stays within the current one"); this entry is the
case it carved out.

## What is enforced

`scripts/plugin_guard.py`, invoked once per resolution site:

```bash
[ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }
```

- **It compares the whole scripts directory, not a named module.** The first design took a module
  argument, and review found two holes in it. A single site can invoke several scripts —
  `cleanup/references/reconciliation.md` runs `knowledge_lint` *and* `synthesis_status`, and only
  the first was named. And every module imports siblings (`workstream_status` imports
  `work_status`; most import `knowledge_lint`/`knowledge_spans`), so naming one left its transitive
  dependencies unchecked. Directory scope makes both **unrepresentable** rather than patched, and
  deletes the argument that could name the wrong module. A file present on only one side counts as
  divergence too — an added or removed script is as stale as an edited one.

- **Exits non-zero; does not warn.** A printed warning from a snippet is unenforced — the caller
  runs the stale code anyway, which is a constraint restated at runtime rather than enforced at
  runtime ([[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]]).
- **Compares file bytes, not realpaths.** Realpaths always differ inside a worktree, so a path
  comparison would hard-fail every self-development session even when the code is identical.
- **Silent no-op for consumer projects**, which have no `plugins/minerva/scripts/` of their own and
  cannot skew. The guard ships in shared prose to every install; a false positive there would warn
  about worktrees and symlinks at users who have neither.
- **`MINERVA_SCRIPTS` is the escape hatch at the call site.**
- **No `$ROOT` fallback in the guard line.** `tests/test_skill_snippets.py` substitutes inside the
  `python3 -c` payload and asserts no `$ROOT` survives; it is also semantically right, since an
  empty `PLUGIN_SCRIPTS` means the fallback *is* the working tree and nothing can diverge.

`tests/test_plugin_guard_sites.py` pins the registered site set, so a new resolution site is a
deliberate registration rather than a silent omission. It **counts** guards against resolutions
per file rather than checking presence: two files carry two resolution sites each, and a presence
check passes while one of them is unprotected. That set was itself the vehicle for the bug above —
pairing each file with one module name made the second module invisible to the test *and* to the
reader, which is why the registration is now files only.

## Placement: the sites are not uniform

Twelve sites across ten files, in two shapes. Seven put the assignment on the **same line** as the
`python3` call it feeds — there, the guard must be injected **inline before that call**. Inserting
it on the following line drops it into the middle of the program's continuation lines and breaks
the snippet; that was the first attempt here. Five have the assignment on its own line and take
the guard on the next line.

## What this does not fix

Skill **prose**. The harness chooses what text to load, and a stale load would omit the guard too.
Repointing the symlink at the active worktree would close both halves and is rejected on cost, not
impossibility: the symlink is global per-user while minerva supports concurrent worktrees, so
repointing for one session corrupts a sibling's. Two such sessions were live when this was
diagnosed.

## Related
- [[2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout]] — the complementary half: it anchors to the primary checkout for paths reaching ACROSS worktrees, this one anchors to the current tree for identifying the code being edited. The two answer different questions; the table above is the boundary, and reading either without the other produces the wrong anchor half the time
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — builds on: it set the plugin-cache-first precedence this leaves intact, and forbade CWD-relative paths
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also: why the guard exits non-zero instead of printing
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also: the twelve sites are consumers of one resolution rule, and adding the rule did not add them
