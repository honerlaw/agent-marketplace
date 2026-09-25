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
- `git mv mcp/openai mcp/openai-ads` then `git mv src/openai_mcp src/openai_ads_mcp`; bulk sed for identifiers, then hand edits.
- Timeout default lowered 600 → 120 s: the 600 s default existed for long model generations on the general API; Ads calls are CRUD/reporting. Not in the proposal text — minor default change, called out in README config table.
- `mcp` 2.x `Client` exposes server instructions as `client.instructions` (no `initialize_result`). Used it to assert the instructions reach clients.
- Live spec (2026-09-25): discovery lists 87 operations incl. `POST /campaigns — Create Campaign`, `POST /ad_groups — Create Ad Group`, `POST /ads — Create Ad`; depth-1 describe of POST /campaigns ≈ 3.4 KB (Ads schemas are small: depth 3 ≤ 13 KB even for insights).
- Live 401 from `api.ads.openai.com` carries `x-request-id`, `openai-version`, `openai-processing-ms`, plus Cloudflare cookies (`set-cookie`, `cf-ray`) — the allowlist keeps the cookies out.
- Docker: `docker build` + `docker run --env-file ci.env` → `/healthz` = ok, `POST /mcp` without token = 401.
- `make check`: 73 passed, 100% line+branch coverage; ruff/format/mypy clean.
- Stale-reference grep (criterion 8): zero hits for the ten retired identifiers outside `.minerva/`; every `openai` hit is openai-ads or the vendor.
