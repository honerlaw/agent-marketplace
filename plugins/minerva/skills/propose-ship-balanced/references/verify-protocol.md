# Verify protocol — full policy

Read once, in full, before the run's first strategic/tactical decision point. Its rules then apply to every decision that follows.

This is `propose-ship-balanced`'s analog of `propose-ship-quick`'s solo-decision protocol and `propose-ship-auto`'s panel protocol. The default is **the main model decides** (exactly as `propose-ship-quick`), with **one** addition: at a fixed set of high-signal gates the main model dispatches a **single fresh-context advisory reviewer** and arbitrates its critique inline — and when it **folds** that critique, it sends **one** more single reviewer to audit the fold (the [fold-audit re-check](#re-check-after-a-fold)), never a third. It never convenes a 3-agent `minerva:round-table` panel — that is `propose-ship-auto`'s mechanism.

## Default — the main model decides

At each strategic/tactical decision point (see the [Decision taxonomy](#decision-taxonomy)), the main model **decides directly**, fast, grounded in the run's context: the proposal, the diff, `CLAUDE.md`/`AGENTS.md`, and any `.minerva/knowledge/` entries already cited this session. Operational decisions (commit messages, PR bodies, file paths) are executed without any decision ceremony, exactly as in `propose-ship-auto`/`propose-ship-quick`. Solo gates run to completion with the main model deciding and the user never touched.

## The reviewer gates

A **single reviewer** fires only at the fixed gates below — never at the solo gates. This is a per-decision-**type** policy (which *kinds* of decision warrant an independent look), not an up-front whole-run sizing classifier; that distinction preserves the gate-per-decision, fail-closed design rule.

**Fire on every run:** scope check, approach selection, whole-proposal soundness, completion-verification.

**Fire only when that decision point is reached** (rare): mid-work divergence confirmation, new-plan acceptance (replan), replan-vs-FIX.

**Always solo (main model decides, quick-style):** review triage, promote partition, TODO disposition.

The gate selection is evidence-grounded in past run logs: independent scrutiny is spent only where it demonstrably changes outcomes (approach selection), independently reproduces claims (completion verification), or averts rare-but-expensive misses (scope check). Whole-proposal soundness joined the list on the same evidence: across 26 `propose-ship-auto` runs, 13 of its 27 panel calls went to a revision round — second only to approach selection (17 of 25), which balanced already reviews, and far ahead of scope (7 of 22) and completion (0 of 18) — including HIGH gaps a solo read had passed. If a solo gate is later shown to miss real defects — or a reviewer gate never changes an outcome — re-measure with `plugins/minerva/scripts/decision_telemetry.py` and revisit the taxonomy via `minerva:replan`.

## Single-reviewer mechanism

At a reviewer gate:

1. **Decide first.** The main model makes its decision exactly as it would solo, and writes it down (the proposed scope cut / chosen approach / completion checklist). Decide-first-then-review is intentional: a fresh-context reviewer that reads the *committed* decision carries no confirmation bias from the main model's reasoning, and this is cheaper than a parallel re-derivation (no second agent to generate the decision).
2. **Dispatch one reviewer.** Spawn **one** subagent via the `Agent` tool, fresh context, `subagent_type: general-purpose`, `model: sonnet`, `run_in_background: false`. The dispatch is synchronous because the gate arbitrates the critique **inline, in this same turn**: a backgrounded dispatch returns only a handle, which parks the run instead of deciding the gate. The reviewer is a **Skeptic** at scope / approach / divergence / replan-acceptance / replan-vs-FIX, and a **Verifier** at completion-verification. Pass it the gate's ARTIFACT + CONTEXT per `references/phases.md`. The model is pinned to `sonnet` regardless of the main session's tier: an independent critique/verification is a structured-judgment task Sonnet handles well (the same cost-determinism call made for round-table's panelists), and pinning it keeps cost deterministic.
3. **Arbitrate inline.** The main model reads the reviewer's critique and acts as the Arbiter. It folds load-bearing points, proceeds past non-load-bearing ones, or escalates (see below). **At most two dispatches per gate**: the review, plus the re-check in step 4 when — and only when — step 3 folded. Never a third, and never a panel vote.
4. **Re-check after a fold (Skeptic gates only).** See [Re-check after a fold](#re-check-after-a-fold). Not at the Verifier gate: a completion `revise` already loops through Phase 2.5 → new-plan acceptance → a second Verifier pass, which is its re-check.

### What "load-bearing critique" means

The main model that made the decision is also the one judging the critique, so the threshold is defined behaviorally to keep that from collapsing into self-confirmation. A critique is **load-bearing** iff it identifies at least one of:

- (a) a violation of a documented `.minerva/knowledge/` constraint, or of a stated success criterion;
- (b) a missed dependency or integration risk the decision did not account for;
- (c) an overlooked scope surface or file;
- (d) **[approach/scope gates]** a viable alternative that is **strictly dominant** on the stated criteria;
- (e) **[completion gate]** a success criterion that is unmet or only partially met.

A critique is **not** load-bearing if it is stylistic disagreement, or a re-weighting of tradeoffs the decision already considered, with no new information.

- **Load-bearing → fold.** Revise the decision to address it (re-cut scope, switch/adjust approach, finish the unmet criterion), log `[reviewed — folded]` with what was folded.
- **Not load-bearing → proceed.** Log `[reviewed — clean]` (record any noted-but-dismissed concern so a later `minerva:review`/`minerva:promote` pass can audit the call).
- **Anti-circularity escape.** If folding the critique would require a **materially different decision** *and* the main model **cannot confidently tell** whether the reviewer is right, that is genuine ambiguity → **escalate to the user** (per the [escalation predicate](#escalation-predicate)). The main model must not self-confirm its way past a critique it cannot honestly adjudicate.

### Re-check after a fold

Thirteen balanced runs logged 30 `[reviewed — folded]` lines against 5 `[reviewed — clean]` and **zero** anti-circularity escalations: the main model folds almost every critique, and nothing independently checked the fold. The re-check closes that gap with a second **single** reviewer — not a panel, not a Proponent or Arbiter, not a vote.

**Trigger.** Step 3 logged `[reviewed — folded]` at a **Skeptic** gate (scope check, approach selection, whole-proposal soundness, mid-work divergence, new-plan acceptance, replan-vs-FIX). A `[reviewed — clean]` outcome dispatches nothing more; the Verifier gate is excluded (see step 4).

**Dispatch.** Write the revised decision down first. Then dispatch **one** more fresh-context agent via the `Agent` tool (`subagent_type: general-purpose`, `model: sonnet`, `run_in_background: false`) carrying the [Fold-audit brief](#fold-audit-brief). ARTIFACT = the original decision as first written, the Skeptic's critique **verbatim**, and the revised decision; CONTEXT = exactly the CONTEXT the gate gave the Skeptic. The re-check reviewer must not be the same agent and must not see the main model's arbitration reasoning — only the three artifacts.

**Arbitrating the re-check — strict.** The re-check exists to take the second look out of the main model's hands, so its arbitration has no discretionary branch:

- `accept` → proceed. Log `[rechecked — clean]`.
- `partially` on an item whose residual is **not** load-bearing (falls outside categories (a)–(e) above) → fold the residual, proceed. Log `[rechecked — residual folded]` naming the residual.
- Anything else — a load-bearing item marked `partially`, `not addressed` or `regressed`, or a new load-bearing concern under `## New concerns` — → **escalate to the user** via the anti-circularity escape. There is **no** self-confirmation path here: the main model may not decide the re-check is mistaken and proceed, and there is **no third dispatch**. Log `[rechecked — escalated]` with the question and the user's answer on that same line (no separate `[escalated to user]` line — escalations are counted once). The escalation increments the global escalation counter like every other.

A rejected alternative, so it is not re-invented at runtime: letting the main model proceed past a re-check `revise` on cited "mechanical" evidence. What counts as mechanical is itself a judgment, and the re-check's whole value is that the second look is not the main model's.

### Verifier brief (completion gate)

The completion reviewer is a **Verifier**, not a Skeptic-of-prose. Dispatch it with:

- **Inputs (ARTIFACT):** the success-criteria checklist (each criterion + the main model's *claimed* evidence + its yes/no), `git diff <default-branch>...HEAD`, and the proposal's `## Success criteria` section.
- **Task:** for **each** criterion, independently determine whether it is honestly met. Do **not** trust the claimed evidence — reproduce it: read the named files in the worktree; where a criterion names a test or an anchor, run a **read-only** command or `grep` to confirm the diff actually contains / passes it. Actively try to **falsify** "done" — hunt for a criterion with no corresponding diff, a partial implementation, or a claim unsupported by the code.
- **Output format:** per criterion, `{met: yes | no | unsure, evidence-or-gap: <one line>}`, then a final verdict `accept` (all honestly met) / `revise` (gaps to close) / `reject`.

A `revise`/`reject` verdict that names an unmet criterion is load-bearing category (e); the main model treats it as a success-criteria divergence and triggers Phase 2.5 (replan) to close the gap, rather than shipping.

### Fold-audit brief

The re-check brief. It audits a **fold**, not the decision — a reviewer that re-litigates the decision produces new concerns indistinguishable from the first review and invites a third dispatch.

```
YOUR ROLE: You are an independent reviewer auditing a REVISION. The ARTIFACT
above has three parts: (1) the ORIGINAL decision, (2) a Skeptic's CRITIQUE of
it, numbered, and (3) the REVISED decision written in response. You did not
write any of them and you have not seen the reasoning behind the revision.

For EACH numbered concern in the CRITIQUE, decide whether the REVISED decision
addressed it. Read the revision; do not take its word for it. Then, and only
then, look for load-bearing problems the REVISION itself introduced — a newly
violated constraint or criterion, a newly missed dependency, a scope surface the
revision dropped, a regression against the original. Do not re-argue the
original decision and do not restyle it.

Output format:
## Disposition
<one line per critique item: `N. addressed | partially | not addressed | regressed — <evidence>`>
## New concerns
<numbered, each with severity high/medium/low; only concerns INTRODUCED by the revision; "none" is a valid answer>
## Verdict
<accept | revise>: <one-sentence reason>
```

### Skeptic brief

The Skeptic brief (scope / approach / divergence / replan gates), adapted from `plugins/minerva/skills/round-table/references/briefs.md`:

```
YOUR ROLE: You are an independent Skeptic reviewing the decision in the ARTIFACT
above. You have fresh context and did not make this decision. Surface every
load-bearing risk, ambiguity, divergence from convention, missing piece, or
unstated assumption — especially an overlooked alternative, a violated
constraint, or a scope/dependency the decision missed. Be specific; cite the
part of the ARTIFACT you are critiquing.

Render a final verdict of accept / revise / reject. Your job is to find
problems, but the verdict must reflect whether the problems are actually
load-bearing — nitpicks that do not block soundness should be 'accept' with
the concerns listed.

Output format:
## Critique
<numbered concerns, each with severity high/medium/low>
## Verdict
<accept | revise | reject>: <one-sentence reason>
```

## Escalation predicate

Before committing any decision — solo or post-review — the main model applies an explicit test to *that specific decision*. It is the same fail-closed predicate `propose-ship-quick` uses. **Decide directly only if you are confident on all of these. Escalate to the user if any holds — or if you are unsure whether it holds:**

- **genuine ambiguity** — after honestly enumerating the options, none is dominant (a coin-flip between materially different paths is the user's call). A reviewer critique that is load-bearing and cannot be confidently adjudicated is genuine ambiguity; non-load-bearing uncertainty is logged with the concern and does not escalate.
- **high blast-radius / irreversible** — hard to walk back, or a broad rather than bounded surface;
- **unfamiliar public interface or cross-cutting contract** — introduces/changes a public interface, API, or cross-cutting contract you cannot confidently get right alone;
- **knowledge conflict** — would violate or sits in tension with a documented `.minerva/knowledge/` constraint.

**Fails closed.** If any named clause holds — or you cannot confidently rule one out — **escalate** — compose a focused multiple-choice question with `AskUserQuestion`, apply the answer as the decision, continue. Deciding alone is never the safe default under doubt; the worst case of a wrong escalation is one extra question, the worst case of a wrong decide-alone is an undetected bad call.

## Scope-fit escape

This skill targets small-to-medium changes. If at any point the change proves **not** small-or-medium — scope explosion, a core assumption breaks open into a large redesign, or sustained complex reasoning is needed — **escalate**, recommending a switch to `minerva:propose-ship-auto` (panel-governed) or `minerva:propose-ship` (human-gated). Leave the work unit recoverable and emit the [final-report-on-bail](governance.md) shape. Do not silently grind a large change through this path.

## Never-bypassed self-checks

Completion verification, mid-work divergence confirmation, and new-plan acceptance are **reviewer gates** — they always fire (with their single reviewer) regardless of how small the change looks; their whole value is a deliberate independent look at the model's own work. For each, the escalation predicate still applies: if the reviewer's critique or your own check leaves you genuinely uncertain, escalate rather than rubber-stamp.

## Hardcoded escalation triggers

These reach the user (or halt) regardless of the predicate — see `references/governance.md` for the full list and bail-report format:

- in-flight work collision (pre-flight, `plugins/minerva/skills/propose/references/in-flight-check.md`);
- an open issue matching the seed at intake (`plugins/minerva/skills/propose/references/issue-match.md`);
- worktree-creation failure (git error, missing gitignore, slug collision);
- ship-phase failures: CI auto-fix classified `other`, push rejection, `gh` auth failure;
- the global escalation counter reaching 3.

## Escalation counter

Maintain one counter across the run — per-run state owned by the main orchestration loop (it survives the inline `Skill`-tool delegations of Phases 4.5 / 6 / 7). Increment on **every** user escalation (predicate-driven or hardcoded). If it reaches **3**, halt before the next decision point and emit the final-report-on-bail. Recovery: run the individual minerva skills manually from the current state.

## Per-decision logging

After every decision point, append a one-line entry to the work unit's `scratchpad.md` under a `## Balanced decisions YYYY-MM-DD` header — a distinct heading that does not collide with `minerva:work`'s sections:

```
## Balanced decisions 2026-06-29
- [decided] whole-proposal soundness: single-surface, no public interface (solo gate)
- [reviewed — clean] scope check: single unit (Skeptic accept; flagged nothing load-bearing)
- [reviewed — folded] approach: option B (Skeptic surfaced a dominant alternative C — folded; rejected A duplicates orchestration)
- [rechecked — clean] approach: fold-audit confirmed C addresses items 1–3; no new concerns
- [reviewed — folded] whole-proposal soundness: Skeptic revise — criterion 4 unsatisfiable under the lifecycle's own writes; reworded
- [rechecked — residual folded] whole-proposal soundness: item 2 partially addressed (example block still named the old field) — non-load-bearing, folded
- [rechecked — escalated] scope check: fold-audit found item 1 not addressed (README surface still missing) — asked; user chose to include the README
- [reviewed — folded] completion verification: criterion #3 unmet per Verifier (no test in diff) → replan to close
- [escalated to user] approach: Skeptic critique I could not confidently adjudicate — user picked option B
- [synthesis] refreshed overview.md (watermark 044→045; 1 entry)
```

- `[decided]` — a solo gate; record the one-line rationale (approach decisions also record the rejected alternatives).
- `[reviewed — folded]` / `[reviewed — clean]` — a reviewer gate; record what the reviewer flagged and whether it was folded.
- `[rechecked — clean]` / `[rechecked — residual folded]` / `[rechecked — escalated]` — the fold-audit re-check; written **immediately after** its `[reviewed — folded]` line, naming the same gate, so the two pair by adjacency. `[rechecked — escalated]` carries the question and the answer itself and is the only escalation line for that gate.
- `[escalated to user]` — record what was asked and the answer.

These are scratchpad data — `minerva:promote` treats them as routine noise unless a decision reveals a durable pattern, in which case it goes through the standard PROMOTE/MERGE/DISCARD partition.

## Decision taxonomy

The `Reviewer?` column marks which gates dispatch the single reviewer. Every other gate is main-model-solo with the escalation predicate as the fail-closed exception.

| Phase | Decision | Default | Reviewer? |
|---|---|---|---|
| Pre-flight | In-flight work collision | Hardcoded user escalation | No (hardcoded) |
| Propose | Open-issue match at intake | Hardcoded user escalation on a match | No (hardcoded) |
| Propose | Scope check (single unit vs. decompose) | Main model decides | **Yes — Skeptic** |
| Propose | Approach selection | Main model decides | **Yes — Skeptic** |
| Propose | Whole-proposal soundness | Main model decides | **Yes — Skeptic** |
| Work | Mid-work load-bearing divergence | Main model confirms | **Yes — Skeptic** (when triggered) |
| Replan | New-plan acceptance | Main model accepts | **Yes — Skeptic** (when triggered) |
| Work | Completion verification | Main model self-checks | **Yes — Verifier** |
| Review | Per-finding triage | Main model decides | No (solo) |
| Review | Replan-vs-FIX | Main model decides | **Yes — Skeptic** (when triggered) |
| Promote | Four-way partition (PROMOTE/MERGE/DISCARD/TODO) | Main model decides | No (solo) |
| Promote | TODO disposition | Main model decides | No (solo) |
| Cleanup | Knowledge reconciliation (index, reciprocals, overview) | Delegated, self-gating | n/a |
| Ship | Commit message / PR title+body | Main model accepts draft | n/a (operational) |
| Ship | CI auto-fix `other` bail | Hardcoded user escalation | No (hardcoded) |
| Cleanup gate | PR state polling + cleanup | No decision | n/a |
