# Scratchpad: lorestrom-backend

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-22
- [reviewed — folded] scope check: one unit, three phases; writes refuse in phase 1, push release moved into phase 2, pins named (tier: reviewer; scrutiny: ambiguity, blast radius; parallel wave)
- [rechecked — residual folded] scope check: C1–C4 addressed; double release added to phase 2 criteria
- [reviewed — folded] approach: A over B/C/D; site inventory + check-tree, no read-side renderer, backend-scoped cleanup rule (tier: reviewer; scrutiny: new interface, knowledge tension; parallel wave)
- [rechecked — escalated] approach: F1 (failed status flip / pending marker) → Adjudicator
- [adjudicated — proceed] approach: F1 resolved. PROTOCOL DEVIATION: the main model edited the draft to fix F1 (and folded F2, F3) after the fold-audit and before this ruling, so the Adjudicator ruled on unaudited text
- [reviewed — folded] whole-proposal (restart: approach fold rewrote Success criteria; first review discarded): C1–C6 folded; main model also changed config to local by default, confirmed import, no upserts, recorded-head merge evidence (tier: reviewer; scrutiny: blast radius, knowledge tension)
- [rechecked — escalated] whole-proposal: C1–C6 addressed; F1–F6 → Adjudicator
- [adjudicated — escalated] whole-proposal: F1–F6 all unresolved → user
- [escalated to user] whole-proposal: F1+F2 — user chose discovery from a Lorestrom project node, optional committed marker, accepting that clones without MCP use files and Codex finds lore only through skills; F3–F6 — user chose fix all four (escalation counter: 1)
- [reviewed — clean] completion, phase 1: Verifier accept, criteria 1-6 and the refusal criterion met; non-blocking: say aliases are space-separated, check-tree for propose and promote lands in phase 2 (tier: reviewer; floor: completion is always a Verifier)
- [solo] review triage, phase 1: 28 FIX and 1 split (25: FIX port, IGNORE case); no replan, all are defects inside the approved Approach (tier: solo; each has one dominant disposition)
- [solo] re-review triage, phase 1: all FIX, no replan: defects inside the approved Approach; the body becomes the entry verbatim, which still meets Approach 2 (tier: solo; each has one dominant disposition)
- [solo] third-review triage, phase 1: 2 blockers and the notes with a realistic failure FIX, 3 rare-environment notes SUGGEST; no replan, all inside the approved Approach (tier: solo; each has one dominant disposition)
- [reviewed — clean] committed-marker check, phase 1: the runtime decides "no link" by file checks only, per criterion 1; the helper still reads the default branch; Skeptic ACCEPT, ordinary fix, no replan (tier: reviewer; scrutiny: two spec rules in tension)
- [user-directed] publishing: rebuild the branch as fresh commits without private references before its first push
- [user-directed] merging: the user merges each PR; each phase starts from main after that merge

## Decisions 2026-11-23
- [user-directed] packaging: a new plugin `lorestrom` in this marketplace, backed by Lorestrom only with no file mode; minerva stays files-only and unchanged (the user chose it over keeping the plan, a fork repo, or a separate repo)
- [reviewed — folded] new-plan acceptance (replan 2026-11-23): Skeptic revise, findings 1–7 folded; its suggestion that init write host plugin settings was not adopted, init tells the user how instead (tier: reviewer; floor: new-plan acceptance is always reviewed)
- [rechecked — escalated] new-plan acceptance: 1–7 and the deviation accepted; R1 stale bridge copies, R2 encoding, R3 guard scope → Adjudicator
- [adjudicated — proceed] new-plan acceptance: R1–R3 resolved with amendments (reference docs wait for 0.2.0's confirmed handover sync; UTF-8 mode with a subprocess locale test; only scanning checks parametrized); applied after the ruling
- [user-directed] branch: rebuilt from main as fresh commits; the old local branch is kept as `2026-11-22-lorestrom-backend-minerva-draft` until phase 1 merges

## Work notes (phase 1)
- `entry_payload` must mirror all three catalog supersession sources: `superseded by` labels and legacy banners become reversed `supersedes` edges; an inverted `supersedes` becomes `relates_to`.
- `2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption` has a summary over Lorestrom's 1000-character property limit: import refuses and reports it, per Approach 2.
- Choices inside Approach 2: a title over 200 is shortened with the whole H1 kept in the body; `minerva:digest` (sha256 of the source file) is how import reports a changed entry without reading bodies; the body keeps anything under `## Related` that is not a single-target link line.
- A repo label strips user/token/port/query, and a local path has no label: it is sent to Lorestrom.
- check-tree reads the index as well as the working tree (staged, then deleted from disk, still commits).
- MCP `get_doc` returns no key/status/properties/ownGate: use `find_docs` and `get_gate`.
- Skill notes are `storage:<op>`; runtime.md binds them. An unlinked project with no Lorestrom server runs nothing, so self-hosting and Python-less read-only runs are unchanged.
- The site scan also matches bare record file names and `storage:` notes, so it registers more files than the path-only scan in Approach 3.
- Units written before linking stay readable as files in 4.1; ship runs `check-tree`, so finishing one needs `minerva:init --backend files`.
- Deletion pass 2026-11-22 in a throwaway copy, green baseline (196): 45 mutations, all caught, including the four inventory cases.
- Before any push: this repository is public and lorestrom's is private, and auto-merge is disabled here. The user decides what is published.

## Review triage 2026-11-22
- [FIX] F1 critical phase 1 — unsafe entry file names reach the shell
- [FIX] F2 critical phase 1 — import follows symlinks
- [FIX] F3 high phase 1 — interrupted create completes with no body
- [FIX] F4 high phase 1 — git failures read as files
- [FIX] F5 high phase 1 — orphan pointer marker deletes notes
- [FIX] F6 high phase 1 — check-tree blind in worktrees under --shared
- [FIX] F7 high phase 1 — re-link loses the label
- [FIX] F8 high phase 1 — opt-out blocked by resolution
- [FIX] F9 high phase 1 — find_docs takes kinds and workspaceId
- [FIX] F10 high phase 1 — taken key can loop
- [FIX] F11 high phase 1 — conflicting or cyclic imported edges refused
- [FIX] F12 medium phase 1 — label leaks credentials and paths
- [FIX] F13 medium phase 1 — marker trusted across forks and symlinks
- [FIX] F14 medium phase 1 — alias separator unstated
- [FIX] F15 medium phase 1 — entry text lost
- [FIX] F16 medium phase 1 — crash exits 1 like stray records
- [FIX] F17 medium phase 1 — case or negated ignore dirties the tree
- [FIX] F18 medium phase 1 — non-UTF-8 and CRLF user files
- [FIX] F19 medium phase 1 — check-tree dead end before link
- [FIX] F20 medium phase 1 — unlinked repos asked or stopped without a remedy
- [FIX] F21 medium phase 1 — retired project links
- [FIX] F22 medium phase 1 — tests miss safety clauses
- [FIX] F23 medium phase 1 — legacy entries unselectable
- [FIX] F24 low phase 1 — wrong origin URL
- [FIX] F25 low phase 1 — port merge; case-folding kept because hosts treat paths case-insensitively
- [FIX] F26 low phase 1 — branch import published unannounced
- [FIX] F27 low phase 1 — edge effects unshown
- [FIX] F28 low phase 1 — setup yes and folder retry
- [FIX] F29 low phase 1 — pointer omits org
- Correction to the deletion-pass note above: 45 of 45 covered only the mutations chosen; review deleted 14 safety rules with the suite green.
- All triaged fixes applied 2026-11-22, each module fix mutated (37 of 37 caught) and each contract line deleted in turn; what still deletes green is framing, fences and descriptive text. Prose tests prove a clause is present, not that an agent obeys it.

## Review triage 2026-11-22 (second pass)
- [FIX] N1-N4 high phase 1 — ref name on a command line; GIT_DIR read as files; import loses link text; re-link dead ends
- [FIX] N5-N14 medium phase 1 — marker lookup; stray .git; several holders; no-remote alias ask; unmerged warning; confirmed digest; one bad entry; edges by declarer; lossy markdown; locale
- [FIX] N15, N16, N18 low phase 1 — exit codes; pointer bytes and other worktrees; small guards
- [FIX] N17 medium phase 1 — tests that cannot fail
- Correction: neither "37 of 37" nor "what still deletes green is framing" held. A deletion pass measures only the mutations its author thought of.
- Second-pass fixes applied: 34 chosen mutations, 33 caught at first and the survivor's test tightened and re-checked. Executed skill text is now pinned whole. `knowledge_lint.parse_entry` gained an optional encoding, defaults unchanged.

## Review triage 2026-11-22 (third pass)
- [FIX] B1 blocking phase 1 — evaluated annotation breaks every caller of parse_entry on Python 3.9
- [FIX] B2 blocking phase 1 — re-link opts the clone out before the user agrees
- [FIX] high phase 1 — unreadable cache read as absent; opt-out follows a stale worktree into another clone
- [FIX] medium phase 1 — tag shadows the default branch; subdirectory marker ignored; symlinked .minerva hides records; junk .git; re-link leaves old pointers; runtime's committed-marker check; truncated pages; lossy warning understated
- [FIX] medium phase 1 — tests for the surviving mutants and untested commands
- [SUGGEST] low phase 1 — standing facts: without origin/HEAD only main/master are recognised; a separate-git-dir main checkout keeps its pointer on opt-out from a linked worktree; GIT_CEILING_DIRECTORIES, relative GIT_DIR and literal pathspecs are unsupported
- Third-pass fixes applied: both blockers replayed, 21 chosen mutations caught, every CLI command run on Python 3.9 once (only import-time annotations and zip keywords are guarded by tests; CI has no 3.9). Re-link now changes nothing in the clone before consent. Not exercised: a live Lorestrom server, or an agent following the skill text.

## Review triage 2026-11-22 (verification of the third pass)
- Verdict: ready, no blocking findings.
- [FIX] medium phase 1 — another spelling of a path (root marker, other pointers, entry confinement); a tag spelled like a branch ref; markers between a subdirectory and the root; committed record symlinks; unchecked worktrees unreported; tests for those guards
- [DECISION] medium phase 1 — the committed-marker shell loop in runtime conflicts with success criterion 1: to a reviewer, loop unchanged until then
- [SUGGEST] low phase 1 — standing facts: a submodule's main checkout keeps its pointer (as separate git dirs); a `.git` holding only `config` stops a non-Git project; lower-value surviving mutants
- [FIX] the committed-marker loop is removed (decision above). Only this unit's own new test clause changed; no 4.0.0 assertion.
- Known limit, for promote: with no Lorestrom server, a clone whose working tree and primary checkout both predate a marker on the default branch uses files until one has it, and can commit records as files. The helper binds it whenever it runs; tree.check catches such records only while they are unmerged. Init's text is unchanged: the limit is in runtime.md and the promoted entry.

## Work notes (lorestrom phase 1)
- Built `plugins/lorestrom/` 0.1.0 from the minerva draft branch, without its files backend. Removed: files resolution, opt-out, check-tree, stray records, `--backend`. `resolve` returns `state` `linked`, `discover` or `unlinked`. A broken link still raises; it never reads as unlinked.
- Local state uses lorestrom's own names. The link is `<git-common-dir>/lorestrom/config.json`, `--shared` commits `.lorestrom/config.json`, and `link` excludes `/.lorestrom/worktrees/`. Kinds, keys and properties stay in the `minerva:` namespace, as the replan says.
- UTF-8, a divergence in wording only: the helper re-execs itself with `-X utf8` (guarded by `LORESTROM_UTF8_REEXEC`, which exits instead of looping). `entry_payload` raises when the text encoding is not UTF-8, meaning neither UTF-8 mode nor a UTF-8 locale. The amendment said "not in UTF-8 mode". The invariant it protects, that `parse_entry`'s default-encoding read is UTF-8, holds either way. Requiring UTF-8 mode itself would break every in-process test on a UTF-8 locale. Raised in the report as a question.
- Entries that are not UTF-8 are refused: `read_entry` decodes strictly, and `import-list` lists them under `refused`.
- Tests load lorestrom's modules through `tests/lorestrom_scripts.py`. It runs the plugin's own files under unique `sys.modules` names and restores the shared ones. The root `scripts/` symlinks (minerva's copies) cannot stand in, and a test checks `co_filename`.
- The locale test really runs here: with `env -i`, `LC_ALL=C` and `PYTHONUTF8=0`, the preferred encoding is US-ASCII. "Café" survives `import-list` → `entry-payload` only through the re-exec.
- Gate gap: the directive's offline 3.11 command has no PyYAML, and uv's offline cache lacks it. So `test_site_catalog.py` and `test_skill_contracts.py` fail to collect, on main as well; both are untouched. The 3.11 run ignores those two modules. CI installs pyyaml.
- Deletion pass, run in a throwaway copy (rsync of the worktree, no `.git`). Each case breaks one thing a new guard protects, runs that guard's module, then restores the file. 25 chosen mutations; 24 went red on the first run:
  - drift (the failure message states the sync rule)
  - a manifest version
  - `.minerva/work` named in a skill
  - `.minerva/knowledge` named outside the import
  - an unknown tool in a row
  - `upsert_doc` in a row
  - a missing operation row
  - a safety clause reworded
  - the helper run without `-X utf8`
  - an ADR mention in the README
  - the re-exec removed
  - the re-exec guard disabled
  - `entry_payload`'s encoding check removed
  - a lenient decode
  - a 3.9-breaking annotation
  - the loader shadowed
  - SKILL.md over budget
  - the runtime pointer dropped
  - `AskUserQuestion` outside the adapter
  - a `<branch>` placeholder
  - an unknown `$VAR`
  - the plugin guard removed
  - the helper block resolving the wrong command
  - the install version
- The survivor was a helper misspelled `import_list` in the contract table: the helper regex skipped underscores. The test now takes every code span in the cell. Re-run, it is red, as is a sharper loader mutant (minerva's `knowledge_lint` already imported, lorestrom's not loaded). The restored copy is green.
- This measures only the mutations I thought of. Not exercised: a live Lorestrom server, or an agent following the skill text.
