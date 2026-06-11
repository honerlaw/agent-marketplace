# Scratchpad: minerva-static-site

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-10

- [skipped — small] scope check: single additive unit (evidence: all output confined to a new `site/` dir + one new test + one workflow line; no existing file rewritten; no contract surface; decomposition has no plausible seam)
- [1/3 accept → revision] approach selection v1: plain hand-authored site (A) failed 3/3 quorum — Skeptic+Arbiter demanded drift DETECTION via the existing 012 enumerating-test pattern instead of comment-nudge-only (A) or generation (B)
- [3/3 accept] approach selection v2: A′ = hand-authored site + bidirectional drift pytest; binding constraints: delimited catalog section w/ explicit end marker, import `_present` (never reimplement token matching), bidirectional check, pytest+pyyaml only, no hardcoded count, "Actions workflow" wording, no drift-proof claims
- [1/3 accept → revision] whole-proposal v1: criterion "no other repo file modified" unsatisfiable under the lifecycle's own writes; 010-staleness fix had to take the 016-compliant form (new entry + Related-span link, NOT the Skeptic's body-append suggestion — promote-invariant test forbids it); external-ref criterion missed CSS vectors; markers unpinned
- [3/3 accept] whole-proposal v2: revised draft accepted; binding execution notes: (1) dependency wording = "pytest + pyyaml, no new deps", (2) promote entry phrases itself as EXTENDING 010, (3) promote entry records why the site is not a SURFACE_FILES/cross_surface surface (19 contract.json edits would violate file-touch criterion; bespoke bidirectional test is stronger)

## Work notes 2026-06-10

- Site built per A′: parchment/ledger editorial design (system font stacks only — web fonts impossible under the no-external-resources criterion); sections problems / record hierarchy / flow stations / delimited catalog / bias ledger / colophon footer.
- Catalog entries grouped lifecycle/orchestrators/utilities inside the markers (grouping is invisible to the test; both directions scan the whole delimited region).
- Dependency wording per execution note 1: "pytest + pyyaml, no new deps" (the `_present` import transitively imports yaml).
- Verified: 9-file suite 179 passed; single http(s) occurrence is the navigational repo link; no "19" in prose; HTML tag balance clean; file-touch set = site/ + test + one workflow line + lifecycle docs.

- [3/3 accept] completion verification: all six criteria independently reproduced (fault-injection on markers fails loudly; 5 negative-path mutations verified on /tmp copies; protocol-relative + CSS vectors clean; 179/179); four prose-accuracy concerns bound as review FIX items
- [panel-derived triage] review: dispositions inherited from the completion panel's binding (FIX: ship-entry provenance — fixed the stronger way, entry rewritten to frontmatter-faithful text; lone-dissent claim scoped to the unanimity tier; "read-only companions" reworded to include gates; synthesize entry gates only the write. IGNORE: str.index duplicate-marker hardening — test-infra outside this unit's page-edit scope; anomalous grep rendering — disproven at byte level). Re-verified post-fix: 179 passed, single permitted http occurrence.

- [3/3 accept] promote partition: PROMOTE knowledge 034 (fourth catalog surface, extends 010), MERGE work notes → Approach rewrite, DISCARD panel logs, TODO → followups.md. Binding notes: Approach rewrite preserves all three rejections incl. comment-nudge-only; P1 scopes bidirectionality to the site surface; Related links to 010 AND 012 with reciprocals; str.index hardening carried as a followups line; 034's index line disambiguates "fourth, extending 010".
- [skipped — small] TODO disposition: single unambiguous destination, followups.md (evidence: proposal-named follow-up; ratified inside the 2/3 partition vote; one additive file)

## Panel concerns 2026-06-10

- (low, logged) external-resource enumeration omits object/embed/SVG-use/fetch — the grep-every-http(s) clause is the operative verifier and subsumes them
- (low, logged) pinned opening marker embeds an em dash and the test path; loud assertion failure is the designed mode if reworded
- (low, logged) site intentionally unlinked from READMEs this unit — follow-up: link it (and optionally wire a Pages Actions workflow) in a later unit
