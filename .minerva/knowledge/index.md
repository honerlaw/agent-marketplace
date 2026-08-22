# Knowledge index

## Decisions

- [[2026-05-19-decision-gitignore-before-worktree]] — add `.minerva/worktrees/` to `.gitignore` before running `git worktree add`
- [[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]] — init's Routing-section detection accepts both old and new directory names
- [[2026-05-19-decision-review-lens-ownership]] — minerva owns spec/knowledge review lenses; code-review owns quality
- [[2026-05-22-decision-minerva-reference-tier]] — `.minerva/reference/` is the present-tense operational-doc tier, distinct from knowledge
- [[2026-05-31-decision-behavioral-evals-provisional]] — behavioral skill-value evals are provisional: don't CI-gate, don't trust deltas yet
- [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] — gate per-decision and fail closed, not via an up-front sizing classifier
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — knowledge is a navigable wiki: maintained index.md + corpus-scan discovery (X′ over X)
- [[2026-06-02-decision-phase-b-deterministic-lint-detector]] — Phase B split: a deterministic knowledge-lint CI gate ships first; the LLM-judged minerva:lint skill is deferred
- [[2026-06-03-decision-knowledge-fix-two-safety-models]] — the wiki fixer uses two safety models: entry body byte-identity vs index skeleton-preservation
- [[2026-06-03-decision-migration-check-read-only-entry-re-blindspot]] — minerva:migrate is the read-only migration-shape check; its reason to exist is the ENTRY_RE false-clean blind spot every wiki tool shares
- [[2026-06-03-decision-minerva-lint-read-only]] — minerva:lint ships read-only (advisory judged dims); the gated fix-applier is deferred to Phase B.3
- [[2026-06-03-decision-related-backfill-hand-authored-rename-redeferred]] — the initial ## Related backfill was hand-authored (the spike for any future skill); rename-APPLY stays deferred at zero live instances
- [[2026-06-03-decision-routing-section-is-the-wiki-reading-protocol]] — the Routing section teaches the wiki reading protocol; stale sections get a gated refresh with markers derived from the template-of-record
- [[2026-06-03-decision-synthesis-layer-separate-file-advisory]] — the synthesis layer is a separate overview.md with a new-scope-only watermark; its content is advisory, never CI-gated
- [[2026-06-03-decision-synthesize-wired-post-promote-self-gating]] — minerva:synthesize is wired into both orchestrators as a self-gating post-promote/pre-ship step (delegation, not a panel)
- [[2026-06-07-decision-phase-handoff-rides-observable-intake]] — phase-to-phase skill handoffs ride an observable intake (an inline arg), not a self-judged "did the prior phase converge?" predicate
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — panel mechanics live in minerva:round-table; orchestrators delegate and keep policy (quorum taxonomy, skip predicates, run-level state)
- [[2026-06-16-decision-propose-ship-quick-main-model-adjudication]] — a third orchestrator (propose-ship-quick) has the main model decide solo; its fail-closed escalation predicate is the structural inverse of auto's skip predicate
- [[2026-06-16-decision-site-gitbook-theme-overrides]] — gitbook-theme site chrome is customized via `theme.custom_dir → overrides/`, never the installed theme; the dead search-results block is CSS-hidden
- [[2026-06-27-decision-worktree-addressing-no-enterworktree]] — minerva dropped `EnterWorktree`; worktrees are addressed by `.minerva/worktrees/<NNN-slug>/`-prefixed paths + `git -C` (it only natively enters `.claude/worktrees/`)
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — a fourth orchestrator (propose-ship-balanced) runs one advisory reviewer at the telemetry-selected high-signal gates, arbitrated inline — between quick (solo) and auto (panels), not a round-table panel
- [[2026-08-05-decision-promote-add-only-reconcile-on-default]] — promote writes only new entry files; index, watermark, reciprocals and overview reconcile on the default branch
- [[2026-08-09-decision-reference-is-a-fifth-entry-type]] — The entry-type vocabulary was four values — `decision` / `bug` / `pattern` / `constraint` — hardcoded in `SECTION_TO_TYPE`, `SECTION_ORDER` and four skill docs. Authors wrote `reference` entries anyway (four of them in one corpus), and the tooling had nowhere to put them: `plan_index` cannot place a line whose declared type has no section, so they were refused indefinitely. Adding `## References` as a fifth section ratifies what authors already do. Two rules fall out: **append a new section, never interleave it** (appending is the only position that leaves every existing index's line order byte-identical), and an empty section renders as its header alone, so the change is inert for every corpus that does not use it.
- [[2026-08-10-decision-date-ids-make-identity-the-path]] — an unallocated id plus full-stem identity turns silent duplicate-merges into loud add/add conflicts
- [[2026-08-11-decision-ci-runs-the-whole-suite]] — three dead test files forced an enumerated CI list for months; deleting them dissolved the constraint instead of guarding it

## Bugs

- [[2026-05-19-bug-promote-idempotency-check-misses-old-marker]] — promote idempotency check missed the old scratchpad marker format
- [[2026-06-03-bug-knowledge-edits-not-fence-aware]] — the span editors read fenced examples as structure: crash/false-dedupe on any edge into 015 (third fence-trap instance; fixed)
- [[2026-07-21-bug-skill-listing-description-drop]] — valid frontmatter descriptions dropped from rendered listing; ambient triggering impossible for affected skills
- [[2026-08-10-bug-absolute-path-guard-matches-everything-inside-a-worktree]] — test paths relative to the repo root; minerva's own work happens inside the directory such guards exclude
- [[2026-08-10-bug-git-follow-and-diff-filter-a-cancel-out]] — --follow reports a creation as a rename, so pairing it with --diff-filter=A filters every commit away

## Patterns

- [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] — rejected alternatives recur at runtime; prohibit in skill text, test-anchored
- [[2026-06-10-pattern-plugin-discovery-mostly-auto-crawl]] — plugin discoverability is mostly auto-crawl once public + licensed + topic-tagged; manual directories are web-form submissions, not source-vendor lists
- [[2026-07-21-pattern-catalog-semantic-drift-recurs]] — catalog surfaces drift semantically even during active scrubbing; sweep all four
- [[2026-07-29-pattern-wait-shape-matches-what-is-awaited]] — size a wait to what's awaited (CI-shaped vs queue-shaped); prefer the CLI's own blocking primitive over a poll loop
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — gate concurrency on an atomic operation's own success, not on a preceding "is it taken?" read
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — "the next run will pick it up" is only true if something SCHEDULES a next run. `minerva:cleanup`'s reconciliation skipped when another reconcile PR was open and deferred to a next run that fires only when someone next finishes a work unit — days away, or never — so entries sat on the default branch present but UNCATALOGUED (in the corpus, absent from the index, invisible to a reader), while the skipping run reported itself successful. Six occurrences in two days on one project, every one found by accident. TWO failures that compound: the deferral had no trigger, and it was silent — either alone is survivable, together they are undetectable. Rules: prefer WAITING over deferring when the blocker is short-lived and observable; if you must defer, name each deferred item in the step's own output, because a report that omits skipped work lies by omission; and RE-DERIVE after waiting, since the thing you waited on may have done part of the job. The tell: a doc saying "the next run", "picked up later" or "eventually" without naming what causes it. Unit 050
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — `parse_entry` read an entry's type from one anchored spelling, `**Type**: x`. Across a 629-entry corpus 42 entries declared it somewhere else — `Type: x` plain (16), `**Type:** x` with the colon inside the bold (13), a prose H1 or nothing (10), frontmatter only (3) — and every one resolved to `None`, which `plan_index` cannot place and the linter reported as `type 'None' but catalogued under a 'constraint' section`: an error naming a mismatch the entry does not have. Fix by resolving through a fallback chain ordered most-deliberate-first (body field in any spelling → frontmatter → filename segment), which makes a fallback able only to fill a gap, never override an author. Before trusting the last resort, MEASURE its concordance: filename type matched declared type 642/642 across two corpora.
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — `assert "x" in prose` cannot fail when x is removed from the codebase; invert it, don't delete it
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — two derivations plus a comment asserting they match will drift; share one implementation, or the invariant is only a wish
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — lint read clean before AND after 182 references broke, because its model of "a reference" was the writer's model; a clean gate is evidence only over what the gate can see
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — permissiveness and scope are separate dials; widening what a parser accepts without bounding where it looks turns a gap-filler into a false reading
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — a knowledge entry stating a rule enforces nothing — this one was violated three times in two months and the first enforcing test caught a live defect immediately
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — a marker with eight spellings broke a check for months, and enumerating them by eye failed three times in one sitting — the assertion that held asks the corpus
- [[2026-08-22-pattern-a-just-written-index-is-not-a-read-back-guarantee]] — guard a retry with the local record; an eventually-consistent index misses what you just wrote
- [[2026-08-22-pattern-a-ledger-line-is-not-a-resolution]] — a record marking work handled must separate decided-and-done from decided-to-wait, or it buries it
- [[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]] — exercising a documented mutating command against the live repo leaves real artifacts behind

## Constraints

- [[2026-05-19-constraint-plugin-skills-auto-discovered-from-directory]] — plugin skills are auto-discovered from `skills/`; no manifest update needed
- [[2026-05-19-constraint-post-promote-scratchpad-canonical-empty]] — the post-promote scratchpad is the canonical empty state downstream skills expect
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — skills must invoke tools directly, not describe actions in prose
- [[2026-05-20-constraint-enter-worktree-absolute-paths]] — worktree file ops use `.minerva/worktrees/<NNN-slug>/`-prefixed paths, not `EnterWorktree`
- [[2026-05-20-constraint-marketplace-plugin-registry-not-auto-discovered]] — marketplace registry isn't auto-discovered: update `marketplace.json` + README
- [[2026-05-21-constraint-minerva-skill-catalog-sync]] — skill catalogs aren't auto-generated: three doc surfaces must stay synced
- [[2026-05-31-constraint-skill-structural-contracts]] — every skill carries a declarative structural contract, enforced by an enumerating test
- [[2026-06-02-constraint-knowledge-cross-reference-convention]] — entries cross-reference via a `## Related` block of wiki-links with a closed relationship vocabulary
- [[2026-06-02-constraint-knowledge-span-model-single-sourced]] — the wiki span model is single-sourced in scripts/knowledge_spans.py; import it, never re-derive
- [[2026-06-02-constraint-promote-narrowed-never-overwrite]] — promote edits existing entries only within the `## Related`/banner span; bodies are append-only
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — a prose skill wraps a sibling Python tool via its importable API, anchored to the working-tree root; not the CLI, not CWD-relative
- [[2026-06-03-constraint-wiki-edge-derivation-fence-aware]] — any tool deriving wiki cross-ref edges must be fence-aware (a fenced `## Related` example is not a real edge)
- [[2026-06-10-constraint-site-fourth-catalog-surface]] — the static site’s skills catalog is a fourth, test-enforced catalog surface (bidirectional, site-only), extending 010’s three
- [[2026-06-11-constraint-ci-test-enumeration-explicit]] — new test modules are invisible to CI until appended to the enumerated pytest list
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — fence-aware scans import the single-sourced FENCE_RE grammar (or a parser built on it), whatever the corpus
- [[2026-06-11-constraint-skill-progressive-disclosure]] — skills keep ≤9KB SKILL.md cores with detail in on-demand references/; contract anchors follow via the `file` field
- [[2026-06-13-constraint-site-catalog-source-is-pages-index]] — site catalog surface is now pages/index.md (MkDocs source); site/ is gitignored build output; test reads source directly
- [[2026-07-21-constraint-handoffs-name-skill-tool]] — handoffs invoke the target via the Skill tool with argument, never bare prose
- [[2026-07-21-constraint-skill-description-house-style]] — descriptions lead with ambient triggers, invocation clause last, ≤1024 chars
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — dispatch instructions pin `run_in_background: false`; the Agent tool backgrounds by default and strands the run
- [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]] — new-file id collisions merge cleanly with no conflict, so the allocator is the only backstop
- [[2026-08-05-constraint-nnn-keyed-lookups-hide-duplicates]] — `{id: record}` silently drops duplicates; build `{id: [records]}` and exclude dupes from every derived edit
- [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]] — a threshold assumes NNN-ordered merges; use a per-record marker, not a scalar floor
- [[2026-08-14-constraint-a-ref-lock-binds-only-writers-that-share-the-ref]] — an atomic-push lock excludes nothing from a second writer that pushes a different branch name
- [[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]] — the pointer gate resolves any `references/<file>.md` substring against the citing skill only

## References
