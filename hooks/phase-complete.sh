#!/bin/bash
# Stop: validate the pipeline completion gates.
# - No own active pipeline in this checkout -> allow.
# - stop_hook_active=true (we already blocked once this turn) -> allow, so the session never loops.
# - Phase waits on a human (human_wait_phases, e.g. LEARN "learner") -> allow with a reminder.
# - A subagent is still running (background_tasks) -> allow; its result is still to come.
# - Otherwise require: phase=done, each judge round unanimous for the tier, notify run, clean
#   tree, not on a protected branch for issue-linked work, and the process repo rules of
#   lib/pl_process_repo.py (clean, no issue commit on a protected process branch).
# - Cannot evaluate (common.sh did not load, python3 unusable, resolver failure) -> warn and
#   allow (HOOK_KIND=stop): blocking a Stop that nothing can repair only loops.
HOOK_KIND=stop
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
# Set by the last line of common.sh. Without it stop_hook_active cannot be read, so a block here
# would repeat on every Stop: warn and allow.
[ "${PL_COMMON_LOADED:-}" = 1 ] || { echo "WARNING (not blocking): $0: lib/common.sh did not load; the pipeline completion check did not run. Stepan: kill switch, .claude/CLAUDE.md section 7" >&2; exit 0; }

ACTIVE_FLAG=""
block() {
  if [ "$ACTIVE_FLAG" = "True" ] || [ "$ACTIVE_FLAG" = "true" ]; then
    echo "WARNING (not blocking twice): $1" >&2
    exit 0
  fi
  echo "BLOCKED: $1" >&2
  pl_log event=stop-block decision=block
  exit 2
}

main_fn() {
  local tier phase p rounds need res notify issue br
  case "$STATE_STATUS" in
    unreadable)
      # Blocking on a file the session cannot repair would only loop; Stepan inspects it.
      echo "pipeline state unreadable: $STATE_FILE; Stepan inspects it" >&2
      pl_log event=state-unreadable decision=allow
      return 0 ;;
    own:*|done) ;;
    *) return 0 ;;
  esac
  ACTIVE_FLAG=$(printf '%s' "$INPUT" | hookio field stop_hook_active)
  tier=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['tier'])" "$STATE_FILE")
  phase=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['phase'])" "$STATE_FILE")

  for p in $(cfg get human_wait_phases); do
    if [ "$phase" = "$p" ]; then
      echo "Pipeline paused in '$phase' (tier $tier): waiting for the learner." >&2
      return 0
    fi
  done

  # A judge round in flight must not be cut off: Stop waits for nothing while subagents still run.
  local running total
  read -r running total <<< "$(printf '%s' "$INPUT" | hookio bg_running)"
  if [ "$running" -gt 0 ]; then
    echo "$running subagent(s) still running; pipeline at $phase" >&2
    pl_log event=stop-allow:subagents-running decision=allow bg_subagents_running="$running" bg_total="$total"
    return 0
  fi

  [ "$phase" != "done" ] && block "Pipeline not complete. Current phase: $phase. Continue, or ask the learner if you are waiting on him."

  rounds="$(cfg judge_phases "$tier")"
  need="$(cfg judges "$tier")"
  if [ -n "$rounds" ]; then
    res=$(python3 -I - "$STATE_FILE" "$rounds" "$need" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
rounds, need = sys.argv[2].split(), sys.argv[3].split()
votes = d.get('artifacts', {}).get('judge_votes', [])
bad = []
for r in rounds:
    latest = {}
    for v in votes:
        if v.get('round') == r:
            latest[v.get('agent')] = v.get('verdict')
    bad += [r + '/' + j for j in need if latest.get(j) != 'PASS']
print(','.join(bad) if bad else 'OK')
PY
)
    [ "$res" != "OK" ] && block "every judge round needs a unanimous PASS. Not PASS: $res"
  fi

  notify=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1])).get('artifacts',{}).get('notify') or '')" "$STATE_FILE")
  [ -z "$notify" ] && block "notify not run. Run: bash .claude/hooks/pipeline-advance.sh notify"

  cd "$STATE_ROOT"
  [ -n "$(git status --porcelain 2>/dev/null)" ] && block "uncommitted changes exist (including untracked files). Commit first, adding each path by name (git add <path> ...); never git add -A or git add ."

  issue=$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1])).get('issue') or '')" "$STATE_FILE")
  if [ -n "$issue" ]; then
    br=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    for p in $(cfg get protected_branches); do
      [ "$br" = "$p" ] && block "issue #$issue work is on protected branch '$br'. Move it to <type>/$issue-<slug> and open a PR."
    done
  fi

  # Before finish removes the state, so a refusal leaves the task resumable.
  local problems prc=0
  problems=$(python3 -I "$LIB/pl_process_repo.py" stop "$STATE_ROOT" "$issue") || prc=$?
  case "$prc" in
    0) ;;
    2) block "process repo: ${problems//$'\n'/; }" ;;
    # block, not a crash: block allows the second Stop of a turn, so a broken check cannot loop.
    *) block "the process repo check failed (rc $prc); see the error above" ;;
  esac

  # Removed under the state lock; a timeout leaves the done state, which never blocks the next init.
  if ! python3 -I "$LIB/state.py" finish "$STATE_ROOT" >/dev/null; then
    echo "WARNING: the done state was not removed; the next init replaces it." >&2
  fi
  return 0
}

run_hook "$@"
