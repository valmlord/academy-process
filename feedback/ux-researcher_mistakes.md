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
