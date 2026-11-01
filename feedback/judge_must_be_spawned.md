# Judge votes MUST come from spawned agents, never inline

**Why:** In more than one task the orchestrator ran `pipeline-advance.sh judge <type> PASS`
directly, without actually spawning the judge agents. That is the same class of failure as
letting a coder bypass the rules and a judge rubber-stamp - nobody actually reviewed the code.
The `agent_roles_mandatory` rule already covered this and was ignored under time pressure.

**How to apply:**
- BEFORE any judge vote is recorded, spawn all three judges of the tier in ONE message (parallel).
  Dev tiers (HOTFIX/TASK/PROJECT/LEARN):

  ```
  Agent(prompt="Read .claude/agents/dev/judge-security.md first. Then review: <diff>")
  Agent(prompt="Read .claude/agents/dev/judge-architecture.md first. Then review: <diff>")
  Agent(prompt="Read .claude/agents/dev/judge-operations.md first. Then review: <diff>")
  ```

  Content tiers (MODULE/LESSON):

  ```
  Agent(prompt="Read .claude/agents/content/judge-accuracy.md first. Then review: <lesson>")
  Agent(prompt="Read .claude/agents/content/judge-pedagogy.md first. Then review: <lesson>")
  Agent(prompt="Read .claude/agents/content/judge-assessment.md first. Then review: <lesson>")
  ```

  Design tier (DESIGN):

  ```
  Agent(prompt="Read .claude/agents/design/judge-usability.md first. Then review: <flows or pages + validator output>")
  Agent(prompt="Read .claude/agents/design/judge-accessibility.md first. Then review: <flows or pages + validator output>")
  Agent(prompt="Read .claude/agents/design/judge-consistency.md first. Then review: <flows or pages + validator output>")
  ```
- Record only the verdict each agent actually returns (the judge-count hook does this).
- All three in ONE message - never three separate messages (that breaks the parallelism and
  wastes time).
- Under time pressure - still spawn them. Two minutes of real judging prevents shipped bugs.
- TASK/PROJECT must have judges. Never skip them and never force-clear the state file to bypass
  the completion gate.
