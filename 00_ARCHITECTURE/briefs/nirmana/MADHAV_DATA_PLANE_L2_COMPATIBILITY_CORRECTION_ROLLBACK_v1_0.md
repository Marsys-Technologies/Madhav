---
artifact: MADHAV_DATA_PLANE_L2_COMPATIBILITY_CORRECTION_ROLLBACK
version: "1.0"
status: CORRECTION_VALIDATED_REVIEW_PENDING
authority: DP-SD-015
migration: platform/migrations/1034_data_plane_l2_producer_generations.sql
---

# L2 compatibility, correction and rollback

## Generations and dependencies

All 23 writers adopt one runtime decorator while preserving existing WriterBase,
registry identities, output schemas and writer-owned natural-key replacement.
One generation is content-addressed from contract version, accepted L0/L1,
chart, transitive writer-source digest, generation context and exact selected
dependency vector; build identity is observation-only. Light writers record one
partition. Multi-substep writers share that generation while recording an exact
calculation context for each substep key. Each partition completes only in the
caller's transaction and carries mandatory `UNAVAILABLE_AT_L2` temporal status.

Migration 1034 adds append-only generation, partition-context, partition-run,
row-snapshot and head-selection structures. Reapply is idempotent. Completed
generations, partition contexts, partitions, runs and snapshots reject update
or delete. There is no mutable `invalidated` state: correction creates a new
content-addressed generation and may name its completed predecessor. A current
head selects a completed generation, and explicit rollback only repoints that
head to another retained completed generation.

## Correction and rollback

Existing L2 rows and migrations remain readable. The new code neither deletes
nor appends `bodha_rm_dasha_windowed_prescriptions`; legacy rows are preserved.
Karanajala writes legacy activation columns as null and imports no Kāla service.
Rollback is application-code rollback plus explicit selection of a retained
completed generation. No delivered evidence is rewritten.

The envelope captures immutable full output rows and semantic digests. At writer
open, every trigger-covered L1 input and every declared L2 output relation is
shadowed transaction-locally from the exact selected snapshots, including empty
generations; writer-owned mutations are explicitly directed to `public`. This
prevents legacy active rows from silently contaminating replay or a downstream
build after head rollback. Pre-migration output rows are not retroactively
versioned.

Disposable PostgreSQL proved apply/reapply; stable replay across build change;
divergent replay rejection; snapshot deletion rejection; exact L1/L2 reads in
the presence of deliberately contaminated active rows; two exact partition
contexts completing one shared generation; two retained generations; selector
output; and rollback/head restoration. The isolated cluster was stopped and its
temporary directory retained rather than destructively removed.

## Cache/replay rules

Cache keys require contract version, exact accepted releases, chart/subject,
calculation context and stable structural identity. A wrong or stale dependency
fails before use. Deterministic slice replay is byte/content stable; volatile
timestamps/builds live only in the observation envelope. Live migration and
production rollback were not run in this goal.
