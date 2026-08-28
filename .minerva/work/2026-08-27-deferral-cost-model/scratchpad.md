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

→ promoted to .minerva/knowledge/2026-08-28-pattern-a-corpus-assertion-must-survive-its-own-first-instance.md

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

## Verified my own work with an eye-enumerated grep, and it false-negatived

Checking that all five decomposition triggers carried the cost-of-splitting text, I grepped for
phrasings I remembered writing — "not to decompose", "reason to phase, not". Two of the five
files reported missing. Both actually had the content; the prose said "not** to re-decompose"
and "not decompose it", neither of which my pattern matched.

This is `2026-08-11-pattern-the-enumeration-is-what-fails` recurring, and recurring in the
verification step of a unit that cites that very entry three times. The pattern's own warning is
that enumerating variants by eye fails repeatedly in one sitting — it took three attempts there
too. What fixed it here is the same fix: grep for a STRUCTURAL marker (`phasing.md`, which every
trigger must cite by construction) rather than for prose I was trying to recall.

Generalizes past greps: when verifying that N sites carry a policy, assert on the thing the
policy REQUIRES them to contain — a pointer, an import, a call — never on how the sentence
around it was worded. Prose has variants; a required reference does not.

## `git branch --list` takes multiple patterns positionally

Wrote `--list pat1 --list pat2` first. Both that and `--list pat1 pat2` work, but the positional
form is git's documented shape. Verified empirically with a throwaway branch that `*-<slug>`
genuinely does NOT match `<date>-<slug>-phase-2` — which is the false-clean the widened glob
exists to close, confirmed rather than assumed.

## A presence assertion passed while the thing it guards was deleted

Wrote two tests for the required `**Failure scenario**:` line: a loose one ("is the string in the
file") and a strict one ("is it inside the `gh issue create` heredoc"). Mutation-tested by
deleting the line from the heredoc — only the strict one failed. The loose one stayed green
because the file's own explanatory prose mentions the field several times.

That is `2026-08-10-pattern-presence-assertions-rot-into-green-lies` in miniature, and the useful
detail is that the loose test was not merely weak, it was actively misleading: it reports green
for a file whose *documentation of a requirement* survives while the *enforcement* of it is gone.
The prose that explains a rule is exactly the thing that keeps a naive presence check alive after
the rule dies. Scope a presence assertion to the region that does the work.

## Retiring a vocabulary term leaks past the definition site

Removed `low` from the priority table; the table test went green immediately. Two live uses
survived elsewhere in the same file — a label hex colour and a `## Deferred work` example — and I
found both by hand-grepping, which is the unreliable method this corpus keeps writing entries
about.

The fix generalises better than the instance: derive the legal set FROM the definition (the
table) and check every *use* against it, so the enforcement cannot drift from the vocabulary and
adding a level needs no test edit. A test written as "assert `low` is absent" would have been
both wrong (the prose legitimately discusses the retired tier) and unmaintainable.

Worth noting the shape: a definition site and its use sites are two different surfaces, and a
test on the former says nothing about the latter. Same family as
`2026-07-21-pattern-catalog-semantic-drift-recurs`.

## The bar's single-sourcing is enforced by its own sentence

`test_the_bar_is_stated_in_exactly_one_place` greps every skill markdown for the bar's defining
clause and fails if any file other than `deferral-bar.md` contains it. That is a cheap, real
guard against the six-copies-and-a-plea shape — and unlike a byte-identity test across copies, it
does not assume the copies should be identical, because there are meant to be none.

## Quick decisions 2026-08-28

- [escalated to user] Scope-fit escape fired on `minerva:propose-ship-quick`: 19 files, 5 commits,
  two phases, a new public mechanism. Not the small low-risk change quick is for. User chose
  `minerva:propose-ship-balanced` for the remaining lifecycle (review → promote → ship ×2).
- [decided] The orchestrator phase-loop gap is fixed inside phase 1 rather than filed as an issue.
  It is a defect in the mechanism phase 1 delivers, phase 1 is unmerged, and filing it would be
  the deferral reflex this unit exists to cure.

## The orchestrators ship phase 1 and then silently stop

Found while running propose-ship-quick against this very unit. All three autonomous orchestrators
were taught about phasing at the SCOPE CHECK — where phases are decided — and nowhere else. Their
Phase 5/6/7 (ship gate, ship, cleanup gate) contain zero phase-awareness.

Failure scenario: hand any orchestrator a unit declaring `## Phases`. Phase 6 ships phase 1's
branch. Phase 7 polls, sees MERGED, invokes `minerva:cleanup` — which correctly defers teardown
because it IS phase-aware — and then reports success and exits. Phase 2 never ships. The unit
stalls at a report that says it finished.

This is `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` reproduced by the
unit that cites it three times: the next phase had no trigger, and the report omitted what it
skipped. Both halves, again.

The general shape worth keeping: teaching a system about a new state at the point where the state
is DECIDED does not teach it at the points where the state is CONSUMED. Deciders and executors
are different surfaces. Same family as the definition-site/use-site split that let `priority: low`
survive its own retirement earlier in this unit — twice in one work unit is not a coincidence,
it is the shape of adding a concept to an existing system.

→ promoted to .minerva/knowledge/2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces.md

## Review triage 2026-08-28 (phase 1)

Minerva audit (main model) + code quality (fresh-context reviewer, local-diff mode). All FIX.

- [FIX] #1 high `ship/references/protocol.md` — snippet read `proposal.md` unprefixed and used
  CWD-relative `sys.path`. Found independently by both lenses. Anchored both paths.
- [FIX] #2 med `work_status.phase_numbering_gaps` was implemented and unit-tested but called by
  no workflow step — the safety property was unreachable. Wired into propose's self-review.
- [FIX] #3 med `read_phases` truncated a phase title at its first physical line. Live in this
  unit's own proposal. Now joins continuations; added `phase_name()` for short report names.
- [FIX] #4 low `test_promote_mode_a_...` asserted two substrings and would have passed with the
  rule stated backwards. Rewritten as a windowed relation; mutation-tested both ways.
- [FIX] #5 low the gap test hand-built its phase list, so `read_phases` + `phase_progress` were
  never exercised together. Now parses a real three-phase section.
- [IGNORE] `read_phases` matches one spelling of `## Phases`. The read-metadata-tolerantly pattern
  earns its force from a measured corpus of variants; `## Phases` has zero instances predating
  this change. Revisit if variants appear.

## TODO: a new script function is invisible to skill prose until the plugin redeploys

Running the new self-review snippet for real resolved `PLUGIN_SCRIPTS` to the installed plugin at
`~/.claude/plugins/minerva/scripts/work_status.py`, which predates these functions, and raised
`ImportError: cannot import name 'read_phases'`. Forcing `$ROOT/scripts` works.

Failure scenario: any skill snippet that calls a function added in the same change throws
ImportError for every user whose installed plugin is older than the change, until they reinstall.
Not specific to phasing — it is a property of the documented plugin-cache-first resolution rule
(`2026-06-03-constraint-skill-wraps-script-via-importable-api`) and will recur for every future
script function. Clears the deferral bar; file it rather than widening this unit.

Mitigated here by naming the exact ImportError and its cause in all three snippets, so the
failure is diagnosable rather than mysterious.

## The reviewer found what the author's own audit could not

My minerva audit caught the path bug (a documented-constraint violation — the lens I was using).
It did NOT catch: an orphaned function I had just written and tested, a truncation bug live in my
own proposal, or a weak assertion in a test I wrote three hours earlier. The reviewer found all
three with no context.

The pattern is not "reviews are good". It is specific: the author's audit is strong on
"does this violate a rule I can look up" and weak on "is this thing I just built actually wired
to anything, and does the test I wrote actually test it". Those need someone who did not write it.

## `git rev-parse --show-toplevel` is wrong for any path that reaches into a worktree

A peer session (building a status skill) flagged this and it applied to code I had shipped in
#101 an hour earlier. `--show-toplevel` returns the *linked worktree* root when invoked from
inside one; all three phasing snippets anchor paths that reach INTO `.minerva/worktrees/`, so
they need the primary checkout. Invoked from inside a worktree they would misresolve — either
FileNotFoundError, or the stale merged copy of a proposal, which derives a wrong `next_branch`
silently.

The replacement, verified from the primary checkout, from inside a linked worktree, and from a
nested subdirectory:

    ROOT="$(cd "$(dirname "$(git rev-parse --git-common-dir)")" && pwd)"

The `cd … && pwd` is not decoration. `git rev-parse --git-common-dir` prints a RELATIVE `.git`
from the primary checkout, so the bare `dirname` is `.` — a CWD-relative ROOT, which is the exact
anti-pattern `2026-06-03-constraint-skill-wraps-script-via-importable-api` forbids. The peer's
version had this bug; I sent the correction back. Absolute in all three positions is the property
worth testing for, not "it works where I ran it".

Note the existing constraint entry already documented the `--show-toplevel` hazard in its
Implications ("a skill that genuinely needs the main checkout cannot use --show-toplevel from
inside a worktree") — and I read that entry during this unit's review and still shipped it. Knowing
the hazard is stated somewhere is not the same as checking whether MY path is one of the cases.

## A stale primary checkout reads as a missing feature

While verifying the fix, the snippet threw `ImportError: cannot import name 'read_phases'` from
the primary checkout — not because the fix was wrong, but because local `main` was still at the
pre-merge commit; I had fetched without fast-forwarding. Anything that resolves scripts through
`$ROOT` reads whatever branch that checkout happens to be on, which can lag origin arbitrarily.
Same class as the plugin-cache skew logged above: two different ways for "the code is right there"
to be false.
