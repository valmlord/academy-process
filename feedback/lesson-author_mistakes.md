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
