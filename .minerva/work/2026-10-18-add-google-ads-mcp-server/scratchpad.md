# Scratchpad: add-google-ads-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-10-18
- (pre-flight/intake: no in-flight collision, no open-issue match in agent-marketplace or seekless — hardcoded checks, clean, no user contact)
- [reviewed — folded] scope check: one unit, one PR, unphased; seekless wiring a separate seekless unit. Folded: size restated (~1,800 → ~2,000-2,500 lines), fix-forward unit stated as expected, dev-token sunset flagged doc-read, hand-off (tag+digest pin, spend bound in seekless) and package-public owner step stated (tier: reviewer — new server surface fails solo's no-new-interface clause; no panel clause; parallel wave)
- [rechecked — residual folded] scope check: items 1,2 partially (no explicit split trigger — declined with reason; fixture derivation is a documented procedure) and 6 not addressed (first-parse cost) — all low; folded first-load timing into criterion 4
- [reviewed — folded] approach: A (four generic spec-driven tools over Discovery v26) over B per-operation (175 tools, standing tool-shape decision), C search+mutate without discovery (cannot reach nested mutate schemas), D wrap mharnett (owner chose agent-marketplace-native). Folded: one template spelling with exact-match describe (removes catch-all tie-breaking), recorded rejection of a read-only switch (owner policy: expose every tool, bound by credential), loud response-size cap, Shorts recipe labelled unverified, login-customer-id normalization, version derivation (tier: reviewer — new interface, no existing consumer; parallel wave)
- [rechecked — residual folded] approach: item 6 partially (bump note) — folded; new low concerns folded: response cap enforced while streaming, video must already be on YouTube
- [reviewed — folded] whole-proposal: path spelling, single version setting (no base/Discovery URL override), large-response behaviour, `:verb` and host assertions in criterion 2, criterion 8 moved to a post-merge check, gsc loader adapted not copied (tier: reviewer; parallel wave, no restart — approach pick unchanged, no phases added, folds did not rewrite Goal)
- [rechecked — residual folded] whole-proposal: items 7 (optional body-vs-fixture test) and 9 (no committed derivation script) partially, low — residual folded: describe says copy templates from list_endpoints, modest pageSize; plus `describe_schema` tool added so the ~6-ref-deep Shorts path is reachable without expanding a whole tree (scope fold-audit new concern 1), linked-customer-id test (new concern 2)

## Work notes 2026-10-18
- Criterion 4 evidence (real v26 doc via GOOGLE_ADS_DISCOVERY_PATH):
    operations: 175 first load + list seconds: 0.017
    list output bytes: 19715
    describe_endpoint bytes: 3016 refs: ['GoogleAdsGoogleadsV26Services__AdGroupOperation', 'GoogleAdsGoogleadsV26Services__MutateAdGroupResult', 'GoogleRpc__Status']
    describe_schema GoogleAdsGoogleadsV26Services__AdGroupOperation bytes: 816
    describe_schema GoogleAdsGoogleadsV26Resources__AdGroup bytes: 20181
    describe_schema GoogleAdsGoogleadsV26Resources_AdGroup_DemandGenAdGroupSettings bytes: 341
    describe_schema GoogleAdsGoogleadsV26Resources_AdGroupDemandGenAdGroupSettings_DemandGenChannelControls bytes: 1361
    describe_schema GoogleAdsGoogleadsV26Resources_AdGroupDemandGenAdGroupSettingsDemandGenChannelControls_DemandGenSelectedChannels bytes: 958
    youtubeShorts reachable: True ['discover', 'display', 'gmail', 'maps', 'youtubeInFeed', 'youtubeInStream', 'youtubeShorts']
    largest describe_schema at depth 1: [(70429, 'GoogleAdsGoogleadsV26Common__Segments'), (113744, 'GoogleAdsGoogleadsV26Common__Metrics'), (282243, 'GoogleAdsGoogleadsV26Errors__ErrorCode')]
    largest describe_endpoint at depth 1: [(6066, '/customers/{customerId}/assetGenerations:generateImages'), (6111, '/customers/{customerId}/googleAds:mutate'), (16045, '/customers/{customerId}/recommendations:generate')]
- Found while building: two methods share one (method, template) pair (GET /{name} = operations.get + operations.list), so describe returns every match. A $ref often carries a sibling description, so a 'bare ref' check must not require len==1.
- Docker image build/healthz NOT run locally (docker context is the devbox droplet; left to the PR's mcp.yml docker job).
