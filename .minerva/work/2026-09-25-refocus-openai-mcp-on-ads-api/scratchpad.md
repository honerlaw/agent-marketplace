# Scratchpad: refocus-openai-mcp-on-ads-api

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-25
- [reviewed — clean] scope check: one unit, one PR (tier: reviewer — multi-file so solo fails; no panel clause). Skeptic accepted; its noted-but-dismissed-for-scope items (undercounted README references incl. `mcp/google-search-console/README.md` `../openai` link; `git mv` untested; frozen `openai-mcp` image) don't bear on the scope call and were folded into the draft proposal before the whole-proposal gate
- [panel — 3/3 accept, 3 with fixes] approach: B — rename to `mcp/openai-ads/`, retarget at the Ads API, remove the general-API server; rejected A (repurpose under old name: silently changes `openai-mcp` meaning) and C (sibling: doesn't refocus *this* server) (tier: panel — public interface change + non-dominant A/B)
    - fix (proponent/arbiter): "Adding a server" template pointer must be re-pointed at a surviving server
    - fix (skeptic/arbiter): broaden the stale-reference grep to `openai-mcp` and the dropped env vars
    - fix (skeptic/arbiter): name the general-API-removal trade-off in Why; make the live-spec check environment-conditional
- [panel — 3/3 accept, 3 with fixes] whole-proposal: accepted (tier: panel — proposal defines a new public interface: tool names, env vars, package/image; fail-closed)
    - fix (skeptic/arbiter): new criterion + test that instructions carry hierarchy/micros/create-paused/Idempotency-Key/confirm-before-activate guidance
    - fix (skeptic/arbiter): header forwarding softened to "retry-after if present" + defensive rate-limit prefixes, with a retry-after test (live 401 confirmed x-request-id/openai-version/openai-processing-ms)
    - fix (all): naming clarified (dist `openai-ads-mcp`, module `openai_ads_mcp`); base64 branch removed; spec parsed with json.loads, pyyaml dropped; live-spec half of criterion 3 marked best-effort

## Work notes
