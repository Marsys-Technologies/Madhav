---
title: "PARIŚEṢA-V4 GA-3 Rebuild Packet — F-104 / F-35: the 10-asset L2→L4→L5 chain on the canonical chart"
canonical_id: F104_F35_TENASSET_REBUILD_PACKET
version: 1.0
status: CURRENT
date: 2026-08-21
authority: >
  GA-3 protected-data execution, v1.1 §19.2 packet discipline, AS AMENDED BY
  OWNER_RULINGS_20260821.md R-7 (mandatory clauses: FK-inclusive rollback rehearsal;
  MEASURED before-image scope). A packet missing either R-7 clause is DATA_PARKED by
  definition — both are discharged here in §3 and §4.
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
findings_covered: [F-104, F-35 (canonical-chart scope only)]
findings_explicitly_NOT_covered: [F-63, F-35 (system-wide/second-chart scope), F-71, F-147, F-143 data]
supersedes: >
  verification_artifacts/PARISESA_V4_GA3_REBUILD_20260821/GA3_EXECUTION_PACKET_v1_0.md
  §5.4 / §8.5 — that packet's own carry-forward asked for exactly this document.
executed: NO — this is an AUTHORING pass. No write of any kind was made against
  chart 482012f1 or any production table in producing this packet.
---

# GA-3 Rebuild Packet — F-104 / F-35, canonical chart, 10 assets

**Status: AUTHORED, NOT EXECUTED.** Everything below is measured against live
production through a read-only connection, and the rollback is rehearsed on a
throwaway local cluster. Nothing in production was written.

---

## §0 — Scope determination: this is ONE packet for TWO findings, not three

The dispatching brief carried the premise that F-35, F-63 and F-104 "share ONE
underlying rebuild scope, per the ledger." **That premise is correct for F-35 and
F-104 and false for F-63**, and the ledger itself says so. Stating this plainly is
the first act of the packet, because forcing F-63 in would reintroduce precisely the
scope-inflation defect (F-146) this packet exists to avoid.

| Finding | ledger `next_action` (verbatim, abridged) | In this packet? |
|---|---|---|
| F-104 | "author a properly-scoped 10-asset L2→L4→L5 GA-3 packet with `phala_*` before-images and an FK-inclusive rollback rehearsal" | **YES** |
| F-35 | "same as F-104 — needs the properly-scoped 10-asset rebuild, native-authorized" | **YES**, canonical chart only (see §0.3) |
| F-63 | "park until a full-chart rebuild is native-authorized (**out of scope for a bounded GA-3 packet by design, not an oversight**)" | **NO** — see §0.2 |

### §0.1 — The 10 assets, derived from the DAG, not from prose

Measured against `asset_registry.depends_on` (the `text[]` column that IS the DAG) by
recursive closure. The minimal asset set that takes `mi_darshana` and `mi_sambandha`
from `error` to `lit`, given that `bo_upaya` has already been rebuilt (`lit`,
2026-08-21 02:31:53Z), is exactly ten:

| # | asset_id | layer | depends_on (in-plan deps in **bold**) | current state | rows_written |
|---|---|---|---|---|---|
| 1 | `ph_pratikara` | Phala (L4) | ph_nimitta, bo_upaya, ka_vighnakara, ka_sangam | `stale` | 536 |
| 2 | `ph_pramana` | Phala (L4) | ph_nimitta, ph_sankrama, ph_muhurta, **ph_pratikara**, ph_sodhana, ph_suddha_sodhana | `stale` | 139 |
| 3 | `ph_phaladesa` | Phala (L4) | ph_nimitta, ph_muhurta, **ph_pratikara**, ph_suddha_sodhana, ph_sankrama, **ph_pramana**, bo_laksana | `stale` | 13 |
| 4 | `mi_bhavisya` | Mīmāṃsā (L5) | **ph_pramana**, ph_nimitta, **ph_phaladesa**, mi_kula, mi_jivanaghatana, bo_laksana | `error` (BLOCKED) | 278 |
| 5 | `mi_pramana` | Mīmāṃsā (L5) | **mi_bhavisya**, mi_jivanaghatana, bg_ghatana, bg_formula_constants | `error` (BLOCKED) | 63 |
| 6 | `mi_pariksha` | Mīmāṃsā (L5) | **mi_pramana**, mi_kula, bg_formula_constants | `error` (BLOCKED) | 1,664 |
| 7 | `mi_gunanaka` | Mīmāṃsā (L5) | **mi_pramana**, mi_kula, bg_formula_constants | `error` (BLOCKED) | 9 |
| 8 | `mi_adhilepa` | Mīmāṃsā (L5) | **mi_gunanaka**, bo_laksana, ka_sangam, ph_nimitta, ga_positions | `error` (BLOCKED) | 112,270 |
| 9 | `mi_sambandha` | Mīmāṃsā (L5) | **mi_pramana**, **mi_pariksha**, **mi_bhavisya** | `error` (BLOCKED) | 24 |
| 10 | `mi_darshana` | Mīmāṃsā (L5) | **mi_pramana**, **mi_adhilepa**, **mi_sambandha**, **mi_pariksha**, **mi_gunanaka**, mi_kula, mi_jivanaghatana, bo_pratijna | `error` (BLOCKED) | 115 |

The label "L2→L4→L5" is inherited from the prior packet's carry-forward and describes
where the cascade *originated*. **No L2 asset is in this plan** — `bo_upaya` (L2) is
already `lit` and is not re-run. The plan is 3 Phala + 7 Mīmāṃsā assets.

**Plan closure is proved, not assumed.** All 15 out-of-plan dependencies of these ten
were measured and every one is `lit`:
`bo_laksana`, `bo_pratijna`, `bo_upaya`, `ga_positions`, `ka_sangam`, `ka_vighnakara`,
`mi_jivanaghatana`, `ph_muhurta`, `ph_nimitta`, `ph_sankrama`, `ph_sodhana`,
`ph_suddha_sodhana` (chart-scoped rows), plus `mi_kula`, `bg_ghatana`,
`bg_formula_constants` (global assets, `chart_id IS NULL`, all `lit`). The scheduler's
seeding query is `SELECT 1 FROM asset_throughput WHERE asset_id=%s AND (chart_id=%s OR
chart_id IS NULL) AND state IN ('lit','service_ok')`
(`platform/python-sidecar/pipeline/orchestrator/runner.py`, `_schedule_parallel`), so the
three global assets seed correctly despite having no per-chart row. **This is the exact
check the previous run failed** — it dispatched 7 assets whose out-of-plan deps were
`stale`, and every one BLOCKED. With 10 assets, nothing blocks.

### §0.2 — Why F-63 is NOT in this packet

`ga_panchanga` is an **L1 root** (`depends_on = {ga_positions}`). It appears nowhere in
the ten assets' dependency closure — verified by the same recursive query. Rebuilding
it would flip 53 downstream assets across all five layers from `lit` to `stale`, and
neither possible disposition of those 53 fits a bounded packet (leave them stale = a
silent five-layer commitment; restore `lit` = asserting a freshness no detector would
now compute, a §N.8 violation). This is not a new judgement: it is the prior packet's
§5 conclusion, re-confirmed by the owner-facing ledger entry, and R-9 lists F-63 as a
separate item in the DATA_PARKED queue. **F-63 stays parked.** Its defect is unchanged
and independently re-measurable (5 rows in `chart_facts` with
`fact_category='panchanga_special_yoga_combinations'`, `fact_key='combination_name'`,
value `'unknown'`).

A packet that swept F-63 in to satisfy a three-finding framing would be exactly the
"scope grew mid-execution" failure F-104's own next_action was written to prevent.

### §0.3 — F-35's second chart is NOT in this packet

F-35's defect is system-wide; its data footprint is 2 charts (`482012f1…` canonical,
`1c826d5a…` Abhinandan). GA-3 authority here is scoped to the native's own canonical
chart. `1c826d5a…` is a different consent surface and gets its own packet of identical
shape. This packet closes F-35's canonical-chart half only; **F-35 does not become
terminal on this execution.**

### §0.4 — Verdict on scoping

**It scopes cleanly as one packet — for two findings, not three.** The ten assets form
a single connected dependency chain with one entry point (`ph_pratikara`) and one exit
(`mi_darshana`); every out-of-plan dependency is satisfied; the post-run stale cascade
touches exactly two assets outside the plan and both are already stale (§10.3). No
sub-scope inside the ten needs its own ruling. The rulings that ARE needed are about
*whether to run it now at all* (§14), not about how to cut it.

---

## §1 — Quiescence proof (§19.2 clause 1)

**Method** — five independent conditions, each a query whose failing value is possible:

```sql
SELECT count(*) FROM pg_stat_activity WHERE datname='amjis' AND pid<>pg_backend_pid();
SELECT count(*) FROM pg_stat_activity WHERE datname='amjis' AND pid<>pg_backend_pid()
                                        AND xact_start IS NOT NULL;
SELECT count(*) FROM pg_locks WHERE mode<>'AccessShareLock' AND pid<>pg_backend_pid();
SELECT count(*) FROM asset_throughput WHERE state IN ('building','running','pending','queued');
SELECT count(*) FROM build_runs      WHERE state IN ('planned','running','paused');
```

**Measured 2026-08-21T13:32:26Z** against production `amjis`:

| Condition | Required | Measured |
|---|---|---|
| other backends on `amjis` | — | 0 |
| open transactions (not self) | 0 | **0** |
| non-AccessShare locks (not self) | 0 | **0** |
| assets in flight (ALL charts) | 0 | **0** |
| active `build_runs` | 0 | **0** |

**A quiescence proof is valid only at its instant.** This one is recorded to show the
system was quiet while the packet was authored; **it does NOT authorise execution.**
The executor MUST re-run all five immediately before dispatch and record the fresh
values in the execution log. Additionally the orchestrator itself takes
`pg_try_advisory_lock(hashtext(chart_id))` and exits 3 if the chart is locked, so a
race arriving after the measurement is refused rather than interleaved — a second,
independent guard, not a substitute for the first.

---

## §2 — Code-provenance gate (precondition; the packet is worthless without it)

A rebuild only helps if the image that runs carries the fixes. Verified as an earned
signal (§N.8) by inspecting the exact deployed commit's tree, not by inferring from a
deploy timestamp.

- Cloud Run job `brahma-build-pipeline-job` image tag:
  `asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:25c8aaacdd712bfd3266c46c2ffa8d07e01f7b0a`
- `25c8aaacd` **is** `origin/main` HEAD (verified by fetching GitHub directly, not a
  local mirror: `git merge-base --is-ancestor` → YES, and `25c8aaacd..origin/main` is
  empty). Production is exactly current with `main`.
- In that commit's tree:
  - `writers/mi_darshana.py` — 6 × `"not_assessed"` literals present (F-104's fix), and
    **zero** occurrences of a `'clean'` literal anywhere in the file. The writer is
    structurally incapable of emitting `leakage_status='clean'`.
  - `writers/mi_darshana.py` — the F-143 fix is present (`_EMPIRICAL_SCORED_MIN`,
    `evidence_refs.n_scored_matches` gating for `emergent_law`, `retrodiction_never_empirical`,
    `_GRADE_STRUCTURAL`). PR #1414 is deployed.
  - `writers/mi_sambandha.py` — F-35's `scored_count` gate present
    (`"empirical" if scored >= 5`), `scored_count` written as column 8 of the insert.
- Migration adding `mimamsa_manifestation_grammar.scored_count` verified **applied** in
  production (`information_schema.columns`: `scored_count integer NOT NULL DEFAULT 0`).
  F-35's write path will not fail on a missing column.
- `writer_timeout_seconds` for all ten assets = **10800** (measured from
  `asset_registry`). None carries the `600` budget that made `mi_bhara` (F-71) time out.
  Job-level `timeoutSeconds` = 86400, `ORCHESTRATOR_WORKER_LIMIT=2`, 4 vCPU / 8 GiB.

**Provenance gate: PASS.** But see §11.1 — one deployed fix (F-35's) is provably inert
in production for a reason unrelated to deployment.

---

## §3 — Before-images (§19.2 clause 2, R-7 clause (b): MEASURED, not documented)

### §3.1 — How the write set was derived (and why `count_sql` is not sufficient)

R-7(b) forbids assuming before-image scope from documentation. The scope below was
derived by reading each of the ten writers' actual `INSERT INTO` / `DELETE FROM`
targets in the deployed commit, then **reconciling the per-table live counts against
each asset's own `rows_written`**. Two findings came out of doing it that way:

1. **`asset_registry.count_sql` UNDER-DECLARES `mi_gunanaka`.** Its `count_sql` names
   only `mimamsa_multipliers`. The writer also inserts into
   **`mimamsa_calibration_snapshot`** (`mi_gunanaka.py`, `INSERT INTO
   mimamsa_calibration_snapshot … ON CONFLICT (snapshot_id) DO NOTHING`). A packet that
   took its before-image scope from `count_sql` — or from `rows_written`, which also
   excludes it — would have missed a real table. This is the F-146 defect class,
   second instance, found by obeying R-7(b).
2. **`mimamsa_calibration_snapshot` ACCRETES.** It is the one table in the write set
   that does **not** follow the §N.3 delete-then-insert standard: each run inserts a
   new `snap_<chart8>_<epoch>` row and never deletes. Consequence for rollback: a
   restore-from-CSV without a preceding `DELETE` leaves the extra row behind (and PK-
   conflicts). The rollback procedure in §4.4 deletes before restoring for **every**
   table precisely so this table is handled correctly; negative control NC-1 (§4.6)
   proves the detector catches it when it isn't.

### §3.2 — Write set, measured 2026-08-21T13:2x Z

| # | asset | table(s) written | live rows (chart-scoped) | Σ | `rows_written` | reconciles |
|---|---|---|---|---|---|---|
| 1 | `ph_pratikara` | `phala_mitigation` | 536 | 536 | 536 | ✓ |
| 2 | `ph_pramana` | `phala_pramana` | 139 | 139 | 139 | ✓ |
| 3 | `ph_phaladesa` | `phala_phaladesa` | 13 | 13 | 13 | ✓ |
| 4 | `mi_bhavisya` | `mimamsa_predictions` 139 · `mimamsa_manifestation_sets` 139 | | 278 | 278 | ✓ |
| 5 | `mi_pramana` | `mimamsa_calibration` 57 · `mimamsa_reliability` 6 | | 63 | 63 | ✓ |
| 6 | `mi_gunanaka` | `mimamsa_multipliers` 9 · **`mimamsa_calibration_snapshot` 4** | | 13 | 9 | ✗ **under-counts by 4** |
| 7 | `mi_pariksha` | `mimamsa_qa_eval` 168 · `mimamsa_attribution` 1425 · `mimamsa_discoveries` 71 | | 1,664 | 1,664 | ✓ |
| 8 | `mi_adhilepa` | `mimamsa_load_bearing` 4 · `mimamsa_anchor_adjustment` 139 · `mimamsa_convergence_adjustment` 500 · `mimamsa_fact_adjustment` 61,523 · `mimamsa_signal_adjustment` 50,104 | | 112,270 | 112,270 | ✓ |
| 9 | `mi_sambandha` | `mimamsa_manifestation_grammar` | 24 | 24 | 24 | ✓ |
| 10 | `mi_darshana` | `mimamsa_insight_units` 115 · `mimamsa_insight_embeddings` 0 | | 115 | 115 | ✓ |

**Write set = 20 tables, 115,115 rows.**

### §3.3 — Collateral witness set (the R-7(a) discovery, see §5)

Five further tables are **not written by any in-plan asset** but are reachable by FK
action from the write set, so they are before-imaged as witnesses and, for one of them,
actively repaired during rollback:

| table | written by | rows | why it is in the before-image |
|---|---|---|---|
| `phala_sankrama` | `ph_sankrama` (out of plan, `lit`) | 2,510 | **child** of `phala_mitigation` via `ON DELETE SET NULL` — the rebuild's DELETE mutates it |
| `phala_muhurta` | `ph_muhurta` (out of plan, `lit`) | 134 | **parent** of `phala_mitigation.initiation_muhurta_ref`; must exist for restore |
| `phala_anchors` | `ph_nimitta` (out of plan, `lit`) | 139 | **parent** of `phala_mitigation.linked_anchor_id` and `phala_pramana.anchor_id` |
| `phala_sodhana` | `ph_sodhana` (out of plan, `lit`) | 97 | sibling child of `phala_anchors`; witness that no cascade reached it |
| `phala_suddha_sodhana` | `ph_suddha_sodhana` (out of plan, `lit`) | 139 | ditto |

**Total before-image = 25 tables, 118,134 rows.**

### §3.4 — Capture procedure (run immediately before dispatch, after the fresh §1 proof)

```bash
CHART=482012f1-710e-4a25-994a-93821f5871aa
DIR=verification_artifacts/PARISESA_V4_GA3_F104_F35_<UTCSTAMP>/BEFORE
mkdir -p "$DIR"
for t in phala_mitigation phala_pramana phala_phaladesa \
         mimamsa_predictions mimamsa_manifestation_sets \
         mimamsa_calibration mimamsa_reliability \
         mimamsa_multipliers mimamsa_calibration_snapshot \
         mimamsa_qa_eval mimamsa_attribution mimamsa_discoveries \
         mimamsa_load_bearing mimamsa_anchor_adjustment mimamsa_convergence_adjustment \
         mimamsa_fact_adjustment mimamsa_signal_adjustment \
         mimamsa_manifestation_grammar mimamsa_insight_units mimamsa_insight_embeddings \
         phala_sankrama phala_muhurta phala_anchors phala_sodhana phala_suddha_sodhana ; do
  psql "$PGURL" -c "\copy (SELECT * FROM $t WHERE chart_id='$CHART') TO '$DIR/BEFORE_$t.csv' CSV HEADER"
done
psql "$PGURL" -c "\copy (SELECT * FROM asset_throughput WHERE chart_id='$CHART') \
                   TO '$DIR/BEFORE_asset_throughput.csv' CSV HEADER"
```

`SELECT *` — every column, every row. `asset_throughput` is snapshotted in full so any
state transition is reversible. **The count in each CSV MUST equal the count in §3.2 /
§3.3 at capture time**; a mismatch means something moved since this packet was authored
and is an ABORT condition (§12).

---

## §4 — Tested rollback (§19.2 clause 3, R-7 clause (a): FK-INCLUSIVE) — REHEARSED

### §4.1 — What R-7(a) demands and what the prior rehearsal did

F-146 was raised because the previous rehearsal replicated only four target tables. The
FK constraint that actually refused the real rollback
(`bodha_rm_dasha_windowed_prescriptions_base_prescription_id_fkey`) did not exist in
the replica, so the rehearsal's `PASS` was a result no code path could have turned into
a `FAIL`. R-7(a) makes the fix mandatory: **the replica must carry the full
FK-connected table set.**

### §4.2 — Defining "full FK-connected set" without it meaning "the whole database"

Taken literally as an undirected transitive closure over `pg_constraint`, the component
containing the 20 write-set tables is **78 tables** — because every chart-scoped table
reaches `charts`, and `charts` reaches `profiles`, `conversations`, `projects` and the
rest of the application schema. That is not a useful rehearsal scope, and pretending to
replicate it would be theatre.

**The operative definition used here:** the undirected FK closure of the write set,
with `charts`, `profiles` and `asset_registry` treated as **terminal nodes** — included,
but not expanded through. Justification: those three are never written by any in-plan
asset, and every edge into them is a leaf-to-root `chart_id`/`asset_id` reference that a
DELETE or INSERT on a dependent row cannot exercise in the outward direction. This
yields **34 tables**, which is the replica actually built.

Measured closure (34): `bodha_contradictions, bodha_msr_signals, bodha_signal_embeddings,
charts, kala_activation, kala_bhavishya, kala_convergence, kala_darshana, kala_obstruction,
mimamsa_anchor_adjustment, mimamsa_attribution, mimamsa_calibration,
mimamsa_calibration_snapshot, mimamsa_convergence_adjustment, mimamsa_discoveries,
mimamsa_fact_adjustment, mimamsa_insight_embeddings, mimamsa_insight_units,
mimamsa_load_bearing, mimamsa_manifestation_grammar, mimamsa_manifestation_sets,
mimamsa_multipliers, mimamsa_predictions, mimamsa_qa_eval, mimamsa_reliability,
mimamsa_signal_adjustment, phala_anchors, phala_mitigation, phala_muhurta,
phala_phaladesa, phala_pramana, phala_sankrama, phala_sodhana, phala_suddha_sodhana`
(+ a `profiles(id)` stub so `charts_client_id_fkey` can be created).

### §4.3 — The replica, and DETECTOR-0 (schema parity)

Built on a throwaway local cluster: PostgreSQL **17.10**, `initdb --auth=trust`, Unix
socket only (`listen_addresses=''`), port 5599, data directory
`/Users/Dev/.claude/jobs/a12a4293/tmp/reh/pg`. Extensions `vector` + `pgcrypto` (real
`vector(768)` columns, not substituted). No production credential was used anywhere in
this rehearsal — the DDL was regenerated from `pg_catalog`/`information_schema` through
the same read-only connection used for the measurements.

DDL: all 34 tables with **exact production column types, NOT NULL flags and DEFAULTs**,
then **every** constraint, reproduced verbatim from `pg_get_constraintdef()`:
**34 PRIMARY KEY + 5 UNIQUE + 59 CHECK + 27 FOREIGN KEY = 125**.

**DETECTOR-0 — constraint parity.** Before any rollback is rehearsed, the replica's
constraint set is compared against production's, normalised as
`table|conname|pg_get_constraintdef`:

```
FK set  — line-by-line diff:   prod 27 lines, replica 27 lines, diff empty
DETECTOR-0 FK-PARITY: PASS (replica FK set == production FK set for the closure)

CHECK set — sha256 of the normalised, ordered definition list:
  production a72f8e4f731e61e86d794d91aedcde82453dc8e4fc2ebf1e217e0fd2b8f49ef1
  replica    a72f8e4f731e61e86d794d91aedcde82453dc8e4fc2ebf1e217e0fd2b8f49ef1
DETECTOR-0 CHECK-PARITY: PASS (byte-identical, 59 of 59)
```

Also measured: **0 user triggers** on any of the 34 tables (`pg_trigger` excluding
`tgisinternal`), so no trigger can alter rollback semantics in production but not in the
replica.

This is the check whose absence made the prior rehearsal hollow. It is proved capable
of failing in NC-2 (§4.6).

### §4.4 — The rollback procedure being rehearsed (this is the runbook, verbatim)

```
STEP 1  For each of the 20 write-set tables, in the order listed in §3.4:
            DELETE FROM <t> WHERE chart_id = '<CHART>';
        (Delete BEFORE restore, for every table without exception — including
         mimamsa_calibration_snapshot, which accretes and will PK-conflict otherwise.)
STEP 2  For each of the 20, in the SAME order (phala_mitigation first — it is the only
        write-set table that is an FK parent):
            \copy <t> FROM 'BEFORE_<t>.csv' CSV HEADER
STEP 3  COLLATERAL REPAIR — mandatory, not optional:
            CREATE TEMP TABLE _sank_before (LIKE phala_sankrama);
            \copy _sank_before FROM 'BEFORE_phala_sankrama.csv' CSV HEADER
            UPDATE phala_sankrama s SET mitigation_ref = b.mitigation_ref
              FROM _sank_before b
             WHERE b.sankrama_id = s.sankrama_id
               AND s.chart_id = '<CHART>'
               AND s.mitigation_ref IS DISTINCT FROM b.mitigation_ref;
STEP 4  Restore asset_throughput states for the 10 assets from BEFORE_asset_throughput.csv.
STEP 5  Run the detector (§4.5). A non-IDENTICAL result on ANY of the 25 tables means
        the rollback did not complete; do not proceed, do not attempt a second
        unrehearsed mutation, escalate.
```

STEP 3 exists because of what the rehearsal found (§5.1). It is the single most
important line in this packet.

### §4.5 — DETECTOR-1 (data identity) and the PASS result

For each of the 25 before-imaged tables: dump the chart-scoped rows with a **total**
ordering (`string_agg(t::text, E'\n' ORDER BY t::text)`) and hash. Compare against the
pristine baseline taken before the simulated rebuild.

Sequence actually executed on the replica:
1. Load the 34-table schema + all 111 constraints. DETECTOR-0: PASS.
2. Load a fixture exercising **every** FK edge the rebuild can touch — including
   `phala_sankrama.mitigation_ref` populated **4 of 4 non-null**. (Production is
   currently 0 of 2,510 non-null; the fixture deliberately populates it so the
   `ON DELETE SET NULL` path is *exercised*, not merely *present*. A rehearsal that
   only reproduced today's benign values would be another detector that cannot fail.)
3. Capture before-images + pristine hashes.
4. **Simulate the rebuild**: run the writers' own `DELETE FROM <t> WHERE chart_id=…`
   statements verbatim, plus `mi_gunanaka`'s non-deleting snapshot INSERT.
   Observed: `phala_sankrama.mitigation_ref` non-null went **4 → 0**;
   `mimamsa_calibration_snapshot` went **2 → 3**.
5. Execute the §4.4 rollback verbatim.
6. DETECTOR-1.

```
ROLLBACK_REHEARSAL_RESULT[full]: PASS
  phala_mitigation                 IDENTICAL  ad0782273b6c960b
  phala_pramana                    IDENTICAL  c129536adf0c52d2
  phala_phaladesa                  IDENTICAL  84cdc58f7652fc8b
  mimamsa_predictions              IDENTICAL  a6dbf5074431581d
  mimamsa_manifestation_sets       IDENTICAL  8b356071a1e9410f
  mimamsa_calibration              IDENTICAL  39bf9f265bd37666
  mimamsa_reliability              IDENTICAL  ac003f6669960e8d
  mimamsa_multipliers              IDENTICAL  9f9b324a0659d229
  mimamsa_calibration_snapshot     IDENTICAL  14d717ba3e133238
  mimamsa_qa_eval                  IDENTICAL  3d52865f7846ab95
  mimamsa_attribution              IDENTICAL  7ebb0eadaf665190
  mimamsa_discoveries              IDENTICAL  12464c1372a1720a
  mimamsa_load_bearing             IDENTICAL  7ad2309071ca40f1
  mimamsa_anchor_adjustment        IDENTICAL  e1aa9fc33e0d11b9
  mimamsa_convergence_adjustment   IDENTICAL  2b0c0d2d15584ef6
  mimamsa_fact_adjustment          IDENTICAL  aa2fae19d55aba5c
  mimamsa_signal_adjustment        IDENTICAL  9400f902937070d2
  mimamsa_manifestation_grammar    IDENTICAL  4456e45d00371b05
  mimamsa_insight_units            IDENTICAL  e62ec7b7d94f3547
  mimamsa_insight_embeddings       IDENTICAL  94aa262b9843ad6e
  phala_sankrama                   IDENTICAL  bf3cc13f272903d4
  phala_muhurta                    IDENTICAL  4072264707f3d7ea
  phala_anchors                    IDENTICAL  fd5131b631fc2321
  phala_sodhana                    IDENTICAL  08259340e1357f3f
  phala_suddha_sodhana             IDENTICAL  1693c2e169dbf17b
```

### §4.6 — Proof the rehearsal is load-bearing: three negative controls

A PASS is worth nothing unless a FAIL was reachable. Three deliberate defects were
introduced and each produced the FAIL it should:

**NC-0 — reproduce the F-146 defect shape.** Same run, `STEP 3` (collateral repair)
disabled. Scored two ways:

```
--- write-set-only verdict (the F-146-shaped rehearsal) ---
  20 of 20 write-set tables IDENTICAL
  0 write-set tables DIFFER  => a write-set-only detector reports PASS
--- FK-complete verdict (this packet's rehearsal) ---
  phala_sankrama  ***DIFFERS***  pristine=9f057047a175067a  now=31af32b68bcee17f
  ROLLBACK_REHEARSAL_RESULT[nc0]: FAIL
```

This is the whole argument for R-7(a) in one experiment: **a rehearsal scoped to the
writers' own output tables reports a clean 20/20 PASS on a rollback that permanently
destroyed real data in a table it never looked at.** The FK-complete rehearsal catches
it. (Historical note: this exact failure happened live on the first `full` run of this
packet's own rehearsal, before `STEP 3` was written — the detector caught the author's
own omission. That is recorded rather than tidied away.)

**NC-1 — incomplete rollback procedure.** `STEP 1`'s pre-restore DELETE omitted for
`mimamsa_calibration_snapshot` (the accreting table), `STEP 3` omitted:

```
ERROR:  duplicate key value violates unique constraint "mimamsa_calibration_snapshot_pk"
  mimamsa_calibration_snapshot     ***DIFFERS***
  phala_sankrama                   ***DIFFERS***
ROLLBACK_REHEARSAL_RESULT[negcontrol-partial]: FAIL
```

**NC-2 — DETECTOR-0 with one constraint dropped.**

```
DETECTOR-0 FK-PARITY: FAIL (as required)
< phala_sankrama|phala_sankrama_mitigation_ref_fkey|FOREIGN KEY (mitigation_ref)
    REFERENCES phala_mitigation(mitigation_id) ON DELETE SET NULL
```

### §4.7 — Honest limits of this rehearsal

Stated so nobody over-reads the PASS:

1. **Row volumes are representative, not production-scale.** The fixture holds tens of
   rows per table, not 61,523. The rehearsal proves the rollback procedure is *correct
   against the real FK topology*; it does not prove `\copy` throughput on a 61k-row CSV.
   That is a performance question, not a correctness one, and `\copy` at that size is
   routine.
2. **It rehearses the ROLLBACK, not the REBUILD.** No writer code was executed. The
   simulated "bad rebuild" is the writers' own DELETE statements, which is the worst
   realistic starting point for a rollback, but it is a simulation.
3. **Column types, constraints and FK actions are exact; indexes are not replicated.**
   Triggers were checked rather than assumed: `pg_trigger` (excluding `tgisinternal`)
   returns **0 user triggers** across all 34 tables in production, so there is nothing
   trigger-shaped that could behave differently there. Indexes affect restore speed,
   not correctness.
4. `charts`/`profiles`/`asset_registry` are terminal stubs by the §4.2 definition. If a
   future migration adds an FK from a write-set table *into* the application schema
   beyond them, this closure must be recomputed before reuse.

---

## §5 — Collateral analysis: what the rebuild touches that it does not write

### §5.1 — The live FK hazard: `phala_sankrama.mitigation_ref`

`ph_pratikara` opens with `DELETE FROM phala_mitigation WHERE chart_id = %s`. Production
carries:

```
phala_sankrama_mitigation_ref_fkey
  FOREIGN KEY (mitigation_ref) REFERENCES phala_mitigation(mitigation_id) ON DELETE SET NULL
```

`phala_sankrama` is written by `ph_sankrama`, which is **`lit` and out of plan**.
`phala_mitigation.mitigation_id` has `DEFAULT gen_random_uuid()` and is *not* in the
writer's INSERT column list, so **every rebuild mints entirely new mitigation ids**.
Therefore: the DELETE nulls `phala_sankrama.mitigation_ref` for every referencing row,
and the re-INSERT cannot restore those references, because the ids they pointed at no
longer exist. The linkage is destroyed silently — no error, no log line.

**Measured state: `phala_sankrama` has 2,510 rows for this chart and 0 of them carry a
non-null `mitigation_ref`.** The hazard is therefore **currently inert** on this chart.
That is a measurement, not a guarantee: it must be **re-measured immediately before
dispatch** (§12 abort condition A4). The rehearsal deliberately populated the column so
the path was exercised anyway.

### §5.2 — Other FK edges, and why each is safe

| edge | action | effect of the rebuild | disposition |
|---|---|---|---|
| `phala_mitigation.linked_anchor_id → phala_anchors` | SET NULL | 536/536 non-null; `phala_anchors` is out of plan and untouched, so all parents remain | safe; restore requires anchors present — witnessed in before-image |
| `phala_mitigation.initiation_muhurta_ref → phala_muhurta` | SET NULL | 0/536 non-null (measured) | inert; witnessed |
| `phala_pramana.anchor_id → phala_anchors` | CASCADE | 139/139 non-null; parents untouched | safe |
| `phala_sankrama.source_anchor_id → phala_anchors` | CASCADE | parents untouched | safe |
| `phala_sodhana`, `phala_suddha_sodhana` `→ phala_anchors` | CASCADE | parents untouched | safe; witnessed |

**The 17 `mimamsa_*` write-set tables carry no foreign keys at all** — not even
`chart_id → charts`. Their rollback is pure delete-then-restore. This is measured from
`pg_constraint`, and it is why the FK risk in this packet is entirely concentrated in
the three `phala_*` assets.

### §5.3 — Soft (non-FK) references, and the one that matters most

`mimamsa_predictions` is fully rewritten by `mi_bhavisya`. Six tables hold a
`prediction_id` column without an FK: `brahma_prospective_ledger`,
`mimamsa_adjudication_log`, `mimamsa_intervention_ledger`, `mimamsa_journal`,
`mcp_prediction_outcomes`, `prashna_followup_schedule`. If prediction ids churned, the
outcome→prediction linkage — the L5 calibration loop, which is the one thing in this
system that cannot be regenerated — would break.

**They do not churn, and this is proved rather than hoped:**

- `mi_bhavisya.py` derives `prediction_id = f"pred_{anchor_id}"` where `anchor_id` comes
  from `SELECT * FROM phala_anchors WHERE chart_id = %s ORDER BY anchor_id`.
- `phala_anchors` is written by `ph_nimitta`, which is **`lit`, out of plan, and not
  rebuilt**. Its 139 rows and their `anchor_id`s are unchanged by this packet.
- Measured: **139 of 139** current `mimamsa_predictions` rows satisfy
  `prediction_id = 'pred_' || anchor_id` against a currently-existing `phala_anchors`
  row. Prediction ids are stable across this rebuild.

Measured contents of the soft-reference tables for this chart:
`mimamsa_adjudication_log` 0, `mimamsa_intervention_ledger` 0, `mimamsa_journal` 0,
`mcp_prediction_outcomes` 0 (all charts), `prashna_followup_schedule` 0 (all charts),
`brahma_prospective_ledger` **19 rows** — of which **0** currently resolve to a
`mimamsa_predictions.prediction_id` (that table's `prediction_id` is `uuid`, while
`mimamsa_predictions.prediction_id` is `text 'pred_<uuid>'`; they are different id
namespaces). **This is a pre-existing condition. The rebuild neither creates nor
repairs it**, and this packet makes no claim about it beyond recording that it was
checked. (Candidate follow-up finding; not raised here to avoid scope drift.)

`mimamsa_discoveries` is rewritten by `mi_pariksha`; `phala_anchors.discovery_id` is a
`uuid` column while `mimamsa_discoveries.discovery_id` is `text` — again separate
namespaces, no linkage to break.

**Non-regenerable data at risk in this packet: none identified.** Every table in the
write set is a deterministic derivation of upstream `lit` assets.

---

## §6 — Bounded scope (§19.2 clause 4)

- **Charts:** exactly one — `482012f1-710e-4a25-994a-93821f5871aa`. No other `chart_id`
  is written. `1c826d5a…` and `cb73cd3d…` are explicitly out (§0.3).
- **Assets:** exactly the ten of §0.1. Not `bo_upaya` (already `lit`), not
  `ga_panchanga` (§0.2), not `mi_bhara` (F-71 — needs a *global registry* change, a
  different consent surface), not `ka_kshetra` (F-141, under an owner ruling with three
  unmet conditions), not `mi_abhilekha`/`mi_seva` (§10.3).
- **Tables:** the 20 of §3.2 are written; the 5 of §3.3 are read and, for
  `phala_sankrama` only, repaired on rollback. Nothing else.
- **Mechanism:** `build_runs` + `build_run_assets` INSERT, then
  `gcloud run jobs execute brahma-build-pipeline-job --args=^:^--run-id:<run_id>`.
  The plan array is the explicit ten-asset list. `_schedule_parallel` seeds already-`lit`
  out-of-plan deps as satisfied, so no dependency is silently pulled into the run.
- **`action` MUST be `rebuild`, not `build`.** `build` only touches
  `dormant|error|incomplete` and silently skips `lit` assets in both the TS planner and
  the Python scheduler. Seven of the ten are currently `error` and three are `stale`, so
  `build` would appear to work while skipping the three `phala_*` assets — the §N.8
  "reported success while doing nothing" class. Use `rebuild`.

---

## §7 — Zero credential / permission / schema-destructive changes (§19.2 clause 5)

- **Credentials:** none created, rotated, read or written **by the authoring pass**.
  This packet was produced entirely over an existing read-only connection; no secret was
  fetched from Secret Manager, and the rehearsal cluster uses `--auth=trust` on a local
  Unix socket with no production secret anywhere in it. The executor will need the
  normal pipeline credential to run `\copy` — reading it is permitted; rotating or
  writing it is not.
- **Permissions:** no `GRANT`/`REVOKE`/`ALTER ROLE`/IAM change, at authoring or execution.
- **Schema:** no `CREATE`/`ALTER`/`DROP` against production, at authoring or execution.
  All DDL in this packet ran on the throwaway cluster, which is destroyed afterwards.
  No migration is applied, and none is required — `scored_count` is already present.
- **Global registry:** untouched. In particular `asset_registry.writer_timeout_seconds`
  is **not** modified (that is F-71's separate, global-scope item).
- **Namespaces:** PARIPRAŚNA / EKAVĀKYATĀ untouched.
- **Idempotency:** nine of ten writers use the L1+ standard (§N.3) per-chart
  delete-then-insert. `mi_gunanaka`'s `mimamsa_calibration_snapshot` is the documented
  exception (§3.1) and accretes one row per run by design.

---

## §8 — Execution runbook

```
0.  Re-pin: confirm the deployed image is still 25c8aaacd (or a later ancestor of main
    that still contains the §2 greps). If it moved, re-run §2 before anything else.
1.  Re-run the §1 quiescence proof. All five must read 0. Record the values.
2.  Re-measure the §3.2 / §3.3 row counts. Any deviation → ABORT (§12 A1).
3.  Re-measure `phala_sankrama` non-null `mitigation_ref` (§5.1). If > 0 → ABORT (§12 A4)
    and re-plan: the rollback then requires STEP 3 to be load-bearing on real data.
4.  Capture before-images per §3.4 (25 tables + asset_throughput). Verify each CSV's
    row count equals step 2's measurement.
5.  Run the §9 verification predicates. Record the BEFORE column.
6.  Dispatch ONE run:
      action = 'rebuild'
      plan   = ph_pratikara, ph_pramana, ph_phaladesa, mi_bhavisya, mi_pramana,
               mi_pariksha, mi_gunanaka, mi_adhilepa, mi_sambandha, mi_darshana
    (Dependency order is resolved by the scheduler; plan order is only a tiebreak.)
7.  Block until the run reaches a terminal state. READ THE JOB LOGS — a run can end
    'complete' with assets BLOCKED. Every one of the ten must reach `lit`.
8.  Re-run the §9 predicates. Record the AFTER column and compare against §10.
9.  If any ABORT condition (§12) fired at any point: execute §4.4 STEPS 1-5 verbatim.
10. Record the outcome in the ledger. Note explicitly which findings this does and does
    not close (§13).
```

---

## §9 — Verification predicates (each states a condition it could fail)

### V1 — F-104: `leakage_status` is honest

```sql
SELECT count(*) FILTER (WHERE leakage_status='clean')        AS clean,
       count(*) FILTER (WHERE leakage_status='not_assessed') AS not_assessed,
       count(*)                                              AS total
  FROM mimamsa_insight_units WHERE chart_id = '<CHART>';
```
**PASS iff `clean = 0` AND `not_assessed = total` AND `total > 0`.**
Current: `clean=115, not_assessed=0, total=115` → FAIL (the defect).
Note the strengthening: the original predicate was only `clean = 0`, which an empty
table would satisfy. `not_assessed = total AND total > 0` cannot be satisfied by a
writer that produced nothing.

### V2 — F-35: no unearned `empirical`, **and the tier was actually reachable**

```sql
SELECT count(*) FILTER (WHERE evidence_grade='empirical')                            AS empirical,
       count(*) FILTER (WHERE evidence_grade='empirical' AND coalesce(scored_count,0)<5)
                                                                                     AS unearned,
       count(*) FILTER (WHERE evidence_grade='assignment_only')                      AS assignment_only,
       count(*) FILTER (WHERE scored_count > 0)                                      AS any_scored,
       count(*)                                                                      AS total
  FROM mimamsa_manifestation_grammar WHERE chart_id = '<CHART>';
```
**PASS iff `unearned = 0` AND `total > 0`.**
Current: `empirical=7, unearned=7, assignment_only=0, any_scored=0, total=24` → FAIL.

**`any_scored` is a discriminator, not a pass condition — and it is expected to be 0.**
Read §11.1 before interpreting a V2 PASS. A PASS here after the rebuild means "no row
claims an empirical grade it did not earn"; it does **not** mean "grades are now
earned," because F-147 makes the empirical tier unreachable. Reporting V2 PASS as
"F-35 resolved, grades are earned" would be a false claim.

### V3 — F-143 residual (recorded either way, not a gate on this packet)

```sql
SELECT count(*) FILTER (WHERE evidence_grade='empirical')  AS empirical,
       count(*) FILTER (WHERE evidence_grade='structural') AS structural,
       count(*) FILTER (WHERE evidence_grade='prior_only') AS prior_only,
       count(*)                                            AS total
  FROM mimamsa_insight_units WHERE chart_id = '<CHART>';
```
Current: `empirical=31, structural=31, prior_only=53, total=115`.
The F-143 fix is deployed (§2), so the rebuild should move retrodiction-class rows to
`structural` and gate `emergent_law` rows on `evidence_refs.n_scored_matches >= 5`.
Expect `empirical` to fall (§10.2). This is F-143's *data* half, which its ledger entry
explicitly assigned to this rebuild.

### V4 — Build state: all ten `lit`, nothing regressed

```sql
SELECT asset_id, state, rows_written, last_built_at
  FROM asset_throughput
 WHERE chart_id='<CHART>' AND asset_id IN (<the ten>)
 ORDER BY asset_id;
SELECT count(*) FROM asset_throughput
 WHERE chart_id='<CHART>' AND state='stale'
   AND asset_id NOT IN ('bo_pramana_mapa','bo_samvada','ka_kshetra','mi_abhilekha',
                        'mi_seva','mi_sankalpa');
```
**PASS iff all ten read `lit` AND the second query returns 0** (no asset outside the
already-stale set was newly staled).

### V5 — Collateral integrity

```sql
SELECT count(*) FILTER (WHERE mitigation_ref IS NOT NULL) AS refs_intact, count(*) AS total
  FROM phala_sankrama WHERE chart_id='<CHART>';
SELECT (SELECT count(*) FROM phala_anchors WHERE chart_id='<CHART>') AS anchors,
       (SELECT count(*) FROM phala_muhurta WHERE chart_id='<CHART>') AS muhurta,
       (SELECT count(*) FROM phala_sodhana WHERE chart_id='<CHART>') AS sodhana,
       (SELECT count(*) FROM phala_suddha_sodhana WHERE chart_id='<CHART>') AS suddha;
```
**PASS iff `refs_intact` equals its BEFORE value (0 today) AND anchors/muhurta/
sodhana/suddha equal 139/134/97/139.** Any change means a cascade reached a table this
packet does not write.

### V6 — Prediction-id stability (protects the calibration loop)

```sql
SELECT count(*) AS preds,
       count(*) FILTER (WHERE p.prediction_id IN
         (SELECT 'pred_'||a.anchor_id::text FROM phala_anchors a WHERE a.chart_id=p.chart_id))
         AS anchored
  FROM mimamsa_predictions p WHERE p.chart_id='<CHART>';
```
**PASS iff `anchored = preds = 139`.** A drop means anchor ids moved, which they must
not, since `ph_nimitta` is not in the plan.

---

## §10 — Expected after-state (deterministic predictions, stated in advance)

Stating these before execution is what makes an unexpected result detectable.

### §10.1 — Row counts

Each writer is a deterministic function of upstream `lit` assets, none of which change
in this run except the in-plan ones. Expect the write-set counts of §3.2 to be
**materially reproduced**, with these specific movements:

- `mimamsa_calibration_snapshot`: **4 → 5** (one new accreted row; the only table whose
  count must increase).
- `mimamsa_insight_embeddings`: currently 0; expected to remain 0 unless embedding
  generation is separately enabled. A jump to 115 is not an error, but should be noted.
- Everything else: same order of magnitude. A change of more than ±10% in any table is
  worth a second look, not an automatic abort — these are deterministic recomputations
  from unchanged inputs plus a changed `bo_upaya` (which `ph_pratikara` reads).

### §10.2 — Value changes (the point of the exercise)

| surface | before (measured) | after (predicted) |
|---|---|---|
| `mimamsa_insight_units.leakage_status` | `clean` × 115 | **`not_assessed` × 115** — the writer contains no `'clean'` literal |
| `mimamsa_manifestation_grammar.evidence_grade` | `empirical` 7, `prior_only` 17 | **`assignment_only` 7, `prior_only` 17, `empirical` 0** — the 7 are exactly the rows with `opportunity_count ≥ 5`; with `scored_count` forced to 0 by F-147 they fall to the `opp ≥ 5` tier |
| `mimamsa_manifestation_grammar.scored_count` | 0 × 24 | **0 × 24** (unchanged — F-147, §11.1) |
| `mimamsa_manifestation_grammar.fire_count` / `channel_propensity` | 0 / 0.0 | **0 / 0.0** (unchanged — same F-147 case bug on the `fire` comparison) |
| `mimamsa_insight_units.evidence_grade` | `empirical` 31, `structural` 31, `prior_only` 53 | `empirical` **falls**, `structural`/`prior_only` rise — the F-143 fix regrades retrodiction rows `structural` and gates `emergent_law` on `n_scored_matches ≥ 5`, which is 0 across all 71 discoveries |
| `phala_mitigation.mitigation_id` | 536 ids | **536 entirely new ids** (`gen_random_uuid()` default) |
| `phala_pramana.pramana_id`, `phala_phaladesa.phaladesa_id` | | **all new ids**, same reason |
| `mimamsa_predictions.prediction_id` | 139 `pred_<anchor>` | **identical 139 ids** (§5.3) |

If `evidence_grade='empirical'` appears on any `mimamsa_manifestation_grammar` row after
the rebuild, something is wrong with this analysis — investigate before recording a
result.

### §10.3 — Post-run stale cascade: two assets, both already stale

The recursive downstream closure of the ten, excluding the ten, is exactly
**`mi_abhilekha` and `mi_seva`** — and both are **already `stale`** with
`rows_written = 0`. **The run therefore flips zero assets from `lit` to `stale`.** This
is the cleanest bounded-scope property in the packet and it is measured, not asserted.

Not widening the plan to 12 is a deliberate choice: the ledger's declared scope is ten,
both assets currently produce no rows, and adding assets to a GA-3 plan after the packet
is written is the exact drift F-104 was re-parked for. Recommend a named follow-up
("bring `mi_abhilekha`/`mi_seva` to `lit`") rather than an in-flight amendment.

The following remain `stale`/`error` after this run and are **not** claimed to be fixed:
`bo_pramana_mapa`, `bo_samvada` (`stale`, from the `bo_upaya` cascade),
`ka_kshetra` (`stale`, under PAR-R-9/R-5/R-6 — explicitly not touched),
`mi_bhara` (`error`, F-71), `mi_sankalpa` (`dormant`).

---

## §11 — Known carried defects; what a PASS here will and will not mean

### §11.1 — F-147 makes F-35's deployed fix inert. THIS IS THE PACKET'S MOST IMPORTANT DISCLOSURE.

`mi_sambandha.py` (deployed commit, line ~83):

```python
verdict = row.get("composite_verdict") or ""
if verdict in ("confirmed", "partial", "denied"):
    counts[key]["scored"] += 1
if verdict in ("confirmed", "partial") and ch_fired == channel_id:
    counts[key]["fire"] += 1
```

Measured production values of `mimamsa_calibration.composite_verdict` (all charts):
**`UNRESOLVED` 25, `PARTIAL` 23, `REFUTED` 7, `CONFIRMED` 2.** Uppercase — and
`REFUTED`, not `denied`. Two independent mismatches: case, and vocabulary. Therefore
after the rebuild `scored_count` is **0 for every row**, `fire_count` is **0 for every
row**, `channel_propensity` is **0.0 for every row**, and `evidence_grade='empirical'`
is **unreachable**.

Consequences, stated plainly:

1. The rebuild **does** deliver F-35's stated goal — no row will claim an `empirical`
   grade it did not earn. The 7 currently-unearned rows fall to `assignment_only`. This
   is a real honesty improvement and the direction is fail-closed (under-grades, never
   over-grades).
2. The rebuild **does not** make the grading tier *work*. The empirical/assignment_only
   distinction F-35 built collapses to "assignment_only or worse, always."
3. Therefore **V2's PASS is a fail-closed PASS, not a functional one.** Reading it as
   "F-35 resolved, grades are earned" would be a §N.8 earned-signal violation committed
   by the verification layer of the very packet written to enforce §N.8.

**This is a native decision, not an executor's call (§14 D2):** run now and accept an
honest-but-degenerate grading tier, or land F-147's one-line fix first and rebuild once.
The engineering recommendation is to land F-147 first — it is a small, well-scoped
change to a file already in the plan's blast radius, and rebuilding twice costs a second
GA-3 packet.

### §11.2 — F-143's data half rides along, and that is intended

`mi_darshana`'s discovery-grading fix (PR #1414) is deployed but its 20 mis-graded rows
on this chart have never been rewritten. This rebuild rewrites them. F-143 is already
`SERVICE_CLOSED` for the code defect; its ledger entry assigns the data half to "the
broader chart-482012f1 rebuild scope (see F-104/F-35 next_action)" — i.e. here.
Record the V3 movement in the execution log; do not claim it as a new finding.

### §11.3 — What this packet does not touch

`ka_kshetra` (11,069,325 `rows_written` against 8,599,775 actual — the PAR-R-9 preserved
specimen) is **not** in the ten assets' closure and is not rebuilt. Its `state` was
already flipped to `stale` by the earlier `bo_upaya` cascade and R-5 ruled that the
honest disposition. Nothing here re-touches it.

---

## §12 — Abort conditions (any one → do not dispatch; if mid-flight → §4.4 rollback)

- **A1** Any §3.2/§3.3 row count differs from this packet's measurement at capture time.
- **A2** Any of the five §1 quiescence conditions is non-zero at dispatch time.
- **A3** Any of the 15 out-of-plan dependencies (§0.1) is not `lit` at dispatch time.
- **A4** `phala_sankrama` shows any non-null `mitigation_ref` for this chart (§5.1). The
  rollback then has real collateral to repair and the risk profile changes — re-plan,
  do not proceed on this packet's authority.
- **A5** The deployed image no longer satisfies the §2 greps.
- **A6** The run ends in any state other than every one of the ten reading `lit` — in
  particular an asset reading `error` with a `BLOCKED:` message. Do not re-dispatch
  ad hoc; that is how the previous attempt grew four runs deep.
- **A7** Any table outside the 20 write-set tables changes row count (V5).
- **A8** V6 returns `anchored < preds`. Prediction ids moved; stop immediately, the
  calibration linkage is at risk.

---

## §13 — What this execution closes, and what it does not

**Closes (data half, canonical chart only):**
- F-104 — `mi_darshana` `leakage_status` becomes honest. Terminal for this chart.
- F-143 — data half; code half already `SERVICE_CLOSED`.

**Advances but does NOT close:**
- F-35 — canonical-chart half only. Its system-wide scope (chart `1c826d5a…`) remains,
  and per §11.1 its grading tier does not actually function until F-147 lands. F-35
  should **not** be flipped terminal on this execution.

**Unaffected, still parked:**
- F-63 (`ga_panchanga`, L1 root, 53-asset cascade — §0.2)
- F-71 (`mi_bhara` timeout — a global `asset_registry` row, different consent surface)
- F-52 (`ka_gochara_v3_century_materialize` — a different chain entirely; per standing
  owner policy 2026-08-21, code-only fixes for gochara-adjacent findings, no rebuild)
- F-62 (moolatrikona D1 rows — has its own packet)
- F-141 (`ka_kshetra` — three unmet R-6 conditions)
- F-147 (the case/vocabulary bug — needs its own PR)

---

## §14 — Native decisions required before this packet may execute

**D1 — Authorise the 10-asset scope.** F-104's ledger entry makes this "explicitly a
native-authorized-scope decision, not a routine execution." The scope is bounded (one
chart, ten assets, twenty tables, zero new stale assets, zero credential/permission/
schema change) and the two R-7 clauses are discharged. What needs authorising is the
size, not the safety.

**D2 — Sequencing against F-147.** Run now and accept a fail-closed but degenerate
grading tier (§11.1), or land F-147 first and rebuild once. Recommendation: **F-147
first.** It is one comparison in a file already inside this plan's blast radius, and it
converts a "grades stopped lying" outcome into a "grades work" outcome for the same
single execution.

**D3 — `mi_abhilekha` / `mi_seva`.** Leave at ten (recommended — they are already stale
and produce no rows) or widen to twelve. Do not decide this mid-flight.

**D4 — F-35's second chart.** Confirm that `1c826d5a…` (Abhinandan) is a separate
consent surface requiring its own authorisation, as this packet assumes.

---

## §15 — Artifacts produced by this authoring pass

Rehearsal materials (throwaway local cluster, no production data, no credential) live
under the authoring agent's scratch directory:
`/Users/Dev/.claude/jobs/a12a4293/tmp/REHEARSAL_ARTIFACTS/` (`sql/01_tables.sql`,
`sql/02_constraints.sql`, `sql/03_fixture.sql`, `rehearse.sh`, `rehearse_nc0.sh`,
`out/PROD_fk.txt`, `out/REPLICA_fk.txt`, `out/full/`, `out/nc0.log`,
`out/negcontrol-partial/`) — job-scratch, not durable; copy into
`verification_artifacts/PARISESA_V4_GA3_F104_F35_<UTCSTAMP>/REHEARSAL/` before
execution if this packet is picked up for a real run, so the rehearsal is reproducible
by a later reviewer rather than merely reported.

---

*Authored 2026-08-21 under R-7-amended GA-3 discipline. Not executed. Every number in
this document was measured against live production over a read-only connection or
produced by the rehearsal described in §4; none was carried over from prior
documentation without re-measurement — that being the whole point of R-7(b).*
