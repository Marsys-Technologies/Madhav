---
artifact: RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md
canonical_id: PHASE_2C_HYGIENE
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session — analysis stream)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
parent_campaign: 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
prerequisite: Phase 2B committed (registry doc update on audit branch)
audit_findings_closed: temporal SLA probe gap, cross_varga_dignity_query unit test gap
---

# Phase 2C — Temporal SLA Probe + cross_varga Unit Tests

Final code-only sub-phase of the Phase 2 retrieval-tools campaign. Two narrow additions:

1. **`temporal` SLA probe** — the workhorse predictive-query tool has no SLA measurement today. Author one with 5 scenarios (one per sub-mode).
2. **`cross_varga_dignity_query` unit tests** — the only retrieval tool from the VARGA-ETL-FULL-S1-CPA work that has no unit-test coverage.

Both are bounded, ~0.5 session total. No data work, no production code changes.

---

## §A — Executor briefing (paste this block)

You are Claude Code in Antigravity IDE with `--dangerously-skip-permissions`. This session belongs to the analysis stream. You operate in `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis` on `analysis/backend-data-pipeline-perf-audit`. Do NOT cd into `/Users/Dev/Vibe-Coding/Apps/Madhav` (Chat V2 worktree).

**Prerequisite check (HARD STOP if not met):**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git status
git branch --show-current
# Expected: analysis/backend-data-pipeline-perf-audit, clean working tree.

git log --oneline | head -5
# Expected: Phase 2B commit visible at top.
```

Acceptance: clean tree, Phase 2B in history. If not, STOP.

**Mandatory reading:**
1. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/CLAUDE.md`
2. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md` §D
3. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md` (this file)
4. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform/scripts/sla_probe_planner_blind_tools.ts` (pattern reference)
5. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform/src/lib/retrieve/__tests__/saham_query.test.ts` (test pattern)
6. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform/src/lib/retrieve/temporal.ts` (the tool's source — read header for sub-mode list)
7. `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform/src/lib/retrieve/cross_varga_dignity_query.ts` (the tool's source)

---

## §B — Phase 1: Author `temporal` SLA probe

### B.1 — Read the tool's source to confirm sub-modes

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
head -80 platform/src/lib/retrieve/temporal.ts
```

Per the RCS entry (in `retrieval_capability_spec.ts`), `temporal` supports five sub-modes:
- **dasha_context**: dasha chain at a date (uses `dasha_context_required: true` + `time_window`)
- **transit**: time-windowed transit lookup (uses `time_window` over multi-day range)
- **sade_sati**: Saturn-over-Moon phases (uses `sade_sati_query: true`)
- **eclipse**: eclipse-window lookup (uses `eclipse_query: true` + optional `time_window`)
- **retrograde**: retrograde windows for a specific planet (uses `retrograde_query: true` + `retrograde_planet`)

Verify the actual param shape from the source. If it diverges from the RCS entry, follow the source.

### B.2 — Author `platform/scripts/sla_probe_temporal.ts`

Mirror `platform/scripts/sla_probe_planner_blind_tools.ts` structure exactly:
- Imports `tool as temporal` from `../src/lib/retrieve/temporal`
- `SLA_BUDGETS_MS` per sub-mode:
  - `dasha_context`: 200ms
  - `transit`: 400ms
  - `sade_sati`: 100ms
  - `eclipse`: 150ms
  - `retrograde`: 150ms
- `SCENARIOS` array (5 scenarios; ≤ 3 runs each via `SCENARIO_COUNT` env var; `WARMUP_RUNS=1` default)
- Output JSON to `platform/scripts/eval/sla_probe_temporal_<ISO_TS>.json`
- Per-scenario assertions: `latency_ms <= budget_ms` AND `rows_returned ≥ 1` for sub-modes that have data; `zero_rows` is acceptable for sub-modes where data may be sparse (e.g., eclipse_query may return 0 if the window has no eclipses)
- Exit codes:
  - 0 if all scenarios within budget
  - 0 with `⚠` if any `budget_exceeded`
  - 1 if any tool error
  - 2 if proxy unreachable (mirror the existing probe's hint message)

### B.3 — Add npm script

Edit `platform/package.json`:

```json
"sla:probe-temporal": "npx tsx --conditions=react-server --env-file-if-exists=../.env.rag scripts/sla_probe_temporal.ts",
```

Place it next to the existing `sla:probe-planner-blind` entry.

### B.4 — Verify

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

npx tsc --noEmit -p . 2>&1 | grep -cE "error TS"
# Expected: 0

# Test run (requires DB proxy in 2nd terminal — start it if not running)
SCENARIO_COUNT=3 WARMUP_RUNS=1 npm run sla:probe-temporal 2>&1 | tee /tmp/phase2c_temporal_sla.log
echo "exit: ${PIPESTATUS[0]}"
```

Acceptance: tsc clean, exit 0, all 5 scenarios within budget.

---

## §C — Phase 2: Author `cross_varga_dignity_query` unit tests

### C.1 — Read the tool's source

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
head -80 platform/src/lib/retrieve/cross_varga_dignity_query.ts
```

Capture: param shape, return shape (`ToolBundleResult`), `source_canonical_id` field value, default chart_id, what divisional charts are covered (D1, D9, D10, D12, D16, D24, D27, D30, D40, D45, D60 etc).

### C.2 — Author `platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts`

Mirror the `saham_query.test.ts` pattern exactly. 5 tests:

1. **Happy path** — no params, returns all expected divisional dignity rows
2. **Param filter** — filter by `varga` (e.g., `D9`); verify SQL `WHERE varga = $1` shape
3. **Empty rows** — mock empty result; assert no throw, empty results array
4. **ToolBundle shape** — `tool_name`, `tool_version`, `schema_version`, `result_hash` (sha256 format), `source_canonical_id`, `confidence`, `significance`
5. **Error path** — mock query throws; assert retrieve() rejects + `writeToolExecutionLog` was called with `status: 'error'`

Use `vi.mock('@/lib/storage')`, `vi.mock('@/lib/db/monitoring-write')`, `vi.mock('@/lib/telemetry')`, and `vi.mock('@/lib/schemas')` (if the tool uses `validate()`).

≤ 150 lines.

### C.3 — Verify

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

npx tsc --noEmit -p . 2>&1 | grep -cE "error TS"
# Expected: 0

npx vitest run src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts --reporter=verbose 2>&1 | tee /tmp/phase2c_cross_varga.log
# Expected: 5/5 PASS
```

---

## §D — Phase 3: Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git status

# Expected modified/new files:
#   new: platform/scripts/sla_probe_temporal.ts
#   new: platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts
#   modified: platform/package.json (one new line)

git add platform/scripts/sla_probe_temporal.ts \
        platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts \
        platform/package.json

git status   # verify no Chat V2 files staged

git commit -m "feat(retrieval): Phase 2C hygiene — temporal SLA probe + cross_varga unit tests

Final code-only sub-phase of the Phase 2 Retrieval Tools campaign. Two narrow
additions to close the audit's remaining test/probe gaps.

TEMPORAL SLA PROBE:
- platform/scripts/sla_probe_temporal.ts — 5 scenarios (one per sub-mode)
  · dasha_context: budget 200ms
  · transit:       budget 400ms
  · sade_sati:     budget 100ms
  · eclipse:       budget 150ms
  · retrograde:    budget 150ms
- npm run sla:probe-temporal (added to package.json)
- Mirrors sla_probe_planner_blind_tools.ts structure: WARMUP_RUNS=1 default,
  SCENARIO_COUNT env var, JSON report to scripts/eval/

CROSS_VARGA_DIGNITY_QUERY UNIT TESTS:
- platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts
- 5 mocked-storage tests: happy path, varga filter, empty rows, ToolBundle
  shape, error path
- Mirrors saham_query.test.ts pattern

Audit references:
- 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md (E.3 temporal SLA gap,
  audited-view §C.4 cross_varga test gap)
- 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md §D

Verification (2026-05-17):
- tsc:           0 errors project-wide
- vitest:        5/5 PASS (cross_varga_dignity_query.test.ts)
- SLA probe:     5 scenarios GREEN, all within budget

Closes Phase 2 campaign. Next step: PR-merge analysis branch to main, Cloud
Run deploy, consolidated answer:eval (deferred per
project_retrieval_tools_consolidated_eval.md until campaign close).
"

git push origin analysis/backend-data-pipeline-perf-audit
```

---

## §E — Report back

```markdown
# Phase 2C — Hygiene Report

## Pre-flight (§A)
- Branch: analysis/backend-data-pipeline-perf-audit ✓
- Phase 2B in history: <SHA> ✓
- Working tree clean: ✓

## Temporal SLA probe (§B)
- File: platform/scripts/sla_probe_temporal.ts (<N> lines)
- Scenarios: 5

| Sub-mode | P50 | P95 | Max | Budget | Reachability |
|---|---|---|---|---|---|
| dasha_context | Xms | Yms | Zms | 200ms | <%> |
| transit | Xms | Yms | Zms | 400ms | <%> |
| sade_sati | Xms | Yms | Zms | 100ms | <%> |
| eclipse | Xms | Yms | Zms | 150ms | <%> |
| retrograde | Xms | Yms | Zms | 150ms | <%> |

## cross_varga_dignity_query unit tests (§C)
- File: platform/src/lib/retrieve/__tests__/cross_varga_dignity_query.test.ts (<N> lines)
- Tests: 5/5 PASS
- Coverage: happy path + varga filter + empty rows + ToolBundle shape + error path

## Verification
- tsc:    0 errors
- vitest: <N>/<N> PASS

## Commit + push (§D)
- SHA: <SHA>
- Files: 3 (2 new + 1 modified)
- Pushed to: analysis/backend-data-pipeline-perf-audit

## Phase 2 campaign — final state
- 2A (M9 wiring + L9 data ship): <SHA> ✓
- 2B (classical attribution + signal_states backfill): <SHA> ✓
- 2C (temporal SLA + cross_varga tests): <SHA> ✓ (this commit)
- Ready for PR-merge to main + consolidated answer:eval.
```

---

## §F — Hard rules

- Stay on `analysis/backend-data-pipeline-perf-audit` in `/Madhav-analysis`
- Do NOT modify `temporal.ts` or `cross_varga_dignity_query.ts` source — only add tests/probes
- Use gemini-2.5-flash as planner-LLM default in any tests
- Do NOT run `npm run answer:eval` — that's the consolidated post-deploy step, not 2C
- If any sub-mode of temporal exceeds budget by > 2x, STOP and report — may indicate DB index regression
- If cross_varga test file already exists (unlikely; we checked), STOP and reconcile

---

*End RETRIEVAL_TOOLS_PHASE_2C_HYGIENE_BRIEF_v1_0.md. Successor: PR-merge to main + Cloud Run deploy + consolidated answer:eval.*
