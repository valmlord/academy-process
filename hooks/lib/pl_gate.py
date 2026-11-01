"""Shared parts of the two PreToolUse gate scripts (pl_write_gate.py, pl_shell_guard.py).

Verdict contract with the .sh wrappers: exit 0 = allow; exit 2 with stdout "<log reason>\\x1f<message>"
= block; anything else is a crash, which the wrapper turns into a block. CPython itself exits 2 when
it cannot open a script, so the wrappers count rc 2 as a verdict only when stdout holds the \\x1f.
"""
import json
import sys
from typing import Callable, Mapping

import cfg
from pl_jsonshape import as_object

VERDICT_SEP = "\x1f"
EXIT_BLOCK = 2


class Blocked(Exception):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(reason, message)
        self.reason = reason
        self.message = message


def tier_of(status: str) -> str:
    """The tier of an own active state (own:<tier>:<phase>), else ""."""
    return status.split(":")[1] if status.startswith("own:") else ""


def has_flag(conf: Mapping[str, object], tier: str, flag: str) -> bool:
    """A malformed tiers section raises, so the gate crashes (blocks) instead of reading it as false."""
    if not tier:
        return False
    tiers = as_object(conf["tiers"])
    if tiers is None:
        raise cfg.ConfigError("%s: tiers is not an object" % cfg.CFG_PATH)
    tier_conf = as_object(tiers.get(tier, {}))
    if tier_conf is None:
        raise cfg.ConfigError("%s: tiers.%s is not an object" % (cfg.CFG_PATH, tier))
    return bool(tier_conf.get(flag))


def read_hook_input() -> dict[str, object]:
    """The hook JSON from stdin. Strict UTF-8: a lenient decode could hand the guard a command text
    that differs from what the shell runs, so a bad byte raises (a crash, i.e. a block). Empty input,
    invalid JSON or a non-object are {}, as the gates always treated them."""
    raw = sys.stdin.buffer.read().decode("utf-8")
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return as_object(data) or {}


def run(decide: Callable[[], None]) -> None:
    """Exit with the verdict of decide. Only Blocked is caught: any other exception ends in a
    traceback and CPython's exit 1, which the wrapper maps to a crash."""
    try:
        decide()
    except Blocked as exc:
        print("%s%s%s" % (exc.reason, VERDICT_SEP, exc.message))
        sys.exit(EXIT_BLOCK)
    sys.exit(0)
