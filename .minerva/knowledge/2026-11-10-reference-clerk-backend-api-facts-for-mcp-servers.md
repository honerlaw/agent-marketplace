# Clerk Backend API facts for MCP servers: a dated spec repo, a version header, and an unscoped key

**Date**: 2026-11-10
**Type**: reference
**Theme**: mcp-servers
**Summary**: Clerk publishes dated BAPI OpenAPI files (edited after release); version by header or query, never both; secret keys are unscoped
**Context**: .minerva/work/2026-11-10-add-clerk-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/clerk/` wraps the Clerk Backend API (`https://api.clerk.com/v1`) for an MCP gateway,
because Clerk's own hosted MCP server (`mcp.clerk.com`) refused a third-party MCP portal: after
a successful OAuth sign-in its authenticated tools answered "This MCP client cannot use
authenticated Clerk tools. Authenticated access is limited to the OAuth application this server
is configured with."

## Finding
- **Spec.** `github.com/clerk/openapi-specs` (MIT) holds one `bapi/<version>.yml` per API
  version: 2021-02-05, 2024-10-01, 2025-03-12, 2025-04-10, 2025-11-10, 2026-05-12, 2026-08-20.
  `bapi/2026-08-20.yml` is OpenAPI 3.0.3, 184 paths, 264 operations (3 multipart image uploads),
  187 schemas, no external `$ref`s, no declared header parameters; 836,785 bytes of YAML, 630,282
  as compact JSON. Dated files are **edited after release** (this one last changed 2026-11-05), so
  a "pinned version" file is not pinned bytes; vendor it with its commit and hash.
- **Versions (docs).** A caller picks a version with the `Clerk-API-Version` header or the
  `__clerk_api_version` query parameter. Both together, or an invalid version, is an invalid
  request. The docs do not say what an unversioned request gets. 2026-08-20 changed only the
  Frontend API, so its Backend API equals 2026-05-12.
- **Auth.** One `bearerAuth` scheme: the instance's secret key (`sk_live_…` production,
  `sk_test_…` development). It is **not scoped**: everything the API can do on that instance,
  including minting sign-in tokens (`POST /sign_in_tokens`), impersonation (`POST /actor_tokens`),
  and GETs that return secrets (`/api_keys/{id}/secret`, `/machines/{id}/secret_key`,
  `/users/{id}/oauth_access_tokens/{provider}`). Some reads are POSTs (`verify_password`,
  `verify_totp`, `*/verify`), so "read-only = GET only" refuses them.
- **Paging.** `limit` (1–500, default 10) and `offset`; `GET /users` orders with `order_by`
  (default `-created_at`) and filters on `created_at_after`, `last_active_at_since`,
  `email_address`, `query` and more. `GET /users/count` gives a total. The only unusual path
  parameter is `/logs/{event_time_and_id}`, which holds a colon.
- **Not measured live.** No call reached Clerk while this was written; the header's acceptance
  and real response sizes were left to the first deployment.

## Implications
- Pin the version in one constant, test it against the vendored spec's `info.version`, and refuse
  the query form so the two cannot conflict.
- A Clerk server's only enforceable bound is in the server (an opt-in read-only mode) or the
  deployment; the credential bounds nothing.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the tool shape `mcp/clerk/` uses
- [[2026-10-18-reference-meta-marketing-api-facts-for-mcp-servers]] — another vendor whose hosted MCP refused the portal
