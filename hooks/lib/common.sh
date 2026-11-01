# shellcheck shell=bash
# Sourced first by every hook script and by pipeline-advance.sh:
#   HOOK_KIND=gate|observer|cli|stop
#   case $0 in */*) HOOK_DIR=${0%/*} ;; *) HOOK_DIR=. ;; esac
#   unset PL_COMMON_LOADED
#   source "$HOOK_DIR/lib/common.sh"
#   [ "${PL_COMMON_LOADED:-}" = 1 ] || { <fail closed, quiet or with exit 1, as below>; }
# Gates fail closed (exit 2), observers fail quiet (exit 0), the CLI fails with exit 1. The Stop
# gate (stop) warns and allows when it cannot evaluate: a Stop block nothing can repair only loops.
# Everything up to the python3 probe uses bash builtins only, so an empty PATH or a missing
# python3 still ends in a clear message instead of a silent non-blocking error.

case "${HOOK_KIND:-}" in observer|cli|stop) ;; *) HOOK_KIND=gate ;; esac
HOOK_NAME=${0##*/}
PL_FORWARDED=false
[ -n "${PIPELINE_HOOK_FORWARDED:-}" ] && PL_FORWARDED=true

pl_fail() {
  case "$HOOK_KIND" in
    gate) echo "BLOCKED: $1" >&2; exit 2 ;;
    cli) echo "ERROR: $1" >&2; exit 1 ;;
    stop) echo "WARNING (not blocking): $1" >&2; exit 0 ;;
    *) exit 0 ;;
  esac
}

# Code always comes from this file's own location, never from cwd, the state or the environment.
CODE_ROOT=$(cd -P "${BASH_SOURCE[0]%/*}/../../.." 2>/dev/null && pwd -P) || CODE_ROOT=""
[ -n "$CODE_ROOT" ] || pl_fail "$HOOK_NAME cannot locate its own checkout"
LIB="$CODE_ROOT/.claude/hooks/lib"

# A copy inside a linked worktree hands over to the main checkout's script of the same name: a
# session started in a worktree runs that worktree's hook wiring, but main's code must decide.
if [ -f "$CODE_ROOT/.git" ]; then
  _pl_line=""; _pl_common=""; _pl_main=""
  IFS= read -r _pl_line < "$CODE_ROOT/.git" || true
  _pl_gitdir=${_pl_line#gitdir: }
  case $_pl_gitdir in /*) ;; *) _pl_gitdir="$CODE_ROOT/$_pl_gitdir" ;; esac
  if [ -f "$_pl_gitdir/commondir" ]; then
    IFS= read -r _pl_common < "$_pl_gitdir/commondir" || true
    case $_pl_common in /*) ;; ?*) _pl_common="$_pl_gitdir/$_pl_common" ;; esac
  fi
  [ -n "$_pl_common" ] && { _pl_main=$(cd -P "$_pl_common/.." 2>/dev/null && pwd -P) || _pl_main=""; }
  if [ "$HOOK_KIND" = cli ]; then
    pl_fail "run the main checkout's copy: bash \"${_pl_main:-<main checkout>}/.claude/hooks/$HOOK_NAME\""
  fi
  if [ -n "$_pl_main" ] && [ -d "$_pl_main/.git" ] && [ -f "$_pl_main/.claude/hooks/$HOOK_NAME" ]; then
    PIPELINE_HOOK_FORWARDED=1 exec /bin/bash "$_pl_main/.claude/hooks/$HOOK_NAME" "$@"
  fi
  pl_fail "this session runs hooks from a linked worktree ($CODE_ROOT) and the main checkout's $HOOK_NAME was not found; start the session in the main checkout"
fi

if ! command -v python3 >/dev/null 2>&1 \
  || ! python3 -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
  pl_fail "python3 not found or unusable; pipeline gates cannot run. Fix python3, or Stepan sets disableAllHooks in .claude/settings.local.json by hand."
fi

# Hook input is read exactly once. A CLI's stdin may be a terminal, so it is never read.
INPUT=""
[ "$HOOK_KIND" = cli ] || IFS= read -r -d '' INPUT || true

CTX=$(printf '%s' "$INPUT" | python3 -I "$LIB/checkout.py" context "$HOOK_NAME" "$PL_FORWARDED")
CTX_RC=$?
STATE_ROOT=""; SOURCE=""; GITDIR=""; BRANCH=""; MAIN_ROOT=""; TOOL_NAME=""; STATE_STATUS=""
IFS=$'\x1f' read -r STATE_ROOT SOURCE GITDIR BRANCH MAIN_ROOT TOOL_NAME STATE_STATUS <<< "$CTX" || true
case $STATE_ROOT in /*) ;; *) STATE_ROOT="" ;; esac
if [ "$CTX_RC" != 0 ] || [ -z "$STATE_ROOT" ] || [ ! -d "$STATE_ROOT" ] || [ -z "$STATE_STATUS" ]; then
  python3 -I "$LIB/checkout.py" log event=resolver-failed hook="$HOOK_NAME" rc="$CTX_RC" >/dev/null 2>&1 || true
  pl_fail "pipeline resolver failed (rc=$CTX_RC); see .git/pipeline-hooks.log"
fi
STATE_FILE="$STATE_ROOT/.claude/pipeline_state.json"

cfg()    { python3 -I "$LIB/cfg.py" "$@"; }
hookio() { python3 -I "$LIB/hookio.py" "$@"; }
pl_log() {
  python3 -I "$LIB/checkout.py" log hook="$HOOK_NAME" tool="$TOOL_NAME" checkout="$STATE_ROOT" \
    source="$SOURCE" forwarded="$PL_FORWARDED" "$@" || true
}

# pl_record_vote <judge> <verdict> <agent_id> <path> [log fields...]: record one judge vote through
# pipeline-advance (run from the state root, so it resolves the same checkout) and log the outcome.
pl_record_vote() {
  local judge="$1" verdict="$2" agent_id="$3" path="$4" phase out rc=0 event error=""
  shift 4
  phase=${STATE_STATUS##*:}
  case "$phase" in
    judge_*) ;;
    *) pl_log event=vote-ignored:not-in-judge-phase judge="$judge" verdict="$verdict" round="$phase" \
         path="$path" agent_id="$agent_id" "$@"
       return 0 ;;
  esac
  out=$(cd "$STATE_ROOT" && JUDGE_HOOK_CALLER=judge-count-hook \
    bash "$CODE_ROOT/.claude/hooks/pipeline-advance.sh" "$phase" "$judge" "$verdict" "$agent_id" "$path" 2>&1) || rc=$?
  case "$out" in
    "Judge recorded"*) event=vote-recorded ;;
    "Duplicate vote"*) event=vote-dup ;;
    # Combined stdout and stderr: the CLI prints nothing before its error line on a failing path.
    *) event="vote-ignored:advance-rc-$rc"; error=${out%%$'\n'*} ;;
  esac
  pl_log event="$event" error="$error" judge="$judge" verdict="$verdict" round="$phase" path="$path" agent_id="$agent_id" "$@"
}

# run_hook: run main_fn with errexit and nounset in a subshell, then map its exit code. A gate
# that crashes (traceback, unset variable, missing file) must block instead of failing open; an
# observer must never block.
run_hook() {
  local rc
  ( set -eu; main_fn "$@" )
  rc=$?
  case "$HOOK_KIND" in
    observer)
      [ "$rc" = 0 ] || pl_log event=observer-crash rc="$rc"
      exit 0 ;;
  esac
  case "$rc" in 0|2) exit "$rc" ;; esac
  pl_log event=gate-crash decision=block rc="$rc"
  echo "BLOCKED: $HOOK_NAME failed internally (rc=$rc); see .git/pipeline-hooks.log" >&2
  exit 2
}

# Must stay the last line: the hooks check it to prove this whole file was executed, because a
# syntax error stops the source early and the hook would then exit 127, which does not block.
PL_COMMON_LOADED=1
