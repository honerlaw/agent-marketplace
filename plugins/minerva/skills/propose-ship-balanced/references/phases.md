# Phase protocols — full inline walkthroughs

Read each phase's section before executing that phase. These mirror `minerva:propose-ship-auto`'s and `minerva:propose-ship-quick`'s phases 1-to-1. The decision rule is `references/verify-protocol.md`: every gate is **main-model-decided**, and at the **reviewer gates** (scope check, approach selection, completion-verification, plus mid-work divergence / replan-acceptance / replan-vs-FIX when triggered) the main model dispatches **one** fresh-context reviewer after deciding and arbitrates inline. No phase is removed.

Each reviewer gate dispatches with a gate-specific **ARTIFACT + CONTEXT** (below), `subagent_type: general-purpose`, `model: sonnet`, `run_in_background: false` (the critique is arbitrated inline in the same turn), at most **one** dispatch per gate (no re-dispatch). CONTEXT is bounded to the run's proposal/diff, `CLAUDE.md`/`AGENTS.md`, and `.minerva/knowledge/` entries already cited this session — never a fresh corpus scan.

## Delegated skills

Every minerva skill this orchestrator runs, and the **observable mode argument** it passes. A skill
marked `inlined` has its protocol restated in the phases below, so this file's own gate policy
governs it; a skill marked `invoked` is run through the `Skill` tool and must receive its argument
on the invocation line. Never infer orchestrated mode from context — pass the argument
(`2026-06-07-decision-phase-handoff-rides-observable-intake`).

| Skill | How | Mode argument |
|---|---|---|
| `minerva:work` | inlined | `--auto=propose-ship-balanced` |
| `minerva:replan` | cited | n/a — protocol restated in Phase 2.5, never run |
| `minerva:review` | inlined | `--auto=propose-ship-balanced` |
| `minerva:promote` | inlined | `--auto=propose-ship-balanced` |
| `minerva:ship` | invoked | `--auto=propose-ship-balanced` |
| `minerva:cleanup` | invoked | `--yes` |

## Phase 1 — Propose (inline)

Replaces the user-interactive intake in `minerva:propose`.

1. **Assemble context.** Read: the inline seed, current chat history, `CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/` entries (at minimum `Type: pattern` and `Type: constraint`), the 2-3 most recent `.minerva/work/*/proposal.md` files for tone/conventions, and deferred work — any adjacent `followups.md` **and** open followup issues (`gh issue list --label "minerva:followup" --state open`), since `minerva:promote` files kept TODOs as issues wherever the repo can host them.
2. **Open-issue match.** Before designing anything, check whether an **open** GitHub issue already tracks what the seed asks for, per `plugins/minerva/skills/propose/references/issue-match.md` — read it and run it. A match is a **hardcoded ask** (`AskUserQuestion`: execute the issue instead / proceed as seeded and link it / adopt and extend), fired regardless of this run's decision policy, exactly as the in-flight-work collision is. Like every other escalation this skill counts, it **increments the global escalation counter**; it is not exempt. No match, or no reachable issue tracker, means no user contact at all. On adoption, `**Closes**: #NN` goes into `proposal.md` at creation.

3. **Design synthesis.** The main model drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) plus the 2-3 candidate approaches it considered. Context-grounded inference, not user Q&A. Keep it in conversation; write no file yet.
4. **Scope check — reviewer gate.** The main model decides: one work unit in one PR, one unit in ordered **phases**, or genuinely separate units? **Too big for one PR is a reason to phase, not to decompose** — a `## Phases` section (soft ceiling ~3) keeps one proposal, one record and one promote, while each extra unit re-pays propose, worktree, review, promote, reconciliation and ship (`plugins/minerva/skills/propose/references/phasing.md`). Decomposition survives only for genuinely independent subsystems. Then dispatch a Skeptic. ARTIFACT = the framed scope decision + recommended pick; CONTEXT = the seed + the draft proposal. Arbitrate per verify-protocol. If the decision is "decompose", abort the run cleanly: "scope check resolved to decomposition — re-run with one sub-unit at a time."
5. **Approach selection — reviewer gate.** The main model picks among its candidates. Then dispatch a Skeptic. ARTIFACT = the 2-3 candidate approaches + the recommended pick + the stated criteria; CONTEXT = the draft proposal's `## Goal`/`## Approach`. The chosen (possibly folded) approach replaces the draft's `## Approach`. Escalate if no option is dominant or a critique can't be confidently adjudicated.
6. **Whole-proposal soundness — solo.** The main model reviews the full draft for internal consistency and soundness. Escalate (no reviewer) if a public-interface or cross-cutting-contract aspect is one it cannot confidently get right alone.
7. **Worktree + branch creation.** Per `minerva:propose`'s "On approval — worktree setup + file writes": derive slug, check duplicates, check for a duplicate slug across local work / local branches / remote branches; take today's date as the id; resolve default branch; pre-flight gitignore check on `.minerva/worktrees/` (abort to user if missing); `git worktree add -b <date-slug> .minerva/worktrees/<date-slug> <default-branch>`; then address the worktree by prefix (**no `EnterWorktree`**): prefix file paths with `.minerva/worktrees/<date-slug>/` and run git as `git -C .minerva/worktrees/<date-slug> …`.
8. **File writes (inside the worktree).** Per `minerva:propose`'s "On approval — worktree setup + file writes": create `.minerva/work/<date-slug>/`; write `proposal.md` and the header-only `scratchpad.md`; append the initial `## Balanced decisions YYYY-MM-DD` block with the decisions from steps 4–6; `git add` + commit `chore: initialize <date-slug> work unit`.
9. **Self-review.** Re-read `proposal.md` with fresh eyes per `minerva:propose`'s "On approval — worktree setup + file writes" (placeholders, internal consistency, ambiguity, scope). Fix inline.
10. Continue to Phase 2.

## Phase 2 — Work (inline)

Replaces the user-interactive setup and completion signal in `minerva:work`. Implementation itself is unchanged — the main model writes code as normal, maintaining `scratchpad.md` per `minerva:work`'s implementation protocol.

1. **Setup.** Already inside the worktree. Read `proposal.md` and any `replan.md`. Open questions that survived Phase 1 surface in the final report.
2. **Implementation loop.** Implement per `minerva:work`'s "Implementation protocol" in `--auto=propose-ship-balanced` mode. No upper bound on implementation time, but the [scope-fit escape](verify-protocol.md) applies — if the change proves large, escalate.
3. **Divergence detection — reviewer gate (when triggered).** When a load-bearing divergence is suspected, the main model decides whether it warrants a replan, then dispatches a Skeptic. ARTIFACT = the suspected divergence + the main model's call (replan vs. routine choice); CONTEXT = the proposal's `## Approach`. On confirm → Phase 2.5; otherwise continue. Escalate if unsure.
4. **Completion verification — reviewer gate.** When every `## Success criteria` item appears met, build the checklist (criterion → claimed evidence → yes/no) and dispatch the **Verifier** per the Verifier brief in verify-protocol.md. ARTIFACT = the checklist + `git diff <default>...HEAD` + the proposal's `## Success criteria`. On a `revise`/`reject` naming an unmet criterion, treat it as a success-criteria divergence → auto-trigger Phase 2.5 (replan) to clarify, then resume. This gate is **never** skipped.

5. Continue to Phase 3.

## Phase 2.5 — Replan (inline, if triggered)

Mirrors `minerva:replan` with reviewer-gated acceptance.

1. Inside the worktree. Read `proposal.md`, prior `replan.md`, current `scratchpad.md`.
2. **Frame the replan** around Original plan / What changed / New plan. The main model drafts all three.
3. **New-plan acceptance — reviewer gate.** The main model accepts the drafted entry, then dispatches a Skeptic. ARTIFACT = the drafted replan entry + the proposal's current `## Approach` for comparison; CONTEXT = the divergence that triggered it. Arbitrate inline; escalate if unsure. This gate is **never** skipped.
4. **Write.** Append the entry to `replan.md` per `minerva:replan`'s "On approval — file write". If success criteria change, also edit `proposal.md`'s `## Success criteria`.
5. Return to Phase 2 (or Phase 3 if triggered from review).

## Phase 3 — Review (inline)

Replaces the user-interactive triage in `minerva:review`, whose protocol is read in `--auto=propose-ship-balanced` mode.

1. **Read context.** `proposal.md`, all `replan.md`, current `scratchpad.md` (including prior `## Review triage` blocks), `followups.md` **plus** open `minerva:followup` issues (`gh issue list --label "minerva:followup" --state open`), relevant `.minerva/knowledge/`.
2. **Diff resolution.** Same as `minerva:review`'s "Diff resolution".
3. **Generate findings.** Two passes — **minerva audit** (spec fidelity + knowledge compliance) and **code review** (if a PR exists, invoke `code-review:code-review` via the `Skill` tool; otherwise the inline structured review per `minerva:review`).
4. **Triage — solo.** The main model triages the full numbered finding set (default by the deferral bar in `plugins/minerva/skills/promote/references/deferral-bar.md`, not by severity alone: a finding with a writable failure scenario → FIX; documentation for behavior this diff touched → always FIX, never deferred; a standing fact about the system → SUGGEST, phrased as what *is* so promote can route it to a `reference` entry; everything else → IGNORE). Escalate if a finding's disposition is genuinely contested. No reviewer is dispatched (the code-review pass already supplied the independent finding set).
5. **Replan-vs-FIX — reviewer gate (when triggered).** If a FIX finding reveals a load-bearing divergence (per `minerva:review`'s heuristic), the main model decides replan vs. fix-in-place, then dispatches a Skeptic. ARTIFACT = the finding + the replan-vs-FIX call; CONTEXT = the proposal's `## Approach`. On replan, persist triage state per `minerva:review`'s "Triage persistence", trigger Phase 2.5, then re-run step 4.
6. **Apply dispositions.** Per `minerva:review`'s "On approval — file writes": FIX edited directly; SUGGEST appended to scratchpad under `## Review finding YYYY-MM-DD`; IGNORE optional.
7. Continue to Phase 4.

## Phase 4 — Promote (inline)

Replaces the user-interactive partition in `minerva:promote` Mode A, whose protocol is read in `--auto=propose-ship-balanced` mode. All gates here are **solo**.

1. Inside the worktree. Read `proposal.md`, `scratchpad.md`, `replan.md` if present.
2. **Idempotency check.** If `work_status.unit_state(<unit-dir>)["promoted"]` is true, report "already promoted" and continue to Phase 5.
3. **Partition — solo.** The main model proposes the four-way partition per `minerva:promote`'s "Mode A — no argument (end-of-work full pass)": PROMOTE / MERGE INTO PROPOSAL / DISCARD / TODO. Skip entries already `→ promoted to ...`. Escalate if an entry's bucket is genuinely ambiguous.
4. **TODO disposition — solo.** Route every TODO through the deferral bar in `plugins/minerva/skills/promote/references/deferral-bar.md` — **read it first**. An item with a writable failure scenario (specific inputs/state → wrong output, crash, data loss, exposure) is filed as a GitHub issue carrying that `**Failure scenario**:` line and a `critical`/`high`/`medium` priority per `plugins/minerva/skills/promote/references/github-issues.md` (or appended to `followups.md` when the repo cannot host issues). An item without one is a standing fact about the system: write it as a `.minerva/knowledge/` `reference` entry, or discard it. Documentation for behavior this diff touched is neither — it is finished now, as part of the work. There is no `low` tier. The main model decides; escalate if unsure.
5. **Apply writes.** Per `minerva:promote`'s "Mode A — no argument (end-of-work full pass)": write PROMOTE items as `.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md`; rewrite `proposal.md`'s `## Approach` and set Status to `Shipped (YYYY-MM-DD)`; apply TODO dispositions; archive the scratchpad and write the one-line promote marker.
6. **TODO seed gate (if any).** Do **not** auto-invoke `minerva:propose` in the same run — surface "seed new proposal" TODOs in the final report as suggested follow-ups.
7. Continue to Phase 5.

**No synthesis phase here.** `overview.md` is a shared aggregate rewritten wholesale, which made it the second-most-conflicted file in the repo once work-unit branches started touching it. It is now written only on the default branch, by `minerva:cleanup`'s reconciliation in Phase 7. Promote is add-only for the same reason — do not stage `.minerva/knowledge/index.md` or `overview.md` in Phase 6.

## Phase 5 — Ship gate

No gate: silent advancement. If the global escalation counter has reached 3, halt instead of shipping (see `references/governance.md`).

Otherwise continue to Phase 6.

## Phase 6 — Ship (delegated)

Invoke `minerva:ship <date-slug> --auto=propose-ship-balanced` via the `Skill` tool, leading with:

> "You are running inside `minerva:propose-ship-balanced`. When `minerva:ship` reaches Hard gate #1 (commit message) and Hard gate #2 (PR title + body), accept the drafted content without prompting the user. All other `minerva:ship` behavior — pre-flight, branch creation, push, PR creation, CI watch loop, auto-merge — is unchanged."

These two gates are operational tier — the main model's draft from `proposal.md` is good enough by definition. If `minerva:ship`'s CI auto-fix classifier marks a failure `other` or bails on a non-trivial test/build, **escalate to the user with the failing job log** — a hardcoded trigger, never silently decided.

When `minerva:ship` returns **in this same turn**, continue to Phase 7. If instead it ended the
turn on its CI watch, it re-enters this gate itself via `--cleanup-only` when checks settle — exactly
one of the two paths runs, never both.

## Phase 7 — Cleanup gate

Identical to `minerva:propose-ship`'s Phase 7. After `minerva:ship` returns:

1. `gh pr view <branch> --json state,mergedAt 2>/dev/null`.
2. **`MERGED`** → invoke `minerva:cleanup` via the `Skill` tool with args `<date-slug> --yes`. Report and exit.
3. **`OPEN`, auto-merge enabled** → `ScheduleWakeup` with `prompt: minerva:propose-ship-balanced --cleanup-only <date-slug> --retry=N`, `delaySeconds: 300`. Unlike ship's CI watch, this delay is deliberately a constant: what is being waited on is auto-merge landing, which can queue behind a required review or a merge queue rather than tracking CI duration, and 300 × the retry cap below is what makes that cap a ~1 hour wall-clock bound. Cap retries at 12; on exhaustion, surface manual instructions.
4. **`OPEN`, auto-merge declined** → surface manual cleanup instructions; do not schedule.
5. **`CLOSED` (not merged)** → leave the worktree; surface manual instructions.
6. **No PR found** → exit silently (ship bailed before opening one — already reported).
7. **Phased unit — not done yet.** Before reporting, re-derive `phase_progress()` (`scripts/work_status.py`). If `complete` is false, **loop back to Phase 6 and ship `next_branch`**, cut from the freshly fetched default branch — do not report and exit. Promote Mode A belongs before the FINAL phase's ship, not phase 1's; the review phase re-runs against each phase's own diff. A run that exits here silently is a unit that stalled while reporting success. Full loop rules: `plugins/minerva/skills/propose/references/phasing.md`. No-op for unphased units.

When re-entered via `--cleanup-only`, skip phases 1–6 and re-run this phase directly.
