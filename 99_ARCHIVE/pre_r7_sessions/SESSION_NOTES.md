# Gate II — Session Notes

Session opened: 2026-05-12 (autonomous overnight execution).
Cowork thread name: **MARSYS Gate II Exec — Trace Pipeline Alignment**

## Baselines captured at §1 entry-gate

### Test baseline (`npm test -- --run`)
- Test files: **185 total** — 158 passed, 27 failed
- Tests: **1571 total** — 1521 passed, 28 failed, 22 skipped
- Duration: ~6.86 s
- Saved log: `/tmp/gate2_test_baseline.log`

### Baseline test failures (pre-Gate II)

Failing files (27) — all pre-existing, none introduced by Gate II:

```
src/components/consume/__tests__/PanelAnswerView.test.tsx
src/lib/storage/__tests__/filesystem.test.ts
src/lib/synthesis/__tests__/orchestrator_wiring.test.ts
src/lib/synthesis/__tests__/panel/orchestrator_panel.test.ts
src/lib/synthesis/__tests__/synthesis.test.ts
src/scripts/etl/__tests__/msr_parser.test.ts
src/scripts/manifest/__tests__/parity_validator.test.ts
tests/components/LogPredictionAction.test.tsx
tests/components/TraceDrawer.test.tsx          ← trace-area, 2/4 failing (EventSource not defined in jsdom)
tests/e2e/clients.spec.ts                       (e2e playwright; skipped in CI by default)
tests/e2e/portal/a11y.spec.ts
tests/e2e/portal/appshell.spec.ts
tests/e2e/portal/build-mode.spec.ts
tests/e2e/portal/chart-profile.spec.ts
tests/e2e/portal/cockpit-rail.spec.ts
tests/e2e/portal/cockpit-redirect.spec.ts
tests/e2e/portal/consume-polish.spec.ts
tests/e2e/portal/mobile.spec.ts
tests/e2e/portal/roster.spec.ts
tests/e2e/portal/timeline.spec.ts
tests/eval/planner_regression_gate.test.ts
tests/pipeline/manifest_planner.test.ts
tests/pipeline/planner_context_builder.test.ts
tests/pipeline/universal_query_engine.test.ts
tests/planner/circuit_breaker.test.ts
tests/synthesis/context_assembler.test.ts
tests/unit/lib/claude/build-tools.test.ts
```

Per §4.5 R5 these are NOT Gate II's to fix.
The TraceDrawer.test.tsx failure is `ReferenceError: EventSource is not defined` from `useTraceStream.ts:63` — jsdom env lacks EventSource polyfill. Pre-existing.

### TypeScript baseline (`tsc --noEmit`)
- **22 errors**, all in `tests/pipeline/**`, `tests/planner/**`, `tests/synthesis/**`.
- Zero errors in `platform/src/components/trace/**` or `platform/src/lib/admin/trace_*`.
- Saved log: `/tmp/gate2_tsc_baseline.log`

### Lint baseline (`npm run lint`)
- **21 errors**, **102 warnings**, 0 errors / 12 warnings auto-fixable.
- Saved log: `/tmp/gate2_lint_baseline.log`

### Working-tree state at session-open

- `M .gitignore` (pre-existing; added `.claude/settings.local.json` to ignore list; not Gate II's; left untouched).
- HEAD: `3a345fc Gate II: install autonomous execution brief v2.0` on `feature/gate2-trace-pipeline-align`.

## Entry-gate result: PASS (proceed to W1)

All §1 checks pass with documented baselines. No blockers.

---

## Running notes

(executor appends as work proceeds)
