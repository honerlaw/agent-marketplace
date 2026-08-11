# A constraint nobody can fail is a wish; write the test and it finds violations that day

**Date**: 2026-08-11
**Type**: pattern
**Summary**: a knowledge entry stating a rule enforces nothing — this one was violated three times in two months and the first enforcing test caught a live defect immediately
**Context**: .minerva/work/2026-08-11-enforce-fence-aware-scans

## Context
[[2026-06-11-constraint-fence-scans-import-fence-re]] has said since June that any scan
over markdown must use the single-sourced `FENCE_RE` grammar. It is precise, correct, and
was cited approvingly in later work. Nothing checked it.

It was violated at least three times while it sat there:

- `work_status.is_post_promote` shipped fence-blind, past three reviewers, in the unit that
  *created* the module;
- `work_status.read_status` shipped fence-blind in the very next unit, written by someone
  who had just fixed a tolerant-reading bug;
- `knowledge_fix.plan_index` scanned `index.md` with a bare `splitlines()` while
  `knowledge_lint.parse_index` scanned the same file through `_strip_fences`.

The third one had teeth. `plan_index` **rewrites** `index.md` from what it parses, so a
fenced catalog line naming a real entry was invisible to the detector and a live line to
the rewriter — the entry came out catalogued **twice**, one copy carrying the example's
fake summary, with zero refusals and a clean lint run.

The enforcing test was written and it failed on the third instance **on its first run**.

## Finding
**A rule recorded in prose changes nothing about whether code obeys it.** That sounds
obvious and is not treated as obvious: this constraint was written down precisely *because*
it had already been violated, and writing it down was mistaken for addressing it.

The empirical claim worth carrying: **when you finally write the enforcement, expect it to
find something.** It is not a formality over an already-clean corpus. If it passes on the
first run, suspect the check before believing the corpus — a gate that has never failed has
not yet been shown capable of failing, which is why the negative-coverage fixture (prove it
fires on the violation) matters more than the positive one.

Two design consequences, both learned the hard way in this repo:

- **Ask the corpus; do not list the things that need checking.** The obvious shape is a
  curated list of "the modules that scan markdown". That list is the artifact
  [[2026-08-11-pattern-the-enumeration-is-what-fails]] describes, and it decays in the
  *dangerous* direction: a module missing from it reads as checked. Enumerate the whole
  directory and require every member to comply.
- **Put the escape hatch at the call site, not in the test.** A module that legitimately
  scans non-markdown declares `# not-markdown: <reason>` on the line. The justification
  then lives next to the code it excuses, an unjustified exemption cannot be added quietly,
  and the test can assert every exemption carries a reason. Exemption lists inside the test
  drift away from the code and nobody reads them.

**State the gate's granularity rather than letting it be assumed.** This check is
per-module, not per-scan: a fence-blind scan added to an already-aware module still passes.
That is the honest limit of a static check without dataflow, it covers both observed
violations, and saying so in the test's own docstring is the difference between a gate and
a false sense of one.

## Implications
- When promoting a constraint, ask what would fail if it were violated. If the answer is
  "a reviewer might notice", it is not yet a constraint.
- A `Type: constraint` entry is a good place to record the *reasoning*; it is not a
  mechanism. Pair it with the test, or record why one is impractical.
- The three violations here were all found by review or by accident, never by the tooling —
  consistent with what the sibling entries record about hand-checking one's own recognizers.
- Cheap enforcement often exists: this one is an enumerating test over a directory, in the
  same style `tests/test_skill_contracts.py` already uses for skill structure.

## Related
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — builds on
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — builds on
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
