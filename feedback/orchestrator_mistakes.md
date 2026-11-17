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
re-spawns THAT role (researcher -> architect -> coder -> judges as needed). Never fix inline,
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
whole module (e.g. `--self-check` -> exit 0). Passing unit tests + a clean compile do NOT prove
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

## 2026-11-04 #43: a task-level constraint left out of a spawned brief
The parent task said "do not run Docker or docker compose". The L3 student re-run brief did not repeat it, and the
student graded in a Docker `python:3.12-slim` container. Spawned agents see only their brief.
Rule: every brief repeats the task's hard constraints (no Docker, paths not to touch, files never read), not only the
role's own rules. Write them once in the plan and paste that block into every spawn.

## 2026-11-11 #43: "stopped" background tasks after an app restart are not lost work
After two restarts the app marked three background shells and two agents as stopped. The shells were only
`tail -f` watchers and the corpus they watched had already finished; the scratchpad was wiped twice, though.
Rule: after a restart, check what the runs left on disk (logs, report sections, TOTAL lines) before rerunning
anything, and keep long-run logs and reports under `plans/` or report files rather than only in the scratchpad.
Resume a stopped agent with SendMessage when its context still holds the work.

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

### 2026-11-10: Extra judge round planned for one judge only, and a check fix not re-run by the student (#44)

After the two-round limit Stepan approved a third round, and I planned to re-run only the judge that failed.
The parent session caught it: a round counts only with all three judges in one message. Separately, two student
cheater rounds each found new passing cheats in checks that the designer had already "closed", and assessment
then found three more bypass families in docker-static over rounds 2-3.
Rule: an extra judge round always spawns all three judges, scoped to the changes. When a check is rewritten to
close a cheat, brief the designer to run a differential or adversarial corpus against the real tool's parser or
semantics (not only the reported forms), and plan one focused student cheater rerun before the judges.

### 2026-11-03: Scoped out an item the issue owner had assigned to design, without reading the comments (#83)

The #83 architect brief put F3 (Radix Tabs ring on mousedown) out of scope as app behaviour. An owner comment on
#83 asks design to decide whether it accepts the ring or wants `:focus-visible`-only rings for tab triggers; the
brief was written from the issue body and the #85 PR body only. judge_design usability failed round 1 on it, and on
follow-ups recorded only in git-ignored `plans/`.
Rule: read `gh issue view <n> --comments` before writing the architect brief, list every owner comment as an
in-scope item or a decision for Stepan, and require each out-of-scope item to be recorded in a committed file or a
follow-up issue, never only in `plans/`.

### 2026-11-04: judge_design rounds spent on sample states nobody had walked as one timeline (#72)

judge_design on #72 took six rounds. Rounds 1-3 closed real flow gaps (deep-link focus, the attempt summary
against #69's per-check words), but every blocker from round 3 on was a prototype sample in the design note:
a row whose panel had another item count, every dashboard row linked to one state, a "Где трудно" list that
needed attempts the 5-row list could not hide, cost rows opening states without cost, and finally samples that
#69's run composition made impossible. Each fix redrew samples in isolation, and the next round found the next
impossible pair. Round 6 passed once the architect rebuilt every sample from one dated timeline.
Rule: when a DESIGN brief asks for page work items with sample states, require in round 1 one sample timeline
(learner, lessons, checks, attempts with dates and costs) from which every state and every link target is
derived, checked against the run and counting rules of the flows it depends on; brief the judges to walk it.

### 2026-11-10: judge_ux rounds spent on doc claims nobody had measured on a fresh load (#72)

judge_ux on #72 took five rounds, each FAIL a single item: stale line citations after a merge, a missing
README member, gallery sizes copied from the wrong scale, an AC not split by release, and twice an
accessible-name claim (the plain item's name, the Проверки tab name) measured in a state reached by hash from
another state, so focus or markup from the previous state leaked into the measurement.
Rule: in the author brief, require every accessible-name and computed-style claim in acceptance notes and
flows to be measured on a fresh load in a new browser context per state, every AC to name the release whose
tester can see its states, and file citations by selector, never by line, once a branch has merged main.

### 2026-11-10: Eleven design rounds on one class, closed by one rule only in round 9 (#70)

judge_design for the quiz flows took 11 rounds. From round 2 on almost every blocker was one more case of "where does
focus go when an answer arrives and the learner is not on the panel": tab switch, Safari mouse focus on `body`, open
menus and dialogs, the idle warning, a control the answer removes. Each fix named the cases the judges listed, and the
next round found the next one. Round 9 replaced the cases with one R2 rule ("focus after a background change", a
fallback order per region) and the tail ended in two rounds. Rounds 3-4 were also spent on prototype mechanics traced
against a sibling task's unmerged proto.js; they went to the author phase only after Stepan decided it.
Rule: at the second FAIL of the same shape, brief the architect for one general rule over the whole class (list the
members, then one rule with a fallback), not the listed cases. Do not judge behaviour that depends on another
branch's uncommitted code in judge_design: state the required behaviour in the flows and test the mechanics in the
author phase, after that branch merges.

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

### 2026-11-09: Two optional README notes I asked for cost a judge round (#33 merge hotfix)

Round 1 of the merge hotfix failed on one ADR line. In the fix brief I also asked for two non-blocking README additions
(a TERMINAL_SHELL=/bin/sh fallback, a detailed #32 rollback list). Both were new procedure text that nobody ran end to
end, and round 2 failed on both.
Rule: a fix round after a FAIL carries the blocker and its class only. Non-blocking notes that add procedure text go to a
follow-up or are dropped unless Stepan asks for them, and any procedure text added gets the same run-it rehearsal as the
original steps.

### 2026-11-10: First architect brief carried my summary of the issue, not the issue (#101)

The first #101 architect brief retold the issue's fields in my words and dropped the definition of
`lastAttemptCount` and the Acceptance list. The architect, who has no shell, invented a definition and could not
map acceptance, so a whole revision went to restoring the issue's text before any judge saw the design.
Rule: before the first architect spawn, save the verbatim issue (body and comments) to `plans/<n>-issue.md` with
`gh issue view <n> --json title,body,comments` and point every brief at it; a summary in the brief is a pointer,
never the source.

### 2026-11-11: Advanced to compound before deciding the last code fixes (#101)

All three code judges passed with non-blocking notes, two of them false doc comments. I advanced judge_code ->
compound and only then asked Stepan whether to fix them in the PR; the coder window ends at judge_code, so the fix
had to move to a separate HOTFIX.
Rule: after the last judge_code PASS, decide every non-blocking note that touches product files (fix now with a
narrow re-judge, or a follow-up) with Stepan before advancing to compound.

### 2026-11-09: Design rounds spent on the test plan, not the fix (#112)

judge_design took three rounds (Stepan approved the third). The fix itself (shouldUpgradeCallback, no timer) passed
all three judges in round 1; every blocker after that was in the test plan: existing tests the new harness reroutes,
a mutation whose input never reaches the mutated line, a live-check layout that skipped Dockerfile COPY lines, and a
mutation recipe whose guards failed silently. Each would have shown up in one scripted run.
Rule: when a design prescribes mutations, a rebuilt image layout or a shell procedure, the architect brief asks for
(1) a trace of every mutation's input through the code to the mutated line, (2) a grep of every existing test that
sends a rerouted input, and (3) a dry run of each procedure, including every guard failure, before judge_design.

### 2026-11-09: Tiered from the issue's "<= 5 LOC" feel, then from the architect's estimate; both were low (#103)

#103 was labelled tier:hotfix. I picked TASK from a read of the code (readYaml plus three call sites), the
architect estimated about 95 lines, and the real diff was 170+/16- in three files (tests 106), so PROJECT by line
count. The phases match, so nothing was skipped, but the size reached Stepan only in the final report. The number
that was right came from the operations judge, who implemented the design in a scratch clone during judge_design.
Rule: when an operations judge implements the design in a scratch clone, take its `git diff --stat` as the size,
re-tier from it before planner and tell Stepan then if it crosses a tier. Count test lines: the tier table does.

### 2026-11-11: A focus rule took three design rounds, one neighbouring case per round (#106)

judge_design for #106 ran seven rounds (Stepan allowed the extra ones). From round 5 to round 7 every architecture
blocker was the same "Продолжить работу" focus rule: first the mouse path in browsers that do not focus a clicked
button, then a stale target after a click on text, then an outside press that moves no focus. Each fix closed the case
named and left the next one. Round 7 passed only after the brief asked for a full decision table over every input
combination with one invariant.
Rule: at the first FAIL on a stateful UI rule (focus, entry records, event ordering), brief the architect for the
decision table over all inputs and the invariant it must keep, not for the listed case.

### 2026-11-11: The tester brief left out ADR-0006's design conformance section (#106)

judge_code round 1 failed because the test report had no "Design conformance" section (ADR-0006 item 5: screenshots,
per-AC lines, token diff, contrast, raw colour grep) for a diff under the lesson page. My tester briefs listed
commands, e2e, mutations and Docker rules but not that section, and they did not ask the tester to explain the history
rewrites it ran after. A fourth stack run was then needed for the screenshots.
Rule: when a diff implements a page in design/pages, the first tester brief names ADR-0006 item 5 and asks for the
screenshots in the same stack run as the e2e suite, plus a section listing every fixup folded into history.

### 2026-11-11: main moved under the design, and the researcher ran before the first advance (#106)

Halfway through judge_design, main gained the quiz prototype (#138), which rewrote the lesson acceptance notes and
prototype the design cited; a judge found it only through a stale course count. Separately, I spawned the researcher
while the phase was still `init` and advanced afterwards; the gate did not stop it.
Rule: `git fetch` and compare origin/main with the branch base before every judge_design round and before the coder,
and re-base the design when design/ or the touched code moved. Advance the phase before spawning its role.

### 2026-11-10: Mutation rows prescribed by an architect with no shell cost a design round (#110)

The #110 architect brief carried the #112 rule (trace every mutation, dry-run every procedure), but the architect role
has no shell, so M12 and M17 were written from reasoning only. judge_design round 1 failed on both: busybox `kill`
rejects `--`, busybox `pkill -x sh` matches nothing, and a by-name kill hits the kill script's own `sh`. The operations
judge found each by running it. What did work: running the design's E0 experiment myself before judge_design, so the
judges reviewed measured premises instead of claims.
Rule: when a design prescribes shell-level mutations or procedures and the architect has no shell, have them run
before judge_design (the orchestrator for a read-only experiment in an own container, or the operations judge), and
pass the output to the judges with the design.

### 2026-11-10: A pre-decided rule measured a proxy, not the issue's own metric (#113)

The #113 design pre-decided that the workspace deploy mount stays only if deploy without it downloads packages.
pnpm printed `downloaded 0, added 0` both ways, so the tester dropped the mount, and the operations judge passed it
in judge_code round 1 on the same counter. The architecture judge then measured the deploy build-cache record: 117 MB
with the mount, 280 MB without, the very growth #113 exists to cut. It cost a revert commit, two re-tests and a
second judge_code round. Separately, judge_design took four rounds; rounds 2-4 were test-plan text and attribution,
and in round 3 the shell-less architect wrote "re-ran" results it could not have produced.
Rule: when a design pre-decides a keep/drop rule, the architect brief requires the rule to measure the issue's own
metric (here: build-cache record size per step from `buildx du --verbose`), with a negative control that shows the
metric moves. Every architect re-brief says: you have no shell; record only results a named run produced, labelled
with that run.

### 2026-11-12: A resumed judge cannot change its vote; a judge round sent only two judges (#130)

The operations judge of judge_design round 4 voted FAIL (CANNOT-CERTIFY: snapshot.ubuntu.com was down). After the
snapshot recovered I resumed the same agent with SendMessage; it reran and reported PASS, but the gate keeps one vote
per agent and round, so the PASS was logged as `vote-dup` and the FAIL stayed. A fresh operations judge had to re-check
the evidence. Separately, after two auto-mode classifier failures I re-sent judge_code with only security and
architecture; operations was missing until the third send.
Rule: a judge whose verdict must change is re-spawned as a new agent, never resumed. Before sending a judge round,
count the Agent calls in the message against the tier's judge list.

### 2026-11-11: A merge pass reopened a judged design and ran seven flow rounds (#72)

After #138 (quiz) merged, #72's PR conflicted in 41 hunks. The merge pass was meant to be narrow, but the
researcher made the quiz send an attempt record and every reader of attempt records had to be re-derived; seven
judge_design rounds followed, each FAIL one edge of the same class (run baseline, vocabulary, the lesson outcome
on a timed-out send, the send window). Two of those edges came from non-blocking notes the orchestrator folded
in, which widened a rule without following what it suppressed.
Rule: when two DESIGN tasks touch the same page, merge the second onto the first before its judge_ux, not after
its PR; in a merge pass, brief the architect to list every decision that goes beyond keeping both sides and put
each to Stepan before judge_design; fold a non-blocking note in only after asking what the changed rule suppresses.

### 2026-11-11: Four design rounds spent on a mutation procedure, not the fix (#129)

The #129 fix (listener error handler, graceful probe, readiness poll, peer on the other network) passed all three
judges in round 1. Every later FAIL was in section 5.1, the procedure for running mutation patches: patching the
real test file and restoring it (round 1: a partial patch left it mutated; round 2: the junk cleanup deleted four
tracked course/*.orig files and the restore trap fired on the exit meant to protect a fix), then a clone-based
rewrite whose leftover check missed the runtime's own objects and took the run id unchecked (round 3). Stepan
allowed rounds 3 and 4. The size also crossed the TASK line (diff 155+/37-, one file); I kept TASK because the
phases match PROJECT and said so in the report, not before planner.
Rule: when a test plan mutates a file that is in the pending diff, the architect brief prescribes from the start
that mutations run only in a throwaway clone (git clone --local into the scratchpad, git apply all-or-nothing,
leftovers listed with the harness's own selectors, run id validated), and the operations judge dry-runs that
procedure with negative controls in round 1. Name the tier change to Stepan when the architect's estimate crosses it.

### 2026-11-10: A judge_code brief let the operations judge mutate product files in the task worktree (#121)

The #121 judge_code round 1 brief asked the operations judge to spot-check mutation rows "on a copy". It mutated the
live files in the task worktree with `*.judgebak` backups, while the architecture judge was reading the same files; the
architecture judge saw `http/errors.ts.judgebak` appear and vanish and had to check its reads against the saved diff.
The tree came back byte-identical (cmp against plans/121-clamp-log-error-fields.diff), so nothing was lost, but a
crash mid-row would have left a mutated file in the diff to be committed, and parallel judges may review a mutant.
Rule: a judge brief that allows mutations names the place: a scratch `git worktree add` under the scratchpad (or a
copied tree), never the task worktree. Before commit, cmp the tree against the saved diff and check no backup files.

### 2026-11-10: A measured number lost its condition on the way into the ADR text (#117)

judge_design took three rounds (Stepan allowed the third). Round 1 failed on a researcher claim the architect copied
(a loader error reaching StarterRefusedError at starter.ts:112, where no YAML is parsed) and a missed caller
(export-course.ts in the image build). Round 2 failed on one parenthetical: the research measured "100 aliases to one
anchor", the design's ADR text said "100 aliases", and yaml's limit is per anchor with nesting multiplying. My own E0
probe printed "aliases 100" without the condition too, so my briefs carried the shortened form. The code, tests and
mutations passed every round; all three failures were prose stating a measured fact more broadly than it was measured.
Rule: when a design turns a measurement into doc or ADR text, the architect brief asks for each number to keep the
condition it was measured under (which input shape, per what), and for every claim about a caller or error path to be
checked against the cited line, not taken from the research. My own probe output labels its inputs fully.

### 2026-11-11: main moved twice while the merge follow-up was in review (#106 merge of #149)

The follow-up to make PR #151 mergeable after #149 was designed against 7aa5a6c. Before the tester finished, main gained
#140 (design/ and ADR-0007 only), the tester stopped at the append-only simulation, and the plan needed a delta and a
second merge commit that had no design round of its own (the code judges reviewed it instead). Each round of the follow-up
took about as long as the time between merges to main.
Rule: for a merge-of-main follow-up, `git fetch` right before the tester and right before the push, and write the merge
design so it already covers "main moved by docs-only commits": a further merge commit with the same checks, judged at
judge_code.

### 2026-11-16: Skipped the #110 rule and sent a no-shell architect's procedures straight to judges (#107)
The #107 design prescribed two mutation rows and two lockfile gates written without a shell. I sent it to judge_design
without anyone running them; the operations judge found a non-unique anchor (app.ts:8 and :52) and a placeholder age
check, and the round failed on procedure text, not on the change.
Rule: the #110 rule applies to every design with shell procedures, however small the change: before judge_design, have
the procedures run (operations judge dry-run or my own scratch run) and pass the output with the design.

### 2026-11-16: The briefed stack run's port was taken by a macOS service (#107)
The #107 tester brief named `isolated-stack.sh t32`; its web port 53081 was held by `/usr/libexec/rapportd`, so the tester
stopped before any build and a second tester round was needed for T5 alone (t31 had both ports free).
Rule: before a tester brief that runs isolated-stack.sh, check the run's two ports with `lsof -nP -iTCP:<port> -sTCP:LISTEN`
and name a run whose ports are free.

### 2026-11-17: Eight design rounds on one memory model, closed only by narrowing what the check reads (#45)
judge_design for module 05 took eight rounds. Rounds 1-5 each failed on the L2 memory check: every round found one more
memory source, setting or wording the model had to cover (AGENTS.md, CLAUDE.local.md, settings keys Claude Code writes
itself, note texts read literally). The lead's D9 ended the class: the check reads only the course's accepted places and
ignores everything else. Rounds 6-8 were wording only.
Rule: when a check models a vendor behaviour with an open-ended set of inputs (memory sources, settings, env), decide at
the first FAIL what the check reads and grade only that; never refuse or model "everything else".

### 2026-11-17: Student-phase anti-cheat loops in three lessons, each closed by one general rule found late (#45)
After the design passed, students found passing cheats in four rounds: L4 given-net weakening (static N1 forms, then
process isolation), L5 static gate classifiers (more twins, then a factorial probe set), L3/L4 oracle rewriting (OUT), L2
runner tricks (OUT). Each general rule (isolation, factorial twins, scope by effect) closed its class in one round; the
case-by-case rounds before it did not.
Rule: at the first student cheat in a check, ask which general rule closes the class by construction (separate
processes, balanced twins, scope cut) and brief the designer for that, not for the reported form.

### 2026-11-17: A transcript bug-hunt was measured blind only after two rewrites (#45)
The L1 bug-hunt was rewritten twice from sighted students' "tells" reports; a blind student who read only the transcript
and theory then passed on attempt 1, twice. The structural cause (a false claim must be visible in a transcript) was in
the design from the start.
Rule: for a bug-hunt over a transcript, run a blind reader (no code, no design) right after the first draft, before any
other student round, and treat its first-attempt result as the measure.

### 2026-11-17: An author without a shell estimated word counts, and a judge round failed on them (#45)
judge_content round 2 failed because the L3/L4 reading times came from estimated word counts; the author role has no
shell. Measuring with wc -w took one command.
Rule: when lesson text states measured numbers (word counts, line counts, file sizes), the orchestrator measures them and
passes the figures in the brief.

### 2026-11-17: Promised that a lower check weight changes completion without reading the progress ADR (#45)
D13's fallback asked to lower legacy-hunt's weight so passing could not rest on it; ADR-0007 counts every counted check
regardless of weight, and bug-hunt is not a counted kind yet. Caught before shipping and reported to the lead.
Rule: before acting on a lever (weight, limit, status) to change a learner outcome, read the rule that computes the
outcome (ADR-0007, progress flows) and state its real effect.
