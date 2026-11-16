# Coder Mistakes

Methodology lessons for implementing. Seeded with coding-discipline lessons; append new
project-specific ones as they are found.

### Heavy object created per-request in a loop

Built an expensive object (connection, client, pool, model) on every call inside a loop instead
of once; it leaked resources until the host nearly crashed.
Rule: Never create heavy objects per-request in a hot path. Build once, reuse.

### Module-level use-before-definition

Referenced a name at module top-level before it was defined. It compiled (a runtime NameError,
not a syntax error) and unit tests passed (they lifted individual functions, never imported the
whole module), but the program could not start.
Rule: Verify every name exists in scope before use, especially at module load. Confirm the whole
module imports, not just that individual functions work.

### Patched a live target ad-hoc instead of edit-locally-then-deploy

Edited a running target in place (`sed -i`, heredoc, in-place edits) instead of editing the
source and deploying through the normal path; the change was untracked and hard to reproduce.
Rule: Edit source locally, then deploy through the project's deploy path. Never patch a live
target ad-hoc.

### Expanded scope beyond the plan

Added features and refactored surrounding code that the plan did not call for.
Rule: Follow the plan exactly. Small, focused edits. On judge feedback, fix ONLY the identified
issues; don't refactor around them.

### 2026-10-27: Reused a path-prefix list as a shell substring rule (#21)
bash-code-guard.sh built its core regex from `pipeline_core_files` verbatim. Those entries are
prefixes for relative file paths in the write gate, so `.claude/hooks/` carries a trailing slash.
In a shell command the directory is usually named without it. As a result `rm -rf .claude/hooks`,
`cp x.sh .claude/hooks`, `mv .claude/hooks .claude/hooks.bak` and `ln -sf /tmp/x .claude/hooks`
passed outside PIPELINE. Deleting or renaming the hooks dir makes every hook command exit 127,
which is a non-blocking error, so all the gates fail open. The design's 2.7 text listed the same
slash form, but D-4 ("core writable only in PIPELINE, shell writes too") is the requirement. The
D11 test only exercised the `.claude/hooks/x.sh` form, so it could not catch this.
Rule: When a prefix list for one matcher (relative paths) feeds another (free-form shell text),
match the bare directory name with a token boundary too, as well as any ancestor that contains it.
Add a test for the directory named without a trailing slash.

### 2026-10-27: A failed state write reported as success through `[ "$(cmd)" = x ]` (#21)
pipeline-advance.sh's vote branch ran `if [ "$(state_op vote ...)" = "vote-dup" ]` and otherwise
printed "Judge recorded" and exited 0. A failure inside a command substitution used as a `[`
argument is invisible to `set -e`, so state.py's lock timeout (75), phase race (3) or unreadable
state (1) became "Judge recorded ... exit 0". pl_record_vote then logged `vote-ignored:advance-rc-0`
with the wrong rc. This broke the design's rule that the CLI passes 1/3/4/75 through, and the
message misinforms. The A10 test called state.py directly, so it never ran this branch.
Rule: Capture a command's output and its rc separately (`out=$(cmd) || rc=$?`) before comparing.
Every error path of a CLI wrapper needs a test that goes through the wrapper, not just the library.

### 2026-10-28: A TypedDict cast justified by a comment that overstates the validation (#23)
`cfg._validate` ends with `cast(Config, data)` under the comment "The checks above are exactly what
Config declares", but `TierConfig` declares `team: str`, `requires_issue: bool`,
`edits_pipeline_core: bool`, `learner_writes_code: bool` and none of them is checked. A
`"edits_pipeline_core": "false"` passes `load()`, `has_flag` returns `bool("false")` = True, and
mypy, trusting the cast, sees a bool, so strict typing cannot flag it. The one cast in the hook
Python carried a false justification: exactly the hole the "no Any, casts justified" rule exists
to close, and a lying comment is a defect under the code-style rules.
Rule: Before casting to a TypedDict, check every declared field (nested ones included) or declare
the unchecked ones as `object`; the comment on the cast lists what was checked, and only that.

### 2026-10-28: A fix added an import edge and a behaviour change; the design record still denied both (#23)
The round-1 fix (58c1152) made `pl_gate.py` import `cfg` (for `cfg.ConfigError`) and made `cfg._validate`
reject wrong-typed tier keys. The design doc still said `pl_gate` "imports only the stdlib and
`pl_jsonshape`" (2.7) and listed `pl_gate imports pl_jsonshape` as its only lib edge in the 2.8 import
graph, the record used to order typing and to rule out cycles. 2.8 also still said `cfg.load()` checks
"the top-level types" and "Behaviour must not change" except AttributeError shapes, while a string or 0/1
flag in ANY tier now crashes every gate (fail closed). The fix to a lying comment left a lying design
record.
Rule: When a fix adds an import or changes behaviour, grep the design/ADR for the module name and update
every statement about its imports and behaviour in the same commit.

### 2026-10-28: A guard placed outside the try it was meant to sit behind became the only crash path (#23)
8aa48dd added `if not math.isfinite(parked_ts)` to `state._parked_at` BEFORE the
`try: time.localtime(...) except (OverflowError, ValueError, OSError)`. `math.isfinite` converts an
int to a float, so a JSON integer above ~1.8e308 (e.g. 10**309; 10**308 still converts; `json.load` returns it as an int)
raises `OverflowError: int too large to convert to float` outside the try: `parked` prints a traceback
and `status` (set -euo pipefail) exits non-zero. Without the isfinite line, `localtime` raises inside
the try for inf, NaN and that int alike, so the extra guard added the only uncaught path while design
2.3 claimed "instead of ... a traceback". The test row used 1e20, which converts to float fine, so the
boundary that breaks the guard was never exercised.
Rule: Every pre-check on untrusted input runs inside the same exception boundary as the call it
protects, and the test rows include the value that breaks the pre-check itself, not only the call.

### 2026-10-29: Added a code span in translation; V3 requires span multisets to be unchanged (#26)
Translating the last criterion of `backlog/20`-`25` ("отчёт агента-ученика приложен к PR, ...") as
"the report of the `student` agent ..." introduced a new inline code span that the original never had.
Design section 4, V3, requires the multiset of inline code spans of every translated file to equal
`main`'s, so the tester's span diff went red on all six files.
Rule: A translation neither adds nor removes code spans. Name a role in plain prose unless the original
already backticks it, and diff the span multiset against `git show main:<file>` before handing back.

### 2026-10-29: A test named for a check could not fail when that check was deleted (#27)
`test_color_token_missing_in_dark_is_an_error` removes `--accent`, a required token, so the required-token
check reports it and the separate theme-symmetry loop (`scripts/design_tokens.py:345-348`, "every colour token
present in one theme is a colour token in the other") is never what the test sees. Deleting that loop leaves all 44
tests green, although the design table names exactly that mutation for this row and the commit says every test was
watched going red. Custom tokens (the case the ui-designer seed warns about) are therefore unguarded.
Rule: Watch the named mutation go red for every row yourself; when two checks would report the same fixture, pick a
fixture only the guarded check can see (here a custom colour token in one theme only).

### 2026-10-29: A secret-leak canary flattened logger arguments with String(), so object leaks stayed green (#28)
`packages/db/test/integration/client.int.test.ts:72` (I8b) builds the logged text as
`consoleError.mock.calls.flat().map(String).join(" ")`. `String({ connectionString })` is `"[object Object]"`, so the
design's own I8b mutation, "log the pool options or the URL in the default logger" (e.g.
`console.error(prefix, error, pool.options)`), leaves the canary assertion green, while the real `console.error`
prints the object through `util.inspect`, password included. Design 4.11 says the tests assert on
`util.inspect(value, { depth: Infinity })` because that is what a logger prints; `test/assertions.ts` already exports
`inspected` for exactly this, and I4/I5/I12 use it.
Rule: A leak canary renders what the sink actually prints (`util.format`/`inspect` of every argument), never
`String()`, and the "log an object that holds the secret" mutation is watched go red before handover.

### 2026-10-29: Exported React components without explicit return types (#1)
`apps/web/app/layout.tsx` `RootLayout`, `apps/web/app/page.tsx` `HomePage` and
`apps/web/components/course-list.tsx` `CourseList` are exported with inferred return types. The author's
code rules (`~/.claude/rules/code-style.md` section 2) require an explicit return type on every exported
function, components included: inference at a boundary turns an implementation change into a silent
contract change. The non-component exports of the same diff (`register`, `runStartup`, `migrateOnStartup`)
were annotated, so the rule was known and skipped for TSX.
Rule: Before handover, grep `export (default )?(async )?function` over the diff and give every hit an explicit
return type (`React.JSX.Element` / `Promise<void>` ...), TSX components included.

### 2026-10-30: A credential form without `method` submits the password in the URL before hydration (#29)
`components/sign-in-form.tsx` renders `<form noValidate onSubmit={...}>` with no `method`. Server-rendered it is a
plain `<form novalidate>`; until React hydrates there is no submit handler, so Enter (the email field is
`autoFocus`, a password manager fills both) makes the browser GET `/sign-in?email=...&password=...`. The password
lands in the address bar, the browser history, same-origin `Referer` headers and any URL log or trace. Every test
ran after hydration, so none could see it.
Rule: Every form that carries a secret gets `method="post"` even when JavaScript handles the submit, with a test
asserting the rendered `method`; check the server-rendered markup, not only the hydrated behaviour.

### 2026-10-30: A stale why-comment, a skipped env-example block and unlisted design-system drift (#29)
`apps/web/test/integration/db.ts` justified raw SQL strings with "two copies of drizzle-orm ... whose SQL types do
not mix". That was the coder's belief before the pause (resume note, finding 2); after the resume the lockfile was
shown to hold one snapshot linked by both packages (design 6.6, tester section 10), and the comment stayed. In the
same diff `.env.example` never got the `SEED_EMAIL` / `SEED_PASSWORD` lines of design 6.2, although the file's
header says every variable the code reads is listed there. And the `radix-nova` defaults written by `shadcn add`
(32px inputs, 28px small buttons, a ring instead of the card border and shadow, a translucent dark input fill) were
left against `design/system/README.md` ("Controls: height 2.25rem, small 2rem", "shadows only on cards", "No
opacity on ... any container with text"), neither fixed nor listed as deviations.
Rule: When a finding is settled, grep the diff for every comment that states the old belief and fix it in the same
commit; before handover, diff `.env.example` against the design's env table; for every vendored shadcn component,
compare its sizes, borders, shadows and fills with `design/system/README.md` and `proto.css`, and fix or list each
difference.

### 2026-10-30: `.env.example` left out variables the new code reads, against the design's literal block (#29)
Design 6.2 gave the exact `.env.example` lines to add, ending with the commented `SEED_EMAIL` / `SEED_PASSWORD`
block and "Put them here, never on a command line". The commit added every line above it and dropped that block,
although `apps/web/lib/seed-cli.ts` reads `SEED_EMAIL`, `SEED_PASSWORD` and `SEED_NAME` and the file's first line
says "Every variable the code reads must be listed here". The README covered it, so no test went red; the file a
fresh checkout copies to `.env` did not.
Rule: Before handover, grep the diff for every `process.env.X` / `env.X` read and check each name appears in
`.env.example`; when the design gives a literal block for a file, diff the file against that block line by line.

### 2026-10-30: The shadcn alignment fixed only the items the judge named (#29, judge_code round 2)
The round-1 rule said to compare every vendored shadcn component with `design/system/README.md` and `proto.css`.
The fix changed the three named items (heights, card, input fill) and left, in the same class strings, `md:text-sm`
on `Input` (README: inputs `text-base`, "16px avoids iOS zoom on focus"), no `aria-disabled` style on `Button` (the
busy "Войти" stays solid primary; `proto.css` paints `muted` / `muted-foreground`), `hover:bg-primary/80` and ghost
`dark:hover:bg-muted/50` (translucent fills under text; proto uses an opaque 90 % mix and `accent`), and
`disabled:opacity-50`. A "design/system" comment was added above a class list that still contradicts it.
Rule: Aligning a vendored component means walking every class in its string (size, font size, every state: hover,
focus, aria-disabled, disabled, dark) against the matching `proto.css` rule, not only the classes a reviewer named;
compare each non-default prototype state (`#state-*`) with the app, not only the default one.

### 2026-10-30: A comment claimed parity with the prototype and a cause the built CSS does not have (#29, judge_code round 3)
`ui/button.tsx` said "when it is also aria-busy the progress cursor wins, as in proto.css", but in proto.css
`.button[aria-disabled="true"]:hover` outranks `[aria-busy]`, so the prototype computes `not-allowed`; the app's
`progress` is right and the prototype is the bug. The same comment said the `aria-disabled:hover:*` classes are what
keep the busy button muted on hover; the tester's mutation removed them and the computed paint did not change,
because `aria-disabled:` already sorts after `hover:`. A unit test then pinned those dead class names.
Rule: Before writing "as in X" or "so it is listed", check the claim against computed values (prototype in a browser,
a mutation on the app); when the app intentionally differs from the prototype, the comment says so and names the
DESIGN note, and a class that changes no computed value is deleted, not asserted on.

### 2026-10-31: A missing course root is logged with an empty file name (#30, judge_code round 1)
`nodeCourseFs.listDirs(root, "")` turns ENOENT into `CourseFileError("", "missing")`, so a wrong `COURSE_ROOT`
or an image without `/app/course` logs `web: course read failed: : missing`, and the image build would stop with
`export-course: CourseExportError: : missing`. The most likely misconfiguration of the feature produces the one
log line that does not say what is missing, while the empty-course case of the same reader already says `"."`.
The tester saw the line (F1) but every unit test exercised only files below the root.
Rule: For every error path that carries a "relative file" field, test the root itself (missing, empty, unreadable)
and check that the printed line names something an operator can act on; never let an empty string reach a log.

### 2026-10-31: A vendored component's link styles became reachable and were not walked (#30, judge_code round 1, architecture)
`components/lesson/prerequisite-alert.tsx` puts the prerequisite links inside `AlertTitle`, the first links any
Alert in the app holds. Design 8.4 "Links" says prerequisite links use `inlineLinkClassName`; they got a bare
`<Link>` instead, so the registry's `[&_a]:underline-offset-3 [&_a]:hover:text-foreground` on `AlertTitle` styles
them: 3px offset and no 2px underline on hover, where the prototype (`proto.css:117-118`) has 0.2em and 2px. Adding
`inlineLinkClassName` alone would not fix it: `.x a` (0,1,1) beats `.underline-offset-[0.2em]` (0,1,0). The catalog's
note links were done right, so the rule was known and applied to one of two call sites.
Rule: When new markup puts an element type inside a vendored component for the first time (a link in an Alert, an
icon in a Badge), read that component's descendant utilities (`[&_a]:*`, `*:[svg]:*`) against the design row for the
element, every state, and check the compiled selector's specificity against the class you add.

### 2026-10-31: A test-infra fix for specs of earlier commits landed in a later feature commit (#30, judge_code round 1, architecture)
The 429 flake from Better Auth's limiter comes from the many page loads of the catalog, not-found, lesson and leak
specs (commits 7 and 8), but their `useOwnBucket` `beforeEach` blocks were added in commit 9 (dashboard), found by
commit 9's three back-to-back runs. Commits 7 and 8 therefore leave a suite that is red on a rerun, and commit 9 mixes
the dashboard with a fix to four other specs; its body also says every page load "now" reads the session endpoint,
which has been true since #29.
Rule: A fix found late goes into the commit that introduced the failing code (fixup and rebase while the branch is
unpushed, with the author's approval of the rewritten history); run the multi-run check at every commit that adds e2e
load, not only at the last.

### 2026-11-03: Work before the lock and state from a stale listing broke the ordering the ADR promises (#31, judge_code round 1, architecture)
`WorkspaceManager.ensure` awaited a whole-course read before `mutex.run`, so a stop or DELETE that arrived later on
the same key ran first and the PUT then re-created the workspace; ADR-0010 item 8 (written in the same PR) says calls
on one workspace queue behind earlier calls. Reconcile's `keep` branch called `tracker.forget` without the lock, from
the container state of the list taken at the start of the pass, so a workspace a PUT started meanwhile ran untracked
(activity 409, `idle: null`). Both were recorded as deviations with a reason, and neither had a test of the order.
Separately, the never-started branch reported the spec's image while the docstring said "what the container was
created from".
Rule: Call `mutex.run` synchronously at the top of every locked operation and do all work inside it; never mutate
shared state (tracker, cache) from a snapshot taken before an await unless under the same lock with a freshness
check; a deviation that touches ordering needs a test whose start state makes the two orders diverge.

### 2026-11-09: ARGs declared at the top of each Dockerfile stage broke the layer-cache property a comment still claims (#33, judge_code round 1, architecture)
Design 3.4 orders the final stage so that "a Claude Code bump rebuilds only the last big layer", and
`images/workspace/Dockerfile:148` repeats it. Coder delta 1 redeclared `GO_VERSION`, `NODE_VERSION` and
`CLAUDE_VERSION` at the top of the final stage (`:121-123`) and declared every fetch-stage pin at the top of `fetch`
(`:31-41`). Docker's reference: every `RUN` after an `ARG` uses it implicitly as an environment variable, so a changed
value is a cache miss for all of them. A version bump therefore re-runs the apt RUN, the identity RUN and the Go and
Node downloads, and every final-stage layer is new. The delta recorded the scoping but not its cache effect, and the
only cache test was a CLI `--label` change, which no ARG touches. Separately, the build script header (`:7`) still
said "On every failure <image> keeps its previous Id" after revision 5 added FAIL lines where the tag has moved.
Rule: Declare each Dockerfile ARG immediately before the first instruction that reads it (label-only ARGs right
before `LABEL`); when a comment claims a cache property, prove it by changing that ARG's value and checking which
steps say CACHED. After changing behaviour, reread the file's header comment against every new path.

### 2026-11-09: The B1 fix added a cache comment that is false as written (#33, judge_code round 2, architecture)
The round-1 fix moved the label ARGs right before `LABEL` and commented them
`# Read only by LABEL, so declared here: a version bump changes no layer of this stage.`
(`images/workspace/Dockerfile:168`, copied into design 3.4 step 8). The placement is right and the cache evidence
is real, but the sentence is not: a `BASE_IMAGE` bump changes every layer of the stage, a Go bump the
`/usr/local/go` COPY layer, a Claude Code bump the `/opt/claude` COPY layer, which the comment at `:150` in the same
stage says outright. What the placement guarantees is narrower: these four declarations put no ARG into any RUN
of the stage, so they cause no cache miss by themselves. The fix was asked to make every caching comment true, and
the new comment was the one left unchecked.
Rule: A comment that states a cache property names the mechanism it covers ("no RUN of this stage sees these ARGs")
and is checked against every value it mentions; when two comments in one stage describe the same bump, read them
side by side before committing.

### 2026-11-09: A reworded cache comment kept the same overclaim (#33, judge_code round 3)
The round-2 fix of images/workspace/Dockerfile:168 replaced "a version bump changes no layer of this stage" with
"no RUN of this stage sees them, and a version bump re-runs none of them". The first clause is true; the second is
still false for three of the four ARGs it sits above: a BASE_IMAGE bump changes `FROM ${BASE_IMAGE}` and re-runs every
RUN of the final stage (apt, usermod, test -x); a GO_VERSION or NODE_VERSION bump changes the fetch output, so the
`COPY --from=fetch` of Go or Node misses and the later `RUN test -x` re-runs. Only CLAUDE_VERSION re-runs no RUN here.
The design delta that quotes the new comment lists "a base bump changes every layer of the final stage" two lines
above it. The rewording narrowed the noun (layer -> RUN) but kept the universal "a version bump", and nobody walked
the four values through the instruction order.
Rule: When fixing a false comment, check the replacement against every value it quantifies over, by tracing the cache
chain (FROM, COPY --from, then every later instruction), not only the mechanism that was wrong. Claim what the
declaration does ("declaring them here invalidates no RUN"), not what a bump does, unless every bump was checked.

### 2026-11-04: Edited a test after the last formatter run and committed a lint-red step (#32, spawn B)
Step 8 (b9b8092) was committed after a late edit to `apps/web/server/relay.test.ts`; `pnpm lint` failed on one formatter
diff, and amend was not allowed, so a separate formatting commit (73ad8fa) followed. The step commit alone is lint-red.
Rule: run `pnpm lint` as the very last command before every `git commit`, after any later edit, and do not commit if it
is red.

### 2026-11-09: Fixed a proven defect by adding a framework internal, with no automatic guard and no ADR entry (#32, spawn D)
0f3a7f9 fixed D1 (merge-blocking SessionReadError on the sign-out redirect) by setting `__NEXT_PRIVATE_ORIGIN` in
`start()`. That makes the custom server depend on a fourth Next internal, one Next's own source marks "TODO: Remove"
(`action-handler.js:143,280`). U-origin tests only the derivation; removing the assignment, or a Next bump that drops
the variable, brings D1 back and no check fails: the tester's mutation run ended `T32 RESULT OK` with sign-out green,
and only a manual grep of the web log showed the error. ADR-0011's "a Next upgrade must re-verify" list and design 8.2's
"R-SMOKE and the e2e guard them" were not updated, so both now claim more than is true. The coder notes recorded the gap
as a residual instead of closing it.
Rule: when a fix couples to a framework internal, add it to the ADR's upgrade-reverify list and the residuals in the
same commit, and give the fix an automatic check that goes red when the fix line is removed; watch it go red before
calling the defect fixed. "Guarded by reading the log" is not a guard.

### 2026-11-09: Merge fix updated "#33 will" sentences in README and ADR-0002 but missed ADR-0011 (#33 HOTFIX merge, judge_code)
f2cb73b rewrote #105's forward references to #33 in README, .env.example, config.ts and ADR-0002 item 13, but
docs/adr/0011-browser-terminal.md:98 (written by #105) still says "tmux/dtach in the container: needs the image
(#33); revisit there". #33 now ships the image without tmux and records no revisit; the follow-up that weighs tmux
is #110. A reader of ADR-0011 is sent to #33 for a decision that is not there. `rg '#33' docs/` lists the line.
Rule: When a merge lands the issue another branch pointed forward to, run `rg '#<issue>'` over every file the other
branch touched (docs/adr included) and make each hit state a current fact or point to the issue that now owns it.

### 2026-11-09: Fallback undo step placed in another section, not in the runbook step that must undo it (#33, judge_code round 2, operations)
2e32272 told Stepan, in "Browser terminal", to add `TERMINAL_SHELL=/bin/sh` to `.env` while on the Alpine override
and to "delete that line together with the override in step 4b". Step 4b's block deletes only `^WORKSPACE_IMAGE=`,
its expected output and prose never mention `TERMINAL_SHELL`, and 4c checks only `printenv WORKSPACE_IMAGE`. Someone
following 4a-4e in order keeps the line, and the lesson image's terminal silently runs dash instead of bash.
Rule: When a runbook gains a temporary workaround, put its undo inside the numbered step that ends it (command,
expected output and a check in the verify step), not only in prose elsewhere that points at that step.

### 2026-11-09: Revert guidance names a subset of the conflict hunks, and following it breaks the build (#33, judge_code round 2, architecture)
2e32272's README rollback note for #32 says to resolve the revert conflicts by removing "the `TERMINAL_SHELL` lines
(`docker-compose.yml`, `.env.example`, `services/workspace/src/config.ts` and its unit tests)". The simulated revert
(`git merge-tree --write-tree --merge-base=a2cef86 HEAD a2cef86^`) shows every one of those hunks also holds the
#32 `TERMINAL_SCROLLBACK_LINES` / `terminalScrollbackLines` lines, and the conflict in
`services/workspace/test/unit/compose.test.ts` is a compose test, not a config.ts test. Kept as listed, the revert
leaves `TERMINAL_SCROLLBACK_LINES` in `CONFIG_DEFAULTS` (typed by a `ConfigVariable` that no longer has it) and
`terminalScrollbackLines` in `Config` with no parser filling it: tsc and config.test.ts go red. The kept ci.yml hunk
also keeps #32's comment about terminal specs that no longer exist.
Rule: Guidance for resolving a revert lists the conflicting files and hunks from the simulation itself, every
line of each hunk, and is checked by finishing the simulated resolution and running typecheck and tests.

### 2026-11-16: A tracked comment cited the local design, and a commit body repeated an unchecked claim (#162, judge_code round 1, architecture)
schema.int.test.ts (I15 accepted rows) says "node-pg returns the elements only (design 1.3)". `plans/` is ignored
by git, so the reference points at nothing for any reader of the repository; #86 already spent a round removing
"(design Dn)" comments from tracked files. The body of `fix(web): quote stored values in StoredFactError` says the
old message printed a stored NULL as "null"; the old `checkKindOf` passed `value ?? "<missing>"`, so a stored NULL
printed `holds "<missing>"`, the same as a missing kind. The claim came from research 5 and was not checked against
the code being replaced, which was in the diff.
Rule: Before handing back, grep the added lines for "design", "research", "plan", "round" and section or decision
ids and keep the reason without the citation; check every "before" claim of a commit body against the old code in
`git show main:<file>`.
