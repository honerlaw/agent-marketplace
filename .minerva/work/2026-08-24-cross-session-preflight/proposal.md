# Proposal: cross-session-preflight

**Date**: 2026-08-24
**Status**: Shipped (2026-08-24)

## Goal

At work-unit intake, minerva detects work that may already be in flight **outside this
checkout's visible state** — pushed branches, open PRs, and live sibling Claude sessions on
this project — and surfaces a likely collision before a second work unit exists. The check is
advisory *detection*, explicitly **not** a lock.

## Why

Today's pre-flight reads only `.minerva/work/*/` and `.minerva/worktrees/*/.minerva/work/*/`
in this checkout, via `work_status.unit_state()["in_flight"]`. Three gaps:

1. **The pre-worktree window.** A sibling session still designing its proposal has written
   nothing to disk. That is the longest stretch before any durable artifact exists, so two
   sessions handed the same seed both sail through pre-flight.
2. **Another clone, or a session working the repo from elsewhere.** Its worktrees are not
   under this checkout's `.minerva/worktrees/`. Its pushed branch and its open PR *are*
   visible — via `git ls-remote` and `gh pr list` — and pre-flight consults neither.
3. **Live sibling Claude sessions.** The harness can enumerate them (`ListAgents`) and message
   them (`SendMessage`). Minerva never asks.

Gaps 2 and 3 overlap rather than partition: `SendMessage` reaches sessions on other machines
too, so the honest split is *durable evidence a session left behind* versus *a live session
you can still ask*.

The cost of a miss is a duplicate work unit racing a real one; one of the two gets discarded.

## Approach

One canonical protocol file, cited by every intake surface. This mirrors the shape unit
`2026-08-22-intake-matches-open-issues` validated for `issue-match.md`, including the
qualified cross-skill pointer form the pointer gate now resolves.

1. **`plugins/minerva/skills/propose/references/in-flight-check.md`** holds the protocol,
   opening with **what this check is not**. Per
   `2026-08-05-pattern-read-then-act-is-not-a-lock`, a read-then-act guard is not mutual
   exclusion, and its documented failure mode is that it *looks* sufficient so the next reader
   extends it rather than replacing it.

2. **The backstop is named together with its precondition.** `git worktree add -b <date-slug>`
   is atomic, so two sessions choosing the *same* slug cannot both create the branch. But
   `2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref` is explicit that a
   ref lock excludes only writers that push that ref, and its stated remedy is to name **the
   resource the lock protects, not just the ref**. The resource here is the *slug*, not the
   *goal* — and two sessions designing the same goal will rarely converge on the same slug.
   So for the pre-worktree race in §1 of Why, **there is no atomic backstop at all**. That
   cuts both ways and the file says so: it is why detection is worth having, and it is why
   detection must not be oversold. The residual risk — same goal, different slug, no reply —
   is stated in the protocol rather than left for a reader to discover.

3. **Four evidence sources, cheapest first**, each failing soft and independently:
   - **(a) Local work units** — today's check, moved verbatim, still *calling* the `in_flight`
     predicate rather than restating it.
   - **(b) Branches, local and remote** — work-unit branches are self-identifying
     (`<YYYY-MM-DD>-<slug>`). Read with `git ls-remote --heads origin`, not `git branch -r`: a
     stale remote-tracking ref set reads clean for a branch pushed five minutes ago.
     **Bounded for staleness** — a branch whose PR is merged or closed is not in flight, and an
     unmerged branch with no commit inside a stated recency window is reported as *stale*, not
     as a collision. Without this bound a pushed-and-abandoned branch produces a recurring
     false collision on every future intake touching its theme, forever.
   - **(c) Open PRs** — `gh pr list --state open`, behind the same capability probe
     `issue-match.md` delegates to; silent where no tracker is reachable.
   - **(d) Live sibling sessions** — below.

4. **The sibling-session query is filtered, bounded, and non-blocking.** `ListAgents` is free
   and read-only, so it always runs — but it returns the whole fleet, not this project's
   sessions. Measured on this repo at authoring time: **32 peers, of which 5 were live local
   sessions and the rest offline Remote Control or idle cloud sessions.** Messaging all of them
   would ping unrelated projects on every intake across the fleet. Three filters, all derived
   from what the listing actually carries:
   - **Liveness** — skip `offline` rows; they cannot process a message.
   - **Reply capability** — skip `cloud` rows; a cloud session receives a message but cannot
     message back, so asking one costs a turn and yields nothing.
   - **Project** — local interactive sessions are named `<project>-<suffix>`
     (`agent-marketplace-32`, `financials-4d`, `seekless-ce`). Message only peers sharing this
     session's project prefix. On the authoring repo this reduced 32 candidate peers to **0**,
     which is the intended common case: no messages at all.

   Only when the durable sources (a)–(c) are silent is the query sent — if they already
   flagged something, the ask fires on that and a ping adds nothing.

   The message is **self-describing**: it names the repo and the seed and states the reply
   contract inline (`MINERVA-BUSY <slug-or-goal>` / `MINERVA-IDLE`), so a peer that has never
   heard of this protocol — an older minerva, a bare Claude Code session — can still comply in
   one line. Cross-session replies drain at the receiver's next tool round, so intake **never
   blocks**: send, proceed, and treat a reply naming overlapping work as a collision at the
   next decision point. **Silence is "unknown", never "clear."** One message per peer per run;
   never a poll loop. Where `ListAgents`/`SendMessage` are unavailable in the running harness,
   the whole source **skips silently**, exactly as (b) and (c) do without a remote or a tracker.

5. **The match bar is behavioral and asymmetric**, same shape as `issue-match.md`'s. A
   **collision** is work that one change would satisfy for both sessions. **Adjacent** is
   everything else not plainly unrelated; same subsystem is not a collision. Unsure resolves to
   adjacent — one informational line, no question. A false collision makes the user abandon or
   re-litigate a request they just made; a missed collision costs a duplicate that the branch
   conflict or review still catches.

6. **A collision is a hardcoded ask at every surface** — `AskUserQuestion` (resume that unit /
   start fresh anyway / abandon this run) — firing regardless of the run's own skip or verify
   predicate, exactly as today's in-flight collision and the intake open-issue match do, and
   **incrementing the escalation counter** in the three autonomous orchestrators.

7. **Five intake surfaces cite it, and their per-surface qualifiers survive the collapse.**
   Per `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`, the
   four pre-flight blocks are *not* pure duplication: `-quick`/`-balanced` say "not
   main-model-decided" while `-auto` says "not panel-decided" and points at
   `panel-protocol.md`; `-quick` calls this the "only guaranteed" pre-run interaction and
   `-auto` the "only permitted" one. Each surface therefore keeps its own framing line and
   cites the shared file for the mechanics only. `propose/SKILL.md` gains an intake step beside
   the open-issue match — it has **no pre-flight block at all** today, only a duplicate-slug
   check that runs *after* the whole proposal is designed, so a standalone `minerva:propose`
   is currently the least protected surface of the five.

8. **The trigger enumerations are updated where they exist** — verified as six locations, two
   per autonomous orchestrator: each `references/governance.md` prose bullet, and the
   prose-bullet + decision-taxonomy row in `solo-decision-protocol.md` / `verify-protocol.md` /
   `panel-protocol.md`.

9. **Contract anchors** in the five `evals/*/contract.json` files pin the wiring, including the
   not-a-lock framing, so a later editor cannot quietly promote the check into a lock
   (`2026-06-06-pattern-rejected-alternative-reinvented-at-runtime`), plus a test that the
   per-surface qualifiers of step 7 survive.

**Rejected alternatives.**
*Widen the pre-flight block in place at all four orchestrators* — four copies of a protocol
several times its current length (`2026-07-21-pattern-catalog-semantic-drift-recurs`); two byte
budgets with under 400 bytes of headroom cannot absorb it; and it would still leave standalone
`minerva:propose` unprotected.
*A deterministic `scripts/session_collisions.py`* — the hard part is the match judgment, not
enumeration, and a Python script cannot call `ListAgents` at all.
*A claim-file registry* (`.minerva/sessions/<id>.json`, exclusive-create) — a genuine atomic
primitive that would close the pre-worktree window without interrupting anyone, but it sees only
sessions running minerva that got far enough to write a claim, and it adds durable state needing
crash-stale garbage collection. Recorded as the upgrade path if detection proves insufficient.
*Splitting the live-session query into its own unit* — proposed at the scope gate on the grounds
that it is the least precedented piece. Rejected: it is also the piece the seed actually asked
for, so shipping the git/gh widening alone would deliver everything except the request.

### What review changed

Review returned six findings, all fixed in place (none was a load-bearing divergence, so no
replan was triggered):

- **Step 4's skip condition was scoped wrong.** "Only send when steps 1–3 came back silent"
  let an *adjacent* result suppress the peer query — silencing the only source that sees the
  pre-worktree window exactly when unrelated noise appeared. Now scoped to "surfaced no
  **collision**", with adjacent and stale explicitly non-suppressing.
- **The staleness bound had no runnable command and an unexplained gap.** "Not in flight when
  its PR is merged or closed" could not be executed with the commands shown — step 3's
  `--state open` query cannot distinguish a merged PR from no PR. Added
  `gh pr list --state all --head <branch>` and `git log -1 --format=%cI`. The absence of an
  age bound on open PRs is now stated as deliberate: an open PR is standing human intent, a
  pushed branch is only residue.
- **The extraction was incomplete.** The four orchestrator blocks each carried a verbatim
  two-sentence summary of the protocol with nothing pinning it, so a fifth evidence source
  would have left four stale copies and a green suite. Pinned by byte-identity across the
  three autonomous rungs, a marker check on all four, and a check tying "four evidence
  sources" to the protocol file's real step run.
- **A negative-coverage test was vacuous**, asserting on a fabricated literal rather than the
  production predicate; it would have passed with the real check gutted. Both now route
  through one `block_keeps_qualifier`.
- **The section locator** required a following `## ` heading; a block placed last in its file
  would fail blaming the heading for being absent. Now tolerates end-of-file. The same latent
  defect in the pre-existing `target_resolution_block` is filed as
  [#98](https://github.com/honerlaw/agent-marketplace/issues/98).

All three new guards were mutation-tested: drifting a summary, adding a fifth evidence-source
step, and flattening a rung qualifier each turn CI red.

## Deferred work

- Apply the same locator fix to `target_resolution_block` — filed as
  [#98](https://github.com/honerlaw/agent-marketplace/issues/98) (`priority: low`).

## Success criteria

- `plugins/minerva/skills/propose/references/in-flight-check.md` exists and specifies, each in
  its own section: the not-a-lock framing, the ref-lock's same-slug precondition and the
  residual same-goal/different-slug risk, the four evidence sources, source (b)'s staleness
  bound, source (d)'s three filters + self-describing reply contract + non-blocking rule +
  fail-soft clause, the collision/adjacent bar, and the response shape.
- The four existing inline pre-flight blocks cite the protocol in the qualified
  `plugins/minerva/skills/propose/references/in-flight-check.md` form, and **each retains its
  own per-surface qualifier** (`-auto`'s "not panel-decided"/"only permitted",
  `-quick`/`-balanced`'s "not main-model-decided"/"only guaranteed").
- A test asserts those per-surface qualifiers still exist, so a future collapse cannot flatten
  them silently.
- `propose/SKILL.md` mentions `references/in-flight-check.md` on a line carrying a read
  directive (the orphan check in `tests/test_skill_budget.py`).
- All six trigger-enumeration locations still name the in-flight collision.
- All five `SKILL.md` files remain at or under the 9216-byte budget.
- Five `evals/*/contract.json` files gain anchors for the new prose, including the not-a-lock
  sentence and source (d)'s fail-soft clause; `tests/test_skill_contracts.py` passes.
- The full pytest suite passes.

## Open Questions

- Whether a peer that never replies should ever escalate on its own. Current answer: no —
  silence is recorded as unknown and the run proceeds, because the alternative stalls every
  intake on an unrelated session's turn length.
- ~~The exact recency window bounding source (b)~~ — resolved: **14 days**, applied to
  branches only. Open PRs are deliberately unbounded (see Approach step 3).
