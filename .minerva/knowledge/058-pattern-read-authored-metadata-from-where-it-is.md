---
name: read-authored-metadata-from-where-it-is
description: Use when a tool parses a hand-authored metadata field across a corpus older than the template that defines it — knowledge entry types, frontmatter keys, doc headers. One anchored regex silently reclassifies every entry using a different spelling, and the damage is invisible because the field looks present to a human reader. Resolve from a fallback chain ordered most-deliberate-first, and prove the last resort concordant before trusting it.
metadata:
  type: pattern
---

# Read authored metadata from wherever it is actually written

**Date**: 2026-08-09
**Type**: pattern
**Context**: .minerva/work/051-resolve-entry-type-tolerantly

**Summary**: `parse_entry` read an entry's type from one anchored spelling, `**Type**: x`. Across a 629-entry corpus 42 entries declared it somewhere else — `Type: x` plain (16), `**Type:** x` with the colon inside the bold (13), a prose H1 or nothing (10), frontmatter only (3) — and every one resolved to `None`, which `plan_index` cannot place and the linter reported as `type 'None' but catalogued under a 'constraint' section`: an error naming a mismatch the entry does not have. Fix by resolving through a fallback chain ordered most-deliberate-first (body field in any spelling → frontmatter → filename segment), which makes a fallback able only to fill a gap, never override an author. Before trusting the last resort, MEASURE its concordance: filename type matched declared type 642/642 across two corpora.

## Why this is invisible

A human opening `268-constraint-config-driven-pipeline-constant.md` sees `**Type:** constraint` and reads it as correct — it *is* correct; the colon is one character to the left. Nothing about the entry looks broken. The breakage only exists inside the parser, and it surfaces as a downstream error about something else entirely (a section mismatch), so the error message points away from the cause.

That is the general shape: **a tolerant human format read by a strict machine, where the failure is reported at a later stage.** Corpora accumulate spelling drift the moment more than one author, or more than one template version, touches them.

## The chain, and why the order is the safety property

Resolve from the first source that yields a value, ordered by how deliberately the author stated it:

1. **The body field, matched tolerantly.** All spellings of the field are the author writing the field. Widening the regex is not laxity — it is reading what is there.
2. **Structured frontmatter.** Machine-readable and unambiguous, but not every entry carries it.
3. **The filename.** The only source that always exists.

Ordering last-resort-last is what makes the change *additive by construction*: a fallback can only fire where the previous source produced nothing, so no entry's stated type is ever overridden. An entry misnamed against its own field keeps its field's answer. Encode that as a test — `test_body_field_beats_frontmatter_and_filename` — because it is the property that makes the fallback safe rather than merely convenient.

## Prove the last resort before trusting it

A fallback derived from a *different* source (a filename, a directory, a title) is a guess unless you measure it. Here: 642 entries across two corpora, filename type vs declared type, **zero disagreements**. That number is what justified the fallback; without it the honest move is to keep refusing.

Where measurement said *don't*, it was obeyed: 10 entries encode their type only in a prose H1 (`# 426 — bug: dontAsk mode …`). Parsing that is guesswork, so it is not attempted — the filename covers them anyway.

## Measure before proposing, not after

The unit began from a stated belief that "46 entries are typed `reference`". The corpus has **4**. The 46 were 42 unparseable-type entries plus 4 genuinely out-of-vocabulary, and the first two fix hypotheses — migrate the entries; add a frontmatter fallback — were each refuted by counting: frontmatter covers 3 of 42. Three rounds of measurement preceded a correct one-line diagnosis. A refusal count is a *symptom*; group it by cause before designing against it.

## Related

- [[026-decision-migration-check-read-only-entry-re-blindspot]] — the same blind spot one level up: there a corpus predating the FILENAME convention is invisible to every wiki tool, here one predating the type-FIELD convention is misread by it. Both are false-cleans, and both are why a shape check has to be tolerant of what corpora actually contain
- [[018-decision-phase-b-deterministic-lint-detector]] — the detector `parse_entry` belongs to; this widens what it can read without changing what it reports
