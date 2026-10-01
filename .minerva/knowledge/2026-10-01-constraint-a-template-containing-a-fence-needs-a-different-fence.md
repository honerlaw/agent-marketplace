# A markdown template that contains a code fence must be fenced with a different delimiter

**Date**: 2026-10-01
**Type**: constraint
**Theme**: skills-and-catalogs
**Summary**: a ``` block inside a ```-fenced template closes it early; fence the template with ~~~
**Context**: .minerva/work/2026-10-01-derive-knowledge-aggregates

## Context
`minerva:init`'s Routing template lives in `skills/init/references/steps.md` inside a
```` ```markdown ```` fence, and init copies it verbatim into consumers' `CLAUDE.md` /
`AGENTS.md`. 3.0 put a ```` ```sh ```` block inside the template (the catalog one-liner).
In CommonMark a closing fence may be indented up to three spaces, so the inner block's
indented ```` ``` ```` line *closes the outer fence*: the rest of the template renders as
document prose, and any reader that extracts "the fenced template" gets a truncated one.

## Finding
**A template that contains a fence must be fenced with a delimiter it does not contain** —
`~~~markdown` around a body that uses ```` ``` ````, or a longer backtick run (```` ```` ````).
The template is now fenced with `~~~`, and `tests/test_knowledge_catalog.py` extracts it
with a `~~~markdown … ~~~` match. minerva's own fence scanners (`knowledge_spans.FENCE_RE`)
toggle on either delimiter, so a nested pair still nets out even; CommonMark renderers and
the extraction regex are what break.

## Implications
- When adding a code block to any fenced template in a skill (Routing section, proposal
  template, entry template), check the outer delimiter first.
- An extraction test that reads a template must anchor on the outer delimiter, or it will
  silently read the truncated span.

## Related
- [[2026-05-21-constraint-minerva-skill-catalog-sync]] — see also: another hand-maintained surface skills copy into consumers
