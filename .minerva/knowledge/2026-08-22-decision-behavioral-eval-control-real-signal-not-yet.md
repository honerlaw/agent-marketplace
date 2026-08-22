# Behavioral-eval control is real now; the delta still is not — backfill stays blocked

**Date**: 2026-08-22
**Type**: decision
**Summary**: the suppression control works via `--plugin-dir` minus one skill, but the measured delta (+0.5) sits inside the noise (sd 0.96), so per-skill backfill stays gated

**Context**: .minerva/work/2026-08-22-validate-behavioral-eval-control (see git history if the worktree has been cleaned up)

## Context

[[2026-05-31-decision-behavioral-evals-provisional]] shipped the behavioral tier with two
standing rules — don't CI-gate it, don't trust the deltas — pending a mandatory validation
spike with two questions: can one auto-discovered skill be cleanly suppressed as a control,
and is `treatment − control` separable from run-to-run variance. The spike ran on
2026-08-22 against `debug` / `stale-cache-incident`, N=4 per arm.

## Finding

**The control works, and the old one was worse than "provisional".** `claude_invoke` ran the
**identical** `claude -p` command for both arms — `skill_available` only chose whether to
print a warning. So `treatment − control` compared a configuration against itself, and every
delta the runner ever produced was noise by construction, not merely unvalidated.

The working mechanism is `--plugin-dir` pointed at a copy of the plugin with the one skill
directory removed. Verified live: a presence probe reports the skill under the treatment
dir and absent under the control dir, reproducibly. **`--bare` must not be added** — it
skips credential resolution and the nested run fails "Not logged in"; the plugin-dir
override alone suffices.

**The signal is not separable at usable N.** With a real control:

| arm | scores (max 5) | mean | sd |
|---|---|---|---|
| treatment | 3, 2, 2, 4 | 2.75 | 0.96 |
| control | 2, 3, 2, 2 | 2.25 | 0.50 |

Delta **+0.5** against pooled noise **0.96** — 0.9 standard errors, with the within-arm
spread about 4x the between-arm difference. Reaching 80% power at that effect size needs
**~59 runs per arm per case**, against the 1 the runner performs.

## Implications

**Backfilling `behavioral.json` cases across the skill set stays blocked** — the reason has
changed but the answer has not. It is no longer "the control is fake"; it is "the
measurement is too noisy to support the per-skill claims a backfill would encode". Only 3 of
23 skills have cases, and that is the correct number until this resolves.

Do not read a single-run delta as evidence about a skill. Prefer **lowering the variance
over raising N**: absolute rubric scoring by an LLM judge is the dominant noise source, and
a paired head-to-head judgment ("which transcript better satisfies this rubric?") removes
judge-scale drift. Raising N works too and costs API proportionally.

The don't-CI-gate rule from the superseded entry stands unchanged and for the same reason.

A methodological note worth carrying: the first live run of the new control failed loudly
because `PLUGIN_ROOT` had been derived as `parent.parent`, which is the repo root rather
than the plugin — a control built from it would have removed nothing and silently
reproduced the very no-op it replaced. The guard that refuses to build a control arm when
the target skill directory is absent is what caught it
([[2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state]] is
the sibling lesson: make the degenerate case refuse rather than quietly return something).

## Related
- [[2026-05-31-decision-behavioral-evals-provisional]] — supersedes
- [[2026-05-31-constraint-skill-structural-contracts]] — see also
- [[2026-08-22-pattern-a-distinguished-state-inferred-from-outputs-is-the-steady-state]] — see also
