# Proposal: validate-behavioral-eval-control

**Date**: 2026-08-22
**Status**: Shipped (2026-08-22)
**Closes**: #74

## Goal

Run the mandatory validation spike #74 gates the behavioral-eval program on, and return a
go/no-go. Two questions: can the control suppress one auto-discovered skill, and is the
`treatment − control` delta separable from run-to-run variance.

## Why

`.minerva/knowledge/2026-05-31-decision-behavioral-evals-provisional.md` has blocked
per-skill backfill since May on those two questions. Only 3 of 23 skills have
`behavioral.json` cases, and backfilling against an unvalidated rubric would entrench noise
at scale.

## Approach and findings

### Q1 — control: **GO**

Reading `claude_invoke` answered the first half without an API call. The control was not a
weak control; it was **no control at all** — both arms ran the identical
`["claude", "-p", prompt]` with identical environment, and `skill_available` only chose
whether to print a warning. `treatment − control` compared a configuration against itself,
so every delta the runner had ever reported was noise by construction.

The working mechanism is `--plugin-dir` pointed at a copy of the plugin with the one skill
directory removed. Verified live before implementing:

| arm | probe: is `minerva:debug` listed? |
|---|---|
| `--plugin-dir <full copy>` | `{"debug_listed":true}` |
| `--plugin-dir <copy minus skills/debug>` | `{"debug_listed":false}` (twice) |

**`--bare` is not needed and must be avoided.** It looked like the natural way to isolate
harder, but it skips credential resolution — a nested run under it dies with
`Not logged in`, measured directly. The plugin-dir override alone suppresses.

Implemented as `arm_plugin_dir(skill, skill_available)`, cached per arm so a multi-case run
copies the tree twice rather than per invocation.

### Q2 — signal: **NO-GO at usable N**

`debug` / `stale-cache-incident`, N=4 per arm, real control:

| arm | scores (rubric max 5) | mean | sd | range |
|---|---|---|---|---|
| treatment | 3, 2, 2, 4 | 2.75 | 0.96 | 2–4 |
| control | 2, 3, 2, 2 | 2.25 | 0.50 | 2–3 |

Delta **+0.5**, pooled noise **0.96**, i.e. **0.9 standard errors** — the within-arm spread
is roughly 4x the between-arm difference. Reaching 80% power at this effect size needs
**~59 runs per arm per case**, against the 1 the runner performs.

So: the methodology now measures *something*, and that something is still smaller than the
noise. Backfill stays blocked — the reason changed, the answer did not.

Recommendation, in preference order: **lower the variance rather than raise N** (absolute
rubric scoring by an LLM judge is the dominant noise source; a paired head-to-head judgment
removes judge-scale drift), or raise N and report an interval instead of a point delta.

### The guard caught its own author

The first live run of the new control failed loudly four times:
`cannot build a control arm for 'debug': no skills/debug directory in <repo>`. `PLUGIN_ROOT`
had been derived as `parent.parent` — but this runner lives in `<repo>/scripts/`, not inside
the plugin, so that is the repo root. A control built from it would have removed nothing and
silently reproduced the exact no-op being replaced. Fixed to `REPO_ROOT / "plugins" /
"minerva"` and pinned by a test. The refusal is the design working: the old control degraded
to noise in silence, this one declines to run.

An earlier batch (treatment 5,4,5,4) was collected before that fix and is **excluded** —
its "treatment" arm pointed at the repo root and so was not a valid treatment.

## Success criteria

1. `pytest tests/` passes — **646**, up from 641.
2. The two arms reach `claude -p` with different `--plugin-dir` values, and the control dir
   differs from the treatment dir in exactly the one skill directory. Both asserted.
3. Building a control for a skill that is not present raises rather than returning a copy
   with nothing removed. Asserted.
4. `PLUGIN_ROOT` resolves to a tree containing `skills/` — the bug above cannot return.
5. Restoring the old same-command-both-arms control fails the suite. Verified by mutation.
6. `evals/README.md` and the superseding knowledge entry both state the go/no-go split and
   the ~59-runs-per-arm figure.

## Open questions

- The N=4 estimate of sd is itself imprecise; ~59 is an order-of-magnitude figure, not a
  target to trust to two digits.
- Whether a paired head-to-head judge actually lowers variance enough is untested — it is
  the recommended next experiment, not a validated claim.
