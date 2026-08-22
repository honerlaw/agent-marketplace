# Followups: publish-minerva-to-plugin-directories

Pending **user-performed** outward submissions (web forms an agent can't fill).
Reusable blurb to paste:

- Name: `minerva`
- Marketplace/repo URL: `https://github.com/honerlaw/agent-marketplace`
- One-liner: "Durable record discipline for AI coding agents — a Claude Code plugin implementing a proposal → work → replan → promote → review → ship lifecycle backed by a `.minerva/` knowledge wiki."
- Install: `/plugin marketplace add honerlaw/agent-marketplace` → `/plugin install minerva@agent-marketplace`

## Submit (web forms)
- [ ] **claudepluginhub.com** — https://www.claudepluginhub.com/tools/submit-plugin — paste the repo URL; fill name/description from the blurb. (queues validation/indexing)
- [ ] **cc-marketplace** (ananddtyagi) — https://claudecodecommands.directory/submit — paste repo URL + blurb. (its README's stated submission path)
- [ ] **aitmpl.com** (optional, low priority) — no open form; optionally open an issue/PR on https://github.com/davila7/claude-code-templates referencing the repo + blurb.

## Await (auto-crawl — no action; re-check in a few days)
- [ ] **claude-plugins.dev** — should index automatically now the repo is public + licensed + topic-tagged. Re-check the listing.
- [ ] **claudemarketplaces.com** — same; auto-indexes public GitHub marketplaces. Re-check the listing.

## Decided: skip
- **awesome-claude-plugins** (GiladShoham) — inclusion requires vendoring minerva's full source into their `plugins/` dir (a maintenance fork). Not pursued; see [[2026-06-10-pattern-plugin-discovery-mostly-auto-crawl]].

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- - Name: `minerva` / Repo URL / One-liner / Install (4 bullets) → not-an-item — a reusable paste-blurb for a human doing the submissions, not a task. Carried into #82-#84 so it is where it is needed
- **claudepluginhub.com** → → #82 (priority: medium, manual)
- **cc-marketplace** (ananddtyagi) → → #83 (priority: medium, manual)
- **aitmpl.com** (optional, low priority) → → #84 (priority: low, manual)
- **claude-plugins.dev** (Await — auto-crawl) → not-an-item — explicitly 'no action; re-check in a few days'; a reminder, not a task
- **claudemarketplaces.com** (Await — auto-crawl) → not-an-item — same
- **awesome-claude-plugins** (Decided: skip) → not-an-item — the author already closed it
