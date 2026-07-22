# Proposal: skill-best-practices-audit

**Date**: 2026-07-21
**Status**: Shipped (2026-07-21)

## Goal

Audit all 21 minerva skills against current Anthropic best practices for skill
authoring and model behavior (opus / sonnet / fable), anchored on the two
observed failure classes: **ambient skill triggering** (skills that should
self-invoke from context — `using-minerva`, `replan`, `debug` — don't, and the
model works freehand) and **mid-lifecycle skill handoffs** (one skill is
supposed to invoke the next via the Skill tool and instead narrates or inlines
the work). Produce a triaged findings artifact in which every triggering
finding is classified **prose-fixable vs needs-a-mechanism** (hook, routing, or
contract test); apply the prose-fixable items in this unit; write mechanism
findings as follow-up seeds.

## Why

The triggering pain is real and already resisted one round of treatment:
minerva's knowledge corpus records prose-level fixes for exactly this class —
skills must call tools, not narrate ([[007-constraint-skills-must-call-tools-not-prose]]),
and handoffs must ride an observable inline argument
([[031-decision-phase-handoff-rides-observable-intake]]) — yet ambient and
handoff triggering still fail in live runs. That makes "polish the prose again"
an untrustworthy default; the audit's job is to determine, per finding, which
lever (prose vs mechanism) actually closes the gap, in the spirit of
[[030-pattern-rejected-alternative-reinvented-at-runtime]] (prose-only
prohibitions recur at runtime unless the executing surface enforces them).

Proactively: the 21 skills were written across many months while Anthropic's
published skill-authoring guidance evolved into the fable era. A broad-sweep
diff against current guidance catches drift before it compounds.

One audit input hypothesis (to confirm or refute, not assume): nearly every
minerva skill description *leads* with "Use when the user invokes
`minerva:X`…" — explicit-invocation phrasing first, ambient trigger phrases
buried mid-sentence — which may bias a cold model toward treating the skills as
slash-command-only.

## Approach

As shipped:

1. **Rubric.** Five Anthropic guidance sources fetched live 2026-07-21 (including
   fable-specific guidance, resolving the open question) and distilled into ten
   cited dimensions R1–R10 — recorded inline in `findings.md`.
2. **Fan-out review.** Eight fresh-context subagent reviewers audited themed batches
   of 2–3 skills each (full 21-skill coverage), returning structured findings plus
   cold-read trigger probes; the main model added a deterministic census
   (invocation-first ordering 17/21, three descriptions over the 1024-char limit).
3. **Synthesis.** 77 raw findings deduped into 12 clusters + 4 mechanism seeds;
   confidence-labeled diagnoses for the two anchor failures (ambient triggering:
   high — a listing-pipeline description drop plus invocation-first ordering;
   handoffs: medium-high — bare-prose handoffs vs. Skill-tool-explicit ones);
   one reviewer finding rejected as factually wrong. All in `findings.md`.
4. **Prose fixes.** 19 descriptions rewritten to the ambient-triggers-lead house
   style; ~60 body edits across 42 files (Skill-tool handoff phrasing,
   delegated-approver gate clauses, tone calibration, stale-content and anchor
   repairs, portability fixes, provenance cleanup); catalog surfaces semantically
   synced — including three stale rows caught only by verification-panel Skeptics;
   six self-introduced edit artifacts caught by fresh-context review and fixed.
   TOC additions and a governance dedup were declined with rationale. Suite green
   throughout (311 passed; three collection failures pre-existing on main).
5. **Seeds, not mechanisms.** followups.md carries the mechanism seeds (listing
   description-drop diagnosis + rendered-listing contract test, six-block sync,
   step-number coupling, ≤1024 test, handoff lint, enforcement layer, empirical
   validation) and declined/deferred items. Four knowledge entries promoted
   (046–049); overview refresh delegated to `minerva:synthesize`.

## Success criteria

- The coverage matrix in `findings.md` shows all 21 skills assessed on every
  rubric dimension — no skill and no dimension skipped.
- A cited, confidence-labeled diagnosis exists for each of the two anchor
  failure classes (ambient triggering, handoff triggering), and every
  triggering finding carries a prose-fixable vs needs-a-mechanism
  classification.
- Every prose-fixable finding is either applied to `plugins/minerva/skills/`
  or explicitly declined with a one-line rationale in `findings.md` — none
  left undispositioned. Catalog blurbs are semantically synced where
  description meaning changed, and the full test suite is green.
- `findings.md` records the rubric's source URLs and fetch date.
- Every mechanism finding exists as a follow-up seed; none is implemented in
  this unit.

## Open Questions

- Does fable-specific skill-authoring guidance exist publicly? If not, the
  rubric falls back to model-agnostic skill guidance plus release-note-level
  behavior notes, and `findings.md` states that fallback explicitly.
