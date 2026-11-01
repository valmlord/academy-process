#!/usr/bin/env python3
"""File-write gate decision for require-pipeline.sh, on the target's real path.

  pl_write_gate.py <cwd_status>     stdin: the PreToolUse hook JSON
Exit 0 = allow; exit 2 = block, stdout "<log reason>\\x1f<message>"; anything else is a crash.
"""
import fnmatch
import os
import sys
from typing import NoReturn

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
import cfg  # noqa: E402
import checkout  # noqa: E402
import pl_gate  # noqa: E402
from pl_jsonshape import as_object  # noqa: E402

OPEN_PREFIXES = (".claude/", "plans/")


def block(reason: str, message: str) -> NoReturn:
    raise pl_gate.Blocked(reason, message)


def always_blocked(path: str, data: dict[str, object], main: checkout.Worktree, conf: "cfg.Config") -> None:
    parts = path.split(os.sep)
    # .git paths hold git hooks and config, and a worktree's .git file is what makes it a worktree.
    if ".git" in parts or checkout.is_under(path, main.gitdir):
        block("git-dir", "the git dir and .git paths are never written by tools")
    home = os.path.expanduser("~")
    projects = os.path.realpath(os.path.join(home, ".claude", "projects"))
    # Role detection reads these files; memory/ beside them stays writable for auto memory.
    if checkout.is_under(path, projects):
        rel_parts = os.path.relpath(path, projects).split(os.sep)
        if parts[-1].endswith((".jsonl", ".meta.json")) or "subagents" in rel_parts:
            block("transcript", "session transcripts are never written by tools")
    transcript, session = data.get("transcript_path"), data.get("session_id")
    if isinstance(transcript, str) and transcript and isinstance(session, str) and session:
        if checkout.is_under(path, os.path.realpath(os.path.join(os.path.dirname(transcript), session))):
            block("transcript", "session transcripts are never written by tools")
    # disableAllHooks there switches every hook off; Stepan edits these files by hand.
    if os.path.dirname(path) == os.path.realpath(os.path.join(home, ".claude")) and fnmatch.fnmatch(parts[-1], "settings*.json"):
        block("user-settings", "user-level settings are never written by tools; Stepan edits them by hand")
    if parts[-1] == os.path.basename(conf["grant_file"]):
        block("grant-file", "the pipeline grant file is never written by tools; Stepan writes it by hand")


def core_rule(rel: str, status: str, conf: "cfg.Config", is_main: bool) -> None:
    if is_main and pl_gate.has_flag(conf, pl_gate.tier_of(status), "edits_pipeline_core"):
        return
    block("core:" + rel, "%s is pipeline core; writable only in a PIPELINE task in the main checkout "
          "(pause this one, then init PIPELINE <issue> with Stepan's grant)" % rel)


def main_zones(path: str, main: checkout.Worktree, conf: "cfg.Config") -> bool:
    """Main's state and core as absolute paths. -> True when the core rule allowed the write."""
    if path.startswith(os.path.join(main.root, ".claude", "pipeline_state")):
        block("state", "pipeline state is written only by pipeline-advance")
    for prefix in conf["pipeline_core_files"]:
        if path.startswith(os.path.join(main.root, prefix)):
            core_rule(os.path.relpath(path, main.root), checkout.status_of(main), conf, True)
            return True
    return False


def decide(data: dict[str, object], conf: "cfg.Config", cwd_status: str) -> None:
    tool_input = as_object(data.get("tool_input")) or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not isinstance(target, str) or not target:
        block("no-path", "the tool input names no file path")
    cwd = data.get("cwd")
    base = cwd if isinstance(cwd, str) and cwd else os.getcwd()
    # Real path: a symlinked directory (apps/link -> ../.claude/hooks) must not launder a core write.
    path = os.path.realpath(os.path.join(base, target))
    accepted, _ = checkout.worktrees()
    main = accepted[0]
    always_blocked(path, data, main, conf)
    if main_zones(path, main, conf):
        return

    owner = checkout.owner_of(accepted, path)
    if owner is None:
        rel, status = path, cwd_status
    else:
        rel, status = os.path.relpath(path, owner.root), checkout.status_of(owner)
    # An accepted worktree under .claude/worktrees/ would have won the longest-prefix match above.
    if owner is main and checkout.is_under(path, os.path.join(main.root, checkout.WORKTREES_DIR)):
        block("unregistered-worktree:" + rel, "%s is under .claude/worktrees/ but not in a registered worktree; "
              "create worktrees with git worktree add" % rel)
    if any(rel.startswith(p) for p in conf["protected_files"]):
        block("protected:" + rel, "%s is pipeline runtime state. Use pipeline-advance.sh; never edit it directly." % rel)
    # PIPELINE runs only in the main checkout, so a linked worktree's core is never writable.
    if owner is not main and any(rel.startswith(p) for p in conf["pipeline_core_files"]):
        core_rule(rel, status, conf, False)
    if rel.startswith(OPEN_PREFIXES):
        return
    if status == "unreadable":
        block("state-unreadable:" + rel, "the pipeline state of the checkout owning %s is unreadable; Stepan inspects it" % rel)
    tier = pl_gate.tier_of(status)
    if not tier:
        block("no-pipeline:" + rel, "no active pipeline. Start one: bash .claude/hooks/pipeline-advance.sh init <TIER> <issue> "
              "(announce [TIER #n] pipeline: ...).")
    if pl_gate.has_flag(conf, tier, "learner_writes_code"):
        if any(rel.startswith(p) for p in conf["learn_tier_editable_paths"]):
            return
        if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch("x/" + rel, g) for g in conf["learn_tier_test_globs"]):
            return
        block("learn:" + rel, "%s task: the learner writes %s. Explain, ask questions, review, write tests; "
              "do not edit product code." % (tier, rel))


def main() -> None:
    cwd_status = sys.argv[1]
    data = pl_gate.read_hook_input()
    pl_gate.run(lambda: decide(data, cfg.load(), cwd_status))


if __name__ == "__main__":
    main()
