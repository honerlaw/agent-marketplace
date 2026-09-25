# The OpenAI MCP server became `mcp/openai-ads/`; general OpenAI API access was retired

**Date**: 2026-09-25
**Type**: decision
**Summary**: mcp/openai renamed to mcp/openai-ads for the Ads API; general-API server and image retired
**Context**: .minerva/work/2026-09-25-refocus-openai-mcp-on-ads-api (see git history if the worktree has been cleaned up)

## Context
`mcp/openai/` wrapped the general OpenAI REST API (`api.openai.com/v1`: responses, files, models)
with five generic tools. The user asked for it to be "focused on their advertisement API so that
we can create campaigns / ads / ad groups". A 3/3 panel weighed three options:
- (A) Repurpose it under the same name.
- (B) Rename it to `mcp/openai-ads/` and retarget it.
- (C) Add a sibling Ads server and keep the general one.

## Finding
Option B was chosen. The directory moved with `git mv`. The package is `openai_ads_mcp`, and the
distribution, console script and GHCR image are `openai-ads-mcp`. The server keeps the generic
shape with four tools: `openai_ads_request`, `openai_ads_multipart_request`,
`openai_ads_list_endpoints` and `openai_ads_describe_endpoint`. `openai_download` was dropped
because the Ads API has no binary responses. The configuration moved to `OPENAI_ADS_*` variables.

- A was rejected because the `openai-mcp` image and client configs would have silently switched
  to a different API and a different kind of key.
- C was rejected because it doesn't make *this* server ads-focused.
- The `-ads` suffix follows `reddit-ads`.

The general-API server no longer exists in the repo. Its last `ghcr.io/<owner>/openai-mcp` image
stays pullable but frozen.

## Implications
- Knowledge entries dated before 2026-09-25 that point at `mcp/openai/` describe the retired
  general-API server. Its patterns (the path guard, discovery, HTTP auth) live on in
  `mcp/openai-ads/`, which `mcp/README.md` now names as the template to copy.
- If general OpenAI API access is wanted again, add it as its own server rather than widening this
  one. The Ads server's instructions and safety posture are specific to spending money.
- The Ads server's instructions steer spending, but the server doesn't enforce them: create
  `paused`, send `Idempotency-Key` on creates, and confirm before activating or changing budgets.
  Real limits come from the ad account's own spend limits.
- Git shows the seven most heavily rewritten files as delete+add rather than renames, because
  they fall under git's 50% similarity threshold even though they were moved with `git mv`.
  `git log --follow` stops at the rename commit for those files.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — builds on: the generic shape kept through the refocus
- [[2026-09-25-decision-mcp-server-tool-shape-follows-api-size-and-stability]] — builds on: 87 fast-growing operations point to the generic shape
- [[2026-09-25-reference-openai-ads-api-facts-for-mcp-servers]] — the API facts behind the tool and config choices
- [[2026-09-25-decision-mcp-servers-ship-a-ci-env-for-the-image-smoke-test]] — see also: `ci.env` now sets `OPENAI_ADS_API_KEY`
