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
