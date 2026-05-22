---
name: triage
description: Investigate a bug end-to-end — first locate the failing component (in a live system or in dev code), then trace through the code to root-cause and recommend a fix. Use this whenever the user reports breakage of any kind. Live-incident framing — "users are reporting", "X is broken in prod", "the cron didn't run", "500s", "timeout", "stuck", "hanging", "queue backed up", "deployment failed", "metrics dropped", or past-tense framing like "we had an outage" — all qualify. Dev-bug framing — "this test fails", "function returns wrong value", "unexpected error", "regression", "TypeError", "why is this failing" — also qualifies. The skill is project-agnostic; it loads project-specific operational facts from `.minerva/reference/` at runtime and cross-references past learnings in `.minerva/knowledge/`. It stays read-only against any system other users depend on, and any mutation that would persist outside the user's own dev branch requires explicit per-turn confirmation. Trigger this even when the user doesn't explicitly say "debug" or "triage" — any reported breakage qualifies.
---

# Triage

Investigate breakage end-to-end. Locate where it's broken, then trace through the code to figure out why. Never mutate state that other users depend on without explicit per-turn confirmation.

## When this skill fires

Two surfaces, one workflow:

- **Live incidents** — something is broken in a running system. Users are affected, observability signals are abnormal, a deploy or cron failed. Past-tense incident framing belongs here too ("we had an outage", "search dropped to zero between 2 and 3am").
- **Dev bugs** — something is broken in code under development. A test fails, a function returns the wrong value, an error appears unexpectedly.

The phase boundary between them is the evidence source: logs / metrics / runtime state for live, repros / tests / local execution for dev. The workflow is the same.

## The two-phase workflow

### Phase 1 — Locate

Find the failing component before you try to fix anything. Skipping straight to a hypothesis without grounding it in evidence is the most common way triage goes off the rails.

1. **Restate the symptom in one sentence.** "Search returns 500s for queries containing accents." Not "search is broken." The restatement forces you to name what's actually observed.

2. **Identify the candidate failing layer.** Which subsystem owns the symptom? Which call site does the evidence point at? If you're not sure, plan to pull evidence from multiple plausible layers and let the data pick.

3. **Load relevant project references.** Use the discovery mechanism below to read `.minerva/reference/` files that describe how the failing layer works in this project. Also skim `.minerva/knowledge/` for past learnings — decisions, bugs, patterns, constraints — that match the symptom.

4. **Pull evidence.**
   - *Live incidents*: logs, metrics, dashboard panels, runtime state via read-only CLI access, read-only queries against operational stores.
   - *Dev bugs*: reproduce locally, read the failing test or call site, add temporary logging if needed, narrow with a targeted assertion.

5. **Always check the pattern catalog.** If `.minerva/reference/` contains a `bug-patterns.md`, `incidents.md`, or similarly-named pattern catalog, load it on every triage regardless of symptom — it's a cheap "have we seen this" check. If the symptom matches an entry, name the pattern explicitly in your report.

Phase 1 ends when you can confidently answer "which code is failing." If the failure turns out to be operational, not a code bug — wrong env var, missing secret, exhausted quota, stale deploy, unhealthy droplet — skip Phase 2 and report what you found.

### Phase 2 — Root-cause

Given a located failing component, figure out why it's failing.

1. **Read the call sites the evidence references.** Logs name file paths and line numbers. Stack traces name functions. Open them. Walk inward from the entry point until you find the offending code.

2. **Form a hypothesis.** State what you think is causing the failure and how the code would have to behave for that to be true.

3. **Confirm.** Either by reading more code (does the suspected path actually execute under these conditions?), by writing a focused repro (does the buggy behavior reproduce against this minimal input?), or by adding a temporary assertion / log line (does runtime match the hypothesis?).

4. **Identify the offending lines.** Be specific: file + line range + what the code does + what it should do.

## Reading the project: knowledge vs. reference

The `.minerva/` directory has two read tiers, and this skill uses both differently:

- **`.minerva/knowledge/`** — atomic, past-tense, durable learnings. Files named `NNN-<type>-<slug>.md` where type is `decision`, `bug`, `constraint`, or `pattern`. Append-only. This is "what we learned" about this project, one concept per file. Triage uses it for "have we seen this symptom before?" pattern matching, and for understanding load-bearing constraints that might explain the failure.

- **`.minerva/reference/`** — thematic, present-tense, operational facts about how the system is configured *right now*. Files named by topic (`topology.md`, `observability.md`, `database.md`, etc.). Replace-on-change. Triage uses it for "how does this layer work in this project?" — the operational map.

The distinction is time-shape: knowledge accumulates; reference snapshots. New durable learnings from a triage go to knowledge via `minerva:promote`. Updates to operational facts overwrite the relevant reference file directly.

## `.minerva/reference/` discovery

The skill cannot bake in project-specific filenames, so reference loading is dynamic:

1. **List first.** `ls .minerva/reference/` to see what exists in this project. Don't read everything blindly.
2. **Symptom-driven selection.** Pick 1-3 files for full read based on filenames + the one-sentence symptom restatement. Filenames are descriptive by convention (`topology.md` for system layout, `observability.md` for logging/metrics conventions, `database.md` for schema and read-only query recipes, etc.) — filename + symptom is enough to pick relevance without reading contents first.
3. **Always load the pattern catalog.** Files matching `bug-patterns.md`, `incidents.md`, `patterns.md`, or similar pattern-catalog names get loaded on every triage regardless of symptom-based selection.

If `.minerva/reference/` doesn't exist or is empty, fall back to reading the codebase directly — the workflow still applies, you just have less project-specific context to lean on.

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

**The past-tense test**: if you'd describe the operation in past tense after running it ("I deleted the row…", "I restarted the worker…", "I posted a comment…"), it needs explicit confirmation in the same turn. If you'd describe it as evidence ("I saw…", "I found…", "I queried and got…"), it's fine.

When in doubt, prefer the read-only variant or ask the user before acting.

## Report format

Structure the final reply as:

1. **Symptom** — one-sentence restatement of what's wrong.
2. **Evidence** — quoted log lines, query results, runtime state, repro output. Include the exact queries and commands you ran so the user can re-run them.
3. **Root cause** — what the evidence points to, mapped to a known pattern from `.minerva/reference/bug-patterns.md` or `.minerva/knowledge/` when applicable. Identify offending file + line range if the bug is in code.
4. **Recommended fix** — what the user should do. Mutating actions go here as suggestions, not as taken actions.
5. **What I did not check** — plausible causes you actively ruled out vs. ones you ran out of time to inspect. Avoid false confidence.

## When the user just wants context, not a fix

If the user is asking "why does X exist" or "how does Y work" rather than reporting a bug, the skill is still useful as a navigation aid: `ls .minerva/reference/`, load the relevant files, summarize, and stop. Don't fabricate a problem to debug.

## Knowledge-base authority

When `.minerva/knowledge/` or `.minerva/reference/` says something different from what this skill body says about the project, **trust the project files**. They're written for this project specifically; this skill body is project-agnostic and may be wrong about specifics. Flag the drift to the user if it matters.
