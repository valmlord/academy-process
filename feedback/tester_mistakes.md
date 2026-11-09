# tester mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### Seed: reported green for a step that was not run

A test report said "e2e: ok" while Playwright was never started; the flow was broken.
Rule: Every line of the report must come from a command you ran, with its output as evidence.

### 2026-11-04: Filled the host disk during a stack build; Docker's VM filesystem went read-only (#32)
With 2.4 GiB free and an empty pnpm cache in the image build, the tester also copied a whole scratch clone with `cp -Rc`
(about 1.7 GiB, not a free clone on this volume). The build hit `read-only file system` in /var/lib/docker; Stepan's
`academy_db-data` sits on the same VM filesystem, so his Postgres could no longer write. Recovery needed Stepan.
Rule: before any Docker build or stack run, check free host disk (`df -h /System/Volumes/Data`) and stop below 5 GiB;
make no file copies while a build runs; delete scratch node_modules and .next as soon as a check is done.
