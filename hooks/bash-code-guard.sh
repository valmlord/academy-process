#!/bin/bash
# PreToolUse (Bash): string heuristics for shell writes the write gate cannot see. A guardrail
# against mistakes, not a sandbox: `python3 -c`, variables and relative `cd` evade it (ADR-0005).
#  1. Pipeline integrity: no tool-issued command may name the state file or forge a judge vote.
#  2. Never, in any tier: core.hooksPath, and a write verb aimed at a .git path, session
#     transcripts, the grant file or user-level settings.
#  3. Pipeline core: shell writes only from the main checkout in an own PIPELINE task. Core is
#     named by the core path strings (.claude/hooks with or without a trailing slash,
#     .claude/pipeline.json, .claude/settings*) or by the .claude directory token: .claude with or
#     without a trailing slash, .claude/ followed by a character that cannot continue a name, or a
#     glob or brace character in the first component after .claude/. `git checkout` with any
#     arguments (a ref included) counts as a write verb. Quoting or backslashes inside a name, ./
#     and .. path segments (.claude/./hooks, .claude/agents/../hooks) and variables evade it
#     (ADR-0005 item 7).
#  4. LEARN tier: no shell writes into product code dirs, for every consulted checkout's state.
# The decision code for 2-4 lives in lib/pl_shell_guard.py (since #23); this wrapper keeps the two
# string checks of 1 and maps the script's exit code.
HOOK_KIND=gate
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
# Set by the last line of common.sh; a source that stopped early would make this hook exit 127,
# which does not block.
[ "${PL_COMMON_LOADED:-}" = 1 ] || { echo "BLOCKED: $0: lib/common.sh did not load; pipeline gates cannot run. Stepan: kill switch, .claude/CLAUDE.md section 7" >&2; exit 2; }

deny() { # deny <message> <log reason>
  echo "BLOCKED: $1" >&2
  pl_log event=block decision=block reason="$2"
  exit 2
}

main_fn() {
  [ "$TOOL_NAME" = "Bash" ] || return 0
  local cmd verdict rc=0
  cmd=$(printf '%s' "$INPUT" | hookio field tool_input.command)

  if printf '%s' "$cmd" | grep -q "pipeline_state"; then
    deny "the pipeline state file is managed only by pipeline-advance.sh (use: pipeline-advance.sh status)." "state-string"
  fi
  if printf '%s' "$cmd" | grep -q "JUDGE_HOOK_CALLER"; then
    deny "judge votes are recorded only by the judge hooks from spawned judge agents." "judge-caller-string"
  fi

  verdict=$(printf '%s' "$INPUT" | python3 -I "$LIB/pl_shell_guard.py" "$STATE_ROOT" "$MAIN_ROOT" "$STATE_STATUS") || rc=$?
  [ "$rc" = 0 ] && return 0
  [ "$rc" = 2 ] || return "$rc"
  # CPython also exits 2 when it cannot open the script (stdout empty): a verdict needs the \x1f.
  case "$verdict" in *$'\x1f'*) deny "${verdict#*$'\x1f'}" "${verdict%%$'\x1f'*}" ;; esac
  pl_log event=gate-no-verdict rc=2
  return 70 # EX_SOFTWARE: the gate ended without a verdict; run_hook blocks it as a crash
}

run_hook "$@"
