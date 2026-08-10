# Skill descriptions lead with function and ambient triggers; invocation clause last; ≤1024 chars

**Date**: 2026-07-21
**Type**: constraint
**Context**: .minerva/work/2026-07-21-skill-best-practices-audit (see git history if the worktree has been cleaned up)

## Context
Unit 046 audited all 21 skills against Anthropic's published skill-authoring and
model-behavior guidance (fetched live 2026-07-21; findings.md carries the source
URLs). The deterministic census found 17/21 descriptions led with "Use when the user
invokes `minerva:X`" — and the four exceptions (debug, explore, grill-plan,
using-minerva) were precisely the skills observed to ambient-trigger best. Three
descriptions exceeded the platform's 1,024-character frontmatter limit, with their
disambiguation payload in the truncation-risk tail.

## Finding
House style for every skill description, applied to 19 skills in unit 046: written in
third person; **leads with what the skill does plus the ambient/contextual trigger
scenarios** (the situations where no `/command` is typed); the explicit "or when the
user invokes `minerva:X`" clause comes **last**; total length ≤1024 characters;
specific key terms and user phrasings included. Current models weight what leads and
read literally, so invocation-first ordering biases toward slash-command-only firing.

## Implications
New skills follow this style or the ambient-trigger regression returns. The 1,024-char
ceiling is a hard platform limit — text beyond it is at truncation risk, and the tail
is where disambiguation phrases used to sit. This entry paraphrases external guidance
dated 2026-07-21; if Anthropic's guidance changes, supersede this entry (bodies are
append-only) rather than editing it. A mechanical ≤1024 contract test is seeded in
unit 046's followups.md.

## Related
- [[2026-07-21-bug-skill-listing-description-drop]] — see also
- [[2026-06-11-constraint-skill-progressive-disclosure]] — see also
