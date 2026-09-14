---
artifact: MADHAV_DATA_PLANE_L2_COMPATIBILITY_CORRECTION_ROLLBACK
version: "1.0"
status: IMPLEMENTED_LOCAL_VALIDATION_IN_PROGRESS
authority: DP-SD-015
migration: platform/migrations/1034_data_plane_l2_producer_generations.sql
---

# L2 compatibility, correction and rollback

## Generations and dependencies

All 23 writers adopt one runtime decorator while preserving existing WriterBase,
registry identities, output schemas and writer-owned natural-key replacement.
One observation generation is derived from contract version, accepted L0/L1,
chart, build and calculation context. Light writers record one partition;
substep writers record their exact substep key. Each receipt carries source
digest, role, counts and mandatory `UNAVAILABLE_AT_L2` temporal status in the
caller's transaction.

Migration 1034 adds only an append-only receipt table. Reapply is idempotent.
Completed `(generation,asset,partition)` receipts are immutable; invalidation
requires timestamp and reason and retains the old receipt. A current head is the
latest completed compatible context, never merely the latest row. Source,
contract, accepted-release or calculation-context change creates a new receipt
set; display/rank/order changes do not alter structural IDs.

## Correction and rollback

Existing L2 rows and migrations remain readable. The new code neither deletes
nor appends `bodha_rm_dasha_windowed_prescriptions`; legacy rows are preserved.
Karanajala writes legacy activation columns as null and imports no Kāla service.
Rollback is application-code rollback plus selection of the last compatible
completed receipt/generation. Invalidation never rewrites delivered evidence.

The receipt envelope retains producer-generation provenance and head selection;
current legacy output tables continue their accepted replace-in-place semantics.
No claim is made that pre-migration output rows were retroactively versioned.

Disposable PostgreSQL proved create/reapply, two independent substep partitions,
completed-row mutation rejection, reasoned invalidation, retention of both prior
receipts, mandatory non-temporal status and selection of the remaining completed
partition as rollback head. The isolated test clusters were stopped; their temp
directories were retained rather than destructively removed.

## Cache/replay rules

Cache keys require contract version, exact accepted releases, chart/subject,
calculation context and stable structural identity. A wrong or stale dependency
fails before use. Deterministic slice replay is byte/content stable; volatile
timestamps/builds live only in the observation envelope. Live migration and
production rollback were not run in this goal.
