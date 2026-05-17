---
artifact: RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md
canonical_id: PHASE_2A_M9_WIRING
version: 1.0
status: READY
authored: 2026-05-17
author: Claude (Cowork session — analysis/backend-data-pipeline-perf-audit)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
parent_campaign: 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md
prerequisite: BRANCH_HYGIENE_RECOVERY_BRIEF_v1_0.md complete (main has da140c8, analysis branch synced)
audit_findings_closed: F.PIPE.1 (M9 tools unwired), F.DATA.2 (L9 DB seeds + GCS uploads deferred)
---

# Phase 2A — M9 Wiring + L9 Data Ship

This brief wires the two M9 retrieval tools (`multi_school_signal_lookup`, `convergence_score_lookup`) end-to-end through the LLM-first planner pipeline AND ships the deferred L9 DB seeds + GCS uploads that M9-C/D/E couldn't complete because the proxy was unavailable at session time.

The M9 tools have been "implemented and tested" (17 integration tests, M9_CLOSE_v1_0.md §1) but live in `platform/src/lib/tools/` as bare async functions with no `RetrievalTool` wrapper. The production dispatcher (`consume/route.ts:619 getTool(toolName)`) consults `RETRIEVAL_TOOLS` in `platform/src/lib/retrieve/index.ts`, which doesn't include them. Result: any query the planner classifies as `multi_school_triangulation` (a valid QueryClass) emits tool_calls that fail silently at dispatch.

The L9 data outputs from M9-C/D/E (7 per-school analyses, convergence_scores.json, school_disagreement_register.json, plus 4 DB tables) exist in Python script memory only — they were never written to DB or uploaded to GCS. Once the wrapper is in place, the tools will return empty results until the data lands.

---

## §A — Executor briefing (paste this block)

You are Claude Code in Antigravity IDE with `--dangerously-skip-permissions`. This session belongs to the analysis stream. Your branch is `analysis/backend-data-pipeline-perf-audit` per `feedback_two_stream_branch_policy.md`. Do NOT touch Chat V2 branches.

**Prerequisite check (HARD STOP if not met):**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout analysis/backend-data-pipeline-perf-audit
git status
git log --oneline -5

# Verify da140c8 (or its cherry-picked equivalent) is in the history.
# If not, STOP — run BRANCH_HYGIENE_RECOVERY_BRIEF_v1_0.md first.
git log --oneline | grep -iE "F\.PIPE\.1|wire 4 planner-blind tools"
```

**Acceptance:** clean working tree on `analysis/backend-data-pipeline-perf-audit`, planner-blind fix visible in log. If not, STOP.

**Mandatory reading:**
1. `/Users/Dev/Vibe-Coding/Apps/Madhav/CLAUDE.md`
2. `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md` (campaign frame)
3. `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md` (this file — full)
4. `/Users/Dev/Vibe-Coding/Apps/Madhav/09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md` §1 (M9 deliverables for context)

Then execute §B through §H below in order.

---

## §B — Phase 1: Mirror the M8 wrapper pattern

Read `platform/src/lib/retrieve/classical_text_search_tool.ts` and `classical_attribution_lookup_tool.ts` end-to-end. These are the M8 wrapper pattern (M8-G). They wrap the bare functions in `lib/tools/classical_*.ts` into the `RetrievalTool` shape — they call the bare function, shape the response into `ToolBundle`, hash the results, log telemetry, and return.

Use this pattern to author **both new wrappers**:

**File 1: `platform/src/lib/retrieve/multi_school_signal_lookup_tool.ts`**

- Imports the bare function: `import { multi_school_signal_lookup, type MultiSchoolSignalLookupInput, type MultiSchoolSignalLookupOutput } from '@/lib/tools/multi_school_signal_lookup'`
- Exports `tool: RetrievalTool` with `name: 'multi_school_signal_lookup'`, `version: '1.0.0'`, `description: <copy from RCS entry tool 27 in retrieval_capability_spec.ts>`
- `retrieve(plan, params)` async:
  - Coerces params to `MultiSchoolSignalLookupInput`
  - Calls the bare function
  - Maps each per-school result row into a `ToolBundleResult` with `content: JSON.stringify(...)`, `source_canonical_id: 'school_signal_coverage'`, `confidence: <coverage_type → 0.95/0.75/0.50>`, `significance: 0.8`
  - Computes result_hash (sha256 over content slices, same pattern as lel_query.ts)
  - Calls `validate('tool_bundle', bundle)` and throws if invalid
  - `telemetry.recordLatency(...)` and `writeToolExecutionLog(...)` non-blocking
  - Returns the assembled `ToolBundle`

**File 2: `platform/src/lib/retrieve/convergence_score_lookup_tool.ts`**

- Imports the bare function: `import { convergence_score_lookup, type ConvergenceScoreLookupInput, type ConvergenceScoreLookupOutput } from '@/lib/tools/convergence_score_lookup'`
- Same shape as File 1
- Each domain's convergence score becomes one `ToolBundleResult` with `content: JSON.stringify(domain_score)`, `source_canonical_id: 'convergence_scores'`, `confidence: <convergence_level → HIGH 0.95 / MEDIUM 0.75 / LOW 0.5>`
- Calls into the bare function which itself handles JSON fallback when DB unavailable

Both files: ≤200 lines each.

---

## §C — Phase 2: Register in all five registries

These five files MUST be updated atomically. Missing any one of them breaks a different layer of the pipeline.

### C.1 — `platform/src/lib/retrieve/index.ts`

Add imports near the existing M8 imports:

```typescript
// M9 — multi-school triangulation (tools 27 + 28)
import * as multiSchoolSignalLookupTool from './multi_school_signal_lookup_tool'
import * as convergenceScoreLookupTool from './convergence_score_lookup_tool'
```

Append to `RETRIEVAL_TOOLS` array AFTER `classicalAttributionLookupTool.tool`:

```typescript
  multiSchoolSignalLookupTool.tool,
  convergenceScoreLookupTool.tool,
```

### C.2 — `platform/src/lib/router/retrieval_capability_spec.ts`

The two entries already exist in `RETRIEVAL_CAPABILITY_SPEC` from M9-D / M9-A work — VERIFY they're present. If yes, skip. If no, port from `CLASSICAL_TOOL_REGISTRY` in `platform/src/lib/tools/index.ts` lines 56-74.

```bash
grep -nE "tool_name: 'multi_school_signal_lookup'|tool_name: 'convergence_score_lookup'" \
  platform/src/lib/router/retrieval_capability_spec.ts
# If both present: skip. If missing: author following the lel_query / classical_text_search pattern.
```

### C.3 — `platform/src/lib/trace/types.ts`

Add to `ALL_21_RETRIEVAL_TOOLS` array (after `lel_query`):

```typescript
  'lel_query',
  'multi_school_signal_lookup',
  'convergence_score_lookup',
] as const
```

Update the comment block: "Updated 2026-05-17 (Phase 2A): added multi_school_signal_lookup + convergence_score_lookup. Literal count is now 24."

### C.4 — `platform/src/app/api/chat/consume/route.ts:73`

Update `toolStepType()`:

```typescript
function toolStepType(toolName: string): TraceStep['step_type'] {
  if (toolName === 'vector_search') return 'vector'
  if (['msr_sql', 'query_msr_aggregate'].includes(toolName)) return 'sql'
  if (['classical_text_search', 'classical_attribution_lookup'].includes(toolName)) return 'sql'
  if (
    ['lel_query', 'query_signal_state', 'query_kp_ruling_planets', 'query_varshaphala'].includes(
      toolName
    )
  ) {
    return 'sql'
  }
  // M9 L9 tools — Postgres-backed convergence + coverage tables
  if (['multi_school_signal_lookup', 'convergence_score_lookup'].includes(toolName)) {
    return 'sql'
  }
  return 'gcs'
}
```

### C.5 — `platform/src/app/api/chat/consume/route.ts:80`

Update `inferLayer()` to include the M9 tools in the L2.5 list (they're consumed at the L2.5 boundary even though the underlying tables are technically L9):

```typescript
function inferLayer(toolName: string): 'L1' | 'L2.5' {
  if (['msr_sql', 'query_msr_aggregate', 'pattern_register', 'resonance_register',
       'cluster_atlas', 'contradiction_register', 'temporal', 'cgm_graph_walk',
       'multi_school_signal_lookup', 'convergence_score_lookup'].includes(toolName)) {
    return 'L2.5'
  }
  return 'L1'
}
```

---

## §D — Phase 3: Unit tests (mocked storage)

Author both:

- `platform/src/lib/retrieve/__tests__/multi_school_signal_lookup_tool.test.ts` (5 tests)
- `platform/src/lib/retrieve/__tests__/convergence_score_lookup_tool.test.ts` (5 tests)

Each mirrors the `lel_query.test.ts` pattern — `vi.mock('@/lib/storage')`, mock the bare-function module (`vi.mock('@/lib/tools/multi_school_signal_lookup', () => ({ multi_school_signal_lookup: vi.fn() }))`), then test:

1. **happy path** — returns the expected ToolBundle shape with N results
2. **param filter** — passes through filters correctly
3. **empty rows** — returns empty results array without throwing
4. **error path** — bare function throws, retrieve() logs error and rethrows
5. **ToolBundle shape** — schema_version, tool_bundle_id, result_hash all present

Update `platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts` if the count assertion needs bumping from 24 → 26.

---

## §E — Phase 4: Live SLA probe coverage

Extend `platform/scripts/sla_probe_planner_blind_tools.ts` to include 3 scenarios per new tool. Rename the file's scope comment to "Phase 1 + 2A tools". Add to `SLA_BUDGETS_MS`:

```typescript
const SLA_BUDGETS_MS: Record<string, number> = {
  lel_query: 250,
  query_signal_state: 400,
  query_kp_ruling_planets: 200,
  query_varshaphala: 250,
  multi_school_signal_lookup: 350,    // 7-school JOIN, complex
  convergence_score_lookup: 200,      // 5-domain rollup, simpler
}
```

Add to `SCENARIOS`:

```typescript
  // multi_school_signal_lookup
  { tool: multiSchoolSignalLookup, scenario_name: 'multi_school · career domain', params: { domain: 'CAREER' } },
  { tool: multiSchoolSignalLookup, scenario_name: 'multi_school · specific signal', params: { signal_ids: ['SIG.MSR.142'] } },
  { tool: multiSchoolSignalLookup, scenario_name: 'multi_school · per-school filter', params: { school: 'parashari', domain: 'HEALTH' } },

  // convergence_score_lookup
  { tool: convergenceScoreLookup, scenario_name: 'convergence · all domains', params: {} },
  { tool: convergenceScoreLookup, scenario_name: 'convergence · single domain', params: { domain: 'RELATIONSHIP' } },
  { tool: convergenceScoreLookup, scenario_name: 'convergence · HIGH only', params: { min_level: 'HIGH' } },
```

Don't re-run the probe yet — that happens after §F data ship lands.

---

## §F — Phase 5: L9 data ship (requires local proxy)

### F.1 — Start the proxy in a separate terminal

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
bash platform/scripts/start_db_proxy.sh
# Leave running.
```

### F.2 — Inspect the M9 scripts

```bash
ls /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/m9/
cat /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/m9/run_multi_school_analysis.py | head -40
cat /Users/Dev/Vibe-Coding/Apps/Madhav/platform/scripts/m9/compute_convergence.py 2>/dev/null | head -40
```

These scripts were authored at M9-C-S1 / M9-D-S1 and noted as "DB seed deferred — proxy unavailable" in the M9 ACs. They contain the actual writes.

### F.3 — Run the M9 analysis + persistence

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
python3 scripts/m9/run_multi_school_analysis.py --write-db
```

If the script doesn't have a `--write-db` flag, read the script to find the right invocation. The 35 analysis rows (7 schools × 5 domains) should land in `school_analysis_runs` and `school_signal_coverage`.

Then:

```bash
python3 scripts/m9/compute_convergence.py --write-db
```

This populates `convergence_scores` (5 rows, one per domain).

If `school_disagreements` needs separate seeding, run `python3 scripts/m9/build_disagreement_register.py --write-db` per the M9-E AC ledger.

### F.4 — Verify DB rows

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" /Users/Dev/Vibe-Coding/Apps/Madhav/.env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT 'school_signal_coverage' as t, count(*) FROM school_signal_coverage
    UNION ALL SELECT 'school_analysis_runs', count(*) FROM school_analysis_runs
    UNION ALL SELECT 'convergence_scores', count(*) FROM convergence_scores
    UNION ALL SELECT 'school_disagreements', count(*) FROM school_disagreements;
  "
```

**Acceptance:**
- school_signal_coverage ≥ 4011 (per audit §C.5 / M9-A audit)
- school_analysis_runs ≥ 35
- convergence_scores = 5 (one per domain — CAREER, HEALTH, RELATIONSHIP, SPIRITUAL, PSYCHOLOGICAL)
- school_disagreements ≥ 10 (per M9-E AC.M9E.1)

### F.5 — Upload to GCS

Per `GCS_LAYOUT_v1_0.md` L9 layout:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform

# 7 per-school analyses
for school in parashari jaimini tajika kp nadi bnn yogini; do
  gsutil cp "scripts/m9/${school}_analysis.json" \
            "gs://madhav-marsys-sources/L9/school_analyses/${school}_analysis.json"
done

# Convergence + disagreements
gsutil cp scripts/m9/convergence_scores.json \
          gs://madhav-marsys-sources/L9/convergence/convergence_scores.json
gsutil cp scripts/m9/school_disagreement_register.json \
          gs://madhav-marsys-sources/L9/convergence/school_disagreement_register.json
```

Adjust paths if the actual script outputs are elsewhere — check `ls platform/scripts/m9/*.json` first.

### F.6 — Verify GCS objects

```bash
gsutil ls -l gs://madhav-marsys-sources/L9/school_analyses/
gsutil ls -l gs://madhav-marsys-sources/L9/convergence/
```

Acceptance: 7 JSONs under school_analyses/, 2 JSONs under convergence/.

---

## §G — Phase 6: Verify pipeline can now select + dispatch M9 tools

### G.1 — Re-run RCS regression test

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit -p . 2>&1 | tee /tmp/phase2a_tsc.log
echo "tsc exit: $?"

npx vitest run \
  src/lib/router/__tests__/retrieval_capability_spec.test.ts \
  src/lib/retrieve/__tests__/multi_school_signal_lookup_tool.test.ts \
  src/lib/retrieve/__tests__/convergence_score_lookup_tool.test.ts \
  --reporter=verbose 2>&1 | tee /tmp/phase2a_unit.log
```

**Acceptance:** tsc 0 errors, all new tests pass (10 new tests).

### G.2 — Live SLA probe with new scenarios

```bash
SCENARIO_COUNT=3 WARMUP_RUNS=1 npm run sla:probe-planner-blind 2>&1 | tee /tmp/phase2a_sla.log
```

**Acceptance:** all scenarios within budget. The two new M9 scenarios should now return non-zero rows since §F seeded the DB.

### G.3 — Planner-only smoke specifically for M9

Extend `tests/eval/planner_blind_fix_smoke.ts` `TARGET_TOOLS` to include `multi_school_signal_lookup` and `convergence_score_lookup`, pointing at GT.050-052 (the multi_school_triangulation golden entries already in the set per M9-D-S1).

Or author a separate `tests/eval/planner_m9_smoke.ts`. Either is fine — pick the simpler path.

```bash
npm run eval:planner-blind-fix 2>&1 | tee /tmp/phase2a_smoke.log
```

**Acceptance:** all 6 tools (4 Phase 1 + 2 Phase 2A) at `selected ≥ 1` and `required-hit ≥ 1`.

---

## §H — Phase 7: Commit + push (ASK NATIVE FIRST)

If §G.1, §G.2, §G.3 are all green, ask Abhisek:

> "All Phase 2A gates green: tsc 0, +10 unit tests pass, SLA probe GREEN on both new M9 tools, planner smoke confirms multi_school_signal_lookup + convergence_score_lookup are now reachable. L9 DB has <N> rows in school_signal_coverage, GCS has 7 + 2 JSONs uploaded. Ready to commit + push to analysis/backend-data-pipeline-perf-audit?"

If approved:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git status

git add \
  platform/src/lib/retrieve/multi_school_signal_lookup_tool.ts \
  platform/src/lib/retrieve/convergence_score_lookup_tool.ts \
  platform/src/lib/retrieve/index.ts \
  platform/src/lib/trace/types.ts \
  platform/src/app/api/chat/consume/route.ts \
  platform/src/lib/retrieve/__tests__/multi_school_signal_lookup_tool.test.ts \
  platform/src/lib/retrieve/__tests__/convergence_score_lookup_tool.test.ts \
  platform/src/lib/router/__tests__/retrieval_capability_spec.test.ts \
  platform/scripts/sla_probe_planner_blind_tools.ts \
  platform/tests/eval/planner_blind_fix_smoke.ts \
  00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md \
  00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md

git commit -m "feat(rcs): wire M9 tools 27+28 + ship L9 data (closes F.PIPE.1, F.DATA.2)

Closes the planner-blind gap on multi_school_signal_lookup and
convergence_score_lookup by adding RetrievalTool wrappers under
platform/src/lib/retrieve/ (mirroring the M8-G wrapper pattern). The
bare functions in platform/src/lib/tools/ were tested at M9-D-S1 but
unreachable by consume/route.ts:619 getTool() because they had no
runtime registration. F.PIPE.1 BLOCKER in MACROPHASE_AND_DATA_AUDIT.

Also ships the L9 data that M9-C/D/E couldn't write because the local
proxy was unavailable at session time:
- school_signal_coverage:  <N> rows seeded
- school_analysis_runs:    35 rows (7 schools × 5 domains)
- convergence_scores:      5 rows (one per domain)
- school_disagreements:    <N> rows (M9-E disagreement register)
- GCS: 7 per-school analyses + convergence_scores.json + school_disagreement_register.json
  uploaded to gs://madhav-marsys-sources/L9/

Includes:
- multi_school_signal_lookup_tool.ts wrapper + 5 unit tests
- convergence_score_lookup_tool.ts wrapper + 5 unit tests
- RETRIEVAL_TOOLS array now 26 entries (was 24)
- ALL_21_RETRIEVAL_TOOLS array now 24 entries (was 22)
- toolStepType + inferLayer mappings updated for both M9 tools
- SLA probe extended with 3 scenarios per M9 tool
- Planner smoke updated to cover M9 tools via GT.050-052

Audit references:
- 00_ARCHITECTURE/MACROPHASE_AND_DATA_AUDIT_v1_0.md F.PIPE.1 + F.DATA.2
- 00_ARCHITECTURE/RETRIEVAL_TOOLS_PHASE_2_CAMPAIGN_v1_0.md §B
- 00_ARCHITECTURE/briefs/RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md
- 09_MULTI_SCHOOL_TRIANGULATION/M9_CLOSE_v1_0.md (predecessor)

Verification (2026-05-17):
- tsc:           0 errors project-wide
- vitest:        <N>/<N> PASS (10 new + existing)
- SLA probe:     GREEN
  · multi_school_signal_lookup  P50=Xms P95=Yms budget=350ms
  · convergence_score_lookup    P50=Xms P95=Yms budget=200ms
- Planner smoke: multi_school_signal_lookup X/3 required-hit Y/3
                 convergence_score_lookup   X/3 required-hit Y/3

Post-deploy: DO NOT run npm run answer:eval. Per native decision recorded
in project_retrieval_tools_consolidated_eval.md, the answer:eval runs ONCE
at the end of the campaign (Phase 2C close), not per sub-phase.

Queued tools shipped this PR: multi_school_signal_lookup,
convergence_score_lookup (appended to memory tracker).
"

git push origin analysis/backend-data-pipeline-perf-audit
```

Watch CI / deploy pipeline. The audit branch isn't tied to Cloud Run deploy directly — only merges to main deploy. So this push is repository-only until the PR merges.

---

## §I — Report back

Deliver this exact Markdown shape to Abhisek:

```markdown
# Phase 2A — M9 Wiring + L9 Data Ship Report

## Pre-flight (§A)
- Branch: <current>
- da140c8 in history: <yes/no>

## Phase 1 — Wrappers (§B)
- multi_school_signal_lookup_tool.ts: <X lines>
- convergence_score_lookup_tool.ts: <X lines>

## Phase 2 — Registry updates (§C)
- C.1 RETRIEVAL_TOOLS: count 24→26 ✓
- C.2 RETRIEVAL_CAPABILITY_SPEC: <verified/added>
- C.3 ALL_21_RETRIEVAL_TOOLS: count 22→24 ✓
- C.4 toolStepType: both mapped sql ✓
- C.5 inferLayer: both mapped L2.5 ✓

## Phase 3 — Unit tests (§D)
- Tests added: 10 (5+5)
- All passing: <yes/no>

## Phase 4 — SLA probe extension (§E)
- Scenarios added: 6 (3+3)

## Phase 5 — L9 data ship (§F)
| Table | Rows before | Rows after |
|---|---|---|
| school_signal_coverage | 0 | <N> |
| school_analysis_runs | 0 | 35 |
| convergence_scores | 0 | 5 |
| school_disagreements | 0 | <N> |

| GCS path | Objects |
|---|---|
| gs://madhav-marsys-sources/L9/school_analyses/ | 7 |
| gs://madhav-marsys-sources/L9/convergence/ | 2 |

## Phase 6 — Verification (§G)
- tsc: <X> errors
- vitest: <pass>/<total>
- SLA probe (warm, 3-run):
  · multi_school_signal_lookup  P50=Xms P95=Yms max=Zms budget=350ms
  · convergence_score_lookup    P50=Xms P95=Yms max=Zms budget=200ms
- Planner smoke (gemini-2.5-flash):
  · multi_school_signal_lookup  selected X/3, required-hit Y/3
  · convergence_score_lookup    selected X/3, required-hit Y/3

## Phase 7 — Commit + push (§H)
- Committed: <yes/no/awaiting>
- Commit SHA: <SHA>
- Pushed to: analysis/backend-data-pipeline-perf-audit
- Open PR? <yes/no/native decision>

## Decisions / escalations
[anything anomalous]
```

---

## §J — Hard rules

- ALWAYS on `analysis/backend-data-pipeline-perf-audit` branch — never touch Chat V2 branches
- Pre-flight check (§A) is a hard gate
- Do NOT run `npm run answer:eval` — deferred to campaign close
- Do NOT modify M9 bare function source files in `platform/src/lib/tools/`; wrap only
- Do NOT commit if any of tsc / vitest / SLA / planner-smoke fail
- Use gemini-2.5-flash as default planner model in smoke tests (production-matching)
- If §F deferred-data scripts don't exist or fail, STOP and report — don't improvise on data writes
- If RCS entries for the M9 tools already exist (likely — M9-A/D added them), SKIP §C.2 — don't duplicate

---

*End RETRIEVAL_TOOLS_PHASE_2A_M9_BRIEF_v1_0.md. Successor: Phase 2B brief (classical attribution + signal_states data backfill) authored at 2A close.*
