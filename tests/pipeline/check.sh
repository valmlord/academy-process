#!/bin/bash
# Every check of the process repo, the same locally and in its CI:
#   bash tests/pipeline/check.sh <venv dir>
# Locally: PL_CHECK_PYTHON=/opt/homebrew/bin/python3.12 (mypy 1.20.2 needs Python 3.10+ to install).
# Steps: shellcheck, py_compile, mypy --strict for the hooks' 3.9 runtime, the self-test. Each prints
# OK <step> or FAIL <step>; all run, and the exit code is 1 when any failed.
set -uo pipefail

if [ $# -ne 1 ] || [ -z "$1" ]; then
  echo "Usage: bash tests/pipeline/check.sh <venv dir>" >&2
  exit 2
fi
case $1 in /*) VENV=$1 ;; *) VENV="$PWD/$1" ;; esac
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
REQUIREMENTS=tests/pipeline/requirements-check.txt
SETUP_HINT="mypy 1.20.2 needs Python 3.10+, set PL_CHECK_PYTHON (on this Mac /opt/homebrew/bin/python3.12)"

TMP_ROOT=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP_ROOT"' EXIT

# A venv counts as set up only with every tool installed: a retry after a failed setup (a venv
# made by Python 3.9, where the mypy pin has no wheel) must set it up again, not skip to the steps.
venv_ready() {
  [ -x "$VENV/bin/python" ] && [ -x "$VENV/bin/shellcheck" ] && "$VENV/bin/python" -m mypy --version >/dev/null 2>&1
}

if ! venv_ready; then
  # --clear empties the directory, so it is used only on something that already is a venv.
  if [ -e "$VENV" ] && [ ! -f "$VENV/pyvenv.cfg" ] && [ -n "$(ls -A "$VENV" 2>/dev/null)" ]; then
    echo "FAIL setup: $VENV exists and is not a venv; pass a new or venv directory"
    exit 1
  fi
  if ! "${PL_CHECK_PYTHON:-python3}" -m venv --clear "$VENV" \
    || ! "$VENV/bin/pip" install -q --disable-pip-version-check --no-deps --only-binary :all: -r "$REQUIREMENTS"; then
    echo "FAIL setup: pip install failed; $SETUP_HINT"
    exit 1
  fi
fi

FAILED=0
step() { # step <name> <command...>
  local name="$1"
  shift
  if "$@"; then echo "OK $name"; else echo "FAIL $name"; FAILED=1; fi
}
compile_hooks() { PYTHONPYCACHEPREFIX="$TMP_ROOT/pycache" python3 -m py_compile hooks/lib/*.py; }
type_check() {
  MYPYPATH=hooks/lib "$VENV/bin/python" -m mypy --strict --python-version 3.9 \
    --cache-dir "$TMP_ROOT/mypy-cache" hooks/lib/*.py
}

step shellcheck "$VENV/bin/shellcheck" -S error hooks/*.sh hooks/lib/*.sh tests/pipeline/*.sh
# The system python3: the interpreter the hooks run on.
step py_compile compile_hooks
step mypy type_check
step self-test bash tests/pipeline/run.sh
exit "$FAILED"
