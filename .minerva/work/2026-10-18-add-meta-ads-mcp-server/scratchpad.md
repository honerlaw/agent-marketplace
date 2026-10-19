# Scratchpad: add-meta-ads-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-10-18
- pre-flight: no collision (no meta/facebook branch, PR or issue; adjacent: shipped unit 2026-10-18-add-google-ads-mcp-server, the template); peer messaging not authorized, skipped
- [user-directed] full campaign access, no read-only default (owner, 2026-10-18)
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — multi-file new server, not single-surface; parallel wave). Skeptic accepted; its content points (token-by-value scrub, uploads, spec fetch failure, form bodies) carried into the other gates
- [reviewed — folded] approach: generic spec-driven tools kept; folded batch refused (path `/` + `batch` key), check_params over query+body+page-URL query incl. method/suppress_http_code/callback, three-layer scrub (literals, paging-only URL strip, access_token keys), follow_page query checked, spec baked into the image (alternative F dominant), licence checked (tier: reviewer — new tool surface, no existing consumer; parallel wave)
- [rechecked — residual folded] approach: fold-audit accepted; residuals folded — no caller headers at all, granular_scopes kept, hash location named; its new concern (refusing method/callback might block real params) disproven by a spec scan (no Marketing API param uses them; access_token only on 2 Instagram token-exchange #gets)
- [reviewed — folded] whole-proposal (first wave): discarded as stale — the approach fold rewrote ## Success criteria (restart condition)
- [reviewed — folded] whole-proposal (restart): content hash over extracted specs (archive bytes unstable), httpx/httpx2 loggers to WARNING + log-capture test (seekless knowledge 2026-10-13-constraint-httpx-logs…), python-only Dockerfile spec step, one-line-per-entry rule (tier: reviewer — re-selected after restart)
- [rechecked — escalated] whole-proposal: fold-audit found criterion 5 regressed (unfiltered list wrongly claimed over the cap) and a new medium concern (test fixture vs hash check) → panel (both folded before the panel: expected hash a constructor arg, no env knob)
- [panel — 3/3 accept, 2 with fixes] whole-proposal: accepted (tier: panel — fold-audit escalation; quorum 3/3)
    - fix: Goal says writes are mock-tested; first live write is a manual owner-approved criterion 9 (create PAUSED campaign, read, delete)
    - fix: spec↔Graph-version mapping recorded (codegen not versioned per Graph version; README caveat)
    - fix: appsecret_proof spelled out (key = app secret, message = token, hex); hash recipe = spec_fetch.content_hash code
    - fix: describe on a concrete path errors toward list_endpoints; 50 KB is a test budget on named outputs; request size bounded by MCP_MAX_REQUEST_BYTES only
    - fix: README notes (ids=, non-hermetic build, logging); tests: nested key passes, ids/include_headers pass, spend warning in description, duplicate pair, token_status without app creds
- live facts 2026-10-18 (owner's Doppler token injected, nothing printed): debug_token with app|secret bearer → SYSTEM_USER, never expires, scopes incl. ads_management; GET /me/adaccounts with bearer + proof → 200 (act_1883284226381771, USD); /me with bearer only → 200

## Work notes
- httpx2 2.14 logs on logger `httpx2` (only name found in its source); httpcore2 2.14 present.
