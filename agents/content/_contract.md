# Lesson contract (summary for content agents)

The authoritative definition is `packages/lesson-schema/src/schema.ts` and ADR-0001
(`docs/adr/0001-lesson-format.md`). `pnpm content:validate` enforces it in CI. Summary:

```
course/<course-id>/course.yaml                 id, title, description, modules[] (dir names, in order)
course/<course-id>/<NN-module>/module.yaml     id, title, summary, outcomes[], status, lessons[] (dir names, in order)
course/<course-id>/<NN-module>/<NN-lesson>/
  lesson.yaml     id, title, type, outcomes[], estimatedMinutes, status, sources[], workspace?, checks[]
  theory.md       short theory, Russian; every factual claim about a tool backed by a source
  task.md         what the learner must do and what "done" means; visible to the learner
  starter/        files copied into the learner's workspace (visible)
  checks/         hidden: grader scripts, hidden tasks, rubrics, bug answer keys (NEVER copied to starter)
  quiz.yaml       for quiz checks
```

Lesson `type`: theory | quiz | artifact | agent-eval | bug-hunt | project.

Check `kind`:
- `quiz` questions with options and the correct answer (`file: quiz.yaml`, `passScore`).
- `command` shell command run in the workspace container, exit 0 = pass (`run`, `timeoutSec`).
- `rubric` AI mentor grades artifacts against `checks/rubric.md` (`artifacts[]` globs, `passScore`).
- `hidden-task` an agent runs headless in a fresh copy of the learner's workspace with a task the
  learner never saw; `verify` script decides (`task`, `verify`, `timeoutSec`, `budgetUsd`).
- `bug-hunt` learner reports bugs found in the starter; matched against `checks/bugs.yaml` (`minFound`).

`status`: planned | draft | ready. Only `ready` lessons appear in the learner UI.
`sources[]`: `{ title, url, checkedAt: YYYY-MM-DD }`. Required for `ready` lessons with theory.
