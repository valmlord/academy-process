# ADR-0005: Pipeline v2 mechanics and trust boundaries

- Status: Proposed
- Date: 2026-10-27
- Issue: #21
- Amended: #23 (items 6, 7, 8 and 9); #27 (item 10)

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
