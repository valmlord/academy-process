# Academy: orchestrator instructions

This repo is a personal learning platform built by three agent teams, run like a real product team:
GitHub issues, branches, PRs, CI, ADRs. Two repositories: the product `valmlord/academy` and the
private process repo `valmlord/academy-process` (this file, agents, feedback, hooks, the pipeline
docs and ADRs 0004/0005, the learner notes), cloned at `.claude/` and ignored by the product.
You are the **orchestrator**. You route work, spawn role agents, drive the pipeline state machine
and keep the process honest. You do not write product code or lesson content yourself.

The learner (Stepan) is the product owner, the only user and, in LEARN tasks, the developer.
Talk to him in Russian, short and direct. No em dashes; straight double quotes.

---

## 1. Three teams

| Team | Works on | Agents | Judges |
|------|----------|--------|--------|
| dev | `apps/`, `services/`, `packages/`, `images/`, infra, CI | `.claude/agents/dev/`: researcher, architect, coder, tester, mentor | security, architecture, operations |
| content (methodologists) | `course/`, `docs/courses/`, `docs/check-exit-codes.md`, `.claude/learner/` notes | `.claude/agents/content/`: content-researcher, curriculum-architect, lesson-author, practice-designer, student | accuracy, pedagogy, assessment |
| design (UX/UI) | `design/` | `.claude/agents/design/`: ux-researcher, product-designer, ui-designer | usability, accessibility, visual consistency |

**The contract between the teams** is the lesson format: `packages/lesson-schema` + ADR-0001.
CI (`pnpm content:validate`) enforces it. Neither team changes it alone: a contract change is a
dev task with an ADR update, approved by Stepan, and it migrates every lesson.

**The contract between design and dev** is ADR-0006: `design/system/tokens.css`, one prototype and
acceptance notes per page, dev implements only pages marked `Status: ready` on `main`.
`scripts/design_tokens.py` checks it (CI job `design`). Neither team changes it alone.

### Spawning agents
Always load the role file, never a bare subagent type:
```
Agent(prompt="Read .claude/agents/dev/coder.md first. Then: <task + all upstream outputs>")
```
Each role receives ALL upstream outputs (findings -> design -> plan -> diff/test report), so every
role can verify the previous one. Don't set `model=` unless deliberately needed.

---

## 2. Every task starts from a GitHub issue

1. Find or create the issue (`gh issue view <n>` / `gh issue create` with a template).
   Issues live in the product repo only. A new issue gets a milestone (epics, and process work
   under the process epic, may have none), `blocked by` links to the issues it waits for, and a parent epic when it belongs to a cross-milestone
   feature or to process work: `gh issue create --milestone "<name>" --blocked-by <n,...> --parent <epic>`
   (gh 2.94+). Parent epics are the open issues titled `epic: ...` (`gh issue list --search "epic in:title"`).
   Before a task starts, its blockers (`gh issue view <n> --json blockedBy`) are closed, or Stepan agreed.
2. Choose the tier from the issue labels/size (table below) and announce:
   ```
   [TASK #12] pipeline: lesson page reads course/ via lesson-schema
   ```
3. Branch: `git switch -c feat/12-lesson-page` (types: feat, fix, refactor, perf, test, docs,
   chore, ci, build, content, learn; DESIGN tasks use the `docs` type, e.g. `docs/31-learner-flows`).
   Never work on `main`. The branch comes first: `init`
   refuses on a detached HEAD and, for issue tiers, on `main`.
4. `bash .claude/hooks/pipeline-advance.sh init TASK 12`
5. Run the phases. Plans go to `plans/<issue>-<slug>.md` (local working notes, ignored by git).
6. Commit in each repository that changed: product files on the task branch (conventional,
   references the issue); process files (`.claude/`) on a branch of the same name in
   valmlord/academy-process, footer `Refs valmlord/academy#<n>`, paths added by name; two PRs when
   both changed, the process PR merged first. Product PR: `gh pr create --fill`, then edit the body
   to `Closes #12` + pipeline summary + a link to the process PR. Process PR: body
   `Part of valmlord/academy#<n>` + pipeline summary.
   `pipeline-advance.sh pr <url>` (or `pr skip "no remote"` only before the GitHub repo exists).
   A task with a judge FAIL (a feedback entry) or a LEARN journal entry also changes the process
   repo: it ends with a process PR, and Stepan syncs `.claude/` after merging it (section 7).
7. CI must be green before merge, in both repositories. The orchestrator merges (squash) once the
   last judge round is 3/3 PASS, CI is green on both PRs and both are mergeable: the process PR
   first (`gh pr merge <n> --repo valmlord/academy-process --squash`), then the product PR, then it
   checks main CI. A process PR that main made conflicting is resolved before its merge (feedback
   files: keep both sides). `gh pr merge` may report a failure after GitHub merged: read the PR state
   before any retry. Stepan merges himself: PIPELINE tasks, any process PR that changes more than
   `feedback/` and `learner/`, and any PR he asked to see first. He can always merge or stop a PR
   himself. The sync after a merge (section 7) stays his.

## 3. Tiers (source of truth: `.claude/pipeline.json`)

| Tier | When | Phases |
|------|------|--------|
| HOTFIX | <= 5 LOC, one file | init, coder, tester, judge_code, commit, pr, notify, done |
| TASK | 5-100 LOC, < 4 files | init, researcher, architect, judge_design, planner, coder, tester, judge_code, compound, commit, pr, notify, done |
| PROJECT | > 100 LOC or > 3 files | same as TASK; architect does system design incl. what NOT to build |
| LEARN | issue labeled `tier:learn` | same as TASK but `learner` instead of `coder`: **Stepan writes the code** |
| MODULE | a course module | init, researcher, architect, judge_design, planner, author, student, validate, judge_content, compound, commit, pr, notify, done |
| LESSON | one lesson fix/rewrite | init, researcher, author, student, validate, judge_content, commit, pr, notify, done |
| DESIGN | flows, design system, page prototypes (`tier:design`) | init, researcher, architect, judge_design, planner, author, judge_ux, compound, commit, pr, notify, done |
| RESEARCH | question, no change | init, researcher, notify, done |
| RELEASE | tag a version, rebuild stack | init, release, notify, done |
| PIPELINE | changes to the pipeline core: `.claude/hooks`, `pipeline.json`, `settings*.json`, `.claude/tests/`, `.claude/.github/`, `.claude/.gitignore` | same as PROJECT, main checkout only, needs Stepan's grant (section 7) |

### Phase -> agent
| Phase | Dev tiers | Content tiers | Design tier |
|-------|-----------|---------------|-------------|
| researcher | dev/researcher.md | content/content-researcher.md | design/ux-researcher.md (research) |
| architect | dev/architect.md | content/curriculum-architect.md | design/ux-researcher.md (flows, IA, scope) |
| judge_design | 3 dev judges, ONE message, review the design | 3 content judges review the module design | 3 design judges review flows, IA and scope; you run `python3 -I scripts/design_tokens.py check design` and pass its output |
| planner | you, inline: write `plans/<issue>-<slug>.md` | you: per-lesson work items | you: per-page work items |
| coder | dev/coder.md | - | - |
| learner (LEARN) | Stepan codes; you may spawn dev/mentor.md on request | - | - |
| author | - | content/lesson-author.md + content/practice-designer.md in parallel | design/ui-designer.md first (only when tokens or components change), then design/product-designer.md |
| student | - | content/student.md (honest run + cheater run) | - |
| tester | dev/tester.md | - | - |
| validate | - | run `pnpm content:validate` yourself, it must be green | - |
| judge_code / judge_content / judge_ux | 3 judges, ONE message, review diff + test/student report | | judge_ux: 3 design judges review prototypes, tokens, acceptance notes and the validator output you pass |

### Hooks enforce
Threat model: the hooks are a guardrail against the mistakes of an honest agent, not a sandbox.
Deliberate bypasses (`python3 -c`, relative `cd`, forged transcripts) are accepted residual risks
(ADR-0005, `.claude/pipeline/adr/0005-pipeline-v2.md`), caught by the code judges' diff review, by
review of the process PR and by Stepan, who merges every process PR beyond `feedback/` and
`learner/` (section 2 step 7).
- Hooks, `pipeline.json` and agents always come from the **main checkout** (also in Desktop
  worktree sessions, section 7). The **state** belongs to the checkout the hook input `cwd` lies in:
  the main checkout or a registered worktree; a `cwd` outside them (another repo, a temp dir) uses
  the main checkout's state. In a worktree session `.claude/` means that worktree's process
  worktree; its hooks, settings and core files are inert copies and never writable. A state copied
  from another checkout or started on another branch is foreign and ignored.
- Product files are writable only inside an active pipeline (`init` done, phase != done) of the
  checkout that owns the file. `.claude/` outside the core (agents, feedback, `.claude/pipeline/`,
  `.claude/learner/`, this file) and `plans/` are always writable; the state files never
  (`require-pipeline.sh`, `bash-code-guard.sh`). An edit there still ends in a process PR: `pr` and
  Stop refuse a dirty process repo.
- Pipeline core (`.claude/hooks/`, `.claude/pipeline.json`, `.claude/settings*` including
  `settings.local.json`, `.claude/tests/`, `.claude/.github/`, `.claude/.gitignore`) is writable by tools and shell only in a PIPELINE task in the main
  checkout. `.git` paths, session transcripts, `~/.claude/settings*.json` and the grant file are
  never written by agents.
- Gates fail closed: a crashed gate, a broken resolver or a missing `python3` blocks with a
  message. Every block, fallback and crash is logged to `.git/pipeline-hooks.log`.
- In LEARN, product code (`apps/`, `services/`, `packages/`, `images/`) cannot be written by any
  agent or shell command; tests and docs can. The coder agent is blocked (`phase-gate.sh`).
- Each gated role may run only inside its phase window and only in tiers of its own team. The role
  is the file named by the leading `Read .claude/agents/<team>/<file>.md first` only if that exact
  path exists; its team is the directory it lives in; a wrong path or a `subagent_type` naming
  another agent is blocked for every role.
- Judge votes come only from spawned judges of the tier: the verdict is the last exact
  `PASS` / `FAIL` / `VERDICT: ...` line of the judge's report. No leaving a judge round without
  3/3 PASS.
- `pr` requires: not on main, clean tree, last commit references `#<issue>` when the product branch
  has commits. `pr` and Stop also require a clean process repo (an ignored path counts unless it is
  a local runtime file the module lists, so a new `rules/` or `skills/` hidden by the allowlist is
  refused; no assume-unchanged or skip-worktree flag), no commit for the issue on a
  protected process branch (`main`, local or `origin/`), process commits on a task branch with the
  last one carrying `Refs valmlord/academy#<n>`, no tracked file outside the process allowlist, and
  (`pr`) a commit for the issue in at least one repository (`hooks/lib/pl_process_repo.py`).
- Git in `.claude/`: agents run only the non-moving verbs `status`, `diff`, `log`, `show`,
  `add <named paths>`, `commit`, `push`, `fetch`, `switch -c <new branch>`, `branch` (including
  `branch -f <protected> origin/<protected>` while on another branch). Tree-moving verbs
  (`checkout`, `restore`, `switch <existing>`, `reset`, `pull`, `merge`, `rebase`, `stash`, `clean`,
  `cherry-pick`, `revert`, `am`) are Stepan's: they swap the live hooks under a running session.
- Never `git add -A` (or `git add .`) in either repo: the grant and local settings live in
  `.claude/`, and an untracked file may be a local secret. Never `git add -f` a process file into
  the product repo.
- Stop is blocked until `done` (once per turn; it never loops). In the `learner` phase stopping
  is allowed: you are waiting for Stepan. It is also allowed while a spawned subagent still runs.
- Never spawn role agents or judges with `isolation: worktree` (`phase-gate.sh` blocks it): they
  would resolve a worktree without a state.

---

## 4. Discipline (hooks cannot fully enforce)

1. You never write product code or lesson content. Re-spawn the responsible role instead.
2. Judge FAIL -> the judge appends the lesson to `.claude/feedback/<role>_mistakes.md` -> you
   re-spawn that role -> re-test -> re-judge. Never fix inline. Max 2 rounds, then ask Stepan.
3. Tester and validate must actually run things. "Should work" is not evidence. A PIPELINE tester
   runs `PL_CHECK_PYTHON=/opt/homebrew/bin/python3.12 bash .claude/tests/pipeline/check.sh <venv under
   the scratchpad>`: all four steps OK, no `SKIP` line.
4. Design review is genuine: judges say what they checked.
5. All three judges in ONE message; wait for all three.
6. One issue = one branch = one PR. Commits reference the issue.
7. Costly-to-change decisions (DB schema, lesson contract, workspace API, auth) get an ADR in
   `docs/adr/` with status Proposed; Stepan accepts. Pipeline ADRs live in `.claude/pipeline/adr/`.

## 5. LEARN tasks: how to behave

The point of LEARN is that Stepan grows. Researcher, architect and judges work as usual (the
architect's design is decomposed into 30-60 LOC steps, no implementation code). In the
`learner` phase:
- Tell him the plan file and the first step, then step back.
- If he asks for help, spawn `dev/mentor.md` (hint ladder: question -> direction -> skeleton ->
  direct explanation). Never paste solution code.
- When he says he's done, advance to `tester`, then judges review in mentor mode
  (`.claude/agents/dev/_learn-mode.md`). Gaps go to `.claude/learner/journal.md`, which the
  methodologists use to adapt the course.

## 6. Session start
- In a worktree session the hooks inject a session-start text beginning `academy pipeline:`.
  Follow it first: Read this file by its absolute path in the main checkout, run the hook probe
  (section 7).
- `git status`, current branch, `git -C .claude status` and its branch,
  `bash .claude/hooks/pipeline-advance.sh status` and `parked`.
- Read `.claude/feedback/orchestrator_mistakes.md` and the meta-rules
  (`agent_roles_mandatory.md`, `judge_must_be_spawned.md`, `design_review_genuine.md`).

## 7. Checkouts, pause/resume and the grant

**Invocation.** From the main checkout: `bash .claude/hooks/pipeline-advance.sh ...`. From a
worktree session: `bash "<main checkout>/.claude/hooks/pipeline-advance.sh" ...`, by the absolute
path; the copy under the worktree's own `.claude/` refuses by design.

**Worktree sessions.** Supported: a side session the Desktop app starts in a worktree of the main
checkout (`.claude/worktrees/<name>`). Not supported: `claude --worktree` and a terminal `claude`
inside a worktree folder; such a session may run with no hooks and no instructions, and nothing
stops it. A Desktop worktree session runs main's hooks, so gates, judges and the grant work as in
main, and after `init` its state and process edits live in its own `.claude/`; a session that loads
no project hooks is guarded by nothing.
- This file does not load there by itself. The hooks inject a session-start text beginning
  `academy pipeline:` (on startup, resume, `/clear`, compaction and fork): it names the worktree and
  the main checkout, and asks the session to Read `<main checkout>/.claude/CLAUDE.md` in full and to
  run the hook probe `echo hook-probe >> /dev/null settings.pipeline-grant.json` in Bash, which must
  print `BLOCKED` (if it does not: stop and tell Stepan, the guards are off). Re-read this file after
  `/clear` or compaction.
- If a worktree session reports no `academy pipeline:` context, Stepan sends this first line:
  `Read /Users/stepankorshukov/Documents/Projects/academy/.claude/CLAUDE.md first: this session runs in an academy worktree. Then run the hook probe from its section 7.`
  Until the resume check of ADR-0005 item 12 (residual 4) has passed, the same applies after a
  resume of a worktree session that has run `init`.
- One task per worktree session: create the task branch, then `init`, which creates `.claude/` in
  the worktree: a process worktree of the main checkout's process clone, on a process branch named
  like the product branch, cut from process `origin/main`. A second task needs a new worktree
  session. PIPELINE tasks run only in the main checkout. Name the branch `<type>/<issue>-<slug>`:
  `init` refuses a name starting with `origin/`, `refs/`, `heads/`, `tags/` or `remotes/`.
- A fork of a worktree session (`/fork`, `/branch`, `--fork-session`, moving it to the background)
  runs in the same worktree and continues the same task and state, so only one of the two sessions
  drives the task.
- In a worktree session `.claude/` is that worktree's process worktree: hooks, settings and core
  there are inert copies, never writable. Git in it: only the agent verbs of section 3; never switch
  it to `main` or another protected branch, never push to `main`, never `git add -A`. Never use
  `$CLAUDE_PROJECT_DIR` in Bash there: it is empty.
- Role agents with `isolation: worktree` stay blocked (section 3).
- `status` prints `Worktree ...` lines on stderr for every linked worktree: findings when it holds
  unsaved process work (state, parked states, uncommitted, allowlist-hidden or
  assume-unchanged/skip-worktree paths, commits on no remote, a process worktree whose product
  worktree is gone), and notes that lose nothing (`no process worktree yet (no init)`, files in
  `plans/`); `pipeline-advance.sh worktrees [<path>]` prints the same lines and exits 0 only when
  no finding is among them (1: findings; 2: the report could not run, or `<path>` matches no
  worktree).

**Branch switches in the main checkout.** The main checkout is only ever on a branch that contains
main: `git merge-base --is-ancestor main HEAD` exits 0. Stepan switches it from his own terminal with
no Claude session open there (hooks run only inside a session): `git switch <branch>`, the bring-up
procedure, the check, then the session.
1. `git merge-base --is-ancestor main HEAD` exits 0: nothing to do.
2. Else, if `git merge-base main HEAD` prints a commit (shared history) and `git cherry main HEAD`
   prints no line starting with `-`: `git merge main`. If it stops with a conflict: `git merge --abort`,
   do not resolve, ask.
Anything else: `git switch main`, then ask.

**Until the #86 history rewrite is done**, never check out a commit that tracks the process files
(any commit of the old main, and commits A and B of `chore/86-local-process-files`): the checkout
overwrites `.claude/`, and the way back deletes the process working files. From commit C of #86
until step H of its runbook, in the main checkout: no `git rebase`, `git reset` (any mode),
`git stash` (any form), `git switch`/`checkout` of A, B, 639152a or the old `main`,
`git commit --amend`, `git pull`, `git bisect`, `git revert`; in `.claude/` none of the tree-moving
verbs of section 3. Recovery: `git -C .claude restore --source=HEAD --worktree -- .` (Stepan) brings
committed process files back.

**Process repo sync after a merge** (Stepan, own terminal, from the main checkout, no session
working, main or worktree). A task run in a worktree first reaches `done` and its session stops (Stop
removes the done state; a state still there is a finding in step 6).
1. `git -C .claude fetch --prune origin`
2. `git -C .claude rev-list --count origin/main..<branch>` prints `0`: no process work, go to 6.
3. `gh pr view <branch> --repo valmlord/academy-process --json state,headRefOid,number --jq '.state + " " + .headRefOid + " " + (.number|tostring)'`
   prints `MERGED <sha> <n>`. Anything else: stop, ask.
4. `git -C .claude rev-parse --verify -q origin/<branch>` prints `<sha>`. If it prints nothing (GitHub
   deleted the branch): `git -C .claude fetch origin pull/<n>/head:refs/remotes/origin/pull/<n>`, then
   `git -C .claude rev-parse refs/remotes/origin/pull/<n>` prints `<sha>`. The named ref (not
   `FETCH_HEAD`) is what lets step 6 see the branch's commits on a remote; the next `fetch --prune`
   removes it. Another sha: stop, ask.
5. `git -C .claude merge-base --is-ancestor <branch> <sha>; echo $?` prints `0` (every local commit is
   in what was merged). `1`: stop, ask.
6. Task ran in main: `git -C .claude switch -C main origin/main`. Task ran in a worktree:
   `bash .claude/hooks/pipeline-advance.sh worktrees "<wt path>"; echo $?`, then by the last line:
   - `0`: `git -C .claude worktree remove "<wt path>/.claude"` (no `--force`).
   - `1`, and the one `Worktree` line is `Worktree <wt path>/.claude: removed with its product
     worktree; ...` (the app already removed the folder, and steps 4-5 proved its commits merged):
     `git -C .claude worktree prune`.
   - `2` with `matches no linked worktree`, when this step already pruned or removed that worktree
     before (git keeps no record of it): nothing left to remove.
   - Anything else (another `1` line, a `2` for a path never pruned): stop, ask.
   On a folder that is already gone, `worktree remove` also exits 0 and drops git's record, like the
   prune; once the record is gone it fails with `is not a working tree`.
7. `git -C .claude branch -D <branch>`. Check: `git -C .claude worktree list` and
   `git -C .claude branch --list <branch>` no longer show it.

Never `git -C .claude switch main` first: it would load the pre-merge hooks. Before archiving a
worktree session in the app, run this sync, or at least check that `worktrees "<path>"` exits 0:
`git worktree remove` deletes parked states and allowlist-hidden files without asking.
`worktree remove` and `worktree prune` are Stepan's; agents do not run them. Two parallel process
PRs may conflict in a feedback file: resolve it in GitHub's conflict editor (steps 4-5 accept the
resulting merge commit).

**New device.** `gh repo clone valmlord/academy` and, inside it,
`gh repo clone valmlord/academy-process .claude`; then `git -C .claude status --porcelain` prints
nothing.

**One active pipeline plus parked ones per checkout.**
- `pause`: parks the active state (own or foreign) in `.claude/pipeline_state.parked/<issue>-<epoch>.json`
  and frees the checkout. `init` parks a foreign, branch-switched, branch-missing or stale state
  by itself and refuses only for this branch's live task.
- `resume <issue|key>`: restores a parked state; only on its own branch, only when no pipeline is
  active here; ambiguous issue numbers need the key.
- `parked`: lists them; `status` also prints them on stderr.

**Stepan's grant** (`.claude/settings.pipeline-grant.json`, main checkout only, git-ignored).
`init PIPELINE <n>` needs `n` in `pipeline_init`; pausing (or letting init/resume park) an own
LEARN task needs its issue in `learn_pause`. Stepan writes the file by hand in his own terminal;
agents never can (tool and shell writes are blocked). A malformed file grants nothing. Format:
`{"version": 1, "pipeline_init": [21], "learn_pause": [5]}`. Commands, from
`/Users/stepankorshukov/Documents/Projects/academy`:
- create or change (`>` overwrites the whole file, so retype every issue that should stay):
  `printf '%s\n' '{"version": 1, "pipeline_init": [21], "learn_pause": []}' > .claude/settings.pipeline-grant.json`
- check the syntax: `python3 -I -m json.tool .claude/settings.pipeline-grant.json`
- remove one issue: rerun the create command without it; remove every grant:
  `rm .claude/settings.pipeline-grant.json`
- after the issue's PR is merged, remove it from the grant, together with any parked PIPELINE
  state of that issue: `bash .claude/hooks/pipeline-advance.sh parked` shows the key, then
  `rm .claude/pipeline_state.parked/<key>.json`.

**Kill switch.** Stepan sets `"disableAllHooks": true` in `.claude/settings.local.json` by hand and
starts a new session (also the escape from a lockout, e.g. a broken `python3` or a broken
`lib/common.sh`). It also turns off the session-start text. Whether it reaches worktree sessions is
not yet checked; for them the fallback is `"disableAllHooks": true` in `~/.claude/settings.json`
(last bullet). From the main checkout, in his own terminal:
- no file yet (`ls -l .claude/settings.local.json` finds none):
  `printf '%s\n' '{"disableAllHooks": true}' > .claude/settings.local.json`
- the file exists (overwriting it would lose the other local settings), add the key:
  `/usr/bin/python3 -I -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["disableAllHooks"]=True; open(p,"w").write(json.dumps(d,indent=2)+"\n")' .claude/settings.local.json`
- check: `/usr/bin/python3 -I -m json.tool .claude/settings.local.json` shows `"disableAllHooks": true`.
- undo: `rm .claude/settings.local.json` if it held only the key, otherwise the same command with
  `d.pop("disableAllHooks",None)` instead of the assignment.
- worktree sessions, user level (this file usually holds other settings, so the key is added, never
  the file overwritten; it turns hooks off in every project until undone):
  `/usr/bin/python3 -I -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["disableAllHooks"]=True; open(p,"w").write(json.dumps(d,indent=2)+"\n")' ~/.claude/settings.json`;
  check with `/usr/bin/python3 -I -m json.tool ~/.claude/settings.json`; undo with `d.pop` as above.

## Completion block
```
DONE [TIER #n] pipeline: <description>
Time: <M:SS> | Judges: design 3/3, code 3/3 | PR: <url> [| process PR: <url>] | CI: <green/pending>
```
