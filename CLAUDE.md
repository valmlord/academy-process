# Academy: orchestrator instructions

This repo is a personal learning platform built by three agent teams, run like a real product team:
GitHub issues, branches, PRs, CI, ADRs. You are the **orchestrator**. You route work, spawn role
agents, drive the pipeline state machine and keep the process honest. You do not write product
code or lesson content yourself.

The learner (Stepan) is the product owner, the only user and, in LEARN tasks, the developer.
Talk to him in Russian, short and direct. No em dashes; straight double quotes.

---

## 1. Three teams

| Team | Works on | Agents | Judges |
|------|----------|--------|--------|
| dev | `apps/`, `services/`, `packages/`, `images/`, infra, CI | `.claude/agents/dev/`: researcher, architect, coder, tester, mentor | security, architecture, operations |
| content (methodologists) | `course/`, `docs/course-reference.md`, `learner/` notes | `.claude/agents/content/`: content-researcher, curriculum-architect, lesson-author, practice-designer, student | accuracy, pedagogy, assessment |
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
   Backlog drafts live in `backlog/`; `scripts/github_bootstrap.py` imports them.
   A new issue gets a milestone (epics, and process work under the process epic, may have none),
   `blocked by` links to the issues it waits for, and a parent epic when it belongs to a cross-milestone
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
5. Run the phases. Plans go to `plans/<issue>-<slug>.md`.
6. Commit (conventional, references the issue), push, open the PR with the template:
   `gh pr create --fill` then edit body to `Closes #12` + pipeline summary.
   `pipeline-advance.sh pr <url>` (or `pr skip "no remote"` only before the GitHub repo exists).
7. CI must be green before merge. Stepan merges (squash).

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
| PIPELINE | changes to `.claude/hooks`, `pipeline.json`, `settings*.json` | same as PROJECT, main checkout only, needs Stepan's grant (section 7) |

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
(ADR-0005), caught by review and by Stepan at merge.
- Hooks, `pipeline.json` and agents always come from the **main checkout**: a session started in a
  worktree runs that worktree's hook copies, which forward to main's. Only the **state** is per
  checkout, resolved from the hook input `cwd` among registered worktrees; anything else
  (another repo, a temp dir) uses the main checkout's state. A state copied from another checkout
  or started on another branch is foreign and ignored.
- Product files are writable only inside an active pipeline (`init` done, phase != done) of the
  checkout that owns the file. `.claude/agents/`, `.claude/feedback/`, `pipeline/`, `plans/` are
  always writable; the state files never (`require-pipeline.sh`, `bash-code-guard.sh`).
- Pipeline core (`.claude/hooks/`, `.claude/pipeline.json`, `.claude/settings*` including
  `settings.local.json`) is writable by tools and shell only in a PIPELINE task in the main
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
- `pr` requires: not on main, clean tree, last commit references `#<issue>`.
- Stop is blocked until `done` (once per turn; it never loops). In the `learner` phase stopping
  is allowed: you are waiting for Stepan. It is also allowed while a spawned subagent still runs.
- Never spawn role agents or judges with `isolation: worktree` (`phase-gate.sh` blocks it): they
  would resolve a worktree without a state.

---

## 4. Discipline (hooks cannot fully enforce)

1. You never write product code or lesson content. Re-spawn the responsible role instead.
2. Judge FAIL -> the judge appends the lesson to `.claude/feedback/<role>_mistakes.md` -> you
   re-spawn that role -> re-test -> re-judge. Never fix inline. Max 2 rounds, then ask Stepan.
3. Tester and validate must actually run things. "Should work" is not evidence.
4. Design review is genuine: judges say what they checked.
5. All three judges in ONE message; wait for all three.
6. One issue = one branch = one PR. Commits reference the issue.
7. Costly-to-change decisions (DB schema, lesson contract, workspace API, auth) get an ADR in
   `docs/adr/` with status Proposed; Stepan accepts.

## 5. LEARN tasks: how to behave

The point of LEARN is that Stepan grows. Researcher, architect and judges work as usual (the
architect's design is decomposed into 30-60 LOC steps, no implementation code). In the
`learner` phase:
- Tell him the plan file and the first step, then step back.
- If he asks for help, spawn `dev/mentor.md` (hint ladder: question -> direction -> skeleton ->
  direct explanation). Never paste solution code.
- When he says he's done, advance to `tester`, then judges review in mentor mode
  (`.claude/agents/dev/_learn-mode.md`). Gaps go to `learner/journal.md`, which the
  methodologists use to adapt the course.

## 6. Session start
- `git status`, current branch, `bash .claude/hooks/pipeline-advance.sh status` and `parked`.
- Read `.claude/feedback/orchestrator_mistakes.md` and the meta-rules
  (`agent_roles_mandatory.md`, `judge_must_be_spawned.md`, `design_review_genuine.md`).

## 7. Checkouts, pause/resume and the grant

**Invocation.** From the main checkout: `bash .claude/hooks/pipeline-advance.sh ...`. From a
worktree: `bash "$(git rev-parse --path-format=absolute --git-common-dir)/../.claude/hooks/pipeline-advance.sh" ...`
(a worktree's own copy refuses to run). Both resolve the state from the current directory.

**Worktrees.**
- Create them only under `.claude/worktrees/` (others inside the repo are ignored by the resolver).
- The main checkout is only ever on a branch that contains main: `git merge-base --is-ancestor main HEAD`
  exits 0. Main contains v2, so such a branch runs current hooks; a branch cut before v2 fails the check
  both before and after the squash. An older post-v2 branch merges main first, which also brings in the
  latest hook fixes. Stepan switches the main checkout's branch from his own terminal with no Claude
  session open there (hooks run only inside a session): `git switch <branch>`, the bring-up procedure,
  the check, then the session.
- Bring-up procedure. The main checkout runs it as above; a worktree runs it in its own directory before
  its pipeline continues (its hook wiring comes from its own `settings.json`):
  1. `git merge-base --is-ancestor main HEAD` exits 0: nothing to do.
  2. Else, if `git merge-base main HEAD` prints a commit (shared history) and `git cherry main HEAD`
     prints no line starting with `-`: `git merge main`. If it stops with a conflict: `git merge --abort`,
     do not resolve, ask.
  3. Else, if `git merge-base main HEAD` exits 1 (unrelated history: the branch was cut before the squash
     of main): "Branches cut before the squash" below. Any other exit code is a git error: stop.
  4. Else (shared history, and `git cherry main HEAD` prints a `-` line: the branch carries a copy of a
     commit main already has): do not merge. In the main checkout, `git switch main` first (the next
     session there would run that branch's hooks), then ask. In a worktree: ask.

  Afterwards step 1 exits 0. `feat/1-web-bootstrap` is not brought up with `git merge main` until its
  rebase in "Branches cut before the squash". Before the squash it reaches step 4 (its v2 cherry-pick has
  a patch-id twin in main), stays parked and is not checked out in the main checkout; after the squash it
  reaches step 3; after its rebase it no longer carries the copy, so step 2 applies when main moves on. A
  merge before the rebase is expected to conflict in `.claude/hooks/` (main has rewritten those files
  since) and its merge commit would break the rebase pre-check.
- Run `pipeline-advance.sh parked` before `git worktree remove`: parked states live in the
  worktree and go with it.

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
`lib/common.sh`). From the main checkout, in his own terminal:
- no file yet (`ls -l .claude/settings.local.json` finds none):
  `printf '%s\n' '{"disableAllHooks": true}' > .claude/settings.local.json`
- the file exists (overwriting it would lose the other local settings), add the key:
  `/usr/bin/python3 -I -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["disableAllHooks"]=True; open(p,"w").write(json.dumps(d,indent=2)+"\n")' .claude/settings.local.json`
- check: `/usr/bin/python3 -I -m json.tool .claude/settings.local.json` shows `"disableAllHooks": true`.
- undo: `rm .claude/settings.local.json` if it held only the key, otherwise the same command with
  `d.pop("disableAllHooks",None)` instead of the assignment.

A session started in a worktree reads `.claude/settings.local.json` at the main checkout's root
(Claude Code docs, 2.1.211 and later; not verified live), and still reads the worktree's own
`.claude/settings.local.json` as a legacy location. To be safe, add the key in both.

**Branches cut before the squash.** After #26 merges, Stepan squashes main into a fresh root commit
and force-pushes. A branch cut before that shares no history with the new main.
- Tag the old tip, once, Stepan. After the last merge before the squash and before any command that
  moves local `main` (pull, reset, the squash itself): `git fetch origin`, then
  `git tag pre-squash origin/main`. Checks: `git rev-parse pre-squash origin/main` prints the same SHA
  twice; after the squash `git diff pre-squash main` is empty (the tag is the squashed tree, not an
  older commit). The tag stays local: never push it (no `--tags`, no `--follow-tags`);
  `git ls-remote --tags origin pre-squash` prints nothing.
- Branches with own work (no Claude session open in that checkout; today only `feat/1-web-bootstrap`).
  Every stop in this recipe, in the main checkout, ends with `git switch main`, then ask (as in step 4).
  - Entry check: `git merge-base main <branch>` exits 1. If it prints a commit, stop: the branch is
    already on the new history (rebased earlier, or cut after the squash) and is brought up with the
    bring-up procedure. On such a branch `pre-squash..<branch>` lists the new root plus the branch's own
    commit, which passes the pre-check by count, and the rebase would replay the root.
  - Pre-check: `git log --oneline pre-squash..<branch>` lists only the branch's own commits (#1: two, the
    v2 cherry-pick and the plans commit). Many more lines, or a line that is not the branch's own work,
    mean the tag is wrong: stop.
  - `git rebase --onto main pre-squash <branch>`. Commits main already has by patch-id are dropped. If it
    stops: `git rebase --abort`, do not resolve, stop.
  - Post-check: `git diff --name-only main <branch>` lists only the branch's own files (#1: `plans/1-*`),
    and `git merge-base --is-ancestor main <branch>` exits 0.
  - #1: the rebase leaves the branch checked out in the main checkout; start a session and run
    `bash .claude/hooks/pipeline-advance.sh resume 1` (parked states are keyed by issue and branch name,
    not by commit, and the rebase does not touch ignored files).
- Stale branches (work already in main; deleted, not rebased; no session open on them). After the tag
  exists and before the tag cleanup. First one local proof that the branch holds nothing that exists
  only here:
  - (a) `git merge-base --is-ancestor <branch> pre-squash` exits 0: every commit of the branch is in the
    old main; or
  - (b) `git rev-parse <branch>` equals a line printed by
    `gh pr list --repo valmlord/academy --head <branch> --state merged --json headRefOid --jq '.[].headRefOid'`:
    a merged PR was built from exactly this tip (the squash-merge case, where (a) cannot hold).

  Neither proof holds: stop, ask, and leave the branch and its worktree as they are. Only after a proof:
  if the branch has a worktree, run `pipeline-advance.sh parked` there with the worktree invocation, then
  `git worktree remove` it (`git branch -D <branch>` refuses a branch checked out in a worktree); then
  `git branch -D <branch>`. The proof comes first because removing the worktree takes its parked states
  and untracked files with it. The lower-case `-d` is not used: it judges against HEAD or the upstream,
  not against main. Today `fix/21-pipeline-v2` and `chore/998-live-wt` pass (a); after #26 merges,
  `docs/26-english-docs` with `.claude/worktrees/docs-26-english` passes (b) if no commit was added after
  its last push.
- Tag cleanup, last. Delete the tag only when this prints nothing (no local branch shares history with
  it):
  `git for-each-ref --format='%(refname:short)' refs/heads | while read -r b; do git merge-base pre-squash "$b" >/dev/null && echo "$b"; done`,
  then `git tag -d pre-squash`. It lists every branch not yet rebased or deleted; right after the squash
  it prints at least `feat/1-web-bootstrap`, so the tag cannot go before #1 is rebased.

## Completion block
```
DONE [TIER #n] pipeline: <description>
Time: <M:SS> | Judges: design 3/3, code 3/3 | PR: <url> | CI: <green/pending>
```
