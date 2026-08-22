# backfill-followups — the six-step protocol

Steps 1-4 are read-only. Step 4 is a hard gate. Only steps 5-6 mutate anything.

## Step 1 — Discover

```bash
find .minerva/work .minerva/worktrees -name followups.md 2>/dev/null | sort
```

`.minerva/worktrees/` is frequently absent or empty (every merged unit is cleaned up) —
`2>/dev/null` and an empty result are the normal case, not an error. Report the file count
and skip straight to the final report when it is zero.

Run `minerva:promote`'s capability probe now, before any triage, so a repo that cannot host
issues is discovered before the expensive judgment work rather than after it.

## Step 2 — Extract items

An LLM reads each file. **This is not a regex.** Real backlogs mix prose bullets, `- [ ]`
checklists, reusable paste-blurbs, and author annotations, and a bullet count is not an item
count.

**Atomization rule.** One item is:

- one **top-level bullet**, or
- one `##` subsection that proposes a distinct action.

A bullet offering two alternative fixes for one problem is **one** item, not two. A `##`
subsection whose bullets are the parts of a single action is **one** item. Nested bullets
elaborating their parent are part of it.

This rule is not stylistic — step 6 records each item's **verbatim first line** as its
re-run anchor, so two runs that atomize differently would not recognize each other's work.

Record anything judged a non-item with its reason. Nothing is dropped silently.

### The heterogeneity case

`publish-minerva-to-plugin-directories/followups.md` in the minerva repo is the worked
example, because one file holds four different shapes:

| Shape | Disposition |
|---|---|
| A reusable paste-blurb (`- Name: …`, `- Install: …`) | `not-an-item` — reference material for a human doing the submissions |
| `## Submit` — `- [ ]` web-form submissions | `manual` — real work, but no agent can do or verify it |
| `## Await (auto-crawl — no action)` | `not-an-item` — explicitly says no action; a reminder, not a task |
| `## Decided: skip` | `not-an-item` — the author already closed it |

A backlog that has only prose bullets is the easy case. Assume it does not.

## Step 3 — Assess relevance

Classify every item, and **cite evidence** for every classification: a file path plus what a
`grep` for it returns, a `.minerva/knowledge/` entry, or a `git log` line. "It looks done" is
not evidence.

| Disposition | Meaning | Filed? |
|---|---|---|
| `open` | Still real work | **yes** |
| `manual` | Needs a human acting outside the repo — submit a form, re-check a third-party listing | grouped at the gate for one keep-or-drop call |
| `shipped` | The work exists now; cite where | no |
| `obsolete` | The reason it existed is gone; say why | no |
| `not-an-item` | Blurb, header, or an author's own skip decision | no |
| `unsure` | Cannot be resolved with evidence | **yes — filed as `open`** |

An `open` item the operator declines to file this pass is recorded `open — not filed`, which is **non-terminal**: the next run offers it again (see step 6).

**`manual` items cannot be verified by any evidence source** — nothing in the repo records
whether someone submitted a web form. Do not guess in either direction: surface them as a
group and let the operator make one call.

**Fail open.** `unsure` is filed. A wrongly-filed issue costs one click; a wrongly-dropped
item is gone silently, with nothing to trigger its rediscovery
(`.minerva/knowledge/2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption.md`).
Never resolve an ambiguous item to `shipped` or `obsolete` to keep the issue count down.

Useful evidence sources, cheapest first:

```bash
ls plugins/*/skills/                       # did the proposed skill ship?
grep -rn "<distinctive phrase>" plugins/ tests/ scripts/
ls .minerva/knowledge/ | grep "<topic>"    # was it captured as knowledge?
git log --oneline --all -S "<distinctive string>" | head
```

An item annotated by its own author — struck through, or marked "CLOSED" / "discharged by
unit N" — is `shipped` or `obsolete` on that basis alone. Cite the annotation.

Assign a priority to each filed item from `github-issues.md`'s vocabulary. An item that sat
in a file for months is rarely `critical`; default to `medium` and justify anything higher.

## Step 4 — Gate (hard, batched per source file)

Present **one source file at a time**: each item, its disposition, its evidence, and the
proposed priority for those that will be filed. Accept subset approval — the operator can
keep some and drop others.

Batching is deliberate. A single table of every item in the project invites a rubber stamp,
which would forfeit the only human check between an LLM's judgment and a public issue
tracker. **Nothing is created before this gate.**

## Step 5 — File

Follow the `github-issues.md` protocol in `minerva:promote`'s `references/` directory exactly: label bootstrap, the
duplicate check, the `gh issue create` invocation with its title/body substitution rules, and
the per-item fail-soft. Two backfill-specific details:

- The back-link line names the **source unit**, so items keep their provenance:
  `Deferred from `.minerva/work/<source-date-slug>/` by `minerva:backfill-followups`.`
- A `manual` item the operator kept gets a body line saying no code change will close it,
  so a reader does not hunt for one.

## Step 6 — Record the disposition ledger

**Append** to each `followups.md` — never rewrite an item line, never delete the file. The
append-only shape is the same one `minerva:promote` uses for its own records
(`.minerva/knowledge/2026-06-02-constraint-promote-narrowed-never-overwrite.md`): the original
text stays readable, the diff at review stays small, and the anchor a re-run matches on stays
byte-stable.

```markdown
## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Items above are unchanged.

- **`minerva:init` should scaffold `.minerva/reference/`.** → shipped — `minerva:init` creates it (`grep -n "reference/" plugins/minerva/skills/init/SKILL.md`)
- **Phase B.2 — the interactive `minerva:lint` skill.** → shipped — `plugins/minerva/skills/lint/` exists
- **Duplicate-NNN detection in the linter** → #74 (priority: low)
- Reusable paste-blurb (`- Name: …`) → not-an-item — reference material, not a task
```

Each line carries the item's **verbatim first line** followed by ` → ` and its disposition.
That verbatim prefix is the ledger's key: step 2's atomization rule exists so it stays stable
across runs.

This section is **this skill's tier-2 idempotency ledger**, standing in for the
`proposal.md` `## Deferred work` section that `github-issues.md` names — a backfill run spans
many already-shipped units and does not own their proposals.

On a re-run, skip an item whose disposition is **terminal** (`→ #NN`, `shipped`, `obsolete`,
`not-an-item`, or a dropped `manual`). **Re-offer** an item whose disposition is
`open — not filed` — it is still live, and a ledger line is not a resolution. An operator who
keeps only the high-priority items this pass gets the rest back next pass; that is what makes
a second run worth doing.

Write a not-filed item as `open (<priority>) — not filed at this pass; <why>`, so the reason
survives for whoever reads it next.

## Step 7 — Report

Per file: items found, and the count per disposition. Then overall: issues created (with
URLs), items skipped as already-dispositioned, and anything that fell back to `followups.md`
because filing failed. **Name every skipped item** — a report that omits what it passed over
lies by omission.

## A note on testing this skill

The `gh` blocks above and in `github-issues.md` **mutate remote state**. Do not wire them
into `tests/test_skill_snippets.py`, which executes what it extracts — a prior verification
run against a live repo created a real label that had to be deleted by hand
(`.minerva/knowledge/2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state.md`).
`bash -n` over an extracted block is free and catches the quoting defects that matter.
