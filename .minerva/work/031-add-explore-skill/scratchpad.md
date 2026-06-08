# Scratchpad: add-explore-skill

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-07
- [3/3 accept, rev2] scope check: single work unit (round 1 was 2/3 — Skeptic flagged a load-bearing omission: inserting a brainstorm phase "before propose" requires reconciling propose; folded the bounded propose boundary-edit into the unit; round 2 reached 3/3)
- [3/3 accept, rev2] approach selection: A‴ — separate `minerva:explore` skill, no-file, explicit inline-arg `Skill`-tool handoff to `minerva:propose` (rejected: B — durable note persistence fights the NNN model; C — `--explore` flag muddies propose's one-skill-one-contract identity). Round 1 was 1/3 (redundancy with propose's own divergent intake; trigger collision; 007 explicit-invocation). Round 2 folded in: explore diverges on the problem axis / propose on the implementation-approach axis (no redundancy); handoff rides propose's existing tested inline-arg path (no self-judged convergence predicate — avoids 014/030); disambiguated descriptions.
- [3/3 accept, rev2] whole-proposal acceptance: round 1 was 1/3 (precision gaps); round 2 folded in: name resolved to `explore`; concrete anchor literals committed (`one at a time`, `writes no file`, `minerva:propose`; propose anchors `minerva:explore`); "explore vs grill-plan don't overlap" demoted to a design constraint.

Carry-forward authoring notes for Work:
- explore/SKILL.md body must contain at least one BARE `minerva:propose` token (the inline-arg handoff line supplies it); boundary-aware matching means `minerva:propose-ship`/`-auto` will NOT satisfy the anchor.
- evals live at REPO-ROOT `evals/<skill>/`, not under `plugins/minerva/`.
- Both edit pairs (explore dir + its contract.json; propose body + propose contract anchor) must each land together or the enumerating suite reds mid-commit.
