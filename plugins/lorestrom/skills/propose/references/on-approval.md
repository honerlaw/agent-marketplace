# propose — on approval: unit, worktree and records

## On approval — unit setup + record writes

Steps 1–5 run from the parent repo (typically on the default branch). `<date-slug>` is a checked id: see the runtime contract's "Names are data". The unit's records are Lorestrom docs written through `storage:` operations (`skills/using-lorestrom/references/storage.md`); code lives in the worktree, addressed **via its prefixed path** — the session's working directory never changes.

**Prerequisites:** a Git repository linked to Lorestrom, with its MCP server connected. Without either, stop before step 1 and name `lorestrom:init`: nothing is written to a file instead.

1. **Derive the slug silently** from the confirmed goal title: lowercase, replace whitespace/underscores with `-`, strip everything outside `[a-z0-9-]`.

2. **Duplicate slug check** — look for a unit id ending `-<slug>` among this project's units (`storage:unit.list`), `.lorestrom/worktrees/<date-slug>/`, and any branch named `*-<slug>` **or `*-<slug>-phase-*`** (`git branch --list "*-<slug>" "*-<slug>-phase-*"`, and the same two patterns via `git branch -r --list`). If found, first check whether it is **this run's own unit**, left by an abort: for a matching checked id, read `python3 "$PLUGIN_SCRIPTS/lorestrom_runtime.py" token --unit <date-slug>` and the unit doc (`storage:unit.read`). When the token exists and the doc's first line is `minerva-token: <token>` with that token, resume with that unit's **original id** (never today's date): continue from the first missing step, each step checking before it writes. Otherwise do **not** proceed. Tell the user the existing unit / branch and suggest `lorestrom:replan` if they want to course-correct an in-flight work unit.

   The `-phase-*` pattern is not optional. A phased unit's later phases live on `<date-slug>-phase-N` branches (see [phasing.md](phasing.md)), and `*-<slug>` cannot match them — the slug is no longer the tail. Without the second pattern this check reads clean against a unit that is actively mid-flight on phase 2, which is the exact false-clean this step exists to prevent.

3. **Take today's date as the unit's id** — `date +%F`, giving `YYYY-MM-DD`. The unit is `<YYYY-MM-DD>-<slug>`.

   No scan, no max+1, no cross-branch comparison: a date is read off the clock, so two units started in parallel never negotiate for an id. **Several units sharing a date is expected**, because a unit is identified by its whole `<date>-<slug>`, not by the date alone. The duplicate-**slug** check in step 2 is what prevents a genuine collision, and `storage:unit.create` refuses a key another unit holds.

4. **Self-review the approved draft** (step 9 below) before anything is written, then **create the unit**: `storage:unit.create`. It saves an operation token, creates the unit doc and opens its gate; an interrupted create resumes on a retry, and a key held by another unit is a duplicate id: choose another slug. `minerva:base` is the default branch's commit, read in the same shell call as the default-branch snippet.

5. **Pre-flight ignore check** — verify `.lorestrom/worktrees/` is ignored: `git check-ignore -q .lorestrom/worktrees/probe`. `lorestrom:init` ignores it in this clone (or in `.gitignore` with `--shared`).

   - If ignored → continue.
   - If not → **abort**: "`.lorestrom/worktrees/` is not ignored here. Run `lorestrom:init` first, then re-run `lorestrom:propose`." The unit doc stays: a re-run finds it by its token and continues.

   Do not edit `.gitignore` from propose: propose may be invoked from inside another worktree, where the change would land on the wrong branch.

6. **Create the worktree and branch**, in the same shell call as the runtime contract's default-branch snippet ("Names are data"):

   ```
   git worktree add --no-track -b <date-slug> .lorestrom/worktrees/<date-slug> "${BASE:?}"
   ```

   Branching explicitly from the default branch (not HEAD) prevents accidentally stacking the new work unit on top of another in-flight branch when propose is invoked from another worktree. The branch name matches the unit id so reviewers can tie a branch to its unit, and so the duplicate-slug check picks up in-flight worktrees by branch.

7. **Address the worktree directly — do *not* call `EnterWorktree`.** lorestrom worktrees live under `.lorestrom/worktrees/`, which must be addressed directly in either host. The session's working directory stays the parent repo. For every later code step, prefix each file path with `.lorestrom/worktrees/<date-slug>/` and run each git command as `git -C .lorestrom/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and will silently land edits on the wrong branch.

8. **Write the proposal record** (`storage:record.write`, record `proposal`) using the approved content, structured as:

   ```markdown
   # Proposal: <slug>

   **Date**: YYYY-MM-DD
   **Status**: Draft
   **Closes**: #12, #34          <- optional; omit the line entirely when nothing is closed
   **Linked**: #56 — <title> (not adopted)   <- optional; see below

   ## Goal
   <approved goal>

   ## Why
   <approved motivation>

   ## Approach
   <approved approach — will be rewritten by lorestrom:promote to describe what shipped>

   ## Success criteria
   - <concrete, checkable item 1>
   - <concrete, checkable item 2>
   <each item must be objectively answerable yes/no when implementation is "done">

   ## Phases
   1. **<name>** — what ships in this PR, and its own success criteria.
   2. **<name>** — what ships in this PR, and its own success criteria.
   <omit this section entirely for a unit that fits one PR — which is most units>

   ## Open Questions
   - <any remaining items>
   ```

   **The `## Phases` section.** Optional, and **absent by default** — omit it unless the work
   genuinely cannot be reviewed as one pull request. When present it declares an ordered list of
   independently shippable increments, each shipping as its own PR while the unit keeps a single
   proposal, scratchpad, promote and knowledge pass. Soft ceiling of about three; more must be
   argued in the proposal. A unit without the section is unphased and every consumer treats it
   exactly as before. **Read [phasing.md](phasing.md) before declaring it** — the branch
   topology, the derived-progress rule, and the Mode B guidance all live there.

   **The `**Closes**` field.** Optional, and normally absent at propose time — you rarely
   know the issue numbers before the work is done. It is authored at the **end** of the
   work phase, by whoever just wrote the diff and therefore knows what it actually closes.

   **The one exception is an adopted issue.** When intake matched this request to an open
   issue and the user chose to execute it (see `references/issue-match.md`), the number is
   known before a line is written and the whole point of adopting it was to close it — so
   write `**Closes**: #NN` here, at creation. That is the only case where the field is
   authored this early; it does not license guessing at any other issue number.
   `lorestrom:ship` reads it when composing the PR body and emits one `Closes #N` line per
   entry, so GitHub closes the issues on merge.

   **The `**Linked**` field.** Also optional. Written at creation in exactly one case: intake
   matched this request to an open issue and the user chose **proceed as asked, link #NN**
   rather than adopting it (see `references/issue-match.md`). It is a note to the end of the
   work phase, not a promise — `lorestrom:promote` reads it and promotes it into `**Closes**`
   only if the diff turned out to resolve the issue after all. Nothing else reads it, and it
   never closes anything by itself.

   Only list an issue the diff genuinely resolves. Nothing infers this field from the diff
   or the branch name — a wrong auto-close destroys a real record, which is why the linkage
   is authored rather than guessed.

   Also write the scratchpad record (`storage:record.write`, record `scratchpad`) with this header and nothing else:

   ```markdown
   # Scratchpad: <slug>

   > **Ephemeral working memory.** Most of what lands here is noise — small
   > decisions that don't matter, dead ends, momentary confusion. At feature
   > completion, run `lorestrom:promote`: significant items get promoted to
   > knowledge entries, the proposal gets updated to match reality, and
   > the raw scratchpad is archived.

   ```

9. **Self-review the written proposal.** Re-read the proposal draft with fresh eyes and fix it before it is written:
    - **Placeholders** — any `TBD`, `TODO`, vague phrasing, or incomplete sections.
    - **Internal consistency** — does `## Approach` actually achieve `## Goal`? Do `## Success criteria` cover what `## Goal` promises?
    - **Ambiguity** — could any requirement be read two different ways? Pick one and make it explicit.
    - **Scope** — is this still a single work unit? If the prose grew past what one PR can carry, the answer is almost always to add a `## Phases` section (see [phasing.md](phasing.md)), **not** to re-decompose: the ceremony of a second unit is real and the ceremony of a second phase is not. Re-decompose with the user only when the drift is into genuinely independent subsystems — work that would not share a proposal, a reviewer, or a record.
    - **Phase numbering** — only if the draft declares `## Phases`. Ask the parser, not your eyes: write `{"proposal": <the draft>}` to a `mktemp` file with a file tool and run the helper's `phases --unit <date-slug>` on it (runtime contract, "Installed paths and helpers"). Any entry in `gaps` means a written ordinal disagrees with the phase's position. **Fix the draft** so the two agree. Everything downstream keys off *position*, so a duplicated `2.` renders fine in markdown while pointing two phases at one branch — silent, and only visible by asking. Also sanity-check each phase's `name`: one that comes back as a fragment usually means the item is missing the `**Name** — …` opening the template asks for.

    Fix issues inline. No need to re-review — just fix and move on.

10. **Post-write user gate.** Report what was created and ask:

    > "Unit `<date-slug>` created in Lorestrom with its proposal and scratchpad, on branch `<date-slug>` in worktree `.lorestrom/worktrees/<date-slug>/`. Please review the proposal and let me know if you want to change anything before we start work."

    Show the proposal's text in the conversation as well. Wait for the user's response. If they request changes, replace the proposal record (`storage:record.write`: read it, then `mode: replace`) and re-run the self-review; Lorestrom keeps each version. Only once the user approves the written proposal is it considered final. No commit is made: the branch starts at the default branch, and records never enter git.

11. Suggest `lorestrom:work` as the next step. The work skill will detect the existing worktree and address it by the same prefix.
