# Scratchpad: backfill-followups-to-issues

## Balanced decisions 2026-08-22

- [reviewed — folded] scope check: single unit, skill + dogfood (Skeptic revise). Folded: `using-minerva/SKILL.md` is 9179/9216 bytes — 37 bytes headroom against a frozen budget, and `cross_surface` requires the skill token in that body; plan is to trim the `propose-ship-balanced` matrix row (514 bytes vs siblings ~250). Folded: state the internal plan→confirm→apply structure and justify one skill against the `lint`/`lint-fix`, `migrate`/`migrate-fix` pair precedent (one-time migration, not a recurring health-check; mirrors `migrate-fix`'s internal shape). Folded: point the completion Verifier at the `shipped`/`obsolete` calls, since the ~70 per-item judgments otherwise get no independent review under this rung's taxonomy. Folded: hard full-preview gate before ANY `gh issue create`; heterogeneity named explicitly; no `test_skill_snippets.py` extraction (issue #70). Corrected: 70 top-level bullets, not 74. Escalation to `propose-ship-auto` considered and declined — fail-open + user gate + targeted Verifier are three independent checks on the drop risk.
- [reviewed — folded] approach: option A, evidence-grounded triage failing open (Skeptic revise). Folded: the user-performed web-form class (~10 bullets in one file) had no disposition — added `manual` and `not-an-item` to make five, with `manual` grouped at the gate for one keep-or-drop call since no evidence source can verify a form submission. Folded: idempotency silently dropped the ledger the reused protocol depends on — backfill's tier-2 ledger is now the appended `## Backfill disposition` section, documented as a specialization of `github-issues.md`'s tier 2 rather than a silent divergence. Folded: append, never rewrite item lines, per `2026-06-02-constraint-promote-narrowed-never-overwrite`. Folded: atomization rule stated (one top-level bullet or one `##` subsection; alternatives-in-one-bullet stay one item) because the ledger anchor depends on it. Folded: gate batched per source file. Folded: `close-the-followups` item 1 — which proposes this very tool — resolves to `shipped (this run)` rather than filing an issue asking for the thing filing it. Rejected alternatives recorded in the proposal.
- [decided] whole-proposal soundness (solo gate): sound. Reuses the shipped `gh` protocol rather than restating it; read-only steps precede the gate; the one irreversible surface (issue creation) sits behind both the gate and the capability probe.

## Implementation notes 2026-08-22

- `using-minerva/SKILL.md` byte budget resolved as planned: the `propose-ship-balanced`
  matrix row was 514 bytes against sibling orchestrator rows at ~250. Trimmed to 260 and
  added the new row — 9179 → 9116, leaving 100 bytes of headroom.
- `tests/test_skill_budget.py::test_every_reference_pointer_resolves` caught real ambiguity:
  writing `minerva:promote`'s `references/github-issues.md` in a SKILL.md reads as a pointer
  into *this* skill's `references/` dir. Rephrased to name the owning skill instead.
- **Gap worth recording:** `REF_MENTION_RE = r"references/[A-Za-z0-9._-]+\.md"` matches that
  substring anywhere, so even a fully-qualified
  `plugins/minerva/skills/promote/references/github-issues.md` fails the check. The gate
  cannot express "another skill's reference file" — a cross-skill pointer is unrepresentable
  and must be phrased around. Same shape as
  [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]]: the gate's model of "a reference" is
  narrower than the reality it guards. Not fixed here (out of scope, and the workaround is
  one sentence), but it will recur for any skill that reuses another's protocol — which is
  now an established pattern rather than a one-off.
