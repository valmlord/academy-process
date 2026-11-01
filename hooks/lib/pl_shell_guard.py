#!/usr/bin/env python3
"""Shell guard decision for bash-code-guard.sh: string heuristics for shell writes the write gate
cannot see. A guardrail against mistakes, not a sandbox (ADR-0005).

  pl_shell_guard.py <state_root> <main_root> <cwd_status>     stdin: the PreToolUse hook JSON
Exit 0 = allow; exit 2 = block, stdout "<log reason>\\x1f<message>"; anything else is a crash.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
import cfg  # noqa: E402
import checkout  # noqa: E402
import pl_gate  # noqa: E402
from pl_jsonshape import as_object, as_str  # noqa: E402

WRITE_VERB = (r"(?:>>?|\btee\b|\bsed\s+-i|\bperl\s+-pi|\bcp\b|\bmv\b|\brm\b|\bln\b|\bchmod\b|\btruncate\b"
              r"|\bgit\s+checkout\b|\bgit\s+restore\b)")
SAME_SEGMENT = r"[^|;&\n]*"
# One rule for "the name ends here": the next character cannot continue a file name.
TOKEN_END = r"(?![\w.-])"
# The .claude directory (ancestor of every core path): removing or renaming it disables every hook.
#  1. ".claude/" followed by anything that cannot continue a name (end, space, "/", "{", "*", quote);
#  2. a bare ".claude" not followed by a name character or "/" (`.claude`, `.claude,`, `".claude"/x`);
#  3. a glob or brace character in the first component after ".claude/" (.claude/h*, .claude/h{ooks,}),
#     which the shell may expand to the hooks directory.
CLAUDE_DIR_TOKEN = r"(?<![\w.-])\.claude(?:/" + TOKEN_END + r"|(?![\w./-])|/[^\s/'\";|&)]*[*?\[{])"
HOME = re.escape(os.path.expanduser("~"))
NEVER_WRITTEN = (
    ("git-dir", r"(?<![\w.-])\.git(?![\w.-])", "a .git path"),
    ("transcript", r"\.claude/projects/", "session transcripts"),
    ("grant-file", r"settings\.pipeline-grant", "the pipeline grant file"),
    ("user-settings", r"(?:~|\$HOME|\$\{HOME\}|" + HOME + r")/\.claude/settings", "user-level settings"),
)


def writes_to(cmd: str, target: str) -> bool:
    return re.search(WRITE_VERB + SAME_SEGMENT + target, cmd) is not None


def core_pattern(core_files: list[str]) -> str:
    """pipeline_core_files are path prefixes for the write gate. In shell text a directory entry
    (trailing slash) is usually named without the slash, and removing or renaming the directory
    turns every hook into a non-blocking exit 127, so both spellings count."""
    parts = []
    for prefix in core_files:
        if prefix.endswith("/"):
            parts.append(re.escape(prefix.rstrip("/")) + "(?:/|" + TOKEN_END + ")")
        else:
            parts.append(re.escape(prefix))
    return "(?:" + "|".join(parts) + ")"


def decide(cmd: str, conf: "cfg.Config", state_root: str, main_root: str, cwd_status: str) -> None:
    if "core.hooksPath" in cmd:
        raise pl_gate.Blocked("hooks-path", "core.hooksPath is never changed by tools")
    for reason, target, what in NEVER_WRITTEN:
        if writes_to(cmd, target):
            raise pl_gate.Blocked(reason, "shell writes to %s are never allowed" % what)
    # The main-checkout check keeps a PIPELINE state that ended up in a worktree from opening
    # main's core to shell writes.
    core_allowed = state_root == main_root and pl_gate.has_flag(conf, pl_gate.tier_of(cwd_status), "edits_pipeline_core")
    if writes_to(cmd, core_pattern(conf["pipeline_core_files"])) and not core_allowed:
        raise pl_gate.Blocked("core-shell", "shell writes to pipeline core (%s) are allowed only in a PIPELINE task "
                              "in the main checkout" % ", ".join(conf["pipeline_core_files"]))
    # Tested after the core files so a command that names one keeps that message; a stray .claude
    # token (node_modules/.claude) names no core file, and the message must not claim it does.
    if writes_to(cmd, CLAUDE_DIR_TOKEN) and not core_allowed:
        raise pl_gate.Blocked("core-shell:claude-dir", "shell writes that name a .claude directory are allowed only in "
                              "a PIPELINE task in the main checkout (removing or renaming .claude disables every hook)")
    # The write gate cannot see shell targets, so every checkout the command names by absolute path
    # is consulted too: cd-ing to a non-LEARN worktree must not lift main's LEARN rule.
    consulted = [cwd_status]
    accepted, _ = checkout.worktrees()
    consulted += [checkout.status_of(wt) for wt in accepted if wt.root != state_root and wt.root in cmd]
    learn = [s for s in consulted if s == "unreadable" or pl_gate.has_flag(conf, pl_gate.tier_of(s), "learner_writes_code")]
    if not learn:
        return
    dirs = "|".join(re.escape(d.rstrip("/")) for d in conf["learn_tier_code_dirs"])
    if writes_to(cmd, r"\b(?:%s)/" % dirs):
        if "unreadable" in learn:
            raise pl_gate.Blocked("learn-shell-write:state-unreadable",
                                  "pipeline state unreadable; shell writes into product code are blocked")
        raise pl_gate.Blocked("learn-shell-write", "%s task: shell writes into product code are not allowed; the "
                              "learner writes the code." % pl_gate.tier_of(learn[0]))


def main() -> None:
    state_root, main_root, cwd_status = sys.argv[1:4]
    data = pl_gate.read_hook_input()
    tool_input = as_object(data.get("tool_input")) or {}
    command = as_str(tool_input.get("command"))
    pl_gate.run(lambda: decide(command, cfg.load(), state_root, main_root, cwd_status))


if __name__ == "__main__":
    main()
