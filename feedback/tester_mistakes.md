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

### 2026-11-16: Synthetic CPU load on a shared laptop starved other sessions and crashed an app (#157)
The #157 harness ran 40 `yes` processes per load run on a 10-core MacBook Air while eight other sessions worked.
Host load reached about 360, then 122 during the `lac6 4 40` run, and another app on Stepan's machine crashed.
The load also made the evidence useless: external spikes (a Docker VM at 45-663 % CPU) dominated, and three
full-suite and paired runs stopped on timeouts that hit unchanged files too.
Rule: At most 4 load generators per run, each started under `trap ... EXIT INT TERM` that kills them, every run
with its own timeout, and `pgrep -x yes` checked and reported empty after each run. Prefer evidence that needs no
synthetic load: a deterministic slow-down (fake timers, a mocked clock, an injected per-call delay) as the control.
