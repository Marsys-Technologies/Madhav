---
title: Telemetry Repair — Execution Record (Phase 0.9)
version: 1.0
status: EXECUTED (T-5 only) — NOT CERTIFIED
authored_by: KARAKA-M0-T39
work_queue_id: M0-T39
authority: D-6 (grant) as corrected by D-12 parts 3 and 5; D-28 part 2 (restore drill); D-15 (commit --only)
branch: campaign/nirmana-autonomous
executed_at_utc: 2026-08-23T08:25Z
snapshot: 00_ARCHITECTURE/control/snapshots/20260823T082402Z_m0t39_asset_registry/
input: 00_ARCHITECTURE/control/TELEMETRY_REPAIR_PROPOSAL_v1_0.md (KARAKA-M0-T3, analysis-only)
---

# Telemetry repair — what executed, and what did not

This document records observations. **It certifies nothing** (I16 / H7). PARĪKṢAKA decides
what the post-state means.

## 0 — Why this task exists

D-6 GRANTED the Phase 0.9 telemetry repair. M0-T3 measured it, snapshotted first, and
correctly executed nothing pending the grant. The grant arrived and the execution was never
dispatched. M0-T36's close-readiness pass surfaced that Phase 0.9 was being treated as
finished and had never run.

## 1 — What executed: T-5 only

**`asset_registry.estimated_seconds` backfilled/corrected from measured medians — 93 rows.**

| quantity | proposal (04:10:49Z) | re-measured (08:22–08:25Z) | match |
|---|---|---|---|
| registry rows | 128 | 128 | yes |
| `estimated_seconds` NOT NULL, pre | 9 | 9 | yes |
| assets with a computable median (in registry) | 93 | 93 | yes |
| assets with NO completed run (stay NULL) | 35 | 35 | yes |
| stored-and-disagreeing | 9 | 9 | yes |
| NULL-and-measurable (backfillable) | 84 | 84 | yes |
| **T-5 affected rows** | **93** | **93** | **yes** |

D-6 condition 3 is satisfied: no count diverged from the proposal, so nothing returned to
ADHIKĀRIN on that ground.

Statement executed (verbatim, the proposal's T-5, unmodified):

```sql
WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets WHERE state='complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS m FROM d GROUP BY asset_id)
UPDATE asset_registry r SET estimated_seconds = ceil(s.m)::int
FROM s WHERE s.asset_id = r.asset_id AND r.estimated_seconds IS DISTINCT FROM ceil(s.m)::int;
```

Observed: `rowcount = 93`; `estimated_seconds IS NULL` moved **119 → 35**; **0** cells in any
other column changed against the snapshot (5,120 cells compared).

**The 35 stay NULL.** They have no completed run in `build_run_assets`; a number for them
would be fabricated (D-6 condition 4, H6, §N.7 item 6).

## 2 — Method

1. **Fresh I2 snapshot** of `asset_registry` (the only table written):
   `snapshots/20260823T082402Z_m0t39_asset_registry/` — full-table CSV (QUOTE_ALL, 128 rows ×
   40 columns), `MANIFEST.json` with sha256 and the exact SELECT, and
   `restore_estimated_seconds.sql` (literal VALUES, 128 rows, NULLs preserved).
   **Verified by read-back**: live re-read compared cell-by-cell to the written CSV —
   5,120 cells, **0 mismatches**.
2. **Restore drill (D-28 part 2 standing requirement), made discriminating.** M0-T26's drill
   restored an unmutated table and found 0 differences, which proves the comparison but not the
   restore. This drill, inside ONE transaction that was **always rolled back**:
   applied the real T-5 mutation (93 rows; NULL count 119→35), *then* applied
   `restore_estimated_seconds.sql` (93 rows), then compared all 5,120 cells to the snapshot —
   **0 differing** — then `ROLLBACK`. Post-rollback NULL count back to **119**; the pre-flight
   was re-run afterwards and still passes. Net effect on the database: **zero**.
   The restore script is therefore a proven recovery path, not an authored one.
3. **Pre-flight discriminating detector.** Every asset's median was recomputed **independently
   in Python** (`statistics.median` over raw durations, `ceil`), never read back from the SQL
   that does the writing. The two derivations were compared: **0 disagreements across 93
   assets**. Six named rows carried a post-value known before the write, and all six were
   proven to *differ* pre-write, so the detector could have failed:

   | asset | pre | expected post | runs | observed post |
   |---|---|---|---|---|
   | ga_dashas | 2400 | 564 | 56 | 564 |
   | ga_panchanga | 60 | 3 | 50 | 3 |
   | ga_vargas | 600 | 94 | 48 | 94 |
   | ga_sensitive | 120 | 246 | 45 | 246 |
   | bo_laksana_rerank | NULL | 398 | 14 | 398 |
   | mi_sankalpa | NULL | 2 | 5 | 2 |

   Negative controls: five no-run assets asserted NULL before and after, with
   `target_floor` and `writer_timeout_seconds` asserted unmoved. All held.
4. **Rowcount assertions inside the write transaction**, with rollback and exit 4 on any
   unexpected number: rowcount ≠ 93, registry row count moved, pre-NULL ≠ 119, post-NULL ≠ 35,
   any value ≠ the independently-computed median, any non-target column changed, any
   discriminator or negative control off. Also asserted at write time: **0 non-terminal
   `build_runs`**, so no build was in flight underneath the measurement.
5. **Post-check on a fresh connection, against the snapshot** — not against the statement's
   shape: 5,120 cells compared; 93 `estimated_seconds` cells changed; **0** other cells changed;
   post NULL = 35; 0 values disagreeing with the independent median.

## 3 — What did NOT execute, and why

| item | rows | disposition |
|---|---|---|
| **T-1** — 3 orphaned `asset_throughput` rows | 3 | **NOT EXECUTED — no ruling reaches these rows.** See §4. |
| **T-2** — 3 `ka_gochara_sweep` throughput rows | 3 | **NOT TOUCHED.** D-12 part 4: leave exactly as they are, deferred to R3. Verified still `error`, unchanged. |
| **T-3** — 1,477 `build_run_assets` `queued` under terminated runs | 1,477 | **NOT EXECUTED — outside authorized scope.** D-12 part 5 admits `build_run_assets` for **telemetry aggregates only**; a state rewrite of 1,477 rows is not an aggregate. Reported, not widened. |
| **T-4** — 23 `build_runs` terminal with `ended_at IS NULL` | 23 (of 31) | **NOT EXECUTED — outside authorized scope.** D-12 part 5 does not name `build_runs` at all. |
| **T-6** — 24 `build_run_assets` rows naming absent assets | 24 | **NOT EXECUTED.** M0-T3 proposed no statement; audit trail. |
| any build dispatch | — | **NONE.** No build was triggered. |

Confirmed unchanged after the write (fresh read): `asset_throughput` 267 rows, states
lit 213 / error 27 / stale 23 / dormant 3 / incomplete 1; 3 orphan rows still present;
T-3 population still 1,477; T-4 population still 31.

## 4 — T-1: the ruling does not reach the rows it is thought to govern

D-12 part 3 corrected D-6 condition 1 and then declared M0-T3's re-dispatch recommendation
impossible, on this evidence:

> *"ka_gochara_sweep's @register is genuinely removed … so there is no writer to re-dispatch
> and no substep plan to be complete about … Both of M0-T3's options are therefore
> unavailable, which resolves to part 4."*

**`ka_gochara_sweep` is not one of the three orphaned rows.** There are two different
three-row sets in this repair, and they share no asset:

- **T-1's orphans** (state `dormant`, >24 h): `ka_kota_chakra`, `ka_vedha_gochara`, `mi_sankalpa`.
- **T-2's inactive-asset rows** (state `error`): three `ka_gochara_sweep` rows.

Verified read-only, in code: all three T-1 orphan assets have a **live `@register`** —
`platform/python-sidecar/services/ka_kota_chakra/writer.py:193`,
`platform/python-sidecar/services/ka_vedha_gochara/writer.py:250`,
`platform/python-sidecar/pipeline/orchestrator/writers/mi_sankalpa.py:76` — each reachable
through its `writers/` shim. Re-dispatch is therefore **available** for these three; the
"@register is genuinely removed" fact is true of `ka_gochara_sweep` only.

D-12 part 3's resolution routes to part 4, and part 4 rules on the `ka_gochara_sweep` rows.
So T-1's actual rows are governed by neither: writing a died-state would fabricate a failure
that did not happen (D-12 part 3, H6); writing `lit` would assert the promotion predicate's
verdict from a completed-run proxy (H4, §N.8 instance 4); `stale` (T-1b) needs a G3 ruling
that no ledger line makes. **T-1 is left untouched and returned to ADHIKĀRIN.** The task's own
constraint — dispatch no build — is honoured: the re-dispatch that would earn these states is
reported as the finding, not triggered.

## 5 — Observations recorded, not acted on

- **The repair survives a re-seed.** `estimated_seconds` appears in
  `ASSET_UPSERT_SQL`'s INSERT column list but **not** in its `ON CONFLICT DO UPDATE SET`
  clause (`platform/scripts/seed/asset_registry_seed.ts:3385-3434`), and the divergence
  report's coverage is derived from that SET clause via `onConflictUpdatedColumns()`
  (:3554-3558). Nothing in the seed overwrites these 93 measured values on an existing row.
- **The NULL population this repair moved was never seed-gated.** Because of the above,
  `estimated_seconds`'s 119 NULLs are outside the D-27/D-28/D-33 NULL-fill gate's column
  coverage. D-33's evidence line counts them among "621 NULL cells across 11 seed-on-conflict
  columns", and D-33 part 2 uses `estimated_seconds` as its second exemplar of a column whose
  NULL must not be filled by the seed. That exemplar does not appear to hold for existing
  rows. Reported as an observation with its evidence; the ruling is ADHIKĀRIN's.
- **M0-T3's design objection stands, unfixed.** `estimated_seconds` is a persisted copy of a
  quantity the cockpit derives live (`platform/src/app/api/cockpit/plan/route.ts:92`); it is
  correct today and drifts again after the next build (§N.7 item 3 shadow-constant). Fixing it
  is a code change, not a telemetry repair.
- `ka_gochara_v2_materialize` has completed runs but no registry row, so it is excluded from
  the backfill by the join. Consistent with M0-T3's T-6.

## 6 — Uncertainties, stated plainly

1. Whether D-12 part 3's conflation is a drafting slip or a deliberate widening I have
   misread. I did not resolve it; I stopped.
2. Whether `ceil()` vs `round()` matters. I used the proposal's `ceil()` unmodified; four
   sub-second assets would land on 0 under `round()`.
3. The 93 values are medians of historical runs on a machine and dataset that may not match
   the next build's. They are honest measurements of the past, not predictions.
4. I did not hold a lock. `build_runs` had 0 non-terminal rows at write time, which is
   evidence nothing was in flight, not proof.
