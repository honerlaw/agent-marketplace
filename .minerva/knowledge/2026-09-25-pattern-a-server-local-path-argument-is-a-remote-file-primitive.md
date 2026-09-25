# A server-local path argument on an MCP tool is a file read/write primitive for remote callers

**Date**: 2026-09-25
**Type**: pattern
**Summary**: Tool args naming server-local paths are safe over stdio, arbitrary file read/write over HTTP
**Context**: .minerva/work/2026-09-25-add-openai-mcp-server (see git history if the worktree has been cleaned up)

## Context
The OpenAI MCP server accepted `local_path` (upload a file from disk) and `save_to` (write a
download to disk). This was designed for stdio, where the server runs as the user on the user's
machine. The same tools were also served over HTTP from a container. Proposal review, three panels
and the completion panel all accepted the design with the caveat "local paths are server-local".
Only the independent code review found what that means over a remote transport.

## Finding
Over HTTP, the path arguments give any authenticated caller, or a prompt-injected model, arbitrary
file read and write on the server host. For example, upload `/proc/self/environ` to the API and
download it back to read the server's own secrets. Or download attacker-supplied bytes into
`~/.ssh/authorized_keys`, where `mkdir(parents=True)` helpfully creates the directory. The fix
gates both arguments on the transport: allowed over stdio, refused over HTTP, through one guard in
`safety.py`. The review caught it because it tried to *use* the feature hostilely. The design
reviews only judged whether the feature was *described* correctly.

## Implications
- A tool argument that names a filesystem path belongs to the security boundary, not the
  convenience layer. Decide its policy per transport when it is introduced.
- The same tool code serving several transports inherits the least-trusted transport's threat
  model. Documenting a limitation ("remote clients should send base64") is not a control.
- Ask review agents to break a feature, not just to confirm it matches its description.

## Related
- [[2026-09-25-decision-mcp-servers-expose-generic-spec-driven-tools]] — the tool surface this guards
- [[2026-08-22-pattern-a-denylist-safety-guard-fails-open]] — the path validator is an allowlist of shape, not a denylist of hosts
- [[2026-09-25-pattern-a-generic-credential-loader-is-a-fetch-and-exec-primitive]] — see also
- [[2026-09-25-pattern-percent-encoding-does-not-confine-a-dot-segment]] — see also
