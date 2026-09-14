---
artifact: MADHAV_DATA_PLANE_L2_COMPATIBILITY_CORRECTION_ROLLBACK
version: "1.0"
status: PRODUCER_READY_ACCEPTED
authority: DP-SD-015
migration: platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql
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

Migration 1034 adds append-only generation, partition-context, replay-run-row,
partition-run, row-snapshot and head-selection structures. Reapply is
idempotent. Completed generations, partition contexts, partitions, runs, exact
run-row receipts and snapshots reject update or delete. A completed replay must
observe the same exact row-identity set and semantic-output digest, so omitting
an existing row is divergence rather than a false pass. There is no mutable
`invalidated` state: correction creates a new content-addressed generation and
may name its completed predecessor. A current head selects only a compatible
completed generation, stale descendants disappear from the current-row view,
and explicit rollback only repoints that head to another retained compatible
generation.

## Correction and rollback

Existing L2 rows and migrations remain readable. The new code neither deletes
nor appends `bodha_rm_dasha_windowed_prescriptions`; legacy rows are preserved.
Karanajala writes legacy activation columns as null and imports no Kāla service.
Samvada is a passive compatibility participant: its legacy serving view remains
preserved and the producer run performs no shared DDL. Migration 1034 declares
its passive zero-row receipt with `target_floor=0`, replaces the legacy view
count with a constant-zero count and retires the view-based output-digest spec,
so pre-existing/query-time rows cannot earn current producer output. Pramāṇa Mapa consumes
only declared L1/L2 structural inputs; it no longer reads `life_events` or
refreshes shared materialized views. Its detectors reject stale selected heads,
absent/non-Gaṇita source provenance and nested LEL-shaped payload keys. The
context detector follows Pramāṇa's declared upstream L2 closure and excludes its
own previous head, because the replacement candidate is completed and selected
only after the writer returns; envelope completion validates the candidate.
Rollback is application-code rollback plus explicit selection of a retained
completed generation. No delivered evidence is rewritten.

The envelope captures immutable full output rows and semantic digests. At writer
open, every trigger-covered L1 input and every declared L2 output relation is
shadowed transaction-locally from the exact selected snapshots, including empty
generations; writer-owned mutations are explicitly directed to `public`. This
prevents legacy active rows from silently contaminating replay or a downstream
build after head rollback. Pre-migration output rows are not retroactively
versioned. Database capture recursively rejects non-finite numeric output.
Writers that use external embedding or multi-arm construction fail the
partition on partial execution rather than completing a partial generation.
Before MSR replacement, a catalog-driven foreign-key guard rejects dependent
rows outside the two owned L2 dependent tables, including cross-layer
`CASCADE`/`SET NULL` relationships. It first locks the exact parent-row scope
`FOR UPDATE`, which serializes concurrent FK insertion through the later delete.
Pratijñā and Upāya dry-run entry paths return before any SQL mutation.

Disposable PostgreSQL proved apply/reapply; stable replay across build change;
divergent and omitted-row replay rejection; snapshot deletion rejection;
recursive non-finite rejection; exact L1/L2 reads in the presence of deliberately
contaminated active rows; two exact partition contexts completing one shared
generation; generic cross-layer MSR-delete rejection; two-connection `CASCADE`
and `SET NULL` FK-insert serialization; dependency-topology addition/removal;
stale-descendant hiding and stale-head detector failure after an upstream-head
change; two retained generations; selector output; and rollback/head restoration.
The isolated cluster is temporary test evidence and
must be stopped before terminal handoff.

## Cache/replay rules

Cache keys require contract version, exact accepted releases, chart/subject,
calculation context and stable structural identity. The simultaneous selected
set is checked transitively: every chosen L2 generation's stored dependency
vector must agree with the selected L1/L2 heads, and its exact dependency key
set must equal the current recursive registry topology. Addition or removal of a
dependency therefore makes the old generation stale. A wrong or stale dependency
fails before use. Deterministic slice replay is byte/content stable; volatile
timestamps/builds live only in the observation envelope. Live migration and
production rollback were not run in this goal.
