# Scratchpad: add-google-search-console-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-25
- [solo] in-flight check: no collision; adjacent local branch `mcp-openai-stateless-and-publish` (already merged as #128); no open issues/PRs; peer discovery skipped (not authorized) (tier: hardcoded pre-flight, no match)
- [reviewed — folded] scope check: one unit, one PR; Skeptic found the root README.md "MCP servers" table missing from the file list and the size estimate understated (~2,000-2,800-line diff, same order as mcp/openai's 2,092) — both folded (tier: reviewer — multi-file, solo predicate fails single-surface)
- [rechecked — clean] scope check: fold-audit confirmed items 1–5 addressed; one cosmetic range-bound note
- [panel — 3/3 accept, 2 with fixes] approach: B — one typed tool per live operation (10), no generic escape hatch; rejected A (generic request + discovery-doc tools: model must percent-encode siteUrl, openai check_path rejects it) and C (B + generic escape hatch: reintroduces caller-controlled path) (tier: panel — new public tool interface, and doubt over tension with 2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools)
    - fix (skeptic/arbiter): state explicitly why GSC is that decision's "narrow capability" carve-out (10 live ops vs 352, slow-moving)
    - fix (skeptic/arbiter): record the size/stability split as a knowledge entry at promote
    - fix (skeptic/arbiter): add a staleness mitigation (README records discovery revision; revisit if it grows materially)
    - fix (skeptic/arbiter): tie GSC_READ_ONLY to the minimal-credential-surface criterion
    - fix (skeptic/arbiter): mark the Mobile-Friendly Test retirement as to-confirm during implementation
    - fix (arbiter): explain generic candidate's 3-tool count (no upload/download surface)
- [reviewed — folded] whole-proposal: gsc_inspect_url is a body-based POST under v1/ not covered by criterion 3; two path prefixes unflagged; read-only scope claim overstated — criterion 3, Approach and criterion 7 revised (tier: reviewer — multi-file proposal, solo predicate fails)
- [rechecked — clean] whole-proposal: fold-audit confirmed items 1–3 addressed; item 4 (google-auth mypy risk, low) left as implementation risk
