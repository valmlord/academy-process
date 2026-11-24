# product-designer mistakes

Seeded with design-discipline rules; append real lessons as they are found. Load before working.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seeded: A CDN script or web font in a prototype

A prototype that loads a script, stylesheet or font from the network breaks when opened offline by
double-click and pulls third-party code into a local file.
Rule: No absolute or protocol-relative URL anywhere in `design/` except an `<a href>` value; the
validator must exit 0.

### Seeded: A hex colour in a prototype bypassing tokens

A raw colour in a prototype drifts from the token file and from the app, and its contrast is never
computed.
Rule: Colours only as `var(--name)` with a name declared in `tokens.css` or `proto.css`.

### Seeded: A flow step with no `data-step` element

A step the prototype does not mark cannot be walked through by the usability judge or checked against the
flow.
Rule: Every flow step id of the page has exactly one element with `data-step="<id>"`.

### 2026-10-29: Cross-page links of the lesson prototype dropped the flow's state (#50)
The lesson prototype's "Войти снова" linked to `../sign-in/prototype.html` (no `next`, no `#state-with-next`),
"Выйти" to sign-in without `#state-signed-out`, the module crumb to `catalog#introduction` (the catalog's id is
`module-introduction`), and the page ignored `?tab=` although the dashboard's "Продолжить" and sign-in's `next`
both send `?tab=task`. So F2 ("Session expires during a lesson") ended on the dashboard instead of F2.4, F3.3
never showed "Вы вышли", F4.3 "Продолжить" opened Теория, and the crumb landed on the page top. The dashboard
and catalog had these links right; the lesson acceptance did not state the destinations at all.
Rule: Walk every flow across pages in a browser: click each cross-page link and confirm the target page opens
in the state the next step names (tab, `#state-`, anchor); state every control's destination in the
acceptance Interactions section, not only on another page's notes.

### 2026-10-29: An accessible name outside the copy register, and a second name for the same tablist (#50)
The lesson prototype names the left-pane tab list `aria-label="Разделы урока"` and the lesson acceptance Copy
table lists it as plain copy, but the string is in no `ia.md` set or page-copy row and is not among the names
Stepan exempted ("Навигация", "Область", flagged as Open questions). The gallery names the same tab list
"Урок". Dev copies the accessible name from the acceptance notes, so an unregistered string ships and the
gallery and the page disagree.
Rule: Run every Cyrillic text node and attribute value of the prototype through the `ia.md` register before
handing over; a string that is not there is either taken from the register or listed under Open questions as
"not yet in the register", and the gallery uses the same name.

### 2026-10-29: Acceptance notes gave two anchor schemes for the catalog module section (#50)
Dashboard acceptance says the module row links to `#module-<id>` (Interactions) and `/courses/<id>#<moduleId>`
(AC6); catalog acceptance says `#module-<id>` (Prototype) and `#<moduleId>` (Interactions, AC); the lesson
crumb uses `#introduction`, which matches no id on the catalog prototype. Dev implementing the dashboard
from its Interactions line would link to an id the catalog never renders.
Rule: An id or route that two pages share is written once, in the route form the IA fixes (`#[moduleId]`),
on every page that links to it; prototype-only ids are labelled as such and never appear as the app value.

### 2026-10-29: "Check bar never obscures focus" verified only at the extremes (#50, judge_ux round 1)
Lesson acceptance (Accessibility notes, 2.4.11; AC13) states the check bar "never overlays a pane", verified at
320x200. At 375x667 and 320x500 with "Окружение" shown, the environment pane's content paints over the check
bar and covers a focused "Проверить" in several states (session expired, API key, idle warning, after a run
with the environment stopped). Dev would ship the claim as an acceptance fact.
Rule: A "verified" layout claim names the sizes checked and includes at least one common phone height
(375x667) and one height just above each height breakpoint, with every pane shown.

### 2026-10-29: Lesson tabs never write `?tab=`, so F2.4 restores a stale tab (#50, judge_ux round 2)
The design's "Controls and their v1 destinations" says the left-pane tabs go to "that tab panel; `?tab=`
updated", and "Войти снова" sends `next=<current path with ?tab=>`. Lesson acceptance documents only the
arrival half (Route, AC4); Interactions and keyboard say nothing about writing the query, and the prototype
leaves `?tab=task` in the URL after the learner selects Теория or Проверки (clicked). Dev building shadcn
Tabs from the notes keeps the tab in component state, so a learner who came from "Продолжить", moved to
Проверки and then lost the session is returned to Задание, and a reload loses the tab.
Rule: For every row of the controls table, copy its full destination into Interactions and an AC, both the
read side and the write side of any URL state, and click the control in the prototype to see the URL change.

### 2026-10-29: A page rule overrode a promoted system component (#50, judge_ux round 3)
After `.outcomes` moved to `proto.css` ("set in text-sm", "pages define neither"), the catalog kept
`.module-section h3 { font-size: var(--text-base) }`. Same specificity as `.outcomes > :is(h2, h3, h4)` and
later in the cascade, so the catalog "Чему научитесь" renders 16px while the lesson and the gallery render
14px (measured live). Dev copying the ready catalog prototype ships a different heading size than the
README contract.
Rule: When a component moves into the system, grep every page `<style>` for selectors that still reach its
elements and measure the computed style on each page, not only that the old class rules are gone.

### 2026-10-29: Simulated actions reset the left-pane tab and rewrite `?tab=theory` (#50, judge_ux round 3)
Every `data-goto-state` transition re-applies `data-select-in-states`, so a state with no tab of its own
selects Теория. Measured headless at 1280 and 375 px: on Проверки or Задание, "Проверить" lands on
`#state-check-running` with Теория selected and the URL rewritten to `?tab=theory`; "Продолжить работу",
"Открыть новый сеанс", "Переподключиться" and "Запустить снова" do the same. That contradicts A17 ("no tab
switch"), AC7 ("A run does not switch the tab") and the new AC17, on the core path F13.1 -> F13.3, and the
`?tab=` writer then publishes the wrong tab ("Войти снова" carries theory).
Rule: After adding URL or selection state, run every simulated action from each tab and assert the tab and
the URL are unchanged unless the acceptance notes say the action switches them.

### 2026-11-09: A focused row button falls to `main` on a background change (#69, judge_ux round 1)
`data-focus-fallback` was put on the check bar and on every `.check-row-panel`, but not on anything that
contains the row button itself. The prototype draws each state's rows as separate markup, so a background
change hides the focused `.check-row-trigger` and the focus repair finds no ancestor fallback and focuses
`main`. Measured headless at 1280 and 375 px in 9 transitions each (for example `#state-results-limit-known`
-> `setState("check-running")`): focus lands on `main#main`. `checks.md` says the row buttons are never removed,
so in B8-B14 focus stays on that row's button. The 26 background pairs focused "Подробности", "Проверить",
"К окружению", "Переподключиться", "Открыть результаты" and "Отмена", never a row button, which is the
element most likely to have focus in Проверки. So the run could not catch this.
Rule: In a prototype that swaps markup per state, every element that "is never removed" in the flows needs
a fallback to its own counterpart in the next state (here `data-focus-fallback` on each row `li`). The
background focus pairs include focus on each kind of element that a background change can hide, not only
the controls the flows list as removed.

### 2026-11-03: Not-found Route reversed the "course id unknown" implication (#83, judge_ux round 1)
`design/pages/not-found/acceptance.md:13-14` says that while the course cannot be read only way (1) reaches
the page "and then the course id is unknown (`#state-no-course`)". The judged design (D2) and `ia.md` R6 say
the converse: the id is unknown only when `course.yaml` itself is unreadable; when it parsed and a later file
failed, the id is known and "Курс" stays. A dev following the note would hide "Курс" and "Открыть курс" on
not-found for every course read failure, so the top bar would differ between pages in the same request,
against R6. The check passed because it asserts only the quoted members, not the sentences around them.
Rule: When a note restates a condition from `ia.md`, copy its direction and its trigger ("`course.yaml`
unreadable"), and read every sentence of the note against the rule, not only the asserted phrases.

### 2026-11-03: Course-error `<title>` stated three ways across the catalog prototype and two notes (#83, judge_ux round 1, accessibility)
`design/pages/catalog/acceptance.md` Route (:6-7) and AC8 now say the catalog's `<title>` is "Не удалось
загрузить курс" while the course cannot be read, but `catalog/prototype.html#state-course-error` renders
`<title>` "ИИ для разработчиков" (measured at 320/375/1280, both themes) and the note gives no caveat, though it
gives one for the top bar and the retry in the same rows. `lesson/acceptance.md:159` then lists `<title>` "Не
удалось загрузить курс" as one of the "three things only" in which the lesson course error differs from the
catalog, which contradicts the catalog's own Route. A dev or tester checking 2.4.2 gets two answers.
Rule: When a note states a per-state `<title>` the static prototype cannot render, say so in that row, and
when another page's note lists differences from it, compare against that page's note, not its prototype.

### 2026-11-10: An app-test AC rewritten without its release scope (#72 judge_ux round 2)
AC44 in `lesson/acceptance.md:1014-1022` was rewritten from "run the design script" into app-test behaviour,
but it tells "the dev tester of #35" to assert it "in every #72 state of the States table". Nine of those states
(seven rows, `:319-325`) are tagged "(from #37)" or "(from #39)", the cost and budget states, so a #35 tester cannot pass the
AC, and the AC's own tag "(#72)" names the design issue, not a release, unlike AC30-AC43 next to it.
Rule: When an AC is rewritten to bind the app, give it a release tag like its neighbours and scope every
state list it names by release ("each state from the release its row is tagged with").

### 2026-11-10: Wrote a measured name for the plain item in a state where it has none (#72, judge_ux round 3, accessibility)
Lesson acceptance.md:795-797 says Chromium computes the plain item's name from contents "in
`#state-history-deep-link-plain` and `#state-history`", and AC31 (:953-954) asks `#state-history` for "seven
names, each the accessible name of its disclosure button". On a fresh load of `#state-history` the `li` is not
focused and Chromium gives it no name (name "", no source); it computes "№ 2. 4 ноября, 13:50. ..." only while
the item has focus. "№ 2" has no button either. A #35 tester asserting AC31 by accessible names gets six.
Rule: Before writing a measured name into acceptance notes, load each named state fresh (new context, no
carried focus) and record whether the element was focused; scope the claim to that condition.

### 2026-11-10: Restated an inherited accessible name as exact for new states without measuring it (#72, judge_ux round 4, accessibility)
Lesson acceptance.md:293, a line #72 added, defines "Check bar of №8's run" with tab name "Проверки, идёт
проверка". #72 also added its 14 running states to #69's `.sr-only` span (prototype.html:224), and in all 14
(both themes, fresh loads) Chromium computes "Проверки , идёт проверка": the span is a flex child of the tab, a
known #69 defect. The round-4 name sweep checked the plain item but not the tab name the same paragraph states.
Rule: Every quoted accessible name in a line you add is measured in the states it describes, including names
copied from another issue's state; if the prototype differs for a known upstream reason, refer to that state
instead of quoting the name, or say so next to it.

### 2026-11-10: Quiz states carried the v1 empty text and a first-attempt send state into later attempts (#70, judge_ux round 1, usability)
Three gaps of one kind: a v1 or first-attempt element reused in quiz states where its facts are false.
(1) `lesson/prototype.html:1192` shows "Попыток пока нет. Нажмите "Проверить", когда будете готовы." in
quiz-failed, -last-attempt, -closed, -row-closed, -limit-unknown, -answered-away, -notice-two-pane and -refused,
right under the quiz row's "Неудачных попыток: N из 3". `checks.md:522-524` ties that text to "every check as
"Не запускалась"", which no longer holds once the quiz row shows a sent attempt. In F15.6 (`#state-quiz-row-closed`)
the learner reads "Закрыта: не пройдено, Неудачных попыток: 3 из 3" and then "Попыток пока нет".
(2) `#quiz-send` (`:1464`) always goes to the one `quiz-sending` state, whose header is "Попытка 1 из 3"
(`:1208`) and whose quiz row is "Ответы не отправлялись, 0 из 3" (`:1007`). So a send from quiz-failed,
-last-attempt or -refused drops the attempt line and the "Осталась 1 попытка" warning. This is not in
"Prototype limitations", and quiz-run.js asserts H1 for every send, so the regression counts as expected.
(3) The refusal that finds the quiz passed or closed (`quiz.md:640-644`, AC43) is neither drawn nor listed as
not drawn. Its composition (refusal title, then "Квиз пройден" or the close line, icon) is left to dev.
AC56 also names only limitation 1 as an exception, though limitations 2-3 are Back and Forward cases its own sweep runs.
Rule: For every element shared across quiz states, check its facts against each state's attempt number and quiz
row, and do the same for every state a control leads to. Each quiz.md state is drawn or listed in "Prototype
limitations", and every limitation the headless AC runs into is named as an exception in that AC.

### 2026-11-24: New states joined a shared link but not the limit that names its states (#222, judge_ux round 1, usability)
#222 added nine two-course states with a readable block 1 to the dashboard (`courses-one-broken`,
`courses-block-error-fails-again`, `courses-broken-no-title`, the three `courses-progress-lost-*` retries,
`courses-other-broke-at-retry`, `courses-block-renamed`, `courses-block-removed`). Their six block-1 module rows
share the markup that links `../catalog/prototype.html#<moduleId>`, which opens catalog `default`: one course, no
"Другие курсы". `dashboard/acceptance.md` says every link opens a state with the same courses "except" L1-L8, but
L4 names "every two-course state" as four (`courses-two`, `courses-one-empty`, `courses-all-passed`,
`attempts-two-courses`), and L5 covers only the block heading links of the #222 states. So the limit list
claims an invariant the drawing breaks, and the A218-14 section is missing from the target with no word about it.
Rule: When new states are added to an element's `data-state`, grep every limit and "every"/"each" list that names
the states of that element, and add the new states to it (or write the list as a rule, "every two-course state
with a readable block 1"), in the same change.

### 2026-11-24: State renamed without its old pointers, and from-#220 sentences left unscoped (#222, judge_ux round 1, consistency)
To reuse `course-error`, `course-error-fails-again` and `progress-unavailable` for the new #220 one-course error
states, the dashboard's kept states were renamed `*-until-220`. Two pointers to the old ids were missed: dashboard
AC31 (an until-#220 AC) still names `progress-unavailable`, now the #220 state, and `ia.md:562` (R6 "Course id
unknown", the until-#220 "Курс" rule) still points to dashboard `#state-course-error`, which now draws the #220
block error with no "Курс". The catalog kept `course-error` as its until-#220 state, so one id now means opposite
releases on two pages. The sweep (`plans/222-author-sweep.md`) also marked catalog `:22-24` ("#220 states: ... the h1
is the course name") and AC13 ("h1 and `<title>` are the URL's course name") as untouched, though
`courses-course-error` and `root-error` are #220 states whose h1 is "Не удалось загрузить курс". AC77, the sample
"course 2 broken" and the R2 press-focus bullet copy the trigger of ES4, ES1 and R2 into the note.
Rule: Before renaming a state id, grep the old id in `design/` (flows included) and either keep it or update every
hit; for each new state, re-read every "from #220" or "#220 states" sentence of the page notes against it; an AC
points to a rule's trigger by id, never by quoting the trigger cell.

### 2026-11-24: Scripted id swap rewrote a kept-state pointer inside an HTML comment (#222, judge_ux round 2, consistency)
Restoring the #233 ids was a two-step scripted rename (`*-until-220` back to the kept ids, the old #220 ids to
`one-course-*`). The comment above the until-#220 Alert in `dashboard/prototype.html:138` named the kept
`#state-course-error-fails-again-until-220`; the swap turned it into `#state-one-course-error-fails-again`, the #220
block-error state, which does not show that Alert (its `data-state` is `course-error course-error-fails-again`). The
sweep repaired five kept-state lines of the notes by hand, but read only attributes in the prototypes, not comments.
Rule: After a scripted rename, list every hit of the new and old ids in prototype comments and prose too, and read
each against the element it describes; an id in a comment is a pointer like any href.
