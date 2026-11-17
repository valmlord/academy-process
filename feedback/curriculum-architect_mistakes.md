# curriculum-architect mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### 2026-10-27: Outcome verb that the check cannot observe; quiz testing volatile trivia (#15)

O1 said "выбирает ... и обосновывает выбор", but its only check was a quiz, which cannot observe a
justification. Three of its eight quiz topics (default effort per surface, budget_tokens on 5.x,
vendor effort names) were recall of facts on the stale watchlist, against the design's own rule
"every question is a scenario requiring the mechanism".
Rule: For every verb in an outcome, name the check that observes it; drop the verb or add an
artifact. Never grade recall of a dated default; grade the habit (name the surface, check it).

### 2026-10-27: Lesson uses concepts the sequence introduces later (#15)

L2 (cost) had prerequisite L1 only, yet its theory and quiz rely on "every turn resends the
context" (the agent loop, L3), subagent fan-out, MCP vs CLI (L3) and CLAUDE.md -> skills (L5,
module 01). The L3-before-L4 swap was justified by exactly this dependency, but not applied to L2.
Rule: For each lesson, list the concepts its theory, task and quiz use, and confirm each is
introduced in an earlier lesson or inside the lesson itself; apply a dependency argument to every
lesson it touches, not only to the one being swapped.

### 2026-10-27: Bug-hunt key format that an honest learner can fail (#15)

bugs.yaml allowed one line range per bug, but the planted "lost instruction" mistake has a cause
(rule said only in chat), a trigger (auto-compaction) and a symptom (migration edited) far apart in
the transcript, so a correct finding can miss the range. Three categories (context-bloat,
handoff-bloat, eager-loading) overlapped with no stated criterion separating them, while matching
requires the exact category.
Rule: When defining a matching format, walk every planted bug: one unambiguous anchor rule or
several accepted ranges, and categories that are mutually exclusive by a stated criterion.

### 2026-10-27: Anti-gaming claims not checked against the cheapest attack (#15)

The #15 design called its checks "not gameable" without computing the best attacker strategy:
bug-hunt with 6 bugs, 4 decoys (2 categories decoy-free) and maxReports 8 is passed
deterministically by reporting both sides of every look-alike pair (2 + 3 pairs = 5 = minFound);
every python command check exits 0 when the learner plants `~/.local/.../usercustomize.py` with
`atexit -> os._exit(0)` (verified), because run strings lacked `python3 -I`; the L6 hook allow/block
probes never include a path that contains "generated" but resolves elsewhere, so a raw-substring or
block-all-but-api.py hook passes; the quiz demo required "1000 random trials all below passScore"
while its own math gives 0.1-0.8% per trial (expected 1-8 passes); quiz explanations shown after a
failed submission reveal the key for attempt two; plan-structure validated paths against the
learner-editable workspace.
Rule: For every check, write down the cheapest attacker strategy (hedging, environment tampering,
over-blocking, retry-with-feedback) and its pass probability before calling it not gameable; every
probe set has both "must block/deny" and near-miss "must allow" cases; every check script runs with
`python3 -I` and takes expected values only from `checks/`.

### 2026-10-27: L6 check expectations contradicted documented Claude Code behaviour (#15)

The #15 design fixed L6 probe outcomes and hook semantics before the research addendum existed,
and several contradict code.claude.com/docs/en/permissions and /hooks: `Bash(git status)` and
`git diff` "allow" ignores that read-only git runs without a prompt in every mode with no rule;
"WebFetch ask" is undefined when no rule matches, since the built-in starting mode in an
interactive terminal is `auto` (v2.1.283+), not a prompt; "malformed stdin -> blocking exit"
did not say exit 2, while CC treats exit 1, crashes and timeouts as non-blocking (fail open)
unless `onFailure: "block"` (v2.1.295+); the generated-file protection relied on the hook alone
though the docs say to use permission rules for hard denies; wrong-solution `Bash(git *)` has no
probe that catches it (`git -C . push`, `git -c core.fsmonitor=...` are documented bypasses).
Rule: A check that emulates a vendor mechanism states, per probe, the documented outcome
including the no-rule/default-mode fallthrough and exact exit codes, and is written only after
the research for that mechanism exists; mark expectations "pending addendum" otherwise.

### 2026-10-27: anti-gaming fixes that reopened the hole they closed (#15, design round 2)

Revision 1 of the #15 design fixed round-1 gaming findings but introduced or missed new ones:
the quiz and bug-hunt show the answer key after 3 failed attempts and never say what happens to
attempt 4, so failing three times on purpose and copying the key passes with certainty; the
bug-hunt "cheapest attack 0.93%" counts each bug as one episode, but lost-instruction and
no-verification accept two anchor ranges each, so a per-category guesser sees 2 accepted blocks
out of 4 and passes at 14/768 = 1.82%, above the design's own 1% bar (the demo would assert the
wrong analytic number and "pass"); L1 routing claims retry enumeration is "bounded by the attempt
cap in 2.5.6" while 2.5.6 defines no cap for command checks; demo 2.4(4) applies the PATH-shim
cheat to the reference solution, where it cannot fail; the hook check feeds a Read payload that
a hook registered `Edit|Write` never receives, failing an honest hook.
Rule: When a fix adds a reveal, a cap or a multi-anchor key, recompute the attack against the
new rule itself: say what the learner can do after the reveal, count every accepted range as a
separate guessable episode, and cite only caps that the design actually defines. Every cheat
probe states the base copy (starter vs reference) on which it must fail.

### 2026-10-27: Hook registration pattern rejects the documented preferred form (#15, design round 3)

Revision 2 tightened the L6 hook registration check to one shell-form regex over `command` and
ignored `args`. code.claude.com/docs/en/hooks says "Prefer exec form for any hook that references
a path placeholder", and its own project-script examples are
`"command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/x.sh", "args": []` (unquoted placeholder, exec
form), or `"command": "node", "args": ["${CLAUDE_PROJECT_DIR}/..."]`. Both fail the regex, so a
learner who copies the vendor's example fails. The reverse also holds: with `args` present the
docs-quoted shell spelling `"\"$CLAUDE_PROJECT_DIR\"/..."` is spawned literally (exec form has no
shell, quotes and bare `$VAR` pass through verbatim), the hook cannot start and fails open, yet the
regex accepts it. The regex also accepts relative `./.claude/...` and bare `.claude/...` forms
although the docs say "Use absolute paths" for hook scripts.
Rule: When a check pins how a vendor config must be written, enumerate every documented form
(here shell vs exec form, decided by the presence of `args`) and verify each accepted string
actually runs under that form; never accept or reject a form by text alone.

### 2026-10-27: A pedagogy add-on silently reopened the attempt-cap arithmetic (#15, design round 4)

Revision 3 added a mentor between failed attempts ("question and direction only, never anchors,
options, field values or the key") but did not forbid the mentor from saying WHICH question, card or
report item is wrong. The quiz and L1 caps were certified on score-only / aggregate-count feedback;
per-item correctness lifts a 6-question quiz from 0.36% to 19.9% within 3 attempts and L1 routing
(12 combos per card) from about 0.2% to 8.3% within 10 submissions.
Rule: Every new feedback channel (mentor, UI hint, log line) is checked against the feedback rule
the rates were computed under. State what it may NOT reveal in terms of that rule (per-item
correctness, counts), and say whether it receives the key at all.

### 2026-10-27: A registration allowlist that pins command/args but not the other fields (#15, design round 4)

Revision 3 pinned the L6 hook `command`/`args` exactly but left the other documented fields open:
`"if": "<rule that never matches>"` (e.g. a typo `Edit(src/invoice/generated/**)`), a tiny `timeout`,
or `"disableAllHooks": true` in the same settings file all pass registration while the hook never
blocks in Claude Code (fail open). The "after trimming" step with Python `str.strip()` also removes
NBSP/VT, so ` "$CLAUDE_PROJECT_DIR"/...` matches yet `sh` exits 127 (verified).
Rule: When a check claims "exactly one accepted form", allowlist every key of the object (and the
settings keys that switch the mechanism off), give allowed values for each, and trim only the
characters the consuming shell also ignores.

### 2026-10-29: Fixed commands and named formats not run against the real layout and template (#41, design round 1)

Revision 1 of #41 pinned `python3 -m unittest discover -s tests -t .` while the module 00 starter has no
`tests/__init__.py` and keeps the package under `src/`. CPython's `discover()` then raises "Start directory is not
importable", so every run would error, and the "wrong directory prints No such file or directory" trap was false.
The design also claimed to accept "the MADR 4.0.0 shape" with `## Consequences`, but the template has
`### Consequences` under `## Decision Outcome` and a quoted, optional status. Its skill chain rule banned a reference
file citing `scripts/`, which PBP shows as correct. And it narrowed S's "packaging or upload fails" (claude.ai,
Skills API, package_skill.py) to "a hard error outside Claude Code", although R 2.3 says Cursor reads
`disable-model-invocation`.
Rule: Every command a check or hook runs is run once on the starter layout before the design pins it, and its
output is quoted. A design that names an external format ("MADR 4.0.0 shape") copies its headings from the template
file, levels included. A vendor restriction keeps the surface list the source gives.

### 2026-10-29: Outcome verbs the starter makes impossible; size ignoring measured evidence; task and check out of step (#41, design round 1)

O5 said the learner "проводит фичу по конвейеру интервью, спецификация, задачи, TDD" and "принимает
результат по скрытым тестам", but the L5 starter shipped the finished spec and tasks, no lesson had
the learner run an interview, and hidden tests are run by the grader, not the learner. L5 put a
five-task TDD loop and a 450-500-line, 21-decoy bug-hunt into 90 min although module 00 had already
measured a smaller bug-hunt at a 70-min lesson; the split was deferred to the student run. L2 task
asked for `verify` body rules no check reads, while L2-L4 checks enforced numeric limits (CLAUDE.md
<= 20 lines, <= 12 terms, 6-12 REQ, 3-8 tasks) the task text was not required to state.
Rule: For each outcome verb, confirm the lesson's starter leaves that step to the learner and that
the learner, not the grader, performs it; size each lesson from the measured time of the closest
past exercise; require task.md to list every constraint its checks enforce and nothing they do not.

### 2026-10-29: Anti-gaming claims that ignored the check's own feedback channel and free-form fields (#41, design round 1, assessment)

Revision 1 called 2.6 mutation grading "pass probability 0 without a behavioural test" because equivalents
defeat source pinning, but the failure message names every test that fails on a correct variant, so two
submissions learn the equivalents' source hashes and a hash-pinning test passes (reproduced in a toy grader).
Traceability let one test name carry every `req_NN`, so one catch-all test satisfied every label. The 2.3 YAML
subset accepted `description: Use when: x`, which YAML rejects, so CC would load the `release` skill with no fields.
The CLAUDE.md check ignored `@` imports and `.claude/rules/`, which module 00 L5 already resolves. Grader C6 read
the editable workspace glossary.
Rule: For every check, list what its failure messages reveal and run the attacker that learns from them across
uncapped submissions; bound every free-form field a rule matches on (label counts, scalar forms); reuse the
resolver an earlier module already built for the same surface; read every expected value, glossary included,
from pristine `checks/data/`.

### 2026-10-29: A sizing rule applied to the lesson the judge named, not to every lesson (#41, design round 2)

Revision 2 sized the new L6 bug-hunt from 00 L4's measured budget, as round 1 required, and its self-review
claimed the rule applied. L1 was left at 65 min / 40 hands-on although its closest shipped analogue, 00 L6 (one
PreToolUse path hook plus settings), took 80 min / 50 hands-on, and L1 asks for more: mutant-killing tests, a
code fix and a Stop hook that runs and parses unittest under 13 probes, after the densest theory of the module,
which revision 2 made longer.
Rule: When a judge's rule fixes one lesson, apply it to every lesson and show the work: for each lesson name its
closest shipped analogue with that analogue's minutes, and give per-part minutes wherever the lesson asks for
more than the analogue did.

### 2026-10-29: An isolation claim tested from one side of the boundary only (#41, design round 2, assessment)

Revision 2 moved mutation variants behind an out-of-process seam and claimed no structural fingerprint was
observable, citing a toy run of the round-1 attack, which only inspected the test process's own proxy module. The
same toy, attacked from outside the proxy, passed with zero behavioural assertions in two ways. The server's argv
named the variant copy, and the leftover `__pycache__` bytecode was a stable fingerprint. A `/tmp` counter keyed by
the grader pid read the fixed variant order. Out-of-domain `TypeError` messages named each variant's operator. The
same revision ran acceptance tests in-process with the learner's module, so a forged record or a patched
`assertEqual` passed a `return 0` implementation.
Rule: For every isolation boundary, attack it from the untrusted side through every channel a same-uid process
has: argv/`ps`, files next to anything imported (bytecode caches), shared writable dirs across runs, run order,
error text on out-of-domain input, and the record fd. Never run grader assertions in a process that imports
learner code. Shuffle run and probe order per run, and state the residual guess probability.

### 2026-10-29: An indistinguishability rule stated in words, then broken by its own generator (#41, design round 3, assessment)

Revision 3 required that red and green Stop-hook probe projects "differ only in values that are visible only
after evaluating `sha256` expressions". It also rested a 1/46656 non-running guess rate on a prototype harness.
That harness wrote the red/green flag as a literal offset (`+ 1` on red, `+ 0` on green). A 15-line hook that
grepped for it, with no test run and no hashing, passed the shuffled probes 5/5. The planned guard, "diff red and
green of one seed", would read `+ 1` vs `+ 0` as a computed value and pass it.
Rule: When a check depends on two generated states being indistinguishable without doing the skill, specify the
generator, not only the property. Use one template and fresh random values. Pick the state only by rejection
sampling, and write no flag literal. Then attack the generated files statically: grep, diff with random names
masked, and compare literal distributions over many seeds. Do this before citing any rate measured on it.

### 2026-10-29: An irreversible attempt cap whose counted/uncounted boundary no check defines (#41, design round 4, pedagogy)

Revision 5 capped five checks at 10 failed submissions (never reset, nothing reopens). It said only failures
that "reached the hidden runs" count, so "honest iteration on the static parts is free". The task.md cap
items then promised specific free failures. But only L7 `change-request-applied` defined a static stage that
runs first. L1 task.md called "item 1 import rules" free, yet the L1 check enforced imports only through the
proxy inside the variant runs, and it read skips and the test count from the run record. So the untouched
starter's skipped test was a counted failure. L5's check listed (A), (B), (C) with no order, so a `todo`
task or a bad test name might burn an irreversible attempt. L7's cap item understated its own free stage.
Rule: When a cap separates counted from uncounted failures, give every capped check an explicit stage 0: the
static rules it runs before any counted run, listed in the check entry. Copy exactly that list into task.md.
Put every rule that can be checked statically into stage 0, and have the demo show that a stage 0 failure
leaves the counter unchanged.

### 2026-10-29: Diversity of syntax counted as diversity of secret (#41, design round 4, accuracy)

Revision 5 drew Stop-hook probes from K = 4 "structurally different" templates. It claimed that an evaluator
written for one template "is left with a guess" on the others, and that copying 1-2 templates gives 1.07% or
18.3% within the cap. All four templates compute the same `h(seed)`. All four put `j` in plain digits in the
fixture file name, and the seed as a 16-hex literal in the files. So one template-agnostic hook ("hash every
hex literal, compare with the `f<j>.json` number") decides every template after one copy. The S-rates were
also labelled "exact, best strategy". In fact they were the non-causal bound: they assumed the hook sees a
class's three probes before deciding the first.
Rule: Before citing a rate for a variant-diversity defence, write the cheapest attacker that ignores the
variation. Look at what the variants share: the decision function, the plain-text carriers of the secret, and
the file layout. Only syntax that is actually different counts. Label every attack rate with its information
model (sequential or all-at-once).

### 2026-10-29: Rejection sampling whose cost depends on the secret leaks it through time (#41, design round 4, assessment)

Revision 5 chose the probe state only by rejection-sampling seeds. A green probe needs about 10^4 draws per seed;
a red one about 1. The prototype created P's directories before the draw and wrote the files after it, so
`mtime(tests/__init__.py) - mtime(src)` was under 0.3 ms on red and 5-100 ms on green. A 20-line hook that only
calls `os.stat` (no test run, no hash, no template knowledge, no memory) passed 20/20 on macOS. Drawing first moved
the cost into the gap between probes, which a hook with a hard-coded `/tmp` timestamp still read (7/10). The
text-only generator guard could not see either channel.
Rule: When a secret is chosen by sampling, make the sampler's work independent of the secret: sample every
outcome every time and select afterwards. Draw everything before creating any file the attacker can stat.
Guard the generator on the artefact as it lands on disk (timestamps, inode order, wall and CPU time between
probes), not only on the text it renders.

### 2026-10-29: A changelog claimed a withdrawn design was removed everywhere; one lesson entry kept it (#41, design round 5, accuracy)

Revision 6 replaced the four probe templates with one (Stepan's K = 1). Section 18 said they were "removed
from 2.8, L1, L7, section 6 and 11.13". L7 `stop-hook-integrity` still said "The test-state P of every probe
come from the 4-template 2.8 generator (revision 5)". The practice-designer implements from that entry.
Rule: When a decision withdraws a design element, grep the whole design for every name and number of the old
element (`4-template`, `K = 4`, `T1`-`T4`, its rates). Fix every hit outside a labelled historical record
before writing "removed from X" in the changelog. List the grep and its remaining hits in the changelog.

### 2026-10-29: A stage-0 list paraphrased into task.md instead of copied (#41, design round 5, pedagogy)

Revision 6 gave each capped check a stage 0 and copied it into task.md. Four of the five copies were exact.
For L7 `change-request-applied`, task.md summarised "all of (C)" as "the L5 consistency and vocabulary rules"
(C1-C3, C6). But (C) runs grader C1-C6, so C4 and C5 were missing. The list also added "the new task has
`Status: done`", which no rule in (C) checks. Its "what counts" list named only the dispute test, although (B)
re-runs all 14 mutants and the 6 correct runs over the learner's edited tests.
Rule: When a check entry says "all of (X)", expand (X) rule by rule in task.md, and do not swap in a summary
borrowed from another lesson. Then diff both ways: every rule in the check appears in the text, and every rule
in the text appears in the check. The "counted" list names every hidden-run rule, including regression on
what the starter already passed.

### 2026-10-30: An "ordered rule, first yes wins" key never walked literally, behind binary feedback (#42, design round 1, pedagogy)

Revision 1 of #42 L1 claimed that the placement ladder (2.7) "leaves one answer" per card and graded 12 cards with
binary "не пройдено" (tolerance 1, mentor barred from per-item hints). Read literally, step 2 ("can the agent learn
it by reading the repo: code, config ...") already says yes for R04 (the signature `late_fee(amount_cents,
days_late)` states the order), R08 and R10 (the hooks are in `.claude/settings.json`) and R12 (dead code imported
by nothing). The ladder never said whether a rule an existing hook enforces is `hook` or `delete`. R07 and R08
pointed at `legacy_format.py`, `money.py` and `make codegen`, which the L1 starter did not ship. An honest
learner applying the printed rule could be 4-5 cards off with no feedback channel.
Rule: For every ordered decision rule used as a key, add a per-item table that shows the answer of each step in
order, with each "no" justified from a file the starter actually ships. Walk it as a literal reader would. Any card
where an earlier step is a defensible yes gets reworded or its key widened. Every file or command a card names
must exist in that lesson's starter.

### 2026-10-30: Task text promised a self-run that the check replaced with its own implementation (#42, design round 1, pedagogy)

L2 "Готово, когда" said "your linter finds nothing in your workspace". The check runs the grader's `arch_rules.py`
on `src/`. L3 said "the allowlist stays empty", but the check reads the pristine allowlist and never the
workspace's.
Rule: When a check substitutes its own implementation or pristine data for the learner's, task.md says so in those
words (as 01 L7 item 4 does). It never states a condition on a file the check does not read.

### 2026-10-30: A closed-set config check graded from the research summary, not from the vendor pages (#42, design round 1, accuracy)

L4 `contour-config` revision 1 did not hold against the docs in five places:
- It failed `CLAUDE_CODE_DISABLE_WEB_FETCH=true`. The env-vars page parses on/off variables as `1|true|yes|on`
  in any case.
- It attributed "any non-empty value" to that variable. That wording comes from a different variable's row.
- It rejected documented deny forms (tool-name globs) and called `WebFetch(domain:*)` semantics "not in R". The
  permissions page documents them.
- It graded only project `allowedDomains`, which pre-allows hosts and does not deny the others, while O4 claimed
  "only internal hosts".
- The fiction (CA not in the OS store, HTTPS mirror) needed `SSL_CERT_FILE` for uv. The closed key list
  rejected it, so the reference contour could not reach its own mirror.

Rule: For every graded key or env var, open its vendor row and copy the parsing rule, every documented
alias and form, and the scope limits into the alternatives column. Then walk the reference config end to
end: every tool the brief names must reach every host it needs under the graded settings alone.

### 2026-10-30: Checks graded the form of a fix, not the fix, and binary meant "not enumerable" (#42, design round 1, assessment)

Five paths passed revision 1 without the skill:
- L1 `poka-yoke-applied` graded callers only by named-argument form and a learner-editable suite. Swapped named
  arguments in `statement.py` passed, either with one test expectation edited or with a `unittest/` shadow package.
- L1 `rule-placement` graded "removed from memory" by `[Rnn]` tags. Stripping the tags and keeping every rule's
  text passed.
- L2 `arch-workspace-clean` reused import-statement rules on the workspace. `importlib.import_module` and
  `__import__` hid A1 and A2.
- L3 `deps-gate` took first-party names from the workspace. Vendoring a stub `src/fastjsonx.py` passed; that stub
  is incident I02 itself.
- L1's binary, uncapped 12-card key lets a learner sure of 9 of 12 pass within 14 submissions.

Rule:
- For every outcome verb, name the wrong state the check must reject and probe behaviour, not form: every caller,
  not only the callee.
- Take every "is it ours" set (first-party names, memory files, test bodies) from `checks/data/`, never from the
  workspace.
- When the workspace check reuses the learner's rules, list the ways around those rules (dynamic import, another
  memory file) and close them on the workspace side.
- Binary feedback is enumerable on a fixed small-domain key. Compute the partial-knowledge search (sure of n-2,
  n-3) and cap the check unless that figure is acceptable.

### 2026-10-30: "Task text equals the checks" applied by printing the answer key (#42, design round 2, pedagogy)

L4 was reshaped to "find and repair seven planted defects", but task.md printed the grader's "Gone when / Accepted
forms" columns. Those columns name the key, the file and the trap for every defect, for example `SSL_CERT_FILE` in
`launcher.env` and `strictAllowlist` in user settings. The uncapped check also reported each failing rule with its file
and field. One run on the starter listed all seven defects, so the outcome verb "Находит" had no practice left, and the
"find 7 defects" time line was fiction.
Rule: 2.6 requires that no checked rule is hidden. It does not require printing the grader's spec. When the outcome is
to find something, state each rule as the requirement it protects, in the brief's terms. Give the general acceptance
rule once ("any documented form with this effect"). Make check messages name the requirement, not the file, the key or
the value. Keep the per-item table for the grader and the mentor. Before finalising, ask of every lesson: "after reading
task.md and running the check once on the starter, what is left for the learner to find?"

### 2026-10-30: Round-1 evasions closed by listing forms, not by observing the effect (#42, design round 2, assessment)

Revision 2 closed each round-1 attack with a rule against the form that was shown, and three neighbouring forms passed.
- L1: the `@` import regex required whitespace before `@`, so `**Rules:**@docs/rules.md` and `<!-- c -->@...` passed.
  Tagged lines were unbounded, and s5 matched raw characters. All ten moved rules passed when written with
  zero-width spaces or homoglyphs, or as one paraphrased `[R03]` line.
- L2: w2 checked `sys.modules`, so `runpy.run_path(".../invoices/money.py")` passed. So did `exec` of the file text.
- L3: "no new `.py`" let three stubs pass: a sourceless `.pyc`, a `fastjsonx` class in an existing module, and a
  `sys.modules` alias.

Rule:
- Write the check against the effect the outcome names: code from that package executed, a stand-in for the invented
  package exists, the rule text is loaded.
- Prefer a superset that is stricter by construction, and reuse a closure the course already demonstrated. Module 01
  L2's `IMPORT_TOKEN` was available.
- Before claiming a residual bound (12.2 "s4 bounds it"), try to exceed it with the cheapest form.

### 2026-10-30: A name ban checked `ast.Name` only; the import alias of the same builtin passed (#42, design round 3, assessment)

Revision 3 closed "plain `exec`" with "no name `exec`" in L2 w1. `from builtins import exec as run_source` binds the
builtin under another name, so every call site passes a Name-only check. w2 does not see it either: no module is
registered. It is still the in-scope "plain exec with a literal name".
Rule: When a check bans a callable by name, ban every way to bind that name without strings. That covers import
aliases (`from builtins import x as y`), the attribute form and the module that provides it. Prefer banning the
provider (`import builtins`, the name `__builtins__`), which honest code never needs. Before claiming the closure,
run the alias neighbour of every listed must-fail.

### 2026-10-30: A runtime probe keyed on a module name, and a tamper snapshot that never ran honest suites (#42, design round 4, assessment)

Revision 4 w2 asked "is a module named `invoices...` loaded". `sys.path.insert(0, ".../invoices")` followed by a plain
`from money import format_cents` loads the same file under the name `money` and passes (a), w1 and w2. That is plain
Python with a literal name, so it is in scope. In 2.3, "tampered = any `vars()` of a unittest module or class changed"
was demonstrated only on `mock.patch`, `MagicMock` and `IsolatedAsyncioTestCase`. `assertLogs`, `mock_open`, a file left
open in a test (the ResourceWarning `__warningregistry__`) and a test returning a value are all green suites, and all of
them are reported as tampered.
Rule:
- A runtime probe identifies code by where it comes from (`__file__` under the forbidden directory), never by the name
  it was imported under.
- A tamper detector compares what an attacker must change (callables and descriptors, by identity), not data the
  library fills lazily.
- Before shipping either, run an honest corpus against it, not only the attack corpus: the common idioms of the API
  under test (for unittest: `assertLogs`, `mock_open`, `subTest`, class and module fixtures, async tests, warnings,
  unclosed resources).

### 2026-11-03: A "find" verb served by a starter that a fresh rewrite bypasses; an attribution verb with no decoy that needs it (#43, design round 1, pedagogy)

O1 said "Находит, какой файл определения загружается". The design mapped it to the config check ("the starter hides the
active file") and to a quiz. The check's must-pass corpus accepted deleting every reviewer file and writing one fresh
file, which passes without any load-rule knowledge. None of the quiz topics covered load or skip rules. O6 said "определяет по
`parent_tool_use_id`", but the only role-breach look-alike was an allowed tool, so "flag every write tool" matched
without building the tree.
Rule:
- A "find" verb is observed only if the honest shortest route still requires finding it. Walk the must-pass corpus for a
  "replace everything" route. If one passes, observe the finding on a fresh case: a quiz scenario on an unseen layout.
- An attribution verb needs a decoy that is identical except for the attribute: the same tool, called by an agent allowed
  to call it.

### 2026-11-03: Flag-semantics corpora that rejected documented forms or gave false reasons (#43, design round 1, accuracy)

Five places in the round-1 design did not hold against the vendor pages:
- L1 rejected `model: claude-sonnet-5-5[1m]` "as undocumented". The frontmatter takes "the same values as the `--model`
  flag", and model-config documents `[1m]` on IDs.
- L2 C7 failed `--permission-mode auto` without giving a reason, yet auto "auto-approves file edits in your working
  directory". It also required `Write` beside `Edit`, though "`Edit` rules apply to all built-in tools that edit files".
- C6 gave "project `permissions.allow` is not used" as the reason a settings-based restriction fails. Deny rules are not
  trust-gated.
- The role-call scenarios had 3 of the 4 documented error subtypes. `error_max_structured_output_retries`, the one tied to
  the schema requirement, was missing.
- L5 called MAST Insight 3 the peer-reviewed anchor for per-joint gates. It had dropped "low-level" from "sole reliance on
  final-stage, low-level checks is inadequate".

Rule:
- For every must-fail form, cite the vendor sentence that shows it lacks the effect, or label it "course rule" in the
  design and the message.
- For every enumeration the check samples (subtypes, modes, values), copy the full list from the type definition and
  count it.
- Paraphrase a paper's finding only with all its qualifiers.

### 2026-11-03: Grading infrastructure specified by intent, not by the mechanics an honest run hits (#43, design round 1, assessment)

The design specified the fake `claude` as "a grader thread" over a socket. A single serving thread serialises three
honest parallel calls, so the fan-out overlap rule fails the reference: the prototype gave a 6.0 s span instead of
2.0 s. The pipeline was to run as `python3 -I`, which breaks the sibling import the starter itself sets up.
`total_cost_usd` was "equal to the sum", which is float equality, and 344 of 1000 reorderings differ. G3 said
"spaces" while the snapshots carry tabs. Roles were identified by schema equality while honest L4 schemas can be
identical. A must-pass `--agent` line could not satisfy C3 under random model draws. The quiz shape "1-2 select-all"
included a value that misses the design's own 2% bar (3.63%).
Rule:
- For every grading mechanism (server, launcher, comparison), write the one sentence that decides concurrency,
  `sys.path` and equality: per-connection serving, the exact launch line, and tolerance or exact arithmetic.
- Run the honest corpus through that sentence on paper, line by line, before sending the design.
- Every honest-corpus line must be checked against every other requirement in the same check, not only the one it
  was written for.
- When a parameter is a range, compute the bar for each end of the range.

### 2026-11-03: New decoys broke a planted item; flags rejected by course rules that the task never states (#43, design round 2, pedagogy)

Round 2 added two decoys to force attribution: the tests reviewer running `python3 -m unittest discover` twice, and a
failing run that the tests reviewer reports. The planted UP1 still said "the tests reviewer reports all tests pass; the
only test run is in the coder's subtree", which those decoys make false, so the rule-5 walk keys UP1 as "no". The 4.3
flag table also rejects about fifteen flags as "course rule" (`--debug*`, `--include-*`, `--session-id`, `--name`,
`--betas`, `--input-format stream-json`, `--permission-prompts host`, `--append-subagent-system-prompt*`, `--worktree`,
the coder's `--restricted`/`--safe-mode`). None is in the printed course-rule list, and C6/C7 name effects ("add tools,
approvals, settings, agents, plugins or directories") that these flags do not have.
Rule:
- After adding a decoy, re-walk every planted item that shares its agent, tool or category, and rewrite any "the only X"
  sentence the decoy touches.
- Every flag a check rejects must follow from a printed requirement or a printed course rule. A failure message whose
  requirement text does not cover the flag misinforms; give the course rule its own id or line.

### 2026-11-03: Course-rule reasons written as "the docs don't" without searching the docs (#43, design round 2, accuracy)

Round-2 fixes added course rules whose stated reasons were false on the vendor pages:
- "Repeated and `--flag=value` forms are not documented for `claude`". The CLI reference shows `--debug='mcp,startup'`
  and `--tmux=classic`, and "Repeat the flag" for `--plugin-dir`/`--plugin-url`.
- "These three have a quoted MCP effect", used to exclude other closures. The `--safe-mode` row says "MCP servers ... do
  not load".
- "The subset is the keywords that both draft-07 and the API accept ... inside both lists". The API requires
  `additionalProperties: false` on objects, lists only 10 `format` values, and never mentions `title` or `$schema`.

Two new items were also keyed on behaviour that is unsettled or contradicted:
- A new L1 quiz option, "edit a notebook" under `disallowedTools: Write, Edit`, which the docs leave unsettled.
- The L6 README run line has no approval for the `python3 -m unittest` calls that the trace shows running.

Rule:
- A course-rule reason that says "only X" or "not documented" is a claim about every row of the source. Grep the whole
  page (`=`, "Repeat", the effect word such as "MCP") before writing it.
- A reason that says "both lists" must be checked against each list's required items, not only its forbidden items.
- Every new quiz option and every new trace context line gets a quoted vendor sentence that decides it. If none
  decides it, replace the option.

### 2026-11-03: Round-2 fixes covered the listed forms, and their neighbours failed (#43, design round 2, assessment)

Four round-2 fixes held for the forms the round-1 report named. A neighbouring form of each failed when run:
- The flag allowlist names `--allowedTools`/`--disallowedTools` only. The documented `--allowed-tools`/`--disallowed-tools`
  spellings and a prompt after `--` fail honest call lines.
- References count only inside `<copy>` and the run dir, and H7 diffs only `<copy>`. So a coder narrative stashed in
  `$TMPDIR`, `$HOME` or `/tmp` and referenced by path reaches the reviewer unseen.
- A reference to the project root expands the whole copy, `.git` included, past the 4000-file cap: a platform error
  on an honest line.
- "Exactly `splitlines()`" is false for an empty file (1 line vs 0), and an honest `splitlines()` gate then returns
  G2 where only G3 is broken.
Rule:
- For every flag a rule names, copy every spelling its CLI row lists, and decide `--`.
- A "where to look" scope (directories, files) is checked against every place the learner's process can write. Close
  the scope by effect: read wherever a reference points, and diff every writable tree.
- A claim that two models agree ("exactly X") gets a run over the degenerate inputs: empty, single separator, no
  final separator.

### 2026-11-03: A new rule's reason overclaimed its effect; a new fake sentence generalised vendor behaviour (#43, design round 3, accuracy)

Revision 3 fixed the five round-2 accuracy blockers. It also added two sentences that are false on the vendor pages:
- The C10 reason "так строка вызова целиком описывает права и вывод роли", repeated in RS20 as "a call line that fully
  describes the role". The module's own L2 theory teaches the opposite: under `-p` the project's hooks, `env` and deny
  rules apply to every call (permissions trust table), and user settings apply too. So the line does not describe the
  role's rights "целиком".
- 4.3 "A documented flag outside the list gets the normal response, because the real CLI accepts it". Headless says
  "Claude Code rejects `--bg`, and rejects `--cloud` with a task description, with an error naming the conflict", and
  `--bg`/`--background` are on the must-fail list.
Rule:
- A course rule's reason states what the rule guarantees by construction ("every flag on the line is one the lesson
  explains"), not a wider effect ("fully describes"). Before writing "fully", "entirely" or "every", check the reason
  against the module's own theory of what else acts on the same object.
- A sentence about "the real CLI" covering a whole class of flags is a claim about every row in that class. Check it
  against the headless "Not every CLI option combines with `-p`" list before writing it, or describe only the fake.

### 2026-11-03: Reference and H7 scope closed by a list of places, not by the effect (#43, design round 3, assessment)

Revision 3 closed the round-2 reference blockers for the forms named, and three neighbours broke:
- Honest prose naming `/tmp` (or `../` with a flat copy layout) expands an ancestor of the run dir, because `<scratch>`
  sits under `/tmp` as in 02 `grader_runtime.py`. A run dir that keeps raw outputs then leaks the coder's narrative into
  the reviewer's material, and leftover `make try-fake` dirs push the read past the 4000-file cap.
- "A directory inside `<copy>` is never expanded, because H7 sees every project change", while H7 excludes every
  `.git`. A stash dir under `<copy>/.git`, referenced as a directory, passes both.
- H7 fails on any new uid-owned path under `/tmp` or the home. The learner's own Claude Code session in the same
  container creates such paths, so honest runs fail at random.
- The new full quiz key keyed cascade Q1 (c) on an output format the scenario never states.
Rule:
- When a rule leaves something unobserved ("not expanded", "excluded"), state the invariant that makes it safe, and
  check every exclusion of the other rule against it.
- Run every place-list in a scope ("expanded inside /tmp, /var/tmp, ...") against honest prose that names each place,
  against the place the grader itself uses, and against concurrent processes of the same uid.
- Prefer a property only this run can produce (files changed since run start, values drawn for this run) to a list of
  directories or names.
- A select-all option whose truth depends on a run parameter (output format, mode, foreground) names that parameter in
  the scenario.

### 2026-11-03: Stated a "the grader reads all three" invariant without attacking the reader that implements it (#43, design round 4, assessment)

Revision 4 wrote "every in-scope path from the pipeline's output to a role goes through the prompt text, a named file,
or the run dir, and the grader reads all three". Two neighbours falsified it:
- The reference tokeniser splits on whitespace and on `, ; : = ( ) [ ] { }` and quotes. So `"<run>/coder out.json"`,
  `<run>/coder(1).json` and `"/tmp/my stash.json"`, each named whole, are never read.
- The directory rule tests only the realpath. So the run-dir entry `<run>/linkdir -> /tmp/stash`, named directly, is
  not expanded, although the same entry is followed when the reviewer is given `<run>/`.
Rule:
- When a design states an invariant ("the grader reads X"), attack its implementation with inputs built from the
  implementation's own edge: names that hold the tokeniser's delimiters, and paths that are inside by name but outside
  by realpath (or the reverse).
- When one form of a must-fail line is caught through a parent ("given `<run>/`"), also run the same object named
  directly.

### 2026-11-03: Bounded a path span by the old tokeniser's own delimiter set and by tokens, then claimed `@` was outside it (#43, judge_design round 5, assessment)
Revision 5 started a span only at a word whose first character is `/`, `.` or `~`, with words cut on the 4.6
delimiter set, and ended it only at a whitespace token end, minus a trailing run of that same set. So any character
outside the set next to a path hides it: `@<run>/a b.json` (unquoted; `@` is not a delimiter, so the word starts
with `@`), `«<run>/coder.json»`, `“/tmp/my stash.json”`, `**<run>/coder out.json**`, `Read <run>/coder.json!`, and
the compact JSON `{"ctx":"<run>/coder out.json","diff":"..."}`. The design text said "any `@` ... before it is already
outside it" without running it. The `.`-strip variants also turn `<run>/..` into `<run>/`, which contradicts the RS21
sentence beside them. A run-dir entry reached through an in-scope alias (`/tmp/r/linkdir/`) passes both L and R.
Rule:
- A span rule for "a path written whole" is checked against what can sit right before and right after a path in real
  prompts: unquoted `@`, Russian and curly quotes, markdown emphasis, `!`/`?`, and a compact JSON continuation.
- Each new trimming variant is run on the out-of-scope and `..` lines too, not only on the must-fail lines.
- When two in-scope aliases are added (an outside link to the run dir, a run-dir link to outside), run their
  composition.

### 2026-11-11: The L2 call requirements never said the call delivers the role's contract (#43, judge_content round 1, assessment)
Design 4.3 lists C3-C10 for every role call (model and cap from roles.json, schema in `--json-schema`, tools,
MCP closure, approvals, call format, flags) but no requirement that the call carries the role's contract
`pipeline/contracts/<role>.md`. task.md step 3 follows the design and also omits it. So a `call_role` without
`--append-system-prompt-file` (or any other way of giving the role its contract) passes `role-call` and
`role-contracts`, while the theory ("the role knows only what came in the prompt and the system prompt"), the
rubric K4 ("it sees the prompt and this contract only") and L3 task.md ("the starter `claude_call` already passes
the contract as a file") all assume the contract reaches the role. A learner who follows step 3 literally hits it
without trying to cheat.
Rule: For each artifact a lesson asks the learner to write, name the requirement and the check that show the
artifact is used by the code under test, not only that it exists and is well formed. Walk the outcome's nouns
(contract, schema, config) and for each ask "which check fails if the code never reads it?".

### 2026-11-03: Capstone sequence contradicted its own slicing rubric; an honest suite lacked the inputs it needed (#44, design round 1, pedagogy)

Revision 1 of #44 said each lesson's "Готово, когда" is one slice of the L1 reference plan, and the L1 rubric
demanded that every slice be vertical. Yet the lessons run layer by layer: the whole contract (L2), the engine (L3),
the API (L4-L5), the UI (L6), CI (L7). That is the horizontal plan that 01 L4's rubric fails. The design also never
said how the learner's own L1 plan relates to the fixed lesson order. In L7 the learner's suite had to pass and fail
grader variants whose slots depend on `CALENDAR_NOW`, but nothing passed that clock to `make ci`. So no honest
suite could compute expected slots or reach the 12 engine mutants. The check's failure message was also left
unspecified, although each submission costs 8-10 minutes. The grader's image-only PATH
(`/usr/local/go/bin:/usr/bin:/bin`) did not provably contain node, npm, tsp or openapi-typescript, which honest
`make ci`, `make gen` and `build-web` call. L2, L4 and L5 had no per-part minutes. L1 gave 10 minutes for
hand-computed exact DST instant lists. And because each lesson's starter is the previous lesson's reference, with
no prerequisite gate, copying the next starter passes L1-L7.
Rule: Walk the module's own reference plan through every rubric the module grades the learner by, and justify any
exception in the learner-facing text. For every check that runs the learner's code against grader-owned state,
list each input the honest solution needs (clock, delays, seeds, URLs) and pass it in. Run the honest commands
under the grader's exact env (PATH, HOME, network) before pinning that env. Give per-part minutes for every
lesson. Say which lessons a starter reveals the answer of, and how that is gated.

### 2026-11-03: Standards cited for semantics while the mandated syntax contradicted them; Docker and Nuxt rules not walked against the docs (#44, design round 1, accuracy)

Revision 1 of #44 mandated `Idempotency-Key` as an unquoted `[A-Za-z0-9_-]{8,64}` token and cited the IETF httpapi
draft for 409/422. draft-08 (2026-10-22) says the value "MUST be a String" (RFC 9651 sf-string, quoted; example
`Idempotency-Key: "8e03978e-..."`). The L8 rule "no `latest` or untagged FROM" rejects `FROM scratch` and
`FROM <stage>`, the very multi-stage and scratch forms the design expects. The L6 honest `routeRules` proxy reads the
backend URL only at `serve-web` time. Nuxt documents env overrides for `runtimeConfig` keys only, and the research
marked the route-rule override as "observed only". Pinned decision 5 claimed that `seal-object-schemas` makes the
openapi-typescript types exact. openapi-typescript already omits index signatures by default
(`--additional-properties` defaults to false), and its docs never mention `unevaluatedProperties`.
Rule: When a design cites a standard for part of a mandated surface, check the rest of that surface against the
standard too. Then either conform, or say in the brief which part is the course's own choice. For every
syntax rule over a vendor format (FROM refs, config keys), list the vendor's documented special forms and exempt or
reject each one explicitly. Never build an honest variant on a behaviour the research marked "observed only".
Every "because" in a pinned decision is a factual claim; check it against the tool's own docs.

### 2026-11-03: Anti-cheat claims rested on unrun stand-ins; the cheapest attacks were fingerprints and placement, not the listed classes (#44, design round 1, assessment)

Revision 1 of #44 put the L7 blind-guess bound at 5.9e-6 under a "nothing observable" model. But each of the 4
green variants differs from the reference in one cosmetic thing: id scheme, problem text, charset plus 50 ms
latency, Allow order. The 18 mutants share the reference's cosmetics. So a suite with no behavioural test calls
those 4 green and guesses among the 19 runs that look like the reference. That passes 2.0% of submissions, and
5.3% with a counter in /tmp or the live workspace, which the learner uid can write even under R0. That is about 19
submissions with no attempt caps. The L5 probe recorded R3, the delay placed outside the critical section, as
residual "because it needs the skill". A toy Go server that sleeps first and then does a racy check-then-insert
passed the 12x6 probe 15/15. A one-rule timing check (a POST that fails the check answers in under delay/2) fails
it by construction. The L7 drift case (3), one property removed, is passed by `cmp schema.d.ts golden`. The
TypeSpec host allowed any JS whose realpath is inside the pinned dir. A `.tsp` import of the image's
`@typespec/compiler/cmd/tsp.js` ran the CLI and killed the compile. `import "yaml"` ran the JS and compiled clean.
Rule: For every "cannot pass" claim, write the cheapest stand-in that uses each observable the check leaves
uninformative (cosmetics, timing, a counter across runs) and compute its pass rate before stating a bound.
Randomise every non-graded dimension the same way over the green and red sets. Before recording a residual, look
for a by-construction observable of the effect, such as where in the handler time is spent. A JS-loading guard is
an exact allowlist of entry files, not a directory.

### 2026-11-03: A time estimate rested on reuse that the earlier lessons never set up (#44, design round 2, pedagogy)

Revision 2 of #44 fixed L7's clock at `CALENDAR_NOW=2026-03-01T08:00:00Z` and budgeted 15 min for "replaying his L3
cases through the HTTP slots endpoint", on the grounds that the cases were "written against this `now`". But L1 and L3
never ask for that `now`. Each case carries its own `request.now`, and the L3 bounds don't constrain it. The case's
`bookings[]` are only required to be "consistent with the model", but over HTTP every booking has to be created
through POST /bookings, which rejects bookings that are off-grid, outside availability or inside notice. Bookings
also conflict host-wide, so cases replayed against one server interfere with each other unless they are cancelled
or put on disjoint dates. So an honest learner's L3 cases mostly cannot be replayed. The 12 engine mutants then have
to be killed by new HTTP tests, and the 85-min suite estimate doesn't hold.
Rule: When a later lesson's minutes count on reusing an earlier artefact, write the reuse conditions (fixed inputs,
which data must be creatable through the public interface, isolation between cases) into the earlier lesson's
task.md and bounds. Then have a demo run the reuse on the reference artefact, not only on a suite the designer wrote.

### 2026-11-04: A tool self-check compared realpaths to install dirs without reading the install layout (#44, design round 2, accuracy)

Revision 2 of #44 (7.1) required `go`, `node`, `npm`, `npx`, `tsp`, `openapi-typescript`, `make`, `git` and
`python3` to "resolve under that PATH to the 11 install dirs (realpath compared)". The PATH has 5 dirs and section 11
pins 3, so "11" matches nothing. And on the official Node build, `bin/npm` and `bin/npx` are symlinks to
`../lib/node_modules/npm/bin/npm-cli.js` and `npx-cli.js` (node `tools/install.py`, `package_files`). Their realpath is
under `/opt/node/lib/...`, not `/opt/node/bin`, so the check would fail closed on the honest image at every check
start. Revision 2 also copied the judge's "earlier stage name, case-insensitive" into the FROM set (F2) without
opening the BuildKit source; see judge_mistakes 2026-11-04.
Rule: Before pinning a check over installed files (paths, realpaths, symlinks), write the expected value of each
member from the vendor's install script or a listing of the real artefact, as a table, and count its rows against the
number in the text. A judge's wording tagged [J-x] is still a claim: open its source before building a closed set on it.

### 2026-11-04: Closed a concurrency residual with the judge's two rules and did not probe their neighbours (#44, design round 2, assessment)

Revision 2 of #44 deleted residual R3 ("R3 is closed (S3)") after adding the judge's rule a (fast 409 on a taken slot)
and rule b (no booking visible before 0.9 x delay). A prototype of the 3.2.8 probe found three servers with no atomic
check-and-write that pass all of the rev-2 rules: an unlocked check, then the delay, then an unlocked recheck and
write, 30/30; the same with a racy pending set, 30/30; and a racy reservation, 9/30. The first is "optimistic read,
lock, recheck, delay, write" with the lock left out, which is a natural mistake. One more observable (a conflicting
POST sent at 0.5 x delay must get 409 no earlier than the winner's 201 and no later than 1.3 x delay) brings all
three to 0/30, and the honest forms stay at 30/30. Revision 2 also recorded the TypeSpec JS allowlist from the
reference compile and required every member to be necessary for that compile. But an honest `import
"@typespec/openapi3"` requests `openapi3/dist/src/tsp-index.js`, and a reference that does not import openapi3 never
requests it. The (3a) drift case also leaves the hand edit uncommitted, so the listed honest form
`make gen && git diff --exit-code` exits 0 on it.
Rule: When a residual is closed with prescribed rules, list the attack's neighbours before deleting the residual:
the same race moved to another point in the request, each lock removed from each honest form, the delay outside the
atomic section. Prototype each one against every rule. When a closed set is recorded from a run, record it over the
whole honest corpus, not only the reference. When a git-based honest form must pass a planted case, commit the plant.

### 2026-11-16: Re-graded an earlier module's skill, sibling checks disagreed on honest forms, the first run named a "find" step (#45, judge_design round 1, pedagogy)

Revision 1 of #45 made "cut the draft to what the code cannot tell" the first verb of L2. It graded that verb with
a copied-lines cap and a rubric criterion that repeats 00 L5's word for word, although the research overlap table
said not to re-grade it. memory-layout accepted facts imported via `@` as an honest form, while memory-rubric read
only CLAUDE.md and rule files and so scored that form 0. Team note F1 ("never rename label files") contradicted
manifest.py's rename to `.done`, so it read like the planted stale note. The S2 test command did not run on the
L2 starter, which has no tests/. The L1 decoy "quote_parcel has no side effects" was a literal yes under the
undefined "changes state" of the ladder (module cache). L4 budgeted 20 min to "find holes by sabotage", but the
first counted run on the untouched starter names all five holes. L1 gave a 400-line transcript 8 min less reading
than the measured 01 L6.
Rule: For every lesson, check each graded verb against the overlap table and the earlier modules' module.yaml.
Then run every honest form one check accepts through each sibling check of the same artifact. Walk each planted
note and decoy against the starter code as a literal reader would. For every "find" step, read the check's message
on the untouched starter. Size each part from the analogue's measured part, not from the analogue's total.

### 2026-11-16: "The docs do not settle it" again, a must-not check on a partial loading model, an always-fails claim never computed (#45, judge_design round 1, accuracy)

Revision 1 of #45 excluded nested `.claude/` rules and subdirectory AGENTS.md from the L2 resolver "because the docs do
not settle them". The memory page settles both. It lists "Rules files in a subdirectory's `.claude/rules/`" among the
files that load on demand, and it reads a subdirectory AGENTS.md only when no CLAUDE.md counts. That is the #43 round-2
mistake again. C3's must-not-load side was computed on that reduced model, and it also left out CLAUDE.local.md,
subdirectory CLAUDE.local.md and the user-level `~/.claude/CLAUDE.md` and `~/.claude/rules/`. So a fact Claude Code
does load for a foreign file could still pass "not loaded". 5.2 and R9 said that a test reading the real date or hour
"fails on at least one green run" and that this is "deterministic by the 26-hour span". At UTC 00:00-00:59 and 12:00-14:59
(local hour 12 or 0-2 at UTC-12), all three zones are before the 15:00 cut-off. A pair of consecutive dates Mon/Tue is
the same "weekday" case. The rollout quiz wrote METR 2025 as "measured -19%", but METR's own convention (2026 update)
writes that result as +19% (slower) and -18% as faster.
Rule: Before writing "the docs do not say", search the vendor page for the file or setting by name and quote what it
says. A must-not-load check models every documented loading source, team or personal, launch or on demand (a superset).
A must-load check counts only the sources the task accepts (a subset), and task.md names both. Before an "always fails"
or "deterministic" claim over a drawn set, enumerate the whole set: every UTC hour, every weekday pair. Copy a study's
numbers with the study's own sign convention and write the direction in words.

### 2026-11-16: An in-process sandbox specified as a blocklist, never attacked through imports, links or fd-relative paths (#45, judge_design round 1, assessment)

Revision 1 of #45 ran grader mutants in the same process as the learner's tests. It left the canonical `shipping/` text
on disk in the run root. It said an audit-hook blocklist "closes" the first-run capture. A prototype showed three
bypasses. First, `unittest.TestLoader().discover("shipping", top_level_dir="shipping")` plus
`mock.patch("labels.X").getter()` loads the original code as a top-level `labels`. That oracle kills every mutant
(5/5), with no banned name and no copied function. Second, a symlinked `tests/canon -> ../shipping` is invisible to
rglob/os.walk in stage 0, but `copytree` copies it in (3/3). Third, `os.open(..., dir_fd=fd)` after an `os.chdir`
writes outside the root. The `open` audit event carries no dir_fd (3/6). So does a hard link whose source is outside
the root (5/8). In agent-gate, R5 and the binary half of R1 were task rules that no probe could fail on.
Rule: When learner code shares a process with the code under test, list every way that process can reach another copy
of that code (import path changes, unittest/mock importers, files copied in through links), and state the effect to
block. Specify a sandbox as an allowlist of effects (writes only inside the root, whatever the API, link sources and
fd-relative paths included), not as a list of events. Stage 0 and the run must see the same bytes. For every rule a
learner-written tool must implement, name the probe that fails when the rule is left out.

### 2026-11-16: Literal walk applied to notes and decoys but not to the outcome's own placement rule; per-part minutes that contradict their stated basis (#45, judge_design round 2, pedagogy)

Revision 2 walked every L1 decoy and every L2 note literally, but not the five L2 facts against O2. O2 says each fact,
"в том числе" for Explore, reaches the agent with the files of that fact. The key puts F4 and F5 at launch, which
Explore skips, and no printed criterion decides launch versus area. Section 8 still claims that choice as the new
skill. A literal reader of O2 puts F5 in a path rule on the Makefile and fails C2. The sizing was shown per part, and
two parts contradict their own basis. L1 sized repo verification for "about 12 claims", but its table has 27 graded
items, 23 of which need the repo. L4 cited "24 + 14" from 02 L2 and budgeted 30.
Rule: Walk every key item against the outcome text and every printed decision rule, not only against the code. Where
the key decides a level or category, print the criterion and table each item against it. After writing per-part
minutes, recount the volume from the design's own tables and redo the arithmetic of every cited analogue.

### 2026-11-16: A tool's output format assumed, a "superset" that missed sources and settings, a quiz key beyond the docs (#45, judge_design round 2, accuracy)

Revision 2 of #45 made S2 accept a test command when its output has "`Ran N tests` with N >= 1". CPython 3.12 prints
`Ran %d test%s`, with no "s" for one test, and writes it to stderr. The L2 starter ships exactly one test, so every
honest corrected command fails stage 0. The changelog called the must-not model "the superset of every source on the
memory page". It left out root `.claude/AGENTS.md` and a subdirectory's `.claude/CLAUDE.md`. It stripped HTML comments
in every file, although the page documents that only for CLAUDE.md files. S4 also refused only `claudeMdExcludes`, while
`instructionFiles` (`managed-only`) in `~/.claude/settings.json`, `CLAUDE_CODE_DISABLE_CLAUDE_MDS` and
`CLAUDE_CODE_SIMPLE` in a settings `env` block also change what loads. O2 promised that Explore gets "каждый факт" with
its files, but the key puts F4 and F5 at launch, and Explore skips launch files. The rollout quiz keyed "with `--bare`
the CI agent does not see the rule file", while the docs name only CLAUDE.md.
Rule: Before a check parses a tool's output, quote the line of the tool's source or docs that prints it, singular and
plural included, and name the stream. A superset claim needs a table: every file and every setting the vendor page
names, each with "in D", "refused by stage 0" or "not learner-writable". Search the settings and env-var references for
the feature name before saying a setting list is complete. Every quiz key sentence has a quoted source that states it.
"I expect it does" is not a source.

### 2026-11-16: Rev-2 import guard carved out tests/, and the oracle moved into tests/ (#45, judge_design round 2, assessment)
Round-1 B1 put the fix target as "no code from a file in the run root except tests/** runs", and rev 2 built the import
guard to admit any file under <root>/tests/. The run writes tests/ to disk and the write guard allows writes in the run
root, so a characterization test writes the original labels.py (carried as a string const or a .txt fixture, read out of
the visible starter) into tests/orig_mod.py at run time and imports it as an oracle; it kills every mutant with no
behavioural assertion. T8 misses it because the copy is never a .py at stage 0. b1_runtime_py, b1_txt_fixture and
b1_overwrite all passed stage 0 and ran green under the literal rev-2 text. Separately, the guard looked up
os.path.realpath each call, so mock.patch("os.path.realpath") (an allowed API, no T4 name) blinded both the import guard
and the write guard: b1_patch_realpath and cap_patch_realpath passed the whole check.
Rule: a guard carve-out ("except tests/**", "inside the run root") is a hole the learner fills with their own pasted
copy; key the admit-list to the stage-0 BYTE set (byte-identity), not to a name or a location, and run the neighbour
that writes/overwrites a file inside the carve-out at run time. A guard that depends on a stdlib function (realpath,
fspath) must capture that reference at install, because mock.patch of it is cheap capture, and the guardrail exists
against cheap capture. Try the "blind the guard's own dependency" neighbour before claiming a guard closes a class.

### 2026-11-16: A blanket course-rule reason false for half the refused places; a habit no literal reader can perform; earlier modules' graded forms refused (#45, judge_design round 3, pedagogy)

Revision 3 of #45 gave one reason for the L2 allowlist: "so team facts lie where everyone finds them, and the check can
compute exactly what loads". That is false for `AGENTS.md` (the team file, and 00 L5's graded `@AGENTS.md` form), for
root `.claude/CLAUDE.md` (a committed file with a documented load time), and for shell startup and `.env*` files, which
are not memory places. Auto memory, which the agent writes by itself (00 L5 theory), was refused with no task text
about how it gets there or how to clear it. No demo listed the keys Claude Code writes into the settings files by
itself. The D8 habit "check the docs for your version" was kept as a sentence. But the research said the docs describe
only the newest release, and no step named `claude --version` or the changelog. The S5 example was a complete accepted
value. F5 ("never run `make reset-spool`") must sit in launch memory, while 02 L1's ladder puts such a rule in a hook
or deny and out of memory. The hook form was refused by the key allowlist. Two-model numbers (5 hops and comment text
for must-not) decided counted results and were not in the task.md lists.
Rule: Walk a course-rule reason against every class it refuses, one class at a time, and write a true reason for each.
List what the tool writes by itself during an ordinary session (memory, settings keys), from a run in the image, and
either accept each item or name it in the task with its fix. A habit the lesson makes central is printed as steps a
literal reader can perform with what the workspace has. Before keying any fact's placement, run it through every
earlier module's placement rule (00 L5, 02 L1), and say in section 8 where this lesson departs and why. Every number
and model rule that decides a counted result goes into the task.md list, the must-not side included.

### 2026-11-16: A hedge applied to one message of a model pair, and the subset model's cuts printed as load facts (#45, judge_design round 3, accuracy)

Revision 3 of #45 closed round-2 note n7 by adding "по модели проверки" to the must-not message only. The must-load
messages ("F4: не загружается при запуске сессии") still state a load fact whenever the subset model A lacks the term. A
drops block HTML comments from rule files, which the memory page strips only "in CLAUDE.md files", and it cuts imports at
3 hops where the page says four. So F4 in a comment of a launch rule gets "не загружается" although the docs say nothing
of the kind. The comment rule for non-CLAUDE.md files was also missing from the task.md course rules.
Rule: When a check uses a subset model and a superset model, every message from either one says it is the check's
model ("по модели проверки"), not the tool's behaviour. Every place where a model is narrower or wider than the docs
(comment stripping, hop count, frontmatter, pattern forms) is printed in task.md as a course rule, with the docs' own
scope quoted.

### 2026-11-16: A captured reference closed the guard's decision but not the importer it delegates to; the allowlist refused what the tool writes itself (#45, judge_design round 3, assessment)

Revision 3 of #45 captured `PathFinder.find_spec` in the import guard and listed
`mock.patch("importlib.machinery.PathFinder.find_spec")` as closed by G-rule 1. The guard only advises. When its
captured lookup finds nothing, it returns None, and the patched `PathFinder` later in meta_path loads a run-time
`<root>/hidden/orig_mod.py` holding the original source. That oracle kills every mutant (3/3). Its neighbours
(`SourceFileLoader.get_data`, `importlib._bootstrap._find_spec`, `pkgutil.get_importer` plus a loader subclass) each
beat at least one runtime fix. A static T4 ban on the import-system vocabulary refused all of them, and the honest
corpus stayed green. In L2, the closed settings key allowlist and the auto-memory term rule gave exit 3 on the passing
reference after `/effort`, a `/config` toggle, the `/memory` toggle or `/sandbox`, and after Claude saved a team fact
to `~/.claude/projects/<project>/memory/MEMORY.md`. Claude Code writes all of these by itself.
Rule: When a guard captures a reference, trace who actually performs the guarded action after the guard returns. If
that is a later, patchable component, the capture closes nothing. Close the class with a static rule the learner can
read, and run each listed neighbour before calling it closed. Before an allowlist refuses state, grep the vendor
reference for what the tool writes by itself ("writes this key", auto memory), and run the reference with that state
present.

### 2026-11-17: Notes restated without their prohibition, and the walk table kept the old prohibition's actions (#45, judge_design round 4, pedagogy)

Revision 4 of #45 took the prohibitions out of F1-F4 so that they reach step 7 of 02 L1's ladder. That left the L2
criterion's "запрещает или объясняет" to decide on "объясняет" alone. F2's first sentence, "Production servers run TZ
`Europe/Moscow`", explains every use of the server's local time: the labels.py stamp, manifest.py's `date.today()`, and
any new module. On a literal reading that makes F2 a session fact. The key says area, with labels.py in F2's must-not
set. The 6.2 walk table still listed revision 3's F2 actions ("change the comparison; change the hour"), which came from
the removed "Do not convert either to UTC". O2 named "окружение продакшена" as an example area fact, so it taught the
reverse of the printed criterion.
Rule: When a note's text changes, walk it against the criterion again, one sentence at a time, and write the actions
each sentence explains into the table from the new text. Check every file that a sentence plausibly concerns against
the note's must-not set. Every category an outcome gives as an example of a level must get that level under the
printed criterion.

### 2026-11-17: A team note contradicted by the codebase it describes; a printed procedure that sends the learner to the wrong pages (#45, judge_design round 4, accuracy)

Revision 4 of #45 rewrote F4 as "`ledger-sync` reads every money amount parcel-desk produces, in any module, as int
kopecks". The design's own section 3 has manifest.py writing rubles (`(k + 49) // 100`) and `format_rubles`, and the
table still said "code agrees? yes". F3's "resolver column included" also makes renaming zones_v1.py a change the note
explains, so a literal reading makes F3 a session fact. That is the same class as the pedagogy F2 entry above. The new
version procedure said "Open the memory and sub-agents pages ... Find V1-V7 there", but V7 is on best-practices and V2's
Bash list is on tools-reference.
Rule: Before writing "code agrees", grep the codebase description for every noun a note quantifies over ("every money
amount", "every change"), and check each output it names. A printed procedure names the page for each statement it asks
the learner to find. Open each page and confirm the statement is there before printing the step.

### 2026-11-17: The check recognises a fact by its term, and task.md never says so (#45, judge_design round 5, pedagogy)

Revision 5 of #45 grades C2/C3 by finding each note's term (`printerd`, `pickup-board`, ...) in the modelled text. But
10.3 never tells task.md to print that rule, and rule 5 ("never name key contents") invites hiding it. A root
CLAUDE.md index line such as "`.claude/rules/printerd-labels.md`", or an `@docs/team-notes.md` import, holds an area
term at launch, and C3 must-not fails, counted. Neither one is a copy of the fact the criterion talks about.
Section 3 also leaves README.md and the stand-in CLAUDE.md unpinned against the terms, though rule 3 k) expects
learners to import them.
Rule: For every counted rule, print the observable the grader matches on (here: which text counts as a fact, and how
it is matched), not only the intent ("the fact loads"). Then run the honest by-products of the task against it: an
index, a pointer, a file name in prose, an import of the source document. Pin every starter file that can become graded
input against the matched tokens.

### 2026-11-17: A criterion sentence kept the old "changes" frame; a research example list printed as a closed set of forms; a size reason lost its condition (#45, judge_design round 5, accuracy)

Revision 5 of #45 moved the L2 level to the scope line but kept "Проверка считает только изменения, которые называет
строка охвата". The line names files, and the check counts no changes, so a literal reader takes it to mean "only the
named files are checked". C3's must-not side checks files the line does not name. Version step 2 printed "version
notes are inline sentences of two forms", but the research had said "Two forms recur". The memory and tools-reference
pages also use "vX and later", "before vX", "vX or earlier" and "On Claude Code vX or later", some with X above 2.1.311.
The printed size reason said the docs cut on-demand files "после этого предела" (40,000). The docs give 40,000 only
for a 200K context window, and say Claude gets the start plus a pointer to read the rest. The design's own 5.3 gap
line had kept "with a 200K context window".
Rule: When a decision changes what decides a result, delete or rewrite every printed sentence that describes the old
observable, and check that each one names what the check computes. Never print an example list from research as the
docs' complete set: grep the page for the general token (`v2.`) and print a rule that covers every hit. Copy a
documented limit together with its condition.

### 2026-11-17: Counted "one hit" in the step-2 sections, over the researcher's own enumeration that listed two (#45, judge_design round 6, accuracy)

Revision 6 of #45 fixed round-5 blocker 2 by searching each page for `v2.` and reading every hit inside the nine
step-2 sections. It then asserted three times (design lines 39, 500, 1356) "the nine sections hold one hit: 'Before
v2.1.211' in 'Set up rules' (accuracy r5)", and sized step 2 on that count. Opening the live sub-agents page today, a
second hit is inside a step-2 section: "## Built-in subagents" (the V6 row of the design's own table) contains
"... set `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` ... Requires Claude Code v2.1.198 or later." That hit lies
between `## Built-in subagents` and the next `##`, so step 2 reads it. The architect's own source,
45-research-pages.md section 4, already listed it ("In 'Built-in subagents': 'Requires Claude Code v2.1.198 or
later.'"), but the design copied the round-5 accuracy judge's undercount with its "(accuracy r5)" citation over the
researcher's data. The learner-facing handling survives (line 1362's expected case is a class, "mentions whose X is
at or below 2.1.311", and v2.1.198 falls in it), but the stated fact and the minutes basis are wrong.
Rule: A count of matches in a defined scope is a claim to verify by scanning the scope, not by copying an upstream
summary. Before writing "N hits" (or "one hit"), run the search the step prescribes over every named section of every
named page, and cross-check it against the researcher's own per-section listing; when a cited review and a cited
research page disagree on an enumeration, open the page and take the larger set.

### 2026-11-17: A trap-list sentence said prose passes the `exec*` prefix rule, and 5.1 and 10.3 disagreed on its tokens (#45, judge_design round 7, accuracy)

Revision 7 applied assessment r6 N5 by adding to 5.1 and to 10.3 rule 10 that part 1's `exec*` prefix rule refuses a
helper `execute()` while "the word 'execute' in prose passes". The cited reference, `stage0_r5fix.py` `bad()`, also
applies the prefix test to every str constant, whole and per `[.:]` segment. So `"""execute the quote twice."""`,
`subTest("spawned label")` and `"runner.execute"` are refused, and only mid-sentence prose and comments pass.
5.1's own rule line still says "any `exec*` ... attribute", while the new sentence says names are refused too. The
only run behind it (judge-r6 `fp/vocab2`) had "We execute" in mid-sentence, which is the one prose form that passes.
Rule: When a revision adds an "X passes" or "X is refused" sentence about a stage-0 rule, read the function that
implements the rule and list every token kind it is applied to. Then walk the sentence's example against each kind,
including a string that begins with the word and a segment after each separator. Make the rule line and the
learner-facing sentence name the same token set.
