# Skill evals

This directory holds the **eval definitions** for the minerva skills. Each skill
under `plugins/minerva/skills/<name>/` has a companion `evals/<name>/` directory.

There are two tiers of evaluation. **Only the structural tier exists today**; the
behavioral tier is a sequenced follow-up (see [Reserved: `behavioral`](#reserved-behavioral)).

| Tier | File | What it checks | Runner | Determinism |
|------|------|----------------|--------|-------------|
| Structural contract | `evals/<skill>/contract.json` | The SKILL.md still carries its required frontmatter, body anchors, and catalog references | `tests/test_skill_contracts.py` (pytest) | Deterministic — the regression floor |
| Behavioral value *(future)* | `contract.json` → `behavioral` key | Does invoking the skill produce a materially better outcome than not? | *(Unit 2 — not yet built)* | Non-deterministic, LLM-judged |

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
    { "any_of": ["brainstorm", "questions one at a time"], "ignore_case": true }
                                        //   object        -> disjunction; ignore_case folds case for the whole group
  ],
  "cross_surface": {                    // which catalogs must list `minerva:<skill>`
    "root_readme": true,                //   README.md
    "plugin_readme": true,              //   plugins/minerva/README.md
    "using_minerva_body": true          //   using-minerva/SKILL.md body
  },
  "behavioral": {}                      // RESERVED — owned by the Unit 2 runner (see below)
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

## Reserved: `behavioral`

The `behavioral` key in every `contract.json` is **reserved for a future behavioral-eval
runner (Unit 2)** and is intentionally left as an empty, opaque object. Unit 2 will measure
whether a skill *adds value* — running a task with the skill available vs. without (a control),
and judging the difference. That runner owns the `behavioral` schema wholesale; the structural
floor here ignores the key's contents. No behavioral fields are designed yet, on purpose:
freezing the schema before its only consumer exists would be a guess. See the work unit
`017-skill-contract-eval-floor` `followups.md` for the Unit 2 seed.
