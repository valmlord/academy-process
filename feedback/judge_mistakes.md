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

### 2026-11-09: Accepted a focus fallback placement without checking the element that is "never removed" (#69, accessibility)
In judge_design round 3 the accessibility judge accepted design note §3.2 "`.check-row-panel`: its row button"
as the prototype fallback, and checked only the controls B8-B14 list as removed. The row button itself is
swapped markup in the prototype, so a focused row button falls to `main`. This surfaced only in judge_ux.
Rule: When a design says "X is never removed, so focus stays", check how the prototype draws X across
states. If it is per-state markup, require a fallback that covers X itself, and a test pair that focuses X.
