# Claude Code and Codex compatibility

Version 3.0.0 packages one canonical `skills/` tree for Claude Code and local
Codex app, CLI, and IDE conversations. Codex cloud and external scheduling are
outside this release. Git, Python 3.11+, and a POSIX shell are required. GitHub
operations require authenticated `gh`, repository permissions, and normal host
approvals. Skills do not bypass those approvals.

## Capabilities

| Operation | Claude Code | Local Codex |
| --- | --- | --- |
| Load another skill | `Skill`, original arguments | Available loader, or read the installed skill and references in the current agent |
| Required user decision | Available question tool | Available question tool in the appropriate mode, or direct question |
| Panel / single reviewer | Fresh `Agent`, synchronous results, `model: sonnet` | Fresh-context native subagent API, inherit session model, await results |
| Code review | Optional PR review skill, otherwise independent diff reviewer | Optional PR review skill, otherwise independent fetched-PR/local-diff reviewer |
| CI watcher | Tracked background completion when supported | Tracked shell process and polling while the session is active |
| Scheduled re-entry | Only when an actual scheduler is exposed | Only when an actual scheduler is exposed |
| Missing scheduler | Save checkpoint; report pending and exact manual resume | Same |
| Peer discovery | Genuine authorized peer integration, project/liveness filters | Skip child-agent lists; genuine authorized peer integration only |

Every skill requires the shared [runtime contract](skills/using-minerva/references/runtime.md)
and its applicable [Claude](skills/using-minerva/references/claude.md) or
[Codex](skills/using-minerva/references/codex.md) adapter. Missing fresh-context
delegation blocks panel/review workflows with recovery instructions. The author
cannot substitute self-review for an independent gate.

## State and upgrades

Helper paths derive from the loaded package, resolve symlinks, and reject stale
or incomplete script directories. No consumer-project `scripts/` fallback or
host cache search remains. Explicit `MINERVA_SCRIPTS` overrides must be complete.
Each shell helper call supplies installed root and skill path anew.

Lifecycle state is untracked, versioned JSON under the Git common directory:
`minerva/runtime/<unit>/run.json`. It survives worktree removal. Reads do not
create files; writes use a per-unit lock, revision check, and atomic replacement.
Caller, original branch/work PR, consumed counters, and an established cleanup deadline
survive resumes. State is progress evidence, never permission. Live Git/PR
identity is checked again before continuation. Corrupt or unknown-version state
requires recovery rather than an automatic reset.

CI fixes consume an attempt before execution and stop at 3. Cleanup merge waits
stop at 12 retries or the original one-hour deadline, whichever comes first.
Completion requires live merge evidence; a completed checkpoint
must be explicitly cleared before an independent new run. The next declared
phase uses `write --start-phase`, renewing only phase-local CI/merge budgets while
retaining aggregate escalation, decision, and reviewer counts. Standalone resume prompts never
invent `--yes` authorization.

```bash
./install.sh minerva --host both --dry-run
./install.sh minerva --host both
```

The installer preserves unrelated settings, marketplaces, plugin registrations,
and project-scoped entries. Real directory conflicts and malformed config stop
before registration changes. Codex registration uses the supported CLI. If it
fails after Claude succeeds, the error reports partial success and the retry
command. Reload Claude plugins and start a new Codex conversation after updates.
Existing host-neutral routing remains; legacy Claude-only routing gets an
offered, diffed refresh through `minerva:init`.

## Upgrading to 3.0

3.0 is a **breaking** release. The knowledge wiki stores entries and nothing else: the
`index.md` catalog and its `index-watermark`, reciprocal `## Related` back-links,
supersession banners and `overview.md` are no longer written. Each was a cache of data the
entries already hold, and each was a shared file concurrent PRs fought over, which is why
a post-merge reconciliation pass existed. 3.0 derives all of them on read
(`scripts/knowledge_catalog.py`, or the Routing section's `awk` one-liner) from two
metadata lines every entry now carries — `**Theme**` (one lowercase kebab-case name) and
`**Summary**` — plus forward-only `## Related` links
(`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`). Entries are write-once,
each work unit's PR carries its knowledge complete, and `minerva:cleanup` only removes
merged worktrees and prunes branches: it opens no PR.

**Removed.**

- `minerva:synthesize` and `minerva:lint-fix` are deleted; invoking either reports
  "skill not found". There is nothing left for them to maintain: the overview is the
  derived theme-grouped catalog, and catalog lines and reciprocals are no longer stored.
- `scripts/knowledge_fix.py` is a **tombstone**: it prints migration instructions and
  **exits non-zero**. That is deliberate — a CI job that "succeeds" doing nothing would
  hide the change. `synthesis_status.py` and `knowledge_edits.py` are gone.
- `minerva:cleanup`'s knowledge reconciliation (and its `minerva/reconcile` PR).

**Upgrade steps, in order.**

1. **Delete any CI job or script that calls `knowledge_fix.py`** (a post-merge
   "reconcile knowledge" workflow). It now fails on every run.
2. Run **`minerva:migrate`** (read-only). It reports legacy `index.md` / `overview.md`
   still present, entries missing `**Theme**` / `**Summary**`, legacy `NNN-` ids, and
   agent files whose routing still names the legacy files.
3. Run **`minerva:migrate-fix`**. It renames `NNN-` ids first if needed, then backfills:
   each missing `**Summary**` from the entry's `index.md` line, each missing `**Theme**`
   from the first `overview.md` section linking the entry, then deletes both files. It
   inserts only those metadata lines, runs as a dry run first, applies behind a
   confirmation gate, and lists entries it could not fill for hand-writing.
4. Re-run **`minerva:init`**. It detects the stale `## minerva` Routing section and offers
   a gated refresh to the catalog one-liner.
5. Run `minerva:lint` and treat its count as a new baseline
   (`skills/migrate-fix/references/upgrading.md`).

**What lint enforces now.** Invalid ids and broken `## Related` links are errors. A missing
`**Theme**` or `**Summary**` is an **error** for an entry whose filename id is a date on or
after 2026-10-01 and a **warning** for an older or `NNN` entry — so every entry written
under 3.0 is enforced and an un-migrated legacy corpus stays green. The rule keys on the
entry's own date, never on whether legacy files exist. A legacy `index.md` / `overview.md`
still present is a warning pointing at `minerva:migrate-fix`; a theme used by one entry is
an advisory warning. There are no index-drift, watermark or missing-reciprocal checks.

**Legacy content is left in place and still read.** Existing stored back-links and
`<!-- superseded-by: -->` banners are not removed: they remain valid links, and the
catalog derives supersession from the union of another entry's `supersedes` edge, the
entry's own legacy `superseded by` edge, and its legacy banner — each successor listed
once. In-flight lifecycle checkpoints written by 2.x with a `reconciliation` phase are
still read and resume as `cleanup`.

**Mixed versions.** Every collaborator should upgrade. Until they do, a collaborator still
on 2.x whose cleanup recreates `index.md` only produces the legacy-aggregate lint warning —
never an error, and no textual conflict, since 3.x never writes that file. A 2.x cleanup
may also write back-links into older entries, which is harmless. A 2.x CI job calling
`knowledge_fix.py` fails on the tombstone (step 1).

## Regression evidence

Run the complete deterministic suite and existing eval gate:

```bash
python3 -m pytest tests/ -q
python3 scripts/run_skill_evals.py --dry-run
python3 scripts/knowledge_lint.py .minerva/knowledge
python3 scripts/run_compatibility_evals.py --host both --dry-run
```

The existing structural contracts, phase rules, review gates, skip/escalation
predicates, and helper tests remain. Host-specific assertions were replaced as
follows; none of their behavioral protections was removed:

| Previous assertion | Replacement |
| --- | --- |
| Every dispatcher spells `run_in_background` | Registered canonical sites must wait for results; adapter tests separately pin Claude synchronous `Agent` and sonnet policy, and Codex fresh context / inherited settings |
| Cache-search resolver appears at every registered helper site | Same registered helper/guard sites use the installed runtime resolver; executable fixtures cover consumers, symlinks, overrides, stale installs, and paths with shell metacharacters |
| Invocation says `via the Skill tool` | Same caller/argument/phase inventory says `via the skill loader`, backed by both adapter contracts |
| References start `plugins/minerva/skills/` | Canonical references resolve inside the loaded package; negative tests still reject missing and wrong-skill references |
| Orphan detector snippet rewrites a hardcoded import | Shipped snippet executes unchanged with installed/corpus paths passed as arguments |

Runtime tests exercise corrupt state, concurrent revisions, immutable identity,
monotonic budgets, completion/clear, host resume prompts, and linked-worktree
teardown. Installer tests use disposable configuration and stub external CLIs.
The fixture runner's own tests reject empty responses, narrated dispatches,
missing fixture-tool calls, duplicate PRs, non-green merges, and unknown commands.
CI runs this whole suite on Python 3.11 and 3.13 without model credentials.

## Host conformance

The optional runner launches authenticated local CLIs and may incur normal model
cost. It creates disposable consumer repos, local bare remotes, installed package
copies, and a GitHub CLI stub. It uses normal host permissions and automatic
approval review in Codex; no sandbox bypass. Unknown fixture commands fail closed.
Results and transcripts remain in the reported temporary artifact directory.
When a CLI omits dispatch events, the runner reads only that fixture thread's
session tool records and exports call identities/settings, excluding prompts.

```bash
python3 scripts/run_compatibility_evals.py --host both --scenario read-only
python3 scripts/run_compatibility_evals.py --host both --scenario manual-resume
python3 scripts/run_compatibility_evals.py --host both --scenario auto
```

Scenarios cover read-only readers, init, human gates, grill/replan, standalone
panels/review, the autonomous orchestrator at two change sizes, phased shipping, manual
resume, cancelled CI, and exhausted cleanup. Acceptance checks inspect artifacts,
fixture actions, checkpoints, and actual structured dispatch events rather than
scoring final prose alone. Live conformance results and any remaining app/IDE
manual validation are recorded in the PR; a dry-run is not host acceptance.

A timed-out lifecycle fixture can continue from its existing checkpoint:

```bash
python3 scripts/run_compatibility_evals.py --host codex --scenario auto-small \
  --resume-fixture /absolute/path/to/minerva-codex-auto-small-fixture --timeout 900
```

Continuation validates the temporary fixture and its local remote, retains the
original transcript, and saves separate resume artifacts. It cannot restart
intake or silently refresh the saved retry budget.
