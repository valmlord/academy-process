#!/usr/bin/env python3
"""Locked transactions on one checkout's pipeline state; pipeline-advance.sh is the only caller
besides the tests.

Every op runs its whole read-modify-write under an exclusive flock and replaces the state file
atomically, so concurrent hooks never lose an update and the gates' unlocked reads never see a
torn file.

  state.py init <root> <tier> <issue> <branch> <gitdir> <code_root>
  state.py advance <root> <expected_current> <next>
  state.py vote <root> <round> <judge> <verdict> [agent_id] [path]
  state.py record_spawn <root> <round> <agent_id> <judge>
  state.py set_artifact <root> <key> <value>
  state.py finish <root>
  state.py park <root> <reason> <code_root> <gitdir> <branch>     (pause: reason "pause")
  state.py resume <root> <issue|key> <code_root> <gitdir> <branch>
  state.py parked <root>

Exit codes: 0 done (one result line on stdout), 1 refused, 3 the state changed under the caller,
4 Stepan's grant is missing or invalid, 75 the lock was not acquired in time. Errors go to stderr; nothing is written on any error.
"""
import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time
from typing import Callable, Iterator, Mapping, Optional

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.append(HERE)
import cfg  # noqa: E402
import checkout  # noqa: E402
from pl_jsonshape import as_list, as_str  # noqa: E402

EXIT_REFUSED = 1
EXIT_CONFLICT = 3
EXIT_NO_GRANT = 4
# EX_TEMPFAIL from sysexits.h: nothing happened, the caller may retry.
EXIT_LOCK_TIMEOUT = 75
LOCK_POLL_SECONDS = 0.05
# Same value as pipeline.json state_lock_timeout_seconds; used only when that key is absent.
DEFAULT_LOCK_TIMEOUT_SECONDS = 5
SECONDS_PER_HOUR = 3600
# A new name, not v1's pipeline_state.json.lock: v1 treats an existing .json.lock as held and
# waits on it, and this lock file is never deleted.
LOCK_NAME = "pipeline_state.flock"
STATE_NAME = "pipeline_state.json"
PARKED_DIR = "pipeline_state.parked"


class Refused(Exception):
    code = EXIT_REFUSED


class Conflict(Refused):
    code = EXIT_CONFLICT


class GrantRefused(Refused):
    code = EXIT_NO_GRANT


class StateLockTimeout(Exception):
    pass


def is_ascii_digits(text: str) -> bool:
    """str.isdigit() also accepts Unicode digits such as "\u00b2", which int() then rejects."""
    return text.isascii() and text.isdigit()


GRANT_KEYS = ("version", "pipeline_init", "learn_pause")
GRANT_VERSION = 1


def _grant_invalid(conf: cfg.Config, why: str) -> GrantRefused:
    return GrantRefused("%s is invalid: %s; no grant applies" % (conf["grant_file"], why))


def read_grant(conf: cfg.Config, code_root: str) -> Optional[dict[str, object]]:
    """Stepan's grant file in the main checkout, read on every decision and never cached. -> dict,
    or None when absent. Anything malformed raises: a typo must be reported, never grant silently."""
    path = os.path.join(code_root, conf["grant_file"])
    if not os.path.lexists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data: object = json.load(fh)
    except (OSError, ValueError) as exc:
        raise _grant_invalid(conf, "not readable JSON (%s)" % exc.__class__.__name__)
    if not isinstance(data, dict):
        raise _grant_invalid(conf, "not a JSON object")
    unknown = sorted(set(data) - set(GRANT_KEYS))
    if unknown:
        raise _grant_invalid(conf, "unknown key %s" % ", ".join(unknown))
    # bool is a subclass of int in Python: JSON true must not pass as version 1 or as issue 1.
    if type(data.get("version")) is not int or data["version"] != GRANT_VERSION:
        raise _grant_invalid(conf, '"version" must be the integer %d' % GRANT_VERSION)
    for key in GRANT_KEYS[1:]:
        if key not in data:
            continue
        value = data[key]
        if not isinstance(value, list):
            raise _grant_invalid(conf, '"%s" must be a list' % key)
        if any(type(x) is not int or x <= 0 for x in value):
            raise _grant_invalid(conf, '"%s" must list positive issue numbers' % key)
    return data


def require_grant(conf: cfg.Config, code_root: str, kind: str, issue: object, refusal: str, root: str) -> None:
    """Raise GrantRefused(refusal) unless the grant file lists issue under kind."""
    try:
        grant = read_grant(conf, code_root)
    except GrantRefused:
        checkout.log_event(event="grant-invalid", hook="state.py", checkout=root, grant=kind, issue=str(issue))
        raise
    text = str(issue)
    number = int(text) if is_ascii_digits(text) else None
    if grant is None or number not in as_list(grant.get(kind, [])):
        checkout.log_event(event="grant-missing", hook="state.py", checkout=root, grant=kind, issue=str(issue))
        raise GrantRefused(refusal)
    checkout.log_event(event="grant-used", hook="state.py", checkout=root, grant=kind, issue=str(issue))


def _claude_dir(root: str) -> str:
    return os.path.join(root, ".claude")


def state_path(root: str) -> str:
    return os.path.join(_claude_dir(root), STATE_NAME)


def _lock_timeout() -> float:
    value = cfg.load().get("state_lock_timeout_seconds", DEFAULT_LOCK_TIMEOUT_SECONDS)
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else DEFAULT_LOCK_TIMEOUT_SECONDS


@contextlib.contextmanager
def transaction(root: str) -> Iterator[None]:
    """Hold the checkout's state lock. flock is released by the kernel when its holder dies, so a
    lock that is still held belongs to a live process and is never broken."""
    lock = os.path.join(_claude_dir(root), LOCK_NAME)
    timeout = _lock_timeout()
    fd = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise StateLockTimeout("could not lock %s within %ss; nothing written" % (lock, timeout))
                time.sleep(LOCK_POLL_SECONDS)
        yield
    finally:
        os.close(fd)


def _test_delay() -> None:
    """PIPELINE_STATE_TEST_DELAY_MS widens the read-to-write window for the concurrency tests; it can
    only slow a write down, never change one."""
    delay_ms = os.environ.get("PIPELINE_STATE_TEST_DELAY_MS", "")
    if is_ascii_digits(delay_ms):
        time.sleep(int(delay_ms) / 1000.0)


def load(root: str) -> Optional[dict[str, object]]:
    """The state dict, or None when there is none. An unreadable state refuses every op, because
    no op may overwrite or move a state it cannot read."""
    status, data = checkout.read_state(root)
    if status == "unreadable":
        raise Refused("state file unreadable: %s; nothing written" % state_path(root))
    return data


def save(root: str, data: Mapping[str, object]) -> None:
    tmp = os.path.join(_claude_dir(root), "pipeline_state.tmp.%d" % os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, state_path(root))


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _list_field(data: dict[str, object], key: str) -> list[object]:
    """data[key] as a list, created when absent. Any other shape is refused before anything is
    written; it used to crash with an AttributeError."""
    value = data.setdefault(key, [])
    if not isinstance(value, list):
        raise Refused("state field %s is not a list; nothing written" % key)
    return value


def _object_field(data: dict[str, object], key: str) -> dict[str, object]:
    """data[key] as an object, created when absent; any other shape is refused, as in _list_field."""
    value = data.setdefault(key, {})
    if not isinstance(value, dict):
        raise Refused("state field %s is not an object; nothing written" % key)
    return value


def append_history(data: dict[str, object], phase: str) -> None:
    _list_field(data, "phase_history").append({"phase": phase, "ts": time.time(), "ts_str": _stamp()})
    _object_field(data, "artifacts")["last_ts"] = _stamp()


def last_activity(data: Mapping[str, object]) -> float:
    """Latest phase_history timestamp: TTL and watchdog age measure inactivity, not task length.
    A non-numeric session_ts is refused (it used to crash the comparison below); a non-numeric ts
    in the history is skipped."""
    session_ts = data.get("session_ts", 0) or 0
    if not isinstance(session_ts, (int, float)):
        raise Refused("state field session_ts is not a number")
    latest: float = session_ts
    for entry in as_list(data.get("phase_history", [])):
        ts = entry.get("ts") if isinstance(entry, dict) else None
        if isinstance(ts, (int, float)) and ts > latest:
            latest = ts
    return latest


def _require(data: Optional[dict[str, object]]) -> dict[str, object]:
    if data is None:
        raise Refused("no pipeline state. Run: pipeline-advance.sh init <TIER> <issue>")
    return data


def _branch_exists(root: str, branch: str) -> bool:
    try:
        return subprocess.run(
            ["git", "-C", root, "show-ref", "--verify", "--quiet", "refs/heads/" + branch],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=checkout.GIT_TIMEOUT_SECONDS,
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _park(root: str, data: dict[str, object], reason: str, code_root: str, gitdir: str, branch: str) -> str:
    """Move the slot's state to parked/<issue>-<epoch>[-n].json. Nothing is ever deleted: parking
    keeps the votes and history of a task that was set aside. Parking this checkout's own LEARN
    task would lift its rules, so it needs Stepan's learn_pause grant; pause, init and resume all
    pass through here."""
    conf = cfg.load()
    if conf["tiers"].get(as_str(data.get("tier")), {}).get("learner_writes_code") \
            and checkout.foreign_reason(data, gitdir, branch) == "":
        issue = data.get("issue") or ""
        require_grant(conf, code_root, "learn_pause", issue,
                      '%s #%s is the task in this checkout; Stepan grants pausing it: add %s to "learn_pause" in %s'
                      % (data.get("tier"), issue, issue, conf["grant_file"]), root)
    parked_dir = os.path.join(_claude_dir(root), PARKED_DIR)
    os.makedirs(parked_dir, exist_ok=True)
    base = "%s-%d" % (data.get("issue") or "noissue", int(time.time()))
    key, n = base, 1
    while os.path.exists(os.path.join(parked_dir, key + ".json")):
        n += 1
        key = "%s-%d" % (base, n)
    data = dict(data, parked_reason=reason, parked_branch=branch, parked_ts=time.time())
    with open(os.path.join(parked_dir, key + ".json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.remove(state_path(root))
    checkout.log_event(event="park:" + reason, hook="state.py", checkout=root, issue=str(data.get("issue") or ""))
    print("WARNING: parked #%s %s/%s (%s) as %s" % (data.get("issue") or "-", data.get("tier"), data.get("phase"),
                                                   reason, key), file=sys.stderr)
    return key


def _init_park_reason(root: str, data: Optional[dict[str, object]], gitdir: str, branch: str,
                      conf: cfg.Config) -> Optional[str]:
    """Why init may set the slot's state aside, or None when the slot is free. Refuses when the
    state is this branch's live task."""
    if data is None or data.get("phase") == "done":
        return None
    if data.get("gitdir_at_init") and data["gitdir_at_init"] != gitdir:
        return "foreign"
    recorded = as_str(data.get("branch_at_init"))
    if recorded != branch:
        if _branch_exists(root, recorded):
            return "branch-switched"
        print("WARNING: branch %s of the parked task is gone; if it was renamed: git branch -m <new> %s, "
              "then pipeline-advance.sh resume <key>" % (recorded, recorded), file=sys.stderr)
        return "branch-missing:" + recorded
    idle = int(time.time() - last_activity(data))
    if idle >= conf["state_ttl_hours"] * SECONDS_PER_HOUR:
        return "stale"
    raise Refused("a pipeline is still active here (#%s %s, phase=%s, last activity %ss ago). Finish it, "
                  "or pipeline-advance.sh pause it first." % (data.get("issue"), data.get("tier"), data.get("phase"), idle))


def op_init(root: str, tier: str, issue: str, branch: str, gitdir: str, code_root: str) -> str:
    conf = cfg.load()
    tier_conf = conf["tiers"].get(tier, {})
    if issue and not is_ascii_digits(issue):
        raise Refused("issue must be a GitHub issue number, got %r" % issue)
    # A branch is what identifies the task; branch_at_init must name a task branch.
    if not branch:
        raise Refused("HEAD is detached; check out a branch first")
    if tier_conf.get("requires_issue") and branch in conf["protected_branches"]:
        raise Refused("you are on protected branch '%s'. Create the task branch first: git switch -c <type>/%s-<slug>"
                      % (branch, issue))
    with transaction(root):
        if tier_conf.get("edits_pipeline_core"):
            # Only the main checkout's hooks are live, so core edits anywhere else cannot be checked.
            if os.path.realpath(root) != os.path.realpath(code_root):
                raise Refused("%s tasks run in the main checkout: only its hooks are live" % tier)
            require_grant(conf, code_root, "pipeline_init", issue,
                          '%s #%s needs a grant: Stepan adds %s to "pipeline_init" in %s (main checkout)'
                          % (tier, issue, issue, conf["grant_file"]), root)
        data = load(root)
        reason = _init_park_reason(root, data, gitdir, branch, conf)
        _test_delay()
        # _init_park_reason returns a reason only for a loaded state; the None check is for mypy.
        if reason and data is not None:
            _park(root, data, reason, code_root, gitdir, branch)
        now = time.time()
        state: dict[str, object] = {
            "tier": tier, "phase": "init", "issue": int(issue) if issue else None,
            "branch_at_init": branch, "gitdir_at_init": gitdir, "session_ts": now,
            "phase_history": [{"phase": "init", "ts": now, "ts_str": _stamp()}],
            "artifacts": {"last_ts": _stamp()},
        }
        if tier_conf.get("edits_pipeline_core"):
            append_history(state, "grant:pipeline_init:%s" % issue)
        save(root, state)
    checkout.log_event(event="init", hook="state.py", checkout=root, issue=issue)
    return "initialized"


def op_advance(root: str, expected: str, nxt: str) -> str:
    with transaction(root):
        data = _require(load(root))
        if data.get("phase") != expected:
            raise Conflict("state changed concurrently (now %s)" % data.get("phase"))
        _test_delay()
        data["phase"] = nxt
        append_history(data, nxt)
        save(root, data)
    checkout.log_event(event="advance", hook="state.py", checkout=root, reason=nxt)
    return "advanced to %s" % nxt


def op_vote(root: str, rnd: str, judge: str, verdict: str, agent_id: str = "", path: str = "") -> str:
    with transaction(root):
        data = _require(load(root))
        if data.get("phase") != rnd:
            raise Conflict("not in round %s (now %s)" % (rnd, data.get("phase")))
        votes = _list_field(_object_field(data, "artifacts"), "judge_votes")
        # The handback and SubagentStop paths both report the same agent: one vote per agent and round.
        if agent_id and any(isinstance(v, dict) and v.get("agent_id") == agent_id and v.get("round") == rnd
                            for v in votes):
            return "vote-dup"
        _test_delay()
        votes.append({
            "agent": judge, "verdict": verdict, "round": rnd, "agent_id": agent_id, "path": path,
            "source": "hook", "ts": _stamp(),
        })
        append_history(data, "judge:%s:%s" % (judge, verdict))
        save(root, data)
    return "vote-recorded"


def op_record_spawn(root: str, rnd: str, agent_id: str, judge: str) -> str:
    with transaction(root):
        data = _require(load(root))
        phase = as_str(data.get("phase", ""))
        if phase != rnd or not phase.startswith("judge_"):
            raise Conflict("not in a judge phase (now %s)" % phase)
        _test_delay()
        _object_field(_object_field(data, "artifacts"), "judge_spawns")[agent_id] = judge
        save(root, data)
    return "spawn-recorded"


def op_set_artifact(root: str, key: str, value: str) -> str:
    with transaction(root):
        data = _require(load(root))
        _test_delay()
        _object_field(data, "artifacts")[key] = value
        save(root, data)
    return "artifact %s set" % key


def op_finish(root: str) -> str:
    with transaction(root):
        data = load(root)
        if data is None:
            return "nothing to finish"
        if data.get("phase") != "done":
            raise Refused("phase is %s, not done; state kept" % data.get("phase"))
        os.remove(state_path(root))
    checkout.log_event(event="finish", hook="state.py", checkout=root)
    return "finished"


def op_park(root: str, reason: str, code_root: str, gitdir: str, branch: str) -> str:
    """pause: set the active state aside, own or foreign (a foreign one is what a repository move or
    the v2 migration leaves behind), and free the checkout."""
    with transaction(root):
        data = load(root)
        if data is None or data.get("phase") == "done":
            raise Refused("no active pipeline to pause here")
        if checkout.foreign_reason(data, gitdir, branch) != "":
            reason += "-foreign"
        _test_delay()
        key = _park(root, data, reason, code_root, gitdir, branch)
    return "parked as %s" % key


def _parked_dir(root: str) -> str:
    return os.path.join(_claude_dir(root), PARKED_DIR)


def _parked_keys(root: str) -> list[str]:
    d = _parked_dir(root)
    return sorted(f[:-len(".json")] for f in os.listdir(d) if f.endswith(".json")) if os.path.isdir(d) else []


def _pick_parked(root: str, wanted: str) -> str:
    keys = _parked_keys(root)
    if wanted in keys:
        return wanted
    matches = [k for k in keys if is_ascii_digits(wanted) and k.startswith(wanted + "-")]
    if len(matches) > 1:
        raise Refused("#%s is parked more than once (%s); resume by key" % (wanted, ", ".join(matches)))
    if not matches:
        raise Refused("nothing parked here matches %s (parked: %s)" % (wanted, ", ".join(keys) or "none"))
    return matches[0]


def op_resume(root: str, wanted: str, code_root: str, gitdir: str, branch: str) -> str:
    """Restore a parked state in one transaction. Every refusal comes before anything moves, so a
    refused resume leaves the slot and the parked directory as they were."""
    conf = cfg.load()
    with transaction(root):
        current = load(root)
        slot_reason = None
        if current is not None and current.get("phase") != "done":
            if checkout.foreign_reason(current, gitdir, branch) != "":
                slot_reason = "foreign"
            else:
                idle = int(time.time() - last_activity(current))
                if idle < conf["state_ttl_hours"] * SECONDS_PER_HOUR:
                    raise Refused("#%s is active here; finish or pause #%s first" % (current.get("issue"), current.get("issue")))
                slot_reason = "stale"
        key = _pick_parked(root, wanted)
        path = os.path.join(_parked_dir(root), key + ".json")
        try:
            with open(path, encoding="utf-8") as fh:
                loaded: object = json.load(fh)
        except (OSError, ValueError) as exc:
            raise Refused("parked state %s is unreadable (%s); Stepan inspects it" % (path, exc.__class__.__name__))
        if not isinstance(loaded, dict):
            raise Refused("parked state %s is not a JSON object; Stepan inspects it" % path)
        data: dict[str, object] = loaded
        if not branch or data.get("branch_at_init") != branch:
            raise Refused("%s was started on branch %s; check it out first (now %s)"
                          % (key, data.get("branch_at_init"), branch or "detached HEAD"))
        _test_delay()
        # slot_reason is set only when current was loaded; the None check is for mypy.
        if slot_reason and current is not None:
            _park(root, current, slot_reason, code_root, gitdir, branch)
        # Found in this checkout's own parked directory, so location proves ownership; a different
        # gitdir means the repository moved.
        if data.get("gitdir_at_init") != gitdir:
            data["gitdir_at_init"] = gitdir
            checkout.log_event(event="resume:gitdir-rebased", hook="state.py", checkout=root, issue=str(data.get("issue") or ""))
        for field in ("parked_reason", "parked_branch", "parked_ts"):
            data.pop(field, None)
        append_history(data, "resume")
        save(root, data)
        os.remove(path)
    checkout.log_event(event="resume", hook="state.py", checkout=root, issue=str(data.get("issue") or ""))
    return "resumed %s" % key


def _parked_at(parked_ts: object) -> str:
    """A missing, non-numeric, non-finite or out-of-range time is "?", not the 1970 epoch or a
    traceback: json.load accepts Infinity, NaN, 1e400 (inf) and ints above the float maximum, and
    localtime raises OverflowError or ValueError for each of them inside the try. No numeric
    pre-check sits outside it: math.isfinite on such an int raises OverflowError itself."""
    if not isinstance(parked_ts, (int, float)) or isinstance(parked_ts, bool):
        return "?"
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(parked_ts))
    except (OverflowError, ValueError, OSError):
        return "?"


def op_parked(root: str) -> str:
    lines: list[str] = []
    for key in _parked_keys(root):
        try:
            with open(os.path.join(_parked_dir(root), key + ".json"), encoding="utf-8") as fh:
                d: object = json.load(fh)
        except (OSError, ValueError):
            lines.append("%s (unreadable)" % key)
            continue
        if not isinstance(d, dict):
            lines.append("%s (not a JSON object)" % key)
            continue
        lines.append("#%s %s/%s (%s, key %s, parked %s, %s)" % (
            d.get("issue") or "-", d.get("tier"), d.get("phase"), d.get("branch_at_init"), key,
            _parked_at(d.get("parked_ts")), d.get("parked_reason")))
    return "\n".join(lines)


OPS: dict[str, tuple[Callable[..., str], int, int]] = {
    "init": (op_init, 6, 6),
    "advance": (op_advance, 3, 3),
    "vote": (op_vote, 4, 6),
    "record_spawn": (op_record_spawn, 4, 4),
    "set_artifact": (op_set_artifact, 3, 3),
    "finish": (op_finish, 1, 1),
    "park": (op_park, 5, 5),
    "resume": (op_resume, 5, 5),
    "parked": (op_parked, 1, 1),
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in OPS:
        print(__doc__, file=sys.stderr)
        return EXIT_REFUSED
    fn, least, most = OPS[argv[1]]
    args = argv[2:]
    if not least <= len(args) <= most:
        print("ERROR: state.py %s takes %d-%d arguments, got %d" % (argv[1], least, most, len(args)), file=sys.stderr)
        return EXIT_REFUSED
    try:
        result = fn(*args)
        if result:
            print(result)
    except StateLockTimeout as exc:
        checkout.log_event(event="lock-timeout", hook="state.py", checkout=args[0], reason=argv[1])
        print("ERROR: %s" % exc, file=sys.stderr)
        return EXIT_LOCK_TIMEOUT
    except Refused as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return exc.code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
