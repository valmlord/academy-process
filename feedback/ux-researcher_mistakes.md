# ux-researcher mistakes

Seeded with design-discipline rules; append real lessons as they are found. Load before working.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seeded: Flows written from assumed needs

A flow that starts from what the designer imagines the learner wants, instead of a course file, a
journal entry or the issue, designs for nobody in particular.
Rule: Every flow names its learner goal and the source it comes from (`course/`, `learner/journal.md`,
the issue).

### Seeded: A flow without error and empty states

A flow that describes only the happy path leaves dev to invent what the learner sees when a check fails,
a workspace does not start or a list is empty.
Rule: Every flow has an entry point, a success state, error and empty states, and an exit.

### Seeded: Two words for one concept

Calling the same thing a "lesson" in one flow and a "class" in another makes the UI inconsistent and the
IA ambiguous.
Rule: Take the vocabulary from `course/` and `docs/learning-process.md` and use one term per concept.

### 2026-10-29: Prototype scope table contradicted the deferred list and the flows (#50)
The lesson row of the design file's prototype table asked for "each status of the checks.md table"
(including closed, runner error, format error) while D1 deferred F14 and runner error; it listed an
"M0 stub" state that no flow defines; it left F3.1-F3.2 (user menu) assigned to no prototype; and
ia.md gave a different F6 region order than lesson-workspace.md and A2.
Rule: Before handing off, cross-check every in-scope state against a flow step or error state, every
deferred item against the in-scope list, and every flow step against exactly one prototype.

### 2026-10-29: Lesson status labels not closed over all states (#50)
F14.4 introduced lesson status "Не пройден" that the catalog status list (F5.3) does not have, and the
mentor action was named "Разобрать с ментором" in F13.6/F16 and "Разбор с ментором" in F14.3/F15.6.
Rule: Put every status label and action label in the ia.md vocabulary table and grep the flows for
variants before handing off.

### 2026-10-29: Keyboard, live-region and contrast decisions left gaps an a11y judge could name (#50)
The accessibility judge failed the #50 design: below 768 px the environment and "Проверить" disappear,
so a 1280 px laptop at 200 % zoom (640 CSS px) loses the task's core function (WCAG 1.4.4, 1.4.10);
the idle banner and the F2 alert can sit in a hidden pane or outside the F6 cycle; the check bar puts a
ticking timer next to a live announcement without saying which element is live; F6 is the only way out
of the terminal and its delivery to the page in browsers is unverified, with no fallback; the terminal
surface follows the theme while xterm's default ANSI palette stays dark-tuned (yellow on white 1.35:1);
and the F6 region order still differs between ia.md and lesson-workspace.md.
Rule: For every keyboard path, name the element that receives focus, the element that is the live
region, and what is outside it; check each breakpoint decision against 200 % zoom on a 1280 px
screen; and mark every unverified key behaviour as a test the dev issue must pass, with a fallback.

### 2026-10-29: English vocabulary, inventory flow column and token names left inconsistent (#50)
The consistency judge failed the #50 design: ia.md:19 fixes English "workspace" for the running
container, yet ia.md, the registry titles (F8, F10, F11) and every flow say "environment", and
lesson-workspace.md:82 and ia.md:64 still say "workspace" for the same thing. The page inventory's
Flows column lists F3 (user menu on every page except sign-in) only for sign-in and dashboard, and F2
(any protected page) for dashboard and lesson but not catalog. The plan leaves the status and terminal
token names open, although the validator checks only `<name>-foreground` on `<name>` (plus
`muted-foreground` and `destructive` on `background`), so a name outside that shape or a status colour
used as text on `background`/`card` ships unchecked. "F6" names both flow F6 and the F6 key.
Rule: Grep docs for every English and Russian synonym of each vocabulary row, derive the inventory's
Flows column from each flow's Entry line, and name every planned colour token in the `<name>` /
`<name>-foreground` shape with the surface it is used on.

### 2026-10-29: Round-1 fixes introduced new gaps at their seams (#50, judge_design round 2)
The usability judge failed round 2: the disabled "Проверить" with no button leaves region "Проверка"
with no focusable element, although the `F6` rule lands on "the first focusable element"; "Открыть
результаты" does not switch the one-pane area back to "Урок" while "К окружению" does; the one-pane
switch belongs to no region; the "closed" status sets omit labels the flows use (terminal and reset
statuses, "Не пройдено: исчерпан бюджет $N", "Осталась 1 попытка"); A18 assumes "Продолжить" means the
learner is practising while A10 auto-starts the environment on any open, and "В процессе" has no rule;
v1 shows "Пройти квиз", "Разобрать с ментором" and "Попросить подсказку" before their features exist,
against the own rule that a control which does nothing is a dead end (F12, A15).
Rule: After a fix, re-walk every flow that touches the changed rule (focus landing, one-pane switch,
closed sets, assumptions) and check each new statement against every other assumption and every
disabled or not-yet-shipped state.

### 2026-10-29: Round-1 a11y fixes added a live region that is not announced and an F6 stop with nothing to focus (#50)
The accessibility judge failed #50 round 2. ia.md:102-103 puts region "Уведомления" in the DOM only while
it holds an alert, and lesson-environment.md:40 makes the idle warning inside it `role="status"`: a live
region inserted together with its text is not reliably announced (ARIA live regions must exist before
their content changes), so the WCAG 2.2.1 warning can stay silent for a screen reader user in the
terminal. ia.md:137 says `F6` focus lands on the region's first focusable element, but in the creating /
starting state (checks.md:75-77) region "Проверка" holds only a disabled "Проверить" and no button, so
the rule has no target, and a `disabled` button's reason is skipped by Tab.
Rule: Every live element exists in the DOM, empty, before its text is set; when a region can hold no
focusable control, say where `F6` focus goes (the region itself with `tabindex="-1"`, or an
`aria-disabled` control with its reason in `aria-describedby`).

### 2026-10-29: "Closed" status sets that flows break, and a token rule the ANSI tokens break (#50)
Round 2 consistency FAIL. ia.md:37 says no flow uses a status label outside the closed sets, yet the
environment status row (ia.md:44, "F8, F10, F11") omits the status-bar texts of F9
("Соединение с терминалом потеряно. Переподключаемся...", "Не удалось переподключиться", "Сеанс
терминала завершён", lesson-environment.md:184-191) and F11.4 "Рабочая папка сброшена"
(lesson-environment.md:267), and the check status set omits "Не пройдено: исчерпан бюджет $N"
(checks.md:88, design file :175). The design file :65 says every new colour token is a
`<name>`/`<name>-foreground` pair, then adds 16 `terminal-ansi-*` tokens with no foreground and no
stated `@theme inline` mapping, which the validator requires for every colour token
(scripts/design_tokens.py:353-357).
Rule: Before calling a set closed, grep every flow for quoted labels on that surface and diff them
against the set; when adding a token family, state its shape, both-theme rule and mapping explicitly
even when it is an exception to the general rule.

### 2026-10-29: R2 left the sign-in errors silent, and the split handle has only a drag (#50)
Round 3 accessibility FAIL. ia.md:154-157 (R2) allows no live container outside the lesson page except
"Уведомления", which sign-in does not have, and auth.md:31-37 gives "Не удалось связаться с сервером..."
and "Слишком много попыток входа..." no focus move (only wrong credentials moves focus, auth.md:27), so
both submit errors are status messages a screen reader never hears (WCAG 4.1.3). lesson-environment.md:168
and design file :237 make pane resizing drag or arrow keys only; a mouse user without fine dragging has no
single-pointer way to resize (WCAG 2.5.7 Dragging Movements; keyboard does not satisfy it).
Rule: When a rule says "nothing else" or "only", walk every page it excludes and every message shown after
an action there; every dragged control gets a click alternative, not only keys.

### 2026-10-29: R6 hides the progress extras, the dashboard state list still draws them (#50)
Round 3 usability FAIL. ia.md:246-248 (R6) says recent attempts, weak topics and cost (#35) are not shown
in v1, and progress.md:24,26 agree, but the dashboard's required states (design file :159) still ask for
"reserved slots for F18.3-F18.4 marked "M2"", ia.md:305 repeats it, and the F18 first-run empty state
(progress.md:34-35) shows cost "$0", which is F18.4. The product-designer's checklist contradicts the rule
it must follow, and a `ready` dashboard would ship a placeholder box R6 calls a dead end.
Rule: After adding a "not shown in v1" rule, grep the required-states lists, the page inventory and every
empty state for each hidden item and remove or re-label it there in the same edit.

### 2026-10-30: Release-state grep searched the link text, not the whole hidden class (#79)
judge_design usability FAIL, round 1. ia.md R6 "Before the catalog ships" hides a class of controls (top-bar
"Курс", "Открыть курс", the Card button "Начать" / "Продолжить", module rows, breadcrumbs), but the design
file's grep (plans/79-...-design.md:147-148) searched only "Курс" and "Открыть курс". So
dashboard/acceptance.md AC1, AC2, AC4, AC5, AC9 (unconditional: "the Card shows the first `ready` lesson",
"the course line counts...") stay unscoped, and against #29's build with module 00 `ready` they fail and
contradict the planned AC14 ("no link to a `/courses/...` route appears anywhere").
Rule: When a release rule hides a class of controls, grep every member of the class (labels, routes,
component names) and scope every acceptance check that describes a hidden control to its release.

### 2026-11-03: README rewrite states prototype-only mechanics as the shared control spec (#80, judge_design usability)
plans/80-proto-css-fixes-design.md D4 rewrites design/system/README.md:86 to say controls use their height "as a
minimum height, so a control grows instead of clipping" and "buttons and inputs have no vertical padding". The
README is the design-dev contract (ADR-0006) and says "every value is a class in the app" (:59), yet the shipped
app uses fixed `h-9`/`h-8` (button.tsx:32-34, input.tsx:14) and the input keeps `py-1.5`, and the task declares
"apps/web needs no change". The truth check in D4 checked the sentences only against proto.css, so after merge the
contract says one thing and the app, which is "ready", does another, with no follow-up recorded.
Rule: When rewriting a README rule that binds the app, check every sentence against the app's classes too; either
scope the mechanism to the prototype in the sentence itself or record the app change as a tracked follow-up.

### 2026-11-03: Acceptance check prints member counts but never asserts them, so an absent member passes (#80, judge_design consistency)
plans/80-proto-css-fixes-check.mjs skips every element without a box and only prints the per-member counts; the
expected counts live in a table in the design (D6) that a human is asked to compare. On the patched tree with the
icon button renamed, every non-busy aria-disabled gallery button stripped and every `.env-details` and
`.dropdown-check` renamed, the script still prints ALL PASS and exits 0: the 36x36 guard, the not-allowed negative
cursor case and two class D members are silently gone.
Rule: A check that enumerates class members asserts each member's expected count (per page and width) in code, and
treats a missing optional probe (`undefined`) as a finding where the design says the member exists.

### 2026-11-04: Registered copy checked against the sample data, not the real cases; spec gaps at state seams (#69, judge_design usability)
Round 1 usability FAIL. The budget confirmation's "...на эти проверки:" (checks.md:224-226, ia.md:69) is plural, but
the first real cases (L4 `plan-rubric`, L5 `agents-md-rubric`) put exactly one check in the list; only the two-item
sample was read. "Агент потратит..." names the rubric grader, which the register calls "ментор" ("оценка ментора"),
and "агент" (also Claude Code in the terminal, ia.md:63) has no vocabulary row. The check bar's "Переподключиться"
gives no feedback and has no focus target when the server is still unreachable (checks.md:283-285). A tab that
becomes visible removes "Открыть результаты" with no focus rule (checks.md:171-172). The row's "grader message of the
latest result that has one" and the "newer run ended" check need data the requirements do not list. The meta
"лимит M:SS" is keyed to the latest result, so a passed or closed row can show it under "Пройдено" or "Закрыта".
Rule: Read every registered string with N = 1 and with the smallest real lesson case, not only with the sample; give
every new word a vocabulary row; for every control or state change, write the outcome on failure and the focus target;
check every row rule against every status word it can sit next to; trace each data-dependent sentence to a named field.

### 2026-11-04: New background transitions remove a focused check-bar control with no focus target (#69, judge_design accessibility)
#69 added state changes the learner does not trigger in the tab that has focus: a hidden tab that becomes visible
re-reads the check states and either clears the end text and removes "Открыть результаты" (checks.md:171-172) or
attaches to a running run, where "Дождитесь окончания проверки" wins over "Сначала запустите окружение" and "К
окружению" goes too (ia.md:142, 149-155). R2's focus rule (ia.md:188-195) names a target only for "an activated
control removes itself", so a focused "Открыть результаты" or "К окружению" falls back to `body`, against R2's own
"Focus never falls back to body" and WCAG 2.4.3. The same design left the check bar's "Переподключиться" with an
unreachable server as "the state stays" (checks.md:283-285): no text changes, so nothing is announced and the press
has no perceivable result. R2's first bullet still says every live container is empty on load (ia.md:168) while
the next bullet and A69-6 render S3's text on load.
Rule: For every new state transition, list which controls it removes and whether one may hold focus at that
moment, including transitions nobody activated (visibility, load, server push); name the focus target for each. A
control whose action can fail with no state change must still change the live text (busy text, then the failure
text again), so the outcome is announced.

### 2026-11-04: Vocabulary row and token rationale contradict the sources they cite (#69, judge_design consistency)
#69 added the vocabulary row "run | проверка" (ia.md:29) next to "attempt | попытка" (ia.md:28) without relating
the two, while ADR-0007:63 defines an attempt as one grading run and the design note's dev requirements head the run
section "Per run (attempt)". In check copy "попытка" is one check's result ("Неудачных попыток: N" per row), and
"cost of an attempt / Стоимость попытки" (ia.md:33) is shown per row, so one run with two token-spending checks
shows two different "Стоимость попытки" values for what the vocabulary calls one attempt. Separately, checks.md:43-44
justifies `warning` for the runner error with "the cross means 'your work missed the bar'", while the counted
"Время вышло" (checks.md:35, 50-51: "counted, like Не пройдено") stays `warning` and ADR-0007:54 files a timeout
under "the learner's work missed the bar": the stated rule does not produce the table.
Rule: A new vocabulary row names how it relates to every neighbouring term and to the ADR's definition of the same
word; a token rationale is a rule, so run it over every row of the table before writing it down.

### 2026-11-04: A new comparison rule with no baseline, and a trigger narrower than its own table (#69, judge_design round 2, usability)
Revision 2 added B9 "a newer finished run (its attempt id differs from the one this page shows)" and the data line
"the UI compares `attemptId` with the one it shows". A page loaded with an empty status line (B1) shows no run, so
the first return to the tab finds a "different" id and announces yesterday's end text as if a run had just ended;
and a tab in "Не удалось получить результат проверки" shows the same id as the run that has since ended, so B9 never
fires there. Separately, F13 error states (checks.md:432) and A69-7 re-read on `visibilitychange` only in "a tab
that never attached", while B8-B10 remove "Переподключиться", which exists only in a tab that did attach.
Rule: A comparison rule names its baseline at every starting state (load with nothing shown, mid-run, after a
failed stream), and the trigger of a transition table row must reach every control the row says it removes.

### 2026-11-04: A vocabulary fix stated as an absolute that the register itself breaks (#69, judge_design round 2, consistency)
The round-1 finding asked the vocabulary to state how attempt, run and check relate. Revision 2 wrote two absolutes:
"In docs 'attempt' means only this record, never one check's result" and "no UI string says 'попытка' for the
run" (ia.md:30-31). The next row is "attempt limit" (per check, ia.md:32), and R7, the F14 title, checks.md:39,
:108-116, :193-195, :498-535 and the data fields `attemptLimit` / `lastAttemptCount` (design note §4, which also
says "every 'attempt' below is the ADR record") all count one check's results. In UI copy "История попыток",
"Попыток пока нет. Нажмите "Проверить"..." (shown in v1, checks.md:461) and "Ментор читает попытку" name the run.
Rule: Before writing "only" or "never" into a vocabulary row, grep the word (both languages, every flow and the data
section) and list each hit under the sense it uses; if both senses exist, the row names both and which strings own
each, instead of a rule the docs break.

### 2026-11-04: A flow fix with no system work item for the markup it contradicts (#69, judge_design round 2, consistency)
Revision 2 made the row running time "not live, no `role="timer"` there" (checks.md:97-101, ia.md:187-190) and
logged it as fixed, but `components.html:387` and `prototype.html:388`, `:445` render
`<span class="timer" role="timer">` inside `.check-row-trigger`, `README.md:182` defines `.timer` as `role="timer"`,
and no §3.2 / §3.3 item changes them, so the authors would ship markup the flow forbids.
Rule: When a flow fix changes how a component is marked up, grep its class in `design/system/` and `design/pages/`
and add a work item for every hit in the same revision.

### 2026-11-09: A new flow's run step sent to the old state, which shows another data set (#69, judge_ux round 1, usability)
Design note §3.3 sent "Проверить" of `limit-warning` (F14.1 -> F14.2, the last-attempt run) and `results-limit-known`
to the #50 state `check-running`. That state draws the limit-unknown lesson: the row reads "Идёт" "0:12 из 0:30" with
no "Осталась 1 попытка" and the counter "Неудачных попыток: 2". So in the prototype the warning disappears the moment
the last attempt starts, against checks.md:123 ("Идёт": the warning, yes), and the counter drops from "9 из 10" to "2".
`mixed -> mixed-running` and both budget runs were given their own running states; F14 was not. The product-designer
followed the table faithfully, and the headless run checks each state alone, so nothing caught it.
Rule: For every new state with a run control, name a target state whose rows continue that state's data (same
counters, same limit form, the meta of the running word) or add one; reusing an older state is allowed only after
diffing its rows against the source state.

### 2026-11-03: Acceptance check asserts the not-found members but not the lesson and catalog keyboard members (#83, judge_design accessibility)
plans/83-app-shell-states-check.mjs counts every not-found member in code, but for W2 and W3 it only asks that
"Не удалось загрузить курс" occur twice anywhere in design/pages/lesson/acceptance.md, and it reads no catalog or
dashboard acceptance file at all. Appending the string twice under "Open questions" satisfies it (run), while the
lesson `F6` row for the course error, its Tab order, AC19 (three retry focus outcomes), AC20 and the D5 heading
mapping, catalog AC8's not-found focus outcome (D7) and the "Course id unknown" scoping lines can all be missing.
The not-found "focus does not move on arrival" half of AC9 is not measured either.
Rule: Every work item that changes a keyboard or focus contract (F6 rows, Tab order, retry focus, heading levels)
gets a code assertion of its own row or AC, located by its heading or row key, never a string count over the file.

### 2026-11-03: Declined a decision the issue assigned to design, and recorded scope only in git-ignored plans/ (#83, judge_design usability)
Issue #83's owner comment asks design to "decide whether the design accepts" the Radix Tabs ring on first
mouse click (F3). The design answered "app behaviour, not a design rule ... dev decides", and the F3, G1 and
`.checks-panel h2` (#69) hand-offs exist only in `plans/83-app-shell-states-design.md`, which is git-ignored:
no lesson acceptance open question, no follow-up issue, nothing on #69. The same phase also left two rows
describing a "Course id unknown" member unscoped or misstated: the ia.md R2 retry sentence names targets
("the catalog h1, the lesson h1, or ... the error's own h1") for a list that includes the dashboard and the
lesson text-load retries, whose targets are the Card heading and the tab panel; the inventory Purpose says
not-found "links to the catalog" without the no-course exception.
Rule: An item the issue explicitly asks design to decide is decided (even "accepted, because ...") in a
committed design file; anything handed off goes to a durable place (issue, comment on the owning issue, Open
questions); every enumeration in a rule is checked against each member it lists.

### 2026-11-03: "Reuse the drawn composition unchanged" pointed at markup that lacks the attribute the design requires (#83, judge_design consistency)
D3 says the lesson course error is the catalog's `#state-course-error` "unchanged", with the h1 as Alert title
carrying `tabindex="-1"` so a second failed retry can focus it (also `catalog.md:38`, `lesson-environment.md:89,95`,
`ia.md:171-172`; the app's `course-error.tsx:26` has `id="course-error-title" tabIndex={-1}`). The drawn reference,
`design/pages/catalog/prototype.html:67`, is `<h1 class="alert-title text-sm">` with no id and no tabindex, and W3
says "No change to either prototype", so the lesson acceptance would send dev to a drawing that contradicts its own
spec. The acceptance check asserts neither this attribute nor that the new `.prose h4` rule uses the scale tokens
(`--text-lg`, `--text-lg-line`, `--space-6`) rather than equal raw lengths: computed px cannot tell them apart.
Rule: Before declaring "reuse X unchanged", diff X's markup against every attribute the design states for it and
against the app component; a mismatch is a work item, and the check asserts the attribute and the token names.

### 2026-11-03: README truth table accepted "h3 on pages" without checking a single page h3 (#83, judge_design round 2)
The D5 truth table marked the README `text-lg` row "card and dialog titles; h3 on pages; h4 in prose" as holding,
citing only `proto.css:114` for h3 and only the app's `.prose h4` for the app column. Every page h3 outside prose
(catalog "Чему научитесь") is `text-sm` (`proto.css:520`, `apps/web/components/catalog/module-section.tsx:33`), so
the phrase is false on both sides, and the check script locks it in. The phrase came from a judge note; the truth
table exists to catch exactly that.
Rule: A README truth-table row verifies every phrase in the sentence against both proto.css and the app, by
grepping the rendered uses, including phrases a judge asked for.

### 2026-11-03: New lesson course-error state left R4 and the not-found route set unscoped (#83, judge_design round 2, usability)
Round 2 added the lesson page whose course cannot be read and scoped R3 to it ("none of the three regions
exists"), but `ia.md` R4 still says, with no exception, that the lesson page's `main` holds "Урок", "Проверка" and
"Окружение" and gives a Tab order through breadcrumbs ("Курс", module), a line the design's own grep terms
(`"Курс"`, `breadcrumb`) match. The not-found entry set was also stated three ways: the inventory Route
(the file the not-found acceptance Route copies) and `lesson-environment.md` F7 error states and retry clause
omit a lesson URL whose course id is not the course's, which the app sends to not-found
(`lessons/[lessonId]/page.tsx:71-72`) and `catalog.md` F5 and the R2 table header include. Round 1 U3 was
this class (a statement not scoped to the case); fixing the listed members only left these.
Rule: When a design adds a state to a page, grep every rule that describes that page's structure, Tab order and
entry causes (`main holds`, `Tab order`, `Route`, the page's own region and control names), and scope each one or
list it as unchanged with the reason; state each set (such as "the ways into not-found") once and point to it.

### 2026-11-04: Deep-link focus rule did not cover every value the linking rows carry (#72, judge_design round 1, accessibility)
F19 says `?attempt=` expands and focuses that attempt's disclosure, with a fallback only for ids that are not
a finished attempt. But F18.3 links every attempt row, including a finished attempt with no check result, which
A72-14 makes a plain list item with nothing to expand or focus; and the arrival while the history read fails had no
stated outcome. Two reachable arrivals had no focus target.
Rule: For every deep link that moves focus, enumerate each value the linking page can emit times each state of
the target section (loaded, empty, error, item rendered as non-interactive) and state the focus target for each.

### 2026-11-04: Ranking rule and status words checked at one corner only (#72, judge_design round 1, usability)
A72-2 sorts closed checks first in "Где трудно" and drops a check only when it passes later. A closed check is
final, so after five closed checks the list never changes again, and its reason ("where to go back now") does
not fit a check where nothing can be done. The attempt summary gives "Сбой проверки, попытка не засчитана" only to
runner errors, so a format-error or an uncounted-timeout attempt reads "Пройдено проверок: 0 из 1", the same as a
counted failure. A72-8 says the word carries the meaning, but the `aria-hidden` icon is the only difference.
The "Words" paragraph also says "attempt is always the record" while F18.4 in the same file shows the per-check
"Неудачных попыток: N".
Rule: For every list rule, walk the end state where a member can never leave (final states, the cap reached) and
say what the list shows then. For every summary set, list each result kind and check that two kinds the learner
must tell apart never get the same text. Grep the file for every "always" or "never" claim about a word.

### 2026-11-04: Icon rule named a shape the system does not have, and pointers checked by memory (#72, judge_design round 1, consistency)
A72-8 gives a running attempt "the `info` ring without spin". No `.status-icon` variant is that: `info` is an "i"
glyph, `running` is the spinning ring that #69 pairs with "Идёт". So either the design adds a variant it says it
does not add, or one word gets two icons on two pages. The same rule's "check mark when every result passed" is
vacuously true for an attempt with no result, which reads "Сбой проверки, попытка не засчитана" (warning in
#69). The new page-copy row `ia.md:81` points to "the lesson row above", which sits below it, and ADR item 11
calls a mentor review "an agent call", which the vocabulary forbids.
Rule: Every icon a flow names is a `data-status` value grepped in `proto.css`, and the same word gets the same
value as in its source set; every "all/every" rule is checked on the empty set. Every "above/below/row X" pointer
and every English term in a new doc line is grepped against the file and the vocabulary before hand-off.

### 2026-11-04: Mapped a snapshot status to an animated icon (#72, judge_design round 2, accessibility)
A72-8 mapped the dashboard's "Идёт" to `.status-icon[data-status="running"]`, which spins with
`animation: ... infinite` (`proto.css:270`). On the Проверки tab that ring is live and stops with the run; on
the dashboard the row is a snapshot that is never updated until reload, so the ring would spin forever after
the run ended, with no pause control (WCAG 2.2.2), and it contradicted the decision's own "the ring is a
snapshot". Cost a review round.
Rule: When a flow reuses an icon in a new place, read its CSS for animation; an animated icon only where the
state it shows is live and ends, a static form wherever the page shows a snapshot.

### 2026-11-04: Outcome sweep enumerated status kinds, not kind x counting rule; new focus target landed on stale copy (#72, judge_design round 2)
Sweep 2 listed every #69 status word but not the S1 case: a failure on a check that already passed (spends no
attempt, `checks.md` F14 note). Its bucket in "attempt summary" is undefined, and whichever #34 picks falsifies
A72-6 ("words alone tell counted from uncounted") or A72-8 ("row and panel differ only for two cases"). The new
deep-link row 3 also moves focus to the F19 empty text "Нажмите "Проверить"" while that button is disabled by the
running first attempt.
Rule: Sweep outcomes over the product of result kind and every counting rule (S1, S2, budget, server flags), not
the status table alone; and for every new focus target, read the text that follows it in that exact state.

### 2026-11-04: New summary note borrowed #69's "попытка не засчитана" for a different set (#72, judge_design round 2, consistency)
The round-1 fix added the attempt-summary note "Проверок с незасчитанной попыткой: N", defined as uncounted
results with runner errors left out and budget-spent-not-counted results put in. #69 defines "попытка не
засчитана" as every result that does not count, the runner error included ("Сбой проверки, попытка не
засчитана"), and the budget variant's word does not say it. So the row's count disagrees with the words in its
own panel, in both directions (design note `attempts-mixed`: the panel shows two "попытка не засчитана", the row
says 1). Cost a review round.
Rule: A new string built from an existing concept's words counts exactly that concept's set. Before adding it,
list the results whose existing word contains those words and check the new count equals them; if it cannot,
word it so it does not name the concept.

### 2026-11-04: Example attempt's summary did not recount to its own drawn panel (#72, judge_design round 3, usability)
Round 3 swept every result kind and combination in the abstract (sweeps 5 and 6) but not the concrete
prototype states. Design note §5.2 has "№ 3" reading "Пройдено проверок: 1 из 2. Проверок с незасчитанной
попыткой: 1" in `history`, while `history-open` expands it to three items (a pass, a runner error and a
removed check), and gives the removed check's item no status word. A72-6 counts every panel item in M, so the
author would draw a row that contradicts its panel. That cost round 4.
Rule: After a counting rule changes, recount every worked example and every prototype state that names both a
summary and its items (design note, flow file, ia.md examples) against the rule, item by item.

### 2026-11-04: Claimed a word had no icon without reading the prototype that draws it (#72, judge_design round 3, consistency)
A72-8 justified a new static `.status-icon` value for the dashboard's "Идёт проверка" by saying #69 shows that
word "with no icon", so "no word gets two icons". #69's lesson prototype draws the tab's ", идёт проверка"
next to `data-status="running"` (`prototype.html:175`) and the bar's "Идёт проверка" beside a `.spinner`
(`:507`, `:515`), and `checks.md:328` names the spinner. The new value would give the run word a second
icon, and the declaration sent to the ui-designer ("pairs only with "Идёт проверка"") was false.
Rule: Before claiming how an existing word is drawn (icon, no icon, which value), grep the word and its
visually hidden forms in `design/pages/*/prototype.html` and read the markup next to it.

### 2026-11-04: Made an error appear in the background with no announcement (#72, judge_design round 4, accessibility)
Round 4 changed F19 so that a failed history re-read after the first run replaces "Попыток пока нет" with the
error state "История попыток недоступна", and stated "nothing is announced" (`progress.md:208-212`). Until
round 3 a failed re-read changed nothing visible, so silence was fine. Now an error message appears without
focus and without a role, which is WCAG 4.1.3 (failure F103); a screen reader user whose focus is on the h3
(deep link row 3) is not told either, since a focused heading's text change is not reliably read. That cost
round 5.
Rule: Whenever an edit makes new text appear without a focus move (an error, a result, a state word), say how
it is announced (a live container that exists from load, listed in `ia.md` R2) or why it is not a status
message; "nothing in this flow is live" stops covering it the moment it shows something.

### 2026-11-04: Prototype links sent every dashboard row to one deep-link state (#72, judge_design round 4, usability)
Design note §5.1 prescribed one href for every "Последние попытки" row, `#state-history-deep-link` ("№ 3"
expanded and focused, deep-link row 1). The `attempts` state draws an "Идёт проверка" row and a no-result row,
whose arrivals are rows 3 and 2 (heading focused, nothing expanded; a plain item). The states drawn for those
rows (`history-deep-link-running`, `-plain`) were reachable from no row, so the prototype click path would
contradict A72-9 and the deep-link table.
Rule: When a page links to states of another page, map each drawn source sample to the target state of its own
case (one row of the arrival table each) and recount that the target shows what the source row says.

### 2026-11-04: Re-drawn samples broke the newest-five rule and left the cost rows' targets on another release (#72, judge_design round 5, usability)
Round 5 made every dashboard attempt row lesson L's. `attempts-mixed` kept "Где трудно" as `attempts` (lesson
P's checks with 3 and 9 failed results, so at least 9 older attempts of a `ready` lesson) and drew 3 rows, while
F18.3 lists the 5 newest attempts over every `ready` lesson. The #37 cost states kept the #35 links, so a row
reading "Потрачено: $0.08" opens the attempt without its cost; Sweep 9 claimed a match through `history-cost`,
which no row opens.
Rule: After re-drawing a sample, re-derive every section of the same state from the same data (the rows a list
rule would select, the counters that imply attempts) and walk each link of every state that reuses the sample,
checking the target's release as well as its case.

### 2026-11-10: Flow cited another task's prototype by line number, stale after the merge (#72, judge_ux round 1, consistency)
progress.md A72-8 pointed at `design/pages/lesson/prototype.html:175`, `:515` and `:507` on #69's branch. After
#69 merged and #72 added its states, `:175` is the hidden "Урок" region heading and the cited elements sit at
`:223`, `:1795` and `:1784`, so the flow sends dev to the wrong element.
Rule: In a flow, cite a prototype element by id, class or selector, never by line number; a line number into a
file another task is still rewriting is wrong the day that task lands.

### 2026-11-10: Stated the plain item's computed name without its focus condition (#72, judge_ux round 3, accessibility)
progress.md A72-19 (:500-502) says "Chromium computes its name from its contents (name source `contents`,
measured)" without a condition. Measured: only while the `li` has focus; unfocused it has no name. ia.md:545
puts the same sentence in the focus-on-load column, where it holds.
Rule: A flow sentence that reports a browser measurement carries the measurement's condition (focused,
expanded, theme) with it.

### 2026-11-10: Widened a concept by decision but left its vocabulary definition narrow (#72 merge with #70, judge_design round 1, consistency)
A72-17 (progress.md:502-513) decides that every answered quiz send is an attempt record that is not a run,
and cites the `ia.md` rows "run" and "attempt (record of a run)" as keeping the two apart. Those rows
(ia.md:31-32), checks.md:24-30 and progress.md:19-20 still define the record as "ADR-0007's record of one
run", the run row says every record is a saved run, and A72-10 (progress.md:474-475) numbers records
"because the learner pressed "Проверить" each time". The register now says a quiz record cannot exist.
Rule: When a merge decision adds a new member to a concept, grep the concept's definition in every flow
file ("record of one run", the row title, the reasons that name its old source) and widen each one in the
same change; a decision that cites a definition must be true against that definition's text.

### 2026-11-10: Made quiz sends attempt records without checking who reads "latest attempt" (#72, merge with #70, judge_design round 1, accessibility)
A72-17 decided that every answered quiz send is an attempt record, but the check bar's re-read baseline is
`latestFinishedAttempt.attemptId`, "the latest finished attempt record" (checks.md "Baseline of a re-read"),
and P7 keeps the baseline after a send. Read literally, the next visibility re-read is B9 and announces a run
end for a run that never happened, the quiz outcome a second time.
Rule: When a decision widens what a data term covers (here "attempt record"), grep every field and rule that
uses the term (`latestFinishedAttempt`, baselines, counts) and state for each whether the new members count.

### 2026-11-10: Made quiz sends attempt records without following the field that counts records (#72 merge with #70, judge_design round 1, usability)
The merge decided that every answered quiz send is an attempt record (A72-17, T1) but left `checks.md`
"Baseline of a re-read" (`latestFinishedAttempt.attemptId`, B8-B11) and the vocabulary row "attempt (record
of a run)" as they were. Read as written, a visibility re-read after a quiz send sets a run end text in the
check bar, against Stepan's P6; read the other way, the history misses a quiz record sent in another tab.
T1 and T3 were also not added to `quiz.md` "Requirements for #36", the list #36 is built against.
Rule: When a decision widens what a stored entity holds, grep every field, rule and vocabulary row that reads
that entity and say for each whether the new kind is in or out; put each new demand on another issue into
that issue's requirements list.

### 2026-11-10: Widened the record's definition but left "run" in the definitions next to it (#72 merge with #70, judge_design round 2, consistency)
The round-1 fix renamed the vocabulary rows and widened the attempt record to quiz sends, but two definitions
in the same ranges still tie the concept to a run: `ia.md:32` quotes ADR-0007 item 5 ("one grading run started
by one learner action") as the definition of every attempt record, then says a quiz attempt record "is never a
run", so the row uses "run" in two senses; `checks.md:38` still heads the per-check sense "one check's result in
a run", while the same bullet counts quiz results and ends "one answered quiz send is one record and one result".
Rule: After widening a term, grep the word of the old scope ("run") inside every definition of that term and of
its sibling senses, and either replace it or say in place how a quoted source's wider word maps to the
vocabulary's narrower one.

### 2026-11-10: Fixed a two-senses finding by adding an absolute claim that is false (#72 merge with #70, judge_design round 3, consistency)
The round-2 fix of `ia.md:32` maps ADR-0007's "grading run" to both record kinds, which is right, but adds that
the vocabulary's run is "the only sense of "run" in these docs". `design/flows/` uses "run" in other senses:
"First run" for an empty product (`progress.md:92`, `dashboard.md:47`, "first-run failure" `auth.md:44`) and
GitHub Actions runs ("`gh run list` shows 10 runs", `progress.md:358`).
Rule: Before writing "the only" / "never" / "every" about a word in the docs, grep the word across all of
`design/flows/` and list the exceptions, or scope the claim to what the grep proves.

### 2026-11-10: Widened a "last read" baseline without following what it suppresses (#72 merge with #138, judge_design round 4, accessibility)
Round 4 added "this page's own send that timed out and the server recorded" to the B27 reads that set the
"changed since the page last read it" baseline (`quiz.md:179`). That baseline suppresses the result block's
lesson line on the next answer. After a B27 re-read, the retry of the timed-out send returns the recorded
result with no "Урок пройден", and P8 has emptied the status line, so the lesson outcome of that send is
announced and shown nowhere, against `quiz.md:202` "announced once". The exclusion is right only for a send
announced in another browser tab.
Rule: When adding a case to a list that suppresses an announcement ("already said", "already read"), name
where that case was said; if nowhere, it does not belong in the list.

### 2026-11-11: Excluded one silent read from the baseline, not the class (#72 merge with #138, judge_design round 5, accessibility)
The round-4 fix took B27 out of the "changed since the page last read it" reads while this page's own
timed-out send waits for its retry (`quiz.md:179-183`), but left the other reads that do not say the lesson
status: a run end with summary 4 (which wins over 5 and 6) and a B8 re-read followed by summary 3 or 4. After
either, the retry of a recorded send that finished the lesson carries no lesson line, so the outcome is
announced zero times, against `quiz.md:641` "nothing else in this page view says it".
Rule: A read suppresses an announcement only if that read itself showed or announced the same fact; when
fixing one silent read, list every read in the baseline and keep only those that said it.

### 2026-11-11: Started the "only reads that said it count" window at the failure, not at the send (#72 merge with #138, judge_design round 6, accessibility)
The round-5 fix made only a read with summary 5 or 6 count while the own failed send waits for its retry
(`quiz.md:179-185`), but the same silent reads (a run end with summary 4, B8, B27 for this page's own send)
can come while the send is still in flight, which may last until a network timeout with the panel left
(`quiz.md:313-316`). The ordinary rule counts them, so the answer or the retry finds the lesson status
unchanged and "Урок пройден" is announced zero times, against row "1, 2 or 3" (`quiz.md:204`).
Rule: A window that suppresses a baseline read starts when the uncertainty starts (the send leaves), not when
the page first notices it (the error); walk every read between the send and its answer.

### 2026-11-04: Quiz send left the shared check bar stale, and flow behaviour lived only in plans/ (#70, judge_design round 1, usability)
`quiz.md` "Lesson outcome after a send" says a quiz send never sets the check bar status line, but never says what
the line then shows. With #69's `checks.md` the quiz counts in "Пройдено: N из M", so after a quiz pass the line keeps
a false "Пройдено: 1 из 2" next to the result block's "Урок пройден"; a quiz close that makes S3 disables
"Проверить" ("Проверки завершены") while the line stays empty or stale, where #69 requires summary 6 and "Открыть
результаты"; and summary 7's "Закрытых проверок" / "Осталась 1 попытка" notes may count a quiz no run includes. The
confirmation question put to Stepan (design note §12, Q2) named none of these corners. Separately, the error-summary
update after answering (A9), the answer lock while sending (A12) and the loading state (`quiz-loading`) were decided
only in the git-ignored design note, so the prototype would draw states no flow describes, and P5/P6 were not
recorded in `quiz.md`.
Rule: When a new surface affects a shared element (check bar, row sets, status line), walk that element's every
state in the owning flow (empty, holding an earlier end text, the nothing-to-run state, each note) after the new
action, write the result into the flow, and put those corners in the question to Stepan; every behaviour a prototype
state draws must be in the committed flow, not only in plans/.

### 2026-11-04: "Reuse X" rows that do not match X's markup, and register placeholders that swap meaning (#70, judge_design round 1, consistency)
The #70 design note's component table marked as plain reuse: `.icon-note` for the exact-set note "with no icon"
(every `.icon-note` in the system has a leading `.status-icon`, and a group's description note already has
`.field-description`); `.icon-note` (muted) for the quiz header's "Осталась 1 попытка", which #69 draws in the
check row with `[data-tone="warning"]` and foreground words; "Alert as focusable message" for the quiz load error,
whose analogue, the lesson text load error, is a plain destructive `.alert` that never takes focus; and the #69
check row "differences in quiz.md only", although the quiz row adds a panel button and a status word with no icon.
In the register, `quiz.md` defines N as the question count and M as the attempt limit, then writes "Вопрос N из M"
(N the index, M the count), and the quiz row uses K and C, which the closed-set placeholder list does not admit. The
merge note "the merge takes this row" also left the row citing "Осталась 1 попытка" in the check row note set, which
#69 moves to a new "check row meta" set.
Rule: For every "yes, reuse X" row, open X's rule in proto.css and one real use of X, and write the row as a variant
(with what changes) when the new use drops a part, changes a colour or role, or adds an item; for a string that
already exists elsewhere, reuse that element's markup. Keep one meaning per placeholder letter across a flow and
`ia.md`, and when a merge "takes this row", re-read every set name the row cites against the other branch.

### 2026-11-04: Send outcome specified only for a learner who stays on the Квиз tab (#70, judge_design round 2, usability)
`quiz.md` locks only the options while sending; the left-pane tab list stays live, and Exit allows "any other tab"
at any time. Yet every send outcome assumes the Квиз panel is shown: "a result arrives" moves focus to the result
block, the send error and the stale-attempt refusal move focus into the panel, and P8 says the lesson outcome "is
announced once, by the result block's lesson line" while the check bar changes silently. A learner who presses
"Отправить ответы" and then selects Проверки or Теория (one click, or Shift+Tab to the tab list) gets a focus target
in an inactive, possibly unmounted panel (focus to `body`, against R2) and, in S3, no announcement anywhere.
Rule: For every "focus moves to X" or "announced by X" after an asynchronous action, state what happens when X's
container is hidden or unmounted at the moment the answer arrives (another tab selected, one-pane mode with the
other pane shown), and make the outcome reachable and announced in that case too.

### 2026-11-04: Prototype attribute list left out the tab switch of a cross-tab action (#70, judge_design round 2, consistency)
Plan §4 "Every attribute a new state must touch" gives "Пройти квиз" (Проверки tab, quiz check row) only
`data-goto-state="quiz"` and `data-focus` on the panel `h2`, and says it works "as "Открыть результаты" does".
In #69's proto.js `gotoState` calls `setState(name, { keepTabs: true })` (A17): each tab list keeps its selected tab
while the new state still shows it, so `data-select-in-states` on `#tab-quiz` does not apply. Only
`data-select-tab` switches the tab, and #69's "Открыть результаты" carries `data-select-tab="tab-checks"`. Built as
listed, "Пройти квиз" leaves Проверки selected and focuses an `h2` inside a hidden panel.
Rule: Before listing "every attribute" for a control that moves to another state, read proto.js `gotoState` and
`setState` on the branch the prototype will be built on, and copy every attribute of the existing control the new
one is said to work like.

### 2026-11-04: Quiz notice removal trigger misses the "focus left, panel still shown" case (#70, judge_design round 3, accessibility)
`quiz.md` :286 defines the Квиз panel as "left" when it is not shown OR when focus is outside it, and the
notice (P9) is set in both cases. But the notice is removed only "when the Квиз panel becomes shown by any
route" (:344, :356; `ia.md` :172-174). In two panes with Квиз selected, a learner who presses "Отправить
ответы" and moves to the terminal gets the notice while the panel stays shown; coming back by Tab or click
never "shows" the panel, so the notice stays. The next send from the panel then focuses a new result block
while "Уведомления" still states the old outcome (false status text), and the "announced once" argument
(:341-343, "the next send needs the panel shown, which removes the notice first") rests on a premise that
does not hold.
Rule: When a message is set under a condition with several branches (A or B), check that its removal
trigger ends every branch, and walk each branch to the next action that relies on the message being gone.

### 2026-11-04: Quiz notice templates join to a double full stop, and the refusal row claims the send was checked (#70, judge_design round 3, usability)
`ia.md` :59 says each notice text is "optionally followed, joined with ". ", by "Осталась 1 попытка"", and
`quiz.md` :322 appends ". Осталась 1 попытка" to "Ответы квиза проверены. Верно C из Q. Нужно K.", which already
ends in a full stop: the template dev writes yields "Нужно 5.. Осталась 1 попытка". The other base texts end
without a full stop ("Квиз пройден"), so terminal punctuation also differs between rows. The refusal row
(`quiz.md` :326) reuses the failed row, "Ответы квиза проверены. Верно C из Q...", for a send the server refused
and counted nothing (`quiz.md` :481-485): the notice tells the learner their answers were checked and scored C,
while the C is another browser tab's attempt and their selection was never scored.
Rule: Write out every composed notice string in full, one line per combination, and read each one aloud; a
reused text must be true for every outcome that reuses it, so check its verb ("проверены") against what the
server did in that outcome.

### 2026-11-04: Control table claimed "checked against proto.js" but never traced Back or the ?tab= arrival (#70, judge_design round 3, consistency)
Plan §4's control table traced each control forwards only. Run in Chromium with wt69 proto.js and the lesson
page script: after a `data-goto-state` control that also names a tab ("Пройти квиз"), the page's
MutationObserver writes `?tab=quiz` into the new entry, so Back changes the query as well as the hash, the
browser fires only `popstate`, and proto.js (which listens to `hashchange`) leaves the state as it is. For
"Открыть квиз" the `data-show-pane` branch selects Квиз before the push, so the observer rewrites the entry being
left to `?tab=quiz`, and Back restores state 21 with Квиз selected, the notice shown beside the Квиз panel and focus
on an unselected tab. The `next` of "Войти снова" carries `?tab=quiz`, but `TAB_QUERY_STATES` has no `quiz`, so the
F2 return lands on Теория and `?tab=` is rewritten to `theory`.
Rule: For every control row, also trace Back, a reload and an arrival with the `?tab=` value it writes, through
both the proto.js listeners and the page script, and run the round trip in a browser before you write "checked".

### 2026-11-04: Quiz notice set row allows combinations the flow forbids (#70, judge_design round 3, consistency)
`ia.md` :59 lets each of the four notice texts take "Осталась 1 попытка" (the first only) or the lesson line. So
"Ответы квиза не отправлены. Попробуйте снова." plus a lesson line, and "Квиз не пройден: попытки исчерпаны. Урок
пройден", are legal in the closed set, although `quiz.md` :322-325 says "never" and "only in S3". A closed set
lists a variant word for word, or the variant does not exist.
Rule: For a composed status string, list every legal combination word for word in the set row, and diff the
list against the flow's outcome table row by row.

### 2026-11-04: Notice focus rule assumes a click on a control moves focus (#70, judge_design round 4, accessibility)
`quiz.md` :386-390 says only two removal triggers can fire while focus is on "Открыть квиз", because "focus
entering the panel or a send starting means focus already left the notice". On Safari (and Firefox on macOS)
a mouse click on a button, radio or checkbox does not focus it, which the same file says at :254. So a pointer
learner with focus on "Открыть квиз" who clicks an option or "Отправить ответы" removes the notice while it still
holds focus. The focus table :488 does not list that case, and ia.md R2 :175 sends focus to the old result
block or send error. During a send that target is wrong: R1 keeps focus on the busy button, and a send error
that the new send replaces is a detached target, so focus would fall to `body`.
Rule: Before writing "trigger X means focus already left Y", check it for a pointer press in Safari. Write one
rule for every removal while focus is inside: focus goes to the control that was pressed if there is one,
otherwise to the outcome target.

### 2026-11-04: "Panel left" decided by focus alone, so a Safari mouse learner who never leaves is "away" (#70, judge_design round 4, usability)
`quiz.md` :286-287 calls the Квиз panel "left" when focus is outside it, and :265-266 says focus "stays on" the busy
button. On Safari and Firefox on macOS a click does not focus a button, radio or checkbox (the file says so at :254),
so a mouse learner who answers and clicks "Отправить ответы" has focus on `body` the whole time. By the rule that is
"outside the panel": every send of that learner gets the quiz notice, the result block never takes focus (it sits
above six questions, off screen from the button), and the notice stays until the next click in the panel, the
opposite of P9's "no notice when the panel is shown with focus in it".
Rule: When a rule branches on "where focus is", walk it for a pointer-only learner in Safari, where focus can be
`body` without the learner having gone anywhere, and say which branch `body` takes.

### 2026-11-04: Stale-attempt refusal in the panel shows another tab's score as the learner's own (#70, judge_design round 4, usability)
Round 3 fixed the notice for a refused send ("Ответы квиза не приняты: ..."), but `quiz.md` :513-517 still shows the
panel-shown end of the same event as "the latest result, the new attempt line and the learner's unsent selection
kept", with focus on the result block. That block is F15.4's: "Верно C из Q. Нужно K." and "Ответы остались
выбранными. ...". The learner reads a score their answers never got, next to their unsent answers, told the answers
"stayed selected". No string for the refusal exists in the quiz set, so the panel cannot say it.
Rule: When a fix changes what one surface says about an event, find every other surface that reports the same
event (notice and result block, panel shown and hidden) and make them say the same fact.

### 2026-11-04: Seams list missed one #69 line, and a draft for #36 kept a stale item count (#70, judge_design round 4, consistency)
`quiz.md` "Seams" says each item is a line the merge must change. It lists #69's vocabulary row and the `checks.md`
R7 table for "Попытка N из M" / "Попытка N", but not wt69 `ia.md:371` (R7: "A quiz follows the same rule ("Попытка N
из M" / "Попытка N", D2)"). After the merge the register would use N there and A in the quiz set. In the same round,
`quiz.md` gained item 10 under "Requirements for #36", while the plan §10 comment for #36 still says "items 1-9" and
does not mention history or arrival. `quiz.md:624` also attributes "replaces the query, no history entry" to the
Navigation model, which does not say that. The rule is in lesson `acceptance.md` :15-16 and AC17.
Rule: When a list claims to be complete ("each line the merge must change"), build it by grepping the other branch for
every string being renamed, not from memory. When adding a numbered item, grep every place that quotes the count.
Cite the file that actually states a rule.

### 2026-11-04: "Away" rule leaves the environment status bar, its menu and the reset dialog unclassified (#70, judge_design round 5, usability)
`quiz.md:291-292` defines away as "focus is inside the environment pane (the terminal or the editor)", while `:507` and
`ia.md:159` say "focus in the terminal or editor", and `:292-294` puts "everything else" in the panel. The "Окружение"
region also holds the status bar ("Действия", "Подробности", the status action), the Терминал / Редактор tab list, and
opens the "Действия" menu and the modal AlertDialog "Сбросить рабочую папку?" (F11.3), both usually portalled outside
the pane's DOM; the split handle belongs to no region. By the narrow reading a learner who sent, pressed `F6` to
"Окружение" and opened the reset dialog in two-pane mode with Квиз shown is "not away": focus is pulled out of a
modal dialog into the result block behind it. Dev cannot tell which reading is meant.
Rule: A rule that sorts "where focus is" into branches names every focusable place of the page (every region, the
split handle, every menu, dialog and popover that a region opens, wherever it is rendered) and its branch, and states
the rule in identical words in every file that repeats it.

### 2026-11-04: Check bar after a quiz send covers pass and close but not a refusal that finds the quiz passed or closed (#70, judge_design round 5, usability)
`quiz.md` "Check bar after a quiz send" (:177-185) keys every row on the send's own outcome (failed, passed, closing),
and P7/P8 on "a status line made untrue by a quiz send". A stale-attempt refusal (:535-547) re-reads the state and may
find the quiz passed or closed by another browser tab: the panel then shows the review, but the check bar keeps
"Пройдено: 1 из 2" or an enabled "Проверить" in S3, and no row says whether P7/P8 apply. The refusal was fixed for the
panel and the notice but not for the third surface that reports the quiz state.
Rule: When an outcome is added to an event (here: refused), add it as a row to every table keyed on that event's
outcomes, or state in the table why it needs none.

### 2026-11-04: Away rule worded as "environment pane" in one file and "terminal or editor" in another, and R3's own F6 landing sits in the gap (#70, judge_design round 5, consistency)
`quiz.md:52`, `:292`, `:377` and plan P10 / A27 say "environment pane"; `quiz.md:309`, `:507`, `:626` and `ia.md:159`
say "terminal or editor". By `ia.md` R3 (`:217`, F6 table) the "Окружение" region also holds the status bar, and
in two-pane mode `F6` into it lands on "Действия", not the terminal. So the default keyboard way to leave the
panel during a send is "away" by one wording and "not away" by the other, and the result block steals focus
only under the second. Same defect as the usability entry above, here as a vocabulary mismatch between the IA and
the flow.
Rule: A term that decides behaviour ("away", "in the panel") is defined once, with the region names of R3, and
every other file quotes that definition word for word; check it against the R3 F6 landing of each region.

### 2026-11-04: "Away" table kept the open user menu "not away" though it is a modal surface (#70, judge_design round 6, accessibility)
`quiz.md:307` classifies "the user menu and its open menu" as not away ("a short visit"), so a send answered
while it is open moves focus to the result block and sets no notice. The app's user menu is shadcn
`DropdownMenu` (`apps/web/components/user-menu.tsx:36`, no `modal` prop), and Radix menus default to
`modal = true`: `hideOthers` puts `aria-hidden` on the quiz panel and the trapped FocusScope sends focus back
to the menu item. The focus move fails, no notice is set, and the outcome is announced nowhere (4.1.3), in
the same round that wrote "a send answered while a modal is open never pulls focus out of it".
Rule: When classifying focus places, classify by what the component does when open (modal, focus trap,
`aria-hidden` on the rest), read from the app's component and its library source, not by the region it sits in.

### 2026-11-04: "Away" table marks places "not away" that the definition makes away when the panel is hidden (#70, judge_design round 6, usability)
`quiz.md:300` makes "the Квиз panel is not shown" away on its own, but the classification table gives the top bar
(`:307`), "Уведомления" (`:308`), "Проверка" (`:311`) and `body` (`:317`) one unconditional branch, "not away", with
the reason "the shown panel is in front of the learner". Only "Урок" (`:309-310`) and one-pane "Окружение" (`:316`)
are split by the panel axis. With Проверки selected (or one-pane "Окружение" shown) and focus on "Проверить", the
table says move focus to a result block in a hidden panel; the definition says away. `:537` and the #36 test at
`:659` ("a send answered while focus is in the check bar or the top bar also focuses the outcome") copy the
unconditional form, so the app test asserts the wrong branch.
Rule: A classification table over two axes (place x panel shown) splits every row by both axes, or states once that
the first axis wins; tests and focus tables that quote a row carry its condition.

### 2026-11-04: Refusal row of the check bar table skips status lines 5 and 6, which a cross-tab refusal can meet (#70, judge_design round 6, usability)
`quiz.md:192` covers a refused send for "any" status line but its branches are only "quiz open", "summary 7 untrue"
(P7) and "S3" (P8), and `:193` says lines 5 and 6 take no send. Across tabs they can: #69 re-reads check states when
a tab becomes visible (wt69 `checks.md` B9) and may show summary 6 or 5 from another tab's run, while the quiz panel
does not re-read (`quiz.md:581-582`). A send then is refused; P8 empties a true summary 6 just announced, and the
refusal block's lesson line ("when the lesson status ... changed since the page last read it", `:576`, `:361-362`)
may say the lesson outcome a second time, because "last read" is not defined to include a check-state re-read.
Rule: A row that claims "any" prior state is walked against every state of that axis, including the ones a later
row calls unreachable, and every such "unreachable" is checked against the other browser tab's paths.

### 2026-11-04: "Away" table sorts the same DropdownMenu two ways: the open user menu is "not away", the open "Действия" menu is "away" because "a modal must keep focus" (#70, judge_design round 6, consistency)
`quiz.md:307` puts "the user menu and its open menu" in "not away", so a send answered while it is open moves
focus to the result block; `quiz.md:315` puts the open "Действия" menu in "away" with the reason "a modal must
keep focus". Both are the one inventory component DropdownMenu (`design/system/README.md:163`, "top bar,
lesson"), and the app's user menu (`apps/web/components/user-menu.tsx`) is a Radix DropdownMenu with the default
`modal = true`, whose content traps focus (`@radix-ui/react-menu` `MenuRootContentModal`: `trapFocus:
context.open`). So the specified focus move out of an open user menu is impossible in the app (FocusScope sends
focus back) and contradicts the table's own reason. The definition's "another open modal dialog" does not cover
a menu, so the defect is in the one definition too.
Rule: When a classification gives a reason ("a modal must keep focus"), apply it to every instance of the same
component on the page (grep the inventory component and its app usages), not only to the instance in the region
being classified.

### 2026-11-04: Quiz notice relied on a live region that the open modal hides (#70, judge_design round 7, accessibility)
`quiz.md` "Away" (:314-323) classifies every Radix modal menu and AlertDialog as away because `hideOthers` puts
`aria-hidden` on the rest of the page, and then announces the outcome by the quiz notice, which is in the rest
of the page. `aria-hidden` 1.2.6 `hideOthers` spares only nodes matching `[aria-live], script`; the notice
container is specified as `role="status"` with no `aria-live` attribute (quiz.md:422, ia.md R2, lesson
`prototype.html:105-106`), so while the user menu, "Действия" or the reset dialog is open the notice lands in an
`aria-hidden` subtree and is announced nowhere (WCAG 4.1.3). Second gap of the same round: making "Уведомления"
away keeps focus on "Продолжить работу" while a pass or close replaces the option or busy button that R2
(ia.md:171) names as the return target after "Продолжить работу", and R2 has no rule for a return target that
no longer exists, so focus falls to `body`.
Rule: When a rule relies on a live region while a modal is open, check in the library source which nodes the
modal leaves exposed and specify the attribute that keeps the container exposed; when a rule keeps focus on a
control whose dismissal "returns focus", check that the return target can still exist.

### 2026-11-04: Focus table lists the "not away" places by example and leaves the Урок controls in neither row (#70, judge_design round 7, usability)
`quiz.md:570` defines the not-away row as "the Квиз panel shown, and focus in it, on `body`, in the check bar, or
in the top bar with no menu open", and `:572` quotes the away definition. The "Away" table (`:335`) makes the
left-pane tab list, breadcrumbs, lesson header, prerequisite links and the one-pane switch tab "Урок" not away
with the panel shown, but they are in neither focus-table row, so a keyboard learner who Shift+Tabs from
"Отправить ответы" to the Квиз tab has no specified focus target in the table dev tests from. The definition's
"Everything else is not away" is the rule; the table row turned it into a closed list that misses places.
Rule: A row that restates a complement ("not away") says "everything the definition does not name" and gives
places only as examples; diff its list against every "not away" cell of the classification table before sending.

### 2026-11-04: Quiz notice specified as the app's Alert inside a live container without dropping its role="alert" (#70, judge_design round 8, accessibility)
`quiz.md:442-444` makes the quiz notice "an Alert (default variant ...)" inserted into the new `role="status"
aria-live="polite"` container. The app's `Alert` renders `role="alert"` by default (`apps/web/components/ui/alert.tsx:36`).
The same file states the override for the result block (`quiz.md:229-232`) and for `FieldError` (`:519-521`), and the
app overrides it for F2.1 (`notifications.tsx:57-58`, "Not a live alert of its own"). For the notice it says nothing,
and no #36 test covers it: item 9 checks "no role="alert"" only in the quiz panel. Built as written, the notice puts an
assertive live region inside the polite container. That is the double-announcement case round 8 was asked to rule out,
it breaks R2's closed list of live containers, and it makes a polite notice interrupt the learner (WCAG 4.1.3).
Rule: Every time a flow puts an app component inside a live container, or uses it as a message, state its `role` there
and add a test for it. The app's Alert defaults to `role="alert"`, so each use has to say "role removed" or "role kept, because".

### 2026-11-04: "Focus stays where the learner put it" while the away-answer removes that very control (#70, judge_design round 8, usability)
Round 8 fixed one removed return target, the one behind "Продолжить работу" (`ia.md:176-183`). Two other focused
controls that the away-answer itself removes were left out. (1) In the Away table (`quiz.md:352`) the check bar is
away when the panel is not shown, and `:378` keeps focus "on a place reached since (the check bar ...)". P8 then
removes "К окружению" and "Переподключиться" (`:202`, as #69's B10). `:202` says "No check bar control holds focus
(it moved to the result block), so focus does not move", which is false when the learner is away. #69's B10 sends
focus to "Проверить" in this case. (2) The Проверки tab is away. A pass or close drops "Пройти квиз" from the open
quiz row (`:565-571`), and no rule says where focus goes if it was on "Пройти квиз". In both cases focus falls to
`body`. That contradicts `:379-380` ("never sends focus to `body`") and the `ia.md:181-183` sweep ("controls that
no state removes"). The Seams row for "Background changes and focus" (`:795`) also says "focus does not move".
Rule: When a rule says "focus stays", list every control that the same event removes or replaces, in every place
the rule keeps focus. Give each one a target (the check bar's controls go to "Проверить", as #69's B-table does), and add a #36 test.

### 2026-11-04: Round-8 insertions in ia.md left a quiz.md line citation stale, and a new sentence called an installed library absent (#70, judge_design round 8, consistency)
Round 8 added about ten lines to `ia.md` R2 (153-156, 176-183). The plan §8 line numbers were updated, but
`quiz.md:828` still cites "this branch's R3 ("Проверка", `ia.md:218`)"; that item is now at `ia.md:228`. The new
paragraph `quiz.md:329-331` says "`@radix-ui/react-dialog` is not installed in `apps/web` yet". It is installed:
the app takes Radix from the umbrella `radix-ui` 1.8.1 (`apps/web/package.json:24`, `ui/dropdown-menu.tsx:5`), which
pins `@radix-ui/react-dialog` 1.3.1 and `@radix-ui/react-alert-dialog` 1.2.1 next to the `react-dropdown-menu` 2.2.1
that `quiz.md:319` cites. Dialog 1.3.1 calls `hideOthers(content)` from `aria-hidden` 1.2.6, so the check the
paragraph puts off could have been done in this round. The page treats one package as installed and its sibling
in the same umbrella as missing.
Rule: After any edit that adds lines to a file, grep every `file:line` citation of that file in all deliverables
(`rg -n 'ia\.md:[0-9]'`) and re-check each one. Before writing that a dependency is "not installed", look in the
lockfile or in `node_modules/.pnpm`, including umbrella packages.

### 2026-11-04: "The one rule" names an idle stop as a trigger, and the next bullet sends the same case elsewhere (#70, judge_design round 9, usability)
Round 9's R2 "Focus after a background change" (`ia.md:176-193`) calls itself "the one rule; every flow points
here" and lists "an idle stop" among its triggers (`:178`). An idle stop removes the idle warning, so focus on its
"Продолжить работу" (region "Уведомления", none of items 1-4) falls to item 5: the R3 landing of the shown pane, which is
the breadcrumb "Курс" with two panes and the switch tab "Урок" in one-pane mode with "Урок" shown. The next bullet
(`ia.md:201-203`, F10.3) sends the same case to "Запустить снова", or to the switch tab "Окружение". Two targets for
one event, in the rule written to give exactly one. `quiz.md:603` repeats the trigger list.
Rule: When you write a general rule that says "the one rule", grep every existing focus sentence for each trigger
it lists (`rg -n 'focus moves|focus returns|focus goes' design/flows/`). Fold each one in as a place in the order,
or name it as an exception in the rule itself.

### 2026-11-04: Plan §8 line ranges renumbered by eye, two off by one against the diff (#70, judge_design round 9, consistency)
Round 9 grew `ia.md` R2 and FU11 and renumbered the plan §8 ranges again. Two are wrong against
`git diff -U0 39ef0b8 -- design/flows/ia.md`: the R2 live-containers edit is hunk `+161,6` (161-166; line 161
holds "from #36, on a"), the plan says "lines 162-167"; FU11 runs to line 570 (hunk `+541,30` ends at 570,
"`[role="alert"]` or `[role="status"]` descendant."), the plan says "lines 561-569". The orchestrator's brief
copied the second. §8 says "Line numbers are of this branch's files after the edit", so the merge reads them as exact.
Rule: After every edit round, regenerate each §8 range from `git diff -U0 <base> -- <file> | grep '^@@'` (the
`+start,count` of each hunk) instead of shifting the old numbers, and check the first and last line of each range
with `sed -n`.

### 2026-11-04: Unscoped fallback change in ia.md R2 not carried to the lesson acceptance it rewrites (#70, judge_design round 10, consistency)
This branch changed the "Продолжить работу" fallback in `ia.md:200-202` from "the first focusable element of
"Урок"" to "the R3 landing of the shown pane's region", for every release (no "from #36"). In one-pane mode with
"Окружение" shown the two differ: the switch tab "Урок" (R3 row "Урок, one-pane mode") against the switch tab
"Окружение" (R3 row "Окружение, one-pane mode"). The plan §8 (`plans/70-quiz-prototype-design.md:379-381`) records the change, but §9
(`:414-419`) tells the author that `acceptance.md:264` "keeps its statement for the release before #36", and N14
(`:491-496`) adds only the gone-target rule. `acceptance.md:264-266` says "else the first focusable element of
"Урок": ... the switch tab "Урок" in one-pane mode (R2)", so a faithful author phase keeps a sentence that
contradicts R2 now, not only after #36.
Rule: When a flow edit changes behaviour outside the issue's release gate, grep every acceptance line that
states the old behaviour (`rg -n '<old phrase>' design/pages/`) and give the plan an item that rewrites it
unscoped; never leave it under a "before #36 keeps its statement" list.

### 2026-11-10: Quiz flow left the Проверки empty text undefined once a quiz attempt exists (#70, judge_ux round 1, usability)
`checks.md:522-524` shows "Попыток пока нет. Нажмите "Проверить", когда будете готовы." "before any run", when
every check is "Не запускалась". `quiz.md` "Empty states" (`:661-662`) adds the quiz row's "Ответы не
отправлялись" but never says whether that text stays after a quiz send, when no run has happened yet but the
quiz row counts sent attempts. The prototype kept it next to "Неудачных попыток: 3 из 3" in F15.6, so the learner
reads "no attempts yet" under a closed quiz. Two senses of "попытка" (`ia.md:32-33`) then stand in one panel,
which `ia.md:40` rules out for "Вопрос".
Rule: When a flow adds a check kind, re-read every empty and "before any run" rule of `checks.md` against that
kind's states, and say in the flow whether each one still holds.

### 2026-11-16: Kept a visible load error silent for an away learner with the panel shown (#99, judge_design round 1, accessibility)
`quiz.md:413-418` keeps a quiz load "Повторить" that fails while the learner is away silent, and justifies it by
cost ("a load spends and changes nothing"). The away set includes places where the Квиз panel stays shown (two
panes with focus in "Окружение", on the split handle, in "Уведомления", in an open menu or modal dialog,
`quiz.md` away table). There the Skeletons are replaced by the visible text "Не удалось загрузить квиз" with no
focus move and an Alert with no role: a status message (result of an action, existence of an error) that is not
programmatically determinable, WCAG 4.1.3. Cost to the learner is not an exemption in 4.1.3.
Rule: When a flow keeps an outcome silent, split it by whether its text becomes visible without a focus move; if
it does, give it a live container (or the existing notice) or show in the flow why it is not a status message.

### 2026-11-16: Parked the most common silent quiz load error as "open for #36" after calling the same change a status message (#99, judge_design round 2, accessibility)
The round-1 rework split the away case by visibility and wrote (`quiz.md:422-424`) that a load error replacing the
Skeletons in view with no focus move is "a status message (the existence of an error)". The same visible change
with the learner not away (focus on the Квиз tab after activating it, on `body` after a Safari click on the tab,
on the panel h2 after "Пройти квиз") stays silent, and `quiz.md:986-991` calls it "open for #36", a dev issue
that implements only designed pages (ADR-0006). That is the common path of a failed first load, so the flow
announces the rare away case and leaves the usual one failing WCAG 4.1.3, against the round-1 rule just above.
Rule: Apply the visibility split to every learner position, not only the one the finding named; a status message
the flow itself identifies is designed in the same task, never deferred to a dev issue as an open question.

### 2026-11-16: Added a closed-set row in the flows but not to the author work list for the page copy of that set (#99, judge_design round 2, consistency)
The round-1 rework added quiz notice row 12 "Не удалось загрузить квиз." to `quiz.md` and `ia.md:79` ("rows
1-12") and listed lesson acceptance AC44, AC47-AC49 and the copy row `:988` for the author. It left out the P9
block of `design/pages/lesson/acceptance.md:725-766`, which restates the flow: `:730-731` "A load or retry
answered while away announces nothing", `:733` "never ... or for a load", the notice text table `:741-751`
("exact; no other text exists", rows 1-11 only), the "Drawn:" list, the Removal list (no "Повторить"
starting a load) and "Открыть квиз" focusing only the result block or the send error. The author follows the
list, so the page acceptance would ship a closed set that contradicts `ia.md:79`. Also `ia.md:207` still says
the notice container is "used only for a send" before naming its second use.
Rule: When a flow changes a closed set or a "never" rule, grep every page acceptance and the system README for
the set's members and the rule's wording (`rg -n 'for a load|announces nothing|no other text'`), and list each
hit in the author work items or say why it stays.

### 2026-11-16: Live container mounted with its tab panel and written a frame after a fast load (#99, judge_design round 3, accessibility)
The quiz load status container is "present and empty whenever the panel is rendered, from the moment a load
starts" and written "after `aria-busy` is removed, at least one rendered frame later" (`quiz.md:295-299`,
`ia.md:227-233`). Radix unmounts an inactive tab panel (`quiz.md:733`, `lesson-tabs.tsx` has no `forceMount`),
so on a first load from the Квиз tab the container enters the accessibility tree at the same moment the load
starts, and a local server that fails in a few milliseconds gets its text set tens of milliseconds later. That
satisfies "never inserted together with its text" only literally: React Aria's live announcer waits 100 ms after
creating its regions because "less than 100ms were not consistent when announcing with Safari"
(`react-aria/src/live-announcer/LiveAnnouncer.tsx:32-34`). The case round 2 failed on (first load, not away)
stays silent in Safari/VoiceOver whenever the failure is fast.
Rule: For a live container that mounts with its panel and can be written by that same mount's request, state a
minimum age before the first write (a named constant with its source), counted from when the container entered
the accessibility tree, not from the last frame.

### 2026-11-16: New panel element added to R2 but not to the panel's DOM-order list (#99, judge_design round 3, consistency)
Round 3 placed the quiz load status container "inside the Квиз tab panel right after its heading (outside the
Skeletons and the load error)" (`quiz.md:293-294`, `ia.md:225-226`), but `quiz.md` "Quiz panel, in DOM order"
(`:231-252`) still lists items 1-7 without it, and "Loading" (`:256-257`) still says that after the heading
"everything after it is replaced by Skeleton blocks", which the container contradicts. The F19 counterpart names
its container in its structure (`progress.md:333`). The same round left the lesson acceptance count "a sixth live
container" (`acceptance.md:1671`) out of the plan's work items, although the new container makes it wrong.
Rule: When an element joins a component, grep every structural list of that component ("in DOM order",
"everything after", composition paragraphs) and every count of its kind ("sixth", "four ... five"), and update
or list each one.

### 2026-11-16: Minimum age for a live container that mounts with its panel (#99, judge_design round 3, accessibility, architect fix)
Round 3 wrote the quiz load status container "one rendered frame after `aria-busy` is removed". Radix unmounts
an inactive tab panel (`lesson-tabs.tsx` has no `forceMount`), so a first load from the Квиз tab mounts the
container in the same moment the load starts, and a fast local failure writes it tens of milliseconds later,
which Safari with VoiceOver can miss. The fix is `QUIZ_LOAD_STATUS_MIN_AGE_MS` = 100 ms, counted from when the
container entered the accessibility tree, the write waiting for the latest of the frame, the text gap and the
age. Source: React Aria's live announcer waits 100 ms after creating its regions, "less than 100ms were not
consistent when announcing with Safari" (adobe/react-spectrum
`packages/react-aria/src/live-announcer/LiveAnnouncer.tsx:32-34`). The F19 history status container has the
same mount, recorded as `ia.md` FU15.
Rule: A live container that mounts together with its panel waits a minimum age (100 ms, the React Aria
source above) before its first write, counted from its entry into the accessibility tree; check every other
container that lives inside a tab panel for the same mount and either apply the rule or record a follow-up.

### 2026-11-16: A flow fix not carried into the acceptance copies, and "all N lists" counted the state label (#99, judge_design round 4, consistency)
Round 4 fixed `quiz.md` "Loading" (the heading and the quiz load status container stay, items 3-8 become
Skeletons), but the plan left lesson `acceptance.md:431` ("everything after it is six Skeleton blocks") and AC44
`:1484` ("the heading stays, the rest is Skeleton") as they are, so both now contradict the flow. The re-derived
prototype counts were right, but "the new name joins all 18" (text-error) and "which all take the new name" (23
quiz-load-error lists) include the state label templates `prototype.html:42` and `:147`; proto.js labels a state
from the first `[data-state-label][data-state~=name]`, so the new state would be listed with the old label. The
dashboard item excluded its label span correctly. Also: the container placed "right after `#quiz-heading`
(`:2079`)" lands before `#quiz-code-heading` (`:2080`), the shown heading in `#state-quiz-code`; `proto.css:853-854`
is a third copy of the quiz DOM order left without the container while the plan says no proto.css change; AC44's
"rows 10-12" (stale since base) is to be "renumbered" with no target (the load rows are 14-19).
Rule: When a flow sentence is reworded, grep every copy of the old claim (acceptance rows, ACs, README, proto.css
comments) and list each in the plan; when a plan says "all N lists take the name", say which lines are excluded
(state label templates or spans) and give every renumbered reference its new number.

### 2026-11-16: Four of six round-4 findings were stale citations or counts a grep would have caught (#99, judge_design round 4, consistency)
Round 4 failed on acceptance lines still saying "everything after the heading is Skeleton" against the new DOM
item 2, state counts that included the label templates (`prototype.html:42`, `:147`; proto.js:210 labels a
state from the first matching template), a container placed before `#quiz-code-heading`, a third copy of the
quiz panel DOM order in a proto.css comment, an AC row reference to the wrong rows, and `proto.css:294` for
`:295`. Each was a fact the plan stated without printing its source.
Rule: before handing over a plan, run a mechanical pass: print every cited line next to its citation (a script
over the plan), grep every copy of each list you change across design/ (prototype.html, proto.css, proto.js,
README.md, acceptance.md), and count state names from the files with a whole-token grep, saying which matches
are lists and which are templates or ids. Never count by hand.

### 2026-11-16: Copies of a composition searched by its heading phrase only (#99, judge_design round 5, consistency)
The round-4 fix grepped "DOM order" to find every copy of the quiz panel order, so the lesson acceptance
composition paragraph (`design/pages/lesson/acceptance.md:288-289`, "`.quiz` (`.quiz-intro` with the `h2` and
`.quiz-header`)") got no work item, although the plan puts the quiz load status container inside `.quiz-intro`
and the paragraph right above it (`:275`) lists the history status container in the F19 composition. After the
author phase that paragraph would say `.quiz-intro` holds two things when the page and README hold three.
Rule: find the copies of a list by the class or element names it contains (`rg 'quiz-intro'`), not only by the
title phrase of the source section, and give each hit a work item or a stated reason to leave it.

### 2026-11-16: Added a notice row without listing the acceptance block that defines the notice (#99, judge_design round 2, usability; moved from architect_mistakes.md, the DESIGN architect role is the UX researcher)
Round 1 rework added quiz notice row 12 and listed lesson acceptance AC44, AC47-AC49, the copy table and the state
rows as author work items, but not the Interactions block that is the acceptance notes' own definition of the
notice (`design/pages/lesson/acceptance.md:730-731` "A load or retry answered while away announces nothing",
`:732-733` "never ... for a load", the notice table `:740-752` "exact; no other text exists", the "Drawn" line
`:754`, the Removal list `:755-759` and the "Открыть квиз" target `:762-763`). AC47 checks the notice title
against that table, so an author who follows the list ships acceptance notes that forbid row 12 in one place and
require it in another.
Rule: When a design changes a rule, grep every page acceptance file for each sentence the old rule produced
(here `rg -n 'for a load|notice|Открыть квиз' design/pages/`) and list each hit as a work item or say why it stays.

### 2026-11-18: Put quiz explanation code blocks in scope but left their composition to a dev issue with no record (#136, judge_design round 1, usability)
The #136 flows say a fenced block in a quiz explanation follows "Scrollable code" with the name "Блок кода",
and that "whether it has "Копировать" is #36's to decide" (`design/flows/quiz.md:608-611`). #36 is an open dev
issue (feat(web)); its list "Requirements for #36" (`quiz.md:791-`) does not mention it, and `ia.md` "Open
follow-ups" has no entry for it. The header decides the Tab order (one stop or two) and the ring corners, so the
`ia.md` R4 bullet names Теория, Задание and the prompt block but not the explanation block. A design question
handed to a dev issue that never lists it is a dead end: the dev of #36 builds whatever falls out.
Rule: A design question you take into scope but do not decide becomes either a numbered item in the target
issue's requirements list or an `ia.md` follow-up; never a prose "is #N's to decide" alone.

### 2026-11-18: Moved a rule "to one place" but left full copies, kept a done follow-up, and kept "unchanged" reasons the new scope falsified (#136, judge_design round 1, consistency)
D1 moves the code-block scroll rule to README "Scrollable code", yet `design/flows/quiz.md:602-609` says the rule
was moved "from this bullet" and still restates the overflow condition, the three attributes and keep-until-blur,
and `design/flows/lesson-environment.md` "Code blocks that scroll" states them a third time; three statements of one
rule are the drift D1 exists to prevent. FU10 stays in `ia.md` "Open follow-ups" as "Resolved by #136", although
the section says "Remove an item when its issue is filed and linked here, or when it is done" and #123 removed FU5
that way. And the design puts quiz explanation blocks in scope while listing `quiz.md:783` and lesson
`acceptance.md:1226-1227` ("only a prompt's code block scrolls") as unchanged "prompt block rule kept".
Rule: After moving a rule, leave only the pointer plus what is local (name, scope, reasons) in each old place; remove
a follow-up the task completes; and re-check every "no item" reason against the final scope, not the starting one.

### 2026-11-18: Removed a navigation link without re-checking WCAG 2.4.5 Multiple Ways per page (#218, judge_design round 1, accessibility)
A218-3 removes the top-bar "Курс", which was a way to the catalog on every page, and the design never states
2.4.5 for the #220 pages. A course with no `ready` lesson (Q6, F20 empty states) then has exactly one link to its
catalog on the whole site, its dashboard block heading: no module rows, no lesson breadcrumb, no all-passed Card,
and not-found way (4) is a typed URL. `ia.md:750-754` and A218-3's "the cost is one link" count steps from the
dashboard, not independent ways.
Rule: When a design removes or replaces a navigation link, list every page the link reached and name two
independent ways (nav, list, breadcrumb or related links, search, site map) to each page in each state, or record
why a page is exempt.

### 2026-11-18: Amended a flow sentence but left the old reference beside it, and named one focus target two ways (#218, judge_design round 1, consistency)
`progress.md:94-99` adds "from #220 a retry that loads focuses the Card heading (row "dashboard progress error")"
and keeps, in the same bullet and unqualified, "The retry and its focus are unchanged (row "dashboard progress
section" ... in the section)", a row `ia.md:326` now scopes "until #220". The "Card heading" focus target is
"Следующий урок" alone in A218-10 (`courses.md:346`) and `ia.md:369`, but "Следующий урок" or "Все доступные
уроки пройдены" in the retry rows `ia.md:325` and `:327`, although A218-10's own case (the Card course broke
meanwhile, the rest all finished) leaves an all-passed Card. A new term, "Card course", was introduced as
"`ia.md` vocabulary" in `courses.md:19-22` with no vocabulary row in `ia.md`.
Rule: After a "from #N" insertion, read the rest of its bullet and qualify every old sentence ("until #N"); when
a target or term is defined in two places, grep its name across `design/flows/` and make every statement name
the same set; a term a flow cites as `ia.md` vocabulary gets its row in the vocabulary table.

### 2026-11-18: Treated "finished" as "passed" in new copy rules, and left a removed course block without a focus target (#218, judge_design round 1, usability)
`courses.md:95-98` says a course whose `ready` lessons are all finished shows "Пройдено уроков: M из M", and A218-2
and the "Dashboard by course count" row "every `ready` lesson finished" give it the all-passed Card "Все доступные
уроки пройдены". A finished lesson may be "Не пройден" (F14, `ia.md` lesson status set), and the course line counts
passed lessons (dashboard AC4), so both texts misinform for a course with a closed check. Separately, A218-10 and
F21 name focus targets for a re-read that changes a block ("that block's heading") but none for a re-read that
removes a whole block, the retried one included, although the design itself says the learner's own edits of
`course/` change courses between reads, and Q5 suggests renaming directories with a prefix, which under Q1 removes
the old id. R2 says focus never falls to `body`.
Rule: When a rule maps a state to copy, check each word of the copy against every member of the state ("finished" =
passed or closed); when a re-read can change a set of blocks, name the focus target for a block that disappears,
not only for one that changes.

### 2026-11-18: New focus rule not walked through its own author sample, and an "only through" left false by it (#218, judge_design round 2, usability)
The round-1 rework wrote the dashboard focus fallback (A218-10: a removed block's focus goes to the next block's
heading, else the previous block's, and only then the Card heading). The author work list sample
`courses-block-renamed` (`plans/218-design.md:79-80`) still says "or on the Card heading when it was the last block",
which the rule sends to the preceding block's heading; the product designer would draw the wrong target. The same
rework made every dashboard retry re-read the whole page, yet `progress.md:140-143` still says F18.3-F18.5 "change only
through the progress section's "Повторить", which moves focus to what it shows" and points only to the until-#220 row.
Rule: After writing an ordered rule, walk every author sample that names it (last block, first block, renamed) through
the rule step by step; after widening what a control re-reads, grep "only", "never" and "changes" in every flow that
describes the re-read parts and scope each sentence.

### 2026-11-18: A focus chain summarised with a branch the states table makes unreachable (#218, judge_design round 2, consistency)
The removed-block chain ends "else the Card heading" in three places (`courses.md:186` F21 error states,
`ia.md:332` R2 row "dashboard course block error", A218-10 (3) "after (2) finds no block"). No block left means the
root holds no course, which is the root error by Q3 and "Dashboard by course count" row 1, so no Card exists; the
reachable end is A218-10 (5), the root error h2, which the two summaries leave out.
Rule: When a fallback list is summarised elsewhere, check each step against the states table and end the summary on
the step that can actually occur, not on the one that reads naturally.

### 2026-11-19: A removed F18 row walked only for "its section is gone", and the rule's summary skipped its own step (1) (#218, judge_design round 3, usability)
`progress.md:148-150` says a dashboard re-read removes a focused F18.3 or F18.4 row only when "no Card is left, so the
sections are not rendered". A course block retry that loads adds that course's attempts and weak checks, so the five
newest rows reshuffle and the focused row can drop out while the Card and both sections stay; a course that broke
meanwhile drops its rows the same way. A218-10 step (4) then sends focus from the bottom of the page to the first
course block's heading, against the rule's own reason ("the nearest one keeps the learner's place"). The same rule
ends "So a chain that starts at a block ends at step (2) or (5)", which skips step (1), a block that remains.
Rule: For every place a fallback names, walk each way the re-read can remove the focused element (the container gone,
and the item gone from a container that stays), and check every summary sentence against every step, the first included.

### 2026-11-19: A rewritten work-list sample names the heading link as the focus target, not the h2 (#218, judge_design round 3, consistency)
The round-2 rework rewrote `courses-block-renamed` (`plans/218-design.md:81-83`) to "focus moves to its heading link
"Пробный курс"". A218-10 step (2), `ia.md:332` and F21.3 all name the block heading, the h2 with `tabindex="-1"`, and
the link is only its content. The neighbour sample `courses-block-removed` correctly says "the last block's heading".
A product designer who draws the sample focuses the `a`, so a screen reader says "link" where the rule says it reads a
heading, and the prototype differs from the R2 row.
Rule: In every sample that walks a focus rule, name the target element exactly as the rule does (h2 `tabindex="-1"`,
not the link inside it), and diff each sample's target against the R2 row before closing the rework.

### 2026-11-20: The single A218-10 definition leans on a render rule that the progress error breaks (#218, judge_design round 4, consistency)
Round 3 rework made `ia.md` R2 A218-10 the one definition, but step (5) (`ia.md:406-408`) justifies itself with
"which happens only with no Card, because the sections render exactly when the Card does", copied from
`courses.md:45` and `progress.md:115`. `progress.md:95-97`, `courses.md:108-112` and "Dashboard structure" item 3 say
that from #220 the progress error shows with a Card and none of F18.3-F18.5 renders then, so a block retry whose
re-read finds the database down removes a focused F18.3/F18.4 section while the Card stays. Defining a rule once does
not help when the definition cites a premise that two other places contradict. In the same rework the guard's
"on `body`" (`ia.md:362`) is not said to be judged before or after the re-read renders, and the two readings give the
`attempts-row-reshuffled` sample two different targets (the block heading or the "Последние попытки" h2). Also
`courses.md:108-109` and `dashboard.md:48` say the no-progress Card takes "the first readable course in list order",
while A218-2 (`courses.md:324-325`) says "the first readable course with one" (`ready` lesson).
Rule: Before closing a single-definition rework, check every premise the definition cites ("only", "exactly when",
"always") against each state that can change it (progress error, root error, empty course), and say when each
condition of an interacting rule (the guard's "on body") is evaluated.

### 2026-11-20: Progress lost at a block retry explained only to a learner who had tabbed away (#218, judge_design round 5, usability)
Round 5 added sample `attempts-progress-lost` and A218-10 step (5): a learner who tabbed on to a "Где трудно" row
before the re-read finds the database down is sent to the h2 "Прогресс недоступен". The main F21 path was not walked
on the same data: focus stays on block 2's "Повторить", course 2 loads, focus goes to the block heading (R2 row
"dashboard course block error", `ia.md:333`), and the block shows the heading only (A218-11, `ia.md:763`). The
progress error appears above, not live, and nothing reads it; the next Tab leaves `main`, because F18.3-F18.5 are
gone. A218-10 calls these changes silent "because between two reads only the learner's own edits of `course/` and
their own activity change them" (`ia.md:396-397`), which a database outage falsifies. `courses.md` F21 error
states do not list the case either.
Rule: When a sample walks a new focus target on one data set, walk the same data with focus where the flow's own
steps leave it (the retried control), and check every "because" of a silent change against each cause that can
produce that change (database, root, the learner's edits).

### 2026-11-20: Two #218 statements of what a block shows during the progress error, and a trigger restated in other words (#218, judge_design round 5, consistency)
A218-11 (`ia.md:763`) says "Every readable block then shows only its heading", and the round-5 plan (`plans/218-design.md:420`)
uses "readable block" for empty-form blocks too. "Dashboard structure" item 4 (`ia.md:835-837`) drops only the "readable,
with a `ready` lesson" form to its heading and keeps the empty form's "В курсе пока нет готовых уроков" in every state. So a
database outage with one course ready and one without a `ready` lesson renders block 2 two ways. Separately, `courses.md:58`
opens the F20 error bullet with "Progress cannot be read (database down), a course can:" and then names the Card and the
progress error, but a readable course with no `ready` lesson gives neither (A218-2, A218-11, "Dashboard by course count"
rows 3 and 6). Both are the same rule stated twice in different words, the class round 5 set out to remove.
Rule: After a single-definition rework, grep each rule's subject nouns ("readable block", "a course can", "heading only")
in every file and in the other ia.md rules, and check that a scope word means the same set (readable course vs readable
form) wherever it appears; a pointer's lead-in names the state only by the rule's own link, never by a shorter condition.

### 2026-11-20: A new focus override took the retry's "Fails again" move and left the learner's own result unsaid (#218, judge_design round 6, usability)
Round 6 A218-10 (a) (`ia.md:421-429`) sends every focus move of a re-read that newly shows the progress error to its h2
"Прогресс недоступен", the row's "Fails again" target included. (b) (`ia.md:430-442`) says only newly shown errors, and the
retried block's error was shown before, so nothing says it. A block retry that fails again while the database newly goes
down (announce table B4) therefore reads exactly what a retry that loads reads (B3): "Прогресс недоступен", and the learner
cannot tell whether their course loaded. The reason for (a) (`ia.md:425-426`, "the retried course's own outcome is one
block that shows its heading only meanwhile") holds only for "Loads". R2 itself says a "Fails again" move exists so a
repeated failure is read (`ia.md:349-355`); the override removed that for this case.
Rule: When a new rule overrides a focus target, list every outcome column it replaces and, for each, say how the outcome
that target used to announce is still announced; check the rule's "because" against each column, not only the first.

### 2026-11-20: A218-10 (a)'s reason restates what a block shows during the progress error (#218, judge_design round 6, consistency)
Round 6 made "Dashboard structure" item 4 (`ia.md:876-893`) the one definition of block forms: only the readable form
drops to its heading while progress cannot be read; the empty form keeps "В курсе пока нет готовых уроков" and the error
form keeps its Alert. A218-10 (a) (`ia.md:424-426`) links item 4 and then, in the same sentence, says "the retried course's
own outcome is one block that shows its heading only meanwhile", which is wrong when the retried course loads into the
empty form or fails again (error form). The round-6 rule table lists `ia.md:424` as a pointer that "adds only local data",
so the pointer walk missed the clause after the link. Separately `courses.md:284` says "The error block's heading" where
item 4 names the form "error form" wherever a block's form is meant.
Rule: Read each pointer to the forms to the end of its sentence: a link followed by a description of what a block shows
is a second definition; name the form ("a block in its error form") or the outcome, never what it renders.

### 2026-11-20: The narrowing to normal states left a broken course's block and retry described in "Questions for #219" and a decision reason (#218, judge_design round 7, consistency)
Round 7 moved every error state with several courses to #222 and replaced each statement with a "see #222" line;
"Dashboard structure" item 4 (`ia.md:752`) says a broken course's block is #222's. `courses.md:135-136` (Q4) still says
what such a block shows: "each block shows the course error under its directory name", the block error form #222 owns.
`courses.md:119` ("a broken course keeps its id and its block") and `courses.md:154-155` (Q9, "what a block heading ...
need when the rest of the tree fails") state the same #222 condition, that a broken course has a block with a heading.
`courses.md:236-238` (A218-14 reason) rests on the broken catalog's "Повторить" and "its own retry", which `catalog.md:45`
moves to #222 ("which ids, the retry"). The orchestrator's grep patterns were the removed rules' own wording, so prose
in Q-text and reasons that paraphrases them was never hit.
Rule: After moving a state out of scope, grep its subject nouns ("broken", "block", "course error", "retry",
"Повторить", "rest of the tree") in Questions, Requirements and Decisions reasons too, and turn every sentence that says
what the moved state shows or does into a "see #<issue>" line.

### 2026-11-20: A new catalog keyboard sentence states the F6 landing in every course error, which R3 scopes to #222 (#218, judge_design round 8, consistency)
#218 added to `catalog.md:72-73` (F5 keyboard path): "`F6` to `main` lands on the first module link, or on "Повторить"
in the course error." It carries no "until #220" and no "see #222", so it also states the landing in the catalog course
error with several courses. `ia.md:441` (R3) scopes the same clause "(with several courses, from #220: see #222)", and
`catalog.md:45` moves that error's retry to #222. The round-8 table (row "catalog.md:72") kept it as a restatement of
main's R3, but main's R3 had no several-courses case to scope, and the line restates an R3 rule in a second file.
Rule: A sentence #218 adds about an error state carries the same scope marker ("until #220" / "with several courses,
from #220: see #222") as its rule in `ia.md`, or is a pointer to that rule only; check a "kept: restates main" verdict
against the current `ia.md` text, not main's.

### 2026-11-20: F22 keyboard path restated the "Урок" landing without R3's one-pane condition (#218, judge_design round 9, accessibility)
`courses.md:109` says "`F6` to "Урок" lands on the course crumb (`ia.md` R3 table); the module crumb is the next Tab",
and the next sentence (:110-111) is about 320 px and 200 % zoom. R3 row `ia.md:415` gives the crumb only in two panes or
full width with no "Окружение"; row :417 lands on the switch tab "Урок" in one-pane mode (below 1024 px with an
environment), where the crumb is the next Tab after the switch. So the sentence is false in the very widths it then
discusses. The round-9 table justified it by quoting only the "course was read" half of row :415.
Rule: A flow that names an `F6` landing either points to the R3 row ("`F6` to "Урок": `ia.md` R3 table") or copies
every condition of that row (width, pane, course state); check each restated landing against every R3 row of its region.

### 2026-11-20: Round-10 sweep closed the class outside ia.md but left #218 restatements of R3/R4 landings inside it (#218, judge_design round 10, consistency)
Round 10 made every flow sentence a pointer, and its "Agreement inside ia.md" check walked the catalog, not-found,
dashboard and "Урок" landings only. Two #218-written sentences in `ia.md` still restate a landing defined elsewhere in
the same file: R6 "Course scope (#218)" ends with "The `F6` landing on "Верхняя панель" stays "Академия"" (`ia.md:600`),
a third statement after the R3 row (:410) and R6's "`F6` lands on "Академия" ... in every release" (:557), which the
"from #220" row of "Top bar by release" (:552, "as from #30") already covers; and Dashboard structure "Tab order and
`F6`" opens with "the skip link moves focus to `main` (R4)" (:772), a second statement of R4's skip-link move
(:462-464), while the until-#220 R3 bullet and `dashboard.md` point to R4 for it.
Rule: When a round closes a "stated once" class, grep every landing verb (`lands`, `moves focus`, `next Tab`, `stays`)
in the lines the task added to `ia.md` as well, and turn each one that is not the defining place into a pointer.

### 2026-11-20: Round-11 rewording kept a counted summary that is narrower than the rules it names (#218, judge_design round 11, consistency)
`ia.md:726-728` (Dashboard by course count) says "With exactly one course the page is the #30 page with three
changes: the top bar, the course name in the Card, and the progress part inside one course block". Round 11 turned
each item into a pointer but kept the count. With one course from #220 the page also changes in two places the other
rules define: the end Card can read "Все доступные уроки завершены" (vocabulary row "end Card", from #220 at every
count, `courses.md` A218-2), and with no `ready` lesson there is no Card at all, only a block in the empty form with a
heading link (the same table's row 3, Dashboard structure item 4), where #30 showed "В курсе пока нет готовых уроков"
in the Card's place and `F6` to `main` landed on `main` itself (R3 until-#220 bullet). A counted list of what other
rules define is a narrower restatement, and it is wrong as soon as one rule adds a change.
Rule: A summary that counts or lists what other rules change ("N changes", "only X and Y") is a restatement: drop
the count and name the rules, or check it against every rule and every row of its own table before keeping it.

### 2026-11-20: Round-12 sweep kept an "every" definition its own table contradicts, and two ways/steps lists narrower than the rules (#218, judge_design round 12, consistency)
`ia.md:585-586` (R6 "Course scope") opens "Every course control is built from one course, the course in view", and
the table four lines below says the "Другие курсы" links (`ia.md:596`) are built from "each other course of the
root", which is not the catalog's course in view. The round-12 table kept it as "R6 Course scope definition". The
same sweep kept `ia.md:908-912` (Multiple ways, catalog): with two or more courses it lists the end Card's "Открыть
курс" among the ways, with one course it does not, although the end Card exists at one course (Dashboard by course
count row 2, A218-2). And `ia.md:891-892` reaches lessons "in two through the catalog, or in one for a block's next
lesson (A218-4)", while A218-5 removes the block link of the Card course, whose next lesson is one step away only by
the Card (A218-2), and from #35 the F18.3/F18.4 rows (A218-13) reach lessons in one step too.
Rule: Before keeping an "every"/"each" sentence or a list of ways or cases as "a definition", read it against every
row of the table or list it introduces and against each rule that adds or removes an element of that set (here
A218-2, A218-5, A218-13, A218-14), and make the per-count variants of one list name the same elements.

### 2026-11-21: Q1's "Depends on it" list built from citations, missing Q5, which restates Q1 without citing it (#218, judge_design round 13, usability)
The round-13 rewording of `courses.md:133-135` (Q1) lists what depends on the course id rule as "the places that cite
Q1". Q5 (`courses.md:144-145`) orders the course list by "the course id (the directory name, ...)", which is Q1's
assumption restated in its own words with no "Q1" in it, so a grep for citations missed it. If #219 keeps a
`course.yaml` `id` with no tie to the directory, Q5's assumption contradicts itself (id order and directory order
diverge), and with it the list order of the blocks and of "Другие курсы" (vocabulary row "list order"); Q1's list, the
one place a #219 decision is checked against, does not name it.
Rule: A "depends on it" list is built from what uses the assumption's content, not from what cites its id: grep the
assumption's nouns ("directory name", "course id") as well, and make every user cite the assumption by id, so the
citation list and the dependency list are the same set.

### 2026-11-21: The round-13 sweep left the #218 lines of the other flow files and the "Открыть курс" (environment rejected) row unchecked (#218, judge_design round 13, consistency)
The sweep covered ia.md and courses.md only. `lesson-environment.md:220-221` (#218 text) restates the R6 "Course scope"
lesson row ("the catalog of the lesson's own course, the URL's") instead of pointing to it, as `dashboard.md:64` does for
the end Card. The same row is missing from lists that claim the ways to or changes of it: `catalog.md:16-21` F5 Entry
(every lesson-page way except that "Открыть курс"), `courses.md:259-260` "No change to ... the environment ... flows
beyond the top bar and the breadcrumb's first crumb" (#218 set that button's target), and its own "When it is not
rendered" cell `ia.md:600` points to "the R3 table", whose only row is the two-pane `F6` landing (`ia.md:425`), not the
F8 state. Same class elsewhere: `ia.md:888` not-found Flows "F22 (way (4))" while `courses.md:109` sends every lesson-URL
way (3 and 4) there, and `ia.md:694-695` A218-12 names "Главная" as "the way on" after round 13 added "Академия" to F22
Exit for that very reason.
Rule: Run the every/only/list sweep over every #218 line of every changed flow file, and for each R6 "Course scope" row
grep the control's label in all flow files: each mention points to the row, and each list of ways, entries, exits or
changes names it.

### 2026-11-21: Round-14 sweep fixed a row-1 restatement in courses.md but kept its twin in dashboard.md (#218, judge_design round 14, consistency)
`dashboard.md:43-44` ("From #220: the course root that cannot be read, or holds no course: the root error, [Dashboard by
course count] row 1") restates row 1's condition cell (`ia.md:724`), which rests on Q3, an assumption #219 may overturn.
The same round fixed the identical wording in `courses.md:58` as a restatement ("The root error: row 1 (Q3)") while the
dashboard table kept it as "exact: the row is named by its own first cell". One fact, two verdicts in one sweep. The twin
of another fix of that round stands too: `ia.md:914` "Sign-in with no `next` also lands on it (F1.4)", the phrase
`courses.md:38` replaced as narrower than F1.4.
Rule: When a sweep fixes a sentence, grep its wording (and its key phrase) in every changed file and give each hit the
same verdict; a row is named by its number or id, never by quoting its condition cell.

### 2026-11-21: Round-15 condition sweep left a paraphrase of not-found way (3) in courses.md Q9 (#218, judge_design round 15, consistency)
`courses.md:162-163` ("a lesson page reads only the URL's course (a course id the root does not hold is not-found way
(3), `ia.md` page inventory)") paraphrases the from-#220 condition of way (3) (`ia.md:888`, "a lesson URL whose course id
names no course of the root") before naming it, the round-14 pattern. The round-15 sweep grepped only the wording of the
round-14 finding ("cannot be read|holds no course|no `next`") and rechecked only the rows marked "exact" in round 14;
Q9 was marked "fixed" in round 14 for another reason, so nobody read it for a restated condition.
Rule: A restated-condition sweep greps the condition words of every rule the files point to (each not-found way, each
dashboard row, each A218 condition) and reads every hit, whatever verdict the row had before.

### 2026-11-21: courses.md gives every #218 decision a second title, several carrying the rule's condition (#218, judge_design round 16, consistency)
`courses.md:198-199` says the list "gives the decisions' titles", but none of the eleven bold titles equals the title the
decision has in `ia.md` (A218-12: "The not-found action." at `ia.md:689` vs "Not-found offers "Открыть курс" only in way
(4)." at `courses.md:239`; A218-13: "Cross-course rows." at `ia.md:693` vs "...rows name the course only with two or more
course blocks." at `courses.md:244-245`; A218-8 adds "no "Главная" crumb", A218-1 "no `/courses` page"). So one id has two
names, and the courses.md one restates the condition `ia.md` defines next to the id, the pattern ia.md:649-650 forbids.
The round-16 sweep checked parentheses and "is <rule>" clauses only and marked the titles "own title".
Rule: A decision has one title, written once in its defining place and copied verbatim wherever the id is listed; a
title never holds the rule's condition (counts, "only in", "no X") unless the defining place's title holds it too.

### 2026-11-21: A218-14 reason still restates the vocabulary row "other-courses list" (#218, judge_design round 17, consistency)
The round-17 rework of the `courses.md` A218-14 reason dropped "never shown with one course" but kept "It is a section of
the catalog, not a course list page (`ia.md` vocabulary row "other-courses list"), so [A218-1] holds" (`courses.md:248-249`).
The words before the pointer are the row's meaning cell ("the catalog section of [A218-14], not the course list",
`ia.md:37`), and `ia.md` A218-1 (`:660-661`) already places "Другие курсы" outside the course list by that same row. The
round-17 table even says the sentence "cites the row that defines it": a definition quoted before its pointer.
Rule: When a reason points to a vocabulary row or rule, delete the words before the pointer that say what the row says;
if the reason is only "the row says so", the pointer alone (or nothing, when the defining place already cites it) stays.

### 2026-11-21: A moved reason duplicates FU21's revisit trigger, and "every row" is glossed by a narrower list (#218, judge_design round 18, consistency)
The round-18 move put "Revisit when the page grows long (FU21)" at the end of A218-6 (`ia.md:698`), while FU21
(`ia.md:1143`) already says "Revisit A218-6 (module rows in every block) when the dashboard grows long": one trigger
now stands twice inside `ia.md`, in two wordings, the first a condition quoted before its pointer. The A218-14 reason's
parenthesis "(the techniques, G185 and G125: [Multiple ways], item "catalog")" (`ia.md:735-736`) is the same shape:
it summarises that item before pointing to it. And `courses.md` "Requirements for #220" item 5 (`:184-185`) glosses
"in every row" of R6 "Course scope (#218)" with "(the dashboard rows: item 2; the lesson row ...; the catalog rows)",
which leaves out the not-found row (`ia.md:599`, item 6) and the top-bar row (`ia.md:592`, item 1).
Rule: When a reason moves next to its rule, delete from it every clause that another entry (an FU, a Multiple ways
item) already defines and keep only the pointer; a parenthesis that maps "every row" must name every row or say
"among them".

### 2026-11-21: The compaction dropped a pointer the replacement statement does not cover, and moved a pointer to the wrong clause (#218, judge_design round 19, consistency)
The r19 rewrite dropped the "Progress by release sentence" amendment (`plans/r19/after.md`, "Dropped"), so `ia.md:585`
"Every other F18 and F19 statement holds in every release from #30" stands with no pointer, although from #220 F18.1-F18.2
move into the course blocks and F18.3-F18.5 run across courses (A218-6, A218-13). The replacement statement
(`ia.md:604-607`) lists only "the F18.3 and F18.4 row names" for F18, and the `progress.md:49` pointer covers
progress.md, not this ia.md claim. Separately, `courses.md:33` puts "(FU23)" after "whose heading link still opens its
catalog": FU23 is about when the empty text shows (#147), and the clause itself restates the "course block" row.
Rule: Before dropping a pointer-only amendment, check the sentence against the replacement statement's list item by item;
if no item covers it, keep the pointer. A pointer goes right after the clause the target defines, never after a
neighbouring clause.
