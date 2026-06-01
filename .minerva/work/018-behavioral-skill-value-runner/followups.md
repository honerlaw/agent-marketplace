# Followups — behavioral-skill-value-runner

## 1. (MANDATORY, FIRST) Live signal-and-control validation spike

Before any per-skill backfill or baseline recording, run a small **live** spike to answer the
two open questions this unit deliberately left unsolved:

- **Is the with-minus-without delta real signal, not noise?** Take 1 skill (e.g. `debug`) and 1
  case, run treatment + control + judge live via `claude -p` **N times each** (e.g. N=5), and
  check whether the delta is separable from run-to-run variance and whether the judge ranks
  consistently.
- **Can the "without skill" control actually suppress one auto-discovered skill** while leaving
  the other 12 available? The current default control is a best-effort stub that does not
  guarantee absence. Determine the real mechanism (isolated fixture repo? a skills-allowlist
  flag? uninstall-in-temp-dir?).

**Output:** a go / no-go. A no-go (delta is noise, or control can't suppress cleanly) **forces a
replan** of the runner — cheap, because `invoke`/`judge` are injectable seams, so the real
methodology drops in without rebuilding the parse/plan/score/report layers. Only after a go does
backfill/baseline work make sense (backfilling against an unvalidated rubric would entrench noise
at scale).

## 2. Per-skill behavioral backfill

Author `evals/<skill>/behavioral.json` value cases for the remaining 11 skills (this unit ships
exemplars for `debug` and `propose` only). Gate behind the spike's go.

## 3. Live baseline recording + regression detection

Once the signal is validated, design the `baseline` field (left unspecified on purpose) from the
shape of real deltas — likely a recorded per-case delta (and/or variance band) that a later run
compares against to flag a *value regression* (a skill that stopped helping). Add a
`--samples N` averaging knob if the spike shows per-run variance warrants it.

## 4. (Optional) Nightly / on-demand harness wiring

If/when the methodology is trusted, wire an on-demand or nightly job (NOT a PR-blocking CI gate)
that runs the behavioral evals and surfaces deltas. Out of scope until after the spike.
