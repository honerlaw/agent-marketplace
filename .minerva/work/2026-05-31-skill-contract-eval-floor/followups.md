# Followups — skill-contract-eval-floor

## Unit 2 — behavioral skill-value runner (seeded)

The original request had two halves: skills must **(a) not regress** and **(b) actually add
value**. This unit (017) shipped (a) — the deterministic structural contract floor — and
defined the shared `evals/` format. (b) is the behavioral runner, deliberately sequenced after
the floor per the scope-decomposition decision (see `scratchpad.md` panel decisions).

**What Unit 2 builds:**
- A runner (e.g. `scripts/run_skill_evals.py`) that, per behavioral case, invokes a task
  **with** the skill available and **without** it (control) via `claude -p`, then scores the
  difference with an LLM-as-judge against a rubric. The with-minus-without delta is the
  "value added" signal; a drop vs. a stored baseline is a behavioral regression.
- Behavioral case definitions living in the **reserved `behavioral` namespace** of each
  `evals/<skill>/contract.json` (Unit 2 owns that schema wholesale) — or a sibling
  `evals/<skill>/cases.*` file, whichever the runner's needs favor once they're concrete.
- Exemplar behavioral evals for ~2 representative skills (e.g. `debug`, `propose`) proving the
  with-vs-without measurement end-to-end. Full per-skill backfill is itself a later follow-up.
- `--dry-run` (no API) to validate parsing + run-plan, and stubbed-LLM unit tests so the runner
  is itself deterministically regression-tested. Tier 2 is on-demand, **not** a CI gate
  (non-deterministic + costs API).

**Prior art:** the official `skill-creator` eval pattern (trigger + with/without behavioral via
`claude -p`, LLM-as-judge) — plumbing is established; the open risk is whether the
with-minus-without delta is a stable, meaningful per-skill signal (the reason it was sequenced
as its own unit).

To start it: `minerva:propose` (or `minerva:propose-ship-auto`) with this seed as the brief.
