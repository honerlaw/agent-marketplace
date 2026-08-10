# Knowledge overview
<!-- synthesis-watermark: 058 -->

A theme-grouped synthesis of the `.minerva/knowledge/` corpus — the LLM-owned
"concept pages" layer over the raw entries (Karpathy's LLM-wiki shape). Each theme is a
short narrative linking the entries that compose it; the entries themselves remain the
source of truth. Maintained by `minerva:synthesize`; see `## Limitations` for what the
synthesis watermark does and does not attest.

## The knowledge wiki: a navigable, machine-checked corpus

The largest arc in the corpus is minerva teaching itself to keep a *wiki*, not just a
pile of notes. The foundational decision is that knowledge is a **navigable wiki** —
a maintained `index.md` plus corpus-scan discovery, chosen over a heavier scheme
([[2026-06-02-decision-knowledge-wiki-navigability-layer]]). Entries connect through a
`## Related` block of wiki-links ([[2026-06-02-constraint-knowledge-cross-reference-convention]]).
That vocabulary began closed and no longer is: four terms stay reserved and exact —
`supersedes` / `superseded by` / `contradicts` / `builds on` — because their reciprocal is
a *claim* rather than a pointer, while every other label is a descriptive sentence and
reciprocates as `see also`. The closed set was the convention as designed; a sentence
saying what the edge *is* turned out to be the convention as practiced, in every corpus,
and refusing those had left roughly half of all cross-references one-way. The machinery
that edits these connections is tightly bounded: only the `## Related` / banner span is machine-
mutable, leaving bodies append-only ([[2026-06-02-constraint-promote-narrowed-never-overwrite]]).
That span invariant still holds exactly, but *who* applies it moved — promote no longer
edits any existing entry at all, and the reciprocal writes happen during default-branch
reconciliation ([[2026-08-05-decision-promote-add-only-reconcile-on-default]]).

The span model that defines those editable regions is **single-sourced** in
`scripts/knowledge_spans.py` so no tool re-derives it
([[2026-06-02-constraint-knowledge-span-model-single-sourced]]), and any tool deriving cross-ref
edges must be **fence-aware** — a `[[…]]` inside a code fence is an example, not a real
edge ([[2026-06-03-constraint-wiki-edge-derivation-fence-aware]]). That fence-awareness is itself
single-sourced: any fence-aware scan **imports the `FENCE_RE` grammar** (or a parser built
on it) rather than re-deriving it, for whatever corpus it walks
([[2026-06-11-constraint-fence-scans-import-fence-re]]). On top of these invariants
sits a deliberately phased tooling effort: a **deterministic lint detector** ships as the
CI gate first, with the LLM-judged skill deferred
([[2026-06-02-decision-phase-b-deterministic-lint-detector]]); the
`minerva:lint` skill then ships **read-only** (advisory for judged dimensions)
([[2026-06-03-decision-minerva-lint-read-only]]); and the gated fixer uses **two distinct safety
models** — entry-body byte-identity vs. index skeleton-preservation
([[2026-06-03-decision-knowledge-fix-two-safety-models]]).

The wiki's final layer is **synthesis** (Phase C): this very `overview.md` is a separate,
LLM-owned file carrying a new-scope-only `synthesis-watermark`, deliberately distinct from
`index.md` and invisible to the frozen detector/fixer — its content is advisory, never
CI-gated ([[2026-06-03-decision-synthesis-layer-separate-file-advisory]]). The `minerva:synthesize`
skill that maintains it was originally wired into the lifecycle orchestrators as a
self-gating post-promote / **pre-ship** step, so the overview rode the same PR that landed
new entries ([[2026-06-03-decision-synthesize-wired-post-promote-self-gating]]) — a position it no
longer holds. `overview.md` is a shared aggregate rewritten wholesale, which made it the
second-most-conflicted file in the repo once concurrent branches touched it; synthesis moved
out of the PR path entirely and now runs on the default branch as part of reconciliation
([[2026-08-05-decision-promote-add-only-reconcile-on-default]]). The wiki also has a
**consumer-facing API**: the agent-file Routing section *teaches the reading protocol*
(overview → index → entries on demand, with the reference and work tiers for operational
docs and historical reasoning), and stale sections get a gated refresh whose staleness
markers are derived from the template-of-record, never hardcoded
([[2026-06-03-decision-routing-section-is-the-wiki-reading-protocol]]).

Adopting this structure on a legacy corpus has its own tooling and lore. The read-only
**migration check** is the one surface that inventories what every other wiki tool is
blind to — files that don't match the `ENTRY_RE` naming convention read as a *false
clean* across the whole toolchain ([[2026-06-03-decision-migration-check-read-only-entry-re-blindspot]]).
The initial cross-reference **backfill** for the pre-convention entries was hand-authored
as a one-time unit (a per-edge disposition table, editor-routed writes, fixer-owned
reciprocals, and an honest standalone residual), with file-rename automation re-deferred
at zero live instances ([[2026-06-03-decision-related-backfill-hand-authored-rename-redeferred]]).
The same blind spot has a second face, one level in from the filename: an entry whose
type field is spelled `**Type:** x` or plain `Type: x` reads as having *no* type at all,
which cannot be placed in the index and surfaces as an error naming a mismatch the entry
does not have. The fix is to resolve authored metadata through a fallback chain ordered
most-deliberate-first — body field in any spelling, then frontmatter, then the filename —
so a fallback can only fill a gap and never override an author, with the last resort's
concordance *measured* (642 entries, two corpora, zero disagreements) before it is trusted
([[2026-08-09-pattern-read-authored-metadata-from-where-it-is]]).

That backfill also flushed out the **third instance of the fence trap**: the span editors
read entry 015's fenced `## Related` example as structure, crashing on (and silently
de-duping against) any edge into it — fixed with fence-aware header *location* that never
drops fenced content from the byte-identity guard
([[2026-06-03-bug-knowledge-edits-not-fence-aware]]).

## Skills, plugins, and catalogs: discovery and contracts

A second theme is the mechanics of the plugin itself — how skills come into existence and
stay trustworthy. Skills are **auto-discovered** from the `skills/` directory with no
manifest to update ([[2026-05-19-constraint-plugin-skills-auto-discovered-from-directory]]), but
the **marketplace registry is not** auto-discovered — `marketplace.json` and the README
must be updated by hand ([[2026-05-20-constraint-marketplace-plugin-registry-not-auto-discovered]]),
and the human-facing **skill catalogs span three doc surfaces** that must be kept in sync
([[2026-05-21-constraint-minerva-skill-catalog-sync]]). Beyond the repo's own registries,
**discoverability is mostly auto-crawl**: once a plugin repo is public, OSS-licensed, and
topic-tagged, the GitHub-crawling aggregators index it passively — the remaining manual
directories are human web-form submissions, and full-source vendor lists are a
maintenance fork to avoid ([[2026-06-10-pattern-plugin-discovery-mostly-auto-crawl]]). Three conventions keep skills honest: a
skill must **invoke tools directly, not narrate actions in prose**
([[2026-05-19-constraint-skills-must-call-tools-not-prose]]); a prose skill that wraps a
sibling Python tool does so **via the tool's importable API, anchored to the working-tree
root** — never the CLI, never CWD-relative
([[2026-06-03-constraint-skill-wraps-script-via-importable-api]]); and every skill-to-skill
handoff **names the Skill tool and the argument to pass** — bare prose ("run the X
protocol") licenses a literal-reading model to inline the target from memory, the
observed handoff failure mode ([[2026-07-21-constraint-handoffs-name-skill-tool]]). Coverage is enforced
structurally: **every skill carries a declarative contract** checked by an enumerating
test, so the skill set can never silently outrun its guarantees
([[2026-05-31-constraint-skill-structural-contracts]]). The static **site's skills catalog is a
fourth surface** — the only one enforced bidirectionally (presence *and* orphans), via a
bespoke enumerating test deliberately kept out of `cross_surface`
([[2026-06-10-constraint-site-fourth-catalog-surface]]). After the move to MkDocs, that fourth
surface's **source of truth is `pages/index.md`** (the MkDocs source the test reads
directly); the built `site/` is gitignored output, never the checked surface
([[2026-06-13-constraint-site-catalog-source-is-pages-index]]). The site's **chrome** is
customized through a `theme.custom_dir → overrides/` layer rather than by editing the
installed gitbook theme, with the dead search-results block CSS-hidden
([[2026-06-16-decision-site-gitbook-theme-overrides]]).

Two newer constraints govern the *size and CI reality* of the skill set. Skills keep
**≤9KB SKILL.md cores** with detail prose in on-demand per-skill `references/` files,
enforced by an enumerating byte-budget + pointer-integrity test; contract anchors follow
moved prose via a per-anchor `file` field
([[2026-06-11-constraint-skill-progressive-disclosure]]). And a trap that test itself fell into:
**new test modules are invisible to CI until appended to the workflow's explicitly
enumerated pytest list** — the failure mode is silent, so a green local run proves
nothing about CI ([[2026-06-11-constraint-ci-test-enumeration-explicit]]).

A 2026-07 audit of all 21 skills against Anthropic's current guidance turned this
theme into a **triggering discipline**. Descriptions follow a house style that
**leads with function and ambient trigger scenarios**, demoting the explicit
"invokes `minerva:X`" clause to last position and staying under the platform's
1024-character limit ([[2026-07-21-constraint-skill-description-house-style]]) — the audit's
census showed the invocation-first ordering correlated exactly with the skills that
failed to trigger ambiently. It also surfaced an open environmental defect: the
**listing pipeline drops some valid frontmatter descriptions** (lint and lint-fix
render as bare names), making ambient triggering structurally impossible for the
affected skills until the loader is fixed — no description polish can compensate
([[2026-07-21-bug-skill-listing-description-drop]]). And the catalog-sync constraint gained
an empirical sting: **semantic drift between skill text and the catalog surfaces
recurs even while a unit is actively scrubbing that exact staleness** — the
token-presence tests cannot see the class, so meaning-changing skill edits demand a
systematic sweep of all four surfaces
([[2026-07-21-pattern-catalog-semantic-drift-recurs]]).

## The lifecycle and its automation

A third theme covers the proposal→work→promote→ship lifecycle and the judgment baked into
its automation. `init`'s Routing-section detection **accepts both old and new directory
names** for backward compatibility ([[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]]).
The corpus distinguishes two documentation tiers: the present-tense
**`.minerva/reference/` operational-doc tier** is separate from the past-tense knowledge
tier ([[2026-05-22-decision-minerva-reference-tier]]). Review responsibility is partitioned —
**minerva owns the spec/knowledge lenses; code-review owns code quality**
([[2026-05-19-decision-review-lens-ownership]]). The auto-orchestrator gates **per decision and
fails closed**, rather than relying on an up-front sizing classifier
([[2026-05-31-decision-per-decision-skip-over-sizing-gate]]). That documented rejection proved
insufficient on its own — live runs re-invented the up-front ceremony ratification
anyway, producing the corpus's first `pattern` entry: **a rejected alternative documented
only in knowledge recurs at runtime**, so the prohibition must live in the executing
skill text and be test-anchored
([[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]]). Two newer decisions extend
the automation arc along the same action-over-self-judgment grain: phase-to-phase skill
handoffs ride an **observable intake** — an inline argument passed by the upstream skill —
never a self-judged "did the prior phase converge?" scan
([[2026-06-07-decision-phase-handoff-rides-observable-intake]]); and the consensus-panel machinery
was extracted along a **mechanism-vs-policy** line — standalone `minerva:round-table` owns
the panel mechanics (briefs, vote semantics, revision round, escalation) for any caller,
while orchestrators keep the policy: the quorum taxonomy, skip predicates, and all
run-level state ([[2026-06-10-decision-panel-mechanics-extracted-to-round-table]]). A **third
orchestrator** then joined the ladder by adjudication cost: `propose-ship-quick` runs the
identical lifecycle but has the **main model adjudicate every decision directly** — no
panel — for small low-risk changes, its fail-closed **escalation predicate** the
structural *inverse* of auto's skip predicate (deciding-alone is the default, escalation
the fail-closed exception) ([[2026-06-16-decision-propose-ship-quick-main-model-adjudication]]).
A **fourth** then split the difference: `propose-ship-balanced` runs the same lifecycle on
quick's main-model engine but dispatches a **single advisory reviewer** (a Skeptic, or a
Verifier at completion) at a fixed set of high-signal gates — scope, approach,
completion-verification — arbitrated inline, with no panel, no sequential Arbiter, and no
revision round. Its gate taxonomy is **telemetry-driven**: it spends independent scrutiny
only where past-run logs showed it changes outcomes, and a behavioral "load-bearing
critique" definition plus an anti-circularity escape (can't-confidently-adjudicate →
escalate, never self-confirm) keep the inline arbitration honest
([[2026-06-29-decision-propose-ship-balanced-single-reviewer]]). The four orchestrators now form
a full ladder — human gates · main model · one reviewer · panels. And the
project is honest about how much it trusts its own measurements: **behavioral skill-value
evals are provisional** — not CI-gated, their deltas not yet trusted
([[2026-05-31-decision-behavioral-evals-provisional]]).

Running that ladder in anger then exposed a defect class *below* the level of any policy:
skill text can name the right tool and still get the control flow wrong by leaving a
default unstated. Dispatch instructions pinned `subagent_type` and `model` but not the
execution mode, and the `Agent` tool backgrounds by default — so roughly half of all
observed dispatches returned a handle instead of a verdict, stranding protocols that
count votes in the same turn, and orchestrator runs visibly parked mid-lifecycle. The rule
that closed it generalizes the handoff constraints one level down: **an instruction must
pin every argument the next protocol step depends on**, and it is enforced by an
enumerating test rather than recorded and hoped for
([[2026-07-27-constraint-agent-dispatch-pins-execution-mode]]). The same investigation found the
lifecycle's *waits* built on unexamined constants, yielding the corpus's second `pattern`
entry: **match a wait's shape to what is actually being awaited** — CI completion is
duration-shaped and varies by two orders of magnitude across repos, while auto-merge
landing is queue-shaped and rightly keeps a constant — and **prefer the tool's own
blocking primitive** (`gh pr checks --watch`) over any interval you would have to invent,
since a hand-rolled poll loop must design around a bound, a rate limit, and an empty-set
edge case that the primitive simply does not have
([[2026-07-29-pattern-wait-shape-matches-what-is-awaited]]). Both entries share the older lesson's
grain: a convention that lives only in prose gets re-improvised at runtime.

Deferral has the same failure mode as prose. Reconciliation used to skip when another run
held the branch, on the reasoning that "the next run will pick it up" — but cleanup runs
once per work unit, so "the next run" is days away or never, and entries sat on the default
branch present but uncatalogued while the run that skipped them reported success. **Deferred
work needs a trigger, not an assumption**: name the thing that will actually pick it up, or
report it as outstanding so a person can ([[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]]).

## Concurrency: what shared state costs, and what hides in it

The newest arc runs orthogonally to the others. Everything above assumes one work unit at
a time; running several concurrently exposed a class of defect the earlier themes never
had to face, and the whole cluster came out of a single unit.

The precipitating observation was economic rather than theoretical. `index.md` appeared in
**78%** of recent commits on a heavy consumer repo, and its conflicts were *guaranteed*
rather than probable — every promote bumped a watermark on line 2, a same-line edit that
collides even when the two catalog lines land in different sections. The fix is structural:
a work-unit branch's `.minerva/` footprint must consist **entirely of newly-added files**,
because new files merge cleanly however many PRs are open. Promote became add-only, and
every aggregate and cross-entry write — catalog lines, watermark, reciprocal links,
banners, the overview — moved to a reconciliation pass that runs on the default branch
where there is exactly one writer ([[2026-08-05-decision-promote-add-only-reconcile-on-default]]).

Removing those conflicts removed something load-bearing that nobody had designed: the
textual collision was the *only* thing incidentally catching duplicate entry ids. A
knowledge entry is a **new file**, so two units picking the same number merge cleanly with
no conflict to notice — a near-miss on number 546 was caught purely because two appends
happened to land on adjacent lines. So allocation had to become a real backstop in the
same change, scanning across branches and treating "allocated" as *ever-added on any
reachable ref* rather than "present on some tip"
([[2026-08-05-constraint-knowledge-allocation-scans-across-branches]]).

Two more defects were hiding underneath, both of the same species: a data structure that
made a bad state *unrepresentable rather than detectable*. The wiki tooling keyed its
lookups `{nnn: entry}`, so on a duplicate the second file silently overwrote the first and
the linter reported a clean bijection over a corpus containing duplicates — invisible by
construction, in the one tool whose job was to see it. A consumer repo carries 65 such
groups. The rule is to group first and then **quarantine** duplicate ids from every
derived check and edit, because the surviving member is arbitrary and anything computed
from it names the wrong file ([[2026-08-05-constraint-nnn-keyed-lookups-hide-duplicates]]).

The sharpest lesson came from the fix that *didn't* work. Distinguishing "not catalogued
yet" from "genuinely drifted" was first modelled as a scalar watermark floor — which
quietly assumes records reconcile in id order. They do not: units merge whenever their PRs
land. Unit A takes 050, B takes 051, B merges and reconciles first, and A's entry then
falls *below* the floor — reddening an innocent branch and, worse, emitting no pending
signal, which is precisely what gates reconciliation, so the entry would never be
catalogued at all. Silent and permanent. The replacement reads state per-record instead of
from a threshold ([[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]]). Two things
about how it was found are worth keeping: it had already passed 413 green tests **and** a
3/3 completion-verification panel, because the tests encoded the same wrong assumption the
design did — and the same shape recurred one file over in the reconciliation guard, where
a `gh pr list` check preceding a branch create is a check-then-act race rather than a lock.
That one is fixed by letting git's atomic ref update *be* the lock: a non-forced push, where
exactly one of two concurrent runs wins and the loser exits cleanly
([[2026-08-05-pattern-read-then-act-is-not-a-lock]]).

Read together, this cluster is one lesson in four shapes: **shared mutable state is where
concurrency bugs go to hide**, and the ones that survive testing are the ones where the
test and the design share an assumption.

## Git worktrees and promote/scratchpad mechanics

The smallest theme is hard-won operational lore about git and the lifecycle's bookkeeping.
`.minerva/worktrees/` must be added to `.gitignore` **before** running `git worktree add`
([[2026-05-19-decision-gitignore-before-worktree]]), and minerva addresses worktrees by **`.minerva/worktrees/<NNN-slug>/`-prefixed
paths and `git -C`, not `EnterWorktree`** — that tool only reliably enters worktrees
under `.claude/worktrees/` ([[2026-05-20-constraint-enter-worktree-absolute-paths]]), the decision
to drop `EnterWorktree` outright recorded in
[[2026-06-27-decision-worktree-addressing-no-enterworktree]]. Two entries capture promote's state
handling: a fixed bug where the **idempotency check missed the old scratchpad marker
format** ([[2026-05-19-bug-promote-idempotency-check-misses-old-marker]]), and the constraint that
the **post-promote scratchpad's one-line marker is the canonical empty state** downstream
skills expect ([[2026-05-19-constraint-post-promote-scratchpad-canonical-empty]]).

## Limitations

This overview is **advisory** — a navigation aid, never a CI-gated artifact. Its
synthesis watermark (`058`) is a **new-scope-only floor**:

- it attests which entries had been *added* at synthesis time (max NNN reflected), and
  the `minerva:synthesize` signal flags any entry with a higher NNN as un-synthesized;
- it does **not** detect in-place edits to already-synthesized entries (a later
  `## Related` rewiring, a supersession banner, or an appended body) — that drift is a
  judgment call for the next synthesis, not something the watermark can show;
- it attests synthesis **intent, not body content** — a watermark at the corpus max with
  a stale narrative below it is not mechanically detectable.

This overview was refreshed during `051-resolve-entry-type-tolerantly`'s reconciliation,
reflecting the corpus through entry `058`, on two un-synthesized entries (`057`, `058`).
The count was small; the reason to refresh was not. It **corrected a claim the corpus had
falsified without any entry recording it**: the `## Related` relationship vocabulary is no
longer closed. That change shipped as a direct PR with no work unit behind it, so no entry
asserts it and the watermark could never have flagged it — the third bullet above, in a
form worse than in-place drift, because there is nothing to read. Entry `058` is adjacent
(it fixes the sibling defect in the same parser) but does not state it. If a behavioural
change to the wiki model ships again without a work unit, the overview is the only place
it can be recorded, and only if someone remembers.

The prior refresh ran in the `049-add-only-knowledge-writes` work unit, reflecting the
corpus through entry `056`, on five un-synthesized entries (`052`–`056`). That refresh
also **corrected two narratives the new entries falsified** — the claim that promote edits
neighbour entries' `## Related` spans, and the claim that synthesis runs pre-ship so the
overview rides the same PR. Both were true when written and are not now; neither is the
kind of drift the watermark can detect. It was the first refresh to run on the **default
branch** as part of reconciliation rather than inside a work-unit PR. Earlier refreshes:
`046-skill-best-practices-audit` (through `049`, on entries `046`–`049`);
`045-add-propose-ship-balanced` (through `045`, on entries `043`/`044`/`045`);
`042-add-propose-ship-quick` (through `042`, on
entries `037`/`038`/`042`); `035-skill-progressive-disclosure` (through `036`);
`033-extract-round-table` (through `033`), `030-no-ceremony-ratification` (through `030`,
opening the previously-empty Patterns bucket), `027-related-backfill` (through `028`, on
the explicit drift rationale of a 16-block `## Related` reshape),
`025-wire-synthesize-into-orchestrators` (through `025`), and the original synthesis in
`024-synthesize-skill` (through `023`). Any entry promoted after
this will correctly show as `unsynthesized` until the next refresh — the advisory signal
working as intended.
