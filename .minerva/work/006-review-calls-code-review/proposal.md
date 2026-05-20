# Proposal: review-calls-code-review

**Date**: 2026-05-19
**Status**: Draft

## Goal

Modify `plugins/minerva/skills/review/SKILL.md` so `minerva:review` always invokes `code-review:code-review` as part of its flow. When a minerva work unit is found, it runs both the spec-fidelity/knowledge audit and `code-review:code-review`, presenting both result sets in parallel (as separate sections) before interactive triage begins. When no minerva context exists, it skips the minerva audit and delegates directly to `code-review:code-review`.

## Why

`minerva:review` currently handles spec fidelity and knowledge compliance but explicitly punts on code quality — it only suggests the user run `code-review:code-review` alongside. This means two separate invocations and no unified picture of a changeset. Making `minerva:review` the single review entry point means: with context, you get design compliance and code quality in one pass; without context, it still works as a useful review tool rather than stopping with "no work units found." The parallel presentation keeps the two concerns distinct — minerva findings are about "did you build what you designed," code-review findings are about "is the code sound" — while avoiding the need to triage them as one jumbled list.

## Approach

Modify `plugins/minerva/skills/review/SKILL.md` with these changes:

1. **Target resolution — make it non-fatal:** Step 4 currently stops if `.minerva/work/` is missing or empty. Change it to: if no minerva work unit is found, skip directly to the `code-review:code-review` invocation (no minerva audit, no context read). The skill continues rather than stopping.

2. **Add `code-review:code-review` invocation after finding generation:** After the minerva spec/knowledge audit runs (when context exists), invoke `code-review:code-review` on the same diff. When no minerva context exists, invoke it directly and return.

3. **Parallel presentation (when both run):** Present findings in two labeled sections before triage:
   ```
   ## Minerva audit
   [spec fidelity + knowledge compliance findings]

   ## Code review
   [code-review:code-review findings]
   ```
   Then run a single unified triage pass across all numbered findings from both sections.

4. **Remove the "suggest running code-review:code-review alongside" line** from the General quality lens — it's now always run, not suggested.

## Open Questions

- None blocking. The no-minerva-context path delegates fully to `code-review:code-review` — whatever that skill's own behavior is (findings, triage, output format) is inherited as-is, not duplicated in this skill.
