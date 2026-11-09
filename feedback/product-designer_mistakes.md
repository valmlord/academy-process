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
