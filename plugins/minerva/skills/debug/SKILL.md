---
name: debug
description: Investigate a bug end-to-end — gather evidence first, then diagnose root cause grounded in that evidence, and report with a mechanically-derived confidence score. Use this whenever the user reports breakage of any kind. Live-incident framing — "users are reporting", "X is broken in prod", "the cron didn't run", "500s", "timeout", "stuck", "hanging", "queue backed up", "deployment failed", "metrics dropped", or past-tense framing like "we had an outage" — all qualify. Dev-bug framing — "this test fails", "function returns wrong value", "unexpected error", "regression", "TypeError", "why is this failing" — also qualifies. Trigger this even when the user doesn't explicitly say "debug" or "triage" — any reported breakage qualifies. The skill is project-agnostic; it loads project-specific operational facts from `.minerva/reference/` at runtime and cross-references past learnings in `.minerva/knowledge/`. It stays read-only against any system other users depend on, and any mutation that would persist outside the user's own dev branch requires explicit per-turn confirmation.
---

# Debug

Investigate breakage end-to-end. Gather evidence, then diagnose. Never present a root cause without citing the evidence that supports it. Never mutate state that other users depend on without explicit per-turn confirmation.

## When this skill fires

Two surfaces, one workflow:

- **Live incidents** — something is broken in a running system. Users are affected, observability signals are abnormal, a deploy or cron failed. Past-tense incident framing belongs here too ("we had an outage", "search dropped to zero between 2 and 3am").
- **Dev bugs** — something is broken in code under development. A test fails, a function returns the wrong value, an error appears unexpectedly.

The phase boundary between them is the evidence source: logs / metrics / runtime state for live, repros / tests / local execution for dev. The workflow is the same.

## The three-phase workflow

The full investigation protocol — evidence gathering, diagnosis grounded in that evidence, and the report with its mechanically-derived confidence score — plus how to read `.minerva/knowledge/` vs `.minerva/reference/` and the reference-discovery protocol, lives verbatim in `references/workflow.md`. **Read it in full before investigating anything.**

## Mutation discipline (hard rule)

Decision rule: **would this change persist in a system other users depend on?**

**Forbidden by default** (require explicit per-turn confirmation):

- Production database writes — any DDL or DML (`UPDATE`, `DELETE`, `INSERT`, `TRUNCATE`, `ALTER`, `DROP`, `CREATE`) against any database other than your local dev one.
- Infrastructure changes — restart, redeploy, scale, rebuild, or delete any production process, container, droplet, pod, or managed service.
- Sending messages on the user's behalf — Slack, email, PR comments, customer-facing notifications.
- Secret rotation, API token regeneration, or modifying any secrets-manager state.
- Mutating CI/CD or feature-flag state.
- Pushing code, force-pushing, deploying, running migrations against prod.
- Mutation CLI subcommands — anything whose name implies state change (`requeue`, `reset`, `delete`, `restart`).

**Always fine**:

- Read-only operations everywhere — `SELECT`, `list`, `get`, `describe`, tailing logs, querying metrics.
- Editing your own dev branch.
- Running tests locally.
- Adding temporary logging or assertions in dev to confirm a hypothesis.
- Writing repro scripts that operate on your local environment.
- Reading any code.
- Calling read-only MCP tools.

**The past-tense test**: if you'd describe the operation in past tense after running it ("I deleted the row...", "I restarted the worker...", "I posted a comment..."), it needs explicit confirmation in the same turn. If you'd describe it as evidence ("I saw...", "I found...", "I queried and got..."), it's fine.

When in doubt, prefer the read-only variant or ask the user before acting.

## When the user just wants context, not a fix

If the user is asking "why does X exist" or "how does Y work" rather than reporting a bug, the skill is still useful as a navigation aid: `ls .minerva/reference/`, load the relevant files, summarize, and stop. Don't fabricate a problem to debug.

## Knowledge-base authority

When `.minerva/knowledge/` or `.minerva/reference/` says something different from what this skill body says about the project, **trust the project files**. They're written for this project specifically; this skill body is project-agnostic and may be wrong about specifics. Flag the drift to the user if it matters.
