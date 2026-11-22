# Scratchpad: untrusted-ref-names

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-22
- [user-directed] intake: a separate patch release ahead of other in-flight work; the user merges the PR; no exploit detail in public records
- [solo] in-flight check: no collision — no open PR, issue or matching branch; no live peer in this project (tier: hardcoded check, nothing found)
- [solo] open-issue match: no open issues (tier: hardcoded check, nothing found)
- [reviewed — folded] scope check: C1 added promote's issue search; C2 status inventoried; C3 printed commands covered by the unit-id rule (tier: reviewer — scrutiny: blast radius, ambiguity; parallel wave)
- [rechecked — residual folded] scope check: C2 partially (status's fallback now takes the refs/ prefix); two wording residuals folded
- [reviewed — folded] approach: A kept; C1 unit ids checked by a no-input listing snippet and the Goal reworded to "checked id"; C2 PR state per branch; C3 explicit refs; C4 bare-mode names keep their shape (tier: reviewer — scrutiny: existing interface change, ambiguity; parallel wave)
- [rechecked — escalated] approach: F1 (remote-only default branch has no start point) → Adjudicator
- [adjudicated — escalated] approach: F1 unresolved — refs/heads/<name> fails where only the remote ref exists → user
- [escalated to user] approach: F1 — measured that today's form checks the worktree out on the default branch itself; user chose the local branch when present, otherwise origin's ref, as start point and for reads, with --no-track (escalation counter: 1)
- Residuals folded after the ruling: F2 bare-mode components start with a letter or digit and fall back to a fixed word when empty; F3 the shell, not the agent, takes commit ids from ls-remote; F4 an id from any source must equal a listed id
- Restart, whole-proposal: first-wave review discarded unread for folding — the approach fold rewrote the Goal; tier selected again on the merged draft: reviewer (scrutiny: blast radius, knowledge tension)
- [reviewed — folded] whole-proposal (restart): C1 criterion 3 narrowed to branch, ref and Python-source sites with the unit-id half tested separately; C2 --no-track enforced and tested; C3–C7 folded, the listing moves into minerva_runtime (tier: reviewer — scrutiny: blast radius, knowledge tension)
- [rechecked — residual folded] whole-proposal (restart): all seven addressed; residuals folded — the units command's compatibility and test coverage named, fetch-then-cut keeps today's tracking, allowed variables and the pointer assertion made exact
- [reviewed — clean] completion verification: Verifier accepted all six criteria; it re-ran the restoration pass and the suite, and took the eval dry-runs and lint from the checklist (tier: reviewer — Verifier floor; parallel with code review)
- [solo] review triage: 9 code-review findings — 8 fixed, 1 kept and disclosed; none changes the approach, so no replan-vs-FIX (tier: default-solo triage; no item ambiguous)

## Work notes 2026-11-22

- Runtime contract gains "Names are data": the default-branch snippet (unsets inherited values; local ref else origin's; `${BASE:?}`), `--no-track` on cuts from it, commit ids and PR numbers from command output, and the checked-unit-id rule backed by `minerva_runtime.py units` (shares `is_unit_id` with `state_path`).
- Sites rewritten in propose, work, review, ship, cleanup, promote, status and both orchestrators. One site the inventory had missed surfaced through the new guard's first run; it was argv-only and needed no change once the guard parsed double-quoted Python correctly.
- Guard `tests/test_untrusted_names.py`: placeholder-first and fail closed (unclassified placeholder, ref placeholder or ref-context placeholder, placeholder or shell expansion inside Python source, unknown or unquoted name variable, `BASE` without `:?`, a cut from `BASE` without `--no-track`), plus a pointer check and executed snippets (main, master, origin-only, an unusual valid name, nothing; bash and zsh; a `trunk` default for both phase snippets; origin-only cut has no upstream).
- Restoration pass (each changed skill hunk reversed alone in a throwaway copy): 30 of 38 fail the guard. The 8 that pass hold no branch/ref or Python-source site: redundant pointers, prose, the tail of a split Python hunk, the PR-title change (free text, out of criterion 3) and the status hardening (name already quoted).
- Mutation pass (12 chosen mutations of `units`, the snippet, `--no-track` and the phase snippet): all killed after adding the `trunk` case; before it, a hardcoded `"main"` in the phase snippet survived.
- Gates: 1160 passed (3.13); new and touched modules pass on 3.11; `units` runs on 3.9; skill and compatibility eval dry-runs and knowledge lint pass; no SKILL.md over 9216 bytes.

## Review triage 2026-11-22

Code review (fresh context, independent of the Verifier):

1. Fixed: review's diff put `${BASE:?}` inside `$(...)`, where a skipped snippet gave an empty diff with exit 0. Now `git diff "${BASE:?}"...HEAD`; pipeline uses start with `: "${BASE:?}" &&`; the runtime rule says so; the guard flags both shapes.
2. Fixed: `units` failed outside Git. It now reads `cwd` there (`test_units_works_outside_git`).
3. Fixed: an id whose worktree was removed before its branch was deleted was no longer listed, so a retried cleanup stopped. `units` also lists local branches shaped like a unit id, never a `-phase-N` branch.
4. Fixed: the bare-mode checkpoint key and branch had no shell recipe. runtime.md now has one that reads the branch and builds the JSON through argv; executed with an unusual name.
5. Fixed: the guard's generic placeholders (`name`, `target`, `x`, `unit`, `path`, `entry`, `n`) are now refused in git/gh commands. Also fixed: the dead `U=`/`UNIT=` alternatives, more branch-cut forms (`-B`, flags before `-b`, `git branch x BASE`, line continuations), Python heredocs, `$@`/`$*`, nested fences, and text inside single quotes treated as literal.
6. Fixed: the in-flight bound now covers local branches too, and `unfetched` is defined (judge by PRs; with none, in flight). Kept: one `gh` call per dated branch.
7. Kept and disclosed: the exact-match fallback in merge detection now also matches a branch checked out in a worktree, which the old `^[* ]` pattern never matched. A branch is "merged locally" only if its tip is reachable from the default branch. `git worktree remove` still refuses a dirty tree, and the confirmation gate still applies.
8. Fixed: list markup in promote and replan.
9. Fixed: an unreadable directory is counted (`unreadable`) and skipped.

The mutation pass was re-run with 8 more mutations covering the fixes: 20 of 20 killed. The suite now has 1176 tests.
