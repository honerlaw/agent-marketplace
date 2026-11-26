# lorestrom

**minerva's successor.** The same lifecycle, with every durable record kept in
[Lorestrom](https://www.lorestrom.com): a shared workspace of linked docs that several
repositories, people and agents read through its MCP server. There is no local file mode. A
repository that uses minerva moves over with `lorestrom:migrate`.

## This version (0.5.1): lifecycle, migration, orchestrators, sweep and lint

- `lorestrom:init` links any Git repository to a Lorestrom project (found by the repository's
  remote, or created in a workspace you pick) and caches the link in the clone, or commits it
  with `--shared`. In a repository that still holds `.minerva/` it names `lorestrom:migrate`.
- `lorestrom:migrate` moves a minerva repository to Lorestrom: it links if needed, imports
  everything `.minerva/` holds — knowledge entries, reference docs, and every work unit with
  its markdown records — then removes the imported files in a confirmed commit. See
  [Migrating from minerva](#migrating-from-minerva).
- **Lorestrom is authoritative** for a linked repository. `propose`, `work`, `replan`,
  `review`, `promote`, `ship`, `cleanup`, `status`, `grill-plan`, `explore`, `one-by-one` and
  `debug` keep work units, their records, knowledge entries and reference docs in Lorestrom.
  A unit's knowledge is held on its gate and becomes current when `cleanup` releases the gate
  on live merge evidence.
- **Connecting** (0.5.1): wherever a skill finds no Lorestrom server, or a sign-in that
  lapsed, it sends the person to their organization's Agents page,
  <https://www.lorestrom.com/agents>, for the filled-in command, then to sign in. See
  [Setup](#setup).
- Worktrees live under `.lorestrom/worktrees/`, checkpoints under
  `<git-common-dir>/lorestrom/runtime/`.
- The orchestrators run the whole lifecycle on Lorestrom: `propose-ship` with a person
  deciding at each transition, and `propose-ship-auto` with per-decision adjudication, passing
  the `--auto` mode the lifecycle skills carry. Their cleanup gate releases the unit's gate
  through `cleanup`, and asks the user whenever a merge cannot be proved.

- `cleanup` with no argument sweeps every open unit of the project, including other clones'
  and other people's: it fetches a unit's PR heads when this clone lacks them, releases only on
  proven merge, asks before acting on a unit someone else opened, and never removes another
  clone's worktree. `status` shows each unit's age, whether it is stale (no recorded head
  after 14 days) and who opened it. `lint` health-checks the project's knowledge in Lorestrom,
  read-only.

## Setup

1. Connect your organization's Lorestrom MCP server in your host and sign in. Sign in at
   <https://www.lorestrom.com> (or create an account) and create or join an organization.
   Then open its **Agents** page, <https://www.lorestrom.com/agents>, with that organization
   chosen in the switcher. In Claude Code, run the `claude mcp add` command it shows, already
   filled in, then `/mcp` and sign in with the same account. Another MCP client connects to
   the address it shows.
2. Install this plugin: `./install.sh lorestrom --host both`.
3. In a repository, run `lorestrom:init`, or `lorestrom:migrate` in one that uses minerva.

## Migrating from minerva

`lorestrom:migrate` takes a repository from minerva to Lorestrom in one skill, every step
confirmed:

1. **Link**, as `lorestrom:init` does, when the repository is not linked yet.
2. **Live minerva work first.** A `.minerva/worktrees/` checkout stops the migration. Units
   still in flight in minerva (Draft, or never promoted) are finished with minerva first, or
   imported as abandoned on your yes. Branches and open PRs that hold `.minerva/` changes are
   shown: merge or drop them first, since the removal will conflict with them.
3. **Import.** Knowledge entries and reference docs, then work units in batches of 25 (your
   choice at the confirmation). Each finished unit arrives as a released lorestrom unit with
   its proposal, scratchpad, replan, followups and other markdown files as records, so
   `status`, `cleanup` and `lint` treat it as done. Scripts, screenshots and other
   non-markdown files are not imported.
4. **Remove.** One commit removes every file Lorestrom now holds; once every unit is in, it
   also replaces the agent file's minerva routing section with the `## Lorestrom` section and
   drops the `.minerva/worktrees/` ignore line. Whatever Lorestrom does not hold is listed and
   removed only on a separate yes; it stays in git history either way.
5. **Disable minerva** for the repository in your host's plugin settings.

A large corpus takes several runs: each run continues where the last stopped, and an
interrupted unit resumes. Files outside `.minerva/` that mention it (CI workflows, docs) are
listed for you to edit.

With minerva also installed, both plugins' skills are available. In a linked repository run
the lifecycle with lorestrom's skills and orchestrators, and never minerva's
orchestrators: they would write records as `.minerva/` files that Lorestrom ignores. Disable
minerva for that repository in the host's plugin settings. minerva itself is unchanged and
keeps working in repositories that have not moved.

## Maintainer notes

- `scripts/knowledge_lint.py` and `scripts/knowledge_spans.py` are **byte-identical copies** of
  minerva's, so import parses entries exactly as minerva's catalog does.
  `tests/test_lorestrom_plugin.py` fails when they differ. A minerva change to either file
  copies it here in the same PR and bumps lorestrom's patch version.
- `scripts/work_status.py` is a byte-identical copy of minerva's phase parser, checked the same way.
- `scripts/plugin_guard.py` and `scripts/lorestrom_runtime.py` are adapted copies of minerva's.
- The 12 lifecycle and read-side skills were copied from minerva verbatim in one commit and
  adapted in later ones, so their diff against minerva's skills is the adaptation itself.
- Lorestrom's tool names, node-key rule, statuses and limits are vendored in
  `scripts/lorestrom_backend.py` and the tests; re-check them when Lorestrom's MCP schemas
  change.
