# In-flight work collision — the intake pre-flight

Before a work unit is created, check whether the work is **already in flight** — in this
checkout, in another clone, or in a live sibling Claude session — and offer to resume it
instead of starting a second unit.

**Read this file before creating a work unit.** Run the commands; do not paraphrase them.

## Step 0 — What this check is, and what it is not

This is **detection, not mutual exclusion.** A read followed by an act is never a lock
(`2026-08-05-pattern-read-then-act-is-not-a-lock`): the window between "nothing found" and
"branch created" is always there, and a busier fleet finds it more often. That entry's stated
failure mode is that such a guard *looks* sufficient, so the next reader extends it rather than
replacing it. Do not extend this into a lock.

**The atomic primitive, and its precondition.** `git worktree add -b <date-slug>` creates a
branch ref, and a ref create is atomic: of two sessions choosing the **same slug**, exactly one
succeeds. But a ref lock binds only writers that push that ref
(`2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref`), and that entry's
remedy is to name **the resource the lock protects, not just the ref**. The resource here is
the **slug**, not the **goal**.

So state the residual risk plainly rather than leaving a reader to find it: **two sessions
designing the same goal will rarely choose the same slug**, and for them there is no atomic
backstop at all. That is exactly why this detection is worth running — and exactly why a clean
result is not a guarantee. A clean result means *no evidence was found*, nothing more.

## Step 1 — Local work units

List `.minerva/work/*/` plus `.minerva/worktrees/*/.minerva/work/*/`. For each unit holding a
`proposal.md`, ask `work_status`:

```bash
python3 -c "import sys; sys.path.insert(0, '<scripts>'); from work_status import unit_state; print(unit_state('.minerva/work/<date-slug>')['in_flight'])"
```

`in_flight` is `Status is Draft` **or** not promoted. **Call the predicate — do not restate it
as a string comparison**: the promote marker has eight spellings in this corpus and `Status`
has two, and matching one spelling of either reads a finished unit as live work.

## Step 2 — Branches, local and remote

Work-unit branches are self-identifying (`<YYYY-MM-DD>-<slug>`), so the branch list is a
second record of in-flight work — including work from a clone whose worktrees this checkout
cannot see.

```bash
git branch --list
git ls-remote --heads origin
```

Use `git ls-remote`, **not** `git branch -r`: remote-tracking refs are only as fresh as the
last fetch, so `git branch -r` reads clean for a branch pushed five minutes ago.

**Bound this source for staleness.** A pushed-and-abandoned branch otherwise produces a
recurring false collision on every future intake touching its theme, forever. Two bounds:

```bash
git log -1 --format=%cI <branch>              # newest commit — older than 14 days is stale
gh pr list --state all --head <branch> --json number,state   # merged/closed is not in flight
```

Use `--state all`, not the `--state open` query in step 3: that one cannot tell a branch whose
PR merged from a branch that never had one. A branch whose PR is merged or closed is **not** in
flight. An unmerged branch whose newest commit is older than **14 days** is reported as *stale*
— named in one line, never raised as a collision.

**Step 3 gets no such bound, deliberately.** An open PR is standing human intent that someone
chose not to withdraw; a pushed branch is only residue. Age alone is not evidence an open PR
was abandoned, so it is never aged out.

## Step 3 — Open pull requests

Run the capability probe in `minerva:promote`'s "Step 1 — Capability probe", exactly as written
there. A non-zero exit (no `gh`, not authenticated, no GitHub remote) or `hasIssuesEnabled:
false` means **skip this step silently**.

```bash
gh pr list --state open --json number,title,headRefName,author,updatedAt
```

An open PR is work that is in flight and already shipped-but-unmerged.

## Step 4 — Live sibling Claude sessions

Steps 1–3 read what a session **left behind**. This step asks a session that is **still live**,
and it is the only source that sees the *pre-worktree window* — a peer still designing its
proposal has written nothing to disk yet, and that is the longest stretch of any run.

**Skip silently if `ListAgents` or `SendMessage` is unavailable in the running harness**, the
same way steps 2 and 3 skip without a remote or a tracker. Never fail an intake over it.

### 4a — Enumerate, then filter hard

`ListAgents` is free and read-only, so always run it. It returns the **whole fleet**, not this
project's sessions — measured on the authoring repo it returned **32 peers**, of which 5 were
live local sessions and the rest offline Remote Control or idle cloud sessions. Messaging all
of them would ping unrelated projects on every intake, fleet-wide. Apply all three filters:

- **Liveness** — skip rows marked `offline`; they cannot process a message.
- **Reply capability** — skip `cloud` rows. A cloud session receives a message but cannot
  message back, so asking one costs a turn and yields nothing.
- **Project** — local interactive sessions are named `<project>-<suffix>`
  (`agent-marketplace-32`, `financials-4d`, `seekless-ce`). Message only peers sharing this
  session's project prefix.

On the authoring repo those filters reduced 32 candidate peers to **0**. That is the intended
common case: **no messages at all**.

**Only send when steps 1–3 surfaced no _collision_.** If they already found one, the ask in
step 6 fires on that evidence and a ping adds nothing. An **adjacent** or **stale** result does
**not** suppress this step: those are not collisions, and this is the only source that sees a
live peer with nothing on disk yet. Suppressing on adjacent noise would silence the step
exactly when it is doing the job it exists for.

### 4b — One self-describing message per peer

The message must carry its own contract, because a peer may be running an older minerva, a
different project, or no minerva at all, and still needs to be able to answer:

```
[minerva pre-flight] I'm about to start work in <repo> on: "<seed>".
Are you working on anything that overlaps? Reply with one line:
MINERVA-BUSY <slug-or-one-line-goal>   — if you are working in this repo
MINERVA-IDLE                            — if you are not
```

**One message per peer per run. Never a poll loop, and never a follow-up "are you done?".**

### 4c — Never block on the reply

Cross-session replies drain at the receiver's next tool round, so a reply may not arrive for
minutes. **Intake does not wait.** Send, proceed with the run, and if a reply naming
overlapping work arrives at any later point, handle it as a collision at the next decision
point.

**Silence is `unknown`, never `clear`.** A peer may be busy, may not answer, or may not have
understood the contract. Record it as unknown and proceed — the alternative stalls every intake
on an unrelated session's turn length.

## Step 5 — The match bar

Two outcomes, and the gap between them is deliberate.

- **collision** — the other session's work and this request would be satisfied by
  **substantially the same change**. One diff would close both.
- **adjacent** — everything else not plainly unrelated: same subsystem, same theme, a
  prerequisite, a sibling. **Same area is not a collision.**

**When unsure, resolve to `adjacent`.** The errors are not symmetric. A false collision makes
the user abandon or re-litigate a request they made moments ago, at the point they are least
able to check the claim. A missed collision costs a duplicate work unit — which the branch-name
conflict, review, or promote still catches later. Only one of those is recoverable downstream.

## Step 6 — Response shape

A **collision** is a **hardcoded ask** at every intake surface. It fires regardless of a run's
own skip or verify predicate — exactly like the intake open-issue match
(`plugins/minerva/skills/propose/references/issue-match.md`) — and in the three autonomous
orchestrators it **increments the run's global escalation counter**. It is not exempt.

Ask with `AskUserQuestion`, naming what was found and where it came from (which unit, branch,
PR, or session):

- **Resume that work** — the existing unit becomes the target; `minerva:work <date-slug>`.
- **Start fresh anyway** — proceed as asked, having been told.
- **Abandon this run** — stop; nothing is created.

An **adjacent** result gets **one line** and no question — "branch `<x>` is related but not the
same thing" — so the user can pull it in without being asked to decide. A **stale** branch from
step 2 and an **unknown** peer from step 4 are reported the same way: one line, no question.
