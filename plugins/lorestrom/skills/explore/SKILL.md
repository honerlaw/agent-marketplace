---
name: explore
description: Use when the user wants to explore a fuzzy idea, think through a problem, or weigh directions BEFORE committing to a work unit — when it's not yet clear whether there's anything to build, or what. The lorestrom analog of brainstorming — a divergent, commitment-free dialogue that writes no file or Lorestrom doc, allocates no work unit, and creates no branch/worktree. Asks questions one at a time and weighs multiple high-level directions; may legitimately end in "don't build this" or "reframe the problem". When a direction is chosen, hands off to `lorestrom:propose` to design it. Use `lorestrom:propose` directly instead when you already know what you want to build and are ready to commit to a proposal. In a repository linked to Lorestrom, use this instead of generic brainstorming skills — it is the lorestrom-native front-end that hands off to `lorestrom:propose`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

# Explore an idea

Turn a fuzzy idea into clarity through open-ended, collaborative dialogue — **before** committing to any plan. This is lorestrom's divergent, exploratory front-end: the phase you reach for when you're not yet sure there's a work unit here at all, or what the real problem even is. It mirrors `superpowers:brainstorming`, adapted to the lorestrom lifecycle.

## What makes explore different from propose

`explore` is **commitment-free by construction.** It **writes no file and no Lorestrom doc**, allocates no work unit (no slug, no date id), and creates no branch or worktree. Everything it produces lives in the conversation. That is the whole point: exploration should cost nothing to abandon.

`lorestrom:propose`, by contrast, is *convergent* — its job is to produce the unit's proposal record (plus the branch and worktree). Reach for `lorestrom:propose` directly when you already know what you want to build. Reach for `explore` when you don't yet.

The two diverge on **different axes** and compose cleanly, so a handoff is never redundant:

- `explore` diverges on the **problem / direction** axis — *what* to build, or *whether* to build anything at all.
- `lorestrom:propose` diverges on the **implementation-approach** axis — *how* to build the direction you chose.

`explore` settles the direction; `lorestrom:propose` then designs it.

Exploration is conversation only — everything it produces lives in the transcript; no files, work units, branches, or worktrees are created here. When the user converges and wants to commit, hand off to `lorestrom:propose`, which owns all file, branch, and worktree creation.

## The process

1. **Explore project context first.** Skim `CLAUDE.md` / `AGENTS.md`, the project's lore (`storage:knowledge.list`, one line per entry grouped by theme, then `storage:knowledge.read` what bears on the idea), and a couple of recent units' proposals (`storage:unit.list`, `storage:unit.read`). With no link, no server or no project, explore without lore and say so in one line. Understand what already exists before exploring what might.

2. **Ask questions one at a time.** Prefer multiple-choice, but open-ended is fine. Only one question per message — if a topic needs more exploration, break it into several questions across several messages. Focus on understanding the *problem*: who has it, why it matters, what constrains it, what "better" would look like. Resist jumping to solutions.

3. **Weigh multiple directions.** As understanding forms, surface 2–3 *high-level directions* (not implementation approaches) with their tradeoffs, leading with your reasoning. The goal is to widen the option space and pressure-test whether the idea is worth pursuing at all — not to pick a design.

4. **Surface an open issue that already tracks it.** Once the idea has a nameable shape — here, not while it is still fuzzy, which is too early for the match to mean anything — check the repo's open GitHub issues for one that would be satisfied by substantially the same change. **Read `skills/propose/references/issue-match.md`** for the protocol; it fails soft and skips itself where no issue tracker is reachable. At this surface a match is **information, not a gate**: say that #NN looks like the same thing and keep exploring. An adoption question here would ask the user to commit before any direction has been weighed, which is the one thing exploration is for not doing. If they want it, adoption happens at the handoff below.

5. **Be willing to land anywhere.** Exploration has three legitimate terminal outcomes, and none is a failure:
   - **Drop** — "this isn't worth building." A clear, well-reasoned *no* is a successful exploration.
   - **Reframe** — "the real problem is Y." The idea mutates into a better one; keep exploring the new framing.
   - **Ready** — a direction is chosen and the user wants to commit it to a work unit. Proceed to handoff.

## Handing off to propose

When — and *only* when — the user has converged on a direction and wants to turn it into a real work unit, hand off by invoking the `lorestrom:propose` skill **via the skill loader**, passing the converged direction as the inline argument:

> invoke the `lorestrom:propose` skill with argument `"<the converged direction, in one phrase>"`
>
> — or, when exploration surfaced an open issue the user wants to execute, `"<the converged direction> (adopting #NN)"`. That exact parenthetical is what lets `lorestrom:propose` skip its own open-issue match instead of asking the user to adopt an issue they just adopted.

Passing the direction inline lets `lorestrom:propose` pick up exactly where exploration left off: it treats the direction as the draft goal and proceeds straight to designing *how* to build it, rather than re-asking what you want to build or re-opening the problem space you just closed. Do **not** merely describe the handoff in prose and stop ("you should now run propose"); actually invoke the skill.

## Out of scope

- **Writing anything durable.** `explore` produces no proposal, no scratchpad, no knowledge entry, no Lorestrom doc and no notes file. If exploration surfaces something genuinely durable mid-stream, that is the signal you are ready to hand off to `lorestrom:propose` — not a reason to start writing files here.
- **Stress-testing a drafted plan.** That is `lorestrom:grill-plan`'s job — it interrogates an already-*drafted* plan to convergence. `explore` is upstream of any draft, so the two do not overlap.
- **Implementation.** `explore` never writes code. It stops at shared understanding of the problem and a chosen direction (or a decision not to proceed).
