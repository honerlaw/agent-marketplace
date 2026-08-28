# Scratchpad: workstream-status-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Balanced decisions 2026-08-28

- [decided] pre-flight: no collision — 63 local units all promoted, one in-flight unit (`2026-08-27-deferral-cost-model`, PR #101) is unrelated; peer sessions `agent-marketplace-69` (orchestrator gates) and `-72` (deferral cost model) both replied non-overlapping. No open issue matches the seed (#94, #98 unrelated).
- [reviewed — folded] scope check: ONE work unit (Skeptic affirmed the split and verified the catalog surfaces are test-forced, not discretionary). Folded its load-bearing #1: root resolution was unspecified and the repo-wide `--show-toplevel` idiom is wrong for a cross-worktree walk. Also folded #2 (dedup across the two roots) and #3 (which layer owns Next step).
- [reviewed — folded] approach: A (hermetic script + prose skill with opportunistic git/gh enrichment); rejected B (subprocess git/gh inside the script — no minerva reader shells out) and C (skill-only — untestable prose). Skeptic returned `revise` on A's concrete design, all folded: join via `phase_branch()`/`phase_progress()` not string equality; `worktree_present` on an incomplete phased unit is not a cleanup signal; named the `draft`/`in-progress` discriminator; added `PLUGIN_SCRIPTS` plugin-cache-first resolution; absolutized `WORK_ROOT`.
- [decided] whole-proposal soundness (solo gate): additive-only surface, new API with no existing consumers, no cross-cutting contract change, no knowledge conflict once the folds landed.

## Notes

- `scripts/*.py` are **symlinks** into `plugins/minerva/scripts/` (git mode `120000`), not
  byte-identical copies. `diff -q` follows symlinks and reports IDENTICAL, which misled both
  me and the scope Skeptic into specifying a "mirrored copy" deliverable. Caught via
  `git ls-tree`. The deliverable is one real file plus one symlink.
- PR #101 merged mid-intake (2026-08-28T11:54Z), so `read_phases` / `phase_progress` /
  `phase_name` / `phase_branch` are on main. The phase column ships in the first cut; the
  planned "defer phases" follow-up is moot.
- `WORK_ROOT` idiom cross-checked with peer session `agent-marketplace-72`, which is
  replacing `--show-toplevel` with the same absolutized `--git-common-dir` form in
  `ship/references/protocol.md`, `cleanup/references/phased-units.md` and
  `propose/references/on-approval.md` on its phase-2 branch. Expect those files to converge
  on the same idiom from two directions — do not edit them here.
