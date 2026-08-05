# Proposal: add-only-knowledge-writes

**Date**: 2026-08-05
**Status**: Draft

## Goal
Make a minerva work-unit branch's `.minerva/` footprint consist **entirely of newly-added files**, so concurrent PRs cannot conflict on minerva records. Because that removes the textual conflict currently acting as an accidental guard on knowledge-ID allocation, make that allocation collision-safe and duplicate-detecting in the same unit.

## Why
`.minerva/knowledge/index.md` appears in 78% of recent commits in a heavy consumer repo, and its conflicts are **guaranteed rather than probable**: every promote bumps `<!-- index-watermark: NNN -->` on line 2 — a same-line edit, which always conflicts — and appends a catalog line to a Type section. `overview.md` adds another 33% as a wholesale rewrite by `minerva:synthesize`. Measured cost is ~20 minutes per surfaced conflict, so three in-flight PRs burn an hour-plus on pure friction.

The cause is that `promote` performs cross-entry and aggregate writes *inside* the work-unit branch. Minerva already solved the sibling problem one layer up: `propose` allocates work-unit NNN by scanning local work dirs, local branches, **and remote branches** (`skills/propose/references/on-approval.md:13-28`), explicitly "so parallel work in worktrees and remotes doesn't collide." Because a unit's branch is *named* `NNN-slug` and pushed, every in-flight unit broadcasts its number.

`promote` has no equivalent. `skills/promote/references/modes.md:24` and `:43` say only "auto-increment NNN across the whole `.minerva/knowledge/` directory" — a single-directory scan in a single worktree, structurally blind to in-flight entries on other branches.

That blindness is not theoretical. A consumer repo carries **65 duplicate-NNN groups** on main today, and a near-miss was observed this cycle: two units independently selected knowledge number 546, caught *only* because their `index.md` appends landed on adjacent lines. Had they landed in different Type sections, git would have merged cleanly and shipped two entries sharing an ID. Nothing would have caught it — the NNN-keyed dict comprehensions in `scripts/knowledge_lint.py` (`:126`, `:135`) and `scripts/knowledge_fix.py` (`:61`) silently drop duplicates, so the wiki tooling cannot see them by construction.

So the textual conflict is currently the *only* thing guarding ID allocation. Removing the conflicts without fixing the allocator would convert a loud, cheap failure into a silent, expensive one — which is why both ship together.

The pain is felt in consumer repos, not here, so every part of the fix must be **portable plugin behavior**: no CI workflow to install, no git merge driver (those are per-clone local config), no per-repo setup.

## Approach

### 1. Entry template gains a self-describing summary
`skills/promote/references/wiki-maintenance.md`'s knowledge-entry template gains `**Summary**: <≤15 words>` in the metadata block beside `**Date**` / `**Type**` / `**Context**`. This is what lets the index be rebuilt mechanically instead of requiring an LLM to condense a Finding at reconciliation time.

### 2. `promote` becomes add-only in-branch
In **both** Mode A (end-of-work) and Mode B (mid-work single-item), promote writes new entry files and its own work-unit directory — nothing else:

- no `index.md` catalog line, no watermark bump;
- no neighbor `## Related` edits;
- no supersession banners.

Neighbor discovery still runs — it is genuine LLM judgment — but emits **forward links only**, into the new entry. This is safe because `knowledge_fix.plan_reciprocals` already derives the reverse direction: "a `supersedes` forward edge gives B both the banner and the `superseded by` line" (`scripts/knowledge_fix.py:165-197`). No new mechanism is needed for reciprocals or banners.

The index-line freshness pre-filter in `wiki-maintenance.md:82-88` is relaxed: "fresh" becomes *watermark ≥ max NNN among entries not written by this run*, so the pre-filter remains usable instead of always falling through to a full corpus scan (which matters at 550+ entries).

### 3. `knowledge_lint.py` — lagging floor plus duplicate detection
- `index-watermark` becomes a **lagging floor** (`watermark ≤ max NNN`). Entries above it are `pending reconciliation` **warnings**, not drift errors. This mirrors the shape `synthesis-watermark` already has, where `scripts/synthesis_status.py`'s docstring states the watermark "deliberately lags, and the lag is the signal." Exit code is unaffected: `main()` returns non-zero only on `severity == "error"` (`:212`).
- Catalog-line-without-entry, wrong Type section, and broken `## Related` links remain **errors**.
- **The reciprocal check becomes pending-tolerant.** This is load-bearing: with promote emitting forward-only links, the missing-reciprocal check at `:186-195` — currently an error — would fire on *every* work-unit branch, since reverse links do not exist until reconciliation. A missing reciprocal is a `pending reconciliation` **warning** when the forward-edge's source entry sits above the index watermark (not yet reconciled), and remains an **error** otherwise. Same lagging-floor framing as the watermark itself.
- New **error**: duplicate NNN. This requires replacing the NNN-keyed dicts at `:126` and `:135` with grouping, since today the second entry sharing a number silently overwrites the first.

Erroring (rather than warning) costs nothing today: this repo's corpus is clean at 001-051, and the consumer repo with 65 legacy groups does not run the lint at all. It stays loud for the case that matters — a fresh collision.

### 4. `knowledge_fix.py` — insert catalog lines, quarantine duplicates
- `plan_index` gains the one operation it refuses today (`:87`, "fixer won't fabricate summaries"): adding a missing catalog line, read mechanically from the entry's `**Summary**`.
- **Duplicate-NNN quarantine**, in both `plan_index` and `plan_reciprocals`. This is a live hazard, not a hypothetical: because `_entries()` (`:61`) is NNN-keyed, on a corpus with duplicates `plan_index` collects *both* catalog lines (both match the one surviving entry) and buckets both under the surviving entry's declared type — misfiling up to 65 lines on the first automatic run. Quarantined groups are left verbatim where they are and reported as refusals, mirroring the existing unrecognized-type handling at `:104-107` ("LEFT where it is (never dropped — that would delete its summary)"). Everything else reconciles normally, so the conflict fix works on a legacy corpus immediately without renumbering anything first.

### 5. `scripts/knowledge_next_nnn.py` (new, tested)
Enumerates `.minerva/knowledge/` across the working tree, local branches, and remote branches via `git ls-tree`, returning max+1. `promote` wraps it via importable API per knowledge `021`, rather than embedding prose bash as `propose` does. This matters because the allocator is now the *only* backstop against silent duplicates — prose bash cannot be unit-tested and can be paraphrased by an agent (knowledge `007`).

### 6. `minerva:cleanup` gains reconciliation
Reconciliation is **decoupled from worktree removal** — cleanup evaluates the signal even when it removed nothing:

1. Compute the deterministic signal: `knowledge_lint` pending warnings + `synthesis_status`'s unsynthesized list.
2. `git fetch`, then create the reconciliation branch from `origin/<default-branch>` rather than assuming the parent repo's working tree is on the default branch or up to date — cleanup's pre-flight only guarantees it is *not* inside a worktree. Run `knowledge_fix` and, if its self-gate warrants, `minerva:synthesize`, both writing onto that branch.
3. Open a reconciliation PR and enable auto-merge. Its content is deterministic — regenerated from the corpus by a tested script, not authored — which is what makes auto-merge defensible here.
4. **Skip if a reconciliation PR is already open.** At most one outstanding at a time; the backlog is picked up by the next pass. Since reconciliation PRs are the only writer of `index.md`/`overview.md`, and work-unit PRs only add entry files, the two classes never overlap.
5. Under `--dry-run`, report what reconciliation would do without opening anything.

`cleanup`'s "never touches the default branch" contract — stated in its own `description` frontmatter — is rewritten deliberately, description included.

### 7. `minerva:lint-fix` becomes default-branch-only for mutation
Its Target section scopes it to "the `.minerva/knowledge/` corpus of the **current working tree**." Run on a work-unit branch, `plan_index` would rewrite `index.md` in-branch — silently reintroducing the exact conflict this unit removes. It gains a default-branch guard on the mutating path, pointing at `cleanup`.

### 8. `synthesize` moves out of the PR path
From Phase 4.5 (`skills/propose-ship-auto/references/phases.md:108` and the two sibling orchestrators) and the equivalent step in `propose-ship`, into cleanup's reconciliation. It then runs cold on main and can batch several merged units into one pass — cheaper, and it never depended on work-unit context since theme grouping is corpus-wide. Because this *removes* text, `propose-ship/SKILL.md`'s 10-byte headroom against the 9216 cap (unit 048) is not at risk.

### 9. Tests
Extend `tests/test_knowledge_lint.py`, `tests/test_knowledge_fix.py`, `tests/test_promote_invariant.py`, `tests/test_skill_contracts.py`. New `tests/test_knowledge_next_nnn.py` with git fixtures, appended to the enumerated pytest list in `.github/workflows/evals.yml` (knowledge `035` — new modules are invisible to CI otherwise). A contract test asserts `promote`'s references contain no index-write instruction, using the prose-site detection pattern `tests/test_skill_dispatch.py` already establishes.

### Rejected alternatives
- **Pending-fragment queue** — promote drops a per-unit catalog fragment under `.minerva/knowledge/pending/` that reconciliation folds and deletes. Same add-only guarantee with zero migration, and the summary is authored when the agent has freshest context. Rejected: it commits transient state to git, splits catalog data across two places, and adds a fold-and-delete step with partial-failure modes.
- **Union-merge `index.md`** — drop the watermark, have `minerva:init` scaffold `.gitattributes` with `index.md merge=union` (a *built-in* driver, so no per-clone install), and move only `synthesize`. Roughly 80% of the win for ~25% of the work with near-zero migration. Rejected: neighbor-entry conflicts survive — and those are the ones that need judgment to resolve, since entries have real content — and union merge silently keeps both sides, the same silent-acceptance failure class that produced the 546 near-miss.
- **Backfilling summaries into all existing entries** — deferred to a followup. It is not a prerequisite: `plan_index` collects each surviving catalog line **verbatim** (`:90-95`), keyed only on whether the entry file exists, so an old entry keeps its line indefinitely while new entries generate theirs from `**Summary**`. The mixed state is stable, not transitional. Backfill only buys robustness if `index.md` is ever lost or rebuilt from scratch, since old summaries live only there.
- **A CI workflow or a git merge driver** — ruled out by the portability constraint. Minerva cannot install a workflow in every consumer repo, and custom merge drivers are per-clone local config that CI checkouts and fresh worktrees would silently lack.

## Success criteria
- A contract test asserts `promote`'s references contain no index-write or neighbor-edit instruction, and a promote run on a work-unit branch leaves `git status` showing only additions under `.minerva/`.
- `knowledge_lint` exits 0 on a corpus with entries above the watermark, reporting them as pending-reconciliation warnings — including a fixture where those entries carry forward `## Related` links whose reciprocals are absent.
- `knowledge_lint` exits non-zero on a corpus containing two entries that share an NNN.
- `knowledge_next_nnn.py` returns a number above an entry existing only on an unmerged local branch, and above one existing only on a remote branch — one git-fixture test per source.
- `knowledge_fix --dry-run` plans catalog lines for summary-bearing un-catalogued entries; entry bodies stay byte-identical outside the permitted `## Related`/banner spans; duplicate-NNN groups appear as refusals with their catalog lines unmoved.
- `minerva:lint-fix` refuses its mutating path when the working tree is not on the default branch.
- `minerva:cleanup` opens at most one reconciliation PR, skips when one is already open, enables auto-merge, and only reports under `--dry-run`.
- No orchestrator invokes `minerva:synthesize` before ship; all four route it through cleanup's reconciliation.
- Every `SKILL.md` stays ≤ 9216 bytes; `tests/test_knowledge_next_nnn.py` is enumerated in `.github/workflows/evals.yml`; the full CI-enumerated suite is green and `knowledge_lint` is clean on this repo.

## Open Questions
- If a consumer repo's branch protection forbids auto-merge, the reconciliation PR simply waits for a human merge. No code path changes, but the "you never see it" property degrades to an occasional manual merge.
- Making `index.md` fully reconstructible from the corpus alone — the deferred summary backfill — is recorded as a followup, not resolved here.
