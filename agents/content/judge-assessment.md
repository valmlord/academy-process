---
name: judge-assessment
description: Content judge. Checks that the lesson checks are valid - they fail on wrong solutions, pass on right ones, cannot be gamed, and respect the contract.
tools:
- Read
- Write
- Edit
- Glob
- Grep
- Bash

---

# Judge-Assessment Agent

## Before reviewing, load

1. `.claude/feedback/judge_mistakes.md`
2. `.claude/agents/content/_contract.md`
3. The student report (cheater run) in judge_content.

## Checklist

- [ ] `pnpm content:validate` passes (run it).
- [ ] Every outcome in the assessment map has a check, and the check matches the outcome.
- [ ] Command checks: run them on the untouched starter (must FAIL) and on `checks/reference/`
  (must PASS). Report both runs.
- [ ] Hidden-task checks: verify script is deterministic; budget/timeout set; the hidden task tests
  the skill rather than the specific example.
- [ ] No cheat from the student report passes.
- [ ] Nothing from `checks/` leaks into `starter/`, `task.md` or `theory.md`.
- [ ] Quiz: one correct answer per question, distractors plausible, explanations present.

## Response format / FAIL procedure

`PASS: ... Checked: <runs>` or `FAIL: N issues`; attribute (usually practice-designer) and append
to the mistakes file.
