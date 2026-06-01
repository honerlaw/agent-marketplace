# Scratchpad: behavioral-skill-value-runner

Running log for the work unit. Promoted/archived at `minerva:promote`.

## Panel decisions 2026-05-31

- [3/3 accept, vote 2] scope check: SINGLE unit. Vote 1 = 2/3 (Proponent accept / Skeptic revise: add mandatory Phase-0 live spike / Arbiter accept). Revision: keep single unit, build with INJECTABLE invoke/judge seams, ship deterministically (stubs+dry-run, no live claude -p in completion path), seed the live signal+control validation spike as the MANDATORY FIRST follow-up (not a completion gate — this runs nested in an unattended auto orchestration). Vote 2 = 3/3.
- [3/3 accept, vote 2] approach selection: **A1-clean** — sibling `evals/<skill>/behavioral.json` + FULLY retire Unit 1's reservation. Vote 1 = 2/3 (Proponent accept A1 / Skeptic revise→A2 embed / Arbiter accept A1-clean). Decisive: 017's followups seed pre-authorized the sibling option. Revision folded in: retire reservation cleanly (no dangling contradiction), reserve `baseline` opaque (don't schema now), correct the overstated skill-creator precedent (triggering + variant-vs-variant, NOT present-vs-absent suppression). Vote 2 = 3/3.
- [3/3 accept, vote 2] whole-proposal acceptance. Vote 1 = Proponent accept / Skeptic revise (2 MAJOR gaps). Revision folded in: criterion 7 scoped to the minerva suite (bare pytest interrupts on pre-existing financials `lib` errors); named the conftest import seam for scripts/; reworded criterion 3 (control = documented stub, not solved); enumerated exact reservation-retirement sites (13 contracts + allowed-set + test docstring + inline comment + 4 README spots). Vote 2 = 3/3 (both verified against repo).

## Panel decisions 2026-05-31 (cont.)

- [3/3 accept] completion verification: Proponent / Skeptic / Arbiter all independently reproduced — 89 passed; `--dry-run` zero-API test-proven (monkeypatch executors to raise); retirement test-enforced (adversarial re-injection of `behavioral` reds the floor); delta non-vacuous (stub treatment 4 > control 0); financials `lib` errors pre-exist on main, diff untouched. All 8 criteria honestly met.

## Panel concerns 2026-05-31

(All reflected in proposal Approach/Success criteria.)
- Control suppression (run a task "without" one auto-discovered skill) is UNSOLVED — ships as documented stub; the spike must solve it. Don't cite skill-creator as proof it works.
- `baseline` NOT schema'd now — reserved for the spike.
- Reservation retirement must hit ALL sites incl. test_skill_contracts.py docstring + inline comment + the dangling 017-followups cross-ref in evals/README.md.
- Criterion 7 green = minerva-scoped suite only (financials `lib` collection errors pre-exist on main).

## Review triage 2026-05-31

- [revision applied; Proponent accept / Skeptic revise on the 012 mechanism] triage panel.
- **Finding HIGH [stale knowledge 012] → FIX IN PROMOTE (binding action).** `.minerva/knowledge/012-constraint-skill-structural-contracts.md` lines 13 & 18 still describe the reserved `behavioral` namespace this unit retired. Per minerva convention `.minerva/knowledge/` writes belong to `minerva:promote` (Phase 4), not review. **BINDING PROMOTE ACTION:** in Phase 4, update 012 lines 13 & 18 to drop the behavioral-namespace mention and instead state that behavioral value evals live in the sibling `evals/<skill>/behavioral.json` read by `scripts/run_skill_evals.py`. Must land before ship.
- **Finding MEDIUM [robustness] → FIX (done).** `claude_invoke`/`claude_judge` now fail loud: raise on non-zero `returncode`, guard `json.loads` with a clear error, and reject a non-numeric judge `score` — prevents a silently-empty transcript from fabricating a value-delta. (Live path only; tests inject stubs, suite unaffected.)
- **Finding LOW [dead field] → FIX (done).** Added a comment marking `Case.files` as reserved/not-yet-wired (consumed by the spike).
- Other dimensions clean (deterministic core, spec fidelity, reuse, maintainability). No load-bearing divergence → no replan.

## Implementation log

(work begins below)
