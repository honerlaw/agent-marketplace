# Scratchpad: swap-financials-for-utils-plugin

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Review triage 2026-05-20
- [FIXED]   #1 high .claude-plugin/marketplace.json:11-14 — removed financials entry, added utils entry
- [FIXED]   #2 med  README.md:10,25 — updated install example + plugin table to match new state
- [IGNORED] #3 low  docs/superpowers/plans/*, docs/superpowers/specs/* — historical planning docs, not current-state docs

## Review fixes 2026-05-20
- Review fix: .claude-plugin/marketplace.json — replaced financials entry with utils entry
- Review fix: README.md — updated install example to `./install.sh utils` and replaced financials row in plugin table with utils/humanizer

## Review finding 2026-05-20
- Proposal Approach underspecified: removing `plugins/financials/` and adding `plugins/utils/` requires updating `.claude-plugin/marketplace.json` (the canonical plugin registry) and `README.md` (the plugin table + install example). These should be folded into the final Approach when promote rewrites it to match reality.
