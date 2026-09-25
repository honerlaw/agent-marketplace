# A mock transport that never yields cannot test a lock

**Date**: 2026-09-25
**Type**: pattern
**Summary**: Concurrency test passed with the lock removed; synchronous mock handlers never let callers overlap
**Context**: .minerva/work/2026-09-25-add-reddit-ads-mcp-server (see git history if the worktree has been cleaned up)

## Context
The Reddit Ads MCP server's token manager guards refreshes with an `anyio.Lock`, so ten
concurrent tool calls share one token refresh. After code review, a test was added that starts
ten `get()` calls in a task group and asserts one token request. The fake Reddit was
`httpx2.MockTransport` with a plain synchronous handler.

## Finding
The test passed, and it **still passed with the lock replaced by a no-op**. A synchronous
`MockTransport` handler returns without reaching an await checkpoint. So the first caller's
refresh finishes before the second caller runs, and the calls are serialized by accident rather
than by the lock. Making the handler `async` with an `await anyio.sleep(0.01)` let every caller
reach the lock while one refresh was in flight. After that, removing the lock failed the test and
restoring it passed.

## Implications
- A test of a lock, a semaphore or any "only one in flight" guard needs a fake that yields
  inside the guarded section. Otherwise the scheduler, not the guard, produces the result.
- Check such a test by deleting the guard. Coverage cannot catch this, because the code under
  test ran every line either way.

## Related
- [[2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail]] — builds on
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — see also
