# Validate a caller URL with the parser that fetches it, or refuse what the two parsers read differently

**Date**: 2026-11-05
**Type**: pattern
**Theme**: mcp-servers
**Summary**: urlsplit silently drops tabs and newlines that httpx2 rejects; refuse non-printable URLs before checking
**Context**: .minerva/work/2026-11-05-add-microsoft-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/microsoft-ads/` fetches report files from a caller-supplied URL, checked against a host
allowlist in `safety.py` with `urllib.parse.urlsplit` and then fetched with httpx2. Code review
found that `https://ev\til.blob.core.windows.net/x` passed the check and then failed inside the
fetch as an unhandled `httpx2.InvalidURL` (not an `HTTPError` subclass), surfacing as an opaque
"Error executing tool".

## Finding
- Python's `urlsplit` follows WHATWG and **silently strips ASCII tab, CR and LF anywhere in the
  URL** (and leading/trailing spaces), so the string it validated is not the string the client
  receives.
- httpx2 instead **rejects** any non-printable ASCII character with `InvalidURL`, which does not
  derive from `httpx2.HTTPError`, so an `except httpx2.HTTPError` misses it.
- Here the mismatch failed closed (httpx2 refused the URL), but a client that also stripped the
  characters, or parsed the authority differently, could fetch a host the check never saw.

## Pattern
Before validating a caller URL, refuse anything that is not printable ASCII without spaces (or
validate with the fetching client's own URL type), and catch the client's URL-construction
error alongside its transport errors. Test the refusal with a tab inside the host.

## Related
- [[2026-09-25-pattern-a-server-local-path-argument-is-a-remote-file-primitive]] — another caller-argument boundary in the MCP servers
- [[2026-11-05-reference-microsoft-advertising-api-facts-for-mcp-servers]] — the download-URL allowlist this came from
