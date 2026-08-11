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

- [3/3 accept] completion verification: all 7 success criteria independently verified against the working tree by Proponent + Skeptic + Arbiter; 143 minerva tests pass; the only suite errors (test_browser/test_storage/test_pull, ModuleNotFoundError 'lib'/'pull') are pre-existing on main and outside this diff. No mid-work divergence occurred (the YAML colon-space fix in the explore description was operational). One operational note: an unquoted YAML description cannot contain a colon-space (`: `) — `minerva:propose` is fine (no space) but `brainstorming: a` broke the parse; fixed by replacing with an em-dash.

- [skipped — small] review triage: all 3 findings low-severity (evidence: independent reviewer rated 0 high / 0 medium / 3 low; disposition is a no-op artifact change; no FIX finding → Replan-vs-FIX precondition not met). Dispositions: #1 IGNORE (full `pytest` red only from pre-existing unrelated `lib`-import collection errors in test_browser/test_storage/test_pull — outside this diff, reproduced on main); #2 SUGGEST; #3 IGNORE (propose-row Situation disambiguation is correct as-is).

## Review finding 2026-06-07
- [SUGGEST] Harden the advisory behavioral eval with a second `evals/explore/behavioral.json` case exercising a "drop / don't build" terminal outcome (rubric: explore reaches a well-reasoned NO without writing files or handing off). Optional — behavioral evals are advisory per [[2026-05-31-decision-behavioral-evals-provisional]]; deferred, not blocking ship.

Carry-forward authoring notes for Work:
- explore/SKILL.md body must contain at least one BARE `minerva:propose` token (the inline-arg handoff line supplies it); boundary-aware matching means `minerva:propose-ship`/`-auto` will NOT satisfy the anchor.
- evals live at REPO-ROOT `evals/<skill>/`, not under `plugins/minerva/`.
- Both edit pairs (explore dir + its contract.json; propose body + propose contract anchor) must each land together or the enumerating suite reds mid-commit.

- [synthesis] no-op (1 un-synthesized entry 031, below threshold; overview.md current at watermark 030, no link rot)
