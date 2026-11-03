# Pipeline state machine

Source of truth: `.claude/pipeline.json` (tiers, phases, judges, agent gates). This file explains
the intent; if they disagree, the JSON wins and this file is a bug.

## Driving it
```
bash .claude/hooks/pipeline-advance.sh init <TIER> <issue>
bash .claude/hooks/pipeline-advance.sh <next-phase>
bash .claude/hooks/pipeline-advance.sh compound skip "reason"
bash .claude/hooks/pipeline-advance.sh pr <url> | pr skip "reason"
bash .claude/hooks/pipeline-advance.sh notify
bash .claude/hooks/pipeline-advance.sh status          # JSON on stdout, parked states on stderr
bash .claude/hooks/pipeline-advance.sh pause           # park the active state
bash .claude/hooks/pipeline-advance.sh resume <issue|key>
bash .claude/hooks/pipeline-advance.sh parked
bash .claude/hooks/pipeline-advance.sh worktrees [<path>]   # unsaved process work in linked worktrees
```
Always run the main checkout's copy, in worktree sessions too: `bash "<main checkout>/.claude/hooks/pipeline-advance.sh"`,
the path a worktree session's session-start text names, or
`bash "$(git rev-parse --path-format=absolute --git-common-dir)/../.claude/hooks/pipeline-advance.sh"`.
The copy under a worktree's own `.claude/` refuses by design. `worktrees` exits 0 when no linked
worktree holds unsaved process work, 1 when it prints findings, 2 when the report cannot run; `status`
prints the same lines on stderr.

## State per checkout
- Hooks, `pipeline.json` and agents come from the main checkout; only the state is per checkout.
  The checkout is the registered worktree containing the hook input `cwd` (linked worktrees count
  only outside the main tree or under `.claude/worktrees/`); anything else uses the main checkout.
- Files (all git-ignored, prefix `.claude/pipeline_state`): `pipeline_state.json` (the active
  state), `pipeline_state.flock` (lock, never deleted), `pipeline_state.parked/<key>.json`.
- Every write is one locked transaction in `lib/state.py` (flock, atomic replace); `advance` is a
  compare-and-set. A lock timeout writes nothing and exits 75.
- Ownership: a state is own when its `gitdir_at_init` equals this checkout's git dir; a legacy
  state without it is own only on its `branch_at_init`. A foreign state is treated as absent by
  every gate.
- TTL (`state_ttl_hours`) and the watchdog measure time since the last `phase_history` entry.
- Linked worktree (#89, ADR-0005 item 12): before taking the lock, `init` creates the worktree's
  `.claude` as a process worktree of the main checkout's process clone, on a process branch named like
  the product branch and cut from process `origin/main`, or re-checks one an earlier init left; it
  refuses a protected branch, a branch name that would shadow another ref (`origin/...`, `refs/...`),
  a `.claude` that is not such a worktree, one on another process branch
  or tracking a protected branch, and a half-created one, and PIPELINE is refused before anything is
  created.
- A worktree session does not load the process `CLAUDE.md`; the SessionStart hook
  (`session-context.sh`, no matcher) injects a short text naming the main checkout's
  `.claude/CLAUDE.md`, the hook probe and the worktree rules.

## init, pause, resume
`init <TIER> <issue>` decides under the lock, first matching row wins:

| Situation | Decision |
|---|---|
| HEAD detached | refuse |
| issue tier on a protected branch | refuse |
| PIPELINE outside the main checkout | refuse |
| PIPELINE without `pipeline_init` grant for the issue | refuse (exit 4) |
| no state, or phase `done` | init |
| state from another checkout (`gitdir_at_init` differs) | park `foreign`, init |
| state's branch differs, branch exists | park `branch-switched`, init |
| state's branch differs, branch is gone | park `branch-missing:<b>`, init |
| same branch, inactive past TTL | park `stale`, init |
| same branch, active | refuse (pause it first) |

Parking an own LEARN state (by any row, `pause` or `resume`) needs a `learn_pause` grant for its
issue (exit 4 without). Parked keys are `<issue>-<epoch>` with `-2`, `-3` on collision, so a
second pause never overwrites the first. `pause` parks an active state, own or foreign.
`resume <issue|key>` refuses while an own state is active within TTL, when the issue matches
several keys or none, and when the current branch is not the parked state's branch; only then
does it park a stale or foreign slot state and restore the parked one (rebasing
`gitdir_at_init` to this checkout, history entry `resume`). Parked states are inert for every gate.

## Grant file
`.claude/settings.pipeline-grant.json` in the main checkout, written only by Stepan:
`{"version": 1, "pipeline_init": [<issues>], "learn_pause": [<issues>]}`. Read on every decision;
an unknown key, a non-integer or a non-list grants nothing and the refusal names the problem.

## Dev tiers
- **HOTFIX**: coder -> tester -> judges -> commit -> pr. Still three judges.
- **TASK / PROJECT**: researcher -> architect -> judge_design (3 judges on the design) -> planner
  (plan file) -> coder -> tester (real runs: unit, compose, integration, e2e) -> judge_code
  (3 judges on diff + test report) -> compound (write lessons learned) -> commit -> pr.
- **PIPELINE**: like PROJECT, for changes to pipeline core (`.claude/hooks/`, `pipeline.json`,
  `settings*`). The only tier that may write core, by tool or by shell; main checkout only, and
  `init` needs Stepan's grant.
- **LEARN**: like TASK, but the `learner` phase replaces `coder`. Stepan implements the plan by
  hand; the mentor helps on request; judges review in mentor mode.

## Content tiers
- **MODULE**: content-researcher -> curriculum-architect -> judge_design (accuracy, pedagogy,
  assessment on the module design) -> planner -> author (lesson-author + practice-designer in
  parallel, per lesson) -> student (honest + cheater run per lesson) -> validate
  (`pnpm content:validate`) -> judge_content -> compound -> commit -> pr.
- **LESSON**: researcher -> author -> student -> validate -> judge_content -> commit -> pr.

## Design tier
- **DESIGN**: ux-researcher (research) -> ux-researcher (flows, IA, scope) -> judge_design
  (usability, accessibility, consistency on the flows; the orchestrator passes the validator output)
  -> planner (per-page work items) -> author (ui-designer first when tokens or components change, then
  product-designer; sequential, because prototypes build on the tokens) -> judge_ux (the same three
  judges on prototypes, tokens, acceptance notes and `scripts/design_tokens.py check design`) ->
  compound -> commit -> pr. A design role is spawnable only in DESIGN (team check), and content or dev
  gated roles never in DESIGN.

## Other
- **RESEARCH**: researcher -> notify. No code change, no issue required.
- **RELEASE**: bump version, update CHANGELOG, tag, `docker compose up -d --build --wait`, smoke test.

## Judge rounds
Votes are recorded only by hooks, from spawned judges: PreToolUse on `SubagentHandback` (primary,
verdict from the report message), SubagentStop (fallback, verdict from the transcript) and
PostToolUse on the spawn (synchronous harnesses; it also records the judge spawn map). One vote per
agent id and round, whichever path comes first.

Each judge phase is a round. All judges of the tier must PASS in that round; a PASS from an
earlier round does not count. FAIL -> judge writes the lesson to the responsible role's mistakes
file -> orchestrator re-spawns that role -> tester/student re-run -> judges re-run (max 2 rounds,
then Stepan decides).

## Escalation
- HOTFIX fails once -> TASK.
- TASK grows past 100 LOC -> PROJECT (new init, same issue).
- A LEARN task where Stepan wants to stop: commit what exists to the branch, note it in the
  issue; never let the coder finish it silently.
- Judge FAIL twice -> discuss with Stepan.
