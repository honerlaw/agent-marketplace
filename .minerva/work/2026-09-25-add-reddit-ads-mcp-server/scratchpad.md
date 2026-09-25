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
