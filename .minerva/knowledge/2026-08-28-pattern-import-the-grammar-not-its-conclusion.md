---
name: import-the-grammar-not-its-conclusion
description: Use when a new reader adopts a shared parsing primitive — this corpus's fence-scan rule ("a fenced line is not a declaration") is a conclusion drawn for declaration-readers, and a reader asking whether ANY content exists needs the same grammar with the opposite conclusion.
metadata:
  type: pattern
---

# Import the shared grammar; do not inherit the conclusion drawn from it

**Date**: 2026-08-28
**Type**: pattern
**Summary**: A fence-scan primitive answers "where are the fences", not "what should I do about them"
**Context**: .minerva/work/2026-08-28-workstream-status-skill

## What happened

`workstream_status._has_scratchpad_body` decides whether a scratchpad holds anything past the
header `minerva:propose` writes — the discriminator between a unit that was proposed and one
somebody actually started. It imported `knowledge_spans.unfenced`, as
`2026-06-11-constraint-fence-scans-import-fence-re` requires, and then did what every other
caller of that primitive does: it skipped the fenced lines.

That was wrong, and the test caught it contradicting its own docstring. A scratchpad whose only
content past the header is a pasted traceback is a unit somebody is working in. Skipping the
fence reported it as an untouched draft.

## The distinction

Every prior reader of this primitive asks the same question — **is this line a declaration?** A
fenced `**Type**: pattern`, a fenced `## Related`, a fenced `**Status**: Shipped` are all
*examples of* a declaration, and reading one as the real thing is the failure the constraint
exists to prevent.

This reader asks a different question — **is there anything here at all?** For that question a
fence is content like any other, and the correct handling is inverted: a non-blank line *inside*
a fence is precisely the evidence being looked for.

So the primitive answers "where are the fences". What to do about them is the caller's, decided
from what the caller is asking. Both readers import the same grammar; only one of them skips.

## The rule

When adopting a shared scanning primitive, restate in the new caller **what question it is
asking**, and derive the handling from that — do not copy the handling from the nearest existing
caller. Where the handling differs from every sibling, say so at the call site: an inverted use
that looks like a mistake will be "fixed" into a real one by the next reader
(`2026-06-06-pattern-rejected-alternative-reinvented-at-runtime`).

## How it was caught

A test asserting the docstring's claim — that fenced content counts as body — failed against the
code. The docstring was right and the code was wrong, which is the useful direction: the intent
had been written down one screen above the loop that contradicted it.

## Related
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — refines: that entry mandates importing the grammar; this one separates the grammar from the conclusion a caller draws from it
- [[2026-06-02-constraint-knowledge-span-model-single-sourced]] — see also: the single-sourcing rule this obeys while diverging in handling
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also: another case where a reader's scope, not its permissiveness, was the dial that mattered
