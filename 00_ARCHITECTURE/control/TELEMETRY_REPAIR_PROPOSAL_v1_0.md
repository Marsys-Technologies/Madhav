---
title: Telemetry Repair Proposal
version: 1.0
status: PROPOSED — NOT APPLIED
authored_by: KARAKA-M0-T3
work_queue_id: M0-T3
campaign: Nirmāṇa (NIRMANA_ELEVATION_PLAN_v4_0.md v4.2), Track M0 "telemetry repair (close orphaned rows, recompute medians, backfill estimated_seconds)"
branch: campaign/nirmana-autonomous
measured_at_utc: 2026-08-23T04:10:49Z  # SELECT now() — Q16
database_timezone: UTC
writes_executed: NONE
gate: ADHIKĀRIN ruling D-6 (2026-08-23T04:14:37Z) landed DURING this analysis and GRANTS the
  repair conditionally. It is mapped condition-by-condition in §10. It did not change what this
  task did: M0-T3's dispatch is analysis-only, so NO UPDATE, DELETE or DDL was executed here.
  Execution is a separate task for SŪTRADHĀRA to dispatch.
snapshot: 00_ARCHITECTURE/control/snapshots/20260823T041000Z_asset_throughput/ (I2 — verified, see §1)
---

# Telemetry Repair Proposal v1.0 — analysis only

**Nothing in this document has been executed.** It is a measured proposal. Every number
below is the output of a query that was actually run against production, read-only, with
`SET statement_timeout = '45s'`. No number is estimated, extrapolated or carried over from
another document. Where a quantity could not be measured, that is said in words rather than
filled with a plausible value (H6).

**This document does not certify anything** (I16 / H7). It records observations. PARĪKṢAKA
decides what they mean; ADHIKĀRIN decides what may be executed.

---

## 1 — Snapshot (invariant I2), taken before any measurement

Directory: `00_ARCHITECTURE/control/snapshots/20260823T041000Z_asset_throughput/`

| file | content |
|---|---|
| `asset_throughput.csv` | full table dump, `QUOTE_ALL`, 267 data rows + header |
| `MANIFEST.json` | row count, column list, exact SELECT, sha256, and the verification record |

Exact SELECT used:

```sql
SELECT * FROM asset_throughput ORDER BY asset_id, chart_id NULLS FIRST
```

- `live_row_count_at_snapshot`: **267**
- `csv_data_rows`: **267**
- `csv_sha256`: `f5b0c2bb4890af7838acc9c5ddc1a125a77390f10255d762725fa99fdaf621f7`
- `csv_bytes`: 46230
- columns (14): `asset_id, rows_per_second, measurement_count, last_measured_at, last_measured_build_id, history, chart_id, state, built_against_upstream_hash, built_against_writer_hash, last_built_at, last_error, rows_written, expected_rows`

### 1.1 — Restore verification (a snapshot whose restore was never verified is not a snapshot)

The verification did not stop at "the file exists and has the right number of lines". It
re-ran the exact SELECT against live, re-encoded every value with the same encoder the dump
used, and compared **cell by cell** against the parsed CSV:

```
checksum_match: True
header_match: True
csv_parsed_rows: 267
live_count_now: 267 | manifest_live_count: 267 | match: True
cell_level_mismatched_rows: 0
distinct_(asset_id,chart_id): 267 of 267
```

The verification record is written into `MANIFEST.json` under `verification`.

**Honest limit of this verification:** it proves the CSV is a faithful, losslessly-encoded,
uniquely-keyed copy of the live table and that a restore has an unambiguous target row for
every line. It does **not** prove a restore was performed into a scratch database and
re-compared — no such database was available to this task, and creating one was not in scope.
If ADHIKĀRIN considers a round-trip into a scratch schema a precondition for G6, that step has
not been done and should be required before any destructive step.

---

## 2 — The state vocabulary the table actually contains

Asked first, before assuming any vocabulary (Q1, Q3).

`asset_throughput.state` CHECK constraint:

```
CHECK (state = ANY (ARRAY['dormant','building','lit','stale','error','incomplete']))
```

Observed distribution (Q1) — 267 rows:

| state | rows |
|---|---|
| lit | 213 |
| error | 27 |
| stale | 23 |
| dormant | 3 |
| incomplete | 1 |
| building | **0** |

There is **no `planned` and no `running` state** in this table, and **no heartbeat column**.
The task brief's vocabulary (`planned / building / running`) does not match the schema; the
real non-terminal pair is `dormant` (never promoted) and `building` (in flight). The only
freshness columns are `last_built_at` and `last_measured_at`. `history` is `jsonb` and is
`[]` on **all 267 rows** (Q6) — there is no in-row duration history to recompute from.

Adjacent telemetry tables and their own vocabularies (Q14, Q15):

- `build_run_assets` (7,144 rows): `complete` 3,255 · `error` 1,565 · `queued` 1,477 · `aborted` 847.
- `build_runs` (665 rows): `failed` 376 · `completed` 267 · `stopped` 22. **No non-terminal run state exists in the data** — nothing is `running` or `queued` at the run level.
- `build_events`: **0 rows**. `asset_throughput_state_audit`: 4 rows, all `bg_transit_rules`, 2026-08-22 (Q38).

---

## 3 — Measurement B1: orphaned rows

### 3.1 — The staleness threshold, and why

Chosen threshold: **24 hours** since `last_built_at`.

Justification, from measured data rather than taste:

- The largest `writer_timeout_seconds` anywhere in `asset_registry` is **86,400 s = 24 h**
  (Q17; distribution 60/120/300/600/1800/3600/10800/21600/86400). A row still in a
  non-terminal state more than 24 h after its last build event has outlived the longest
  watchdog budget the system itself declares, so it cannot be an in-flight build under any
  registered writer.
- The longest **successfully completed** asset run ever recorded is **8,022.84 s ≈ 2.2 h**
  (Q18, over 3,255 completed runs) — an order of magnitude under the threshold, so 24 h is
  not a borderline cut.
- It is deliberately conservative. A tighter threshold (e.g. 3 × p99) would classify more
  rows as orphaned; at 24 h the answer happens to be the same, because every candidate is
  10+ days old.

### 3.2 — The result

```sql
-- Q39
SELECT count(*) FROM asset_throughput
WHERE state IN ('dormant','building')
  AND (last_built_at IS NULL OR last_built_at < now() - interval '24 hours');
-- => 3
```

All three rows, verbatim (Q19 / Q51):

| asset_id | chart_id | state | last_built_at | age at measurement | rows_written | last_error |
|---|---|---|---|---|---|---|
| `ka_kota_chakra` | `1c826d5a…` | dormant | 2026-08-10 06:31:50.205106+00 | 12 d 21:38:59 | 585 | NULL |
| `ka_vedha_gochara` | `1c826d5a…` | dormant | 2026-08-10 06:31:50.294612+00 | 12 d 21:38:59 | 178 | NULL |
| `mi_sankalpa` | `482012f1…` | dormant | 2026-08-13 01:02:38.387443+00 | 10 d 03:08:11 | 0 | NULL |

Split by whether the run left data behind:

- rows_written > 0: **2** (Q40)
- rows_written = 0 or NULL: **1** (Q41)

### 3.3 — What the run record says these three actually did (Q49)

For each of the three, `build_run_assets` holds a `state='complete'` record whose `ended_at`
is **bit-identical to `asset_throughput.last_built_at`**:

| asset_id | run-asset state | started_at | ended_at | parent run state |
|---|---|---|---|---|
| `ka_kota_chakra` | complete | 2026-08-10 06:31:47.040230+00 | 2026-08-10 06:31:50.205106+00 | completed |
| `ka_vedha_gochara` | complete | 2026-08-10 06:31:46.934590+00 | 2026-08-10 06:31:50.294612+00 | completed |
| `mi_sankalpa` | complete | 2026-08-13 01:02:38.055325+00 | 2026-08-13 01:02:38.387443+00 | **failed** |

`build_substep_progress` holds **0 rows** for all three (Q50) — none of them is a
substep-planned heavy writer.

This is the orphan signature: the writer ran to completion and the promotion to a terminal
state never fired. Note the asymmetry — the `mi_sankalpa` run's **parent run** is `failed`,
so "the asset completed" and "the run completed" are different facts for that row.

### 3.4 — Orphans in the adjacent run tables (same defect class, different table)

- **1,477** `build_run_assets` rows are `state='queued'` while their parent `build_runs` row
  is terminal (Q42). **0** are queued under a non-terminal run (Q43); **0** are orphaned by a
  missing parent (Q44). Every queued row in the database is a child of a run that already ended.
- **31** `build_runs` rows carry a terminal state with `ended_at IS NULL` (Q45: `failed` 27,
  `stopped` 4). Of those, **23** have at least one child with a non-null `ended_at` from which
  a run end could be derived (Q55); **8** have none (Q56).
- **1,726** `build_run_assets` rows have `ended_at` set with `started_at` NULL (Q46: `error`
  1,250, `aborted` 476) and **362** `aborted` rows have neither timestamp (Q47). These are
  unmeasurable for duration and are excluded from every median below.

---

## 4 — Measurement B2: rows attached to inactive / retired / absent assets

`asset_registry` lifecycle vocabulary as it actually exists (Q22): `is_active=true/CURRENT` 80 ·
`is_active=true/DRAFT` 47 · `is_active=false/RETIRED` 1. Total 128 assets.

| question | query | answer |
|---|---|---|
| throughput rows whose `asset_id` is absent from `asset_registry` | Q23 | **0** (a FK `asset_throughput_asset_id_fkey` makes this impossible) |
| throughput rows on `is_active IS DISTINCT FROM true` assets | Q24 | **3** |
| throughput rows on `catalog_status <> 'CURRENT'` | Q25 | **112** (DRAFT 109 + RETIRED 3) |
| throughput rows whose `chart_id` is absent from `charts` | Q28 | **0** |
| scope mismatches (global asset with a chart_id, or per_chart asset without) | Q29/Q29b | **0** |
| registry assets with no throughput row at all | Q30 | **2** |

The 3 inactive-asset rows are all one asset (Q24):

| asset_id | chart_id | state | is_active | catalog_status | last_built_at | rows_written |
|---|---|---|---|---|---|---|
| `ka_gochara_sweep` | `1c826d5a…` | error | false | RETIRED | 2026-08-12 16:30:19.625456+00 | 1705 |
| `ka_gochara_sweep` | `482012f1…` | error | false | RETIRED | 2026-08-12 15:56:35.616518+00 | 0 |
| `ka_gochara_sweep` | `cb73cd3d…` | error | false | RETIRED | 2026-07-27 19:58:18.289258+00 | 2684 |

The 109 DRAFT rows are **not** proposed for anything here. DRAFT is an active lifecycle state
(`is_active=true`), and catalogue disposition of DRAFT assets is G1, belonging to the rung
that owns each asset — not to a Track-M telemetry task (I13).

---

## 5 — Measurement B3: per-asset duration statistics and median disagreement

### 5.1 — Where a median lives, and what "stored" means here

There is **no stored median column** anywhere. The cockpit computes it live, per request,
in `platform/src/app/api/cockpit/plan/route.ts:92-103`:

```sql
SELECT asset_id,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (ended_at - started_at)))::numeric AS median_seconds
FROM build_run_assets
WHERE asset_id = ANY($1) AND ended_at IS NOT NULL AND started_at IS NOT NULL AND state = 'complete'
GROUP BY asset_id
```

The only **persisted** per-asset duration figure is `asset_registry.estimated_seconds`. So
"stored median vs recomputed median" is read here as **`estimated_seconds` vs the median that
the cockpit's own query produces**. This reading should be confirmed by ADHIKĀRIN; if a
different "stored median" is meant, it is not in this schema and I did not find it.

### 5.2 — Every asset that has a stored value disagrees with its recomputed median (Q33)

9 assets carry a non-null `estimated_seconds`. **9 of 9 DISAGREE** (tolerance ±0.5 s):

| asset_id | stored_est | completed_runs | median_s | p90_s | min_s | max_s | verdict |
|---|---|---|---|---|---|---|---|
| ga_dashas | 2400 | 56 | 563.46 | 2767.76 | 125.18 | 4199.34 | DISAGREE |
| ga_panchanga | 60 | 50 | 2.87 | 43.42 | 0.93 | 56.53 | DISAGREE |
| ga_positions | 60 | 54 | 4.02 | 54.65 | 1.64 | 165.05 | DISAGREE |
| ga_sade_sati | 120 | 51 | 64.77 | 510.28 | 18.38 | 783.01 | DISAGREE |
| ga_sensitive | 120 | 45 | 245.20 | 1280.96 | 0.24 | 2109.47 | DISAGREE |
| ga_strength | 60 | 49 | 96.92 | 210.25 | 6.66 | 1251.58 | DISAGREE |
| ga_structural | 120 | 52 | 98.34 | 157.82 | 61.56 | 228.05 | DISAGREE |
| ga_tajaka | 60 | 52 | 13.96 | 34.06 | 6.34 | 53.67 | DISAGREE |
| ga_vargas | 600 | 48 | 93.02 | 450.23 | 10.83 | 3536.43 | DISAGREE |

The disagreements go both ways (`ga_vargas` stored 600 vs measured 93; `ga_sensitive` stored
120 vs measured 245), so this is drift, not a single systematic offset. All nine stored values
are round numbers from the {60,120,600,2400} set — they read as seeded placeholders that were
never re-measured, not as measurements.

### 5.3 — Is the median input polluted?

The plan §Phase-0 note says telemetry is "polluted to 16.9-day maxima". Measured (Q52):

| build_run_assets state | rows with both timestamps | max duration | max in days |
|---|---|---|---|
| error | 315 | 1,461,818.14 s | **16.92 d** |
| complete | 3,255 | 8,022.84 s | 0.09 d |
| aborted | 7 | 2,671.73 s | 0.03 d |

The 16.9-day maximum lives **entirely in `state='error'` rows**, which the median query already
excludes. Negative durations: **0** (Q54). Completed runs exceeding their own asset's
`writer_timeout_seconds`: **6** (Q53), all `bo_laksana_rerank` (timeout 600 s; observed 637–1233 s).
That is a timeout-budget finding, not a duration-data defect, and it is not repaired here.

### 5.4 — Full recomputed statistics

93 registry assets have at least one completed run and therefore a computable median. The full
table (asset_id, layer, scope, catalog_status, is_active, stored_est, timeout_s, completed_runs,
median, p90, min, max) is in §9 below.

Coverage (Q34–Q36):

- assets appearing with completed runs in `build_run_assets`: **94** (one of which is not in the registry — see §6, T-6)
- registry assets with a computable median: **93**
- registry assets with `estimated_seconds IS NULL`: **119** of **128** (Q27)
  - of those, with a computable median (backfillable): **84** (Q35)
  - of those, with no completed run at all (not measurable): **35** (Q36)

The 35 unmeasurable assets are 34 `bg_*` L0 assets plus `lel_events` (Q37) — all CURRENT and
active except `lel_events` (DRAFT). They have never run through `build_run_assets`, so a
measured value for them does not exist and **must not be invented** (H6).

---

## 6 — Proposed repair, as exact SQL

Every statement is annotated with the number of rows it would affect, **measured by running
the equivalent `SELECT count(*)`**, quoted verbatim from the run. None was executed.

> **Ordering constraint.** T-1 and T-3/T-4 read each other's tables. If more than one is
> approved they should be applied in the listed order, in one transaction, with the §1
> snapshot in hand.

### T-1 — the three orphaned `asset_throughput` rows

**Measured affected rows: 3.**

```sql
-- measurement (executed, read-only): returns 3
SELECT count(*) FROM asset_throughput
WHERE state IN ('dormant','building')
  AND (last_built_at IS NULL OR last_built_at < now() - interval '24 hours');
```

**T-1a — RECOMMENDED. No SQL. Re-dispatch, do not hand-write the state.**

The correct terminal state for these three rows is whatever the orchestrator's promotion
predicate produces (CLAUDE.md §N.8 / SATYA-DĪPA; `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1).
Writing `lit` by hand because a `build_run_assets` row says `complete` would be exactly H4 —
a status written on a proxy rather than on its detector's verdict. I decline to propose it and
recommend the three assets be re-dispatched through the normal build path, so the state is
*earned*. Rows affected by hand: **0**.

**T-1b — fallback, only if ADHIKĀRIN rules under G3 that "a `complete` run record whose
`ended_at` equals `last_built_at`" is a real detector for *ran-and-left-data*.** Even then the
honest target is `stale` (data exists; freshness unproven), never `lit`:

```sql
-- affected rows: 3 (measured)
UPDATE asset_throughput t
SET state = 'stale'
WHERE t.state IN ('dormant','building')
  AND (t.last_built_at IS NULL OR t.last_built_at < now() - interval '24 hours')
  AND EXISTS (
    SELECT 1 FROM build_run_assets a
    JOIN build_runs r ON r.id = a.run_id
    WHERE a.asset_id = t.asset_id
      AND r.chart_id IS NOT DISTINCT FROM t.chart_id
      AND a.state = 'complete'
      AND a.ended_at = t.last_built_at
  );
```

Sub-counts if ADHIKĀRIN wants to split by whether data was written: **2** rows with
`rows_written > 0`, **1** row (`mi_sankalpa`) with `rows_written = 0`. Note that `mi_sankalpa`'s
completing run sat inside a **failed** parent run, which is the weakest of the three cases.

### T-2 — the three throughput rows on the RETIRED `ka_gochara_sweep`

**Measured affected rows: 3. PARKED — no statement proposed.**

```sql
-- measurement (executed, read-only): returns 3
SELECT count(*) FROM asset_throughput t
JOIN asset_registry r ON r.asset_id = t.asset_id
WHERE r.is_active IS DISTINCT FROM true;
```

`ka_gochara_sweep` is the asset charter §2 P1 names by name as unrecoverable. I propose no
statement against it — not a DELETE (I6 forbids it and H1 forbids the class), not a state
rewrite. M0's exit criterion "throughput rows on inactive assets = zero" collides with P1
here, and resolving that collision is ADHIKĀRIN's, not mine. **This is the single question in
this document I most want ruled on before anything else in it runs.**

### T-3 — 1,477 `build_run_assets` rows left `queued` under terminated runs

**Measured affected rows: 1,477.**

```sql
-- measurement (executed, read-only): returns 1477
SELECT count(*) FROM build_run_assets a
JOIN build_runs r ON r.id = a.run_id
WHERE a.state = 'queued' AND r.state IN ('completed','failed','stopped');

-- proposed statement, affected rows: 1477
UPDATE build_run_assets a
SET state = 'aborted'
FROM build_runs r
WHERE r.id = a.run_id
  AND a.state = 'queued'
  AND r.state IN ('completed','failed','stopped');
```

`aborted` is chosen because it is already the vocabulary this table uses for "planned but
never executed" (847 existing rows, 362 of them with neither timestamp — Q47), and because it
leaves `started_at`/`ended_at` NULL rather than inventing times. No timestamp is written.

### T-4 — 31 `build_runs` rows terminal with `ended_at IS NULL`

**Measured: 31 total; 23 derivable; 8 not derivable.**

```sql
-- measurement A (executed): returns 23
SELECT count(*) FROM build_runs r
WHERE r.ended_at IS NULL AND r.state IN ('completed','failed','stopped')
  AND EXISTS (SELECT 1 FROM build_run_assets a WHERE a.run_id = r.id AND a.ended_at IS NOT NULL);

-- measurement B (executed): returns 8
SELECT count(*) FROM build_runs r
WHERE r.ended_at IS NULL AND r.state IN ('completed','failed','stopped')
  AND NOT EXISTS (SELECT 1 FROM build_run_assets a WHERE a.run_id = r.id AND a.ended_at IS NOT NULL);

-- proposed statement, affected rows: 23
UPDATE build_runs r
SET ended_at = sub.max_child_end
FROM (
  SELECT a.run_id, max(a.ended_at) AS max_child_end
  FROM build_run_assets a
  WHERE a.ended_at IS NOT NULL
  GROUP BY a.run_id
) sub
WHERE sub.run_id = r.id
  AND r.ended_at IS NULL
  AND r.state IN ('completed','failed','stopped');
```

The remaining **8** rows are deliberately left NULL. No timestamp exists from which their end
can be derived, and inventing one — `now()`, `created_at`, a nearby run's end — would be H6.
An honest NULL beats an invented value (§N.7 item 6).

### T-5 — backfill / correct `asset_registry.estimated_seconds` from the measured median

**Measured affected rows: 93** (9 stored-and-wrong + 84 stored-NULL-and-measurable).

```sql
-- measurement (executed, read-only): returns 93
WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets
  WHERE state = 'complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (
  SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS median_seconds
  FROM d GROUP BY asset_id
)
SELECT count(*) FROM asset_registry r JOIN s ON s.asset_id = r.asset_id
WHERE r.estimated_seconds IS DISTINCT FROM ceil(s.median_seconds)::int;

-- proposed statement, affected rows: 93
WITH d AS (
  SELECT asset_id, EXTRACT(EPOCH FROM (ended_at - started_at)) AS secs
  FROM build_run_assets
  WHERE state = 'complete' AND started_at IS NOT NULL AND ended_at IS NOT NULL
), s AS (
  SELECT asset_id, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY secs) AS median_seconds
  FROM d GROUP BY asset_id
)
UPDATE asset_registry r
SET estimated_seconds = ceil(s.median_seconds)::int
FROM s
WHERE s.asset_id = r.asset_id
  AND r.estimated_seconds IS DISTINCT FROM ceil(s.median_seconds)::int;
```

The **35** assets with no completed run (§5.4) are untouched by this statement and stay NULL.
That is the correct outcome: `estimated_seconds` is a measurement, and 35 of them have never
been measured. `ceil()` is used so a sub-second median does not round to 0 in an `integer`
column; if ADHIKĀRIN prefers `round()`, the affected count is unchanged at 93 but four
sub-second assets would land on 0 — I recommend against it for that reason.

**Design objection I want on the record, not fixed here:** `estimated_seconds` is a persisted
copy of a quantity the cockpit already derives live from `build_run_assets`
(`plan/route.ts:92`). Backfilling it makes it correct today and stale again after the next
build — a §N.7 item 3 shadow-constant. The structurally right repair is for the column to be
dropped in favour of the live derivation, or for a job to own it. That is a code change, not a
telemetry repair, and it is outside M0-T3; it is reported as a finding, not proposed here.

### T-6 — 24 `build_run_assets` rows naming assets that are not in the registry

**Measured affected rows: 24. No statement proposed.**

```sql
-- measurement (executed, read-only): returns 24
SELECT count(*) FROM build_run_assets a
LEFT JOIN asset_registry r ON r.asset_id = a.asset_id
WHERE r.asset_id IS NULL;
```

| asset_id | rows | first_seen | last_seen |
|---|---|---|---|
| `ga_pyjhora_engine` | 10 | 2026-06-12 12:02:05+00 | 2026-07-13 21:13:41+00 |
| `ka_gochara_v2_materialize` | 10 | 2026-08-10 06:31:52+00 | 2026-08-10 06:37:50+00 |
| `chart_dashas` | 3 | (no started_at) | 2026-07-13 21:13:41+00 |
| `ga_chart_service` | 1 | (no started_at) | 2026-07-13 21:13:41+00 |

These are historical run records for asset ids that no longer exist in the registry (there is
no FK on `build_run_assets.asset_id`). They are audit trail. Deleting them destroys evidence
and gains nothing; renaming them asserts an identity I have not established. Reported, not
repaired. `build_substep_progress` has **0** such rows (Q60).

---

## 7 — What this analysis did NOT do

- **Executed no write.** No UPDATE, no DELETE, no DDL, no `SET` other than `statement_timeout`.
  Every connection was `autocommit=True` and every statement was a SELECT.
- Did not restore the snapshot into a scratch database (§1.1) — the verification is
  cell-level fidelity against live, not a round-trip restore.
- Did not touch `ka_gochara_sweep` in any way (P1).
- Did not decide any catalogue disposition, floor, or DRAFT resolution (G1/G2 — ADHIKĀRIN's).
- Did not repair the `bo_laksana_rerank` timeout budget (§5.3) or the `estimated_seconds`
  design objection (T-5) — both are outside M0-T3.
- Did not certify anything (I16/H7). This document contains observations and proposals only.

## 8 — Uncertainties, stated plainly

1. **"Stored median" is an interpretation.** No column stores a median. I read it as
   `asset_registry.estimated_seconds`. If the campaign means something else, I did not find it.
2. **The task brief's state vocabulary does not match the schema** (`planned`/`running` do not
   exist). I used the CHECK constraint's vocabulary. If `planned`/`running` referred to
   `build_run_assets.queued` and a running state, note that no running state exists in that
   table's data either.
3. **T-1's correct target state is genuinely undecided.** I believe hand-writing `lit` is
   forbidden. I am less sure whether `stale` is right or whether the rows should simply be left
   dormant until re-dispatched. I recommend re-dispatch (T-1a) and would rather do nothing than
   guess.
4. **The 24 h threshold is defensible but not the only defensible choice.** At 24 h the answer
   is 3; I did not test whether a tighter threshold changes it, because every candidate is 10+
   days old and no threshold between 1 h and 10 d could change the count.
5. **T-3's choice of `aborted`** is inferred from how the table already uses the word, not from
   a written specification. If a `cancelled`/`skipped` vocabulary was intended, the CHECK
   constraint does not say so — `build_run_assets.state` has **no** CHECK constraint at all
   (Q3 lists constraints for `asset_throughput` only; I did not find one for `build_run_assets`).
6. **I did not verify that no concurrent build was running** while I measured. `build_runs` has
   no non-terminal row (Q15), which is strong evidence nothing was in flight, but it is
   inference, not a lock.

---

## 9 — Full per-asset duration statistics (93 registry assets with a computable median)

Source: `build_run_assets` where `state='complete'` and both timestamps are non-null.
`stored_est` is `asset_registry.estimated_seconds`; `timeout_s` is `writer_timeout_seconds`.

| asset_id | layer | scope | catalog_status | is_active | stored_est | timeout_s | completed_runs | median_seconds | p90_seconds | min_seconds | max_seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bg_class_priors | brahmagyan | global | CURRENT | True |  | 10800 | 1 | 9.61 | 9.61 | 9.61 | 9.61 |
| bg_formula_constants | brahmagyan | global | CURRENT | True |  | 10800 | 1 | 1.61 | 1.61 | 1.61 | 1.61 |
| bg_ghatana | brahmagyan | global | CURRENT | True |  | 10800 | 1 | 2.96 | 2.96 | 2.96 | 2.96 |
| bg_kp_sublord_division | brahmagyan | global | CURRENT | True |  | 120 | 1 | 0.90 | 0.90 | 0.90 | 0.90 |
| bg_vidhi_floors | brahmagyan | global | DRAFT | True |  | 600 | 5 | 0.46 | 0.57 | 0.31 | 0.61 |
| bg_vidhi_primitives | brahmagyan | global | DRAFT | True |  | 600 | 5 | 0.17 | 0.19 | 0.14 | 0.19 |
| bo_anveshana | bodha | per_chart | CURRENT | True |  | 10800 | 42 | 31.31 | 196.28 | 0.08 | 511.46 |
| bo_arudha | bodha | per_chart | DRAFT | True |  | 600 | 13 | 0.82 | 7.13 | 0.37 | 7.77 |
| bo_bimba | bodha | per_chart | CURRENT | True |  | 10800 | 51 | 15.77 | 38.24 | 0.33 | 73.43 |
| bo_cdlm_summary | bodha | per_chart | DRAFT | True |  | 10800 | 43 | 1.35 | 10.09 | 0.08 | 16.74 |
| bo_cgm_motifs | bodha | per_chart | CURRENT | True |  | 10800 | 46 | 2.75 | 67.39 | 0.10 | 143.68 |
| bo_cgm_paths | bodha | per_chart | CURRENT | True |  | 10800 | 45 | 1.48 | 9.25 | 0.11 | 25.54 |
| bo_chart_gestalt | bodha | per_chart | DRAFT | True |  | 10800 | 38 | 1.87 | 9.36 | 0.99 | 52.82 |
| bo_drishti | bodha | per_chart | CURRENT | True |  | 10800 | 47 | 89.26 | 167.85 | 0.34 | 188.05 |
| bo_karanajala | bodha | per_chart | CURRENT | True |  | 10800 | 52 | 18.19 | 130.33 | 0.08 | 1091.40 |
| bo_laksana | bodha | per_chart | CURRENT | True |  | 10800 | 56 | 192.78 | 736.76 | 47.87 | 1286.32 |
| bo_laksana_rerank | bodha | per_chart | DRAFT | True |  | 600 | 14 | 397.41 | 1185.39 | 83.64 | 1233.07 |
| bo_nakshatra_semantic | bodha | per_chart | DRAFT | True |  | 600 | 14 | 0.90 | 9.90 | 0.58 | 11.48 |
| bo_pramana_mapa | bodha | per_chart | CURRENT | True |  | 10800 | 43 | 4.07 | 18.88 | 1.36 | 27.78 |
| bo_pratijna | bodha | per_chart | CURRENT | True |  | 10800 | 44 | 15.99 | 35.95 | 2.81 | 70.58 |
| bo_samskara | bodha | per_chart | CURRENT | True |  | 10800 | 45 | 756.11 | 1206.51 | 293.45 | 1467.98 |
| bo_samvada | bodha | per_chart | CURRENT | True |  | 10800 | 43 | 0.19 | 1.48 | 0.09 | 2.42 |
| bo_sangati | bodha | per_chart | CURRENT | True |  | 10800 | 50 | 12.35 | 34.57 | 0.08 | 47.18 |
| bo_special_lagna | bodha | per_chart | DRAFT | True |  | 600 | 11 | 0.41 | 4.18 | 0.31 | 8.82 |
| bo_sudarshana | bodha | per_chart | DRAFT | True |  | 600 | 11 | 0.99 | 10.09 | 0.62 | 10.33 |
| bo_upaya | bodha | per_chart | CURRENT | True |  | 10800 | 51 | 8.72 | 48.48 | 0.54 | 75.70 |
| bo_vargottama_dhana | bodha | per_chart | DRAFT | True |  | 600 | 12 | 0.87 | 7.30 | 0.32 | 8.21 |
| bo_yantra_mechanism | bodha | per_chart | DRAFT | True |  | 600 | 15 | 12.78 | 127.60 | 2.38 | 137.76 |
| ga_ayurdaya | ganita | per_chart | CURRENT | True |  | 10800 | 13 | 3.65 | 18.43 | 0.57 | 19.38 |
| ga_condition | ganita | per_chart | CURRENT | True |  | 10800 | 51 | 29.62 | 269.53 | 10.57 | 296.98 |
| ga_dashas | ganita | per_chart | CURRENT | True | 2400 | 10800 | 56 | 563.46 | 2767.76 | 125.18 | 4199.34 |
| ga_medical | ganita | per_chart | CURRENT | True |  | 10800 | 50 | 1.00 | 7.19 | 0.27 | 10.41 |
| ga_nakshatra | ganita | per_chart | CURRENT | True |  | 10800 | 48 | 15.60 | 189.23 | 5.29 | 395.06 |
| ga_panchanga | ganita | per_chart | CURRENT | True | 60 | 10800 | 50 | 2.87 | 43.42 | 0.93 | 56.53 |
| ga_positions | ganita | per_chart | CURRENT | True | 60 | 10800 | 54 | 4.02 | 54.65 | 1.64 | 165.05 |
| ga_prashna | ganita | per_chart | CURRENT | True |  | 10800 | 47 | 0.76 | 3.48 | 0.10 | 5.68 |
| ga_sade_sati | ganita | per_chart | CURRENT | True | 120 | 10800 | 51 | 64.77 | 510.28 | 18.38 | 783.01 |
| ga_sensitive | ganita | per_chart | CURRENT | True | 120 | 10800 | 45 | 245.20 | 1280.96 | 0.24 | 2109.47 |
| ga_sensitive_degree | ganita | per_chart | CURRENT | True |  | 10800 | 15 | 22.37 | 44.29 | 1.53 | 55.90 |
| ga_strength | ganita | per_chart | CURRENT | True | 60 | 10800 | 49 | 96.92 | 210.25 | 6.66 | 1251.58 |
| ga_structural | ganita | per_chart | CURRENT | True | 120 | 10800 | 52 | 98.34 | 157.82 | 61.56 | 228.05 |
| ga_tajaka | ganita | per_chart | CURRENT | True | 60 | 10800 | 52 | 13.96 | 34.06 | 6.34 | 53.67 |
| ga_transit_anchors | ganita | per_chart | CURRENT | True |  | 10800 | 47 | 0.87 | 8.44 | 0.21 | 12.64 |
| ga_vargas | ganita | per_chart | CURRENT | True | 600 | 10800 | 48 | 93.02 | 450.23 | 10.83 | 3536.43 |
| ga_vastu | ganita | per_chart | CURRENT | True |  | 10800 | 50 | 0.73 | 6.68 | 0.22 | 13.47 |
| ga_vichara | ganita | per_chart | DRAFT | True |  | 10800 | 18 | 29.08 | 725.85 | 14.11 | 1272.23 |
| ga_yoga | ganita | per_chart | CURRENT | True |  | 10800 | 51 | 6.26 | 20.93 | 2.28 | 41.48 |
| ka_avadhi | kala | per_chart | CURRENT | True |  | 10800 | 43 | 13.13 | 24.29 | 0.99 | 60.61 |
| ka_bhavishya_lekha | kala | per_chart | DRAFT | True |  | 10800 | 48 | 0.23 | 1.98 | 0.03 | 2.32 |
| ka_dasha_kala | kala | per_chart | DRAFT | True |  | 10800 | 47 | 1.51 | 5.06 | 0.07 | 25.93 |
| ka_gochara | kala | per_chart | CURRENT | True |  | 1800 | 33 | 0.19 | 1.65 | 0.07 | 139.03 |
| ka_gochara_resonance | kala | per_chart | CURRENT | True |  | 600 | 18 | 0.32 | 16.63 | 0.15 | 17.05 |
| ka_gochara_sweep | kala | per_chart | RETIRED | False |  | 21600 | 9 | 999.52 | 7634.18 | 0.57 | 8022.84 |
| ka_gochara_v3_century_materialize | kala | per_chart | CURRENT | True |  | 3600 | 3 | 613.49 | 2915.95 | 239.72 | 3491.56 |
| ka_graha_sancara | kala | global | DRAFT | True |  | 10800 | 32 | 0.14 | 0.90 | 0.09 | 1.99 |
| ka_jivana_parva | kala | per_chart | DRAFT | True |  | 10800 | 45 | 0.62 | 2.42 | 0.17 | 3.19 |
| ka_kala_darshana | kala | per_chart | DRAFT | True |  | 10800 | 48 | 0.37 | 3.20 | 0.03 | 4.24 |
| ka_kalasutra | kala | per_chart | DRAFT | True |  | 10800 | 49 | 32.98 | 619.50 | 0.04 | 1040.83 |
| ka_kota_chakra | kala | per_chart | CURRENT | True |  | 120 | 3 | 2.59 | 3.05 | 2.11 | 3.16 |
| ka_kshetra | kala | per_chart | CURRENT | True |  | 86400 | 15 | 236.74 | 3141.52 | 0.03 | 7129.39 |
| ka_moorti_nirnaya | kala | per_chart | CURRENT | True |  | 120 | 4 | 2.23 | 3.83 | 1.26 | 4.51 |
| ka_muhurta_seva | kala | global | DRAFT | True |  | 10800 | 32 | 0.33 | 0.95 | 0.14 | 4.18 |
| ka_sangam | kala | per_chart | DRAFT | True |  | 10800 | 50 | 462.87 | 2217.22 | 0.03 | 4389.75 |
| ka_sudarshana_varsha | kala | per_chart | CURRENT | True |  | 60 | 3 | 1.95 | 2.33 | 1.89 | 2.42 |
| ka_taranga | kala | per_chart | CURRENT | True |  | 10800 | 43 | 22.33 | 47.24 | 7.07 | 82.52 |
| ka_tithi_pravesha | kala | per_chart | CURRENT | True |  | 120 | 4 | 2.27 | 2.41 | 1.83 | 2.43 |
| ka_tulana | kala | per_chart | DRAFT | True |  | 10800 | 44 | 0.08 | 1.25 | 0.05 | 1.35 |
| ka_vedha_gochara | kala | per_chart | CURRENT | True |  | 120 | 3 | 3.18 | 3.32 | 2.83 | 3.36 |
| ka_vighnakara | kala | per_chart | DRAFT | True |  | 10800 | 47 | 13.88 | 23.57 | 0.04 | 86.52 |
| ka_yojaka | kala | per_chart | DRAFT | True |  | 10800 | 51 | 35.76 | 76.96 | 0.03 | 111.50 |
| mi_abhilekha | mimamsa | per_chart | DRAFT | True |  | 10800 | 40 | 0.08 | 1.35 | 0.05 | 1.69 |
| mi_adhilepa | mimamsa | per_chart | DRAFT | True |  | 10800 | 42 | 10.32 | 23.00 | 0.09 | 47.27 |
| mi_bhara | mimamsa | per_chart | DRAFT | True |  | 10800 | 34 | 1.63 | 4.57 | 0.14 | 7.45 |
| mi_bhavisya | mimamsa | per_chart | DRAFT | True |  | 10800 | 43 | 1.81 | 5.53 | 0.82 | 15.64 |
| mi_darshana | mimamsa | per_chart | DRAFT | True |  | 10800 | 39 | 0.62 | 4.77 | 0.13 | 6.02 |
| mi_gunanaka | mimamsa | per_chart | DRAFT | True |  | 10800 | 44 | 0.10 | 1.84 | 0.07 | 2.33 |
| mi_jivanaghatana | mimamsa | per_chart | DRAFT | True |  | 10800 | 41 | 0.20 | 1.57 | 0.07 | 22.79 |
| mi_kula | mimamsa | global | DRAFT | True |  | 10800 | 38 | 0.11 | 1.39 | 0.07 | 1.84 |
| mi_pariksha | mimamsa | per_chart | DRAFT | True |  | 10800 | 42 | 1.95 | 9.24 | 0.13 | 32.91 |
| mi_pramana | mimamsa | per_chart | DRAFT | True |  | 10800 | 43 | 0.20 | 3.52 | 0.14 | 3.90 |
| mi_sambandha | mimamsa | per_chart | DRAFT | True |  | 10800 | 42 | 0.16 | 1.63 | 0.07 | 4.70 |
| mi_sankalpa | mimamsa | per_chart | DRAFT | True |  | 300 | 5 | 1.10 | 1.59 | 0.33 | 1.71 |
| mi_seva | mimamsa | per_chart | DRAFT | True |  | 10800 | 39 | 0.09 | 1.57 | 0.06 | 1.72 |
| mi_vistara | mimamsa | global | DRAFT | True |  | 10800 | 38 | 0.13 | 1.12 | 0.05 | 1.46 |
| ph_muhurta | phala | per_chart | DRAFT | True |  | 10800 | 46 | 0.99 | 14.06 | 0.06 | 38.12 |
| ph_nimitta | phala | per_chart | DRAFT | True |  | 10800 | 46 | 2.35 | 46.78 | 0.53 | 68.51 |
| ph_phaladesa | phala | per_chart | DRAFT | True |  | 10800 | 43 | 0.74 | 5.50 | 0.10 | 8.26 |
| ph_pramana | phala | per_chart | DRAFT | True |  | 10800 | 43 | 0.86 | 17.32 | 0.06 | 38.22 |
| ph_pratikara | phala | per_chart | DRAFT | True |  | 10800 | 46 | 2.78 | 52.19 | 0.04 | 73.38 |
| ph_rectification | phala | per_chart | DRAFT | True |  | 10800 | 46 | 0.95 | 20.49 | 0.39 | 34.17 |
| ph_sankrama | phala | per_chart | DRAFT | True |  | 10800 | 46 | 4.23 | 136.04 | 0.05 | 211.66 |
| ph_sodhana | phala | per_chart | DRAFT | True |  | 10800 | 43 | 0.45 | 5.12 | 0.03 | 10.99 |
| ph_suddha_sodhana | phala | per_chart | DRAFT | True |  | 10800 | 43 | 0.81 | 11.11 | 0.04 | 31.55 |
---

*End of TELEMETRY_REPAIR_PROPOSAL v1.0. Authored by KĀRAKA on work item M0-T3. NO WRITES WERE
EXECUTED. Every statement in §6 is gated on an ADHIKĀRIN ruling that has been requested and has
not returned. This document certifies nothing (I16/H7).*

---

## 10 — Addendum: ADHIKĀRIN ruling D-6, mapped condition by condition

D-6 (`state/DECISIONS.jsonl`, G9, 2026-08-23T04:14:37Z, subject *M0-T3 / asset_throughput
telemetry repair*) was appended to the ledger **while this analysis was running** — three
minutes before this document was written — answering SŪTRADHĀRA's Q2(b). It rules
**GRANTED, conditionally**.

**It did not cause anything to be executed, and nothing was.** M0-T3's dispatch is
analysis-only; a ruling that the repair *may* run is not a dispatch that it *should* run, and
condition 6 requires an independent verifier for a post-state that does not yet exist.
Execution belongs to a task SŪTRADHĀRA dispatches, with this document as its input.

| D-6 condition | status against this proposal |
|---|---|
| **(1) An orphaned row is closed to an honest terminal state that says the run died — never `lit`/`complete`/`service_ok`, never anything that reads as success. H4, refused not parked.** | **Satisfied, and independently arrived at.** T-1 declines to propose `lit` on exactly this reasoning (a `complete` run record is a proxy, not the promotion predicate's verdict) before D-6 was read. **But note a real divergence:** D-6 says close to a state that *says the run died*. All three orphans have a run record that says the run **completed** — what died was the promotion, not the run. `stale` (T-1b) says "data exists, freshness unproven", which is honest but is not "the run died"; `error` would say the run died, which the evidence contradicts. My recommendation stays T-1a — re-dispatch, so the state is produced by the detector rather than chosen by an agent. If ADHIKĀRIN requires a written state, the choice between `stale` and `error` is a ruling I do not have. |
| **(2) Snapshot first; confirm readable before executing, not merely present.** | **Satisfied and exceeded.** §1.1: checksum re-verified, CSV re-parsed, live re-counted, and every cell re-compared against a live re-read — 0 mismatches, 267/267 unique keys. Honest gap recorded: no round-trip restore into a scratch database. |
| **(3) Exact affected-row counts; executed statement must affect exactly that many; divergence halts and returns to ADHIKĀRIN.** | **Satisfied on the proposal side.** Every statement in §6 carries a count from a `SELECT count(*)` that was actually run: T-1 = 3, T-2 = 3 (parked), T-3 = 1477, T-4 = 23 (+8 deliberately untouched), T-5 = 93, T-6 = 24 (no statement). The executing task must re-measure immediately before executing — these counts are from 2026-08-23T04:10:49Z and `now()`-relative predicates drift. |
| **(4) Medians/estimates derived from measured telemetry only; no clean telemetry ⇒ NULL, not a plausible number.** | **Satisfied.** T-5 touches only the 93 assets with a computable median and leaves the 35 with no completed run at NULL, explicitly. §5.3 also shows the 16.9-day pollution is confined to `state='error'` rows the median query already excludes. |
| **(5) Scoped to `asset_throughput`; no asset's target table touched.** | **Partially exceeded, and this needs a ruling.** T-1 is inside `asset_throughput`. But D-6's own subject line names all three of "close orphaned rows, recompute medians, backfill estimated_seconds", and **medians and `estimated_seconds` do not live in `asset_throughput`** — the durations are in `build_run_assets` and `estimated_seconds` is a column of `asset_registry` (§5.1). T-3/T-4 (`build_run_assets`, `build_runs`) and T-5 (`asset_registry`) therefore fall outside a literal reading of condition 5 while falling inside the ruling's own subject. I flag the contradiction rather than resolve it: **T-3, T-4 and T-5 should not execute until ADHIKĀRIN confirms condition 5 is scoped to the repair's content, not to the single table named.** |
| **(6) PARĪKṢAKA verifies the post-state independently (I16).** | **Not applicable yet — there is no post-state.** Nothing was executed. |

**Net:** D-6 changes nothing this task did, and adds one question (condition 5's table scope)
and one refinement (condition 1's "says the run died" vs. these rows' actual evidence) that the
executing task must have settled before it runs.
