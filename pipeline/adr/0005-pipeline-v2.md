# ADR-0005: Pipeline v2 mechanics and trust boundaries

- Status: Proposed
- Date: 2026-10-27
- Issue: #21
- Amended: #23 (items 6, 7, 8 and 9); #27 (item 10); #86 (item 11, Proposed); #89 (item 12, Proposed)

## Context
Pipeline v1 assumed one checkout. With git worktrees (#15) every hook still read the main
checkout's state, a state copied into a new worktree unlocked writes there, files of a nested
worktree matched the always-writable `.claude/*` rule, judge votes went missing when the
SubagentStop transcript lagged (#1), state writes were unlocked read-modify-writes, and a crashing
hook failed open (any exit code other than 2 lets the tool call proceed). Facts and Stepan's
decisions 1-7: `plans/21-pipeline-v2-research.md`; full design: `plans/21-pipeline-v2-design.md`.

## Decision
1. **Threat model.** The pipeline is a guardrail against the mistakes of an honest, cooperating
   agent, not a sandbox against deliberate subversion. A mechanism stays when it also stops a
   plausible accident or costs a few lines; machinery that only defends against deliberate action
   is not built. Judges evaluate pipeline changes against this model.
2. **Code from main, state per checkout.** Hooks, `pipeline.json` and agents always come from the
   main checkout; a linked worktree's hook copy only forwards to main's script of the same name.
   The state is per checkout, located from the hook input `cwd` among the worktrees git lists;
   linked worktrees count only outside the main tree or under `.claude/worktrees/`. Anything else
   falls back to the main checkout. A state is own when its `gitdir_at_init` matches (legacy:
   its `branch_at_init`); a foreign state is ignored by every gate.
3. **Parked states.** One active state plus parked ones per checkout, in
   `.claude/pipeline_state.parked/<issue>-<epoch>.json` (`-2`, `-3` on collision). `init` parks
   instead of deleting; `pause` / `resume` move states explicitly. All writes are flock
   transactions with atomic replace.
4. **PIPELINE tier.** The only tier that may write pipeline core (`.claude/hooks/`,
   `.claude/pipeline.json`, `.claude/settings*`, which includes `settings.local.json`), by tool or
   shell, and only in the main checkout (its hooks are the only live ones). `init PIPELINE <n>` and
   parking an own LEARN task need a grant Stepan writes by hand in
   `.claude/settings.pipeline-grant.json` (main checkout); agents can never write that file.
5. **Fail closed, fail quiet.** Gates map every unexpected exit code to a block and block when
   `python3` is missing or the resolver fails; observers always exit 0, so a judge is never
   trapped. All Python runs as `python3 -I`.
6. **Hook log** in `<main git dir>/pipeline-hooks.log`, JSON lines, bounded with one rotation,
   opened with `O_NOFOLLOW`, a whitelist of fields (never commands, file contents or messages). It
   has no authority: no gate reads it. Since #23 the whitelist includes `error`: the first line of
   the output of a vote or spawn-map CLI call that failed (stdout and stderr combined), capped at
   200 characters. It may contain absolute paths, never a command, file content or handback
   message.
7. **Accepted residual risks** (deliberate bypass only; caught by review and by Stepan at merge):
   - a worktree registered inside main's tree on an orphan branch: inert for resolution, and main's
     zones are checked as absolute paths first; `git worktree add` is not treated as a write verb;
   - shell evasion of bash-code-guard: `python3 -c`, variables, and relative paths. A relative `cd`
     evades the LEARN rule **and** the core, grant-file and user-settings shell strings, which
     match path text only, e.g. `cd .claude && echo x >> hooks/x.sh`;
   - write verbs outside bash-code-guard's list pass: `find .claude/hooks -delete`,
     `rsync -a --delete x/ .claude/hooks/`, `git clean -fdx .claude`, `tar -C .claude -xf x.tar`. So
     do spellings that hide a core name from a string match: `./` and `..` path segments
     (`rm -rf .claude/./hooks`, `rm -rf .claude/agents/../hooks`, and
     `printf x > .claude/./settings.local.json`, which reaches the kill-switch file), quotes or a
     backslash inside a name (`.claude/h""ooks`, `.claude/h''ooks`, `.claude/h\ooks`), a brace
     that splits the name (`.cla{ude,}/hooks`), a variable (`d=.claude; rm -rf $d/hooks`) and
     `cd .claude && rm -rf hooks`. Since #23, `.claude//hooks`, `.claude/{hooks,}`,
     `.claude/h{ooks,}` and `mv .claude, x` are blocked. Accepted false positive of the same rule:
     `rm -rf .claude/{agents,feedback}/x` is blocked too. Each spelling was run through the guard
     once (#23 test report);
   - transcript forgery through the shell;
   - `JUDGE_HOOK_CALLER` set by indirection: vote authenticity is an env flag plus a transcript
     role, not cryptographic;
   - `cd` into a sibling registered worktree to pick a permissive state for spawns, votes or Stop;
   - a planted log file (no ownership check);
   - a deliberately replaced registered worktree directory with a valid-looking `.git` file;
   - a pre-v2 worktree session runs v1 hooks until it merges main;
   - a harness kill at the hook timeout fails open;
   - a PIPELINE agent with an open grant could edit core beyond its issue's scope.
8. **`transcript_path` inside a subagent.** Answered by the live check L3: inside a subagent, the
   `PreToolUse(SubagentHandback)` hook received the parent session's `transcript_path`, and the
   subagent's own transcript was found at `<session dir>/subagents/agent-<id>.jsonl`
   (`transcript_kind=main`, `role_source=transcript`; hook log 2026-10-27 20:23:49 and 20:23:56,
   Claude Code 2.1.267). The handback path still tries the other layouts as fallbacks and logs
   `transcript_kind`.
9. **Shared library and gate scripts (#23).** The last line of `lib/common.sh` sets a sentinel that
   every hook checks after sourcing it: a syntax error stops the source early, and the hook would
   otherwise exit 127, which does not block. Without it the PreToolUse gates exit 2, observers 0,
   the CLI 1. The gates' decision code lives in `lib/pl_write_gate.py` and `lib/pl_shell_guard.py`;
   rc 2 counts as a verdict only when stdout carries the `\x1f` separator, because CPython also
   exits 2 when it cannot open a script, so an unopenable gate script is a crash, i.e. a block. The
   Stop gate (`phase-complete.sh`) instead warns and allows when it cannot evaluate (no
   `common.sh`, no usable python3, a resolver failure): a Stop block that nothing can repair only
   re-prompts the session. A crash inside its own checks still blocks every Stop (residual).
   `lib/cfg.py` validates `pipeline.json` on every load, every tier included (active or not): a
   tier's `team` must be a string and its three flags exactly `true`/`false`. Anything else is a
   crash of both PreToolUse gates, i.e. every write and command blocked, rather than a string
   `"false"` read as true; the way out is fixing the file by hand or the kill switch.
10. **Team of a role (#27).** The role of a spawn is the agent file named by the prompt's leading
    `Read .claude/agents/<dir>/<file>.md first` only when that exact path (directory and case) exists
    in the main checkout's agent tree, and its team is the directory the file lives in. A prompt naming
    a path that does not exist, or a `subagent_type` naming a known agent other than the prompt's role,
    is denied for every role (`role-path`, `role-type`), and such a judge's vote never counts. A gated
    role may be spawned only in a tier whose `team` equals its team; a tier without a team refuses
    gated roles. An unreadable or empty agent tree, or a `.md` under `.claude/agents/` that is not a
    `<team>/<file>.md` with lower-case names (files starting with `_` excepted; Claude Code registers
    agents recursively), blocks role spawns (fail closed). Agent names and basenames are unique across
    directories (CI, `tests/pipeline/run.sh` S1); judges are bound by the tier's judge list. Residual
    risk accepted as for items 1-9: a deliberate bypass (a prompt without the leading `Read` line and no
    `subagent_type`) is not a role spawn and is caught by review.

11. **Process repository (#86, amendment, status Proposed; Stepan accepts).** The process files
    (this ADR, `.claude/CLAUDE.md`, agents, feedback, hooks, `pipeline.json`, settings, the self-test,
    the learner notes) are the private repository `valmlord/academy-process`, cloned at the product's
    `.claude/` in the main checkout, which the product ignores as a whole; a linked worktree's
    `.claude/` is a worktree of that clone (item 12). Its `.gitignore` is an allowlist, so runtime
    files (state, parked states, flock, grant, `settings.local.json`, `worktrees/`) stay untracked.
    Every process change is a commit on a branch named like the product branch, footer
    `Refs valmlord/academy#<n>`, a process PR with CI (`tests/pipeline/check.sh`), merged by Stepan
    before the product PR. "Caught by review and by Stepan at merge" (item 7) now means the process
    PR. `pr` and Stop at `done` refuse a dirty process repo (untracked files listed whatever
    `status.showUntrackedFiles` says), an ignored path that is not on the module's local runtime list
    (state, lock, parked states, grant, `settings.local.json`, `worktrees/`, `.DS_Store`,
    `__pycache__/` while it holds only regular `*.pyc` files, walked without following symlinks: so a
    new `rules/`, `skills/` or `commands/` hidden by the allowlist's `/*`, or an agent file inside an
    `agents/**/__pycache__/`, is refused), a mode change on a tracked file whatever `core.fileMode`
    says, a tracked file flagged assume-unchanged or skip-worktree, a commit for the issue (process footer or
    `Refs #<n>`) reachable from a local or remote-tracking protected process branch, process commits on
    a detached or unpushed protected HEAD, a last process commit without the footer, a tracked file
    outside the allowlist, and (`pr`) a task with no commit in either repository
    (`hooks/lib/pl_process_repo.py`). In the main checkout, a missing `.claude/.git` skips these
    rules with a log line, and a `.git` that is not a directory and any git error refuse; a linked
    worktree's layout is checked as item 12 says. Residual risks, accepted:
    1. A CLI session in a `git worktree add` checkout loads no hooks (the worktree has no
       `.claude/`); only Stepan's habit of working in the main checkout stops it. For worktree
       sessions since #89: item 12, residual 1.
    2. Tree-moving git verbs in `.claude/` (`checkout`, `restore`, `switch <existing>`, `reset`,
       `pull`, `merge`, `rebase`, `stash`, `clean`) swap the live hooks under a running session: a
       rule in `.claude/CLAUDE.md` section 3, no guard. The shell guard's write-verb list does not see
       `git -C .claude checkout <ref> -- <path>` or `git -C .claude restore ...` (no write verb next to
       `git`, no core path in the string); the same class as the relative `cd` of item 7.
    3. `core.fsmonitor` (or another command-running config) set with `git -C .claude config` runs
       code in every later git call there; the process-repo rules pass `-c core.fsmonitor=false`
       (and `-c core.fileMode=true`, so a lost exec bit is not hidden), other git calls do not.
    4. A product checkout across #86 (a commit that tracks the process files) deletes the process
       working files until they are restored from the process repo
       (`git -C .claude restore --source=HEAD --worktree -- .`); uncommitted edits are lost.
    5. `.claude/CLAUDE.md`, this ADR and the agent files are under the open `.claude/` prefix,
       writable with no active pipeline (the root `CLAUDE.md` needed one), and so is any new path
       there (`rules/`, `skills/`, `commands/`), which Claude Code may load as instructions. The
       dirty-repo rule turns each such edit into a process PR at the next `pr` or Stop at `done`:
       a tracked path shows as changed, a new path as untracked or, when the allowlist's `/*` hides
       it, as an ignored path off the local runtime list. An edit made and removed again between two
       gates, or made in a session that never reaches `pr` or Stop at `done`, is not seen. The commit phase pushes the process branch
       before `pr` runs, so a force-added runtime file (`git add -f settings.local.json`) reaches the
       private repo's task branch before the tracked-file rule refuses it; Stepan then deletes that
       branch and rotates anything secret the file held.
    6. Process `main` has no branch protection (private repository, free plan). The gates refuse an
       issue commit on it; a push outside any task, and a process commit on `main` that carries
       neither `Refs valmlord/academy#<n>` nor `Refs #<n>`, once `main` is pushed or HEAD has left
       `main`, are seen only by Stepan (while HEAD is on an unpushed `main`, the gates refuse it).

12. **Worktree sessions (#89, amendment, status Proposed; Stepan accepts).** A Desktop worktree side
    session works in a linked product worktree `{wt}` under `{main}/.claude/worktrees/`, with its own
    task, pipeline state, judges and process PR. It extends item 2 (state per checkout) and item 11
    (the process clone); design: `plans/89-worktree-process-design.md`.
    - **Layout.** The worktree's state and process files live in `{wt}/.claude`, a `git worktree` of
      the main checkout's process clone `{main}/.claude`, on a process branch named like the product
      branch, cut from process `origin/main` with `--no-track`, so a bare `git push` cannot land on
      `main`. State paths stay `{root}/.claude/...`: the resolver and the gates do not change. Hooks,
      `pipeline.json`, agents, the grant and the hook wiring keep coming from main.
    - **Creation at init.** `pipeline-advance.sh init` in the worktree creates it before taking the
      state lock (`hooks/lib/pl_process_worktree.py`), with the process repo's own hooks switched off
      (`core.hooksPath=/dev/null`), or re-checks one an earlier init left. It refuses a protected product
      branch, a `.claude` that is a file, a symlink or not such a worktree, a process worktree on
      another branch, a process branch tracking a protected branch, and a half-created worktree (lock
      left behind or tracked files missing); an existing process branch is reused with a warning. The
      upstream check reads every spelling of `branch.<b>.merge` (`main`, `refs/heads/main`, any
      remote), and a product branch name that would shadow another ref in the process clone (first
      component `origin`, `refs`, `heads`, `tags` or `remotes`, or `HEAD`) is refused; new process
      branches start at the full `refs/remotes/origin/main`.
      PIPELINE runs only in the main checkout and is refused before anything is created.
    - **Validation.** In `ensure` and in the process repo rules alike, `{wt}/.claude/.git` must be a
      regular file naming an admin dir strictly under `{main}/.claude/.git/worktrees/` whose `gitdir`
      file points back at that `.git`. At a linked root, anything else is a refusal of `pr` and Stop,
      never a skip; then every rule of item 11 runs on the process worktree.
    - **Session-start channel.** A worktree session loads no process `CLAUDE.md` (rehearsal R7), but
      main's hooks run in it. A SessionStart entry in main's `settings.json` with no matcher, so all
      five sources (`startup`, `resume`, `clear`, `compact`, `fork`), runs `hooks/session-context.sh`:
      a session in a linked worktree gets a short text (Read `{main}/.claude/CLAUDE.md`, run the hook
      probe, the worktree rules), a main-checkout session gets nothing, a directory under
      `{main}/.claude/worktrees/` that git does not accept gets a short text naming main's `CLAUDE.md`,
      and any failure gets a fixed fallback text plus a log line with its reason. The self-test pins
      the whole hook wiring by exact equality.
    - **Removal.** The app removes worktrees outside any hook, and `git worktree remove` deletes
      ignored files (parked states, allowlist-hidden paths) without asking. `pipeline-advance.sh
      worktrees [<path>]` reports unsaved process work (state, parked states, uncommitted, hidden or
      assume-unchanged/skip-worktree paths, commits on no remote, process worktrees whose product
      worktree is gone; exit 2 when `<path>` matches no worktree), `status` prints
      it, and Stepan removes a process worktree only after `worktrees "<wt>"` exits 0
      (`.claude/CLAUDE.md` section 7). `worktree remove` and `worktree prune` stay his.

    Residual risks, accepted:
    1. A session that loads no project hooks (CLI before init, `claude --worktree` if it loads the
       worktree's settings, manual worktrees outside the accepted places) gets neither gates nor
       instructions. Nothing catches it; the only control is the rule not to start those sessions.
    2. A session with hooks gets the process rules only through the SessionStart injection and its own
       Read of main's `CLAUDE.md`. If it ignores that text, the gates hold and the instruction-only
       rules (git verbs in `.claude/`, never `git add -A`, never fix inline) do not. A context hook
       killed at its 15 s timeout injects nothing, not even the fallback; the gates still hold.
    3. Uncommitted process edits, parked states and `plans/` die when the app removes a worktree
       outside the sync procedure.
    4. Hook wiring after init, not yet observed (live check L5 records which one holds). With
       `forwarded=false`, a Desktop session keeps main's wiring after init. With `forwarded=true`, a
       session that starts or resumes in a worktree after init wires its hooks from that process
       branch's `settings.json`: gate code still comes from main (forwarding), but the injection
       arrives only if the branch was cut after #89 reached process `origin/main` (L5b), and any later
       wiring change in main reaches the worktree only on a newly cut branch. A CLI session in a
       worktree after init behaves the same way.
    5. Hook edits in main are live for every worktree session.
    6. Role prompts `Read .claude/agents/<team>/<file>.md` resolve to `{wt}/.claude/agents` (the
       `origin/main` copy), while `phase-gate` validates main's `.claude/agents`: a role file changed in
       main and not yet merged differs between what is gated and what is read.
    7. After init, `CLAUDE.md`'s relative `.claude/...` references resolve to the process worktree's
       copy; `bash .claude/hooks/pipeline-advance.sh` there refuses by design (`common.sh`) and names
       main's path; `$CLAUDE_PROJECT_DIR` is empty in a worktree session's Bash and is never used in
       Bash commands.

## Alternatives considered
- Dispatch to the resolved checkout's own scripts: an old-commit worktree or a fake `.git`-file
  directory would choose the code that gates main.
- Accept any directory whose git common dir is main's: passed by a fake `.git`-file directory.
- Block every hook in a worktree-started session: worktree sessions are routine; forwarding keeps
  code-from-main with a dozen builtin lines.
- Signed, expiring or consumed grants: they defend only deliberate forgery, which the threat
  model leaves to review.
- Deleting foreign or stale states at init: loses votes and history; parking is cheap.

## Consequences
- Hook edits in a PIPELINE task are live for every session at once, including worktree sessions;
  a broken edit fails closed and the kill switch (`disableAllHooks` in `settings.local.json`, by
  hand) is the way out.
- Every checkout must carry v2 before it runs a pipeline: older branches merge main first.
- Stepan maintains the grant file and removes an issue from it after its PR is merged.
- Pipeline mechanics described in ADR-0004 are superseded in detail by this record.
