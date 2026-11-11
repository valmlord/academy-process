# Judge Mistakes

Methodology lessons for reviewing. Seeded with review-discipline lessons; append new
project-specific ones as they are found.

### Rubber-stamp PASS without reading the code

Returned PASS without actually reading the changed files; a resource leak shipped.
Rule: Always read the actual changed files. Check resource management explicitly. If you cannot
read the code (it lives on a remote host or an un-checked-out branch), FAIL / CANNOT-CERTIFY -
never PASS on the description.

### Wrong attribution - blamed the coder for the architect's flaw

The architect designed something unworkable; the coder implemented it faithfully; the judge
blamed the coder for the resulting workaround.
Rule: When you find a FAIL, trace design vs implementation. If the coder followed the design
correctly, it is an ARCHITECT mistake, not a coder mistake.

### Missed a broken import / missing file

A new package imported a module that was never added; every judge PASSed; the program would
have crashed on startup with an import error.
Rule: Every review includes a basic "do all imports resolve to real files?" check.

### Accepted a self-referential guardrail as proof of safety

A change validated its output by re-deriving it with the SAME code that produced it, and the
comment claimed this made an outage "impossible". PASS on that trust would have been wrong.
Rule: Do not accept a guardrail's self-comparison as a correctness guarantee. Independently
enumerate everything downstream re-derives from the changed data and confirm each is handled or
provably not affected - from the real consuming code, not the author's comment.

### A decision rule safe at one corner, harmful at another

A rule was correct at the single state the reviewers happened to walk, but harmful at the
opposite end of another axis.
Rule: For any decision/threshold rule, walk BOTH ends of every state axis it depends on before
PASS. Name the corners you checked. A PASS that only exercised one corner is incomplete.

### An acceptance test that cannot fail on the old behavior tests nothing

A test named to guard a fix passed on both the fixed AND the broken version - it started from a
state where correct and incorrect behavior coincide.
Rule: For every test that claims to verify a constraint, ask "can this fail on the OLD/broken
behavior?" Require a negative run: a starting state where correct and incorrect behavior
DIVERGE, so the assertion distinguishes them.

### Green tests + clean compile ≠ the program runs

A module with a module-level use-before-definition compiled and passed all unit tests, but
could not start - the tests never imported the whole module.
Rule: When the tests do not import the module as a whole, do not treat passing tests as proof
it runs. Require at least one whole-module import/self-check. If none exists, FAIL on acceptance
completeness regardless of how many unit tests pass.

### Asserted a mechanism/symptom not verified in the actual source

A round-1 FAIL described the wrong failure mechanism (a call that "raises" actually failed
silently on a background thread), which sent the next fix chasing the wrong layer - and told
reviewers to watch for a symptom that could never appear.
Rule: Before asserting HOW something fails, read the actual call and confirm the failure mode
(synchronous vs silent/threaded). A wrong symptom is a wrong detector.

### 2026-10-27: A judge condition listed an incomplete value set (#15)

Round-2 accuracy condition 1 gave the L5 `instructionFiles` values as three
(`claude-md-or-agents-md`, `claude-md-and-agents-md`, `managed-only`); the memory page lists four
(also `claude-md`). The architect copied the condition verbatim, so the omission reached the design.
Rule: When a condition dictates an enumeration (values, scopes, versions), copy the full table
from the source and say "complete list" only after counting its rows.

### 2026-10-28: A judge's prescribed fix wording was itself inaccurate (#15)

Round-4 accuracy FAIL on L6 theory.md:70 prescribed "no prompts; only deny rules, ask rules and the
few actions no mode auto-approves stop a call". The lesson-author copied it. permission-modes says
those actions "get a prompt or a denial" even in bypassPermissions, and the permissions mode table
says bypass "Skips permission prompts, except for the actions no mode auto-approves". So "запросов
нет" was false, and the round-5 text was wrong because of the judge.
Rule: A fix wording in a FAIL is a factual claim too. Check it against the source sentence by
sentence before writing it, and quote the source's own verb (prompt or deny, block, skip).

### FAILed a hunk on an unverifiable direction-of-drift claim

FAILed an out-of-scope edit as "pushes a new value onto a shared surface" when it was actually
reconciling a stale mirror toward the already-live value - reverting it would have re-introduced
the drift.
Rule: An edit to a shared surface is only a "live change" if it differs from what is ALREADY
there. Establish the direction of drift first. If you cannot check, state the conditional
instead of issuing a FAIL whose severity hinges on the unknown.

### 2026-10-28: PASSed a design whose post-merge step was impossible on the real repo (#23)
The operations judge passed #23's design, including "Stepan adds pipeline-types to required
checks", without checking that the private free-plan repo supports branch protection (it does
not: 403). The flaw surfaced only in code review.
Rule: For every "Stepan does X after merge" step, run the read-only check of X against the real
repo/host during design review.

### 2026-10-29: Accessibility judge missed 2.5.7 on the pane split in rounds 1-2 (#50)
F9.3 "drag, or focus the handle and use arrow keys" was in the design from round 1; the accessibility
judge reviewed keyboard paths only and did not check WCAG 2.2's new pointer criteria, so the gap surfaced
in round 3 and cost a review round.
Rule: In judge_design, check every WCAG 2.2 addition (2.4.11, 2.5.7, 2.5.8, 3.2.6, 3.3.7, 3.3.8) against
every flow in round 1, not only the checklist's design items.

### 2026-10-29: Usability judge checked `?tab=` on arrival only (#50, judge_ux round 1)
Round 1 U3 asked the lesson to honour `?tab=` on arrival but did not check the other half of the same
control row ("`?tab=` updated" when a tab is selected), which F2.4 depends on. It surfaced in round 2.
Rule: When a finding concerns URL state, check every control row that reads or writes it, and click the
control to see the URL change, in the same round.

### 2026-10-29: Usability judge never ran simulated actions from a non-default tab (#50, judge_ux rounds 1-2)
Rounds 1-2 clicked "Проверить" and the status actions only from the default Теория state, so nobody saw
that every `data-goto-state` transition resets the left tab to Теория, against A17 and AC7. It surfaced in
round 3, once `?tab=` made the reset visible in the URL.
Rule: In judge_ux, run each state-changing control from every left-pane tab and compare the selected tab
and URL before and after against the acceptance notes.

### 2026-10-30: Pedagogy judge diffed task text against checks but not against the outcome verb (#42)
In round 1 the pedagogy judge confirmed that L4's "Готово, когда" matched its check one to one and stopped there. It
did not ask whether that text, together with the check's per-rule file and field messages, already handed over the
answers the outcome "Находит" expects the learner to produce. The problem surfaced in round 2 and cost a round.
Rule: After the 2.6 diff, read the task text and the check's message on the untouched starter as the learner sees
them. For every outcome verb (find, choose, place), state what is still left to do. If the answer is "nothing", FAIL in
round 1.

### 2026-10-30: A prescribed fix modelled the tool's regex but not its input (#41)

Round-1 assessment FAIL on the L2 import resolver prescribed "tokenize exactly as Claude Code does:
the regex, cut at `#`, `\ ` to space". The same `strings` dump showed the regex runs on marked `text`
tokens and on HTML comments after stripping. The designer applied the prescription faithfully, and
eight glued forms (`**x:**@path`, `<!-- c -->@path`, ...) still passed in round 2.
Rule: When prescribing "do what the tool does", read the whole function around the regex: what it is
applied to, which tokens are skipped, what transformations happen first. Prefer prescribing a superset
that is stricter by construction, and give a corpus to compare against, not only the cases found.

### 2026-10-30: Round-1 fix targets prescribed forms, and round 2 found the neighbours (#42)

Round-1 assessment B4 prescribed "no new top-level module or package under `src/`", and B3 prescribed a list of
banned calls. The architect implemented both faithfully. A sourceless `.pyc`, a stub inside an existing module, a
`sys.modules` alias and `runpy.run_path` then passed in round 2.
Rule: A blocking item's fix target names the effect to observe: no stand-in for the package, no code of that
package executed. A list of forms is at most an example. Before writing the fix, try two neighbouring forms against
it. This applies the #41 lesson ("prefer a superset stricter by construction") to every evasion finding, not only
to parsers.

### 2026-10-30: Accepted a residual bound counted in lines without bounding line length or exempt line types (#42)

Round-2 assessment prescribed "the residual paraphrase is bounded by 3 untagged lines plus 10 words per memory line".
s4 counts untagged lines but neither their length nor `#` headings. So in round 3 one untagged line or one heading
held a paraphrase of all ten moved rules, and the bound in 12.2 was not a bound.
Rule: A bound stated in units (lines, files, calls) is a bound only when each unit is also bounded in size and no
unit type is exempt. Before prescribing or accepting it, fill one unit with the whole forbidden payload and run it.

### 2026-10-30: Round-1 variant list for `make check` named only one rule (#42, judge_content round 2, assessment)

Round-1 assessment B1 stated the right effect ("a target that does not run both cannot pass") but its example variant
set planted only A1 violations. The designer implemented it with three column-0 A1 lines, and in round 2 a target with
the real suite plus a one-line `grep` for `^(import|from) invoices` passed. The B2 prescription ("run the pristine starter
tests") likewise did not say "and nothing else in that process", and a new test file monkeypatching a starter class
passed.
Rule: When a prescription includes example variants or a construction, write the cheapest stand-in that would satisfy
exactly those examples (grep for the planted line, monkeypatch from a sibling file) and run it against the prescription
before sending the FAIL. If it passes, the examples are not the fix.

### 2026-10-30: Accepted on paper that a message-forging grep would fail, without running it (#42, judge_content round 3, assessment)

Round-2 C2 said a `grep -n | sed` stub that copies the learner's message "fails (2)/(3) unless it grows into an AST
linter", and prescribed "plant A1, A2 and A3" without saying "every form". The designer planted one drawn form per rule.
In round 3 a 12-line grep forger passed 10% of runs. The prescription was the gap, and so was the untested claim.
Rule: Every "this stand-in would fail" in a FAIL is a test to run before sending it, not a judgement. When the
construction samples from a set, state whether the whole set or one draw is required, and compute the stub's pass
rate per run from the per-member results.

### 2026-10-30: A non-blocking note diagnosed only one of the files its sentence covered (#42, judge_content round 3, accuracy)

Round-3 accuracy note 3 said that "Правка, пропуск или удаление стартового теста ничего не меняют" was untrue only for
`tests/test_late_fee.py`. It did not check `verify_pokayoke.STATIC_TEST_FILES`, which also lists `test_statement`.
The designer narrowed the sentence to `test_statement.py` and `test_api.py`, which made it false for the very file the
note had missed. That cost round 4.
Rule: A note that says a sentence is wrong "only for X" is a claim about every other case. Before writing it, grep the
constant or stage that decides each case, even when the note is non-blocking.

### 2026-10-30: Security judge prescribed a per-file allowlist and missed sign-out revocation in round 1 (#29)

Round 1 F6 prescribed a file-level allowlist for the DAL guard, which exempts every later export of an
allowlisted actions module; round 1 also never checked that any test proves sign-out deletes the server
session. Both surfaced in round 2 and cost a review round.
Rule: When prescribing an allowlist, key it by the smallest unit the check can see; for every auth flow,
check in round 1 that a test asserts the server-side state, not only the browser's.

### 2026-10-30: Architecture judge listed shadcn drift by example, missing font size and state styles (#29)
Round 1 named control heights, the card and the dark input fill as the radix-nova drift, from default-state
screenshots. The input's `md:text-sm`, the unstyled `aria-disabled` busy button and the translucent hover fills were
in the same class strings and surfaced only in round 2, costing a round.
Rule: When a finding is "vendored component differs from the design system", read the whole class string against
the matching proto.css rules, every state included, and list every item in round 1.

### 2026-10-31: Round-1 citation grep listed forms by example, missing "design N.N" and review ids (#86, architecture)
Round-1 F1 grepped "design file", "design Dn", "design section n" and "research §n" and listed 33 hits. The same class
in "design 4.Q5", "(Arch A4)", "O N2", "decision A8" outside `design/flows/`, "round-n advisory" was 37 more lines;
the architect fixed the 33 and round 2 was spent on the rest.
Rule: For a "class of references" finding, grep the class with several neighbouring forms (section numbers, decision
ids, review finding ids) before sending round 1, and state that the list is an example and the effect is the target.

### 2026-11-11: Six design rounds checked the call line's flags but not that the call carries the contract (#43, assessment)
Design-review assessment rounds 1-6 for #43 attacked every C3-C10 flag rule and passed, but none asked whether
`role-call` fails when `call_role` never gives the role its contract. It surfaced only in judge_content, where
removing `--append-system-prompt-file` from the reference still passed both L2 command checks.
Rule: For every learner artifact an outcome names, run in round 1 the variant where the graded code ignores
that artifact entirely, and require that some check goes red.

### 2026-11-04: Round-1 accuracy prescribed "earlier stage name (case-insensitive)" for FROM without reading BuildKit (#44)
Round-1 A3 listed "earlier stage name (case-insensitive)" among the FROM forms. The architect copied it as F2 [J-acc].
BuildKit lowercases the declared name (`parseBuildStageName`: `stageName = strings.ToLower(args[2])`) but looks up the
FROM base with the raw string (`addState`: `dss.statesByName[ds.stage.BaseName]`); only `COPY --from` lowercases the
query (`findStateByName`). So `FROM Build` after `AS build` is not a stage reference, and as an image name it is
invalid (path components are `[a-z0-9]+`). The case-insensitive lookup belongs to COPY --from, not FROM.
Rule: Every value in a prescribed closed set is a claim. Before sending it, quote the vendor source or doc line for
each member, and check which code path (FROM vs COPY --from) the behaviour belongs to.

### 2026-11-04: A round-1 prescription said two rules "separate" a race, and they were tested only against the named forms (#44, judge_design round 2, assessment)

Round-1 S3 prescribed rule a and rule b and said they "separate" sleep-first and check-write-sleep from the honest
forms. That was tested against exactly those two attack forms. In round 2, an unlocked check, then the delay, then an
unlocked recheck and write passed every rev-2 rule 30/30, and so did a racy pending set. The architect had deleted
the residual on the strength of the prescription.
Rule: Before writing that a prescribed rule closes an attack class, run it against the class's neighbours: the race
moved before or after the delay, each lock removed from each honest form, a fast-path precheck added. Name the forms
you ran it against. "Separates X and Y" should read "separates X and Y; neighbours Z not tested".

### 2026-11-09: Accepted a focus fallback placement without checking the element that is "never removed" (#69, accessibility)
In judge_design round 3 the accessibility judge accepted design note §3.2 "`.check-row-panel`: its row button"
as the prototype fallback, and checked only the controls B8-B14 list as removed. The row button itself is
swapped markup in the prototype, so a focused row button falls to `main`. This surfaced only in judge_ux.
Rule: When a design says "X is never removed, so focus stays", check how the prototype draws X across
states. If it is per-state markup, require a fallback that covers X itself, and a test pair that focuses X.

### 2026-11-03: Round-1 note asked the README to claim "h3 on pages" from the element rule alone (#83, judge_design round 2, consistency)
Round-1 consistency note said the README `text-lg` row "should mention page-level h3" because `proto.css:114`
sets `h3 { font-size: var(--text-lg) }`. No page renders that: the only page h3 outside prose is "Чему научитесь",
which `proto.css:520` (`.outcomes > h3`) and the app (`module-section.tsx:33`) draw at `text-sm`. The researcher
wrote the note in and the check now asserts the false text. That cost round 3.
Rule: Before a note asks a README "Used for" cell to name a use, grep the element on every page and in the app
and confirm at least one instance computes to that step; an element default that every use overrides is no use.

### 2026-11-02: Named KELVIN SIGN as the case that needs NFKC without checking `toLowerCase` (#31, security)
Round-2 N1 direction named `Checks` and KELVIN SIGN as the unit cases of the folded check. The architect wrote a
mutation row "lower-case without NFKC -> KELVIN SIGN red". In JS `"K".toLowerCase()` is already `"k"`, so that
case stays green under the mutation; only fullwidth (and LONG S, U+017F) need NFKC. Caught in round 3, non-blocking.
Rule: When a direction names example inputs for each step of a transformation, run each input through each step
alone (a one-line `node -e`) before sending, so every named case really depends on the step it is meant to test.

### 2026-11-02: Prescribed a compose guard on the source file's syntax, checked against rendered output (#31, operations)
Round-2 A2 asked the isolated-recipe guard for "no `name:` on networks and volumes". The guard parses
`docker compose config --format json`, which renders `name:` on every network and volume, so the faithfully applied
wording can never pass. Found in round 3; it fails closed, but it would have stalled S39.
Rule: When prescribing a check on rendered config, run the render once and phrase the property on what it actually
prints (here: every name starts with the project prefix, none external), not on the source file's syntax.

### 2026-11-02: Prescribed the protected set as the academy stack, not "everything this run did not create" (#31, security)
Round-6 blocking 1 told the architect to define the owner set as the academy objects (by label, name, image) and to
forbid effects on it. The architect applied it faithfully, so in round 7 Stepan's other projects' containers (env
secrets) and the images his stack runs but does not build (`postgres:17.6-alpine`) were still open to a bare inspect,
exec or retag. That cost a round.
Rule: When prescribing a protected set for an agent on a shared host, start from the complement ("everything this run
did not create") and name the owner's known objects as detection subsets. Before sending, ask what else on the host
holds secrets or feeds the owner's stack.

### 2026-11-04: Usability judge checked the summary rule but not the design note's drawn examples (#72, judge_design round 2)
Round 2 checked A72-6 and A72-8 against #69 at the rule level and did not recount the §5.2 states. In those
states, "№ 3" ("1 из 2") is expanded into a three-item panel. Found in round 3.
Rule: When a review checks a counting or summary rule, also recount each example state the design note names
for the author phase, not only the rule text.

### 2026-11-04: Walked only some prototype samples against the icon and count rule (#72, judge_design round 2, consistency)
Round 2 checked the dashboard `attempts-mixed` rows against A72-8 but not the lesson samples of the same
design note. `history` gave "№ 3" "1 из 2" while `history-open` expands it to three items; it surfaced in
round 3.
Rule: When a rule maps summaries to items or icons, recount every sample state in the design note that names
both, on every page, not one table of them.

### 2026-11-04: Recounted the samples but never followed the prescribed links between them (#72, judge_design rounds 1-3, usability)
The design note's single dashboard-row href (`#state-history-deep-link`) was there from round 1. Three rounds
checked the deep-link table and the sample summaries but not which lesson state each dashboard sample row
opens, so the running and no-result rows landing on an expanded attempt surfaced only in round 4.
Rule: In judge_design, for every cross-page link the design note prescribes, walk each source sample to its
target state and check it against the arrival table row for that sample's case.

### 2026-11-10: Round-2 measurement of a name carried focus from the previous state (#72, judge_ux round 2, accessibility)
Round-2 `plain.mjs` loaded `#state-history-deep-link-plain` and then `#state-history` in the same page by hash, so
focus on `#attempt-2` carried over and the report (and then acceptance.md:797) said Chromium names the plain item
in `#state-history`. A fresh load of `#state-history` gives the unfocused `li` no name. Found in round 3.
Rule: Measure each state in a new browser context and print the `focused` property with every computed name.

### 2026-11-04: Prescribed `data-select-tab` on a goto control without tracing Back (#70, judge_design round 2, consistency)
Round 2 asked "Пройти квиз" to carry `data-select-tab="tab-quiz"` after tracing only the forward path through
`gotoState`. Once the tab changes after the push, the page script writes the new `?tab=` into the new history entry.
Back then changes the query too, Chromium fires `popstate` with no `hashchange`, and proto.js leaves the state
unchanged. Round 3 found this by running it, and the round-2 prescription was part of the defect.
Rule: Before prescribing a prototype attribute, run the control in a browser: forward, Back, reload. Check that
the URL query and the hash both round-trip, and that the listener the code relies on actually fires.

### 2026-11-04: Usability round 3 fixed the refusal notice but not the refusal in the panel (#70, judge_design round 4, usability)
Round 3 item 3 flagged that the refused-send notice claimed the answers were checked, and stopped at the notice.
The panel-shown end of the same refusal (`quiz.md` Error states) still renders F15.4's result block, "Верно C из
Q. Нужно K. Ответы остались выбранными.", for another tab's attempt. The usability judge also walked "focus in/out"
in rounds 2-3 without the pointer-only Safari case, where focus is `body`. Both surfaced in round 4.
Rule: A finding about what one surface says of an event names every surface that reports that event in the same
round; and every "focus in/out" walk includes a Safari mouse learner whose focus is `body`.

### 2026-11-04: Usability round 4 named the refusal's panel and notice but not the check bar (#70, judge_design round 5, usability)
Round 4 item 2 asked the refusal to say the same fact in the panel and the notice, right after the lesson "name every
surface". The check bar is a third surface of the quiz state ("Check bar after a quiz send", P7/P8), and a refusal that
finds the quiz passed or closed is in none of its rows. It surfaced in round 5.
Rule: Before sending a "surfaces of an event" finding, grep every table and rule keyed on that event's outcomes (here
`quiz.md` P6-P8 table, notice table, focus table) and list each one in the finding.

### 2026-11-04: Accessibility judge passed round 5 with the open user menu implicitly "in the panel" (#70, judge_design round 6)
Round 5's away rule ("panel hidden or focus in terminal/editor") already made the open top-bar user menu "not
away", and the accessibility judge passed it. The menu is a Radix modal menu (focus trap, `aria-hidden` on the
rest), so the focus move to the result block cannot happen and the outcome goes unannounced. Found in round 6.
Rule: For any rule that moves focus on a background event, walk every open overlay on the page (menus,
dialogs, popovers) and check in the app's component source whether it traps focus before passing.

### 2026-11-04: Accessibility judge passed the notice behind modal menus without reading `hideOthers` (#70, judge_design round 7)
Round 6 classified the "Действия" menu and the reset AlertDialog as away with the outcome announced by the quiz
notice, and the accessibility judge accepted it. Both modals call `aria-hidden` `hideOthers`, which spares only
`[aria-live]` nodes, and the notice container is `role="status"` only, so the announcement is lost while the
modal is open. Found in round 7, a round later than it could have been.
Rule: For every live region that must announce while a modal is open, read the modal library's hide routine and
confirm the container matches what it spares (attribute, not role) before passing.

### 2026-11-04: Usability judge walked "focus stays" without the controls the same answer removes (#70, judge_design round 8)
P8's removal of "К окружению" / "Переподключиться" and the row's "Пройти квиз" after a pass or close were in the design
from rounds 4-6. "Focus stays where the learner put it" when away (check bar and Проверки away with the panel hidden)
came in round 6. Rounds 6-7 walked the away places but never asked whether the answer removes the focused control,
so focus could fall to `body` and nobody saw it until round 8.
Rule: For every "focus stays" rule, cross every place it keeps focus with every control the same event removes
(grep the "goes", "removed" and "no action" sentences and #69's B-table), before passing.

### 2026-11-04: Accessibility judges passed the quiz notice markup without checking the app Alert's default role (#70, judge_design round 8)
The notice composition ("an Alert ... inside a `role="status"` container", `quiz.md:442`) stood through several
accessibility rounds. In rounds 7 and 8 the container's own attributes were checked, but not the role of the component
put inside it. The app's `Alert` defaults to `role="alert"` (`alert.tsx:36`), so a faithful build nests an assertive
region inside the polite one. Found in round 8.
Rule: When reviewing a live container, also read the default ARIA role of every app component the spec puts inside it,
and confirm the spec removes it or justifies keeping it.

### 2026-11-10: Consistency round 1 listed three shadcn departures and missed `outline-none` (#70, judge_ux round 2)
Round 1 FAILed the RadioGroup/Checkbox bullet for three departures but did not walk the full upstream class
string. The designer then wrote "changes exactly these classes, nothing else", and upstream's `outline-none`,
which would hide the app's base-layer focus ring, was still missing. Round 2 found it. That is the #29 lesson
again.
Rule: When a FAIL concerns departures from a vendored component, list every upstream class token as kept,
changed or removed in the FAIL itself, so the fix cannot claim to be complete without covering all of them.

### 2026-11-04: Prescribed a string-length check before `timingSafeEqual` over UTF-8 bytes (#32, security round 1)
Round-1 S-N1 prescribed "compare the expected MAC's base64url string (length check, timingSafeEqual over string bytes)".
The architect applied it word for word. String length is not byte length: a percent-decoded non-ASCII character keeps
the string length at 43 and makes the UTF-8 buffer 44 bytes, so `timingSafeEqual` throws `RangeError` on a pre-auth
path. Round 1 also did not check that the new upgrade listener catches errors and adds a socket `error` listener.
Both surfaced in round 2.
Rule: Before prescribing a crypto comparison, state the input's charset and its byte-length check, and name what
the primitive throws on. For every new pre-auth socket handler, check error containment in round 1.

### 2026-11-04: Prescribed a standalone smoke inside the clone, where Node resolves the workspace's node_modules (#32, judge_design round 2, operations)
Round-1 O-B1 prescribed copying the built server into `<clone>/apps/web/.next/standalone/apps/web/server` and importing
it there. From that path Node walks up into `<clone>/apps/web/node_modules`, so `yaml`, `drizzle-orm`, `better-auth`
and `@academy/db` all resolve; only `zod` (not a web dependency) failed. The architect applied it, and design 3.1 then
claimed "a new npm import turns it red". Copied out of the clone, every untraced package fails.
Rule: A layout smoke runs in a copy outside the repository tree. Before prescribing it, try two neighbouring imports
(a direct dependency of the package, a workspace package) and confirm both fail there.

### 2026-11-04: A planted-object proof that the old behaviour also passes (#32, judge_design round 2, operations)
Round-1 S-N8 asked to prove "preflight before the trap" with a planted academy-t32-labelled object surviving the
refusal. The teardown never removes a label-only volume (it removes MANAGED objects, `academy-t32_db-data` by name and
`:t32` images; `down` has no `-v`), so in a simulation the trap-first order also prints STOP, exits 1 and keeps the
volume. R-PREFLIGHT could not fail.
Rule: For a "survives" proof, plant an object the old code path would actually remove (read its removal list first)
and also assert the old path's own output (here no TEARDOWN or RESULT line) is absent. Simulate both orders first.

### 2026-11-04: Three architecture rounds accepted `term.reset()` without reading xterm's own doc of it (#32, judge_design round 4, architecture)
"The client resets the terminal and writes the snapshot" was in the design from round 1. Rounds 1-3 walked the state
rows but never opened xterm 6.0.0's `reset()`, whose doc says it keeps queued input and the parser state
(`CoreBrowserTerminal.ts:1260-1267`). The source was in the scratch clone's `node_modules` all along. It surfaced only
in round 4, once the A3-B1 test made a queued write at the switch explicit.
Rule: For every library call a state row depends on (reset, dispose, close, pause), read its doc comment and body in
the installed version during round 1, and say what it does to queued work.

### 2026-11-04: Round-1 prescription for the "never counted" floor dropped #15's safety condition (#68, judge_design round 2, security)
Round-1 architecture finding 1 prescribed the ADR-0001 floor as a bare list ("format errors, stage-0 rejections,
platform `error` results") and the round-1 security review did not check it against #15 §2.5.6, which exempts a
format error only when the run is "rejected ... before any key comparison" (bug-hunt: "not scored"). The architect
applied the list faithfully, so the contract now makes any result an implementer labels "format error" a free,
uncounted probe of an enumeration-capped check. Found in round 2.
Rule: When a prescription moves an exemption from a security design into a contract, copy the condition that makes
the exemption safe (here: the uncounted result shows nothing derived from grader material), not only its name.

### 2026-11-04: Round-1 rollout prescription named a form (03/04 ready flips), not the effect (#68, operations)
Round-1 operations asked for "(a) any 03/04 lesson ready on main before #68 merges: rebase and migrate; (b) any
content PR flipping a lesson to ready rebases". The architect applied it faithfully, so round 2 found the
neighbours: main moving outside course/ (fixtures, schema), and content PRs that add a quiz to an already ready
lesson. It cost a round.
Rule: When the finding is "CI does not re-run when main moves", prescribe the effect for both sides (no PR that
touches the lesson contract or lesson YAML merges unless its head contains current main and CI ran on that head),
with the `merge-base --is-ancestor` test as the check; ready flips are one example.

### 2026-11-04: Round-2 note "run U1 on parse failure too" did not mention the raw input lacks zod defaults (#68, architecture)
Round-2 architecture note 1 offered "have U1 look the member up by the raw `kind` so it runs on parse failure too",
and security asked U1 to fail closed. Neither note said that raw YAML has not had `checks: ...default([])` applied.
The architect combined both and made a valid ready lesson without `checks:` a U1 issue. Found in round 3.
Rule: When suggesting that a check run on pre-parse data, name the parser defaults and optionals it will no longer
get and say how the check treats each.

### 2026-11-10: Round 1 compared layout rules with proto.css but never checked their cascade layer (#106, judge_design round 2, architecture)
Round 1 walked the `.lesson-layout` block against proto.css rule by rule and passed `.lesson-layout > .resizable-handle
{ display:none }`. That rule sits in `@layer components`, while the handle's class string (2.7) has the `flex`
utility, and Tailwind 4's `utilities` layer beats `components`. Round 1 also passed E-hint ("accessible description
still matches") without running the Kbd markup through Playwright's accname. Both surfaced in round 2 and cost a round.
Rule: For hand-written CSS in a Tailwind 4 app, read the layer of every rule and the full class list of each element
it targets in round 1. For every e2e assertion the design keeps, read the matcher's algorithm in the installed tool.

### 2026-11-10: Round-1 gate prescriptions were not run on a loaded host before sending (#106, judge_design round 2, operations)
Round-1 operations prescribed the per-commit loop as one `&&` chain ending in `|| echo "commit $c red"`, and the
flaky rule as "re-run alone, must be green alone". Round 1 had already seen that test go red in the full suite.
Neither prescription was run at base. In round 2 at base the chain stopped at the test step, so the build never
ran. The file alone was red twice and passed only with `--testTimeout=60000`.
Rule: Before prescribing a gate command, run it at base under the host's current load and check that each step it
lists actually ran (look for the step's output artefact). A known-flaky test's rerun rule must give green at base.

### 2026-11-10: Round-2 frame finding described `flex` as sizing the height, without checking the container's axis (#106, judge_design round 3, architecture)
Round-2 architecture blocker 1 said the frame's `flex-1` beats `flex:none` and that "with `flex-basis: 0%` the main size
comes from flex, not from `height`". The frame's container (TabsContent `flex flex-1`) is a row, so `flex` sets the
frame's width and `height` sets its cross size. The architect built revision 4's `flex:none` below 30rem on that
framing, which makes the frame as wide as xterm's own screen and lets FitAddon shrink the terminal on every refit. Found
in round 3.
Rule: Before stating what a flex declaration does to an element, read the parent's full class list for `flex-col` and
name the main axis in the finding.

### 2026-11-10: Round-3 operations prescribed a one-test flaky check from four logs, without repeated base runs (#106, judge_design round 4, operations)
Round-3 operations issue 2 gave command F, which accepts a red root test only when the lesson-markdown timeout is the
single failure. It was checked on four logs, two of them at base. In round 4, two of three fresh base runs had other
5 s timeouts (`starter-walk`, `sign-in-form`) as well, so command F said `not-met` and 8b stops the tester at base.
The architect applied the prescription word for word; it cost a round.
Rule: Before prescribing a flaky-test rule, run the full suite at base at least three times under current load and
list every test that timed out; prescribe for the class of failure seen, not for the one test seen first.

### 2026-11-09: Round-1 construction for blocker 1 contradicted blocker 2 of the same report (#101, judge_design round 2, security)
Round-1 security blocker 1 offered "the sweep and the deadline mark as `error` only the included checks that have no
committed result", while blocker 2 of the same report said a missing result after the grader started is counted. The
architect applied both; the deadline then labels a started check whose runner failed as an uncounted platform stop.
Found in round 2.
Rule: When one report carries two prescriptions over the same rows, run each prescribed construction against the other
finding's fix target before sending.

### 2026-11-09: Prescribed a per-commit code rollback without checking how PRs land on main (#101, operations)
Round-1 operations finding 3 prescribed "revert commits 4-9, keep commit 3". The architect copied it into 5.6. Main
is squash-merged (`git log --first-parent` has one commit per PR and no merge commits), so after the merge those
commits are not in main's history; the only revert available on main is the whole squash commit, which deletes 0002
and fails `check-append-only.sh`. Found in round 2, non-blocking because the append-only guard fails closed.
Rule: Before prescribing a rollback or any step that names commits of a PR, run `git log --first-parent` on main
and phrase the step for the merge method the repo actually uses (here: revert the squash commit, then restore
`packages/db` from it, as one PR).

### 2026-11-10: Counted a header line as a record in a read-only rehearsal (#113, judge_design round 1, operations)
Round 1 reported `docker buildx du --filter 'type!=exec.cachemount'` as "223 records selected"; the file had 223
lines including the `ID RECLAIMABLE SIZE LAST ACCESSED` header. The real count is 222 (194 regular + 27
source.local + 1 frontend, which the same report listed), 223 without the filter. The architect copied 223 into 2.4,
R-1 and R-U1, so the design's evidence does not add up.
Rule: Count records by a per-record key (`grep -c '^ID:'` on `--verbose`), never `wc -l` on a table, and check that
the parts sum to the total before reporting it.

### 2026-11-10: Judged the deploy store mount by the pnpm counter, not by the metric of the issue (#113, judge_code round 1, operations)
Round 1 passed 5c6880c and wrote that the workspace deploy step "is the same with and without the store mount",
because deploy printed `downloaded 0` and the image check exited 0. That counter reads the same in both variants,
so it could not show a difference. The issue is about build-cache growth, and the deploy record in
`docker buildx du --verbose` is about 117 MB with the mount and about 280 MB without it (architecture judge, then the
tester's M1/M2). The mount had to be restored in 1ac739d.
Rule: When a change is judged "no effect", measure it with the metric the issue is about (here the new build-cache
record of the step, matched by before/after ID diff), not with a proxy that prints the same value in both variants.

### 2026-11-10: Suggested fix wording carried an unchecked absolute (#72 merge, judge_design round 2, consistency)
The round-2 consistency report proposed ""run" in these docs is only the row above" as example wording for
`ia.md:32`; the fix adopted it, and round 3 found other senses of "run" in `design/flows/` (`progress.md:92`,
`:358`, `dashboard.md:47`, `auth.md:44`). The judge had grepped only the attempt vocabulary, not the word itself.
Rule: Grep every word a suggested fix makes a claim about before proposing the wording.

### 2026-11-10: Design round passed a prescribed "the only way" header comment without a counter-example grep (#121, judge_design, architecture)
Design 1.1 dictated the log-fields.ts header "these four functions are the only way a field taken from a thrown value
reaches a log line"; all three design judges passed it. http/errors.ts:96, reconcile.ts:109 and main.ts:30 log fields
of our own error classes directly, so the coder shipped a false comment and judge_code had to FAIL it.
Rule: In judge_design, treat every comment text a design dictates as code: for an exclusivity claim, grep the
counter-examples before PASS.
