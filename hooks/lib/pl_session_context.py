#!/usr/bin/env python3
"""Session-start text for a session that does not load the main checkout's CLAUDE.md.

  pl_session_context.py <state_root> <main_root> <resolution> <state_status>
      stdout: one SessionStart hook JSON object, or nothing for a session in the main checkout.
      <resolution> is the resolver's source field (cwd | fallback:<why>), not the hook input's
      `source`. Exit 3, with nothing on stdout, when the text exceeds SESSION_CONTEXT_MAX_CHARS.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
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


def render(state_root: str, main_root: str, resolution: str, status: str) -> str:
    """The additionalContext text; empty for the main checkout, whose CLAUDE.md loads by itself."""
    if resolution != "cwd":
        return FALLBACK_TEMPLATE.format(resolution=printable(resolution), main=printable(main_root))
    if os.path.realpath(state_root) == os.path.realpath(main_root):
        return ""
    return LINKED_TEMPLATE.format(wt=printable(state_root), main=printable(main_root), status=printable(status))


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 1
    text = render(argv[1], argv[2], argv[3], argv[4])
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
