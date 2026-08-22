# Proposal: close-open-issue-backlog

**Date**: 2026-08-22
**Status**: Draft
**Base**: `origin/main`

## Goal

Give every one of the 13 open GitHub issues a correct terminal state. Nine land code or
doc fixes and are closed by this unit's PR. One (#76) is investigated, has its finding
recorded, and is deliberately left open because the test it asks for cannot exist. Three
(#74, #82, #83) cannot be actioned by an agent at all and are reported with reasons.

"Address all" is read as *give each issue the right disposition*, not *close every issue*.
Closing #76 with a test that cannot observe its defect would satisfy the count and betray
the instruction.

## Why

`minerva:promote` and `minerva:backfill-followups` file deferred work as `minerva:followup`
issues. Nothing drains the queue — [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]]
in its purest form. The backlog is 13.

Six of them (#85, #79, #78, #77, #70, and #76's stated ask) are one pattern this repo has
already named: [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — a documented
rule with no enforcing test gets violated. The remaining four closable items (#81, #80, #75,
#71) are **not** that theme; they are small independent fixes grouped because they are in the
backlog, and this proposal does not pretend otherwise. Precedent for draining a
heterogeneous backlog as one unit is direct and recent: `2026-08-11-close-the-followups`
(5 fixes) and `2026-08-11-close-remaining-loose-ends` (7 fixes).

**Why not decompose into three units.** The one dependency that matters runs the wrong way
for a split: #71 builds the mechanism (`Closes #N` in the PR body) that closes this very
backlog. Shipped as its own later unit, it arrives after the issues it would have closed
are already closed by hand, and lands unexercised. Bundled, the batch is its own first test
case. The remaining items touch disjoint files and carry no cross-unit risk that isolation
would reduce.

**Blast radius, accepted deliberately.** One PR across `tests/`, `scripts/knowledge_fix.py`,
seven skill files and two READMEs means a red check on any one item blocks the rest. The
response is `minerva:ship`'s bounded auto-fix loop, not a partial re-split — splitting a PR
mid-flight would strand the `Closes` footer that closes nine issues.

## Approach

Execution order is load-bearing and fixed: **#85 → #79 → #70 → #75 → #81 → #71 → #80 → #78 → #77 → #76**.
#71 early so the mechanism exists before this unit's own ship phase, and #80 before #78 so
the anchor test sees `propose-ship`'s final file layout — those two are genuine dependencies.
#85 leads for a weaker reason, stated honestly: it changes the pointer grammar that every
later skill edit is checked against, and only #85 itself is known to introduce a qualified
cross-skill path. It is defensive sequencing, not a hard dependency.

### 1. #85 — the pointer gate cannot express a cross-skill reference

`REF_MENTION_RE` in `tests/test_skill_budget.py` is unanchored, so a fully-qualified
`plugins/minerva/skills/promote/references/github-issues.md` matches as bare
`references/github-issues.md` and is resolved against the **citing** skill, where it dangles.
A cross-skill reference is therefore unrepresentable as a path, and `minerva:backfill-followups`
had to phrase around it.

Extend the mention grammar with an optional `plugins/minerva/skills/<skill>/` qualifier.
A qualified pointer resolves against the **named** skill; a bare pointer keeps resolving
locally. `test_every_reference_file_is_pointed_to` stays local-only — a foreign mention must
not satisfy the owning skill's own must-point-at-it rule, or a reference file could become
undiscoverable from its own SKILL.md. Then convert `backfill-followups`'s phrased-around
prose to the real path, which is the proof the constraint is dissolved.
[[2026-08-22-constraint-a-skill-cannot-path-reference-a-sibling-skills-reference-file]] is
superseded by this, not amended.

### 2. #79 — nothing enforces the 1024-char description ceiling

One parametrized test over the enumerated skills asserting
`len(frontmatter["description"]) <= 1024`. Measured current max is 974
(`propose-ship-balanced`), so it lands green with real headroom.
[[2026-07-21-constraint-skill-description-house-style]] states the ceiling; nothing tested it.

### 3. #70 — the snippet runner could extract a mutating `gh` block

`tests/test_skill_snippets.py` extracts fenced blocks from SKILL.md files and **executes**
them. It is safe only because every currently-extracted block happens to be read-only —
a property nothing enforces. `minerva:promote`'s `references/github-issues.md` documents
`gh label create` and `gh issue create`; an extraction added for it would have CI mutating
whatever repo the runner is authenticated against. This has already cost a real label that
had to be deleted by hand ([[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]]).

The guard goes **inside `fenced_blocks()`**, not beside it: every extraction is checked,
present and future. A guard a future author must remember to call is the same defect shape
as #77's plea.

### 4. #75 — the docs site is unreachable from the repo

`.github/workflows/pages.yml` builds and deploys the MkDocs site; neither `README.md` nor
`plugins/minerva/README.md` links it. Add the GitHub Pages URL to both.

### 5. #81 — `plan_reciprocals` runs when `plan_index` refuses

`knowledge_fix.plan()` calls `plan_index` and `plan_reciprocals` independently, so a hard
index refusal still returns entry edits and `apply()` writes them — a half-reconciled corpus
where neighbour entries gained back-links the index does not know about.

The distinction that matters: `plan_index` has **two** refusal kinds. A *per-entry* refusal
(no `**Summary**`, unrecognized type) still returns a rewritten index and must keep both
halves. A *hard* refusal (missing/empty index; an entry unplaceable in any known section)
early-returns `old, old, refusals` and must suppress the entry edits entirely.

**The obvious gate is wrong, and it was caught by reproduction rather than reasoning.** The
first draft inferred hardness from the return values — "index unchanged **and** refusals
present". That signature is not unique to a hard refusal. It is the *steady state*: once a
corpus has been canonicalised, a benign per-entry refusal (say one entry of unrecognized
type, already sitting in a known section) recurs on every subsequent run against an index
that no longer changes. Reproduced against the real module: `new == old` is `True` with a
per-entry refusal present. An inferred gate would discard legitimate reciprocal edits on
every steady-state run, reintroducing the half-reconciled corpus from the other direction —
the bug wearing a different hat.

So the signal is **explicit, not inferred**: `plan_index` returns a fourth element,
`hard: bool`, set only at its two early-return sites. `plan()` suppresses entry edits on
`hard` alone and never inspects text equality. This follows the repo's standing rule against
deriving state from a spelling or a coincidence — the same reasoning behind
[[2026-08-09-pattern-read-authored-metadata-from-where-it-is]]. Two in-repo test call sites
unpack the 3-tuple and are updated with it; the unpack arity is itself the mechanical check
that no caller silently ignores the flag. Both paths get a test, including the steady-state
case above as the negative case.

### 6. #71 — nothing closes followup issues whose work has shipped

Not a heuristic. The issue itself warns "a wrong auto-close is worse than a stale-open
issue", and inferring linkage from a diff is exactly that. Instead make the linkage
**authored** and let GitHub do the closing:

- `minerva:propose`'s proposal template gains an optional `**Closes**: #N, #M` field.
- `minerva:ship`'s PR-body step emits one `Closes #N` line per entry.

No inference at any point. **Bootstrap:** the field is optional, so its absence at propose
time is legal; it is authored at the end of the work phase by the model that just wrote the
diff and knows what it closed, and read at ship time. That is why #71 sits early in the
execution order — the mechanism must exist before this unit's own ship phase needs it.

**Prospective only.** It does nothing for followup issues opened by units that already
shipped; retroactively editing closed proposals is out of scope. Those close by hand, as
they do today.

### 7. #80 — `minerva:propose-ship` has no `references/` split

It is the only orchestrator with no `references/` directory; its three siblings are all
split, and the originating unit could not add the Phase 7 rationale its siblings carry
because there was nowhere to put it. Move the phase detail into `references/phases.md`,
add that rationale, and keep `SKILL.md` under the 9216-byte budget behind a read-directive
pointer per [[2026-06-11-constraint-skill-progressive-disclosure]]. Currently 8691 bytes,
so this is headroom work, not an emergency.

### 8. #78 — cross-skill references by internal step number

`propose-ship-quick`/`-balanced`/`-auto` cite siblings as "per `minerva:propose` steps 8–9, 11".
Renumbering a sibling breaks the reference with nothing to detect it. The sibling
`Hard gate #1/#2` citations are a milder case — they already carry parenthetical names
(`(commit message)`, `(PR title + body)`), so they degrade rather than break — but they are
converted too, since the same anchor form covers both.

Adopt the named-anchor form the corpus **already uses** elsewhere — ``per `minerva:review`'s
"Triage persistence" section`` — rewrite the step-number citations into it, and add a contract
test that extracts every ``` `minerva:<skill>`'s "<Heading>" ``` mention and asserts a matching
heading exists in that skill's `SKILL.md` or `references/*.md`. Runs after #80 so the test
sees `propose-ship`'s final layout.

### 9. #77 — six target-resolution blocks kept in sync by a plea

**Revised from the approach the panel approved, on evidence gathered after that vote.**
The approved plan was a normalized-diff test asserting the six blocks are byte-identical
once the sibling enumeration is stripped. Inspecting all six shows they are **not copies**:

| block | steps | deliberate divergence |
|---|---|---|
| `work/SKILL.md` | 5 | verbose, carries a worked example |
| `replan/SKILL.md` | 5 | terse |
| `promote/SKILL.md` | 5 | extra Mode B paragraph |
| `cleanup/SKILL.md` | **3** | different semantics — no-arg means "all merged worktrees" |
| `review/references/protocol.md` | 5 | step 5 = no minerva context, skip to code review, **do not stop** |
| `ship/references/protocol.md` | 5 | step 5 = **bare mode** |

Byte-identity is unreachable: normalizing enough to make `cleanup`'s three steps match
`work`'s five would erase everything the test is supposed to check. That is precisely the
green lie the Skeptic warned this test could become
([[2026-08-10-pattern-presence-assertions-rot-into-green-lies]]).

What is genuinely shared, mechanically exact, and load-bearing:

1. **The sibling enumeration.** Each block names the other five. Verified: all six are
   currently correct. A rename or a seventh adopter breaks this, exactly and detectably.
2. **The two operational clauses.** Every block must state that *both* locations are
   scanned (`.minerva/work/*/` **and** `.minerva/worktrees/*/`) and that *both* id forms are
   matched (`YYYY-MM-DD-<slug>` and legacy `NNN-<slug>`). These are not stylistic — a
   digit-anchored glob silently skipping date-named units is a bug this repo has already
   shipped and fixed.

The test enumerates the six blocks by their `## Target resolution` heading and asserts both.
The plea sentence stays, but it is no longer the *only* mechanism, which is what
[[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] asks for. Each assertion
gets a negative case proving it fires. **Framing corrected:** this makes drift impossible to
ship silently; it does not stop drift being introduced, and it does not reduce the six-copy
maintenance burden.

**Why #77 closes while #76 stays open, given both fixes are partial.** The test is narrower
than #77's title implies, so the asymmetry needs saying rather than inferring. The line is
whether the delivered check can *fail on the defect it names*. #77's can: the plea's job is
to keep the six blocks agreeing, and a rename, a seventh adopter, or a dropped
both-id-forms clause now reds CI. Real enforcement replaces some of the plea, and what is
left unenforced is prose style, not operational content. #76's cannot fail on anything: every
property a repo test can reach is green on precisely the skills that are broken. Partial
enforcement closes; zero enforcement does not.

Extraction to one shared file (the alternative) stays rejected: ownership is ambiguous among
six equal peers, it changes the runtime load path of six live skills, and — now that the
blocks are known to be genuinely different — there is no single block to extract.

### 10. #76 — rendered skill listings drop valid descriptions

The issue asks for a test that renders the listing and asserts descriptions survive.
**That test cannot exist in this repo,** and the evidence is direct:

- Live 2026-08-22 session: `backfill-followups`, `lint`, `migrate-fix` and `replan` render
  as bare names. `lint-fix` — bare in the original 2026-07-21 observation — now renders fine,
  with no source change between the two observations.
- Ruled out as correlates: frontmatter line count (the bare set spans both 2-line and 7-line
  frontmatter) and description length (`lint` 630 chars renders bare; `lint-fix` 627 chars
  renders fine — same directory, same format, same shape).
- [[2026-07-21-bug-skill-listing-description-drop]] already records valid frontmatter in
  every on-disk copy: source repo, installed plugin, plugin cache.

Every property a repo-side test can reach is therefore known-good on precisely the skills
that are broken. Such a test passes while the defect is live — the exact shape of
[[2026-08-10-pattern-presence-assertions-rot-into-green-lies]], whose own entry records two
defects that shipped under passing anchors.

Deliverable: append the new observation to the bug entry (append-only, per that entry's own
Implications), comment on #76 explaining why the specified test cannot observe the failure,
and retitle it to the real ask — diagnose the loader. The issue stays **open** and is
**not** in the PR's `Closes` list.

### Not actionable by this run

- **#82, #83** — submit minerva to claudepluginhub.com and to cc-marketplace. Both are human
  web-form submissions; both issue bodies already say "close it by hand once submitted".
  No code change closes them and no agent can verify they were done.
- **#74** — validate the behavioral-eval signal and control. Requires N live `claude -p` runs
  per case, a run-to-run variance analysis, and a go/no-go judgment that gates a 20-skill
  backfill. That is a research unit with its own proposal, not a line item in a backlog drain.

These three are reported prominently in the final report, not buried: the user reserved
scope calls for themselves, so the exclusions are surfaced as decisions to review.

## Success criteria

1. `pytest tests/` passes from a clean checkout of the branch.
2. Every new assertion has a negative case that fails when its defect is reintroduced —
   demonstrated by a test, not asserted in prose.
3. **#85**: a qualified `plugins/minerva/skills/<other>/references/<f>.md` pointer resolves;
   a bare pointer still resolves locally; a qualified pointer naming a nonexistent file still
   fails; `backfill-followups` cites `minerva:promote`'s file by real path.
4. **#79**: a description over 1024 chars fails the suite.
5. **#70**: a fenced block containing a mutating `gh`/`git` verb fails extraction, from
   inside `fenced_blocks()`.
6. **#75**: both READMEs link the site URL.
7. **#81**: `plan_index` returns an explicit `hard` flag; `plan()` gates on it alone. A hard
   refusal yields `entries == {}`; a per-entry refusal on an already-canonical index (where
   `new == old`) still yields entry edits. Both tested, the second as the negative case.
8. **#71**: the proposal template documents `**Closes**`; `minerva:ship`'s PR-body step emits
   `Closes #N`; this unit's own PR carries `Closes` for #70, #71, #75, #77, #78, #79, #80,
   #81, #85 — and not #76.
9. **#80**: `propose-ship/references/phases.md` exists and is pointed at with a read
   directive; `propose-ship/SKILL.md` is ≤ 9216 bytes; budget and pointer tests green.
10. **#78**: every `` `minerva:<skill>`'s "<Heading>" `` citation resolves to a real heading;
    no step-number citation remains in the three orchestrators.
11. **#77**: each of the six blocks names exactly the other five siblings and carries both
    the both-locations and both-id-forms clauses; each assertion has a negative case.
12. **#76**: the bug entry carries the 2026-08-22 observation; #76 is commented, retitled,
    and left open.
13. **#74, #82, #83** are named with reasons in the final report.

## Open questions

- **#76's issue retitle and comment mutate GitHub state rather than the repo.** Taken as in
  scope: the user's instruction was to address issues, and the issue is the artifact. Flagged
  because it is the one deliverable with no diff.
- **#78's anchor grammar has no prior art as a machine-checked form.** It is used in prose
  today; making it load-bearing is new. If the extraction proves too noisy against real prose,
  the fallback is to check only citations that already match the quoted-heading shape.
