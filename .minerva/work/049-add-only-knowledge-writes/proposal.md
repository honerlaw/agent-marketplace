# Proposal: add-only-knowledge-writes

**Date**: 2026-08-05
**Status**: Shipped (2026-08-05)

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

*(Rewritten at promote to describe what shipped. The run began with §3 as a "lagging
floor" — a scalar `index-watermark` threshold separating pending entries from drift —
and the Phase 3 review invalidated it. See `replan.md` for the reproduction and the
pivot. Numbers and mechanisms below are the shipped ones.)*

### 1. Entry template gains a self-describing summary
`skills/promote/references/wiki-maintenance.md`'s knowledge-entry template gains `**Summary**: <≤15 words>` in the metadata block beside `**Date**` / `**Type**` / `**Context**`. This is what lets the index be rebuilt mechanically instead of requiring an LLM to condense a Finding at reconciliation time.

### 2. `promote` becomes add-only in-branch
In **both** Mode A (end-of-work) and Mode B (mid-work single-item), promote writes new entry files and its own work-unit directory — nothing else:

- no `index.md` catalog line, no watermark bump;
- no neighbor `## Related` edits;
- no supersession banners.

Neighbor discovery still runs — it is genuine LLM judgment — but emits **forward links only**, into the new entry. This is safe because `knowledge_fix.plan_reciprocals` already derives the reverse direction: "a `supersedes` forward edge gives B both the banner and the `superseded by` line" (`scripts/knowledge_fix.py:165-197`). No new mechanism is needed for reciprocals or banners.

The index-line freshness pre-filter in `wiki-maintenance.md:82-88` is relaxed: "fresh" becomes *watermark ≥ max NNN among entries not written by this run*, so the pre-filter remains usable instead of always falling through to a full corpus scan (which matters at 550+ entries).

### 3. `knowledge_lint.py` — pending-vs-drift, and duplicate detection

**No watermark comparison anywhere.** An uncatalogued entry, and a forward `## Related` link whose reverse direction is missing, are **always** `pending reconciliation` warnings. That is sound because promote no longer writes catalog lines at all, so no promote-driven path produces genuine drift, and reconciliation repairs whatever it finds regardless of the order entries arrive in.

The scalar "lagging floor" this section originally specified was reproduced broken during review: it assumes entries reconcile in NNN order, and concurrent units merge whenever their PRs land. Full reproduction and reasoning in `replan.md`; the durable form is `.minerva/knowledge/053-constraint-reconciliation-state-is-not-a-scalar.md`.

- The reciprocal check is pending-tolerant for the same reason, and it is load-bearing: with promote emitting forward-only links, an error-severity reciprocal check would fire on *every* work-unit branch, for every cross-link a new entry declares.
- Catalog-line-without-entry, wrong Type section, broken `## Related` links, and a watermark *above* max NNN remain **errors**.
- New **error**: duplicate NNN — which required replacing the NNN-keyed dicts with grouping, plus quarantining duplicate ids from every downstream check, since the surviving group member is arbitrary and anything derived from it names the wrong file.
- NNN patterns widened to `\d{3,}` with numeric comparison, so the corpus can pass 999 without the allocator and the duplicate detector going blind simultaneously.

Erroring on duplicates (rather than warning) costs nothing today: this repo's corpus is clean at 001-051, and the consumer repo with 65 legacy groups does not run the lint at all. It stays loud for the case that matters — a fresh collision.

### 4. `knowledge_fix.py` — insert catalog lines, quarantine duplicates
- `plan_index` gains the one operation it refuses today (`:87`, "fixer won't fabricate summaries"): adding a missing catalog line, read mechanically from the entry's `**Summary**`.
- **Duplicate-NNN quarantine**, in both `plan_index` and `plan_reciprocals`. This is a live hazard, not a hypothetical: because `_entries()` (`:61`) is NNN-keyed, on a corpus with duplicates `plan_index` collects *both* catalog lines (both match the one surviving entry) and buckets both under the surviving entry's declared type — misfiling up to 65 lines on the first automatic run. Quarantined groups are left verbatim where they are and reported as refusals, mirroring the existing unrecognized-type handling at `:104-107` ("LEFT where it is (never dropped — that would delete its summary)"). Everything else reconciles normally, so the conflict fix works on a legacy corpus immediately without renumbering anything first.

### 5. `scripts/knowledge_next_nnn.py` (new, tested)
Unions the working tree (including uncommitted entries) with every entry ever *added* along the history of any ref — `git log --all --diff-filter=A --name-only` over the knowledge path, one path-limited command rather than a per-ref `git ls-tree`. Returns max+1, widening past 999 rather than wrapping. Git failures raise rather than degrading to the local-only scan, since a silent under-count is exactly the duplicate this exists to prevent. `promote` wraps it via importable API per knowledge `021`, rather than embedding prose bash as `propose` does. This matters because the allocator is now the *only* backstop against silent duplicates — prose bash cannot be unit-tested and can be paraphrased by an agent (knowledge `007`).

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
- A contract test asserts `promote`'s references contain no index-write or neighbour-edit instruction. *(The originally-stated second clause — that a promote run leaves `git status` showing only additions — is not assertable in CI, because `minerva:promote` is LLM-executed prose with no callable entry point. It was nonetheless **observed** on this unit's own promote: five new entry files, `index.md` unmodified, `knowledge_lint` exit 0 with five pending warnings. Recorded in `followups.md`.)*
- `knowledge_lint` exits 0 on a corpus with uncatalogued entries, reporting them as pending-reconciliation warnings — including a fixture where those entries carry forward `## Related` links whose reciprocals are absent, and one where an entry arrives *below* an already-advanced watermark (the out-of-order merge case).
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
