# Proposal: run-context-footprint-estimator

**Date**: 2026-06-12
**Status**: Draft

## Goal

Add a **full-run cumulative context-usage estimator** for the minerva skills: a script (`scripts/skill_footprint.py`, with an importable API per [[021-constraint-skill-wraps-script-via-importable-api]]) that, given an entry skill, transitively resolves everything a complete run pulls into the **main-loop** context — the entry `SKILL.md`, the `references/*.md` files it reads, and the `SKILL.md` + references of every skill it **delegates to** via the `Skill` tool — and reports **token-accurate** counts per file plus a deduplicated run total.

This makes the usage question we could not previously answer mechanical: *"how much context does a full `propose-ship-auto` run actually load, and did a change grow it?"* — the exact regression PR #33's tooling (unit 036) could not see, because `tests/test_skill_budget.py` only caps each core file in isolation.

**Explicitly out of scope** (user-deselected): a generic per-skill static footprint report, and a CI regression gate that fails on budget growth. This unit ships the on-demand estimator and accurate token counting only. (A gate can be layered on the importable API later as its own unit, if wanted.)

## Why

We currently have no way to see **aggregate or per-run** context cost. `tests/test_skill_budget.py` enforces a 9 KB-per-`SKILL.md` floor ([[036-constraint-skill-progressive-disclosure]]) — a *per-file* check that is blind to two things that actually drive run cost:

1. **References that load on demand and persist.** Progressive disclosure (unit 035) shrank the always-resident cores but moved prose into `references/*.md` that a full run reads anyway — so peak per-run context barely moved even though every per-file check passed.
2. **Cross-skill delegation.** Extracting the panel protocol into `minerva:round-table` (unit 033 / PR #29) added a separate `SKILL.md` + `briefs.md` + `caller-mode.md` (~12 KB) that a `propose-ship-auto` run now loads on top of its own `references/panel-protocol.md` — a real per-run increase that was **invisible** to every existing check.

Both are *graph* properties (what a run transitively loads), not *file* properties. An estimator that walks the load graph and counts tokens is the smallest tool that surfaces them.

## Approach

A standalone resolver + reporter, following the existing `scripts/` + importable-API conventions:

**1. Load-graph resolution.** From an entry skill directory, build the set of markdown files that enter the main loop over a complete run, via two transitively-followed edge types:

- **Reference edges** — canonical `references/<name>.md` mentions, reusing the same `REF_MENTION_RE` grammar already in `tests/test_skill_budget.py` (single-source it rather than re-derive, per [[019-constraint-knowledge-span-model-single-sourced]]'s spirit).
- **Delegation edges** — `Skill`-tool invocations of another minerva skill. Detected on the **anchored phrase** pattern (`invoke \`minerva:<skill>\` via the \`Skill\` tool`), *not* any bare `minerva:<name>` mention — because prose lists skills it explicitly does **not** load (e.g. `governance.md`'s "never modify these" roster, `phases.md`'s "do **not** auto-invoke `minerva:propose`"). A bare-mention scan would massively overcount.

Resolution is fence-aware (reuse `FENCE_RE` per [[037-constraint-fence-scans-import-fence-re]]) so fenced examples aren't read as live edges, deduplicates (a file billed once — it persists once read), and detects cycles. Cross-plugin targets that don't resolve under `plugins/minerva/skills/` (e.g. `code-review:code-review`) are reported as **`external (unresolved)`**, never a crash.

**2. Token-accurate counting (layered, degrades gracefully).**

- **Primary:** a local tokenizer (`tiktoken`, `o200k_base`) — dependency-light, offline, close to Claude's tokenization. Counts are labeled *approximate (tiktoken)*.
- **Opt-in exact:** `--exact` uses Anthropic's `client.messages.count_tokens` when `ANTHROPIC_API_KEY` + network are available; labeled *exact (Anthropic API)*.
- **Fallback:** if neither is available, a `bytes / 4` heuristic, clearly labeled *rough (byte heuristic)* so a number is never silently passed off as precise.

The active method is named in every report so a reader never confuses an estimate for a measurement.

**3. Reporting.** A per-file table (path · tokens · edge type that pulled it in) and a **deduplicated run total**, with a separate labeled line for **subagent-only** context — round-table dispatches 3 fresh-context agents whose per-agent briefs are *separate* context windows, not added to the main-loop total. Folding them in would misrepresent main-loop cost; omitting them silently would hide real spend. So they are counted and reported **under their own heading**. Default entry skill is `propose-ship-auto` (the heaviest, most-asked-about run); any skill can be passed.

The script is importable (functions return structured data; the CLI is a thin `__main__` wrapper) so a future CI gate or per-skill report can build on it without re-implementing the resolver.

## Success criteria

- `python3 scripts/skill_footprint.py propose-ship-auto` prints a per-file table and a deduplicated main-loop total, with the active token-counting method named in the output.
- The resolved load set for `propose-ship-auto` **includes** `round-table/SKILL.md`, `round-table/references/briefs.md`, and `round-table/references/caller-mode.md` (proving delegation edges are followed) **and** its own `references/{phases,panel-protocol,governance}.md` (proving reference edges are followed).
- The resolver does **not** include skills that appear only in non-delegation prose (e.g. it does not pull every skill named in `governance.md`'s "never modify" list, nor `minerva:propose` from `phases.md`'s explicit do-not-invoke line).
- Subagent (round-table panel) context is reported under a **separate** heading, not folded into the main-loop total.
- Token counting degrades cleanly across all three tiers: works with `tiktoken` present, with `--exact` + API access, and with neither (byte heuristic) — each run labels which method it used; no tier crashes when its dependency is absent.
- Unresolvable cross-plugin delegations (`code-review:code-review`) are reported as `external (unresolved)`, not errors.
- An importable-API test (`tests/test_skill_footprint.py`) pins the resolver's edge-following and overcounting-avoidance on fixtures; if added to CI it is appended to the enumerated pytest list per [[035-constraint-ci-test-enumeration-explicit]].

## Open Questions

- **Delegation detection precision.** The anchored-phrase pattern is a heuristic over English prose; a future reworded delegation could slip past it. Acceptable for a measurement tool (a missed edge undercounts visibly in the total, and the phrase is consistent across the current corpus) — but worth a knowledge entry if it proves brittle. Should conditional delegations (`ship`→`cleanup` only on `MERGED`; `review`→`code-review` only if a PR exists) be counted as **worst-case loaded** (recommended — the estimator reports the *ceiling*) or flagged **conditional**?
- **Tokenizer choice.** `tiktoken` is an OpenAI tokenizer; it approximates Claude's but isn't identical. Is approximate-but-offline the right default, with `--exact` (Anthropic API) reserved for when a precise number is needed? (Recommended: yes — a regression-spotting tool needs *consistent* counts more than *exact* ones, and offline keeps it usable in CI.)
- **Should this ship with a test wired into CI now**, or stay a pure on-demand script? The user deselected the CI gate; leaning toward shipping the importable-API test but **not** adding a budget-threshold assertion (measurement, not enforcement).
