# Knowledge index
<!-- index-watermark: 056 -->

## Decisions

- [[001-decision-init-routing-detection-accepts-old-and-new-names]] — init's Routing-section detection accepts both old and new directory names
- [[005-decision-gitignore-before-worktree]] — add `.minerva/worktrees/` to `.gitignore` before running `git worktree add`
- [[006-decision-review-lens-ownership]] — minerva owns spec/knowledge review lenses; code-review owns quality
- [[011-decision-minerva-reference-tier]] — `.minerva/reference/` is the present-tense operational-doc tier, distinct from knowledge
- [[013-decision-behavioral-evals-provisional]] — behavioral skill-value evals are provisional: don't CI-gate, don't trust deltas yet
- [[014-decision-per-decision-skip-over-sizing-gate]] — gate per-decision and fail closed, not via an up-front sizing classifier
- [[017-decision-knowledge-wiki-navigability-layer]] — knowledge is a navigable wiki: maintained index.md + corpus-scan discovery (X′ over X)
- [[018-decision-phase-b-deterministic-lint-detector]] — Phase B split: a deterministic knowledge-lint CI gate ships first; the LLM-judged minerva:lint skill is deferred
- [[020-decision-minerva-lint-read-only]] — minerva:lint ships read-only (advisory judged dims); the gated fix-applier is deferred to Phase B.3
- [[022-decision-knowledge-fix-two-safety-models]] — the wiki fixer uses two safety models: entry body byte-identity vs index skeleton-preservation
- [[024-decision-synthesis-layer-separate-file-advisory]] — the synthesis layer is a separate overview.md with a new-scope-only watermark; its content is advisory, never CI-gated
- [[025-decision-synthesize-wired-post-promote-self-gating]] — minerva:synthesize is wired into both orchestrators as a self-gating post-promote/pre-ship step (delegation, not a panel)
- [[026-decision-migration-check-read-only-entry-re-blindspot]] — minerva:migrate is the read-only migration-shape check; its reason to exist is the ENTRY_RE false-clean blind spot every wiki tool shares
- [[027-decision-related-backfill-hand-authored-rename-redeferred]] — the initial ## Related backfill was hand-authored (the spike for any future skill); rename-APPLY stays deferred at zero live instances
- [[029-decision-routing-section-is-the-wiki-reading-protocol]] — the Routing section teaches the wiki reading protocol; stale sections get a gated refresh with markers derived from the template-of-record
- [[031-decision-phase-handoff-rides-observable-intake]] — phase-to-phase skill handoffs ride an observable intake (an inline arg), not a self-judged "did the prior phase converge?" predicate
- [[033-decision-panel-mechanics-extracted-to-round-table]] — panel mechanics live in minerva:round-table; orchestrators delegate and keep policy (quorum taxonomy, skip predicates, run-level state)
- [[042-decision-propose-ship-quick-main-model-adjudication]] — a third orchestrator (propose-ship-quick) has the main model decide solo; its fail-closed escalation predicate is the structural inverse of auto's skip predicate
- [[043-decision-site-gitbook-theme-overrides]] — gitbook-theme site chrome is customized via `theme.custom_dir → overrides/`, never the installed theme; the dead search-results block is CSS-hidden
- [[044-decision-worktree-addressing-no-enterworktree]] — minerva dropped `EnterWorktree`; worktrees are addressed by `.minerva/worktrees/<NNN-slug>/`-prefixed paths + `git -C` (it only natively enters `.claude/worktrees/`)
- [[045-decision-propose-ship-balanced-single-reviewer]] — a fourth orchestrator (propose-ship-balanced) runs one advisory reviewer at the telemetry-selected high-signal gates, arbitrated inline — between quick (solo) and auto (panels), not a round-table panel
- [[052-decision-promote-add-only-reconcile-on-default]] — promote writes only new entry files; index, watermark, reciprocals and overview reconcile on the default branch

## Bugs

- [[002-bug-promote-idempotency-check-misses-old-marker]] — promote idempotency check missed the old scratchpad marker format
- [[028-bug-knowledge-edits-not-fence-aware]] — the span editors read fenced examples as structure: crash/false-dedupe on any edge into 015 (third fence-trap instance; fixed)
- [[046-bug-skill-listing-description-drop]] — valid frontmatter descriptions dropped from rendered listing; ambient triggering impossible for affected skills

## Patterns

- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — rejected alternatives recur at runtime; prohibit in skill text, test-anchored
- [[032-pattern-plugin-discovery-mostly-auto-crawl]] — plugin discoverability is mostly auto-crawl once public + licensed + topic-tagged; manual directories are web-form submissions, not source-vendor lists
- [[048-pattern-catalog-semantic-drift-recurs]] — catalog surfaces drift semantically even during active scrubbing; sweep all four
- [[051-pattern-wait-shape-matches-what-is-awaited]] — size a wait to what's awaited (CI-shaped vs queue-shaped); prefer the CLI's own blocking primitive over a poll loop
- [[056-pattern-read-then-act-is-not-a-lock]] — gate concurrency on an atomic operation's own success, not on a preceding "is it taken?" read

## Constraints

- [[003-constraint-post-promote-scratchpad-canonical-empty]] — the post-promote scratchpad is the canonical empty state downstream skills expect
- [[004-constraint-plugin-skills-auto-discovered-from-directory]] — plugin skills are auto-discovered from `skills/`; no manifest update needed
- [[007-constraint-skills-must-call-tools-not-prose]] — skills must invoke tools directly, not describe actions in prose
- [[008-constraint-enter-worktree-absolute-paths]] — worktree file ops use `.minerva/worktrees/<NNN-slug>/`-prefixed paths, not `EnterWorktree`
- [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — marketplace registry isn't auto-discovered: update `marketplace.json` + README
- [[010-constraint-minerva-skill-catalog-sync]] — skill catalogs aren't auto-generated: three doc surfaces must stay synced
- [[012-constraint-skill-structural-contracts]] — every skill carries a declarative structural contract, enforced by an enumerating test
- [[015-constraint-knowledge-cross-reference-convention]] — entries cross-reference via a `## Related` block of wiki-links with a closed relationship vocabulary
- [[016-constraint-promote-narrowed-never-overwrite]] — promote edits existing entries only within the `## Related`/banner span; bodies are append-only
- [[019-constraint-knowledge-span-model-single-sourced]] — the wiki span model is single-sourced in scripts/knowledge_spans.py; import it, never re-derive
- [[021-constraint-skill-wraps-script-via-importable-api]] — a prose skill wraps a sibling Python tool via its importable API, anchored to the working-tree root; not the CLI, not CWD-relative
- [[023-constraint-wiki-edge-derivation-fence-aware]] — any tool deriving wiki cross-ref edges must be fence-aware (a fenced `## Related` example is not a real edge)
- [[034-constraint-site-fourth-catalog-surface]] — the static site’s skills catalog is a fourth, test-enforced catalog surface (bidirectional, site-only), extending 010’s three
- [[035-constraint-ci-test-enumeration-explicit]] — new test modules are invisible to CI until appended to the enumerated pytest list
- [[036-constraint-skill-progressive-disclosure]] — skills keep ≤9KB SKILL.md cores with detail in on-demand references/; contract anchors follow via the `file` field
- [[037-constraint-fence-scans-import-fence-re]] — fence-aware scans import the single-sourced FENCE_RE grammar (or a parser built on it), whatever the corpus
- [[038-constraint-site-catalog-source-is-pages-index]] — site catalog surface is now pages/index.md (MkDocs source); site/ is gitignored build output; test reads source directly
- [[047-constraint-skill-description-house-style]] — descriptions lead with ambient triggers, invocation clause last, ≤1024 chars
- [[049-constraint-handoffs-name-skill-tool]] — handoffs invoke the target via the Skill tool with argument, never bare prose
- [[050-constraint-agent-dispatch-pins-execution-mode]] — dispatch instructions pin `run_in_background: false`; the Agent tool backgrounds by default and strands the run
- [[053-constraint-reconciliation-state-is-not-a-scalar]] — a threshold assumes NNN-ordered merges; use a per-record marker, not a scalar floor
- [[054-constraint-nnn-keyed-lookups-hide-duplicates]] — `{id: record}` silently drops duplicates; build `{id: [records]}` and exclude dupes from every derived edit
- [[055-constraint-knowledge-allocation-scans-across-branches]] — new-file id collisions merge cleanly with no conflict, so the allocator is the only backstop
