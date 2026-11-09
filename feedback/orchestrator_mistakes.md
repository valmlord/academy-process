# Orchestrator Mistakes

Methodology lessons for running the pipeline. Seeded with pipeline-discipline lessons; append
new project-specific ones as judges surface them.

### Inline judge votes

Recorded PASS via `pipeline-advance.sh judge` directly instead of spawning judge agents.
Rule: Always spawn the three judges (one message, parallel). The hook auto-records. Never call
`pipeline-advance.sh judge` yourself.

### Rubber-stamp design review

Said "design solid" in ~50 seconds without checking the deploy model.
Rule: Spawn the architect as reviewer. Check deploy/packaging/deps. State what you checked.

### Used a bare subagent type instead of the role file

Spawned a generic agent without its `.claude/agents/<role>.md` - no project rules - and a
resource leak shipped.
Rule: Always `Agent(prompt="Read .claude/agents/<role>.md first. Then: <task>")`.

### Judges spawned sequentially, not in parallel

Spawned the three judges across three messages instead of one message with three parallel Agent
calls. Wasted time and broke the design.
Rule: All three judges in ONE message. Never sequential.

### Fixed a role's mistake inline instead of re-spawning that role

Judges found an architect design flaw; the orchestrator hacked a fix inline instead of
re-spawning the architect with the updated mistakes file.
Rule: On a role's mistake - the judge writes it to that role's file, then the orchestrator
re-spawns THAT role (researcher → architect → coder → judges as needed). Never fix inline,
never delegate an architect fix to the coder.

### Advanced past a judge FAIL

Judges FAILed the design, but the orchestrator advanced through planner/coder anyway, so code
would have been written from a flawed design.
Rule: Judge FAIL = STOP. Send back to the responsible role. Never advance past a FAIL.

### Advanced the phase without actually running test_deploy

Marked test_deploy done without deploying/testing; testing happened later, manually.
Rule: test_deploy must ACTUALLY deploy and test - verify the real outcome, not just syntax.

### Advanced without waiting for the judges to return

Did an inline review and advanced while spawned judges were still running.
Rule: Wait for all three judges to return before advancing. If they are slow, say so and wait.

### Coder/judge prompts missing the full architect design

The coder prompt carried the orchestrator's summary, not the full design, so a feature was
missed; the judges couldn't catch it because their prompt lacked the design too.
Rule: The coder prompt references the FULL architect design. The judge prompt includes the
design verbatim so judges can verify completeness.

### Assumed the user wanted to stop instead of asking

With outstanding judge FAILs, the orchestrator assumed "stop" and rushed closure.
Rule: When work is outstanding (judge FAILs), ASK the user to continue or defer. Don't decide.

### Deployed a live-service module with no whole-module acceptance step

Shipped a module with a module-level use-before-definition: it compiled and all unit tests
passed, but it could not START (the tests never imported the whole module).
Rule: Any change to a live-service module needs an acceptance step that IMPORTS/EXECUTES the
whole module (e.g. `--self-check` → exit 0). Passing unit tests + a clean compile do NOT prove
the program runs.

### Asserted a root cause / "lever" without checking prior notes for a refutation

Built work on a causal story that a prior, authoritative note had already refuted.
Rule: Before declaring a mechanism a root cause or a lever - grep the changelog / design notes
for that mechanism and the words refuted/disproven, especially if it has a history. A prior
verified refutation outranks a fresh, convincing story.

### A post-deploy verification command keyed on a path that does not exist

Shipped a verification one-liner that queried a wrong/absent field, so it returned empty and
gave a false GREEN on a critical path.
Rule: Validate every post-deploy check against the ACTUAL emitted artifact's structure, not a
variable name read off the source.

### Spawned a judge to review code it could not read

Asked a judge (Read/Grep-only) to review code that lived on a remote host or an un-checked-out
branch - it could not open a single line.
Rule: Materialize the code where the judge's tools can read it first (check out the branch, or
pull the diff/files into a scratch path, or grant the needed tool). A judge that cannot read
the diff must FAIL/CANNOT-CERTIFY, never PASS on trust.

### 2026-10-28: Every code-review fix round produced the next round's finding (#23)

Code review of #23 took four rounds; rounds 2-4 each failed on something the previous fix round
introduced: a design doc left behind the code change (pl_gate -> cfg), then a new guard placed
outside the try it was meant to sit behind, tested only with a value that does not reach it.
Rule: When re-spawning the coder after a judge FAIL, the brief always says (1) update every design
and ADR statement the fix contradicts, in the same pass; (2) add a test at the exact boundary that
breaks the old code and watch it go red before the fix; (3) no new guard outside an existing
exception boundary.

### Forwarded a judge's suggested wording as the fix, unchecked (#15)

judge_content on #15 took six rounds. Twice the next blocker came from the replacement text a judge had
proposed in the previous round: "запросов нет; ... ask-правила" for bypassPermissions, and a closed
defaultMode set that dropped the documented `manual` alias. I passed those suggestions to the author as
the fix.
Rule: A judge's proposed wording is a hint, not a source. When re-spawning the author, tell them to fetch
the primary source themselves and write from its quotes, and to report the quotes. When a fix narrows a
rule to a closed set, have the researcher or author enumerate every documented value (aliases included)
before the set is written.

### Content round budget spent on one lesson's long tail (#15)

From round 3 on, every judge_content blocker was in L6 permissions text or checks, and each round surfaced
one new edge. Asking Stepan before every extra round was right, but a single targeted "close every
documented value and every claim about modes against the docs" pass on L6 would have saved three rounds.
Rule: When two consecutive FAILs land in the same file and topic, the next re-spawn asks the author for a
full sweep of that topic against the source, not only the listed item.

### Design review rounds spent on unrun runbook scripts (#26)

A translation task grew a GitHub runbook and a git squash recipe as prose and shell literals that nobody had
run. Five design rounds followed; every FAIL from round 2 on was a script defect (quotes, rm, detached HEAD,
missing push, unchecked writes) that a single run would have shown. Round 5 passed once the operations judge
ran every check live.
Rule: when a design prescribes scripts or git procedures, have them executed (scratch clone, scratch
directory, dry run) before the judge round, and give the operations judge the explicit job of running them.
Put the infra procedure in its own issue when it dominates the design of a docs task.

### 2026-10-29: Pasted tool output can carry a vote line (#27)

judge_code round 1 on #27 found that the design validator printed lines starting with `PASS :root ...`, which
`hookio.VERDICT_RE` parses as a verdict; the design judges were told to paste that output under their FAIL items, so
an honest FAIL would have been recorded as PASS. Design review (two rounds, 3/3) did not catch it because nobody ran a
tool's output through `verdict_from`.
Rule: whenever a design adds a tool whose output a judge pastes into its report, the design review brief asks one
judge to run sample output through `hookio.verdict_from` and confirm no line parses as a verdict; judge templates put
the verdict on the last line.

### 2026-10-29: Plan the unrelated uncommitted file before the pr gate (#27)

Stepan's uncommitted `.github/CODEOWNERS` edit blocks `pr` and Stop at done (clean-tree checks), and agents may not
stash. Round 1 of the #27 design FAILed partly for having no path.
Rule: at init, if `git status --porcelain` shows a file outside the task, put "how the tree gets clean before pr"
into the architect brief as a requirement, with the step owned by Stepan.

### 2026-10-29: Issue spec exempted only process work from "every new issue gets a milestone" (#57)

The #57 issue body said "a new issue gets a milestone (process work under #56 may have none)". Cross-milestone
epics (#52, #53) exist precisely because they span milestones and carry none, so the rule, applied literally,
tells the orchestrator to give the next feature epic a single milestone. The coder copied the exemption as
written. Judge-architecture FAILed the HOTFIX on it.
Rule: When a spec states a universal rule ("every new X gets Y"), check it against every existing kind of X
in the live data (here: epics, process issues, feature issues) and list each exemption the data already shows.

### 2026-10-29: A shell-less architect prescribed tester commands nobody had run (#28)

The #28 design took three rounds. Rounds 2 and 3 were spent on the tester's command register: commands written for a
clean machine (T-install on a populated node_modules, `git diff` without histogram, DOCKER_HOST that testcontainers
ignores, a vitest globalSetup error it rewrites), and checks run in the worktree where uncommitted generated files
make them red on correct work. The architect has no shell, so every round trusted text that only the operations judge
could run. Round 3 passed once the operations judge was told to run every command verbatim against a scratch clone
that reproduces the state the pipeline leaves behind.
Rule: when a design prescribes tester or CI commands, the round-1 operations brief already says "run every
prescribed command verbatim in a scratch clone with the pipeline's real state (populated node_modules, uncommitted
generated files, leftover containers)". Tooling checks that depend on a clean tree run in a clone, never in the
worktree.

### 2026-10-29: A flow gap found after judge_design had no owner (#50)

In the author phase the lesson prototype needed a label set (check kind) and accessible names ("Навигация",
"Область", "Разделы урока") that `design/flows/ia.md` did not register. The ux-researcher's window ends at
judge_design and phases cannot go back, so nobody could fix the flows; Stepan had to decide to drop the field and
defer the names to a follow-up.
Rule: in a DESIGN architect brief, require a register entry for every string and accessible name each in-scope page
will render (incl. landmark, tab-list and menu labels and every field a row shows), and have judge_design check the
register against the page inventory before passing.

### 2026-10-29: judge_ux rounds spent on behaviour nobody ran (#50)

judge_ux took four rounds; every blocker from round 2 on was cross-page or state behaviour (tab reset by simulated
actions, `?tab=` not written, Back) that a scripted run would have shown, and two rounds were page workarounds of
system gaps that the consistency judge then failed.
Rule: before judge_ux, have the product-designer report system gaps instead of working around them (ui-designer
closes them first), and require a headless run of every control in every state from every tab, plus Back and the
cross-page round trips, with counts in the report.

### 2026-10-29: Formatter fix plan claimed "whitespace only" without running the formatter (#50 CI fix)
`plans/50-learner-flows-design-system-ci-format.md` scoped the biome run as "whitespace and line breaks
only", but `biome format design/system/proto.js` also inserts trailing commas (call arguments, arrays).
The acceptance offered an eyeballed `git diff -w` as an alternative to a token-level proof, and the
behaviour test it named covers only the lesson page, while `proto.js` drives all four prototypes.
Rule: Run the formatter in check mode before writing the plan, list every change class it makes, and make
a mechanical equivalence check (minified or AST output byte-identical) the mandatory acceptance.

### 2026-10-29: CI-format plan claimed "whitespace only" without dry-running the formatter (#50)
The proto.js format plan set "token-identical / pure line wrapping" as acceptance, but a dry run of
`biome format` adds 11 trailing commas and moves a parenthesis inside the F6 region-cycle filter
(equivalent only by `&`-over-`&&` precedence). The plan's behaviour check (r4.mjs) does not exercise F6
or focus at all, so the one non-whitespace change in a keyboard path had no test.
Rule: Before writing acceptance for a mechanical rewrite, dry-run the tool to a scratch file, list every
non-whitespace delta, and require a behaviour check for each code path a delta touches.

### 2026-10-30: Anti-cheat rounds spent on a deliberate cheater with the grader in hand (#41)

judge_design took six rounds and student plus judge_content four more; from design round 3 on, every blocking
item was a new way for a learner who reverse-engineers the grader to pass a deterministic check (Stop-hook probe
literals, then timing, then a static evaluator of the probe files; L2 glued words, marker-only skills, `@` import
forms). Each fix exposed the next, and two fixes (four probe templates, the first import regex) bought nothing.
Stepan ended both loops by moving the class to accepted residuals or to a mentor rubric.
Rule: at the first FAIL of this shape, before the re-spawn, ask Stepan which cheater classes are in scope for
command checks and which go to a rubric or a recorded residual, and put that list in every later judge brief;
when a vendor parser is emulated, make the check stricter than the vendor by construction instead of copying
its regex.

### 2026-10-30: Claimed an approval Stepan had not given; rounds ran past 2 (#42)

judge_design took five rounds and judge_content four plus an accuracy-only re-check. The #41 rule (ask for the
cheater scope at the first FAIL of that shape) was applied in design round 2 and held: from round 3 on no blocker
was an out-of-scope class. What still cost rounds: fixes that broke honest solutions (content round 3, planted
imports in L2), a check that a grep could forge (D1), and task text that described an earlier version of the
check (round 4 accuracy, two sentences). Separately, the orchestrator told the parent that the L2 fix would be
checked "with Stepan's approval" without a new round; Stepan had said nothing of the kind.
Rule: never attribute a decision to Stepan that he did not state; when skipping a review seems right, send the
question and wait. After any check-code change, re-spawn the lesson-author to re-read every task.md sentence
that describes that check before the judges see it, and run the honest corpus before the attack corpus.

### 2026-10-30: status: ready not set before leaving the author window (#42)

The orchestrator advanced judge_content -> compound -> commit with module.yaml still `planned` and every
lesson.yaml `draft`. The phase gate then refused lesson-author (window author..judge_content), and Stepan had to
approve the orchestrator editing the six status lines itself.
Rule: right after the last judge_content PASS and before advancing to compound, have the lesson-author set
`status: ready` in module.yaml and every lesson.yaml and re-run `pnpm content:validate`.

### 2026-10-30: Design-system drift reviewed by example, fixed by example (#29)

judge_code needed four rounds for #29, and rounds 2-4 were all about vendored shadcn styles. Round 1 named three
differences the tester saw (heights, card shadow, dark fill); the coder fixed exactly those; round 2 found `md:text-sm`
and the Button states; round 3 found a why-comment the round-2 fix made false. My briefs passed the judges' examples
straight to the coder instead of the class of problem. A separate cost: the operations judge's round-3 design verdict
was not recorded because its final report did not end with the verdict line, which stalled the gate.
Rule: when a finding is "vendored component defaults differ from the design system", brief the coder to walk every
class and state of every vendored component against `proto.css` and the README and return a state table, and brief
the tester to compare computed styles for every state, in round 1. In every judge brief, repeat that the final report
must end with the bare PASS or FAIL line.

### 2026-10-30: Architect brief named the hidden link, not the hidden class (#79)

judge_design usability failed round 1 because my architect brief said "grep for the hidden item" and named the
top-bar "Курс" link, while the rule the architect wrote hides every `/courses/...` control (Card button, module
rows, "Открыть курс", breadcrumbs). The grep followed my wording, so five dashboard ACs describing the other
hidden controls stayed unconditional. Round 2 passed once the brief named the class.
Rule: when a DESIGN brief asks for a release or visibility rule, ask the architect to list every member of the
class the rule hides first (labels, routes, flow step ids, components), then grep each member and scope every
acceptance check, table row and AC that describes one.

### 2026-10-31: One coder spawn for a 47-step design ran out of context (#30)

The first #30 coder stopped after commit 6 of 10 when its context ran low; a second spawn finished. It stopped
cleanly only because the brief asked for a clean commit boundary. The fix rounds also rebased onto
`origin/main`, which a background fetch had moved, and the coder had to move the branch back by hand.
Rule: for a design over about 25 steps, brief the coder in commit ranges from the start (one spawn per 4-5
commits, each with the resume notes of the previous one), and name the base commit explicitly in every rebase
instruction instead of `origin/main`.

### 2026-11-01: The tester's brief asked it to attack the new gate (#86), keep doing that

The coder watched every guard it wrote go red, yet three tester rounds still found gate gaps,
each from a case the coder had not imagined (hidden paths, repo config, nested caches).
Rule: For any new gate, the tester brief names the gate and asks for bypass attempts the coder
did not list (config, symlinks, odd names, nested paths), on scratch copies. A coder's own
mutation set shows the guard can fail, not that it covers the class.

### 2026-11-03: Tester fixes moved the code past the design, and nobody updated the design (#89)

Three tester rounds on #89 added behaviour the judged design never described (casefolded names, shadow-ref
refusals, new report findings, an extra formatter argument). The architecture code judge caught it and asked for
an "Implementation deltas" section before the PR; the operations judge found a doc step (sync step 6) that the
design had specified wrongly and the coder had copied faithfully.
Rule: after any tester-driven fix round, brief the architect to append the deltas to the design in the same
turn as the coder fix, and brief the tester to rehearse every procedure Stepan follows by hand literally, not
only the hooks. Live checks that need a new session are proposed as cards or started on Stepan's own words: the
app refuses to start sessions from a turn an agent's report started.

### 2026-11-02: A design took away a capability Stepan used, and I did not ask him (#86)

The #86 design decided "main checkout only, no worktrees" (design line 68, accepted by the judges in round 1).
That ended parallel side sessions in worktrees, which Stepan had used before: a worktree no longer gets
`.claude/`, so it has no hooks, agents or instructions. The decision sat in one line of a long design, I never
put it to Stepan as a question, and he found out only when he asked for parallel work.
Rule: when a design removes or changes something Stepan does today (a workflow, a command, a capability,
parallel sessions), name the loss in plain words and ask him with AskUserQuestion before judge_design ends.
A judge's acceptance is not his consent.

### 2026-11-03: A process commit parked on a stale task branch while the task was paused (#31)

I committed #31's design lessons to the process branch `feat/31-workspace-service` before pausing #31 for #89,
then moved `.claude` to a new branch from main. The lessons left the working tree with that branch, #89 and #80
merged around it, and at #31's commit phase the old branch sat on a superseded main with the lessons missing from
the files. I had to re-apply them by hand.
Rule: when a task is paused, do not leave its process edits committed on a task branch that the next task will
not build on; either open its process PR before the pause or leave the edits uncommitted on main's files and
commit them on a fresh branch at the task's commit phase. Also: a design that the code outgrows (two amendments,
25 accepted deviations) gets its implementation-deltas file before judge_code, not after the judges ask.

### 2026-11-03: Architect brief checked README truth against the CSS only (#80)

judge_design round 1 failed twice on items my brief shaped: I asked that every README statement "match the CSS after
the change", so the architect never checked it against the shipped app, which the README binds as the ADR-0006
contract; and I asked for an acceptance script with "expected counts per page" without saying the counts must be
asserted in code, so the script printed them and passed on an absent member.
Rule: in a DESIGN brief that edits design/system/README.md, require each changed sentence to be checked against both
proto.css and the app classes (file:line). When a brief asks for an executable check over a class of members, say
that every member's expected count is asserted in code and that absence is a finding.

### 2026-11-03: Scoped out an item the issue owner had assigned to design, without reading the comments (#83)

The #83 architect brief put F3 (Radix Tabs ring on mousedown) out of scope as app behaviour. An owner comment on
#83 asks design to decide whether it accepts the ring or wants `:focus-visible`-only rings for tab triggers; the
brief was written from the issue body and the #85 PR body only. judge_design usability failed round 1 on it, and on
follow-ups recorded only in git-ignored `plans/`.
Rule: read `gh issue view <n> --comments` before writing the architect brief, list every owner comment as an
in-scope item or a decision for Stepan, and require each out-of-scope item to be recorded in a committed file or a
follow-up issue, never only in `plans/`.

### 2026-11-09: My own suggested comment wording cost a judge round (#33)

judge_code round 2 failed on a false Dockerfile comment. In the coder brief I wrote a replacement sentence myself
("no RUN of this stage sees them, and a version bump re-runs none of them") and the coder used it verbatim; its second
clause was false for a base, Go or Node bump, and round 3 failed on it. The #15 rule (a judge's wording is a hint) applies
to my own wording too.
Rule: when a fix is a sentence about behaviour, do not hand the coder a ready sentence; ask for one that claims only what
the code and the evidence show, and have the coder list each case the sentence covers with the evidence for it.

### 2026-11-09: Docker disk and parallel sessions were not in the brief until they bit (#33)

The Docker VM disk filled once (another session's builds), and later the build cache stood at 43.5 GB before my
coder's first build. The owner snapshot then showed a parallel session's `:t32` images. Each cost a stop and a question
to Stepan. The guard harness for the fake-docker runs also took four design rounds (sec r4 N1 still lists `env -P`,
`bash -l` and `env -i` forms as residual), because the first versions proved the stub resolved but not that the script
used it.
Rule: for any task that builds images, put in the first coder and tester briefs: `docker system df` and `df -h /`
before and after, a stop threshold, own images removed right after each check, and an owner-snapshot exclusion for
every parallel session's tags known at init. For any stub harness, gate every risky row on a positive control that
proves the script under test reached the stub.

### 2026-11-09: Briefed stack runs without a disk and build-cache budget (#32)

The first #32 tester run copied the tree several times while images built; the host disk filled, the Docker VM
went read-only and Stepan's Postgres was hit. After the restart every isolated stack run still added about 3 GB of
build cache that agents may not prune, so the cache went from 0 to 43 GB over one task.
Rule: every brief that may build images or run a stack states the host-free floor, a build-cache ceiling, the
maximum number of stack runs and "never prune"; check `df -h /` and `docker system df` between spawns and tell
Stepan when the cache passes the ceiling instead of starting another run.

### 2026-11-04: A contract change sized from the issue label, and a design that took four rounds (#68)

#68 was labelled tier:task and the issue said "migrate the six module 00 lessons"; the researcher found 18 ready
lessons on main, the design estimated ~25 files, and I kept the TASK tier. The phases match PROJECT, so nothing was
skipped, but the size should have been named before judge_design. judge_design then took four rounds: each round's fix
(a judge's prescription copied into the design) carried a new defect the next round found (a counting floor without
#15's safety condition, a rollout rule that listed cases, a raw-YAML rule that ignored zod defaults).
Rule: re-tier from the architect's own size estimate and tell Stepan when it crosses a tier. When re-briefing the
architect after a FAIL, ask it to check each prescribed fix against its source (the cited design, the schema's
defaults, the property behind a listed case) before writing it in, not to copy the judge's sentence.
