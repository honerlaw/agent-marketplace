# Scratchpad: add-reddit-ads-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-25
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — multi-surface diff (new server + CI + READMEs) fails solo's single-surface clause; Skeptic accepted; noted-but-dismissed: size may exceed openai's PR because of the token manager, and the PR body must call out the openai CI behavior change)
- [panel — 3/3 accept, 3 with fixes] approach: A — generic spec-driven tools over Reddit's official openapi.json, OAuth refresh manager + static mode, copy-adapt (no shared package), per-server ci.env for the docker smoke job (tier: panel — changes the cross-cutting mcp.yml / per-server contract); rejected B per-op tools, C curated tools, D mcp/common, enumerating env vars in the workflow, lazy credential validation
    - fix (proponent): drop PUT from the method list; the spec uses GET/POST/PATCH/DELETE only
    - fix (skeptic/arbiter): describe returns scope null for the one op without security; UA default carries a visible placeholder username; note token-manager decomposition for the complexity gates; add a dotted-query-key test (later superseded by follow_page)
    - fix (arbiter): keep the July 13th 2026 date; it is in the spec verbatim (the Skeptic's fabrication claim was a grep miss)
- [reviewed — folded] whole-proposal: pagination contradicted the spec's "follow next_url directly" → added reddit_ads_get_page with check_page_url; bootstrap now lists all four scopes incl. adsdatadeletion; POST wording and RateLimit-header provenance fixed; method-enum and naming concerns dismissed (enum mirrors openai; openai already uses text_filter) (tier: reviewer)
- [rechecked — escalated] whole-proposal: fold-audit found a new load-bearing concern — GET-only page tool cannot continue the four POST paginators (reports/history/query) — plus a wrong page.token count → panel
- [panel — 3/3 accept, 2 with fixes] whole-proposal: sound after revising to reddit_ads_follow_page(url, method, body?) and correcting to 36 ops (tier: panel — fold-audit escalation)
    - fix (skeptic): Open Question + tool description caveat that POST re-send-body is inferred, not live-confirmed; scope-null wording covers absent or empty; DELETE purpose named
    - fix (arbiter): surface the POST-pagination caveat in the tool description/README; "has no `security` key at all" wording
- [panel — 3/3 accept, 1 with fixes] completion verification: all 13 criteria independently reproduced by all three (make check 112/100%, both images /healthz 200 via ci.env, openai 78, root 1018) (tier: panel — diff changes the cross-cutting mcp.yml per-server contract)
    - fix (arbiter): record why check_path's small delimiter blocklist is acceptable (inherited verbatim from openai; defense-in-depth on a fixed httpx base_url) — noted in work notes for promote
    - fix (arbiter): check_page_url host comparison was case-sensitive — made case-insensitive in code (urlsplit lowercases scheme already) + test

## Work notes 2026-09-25
- Reddit publishes its Ads API v3 spec at https://ads-api.reddit.com/api/v3/openapi.json (no auth, ~1 MB JSON, OpenAPI 3.1, 108 ops / 80 paths). WebFetch is blocked on ads-api.reddit.com; plain curl works. Only GET/POST/PATCH/DELETE; every body application/json.
- Operation descriptions embed a rendered HTML rate-limit panel with inline SVG; stripping tags takes POST /ad_accounts/{id}/campaigns describe from ~14 KB to ~10 KB at depth 1 and leaves readable "Policy Slug / Window / Quota" text.
- Pagination: next_url/previous_url are full URLs the spec says to follow directly; four POST endpoints paginate (reports, history, two /query). page.token is a shared components parameter on 36 ops.
- Rate limits use IETF `RateLimit` / `RateLimit-Policy` headers (docs, not spec — the spec declares no response headers).
- Token endpoint can answer HTTP 200 with {"error": "invalid_grant"}; the token manager checks for access_token rather than status alone.
- Refresh tokens: the refresh response may carry a new refresh_token; kept in memory only.
- Tests: the token manager's clock is a module-level `now` so tests monkeypatch it instead of time.monotonic (patching the time module would disturb anyio).
- CI: docker smoke job now reads `<server>/ci.env`; both images verified locally to answer /healthz with their ci.env. Root pytest 1018 passed; openai make check 78 passed; reddit-ads make check 112 passed at 100% line+branch.
- check_path keeps openai's small delimiter blocklist (?, #, \) alongside structural allowlist checks (single leading /, no ://, no .. after one unquote). Judged acceptable because it is a fixed RFC 3986 delimiter set, not an open surface, and requests are confined by httpx base_url anyway (completion panel note; cf. 2026-08-22-pattern-a-denylist-safety-guard-fails-open).
- main moved during work: #129 added mcp/google-search-console without touching mcp.yml (it starts with only MCP_AUTH_TOKEN via ADC fallback). The ci.env contract therefore needs mcp/google-search-console/ci.env too — added on rebase (routine: the approved plan's "every server ships ci.env" applied to a new sibling).
