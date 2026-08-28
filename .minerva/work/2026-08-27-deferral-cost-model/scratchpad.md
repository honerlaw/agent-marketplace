# Scratchpad: deferral-cost-model

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## A corpus-wide assertion about a new feature must survive the feature's own first use

Wrote the phasing inertness guarantee as `test_no_existing_unit_in_the_corpus_reads_as_phased`
— asserting no unit in `.minerva/work/` reads as phased. It failed immediately, on THIS unit,
which is the first legitimately-phased proposal in the corpus. The assertion was true only in
the window between writing the parser and using it.

Two ways out, and the tempting one is wrong. Hardcoding an exclusion list of known-phased
slugs rots with every phased unit added, and it makes the test weaker exactly as the feature
gets more use. The fix was to restate the invariant so the feature's own instances satisfy it:
**no `## Phases` heading implies no phases parsed**, which is the actual inertness claim and
stays true forever.

Second trap on the way: I first wrote it as an `iff` (declared heading ⇔ phases found). That
is also wrong — an EMPTY `## Phases` section legitimately parses to nothing, which I had
already written a unit test for two functions earlier. Contradicted my own test within the
same file. The one-directional form is the only correct one.

General shape: when a test asks the corpus about a property a new feature introduces, write it
about the property, not about the corpus's current contents. "Nothing does X yet" expires the
first time something does.

## The phase predicate stays hermetic on purpose

`phase_progress` takes the merged-branch set as an argument rather than shelling out to git.
`work_status.py` is a pure reader of declarations and its tests need no repo/network/fixtures;
`ship` and `cleanup` already hold the `git branch --merged` / `gh pr list` result when they
call it. Keeps the module's existing testability property intact.

## Phase 1 keeps the bare `<date-slug>` branch

Drafted as `<date-slug>-phase-N` for all N, changed during execution. Phase 1 on the bare slug
means the worktree dir and phase-1 branch stay matched, so all six `Target resolution` blocks,
the duplicate-slug check and `cleanup`'s merge detection work unchanged on a phased unit's
first phase. Only phases 2+ are new. Also removed the bootstrapping problem — this unit needed
no manual deviation to create itself.

## The 9KB skill budget forced a refactor, and that was the right call

`cleanup/SKILL.md` sat at 9204 of 9216 bytes on main — twelve bytes of headroom. Any change to
that skill was going to hit the wall; phasing just happened to be the one that did. Moving the
`## Removal` protocol verbatim into `references/removal.md` and leaving a read-directive pointer
is exactly the progressive-disclosure pattern unit 035 established, so the gate did its job:
it converted "add prose to a full file" into "split the file", which is what should happen.

Worth noting the budget test is the only thing that would have caught this. Nothing else in the
suite cares how long a SKILL.md is, and the cost of an over-long one (silent context bloat at
every invocation) is invisible at authoring time.

Also tripped it on `work/SKILL.md` — committed a 19-byte overflow because I ran the suite
BEFORE the final edit rather than after. Order matters: run the gate after the last write, not
after the last write you happened to be thinking about.
