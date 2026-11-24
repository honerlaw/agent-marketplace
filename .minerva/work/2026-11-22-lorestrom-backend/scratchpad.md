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
- [solo] UTF-8 guard, lorestrom phase 1: `entry_payload` raises unless files are read as UTF-8 (UTF-8 mode or a UTF-8 locale), not only in UTF-8 mode; the amendment's aim, never guessing an encoding, holds either way (tier: solo; small, reversible, inside the adjudicated amendment's intent)
- [solo] 3.11 gate: run with `--with pyyaml` online; 1539 passed, same as 3.13 (tier: solo; operational, no plan change)
- [reviewed — clean] completion, lorestrom phase 1: Verifier accept, criteria 1–6 and phase 1 scope met; non-blocking: the sync rule lives in lorestrom's README and the drift test only, since minerva's README cannot change (tier: reviewer; floor: completion is always a Verifier)
- [solo] review triage, lorestrom phase 1: M1, M2, L1–L4 all FIX, no replan: defects inside the approved plan (tier: solo; each has one dominant disposition)

## Decisions 2026-11-24
- [user-directed] merge: the user had #152 merged and phase 2 started; phase 1 cleanup deferred teardown (phase 1 of 3 merged, counted from merged PRs because a squash merge hides the branch); the old draft branch is kept until the unit's final cleanup
- [reviewed — folded] new-plan acceptance (replan 2026-11-24, split the lifecycle phase): Skeptic revise, 1–6 folded (grill-plan, explore, one-by-one and debug into 0.2.0; the disable instruction kept with the orchestrators-in-0.3.0 note; size estimate and copy-then-adapt commits; inert --auto hooks; the case for four phases; per-phase guard coverage) (tier: reviewer; floor: new-plan acceptance is always reviewed)
- [rechecked — escalated] new-plan acceptance: 1–6 addressed; N1, debug's live reference write against a unit's held replace and the waiting-for-merge rule → Adjudicator
- [adjudicated — proceed] new-plan acceptance: N1 resolved; Lorestrom's release fails a held replace STALE after a later live edit; amendment: a unit reads the doc in the same step as its hold and the contract states the remaining window; the rule change is stated explicitly; applied after the ruling
- [reviewed — folded] completion, lorestrom phase 2: Verifier reject on B1 (a plain confirm never reaches reconcile), everything else met; B1 is an implementation defect against the unchanged Approach 6, not a criterion the plan cannot meet, so it is fixed in the review round with no replan (tier: reviewer; floor: completion is always a Verifier)
- [solo] review triage, lorestrom phase 2: B1, the skill-text review's 2 high, 8 medium and 6 low, the scripts review's 3 high, 2 medium and 3 low, and the Verifier's notes N1–N4 all FIX, no replan: each is a defect inside the approved plan (tier: solo; each has one dominant disposition)
- [solo] re-review triage, lorestrom phase 2: medium 1 (confirmation lost on the release path), medium 3 (resurrection with a local branch, or a complete phased unit) and lows 4–7 FIX; medium 2 resolved by reverting S6 instead of amending Approach 6: ship records a head only for a branch with its own commits, so an ancestor head on the mainline is a fast-forward merge the plan releases, and S6 cost that case a question while guarding a near-impossible one (tier: solo; reversible, keeps the approved plan unchanged)
- [reviewed — clean] completion, lorestrom phase 3: Verifier accept, every criterion reproduced, 6 of 6 mutations caught; notes on the phase loop's target and two weak tests folded into the review round (tier: reviewer; floor: completion is always a Verifier)
- [solo] review triage, lorestrom phase 3: the code review's 1 high, 3 medium and 4 low, plus the Verifier's notes, all FIX, no replan: each is a defect against phasing.md and the storage contract as approved (the loop returns to work, Mode A waits for the final phase); the shared successor-test blind spot is left as a follow-up because tightening it changes minerva's tests (tier: solo; each has one dominant disposition)
- [reviewed — folded] completion, lorestrom phase 4: Verifier revise on one defect (a closed PR is judged before a missing head is fetched, so the sweep proposes abandon on unchecked evidence), everything else met; an implementation defect against Approach 6, fixed in the review round with no replan; the builder's two calls (status staleness from recorded heads, a dry run that never fetches) judged acceptable (tier: reviewer; floor: completion is always a Verifier)
- [solo] review triage, lorestrom phase 4: the code review's 1 high, 2 medium and 6 low, the Verifier's defect and its notes all FIX, no replan: each is a defect against the approved sweep, status and lint rules (tier: solo; each has one dominant disposition)

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

## Review triage 2026-11-23 (lorestrom phase 1)
- [FIX] M1 medium — a project with no remote was resumed silently by another repo typing the same name: init now always asks, showing title, kind, status and aliases
- [FIX] M2 medium — CRLF entries were normalised and their digest was not the file's: read byte-faithfully; CLI test checks digest = sha256 of the bytes
- [FIX] L1 low — `find_docs` has no key filter: page by workspace without `kinds` and compare keys; a same-key doc of another kind is refused
- [FIX] L2 low — SSH remotes under a home directory gave a label naming a person: no label
- [FIX] L3 low — the UTF-8 re-exec dropped `-I`/`-E`/`-s`: carried over
- [FIX] L4 low — property keys trimmed as Python, not as Lorestrom (JavaScript) trims: explicit set
- Each fix reverted in turn: its test fails (5 of 5). Full suite green after.

## Work notes (lorestrom phase 2)
- Size check before porting: the 14 lifecycle skills are 35 files and about 4,000 lines of minerva prose, much of it shell snippets under the names-are-data guard. Phase 1's PR was 4,250 inserted lines across 31 files and needed review fixes. A full phase 2 PR would plausibly pass 7,000 lines, too large to review well. The work stopped at a foundation commit, and the split goes back to the orchestrator as a question (it changes the replan's phases).
- Foundation, inside the replan and proposal Approach 4–6, and needed by any split. In `lorestrom_backend.py`:
  - `unit_key`, `record_key`, `unit_state` (the gate is the authority, `refresh` when `minerva:state` lags), `release_outcome` (a CONFLICT is success only when `get_gate` shows the gate released) and `repair_flips` (failed `set_status current` writes whose entry is still `draft`);
  - `reconcile_action` (pure safety table) and `merge_evidence` (git evidence: 40-hex shas only, default branch found, never input; `merge-tree --write-tree` needs git 2.38);
  - `reference_payload`, `reference_list` and `read_repo_reference` (no symlinks followed, byte-faithful, digest confirmed);
  - CLI commands `unit-state`, `release-outcome`, `repair-flips`, `reconcile`, `reference-list` and `reference-payload`.
- `reconcile_action` choices: a CLOSED PR in any phase abandons, as Approach 6 says. `--merged <sha>` confirms one phase, and only when that commit is on the default branch. `--yes` has no input here, so it cannot confirm. Staleness (no head after 14 days) only flags.
- Deletion pass 2026-11-23, 20 chosen mutations over the new rules: 18 caught at first. "Confirm needs no PR" is an equivalent mutant: OPEN already waits, MERGED counts as merged and CLOSED abandons, so the clause is defensive. "Reference read stays in its directory" survived because no test asked for an existing `.md` outside it; the test was added and the mutant is now caught. As before, this measures only the mutations chosen.
- Not started at the foundation commit; done after the 2026-11-24 replan split (below).
- Built to the 2026-11-24 split (phase 2 = 0.2.0 "Lifecycle and handover"). Commit order: verbatim copy of the 12 skills (6339c45; tree hashes equal minerva's at that commit), a mechanical rename (dc87483), then adaptations: runtime and contract (12a4572), intake skills (781a8a8), lifecycle skills (cb46328), status (a51aec4), handover and authority (a30b280), 0.2.0 and guards (7d7cddc), and small fixes.
- Choices made inside the plan, not new plan:
  - The GitHub label stays `minerva:followup` and the cross-session markers stay `[minerva pre-flight]` / `MINERVA-BUSY|IDLE`, so a minerva peer and a lorestrom peer interoperate. This follows the kept `minerva:` namespace.
  - `work_status.py` is copied byte for byte (drift-tested like the knowledge files) for phase parsing; minerva's `knowledge_catalog.py` and `workstream_status.py` are not ported, since lore comes from `storage:knowledge.list` and status reads units from Lorestrom.
  - Target resolution's fallback is "the only open unit" instead of "most recently modified": unit docs carry no mtime the contract relies on. An explicit id must be a checked one.
  - Records never enter git: propose makes no initial commit, and the worktree's ignore check is `git check-ignore`, since init ignores worktrees in `.git/info/exclude` unless `--shared`.
  - `find_docs` filters in the ground rules now include `properties`, `statuses`, `tags` and `gateId` (Lorestrom's public tool surface); the pinned safety clause was reworded deliberately.
  - `--merged <sha>` and `--abandon` are new cleanup arguments, feeding `reconcile`.
- Deletion pass 2026-11-24, 28 chosen mutations over the new helper, runtime and guard rules: 22 caught at first. Fixed by tests: `removal-plan` keeping refused files, `unit-ids` kind filter (the test's record shared a real unit's id), `phases` filtering unhashable names. The `removal-plan` single-doc check was an equivalent mutant (an earlier branch already keeps duplicates) and was simplified away. One survivor remains: a prose contradiction ("…also after a no") added beside an offer's "On a yes" passes the structural offer test; the "kept by default" and "No earlier yes…" pins still hold. After fixes: 26 of 27 caught. Safety clauses are exact-string pins: removing one fails its row by construction.

## Review triage 2026-11-24 (lorestrom phase 2)
Verifier and the two code reviews; every item FIX inside the approved plan, no replan. Each test below fails with its fix reverted in a throwaway worktree.
- B1 fixed: `reconcile` takes `userConfirmed` (phase numbers), counted only for `phasesToConfirm`, others reported as `refusedConfirmations`; storage.md's `unit.confirm` passes it — `test_a_user_confirmation_reaches_reconcile_through_the_request`, `test_a_confirmation_counts_only_for_a_phase_reconcile_asked_about`.
- S1 fixed: `phases` takes the unit's recorded `heads` and `base` and counts a local merge only for a head ≠ base that is an ancestor of default; storage, ship, cleanup, status and phasing pass them — `test_a_fresh_phase_branch_is_not_merged`, `test_a_recorded_head_on_the_default_branch_is_merged`.
- S2 fixed: merged evidence first; a CLOSED PR abandons only an unmerged phase whose merge is not a no-op (CLOSED+noop asks) — CASES closed+confirmed, closed+ancestor, closed+noop, closed later phase.
- S3 fixed: `lorestrom_scripts.load` restores `sys.path` — `test_loading_lorestroms_scripts_leaves_minervas_imports_alone`.
- S4 fixed: `read_repo_reference` builds the path from the repository top — `test_reference_payload_reads_through_a_symlinked_cwd`.
- S5 fixed: the guard list (`GUARDED`) adds debug, explore, grill-plan, one-by-one, using-minerva — `test_the_guard_covers_every_minerva_skill_but_status`.
- S6 fixed: a head on `rev-list --first-parent <default>` is an ancestor only with a MERGED PR — `test_a_head_on_the_mainline_needs_a_merged_pr` (the fast-forward test now asks; a `--no-ff` merge releases).
- S7 fixed: runtime `UNIT_ID_RE` is the helper's pattern; checkpoints also accept `bare-<sha256>` keys — `test_the_runtime_takes_the_helpers_unit_id_shape`, `test_the_runtime_and_the_helper_share_one_unit_id_pattern`, `test_a_bare_ship_key_is_still_a_checkpoint`.
- S8 fixed: a token that is not 32 hex fails the read — `test_a_damaged_token_is_refused_not_read_as_empty`.
- K1 fixed: issue title and body written to mktemp files with a file tool; `--title "$(cat "$T")" --body-file "$B"` — `test_no_skill_puts_text_into_a_shell_heredoc`, `test_promote_files_an_issue_from_two_temp_files`.
- K2 fixed: Will abandon section; abandon only on a yes naming the unit, or an explicit `<unit> --abandon` — safety pins + `test_the_cleanup_gate_has_a_will_abandon_section`.
- K3 fixed: on-approval step 2 resumes this clone's own aborted unit (token matches the doc's first line) under its original id — safety pin.
- K4 fixed: with no link or server, nothing under `.lorestrom/worktrees/` is torn down — safety pin.
- K5 fixed: cleanup's explicit argument exempts `--abandon` and `--merged` from "merged" — safety pin.
- K6 fixed: the proposal rewrite uses `storage:record.write`; `storage:unit.finish` is Mode A's last step — `test_unit_finish_is_promotes_last_step`.
- K7 fixed: `git commit -F <temp file>` — `test_ship_commits_from_a_message_file`, heredoc test.
- K8 fixed: resurrection checks out `refs/remotes/origin/<branch>` (phased: `next_branch`), otherwise asks — safety pins.
- K9 fixed: `removal-plan` also removes for superseded and deprecated docs; draft, archived and no match keep — `test_removal_plan_removes_a_file_whose_retired_doc_holds_its_digest`, archived case, `test_removal_keeps_retired_docs_removable`.
- K10 fixed: debug shows the text and gets a yes before an inside-unit hold; cleanup's Will release line lists held reference writes — safety pins + gate test.
- K11 fixed: `list_doc_changes` pages by `limit`/`before` until the import's own write — safety pins.
- K12 fixed: `git diff --cached --quiet` first, then `git commit -F <temp file> -- <listed path>…` — safety pins.
- K13 fixed: `checkout --no-track -b` on the phase cut — `test_the_phase_cut_does_not_track_the_default_branch`.
- K14 fixed: `unit.ship` re-recorded after every push, including CI fixes — safety pins.
- K15 fixed: runtime Scope states one rule (no orchestrator passes `--auto` until 0.3.0; a user-typed one changes only the gates it names) — safety pin, reworded deliberately.
- K16 fixed: the five session-context steps drop a trailing `-phase-N` (cleanup's variant has no branch-name step) — `test_every_session_context_step_strips_the_phase_suffix`.
- N1 fixed: rows gain `update_doc` (unit.list, record.write, reference.write) and `hold_write`/`reference-payload` (reference.update); `test_each_rows_columns_name_every_tool_and_helper_its_section_uses` checks completeness.
- N2 fixed: work, grill-plan and one-by-one say records, not files — `test_no_skill_assumes_record_files`.
- N3 fixed: every "`propose-ship-*` orchestrators" says (0.3.0) — `test_every_orchestrator_mention_says_it_arrives_in_0_3_0`.
- N4 fixed: a minerva-begun unit finishes on minerva's skills run one by one, never its orchestrators — safety pin.
- each fix reverted in turn: 29 of 29 caught

## Re-review triage 2026-11-24 (lorestrom phase 2 fixes)
- [FIX] medium 1 — `unit.release` re-ran reconcile without the user's confirmation: it acts on the `release` from `unit.confirm`'s re-run
- [FIX] medium 2 — S6 changed Approach 6's release rule unrecorded: S6 reverted, a fast-forward merge releases again; test renamed to say so
- [FIX] medium 3 — resurrection reuses an existing local branch (no `-b`, never `-B`) before origin's; a phased unit with every phase merged stops and asks
- [FIX] low 4 — phases example keyed heads by PR; it is the phase number
- [FIX] low 5 — an integer confirmation is refused with an error instead of being reported as the string form
- [FIX] low 6 — ship's garbled head-recording sentence split
- [FIX] low 7 — `T` and `B` set to the files' absolute paths in the same shell call
- Each logic and safety fix reverted in turn: its test fails (5 of 5); 4 and 6 are wording.

## Work notes (lorestrom phase 3)

- Commits: verbatim copy of minerva's propose-ship and propose-ship-auto (tree hashes equal
  minerva's at that commit), the same mechanical rename phase 2 used, one adaptation commit for
  the orchestrators, one for the live `--auto` hooks and 0.3.0, one for tests.
- Choices inside the plan:
  - cleanup's `--yes` never confirms an unproven merge, so an orchestrator's cleanup gate that
    meets one asks the user; in propose-ship-auto it is a new hardcoded trigger (counted).
  - A closed PR leaves the unit's gate open; no orchestrator abandons a gate.
  - propose-ship's cleanup gate gained the phased-unit loop phasing.md asks of every
    orchestrator; minerva's propose-ship lacks it (a minerva follow-up to report).
  - Decision lines keep minerva's telemetry format in the scratchpad record; lorestrom ships
    no tally (minerva's `decision_telemetry.py` reads files only).
  - The orchestrator contract tests (orchestrated mode, phase continuation, phasing) now run
    over both plugins via `skills_corpus.PLUGIN_SKILLS`; minerva's assertions are unchanged.
- Deletion pass: 20 of 21 mutations caught. Survivor: deleting "advance to Phase 3" from
  Phase 2 passes, because `test_every_integer_phase_names_its_successor` accepts any mention of
  Phase 3 in the section (Phase 2 cites "Phase 3 step 3"). The same blind spot exists for
  minerva; it is the shared guard's, not this phase's.
- Noted, unchanged: the runtime's ship resume prompt adds `--auto=<caller>` for any caller,
  as minerva's does; propose-ship never passes `--auto` to ship, so its checkpoints carry
  caller null.

## Review triage 2026-11-24 (lorestrom phase 3)

- R1 FIX (high): a phased unit's loop skipped work. propose-ship returns to Execution step 3 (`lorestrom:work`), propose-ship-auto to Phase 2, each cutting next_branch as ship's phase resolution says; phasing.md's rule loops to the work phase. The shared phasing test now takes each plugin's loop sentence and target (minerva's unchanged).
- R2 FIX (med): before a phased unit's final phase both orchestrators run promote's Mode B only, and promote's Mode A stops there (`phases`: `complete` false, `next_position` not `total`), so no unit.finish after phase 1.
- R3 FIX (med): propose-ship writes its own `--cleanup-only` resume prompt (its checkpoint caller is null) and tells the user before ship how to re-enter after a CI-watch wake-up. Nothing writes `propose-ship` as a caller, so the runtime refuses it.
- R4 FIX (med): Lorestrom's body writes do not check a doc's status, so an archived record still takes them. Decision lines after promote go into the archived scratchpad record (storage.md), and the checkpoint's counters carry the totals (governance.md).
- R5 FIX (low): a decision line is a replace inside its Decisions block, not an append.
- R6 FIX (low): the runtime scope matches the Delegated skills table (ship invoked, work/review/promote inlined, replan restated).
- R7 FIX (low): the Verifier's artifact is the worktree's diff as review's Diff resolution computes it, uncommitted and untracked work included.
- R8 FIX (low): every `lorestrom:propose-ship*` mention names one of the two skills; every `--auto=` value in the auto orchestrator is `propose-ship-auto`.
- Follow-up (left alone): `test_every_integer_phase_names_its_successor` accepts any mention of the next phase; the blind spot is shared with minerva.
- Follow-up (minerva, reported): minerva's phasing rule loops back to the ship phase and its propose-ship has no phase loop.
- each fix reverted in turn: 16 of 16 caught

## Re-review triage 2026-11-24 (lorestrom phase 3 fixes)
- [FIX] medium 1 — the Verifier brief still used `git diff BASE...HEAD`: it now uses review's Diff resolution, uncommitted and untracked work included
- [FIX] low 2 — completion on a phased unit checks the current phase's own criteria from `## Phases`, in the brief and in Phase 2
- [FIX] low 3 — every final-phase check names `phased` true, so an unphased unit never stops before Mode A
- [FIX] low 4 — the scope check's cost line says phasing re-runs work, review, promote (Mode B) and ship
- [FIX] low 5 — propose-ship's step 5 runs the phase check before invoking promote
- Each logic fix reverted in turn: its test fails (3 of 3); 4 and 5 are wording.

## Work notes (lorestrom phase 4)

- lint is ported like phases 2–3: a verbatim copy (tree equal to minerva's lint), the same mechanical rename, then adaptation. Its mechanical pass is the helper's `lint-docs` over `find_docs` (every status), `find_relations` (`supersedes`, `relates_to`) and the units' gate states; the checks keep minerva's families where they carry over (id, metadata with the same 2026-10-01 cutoff, theme) and add what only Lorestrom has (key, broken-link to an archived entry, supersession drift, pending on a released or abandoned gate, incomplete import). Orphans are computed from edges, so backlinks from other projects count. A finding names an entry by its checked stem or doc id, never by its title, theme or body.
- Age and owner come from the gate: Lorestrom's `get_gate` returns `openedAt` and `openedByUserId`, and `whoami` the person; `find_docs` returns neither a creator nor a date. `unit-state` now prints `age_days` (what `reconcile` already took, previously "0 when unknown"), `mine`, and `stale`.
- Status cannot run `reconcile` for staleness: `git merge-tree --write-tree` writes objects, which breaks status's read-only contract. So `unit-state` computes `stale` from recorded properties (a phase with no recorded head, or a head equal to the base, after `STALE_DAYS`), sharing reconcile's threshold constant. reconcile keeps its tree-based check.
- Another clone's unit: its heads may be absent here, which reconcile used to report as "no recorded head". It now answers `wait` with `fetch` (the phases whose head is missing), and the sweep fetches `refs/pull/<pr>/head` by the recorded all-digit PR number, which GitHub keeps after the branch is deleted, then asks once more.
- The sweep's rules (`cleanup/references/sweep.md`): releases only on reconcile's answer; a unit someone else opened (or whose opener is unknown) needs a yes naming it for any action, and `--yes` never covers one; abandon keeps the K2 rule; staleness is shown, never acted on; only this clone's worktrees are removed, and the owning clone tears its own down later (release-outcome reads the released gate as success). cleanup/SKILL.md went down to 9057 bytes (one parenthetical moved out, the protocol into the reference).
- Deletion pass, in a throwaway copy: 24 mutations over the helper's new functions, the sweep's and lint's safety clauses, the contract row and the deferral wording. 23 caught on the first run; the survivor (dropping the record of `supersedes` targets) gained `test_a_superseded_entry_with_its_successor_edge_is_clean` and is caught now: 24 of 24.

## Review triage 2026-11-24 (lorestrom phase 4)

- V1/P4 FIX (blocking): a closed PR with an unfetched head abandoned before the fetch. The missing-head `wait` with `fetch` now comes before the closed check, and the closed check also excludes `missing`. That second guard is unreachable after the reorder (a missing head is always headless), so it is defence in depth that no test can isolate; reverting V1 whole is caught.
- P1 FIX (high): every cleanup, a single-unit one included, computes `mine` and `age_days` in release.md's Decide step (`get_gate`, `whoami`, `unit-state`); `--yes` acts only on a unit whose `mine` is true. `unit.release` gains `whoami`; both orchestrators say their `--yes` covers only the run's own unit.
- P2 FIX (med): lint-docs takes units as `{id, state}` and builds each key with `unit_key`; a hand-made key or a malformed id is ignored.
- P3 FIX (med): an edge whose source entry is archived (an abandoned unit's) is not a broken link.
- P5 FIX (low): a draft entry is not an orphan: its edges may still be held.
- P6 FIX (low): status pipes `unit-state` in step 3, after `phases`; `unit.list` and the sweep pass the phase count.
- P7 FIX (low): `unit-state` reads `openedByUserId`, get_gate's own field (the older `openedBy` is still accepted); the contract text uses `openedByUserId`.
- P8 FIX (low): the fetch test builds the PR head in a second clone used as origin, so the head must be fetched; the false comment is gone.
- P9 FIX (low): cleanup's Target resolution says the default is the sweep.
- V-note FIX: `--dry-run` fetches nothing, not even origin, and reports a unit from elsewhere as waiting on a fetch.
- V-note FIX: a malformed edge is skipped and counted (`skippedEdges`), and a non-string `minerva:context` is a `pending` finding, not a crash.
- each fix reverted in turn: 11 of 11 caught (V1 counted whole, as above). A first revert run printed CAUGHT for V1's second guard alone; rerun with exit codes and test counts, it passed, which is how the unreachable guard was found.

## Re-review triage 2026-11-24 (lorestrom phase 4 fixes)
- [FIX] medium — cleanup's question on a unit whose `mine` is not true (a resumed colleague's unit, an unreadable opener) stopped the autonomous run uncounted: it is now a hardcoded, counted trigger in propose-ship-auto and is named in both orchestrators' cleanup gates; release.md says only a unit the run opened is `mine`
- [FIX] low — an archived entry's edge no longer counts as a link (orphans, supersession); live edges from other projects still count
- [FIX] low — a dry run says a unit whose only evidence is ancestry against an unfetched default branch may show as waiting
- Each logic fix reverted in turn: its test fails (2 of 2); the dry-run line is wording.
