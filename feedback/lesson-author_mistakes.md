# lesson-author mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

### 2026-11-17: Reading times re-derived from guessed word counts, printed to the learner as facts (#45)

Round 1 asked to re-time the L3 and L4 reading lines on one basis. The author stated 200 words a minute but took
the inputs from a judge's rough estimate and an older student count: L3 "около 4 300 слов" (actual about 3,370),
L4 "около 6 000, из них около 3 000 блок урока 3" (actual about 6,440 and 2,450). The minutes followed the wrong
inputs (L3 22 instead of 17, L4 15 after L3 instead of 20), so the inversion the fix was meant to remove stayed.
Rule: A word count or minute figure printed in task.md is counted on the file as it now stands (with `wc -w`, or
Grep `\S+` offsets when there is no shell), never copied from a review or an older run; if you cannot count,
say so and do not print the number.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### 2026-10-28: Mode summary listed what bypassPermissions still stops and left out deny rules (#15)

L6 theory.md:70 said "`bypassPermissions`: выполняется всё, кроме ask-правил и немногих защищённых
действий". permission-modes says "Deny rules block in every mode, including `bypassPermissions`", and
the module's own reserve quiz says deny works in any mode. "защищённых действий" also clashes with the
docs' "protected paths", which bypassPermissions does allow writes to.
Rule: When a one-line summary says "everything except X", copy the full list of exceptions from the
source (here: deny rules, ask rules, the actions no mode auto-approves) and use the docs' own terms.

### 2026-10-30: Student unclear places left open in theory; a quiz key not taught (#41)

L2 theory.md:102-110 warns that a tests-based `verify` changes the meaning of the bundled `/verify`, and
the task then requires exactly that skill, with no sentence on why. Quiz option "skill hooks register on
invocation" (quiz.yaml:61) is in the correct set, while theory.md:126 says only that skill hooks last
until the session ends. Student B flagged both in round 1; rounds 2-3 fixed other items and left these.
Rule: After each student round, walk every "unclear" item and either change the text or record why it
stays; and read every quiz key option against theory sentence by sentence: each part of a correct option
(here "when") must be on the page.

### 2026-10-30: A summary row widened a source rule; a quote was moved next to the wrong subject (#41)

L1 theory.md:157 (Stop outcomes table) says exit 0 with "объект без `decision`" ends the turn. The hooks
reference says `hookSpecificOutput.additionalContext` on Stop is not a block, yet "The conversation
continues so Claude can act on it"; the research addendum (A2) had that sentence. L4 theory.md:23-25 puts
the Spec Kit README sentence "These are independent entry points, not mandatory phases." right after the
command list, so it reads as a statement about the commands. In the README it follows the table of
processes (Spec-Driven Development, Bug fixing, Idea assessment, your own process); the research said
"its processes". The agentic-sdd reference says the commands "are designed to run in order".
Rule: When a table row or summary uses a broader condition than the source sentence ("object without
X"), list every documented field that changes the outcome under that condition. When you quote a
source, keep the quote attached to the subject the source attaches it to, and re-read the sentence
just before it in the source.

### 2026-10-30: Student ambiguity and time overrun left neither fixed nor recorded (#42, judge_content round 1)

Student A flagged L1 R06 as readable as `code` at step 4 ("remove the misleading thing: delete a dead module"), against
a `check` key with 3 binary submissions; no sentence was added and nothing recorded it as accepted. Student A also
estimated L2 at 85-90 min against 75; the design's named fallback was not applied and the estimate was not changed.
Rule: For every student "ambiguous" item on a capped binary check, add the sentence that decides it or record why it
stays; for every time overrun, apply the design's fallback, change `estimatedMinutes` and the task.md breakdown, or record
why the number stands.

### 2026-10-30: Own examples presented as a cited author's examples (#42, judge_content round 1, accuracy)

L1 theory.md:27-33 says Böckeler's guides are "файл памяти, документация, типы, понятные имена". Her article lists
AGENTS.md, Skills, codemods (OpenRewrite), LSPs, architecture docs and how-tos as guides. She names type checking only
as a computational sensor, and the lesson's own line 37 says so too.
Rule: In a sentence that starts "<Author> делит/называет/пишет", give only examples the source gives. Put your own
examples into a sentence the module owns ("В терминах этого модуля ...").

### 2026-10-30: New round-1 fix text widened facts past the cited page and overstated a rule (#42, judge_content round 2, accuracy)

L4 theory.md:185-187 says the WebFetch preflight runs "куда бы ни шли запросы к модели" and that
`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` does not stop it. That is true, but only data-usage says so, and data-usage was
not in `sources`. The cited network-config names only Bedrock, Vertex, Foundry and the Claude apps gateway. The quiz key
then depended on the unlisted page. L4 theory.md:110-112 says excluded commands "всегда" run outside the sandbox "даже
при false". The same sandboxing page says a `false` from managed settings or `--settings` makes the sandbox
admin-required and ignores the repository's `excludedCommands`.
Rule: When a fix adds a sentence, find the page that states it, add that page to `sources` if it is missing, and read
the whole section of the cited page for exceptions before you write "всегда", "любой" or "куда бы ни". This matters most
for scopes you named in the sentence before.

## 2026-11-04 #43: a `\uXXXX` example lost its backslash on edit
L3 task.md showed a JSON escape example as a plain `A`: the Edit/Write tools decode a literal backslash-u-hex sequence in
their input into the character. Two passes "restored" it without checking and it stayed wrong.
Rule: after writing any backslash escape into lesson text, confirm the bytes (Grep for the literal, or ask the
orchestrator for `od -c`). Escape the backslash itself in the tool input when the tool decodes it.

### 2026-11-11: A student readability point grew through fix rounds and was never decided (#43, judge_content round 1, pedagogy)
plans/43-student-l4-final.md friction 1 said the L4 task.md "Как проверяется" material bullet was about 30 lines in one
list item and asked for a sub-list. student-l4-final2 reported it "unchanged". Neither the author pass nor "Not
applied" in plans/43-w4-report.md mentions it, and fix rounds kept appending sentences to the same item (task.md:170-193,
now one 24-line bullet). The rule an honest learner most needs there (synthesizer and summarizer: `file`/`line` next to
`id`) sits at its end, after the section-only place rule. This repeats the #42 entry above for a readability item.
Rule: when a fix round adds a sentence to a check-behaviour paragraph, re-read the whole paragraph as the learner sees it
after an F-line, and keep one rule per bullet. Every student readability point is applied or listed under "Not applied"
with a reason in the round's report, even when the student called it non-blocking.

### 2026-11-11: Two verbatim doc quotes no longer exist on the cited pages (#43, judge_content, accuracy)
L2 theory.md:73-74 quotes structured-outputs as "A result can also end with subtype `success` but no `structured_output`
value ... Treat that case as a failure as well." The page now says "A `success` subtype doesn't by itself mean the run
produced an answer. Treat a result as a failure when the result's `is_error` is `true` or `structured_output` is absent".
L4 theory.md:130-132 (and lesson.yaml:20) quotes "Delegation saved money in only two situations, in measurements with
workers on Claude Sonnet 5, an earlier model". The page now says "In Anthropic's measurements, delegation came out ahead
in only two situations", and only the first (routine work with a long cost tail) is "on earlier models"; the second (work
larger than one context window) is measured with Opus 5.5 and Sonnet 5.5 subagents. Both quotes were right at research
time (2026-11-03) and drifted; nobody re-fetched them before the final round.
Rule: before hand-back to judge_content, re-fetch every page the lesson quotes verbatim and diff each English quote
against it. For agent-tooling pages a checkedAt older than 7 days is a re-check trigger. Update the qualifier around a
quote (model names, "earlier models") together with the quote.

### 2026-11-10: Student timings, a reversed course rule and REQ numbering left as they were (#44, judge_content round 1, pedagogy)

The student timed the three parts the design judges had flagged twice: L1 examples 35-45 min against 25, L4 handlers
with validation 60-90 against 35, L3 local time 20-25 against 15. No `estimatedMinutes`, no task.md breakdown and no
load-reducing line changed, and nothing records why the numbers stand. The same entry of #42 above already asked for
this. L5 task.md:54-59 was changed to accept the reserve form (student R2-B1), but theory.md:158-160 still says "курс
её не принимает", and the lesson outcome still says the delay sits "внутри одной атомарной секции". The REQ numbers of
the reference spec in every theory.md (L2-L8) and in L3 task.md:34, and the starter cases' `"req": [..., "REQ-05"]`
under "можно перенести свою работу", were flagged by the student and neither fixed nor accepted.
Rule: Before hand-back, walk the student reports item by item and mark each one fixed (file:line) or accepted (where
recorded). When task.md changes a rule, grep theory.md, lesson.yaml outcomes and module.yaml for the old rule and
change them in the same edit.

### 2026-11-10: L5 theory states a course rule the check no longer enforces (#44, judge_content round 1, accuracy)

05-api-bookings/theory.md:158-160 says the form "reserve under the lock, wait outside it, then write" "курс её не
принимает ... иначе пробы не отличат её от гонки". task.md:54-59 (changed after student R2-B1) says the reserve form
with a waiting conflict is correct, and student report 2 measured it passing booking-integrity 20/20. So the theory
sentence is false about the check, contradicts the task of the same lesson, and its reason ("the probes cannot tell
it from a race") is also false: the probes tell it from a race and accept it. theory.md:27-28 and the lesson.yaml
outcome still define the seam as "внутри той же атомарной секции".
Rule: A sentence about what a check accepts is a factual claim about the check. When a task.md rule changes, grep
theory.md, lesson.yaml outcomes and the quoted check messages for the old rule and fix them in the same edit.

### 2026-11-16: Exit-code summary said "any other end is counted" and dropped the ADR's uncounted platform ends (#146, judge_content round 1, accuracy)

docs/course-reference.md "Command check exit codes" says "Any other end is a counted failure: ... and a grader or
platform fault after the grader has started (ADR-0007 decision D11)". ADR-0007 rule 3 (:307-310, :316-322) keeps two
uncounted `error` ends outside 0 and 3: any failure before the grader started (`pre-start: <stage>`), and a stop the
platform issued and recorded after the start (`platform-stop: service-stop`, `web-restart`); D11 (:323-324) covers
only "a genuine platform fault ... that is not such a recorded stop". `classifyResult` maps `not-started` and
`platform-stop` to `error`. The research's suggested wording (findings section 6) already left the exceptions out.
Rule: When a summary of a rule says "any other" or "every", read the whole rule for its exceptions (here every bullet
of rule 3 and every `case` of `classifyResult`) and either list them or narrow the sentence to the cases it covers.

### 2026-11-17: L4 re-prints L3's rule block silently, reading timed on two bases, one student item dropped (#45, judge_content round 1, pedagogy)

L4 task.md:174-311 repeats L3's T1-T9, T4, course rules and honest forms nearly verbatim (about 3,000 words). Nothing
tells an L3 graduate that the block is unchanged, so the 28-minute reading line (raised by word count at 150-200 words a
minute) is half a re-read. L3, where the same block is met first, keeps 14 minutes from an agent-student estimate. L4
also refers to a stage-0 header ("Под заголовком этапа 0") that only L3 prints. Student-c's unclear items 1 (R2 accepts all
of `shipping/` while K2 limits a stage's scope to proven nets) and 2 (the plan's language) were never fixed or accepted.
L3 step 1 promises that the labels/manifest functions change in later lessons, and no later lesson changes them.
Rule: When a lesson repeats an earlier lesson's rule text, say so where the repeat starts and list the differences. Time
every reading line in a module on one basis. Before hand-back, mark every student unclear item fixed (file:line) or
accepted (where recorded), including items from early reports that later reruns did not repeat.

### 2026-11-17: Book quote backed by a source without it; a scope qualifier dropped from a doc fact (#45, judge_content round 1, accuracy)

L3 theory.md:11 quotes Feathers as "legacy code is simply code without tests", and lesson.yaml:11 names Nicolas Carlo's
page as the source "(legacy code is simply code without tests; ... алгоритм изменения legacy-кода)". That page has
"Legacy Code is code without tests" (no "simply"), and its recipe is "Identify change points (Seams), Break dependencies,
Write the tests, Make your changes, Refactor", without the "find test points" step L3 theory.md:15-19 and L4
theory.md:20-25 list and L3/L4 task.md build steps 1-2 on. The research had said the book was not read. L5 theory.md:36
(and lesson.yaml:26) says the GitHub Action in automation mode has no shell or GitHub API without `--allowedTools` or
`permissions.allow`. The page says that for "a plain-text prompt" only; a skill prompt gets the tools its `allowed-tools`
grants, and the page's own review example, the case the sentence sits in, is a skill. The research note kept "plain
prompt"; the lesson dropped it.
Rule: A direct quote and a source title are claims about the cited page: open the page and find the exact words before
writing either; if the words come from a book nobody read, cite a page that has them or quote the page you cite. When
condensing a doc fact, keep the condition the doc states it under ("for a plain-text prompt") and check it against the
example the lesson places next to it.
