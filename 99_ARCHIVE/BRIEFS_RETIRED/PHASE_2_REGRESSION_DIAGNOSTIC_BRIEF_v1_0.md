---
artifact: PHASE_2_REGRESSION_DIAGNOSTIC_BRIEF_v1_0.md
canonical_id: PHASE_2_REGRESSION_DIAGNOSTIC
version: 1.0
status: READY
authored: 2026-05-18
author: Claude (Cowork session — analysis stream)
intended_executor: Claude Code (Antigravity IDE, --dangerously-skip-permissions)
purpose: >
  Diagnose why answer:eval pass rate dropped from 80% (4/5 on completed at
  baseline 2026-05-11) → 22% (2/9 on completed post-Phase-2 deploy 2026-05-18).
  Read-only investigation. No code or data changes. Output: a structured root
  cause report so we can decide between rollback, surgical fix-forward, or
  accept-with-known-limits.
trigger_eval_run: 8989aa3e-8893-4cfc-ac9e-857ece3a4f39
deploy_under_test: amjis-web-00210-qzg (commit bb6b279 on main)
baseline_compare: platform/scripts/eval/results_gemini_baseline_20260511.json
---

# Phase 2 Post-Deploy Regression — Diagnostic Brief

The Phase 2 retrieval-tools campaign shipped end-to-end (PR #78 merged, Cloud Run deployed). But the consolidated answer:eval revealed a real regression: **pass rate dropped from 80% (4/5 on completed) to 22% (2/9 on completed)**. B10 stayed clean at 100% (no fabricated values), so this is not a fabrication problem — it's a quality-of-context problem. The newly-wired tools are presumably firing but their output isn't producing pass-grade synthesis.

This brief diagnoses the root cause via read-only DB inspection. No code or data mutations. Just inspection of `query_plan_log`, `tool_execution_log`, `audit_events`, and `query_trace_steps` for the failed eval run.

---

## §A — Executor briefing (paste this block)

You are Claude Code in Antigravity IDE with `--dangerously-skip-permissions`. Operate in `/Users/Dev/Vibe-Coding/Apps/Madhav-analysis` on branch `analysis/backend-data-pipeline-perf-audit`. The Chat V2 stream lives in `/Users/Dev/Vibe-Coding/Apps/Madhav` — do not touch.

**Prerequisite check:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git status
git branch --show-current
# Expected: clean working tree, on analysis branch

# Verify the deploy under test is live
gcloud run services describe amjis-web --region=asia-south1 \
  --format="value(status.latestReadyRevisionName)" 2>&1
# Expected: amjis-web-00210-qzg (or whatever §B records)
```

**Pre-flight: start DB proxy in a second terminal:**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
bash platform/scripts/start_db_proxy.sh
# Leave running.
```

This brief is **read-only**. Do NOT run any INSERT/UPDATE/DELETE. Do NOT modify any code files. Do NOT commit anything. Output is a diagnostic report only.

---

## §B — Inspect the failing eval run

The eval run ID is `8989aa3e-8893-4cfc-ac9e-857ece3a4f39`. All eval queries logged their full lifecycle. Pull the data:

### B.1 — Which queries ran, with what outcome?

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      gq_id,
      query_class,
      status,
      latency_ms,
      LEFT(query_text, 80) AS query_preview
    FROM eval_runs
    WHERE id = '8989aa3e-8893-4cfc-ac9e-857ece3a4f39'
    ORDER BY gq_id;
  "
```

(Adapt table/column names if the actual schema differs — the schema for eval runs may be `eval_run_rows` or similar; check migration 044 for the actual structure.)

If the schema isn't obvious, run:

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    \dt eval*
  "
```

### B.2 — For each fixture, what plan did the planner emit?

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      qpl.query_id,
      qpl.query_class,
      qpl.tool_calls_json,
      qpl.synthesis_guidance,
      qpl.latency_ms AS planner_latency_ms,
      qpl.model_id AS planner_model
    FROM query_plan_log qpl
    WHERE qpl.created_at >= '2026-05-18T10:30:00Z'
      AND qpl.created_at <= '2026-05-18T11:15:00Z'
    ORDER BY qpl.created_at;
  "
```

This tells you WHICH tools the planner picked for each fixture. Compare against expected_tools for each GQ:

- **GQ-001/002/003 factual**: should pick chart_facts_query, msr_sql
- **GQ-004/005/006 interpretive**: should pick msr_sql + cgm_graph_walk + pattern_register + resonance_register + contradiction_register
- **GQ-007/008/009 holistic**: should pick wide bundle including domain_report_query
- **GQ-010/011/012 discovery**: should pick pattern_register, resonance_register, cluster_atlas, vector_search
- **GQ-013/014/015 predictive**: should pick temporal + lel_query (NEW) + msr_sql + pattern_register

**Key questions to answer from §B.2:**

1. Did the planner SELECT the new tools (lel_query, query_signal_state, multi_school_signal_lookup, etc.) on the failing queries?
2. Did the planner produce sensible plans, or did it return malformed/empty tool_calls arrays?
3. Are there signs the few-shot injection in pipeline_planner.ts misfired on non-M9 queries (i.e., M9 detectM9Query() false-positive triggered for unrelated query classes)?

### B.3 — For each fired tool, what was its execution latency + result count?

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      tool_name,
      COUNT(*) AS calls,
      AVG(latency_ms)::int AS avg_ms,
      MAX(latency_ms)::int AS max_ms,
      AVG(rows_returned)::int AS avg_rows,
      SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS errors,
      SUM(CASE WHEN status='zero_rows' THEN 1 ELSE 0 END) AS zero_rows
    FROM tool_execution_log
    WHERE created_at >= '2026-05-18T10:30:00Z'
      AND created_at <= '2026-05-18T11:15:00Z'
    GROUP BY tool_name
    ORDER BY MAX(latency_ms) DESC;
  "
```

**Look for:**
- Tools with `max_ms` > 30000 (30s) — these are timeout candidates
- Tools with `errors` > 0 — straight failures
- Tools with `zero_rows` AND that should have returned data — the new wiring may be calling but the bare functions return nothing (DB query mismatched parameters?)
- `query_signal_state` — verify it returns rows (we backfilled 1M; should not be empty for any 2026 date)
- `multi_school_signal_lookup`, `convergence_score_lookup` — were they invoked at all?

### B.4 — For the 5 TIMEOUT fixtures specifically

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    -- Identify the query_ids of the timed-out fixtures.
    -- A timeout in answer_eval.ts is implemented as a fetch timeout at the
    -- HTTP client level — these queries may still be running server-side.
    -- Look for queries that started but never produced an audit_events row.
    SELECT
      qts.query_id,
      MIN(qts.started_at) AS first_step,
      MAX(qts.completed_at) AS last_step,
      COUNT(*) AS step_count,
      EXISTS(SELECT 1 FROM audit_events ae WHERE ae.query_id = qts.query_id) AS audit_landed
    FROM query_trace_steps qts
    WHERE qts.created_at >= '2026-05-18T10:30:00Z'
      AND qts.created_at <= '2026-05-18T11:15:00Z'
    GROUP BY qts.query_id
    HAVING NOT EXISTS(SELECT 1 FROM audit_events ae WHERE ae.query_id = qts.query_id)
    ORDER BY MIN(qts.started_at);
  "
```

For each timed-out query, get its full step trace:

```bash
# Replace <QID> with each query_id from above
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      step_seq,
      step_name,
      step_type,
      status,
      latency_ms,
      parallel_group,
      LEFT(data_summary::text, 100) AS data_summary_preview
    FROM query_trace_steps
    WHERE query_id = '<QID>'
    ORDER BY step_seq;
  "
```

**Look for:** the LAST step that completed before the timeout. That's where production hung.

### B.5 — signal_states query plan check (likely culprit for timeouts)

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    EXPLAIN ANALYZE
    SELECT signal_id, query_date, state, confidence, dasha_system
    FROM signal_states
    WHERE chart_id = 'abhisek_mohanty_primary'
      AND query_date BETWEEN '2026-01-01' AND '2026-12-31'
      AND state IN ('lit', 'ripening')
    LIMIT 50;
  "
```

**Look for:**
- Sequential Scan on signal_states → CONFIRMED INDEX GAP (no composite index on (chart_id, query_date, state))
- Index Scan → fine, latency is from elsewhere
- Execution Time → should be < 100ms; if > 1000ms, this is the timeout cause

### B.6 — Existing indexes on signal_states

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'signal_states';
  "
```

**Hypothesis:** migration 023 created basic primary key but no composite index on the columns query_signal_state.ts actually filters by. A 1M-row sequential scan on every signal_state query explains 30s+ latency.

---

## §C — Cross-reference with the 2 PASSING queries

What did GQ-008 (holistic, PASS) and GQ-010 (discovery, PASS) do differently?

```bash
PGPASSWORD=$(grep -E "^DB_PASSWORD=" .env.rag | cut -d= -f2) \
  psql -h 127.0.0.1 -p 5433 -U amjis_app -d amjis -c "
    SELECT
      ae.query_id,
      ae.query_class,
      ae.latency_ms,
      ae.tool_bundles,
      LEFT(ae.query_text, 80) AS preview
    FROM audit_events ae
    WHERE ae.created_at >= '2026-05-18T10:30:00Z'
      AND ae.created_at <= '2026-05-18T11:15:00Z'
      AND ae.audit_status = 'ok'
    ORDER BY ae.created_at;
  "
```

Compare the `tool_bundles` field on the PASSes vs the FAILs. If the PASSes used ONLY the old tool set and the FAILs used new tools, that's the smoking gun.

---

## §D — Hypothesis tree (rank these by likelihood after §B-C)

H1. **signal_states index gap** — 1M rows + no composite index → seq scan on every query_signal_state call → timeout. Fix: add `CREATE INDEX idx_signal_states_chart_date_state ON signal_states (chart_id, query_date, state)`.

H2. **detectM9Query false-positive** — the few-shot injection in pipeline_planner.ts fires on non-M9 queries, derailing them to multi_school_triangulation routing. Fix: tighten the regex in detectM9Query.

H3. **Synthesis prompt + new tool output shape mismatch** — synthesis was tuned on the old tool set's `ToolBundleResult` shape; new tools (LEL, signal_state, M9) return shapes the synthesis prompt doesn't grok → empty/low-quality answers (the 7 with 0% on B11/citations/calibration). Fix: update synthesis prompt to handle the new tools' output shape.

H4. **Bundle bloat** — the planner now includes lel_query + signal_state + multi_school in plans where they weren't actually needed → exceeded token budget → context truncation → degraded synthesis. Fix: tighten planner R-rules to be more selective.

H5. **Classical attribution lookup latency** — 2330 rows now (vs 420); maybe queries got slower despite indexes. Fix: add classical_attributions index.

H6. **Cold-start hit** — new revision amjis-web-00210-qzg may have slow cold start; eval ran shortly after deploy. Fix: rerun eval after warm-up.

The §B inspection results will indicate which hypothesis is correct (or whether it's a combination).

---

## §E — Report back

Deliver to native in this exact Markdown shape:

```markdown
# Phase 2 Regression Diagnostic — Report

## Eval run details
- Run ID: 8989aa3e-8893-4cfc-ac9e-857ece3a4f39
- Deploy revision: amjis-web-00210-qzg
- 15 fixtures: 2 PASS, 7 FAIL, 5 TIMEOUT, 1 EMPTY

## §B.1 Fixtures run + outcomes
[table of gq_id × status × latency × class]

## §B.2 Planner output per fixture
- Did the planner select new tools on failing queries? <yes/no/partial>
- detectM9Query false-positives observed? <yes/no — N times>
- Plans that look malformed? <list of gq_ids>

## §B.3 Tool execution profile
[per-tool table: calls, avg_ms, max_ms, errors, zero_rows]
- Top latency offender: <tool_name> at <max_ms>ms
- Tools that returned zero_rows when they should have returned data: <list>

## §B.4 Timeout root cause
- 5 timeouts identified: <gq_ids>
- Common pattern: <description of which step hangs>
- Stuck at step: <step_name>

## §B.5 signal_states EXPLAIN ANALYZE
- Index used: <yes/no — index name>
- Execution time: <X>ms
- Scan type: <Seq Scan / Index Scan / Bitmap Heap Scan>

## §B.6 signal_states existing indexes
[paste the pg_indexes output]

## §C 2-PASS analysis
- GQ-008 tools used: <list>
- GQ-010 tools used: <list>
- Pattern: <did PASSes avoid the new tools?>

## §D Hypothesis ranking after evidence
1. <strongest hypothesis>: <evidence>
2. <next>: <evidence>
...

## Recommended next action
- <Specific fix proposal — most likely: surgical fix for top hypothesis>
- Rollback advisability: <yes / no / partial — and why>
```

---

## §F — Hard rules

- **READ-ONLY.** No INSERT/UPDATE/DELETE. No file modifications. No commits.
- Stay on `analysis/backend-data-pipeline-perf-audit` in `/Madhav-analysis`. Never touch /Madhav.
- If any DB query takes > 30s, kill it. Don't load production into a death spiral.
- If the eval run ID `8989aa3e-...` produces 0 rows in any query_plan_log / audit_events / tool_execution_log query, the eval may have used a different correlation field — try matching by timestamp range instead.
- Do NOT propose fixes that involve modifying production data. Index additions are deferred to a follow-up brief if H1/H5 confirmed.
- Time-box this brief to 30 min. If §B inspection is incomplete after 30 min, deliver §E with whatever has been gathered and flag the gaps.

---

*End PHASE_2_REGRESSION_DIAGNOSTIC_BRIEF_v1_0.md. Successor: a surgical fix-forward brief authored from this brief's recommended-next-action, OR a rollback decision if the regression is severe and root cause is structural.*
