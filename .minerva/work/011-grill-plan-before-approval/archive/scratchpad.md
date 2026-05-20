# Scratchpad: grill-plan-before-approval

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Review finding 2026-05-20

- grill-plan/SKILL.md:35 (Protocol section 6, termination conditions): third bullet "The user explicitly approves the current state" risks being misread as the formal per-section approval that the Out-of-scope section disclaims. Consider sharpening to "The user signals the draft is good enough to proceed (separate from the per-section approval the caller runs next)" or similar. Reader-clarity tweak, not a behavior bug.

## Review triage 2026-05-20

- [SUGGESTED] #1 low grill-plan/SKILL.md:35 — termination bullet wording clarity (logged above)
- [IGNORED]   #2 low propose/SKILL.md:34 — internal-draft requirement is intentional per Approach step 1
