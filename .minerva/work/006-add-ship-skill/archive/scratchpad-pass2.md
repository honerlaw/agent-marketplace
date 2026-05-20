Summarized at minerva:promote on 2026-05-19 — see archive/.

## Review finding 2026-05-19

- Review fix: plugins/minerva/skills/ship/SKILL.md — added explicit `gh pr view` check at the top of Push & open PR so re-running ship on a branch with an existing OPEN PR reuses it instead of erroring on `gh pr create`. The Idempotency section was claiming this behavior; now the protocol actually does it.
- Review fix: plugins/minerva/skills/ship/SKILL.md — lifted default-branch detection (origin/HEAD → main → master) into a dedicated section resolved once and reused, instead of repeating the rule inside Branch creation and leaving Pre-flight to reference "the default branch" without a definition.
- Review fix: plugins/minerva/skills/ship/SKILL.md — noted that a post-`minerva:promote` scratchpad (the one-line marker) is the canonical state and the commit message should fall back to `## Goal` + filenames in that case. Avoids the implicit silent fallback.
