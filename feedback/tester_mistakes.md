# tester mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seed: reported green for a step that was not run

A test report said "e2e: ok" while Playwright was never started; the flow was broken.
Rule: Every line of the report must come from a command you ran, with its output as evidence.
