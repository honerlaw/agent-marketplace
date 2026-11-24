# Decision protocol — full policy

Read once, in full, before the run's first strategic/tactical decision point. Its rules then apply to every decision that follows.

This skill picks the adjudication **tier** each decision earns, one decision at a time. There are two tiers:

- **solo** — the main model decides alone;
- **reviewer** — one fresh-context Skeptic (or a Verifier at completion), arbitrated inline, plus one fold-audit re-check after a fold and, when that still cannot settle the decision, one Adjudicator.

When the reviewer tier cannot settle a decision, it goes to the **user**. It never stops the run to recommend a different orchestrator. The whole ladder lives here because the run cannot know in advance which decisions will turn out load-bearing (`2026-05-31-decision-per-decision-skip-over-sizing-gate`).

There is no multi-agent panel tier. The 3-agent consensus panel was removed in minerva 4.0.0, the protocol this skill was ported from: at matched compute, debate ties or loses to independent review, role-locked votes are not independent samples, and in this repo's own logs the panel's output was the fixes a single Skeptic also produces. minerva's work unit `2026-11-19-remove-round-table-tier`, in the marketplace repository that ships both plugins, holds the evidence.

## No whole-run sizing

There is **no** up-front classification of the run as small, medium or large, and no mode flag. A size verdict made at intake judges the seed before the risky decision exists, so it is blind to the task that looks small but contains one load-bearing call. Each decision is routed on its own evidence at the moment it is made.

## Decide first, then route

At each strategic/tactical decision point, the main model first **drafts the decision** exactly as it would alone: the scope cut, the chosen approach, the completion checklist, the dispositions. It then selects the tier for **that drafted decision** by the [tier-selection order](#tier-selection-order). Routing after deciding catches ambiguity that only shows up while deciding, and a reviewer then reads a committed decision rather than the main model's reasoning, so it carries no confirmation bias.

Operational decisions (commit messages, PR bodies, file paths) take no tier. The main model executes them.

## Tier-selection order

For a drafted decision, take the first step that applies, then clamp the result to the row's floor in the [Decision taxonomy](#decision-taxonomy):

1. **Hardcoded trigger → user.** In-flight collision, open-issue match at intake, worktree-creation failure, ship-phase failures (`other` classification, push rejection, `gh` auth failure), cleanup's wait on a confirmation of a merge it could not prove, global escalation counter at 3. See `references/governance.md`.
2. **Scrutiny predicate → reviewer.** Route to the reviewer if **any** clause holds, **or if you are unsure whether it holds**, and name each clause that fired (or that you could not rule out) in the reviewer's CONTEXT:
   - **genuine ambiguity** — you enumerated ≥2 viable options and none is dominant on the stated criteria;
   - **high blast radius / irreversible** — hard to walk back, or a broad rather than bounded surface;
   - **existing interface change** — the decision renames, removes or changes the behaviour of an **existing** public interface or cross-cutting contract that consumers **outside this work unit** already rely on. *Introducing* a new interface, package or tool surface is not this clause; it fails the solo predicate's "no new public interface" clause and lands at reviewer anyway. A consumer added inside the same unit does not make an interface "existing";
   - **knowledge tension** — the decision would violate, or sits in tension with, a constraint entry in the project's lore (pending entries included).
3. **Solo predicate → solo.** Decide alone **only if every** clause holds:
   - **additive / low blast radius** — the artifact adds rather than rewrites, with a bounded surface;
   - **mechanically verifiable** — the supporting evidence is a named passing test, a file that exists, a count — not an opinion;
   - **single surface** — one file or one concern;
   - **no new public interface or cross-cutting contract**;
   - **no knowledge conflict**;
   - **(approach-bearing decisions only)** you actually **enumerated ≥2 viable approaches and one is strictly dominant**. This is an action check (did you enumerate), not a self-judgment that no alternative exists.
4. **Otherwise → reviewer.** The default tier: a decision that is not provably small.

**Both predicates fail closed.** Doubt about a scrutiny clause routes to the reviewer and names the doubt; doubt about a solo clause denies solo. A wrong escalation costs a dispatch; a wrong de-escalation is an unchecked call on a decision that deserved a second look.

**Naming the clause is what the scrutiny predicate buys.** Steps 2 and 4 both land on the reviewer, so on most rows the predicate's only effect is the brief: the Skeptic is told which clause put the decision under review ("existing interface change: does the reddit-ads tool rename break the README's documented calls?") and tests exactly that. On the default-solo rows below, the predicate is also what moves a decision from solo to reviewer.

**Row floors override step 3.** On a row floored at reviewer, a holding solo predicate still routes to reviewer.

**Triage, promote partition and TODO disposition do not run steps 3–4.** A disposition is a judgment call by nature, so the solo predicate's mechanical-evidence clause would never pass and every item would fall through to reviewer. These rows are **solo** unless the scrutiny predicate holds, then **reviewer**. On them the clause that realistically fires is ambiguity — an item with two defensible dispositions and none dominant (FIX vs. SUGGEST on a finding, PROMOTE vs. DISCARD on an entry) — or knowledge tension, when a disposition would contradict an entry.

## Reviewer tier

### The ladder at a Skeptic gate

At every Skeptic gate — every row except completion — the reviewer tier is a short, fixed ladder. Each rung runs only when the one before it could not settle the decision:

1. **Skeptic.** Dispatch one fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Skeptic brief](#skeptic-brief). Pass only the gate's ARTIFACT + CONTEXT from `references/phases.md`, plus every scrutiny clause that fired or that you could not rule out; dispatch parameters and model policy belong to the host adapter. Then [arbitrate the critique](#arbitrating-a-skeptic-critique) inline.
2. **Fold-audit** — only after a fold. See [Fold-audit re-check](#fold-audit-re-check).
3. **Adjudicator** — only after a failed fold-audit or the anti-circularity escape. See [Adjudicator](#adjudicator).
4. **User** — only when the Adjudicator's rulings leave a disputed item `unresolved` (logged `[adjudicated — escalated]`). Ask with the user question operation, naming the gate, the disputed items by their `C<n>` / `F<n>` labels and each side's evidence. This increments the global escalation counter.

**Budget: at most three dispatches per Skeptic gate** — the Skeptic, the fold-audit when and only when step 1 folded, and the Adjudicator when and only when the decision could not otherwise be settled. Never a second Skeptic, never a second fold-audit, never a fourth reviewer.

### Arbitrating a Skeptic critique

The main model that drafted the decision also judges the critique, so "load-bearing" is defined behaviourally to keep that from collapsing into self-confirmation. A critique is **load-bearing** iff it identifies at least one of:

- (a) a violation of a constraint entry in the project's lore, or of a stated success criterion;
- (b) a missed dependency or integration risk the decision did not account for;
- (c) an overlooked scope surface or file;
- (d) **[approach/scope gates]** a viable alternative that is **strictly dominant** on the stated criteria.

Stylistic disagreement, or a re-weighting of tradeoffs the decision already considered with no new information, is **not** load-bearing. A concern the Skeptic itself marked non-blocking is load-bearing only if it independently meets (a)–(d).

- **Load-bearing → fold.** Revise the decision to address it. Log `[reviewed — folded]` with what was folded, then run the fold-audit.
- **Not load-bearing → proceed.** Log `[reviewed — clean]`, recording any noted-but-dismissed concern so review/promote can audit the call.
- **Anti-circularity escape → Adjudicator.** If folding would require a **materially different decision** and the main model **cannot confidently tell** whether the Skeptic is right, do not fold and do not proceed. Send the disputed items to the Adjudicator. Log `[reviewed — escalated]` naming the items. Never self-confirm past a critique you cannot honestly adjudicate.

### Fold-audit re-check

**Trigger.** Step 1 logged `[reviewed — folded]` at a Skeptic gate.

**Dispatch.** Write the revised decision down first. Then dispatch one more fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Fold-audit brief](#fold-audit-brief). ARTIFACT = the original decision as first written, the Skeptic's critique **verbatim**, and the revised decision; CONTEXT = exactly the CONTEXT the gate gave the Skeptic. It must not be the same agent and must not see the main model's arbitration reasoning.

**Arbitration is strict — no discretionary branch:**

- `accept` → proceed. Log `[rechecked — clean]`.
- `partially` on an item whose residual is **not** load-bearing → fold the residual, proceed. Log `[rechecked — residual folded]`, naming the residual.
- Anything else — a load-bearing item `partially`, `not addressed` or `regressed`, or a load-bearing item under `## New concerns` → **send those items to the Adjudicator**. Log `[rechecked — escalated]` naming them. The main model may not decide the re-check is mistaken and proceed.

The per-item `## Disposition` lines govern; the `## Verdict` line summarises them. If they disagree, the dispositions win.

### Adjudicator

The Adjudicator is the last independent look before the user. It is deliberately narrow: it **rules on the disputed items and nothing else**. It does not re-review the decision and it raises no new concerns. A fresh critic over a revised decision re-critiques from a blank page, and its new concerns cannot be told apart from the first review's (`2026-09-05-decision-balanced-rechecks-its-folds` rejected exactly that). An Adjudicator that may only rule on named items cannot do that.

**Dispatch.** Dispatch one fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Adjudicator brief](#adjudicator-brief). It is never the Skeptic or the fold-audit agent, and it never sees the main model's arbitration reasoning. ARTIFACT = the original decision, the Skeptic's critique **verbatim**, the revised decision and the fold-audit's output verbatim when a fold happened, and the **disputed items** by label — `C<n>` for the Skeptic's critique item *n*, `F<n>` for the fold-audit's new concern *n* (the two lists are numbered separately, so a bare number is ambiguous); CONTEXT = the gate's CONTEXT.

The disputed items are the load-bearing items the fold-audit did not accept, or, on the anti-circularity escape, the critique items the main model could not adjudicate.

**Arbitration is strict:**

- Every disputed item `resolved` or `critique mistaken` → proceed with the decision as it stands (the revised decision after a fold, the original decision on the escape path). Log `[adjudicated — proceed]`.
- Any disputed item `unresolved` → go to the **user**. Log `[adjudicated — escalated]`. This includes the escape path when the Adjudicator rules the Skeptic right: adopting a materially different decision with the gate's budget spent would ship a rewrite nobody audited, so the user decides.

The per-item rulings decide the outcome; the verdict line only summarises them. If they disagree, the rulings win, so a `proceed` verdict over an `unresolved` item still goes to the user and an `escalate` verdict over all-settled items still proceeds. A ruling with no evidence counts as `unresolved`, and so does a disputed item the Adjudicator returned no ruling for.

### The Verifier gate (completion) is asymmetric

Completion verification uses a **Verifier**, not a Skeptic, and it is deliberately different (`2026-09-05-decision-balanced-rechecks-its-folds`): **one dispatch, no fold-audit re-check, no Adjudicator, no anti-circularity escape**. Dispatch one fresh-context agent via the independent reviewer operation and **wait for results**, carrying the [Verifier brief](#verifier-brief). A Verifier `revise`/`reject` that names an unmet criterion is a success-criteria divergence: go to Phase 2.5 (replan), whose new-plan acceptance is itself a Skeptic gate. That loop is the Verifier's re-check. The Skeptic ladder above does **not** apply here. Completion is always a Verifier, whatever the scrutiny predicate says. Its value is independent *reproduction* of each criterion against the diff, which is exactly the execution-grounded check the evidence supports most strongly.

### Skeptic brief

The Skeptic keeps three verdicts. The main model already arbitrates each critique item as load-bearing or not, so there is nothing a fourth verdict would add.

```
YOUR ROLE: You are an independent Skeptic reviewing the decision in the ARTIFACT
above. You have fresh context and did not make this decision. Look for
load-bearing problems: an overlooked alternative, a violated constraint or
success criterion, a scope surface or dependency the decision missed, an
unstated assumption it relies on.

Every concern must cite its evidence: the part of the ARTIFACT, or the file and
line in the repo, that shows the problem. A concern you cannot point at is not a
concern. Mark each one blocking (the decision is unsound unless it changes) or
non-blocking (worth fixing, but the decision stands). "No concerns" is a valid
and expected answer for a sound decision; do not invent problems to have
something to report.

If CONTEXT names a scrutiny clause (ambiguity, blast radius, existing interface
change, knowledge tension), test that clause directly and say whether it holds.

Render a final verdict of accept / revise / reject. The verdict must reflect
whether the blocking concerns are real: non-blocking concerns alone are 'accept'
with the concerns listed.

Output format:
## Critique
<numbered concerns, each: blocking | non-blocking — severity high/medium/low — evidence — the concern; or "none">
## Scrutiny clause
<for each clause named in CONTEXT: holds | does not hold — <evidence>; or "none named">
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

### Adjudicator brief

```
YOUR ROLE: You are an independent Adjudicator. The ARTIFACT above holds a
decision, a Skeptic's numbered CRITIQUE of it, and — when the decision was
revised — the REVISED decision and a fold-audit of that revision. It ends with
the DISPUTED ITEMS: the critique or fold-audit items nobody has been able to
settle, each labelled C<n> (critique item n) or F<n> (the fold-audit's new
concern n). You did not write any of it and have not seen anyone's reasoning about
it.

Rule on each disputed item, and only on those. For each, read the decision as it
now stands and the repo, then decide:
- resolved — the decision as it stands already deals with the concern;
- unresolved — the concern is real and the decision as it stands does not deal
  with it;
- critique mistaken — the concern is wrong on the facts.
Cite the evidence for each ruling: the part of the ARTIFACT, or the file and
line. A ruling without evidence counts as unresolved.

Do not raise new concerns, do not review anything outside the disputed items,
and do not propose a different decision.

Output format:
## Rulings
<one line per disputed item, by its label: `C<n>|F<n>. resolved | unresolved | critique mistaken — <evidence>`>
## Verdict
<proceed | escalate>: <one-sentence reason>; proceed only if no item is unresolved
```

### Verifier brief

- **ARTIFACT:** the success-criteria checklist (each criterion + the main model's *claimed* evidence + its yes/no), `git diff "${BASE:?}"...HEAD` (with the runtime contract's default-branch snippet), and the proposal's `## Success criteria`.
- **Task:** for **each** criterion, independently determine whether it is honestly met. Do not trust the claimed evidence — reproduce it: read the named files; where a criterion names a test or an anchor, run a **read-only** command or `grep` to confirm the diff contains or passes it. Actively try to falsify "done": a criterion with no corresponding diff, a partial implementation, a claim the code does not support. Also check that the diff does not change an **existing** interface or contract beyond what the proposal approved; if it does, report that as an unmet criterion.
- **Output:** per criterion, `{met: yes | no | unsure, evidence-or-gap: <one line>}`, then `accept` (all honestly met) / `revise` (gaps to close) / `reject`.

## Parked dispatches

A reviewer dispatch may come back as a background handle regardless of the synchronous pin (`2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch`). Every rung survives that: dispatch, end the turn if the result is not back, resume on the completion notification, then arbitrate. **Never skip a rung to avoid a park** — a parked run is recoverable; an unreviewed decision is not.

**Waves park the same way, several handles at once.** When independent decisions are dispatched together (the propose gate wave, completion alongside code review — `references/phases.md`), several handles can be outstanding. Resume on each notification and act on what that result unblocks — a gate's fold-audit goes out as soon as its own fold is written, never held for a joint batch (whole-proposal's only after the restart check, `references/phases.md` Phase 1 (d)). Reconcile the wave only once every result it waits on is in. A parked handle is never a verdict, and a wave never reconciles on a partial set.

## No ceremony ratification

Never ask the user — up front or mid-run — to pick a tier, a "ceremony level", or to pre-authorize skipping reviews that have not yet run and failed. The per-decision tier selection is the **only** de-ceremony mechanism. User interaction happens only at the hardcoded triggers and at genuine escalations (`2026-05-31-decision-per-decision-skip-over-sizing-gate`).

- **Escalation batching stays legitimate.** An Adjudicator escalation asks one focused, batched question covering every unresolved item at that gate.
- **Memories never lower a tier.** Stored preferences and prior-session feedback never satisfy the solo predicate or substitute for its per-decision evidence.
- **Unsolicited user directives are honored, never solicited.** If the user spontaneously tells you to skip reviews, honor it and log each affected decision as `[user-directed]`. Never prompt for such a directive.

## Per-decision logging

After every decision, append one line to the work unit's scratchpad record under a `## Decisions YYYY-MM-DD` header (`storage:record.write`: read it, then `mode: replace`). Append **inside that block**, not at the end of the record: a line under a later header (`## Work notes`, `## Review triage`) is invisible to a tally that reads the block, such as minerva's `scripts/decision_telemetry.py`, whose format this is. Each line starts with its tier and outcome and ends with why that tier was chosen:

```
## Decisions 2026-11-19
- [solo] scope check: single unit (tier: solo predicate — only SKILL.md touched, additive, no interface)
- [reviewed — clean] approach: option B (tier: reviewer — not provably small; Skeptic flagged nothing blocking)
- [reviewed — folded] whole-proposal: criterion 4 unsatisfiable under the lifecycle's own writes; reworded (tier: reviewer)
- [rechecked — clean] whole-proposal: fold-audit confirmed C1–C3 addressed
- [reviewed — folded] approach: Skeptic surfaced a dominant alternative C — switched to C (tier: reviewer)
- [rechecked — residual folded] approach: C2 partially addressed (example still named the old field) — folded
- [reviewed — folded] scope check: README surface missing (tier: reviewer — scrutiny: existing interface change)
- [rechecked — escalated] scope check: C1 not addressed → Adjudicator
- [adjudicated — proceed] scope check: C1 resolved — README section already covered by the revised scope
- [reviewed — escalated] whole-proposal: C3 says criterion 3 is untestable; cannot adjudicate → Adjudicator (tier: reviewer)
- [adjudicated — escalated] whole-proposal: C3 unresolved — no test can observe the criterion → user
- [escalated to user] whole-proposal: C3 — user reworded it to a grep-checkable form
- [reviewed — clean] approach: option A, new mcp/gsc tool surface (tier: reviewer — introduces an interface, no existing consumer; parallel wave)
- [reviewed — clean] whole-proposal (restart): re-reviewed after the approach pick changed B → C (tier: reviewer; parallel wave restart)
- [solo] review triage: 3 FIX / 1 SUGGEST / 0 IGNORE (tier: default-solo row — no item had two defensible dispositions)
- [reviewed — clean] completion verification: Verifier reproduced all 5 criteria (tier: reviewer floor)
- [user-directed] review triage: user asked to skip the reviewer
```

- `[solo]` — on a row that could have gone higher, record the **concrete evidence** that satisfied the solo predicate, so review/promote can audit that it was honest. On a default-solo row (triage, partition, TODO), record the disposition counts and why no item met the ambiguity clause. Approach decisions also record the rejected alternatives.
- `[reviewed — clean]` / `[reviewed — folded]` — a Skeptic or Verifier gate; record what the reviewer flagged, whether it was folded, and the scrutiny clause that fired, if any.
- `[reviewed — escalated]` — the anti-circularity escape; name the disputed items by their `C<n>` labels. Its `[adjudicated — …]` line follows it.
- `[rechecked — clean]` / `[rechecked — residual folded]` / `[rechecked — escalated]` — the fold-audit re-check, written **immediately after** its `[reviewed — folded]` line and naming the same gate, so the two pair by adjacency. `[rechecked — escalated]` names the items sent to the Adjudicator by their `C<n>` / `F<n>` labels; its `[adjudicated — …]` line follows it.
- `[adjudicated — proceed]` / `[adjudicated — escalated]` — the Adjudicator, written **immediately after** the `[reviewed — escalated]` or `[rechecked — escalated]` line that sent the decision there, naming the same gate. An `[adjudicated — escalated]` line is followed by the `[escalated to user]` line.
- `[escalated to user]` — what was asked and the answer.
- `[user-directed]` — an unsolicited user directive; the directive is the justification.

These are scratchpad data. `lorestrom:promote` treats them as routine noise unless a decision reveals a durable pattern.

## Re-measure

The Adjudicator's trigger rate is a prediction, not a measurement. In the panel era, only 3 decisions moved up from a reviewer (all failed fold-audits on whole-proposal) and the anti-circularity escape never fired, so the Adjudicator should rarely run and the user should rarely be asked. minerva's `scripts/decision_telemetry.py` tallies tier × gate × outcome from scratchpad files; lorestrom ships no tally yet, so its logs are counted by reading the records. Once ~10 runs have logged under this protocol, revisit it via `lorestrom:replan`:

- How often the Adjudicator runs, and how often it escalates.
- Whether the user-escalation rate rose against the panel era. If it did, look at what the escalations asked before adding any tier back.
- Whether a reviewer gate on a former always-panel row (divergence, new-plan acceptance, replan-vs-FIX) let through something a later gate or review had to fix.
- Whether the propose-phase abort (`references/governance.md`) has gone inert; if it has, re-key it rather than leave dead text.

## Decision taxonomy

Default = the tier when no predicate fires. The floor clamps whatever the [tier-selection order](#tier-selection-order) picks. Every reviewer row other than completion uses the Skeptic ladder.

| Phase | Decision | Default | Floor | Reviewer brief |
|---|---|---|---|---|
| Pre-flight | In-flight work collision | Hardcoded user escalation | — | — |
| Propose | Open-issue match at intake | Hardcoded user escalation on a match | — | — |
| Propose | Scope check (one PR / phases / decompose) | reviewer | solo | Skeptic |
| Propose | Approach selection | reviewer | solo | Skeptic |
| Propose | Whole-proposal soundness | reviewer | solo | Skeptic |
| Work | Mid-work load-bearing divergence | reviewer | **reviewer** | Skeptic |
| Replan | New-plan acceptance | reviewer | **reviewer** | Skeptic |
| Work | Completion verification | reviewer | **reviewer** | **Verifier** (asymmetric) |
| Review | Per-finding triage | solo | solo | Skeptic |
| Review | Replan-vs-FIX | reviewer | **reviewer** | Skeptic |
| Promote | Four-way partition (PROMOTE/MERGE/DISCARD/TODO) | solo | solo | Skeptic |
| Promote | TODO disposition | solo | solo | Skeptic |
| Ship | Commit message / PR title + body | Operational — main model accepts draft | — | — |
| Ship | CI auto-fix `other` bail | Hardcoded user escalation | — | — |
| Cleanup gate | PR state polling + cleanup | No decision | — | — |

**Why these floors.** Divergence, new-plan acceptance and replan-vs-FIX were always panels until 4.0.0. They keep a reviewer floor, never solo, because their precondition is an already-surfaced load-bearing divergence or finding, and they fire rarely. Completion keeps its Verifier floor on evidence: 0 of 18 completion panels ever went to a revision round, and its value is independent *reproduction* of each criterion (`2026-06-29-decision-propose-ship-balanced-single-reviewer`). Scope, approach and whole-proposal run the full ladder: the revision rates that justify reviewing them (approach 17/25, whole-proposal 13/27, scope 7/22 panels) were measured on decisions that had **already failed** the solo predicate, which is exactly where this table sends a reviewer.
