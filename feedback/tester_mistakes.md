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

### 2026-11-11: Test report without the ADR-0006 "Design conformance" section, and a fixup left unexplained (#106)
The #106 diff touches design/pages/lesson, so ADR-0006 item 5 requires a "Design conformance" section: prototype and
app screenshots at 375 and 1280 in light and dark, every AC marked pass or fail with evidence, the token block diff,
the destructive button contrast, an empty raw colour grep. The report had none of it, also not the AC15 copy-table
comparison or the AC2 `git diff` check that design 1.1 hands to the tester, nor the command 6 line. Judge-architecture
must FAIL a change without that section. The report also did not say what the tester-phase `fixup!` into commit 10
(the destructive e2e guard) changed, so its content could not be reviewed.
Rule: When the diff touches a page under design/pages/, the report has a "Design conformance" section with one
pass/fail line per AC, and every commit the tester phase adds or folds in is named with the files it changes and why.
