#!/bin/bash
# Pipeline state machine: tracks phase transitions per tier.
# Tiers, phases and judges come from .claude/pipeline.json (via lib/cfg.py), never hardcoded here.
#
# Usage:
#   pipeline-advance.sh init <TIER> [issue-number]     start a pipeline (issue required for most tiers)
#   pipeline-advance.sh <phase>                         advance to the next phase
#   pipeline-advance.sh compound skip "reason"          skip the compound step
#   pipeline-advance.sh pr <url>                        record the opened PR and advance
#   pipeline-advance.sh pr skip "reason"                no remote yet: record why, advance
#   pipeline-advance.sh notify                          run notify hook and advance
#   pipeline-advance.sh status                          print state (parked ones on stderr)
#   pipeline-advance.sh pause                           park the active state, free the checkout
#   pipeline-advance.sh resume <issue|key>              restore a parked state on its own branch
#   pipeline-advance.sh parked                          list parked states
#   pipeline-advance.sh worktrees [<path>]              report unsaved process work in linked worktrees
# Judge votes and the judge spawn map are recorded ONLY by the judge hooks (JUDGE_HOOK_CALLER):
#   pipeline-advance.sh <judge_phase> <judge> <PASS|FAIL> [agent_id] [path]
#   pipeline-advance.sh spawn <judge_phase> <agent_id> <judge>
#
# State: .claude/pipeline_state.json of the checkout that contains the current directory (a
# registered worktree, else the main checkout). Run the main checkout's copy of this script; from a
# worktree: bash "$(git rev-parse --path-format=absolute --git-common-dir)/../.claude/hooks/pipeline-advance.sh"
HOOK_KIND=cli
case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
# An inherited value must not fake a load.
unset PL_COMMON_LOADED
# shellcheck source=lib/common.sh
source "$HOOK_DIR/lib/common.sh"
# Set by the last line of common.sh; a source that stopped early must not run half-defined.
[ "${PL_COMMON_LOADED:-}" = 1 ] || { echo "ERROR: lib/common.sh did not load" >&2; exit 1; }

set -euo pipefail
SCRIPT_DIR="$CODE_ROOT/.claude/hooks"
STATE_FILE=$(cygpath -w "$STATE_FILE" 2>/dev/null || echo "$STATE_FILE")
REPO_DIR="$STATE_ROOT"
PHASE="${1:?Usage: pipeline-advance.sh <phase> [args...]}"
shift

# The script comes on stdin, never through a temp file: BSD mktemp keeps a template without
# trailing X's literal, so concurrent calls collided on one file name and lost votes (#23).
# Shell values reach the script only as arguments, never inside its source text.
py_run() { python3 -I - "$@"; }

read_state() { # read_state <key>
  py_run "$STATE_FILE" "$1" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
v = d.get(sys.argv[2], '')
print('' if v is None else v)
PY
}
read_state_json() {
  py_run "$STATE_FILE" <<'PY'
import json, sys
print(json.dumps(json.load(open(sys.argv[1])), indent=2, ensure_ascii=False))
PY
}

# Every state write is one locked transaction in lib/state.py.
state_op() { python3 -I "$LIB/state.py" "$1" "$STATE_ROOT" "${@:2}"; }
set_artifact() { state_op set_artifact "$1" "$2" >/dev/null; }

# Unanimity for the CURRENT judge round. Prints OK / FAIL:<..> NOTVOTED:<..>
check_judges_unanimous() {
  py_run "$STATE_FILE" "$1" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1]))
cur=d.get('phase','')
need=sys.argv[2].split()
latest={}
for v in d.get('artifacts',{}).get('judge_votes',[]):
    if v.get('round')==cur:
        latest[v.get('agent')]=v.get('verdict')
fails=[j for j in need if latest.get(j)=='FAIL']
notvoted=[j for j in need if latest.get(j) not in ('PASS','FAIL')]
if not fails and not notvoted:
    print('OK')
else:
    parts=[]
    if fails: parts.append('FAIL:'+','.join(fails))
    if notvoted: parts.append('NOTVOTED:'+','.join(notvoted))
    print(' '.join(parts))
PYEOF
}

# A function, not a heredoc inside $(...): bash 3.2 mis-parses a heredoc in a command substitution
# when its body has unbalanced quotes or parentheses.
notify_body() {
  py_run "$STATE_FILE" <<'PYEOF'
import json,sys,time
d = json.load(open(sys.argv[1]))
lines = ['Tier: %s  Issue: #%s' % (d.get('tier','?'), d.get('issue') or '-')]
st = d.get('session_ts', 0)
lines.append('Total: %.1f min' % ((time.time()-st)/60 if st else 0))
a = d.get('artifacts',{})
if a.get('pr'): lines.append('PR: %s' % a['pr'])
votes = a.get('judge_votes',[])
if votes:
    lines.append('Judge verdicts:')
    for v in votes:
        lines.append('  [%s] %s: %s' % (v.get('round'), v.get('agent'), v.get('verdict')))
print('\n'.join(lines))
PYEOF
}

unreadable_state() {
  echo "ERROR: state file unreadable: $STATE_FILE. Stepan inspects it, then moves it aside by hand:" >&2
  echo "  mv \"$STATE_FILE\" \"$STATE_FILE.broken\"" >&2
  exit 1
}

# Parked states and a foreign slot are reported on stderr, so stdout stays pure JSON for consumers.
report_parked() {
  local line
  state_op parked | while IFS= read -r line; do echo "Parked here: $line" >&2; done
}

# Unsaved process work in linked worktrees, on stderr like the parked list. Best effort: status
# itself never fails on it, so a failed report is one warning line.
report_worktrees() {
  local out rc=0
  out=$(python3 -I "$LIB/pl_process_worktree.py" report) || rc=$?
  case "$rc" in
    0|1) [ -z "$out" ] || printf '%s\n' "$out" >&2 ;;
    *) echo "WARNING: worktree report failed (rc $rc)" >&2 ;;
  esac
}

# ---------------------------------------------------------------- STATUS
if [ "$PHASE" = "status" ]; then
  case "$STATE_STATUS" in
    own:*|done) read_state_json ;;
    foreign:*)
      echo "No active pipeline."
      echo "Foreign state in slot: #$(read_state issue) $(read_state tier)/$(read_state phase) (started on $(read_state branch_at_init); pause parks it)" >&2 ;;
    unreadable) unreadable_state ;;
    *) echo "No active pipeline." ;;
  esac
  report_parked
  report_worktrees
  exit 0
fi

# ---------------------------------------------------------------- PAUSE / RESUME / PARKED
if [ "$PHASE" = "pause" ]; then
  state_op park pause "$CODE_ROOT" "$GITDIR" "$BRANCH"
  exit 0
fi
if [ "$PHASE" = "resume" ]; then
  state_op resume "${1:?Usage: pipeline-advance.sh resume <issue|key>}" "$CODE_ROOT" "$GITDIR" "$BRANCH"
  exit 0
fi
if [ "$PHASE" = "parked" ]; then
  state_op parked
  exit 0
fi
# The sync gate before Stepan removes a process worktree: exit 0 only when nothing would be lost.
if [ "$PHASE" = "worktrees" ]; then
  WORKTREES_RC=0
  python3 -I "$LIB/pl_process_worktree.py" report ${1:+"$1"} || WORKTREES_RC=$?
  exit "$WORKTREES_RC"
fi

# ---------------------------------------------------------------- INIT
if [ "$PHASE" = "init" ]; then
  TIER="${1:?Usage: pipeline-advance.sh init <TIER> [issue-number]}"
  ISSUE="${2:-}"
  ISSUE="${ISSUE#\#}"
  if ! cfg tiers | tr ' ' '\n' | grep -qx "$TIER"; then
    echo "ERROR: Unknown tier: $TIER. Known: $(cfg tiers)" >&2; exit 1
  fi
  if [ "$(cfg tier_flag "$TIER" requires_issue)" = "1" ]; then
    if ! [[ "$ISSUE" =~ ^[0-9]+$ ]]; then
      echo "ERROR: tier $TIER requires a GitHub issue number: pipeline-advance.sh init $TIER <issue>" >&2
      echo "No issue yet? Create one first (gh issue create --template ...)." >&2
      exit 1
    fi
  fi
  state_op init "$TIER" "$ISSUE" "$BRANCH" "$GITDIR" "$CODE_ROOT" >/dev/null
  echo "Pipeline initialized: tier=$TIER issue=${ISSUE:-none}"
  echo "Phases: $(cfg phases "$TIER")"
  if [ -n "$ISSUE" ]; then
    echo "Work on a branch named <type>/$ISSUE-<slug> (e.g. feat/$ISSUE-lesson-page). Never commit to main."
  fi
  echo ""
  echo "REMINDER: read .claude/feedback/orchestrator_mistakes.md and the role mistake files before starting."
  exit 0
fi

case "$STATE_STATUS" in
  own:*|done) ;;
  foreign:*) echo "ERROR: the state here belongs to another checkout or branch ($STATE_STATUS). pause parks it; then init or resume." >&2; exit 1 ;;
  unreadable) unreadable_state ;;
  *) echo "ERROR: No pipeline state. Run: pipeline-advance.sh init <TIER> <issue>" >&2; exit 1 ;;
esac

TIER=$(read_state tier)
CURRENT=$(read_state phase)
ISSUE=$(read_state issue)
ORDER="$(cfg phases "$TIER")"
JUDGES="$(cfg judges "$TIER")"

# ---------------------------------------------------------------- JUDGE VOTE
if [[ "$PHASE" == judge_* ]] && [ "$CURRENT" = "$PHASE" ] && [ $# -ge 2 ]; then
  AGENT="$1"; VERDICT="$2"
  if [ "${JUDGE_HOOK_CALLER:-}" != "judge-count-hook" ]; then
    echo "REJECTED: Inline judge votes are not allowed. Spawn the judges for tier $TIER in ONE message:" >&2
    for j in $JUDGES; do
      F=$(cfg all_judges | tr ' ' '\n' | grep "^$j=" | cut -d= -f2)
      echo "  Agent(prompt=\"Read .claude/agents/<team>/$F first. Then review: ...\")" >&2
    done
    exit 1
  fi
  if ! echo " $JUDGES " | grep -q " $AGENT "; then
    echo "IGNORED: judge '$AGENT' is not part of tier $TIER (judges: $JUDGES)." >&2
    exit 0
  fi
  case "$VERDICT" in PASS|FAIL) ;; *) echo "IGNORED: verdict '$VERDICT'" >&2; exit 0 ;; esac
  # Output and rc are taken apart: inside a [ ] argument a failed write (lock timeout 75, phase
  # race 3, unreadable state 1) would read as success.
  VOTE_RESULT=$(state_op vote "$PHASE" "$AGENT" "$VERDICT" "${3:-}" "${4:-}") || exit $?
  if [ "$VOTE_RESULT" = "vote-dup" ]; then
    echo "Duplicate vote ignored ($PHASE: $AGENT, agent ${3:-?} already voted this round)."
    exit 0
  fi
  echo "Judge recorded ($PHASE: $AGENT=$VERDICT). Round status: $(check_judges_unanimous "$JUDGES")"
  exit 0
fi

# ---------------------------------------------------------------- SPAWN map (judge-count hook)
# spawn <round> <agent_id> <judge>: remember which judge an agent id is, for a handback whose
# transcript cannot be found.
if [ "$PHASE" = "spawn" ]; then
  if [ "${JUDGE_HOOK_CALLER:-}" != "judge-count-hook" ]; then
    echo "REJECTED: the spawn map is written only by the judge-count hook." >&2; exit 1
  fi
  if ! echo " $JUDGES " | grep -q " ${3:?Usage: pipeline-advance.sh spawn <round> <agent_id> <judge>} "; then
    echo "IGNORED: judge '$3' is not part of tier $TIER (judges: $JUDGES)." >&2; exit 0
  fi
  state_op record_spawn "$1" "$2" "$3"
  exit 0
fi

# ---------------------------------------------------------------- COMPOUND skip
if [ "$PHASE" = "compound" ] && [ "${1:-}" = "skip" ]; then
  set_artifact compound_skip "${2:-no reason given}"
fi

# ---------------------------------------------------------------- PR gate (commit -> pr)
if [ "$PHASE" = "pr" ]; then
  ARG="${1:-}"
  if [ "$ARG" = "skip" ]; then
    set_artifact pr "skipped: ${2:-no reason given}"
    echo "WARNING: PR skipped (${2:-no reason}). Open it as soon as the remote exists." >&2
  elif [[ "$ARG" =~ ^https?:// ]]; then
    set_artifact pr "$ARG"
  else
    echo "ERROR: Usage: pipeline-advance.sh pr <pr-url> | pr skip \"reason\"" >&2; exit 1
  fi
  if [ -n "$ISSUE" ]; then
    BR=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
    for pb in $(cfg get protected_branches); do
      if [ "$BR" = "$pb" ]; then
        echo "BLOCKED: you are on protected branch '$BR'. Work happens on <type>/$ISSUE-<slug>, merged via PR." >&2; exit 1
      fi
    done
    if [ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)" ]; then
      echo "BLOCKED: uncommitted changes. Commit first, adding each path by name (git add <path> ...); never git add -A or git add ." >&2; exit 1
    fi
    # The issue reference, a commit for the issue in at least one repository, and the process repo
    # at .claude/ (clean, nothing for the issue on a protected branch): lib/pl_process_repo.py.
    PROC_RC=0
    PROC_OUT=$(python3 -I "$LIB/pl_process_repo.py" pr "$REPO_DIR" "$ISSUE") || PROC_RC=$?
    if [ "$PROC_RC" = 2 ]; then
      while IFS= read -r problem; do echo "BLOCKED: $problem" >&2; done <<< "$PROC_OUT"
      exit 1
    elif [ "$PROC_RC" != 0 ]; then
      echo "ERROR: the process repo check failed (rc $PROC_RC); see the error above" >&2; exit 1
    fi
  fi
fi

# ---------------------------------------------------------------- NOTIFY
if [ "$PHASE" = "notify" ]; then
  NOTIFY_BODY=$(notify_body)
  if [ -f "$SCRIPT_DIR/notify.sh" ]; then
    echo "$NOTIFY_BODY" | bash "$SCRIPT_DIR/notify.sh" "$TIER" || echo "WARNING: notify hook failed (non-fatal)" >&2
  fi
  set_artifact notify "$(date +%Y-%m-%dT%H:%M:%S)"
fi

# ---------------------------------------------------------------- Phase validation
validate_advance() {
  local order_arr=($ORDER)
  local cur_idx=-1 next_idx=-1
  for i in "${!order_arr[@]}"; do
    [ "${order_arr[$i]}" = "$CURRENT" ] && cur_idx=$i
    [ "${order_arr[$i]}" = "$PHASE" ] && next_idx=$i
  done
  if [ "$next_idx" -eq -1 ]; then echo "ERROR: Phase '$PHASE' not valid for tier $TIER ($ORDER)" >&2; exit 1; fi
  if [ "$next_idx" -le "$cur_idx" ]; then echo "ERROR: Cannot go back from '$CURRENT' to '$PHASE' (tier=$TIER)" >&2; exit 1; fi
  if [ "$next_idx" -gt $((cur_idx + 1)) ]; then echo "ERROR: Cannot skip from '$CURRENT' to '$PHASE'. Next expected: '${order_arr[$((cur_idx + 1))]}' (tier=$TIER)" >&2; exit 1; fi
}
validate_advance

# Cannot leave a judge phase without a unanimous PASS in that round.
if [[ "$CURRENT" == judge_* ]]; then
  UNAN=$(check_judges_unanimous "$JUDGES")
  if [ "$UNAN" != "OK" ]; then
    echo "BLOCKED: cannot leave '$CURRENT': need a unanimous PASS from [$JUDGES]. Status: $UNAN" >&2
    echo "  FAIL:<judges>     = real issue; the judge wrote it to the responsible role's mistakes file. Re-spawn that role and re-judge." >&2
    echo "  NOTVOTED:<judges> = verdict not recorded yet (still running or no PASS/FAIL line). Wait or re-spawn. Not a FAIL." >&2
    exit 1
  fi
fi

state_op advance "$CURRENT" "$PHASE" >/dev/null
echo "Advanced: $CURRENT -> $PHASE (tier=$TIER, issue=#${ISSUE:-none})"
