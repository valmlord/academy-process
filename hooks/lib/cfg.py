#!/usr/bin/env python3
"""Query helper for .claude/pipeline.json so bash hooks never hardcode tiers/phases/judges.

Usage: cfg.py <command> [args]
  tiers                         space-separated tier names
  phases <TIER>                 space-separated phases
  judges <TIER>                 space-separated judge keys
  team <TIER>                   the tier's team, or an empty line when the tier or the key is missing
  judge_phases <TIER>           judge phases (phase names starting with judge_)
  all_judges                    "key=file" pairs for every judge
  gate <agent_file>             "<first> <last>" phase window for an agent file, or empty
  tier_flag <TIER> <flag>       prints 1 if flag is true for tier, else 0
  get <key>                     top-level scalar or list (lists space-separated)
"""
import json
import os
import sys
from typing import Mapping, TypedDict, cast

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.normpath(os.path.join(HERE, "..", "..", "pipeline.json"))


class TierConfig(TypedDict, total=False):
    team: str
    requires_issue: bool
    phases: list[str]
    judges: list[str]
    edits_pipeline_core: bool
    learner_writes_code: bool


class _RequiredConfig(TypedDict):
    tiers: dict[str, TierConfig]
    judge_agents: dict[str, str]
    agent_gates: dict[str, object]
    grant_file: str
    state_ttl_hours: float
    protected_branches: list[str]
    pipeline_core_files: list[str]
    protected_files: list[str]
    learn_tier_editable_paths: list[str]
    learn_tier_test_globs: list[str]
    learn_tier_code_dirs: list[str]


class Config(_RequiredConfig, total=False):
    # Read with .get() and a default; each caller checks the value's type itself.
    hook_log_max_bytes: object
    state_lock_timeout_seconds: object
    watchdog_minutes: object
    human_wait_phases: object


class ConfigError(ValueError):
    """pipeline.json lacks a key the hooks use, or holds it in another shape. A ValueError, so the
    existing `except (OSError, ValueError)` handlers treat it like unreadable JSON."""


STR_LIST_KEYS = ("protected_branches", "pipeline_core_files", "protected_files", "learn_tier_editable_paths",
                 "learn_tier_test_globs", "learn_tier_code_dirs")
TIER_FLAG_KEYS = ("requires_issue", "edits_pipeline_core", "learner_writes_code")


def _is_str_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _validate(data: object) -> Config:
    if not isinstance(data, dict):
        raise ConfigError("%s is not a JSON object" % CFG_PATH)
    tiers = data.get("tiers")
    if not isinstance(tiers, dict):
        raise ConfigError("%s: tiers must be an object" % CFG_PATH)
    for name, tier in tiers.items():
        if not isinstance(tier, dict):
            raise ConfigError("%s: tiers.%s must be an object" % (CFG_PATH, name))
        for key in ("phases", "judges"):
            if key in tier and not _is_str_list(tier[key]):
                raise ConfigError("%s: tiers.%s.%s must be a list of strings" % (CFG_PATH, name, key))
        if "team" in tier and not isinstance(tier["team"], str):
            raise ConfigError("%s: tiers.%s.team must be a string, not %s"
                              % (CFG_PATH, name, type(tier["team"]).__name__))
        # Exact type: a string "false" or a 0/1 would be truthy or falsy by accident, and a truthy
        # edits_pipeline_core opens core writes.
        for key in TIER_FLAG_KEYS:
            if key in tier and type(tier[key]) is not bool:
                raise ConfigError("%s: tiers.%s.%s must be true or false, not %s"
                                  % (CFG_PATH, name, key, type(tier[key]).__name__))
    judge_agents = data.get("judge_agents")
    if not isinstance(judge_agents, dict) or not all(isinstance(v, str) for v in judge_agents.values()):
        raise ConfigError("%s: judge_agents must map judge keys to file names" % CFG_PATH)
    if not isinstance(data.get("agent_gates"), dict):
        raise ConfigError("%s: agent_gates must be an object" % CFG_PATH)
    if not isinstance(data.get("grant_file"), str):
        raise ConfigError("%s: grant_file must be a string" % CFG_PATH)
    ttl = data.get("state_ttl_hours")
    if not isinstance(ttl, (int, float)) or isinstance(ttl, bool):
        raise ConfigError("%s: state_ttl_hours must be a number" % CFG_PATH)
    for key in STR_LIST_KEYS:
        if not _is_str_list(data.get(key)):
            raise ConfigError("%s: %s must be a list of strings" % (CFG_PATH, key))
    # mypy cannot narrow a dict to a TypedDict. Checked above: every key of _RequiredConfig and every
    # TierConfig key that is present. Not checked: the optional Config keys, declared as object
    # because their readers check them.
    return cast(Config, data)


def load() -> Config:
    with open(CFG_PATH, encoding="utf-8") as fh:
        data: object = json.load(fh)
    return _validate(data)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    cfg = load()
    cmd, args = argv[1], argv[2:]
    tiers = cfg["tiers"]
    if cmd == "tiers":
        print(" ".join(tiers.keys()))
    elif cmd == "phases":
        print(" ".join(tiers.get(args[0], {}).get("phases", [])))
    elif cmd == "judges":
        print(" ".join(tiers.get(args[0], {}).get("judges", [])))
    elif cmd == "team":
        print(tiers.get(args[0], {}).get("team", ""))
    elif cmd == "judge_phases":
        print(" ".join(p for p in tiers.get(args[0], {}).get("phases", []) if p.startswith("judge_")))
    elif cmd == "all_judges":
        print(" ".join("%s=%s" % (k, v) for k, v in cfg["judge_agents"].items()))
    elif cmd == "gate":
        w = cfg["agent_gates"].get(args[0], "")
        print(" ".join(w) if isinstance(w, list) else w)
    elif cmd == "gated_agents":
        print(" ".join(k for k in cfg["agent_gates"] if not k.startswith("_")))
    elif cmd == "tier_flag":
        flags: Mapping[str, object] = tiers.get(args[0], {})
        print("1" if flags.get(args[1]) else "0")
    elif cmd == "get":
        top: Mapping[str, object] = cfg
        val = top.get(args[0], "")
        print(" ".join(map(str, val)) if isinstance(val, list) else val)
    else:
        print("unknown command: %s" % cmd, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
