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
