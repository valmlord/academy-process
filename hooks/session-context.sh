#!/bin/bash
# SessionStart (no matcher: startup, resume, clear, compact, fork): a session in a linked worktree
# loads no process CLAUDE.md, so it is told where main's copy is, to run the hook probe, and the
# worktree rules. A main-checkout session gets nothing. Any failure prints a short fixed fallback.
HOOK_KIND=observer
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac

# Bash builtins only: it must work when python3 is missing or common.sh stopped early. _pl_main is
# set by common.sh when a linked copy could not forward, and then names main, not the worktree.
pl_ctx_fallback() {
  [ "${PL_CTX_DONE:-}" = 1 ] && return 0
  local root="${_pl_main:-${CODE_ROOT:-}}" where
  root=${root//[[:cntrl:]]/}
  # Backslashes first: escaping the quotes first would double the backslashes it adds.
  root=${root//\\/\\\\}
  root=${root//\"/\\\"}
  if [ -n "$root" ]; then
    where="If your working directory is not $root, Read $root/.claude/CLAUDE.md first"
  else
    where="If your working directory is not the main checkout, Read the main checkout's .claude/CLAUDE.md first"
  fi
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' \
    "academy pipeline: the session-context hook failed. $where and run the hook probe it describes; tell Stepan the hook failed."
}
PL_CTX_DONE=""
trap pl_ctx_fallback EXIT

# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
[ "${PL_COMMON_LOADED:-}" = 1 ] || exit 0

# Not run_hook: it maps every observer exit to 0, and a formatter crash must reach the fallback.
pl_ctx_out=$(python3 -I "$LIB/pl_session_context.py" "$STATE_ROOT" "$MAIN_ROOT" "$SOURCE" "$STATE_STATUS") || exit 0
printf '%s' "$pl_ctx_out"
PL_CTX_DONE=1
if [ "$SOURCE" != cwd ]; then pl_ctx_reason=fallback
elif [ "$STATE_ROOT" = "$MAIN_ROOT" ]; then pl_ctx_reason=main
else pl_ctx_reason=linked
fi
pl_log event=session-context reason="$pl_ctx_reason"
exit 0
