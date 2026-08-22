---
name: backfill-followups
description: Migrates a project's existing `followups.md` backlog into prioritized GitHub issues, triaging each item for whether it is still relevant first. Use when a minerva project has accumulated `.minerva/work/*/followups.md` files that predate the GitHub-issue disposition, when the user asks to backfill/migrate/triage the followup backlog or wants to know which deferred items are still live, or when they invoke `minerva:backfill-followups`. A one-time migration per project — `minerva:promote` already files new TODOs as issues. Read-only through the triage gate; nothing is created until the gate is confirmed, and an item it cannot judge is filed rather than dropped.
---

Turn a `followups.md` backlog into GitHub issues, without importing the staleness that made the backlog worth migrating.

## The problem this solves

`followups.md` is write-only. Nothing in the format marks an item **done**, so a project's backlog accretes shipped, obsolete, and still-live items in one undifferentiated list, and every scoping pass re-reads all of it to re-derive which is which. `minerva:promote` fixed this going forward — kept TODOs become issues, which close. This skill fixes it backwards.

Migrating without triage would just move the staleness into the issue tracker, where it is more visible and no more true. **The relevance pass is the point of the skill**; filing is the easy half.

## Scope

- **Input.** Every `followups.md` under `.minerva/work/` (plus any worktree copies).
- **One-time per project.** After a successful run, new TODOs flow through `minerva:promote`'s disposition gate. Re-running is safe (idempotent) but should find nothing new.
- **Never deletes a `followups.md`.** Files are appended to, never rewritten — they remain the historical record of what the unit deferred and why.
- **Never invents work.** An item judged shipped or obsolete is annotated with its evidence, not filed.

## Protocol

The seven steps — discovery, item extraction with its atomization rule, the five dispositions and the fail-open `unsure` rule, the batched gate, filing, the disposition ledger, and the report — live in `references/protocol.md`. **Read it in full before running any step.**

Steps 1-4 are read-only and step 4 is a hard gate; only steps 5-6 mutate anything. That plan → confirm → apply shape is deliberate. This is one skill rather than a detector/applier pair like `minerva:lint`/`minerva:lint-fix` and `minerva:migrate`/`minerva:migrate-fix` because those are recurring health-checks a project re-runs forever, while this runs once — a detector whose only consumer is its own applier earns nothing by being split.

## Filing is delegated, not reimplemented

Issue creation follows `plugins/minerva/skills/promote/references/github-issues.md`, **verbatim** — the capability probe, the `critical`/`high`/`medium`/`low` vocabulary, label bootstrap, the duplicate check, and the per-item fail-soft to `followups.md`. **Read that file too.** Do not restate `gh` mechanics here; if the two ever disagree, `github-issues.md` wins.

There are **three** documented divergences, all in `references/protocol.md`; two are cosmetic (the back-link names this skill, and a kept `manual` item gets a line saying no code change will close it). The load-bearing one is the idempotency ledger. That file's tier-2 duplicate check reads the unit's `proposal.md` `## Deferred work` section, written by promote for the unit it is promoting. A backfill run spans many already-shipped units and does not own their proposals, so **its tier-2 ledger is the `## Backfill disposition` section** this skill appends to each `followups.md` instead. Same role, different file.

## Fail open

An item the triage cannot confidently resolve is classified `unsure` and **filed as an issue**. This direction is not arbitrary: a wrongly-filed issue costs one click to close, while a wrongly-dropped item is gone with no trace and no trigger to rediscover it. Never resolve an ambiguous item to `shipped` or `obsolete` to keep the issue count down.

## Idempotency

A disposition is **terminal** or **non-terminal**, and only terminal ones are skipped:

- **Terminal** — `→ #NN`, `shipped`, `obsolete`, `not-an-item`, or a `manual` item the
  operator dropped. The item is done being decided; a re-run passes over it.
- **Non-terminal** — `open (…) — not filed`. The item is still live and was simply not filed
  this pass — declined at the gate, or on a repo that cannot host issues at all. **A re-run re-offers it at the gate.**

That split is the whole reason a re-run is worth anything. Skipping every dispositioned line
would let an `open` item sit annotated forever with nothing to resurface it — the exact
shape `.minerva/knowledge/2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption.md`
warns about, reintroduced inside the tool built to cure it. Re-running the skill **is** the
trigger; do not let it become a no-op over live work.

Filing additionally inherits the `github-issues.md` duplicate check, so a run interrupted
between filing and recording is recovered by re-running it.
