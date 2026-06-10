# Scratchpad: publish-minerva-to-plugin-directories

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-10
- [skipped — small] scope check: single additive unit (evidence: committable surface is LICENSE + repo topics only; one cohesive discoverability push, no multi-subsystem decomposition)
- [skipped — small] approach selection: Approach A dominant (rejected: B — skip-verification risks dup submissions / maintainer rejection, violates verify-first; C — only top-2 channels, contradicts chosen tier-2+tier-3 scope)
- [escalated/panel] whole-proposal acceptance: round 1 → 1/3 accept (Proponent accept; Skeptic + Arbiter revise — HIGH-1 criteria didn't bind goal via user-declined auto-pass; HIGH-2 awesome-list PR diff non-executable) → revision round
- [3/3 accept] whole-proposal acceptance: round 2 (revised) — HIGH-1 fixed (artifact-production decoupled from outward send; listing-appearance excluded), HIGH-2 fixed (Phase 2 reads CONTRIBUTING, emits exact diff), MED-3/4/5 folded in; two LOW clarifications (channel inventory fixed; criterion 6 topics-out-of-band) folded into final write

## Panel decisions 2026-06-10 (cont.)
- [3/3 accept] completion verification: criteria 1-5 honestly met (LICENSE committed, topics readback-confirmed live, all 6 channels recorded, awesome-list skip = sound eligibility finding, web-form checklists produced); 6 (ship) + 7 (promote) wired downstream with inputs materialized. One MEDIUM (criterion-5 form fields blocked by HTTP 429) judged non-load-bearing — repo URL+blurb captured, send is human-in-the-loop against the live form.
- [skipped — small] review triage: no load-bearing findings (evidence: committable diff is standard MIT LICENSE text + work-unit docs only, no code; constraint 009 not triggered [no plugin added to marketplace.json], constraint 010 not triggered [no skill change]; additive single-surface, no new interface)

## Phase 1 outcome 2026-06-10
- LICENSE (MIT, Derek Honerlaw 2026) committed to branch.
- Repo topics set + readback-confirmed (all 6 accepted, none dropped): agent-skills, ai-agents, claude-code, claude-code-marketplace, claude-code-plugin, claude-plugin.

## Phase 2 per-channel discovery 2026-06-10 (criterion 3)
Verified each channel's indexing state / inclusion criteria / unit-of-submission / mechanism:

1. **claude-plugins.dev** (Kamalnrf/claude-plugins) — mechanism: AUTO-CRAWL of all public GitHub Claude Code plugins/marketplaces. Unit: both. Current: not yet confirmed listed; will be picked up automatically now that repo is public + licensed. Action: **none** (await crawl; no submit path — repo PRs are for the tool itself, not registry entries).
2. **claudemarketplaces.com** — mechanism: appears AUTO-INDEXED from GitHub (advertises ~2,500+ scraped marketplaces; only an /advertise sponsorship path, no plugin-submit form found). Unit: marketplaces + plugins. Action: **none / await crawl** (no manual submit surfaced).
3. **claudepluginhub.com** — mechanism: WEB-FORM URL submission at /tools/submit-plugin (takes a repo/marketplace URL to queue validation). Form fields not loadable (HTTP 429). Unit: plugins/marketplaces. Action: **user web-form submit** → checklist.
4. **aitmpl.com** — mechanism: curator-maintained, backed by github.com/davila7/claude-code-templates; no open submission path shown. Action: **none / curator-discretion** (optionally open an issue/PR on davila7/claude-code-templates — low priority).
5. **GiladShoham/awesome-claude-plugins** — mechanism: NOT a link-list. It is an in-repo marketplace; CONTRIBUTING requires forking and COPYING your full plugin into their `plugins/{name}/` dir (marketplace.json uses local `./plugins/...` sources only, no external GitHub refs). Unit: in-repo vendored plugins. Eligibility finding: including minerva here = vendoring its entire source into their repo = a maintenance fork. **Recommend SKIP** (inappropriate for a self-distributing plugin); surface as user decision (criterion 4).
6. **ananddtyagi/cc-marketplace** — mechanism: README routes submissions to claudecodecommands.directory/submit (external WEB-FORM), not a direct PR to this repo. Unit: commands/agents/plugins. Action: **user web-form submit** → checklist.

Net: discovery reach is mostly won by auto-crawl (1,2) now preconditions are met. Manual outward surface reduces to 2 web-form URL submissions (3, 6) + 1 recommended-skip vendor PR (5) + 1 optional curator nudge (4). All outward sends are user-confirmed per proposal.

## Submission artifacts 2026-06-10 (criteria 4, 5)
**Reusable submission blurb:**
- Name: `minerva`
- Marketplace/repo URL: `https://github.com/honerlaw/agent-marketplace`
- One-liner: "Durable record discipline for AI coding agents — a Claude Code plugin implementing a proposal → work → replan → promote → review → ship lifecycle backed by a `.minerva/` knowledge wiki."
- Install: `/plugin marketplace add honerlaw/agent-marketplace` → `/plugin install minerva@agent-marketplace`

**Submission-ready checklist (user-performed outward sends):**
- [ ] **claudepluginhub.com** — go to https://www.claudepluginhub.com/tools/submit-plugin ; paste repo URL `https://github.com/honerlaw/agent-marketplace`; fill any name/description fields with the blurb above; submit. (queues validation/indexing)
- [ ] **cc-marketplace** (ananddtyagi) — submit via https://claudecodecommands.directory/submit ; paste repo URL + blurb above. (its README's stated submission path)
- [ ] **aitmpl.com** (optional, low-priority) — no open form; optionally open an issue/PR on https://github.com/davila7/claude-code-templates referencing the repo + blurb.

**Auto-crawl channels (no action — await indexing):**
- claude-plugins.dev, claudemarketplaces.com — both index public GitHub marketplaces automatically; the new LICENSE + topics improve crawl eligibility. Re-check listings in a few days.

**Recommended SKIP (criterion 4 — eligibility finding):**
- awesome-claude-plugins (GiladShoham) — inclusion requires vendoring minerva's full source into their `plugins/` dir (a maintenance fork), not a link/external-source entry. Inappropriate for a self-distributing plugin. Recommend not pursuing.
