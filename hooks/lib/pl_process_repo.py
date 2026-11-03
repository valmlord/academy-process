#!/usr/bin/env python3
"""Commit-time rules for the process repository at <state root>/.claude: the main checkout's clone
(issue #86), or a linked worktree's process worktree of that clone (issue #89).

  pl_process_repo.py pr <state root> <issue>     rules 0-5 for the process repo, 6-7 for the product
  pl_process_repo.py stop <state root> [issue]   rules 0-5 only (Stop at done; product checked by the hook)
Exit 0 = no problem; exit 2 = one problem per stdout line; 1 = a usage error (stderr names it);
anything else is a crash. The callers refuse on every exit but 0. Rule numbers are those of the #86 design, section 4.2.
"""
import os
import re
import stat
import subprocess
import sys
from typing import NamedTuple, Optional, Sequence

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
import cfg  # noqa: E402
import checkout  # noqa: E402

EXIT_PROBLEMS = 2
PROCESS_DIR = ".claude"
PROCESS_SLUG = "valmlord/academy-process"
# Process commits cite the product issue with the repository prefix: a process squash subject ends
# with the process PR number, which would collide with a bare product issue number.
PROCESS_FOOTER = r"valmlord/academy#%d([^0-9]|$)"
# The product footer convention; on a protected process branch it marks an issue commit as well.
PRODUCT_FOOTER = r"Refs #%d([^0-9]|$)"
PRODUCT_REFERENCE = r"#%d\b"
MAX_LISTED_PATHS = 10
# The only ignored entries a process repo may hold. The allowlist .gitignore ignores every new
# top-level entry (/*), so an instruction path Claude Code loads (rules/, skills/, commands/) would
# be invisible to the dirty rule; anything ignored that is not named here is refused instead.
# Top-level names: the hooks' state, its lock, parked states and atomic-write temp files
# (lib/state.py), the grant, Claude Code's local settings and its worktrees.
LOCAL_RUNTIME_TOP_LEVEL = ("pipeline_state.json", "pipeline_state.flock", "pipeline_state.parked/",
                           "settings.local.json", "settings.pipeline-grant.json", "worktrees/")
LOCAL_RUNTIME_TOP_LEVEL_PREFIXES = ("pipeline_state.tmp.",)
# Names allowed at any depth: Finder metadata and Python's bytecode cache.
PYCACHE_DIR = "__pycache__/"
LOCAL_RUNTIME_ANY_DEPTH = (".DS_Store", PYCACHE_DIR)
# A cache directory is ignored at any depth, including under agents/, so it counts as runtime only
# while it holds nothing but bytecode: an agents/dev/__pycache__/coder.md must not pass unseen.
BYTECODE_SUFFIX = ".pyc"
# Porcelain v1 status codes whose -z record carries a second path (the rename or copy source).
STATUS_TWO_PATH_CODES = ("R", "C")
IGNORED_STATUS = "!!"
# `symbolic-ref -q HEAD` exits 1 on a detached HEAD; every other non-zero exit is a git error.
SYMBOLIC_REF_DETACHED_RC = 1
GIT_TIMEOUT_SECONDS = checkout.GIT_TIMEOUT_SECONDS


class Repo(NamedTuple):
    path: str
    # Set for the process repo. Without it, a broken .claude/.git makes git search upward and answer
    # for the product repo, which ignores .claude/ as a whole: every rule would pass on its status.
    git_dir: Optional[str]


class GitFailed(Exception):
    def __init__(self, directory: str, args: Sequence[str], rc: str) -> None:
        super().__init__("git failed in %s: %s (rc %s)" % (directory, " ".join(args), rc))


class GitResult(NamedTuple):
    rc: int
    out: str


def git(repo: Repo, *args: str, allowed_rcs: Sequence[int] = (0,)) -> GitResult:
    # core.fsmonitor names a program git would run; a value set in the nested repo must not run here.
    # core.fileMode=false in a repo config would make status report a hook that lost its exec bit
    # as clean, so the mode change would never reach a process PR.
    cmd = ["git", "-c", "core.fsmonitor=false", "-c", "core.fileMode=true", "--no-optional-locks",
           "-C", repo.path]
    if repo.git_dir is not None:
        cmd += ["--git-dir=" + repo.git_dir, "--work-tree=" + repo.path]
    try:
        proc = subprocess.run(cmd + list(args), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              timeout=GIT_TIMEOUT_SECONDS, universal_newlines=True)
    except subprocess.TimeoutExpired:
        raise GitFailed(repo.path, args, "timeout")
    except OSError as exc:
        raise GitFailed(repo.path, args, exc.__class__.__name__)
    if proc.returncode not in allowed_rcs:
        raise GitFailed(repo.path, args, str(proc.returncode))
    return GitResult(proc.returncode, proc.stdout)


def protected_refs(repo: Repo, branches: Sequence[str]) -> list[str]:
    """The refs refs/heads/<b> and refs/remotes/origin/<b> that exist, for every protected <b>."""
    wanted = [prefix + b for b in branches for prefix in ("refs/heads/", "refs/remotes/origin/")]
    if not wanted:
        return []
    listed = git(repo, "for-each-ref", "--format=%(refname)", *wanted).out.splitlines()
    # for-each-ref also matches refs below a pattern (refs/heads/main/x); only exact names count.
    return [ref for ref in wanted if ref in listed]


def ahead_count(repo: Repo, refs: Sequence[str]) -> int:
    """Commits of HEAD reachable from none of refs (all of HEAD's commits when refs is empty)."""
    return int(git(repo, "rev-list", "--count", "HEAD", "--not", *refs).out.strip() or "0")


def short_ref(ref: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def head_branch(repo: Repo) -> Optional[str]:
    """The checked-out branch, or None on a detached HEAD."""
    result = git(repo, "symbolic-ref", "-q", "HEAD", allowed_rcs=(0, SYMBOLIC_REF_DETACHED_RC))
    if result.rc == SYMBOLIC_REF_DETACHED_RC:
        return None
    return short_ref(result.out.strip())


def last_message(repo: Repo) -> str:
    return git(repo, "log", "-1", "--format=%B", "HEAD").out


def listed(paths: Sequence[str]) -> str:
    more = " (and %d more)" % (len(paths) - MAX_LISTED_PATHS) if len(paths) > MAX_LISTED_PATHS else ""
    return ", ".join(paths[:MAX_LISTED_PATHS]) + more


def status_entries(proc: Repo) -> list[tuple[str, str]]:
    """(two-letter code, path) for every changed, untracked and ignored entry of the work tree."""
    # The flags pin what a repo or user config could otherwise hide: status.showUntrackedFiles=no
    # drops untracked files, and only --ignored shows what the allowlist's /* hides.
    out = git(proc, "status", "--porcelain=v1", "-z", "--untracked-files=normal", "--ignored=matching").out
    fields = out.split("\0")
    entries = []
    index = 0
    while index < len(fields):
        record = fields[index]
        index += 1
        if not record:
            continue
        code = record[:2]
        entries.append((code, record[3:]))
        if code[0] in STATUS_TWO_PATH_CODES:
            index += 1
    return entries


def is_local_runtime(path: str) -> bool:
    if path in LOCAL_RUNTIME_TOP_LEVEL or (path.startswith(LOCAL_RUNTIME_TOP_LEVEL_PREFIXES) and "/" not in path):
        return True
    # status marks a directory with a trailing slash; keep it, so a file named __pycache__ is no cache.
    trailing = "/" if path.endswith("/") else ""
    return path.rstrip("/").rsplit("/", 1)[-1] + trailing in LOCAL_RUNTIME_ANY_DEPTH


def is_pycache_dir(path: str) -> bool:
    return path.endswith("/") and path.rstrip("/").rsplit("/", 1)[-1] + "/" == PYCACHE_DIR


def non_bytecode_paths(proc: Repo, cache_dir: str) -> list[str]:
    """Paths under a __pycache__/ status entry that are not regular *.pyc files, symlinks included."""
    # Walked with lstat, not taken from status: status collapses an ignored directory to one entry,
    # and following a symlink would let a link named x.pyc point at any file.
    offending = []
    pending = [cache_dir.rstrip("/")]
    while pending:
        current = pending.pop()
        try:
            mode = os.lstat(os.path.join(proc.path, current)).st_mode
            names = sorted(os.listdir(os.path.join(proc.path, current))) if stat.S_ISDIR(mode) else []
        except OSError:
            # Unreadable or gone between status and the walk: fail closed and name it.
            offending.append(current + "/")
            continue
        if not stat.S_ISDIR(mode):
            offending.append(current)
            continue
        for name in names:
            child = current + "/" + name
            try:
                child_mode = os.lstat(os.path.join(proc.path, child)).st_mode
            except OSError:
                offending.append(child)
                continue
            if stat.S_ISDIR(child_mode):
                pending.append(child)
            elif not (stat.S_ISREG(child_mode) and name.endswith(BYTECODE_SUFFIX)):
                offending.append(child)
    return sorted(offending)


def dirty_rule(proc: Repo) -> list[str]:
    entries = status_entries(proc)
    changed = [path for code, path in entries if code != IGNORED_STATUS]
    hidden = [path for code, path in entries if code == IGNORED_STATUS and not is_local_runtime(path)]
    in_caches = [found for code, path in entries if code == IGNORED_STATUS and is_pycache_dir(path)
                 for found in non_bytecode_paths(proc, path)]
    problems = []
    if changed:
        problems.append("the process repo has uncommitted changes: %s. Commit them on a branch of %s, adding each "
                        "path by name (git -C .claude add <path>); never git add -A: the grant and local settings "
                        "live in the same directory." % (listed(changed), PROCESS_SLUG))
    if hidden:
        problems.append("the process repo holds ignored path(s) that are not local runtime files: %s. Remove them, "
                        "or track a new process path with a !/<entry> line in .claude/.gitignore (a PIPELINE task); "
                        "a runtime file the hooks or Claude Code create goes on LOCAL_RUNTIME_* in "
                        "hooks/lib/pl_process_repo.py." % listed(hidden))
    if in_caches:
        problems.append("the process repo holds path(s) other than regular *.pyc files in a __pycache__ directory, "
                        "which the allowlist ignores at any depth: %s. Remove them; only Python's bytecode cache "
                        "may live there." % listed(in_caches))
    return problems


def hidden_edits_rule(proc: Repo) -> list[str]:
    """Tracked files whose edits git is told not to look at."""
    # ls-files -v prints the tag in lower case for assume-unchanged and S for skip-worktree; either
    # makes status report an edited tracked hook as clean.
    records = [r for r in git(proc, "ls-files", "-v", "-z").out.split("\0") if r]
    flagged = [r[2:] for r in records if r[0].islower() or r[0] == "S"]
    if not flagged:
        return []
    return ["tracked file(s) flagged assume-unchanged or skip-worktree hide their edits: %s. Stepan clears the "
            "flag: git -C .claude update-index --no-assume-unchanged --no-skip-worktree <path>" % listed(flagged)]


def protected_issue_commit_rule(proc: Repo, issue: int, refs: Sequence[str], task_branch: str) -> list[str]:
    problems = []
    for ref in refs:
        found = git(proc, "log", "-E", "--grep=" + PROCESS_FOOTER % issue, "--grep=" + PRODUCT_FOOTER % issue,
                    "--format=%h", "-1", ref).out.strip()
        if not found:
            continue
        name = short_ref(ref)
        base = name.split("/", 1)[1] if name.startswith("origin/") else name
        problems.append(
            "commit %s for #%d is on %s of the process repo; it needs a PR. Not pushed: `git -C .claude switch -c "
            "%s` (if on it), then `git -C .claude branch -f %s origin/%s`. Pushed: stop and ask Stepan."
            % (found, issue, name, task_branch or "<task branch>", base, base))
    return problems


def protected_head_ahead(proc: Repo, branch: str) -> bool:
    """On a protected branch <b>, HEAD is part of refs/heads/<b>, so "ahead" compares it with origin/<b>."""
    remote = "refs/remotes/origin/" + branch
    # Never pushed (or no remote at all): every commit of <b> is unreviewed.
    if remote not in protected_refs(proc, [branch]):
        return True
    return int(git(proc, "rev-list", "--count", remote + "..refs/heads/" + branch).out.strip() or "0") > 0


def linked_process_repo(path: str, main_root: str) -> tuple[Optional[Repo], list[str]]:
    """A linked worktree's process repo must be a process worktree of main's clone, back-pointer
    included; anything else is one problem line, never a skip. -> (repo, []) or (None, [problem])."""
    # Imported here: pl_process_worktree imports this module for its git helpers.
    import pl_process_worktree
    try:
        if os.path.islink(path):
            raise pl_process_worktree.NotAProcessWorktree(path, main_root, "a symlink")
        return Repo(path, pl_process_worktree.admin_dir_of(path, main_root)), []
    except pl_process_worktree.NotAProcessWorktree as exc:
        # Not "run init": init refuses while this directory is in the way.
        return None, ["%s; Stepan moves it aside" % exc]


def process_rules(state_root: str, issue: Optional[int], protected: Sequence[str],
                  task_branch: str) -> tuple[list[str], bool]:
    """Rules 0-5. -> (problems, whether the process repo has commits outside its protected branches)."""
    path = os.path.join(state_root, PROCESS_DIR)
    dotgit = os.path.join(path, ".git")
    main_root = checkout.code_root()
    if os.path.realpath(state_root) != main_root:
        linked, refused = linked_process_repo(path, main_root)
        if linked is None:
            return refused, False
        proc = linked
    else:
        try:
            mode = os.lstat(dotgit).st_mode
        except FileNotFoundError:
            # Fixtures and a fresh device before the clone have no process repo.
            checkout.log_event(event="process-check-skipped", reason="process repo check skipped: %s missing" % dotgit,
                               path=path)
            return [], False
        if not stat.S_ISDIR(mode):
            return ["%s is not a directory; the process repo must be a plain clone" % dotgit], False
        proc = Repo(path, dotgit)

    problems = dirty_rule(proc) + hidden_edits_rule(proc)
    refs = protected_refs(proc, protected)
    ahead = ahead_count(proc, refs) > 0
    if issue is not None:
        if refs:
            problems += protected_issue_commit_rule(proc, issue, refs, task_branch)
        branch = head_branch(proc)
        if branch is None:
            off_task_branch = ahead
        else:
            off_task_branch = branch in protected and protected_head_ahead(proc, branch)
        if off_task_branch:
            problems.append("process commits are not on a task branch (HEAD: %s); move them to a branch named like "
                            "the product branch" % (branch or "detached"))
        if ahead and not re.search(PROCESS_FOOTER % issue, last_message(proc), re.M):
            problems.append("the last process commit lacks Refs valmlord/academy#%d; if this branch's PR is merged, "
                            "sync the process repo (.claude/CLAUDE.md section 7)" % issue)
    tracked = [p for p in git(proc, "ls-files", "-ci", "--exclude-standard").out.splitlines() if p]
    if tracked:
        problems.append("tracked runtime file(s) %s: git -C .claude rm --cached <path>"
                        % ", ".join(tracked[:MAX_LISTED_PATHS]))
    return problems, ahead


def product_rules(product: Repo, issue: int, protected: Sequence[str], process_ahead: bool) -> list[str]:
    """Rules 6 (issue reference) and 7. The branch and clean-tree parts of rule 6 stay in the CLI."""
    product_ahead = ahead_count(product, protected_refs(product, protected)) > 0
    if product_ahead and not re.search(PRODUCT_REFERENCE % issue, last_message(product)):
        return ["the last commit message must reference the issue (e.g. 'Refs #%d')." % issue]
    if not product_ahead and not process_ahead:
        return ["no commit for #%d in either repository" % issue]
    return []


class InvalidIssueError(ValueError):
    def __init__(self, text: str) -> None:
        super().__init__("issue must be ASCII digits, got %r" % text)


def parse_issue(text: str) -> int:
    # isdigit() accepts Unicode digits that int() reads too; the state holds ASCII digits only.
    if not (text.isascii() and text.isdigit()):
        raise InvalidIssueError(text)
    return int(text)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] not in ("pr", "stop") or (argv[1] == "pr" and len(argv) < 4):
        print(__doc__, file=sys.stderr)
        return 1
    mode, state_root = argv[1], argv[2]
    try:
        issue = parse_issue(argv[3]) if len(argv) > 3 and argv[3] else None
    except InvalidIssueError as exc:
        # A usage error, not a problem of the repositories: rc 1, which both callers refuse on.
        print("pl_process_repo.py: %s" % exc, file=sys.stderr)
        return 1
    protected = cfg.load()["protected_branches"]
    product = Repo(state_root, None)
    try:
        task_branch = head_branch(product) or ""
        problems, process_ahead = process_rules(state_root, issue, protected, task_branch)
        if mode == "pr" and issue is not None:
            problems += product_rules(product, issue, protected, process_ahead)
    except GitFailed as exc:
        problems = [str(exc)]
    for problem in problems:
        print(problem)
    return EXIT_PROBLEMS if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
