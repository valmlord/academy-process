# lesson-author mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

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
