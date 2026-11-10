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
