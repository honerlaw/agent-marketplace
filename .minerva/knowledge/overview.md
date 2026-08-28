# Knowledge overview

A theme-grouped synthesis of the `.minerva/knowledge/` corpus — the LLM-owned
"concept pages" layer over the raw entries (Karpathy's LLM-wiki shape). Each theme is a
short narrative linking the entries that compose it; the entries themselves remain the
source of truth. Maintained by `minerva:synthesize`; see `Three later findings extend the same cluster, and each is a case where the *check itself*
was the thing that could not fail.

**A distinguished state inferred from the shape of the outputs is usually the resting
state.** A fixer refused index rewrites in two ways — wholesale, and per-entry — and only
the first should suppress the companion pass that writes reciprocal links. The obvious test
read it off the return values: index unchanged *and* refusals present. That signature is not
the failure; it is what a healthy canonical corpus looks like on every subsequent run, once
a benign standing refusal coexists with an index that no longer changes. Gating on it would
have discarded legitimate edits forever after — the very half-reconciled corpus the fix
existed to prevent, arrived at from the other side. The trap passes every test written
against a fresh fixture, because the collision only appears at equilibrium, which is exactly
when nobody is watching ([[2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state]]).

**Repeated blocks that look like copy-paste may be diverging on purpose.** Six skills carry
a `## Target resolution` block held together by a plea to keep them in sync, which reads as
pure duplication and invites a byte-identity test. They are not copies: one has three steps
because its no-argument mode means something different, and two more have materially
different terminal cases. Normalizing enough to make them match would have erased everything
the test was meant to check. Read the copies before choosing the invariant — when they
differ deliberately, the enforceable property is the intersection, the specific clauses whose
absence causes bugs, not the whole text
([[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]]).

**A safety guard written as a denylist fails open on everything its author did not recall.**
The guard stopping the snippet runner from executing mutating commands shipped as an
enumerated list; review found ten real gaps in it on first inspection, including a GraphQL
mutation that bypassed the method-flag checks entirely. Inverted to an allowlist of
read-only verbs, all ten close by construction. The denylist's inadequacy is unobservable
by definition — you cannot notice the entry you did not think of — and the surface it
guards grows independently of the list. Enumerate the safe set whenever the unsafe set is
open-ended or belongs to someone else
([[2026-08-22-pattern-a-denylist-safety-guard-fails-open]]).

Three later entries turn that cluster from a set of cautions into a **procedure**. Reading an
assertion cannot establish that it can fail — only removing its subject can, so the discipline is
a deletion pass **per assertion**, not per file. Two contract tests written by an author who had
just read the scoping rule still contained five vacuous assertions, three of them inside tests
written specifically to prevent this class, one guarding a finding a reviewer had raised minutes
earlier; all five read correctly by eye and were caught only by deletion, and four sat beside
assertions that were sound ([[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]]).

The other two are about the *shape* of a check rather than its strength. Deriving a set from the
corpus is grounded and still **bounded**: a test that enumerated affected skills from the three
orchestrators' phase protocols reported complete coverage while missing `minerva:synthesize`,
which is reached at two hops and therefore named by no protocol — "I asked the corpus" is not "I
asked the whole corpus", and a coverage claim inherits its derivation's horizon
([[2026-08-28-pattern-a-coverage-claim-inherits-its-derivations-horizon]]). Worse than a bounded
registry is one whose **arity** is wrong: pairing each site with a single attribute does not
merely miss a second, it asserts there isn't one, so the code, the test and the reader all agree
on an incomplete picture. The repair that holds is deleting the dimension rather than adding the
row — making the wrong state unrepresentable instead of recording one more true fact
([[2026-08-28-pattern-a-registry-with-the-wrong-arity-manufactures-agreement]]).

## Limitations` for what the
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

The type *vocabulary* moved for the same reason the parser did — because authors had
already moved it. Four values (`decision` / `bug` / `pattern` / `constraint`) were
hardcoded across the tooling and four skill docs, and entries declaring `reference` were
refused indefinitely, since a line whose declared type has no section cannot be placed.
Admitting `## References` as a fifth section ratifies practice rather than inventing
policy, and it lands inertly: the section is **appended, never interleaved**, which is
the only position leaving every existing index byte-identical, and an unused section
renders as its bare header ([[2026-08-09-decision-reference-is-a-fifth-entry-type]]).

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

Reuse between skills has since exposed a limit in that same guard. The pointer check finds
mentions with an unanchored `references/<file>.md` pattern and resolves each against the
**citing** skill, which was exactly right while every skill's references were private to it.
Once `minerva:backfill-followups` began delegating its `gh` mechanics to `minerva:promote`'s
protocol rather than restating them — the pattern to prefer, not an exception — that shape
became unrepresentable: even a fully-qualified path to the sibling's file still contains the
substring, resolves locally, and dangles. A cross-skill reference now has to be phrased
around, naming the owning skill and the bare filename
([[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]]).

That constraint has since been **dissolved rather than accommodated**. The gate now reads two
pointer forms: a bare `references/<f>.md` resolves under the citing skill as before, and a
qualified `plugins/minerva/skills/<skill>/references/<f>.md` resolves under the skill it
names. The ordering is the whole fix — qualified mentions are matched and stripped *before*
the bare pass, because a qualified path literally contains a bare-looking tail and
attributing that tail locally was the defect. Two properties are deliberately kept: the
orphan check stays local, so a reference file must still be pointed at from its own
`SKILL.md` or it becomes undiscoverable from the skill that owns it; and qualification is no
escape hatch, so a qualified pointer to a missing file still dangles and still fails. The
standing guidance flips accordingly — cite a sibling's protocol by path rather than
restating it, because copies drift silently while a pointer fails loudly
([[2026-08-22-decision-qualified-cross-skill-reference-pointers]]).

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

That honesty was later vindicated in a sharper way than intended. The validation spike
finally ran, and the first half of its answer was that the control had never been a control
at all: both arms shelled out to the *identical* command, so every delta the runner had
reported compared a configuration against itself. A real control does exist — point
`--plugin-dir` at a copy of the plugin with the one skill directory removed — and with it
the second half of the answer is a **no**: on a 5-point rubric the treatment-minus-control
delta came out at +0.5 against a within-arm standard deviation of 0.96, roughly 0.9 standard
errors, needing ~59 runs per arm to resolve. So the methodology now measures something, and
that something is still smaller than the noise; per-skill backfill stays blocked, for a new
reason. The recommended move is to cut variance — a paired head-to-head judge removes
judge-scale drift — rather than pay for 59x the runs
([[2026-08-22-decision-behavioral-eval-control-real-signal-not-yet]]).

The spike also produced a small, general lesson about degenerate cases. Its first live run
failed loudly because the new control was being built from the repo root rather than the
plugin root, and would have removed nothing — silently reproducing the very no-op it
replaced. It refused instead, because the code that builds a control arm raises when the
skill it is meant to suppress is absent. The old control degraded to noise in silence; the
new one declines to run.

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

One automation premise turned out to be false on the build it ran on. The remedy for backgrounded
dispatches was to pin `run_in_background: false` in every dispatch instruction, enforced over five
registered sites — but that rests on the `Agent` tool accepting the parameter, and its schema
exposes only `description` / `isolation` / `model` / `prompt` / `subagent_type`. Reviewer gates
dispatched with the pin still backgrounded and still parked the run, while the enforcing test went
on passing: the test checks that the instruction says the words, not that the platform honours
them ([[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]]).

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

A later entry extends the cluster from *two writers* to *one writer and its own guard*.
When `minerva:promote` gained the ability to file deferred TODOs as GitHub issues, it needed
the same check-before-write `minerva:ship` uses. The first draft read GitHub's **search
index** — which is not updated synchronously with creation, so the guard was strongest where
it mattered least (a re-run days later, against a settled index) and blindest exactly where
it mattered most (a retry seconds after a partial failure, when the just-created issue is not
yet searchable). The general shape: **when a write and its guard travel through different
consistency domains, the guard is weakest in the window right after the write** — true of a
search index, a CDN, a read replica, a cache. The fix was ordering rather than timing: check
the source you control first (the run's own record, then a local file), and demote the
eventually-consistent one to a backstop for the cases only it can see
([[2026-08-22-pattern-a-just-written-index-is-not-a-read-back-guarantee]]).

Removing those conflicts removed something load-bearing that nobody had designed: the
textual collision was the *only* thing incidentally catching duplicate entry ids. A
knowledge entry is a **new file**, so two units picking the same number merge cleanly with
no conflict to notice — a near-miss on number 546 was caught purely because two appends
happened to land on adjacent lines. So allocation had to become a real backstop in the
same change, scanning across branches and treating "allocated" as *ever-added on any
reachable ref* rather than "present on some tip"
([[2026-08-05-constraint-knowledge-allocation-scans-across-branches]]).

That backstop has since been **removed by removing its premise**. An id only needs
allocating while it is scarce, and a sequential number is scarce only because someone
chose it to be. Entry ids are now dates, and identity is the full `YYYY-MM-DD-type-slug`
stem ([[2026-08-10-decision-date-ids-make-identity-the-path]]). Nothing is negotiated —
a date is read off the clock — and the guard moves out of a script and into the
filesystem: two branches producing an identical stem produce the *same path*, which git
refuses to merge. The failure mode inverts from silent to loud, which is the whole
argument. It also makes a rule out of what used to be a defect — **several entries
sharing a leading token is now ordinary**, so the duplicate-id check and its quarantine
were deleted rather than adapted, and every scalar floor over ids went with them: a date
is not totally ordered, so no watermark can express progress even in principle.

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
([[2026-08-05-pattern-read-then-act-is-not-a-lock]]) — subject to a precondition that later
turned out to be load-bearing. That lock is a lock over one **ref**, not over the resource
it was meant to protect. When a consumer repo added a CI job that reconciles on merge,
pushing a unique branch per run so its own runs could not collide, there was suddenly no
contended ref: nothing rejected the loser, two writers could edit `index.md`, and the
absence of the exclusion produced no error at all. The fix was not to make the second
writer share the ref but to detect it and have the first stand down — where two writers
cannot be serialised, only one of them runs
([[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]]).

The ref/resource gap then turned up a third time, in the opposite direction. A pre-flight
check for concurrent work needed an honest answer to "if a check-then-act read is not a
lock, what is?", and named the obvious one: `git worktree add -b <date-slug>` creates a
branch ref, and a ref create is atomic. True, and beside the point — that serializes two
sessions choosing the same **slug**, while what collides is the **goal**. A slug is a
summary of intent, and two summarizations of one idea rarely match, so for the case that
motivated the whole feature there is no atomic backstop at all. The lock sits on a
**derived** name while the contention sits on the **source** it was derived from, and a
derivation that is not injective breaks the correspondence in whichever direction it is
non-injective ([[2026-08-24-pattern-a-lock-on-a-derived-name-does-not-cover-the-source]]).
The remedy was not a better lock but writing the residual risk into the protocol itself —
a guard whose limits go undocumented is worse than none, because the next reader extends
it rather than replacing it.

That check also had to reach *outside* the repo, to sibling Claude sessions that may be
designing the same work with nothing yet on disk — the longest blind window in any run.
Designing that fan-out before running the enumeration proved a mistake: `ListAgents`
returns the whole fleet, and on one machine that was 32 peers of which 27 could never
answer (offline, or cloud sessions that receive but cannot reply). Filtering on liveness,
reply capability, and a project-name prefix took 32 candidates to **0**, which is the
intended common case rather than a degenerate one
([[2026-08-24-reference-listagents-returns-the-whole-fleet]]). The listing carries name,
kind and liveness but never intent, so overlap can only be learned by asking — and a reply
that drains at the peer's next tool round means silence has to count as `unknown`, never
as `clear`.

Read together, this cluster is one lesson in several shapes: **shared mutable state is where
concurrency bugs go to hide**, and the ones that survive testing are the ones where the
test and the design share an assumption — or where the guarantee was written down as a
property of the resource when it was only ever a property of the ref, or of a name derived
from it.

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

Three later entries turn the same lore into rules about *what a worktree is*, and each was
found by a tool reading one and meaning the other. A path that reaches **into**
`.minerva/worktrees/` must anchor on the **primary checkout** — `git rev-parse
--show-toplevel` returns the *linked* worktree from inside one, and the `--git-common-dir`
replacement prints a relative `.` from the primary checkout unless wrapped in
`cd … && pwd` ([[2026-08-28-constraint-worktree-reaching-paths-anchor-to-the-primary-checkout]]).
The complementary trap is scope rather than anchoring: because `.minerva/work/` is
*committed*, every linked worktree carries the whole history, so a glob through
`.minerva/worktrees/*/` sees every unit in the project — reachability through a worktree is
evidence about the repository, never about that worktree
([[2026-08-28-bug-a-worktree-glob-sees-every-unit-in-the-project]]). And the branch side has
its own two-directional hazard: `git branch --merged` misses a squash-merged branch *and*
counts a freshly created zero-commit branch as merged, so shipped-ness comes from the
merged-PR query with the git check as a fallback, never a union of the two
([[2026-08-28-constraint-git-branch-merged-is-wrong-in-both-directions]]).

The sharpest worktree hazard is that minerva, developing itself, **loads itself from the wrong
tree**. `~/.claude/plugins/minerva` symlinks to the primary checkout, so every skill snippet's
script resolution — and the harness's own loading of `SKILL.md` prose — reaches that checkout's
current branch rather than the worktree being edited. Adding a function fails loudly with an
`ImportError`; *modifying* one imports cleanly and runs the old behavior, so a change gets
"verified" against code nobody wrote. A guard now refuses rather than warns, comparing the whole
scripts directory because naming one module left both sibling scripts and transitive imports
unchecked. Note this entry anchors to the **current** tree where its neighbour anchors to the
primary one: the two answer different questions, and reading either alone produces the wrong
anchor half the time ([[2026-08-28-constraint-a-skill-snippet-runs-the-primary-checkouts-code]]).

## Silent success: when a tool reports done and did nothing

The corpus's newest entries share a shape distinct from the concurrency cluster. There the
danger was two writers colliding; here it is a **single** operation that completes, exits
zero, and reports success while having accomplished nothing — leaving no failure for
anyone to investigate.

Three instances, found within one migration:

- `git log --follow --diff-filter=A` returns **empty for every renamed path**, because
  `--follow` reports a creation as a rename and the add-filter then discards it. The
  command succeeds and prints nothing; the caller read that as "this path has no history"
  and skipped it. Five of 102 paths would have been dropped from a migration reporting
  success ([[2026-08-10-bug-git-follow-and-diff-filter-a-cancel-out]]).
- A guard excluding `.minerva/worktrees` by **absolute** path matches every file in the
  repo when the tool runs inside a worktree — which is where minerva always runs. The run
  renamed 107 paths and rewrote 0 references, and said so
  ([[2026-08-10-bug-absolute-path-guard-matches-everything-inside-a-worktree]]).
- A test written as `assert "x" in prose` **cannot fail** once `x` is deleted, because
  deleting a thing does not touch the text mentioning it. The invariant pinning promote's
  use of the id allocator stayed green after the allocator was removed, attesting a
  configuration that no longer existed
  ([[2026-08-10-pattern-presence-assertions-rot-into-green-lies]]).

The common lesson is that **an empty or zero result is not self-evidently correct**. Each
case had a signal available — a count of zero rewrites beside 107 renames, an empty git
result distinguishable from an unanswerable query, an assertion that could have
dereferenced its subject instead of grepping for its name — and in each the check that
would have caught it was cheaper than the one that was written. Two of the three had
survived a multi-agent design review, which is the sharpest point: review reads intent,
and these failures are invisible in intent. They surface only when the thing is run and
its output is read sceptically.

A second pass over the same tooling found a harder variant, where the thing reporting
success is the **verifier itself**:

- `knowledge_rename` could not see an entry referenced by *path* rather than by wikilink,
  so 182 references broke in one migration — and `knowledge_lint` reported the corpus
  clean on **both** sides, because the linter's edge model has the same blind spot as the
  writer's. Two checks whose job was to confirm a migration had worked were likewise
  wrong: a verification grep for `[[0-9]{3,}-` matched the `2026` of every correctly
  migrated link (6,005 hits against 26 real leftovers), and an orphan query keyed on an id
  prefix that under date ids *is the date* collapsed 642 entries into ~85 buckets and
  reported 0 orphans against 14 ([[2026-08-11-pattern-a-gate-blind-to-what-it-checks]]).
- The linter and the fixer derived `## Related` edges from **two different regexes**,
  above a comment asserting they were single-sourced. Every line with trailing content
  diverged, so 18 of 41 findings were neither planned nor refused, and the convergence
  loop ran forever while the fixer printed "corpus clean". The same shape, independently:
  one bare `\d{3,}` id pattern among many sharing a grammar made the migration
  non-idempotent for work directories
  ([[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]]).

This sharpens the cluster's thesis. A zero result is suspect; **a green gate is suspect in
exactly the same way**, and worse, because a green check ends the investigation where an
absent one prompts a manual look. A gate is evidence only over the forms it models, so
when its model is inherited from — or merely coincides with — the model of the thing it
validates, a clean run carries no information about the shared blind spot. Every instance
above was found by running the tool on a real corpus and reading the output, never by the
gate. Two practical rules follow: an invariant between two pieces of code is enforced by a
shared *implementation* or not at all (a comment describing it is documentation
substituting for verification), and when a change adds a form the gate cannot see, the
coverage has to come from a fixture that **fails before the fix** — on the repo where these
were fixed, 0 of 62 entries exhibited the divergent shape, so a clean lint run proved
precisely nothing.

A third pass closed the loop on *why* these keep recurring, and the answer is uncomfortable:
the recognizer is usually a hand-written list of the shapes someone believed the data took.

- `minerva:promote`'s idempotency check matched **one** post-promote marker string. The
  corpus holds **eight**, so on 16 of 51 units the check failed open — promote re-ran a
  mutating pass and could duplicate knowledge entries. It had been reported in May with a
  prescribed fix that was never applied, while the affected set grew from 3 units to 16 as
  each promote author reworded the marker. The sharper finding is what happened next:
  enumerating those spellings **failed three times in one sitting**, once producing a format
  that exists nowhere — an artifact of `head -1` over a file with no trailing newline
  splicing two units' markers together, which was then pinned in a fixture asserting it was
  real. Both errors were caught by review, never by rereading
  ([[2026-08-11-pattern-the-enumeration-is-what-fails]]).
- The same shape one layer up: fixing the check in `promote` left **eight other files**
  carrying their own inlined copy of it, including three orchestrators' Phase 4. A shared
  invariant duplicated across nine prose files is not shared
  ([[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]]).
- And sometimes the honest move is to delete the cause instead. CI ran a hand-enumerated
  test-module list — silently skipping anything not appended, which had already shipped one
  unit's tests dark — solely because three files testing a **deleted plugin** aborted
  collection. Removing them let CI run `pytest tests/`, so collection *is* the enumeration
  and the constraint governing it was superseded rather than obeyed
  ([[2026-08-11-decision-ci-runs-the-whole-suite]]).

So the cluster's final rule is about where recognition lives. A list of accepted forms is a
hypothesis about the data, maintained by hand, and it decays every time an author writes
something reasonable that nobody predicted. What holds is a **tolerant predicate over
meaning, paired with one assertion that queries the real corpus** — that pairing found the
eighth marker spelling immediately, after eight had been enumerated by eye. Fixtures record
the shapes you know about; only the corpus test finds the ones you do not.

That rule has a counterweight, learned immediately afterwards by getting it wrong twice in
one module. **Tolerance and scope are separate dials, and widening the first without setting
the second turns a gap-filler into a false reading.** A `## Status` fallback that took "the
next non-blank line" walked past the empty section into the following `## Goal` and returned
its prose, so a live draft read as finished; and neither that reader nor its sibling was
fence-aware, so a fenced *example* of a status field or a promote marker — which every skill
documenting the convention contains — shadowed the real declaration below it. Both failures
point the dangerous way for their consumer, and both were found by reviewers rather than by
rereading. So a fallback chain needs a **scope per link**, not just an order: a section ends
at the next heading, a declaration is not inside a fence, and an empty section means the
author said nothing rather than "keep looking"
([[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]]).

Which direction to be generous in is likewise not a style choice but a consequence of what
breaks. `is_post_promote` reads permissively because a false negative re-runs a mutating
pass; `read_status` feeds the in-flight collision check, where the costly error is the
opposite — calling live work finished — so its fallback is deliberately the narrower of the
two. Same module, same author, opposite calls.

The cluster closes on the question it had been avoiding: **why did the same mistake keep
landing when the rule was already written down?** Fence-awareness has been a documented
constraint since June, cited approvingly in later work, and was violated three times in two
months — twice in `work_status.py`, once in `knowledge_fix.plan_index`, every instance found
by review or by accident and none by tooling. Writing the rule down had been mistaken for
addressing it. The first test that actually enforced it failed **on its first run**, on a
live defect: `plan_index` rewrites `index.md` from a fence-blind parse, so a fenced catalog
line naming a real entry became a real catalogued line, duplicating the entry with the
example's fake summary while the fence-aware linter reported clean
([[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]]).

A companion hazard sits one step upstream, in how these rules get *verified*. minerva
skills document commands an agent runs verbatim, and this repo executes some of them in
tests — safe only while every extracted block is read-only, a property nothing enforces.
`minerva:promote`'s issue path is the first documented flow whose commands **mutate remote
state**. Checking that its label helper correctly reported an unusable label was run against
the live repository; the account had admin rights, so the "should fail" branch never
executed and the command instead did exactly what it documents — creating a real label that
had to be deleted. The trap generalizes: **a test written around "this should fail" becomes
a test that succeeds and mutates the moment it runs with more permission than assumed**, and
the stronger the credentials, the less the negative path is exercised and the more real the
side effect. `bash -n` catches the quoting defects that motivate most such checks at zero
side-effect cost; anything beyond that wants a stub or a scratch target
([[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]]).

The sharpest instance of the cluster turned up inside a tool built to cure it.
`minerva:backfill-followups` exists because 24 `followups.md` files held ~79 deferred items
with **nothing marking any of them done**, so every scoping pass re-read all of them. It
triages each item, files the live ones, and writes a disposition ledger. Its first run left 25
items honestly recorded as `open — not filed at this pass` — and its idempotency rule said
*skip any item already carrying a disposition line*. That rule is right for a resolved item
and wrong for a deferred one, and a single has-a-disposition test cannot tell them apart, so
every one of those live items would have been passed over by every future run. The prose said
"still open"; the machinery said "handled". **The cure had reproduced the disease one layer
up, and strictly worse — a ledger invites you to stop looking.** The fix is to type
dispositions rather than count them: terminal ones are skipped, `open — not filed` is
re-offered every run, and only then does re-running become the trigger that deferral needs
([[2026-08-22-pattern-a-ledger-line-is-not-a-resolution]]).

Two later entries show the same failure wearing different clothes. One is about a value
that looks settled and is not: `proposal.md`'s `**Closes**: #NN` was safe while only
end-of-work promote wrote it, having just read the finished diff. Moving the authoring
point to intake — where a user adopts an open issue before any diff exists — turned the
field into a **claim that predates its evidence**, and a claim has to be re-verified at
every consumer rather than the nearest one, because the work may since have been
replanned, narrowed or split
([[2026-08-22-pattern-a-value-written-before-its-evidence-needs-re-verifying]]).

The other is about what survives an extraction. Pulling one repeated protocol out of four
skills left each caller with a short block, and the obvious next question — "are these
copies or are they deliberately different?" — has the annoying answer *both*. Each block
split into a **shared half** (what the check does) where drift is always a bug, and a
**divergent half** (which rung adjudicates, how much user contact it permits) where
sameness would be the bug. The two halves need opposite invariants, and pinning only one
leaves the other free to rot while the suite reads green; the first draft pinned only the
divergent half, so a fifth evidence source would have left four stale summaries and a
passing build ([[2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves]]).
Mutation-testing each new guard is what separates this from a presence assertion that
cannot fail.

That yields the cluster's governing test. For any rule this corpus records, ask **what fails
if it is violated**; if the answer is "a reviewer might notice", it is a wish, not a
constraint. And when the enforcement is finally written, expect it to find something —
a gate that passes on its first run has not yet been shown capable of failing, which is why
the fixture proving it *fires* matters more than the one proving it passes.

The newest entries sharpen that test into questions about the assertion itself. A presence
check must be **scoped to the region that does the work**: surrounding prose explaining a
requirement keeps a whole-file `assert "X" in doc` green long after the enforcement was
deleted ([[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]]). An
assertion phrased about the corpus's current contents — *nothing does X yet* — expires the
moment the feature it guards is first used, and the tempting exclusion list gets weaker as
adoption grows, so state the invariant about the property instead
([[2026-08-28-pattern-a-corpus-assertion-must-survive-its-own-first-instance]]). Who looks
matters too: an author self-reviewing finds rule violations they can look up, and reliably
misses orphaned code and toothless tests, which is the reviewer's half
([[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]]).

Two entries generalise the shape beyond tests. Adopting a shared primitive means importing
the **grammar** and re-deriving the **conclusion**: this corpus's fence scan answers "where
are the fences", and a reader asking whether any content exists at all needs the same
grammar with the opposite handling from every declaration-reading sibling
([[2026-08-28-pattern-import-the-grammar-not-its-conclusion]]). And a new state's **decider**
and its **executors** are separate surfaces — teaching the one that chooses without teaching
the ones that act leaves the others silently wrong
([[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]]).

## Limitations

This overview is **advisory** — a navigation aid, never a CI-gated artifact. It no longer
carries a synthesis watermark: coverage is derived **per-record** from the file itself, an
entry counting as synthesized iff this document actually links it. That is strictly
stronger than the floor it replaces, which could not survive out-of-order merges and
cannot express anything at all over date ids, since same-day ties mean they are not
totally ordered.

What the per-record signal does and does not attest:

- it detects an entry this overview has **never mentioned** — including one dropped by a
  rewrite, which the old floor silently counted as done;
- it does **not** detect in-place edits to an already-linked entry (a later `## Related`
  rewiring, a supersession banner, an appended body) — that drift remains a judgment call
  for the next synthesis;
- it attests synthesis **intent, not body content** — a link from a narrative that no
  longer describes the entry reads as covered, and nothing mechanical can tell.

This refresh ran during `2026-08-09-date-prefixed-identity`'s reconciliation, on five
un-synthesized entries. It is the first refresh after the id migration, so every wikilink
above is a date stem, and it **retired its own watermark** — the paragraph describing that
floor is gone because the floor is. It also closed the concurrency arc: the cross-branch
allocator that theme introduces as a necessary backstop no longer exists, its premise
removed rather than its implementation improved.

The prior refresh ran during `051-resolve-entry-type-tolerantly`'s reconciliation,
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
