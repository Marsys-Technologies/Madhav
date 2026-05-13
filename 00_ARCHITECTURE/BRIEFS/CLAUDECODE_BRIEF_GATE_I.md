---
brief_id: GATE-I-PERF-CMD-001
version: 1.0
status: ACTIVE
authored_by: Claude Opus 4.7 (Gate I — Performance Command Center Design Session) — 2026-05-12
supersedes: none
purpose: >
  Design and ship a super-admin-gated /performance dashboard that captures every
  consume-triggered and eval-triggered query into a unified log, computes seven
  P0 pipeline KPIs across four bundles, surfaces them with a time-window picker
  and KPI tiles + sparklines, and provides an on-demand LLM-judge to label
  plan accuracy on consume queries. Net-new. No equivalent exists today.
executor: Claude Code Sonnet 4.6 (Anti-Gravity, VS Code, --dangerously-skip-permissions)
working_directory: /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center
branch: feature/gate1-perf-command-center
model_preference: gemini-2.5-pro (critical); gemini-2.0-flash-lite (LLM judge + non-critical)
migration_range: 043–044 (only)
gate_pair: marsys-gate1-perf-center worktree (independent of Gates II + III)
---

# CLAUDECODE_BRIEF — Gate I: Performance Command Center

## §0 — Read This First

You are building the Performance Command Center for MARSYS-JIS — a brand-new, super-admin-gated portal section at `/performance`. It ingests every consume-triggered and eval-triggered query into a unified table, computes seven KPIs across four bundles (pipeline correctness, answer quality, performance health, retrieval health), and presents them on a single landing page with a time-window picker, KPI tiles + sparklines, and a filterable query log that drills into the existing TracePanel. Eval-script captures auto-hook (every eval run writes to the new tables). Consume queries' plan accuracy is labeled by an **on-demand LLM judge** (gemini-2.0-flash-lite) triggered from the UI — no automatic judging.

This gate is entirely net-new code paths. You will not modify the consume pipeline, the trace components, or the navigation rail. The navigation entry for `/performance` is added during **Gate IV** (post-merge cleanup), not here.

Before writing any code, read in order:
1. `CLAUDE.md` (project root) — orientation, B.10 / B.11 rules, file-placement policy
2. `00_ARCHITECTURE/briefs/OPUS_PLANNING_SESSION_v2_0.md` — gate-master plan, scope rules, migration ranges (§3.7, §3.8), CLAUDECODE_BRIEF format (§10)
3. `00_ARCHITECTURE/ROOT_FILE_POLICY.md` — file placement decision tree
4. This brief, end-to-end
5. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 — confirm M5 is INCOMING and pre-M5 gates active

Then proceed to §1 entry gates.

---

## §1 — Entry Gates

All must be GREEN before W0 starts:

- [ ] Worktree exists at `/Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center` on branch `feature/gate1-perf-command-center`
- [ ] `cd platform && npm install` completed without errors in this worktree
- [ ] You have read CLAUDE.md, OPUS_PLANNING_SESSION_v2_0.md, ROOT_FILE_POLICY.md, this brief
- [ ] Latest applied migration in `platform/supabase/migrations/` is `042_tool_execution_log_scores.sql` — nothing newer
- [ ] Cloud SQL Auth Proxy is running locally OR a test Postgres is reachable; `pgvector` extension is available
- [ ] You confirm SWR (or the project's prevailing client-data hook) is available in `platform/src` — confirm by inspection, not assumption
- [ ] You confirm the existing super-admin auth pattern by reading the route guard used by `/observatory` or `/audit` — note file path and pattern

If any entry gate fails, STOP and report. Do not proceed.

---

## §2 — Scope

### may_touch

- `platform/src/app/performance/**` — new pages
- `platform/src/app/api/performance/**` — new API routes
- `platform/src/components/performance/**` — new components (this is **Gate I's exclusive territory**)
- `platform/src/lib/performance/**` — new lib code
- `platform/supabase/migrations/043_*.sql` — new schema
- `platform/supabase/migrations/044_*.sql` — new schema
- The audit-event finalize call-site for consume queries (identified in W0.B) — **only** to add a fire-and-forget `writeConsumePerformanceRow(...)` call. Do not change audit semantics.
- The eval-script entry point (identified in W0.A) — **only** to add `writeEvalRun(...)` and per-query `writeEvalPerformanceRow(...)` writes. Do not change scoring logic.
- Test files under `platform/**/__tests__/` matching the new modules above
- This file itself, on session close, to flip `status: COMPLETE` and move to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_I_v1_0.md`

### must_not_touch

- `components/trace/**` (Gate II territory; including TraceDrawer, TracePanel, PipelineLifecycleView, all step-detail variants)
- `lib/admin/trace_assembler.ts` (Gate II territory; read-only consumer via existing `/api/admin/trace/[query_id]`)
- `components/consume/**` (Gate III territory; ConsumeChat, AnswerView, StreamingAnswer, TierPicker, LogPredictionAction, etc.)
- `app/api/chat/consume/route.ts` (frozen)
- `components/shared/AppShellRail.tsx` (Gate IV nav cleanup)
- `components/shared/MobileNavSheet.tsx` (Gate IV nav cleanup)
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `06_LEARNING_LAYER/**` (corpus / governance)
- Migrations `042_*` and below (frozen)
- Migrations `045_*` and above (reserved for Gates II / III)
- Any file under `app/audit/**` and `app/observatory/**` (existing portal sections; read-only references)
- New npm packages — if you find a missing dependency, flag it as a manual step at the top of `SESSION_LOG` entry and choose a path that uses what's already installed. Do not run `npm install <new-pkg>`.

Run `git diff --name-only main` at any milestone to verify; any file outside `may_touch` is a scope violation.

---

## §3 — Work Items

### W0 — Audit step (no code yet)

Produce `GATE_I_AUDIT.md` at the worktree root with the answers to A–E below. Commit before starting W1. The audit is load-bearing — every downstream W references its findings.

**A. Eval entry point.** Where do the eval scripts live? Specifically the golden-set v1.2 runner that produces `recall=0.983 precision=0.961` (per memory `project_pipeline_gap_plan_complete`). List the file path(s), the CLI invocation, and the function/section where per-query results are computed today.

**B. Consume audit finalize hook.** What function (file + signature) finalizes the audit event after a successful consume query? This is where `writeConsumePerformanceRow(...)` (W2) will be invoked fire-and-forget.

**C. Phase 8 outcome table.** What table holds prediction outcome labels populated by `/audit/predictions`? Confirm table name + columns. The calibration KPI (W5) joins against this.

**D. Super-admin auth pattern.** How does `/observatory` gate super_admin? Cite the file + line where the role check happens. W12 reuses this pattern.

**E. Audit-event field mapping.** For a finalized consume audit event, document where each of the following lives in code: `query_class`, `plan_type`, `tools_selected`, `planner_confidence`, `validator_verdict`, `disclosure_tier`, `synthesis_status`, `citation_count`, `citation_objects` (for B.10 detection), `latency_planner_ms`, `latency_retrieval_ms`, `latency_synthesis_ms`, `latency_total_ms`, retrieval-hit signal (any retrieval result above threshold), `retrieval_score_top1`, presence of `[EXTERNAL_COMPUTATION_REQUIRED]` marker in synthesis text, L2.5 stage firing indicator, `is_prediction` flag if present.

**F. SWR confirmation.** Is `swr` in `platform/package.json`? Or does the project use `@tanstack/react-query`? W13 uses whichever is present.

Do not proceed to W1 until `GATE_I_AUDIT.md` is committed.

---

### W1 — Migrations 043 + 044

`platform/supabase/migrations/043_performance_schema.sql` creates `performance_queries`:

```sql
CREATE TABLE performance_queries (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audit_event_id              uuid NULL,                       -- FK named in W0.B; ON DELETE SET NULL
  eval_run_id                 uuid NULL,                       -- FK added in 044 once eval_runs exists
  source                      text NOT NULL CHECK (source IN ('consume','eval')),
  created_at                  timestamptz NOT NULL DEFAULT now(),

  query_text                  text,
  query_class                 text,
  plan_type                   text,
  plan_tools_selected         jsonb,
  planner_confidence          numeric,

  latency_planner_ms          integer,
  latency_retrieval_ms        integer,
  latency_synthesis_ms        integer,
  latency_total_ms            integer,

  citations_present           boolean,
  citation_count              integer DEFAULT 0,
  synthesis_status            text,                            -- 'success' | 'failure' | 'partial'
  validator_verdict           text,
  disclosure_tier             text,

  b10_violation               boolean,                         -- W4 detector output
  b11_violation               boolean,                         -- W4 detector output
  retrieval_hit               boolean,
  retrieval_score_top1        numeric,

  plan_accuracy_label         text DEFAULT 'unjudged'
                              CHECK (plan_accuracy_label IN
                                ('correct','wrong','ambiguous','unjudged','n_a')),
  plan_accuracy_source        text                             -- 'golden' | 'judge' | NULL
                              CHECK (plan_accuracy_source IN ('golden','judge') OR plan_accuracy_source IS NULL),

  is_prediction               boolean DEFAULT false,
  prediction_outcome_state    text DEFAULT 'n_a'
                              CHECK (prediction_outcome_state IN
                                ('pending','observed_correct','observed_incorrect','n_a'))
);

CREATE INDEX perf_queries_created_at_idx       ON performance_queries (created_at DESC);
CREATE INDEX perf_queries_source_created_idx   ON performance_queries (source, created_at DESC);
CREATE INDEX perf_queries_class_created_idx    ON performance_queries (query_class, created_at DESC);
CREATE INDEX perf_queries_audit_event_idx      ON performance_queries (audit_event_id);
CREATE INDEX perf_queries_eval_run_idx         ON performance_queries (eval_run_id);
```

`platform/supabase/migrations/044_eval_runs_and_judge.sql` creates two tables and finalizes the FK on `performance_queries.eval_run_id`:

```sql
CREATE TABLE eval_runs (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at                  timestamptz NOT NULL DEFAULT now(),
  finished_at                 timestamptz,

  golden_set_version          text NOT NULL,
  planner_prompt_version      text,
  synthesis_prompt_version    text,
  triggered_by                text,                            -- script name OR user_id

  query_count                 integer DEFAULT 0,
  plan_accuracy_recall        numeric,
  plan_accuracy_precision     numeric,
  citation_rate               numeric,
  avg_latency_total_ms        integer,
  synthesis_pass_rate         numeric,
  retrieval_hit_rate          numeric,
  b10_compliance_rate         numeric,
  b11_compliance_rate         numeric,

  notes                       text
);

CREATE INDEX eval_runs_created_idx ON eval_runs (created_at DESC);

CREATE TABLE performance_judge_verdict (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  performance_query_id        uuid NOT NULL
                              REFERENCES performance_queries(id) ON DELETE CASCADE,
  judge_run_id                uuid NOT NULL,
  judge_model                 text NOT NULL,
  planner_verdict             text NOT NULL
                              CHECK (planner_verdict IN ('correct','wrong','ambiguous')),
  planner_reasoning           text,
  triggered_by_user_id        uuid,
  created_at                  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX judge_verdict_pq_idx        ON performance_judge_verdict (performance_query_id);
CREATE INDEX judge_verdict_run_idx       ON performance_judge_verdict (judge_run_id);

ALTER TABLE performance_queries
  ADD CONSTRAINT performance_queries_eval_run_fk
  FOREIGN KEY (eval_run_id) REFERENCES eval_runs(id) ON DELETE SET NULL;
```

Apply both to the local dev DB. Verify with `\d performance_queries`, `\d eval_runs`, `\d performance_judge_verdict`. Confirm all FK constraints resolve and CHECK constraints accept the documented values.

**Migration safety:** before running 043, query `pg_constraint` and confirm no existing table named `performance_queries` or `eval_runs` exists. Per feedback memory `feedback_swap_fk_dependents`, enumerate dependents before any DELETE — not applicable here (no DELETEs), but apply the discipline reflexively.

---

### W2 — Consume-query ingestion writer

`platform/src/lib/performance/ingestion.ts` exports:

```ts
export async function writeConsumePerformanceRow(
  auditEvent: AuditEvent,            // type alias from existing audit lib
): Promise<void>
```

Behavior:
1. Resolve all fields per the W0.E mapping.
2. Run `detectB10Violation(...)` and `detectB11Violation(...)` (W4) to populate b10/b11 flags.
3. Insert one row into `performance_queries` with `source='consume'`, `plan_accuracy_label='unjudged'`, `plan_accuracy_source=NULL`, `audit_event_id` set to the audit event's id.
4. Failures: log and swallow — must never block or fail a consume response.

Wire into the consume audit finalize call-site identified in W0.B. Pattern: fire-and-forget inside `void writeConsumePerformanceRow(event).catch(err => logger.error(...));` — do not `await`.

---

### W3 — Eval-script auto-hook writer

Same module as W2. Exports:

```ts
export async function writeEvalRun(
  meta: { golden_set_version: string; planner_prompt_version?: string;
          synthesis_prompt_version?: string; triggered_by: string }
): Promise<{ runId: string }>

export async function writeEvalPerformanceRow(
  runId: string,
  rowData: EvalPerformanceRow           // includes deterministic plan_accuracy_label from golden compare
): Promise<void>

export async function finalizeEvalRun(
  runId: string,
  aggregates: EvalRunAggregates
): Promise<void>
```

Wire into the eval entry point identified in W0.A:
- Before the first query: `const { runId } = await writeEvalRun(...);`
- Per query, after scoring: `await writeEvalPerformanceRow(runId, ...)` with `source='eval'`, `eval_run_id=runId`, and `plan_accuracy_label='correct'|'wrong'|'ambiguous'` derived from the existing golden-compare logic, `plan_accuracy_source='golden'`.
- After all queries: `await finalizeEvalRun(runId, { finishedAt, queryCount, recall, precision, citationRate, avgLatencyMs, synthesisPassRate, retrievalHitRate, b10ComplianceRate, b11ComplianceRate, notes })`.

Do NOT change scoring logic; only persist what the script already computes.

---

### W4 — Compliance detector

`platform/src/lib/performance/compliance.ts`. Pure functions, no side effects:

```ts
export function detectB10Violation(input: {
  synthesisText: string;
  citationObjects: Array<{ source_layer: 'L1'|'L2_5'|'L3'; citation_id: string }>;
}): boolean
```

**B.10 rule (per CLAUDE.md §I.B.10):** the LLM must never invent numerical chart values; missing values must be marked `[EXTERNAL_COMPUTATION_REQUIRED]`. Violation if synthesisText contains numeric tokens that look like chart values (e.g. degree / minute / arc patterns: `\d{1,2}°\s*\d{1,2}['′]` or `\d+\s*deg\b` or any of the prevailing patterns observed in current synthesis output) AND no `[EXTERNAL_COMPUTATION_REQUIRED]` marker AND no L1 citation present. Implement as deterministic regex/heuristic — no LLM call. Document the exact heuristic in code comments. Surface false-positive risk in the unit test fixtures (W14 covers 12 cases).

```ts
export function detectB11Violation(auditEvent: AuditEvent): boolean
```

**B.11 rule:** every query routes through L2.5 Holistic Synthesis first. Violation if the audit event's stage sequence does NOT include an L2.5 retrieval/synthesis indicator (exact field name from W0.E).

Both functions: side-effect-free, table-driven tests in W14.

---

### W5 — KPI aggregation API

`platform/src/app/api/performance/kpis/route.ts`. Server-side handler.

```
GET /api/performance/kpis
  ?window_start=ISO8601
  &window_end=ISO8601
  &source=consume|eval|all          (default: all)
```

Response:

```json
{
  "window": { "start": "...", "end": "...", "source": "all" },
  "bundles": {
    "pipeline_correctness": {
      "plan_accuracy_recall":    0.97,
      "plan_accuracy_precision": 0.95,
      "plan_accuracy_n":         46,
      "plan_accuracy_consume_unjudged_n": 14,
      "citation_rate":           0.84,
      "citation_n":              312
    },
    "answer_quality": {
      "calibration_brier":       0.18,
      "calibration_n":           12,
      "b10_compliance_rate":     0.99,
      "b11_compliance_rate":     1.00,
      "compliance_n":            312
    },
    "performance_health": {
      "latency_p50_ms":          1800,
      "latency_p95_ms":          5400,
      "latency_by_class": {
        "factual":      { "p50": 900,  "p95": 2100 },
        "interpretive": { "p50": 2300, "p95": 6100 },
        "predictive":   { "p50": 2800, "p95": 7200 },
        "discovery":    { "p50": 2100, "p95": 5400 },
        "holistic":     { "p50": 3200, "p95": 8400 }
      },
      "synthesis_pass_rate":     0.98,
      "synthesis_n":             312
    },
    "retrieval_health": {
      "retrieval_hit_rate":      0.93,
      "retrieval_n":             312
    }
  },
  "sparklines": {
    "pipeline_correctness":   [{ "t": "ISO8601", "v": 0.96 }, ...],
    "answer_quality":         [...],
    "performance_health":     [...],
    "retrieval_health":       [...]
  }
}
```

Computation rules:
- **plan_accuracy_recall / precision** — denominator is rows with `plan_accuracy_label IN ('correct','wrong')`. For consume rows that are 'unjudged', surface separately as `plan_accuracy_consume_unjudged_n`; do not include in recall/precision. Recall = correct / (correct + wrong) on rows tagged as "should-have-fired" by the golden set (eval) or as "judged-positive" (judge); precision = analogous. For consume rows judged by the LLM, treat recall == precision (judge gives one verdict per row); the eval slice carries true recall/precision per existing eval script. Average the two slices weighted by sample size where both are present; if only one source has data, return that source's value with `plan_accuracy_source_breakdown` field.
- **citation_rate** — `count(citations_present=true) / count(*)`.
- **calibration_brier** — Brier score over rows where `is_prediction=true AND prediction_outcome_state IN ('observed_correct','observed_incorrect')`. Joins against the Phase 8 outcome table (W0.C). Brier = mean((forecast - outcome)^2) where forecast is `planner_confidence` (or the canonical prediction-confidence field per W0.E) and outcome is 0/1. Lower is better; surface as-is, no inversion.
- **b10/b11_compliance_rate** — `1 - (count(violation=true) / count(*))`.
- **latency percentiles** — Postgres `percentile_cont` over `latency_total_ms`, optionally bucketed by `query_class`.
- **synthesis_pass_rate** — `count(synthesis_status='success') / count(*)`.
- **retrieval_hit_rate** — `count(retrieval_hit=true) / count(*)`.
- **sparklines** — 24 bucket points spanning the window, computed per bundle's headline metric. Use Postgres `width_bucket` or `date_bin` for bucketing.

Cache: none at P0 (per native decision — keep it simple; revisit if latency becomes a concern). Performance budget: ≤ 800ms p95 on a 30-day window with 5k rows.

---

### W6 — Query log API

`platform/src/app/api/performance/queries/route.ts`.

```
GET /api/performance/queries
  ?window_start=ISO8601
  &window_end=ISO8601
  &source=consume|eval|all          (default: all)
  &query_class=...                  (multi via repeated param)
  &validator_verdict=...
  &plan_accuracy_label=...
  &b10_violation=true|false
  &b11_violation=true|false
  &page=1                           (default: 1)
  &page_size=50                     (default: 50, max: 200)
```

Response:
```json
{
  "page": 1,
  "page_size": 50,
  "total": 312,
  "rows": [ { /* performance_queries row + judge_verdict_summary if present */ } ]
}
```

Each row includes a derived `judge_verdict_summary` field (latest verdict from `performance_judge_verdict` for that row, or null).

---

### W7 — Eval runs APIs

- `GET /api/performance/eval-runs?page=1&page_size=20` — list, ordered `created_at DESC`. Returns paginated `eval_runs` rows.
- `GET /api/performance/eval-runs/[id]` — returns the run metadata + a `queries_summary` block (counts by `plan_accuracy_label`, by `synthesis_status`, by `validator_verdict`). The constituent-query list is fetched by the page via W6 with `eval_run_id` query param (add support in W6).

---

### W8 — Judge endpoint

`platform/src/app/api/performance/judge/route.ts`.

```
POST /api/performance/judge
Body: { window_start: ISO8601, window_end: ISO8601, limit: number (max 200) }
```

Behavior:
1. Acquire Postgres advisory lock `pg_try_advisory_lock(hashtext('gate1.performance.judge'))`. If not acquired, return HTTP 409 with `{ error: 'judge_run_in_progress' }`.
2. Generate `judge_run_id = uuid_v4()`.
3. Query unjudged consume rows in window:
   ```sql
   SELECT id, query_text, query_class, plan_type, plan_tools_selected, planner_confidence
   FROM performance_queries
   WHERE source = 'consume'
     AND plan_accuracy_label = 'unjudged'
     AND created_at BETWEEN $1 AND $2
   ORDER BY created_at DESC
   LIMIT LEAST($3, 200);
   ```
4. For each row, call `gemini-2.0-flash-lite` with the prompt from `platform/src/lib/performance/judge_prompt.ts` (W8a below). Parse the verdict.
5. Transactionally insert one `performance_judge_verdict` row + update `performance_queries.plan_accuracy_label` and `.plan_accuracy_source='judge'`.
6. Release the advisory lock.
7. Return `{ judge_run_id, judged_count, breakdown: { correct, wrong, ambiguous }, model: 'gemini-2.0-flash-lite' }`.

Failure handling: per-row try/catch; record `'ambiguous'` with reasoning text `'judge_call_failed: <err>'` for any row whose judge call throws. Do not abort the run on a single failure.

#### W8a — Judge prompt

`platform/src/lib/performance/judge_prompt.ts` exports a v1.0 prompt template. **Read the existing planner prompt source of truth** (PLANNER_PROMPT v2.1+ — per memory `project_pipeline_gap_plan_complete`, latest committed v2.1 with 7 added rules) to anchor the rubric. The judge sees: original query text, planner output (`query_class`, `plan_type`, `tools_selected`). It outputs structured JSON:

```json
{
  "verdict": "correct" | "wrong" | "ambiguous",
  "reasoning": "<1–2 sentences citing rubric clauses>"
}
```

Use Gemini structured-output mode (JSON schema) if available in the project's existing Gemini client. If not, parse JSON from text response and fail gracefully on parse error (record as 'ambiguous').

---

### W9 — `/performance` landing page

`platform/src/app/performance/page.tsx`. Server component for initial data fetch; nested client components for interactions. Layout from top to bottom:

1. **Header bar** (client) — title "Performance Command Center", super-admin badge.
2. **Time-window picker** (client, sticky) — preset chips: "Last 24h", "Last 7 days" (default), "Last 30 days", "All-time", "Custom". The "Custom" option opens a date-range picker (use shadcn `Calendar` + popover; do not install a new picker library). State persists to URL query params so the view is shareable.
3. **KPI tile grid** (client) — 4 tiles in a responsive 2×2 grid (collapses to 1-column on narrow viewports). Each tile renders via `<KpiTile bundle="pipeline_correctness" />` etc:
   - Bundle name + brief description tooltip
   - Headline metric (largest number)
   - Secondary metrics (smaller, below headline)
   - Delta vs equivalent prior window (e.g. last-7d vs prior-7d): green ↑ / red ↓ / grey "—" if insufficient data
   - Sparkline (recharts `LineChart`, dark theme matching Observatory)
   - For `pipeline_correctness`: if `plan_accuracy_consume_unjudged_n > 0`, show a small "Run judge" affordance.
4. **"Run plan-accuracy judge" affordance** (client) — opens a modal:
   - Window selector defaults to current view's window
   - Limit slider (10–200, default 100)
   - "Run judge" button → POST W8 → toast on completion → SWR mutate
5. **Query log section** (client):
   - Filter row: source (chips), query class (multi-select), validator verdict (multi-select), plan_accuracy_label (multi-select), B.10 violation (toggle), B.11 violation (toggle)
   - Table (use existing shadcn `Table` if available, otherwise a minimal table component under `components/performance/QueryLogTable.tsx`):
     - Timestamp · Source · Class · Plan type · Plan accuracy · Validator verdict · B.10 · B.11 · Citations · Latency (ms) · Synthesis status
   - Click a row → open TracePanel (W11)
   - Pagination footer (50 per page default)
6. **Manual "Refresh" button** in header right (mutates SWR keys).

Auto-refresh: SWR (or react-query) with `refreshInterval: 45000` and `refreshWhenHidden: false`. Confirm the project's prevailing client-data lib in W0.F and use that.

Dark theme: match Observatory's existing palette (per memory `project_observatory_redesign`). Inherit Tailwind tokens; do not redefine colors.

---

### W10 — `/performance/eval-runs` pages

- `app/performance/eval-runs/page.tsx` — list view: paginated table of eval runs ordered latest-first. Columns: timestamp, golden_set_version, planner_prompt_version, query_count, recall, precision, citation_rate, synthesis_pass_rate, retrieval_hit_rate, "View detail" link.
- `app/performance/eval-runs/[id]/page.tsx` — detail view:
  - Header block with run metadata + all aggregate KPIs
  - Constituent-query table: reuse `<QueryLogTable />` from W9 filtered to `eval_run_id=:id`, with all the same row-click drill-down behavior

---

### W11 — TracePanel drill-down integration

When a row in `QueryLogTable` is clicked, open the existing `TracePanel` for that query.

`platform/src/components/performance/TracePanelLauncher.tsx`:
- Accepts `queryId: string` (resolves to `performance_queries.audit_event_id`).
- Dynamically imports `TracePanel` (`next/dynamic`, `{ ssr: false }`) so this gate does not statically depend on Gate II's evolving TracePanel surface.
- Renders TracePanel inside a portal-friendly side drawer (use shadcn `Sheet`).
- This wrapper is the **only** new file that touches the trace surface. TracePanel itself is read-only from Gate I.

If, on import, TracePanel's prop contract has shifted in a way that breaks integration, **do not modify TracePanel** — instead log the breakage in `SESSION_LOG`, render a fallback message "Trace unavailable — see /audit/[query_id]", and link to the audit detail page. The drill-down is required to be wired (AC.8); the fallback path counts as wired with a documented gotcha.

---

### W12 — Super-admin auth gating

Reuse the route guard pattern identified in W0.D for every:
- Page under `/performance/**`
- API route under `/api/performance/**`

Implementation pattern at every route handler entry:
- Resolve user from Firebase Auth session cookie
- Look up the user's role (per existing pattern)
- If role !== 'super_admin', return 403 (API) or redirect to `/` (pages)

No middleware — match the project's existing per-route pattern unless W0.D explicitly shows a middleware-based pattern.

Citation auth (per memory `project_ganga_baseline`): the project uses `__session` cookie, not Bearer token. Match.

---

### W13 — Polling refresh client

Hook (in the prevailing client-data lib per W0.F):
- `refreshInterval: 45000`
- `refreshWhenHidden: false`
- `revalidateOnFocus: true`
- Manual "Refresh now" button calls `mutate()` on the relevant keys (`/api/performance/kpis`, `/api/performance/queries`)
- Loading skeletons via existing skeleton components (`components/ui/skeleton` if present)

---

### W14 — Test suite (Vitest)

**Vitest 4.x note (per feedback memory `feedback_llm_model_selection` and Phase 9 hotfix lesson):** use `vi.fn().mockImplementation(function () { ... })` — non-arrow function — for any mock that needs `this` binding or that proxies through Vitest's internal hooks. Arrow functions break under Vitest 4.x.

Minimum coverage:

- `platform/src/lib/performance/compliance.test.ts` — **12+ cases**
  - B.10: present marker + numerics → no violation
  - B.10: missing marker + numerics + no L1 citation → violation
  - B.10: missing marker + numerics + L1 citation → no violation
  - B.10: prose only (no numerics) → no violation
  - B.10: false-positive guard — year tokens (e.g. "1984") not flagged as chart values
  - B.10: degree-minute pattern (`12°34'`) flagged
  - B.11: audit event with L2.5 stage → no violation
  - B.11: audit event without L2.5 stage → violation
  - B.11: malformed audit event (missing stage list) → defaults to violation (fail-closed)
  - … 3 more covering edge cases discovered during W4 implementation

- `platform/src/lib/performance/ingestion.test.ts` — **6+ cases**
  - `writeConsumePerformanceRow` happy path
  - `writeConsumePerformanceRow` failure swallowed (DB unavailable → no throw)
  - `writeEvalRun` returns runId + persists row
  - `writeEvalPerformanceRow` ties to runId
  - `finalizeEvalRun` updates aggregates
  - Concurrent eval-row writes under one run

- `platform/src/lib/performance/kpi_aggregator.test.ts` — **6+ cases**
  - Plan accuracy with mixed golden + judge rows
  - Citation rate with zero rows (returns null, not NaN)
  - Brier on 0 outcomes (returns null)
  - Latency p95 correctness
  - Sparkline bucketing edge case (window spans daylight-savings boundary)
  - Source filter (consume-only vs eval-only vs all)

- `platform/src/lib/performance/judge.test.ts` — **6+ cases**
  - Mock Gemini returns 'correct' → verdict + label update
  - Mock Gemini throws → 'ambiguous' with error reasoning
  - Advisory lock held → 409
  - Limit cap enforced (request 500 → run on 200)
  - Idempotent: re-running with same window does not re-judge already-judged rows
  - Breakdown counts match inserted verdicts

- `platform/src/app/api/performance/__tests__/auth.test.ts` — **6+ cases**
  - 403 on each of /api/performance/kpis, /queries, /eval-runs, /eval-runs/[id], /judge for non-super_admin
  - 200 on each for super_admin
  - Missing session cookie → 401 (or 403, match existing pattern)

- `platform/src/components/performance/__tests__/KpiTile.test.tsx` — **4+ cases**
  - Renders headline + delta + sparkline shape
  - Delta arrow color: green for improvement, red for regression, grey for insufficient data
  - Sparkline tolerates empty data array (renders empty state, no crash)
  - Tooltip surfaces bundle description

- `platform/src/components/performance/__tests__/QueryLogTable.test.tsx` — **4+ cases**
  - Renders rows with all column values
  - Row click invokes onSelect with row id
  - Filter chip click filters the visible rows (component-state filter, separate from API filter — confirm both layers test)
  - Pagination buttons enabled/disabled correctly at edges

**Bar:** ≥ 40 new tests, all green. Existing test suite remains fully green.

---

## §4 — Acceptance Criteria

- [ ] AC.1 — Migrations 043 and 044 apply cleanly on a fresh DB; `\d performance_queries`, `\d eval_runs`, `\d performance_judge_verdict` all match the schema declared in W1
- [ ] AC.2 — A successful consume query produces exactly one `performance_queries` row with `source='consume'`, `plan_accuracy_label='unjudged'`, and all W0.E fields populated; consume response latency is not measurably degraded (within ±5% of pre-gate baseline)
- [ ] AC.3 — Triggering the existing golden-set eval script produces exactly one `eval_runs` row + 46 `performance_queries` rows tagged `source='eval'` with deterministic `plan_accuracy_label`; aggregate scores on the eval_runs row equal what the eval script already prints today (cross-check by direct comparison)
- [ ] AC.4 — `GET /api/performance/kpis` returns all 4 bundle blocks with non-null values for a populated 7-day window; null/undefined values are surfaced explicitly (not silently coerced to 0) for empty windows
- [ ] AC.5 — Sparklines render on each KPI tile using recharts (24 buckets) and respect the active time window
- [ ] AC.6 — Time-window picker switches between Last 24h / 7d / 30d / All-time / Custom; both KPI tiles and query log update on change; URL query params reflect the active window
- [ ] AC.7 — Query log filters function for source, query_class, validator_verdict, plan_accuracy_label, B.10, B.11; pagination works at default (50/page) and at max (200/page)
- [ ] AC.8 — Clicking a row in the query log opens TracePanel (or the documented fallback per W11) for that query; drill-down end-to-end verified manually
- [ ] AC.9 — `/performance/eval-runs` lists runs latest-first with all aggregate KPI columns visible
- [ ] AC.10 — `/performance/eval-runs/[id]` shows run metadata + constituent queries via the same QueryLogTable
- [ ] AC.11 — "Run judge" affordance: POST /api/performance/judge with window + limit returns judged_count > 0 when unjudged consume rows exist in window; rerunning the same window is idempotent (no double-judging); pipeline-correctness KPI tile updates on next refresh
- [ ] AC.12 — B.10 and B.11 detectors return correct values on the W14 12-case test fixture
- [ ] AC.13 — Non-super_admin users get HTTP 403 (API) or redirect to / (pages) on every `/performance/**` and `/api/performance/**` surface; super_admin gets 200
- [ ] AC.14 — Auto-refresh fires every 45s; manual refresh button works; refresh pauses when tab is backgrounded
- [ ] AC.15 — Regression check: `/audit`, `/observatory`, `/cockpit`, `/clients/[id]/consume`, and the consume API behave identically to pre-gate baseline (manual smoke + `npm test`)
- [ ] AC.16 — `npm test` green (≥ 40 new tests passing); `tsc --noEmit` clean; `eslint` clean

---

## §5 — LLM Stack

- **Default for any application logic in this gate:** `gemini-2.5-pro` — but **note that no synthesis-grade LLM call exists in Gate I scope** outside the judge. KPI aggregation, compliance detection, and ingestion are all deterministic SQL/regex code.
- **LLM judge (W8):** `gemini-2.0-flash-lite` — on-demand only, capped at 200 queries per run, advisory-locked to one run at a time.
- **BANNED:** `anthropic/claude-*` anywhere in this gate. Per memory `feedback_llm_model_selection` — Anthropic stack banned unless native explicitly requests. If you find an Anthropic reference in any file you touch, halt, flag it in `SESSION_LOG`, and replace with Gemini before continuing.

---

## §6 — Tests

See §3.W14. Minimum bar: ≥ 40 new tests, all green; existing test suite remains green.

Commands (must all pass before AC.16 can be ticked):

```bash
cd /Users/Dev/Vibe-Coding/Apps/marsys-gate1-perf-center/platform
npm test
npx tsc --noEmit
npx eslint .
```

---

## §7 — Migration Numbers

- **043** — `platform/supabase/migrations/043_performance_schema.sql`
- **044** — `platform/supabase/migrations/044_eval_runs_and_judge.sql`

Do not use `042_*` (frozen) or `045_*` and above (reserved for Gates II / III).

---

## §8 — Native Decisions Locked During Design (verbatim)

These are the scoping answers from the 2026-05-12 Opus design session. Do not relitigate. If you believe the design conflicts with a discovery made during W0 audit, halt and ask the native before proceeding.

1. **Nav placement:** `/performance` as top-level (peer to `/observatory`, `/audit`, `/cockpit`). Nav entry added in Gate IV, not here.
2. **Eval capture:** auto-hook eval scripts (every run writes via W3).
3. **P0 KPIs:** all 7 ship at launch — pipeline correctness (plan accuracy, citation rate), answer quality (calibration, B.10/B.11 compliance), performance health (latency by class, synthesis pass rate), retrieval health (retrieval hit rate).
4. **Source split:** unified `performance_queries` table with `source` tag.
5. **Refresh model:** polling at 45s, manual refresh button.
6. **Plan accuracy on consume queries:** LLM judge (gemini-2.0-flash-lite), **on-demand only** — no automatic judging cron, no inline-at-query judging. Native triggers from the UI.
7. **Calibration:** reuse Phase 8 outcome table (`/audit/predictions` form). `/performance` is read-only against it.
8. **Drill-down:** click a row → opens existing TracePanel for that query (W11 with documented fallback).
9. **Time windows:** preset chips (24h / 7d / 30d / All-time) + custom date-range picker.
10. **B.10/B.11 detection:** regex/heuristic over synthesis text + audit metadata. No LLM call.
11. **Retention / sampling:** none at P0. Store everything.
12. **Alerts:** deferred to P1.
13. **Landing layout:** single page — KPI tile grid + query log + sparklines + time-window picker.
14. **Eval runs:** separate `/performance/eval-runs` page (list + detail).
15. **Export (CSV/JSON):** deferred to P1.

---

## §9 — Session Close Checklist

- [ ] All 16 ACs above pass
- [ ] `npm test` green; `tsc --noEmit` clean; `eslint .` clean
- [ ] `GATE_I_AUDIT.md` (from W0) committed to worktree root
- [ ] No files touched outside `may_touch` — verify with `git diff --name-only main`
- [ ] Nav rail untouched — `git diff main -- components/shared/AppShellRail.tsx components/shared/MobileNavSheet.tsx` → empty diff
- [ ] Trace + consume untouched — `git diff main -- components/trace components/consume app/api/chat/consume` → empty diff
- [ ] Corpus untouched — `git diff main -- 01_FACTS_LAYER 025_HOLISTIC_SYNTHESIS 06_LEARNING_LAYER` → empty diff
- [ ] Migration sequence — only 043 and 044 added; nothing else under `platform/supabase/migrations/`
- [ ] This brief moved to `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_GATE_I_v1_0.md` with frontmatter `status: COMPLETE`, and the worktree-root copy deleted
- [ ] `00_ARCHITECTURE/SESSION_LOG.md` entry appended with: work items completed (W0–W14), all 16 AC pass/fail, file count, new-test count, rough LOC, any deviations from this brief with justification, manual-step flags (npm packages, etc.)
- [ ] Branch `feature/gate1-perf-command-center` is ready to merge (clean, rebased on main if needed)

---

## §10 — Notes for the Executor

- This gate is independent. Gates II and III run in parallel worktrees and will not collide with this one as long as you respect `must_not_touch`.
- If you discover during W0 that an assumption in this brief is wrong (e.g. the audit event does not carry `latency_*` fields where I claimed), document the gap in `GATE_I_AUDIT.md` and either (a) adapt this brief's W to the actual surface and note the deviation in `SESSION_LOG`, or (b) halt and consult the native if the gap is structural. Adapt freely on field-naming-only deltas; consult on missing capabilities.
- Per memory `feedback_gcs_layout_lookup`: this gate does not write GCS URIs. If you do at any point, read `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md` first.
- Per memory `feedback_artifact_callmcptool`: Cowork artifacts are not part of this gate's surface; do not use them here.
- B.10 and B.11 are project axioms (CLAUDE.md §I). The detectors in W4 are the operational embodiment of those axioms inside this gate; keep their logic visible and well-commented.

---

*End of CLAUDECODE_BRIEF — Gate I: Performance Command Center, v1.0, authored 2026-05-12 by Claude Opus 4.7.*
