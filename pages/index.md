# minerva

**Durable record discipline for software work done with agents.**
Artifacts get *promoted, not just accumulated* — decisions become files a future agent reads, proposals are rewritten to match what actually shipped, and everything else is archived out of the way.

minerva is a [Claude Code](https://github.com/honerlaw/agent-marketplace) plugin.

---

## I. The problems it solves

Agent-assisted work has a memory problem, and it isn't the agent's context window. It is that nothing the agent learns survives in a form the *next* session can trust.

**1. Context dies with the session**

The reasoning behind a design — what was tried, what was rejected, why — lives in a chat transcript nobody rereads. The next session starts from zero and re-derives (or contradicts) it.

**2. Knowledge lives only in chat**

Hard-won facts — "the gitignore entry must land *before* `git worktree add`", "this registry is not auto-discovered" — are learned, used once, and lost. minerva promotes them to `.minerva/knowledge/`, a cross-referenced wiki with an index, an advisory overview, and CI-gated link integrity.

**3. Plans drift silently from reality**

The proposal says one thing; the code does another; nobody updated the document. minerva treats load-bearing divergence as an event — a dated replan entry — and rewrites the proposal at the end to describe what actually shipped.

**4. AI judgment goes unaudited**

"Looks done to me" is an easy sentence for a model to produce. minerva routes the load-bearing calls — is this done? is this finding real? is this knowledge durable? — through adversarial review, with the votes logged where a later audit can read them.

---

## II. The record it keeps

Everything minerva writes lands in a small hierarchy under `.minerva/`, ordered by how long it deserves to live:

| Tier | Contents |
|---|---|
| `knowledge/` | Atomic, past-tense entries — decisions, bugs, patterns, constraints — cross-referenced like a wiki and read at the start of every new piece of work. Append-only by construction; corrections arrive as new entries. |
| `reference/` | Present-tense operational docs: how the system works *now*. Replaced on change, read on demand. |
| `work/` | One numbered directory per unit of work: the proposal, any replans, followups — the reasoning a future engineer can grep. |
| scratchpad | Ephemeral working memory, kept honest by being disposable: at the end of a unit, the durable parts are promoted and the rest is archived. |

---

## III. The flow

The lifecycle is a rail with stations. You can board anywhere, but each skill assumes the record its predecessors leave behind.

1. **explore** — diverge on the problem; commitment-free, writes nothing, may end in "don't build this"
2. **propose** — converge on a design; branch, worktree, and a proposal stress-tested by *grill-plan* before approval
3. **work** — implement against the proposal, scratchpad live; *replan* fires when reality drifts in a load-bearing way
4. **review** — audit the diff against the spec and the knowledge wiki, then triage findings
5. **promote** — partition the scratchpad; durable knowledge up, proposal rewritten to match reality, the rest archived
6. **synthesize** — refresh the wiki's theme-grouped overview when enough new scope accumulated; self-gating
7. **ship** — commit, open the PR, watch CI by polling, bounded auto-fix, auto-merge where permitted
8. **cleanup** — after merge: remove the worktree, prune the branch

Two orchestrators run the whole rail end-to-end: `minerva:propose-ship` with human gates at every strategic decision, and `minerva:propose-ship-auto` with those gates replaced by three-agent consensus panels. The remaining skills are utilities you reach for out of band — debugging, wiki hygiene, migration, orientation.

---

## IV. The skills

Each entry below is excerpted from the skill's own `description:` frontmatter — the same source of truth the runtime discovers skills from. Presence of every skill on this page is enforced by a test; the prose is a point-in-time excerpt.

<!-- skills-catalog: source of truth is each skill's SKILL.md description frontmatter; when adding a skill, add an entry here — tests/test_site_catalog.py enforces presence -->

### The lifecycle

**`minerva:explore`**
: A divergent, commitment-free dialogue that writes no file, allocates no work unit, and creates no branch or worktree. Asks questions one at a time; may legitimately end in "don't build this" or "reframe the problem". When a direction is chosen, hands off to `minerva:propose` to design it.

**`minerva:propose`**
: Runs a brainstorm-style intake flow, asks clarifying questions one at a time, proposes 2–3 approaches, drafts the design and stress-tests it via `minerva:grill-plan` before approval, creates the work unit's branch and worktree, and writes the approved design to `.minerva/work/NNN-<slug>/proposal.md`.

**`minerva:grill-plan`**
: Interviews the user relentlessly about a drafted plan, one question at a time, with the LLM's recommended answer leading each question, until shared understanding is reached.

**`minerva:work`**
: Reads the proposal and any replans, maintains a live scratchpad, and auto-invokes the `minerva:replan` protocol when reality drifts in a load-bearing way. Checks Success criteria before signaling completion.

**`minerva:replan`**
: For when work has diverged from the proposal in a load-bearing way — a core assumption was wrong, the approach is changing, or scope is shifting. Drafts the new plan, stress-tests it, then appends a dated divergence entry to `replan.md`.

**`minerva:review`**
: Runs a spec/knowledge audit alongside a code quality review, presenting both result sets in parallel before unified triage. Delegates to a PR code review when one exists; triage state is persisted to the scratchpad so re-runs pre-fill prior dispositions.

**`minerva:promote`**
: Promotes durable knowledge to `.minerva/knowledge/`, rewrites `proposal.md` to match reality, and archives the scratchpad. Forward-looking TODOs aren't silently discarded. Idempotent.

**`minerva:synthesize`**
: Reports the deterministic un-synthesized-scope signal, then drafts the theme-grouped `overview.md` and — behind a confirmation gate — writes it and bumps the synthesis watermark. The overview is advisory; only the mechanical link-rot signal is deterministic.

**`minerva:ship`**
: Commits outstanding changes to a branch, opens a pull request, watches CI, fixes CI failures, and enables auto-merge. CI is watched by polling instead of blocking. Closes the lifecycle after work, promote, and review.

**`minerva:cleanup`**
: Removes worktrees whose branches have been merged into the default branch, and prunes the corresponding local branches. Idempotent. Never touches the default branch or unmerged work.

### The orchestrators

**`minerva:propose-ship`**
: Orchestrates propose → work → review → promote → ship → cleanup by delegating to each skill in sequence with no logic duplication. Refuses to start if in-flight work exists for the same intent; waits for the PR to actually merge before invoking cleanup.

**`minerva:propose-ship-auto`**
: The same lifecycle, but replaces each human-facing decision with a 3-agent Proponent/Skeptic/Arbiter consensus panel (the panel mechanics are delegated to `minerva:round-table`). Human input is only a fallback when the panel can't agree after one revision round; small, low-risk decisions skip the panel via a fail-closed skip predicate.

**`minerva:propose-ship-quick`**
: The lightweight fast-path sibling — the same lifecycle with no scheduled human gates, but the main model adjudicates every decision directly instead of convening a panel. Built for small, low-risk changes (small UI fixes, bug fixes) you want done quickly. A fail-closed escalation predicate sends genuinely-undecidable decisions to the user, and a scope-fit escape recommends `propose-ship-auto`/`propose-ship` if the change turns out not to be small.

### The utilities

**`minerva:round-table`**
: Dispatches a 3-agent Proponent/Skeptic/Arbiter panel of fresh-context subagents over a decision or drafted artifact, counts accept votes against a caller-specified quorum (default 2/3), runs at most one revision round, and escalates to the user when consensus fails twice. Usable standalone for any decision.

**`minerva:debug`**
: Investigates a bug end-to-end — gathers evidence first, then diagnoses root cause grounded in that evidence, and reports with a mechanically-derived confidence score. Stays read-only against any system other users depend on.

**`minerva:lint`**
: Read-only health-check of the knowledge wiki: a deterministic detector for mechanical defects (index drift, broken links, missing reciprocals) plus LLM-judged advisory findings (orphans, contradictions, stale claims). It never edits files; it reports.

**`minerva:lint-fix`**
: The mutating companion to `minerva:lint` — behind a confirmation gate, applies the deterministically-repairable findings via a tested script. It does not touch entry bodies, and it does not auto-fix judgment calls.

**`minerva:migrate`**
: Read-only migration check for a pre-conventions knowledge corpus — inventories the non-conforming files invisible to the wiki tooling and emits a checklist naming the existing skills that close each gap.

**`minerva:init`**
: One-time scaffolding of the `.minerva/` directory layout. Idempotent — re-runs report per-piece status without rewriting anything in place.

**`minerva:using-minerva`**
: Context-aware orientation — explains when to invoke each minerva skill and gives common scenarios.

<!-- end skills-catalog -->

---

## V. The bias built in

minerva is opinionated, and the opinions are load-bearing. Each entry below names where the bias is enforced, so you can read the enforcing text yourself.

**Fail closed** — When it is unclear whether a decision is small enough to skip review, it is not. The auto orchestrator's skip predicate is conjunctive — every clause must hold, and any uncertainty convenes the full panel.
*source: `minerva:propose-ship-auto` · knowledge 014 (per-decision skip over sizing gate)*

**Adversarial by default** — Artifacts earn acceptance by surviving an argument: a Proponent defends, a Skeptic attacks, an Arbiter weighs — and at the strictest decision tier, where unanimity is required, a lone Skeptic dissent blocks outright.
*source: `minerva:round-table` · knowledge 033 (panel mechanics extraction)*

**Interrogate the plan** — Plans are not approved on vibes. A drafted design is questioned one question at a time, recommended answer first, until shared understanding — not until the user gets tired.
*source: `minerva:grill-plan`*

**Gates before mutation** — Anything that rewrites the durable record asks first. The wiki fixer, the synthesis layer, and promotion all sit behind explicit confirmation gates; every mutating path has a read-only companion or a gate that shows its hand before writing.
*source: `minerva:lint-fix`, `minerva:synthesize`, `minerva:promote`*

**Observable over self-judged** — Skills hand off on signals that can be checked — an inline argument was passed, a file exists — never on a model's own claim that "the prior phase converged". Self-assessment is treated as gameable; actions are not.
*source: knowledge 031 (observable intake) · knowledge 014*

**Durable over ephemeral** — The chat is not the record. Decisions worth keeping are promoted into files a future agent reads; the scratchpad that produced them is archived, unsentimentally.
*source: `minerva:promote` · the `.minerva/knowledge/` tier*

**Append, never overwrite** — Knowledge entry bodies are byte-identity-guarded; tooling may only touch the cross-reference span. Corrections arrive as new entries that cite the old ones — the record keeps its own history honest.
*source: knowledge 016 (promote narrowed, never overwrite)*

**Distrust its own metrics** — The behavioral "does this skill add value" measurements are marked provisional in the record itself — not CI-gated, deltas not yet trusted. The system is biased toward saying so out loud.
*source: knowledge 013 (behavioral evals provisional)*

---

## Colophon

Generated with [MkDocs](https://www.mkdocs.org/) using the default theme. The *presence* of every skill in the catalog above is enforced by `tests/test_site_catalog.py` in this repository; the descriptions are excerpts taken at authoring time, and the narrative reflects the repository as of June 13, 2026.

minerva lives in the [honerlaw/agent-marketplace](https://github.com/honerlaw/agent-marketplace) repository, under `plugins/minerva/`.
