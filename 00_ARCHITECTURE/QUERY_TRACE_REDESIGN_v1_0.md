---
artifact: QUERY_TRACE_REDESIGN_v1_0
canonical_id: QUERY_TRACE_REDESIGN
version: 1.0
status: CURRENT
created_date: 2026-05-05
author: Cowork + Opus 4.7 brainstorm
reference: OBS-S1/S2/S3 complete; trace redesign is the next major diagnostic layer
---

# MARSYS-JIS Query Trace — Complete Redesign Plan v1.0

## 1. Design Philosophy

**Principle 1: A trace is a story, not a log.** The current trace is a flat numbered list — a list of *what happened*. The new trace renders a *narrative of decisions and data*: at every node, the system made a choice between alternatives, fetched (or failed to fetch) data, and passed (or dropped) information forward. The UI's primary job is to make that narrative legible. This means the lifecycle is rendered as a **directed graph with decision branches**, not a list. Every node carries its own "input → decision → output" triad inline, never deferred to a lone right-side panel.

**Principle 2: Information density is a feature, not a bug.** Super-admins are debugging multi-stage LLM pipelines. They need to see classification confidence, planner alternatives, retrieval scores, context-budget burndown, and synthesis quality *simultaneously* to spot the failure mode. The current "panel on the right shows the selected step" pattern forces serial inspection of an inherently parallel system. We use a **three-zone always-visible layout** (lifecycle graph, focus detail, health/baselines) where every zone shows useful information by default and the focus zone updates on selection. Nothing critical lives behind a click.

**Principle 3: Show the negative space.** The most diagnostic data in any LLM pipeline is what *didn't* happen — bundles considered but pruned, signals retrieved but filtered out, classification options ranked second, context items truncated. The new trace renders **alternatives as ghosted siblings** at every decision point, with retrieval results split into "made-it" vs "dropped" tiers, and context assembly visualized as a budget waterfall where rejected items are explicit.

---

## 2. Information Architecture

**Tier A — Always visible (zero-click):**
1. Query header strip — query text, query_id, classification verdict + confidence, total wall-clock + cost, overall health badge.
2. Lifecycle graph (left zone) — full directed graph of every step, with executed path solid and alternatives ghosted.
3. Health rail (right zone) — per-stage health bars showing latency-vs-baseline, completeness-vs-baseline, quality-vs-baseline.

**Tier B — One-click (focus zone, default = Synthesis node):**
4. Step detail panel (center zone) — full input/decision/output triad for selected step.

**Tier C — Two-click (drill-down within step detail):**
5. Per-item drill-down — raw payload, retrieval scores, embedding distance, drop reason.

**Tier D — Modal-within-modal (rare, deep diagnostics):**
6. Raw payload viewer — full LLM prompt, full LLM response, full SQL + result rows.

---

## 3. Layout Blueprint

**Outer frame:** Modal overlay, 92vw × 92vh, centered, dark backdrop, `--brand-gold` 1px border at 0.4 opacity.

**Inner CSS Grid:**
```
grid-template-rows: 56px 1fr 88px;
```

- **Row 1 (56px) — Query Header Strip:** query text, classification pill, latency pill, cost pill, health badge, query_id + copy button.
- **Row 2 (1fr) — Three-column work area:**
  ```
  grid-template-columns: 380px 1fr 320px;
  ```
  - Left (380px): Lifecycle Graph
  - Center (fluid): Step Detail Panel
  - Right (320px): Health & Performance Rail
- **Row 3 (88px) — Timing & Cost Ribbon:**
  - Top 44px: Wall-clock Gantt with parallel-step swim-lanes, P50 overlay
  - Bottom 44px: Cost breakdown stacked bar by stage

---

## 4. Query Lifecycle Flow (Left Panel)

**Visual model:** Vertical directed graph, top-to-bottom. Parallel steps render as horizontal siblings in a shared swim-lane. Ghost-branches show non-selected alternatives.

**Node types:**

| Node | Shape | Border | Inline content |
|---|---|---|---|
| Classify | Rounded rect 64px | gold solid | `type · confidence · N alts` |
| Plan | Rounded rect 64px | gold solid | `N bundles · plan vX.X` |
| Fetch (success) | Rounded rect 56px | green solid | `bundle · N→M items · Xms` |
| Fetch (empty) | Rounded rect 56px | amber dashed | `bundle · 0 items · Xms` |
| Fetch (failed) | Rounded rect 56px | red solid | `bundle · TIMEOUT/AUTH · Xms` |
| Context Assembly | Hexagon 80px | gold solid | `Nk / Mk tokens · D dropped` |
| Synthesis | Rounded rect 88px | gold solid | `model · tokens · quality Q` |
| Ghost alternative | Rounded rect 40px | dim dashed | label only, 0.4 opacity |

**Decision representations:**
- **Classify node:** sub-rail below showing top-3 candidate types as pills (selected = solid gold, others = ghost with confidence).
- **Plan node:** sub-rail of selected bundles (green pills) + available-but-excluded bundles (ghost pills). Hover ghost = tooltip with LLM exclusion rationale.
- **Fetch fan-out:** single fan-out edge from Plan to all parallel fetch nodes; fan-in edges into Context Assembly, color-coded by token contribution (thin grey <500, medium gold 500–3000, thick gold >3000).

**Edge coloring by quality:**
- Context Assembly → Synthesis edge: green if assembly completeness ≥90%, amber 70–90%, red <70%.
- Failed Fetch → Context Assembly: dashed grey.

**Selection state:** Selected node has 2px gold ring + 6px glow; non-connected edges dim to 0.2 opacity.

---

## 5. Step Detail Panel (Center Zone)

**Common chrome (every step):** Sticky 48px sub-header with step type badge, step name, ordinal, latency + baseline delta (`+18% vs p50`), "View raw" link, "Copy step JSON" button.

Below: three sections — **Input** / **Decision** / **Output** — separated by 1px rules.

### 5.1 Classify
- Input: raw query text, pre-classification hints, model + temperature + tokens.
- Decision: ranked list of top-N candidate types with confidence bars + one-line LLM rationale. Selected has gold left-border. "Why this winner?" expander.
- Output: final type + confidence + downstream-impact summary.

### 5.2 Plan
- Input: classification verdict, available bundle catalog, model + temperature.
- Decision: two-column table (Included bundles with rationale | Excluded bundles with rationale). Planner execution graph diagram. Plan-version chip → prompt registry.
- Output: QueryPlan JSON (collapsed by default). Predicted vs actual token cost.

### 5.3 Fetch — `msr_sql`
- Input: tool args, generated SQL (syntax-highlighted), SQL parameters.
- Decision: what the SQL was filtering for (signal_class, house, planet, period).
- Output: results table with tabs **Kept (N)** | **Dropped (M)**. Dropped tab shows drop_reason column (`BELOW_THRESHOLD`, `DEDUP`, `POST_RERANK_PRUNE`).

### 5.4 Fetch — GCS (`pattern_register`, `remedial_codex_query`, `bundle_load`)
- Input: tool args, GCS URIs requested, layer prefix.
- Decision: URI resolution map (cache hit / fresh fetch / 404).
- Output: document list with tabs **Loaded (N)** | **Skipped (N)** | **Failed (N)**. Click row → inline preview.

### 5.5 Fetch — `vector_search`
- Input: embedder model, query text, top_K, distance metric.
- Decision: similarity score distribution histogram (Recharts). Threshold line dividing kept vs dropped.
- Output: ranked chunks table. Tabs: **Top-K Kept** | **Dropped (below threshold)** | **Adjacent (chunk neighbors)**. Shows rank-1 vs rank-K similarity gap.

### 5.6 Context Assembly — Hero visualization
- Input: per-bundle item counts + token estimates. Token budget + per-layer sub-budgets.
- Decision: **Context Waterfall**:
  - Horizontal stacked bar (System Preamble | L1 | L2.5), sub-segments per contributing item.
  - Below: vertical ordered list of every item considered:
    - Priority rank, item label, source bundle, token cost, relevance score.
    - Status badge: `INCLUDED` (green) / `TRUNCATED` (amber with "kept N of M tokens") / `DROPPED` (red with drop_reason).
    - Running cumulative token bar vs budget.
    - Click row → expands to show actual included text (or would-have-been text if dropped).
  - "Items dropped that scored higher than items kept" red callout (priority violation flag).
- Output: tabbed context preview (Preamble / L1 / L2.5). Token ledger.

### 5.7 Synthesis
- Input: model + temperature + max_tokens. Full assembled prompt (collapsible by section: Preamble | L1 | L2.5 | User Query | Format). Template version.
- Decision: tokens-per-second streaming chart. Stop reason (`stop`, `length`, `error`).
- Output:
  - Full synthesized answer with citations linkable to context items.
  - Quality scorecard inline:
    - Citation density (citations/claim)
    - B.11 whole-chart-read coverage (MSR / UCN / CDLM / CGM / RM)
    - B.3 derivation-ledger compliance
    - B.10 fabricated-computation check
    - Disclosure tier verdict
  - Each scorecard item: green/amber/red dot + failing examples inline.

---

## 6. Health & Performance Rail (Right Zone)

Five stacked cards:

**Card 1 — Overall Health Verdict (120px):**
Large circular badge: `HEALTHY` / `DEGRADED` / `FAILED`. 3-line computed summary ("Classification confident · Retrieval thin · Synthesis cited well").

**Card 2 — Per-Stage Health Strip (~200px):**
Five rows (Classify, Plan, Fetch, Assemble, Synthesize). Each row has:
- Latency bar vs p50 baseline (green ≤1.2×, amber 1.2–2.0×, red >2.0×).
- Completeness dot (green/amber/red).
- Quality dot.

**Card 3 — Baseline Comparison (~240px):**
Recharts grouped horizontal bars: this query (gold) vs p50 (grey) vs p95 (dim grey). Metrics: total latency, plan tokens, fetch items, context tokens, synthesis tokens, cost. Baselines conditioned on query_type.

**Card 4 — Anomaly Callouts (variable height):**
Auto-populated. Examples:
- `Plan latency 4.76s (3.2× p50 for holistic)`
- `vector_search dropped rank-1 chunk (similarity 0.91 below floor 0.92)`
- `Context assembly dropped 3 L2.5 items — budget pressure`
- `Synthesis cited 4 sources; baseline median is 8`

Each callout is clickable → selects the corresponding lifecycle node. Severity filter: All / Errors / Warnings.

**Card 5 — Cost & Token Ledger (160px):**
Table: call name (Classify / Plan / Synthesis / checkpoints), input tokens, output tokens, cost USD. Total row at bottom.

**Color semantics:**
- Green: within 1.2× p50, completeness ≥90%, quality scorecard 0 fails.
- Amber: 1.2–2.0× p50 OR completeness 70–90% OR 1 scorecard fail.
- Red: >2.0× p50 OR completeness <70% OR ≥2 scorecard fails OR any step errored.

---

## 7. Data Model — New Capture Required

### 7.1 `llm_call_log` additions

```sql
ALTER TABLE llm_call_log ADD COLUMN decision_alternatives JSONB;
-- Classify: [{type, confidence, rationale}]. Plan: [{bundle, was_selected, rationale}]
ALTER TABLE llm_call_log ADD COLUMN decision_reasoning TEXT;
ALTER TABLE llm_call_log ADD COLUMN prompt_template_id TEXT;
ALTER TABLE llm_call_log ADD COLUMN prompt_template_version TEXT;
ALTER TABLE llm_call_log ADD COLUMN parent_call_id UUID REFERENCES llm_call_log(id);
```

### 7.2 `tool_execution_log` additions

```sql
ALTER TABLE tool_execution_log ADD COLUMN raw_result_count INTEGER;
ALTER TABLE tool_execution_log ADD COLUMN kept_result_count INTEGER;
ALTER TABLE tool_execution_log ADD COLUMN dropped_items JSONB;
-- [{item_id, score, drop_reason}] capped at 200
ALTER TABLE tool_execution_log ADD COLUMN kept_items JSONB;
-- [{item_id, score, contribution_tokens}] capped at 200
ALTER TABLE tool_execution_log ADD COLUMN tool_input_payload JSONB;
ALTER TABLE tool_execution_log ADD COLUMN tool_output_summary JSONB;
ALTER TABLE tool_execution_log ADD COLUMN error_class TEXT DEFAULT 'OK';
-- ENUM: 'OK' | 'TIMEOUT' | 'AUTH' | 'MALFORMED_RESPONSE' | 'EMPTY'
```

### 7.3 New table — `context_assembly_log`

```sql
CREATE TABLE context_assembly_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL,
  assembly_step_id UUID NOT NULL,
  item_rank INTEGER NOT NULL,
  source_bundle TEXT NOT NULL,
  source_item_id TEXT NOT NULL,
  layer TEXT NOT NULL,          -- 'preamble' | 'L1' | 'L2_5'
  token_cost INTEGER NOT NULL,
  relevance_score REAL,
  status TEXT NOT NULL,         -- 'INCLUDED' | 'TRUNCATED' | 'DROPPED'
  drop_reason TEXT,             -- 'BUDGET_EXCEEDED' | 'DEDUP' | 'RELEVANCE_FLOOR' | NULL
  truncated_to_tokens INTEGER,
  cumulative_tokens_at_decision INTEGER,
  budget_at_decision INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_context_assembly_log_query ON context_assembly_log(query_id, item_rank);
```

### 7.4 New materialized view — `query_baseline_stats`

```sql
CREATE MATERIALIZED VIEW query_baseline_stats AS
SELECT
  query_type,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_latency_ms)  AS p50_total_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms)  AS p95_total_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY plan_latency_ms)   AS p50_plan_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY plan_latency_ms)   AS p95_plan_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fetch_latency_ms)  AS p50_fetch_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY fetch_latency_ms)  AS p95_fetch_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY synth_latency_ms)  AS p50_synth_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY synth_latency_ms)  AS p95_synth_latency_ms,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY total_cost_usd)    AS p50_total_cost_usd,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_cost_usd)    AS p95_total_cost_usd,
  COUNT(*) AS sample_size
FROM query_summary
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY query_type;
```

Refresh nightly via existing Observatory reconciliation cron.

### 7.5 New table — `synthesis_quality_scorecard`

```sql
CREATE TABLE synthesis_quality_scorecard (
  query_id UUID PRIMARY KEY,
  citation_density REAL NOT NULL,
  whole_chart_coverage JSONB NOT NULL,         -- {MSR: bool, UCN: bool, CDLM: bool, CGM: bool, RM: bool}
  derivation_ledger_compliance REAL NOT NULL,  -- 0.0–1.0
  fabricated_computation_flags JSONB,          -- [{claim, reason}]
  disclosure_tier_verdict TEXT NOT NULL,
  composite_score REAL NOT NULL,               -- 0.0–1.0
  failures JSONB,                              -- [{check, detail}]
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 7.6 New table — `plan_alternatives_log`

```sql
CREATE TABLE plan_alternatives_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query_id UUID NOT NULL,
  bundle_name TEXT NOT NULL,
  was_selected BOOLEAN NOT NULL,
  rationale TEXT,
  expected_recall_score REAL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_plan_alternatives_log_query ON plan_alternatives_log(query_id);
```

### 7.7 Trace API endpoint

```
GET /api/admin/trace/:query_id
Authorization: super_admin role required (403 otherwise)
Response: {
  query: { id, text, type, confidence, total_ms, total_cost_usd, health },
  classify: { input, alternatives[], decision_reasoning, latency_ms, tokens },
  plan: { included_bundles[], excluded_bundles[], plan_json },
  fetches: [{ bundle, raw_count, kept_count, dropped_items[], kept_items[], error_class }],
  context_assembly: { items[], token_ledger },
  synthesis: { prompt_sections, response, scorecard },
  baselines: { p50_*, p95_*, sample_size },
  anomalies: [{ stage, severity, message, step_id }],
  partial: boolean  -- true if pre-instrumentation query (missing some sections)
}
```

Target p95 latency: ≤ 800ms.

---

## 8. Interaction Design

**Click behaviors:**
- Click lifecycle node → center panel updates, Gantt segment highlights, off-path edges dim.
- Click anomaly callout → selects corresponding lifecycle node.
- Click any item row in fetch/assembly detail → inline accordion expand (max 320px height).
- Click "View raw" → Tier D nested modal (Esc dismisses, returns to trace).

**Hover behaviors:**
- Hover lifecycle node → 1px gold ring + tooltip (one-line: latency, item count, status).
- Hover ghost pill → tooltip with LLM rationale.
- Hover baseline bar → tooltip with absolute values (this: 4.76s, p50: 1.48s, p95: 6.10s, n=312).
- Hover Gantt segment → highlights corresponding lifecycle node.

**Keyboard shortcuts:**
- `Esc` — close modal
- `j` / `k` — next / previous step
- `1`–`9` — jump to step N
- `r` — re-run query (confirmation dialog)
- `c` — copy current step JSON
- `?` — toggle shortcut help overlay
- `/` — focus graph search filter

**Empty / partial states:**
- Pre-instrumentation queries: "Context assembly trace not captured (query predates 2026-05-XX instrumentation)".
- Baselines with n<30: "Baselines unreliable (n=X); comparisons are suggestive only".

---

## 9. Implementation Plan

### TRACE-T1 — Data Capture & API
**Trigger:** `"Read CLAUDECODE_BRIEF_TRACE_T1.md and execute it."`
- DB migration with 3 new tables + 1 materialized view + 5 column additions
- Logging hooks in classify, plan, retrieval, context assembler, synthesis
- `GET /api/admin/trace/:query_id` endpoint + assembler
- ≥ 25 unit tests

### TRACE-T2 — Lifecycle Graph + Step Detail
**Trigger:** `"Read CLAUDECODE_BRIEF_TRACE_T2.md and execute it."`
- `TraceModal`, `QueryHeaderStrip`, `LifecycleGraph`, `StepDetail` (7 variants), `TimingRibbon`
- Full interaction model (click/hover/keyboard)
- ≥ 30 RTL tests

### TRACE-T3 — Health Rail + Anomaly Detection + Polish
**Trigger:** `"Read CLAUDECODE_BRIEF_TRACE_T3.md and execute it."`
- `HealthRail`, `AnomalyDetector`, `BaselineResolver`
- Accessibility (Lighthouse a11y ≥ 95), performance hardening (virtualized tables)
- Architecture doc in `00_ARCHITECTURE/`

---

*Plan authored 2026-05-05. Basis: Opus 4.7 brainstorm session + existing pipeline analysis.*
*Sessions T1/T2/T3 briefs live at project root: `CLAUDECODE_BRIEF_TRACE_T1.md`, `_T2.md`, `_T3.md`.*
