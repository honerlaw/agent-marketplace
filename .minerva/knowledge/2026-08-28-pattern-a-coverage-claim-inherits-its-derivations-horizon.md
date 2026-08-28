# A coverage claim inherits the horizon of the derivation that produced it

**Date**: 2026-08-28
**Type**: pattern
**Summary**: Deriving consumers from a definition site finds only what that site names; search for the construction instead
**Context**: .minerva/work/2026-08-28-observable-orchestrator-mode (see git history if the worktree has been cleaned up)

## Context

A migration replaced a prose carve-out — a gate bypassed by the skill judging *"am I being invoked
by an orchestrator?"* — with an observable argument. To avoid hand-maintaining a list of affected
skills, the contract test derived its set from the corpus: every `minerva:<skill>` named in the
three autonomous orchestrators' phase protocols. Six skills, all migrated, suite green, coverage
reported complete.

`minerva:synthesize` still carried the old carve-out. It is reached at **two** hops — an
orchestrator invokes `minerva:cleanup --yes`, which invokes synthesize during reconciliation — so
no orchestrator's phase protocol names it, and the derivation could not see it. It was found by a
hand audit, not by the test built to find exactly this.

## Finding

**Deriving consumers from a definition site is corpus-grounded and still bounded: it finds the
consumers that site names, and nothing further out.** "I asked the corpus" is not the same as "I
asked the whole corpus." The derivation has a horizon, and the coverage claim inherits it —
silently, because within its horizon the check is genuinely correct.

The complementary check is cheap and hop-independent: **search the corpus for the construction
being removed, not for a list of consumers.** Here that is one regex over all skill prose for the
self-judgment phrasing, asserting none remains. It has no notion of hops, so it cannot have a
horizon, and it would have found synthesize on day one.

## Implications

- When a migration replaces construction A with construction B, ship **two** checks: a positive one
  (every known consumer uses B) and a **negative** one (A appears nowhere). The negative check is
  the one that survives an incomplete consumer list.
- A negative check is also the cheaper of the two to write, and it does not need updating when a
  consumer is added — which is precisely when a positive check goes stale.
- State the derivation's horizon in the test itself. A reader who knows the set comes from
  one-hop mentions can tell what it does not cover; a reader who sees only "derived from the
  corpus" reasonably assumes completeness.
- This is the enumeration failure in [[2026-08-11-pattern-the-enumeration-is-what-fails]] one level
  up: asking the corpus beats enumerating by eye, but *which question* you ask it still bounds the
  answer.

## Related
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — builds on
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — builds on
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — see also
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — see also
