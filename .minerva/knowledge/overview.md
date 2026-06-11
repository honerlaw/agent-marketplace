# Knowledge overview
<!-- synthesis-watermark: 033 -->

A theme-grouped synthesis of the `.minerva/knowledge/` corpus — the LLM-owned
"concept pages" layer over the raw entries (Karpathy's LLM-wiki shape). Each theme is a
short narrative linking the entries that compose it; the entries themselves remain the
source of truth. Maintained by `minerva:synthesize`; see `## Limitations` for what the
synthesis watermark does and does not attest.

## The knowledge wiki: a navigable, machine-checked corpus

The largest arc in the corpus is minerva teaching itself to keep a *wiki*, not just a
pile of notes. The foundational decision is that knowledge is a **navigable wiki** —
a maintained `index.md` plus corpus-scan discovery, chosen over a heavier scheme
([[017-decision-knowledge-wiki-navigability-layer]]). Entries connect through a
`## Related` block of wiki-links drawn from a **closed relationship vocabulary**
([[015-constraint-knowledge-cross-reference-convention]]), and the machinery that edits
those connections is tightly bounded: promote may touch only the `## Related` / banner
span, leaving bodies append-only ([[016-constraint-promote-narrowed-never-overwrite]]).

The span model that defines those editable regions is **single-sourced** in
`scripts/knowledge_spans.py` so no tool re-derives it
([[019-constraint-knowledge-span-model-single-sourced]]), and any tool deriving cross-ref
edges must be **fence-aware** — a `[[…]]` inside a code fence is an example, not a real
edge ([[023-constraint-wiki-edge-derivation-fence-aware]]). On top of these invariants
sits a deliberately phased tooling effort: a **deterministic lint detector** ships as the
CI gate first, with the LLM-judged skill deferred
([[018-decision-phase-b-deterministic-lint-detector]]); the
`minerva:lint` skill then ships **read-only** (advisory for judged dimensions)
([[020-decision-minerva-lint-read-only]]); and the gated fixer uses **two distinct safety
models** — entry-body byte-identity vs. index skeleton-preservation
([[022-decision-knowledge-fix-two-safety-models]]).

The wiki's final layer is **synthesis** (Phase C): this very `overview.md` is a separate,
LLM-owned file carrying a new-scope-only `synthesis-watermark`, deliberately distinct from
`index.md` and invisible to the frozen detector/fixer — its content is advisory, never
CI-gated ([[024-decision-synthesis-layer-separate-file-advisory]]). The `minerva:synthesize`
skill that maintains it is wired into **both lifecycle orchestrators** as a self-gating
post-promote / pre-ship step — delegation, not a panel decision — so the overview refreshes
as part of the same PR that lands new entries
([[025-decision-synthesize-wired-post-promote-self-gating]]). The wiki also has a
**consumer-facing API**: the agent-file Routing section *teaches the reading protocol*
(overview → index → entries on demand, with the reference and work tiers for operational
docs and historical reasoning), and stale sections get a gated refresh whose staleness
markers are derived from the template-of-record, never hardcoded
([[029-decision-routing-section-is-the-wiki-reading-protocol]]).

Adopting this structure on a legacy corpus has its own tooling and lore. The read-only
**migration check** is the one surface that inventories what every other wiki tool is
blind to — files that don't match the `ENTRY_RE` naming convention read as a *false
clean* across the whole toolchain ([[026-decision-migration-check-read-only-entry-re-blindspot]]).
The initial cross-reference **backfill** for the pre-convention entries was hand-authored
as a one-time unit (a per-edge disposition table, editor-routed writes, fixer-owned
reciprocals, and an honest standalone residual), with file-rename automation re-deferred
at zero live instances ([[027-decision-related-backfill-hand-authored-rename-redeferred]]).
That backfill also flushed out the **third instance of the fence trap**: the span editors
read entry 015's fenced `## Related` example as structure, crashing on (and silently
de-duping against) any edge into it — fixed with fence-aware header *location* that never
drops fenced content from the byte-identity guard
([[028-bug-knowledge-edits-not-fence-aware]]).

## Skills, plugins, and catalogs: discovery and contracts

A second theme is the mechanics of the plugin itself — how skills come into existence and
stay trustworthy. Skills are **auto-discovered** from the `skills/` directory with no
manifest to update ([[004-constraint-plugin-skills-auto-discovered-from-directory]]), but
the **marketplace registry is not** auto-discovered — `marketplace.json` and the README
must be updated by hand ([[009-constraint-marketplace-plugin-registry-not-auto-discovered]]),
and the human-facing **skill catalogs span three doc surfaces** that must be kept in sync
([[010-constraint-minerva-skill-catalog-sync]]). Beyond the repo's own registries,
**discoverability is mostly auto-crawl**: once a plugin repo is public, OSS-licensed, and
topic-tagged, the GitHub-crawling aggregators index it passively — the remaining manual
directories are human web-form submissions, and full-source vendor lists are a
maintenance fork to avoid ([[032-pattern-plugin-discovery-mostly-auto-crawl]]). Two conventions keep skills honest: a
skill must **invoke tools directly, not narrate actions in prose**
([[007-constraint-skills-must-call-tools-not-prose]]), and a prose skill that wraps a
sibling Python tool does so **via the tool's importable API, anchored to the working-tree
root** — never the CLI, never CWD-relative
([[021-constraint-skill-wraps-script-via-importable-api]]). Coverage is enforced
structurally: **every skill carries a declarative contract** checked by an enumerating
test, so the skill set can never silently outrun its guarantees
([[012-constraint-skill-structural-contracts]]).

## The lifecycle and its automation

A third theme covers the proposal→work→promote→ship lifecycle and the judgment baked into
its automation. `init`'s Routing-section detection **accepts both old and new directory
names** for backward compatibility ([[001-decision-init-routing-detection-accepts-old-and-new-names]]).
The corpus distinguishes two documentation tiers: the present-tense
**`.minerva/reference/` operational-doc tier** is separate from the past-tense knowledge
tier ([[011-decision-minerva-reference-tier]]). Review responsibility is partitioned —
**minerva owns the spec/knowledge lenses; code-review owns code quality**
([[006-decision-review-lens-ownership]]). The auto-orchestrator gates **per decision and
fails closed**, rather than relying on an up-front sizing classifier
([[014-decision-per-decision-skip-over-sizing-gate]]). That documented rejection proved
insufficient on its own — live runs re-invented the up-front ceremony ratification
anyway, producing the corpus's first `pattern` entry: **a rejected alternative documented
only in knowledge recurs at runtime**, so the prohibition must live in the executing
skill text and be test-anchored
([[030-pattern-rejected-alternative-reinvented-at-runtime]]). Two newer decisions extend
the automation arc along the same action-over-self-judgment grain: phase-to-phase skill
handoffs ride an **observable intake** — an inline argument passed by the upstream skill —
never a self-judged "did the prior phase converge?" scan
([[031-decision-phase-handoff-rides-observable-intake]]); and the consensus-panel machinery
was extracted along a **mechanism-vs-policy** line — standalone `minerva:round-table` owns
the panel mechanics (briefs, vote semantics, revision round, escalation) for any caller,
while orchestrators keep the policy: the quorum taxonomy, skip predicates, and all
run-level state ([[033-decision-panel-mechanics-extracted-to-round-table]]). And the
project is honest about how much it trusts its own measurements: **behavioral skill-value
evals are provisional** — not CI-gated, their deltas not yet trusted
([[013-decision-behavioral-evals-provisional]]).

## Git worktrees and promote/scratchpad mechanics

The smallest theme is hard-won operational lore about git and the lifecycle's bookkeeping.
`.minerva/worktrees/` must be added to `.gitignore` **before** running `git worktree add`
([[005-decision-gitignore-before-worktree]]), and `EnterWorktree` **does not redirect
absolute paths** — a sharp edge when scripting inside a worktree
([[008-constraint-enter-worktree-absolute-paths]]). Two entries capture promote's state
handling: a fixed bug where the **idempotency check missed the old scratchpad marker
format** ([[002-bug-promote-idempotency-check-misses-old-marker]]), and the constraint that
the **post-promote scratchpad's one-line marker is the canonical empty state** downstream
skills expect ([[003-constraint-post-promote-scratchpad-canonical-empty]]).

## Limitations

This overview is **advisory** — a navigation aid, never a CI-gated artifact. Its
synthesis watermark (`033`) is a **new-scope-only floor**:

- it attests which entries had been *added* at synthesis time (max NNN reflected), and
  the `minerva:synthesize` signal flags any entry with a higher NNN as un-synthesized;
- it does **not** detect in-place edits to already-synthesized entries (a later
  `## Related` rewiring, a supersession banner, or an appended body) — that drift is a
  judgment call for the next synthesis, not something the watermark can show;
- it attests synthesis **intent, not body content** — a watermark at the corpus max with
  a stale narrative below it is not mechanically detectable.

This overview was refreshed in the `033-extract-round-table` work unit, reflecting
the corpus through entry `033`. The refresh was invoked on three un-synthesized entries
(`031`, `032`, `033`). Prior refreshes: `030-no-ceremony-ratification` (through `030`,
opening the previously-empty Patterns bucket), `027-related-backfill` (through `028`, on
the explicit drift rationale of a 16-block `## Related` reshape),
`025-wire-synthesize-into-orchestrators` (through `025`), and the original synthesis in
`024-synthesize-skill` (through `023`). Any entry promoted after
this will correctly show as `unsynthesized` until the next refresh — the advisory signal
working as intended.
