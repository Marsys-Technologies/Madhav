---
artifact: MCP_PERF_SYSTEM_BRIEF_2026-05-22.md
status: DRAFT
version: 3.1
authored_by: Claude (Cowork session, Opus 4.7) — regeneration of Sonnet 4.7's v3.0 draft per native's review-package mandate
authored_on: 2026-05-22
supersedes_in_place:
  - MCP_PERF_SYSTEM_BRIEF_2026-05-22.md (Sonnet 4.7, v3.0 — same filename; substantive regeneration)
parent_brief: 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md (v3.1)
companion_handoff: 00_ARCHITECTURE/MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md
audience: native (Abhisek Mohanty); secondary acharya readership at v3.1 close
disposition: subsystem brief that operationalizes the §3.5 Tier 5 perf tools, the §7.6 operator-side audit subsystem, the prediction-calibration loop, and the operator dashboard at /admin/mcp/health
guiding_principle: "The performance system is not operator telemetry. It is first-class agent context that shapes orchestration quality in real time, AND it is the seat of governance verification — the closure that v3.0 tried to put inside the host (validate_response) lives here instead."
version_bump_rationale: |
  v3.0 → v3.1, paired with the architecture doc's version bump. v3.1 promotes the
  perf system from "tool/data health visibility" to "tool/data health visibility +
  operator-side audit subsystem + prediction-calibration loop" — three substrates
  rolled together. Sonnet's v3.0 perf brief envisioned the first; v3.1 absorbs the
  validate_response responsibility (now lives here as nightly audit) and adds
  calibration as a first-class metric. The §12 depth-over-tokens directive is baked
  throughout rather than appended. New sections on the audit subsystem (§5),
  calibration loop (§9), and alerting (§7.5). Same materialized-view spine but with
  added audit and calibration views.
---

# MCP Performance, Audit, and Calibration System — Brief

The performance system under v3.1 is three subsystems sharing one data spine. The first subsystem is **tool/data-source health visibility** — the agent-facing perf tools (`tool_health`, `data_coverage`) and the operator dashboard. The second is **the audit subsystem** — the nightly job that verifies governance compliance (B.11 floor, citation set-membership, numerical claim grounding) against recorded traces; this is where the responsibility v3.0 put inside the host (`validate_response`) actually lives in v3.1. The third is **the prediction-calibration loop** — the long-horizon measurement that turns logged predictions plus recorded outcomes into per-confidence-band hit rates, the only metric that empirically validates the calibrated-epistemics rubric dimension.

All three subsystems share the same materialized-view substrate over `tool_execution_log` + a few new tables. All three surface through the same operator dashboard at `/admin/mcp/health`. Two of three (health + audit-findings-on-trace) surface to the host via MCP tools and the `marsys://capabilities` resource. The unifying property: the operator's view of the system, the host's view of the system, and the governance verification of the system are the *same view from different angles*. Edits by the operator propagate to the agent in the next session. Audit findings inform house-rules iteration. Calibration scores feed back into the host's confidence-band guidance.

This is what makes v3.1 a research instrument, not an oracle: every claim is auditable, every prediction is testable against outcomes, and the system gets better at calibration as data accumulates.

---

## §0 — TL;DR

A subsystem with **three audiences (operator + host + governance) sharing one backing data layer.** **Seven metric dimensions captured at five scopes** (per-call → per-tool → per-data-source → per-session → per-prediction-horizon). Backed by a small set of materialized views over the already-existing `tool_execution_log` plus three new tables (`mcp_audit_findings`, `data_source_expected`, `tool_caveats`) and one new metric class (`prediction_calibration_score` per `(confidence_band, domain, horizon_bucket)` cell). Surfaced as: (a) two MCP tools (`tool_health` + `data_coverage`) the host calls on demand; (b) the `marsys://capabilities` resource auto-loaded at session attach; (c) the operator HTML dashboard at `/admin/mcp/health` with five tabs (Tool Health, Data Coverage, Audit Findings, Predictions / Calibration, Sessions); (d) Slack/email alerts on threshold breaches. The nightly audit subsystem is the structural replacement for v3.0's self-audit tool — independent of the host, mandatory rather than opt-in, retrospective and continuous. The prediction-calibration loop closes the long-horizon measurement that the depth-over-tokens directive intensifies: more depth means more confident claims means more skin in the calibration game. The system is *additive* — it does not change any retrieval tool's behavior; it only measures, audits, and reports honestly.

**The §12 depth-over-tokens directive applied to this brief:** latency is informational, not a target; `avg_bundle_size_tokens` is a tracked metric and an *honest reporting* signal, not a budget; `depth_score` (a heuristic proxy for "did this tool deliver useful signal?") replaces "token efficiency" thinking; the caveat taxonomy explicitly distinguishes *data-depth gaps* from *tool-reliability gaps* because they have different mitigations.

---

## §1 — Why measurement matters more in v3.1 than in v1

In v1, the planner picked tools deterministically from a static `RETRIEVAL_TOOLS` registry, and the synthesis LLM glossed over zero-row results as if they were fine. Tool quality was an opaque concern; no agent ever needed visibility, and no operator-side verification ran continuously. Failure modes were silent.

v3.1 inverts the opacity. The host orchestrates. The host needs to know:

- Which tools are healthy enough to call this turn? If `query_chart_facts(shadbala)` has returned zero rows for six weeks because of a backfill gap, the host should route around it before the user opens their mouth — not after wasting six seconds on an empty result.
- Which data sources are sparse for this question class? If the user asks about Tajaka varshphal and the Tajaka tables are 20% populated, the host should disclose the limitation honestly rather than confabulate.
- Did its own last turn cite anything fabricated, skip the B.11 floor, or make a numerical claim that doesn't appear in retrieved data? In v3.0 the host was expected to ask itself this via `validate_response`; in v3.1 a nightly audit asks, and surfaces findings the operator can act on. The host can also call `get_trace(prior_trace_id)` mid-session to inspect findings attached to its own prior calls.
- Over time, how well-calibrated were its predictions? If the host's "0.7 confidence" claims have a 0.4 hit rate, the rubric's calibrated-epistemics dimension is failing. The system needs to measure this and tell both the operator and the next host session (via `house-rules` updates the operator authors based on observed calibration).

All four require visibility. The perf system is the substrate. Without it, v3.1 is a blindfolded orchestrator. With it, v3.1 is the research instrument the rubric demands.

---

## §2 — Three audiences, one data layer

```
                ┌───────────────────────────────────────────────────────┐
                │  Source data                                          │
                │  - tool_execution_log (exists; extended in §4.1)       │
                │  - query_trace_steps (exists)                          │
                │  - mcp_predictions (new in v1 MCP; extended)           │
                │  - mcp_audit_findings (NEW in v3.1)                    │
                │  - mcp_prediction_outcomes (NEW in v3.1)               │
                │  - data_source_expected (NEW; operator-authored)       │
                │  - tool_caveats (NEW; operator-authored)               │
                └───────────────────────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────────┐
              ▼                        ▼                            ▼
        ┌──────────────┐      ┌──────────────────┐         ┌────────────────────┐
        │ Materialized  │      │ Materialized      │         │ Materialized        │
        │ rollups:      │      │ rollups:          │         │ rollups:            │
        │ per-tool      │      │ per-data-source   │         │ per-confidence-band │
        │ metrics       │      │ coverage          │         │ calibration         │
        │ (mv_tool_…)   │      │ (mv_data_source_…)│         │ (mv_calibration_…)  │
        └──────────────┘      └──────────────────┘         └────────────────────┘
              │                        │                            │
              └────────────────────────┴────────────────────────────┘
                                       ▼
              ┌──────────────────────────────────────────────────────┐
              │ Three audiences, four surfaces:                       │
              │                                                       │
              │ 1. tool_health() / data_coverage() MCP tools         │ ← Host (agent)
              │                                                       │
              │ 2. marsys://capabilities resource (session attach)   │ ← Host (agent)
              │                                                       │
              │ 3. /admin/mcp/health dashboard (5 tabs)              │ ← Operator
              │    - Tool Health                                      │
              │    - Data Coverage                                    │
              │    - Audit Findings   ← governance verification        │
              │    - Predictions/Calibration ← long-horizon measurement│
              │    - Sessions                                         │
              │                                                       │
              │ 4. Slack/email alerts on threshold breaches          │ ← Operator
              │                                                       │
              │ (5.) get_trace(trace_id) extended to include findings│ ← Host (agent)
              │      — same data, different access pattern            │
              └──────────────────────────────────────────────────────┘
```

Same numbers, four access patterns. No double-counting, no parallel telemetry systems. The fifth access path — `get_trace` returning audit findings inline — is the closure that lets the host inspect *what the audit said about its own prior calls* without leaving the conversation surface.

---

## §3 — Metrics taxonomy

Five scopes × seven dimensions. v3.0 had four × six. v3.1 adds:
- A new dimension: **calibration** (per-confidence-band hit rate; only meaningful at the per-prediction-horizon scope).
- A new scope: **per-prediction-horizon** (rolls up by `(confidence_band, domain, horizon_bucket)`).
- A new per-tool metric: **`depth_score`** (replacing v1's implicit "token efficiency").
- A new per-tool metric: **`avg_bundle_size_tokens`** (honest depth reporting; not a target for minimization).

The cells that don't apply are blank.

| Scope ↓ \ Dim → | Latency | Volume | Reliability | Data quality | Depth (NEW) | Calibration (NEW) | Freshness |
|---|---|---|---|---|---|---|---|
| **Per-call** | `latency_ms` (informational) | 1 | `status` (ok/zero_rows/error) | `rows_returned`, `kept_result_count` | `bundle_size_tokens` (for bundles) | n/a | n/a |
| **Per-tool** | `p50_latency_ms`, `p95_latency_ms`, `p99_latency_ms` (informational; not target) | `calls/window`, `calls/key`, `calls_per_audience_tier` | `error_rate`, `zero_rows_rate`, `degraded_rate` | `avg_rows_returned`, `grounding_rate`, `dropped_items_rate` | `avg_bundle_size_tokens`, `depth_score` | n/a | n/a |
| **Per-data-source** | n/a | n/a | n/a (DB health is separate) | `row_count`, `coverage_by_subkey`, `staleness_flag`, `citation_grounded_pct` (for MSR) | `expected_vs_actual_completeness_pct` | n/a | `last_bootstrap_ts`, `last_row_written_ts`, `next_backfill_planned` |
| **Per-session** | `total_session_latency_ms` | `tools_called`, `unique_tools`, `bundles_called`, `primitives_called`, `predictions_logged` | `failed_calls`, `audit_findings_count` | `bundles_returned_empty`, `total_signals_returned`, `unique_layer_tags` | `total_bundle_tokens_returned` (estimated host token absorption) | n/a (lives at prediction-horizon scope) | n/a |
| **Per-prediction-horizon (NEW)** | n/a | `predictions_in_band`, `predictions_realized`, `predictions_disconfirmed`, `predictions_pending` | n/a | n/a | n/a | `calibration_score = realized/(realized+disconfirmed)` per `(confidence_band, domain, horizon_bucket)`, with confidence interval (Wilson) | `horizon_completion_rate` (fraction of band's predictions past their horizon) |

Seven dimensions total; ~26 distinct metric names; surface stays tight.

### §3.1 — Why each dimension matters under the rubric

**Latency — informational, not target.** v1 implicitly ranked tools partially on speed; v3.1 says: a tool that takes 8s to deliver 200 high-grounding-rate rows is better than one that takes 200ms to deliver 5 truncated rows. The dashboard displays latency without coloring it red unless it's truly pathological (p95 > 30s on a frequently-called tool). The host doesn't penalize slow tools; the operator only worries about latency when it threatens UX (long bundles still complete progressively via SSE per arch §8).

**Volume — sanity check + tier-aware billing input.** Calls per audience tier surfaces tier-misuse (e.g., a client-tier key making 10,000 calls in an hour) and informs rate-limit tuning over time.

**Reliability — the operator backlog signal.** `zero_rows_rate` and `error_rate` are the operator's primary backlog inputs. A tool with a 57% `zero_rows_rate` (the v1 `query_chart_facts(shadbala)` case) tells the operator "this tool is mostly returning empty; something's wrong with data or with how the host's calling it." Combined with `audit_findings_count`, reliability is the spine of operator triage.

**Data quality — does the tool produce *useful* output?** `grounding_rate` measures whether retrieved data was actually cited by the host. This is the metric that catches the v1 `vector_search` bug-class: tool returns 5 chunks, but they were embedded against `"surgical_primitive:vector_search"` so they're all generic and the host ignores all 5. Pure success/error metrics miss this; grounding rate surfaces it.

**Depth — the §12 directive's metric expression.** `avg_bundle_size_tokens` is honest reporting: am I delivering enough depth? `depth_score = grounding_rate × log(1 + avg_rows_returned)` is a heuristic that captures both "useful signals" and "enough of them." A tool with 100% grounding rate but 2 rows returned is delivering accurate but thin depth; a tool with 70% grounding rate but 50 rows returned is delivering more useful signal in absolute terms. The dashboard surfaces both factors, not a single ratio.

**Calibration — the rubric closure for forward-looking claims.** This is the metric that says: when I claimed "0.7 confidence", did the empirical hit rate actually approach 0.7? Without it, calibrated epistemics is theater. With it, the system grades its own epistemic discipline over time and the operator can author house-rules updates ("0.7-band predictions in the career domain are currently 0.4-realized — be more conservative on career-domain confidence claims this session") that propagate via `marsys://house-rules`. The calibration loop is detailed in §9.

**Freshness — backfill cadence + staleness.** Tells the operator when each asset was last bootstrapped, when its rows were last written, and what's planned next.

### §3.2 — The non-obvious metric: tool-grounding rate (still load-bearing)

Sonnet's brief singled out `tool_grounding_rate` as the non-obvious metric. v3.1 keeps it load-bearing but defines it more precisely: for each *response* the host produces with available transcript, the `cited_ids[]` set is regex-extracted from the response text; for each tool that contributed to that response's bundle, `grounding_rate(tool) = |cited_ids ∩ tool_signal_ids| / |tool_signal_ids|` (i.e., the fraction of THAT tool's retrieved IDs that the host actually cited). Aggregated per tool over a window.

A tool with high `grounding_rate` is delivering useful signal that the host can compose with. A tool with high `ok_rate` but low `grounding_rate` is succeeding by traditional metrics but failing to be *useful* — exactly the v1 `vector_search` failure mode.

Computation requires response transcripts. Cowork sessions transcribe; Claude Chat sessions don't transcribe to the platform. Limitation acknowledged; metric is computed on the subset of traces with transcripts available, with `grounding_rate_coverage_pct` reported alongside so the operator knows the sample size.

---

## §4 — Data structures

### §4.1 — Source table extensions

`tool_execution_log` already exists; every retrieval tool writes a row (see `platform/src/lib/retrieve/chart_facts_query.ts:283` for the pattern). v3.1 adds **five** columns (Sonnet had three; v3.1 adds two more for audit-side joins):

| Column | Type | Why add |
|---|---|---|
| `source` | text | `"web_consume" \| "mcp_primitive" \| "mcp_bundle" \| "mcp_sub_tool"` — promotes Sonnet's payload field to an indexed column. `mcp_sub_tool` is new: rows written by primitives called *from inside a bundle* are tagged differently so per-tool metrics don't double-count bundle-internal sub-tool calls vs direct primitive calls. |
| `mcp_key_id` | text NULL | Which API key called (per-principal volume + per-tier rollups). |
| `mcp_tool_name` | text NULL | MCP-facing tool name (e.g., `holistic_bundle` vs the underlying `msr_sql` it ran). For sub-tool rows, both `mcp_tool_name` (the bundle) and `tool_name` (the underlying retrieval) are populated. |
| `audience_tier` | text NULL | Stamped from the calling principal; enables per-tier rollups in `mv_tool_metrics_24h`. |
| `bundle_trace_id` | uuid NULL | For `mcp_sub_tool` rows, links back to the parent bundle's trace_id. Enables "which sub-tools ran for bundle X" queries. |

These five columns enable per-MCP-tool and per-bundle aggregation without affecting the web `/consume` path's existing writes. Migration is a single ALTER + backfill-with-NULLs.

### §4.2 — Materialized views

**View 1: `mv_tool_metrics_24h`** — per-tool rollup over the last 24 hours, refreshed every 5 minutes.

```sql
CREATE MATERIALIZED VIEW mv_tool_metrics_24h AS
SELECT
  mcp_tool_name,
  source,
  audience_tier,
  count(*)                                                   AS calls_24h,
  count(*) FILTER (WHERE status = 'ok')                      AS ok_calls,
  count(*) FILTER (WHERE status = 'zero_rows')               AS zero_rows_calls,
  count(*) FILTER (WHERE status = 'error')                   AS error_calls,
  count(*) FILTER (WHERE status = 'ok')::float / count(*)    AS ok_rate,
  count(*) FILTER (WHERE status = 'zero_rows')::float / count(*) AS zero_rows_rate,
  percentile_cont(0.50) WITHIN GROUP (ORDER BY latency_ms)   AS p50_latency_ms,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)   AS p95_latency_ms,
  percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms)   AS p99_latency_ms,
  avg(rows_returned)                                         AS avg_rows_returned,
  avg(bundle_size_tokens) FILTER (WHERE bundle_size_tokens IS NOT NULL) AS avg_bundle_size_tokens,
  max(timestamp)                                             AS last_call_at
FROM tool_execution_log
WHERE timestamp >= now() - interval '24 hours'
  AND mcp_tool_name IS NOT NULL
GROUP BY mcp_tool_name, source, audience_tier;

CREATE UNIQUE INDEX ON mv_tool_metrics_24h (mcp_tool_name, source, audience_tier);
```

**View 2: `mv_data_source_coverage`** — per-asset row counts + freshness, refreshed nightly. Schema same as Sonnet's; UNION ALL one block per asset (chart_facts, msr_signals, lel_events, panchang_daily, ephemeris_daily, rag_chunks, multi_school_*, classical_texts):

```sql
CREATE MATERIALIZED VIEW mv_data_source_coverage AS
SELECT
  'chart_facts'::text                         AS asset_id,
  category                                     AS subkey,
  count(*)                                     AS row_count,
  max(updated_at)                              AS last_row_written_ts,
  (SELECT max(completed_at) FROM build_manifests WHERE asset_id = 'chart_facts') AS last_bootstrap_ts,
  count(*) FILTER (WHERE is_stale = true)      AS stale_rows
FROM chart_facts
GROUP BY category

UNION ALL

SELECT 'msr_signals', null, count(*), max(updated_at),
       (SELECT max(completed_at) FROM build_manifests WHERE asset_id = 'msr_signals'),
       count(*) FILTER (WHERE is_stale = true)
FROM msr_signals

UNION ALL

SELECT 'lel_events', category, count(*), max(updated_at),
       (SELECT max(completed_at) FROM build_manifests WHERE asset_id = 'lel_events'),
       count(*) FILTER (WHERE is_stale = true)
FROM lel_events
GROUP BY category

-- ... one block per asset (panchang_daily, ephemeris_daily, rag_chunks, multi_school_*, classical_texts) ...
;

CREATE UNIQUE INDEX ON mv_data_source_coverage (asset_id, subkey);
```

**View 3: `data_source_expected`** — operator-authored expected-coverage targets (NOT a materialized view; a regular table the operator edits via dashboard):

```sql
CREATE TABLE data_source_expected (
  asset_id text NOT NULL,
  subkey text NULL,
  expected_row_count int NOT NULL,
  expected_last_bootstrap_after timestamptz NULL,
  rationale text NULL,
  next_backfill_planned text NULL,
  notes text NULL,
  caveat_class text NULL CHECK (caveat_class IN ('data_depth_gap', 'tool_reliability_gap', NULL)),
  updated_at timestamptz DEFAULT now(),
  updated_by text DEFAULT current_user,
  PRIMARY KEY (asset_id, subkey)
);

-- Seed example rows (operator authors via dashboard):
INSERT INTO data_source_expected VALUES
  ('chart_facts', 'shadbala', 63, NULL,
   '9 planets × Sthana/Dig/Kala/Cheshta/Naisargika/Drik/Total = 63 rows',
   'v3.3-S1 ingestion from Jagannatha Hora source', NULL, 'data_depth_gap', now(), 'native'),
  ('chart_facts', 'ashtakavarga_sav', 12, NULL,
   '12 houses × SAV = 12 rows',
   'v3.3-S1 ingestion', NULL, 'data_depth_gap', now(), 'native'),
  ('classical_texts', 'BPHS', 1500, NULL,
   '~50 chapters × ~30 verses each = ~1500 verse-rows',
   'v3.2-S1 BPHS indexing', NULL, 'data_depth_gap', now(), 'native')
;
```

The `caveat_class` column splits "data depth gap" from "tool reliability gap" per the §12 directive (Sonnet's brief observed these need different mitigations). The dashboard's caveat-editing UI exposes the class as a dropdown.

**View 4: `mv_session_summary`** — per-MCP-session rollup, refreshed every 10 minutes:

```sql
CREATE MATERIALIZED VIEW mv_session_summary AS
SELECT
  mcp_key_id,
  audience_tier,
  date_trunc('hour', timestamp)                        AS session_hour,
  count(DISTINCT mcp_tool_name) FILTER (WHERE source = 'mcp_primitive') AS unique_primitives,
  count(*) FILTER (WHERE source = 'mcp_primitive')      AS primitive_calls,
  count(*) FILTER (WHERE source = 'mcp_bundle')         AS bundle_calls,
  count(*) FILTER (WHERE source = 'mcp_sub_tool')       AS sub_tool_calls,
  sum(rows_returned)                                    AS total_rows_returned,
  count(*) FILTER (WHERE status = 'zero_rows')          AS zero_rows_calls,
  sum(bundle_size_tokens) FILTER (WHERE source = 'mcp_bundle') AS total_bundle_tokens
FROM tool_execution_log
WHERE source LIKE 'mcp%'
GROUP BY mcp_key_id, audience_tier, date_trunc('hour', timestamp);

CREATE UNIQUE INDEX ON mv_session_summary (mcp_key_id, session_hour);
```

**View 5: `mv_tool_grounding_24h`** — per-tool grounding rate over 24h, refreshed every 15 minutes. Depends on `mcp_audit_findings` (§5):

```sql
CREATE MATERIALIZED VIEW mv_tool_grounding_24h AS
WITH cited_per_trace AS (
  SELECT trace_id, unnest(cited_signal_ids) AS cited_id
  FROM mcp_audit_findings
  WHERE finding_class = 'cite_grounded'
    AND attached_at >= now() - interval '24 hours'
)
SELECT
  tel.mcp_tool_name,
  count(DISTINCT tel.trace_id)                                 AS traces,
  count(DISTINCT cpt.cited_id)                                 AS cited_signals,
  count(DISTINCT tel.id) FILTER (
    WHERE tel.signal_ids_available && (SELECT array_agg(cited_id) FROM cited_per_trace cpt2 WHERE cpt2.trace_id = tel.trace_id)
  )::float / NULLIF(count(DISTINCT tel.id), 0)                 AS grounding_rate
FROM tool_execution_log tel
LEFT JOIN cited_per_trace cpt ON cpt.trace_id = tel.trace_id
WHERE tel.timestamp >= now() - interval '24 hours'
  AND tel.mcp_tool_name IS NOT NULL
GROUP BY tel.mcp_tool_name;
```

**View 6: `mv_calibration_score`** — per-confidence-band hit rate, refreshed nightly. Depends on `mcp_predictions` + `mcp_prediction_outcomes` (§4.4):

```sql
CREATE MATERIALIZED VIEW mv_calibration_score AS
SELECT
  p.confidence_band,
  p.domain,
  CASE
    WHEN p.horizon_days <= 30 THEN '<=30d'
    WHEN p.horizon_days <= 180 THEN '31-180d'
    WHEN p.horizon_days <= 730 THEN '181-730d'
    ELSE '>730d'
  END                                                     AS horizon_bucket,
  count(*)                                                AS total_predictions,
  count(o.outcome) FILTER (WHERE o.outcome = 'realized')  AS realized,
  count(o.outcome) FILTER (WHERE o.outcome = 'disconfirmed') AS disconfirmed,
  count(o.outcome) FILTER (WHERE o.outcome = 'partial')   AS partial,
  count(*) - count(o.outcome)                             AS pending,
  count(o.outcome) FILTER (WHERE o.outcome = 'realized')::float /
    NULLIF(count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')), 0)
                                                          AS realized_rate,
  /* Wilson confidence interval lower bound at 95% */
  CASE WHEN count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')) > 0 THEN
    wilson_lower_bound(
      count(o.outcome) FILTER (WHERE o.outcome = 'realized'),
      count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')),
      0.95
    )
  ELSE NULL END                                           AS realized_rate_ci_low,
  CASE WHEN count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')) > 0 THEN
    wilson_upper_bound(
      count(o.outcome) FILTER (WHERE o.outcome = 'realized'),
      count(o.outcome) FILTER (WHERE o.outcome IN ('realized', 'disconfirmed')),
      0.95
    )
  ELSE NULL END                                           AS realized_rate_ci_high
FROM mcp_predictions p
LEFT JOIN mcp_prediction_outcomes o ON o.prediction_id = p.id
GROUP BY p.confidence_band, p.domain, horizon_bucket;

CREATE UNIQUE INDEX ON mv_calibration_score (confidence_band, domain, horizon_bucket);
```

The Wilson interval gives honest confidence bands on small samples — important because per-band-per-domain-per-horizon cells will have small N for a long time (especially client-tier predictions until many clients exist).

### §4.3 — `mcp_audit_findings` (NEW; the audit subsystem's output)

This is the table the operator-side nightly audit job writes to. It is the structural replacement for v3.0's `mcp_response_audits`.

```sql
CREATE TABLE mcp_audit_findings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  trace_id uuid NOT NULL,
  mcp_key_id text,
  audience_tier text,
  finding_class text NOT NULL CHECK (finding_class IN (
    'b11_skipped',
    'cite_grounded',
    'cite_fabricated',
    'numerical_grounded',
    'numerical_unverified',
    'ppl_missing',
    'ppl_emitted',
    'tier_template_compliant',
    'tier_template_violation',
    'layer_mixing'
  )),
  severity text NOT NULL CHECK (severity IN ('info', 'warn', 'class_1', 'class_2')),
  description text NOT NULL,
  evidence jsonb NOT NULL,   -- {cited_ids: [...], available_ids: [...], fabricated_ids: [...], ...}
  available_signal_ids text[],
  cited_signal_ids text[],
  fabricated_cite_ids text[],
  numerical_claims jsonb,    -- [{claim: "59.18 virupa", grounded: true, source: "SIG.MSR.053"}, ...]
  attached_at timestamptz NOT NULL DEFAULT now(),
  audit_job_run_id uuid NOT NULL,
  resolved_at timestamptz NULL,
  resolved_by text NULL,
  resolution_note text NULL,
  CONSTRAINT severity_class_alignment CHECK (
    (finding_class IN ('cite_grounded', 'numerical_grounded', 'ppl_emitted', 'tier_template_compliant') AND severity = 'info') OR
    (finding_class IN ('b11_skipped', 'cite_fabricated') AND severity IN ('warn', 'class_1', 'class_2')) OR
    (finding_class IN ('numerical_unverified', 'ppl_missing', 'tier_template_violation', 'layer_mixing') AND severity IN ('warn', 'class_2'))
  )
);

CREATE INDEX mcp_audit_findings_by_trace ON mcp_audit_findings (trace_id);
CREATE INDEX mcp_audit_findings_by_class_severity ON mcp_audit_findings (finding_class, severity, attached_at DESC);
CREATE INDEX mcp_audit_findings_by_unresolved ON mcp_audit_findings (resolved_at) WHERE resolved_at IS NULL;
```

Findings carry both a `class` (what was checked) and a `severity` (info/warn/class_1/class_2). `info`-class findings are the positive results (cite was grounded, PPL was emitted, template was compliant) — captured for completeness and to enable rate calculations. `warn` is "this needs attention but isn't a violation" (numerical unverified often falls here — the claim might be valid but unverifiable from retrieved data). `class_1` and `class_2` are the violation severities matching `DISAGREEMENT_REGISTER` class taxonomy.

The `resolved_at` / `resolved_by` columns let the operator triage findings on the dashboard — mark "false positive," "fixed in next run," "house-rules updated to prevent," etc. Unresolved findings drive the dashboard's red-flag count.

### §4.4 — `mcp_predictions` + `mcp_prediction_outcomes` (extended in v3.1)

`mcp_predictions` already exists (v1 migration 071). v3.1 adds two columns and a sibling table.

```sql
ALTER TABLE mcp_predictions ADD COLUMN confidence_band text;
   -- e.g., '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0';
   -- or 'low', 'medium', 'high' for plain-language tiers;
   -- bucketing rule: numeric → narrowest 0.1 band containing it.
ALTER TABLE mcp_predictions ADD COLUMN source_signals text[];
   -- the subset of provenance.signal_ids_available[] that the host cited as grounding for the prediction;
   -- enables tracing each prediction back to the retrieval that generated it.

CREATE TABLE mcp_prediction_outcomes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  prediction_id uuid NOT NULL REFERENCES mcp_predictions(id),
  outcome text NOT NULL CHECK (outcome IN ('realized', 'disconfirmed', 'partial', 'horizon_not_yet_reached')),
  observed_at timestamptz NOT NULL,
  notes text NULL,
  recorded_by_principal text,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT unique_outcome_per_prediction UNIQUE (prediction_id)
);
```

The `record_outcome` MCP write tool writes here. `mv_calibration_score` joins these two tables to produce per-band hit rates.

### §4.5 — `tool_caveats` (NEW; operator-authored prose)

```sql
CREATE TABLE tool_caveats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mcp_tool_name text NOT NULL,
  caveat_text text NOT NULL,
  caveat_class text NOT NULL CHECK (caveat_class IN ('data_depth_gap', 'tool_reliability_gap', 'known_bug', 'usage_hint')),
  severity text NOT NULL CHECK (severity IN ('info', 'warn', 'critical')),
  active_until timestamptz NULL,   -- NULL = indefinite; non-null = caveat auto-expires
  authored_by text NOT NULL,
  authored_at timestamptz NOT NULL DEFAULT now()
);

-- Seed examples:
INSERT INTO tool_caveats (mcp_tool_name, caveat_text, caveat_class, severity, authored_by) VALUES
  ('query_chart_facts',
   'Categories shadbala, ashtakavarga_*, kp_*, upagraha currently return 0 rows. Backfill scheduled v3.3-S1. Prefer query_signals for strength claims until then.',
   'data_depth_gap', 'warn', 'native'),
  ('vector_search',
   'Returns relevant chunks for the user query text since v3.1 fix (was returning generic chunks in v1). Recommended top_k=25 for adequate depth coverage.',
   'usage_hint', 'info', 'native'),
  ('cross_school_lookup',
   'Tajaka coverage currently ~20%; Tajaka-school stances may be sparse. Backfill scheduled v3.2-S5. KP at ~60%.',
   'data_depth_gap', 'warn', 'native')
;

CREATE INDEX tool_caveats_active ON tool_caveats (mcp_tool_name, severity) WHERE active_until IS NULL OR active_until > now();
```

Caveats surface in three places: in `tool_health()` MCP-tool output, in the `marsys://capabilities` resource (per-tool description), and on the operator dashboard (inline-editable Caveats column).

---

## §5 — The audit subsystem (the moved validate_response responsibility)

This is the structural piece v3.1 adds vs Sonnet's v3.0 brief: the operator-side nightly audit job that performs governance verification independent of the host. v3.0 put this responsibility inside the host (`validate_response` self-audit tool); v3.1 moves it out.

### §5.1 — What the audit job does

The audit job runs nightly at 03:00 UTC (one hour after `mv_data_source_coverage` refresh). It processes all traces from the prior 24 hours. For each trace:

```
trace_record = query_trace_steps(trace_id) joined with tool_execution_log + mcp_predictions + response_transcript (if available)

for trace in traces_last_24h:
  findings = []

  # Check 1: B.11 floor — for non-factual responses, was ≥1 L2.5 retrieval logged?
  if is_non_factual_response(trace.response_text):
    l2_5_retrievals = [t for t in trace.tool_calls if t.data_sources_touched intersects L2_5_ASSETS]
    if not l2_5_retrievals:
      findings.append(Finding(class='b11_skipped', severity='class_2', ...))

  # Check 2: Citation set-membership
  if trace.response_text:
    cited_ids = extract_citations(trace.response_text)   # regex: [\^N], SIG.MSR.NNN, LEL.E.NNN, FORENSIC.§N.N
    available_ids = union(t.signal_ids_available for t in trace.tool_calls)
    fabricated = cited_ids - available_ids
    grounded = cited_ids - fabricated
    if fabricated:
      findings.append(Finding(class='cite_fabricated', severity='class_1', evidence={fabricated: list(fabricated)}, ...))
    if grounded:
      findings.append(Finding(class='cite_grounded', severity='info', evidence={grounded: list(grounded)}, ...))

  # Check 3: Numerical claim grounding
  if trace.response_text:
    numerical_claims = extract_numerical_claims(trace.response_text)   # regex: \d+\.?\d*\s*(virupa|degrees|rupas|points)
    retrieved_numerical_strings = collect_numerical_strings(trace.tool_calls)
    for claim in numerical_claims:
      if claim.value in retrieved_numerical_strings:
        findings.append(Finding(class='numerical_grounded', severity='info', ...))
      else:
        findings.append(Finding(class='numerical_unverified', severity='warn', evidence={claim: ...}, ...))

  # Check 4: PPL emission
  if has_forward_looking_language(trace.response_text):
    predictions_in_session = mcp_predictions.filter(session_id=trace.session_id, created_at > trace.opened_at)
    if not predictions_in_session:
      findings.append(Finding(class='ppl_missing', severity='warn', ...))
    else:
      findings.append(Finding(class='ppl_emitted', severity='info', ...))

  # Check 5: Tier-template compliance (heuristic, client-tier only)
  if trace.audience_tier == 'client':
    if not glosses_first_sanskrit_use(trace.response_text):
      findings.append(Finding(class='tier_template_violation', severity='warn', evidence={...}, ...))
    if has_forward_looking_language(trace.response_text) and not contains_explicit_falsifier(trace.response_text):
      findings.append(Finding(class='tier_template_violation', severity='warn', evidence={missing: 'falsifier'}, ...))

  # Check 6: Layer mixing — L1 claims should cite L1 sources; L2.5 claims should cite L2.5 sources
  if trace.response_text and trace.cited_signals_layer_tags:
    cross_layer = check_layer_attribution(trace.response_text, trace.cited_signals_layer_tags)
    if cross_layer:
      findings.append(Finding(class='layer_mixing', severity='warn', evidence=cross_layer, ...))

  bulk_insert(mcp_audit_findings, findings, trace_id=trace.id, audit_job_run_id=current_run_id)
```

### §5.2 — Heuristics, not LLM-calls

The audit job uses regex + rule heuristics, not LLM inference. Two reasons: (a) cost — running an LLM over thousands of traces nightly is expensive; (b) the audit must be independent of any LLM's interpretation (the whole point is to verify host behavior without trusting another model's read). Heuristics are imperfect — `is_non_factual_response` is response-length-plus-question-shape; `has_forward_looking_language` is keyword-matching for "will", "by 2027", "next year", "during this dasha"; `glosses_first_sanskrit_use` is matching Sanskrit unicode ranges against subsequent parenthetical glosses — but they're consistent, reproducible, and fast. Misclassifications are flagged for operator review and improve the heuristics over time.

LLMs could be added as a *second pass* for borderline findings (e.g., "the heuristic flagged this as numerical_unverified but the numerical value is `59.18` and the retrieved row's content says `Saturn Uccha Bala: 59.18 virupa` — confirm if grounded"). This would be an opt-in cost; deferred to v3.2 or later.

### §5.3 — Audit findings → operator dashboard → house-rules feedback

The dashboard's Audit Findings tab shows:
- Unresolved findings by class and severity (sortable).
- Drill-down: click finding → see trace_id, response text, retrieved signal IDs, cited IDs, fabricated IDs (highlighted).
- Resolve action: mark as "false positive" (heuristic was wrong), "fixed in next backfill", "house-rules updated to prevent", "needs investigation."
- Patterns: top 5 tools with most findings; top 5 finding classes by frequency; trend line over 30 days.

The feedback loop: a recurring finding class (e.g., `cite_fabricated` keeps showing up for `vector_search` results) tells the operator to update house-rules ("when citing from `vector_search` results, double-check that the cited ID appears in `provenance.signal_ids_available[]` for the same call — the chunk-vs-signal-id mapping in vector_search results is non-obvious"). The updated house-rules propagates to the next session's `marsys://house-rules` resource. The host learns. Audit findings decrease over time.

### §5.4 — Audit findings reachable to the host via `get_trace`

The v1 `get_trace` tool is extended in v3.1 to include attached audit findings in its return:

```jsonc
{
  "ok": true,
  "result": {
    "trace_id": "qry_...",
    "steps": [ /* unchanged */ ],
    "audit_findings": [
      {
        "class": "cite_grounded",
        "severity": "info",
        "description": "All cited signal IDs appeared in retrieved data.",
        "attached_at": "2026-05-23T03:14:22Z"
      },
      {
        "class": "ppl_missing",
        "severity": "warn",
        "description": "Response contains forward-looking language ('over the next antar') but no log_prediction call was made in this session.",
        "attached_at": "2026-05-23T03:14:22Z"
      }
    ]
  }
}
```

This gives the host a way to inspect what the audit said about its prior turn, mid-session. A discplined host with self-awareness can self-correct on the next turn — "the audit flagged me last turn for not emitting a log_prediction; I'll be more careful this turn." This is the structural improvement over v3.0's self-audit: instead of asking the host to validate itself before responding (which can be skipped), the system tells the host what the operator-side validation found (which the host can choose to attend to).

### §5.5 — Coverage limitation: response transcripts

Several audit checks (citation set-membership, numerical grounding, tier-template compliance) require the host's response text. Cowork sessions transcribe their full conversation to the platform via the cowork session-info MCP; Claude Chat sessions don't. The audit job degrades gracefully:
- Traces without response transcripts: get a subset of checks (B.11 floor and PPL emission, both verifiable from trace alone).
- The dashboard's Audit Findings tab shows `transcript_coverage_pct` per finding class so the operator knows the sample size.
- A v3.x enhancement could add an opt-in "send transcript" path from Claude Chat (e.g., a `send_transcript_to_audit` tool the host calls voluntarily). Deferred.

---

## §6 — Agent-facing surfaces

### §6.1 — `tool_health(tool_name?, window_hours?)`

**Purpose:** the host's quick look at what's working.

**Input:**
```jsonc
{
  "tool_name": "query_chart_facts",   // optional; if omitted, return all
  "window_hours": 24                  // optional; default 24, max 168
}
```

**Output:**
```jsonc
{
  "ok": true,
  "result": {
    "window_hours": 24,
    "as_of": "2026-05-22T20:15:00Z",
    "tools": [
      {
        "tool_name": "query_chart_facts",
        "source_kinds": ["mcp_primitive"],
        "calls_24h": 47,
        "ok_calls": 19,
        "zero_rows_calls": 27,
        "error_calls": 1,
        "ok_rate": 0.40,
        "zero_rows_rate": 0.57,
        "latency": {
          "p50_ms": 8,
          "p95_ms": 18,
          "p99_ms": 42,
          "interpretation": "informational; not a target"
        },
        "depth": {
          "avg_rows_returned": 3.2,
          "avg_bundle_size_tokens": null,   // n/a for primitives
          "depth_score": 1.8                // = grounding_rate × log(1 + avg_rows)
        },
        "grounding": {
          "grounding_rate_24h": 0.85,
          "grounding_rate_coverage_pct": 0.62   // 62% of calls had transcripts
        },
        "data_sources_backing": ["chart_facts (FORENSIC L1)"],
        "caveats": [
          {
            "text": "Categories shadbala, ashtakavarga_*, kp_*, upagraha currently return 0 rows. Backfill scheduled v3.3-S1.",
            "class": "data_depth_gap",
            "severity": "warn"
          }
        ],
        "recent_audit_findings_24h": {
          "cite_fabricated": 0,
          "numerical_unverified": 2,
          "b11_skipped": 0
        },
        "last_call_at": "2026-05-22T20:13:42Z"
      },
      { /* ... one block per tool ... */ }
    ]
  }
}
```

**Tier-gating:** super_admin + acharya can call; client gets 403 with a `house-rules` reference. The host knows ahead of time (from the `capabilities` resource at session attach) whether it has permission.

### §6.2 — `data_coverage(asset_id?, subkey?)`

**Purpose:** the host's view of data completeness.

**Input:**
```jsonc
{
  "asset_id": "chart_facts",    // optional
  "subkey": "shadbala"          // optional; only valid with asset_id
}
```

**Output:**
```jsonc
{
  "ok": true,
  "result": {
    "as_of": "2026-05-22T20:15:00Z",
    "assets": [
      {
        "asset_id": "chart_facts",
        "asset_version": "8.0",
        "last_bootstrap_ts": "2026-05-19T08:00:00Z",
        "total_rows": 213,
        "subkeys": [
          { "subkey": "planet",           "actual": 9,  "expected": 9,  "coverage_pct": 1.00, "status": "complete",    "caveat_class": null },
          { "subkey": "house",            "actual": 12, "expected": 12, "coverage_pct": 1.00, "status": "complete",    "caveat_class": null },
          { "subkey": "strength",         "actual": 9,  "expected": 9,  "coverage_pct": 1.00, "status": "complete",    "caveat_class": null },
          { "subkey": "shadbala",         "actual": 0,  "expected": 63, "coverage_pct": 0.00, "status": "missing",     "caveat_class": "data_depth_gap", "next_backfill_planned": "v3.3-S1" },
          { "subkey": "ashtakavarga_sav", "actual": 0,  "expected": 12, "coverage_pct": 0.00, "status": "missing",     "caveat_class": "data_depth_gap", "next_backfill_planned": "v3.3-S1" },
          { "subkey": "bhava_bala",       "actual": 4,  "expected": 12, "coverage_pct": 0.33, "status": "sparse",      "caveat_class": "data_depth_gap", "next_backfill_planned": "v3.3-S2" }
          /* ... */
        ],
        "missing_subkeys_count": 18,
        "total_subkeys_count": 37,
        "asset_completeness_pct": 0.51,
        "notes": "Phase 4C completed for panchang; chart_facts is the v3.3 priority."
      },
      {
        "asset_id": "msr_signals",
        "asset_version": "5.0",
        "last_bootstrap_ts": "2026-05-15T12:00:00Z",
        "total_rows": 514,
        "subkeys": null,
        "asset_completeness_pct": 1.00,
        "citation_grounded_pct": 0.73,
        "notes": "419/573 signals lack explicit FORENSIC/LEL citations. v3.4-S1 closes this gap."
      },
      {
        "asset_id": "classical_texts",
        "asset_version": "TBD",
        "last_bootstrap_ts": null,
        "total_rows": 0,
        "subkeys": [
          { "subkey": "BPHS",            "actual": 0, "expected": 1500, "coverage_pct": 0.00, "status": "pending", "next_backfill_planned": "v3.2-S1" },
          { "subkey": "Jaimini Sutram",  "actual": 0, "expected": 400,  "coverage_pct": 0.00, "status": "pending", "next_backfill_planned": "v3.2-S2" },
          { "subkey": "KP Reader",       "actual": 0, "expected": 2000, "coverage_pct": 0.00, "status": "pending", "next_backfill_planned": "v3.2-S2" },
          { "subkey": "Tajaka Neelakanthi","actual": 0, "expected": 500, "coverage_pct": 0.00, "status": "pending", "next_backfill_planned": "v3.2-S3" }
        ],
        "asset_completeness_pct": 0.00,
        "notes": "Classical-grounding rubric capability — v3.2 is the entire ship of this corpus."
      }
      /* ... */
    ]
  }
}
```

The `caveat_class` is on every subkey row — split between `data_depth_gap` and `tool_reliability_gap`. The host knows whether the empty result it's about to deliver to the user is "this isn't backfilled" (data) vs "this tool has a bug" (code).

### §6.3 — `marsys://capabilities` resource (auto-loaded at session attach)

Built at session attach. Loads the same data the tools above return, pre-formatted as compact markdown. Tier-conditioned content per §3.5 of arch doc.

Structure (super_admin / acharya view):

```markdown
# MARSYS-JIS — Current Operational State (as of 2026-05-22T20:15:00Z)

## Tools (21)

### Surgical primitives (10)
- **query_chart_facts** — FORENSIC L1 chart facts.
  - Real categories: planet, house, strength, birth_metadata, dasha_vimshottari, shadbala, ashtakavarga_sav, ashtakavarga_bav, ashtakavarga_pinda, kakshya_zone, bhava_bala, kp_cusp, kp_planet, kp_significator, upagraha, mrityu_bhaga, longevity_indicator, avastha, varshphal, arudha, arudha_occupancy, saham, sensitive_point, cusp, chandra_placement, navatara, dasha_chara, dasha_yogini, deity_assignment, yoga, special_lagna, strength_extra, chalit_shift, mercury_convergence, aspect, ishta_kashta, panchang.
  - **Coverage caveat (data_depth_gap, warn):** categories shadbala, ashtakavarga_*, kp_*, upagraha, mrityu_bhaga, longevity_indicator, avastha, varshphal currently return 0 rows. Backfill scheduled v3.3-S1+S2. **Prefer query_signals for strength claims until then.**
  - 24h: 47 calls, 40% ok, 57% zero-rows, p50 8ms, grounding 85%.
- **query_signals** — MSR signal corpus (514 signals).
  - **Coverage note:** 27% of signals lack explicit FORENSIC/LEL citations (v3.4-S1 backfill).
  - 24h: 312 calls, 97% ok, 2% zero-rows, p50 35ms, grounding 91%.
- **query_dasha_periods** — dasha schedules (Vimshottari, Chara, Yogini, Char, Yogini, Kalachakra). Full coverage.
  - 24h: 28 calls, 100% ok, p50 12ms, grounding 88%.
- **query_panchanga** — daily panchang, full enrichment, 1900–2100.
  - 24h: 18 calls, 100% ok, p50 24ms, grounding 78%.
- **query_ephemeris** — planetary positions, full coverage 1900–2100.
- **query_transit_event** — transit-event search.
- **lel_query** — Life Event Log. 36 events + 5 period summaries + 6 chronic patterns. Complete.
- **vector_search** — RAG semantic search (~14k chunks, Vertex 768-dim).
  - **Usage hint:** since v3.1 fix, returns relevant chunks for user query (was returning generic chunks in v1). Recommended top_k=25.
- **get_cgm_subgraph** — CGM topology (~500 nodes / ~1200 edges).
- **cross_school_lookup** — multi-school stance per claim.
  - **Coverage caveat (data_depth_gap, warn):** Tajaka ~20%, KP ~60%, Jaimini ~80%, Parashara 100%. v3.2 closes these gaps.

### Composite bundles (2) — opt-in orchestration aids
- **holistic_bundle(query_text, focus_domains?, time_window?, subset?)** — parallel fan-out across 8 sub-tools. **Use when intent is diffuse or you want a one-call B.11 floor satisfier.** When intent is targeted, compose primitives directly.
- **multi_school_bundle(claim, schools?)** — per-school evidence + classical-text excerpts. **Use for triangulation queries.**

### Raw asset reads (2)
- **read_asset(canonical_id, section?)** — MSR / UCN / CDLM / CGM / RM / FORENSIC / LEL.
- **read_classical_text(work, chapter?, verse_range?)** — BPHS / Jaimini Sutram / KP Reader / Tajaka. **Coverage caveat: v3.1 ships with sparse corpus; full coverage lands v3.2.**

### Observability (2)
- **get_trace(trace_id)** — step ledger + attached audit findings (new in v3.1).
- **list_recent_queries(limit?, since?)**.

### Perf / coverage (2)
- **tool_health(tool_name?, window_hours?)**, **data_coverage(asset_id?, subkey?)**.

### Writes (3)
- **log_prediction(horizon_days, domain, prediction_text, confidence_band, falsifier, source_signals)**.
- **record_outcome(prediction_id, outcome, observed_at, notes?)**.
- **flag_disagreement(class, description, evidence_signal_ids)** (super_admin only).

## Data sources (live coverage)

| Asset | Version | Completeness | Notes |
|---|---|---|---|
| FORENSIC (chart_facts) | v8.0 | 51% | shadbala, ashtakavarga_*, kp_* pending v3.3. |
| MSR (msr_signals) | v5.0 | 100% loaded; 73% citation-grounded | v3.4-S1 closes citation gap. |
| LEL (lel_events) | v1.6 | 100% | 36 events + 5 periods + 6 patterns. |
| CGM | v9.0 | 100% indexed | ~500 nodes / ~1200 edges. |
| UCN + CDLM + RM | v4.1 / v1.3 / v2.2 | 100% in RAG | |
| panchang_daily | post-Phase-4C | 100%, 1900–2100, full enrichment | |
| ephemeris_daily | Phase-4B | 100%, 1900–2100 | |
| multi_school_* | partial | Parashara 100%, Jaimini ~80%, KP ~60%, Tajaka ~20% | v3.2 closes. |
| classical_texts | unindexed at v3.1 | 0% | v3.2 is the entire ship of this corpus. |

## Calibration history (last 90d)
| Confidence band | Domain | Horizon | Predictions | Realized rate (95% CI) |
|---|---|---|---|---|
| 0.7-0.8 | career | 31–180d | 4 | 0.50 (0.15–0.85) — small sample |
| 0.7-0.8 | health | <=30d | 2 | 0.50 (0.07–0.93) — small sample |
| 0.8-0.9 | (all) | <=30d | 6 | 0.83 (0.44–0.97) |

(Sample sizes small at v3.1 start; calibration accumulates over time.)

## Audit findings (last 24h, summary)
- 0 cite_fabricated findings
- 2 numerical_unverified findings (one for vector_search — operator reviewing)
- 0 b11_skipped findings
- 1 ppl_missing finding (forward-looking response in a session that didn't call log_prediction — house-rules reminder recommended)
```

Client-tier `capabilities` resource is the same tool list (with the same caveats — clients deserve honesty about what's working) but without the per-tool reliability stats and without the audit findings summary. ~5k tokens at super_admin/acharya; ~1.5k at client.

---

## §7 — Operator dashboard at `/admin/mcp/health`

Single HTML page, super_admin only, mounted alongside `/admin/mcp/keys`. **Five tabs** (Sonnet's v3.0 had three).

### §7.1 — Tab 1: Tool Health

Sortable table, one row per MCP tool. Same as Sonnet's v3.0 but with two additions:

| Tool | Source | Calls 24h | OK% | Zero-rows% | Error% | p50 ms | p95 ms | Grounding% | Depth score | Audit findings 24h | Caveats |
|---|---|---|---|---|---|---|---|---|---|---|---|
| query_chart_facts | primitive | 47 | 40% | 57% 🔴 | 2% | 8 | 18 | 85% | 1.8 | 0 / 2 / 0 | [edit] |
| query_signals | primitive | 312 | 97% | 2% | 1% | 35 | 88 | 91% | 4.5 | 0 / 1 / 0 | [edit] |
| holistic_bundle | bundle | 24 | 100% | 0% | 0% | 11200 | 24000 | n/a | 5.7 (composite) | 0 / 0 / 0 | [edit] |

Latency cells use no red coloring unless p95 > 30 s on a frequently-called tool (consistent with §3.1's "latency is informational"). Audit findings column shows `class_1 / warn / info` counts.

Click a row → drill-down: time-series of latency over 7 days (Chart.js line); error log; top failing parameter combinations; recent traces; calibration history if the tool's signals appeared in any predictions.

Inline-editable `caveats` column. Operator can write a one-liner with a `caveat_class` dropdown; saves to `tool_caveats`; surfaces in next `tool_health()` call and next `marsys://capabilities` resource build.

### §7.2 — Tab 2: Data Coverage

Two-level table. Top level = asset. Click → expand to subkey breakdown:

```
chart_facts (v8.0)            51% complete            213/420 expected rows
  Last bootstrap: 2026-05-19  Next planned: v3.3-S1 (shadbala + ashtakavarga)
  ├─ planet                   100%                    9/9
  ├─ house                    100%                    12/12
  ├─ strength                 100%                    9/9
  ├─ shadbala                   0%  🔴 MISSING        0/63   [data_depth_gap]    Next: v3.3-S1
  ├─ ashtakavarga_sav           0%  🔴 MISSING        0/12   [data_depth_gap]    Next: v3.3-S1
  ├─ bhava_bala                33%  🟡 SPARSE         4/12   [data_depth_gap]    Next: v3.3-S2
  └─ ...

msr_signals (v5.0)            100% loaded             514/514
  ├─ citation-grounded         73%                    375/514
  └─ ungrounded                27%                    139/514   Next: v3.4-S1

multi_school_*                Parashara 100%, Jaimini 80%, KP 60%, Tajaka 20%
  ├─ Parashara                 100% ✓
  ├─ Jaimini                    80% 🟡    Next: v3.2-S4
  ├─ KP                         60% 🔴    Next: v3.2-S4
  └─ Tajaka                     20% 🔴    Next: v3.2-S5

classical_texts               0% (unindexed at v3.1)
  ├─ BPHS                       0%  🔴    Next: v3.2-S1   ~1500 verse-rows expected
  ├─ Jaimini Sutram             0%  🔴    Next: v3.2-S2   ~400
  ├─ KP Reader                  0%  🔴    Next: v3.2-S2   ~2000
  └─ Tajaka Neelakanthi         0%  🔴    Next: v3.2-S3   ~500
```

Inline `next_backfill_planned` + `notes` editable per row. Color coding by `caveat_class`: depth gaps in amber, reliability gaps in red. Status thresholds: complete (100%), sparse (10–80%), missing (<10%), pending (planned but not started).

### §7.3 — Tab 3: Audit Findings

The dashboard tab unique to v3.1. Shows the output of the nightly audit subsystem.

**Top:** summary cards for last 24h: `class_1 findings: 0`, `warn findings: 3`, `info findings: 1429`. Trend sparklines over 30d.

**Filters:** finding class (multi-select), severity (multi-select), resolved/unresolved, audience tier, mcp_tool_name, date range.

**Table:** sortable, one row per finding.

| Finding class | Severity | Trace | Tool | Mcp_key | Description | Attached | Status | Resolve |
|---|---|---|---|---|---|---|---|---|
| cite_fabricated | class_1 | qry_2026-05-22_8f3a | (multi) | mcp_acharya_x | Response cited SIG.MSR.999 (not in bundle) | 03:14 | unresolved | [▼] |
| ppl_missing | warn | qry_2026-05-22_2b1c | holistic_bundle | mcp_super_admin | Response contains "over the next antar" but no log_prediction emitted | 03:14 | unresolved | [▼] |
| numerical_unverified | warn | qry_2026-05-22_5d7e | vector_search | mcp_acharya_y | Claim "59.18 virupa" not in retrieved row contents (false positive likely — confirm in trace) | 03:14 | unresolved | [▼] |

Drill-down per finding → see trace details, response text, retrieved IDs, cited IDs. Resolve actions: `false_positive` (heuristic was wrong; record the heuristic miss), `fixed_in_next_backfill` (links to a planned data/code change), `house_rules_updated` (free-form note of the house-rules iteration), `needs_investigation` (operator backlog).

**Bottom:** pattern aggregations. "Top 5 tools by cite_fabricated count this week." "Trend: ppl_missing rate down 60% since house-rules v3.1.2." "Open findings older than 7 days." These are the operator's prompt-engineering surface — they tell you which house-rules variant needs updating.

### §7.4 — Tab 4: Predictions / Calibration

Two sub-tables.

**Recent predictions (last 90d):**

| Logged at | Domain | Horizon | Prediction text (truncated) | Confidence band | Source signals | Outcome | Outcome recorded |
|---|---|---|---|---|---|---|---|
| 2026-04-15 | career | 90d | "Promotion talks materialize…" | 0.7-0.8 | [SIG.MSR.317, ...] | realized | 2026-05-10 |
| 2026-05-01 | health | 30d | "Energy levels improve…" | 0.6-0.7 | [SIG.MSR.421] | partial | 2026-05-22 |
| 2026-05-10 | career | 180d | "External opportunity…" | 0.6-0.7 | [SIG.MSR.388] | pending | n/a |

Click a prediction → see the trace it was logged from, the source signals, the host's stated falsifier, and a `record_outcome` button if pending and horizon reached.

**Calibration grid (90d window, refreshed nightly):**

| Confidence band | Domain | Horizon bucket | N | Realized rate (95% CI) | Discrepancy |
|---|---|---|---|---|---|
| 0.5-0.6 | (all) | <=30d | 12 | 0.58 (0.30–0.83) | aligned |
| 0.6-0.7 | career | 31–180d | 8 | 0.50 (0.18–0.82) | aligned (small N) |
| 0.7-0.8 | career | 31–180d | 4 | 0.50 (0.15–0.85) | **under-realized — investigate** |
| 0.8-0.9 | health | <=30d | 6 | 0.83 (0.44–0.97) | aligned |

"Discrepancy" column flags bands where the realized rate is more than one CI-band off the band's midpoint (under- or over-realized). These are the cells where the host's calibration is wrong; they feed the operator's house-rules iteration ("0.7-band career-domain predictions are under-realized; recommend the host be more conservative or expand the falsifier criteria for those").

Per band/domain cell, a sparkline of realized-rate over time tells whether calibration is improving, regressing, or stable.

### §7.5 — Tab 5: Sessions

Recent MCP sessions, per API key. For each session:

| Session hour | Principal | Tier | Tools called | Primitives / Bundles | Unique tools | Predictions logged | Audit findings | Bundle tokens |
|---|---|---|---|---|---|---|---|---|

Use case: spot patterns. "Acharya X's session called `query_chart_facts(shadbala)` 4 times and got zero rows each time — they hit the gap; we should add a per-tier hint to house-rules that primes the host away from shadbala until v3.3 closes." Operator clicks the session → sees the full trace timeline → can author a `tool_caveats` row from there.

### §7.6 — Alerts

Threshold-based Slack + email hooks. Operator-configurable per metric:

| Alert | Default threshold | Channel |
|---|---|---|
| `zero_rows_rate` spike | >0.30 over 1h on a tool that averaged <0.10 over prior 24h | Slack #marsys-ops |
| `error_rate` spike | >0.05 over 1h | Slack #marsys-ops |
| `cite_fabricated` rate | >0.05 over 24h, any tool | Slack + email |
| `b11_skipped` count | >5 in 24h | Email digest |
| Calibration discrepancy | new band cell exceeds 1-CI deviation from midpoint, N≥10 | Slack #marsys-ops |
| `p95_latency_ms` spike | >2x baseline on frequently-called tool | Slack (info only — no action required) |

All alerts are configurable from a small `mcp_alerts_config` table the operator edits via dashboard. Defaults are conservative — calibration discrepancies require N≥10 to fire (to avoid false alarms on small-sample bands).

### §7.7 — Page refresh + data freshness

Page polls `tool_health()` and `data_coverage()` every 30 seconds (cheap; mat-view query is sub-100ms). Calibration tab polls every 5 minutes. Audit findings tab polls every 1 minute when there are unresolved class_1 findings; every 10 minutes otherwise.

---

## §8 — Collection and retention infrastructure

**Collection.** Already happens — `tool_execution_log` is written by every retrieval tool. v3.1 adds five columns (§4.1) and writes to four new tables (`mcp_audit_findings`, `mcp_prediction_outcomes`, `data_source_expected`, `tool_caveats`).

**Aggregation.** Materialized views refresh on schedules:
- `mv_tool_metrics_24h` — every 5 minutes
- `mv_data_source_coverage` — nightly at 02:00 UTC, or on-demand after a backfill
- `mv_session_summary` — every 10 minutes
- `mv_tool_grounding_24h` — every 15 minutes
- `mv_calibration_score` — nightly at 04:00 UTC (after audit job finishes at 03:30)

Audit job: nightly at 03:00 UTC. Cron entry in the existing Cloud Run scheduler (the same one that runs Observatory's nightly reconciliation and Phase 4C's panchang refresh).

**Retention.**
- `tool_execution_log` — 90 days hot, archives to GCS Parquet older (matches existing trace-log retention).
- `query_trace_steps` — 365 days hot (longer because audit job needs them; small table).
- `mcp_audit_findings` — 730 days (governance audit material; small table; valuable for long-horizon analysis).
- `mcp_predictions` + `mcp_prediction_outcomes` — indefinite (this is the calibration dataset; cannot be pruned).
- `data_source_expected`, `tool_caveats`, `mcp_alerts_config` — indefinite (small operator-authored tables).

**Indices.** Added to `tool_execution_log`:
- `(source, mcp_tool_name, timestamp DESC)` — supports `mv_tool_metrics_24h`
- `(mcp_key_id, timestamp DESC)` — supports `mv_session_summary`
- `(trace_id)` — supports audit-side joins (existing in v1)
- `(audience_tier, timestamp DESC)` — supports per-tier rollups
- `(bundle_trace_id)` — supports sub-tool drill-down

Added to `mcp_audit_findings`: see §4.3.
Added to `mcp_predictions`: `(confidence_band, domain, horizon_days)` for calibration view.
Added to `mcp_prediction_outcomes`: `(prediction_id)` for the calibration view's join.

---

## §9 — The prediction-calibration loop (the long-horizon measurement)

This is the perf system's most strategic measurement. v3.0 didn't address it; v3.1 makes it first-class because the rubric's `calibrated_epistemics` dimension can only be validated by it.

### §9.1 — The loop

```
Host's response includes forward-looking claim
    ↓
Host calls log_prediction(horizon_days, domain, prediction_text, confidence_band, falsifier, source_signals)
    ↓
Row written to mcp_predictions
    ↓
Time passes (1 day to several years, depending on horizon)
    ↓
Native (or trusted observer) calls record_outcome(prediction_id, outcome, observed_at, notes)
    ↓
Row written to mcp_prediction_outcomes
    ↓
Nightly mv_calibration_score refresh aggregates by (confidence_band, domain, horizon_bucket)
    ↓
Dashboard Tab 4 surfaces the calibration grid
    ↓
Operator identifies under- or over-realized bands
    ↓
Operator updates house-rules: "0.7-band career predictions are under-realized; be more conservative"
    ↓
Next session's marsys://house-rules carries the update
    ↓
Host's subsequent confidence-band choices shift
    ↓
Calibration improves over many sessions
```

Two things make this hard, both honestly:

**Sample size.** A given `(confidence_band, domain, horizon_bucket)` cell may have 4 predictions in a 90-day window. Wilson confidence intervals on N=4 are very wide. The system reports them honestly. Operators interpret with caution. Over years, sample sizes grow.

**Outcome recording cadence.** Forward-looking claims need outcomes to be recorded. Some happen organically (the native or an observer notices "the prediction realized"); some need explicit prompting. The dashboard's Tab 4 surfaces pending-and-horizon-reached predictions with a one-click `record_outcome` action; daily email digests of "predictions whose horizon has passed without an outcome" can be authored as a scheduled task (see §10 below).

### §9.2 — Calibration as feedback into house-rules

The most important consumer of calibration data is the operator authoring house-rules variants. Three rules of thumb:

**If a band is consistently under-realized (CI lower bound > band midpoint),** the host is over-confident in that band/domain/horizon. House-rules update: "predictions in domain X at horizon Y require additional caveats; downgrade confidence by one band when ambiguity exists."

**If a band is consistently over-realized (CI upper bound < band midpoint),** the host is under-confident. House-rules update: "high-confidence claims in domain X at horizon Y are well-supported by the data; the host may state them with appropriate confidence rather than hedging."

**If a band's discrepancy is N/A (too few samples),** the operator does not adjust. The system reports the small-sample state honestly.

Calibration data is itself a research output of the instrument: across many sessions, the per-band-per-domain-per-horizon hit-rate matrix is publishable evidence of the instrument's epistemic discipline. This is one of the things that makes MARSYS-JIS a research instrument and not just a deployment.

### §9.3 — Why this lives in the perf brief, not the arch doc

Calibration is a measurement subsystem with a deep data layer (`mcp_prediction_outcomes` joined with `mcp_predictions` on a 30–730+ day horizon) and an operator-side analysis surface (Dashboard Tab 4). The architecture doc establishes the *tools* (`log_prediction`, `record_outcome`); the perf brief establishes the *system that turns prediction logs into calibration scores*. The split is clean: tools are how the host interacts; the perf system is how the operator measures.

---

## §10 — Three feedback loops (the cohesion claim)

The unifying claim of v3.1's perf system: **operator's view, host's view, and governance verification are the same view from three angles.** Three concrete loops:

### §10.1 — Session-start loop

`marsys://capabilities` loaded at attach. Host knows shadbala is empty, Tajaka is sparse, vector_search is fixed, the operator has authored a caveat about preferring `query_signals` for strength claims. When the user asks "which is my strongest planet?", host doesn't waste a call on `query_chart_facts(shadbala)`. It goes straight to `query_signals` + `query_chart_facts(strength)`. The user gets the right answer on first try.

### §10.2 — Mid-session loop

Host calls a primitive and gets unexpected results (zero rows, or rows that don't match what the user asked). Host calls `tool_health(tool_name)` and `data_coverage(asset_id)` to disambiguate. Result: data problem (skip + disclose to user) vs transient problem (retry) vs misunderstood-the-data-shape (re-read the asset's coverage notes). The host self-corrects within the turn.

Optionally: host calls `get_trace(prior_trace_id)` to see what the audit said about its previous turn. If a finding says "ppl_missing", the host emits a `log_prediction` for the forward-looking claim it made last turn (retroactive, but auditable).

### §10.3 — Operator-feedback loop

Operator edits `tool_caveats`, `data_source_expected.next_backfill_planned`, or `house-rules` based on aggregate patterns visible on the dashboard. The next session's `marsys://capabilities` and `marsys://house-rules` carry the operator's edits. The host's behavior shifts in the direction the operator intended. The cycle repeats. Over many sessions, the system tunes itself.

This is the "first-class agent context" claim from Sonnet's v3.0, sharpened: the operator is the prompt-engineer of the instrument's epistemic discipline, the agent is the operator's deputy, and the governance verification (audit subsystem) is the impartial third party that keeps both honest.

### §10.4 — Where the loop breaks (acknowledged)

- **Claude Chat sessions don't transcribe responses.** Audit subsystem checks degrade gracefully (B.11 floor and PPL emission still verifiable from trace; citation grounding only verifiable on Cowork sessions). This is documented as a known limitation in §5.5.
- **Heuristic audit produces false positives.** Operator marks them `false_positive` on the dashboard; heuristic accuracy improves over time as the operator's marks accumulate.
- **Calibration over short timeframes is noisy.** Wilson CIs reported honestly; operators advised to interpret with caution at small N.
- **Outcome recording is operator-dependent.** A scheduled task ("daily horizon-reached digest") helps; full automation would require external grounding (e.g., LEL ingestion from observed life events) which is the LEL workstream's responsibility, not perf system's.

---

## §11 — Migration plan

### Phase P0 — Source-table extensions (1 session, parallelizable with v3.1.0-S1)

- ALTER `tool_execution_log` to add `source`, `mcp_key_id`, `mcp_tool_name`, `audience_tier`, `bundle_trace_id` columns.
- Backfill existing rows with NULLs.
- Update `writeToolExecutionLog()` and `writeBundleSubToolLog()` (new helper) to set these.
- Create `mcp_audit_findings`, `mcp_prediction_outcomes`, `data_source_expected`, `tool_caveats`, `mcp_alerts_config` tables. Seed `data_source_expected` from operator (initial values committed to `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql`).

### Phase P1 — Materialized views (1 session)

- Create the 6 materialized views (§4.2).
- Wire 5-min / 10-min / 15-min / nightly refresh into the existing Cloud Run scheduler. One new cron entry per view.
- Smoke: query each view manually, confirm shape.

### Phase P2 — MCP tools (1 session — bundled with v3.1.0-S4 work)

- Implement `/api/mcp/health/tools` + `/api/mcp/health/coverage` platform endpoints.
- Implement MCP tools `tool_health` + `data_coverage` in `platform-mcp/src/tools/`.
- Tier-gating enforced at endpoint level (client tier 403's).
- Test: call from Claude Chat + Cowork, verify structure.

### Phase P3 — Capabilities resource (~1 hour — bundled with v3.1.0-S3 resource work)

- Implement resource generator at `platform-mcp/src/resources/capabilities.ts` that compiles `tool_health` + `data_coverage` + tool descriptions + recent audit findings into the markdown structure (§6.3).
- Tier-conditioned: super_admin / acharya see full; client sees abridged.
- Wire to MCP resource registration.
- Test: session-attach in Claude Chat + Cowork, verify resource auto-loads.

### Phase P4 — Audit subsystem (1 session — bundled with v3.1.0-S4)

- Implement nightly audit job at `platform-mcp/jobs/audit_nightly.ts` (or platform-side, depending on infra). Cron at 03:00 UTC.
- Implement extraction heuristics (`extract_citations`, `extract_numerical_claims`, `has_forward_looking_language`, `glosses_first_sanskrit_use`, `is_non_factual_response`, `check_layer_attribution`).
- Wire findings into `mcp_audit_findings`.
- Extend `get_trace` MCP tool to include findings in its return.
- Test: run audit on a backfilled day of v1 traces; verify findings shape; verify at least one `cite_fabricated` finding gets generated from a known v1 trace.

### Phase P5 — Operator dashboard (1 session — bundled with v3.1.0-S5)

- Implement `/admin/mcp/health` page in the platform's existing admin UI shell.
- Five tabs (§7.1–§7.5). Inline-editable caveats / backfill notes / alert thresholds.
- Implement Slack/email alert dispatch on threshold breaches (§7.6).
- Test: edit a caveat → refresh → verify it surfaces in `tool_health()` MCP call + `marsys://capabilities` resource on next session.

### Phase P6 — Calibration loop (1 session — bundled with v3.4-S1 or v3.4-S2 closing)

- Implement `wilson_lower_bound` and `wilson_upper_bound` SQL functions (or use a Postgres extension).
- Build `mv_calibration_score` materialized view.
- Implement Tab 4 of the dashboard.
- Implement scheduled task "daily horizon-reached digest" (one email per day listing pending predictions whose horizon has passed).
- Test: record outcomes for at least 5 historical predictions; verify the grid populates; verify CIs render.

**Total: 6 phases bundled into v3.1.0 (P0–P5) + 1 phase in v3.4 (P6).** Each phase is a closed sub-session of the corresponding architecture phase.

---

## §12 — Open questions (with Opus 4.7's positions)

Sonnet flagged 7 open questions in v3.0 §10. v3.1 settles most.

| # | Question | v3.1 position |
|---|---|---|
| Q1 | Should `tool_health()` be tier-gated? | **Settled: super_admin + acharya only; client 403.** Arch §3.5. |
| Q2 | Should the dashboard show LLM cost (Observatory)? | **Cross-link from `/admin/mcp/health` → `/admin/observatory`** rather than duplicate. Cheap one-line add to the dashboard nav. The two systems remain separate; perf brief is retrieval-focused, Observatory is LLM-cost-focused. |
| Q3 | Alerting thresholds? | **Settled: yes, ship with v3.1.0-S5 / P5.** Defaults in §7.6; operator-configurable via `mcp_alerts_config`. |
| Q4 | Should `marsys://capabilities` be tier-conditioned? | **Settled: yes.** Super_admin + acharya see full snapshot; client sees tool names + caveats only (no reliability stats, no audit findings, no calibration history). §6.3. |
| Q5 | Data freshness for `marsys://capabilities` — refresh on every session attach, or cache? | **Settled: refresh on attach, no per-session caching.** Materialized views underneath cache; the resource generator is sub-100ms. Refresh-on-attach gives the host the freshest possible view. |
| Q6 | Cross-session learning — should Claude write back what it learned? | **Already covered by `log_prediction` + audit subsystem.** No additional surface needed. The host's confidence-band choices are captured at prediction time; calibration loop measures hit rates; operator iterates house-rules. The cycle works without a separate "learning" write tool. |
| Q7 | Should the operator be able to disable a tool from the dashboard? | **Settled: yes, ship with v3.1.0-S5.** `tool_registry.tool_enabled` boolean; MCP primitives dispatcher checks before executing. `tool_health()` reports disabled status. Useful for "stop calling X until Y is fixed" cases. |

### §12.1 — New open questions surfaced by v3.1

| # | Question | v3.1 position |
|---|---|---|
| Q8 | How should the audit job handle the response-transcript availability gap? (Cowork transcribes; Claude Chat doesn't.) | **For v3.1: degrade gracefully** (subset of checks on non-transcribed traces) and report `transcript_coverage_pct` per finding class. **For v3.x:** consider an opt-in `send_transcript_to_audit` MCP tool the host calls voluntarily for Claude Chat sessions. The host writing its own response to the audit is a slight self-audit risk; mitigated because the audit *runs the checks*, the host just submits the text. Defer to v3.2 or v3.3. |
| Q9 | Should the audit job include an LLM-based second-pass for borderline findings? | **Recommend: defer to v3.3 or later.** v3.1 ships with heuristics-only. LLM-second-pass adds cost and reintroduces an LLM into the governance loop (which v3.1's pure-MCP framing tried to remove). If heuristic false-positive rate proves too high, revisit. |
| Q10 | Should calibration scores affect the host's default confidence-band choices? (i.e., should the system *automatically* shift the host toward more conservative confidence when a band is under-realized?) | **Recommend: no, not automatically.** The operator authors `house-rules` updates based on calibration data. Auto-shifting confidence based on metrics creates a feedback loop where the system loses calibration in one direction in response to noise. Keep the operator in the loop. |
| Q11 | Should the dashboard expose a "audit-replay this trace" button for trace forensics? | **Recommend: yes, ship with v3.4 (after audit subsystem matures).** Operator clicks → audit job re-runs all checks against the trace with current heuristics. Useful for re-evaluating findings as heuristics improve. |

---

## §13 — One-paragraph TL;DR

The MCP performance system under v3.1 is three subsystems sharing one materialized-view substrate over `tool_execution_log` plus four new tables (`mcp_audit_findings`, `mcp_prediction_outcomes`, `data_source_expected`, `tool_caveats`). The **agent-facing surface** is two MCP tools (`tool_health`, `data_coverage`) and the `marsys://capabilities` resource auto-loaded at session attach — giving the host pre-knowledge of tool/data state before the user opens their mouth. The **operator-facing surface** is the `/admin/mcp/health` dashboard with five tabs (Tool Health, Data Coverage, Audit Findings, Predictions/Calibration, Sessions) plus Slack/email alerting on threshold breaches. The **governance-facing surface** is the nightly audit subsystem — the structural replacement for v3.0's self-audit (`validate_response`) — that verifies B.11 floor compliance, citation set-membership against the strict cite-allowlist contract, numerical claim grounding, PPL emission for forward-looking responses, tier-template compliance, and layer-purity attribution; findings are written to `mcp_audit_findings`, surfaced on the dashboard, and reachable to the host via extended `get_trace`. The **prediction-calibration loop** turns logged predictions plus recorded outcomes into per-(confidence-band × domain × horizon-bucket) realized rates with Wilson confidence intervals, feeding the operator's house-rules iteration over time; this is the only metric that empirically validates the rubric's calibrated-epistemics dimension and the long-term research output that makes MARSYS-JIS an instrument and not just a deployment. The §12 depth-over-tokens directive is baked throughout: `avg_bundle_size_tokens` is honest depth reporting (not a minimization target), `depth_score` replaces "token efficiency" thinking, latency is informational rather than ranked, and the caveat taxonomy distinguishes data-depth gaps from tool-reliability gaps because they have different mitigations. The system is additive — no retrieval tool's behavior changes — and tier-aware, with `tool_health` / `data_coverage` visible to super_admin + acharya and hidden from client. Ships in 6 phases bundled into v3.1.0 + 1 phase in v3.4. The unifying claim: operator's view, host's view, and governance verification are the same view from three angles, with the operator as prompt-engineer of the instrument's epistemic discipline and the audit subsystem as the impartial third party keeping the loop honest. Without this system, v3.1 is a blindfolded orchestrator with no closed governance loop; with it, the agent is informed, the operator sees data debt and audit drift as actionable backlog, and the calibration grid grows into the publishable record of the instrument's epistemic discipline.

---

*End of MCP_PERF_SYSTEM_BRIEF_2026-05-22.md v3.1 (DRAFT, Opus 4.7 regeneration). Paired with `MCP_ARCH_v3_PROPOSAL_2026-05-22.md` v3.1. Companion handoff in `MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md`. Awaits native review; if accepted, supersedes Sonnet's v3.0 in place.*
