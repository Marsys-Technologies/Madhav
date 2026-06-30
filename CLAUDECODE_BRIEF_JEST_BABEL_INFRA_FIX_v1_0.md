---
canonical_id: CLAUDECODE_BRIEF_JEST_BABEL_INFRA_FIX
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-30
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — test-infra repair (jest/Babel transform breakage, all 505 suites)
priority: HIGH — restores the test signal; until fixed, every "tests pass" claim is blind, and the
  eval-confidence gate for go-live cannot be trusted.
session_type: implementation — DIAGNOSE FIRST, then apply the matching fix (do not guess the fix)
why_this_matters: the platform jest Babel transform is failing across ALL ~505 suites. This masks the true
  test signal — the retrieval eval, the chart_agnostic_gate test, the 34 pre-existing failures, everything.
  Restoring it is the prerequisite to trusting any test-based go-live confidence.
hard_constraint: this is a CONFIG/TOOLCHAIN fix — do NOT modify test assertions or app logic to "make tests
  pass." Fix the transform so the suites RUN; the resulting pass/fail signal (incl. the 34 known failures) is
  the honest output, not something to massage.
---

# CLAUDE CODE BRIEF — JEST/BABEL INFRA FIX (diagnose-then-fix)

> The platform jest Babel transform breaks on all 505 suites — the test signal is currently blind. Diagnose the
> ACTUAL error first (the root cause is one of several distinct possibilities, each with a different fix), then
> apply the matching fix. Do not author a fix blind; do not massage assertions.

## §1 — DIAGNOSE (reproduce the real error; this determines the fix)
1. Run the platform suite (`npm test` / the project's jest invocation) and capture the EXACT transform error +
   stack — the first failing suite's full output, not a summary. (This determines the fix.)
2. Inspect the toolchain: `jest.config.*`, `babel.config.*` / `.babelrc`, `package.json` jest+babel deps +
   versions, `tsconfig.json`, and whether transform is via `babel-jest` or `ts-jest`.
3. Identify the root cause among the candidates (state which one it is, with evidence):
   - (a) Babel config missing / wrong/absent preset (e.g. `@babel/preset-typescript`, `preset-env`, `preset-react`).
   - (b) ESM↔CJS mismatch (`"type":"module"`, `transformIgnorePatterns` not transpiling an ESM dep, import.meta).
   - (c) `ts-jest` vs `babel-jest` conflict / both configured / wrong transform mapping.
   - (d) A dependency bump (jest/babel/ts) that changed the transform contract or Node version mismatch.
   - (e) A `tsconfig`/path-alias the transform can't resolve (e.g. `@/` moduleNameMapper missing).
4. Confirm WHEN it broke (git blame / recent jest|babel|tsconfig|package.json changes) — pin the regressing commit if there is one.

## §2 — FIX (apply only the fix that matches the diagnosed cause)
- Apply the minimal config change that resolves the diagnosed root cause (e.g. add the missing preset; fix
  `transformIgnorePatterns`; reconcile ts-jest/babel-jest; pin/align the dep version; add the moduleNameMapper).
- Do NOT change test assertions or application code. This is a transform/config repair only.
- If the cause is a dep-version regression, prefer aligning to the last-known-green versions (check git) over
  rewriting config, unless config is genuinely the cleaner fix.

## §3 — ACCEPTANCE
- The full platform suite RUNS (no global transform failure) — suites execute and report real pass/fail.
- The honest signal is restored: the ~34 pre-existing failures now surface as individual, triageable failures
  (NOT hidden behind the transform break). Report the real current pass/fail counts.
- The retrieval-critical tests actually execute: `chart_agnostic_gate.test.ts`, the dual-channel drift test,
  the multi-LLM consistency tests, the inverted phala_muhurta native-name test.
- No assertion or app-logic change; the fix is config/toolchain only.
- Prod-verify not applicable (test infra) — but confirm the same `npm test` works clean in CI, not just locally.

## §4 — OUTPUT
- Commit the config fix with a message naming the diagnosed root cause + the regressing commit (if any).
- Report back: the root cause, the fix, and the RESTORED test signal (total suites, pass/fail, and the list of
  the now-visible pre-existing failures so they can be triaged next). Note explicitly whether the retrieval
  eval/gate tests pass now that they actually run.

## §5 — Follow-on (not this brief)
Once the signal is restored, the ~34 now-visible failures get triaged separately (legacy-teardown artifacts,
mimamsa_lel_intake live-sidecar dependency, the FORENSIC-grounding description assertion, etc.) — each decided
on merit (real bug → fix; stale assertion → invert/remove), NOT made-green. That triage is a separate brief.

*End of CLAUDECODE_BRIEF_JEST_BABEL_INFRA_FIX v1.0 — diagnose first; fix the transform, not the tests.*
