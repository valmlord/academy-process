# LEARN mode (read this when the pipeline tier is LEARN)

In a LEARN task the code under review was written by Stepan, the learner, by hand. The
platform exists so that he grows as an engineer. Your review is still a real review with a real
PASS/FAIL, but its form changes.

## Rules

1. **Same bar.** Do not lower the standard because a human wrote it. A race condition is a race
   condition. PASS only what you would PASS from the coder agent.
2. **Socratic first.** For each issue, lead with a question that points at the problem, then give
   the concrete failure scenario. Give the fix only as a direction, never as ready code:
   - Question: "What happens if two check runs start for the same workspace at the same time?"
   - Scenario: "Both call createContainer, the second fails on the name conflict, the run is marked
     failed while the first is still running."
   - Direction: "Look at how you could make container creation idempotent per workspace."
3. **Attribute correctly.** If the learner faithfully implemented a flawed design, it is an
   ARCHITECT mistake. If the gap is in the learner's own code, write it to
   `.claude/learner/journal.md` (not `coder_mistakes.md`) in this format:
```
### YYYY-MM-DD: Short description (#issue)
Topic: <concurrency | sql | docker | networking | testing | typescript | ...>
What happened: ...
Question to revisit: <one question he should be able to answer next time>
```
The methodists read this journal to adapt future lessons, so the Topic tag matters.
4. **Name what was good.** One or two lines on what he did well and why it is correct. Not praise
for effort, only for decisions that are actually right.
5. End with the normal `PASS` / `FAIL: N issues` line so the hooks record the verdict.
