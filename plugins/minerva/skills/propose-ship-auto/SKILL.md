---
name: propose-ship-auto
description: Runs the full minerva lifecycle end-to-end with no scheduled human gates — the one autonomous orchestrator, for any size of change ("do the whole thing without asking", "just ship this", "ship this with a second opinion", "auto propose and ship"). Same lifecycle as `minerva:propose-ship` (propose - work - review - promote - ship - cleanup, where `minerva:cleanup` reconciles the knowledge wiki), but each decision gets the adjudication tier it earns — the main model alone when provably small, one fresh-context reviewer by default, a 3-agent `minerva:round-table` panel when ambiguous, high-blast-radius, interface-changing or in tension with knowledge — and moves up a tier instead of stopping. The user is asked only when a panel cannot agree or a hardcoded trigger fires. Use for autonomous changes, or when the user invokes `minerva:propose-ship-auto`.
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Run the full minerva lifecycle end-to-end with **per-decision adjudication** in place of human gates. This skill is a **hybrid orchestrator** — it delegates to `minerva:ship` and `minerva:cleanup` directly (those phases have no strategic gates) but inlines the propose / work / review / promote / replan phases so it can adjudicate them itself.

The mechanism: at each strategic or tactical decision point the main model drafts the decision, then picks its **tier** — **solo** (decide alone, only when a strict conjunctive predicate proves the decision small), **reviewer** (one fresh-context Skeptic, or a Verifier at completion, arbitrated inline; a fold gets one fold-audit re-check), or **panel** (a Proponent/Skeptic/Arbiter `minerva:round-table` vote). Uncertainty moves a decision **up** a tier within the run; there is no whole-run sizing and no recommendation to switch orchestrators. Operational decisions (commit messages, PR bodies, file paths) take no tier.

## Usage

- `minerva:propose-ship-auto "add rate limiting"` — start a new run with the inline description as the strategic seed.
- `minerva:propose-ship-auto` — start with current-session chat context as the seed (only sensible if the chat already discussed what to build).
- `minerva:propose-ship-auto --cleanup-only <date-slug> --retry=N` — internal re-entry from the cleanup-gate wake-up loop. Skips phases 1–6 and re-runs Phase 7.

## Pre-flight: in-flight work collision

Identical to `minerva:propose-ship`'s pre-flight section. This check is **not** panel-decided — wrong call here destroys real work, so escalation to the user is hardcoded.

**Read `skills/propose/references/in-flight-check.md` and run it.** It reads four evidence sources — local work units (via the `in_flight` predicate, never a string match), local and remote branches, open PRs, and available live peer sessions — each failing soft, so a repo with no remote, no tracker and no siblings passes through silently. It is **detection, not a lock**: `git worktree add -b` serializes only sessions choosing the *same slug*, so a clean result means no evidence was found, not that nobody else is working the goal.

When a peer session messages you, read `skills/propose/references/cross-session.md`: inform, never delegate.

A collision is a hardcoded user question operation (resume that work / start fresh anyway / abandon this run) and **increments the global escalation counter**.

Only proceed after the user confirms. This is the single mandatory — and **only permitted** — pre-run user interaction (see No ceremony ratification in `references/decision-protocol.md`).

## Decision protocol

The full policy — **tier selection** (hardcoded → panel predicate → solo predicate → reviewer), per-row **floors and ceilings**, **upward moves**, the **reviewer tier** (Skeptic, fold-audit re-check, the asymmetric Verifier), delegation of the **panel tier** to `minerva:round-table`, **No ceremony ratification**, **parked dispatches** and **per-decision logging** — lives in `references/decision-protocol.md`. **Read it once, in full, before this run's first strategic/tactical decision point**; its rules then apply to every decision.

Binding floor, even before the reference is read:

- **Decide first, then route.** Draft the decision, then choose its tier. Both predicates fail closed: doubt about a panel clause convenes the panel; doubt about a solo clause denies solo.
- **Never below the floor:** divergence confirmation, new-plan acceptance and replan-vs-FIX are always panels; completion verification is at least a Verifier. Triage, promote partition and TODO disposition never convene a panel.
- **Up, never sideways.** An unadjudicable critique or a failed fold-audit moves the decision to a panel; a panel that fails quorum twice goes to the user. No step recommends switching to another orchestrator.
- Panel mechanics are delegated to `minerva:round-table` in caller mode; quorums come from the Decision taxonomy in `references/decision-protocol.md`, never round-table's standalone default.
- Every decision logs one line to `scratchpad.md` under `## Decisions YYYY-MM-DD`, naming its tier and why.

## Phases

Execute the phases in order. The full inline protocols — per-gate artifacts, tier handling, escalation aftermath and file-write steps — live in `references/phases.md`. **Before executing each phase, read that phase's section there**; the map below locates the work, it is not the protocol:

1. **Propose (inline)** — assemble context → design synthesis → scope check → approach selection → whole-proposal soundness (each tiered) → worktree + branch + file writes per `minerva:propose` → self-review. No post-write user gate.
2. **Work (inline)** — implement per `minerva:work`'s protocol; divergence confirmation (panel) when a load-bearing divergence is suspected; completion verification (Verifier floor) on the success-criteria checklist + diff.
   - **2.5 Replan (inline, if triggered)** — draft Original plan / What changed / New plan; new-plan acceptance (panel); append to `replan.md`.
3. **Review (inline)** — minerva audit + code review (optional PR skill or independent diff reviewer); triage (solo, reviewer ceiling); replan-vs-FIX (panel) if a load-bearing finding surfaces.
4. **Promote (inline)** — partition and TODO disposition (solo, reviewer ceiling); apply writes per `minerva:promote` Mode A; archive scratchpad.
5. **Ship gate** — no gate: silent advancement, except halt if the global escalation counter has reached 3.
6. **Ship (delegated)** — invoke `minerva:ship` via the skill loader with its auto-mode instruction (auto-accept hard gates #1 commit message and #2 PR title/body; everything else unchanged). CI auto-fix bails classified `other` are escalated to the user — never tiered.
7. **Cleanup gate** — poll PR state via `gh pr view`; on `MERGED` invoke `minerva:cleanup` via the skill loader with args `<date-slug> --yes` (which also reconciles the knowledge wiki and opens its auto-merging PR); on `OPEN` with auto-merge, use scheduled re-entry when available or checkpoint and report pending with a manual resume prompt (`--cleanup-only <date-slug> --retry=N`, cap 12); otherwise surface manual instructions.

## Failure modes, escalation, budget caps

Binding caps: a Skeptic gate spends at most **two** reviewer dispatches (review + one fold-audit re-check); a panel spends **one initial vote + one revision vote** (6 subagent dispatches max); **propose-phase abort** when 2 of its 3 decisions reach the user; the **global escalation counter** halts the run at **3**. Hard escalation triggers that skip tier selection entirely: in-flight collision, open-issue match, worktree-creation failure, ship-phase failures (`other` classification, push rejection, `gh` auth failure), counter at 3. The full trigger list, final-report-on-bail format and observability requirements live in `references/governance.md` — read it at the first escalation or before reporting any bail.

## Out of scope

Never modify any existing minerva skill at run time (this skill orchestrates by *invocation only*); never size the whole run up front; never recommend switching orchestrators mid-run; never auto-cascade into new work units; never cap implementation time; review/promote ordering is fixed; quorums are not configurable. Rationale and detail: `references/governance.md`.
