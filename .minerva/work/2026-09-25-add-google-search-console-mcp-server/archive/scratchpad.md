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
- [panel — 3/3 accept, 1 with fixes] completion verification: all 7 criteria independently reproduced by Proponent and Skeptic (make check, 3.11, docker 200/401, gate-config diff, mcp.yml untouched) (tier: panel — diff introduces a public tool interface)
    - fix (arbiter): tighten the row-limit test to assert the actual field name (`query.row_limit`)
    - fix (arbiter): remove the no-op `@pytest.mark.anyio` from the sync bearer-scheme test
- [solo] review triage: 14 FIX (code findings 1–7, 9–11 + README fixes; minerva audit findings 2 → promote rewrite) / 0 SUGGEST / 1 IGNORE (8, concurrent-refresh test: no failure scenario) (tier: default-solo row — no finding had two defensible dispositions; the dot-segment fix is a bug fix inside the approach, not a divergence, so no replan-vs-FIX panel)
- [solo] promote partition: 4 PROMOTE / 6 MERGE INTO PROPOSAL / 3 DISCARD / 0 TODO (tier: default-solo row — no entry had two defensible buckets; openai's opaque transport errors discarded: the call still fails as an error, no wrong output, so not a defect under the deferral bar)

## Work notes
- Mobile-Friendly Test API: confirmed retired 2023-12-01 (Google announced April 2023; tool, report and API shut down together). Excluded; open question closed.
- Discovery doc: `searchType` and `type` both exist on SearchAnalyticsQueryRequest; `type` is current, `searchType` deprecated. Filter enums are UPPER_CASE (EQUALS, CONTAINS, …); groupType only AND; dataState adds HOURLY_ALL.
- Security find: `google.auth.load_credentials_from_dict` emits a DeprecationWarning because it also loads `external_account` configs, which can make the process fetch arbitrary URLs or run executables (credential_source). Inline JSON is therefore restricted to `service_account` / `authorized_user` via their type-specific constructors; other types raise ToolError. Worth a knowledge entry: a generic credential loader is a remote-fetch/exec primitive when its input is operator-configurable.
- google-auth 2.58 ships py.typed but leaves many functions unannotated (from_*_info, refresh, exception constructors, Credentials.__init__). mypy --strict flags each as no-untyped-call. Tried `untyped_calls_exclude = ["google"]` (clean, one line) but it (a) changes the copied [tool.mypy] block (criterion 1 requires it unchanged) and (b) doesn't reach `super().__init__()`. Reverted to commented per-call ignores (3 in src, 3 in tests).
- mcp 2.x Client: `client.instructions` (not initialize_result); `Tool.input_schema` (snake_case). Tool errors are prefixed "Error executing tool <name>: ".
- Pydantic model params: alias_generator=to_camel + populate_by_name → tool schema shows the API's camelCase names; either spelling accepted.
- Added `models.py` (not in the proposal's file list) for the request models; small layout deviation, not load-bearing.
- Added one "pick the tool shape by API size" line to mcp/README.md "Adding a server" (the approach panel asked for this precedent to be recorded).
- MCP_MAX_REQUEST_BYTES default is 4 MiB (SDK default) rather than openai's 64 MiB: there are no uploads here.
- Verified: make check on 3.13 and 3.11 (uv), docker build + /healthz 200 with only MCP_AUTH_TOKEN/OPENAI_API_KEY (CI smoke env), /mcp 401 without token.

## Review triage 2026-09-25
Code review: independent fresh-context subagent on the local diff (no PR yet — local-diff mode). Minerva audit: inline.
- [FIX] (high) api.py segment(): `quote(safe="")` leaves `.`/`..` intact and httpx2 resolves dot segments — `gsc_delete_sitemap(feedpath="..")` sent DELETE on the site itself. Now "", ".", ".." are refused; tool-level tests added; deletion check confirmed 7 tests fail without the guard.
- [FIX] (medium) README / api.py docstring claimed values "cannot leave their segment" — corrected.
- [FIX] (medium) no test for bare dot segments — added (api + 4 tools).
- [FIX] (medium) models: extra fields silently dropped (e.g. `searchType`, `rowlimit`) — `extra="forbid"`, `searchType` accepted as a validation alias; tests added; README notes it.
- [FIX] (low) 2xx non-JSON body raised an opaque error — returned as `{"status", "text"}`; test added.
- [FIX] (low) httpx2 transport errors/timeouts were opaque — ToolError naming the exception; test added. (mcp/openai has the same gap; out of this diff.)
- [FIX] (low) bearer-scheme test only asserted != 401 — now a lowercase-bearer initialize must return 200.
- [IGNORE] (low) no concurrent token() test — lock is a single anyio.Lock around load+refresh; no failure scenario.
- [FIX→promote] (low, audit) proposal Approach names `google.auth.load_credentials_from_dict` and omits models.py — promote rewrites Approach to match what shipped.

## Review finding 2026-09-25
- The dot-segment escape is the 2026-08-22 denylist pattern in a new form: percent-encoding is an enumeration of *characters* to neutralise, and `.`/`..` are whole-segment values no character-level encoding touches. Candidate knowledge: a path-segment encoder must also refuse dot segments; `quote(value, safe="")` alone does not make a value "one segment". mcp/openai's check_path does reject `..` segments, so it is not affected.
