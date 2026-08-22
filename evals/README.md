# Skill evals

This directory holds the **eval definitions** for the minerva skills. Each skill
under `plugins/minerva/skills/<name>/` has a companion `evals/<name>/` directory.

There are two tiers of evaluation, each with its own file:

| Tier | File | What it checks | Runner | Determinism |
|------|------|----------------|--------|-------------|
| Structural contract | `evals/<skill>/contract.json` | The SKILL.md still carries its required frontmatter, body anchors, and catalog references | `tests/test_skill_contracts.py` (pytest) | Deterministic — the regression floor |
| Behavioral value | `evals/<skill>/behavioral.json` | Does invoking the skill produce a materially better outcome than not? | `scripts/run_skill_evals.py` | Non-deterministic, LLM-judged — **on-demand, not a CI gate** |

The two files are independent: the structural floor never reads `behavioral.json`, and the
behavioral runner never reads `contract.json`.

## `contract.json` — structural contract format

```jsonc
{
  "skill": "propose",                  // must equal the directory name
  "frontmatter": {
    "required_keys": ["name", "description"],
    "values": { "name": "propose" },   // exact-match constraints (optional)
    "non_empty": ["description"],       // keys whose value must be truthy (optional)
    "contains": [".minerva"]            // raw substrings the frontmatter block must contain (optional)
  },
  "anchors": [                          // substrings the SKILL.md *body* must contain
    "proposal.md",                      //   plain string  -> must-contain, case-sensitive
    { "any_of": ["brainstorm", "questions one at a time"], "ignore_case": true },
                                        //   object        -> disjunction; ignore_case folds case for the whole group
    { "any_of": ["git worktree add"], "file": "references/on-approval.md" }
                                        //   file          -> check a reference file instead of the SKILL.md body
  ],
  "cross_surface": {                    // which catalogs must list `minerva:<skill>`
    "root_readme": true,                //   README.md
    "plugin_readme": true,              //   plugins/minerva/README.md
    "using_minerva_body": true          //   using-minerva/SKILL.md body
  }
}
```

### Anchors

An anchor is **either**:

- a **plain string** — must appear verbatim in the body (case-sensitive); or
- an **object** `{"any_of": [...], "ignore_case": <bool>}` — at least one alternative must
  appear. `ignore_case: true` folds case for every alternative in the group, which is how the
  legacy `... in body.lower()` checks are represented. To express a **case-insensitive single
  anchor**, use a one-element `any_of`: `{"any_of": ["Root cause"], "ignore_case": true}` —
  there is no `ignore_case` flag on plain-string anchors.

An object anchor may additionally carry `"file": "references/<name>.md"` — the anchor is then
checked against that file (path relative to the skill directory) instead of the SKILL.md body.
This is the **deliberate-retarget** mechanism from work unit 035 (skill-progressive-disclosure):
when anchored prose moves verbatim from a fat SKILL.md into an on-demand `references/` file, the
contract follows it via `file` rather than being weakened or deleted. The target file must exist
(the runner fails on a dangling `file`), and a plain-string anchor that needs retargeting becomes
a one-element `any_of` with `file`, since plain strings carry no fields. Companion guards live in
`tests/test_skill_budget.py`: every SKILL.md stays ≤9 KB, every `references/*.md` is pointed to
from its SKILL.md, and every `references/` mention resolves.

A `minerva:<skill>` anchor (or cross-surface token) is matched on a **token boundary**, so
`minerva:propose` is not satisfied by `minerva:propose-ship` — a dropped catalog row can't hide
behind a longer sibling token.

Anchors are deliberately structural string matches, not behavioral assertions — they catch
"the protocol text that made this skill load-bearing was deleted." Measuring whether the skill
actually *helps* is the behavioral tier's job.

### `cross_surface`

minerva keeps its skill catalog synced across surfaces (knowledge constraint
`010-constraint-minerva-skill-catalog-sync`). A skill's `cross_surface` block declares which
catalogs must contain its `minerva:<skill>` token. **Exception:** `using-minerva` sets
`using_minerva_body: false` — its own decision matrix lists every *other* skill but not itself
(self-reference is circular).

## The runner

`tests/test_skill_contracts.py` **enumerates** every skill directory under
`plugins/minerva/skills/` and **fails if any one of them lacks a `contract.json`** — so a newly
added skill cannot slip through with no contract. It parses each SKILL.md's frontmatter with
`yaml.safe_load`, then validates the frontmatter, anchors, and cross-surface references per
skill.

Run it:

```bash
python3 -m pytest tests/test_skill_contracts.py -q
```

### Adding a skill

1. Create `plugins/minerva/skills/<name>/SKILL.md`.
2. Add `<name>` to the catalogs (root README, plugin README, using-minerva matrix) per the
   catalog-sync constraint.
3. Create `evals/<name>/contract.json` declaring its contract. The runner fails until you do.
4. Optionally add `evals/<name>/behavioral.json` with value cases (below).

## `behavioral.json` — behavioral value format

```jsonc
{
  "skill": "debug",                       // must equal the directory name
  "cases": [
    {
      "id": "stale-cache-incident",       // unique within the file
      "prompt": "Users report ...",       // the task to run with vs without the skill
      "files": ["path/to/fixture"],       // optional input files
      "rubric": [                         // criteria the LLM-as-judge scores (1 point each)
        "Restates the symptom before diagnosing",
        "Gathers evidence before asserting a cause"
      ]
    }
  ]
}
```

There is **no `baseline` field yet** — recording live deltas as a regression baseline is
deferred to the validation spike (below), which will learn its shape from real runs rather than
guessing it now.

### Running behavioral evals

```bash
python3 scripts/run_skill_evals.py --dry-run --skill debug   # validate + print run plan, zero API
python3 scripts/run_skill_evals.py --skill debug             # live: costs API, non-deterministic
python3 scripts/run_skill_evals.py --out report.json         # all skills → JSON + markdown
```

Per case the runner plans three steps — **treatment** (skill available), **control** (skill
suppressed), and **judge** — then reports `treatment - control` as the per-case "value-added"
delta. `--dry-run` only parses and prints the plan; it makes no API calls.

### The validation spike has run — control GO, signal NO-GO

Live spike, 2026-08-22, `debug` / `stale-cache-incident`, N=4 per arm.

**The control works now (was: a stub that suppressed nothing).** A single skill is suppressed
by pointing `--plugin-dir` at a copy of the plugin with that one skill directory removed.
Verified: a presence probe returns the skill under the treatment dir and absent under the
control dir, reproducibly. Do **not** add `--bare` to isolate harder — it skips credential
resolution and the nested run dies with "Not logged in" (measured).

What shipped before was worse than a stub: `claude_invoke` ran the **identical** command for
both arms and only printed a warning, so `treatment - control` compared a configuration
against itself. Every delta it ever reported was run-to-run noise, by construction.

**The signal is not yet separable from noise.** With a real control:

| arm | scores (rubric max 5) | mean | stdev |
|---|---|---|---|
| treatment | 3, 2, 2, 4 | 2.75 | 0.96 |
| control | 2, 3, 2, 2 | 2.25 | 0.50 |

Delta **+0.5**, pooled noise **0.96** — the within-arm swing is ~4x the between-arm
difference, and the delta is 0.9 standard errors. Not significant, not usable.

**Therefore: do not backfill per-skill cases yet, and do not read a single-run delta as
evidence about a skill.** At the observed effect size and variance, ~**59 runs per arm per
case** would be needed for 80% power — against the 1 run per arm the runner does today.

Two ways forward, in preference order:
1. **Lower the variance rather than raise N.** Absolute rubric scoring by an LLM judge is the
   dominant noise source. A paired head-to-head judgment ("which transcript better satisfies
   this rubric?") removes judge-scale drift and typically needs far fewer runs.
2. **Raise N** per case and report a confidence interval instead of a point delta, accepting
   the API cost.

Judge calibration remains unproven independently of the above.

The cited prior art (`skill-creator`) does skill **triggering** and **variant-vs-variant**
blind comparison — **not** present-vs-absent suppression, which is why the control had to be
built rather than borrowed.

The runner's own logic (parsing, planning, scoring, reporting) is deterministically
regression-tested in `tests/test_skill_evals.py` with stubbed LLM calls — only the live
`claude -p` execution is non-deterministic, which is why this tier is on-demand, never a CI gate.
