# Decision protocol — full policy

Read once, in full, before the run's first strategic/tactical decision point. Its rules then apply to every decision that follows.

This skill picks the adjudication **tier** each decision earns, one decision at a time: **solo** (the main model decides), **reviewer** (one fresh-context Skeptic or Verifier, plus one fold-audit re-check after a fold), or **panel** (a 3-agent `minerva:round-table`). Uncertainty moves a decision **up a tier** inside this run. It never stops the run to recommend a different orchestrator. The whole ladder lives here because the run cannot know in advance which decisions will turn out load-bearing (`2026-05-31-decision-per-decision-skip-over-sizing-gate`).

## No whole-run sizing

There is **no** up-front classification of the run as small, medium or large, and no mode flag. A size verdict made at intake judges the seed before the risky decision exists, so it is blind to the task that looks small but contains one load-bearing call. Each decision is routed on its own evidence at the moment it is made.

## Decide first, then route

At each strategic/tactical decision point, the main model first **drafts the decision** exactly as it would alone: the scope cut, the chosen approach, the completion checklist, the dispositions. It then selects the tier for **that drafted decision** by the [tier-selection order](#tier-selection-order). Routing after deciding catches ambiguity that only shows up while deciding, and a reviewer then reads a committed decision rather than the main model's reasoning, so it carries no confirmation bias.

Operational decisions (commit messages, PR bodies, file paths) take no tier. The main model executes them.

## Tier-selection order

For a drafted decision, take the first step that applies, then clamp the result to the row's floor and ceiling in the [Decision taxonomy](#decision-taxonomy):

1. **Hardcoded trigger → user.** In-flight collision, open-issue match at intake, worktree-creation failure, ship-phase failures (`other` classification, push rejection, `gh` auth failure), global escalation counter at 3. See `references/governance.md`.
2. **Panel predicate → panel.** Convene a panel if **any** clause holds, **or if you are unsure whether it holds** (except the interface clause — see below):
   - **genuine ambiguity** — you enumerated ≥2 viable options and none is dominant on the stated criteria;
   - **high blast radius / irreversible** — hard to walk back, or a broad rather than bounded surface;
   - **existing interface change** — the decision renames, removes or changes the behaviour of an **existing** public interface or cross-cutting contract that consumers **outside this work unit** already rely on. *Introducing* a new interface, package or tool surface is not this clause; it fails the solo predicate's "no new public interface" clause and lands at reviewer. A consumer added inside the same unit does not make an interface "existing";
   - **knowledge tension** — the decision would violate, or sits in tension with, a documented `.minerva/knowledge/` constraint.
3. **Solo predicate → solo.** Decide alone **only if every** clause holds:
   - **additive / low blast radius** — the artifact adds rather than rewrites, with a bounded surface;
   - **mechanically verifiable** — the supporting evidence is a named passing test, a file that exists, a count — not an opinion;
   - **single surface** — one file or one concern;
   - **no new public interface or cross-cutting contract**;
   - **no knowledge conflict**;
   - **(approach-bearing decisions only)** you actually **enumerated ≥2 viable approaches and one is strictly dominant**. This is an action check (did you enumerate), not a self-judgment that no alternative exists.
4. **Otherwise → reviewer.** The default tier: a decision that is not provably small and not ambiguous or high-stakes.

**Both predicates fail closed, in opposite directions — with one exception.** Doubt about a panel clause convenes the panel; doubt about a solo clause denies solo. A wrong escalation costs a dispatch; a wrong de-escalation is an unchecked call on a decision that deserved a second look.

The exception is **doubt about the existing-interface clause** at a **Skeptic gate** (scope, approach, whole-proposal): it routes to the **reviewer**, not the panel, and never to solo. Write your specific doubt ("does the reddit-ads tool rename break the README's documented calls?") into the Skeptic's CONTEXT; the Skeptic answers it in its `## Panel warranted?` section, and a named, evidenced clause you cannot rule out moves the decision up to a panel (see [Upward moves](#upward-moves)). The trade-off is deliberate: the interface clause's second look is an independent Skeptic seeded with your doubt rather than an automatic panel. The evidence was that this clause, on doubt and on new surfaces nobody consumed yet, convened most of auto's panels (9 of 11 predicate panels in the 2026-09-23..26 runs), while the other clauses fired rarely. Doubt about ambiguity, blast radius or knowledge tension still convenes a panel. The exception does not reach **completion**: there the reviewer is a Verifier, which has no `## Panel warranted?` section and no upward move, so doubt about whether the diff changes an existing interface beyond what the proposal approved still convenes the completion panel.

**A clause fires once per approved change.** A *surface* is the named thing consumers bind to: a server's tool set, a CLI's flags and output, an env-var contract, a skill's protocol file. Once a gate has adjudicated a panel clause for a surface **and approved that change** (at any tier), later gates in the run do not re-fire that clause for the same approved change. Every decision line's `(tier: …)` reason names the clause and surface it adjudicated, and that log is the record later gates check. This suppresses only re-firing on what was already approved. Inside a gate wave (`references/phases.md` Phase 1), an earlier gate's clause is still **pending** when later gates are routed. A later gate may route on it provisionally, but only if that gate is re-routed at the restart check whenever the earlier gate did not approve the change as drafted. A surface that raised no concern at an earlier gate is not exempt when one appears later, and completion convenes a panel on the interface clause only when the diff changes an interface or contract **beyond what the proposal approved**.

**Row ceilings override step 2 and row floors override step 3.** On a row capped at reviewer, a holding panel predicate routes to reviewer. On a row floored at reviewer, a holding solo predicate still routes to reviewer. On a row floored at panel, the decision is a panel whatever steps 2–4 say.

**Triage, promote partition and TODO disposition do not run steps 3–4.** A disposition is a judgment call by nature, so the solo predicate's mechanical-evidence clause would never pass and every item would fall through to reviewer. These rows are **solo** unless the panel predicate holds, then **reviewer**. On them the clause that realistically fires is ambiguity — an item with two defensible dispositions and none dominant (FIX vs. SUGGEST on a finding, PROMOTE vs. DISCARD on an entry) — or knowledge tension, when a disposition would contradict an entry.

## Upward moves

A decision moves **up** a tier, never sideways to another skill:

- **Reviewer → panel** when the reviewer's critique is load-bearing and the main model **cannot confidently adjudicate** it (the [anti-circularity escape](#arbitrating-a-skeptic-critique)).
- **Reviewer → panel** when the [fold-audit re-check](#fold-audit-re-check) finds a load-bearing item not addressed, partially addressed or regressed, or a new load-bearing concern.
- **Reviewer → panel** when the Skeptic's `## Panel warranted?` section names a panel clause with evidence and the main model **cannot rule it out** on the facts. A bare "yes" with no evidence is not an event. This event applies only on rows whose ceiling is panel, and only for a clause that was **not** already the reason the decision reached the reviewer. Capped rows (triage, partition, TODO) reach the reviewer *because* a panel clause holds, so the section is ignored there. When it fires, go up to the panel **immediately**, before arbitrating or folding the critique, and carry the critique into the panel's CONTEXT. No fold-audit runs; log `[reviewed — escalated]`.
- **Panel → user** when the panel fails quorum after its one revision round (`minerva:round-table`'s escalation). This increments the global escalation counter.
- **Capped rows go to the user instead.** On a row whose ceiling is reviewer (triage, partition, TODO), an upward move that would reach a panel goes to the **user**. The ceiling wins; these rows never convene a panel.

The up-arm keys **only** on the three reviewer events above — the two that used to go straight to the user, plus an evidenced panel clause — never on a Skeptic `revise` as such. A Skeptic returns `revise` on most dispatches, and keying on it would turn every reviewer gate into a panel (`2026-09-05-decision-balanced-rechecks-its-folds`).

**What a panel receives on an upward move.** ARTIFACT = the decision as it now stands (the revised decision after a fold). CONTEXT adds, as enumerated items beyond round-table's usual list, the original decision, the reviewer's critique verbatim, and the fold-audit disposition if one ran. The panel judges whether the current decision is sound given that history; it does not re-derive the decision from a blank page.

**A change that grows mid-run needs no escape hatch.** Its later decisions fail the solo predicate and trip the panel predicate on blast radius. There is no "switch to another orchestrator" recommendation anywhere in this skill.

## Reviewer tier

### Skeptic gates

At a Skeptic gate, after the decision is drafted and routed to reviewer:

1. **Dispatch one reviewer.** Dispatch one fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Skeptic brief](#skeptic-brief). Pass only the gate's ARTIFACT + CONTEXT from `references/phases.md`, plus your specific doubt when the gate reached reviewer on doubt about the interface clause; dispatch parameters and model policy belong to the host adapter.
2. **Arbitrate inline** — see [Arbitrating a Skeptic critique](#arbitrating-a-skeptic-critique).
3. **After a fold, run the [fold-audit re-check](#fold-audit-re-check).** After a clean outcome, nothing more is dispatched.

**Budget: at most two dispatches per Skeptic gate** — the review, plus the re-check when and only when step 2 folded. Never a third reviewer. An upward move to a panel is a separate tier with its own budget.

### Arbitrating a Skeptic critique

The main model that drafted the decision also judges the critique, so "load-bearing" is defined behaviourally to keep that from collapsing into self-confirmation. A critique is **load-bearing** iff it identifies at least one of:

- (a) a violation of a documented `.minerva/knowledge/` constraint, or of a stated success criterion;
- (b) a missed dependency or integration risk the decision did not account for;
- (c) an overlooked scope surface or file;
- (d) **[approach/scope gates]** a viable alternative that is **strictly dominant** on the stated criteria.

Stylistic disagreement, or a re-weighting of tradeoffs the decision already considered with no new information, is **not** load-bearing.

- **Load-bearing → fold.** Revise the decision to address it. Log `[reviewed — folded]` with what was folded.
- **Not load-bearing → proceed.** Log `[reviewed — clean]`, recording any noted-but-dismissed concern so review/promote can audit the call.
- **Anti-circularity escape → panel.** If folding would require a **materially different decision** and the main model **cannot confidently tell** whether the reviewer is right, move the decision up to a panel. Log `[reviewed — escalated]` naming where it went. Never self-confirm past a critique you cannot honestly adjudicate.

### Fold-audit re-check

**Trigger.** Step 2 logged `[reviewed — folded]` at a Skeptic gate.

**Dispatch.** Write the revised decision down first. Then dispatch one more fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Fold-audit brief](#fold-audit-brief). ARTIFACT = the original decision as first written, the Skeptic's critique **verbatim**, and the revised decision; CONTEXT = exactly the CONTEXT the gate gave the Skeptic. It must not be the same agent and must not see the main model's arbitration reasoning.

**Arbitration is strict — no discretionary branch:**

- `accept` → proceed. Log `[rechecked — clean]`.
- `partially` on an item whose residual is **not** load-bearing → fold the residual, proceed. Log `[rechecked — residual folded]`, naming the residual.
- Anything else — a load-bearing item `partially`, `not addressed` or `regressed`, or a load-bearing item under `## New concerns` → **move up to a panel** (on a capped row, to the user). Log `[rechecked — escalated]` naming where it went. The main model may not decide the re-check is mistaken and proceed, and there is no third reviewer.

The per-item `## Disposition` lines govern; the `## Verdict` line summarises them. If they disagree, the dispositions win.

### The Verifier gate (completion) is asymmetric

Completion verification uses a **Verifier**, not a Skeptic, and it is deliberately different (`2026-09-05-decision-balanced-rechecks-its-folds`): **one dispatch, no fold-audit re-check, no anti-circularity escape**. Dispatch one fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Verifier brief](#verifier-brief). A Verifier `revise`/`reject` that names an unmet criterion is a success-criteria divergence: go to Phase 2.5 (replan), whose new-plan acceptance has a panel floor. That loop is the Verifier's re-check. The two-dispatch Skeptic budget and the upward moves above do **not** apply here. When the panel predicate holds at completion, completion is a panel instead. On the interface clause that means the diff changes an interface or contract **beyond what the proposal approved**; an interface the proposal's gates already adjudicated and approved does not re-fire here ([a clause fires once per approved change](#tier-selection-order)).

### Skeptic brief

Adapted from `skills/round-table/references/briefs.md`. It keeps three verdicts on purpose: there is no quorum to protect at the reviewer tier, and the main model already arbitrates each critique item as load-bearing or not, which is the distinction a panel's `accept with fixes` draws.

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

Then say whether this decision needed a full panel instead of one reviewer. A
panel is warranted only if one of these holds: genuine ambiguity (≥2 viable
options, none dominant); high blast radius or irreversibility; a change to an
EXISTING public interface or cross-cutting contract that consumers outside this
work unit rely on (introducing a new one does not count); or tension with a
documented knowledge constraint. If CONTEXT carries the author's doubt about one
of these, answer that doubt directly.

Output format:
## Critique
<numbered concerns, each with severity high/medium/low>
## Panel warranted?
<no | yes — <clause>: <evidence from the ARTIFACT or repo>>
## Verdict
<accept | revise | reject>: <one-sentence reason>
```

### Fold-audit brief

It audits a **fold**, not the decision. A reviewer that re-litigates the decision produces new concerns indistinguishable from the first review.

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

### Verifier brief

- **ARTIFACT:** the success-criteria checklist (each criterion + the main model's *claimed* evidence + its yes/no), `git diff <default-branch>...HEAD`, and the proposal's `## Success criteria`.
- **Task:** for **each** criterion, independently determine whether it is honestly met. Do not trust the claimed evidence — reproduce it: read the named files; where a criterion names a test or an anchor, run a **read-only** command or `grep` to confirm the diff contains or passes it. Actively try to falsify "done": a criterion with no corresponding diff, a partial implementation, a claim the code does not support.
- **Output:** per criterion, `{met: yes | no | unsure, evidence-or-gap: <one line>}`, then `accept` (all honestly met) / `revise` (gaps to close) / `reject`.

## Panel tier

The panel mechanics — dispatch, the Proponent/Skeptic/Arbiter briefs, vote semantics including `accept with fixes`, the revision round and escalation composition — live in `minerva:round-table`. When the run's first panel arrives, invoke `minerva:round-table` via the skill loader in caller mode, leading with:

> "You are running inside `minerva:propose-ship-auto`. Apply your protocol in caller mode for every panel of this run: each decision's artifact and decision context come from the orchestrator, and its quorum comes from the orchestrator's decision taxonomy (3/3 or 2/3 — never your standalone default). Log every panel line to the work unit's `scratchpad.md` under the `## Decisions YYYY-MM-DD` header, prefixing the vote tag with `panel — `."

Once loaded, apply it at each later panel **without re-invoking the skill loader**; re-invoke only if the protocol is no longer in context (for example after compaction).

Orchestrator-owned rules that round-table does not own: **whether to convene** (this file's tier selection), **quorums** (the taxonomy below), **escalation aftermath** (this skill increments the global escalation counter after a panel escalation), and the **per-decision budget** in `references/governance.md`.

## Parked dispatches

A reviewer or panel dispatch may come back as a background handle regardless of the synchronous pin (`2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch`). Every tier survives that: dispatch, end the turn if the result is not back, resume on the completion notification, then arbitrate. **Never drop a tier to avoid a park** — a parked run is recoverable; an unreviewed decision is not.

**Waves park the same way, several handles at once.** When independent decisions are dispatched together (the propose gate wave, completion alongside code review — `references/phases.md`), several handles can be outstanding. Resume on each notification and act on what that result unblocks — a panel's Arbiter goes out as soon as its own Proponent and Skeptic are back. Reconcile the wave only once every result it waits on is in. A parked handle is never a verdict, and a wave never reconciles on a partial set.

## No ceremony ratification

Never ask the user — up front or mid-run — to pick a tier, a "ceremony level", or to pre-authorize skipping reviews or panels that have not yet run and failed. The per-decision tier selection is the **only** de-ceremony mechanism. User interaction happens only at the hardcoded triggers and at genuine escalations (`2026-05-31-decision-per-decision-skip-over-sizing-gate`).

- **Escalation batching stays legitimate.** A panel that failed quorum twice escalates with a focused, batched question.
- **Memories never lower a tier.** Stored preferences and prior-session feedback never satisfy the solo predicate or substitute for its per-decision evidence.
- **Unsolicited user directives are honored, never solicited.** If the user spontaneously tells you to skip reviews or panels, honor it and log each affected decision as `[user-directed]`. Never prompt for such a directive.

## Per-decision logging

After every decision, append one line to the work unit's `scratchpad.md` under a `## Decisions YYYY-MM-DD` header. Append **inside that block**, not at the end of the file: a line under a later header (`## Work notes`, `## Review triage`) is invisible to `scripts/decision_telemetry.py`. Each line starts with its tier and outcome and ends with why that tier was chosen:

```
## Decisions 2026-09-23
- [solo] scope check: single unit (tier: solo predicate — only SKILL.md touched, additive, no interface)
- [reviewed — clean] approach: option B (tier: reviewer — not provably small; Skeptic flagged nothing load-bearing)
- [reviewed — folded] whole-proposal: criterion 4 unsatisfiable under the lifecycle's own writes; reworded (tier: reviewer)
- [rechecked — clean] whole-proposal: fold-audit confirmed items 1–3 addressed
- [reviewed — folded] approach: Skeptic surfaced a dominant alternative C — switched to C (tier: reviewer)
- [rechecked — residual folded] approach: item 2 partially addressed (example still named the old field) — folded
- [reviewed — folded] scope check: README surface missing (tier: reviewer)
- [rechecked — escalated] scope check: item 1 not addressed → panel
- [panel — 3/3 accept, 1 with fixes] scope check: include README (tier: panel — fold-audit escalation)
- [panel — 2/3 accept, skeptic dissented] approach: option B (tier: panel — existing interface change)
- [reviewed — escalated] whole-proposal: Skeptic says criterion 3 is untestable; cannot adjudicate → panel (tier: reviewer)
- [panel — 3/3 accept] whole-proposal: criterion 3 reworded (tier: panel — anti-circularity escape)
- [reviewed — clean] approach: option A, new mcp/gsc tool surface (tier: reviewer — introduces an interface, no existing consumer; parallel wave)
- [reviewed — escalated] approach: Panel warranted? named existing-interface change — renames tools the README documents; cannot rule out → panel (tier: reviewer — interface-clause doubt passed to the Skeptic)
- [reviewed — clean] whole-proposal (restart): re-reviewed after the approach pick changed B → C (tier: reviewer; parallel wave restart)
- [solo] review triage: 3 FIX / 1 SUGGEST / 0 IGNORE (tier: default-solo row — no item had two defensible dispositions)
- [reviewed — clean] completion verification: Verifier reproduced all 5 criteria (tier: reviewer floor)
- [escalated to user] approach: panel split 1/3 twice — user picked option B
- [user-directed] review triage: user asked to skip the reviewer
```

- `[solo]` — on a row that could have gone higher, record the **concrete evidence** that satisfied the solo predicate, so review/promote can audit that it was honest. On a default-solo row (triage, partition, TODO), record the disposition counts and why no item met the ambiguity clause. Approach decisions also record the rejected alternatives.
- `[reviewed — clean]` / `[reviewed — folded]` — a reviewer gate; record what the reviewer flagged and whether it was folded.
- `[reviewed — escalated]` — the anti-circularity escape, or an evidenced `## Panel warranted?` clause; name which, and where the decision went (panel, or user on a capped row). The panel's own line follows it.
- `[rechecked — clean]` / `[rechecked — residual folded]` / `[rechecked — escalated]` — the fold-audit re-check, written **immediately after** its `[reviewed — folded]` line and naming the same gate, so the two pair by adjacency. `[rechecked — escalated]` names where the decision went (panel, or user on a capped row).
- `[panel — …]` — round-table's vote line, **prefixed `panel — `** so the tier is explicit (round-table's own standalone format is the bare `[3/3 accept]`; telemetry reads either under this header). A vote counted from `accept with fixes` renders as `, N with fixes`, each folded fix on an indented line beneath.
- `[escalated to user]` — what was asked and the answer.
- `[user-directed]` — an unsolicited user directive; the directive is the justification.

These are scratchpad data. `minerva:promote` treats them as routine noise unless a decision reveals a durable pattern.

## Re-measure

The up-arm's trigger rate is a prediction, not a measurement: the anti-circularity escape fired 0 times in 13 balanced runs, and fold-audit escalations have a few weeks of history. `scripts/decision_telemetry.py` tallies tier × gate × outcome. Once ~10 runs have logged, revisit this taxonomy via `minerva:replan` — including how often a `## Panel warranted?` escalation fires, and whether a reviewer at the narrowed interface clause let through something a later gate or review had to fix, and whether the propose-phase abort (`references/governance.md`) has gone inert now that most escalations pass through a panel first; if it has, re-key it rather than leave dead text.

## Decision taxonomy

Default = the tier when no predicate fires. Floor and ceiling clamp whatever the [tier-selection order](#tier-selection-order) picks. Quorum applies when the decision reaches a panel.

| Phase | Decision | Default | Floor | Ceiling | Reviewer brief | Panel quorum |
|---|---|---|---|---|---|---|
| Pre-flight | In-flight work collision | Hardcoded user escalation | — | — | — | — |
| Propose | Open-issue match at intake | Hardcoded user escalation on a match | — | — | — | — |
| Propose | Scope check (one PR / phases / decompose) | reviewer | solo | panel | Skeptic | 3/3 |
| Propose | Approach selection | reviewer | solo | panel | Skeptic | 3/3 |
| Propose | Whole-proposal soundness | reviewer | solo | panel | Skeptic | 3/3 |
| Work | Mid-work load-bearing divergence | panel | **panel** | panel | — | 2/3 |
| Replan | New-plan acceptance | panel | **panel** | panel | — | 3/3 |
| Work | Completion verification | reviewer | **reviewer** | panel | **Verifier** (asymmetric) | 3/3 — with a deliberate exception: 2/3 proceeds with dissent logged, ≤1/3 replans (`references/phases.md`) |
| Review | Per-finding triage | solo | solo | **reviewer** | Skeptic | — |
| Review | Replan-vs-FIX | panel | **panel** | panel | — | 2/3 |
| Promote | Four-way partition (PROMOTE/MERGE/DISCARD/TODO) | solo | solo | **reviewer** | Skeptic | — |
| Promote | TODO disposition | solo | solo | **reviewer** | Skeptic | — |
| Cleanup | Knowledge reconciliation | Delegated to `minerva:cleanup`, self-gating | — | — | — | — |
| Ship | Commit message / PR title + body | Operational — main model accepts draft | — | — | — | — |
| Ship | CI auto-fix `other` bail | Hardcoded user escalation | — | — | — | — |
| Cleanup gate | PR state polling + cleanup | No decision | — | — | — | — |

**Why these floors.** Divergence, new-plan acceptance and replan-vs-FIX keep auto's always-panel floor: their precondition is an already-surfaced load-bearing divergence or finding, they fire rarely, and there is no evidence for lowering them. Completion is the one never-skipped row lowered to a reviewer floor, on evidence: 0 of 18 auto completion panels went to a revision round, and its value is independent *reproduction* of each criterion, which one Verifier does (`2026-06-29-decision-propose-ship-balanced-single-reviewer`). Scope, approach and whole-proposal run the full ladder: the revision rates that justify reviewing them (approach 17/25, whole-proposal 13/27, scope 7/22 auto panels) were measured on panels that had **already failed** the solo predicate, which is exactly where this table sends a reviewer. None of these floors or ceilings changed when the interface clause was narrowed to **existing** interfaces (2026-09-26). That change only moves which decisions reach a panel from the reviewer default. In the six runs before it, approach, whole-proposal and completion each went to a panel in 5 of 6 runs, mostly on new, not-yet-consumed tool surfaces and on the same approved interface re-firing at completion.
