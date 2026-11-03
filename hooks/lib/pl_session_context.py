#!/usr/bin/env python3
"""Session-start text for a session that does not load the main checkout's CLAUDE.md.

  pl_session_context.py <state_root> <main_root> <resolution> <state_status> [-]
      stdout: one SessionStart hook JSON object, or nothing for a session in the main checkout.
      <resolution> is the resolver's source field (cwd | fallback:<why>), not the hook input's
      `source`. With "-", the hook input JSON on stdin supplies the session's cwd. Exit 3, with
      nothing on stdout, when the text exceeds SESSION_CONTEXT_MAX_CHARS.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
from checkout import WORKTREES_DIR, is_under  # noqa: E402
from pl_text import printable  # noqa: E402

# The text points at CLAUDE.md and lists the rules a session needs before reading it; anything
# longer belongs in CLAUDE.md itself. Cutting it short could drop the probe or a rule, so an
# over-long text is an error and the wrapper's complete fallback is printed instead.
SESSION_CONTEXT_MAX_CHARS = 2000
EXIT_TOO_LONG = 3

LINKED_TEMPLATE = """\
academy pipeline: this session runs in a linked worktree of the academy repository.
Worktree: {wt}. Main checkout: {main}. Pipeline state here: {status}.
Before anything else:
1. Read {main}/.claude/CLAUDE.md in full: it holds your instructions (you are the orchestrator).
   Main's copy is the one that counts; {wt}/.claude/ exists only after init and is a process worktree
   whose files may lag main. Re-read it after /clear or compaction.
2. Run the hook probe in Bash: echo hook-probe >> /dev/null settings.pipeline-grant.json
   It must print BLOCKED. If it does not, stop and tell Stepan: the guards are off.
Worktree rules (CLAUDE.md section 7):
- One task per worktree session: create the task branch, then init. A second task needs a new session.
- Run every pipeline command as: bash "{main}/.claude/hooks/pipeline-advance.sh" <args>
  The copy under .claude/ here refuses by design. Never use $CLAUDE_PROJECT_DIR in Bash: it is empty.
- PIPELINE tasks run only in the main checkout.
- Git in {wt}/.claude: only status, diff, log, show, add <named paths>, commit, push, fetch,
  switch -c <new branch>, branch. Never switch it to main or another protected branch, never push to
  main, never git add -A."""

FALLBACK_TEMPLATE = """\
academy pipeline: this session's working directory did not resolve to an accepted academy checkout ({resolution}).
Gates and pipeline state use the main checkout {main}.
Read {main}/.claude/CLAUDE.md first, then run the hook probe in Bash: echo hook-probe >> /dev/null settings.pipeline-grant.json (it must print BLOCKED)."""


# The resolver maps a worktree git does not list, or one it skips (a path with a newline), to main
# with source cwd when it lies under <main>/.claude/worktrees/; such a session loads no CLAUDE.md.
UNACCEPTED_RESOLUTION = "unaccepted worktree under %s"
READ_HOOK_INPUT_ARG = "-"


def hook_input_cwd() -> str:
    """The session's cwd as the resolver reads it: the hook input's cwd, else this process's."""
    try:
        data: object = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except ValueError:
        data = {}
    cwd = data.get("cwd") if isinstance(data, dict) else None
    if isinstance(cwd, str) and cwd:
        return cwd
    try:
        return os.getcwd()
    except OSError:
        return ""


def render(state_root: str, main_root: str, resolution: str, status: str, cwd: str = "") -> str:
    """The additionalContext text; empty for the main checkout, whose CLAUDE.md loads by itself."""
    if resolution != "cwd":
        return FALLBACK_TEMPLATE.format(resolution=printable(resolution), main=printable(main_root))
    if os.path.realpath(state_root) == os.path.realpath(main_root):
        nest = os.path.join(os.path.realpath(main_root), WORKTREES_DIR)
        target = os.path.realpath(cwd) if cwd else ""
        if target and target != nest and is_under(target, nest):
            return FALLBACK_TEMPLATE.format(resolution=printable(UNACCEPTED_RESOLUTION % nest),
                                            main=printable(main_root))
        return ""
    return LINKED_TEMPLATE.format(wt=printable(state_root), main=printable(main_root), status=printable(status))


def main(argv: list[str]) -> int:
    if len(argv) not in (5, 6) or (len(argv) == 6 and argv[5] != READ_HOOK_INPUT_ARG):
        print(__doc__, file=sys.stderr)
        return 1
    cwd = hook_input_cwd() if len(argv) == 6 else ""
    text = render(argv[1], argv[2], argv[3], argv[4], cwd)
    if not text:
        return 0
    if len(text) > SESSION_CONTEXT_MAX_CHARS:
        print("pl_session_context.py: text is %d characters, over SESSION_CONTEXT_MAX_CHARS = %d"
              % (len(text), SESSION_CONTEXT_MAX_CHARS), file=sys.stderr)
        return EXIT_TOO_LONG
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
