# Architect Mistakes

Methodology lessons for designing. Seeded with design-discipline lessons; append new
project-specific ones as they are found.

### Missed a deploy/packaging requirement

Designed a new module without accounting for how it gets packaged/imported/installed in the
target environment; the coder then hit a runtime "module not found".
Rule: Every design that adds a module, directory, or dependency must state how it reaches the
target environment (packaging, import path, install/symlink step). The design review checks this.

### 2026-11-16: Moved graders to another uid but kept the learner's HOME without listing what it feeds (#163, judge_design round 1, security)
Revision 2 runs graders as uid 2000-2003 so that uid 1000 cannot read `checks/`, and keeps `HOME=/workspace/home` (4.2)
for `verify_permissions.py`. HOME and the learner repo copies that module 04 makes hold per-user and per-repo config
of git, node, go and other tools. Some of those settings make the tool run a command of the learner's choosing, so a
grader that only calls git on its own copy can start learner-chosen code as the grader uid. Under uid 1000 that did not
matter; under the new uid the isolation depends on it. Neither R1, ADR-0002 item 12 nor the 19.2 audit names it, and
the contract does not state that `PATH` must hold no learner-writable directory, although the setup script resolves
`tar`, `mktemp`, `rm` and `chmod` through it.
Rule: When a design moves a process to a new trust identity, list every input it still inherits from the old one
(env, HOME, cwd, PATH, config files in copied trees) and, for each, state whether it can make a tool execute code,
then either remove the input or name it as a residual with an owner.

### Designed against assumptions instead of the researcher's facts

Produced a design based on how the system was assumed to work, not on what the researcher
actually found; the design contradicted the real runtime config.
Rule: Design against the researcher's findings. If a needed fact is missing, ask for it - don't
assume.

### Hand-derived a third-party tool's internal behavior from memory

Modeled a library's internal resource accounting from memory rather than its source/docs, and
the imprecise model sent a later fix at the wrong layer.
Rule: When you rely on a third-party tool's internal mechanics, flag the derivation as unverified
and prefer its DOCUMENTED external contract over guessing at internals. An imprecise internal
claim can send the next fix chasing the wrong layer even when the verdict was directionally right.

### 2026-10-27: .dockerignore secret patterns anchored to the context root only

Issue #1 design excluded `.env` and `.env.*` in a root-context `.dockerignore`. Docker anchors
these patterns at the context root, so `apps/web/.env*` (where Next.js loads env files from)
still entered `COPY . .`, and `next build` with `output: "standalone"` copies `apps/web/.env`
and `apps/web/.env.production` into `.next/standalone/apps/web/` (next/dist/build/index.js,
writeStandaloneDirectory) - i.e. into the shipped runner image. The tester check
(`ls -a /app`) only looked at the image root, so it could not fail on this leak.
Rule: Secret patterns in .dockerignore are always depth-agnostic (`**/.env`, `**/.env.*`),
and the image-leak check searches the whole image (`find / -name '.env*'`) after planting a
canary env file in the app directory, so it can actually go red.

### 2026-10-27: Claimed a test guard is "broken once" when the planned negative run cannot reach it

Issue #1 design: the Playwright smoke records same-origin responses >= 400 so it "catches missing
/_next/static", and the failure-mode table says every guard is broken once (tester checks 8, 12).
Check 12 only stops the web container. That turns the test red at `goto` before the >= 400
assertion runs, so it shows nothing about that assertion. A listener attached too late, or an
origin filter that never matches, would leave the static-asset guard always green while the table
reports it as verified.
Rule: For each assertion a test adds, the negative run must break exactly the thing that assertion
guards, with everything else still healthy. Example: the server is healthy but `.next/static` is
removed, and the run turns red on that assertion. Killing the whole service only proves the test
can reach the service.

### 2026-10-27: Negative-run cleanup restores a file with git when the file is part of the pending diff (#1)

Issue #1 design revision 2, tester check 18: `echo >> README.md`, run the dirty-tree script, then
`git checkout README.md`. The same design edits README.md (the "Web app" section), and the tester
runs before the commit phase, so the checkout silently throws away the coder's README work. Check
9b has the same shape: it edits `.dockerignore`, a new untracked file, then relies on `git status`
to prove it was restored; git cannot restore an untracked file and shows `?? .dockerignore` either
way, so the "restored" assertion cannot fail.
Rule: A check that mutates a file to force a red run must restore it from a backup copy taken just
before the mutation (or mutate a file outside the pending diff), and must prove the restore with
`cmp`/`diff` against that backup, never with `git checkout` / `git status` on files the change itself
adds or edits.

### 2026-10-27: Tester shell recipe assumes one persistent bash session (#1)

Issue #1 design revision 3, section 11. The recipe keeps `SCRATCH` and the `fp`/`fp_check` helpers
as shell variables/functions and chains "backup; mutate" with `;`. The tester runs through the Claude
Code Bash tool, which starts a fresh zsh per call: variables and functions are gone in the next call.
With `SCRATCH` empty, check 9b's `cp .dockerignore "$SCRATCH/dockerignore.bak"; awk ... > .dockerignore`
fails the backup and then truncates the untracked `.dockerignore` to 0 bytes (reproduced), the exact
data loss revision 3 set out to prevent; check 8 breaks course-list.tsx with no backup the same way.
Checks 7/10 start `pnpm dev` with `(set -m; ...)`, which zsh rejects ("can't change option: -m"),
so the dev server never starts.
Rule: Write tester shell steps for the shell that will actually run them (one fresh zsh per call):
persist helpers and paths in a file at a fixed path and source it each call, guard with
`: "${SCRATCH:?}"`, chain backup and mutation with `&&`, and run job-control snippets under an explicit
`bash -c`. Execute every non-trivial snippet once in that shell before handing it over.

### 2026-10-27: Delegated gate code to a checkout without bounding whose code may decide (#21)

Issue #21 design, section 2.2: the dispatcher runs the resolved checkout's OWN hook scripts, and the
resolver accepts any directory whose `git rev-parse --git-common-dir` equals main's `.git`. That check
is passed by a bare directory holding a `.git` file `gitdir: <main>/.git` (reproduced: it reports the
same common dir and is absent from `git worktree list`), and by any registered worktree checked out at
an old commit (`git worktree add <p> c66e1a0`), whose pre-v2 require-pipeline computes REL against the
worktree, so main's `.claude/pipeline_state.json` and `.claude/hooks/*` become plain writable paths once
that worktree has any active tier. A `cd` (or an inherited `PIPELINE_CHECKOUT`) then puts every gate of
the session under scripts the agent chose, defeating decision 4 and state protection with no PIPELINE
tier and no gated write. Separately, `.claude/settings.local.json` stayed outside `pipeline_core_files`,
so a Write to it (`disableAllHooks`, `env`) is always allowed by the `.claude/*` rule.
Rule: When gate code is chosen from data an agent can influence (cwd, env, checkout contents), state
the trust bound explicitly and enforce it in code the agent cannot swap: accept only registered
worktrees, let a checkout's scripts decide only about files inside that checkout, keep a floor check
in the dispatcher for every checkout's state/core/settings files, and list every file that can switch
hooks off as pipeline core.

### 2026-10-27: Real-state migration designed against the wrong branch's code (#21)

Issue #21 design 2.8: park live #1 in main, "later, on feat/1-web-bootstrap, `resume 1` restores it".
feat/1-web-bootstrap (4cda2ba) branches off 5c4d853, before v2. Hook scripts run from the checkout's
own working tree (decision 1), so on that branch `pipeline-advance.sh resume` does not exist, and its
old `.gitignore` leaves `.claude/pipeline_state.parked/` untracked, which trips the dirty-tree gates.
The same design also claimed "every row has a mutation in section 11" while D1, D4, D7, D9, D12, B1,
B4, B8, B12, A4, A5 had none, and made `init` refuse on a renamed branch although scope C says a
differing `branch_at_init` must not block init and parking would have lost nothing.
Rule: For every step that touches real state, name the branch/commit it runs on and check that the
code and ignore rules it needs exist there (`git merge-base`, `git show <branch>:<path>`). Every
"each test has a negative run" claim lists the mutation per row, and every deviation from a scope
item is stated as a deviation with its reason.

### 2026-10-27: Rollout, rollback and verification steps not tied to what is actually on disk (#21)

Issue #21 design (operations review). Section 12 creates the live-check worktree with
`git worktree add ... -b chore/998-live-wt` from HEAD but never says v2 must be committed first, while
"Step 11" runs "after the tester and judges", i.e. before the commit phase: the worktree would get the
pre-v2 tree and L2/L3 would certify the dispatcher's fallback, not v2. Rollback is only "re-disable
hooks"; reverting v2 leaves `.claude/pipeline_state.parked/` untracked under the old `.gitignore` (Stop
and PR dirty-tree gates block), strands parked #1 with no `resume`, and leaves a never-deleted
`.lock` that the old O_EXCL vote path waits 5 s on. The F1 mutation cannot go red: the tester's `mut`
helper itself excludes worktrees/settings.local.json/state from the copy, so run.sh's filter has
nothing to filter. `dispatch.sh` reads `root<TAB>source<TAB>gitdir` with default IFS, which splits
the test repo's deliberate "work dir" path. "Never fail open" is false when python3 is missing: every
gate exits 0 and nothing is logged.
Rule: Every operational step names the commit it runs against and its precondition (committed,
rebased, ignored); every design ships a rollback section (kill switch, revert, leftover runtime
files); every mutation is checked against the harness that will run it (does the copy still contain
the condition the guard detects?); pseudo-code that parses paths is checked against the test suite's
own paths; a "never fail open" claim is walked through "interpreter missing".

### 2026-10-27: Mutation table rows whose mutation misses the test, or whose test cannot pass (#21, round 2)

Issue #21 design rev 2, table 2.13. A9 "concurrent advance and vote lose nothing" is paired with the
mutation "set_artifact bypasses transaction()", but neither `advance` nor `vote` calls set_artifact
(2.4), so the mutated run stays green. C1 "init parks a state copied from another checkout" with the
mutation "treat any gitdir_at_init as matching" falls through to the next init row, `branch-switched`,
which also parks: green unless the test asserts `parked_reason == foreign`, which the row does not say.
S8 (PATH holds only `cat`) cannot pass on the design itself: 2.11 sources common.sh via
`$(dirname "$0")` and common.sh computes CODE_ROOT with `realpath`; both are external binaries
(/usr/bin/dirname, /bin/realpath), so sourcing fails before the python3 probe and the gate exits 1,
i.e. fails open. S5 is scheduled in coder step 3 but its setup "PIPELINE active" needs the tier added
in step 7. F1's copy check exits 1 without saying it prints the `FAIL <name>` line step 11.1/6 greps.
Rule: For every mutation row, trace the mutated code path through the exact test setup and name the
assertion that distinguishes it (reason field, count, message text), checking that no later branch
(next table row, fallback) produces the same observable; walk "tool missing from PATH" for every
external command a hook runs before its own probe; check each test's setup only uses features added
in or before the step that adds the test.

### 2026-10-27: Treated "registered worktree" as trusted and let tier switches bypass the tier rules (#21)

Issue #21 design revision 2. The resolver and the write gate trust any root listed by
`git worktree list` ("the only source an agent cannot fake"), but registering one is a single
unguarded shell command: `git worktree add <main>/.claude/hooks/lib/json <orphan-branch>` (no write
verb, no blocked string). `checkout_of` then picks that nested root as the owner (longest prefix), so
REL is no longer `.claude/hooks/...` and the core rule does not apply to tool writes there; worse,
hook Python runs with `lib/` as `sys.path[0]`, so the nested `json/__init__.py` shadows the stdlib
module and runs inside main's gates (reproduced). Separately, `pause` + `init PIPELINE <n>` (or
`pause` of a LEARN state + `init TASK`) turns the "core only in PIPELINE" and "learner writes the
code" rules into two unauthenticated commands, where v1's init at least refused while a state was
active. And the absolute always-blocked zones omit `~/.claude/settings*.json`, the user-level
equivalent of the `settings.local.json` kill switch that D-5 made core.
Rule: Any trust anchor an agent can create with one command (worktree registry, branch, state via a
documented CLI) is not a trust anchor: evaluate main's core/state/git paths as absolute zones before
any ownership mapping, accept only worktrees outside main's tree or under `.claude/worktrees/`, and
for every tier rule ask "which command switches the tier, and who may run it?".

### 2026-10-27: TAB-separated read with IFS=$'\t' collapses empty fields; precondition grep on the wrong field (#21)

Issue #21 design revision 2, 2.1/2.2: the context line `state_root, source, gitdir, branch, main_root,
tool_name, state_status` is read with `IFS=$'\t' read -r`. TAB is IFS whitespace in bash, so consecutive
TABs collapse (reproduced: `a\tb\tc\t\te\t\tg` gives 5 fields, the last two empty). `tool_name` is empty on
every Stop/SubagentStop event and for pipeline-advance's empty-stdin call; `branch` is empty on a detached
HEAD. The fields shift and STATE_STATUS reads empty, i.e. "no state": phase-complete allows Stop (fails
open) and the LEARN shell rule is lifted. The fix for "paths with spaces" introduced it. Section 12 R1
checks `git log -1 --format=%s | grep -q '#21'`, but the convention (and a58679d itself) puts `Refs #21`
in the body, and the v2 PR gate reads `%B`: as written R1 never prints R1_OK and the rollout halts silently.
Rule: Machine-readable lines between scripts use a non-whitespace separator (`\x1f`) or a placeholder for
empty fields, and the test suite includes a row with every optional field empty. Every precondition
command is run once against the real commit it will check before it is handed to Stepan.

### 2026-10-27: A new fail-closed check silently absorbed an older test row's mutation (#21, round 3)

Issue #21 design revision 3 added to common.sh step 5 "STATE_STATUS empty -> gate exits 2 `pipeline
resolver failed`" (for S9). B18 (`context line keeps empty fields`) still asserts only "phase-complete
blocks, rc 2" and claims its TAB mutation makes Stop "allowed". Under that mutation the fields collapse
(reproduced on bash 3.2.57: `[r][s][g][m][own:PROJECT:coder][][]`), STATE_STATUS is empty, and the new
check blocks with rc 2: the row stays green, so it cannot fail. B18 is also scheduled in coder step 2,
while `gitdir_at_init` arrives in step 6: with the legacy branch rule a state on a detached HEAD is
foreign, so Stop is allowed and B18 is red on the correct code in step 2.
Rule: After adding any fail-closed branch, re-trace every existing mutation row whose broken path now
reaches that branch, and assert the message, not just the exit code, whenever two code paths share
an exit code. A row whose setup depends on a field (here `gitdir_at_init`) goes in the step that adds the field.

### 2026-10-27: B18 cannot fail, confirmed by operations; human-run steps without commands (#21, round 3)

Operations judge, independently of the entry above: simulated common.sh step 5 plus phase-complete for the
B18 setup with both separators. `\x1f` blocks with phase-complete's own reason; the TAB mutation blocks
with `pipeline resolver failed`; both rc 2, so the row as written stays green. The real hazard of the
mutation is spurious blocking (every Stop and every detached-HEAD call fails closed), not "Stop allowed".
Separately, 2.9a tells Stepan to write and later trim the grant file "by hand in an editor" but gives no
exact command to create it, validate it, or remove an issue, while every other Stepan step in section 12
has one.
Rule: A mutation row asserts the distinguishing message, and its stated failure mechanism is reproduced
before it is written down. Every step a human performs gets copy-paste commands plus a check command.

## 2026-10-27: Wrote a path-prefix list that the shell guard reused as a substring rule (#21)
Design 2.7/2.12 listed pipeline core as `.claude/hooks/` with a trailing slash, and D11 tested only
`.claude/hooks/x.sh`. The shell guard matched that string verbatim, so `rm -rf .claude/hooks`,
`mv .claude/hooks x` and `rm -rf .claude` passed outside PIPELINE; removing the hooks directory makes
every hook exit 127 (non-blocking), so all gates fail open. Design 2.3 (logs carry only relative
paths) also contradicted 2.6 step 4 (REL is absolute when no checkout owns the path).
Rule: A protected directory is specified for both matchers: as a path prefix for tools and as a
directory token (with and without a trailing slash, plus its ancestors) for shell commands, with a
test row for each spelling. Cross-check every "only"/"never" claim against the steps that produce it.

### 2026-10-27: Residual-risk list written from the old regex; moved gate code got an exit-code collision (#23)

Issue #23 design 2.9 has ADR-0005 item 7 say `.claude//hooks` passes the shell guard. Under the new
2.4 rule, `.claude/` followed by `/` matches `/(?![\w.-])`, so that spelling is now blocked. Spellings
that still pass are not listed: `.claude/./hooks`, `.claude/h{ooks,}`, `.claude/h""ooks`. The 2.4
header also claims braces are covered, but a brace after the first character of the component is not
(alt 3 knows only `*?[`). Separately, 2.7 moves the gate code into `lib/*.py` but keeps the contract
"exit 2 = block, stdout `<reason>\x1f<message>`". CPython itself exits 2 when it cannot open the
script (a missing or unreadable `lib/write_gate.py` or `lib/shell_guard.py`). The wrapper then
denies with an empty message and an empty log reason, not as `gate-crash`. The wrapper still blocks,
so this does not fail open. But this failure mode is new with the refactor and appears in neither
section 7 nor section 3.
Rule: Derive every "still passes" or "now blocked" spelling in a residual-risk list by running it
against the NEW pattern, never the old one. When code moves out of a wrapper into a file the
interpreter opens, check the interpreter's own exit codes against the wrapper's contract. Add a row
that makes the new file unreadable and asserts the crash message.

### 2026-10-27: Live-edit rollout claimed "one gate per step" while steps edit code both gates share (#23)

Issue #23 design, F1 and section 10: the hooks are edited live in the main checkout, and the stated
mitigation is "at most one gate changes per step, repair a broken gate through the other one". Steps
2 and 5 edit `lib/checkout.py` (`LOG_FIELDS`, `_context`) and step 2 edits `lib/common.sh`; step 9
re-annotates `cfg.py`, `checkout.py`, `state.py`, `hookio.py` and adds a raising validation to
`cfg.load()`. `common.sh` runs `checkout.py context` for every hook, and both gates import `cfg` and
`checkout`. One NameError, one 3.10-only annotation evaluated on a 3.9 Mac, or a `ConfigError` on the
real pipeline.json makes `require-pipeline.sh` and `bash-code-guard.sh` fail closed together. No Write
or Bash can then repair the file, and only the kill switch plus a new session gets out. The section 10
procedure ("make the change, then run run.sh") puts every change live before any test has run.
Rule: In a live-edit rollout, list for each step every file that more than one gate executes
(common.sh, resolver, config loader, shared lib). For those steps, apply the change to a scratch
export and run the suite there first. Only then copy the change into the live tree, as one write per file.

### 2026-10-27: Assumed a broken shared hook file always fails closed (#23)

Issue #23 design, F1: the recovery story assumes a broken gate blocks, so the other gate or the kill
switch can repair it. Checked on a scratch export: a syntax error in `lib/checkout.py` or `lib/cfg.py`
makes both gates exit 2 for every command, `ls` included (lockout). But a syntax error in
`lib/common.sh` (edited live in step 2) leaves `run_hook` undefined, and both gates exit 127. Claude
Code treats 127 as a non-blocking error, so every guard is silently off for the rest of the session.
The same design also told the coder to build the local mypy venv with `python3 -m venv`. On this Mac
that is 3.9.6, which cannot install the only mypy line that still targets 3.9 (1.19.x/1.20.x need >= 3.10).
Rule: For each live-edited shared file, establish what the hooks do when that file is broken (exit 2,
exit 127, or a traceback) by breaking a scratch copy. Do not assume "fail closed". Name the interpreter
that each tool command actually runs on the target machine.

### 2026-10-28: Generic "gates exit 2" fallback breaks the Stop hook's no-loop rule (#23)
Design rev 2 section 2.10 gave every HOOK_KIND=gate script the same fallback when lib/common.sh
does not load: print BLOCKED and exit 2. phase-complete.sh is a gate on the Stop event, where its
own contract (header line 4, run.sh row "stop not blocked twice (stop_hook_active)") is to block at
most once per turn. An unconditional exit 2 blocks every Stop, so in exactly the lockout where the
orchestrator must stop and hand over to Stepan, the session is re-prompted again and again until a
human interrupts it. T15 did not cover phase-complete.sh, so no row would notice.
Rule: When one fallback is applied to all scripts of a kind, walk each script's event (PreToolUse,
Stop, SubagentStop, PostToolUse) and check that the fallback still honours that script's own
invariants; give each event its own test row.

### 2026-10-28: "Unreadable imported module = crash" ignores the bytecode cache (#23, round 2)
Design rev 2 T18/F16 says `chmod 000 lib/pl_gate.py` makes both gates crash with rc 1, because
the import fails. In fact `pl_gate` is imported, not run as a script. Earlier suite rows have
already written `lib/__pycache__/pl_gate.cpython-39.pyc` into the `$WORK` copy, and `python3 -I`
does not stop bytecode writes. CPython's SourceLoader only stats the source (stat works on a
mode-000 file), finds a pyc whose mtime and size match, and loads that without ever reading the
source. So the gates keep working and T18 is red on correct code. Under its own mutation the row
cannot distinguish anything either. The existing chmod rows (`run.sh:402`, `:424`) and T16/T17
only work because they make a script that CPython opens directly unreadable, and directly run
scripts are never cached.
Rule: When a test makes an *imported* Python module unreadable or broken, account for
`__pycache__`. Remove the cache directory first, or make it unreadable too, or change the
source's mtime/size. Then confirm the crash on a scratch run before the row goes into the table.

### 2026-10-28: Rows that contradict the design's own code path, and a typing order that cannot pass (#23, round 2, architecture)
Design rev 2: (1) T16/T17 assert "last log line `gate-no-verdict`", but 2.7 has the wrapper log
`gate-no-verdict` and then `return 70`, after which `run_hook` (`common.sh:111`) logs `gate-crash`.
The last line is always `gate-crash`, so both rows are red on correct code. (2) 2.5 has the marker
helper catch `UnicodeError` and log. T11(c) still claims that a strict `encode("utf-8")` crashes
`_context`. If the encode sits inside that try, the mutation is absorbed and the row stays green.
If it sits outside, the `UnicodeError` handler is dead code. The design does not say which.
(3) Step 10b types `hookio` before 10c types `checkout`, and requires "mypy on that module clean".
But `hookio.py:45` calls `checkout.code_root()`, and `--strict` reports `no-untyped-call` in
hookio itself until checkout is annotated. So 10b's gate is unreachable.
Rule: Trace every assertion through the full wrapper chain, including the trailing `run_hook`
mapping and its log line, before writing it down. A mutation must not land inside a handler the
same design adds. Order strict-typing steps by the import graph, callees first.

### 2026-10-28: Post-merge step relied on a GitHub feature the repo plan does not have (#23)
The #23 design (section 12, F20, line 260) told Stepan to make `pipeline-types` a required status
check on `main`, and the coder echoed it in the ci.yml comment ("the name the required-checks rule
uses"). `valmlord/academy` is a private repo on the free plan: both
`gh api repos/valmlord/academy/branches/main/protection` and `.../rulesets` return 403 "Upgrade to
GitHub Pro or make this repository public". No required-checks rule exists or can exist, so the
step is unexecutable and the comment describes a rule that is not there. The real merge guard is
Stepan checking `gh pr checks` before he merges.
Rule: Before a design relies on a platform feature (branch protection, rulesets, required checks,
environments), call its API on the real repo and quote the answer; a 403/404 means the design
needs another enforcement point.

### 2026-10-29: SHA-free git rule checked only after the squash; deviations executed before the owner saw them (#26)
Issue #26 design section 6 replaces "branch contains v2" (`merge-base --is-ancestor <v2 commit> HEAD`)
with "`git merge-base main HEAD` prints a commit". That is only equivalent after Stepan squashes main.
Between this PR's merge and the squash, pre-v2 `feat/1-web-bootstrap` (still at 4cda2ba, carrying
5ad27f4) shares history with main, passes the check, and may be checked out in the main checkout,
which runs its v1 hooks: the exact hazard #21 R5 existed to prevent. The `git tag pre-squash main`
step is timed "before force-pushing", but a local squash moves `main` earlier; a tag on the new root
makes `rebase --onto main pre-squash <branch>` replay the whole old history. Separately, the GitHub
runbook (G2) edits #1/#15/#21 in place, against the owner's explicit "recreate, never edit", before
Stepan has seen the deviation, and G7 emits irreversible `gh issue delete` commands from a snapshot
that omits comments and is not tied to the verified mapping.
Rule: Walk every replacement rule through each state window it will live in (before and after the
owner's planned history rewrite) and prefer a check that is correct in all of them (here
`git merge-base --is-ancestor main HEAD`). Time a "mark the old tip" step relative to the first
command that moves the ref, with a check. Any deviation from an explicit owner instruction that
acts on GitHub needs the owner's yes before it runs, and every irreversible delete is generated only
from verified mapping rows, after snapshotting everything it destroys (comments included).

### 2026-10-29: Runbook asserted exact live counts it never measured, and its recovery path contradicted its own stop rules (#26)
The #26 GitHub runbook required the bootstrap dry-run to show "0 label creates" and stopped on any
other count, but the live repo lacks `tier:pipeline` (in `.github/labels.yml`), so the real dry-run
prints `label + tier:pipeline` and the runbook halts at G4. Its F2 recovery ("rerun G4+G5") also
contradicts G4 (exactly 18 creates) and G0 (stop if an English title exists or milestones are not
Russian, and re-snapshotting overwrites the rollback source), so any partial failure after G1 leaves
the orchestrator improvising.
Rule: Every exact expected output in a runbook is taken from a real read-only run against the live
host, and every step states its resume condition (already done -> skip, how to verify), with the
rollback snapshot written once and never overwritten.

### 2026-10-29: Narrowed an upstream decision's list silently; rewrote one bullet of a section whose neighbours break under the same change (#26, architecture)
Issue #26 design 2.2 keeps only "скажи прямо" as a Russian quote and calls that "decision 3", but
research decision 3 lists three learner-typed hint words ("скажи прямо", "подсказка", "скелет"). All
six lessons say "уровни \"скелет\" и \"скажи прямо\"", and mentor.md:35 says the learner types
"подсказка", so translating them in docs/learning-process.md breaks the link between the docs and the
course. The coders receive both files, so they get two contradictory rules, and V1 then flags the
coder who follows the research. Separately, section 6 rewrites only the first Worktrees bullet. The
same bullet's "bring an older branch up with `git merge main`" and the next bullet ("a worktree on an
older branch runs `git merge main`") stay. After the squash, those commands fail with "refusing to
merge unrelated histories". The new `rebase --onto main pre-squash` recipe was not rehearsed on a
scratch clone either, although the only real branch (feat/1-web-bootstrap) carries 5ad27f4. That
commit is a cherry-pick twin of a58679d in old main. The recipe works only if rebase drops it by
patch-id, and that was never checked.
Rule: When a design restates an upstream enumeration, copy it whole or state each dropped item as a
deviation with its reason. When a history rewrite changes one git instruction, re-read every git
command in the same section against the new history. Rehearse each new recipe on a scratch clone
with the real branch before it goes into CLAUDE.md.

### 2026-10-29: Tag cleanup condition true from the moment of the squash; window-B merge claimed without a run (#26, round 2, architecture)
Issue #26 design rev 2, 6.2: "when `git branch --contains pre-squash` prints nothing, `git tag -d
pre-squash`". `--contains` lists descendants of the tag. After the squash, local `main` is the new root,
the squash-merged branches are ancestors of old main, and `feat/1-web-bootstrap` (4cda2ba on 5c4d853)
never contained main. So the command prints nothing right after the squash, before #1 is rebased, and
following the rule deletes the tag that `git rebase --onto main pre-squash feat/1-web-bootstrap` needs.
V7 never exercises the cleanup, so nothing would notice. Separately, 6.3 window B says bring-up step 2
`git merge main` "works" for pre-v2 `feat/1-web-bootstrap`, with no run behind it. That branch carries
5ad27f4 (v2 cherry-pick) on a pre-v2 base, while main has since rewritten the same hook files (#23, #25).
Both sides changed the same regions relative to 5c4d853, so a conflict in `.claude/hooks/` is expected,
the same reason the old section 7 said a plain rebase "would conflict".
Rule: For every "when X prints nothing, delete Y" rule, check what X prints in the state right after
the event that creates Y. Put every "this command works" cell of a window table into the rehearsal
script, or say that the window is not supported.

### 2026-10-29: Tag cleanup condition that is already true when the tag is still needed (#26, round 2, security)
Design revision 2, 6.2 "Cleanup": delete `pre-squash` "when `git branch --contains pre-squash` prints
nothing". `--contains` lists branches whose tip descends from the tag. After the squash, main is a new
root, and a branch cut before the squash (feat/1-web-bootstrap at 4cda2ba on 5c4d853) is older than the
tag tip, so it does not contain it either: the command prints nothing right after the squash, before the
one branch that needs the tag has been rebased. Following the rule deletes the anchor of
`rebase --onto main pre-squash <branch>`, and the obvious improvisation (`git rebase main`) replays the
whole pre-squash history onto the new root, the failure round 1 flagged. V5 blesses the command (it is in
6.4) and V7 never runs the cleanup, so nothing would catch it.
Rule: A "safe to delete the anchor" condition must test the property the anchor serves (here: no local
branch shares history with it, `git merge-base pre-squash <b>` fails for every `refs/heads` branch), and
the rehearsal must show the condition is false before the last dependent step and true after it.

### 2026-10-29: Prescribed commands that the harness refuses, and a file-set check that is red on day one (#26, round 2, operations)
Design revision 2, V7 starts with `rm -rf "$V"` inside `bash -uo pipefail -c '...'`, and G0 starts with
`rm -rf "$D"`. Claude Code's built-in removal check refuses `rm -rf` of a shell variable inside a `-c`
script without a human approval; run live by the operations judge, the V7 call was denied before
anything ran. With `V=$(mktemp -d "$S/v7.XXXXXX")` and no rm, the same script printed `V7 OK`. Separately,
V3 requires `git diff --name-only main` plus `git status` to list only scope files and `plans/26-*`, but
the worktree already carries `.claude/feedback/architect_mistakes.md` (design-review lessons), and
judge_code and compound append more, so V3 is red for a legitimate file.
Rule: Every command a design prescribes for an agent is run once in the same harness before the design
is handed over (the architect asks the orchestrator if it has no shell); scratch paths come from
`mktemp -d`, never `rm -rf $VAR`. A "changed files are only X" check enumerates every file the pipeline
itself writes on the branch (`.claude/feedback/*_mistakes.md`, `plans/`).

### 2026-10-29: A literal with an apostrophe inside a mandated single-quoted `bash -c`; `branch -D` gated on "PR merged" only (#26, round 3, security)
Design revision 3, 5.3 mandates every runbook step as `bash -uo pipefail -c '...'`, and G1b prescribes
`--description "Pipeline core changes, needs Stepan's grant"` (copied from `labels.yml:15`). The `'` in
`Stepan's` closes the outer single quote: bash gets a truncated script with an unterminated `"`, and
the rest of the step is parsed by the calling zsh, outside the `umask 077` / `: "${D:?}"` guards that
5.3 relies on. Separately, 6.2 lets Stepan `git branch -D` any stale branch after confirming "its PR is
merged" on GitHub; that does not prove the local tip has no unpushed commits, and `-D` also drops the
branch reflog.
Rule: Every literal placed inside a single-quoted `-c` script is scanned for `'` (or values are read from
their source file inside the script, never retyped). A force-delete gets a local, verifiable precondition
(tip equals the merged PR's `headRefOid`, or `git merge-base --is-ancestor <b> pre-squash`), not a
human "it was merged" check.

### 2026-10-29: A rehearsal edit added in review broke an assertion it was never re-run against (#26, round 3, operations)
Design revision 3 added `g checkout -q --detach origin/main` to V7 (so `update-ref refs/heads/main` never
moves a checked-out branch) and, in the same revision, the regression line
`[ -z "$(g branch --contains pre-squash)" ]`. `git branch --contains` also lists a detached HEAD, which
sits exactly on the tag, so it prints `* (HEAD detached at origin/main)` and V7 stops with
`V7 FAIL: B: regression premise` although no `refs/heads` branch contains the tag. The design said the
revision 3 additions "have not been run yet". With `g checkout -q main` right after the squash the rest
of V7 passed. Same revision: G8 runs `bash .claude/hooks/pipeline-advance.sh pr <url>` from the
worktree, which `lib/common.sh` refuses for a worktree copy (CLI kind), and `gh pr create --head
docs/26-english-docs` with no `git push` step, while the branch is not on the remote.
Rule: An unrun check is not a deliverable: when a revision touches a rehearsal script, the whole script is
re-run (via the orchestrator if the architect has no shell) before handover. Assertions about "no branch
contains X" use `git for-each-ref refs/heads --contains X`, never `git branch` output, which includes a
detached HEAD. Every pipeline command in a runbook uses the invocation CLAUDE.md prescribes for the
checkout it runs in, and a PR-creation step pushes and checks the remote head first.

### 2026-10-29: A by-name exclusion written "in any window" outlives the state it guards (#26, round 3, architecture)
Design revision 3, 6.1: bring-up step 2 skips `feat/1-web-bootstrap` by name, and the section text says it
"is never brought up with `git merge main`, in any window". The exclusion is only needed before the squash
(pre-v2 base, expected hook conflict). After its 6.2 rebase, #1 sits on the new root like any other branch.
Once anything else merges to main (likely while #1 is active), step 1 fails, step 2 skips #1 by name, and
step 3 sends it back to 6.2. There the pre-check `git log pre-squash..feat/1-web-bootstrap` lists the whole
new history ("tag is wrong: stop"), or fails outright because the cleanup rule has already deleted the tag.
#1 has no valid path, and the obvious improvisation is a rebase. The 6.3 window table stops at "after the
recipe", so it never looked at a fourth state: rebased, then main moves on. Step 3's wording ("cut before
the squash") is also wrong for that state.
Rule: Every special case keyed on a name or a window gets an end condition that the procedure itself
checks, and the window walk includes the state after the special handling, with main moving on.

### 2026-10-29: A write-once marker set after unchecked writes freezes a broken snapshot (#26, round 4, operations)
Design revision 4, 5.3 G0: the mandated preamble is `bash -uo pipefail -c` (no `-e`), G0 is composed from
prose that says "write each file with `>`" and "`touch "$D/complete"` as the last command", and later runs
skip G0 whenever `complete` exists. The stop conditions validate only `issues.json` and the milestones; they
never check that `pr-22/24/25.json`, `labels.json`, `head`, the backlog archive and `main-backlog.list` were
written. Run live: a failing `gh pr view ... > "$D/pr-24.json"` followed by `touch "$D/complete"` left a
0-byte file and the marker. Every rerun then skips G0, G3 dies on `json.load` of the empty file, the F14
rollback of PR #24 has no source, and no agent can repair it (no `rm` in any step). An empty
`main-backlog.list` would also make the "#1-#20 title equals main's backlog" stop condition pass vacuously.
The literals (G1b, G2, G3, G8a) all check exit codes; only the one irreversible step does not.
Rule: Before a write-once or commit marker, the design names a check for every artifact the marker vouches
for (exit status of each write, and a content check: parses, expected shape, expected count), and the step
that sets the marker is either a prescribed literal or names those checks explicitly.

### 2026-10-29: Identity rule stated as "where the file lives", mechanism trusts the prompt's claim (#27, round 1, security)
Design rev 1, 1.1 says a gated role may run only when "the directory its file lives in" equals the tier's team,
but 2.1.2 takes the team from the `ROLE_RE` capture of the prompt text. `Read .claude/agents/dev/curriculum-architect.md
first` in TASK architect yields `dev/curriculum-architect.md`: team equals the tier, window exists, spawn allowed, and the
leak the design claims to close stays open behind a wrong directory (case-insensitive `re.I` plus the macOS file system
widens it: `content/Curriculum-Architect.md` is an ungated basename). Likewise `role_from` returns the prompt match before
looking at `subagent_type`, so a dev prompt plus `subagent_type: curriculum-architect` (which selects the real agent
definition) is never team-checked, although the design says the leak is closed "both by prompt and by subagent_type".
Rule: When a gate enforces an identity, derive it from the ground truth (the scanned file location, every identity
source present in the input), never from a value the input merely claims; a claim that disagrees with the ground truth
or a missing file resolves to a non-matching sentinel, never to empty ("not a role").

### 2026-10-29: The enforced rule reads the prompt's claim, the documented rule names the file (#27, round 1, architecture)
Design revision 1, 2.1.2-2.1.3: the team check compares the tier's `team` with the directory captured from the
prompt text (`ROLE_RE` group 1), while 1.1 and the ADR-0005 item 10 text say "the directory its file lives in".
`Read .claude/agents/dev/curriculum-architect.md first` in TASK `architect` yields team `dev`, passes the check and the
window, and the leak the change exists to close stays open for a one-word slip; T1/T2 only test the correctly spelled
path, so the suite reports the leak closed. Same revision, 2.7/2.8: `tokens.css` is said to style the prototypes
unchanged, yet browsers drop the whole `@theme inline` block, so `--radius-sm`, `--font-sans` or `--color-*` defined
there are undefined in a prototype; the validator's "defined token" set and its color/non-color classification of
`:root` declarations were left unstated, so it can certify a prototype that renders wrong. The unit test list has no
text pair between 3:1 and 4.5:1, so the core 1.4.3 threshold could be 3.0 and every test would stay green.
Rule: When a rule is stated about a real object (a file's location, what a browser applies), the check derives it from
that object, not from a string that describes it, and a test exercises the description and the object disagreeing.
Every threshold a validator enforces gets a test case on each side of it.

### 2026-10-29: "Leave the file out of every commit" with no path through the clean-tree gates (#27, round 1, operations)
Design revision 1, 9.3 and 5 keep Stepan's uncommitted `.github/CODEOWNERS` out of every commit (explicit-path
commits) and 11.2 defers it to "when committing the pending edit", but never says what happens at `pr`:
`pipeline-advance.sh:249` refuses on any `git status --porcelain` output and the Stop gate at `done`
(`phase-complete.sh:90`) does the same, so the pipeline cannot leave `commit` while the edit sits in the tree. The
research listed this constraint explicitly; #23 got past it only by an ad hoc `git stash`. Same revision: the recovery
row "S1 blocked, S3 succeeds" names `cfg.py` although F1 says a broken `cfg.py` closes the Write gate too, and P3
prescribes `shellcheck` and mypy runs with no tool present on this Mac (no local shellcheck, no offline mypy).
Rule: For every working-tree file a design keeps out of commits, it names the exact step that gets it past each
clean-tree gate (`pr`, Stop at `done`) and back afterwards; every prescribed local command names a runnable tool
invocation that was actually run on this machine.

### 2026-10-29: A tool's output format collided with the vote parser the judges feed it to (#27)
Design 2.8 fixed the validator's lines as `PASS|FAIL <theme> ...`, and 2.5 told the design judges to paste them and
gave a FAIL template whose items follow the verdict line. With the theme `:root`, `PASS :root --ring on
--background: ...` matches `hookio.VERDICT_RE` (`\s*[:\-]` after PASS), and `verdict_from` takes the last
verdict-shaped line, so a FAIL report with the validator output pasted below it is recorded as a PASS vote.
Rule: Any text a judge is told to quote in its report must be checked against VERDICT_RE; tool output lines never
start with a bare PASS or FAIL token.

### 2026-10-29: Security constraints described in words, tests that a naive version passes (#28, round 1, security)
Design rev 1, 4.5 describes `attempts_transcript_path_check` as "no `..` segment" without the SQL, and I11 tests only
`../etc/passwd` and `/abs/path`: `NOT LIKE '../%'` passes both and accepts `a/../../x`. 4.7 says "`SET lock_timeout`"
from a public `lockTimeoutMs` option, but `SET` takes no bind parameters, so the natural implementation interpolates
an unvalidated value with `sql.raw`. 4.6 justifies CASCADE as "one path removes everything" while the learner's
transcripts live outside Postgres and survive account deletion. A default `console.error` "with context" and new error
types came with no rule keeping the connection string (password) out of messages.
Rule: Every security-relevant constraint is written as the exact expression, with reject cases for each spelling the
rule targets (start, middle, end, bare) and a mutation that a naive version fails. Any value that reaches SQL where
parameters are impossible (SET, DDL) is either passed via `set_config($1)` or validated with a named error. A deletion
or retention claim lists every store holding the user's data, not only the DB. Every new log or error path states what
it must never contain and has a test with a canary secret.

### 2026-10-29: A coupling justified by an unverified tool diff; plain-Node path logic assumed for a bundled consumer; semantics left to four writers (#28, round 1, architecture)
Design rev 1 derives `CHECK_KINDS` from lesson-schema "so a new kind turns the drift step red". That only
holds if drizzle-kit 0.31 regenerates a named CHECK whose body changed. Nothing verified this, and T-drift's
only negative run adds a column, which exercises a different diff path. The design also called
`MIGRATIONS_FOLDER = new URL("../drizzle", import.meta.url)` reliable for "consumers from any cwd". The
first consumer is Next.js, which bundles workspace packages, and bundlers rewrite that expression. The
`migrationsFolder` escape hatch was labelled "only for a test fixture". `MigrationError` said "transaction
rolled back" for lock-timeout and connect failures as well. And the progress-model ADR defined attempt
aggregation, but not what an attempt covers or when a lesson becomes `completed`, although four separate
writers (#8, #10, #11, #13) must agree on both.
Rule: Every guard that justifies a design choice gets a negative run that changes exactly the thing the
guard claims to catch (here, a CHECK value). Path resolution is checked against how the first real
consumer loads the package (bundler or plain Node). Error messages name the failing stage. A data-model ADR
defines every status transition that more than one writer performs.

### 2026-10-29: A drift guard that exits 0 on drift; a lockfile check that cannot pass (#28, round 1, operations)
Design rev 1 said a drizzle-kit rename prompt "hangs" in non-TTY CI and that a step timeout turns it red.
Run live, drizzle-kit 0.31.11 does something else: it prints "Interactive prompts require a TTY terminal",
writes nothing and exits 0. The drift step (exit code plus `git status` empty) therefore passes on a renamed
column that has no migration. The design's only negative run (adding a column) never takes that code
path. T-install also required "only additions" in the lockfile diff. But the committed `pnpm-lock.yaml`
is not in pnpm's native format, so any dependency change rewrites the whole file (2612+/985-), and the
check could never pass on correct work.
Rule: A CI guard asserts the tool's positive success output (e.g. "No schema changes, nothing to
migrate"), not just exit 0 and a clean tree. Each class of input the guard claims to catch (add, rename,
constraint change) gets its own negative run. Before prescribing a diff-shape check on a generated file,
run the generator on the committed file once and look at the real diff.

### 2026-10-29: Tester commands written for a clean machine, not for the state the pipeline leaves behind (#28, round 2, operations)
Revision 2 prescribed exact tester commands, but four of them fail on correct work when run in the order
the design itself sets. T-install expects no "Ignored build scripts" line, but step 0's frozen install
(and this worktree's existing `node_modules`) recorded `esbuild@0.28.2` as ignored, and pnpm keeps
reprinting it, so the negative run cannot fire either. Git's default Myers diff shows 24 "deletions" that
are moved, unchanged entries (`histogram` shows 0). The first resolving install prints a drizzle-kit
deprecation `WARN`. T-sep's negative uses `DOCKER_HOST=unix:///nonexistent`, but testcontainers 12.2.1
falls back to `/var/run/docker.sock`. And vitest 5.0.5 replaces every globalSetup error with
`TypeError: code.charCodeAt is not a function`, so F9's message is never shown. The I11 mutations claimed
"exactly" the listed cases go red, but each mutation accepts more cases. Section 6 left the drift
script's green output open, while T-drift positive greps that output.
Rule: Every prescribed check states its starting state (fresh `node_modules`, which installs already
ran, the diff algorithm) and is traced against the state the earlier steps leave behind. A negative run
names a failure the tester can actually cause on a machine where Docker is running. An expected set of
test results says "exactly" only after every case has been evaluated.

### 2026-10-29: A schema mutation that cannot be applied alone, because a foreign key depends on the key it removes (#28, judge_code round 1, architecture)
Design section 7 I7 prescribed two mutations: "drop `course_id` from the `lesson_progress` PK" and "drop
the PK". Neither can be applied by itself. `attempts_lesson_progress_fk` references
`lesson_progress (user_id, course_id, lesson_id)`, and Postgres needs a unique key on exactly those
columns. So the regenerated `0000` fails with `42830`, I1-I4 go red with `MigrationError` stage `apply`, and
the whole schema test file is skipped in `beforeAll`. I7 went red for the wrong reason, and the coder had
to invent its own variants (confirmed live by the tester). The design's own section 5 shows that FK, so a
look at the key/FK chain would have caught it. The working mutations keep a unique key on the three columns:
PK `(user_id, lesson_id)` plus a unique on the three columns (isolates the other-course assertion), or a
separately named unique in place of the PK (red at the constraint-name assertion).
Rule: A prescribed mutation must be applicable alone, with every other test still able to run. Before
prescribing one that removes or narrows a key, constraint, column or table, list every dependent object
(FKs that reference the key, indexes, CHECKs, views, other tests' fixtures) and keep or replace what they
need. Then state which test goes red, at which assertion, and which tests stay green.

### 2026-10-29: A redaction rule with no test that fails when it is broken (#1, judge_design rev 2, security)
Design 4.2 item 3 says the startup log prints `message` only for `MigrationError`,
`InvalidConnectionStringError` and the two option errors, and only the name for any other value. U1-U3 and
mutations 8b (i)-(iii) never hand `migrateOnStartup` an unlisted error, so code that prints `message` for
every error passes them all; the rule that protects against a raw driver or import error carrying the URL
is unguarded. Check 7b's leak grep was the literal `academy:academy@`, which finds nothing whenever the root
`.env` uses another password, so it cannot fail in that state either.
Rule: For every "never log X" rule, add a test whose input carries a canary in exactly the place the rule
covers (here: the `message` of an unlisted error), assert the canary is absent from every log sink, and
prescribe the mutation that breaks the rule. A leak grep searches for the secret actually in use, read
from its source, never a hard-coded default.

### 2026-10-29: A "stays empty" guard that matches the verbatim copy it requires (#1, judge_design rev 2, architecture)
Design 2.1 (row ADR-0006 item 3) and tester Call 5-6 say `rg -n "design/" apps/ -g '!**/*.test.ts'` stays
empty, while 3.1 copies `design/system/tokens.css` byte for byte into `apps/web/app/globals.css`. Line 6 of
tokens.css is a comment naming `design/system/README.md`, so the grep matches globals.css on correct work and
the tester has to stop and report a design defect (the same class as the dropped filesystem-access guard).
`lib/copy.ts` comments citing `design/flows/ia.md` would match too.
Rule: Before declaring a grep "stays empty", run it against every file the design itself copies or
prescribes (verbatim blocks, comments it asks for), and narrow the pattern to what the ADR forbids (a
runtime import), not the bare substring.

### 2026-10-29: Took a design-system rule without its exceptions (#1, judge_design rev 2, architecture)
Design 2.1 and 3.1 adopt the `design/system/README.md` focus ring as one global rule (`:focus-visible`, 2px
`ring`, offset 2px outside) and add `main#main tabIndex={-1}` as the skip-link target, but the README's
"Focus ring" section says elements focused programmatically with `tabindex="-1"` (`main`, headings) draw
the ring inset. After the skip link, `main` spans the viewport, so an outside outline is clipped at the
page edges.
Rule: When a design adopts a rule from the design system, quote the whole rule including its exceptions
and check each exception against the elements the design itself builds.

### 2026-10-29: One recovery hint appended to every startup failure (#1, judge_design rev 2, operations)
Design 4.2 item 3 ends every migration failure line with "is the database running? (docker compose up -d
--wait db)". Run live in a scratch image without the drizzle COPY (tester check 9e), web logged
"MigrationError stage apply: applying migrations from /app/packages/db/drizzle failed (unknown) ...; is the
database running?" while db was healthy: the hint sends the 3 AM reader to the wrong layer.
Rule: Attach a recovery hint only to the failure class it is true for (here: stage connect); for every
other branch of an error formatter, run one failure of that branch and read the line it prints.

### 2026-10-29: A mutation command written for the unformatted line (#1, judge_design rev 2, operations)
Tester check 8d replaces the single line starting `export const MIGRATIONS_FOLDER`, but the new
declaration is 113 characters and biome (lineWidth 100) wraps it to 5 lines, so the prescribed awk leaves
four dangling lines and the red run fails on a syntax error instead of "Can't resolve '../drizzle'".
Rule: Write mutation commands against the code as the formatter will leave it (run the formatter on the
prescribed snippet first) and make them replace the whole statement.

### 2026-10-29: Reused tester calls that wipe the owner's database volume (#1, judge_design rev 2, operations)
Revision 2 reuses 3fea0fe Calls 14-16, 17 and 20 verbatim, each with `docker compose down -v`. When they
were written compose had no stateful service; now `db` keeps the named volume `academy_db-data`, which
exists on Stepan's machine, and the tester runs in the main checkout, so the run deletes his local database.
Rule: When reusing a procedure, re-check every destructive command against the current stack; record at
setup what pre-existed (volumes, images, `.env`) and tear down only what the run created.

### 2026-10-29: Verified an env override on a path the README does not document (#1, judge_code, operations)
Design 0.7 and 3.x prescribe the `next.config.ts` comment "a variable already set in the shell wins over the
file", verified with `pnpm --filter @academy/web dev`. The README documents root `pnpm dev` = `turbo run dev`,
and turbo 2 strict env mode drops undeclared variables: the `dev` task has no `env`/`passThroughEnv`, so a
shell `DATABASE_URL` never reaches next and the root `.env` value is used instead. Run in a scratch clone:
shell URL at a live db on 55432, root `.env` at 5432 -> root `pnpm dev` fails ECONNREFUSED (the `.env` URL),
`pnpm --filter @academy/web dev` with the same shell applies the migrations. The same design already knew
strict env drops `E2E_BASE_URL` and added `passThroughEnv` for `test:e2e`, but not for `dev`.
Rule: Verify every env-precedence claim through the exact command the README documents, and for every turbo
task list the variables the process reads and declare each in `env`/`passThroughEnv`.

### 2026-10-30: Step order claimed "each leaves the repo green" without walking runtime gates (#29)
Issue #29 design section 14: the startup secret check (step 6, commit 3) lands eight commits before
compose and CI supply the secret (steps 31, 37), so the web container exits 1 and the e2e job and
image check I2 are red in between. The default-deny proxy (step 19) lands before `/sign-in` exists
(step 26), so `/` redirects to a 404 and the compose healthcheck never passes. `lib/courses.ts` is
deleted (step 30) while `e2e/home.spec.ts`, which tsconfig includes, still imports it. The same
design handed dashboard deviations to #30 although #30's body has no dashboard criterion and the
progress ACs belong to #35. It also changed two ADR-0007 obligations (deletion owner, the single DB
client) without amending ADR-0007, and marked modules server-only without saying how Vitest and the
seed import them.
Rule: For every step, walk the CI jobs that run on it (compose up + healthcheck, image checks, e2e,
typecheck over every included file), not only the unit check in brackets. Introduce a new runtime
requirement in the same step as whatever supplies it. Check each follow-up issue's body really covers
what is deferred to it. Amend an accepted ADR wherever the design changes one of its obligations.

### 2026-10-30: A host-side CLI that imports workspace packages built only to gitignored dist (#29, judge_design round 1, operations)
Design 4.5/6.4 runs `pnpm seed` (`tsx scripts/seed.ts` via `pnpm --filter`) right after `compose up` in CI
and on Stepan's machine. It imports `@academy/db` and, through it, `@academy/lesson-schema`; both export only
`./dist/index.js`, `dist/` is git-ignored, and a plain `pnpm --filter` script runs no `^build`. In CI no host
build has happened yet (ERR_MODULE_NOT_FOUND); on Stepan's machine `dist` predates the new tables.
Rule: For every new host-side command, trace each workspace import to its package `exports` and state what
builds it first (a turbo task with `dependsOn: ["^build"]`, or an explicit build), on a clean clone and on a
machine with a stale build.

### 2026-10-30: An isolation recipe that covered typed commands, not scripts, the shared image tag or the coder (#29, judge_design round 1, operations)
Design 13.5 isolated the tester with `-p academy-t29`, but `check-image-migrations.sh` runs bare
`docker compose` (it targets project `academy`), tester builds, including mutated ones, retag the shared
`academy-web:local`, and the coder's `pnpm dev`/`pnpm seed` steps read the root `.env` (Stepan's db),
so an unmerged migration could land in `academy_db-data`.
Rule: Isolate by environment, not by flags: export `COMPOSE_PROJECT_NAME`, use a separate image tag and a
DB port in a sourced helper, apply it to every role that runs anything, forbid writes to the root `.env`,
and assert the owner's volume is unchanged at teardown.

### 2026-10-30: A two-write seed whose rerun reports success on a half-written state (#29, judge_design round 1, operations)
The seed creates the user, then links the credential account, without a transaction; the rerun branch
"user exists -> update password" updates 0 rows when the account is missing and prints "updated".
Rule: For every idempotent operator command, list the states a crash between its writes can leave, and make
the rerun converge from each (or make the writes atomic), with a test that starts from the half-written state.

### 2026-10-30: Mutation rows checked against the design's model of the library, not the library's condition (#29, judge_design round 1, security)
I-dal's M14 precondition aged `updated_at`, but Better Auth refreshes on `expiresAt - expiresIn + updateAge <= now`
(`session.mjs:178`), so the mutation stays green. U-log put its canary on line 2 of a message the logger truncates to
line 1. I-host expected a response where `auth.handler` throws before the router. The secret rule "refuse short values
everywhere" ignored `BETTER_AUTH_SECRETS`, which overrides `options.secret` (`create-context.mjs:76`). The seed's
password re-key, the only recovery path, left existing sessions valid. The DAL guard scanned pages only, although
server actions are public POST endpoints.
Rule: For each mutation row, read the library's exact condition and the code path the test input takes (truncation,
throw vs response), and state why the input crosses it. For every "refuse X" invariant, grep the library for every
other source of X (env names, option aliases). A credential reset revokes sessions. An enforcement test covers every
entry point kind the rule names (pages, server actions, route handlers), with an explicit allowlist.

### 2026-10-30: A security property was tested only through a side effect that a fallback also produces (#29)

Round-2 security FAIL. Sign-out was tested by "cookie gone, `/` redirects to sign-in", which the cookie
deletion alone produces; Better Auth's `signOut` also swallows a DB delete failure itself
(`sign-out.mjs:49-53`), so a sign-out that never revokes the server row stayed green everywhere. The design's
failure-mode row assumed the library throws there without reading it. The same round found the DAL guard's
allowlist keyed by file, so any later export in an allowlisted actions module was exempt.
Rule: For every security property (revocation, authorization), assert the server-side state itself (the old
token is rejected), read the library's error handling before claiming where a failure lands, and allowlist
the narrowest unit the check can see (an export, not a file).

### 2026-10-30: Isolation recipe checked compose only; node entry points and turbo strict mode load the root .env (#30)

Issue #30 design 13.6 / V8: with a root `.env` now present, the architect rehearsed that `docker compose
--env-file /dev/null` ignores it and claimed "exported values win" everywhere else. But `next.config.ts`,
`scripts/seed.ts` and `playwright.config.ts` each call `process.loadEnvFile(<repo>/.env)`, and turbo 2's strict
env mode drops shell variables a task does not list: `build` lists none, so `[B]` (`env -u BETTER_AUTH_SECRET
-u DATABASE_URL pnpm build`) loads Stepan's real secret and DATABASE_URL into every coder build; `test:e2e`
passes only `E2E_BASE_URL`/`SEED_*`, so Playwright loads them too. The image scripts call bare `docker compose`
(reads `.env`; `COMPOSE_ENV_FILES=/dev/null` stops it, verified) and the teardown runs `cksum .env`. Separately,
yaml 2.9.1 `parse()` prints warnings with the quoted source line via `process.emitWarning` (reproduced), which
the typed-error rule for thrown errors did not cover, and the M-leak-rsc mutation added an undeclared prop, so
`next build`'s type check would fail before the leak test could run.
Rule: For "never read file X", grep every entry point for loaders of X (`loadEnvFile`, dotenv, compose) and
trace each command of the recipe through the task runner's env filtering, then state per process why X is
not read. For "no content in logs", cover every output channel of each parser (warnings, emitWarning,
console), not only thrown errors. Every mutation that runs through a build must type-check.

### 2026-10-30: Cross-commit string supply, mutations that miss the shipped code, drift listed by example (#30, judge_design round 1, architecture)
Design rev 1: commit 5's copy button needs lesson strings added in commit 7; E-cat-2 (commit 6) clicks dashboard
rows that arrive in commit 8. E-les-2 fulfils `get-session` after the tab change, the order in which today's
`notifications.tsx` (reads `window.location` on resolve) already passes, so step 36 is unguarded. E-les-3's
"`data-region` on `main`" leaves F6 landing on the same breadcrumb (`region-cycle.tsx` focuses the first
focusable). U-read's M-msg "use `issue.message`" cannot leak the canary: zod 4 messages never echo the input
(run live). 8.4 named a few shadcn differences; the radix-nova registry shows `outline-none`/`ring-[3px]` on
Item, TabsTrigger and TabsContent overriding the design focus ring, the dark `border-input` active tab,
`BreadcrumbPage role="link" aria-disabled`, Badge `rounded-4xl h-5`. `listLearnerFiles` throws
`CourseExportError` while the ADR says the server uses the same listing.
Rule: For every step, list the constants, components and routes it imports or asserts and the step that
supplies each, across commits. Before naming a mutation, read the code the test runs against today and the
library's real output (run it), and state why the assertion goes red under it and was red before the change.
Write the vendored-component table from the registry source in the design, every class, every state.

### 2026-10-30: A tester command the design's own wrapper refuses; a log check that cannot see one-off containers (#30, judge_design round 1, operations)
T-err prescribed `t30 run -d --rm --no-deps -p 127.0.0.1:3231:3000 ...`, but the `t30` wrapper refuses every
`-p` argument (rc 97, rehearsed), the log assertion used `docker compose logs`, which never shows `run`
one-off containers, and nothing stopped the detached container, so `t30 down -v` left it running ("Resource is
still in use") and `docker image rm academy-web:t30` would fail. The same recipe claimed compose never reads
the root `.env` while the image scripts call bare `docker compose` (fixed by `COMPOSE_ENV_FILES=/dev/null`).
Also: `COURSE_ROOT` was not added to `.env.example`, `@academy/web#test` inputs ignored the `course/` files a
unit test reads, and E-leak left fragment trimming, the body-capture race and its runtime unspecified
(6,794 fragments; two already occur in today's server bundle).
Rule: Run every prescribed tester command through the wrapper it must use, once, against a scratch compose
file. Give each detached container a name, a log command and a stop step before teardown. Every new env var
goes into `.env.example`. Every turbo task that reads files outside its package declares them in `inputs`.

### 2026-10-30: A mutation that triggers the forbidden read; a library's "never logs" tested on one call of two (#30, judge_design round 2, security)
Revision 2 isolated the root `.env` behind `ACADEMY_SKIP_ROOT_ENV` and turbo `globalPassThroughEnv`, then named
M-env-turbo "remove the passthrough entry and run [B]": that build loads Stepan's real `.env` (secret and
DATABASE_URL unset by `env -u`), or, on a turbo cache hit, replays the skip line and stays green. The flag's
arrival was also proven only after the fact, by a skip line in a process that could already have read the file.
Separately, V15 "`parseDocument` never logs" spied on parsing only; yaml 2.9.1 `toJS()` logs a collection key
through `process.emitWarning` at the default `logLevel` (`addPairToJSMap.js:57`), so the chosen `"error"` was
right by accident and no test pinned it.
Rule: A mutation of a guard must never perform the act the guard forbids on the real asset: check it statically
or against a canary copy, and prove a protective setting before the first run that depends on it. When claiming
"library X never logs", spy on every call the code makes (parse and convert), and pin each protective option
with its own mutation.

### 2026-10-30: A mutation that defeats the isolation it guards; a closed error set missing a case its ADR promises (#30, judge_design round 2, architecture)
Design rev 2: M-env-turbo removes `ACADEMY_SKIP_ROOT_ENV` from turbo's `globalPassThroughEnv` and expects the
skip line to vanish from `pnpm build`; under that mutation `loadRootEnv` sees the flag unset and loads Stepan's
real root `.env` into the coder's build, the read Q11 forbids. M-env-flag and M-env-site do the same if anything
beyond the unit file runs while they are applied (`pnpm typecheck` loads `next.config.ts`). Separately, Q8 and
ADR-0009 item 7 promise "unreadable" files give the designed error states, but the "closed" reason set of
`CourseFileError` has no reason for `EACCES`/`EIO`, so the coder must either misreport it as `missing` or let a
raw error become a 500. And step 6 (`node-fs.ts`) used `LEARNER_FILES` from `files.ts`, created at step 9.
Rule: For every mutation, state what else the mutated code does when the commands of its step run, and confine
mutations that weaken an isolation or security guard to the one test file, or to a scratch copy without the
protected resource. For every "closed set" of error reasons, map every failure the call can raise (errno codes
included) and check it against each promise in the ADR. The step-level supply walk covers modules within a commit.

### 2026-10-30: A mutation that switches off the isolation it proves; a widened check run as the wrong user (#30, judge_design round 2, operations)
M-env-turbo removed `ACADEMY_SKIP_ROOT_ENV` from `globalPassThroughEnv` and expected the skip line to vanish
from [B]. With the flag gone, `loadRootEnv` loads the existing root `.env`, and the `turbo.json` change forces a
cache miss, so the coder's real `next build` would read Stepan's secrets: the very read revision 2 removed.
Rehearsed in a scratch turbo 2.11.10 workspace (`flag=UNSET` in build and seed without the entry). C2 was
widened to `find / -xdev -type f -exec sha256sum {} +`, but the runner is `USER node`: `/root`,
`/lib/apk/db/lock` and `/etc/crontabs/root` are unreadable and `find` returns 1 (rc 0 with `--user 0`). That
means a red CI on correct code, or a partial scan if the errors are suppressed.
Rule: A mutation of a safety guard must not run the guarded entry point where the protected resource exists;
prove it in a scratch copy instead. When a check's scope widens, run it once as the user it will run as, and
make it compare the count it covered with the count it should cover.

### 2026-10-30: Widened a source walk to a directory that exists only locally (#30, judge_design round 3)
Revision 3 widened U-env-sites to walk `apps/`, `packages/`, `services/`. `services/` is an empty, untracked
directory in the main checkout; git does not store empty directories, so CI's checkout has none and a plain
`readdir` per root throws `ENOENT`: green on the coder's machine, red in CI on correct code at commit 1.
Rule: Every path a test walks or reads must be tracked (`git ls-files <path>` non-empty) or explicitly optional in
the design; when widening a scan, add a positive control per root.

### 2026-10-31: Prescribed `transition-colors` for focusable rows, which animates the focus ring (#30, judge_code round 1, architecture)
Design 8.4 gave `Item` and `BreadcrumbLink` `transition-colors duration-150` "as button.tsx does", but `button.tsx`
uses `transition-[background-color]`, and Tailwind 4's `transition-colors` includes `outline-color`. Every catalog
row, dashboard row and breadcrumb link fades its focus ring from `currentColor` to `ring` over 150 ms (tester F2);
`proto.css` has no transition on `.item` or `.breadcrumb a`, and the README's `duration-fast` is for hover only. The
8.4 tables were read against proto.css property by property, but not against what the prescribed utility expands to.
Rule: When a design prescribes a Tailwind utility, check what it compiles to (property list included) against the
prototype rule and the global focus rule; transitions name only the properties the prototype animates.

### 2026-10-31: Removed the review and CI controls of the hooks without naming or replacing them (#86, judge_design round 1, security)
The design untracked `/.claude/` and deleted CI jobs `pipeline`/`pipeline-types`. ADR-0005 item 7 accepts deliberate
bypasses because they are "caught by review and by Stepan at merge", and CI was the only place shellcheck, py_compile
and strict mypy of the hooks ran. After the change no hook, settings or agent edit shows up in any diff and nothing
runs those checks, yet "What NOT to build" said "no change to the judge process". The same design took the backup of
the local files only after `done`, though commits A and B still track them and a checkout across commit C deletes the
hooks (gates fail open), and its rollback pushed a refspec from a `--mirror` clone, which git refuses.
Rule: When a change removes files or CI jobs, list every control that relied on them (review at merge, CI checks,
residual-risk ADRs) and replace each or have Stepan accept the loss in writing; back up before the first destructive
step, and run every rollback command once in scratch.

### 2026-10-31: Removed the definition of "the design file" while 33 citations of local design notes stayed tracked (#86, judge_design round 1, architecture)
The #86 design rewrote the `design/flows/ia.md` header to explain only the "research §n" tags and dropped
the line that named `plans/50-...-design.md`, while 24 "the design file" citations in `design/flows/*`,
4 "design section 2" in `design/system/`, and 5 "(design D2/D3)" comments in `apps/web` (the #30 design)
stayed in tracked files with no decision about them. The grep covered path references only, not citations
of a note by name ("design file", "design Dn", "research §n", "review n").
Rule: when files leave the repository, grep tracked files for every way they are cited (path, file nickname, section and decision ids) and decide each group explicitly in the change list or in "What NOT to build".

### 2026-10-31: Rollback from a mirror that git refuses, and no guard for the window after the untracking commit (#86, judge_design round 1, operations)
Design section 7 restored main and deleted branches with `git -C <mirror> push origin <sha>:refs/heads/<name>`;
a `git clone --mirror` sets `remote.origin.mirror=true` and git answers "--mirror can't be combined with refspecs"
(rehearsed in scratch; pushing to the URL works). The same design took its only backup of the local process files
after `done`, although from the untracking commit on a rebase across it deletes `.claude/` from disk (rehearsed) and
`stash`/`pop` re-tracks it, and the four commits needed intermediate file states with no stated way to build them.
Its rewrite script took two args but its checks needed two more values, and its rehearsal could not pass its own checks.
Rule: Every rollback and recovery command is run once against a scratch remote before the design ships it; a
design that makes some git operation destructive names the first moment that is true, takes the backup before it,
and forbids the operations by name from then on; a prescribed script's args cover every value its checks compare with.

### 2026-10-31: A gate rule that its own definition makes unreachable, and an allowlist that never reaches the live directory (#86, judge_design round 2, security)
Design 4.2 blocked a process repo "ahead" on a protected branch, with "ahead" = `<local protected branch>..HEAD`; on
`main` that range is always empty (rehearsed: 0 after the commit, and `origin/main..HEAD` is 0 after the push), so an
honest commit on process `main` passes `pr` and Stop and is pushed without a PR. The same design wrote the allowlist
`.gitignore` only into the import dir; the attach of the live `.claude/` leaves it deleted, and the grant, local
settings and state show as untracked and are staged by `git add -A` (rehearsed), while V12 described the attach as
clean.
Rule: For every gate rule, construct the exact state it must block (including the "already pushed" variant) and
evaluate the rule's own definition on it before writing it down; every file a design creates is traced to the
directory where it must exist at runtime, and rehearsals run on a copy of that directory as it is today.

### 2026-10-31: Fixed the 33 listed citations and stopped, 37 of the same class stayed (#86, judge_design round 2, architecture)
Revision 2 rewrote exactly the citations round-1 F1 listed ("design file", "design section 2", "(design D2/D3)")
and its test grep matched only those forms. "design 4.Q5", "design 7.2", "(Arch A4)", "O N2", "decision A8" in
`design/pages` and `design/system`, "round-4 advisory" and "(design 6.3)" in ADR-0008 cite the same unpublished notes
in 37 more tracked lines, although the round-1 lesson above already said to grep section and decision ids.
Rule: A finding's list is an example of a class. Run your own broad grep for the class, record the pattern and the
hit count in the design, classify every hit, and prefer one convention that covers the class over per-line edits.

### 2026-10-31: Attach rehearsed without the file the import commit adds, and a tool pin assumed to install on the runtime Python (#86, judge_design round 2, operations)
Revision 2 claimed (V12, 3.2) that attaching the live `.claude/` to the pushed import commit changes no file and shows
only #86's edits. The allowlist `.gitignore` exists only in the import commit; the mixed reset writes nothing, so on a
copy of the live directory `status` shows ` D .gitignore` and the grant, state and flock as `??`, P1.4 fails and the
new `pr`/Stop rule blocks. The same revision kept "mypy 1.20.2 under /usr/bin/python3 3.9.6" as an open question,
while `pip download` answers it in seconds: no distribution for 3.9.
Rule: Rehearse every operator command on a copy of the real directory and diff the copy against each file the
commit being attached adds; an unverified install is checked with `pip download --only-binary :all:` on the target
interpreter before the design relies on it.

### 2026-11-01: A dirty-tree gate over an allowlist .gitignore saw nothing new (#86)

The process repo ignores `/*` and re-includes known paths, and the design's gate checked only
`git status --porcelain`. Any new top-level entry (`rules/`, `skills/`, `commands/`, which Claude
Code loads as instructions) was ignored, so it never reached a process PR. The tester found it,
then two more of the same class (`__pycache__/` at any depth, `core.fileMode=false`).
Rule: When a gate decides "nothing changed" from git output, design it against what git hides,
not only what it shows: list ignored entries and compare them with an explicit local-runtime
list, and pin every config that changes the output (`--untracked-files`, `core.fileMode`,
`core.fsmonitor`, assume-unchanged/skip-worktree flags).

### 2026-11-03: A guardrail delivered through a file the session does not load (#89, judge_design round 1, security)

The #89 design made "every non-main session runs the R3 probe first" its only mitigation for sessions
without hooks. It put the probe and the R7 fallback in CLAUDE.md section 6 and called R7 (does the
worktree session load CLAUDE.md?) "docs only". The rehearsal showed a Desktop worktree session loads no
process CLAUDE.md. So the probe, the git-verb rules for `.claude/` and every other instruction-only rule
never reach the session, and sections 1, 2, F1, the ADR residual and the accepted section 10 all claimed
coverage that did not exist.
Rule: For every instruction-level guardrail, name the channel that delivers it to the session it targets,
and treat "is that channel loaded there" as a load-bearing rehearsal row, not a docs row.

### 2026-11-03: Put the mitigation for sessions in the instructions file those sessions do not load (#89, judge_design round 1, architecture)

The design's guard for worktree sessions (the R3 probe, the common-dir invocation, "branch then init") lived
only in CLAUDE.md sections 6-7, and R7 ("does the worktree session load that CLAUDE.md?") was classed as
docs-only. R7 failed: a Desktop worktree session loads no process CLAUDE.md, so the mitigation never reaches
the sessions it exists for, and section 10 gave Stepan no step to compensate.
Rule: For every instruction-based mitigation, name the mechanism that delivers it to the target session and
rehearse that delivery; if it is not loaded automatically, the design names who gives it (an absolute-path
first prompt) and the residual risk says the guard runs only when that happens.

### 2026-11-03: Cleanup procedure trusted "git refused nothing" as "nothing lost" (#89)
The #89 design's sync step ran `git worktree remove` (no `--force`) on a process worktree and treated a refusal
as the only sign of unsaved work. Under the allowlist `.gitignore` (`/*`), git deletes every ignored file without
refusing: parked states and allowlist-hidden new dirs went silently (rehearsed). The same design told Stepan to
resolve feedback conflicts in GitHub's editor, which moves `headRefOid`, so its own merged check failed on that
path.
Rule: For every destructive step in a procedure, list what it deletes under the repo's ignore rules and gate it on
the check that sees those files. Walk each documented recovery path through the procedures that run after it.

### 2026-11-03: Contingency branch deleted an imported module; a sanitiser test on JSON-escaped output; a live row red by construction (#89, judge_design round 2, architecture)
Revision 2 said "if L1 fails, remove the SessionStart entry and both new files; steps 2-5 proceed", while step 4's
report imports `printable` from one of those files. W14c checked raw JSON stdout for control characters, which
`json.dumps` escapes anyway, so dropping `printable` could not turn it red; the report's `printable` had no row.
L5 accepted `forwarded=true` as an outcome but stopped on a missing injection, which that outcome guarantees
before merge (the origin/main settings copy has no entry yet).
Rule: Walk every contingency branch through the later steps' imports; assert a sanitiser on the decoded value the
consumer reads, not on the encoded transport; for each live-check outcome you accept, derive what the other
assertions must then show.

### 2026-11-03: A fallback path passed its own check and failed the next step's gate; a guard row that tests presence, not wiring (#89, judge_design round 2, operations)
Revision 2 added `fetch origin pull/<n>/head` for a deleted remote branch; steps 3-5 passed, but `FETCH_HEAD` is not
a remote ref, so the step-6 gate's "commits on no remote" refused the removal (rehearsed). W10(f) made `{wt}/.claude`
unreadable and expected "cannot inspect", while 1.3 checks `.git` first and `lexists` returns False there, so the
design's own code reports "not a process worktree; run init". W18 checked that each script is still wired, which a
changed matcher also satisfies.
Rule: Walk every fallback branch of a procedure through all later steps and their gates; for each test row, trace
which check of the design fires first on that setup; pin a safety-critical config by exact equality, not by presence.

### 2026-11-03: The sync's "app already removed the folder" branch was not walked through its own gate (#89)
Design section 7 step 6 runs the gate `worktrees "<wt>"` (1 or 2: stop, ask) and then says "already gone
(`is not a working tree`): `worktree prune`". When the app archives the product worktree first, the gate prints
the prunable line and exits 1, so Stepan is told to stop while that line tells him to prune; and `worktree remove`
on the missing folder exits 0 with no "is not a working tree" message at all. W12(f) skipped the gate, so the
self-test pinned a path the doc never lets Stepan take. Same class as the round-2 lesson above, one branch later.
Rule: For every documented branch of a procedure ("if X already happened"), run the doc's commands in the doc's
order on that exact setup, gates included, and make the test row run the same sequence.

### 2026-11-03: Hardening specified for create only, while the ADR reads it as a property of every workspace (#31, judge_code round 1, security)
Revision 11 pinned the container create body as an exact allowlist, and design 6.1's dispatch table starts every
existing container whose labels match the key (never-started, adopted after a 409, and every stopped one that ran
before) without saying which HostConfig it carries. `LABEL_SCHEMA` is bumped only for label-parse changes, so a later
spec change (#88's egress filter, a tighter limit) never reaches existing workspaces, yet ADR-0002 item 6 says the
egress residuals "last until the egress filter ships". The tester found the never-started half (F3); nobody had
stated the scope.
Rule: For every security property set at object creation, state in the ADR whether it holds for objects created
earlier, and name the mechanism (schema bump, spec-version label, compare-and-recreate) that carries a later change
to them; a follow-up that relies on it gets the same sentence.

### 2026-11-02: Security properties stated by spelling, by name, or by an untestable probe (#31)

The #31 design refused `checks/` in the starter by comparing path segments as text (a symlinked segment or `Checks`
on the case-insensitive Mac bind mount still packs the grader files), let `DELETE` remove a volume by name while
claiming foreign objects with our name are never changed, guarded the container hardening with a denylist of
forbidden fields, checked "workspaces cannot reach the service port" with a DNS name that never resolves there, and
filed workspace -> `host.docker.internal` -> Postgres superuser (shell in the db container, adjacent to the
socket-holding service) as a residual without Stepan's decision.
Rule: State every isolation property by its effect and give it a check that fails on the bad case: compare file
identity (dev, ino) not names, verify labels before every destructive call, assert exact allowlists of security
fields, probe reachability by IP with a positive control, and put any residual that contradicts an ADR's decision to
Stepan as an open question.

### 2026-11-02: LEARN steps unsized, and library failure shapes and contracts assumed (#31, architecture)

The #31 design gave no LOC estimate per step while S8, S11, S13 and S20 each bundle 90-150 lines; S1's "done when"
claimed a lockfile diff without fastify, which the lockfile does not hold; the error contract ignored Fastify's own
400/415 errors and 404 handler; the classifier expected ETIMEDOUT where docker-modem's timeout yields ECONNRESET;
the convergence table re-created containers without re-ensuring the network; reconcile's lesson set had no rule for
one invalid lesson among valid ones; I-hardening asserted CapEff, which is zero for any non-root user anyway.
Rule: In a LEARN design, estimate every step's LOC and split above 60; derive each failure shape and each
framework-level response from the library source or docs, not from the name of the option; and for every guard,
write the variant without the guarded property and confirm the assertion fails on it.

### 2026-11-02: Test and recipe isolation designed for a quiet daemon and a careful shell (#31)

The #31 design asserted in integration teardown that every object present at the start still exists, while turbo
runs the db and web suites in parallel and they remove their own testcontainers; let test decoys and helpers carry
no marker the teardown could find, with no sweep of crashed runs; made the S23 recipe's isolation depend on
exports surviving in one shell (a `down` elsewhere hits project `academy`, and web still resolves to
`academy-web:local`); left the compose `environment` block for the tunables unspecified; let GC force-remove a
running workspace when the bind-mounted working tree is on another branch; and claimed the socket probe on the CI
runner with no CI step that checks it.
Rule: Design operational checks for a shared, busy host: assert only what this run owns, mark every object a test
creates, carry the project/tag explicitly on every command of a manual recipe, list every env var each process
receives, never force-remove a running workspace on derived state, and back every "verified on CI" with a CI step.

### 2026-11-02: A fix verified on the host while the failure lives in the container, and a residual left as a pointer (#31, security round 2)

Revision 2 of #31 refused `Checks` by `(dev, ino)` but tested it only in a host temp directory on APFS, while the
service compares inodes on Docker Desktop's bind mount of the course, where inode numbering is unverified. It also
recorded the Q-W1 residual as "Q-W1's answer and the residual it accepts", keeping ADR-0002's "no access to internal
services" and describing the reopened db port as "can reach Postgres" (it is a superuser with a default password and
`COPY TO PROGRAM`), without web's adjacency to the socket holder or LAN reachability, and accepted W2 as REACHABLE on
"Docker Desktop" without saying how that is detected.
Rule: Run each isolation check in the environment where the attack happens (inside the container, on the real mount),
or name the probe that proves the host test transfers; and write a residual as the full text the ADR will carry,
including the worst consequence and the ADR sentence it amends.

### 2026-11-02: A cleanup that deletes other runs' objects without the label check, and a consumer list built from config only (#31, operations round 2)
Revision 2 of #31 added a setup sweep that removes leftovers of earlier test runs, but its own removal helper refuses
everything not of this run, so the sweep runs outside it, with no per-object inspect and no red run; a filter bug would
remove `academy-db-1` and then the freed `academy_db-data`. The db port change listed host-port consumers from config
and CI only and missed the web's connect hint (`docker compose up -d --wait db`, which cannot fix a db that is up but
unpublished) and the README procedures that start the db and then connect from the host.
Rule: Every function that deletes objects it did not create inspects each one and applies a unit-tested predicate
before acting, with a mutation in the table; and when a change removes something others rely on, grep messages, hints
and docs for it, not only config and scripts.

### 2026-11-02: Step order checked per row, not against what later rows write (#31, architecture round 2)

Revision 2 of #31 sized every LEARN step and stated "each done-when uses only files that exist at that step", but
S37's done-when needs `.env.example` lines that S38 writes, S32's auth mutation targets `/v1/settings`, which S33
registers, and S21/S22 test-first cases exercise `ensureRunning`, which only S23 assembles; a `DockerRuntime
implements WorkspaceRuntime` written at S21 would also turn commit 8's typecheck red until S26.
Rule: After decomposing, walk the steps in order and, for each done-when and each commit, list every file, route,
function and interface member it touches and the step that creates it; any later step is a defect. Name the entry
point every test-first test calls.

### 2026-11-02: A new test pinned the opposite of the algorithm it serves, and tests referenced a deleted revision (#31, architecture round 3)

Revision 3 of #31 added I-gc-primitives, asserting that `removeContainer`/`stopContainer` refuse a container whose
labels do not parse, and 5.1 said "every destructive call refuses both" `other-schema` and `invalid`; but reconcile
(6.5) must stop running `invalid` containers and remove stopped ones through exactly those primitives. The unit tests
use a fake, so the contradiction would ship green and leave such containers running forever. The same revision kept
"as rev. 1" for I-half (a)-(e), I-idem, I-oom, I-pids, U-lock and U-idle, while rev. 1 had been overwritten in the
git-ignored `plans/`, so the tester could not write them test-first and the "I-half (b)" mutation had no target.
Rule: When adding a test for a primitive, read every caller's rule for that primitive and make the asserted predicate
the one the callers need; and a design file is self-contained: never refer to an earlier revision of itself.

### 2026-11-02: Written-out integration tests had no isolation unit, and one asserted a state the spec rules out (#31, operations round 4)

Revision 4 wrote out I-idem, I-half, I-network-pruned, I-gc-primitives and I-reconcile-invalid with exact object
counts "filtered by the test instance", while instances were per test file and nothing removed objects between
tests: earlier tests' containers make the counts red and keep the instance network busy, so I-network-pruned cannot
remove it. I-pids case 3 ran `kill -9 -1` as uid 1000 and expected the container to keep running, but 4.5's own
spec runs `sleep infinity` as uid 1000 under docker-init, so it dies and the container stops.
Rule: For every test that asserts counts or removes shared objects, state what else exists in its scope at that
moment and who removes it; and check each expected state against the container spec (uids, PID 1, Cmd) it runs on.

### 2026-11-02: Agent hard rules protected three names and a verb list, and allowed the read that leaks the secrets (#31, judge_design round 6, security)

Revision 6 wrote H1-H10 as the only protection of the owner's stack for an agent coder and tester. H2 forbade naming
project `academy`, `academy_db-data` and `academy-web:local` in a listed set of verbs, so `docker stop academy-db-1`,
`docker exec academy-db-1 psql ...`, `docker run -v academy_db-data:...` and `network connect` to the owner's networks
all passed the rule, and H3 even named "by exact name" as the allowed removal form. H2 also allowed `docker inspect` of
owner objects by name, which prints `BETTER_AUTH_SECRET` (interpolated from the root `.env`) from the web container's
`Config.Env`: the secret H4 protects, by another path.
Rule: A rule that protects objects defines the protected set by label and name pattern and forbids the effect (change,
exec, mount, attach, read env); verbs are examples. For every secret a rule protects at its source, list every place
the secret is copied to (container env, logs, rendered config) and close each read path too.

### 2026-11-02: Spawn entry checks admitted only a fresh start, not the resume the stop rule creates (#31, architecture round 6)

Revision 6 split the coder work into spawns A-E with a stop rule (stop after any commit, or mid-commit with the dirty
files listed; the orchestrator re-spawns "the remaining range"), but every entry check was written for a spawn
starting at its first commit on a clean tree ("HEAD equals A's hash", "log prints nothing", "HEAD is commit 14",
TS1 "15 (or 16)" commits). A re-spawn after a context stop, the exact #30 failure the split exists for, would fail
its own entry check and stop; allowed `fix(workspace)` commits break the commit-number checks too.
Rule: When a design defines a stop-and-resume protocol, walk the resume at every possible stop point (after each
commit, mid-commit) against the entry checks, and key resume checks on the hand-off notes (HEAD, commit list, dirty
files), never on fixed commit numbers.

### 2026-11-02: Owner snapshot recorded names and states, so a recreate or `down -v` + `up` diffed identical (#31, operations round 6)

Revision 6's tester procedure guarded Stepan's stack with a before/after snapshot of volume names, image Id and
container `Names State Image`, taken only at the tester's start. A recreate, restart or `down -v` + `up` of project
`academy` leaves those strings identical (shown with a throwaway container: empty diff after a recreate), and spawns
B and C, which run the predicate-based removal code against the same daemon, had no snapshot at all.
Rule: An "untouched" snapshot records identities and lifetimes (container Id, StartedAt, RestartCount, port bindings,
volume CreatedAt, network Id), is proven by recreating a throwaway object and seeing the diff, and brackets every
phase that mutates the daemon, not only the last one.

### 2026-11-02: One protection, two scopes: H3 and the harness said "not created by this run", H2 said "the academy list" (#31, judge_design round 7, security)

Revision 7 scoped removals (H3) and the harness's no-`{{json .}}` rule (12.2) to every object the run did not create.
But it limited H2's effect ban and its formatted-read rule, the text every brief quotes, to the academy owner set. A
bare `docker inspect` of another compose project's container (its env secrets), a `docker exec`/`stop` of it, or a
`docker tag` onto `postgres:17.6-alpine`, which Stepan's stack runs, broke no rule.
Rule: When a design states one safety property in several places, write its scope once, as the widest the property
needs (here "everything on the daemon this run did not create"). The named lists are subsets used for detection, not
the boundary of what is allowed.

### 2026-11-02: Widened the protected set, then wrote an open-ended exception that hands any protected image back (#31, judge_design round 8, security)

Revision 8 added class (5), every image this run did not build, to H2. In the same paragraph it wrote the exception
"creating this run's own container or image from an image already on the daemon uses the image as a base: it is this
run's own create". The examples were node, postgres and the reaper, but the sentence named no closed list. So
`docker run --rm <another project's image> env`, or `cat` of a `.env` baked into it, or a build `FROM` it, counted as
this run's own create, although H2 forbids reading the filesystem or environment of a protected object. R8-O1 used the
same opening for P-SNAP: `<img>` became "any alpine- or debian-based image" on the daemon, and P-SNAP step 5 runs
`docker start` on it. That executes the image's own ENTRYPOINT (`academy-web:local`, or another project's image)
inside a step that R7 had pinned to `node:22.23.4-alpine`.
Rule: An exception to a protection is a closed list of named objects, never a general class. Check every exception
against each forbidden effect (read secrets, execute, retag, replace) before writing it. An ops-convenience change must
not widen which protected objects a step runs code from.

### 2026-11-02: Widened H2 to every node image but left the recipe's node removal in place (#31, judge_design round 8, operations)

Revision 8 put "every `node` image" into H2 class (5) and listed `docker image rm node:22.23.4-alpine` as a forbidden
example. H3's exact-name list still did not include a pulled image. The 12.6 teardown still removes
`node:22.23.4-alpine` when its snapshot shows the image was absent, and the new 12.6 last line says the recipe "never
acts on the protected set". A coder quoting H2 at S39 has to stop under H10, and on this Mac node is absent, so the
branch is live.
Rule: When a revision widens a protected set or adds a forbidden example, grep every procedure in the design (recipe,
harness, teardown, P-SNAP) for commands on the newly protected objects, and either change the procedure or write a
closed exception in the same revision.

### 2026-11-02: A closed "only pulls" list omitted BuildKit's own fetches (#31)
Revision 9 made H9 say "The only pulls on this daemon are ... Any other pull is an H10 stop", but the prescribed
`:t31` builds (12.6 `up --build`, S36/TS6 `docker build`) make BuildKit resolve the `# syntax=docker/dockerfile:1`
frontend of `apps/web/Dockerfile` on every build and fetch an absent `node:22.23.4-alpine` base, as the daemon's own
build history shows. The stop rule fires on the recipe it governs, the same mechanism as round 8.
Rule: Before closing a list of what a step may pull, run, or touch, read the build logs (`docker buildx history logs`)
and the Dockerfiles of every prescribed build, and list every image they resolve, `# syntax` frontends included.

### 2026-11-02: Closed a build-log case by line form and missed half the forms (#31, judge_design round 10, operations)
Revision 10 wrote that H9's build case "shows only as" three log lines. Every `:t31` build on this daemon also prints
`resolve docker.io/docker/dockerfile:1@sha256:... done`, `[stage n/m] FROM docker.io/library/node:22.23.4-alpine@sha256:...`
and `resolve docker.io/library/node:...@sha256:... done`, and a no-`# syntax` node build prints the last two. S36 and
TS6 pull node first, so a literal reader cannot fit those lines into case (b) "node when absent" and stops under
"any other build fetch". This is the third round with the same mechanism.
Rule: State a closed case by the object a line names (the image), not by the log line's form. When you quote example
forms, collect them from every log of the prescribed builds (`docker buildx history logs` piped through
`grep docker.io/ | sort | uniq -c`) and say they are examples.

### 2026-11-04: Exact smoke commands that cannot run as written under the flags they sit beside (#33, judge_design round 1, architecture)
Design 5.1 gives the volume setup as `docker run --user 0:0 --cap-drop ALL --cap-add CHOWN ... install -d -m 0755 -o 1000 -g 1000 /workspace/home /workspace/home/work`.
`install` chowns `/workspace/home` to 1000 right after creating it, then root without `CAP_DAC_OVERRIDE` must
create `work` inside a `1000:1000 0755` directory and gets EACCES: every smoke run, and so every
`build-workspace-image.sh` run, fails at setup. Design 5.2 S12 asserts "no output" from
`command -v curl wget gcc cc sudo` inside `docker exec sh -c`; `/bin/sh` on Ubuntu is dash, whose `command -v`
looks up only the first operand (checked: `dash -c 'command -v nonexist ls'` prints nothing, rc 127), so a gcc,
wget or sudo in the image could never turn the row red.
Rule: For every exact command in a design, trace it under the exact privileges and the exact shell it runs with
(capabilities after `--cap-drop`, `/bin/sh` of the image), and give multi-name checks one name per invocation.

### 2026-11-04: The delivery script moved the owner's tag before its own check, with no way back (#33, judge_design round 1, operations)
Design 4.1 builds with `docker build -t "$image"` and runs `smoke.sh` afterwards. When the smoke fails (or is
interrupted), `academy-workspace:dev`, the only image name the service uses, already points at the unverified build;
the previous image is left untagged and its Id is recorded nowhere. README 8.1 and section 9 say only "it ends with
`SMOKE result OK`": nothing tells Stepan to stop before deleting the `.env` line, how to put the old image back, or
how to roll #33 back (README has a rollback paragraph for #31). In the same design, S6 checks
`for d in ...; do test ! -e "$d/claude"; done` in `sh -c`: a loop's status is its last iteration's, so a `claude` in
any directory but the last one passes (checked with dash: `/usr/bin/ls` present in the middle iteration, loop rc 0),
and the R-e5 red run plants it in `/usr/bin`, the last iteration, so the red run cannot show the hole.
Rule: A script that tags an owner's image verifies under a candidate name or records the previous Id and restores it
on failure, and the README states the failure path and the rollback. Every loop or list in an exact check fails on
the first bad element (`|| exit 1`), and its red run plants the fault in a non-last element.

### 2026-11-04: The fake-docker exception to "agents never build :dev" never checks that the stub is the docker it runs (#33, judge_design round 2, security)
Design D5 and 13 [O2]/[O2b] let the coder (step 5), the tester and the operations judge run
`PATH="$scratch/nodocker:$PATH" bash scripts/build-workspace-image.sh academy-workspace:dev` on the strength of a stub
`docker` alone. Nothing proves the stub is what resolves: agent Bash calls do not keep shell variables, so in a call
that did not set `scratch` the prefix is `/nodocker` and `command -v docker` prints `/usr/local/bin/docker` (checked
in this session). The expected result of a working guard (rc 2, no `fake docker called`) is the same whether or not
the stub resolved, so a missing stub is invisible exactly until the guard is broken, and the coder runs [O2b] right
after writing the guard, before any other test of it. Then the real daemon builds `academy-workspace:dev-candidate`
and moves Stepan's `academy-workspace:dev`: decision 5 broken by the very check meant to protect it.
Rule: A safety net that lets an agent run a forbidden command must be verified in the same command before it is
relied on (the stub answers with its marker and exit code), and must not depend on a variable from an earlier call;
better, build PATH so the real tool is unreachable at all (`PATH=<absolute stub dir>:/usr/bin:/bin`).

### 2026-11-04: README commands proven in non-interactive zsh, broken in the owner's interactive zsh (#33, judge_design round 2, operations)
Revision 2's README 8.1 step 4 puts a trailing `# comment` on every command (`bash scripts/build-workspace-image.sh   # must end with "SMOKE result OK"; on FAIL stop here (step 2)`,
`docker compose up -d --build --wait workspace   # recreates ...`, the `sed`, `grep`, `echo` and `printenv` lines, and
the rollback block). Stepan's interactive zsh has no `interactivecomments` (`zsh -i -c setopt` lists only `interactive`),
so `#` is an ordinary word and `;` inside the comment ends the command. Pasted, the build line exits 2 with the usage
error, `compose up` gets services named `#`, `recreates`, ..., and the `sed` line still deletes the `.env` override:
the exact "delete before building" order the README warns against. The 5.6 evidence ran the lines with `zsh` on a
script, where comments always work.
Rule: Run every README command block the way the owner runs it (pasted into `zsh -i` with his own config), not as a
script; keep comments out of copy-paste blocks.

### 2026-11-04: The delivery script told the owner to delete an image Id without checking it is not the current one (#33, judge_design round 2, operations)
Design 4.1 step 7 prints "the previous image stays on disk untagged; docker image rm ${prev} frees it" whenever `prev`
is an Id. A rebuild with unchanged inputs and the same context label is fully cached and BuildKit gives it the same
Id, so `prev` is the new `:dev` itself; after the README's container removal, following the message deletes
`academy-workspace:dev` and every lesson answers `image-missing`.
Rule: A printed clean-up instruction names an object only after the script has proven it is not the one just
delivered (`prev != new`), and says "unchanged" otherwise.

### 2026-11-04: The fake-docker harness proves the stub runs only after the row that would hurt (#33, judge_design round 3, security)
Revision 3's harness (`plans/33-fake-docker-guard.sh`) checks that `docker` on its own `PATH` is the stub, but the
script under test can still reach the real client by an absolute path (`/usr/local/bin/docker`) or a `PATH=` line of
its own. The positive control that would catch it (`t33-stubcheck`) only increments `failures` and the harness goes
on to `academy-workspace:dev` with `CLAUDECODE` removed, so one coder slip runs a real `docker build -t
academy-workspace:dev-candidate` (a protected D2 name) before the run turns red. Reproduced with stubs only
(scratchpad `sec3/repo2`): both rows report `docker-called=no` after the "absolute" docker was reached.
Rule: A control that proves a safety precondition gates the risky step: run it first and stop on its failure; never
let it only change the final verdict after the risky step has run.

### 2026-11-04: A long-lived connection authorized once silently weakened an ADR's revocation guarantee (#32, judge_design round 1, security)
The #32 design authorizes the terminal WebSocket once, with a 30 s ticket, and the relay keeps it open until the
session's `expiresAt`, up to 7 days. The residual (8.2, ADR-0011 Consequences) names only "sign-out in another tab".
It does not say that ADR-0008 item 10 ("re-keying deletes every session, so a leaked password's sessions die with it")
and item 5 (the e2e proves sign-out revokes on the server) stop holding for an open terminal. A leaked password's
terminal survives the documented recovery. No recovery step is given, Stepan was not asked, and no test shows what a
deleted session does to an open relay.
Rule: When a design adds a connection that is authorized once and stays open, list every ADR item that promises
revocation (sign-out, re-key, account deletion). For each, bound the lag with a test, or give a documented recovery
step and get the owner's explicit decision on the residual.

### 2026-11-04: Long-lived session object specified by its happy path; packaging fact assumed (#32, judge_design round 1, architecture)
The #32 design checked Next's internals carefully but left the session and relay lifecycles to the coder: the resume
snapshot is serialized while up to 1 MiB is still unparsed by the headless terminal (bytes lost on resume); the old
tab's asynchronous `close` after a takeover can detach the new tab; no single teardown names the headless terminal,
timers and listeners for each end path; the relay's 10 s connect timeout can stay on the upgraded socket (the same
mechanism the design neutralised for docker-modem). It also claimed `zod` is in the standalone `node_modules` "because
the bundle uses it", while Turbopack bundles zod and tracing copies only runtime requires, so the custom server cannot
import it in the image. And the D6 write path had a writer test but no test of the browser calling it.
Rule: For every long-lived object (session, relay pair, socket), write the event order for attach, detach, takeover and
each end path, including late events from the replaced party, plus one teardown that releases every resource, each with
a test. Every npm import of code that runs outside the bundle is checked against the traced tree, not the bundle.

### 2026-11-04: Register guards that pass while watching nothing (#32, judge_design round 1, operations)
R-SNAP ran `bash <clone>/plans/32-owner-snapshot.sh`, but `/plans/` is git-ignored, so no clone has the script: both
runs exit 127 with empty output and `diff` of the two empty files passes. R-RUNS used `docker volume ls --format
'{{.CreatedAt}}'`, a field `volume ls` does not have, so it prints nothing on stdout in the very case it exists to catch.
Rule: Every guard command in a register states its success as "rc 0 and a positive marker" (last line `== end`, an
explicit count), never only "prints nothing" or "diff is empty". Check each path exists where the command runs and
each `--format` field against the command's own formatter.

### 2026-11-04: CJS interop and a pre-decided stop left to the coder (#32, judge_design round 1, operations)
`import { Terminal } from "@xterm/headless"` passes tsc (NodeNext) and vitest but throws "Named export 'Terminal' not
found" under plain Node, so the service image would crash at startup. `import next from "next"` fails tsc under NodeNext,
while the type-correct `next.default` is undefined at runtime. The design also told the coder to stop if
`@fastify/websocket`'s non-upgrade GET answer is outside the closed error set, and 11.3.4 always answers an empty 404,
so the stop was certain. A `wsHandler` route with its own HTTP handler avoids it.
Rule: For every new CommonJS package imported from ESM code that runs outside a bundler, name the import form and
add one plain-`node` import of the built module to a step check. A "stop if X" condition that the pinned source already
decides is resolved in the design, not passed to the coder.

### 2026-11-04: Section 6 omitted what the e2e suite now writes into the owner's own stack (#32, judge_design round 1, operations)
The README runs `pnpm test:e2e` against Stepan's own compose stack as his only user. After #32 the terminal specs type
into his real workspaces, take over his tabs and write `lesson_progress` rows that are never cleared. Section 6 did not
mention this.
Rule: When a change adds a durable write or a side effect to a flow that tests drive, check whether the documented test
command runs against the owner's own data, and put the effect, or an opt-in gate, in section 6.

### 2026-11-04: A pre-auth upgrade handler with no error containment, and an S-B1 test its own verifier refuses (#32, judge_design round 2, security)
Revision 3 moved the terminal upgrade out of Next into `publicServer.on("upgrade")` but never said that the dispatch
catches errors, or that the raw socket gets an `error` listener before anything else. Node's HTTP server removes its own
socket error handler before it emits `upgrade` (that is why `ws`'s `handleUpgrade` starts with
`socket.on("error", socketOnError)`), and Next's `start-server.js:236-243` wraps its upgrade handler in try/catch. The
custom server replaces that code and does neither. The ticket verify also checks the MAC by string length, then calls
`timingSafeEqual(Buffer.from(given), Buffer.from(expected))`. A percent-encoded non-ASCII character in the MAC passes
the length check, gives buffers of different byte lengths, and `timingSafeEqual` throws `RangeError`. Thrown inside the
listener, or rejected from an async `handle`, this crashes web for every user, without authentication, from anything that
reaches 127.0.0.1:3080, including a workspace container on Docker Desktop (ADR-0002 residual 3). Separately, U-relay-cap
mints a ticket with `dl` 7 days ahead, which the design's own verify refuses (`dl > now + 3600 s`), so the S-B1 guard
cannot pass as written.
Rule: Every handler that receives a raw socket before authentication attaches an `error` listener first, runs inside one
try/catch or `.catch` that destroys the socket, and has a test that it survives a reset and a malformed request. Check
each input's charset and byte length before any primitive that throws on bad input. Build every guard test's fixture
through the real verifier and confirm it is accepted.

### 2026-11-04: Round-1 lifecycle fixes added async gaps and timers whose overlaps were never walked (#32, judge_design round 2, architecture)
Revision 3's A-B2 flush made attach asynchronous, but takeover still looks only at `session.client`, which is null
during the flush: two attaches inside one flush (U-registry-race's own scenario, a renewal racing another tab, two
restored tabs) both get `attached` and the first becomes a silent zombie with no 4001, and `Session.end` never closes
a socket whose flush is pending. The renewal timer had no rule for leaving the running state (a taken-over tab silently
takes the session back 15 minutes later, against D4) and loops at once when the deadline is within the 60 s margin,
which happens at every natural session expiry because the DAL reads with `disableRefresh`. The flow-control gates
reset only on attach, so a client that detaches while paused freezes the shell until someone re-attaches. A
`markStopping` with no session has nobody to clear it. Step 6 imports zod in `apps/web`, which has no zod dependency.
Rule: For every async step and timer a fix adds, walk what happens when a second event of each kind arrives inside
the gap and when the object leaves its state during it; for every gate or mark, name who clears it on every exit
path, including "nothing was there". Check each new import against the importing package's own dependency list.

### 2026-11-04: Dedicated e2e lessons checked against named lessons only; leak.spec opens every lesson (#32, judge_design round 2, operations)
Revision 3 gives `terminal.spec.ts` and `region-keys.spec.ts` dedicated lessons "asserted different from every lesson
other specs open by name". `leak.spec.ts` opens every lesson in a loop, so with auto-start (D5) and takeover (D4) a
parallel worker takes the terminal spec's session over with 4001 mid-test; the three region-keys engines also share one
lesson in parallel. The guard as written cannot see a loop.
Rule: When a test needs exclusive use of a shared resource (one user's session, one workspace), prove exclusivity by
scheduling (project dependencies, serial workers) or a runtime check, after grepping every spec for loops over the same
collection, not by comparing the names other specs mention.

### 2026-11-04: A bash function placed "at the end" but called mid-script, at a point whose state was not walked (#32, judge_design round 2, operations)
Section 9 put `run_e2e_stages` at the end of `isolated-stack.sh` and called it "after check-image-migrations.sh".
Bash runs top to bottom, so the call exits 127. Only one call position works anyway: after line 255 db loses its host
port, which the seed and E-echo need, and after line 251 the probes that e2e-cleanup prepares for have already run.
Rule: For a script change, name the exact line a new call goes after, define every function above its first call, and
list the stack state at that line (ports published, services up) that the new step depends on.

### 2026-11-04: Changed the byte encoding of a compare but kept the mutation row written for the old one (#32, judge_design round 3, security)
Revision 4 compares the MAC as `timingSafeEqual(Buffer.from(mac, "latin1"), Buffer.from(expected, "latin1"))`. Latin1
writes one byte per UTF-16 code unit, so the round-2 input (42 base64url characters plus `é`) gives a 43-byte buffer and
never throws. The mutation row "compare without the charset check -> U-ticket: the non-ASCII MAC throws RangeError"
therefore stays green, and no other U-ticket case diverges without the token regex: the guard S2-B1 asked for has no
test that can fail. Latin1 also maps U+0141 to 0x41 (`A`), so without the regex a MAC with one character shifted by
0x100 is accepted.
Rule: When a fix changes how an input is encoded, re-run every test input and mutation row of that input through the
new encoding (one `node -e` per case) and replace the cases whose correct and mutated outcomes now coincide.

### 2026-11-04: State tables walked per state, not per object that outlives a socket or a promise (#32, judge_design round 3, architecture)
Revision 4's tables gave every state an action, but not every object that crosses a state change. The browser's
processed-bytes counter and `ackTimer` are not tied to a socket, so bytes parsed from the old socket are acknowledged on
the renewal socket, whose service counter `sent` restarts at 0 (row 7), and the service closes it 1008. Row 27 sets
`renewal = null` without closing it, so a slow renewal socket attaches later and the tab takes itself over (4001, TO)
with a leaked socket that row 38 can no longer close; an `openTerminal`/`startEnvironment` result arriving after unmount
does the same to the next mount. No cell sends `resize` after `attached`, so every first attach leaves the shell at
80x24. On the service, row 16 ignores only a 404 from `resizeExec`; any other rejection inside a `message` listener is
an unhandled rejection, and the service has no handler, so the process (every shell) dies.
Rule: In a state table, list the objects that survive a transition (counters, timers, sockets, in-flight promises) and
give each an owner and a disposal in every row that replaces or drops it; every async call started from a listener
names its rejection's action; every "set X = null" for a socket says "close X".

### 2026-11-04: A prescribed shell command that the CLI rejects, and two specs of one output that disagree (#32, judge_design round 3, operations)
Section 9 row 6 told the coder to run `docker image ls -q academy-web:$TAG academy-workspace-service:$TAG`. The docker
CLI takes at most one reference (`cli.RequiresMaxArgs(1)` in `cli/command/image/list.go`; usage
`ls [OPTIONS] [REPOSITORY[:TAG]]` in the 29.9.2 binary). Simulated with a stub docker: in `found=$(...)` form, `set -e`
ends every run with rc 1 and no STOP line; in `[ -n "$(...)" ]` form, the check passes silently and misses a planted
`academy-web:t32`. R-PREFLIGHT plants only a volume, so it could not catch either. Separately, 3.1 says `main.ts` logs
`web: startup failed: <error name>`, while R-SMOKE expects `StandaloneConfigError: .next/required-server-files.json
missing`. The prototype prints `web: startup failed: StandaloneConfigError`, so the check cannot pass.
Rule: Before prescribing a CLI command verbatim, read its usage line (or the source's argument rule) for every
argument form you give it, and say how a non-zero exit is handled under `set -e`. When one output is specified in two
places (code and check), write it once and quote that line in the other place.

### 2026-11-04: Prescribed a synchronous `term.reset()` while the design itself leaves writes queued (#32, judge_design round 4, architecture)
3.6.1 rows 6, 6a, 24 and 24a call `term.reset()` and then write the snapshot. xterm 6.0.0 documents that `reset()`
"does not clear input buffers and does not reset the parser, thus the terminal will continue to apply pending input
data" (`src/browser/CoreBrowserTerminal.ts:1260-1267`); `CoreTerminal.reset` (`src/common/CoreTerminal.ts:244-250`)
never touches the `WriteBuffer` or `_parser`. Revision 5's own G3 test builds the exact state where this bites: a
frame of the old socket is still queued when row 24 switches. Those bytes are parsed after the reset, before the
snapshot (duplicated scrollback, an alt-screen switch applied under the snapshot), and a parser left inside an OSC or
CSI sequence by a connection cut swallows the head of the snapshot. RIS (`ESC c`) written in band runs
`InputHandler.fullReset` (`_parser.reset()`, then the same `reset()`) in order with the queue.
Rule: When a design calls a library method on an object that has a queue (a terminal write buffer, a stream, a
batching renderer), read the method's doc and body for what it does to queued work, and walk the row with work still
queued; prefer the in-band form when order matters.

### 2026-11-04: Scoped a security rule by check kind, missing the capped command checks (#68, security)
The #68 design required `attempts.limit` only on ready quiz and bug-hunt checks, calling them "the
security-relevant kinds", and left a missing or misspelled `attempts` block on a command check to human review
(F5 deferred). #15 §2.5.6 computes the cap of 10 on `model-routing` and `cost-estimate` as an anti-enumeration
control (uncapped, the adaptive attack passes in about 30-200 submissions), so a typo there ships an uncapped
check with CI green. The same design said "no source gives an upper bound" while #15 states 3 for quiz and
bug-hunt.
Rule: Before scoping a security rule, list every place the source design calls the control a security property
(grep the cap's number and "attack"/"enumerat" in it); a rule that covers a subset by kind needs a machine check
for the rest, not a reviewer.

### 2026-11-04: Defined "counted" in the contract ADR in words that prejudge the rule it defers (#68, architecture)
The #68 design's counting sentence and ADR-0001 item 8 say "a result is counted only when the grader scored
the submission", then hand timeout and budget-exhausted counting to ADR-0007 (#101). A timeout or an exhausted
budget is not a scored submission, so the sentence already answers "not counted", while #101 counts
budget-exhausted results, proposes counting timeouts, and ADR-0007 item 4 calls a timeout the learner's work
missing the bar. Two ADRs would then disagree, and #34 would implement whichever it read first.
Rule: When a contract defers part of a definition to another ADR, state only the fixed floor (what is never
counted) and point to the other ADR for the rest; read the deferred-to issue and check every case it decides
against your sentence.

### 2026-11-04: Follow-ups and the module hand-over left only in a gitignored plans/ file (#68, architecture)
The #68 design's section 7 (what #43 and #44 must add when their lessons go ready, including the
`trace-attribution` task.md mismatch) has no issue target, and F1-F5 are written as "comment to add" with no
step that posts them. `plans/` is in `.gitignore`, so all of it is lost when the worktree is archived, and the
module authors meet R4 as a red CI with no explanation.
Rule: Every follow-up and hand-over in a design names its issue and the step that posts it (before the PR
opens, linked from the PR body); nothing a later task depends on lives only in plans/.

### 2026-11-04: Parallel-branch rollout covered only "drafts rebase later", not merge order (#68, operations)
The #68 design's failure table says drafts in other worktrees rebasing onto R4 break nothing, and the hand-over
says R4 turns content:validate red when a module 03/04 lesson goes ready. It never says what happens when the
two PRs overlap: main has no required-up-to-date protection (private repo, free plan: the protection API answers
403), and PR CI runs on the merge commit as of its last push. A content PR that flips a quiz to ready, green
before #68 merged and merged after it, turns main's content, checks (workspace starter-walk real-course guard)
and e2e jobs red; if the content PR lands first, #68's fixed "18 lessons" table is incomplete.
Rule: A design that tightens a contract other open branches feed names the merge order both ways (who rebases
and re-runs CI, who migrates what) and every CI job that reads the affected data, since nothing on GitHub
enforces an up-to-date base here.

### 2026-11-04: ADR "never counted" floor copied category names without #15's condition (#68, judge_design round 2, security)
Revision 2 of the #68 design states in ADR-0001 item 8 and §1.2 that format errors and stage-0 rejections are
never counted, unconditionally. #15 §2.5.6, which the design cites for the caps, exempts a format error only when it
is rejected before any comparison with the key (bug-hunt: "not scored"). Without that condition #101/#34 may label a
result that already carried score or aggregate-count feedback a format error, and the cap of 10 on `model-routing`
and `cost-estimate` stops bounding enumeration.
Rule: An exemption from an anti-enumeration counter is written with the property that makes it safe (the result
shows the learner nothing computed from grader material), never as a bare category name.

### 2026-11-04: Rollout check diffed from a hard-coded base and only course/ (#68, judge_design round 2, operations)
Revision 2 §7.1 (a) runs `git diff --name-only 39ef0b8 origin/main -- course/` before the PR opens and before merge.
After the first rebase the fixed base keeps listing lessons already migrated, so "empty output" can never again
mean "nothing to do"; and a main commit outside course/ (a test fixture with a ready quiz, a schema change) leaves
the PR merging on CI computed against an older main, which is the round 1 problem itself.
Rule: A "has main moved under this PR" check tests the effect (`git merge-base --is-ancestor origin/main HEAD`,
else rebase and re-run CI), and any listing of what moved diffs from the current merge base, never a literal sha.

### 2026-11-04: Moved a check from parsed to raw input and lost the parser's default (#68, judge_design round 3, architecture)
Revision 3 runs U1 on the raw YAML before the parse result is inspected and makes it fail closed when `checks` is
"not a list of check objects". The schema has `checks: z.array(Check).default([])`, so a ready lesson with no
`checks:` key (a theory lesson; `apps/web/test/course-fixture.ts` has two) is valid and every loader accepts it, but
U1 would report it with a false message. The design claimed "a non-array `checks` fails the array schema" and "U1
adds no restriction on any valid lesson"; neither holds for the absent key.
Rule: When a check moves from parsed to raw input, list every `.default()` / `.optional()` / transform on the path
it reads and give the raw-input rule the same meaning for each (absent `checks` = empty list), with a test.

### 2026-11-04: A corpus scan was offered as proof that a fail-closed rule adds no restriction (#68, judge_design round 3, operations)
Revision 3 states that U1 "adds no restriction on any valid lesson (scan in §3)". The scan covered the lessons that
exist in three checkouts, all of which happen to carry a `checks:` key. A valid shape absent from the corpus (a ready
`type: theory` lesson without `checks:`, accepted by `Lesson` through `.default([])`) is reported by the new
fail-closed branch, so the first such content PR would get a red `content` job on a valid lesson.
Rule: A scan shows only that today's files pass. Before claiming a new rule restricts no valid input, walk the schema
for valid shapes the corpus lacks (defaults, optional keys, every lesson `type`) and add a test for each.

### 2026-11-09: A persisted fact derived from filtered inputs was stored without the filter key (#101, judge_design round 1, architecture)
The design makes a check-kind change ignore old results (D8 Q8, deviation 4: "a quiz with limit 3 must not inherit
nine command failures and close at once"), but `check_closures` has no `check_kind` and `isClosed` reads any closure
row for the check id. A command check closed after 10 failures and later changed to a quiz is closed at once with
`failedCount` 0, the exact case the deviation names. The startup recompute also skips `completed` rows, so a closure a
lowered limit causes in a completed lesson (a check added after completion) is never persisted, and a later raised
limit reopens it, against D4.
Rule: When a persisted row records a conclusion drawn from filtered facts, store every key the filter uses and apply
the same filter on read; and run "persist when it happens" over every row where it can happen, not only the rows
whose stored status can still change.

### 2026-11-09: A port type for live data reused the committed-fact type with a field live data cannot have (#101, judge_design round 1, architecture)
`LiveCheckProgress` `done` carries a `ResultFact`, which requires `attemptFinishedAt: Date`; a result streamed from a
running attempt has no attempt finish time, so #34 must invent one, and `ResultView.finishedAt` then shows it.
Rule: For every port another issue implements, fill each field of its types from the state the implementer has at
that moment; a field it cannot know gets its own live type, not a placeholder.

### 2026-11-09: Amended an ADR's rules and left contradicting sentences of the same item standing (#101, judge_design round 1, architecture)
Rule 7 makes `applyLessonOutcome` "the only writer of `completed`" and rule 4 derives `in-progress` for a lesson with
no counted check, while ADR-0007 item 5 "Theory lessons" (a "mark as done" action completes them) and the #34
follow-up "write step (4) as `UPDATE ... WHERE status = 'in-progress'`" stay in force; the second blocks the
`not-passed` -> `completed` move rule 4 allows.
Rule: Before finishing an ADR amendment, grep the whole ADR for every sentence the new rules touch (writers, status
values, guards in follow-ups) and replace or retire each one explicitly.

### 2026-11-09: Streamed live results that a rolled-back finish later turns into uncounted errors (#101, judge_design round 1, security)
Design 7.1 shows a running attempt's live `done` results (with `details`) through `LiveAttemptSource` before the finish
commits, R34-8 streams them, and 6.2/R34-14 say a failed finish rolls back and the sweep makes every included check an
uncounted `error`. A learner who can make the finish fail (a NUL byte or invalid UTF-8 echoed into the grader message,
which Postgres `text` rejects) sees counted-failure messages derived from the key for free, against the owner's F1
counting floor.
Rule: For every result path, show nothing to the learner that is not yet durable with its counted status, and check
that no later failure (rollback, sweep, deadline) can turn a result already shown into an uncounted one.

### 2026-11-09: Mapped learner-triggerable grader deaths to the uncounted platform `error` (#101, judge_design round 1, security)
Rule 3 maps "no exit code because the runner failed (container gone, ...)" to `error`, never counted, and leaves a grader
killed by a signal unmapped. Graders run learner code as children in the learner's own container (verify_hook.py:253
feeds hidden probe input to the learner's hook), so that code can save the input to `/workspace` and SIGKILL its
parent or stop the container: an uncounted, unlimited probe of grader material.
Rule: When a contract exempts "platform" failures from a counter, define them by who can cause them; anything code
under test can cause after grading started is counted.

### 2026-11-09: Prescribed a pnpm command that fails verbatim, and missed existing tests the new index breaks (#101, judge_design round 1, operations)
Design 5.1 prescribes `pnpm --filter @academy/db run db:generate -- --name check_limits`; pnpm 10.28 passes the `--`
through and drizzle-kit exits 1 ("Unrecognized options for command 'generate': --, check_limits"). Design 5.4 lists only
new db tests, but the planned migration turns six existing ones red in a scratch run: migrate.int.test.ts I1 compares an
exact table list (no `check_closures`), and schema.int.test.ts I11 seeds a `running` attempt in `beforeAll` and then
inserts more `running` attempts of the same lesson, which `attempts_one_running_idx` now rejects with 23505.
Rule: For a new constraint or table, grep every existing test that inserts into or enumerates the touched tables and
name its change in the design; never prescribe a script invocation without its exact argument-forwarding form.

### 2026-11-09: Rollback covered only "start the previous image", not a code revert (#101, judge_design round 1, operations)
Design 2.7 and 5.3 say the migration is additive and the previous image ignores it, which holds. A `git revert -m 1` of
the merge deletes `0002_check_limits.sql` and its snapshot, and CI's append-only step fails on that (rehearsed), so the
standard revert path is closed and the design does not say what to revert instead.
Rule: For a PR that adds a migration, state the code-revert plan (which commits are reverted, that the migration commit
stays, and that removing the schema is a later forward migration), checked against check-append-only.sh.

### 2026-11-09: The run deadline relabels a started check's runner fault as an uncounted platform stop (#101, judge_design round 2, security)
R34-15 says itself that a started check reaches the deadline without a row "only when web's runner itself failed", and
R34-3 sends a twice-failed result insert to the deadline. The deadline then writes `platform-stop: run-deadline`
(uncounted) for every rowless included check, started or not. D11 says a platform fault after the grader started
spends the attempt, and the deadline never stops a started grader (R34-4's timer already did), so this reopens an
uncounted end after start for every runner fault a learner can provoke through grader output.
Rule: A cleanup path that writes results for "rows still missing" must split them by the same cause test the main
rule uses (here: did the grader start?), never apply one label to all of them.

### 2026-11-09: Replaced an ADR sentence by quoting it with "..." and dropped the safety clause in the elided part (#101, judge_design round 2, architecture)
S11 quotes ADR-0007 "Dashboard" sentence 3 as "Course percentage = completed counted lessons / counted lessons;" and
replaces it with rule 8, which does not restate the rest of that sentence: "a course with 0 counted lessons shows no
percentage (never `0/0`, `NaN` or `0%`)". In the same revision 7.4 adds a fallback that makes `next` non-null with
`totalLessons` 0, the exact state the dropped clause forbids: `CourseProgress` renders `<Progress max={0}>`, whose
indicator is `width: ${(0 / 0) * 100}%` = `NaN%` (components/ui/progress.tsx:35).
Rule: When an amendment replaces a sentence, quote it whole (no "..."), list every clause it carries and say where each
clause now lives; walk any new view state through the components that render it.

### 2026-11-09: The sweep sets an attempt `error` unconditionally while the same amendment defines `error` as "at least one result is error" (#101, judge_design round 2, architecture)
S2 redefines the attempt status `error` as "at least one result is `error`", and R34-14 / R34-15 / S13 set the attempt
`error` whatever rows it holds. Under D10 an attempt whose every included check committed its row before a crash gets
no new row from the sweep, so it ends `error` with `errorCheckCount` 0, and the R34-11 end text reads "Проверок со
сбоем: 0".
Rule: A cleanup path that sets a summary status derives it with the same aggregation as the normal path, over the rows
present after its own inserts.

### 2026-11-09: Code-rollback plan reverts individual commits of a repository that squash-merges (#101, judge_design round 2, architecture)
Design 5.6 says "`git revert -m 1` of the merge" and "one PR that reverts commits 9, 7, 6, 5, 4"; the repository
squash-merges (CLAUDE.md section 2 item 7; main is `... (#120)`, `... (#116)`), so main holds one #101 commit, with no
merge commit and none of commits 1-9.
Rule: Write a rollback plan against the history the merge method produces, and rehearse it on a scratch clone merged
the same way.

### 2026-11-09: Rerouted an input class without grepping the tests that send it (#112, judge_design round 1, architecture)
The design sends every non-terminal upgrade, `//[` included, to the request listener through `shouldUpgradeCallback`
and changes the shared harness to use it, then states "All existing relay tests ... must stay green unchanged".
Three tests send `//[` or `/elsewhere` through that harness and expect the relay's containment: relay-robust.test.ts:77
(400 for a malformed URL), relay.test.ts:316 (one F4d line for 100 malformed URLs) and relay.test.ts:329 (S5-N1, a
flood of one contained kind does not hide another). Under the design each gets the stand-in's keep-alive 308, never
closes within the 5 s test timeout, and logs nothing. Two of them pin a security finding, and the design does not
say what replaces them.
Rule: When a design changes where an input goes, grep every test for that input (here `//[`, other non-terminal
paths) before writing "unchanged", and for each test that changes, name its replacement and the mutation that
turns it red.

### 2026-11-09: Live-check layout copied two of the Dockerfile's runner COPY lines and left out the migrations (#112, judge_design round 1, operations)
Design 8.4 step 2 assembles the image layout in place by copying `dist/server` and `.next/static` only. The
Dockerfile runner stage also copies `packages/db/drizzle` (and `public`), because Turbopack resolves the migrations
folder from the standalone root (`[turbopack]_runtime.js` ABSOLUTE_ROOT + `packages/db/dist/migrate.js` -> `../drizzle`),
which gives `apps/web/.next/standalone/packages/db/drizzle`. The build does not trace it there, so web would exit 1
at stage apply and step 4's "wait for `web: database migrations applied`" never happens: L1-L6 cannot run.
Rule: When a test plan rebuilds an image layout outside Docker, copy every runner-stage COPY line of the Dockerfile
(or say why one is skipped), and run the entry once in that layout before sending the design.

### 2026-11-09: A mutation that changes code the test's input never reaches (#112, judge_design round 2, architecture)
Design 7.1 W1 lists M2 "restore the `emit` to a `nextFacing` with a silent listener -> no status line -> red". W1
runs through `createPublicServer`, whose `shouldUpgradeCallback` sends every non-terminal path to the request
listener, so the dispatch (where M2 changes code) never sees W1's requests: under M2 alone W1 still gets 308 and stays
green. The mutation only goes red together with M1 (no callback), which the design does not say, and the patch must
also stand in for the removed `nextFacing` dep inside app.ts.
Rule: For every mutation, trace the test's input through the mutated code path; if an earlier layer (a filter, a
callback, a guard) keeps the input away from the mutated line, the mutation must also remove that layer, written as
one exact patch.

### 2026-11-09: Mutation guards that fail silently and are followed by `;` (#112, judge_design round 2, operations)
Design 8.3 step 1 chains `[ ! -e "$B" ] && cp && patch --forward && ! cmp -s "$F" "$B"`, then `;` runs the test.
Dry-run on a scratch copy: a left-over backup and a patch that leaves the file unchanged both make the chain return
1 with no output, and the test still runs on an unmutated (or stale) file. For M3 against W4 the expected result is
"stays green", so a guard failure there is reported as the expected outcome. A plain `diff -u <src> <copy>` also
writes headers that `patch -p1` cannot resolve ("File to patch:", rc 1), and a refused hunk leaves `<file>.rej` next
to the source.
Rule: A guard in a test procedure must print a distinct line and stop the call when it fails (`|| { echo "GUARD
FAILED <M>"; exit 1; }` before the test), and a patch-file recipe must give the exact command that produces paths
the apply step strips correctly (`diff -u --label a/<path> --label b/<path>`), plus cleanup of `.rej`/`.orig`.

### 2026-11-09: New early exit left a neighbouring doc comment false; a mutation row's red set not walked per test (#103, judge_design round 1, architecture)
The design makes the lesson branch `continue` before `unknownCheckKeys` when the YAML fails, but leaves its doc
comment (validate.ts:65-69, "runs whether or not the lesson parses") untouched; once a YAML parse can fail there, the
comment is false on its plain reading. C9 M4 (failed lesson not counted) lists T3-T5 as red and omits T6, whose only
lesson fails and whose `[1, 1, 1]` count becomes `[1, 1, 0]`; the tester is told to report any deviation as a design
defect, so a correct mutation run would be reported as one.
Rule: When a change adds an early exit before a function call, reread that function's doc comment against the new
path; for every mutation row, evaluate each new test's assertions under the mutation, not only the ones it targets.

### 2026-11-10: A destructive e2e guard keyed on a variable the owner's .env and CI's own command both set (#106, judge_design round 1, security)
D8 says the reset spec skips without E2E_BASE_URL and never runs on Stepan's 3080 stack. Design 7.4 implemented only
the first half: "skipped unless E2E_BASE_URL is set", reasoning that the default URL is the owner's stack. But
.env.example:34 offers `E2E_BASE_URL=http://127.0.0.1:3080` as a root .env line, playwright.config.ts:8-12 loads the
root .env into process.env, and ci.yml:190 sets exactly that value; README:139 documents the override. Any of these
makes the spec reset the owner's own working folder. "Is the variable set" is not "is this not the owner's stack".
Rule: Guard a destructive test on a signal only the disposable stacks produce and that the owner's .env cannot supply
(read before loadRootEnv), and refuse the owner's default origin explicitly; check each half of the decision's wording
against .env.example, README and CI before writing the guard.

### 2026-11-10: Tester commands neither run at base nor match CI's checks job (#106, judge_design round 1, operations)
Design 7.5 prescribed the tester's commands without running them at e469b09. Run verbatim, command 4 was red there
(a pre-existing 5 s timeout under host load), and command 6's `--glob '!lib/copy.ts'` did not exclude
apps/web/lib/copy.ts, so it printed 87 lines. 7.5 also left out `pnpm build`, check-build-course.sh and the
porcelain check that ci.yml runs, and section 9's "each commit builds and is green" had no command behind it. E-reset
asserted that a file was gone without creating it in the same test.
Rule: Run every prescribed gate command once at the base in a scratch clone and record its output in the design.
Mirror every step of the CI job the change touches. Back a per-commit claim with a loop command. Give every
"X is gone" e2e assertion its own setup and a check that X exists before the action.

### 2026-11-10: Library calls and test queries assumed to work in the context the design puts them in (#106, judge_design round 1, architecture)
Design 7.3 said `getByText(regionKeyHint)` keeps matching once the hint is split into `<kbd>` parts, but
@testing-library/dom 10.4.2 `getNodeText` joins only the element's own text nodes, so panel tests :260 and :267 go
red. Section 5 had Notifications `flushSync` on `IDLE_CLEARED_EVENT`, which the watcher's `stop()` dispatches inside
the panel's effect cleanup; React 19.3.1 runs that under CommitContext, where `flushSync` logs an error and flushes
nothing. Test I1 (warning in 10 min, "no read at 9:59") contradicted the design's own 5 min read cap. The AlertDialog
state table copied proto.css but not the `<dialog>` UA max-height/overflow the prototype relies on at 320x200.
Rule: For every library call and test query the design keeps or adds, read its installed source for the context it
will run in (commit phase, nested markup, UA defaults), and run each named test input through the design's own
schedule before writing the expected result.

### 2026-11-10: Gate loop whose known red hides the steps after it, and a guard that can skip silently in CI (#106, judge_design round 2, operations)
Design 7.5 command 8 chains typecheck, lint, test, build, check-build-course and porcelain with `&&` and sends
stdout to /dev/null. The pre-existing lesson-markdown timeout is red on this host every time, so the loop printed
`commit <base> red` and never ran the build (no `.next/standalone` afterwards). The flaky rule's "red alone -> a real
failure" is also red at base: the file alone timed out twice at load 38-45 and passed only with a longer timeout.
Section 2.8 says CI runs the destructive spec, but if the spec skips there nothing fails. On main's turbo.json the
switch does not reach the task (`DS=undefined`), so one lost passthrough entry or a live `.env.example` line skips
the spec and CI stays green.
Rule: A per-commit gate runs every step on every commit and reports each step's exit code; a known flaky red never
stops the later steps. Run it at base first: base must come out green under the rule. A guard that may skip must
fail the run in the one place where it has to run (CI with the switch set).

### 2026-11-10: Layout rules placed in a cascade layer that the elements' own utilities beat; e2e asserts not run through the tool's rules (#106, judge_design round 2, architecture)
Design 2.2 puts `.lesson-layout > .resizable-handle { display:none }` and the [R3-N7] frame rule `flex:none; height:12rem`
in `@layer components`, while the same elements carry the Tailwind utilities `flex` (handle, 2.7) and `flex-1` (frame,
2.5). Tailwind 4.3.3 declares `@layer theme, base, components, utilities` (index.css:1), so the utilities win: the
handle shows and takes focus in one-pane mode, and the "fixed" terminal still grows to the lesson's height below 30rem.
The CSS comment and key decision 2 claim the fix anyway. Two tests were also red on correct code: terminal.spec.ts:217
`toHaveAccessibleDescription` (Playwright pads every non-inline child, so `inline-flex` Kbd parts add spaces), and
E-dialog-small (Radix AlertDialog focuses Cancel with `preventScroll: true`, so in a dialog that scrolls inside, the
focused footer stays clipped). The commit plan also missed six existing `WorkspaceClient`/`EnvironmentDeps` literals in
open-terminal.test.ts, terminal-revoked.int.test.ts and environment.test.ts, and LL1's actions in commit 9.
Rule: For every CSS rule, name the layer it lives in and check every class on the same element for a property it sets;
for every kept or new assertion, run the expected value through the assertion tool's own algorithm (accname, focus
options); when a type gains a required member, grep every literal of that type and list each file in its commit.

### 2026-11-10: Sized a flex item without checking its container's main axis (#106, judge_design round 3, architecture)
Revision 4 gives the terminal frame `flex:none; height:12rem` below 30rem and `flex: 1 1 0%` above it, reasoning about
`flex` as if it set the height. The frame's parent is the TabsContent `min-w-0 flex flex-1`, a row flex container
(proto.css:646 too), so `flex` sets the frame's width. With `flex:none` the width is the frame's max-content, which is
xterm's own screen width (DomRenderer.ts:152). FitAddon subtracts the scrollbar from that width, so every ResizeObserver
refit drops about two columns, down to 2 (or, if the scrollbar counts in the intrinsic width, it stays at 80 columns in
a 320 px viewport). Above 30rem the frame has no `overflow` or `min-width:0`, unlike proto's `overflow:auto`, so its
automatic minimum is the current terminal width and every narrowing overflows first. Layer probe 3 cannot fail,
because `flex` on a row item never changes its height. The round-2 judge text assumed the same wrong axis; the design
accepted it without checking.
Rule: Before writing `flex`, `height` or `width` on a flex item, name its container's `flex-direction` (from the actual
class list) and say which axis each declaration sizes. For any item that holds self-sized content (xterm, canvas,
tables), set `min-width:0` or `overflow`. Then add one e2e assert per axis that fails if the rule is wrong.

### 2026-11-10: Closed a "three routes" finding for two of them, and wrote gate strings that are not in the log (#106)
Round-2 operations issue 3 named three ways the destructive spec skips silently in CI: the turbo entry, the ci.yml
step env, and a live `.env.example` line (`E2E_DISPOSABLE_STACK`, `E2E_BASE_URL` or `CI`). Revision 4's
`requireDestructiveE2eInCi` only throws when `CI` is not a root .env key, so a live `CI=` line in `.env.example` (CI's
`.env` is a copy of it) still skips the spec with no throw, while design 10's risk row says "a live `.env.example`
line" throws. Simulated with 2.8's own conditions: `+ CI=true` gives allowed=false, guard=no-throw. The flaky rule
also states its conditions as literals (`Tests 1 failed`, the test's full name) that a grep of the kept log never
finds: turbo forces colour into the log, and vitest prints `Tests  1 failed` with two spaces.
Rule: When a finding names several routes, write one test row per route and run each against the new construction
before claiming the class closed; when a rule says "check X from the log", give the exact command and run it on the
real log at base.

### 2026-11-10: A flaky rule that admits exactly one known test, on a host where other tests time out too (#106, judge_design round 4, operations)
Revision 5's command F counts a red root test as pre-existing only when the lesson-markdown timeout is the single
failure, and 8b says a base that does not pass it means "stop, the gate is broken at base". The anchor was right
against round 3's four logs, which were the only evidence offered. In round 4, three fresh full runs at e469b09
(load 8 to 54 on 10 cores, other sessions running) gave `not-met (0111)`, `not-met (0011)` and `met`: vitest's 5 s
default also hit `starter-walk.test.ts > accepts 2000 entries` (workspace) and a `sign-in-form.test.tsx` retry test
(web). Both pass alone. A tester following 8b verbatim stops at base in two runs of three. The same suite with
`-- --testTimeout=60000` passed through turbo was 6/6 green at load 52-54.
Rule: A local gate on a shared host must not depend on which test the load happens to slow down. Before narrowing a
flaky rule to one named test, run the full suite at base at least three times under the current load; if any other
test times out, fix the timeout class (a gate-wide timeout, CI keeping the default as the authority), not the name.

### 2026-11-10: A focus-return rule written for keyboard focus only, against a design that names the mouse case (#106, judge_design round 5, architecture)
Revision 6 rebuilt "Продолжить работу" from AC30. It acts only "if focus is inside the wrapper", and it remembers the
last `focusin` outside the wrapper as the return target. Safari and Firefox on macOS do not focus a clicked button,
which #138's quiz.md (:289, :360, :600) and acceptance.md (:578, :609) state. In those browsers focus is on `body` at
the click, nothing moves, and the Alert's removal leaves focus on `body`, which AC30 forbids. In Chromium, a click on
plain text first moves focus to `body` with no `focusin`, so the stale target wins where AC30 says "none". The unit
tests put focus on the button with `focus()`, so they cannot see either case.
Rule: For every focus rule triggered by a control, walk the pointer path in each engine the design names (focus on
`body`, or left where it was), and the blur-to-`body` path, before relying on `focusin`. Give each path its own test.

### 2026-11-10: A gate proof read from a tool's dry-run field whose meaning was never checked (#106, judge_design round 5, operations)
Revision 6 added command 4a to prove that `-- --testTimeout=60000` reaches the four vitest tasks and no build task. It
reads `cliArguments` from `turbo run test --dry=json` and asks for `[]` on every non-test task. In turbo 2.11.10 that
field holds the run's pass-through arguments on every task in the graph, `^build` dependencies included, while the
real run gives them only to the named tasks (a planted `lesson-schema` build that prints its argv prints `[]`). So 4a
says `test-args bad` at 0167a5d on correct code, and the design tells the tester to stop there. The design itself
said the turbo leg was "not read from its sources" and rested on 4a, but 4a was never run.
Rule: A check that proves how a tool behaves reads the tool's actual effect (the command lines pnpm echoes in the run's
own log, or a planted script that prints its argv), not a report field. Run it at base green and on a red plant before
it goes into the design.

### 2026-11-11: One of two entry listeners filtered "outside the wrapper", the other did not (#106, judge_design round 6, architecture)
Revision 7's Notifications entry record took `relatedTarget` at `focusin` only when it was outside the wrapper, but took
`document.activeElement` at `pointerdown` unfiltered. An outside press that moves no focus (a Chromium scrollbar press,
a touch press that becomes a scroll) clears the entry while focus stays on "Продолжить работу". The next press then
records the button itself, the activation "returns" focus to it, and the Alert's removal drops focus to `body`, which
AC30 forbids. Every N test started the press with focus outside the wrapper or on `body`, so none could see it.
Rule: When two listeners feed one record, state its invariant (here: the target is never inside the wrapper) and
enforce it in every writer. Walk the clear-then-record order for a press that clears the record but moves no focus.

### 2026-11-10: A mutation named "style" whose literal form kills its own script, and a socket-release test with no timeout stated (#110, judge_design round 1, architecture)
Design 8.4 M17 ("KILL_SCRIPT `pkill -HUP -u 1000 -x sh` style (kills by name)") claims I-term-exit goes red. The
kill script runs as `/bin/sh -c`, comm `sh`, uid 1000, so a by-name HUP on line 4 kills the script itself: `sleep 2`
and the KILL line never run, and the HUP races the second shell's open (two Docker round trips ahead of four), so the
new shell is usually not there yet and the test stays green. The 3 s sleep added to I-term-exit is then a guard nobody
watched go red. Separately, the U-exec detached-start row asserts "the socket closes within 2 s" for M9 without saying
which engine options the test uses; the neighbouring tests build `DockerEngine({ timeoutMs: 200 })`, whose docker-modem
`req.setTimeout` destroys the socket at 200 ms with or without `destroyStream`, so M9 would stay green.
Rule: Every mutation row gives the exact replacement text, and the architect walks it through the mutated program
(including what the mutation does to the script or process that carries it). Every test that asserts a release or
close within a bound names every other mechanism that could close it within that bound and rules each out in the setup.

### 2026-11-10: Mutation scripts written for a shell the test image does not run, and a decision left without its deliverable (#110, judge_design round 1, operations)
Design 8.4 M12 replaces the kill lines with `kill -HUP -- "-$sid"`. busybox ash's `kill` rejects `--` ("invalid
number '--'"), so on node:22.23.4-alpine neither line signals anything and I-term-end-kills goes red because nothing
is killed, not because a group kill misses the jobs: the row does not prove K2. M17's `pkill ... -x sh` matches
nothing on busybox (rc 1 with seven `/bin/sh -l` running), so it survives regardless of the race. Both were found by
running them in a judge's own container. Separately, Stepan's decision 5 asked for a follow-up issue (pkill in the
image smoke), and the design still lists it as open question 3 with no issue text, and its manual check M1 covers
only `exit`, although the SIGTERM path is the one no automated test runs.
Rule: Run every mutation's replacement text once in the test image's shell before writing the row (`docker exec
<own container> /bin/sh -c '<mutated script>'`), and check that it does the wrong thing it names, not nothing. After
Stepan answers open questions, update the design: every answer that asks for an artifact (issue text, ADR line) has
that artifact in the design, and a property no automated test covers gets a manual step.

### 2026-11-10: README prune note implies an academy-only clean-up; rehearsal kept a non-H9 pull and live prunes (#113, judge_design round 1, security)
Design 2.3 introduces `docker builder prune --filter 'type!=exec.cachemount'` as the way to free "the build cache
records" of the web and workspace builds. The command acts on the whole default builder: every other project's
regular build cache goes too, and the text never says so, so Stepan cannot judge what he loses. Design 9.5 R-A..R-C
still prescribe a `docker-container` builder (pulls `moby/buildkit`, outside 16.5 H9) and two prune runs, gated only
on "explicit OK", although the read-only form (`docker buildx du --filter ...`) answers the same question.
Rule: A destructive command written for the owner states its full scope (here: all build cache on this Docker, every
project) next to the command. A rehearsal of a destructive command is read-only by default (the same filter on a
listing verb); a pull or a write outside the hard rules is not a design option behind an "OK" gate.

### 2026-11-10: Pass condition for the probe diff did not match what the probe edit produces (#113, judge_design round 2, operations)
9.3 "After B6" says `diff <worktree>/apps/web/proxy.ts "$T113/ctx/apps/web/proxy.ts"` (and config.ts) "each show
only the added `// t113 cache probe` line". The probe is an append of `\n// t113 cache probe\n` to files that already
end in a newline, so the rehearsed diff shows two added lines, an empty one and the probe (`37a38,39`, `215a216,217`),
and exits 1. Read literally, a correct run fails its own check.
Rule: Write a diff-based pass condition from a rehearsed run of the exact edit (blank lines, exit status included),
or make the edit produce exactly the stated output.

### 2026-11-10: Design recorded runs the architect could not have made (#113, judge_design round 3, architecture)
The architect role has no shell (design 9 says so itself), yet round 3 wrote "re-ran" observations into the design:
D4 adds a `--ignore-scripts` re-run with rc 0, "no output line naming `packages/db`", an `@academy/db` link to the
absent directory and a `pnpm ls` before/after diff with rc 1; the round-3 notes claim G0 was "re-run" on the local
node image and the probe diff "rehearsed in round 3"; R-1 dates the du counts "round 3". The operations judges
recorded only rc 0 for the round-1 frozen install, and 222/223 and `37a38,39`/`215a216,217` in round 2. The numbers
that match a judge run are right but misattributed; the rest is evidence no run produced.
Rule: Every observation in a design names the run that produced it (role, round) and quotes only what that run
recorded. Anything else is marked "to be rehearsed by operations", never "re-ran".

### 2026-11-10: Pre-decided keep/drop rule for a cache mount looked at a counter, not at the cache growth the issue is about (#113, judge_code, architecture)
Design 9.3 B5 decided the workspace deploy mount by "deploy shows `downloaded 0` and the image check exits 0 ->
drop it". Both held without the mount, so the coder dropped it (5c6880c). But pnpm's progress line printed
`downloaded 0, added 0` with and without the store, so it could not tell the two apart, and the builder's own
records show the cost: the deploy RUN record is 117.2 MB with the mount (tester B3 03:31:59, B4 03:33:24 UTC) and
280 MB without it (B5 03:34:46, re-test B4 03:51:24), about +163 MB of build cache on every source-only workspace
build, which is exactly what #113 exists to cut (B4 delta +0.20 GB -> +0.35 GB). The doubled deploy time was the
visible hint.
Rule: A pre-decided rule for a cache or layer change measures the issue's own metric (the step's record size in
`docker buildx du --verbose`, or the Build Cache delta) for both variants, never only a tool's progress counter.

### 2026-11-10: Hard wall-clock kill on apt chosen before the normal durations were known (#130, judge_design round 1, security)
Design 1/5/D2/D6 bounds each apt helper call by `timeout --kill-after=10 "$remaining"` within a 240 s budget and
names "normal durations" as unknown (gate G). The research notes already held a slow but working fetch (#128
42756938732 a1, 5 min 33 s at about 100 kB/s), and gate G then measured green apt RUNs up to 431 s (fetch, ci.yml
42737998827) and 200.5 s (final, ci.yml 42864732752), 2 of 10 green ci.yml fetch RUNs over 240 s. The design would
have turned green builds red, which is the opposite of the issue's done criterion, and its own stop rule (no budget
passes G-A and G-T1 together) sends it back before the coder. A red build on a slow mirror is also the pressure
that later gets "fixed" with a fallback mirror, i.e. by dropping the pin.
Rule: Before bounding a step by wall-clock time, read the measured green-run tail of that step; if the tail exceeds
the bound, bound stalls (no progress, connection timeouts) and the decision to start another attempt, never kill a
progressing download.

### 2026-11-10: Hard wall-time budget on a network phase chosen before its normal duration was known (#130, judge_design, architecture)
Design D2/D6 put every networked apt-get call under `timeout "$remaining"` with a 240 s total budget per helper call
and made the fallback "lower the budget" if gate G failed. Gate G (orchestrator, green runs only) then showed green
apt RUNs of 246.6 s and 431.0 s (fetch, ci.yml 42756938732, 42737998827) and 194.7-200.5 s (final): the design would
have turned at least 2 of 10 green ci.yml builds red, and the fallback rule would have made it worse. The flake the
issue names is fast failure (5xx, rc-0 update with W:, size mismatch), not slowness; apt already retries its own
connection timeouts, so a wall-time kill bounded nothing the issue asked for and added the timeout/kill-after
machinery, F3/F4, H2/H5, two stubs, FI-8..10 and M4/M5.
Rule: Bound a retried network step by attempts and by apt's own no-progress timeouts, never by total wall time,
unless measured green durations exist and the bound sits well above their maximum; a fallback must never tighten a
bound that already kills green runs.

### 2026-11-10: Failure text and cache claims written from memory, not from the paths that produce them (#130, judge_design round 1, operations)
The give-up line ends "the E: and W: lines above name the failing URL", but on the budget-kill path (rc 124) apt is
killed before it prints any E:/W: line: in the ops rehearsal both a stalled InRelease (full 240 s budget) and a slow
but progressing .deb (budget lowered to 60 s for the run) printed the give-up line with no E:/W: line above it, and
the slow case told the reader to "rebuild once these sources answer again" about a source that was answering. H1 also
claimed complete .deb files of an earlier attempt "stay in archives/ and are reused"; the base's docker-clean has
`APT::Update::Post-Invoke { "rm -f /var/cache/apt/archives/*.deb ..." }`, and the rehearsal showed 1 deb after
--download-only and 0 after the next update, so every retry downloads everything again.
Rule: For each failure line, name the code path that prints it and state only what that path has actually printed
before it; read the base's /etc/apt/apt.conf.d before claiming anything about what apt keeps between calls.

### 2026-11-10: The rehearsal for the decisive premise could not fail, and one rehearsal had no rule for its bad result (#130, judge_design round 2, architecture)
Revision 2 rests on `Acquire::http::Timeout=30` being an inactivity timeout and names FI-slow as what settles it.
FI-slow's oracle cannot see a total-request cut: the fault proxy forwards `Range` and `Content-Range`, so a try cut
at 30 s resumes from `archives/partial` and finishes on attempt 1 (rc 0, `complete on attempt 1`, installed, elapsed
>= 35 all still pass), and the "no `Delaying` line naming `/pool/`" check is vacuous because apt's Delaying line
prints the item description (`http://.../20261104T000000Z noble InRelease`, ops r1 out-w75.log), never the pool path.
Separately, FI-6r feeds G-T1d with D but had no rule for the outer 900 s timeout firing (serial per-host retries)
or for D so large that the download-path give-up line is lost on every run, not only "the slowest ci.yml run".
The harness pin guard also greps `tzdata=2026e-0ubuntu0.24.04.1`, which is not in the Dockerfile (it is an ARG).
Rule: For each premise a rehearsal settles, write the oracle that the false premise would turn red (count requests
at the proxy, not only end states) and a pre-decided consequence for every outcome, including the outer timeout.

### 2026-11-10: Stall arithmetic and a fault case left to the tester without checking the harness can show them (#130, judge_design round 2, operations)
Revision 2 put a stalled request at "up to 6 tries x 30 s plus 31 s" (about 211 s) and wrote the header claim "a
stalled connection is ended by apt's 30 s timeout". The ops round-2 rehearsal of the rev-2 helper (FI-hang, hang on
InRelease and on /dists/) showed each apt try opens two connections 30 s apart, so one stalled request costs 391 s:
attempt 1 failed at 391 s, attempt 2 at 842 s, and the outer 900 s timeout fired (rc 124) before attempt 3; the
give-up line cannot print under a stall inside the 15-minute step, and apt names it "Connection failed". FI-6r was
specified in the FI image, which already has ca-certificates 20260816ubuntu0.24.04.2 and python3 from the live
archive: the seven-pin list then fails every attempt with "E: Packages were downgraded and -y was used without
--allow-downgrades", 0 FAULT requests, and still meets every FI-6r pass condition (D would read 49 s and pass G-T1d;
on a pristine base D is 90.7 s and G-T1d fails). The --simulate check without -y let that deterministic failure be
retried three times and reported as "rebuild later".
Rule: When a number or a pass condition is left "to be rehearsed", state the mechanism it depends on (connections per
try, the image's preinstalled versions) and give the case a marker that proves the fault was the cause (FAULT count
> 0, a positive control with the same list and image); a fault case that can pass with zero injected faults is not a
test.

### 2026-11-10: FI-slow fixed with a marker the proxy cannot produce (#130, judge_design round 3, architecture)
Revision 3 made FI-slow pass on "exactly one SLOW line (a cut and resume would be a second request)" and no
Delaying line. `fault_proxy.py` logs SLOW only after the last chunk and its sleep: a request apt cuts raises
BrokenPipe in `wfile.write` and leaves a traceback, not a SLOW line, so cut plus resume still shows one SLOW line.
FI-hang already shows apt's first timeout in a try reconnects without a Delaying line (HANG at 0.1 and 30.1 s,
first Delaying at 60 s), so one cut leaves no Delaying line either. The marker also goes red on a correct helper:
ops r2 FI-slow5 (slow 0.5, completed in 95 s on attempt 1) has 0 SLOW lines because the min-profile proxy dies with
the case container before it logs, and the red branch of FI-slow would then drop the Timeout options.
Rule: Before using a harness log line as a pass marker, read where the harness prints it: on which path (start,
completion, error) and whether it can be lost when the case ends; a marker printed only on success cannot count
failed attempts.

### 2026-11-11: Final-list FI cases prescribed on a fault proxy that buffers whole responses (#130, judge_design round 3, operations)
Revision 3 moved FI-1f and FI-6r to the pristine base and kept `fault_proxy.py` as is. Its pass-through reads the
whole upstream body before it sends the status line, so apt sees no byte until the file has arrived at the proxy.
On 2026-11-11 the snapshot served the by-hash `noble/universe/binary-arm64` index (15.3 MB) in 54.8 s from the
host (TTFB 2.2 s), so through the proxy every try hit `Acquire::http::Timeout=30`: FI-1f printed Delaying 1/2/4/8/16
on that index and no helper line by 376 s; the same list on the FI image ended rc 124 at 330 s. With a streaming
pass-through FI-1f was green (rc 0, attempt 1 after 307 s). The plan reads a red FI-1f as "the list or the base is
wrong", and FI-6r would fail on update, not on the debs, so neither verdict means what the plan says.
Rule: A fault proxy in front of apt must stream pass-through responses (headers on arrival, body in chunks), and a
positive control's red-reading must first rule out the harness (Delaying or Ign on an index in a no-fault case).

### 2026-11-12: `--error-on=any` on the live archive made a partial outage fatal (#130)
D7 put the fetch stage through the same helper as the snapshot. The base's sources span several suites (on amd64
two hosts: archive.ubuntu.com and security.ubuntu.com), and the fetch stage needs none of noble-security or
noble-backports to resolve its five packages. Before, one unreachable suite was `W:` and rc 0, and the RUN was green
(judge_code ops: old commands rc 0 in 14 s with noble-security refused); with `--error-on=any` the same fault is three
failed attempts and the give-up line at 215 s. Section 6 did not list it, so the change turns a green case red.
Rule: Before making a failure strict on a source, list every index the source config fetches, and for each one the
build does not need, state what the old command did when only that index failed and whether the new one keeps it.

### 2026-11-10: Mutation guard exited on a failed patch without restoring the file it had half patched (#129, judge_design, operations)
Design 5.1 applied each mutation with `patch -p1 --forward < M<n>.patch || { echo "GUARD FAILED"; exit 1; }`
and restored the backup only after the test run. Dry-run in a scratch copy (Apple patch 2.0): a two-hunk patch whose
second hunk does not match applies the first hunk, exits 1, and leaves `.orig`, `.rej` beside the file, so the guard
exits with the pending-diff file mutated. The next mutation then backs up the mutated file, and its final `cmp -s`
proves only that it restored the corrupted copy. The procedure also never said which directory `-p1` runs from;
from `services/workspace` it prompts for a file name and writes `Oops.rej` there.
Rule: A patch-apply guard checks with `patch --dry-run -d <root>` before the real apply, keeps one pristine copy
with its sha256 taken before the first mutation, and every exit path (guard failure, red run, interrupted call)
restores from it and checks the sha. Dry-run the failure path, not only the success path.

### 2026-11-10: Restore trap armed before the check that must exit without restoring (#129, judge_design round 2, architecture)
Rewritten 5.1.3 sets `trap restore EXIT INT TERM` in step 1, and step 2 then says: when `F` differs from the
pristine sha and there is no `in-flight`, print `STALE PRISTINE` and "exit without restoring", because `F` was
changed by someone else (a coder fix) and restoring would destroy it. The exit fires the trap, `restore` copies
`pristine.ts` over `F`, the sha matches, and the call prints `RESTORED OK` over the coder's lost fix. The 5.1.5
"already-applied" row ("nothing written") contradicts the same steps. The 5.1.5 cut-off row also says "kill it",
but INT/TERM run the trap, so only SIGKILL leaves the `in-flight` state the row wants to recover from.
Rule: Walk every exit of a guarded script with the trap that is armed at that point. Arm a restore trap only once
the script itself has changed the file (here right after writing `in-flight`), or make `restore` a no-op unless
the marker exists; name the signal a cut-off test sends.

### 2026-11-10: Mutation guard's junk check and STALE PRISTINE exit fail on the real tree (#129, judge_design round 2, operations)
Round-2 5.1 defines junk as every `*.orig`/`*.rej` under ROOT (node_modules and .git pruned) and arms
`trap restore EXIT INT TERM` in step 1. Dry-run in a scratch copy (Apple patch 2.0-12u11, bash): in the real worktree
the junk check prints four tracked files (`course/.../checks/data/{CLAUDE.md,Makefile,procedures,release.py}.orig`),
so setup step 1 stops on every round and the procedure can never start; with those files present, one M5 call's
`restore` deleted all four and printed `RESTORED OK`. And step 2's `STALE PRISTINE; exit` runs the armed trap, which
copied pristine over a hand-applied F (measured: F rewritten), the exact case 5.1.5 says must write nothing.
Rule: Before defining a cleanup by glob, run the glob on the real tree and subtract tracked files (or delete only
the exact names the tool creates); arm a restoring trap only after the last exit that must not restore.

### 2026-11-10: Leftover check filtered by the test-run label only, which the runtime's own objects never carry (#129, judge_design round 3, security)
Round-3 5.1.3 step 5 and 5.1.4 step 1 declare "leftovers none" from `docker ... ls --filter
label=academy.workspace.test-run=<id>`. The workspace container, its volume and `wks-t<id>-h-net` are created by
the src runtime with `workspaceLabels` (`academy.workspace.managed=true`, `academy.workspace.instance=t<id>-h`,
`src/identity.ts:94-108`) and no test-run label; the harness itself finds them by the managed+instance pair
(`harness.ts:141-156`). So a killed or broken mutation run that leaves the workspace container (the one M4 connects
to `otherNetwork`) prints "leftovers none" and `MUTATIONS CLOSED`. The run id is also taken from a log line that
global-setup prints only after setup succeeds (`global-setup.ts:46`, after `createSentinel` at :39), with no format
check, so a run that died in setup gives no id or an arbitrary string, and the check runs vacuously or interpolates
unvalidated text into a shell command.
Rule: A leftover check uses the same selectors as the code that removes the objects (run label OR managed+instance,
plus the network name), and a run id read from a log is matched against its generator's format (`^[0-9a-f]{8}$`,
exactly one per log) or the check stops instead of passing.

### 2026-11-10: The leftover check was carried into the clone rewrite without re-deriving its selector (#129, judge_design round 3, architecture)
Architecture confirms the security finding above independently. The round-3 rewrite of 5.1 replaced the whole restore
scheme but kept the step 5 leftover check from earlier rounds as it was. Nobody re-read who creates the objects the
I-network run leaves: helpers, peer and `otherNetwork` carry the run label, while the workspace container, volume and
instance network come from `src/identity.ts` `workspaceLabels`/`networkLabels`, which have none. The 5.1.3
killed-call branch ("re-run the baseline if a killed run still has objects") and 5.1.4 step 1 both take their
decision from that check, so they skip the very case they exist for.
Rule: When a procedure is rewritten, re-derive every check you keep from the code that creates and removes the objects
it watches (here `harness.ts` `listRunObjects`), and do not copy it over unchanged.

### 2026-11-10: 5.1.3 step 1 path guard is a string test, and the missing run id passes silently (#129, judge_design round 3, operations)
Dry run of the clone rewrite. 5.1.3 step 1 says `C` must "contain `services/workspace`"; the clone path string never
does (measured: `[[ $C == *services/workspace* ]]` false on `.../scratchpad/m129-clone-ZRrW04`, while
`$C/services/workspace` exists), so a literal run stops every mutation call; 5.1.4 step 2 already had the right form.
The run-id gap in the security entry above is measured, not only read: with a labelled container present,
`docker ps -a --filter label=<key>= -q` (empty value) prints nothing, so a log with no run line gives "leftovers none".
Rule: An existence guard is a path test (`-d <C>/services/workspace`), never "the string contains"; every value a
check is keyed on is shape-checked first (exactly one `[0-9a-f]{8}`) or the step stops.

### 2026-11-10: Prescribed a module header claiming "the only way" without grepping the other log lines (#121, judge_code, architecture)
Design 1.1 prescribed the log-fields.ts header "these four functions are the only way a field taken from [a thrown
value] reaches a log line". The coder wrote it faithfully (log-fields.ts:2-4). It is false in the same service: our
own classes' fields reach log lines directly at http/errors.ts:96 (`error.message`), reconcile.ts:109 (`error.file`,
`error.reason` of CourseReadError) and main.ts:30 (`error.message` of the config error). A reader auditing log
injection would trust the header and skip those three lines. The design's own section 2 even lists the
`${kind}: ${error.message}` branch as kept, so the claim contradicted the design it lives in.
Rule: Before prescribing an exclusivity comment ("the only way", "never", "every"), grep the codebase for the
counter-examples (here every `log.*(`/`console.*(` line that interpolates a property of a caught value) and scope the
sentence to what the grep proves.

### 2026-11-10: Operator view listed a starter refusal that cannot happen and missed the image build (#117)
Design 3 F8 said that after the fix a bad alias also gives "StarterRefusedError in starter.ts:112". That line wraps
only `lstatBelowRoot` of the lesson directory; no YAML is parsed on the starter path, so a YAML failure never
becomes `starter-invalid` (it is 500 `course-unreadable` through manager.ts:79 and mapError). The claim was copied
from the research without reading the call. The same table missed the one build-time consumer of `readCourse`,
`apps/web/scripts/export-course.ts` (Dockerfile:35): today an unresolved alias aborts the web image build with an
uncaught ReferenceError whose message prints the alias name, file text, into the build log.
Rule: The "what the operator sees" row is built from `git grep` of every caller of the changed function and of the
function above it (here `parseYamlFile` and `readCourse`), each call read, never from a caller list in the research.

### 2026-11-10: ADR text stated the alias limit as "100 aliases", dropping the research's "to one anchor" (#117, judge_design round 2, operations)
Design 6 dictated the ADR-0009 Consequences text "unknown anchor, or 100 aliases at the parser's default limit".
The research measured only one anchor with 100 aliases to it. yaml 2.9.1 checks `count * aliasCount > maxAliasCount`
per anchor (dist/nodes/Alias.js:61-67), so 120 aliases split over two scalar anchors (60 + 60) pass, and 30 aliases
(20 to an anchor that holds 10 aliases) fail. An author reading the ADR is misinformed in both directions.
Rule: When an ADR or reason text restates a measured limit, keep every condition the measurement had (here "to one
anchor"), or describe the mechanism, never the bare number.

### 2026-11-11: The merge follow-up told the tester to run ci.yml's commands verbatim, with no local rule for them (#106 merge of #149, judge_design round 1, operations)
Check 8 of the merge design says to run the `checks` job "as ci.yml runs them ... do not retype from older plans". At this
load (8 to 22 on 10 cores) a fresh plain `pnpm test` was red in 2 of 3 runs on the merged tree and in 2 of 2 web runs at
92cb2c0, always `lesson-markdown.test.tsx` with `Test timed out in 5000ms`. That is the pre-existing timeout #106 already
settled with rule R6-1 (`-- --testTimeout=60000`, any red is real), and the design dropped that rule. Check 10 has the same
problem: `check-append-only.sh` copied from ci.yml exits 1 at commit B, because it needs a PR merge commit and
`PR_HEAD_SHA`. Run at commit A it exits 0 against the wrong base.
Rule: When a design tells the tester to run CI's commands locally, run each one on the host at base first. Carry over any
local rule the task already has (timeouts, a simulated merge commit), or say why it no longer applies.

### 2026-11-16: Mutation row named a non-unique anchor and gates were left as placeholders (#107, judge_design round 1, operations)
T4 M1 said "add after `frameworkErrors,`" with a must-match-once replacement; the string also occurs in app.ts:8's import,
so the row stops on its first run. Gate 4.1 c) gave the age check as `<parse ...>` and 4.1 b) compared 13 lines by eye
with no red control.
Rule: every mutation row and gate in a design is a literal, runnable string that was run once at base (anchor match count
printed); every gate names its red control.

### 2026-11-16: A flaky-fix stability check with no base control and an unguarded load loop (#93)
Design 5 check 3 passes on "0/20 foreground failures" and "background counts >= 1". Each background iteration creates
its log before the run starts, so the count is >= 1 even when the suite never starts. On an idle host (load 2, old test
1084 ms) the old single test would also pass 20/20, so the check cannot tell the fix from no fix. In the judge's dry run
the same harness gave the old test 16/20 timeouts at load 28-44 and the new file 0/20 at load 7-36. Only that pair is
evidence. The loop also has no trap: after SIGTERM to the parent `bash -c`, the background loops kept running
(verified). The run takes 180-209 s, longer than the 120 s default Bash timeout, and `rm "$L/run"` is denied by
Claude Code's rm safety check. The plan also had no cleanup step for an 861 MB clone, and the mutations were prose on
a host with BSD sed.
Rule: A stability check for a flaky fix runs the old code under the same load, interleaved, and requires it to go red.
Every background load loop has an EXIT/INT/TERM trap, guarded `${L:?}` paths and a stated Bash timeout. Every
throwaway clone has a scripted cleanup step and every mutation an exact command.

### 2026-11-16: Derived web's deadline margin from a setup bound that skips half the pre-start path (#163, judge_design round 1, architecture)
Design 3.3/3.7 bounds setup "60 s from exec start to marker", then tells #165 that "before `started` web needs only its
inactivity limit" and that the R34-15 margin floor is 90 s per check. Between the request and the exec start, the runner
waits for the workspace lock, which an ensure can hold for up to 30 engine calls. It then makes five Docker calls, and each
is bounded only by a 30 s inactivity timeout (ADR-0010 item 8). Keepalives keep flowing the whole time, so web never aborts,
and nothing in the service ends that phase. The deciding phase after the stream ends ("8 polls of 250 ms") is also polls, not
wall-clock time, and each poll is a Docker call with the same 30 s cut. So the service can reach web's 30 s backstop, or
the run deadline, while it is alive and healthy. A grader that passed then lands as a counted `no-result`. The same design
also lists "framing error -> no-result" as a contract row, but its `CheckProcess.ended: Promise<void>` carries no reason,
so PR B cannot implement that row. And it amended ADR-0007 rule 3 and R34-4 for the service-held timer without changing
the two rule 3 sentences that still say "the runner's timer".
Rule: For every number a contract gives the other team (margin, backstop, "only X needed"), list every phase from request
to final line, and give each one a wall-clock bound that the service itself enforces. Check that the port interface has a
field for each row of the end table it promises. Grep the amended ADR for each old term ("runner's timer", "exec start")
and replace every hit.

### 2026-11-16: "Nothing outlives a check" written without trying the cleanup when the container cannot start an exec (#163)
Design revision 2 dictates ADR-0002 item 12 "Nothing outlives a check" and 6.3 "a slot is released only after its cleanup
finished (or failed), so a new check never reuses a uid whose processes may still run". The cleanup is itself an exec. A
grader (or learner code it starts) that fills the container's pids limit makes that exec fail to start (`docker exec`
exit 128, "unable to start container process ... Resource temporarily unavailable", judge_design ops N2 on both images), so
the uid's processes and its `/tmp` checks dir live until the container stops, the terminal cannot open either, and the
outcome is a bare `failed` next to a learner-planted name (exit 5, which the learner can force on every run and which wins
over exit 4). Residuals and the failure table missed it. The same design's mutation clone recipe (section 21) was never run:
`git apply` stops on an empty diff, and without a build of `@academy/lesson-schema` (exports only `dist/`) every test that
imports `identity.ts` or `lessons.ts` fails at import, so every mutation row's `TEST rc=1` is vacuous.
Rule: For every "after every end X happens" claim whose X is a Docker call, run it once with the container's pids limit
exhausted and once with the learner's own interference, and write the observed outcome into the contract. Run every
prescribed clone or setup command at base and check that one known-green test is green in it before prescribing it.

### 2026-11-16: Listed /tmp as a learner-controlled input but checked only fixed names, not ancestor lookups (#163, judge_design round 2, security)
Revision 3's 4.4 table lists every grader input from learner-controlled places, and its `/tmp` row says "no tool we know
loads code from a fixed `/tmp` name"; ADR-0002 item 12 tells grader authors only "graders use random names", and audit
19.2 (f) asks only about fixed names a grader itself uses. The design puts the checks dir directly in `/tmp`, so `/tmp`
is an ancestor of every grader file. Tools that resolve code or config by walking up from a file or cwd then reach a
fixed name in a learner-writable directory: Node's `node_modules` lookup (a bare import from a checks file tries
`/tmp/node_modules/<pkg>`), Node's package scope (`/tmp/package.json`), npm's project root and `.npmrc`, pytest's
rootdir and `conftest.py`. A random directory name does not help, because the walk goes through the parent. Git is
safe here only through its ownership check, and module 04's go calls only through `GOWORK=off`.
Rule: For every learner-writable directory in the input table, also ask "is it an ancestor of a grader file or cwd?"
and list each tool that walks up from a file or cwd, with a planted red control.

### 2026-11-16: ADR text dictated verbatim kept claims that the design's own tables and P5 contradict (#163, judge_design round 2, architecture)
Revision 3 rewrote the phase table (3.3) and the port (11.1) but did not re-read the ADR sentences dictated from the
older text. 3.8 and the ADR-0010 item 8 amendment say a check holds the lock "only from its container inspect to its exec
start", while 11.1's `startCheck` (called under the lock, 7) first runs `loadChecks` and `buildChecksTar`. ADR-0002 item 12
says "every other phase of a check has a wall-clock bound the service enforces", while 3.3 rows 1 and 7 have none. Item 12,
3.5, R6 and F27 say the failed cleanup is logged "with the exit code Docker reported", while P5 (run 3, both images) showed
the start refused with HTTP 500 and no exit code. S163-4 says the service ended every started check "by `timeoutSec`",
while 3.3 row 4 allows `timeoutSec + 5 s`. And 3.2 sends `service-stop` before `started`, which ADR-0007 rule 3's first
bullet ("before the grader started, every failure is ... `pre-start: <stage>`") contradicts, and no S163 item replaces it.
Rule: After changing a table, a port or a procedure result, grep every sentence the design dictates into an ADR for each
claim of span, "every", "only" and "with X", and check each one against the table row, the port and the measured output.

### 2026-11-16: Moved the slot-reuse guarantee onto the prelude kill and gave that line no test (#163, judge_design round 2, operations)
Revision 3 corrected 6.3 as round 1 asked: reuse of a slot after a crash (R3) or a cleanup that never started (R6) is safe
"because the next check's prelude kills every process of the uid" (decision 18). The prelude's `kill -9 -1 2>/dev/null` then
became load-bearing, but no I-c test and no M row exercises it: I-c7b and M13 cover only the prelude's `rm`, and P5's
`reuse` runs after a container restart that had already killed everything. The ops probe pk.sh (a leaker left by an
uncleaned check, then a second check in the same slot) gave `uid2000=0 terminal-saw-B=0` with the line and
`uid2000=2 terminal-saw-B=1` without it, on both images: the next check's `checks/` reaches the terminal. Only the
U-exec-check literal would go red, and a literal that restates the code is edited along with it.
Rule: When a revision makes a line the reason a guarantee holds, add in the same revision a behavioural test that starts
from the state the line exists for, and a mutation row that deletes the line, with its anchor counted in both script forms.

### 2026-11-17: Fixed a flagged ADR claim by scoping it, then re-added the counterexample in a new clause (#163, judge_design round 3, architecture)
Round 2 said ADR-0002 item 12's "every other phase has a wall-clock bound the service enforces" was false for 3.3 rows 1
and 7 (row 7: the cleanup's exec create and start are bounded only by docker-modem's inactivity). Revision 4 scoped the
sentence to "from the start of the response to the last line" and then appended "and so has the cleanup after it (30 s)",
which states the row 7 claim again: the 30 s cap covers only the polls after the start answered, and `terminate` (so the
slot release) waits for the create and start. The sweep row 2-12p marked it fixed against rows 7-8. The same pass left two
other ADR sentences false under item 12: ADR-0002 item 10's residual "Every process in that workspace runs as the same
uid and can read it" (9.1 checked the neighbouring sentence at :215-216 only), and S163-11's "The one exception before the
start", while rule 3's fourth bullet (run-deadline) and R34-14 (web-restart for every rowless check) are exceptions too.
Rule: When fixing a flagged sentence, re-check every clause added in the fix against the same counterexample row; and when
a decision changes who runs in the container, grep every ADR for sentences about "every process", "the same uid" and "the
one exception" before the sweep is called full.

### 2026-11-17: Gave the grader more read access than the learner but never asked where the learner's names point (#163, judge_design round 3, security)
Rule G (4.4, ADR-0002 item 12) lists every place a grader's tools take code or config from, and the 4.4 row "Learner files the
grader reads as data" says they matter only if executed (R1). Since the grader runs as uid 2000+slot it can read `$s`, which
uid 1000 cannot, and revision 4 made the target path fixed and published (`/workspace/.academy-grader/<uid>/checks`). uid 1000
can still name any path: `work` itself can be replaced by a symlink (`/workspace/home` is the learner's), and every file in
the tree can be one. The setup's `cd /workspace/home/work` runs after the checks are extracted, so a `work` symlink to
`$s/checks/reference` makes the reference the graded tree (`verify_ci.py:58` takes `Path.cwd().resolve()`); a
`routing.json` symlink into `checks/data` makes `verify_routing.py:60-65` print the key file's top-level keys under an
uncounted exit 3. A wrong slot guess is a free `exit 123`. The same pass called a check "no destination" for key copies in
ADR-0002 item 14, though its stdout is stored in `message` (ADR-0007 :270) and shown to the learner.
Rule: When a design gives one principal read access another lacks, list every path the weaker principal can name to the
stronger one (symlinks, cwd, arguments, config values) and say per path why it cannot point into the stronger one's private
places, with a planted red control. For every secret, list each channel that persists or displays a reader's output.

### 2026-11-17: Counted the array-form mutation anchors in quotes the repo's formatter never writes (#163, judge_design round 3, operations)
Design 13.3 lets the coder write both scripts as a template literal or as an array of lines and dictates array-form anchors
for M3 (`'  kill -9 -1 2>/dev/null',\n`) and M23 (`'kill -9 -1 2>/dev/null',`), copied from the round-2 ops note. The repo's
biome config has `quoteStyle: "double"` and CI runs `biome check .`, so a line with no quote inside it is written
`"kill -9 -1 2>/dev/null",`. Both scripts generated from 5.2/5.3, formatted by biome in a clone and appended to today's
spec.ts: M3 and M23 array anchors count 0 (double-quoted forms count 1); every other anchor counts 1 in both forms. The
tester would have stopped the mutation pass at `count=0`. 5 intro's "both hold them unchanged" is also false for the printf
line's `\n` (biome writes `"printf 'academy-check-started\\n'"`).
Rule: Count every dictated anchor against source text produced by the repo's own formatter (write the form, run the
formatter, then count), never against a hand-written form; if two forms are allowed, dictate one or give both anchors as
measured.

### 2026-11-17: Analysed cmdline readability for the key but kept "the grader's cmdline shows only the checks path" (#163, judge_design round 4, security)
Revision 4e added R8 and P11 because `/proc/<pid>/cmdline` is readable across uids, but applied that fact only to uid-1000
holders of the agent key. The other direction stayed as R2 and ADR-0002 item 12 residual (2) ("shows the checks path ...
published anyway"), and the new ADR-0001 Decision 5 note says `checks/` content reaches the browser only "as residuals (1) and
(7) state". uid 1000 reads the arguments of every process of the check's uid, and graders put grader material there:
`verify_pokayoke.py:363-371` passes `checks/data/late_fee_grid.json` points and the `statement_grid.json` invoices as argv to its
probe child (20 s), `verify_workspace.py:389` passes `behaviour.json` `inputs`, `verify_deps.py:198-200` the hidden dicts. A
terminal loop over `/proc/*/cmdline` shows them in the browser with no learner code involved. Item 12 gives graders no rule on
arguments, and audit 19.2 has no item, so a grader that passes an expected answer to its own helper would leak it silently.
Rule: When a design states that a channel is readable across uids, apply it in both directions and to every process of each
uid, and check each "except as residuals ..." note against that channel before calling the exception list complete.

### 2026-11-17: Added a clause to a prescribed one-line fix and checked it against one way of ending only (#163, judge_design round 5, architecture)
Round 4 architecture note 1 asked for one line on ADR-0010 Consequences :149: "a restart also loses every running check (item
14)". Revision 4f added "and its grader runs on as ADR-0002 item 12, residual 3, says". Residual 3 is the crash case. A graceful
restart (compose restart, SIGTERM) is the 3.5 row "service SIGTERM (compose stop, restart)", sweep row 10-14g1 and 6.2: every live
check gets `service-stop` and its cleanup exec is created and started, so the grader is killed. Sweep row 10-C searched only
web's crash backstops. The same pass wrote an exception list from 4.4's new channel table and dropped one of its rows: item 12's
new bullet and R2 name abstract `AF_UNIX` names as reachable by uid 1000, and the bullet's exception lets a grader serve
learner-code material there, but residual (2), the ADR-0001 Decision 5 note and S163-12 name only "an argument or ... a
loopback port". Sweep row 0001:22 says it walked every row of that table and found "no other".
Rule: When a fix adds a clause, check that clause against every way the thing ends: graceful stop, crash, caller close. When
an exception list is derived from a table, tick each table row "reachable" against the list and name the row in the sweep.

### 2026-11-17: Dropped a check in one section and left it as a step and a guard in two others (#163, judge_design round 5, operations)
Round 4 operations note 1 showed 13.2's hook-time check could never fire. Revision 4f dropped it in 13.2, section 2, decision 27
and 19.3, and 13.2 now says "Revision 4c's hook-time check is therefore dropped: it could not fire". Section 11's step A8 still
ends "the tester reports the new file's hook time (13.2)", and section 14's F44 still names "the tester measures the hook time
(13.2)" as its mitigation and "A8's measured hook time" as its test. A tester following A8 has no defined measurement, and F44
claims a guard that the same design calls unfireable. The 4f change list touched only the sections the judge named; nobody
grepped the design for the other places the check was referenced.
Rule: When a revision drops or renames a check, grep the whole design for its name and every phrase that cites it (steps,
failure modes, decisions, issue texts) and change each hit in the same pass; list the hits in the change note.

### 2026-11-17: Listed argv members by one grep form and gave the audit a red control one named member cannot trip (#163, judge_design round 5, security)
Revision 4f listed today's "grader material in arguments" with a Grep for `json.dumps(...)]` ("finds exactly these three") and
gave audit 19.2 (l) one argv red control: a marker in the audit's copy of `checks/data`, then "Today the count is above 0 for
the three graders above". `verify_deps.py:198` makes its hidden dicts from `random.Random(seed ^ 0x5EED)` in code, and no
`checks/data` value goes into its argv, so that control reads 0 for verify_deps before any fix. The same grep missed that every
module 02 `run_child` (`grader_runtime.py:245`, three copies, used by the probe and by `run_suite`) puts checks/ source
(`PROBE`, `SUITE_BOOTSTRAP`) and the record nonce into argv, and module 03's `run_reporting_child` (`orchestra_runtime.py:205`)
puts its nonce there. Each of those is a learner-code process, so it falls under residual (1). But the 4.4 row, section 2 and the
audit's member list are incomplete, and the control cannot see material that comes from grader code or from a generator.
Rule: Find the members of a channel class by its mechanism (every process-start call and the argv it builds), not by the form
of one argument. Every red control the design calls "present today" gets traced to the source of that member's material
before the sentence is written.

### 2026-11-17: Narrowed one ADR sentence with a correct condition and left its siblings stating the broader universal (#163, judge_design round 6, architecture)
Revision 4g wrote the ADR-0010 Consequences bullet as "a graceful one with `service-stop` and, when the check's exec had
started, its cleanup", because 6.2 `stopAll` also reaches checks still preparing, and ADR-0002 item 12 "Cleanup" starts a
cleanup only for an exec Docker started. The same amendment's item 14 text still says the broader thing: 3.5's SIGTERM row
"every live check: `end service-stop`, response ended, cleanup exec created and started", the idle stop and web-disconnect
rows "then the cleanup" and "the cleanup", 3.3 row 9 "in any phase ... then row 7", row 7 "the cleanup after any end", 3.6
"start the cleanup"; and ADR-0007 S163-9 says SIGTERM "starts the cleanup of each" running check, which S163-11 says may be
before `started`. Sweep row 10-C lists the 3.5 SIGTERM row, 10-14g1 and S163-9 as "checked against", and its own text says
both "stopAll ... calls terminate, which creates and starts the cleanup exec" for every live check and "a check whose exec
Docker had not started has no cleanup". 10-14g1 stays "consistent". The ADR text then contradicts itself inside one amendment.
Rule: When a fix adds a condition to one sentence because a premise is narrower than it said, grep every sentence in the same
ADR texts that states the same premise (here: "cleanup" after an end or a stop), give each the same condition or a pointer, and
re-verdict their sweep rows in the same pass.

### 2026-11-17: The audit issue's helper cleanup was written, not run, and dropped the no-load rule (#163, judge_design round 6, operations)
Revision 4g moved the audit controls into #187 with the preamble "runs under `timeout <seconds>` inside a shell with
`trap 'kill 0' EXIT` ... after each control, `pgrep -u 1000 -f audit-` prints nothing". Measured in a `t163-` container of
`academy-workspace:dev` (dash) as uid 1000: `timeout --foreground 2 sh -c "trap 'kill 0' EXIT; sleep 300 & ..."` leaves the
`sleep 300` (count 1); `EXIT INT TERM` leaves 0. Plain GNU `timeout` hides it by signalling its own group; busybox `timeout`
(node alpine) leaves 1 with `EXIT` alone. The emptiness check, run the usual way (`docker exec ... sh -c 'pgrep -u 1000 -f
audit-'`), counts its own `sh` (1), and on the macOS host it can never be non-empty. The issue also carries no part of the
machine's no-synthetic-load rule (at most 4 helpers at once, no fills), while it tells the auditor to tighten 50 ms polls to
10 ms; the #163 constraints file that holds the rule does not travel with the issue.
Rule: A cleanup or "nothing left" guard that a text dictates is run once before sending, with a child it must end and in the
shells the target images use (dash, busybox), and its emptiness check is shown non-empty while a helper runs; a moved
procedure carries the host-load limits it needs in its own text.

### 2026-11-17: An audit control attributed sockets as a root with no capabilities, and dropped what it could not attribute (#163, judge_design round 7, security)
The revised #187 control 4 (plans/163-audit-issue-body-v2.md:290-293) tells the auditor to match each new abstract
`AF_UNIX` name's inode, "as root through `docker exec -u 0`", against the `socket:[<inode>]` links in `/proc/<pid>/fd` of
slot-uid processes, and says "Only names whose owner is the slot uid count". The workspace container has `CapDrop ALL`
(spec.ts:94), and a `docker exec` without `--privileged` gets the container's capabilities, so that root has none. Reading
another uid's `/proc/<pid>/fd` is gated like `environ` (proc(5): a PTRACE_MODE_READ_FSCREDS check; the directory is 0500 of
the process's uid): uid 0 against uid 2000 with no CAP_SYS_PTRACE is refused, which is the same mechanism the design itself
cites for the environ denial (ADR-0002 item 14 text, run 4b P9). So no name gets an owner, and the stated rule then counts
none: the only dynamic check of the abstract-name channel passes every grader, and it has no known red member to expose that.
Rule: A control step that needs privilege is checked against the container's real capability set (CapDrop, no-new-privileges)
before it is dictated, and an attribution step fails closed: whatever it cannot attribute counts as a hit, never as clean.

### 2026-11-17: Classed a sentence as a pointer because it named the source, while its other clause restated the leftovers' fate (#163, judge_design round 7, architecture)
Revision 4h made ADR-0002 item 12 "Cleanup" the one text on what outlives a check, including where leftovers go ("leftover
files stay in the scratch ... until the slot's next check empties it or the workspace is deleted"). Design 4.1 (:453-455)
was rewritten in the same revision as "its files removed by the cleanup of ADR-0002 item 12 "Cleanup", with whatever that
leaves removed by the slot's next start, whose prelude empties `$s`", and `cleanup-hits.md` classed it POINTER ("the prelude
is not the cleanup"). The second clause is a statement of what happens to what the cleanup leaves, and it is false for
residual 4 of the same bullet: an entry learner code made undeletable survives the cleanup (exit 5, P1u) and the next start's
prelude cannot remove it either (exit 119), so it stays until `DELETE W`. Siblings say the same narrower thing: R3 (:538-539)
and 5.3 "When the cleanup cannot run" (:916-917) "empties `$s`", F27 (:1898) "kills the leftovers and empties `$s` once it
can"; only 6.3's "Why a slot may be reused" adds "and refuses to start when it cannot empty it".
Rule: A hit is a POINTER only if every clause of the sentence is the pointer; a clause that names the source and then says
what happens to the leftovers anyway is a restatement, and each such clause is tried against every residual of the source.

### 2026-11-17: Gave the #187 helpers an exact command form whose output every specified ending discards (#163, judge_design round 8, operations)
The #187 v3 body fixes each helper as "one `python3 -I .../audit-*.py` process run under `timeout <seconds>`" and says
`audit-fdmap` "prints `inode pid` pairs on its stdout, which the host keeps, and it ends with the check's cleanup ... or by
its own timeout". Every ending the text gives a helper is a signal (the cleanup's SIGKILL, `timeout`'s SIGTERM, the trap's
`kill 0`), and Python block-buffers stdout on a pipe and does not flush on either signal. Measured in academy-workspace:dev:
`audit-fdmap` as written delivered 0 lines to the host after the cleanup, the same loop with a flush 2 (`<inode> 171`,
`denied 172`); a uid-1000 helper in the trap shell ended by `timeout 2` delivered nothing, with `-u` its line. The red run 1
("held by the slot uid") then shows every name unattributed, and the poll of controls 1 to 3 shows 0, which the text tells the
auditor to answer with a tighter poll. The same text counts "control 4 has two" helpers and concludes "a run with controls 1
to 5 stays at 4", while it also says each slot uid with a process needs its own `audit-fdmap`: with two checks the run is 5.
Rule: When a text fixes a helper's command line, run that exact line through each ending the text gives it and check what the
host received; and recount a load budget for every configuration the same text allows, not only the default one.

### 2026-11-17: Hid a probe behind one exit code while the two paths fork a different number of processes (#163, judge_design round 9, security)
Design 5.2 gives every work-dir refusal exit 123 "on purpose", so that `work -> $s/checks/<name>` does not tell the learner
whether `<name>` exists (section 1: "the refusal probes nothing"; 4.5: "the outcome tells the learner nothing about what exists
in `$s`"). The line is `cd -P ... && [ "$(pwd -P)" = ... ] || exit 123`: the command substitution forks a uid-N subshell only
when `cd -P` succeeded, and 5.3 of the same design says such subshells are uid-N processes with their own pid. uid 1000 can
see them (process listings and Uid lines are readable across uids, section 2) and can count pids allocated in the container's
pid namespace around each attempt, deterministically, with unlimited uncounted retries. So the exit code is one, but the
process count still answers "does this directory exist in the checks copy".
Rule: When a design merges outcomes into one code to close a probe, list every observable that differs between the merged
paths (forks, pids, process names, timing, files touched), not only the exit code, and remove or name each one.

### 2026-11-17: Shutdown ends the checks the runner knows, and a request already in its course read starts one after (#163, judge_design round 9, architecture)
Design 6.2 runs `checks.stopAll()` and then `app.close()`, and says "every check response is ended before `app.close()`, so
Fastify's `forceCloseConnections: "idle"` has no open stream to wait for". The route reads the course before it calls
`runner.run` (3.1, phase 1), and 6.3 has no row for `run` after `stopAll`. A request whose course read is awaiting at SIGTERM
resumes after `stopAll`, and Fastify 5.12.7's close only routes new requests to 503 (`router.closeRoutes()`); a handler in
flight goes on. So that check takes a slot, starts and sends `started`; its open stream holds `app.close()` until compose's
SIGKILL, and web sees the stream end after `started`: a counted `no-result` caused by a graceful restart. That breaks the
ADR texts the same design dictates (ADR-0010 Consequences "a graceful one with `service-stop`", S163-9 "it ends every
running check with `service-stop`", the 3.5 SIGTERM row).
Rule: For every "stop all X, then close" shutdown, walk the X that arrive after the stop: an in-flight request that has not
reached the component yet. Give the component a closed state that refuses or ends them, and test it.

### 2026-11-17: Removed the one observable the judge measured and left the path walk that touches learner files (#163, judge_design round 10, security)
Revision 4j answered the round 9 pid probe by swapping `"$(pwd -P)"` for `"$PWD"` and measured pids only. The round 9 rule
listed "files touched" among the observables. The setup still resolves the learner's `work` link as the slot uid after the tar
has filled `$s/checks`. A link target `/workspace/.academy-grader/<uid>/checks/<name>/../../../../home/L` reaches the
learner's own symlink `L` only when `<name>` is a directory in the checks copy, and following a symlink updates its atime
(Linux `pick_link` -> `touch_atime`, under the default `relatime`). uid 1000 reads that atime with `lstat`, so each uncounted
exit 123 still answers "does this directory exist in the checks copy", with either form of the line.
Rule: To close a probe through a learner-named path, order the script so the path is resolved before any grader material
exists where the slot uid can reach it, instead of removing the observables one by one.

### 2026-11-17: Replaced "terminate" with a list of in-flight cases and left out the awaits of the runner's own rows (#163, judge_design round 10, architecture)
Revision 4j split the 6.3 row "preparing or running | `onStopping` / `stopAll` | terminate" into a preparing row that lists
the in-flight cases (checks read, lock task, `startCheck` in flight, "a running setup"), and 6.4 claimed every member of the
class "awaits, then acts after a stop began". Two states of the runner's own table await Docker calls while holding a live
`CheckProcess` and terminate only after those calls answer: "setup resolves not-started" (one `exitStatus()`, then
`isContainerRunning`, then "send the end ...; terminate") and "deciding" (its `stopAll` row says only "`service-stop` wins").
A stop in either window sends the end, and when the await resumes the row "ended | anything | ignored" drops its terminate.
After `stopAll` the container keeps running, so a setup that ended `socket-error`, `framing` or `stdin-failed` (whose shell
may go on to exec the grader) or a grader that closed its stdout and runs on is never cleaned, against ADR-0002 item 12
"Cleanup" ("a not-started after that answer, a service stop"). 6.4 marked "deciding" as "none". The same pass fixed the poll
timer of `terminate({ wait: true })` as "the poll's timer is unref'd" without naming its 30 s cap, which a fake-timer-friendly
implementation writes as a second `setTimeout`.
Rule: When a stop row lists the cases in flight, derive the list from every row of the same table whose action follows an
await (a pending call holds the process too), or state it as one rule over the object ("any `CheckProcess` without a
terminate gets one"); and name every timer of a component a shutdown must not wait for, not one of them.

### 2026-11-17: Justified "no test" for the unref'd cleanup poll with a claim nobody ran, and named a test after a case it contradicts (#163, judge_design round 10, operations)
Revision 4j fixes F45 with "the poll's timer is unref'd" and says no test pins it because "no unit test here observes" when a
process under SIGTERM can exit. Vitest 5.0.5's fake timers return handles whose `hasRef()` tracks `unref()`: a spy on
`setTimeout` during `terminate({ wait: true })` with an exec that stays `Running` asserts every handle has `hasRef() === false`,
and the same test goes red when the call is removed (run in the scratchpad, 1 passed / 1 failed). Measured with dockerode 5.0.1
against a fake daemon that always answers `Running: true`: an unref'd poll lets the process exit 14 ms after the loop drains, a
referenced poll holds it 30,123 ms, and an unref'd poll beside a referenced 30 s cap timer holds it 30,001 ms. So the fix holds
only for one implementation shape, and nothing would catch the other. The same revision names the PR B test "stopAll while
preparing starts no exec" (12, 19.1 Done list and body), while its third case, a `startCheck` in flight, lets the check exec
start and then starts a cleanup exec through `terminate({ wait: false })`.
Rule: Before writing "no test can observe X", try the cheapest observer (a fake-timer handle, a spy, a child process) and
record what was run; and a test name dictated by a design must be true of every case listed under it.

### 2026-11-17: Stated rule T over every await and end, then listed the test pairs by hand and left out pairs F46 itself names (#163, judge_design round 11, architecture)
Revision 4k's rule T (6.3) is universal, but its acceptance test (12, 19.1 "one parametrised test over every pair of await
state and end that can meet") was a hand-written list. It leaves out the caller's close in the setup not-started window
(awaiting `exitStatus()` and `isContainerRunning()`), although F46 names exactly that end and the 6.3 close row still reads
"internal `aborted` (logged only)", so a build that keeps that row passes every listed case and never terminates a setup that
ended `stdin-failed`. It also leaves out deciding while awaiting `isContainerRunning()` (named in 6.4 and F46), `ended`
`socket-error`, the terminating state against `stopAll` / `onStopping` / close (no second terminate), the natural ends
(setup not-started after both answers, decided exit, `no-result`, `container-ended`), and point 4 for the checks read and the
lock wait against the caller's close and `onStopping` (only `stopAll` and the start timer are tested there). And 6.2 still
says `stopAll` gives "every `CheckProcess` it holds" a `{ wait: false }` terminate, while rule T says the runner holds one
until its terminate resolves and point 3 says a call under way is left as it is: followed literally, 6.2 makes two calls.
Rule: When a rule is stated over a product (await states x ends), write the product as a matrix in the design, mark each cell
"can meet" with the code line that proves it or "cannot" with the reason, derive the test cases from the cells, and grep every
sibling section for a sentence that restates the rule with a wider or narrower quantifier.

### 2026-11-17: Copied a Done line that promises "every CleanupKind mapping" without checking the test table, after the split moved the only wait-false test out (#163, judge_design round 12, architecture)
Revision 4l copies the posted #163 Done line into section 0 ("U-runtime-check (including ... every `CleanupKind` mapping, ...)")
and says 13.1 to 13.4 need no change. The 13.1 U-runtime-check row has cases for clean, processes-left, files-left,
processes-and-files-left, no-proc, not-started (128 and start 500), killed, unexpected-exit, container-stopped (create 409,
inspect 404) and timed-out, but none for `docker-error` (5.3 rows 994-995) or `cleanup-started` (5.3 row 996, `terminate({ wait:
false })`). Before the split, `wait: false` was exercised only through PR B's `stopAll` integration test, which moved to #196, so
PR A now ships the shutdown form of `terminate` with no test at all, while the 4l 9.1 evidence insert cites that same form as
PR A's evidence for ADR-0002 item 12 "Cleanup"'s shutdown sentence.
Rule: When a scope split moves tests out, list every code path the remaining PR still builds and name the test left for each;
and when copying a Done line that says "every X", count X's members in the type or table and check each has a named case.

### 2026-11-17: Moved a security obligation to an issue body "that already lists it" without reading that body (#163, judge_design round 13, security)
Revision 4m's Q5 planner note (design :2496) says that with the A1/A2 split "the obligations from #34, the round 11 acceptance
items and the ADR texts move to the A2 issue, whose body (19.3) already lists them", and that A1 then closes #163 on a Done line
narrowed to A1. The 19.3 body (:2533-2560) lists the ADR texts and the A2 tests, but no obligation: not ADR-0007 item 5 (the
`checks/` confidentiality obligation that [E3] rewrites in the same revision, with its I-c2/I-c4/I-c7/I-c7b/I-c8 mapping and its
"completed only with #187 item k" link), not R34-4, not the content-contract and ADR-0010 obligations, and not the round 11
acceptance items. Grep "bligation" in the design: three hits, none in 19.3. Followed as written, the split closes #163 and files
A2 with no issue owning the security obligation the coverage pass just narrowed. coverage.md's Q3 row did not catch it,
because it checked 19.3's Done items and never the claim that 19.3 carries the obligations.
Rule: A sentence that moves an item to another text ("already lists them") is a claim to check with Grep against that text, item
by item, in the same revision; a security obligation that changes issue goes into the receiving body verbatim.

### 2026-11-17: Coverage cases dictated a fault the transport cannot produce, and absences observed with no barrier (#163, judge_design round 13, architecture)
Revision 4m's coverage pass gave every member a named test, but did not check that each dictated construction produces its
member. RC14's `socket-error` input is "the fake daemon first reads the checks tar up to the client's half-close ... or it
destroys the connection". The fake daemon listens on a Unix socket (`exec.test.ts:104-166`); a peer that closes an AF_UNIX
stream socket with an empty receive queue gives the other end a clean EOF, not an error (Linux sets `ECONNRESET` on the peer
only when unread data is queued), so the hijacked attach stream emits `end`, a correct `CheckProcess` reports
`ended-before-marker`, and the case is red against correct code. RC1 ("no exec inspect"), RC5 ("no further inspect") and RC9
("249 ms leaves no inspect recorded") assert that a timer-fired HTTP request has not reached the fake daemon right after
`advanceTimersByTimeAsync`, which yields only one native `setTimeout(0)` per fired timer: a request that a mutated poll did send
may still be in flight, so a shorter poll period or a wait-false form that polls can stay green. coverage.md marked all three
"Now: RCn" without a negative run.
Rule: For every dictated test input, name the mechanism that produces the member on the real transport of the test (Unix
socket, TCP, fake timers) and check it in the library or kernel source; assert an absence only through a synchronous
observable (a spy on the timer call and its delay) or after an explicit barrier, and say which mutation makes the case red.

### 2026-11-17: Fake-clock tests dictated without a negative run against the mutants they claim to catch (#163, judge_design round 13, operations)
Operations measured the round 13 class above in a scratch clone with the repo's `DockerEngine` and a Unix-socket fake daemon
(vitest 5.0.5, default fake timers). RC1 as written stayed green 20/20 on a wait-false form that polls and 20/20 on one that
resolves once the create answered, because the "not settled after 1 s" check runs before the create's answer has crossed the
socket. RC9 as written stayed green 10/10 on a 100 ms period and on a first poll at 0 ms. With a real-I/O barrier (await the
daemon's record of the held start before the 1 s check; a real 50-100 ms wait after each fake advance before an absence is
read) each mutant went red 20/20 or 10/10 and the faithful form stayed green. RC14's destroy after the half-close gave
`end,close` and no `error` on macOS (Node 22.23.1) and in node:22.23.4-alpine; `resetAndDestroy()` throws
`ERR_INVALID_HANDLE_TYPE` on a Unix socket. The design said "Red when ..." for RC1 without having run it.
Rule: A dictated test that says "red when X" is run once against X before the design ships it, in the test's own transport and
timer mode, and the design states the barrier that makes each absence or not-settled assertion observable.

### 2026-11-17: Recorded a label-mismatch member as covered by tests that never run that code, and left the mismatch input unpinned (#163, judge_design round 14, security)
Revision 4n's RC11 (13.1) and coverage.md T13 say the volume label path of `startCheck` (`runtime.ts:196-197`, `#checkedObjects`)
is "covered by `adopt.test.ts:121`, `objects.int.test.ts:83-170`". Those tests call `createOrAdoptContainer`, `ensureNetwork`
and `ensureVolume` in `objects.ts`; none of them calls `#checkedObjects`, and none calls `startCheck`. The only test of
`runtime.ts:196-197` is `runtime-stop.int.test.ts:164-182` (ensureRunning, stop, remove), still not `startCheck`. The citation came
from the round 13 security note and was copied without opening the files. RC11's requirement also says only "a container whose
labels do not match": an input with no labels or another instance is refused by a weaker check (`isOwnManaged`, a valid-label
parse), so the case stays green on a `startCheck` that would exec in another user's container of this instance, the corner the
check exists for (`labelsMatchKey` compares userId, courseId, lessonId).
Rule: Before writing "covered by <test>", open the test and confirm it calls the function under test on the path named; a
mismatch case uses the input where the right check and the nearest weaker one diverge (another key of the same instance).

### 2026-11-17: Left a known contradiction between 11.1 and 5.3 to the planner instead of deciding it (#163, judge_design round 14, operations)
Revision 4n's note found that 11.1 maps "any other `DockerApiError`" at the cleanup start to `not-started` and sets `httpStatus`
to its `statusCode`, while 5.3 maps "any other Docker error (no status: socket, timeout, bad response)" to `docker-error` with
none / none, and that `classifyDockerError` builds `DockerApiError` with `statusCode` 0 for an error with no status
(`classify.ts:21-26`). It then left the choice to the planner. Measured: a fake daemon that answers the detached start with bytes
that are not HTTP makes `startDetachedExec` reject with `DockerApiError(0)`, and the stub that follows 11.1 literally resolves
`{ kind: "not-started", exitCode: null, httpStatus: 0 }`; the same rule gives `docker-error` with `httpStatus` 0 at the create and
the inspect. The result and #196's log line then say Docker refused the cleanup with HTTP 0, when the cleanup's state is unknown,
and no case pins either reading.
Rule: A contradiction between two sections that the design itself finds is decided in the design, with a case that pins it;
`statusCode` 0 is "no status" wherever a result or a log carries an HTTP status.

### 2026-11-16: Load control with a pass rule that no-fix passes 25 % of the time, and a TERM trap that orphans vitest's worker (#160, judge_design round 1, operations)
6.5 passed on "old red-resize >= 1, new 0" over 40 pairs. If the fix did nothing, both sides share one p, and
(1-(1-p)^40)(1-p)^40 peaks at 0.25 (p about 1/58), so the rule cannot tell the fix from no fix; only old >= 5 vs new 0
(Fisher one-sided 0.027) is evidence, and p = 1/12 gives 3.3 old reds expected. The classifier counted any 15000 ms
waitFor timeout as the stale-size defect, so a slow shell or a 2 s hold release under load would both send the coder
back. The INT/TERM trap killed only the vitest main process: vitest 5.0.5 exits on SIGTERM without the global teardown
and its fork worker is reparented to PID 1 and runs the test body to the end (verified with a 20 s test). 6.6 did not
list test-run volumes or networks, so the run's sentinel volume stays unreported.
Rule: A load control's pass rule is a stated significance threshold on old vs new counts, with N chosen from p to
reach it. Each red class the tester can see gets its own label and owner. A trap that stops a test runner kills its
whole process group and waits for it; the leftover check lists every object kind the harness labels.

### 2026-11-16: Hog lifetime justified by a run length the calibration contradicts, and no time budget on a shared VM (#160, judge_design round 2, operations)
6.5 says `sleep 10800` "caps the hog at 3 h, above the longest allowed run (N <= 100 pairs)". The calibration at
HOG_LOOPS=96 measured 11-67 s per run, mean 28.2 s but 55.8 s over runs 1-13 while other sessions loaded the host.
At that rate 94 pairs take about 2.9 h and 100 pairs at the 67 s maximum about 3.7 h, so the hog can expire near the
end, `LOAD LOST` voids the batch, and the rule says "rerun": several hours of a 96-loop hog on a VM that also runs
the owner's `academy` stack and other sessions' suites, with nothing bounding the total.
Rule: Size every lifetime cap and duration claim from the measured maximum, not the mean, and give a long load run a
wall-clock budget that stops cleanly and keeps the completed interleaved pairs instead of voiding them.

### 2026-11-16: Hard load limit enforced in code for the loop count only, not for the time budget or the host-load gate (#160, judge_design round 4, security)
The round-4 hard limit has two parts: at most 4 generators, and a total budget well under 30 minutes. r160-load.sh
refuses HOG_LOOPS outside 1-4 before it creates anything. It takes any digits for BUDGET_S, and the hog's lifetime is
BUDGET_S + 120. So `BUDGET_S=7200`, the round-3 default and still in that round's run lines, starts a 2 h hog with no
refusal. HOST_LOAD_MAX is the same: "never with a raised HOST_LOAD_MAX" is only in the prose of 6.7.2 step 7, and
`HOST_LOAD_MAX=999` turns off the host gate that exists because of the incident. The limit held only for as long as
everyone typed the documented values.
Rule: When a hard limit comes from an incident, every knob that can exceed it (count, duration, gate threshold) gets a
refusal in the script before anything is created, and the dry run includes one refusal per knob.

### 2026-11-16: A "strong proof" rule with 3 runs per side that a non-fix passes 11-30% of the time (#157, judge_design round 1, architecture)
Design 5.4 calls starter-walk "fixed, base red and new green" when the old file times out in >= 1 of 3 full-suite runs
and the new file in 0 of 3. #106 saw this timeout in about 1 of 3 base runs. At a base rate of 1/3 a change that does
not touch the cause passes that rule with P = (1 - (2/3)^3) * (2/3)^3 = 0.21, at 1/2 with 0.11. The design's own
failure-mode row ("the 5000 ms timeout has a cause batching does not touch") is exactly that change: 5.9 would show the
duration drop and 5.4 would then print "fixed" by chance. The same design did the power math for L-AC6 (P(old = 0)
about 4e-5) but not here. fullsuite.sh also runs old before new in every round, while interleave.sh alternates.
Rule: A red-base/green-new rule states the chance that a non-fix passes it at the observed base rate (one-sided
Fisher: C(n_old, k)/C(n_old + n_new, k) when new is 0/n_new) and claims "fixed" only at <= 0.05, extending rounds up to
a stated cap first; old and new alternate order across rounds.

### 2026-11-16: Harness steps never run once: zsh modifier, no build, wrong calibration count, blocked poll (#157, judge_design round 1, operations)
The operations judge ran section 5 in a throwaway clone. 5.3 step 2 stops at once in the tester's zsh:
`"$BASE:apps/..."` and `"$BASE:services/..."` are read as zsh `:a`/`:s` modifiers (`git show` gets
`<W>/3c5ef63pps/web/...`). 5.3.3 runs the walk calibration in a fresh clone before anything is built, so the file
fails to import `@academy/lesson-schema/schema` and detect prints 0, a STOP. After a deps build (2.5 s) the
calibration prints `failed=2 timedOut=2`, not the `timedOut=1` the step requires, because a timed-out walk test gets
a second FAIL block from its afterEach (ENOTEMPTY, the write loop keeps going) and the 10-line window runs into the
next block. That is a second STOP. The 5.0 poll `sleep 60; ls` is blocked by Claude Code. Each walk timeout also leaves
a `$TMPDIR/wks-walk-*` dir that no cleanup step removes.
Rule: A design that hands the tester scripts has each command run once as written, in the tester's shell (zsh:
`${VAR}:path`), from a fresh clone (install and build), with each calibration's printed value copied from that run.
Waits use run_in_background notifications, not foreground sleep.

### 2026-11-16: The stop red control finishes before the tester can send the stop, and the stall rule has no trigger (#157, judge_design round 2, operations)
Dry run of round 2 in a fresh clone. 5.3 step 5 starts `interleave.sh stopcheck 3 4` on starter-walk.test.ts: 10 s warm-up
plus six runs of 1-2 s, so the harness exited on its own about 18 s after start (uptime 3.9-4.4). The kill sent right after
the GROUP line printed `kill -<pgid> failed: no such process`, and both pass conditions (`pgrep -x yes` = 0, output ends with
`HARNESS_EXIT`) still held, because a natural exit satisfies them. So the check that decides group stop vs fallback for every
later run can pass without stopping anything. With 100 rounds the same kill stopped yes, pnpm and vitest within 0.5 s.
Separately, 5.0 and 5.2 tell the tester to wait for the completion notification and to stop a run with no new line for
15 minutes, but give no command that waits: a hung run sends no notification, and nothing makes the tester look at the clock.
Rule: A stop red control runs long enough that the stop lands mid-run (rounds sized from a measured per-run time), and its
pass condition must be false on a natural exit (kill rc 0, `rc=143`, no `.done`, fewer run lines than planned). Every wait on
a background run is a literal bounded command that also checks the stall rule.

### 2026-11-16: A load-based stability plan for a shared host, sized as if the machine were idle (#157)
Every #157 design round prescribed +40 `yes` (and full-suite loops) as the load for base controls, on a 10-core
laptop shared with up to eight other sessions. Host load reached about 360 and another app crashed; the runs
measured other sessions' spikes rather than the change, and the plan stopped three times on host noise. The one
control that gave a clean answer, the forced-yield `performance.now` mock for AC6, needed no load at all.
Rule: A stability plan prefers deterministic controls (fake timers, a mocked clock, an injected per-call delay that
makes the old code exceed the timeout and leaves the new code under it). Synthetic load is a last resort: at most 4
generators, trapped, a per-run timeout, `pgrep -x yes` empty after each run, and the plan states why no
deterministic control exists.

### 2026-11-16: A catch-all flag taker that focuses on stale flags, with a comment claiming it never does (#95, judge_design round 1, architecture)
Design 1.1 `FocusOnAnyRetry` focuses the not-found h1 whenever `takeAnyRetryFocus()` finds any flag. D1 says a pending
flag is either from the retry this page replaced or "stale from an interrupted refresh; in both cases clearing it is
right", but the code focuses in both cases, not only clears. Section 8 then accepts the stale case as "pre-existing for
every FocusOnMount", which is false for this page: today not-found never moves focus, after #95 every stale flag of any
id (a refresh superseded by a navigation; a lesson text retry that ended on the lesson course error, flag = panel id)
moves focus to the h1 on the next ordinary not-found arrival, against AC9 "otherwise focus does not move". The dictated
not-found header "The h1 takes focus only after a retry this page replaced" is therefore false, and no test or mutation
row covers the case. A cheap fix exists: store the pathname with the flag in `retry()` and let the not-found taker
clear always but focus only when the pathname still matches.
Rule: When widening a one-id taker to "any id", enumerate every path that leaves the flag stale and decide focus and
clear separately for each; an exclusivity claim in a dictated comment needs a test for the counter-example.

### 2026-11-16: Scratch-clone procedure leaks its clone on an early guard and its cleanup guard passes a dot-dot path (#95, judge_design round 1, operations)
Design 6.3 prints `CLONE $C` only after the per-file guards, so the dry-run's `GUARD FAILED missing ... not-found.test.tsx`
left a full clone in the scratchpad with no path printed. 6.4 runs the cleanup only after `RED TREE READY`, never sets
`C`, and its `case "$C" in "$S"/m95-clone-*)` guard accepted `$S/m95-clone-X/../../outside` (case `*` matches `/` and
`..`), echoed its refusal with exit 0, and did nothing silently when `repo/apps/web` was missing.
Rule: A scratch procedure prints its scratch path right after creating it, runs its cleanup on every exit path, rejects
`..` and exits non-zero on refusal; dry-run the cleanup with a dot-dot path and an early guard failure.

### 2026-11-16: Dictated comment states a URL-timing guarantee that back/forward breaks (#95, judge_design round 2, architecture)
Design 1.1 dictates the comment over `isSetOnShownPage`: "Next writes the new URL in an insertion effect of the commit
that shows the route (app-router.js HistoryUpdater), so the pathname here is the one of the view now mounted", and
section 0 states the same as a fact. On a back/forward press the browser changes `window.location` before `popstate`
fires; Next then dispatches ACTION_RESTORE in a transition (`app-router.js` handlePopState/traverse) and commits later,
and HistoryUpdater can even skip its write (`hasMissedTraversal`). Between the two, the old view is mounted under the
new pathname. The rule still fails closed there (a taker sees a foreign pathname and drops), but the comment would ship
false, and 1.4 lists back/forward under E4 itself.
Rule: Before dictating a comment that says when the browser URL changes, check every way the URL can change (Next
navigation, refresh, history.replaceState from app code, popstate), and qualify the claim for the ones that do not go
through the router's commit.

### 2026-11-16: Listed what a stack run writes outside the scratchpad, but not all of it (#95, judge_design round 3, operations)
Round 3 change 11 added to 6.4 (and the round-3 table) that `isolated-stack.sh t32` writes "Docker resources of
project `academy-t32` (containers, network, volumes) and the image `academy-web:t32`, which its teardown removes".
The script runs `up -d --build` (`isolated-stack.sh:335`), so it also builds `academy-workspace-service:t32`
(`docker-compose.yml:71`, removed by teardown through `T31_IMAGES`, `isolated-stack.sh:58`), adds BuildKit build-cache
records for both images that teardown never removes, and pulls `node:22.23.4-alpine` when it is absent
(`isolated-stack.sh:48,328`), which also stays. A tester reading the list as complete reports a clean machine when it
is not, and build-cache growth is exactly what #113 measured.
Rule: When a design says what a command writes outside the scratchpad, derive the list from every create/build/pull
in the script it runs, and say which items its teardown removes and which stay.

### 2026-11-16: The round-4 "every create, build and pull" list still stopped at the script's own lines (#95, judge_design round 4, operations)
Round 4 rebuilt the 6.4 table from the docker lines of `isolated-stack.sh` itself, not from what those lines run.
Missing: the `docker/dockerfile:1` frontend that BuildKit pulls for `apps/web/Dockerfile:1` (`# syntax=` directive;
a `frontend` build-cache record that stays, and a new one when the tag moves), the `pnpm` cache mounts of both
Dockerfiles (`exec.cachemount` records, stay), and the one-off `docker compose run --rm --no-deps web` containers of
`check-image-migrations.sh:40,63` (called at `isolated-stack.sh:340`). 6.2's list of git-ignored worktree files cited
`.gitignore:12-20` but left out `apps/web/.next/` and `apps/web/next-env.d.ts`, which `next typegen` in
`pnpm typecheck` (step 1) writes. Same class as the round-3 entry above, one level deeper.
Rule: Derive a "what this writes" list by following every command the script runs into the files it reads
(Dockerfiles incl. `# syntax=` and `--mount=type=cache`, called scripts, package scripts behind turbo tasks), not
only the script's own lines.

### 2026-11-16: "Every create, build and pull" list still misses the build's own registry fetch (#95, judge_design round 4, architecture)
Round 4 change 1 says the 6.4 table is derived from every create, build and pull of `isolated-stack.sh t32`, and 6.2
reuses it for t31. The web build reads `apps/web/Dockerfile:1` `# syntax=docker/dockerfile:1`, which makes BuildKit
fetch the dockerfile frontend image from the registry; the repo says so itself (`services/workspace/Dockerfile:2-3`,
"a directive would make every build fetch a frontend image from the registry"). The table names only
`docker pull "$NODE_IMAGE"` as a pull, so the tester checks the node image and not the frontend, which stays after
teardown. Lesser: `check-image-migrations.sh:40,63` (called at `isolated-stack.sh:340`) creates `docker compose run --rm`
web containers, a creator the table does not name (they are removed by `--rm` and caught by the final check).
Rule: Derive a "what stays" list from the Dockerfiles and the scripts the script calls too (syntax directives, FROM,
cache mounts, `compose run`), not only from the script's own docker lines, before claiming it is complete.

### 2026-11-16: Two judge rounds spent patching a hand-written inventory of a stack run's side effects (#95, judge_design rounds 3-4)
The #95 tester procedure listed what `isolated-stack.sh t31|t32` leaves outside the scratchpad. Round 3 failed because
the list missed a second image, the build cache and a base-image pull; the round-4 table claimed "every create, build
and pull" and failed again on the dockerfile frontend fetch, the pnpm cache mounts, the `check-image-migrations.sh`
run containers and the `next typegen` output. Each fix read one level deeper and still stopped short: side effects
hide in what the script calls (Dockerfile directives, helper scripts, tool internals).
Rule: never hand-write an inventory of side effects. State only what the code verifies (the script's own teardown and
final check, with line refs), name known leftover categories as examples, and have the tester measure the rest with
read-only before/after snapshots, each snapshot command run once before the judges see it.

### 2026-11-16: "Verified by code" bullet implied the final check covers the built images (#95, judge_design round 5, architecture)
Design 6.4 lists under "Verified by code" the line "Not checked by the final check: images other than `T31_IMAGES`".
The final check (`isolated-stack.sh:236-244`) lists only containers, volumes and networks by label; it checks no image.
`T31_IMAGES` are only removed in teardown (`:226-230`), and a failed `docker image ls` at `:227` yields an empty
string, so the removal is skipped with no `TEARDOWN FAIL`. The sentence credits the code with a check it does not do,
in the very section whose round-5 promise was "states only what the code verifies".
Rule: in a "verified by code" list, every negative ("not checked: X other than Y") is also a positive claim about Y;
check Y against the cited lines the same way as the positive bullets.

### 2026-11-16: Gate commands dry-run in a shell other than the one the tester runs, and a per-commit loop that ran zero times (#162)
Design 4.4 and 5.14 were written for bash, but the tester's Bash tool runs zsh with `grep` wrapped by ugrep. There
`$IT test/...` is one word (zsh does not split it: `command not found`, rc 127, which reads as "red" on every M row),
and the M8 guard `grep -c 'holds ${storedValueText(value)}'` counts 0 (ugrep takes the `$` as an anchor; BSD
`/usr/bin/grep` counts 1), so M8 stops at GUARD FAILED. Step 14 runs `git rev-list main..HEAD` "in the throwaway
clone", which has no local `main` (the design says so itself in step 6): rev-list fails, the loop runs zero times,
prints nothing and exits 0, so per-commit greenness is never checked.
Rule: Dry-run every gate command in the shell the tester will use (the Bash tool, zsh), or put it in a file run with
`bash <file>`; never pass a command through an unquoted variable; use `grep -F` for literal anchors; any loop over
revisions in a clone uses `origin/main` and fails when the list is empty.

### 2026-11-16: A red control that relied on a CHECK refusing NULL (#162, judge_design, architecture)
Design 4.4 M6 strips `array_ndims(x) IS NULL OR` from `attempts_included_check_ids_dims_check` and predicts that `{}`
is then refused (T9, T13 and every default-`{}` fixture red). `array_ndims('{}')` is NULL, `NULL = 1` is NULL, and a
CHECK accepts NULL, so nothing goes red: the disjunct is a no-op inside a CHECK and the control was never run. The
same blind spot sits in 1.2, where `ELSE false` is rejected only for the reported name, not because it would refuse
`{}` (ndims NULL takes the ELSE branch).
Rule: For every CHECK mutation, evaluate the mutated expression on each listed value to TRUE/FALSE/NULL (NULL passes)
before predicting red, and dry-run every red control whose prediction is not obvious; a clause that only turns NULL
into TRUE inside a CHECK is redundant and is described as such, not given a red control.

### 2026-11-16: Mutation helper edits a relative path, so a reset cwd mutates the task worktree (#148, judge_design round 1, security)
Design 3.1 `mutate()` runs `perl -0pi` on `"$file"`, and the 3.2 rows pass `apps/web/lib/progress/rules.ts` /
`outcome-writer.ts` relative, with only "(from `$M`)" in prose and no `cd "$M" &&` in the step. Agent Bash calls start in
the task worktree, the anchors exist there too (same base), and the active pipeline lets shell writes to product files
through, so the mutant lands in the task worktree's product code. The helper's `git -C "$M" diff --stat` is printed,
not asserted, so it shows nothing and the run continues; the between-runs restore is `git -C "$M"` and does not undo it.
Rule: every mutation command takes an absolute `"$M/..."` path (or the helper prefixes `$M` itself and refuses a file
whose real path is not under `$M`), and asserts the clone's diff is non-empty and the task worktree's diff is unchanged.

### 2026-11-16: Expected red set for a mutant was taken from a grep of one field, not of every test reading the changed value (#148, judge_design round 1, architecture)
Design 3.2 expects M1 (`isInNextRun: isCounted && !isClosed && !tally.hasPassed`) to turn exactly {P6, the example at
rules.test.ts:263} red. The design's fact list grepped `spendsTokens`/`isInNextRun` and missed that `composeRun` reads
`isInNextRun`: rules.test.ts:278 "composes a run of exactly the checks in the next run, with their kinds" expects the
passed command check "done" in `includedChecks`, which M1 drops, so M1 is red in three tests. The tester is told a
larger red set is reported, not dismissed, so the run would come back as a mismatch against the design.
Rule: for each mutant, list every test that reads the mutated value directly or through a consumer (here composeRun,
hasNextRun) and derive the expected red set from that list, not from a grep of the field name alone.

### 2026-11-16: Between-runs restore check scoped to a directory that also holds the test patch (#148, judge_design round 1, operations)
Design 3.2 says after each restore `git -C "$M" diff --stat -- apps/web/lib` "prints nothing (the test patch lives in
other files and stays)". The patched rules.property.test.ts is itself under apps/web/lib, so in the dry run the line
printed that file after every restore and can never be empty; a tester following it literally stops or learns to
ignore it, and then a leftover mutant in rules.ts would be ignored too. The `mutate` helper's own `diff --stat` has the
same scope. Separately, the Bash tool's shell is zsh, where `rm -f "$S"/148-*.json` aborts with "no matches found" when
no JSON was written, and that whole rm (patch file included) is skipped.
Rule: a "prints nothing" check is scoped to exactly the files the step restores (here rules.ts and outcome-writer.ts),
and every scripted step is dry-run in the agent's real shell (zsh here), with globs that tolerate no match.

### 2026-11-16: Dictated an exclusivity comment that ADR-0007 rule 7 contradicts (#148, judge_code, architecture)
Design D9 prescribed the I-out-7b holder comment "this is the shape of #34's per-check commit, the one write that
can land while the writer waits". ADR-0007 rule 7(a) runs applyLessonOutcome after every transaction that inserts
check results or sets an attempt final (R34-3, R34-14, R34-15), and a finished attempt changes the facts through its
missing results (rules.ts resultsWithMissing). So the result insert is not the one write; the same test's D15
comment even names the attempt change as a possible concurrent write.
Rule: Before dictating "the one"/"only" in a comment, read the ADR rule that lists the writers and grep for the others.

### 2026-11-16: Claimed a test goes red for a new kind the generators never draw (#148, judge_code round 2, architecture)
Design section 5 says "A new token-spending kind is added to CHECK_KIND_TRAITS without the test set: P6 (a) goes red
at once", and the coder wrote it into the TOKEN_SPENDING_KINDS comment as "has to be added in both places, or P6 goes
red". P6 sees only kinds that scenarioArb draws from the hand-written KINDS list (rules.property.test.ts:28, typed
`readonly CheckKind[]`, not exhaustive) and tokenPassedScenarioArb's own `constantFrom("rubric", "hidden-task")`. A new
kind added to the lesson schema and to CHECK_KIND_TRAITS (a Record, so it must be) but not to KINDS is never
generated, and P6 stays green. Only a changed trait of an existing kind turns it red.
Rule: Before writing "X goes red when Y", trace whether the test's generators can produce Y at all; a hand-written
list of variants guards only the variants on it.

### 2026-11-16: Listed one stale comment of the changed path and missed the one beside the changed line; ADR said "not in process listings" (#115, judge_design round 1, architecture)
Design 2.2 updates the errors.ts:123-125 comment because #115 makes it stale, but not the comment directly above the
line it changes: spec.ts:197 "Added to the container's own `HOME`; nothing from the service's environment reaches the
shell." Once `Env` carries `ANTHROPIC_API_KEY` from the service's config, that sentence is false, and a coder who
follows the design's list leaves it. Separately, ADR item 14 and the 2.2 table say the key is "not shown by process
listings" / "`ps` / `docker top`: no, they show arguments". procps `ps e` (the #33 image has procps, ADR-0002 item 13)
prints each process's environment from `/proc/<pid>/environ` for any uid-1000 caller, and `docker top <id>` passes ps
options to a root `ps`; the readers are the same as the uid-1000 and socket-holder rows, but the sentence is false.
Rule: When a change makes a value flow where a comment or ADR said nothing flows, grep every comment and ADR sentence on
that path (`rg -n 'service.s environment|reaches|never' <changed files>`) and list each one to rewrite; for every
"not shown by tool X" claim, check the tool's options that read the same source (`ps e`), not only its default output.

### 2026-11-16: "Who can read the key" table missed the service-API path, and the web/db guard checked names only (#115, judge_design round 1, security)
Design 2.2 says "web, db, any other container: no". Web holds `WORKSPACE_SERVICE_SECRET` and reaches the service on
`workspace-api`; `GET W/terminal` with that Bearer opens a uid-1000 shell whose env is the key (ADR-0011 items 1 and 4),
so whoever controls web, or holds the secret and reaches the service, reads the key without the learner's involvement.
The same path already reached the `/login` credential, and ADR-0002 item 10 never named it. Separately, U-compose-key
asserts only that web/db environment KEYS do not match `/AGENT_API_KEY|ANTHROPIC/`: `FOO: ${WORKSPACE_AGENT_API_KEY:-}`
or `env_file: .env` on web passes it, so "web gets nothing" is not proven.
Rule: For a "who can read secret S" table, enumerate every capability that yields S (env, /proc, socket, and every API
that runs code where S lives) and name each credential holder of that API as a reader. A "service X never gets S" guard
checks values and `env_file` of every other service, not only variable names.

### 2026-11-16: README append command glues the key onto the previous .env variable (#115, judge_design round 1, operations)
Design 6.4 point 1 dictates `printf 'WORKSPACE_AGENT_API_KEY=%s\n' "$(pbpaste)" >> .env`. When `.env` does not end
with a newline (editors such as VS Code do not add one by default), compose reads the key as part of the previous
line's value: measured with fake values, `WORKSPACE_SERVICE_SECRET` became `<secret>WORKSPACE_AGENT_API_KEY=<key>`, so
the key reached web's environment and the service's bearer secret, the service started with no key, and nothing failed.
Rule: A prescribed command that appends to or edits an owner's file is run against that file's corner cases (no final
newline, an existing line for the same name) before it goes into the design.

### 2026-11-16: Dictated replacement comments said "nothing else from the service's environment" over bodies built from it (#115, judge_code round 1, architecture)
Design 6.0 dictated the spec.ts:79 comment "nothing else from the service's environment enters the container create
body" and the spec.ts:216 comment "The only value from the service's environment that reaches the shell is the agent
key". The coder wrote both word for word. The create body's `Image` (WORKSPACE_IMAGE override), `NanoCpus`/`Memory`/
`PidsLimit` (WORKSPACE_*_LIMIT) and labels (WORKSPACE_INSTANCE) all come from the service's environment, and the
exec's `Cmd` carries TERMINAL_SHELL, which becomes the shell itself. Both sentences were meant about `Env` and say
something wider. This is the #121 lesson again, on the very rows written to fix stale comments.
Rule: A dictated replacement comment names the field it is about (`Env`, not "the create body" or "the shell"), and
before sending it, list every input of the function it sits in and check the sentence against each one.

### 2026-11-16: Scratch red/green harness was blocked by the shell guard and still wrote into the worktree (#156)
Design 6 dictated `cp "$W/apps/web/..." "$S/"` and `ln -s "$W/apps/web/node_modules" "$S/node_modules"`. While the main checkout holds a LEARN state, bash-code-guard consults it for any command naming `$W` (the worktree path contains the main path) and blocks a write verb followed by `apps/`, so both setup steps fail as worded. The design also claimed the harness never touches the worktree, but vitest without `--no-cache --no-fsModuleCache` writes `results.json` and creates `node_modules/.vitest-cache` through the symlink into `$W/apps/web/node_modules`. With no `--reporter=verbose` the default reporter lists only failing tests, so the "X green" expectations cannot be read from the output, and the R3-R5 rows named only some of the tests that go red.
Rule: A scratch harness is dictated as a script file run whole, with source reads whose write target is the scratch dir, every tool cache pointed at or disabled for the scratch dir, a reporter that names every test, and an expected outcome for every test the mutation can reach.

### 2026-11-16: Dictated an unconditional exactness comment that the same design's 4.1 contradicts (#156)
Design 4.6 told the coder to write in split.ts that "multiplying first leaves a single rounding (the division)", with no condition. Design 4.1 itself says that on non-dyadic live inputs (17.6 px root font, 90 % or 110 % page zoom, passed by lesson-layout.tsx:73 from getBoundingClientRect and getComputedStyle) paneMinPx * 100 and the subtraction round too, and a limit can be off by one. The coder copied the wording, so split.ts:34-36 claims an always-exact limit that holds only for binary-exact widths. 4.6 also dictated "rounds and put the 440 px tie on the wrong side", a tense clash that reached split.test.ts:22.
Rule: A comment a design dictates carries every condition the design's own analysis attaches to the claim; reread each dictated sentence against the section that proves it, and for grammar, before handing over.

### 2026-11-17: Read scripts anchored on Playwright summary lines that turbo prefixes (#180, judge_design round 1, operations)
c180-read.sh R3/R4 grep `^ +[0-9]+ (failed|flaky|interrupted)$` and `-Fx '  1 failed'`, but the e2e stage of
isolated-stack.sh runs `pnpm test:e2e` -> `turbo run test:e2e`, and turbo prefixes every line with
`@academy/web:test:e2e: ` (real #95 t32 log: `@academy/web:test:e2e:   5 failed`). R3 reads `[]` on any real run, so
the control can never print AS EXPECTED, and c180-read-t31.sh's summary guard can never fail for the e2e stage. The dry
run used a hand-written log without the prefix, so it could not see it; a real log of the same harness was on disk.
Rule: Before a read script anchors on tool output, run it against a real log of the same harness (an earlier run's
log), never only a hand-made one, and make every guard go red on a real failing log.

### 2026-11-17: Control hold caught the stylesheet too, and a dictated comment stated a "can" as an "is" (#180, judge_design round 1, architecture)
The C1 hold routes `**/_next/static/chunks/**`, which in this Turbopack build also serves the CSS (`static/chunks/*.css`).
`app/layout.tsx:16` puts an inline theme script in `<head>` after the hoisted stylesheet, and an inline script waits
for a pending stylesheet, so the parser stalls in `<head>` for the whole hold: the user button is not in the DOM, the
old variant's `focus()` auto-waits until the hold ends and its Enter races hydration instead of landing 2-3 s before
it. The positive control counts CSS requests too, so it passes with no script held. Separately, the dictated comment
says an Enter before the chunks run "reaches no React handler and is lost" (React's root listener does receive it, and
a forced hydration that does not suspend on the menu's path dispatches it), and "the load event waits for the scripts
the document loads" (an implicit "every"; the design's own table excludes scripts added after load).
Rule: A route hold is scoped by resource type to the thing the claim is about (`resourceType() === "script"`), and the
positive control counts only that type; check what else the pattern serves and whether it blocks the parser. Dictated
comments say "can" where the evidence shows a possibility, and name the cases a universal-sounding noun covers.

### 2026-11-17: Temp-file prefix shared with a script name, and an exit code read after a command substitution (#180, revision 2, own dry run)
In revision 1 the read scripts made their stripped copy with `mktemp "$S/c180-read-XXXXXX"`, next to `c180-read.sh`
and `c180-read-t31.sh`. While dry-running revision 2, a cleanup `rm -f c180-read-*` meant for the temp copies also
deleted `c180-read-t31.sh`. In the same dry run, `echo "rc=$?"` placed after `$(basename ...)` in one echo printed
rc=0 for every read, red or green, because the substitution reset `$?`.
Rule: Temp files get a prefix no script or log shares (`c180-strip-XXXXXX`) and are removed by the script's own EXIT
trap, never by a glob. Capture an exit code into a variable on the next statement (`r=$?`) before anything else runs.

### 2026-11-17: Decision table titled "every outcome, every step" left the step wrappers' own guards out (#180, judge_design round 2, operations)
Revision 2 closed round-1 operations blocker 2 with one table in 4.2 and covered every line isolated-stack.sh and
c180-prep.sh print. The one-line wrappers of steps 1, 4, 6 and 7 print their own guards, and six of them have no row:
`GUARD FAILED $F exists` (1, 7), `GUARD FAILED ..`, `not a c180 clone: $C`, `$L exists` (4, 6), and in step 6
`worktree differs from $B beyond the spec` and `untracked files in the worktree`. The step-6 diff guard is where a
moved and merged origin/main shows up before C2, which is the base-as-value case the revision was about; without a
row the tester has to improvise (edit the base file, re-run step 0, revert the tree).
Rule: When a design says a decision table covers every outcome, grep every `echo`/`GUARD`/`STOP` text of every script
AND every inline command the procedure runs, and give each one a row, or add an explicit catch-all row for the rest.

### 2026-11-17: A catch-all "any output a row does not name -> stop" turned the happy path into stops (#180, judge_design round 3, operations)
Revision 2.2 of the #180 design added a catch-all row to the tester decision table (4.2) but no rows for the success
output of steps 1, 2, 3, 7 and 8 (the disk record, lint/turbo output, step 3 `rc=0` and `PREP READY`, `CLEANUP OK`).
Read literally, every clean run stops at step 1; worse, the step 7 disk record printed right after C1 maps to "stop",
whose step 8 deletes the clone, and `c180-read.sh` needs `$C/n-old.txt` from that clone, so the C1 stack run could
never be read and would be burned from the budget of 3.
Rule: A decision table that claims every outcome names the success output of every step too, and a "stop" after a
stack run always runs the read-only log read before any cleanup removes what the read needs.

### 2026-11-17: Running the read after every stack run let an infrastructure failure read as "(a) unproven" (#180, judge_design round 4, architecture)
Revision 2.3 of the #180 design made the read script part of a post-run sequence P that runs after every
`isolated-stack.sh` invocation, then decides "on the run's own lines, P1 and P3" with no order between them. In 2.1/2.2
step 5 was reached only from the expected step-4 pair, so `NOT R3`-`NOT R9` always described a control that ran. Now a
run where the e2e stage did not run or ran on a broken stack (`STOP preflight ...`, `FAIL guard`, `STOP postgres...`,
`FAIL seed`, a `set -e` abort giving `RESULT FAIL (run rc=1 ...)`, no RESULT line) makes the read print `NOT R3`-`NOT R9`
too, and the step-5 row "NOT AS EXPECTED with NOT R3-NOT R9 -> architect (R7/R8: fixed variant red, (a) unproven)"
matches it alongside the Stepan/orchestrator route of the run line. `FAIL seed` and the `rc=1` aborts have no run-line
row at all, so the only specific route left is "-> architect, (a) unproven", which 1.2 turns into a switch to (b).
Rule: When a read that judges the fix is run unconditionally (to keep its inputs alive), state that it only counts as
evidence when the run's own lines were the expected ones; otherwise its output is reported, never routed, and the run
line decides.

### 2026-11-17: The general stop rule caught the C2 repeat path, and step 3 hid the CLONE line on its own failures (#180, judge_design round 4, operations)
Revision 2.3 replaced the case list by R-stop with exceptions "the only ones". Step 4 got a carve-out for its expected
`rc=1` and `T32 RESULT FAIL (run rc=0, check status=1, teardown failed=0)`; step 6 got none. A C2 run that the read
calls `C180 REAL RUN REPEATABLE` has the wrapper print `rc=1` and `T31 RESULT FAIL (run rc=0, check status=1, teardown
failed=0)` (checked on the t31-green log with the dry run's other-spec edit), so R-stop (1), (2) and (3) fire and the
step-6 repeat row can never be reached; neither walk took that branch. Separately, 4.2 counts only printed lines as
output and runs step 8 "if a CLONE line was printed", but step 3 prints only `tail -n 5` of the prep log: on a
typecheck failure the tail is turbo output plus `GUARD FAILED typecheck (see <C>/typecheck.log)`, the CLONE line is
log line 2 of 33, so a literal tester skips `c180-clean.sh` and leaves the clone with node_modules (du 859M measured).
Rule: After writing a general stop rule, walk every row that routes somewhere other than "stop" (each repeat, each
exception) with the real wrapper output of that branch, and for every later step that needs a value from an earlier
one, check that the earlier step prints it on its failure paths too, not only on success.

### 2026-11-17: The expected run line was taken as proof that the tests ran (#180, judge_design round 5, architecture)
Revision 2.4 of the #180 design orders 4.2 so that the read decides only when P0 shows nothing but `T3x FAIL e2e` and
a `RESULT` line with run rc=0. But `isolated-stack.sh:294` prints `FAIL e2e` for any non-zero `pnpm test:e2e`,
and the run goes on to `RESULT FAIL (run rc=0, check status=1, teardown failed=0)`: exactly the expected C1 pair.
An e2e stage that never produced a Playwright result (turbo `^build` dependency failure, a config-load throw in
`playwright.config.ts`, a globalSetup or runner crash) therefore passes B1 and B2, and the read prints `NOT R3
summary lines: []` ... `C180 CONTROL NOT AS EXPECTED` (C2: `NOT G4`, `C180 REAL RUN NOT GREEN`), which B3 routes
to the architect, the same infra-as-evidence route round 4 closed for the other stages.
Rule: Before a read counts as evidence, check that the stage it judges actually produced its own result (here the
e2e stage's prefixed `<n> passed (` summary line), not only that the wrapper printed the expected failure line.

### 2026-11-17: The cleanup that runs "after any stop" also runs under a stack run that is still alive (#180, judge_design round 5, operations)
Revision 2.4 of the #180 design says in 4.0 that a run with no completion notification after 45 minutes gets one
`tail`/`stat` and then rule B (no `RESULT` line: B2), and 4.2 C says step 8 runs after any stop. On that path the C1
run is by definition still running, from the clone: `isolated-stack.sh` did `cd "$root"` into `$C/repo` and its
EXIT trap runs `docker compose -p academy-t32 -f docker-compose.yml down` and the image removals from there. Step 8
`rm -rf`s that clone, so when the run ends or is killed its teardown has no compose files and leaves the t32
containers, volumes, network and images behind. P1 on a live run also prints `LEFTOVERS FOUND t32` (B1 -> Stepan),
and C still deletes the clone before Stepan can act.
Rule: A cleanup step that removes the files a background job runs from is gated on that job's exit, not on a stop
decision; a timeout path stops and hands the live job to Stepan without cleanup.

### 2026-11-17: The routing table was closed but the frozen sections kept their own routes to (a)/(b) (#180, judge_design round 6, architecture)
Revision 2.5 of the #180 design says in 4.2 B3 that nothing in the procedure routes to the architect and that only the
orchestrator, after reading the log, may send the task to (b). The frozen sections still route by name: 1.2 "If G1 or
G2 fails, (a) is wrong for this page and the task comes back to the architect for (b)", 3.3 "R9 is red ... (decision
table: architect)" (the decision table has no such row any more), 6 "(b) kept as the fallback if G1 or G2 fails". In
1.2 G1/G2 are the control's marker and fixed-green gates (R7/R8 in 3.4), but `c180-read-t31.sh` prints `NOT G1` ...
`NOT G5` for C2, and those NOT ids are exactly what the B3 stop report hands the orchestrator. A C2 `NOT G1 T31 FAIL
lines: [T31 FAIL e2e]` from another spec's flake beyond the budget reads, by 1.2, as "(a) is wrong -> (b)": the
round-5 class (a read's NOT id taken as a verdict on (a)) through the prose instead of the table. Freezing sections
0-3 is what kept the old routes alive.
Rule: When a routing rule is narrowed, grep the whole document (frozen sections included) for every route word and
gate id it replaces (`architect`, `(b)`, `fallback`, `is wrong`, each gate name), and give every gate id one meaning
across the design and the scripts' output.

### 2026-11-17: Container lookup protected only the owner's project, not "every container this run did not create" (#96)
Design D2 made the destructive chmod target any running compose `web` service on 127.0.0.1:<port> whose project is non-empty and not `academy`. So a local run with the switch on and a base URL that points at another session's isolated stack (`academy-t32`, same image, the glob `/app/course/*/course.yaml` matches) or at another project's web container passes the lookup, and `docker exec -u 0 ... chmod a-r` runs there. D3's "the chmod never reaches a host file" was derived from academy's compose file, but the lookup never checks the mounts of the container it accepts. This repeats the #31 judge lesson (protected set as the owner's objects instead of the complement).
Rule: A destructive action on a shared host targets only objects the run itself names: the stage passes its own compose project and the lookup requires equality with it (and refuses `academy`); every safety claim about the target (no host mount) is checked on the accepted object, not inferred from one compose file.

### 2026-11-17: Pass criteria and a guard claim stated from assumed tool behaviour, not measured (#96, judge_design round 1, operations)
T4 required "every test is listed failed, none skipped" for a spec whose gate throws in `beforeAll`. Playwright 1.64.1
(measured in a scratch spec) reports only the first test failed and the rest "did not run" (`skipped` in the JSON
stats), exit 1, so the tester could never meet the criterion. D7 claimed a copied `WEB_PORT=3080` line would also
throw in CI's main suite, but `pnpm test:e2e` runs through turbo, whose strict env (`turbo.json:3,16-25`) drops the
job's `WEB_PORT` (measured with turbo 2.11.10): the file value 3080 then differs from the base URL port and the
decision allows. Only the direct Playwright stage would refuse.
Rule: Every pass criterion and every "this goes red in X" claim names how it was measured; for a step that runs
through turbo, check its passThroughEnv before reasoning about which variables the process sees.

### 2026-11-17: "Fails, never skips" promised for a gate whose hook semantics were not read (#96, judge_design round 1, architecture)
D1 and section 1 promise that with the switch on the spec "fails (never skips)", and the failure-mode table says "tests fail", for a gate in `beforeAll`. Playwright 1.64.1 source: a failing beforeAll records `_skipRemainingTestsInSuite` (`lib/worker/workerProcessEntry.js:1787-1788`), and the runner reports those tests with status `skipped` (`lib/runner/index.js:6059,6094`). Only the first test fails; the run still exits 1. The sentence would have become a spec comment that lies, and T4 could not pass. Same round: D7's "red in two places" ignored that `pnpm test:e2e` goes through turbo's strict env, which drops the job's `WEB_PORT`.
Rule: Before promising how a test runner reports a hook failure, read it in the installed runner's source or a scratch spec, and pick the hook (beforeAll vs beforeEach) from the reporting the design needs.

### 2026-11-17: Pass criteria counted by grepping the list reporter's log, which repeats source text (#96, judge_design round 2, operations)
r2's E9 counts `E9 afterEach ran` and `E9 gate refused` with `grep -c` on the list log and requires `afterEach=3`. The
list reporter prints a code frame around each throw, so source lines appear again: the orchestrator's dry run got
`afterEach=6`, and by the block's own rule the tester must stop before T4. T4 then says "every failure carries the
reason" without saying where to read it; T4c's reason is a literal at the throw site, and a scratch spec
(Playwright 1.64.1, helper module throwing that literal) gave 6 grep hits for 3 failed tests, so a log count of 11 would
pass with only half the failures carrying it. The JSON per-result `error.message` gave the right answer (3/3).
Rule: Count tests, statuses and messages from the JSON reporter's per-result fields, never with grep on a human
reporter's log, and dry-run each criterion's counting command once before handing it to the tester.

### 2026-11-17: Pass count for a file-filtered run ignored the project's dependency (#96, judge_design round 2, architecture)
E8 requires the PR's course-unreadable step to list "11 passed" and T3 "the 11 tests passed", for
`playwright test e2e/course-unreadable.spec.ts --project=chromium` without `--no-deps`. The chromium project has
`dependencies: ["setup"]` (`apps/web/playwright.config.ts:95`), and Playwright 1.64.1 gives a dependency project
all its files regardless of the file filter (`lib/runner/index.js:2517-2522`, `allFilesForProject`), so
`auth.setup.ts`'s one test runs too and the summary reads 12 passed. Only T4 (with `--no-deps`) gets 11.
Rule: For every expected test count, list the projects the command actually runs, dependencies included, and
count from the JSON stats of that whole run.

### 2026-11-17: ADR residual scoped the scan's blind spot to the title, though the code drops the fragment everywhere (#148, judge_design, security)
Design 3.1 R2 states the residual as "the e2e scan cannot detect grader material quoted inside a title". The code
removes such a fragment from the forbidden list itself (`apps/web/e2e/leak-fragments.ts:111-114`), and the
FragmentScanner (:119-139) then scans every served body without it. So the fragment goes undetected in any response,
including a leak of the grader file it came from; a grader file whose fragments are all contained in titles can
reach the browser whole without the scan noticing. The residual as written understates the leak-defence gap.
Rule: When stating what a filter exempts, state where the exemption applies (every scanned body, not only the
place the exempting text appears), and check it against the consumer of the filtered list, not only the filter.

### 2026-11-17: Revision stated the scan's second blind spot as an absolute the matcher contradicts (#148, judge_design round 2, security)
The round-2 R2 (design 3, line 111) adds: "a body that carries only part of a run, or grader text in shorter runs, is
not detected either". The scanner tests every listed fragment at every body index (`leak-fragments.ts:131-138`), so a
part of one grader run that contains another source's whole fragment is detected: a scratch run with run A =
"assert result equals <starter line> exactly here" and B = the starter line alone reported B for a body holding only
B. Shared text between `starter/` and `checks/` makes this realistic. The run description also drops the trim
(`:33-34`: a 24-character regex match with edge spaces yields no fragment). Writing a gap too wide is still a false
claim in an ADR about a security control.
Rule: When a design states what a matcher misses, phrase it per fragment ("a body is reported only when it holds a
whole listed fragment") and test the absolute against overlapping fragments from two sources before sending.

### 2026-11-17: Claimed an e2e "first visit" guard without checking what earlier specs did to the same workspace (#150, judge_design round 1, operations)
Design 8.2 adds a no-note assertion to E-echo and says it "goes red for a server that shows the note on any
`created`". E-echo's lesson is the last visible lesson, and `leak.spec.ts:174` opens every visible lesson in the
`chromium` project, which the `terminal` project depends on (`playwright.config.ts`). The page open starts the
workspace there, so at E-echo the peek finds it running and the page attaches with no `PUT` at all (a t31 log of
2026-11-17: leak opens `final-deploy-and-change` at line 598, E-echo passes in 1.1 s at line 610). The assertion
cannot see `created`, on CI or on the isolated stack. The same step 6 also asked the tester to find `T31 OK e2e` in
`tail -n 40`, while that line sits about 200 lines before the end of the log.
Rule: Before claiming an e2e assertion distinguishes a server-side outcome, list every spec that opens the same
lesson earlier in the project chain and confirm the outcome the assertion needs actually happens in that run; and
check every success line of a tester step against an earlier real log of the same script.

### 2026-11-17: Dictated comment and ADR texts carried absolutes the code and the design's own sections contradict (#150, judge_design round 1, architecture)
Design 2.4 dictates the `lesson-started.ts` header "The one writer and the one reader of" the started flag, while
`lib/progress/check-state.ts:224-239` (`storedStatus`, null without a row) and `lib/progress/outcome-writer.ts:65-82`
(`lockStoredStatus`) read the same `lesson_progress` row. The ADR-0010 bullet (7.2) says `created` plus the row
"mean the working folder was lost", while 3 and the ADR-0007 bullet (7.1) accept an interrupted reset and a start
between another tab's `DELETE` and `PUT`, where the folder was removed on purpose. The ADR-0007 bullet says a failed
read is logged "by name and code only", while 2.2 and `describeDbError` print the constraint too.
Rule: Grep every "the one", "only", "mean" in a dictated comment or ADR text against the code and against the
design's own accepted cases before sending the design.

### 2026-11-17: Design conformance plan had no app screenshots at all (#150, judge_design round 1, architecture)
Design 5.1 says the app side of the Design conformance section uses reset-done screenshots, but tester step 7 takes
only prototype screenshots, and no step produces any app screenshot. ADR-0006 item 5 requires prototype and app
at 375 and 1280, light and dark, every AC marked, and judge-architecture fails the change without them; leaving it
to Stepan "at the PR" (O1) guarantees a judge_code FAIL.
Rule: For a page with design/pages/<slug>/, the tester procedure has a command that produces every ADR-0006 item 5
artifact, or the gap goes to Stepan as a decision before the coder starts, not at the PR.

### 2026-11-17: A rejected destructive option was voided by one later section, its branches left in the procedure (#150, judge_design round 2, security)
Section 17 declared option B (a tester spec that runs `docker rm -f` and `docker volume rm` during a t31 run) void,
but named only section 15 and step 7b's branch. Section 9 step 6 still opened with "If Stepan chose option B, the
tester writes its scratch spec first", step 7b kept the B branch and a "Neither answered yet" stop that no longer
matches how the decision was taken, and section 10 "What NOT to build" still said option B's scratch spec "is the
tester's". A tester handed section 9 alone reads a live, conditional instruction to write a removing spec.
Rule: When a decision rejects an option with a destructive step, delete every branch, condition and permission of
that option from the procedure and file-list sections in the same round, then grep the option's name and its
destructive verbs (`rm`, `volume rm`, the spec's file name) and leave hits only in a history section.

### 2026-11-17: Decision applied as an appended section, procedure still conditional on it (#150, judge_design round 2, operations)
Same root as the security entry above, seen from the run: besides the option-B opener of step 6 (:377-378) and
section 10's "What NOT to build" (:452), step 6's closing sentence (:402-403) and section 10's test LOC (:440)
still read "unless/if Stepan picks option A", and 7b still opens "as Stepan decides". With A decided, the coder
reading section 10 is told the E-reset spec change is optional, and the tester reading section 9 sees three
branches where one applies.
Rule: After a decision, rewrite the procedure and file-list sections in the decided form (no "if X picks"), and
grep `option [AB]|picks|chose|decides|answered` across them before sending.

### 2026-11-17: Round-2 fix of an exclusive comment wrote a new exclusive claim into the ADR (#150, judge_design round 2, architecture)
Round 1 FAILed "the one writer and the one reader". The fix removed it from the code comment, then wrote into the
ADR-0007 amendment (7.1) and section 1 that `recordLessonStarted` is "the only code that inserts the row".
`test/integration/progress-seed.ts:46` inserts it too, and ADR-0007 item 5 itself says the row is upserted "at the
latest together with the first attempt", which #34's attempt writer will do, so the ADR sentence is false today for
test code and will be false for production after #34. Section 5.1 also left AC16 (both themes, tokens only) out of
the marked ACs and never said whether the reset-done stand-in is a "Design deviation" (ADR-0006 item 5 needs a
DESIGN follow-up for one; #192 is a dev issue), so judge_code has no settled rule to check the PR body against.
Rule: When fixing an exclusivity finding, grep every new "only/one/sole/never" in the ADR text you add against tests,
seeds and the ADR's own future obligations; and when a decision changes the evidence, state in the design whether it
is a Design deviation and which ACs it answers, all of them by number.

### 2026-11-17: Dictated an e2e colour read and a tester grep that were never run (#150, judge_design round 3, operations)
Design 5.1 had E-reset read the destructive button's computed colours right after `page.emulateMedia({ colorScheme })`.
The app switches theme with a `matchMedia` change listener (lib/theme-script.ts) and the button has a 150 ms
`background-color` transition, so in Chromium (Playwright 1.64.1) the read straight after the switch returns the
previous theme's values, and 50 ms later an interpolated `oklab(...)`. The "dark" slot would carry light values and
`design_tokens.py pair` would print a plausible 5.160:1 for the wrong theme. Step 7c also required the full-tree raw
colour grep of tester.md item 7 to be empty with `rg rc=1`; at base it prints 72 lines with rc=0 (issue references like
`#106` and colour literals in tests), so the step fails before any change.
Rule: Before dictating an e2e read of computed style after a theme or media change, read how the app applies the
theme and the element's transition classes, and wait for both; run every pass criterion of the tester procedure at
base before sending.

### 2026-11-17: Dictated a computed-colour read right after emulateMedia, which returns the old theme (#150, judge_design round 3, architecture)
Round 3 added to E-reset: for light then dark, `page.emulateMedia({ colorScheme })`, then read `getComputedStyle`
of the destructive button into `app-destructive-colours.json`. The app's dark class is toggled by a
`matchMedia` change listener (lib/theme-script.ts), which runs on the next rendering frame, not when `emulateMedia`
resolves, and the button has `transition-[background-color] duration-150` (button.tsx:14). On a replica with the same
script and transition, the immediate read gave the light values for "dark" (class still empty), which `pair` accepts,
so the dark contrast would be reported as 5.160:1, the light pair; after waiting for the class only, the background
read `oklab(...)` mid-transition while the text was already dark. Nothing in 7c could tell the first case apart.
Rule: Before dictating a read of computed styles after a theme or media switch, find how the app applies the switch
(listener, class, transition) and wait for the applied state (class on `<html>`, transitions off via
`reducedMotion: "reduce"` or a settled value); give the tester a check that the two theme records differ.

### 2026-11-17: Removed two tester.md item 7 steps from the procedure without saying so in the step (#150, judge_design round 4, operations)
Round 4 dropped the destructive contrast and the raw colour grep from step 7c, which still opens "The rest of
tester.md item 7:". tester.md:132-134 makes both mandatory, so a tester following his role file runs the repo-wide
grep (72 hits at a981bf4) and fails the run, the same failure round 3 named. The deferral to #192 was written only in
5.1 and the AC16 row, not in the step the tester executes.
Rule: When a design drops or replaces a step a role file mandates, the procedure step itself names the role-file line, says it is not run and where it went.

### 2026-11-17: Removed the raw colour grep without a replacement, leaving an ADR-0006 item 5 clause unanswered (#150, judge_design round 4, architecture)
Round 3 failed the repo-wide raw colour grep because it has 72 hits at base. Round 4 (orchestrator decision, applied
as given) dropped every colour check from #150 and "moved" the diff-scoped one to #192, although only #150's tree can
show that #150's lines add no raw colour. 5.1 still quotes ADR-0006 item 5's "an empty raw colour grep" and AC16's
"tokens only" stays in scope with no evidence for it. The contrast clause was answered with "unchanged" and no
number, while `design_tokens.py pair` over the globals.css token values gives both ratios without any capture.
Rule: When a check is removed because it cannot pass as written, replace it with the narrowest form that answers the
same clause on this diff (here a grep over the diff's added lines) and state the residual; never hand a check of this
diff to another issue.

### 2026-11-17: Dictated alias comments state a universal the same design's conversion doc contradicts (#118, judge_design round 1, security)
Design 1.1 dictates over ALIAS_REASON "toJS() throws a ReferenceError ... for an alias with no anchor before it", and
on the `"alias"` member "a ReferenceError, which the library throws for an alias it cannot resolve: no anchor before
it, or past its default alias limit". A few lines further down, the `"conversion"` doc, test Y11 and ADR-0009's
Consequences all say that an unresolved alias used as a YAML 1.1 merge source (`<<: *nope`) throws a plain Error. In
yaml 2.9.1, `merge.js:65-66` calls `Alias.resolve()`, which returns undefined there (`Alias.js:41-71`), and
`merge.js:43-44` then throws `Error('Merge sources must be maps or map aliases')`. Only `Alias.toJSON` (`:77-79`)
throws the ReferenceError. The validator comment the design deletes ("the only shape the library uses for an alias it
cannot resolve") was false for the same reason, and the replacement softens it without making it true. This is the
#121/#156 lesson again.
Rule: Before dictating a comment of the form "the library throws X for Y", grep every code path that reaches Y (here
both callers of `Alias.resolve`) and scope the sentence to the path that throws X, naming the exception.

### 2026-11-17: A "prints nothing" check that greps for the required issue number, and doc absolutes the same doc qualifies (#118, judge_design round 1, architecture)
Design 10 step 4 says `rg -n '#188|until #118|three copies|the fs-free entry point' docs packages apps services` must
print nothing, while 1.3 and 6.2 require "#188" in validate.ts's readYaml doc and twice in ADR-0009 Consequences. The
check can never pass on a faithful build; a coder who trusts it deletes the follow-up references. The pattern was
written for a placeholder, and the placeholder was later replaced by the real number everywhere, the check included.
The same design dictates readYaml's doc "Neither the system error's message ... nor the library's message nor any
file text is printed" and ends that doc with "A conversion failure ... propagates ... as the library's own error",
which content:validate prints (`Error: Merge sources must be maps or map aliases`, pinned by B6/A5). The `"alias"`
member doc says "Carries nothing: the library's message names the alias", but the alias-limit message the same doc
names (`Alias.js:66`) does not.
Rule: After replacing a placeholder, grep every check pattern for it; and read each dictated doc against its own last
sentence and every case it lists before sending.

### 2026-11-17: A "worktree unchanged" guard that cannot see the files the mutations target (#118, judge_design round 1, operations)
Design 7.4's mutate.py proves "WORKTREE UNCHANGED" by hashing `git status --porcelain` plus `git diff HEAD` of the task
worktree. In the tester phase `packages/lesson-schema/src/yaml.ts` and `test/yaml.test.ts` are untracked (A0 expects
`??`), so their content is in neither output: an edit appended to an untracked yaml.ts left the hash identical, while
the same edit to tracked validate.ts changed it. Eight of the nine rows mutate yaml.ts, and the script never refuses
`repo == worktree`. The guard passes exactly where it is needed.
Rule: A no-write guard hashes the bytes of every file the change touches, untracked ones included
(`git ls-files -o --exclude-standard`), refuses a target equal to or inside the protected tree, and is tested once by
planting an edit in an untracked file.

### 2026-11-17: Control procedure expectations not walked against the spec's own lines and the printed format (#197, judge_design, operations)
Design 7.2 for #197 has four defects a line-by-line walk finds. P1 greps the literal `C197 E-layout sizing C197 mount
delayed`, but armControl prints the full title ("E-layout sizing: the terminal fits its frame ..."), so the literal
never matches. P1 also needs `C197 mounted` in run A, where E-layout sizing throws at its first poll about 50 ms
after load and the page closes before the 1500 ms timer. Run B expects a red for the `:97-119` row, but the one-shot
abort is spent on the `:102` document and the `:105` navigations load every chunk, so that test passes. "Plus its
import" in fixtures.ts is unplaced: next to line 1 it fails `git apply --check` on clone B, where the task rewrites
line 1 (checked on a simulated B).
Rule: For every expected line of a control run, write the exact string the code under test prints, walk each judged
test's navigations against the control's trigger (which document it hits), and give every patch hunk an anchor that
both trees share.

### 2026-11-17: Control scope and coverage claimed without reading the runner, and a hedge the design did not apply (#197, judge_design, architecture)
Design 7.2 says "Only lesson.spec runs there" after scoping `test:e2e`, but `isolated-stack.sh:298-321` also runs
`course-unreadable.spec.ts` and `service-down.spec.ts` by `playwright test <file>`, and both call `useOwnBucket`, so the
abort and the 1500 ms mount delay hit them too. It says the control route is registered after the bucket route, but
the anchor (after `bucket += 1;`) puts it before `page.route` at fixtures.ts:32. The note on what the controls cannot
show names only the F6 idle period: the one-shot abort is spent on each test's first document, so no wait after a
later navigation (E-split's six reloads, the F6 test's reload wait, E-live's Actions wait, E-layout sizing's switch
waits) is ever shown red. Section 3 hedges that Next may put a boundary between layout and page, yet E-f6-one-pane
waits only on the brand link while its second F6 needs the page's SHOW_PANE listener (lesson-layout.tsx:108). The
hedge was checkable: Next 16.4.3 adds Suspense only for loading.tsx (layout-router.js:322-345) and Activity only with
cacheComponents (:518), neither used here, so the root hydrates in one commit.
Rule: Before stating what a control run executes, read every stage of the runner script; list for each new guard
whether a control drives it red, and name the ones none does; settle a checkable premise from the installed source
instead of hedging, and apply any hedge you keep to every row it governs.

### 2026-11-17: E-ring left as "native Tab", but the Tab target is set by Radix passive effects (#197, judge_design round 2, architecture)
Design section 4 keeps `lesson.spec.ts:223-262` (E-ring) unchanged as "native hrefs and Tab". Its Tab from the
breadcrumb reaches the theory tab only through Radix RovingFocusGroup: the group root has
`tabIndex: focusableItemsCount === 0 ? -1 : 0` and every item `tabIndex: -1` until `currentTabStopId` is set
(`@radix-ui/react-roving-focus` 1.2.1 `dist/index.mjs:68-100, 147-175`), and items register in a `useEffect` while
`useIsHydrated()` is false (`:151-164`). So between `load` and the passive effects the SSR tab list is out of the tab
order and the Tab lands elsewhere; `toBeFocused` at `:232` cannot recover. That is the same passive-effect window as
the F6 listener the design does wait for. Run A pass 1 shows it: `:223` fails at `:232` with `Received: inactive`.
Rule: For every "no change" row, name what decides where the input lands (DOM attribute from SSR, or state set by an
effect) and check it in the installed library source; a keyboard Tab through a roving-focus widget is not native.

### 2026-11-18: Stale-text grep predicted empty while its pattern hits a true line the design keeps (#188, judge_design round 1, architecture)
Design 6 T7 says `rg -n 'rethrow|...' packages/lesson-schema/src ...` "prints nothing". The pattern `rethrow`
also matches validate.ts:33, the readFailureReason doc "the caller rethrows it", which is true (readText:48 rethrows
an error without an errno code) and which the design leaves unchanged (5.1 replaces only :53-61). So T7 is red on a
correct diff: the tester reports a false failure, or the coder rewrites a true comment to quiet the grep.
Rule: Before writing "prints nothing" for a grep gate, run the pattern on HEAD and account for every hit as either
replaced by the design or excluded by the pattern.

### 2026-11-17: M20's red test watches the fake daemon for a close that an upgraded HTTP socket never emits (#198, judge_design round 1, architecture)
Design 7.2 and section 9 copy 4o's "a framing error closes the attach socket": the fake daemon sends the marker and a
type-3 header, "its server socket sees the close within 1 s". The fake daemon is the `http.createServer` pattern of
`exec.test.ts:104-166`; an http server is `allowHalfOpen: true`, and after the upgrade nothing closes its end. Measured
in the probe clone with the probe `check-process.ts` and the real `DockerEngine`: with the correct handler the client
socket is destroyed, yet the server socket shows only `end` (from the client's half-close after the checks tar, before
the marker was even sent) and no `close` within 1 s, so the row is red on the correct code. The obvious repairs cannot
fail: the server's `end` arrived before the framing error, so a test on `end` is green under M20. The design measured
RC15 and RC16 against the probe but not this row's observable.
Rule: For every "the peer sees X" assertion, run the correct form and the mutant against the fake peer the design
names, and name the event that only the mutated line changes (here: the server writes after the barrier and sees
`close`/EPIPE only when the client destroyed its socket).

### 2026-11-18: Mutation clone procedure written without an install step, and two commands that skip ^build (#137, judge_design round 1, operations)
Design section 6 tells the tester to `git clone --local` the worktree, apply the task diff, mutate and run vitest,
but never says `pnpm install --frozen-lockfile` in that clone (only 7.3 mentions it for the second clone). Run as
written, every row M1-M6 exits 254 with `Command "vitest" not found`: a non-zero exit that reads as "red" for all
six mutations. Section 7 also offers `pnpm --filter @academy/web test` and `pnpm --filter @academy/web typecheck` as
the whole-suite and typecheck commands; neither builds `packages/*/dist` (turbo `^build`), so in a fresh clone they
fail with 12 unresolved-package files and TS2307 for `@academy/db`. They pass in the worktree only because an old
dist happens to match. The M6 row's expected-red list also missed the idle-notifications test.
Rule: Before handing a procedure to the tester, run it once from an empty clone exactly as written, and prefer the
CI command forms (`pnpm test`, `pnpm typecheck`) to package filters that skip the dependency build.

### 2026-11-17: Red/green isolation proved by the branch diff, while PR CI runs on a merge with a moving main (#201, judge_design round 1, architecture)
Design 4 claims "`git diff c4 c5 --stat` shows only ci.yml, so A is the only difference between red and green". CI runs
only on `pull_request` (ci.yml:3-6), which checks out `refs/pull/<n>/merge`, recomputed against main's head at each
push. C-red (push 2) and C-green (push 3) are 20+ minutes apart, and parallel worktree sessions merge into main, so the
two runs can test `merge(main, c4)` and `merge(main', c5)`: a main change to the e2e specs, the workspace service or
ci.yml would then sit between red and green, and the evidence would credit it to A. Same design: the dictated step name
and comment "Interfaces created from here on get no IPv6" are false for interfaces created in new container namespaces
(every container's lo keeps ::1; `net.core.devconf_inherit_init_net=0` resets IPv6 settings in a new netns); `default`
covers the runner's own namespace only.
Rule: A red/green pair on PR CI is isolated only when both runs have the same base SHA; the tester reads it from each
run (checkout log `Merge <head> into <base>`) and the design says what happens when they differ. A dictated comment
about a sysctl names the namespace it applies to.

### 2026-11-17: D-red success line matched reporter-coloured text in Playwright JSON (#201, judge_design round 1, operations)
Design 5.1 decides D-red by "first error message contains `not hydrated (1 matching elements)`" in `e2e.json`. Playwright
1.64.1 starts every worker with `FORCE_COLOR=1` (runner/index.js, WorkerHost), and the JSON reporter keeps the message
as is (`formatError` strips ANSI only from the snippet). `toBe("hydrated")` highlights the changed parts of the received
string, so the message holds `\u001b[7mnot \u001b[27mhydrated\u001b[7m (1 matching elements)...`: the substring never
matches in `errors[].message` or `error.message` (scratch run: raw=false, stripped=true), and the success line can never
print. Same design: "every printed line is fe80 on veth/br" and "timestamps inside the window" were left to reading,
although 4 says every decision is a step conclusion or an exit code.
Rule: Before a design decides on text inside a Playwright JSON report, run one failing scratch test through the same
reporter and matcher and match the stripped message (`/\u001b\[[0-9;]*m/g`); every tester decision gets a command whose
output is the success line.

### 2026-11-17: Round-2 fix gave commands to the two named C-red decisions, not to the rest of the class (#201, judge_design round 2, operations)
Round 1 found two C-red decisions left to reading; round 2 added commands for exactly those two, and section 4 again
says every decision is a step conclusion, an exit code or a command with a success line. Three are still read by eye:
"`head` is the commit pushed for that run" (base step 2, the check that a run tested what was pushed, which the BASE
SAME pairing relies on), "`grep -c '^\['` >= 1 and equal to the N of the scan's first line" (C-red), and
"`git diff c4 c5 --stat` shows only ci.yml" (C-green). Each needs one line of shell that prints a success line.
Rule: When a finding names examples of a class (decisions without a command), fix the class: list every tester
decision in the design and give each one its command and success line before claiming "every decision" in writing.

### 2026-11-17: Dictated guard message says every address line flushes Chromium, against the design's own F3 and R2 (#201, judge_code round 1, architecture)
Design 3.2 dictated the scan failure text "... Chromium flushes its socket pools on each", and the coder printed it
(scripts/netlink-guard.sh:148). R2 says RTM_NEWADDR counts only when the address is new or its ifaddrmsg differs, and
IPv6 temporary addresses are excepted; the design's own F3 row says a pure lifetime refresh "may not flush, deciding that
needs evidence". The guard deliberately fails on a superset, so in exactly the F3 case (an eth0 refresh at 3 AM) the
message tells the reader a flush happened when it may not have. The #121/#156 lesson again, this time in an error text.
Rule: A dictated error message is a factual claim; when the check is a deliberate superset of the harm, the message says
"may" and names the superset, and it is read against every failure-mode row of the same design before judge_design.

### 2026-11-17: Red control by JavaScript off also stops the inline streaming scripts, so streamed boundaries never show (#201, judge_code round 1, architecture)
Design 5.1 counted the three not-found F6 waits and the ordinary-arrival wait as driven red by D-red, on the premise that
not-found reaches the wait through SSR-only asserts. With `javaScriptEnabled: false` the inline `$RC` swap scripts do not
run either, so the not-found boundary stays in a hidden div: the three 404 tests failed at :41 before the wait, and the
ordinary-arrival wait went red with 0 matches instead of 1. The real failure the waits guard (a chunk that fails while
inline scripts run) does not have this effect.
Rule: Before choosing "JavaScript off" as a hydration control, list which targets live inside a streamed boundary
(notFound(), Suspense, async pages) and either pick a control that keeps inline scripts (abort `/_next/static/chunks/**`)
or name those sites as not driven red in the design.

### 2026-11-18: Real-daemon control counted a run green from the JSON report, which vitest writes before the global teardown (#181, judge_design, operations)
Design 7 step 3 judged the 20 I-conc-docker runs by `numPassedTests == 1 && numFailedTests == 0` in each JSON file and
only echoed a non-zero exit code. vitest 5.0.5 runs `_teardownGlobalSetup` in `Vitest.close()` (cli-api chunk, line
13232), after the reporter has written the file. So a run whose `teardownRun` (harness.ts:349-367) found the sentinel
or an owner object missing, or a run cut by `timeout` before teardown, still reads as a pass, and no step checked the
daemon for leftover run-labelled objects after the loop. The brief asked for checked teardown.
Rule: When a control's evidence comes from a test runner's report, check when the runner writes it relative to the
teardown, and make the pass criterion include the exit code and a post-run listing of the objects the run may leave.

### 2026-11-18: A "no new test, same outcome as today" failure row was wrong about what the new re-create does (#181, judge_design, architecture)
Design 4 row F8 said a re-create that succeeds after another process removed the container gives "the same outcome as
the caller's retry of the ensure". It does not. The retry runs `ensureVolume` first. The re-create in the adopt loop
does not, and the container body mounts the volume by name with no `VolumeOptions.Labels` (`spec.ts:104-110`). So if
the other process's `DELETE` (`runtime.ts:165-172`, container then volume) removed the volume too, Docker creates an
unlabelled volume during our create. Every later ensure of that key then fails `ensureVolume` with
`WorkspaceIdentityMismatchError` until someone removes the volume by hand. Today the same race exists only in the
milliseconds between `ensureVolume` and the first create, and the adopt path ends in `ContainerNameUnresolvedError`, a
clean retry. The re-create keeps that window open for up to 5 s.
Rule: When a design adds a retry of a write, list what the caller ran before the original write (ensures, checks) and
say for each one whether the retry still holds it. A row that says "same as today" has to name the call path it is
compared with.

### 2026-11-18: The recorded residual window was sized as "a few milliseconds"; it lasts until the daemon mounts the volume (#181, judge_design round 2, architecture)
Rev 2 records the remaining F8 race in the ADR-0010 consequence bullet as "the few milliseconds between the two
calls" (ensureVolume, then the container create), and F8, K8 and Q4 say the same. A remove can delete the volume until
the daemon takes its reference on it, and that happens inside our create at `setHostConfig` (moby v28.0.4
`daemon/create.go:203` -> `registerMountPoints`, `daemon/volumes.go:213-221`, `WithCreateReference`), after
`newContainer` (:166) and `CreateLayer` (:189). Before the reference, `VolumeStore.Remove` (`volume/service/store.go:809`
`hasRef`) lets the remove through. `CreateLayer` is the slow part of a create under load, the very duration #181 measured
beyond 375 ms. So the window is the create's pre-mount time, not milliseconds, and the ADR would record it too small.
The design's own F8 cites `create.go:203` and the findings cite `:189` before it. (Round 1's architecture finding said
"milliseconds" too; it was wrong in the same way.)
Rule: When a design records a residual race window in an ADR, end it at the point the other side can no longer act
(here: the daemon's volume reference), read the daemon code up to that point, and state its length in the terms of the
slow steps on that path.

### 2026-11-18: Test plan retagged a shared image name to fake a leftover the shim could fake (#176, judge_design round 1, security)
Design 5 T2 ran `docker tag node:22.23.4-alpine academy-web:t31` and later `docker image rm academy-web:t31`, gated only
by the T0.2 check run before pnpm install and T1. `docker tag` moves an existing tag without error, so a `:t31` image
another session built in the meantime would lose its tag, and the step 4 "only Untagged" check cannot see that. The
shim already refuses that `image rm`, so the real tag adds no coverage: the listing is the only thing it feeds.
Rule: A test plan fakes a state in the shim it already has before it writes to Docker. A write that is still needed
names an object the run created and checks right before the write that the name is free.

### 2026-11-18: Test plan prescribed a counter reset the orchestrator's dry-run could not run (#176, judge_design round 1, operations)
Design 5 T0.6 resets the shim counters with `rm -rf "$S/state" "$S/calls.log"; mkdir -p "$S/state"`. In the
orchestrator's dry-run the Claude Code safety check refused that `rm -rf` on a variable path, and the run went on with
per-run dirs plus `ln -sfn`, which the design does not describe. A tester who improvises the reset can leave a real
`$S/state` directory, where `ln -sfn` puts the link inside it and old counters carry over, so T1a stops at
`STOP preflight listing failed` before the trap and T2 loses its preflight bypass. Each run's `calls.log` is also
overwritten by the next one, so the `image rm` count cannot be checked afterwards.
Rule: Each step of a test plan is run once as written before the design goes out, and any state reset uses per-run
directories (no `rm -rf` on a variable path) with a check that the reset worked before the run starts.

### 2026-11-18: T3 recovery triggered by a later listing, not by the run's own evidence (#176, judge_design round 2, security)
Revision 2 T3 step 5 runs `compose -p academy-t31 down --remove-orphans` and `image rm` of the `:t31` refs when "a
`left behind` line, or the T0.2 listings print something". The second trigger fires on objects T3 never created: if
another session (another worktree runs the same script with t31) starts between step 2 and T3's preflight, T3 prints
`T31 STOP leftovers of academy-t31 exist`, creates nothing, and the recovery then tears down that session's stack and
images. The same holds when such a session starts after T3's own `RESULT OK` and before the post-run listings. T3 also
has no exit-point rule for the preflight STOP lines that T1/T2 have.
Rule: A recovery step removes only what the run's own log proves the run created and left (here: teardown ran, no
preflight STOP, a `left behind` line); objects a later listing shows without that evidence are reported, never removed.

### 2026-11-18: Revision 2 named per-run dirs that already exist under the scratch root (#176, judge_design round 2, operations)
Revision 2 T0.6 says each run gets "a name not used before (T1a, T1b, T1c, T1d, T2, T2b)", but `$S/T1b` and `$S/T1d`
already exist with filled `state/` from the orchestrator's round-1 dry-run. At T1b the reset chain stops at `mkdir`,
`$S/state` still points at T1a's counters, the emptiness check fails and the tester stops. Fail-closed, but the plan
is not executable as written. The T3 recovery also re-checks only the four T0.2 listings, which omit the
`academy.workspace.instance=t31` ps/volume/network listings the script's preflight (:64-73) checks, so a leftover probe
workspace (`api ensure`, :373) survives `compose down` and the recovery reads clean while the next run STOPs.
Rule: Before naming run directories, `ls` the scratch root and pick names that are absent; a recovery's closing check
lists everything the script's own preflight lists.

### 2026-11-21: Course id boundary rule scoped to "a URL's course id" while server actions take it as an argument (#219, judge_design round 1, security)
The #219 ADR-0009 amendment (plans/219-design.md:184-186) checks the id form and looks the id up among listed names
only for "a URL's course id", and says a lesson page's server actions read "the URL's course" (:182). The lesson
actions take `courseId: unknown` from the browser (`apps/web/app/(app)/courses/[courseId]/lessons/[lessonId]/actions.ts:35-89`,
`lib/workspace/environment.ts:98-108`), independent of the page URL, and the not-found page's course id comes from a
mechanism #220 has not chosen yet. A faithful #220 could read the action argument into a per-course read with no form
check, leaving only the fs layer's real-path check between browser input and a joined path.
Rule: A rule about untrusted input names every way the value enters (route params, server action arguments, headers,
API path params) and puts the check in the one function that turns the value into a read, so no caller can skip it.

### 2026-11-21: ADR text justified a decision with a "required" CI job that GitHub does not enforce (#219, judge_design round 1, operations)
The #219 amendment (plans/219-design.md:163-164, also alternative 1 at :35-36) keeps the export failing the image
build on one broken course because "a failing course reaches main only past the required `content:validate` job".
`gh api repos/valmlord/academy/branches/main/protection` answers 404 "Branch not protected" and `.../rulesets` is
`[]`: no job is required, and the 2026-10-28 (#23) entry already recorded this. The real guards are the `content`
job and the `e2e` job's `docker compose up -d --build` both going red, plus the process rule that a PR merges only
on green CI. The same design accepted "a renamed course directory orphans progress, nothing checks this" although
the startup recompute already reads every progress row and folds unknown-course rows into one generic `skipped`
count, so one log line per unknown course id would tell the operator, and renaming back is a recovery the text
never states.
Rule: Every enforcement word in ADR text ("required", "blocked", "only past") is backed by a quoted API or file
answer in the design; a silent data-orphaning residual names the log line that reveals it and the recovery step.

### 2026-11-21: Amendment replaced a sentence by ordinal alone, with two counting conventions in one entry (#219, judge_design round 1, architecture)
The #219 amendment (plans/219-design.md:165) says "Item 2's first sentence reads ..." without quoting the sentence it
replaces, and section 6 does not list it among the byte-for-byte quote checks. The same entry calls item 1's "The web
server reads ..." its "second sentence" (:157), counting the bold title "Runtime reads of an allowlisted copy." as
sentence one, but calls item 7's "An unreadable or invalid ..." its "first sentence" (:146), not counting "Failures.".
By the item 1 convention, item 2's first sentence is the title "The allowlist, by structure.", so the replacement
target is ambiguous in an ADR whose original text stays and whose amendment "wins once accepted".
Rule: An amendment that replaces text quotes every replaced sentence whole, never an ordinal alone, and the coder's
quote check lists every replacement in the entry, counted against the entry's replacement bullets.

### 2026-11-21: Class sweep named three operator signals, the test list covered only some of them (#219, judge_design round 2, operations)
Revision 2 of the #219 design (plans/219-design.md:63-65) lists the signals for a failing course and a root failure:
the web request log line (item 7, now naming the course id), the recompute line and the reconcile line, each also
naming the root on a root failure. The #220 test list (:408-425) asserts the recompute line for failing course B,
the unknown-course line and placeholder, and the reconcile line naming a failing course, but nothing for item 7's
web line (`apps/web/lib/course/server.ts:18`, no test matches `course read failed` today) and nothing for any of the
three root-failure lines, whose meaning #220 changes (a missing `course.yaml` is no longer a root failure). A signal
with no test can lose its course id in #220 and every judge would still pass.
Rule: When a design names log lines as the mitigation for an invisible state, the follow-up test list has one
assertion per named line and per variant (course failure, root failure), counted against the sweep.

### 2026-11-21: Guarded a dialog test on the owner's stack by one identifier, and closed a fetch list with no check (#206, judge_design round 1, security)
Design D1 put a test that opens the reset dialog outside the DESTRUCTIVE_E2E gate, so it runs on Stepan's plain
`pnpm test:e2e` against his real firstLesson workspace. The only "never press Сбросить" check was
`rg resetConfirmLabel`, a form check: `dialog.getByRole("button").last().click()`, a `/Сбросить/` name regex or an
Enter after a focus move all pass it and reset his folder. The same test plan said the builds "may fetch exactly"
two images, "nothing else", but its read script keeps only turbo-prefixed lines, so no command ever looks at a build
line, and section 4.2 claimed "nothing touches any object this run did not create" while both Dockerfiles write the
shared `id=pnpm` BuildKit cache mount and `pnpm install` in W and C writes the host pnpm store.
Rule: A safety property of a test that runs on the owner's stack is checked by its effect (list every interaction
call in the test and its helpers, the set must equal the prescribed one), never by grepping one name; every closed
"only X" list in a test plan has a command whose output decides it; an absolute "touches nothing it did not create"
names each shared write (cache mounts, package stores) as an explicit exception or is not written.

### 2026-11-21: Red-set prediction ignored Playwright project dependencies (#206, judge_design round 1, architecture)
Design 4.4 predicted for R "skipped + did not run = B" and for N two failed tests (E-live-reset and E-reset-cancel), and
D1 said a failure in lesson.spec "fails only this test". playwright.config.ts:107-112 makes `terminal` depend on
`chromium`, and Playwright 1.64.1 runs a project only when every dependency project passed (runner/index.js:6757-6759,
6773-6775). So one red chromium test turns the whole terminal and terminal-webkit projects into "did not run":
E-reset-cancel never runs in N, and both R and N would read NOT AS EXPECTED and stop the tester on a correct product.
Rule: Before predicting a red set, read the runner config's project graph (dependencies, serial mode, shards) and the
runner's rule for dependents of a failed project; list every test that the failure stops from running.

### 2026-11-21: Error-block anchor matched by the test's own title, and a wait with no command (#206, judge_design round 1, operations)
Design 4.4 R checks that E-live-reset's error block has "a line containing `under the reset dialog` and not `notices
shown`". The block starts with the failure header, and the test title "...stay announced under the reset dialog
(AC51)" is in it, so the header alone meets the check when the second read fails (scratch spec, Playwright 1.64.1:
header line plus `Error: under the reset dialog, notices shown`). The check cannot tell the first read from the second,
and 4.6 claims it does. The same read filters the log down to turbo-prefixed lines before it extracts the `T32` lines,
which carry no prefix, and the 60-minute hang limit gives no command that waits. The project-dependency part of the
red sets is the architecture entry above, found in the same round.
Rule: A log anchor that tells two failures apart matches the full message line (`^ *Error: <message>$`), is checked
against the test title and header, and is run once on a scratch failure of each kind. A read names which stream each
item comes from, and a time limit on a background run comes with the literal bounded wait command.

### 2026-11-21: Self-test expectations named a subset of items, and one of them wrongly (#206, judge_design round 2, operations)
Design r2 4.8 says K1 read in mode R gives "C6 OK and C7R OK (C1, C2, C3 BAD)". The read's C1 takes K1's own rc file,
which holds `rc=1` (K1 fails on purpose), and mode R expects `rc=1`, so C1 is OK, not BAD; C4 (passed 0, not Pc-1, no
`did not run` line) and C5 (setup+chromium line count) are BAD and not listed. X3, X5, X6 and X8 also turn further
items BAD (X5 changes a ✓, so C4's passed-equals-✓ count breaks too) while 4.8 allows other BAD items only "where
listed". 4.8 then says a self-test that comes out otherwise stops the tester before R, so a correct read stops the
run. The same section asks for one Bash call per poll of up to 540 s without naming the call's timeout; the tool's
default is 120 s.
Rule: For each read self-test, write the full expected vector (every item OK or BAD) derived from the doctored input
and the rc file actually passed, or state that only the named items are judged; a poll prescribed as one tool call
names the call's timeout, above the loop's own bound.

### 2026-11-21: One doctored self-test input with no before/after check, while the design claims all have one (#206, judge_design round 3, operations)
Design r3 4.8 X7 builds `206-x7.log` by appending a line to G's log and states C2 OK because "the last T32 line is
still `T32 RESULT OK`", but X7 has no precondition before or after the edit: nothing checks that G's log ends in a
newline (otherwise the line joins `T32 RESULT OK`, C2 turns BAD and a correct read stops the run), that `alpine:3.20`
is absent from G's log and present once in the copy, or that the `^T32 ` lines are the same in both. X5s, X10 and K4d
each have both checks, and F16 says "preconditions on every doctored edit", so the claim is false for X7.
Rule: Every doctored input, an append included, gets a command before the edit and one after it that prove exactly
the change the expected vector assumes; list the doctored inputs and tick each one off before claiming "every".

### 2026-11-21: Dropped the only self-test of a check moved into C5, while C5's clause is the sole guard (#206, judge_design round 3, architecture)
Design r3 drops C6 and X6 and says a second failed test in R or N "is a second ✘ result line, which C5's exactly one ✘
reads BAD". No kept self-test makes C5 BAD through that clause: X9 is BAD on "terminal lines, no ✘", K2-R and X10 on
"count 1, no E-live line". A C5 without the "exactly one ✘" and "E-live ✓" clauses prints the same vectors, passes every
self-test, and reads an R or N log with a red E-live, or any second red chromium test (F11), as AS EXPECTED; C1, C2,
C7R and C8 are the same in that log. 4.8's own rule ("a self-test exists where a wrong read could report OK on a red
result and no other kept check would catch it") keeps exactly this case, as it kept X5s for the skip.
Rule: When a scope cut moves a guard from a dropped check into a clause of a kept one, find a kept self-test whose
expected BAD comes only from that clause; if none, add one, and list which clause each kept self-test's BAD isolates.

### 2026-11-21: Fetch list command omits the resolve and FROM line forms tester.md names (#206, judge_design round 4, operations)
Design r4 4.2 says the image fetch list is closed per tester.md:60-70, but its grep keeps only `load metadata for`,
`Pulling from`, `[auth]`, `naming to` and `unpacking to`. tester.md defines the closed build case by every resolve,
metadata, fetch, auth/pull-token or `FROM` line. On two real isolated-stack logs (#216, 2026-11-21) the
`docker/dockerfile:1` frontend shows up only as `resolve image config for docker-image://docker.io/docker/dockerfile:1`,
which the command never prints, while the allowed `load metadata for docker.io/docker/dockerfile:1` never appears.
So the one fetch the list allows for the frontend is never observed, and a different frontend or base would not be
either.
Rule: Before closing a fetch list with a grep, run that grep on a real build log from the same recipe and check that
every line form the governing rule names (resolve, metadata, auth, FROM, naming, unpacking) is in the pattern and
each allowed entry actually appears in the output.

### 2026-11-21: Bounded leftover slot-uid processes by "the next start kills them", against a same-uid killer (#199, judge_design round 1, security)
The #199 rebuild says the slot's next start is the backstop for a failed cleanup, that "two checks never share a uid",
and in ADR-0002 item 12 "Cleanup" and S199-10 that leftovers live "until the slot's next start". The cleanup and the
setup are themselves processes of the slot uid, and residual (1) puts learner code under that uid. A learner process
that loops `kill -9 -1` kills the cleanup and every later setup before their own kill line (exit 137, uncounted
not-started), so it runs until the container stops; `kill -STOP` turns the cleanup into `timed-out`. The 137 row named
only the OOM killer and a container stop. The #163 round-2 entry had already made the prelude kill the guarantee
against a leftover reaching the next check's `checks/`.
Rule: For every guarantee that rests on one process of uid U killing all others of U, list the processes of U the
adversary controls, ask what they do if they act first (kill, stop, ptrace), and state the bound that holds then.

### 2026-11-21: Mutation rows whose named assertion cannot go red, and fake-clock rows shipped with no negative run (#199, judge_design round 1, architecture)
The #199 rebuild maps every mutant to "the exact test and assertion that goes red" and procedure 21 rejects a red at
any other assertion, yet two rows fail that on paper. RC9b's named "settle(250): 1" stays 1 under a 100 ms period,
because the design's own settle model schedules the next poll only after the inspect crosses the socket in the real
barrier; the difference appears one step later, at an assertion with no message (the round-13 RC9 class again).
I-c13 asserts setup `not-started` before "exitStatus 123", so under M26 (plain `cd`) the setup starts and the
unnamed first assertion fails before the named one runs. The design handed every RC negative run to the coder
instead of running them, and stated "a container stop gives exit 137 `killed`" without a measurement, although Docker
unregisters a container's execs when it exits, so the inspect answers 404.
Rule: For each mutation row, walk the test's assertions in order under the mutant and confirm the first failing one
is the named one; run every fake-clock row against its mutant before the design ships, not after.

### 2026-11-21: Procedure 21 compared Docker objects of other sessions, and four mutation rows could not be decided as written (#199, judge_design round 1, operations)
The #199 rebuild of procedure 21 lists every `academy.workspace.test-run` object and every managed container. It then
requires "equals before" and "managed containers show only instance `local`". On the shared daemon the before-listing
already held another session's `wks-t31-*` container, and that container vanished during the rehearsal with no action
of the run. Step 8 was false before anything ran. The same design had more steps that do not hold:
- M26's red test asserts setup `not-started` before the named "exitStatus 123", so the mutant goes red at the wrong
  assertion.
- Ten RC rows name no assertion message for the FAILLINE rule.
- `-t '<name>'` breaks on I-c4's apostrophe.
- Q5 needs `terminate` before the coder wrote it.
Rule: A procedure's Docker checks compare only objects carrying the run's own id (the printed `run <id>`, instance
`t<id>-*`). For every mutation row, walk the red test's assertions in order under the mutant and confirm that the first
one to fail carries the row's message. Run every dictated command once with the real names in it.

### 2026-11-21: Rev 2 Done gate fails on main, and the slot-trust cost omits the restart trigger (#199, judge_design round 2, operations)
The #230 Done line runs `rg '\p{Cyrillic}'` over the five ADR files whole. On main before #230 changes anything, it
prints 13 lines of quoted UI strings (ADR-0007, 0010, 0011), so the gate can pass only if accepted product text is
deleted. The #230 issue body also kept an older Done line than the design's. Separately, the slot-trust "cost"
paragraph names only results other than `clean` and calls them rare. By the same rule, every service restart makes
the first check in each adopted workspace fail uncounted and stop the container, which ends the terminal. That
trigger is routine (every deploy), and Stepan accepts the rule without it being stated.
Rule: Run every dictated gate on today's main before sending it. A gate that is not red on main by design checks
added lines only (`git diff -U0 main | rg '^\+'`). When a rule's cost is stated for Stepan, walk every trigger of the
rule, including service restart and deploy, and name the most frequent one.

### 2026-11-21: The #230 Done block renders as other commands, and option B leaves the trust read unlocked (#199, judge_design round 3, operations)
The block the orchestrator pastes into #230 puts the gate commands on indented plain lines with no code fence. GitHub
renders them as Markdown, so `\+`, `\(` and `\)` lose their backslashes and `<n>` is dropped. The rendered H4 regex
`follow-up\s+issue)` is an rg parse error, `|| true` hides it, and H4 prints FOLLOWUP-OK with the placeholder still in
the file. Separately, ADR-0010 item 14 does not say that a run request reads the start record under the workspace lock.
Under option B, two checks of one attempt after a restart can each restart the container, and the second restart ends
the first check with `service-stop`. 9.2.1 then states B's cost for a one-check attempt only.
Rule: Text meant for an issue or PR body puts every command in a code fence and is checked with `gh api markdown`
before it is pasted. A contract rule that decides on in-memory state says the state is read after the lock is taken,
and its cost is walked with concurrent requests.

### 2026-11-21: V2 locked the trust read of run requests only, and asked a non-reentrant lock to be taken twice (#199, judge_design round 4, architecture)
Revision 4 made a run request read the start record after taking the workspace lock. The other stopper in the same
ADR-0010 item 14 paragraph, the stop after a cleanup result other than `clean`, still queues on the FIFO lock and
stops unconditionally. Behind a `PUT W` (the learner's restart from the menu) or, under option B, behind a run request
that already stopped, started and recorded, it stops the fresh trusted container and ends that check `service-stop`.
Separately, item 14 says the run request holds the lock through the stop and start, while item 8 and 9.2.1 say the
stop and start take the lock "as `POST W/stop` and the start path do". `KeyedMutex` is not reentrant: a nested
`mutex.run` on the same key waits for the task that awaits it, and the workspace hangs until restart.
Rule: When a lock rule is added for one actor, list every actor that reads or acts on the same state and give each the
read-after-lock rule; when a rule says "hold the lock across X", read the lock's code and say how X runs inside that
hold (no second acquisition of a non-reentrant lock).

### 2026-11-21: V2's lock hold, implemented through the manager, hangs the workspace and stops every idle stop (#199, judge_design round 4, operations)
The same V2 text as the architecture entry above, seen for its blast radius. Following item 8 ("take it as `POST W/stop`
and the start path do") and 9.2.1 ("the same path that starts a workspace today") inside the hold item 14 asks for
means `manager.stop` or `manager.ensure` inside `mutex.run` on the same key. Measured with a copy of `KeyedMutex`: the
nested task never settles. Every later request on that workspace then queues forever, and since `every` (main.ts)
skips a tick while the previous sweep runs, no workspace is idle-stopped again until the service restarts.
Rule: For a lock rule in a contract, name the call path that runs inside the hold and state its failure on the real
lock implementation; say what is called directly so that nothing takes the lock twice.

### 2026-11-21: The #196 lock obligation banned a call shape, not the hang, and kept an option-B clause for both options (#199, judge_design round 5, operations)
Constraint (i) says nothing calls `mutex.run` on a key it already holds. A run request that holds the lock and awaits a
stop the cleanup path queued on the same key meets that wording and still hangs (measured). The reach sentence named
one workspace and left out the idle sweep, which stalls for every workspace. Test 2 of the same paragraph says "under
option B", and the paragraph is kept whichever option lands, against 9.2's "drop the other option's sentences".
Rule: A constraint written to prevent a failure states the failure's condition (hold and wait on the same lock) and its
whole reach, not the one call that showed it; text kept for every option names no option.

### 2026-11-21: Dictated a component comment that its own failure-mode table contradicts (#216, judge_design round 1, architecture)
Design 1.1 dictates for `scrollable-code.tsx` "Pane split, one-pane switch, window width, zoom and text size all change
the pre's box". The one-pane switch does not: below 64rem both panes share one grid area of `main.lesson-layout`
(no padding), and the hidden pane is `position:absolute; inset:0` of the same box, so the `pre`'s width is the same
shown and hidden; F6 of the same design says exactly that. Zoom also leaves the box in CSS px unchanged while the
`.prose` 70ch cap holds. The coder would copy a false comment (the #121 and #156 lesson again).
Rule: Before dictating a "these all do X" comment, check each listed case against the CSS that sizes the element and
against the design's own failure-mode rows; state the cases where X does not happen and why the result is still right.

### 2026-11-21: "Same width shown and hidden" stated from the tall-viewport grid only (#216, judge_design round 2, architecture)
Round 2 put "the `pre`'s width is therefore the same shown and hidden" into "Verified" and F6, and took the judge's
comment "a one-pane switch ... changes neither the box nor the overflow" into 1.1. At viewport height <= 30rem
(`globals.css:405-408`, rows `auto auto`) the shown lesson pane grows to its content and the document scrolls, while
the hidden pane is `inset:0` of `main` and its `ScrollArea` (`overflow-auto`, `page.tsx:150`) overflows vertically;
with classic scrollbars, which AC75 itself was measured with, the scrollbar narrows the `pre`. The observer still
catches it, so only the dictated text is false; the round-1 wording came from the judge, the "Verified" line and F6
are the architect's.
Rule: A "same box in both states" claim is checked against every media block of the layout (height queries too) and
against classic scrollbars of every scroll container between the element and the grid, before it is written as
verified.

### 2026-11-21: "Their assertions do not change" for a fixture swap that leaks into a later loop iteration (#135, judge_design round 1, architecture)
Design 8.3 replaces every `write(\`${L}/quiz.yaml\`, "q: 1\n")` with a helper that also writes task.md with the
`` **`q`** (квиз): ... `` sentence, and says the assertions of the three affected tests stay. In
`caps the limit of ready quiz and bug-hunt checks at 3` (validate.test.ts:309-326) the fixture is written once before
a loop whose second iteration replaces the checks with a bug-hunt check only and expects `[]`; the task.md sentence
then names "q", which is no quiz check of that lesson, so the new check reports T5 and the test goes red with the
design followed exactly.
Rule: When a fixture change adds a file that a new check reads, trace every test that writes it through each
`withChecks`/loop iteration after the write, and run the old assertions against the new rules before saying they hold.

### 2026-11-21: Merge-order rule without a fetch, ADR text narrower than the code, a miscounted restore criterion (#135, judge_design round 1, operations)
Design section 6 makes `git merge-base --is-ancestor origin/main HEAD` the merge gate for content PRs with no
`git fetch` before it, while main is unprotected (branch protection 404, `allow_update_branch` false), so the check
can pass against a stale ref and nothing else enforces it; the design also does not say where the rule is written
for whoever merges. Section 7's ADR paragraph lists the count markers as "N верных", "N из M" or a percentage and
the restatement as "Квиз: не меньше K из Q", while 3.3 also triggers on "N правильн..." and accepts
"не меньше K верных из Q"; T3 points authors to ADR-0001 item 8 although the form is defined in the amended item 6.
14(d) decides the restore by "the three RESTORED lines" for four mutants (M1, M2, M2b, M3).
Rule: A merge-order rule fetches the ref it compares and names the place it is recorded; ADR text that defines what
a check matches is checked phrase by phrase against the regexes; every counted pass criterion is recounted against
the list it counts.

### 2026-11-21: Prototype run reinstalled the worktree's lesson-schema node_modules; ADR "one word" wider than the code (#135, judge_design round 2, operations)
The r6 mutant run called `pnpm exec vitest` in the scratch prototype, a package outside the workspace whose
node_modules is a symlink to the worktree's `packages/lesson-schema/node_modules`. pnpm's pre-run dependency check
ran a fresh install without the lockfile (`r6/m-before.out`: "Packages are cloned...", `+ vitest 5.1.1`), which
replaced the worktree's tree: `.bin/vitest` is now 5.1.1 while pnpm-lock.yaml pins 5.0.5 (vite 8.3.8 for 8.3.5).
The design still says the prototype ran on 5.0.5, offers `git status` as the proof that nothing outside the
scratchpad changed (git does not see node_modules), and the tester precondition only installs when
`$W/node_modules` is missing, so the coder and tester would run a vitest that CI does not. Separately, amended
item 6 defines a count as "N <one word> из M" while the code accepts only `[а-яё-]+`, so
"Квиз: не меньше 5 tasks из 6." is skipped although the ADR says it is reported; the sweep row calls it "exact".
Rule: A prototype never shares a node_modules with the worktree through a symlink and never runs `pnpm exec`/`pnpm
run` outside the workspace; side effects are proven on node_modules too (`vitest --version` against the lockfile),
not only by `git status`. An ADR phrase that names a character class says the class the regex uses.

### 2026-11-21: ADR clause (e) keeps mid-paragraph terminators; PR comment addresses the author under his own name (#135, judge_design round 3, operations)
Amended item 6 (e) says the paragraph "is split after every `.`, `!` or `?` that is followed by whitespace, and one
`.`, `!` or `?` that ends the paragraph is dropped". Section 3.2 and the code also drop the inner terminator and the
whitespace after it; the clause does not. Read literally with (i) and (j), "... нужно 4 верных." keeps its dot and
" Квиз: не меньше 5 из 6" starts with a space, so neither grammar matches (measured, `jops3/adr-literal.mjs`): the
own sentence of 17 of 18 quiz lessons and every mid-paragraph restatement would be "in neither form" and reported
under (l), while the code reads them. The 7a row (e) is "exact" because its expectations came from the code's
output, not from the clause. (i) "the id part of (g)" also leaves open whether ` (квиз):` belongs to it. Separately,
the section 6 PR comment is posted through gh as valmlord, Stepan's own account, and says "Stepan, ... since you
merge everything here": under the author's name it reads as the author writing to himself (human-text.md), and it
repeats the PR body's "Merge order" section; "minus #135 itself" names the issue number, not the PR's.
Rule: Measure each ADR clause by implementing the clause's literal reading, not by comparing fixture output with
the code; text posted under the author's account is written in his voice and never addresses him.

### 2026-11-21: ADR item 6 (d)/(e) leave out the trimming and the terminator drop the code does (#135, judge_design round 3, architecture)
Read literally, amended item 6 trims only the lines that (d) joins to a paragraph, and (e) splits "after" a
terminator without dropping it or the whitespace after it. The reader trims every line outside a fence (the
first line of a paragraph and every block-start line too) and drops the inner terminator with the whitespace.
So under the clauses, `- Квиз: не меньше 5 из 6   ` (trailing spaces, also a Markdown hard break "  " before
a wrapped continuation), `Квиз пройден. Квиз: не меньше 5 из 6.` (fixture e2-dot) and the own sentence of 17
of 18 quiz lessons are "in neither form" and reported under (l), while the code reads all of them
(measured, `jarch3/bin/trail.ts`). Section 7a marks (d) and (e) "exact" because the expected column is the
code's output, the same method revision 3 says it removed. Also (i) "the id part of (g)" does not say
whether ` (квиз):` belongs to it.
Rule: Each ADR clause that describes text processing names every transformation the code applies (trim,
drop, normalise) at every place it applies, and is checked by an implementation of the clause's literal
reading run over table C, not by the code's output.

### 2026-11-21: Revision-4 ADR item 6 still calls 13 of 18 own sentences "not in the first form" (#135, judge_design round 4, operations)
The amended paragraph (design section 7) gives the own-sentence form as `` `<id>` (квиз): Q вопросов, нужно K верных. `` and then says a sentence that begins with `` `<id>` (квиз): `` "but is not in the first form" is reported. 13 of the 18 course sentences are not in that form literally ("вопросов-сценариев", "нужно не меньше 5 верных", words before "нужно") and the code reads them with 0 issues (run on a prototype copy: `` `closed-environments-quiz` (квиз): 6 вопросов-сценариев, нужно не меньше 5 верных. `` and "... 6 вопросов про всё подряд, нужно 5 верных." give 0 issues). The next bullet, "Counts written another way are not recognised, and their sentences pass unchecked", is false for anchor-led sentences: "`closed-environments-quiz` (квиз): шесть вопросов, нужно пять верных." and "..., нужно 5/6." are reported (T4). Section 7a ran only examples that agree with each sentence, never the course's own variants A, C, D against the sentence that says what is reported.
Rule: For every ADR sentence that says what is reported or what passes, run the course's own variants and the other bullets' examples against it, not only the sentence's own examples.

### 2026-11-24: Issue text made the source of a file path with no form check (#221, judge_design round 1, security)
plans/221-course-reference.md Q1 makes "the `<course-id>` of the "Module / lesson" path in its issue" the course
of a task and builds `docs/courses/<course-id>/reference.md` from it. valmlord/academy is public and the
module.yml form is open to any GitHub account, so that field is untrusted text, and it now reaches roles that have
Bash (content-researcher, practice-designer, student). The design states no form for the value (one path segment,
an existing directory directly under `course/`, ADR-0009 item 6), no "ask on mismatch", and no rule that the value
is data and never pasted into a shell command. F3 even says the orchestrator's prompt carries the path, which
contradicts Q1 naming the issue as the source.
Rule: When a design turns issue or other untrusted text into a path or argument an agent uses, name one source,
state the accepted form and the existence check, say what the role does on anything else (stop and ask), and
forbid interpolating it into a shell command.

### 2026-11-24: Tester grep could not see .claude/, and a count check could not fail (#221, judge_design round 1, operations)
T1 of the #221 tester plan ran `grep -rn ... .` from the product worktree root and expected the one historical
`./.claude/feedback/...` line. In an agent's Bash `grep` is a shell function that runs ugrep with `--ignore-files`,
and the product `.gitignore` ignores `/.claude/`, so every process-repo hit (CLAUDE.md, the content briefs) is
silently dropped: the check meant to catch stale pointers in the process repo saw none of it. T2 also expected
"at least 1" `_contract.md` per brief, but each brief already names `_contract.md` once in its load list, so the
check passed before any edit.
Rule: A tester grep across both repos uses `command grep` (or `git grep` per repo), and every expected count is
checked against the current tree first: if the unchanged tree already meets it, the check cannot fail.

### 2026-11-24: #220 design obliges #241 to add the stub course #241 ruled out, and claims the proxy matcher covers every app path (#220, judge_design round 1, security)
`plans/220-design.md:213` ("the content team adds the #217 stub only with #241") and `:319` ("the stub course added
together with it") hand #241 a second course in `course/`, while #241's own text decides the two-course e2e runs
against a fixture root "not a stub course in `course/`, so the learner never sees a test course". #220 is not the
owner of that choice. `:139` says the matcher `proxy.ts:36` "already covers every app path"; the negative lookahead
`(?!_next/static|_next/image|favicon.ico)` is unanchored, so `/favicon.ico/courses/...`, `/_next/staticX/...` and
`/_next/imageX/...` reach the `[...missing]` catch-all with no proxy run, and a client-sent `x-academy-pathname`
arrives at `not-found.tsx` untouched. The read function bounds the harm, but the boundary claim was wrong and no
test pins the unproxied case.
Rule: An obligation handed to another issue is checked against that issue's decided text before it is written; a
claim that a guard covers "every" path is checked against the guard's actual pattern, with the paths it lets through
named in the failure modes.

### 2026-11-24: #220 seam drops a top-bar link the design says it keeps, and leaves a seam result undefined (#220, judge_design round 1, architecture)
`plans/220-design.md:122` sets the layout's `courseId` to undefined for every failure, while today
`layout.tsx:20` passes `error.courseId`, set once `course.yaml` parsed (`read.ts:111,116`): a course whose
`module.yaml` or `lesson.yaml` fails loses its "Курс" link in #220, yet `:268` says "No page ... change beyond
A218-12's action rule; `TopBar` keeps `courseId`". The change was forced by `CourseReadError.courseId` becoming the
directory name (always known), which the design noticed for L1 (`:37`) but did not follow to the case it now
changes. `firstReadableCourse` (`:100-102`) returns the first `course`, else "the first failure", but a root whose
listed names are all non-slugs gives `courseById` only `not-found` (form check first), so there is no failure to
return and the typed `CourseRead` result is undefined; T8 does not cover it, and `readEveryCourse` calls the same
root a failing course. `:316-318` also tells #241 to cache `readEveryCourse` as one unit, which is a mechanism #241
owns and reads against item 8's "cache() per course id".
Rule: When a design changes what a field means, list every reader of the old meaning and say what each now shows;
every branch of a seam's typed result is defined for every listing, non-slug names included; obligations for
another issue state the rule with its ADR pointer, not the mechanism.

### 2026-11-24: #220 rework restates an ADR rule for #241 wider than the ADR says it (#220, judge_design round 2, architecture)
Fixing A3 (an obligation dictating #241's mechanism), `plans/220-design.md:327-329` now obliges #241's dashboard and
"Другие курсы" to read "only through the one per-course read function (item 8; no second id path)". ADR-0009 item 8
puts that rule on "every course id that arrives with a request"; the dashboard and "Другие курсы" take their ids from
the root's listing, not a request. Item 8 also says "Другие курсы" reads only "the `course.yaml` of each other
course", while the per-course read function (`readCourseById`, section 1) reads the whole tree, so the obligation
cannot be met as written: #241 must either read other courses' modules (breaking item 8) or add a second function
(breaking the obligation). The dashboard via `readEveryCourse` would also not be "the one per-course read function".
Rule: When an obligation cites an ADR item, quote the item's own scope (whose ids, which files) and check every
reader the obligation names can meet it; shortening a rule must not widen whom it binds.
