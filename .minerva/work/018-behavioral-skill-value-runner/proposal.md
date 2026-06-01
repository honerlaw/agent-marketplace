# Proposal: behavioral-skill-value-runner

**Date**: 2026-05-31
**Status**: Shipped (2026-05-31)

> **Unit 2 of 2.** Unit 1 (`017-skill-contract-eval-floor`, shipped) built the deterministic
> structural *don't-regress* floor and the shared `evals/` format. This unit builds the
> behavioral *adds-value* half: a runner that measures whether invoking a skill produces a
> materially better outcome than not.

## Goal

Build the behavioral skill-value runner — a mechanism that, for declarative behavioral eval
cases, runs a task **with** a skill available and **without** it (control) via `claude -p`,
judges both transcripts with an LLM-as-judge rubric, and reports the with-minus-without
"value-added" delta. Ship: the runner + the sibling `evals/<skill>/behavioral.json` case format
+ exemplar cases for `debug` and `propose` + `--dry-run` + stubbed-LLM unit tests. **Completion
is deterministic — no live `claude -p` in the completion path.** On-demand, **not** a CI gate.

## Why

The user's headline ask — do the skills *actually add value* — is only answerable
behaviorally: does invoking the skill produce a materially better outcome than not having it? A
**with-vs-without control** isolates the skill's contribution; an LLM-as-judge rubric quantifies
it as a per-case delta. This lets skill edits be judged on evidence (the delta moved) and
catches value regressions (a skill that stopped helping).

**Honest caveat — the methodology is provisional.** Whether the with-minus-without delta is a
stable, meaningful per-skill signal is **unvalidated**. This unit builds the *measurement
mechanism* and makes that question empirically answerable; it does **not** claim the signal is
proven. The genuinely unsolved sub-problem — cleanly suppressing one auto-discovered skill as a
control without disturbing the other 12, plus rubric calibration — is scoped to a **mandatory
first-follow-up validation spike**. The cited prior art (`skill-creator`) does skill *triggering*
and *variant-vs-variant* blind comparison, **not** present-vs-absent suppression, so the control
is an unsolved problem, not a known pattern to wire up.

## Approach (sibling file + retire the reservation)

### Case format — sibling `evals/<skill>/behavioral.json`
```json
{ "skill": "<name>", "cases": [ { "id": "...", "prompt": "...", "files": ["..."], "rubric": ["criterion", "..."] } ] }
```
The runner reads this sibling file. **`baseline` is intentionally NOT in the schema yet** — left
unspecified, to be populated by the validation spike once real deltas reveal its shape (mirrors
Unit 1's reserve-don't-guess discipline). `files` is optional.

### Retire Unit 1's behavioral reservation cleanly
Unit 1 reserved an opaque `behavioral` key inside `contract.json`; 017's `followups.md`
**pre-authorized** the sibling-file alternative ("...or a sibling `evals/<skill>/cases.*` file,
whichever the runner's needs favor"). Unit 2, the sole consumer, takes the sibling and retires
the embedded reservation so there is no dangling two-places-to-look contradiction. Verifiable
site-by-site:
- Strip `"behavioral": {}` from all **13** `evals/<skill>/contract.json`.
- Remove `behavioral` from `tests/test_skill_contracts.py`'s `allowed` keys set **and** from its
  module docstring **and** its inline `behavioral`-namespace comment. (Dropping it from `allowed`
  makes the strip **test-enforced** — any leftover key reds the structural floor.)
- Repoint/remove every `evals/README.md` reference: the tier-table row, the JSONC schema comment,
  the `## Reserved: behavioral` section, and the dangling `017-followups` cross-reference. The
  sibling `behavioral.json` becomes the single documented home.

This supersedes 017's seed framing that "Unit 2 owns the `behavioral` schema wholesale" — the
seed offered the sibling as an explicit option; Unit 2 takes it.

### Runner — `scripts/run_skill_evals.py`
Layered, so the deterministic parts are testable without API:
1. **parse** `behavioral.json` → validated case list.
2. **plan** → per case, a run plan of three steps: treatment (skill available), control (skill
   suppressed), judge.
3. **execute** via **injectable** `invoke(prompt, skill_available) -> transcript` and
   `judge(prompt, transcript, rubric) -> score`. In production these shell out to `claude -p`;
   tests inject stubs. The "without-skill" **control ships as a documented best-effort/stub** —
   clean single-skill suppression is the deferred spike's job; the control path is **present and
   exercised** by `--dry-run` and the stubbed tests, never silently absent.
4. **score** → per-case delta = treatment_score − control_score.
5. **report** → `eval-report.json` + a markdown summary.

Flags: `--dry-run` (validate parse + emit run plan, **zero API**), `--skill <name>`, `--out <path>`.

### Test import seam
`scripts/` is not importable today (`conftest.py` only wires `plugins/financials/scripts`). Add a
`sys.path` insert for `scripts/` to the existing `conftest.py` (mirroring that wiring) so
`tests/test_skill_evals.py` can import the runner module and inject stub `invoke`/`judge`.

### Tests — `tests/test_skill_evals.py`
Unit-test parse / plan / delta-scoring / report rendering with **stubbed** `invoke`/`judge` —
deterministic, no live API. Plus a check that the runner's `--dry-run` plan is well-formed and
that the control step is present in every case's plan.

### Docs — `evals/README.md` Tier-2 section
Document the sibling case format, the run + `--dry-run` commands, the with/without methodology
marked **PROVISIONAL**, the **corrected** `skill-creator` precedent, and the
on-demand / not-a-CI-gate / costs-API caveat.

### Scope guard
Ship: runner + 2 exemplar skills + `--dry-run` + stubbed tests + reservation retirement. **Defer**:
full per-skill backfill, live baseline recording, and solving the control-suppression problem —
the last is the **mandatory first follow-up** validation spike.

## Success criteria

1. The `evals/<skill>/behavioral.json` format is documented in `evals/README.md`; exemplar cases
   for `debug` and `propose` exist and parse cleanly.
2. `scripts/run_skill_evals.py --dry-run` runs with **zero API** and emits a valid per-case run
   plan (treatment + control + judge) for the selected skill(s).
3. The runner **wires** treatment / control / judge as **injectable** seams; the "without-skill"
   control ships as a documented best-effort/stub (clean suppression = deferred spike), **present
   and exercised** by `--dry-run` + stubbed tests, not silently absent; it computes a per-case
   delta and renders a JSON + markdown report.
4. `tests/test_skill_evals.py` unit-tests parse / plan / score / report with **stubbed** LLM calls
   — all green, no live API.
5. Unit 1's behavioral reservation is **fully retired**, site-by-site: `behavioral` stripped from
   all 13 `contract.json`; removed from `test_skill_contracts.py`'s `allowed` set **and** module
   docstring **and** inline comment; every `evals/README.md` reference repointed/removed (tier
   row, JSONC comment, `## Reserved` section, dangling 017-followups cross-ref).
   `test_skill_contracts.py` stays green.
6. `evals/README.md` Tier-2 marks the value-delta methodology **PROVISIONAL**, corrects the
   `skill-creator` precedent, and states the on-demand/not-a-CI-gate caveat. `baseline` is **not**
   schema'd.
7. The minerva-scoped suite is green:
   `python3 -m pytest tests/test_skill_contracts.py tests/test_minerva.py tests/test_skill_evals.py`.
   The pre-existing financials collection errors (`No module named 'lib'`) on `main` are out of
   scope, exactly as Unit 1 scoped it.
8. `followups.md` records the **mandatory first follow-up** (live signal-and-control validation
   spike: 1 skill / 1 case / N runs, go/no-go that can force a runner replan), then per-skill
   backfill + live baseline recording.

## Open Questions

- **Multi-sample per case** — a `--samples N` knob to average over `claude -p` non-determinism?
  *Lean: support the knob, default 1; full variance analysis is follow-up.* Non-load-bearing.
- **Report markdown shape** — exact table columns. Non-load-bearing; resolved during work.
