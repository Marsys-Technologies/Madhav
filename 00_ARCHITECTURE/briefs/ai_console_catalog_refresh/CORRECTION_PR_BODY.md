## Summary

- Correct Gemini/OpenRouter metadata refresh HTTP 500 failures found during authenticated production acceptance of PR #2977.
- Admit the independently inspected native Antigravity 1.2.15 subscription protocol, with exact version pins only.

## Changes

| Surface | Change |
|---|---|
| Provider refresh service | Explicitly project persisted model fields; discard unpersisted capacity metadata without weakening strict validation. |
| Provider regression tests | Real adapters and real DAO validation with realistic Google/OpenRouter capacity fixtures. |
| CLI registry/private bridge/smoke | Consistent exact 1.2.12/1.2.13/1.2.15 admission; unknown versions remain blocked. |
| Real private bridge fixture | Assert metadata-only discovery for inspected version and rejection before discovery for an uninspected version. |
| Release evidence | Record failed first acceptance, verified web rollback, corrective scope, test-first proof and independent review. |

## Test plan

- [x] Full ESLint: zero errors, 595 pre-existing warnings.
- [x] Fresh complete TypeScript check: zero errors.
- [x] Complete suite: 15,099 passed, 975 skipped, two todo.
- [x] Guarded disposable PostgreSQL catalogue/isolation: 22 passed.
- [x] Independent corrective review: no blockers, 44 focused tests passed.
- [x] Native AGY consumer-OAuth headless protocol: one bounded OK call; 13,330 input/one output CLI token, no direct API-key/app fallback.
- [ ] Protected build/merge-group/main gates.
- [ ] Paired private bridge alignment and exact-SHA web deployment.
- [ ] Authenticated production API refresh, CLI model/effort setup, AGY explicit test, 15-minute error watch.

## Migration notes

None. Migration 1301 is already applied and unchanged; no destructive rollback.

## Acceptance criteria

Metadata-only API refresh completes for realistic capacity-bearing catalogues. Exact supported CLI admission is consistent across both execution surfaces. Discovery never claims generation readiness. Saved roles/defaults and strict ownership/version fences remain unchanged. Production acceptance is not claimed until the last three checks above pass.

Generated with Codex.
