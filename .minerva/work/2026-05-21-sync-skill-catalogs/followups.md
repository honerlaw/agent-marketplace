# Follow-ups: 013-sync-skill-catalogs

Items deferred from the original work unit. Not committed work — read these as "consider next time the trigger fires."

## Drift-prevention automation for minerva skill catalogs

**Status**: deferred (followup, not a proposal seed).

**Trigger to revisit**: next observed catalog drift in any context (review, work, ad-hoc, or external report) on minerva-plugin work. The HTML-comment convention reminders added in 013 are the interim mitigation; if drift still slips through despite them, the convention is insufficient and automation becomes the cheaper option.

**Why followup, not seed**: drift is rare (third occurrence over the plugin's lifetime as of 2026-05-21) and cheap to fix manually. Building automation now would pay recurring infrastructure cost (script, CI wiring, false-positive triage) against a problem that recurs every few weeks and is currently absorbed by manual review. Seed only if frequency rises and the comment-based convention fails.

**Likely shape when promoted**: a small `scripts/check-skill-catalog.sh` (e.g.) that diffs `ls plugins/minerva/skills/` against the row sets in each of the three catalog surfaces (`plugins/minerva/README.md` skills table, `plugins/minerva/skills/using-minerva/SKILL.md` decision matrix, top-level `README.md` plugins-table minerva cell) and fails if any skill is missing. Run from CI or a pre-commit hook. Constraint to honor: the marketplace is "pure markdown, no Python deps, no build step" per the install README — shell-only is preferred. See [[2026-05-21-constraint-minerva-skill-catalog-sync]] for the rules the script would enforce.
