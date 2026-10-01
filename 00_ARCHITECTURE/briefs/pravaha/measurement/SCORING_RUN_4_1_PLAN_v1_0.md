---
artifact: SCORING_RUN_4_1_PLAN
version: "1.1"
status: PREPARED (awaits A2.5; the dry-run of this plan against '3.0' data is B4_7_DRY_RUN_v1_0.md — every command below that can run before '4.1' exists has run green)
date: 2026-09-30
amended: 2026-10-01 (v1.1 — column names corrected to the production schema after the B4.7 dry-run found the v1.0 SQL named the adapter aliases, not the table columns; no threshold, horizon, or procedure change)
author: Stream B (Śāstra), item B4.7
declared_before: "any '4.1' scoring — this plan is written before generation '4.1' exists"
---

# Scoring run plan — generation '4.1' under EVALUATION_PROTOCOL_v2_3

This is the run plan for scoring Stream A's `'4.1'` century build the moment A2.5 lands
(detector: publication row `'4.1'`). It is declared **before** the generation exists, per the
protocol's declared-before rule. It performs **no flip, no production write** — the extract
step is read-only; scoring runs locally against materialised files. The scoring deliverable
itself is B4.4 (`BASELINE_4_1_v1_0.md`); this page is only the plan.

## 1. Preconditions (all must hold before step 2)

1. A2.5 done: the `'4.1'` build for chart `482012f1-710e-4a25-994a-93821f5871aa` exists in
   `kala_gochara_windows` with `generation='4.1'` (candidate-only; `'3.0'` rows untouched —
   migration 1071's generation guard). Per native ruling, `'4.1'` is **not** a century
   build: it is narrowed to the scored horizon **1998-01-01 → 2026-04-18 (end-exclusive)**.
2. A2.6 evidence pack available (Link-2, gates, PRAMĀṆIN) — context for the baseline write-up,
   not an input to the scorer.
3. Protocol: `EVALUATION_PROTOCOL_v2_3.md` (accepted via D-PROTO, conditions verified B4.6).
4. Registry: `event_registry_v2_3.json` (47 held-out = 32 timing-usable + 15 year-grain).
5. Controls: `random_controls_v1_3.json` (materialised §7 controls, seed 482012).
6. Harness: `services/gochara_eval` at the merge commit of PR #2766 (B5.3), whose `'3.0'`
   reproduction is figure-identical to `rerun_result_v2_3.json` — that reproduction is the
   harness qualification; it is re-run first (step 3).

## 2. Extract spec (read-only)

Mirror of `baseline_3_0_extract_v1_0.json`, generation substituted:

- **Predicate:** `kala_gochara_windows where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  and generation='4.1'`
- **Columns:** `event_class, ws, we, pk, si, valence, adv, resolution, temporal_shape`
  (the harness's input adapter contract; any extra column is dropped, any missing column is
  INPUT_REJECTED).
- **TZ convention:** dates converted to IST civil dates via `(ts at time zone
  'Asia/Kolkata')::date` — identical to the '3.0' extract so figures compare.
- **Sign rule:** raw `si >= 0` on every row (valence domain {gain, loss, mixed, neutral} is
  descriptive; the convention is on si sign). A negative raw si ⇒ INPUT_REJECTED, stop.
- **Class universe:** every `event_class` validated against the 27-class universe
  (protocol §9.1 C4); an unknown class ⇒ INPUT_REJECTED.
- **Output:** `measurement/baseline_4_1_extract_v1_0.json`, same header shape as the '3.0'
  extract (`artifact`, `version`, `pinned_at`, `predicate`, `tz_convention`, `row_count`,
  `columns`, `rows`), sha256 computed at write and recorded here as the declared pin:
  `baseline_4_1_extract_v1_0.json sha256 = <TO PIN AT DUMP TIME>`.
- Row count is **not** required to equal '3.0''s 914; it is recorded and disclosed.
- **Horizon assertion (native narrowing):** `'4.1'` covers only the scored horizon — assert
  at extract time that no dumped window falls outside it, and stop on violation:

```sql
-- v1.1: production column names (window_start/window_end are DATE columns;
-- the v1.0 text named the adapter aliases ws/we — corrected after the B4.7 dry-run).
SELECT COUNT(*) AS outside_horizon
  FROM kala_gochara_windows
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND generation = '4.1'
   AND (((window_end at time zone 'Asia/Kolkata')::date) < DATE '1998-01-01'
        OR ((window_start at time zone 'Asia/Kolkata')::date) >= DATE '2026-04-18');
-- MUST BE 0 (horizon 1998-01-01 → 2026-04-18, end-exclusive); anything else ⇒ INPUT_REJECTED
-- Dry-run 2026-10-01: query executes against production read-only; returns 0 ('4.1' absent).
```

Dump (read-only role, governed path):

```sql
-- v1.1: production column names, adapter aliases kept on the SELECT list so the
-- output rows match the extract-file contract exactly (B4.7 dry-run verified:
-- the same query shape against generation='3.0' reproduces the pinned 914-row
-- extract, server-side md5 007aae8994b43b6291312f4719d1f949 == client-side).
SELECT event_class,
       (window_start at time zone 'Asia/Kolkata')::date AS ws,
       (window_end   at time zone 'Asia/Kolkata')::date AS we,
       (peak_date    at time zone 'Asia/Kolkata')::date AS pk,
       signed_intensity AS si, valence, is_adverse AS adv, resolution, temporal_shape
  FROM kala_gochara_windows
 WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
   AND generation = '4.1'
 ORDER BY event_class, ws;
```

## 3. Commands (exact)

Run from `platform/python-sidecar` on current `main`:

```sh
# 3a. Harness qualification — reproduce '3.0' figure-identical first:
python3 -m services.gochara_eval \
  --registry   ../../00_ARCHITECTURE/briefs/pravaha/measurement/event_registry_v2_3.json \
  --extract    ../../00_ARCHITECTURE/briefs/pravaha/measurement/baseline_3_0_extract_v1_0.json \
  --controls   ../../00_ARCHITECTURE/briefs/pravaha/measurement/random_controls_v1_3.json \
  --output     /tmp/requalify_3_0.json \
  --declared-pin 70ba6142…(full pin from baseline_3_0_extract_v1_0.json header record) \
  --generation 3.0
# EXPECT: exit 0; every endpoint figure equals rerun_result_v2_3.json.
# If not: STOP — the harness, not '4.1', is the suspect; do not score.

# 3b. '4.1' scoring pass:
python3 -m services.gochara_eval \
  --registry   ../../00_ARCHITECTURE/briefs/pravaha/measurement/event_registry_v2_3.json \
  --extract    ../../00_ARCHITECTURE/briefs/pravaha/measurement/baseline_4_1_extract_v1_0.json \
  --controls   ../../00_ARCHITECTURE/briefs/pravaha/measurement/random_controls_v1_3.json \
  --output     ../../00_ARCHITECTURE/briefs/pravaha/measurement/rerun_result_4_1_v2_3.json \
  --declared-pin <sha256 recorded in §2> \
  --generation 4.1
```

Determinism: the harness is deterministic; a same-input rerun must reproduce the output
byte for byte (checked once, recorded).

## 4. Expected outputs and acceptance thresholds (protocol §6, co-primary)

The result file `rerun_result_4_1_v2_3.json` carries the same top-level blocks as
`rerun_result_v2_3.json`: `input_adapter`, `source_reconciliation`, `dedup_table`,
`t_cover`, `t_time`, `t_rank`, `t_fp_overall` (+ per-class `t_fp_gain`), `t_honesty`,
`random_controls`. Horizon H = 1998-01-01 → 2026-04-17 = 10,334 days.

| endpoint | threshold | '3.0' reference (v2.3) |
|---|---|---|
| T-cover | ≥ 32/47, every miss named | 32/47 |
| T-time | capped median ≤ 45 d over the 5 exact-date events (misses at 182 d; uncapped disclosed) | 182 d (uncapped 686/998/333) |
| T-rank | median rank percentile ≤ 25, ≥ 17 of 32 timing-usable eligible, else rank-unproven (blocks flip); VOID possible with named degeneracy | VOID 0/32 |
| T-FP adverse | per frozen adverse class: admitted day-fraction ≤ min(1, 3·n_c·90/H) → 2.61 % (n_c=1), 5.23 % (n_c=2), 2.61 % allowance (major_loss n_c=0) | pass |
| T-FP gain (C1) | every non-adverse, non-`birth_anchor` class with scored rows inside 0.5 %–40 % of horizon days | pass |
| T-honesty | per-class coverage ≥ 50 % of horizon else `unqualified`; **'4.1' must ship the computation-coverage manifest** (protocol §6.5 R2-M06 build requirement — '3.0' is reported with it absent; '4.1' has no such excuse). Absent manifest ⇒ `t_honesty.status = UNVERIFIABLE` and the consequences of C3 apply | absent (disclosed) |
| Random controls | `random_controls.status = PASS` (materialised controls verified, seed 482012) | pass |

INPUT_REJECTED / source-reconciliation halt / controls rejection each write the partial
result with the machine-readable block and exit non-zero — that is a report, not a failure
of procedure.

## 5. Deliverable

`BASELINE_4_1_v1_0.md` (B4.4): every endpoint figure, every named miss, the degeneracy
tally, the coverage manifest status, the extract pin, the harness requalification evidence,
and the side-by-side with '3.0' — scored, never flipped.

## 6. What this plan never does

- No flip, no serving-authority change, no production write of any kind.
- No edit to the registry, the controls, the protocol, or the LEL after the extract exists;
  a discovered registry problem follows the source-reconciliation halt, not a quiet fix.
- No scoring of the three §11.3 worked events (development cases; excluded from the registry).
