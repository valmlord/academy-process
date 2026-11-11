# practice-designer mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seed: a check that could not fail

A command check passed on the untouched starter, so it proved nothing.
Rule: Run every check on the untouched starter (must fail) and on the reference solution (must pass).

### 2026-10-30: A quiz decoy keyed false on a point the docs leave open (#42, judge_content round 1, accuracy)

L4 quiz.yaml `local-open-weight-model` option d ("Claude Code сам перейдёт на короткий системный промпт для незнакомой
модели") is keyed false. Changelog 2.1.312 only says which providers changed (Bedrock, Vertex, Foundry, Mantle). The
env-vars row gives the full prompt only to the Haiku 4.5 / Sonnet 5 / Opus 4.7 families and the shorter one to newer
models, so a learner can read d as true. The lesson's own theory says the docs are silent on gateways.
Rule: Before you key a decoy false, find a source sentence that refutes it. If the docs are silent, or a sentence
can be read as supporting it, replace the decoy with one the docs clearly refute.

### 2026-10-30: The replacement decoy is refuted only by a page missing from `sources` (#42, judge_content round 2, accuracy)

The new L4 option d ("WebFetch перестанет отправлять имя хоста на `api.anthropic.com`") with a local Ollama server is
keyed false. The explanation says the check runs "куда бы ни шли запросы к модели" and that NONESSENTIAL_TRAFFIC does not
affect it. The cited network-config names only Bedrock, Vertex, Foundry and the Claude apps gateway. Only data-usage
("runs regardless of which model provider you use and is not affected by `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`")
covers a local server, and it was not in lesson.yaml `sources`.
Rule: The refuting sentence must be on a page listed in the lesson's `sources`, and it must cover the exact scenario of the
question (here a local server, not a cloud provider). If it is on another page, add that page before you key the option.

### 2026-10-27: Grader environment and probe sets are part of the check (#15, design review)

Found at #15 design review: python checks can be forced to exit 0 via a learner-written
usercustomize.py unless run with `python3 -I`; learner code running in the same uid can find the
grader mount via /proc/<ppid>/cmdline and exec `checks/reference/`; a hook/permission check whose
probes are all "must block" passes a block-everything solution.
Rule: Run every python check as `python3 -I`, keep the oracle (scripted model, recorder log, verdict)
outside the learner process, add near-miss "must allow" probes, and try the usercustomize and
read-the-reference cheats in the demonstration.

### 2026-10-28: One file-loading model, implemented twice and inconsistently (#15, judge_content)

L5 `verify_memory.py` resolves `@path` imports correctly in `imports_of()`: the path is relative to
the importing file, and an `@` inside code spans or fences does not count. `check_hookup()` ignores
that and only looks for a raw `@AGENTS.md` line. So `.claude/CLAUDE.md` = `@AGENTS.md` passes,
although it imports `.claude/AGENTS.md`. A `@AGENTS.md` inside a ``` fence passes too, and that
imports nothing. The correct `.claude/CLAUDE.md` = `@../AGENTS.md` fails. The rubric does not grade
the hookup, so in these cases AGENTS.md never loads and the solution still passes.
Rule: When a check models how a tool loads or resolves something, every rule in the check goes
through that one resolver. Then add demo cases where a raw text match and the real resolution give
different answers.

### 2026-10-28: A closed list of dangerous allow rules is never closed (#15, judge_content)

L6 `permissions-policy` rejects broad allow rules from a fixed list (`Bash(sh *)`, `Bash(python3 *)`,
...). `Bash(uv run *)`, `Bash(npx *)`, `Bash(npm run *)`, `Bash(find *)`, `Bash(docker *)` and
`Edit(//**)` are not on it, and each one passes. Each lets the agent run db-reset, curl or anything
else on the host with no prompt (`uv run python -c`, `find -exec`, `docker run -v /:/h`), which
breaks policy item 7. The Makefile was fixed the right way (C11/C12: compare against the pristine
copy). The allow list kept the deny-list approach.
Rule: When the policy names exactly what may run without a prompt, make allow a closed set: accept
only rules from that set and fail any other rule by name. Do not try to list the dangerous ones.

### 2026-10-28: Closing the allow list but not the other keys that grant without a prompt (#15, judge_content round 2)

L6 `permissions-policy` made `permissions.allow` a closed set, but `permissions.defaultMode` is
still a deny list with one entry (`bypassPermissions`). The reference settings plus
`"defaultMode": "acceptEdits"` (or `"dontAsk"`) pass. The same lesson's Makefile check rejects
`claude --permission-mode acceptEdits` (C6), so the check accepts in settings the mode it rejects in
the Makefile. In acceptEdits, edits outside `src/` and `cp`/`mv`/`rm`/`sed` in the working dir run
without a prompt (research-l6, modes table), and `cp .env.staging x` is not covered by the Read deny.
Rule: When you close one channel that grants actions without a prompt, list every other channel the
model knows (allow rules, starting mode, launch flags, hooks) and close each one the same way. Use
one accepted set for one concept, for example the same mode set for `defaultMode` and the Makefile
recipe.

### 2026-10-28: A closed set that drops a documented alias, with one reason line for every value (#15, judge_content round 3)

L6 `permissions-policy` closed `defaultMode` to absent / `"default"` / `"plan"`, but the
permission-modes page says the CLI accepts `"defaultMode": "manual"` (and `--permission-mode manual`)
as an alias of `default`, research-l6 lists it, and the lesson's own theory.md:60 names `default`
"Manual". The check fails `"manual"` with the generic reason "другие режимы пропускают вопросы, на
которых стоит политика", which is false for `manual` (it is `default`) and for `auto` (ignored from
project settings, as task.md:99 itself says). The reason line for `acceptEdits` also claims
`cp .env.staging x` runs without a prompt despite the learner's `Read(.env*)` deny; the permissions
page lists Bash file commands the deny covers only as "such as `cat`, `head`, `tail`, `sed`, `tee`",
so whether `cp` is covered is undocumented.
Rule: When you close a value set, take the full list of accepted spellings from the source, including
aliases, and accept every alias of an accepted value. Give each rejected value its own failure
message that matches the reason stated in task.md. Do not put in a reason line a bypass that the
source does not document; use an example the source states outright.

### 2026-10-30: An import resolver that tokenizes differently from the tool it models (#41, judge_content round 1)

L2 `skills-structure` follows `@path` imports to count the memory budget. Its token regex was
`(?:^|\s)@([^\s]+)`, and it kept the token as written. Claude Code's own loader (found with `strings` on the
installed binary) uses `(?:^|\s)@((?:[^\s\\]|\\ )+)`, cuts the token at `#`, and turns `\ ` into a space.
So `@docs/procedures.md#steps` and `@docs/proc\ edures.md` import the whole old procedure in Claude Code,
but the check never followed them, and the memory check passed (exit 0). The plain `@docs/procedures.md`
correctly failed.
Rule: When a check models how a tool parses something (imports, globs, frontmatter, paths), copy the
tool's own tokenization from its source: the regex, fragment handling, escapes and the resolution base.
Then add one must-fail case for each normalization the tool applies (`#fragment`, escaped space). "We
reject the forms we thought of" is not a resolver.

### 2026-10-30: Copied the tool's regex but not the input it runs on (#41, judge_content round 2)

The round-4 fix gave L2 `verify_skills.py` Claude Code's import regex, `#` cut, `\ ` unescape and
path-start rule. But Claude Code does not run that regex on raw lines. It lexes the file with marked
(`gfm: false`), runs the regex on each inline `text` token, skips `code`/`codespan`, and runs it on
HTML-comment blocks after the comments are removed. A text token starts right after `**...**`, `_..._`,
`<b>`, `\*`, a link or an HTML comment, so `(?:^|\s)` matches there even though the raw line has no
space before `@`. The checker's own per-line backtick and fence detection also disagrees with
CommonMark (a backtick fence info string containing a backtick, a shorter fence inside a longer one,
code spans that cross a line break). Eight such forms (`<!-- c -->@docs/procedures.md`,
`**Team conventions:**@docs/procedures.md`, ...) load the whole old procedure in Claude Code and pass
the check with exit 0. The record called "HTML comments not stripped" stricter-only, but it was the
opposite: stripping is what puts `@` at the start of the text.
Rule: When you model a tool's parser, find the regex, then also find what it is applied to (token
stream, after which transformations). If you cannot reproduce that input exactly, use a superset that
is stricter by construction (for example: any `@` not preceded by a letter or digit, anywhere in the
file, every delimiter-cut prefix tried) and prove it covers the tool. Run the comparison on a corpus,
not only on the cases from the FAIL. "Stricter only" is a claim that needs its own negative case.

### 2026-10-30: A key layer that the lesson's own definitions reject (#42, judge_content round 1)

L3 I04: the incident says the Stop hook runs only tests and A2 already exists in `make check`; task.md says "choose the fix
that prevents the repeat, not what the repo already has" and "a Stop hook running `make check` is `hook`". The key
(`failure_key.json`) accepts `check` and `code` and rejects `hook`, and the reference fix ("make the Stop hook run
`make check`") is labelled `check`, so it fails rubric F1 on its own definitions. The key was carried from the design walk
after the text around it changed.
Rule: After any change to the printed ladder or its definitions, re-walk every key entry from the printed text alone and
check that each reference fix sits at the layer it is labelled with under the rubric's definitions.

### 2026-10-30: Probes that a stub can tell apart without doing the work (#42, judge_content round 1, assessment)

L2 `arch-workspace-clean` item 8 ran `make -s check` on the copy as is and with one NEW planted file (an A1 import, a
failing test). A `check` target that only compares the file list with a committed list, or only looks for an
`m<6hex>.py` name, runs neither the suite nor the linter and passed on 3.11 and 3.12. Separately, the L2 and L3 suite
ran the workspace's own test files: a regression in `/invoices` plus an edited starter-test assertion passed both
checks with "стартовые тесты зелёные". The demo covered exactly the design's listed forms (`check: true`, `|| true`) and
no neighbour.
Rule: For every probe of learner machinery, write down what a stub would need to tell the variants apart, and add a
must-pass variant that differs only in a harmless way plus a must-fail variant inside an existing file, so that only
doing the real work separates them. Run graded tests from the pristine copy in `checks/data/` (or hash them) wherever the
task does not ask the learner to edit them. Before the demo, build two stubs that are not on the design's list and show
them failing.

### 2026-10-30: Fixes that closed the named form and left its neighbour (#42, judge_content round 2, assessment)

Round-1 B2 fix put pristine starter test files back, but learner-added test files still ran in the same process and are
imported first: a new `tests/test_00_helpers.py` that rebinds `InvoiceListTest.test_filters_by_status` (or its `run`, or
its `assertEqual`) hid a broken status filter in L1, L2 and L3 on 3.11 and 3.12. Round-1 B1 fix planted only A1, in three
column-0 forms, so a `check` target running the real suite plus `! grep -rqE '^(import|from) +invoices' src/ledger`
passed item 8 without running the linter.
Rule: State each fix as the effect to observe ("no learner file runs in the process that runs the pristine tests";
"`make check` passes only if the learner's linter ran"), and build it so that the effect holds by construction
(separate child with only pristine files; require the linter's own line for the planted statement in make's output, and
plant every rule in forms drawn from the hidden-root renderer). Then demo the one-line cheat a stubborn agent would
write first (monkeypatch from a new test file, grep for the planted line) against the fix before handing it back.

### 2026-10-30: A planted mutation that can break a correct project before the graded command runs (#42, judge_content round 3, pedagogy)

C2 appends an A1 chunk, drawn from the `a1-forms` templates, to `src/ledger/accounts.py` and then requires the learner's
own linter line in the output of `make -s check`. Four of the ten A1 chunks execute `import invoices.money` at module
level. The task allows an A1 fix that moves `format_cents` to `src/shared/` and deletes `src/invoices/money.py`, and it
allows added tests. If the learner also has a test that imports `ledger`, that test errors on the planted copy. The
canonical target `check: test` (the reference Makefile's own shape) then stops before the linter, and item 8 fails with
"цель check должна запускать линтер". That message is wrong for this project, and it fails about 40% of runs. The
reference keeps `invoices/money.py` as a shim, so its 20/20 never reached this corner.
Rule: A mutation the grader plants to observe one command (the linter) must not change the result of the commands that
run before it on any solution the task allows. Either draw only forms that cannot fail at runtime (not executed, or
importing only modules the task guarantees exist), or run the copy's tests after planting and redraw if they turn red.
Demo with a correct solution that differs from the reference in every way the task leaves open: deleted shims, added
tests, `check: test` ordering.

### 2026-10-30: One drawn form per rule let a grep stub that forges the linter's lines pass 10% of runs (#42, judge_content round 3, assessment)

The C2 fix in L2 item 8 plants one A1, one A2 and one A3 chunk per run and requires the learner's own linter line for
each in the output of `make -s check`. A 12-line `grep -n` script printed `<rule> <path>:<line>: ` plus the reference
linter's exact message, with fixed module names, and never ran the linter. It reproduced the line for 3 of 10 A1, 3 of
5 A2 and 4 of 5 A3 chunks, so the real check passed it in 4 of 40 runs on 3.11 and on 3.12. With unlimited attempts that
is a pass. The demo had tried only the two round-2 grep stubs.
Rule: When a check samples one variant per run from a set, a stub only has to beat the sampled variant, and retries
are free. Require the whole set in every run when it fits the budget. Before handing the fix back, demo the cheapest
stub that targets the easiest member of the set, and report its pass rate over 40 runs, not one verdict.

### 2026-10-30: Reworded task text describes the check from memory, not from its code (#42, judge_content round 4, accuracy)

Two items in the round-3 fixes were reworded without reading the code they describe. L1 item 10 now says that deleting
a starter test in `tests/test_statement.py` "ничего не меняют". But `verify_pokayoke.STATIC_TEST_FILES` includes
`test_statement`, so stage 0 reports the missing name, and the same task.md says so two paragraphs later. L2 item 8
now says that "все формы нарушения ... из скрытых проектов" are planted. But `planted_violations` takes only `files[0]`
of each template: 10/5/5 of the 11/8/8 single-finding forms.
Rule: Every sentence that says what a check does, or does not react to, is checked against the constant or function
that implements it before hand-back: grep the file named, the list or constant that bounds the set, and the stage that
reads it. Words like "все", "ничего", "всегда" need a pointer to the code line that makes them true.

### 2026-11-11: Model ID set and alias map frozen while the task text defers to the live models page (#43, judge_content, accuracy)
L1 task.md rule 2 accepts any ID "в точности как в строках Claude API ID и Claude API alias обзора моделей". The models
overview now lists `claude-fable-5-2` (Fable 5.1 moved to Legacy) and model-config resolves `fable` to Fable 5.2. Every
`checks/agent_defs.py` FULL_MODEL_IDS lacks `claude-fable-5-2`, and ALIAS_MODELS, the starter fakes, result_templates.json
and verify_*.py still map `fable` to `claude-fable-5-1`. So the grader rejects an ID the task text says is accepted.
Rule: a check that implements a rule phrased as "whatever page X lists" pins the snapshot in the task text ("обзор
моделей на 2026-11-03: ...") or is re-synced with the page before every judge round. Keep the alias map and ID list in one
shared constant and grep every copy when it changes.
