# ListAgents returns the whole fleet, not this project's sessions

**Date**: 2026-08-24
**Type**: reference
**Summary**: filter ListAgents on liveness, reply capability, and project-name prefix before messaging — unfiltered fan-out pings unrelated projects
**Context**: .minerva/work/2026-08-24-cross-session-preflight

## Context
Minerva's intake pre-flight asks live sibling Claude sessions whether they are already
working the same goal. The obvious implementation — enumerate peers with `ListAgents`,
`SendMessage` each one — was designed before anyone ran the enumeration.

## Finding
Measured on one developer machine, `ListAgents` returned **32 peers**:

| Kind | Count | Can it answer? |
|---|---|---|
| `interactive` (local sessions) | 5 | yes |
| Remote Control, `offline` | 18 | no — cannot process a message |
| `cloud`, `idle` | 10 | receives a message, **cannot reply** |

Unfiltered fan-out would therefore send 32 messages per intake, of which 27 could never
produce an answer, and most of the remaining 5 were on unrelated projects.

**Three filters, all derivable from what the listing already prints:**

1. **Liveness** — skip `offline` rows.
2. **Reply capability** — skip `cloud` rows; a cloud session receives but cannot message back.
3. **Project** — local interactive sessions are named `<project>-<suffix>`
   (`agent-marketplace-32`, `financials-4d`, `seekless-ce`). Match this session's own prefix.

Applied together these took **32 candidates to 0** on the authoring repo. Zero messages is
the correct common case, not a degenerate one.

## Implications
- **Run the enumeration before designing on top of it.** The design that assumed a handful
  of same-project peers was wrong by an order of magnitude and in the wrong direction.
- Rows carry **name, kind, and liveness — never intent or working directory**. Whether a
  peer overlaps can only be learned by asking it, so any "who else is working on X?" feature
  needs a message, not a smarter read of the listing.
- Cross-session replies drain at the receiver's next tool round, so **never block on one**.
  Silence means `unknown`, never `clear` — a peer may be busy, gone, or uninterested.
- Make the message self-describing. A peer may run an older plugin version, a different
  project, or no minerva at all, so any reply contract has to be stated inline in the
  message itself for the peer to be able to honour it.

## Related
- [[2026-08-24-pattern-a-lock-on-a-derived-name-does-not-cover-the-source]] — see also
