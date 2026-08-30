---
name: propose
description: Starts a new minerva work unit — brainstorm-style intake with one-question-at-a-time clarification, 2-3 candidate approaches, a `minerva:grill-plan` stress-test before approval, then creates the unit's branch + worktree and writes the approved design to `.minerva/work/<date-slug>/proposal.md`, with a self-review and a post-write user gate. Use when the user wants to plan or design a new feature, refactor, or investigation in a minerva-tracked project, says things like "let's build X", "let's plan Y", or "start a new unit of work", when `minerva:explore` hands off a converged direction, or when the user invokes `minerva:propose`.
---

Start a new work unit by brainstorming, creating its branch + worktree, and writing its proposal inside the worktree.

## Usage

- `minerva:propose` — brainstorms a new work unit; infers intent from current-session context, or asks if context is blank
- `minerva:propose "add rate limiting"` — inline description used as the starting point for Q&A

## Pre-flight check

If `.minerva/` doesn't exist yet at the project root, suggest the user run `minerva:init` first so the directory layout and agent-file Routing section are in place. You can still write the proposal without it, but `minerva:init` is the cleaner entry point.

## Protocol

This skill mirrors the `superpowers:brainstorming` flow but writes to `.minerva/work/<date-slug>/proposal.md` instead of a generic spec path.

**Convergent step — relationship to `minerva:explore`.** `minerva:propose` is the *convergent* step of the lifecycle: its job is to produce the `proposal.md` artifact (plus the branch and worktree). Its optional upstream counterpart is `minerva:explore` — the *divergent*, commitment-free phase for exploring a fuzzy idea before any work unit exists. The two diverge on different axes and compose: `minerva:explore` diverges on the **problem / direction** axis (*what* or *whether* to build), while `propose` diverges on the **implementation-approach** axis (*how* to build the chosen direction). When you arrive here from a `minerva:explore` handoff, the converged direction is passed as the inline description (see step 1) — the problem-space exploration is already done, so do **not** re-litigate *whether* or *what* to build; confirm the chosen direction and proceed to designing *how* (the approach work in steps 7–8). This boundary rides propose's existing inline-argument intake; there is no separate "did exploration happen?" detection to perform.

1. **Context-sensitive intake.** Determine what the user wants to build before asking clarifying questions:
   - If a description was passed inline → treat it as the draft goal; skip the "what do you want to build?" question and confirm/refine it. (A handoff from `minerva:explore` arrives exactly this way — the converged direction is the inline description.)
   - If no description but current-session chat history is present → read the history and repo structure, state the inferred intent ("Based on our conversation, it sounds like you want to X — is that right?"), and let the user confirm or redirect.
   - If no description and no relevant current-session history → ask "What would you like to build?"

2. **Open-issue match.** Now that you know what is being asked for — and *before* any clarifying question — check whether an **open** GitHub issue already tracks it, and offer to execute that issue instead. Nothing but a work unit that links back to an issue ever closes the backlog `minerva:promote` files, so a request that unknowingly duplicates one leaves the issue open forever. **Read `references/issue-match.md` and run it now**; it fails soft, skipping itself silently on any repo with no reachable issue tracker.

3. **In-flight work check.** Still before any clarifying question, check whether this work is **already in flight** — in this checkout, in another clone, or in a live sibling Claude session. Propose's own duplicate-slug check runs only *after* the whole design exists, which is too late to save the design work, and it sees only slugs. **Read `references/in-flight-check.md` and run it now**; every one of its four evidence sources fails soft, so a repo with no remote, no issue tracker, and no sibling sessions passes through it silently. That step messages live peers, so also **read `references/cross-session.md`** — the inform-never-delegate contract governing what a session may send a peer and what it does with what arrives. It applies for the rest of the session, not just at intake.

4. **Scope check.** Before asking clarifying questions, decide whether the request fits a single work unit. **Too big for one PR is not a reason to decompose** — it is a reason to *phase*: one work unit with an ordered `## Phases` section, shipping one PR per phase. **Read [references/phasing.md](references/phasing.md) before declaring phases** — it carries the soft ceiling, the branch topology, and the derived-progress rule. Reach for separate work units only when the request spans **genuinely independent subsystems** ("build a platform with chat, billing, analytics", "rewrite the entire data layer") — work that would not share a proposal, a reviewer, or a record.

   **Splitting into separate units is not free, and this step used to read as though it were.** Each additional unit pays its own propose, worktree, review, promote, knowledge reconciliation and ship cycle, plus a human decision gate at every phase transition — and each one re-derives the project context the last one just built. Weigh that against the one cost splitting avoids (a long proposal). Do not produce a 500-line proposal for work that should be three separate units; equally, do not produce five work units for work that is one unit with three phases.

5. **Explore project context.** Read `CLAUDE.md` / `AGENTS.md` if present, skim `.minerva/knowledge/` (and `.minerva/decisions/` if it still exists — legacy directory), glance at recent `.minerva/work/*/proposal.md` files for tone and conventions. This informs the questions you'll ask.

6. **Ask clarifying questions one at a time.** Cover purpose, constraints, and success criteria. Prefer multiple-choice. Don't batch.

7. **Propose 2–3 approaches** with tradeoffs and a recommendation. Lead with the recommendation. Iterate based on user feedback.

8. **Draft the design internally**, then **stress-test it before showing it for approval.** Pull the chosen approach plus everything gathered so far into a complete first-pass draft of Goal / Why / Approach / Success criteria / Open Questions — keep it in conversation, do not write any file yet. Then invoke the `minerva:grill-plan` skill via the `Skill` tool against that draft (it takes no argument — it reads the drafted design from conversation); do not paraphrase its protocol inline. Let grill-plan walk the decision tree, edit affected sections of the draft in place as answers surface, and return only once shared understanding is reached. The draft that exits grilling is what step 9 presents.

9. **Present the design in sections** (Goal, Why, Approach, Success criteria, Open Questions). Get approval per section before moving on.

10. **Pre-write hard gate:** do not write any file until the user has explicitly approved every section.

## On approval — worktree setup + file writes

The full on-approval sequence — slug derivation, duplicate check, date id, default-branch resolution, gitignore pre-flight, `git worktree add`, worktree-prefixed addressing (no `EnterWorktree`), the `proposal.md` + `scratchpad.md` templates, self-review, initial commit, and the post-write user gate — lives verbatim in `references/on-approval.md`. **Read it in full the moment every section is approved, before writing anything.**

## Out of scope

- **Implementation.** This skill stops at writing and confirming the files. `minerva:work` is the next phase.
- **Worktree abandonment.** If the user rejects at the post-write gate and wants to abandon the work unit, they run `git worktree remove .minerva/worktrees/<date-slug>` plus `git branch -D <date-slug>` manually. Propose does not offer an `--abandon` flow; cleanup is reserved for shipped work.
