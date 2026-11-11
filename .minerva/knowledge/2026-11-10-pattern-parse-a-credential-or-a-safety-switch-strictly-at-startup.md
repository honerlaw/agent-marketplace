# Parse a credential or a safety switch strictly at startup, or a typo quietly disables the protection

**Date**: 2026-11-10
**Type**: pattern
**Theme**: mcp-servers
**Summary**: a key with a trailing newline escaped the literal scrubber via h11's bytes repr; a lenient `_flag` read `on` as off
**Context**: .minerva/work/2026-11-10-add-clerk-mcp-server (see git history if the worktree has been cleaned up)

## Context
`mcp/clerk/` scrubs its secret key from every result and offers an opt-in `CLERK_READ_ONLY`.
Both were built, tested to 100% branch coverage, and passed a Verifier. An independent code
reviewer then reproduced two ways a plausible operator mistake turned them off.

## Finding
- **A credential with a trailing `\n`, `\r\n` or NUL leaked in full.** The config check was
  `startswith("sk_")`, so `"sk_live_…\n"` (a key piped into a secret store, or a CRLF `.env`) was
  accepted. h11 then rejects the header and httpx2 raises
  `LocalProtocolError("Illegal header value b'Bearer sk_live_…\\n'")`. In that bytes repr the
  newline is the two characters `\` `n`, so the scrubber's literal (with a real newline) never
  matches, and the whole key reaches the model and the client's logs. `httpx2.MockTransport`
  skips h11, so the existing scrub tests could not see it.
- **A lenient switch fails open.** The shared `_flag` idiom (`value.lower() in {"1","true","yes"}`)
  reads `on`, `enabled`, `y` or `true\n` as false. For a switch that turns a protection *on*, that
  silently means unprotected. `mcp/google-search-console/`'s `GSC_READ_ONLY` uses that idiom
  today: `GSC_READ_ONLY=on` runs read-write. It was left as it is because fixing it changes that
  server's env contract (values it accepts now would stop startup).

## Implications
- Strip a credential, then require its documented shape with an allowlist pattern (here
  `sk_(live|test)_[A-Za-z0-9]+`), and refuse anything else without echoing it. Then the bytes
  sent equal the literal the scrubber looks for.
- Parse switches against both a true set and a false set, and refuse anything else at startup.
- Keep credentials out of `repr`: `field(repr=False)` on the settings dataclass.
- A deletion check of each guard (remove it, watch a test fail) proves the tests bite; it does
  not prove the inputs reaching the guard are the ones an operator will give.

## Related
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — the same direction of failure, in config
- [[2026-11-05-pattern-validate-a-url-with-the-parser-that-fetches-it]] — the same root: the checker and the sender read bytes differently
- [[2026-11-10-reference-clerk-backend-api-facts-for-mcp-servers]] — the server where it was found
