# Agents MUST load their role files - not optional

**Why:** A generic subagent spawned without its role file skips the project's rules. In one
real incident a coder that never loaded its role file created a heavy object per-request inside
a loop - a rule its role file explicitly forbids - and leaked memory until the host nearly
crashed; the judges rubber-stamped PASS without loading their own role file that says "check
for resource leaks". Two roles skipped their files; one bug took the host down.

**How to apply:**
- ALWAYS spawn as `Agent(prompt="Read .claude/agents/<team>/<role>.md first. Then: <task>")`, with the
  directory the file really lives in (the hooks deny a path that does not exist).
- NEVER rely on a bare built-in `subagent_type` - that is a generic agent with none of the
  project's rules and checklists.
- For judges: `Agent(prompt="Read .claude/agents/dev/judge-security.md first. Then: <review>")`,
  and likewise for the other judges of the tier (`.claude/pipeline.json`).
- NEVER record a judge PASS inline without actually spawning the judge agents.
- Under time pressure - still load the files. Ten seconds of reading prevents the class of
  bug that takes a host down.

**Key distinction:**
- bare `subagent_type` → generic agent, no project rules.
- `Agent(prompt="Read .claude/agents/<team>/<role>.md first...")` → the role agent with its rules.
