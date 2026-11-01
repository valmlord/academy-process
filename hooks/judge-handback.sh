#!/bin/bash
# PreToolUse (SubagentHandback): primary path for recording a judge's verdict. The report is the
# handback call's tool_input.message, so no transcript flush is needed for the verdict; the role
# comes from the subagent's spawn prompt (first transcript record) or the judge spawn map.
# Observer: it never blocks, because a blocked handback would trap the judge.
HOOK_KIND=observer
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
# Set by the last line of common.sh; an observer never blocks, even when it did not load.
[ "${PL_COMMON_LOADED:-}" = 1 ] || exit 0

main_fn() {
  [ "$TOOL_NAME" = "SubagentHandback" ] || return 0
  local agent_id parsed outcome judge verdict role_source kind
  agent_id=$(printf '%s' "$INPUT" | hookio field agent_id)
  [ -n "$agent_id" ] || return 0
  case "$STATE_STATUS" in
    own:*) ;;
    *) pl_log event=vote-ignored:no-state path=handback; return 0 ;;
  esac
  parsed=$(printf '%s' "$INPUT" | hookio handback_vote "$STATE_FILE")
  IFS='|' read -r outcome judge verdict agent_id role_source kind <<< "$parsed"
  if [ "$outcome" != vote ]; then
    pl_log event="$outcome" judge="$judge" verdict="$verdict" path=handback agent_id="$agent_id" \
      role_source="$role_source" transcript_kind="$kind"
    return 0
  fi
  pl_record_vote "$judge" "$verdict" "$agent_id" handback role_source="$role_source" transcript_kind="$kind"
  return 0
}

run_hook "$@"
