#!/bin/bash
# SubagentStop: record a judge's verdict from the agent's final report (fallback path; the primary
# path is judge-handback.sh). Role = leading "Read .claude/agents/<team>/judge-X.md first" of the
# agent's spawn prompt (first user record of its transcript). Verdict = last exact PASS/FAIL line.
# Falls back to the transcript's last assistant text when last_assistant_message is absent.
# pipeline-advance.sh only records votes for judges of the current tier inside a judge phase.
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
  local parsed judge verdict agent_id lines handback
  parsed=$(printf '%s' "$INPUT" | hookio judge_vote)
  IFS='|' read -r judge verdict agent_id lines handback <<< "$parsed"
  [ -n "$judge" ] || return 0
  case "$verdict" in
    PASS|FAIL) ;;
    *) # A transcript that lags behind the hook has no verdict yet; the handback path covers it.
       pl_log event=verdict-unknown judge="$judge" path=subagent_stop agent_id="$agent_id" \
         transcript_lines="$lines" handback_in_transcript="$handback"
       return 0 ;;
  esac
  pl_record_vote "$judge" "$verdict" "$agent_id" subagent_stop transcript_lines="$lines" handback_in_transcript="$handback"
  return 0
}

run_hook "$@"
