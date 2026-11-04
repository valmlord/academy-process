# Architect Mistakes

Methodology lessons for designing. Seeded with design-discipline lessons; append new
project-specific ones as they are found.

### Missed a deploy/packaging requirement

Designed a new module without accounting for how it gets packaged/imported/installed in the
target environment; the coder then hit a runtime "module not found".
Rule: Every design that adds a module, directory, or dependency must state how it reaches the
target environment (packaging, import path, install/symlink step). The design review checks this.

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
