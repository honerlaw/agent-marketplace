# Phase protocols — full inline walkthroughs

Read each phase's section before executing that phase.

Every strategic/tactical gate below follows `references/decision-protocol.md`: **draft the decision, then choose its tier** (solo / reviewer / panel) by the tier-selection order, clamped to the row's floor and ceiling in its Decision taxonomy. Each gate names its ARTIFACT + CONTEXT; the same pair is used whichever tier the decision reaches. At the reviewer tier, dispatch via the independent reviewer operation and **wait for results** before arbitrating; at the panel tier, apply `minerva:round-table` in caller mode at the taxonomy's quorum. CONTEXT is bounded to the run's proposal/diff, `CLAUDE.md`/`AGENTS.md`, and `.minerva/knowledge/` entries already cited this session — never a fresh corpus scan.

## Delegated skills

Every minerva skill this orchestrator runs, and the **observable mode argument** it passes. A skill
marked `inlined` has its protocol restated in the phases below, so this file's own gate policy
governs it; a skill marked `invoked` is run through the skill loader and must receive its argument
on the invocation line. Never infer orchestrated mode from context — pass the argument
(`2026-06-07-decision-phase-handoff-rides-observable-intake`).

| Skill | How | Mode argument |
|---|---|---|
| `minerva:work` | inlined | `--auto=propose-ship-auto` |
| `minerva:replan` | cited | n/a — protocol restated in Phase 2.5, never run |
| `minerva:review` | inlined | `--auto=propose-ship-auto` |
| `minerva:promote` | inlined | `--auto=propose-ship-auto` |
| `minerva:ship` | invoked | `--auto=propose-ship-auto` |
| `minerva:cleanup` | invoked | `--yes` |

## Phase 1 — Propose (inline)

This phase replaces the user-interactive intake in `minerva:propose`.

1. **Assemble context.** Read: inline description, current chat history, `CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/` entries (at minimum `Type: pattern` and `Type: constraint`), the 2-3 most recent `.minerva/work/*/proposal.md` files for tone and conventions, and deferred work — any adjacent `followups.md` **and** open followup issues (`gh issue list --label "minerva:followup" --state open`), since `minerva:promote` files kept TODOs as issues wherever the repo can host them.

2. **Open-issue match.** Before designing anything, check whether an **open** GitHub issue already tracks what the seed asks for, per `skills/propose/references/issue-match.md` — read it and run it. A match is a **hardcoded ask** (the user question operation: execute the issue instead / proceed as seeded and link it / adopt and extend), fired regardless of this run's decision policy, exactly as the in-flight-work collision is. Like every other escalation this skill counts, it **increments the global escalation counter**; it is not exempt. No match, or no reachable issue tracker, means no user contact at all. On adoption, `**Closes**: #NN` goes into `proposal.md` at creation.

3. **Design synthesis.** The main LLM drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) along with 2-3 candidate approaches it considered. This is the strategic intake — context-grounded inference rather than user Q&A. Keep it in conversation; do not write any file yet.

4. **Scope check (tiered).** The main model decides: one work unit shipped in one PR, one unit shipped in ordered **phases**, or genuinely separate units? ARTIFACT = the framed scope decision + the recommended pick; CONTEXT = the seed + the draft proposal. **Too big for one PR is a reason to phase, not to decompose** — the panel's default for oversized-but-coherent work is a `## Phases` section (soft ceiling ~3), which keeps one proposal, one record and one promote; see `skills/propose/references/phasing.md`. Frame the cost of splitting explicitly for whoever reviews it: each extra unit re-pays propose, worktree, review, promote, knowledge reconciliation and ship, and re-derives the context the last unit just built; phasing re-runs only review and ship. Decomposition survives only for genuinely independent subsystems. If the decision (at any tier, or from a user escalation) is "decompose", abort the run cleanly: "scope check resolved to decomposition — re-run with one sub-unit at a time."

5. **Approach selection (tiered).** The main model picks among its 2-3 candidates. ARTIFACT = the candidate approaches + the recommended pick + the stated criteria; CONTEXT = the draft proposal's `## Goal`/`## Approach`. Solo only if ≥2 approaches were enumerated and one is strictly dominant (the solo predicate's action check); the log records the rejected alternatives. Once the decision stands — after any fold and re-check, or a panel accept — the picked approach replaces the draft's `## Approach`.

6. **Whole-proposal soundness (tiered).** The main model reviews the full draft for internal consistency and soundness (does `## Approach` achieve `## Goal`; do the criteria cover the goal; is anything unsatisfiable or two-way ambiguous) and writes its verdict down. ARTIFACT = the complete draft, all five sections (post step 5); CONTEXT = the seed + the `.minerva/knowledge/` entries cited this session. Once the decision stands, the draft is final.

7. **Worktree + branch creation.** Identical to `minerva:propose`'s "On approval — worktree setup + file writes":
   - Derive slug, check for a duplicate slug across local work / local branches / remote branches, and take today's date as the id.
   - Resolve default branch.
   - Pre-flight gitignore check on `.minerva/worktrees/` — abort to user if missing.
   - `git worktree add -b <date-slug> .minerva/worktrees/<date-slug> <default-branch>`.
   - Address the worktree by prefix — **no `EnterWorktree`** (it does not reliably enter `.minerva/worktrees/`): prefix file paths with `.minerva/worktrees/<date-slug>/` and run git as `git -C .minerva/worktrees/<date-slug> …`.

8. **File writes (inside the worktree).** Identical to `minerva:propose`'s "On approval — worktree setup + file writes":
   - Create `.minerva/work/<date-slug>/`.
   - Write `proposal.md` with the approved content per the template in `minerva:propose`'s "On approval — worktree setup + file writes".
   - Write `scratchpad.md` with the header-only template in `minerva:propose`'s "On approval — worktree setup + file writes".
   - Append the initial `## Decisions YYYY-MM-DD` block to `scratchpad.md` with the tiered decisions from steps 4–6.
   - `git add` the work-unit directory; commit `chore: initialize <date-slug> work unit`.

9. **Self-review.** Re-read `proposal.md` with fresh eyes per `minerva:propose`'s "On approval — worktree setup + file writes" (placeholders, internal consistency, ambiguity, scope). Fix inline. **No post-write user gate** — the whole-proposal soundness gate already covered that role.

10. Continue to Phase 2.

## Phase 2 — Work (inline)

This phase replaces the user-interactive setup and completion signal in `minerva:work`. Implementation work itself is unchanged — the main LLM writes code as normal, maintains `scratchpad.md` per `minerva:work`'s implementation protocol.

1. **Setup.** Already inside the worktree from Phase 1. Read `proposal.md` and any `replan.md` entries (none on first pass). Skip the user-facing "resolve open questions" step — the whole-proposal gate already addressed open questions; any that remain are deferred deliberately and surface in the final report.

2. **Implementation loop.** Main LLM implements per `minerva:work`'s "Implementation protocol" section in `--auto=propose-ship-auto` mode: scratchpad maintenance, divergence detection. **No upper bound on implementation time** — the auto skill doesn't cap coding work.

3. **Divergence detection.** When the main LLM notices what looks like a load-bearing divergence (a core assumption broke, the approach is shifting, scope is shifting), the main model calls it (replan vs. routine choice), then convenes the **divergence panel** (panel floor): ARTIFACT = the suspected divergence + the main model's call; CONTEXT = the proposal's `## Approach`. On `2/3 accept`, proceed to replan ([Phase 2.5](#phase-25--replan-inline-if-triggered)). On `≤1/3 accept`, continue implementing without replan — the panel determined the divergence was a routine choice. On escalation, ask the user.

4. **Completion verification.** When the main LLM judges that every `## Success criteria` item appears met:
   - Compose a checklist: each criterion, the evidence (test name, file path, behavior observed), and a yes/no.
   - Route it: reviewer floor, so the **Verifier** unless the panel predicate holds (e.g. the diff changes a public interface), in which case a panel. ARTIFACT = the checklist + `git diff <default>...HEAD` + the proposal's `## Success criteria`.
   - **Verifier:** one dispatch — no fold-audit re-check, no upward move (`references/decision-protocol.md`, *The Verifier gate is asymmetric*). On `accept`, advance to Phase 3. On a `revise`/`reject` naming an unmet criterion, treat it as a **success-criteria divergence** — auto-trigger Phase 2.5 (replan) to clarify the criteria, then resume implementation.
   - **Panel:** on `3/3 accept`, advance. On `≤1/3 accept`, treat it as a success-criteria divergence (Phase 2.5), not a regular consensus failure — skip the standard revise-and-revote. On `2/3 accept`, proceed but log dissent concerns to scratchpad for the review phase to scrutinize.
   - This gate is **never** skipped.

## Phase 2.5 — Replan (inline, if triggered)

Mirrors `minerva:replan`'s protocol; acceptance is always a panel (panel floor).

1. Already inside the worktree. Read `proposal.md`, prior `replan.md` entries, current `scratchpad.md`.

2. **Frame the replan** around the three pieces: Original plan / What changed / New plan. The main LLM drafts all three.

3. **New-plan-acceptance panel.** ARTIFACT = the full replan entry draft + the proposal's current `## Approach` for comparison; CONTEXT = the divergence that triggered it. On `3/3 accept`, write. On revision-round failure, escalate.

4. **Write.** Append the entry to `replan.md` per `minerva:replan`'s "On approval — file write" section. If the new plan changes success criteria, also edit `proposal.md`'s `## Success criteria` section.

5. Return control to Phase 2 (or Phase 3 if replan was triggered from review).

## Phase 3 — Review (inline)

Replaces the user-interactive triage in `minerva:review`, whose protocol is read in `--auto=propose-ship-auto` mode. Diff resolution and finding generation use the optional OPEN-PR review skill when installed, otherwise the host adapter's independent diff reviewer; triage is solo with a reviewer ceiling.

1. **Read context.** `proposal.md`, all `replan.md` entries, current `scratchpad.md` (including prior `## Review triage YYYY-MM-DD` blocks), `followups.md` **plus** open `minerva:followup` issues (`gh issue list --label "minerva:followup" --state open`), and relevant `.minerva/knowledge/` entries.

2. **Diff resolution.** Same as `minerva:review`'s "Diff resolution" section.

3. **Generate findings.** Two passes:
   - **Minerva audit** (inline): spec fidelity (does the diff achieve `## Goal`, `## Approach`, `## Success criteria`?) + knowledge compliance (does the diff violate any documented pattern/constraint/decision?).
   - **Code review**: use `code-review:code-review` only for an OPEN PR when installed. Otherwise, use the independent PR/local diff review per `minerva:review`'s "Code review invocation" section and host adapter.

4. **Triage (solo; reviewer ceiling).** The main model triages the full numbered finding set in one decision. ARTIFACT = the findings list + proposed dispositions (default by the deferral bar in `skills/promote/references/deferral-bar.md`, not by severity alone: a finding with a writable failure scenario → FIX, even outside the diff, unless too large to absorb — then SUGGEST (an issue candidate if `critical`/`high`, otherwise a standing fact); documentation for behavior this diff touched → always FIX, never deferred; a standing fact about the system → SUGGEST, phrased as what *is* so promote can route it to a `reference` entry; everything else → IGNORE). Solo unless the panel predicate holds — in practice, a finding with two defensible dispositions and none dominant — in which case one Skeptic reviews the set (reviewer ceiling: an upward move from here goes to the user, never a panel). The code-review pass already supplied an independent finding set.

5. **Replan-vs-FIX check.** If any FIX finding reveals a load-bearing divergence (per `minerva:review`'s "Load-bearing divergence" heuristic), the main model makes the replan-vs-FIX call and convenes a **replan-vs-FIX panel** (panel floor): ARTIFACT = the finding + the call; CONTEXT = the proposal's `## Approach`. On `2/3 accept for replan`, persist current triage state to scratchpad per `minerva:review`'s "Triage persistence" section, then trigger [Phase 2.5](#phase-25--replan-inline-if-triggered). After replan completes, return to step 4 (re-run triage).

6. **Apply dispositions.** Per `minerva:review`'s "On approval — file writes" section. FIX items get edited directly; SUGGEST items append to scratchpad under `## Review finding YYYY-MM-DD`; IGNORE items optional.

7. Continue to Phase 4.

## Phase 4 — Promote (inline)

Replaces the user-interactive partition in `minerva:promote` Mode A, whose protocol is read in `--auto=propose-ship-auto` mode.

1. **Already inside the worktree.** Read `proposal.md`, `scratchpad.md`, `replan.md` if present.

2. **Idempotency check.** If `work_status.unit_state(<unit-dir>)["promoted"]` is true, report "already promoted" and continue to Phase 5. Use that predicate, never a match against the marker string — the marker has nine spellings in one 51-unit corpus and a string match reads 16 of them as un-promoted, re-running a mutating pass.

3. **Partition draft.** The main LLM proposes a four-way partition per `minerva:promote`'s "Mode A — no argument (end-of-work full pass)": PROMOTE / MERGE INTO PROPOSAL / DISCARD / TODO. Skip entries already marked `→ promoted to ...`.

4. **Partition (solo; reviewer ceiling).** ARTIFACT = the full partition with one-line justifications per entry. Solo unless an entry has two defensible buckets and none dominant, then one Skeptic reviews it; an upward move from here goes to the user.

5. **TODO disposition (solo; reviewer ceiling).** Only if any entries landed in the TODO bucket. **Read the deferral bar in `skills/promote/references/deferral-bar.md` first** and pre-sort against it; a reviewer, if the ceiling is reached, reviews the sorting, not each item from scratch. Artifact = each TODO with its proposed outlet — fix now (a defect small enough to absorb; fix it, then return to Phase 3 so the fix is reviewed before promote re-runs), a GitHub issue (all three conditions: writable failure scenario, `critical`/`high` priority per `skills/promote/references/github-issues.md`, too large to absorb; carrying that `**Failure scenario**:` line, or `followups.md` where the repo cannot host issues; more than one per unit needs a logged justification), a `.minerva/knowledge/` `reference` entry (a standing fact, or a defect that is neither urgent nor absorbable), or discard. Documentation for behavior this diff touched is not on the list — it is done as part of the work. There is no `medium` or `low` tier.

6. **Apply writes.** Per `minerva:promote`'s "Mode A — no argument (end-of-work full pass)": write PROMOTE items as `.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md` using the knowledge entry template; rewrite `proposal.md`'s `## Approach` (and Status to `Shipped (YYYY-MM-DD)`); apply TODO dispositions; archive the scratchpad and write the one-line promote marker.

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

There is no gate. The `promote → ship` confirmation that `minerva:propose-ship` requires is replaced by silent advancement. The completion gate, review triage and promote dispositions have already been adjudicated at their tiers; the run trusts those decisions and proceeds.

If the global escalation counter has reached 3 by this point, halt instead of shipping (see the failure-modes caps in `references/governance.md`).

Otherwise continue to Phase 6.

## Phase 6 — Ship (delegated)

Invoke `minerva:ship <date-slug> --auto=propose-ship-auto` via the skill loader. Before invoking, lead with this auto-mode instruction:

> "You are running inside `minerva:propose-ship-auto`. When `minerva:ship` reaches Hard gate #1 (commit message) and Hard gate #2 (PR title + body), accept the drafted content without prompting the user. All other `minerva:ship` behavior — pre-flight, branch creation, push, PR creation, CI watch loop, auto-merge — is unchanged."

These two gates are operational and take no tier — the main LLM's draft from `proposal.md` is good enough by definition.

If `minerva:ship`'s CI auto-fix classifier marks a failure as `other` or bails on a non-trivial test/build, **do not tier the bail** — escalate to the user with the failing job log. This is a hard escalation trigger.

When `minerva:ship` returns **in this same turn**, continue to Phase 7. If instead it ended the
turn on its CI watch, it re-enters this gate itself via `--cleanup-only` when checks settle — exactly
one of the two paths runs, never both.

## Phase 7 — Cleanup gate

**Runtime continuation.** Read the saved checkpoint before this gate; preserve
caller, escalation/decision/reviewer counters, cleanup retries and its absolute
deadline. Save phase `cleanup` before waiting. The scheduled resume operation is
conditional on a real re-entry capability: without it, checkpoint and report
**pending — manual resume required**, with the exact host-correct
`--cleanup-only <date-slug> --retry=N` prompt. Count each retry before waiting;
cap at 12 or the original one-hour deadline, whichever comes first. Never reset
these limits when switching sessions. Reconciliation can remain pending after
merge; preserve phase `reconciliation` and name every uncatalogued entry.

Identical to `minerva:propose-ship`'s Phase 7. After `minerva:ship` returns:

1. `gh pr view <branch> --json state,mergedAt 2>/dev/null`. On resume, use the
   checkpoint's work PR number if its branch has already been pruned.
2. **`MERGED`** → invoke `minerva:cleanup <date-slug> --yes` via the skill loader. Besides removing the worktree, cleanup reconciles the knowledge wiki on the default branch — cataloguing this unit's entries from their `**Summary**` fields, writing their reciprocal links, and refreshing `overview.md` if warranted — and opens a single auto-merging PR for it. Surface that PR (and any reconciliation refusals) in the final report. Report and exit.
3. **`OPEN`, auto-merge enabled** → when a scheduler supports re-entry, use the scheduled resume operation with `prompt: minerva:propose-ship-auto --cleanup-only <date-slug> --retry=N`, `delaySeconds: 300`. Unlike ship's CI watch, this delay is deliberately a constant: what is being waited on is auto-merge landing, which can queue behind a required review or a merge queue rather than tracking CI duration, and 300 × the retry cap below is what makes that cap a ~1 hour wall-clock bound. Cap retries at 12. On exhaustion, surface manual instructions.
4. **`OPEN`, auto-merge declined** → surface manual cleanup instructions; do not schedule wake-up.
5. **`CLOSED` (not merged)** → leave worktree in place; surface manual cleanup instructions.
6. **No PR found** → exit silently (ship must have bailed before opening one — already reported above).
7. **Phased unit — not done yet.** Before reporting on a `MERGED` phase, re-derive `phase_progress()` (`scripts/work_status.py`). If `complete` is false, **loop back to Phase 6 and ship `next_branch`**, cut from the freshly fetched default branch — do not report and exit. Promote Mode A belongs before the FINAL phase's ship, not phase 1's; the review phase re-runs against each phase's own diff. A run that exits here silently is a unit that stalled while reporting success. Full loop rules: `skills/propose/references/phasing.md`. No-op for unphased units.

When re-entered via `--cleanup-only`, skip phases 1–6 and re-run this phase directly.

