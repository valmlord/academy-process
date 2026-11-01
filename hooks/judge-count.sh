#!/bin/bash
# PostToolUse (Agent|Task): synchronous-harness fallback for recording a judge verdict.
# On async harnesses tool_response holds only launch metadata -> UNKNOWN -> silently skipped;
# judge-handback.sh / judge-vote.sh record it when the agent finishes.
HOOK_KIND=observer
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
# Set by the last line of common.sh; an observer never blocks, even when it did not load.
[ "${PL_COMMON_LOADED:-}" = 1 ] || exit 0

main_fn() {
  case "$STATE_STATUS" in own:*) ;; *) return 0 ;; esac
  case "$TOOL_NAME" in Agent|Task) ;; *) return 0 ;; esac
  local parsed judge verdict agent_id phase spawn_out spawn_rc=0
  # An async launch response carries the new agent's id: remember which judge it is, so its
  # handback can be attributed even when no transcript is found.
  IFS='|' read -r judge agent_id <<< "$(printf '%s' "$INPUT" | hookio spawn_info)"
  phase=${STATE_STATUS##*:}
  if [ -n "$judge" ] && [ -n "$agent_id" ]; then
    spawn_out=$(cd "$STATE_ROOT" && JUDGE_HOOK_CALLER=judge-count-hook \
      bash "$CODE_ROOT/.claude/hooks/pipeline-advance.sh" spawn "$phase" "$agent_id" "$judge" 2>&1) || spawn_rc=$?
    # A lost spawn entry leaves a handback without a transcript unattributed, so it is logged.
    if [ "$spawn_rc" != 0 ]; then
      pl_log event=spawn-failed rc="$spawn_rc" error="${spawn_out%%$'\n'*}" judge="$judge" \
        agent_id="$agent_id" round="$phase"
    fi
  fi
  parsed=$(printf '%s' "$INPUT" | hookio judge_vote_post)
  judge="${parsed%%|*}"
  verdict="${parsed#*|}"
  [ -n "$judge" ] || return 0
  case "$verdict" in PASS|FAIL) ;; *) return 0 ;; esac
  pl_record_vote "$judge" "$verdict" "" post_tool_use
  return 0
}

run_hook "$@"
