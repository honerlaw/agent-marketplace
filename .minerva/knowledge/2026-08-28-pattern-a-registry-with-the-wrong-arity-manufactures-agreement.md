---
name: a-registry-with-the-wrong-arity-manufactures-agreement
description: Use when a test pins a set of sites and pairs each with one attribute — if a site can legitimately have two, the registry asserts there is one, and the code, the test and the reader all agree on an incomplete picture. Prefer deleting the dimension over adding the missing row.
metadata:
  type: pattern
---

# A registry with the wrong arity is worse than no registry — it manufactures agreement

**Date**: 2026-08-28
**Type**: pattern
**Summary**: A one-per-site registry asserts there is one; the missing second is invisible at every layer at once
**Context**: .minerva/work/2026-08-28-guard-stale-script-resolution (see git history if the worktree has been cleaned up)

## What happened

A guard had to run at every site where a skill resolves its scripts directory. The enforcing test
pinned the sites in a set of `(file, module)` pairs — one module per file — so that a *new* site
would be a deliberate registration rather than a silent omission. That much worked.

But a site can invoke more than one script. `cleanup/references/reconciliation.md` runs
`knowledge_lint` **and** `synthesis_status`. The registry named the first. The guard guarded the
first. The test confirmed the first. Every layer agreed, and the second was unprotected — the exact
failure the whole change existed to prevent, sitting inside the mechanism built to prevent it.

An independent verifier found it. Nothing in the repo could have.

## Why this is worse than a missing registry

A **missing** entry gets noticed when something fails: nothing claims coverage, so the gap is a
gap. A registry with the **wrong arity** makes a positive claim — *this site has one module* — and
then the code, the test, and the reader all inherit it. The test does not fail to see the second
module; it asserts there isn't one. That is manufactured agreement, and it is stable: re-reading
the code, re-running the suite, and re-reading the registry all confirm each other.

The tell is a registry whose row shape encodes a **cardinality assumption** nobody checked. Ask of
every `(key, value)` registry: can the key legitimately have two values? If yes, and the shape says
no, the shape is a claim you have not verified.

## The fix is usually to delete the dimension, not add the row

The obvious repair was to register the missing pair, or to allow a list of modules per file. Both
keep the assumption alive — the next site with three scripts, or a script added later, reopens it.

What closed it was removing the parameter: compare the **whole directory** instead of a named
module. Then there is no module to name, no second module to forget, and no pairing to get wrong.
The registration became files only, and the test began **counting** guards against resolutions per
file rather than checking presence — two files carry two sites each, and a presence check passes
while one of them is unguarded.

Deleting the dimension also closed a hole nobody had raised yet: every module imports siblings, so
"this named module is current" never implied "the code that will run is current". The
narrower-looking design had been imprecise all along, and the precision it seemed to buy was
imaginary.

**Generalisation:** when a registry's arity is wrong, prefer the change that makes the wrong state
unrepresentable over the change that records one more true fact. The second is correct today; only
the first is correct for the case you have not met.

## Related
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — builds on: there a concept was taught where it was decided and not where consumed; here the registry of consumers itself carried the wrong shape
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also: both replace a hand-maintained enumeration with something derived; the enumeration's *shape* can be wrong as easily as its contents
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — see also: this was found by the completion verifier, not by the author, and it is precisely a wiring defect rather than a rule violation
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also: the registry existed *because* of this rule; getting the enforcement's shape wrong is the subtler way to leave a constraint aspirational
