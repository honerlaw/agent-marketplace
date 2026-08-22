# using-minerva — deeper guidance

## The persistence hierarchy (quick reference)

| Tier | Files | Read by Claude |
|---|---|---|
| Always-read | `CLAUDE.md` / `AGENTS.md`, `.minerva/knowledge/` (start from `index.md`, the catalog) | Every conversation in this project — decisions, bugs, patterns |
| Reference (read on demand) | `.minerva/reference/<topic>.md` | Present-tense operational docs — architecture, glossary, conventions: how the system works now |
| Searchable-on-demand | `.minerva/work/<date-slug>/proposal.md`, `.minerva/work/<date-slug>/replan.md`, `followups.md` if present, plus open `minerva:followup` GitHub issues | Grep the files; `gh issue list --label "minerva:followup" --state open` for the rest |
| Ephemeral | `.minerva/work/<date-slug>/scratchpad.md` | Live during `minerva:work`, archived by `minerva:promote` |

The two LLM-owned wiki tiers differ in **time-shape**: `.minerva/knowledge/` is atomic, past-tense, append-only "what we learned"; `.minerva/reference/` is thematic, present-tense, replace-on-change "how the system works now."

**The knowledge wiki is navigable, not a flat pile.** `.minerva/knowledge/index.md` is the maintained catalog — one line per entry (link + one-line summary), grouped by type. Entries cross-reference each other in a trailing `## Related` block using `[[YYYY-MM-DD-type-slug]]` wiki-links keyed on the full stem, with a closed relationship vocabulary (`builds on` / `supersedes` / `superseded by` / `contradicts` / `see also`); superseded entries keep a `<!-- superseded-by: <stem> -->` banner rather than being deleted. `minerva:promote` maintains the index and these cross-references (including the reciprocal links on neighbor entries) through its existing confirmation gate. Inline `[[…]]` mentions in entry prose remain valid and are not migrated — the `## Related` block is the structured, machine-maintained surface; inline mentions are free prose.

When in doubt about whether something belongs in a knowledge file vs. a scratchpad note, apply the new-engineer-in-a-year heuristic: would a new engineer or agent joining in a year benefit from reading it?

## Common scenarios

**"This is a fresh project — let's start using minerva."**
→ `minerva:init`. Scaffolds `.minerva/work/` and `.minerva/knowledge/`, checks `.gitignore`, warns about any legacy `.minerva/decisions/`, adds a Routing section to the agent file, and offers to commit.

**"I'm toying with the idea of payments, but I'm not sure it's worth it or what it'd look like."**
→ `minerva:explore`. Divergent, commitment-free brainstorming: it asks questions one at a time, weighs a few high-level directions, and writes nothing — no proposal, no work unit, no branch/worktree. It may legitimately end in "let's not", a reframed problem, or a chosen direction. If you converge on something, it hands off to `minerva:propose` (passing the direction inline) to design it. Reach for `minerva:propose` directly when you already know what you want to build.

**"Let's add a payments flow."**
→ `minerva:propose "add payments flow"` (or just `minerva:propose` — the skill infers your intent from context). Brainstorm the design through the skill's flow. After you approve every section, propose creates the `2026-08-09-add-payments` branch and worktree at `.minerva/worktrees/2026-08-09-add-payments/`, enters the worktree, writes `proposal.md` + `scratchpad.md` inside it, and commits the initial docs. Don't start coding until the proposal is written, self-reviewed, and you've approved the file directly.

**"Where were we on the payments thing?"**
→ `minerva:work` (or `minerva:work 005-add-payments` to be explicit). The skill enters the existing worktree at `.minerva/worktrees/005-add-payments/`, reads `proposal.md`, the latest `replan.md`, surfaces any unresolved Open Questions, and skims `scratchpad.md` to figure out where to pick up.

**"It turns out we can't use Stripe's hosted checkout — we need our own form."**
→ Load-bearing divergence. Inside `minerva:work`, the protocol auto-triggers `minerva:replan`. Outside `minerva:work` (coming back from a tangent), invoke `minerva:replan` directly.

**"I want to tweak the proposal before we start."**
→ `minerva:replan` works here too — it's the same divergence flow, framed for a pre-work tweak. The replan entry's "What changed" is "user requested adjustment before implementation."

**"We just decided the queue retry policy should be exponential backoff capped at 5 minutes."**
→ Mid-work durable decision. Run `minerva:promote "exponential backoff capped at 5 minutes for queue retries"`. The scratchpad entry gets marked so the end-of-work pass doesn't re-promote it.

**"Before I open the PR, let's check the code actually matches what we designed."**
→ `minerva:review`. The skill reads the proposal + replans, audits the branch-vs-default diff (or the uncommitted diff if the tree is dirty), runs `code-review:code-review` (or a structured inline check if no PR exists yet), and walks you through each finding. Triage state is persisted to scratchpad so re-runs pre-fill prior dispositions. Run review **before** promote so review-derived notes flow through promote's partition.

**"Tests pass, the feature works, success criteria are met."**
→ `minerva:promote` (no argument). Partitions the scratchpad into promote / merge / discard / TODO. TODOs aren't silently dropped — you decide per-item whether to keep them (filed as a GitHub issue at a `critical`/`high`/`medium`/`low` priority when the repo can host one, otherwise appended to `followups.md`), seed a new proposal, or discard.

**Adopting the issue workflow on a project with an existing backlog?**
→ `minerva:backfill-followups`. A one-time pass that triages every `.minerva/work/*/followups.md` item as open / manual / shipped / obsolete with cited evidence, files the survivors as prioritized issues behind a batched gate, and appends a `## Backfill disposition` section to each file. Items it cannot judge are filed, not dropped.


**"OK, ship it — commit, PR, watch CI, and merge if it goes green."**
→ `minerva:ship`. Commits outstanding changes (creating a branch if you're on the default), opens a PR titled and described from `proposal.md`, watches CI without blocking (a detached `gh pr checks --watch` resumes the run when checks settle, with a long re-arming `ScheduleWakeup` armed underneath), runs a bounded auto-fix loop on CI failures, and enables auto-merge when permissions allow.

**"PR is merged — let's clean up."**
→ `minerva:cleanup`. Removes worktrees whose branches have been merged into the default branch, and prunes the local branches. Idempotent and conservative — never touches unmerged work without explicit override.

## Working in a minerva project without invoking skills

Even when you don't run a `minerva:` skill this session, respect the hierarchy:

- Treat `CLAUDE.md` / `AGENTS.md` and `.minerva/knowledge/` as authoritative — read them when starting work in the project. These contain decisions, fixed bugs, and discovered patterns, not just architecture.
- Grep `.minerva/work/` when you need historical context for a feature. Active work lives at `.minerva/worktrees/<date-slug>/.minerva/work/<date-slug>/`; shipped work lives at `.minerva/work/<date-slug>/` on the default branch.
- Don't create `scratchpad.md` files directly outside of `minerva:work`. If you need scratch space, use a TodoWrite or notes in conversation instead.
- If a project has a leftover `.minerva/decisions/` directory, that's the legacy location — `minerva:init` will report it; either migrate to `.minerva/knowledge/` or treat both as authoritative until you do.
