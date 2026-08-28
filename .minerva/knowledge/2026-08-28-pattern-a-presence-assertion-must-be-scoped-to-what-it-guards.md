---
name: a-presence-assertion-must-be-scoped-to-what-it-guards
description: Use when asserting that a required element exists in a document — scope the search to the region that DOES the work, because the surrounding prose explaining the requirement keeps a whole-file check green after the enforcement is deleted.
metadata:
  type: pattern
---

# A presence assertion must be scoped to the region that does the work

**Date**: 2026-08-28
**Type**: pattern
**Summary**: Prose explaining a requirement keeps a whole-file presence check green after the enforcement is deleted
**Context**: .minerva/work/2026-08-27-deferral-cost-model (see git history if the worktree has been cleaned up)

## What happened

A new rule required every filed tracker issue to carry a `**Failure scenario**:` line, enforced by
putting that line in the `gh issue create` body template. Two tests guarded it:

- loose — `assert "**Failure scenario**:" in github_issues_md`
- strict — extract the text between `gh issue create` and the heredoc terminator, and assert the
  line is inside *that*

Mutation-testing by deleting the line from the heredoc, **only the strict test failed**. The loose
one stayed green because the same file's prose explains the requirement several times over.

## Why this is worse than an ordinary weak test

`2026-08-10-pattern-presence-assertions-rot-into-green-lies` covers the general case: a presence
assertion cannot fail once its subject is removed. This is a sharper variant, and the sharpness is
the point.

**The documentation of a requirement is exactly what keeps a naive check alive after the
requirement's enforcement dies.** The two are not independent — a well-documented rule has its
key phrase scattered across explanation, rationale, and examples, so the better the prose, the
more reliably the loose assertion passes over a file whose *executable* half no longer enforces
anything. The failure mode arrives precisely at the files someone cared enough to explain.

## The rule

Scope the assertion to the region that does the work: the command, the template body, the code
block, the function — never the whole document. Locate that region structurally (its delimiters),
not by line number.

Keeping the loose test alongside is fine and mildly useful as a fast smoke check, provided the
strict one exists. What is not fine is having only the loose one and believing it means something.

## The tell

An assertion whose search space is a whole file, for an element whose absence would be a defect
only in one part of that file. Ask: if I delete this element from the place that uses it, but the
file still talks about it, does my test fail?

## Related
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — builds on: the general form; this is the variant where the file's own explanatory prose is what sustains the false green
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also: a check whose model of its subject is wider than the subject, rather than narrower
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also: the same definition-site / use-site distinction, here inside a single file
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — see also
