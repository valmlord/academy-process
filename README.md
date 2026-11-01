# academy-process

Agent process files of valmlord/academy: orchestrator instructions, agents, feedback, pipeline hooks and their self-test.
The repository lives at `<academy checkout>/.claude/`; the product repository ignores that directory as a whole.
New device: `gh repo clone valmlord/academy-process <academy checkout>/.claude`.
Local checks: `PL_CHECK_PYTHON=/opt/homebrew/bin/python3.12 bash tests/pipeline/check.sh <venv dir>` (mypy 1.20.2 needs Python 3.10+).
Commits add paths by name (`git add <path> ...`), never `git add -A`: the grant and local settings live in this directory.
Changes reach `main` only through pull requests; Stepan merges them.
