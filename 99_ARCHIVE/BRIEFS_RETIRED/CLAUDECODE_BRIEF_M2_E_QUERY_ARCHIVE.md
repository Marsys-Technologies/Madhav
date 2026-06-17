---
brief_id: M2_E_QUERY_ARCHIVE
karn_session_name: KARN-W2-R4-QUERY-ARCHIVE
wave: 2
stream: E
status: PENDING
authored_by: Claude (Cowork) 2026-04-30 — Wave 1 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (GCP infra + BigQuery schema + GCS bucket + writers + backfill + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W1-R3-OBSERVABILITY (created audit_events + query_plans, established
    non-blocking writer pattern in consume/route.ts onFinish).
  blocks: |
    M2_E2_EVAL_HARNESS (W7-R1) — eval harness reads from query_archive BigQuery
    table, NOT from Cloud SQL audit_events directly.
    M2_E1_PROVENANCE_AUDIT (W6-R3) — provenance audits run BigQuery analytical
    queries over archive.
    Native's offline analysis loop — depends on archive being populated.
parallel_stream_note: |
  Wave 2 was originally three briefs (W2-R1 MSR ETL, W2-R2 chart_facts ETL,
  W2-R3 CGM edges). The native added this brief at Wave 1 close as a 4th
  sibling because the GCP infra + writer extension scope is disjoint from
  the corpus-ETL siblings — different files, different services, no path
  collision. Documented as protocol amendment in PROJECT_KARN_PROTOCOL.md
  v1.2 (Wave 2 = 4 parallel; non-recurring exception).

  Stream-A siblings own:
    W2-R1 → migration 028 + msr_signals + msr_extractor.py + msr_sql.ts
    W2-R2 → migration 029 + chart_facts_extractor.py + chart_facts categories
    W2-R3 → migration 030 + l25_cgm_edges + cgm_extractor.py
  This brief (Stream E) owns:
    GCP BigQuery dataset + table (no Cloud SQL migration)
    GCS bucket + lifecycle policy
    platform/src/lib/audit/bigquery_writer.ts (NEW)
    platform/src/lib/audit/gcs_writer.ts (NEW)
    platform/src/app/api/chat/consume/route.ts (extend onFinish — minor)
    Backfill script
    Trace UI panels (deferred to optional §3.13 — out-of-scope by default)
estimated_time: 1–1.5 days single Claude Code session

scope_summary: |
  Stand up the per-query archive on Google Cloud — BigQuery as the primary
  analytical store, GCS as the immutable backup layer — and wire the writers
  so every Consume-tab query lands one row in BigQuery + one JSONL object in
  GCS, non-blocking, in onFinish.

  The archive captures EVERYTHING currently logged (audit_events 13 cols,
  query_plans 24 cols, query_trace_steps per-step 12 cols × N steps) PLUS
  the response_text (currently not persisted anywhere) PLUS prediction
  metadata when present (Learning Layer substrate). Single flat-mirror table
  in BigQuery per protocol §1 below; GCS holds raw JSONL for replay.

  This is the substrate the eval harness (W7-R1), provenance audit (W6-R3),
  and Learning Layer (M3+) all read from. Without it, eval scores against
  current behavior only — there's no historical signal.

  Cloud SQL audit_events + query_plans + query_trace_steps stay as-is for
  fast operational lookups (trace UI today, recent-history features later).
  Archive write is additive, non-blocking, failure-isolated — never breaks
  the Consume path.

may_touch:
  - platform/scripts/gcp/setup_bigquery_archive.sh                     # NEW — one-time GCP infra setup
  - platform/scripts/gcp/setup_gcs_archive_bucket.sh                   # NEW — one-time GCS bucket + lifecycle
  - platform/scripts/gcp/backfill_query_archive.ts                     # NEW — backfill historical rows
  - platform/src/lib/audit/bigquery_writer.ts                          # NEW
  - platform/src/lib/audit/gcs_writer.ts                               # NEW
  - platform/src/lib/audit/audit_writer.ts                             # extend exports + onFinish entry-point
  - platform/src/lib/audit/types.ts                                    # NEW or extend — QueryArchiveRecord type
  - platform/src/lib/audit/__tests__/bigquery_writer.test.ts           # NEW
  - platform/src/lib/audit/__tests__/gcs_writer.test.ts                # NEW
  - platform/src/lib/audit/__tests__/audit_writer.test.ts              # extend
  - platform/src/app/api/chat/consume/route.ts                         # add response_text capture + writeQueryArchive call in onFinish
  - platform/src/lib/config/feature_flags.ts                           # add MARSYS_FLAG_QUERY_ARCHIVE_ENABLED
  - platform/package.json                                              # add @google-cloud/bigquery + @google-cloud/storage deps
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_E_QUERY_ARCHIVE.md      # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_E_QUERY_ARCHIVE_VERIFICATION_<DATE>.txt  # CREATE
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                         # add §9 — Query Archive
  - 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md                           # bump v1.1 → v1.2 (Wave 2 expanded note)
  - 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md                        # append entry

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)                                         # UI/UX stream
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A1_MSR_ETL.md           # sibling W2-R1
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A2_CHART_FACTS_ETL.md   # sibling W2-R2
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_B1_CGM_FULL_EDGES.md    # sibling W2-R3
  - platform/migrations/**                                             # NO Cloud SQL migrations this brief
  - platform/python-sidecar/**                                         # backend off-limits
  - platform/src/components/**                                         # UI/UX scope (trace UI is OPTIONAL §3.13)
  - platform/src/app/**                                                # EXCEPT consume/route.ts (minimal extension)
  - platform/src/hooks/**                                              # UI/UX scope
  - platform/src/lib/retrieve/**                                       # not in scope
  - platform/src/lib/router/**                                         # not in scope
  - platform/src/lib/synthesis/**                                      # not in scope
  - platform/src/lib/bundle/**                                         # not in scope
  - 025_HOLISTIC_SYNTHESIS/**                                          # source-of-truth
  - 035_DISCOVERY_LAYER/**                                             # off-limits
  - GCP project IAM (do NOT modify; only verify service-account scopes)

acceptance_criteria:
  AC.1: |
    Pre-flight gate passes:
      - branch redesign/r0-foundation
      - gcloud ADC active
      - secret `amjis-db-password` accessible (NOT `amjis-app-db-password`)
      - GCP project = madhav-astrology
      - BigQuery API enabled (gcloud services list --enabled | grep bigquery)
      - Cloud Storage API enabled
      - The Cloud Run service account has bigquery.dataEditor + storage.objectCreator
        on the target dataset/bucket (verify; do NOT modify IAM if missing — HALT)
  AC.2: |
    BigQuery dataset created at `madhav-astrology.amjis_query_archive` (region: us-central1).
    Created via `platform/scripts/gcp/setup_bigquery_archive.sh` (idempotent).
    Description: "Per-query analytical archive — every Consume-tab query → one row".
  AC.3: |
    BigQuery table `madhav-astrology.amjis_query_archive.queries` created.
    Schema is the comprehensive flat-mirror per §1 below — every audit_events,
    query_plans, and aggregated query_trace_steps field present, plus response_text +
    prediction_metadata fields.
    Partitioned by DATE(_PARTITIONTIME) on `created_at` field, daily grain.
    Clustered by (query_class, user_id) for common filter patterns.
  AC.4: |
    GCS bucket created at `gs://madhav-astrology-amjis-query-archive` (region: us-central1,
    Standard storage class). Created via `setup_gcs_archive_bucket.sh` (idempotent).
    Lifecycle policy:
      - 30 days: Standard → Coldline
      - 365 days: Coldline → Archive
      - never delete (immutable audit trail)
    Versioning enabled.
    IAM: Cloud Run service account has roles/storage.objectCreator (write-only; can't read or delete).
  AC.5: |
    bigquery_writer.ts implemented with public function:
      writeQueryArchive(record: QueryArchiveRecord): Promise<void>
    - Uses @google-cloud/bigquery streaming insert
    - Failure-isolated: catches all errors, logs to console.warn, never throws
    - Honors MARSYS_FLAG_QUERY_ARCHIVE_ENABLED (no-op when false)
    - Backward compatible: missing fields default to NULL
    Tests: ≥10 cases covering happy path, partial fields, BigQuery API failure,
    feature flag disabled, all current metrics serialized correctly.
  AC.6: |
    gcs_writer.ts implemented with public function:
      writeQueryArchiveToGcs(record: QueryArchiveRecord): Promise<void>
    - Uses @google-cloud/storage; writes JSONL to gs://<bucket>/<YYYY-MM-DD>/<query_id>.json
    - Failure-isolated; non-blocking; honors feature flag
    Tests: ≥6 cases covering path generation, content shape, retry semantics, feature flag.
  AC.7: |
    QueryArchiveRecord type defined in audit/types.ts. Schema mirrors AC.3 BigQuery
    table column-for-column. Includes nested types for tool_bundles, trace_steps[],
    prediction_metadata.
  AC.8: |
    consume/route.ts onFinish extended:
      - Captures the assembled response text from the streaming output (the same
        string that was sent to the user — fork at the end of the LLM stream completion)
      - Builds QueryArchiveRecord by composing:
        * fields from the QueryPlan (writeQueryPlan input)
        * fields from AuditEventParams (writeAuditEvent input)
        * trace_steps[] aggregated by reading query_trace_steps for this query_id
        * response_text + response_token_count + response_assembled_at
        * prediction_metadata (if present in synthesis output)
      - Calls writeQueryArchive(record) AND writeQueryArchiveToGcs(record) — both
        non-blocking, both failure-isolated
      - These calls happen AFTER existing writeAuditEvent + writeQueryPlan
        (preserve W1-R3 invariant — never block the Consume response)
  AC.9: |
    Feature flag MARSYS_FLAG_QUERY_ARCHIVE_ENABLED added to feature_flags.ts.
    Default: TRUE (gate present for emergency disable; default-on in deployed).
  AC.10: |
    Backfill script `backfill_query_archive.ts` implemented:
      - Reads existing audit_events + query_plans + query_trace_steps from Cloud SQL
        (joined by query_id) for rows where created_at > NOW() - 90 DAYS
      - Composes QueryArchiveRecord per existing row
      - Writes to BigQuery (NOT GCS — backfill goes to BQ only; GCS is forward-only)
      - Skips rows already present in BigQuery (check by query_id)
      - Idempotent (safe to re-run)
      - Reports inserted / skipped / errored counts
    NOTE: response_text will be NULL for backfilled rows (not previously captured).
    This is expected and documented in the verification txt.
  AC.11: |
    Backfill executed against current Cloud SQL state. Captures all existing audit_events
    rows (≥5 from W1-R3 verification + any subsequent ones).
    Verification:
      bq query "SELECT COUNT(*) FROM amjis_query_archive.queries"
      ≥ existing audit_events rows count
  AC.12: |
    Tests pass at pre-existing baseline (no new failures relative to W1-R3 baseline 958/13
    + W2 sibling deltas if landed first). Unit test count grows by ≥16 (10 BQ + 6 GCS).
  AC.13: |
    Cloud Run revision rebuilt and serving 100% via cloud_build_submit.sh.
    Cloud Run env vars set:
      MARSYS_FLAG_QUERY_ARCHIVE_ENABLED=true
      BIGQUERY_DATASET=amjis_query_archive
      BIGQUERY_TABLE=queries
      GCS_ARCHIVE_BUCKET=madhav-astrology-amjis-query-archive
    Capture revision name to verification txt.
  AC.14: |
    Send 5 fresh queries through deployed Consume tab. Verification (in BigQuery):
      bq query "SELECT query_id, query_text, query_class,
                LENGTH(response_text) AS resp_chars,
                ARRAY_LENGTH(planets) AS n_planets,
                ARRAY_LENGTH(trace_steps) AS n_steps,
                latency_ms_total
                FROM amjis_query_archive.queries
                WHERE created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
                ORDER BY created_at DESC LIMIT 5"
    All 5 rows present. response_text non-NULL on all 5 (proves response_text capture works).
    trace_steps[] has length matching query_trace_steps for that query_id.
    Capture full output to verification txt.
  AC.15: |
    GCS verification:
      gsutil ls gs://madhav-astrology-amjis-query-archive/$(date +%Y-%m-%d)/ | wc -l
      ≥ 5 (one JSONL object per query in last 5 min)
      gsutil cat gs://madhav-astrology-amjis-query-archive/$(date +%Y-%m-%d)/<sample-query-id>.json | jq .
      → valid JSON; contains response_text, all metrics, trace_steps array.
  AC.16: |
    Negative-path verification: temporarily set MARSYS_FLAG_QUERY_ARCHIVE_ENABLED=false in
    a test query (or use a direct unit-test path), confirm:
      - Cloud SQL audit_events still gets a row (unaffected)
      - BigQuery gets NO new row
      - GCS gets NO new object
    Then restore flag to true. (This may be a unit test rather than live deployed.)
  AC.17: |
    Cost sanity check: BigQuery storage cost estimate for 5 rows < $0.001. Current
    daily query volume × estimated row size × 365 = annual storage projection
    documented in verification txt §5. Should be well under $5/year for first
    operating year given current query volume.
  AC.18: |
    Trace UI panels (OPTIONAL — defer to a follow-up brief unless time permits).
    See §3.13 for spec. If implemented:
      - Query Intent panel at top of trace showing classifier output
      - Query Summary panel at bottom showing tools_authorized vs tools_fired,
        per-tool counts, total latency
    If skipped, document the deferral in §3.13 of verification txt and add a
    "M2_E_TRACE_UI_PANELS" entry to deferred-briefs list.
  AC.19: |
    M1_M2_ACTIVATION_MATRIX.md gains §9 — Query Archive section showing:
      - BigQuery dataset/table state
      - GCS bucket state
      - Backfill row count
      - Live-write verification
      - Schema completeness check (all current metrics ✅)
  AC.20: |
    PROJECT_KARN_PROTOCOL.md bumped to v1.2 with note: "Wave 2 expanded to 4 parallel
    briefs at Wave 1 close — sidecar W2-R4 (M2_E_QUERY_ARCHIVE) added because GCP
    infra scope is disjoint from corpus-ETL siblings. Non-recurring exception."
    Wave plan §5 updated to show Wave 2 with 4 entries.
  AC.21: |
    git status shows ONLY:
      platform/scripts/gcp/setup_bigquery_archive.sh (new)
      platform/scripts/gcp/setup_gcs_archive_bucket.sh (new)
      platform/scripts/gcp/backfill_query_archive.ts (new)
      platform/src/lib/audit/bigquery_writer.ts (new)
      platform/src/lib/audit/gcs_writer.ts (new)
      platform/src/lib/audit/audit_writer.ts (modified — exports + onFinish helper)
      platform/src/lib/audit/types.ts (new or modified)
      platform/src/lib/audit/__tests__/bigquery_writer.test.ts (new)
      platform/src/lib/audit/__tests__/gcs_writer.test.ts (new)
      platform/src/lib/audit/__tests__/audit_writer.test.ts (modified — light)
      platform/src/app/api/chat/consume/route.ts (modified — onFinish extension)
      platform/src/lib/config/feature_flags.ts (modified — flag added)
      platform/package.json (modified — 2 new deps)
      platform/package-lock.json (auto-modified)
      00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_E_QUERY_ARCHIVE.md (status flip)
      00_ARCHITECTURE/BRIEFS/M2_E_QUERY_ARCHIVE_VERIFICATION_<DATE>.txt (new)
      00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md (modified — new §9)
      00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md (modified — v1.2 bump)
      00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md (modified — append entry)
    No other changes.
  AC.22: |
    This brief's frontmatter `status` flipped to COMPLETE. Closing summary appended
    to PROJECT_KARN_SESSION_LOG.md per protocol §3.1.

halt_conditions:
  - gcloud ADC missing OR `amjis-db-password` secret unreadable
  - BigQuery API not enabled (HALT and report — user must enable manually)
  - Cloud Storage API not enabled (HALT and report)
  - Cloud Run service account lacks bigquery.dataEditor or storage.objectCreator
    (HALT — IAM changes are out-of-scope per safety policy)
  - Branch is not redesign/r0-foundation
  - Wave 1 baseline tests not at 958/13 (account for Stream-A sibling deltas if landed)
  - BigQuery dataset creation fails (likely IAM or quota)
  - GCS bucket name conflict (someone else owns the global-namespace name)
  - Cloud Build failure
  - Live-deploy queries fail to populate BigQuery (writer broken)
  - response_text is NULL on all 5 live queries (capture point in onFinish wrong)
  - Cost projection >$50/year (likely schema bloat — investigate before deploy)
---

# CLAUDECODE_BRIEF — M2_E_QUERY_ARCHIVE (Wave 2, Stream E, Run 4 — sidecar)

## §1 — Comprehensive schema (the BigQuery `queries` table)

This is the load-bearing artifact. Every metric currently captured anywhere in the system MUST be present in this schema. Field origins are annotated.

```sql
-- BigQuery table: madhav-astrology.amjis_query_archive.queries
-- Partitioning: DAY on created_at
-- Clustering: query_class, user_id

CREATE TABLE `madhav-astrology.amjis_query_archive.queries` (
  -- ── Identity ──────────────────────────────────────────────────────────────
  query_id              STRING NOT NULL,                    -- from audit_events.query_id
  query_plan_id         STRING,                              -- from query_plans.query_plan_id
  conversation_id       STRING,                              -- from audit_events.conversation_id
  user_id               STRING,                              -- from audit_events.user_id
  chart_id              STRING,                              -- from audit_events.chart_id

  -- ── Query input ───────────────────────────────────────────────────────────
  query_text            STRING NOT NULL,                     -- from audit_events.query_text
  query_text_hash       STRING,                              -- sha256(query_text), for dedup detection

  -- ── Classifier output (every field from query_plans) ──────────────────────
  query_class           STRING,                              -- from query_plans.query_class
  domains               ARRAY<STRING>,                       -- from query_plans.domains[]
  planets               ARRAY<STRING>,                       -- from query_plans.planets[]
  houses                ARRAY<INT64>,                        -- from query_plans.houses[]
  forward_looking       BOOL,                                -- from query_plans.forward_looking
  audience_tier         STRING,                              -- from query_plans.audience_tier
  tools_authorized      ARRAY<STRING>,                       -- from query_plans.tools_authorized[]
  history_mode          STRING,                              -- from query_plans.history_mode
  panel_mode            BOOL,                                -- from query_plans.panel_mode
  expected_output_shape STRING,                              -- from query_plans.expected_output_shape
  graph_seed_hints      ARRAY<STRING>,                       -- from query_plans.graph_seed_hints[]
  graph_traversal_depth INT64,                               -- from query_plans.graph_traversal_depth
  edge_type_filter      ARRAY<STRING>,                       -- from query_plans.edge_type_filter[]
  vector_search_filter  STRING,                              -- from query_plans.vector_search_filter (jsonb → JSON string)
  dasha_context_required BOOL,                               -- from query_plans.dasha_context_required
  bundle_directives     STRING,                              -- from query_plans.bundle_directives (jsonb → JSON string)
  router_model_id       STRING,                              -- from query_plans.router_model_id
  router_confidence     FLOAT64,                             -- from query_plans.router_confidence
  manifest_fingerprint  STRING,                              -- from query_plans.manifest_fingerprint
  schema_version        STRING,                              -- from query_plans.schema_version

  -- ── Audit / execution summary (from audit_events) ─────────────────────────
  tool_bundles          STRING,                              -- from audit_events.tool_bundles (jsonb → JSON string)
  -- denormalized per-tool counts for cheap analytical queries (extracted from tool_bundles):
  tools_fired           ARRAY<STRING>,                       -- which tools actually executed (subset of tools_authorized)
  msr_sql_count         INT64,
  msr_sql_latency_ms    INT64,
  vector_search_count   INT64,
  vector_search_latency_ms INT64,
  cgm_graph_walk_count  INT64,
  cgm_graph_walk_latency_ms INT64,
  pattern_register_count INT64,
  resonance_register_count INT64,
  contradiction_register_count INT64,
  cluster_atlas_count   INT64,
  temporal_count        INT64,
  manifest_query_count  INT64,
  query_msr_aggregate_count INT64,
  -- end-to-end:
  latency_ms_total      INT64,                               -- from audit_events.latency_ms
  audit_status          STRING,                              -- from audit_events.audit_status
  audit_warnings        STRING,                              -- from audit_events.audit_warnings (jsonb → JSON string)

  -- ── Per-step trace (from query_trace_steps, aggregated) ───────────────────
  trace_steps ARRAY<STRUCT<
    step_seq        INT64,
    step_name       STRING,
    step_type       STRING,
    status          STRING,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    latency_ms      INT64,
    parallel_group  STRING,
    data_summary    STRING,                                  -- jsonb → JSON string
    payload_truncated STRING                                 -- jsonb → JSON string, truncated at 8KB
  >>,

  -- ── Response (NEW — not currently captured) ────────────────────────────────
  response_text         STRING,                              -- the synthesized output streamed to user
  response_token_count  INT64,                               -- approximate token count
  response_assembled_at TIMESTAMP,                           -- when streaming completed

  -- ── Prediction metadata (NEW — Learning Layer substrate) ──────────────────
  has_predictions       BOOL,
  prediction_metadata ARRAY<STRUCT<
    prediction_text   STRING,
    horizon           STRING,                                -- e.g., "2026-Q3", "next 6 months"
    confidence        FLOAT64,
    falsifier         STRING,                                -- the observable that would disconfirm
    domain            STRING,
    planets           ARRAY<STRING>
  >>,

  -- ── Bookkeeping ───────────────────────────────────────────────────────────
  archive_schema_version STRING NOT NULL,                    -- e.g., "1.0.0" — bump when schema evolves
  ingested_via          STRING NOT NULL,                     -- "live" | "backfill"
  created_at            TIMESTAMP NOT NULL,                  -- the original query timestamp
  archived_at           TIMESTAMP NOT NULL                   -- when this BQ row was inserted
)
PARTITION BY DATE(created_at)
CLUSTER BY query_class, user_id
OPTIONS (
  description = "Per-query analytical archive — one row per Consume-tab query. Mirrors audit_events + query_plans + aggregated query_trace_steps + adds response_text + prediction_metadata.",
  partition_expiration_days = 1825  -- 5 years; raise/lower based on retention policy
);
```

**Why these fields specifically — schema completeness audit:**

| Source table (Cloud SQL) | Cols | All present in BQ? |
|---|---|---|
| audit_events | 13 | ✅ all 13 (id is reborn as archive_id internally; query_id is canonical) |
| query_plans | 24 | ✅ all 24 |
| query_trace_steps | 12 (per row) | ✅ aggregated as ARRAY<STRUCT> trace_steps |
| (new) response capture | 3 | ✅ response_text, response_token_count, response_assembled_at |
| (new) prediction substrate | 1 ARRAY | ✅ prediction_metadata for Learning Layer |
| (new) bookkeeping | 3 | ✅ archive_schema_version, ingested_via, archived_at |

Total: ~60 top-level fields. JSON blobs (vector_search_filter, bundle_directives, tool_bundles, audit_warnings, payload_truncated) preserved as STRING-encoded JSON, queryable via `JSON_EXTRACT_*` in BigQuery.

## §2 — Why this session

W1-R3 landed `audit_events` and `query_plans` in Cloud SQL. Those are operational tables — fast lookups, last-90-days TTL, drives the trace UI. They're not a long-term archive: cost grows with size, no analytical query story beyond `WHERE`, response_text isn't captured.

The per-query archive on BigQuery solves three things at once:

1. **Eval harness substrate (W7-R1).** The eval harness needs hundreds of historical queries with full input + classifier plan + tool firings + response to compute precision/recall. Without an archive, every eval run synthetic-generates queries, scoring against current behavior, missing drift. With the archive, we score against three months of real queries.

2. **Learning Layer substrate (M3+).** MACRO_PLAN §Cross-cutting workstreams mandates prospective prediction logging — every time-indexed prediction with horizon + confidence + falsifier captured BEFORE the outcome is observed. The `prediction_metadata` array in this schema IS that substrate.

3. **Native's offline analysis loop.** BigQuery → Looker Studio dashboards on tool-firing rates, latency distributions, classifier confidence by query class, retrieval coverage. The "where do we improve next?" question becomes one SQL query instead of an evening of psql probing.

**Not in scope:**
- Modifying existing audit_writer behavior (additive only).
- Cloud SQL schema changes (no new migration).
- Trace UI panels (deferred — see §3.13 OPTIONAL).
- IAM modifications (HALT if perms missing; user fixes manually).

## §3 — Implementation steps

### §3.1 — Pre-flight diagnostics

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
test "$(git branch --show-current)" = "redesign/r0-foundation" || HALT "wrong branch"

# gcloud auth
gcloud auth application-default print-access-token > /dev/null 2>&1 || HALT "ADC missing"
gcloud config get-value project | grep -q madhav-astrology || HALT "wrong GCP project"

# secret name (W1-R1 finding)
PGPASSWORD=$(gcloud secrets versions access latest --secret="amjis-db-password" --project=madhav-astrology) || HALT "secret unavailable"

# APIs enabled
gcloud services list --enabled --project=madhav-astrology --format="value(config.name)" | grep -q bigquery.googleapis.com || HALT "BigQuery API not enabled — run: gcloud services enable bigquery.googleapis.com"
gcloud services list --enabled --project=madhav-astrology --format="value(config.name)" | grep -q storage.googleapis.com || HALT "Storage API not enabled — run: gcloud services enable storage.googleapis.com"

# Cloud Run service account perms
SA=$(gcloud run services describe amjis-web --region=us-central1 --format="value(spec.template.spec.serviceAccountName)")
gcloud projects get-iam-policy madhav-astrology --flatten="bindings[].members" --filter="bindings.members:${SA}" --format="value(bindings.role)" | tee /tmp/sa_roles
grep -qE 'bigquery\.dataEditor|bigquery\.user' /tmp/sa_roles || HALT "service account lacks BigQuery write perms — user must grant: gcloud projects add-iam-policy-binding madhav-astrology --member=serviceAccount:${SA} --role=roles/bigquery.dataEditor"
grep -qE 'storage\.objectCreator|storage\.objectAdmin' /tmp/sa_roles || HALT "service account lacks GCS write perms"

# tests baseline
cd platform && npm test 2>&1 | tail -5
# Expected baseline (account for any sibling W2 deltas if landed first)
```

### §3.2 — GCP infra: BigQuery dataset + table

Create `platform/scripts/gcp/setup_bigquery_archive.sh`:

```bash
#!/usr/bin/env bash
# Idempotent BigQuery archive setup.
# Usage: bash platform/scripts/gcp/setup_bigquery_archive.sh

set -euo pipefail
PROJECT="${GCP_PROJECT:-madhav-astrology}"
DATASET="${BIGQUERY_DATASET:-amjis_query_archive}"
TABLE="${BIGQUERY_TABLE:-queries}"
LOCATION="${BIGQUERY_LOCATION:-US}"  # multi-region for redundancy

# 1. Create dataset (idempotent)
bq --location=${LOCATION} mk --dataset \
  --description="Per-query analytical archive — every Consume-tab query → one row" \
  ${PROJECT}:${DATASET} 2>/dev/null || echo "dataset already exists"

# 2. Create table from schema file (idempotent — uses --force)
bq mk \
  --table \
  --time_partitioning_field=created_at \
  --time_partitioning_type=DAY \
  --clustering_fields=query_class,user_id \
  --description="Per-query analytical archive (M2_E_QUERY_ARCHIVE)" \
  ${PROJECT}:${DATASET}.${TABLE} \
  platform/scripts/gcp/query_archive_schema.json \
  2>/dev/null || {
    echo "table exists — applying schema update if needed"
    bq update ${PROJECT}:${DATASET}.${TABLE} platform/scripts/gcp/query_archive_schema.json
  }

# 3. Verify
bq show ${PROJECT}:${DATASET}.${TABLE}
echo "✅ BigQuery archive ready"
```

Companion schema JSON at `platform/scripts/gcp/query_archive_schema.json` — full schema from §1 in BigQuery JSON format.

### §3.3 — GCP infra: GCS bucket

Create `platform/scripts/gcp/setup_gcs_archive_bucket.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
BUCKET="${GCS_ARCHIVE_BUCKET:-madhav-astrology-amjis-query-archive}"
PROJECT="${GCP_PROJECT:-madhav-astrology}"
LOCATION="${GCS_LOCATION:-us-central1}"

# 1. Create bucket (idempotent)
gcloud storage buckets create gs://${BUCKET} \
  --project=${PROJECT} \
  --location=${LOCATION} \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access 2>/dev/null || echo "bucket exists"

# 2. Enable versioning
gcloud storage buckets update gs://${BUCKET} --versioning

# 3. Lifecycle policy
cat > /tmp/lifecycle.json <<EOF
{
  "rule": [
    {"action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
     "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}},
    {"action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
     "condition": {"age": 365, "matchesStorageClass": ["COLDLINE"]}}
  ]
}
EOF
gcloud storage buckets update gs://${BUCKET} --lifecycle-file=/tmp/lifecycle.json

echo "✅ GCS archive bucket ready"
```

### §3.4 — Add npm dependencies

```bash
cd platform
npm install @google-cloud/bigquery @google-cloud/storage
```

Both libraries auto-detect ADC; no explicit credential setup needed in code.

### §3.5 — Implement bigquery_writer.ts

Pattern (sketch):

```typescript
// platform/src/lib/audit/bigquery_writer.ts
import { BigQuery } from '@google-cloud/bigquery';
import { isFlagEnabled } from '@/lib/config/feature_flags';
import type { QueryArchiveRecord } from './types';

const bq = new BigQuery();
const DATASET = process.env.BIGQUERY_DATASET ?? 'amjis_query_archive';
const TABLE = process.env.BIGQUERY_TABLE ?? 'queries';

export async function writeQueryArchive(record: QueryArchiveRecord): Promise<void> {
  if (!isFlagEnabled('QUERY_ARCHIVE_ENABLED')) return;

  try {
    await bq.dataset(DATASET).table(TABLE).insert([record], {
      skipInvalidRows: false,
      ignoreUnknownValues: false,
    });
  } catch (err) {
    // Non-blocking: log but never throw. Same isolation pattern as audit_writer.
    console.warn('[bigquery_writer] insert failed:', err instanceof Error ? err.message : err);
  }
}
```

Tests in `__tests__/bigquery_writer.test.ts`:
- happy path → BQ insert called with right shape
- feature flag disabled → no call made
- BQ API throws → no exception propagates
- partial fields → fields default to NULL correctly
- all 60 schema fields serialized correctly (one test per field group)
- response_text > 100KB → truncates payload_truncated, full response_text preserved
- prediction_metadata array → serialized correctly
- trace_steps with 30 entries → serialized correctly
- ingested_via='live' vs 'backfill' set correctly
- archive_schema_version baked in

### §3.6 — Implement gcs_writer.ts

```typescript
// platform/src/lib/audit/gcs_writer.ts
import { Storage } from '@google-cloud/storage';
import { isFlagEnabled } from '@/lib/config/feature_flags';
import type { QueryArchiveRecord } from './types';

const storage = new Storage();
const BUCKET = process.env.GCS_ARCHIVE_BUCKET ?? 'madhav-astrology-amjis-query-archive';

export async function writeQueryArchiveToGcs(record: QueryArchiveRecord): Promise<void> {
  if (!isFlagEnabled('QUERY_ARCHIVE_ENABLED')) return;

  const date = new Date(record.created_at).toISOString().slice(0, 10); // YYYY-MM-DD
  const path = `${date}/${record.query_id}.json`;

  try {
    await storage.bucket(BUCKET).file(path).save(JSON.stringify(record, null, 2), {
      contentType: 'application/json',
      metadata: { metadata: { archive_schema_version: record.archive_schema_version }},
    });
  } catch (err) {
    console.warn('[gcs_writer] save failed:', err instanceof Error ? err.message : err);
  }
}
```

Tests in `__tests__/gcs_writer.test.ts`:
- happy path → file saved at right path
- path uses YYYY-MM-DD/queryId.json shape
- feature flag disabled → no call
- GCS API failure → no exception
- metadata includes schema version
- content is valid JSON

### §3.7 — Define QueryArchiveRecord type

In `platform/src/lib/audit/types.ts` (create if missing, extend if exists):

```typescript
export interface QueryArchiveRecord {
  // Identity
  query_id: string;
  query_plan_id?: string;
  conversation_id?: string;
  user_id?: string;
  chart_id?: string;

  // Query input
  query_text: string;
  query_text_hash?: string;

  // Classifier output (24 fields from query_plans)
  query_class?: string;
  domains?: string[];
  planets?: string[];
  houses?: number[];
  forward_looking?: boolean;
  audience_tier?: string;
  tools_authorized?: string[];
  // ... all 24 fields ...

  // Audit / execution
  tool_bundles?: string;  // JSON-stringified
  tools_fired?: string[];
  msr_sql_count?: number;
  msr_sql_latency_ms?: number;
  // ... all denormalized counters ...
  latency_ms_total?: number;
  audit_status?: string;
  audit_warnings?: string;

  // Per-step trace
  trace_steps?: TraceStep[];

  // Response
  response_text?: string;
  response_token_count?: number;
  response_assembled_at?: string;  // ISO timestamp

  // Predictions
  has_predictions?: boolean;
  prediction_metadata?: PredictionMetadata[];

  // Bookkeeping
  archive_schema_version: string;
  ingested_via: 'live' | 'backfill';
  created_at: string;     // ISO timestamp
  archived_at: string;    // ISO timestamp
}

export interface TraceStep { /* ... */ }
export interface PredictionMetadata { /* ... */ }
```

### §3.8 — Wire into consume/route.ts onFinish

The existing onFinish (per W1-R3) already has access to:
- the QueryPlan (for writeQueryPlan)
- the AuditEventParams (for writeAuditEvent)
- the response text (assembled from the streaming output)

Add a third call site after the existing two:

```typescript
// platform/src/app/api/chat/consume/route.ts (in onFinish)
import { writeAuditEvent, writeQueryPlan } from '@/lib/audit/audit_writer';
import { writeQueryArchive } from '@/lib/audit/bigquery_writer';
import { writeQueryArchiveToGcs } from '@/lib/audit/gcs_writer';
import { fetchTraceStepsForQuery } from '@/lib/audit/audit_writer'; // helper to load query_trace_steps for archive composition

// ... existing onFinish body ...

await Promise.all([
  writeAuditEvent(auditParams),     // existing
  writeQueryPlan(queryPlan),         // existing
]);

// NEW — fork: compose archive record AFTER the above lands so trace_steps is complete
const traceSteps = await fetchTraceStepsForQuery(queryPlan.query_id);
const record: QueryArchiveRecord = {
  ...mapPlanToArchive(queryPlan),
  ...mapAuditToArchive(auditParams),
  trace_steps: traceSteps,
  response_text: assembledText,
  response_token_count: estimateTokens(assembledText),
  response_assembled_at: new Date().toISOString(),
  has_predictions: detectPredictions(assembledText),
  prediction_metadata: extractPredictions(assembledText),
  archive_schema_version: '1.0.0',
  ingested_via: 'live',
  created_at: queryPlan.created_at,
  archived_at: new Date().toISOString(),
};

// Both calls non-blocking, fire-and-forget. Fail isolation already inside the writers.
void writeQueryArchive(record);
void writeQueryArchiveToGcs(record);
```

**Critical:** `void` prefix means we don't await — the response has already been streamed to the user before this fires. Archive writes are pure background.

### §3.9 — Feature flag

Add to `platform/src/lib/config/feature_flags.ts`:

```typescript
QUERY_ARCHIVE_ENABLED: parseBool(process.env.MARSYS_FLAG_QUERY_ARCHIVE_ENABLED, true),
```

Default `true`. Provides emergency disable without redeploy.

### §3.10 — Backfill script

`platform/scripts/gcp/backfill_query_archive.ts`:

```typescript
// Usage: npx ts-node platform/scripts/gcp/backfill_query_archive.ts [--days 90]
// Reads existing audit_events JOIN query_plans, composes archive records, writes to BQ.
// Idempotent: skips query_ids already present.
//
// NOTE: response_text will be NULL for backfilled rows (not captured before this brief).
//       This is expected.

import { Pool } from 'pg';
import { writeQueryArchive } from '../../src/lib/audit/bigquery_writer';
// ... composer logic ...

async function main() {
  const days = parseArg('--days') ?? 90;
  const rows = await fetchHistoricalQueries(days);
  const existing = await fetchExistingArchiveQueryIds();

  let inserted = 0, skipped = 0, errored = 0;
  for (const row of rows) {
    if (existing.has(row.query_id)) { skipped++; continue; }
    try {
      const record = composeArchiveRecord(row, 'backfill');
      await writeQueryArchive(record);
      inserted++;
    } catch (err) {
      errored++;
      console.warn(`backfill failed for ${row.query_id}:`, err);
    }
  }
  console.log(`backfill complete: inserted=${inserted}, skipped=${skipped}, errored=${errored}`);
}
```

Run after AC.5 + AC.6 are deployed:
```bash
cd platform
npx ts-node scripts/gcp/backfill_query_archive.ts --days 90
```

### §3.11 — Build, test, deploy

```bash
cd platform
npm test 2>&1 | tail -10
# AC.12 — confirm baseline + 16 new tests

# Set Cloud Run env vars (one-time):
gcloud run services update amjis-web --region=us-central1 \
  --update-env-vars=MARSYS_FLAG_QUERY_ARCHIVE_ENABLED=true,BIGQUERY_DATASET=amjis_query_archive,BIGQUERY_TABLE=queries,GCS_ARCHIVE_BUCKET=madhav-astrology-amjis-query-archive

bash platform/scripts/cloud_build_submit.sh
# AC.13 — capture revision name
```

### §3.12 — Live-deploy verification (AC.14 + AC.15)

Send 5 fresh queries through Consume tab. Wait 30s for streaming inserts to land. Then:

```bash
# BigQuery check
bq query --use_legacy_sql=false "
  SELECT query_id, query_text, query_class,
         LENGTH(response_text) AS resp_chars,
         ARRAY_LENGTH(planets) AS n_planets,
         ARRAY_LENGTH(trace_steps) AS n_steps,
         latency_ms_total,
         ingested_via,
         archive_schema_version
  FROM \`madhav-astrology.amjis_query_archive.queries\`
  WHERE created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
  ORDER BY created_at DESC
  LIMIT 10
"

# GCS check
gsutil ls gs://madhav-astrology-amjis-query-archive/$(date +%Y-%m-%d)/ | wc -l
gsutil cat gs://madhav-astrology-amjis-query-archive/$(date +%Y-%m-%d)/$(gsutil ls gs://madhav-astrology-amjis-query-archive/$(date +%Y-%m-%d)/ | head -1 | xargs basename) | jq '.query_text, .query_class, .response_text | length'
```

Capture all output to verification txt.

### §3.13 — OPTIONAL: Trace UI panels

If time remains after AC.1–AC.17 pass:
- Add a `<QueryIntentPanel queryId={...}>` component at top of trace, fetches query_plans row, shows query_class / planets / houses / graph_seed_hints / vector_search_filter / router_confidence in a clean info card.
- Add a `<QuerySummaryPanel queryId={...}>` component at bottom of trace, fetches audit_events row, shows tools_authorized vs tools_fired (gap highlighted), per-tool counts + latency, total latency.

If skipped — and the time-budget likely says skip — write a 5-line note in verification txt §6 deferring to a follow-up brief named `M2_E_TRACE_UI_PANELS` for the portal redesign workstream to pick up. Add to deferred-briefs section in PROJECT_KARN_SESSION_LOG.md.

### §3.14 — Update activation matrix + protocol + log

`M1_M2_ACTIVATION_MATRIX.md` — add §9:

```markdown
## §9 — Query Archive

| Layer | State |
|---|---|
| BigQuery dataset | madhav-astrology.amjis_query_archive ✅ |
| BigQuery table | queries (~60 fields, partitioned by date, clustered) ✅ |
| GCS bucket | gs://madhav-astrology-amjis-query-archive ✅ (lifecycle: Standard→Coldline→Archive) |
| Live writer | bigquery_writer.ts + gcs_writer.ts in onFinish ✅ |
| Backfill | last 90 days populated ✅ |
| Schema completeness | all audit_events + query_plans + query_trace_steps fields mirrored ✅ |
| Response capture | response_text + response_token_count + response_assembled_at ✅ |
| Prediction substrate | prediction_metadata array (Learning Layer wiring) ✅ |
```

`PROJECT_KARN_PROTOCOL.md` — bump v1.1 → v1.2, add changelog entry:

```yaml
- 1.2 (2026-04-30): Wave 2 expanded to 4 parallel briefs at Wave 1 close
  per native request — sidecar W2-R4 (M2_E_QUERY_ARCHIVE) added. Storage
  scope (GCP infra + writers) is disjoint from corpus-ETL siblings; no
  path collision. Non-recurring exception; Wave 2 = 4 parallel.
```

§5 wave plan: update Wave 2 row to show 4 entries.

`PROJECT_KARN_SESSION_LOG.md` — append per-brief entry per protocol §3.1.

### §3.15 — Status flip

- Flip `status: PENDING` → `status: COMPLETE` in this brief's frontmatter.

## §4 — Closing summary template

```
KARN-W2-R4-QUERY-ARCHIVE closed.
- BigQuery: madhav-astrology.amjis_query_archive.queries created (~60 fields, partitioned + clustered)
- GCS: gs://madhav-astrology-amjis-query-archive (lifecycle Std→Coldline→Archive)
- writers: bigquery_writer.ts + gcs_writer.ts (failure-isolated, feature-gated)
- consume/route.ts onFinish extended: response_text + trace_steps + prediction_metadata
- backfill: N rows imported from last 90 days of audit_events (response_text NULL for backfill)
- live verification: 5 fresh queries → BQ rows + GCS objects, response_text non-null
- tests: pre N/13 → post N+16/13 (no new failures)
- Cloud Run revision: amjis-web-XXXXX-YYY
- env vars set: BIGQUERY_DATASET, BIGQUERY_TABLE, GCS_ARCHIVE_BUCKET, MARSYS_FLAG_QUERY_ARCHIVE_ENABLED
- cost projection: ~$1–5/year storage at current volume
- M1_M2_ACTIVATION_MATRIX.md §9 added
- PROJECT_KARN_PROTOCOL.md bumped v1.1 → v1.2 (Wave 2 = 4)
- trace UI panels: deferred to M2_E_TRACE_UI_PANELS (portal redesign workstream)
- next pointer: archive is write-live; W7-R1 eval harness reads from BigQuery
```

## §5 — Halt-and-report checklist

- Pre-flight failure (any of §3.1)
- BigQuery API or Cloud Storage API not enabled
- Service account missing required IAM roles (user fixes manually; do NOT modify IAM)
- BigQuery dataset/table creation fails
- GCS bucket name conflict
- Cloud Build failure
- Live deploy: response_text NULL on all 5 verification queries (capture point wrong)
- Cost projection >$50/year (likely schema bloat — investigate)
- Tests baseline drift > 2 failures

---

*End of CLAUDECODE_BRIEF_M2_E_QUERY_ARCHIVE. Predecessor: KARN-W1-R3-OBSERVABILITY. Wave 2 sidecar.*
