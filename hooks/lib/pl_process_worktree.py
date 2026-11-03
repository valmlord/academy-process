#!/usr/bin/env python3
"""The process worktree of a linked product worktree (issue #89).

A session in a linked worktree <wt> keeps its pipeline state and process edits in <wt>/.claude, a
git worktree of the main checkout's process repo <main>/.claude, on a process branch named like the
product branch. lib/state.py's init calls ensure() to create or re-check it; admin_dir_of() is the
layout check the process repo rules (lib/pl_process_repo.py) share.
"""
import os
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
import cfg  # noqa: E402
import checkout  # noqa: E402
from pl_process_repo import PROCESS_DIR, GitFailed, Repo, git, head_branch, status_entries  # noqa: E402

# git worktree add checks out the whole process tree; init is a CLI call, not a gate under the
# 15 s hook timeout.
PROCESS_WORKTREE_ADD_TIMEOUT_SECONDS = 30
# A new process branch starts from the reviewed state, never from Stepan's local main.
PROCESS_BASE = "origin/main"
PROCESS_BASE_REF = "refs/remotes/" + PROCESS_BASE
# Present in an admin dir while `worktree add` is still checking out, or after `worktree lock`.
LOCKED_FILE = "locked"
# The admin dir's pointer back to the worktree's .git file.
BACK_POINTER_FILE = "gitdir"
HEADS_PREFIX = "refs/heads/"


class WorktreeRefused(Exception):
    """ensure() will not create or reuse the process worktree; the message says why and what to do."""


class NotAProcessWorktree(Exception):
    def __init__(self, proc_path: str, main_root: str, why: str) -> None:
        super().__init__("%s is not a process worktree of %s (%s)"
                         % (proc_path, os.path.join(main_root, PROCESS_DIR), why))


def _process_repo(main_root: str) -> Repo:
    path = os.path.join(main_root, PROCESS_DIR)
    return Repo(path, os.path.join(path, ".git"))


def _back_pointer(admin_dir: str) -> str:
    """Real path of the .git file the admin dir names, or "" when it cannot be read."""
    try:
        with open(os.path.join(admin_dir, BACK_POINTER_FILE), encoding="utf-8", errors="surrogateescape") as fh:
            target = fh.readline().rstrip("\r\n")
    except OSError:
        return ""
    if not target:
        return ""
    # worktree.useRelativePaths (git 2.48+) writes it relative to the admin dir.
    return os.path.realpath(os.path.join(admin_dir, target))


def admin_dir_of(proc_path: str, main_root: str) -> str:
    """The admin dir of the process worktree at proc_path. Raises NotAProcessWorktree unless its .git
    is a regular file naming a dir strictly under <main>/.claude/.git/worktrees/ whose back-pointer
    is this very .git file: a copied .git file would otherwise borrow a sibling's admin dir."""
    dotgit = os.path.join(proc_path, ".git")
    try:
        mode = os.lstat(dotgit).st_mode
    except FileNotFoundError:
        raise NotAProcessWorktree(proc_path, main_root, "no .git file")
    except OSError as exc:
        raise NotAProcessWorktree(proc_path, main_root, "cannot read .git: %s" % exc.__class__.__name__)
    if not stat.S_ISREG(mode):
        raise NotAProcessWorktree(proc_path, main_root, ".git is not a regular file")
    admin_dir = checkout.linked_gitdir(proc_path)
    admin_root = os.path.realpath(os.path.join(main_root, PROCESS_DIR, ".git", "worktrees"))
    if admin_dir is None or admin_dir == admin_root or not checkout.is_under(admin_dir, admin_root):
        raise NotAProcessWorktree(proc_path, main_root, "its gitdir is not under %s" % admin_root)
    if _back_pointer(admin_dir) != os.path.realpath(dotgit):
        raise NotAProcessWorktree(proc_path, main_root, "its admin dir %s belongs to another worktree" % admin_dir)
    return admin_dir


def _check_existing(proc_path: str, main_root: str, branch: str, conf: cfg.Config) -> None:
    """Design 1.2 steps 3a-3f: refuse a process worktree init must not use as it is."""
    if os.path.islink(proc_path) or not os.path.isdir(proc_path):
        raise WorktreeRefused("%s exists and is not a directory; Stepan moves it aside" % proc_path)
    try:
        admin_dir = admin_dir_of(proc_path, main_root)
    except NotAProcessWorktree as exc:
        raise WorktreeRefused("%s; Stepan moves it aside" % exc)
    repo = Repo(proc_path, admin_dir)
    main_proc = _process_repo(main_root).path
    try:
        head = head_branch(repo)
        merge = git(repo, "config", "--get", "branch.%s.merge" % branch, allowed_rcs=(0, 1)).out.strip()
        deleted = any("D" in code for code, _ in status_entries(repo))
    except GitFailed as exc:
        raise WorktreeRefused("cannot inspect the process worktree at %s: %s" % (proc_path, exc))
    if head != branch:
        raise WorktreeRefused("the process worktree %s is on %s; sync that task (.claude/CLAUDE.md section 7) or "
                              "start a new worktree session" % (proc_path, head or "a detached HEAD"))
    upstream = merge[len(HEADS_PREFIX):] if merge.startswith(HEADS_PREFIX) else ""
    # An upstream on the branch's own name (push -u) is fine; one on main would carry a bare push there.
    if upstream in conf["protected_branches"]:
        raise WorktreeRefused("process branch %s tracks %s; Stepan: git -C %s branch --unset-upstream %s"
                              % (branch, upstream, main_proc, branch))
    # A worktree add that died mid-checkout leaves its lock behind and the tree short of tracked files.
    if os.path.lexists(os.path.join(admin_dir, LOCKED_FILE)) or deleted:
        raise WorktreeRefused("half-created process worktree at %s; Stepan: git -C %s worktree unlock %s, then "
                              "git -C %s worktree remove --force %s (it was never initialised)"
                              % (proc_path, main_proc, proc_path, main_proc, proc_path))


def _add(main_root: str, proc_path: str, branch: str, state_root: str) -> None:
    """Design 1.2 steps 4-5: git worktree add from origin/main, or of an existing process branch."""
    main_proc = _process_repo(main_root)
    if not os.path.isdir(main_proc.git_dir or ""):
        raise WorktreeRefused("%s is not a directory: the main checkout has no process clone; Stepan: "
                              "git -C %s fetch origin after cloning it" % (main_proc.git_dir, main_proc.path))
    short = ahead = ""
    try:
        has_base = git(main_proc, "show-ref", "--verify", "--quiet", PROCESS_BASE_REF, allowed_rcs=(0, 1)).rc == 0
        exists = git(main_proc, "show-ref", "--verify", "--quiet", HEADS_PREFIX + branch, allowed_rcs=(0, 1)).rc == 0
        if exists and has_base:
            short = git(main_proc, "rev-parse", "--short", HEADS_PREFIX + branch).out.strip()
            ahead = git(main_proc, "rev-list", "--count", HEADS_PREFIX + branch, "--not", PROCESS_BASE_REF).out.strip()
    except GitFailed as exc:
        raise WorktreeRefused("cannot inspect the process repo %s: %s" % (main_proc.path, exc))
    if not has_base:
        raise WorktreeRefused("the process repo %s has no %s; Stepan: git -C %s fetch origin"
                              % (main_proc.path, PROCESS_BASE, main_proc.path))
    if exists:
        print("reusing existing process branch %s at %s (%s commits not on %s)" % (branch, short, ahead, PROCESS_BASE),
              file=sys.stderr)
        checkout.log_event(event="process-worktree-reused-branch", hook="state.py", checkout=state_root, path=proc_path)
        where = [proc_path, branch]
    else:
        # --no-track: a -b from a remote-tracking ref would set origin/main as upstream, and with
        # push.default=upstream a bare git push would land on process main.
        where = ["--no-track", "-b", branch, proc_path, PROCESS_BASE]
    # core.hooksPath=/dev/null: the process repo's own post-checkout hook must not run inside init.
    cmd = ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-C", main_proc.path,
           "worktree", "add"] + where
    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, universal_newlines=True,
                              timeout=PROCESS_WORKTREE_ADD_TIMEOUT_SECONDS)
        rc, first = proc.returncode, (proc.stderr.strip().splitlines() or [""])[0]
    except subprocess.TimeoutExpired:
        rc, first = -1, "timed out after %ss" % PROCESS_WORKTREE_ADD_TIMEOUT_SECONDS
    except OSError as exc:
        rc, first = -1, exc.__class__.__name__
    if rc != 0:
        raise WorktreeRefused("git worktree add failed: %s; see git -C %s worktree list" % (first, main_proc.path))


def ensure(state_root: str, main_root: str, branch: str, conf: cfg.Config) -> None:
    """Create or re-check <state_root>/.claude before init writes a state there; a no-op for main.
    Raises WorktreeRefused, after which no state is written."""
    if os.path.realpath(state_root) == os.path.realpath(main_root):
        return
    # The process branch takes the product branch's name, so no process worktree ever holds main.
    if not branch or branch in conf["protected_branches"]:
        raise WorktreeRefused("the product branch is %s; process worktrees take the task branch's name. Create "
                              "it first: git switch -c <type>/<issue>-<slug>" % (branch or "a detached HEAD"))
    proc_path = os.path.join(state_root, PROCESS_DIR)
    if os.path.lexists(proc_path):
        # A rerun after a crash between creation and the state write reuses a valid one.
        _check_existing(proc_path, main_root, branch, conf)
        return
    _add(main_root, proc_path, branch, state_root)
    _check_existing(proc_path, main_root, branch, conf)
    checkout.log_event(event="process-worktree-created", hook="state.py", checkout=state_root, path=proc_path)
