# A generic credential loader fed operator config is a remote-fetch and exec primitive

**Date**: 2026-09-25
**Type**: pattern
**Summary**: google-auth's generic loaders accept external_account configs that fetch URLs or run executables; accept only the expected types
**Context**: .minerva/work/2026-09-25-add-google-search-console-mcp-server (see git history if the worktree has been cleaned up)

## Context
The Search Console MCP server accepts Google credentials as inline JSON (`GSC_CREDENTIALS_JSON`).
The first implementation passed that JSON to `google.auth.load_credentials_from_dict`. In
google-auth 2.58 that call emits a DeprecationWarning explaining the risk.

## Finding
google-auth's generic loaders (`load_credentials_from_dict`, `load_credentials_from_file`) accept
every credential type, including `external_account`. Such a config's `credential_source` can
name a URL to fetch a token from, or an executable to run. Anyone who can set the credential
JSON can therefore make the server send requests to arbitrary URLs, or run programs where the
executable source is enabled. The server now calls the type-specific constructors
(`service_account.Credentials.from_service_account_info`,
`google.oauth2.credentials.Credentials.from_authorized_user_info`) and refuses every other
`type` with a clear error. Application Default Credentials (`google.auth.default`) are still
used when no inline JSON is set. ADC config comes from the environment, which the operator
controls directly.

## Implications
- When a server takes credentials as configuration, accept an explicit list of credential types
  and call each type's own constructor. Don't use a loader that dispatches on a `type` field in
  the input.
- A library DeprecationWarning that names "untrusted source" is a security finding, not noise.
  Read it before silencing it.

## Related
- [[2026-09-25-pattern-a-server-local-path-argument-is-a-remote-file-primitive]] — same shape: a configuration or tool argument that turns into file or network access
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — accepting only the expected types is the allowlist direction
- [[2026-09-25-reference-google-auth-and-mcp-client-facts-for-mcp-servers]] — see also
