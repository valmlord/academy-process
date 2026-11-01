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
