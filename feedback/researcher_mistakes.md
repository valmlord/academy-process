# Researcher Mistakes

Methodology lessons for investigating. Seeded with research-discipline lessons; append new
project-specific ones as they are found.

### Guessed instead of reading the actual file

Reported how something "probably" works from memory instead of opening the file; the design was
built on a wrong fact.
Rule: Read the actual file. If you cannot verify something, say "could not verify" - never guess.

### Reported code defaults as if they were the live values

Reported the value hardcoded in the source as the effective one, when the runtime config
overrode it.
Rule: Check BOTH the code AND the runtime config (env vars, service definitions, overrides).
A code default is not the live value until you confirm nothing overrides it.

### Incomplete findings - missed one of several inputs

A function took several inputs that each drive its output in different regimes; the research
covered only one, so a fix scoped only that one and left the same problem alive in another branch.
Rule: When something has multiple inputs/branches that each drive the outcome, enumerate ALL of
them and report each - not just the one named in the task.

### 2026-11-10: Named starter.ts:112 as a consumer of a YAML CourseReadError (#117)
Research 4 said a CourseReadError "maps ... to StarterRefusedError in starter.ts:112". That catch wraps only an
lstat of the lesson directory; the YAML loader is never called on that path. The architect copied it into the
operator view. The research also listed only the direct caller of `parseYamlFile`, not the callers of
`readCourse`, so the image-build export (`apps/web/scripts/export-course.ts`) was missed.
Rule: A "maps to" fact names the call path from the throw to the catch, read line by line; a grep hit on the class
name is not a consumer.
