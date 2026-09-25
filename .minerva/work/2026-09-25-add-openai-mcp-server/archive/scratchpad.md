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
- [panel — 3/3 accept, 3 with fixes] completion verification: all 13 criteria independently reproduced (make check, docker 200/401, root 1018 passed) (tier: panel — diff introduces a public interface, the MCP tool surface)
    - fix (all): proposal Approach says $ref default depth 6; shipped default 1 with optional depth 1..6 — reconcile at promote
    - fix (skeptic/arbiter): name httpx2 (not httpx) as the HTTP dependency in proposal — reconcile at promote
- [solo] review triage: 9 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — every finding had a writable failure scenario and one dominant disposition; the local-path fix narrows behavior the proposal already scoped as server-local, so no replan-vs-FIX panel)
- [solo] promote partition: 4 PROMOTE (decision, pattern, 2 reference) / MERGE httpx2, depth default, review fixes / DISCARD routine lint refactors / 0 TODO (tier: default-solo row — no entry with two defensible buckets)

## Work notes
- Used `httpx2` (pydantic's httpx fork, already a hard dependency of mcp 2.x) instead of `httpx`, avoiding a second HTTP stack. Routine choice; proposal says httpx — fix wording at promote.
- mcp 2.x renamed FastMCP → `MCPServer`; `custom_route` is an untyped decorator, so mypy --strict forced registering `/healthz` by call instead of decorator syntax.
- Strict gates bit as intended: `build_server` hit McCabe 7 with nested tool closures → split into `_add_api_tools` / `_add_discovery_tools`. Only added ignores: `CPY001` (repo LICENSE covers files) and `D103` in tests (test names document them).
- `openai_describe_endpoint` $ref depth: default 6 (as proposed) produced 300 KB for POST /responses (165 KB at 4, 55 KB at 2, 9 KB at 1). Changed to default 1 with an optional `depth` param clamped 1..6. Routine tuning, not a load-bearing divergence (tool count, approach, criteria unchanged) — reflect in proposal at promote.
- Live spec (`manual_spec` branch) lists 148 operations; it lags some newer endpoints — `openai_request` still reaches them. Documented in README Limitations.
- Verified: `make check` green on 3.13 and 3.11 (70 tests, 100% line+branch); docker image builds, /healthz 200, /mcp 401 without token, startup refused without MCP_AUTH_TOKEN; root `pytest tests/` 1018 passed.
- SDK's default HTTP body cap is 4 MiB → `MCP_MAX_REQUEST_BYTES` (64 MiB) passed to `streamable_http_app`.
