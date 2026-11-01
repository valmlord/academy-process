#!/bin/bash
# PreToolUse (any): warn if the pipeline has been stuck at a non-done phase for too long.
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
  local state_path result phase tier age_min marker limit should age
  state_path=$(cygpath -w "$STATE_FILE" 2>/dev/null || echo "$STATE_FILE")
  # The marker is per checkout (hash of its root), so a stuck worktree does not silence main.
  # Inactivity comes from state.last_activity, the same rule as the TTL in init.
  result=$(python3 -I - "$state_path" "$STATE_ROOT" "${TMPDIR:-/tmp}" "$LIB" <<'PY'
import hashlib, json, os, time, sys
sys.path.append(sys.argv[4])
import state
d = json.load(open(sys.argv[1]))
last_ts = state.last_activity(d)
age_min = (time.time() - last_ts) / 60 if last_ts else 999
marker = os.path.join(sys.argv[3], 'pipeline_watchdog_' + hashlib.sha1(sys.argv[2].encode('utf-8')).hexdigest()[:12])
print('%s|%s|%.0f|%s' % (d.get('phase', ''), d.get('tier', '?'), age_min, marker))
PY
)
  [ -n "$result" ] || return 0
  IFS='|' read -r phase tier age_min marker <<< "$result"
  limit=$(cfg get watchdog_minutes)
  [ "$age_min" -gt "${limit:-30}" ] || return 0
  echo "WARNING: Pipeline interrupted - phase '$phase' (tier=$tier) stuck for ${age_min} min. Continue it, or pipeline-advance.sh pause it (resume <issue> later)." >&2
  should=1
  if [ -f "$marker" ]; then
    age=$(python3 -I -c "import os,sys,time; print(int(time.time()-os.path.getmtime(sys.argv[1])))" "$marker")
    [ "$age" -lt 900 ] && should=0
  fi
  if [ "$should" -eq 1 ] && [ -f "$CODE_ROOT/.claude/hooks/notify.sh" ]; then
    touch "$marker"
    pl_log event=watchdog-notify
    echo "Pipeline stuck: phase=$phase tier=$tier age=${age_min}min" | bash "$CODE_ROOT/.claude/hooks/notify.sh" "$tier" >/dev/null 2>&1 || true
  fi
  return 0
}

run_hook "$@"
