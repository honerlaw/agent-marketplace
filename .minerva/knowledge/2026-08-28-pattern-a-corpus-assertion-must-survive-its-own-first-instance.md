---
name: a-corpus-assertion-must-survive-its-own-first-instance
description: Use when writing a test that asks the whole corpus about a property a new feature introduces — "no file does X yet" expires the moment the feature is used, and the tempting fix (an exclusion list) gets weaker as adoption grows. State the invariant about the property instead, and one-directionally.
metadata:
  type: pattern
---

# A corpus-wide assertion about a new feature must survive the feature's own first use

**Date**: 2026-08-28
**Type**: pattern
**Summary**: "Nothing does X yet" expires on first adoption; assert the property, not the corpus's current contents
**Context**: .minerva/work/2026-08-27-deferral-cost-model (see git history if the worktree has been cleaned up)

## What happened

Plan-level phasing was safe to add to six consumers at once only because a work unit that does
not declare `## Phases` is untouched by any of it. That inertness needed an assertion, and the
obvious one was: *no unit in `.minerva/work/` reads as phased.*

It failed on its first run — against the very unit that introduced phasing, which is legitimately
phased. The assertion was true only in the window between writing the parser and using it.

## The tempting fix is the wrong one

Excluding the known-phased slugs restores green immediately. It is also strictly self-defeating:
the exclusion list grows with every phased unit, so the test covers a smaller fraction of the
corpus exactly as the feature gets more use. A guard that weakens as its subject spreads is worse
than no guard, because it still reports green.

## The fix

Restate the invariant so the feature's own instances satisfy it. Not "no unit is phased" but
**"a unit that declares no `## Phases` heading parses to no phases"** — which is the actual
inertness claim, and stays true forever no matter how many units adopt the feature.

## State it one-directionally

The first rewrite overshot into an `iff`: *heading present ⇔ phases found*. That is also wrong,
and wrong in a way a unit test two functions earlier already contradicted — an **empty**
`## Phases` section legitimately parses to nothing. The safe direction is the one that encodes
the safety property: **no heading ⇒ no phases**. The converse is a separate claim, usually false,
and asserting it buys nothing.

The general form: when a corpus-wide test exists to protect a *safety* property, only the
implication that carries the safety belongs in the assertion. Adding the reverse direction for
symmetry is how a correct test acquires a false clause.

## The tell

Any assertion phrased as a census of what the corpus currently contains — "no file", "every
file", "exactly N" — where the number or the emptiness is a fact about *today* rather than about
the rule. Ask: what does this assert after the feature succeeds? If the answer is "it fails, and
I add an exception", rewrite it before merging, not after.

## Related
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on: there the assertion could not fail; here it could only fail, and for the wrong reason. Both are tests whose relationship to their subject decays over time
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also: both replace a hand-maintained fact about the corpus with a question asked of it
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also: the reason the inertness claim needed an assertion at all
