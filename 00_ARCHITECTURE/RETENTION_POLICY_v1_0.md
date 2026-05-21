---
artifact: RETENTION_POLICY_v1_0
title: "BHISMA Wave 2 — Monitoring Data Retention & Archival Policy"
canonical_id: RETENTION_POLICY
version: 1.0
status: CURRENT
created_date: 2026-05-03
session_id: BHISMA-W2-S-B
scope: "Platform monitoring tables: llm_call_log, query_plan_log, tool_execution_log, context_assembly_log"
governs:
  - 00_ARCHITECTURE/BHISMA_WAVE2_PLAN_v1_1.md (§3 Stream SCHEMA — SCHEMA-6)
  - platform migrations 032–036 (PENDING — Session BHISMA S-C)
---

# Retention & Archival Policy — BHISMA Wave 2 Monitoring Tables

## §0 Purpose

The four BHISMA Wave 2 monitoring tables capture every LLM call, every query plan, every tool execution, and every context-assembly event the platform performs. Without bounded retention, these tables grow unboundedly; without archival, audit-grade history is irrecoverable once rows are deleted. This policy specifies the per-tier retention windows, the GCS archive layout, the cleanup-job cadence, and the exceptions that override deletion.

The hot/warm/cold tiering balances **query-latency** (hot is query-live in Postgres), **storage cost** (warm/cold compress to GCS), and **audit recoverability** (cold is preserved indefinitely as JSONL with per-day granularity).

## §1 Retention Tiers

| Tier | Window | Storage | Action |
|------|--------|---------|--------|
| Hot  | 0–90 days     | Cloud SQL (Postgres) | Query-live; full indexes available |
| Warm | 91–365 days   | GCS (JSONL, gzip)    | Accessible via batch job; not query-live |
| Cold | >365 days     | GCS (JSONL, Zstandard) | Audit trail only; access requires manual restore |

Tier transitions are atomic: a row leaves hot only after its archive write to GCS confirms (HTTP 200 from `gsutil cp`). Warm→cold transition is a re-encode pass that runs monthly.

## §2 Per-Table Policy

All four tables share the same hot-window length (90 days) and the same archive structure. Retention reasons differ — recorded below per table to make the cost-vs-audit tradeoff explicit per surface.

### 2.1 `llm_call_log`
- Hot window: 90 days
- Reason for retention: cost accountability (per-provider per-model spend), model comparison (latency + quality vs price), R1 reasoning-token auditing (DeepSeek-R1 / o1 reasoning costs)
- Archive format: JSONL per day, gzip compressed
- GCS path: `gs://[BUCKET]/retention/llm_call_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation
- Sensitive columns: `prompt_full_text`, `response_full_text` — redacted per `LLM_CALL_LOG_REDACTION_POLICY` (PENDING; out of scope for S-B)

### 2.2 `query_plan_log`
- Hot window: 90 days
- Reason for retention: planner quality monitoring (tool_recall / tool_precision per query class), A/B comparison data source (LLM-first vs deterministic baseline), Lever 2 calibration over time
- Archive format: JSONL per day, gzip compressed
- GCS path: `gs://[BUCKET]/retention/query_plan_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

### 2.3 `tool_execution_log`
- Hot window: 90 days
- Reason for retention: tool zero-row tracking (which tools return empty results and why), B.3 grounding audits (which L1 fact_ids were consumed per tool call)
- Archive format: JSONL per day, gzip compressed
- GCS path: `gs://[BUCKET]/retention/tool_execution_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

### 2.4 `context_assembly_log`
- Hot window: 90 days
- Reason for retention: B.3 compliance audit (every assembled context maps to its source fact_ids), citation validation audit trail (every citation in a synthesizer response traces back to assembled context)
- Archive format: JSONL per day, gzip compressed
- GCS path: `gs://[BUCKET]/retention/context_assembly_log/YYYY/MM/DD.jsonl.gz`
- Delete-after-archive: 90 days post-creation

## §3 Cleanup Jobs

Cleanup runs daily via scheduled Cloud Run Job (preferred) or `pg_cron` (fallback if Cloud SQL `cloudsql.enable_pg_cron=on` is enabled). Both jobs share a strict ordering: archive → verify → delete. No row leaves Postgres without a confirmed GCS write.

### 3.1 Archive job (daily, 02:00 UTC)

```sql
-- Pseudocode: actual implementation uses COPY ... TO PROGRAM 'gsutil cp - ...'
-- One archive query per table; runs in a single transaction per table.
COPY (
  SELECT * FROM llm_call_log
  WHERE created_at < NOW() - INTERVAL '88 days'
    AND created_at >= NOW() - INTERVAL '89 days'
)
TO PROGRAM
  'gsutil -q cp - gs://[BUCKET]/retention/llm_call_log/$(date -u +%Y/%m/%d -d "89 days ago").jsonl.gz'
WITH (FORMAT csv, HEADER true);

-- Repeat for query_plan_log, tool_execution_log, context_assembly_log.
```

The 88–89-day window (rather than `created_at < NOW() - INTERVAL '90 days'`) gives a 1–2-day buffer between archive and delete, so a row is in GCS for at least 24 hours before being eligible for deletion.

### 3.2 Delete job (daily, 03:00 UTC, runs after archive)

```sql
DELETE FROM llm_call_log         WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM query_plan_log       WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM tool_execution_log   WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM context_assembly_log WHERE created_at < NOW() - INTERVAL '90 days';
```

Delete is gated on archive success: the Cloud Run Job orchestrator records archive completion to a state file in GCS (`gs://[BUCKET]/retention/_state/YYYY-MM-DD.archive.done`); the delete step refuses to run if the state file for the corresponding day is missing.

### 3.3 Warm→cold re-encode (monthly, 1st of month, 04:00 UTC)

Re-encodes day-files older than 365 days from gzip JSONL to Zstandard-compressed JSONL (~3× smaller for log payloads). Original gzip files are deleted only after Zstd file checksum verifies.

## §4 Exceptions

These exceptions bypass deletion. Each is opt-in and audit-logged.

- **Super-admin override.** A row tagged `retain_indefinitely=true` (column added in migration 032) is excluded from both delete jobs. Use cases: golden-set calibration rows, baseline measurements, post-incident forensics. Setting the flag requires super-admin role per `feature_flags.ts` access control (out of S-B scope).
- **Incident hold.** During active incidents, deletion is suspended platform-wide by setting the env flag `MARSYS_RETENTION_HOLD=true` on the cleanup Cloud Run Job. Archive continues; delete pauses until the flag is cleared. Hold state is surfaced in the Observatory super-admin UI (PENDING).
- **Legal hold.** A column `legal_hold BOOLEAN DEFAULT FALSE` (added per future migration when first needed) overrides delete. Legal team flags rows by query_id; the row remains in hot tier indefinitely. This is intentionally a different mechanism from `retain_indefinitely` — legal holds carry a chain-of-custody record (separate `legal_hold_audit` table; PENDING; not in S-C scope).

## §5 Implementation Status

| Component | Status | Owner / Next Session |
|-----------|--------|----------------------|
| Cloud SQL hot-tier tables (`llm_call_log`, `query_plan_log`, `tool_execution_log`, `context_assembly_log`) | PENDING | Session BHISMA S-C — migrations 032–036 |
| `retain_indefinitely` column on all 4 tables | PENDING | Session BHISMA S-C — fold into the table-creation migrations |
| GCS bucket for retention archive | PENDING — `[BUCKET]` placeholder above | Native decision: reuse `madhav-marsys-build-artifacts` or provision dedicated `madhav-marsys-monitoring-archive` |
| Archive job (Cloud Run Job, daily 02:00 UTC) | PENDING | Post-S-C session — author after migrations apply and rows accumulate |
| Delete job (Cloud Run Job, daily 03:00 UTC) | PENDING | Post-S-C session — must reference archive-done state file |
| Warm→cold monthly re-encode | PENDING | Defer — not load-bearing until 2027-05 (1 year post-launch) |
| Monitoring alert (archive failure → PagerDuty / native email) | PENDING | Post-S-C session — wire to existing alerting from Phase 14 |
| `LLM_CALL_LOG_REDACTION_POLICY` companion artifact | PENDING | Separate session — sensitive-column redaction is a distinct policy concern |
| `legal_hold_audit` table | DEFERRED | Author when first legal hold is required |

## §6 Acceptance

Policy document complete (this artifact). Implementation items above tracked to Session BHISMA S-C (migration apply) and post-S-C sessions (cleanup jobs, monitoring, redaction).

The four monitoring tables do not yet exist in Cloud SQL — until S-C closes, this policy document is forward-looking governance, not active enforcement. From S-C close onward, this document is the single source of truth for retention behavior; any deviation in the cleanup job implementation must round-trip through a version bump here.

## §7 Changelog

- **v1.0 (2026-05-03, BHISMA-W2-S-B)** — initial publication. Specifies hot 90d / warm 91–365d / cold >365d tiering, per-table archive paths, daily archive + delete cadence with archive-done gating, exception mechanism (super-admin / incident hold / legal hold), implementation status table.
