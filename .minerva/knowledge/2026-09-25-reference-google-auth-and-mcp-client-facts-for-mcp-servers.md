# google-auth typing and mcp 2.x client facts met building the Search Console server

**Date**: 2026-09-25
**Type**: reference
**Summary**: google-auth is only partly annotated under mypy --strict; mcp 2.x Client uses snake_case accessors
**Context**: .minerva/work/2026-09-25-add-google-search-console-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/google-search-console/` added google-auth 2.58 to a codebase held to `mypy --strict` and
100% branch coverage, with no network in tests.

## Finding
- **google-auth ships `py.typed` but leaves many functions unannotated**:
  `from_service_account_info`, `from_authorized_user_info`, `Credentials.refresh`, exception
  constructors such as `DefaultCredentialsError(...)`, and `Credentials.__init__`. `mypy
  --strict` reports each call as `no-untyped-call`. mypy's `untyped_calls_exclude = ["google"]`
  silences the calls but not `super().__init__()` in a `Credentials` subclass, and it changes the
  `[tool.mypy]` block that every `mcp/` server copies verbatim. The server uses a commented
  per-call `type: ignore[no-untyped-call]` instead (3 in the source, 3 in the tests).
- **Token refresh is synchronous.** It goes through `google.auth.transport.requests.Request`
  (the `google-auth[requests]` extra), so it runs in `anyio.to_thread.run_sync` under an
  `anyio.Lock`. A fake `Credentials` subclass whose `refresh` sets `token` exercises the whole
  path without network. `authorized_user` JSON loads without key material, so it is the
  cheapest real credential type to use in tests.
- **The mcp 2.x client API is snake_case**: `client.instructions` (there is no
  `initialize_result`), `Tool.input_schema`, `CallToolResult.structured_content`. A tool error
  reaches the client as `"Error executing tool <name>: <message>"`.
- **Pydantic models as tool parameters.** Use `alias_generator=to_camel` with
  `populate_by_name=True`. The tool's input schema then uses the vendor API's camelCase names
  and either spelling is accepted. Set `extra="forbid"`, or a misspelled field is silently
  dropped and the tool returns a different report than the one asked for.
- **httpx2 resolves `.` and `..` path segments client-side and keeps `%2E` and `%2F` as sent.**
  See [[2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment]].

## Implications
- A new `mcp/` server that uses google-auth should reuse `mcp/google-search-console`'s
  `credentials.py` and its test fakes, not start again from a tutorial.

## Related
- [[2026-09-25-reference-mcp-python-sdk-2x-server-facts]] — builds on
- [[2026-09-25-pattern-a-generic-credential-loader-is-a-fetch-and-exec-primitive]] — why the type-specific constructors are used
- [[2026-09-25-reference-reddit-ads-api-v3-facts-for-mcp-servers]] — see also
