# Scratchpad: add-openai-mcp-server

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-09-25
- [reviewed — folded] scope check: one unit, one PR — Skeptic flagged the draft's path-scoped `mcp.yml` as reproducing the "tests go dark" incident in 2026-08-11-decision-ci-runs-the-whole-suite; folded: no `paths:` filter, glob discovery, fail on zero collected tests; also argued (b) phases vs (c) units separately and re-estimated size (tier: reviewer — multi-file, not provably small; no panel clause)
- [rechecked — residual folded] scope check: item 5 partially addressed ("touches no existing code paths" wording alongside the README edit) — wording folded
- [panel — 3/3 accept, 3 with fixes] approach: A — five generic spec-driven tools in Python on mcp 2.x; rejected B (per-operation tools, exceeds client tool limits), C (curated subset, fails "full control"), TypeScript (repo is Python) (tier: panel — introduces a public interface, the MCP tool surface)
    - fix (skeptic/arbiter): mcp.yml CI precedent named; required-check status is a repo setting surfaced in final report
    - fix (skeptic/arbiter): multipart local paths are server-local — base64 for remote HTTP/Docker clients
    - fix (skeptic/arbiter): accepted cost risk named; rate/spend limits deferred to Open Questions
    - fix (skeptic/arbiter): spec GitHub egress dependency accepted; `OPENAI_OPENAPI_PATH` local-file option
    - fix (skeptic/arbiter): binary size cap `OPENAI_MCP_MAX_BINARY_BYTES` (20 MiB) configured and tested
    - fix (skeptic/arbiter): first pyproject/Dockerfile acknowledged; hatchling backend named
    - fix (proponent/skeptic/arbiter): `stream: true` buffered — stated v1 limitation; mcp pin verified (2.2.0)
- [user-directed] approach: strict quality gates added (ruff ALL + McCabe 5 + pylint limits, ruff format, mypy --strict, 100% line+branch coverage) — user: "make sure that we add extremely strict linting / static analysis / test suites"
- [panel — 3/3 accept, 3 with fixes] whole-proposal: sound (tier: panel — public interface; fail closed)
    - fix (skeptic/arbiter): `openai_download` save_to is server-local — large-binary retrieval limitation stated for HTTP/Docker, added to Open Questions and README criterion
    - fix (skeptic/arbiter): path-safety criterion covers all three path-taking tools
    - fix (skeptic/arbiter): real stdio subprocess smoke test criterion added
    - fix (proponent/skeptic/arbiter): response-header allowlist named; $ref depth default 6
    - fix (main model, implementation detail): `MCP_MAX_REQUEST_BYTES` (64 MiB) since the SDK caps HTTP bodies at 4 MiB
