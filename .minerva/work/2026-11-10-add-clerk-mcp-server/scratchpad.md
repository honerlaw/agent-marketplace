# Scratchpad: 2026-11-10-add-clerk-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-10
- [reviewed — clean] scope check: one unit, one PR in agent-marketplace; the seekless wiring is a dependent follow-up unit (needs the published digest), as in the microsoft-ads precedent; Skeptic noted wheel packaging of bapi.json and a response-size cap as build items (tier: reviewer — introduces a new server surface, no panel clause; parallel wave)
- [reviewed — folded] approach: option A (generic spec-driven tools over a vendored pinned BAPI spec + pinned Clerk-API-Version); rejected B (runtime YAML fetch) and C (typed users-only tools). Folded: path guard refuses `%`/whitespace outright and asserts the sent URL; no redirects; MAX_BODY_CHARS cap; credential-minting endpoints stay reachable and are named; opt-in CLERK_READ_ONLY (default off); prompt-injection note; read-only-vs-write carried to the wiring unit as an owner decision (tier: reviewer — new tool surface; author's blast-radius doubt answered "not high: deploys nothing"; parallel wave)
- [rechecked — clean] approach: fold-audit found all 8 items addressed; two lows (verify no spec path needs `%`; scrub before truncate) folded into the plan
- [reviewed — clean] whole-proposal (first wave): accept; result discarded at the restart check
- [reviewed — folded] whole-proposal (restart): the approach fold added the read-only criterion to ## Success criteria, so the first-wave review was stale. Re-reviewed: folded method handling (string, upper-cased, five allowed), version-header fallback to 2026-05-12, spec provenance (commit/blob/sha256), forwarded-header list without set-cookie and no retries, PII note, case-insensitive query refusal, explicit file plan (tier: reviewer; parallel wave restart)
- [rechecked — residual folded] whole-proposal: all 9 items addressed; residuals folded: scrub.py named as microsoft-ads' Scrubber reduced to one literal; method is a plain string so `get` reaches the server's normalization
