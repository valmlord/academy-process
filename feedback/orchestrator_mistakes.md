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

### 2026-11-16: Comment rewrites dictated by the design passed judge_design and failed judge_code (#115)

judge_design round 2 passed a 6.0 table of replacement comments the architect wrote. Two of them (spec.ts:79-80,
:216-217) claimed more than the code: "nothing enters the create body" while Image, limits and labels come from the
config; "the only value from the service's environment reaches the shell" while TERMINAL_SHELL goes into Cmd. The coder
copied them verbatim, and judge_code round 1 failed on them plus two of the coder's own lines of the same class. The
#33 rule (no ready sentences from me) covered my wording, not the architect's. What worked: running the design's
/proc premises myself before judge_design (E0), so round 1 argued about text, not about unmeasured facts.
Rule: when a design dictates comment or doc sentences, the architect brief asks for each one the list of cases it
covers with the code line behind each case, and the coder brief asks the coder to re-check every dictated sentence
against the code and grep the diff for the same class (only, nothing, never, exactly, every) before the first commit.

### 2026-11-16: Merged PRs without checking main CI, and a known flake waited (#43, #130)
After merging I moved on without looking at the CI run on main. A green PR run does not cover the merge result, and
the e2e job on main had been failing on an Ubuntu mirror outage for hours before I noticed it.
Rule: after every merge, read the CI run of the new main commit to its end. A failure there is fixed or rerun at once,
and a known flake gets its issue the same day.

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

### 2026-11-17: Fifteen design rounds on one too-large design before splitting it (#163)
#163's design (service check runner) went through fifteen judge_design rounds. Most FAILs after round 4 were text drift in a
design over 3,000 lines: ADR sentences copied in many places, then narrowed in one; test cases dictated as code nobody had
run; an audit inventory of course graders inside a service design. Each class closed only after a structural move: one
source for the cleanup rule with pointers elsewhere, every dictated test case backed by a run sketch with named mutants,
the grader inventory moved to its own issue (#187), and the runner and stop handling split to #196. Splitting the PR at
the planner (A1 #163, A2a #198, A2b #199) came last, though the size was over the bound from round 1.
Rule: when the architect's first estimate is over the bound, split the issue before judge_design, not after; keep each
behaviour stated once in a design and point to it; never dictate a test case as code without a run that shows it green on
the correct form and red on its named mutant; move inventories of other code (course graders, other services) to their
own issue at the first FAIL about them.

### 2026-11-17: My own splice script truncated a file before reading it (#163)
While splicing revision 4o I wrote `open(p, "w").write(apply(open(p).read()))`: Python opens the target for writing (and
empties it) before the inner read, so coverage.md was truncated and the edit reported "OLD count 0". A backup made just
before let me restore it.
Rule: when a script rewrites a file in place, compute the new text first and write it in a separate statement; keep a copy
of every file a splice touches before running it.

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

### 2026-11-17: An offline leak scan missed the JSON-escaped body the e2e spec reads (#45)
PR #193 went red in the e2e leak spec: grader string literals with an escaped newline before `from unittest import mock`
formed the run `nfrom unittest import mock`, which only the RSC payload of a theory page carries (newlines there are a
backslash and n). content:validate has no fragment scan, and my offline scan rendered soft wraps but not JSON escaping.
Rule: an offline stand-in for the leak spec scans every learner text both raw and JSON-escaped with the spec's own
forbiddenFragments and FragmentScanner (plans/45-runs/leak_repro.mts); a grader writes generated source with real
newlines or one literal per line, never an escape followed by text. Follow-up: valmlord/academy#195.

### 2026-11-16: A flaky-fix calibration loaded the shared host far past what it can carry (#160)
For the #160 base control under load I ran, in my own pre-judge dry run, a Docker CPU hog of 48 busy loops (40 runs,
17:09-17:25 UTC) and then 96 busy loops (40 runs, 17:25-17:46 UTC), plus short dry runs at 96 loops (18:06-18:10 UTC),
on Stepan's 10-core MacBook Air whose Docker VM has 10 CPUs and also runs his `academy` stack and other sessions'
integration suites. Host loadavg1 during those runs was 90-370 (VM loadavg1 up to 103); the same afternoon another
session's 40 `yes` generators took the host to about 360 and an app crashed. The design (and I) bounded the hog by
container lifetime and traps, but not by what the host can carry; the result was also weak: 0/40 old reds at 48 loops,
3/40 at 96.
Rule: synthetic load on this machine is at most 4 generator processes, each under an EXIT/INT/TERM trap, with a
per-test-run timeout, a total budget well under 30 minutes, and an empty `pgrep` for the generator after each run,
reported in the tester output. A flaky fix's base control is deterministic first (inject the delay that opens the
race, e.g. a stubbed dependency that settles late); host load is at most a bounded regression check, never the proof.

### 2026-11-16: Five design rounds on an evidence procedure the fix never needed (#160)
The #160 product design (serialize exec resizes, hold input behind a pending resize for at most 2 s) passed every
judge from round 1 to round 5 unchanged. All four FAILs (round 1 and 2 operations, round 4 security) were in the
host-load base control: a pass rule a no-op fix could pass, a classifier mixing stale size with a slow shell, an
orphaned vitest worker, an unbounded hog lifetime, a budget enforced only in prose. Round 3 passed 3/3, and only the
shared-host load limit (40 `yes` generators crashed an app) and the main orchestrator's decision to delete the load
run ended the loop. The deterministic control (the runtime's resize stubbed to settle 1000 ms late in a throwaway
clone) had been in the design since round 1 and gave old 10/10 red, new 5/5 green on the real daemon.
Rule: for a race fix, ask at the architect brief whether a deterministic injection of the race window exists; if it
does, it is the base control and no load run is designed at all. When the same procedure class fails twice, delete
the procedure instead of hardening it, and ask the main orchestrator before a third round on it.

### 2026-11-16: Six judge_design rounds for a design-only accessibility fix (#99)
judge_design took six rounds (3, 4, 5 and 6 granted by the parent orchestrator under Stepan's standing instruction).
Round 1 FAILed on a silent quiz load while away; round 2 widened the quiz notice and missed its acceptance block;
round 3 replaced that with a panel status container and missed the Safari minimum age; rounds 4 and 5 failed only
on the author plan: stale counts, citations and copies of a DOM-order list that a grep would have caught. My briefs
named the files to grep but did not run the greps myself before sending the judges.
Rule: before every DESIGN judge round, run the mechanical pass myself and pass its output: print every plan
citation next to the cited line, grep every copy of each changed list by its class names and section title across
design/ (prototype.html, proto.css, proto.js, README.md, components.html, acceptance.md), and count state names
from the files. When a judge asks for a status message on one path, ask the architect at once whether the same
visible change on every other path is announced, so the fix is not found one path per round.

### 2026-11-16: Briefed a load-based stability plan on a shared laptop and kept it through three stops (#157)
My architect brief for #157 asked for base controls "under the same load" and named +40 `yes` as an example. Three
judge_design rounds then refined a load harness, and the tester's full-suite and paired runs stopped three times on
external spikes (other sessions, a Docker VM at up to 663 % CPU; host load up to ~360). The session that started this
one halted the runs after another app on Stepan's machine crashed. The control that settled both tests needed no
load: a forced-yield clock mock for AC6 and an injected 4 ms writeFile delay for starter-walk, both run in minutes.
Rule: For a flaky-under-load fix, brief the architect to find a deterministic control first (mocked clock, fake timers,
an injected per-call delay that makes the old code cross the timeout); synthetic load only when none exists, capped at
4 generators. After a load run stops on host noise once, switch to a deterministic control rather than redesigning
the load harness. Check sibling sessions' notes and `uptime` before any load run on this machine.

### 2026-11-16: Six design rounds, four of them on the tester procedure's prose, not the fix (#95)
The #95 fix (about 70 product LOC) had its focus rule settled by round 2 and confirmed for the whole class. Rounds 3-6
failed on text around the tester procedure: an incomplete hand-written list of what an isolated-stack run leaves
behind (rounds 3 and 4, same class twice), then one sentence crediting the final check with an image check it does not
do (round 5). I patched the list once before closing the class by measurement; the second FAIL of the same shape was
the signal I should have acted on at the first. Rounds 4-6 needed grants from the main orchestrator.
Rule: a design never states a side-effect inventory or what a check verifies without a line ref the judge can read; at
the first FAIL on such a claim, replace it with a measurement (read-only before/after snapshots run once before the
judges) instead of correcting the list. Size the tester procedure to the change: a 70-LOC UI fix does not need the
design to narrate the stack harness's teardown.

### 2026-11-16: A worktree judge wrote its lesson into the main checkout's process repo (#162)
In a Desktop worktree session the judge_design round 1 briefs said only "append the lesson to the responsible role's
feedback file". The architecture judge appended to `<main checkout>/.claude/feedback/architect_mistakes.md`, which left
an uncommitted change in main's process repo that this session cannot undo (the worktree hook blocks edits to main's
`.claude/`). The entry had to be copied into the worktree's process repo by hand and main's copy left for Stepan.
Rule: in a worktree session every judge and role brief names the absolute feedback path of the worktree's own
`.claude/feedback/` and says "never the main checkout's `.claude/`".

### 2026-11-16: Two judge votes of a round were never recorded (#162)
judge_code round 2 sent three fresh judges in one message. Only the operations vote was recorded; the security and
architecture spawns are missing from `judge_spawns` and their handbacks left no line in `.git/pipeline-hooks.log`
(host load 70-300 at the time, cause not found). The architecture report also ended with `PASS - no architecture
issues found` instead of a bare `PASS`. The gate kept the round 1 architecture FAIL, so a fresh architecture judge
was needed.
Rule: right after sending a judge round, check `status` for each new agent id in `judge_spawns`; re-send any judge
that is missing before waiting. Every judge brief ends with "the last line is exactly `PASS` or `FAIL`, alone".

### 2026-11-16: A clone decision was added as prose next to code blocks that still prescribe the worktree (#148)
The "Orchestrator decision" paragraph in 148-design 3.3 replaces `git worktree add` / `git worktree remove` with a
`git clone --local` and a guarded `rm -rf "$M"`, but the literal blocks in 3.1 step 1 and 3.3 still run
`git worktree add --detach "$M" HEAD` and `git worktree remove "$M"`, and the rm guard exists only as a sentence. A tester
running the blocks verbatim registers a worktree in the shared repo and runs a verb that is Stepan's; the rm has no
literal `${M:?}`/path check and is the form Claude Code's rm check refuses (architect_mistakes 2026-10-29).
Rule: a procedure decision is applied to the design's code blocks themselves (old lines removed, the guard written as a
runnable command) before judge_design, never as a paragraph saying which lines it replaces.

### 2026-11-16: Two judge_code rounds spent on comments that claimed more than the code does (#148)
The #148 test code passed every lane in round 1; architecture failed round 1 on the I-out-7b holder comment (it gave
#34's step order backwards and called a result "the one write") and round 2 on the TOKEN_SPENDING_KINDS comment (it
promised a new token-spending kind would turn P6 red, but P6 only draws kinds from KINDS). Both claims came from the
design text, so neither the coder nor I checked them. Before round 3 I had the coder re-check every added comment
against the line it describes, which found two more overclaims, and I caught a number that had lost its condition
("3.3 s test run" for a whole-file measurement).
Rule: the coder brief for any change with new comments asks, before tester, for a list of each added comment with the
code line or document line that makes it true; I read that list against the #117 rule (numbers keep their condition)
before sending judge_code.

### 2026-11-17: Dry-ran log-reading scripts against logs I wrote by hand (#180)
My judge_design dry run of the #180 read scripts fed them hand-made logs, so all checks passed, and I wrote down
"reporter format" as the one open premise. The operations judge ran the same scripts against a real #95 isolated-stack
log: turbo prefixes every e2e line with `@academy/web:test:e2e: `, so the anchored summary greps could never match, and
the read scripts would have failed every real run (and the t31 guard could never go red).
Rule: a dry run of any script that parses a tool's output uses a real captured log of that tool (a sibling task's run log,
or a short real run), never a hand-written sample; the brief names the real log's path.

### 2026-11-17: Asked for "a row for every line" and got a catch-all that stopped the happy path (#180)
After the round-2 operations FAIL (wrapper guard lines without a row) my re-brief asked the architect to list every line
and add a catch-all. The catch-all ("any output a row does not name -> stop") then covered the success output, and round 3
failed on that, the same class one step later. The #70 and #106 rules (at the second FAIL of one shape, ask for one general
rule over the class) applied already at round 2: the shape was "what does the tester do with this output".
Rule: for a tester decision table, brief the rule first: each step passes on its Pass criterion and moves on; it stops only
on named failure prefixes or a Pass not met; one fixed stop sequence after a stack run (leftovers, disk record, read, clean),
another before one. Rows only for the exceptions to that rule.

### 2026-11-17: Seven design rounds for a 5-line test fix, six of them on the tester procedure (#180)
The fix (one `waitForLoadState("load")` plus a comment) passed every judge from round 1 on, and the control passed its
first real run. Rounds 1-6 failed on the tester procedure: log format (hand-made dry-run logs), then the decision table
three times in a row (missing rows, a catch-all that stopped success, no precedence between the run line and the read),
then prose routes outside the table. The #95 rule ("size the tester procedure to the change") was in the file and I did
not apply it at init: I let the architect write a full state machine for a tester who could have reported outputs.
Rule: for a small fix with a stack-run control, brief the tester procedure from the start as "run these commands, report
every output, move on only on the named success lines, everything else comes back to the orchestrator", and keep
routing decisions out of the design. Dry-run log parsers against a real captured log before the first judge round.

### 2026-11-17: Three design rounds, two on how the tester counts, and a CI YAML line nobody parsed (#96)
judge_design round 1 failed on the mechanism (the container lookup accepted any non-owner web container) and on two
claims about hook and turbo behaviour; round 2 failed only on the tester procedure counting tests by grepping the list
reporter's log (its code frames reprint source lines) and on a count that left out the setup dependency. My own E9
dry run had already printed the wrong grep counts in round 2; I recorded them as an extraction defect instead of
sending them back to the architect before the judges saw them. In round 3 all three judges passed a CI step whose
`run:` line does not parse as YAML (a ": " inside a plain scalar); the security judge noted it as non-blocking and I
confirmed it with the yaml package. It went to the coder as plan constraint C1, not as a fourth design round.
Rule: when a dry run of a design block prints anything other than the design's pass line, it goes back to the
architect before judge_design, even when the cause looks like counting. Every criterion that counts tests or reasons
reads the Playwright/Vitest JSON report. Every YAML snippet a design adds to a workflow is parsed with the yaml package
before judge_design.

### 2026-11-17: init refused because the worktree's process repo was still on a merged task's branch (#96)
This Desktop worktree had run #162 before; its `.claude/` stayed on `fix/162-attempt-arrays` after process PR #32
merged, so `init` refused. I checked the PR was merged at the branch's head sha (`gh pr view`, `rev-parse`,
`merge-base --is-ancestor`), that `worktrees "<path>"` exited 0 and that the process tree was clean, then cut the new
process branch with `switch -c <branch> origin/main` and `branch --unset-upstream` (init then refuses a branch that
tracks main). The old local branch `fix/162-attempt-arrays` is left for Stepan's sync.
Rule: a reused worktree session checks `git -C .claude branch --show-current` before `init`; if it names a finished
task, prove the merge as in section 7 steps 3-5 before cutting the new branch, and name the left branch in the report.

### 2026-11-17: A docs-only design took three rounds on claims about what a scanner detects (#148)

judge_design for a 13-line comment and ADR fix ran three rounds (the third under Stepan's standing instruction). Both
FAILs were security findings of one class: a sentence about what the e2e leak scan does or does not detect, written as a
case (first at the title instead of every scanned body, then a "part of a run" absolute and a run length without the
trim). Round 3 passed once the architect wrote the detection rule once from the code (D1-D5) and derived every claim
from it per listed fragment. Separately, `init` refused because this worktree's process worktree still sat on a merged
task's branch; `git -C .claude switch --no-track -c <task branch> origin/main` (allowed verbs, clean tree, merged PR)
let init proceed.
Rule: when a design's deliverable is prose about the behaviour of a matcher, filter or gate, the first architect brief
asks for the mechanism written once with file:line and every claim derived from it, before any judge round. Before
init in a reused worktree, check `git -C .claude branch --show-current` and the PR state of that branch.

### 2026-11-17: A step moved out of the task took the evidence an AC still needed (#150)
In judge_design round 4 the orchestrator decided to drop the E-reset destructive-colour capture (a race-prone step the
architect had added in round 3) and to move it, together with the diff-scoped raw-colour grep, to follow-up #192.
The grep was evidence for AC16 "tokens only (no raw colour)" and ADR-0006 item 5 in #150's own diff; only #150's tree
can show its added lines carry no raw colour. Round 4 failed 1/3 on exactly that gap. Earlier in the same task,
recording decision C/A only as a new section 17 left option B live in steps 6, 7b and 10, and round 2 failed on it.
Rule: when moving a step out of a task, move only what it does, not the evidence an acceptance item still needs, and
re-check each AC that cited that step before the next judge round. A decision is applied by having the architect
rewrite every section it touches, never by appending a decision section.

### 2026-11-17: A fix round added an unasked step and the next round failed on it (#150)
The round-3 architect brief listed the round-2 findings to fix; the architect also added, unasked, an in-app capture
of the destructive button colours for tester.md item 7. Round 3 failed on that step alone (a theme read that races the
matchMedia listener and a 150 ms transition). judge_design took five rounds for a design whose mechanism passed from
round 1.
Rule: every architect fix-round brief says "fix only the listed findings; anything else you think is needed comes back
to me as a question, not as design text", and the orchestrator diffs the round against the previous copy before the
judges see it and sends back any change no finding asked for.

### 2026-11-17: A blanket sed of the follow-up placeholder broke the design's own guard check (#118)
The #118 design used `#<F>` for a follow-up number the orchestrator was to file. After filing #188 I ran
`sed 's/#<F>/#188/g'` over the whole design, which also rewrote the coder's "must print nothing" check
`rg '#<F>|until #118|...'` into a pattern that matches the three `#188` references the design requires. Two judges
failed judge_design round 1 on it. My dry-run extractor also wrote the wrong block to dry/tools/mutate.py.
Rule: never fill a placeholder in a design with a blind global replace; hand the number to the architect, or edit
each occurrence and grep the result for every check that names the placeholder. Diff any tool file extracted
from a design against the design block before using it.

### 2026-11-17: Design round 1 sent a red/green procedure to judges unrun (#197)
judge_design round 1 failed 1/3 on the control procedure only (a grep literal that could never match the printed
title, a one-shot abort spent before the judged wait, an unplaced import, stages the control also hit). My dry-run
checked anchors, not outcomes. Round 2 passed operations after I ran control run A for real in a scratch clone and
handed the judges its log; round 3 (approved ahead by the orchestrator session under Stepan's standing instruction)
fixed one misclassified "no change" row that run A's own log had already shown failing.
Rule: before judge_design, run the "red without the fix" half of any control procedure for real in a throwaway
clone and pass the log; read every failure in it, including tests the design marks "safe", before the judges do.
Also: a reused worktree may carry a stale process branch; init refuses it. If that branch is clean and has no
commits past process origin/main, `git -C .claude switch --no-track -c <task branch> origin/main` lets init proceed.

### 2026-11-18: A plan split put a test row in a commit before the code it calls (#198)
The #198 plan put the check create body row of the `exec.test.ts` `it.each` into the A5 commit, but `createExec` accepts
that body only from A6, so A5 alone failed typecheck (TS2345) while lint and units passed. The coder caught it; the four
unpushed commits were rebuilt with cherry-pick so each typechecks. Separately, judge_design round 1 failed on one test
observable copied from the parent design unmeasured (M20); round 2 passed once the brief asked for every fake-daemon and
attach-double case to be measured (REPEAT=5 green, named mutant red), which found two more rows that did not hold.
Rule: when a plan splits work into commits, check each item's tests against what that item's own code accepts (types
included), not only the step that owns the test file. When a judge fails one dictated observable, the fix brief asks for
every observable of that kind to be measured, not just the failed one.

### 2026-11-18: A reused worktree folder still held the last task's process branch (#137)
The #137 session started in the folder of #118's worktree. `init` refused: the process worktree in it was still on
refactor/118-yaml-helper (PR merged, Stepan's sync not yet run). `git -C .claude switch -c fix/137-aria-live origin/main`
and `branch --unset-upstream` made it usable and left the #118 branch for the sync. Separately, the issue's fix had
already landed in #151; the researcher found it, and the task became test-only. Without that read the coder would
have had nothing to change and the tier would have been wrong.
Rule: in a reused worktree, check `git -C .claude status -sb` before `init`; if it is on a merged task's branch, cut
the new process branch from origin/main with `switch -c` and unset its upstream, then tell Stepan the old branch
still needs his sync. Before tiering a bug issue, check with `git log -S` whether the change is already on main.

### 2026-11-17: A dry-run fixture I wrote by hand broke a design check, and a control premise went unrun (#201)
Before judge_design I saved the probe dry run as plans/201-dry-probe.log with my own annotation lines, and the design
used it as a raw monitor log in its local scan checks. Plan constraint C3 (any non-record line fails closed) then made
those checks return 2 instead of 1 and 0; the coder stopped and asked. Separately, the D-red control (JavaScript off)
rested on the premise that not-found pages reach their waits through SSR-only asserts; nobody ran a JS-off page load
before the judges, and in CI the streamed not-found boundary never swapped in, so 4 of 51 sites failed before their
wait. judge_design also took three rounds, the last two on tester decisions still made by reading.
Rule: a fixture that a design check reads is saved as the tool's raw output, never with notes in it; notes go in a
separate file. A red control's premise about what each target page does under the control is checked once for real
(or listed as unverified per site) before judge_design. When a judge names an example of "decided by reading", ask
the architect to sweep every decision of that class, not only the examples.

### 2026-11-18: A failure row and its residual took two extra design rounds (#181)
judge_design passed 3/3 in round 3. Round 1 failed on two gaps: the 20-run real-daemon control judged runs by the
JSON report, which vitest writes before the global teardown, so a teardown failure or a timeout still read as a
pass; and failure row F8 claimed a re-create had "the same outcome as today's caller retry", missing that the
retry re-ensures the volume and that Docker auto-creates an absent mounted volume without labels. Round 2 failed
on the size of the residual left after the volume guard: "milliseconds", while the window runs until the daemon
takes the volume reference after creating the container layer. The size of the task was also misjudged: the TASK
tier was set from the researcher's 2-4 files and under 100 lines, but the diff came to 5 files, +391/-72, mostly
the deterministic stub tests.
Rule: a control that runs a test process decides each run by the exit code as well as the report, and lists
leftovers and the owner set afterwards. A design row that says "same as today" names the code path it compares
with, and the architect checks that each step of today's path also happens in the new one. Any time sized in a
residual is derived from the anchors that end the window, never estimated. Count test lines in the tier sizing.

### 2026-11-18: An "optional" item in a rework brief cost judge_ux a third round (#136)
judge_ux round 1 failed on one gallery padding issue. My rework brief also passed on a judge's optional nit ("say the
first tree fits with zero slack, or leave it"). The ui-designer measured it in Playwright's default Chromium, which
hides scrollbars, and wrote a 9px margin as fact. Round 2 failed on that line in two judges, because AC75 and README
measure with classic scrollbars, where the tree overflows. The class sweep in round 3 then found a page-width claim in
acceptance.md that was false for 30 tall states in the same setup.
Rule: a rework brief carries only blocking findings and items a judge made a condition; optional nits wait for the
next real edit. Any brief that asks for a measured layout claim names the engines and scrollbar mode the page's
acceptance notes use, and asks for that setup to be stated next to the number.

### 2026-11-18: Two design rounds patched test-plan Docker writes one by one instead of closing the class (#176)

The #176 fix (one file, 12+/2-) passed all three judges in every design round. Rounds 1 and 2 failed on the test
plan only: security found a write to a Docker object the run did not create twice (r1 a `docker tag` onto the shared
name academy-web:t31, r2 a recovery step triggered by a later listing that could tear down another session's
academy-t31 stack), operations found reset and naming defects in the shim procedure. My r1 brief asked the architect
to patch the one write the judge named, so the next write of the same kind appeared in r2. Round 3, approved by the
main orchestrator, closed the class structurally: a fully fake docker shim with no delegation path, no real
isolated-stack run (t31/t32 are hard-coded and shared), nothing removed, the real run stated as a residual in the PR
body. It passed 3/3, and judge_code passed 3/3 in round 1. A delegating shim also meant that even the script's own
`compose down` of academy-t31 under the shim was a real write to a shared project.
Rule: when a task's test plan for isolated-stack.sh (or any script on shared t31/t32 names) needs Docker, the
architect brief prescribes from the start that failure paths are proven with a shim that answers every call itself,
and that a real run happens only under a tag unique to the run; if the script cannot take one, the real run is a
residual. When a judge names one instance of "acts on objects the run did not create", brief the architect to remove
the class, not the instance.

### 2026-11-20: #222 issue text lists the #218 assumptions it builds on without Q4, after round 8 tied Q4 to #222 (#218, judge_design round 8, consistency)
`courses.md:119-120` says "The error states of #222 build on Q1 to Q4 and Q9", and Q4 (`courses.md:132-134`) ends
"(failure cases: see #222)". `plans/222-comment.md:15` and the posted #222 body say "Q1, Q2, Q3 and Q9". The two
statements of what #222 depends on disagree; a #219 decision against Q4 would not be traced to #222 from the issue.
Rule: When a rework changes which #218 parts point to a moved-out issue, re-read that issue's scope text (the plans
comment and the posted body) against the design and update both in the same round.

### 2026-11-24: Two judge phases spent extra rounds on one class each, and an author phase had nothing to draw on (#222)
judge_design took three rounds: rounds 1 and 2 failed consistency on pointers added next to main sentences
that the new rule left false, and on a twin sentence left unscoped after its pair was fixed. Round 3 passed
only after Stepan chose to delete the three failing sentences instead of rewriting them. judge_ux also took
three rounds: the author renamed kept prototype states with a script, which broke an ia.md pointer, split one
id across two pages and, after the round-1 sweep, still left the old id in an HTML comment. Separately, #218
merged without an author phase, so #222's author phase had no several-course prototypes to draw on and the
task waited for #233.
Rule: a flow sentence a judge fails twice in one class is deleted, with at most a bare id pointer, before it
is rewritten. Before judge_ux, run a two-way state id check (every cited id in comments, notes and flows
against the declared states, and every declared state against its States row) and pass its output to the
judges. A DESIGN task that changes pages does not leave the author phase to another issue without one filed
first.

### 2026-11-24: Rewrite briefs kept a DESIGN task in judge rounds for days; deletion briefs closed it (#71)
judge_design took five rounds and judge_ux three. Rounds 1-2 failed on the same two classes (a state the rules
did not cover, and old sentences an extended rule made false), because each rework brief asked for the failing
place to be rewritten, which added new sentences that the next round failed. From round 3 Stepan's rule was to
delete the failing place instead (drop the review's budget dialog, the mentorAfter threshold, the stale-tab cases,
the hint cost in the total) and keep each removed need as a one-line obligation in the repo
(`mentor.md` "Not designed in #71"); every later round was a byte diff of a few lines plus a grep of every place
naming the touched string, and three of the four later rounds failed only on one leftover sentence. Separately,
`gh issue comment` was denied in this session by the permission classifier, so obligations meant for the issue
had to live in the design.
Rule: In a DESIGN rework, brief the role to delete the failing rule or sentence and record the need as an
obligation, unless the issue cannot be met without it; pass the judges the byte diff against the last round and a
grep of every place that names each touched string or control. Keep obligations in the repo, not only in an issue
comment that may not be postable.

### 2026-11-23: An ADR amendment specified log lines one by one and cost a third design round (#219)
judge_design round 1 failed 3/3 (course id rule only for URL ids, a "required" CI job that GitHub does not enforce,
a replaced sentence named by ordinal, a renamed course directory with no operator signal). My round-1 brief asked the
architect to name a log line for every operator-invisible state; round 2 then failed on the same class, because the
#220 test list did not pin each of those lines. Stepan chose to cut: the amendment now holds one obligation of #220
(decide, document and test what an operator sees; no user id, no file contents) instead of per-line text, and round 3
passed 3/3. Separately, all three round-1 judges lacked a shell and could not read the issue body; from round 2 the
brief quoted the issue bullets.
Rule: an ADR states decisions and constraints on log lines (what must be distinguishable, what they never carry), not
the lines themselves; the implementing issue owns and tests the exact lines. When judges cannot run `gh`, the brief
quotes the issue text they must check against.

### 2026-11-21: A test-only task spent four design rounds on its own evidence harness (#206)
#206 adds one Playwright test (the AC51 reset dialog case). Every judge found the test itself sound from round 1.
All seven FAILs over four rounds were in the test plan: first in predicted red sets, then in a log-reading script
with eight checks and a dozen self-tests whose expected vectors kept being incomplete, and in round 4 in a closed
image fetch list whose grep missed the line forms tester.md names. My round-1 brief asked the architect to make every
read check provably able to fail, which grew the harness the later rounds failed on. The orchestrator then removed
the harness (round 4: two quoted runs, green and one mutation), and round 4 still failed on the one closed list left.
Rule: for a test-only task, brief the architect from the start for the smallest evidence that decides it (a green
run and one named mutation, with the relevant runner output quoted), not a script that grades the logs. Any closed
list the plan keeps is checked once against a real log of the same recipe (another session's log counts) before
judge_design.

### 2026-11-21: A lost design cost six design rounds, most of them on ADR text for other issues (#199)
#199 was written to implement rev 4o of the #163 design "unchanged", but that design, its ADR sweep and its sketch
suite lived only in git-ignored plans/ of removed worktrees, so the task became a rebuild. judge_design took six
rounds: r1 0/3 (same-uid attacker, observables decided by reading, procedure 21 comparing other sessions' objects),
r2 2/3 (restart cost missing, a #230 gate red on main), r3 2/3 (paste block unfenced, lock read order), r4 1/3 and
r5 2/3 (the lock protocol dictated for #196 deadlocked on the non-reentrant KeyedMutex and then banned only one call
shape), r6 3/3 once Stepan moved the protocol into a #196 obligation. The code-PR part was stable from r3 on and passed
judge_code 3/3 in round 1. What worked: a researcher measuring the design's forms in a throwaway clone between
rounds, running every gate on main with its seed before a round, rendering paste blocks with `gh api markdown`, and a
byte snapshot of the design before each architect rewrite (the architect role has Write only) so the diff proved the
edit stayed in scope.
Rule: a design that other issues build on is posted to its issue as soon as it is approved, not left in plans/.
When an issue's design would dictate behaviour another issue owns (a lock protocol, a route), state it as a named
obligation with constraints from the start instead of as ADR text. Before handing a design to an architect for a
targeted edit, snapshot the file and diff afterwards; give judges the diff.

### 2026-11-21: Two design rounds on a dictated comment that listed which actions change a box (#216)
judge_design passed 3/3 in round 3 (approved by the main orchestrator). Rounds 1 and 2 failed only in architecture,
both on the same sentence in the dictated `scrollable-code.tsx` comment and its Verified and F6 echoes: a list of user
actions that do or do not change the `pre`'s box. Round 1 claimed the one-pane switch and zoom change it; round 2
claimed the one-pane switch never does, false at viewport height <= 30rem with classic scrollbars. My round-1 brief
asked the architect to fix that line and sweep comments for overclaims, so the rewrite produced a new, narrower list
that was again wrong in one corner. Round 3 dropped every list and stated only the mechanism (the observer reruns on
any box change; a remount decides afresh), and judge_code passed 3/3 in round 1. The size was also misjudged: TASK
by the issue, 8 files and about 360 lines with tests.
Rule: when a dictated comment or failure row enumerates cases ("X, Y and Z change the box", "W does not"), brief the
architect from round 1 to state the mechanism the code relies on instead of a case list, unless the list is
exhaustive and each case is checked against the code that sizes the element. Count test lines in the tier sizing.

### 2026-11-24: A sentence I moved "to remove ambiguity" was also the scope of the rule it left (#233)
judge_design round 5: the architect's cross-check relied on "In-page anchors keep the state; sign-in has no release
form." applying to every state, but the sentence sat inside L1. I briefed moving it into the LT paragraph. That
sentence was also what limited L1 to cross-page hrefs, so after the move L1 ("an href of a past or kept state to a
catalog module section opens its default state") covered the in-page module list of the kept catalog states too,
the opposite of the LT sentence. Consistency failed the round on it; usability and accessibility passed.
Rule: before moving a sentence out of a rule, read the rule without it and check its scope did not widen; when a
rule needs a scope, state it in the rule itself ("on another page"), never by a neighbouring exception.

### 2026-11-24: Six design rounds on link targets, closed by a parsed two-direction anchor check (#233)
judge_design took six rounds, every FAIL from round 2 on in one class: where a state's links go (shared top bar,
kept-state lesson links, prerequisite links, pointers that covered no anchor, a moved sentence that widened L1).
Each rework fixed the named links and the next round found the next one, because the tables were checked by
reading. What closed it: running the consistency judge's parser (each a[href] / [data-goto-state] by data-state
scope, per state) and checking two directions against the LT tables: every anchor has exactly one rule, every rule
cell covers an anchor. The author phase reused it per page and judge_ux needed two rounds, the second only for state
globs (`attempts-*`) that a new state had joined.
Rule: when a DESIGN task assigns link targets per state, give the architect the parsed anchor list from round 1 and
require the two-direction check before the first judge round; in the author brief, require a sweep of every state
glob and counted list in acceptance notes against the page's data-state-label set.

### 2026-11-23: An ADR that paraphrased a parser took five design rounds (#135)
judge_design for the task.md quiz threshold check passed only in round 5. Security passed every round; the other
failures were nearly all one class: the ADR-0001 item 6 amendment described the reader in English (which words a
count may hold, how lines are trimmed and sentences split, "the form" of the sentence, which counts pass unchecked),
and each rewrite drifted from the regexes while its sweep table said "exact", because the expected column was taken
from the code. My round 1 brief asked the architect to make the ADR "name exactly what the code matches", which set
up the paraphrase. Stepan's fix was to delete every sentence that described the reader and name the code and its
fixture table as normative. Separately: in round 2 the architect ran a prototype outside the workspace with
`pnpm exec`, which did a lockfile-less install into the worktree (vitest 5.1.1) that git status could not show; and
the TASK tier was set from the issue while the change came to about 1 200 lines, most of them fixtures.
Rule: when a contract or ADR text covers parser or matcher behaviour, the brief says from round 1 that the text
states only the author-level rule and names the code and its test table as normative, with no description of
phrasings, tokens or residuals. Any prototype run outside the workspace calls the workspace's binaries directly,
never pnpm, and each run logs the tool version next to the lockfile pin; judges each work on a private copy.

### 2026-11-24: A tester grep in my design brief could not see the process repo (#221)
judge_design round 1 failed 0/3. Operations and architecture both found that T1, the stale-pointer grep, ran
through the agents' `grep`, a ugrep shell function with `--ignore-files`, so the product `.gitignore` line
`/.claude/` hid every process-repo hit; a count check also passed before any edit. Security found that the course
id taken from issue text had no accepted form. Round 2 passed 3/3 after `command grep`, exact-line counts that read
0 before the change, and a two-sentence form rule in `_contract.md`. judge_code passed 3/3 in round 1.
Rule: any grep that must search `.claude/` from the product root uses `command grep` (or `git grep` per repo), and
the brief asks for each check's output on the unchanged tree, which must differ from the expected result.

### 2026-11-24: A plan item dictated a comment's reason I had not checked against the code path (#220)
judge_code round 1 (architecture) failed on the doc comment of `firstReadableCourse`: it said the non-slug and
`.: no course` results log no per-request line because the startup recompute and the export report such a root.
The coder copied that reason from my plan item P2, which I wrote from a judge's non-blocking note. For `.: no course`
it is false: that result comes from a `pnpm dev` race after the listing, which neither startup nor the export sees.
Rule: a plan item that dictates a comment states only the guarantee the code gives; a reason or "reported by" clause
goes in only after I traced the path that produces the case, otherwise it is left out.

### 2026-11-24: A design size estimate missed by 70 % on test lines, after the issue was already split (#220)
The approved design estimated about 1470 lines (480 source, 990 tests). The code came to 2479 (857 source, 1622
tests, fixture and fakes): new test helpers, page tests that need mocks of server components, and adapting every
existing test to the renamed fixture were not in the table. The orchestrator accepted one PR because the core commit
could not be split without breaking callers. judge_design went 3 rounds (all FAILs on obligation text about other
issues, closed by a sweep to bare pointers), judge_code 2 rounds (one false comment reason from my plan, one dead
test buffer).
Rule: a size table counts test helpers, mocks and adapted existing tests as their own rows, and when the estimate is
within 20 % of the bound, treat it as over and name the split before judge_design.
