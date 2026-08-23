# Open-issue match — the intake pre-flight

A user asks for something. Before a work unit is created for it, check whether an **open**
GitHub issue already tracks that same thing, and offer to execute the issue instead.

This exists because `minerva:promote` files kept TODOs as issues and `minerva:backfill-followups`
migrated the historical backlog into the same tracker. Nothing but an authored `**Closes**` field
ever closes a `minerva:followup` issue, so a request that duplicates one produces a second record
of the same work and leaves the first open indefinitely. Matching at intake is the only point
where that is cheap to notice.

**Read this file before the first intake question.** Run the commands; do not paraphrase them.

## Step 0 — Skip clause

If the incoming inline argument already names an adopted issue — the form
`"<direction> (adopting #NN)"` written by [step 5](#step-5--response-shape-graded-by-surface) —
the decision is already made. **Skip this whole protocol**, carry `#NN` into the record per
[step 6](#step-6--what-adoption-records), and proceed with intake.

Without this clause an `minerva:explore` → `minerva:propose` handoff runs the check twice and
asks the user to adopt an issue they just adopted.

## Step 1 — Capability probe

Run the probe in `minerva:promote`'s "Step 1 — Capability probe", exactly as written there —
the same `gh repo view --json nameWithOwner,hasIssuesEnabled` call, read the same way.

A **non-zero exit** (no `gh`, not authenticated, no GitHub remote) or **`hasIssuesEnabled: false`**
means this repo cannot host the backlog this check reads. **Skip silently and proceed with
intake** — say nothing about it. Most projects are in this state, and an intake that stalls or
apologises because a tracker is absent is worse than one that never looked.

## Step 2 — Query the open issues

```bash
gh issue list --state open --limit 100 --json number,title,labels,updatedAt
```

Judge candidates from the titles; run `gh issue view <N>` for the few whose titles are plausible,
never for all 100. If the list came back at the 100 cap, the backlog is larger than one page —
run a second, keyword-targeted pass so a match beyond the cap is still reachable:

```bash
gh issue list --state open --search "<2-4 content words from the request>"
```

**This is not the duplicate check in
`minerva:promote`'s "Step 3 — Labels, and the duplicate check".** That one searches for an exact slug it wrote itself and is mechanical. This one matches
a fresh natural-language request against issue titles nobody wrote with this request in mind — a
judgment call, which is why the bar below is stated behaviorally rather than as a query.

## Step 3 — The match bar

Two outcomes, and the gap between them is deliberate.

- **match** — the issue's stated outcome and the user's request would be satisfied by
  **substantially the same change**. Both would be closed by one diff.
- **adjacent** — everything else that is not plainly unrelated: same subsystem, same theme, a
  prerequisite, a sibling of the request. **Same area is not a match.**

**When unsure, resolve to `adjacent`.** The two errors are not symmetric. A false match derails an
intake and forces the user to re-litigate a request they already made, and it does so at the
moment they are least able to check the claim. A missed match costs a duplicate work unit — which
`minerva:promote` still catches at end-of-work, when it authors the `**Closes**` field against a
diff that plainly resolves the issue. Only one of those two failures is recoverable downstream.

## Step 4 — Never adopt silently

An issue is adopted only when the user says so. Do not treat a match as a decision, and do not
rewrite the request to be the issue. The user asked for something; the issue is evidence that
someone else already asked for it, not a correction.

## Step 5 — Response shape, graded by surface

**At the convergent surfaces** — `minerva:propose`, and the inline Phase 1 of
`minerva:propose-ship-quick` / `-balanced` / `-auto`, where a work unit is about to exist — a
`match` is a real gate. Ask with `AskUserQuestion`, naming the issue number, its title, and its
`priority:` label when it has one — a human-filed issue, or one predating the convention, carries
no priority, and its absence is not a reason to withhold the offer:

- **Execute #NN instead** — the issue becomes the work unit's goal.
- **Proceed as asked, link #NN** — build the request as stated, and write
  `**Linked**: #NN — <title> (not adopted)` into `proposal.md` beside the `**Closes**` field, per
  `references/on-approval.md`. That field is the whole record: `minerva:promote` reads it at
  end-of-work and promotes it into `**Closes**` if the diff resolved the issue after all. A note
  left anywhere else — the scratchpad, this conversation — does not survive to that point.
- **Adopt #NN and extend it** — the unit covers the issue plus what the user added.

In an autonomous orchestrator this ask is **hardcoded** — it fires without regard to the run's
skip or verify predicates, exactly like the in-flight-work collision those skills already
escalate on — and it **increments the run's global escalation counter**, like every other
escalation those skills count. It is not exempt. A run that spends an escalation here has still
spent one.

**At `minerva:explore`** a `match` is information, never a gate. Say that #NN looks like the same
thing and keep exploring. Explore is commitment-free by construction and its own protocol says to
resist jumping to solutions; an adoption gate mid-exploration converts a dialogue that was cheap
to abandon into a commitment made before any direction was weighed. If the user shows interest,
adoption happens at the handoff — pass `"<direction> (adopting #NN)"` as the inline argument to
`minerva:propose`. The skip clause above then detects it, so nobody is asked twice.

**More than one issue can clear the bar.** Offer them together in one question rather than picking
for the user — a backlog that duplicated a request once often duplicated it twice, and which of two
overlapping issues to close is exactly the call the user is better placed to make. Adopting several
is legal: `**Closes**` takes a comma-separated list, and `minerva:ship` emits one `Closes #N` line
per entry.

**An `adjacent` result gets one line at any surface** — "#NN is related but not the same thing" —
and no question, so the user can pull it in if they want it without being asked to decide.

## Step 6 — What adoption records

On adoption, and only then:

1. The issue's title and body seed the drafted `## Goal` and `## Why`. Read the issue body; a
   `minerva:followup` issue carries the context of the unit that deferred it.
2. Write `**Closes**: #NN` into `proposal.md` at creation, per the field's rules in
   `references/on-approval.md`. `minerva:ship` reads it and emits one `Closes #N` line per entry
   into the PR body, which is what actually closes the issue on merge.

Nothing else changes. The unit is a normal work unit from here.
