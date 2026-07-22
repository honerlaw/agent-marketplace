# Proposal: skill-best-practices-audit

**Date**: 2026-07-21
**Status**: Draft

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

1. **Rubric.** Fetch Anthropic's current published guidance live at audit time
   — the skill-authoring best-practices documentation, agent-skills engineering
   material, and any model-behavior notes covering opus / sonnet / fable.
   Distill a numbered rubric; every dimension cites its source. Record source
   URLs and fetch date in the findings artifact so the audit is reproducible
   and datable.
2. **Fan-out review.** Dispatch fresh-context subagents via the Agent tool,
   each auditing a batch of 2–3 skills against the rubric and returning
   structured findings (dimension, evidence, severity, citation). Fresh
   contexts are deliberate: a cold reader judges frontmatter descriptions the
   way a cold model deciding whether to trigger would, avoiding the main
   context's familiarity bias.
3. **Synthesis.** The main model dedups findings, builds the 21-skill ×
   rubric-dimension coverage matrix, writes the cross-cutting triggering
   diagnosis for the two anchor failure classes — each diagnosis stating its
   mechanism, citing the guidance it rests on, and carrying an explicit
   confidence label (high / medium / speculative) — classifies every finding
   prose-fixable vs needs-a-mechanism, and writes `findings.md` in this work
   unit.
4. **Prose fixes.** Applied during `minerva:work`, confined to
   `plugins/minerva/skills/*/SKILL.md` (and per-skill `references/` files).
   Where a description's *meaning* changes, sync the site-catalog blurb in
   `pages/index.md` and the README entry per the catalog-sync constraint
   ([[010-constraint-minerva-skill-catalog-sync]],
   [[034-constraint-site-fourth-catalog-surface]]) — the site test only checks
   token presence, so semantic sync is on us. All contract tests stay green
   (≤9KB cores per [[036-constraint-skill-progressive-disclosure]], catalog
   surfaces, site catalog test). The gate for these fixes is the normal
   review → promote → ship flow — no extra per-fix ceremony.
5. **Follow-up seeds.** Written, not built: mechanism findings (e.g. a
   SessionStart-style hook, init-template Routing-section changes — explicitly
   out of scope here because the Routing section is a template-of-record with
   distribution-level blast radius per
   [[029-decision-routing-section-is-the-wiki-reading-protocol]] — description
   contract tests, mechanized rubric checks) and empirical validation of the
   triggering diagnosis via captured session transcripts / PostHog LLM
   analytics.

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
