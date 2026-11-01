# ADR-0004: Development process as in production

- Status: Proposed
- Date: 2026-10-27

## Decision
- Any work starts with a GitHub issue (templates: feature, bug, LEARN, module/lesson, ADR).
- Branch `<type>/<issue>-<slug>`, conventional commits referencing the issue, a PR with `Closes #N`.
- `main` is protected: merge only through a PR with green CI (squash).
- CI: lint, typecheck, unit, build, content:validate, pipeline self-test, `docker compose up --wait`;
  e2e is added together with web.
- PR hygiene in CI: title format, issue reference, branch name.
- The agent pipeline (`.claude/`) is mandatory for any task; tiers and phases are in `.claude/pipeline.json`.
- Decisions that are costly to change are recorded as ADRs.
- Releases: semver tags and a CHANGELOG (RELEASE task).

Pipeline mechanics: see ADR-0005.

Amended by #86: the pipeline self-test runs in the CI of the process repository
(`valmlord/academy-process`, `tests/pipeline/check.sh`), not in the product's CI.

## Consequences
- Branch protection for private repositories on GitHub's free plan may be unavailable. In that case
  the rule is held by the pipeline hooks (no work on main) and by discipline.
