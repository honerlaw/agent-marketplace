# The agent-file Routing section is the wiki's reading protocol; stale sections get a gated refresh with markers derived from the template-of-record

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/2026-06-03-init-routing-wiki-protocol (see git history if the worktree has been cleaned up)

## Context

The wiki's layered structure (overview → index → entries; reference tier) was built to
give an LLM a cheap, structured entry point — but the `## minerva` Routing section that
*directs* the LLM on session start (and after compaction) predated it. init's
deliberately-lenient detection ([[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]])
never revisits an existing section, so every already-initialized repo was permanently
stale; init's own out-of-scope had explicitly deferred a refresh path ("--refresh mode …
out of scope for v1").

## Decision

**The Routing section is the wiki's consumer-facing API — it teaches the reading
protocol**, not just the directory layout: `overview.md` first (theme synthesis; the
bullet notes it is absent until `minerva:synthesize` first runs → fall back to the
index), `index.md` for catalog lookup, entries on demand via `[[NNN-type-slug]]` links,
`.minerva/reference/` for present-tense operational docs, `.minerva/work/` for historical
reasoning. The bullets stay terse and verb-led — the Routing section *routes*; the
methodology lives in `minerva:using-minerva`.

**Stale sections get a gated refresh offer in init's idempotent mode** (the v1 deferral
is discharged as an in-flow offer, not a flag):

- **Staleness markers are derived from the template-of-record, never hardcoded** — the
  section is stale if it is missing *any* of the current template's `.minerva/...`
  path-bullet substrings. A hardcoded marker list would rot exactly the way the template
  itself did. Note the quantifier asymmetry: *detection* (is a section present?) is a
  conjunction of both signals; *staleness* (is the present section complete?) is a
  disjunction over the markers.
- **User-territory mutation posture:** whole-section replace (bounded `## minerva` →
  next `^## ` line or EOF; a `### ` subsection does not terminate), behind a gate that
  shows the full before/after diff and names the possibility of customization ("…or you
  may have customized it — anything custom inside it will be removed"). Never automatic;
  declining keeps the old section. Splice-preserving refresh is recorded future
  hardening.

**Detection arithmetic stays in sync per 001:** the new template's first
`.minerva/knowledge/`-bearing line (the `overview.md` bullet — its *path* carries the
substring) is the 4th line after the heading, inside the existing 6-line window — no
widening. Any future template edit must re-verify this count.

## Implications

- When the Routing template next changes, three things move together: the template, the
  detection-window arithmetic (001), and *nothing else* — the staleness markers update
  automatically because they derive from the template.
- The "derive the check from the artifact-of-record" pattern is the general anti-rot
  move: a checker hardcoding a snapshot of the thing it checks goes stale with it.
- An LLM starting work in a minerva repo should follow the Routing protocol literally:
  overview first, index for lookup, entries on demand — not a wholesale corpus read.
- init never scaffolds an `overview.md` stub ([[2026-06-03-decision-synthesis-layer-separate-file-advisory]]:
  synthesize owns that file); the template's parenthetical handles the fresh-scaffold gap.

## Related
- [[2026-05-19-decision-init-routing-detection-accepts-old-and-new-names]] — builds on
- [[2026-06-03-decision-synthesis-layer-separate-file-advisory]] — see also
- [[2026-06-02-decision-knowledge-wiki-navigability-layer]] — see also
