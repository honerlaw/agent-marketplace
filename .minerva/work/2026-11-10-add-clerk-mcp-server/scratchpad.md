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

## Work notes 2026-11-10
- Built mcp/clerk from openai-ads: config/safety/api/spec/server/http_app/main/__main__ + scrub.py (microsoft-ads Scrubber reduced to one literal). Vendored bapi.json (630,282 bytes) converted with system PyYAML via `python3 -I`; bapi.LICENSE carries Clerk's MIT text (Copyright (c) 2025 Clerk) plus commit/blob/sha256.
- Path guard is an allowlist of characters (letters, digits, `/-._~:@!$&'()*+,;=`) rather than a denylist: that refuses `%`, whitespace, non-ASCII (fullwidth dots too) in one rule. Every vendored path template (ids filled) passes it; `/logs/{event_time_and_id}` holds a colon, which is allowed.
- `check_query` uses a `QueryValue` alias: PEP 695 generics need 3.12 and the package targets 3.11.
- Slip: a scripted `.replace('== 4', '== 3')` on the copied test_http.py also rewrote `== 401`/`== 400`; the test run caught it and it was reverted by hand; diff against the template confirms only intended changes.
- Deletion checks: removing each guard fails tests — allow `%` (9), allow dot segments (5), drop read-only (8), case-sensitive version key (2), follow redirects (1), no JSON scrub (2), no header scrub (1), no error scrub (1), forward set-cookie (1), drop version header (1).
- Wheel (pip wheel) contains bapi.json + bapi.LICENSE; docker image: /healthz ok, POST /mcp without bearer 401, spec loads in-image (2026-08-20, 264 ops), runs as uid 10001. Python 3.11.14 venv: 108 passed, 100%, mypy clean.
- Two probes refused by this session's permission check (DCR earlier; unauthenticated GET api.clerk.com/v1/users now); no live Clerk call was made.
