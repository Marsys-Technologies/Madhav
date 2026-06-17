---
brief_id: EXEC_BRIEF_PHASE_4
version: 1.0
status: AUTHORED
authored_by: Cowork (Opus)
authored_at: 2026-04-27
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_4_v1_0.md and execute it."
phase: 4
phase_name: Audit & Persistence
risk_classification: MEDIUM
parallelizable_with: [EXEC_BRIEF_PHASE_5_v1_0.md, EXEC_BRIEF_PHASE_9_HOTFIX_v1_0.md, M2/B.5 work]
depends_on: [EXEC_BRIEF_PHASE_3_v1_0.md (COMPLETE)]
estimated_streams: 4
---

# EXEC_BRIEF — Phase 4 — Audit & Persistence

## Mission

Persist every query's full execution trace to durable storage so that (a) the Discipline stage of the pipeline has a record to reference; (b) calibration in Phase 10 has a fact base to learn from; (c) the audit-view UI in Phase 8 has rows to render; (d) the cross-cutting **prospective prediction logging** workstream from `CLAUDE.md §E` has its scaffolded home.

Phase 3 emits structured audit event hooks via Telemetry. Phase 4 consumes those hooks and writes them to two new tables: `audit_log` (every query) and `prediction_ledger` (time-indexed predictions only).

## Scope (`may_touch` / `must_not_touch`)

**`may_touch`:**
- `platform/supabase/migrations/011_audit_log.sql` (new)
- `platform/supabase/migrations/012_prediction_ledger.sql` (new)
- `platform/src/lib/audit/**` (new — writer module + types)
- `platform/src/lib/prediction/**` (new — prediction ledger writer)
- `platform/src/lib/synthesis/orchestrator.ts` (extend audit event emission only — no behavior change)
- `platform/src/app/api/consume/route.ts` (wire audit consumer hook only — no flag-OFF behavior change)
- `platform/scripts/audit/replay.ts` (new — CLI for inspecting audit history)
- `platform/src/lib/audit/__tests__/**`, `platform/src/lib/prediction/__tests__/**`
- `package.json` scripts: add `audit:replay`, `audit:smoke`

**`must_not_touch`:**
- `platform/python-sidecar/**` (sidecar untouched)
- `platform/src/lib/validators/**` (Phase 3 deliverable, frozen)
- `platform/src/lib/prompts/**` (Phase 3 deliverable, frozen)
- `platform/src/lib/disclosure/**` (Phase 3 deliverable, frozen)
- `platform/src/lib/router/**`, `platform/src/lib/bundle/**`, `platform/src/lib/retrieve/**` (Phase 2/9 deliverables, frozen)
- Any flag-OFF code path
- Any UI surface (that's Phase 5)
- Any LLM-checkpoint logic (that's Phase 6)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (manifest is governance, not Phase 4 territory)

## Sub-streams (4 total)

### Stream A — `audit_log` schema + writer
- Migration `011_audit_log.sql`: table with columns `id` (uuid pk), `query_id` (uuid, indexed), `created_at` (timestamptz), `query_text` (text), `query_class` (text — one of 8 classes), `bundle_keys` (jsonb — list of asset_ids consumed), `tools_called` (jsonb — array of `{tool, params_hash, latency_ms, cached}`), `validators_run` (jsonb — array of `{validator_id, passed, message}`), `synthesis_model` (text), `synthesis_input_tokens` (int), `synthesis_output_tokens` (int), `disclosure_tier` (text), `final_output` (text), `audit_event_version` (int default 1).
- Index on `(query_id)` and `(created_at desc)`.
- Writer module `platform/src/lib/audit/writer.ts`: single function `writeAuditLog(event: AuditEvent): Promise<void>`. Idempotent on `query_id` (upsert; same query_id rewrites). Failure mode: log + emit Telemetry but never throw into the caller — audit-write must NOT crash the user's response path.
- Types in `platform/src/lib/audit/types.ts` mirroring the JSON shape.
- 12+ tests covering: write happy path; idempotent re-write; partial-event tolerance; failure-doesn't-throw guarantee.

### Stream B — `prediction_ledger` schema + writer
- Migration `012_prediction_ledger.sql`: table with columns `id` (uuid pk), `query_id` (uuid, indexed, references audit_log.query_id), `created_at` (timestamptz), `prediction_text` (text), `confidence` (numeric, 0-1), `horizon_start` (date), `horizon_end` (date), `falsifier` (text — what observation would refute it), `subject` (text — usually 'native:abhisek' for now but extensible), `outcome` (text nullable — populated post-hoc when reality checks in), `outcome_observed_at` (timestamptz nullable), `calibration_bucket` (text nullable — assigned by Phase 10 calibration loop).
- Index on `(query_id)`, `(horizon_start)`, `(subject, horizon_start)`.
- Writer module `platform/src/lib/prediction/writer.ts`: function `logPrediction(p: Prediction): Promise<string>` returns the new `id`. Strict input validation per `CLAUDE.md §E`: predictions must carry `confidence`, `horizon`, and `falsifier` BEFORE outcome is observed. Refuses to write if `outcome` is non-null at insert time (sacrosanct held-out rule).
- Types in `platform/src/lib/prediction/types.ts`.
- Reader helper `platform/src/lib/prediction/reader.ts`: `listOpenPredictions({subject, beforeHorizonEnd})` for Phase 10 to consume.
- 10+ tests including: valid write; reject write with outcome populated; horizon validation; reader filters.

### Stream C — Audit event consumer wiring
- Extend `synthesis/orchestrator.ts` to emit a richer `AuditEvent` payload (additive only — keep existing telemetry signature stable). Stream D of Phase 3 already emits a hook; Stream C of Phase 4 wires the consumer.
- New module `platform/src/lib/audit/consumer.ts`: subscribes to the synthesis-emit channel, transforms event → AuditLog row, calls Stream A's writer. If the synthesized output contains a time-indexed prediction (heuristic: contains a date range AND a confidence assertion), also calls Stream B's writer.
- Wire-up in `route.ts`: when flag is ON, attach consumer; when OFF, do not. Zero behavior change in flag-OFF path.
- Prediction extraction is intentionally heuristic in Phase 4 — Phase 6 (LLM Checkpoints) replaces it with a checkpoint-derived structured prediction object. Phase 4's heuristic is a placeholder, marked TODO with clear extension point.
- 8+ tests: end-to-end flag-ON synthesizer→audit row; prediction-detection heuristic happy path + miss case; flag-OFF asserts no DB write.

### Stream D — Audit replay/inspection helpers
- CLI `platform/scripts/audit/replay.ts`: usage `npm run audit:replay -- --query-id=<uuid>` or `--last=N`. Prints the full audit event in human-readable form. Used by native to inspect why a query went a particular direction.
- Smoke script `audit:smoke`: writes 5 fake audit events + 2 fake predictions, reads them back, prints diff. Verifies migration + writers end-to-end against live Cloud SQL in dev environment.
- 5+ tests on the formatter; smoke script is integration-tested manually.

## Critical constraints

- **Audit writes are best-effort, not blocking.** A DB outage must not crash the user's query response. Stream A guarantees this via try/catch + Telemetry.
- **Prospective prediction logging is sacrosanct** (per `CLAUDE.md §E` + Learning Layer rule #4). The writer refuses to insert a prediction with `outcome` already set — that would corrupt the held-out discipline.
- **Schema migrations are forward-only.** No DROP-and-recreate. If a migration fails halfway, the up.sql script must include rollback comments at the top describing recovery.
- **Phase 4 does NOT touch the flag-OFF code path.** All audit consumer wiring is gated on `NEW_QUERY_PIPELINE_ENABLED`. Flag OFF = no audit row written = behaviorally identical to today.
- **Audit event versioning.** `audit_event_version` column starts at 1. Phase 6 will introduce v2 (with checkpoint payloads); writer must handle v1-shaped reads gracefully forever.
- **Indexing.** `(query_id)` + `(created_at desc)` are required for Phase 8 UI; do not skip.

## Done criteria

1. Stream A: migration 011 applies cleanly; writer module + tests pass; idempotency verified.
2. Stream B: migration 012 applies cleanly; writer module + tests pass; sacrosanct rule enforced.
3. Stream C: consumer wired; flag-ON E2E test produces an audit row; flag-OFF asserts no row.
4. Stream D: replay CLI works against live dev DB; smoke script green.
5. Live-DB integration: run `npm run audit:smoke` against dev Cloud SQL; 5/5 + 2/2 round-trip clean.
6. No regression in Phase 3 tests (run full suite).
7. `lint` + `type-check` clean.
8. `must_not_touch` verified by directory diff.
9. New rows in CAPABILITY_MANIFEST.json for the two migrations + new code modules (manifest builder picks them up automatically; verify it ran).
10. Flag stays OFF — Phase 4 does NOT include flag activation; native flips later.
11. Native acceptance.

## Risk classification: MEDIUM

Writes to a new DB table are a real surface change. Mitigations:
- Migrations are additive, no existing-table modification
- Writer is best-effort and never blocks the response path
- Flag-OFF path completely untouched (regression suite proves it)
- Smoke script runs against dev before staging/prod migration

## Forward implications

- **Phase 5 (Interface basic)** is independent — UI doesn't read audit_log yet; that's Phase 8.
- **Phase 6 (LLM Checkpoints)** extends `audit_event_version` to 2 with checkpoint payloads. Phase 6 also replaces the heuristic prediction extractor in Stream C with a structured object.
- **Phase 8 (Audit View UI)** depends on Phase 4 completing.
- **Phase 10 (Calibration Loop)** depends on `prediction_ledger` having data accumulated. Native flips flag → predictions accumulate → Phase 10 closes the loop.

## How native triggers

Open a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension). Paste:

> Read EXEC_BRIEF_PHASE_4_v1_0.md and execute it.

This brief is disjoint from Phase 5 and the Phase 9 hotfix — they can run in three concurrent Claude Code sessions safely.

## Status updates

- AUTHORED 2026-04-27
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 11 done-criteria pass and native accepts
