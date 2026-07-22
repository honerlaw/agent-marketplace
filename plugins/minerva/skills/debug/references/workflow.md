# debug — the three-phase workflow + project-reading protocol

## The three-phase workflow

### Phase 1 — Gather

Collect evidence before forming any diagnosis. This phase produces an evidence ledger, not causal claims. Hypotheses may not appear in Phase 1 output — the output contract is evidence artifacts only.

1. **Restate the symptom in one sentence.** "Search returns 500s for queries containing accents." Not "search is broken." The restatement forces you to name what's actually observed.

2. **Identify the candidate failing layer.** Which subsystem owns the symptom? Which call site does the evidence point at? If you're not sure, plan to pull evidence from multiple plausible layers and let the data pick.

3. **Load relevant project references.** Use the discovery mechanism below to read `.minerva/reference/` files that describe how the failing layer works in this project. Also skim `.minerva/knowledge/` for past learnings — decisions, bugs, patterns, constraints — that match the symptom.

4. **Pull evidence.** Gather concrete artifacts from multiple sources:
   - *Live incidents*: logs, metrics, dashboard panels, runtime state via read-only CLI access, read-only queries against operational stores.
   - *Dev bugs*: reproduce locally, read the failing test or call site, add temporary logging if needed, narrow with a targeted assertion.

5. **Log every piece of evidence to the evidence ledger.** Each entry gets a sequential ID (E1, E2, E3...) and must include:
   - The **tool name** and **parameters** used to obtain it (e.g., `Read: src/search.ts:45-60`, `Bash: npm test -- search.test.ts`, `mcp__grafana__query_loki_logs: {query: ...}`).
   - A **bounded excerpt** of the tool's output — the raw result, not your interpretation. Keep excerpts focused on the relevant lines.
   - The **artifact category** it belongs to (see closed enumeration below).

   Evidence is defined as the literal output of a tool invocation. Agent narration and interpretation are NOT evidence — they can accompany evidence entries as analysis, but they cannot substitute for tool output.

6. **Always check the pattern catalog.** If `.minerva/reference/` contains a `bug-patterns.md`, `incidents.md`, or similarly-named pattern catalog, load it on every debug regardless of symptom — it's a cheap "have we seen this" check. If the symptom matches an entry, name the pattern explicitly.

7. **Minimum-breadth gate.** Do not proceed to Phase 2 until the evidence ledger contains entries from **>=2 distinct artifact categories**. If it does not, continue gathering.

#### Artifact categories (closed enumeration)

| Category | Examples |
|----------|----------|
| Source code | Reading implementation files, function definitions, class hierarchies |
| Error output | Stack traces, exception messages, error logs from a failing process |
| Log output | Application logs, system logs, structured log queries |
| Test output | Test run results, assertion failures, coverage reports |
| Runtime state | Metrics, dashboard panels, process state, memory/CPU, queue depths |
| Configuration | Environment variables, config files, feature flags, secrets presence |
| Version history | Git log, git diff, git blame, recent changes to relevant files |

#### When evidence is unavailable

When a planned evidence source is inaccessible (no access, tool errors, logs don't exist, system is down), record a **failed-attempt entry** in the ledger: what was attempted, why it failed, and what you would need to proceed. Failed attempts do not count toward the breadth gate. Confidence automatically caps at **Suspected** if any planned evidence source was unavailable.

### Phase 2 — Diagnose

Given the evidence ledger from Phase 1, form and test hypotheses. Every causal claim must cite evidence.

1. **Form a hypothesis by citing evidence.** Each hypothesis must reference >=1 evidence ID from the ledger. State what you think is causing the failure and which evidence supports that belief.

2. **Confirm or disconfirm.** Gather more evidence to test the hypothesis — new evidence gets added to the ledger with new IDs. Confirmation methods:
   - Read the call sites the evidence references. Logs name file paths and line numbers. Stack traces name functions. Open them. Walk inward from the entry point.
   - Write a focused repro that isolates the suspected cause.
   - Add a temporary assertion or log line to check runtime behavior.

3. **Identify the offending code.** Be specific: file + line range + what the code does + what it should do.

4. **Iterate.** If the hypothesis is disconfirmed, return to Phase 1 for more evidence gathering. Multiple hypothesis-test cycles are normal and expected.

### Phase 3 — Report

Structure the final reply using this format. Every section is required.

#### 1. Symptom

One-sentence restatement of what's wrong.

#### 2. Inspected Artifacts

What was opened, queried, or run during the investigation — the **scope**. This is the input list: which files were read, which commands were run, which queries were executed, which dashboards were checked. This tells the reader what the investigation covered and, by implication, what it did not.

#### 3. Evidence Ledger

The **findings** from those inspections, each with an ID. Format:

```
E1 [source code] Read: src/search.ts:45-60
   > function normalize(query) { return query.toLowerCase(); }
   > // no unicode normalization — accented chars pass through raw

E2 [error output] Bash: curl -s 'localhost:3000/search?q=café' | jq .error
   > {"error": "invalid byte sequence in UTF-8", "status": 500}

E3 [test output] Bash: npm test -- search.test.ts
   > FAIL src/search.test.ts
   > ✕ handles accented characters (12ms)
   >   Expected: 200, Received: 500
```

#### 4. Root Cause

Every claim in this section must cite evidence IDs in parentheses. Any claim without a citation must be explicitly flagged as **[SPECULATION]** — it is not a finding, it is a guess.

Example: "The `normalize()` function at `src/search.ts:48` passes accented characters through without Unicode normalization (E1), causing a UTF-8 encoding error when the raw bytes hit the search index (E2)."

#### 5. Confidence

Mechanically derived from what was actually done during the investigation. The tier is determined by the highest level whose criteria are **fully** met:

| Tier | Criteria |
|------|----------|
| **Confirmed** | The bug was **reproduced** via a repro script or test (evidence includes test/repro output showing the failure) AND the root cause was **identified in code** (evidence includes the offending source lines). |
| **Probable** | Multiple corroborating evidence artifacts from **different artifact categories** (e.g., error output + source code, log output + configuration). No contradicting evidence found. Root cause identified but not independently reproduced. |
| **Suspected** | Single evidence source only, OR analysis based on code reading alone without runtime evidence. Alternative explanations have not been ruled out. Also the automatic cap when planned evidence sources were unavailable. |
| **Unknown** | Could not narrow to a single cause. Evidence is contradictory, or insufficient evidence was gathered. |

State the tier and the specific evidence that justifies it. Example: "**Confirmed** — reproduced via test (E3), root cause identified in source (E1), confirmed by direct request (E2)."

#### 6. Recommended Fix

What the user should do. Mutating actions go here as suggestions, not as taken actions.

#### 7. What I Did Not Check

Two sub-sections:
- **Ruled out**: plausible causes you actively investigated and eliminated, with the evidence that eliminated them.
- **Not investigated**: plausible causes you did not have time or access to check. Be specific — name the system, file, or layer you would check next.

## Reading the project: knowledge vs. reference

The `.minerva/` directory has two read tiers, and this skill uses both differently:

- **`.minerva/knowledge/`** — atomic, past-tense, durable learnings. Files named `NNN-<type>-<slug>.md` where type is `decision`, `bug`, `constraint`, or `pattern`. Append-only. This is "what we learned" about this project, one concept per file. Debug uses it for "have we seen this symptom before?" pattern matching, and for understanding load-bearing constraints that might explain the failure.

- **`.minerva/reference/`** — thematic, present-tense, operational facts about how the system is configured *right now*. Files named by topic (`topology.md`, `observability.md`, `database.md`, etc.). Replace-on-change. Debug uses it for "how does this layer work in this project?" — the operational map.

The distinction is time-shape: knowledge accumulates; reference snapshots. New durable learnings from a debug go to knowledge via `minerva:promote`. Updates to operational facts overwrite the relevant reference file directly.

## `.minerva/reference/` discovery

The skill cannot bake in project-specific filenames, so reference loading is dynamic:

1. **List first.** `ls .minerva/reference/` to see what exists in this project. Don't read everything blindly.
2. **Symptom-driven selection.** Pick 1-3 files for full read based on filenames + the one-sentence symptom restatement. Filenames are descriptive by convention (`topology.md` for system layout, `observability.md` for logging/metrics conventions, `database.md` for schema and read-only query recipes, etc.) — filename + symptom is enough to pick relevance without reading contents first.
3. **Always load the pattern catalog.** Files matching `bug-patterns.md`, `incidents.md`, `patterns.md`, or similar pattern-catalog names get loaded on every debug regardless of symptom-based selection.

If `.minerva/reference/` doesn't exist or is empty, fall back to reading the codebase directly — the workflow still applies, you just have less project-specific context to lean on.

