#!/bin/bash
# PreToolUse (Edit|Write|MultiEdit|NotebookEdit): file-write gate, decided on the target's real path.
#  1. Never written by tools, in any tier: .git paths and the git dir, session transcripts,
#     user-level settings, the pipeline grant file.
#  2. The main checkout's state and core are checked as absolute paths before any checkout mapping,
#     so no worktree layout can re-label them. Core is writable only in an own PIPELINE task in main.
#  3. Otherwise the checkout that owns the file governs: its state files are protected, its core is
#     never writable, .claude/ and plans/ are open, everything else needs its active pipeline.
#  4. LEARN tier: product code is written by the learner; only meta paths and test files are writable.
# The decision code lives in lib/pl_write_gate.py (since #23); this wrapper maps its exit code.
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
  case "$TOOL_NAME" in Edit|Write|MultiEdit|NotebookEdit) ;; *) return 0 ;; esac
  local verdict rc=0
  verdict=$(printf '%s' "$INPUT" | python3 -I "$LIB/pl_write_gate.py" "$STATE_STATUS") || rc=$?
  [ "$rc" = 0 ] && return 0
  [ "$rc" = 2 ] || return "$rc"
  # CPython also exits 2 when it cannot open the script (stdout empty): a verdict needs the \x1f.
  case "$verdict" in *$'\x1f'*) deny "${verdict#*$'\x1f'}" "${verdict%%$'\x1f'*}" ;; esac
  pl_log event=gate-no-verdict rc=2
  return 70 # EX_SOFTWARE: the gate ended without a verdict; run_hook blocks it as a crash
}

run_hook "$@"
