#!/usr/bin/env python3
"""Shared parsing for hook inputs, so every hook identifies roles and verdicts the same way.

  hookio.py role_team            stdin: PreToolUse JSON -> "<team>/<file>" of the spawned agent (e.g. dev/coder.md;
                                 the team may be the sentinel !path or !type) or ""
  hookio.py judge_vote           stdin: SubagentStop JSON ->
                                 "<judge-key>|<PASS|FAIL|UNKNOWN>|<agent_id>|<transcript lines>|<true|false>"
                                 (the last field: the transcript already holds a SubagentHandback call)
  hookio.py judge_vote_post      stdin: PostToolUse(Agent) JSON -> "<judge-key>|<verdict>"
  hookio.py handback_vote <state file>
                                 stdin: PreToolUse(SubagentHandback) JSON ->
                                 "<outcome>|<judge-key>|<verdict>|<agent_id>|<role_source>|<transcript_kind>"
                                 outcome: vote | role-unknown | vote-ignored:not-a-judge |
                                 vote-ignored:bad-agent-id | verdict-unknown
  hookio.py spawn_info           stdin: PostToolUse(Agent) JSON -> "<judge-key>|<agent_id>" of a launched judge
  hookio.py bg_running           stdin: Stop JSON -> "<running subagents> <background tasks>"
  hookio.py field <dotted.path>  stdin: any hook JSON -> value or ""

Role detection rule (deliberately strict): the role is the agent file named in the LEADING
"Read .claude/agents/<team>/<file>.md first" instruction of the spawn prompt when that exact file
(directory and case) exists in the main checkout's agent tree, and its team is the directory it lives
in; without that instruction, the subagent_type when it names an agent's frontmatter name. A
subagent_type that names a known agent must agree with the prompt's role. A claim that is not true
yields the sentinel team !path (no such file at that path) or !type (subagent_type names another
agent). Other agent files mentioned later in the prompt are context, not the role.
Verdict rule: the last line that is exactly a verdict: "PASS", "FAIL", "PASS: ...", "FAIL: ...",
"PASS - ...", "FAIL - N issues", or "VERDICT: PASS|FAIL" (markdown markers stripped). Uppercase only,
so prose like "pass-through" never counts.
"""
import json
import os
import re
import sys
from typing import Callable, Iterator

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import cfg  # noqa: E402
import checkout  # noqa: E402
from pl_jsonshape import as_list, as_object, as_str  # noqa: E402

# agent_id becomes part of a transcript file path and the vote dedupe key.
AGENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# Case-insensitive, so both groups are only a claim: role_spec resolves them against the scanned tree.
ROLE_RE = re.compile(r"""^\s*Read\s+[`"']?\.claude/agents/([a-z0-9-]+)/([a-z0-9-]+\.md)[`"']?\s+first""", re.I)
# Case-sensitive on purpose: the index holds names exactly as the file system reports them.
TEAM_DIR_RE = re.compile(r"[a-z0-9-]+")
ROLE_FILE_RE = re.compile(r"[a-z0-9-]+\.md")
NAME_RE = re.compile(r"^name:\s*([a-z0-9-]+)\s*$", re.M)
FRONTMATTER_HEAD_BYTES = 400
# Never produced by TEAM_DIR_RE, so a sentinel never equals a tier's team; never empty, because an
# empty team means "not a role", which the gate allows.
TEAM_BAD_PATH = "!path"
TEAM_BAD_TYPE = "!type"
VERDICT_RE = re.compile(r"^(?:VERDICT:\s*)?(PASS|FAIL)(?:\s*$|\s*[:\-]|\s+-)")


def _obj(value: object, what: str) -> dict[str, object]:
    """A JSON object; a missing or empty value reads as {}. Any other value is refused with a message,
    because the parsing code always crashed on it and the phase gate must keep blocking then."""
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    raise ValueError("%s is not a JSON object" % what)


def _text(value: object, what: str) -> str:
    """A string; a missing or empty value reads as "". Any other value is refused, as in _obj."""
    if isinstance(value, str):
        return value
    if not value:
        return ""
    raise ValueError("%s is not a string" % what)


AgentPair = tuple[str, str]


def _raise_oserror(err: OSError) -> None:
    raise err


def _stray_role_files(top: str) -> list[str]:
    """Every .md below `top` (a directory that is not itself a team directory, or a team directory's
    subdirectory). Claude Code registers agents recursively, so such a file would be a spawnable agent
    the gates do not know."""
    found: list[str] = []
    for root, _dirs, files in os.walk(top, onerror=_raise_oserror):
        found.extend(os.path.join(root, f) for f in files if f.endswith(".md") and not f.startswith("_"))
    return found


def _frontmatter_name(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        m = NAME_RE.search(fh.read(FRONTMATTER_HEAD_BYTES))
    return m.group(1).lower() if m else ""


def agent_index() -> tuple[frozenset[AgentPair], dict[str, AgentPair]]:
    """(every (team, file) of the agent tree, lower-cased frontmatter name -> (team, file)).

    Agents always come from the main checkout, like the hook code itself. Names come from os.listdir,
    so they carry the real case on a case-insensitive file system too. An unreadable tree raises
    OSError and a tree with no role file or with a stray one raises ValueError: the callers map both to
    a block or to "no vote", because treating every role as unknown would allow it."""
    base = os.path.join(checkout.code_root(), ".claude", "agents")
    pairs: set[AgentPair] = set()
    names: dict[str, AgentPair] = {}
    stray: list[str] = []
    for team in sorted(os.listdir(base)):
        team_path = os.path.join(base, team)
        if not os.path.isdir(team_path):
            if team.endswith(".md") and not team.startswith("_"):
                stray.append(team_path)
            continue
        if not TEAM_DIR_RE.fullmatch(team):
            stray.extend(_stray_role_files(team_path))
            continue
        for f in sorted(os.listdir(team_path)):
            path = os.path.join(team_path, f)
            if os.path.isdir(path):
                stray.extend(_stray_role_files(path))
            elif f.startswith("_") or not f.endswith(".md"):
                continue
            elif not ROLE_FILE_RE.fullmatch(f):
                stray.append(path)
            else:
                pairs.add((team, f))
                name = _frontmatter_name(path)
                if name:
                    # First one wins in sorted order; duplicates are a CI failure (run.sh S1a).
                    names.setdefault(name, (team, f))
    if stray:
        raise ValueError("agent files outside .claude/agents/<team>/<file>.md (lower-case names): %s"
                         % ", ".join(sorted(stray)))
    if not pairs:
        raise ValueError("no agent role files under %s" % base)
    return frozenset(pairs), names


def role_spec(prompt: object, subtype: object) -> AgentPair:
    """(team, file) of a spawned role: team is a real directory, TEAM_BAD_PATH, TEAM_BAD_TYPE, or ""
    (not a role, file "" too)."""
    m = ROLE_RE.search(_text(prompt, "prompt"))
    sub_name = _text(subtype, "subagent_type")
    if not m and not sub_name:
        return "", ""
    pairs, names = agent_index()
    # Lower-cased because whether Claude Code matches subagent_type case-insensitively is not
    # verified; an unknown name (general-purpose, Explore, fork) is ignored.
    sub = names.get(sub_name.lower()) if sub_name else None
    if not m:
        return sub if sub else ("", "")
    claim = (m.group(1), m.group(2))
    if claim not in pairs:
        same_name = [f for _team, f in pairs if f.lower() == claim[1].lower()]
        return TEAM_BAD_PATH, same_name[0] if len(same_name) == 1 else claim[1]
    if sub and sub != claim:
        return TEAM_BAD_TYPE, claim[1]
    return claim


def role_from(prompt: object, subtype: object) -> str:
    """The role file, or "" when the claim is not true: a vote under a false identity never counts."""
    team, role_file = role_spec(prompt, subtype)
    return role_file if team and not team.startswith("!") else ""


def verdict_from(text: object) -> str:
    for line in reversed(_text(text, "report").splitlines()):
        s = line.strip().strip("#").strip().strip("*").strip().strip("`").strip()
        m = VERDICT_RE.match(s)
        if m:
            return m.group(1)
    return "UNKNOWN"


def judge_key(role_file: str) -> str:
    try:
        conf = cfg.load()
    except (OSError, ValueError):
        return ""
    for key, f in conf.get("judge_agents", {}).items():
        if f == role_file:
            return key
    return ""


def _records(path: str) -> Iterator[dict[str, object]]:
    """The JSON records of a transcript, read lazily; lines that are not JSON are skipped."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                rec: object = json.loads(line)
            except ValueError:
                continue
            yield _obj(rec, "transcript record")


def _content_text(content: object, block_text: Callable[[dict[str, object]], str]) -> str:
    """A message content: a string, or the text of each object block joined by spaces."""
    if isinstance(content, str):
        return content
    return " ".join(block_text(b) for b in map(as_object, as_list(content)) if b is not None)


def first_user_text(path: str) -> str:
    try:
        for rec in _records(path):
            if rec.get("type") != "user":
                continue
            content = _obj(rec.get("message", {}), "message").get("content")
            return _content_text(content, lambda b: as_str(b.get("text")))
    except OSError:
        pass
    return ""


def _block_text(block: dict[str, object]) -> str:
    """Text of one assistant content block. A background agent delivers its final report as the
    `message` input of a SubagentHandback tool call rather than as a text block."""
    if block.get("type") == "text":
        return as_str(block.get("text"))
    if block.get("type") == "tool_use" and block.get("name") == "SubagentHandback":
        return as_str(_obj(block.get("input"), "tool_use input").get("message"))
    return ""


def last_assistant_text(path: str) -> str:
    last = ""
    try:
        for rec in _records(path):
            if rec.get("type") != "assistant":
                continue
            t = _content_text(_obj(rec.get("message", {}), "message").get("content"), _block_text)
            if t.strip():
                last = t
    except OSError:
        pass
    return last


def valid_agent_id(agent_id: str) -> bool:
    return bool(AGENT_ID_RE.match(agent_id))


def transcript_facts(path: str) -> tuple[int, bool]:
    """(line count, whether an assistant record already holds a SubagentHandback call): logged so
    a verdict missing because the transcript lagged behind the hook is visible."""
    lines, handback = 0, False
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                lines += 1
                if '"SubagentHandback"' in line:
                    try:
                        loaded: object = json.loads(line)
                    except ValueError:
                        continue
                    rec = _obj(loaded, "transcript record")
                    content = _obj(rec.get("message", {}), "message").get("content") if rec.get("type") == "assistant" else None
                    handback = handback or any(
                        b is not None and b.get("type") == "tool_use" and b.get("name") == "SubagentHandback"
                        for b in map(as_object, as_list(content)))
    except OSError:
        pass
    return lines, handback


def subagent_transcript(d: dict[str, object], agent_id: str) -> tuple[str, str]:
    """(path, kind) of the subagent's own transcript. Observed with Claude Code 2.1.267 (2026-10-27):
    a PreToolUse inside a subagent receives the parent session's transcript_path, so the subagent's
    transcript is <session dir>/subagents/agent-<id>.jsonl (kind "main"). The other layouts stay
    as fallbacks, tried in order."""
    tpath = as_str(d.get("transcript_path"))
    session = as_str(d.get("session_id"))
    own = "agent-%s.jsonl" % agent_id
    candidates: list[tuple[str, str]] = []
    explicit = as_str(d.get("agent_transcript_path"))
    if explicit:
        candidates.append((explicit, "explicit"))
    if tpath and os.path.basename(tpath) == own:
        candidates.append((tpath, "subagent"))
    if tpath and session:
        candidates.append((os.path.join(os.path.dirname(tpath), session, "subagents", own), "main"))
    if tpath:
        candidates.append((os.path.join(os.path.dirname(tpath), own), "sibling"))
    for path, kind in candidates:
        if os.path.isfile(path):
            return path, kind
    return "", "none"


def spawn_map(state_file: str) -> dict[str, object]:
    try:
        with open(state_file, encoding="utf-8") as fh:
            data: object = json.load(fh)
    except (OSError, ValueError):
        return {}
    artifacts = as_object((as_object(data) or {}).get("artifacts", {})) or {}
    return as_object(artifacts.get("judge_spawns", {})) or {}


def handback_vote(d: dict[str, object], state_file: str) -> list[str]:
    agent_id = as_str(d.get("agent_id"))
    if not valid_agent_id(agent_id):
        return ["vote-ignored:bad-agent-id", "", "", "", "none", "none"]
    message = (as_object(d.get("tool_input")) or {}).get("message", "")
    verdict = verdict_from(as_str(message))
    path, kind = subagent_transcript(d, agent_id)
    if path:
        role = role_from(first_user_text(path), "")
        role_source, key, found_role = "transcript", judge_key(role), bool(role)
    else:
        key = as_str(spawn_map(state_file).get(agent_id, ""))
        role_source, found_role = ("spawn_map", True) if key else ("none", False)
    if not found_role:
        outcome = "role-unknown"
    elif not key:
        outcome = "vote-ignored:not-a-judge"
    elif verdict == "UNKNOWN":
        outcome = "verdict-unknown"
    else:
        outcome = "vote"
    return [outcome, key, verdict, agent_id, role_source, kind]


def spawn_info(d: dict[str, object]) -> list[str]:
    ti = as_object(d.get("tool_input")) or {}
    key = judge_key(role_from(ti.get("prompt", ""), ti.get("subagent_type", "")))
    resp = as_object(d.get("tool_response")) or {}
    agent_id = resp.get("agentId") or resp.get("agent_id") or ""
    if not key or not isinstance(agent_id, str) or not valid_agent_id(agent_id):
        return ["", ""]
    return [key, agent_id]


def bg_running(d: dict[str, object]) -> tuple[int, int]:
    """Running subagents only: a dev server, monitor or cron must not keep Stop open forever."""
    tasks = d.get("background_tasks")
    if not isinstance(tasks, list):
        return 0, 0
    running = sum(1 for t in tasks if isinstance(t, dict) and t.get("type") == "subagent" and t.get("status") == "running")
    return running, len(tasks)


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else ""
    try:
        raw: object = json.load(sys.stdin)
    except ValueError:
        raw = {}
    d = as_object(raw) or {}
    if cmd == "role_team":
        ti = _obj(d.get("tool_input", {}), "tool_input")
        team, role_file = role_spec(ti.get("prompt", ""), ti.get("subagent_type", ""))
        print("%s/%s" % (team, role_file) if role_file else "")
    elif cmd == "judge_vote":
        if d.get("hook_event_name") not in (None, "", "SubagentStop"):
            print("||||false")
            return 0
        tpath = _text(d.get("agent_transcript_path", ""), "agent_transcript_path")
        prompt = first_user_text(tpath) if tpath else ""
        role = role_from(prompt, d.get("agent_type", ""))
        key = judge_key(role)
        verdict = verdict_from(d.get("last_assistant_message"))
        # last_assistant_message can be present yet carry no verdict (the report went through
        # SubagentHandback), so UNKNOWN there falls back to the transcript.
        if verdict == "UNKNOWN" and tpath:
            verdict = verdict_from(last_assistant_text(tpath))
        agent_id = as_str(d.get("agent_id"))
        lines, handback = transcript_facts(tpath) if tpath else (0, False)
        print("|".join([key, verdict if key else "", agent_id if valid_agent_id(agent_id) else "",
                        str(lines), "true" if handback else "false"]))
    elif cmd == "handback_vote":
        print("|".join(handback_vote(d, argv[2] if len(argv) > 2 else "")))
    elif cmd == "bg_running":
        print("%d %d" % bg_running(d))
    elif cmd == "spawn_info":
        print("|".join(spawn_info(d)))
    elif cmd == "judge_vote_post":
        ti = _obj(d.get("tool_input", {}), "tool_input")
        role = role_from(ti.get("prompt", ""), ti.get("subagent_type", ""))
        key = judge_key(role)
        resp = d.get("tool_response", {})
        content = resp.get("content", []) if isinstance(resp, dict) else []
        if isinstance(content, list):
            txt = "\n".join(as_str(b.get("text")) for b in map(as_object, content) if b is not None)
        else:
            txt = str(content)
        print("%s|%s" % (key, verdict_from(txt) if key else ""))
    elif cmd == "field":
        cur: object = d
        for part in (argv[2] if len(argv) > 2 else "").split("."):
            cur = cur.get(part, "") if isinstance(cur, dict) else ""
        print(cur if not isinstance(cur, (dict, list)) else json.dumps(cur))
    else:
        print("unknown command", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
