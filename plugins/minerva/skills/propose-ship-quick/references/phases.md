# Phase protocols — full inline walkthroughs

Read each phase's section before executing that phase. These mirror `minerva:propose-ship-auto`'s phases 1-to-1; the only change is that every panel-dispatch / skip-predicate / revision-round step is replaced by **the main model decides per `references/solo-decision-protocol.md`; escalate on genuine uncertainty**. No phase is removed.

## Phase 1 — Propose (inline)

Replaces the user-interactive intake in `minerva:propose`.

1. **Assemble context.** Read: the inline seed, current chat history, `CLAUDE.md`/`AGENTS.md`, `.minerva/knowledge/` entries (at minimum `Type: pattern` and `Type: constraint`), the 2-3 most recent `.minerva/work/NNN-*/proposal.md` files for tone/conventions, and any adjacent `followups.md`.

2. **Design synthesis.** The main model drafts a complete proposal (Goal / Why / Approach / Success criteria / Open Questions) along with the 2-3 candidate approaches it considered. Context-grounded inference, not user Q&A. Keep it in conversation; write no file yet.

3. **Scope check.** The main model decides: single work unit, or decompose? Escalate only if genuinely ambiguous (per the escalation predicate). If the decision is "decompose", abort the quick run cleanly: "scope check resolved to decomposition — re-run with one sub-unit at a time."

4. **Approach selection.** The main model picks among its candidates; if no option is dominant, escalate (offer the candidates via `AskUserQuestion`). The chosen approach replaces the draft's `## Approach`.

5. **Whole-proposal soundness.** The main model reviews the full draft for internal consistency and soundness. Escalate if a public-interface or cross-cutting-contract aspect is one it cannot confidently get right alone.

6. **Worktree + branch creation.** Identical to `minerva:propose`'s "On approval — worktree setup" steps 1–7: derive slug, check duplicates, compute NNN across local work / local branches / remote branches; resolve default branch; pre-flight gitignore check on `.minerva/worktrees/` (abort to user if missing); `git worktree add -b <NNN-slug> .minerva/worktrees/<NNN-slug> <default-branch>`; then address the worktree by prefix (**no `EnterWorktree`** — it does not reliably enter `.minerva/worktrees/`): prefix file paths with `.minerva/worktrees/<NNN-slug>/` and run git as `git -C .minerva/worktrees/<NNN-slug> …`.

7. **File writes (inside the worktree).** Per `minerva:propose` steps 8–9, 11: create `.minerva/work/<NNN-slug>/`; write `proposal.md` and the header-only `scratchpad.md`; append the initial `## Quick decisions YYYY-MM-DD` block with the decisions from steps 3–5; `git add` + commit `chore: initialize <NNN-slug> work unit`.

8. **Self-review.** Re-read `proposal.md` with fresh eyes per `minerva:propose` step 10 (placeholders, internal consistency, ambiguity, scope). Fix inline.

9. Continue to Phase 2.

## Phase 2 — Work (inline)

Replaces the user-interactive setup and completion signal in `minerva:work`. Implementation itself is unchanged — the main model writes code as normal, maintaining `scratchpad.md` per `minerva:work`'s implementation protocol.

1. **Setup.** Already inside the worktree. Read `proposal.md` and any `replan.md`. Open questions that survived Phase 1 surface in the final report.
2. **Implementation loop.** Implement per `minerva:work`'s "Implementation protocol". No upper bound on implementation time, but the [scope-fit escape](solo-decision-protocol.md) applies — if the change proves large, escalate.
3. **Divergence detection.** When a load-bearing divergence is suspected, the main model **confirms** whether it warrants a replan (Phase 2.5). Escalate if unsure. A routine choice continues without a replan.
4. **Completion verification.** When every `## Success criteria` item appears met, build the checklist (criterion → evidence → yes/no) and honestly verify it against `git diff <default>...HEAD`. If a criterion is not cleanly met, auto-trigger Phase 2.5 (replan) to clarify, then resume. This self-check is **never** skipped.

## Phase 2.5 — Replan (inline, if triggered)

Mirrors `minerva:replan` with main-model acceptance.

1. Inside the worktree. Read `proposal.md`, prior `replan.md`, current `scratchpad.md`.
2. **Frame the replan** around Original plan / What changed / New plan. The main model drafts all three.
3. **New-plan acceptance.** The main model re-reads the drafted entry against the proposal's current `## Approach` and accepts it; escalate if unsure. This self-check is **never** skipped.
4. **Write.** Append the entry to `replan.md` per `minerva:replan`'s "On approval — file write". If success criteria change, also edit `proposal.md`'s `## Success criteria`.
5. Return to Phase 2 (or Phase 3 if triggered from review).

## Phase 3 — Review (inline)

Replaces the user-interactive triage in `minerva:review`.

1. **Read context.** `proposal.md`, all `replan.md`, current `scratchpad.md` (including prior `## Review triage` blocks), `followups.md`, relevant `.minerva/knowledge/`.
2. **Diff resolution.** Same as `minerva:review`'s "Diff resolution".
3. **Generate findings.** Two passes — **minerva audit** (spec fidelity + knowledge compliance) and **code review** (if a PR exists, invoke `code-review:code-review` via the `Skill` tool; otherwise the inline structured review per `minerva:review`).
4. **Triage.** The main model triages the full numbered finding set (default: high → FIX, medium → SUGGEST, low → IGNORE). Escalate if a finding's disposition is genuinely contested.
5. **Replan-vs-FIX.** If a FIX finding reveals a load-bearing divergence (per `minerva:review`'s heuristic), the main model decides replan vs. fix-in-place; escalate if unsure. On replan, persist triage state per `minerva:review`'s "Triage persistence", trigger Phase 2.5, then re-run step 4.
6. **Apply dispositions.** Per `minerva:review`'s "On approval — file writes": FIX edited directly; SUGGEST appended to scratchpad under `## Review finding YYYY-MM-DD`; IGNORE optional.
7. Continue to Phase 4.

## Phase 4 — Promote (inline)

Replaces the user-interactive partition in `minerva:promote` Mode A.

1. Inside the worktree. Read `proposal.md`, `scratchpad.md`, `replan.md` if present.
2. **Idempotency check.** If `scratchpad.md` is the post-promote marker, report "already promoted" and continue to Phase 4.5 (synthesis self-gates and no-ops if current).
3. **Partition.** The main model proposes the four-way partition per `minerva:promote` Mode A step 3: PROMOTE / MERGE INTO PROPOSAL / DISCARD / TODO. Skip entries already `→ promoted to ...`. Escalate if an entry's bucket is genuinely ambiguous.
4. **TODO disposition.** For each TODO: followups.md / seed new proposal / discard. The main model decides; escalate if unsure.
5. **Apply writes.** Per `minerva:promote` Mode A step 7: write PROMOTE items as `.minerva/knowledge/NNN-<type>-<slug>.md`; rewrite `proposal.md`'s `## Approach` and set Status to `Shipped (YYYY-MM-DD)`; apply TODO dispositions; archive the scratchpad and write the one-line promote marker.
6. **TODO seed gate (if any).** Do **not** auto-invoke `minerva:propose` in the same run — surface "seed new proposal" TODOs in the final report as suggested follow-ups.
7. Continue to Phase 4.5.

## Phase 4.5 — Synthesis (delegated, self-gating)

Promote just added knowledge entries, so there is now un-synthesized scope. **Always invoke `minerva:synthesize`** via the `Skill` tool, leading with this auto-mode instruction:

> "You are running inside `minerva:propose-ship-quick`. When `minerva:synthesize` reaches its Step-4 write-confirmation gate, accept the drafted `overview.md` without prompting. Its Step-2 'decide IF to (re)synthesize' self-gate is **unchanged** — if there is too little new scope, it correctly no-ops and writes nothing."

This is **delegation, not a decision** — the "decide IF" judgment lives inside `minerva:synthesize`. **Log the outcome** with one line under `## Quick decisions YYYY-MM-DD`, `[synthesis]` prefix (wrote → `refreshed overview.md (watermark NNN→MMM; K entries)`; no-op → `no-op (below threshold / current)`). Phase 4 has already archived the scratchpad, so this line goes to `archive/scratchpad.md` — the live `scratchpad.md` is by then the one-line post-promote marker that downstream skills rely on being empty (knowledge 003), and must stay that way. If it wrote, Phase 6 must **name `.minerva/knowledge/overview.md` among the paths to stage** and note "overview.md refreshed (advisory navigation)" in the PR body. Continue to Phase 5.

## Phase 5 — Ship gate

No gate: silent advancement. If the global escalation counter has reached 3, halt instead of shipping (see `references/governance.md`).

## Phase 6 — Ship (delegated)

Invoke `minerva:ship` via the `Skill` tool, leading with:

> "You are running inside `minerva:propose-ship-quick`. When `minerva:ship` reaches Hard gate #1 (commit message) and Hard gate #2 (PR title + body), accept the drafted content without prompting the user. All other `minerva:ship` behavior — pre-flight, branch creation, push, PR creation, CI watch loop, auto-merge — is unchanged."

These two gates are operational tier — the main model's draft from `proposal.md` is good enough by definition. If `minerva:ship`'s CI auto-fix classifier marks a failure `other` or bails on a non-trivial test/build, **escalate to the user with the failing job log** — a hardcoded trigger, never silently decided.

## Phase 7 — Cleanup gate

Identical to `minerva:propose-ship`'s Phase 7. After `minerva:ship` returns:

1. `gh pr view <branch> --json state,mergedAt 2>/dev/null`.
2. **`MERGED`** → invoke `minerva:cleanup` via the `Skill` tool with args `<NNN-slug> --yes`. Report and exit.
3. **`OPEN`, auto-merge enabled** → `ScheduleWakeup` with `prompt: minerva:propose-ship-quick --cleanup-only <NNN-slug> --retry=N`, sizing `delaySeconds` as `minerva:ship`'s watch policy does — roughly the expected remaining CI time for this repo (`gh run list`), clamped `[60, 3600]`; 600 when there is no history. Auto-merge lands within seconds of checks going green, so the wait *is* the CI wait; a fixed constant is wrong at both ends of the range. Cap retries at 12; on exhaustion, surface manual instructions.
4. **`OPEN`, auto-merge declined** → surface manual cleanup instructions; do not schedule.
5. **`CLOSED` (not merged)** → leave the worktree; surface manual instructions.
6. **No PR found** → exit silently (ship bailed before opening one — already reported).

When re-entered via `--cleanup-only`, skip phases 1–6 and re-run this phase directly.
