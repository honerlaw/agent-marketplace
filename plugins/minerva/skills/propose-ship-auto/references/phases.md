# Phase protocols — full inline walkthroughs

Read each phase's section before executing that phase.

## Phase 1 — Propose (inline)

This phase replaces the user-interactive intake in `minerva:propose`.

1. **Assemble context.** Read: inline description, current chat history, `CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/` entries (at minimum `Type: pattern` and `Type: constraint`), the 2-3 most recent `.minerva/work/*/proposal.md` files for tone and conventions, and any `followups.md` whose entries could be adjacent.

2. **Design synthesis.** The main LLM drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) along with 2-3 candidate approaches it considered. This is the strategic intake — context-grounded inference rather than user Q&A. Keep it in conversation; do not write any file yet.

3. **Scope-check panel.** Dispatch panel with artifact = "is this a single work unit, or should it decompose into multiple?". On `≤1/3 accept` after revision, escalate with the sub-units the Skeptic identified as options. If user picks "decompose", abort the auto run cleanly: "scope check escalated to decomposition — re-run with one sub-unit at a time."

4. **Approach-selection panel.** Dispatch panel with artifact = the 2-3 candidate approaches + the recommended one. On consensus, the picked approach replaces the draft's `## Approach` section. On escalation, ask the user to pick.

5. **Whole-proposal-acceptance panel.** Dispatch panel with artifact = the full Goal/Why/Approach/Success-criteria/Open-Questions draft (post step 4). On `accept`, the draft is final. On revision-round failure, escalate with the Skeptic's top 1-3 concerns as a batched question.

6. **Worktree + branch creation.** Identical to `minerva:propose`'s "On approval — worktree setup + file writes" section, steps 1–7:
   - Derive slug, check for a duplicate slug across local work / local branches / remote branches, and take today's date as the id.
   - Resolve default branch.
   - Pre-flight gitignore check on `.minerva/worktrees/` — abort to user if missing.
   - `git worktree add -b <date-slug> .minerva/worktrees/<date-slug> <default-branch>`.
   - Address the worktree by prefix — **no `EnterWorktree`** (it does not reliably enter `.minerva/worktrees/`): prefix file paths with `.minerva/worktrees/<date-slug>/` and run git as `git -C .minerva/worktrees/<date-slug> …`.

7. **File writes (inside the worktree).** Identical to `minerva:propose` steps 8–9, 11:
   - Create `.minerva/work/<date-slug>/`.
   - Write `proposal.md` with the approved content per the template in `minerva:propose` step 9.
   - Write `scratchpad.md` with the header-only template from `minerva:propose` step 9.
   - Append the initial `## Panel decisions YYYY-MM-DD` block to `scratchpad.md` with the votes from steps 3–5.
   - `git add` the work-unit directory; commit `chore: initialize <date-slug> work unit`.

8. **Self-review.** Re-read `proposal.md` with fresh eyes per `minerva:propose` step 10 (placeholders, internal consistency, ambiguity, scope). Fix inline. **No post-write user gate** — the whole-proposal-acceptance panel already covered that role.

9. Continue to Phase 2.

## Phase 2 — Work (inline)

This phase replaces the user-interactive setup and completion signal in `minerva:work`. Implementation work itself is unchanged — the main LLM writes code as normal, maintains `scratchpad.md` per `minerva:work`'s implementation protocol.

1. **Setup.** Already inside the worktree from Phase 1. Read `proposal.md` and any `replan.md` entries (none on first pass). Skip the user-facing "resolve open questions" step — the proposal-acceptance panel already addressed open questions during whole-proposal review; any that remain are deferred deliberately and surface in the final report.

2. **Implementation loop.** Main LLM implements per `minerva:work`'s "Implementation protocol" section: scratchpad maintenance, divergence detection. **No upper bound on implementation time** — the auto skill doesn't cap coding work.

3. **Divergence detection.** When the main LLM notices what looks like a load-bearing divergence (a core assumption broke, the approach is shifting, scope is shifting), trigger the **divergence panel**: artifact = "is this divergence load-bearing enough to warrant a replan?". On `2/3 accept`, proceed to replan ([Phase 2.5](#phase-25--replan-inline-if-triggered)). On `≤1/3 accept`, continue implementing without replan — the panel determined the divergence was a routine choice. On escalation, ask the user.

4. **Completion verification.** When the main LLM judges that every `## Success criteria` item appears met:
   - Compose a checklist: each criterion, the evidence (test name, file path, behavior observed), and a yes/no.
   - Dispatch the **completion-verification panel**: artifact = the checklist + the latest diff (`git diff <default>...HEAD`). The panel votes on whether each criterion is honestly checkable.
   - On `3/3 accept`, advance to Phase 3.
   - On `≤1/3 accept`, this is treated as a **success-criteria divergence**, not a regular consensus failure — auto-trigger Phase 2.5 (replan) to clarify the criteria, then resume implementation. Skip the standard revise-and-revote.
   - On `2/3 accept`, proceed but log dissent concerns to scratchpad for the review phase to scrutinize.

## Phase 2.5 — Replan (inline, if triggered)

Mirrors `minerva:replan`'s protocol with panel-based acceptance.

1. Already inside the worktree. Read `proposal.md`, prior `replan.md` entries, current `scratchpad.md`.

2. **Frame the replan** around the three pieces: Original plan / What changed / New plan. The main LLM drafts all three.

3. **New-plan-acceptance panel.** Artifact = the full replan entry draft + the proposal's current `## Approach` for comparison. On `3/3 accept`, write. On revision-round failure, escalate.

4. **Write.** Append the entry to `replan.md` per `minerva:replan`'s "On approval — file write" section. If the new plan changes success criteria, also edit `proposal.md`'s `## Success criteria` section.

5. Return control to Phase 2 (or Phase 3 if replan was triggered from review).

## Phase 3 — Review (inline)

Replaces the user-interactive triage in `minerva:review`. Diff resolution and finding generation can still delegate to `code-review:code-review` for PR-mode, but the triage is panel-driven.

1. **Read context.** `proposal.md`, all `replan.md` entries, current `scratchpad.md` (including prior `## Review triage YYYY-MM-DD` blocks), `followups.md`, and relevant `.minerva/knowledge/` entries.

2. **Diff resolution.** Same as `minerva:review`'s "Diff resolution" section.

3. **Generate findings.** Two passes:
   - **Minerva audit** (inline): spec fidelity (does the diff achieve `## Goal`, `## Approach`, `## Success criteria`?) + knowledge compliance (does the diff violate any documented pattern/constraint/decision?).
   - **Code review**: if a PR exists for this branch, invoke `code-review:code-review` via the `Skill` tool. Otherwise, perform the inline structured code review per `minerva:review`'s "Code review invocation" section.

4. **Triage panel.** Single panel call for the full set of numbered findings. Artifact = the findings list + proposed dispositions (default: high → FIX, medium → SUGGEST, low → IGNORE). Each panel agent reviews the disposition for every finding and votes on the set as a whole. On `2/3 accept`, apply dispositions. On `≤1/3 accept`, revise (the main LLM adjusts dispositions per Skeptic critique) and re-vote. On revision-round failure, escalate with the contested findings.

5. **Replan-vs-FIX check.** If any FIX finding reveals a load-bearing divergence (per `minerva:review`'s "Load-bearing divergence" heuristic), dispatch a **replan-vs-FIX panel** with that finding's context. On `2/3 accept for replan`, persist current triage state to scratchpad per `minerva:review`'s "Triage persistence" section, then trigger [Phase 2.5](#phase-25--replan-inline-if-triggered). After replan completes, return to step 4 (re-run triage).

6. **Apply dispositions.** Per `minerva:review`'s "On approval — file writes" section. FIX items get edited directly; SUGGEST items append to scratchpad under `## Review finding YYYY-MM-DD`; IGNORE items optional.

7. Continue to Phase 4.

## Phase 4 — Promote (inline)

Replaces the user-interactive partition in `minerva:promote` Mode A.

1. **Already inside the worktree.** Read `proposal.md`, `scratchpad.md`, `replan.md` if present.

2. **Idempotency check.** If `work_status.unit_state(<unit-dir>)["promoted"]` is true, report "already promoted" and continue to Phase 5. Use that predicate, never a match against the marker string — the marker has nine spellings in one 51-unit corpus and a string match reads 16 of them as un-promoted, re-running a mutating pass.

3. **Partition draft.** The main LLM proposes a four-way partition per `minerva:promote` Mode A step 3: PROMOTE / MERGE INTO PROPOSAL / DISCARD / TODO. Skip entries already marked `→ promoted to ...`.

4. **Partition panel.** Artifact = the full partition with one-line justifications per entry. On `2/3 accept`, apply. On revision-round failure, escalate with the contested entries.

5. **TODO disposition panel.** Only if any entries landed in the TODO bucket. Artifact = each TODO with a proposed disposition (followups.md / seed new proposal / discard). On `2/3 accept`, apply. On revision-round failure, escalate.

6. **Apply writes.** Per `minerva:promote` Mode A step 7: write PROMOTE items as `.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md` using the knowledge entry template; rewrite `proposal.md`'s `## Approach` (and Status to `Shipped (YYYY-MM-DD)`); apply TODO dispositions; archive the scratchpad and write the one-line promote marker.

7. **TODO seed gate (if any).** If any TODO was marked "seed new proposal", do **not** auto-invoke `minerva:propose` in the same run — surface the list in the final report as suggested follow-up work units. Auto mode does not cascade into new auto runs without explicit user direction.

8. Continue to Phase 5.

**No synthesis phase here.** Earlier revisions refreshed `overview.md` between promote
and ship so it could ride the same PR. It no longer does: `overview.md` is a shared
aggregate, and writing it on a work-unit branch made it the second-most-conflicted
file in the repo (33% of commits, rewritten wholesale — nothing can merge that). It is
now written only on the default branch, by `minerva:cleanup`'s reconciliation in
Phase 7, where there is one writer at a time. Promote is add-only for the same reason;
do not stage `.minerva/knowledge/index.md` or `overview.md` in Phase 6.

## Phase 5 — Ship gate

There is no gate. The `promote → ship` confirmation that `minerva:propose-ship` requires is replaced by silent advancement. If the completion-verification panel in Phase 2 voted with full consensus and the review + promote panels also accepted, the auto skill trusts those signals and proceeds.

If the global escalation counter has reached 3 by this point, halt instead of shipping (see the failure-modes caps in `references/governance.md`).

## Phase 6 — Ship (delegated)

Invoke `minerva:ship` via the `Skill` tool. Before invoking, lead with this auto-mode instruction:

> "You are running inside `minerva:propose-ship-auto`. When `minerva:ship` reaches Hard gate #1 (commit message) and Hard gate #2 (PR title + body), accept the drafted content without prompting the user. All other `minerva:ship` behavior — pre-flight, branch creation, push, PR creation, CI watch loop, auto-merge — is unchanged."

These two gates are operational tier and don't warrant panel calls — the main LLM's draft from `proposal.md` is good enough by definition.

If `minerva:ship`'s CI auto-fix classifier marks a failure as `other` or bails on a non-trivial test/build, **do not panel-vote on the bail** — escalate to the user with the failing job log. This is a hard escalation trigger.

## Phase 7 — Cleanup gate

Identical to `minerva:propose-ship`'s Phase 7. After `minerva:ship` returns:

1. `gh pr view <branch> --json state,mergedAt 2>/dev/null`.
2. **`MERGED`** → invoke `minerva:cleanup <date-slug> --yes` via the `Skill` tool. Besides removing the worktree, cleanup reconciles the knowledge wiki on the default branch — cataloguing this unit's entries from their `**Summary**` fields, writing their reciprocal links, and refreshing `overview.md` if warranted — and opens a single auto-merging PR for it. Surface that PR (and any reconciliation refusals) in the final report. Report and exit.
3. **`OPEN`, auto-merge enabled** → `ScheduleWakeup` with `prompt: minerva:propose-ship-auto --cleanup-only <date-slug> --retry=N`, `delaySeconds: 300`. Unlike ship's CI watch, this delay is deliberately a constant: what is being waited on is auto-merge landing, which can queue behind a required review or a merge queue rather than tracking CI duration, and 300 × the retry cap below is what makes that cap a ~1 hour wall-clock bound. Cap retries at 12. On exhaustion, surface manual instructions.
4. **`OPEN`, auto-merge declined** → surface manual cleanup instructions; do not schedule wake-up.
5. **`CLOSED` (not merged)** → leave worktree in place; surface manual cleanup instructions.
6. **No PR found** → exit silently (ship must have bailed before opening one — already reported above).

When re-entered via `--cleanup-only`, skip phases 1–6 and re-run this phase directly.

