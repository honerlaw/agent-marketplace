# Scratchpad: date-prefixed-identity

## Panel decisions 2026-08-09

- [user-directed] scope check: ONE unit covering both knowledge entries and work units. User instruction: "do the entire thing in one unit, do not stop to ask me to continue". A prior `propose-ship-balanced` scope check had resolved to decomposition (two units, entries first); the user overrode it. Not recast as predicate evidence.
- [user-directed] rename lives in a NEW `minerva:migrate-fix` skill rather than an apply-mode on `minerva:migrate` — user chose this when asked, preserving the `020` read-only/applier split and leaving `026`/`027` intact in spirit.
- [escalated to user] work-unit scope: user chose "Both entries and work units" over entries-only. Escalation counter: 1.
- [1/3 accept → revised] approach selection, round 1: Proponent accept; Skeptic revise (7 findings); Arbiter revise. Skeptic's headline claim — that retiring `knowledge_next_nnn.py` reopens knowledge `055`'s silent-duplicate hole — was judged MISTAKEN by the Arbiter and independently by the main model: under full-stem identity an identical stem is the same PATH, so git raises an add/add conflict. `055`'s premise is inverted, not ignored.
- [2/3 accept, skeptic dissented] approach selection, round 2: A1 adopted. Folded: dual-accepting alternation extended to `cleanup/SKILL.md:19` and `ship/references/protocol.md:9` bulk globs; date semantics restated as landing-commit (ship's `--squash` has `--merge`/`--rebase` fallbacks, so it is not uniformly the ship date); `propose`'s duplicate-slug check audited for date-compatibility.
- [0/3 accept → revised] whole-proposal acceptance, round 1: both reviewers independently flagged the same two gaps — the 532-occurrence wikilink rewrite had NO documented mechanism, and the proposal's own named worst case (a dated work unit invisible to `cleanup`/`ship` bulk scans) had no success criterion.
- [2/3 accept, skeptic dissented] whole-proposal acceptance, round 2: accepted with five Arbiter folds — (1) extend the allocation rewrite to `minerva:promote` and invert `test_promote_invariant.py:234`; (2) add `--follow` to date derivation; (3) add calendar validation so criterion 5 is achievable; (4) add criteria 15b/15c for the banner marker and allocator removal; (5) pin `width` in the composite sort key.

## Panel concerns 2026-08-09

Logged from dissenting Skeptics, for `minerva:review` to scrutinise:

- **Rename-history sensitivity (medium-high).** `--follow` is now specified, but the Arbiter noted the cited example (`9f40272` renaming `005-…`→`008-…`) happens to land on the same calendar day as the original add, so the fix is unverified against a real cross-day rename. Worth a fixture.
- **Criterion 8 is judgment-based, not mechanical** (contrast criterion 9's byte-identity assertion). Distinguishing fenced examples and superseded-entry prose from stray live links needs a read, not a script.
- **Regex/script surface was undercounted twice** across rounds. The sweep must be grep-enumerated, not driven off any count in the proposal.
- **`propose`'s steps 3–8 are a procedure, not a glob.** Risk of "just fix the regex" when the whole allocate-then-name flow must be rewritten.

## Notes
