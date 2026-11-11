#!/bin/bash
# SessionStart (no matcher: startup, resume, clear, compact, fork): a session in a linked worktree
# loads no process CLAUDE.md, so it is told where main's copy is, to run the hook probe, and the
# worktree rules. A main-checkout session gets nothing. Any failure prints a short fixed fallback.
HOOK_KIND=observer
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac

# The text uses bash builtins only: it must print when python3 is missing or common.sh stopped early.
# _pl_main is set by common.sh when a linked copy could not forward, and then names main, not the worktree.
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
  # Logged after the text is out, so a hanging python3 cannot hold it back. Best effort: without
  # python3 (common.sh's probe failed) there is no log writer.
  if [ -n "${LIB:-}" ] && command -v python3 >/dev/null 2>&1; then
    python3 -I "$LIB/checkout.py" log event=session-context reason="fallback:$pl_ctx_why" rc="${pl_ctx_rc:-}" \
      hook="${HOOK_NAME:-}" checkout="${STATE_ROOT:-}" source="${SOURCE:-}" >/dev/null 2>&1 || true
  fi
}
PL_CTX_DONE=""
# Why the fallback printed, for its log line; each stage below names itself before it can fail.
pl_ctx_why=common-sh
pl_ctx_rc=""
trap pl_ctx_fallback EXIT

# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
[ "${PL_COMMON_LOADED:-}" = 1 ] || exit 0

# Not run_hook: it maps every observer exit to 0, and a formatter crash must reach the fallback.
# The hook input goes along on stdin ("-"): the session's cwd tells an unaccepted nested worktree from main.
pl_ctx_why=formatter
pl_ctx_out=$(printf '%s' "$INPUT" | python3 -I "$LIB/pl_session_context.py" "$STATE_ROOT" "$MAIN_ROOT" "$SOURCE" \
  "$STATE_STATUS" -) || { pl_ctx_rc=$?; exit 0; }
printf '%s' "$pl_ctx_out"
PL_CTX_DONE=1
if [ "$SOURCE" != cwd ]; then pl_ctx_reason=fallback
elif [ "$STATE_ROOT" != "$MAIN_ROOT" ]; then pl_ctx_reason=linked
elif [ -n "$pl_ctx_out" ]; then pl_ctx_reason=unaccepted-worktree
else pl_ctx_reason=main
fi
pl_log event=session-context reason="$pl_ctx_reason"
exit 0
