---
name: one-by-one
description: Walks the user through the questions already outstanding in the current session, one at a time, showing the running position and total ("Question 3 of 10") and waiting for each answer before the next. Every question offers three to five concrete options, marks a recommended answer or says there is none, and always accepts the user's own direction instead. Use when several questions have piled up and answering them in one reply would be awkward, or the user says "ask me one by one", "one at a time", "go through these questions", "walk me through the open questions" or "what do you still need from me". Takes a finite list that already exists; to probe a drafted plan with new questions until understanding is reached, use `minerva:grill-plan` instead. Use also when the user invokes `minerva:one-by-one`.
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Turn a pile of open questions into a walk-through the user can answer one at a time, always knowing how far along they are.

## Usage

- `minerva:one-by-one` — collect the questions from the current session.
- `minerva:one-by-one "<topic or list>"` — limit it to a topic, or supply the questions directly.

## Protocol

### 1. Collect

With an inline argument, use only that topic or list. Otherwise gather every question still open in this session: questions the assistant asked that went unanswered, decisions blocking work in progress, and the `## Open Questions` of a work unit this session is working on.

The list is finite. Do not invent probing questions to extend it.

### 2. Reduce

Drop what the session already answered. Answer what a quick look at the repo or `.minerva/knowledge/` settles, and report those in the announcement instead of asking them. Merge duplicates. A question a quick look does not settle stays a question.

### 3. Order

Ask a question first when its answer changes another question. Otherwise lead with what matters most.

### 4. Announce

State the total, list one short line per question, and name the reply words (`skip`, `back`, `stop`, or add a question). Then ask question 1 in the same turn; do not wait for a go-ahead.

With nothing left to ask, say so, name what you checked, and stop.

### 5. Ask

Ask exactly one question per turn and wait for the answer before asking the next. Never batch questions, and do no work that depends on the answer while waiting.

Put `Question k of N` inside the question itself, on every question, because a question dialog may be all the user sees. For the same reason, include the context needed to answer the question cold, and the reply words.

Offer three to five concrete options on every question. Prefer three or four; add a fifth only for a real fifth answer. When a question has fewer than three natural answers, complete the list with a real variant ("yes, but only for X") or a real disposition ("decide later"), never with filler.

Mark exactly one option `(Recommended)`, put it first, and give a one-line reason. When you have no recommendation, write `No recommendation — <why>` in the question and mark no option. Never leave the reader to guess which case applies.

Use the user question operation from the runtime contract when it can carry every option plus a free-form answer. When it cannot, or when you are unsure, ask directly in a message and wait. Never drop a real option to fit the tool. The free-form path does not count toward the three to five.

As a direct message:

```text
Question 3 of 10 — Cache location

Sessions are lost on deploy today. Where should they live?

1. Redis (Recommended) — already deployed and shared across instances
2. In-process LRU — simplest, but still lost on deploy
3. Postgres table — durable, slower on every request
4. Decide later — keep the current behaviour for now

Reply with a number or your own direction, or: skip, back, stop.
```

With no recommendation, a line above the options reads `No recommendation — depends on the launch date, which only you know.` and the options carry no mark.

### 6. Handle the reply

Always accept the user's own direction in place of any option, and never re-argue it against your recommendation. Their words are the answer.

| Reply | Do this |
|---|---|
| An option, or their own direction | Record it and go to the next question. |
| An answer that also settles later questions | Record those too, and drop them from the list. |
| Unclear | Ask one clarification under the same number. If it stays unclear, record their words as skipped and go on. |
| A question back to you | Answer it, then re-ask the same question. |
| A new question to add | Add it to the end of the list, then re-ask the current question. |
| `skip` | Record it as skipped, then reword or drop any question that depended on it. |
| `back`, or `back 2` | Re-ask the previous or named question, re-check any that depended on it, then return to where you were. At question 1, say nothing is earlier and re-ask it. |
| `stop` | Go to the recap. |
| "Take your recommendations" | Apply them to the remaining questions that have one, and mark those `recommended, unseen` in the recap. Still ask each `No recommendation` question. |
| A dismissed dialog | Stop and recap. A dismissal is not an answer, and nothing is assumed. |

The total never changes silently. When an answer or the user adds a question, or makes one irrelevant, say so on the next question: `Question 4 of 11 (1 added)`, `Question 5 of 9 (1 dropped: settled by question 3)`.

### 7. Recap, then hand back

Show a table of every question: number, question, answer, and how it was answered (recommended, another option, own words, skipped, dropped, not reached).

If an answer resolves a work unit's `## Open Questions`, say so: it stays open in `proposal.md` until the work phase records it.

The skill ends there and takes no action of its own. A caller, or work this session was already doing, continues under the authorization it already had; with neither, stop. The answers grant nothing beyond what they say.

## Out of scope

- **Writing files.** The answers live in the conversation; a caller owns any persistence.
- **Generating new questions.** Probing a drafted plan is `minerva:grill-plan`; weighing directions before a plan exists is `minerva:explore`.
- **Gating an orchestrator.** No orchestrator calls this skill, and an autonomous run's escalations stay as they are.
