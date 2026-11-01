# Design review must be genuine, not a rubber-stamp

**Why:** In one task the architect's design missed a packaging requirement for a new module,
the design review said "solid" in ~50 seconds without checking how it deploys, and the coder
then hit a runtime "module not found" - minutes wasted debugging something a real review would
have caught before any code was written.

**How to apply:**
- Spend real time on the review (a <30s design_review reads as a rubber-stamp - the
  judge-architecture agent flags it).
- Check: does the design add new modules/directories? → any packaging/import/symlink step needed?
- Check: does it add new dependencies? → present in the target environment?
- Check: does it change file layout? → are the deploy/build scripts aware?
- Check: does it assume something about runtime? → verify it.
- If the review finds nothing, state WHAT you checked - not just "looks good".
