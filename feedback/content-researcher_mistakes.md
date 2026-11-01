# content-researcher mistakes

Lessons appended by judges when this role caused a FAIL. Load before working. Let it grow.

Format:
### YYYY-MM-DD: Short description (#issue)

What happened and why it is wrong.
Rule: One-line rule that prevents this.

### 2026-10-27: Permission-rule findings omitted the exceptions that change the lesson (#15)

The #15 research summarised CC permissions as "allow cannot carve exception from deny" without
the documented `!` gitignore negation in deny/ask lists (same settings source only, cannot reopen
a directory blocked as a whole), the allow-vs-deny depth asymmetry of single-segment patterns
(`Edit(src/**)` as deny matches `src` at any depth, as allow only `<cwd>/src`), that a `Read`
deny also blocks Edit/Write on the path, that `Write(path)`/`MultiEdit(path)` rules are accepted
but never match, the built-in read-only Bash set, and hook fail-open on non-2 exits. A check
emulating these semantics cannot be faithful without them.
Rule: When a lesson will emulate a vendor rule engine, extract every exception, asymmetry and
no-op form from the reference page, not only the headline evaluation order.

### 2026-10-28: Research paper findings taken from snippets of a superseded version (#15)

The #15 research recorded Gloaguen et al. (arXiv:2602.11988) as "ICLR 2026: unnecessary
requirements make tasks harder, LLM-generated files reduced success" while noting "from
snippets". Those are v1 (2026-02-12) abstract phrasings. The version live at checkedAt is v3
(2026-09-29): context files "do not generally improve task success rates" (+20% cost);
LLM-generated files drop in 5 of 8 settings without statistical significance; "additional
instructions make the task harder" is stated as a hypothesis. The venue is the MemAgents
workshop at ICLR 2026 (eth-sri.github.io), not ICLR main. The lesson repeated the v1 claims as
findings under "Исследования это подтверждают".
Rule: For a cited paper, read the current arXiv version (note vN and its date) and the
publisher/author page for the venue; never record findings "from snippets" as verified, and mark
a hypothesis as a hypothesis.

### 2026-10-30: Config findings that dropped scope limits, aliases and enumerations (#42, design round 1, accuracy)

The #42 research got four config findings wrong:
- C1 named three provider modes. The env-vars page lists five (also `CLAUDE_CODE_USE_ANTHROPIC_AWS` and
  `_MANTLE`), plus their provider base URLs.
- C1 stated the 2.1.312 shorter-prompt change for unrecognised names as general. The changelog limits it to
  Bedrock, Vertex, Foundry and Mantle.
- C5 said `strictAllowlist` "refuses non-listed hosts in every mode". It omitted that it works only in user,
  managed or `--settings` scope, and that plain `allowedDomains` only pre-allows (other hosts prompt). It
  also missed that `WebFetch(domain:)` allow rules feed the sandbox allowlist.
- C6 omitted `UV_INDEX_URL` (a deprecated equivalent) and `SSL_CERT_FILE` (uv's CA bundle).

The architect built a closed-set check on these summaries.
Rule: For every config key or env var a lesson may grade, record its scope limits, its parsing rule (boolean,
presence-only, exact), every documented alias or deprecated equivalent, and the complete enumeration, with
row counts. A changelog entry is quoted with its stated scope, never generalised.
