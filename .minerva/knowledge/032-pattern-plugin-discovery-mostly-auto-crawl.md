# Claude Code plugin discoverability is mostly auto-crawl once a repo is public + licensed + topic-tagged; manual directories are web-form submissions, not source-vendor lists

**Date**: 2026-06-10
**Type**: pattern
**Context**: .minerva/work/032-publish-minerva-to-plugin-directories

## Context
minerva already shipped as a valid public Claude Code marketplace (its repo has `.claude-plugin/marketplace.json`), so it was installable by anyone with the URL but undiscoverable without it. The task was to get it onto the low-gatekeeping discovery channels — tier-2 aggregators and tier-3 "awesome" lists — excluding the official Anthropic directory. A per-channel verification pass (read each channel's README/CONTRIBUTING **before** acting) showed the channels' real mechanisms differ sharply from a naive "submit to each directory" model.

## Finding
For a public GitHub-hosted plugin/marketplace, most discovery reach is pursued **passively via auto-crawlers**, not manual submission. The load-bearing preconditions are repo **public + an OSS LICENSE + discovery GitHub topics**; once those hold, the GitHub-crawling aggregators index the repo on their own (listing *appearance* is async and not directly controllable, so judge the work by preconditions-met, not by a listing showing up).

Channels cluster into three mechanism kinds that need different — or no — action:
- **Auto-crawl (no action):** registries that crawl public GitHub for marketplaces. The only "work" is satisfying crawl eligibility (the preconditions above); there is no submit surface (such a registry's own repo PRs target the tool, not its index).
- **Web-form URL submission (human-only):** directories whose submission is a web form keyed on the repo URL. An agent can't fill the form, so the deliverable is a submission-ready checklist (exact URL + a reusable name/description blurb) for a human to paste.
- **Full-source vendor lists (avoid for self-distributing plugins):** a "list" whose `marketplace.json` uses only local `./plugins/...` sources and whose CONTRIBUTING requires copying your entire plugin into their repo. Listing a self-distributing marketplace there is a maintenance fork that desyncs on every release — record it ineligible and skip.

## Implications
- When publishing any future plugin for discovery: satisfy the passive preconditions first (public + LICENSE + topics), then scope the manual work to a short human web-form checklist — do **not** assume every "directory" takes a PR.
- Verify each channel's actual mechanism (read its README/CONTRIBUTING) before producing an artifact; the mechanism, not the channel's marketing, determines whether there's anything an agent can even do.
- Judge discovery work by the action taken (preconditions met / checklist produced / submitted), never by a public listing appearing.

## Related
- [[009-constraint-marketplace-plugin-registry-not-auto-discovered]] — see also
