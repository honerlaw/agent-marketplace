# Percent-encoding does not confine a value to one path segment when the value is a dot segment

**Date**: 2026-09-25
**Type**: pattern
**Summary**: quote(value, safe="") leaves "." and ".." intact; URL resolution collapses them into another endpoint
**Context**: .minerva/work/2026-09-25-add-google-search-console-mcp-server (see git history if the worktree has been cleaned up)

## Context
The Search Console MCP server puts caller values (`site_url`, `feedpath`) into URL paths.
`quote(value, safe="")` encodes them, so `/`, `?` and `#` can't split the value and a value
like `../../x` stays in one segment. Author self-review, a 3/3 completion panel and 100%
branch coverage all passed this code. An independent code reviewer then found the hole.

## Finding
`.` and `..` consist only of unreserved characters, so percent-encoding leaves them unchanged.
httpx2 (like browsers and most HTTP clients) resolves dot segments before sending, so
`/webmasters/v3/sites/<site>/sitemaps/..` is sent as `/webmasters/v3/sites/<site>`. As a result,
`gsc_delete_sitemap(site_url=X, feedpath="..")` sent **DELETE on the property itself**, and
`feedpath="."` on submit turned into "add site". The request never left the API host, but it
reached a different, more destructive operation than the tool's name and its "confirm with the
user" guidance implied. Encoding the dots as `%2E` is not a reliable fix: WHATWG URL parsing,
and proxies that normalize, treat `%2e` as a dot segment too. The fix is to refuse `""`, `.`
and `..` outright (`api.segment`).

This is [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] in a new form. Percent-encoding
works on individual characters, but a dot segment is dangerous as a whole value, so no
character-level encoding catches it.

## Implications
- Any code that builds a URL path from untrusted values needs two steps. Encode the value, and
  also refuse the whole values `""`, `.` and `..`. A test that only uses slash-containing
  traversal (`../../x`) passes while the bare `..` case is broken. Test the bare values at the
  tool level and assert the request never went out.
- The guard's tests were checked by deletion: emptying the refused set failed 7 tests
  ([[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]]).
- `mcp/openai`'s `check_path` already rejects `..` segments, and there a `.` segment resolves
  to the same path, so it is not affected.

## Related
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — builds on
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — the independent reviewer, not self-review, found it
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — how the guard's tests were verified
- [[2026-09-25-pattern-a-server-local-path-argument-is-a-remote-file-primitive]] — a sibling hazard of caller values reaching a path
