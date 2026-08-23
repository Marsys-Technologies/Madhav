---
artifact: M0_EXIT_SCORECARD
version: 1.0
status: LIVE-MEASUREMENT
task: M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42)
built_by_task: M0-T17
readings: 7
generated: 2026-08-23T23:19:36.402996+00:00
generator: 00_ARCHITECTURE/control/m0_exit_scorecard.py
---

# NIRMĀṆA M0 — Exit-Criteria Scorecard v1.0

**Measured:** 2026-08-23T23:19:28.106490+00:00 → 2026-08-23T23:19:36.402996+00:00 (UTC)  
**Branch / commit:** `campaign/nirmana-autonomous` @ `4d1b679d54f4`  
**Database access:** READ-ONLY (default_transaction_read_only=on; SELECT only)  
**Regenerate:** `python3 00_ARCHITECTURE/control/m0_exit_scorecard.py`  
**Status:** measurement only. This document certifies nothing and closes nothing (I16 / charter H7). PARĪKṢAKA decides; M0-T10 re-runs the generator at freeze time rather than trusting this snapshot.

## 0 — Tally, then and now

**then** = `reading 1 — M0-T17 first measurement`, 2026-08-23T05:05:59.484414+00:00 @ `01397f9216de`  
**now** = `reading 7 — M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42)`, 2026-08-23T23:19:36.402996+00:00 @ `4d1b679d54f4`

| status | then | now | Δ | meaning |
|---|--:|--:|--:|---|
| PASS | 0 | 2 | +2 | a detector ran and returned zero |
| FAIL | 6 | 6 | — | a detector ran and returned non-zero |
| NOT-MEASURABLE | 3 | 3 | — | **no detector exists that could return non-zero. Not a pass** (CLAUDE.md §N.8) |
| BLOCKED | 3 | 1 | -2 | a detector exists but cannot run yet; the blocker is named per row |

**2 of 12 criteria are satisfied by a detector's output.** The other 10 are not, and none of them is green.

**Criteria whose PASS rests on a NON-DURABLE repair: 1 (11_domain_and_rung_present). Criteria passing on inputs a re-seed would move (EXPOSED): 0.** A repair is *durable* only if the column it wrote is absent from `asset_registry_seed.ts`'s `ON CONFLICT (asset_id) DO UPDATE SET` list; columns in that list are restored from `EXCLUDED` on the next seed run. Contract rules resting on such a repair: `C-05, C-14, C-18`. Rules that a projected re-seed makes start firing again: `C-05, C-14, C-18`. §3b measures all of this, projects each PASSing rule forward through a simulated re-seed, and names every cell that would move.

### At a glance — then → now

| # | criterion | then | now | measured | durability | blocker |
|---|---|---|---|--:|---|---|
| 1 | three-way diff (registry vs `@register` vs seed) = 0 | FAIL | **FAIL** | `5` | n/a — not passing | — |
| 2 | contract violations per kind = 0 | NOT-MEASURABLE | **NOT-MEASURABLE** | `84` | n/a — not passing | rules C-25, C-26, C-27 have NO detector at all (contract §8) and must never read green |
| 3 | prefix mismatches = 0 | FAIL | **FAIL** | `1` | n/a — not passing | — |
| 4 | dangling or DRAFT-targeted edges = 0 | FAIL | **FAIL** | `3` | n/a — not passing | — |
| 5 | multi-producer partitions = 0 | NOT-MEASURABLE | **NOT-MEASURABLE** | `—` | n/a — not passing | NO DETECTOR EXISTS. The criterion asserts that no two producers write the same (table × generati… |
| 6 | throughput rows on inactive assets = 0 | BLOCKED | **BLOCKED** | `3` | n/a — not passing | CHARTER §2 P1 COLLISION — the only offender is `ka_gochara_sweep`, the charter's named unrecover… |
| 7 | retired assets without a `data_disposition` = 0 | BLOCKED | **FAIL** *(moved)* | `1` | n/a — not passing | — |
| 8 | active assets with neither build coverage nor a dead flag = 0 | NOT-MEASURABLE | **NOT-MEASURABLE** | `—` | n/a — not passing | NO 'DEAD FLAG' FIELD IS DEFINED. asset_registry has no column that designates a registered-but-d… |
| 9 | unresolved zero-consumer findings = 0 | FAIL | **PASS** *(moved)* | `0` | durable | — |
| 10 | CI guard merged and **blocking** | FAIL | **FAIL** | `{"guard_scripts_found": 2, "workflow_invocations_fou…` | n/a — not passing | — |
| 11 | every asset carrying `domain` and `rung` *(v4.1)* | BLOCKED | **PASS** *(moved)* | `0` | **NON-DURABLE** | — |
| 12 | the §11 CI domain-coherence assertion green *(v4.1)* | FAIL | **FAIL** | `{"assertion_exists": true, "assertion_wired_to_a_wor…` | n/a — not passing | — |

Every reading this generator has taken is retained in `m0_exit_scorecard.json` under `_meta.reading_history` (oldest first), so a re-run adds a reading rather than erasing the one it replaces:

| reading | task | measured | commit | PASS | FAIL | NOT-MEASURABLE | BLOCKED |
|---|---|---|---|--:|--:|--:|--:|
| reading 1 — M0-T17 first measurement | M0-T17 | 2026-08-23T05:05:59.484414+00:00 | `01397f9216de` | 0 | 6 | 3 | 3 |
| reading 2 — M0-T27 (re-measurement) | M0-T27 (re-measurement) | 2026-08-23T06:20:44.013647+00:00 | `ee93b76e8a57` | 1 | 7 | 3 | 1 |
| reading 3 — M0-T32 (re-measurement 3) | M0-T32 (re-measurement 3) | 2026-08-23T07:23:54.296317+00:00 | `df78d1aa3aa4` | 1 | 7 | 3 | 1 |
| reading 4 — M0-T36 (re-measurement 4 — post V-8/V-9/V-10/V-11, post D-29/D-30/D-31) | M0-T36 (re-measurement 4 — post V-8/V-9/V-10/V-11, post D-29/D-30/D-31) | 2026-08-23T08:00:26.645600+00:00 | `326e4cb372b5` | 1 | 7 | 3 | 1 |
| reading 5 — M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | 2026-08-23T12:26:07.136461+00:00 | `ac16535d1b67` | 2 | 6 | 3 | 1 |
| reading 6 — M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | 2026-08-23T21:08:40.089548+00:00 | `68cb017d69da` | 2 | 6 | 3 | 1 |
| reading 7 — M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | M0-T46 (re-measurement 5 — applies D-38/D-39/D-40/D-41/D-42) | 2026-08-23T23:19:36.402996+00:00 | `4d1b679d54f4` | 2 | 6 | 3 | 1 |

### Did anything move while this ran?

A migration wave was running concurrently, so every load-bearing quantity was read again at the end of the run:

| quantity | at start | at end |
|---|--:|--:|
| `asset_registry` rows | 128 | 128 |
| throughput rows on inactive assets | 3 | 3 |
| contract columns added/removed mid-run | — | none |

**Anything moved: no.** Contract columns present at end of run: `{'domain': True, 'rung': True, 'data_disposition': True, 'superseded_by': True}`.

### What changed since the previous run of this generator

Previous run: `2026-08-23T21:08:40.089548+00:00`. no criterion changed status or value since the previous run.

Filesystem-sourced criteria (10 and 12) can move between runs without any database change, because sibling tasks are authoring the guards they look for. The block above is where that shows up; the table above it covers database movement inside a single run.

Most recent rows of `_migrations_applied`:

- `591_nirmana_m0_partition_and_dead_flag_columns.sql` — 2026-08-23 13:58:56.247380+00:00
- `590_nirmana_m0_catalogue_contract_columns.sql` — 2026-08-23 05:36:13.833986+00:00
- `589_drop_orphaned_protection_functions.sql` — 2026-08-23 05:34:38.787119+00:00
- `588_remove_asset_build_protection.sql` — 2026-08-23 05:33:15.527766+00:00
- `588_samiksha_digest_journal.sql` — 2026-08-22 23:42:20.550183+00:00

---

## 1 — The twelve criteria

### 1 · three-way diff (registry vs `@register` vs seed) = 0

**Status: FAIL → FAIL**  
**Measured value:** `5` → `5`  

**Detector**

```
this script: SELECT asset_id FROM asset_registry  ×  AST scan of @register('<id>') under platform/python-sidecar (production files only, asset-shaped ids only)  ×  regex `^\s*asset_id:` over platform/scripts/seed/asset_registry_seed.ts read as TEXT. Violations = ids not present in all three.
```

**Where the number came from:** this script's own live query. A sibling artifact — CENSUS_REPORT.md / census.json (M0-T1) — reports: registry_only 1 · registry+seed_not_decorator 4 · all other buckets 0 → 5 ids not in all three.

<details><summary><code>counts</code></summary>

```json
{
 "registry": 128,
 "production_decorators": 123,
 "seed": 127,
 "in_all_three": 123
}
```

</details>

<details><summary><code>buckets</code></summary>

```json
{
 "registry_only": [
  "bg_gochara_citation_resolution"
 ],
 "decorator_only": [],
 "seed_only": [],
 "registry+decorator_not_seed": [],
 "registry+seed_not_decorator": [
  "bg_ephemeris_engine",
  "bg_panchanga",
  "bg_sarvatobhadra_grid",
  "lel_events"
 ],
 "decorator+seed_not_registry": []
}
```

</details>

---

### 2 · contract violations per kind = 0

**Status: NOT-MEASURABLE → NOT-MEASURABLE**  
**Measured value:** `227` → `84`  

**Detector**

```
this script: every §8 detection SQL of 00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md, run live; plus C-13b (DFS) and C-23 (AST) implemented here.
```

**Blocked by / why this is not a pass:** rules C-25, C-26, C-27 have NO detector at all (contract §8) and must never read green

**Note:** D-42 (ADHIKĀRIN, 2026-08-23T11:04:17Z) reclassified C-28's framing: asset_throughput.state='lit' is a claim, not evidence, and build_run_assets is authoritative for 'was this asset built'. D-94 (2026-08-23T18:46:28Z) SUPERSEDES D-42 part 3 and confirms the DATA_KINDS-scoped `estimated_seconds` question is the authoritative C-28 (31 rows, imported from check_asset_catalogue_contract.py::c28() per D-94 part 7 — see _c28_via_contract_module). measured_value HERE changed accordingly (was 32 under this file's own now-removed unfiltered SQL; is 31 under the imported, narrowed, authoritative definition) — that narrowing is authorised ONLY because D-94 requires it to land atomically with a NEW all-asset-kind rule (X-06 in check_asset_catalogue_contract.py) that covers exactly what the narrowing drops. THIS criterion's measured_value does NOT include X-06's count — X-06 is reported by that module's own --live run, not folded into this file's contract_violations total. A reader treating this criterion's number as 'all unearned-lit assets, every kind' would be wrong in exactly the way D-94 found; the cross-kind figure is check_asset_catalogue_contract.py --live's X-06 row.

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>violations_by_asset_kind</code></summary>

```json
{
 "data": 69,
 "artifact": 0,
 "service": 15,
 "source": 0
}
```

</details>

<details><summary><code>failing_rules</code></summary>

```json
[
 "C-01=1",
 "C-02=1",
 "C-03=1",
 "C-04=9",
 "C-06=1",
 "C-07=4",
 "C-08=1",
 "C-11=3",
 "C-15=6",
 "C-17=4",
 "C-20=3",
 "C-21=19",
 "C-28=31"
]
```

</details>

<details><summary><code>never_checkable_rules</code></summary>

```json
[
 "C-25",
 "C-26",
 "C-27"
]
```

</details>

---

### 3 · prefix mismatches = 0

**Status: FAIL → FAIL**  
**Measured value:** `1` → `1`  

**Detector**

```
C-01 detection SQL (asset_id prefix vs layer), run live
```

```sql
SELECT asset_id, layer FROM asset_registry WHERE asset_kind <> 'source' AND left(asset_id,3) IS DISTINCT FROM (CASE layer WHEN 'brahmagyan' THEN 'bg_' WHEN 'ganita' THEN 'ga_' WHEN 'bodha' THEN 'bo_' WHEN 'kala' THEN 'ka_' WHEN 'phala' THEN 'ph_' WHEN 'mimamsa' THEN 'mi_' END) ORDER BY asset_id
```

**Where the number came from:** this script's own live query. A sibling artifact — CENSUS_REPORT.md §6 (M0-T1) and ASSET_CATALOGUE_CONTRACT §6 rule C-01 — reports: 1 (`lel_events`).

<details><summary><code>rows</code></summary>

```json
[
 {
  "asset_id": "lel_events",
  "layer": "mimamsa"
 }
]
```

</details>

---

### 4 · dangling or DRAFT-targeted edges = 0

**Status: FAIL → FAIL**  
**Measured value:** `3` → `3`  

**Detector**

```
C-12 (dangling: dep with no registry row) + C-11 (CURRENT depending on a non-CURRENT, non-source asset), both run live
```

**Note:** D-38 (ADHIKĀRIN, 2026-08-23T09:24:48Z) ruled Phase 0.8b's general disposition REMAIN DRAFT — a decision, not a promotion — for any DRAFT-but-served asset no rung clause names by asset_id for promote-or-retire. None of the three C-11 dependencies (ga_vichara R1, ka_dasha_kala R3, ka_sangam R3) is named by any such clause, so bulk promotion in M0 is refused for all three and the status here stays FAIL: the detector still returns 3, and D-38 explicitly forbids reading REMAIN-DRAFT as a repair. This criterion's own deferral (deferred to R1/R3, ruling D-38) is recorded in M0_DEFERRAL_REGISTER_v1_0.md, not in this scorecard's status field — see criteria 3 and 7 for the same convention.

**Where the number came from:** this script's own live query. A sibling artifact — DAG_AUDIT_v1_0.md §1–§2 (M0-T7) — reports: dangling 0 · CURRENT→DRAFT 3 → 3.

<details><summary><code>components</code></summary>

```json
{
 "dangling_C-12": 0,
 "draft_targeted_C-11": 3
}
```

</details>

<details><summary><code>rows</code></summary>

```json
{
 "C-12": [],
 "C-11": [
  {
   "asset_id": "bo_laksana",
   "dep": "ga_vichara",
   "dep_status": "DRAFT"
  },
  {
   "asset_id": "ka_kshetra",
   "dep": "ka_dasha_kala",
   "dep_status": "DRAFT"
  },
  {
   "asset_id": "ka_taranga",
   "dep": "ka_sangam",
   "dep_status": "DRAFT"
  }
 ]
}
```

</details>

<details><summary><code>total_edges_in_registry</code></summary>

```json
284
```

</details>

---

### 5 · multi-producer partitions = 0

**Status: NOT-MEASURABLE → NOT-MEASURABLE**  
**Measured value:** `None` → `None`  

**Detector: NONE.** See the blocker below. An unmeasurable criterion is not a satisfied one.

**Blocked by / why this is not a pass:** NO DETECTOR EXISTS. The criterion asserts that no two producers write the same (table × generation × partition). The natural-key partition declaration HAS NO COLUMN in asset_registry — contract §4.9 / §10.3, rule C-25, which the contract itself marks 'not checkable, never report as passing'. Under CLAUDE.md §N.8 this criterion is null, not green.

**Where the number came from:** this script's own live query. A sibling artifact — census.json target_table_collisions (M0-T1) — reports: 5 co-written target_tables.

<details><summary><code>measurable_proxy</code></summary>

```json
{
 "what_it_is": "target_table shared by more than one registry row \u2014 a NECESSARY but not sufficient condition for a multi-producer partition. A shared table with correctly disjoint partitions is legitimate (co-writers), and this proxy cannot tell the two apart.",
 "co_written_target_tables": 5,
 "co_written_with_more_than_one_ACTIVE_producer": 4,
 "detail": [
  {
   "target_table": "bodha_msr_signals",
   "n": 7,
   "ids": [
    "bo_arudha",
    "bo_laksana",
    "bo_laksana_rerank",
    "bo_nakshatra_semantic",
    "bo_special_lagna",
    "bo_sudarshana",
    "bo_vargottama_dhana"
   ],
   "statuses": [
    "CURRENT",
    "DRAFT"
   ],
   "any_active": true,
   "n_active": 7
  },
  {
   "target_table": "brahma_class_priors",
   "n": 2,
   "ids": [
    "bg_class_lifetime_counts",
    "bg_class_priors"
   ],
   "statuses": [
    "CURRENT"
   ],
   "any_active": true,
   "n_active": 2
  },
  {
   "target_table": "chart_facts",
   "n": 5,
   "ids": [
    "ga_ayurdaya",
    "ga_nakshatra",
    "ga_panchanga",
    "ga_positions",
    "ga_sensitive_degree"
   ],
   "statuses": [
    "CURRENT"
   ],
   "any_active": true,
   "n_active": 5
  },
  {
   "target_table": "classical_text_chunks",
   "n": 2,
   "ids": [
    "bg_text_index",
    "bg_texts"
   ],
   "statuses": [
    "CURRENT"
   ],
   "any_active": true,
   "n_active": 2
  },
  {
   "target_table": "kala_gochara_windows",
   "n": 2,
   "ids": [
    "ka_gochara",
    "ka_gochara_sweep"
   ],
   "statuses": [
    "CURRENT",
    "RETIRED"
   ],
   "any_active": true,
   "n_active": 1
  }
 ],
 "sql": "SELECT target_table, count(*), array_agg(asset_id) FROM asset_registry WHERE target_table IS NOT NULL GROUP BY target_table HAVING count(*)>1"
}
```

</details>

---

### 6 · throughput rows on inactive assets = 0

**Status: BLOCKED → BLOCKED**  
**Measured value:** `3` → `3`  

**Detector**

```
SELECT ... FROM asset_throughput t JOIN asset_registry r USING(asset_id) WHERE r.is_active = false  (+ throughput rows with no registry row)
```

**Blocked by / why this is not a pass:** CHARTER §2 P1 COLLISION — the only offender is `ka_gochara_sweep`, the charter's named unrecoverable asset. Any operation on it is a RESERVED power: parked, never decided by an agent. Plan §14.2 assigns its lifecycle exit to rung R3, which has not opened. This criterion is therefore NOT PASS and NOT FAIL: it is blocked on a reserved decision, and this task neither marks it green nor resolves it.

**Where the number came from:** this script's own live query. A sibling artifact — census.json throughput_on_inactive_or_retired (M0-T1) — reports: 1 asset (`ka_gochara_sweep`), 3 rows.

<details><summary><code>rows_on_inactive</code></summary>

```json
[
 {
  "asset_id": "ka_gochara_sweep",
  "rows_n": 3,
  "states": [
   "error"
  ],
  "is_active": false,
  "catalog_status": "RETIRED"
 }
]
```

</details>

<details><summary><code>offending_assets</code></summary>

```json
[
 "ka_gochara_sweep"
]
```

</details>

---

### 7 · retired assets without a `data_disposition` = 0

**Status: BLOCKED → FAIL**  
**Measured value:** `None` → `1`  

**Detector**

```
SELECT asset_id FROM asset_registry WHERE catalog_status='RETIRED' AND data_disposition IS NULL ORDER BY asset_id
```

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>retired_assets_live</code></summary>

```json
[
 {
  "asset_id": "ka_gochara_sweep",
  "catalog_status": "RETIRED"
 }
]
```

</details>

---

### 8 · active assets with neither build coverage nor a dead flag = 0

**Status: NOT-MEASURABLE → NOT-MEASURABLE**  
**Measured value:** `None` → `None`  

**Detector**

```
SELECT asset_id, catalog_status, asset_kind, has_writer FROM asset_registry WHERE is_active  -- minus the AST @register set
```

**Blocked by / why this is not a pass:** NO 'DEAD FLAG' FIELD IS DEFINED. asset_registry has no column that designates a registered-but-dead asset. `has_writer` (boolean) is the only candidate, and the contract (ASSET_CATALOGUE_CONTRACT_v1_0.md) does not designate it as the dead flag — nor does it define one. The criterion's second half therefore has no detector, so the criterion as a whole cannot return a non-zero answer honestly. Its FIRST half is measured below.

**Note:** D-39 (ADHIKĀRIN, 2026-08-23T09:25:50Z) CONFIRMS ownership of this criterion's dead-flag work to M0 (independently re-derived) and SETTLES that a new column is authorised under D-4's standing conditions, NOT reserved by charter P5 — but no column has been created and this task did not create one, so the criterion remains NOT-MEASURABLE here; a known repair now exists (add the column, backfill, verify per D-4) and nobody has executed it. Separately, D-42 (ADHIKĀRIN, 2026-08-23T11:04:17Z) ranks build_run_assets as authoritative wherever a surface asks 'was this asset built' — bearing on this criterion's BUILD-COVERAGE half, not its dead-flag half: has_writer/asset_throughput.state='lit' remain proxies for 'built', and this criterion's own first-half measurement above (no production @register) does not depend on either proxy, so D-42 does not change the numbers here.

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>measured_components</code></summary>

```json
{
 "active_assets": 127,
 "active_assets_with_no_production_@register": 5,
 "of_those_carrying_has_writer=false": 5,
 "of_those_NOT_carrying_has_writer=false": 0,
 "detail_no_writer": [
  {
   "asset_id": "bg_ephemeris_engine",
   "catalog_status": "CURRENT",
   "asset_kind": "service",
   "has_writer_flag": false
  },
  {
   "asset_id": "bg_gochara_citation_resolution",
   "catalog_status": "CURRENT",
   "asset_kind": "data",
   "has_writer_flag": false
  },
  {
   "asset_id": "bg_panchanga",
   "catalog_status": "CURRENT",
   "asset_kind": "service",
   "has_writer_flag": false
  },
  {
   "asset_id": "bg_sarvatobhadra_grid",
   "catalog_status": "CURRENT",
   "asset_kind": "data",
   "has_writer_flag": false
  },
  {
   "asset_id": "lel_events",
   "catalog_status": "DRAFT",
   "asset_kind": "data",
   "has_writer_flag": false
  }
 ],
 "has_writer_flag_disagrees_with_decorator_scan": [
  {
   "asset_id": "bg_nakshatra_medical",
   "has_writer": false,
   "production_decorator": true
  },
  {
   "asset_id": "bg_transit_engine",
   "has_writer": false,
   "production_decorator": true
  }
 ],
 "why_the_candidate_flag_is_not_trustworthy": "2 rows have has_writer disagreeing with the live decorator scan, so even reading has_writer=false as 'dead' would be reading a flag that is itself wrong on those rows."
}
```

</details>

---

### 9 · unresolved zero-consumer findings = 0

**Status: FAIL → PASS**  
**Measured value:** `23` → `0`  
**Durability of this reading: durable** — criterion is not sourced from asset_registry columns the seed writes  

**Detector**

```
count of zero-consumer packets in 00_ARCHITECTURE/control/zero_consumer_evidence.json whose reading class (ZERO_CONSUMER_EVIDENCE_v1_0.md §1/§2) carries NO D-38 disposition. D-38 (ADHIKĀRIN, 2026-08-23T09:24:48Z, power G1) adjudicated all five reading classes and rules that adjudication IS resolution ('RESOLVED MEANS ADJUDICATED, NOT MUTATED'); the prior reading (packets minus asset_id-named DECISIONS entries) is superseded by this task, D-38 having been made since.
```

**Note:** ALL 23 PACKETS RESOLVED BY D-38 PART 3 — 8 INPUT-ONLY and 2 BY-DESIGN closed with no action; 7 METHOD-BLIND closed as unknown (explicitly NOT retirement candidates); 1 NO-CONSUMER-FOUND and 5 SHADOWED are ROUTED TO THEIR OWNING RUNGS as a retirement candidate / a real defect respectively — routed is still a recorded determination, not an open question, per D-38. The zero here is the M0-level adjudication; the 6 routed packets carry follow-on asset-lifecycle work that only their owning rungs may perform (I13).

**Where the number came from:** this script's own live query. A sibling artifact — ZERO_CONSUMER_EVIDENCE_v1_0.md §0/§2 (M0-T6) — reports: 23 packets found live; plan §1 states 13; the plan's own per-asset annotations count 7.

<details><summary><code>disposed</code></summary>

```json
{
 "bg_cohort": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_concordance": {
  "reading_class": "NO CONSUMER FOUND",
  "disposition": "recorded as a retirement candidate, NOT retired \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_ephemeris_engine": {
  "reading_class": "BY DESIGN EMPTY / CATEGORY MISMATCH",
  "disposition": "closed, no action \u2014 mismatch recorded",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_gochara_arcs": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_kota_chakra_rings": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_kp_sublord_division": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_panchanga": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_phaladeepika_latta": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_reference": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_sarvatobhadra_grid": {
  "reading_class": "BY DESIGN EMPTY / CATEGORY MISMATCH",
  "disposition": "closed, no action \u2014 mismatch recorded",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_sky_calendar": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_vedha_malefic_scale": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_vidhi_floors": {
  "reading_class": "SHADOWED",
  "disposition": "a real defect \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bg_vidhi_primitives": {
  "reading_class": "SHADOWED",
  "disposition": "a real defect \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bo_cdlm_summary": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "bo_samskara": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_dasha_kala": {
  "reading_class": "SHADOWED",
  "disposition": "a real defect \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_gochara_v3_century_materialize": {
  "reading_class": "INPUT-ONLY",
  "disposition": "closed, no action \u2014 absence of a serving consumer is the design",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_graha_sancara": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_kshetra": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_muhurta_seva": {
  "reading_class": "SHADOWED",
  "disposition": "a real defect \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "ka_tulana": {
  "reading_class": "SHADOWED",
  "disposition": "a real defect \u2014 routed to the owning rung",
  "decision": "DECISIONS.jsonl D-38 part 3"
 },
 "mi_jivanaghatana": {
  "reading_class": "METHOD-BLIND",
  "disposition": "closed as UNKNOWN \u2014 explicitly NOT a retirement candidate (H6 if it were)",
  "decision": "DECISIONS.jsonl D-38 part 3"
 }
}
```

</details>

<details><summary><code>packets</code></summary>

```json
23
```

</details>

<details><summary><code>asset_ids</code></summary>

```json
[
 "bg_cohort",
 "bg_concordance",
 "bg_ephemeris_engine",
 "bg_gochara_arcs",
 "bg_kota_chakra_rings",
 "bg_kp_sublord_division",
 "bg_panchanga",
 "bg_phaladeepika_latta",
 "bg_reference",
 "bg_sarvatobhadra_grid",
 "bg_sky_calendar",
 "bg_vedha_malefic_scale",
 "bg_vidhi_floors",
 "bg_vidhi_primitives",
 "bo_cdlm_summary",
 "bo_samskara",
 "ka_dasha_kala",
 "ka_gochara_v3_century_materialize",
 "ka_graha_sancara",
 "ka_kshetra",
 "ka_muhurta_seva",
 "ka_tulana",
 "mi_jivanaghatana"
]
```

</details>

---

### 10 · CI guard merged and **blocking**

**Status: FAIL → FAIL**  
**Measured value:** `{"guard_scripts_found": 1, "workflow_invocations_found": 0}` → `{"guard_scripts_found": 2, "workflow_invocations_found": 3, "merged_to_default_branch": false, "invocation_is_blocking": false}`  

**Detector**

```
(a) does a guard implementing the Asset Catalogue Contract exist under platform/scripts/{governance,ci}; (b) is it invoked from a .github/workflows job; (c) is that job/step BLOCKING — no `continue-on-error: true`, no `|| true` on the run line; and is the guard MERGED, i.e. present on `origin/main` per `git ls-tree`. PASS requires all four. GitHub run history is corroboration, not the verdict.
```

**Note:** WORK_QUEUE id M0-T9 shipped the two guard scripts and a workflow that invokes them, and shipped it NON-BLOCKING on purpose: .github/workflows/nirmana-m0-guards.yml carries `continue-on-error: true` on both jobs and says so in its own header. Flipping it to blocking is ADHIKĀRIN's call (charter G9) and has not been made. So the merged-and-wired halves have genuinely moved and the BLOCKING half has not, which is why this stays FAIL rather than becoming green on two of its three clauses. Shortfall: the guard/workflow is NOT on the default branch (`origin/main`) — 'merged' means merged, and present-on-the-campaign-branch is not that; the invocation is NOT blocking

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>shortfall</code></summary>

```json
[
 "the guard/workflow is NOT on the default branch (`origin/main`) \u2014 'merged' means merged, and present-on-the-campaign-branch is not that",
 "the invocation is NOT blocking"
]
```

</details>

<details><summary><code>blocking_analysis</code></summary>

```json
{
 "parser": "pyyaml",
 "invocations": [
  {
   "workflow": ".github/workflows/nirmana-m0-guards.yml",
   "job": "asset-catalogue-contract",
   "step": "Contract conformance \u2014 self-test (fixtures + spec cross-check)",
   "scripts": [
    "check_asset_catalogue_contract.py"
   ],
   "job_continue_on_error": true,
   "step_continue_on_error": false,
   "run_line_swallows_exit_code": false,
   "blocking": false
  },
  {
   "workflow": ".github/workflows/nirmana-m0-guards.yml",
   "job": "asset-catalogue-contract",
   "step": "Contract conformance \u2014 dated live baseline (report only)",
   "scripts": [
    "check_asset_catalogue_contract.py"
   ],
   "job_continue_on_error": true,
   "step_continue_on_error": false,
   "run_line_swallows_exit_code": false,
   "blocking": false
  },
  {
   "workflow": ".github/workflows/nirmana-m0-guards.yml",
   "job": "asset-source-parity",
   "step": "Source parity \u2014 self-test (fixture writer trees)",
   "scripts": [
    "check_asset_source_parity.py"
   ],
   "job_continue_on_error": true,
   "step_continue_on_error": false,
   "run_line_swallows_exit_code": false,
   "blocking": false
  },
  {
   "workflow": ".github/workflows/nirmana-m0-guards.yml",
   "job": "asset-source-parity",
   "step": "Source parity \u2014 repo scan against the dated registry baseline",
   "scripts": [
    "check_asset_source_parity.py"
   ],
   "job_continue_on_error": true,
   "step_continue_on_error": false,
   "run_line_swallows_exit_code": false,
   "blocking": false
  }
 ],
 "any_blocking": false,
 "all_blocking": false,
 "undecidable": []
}
```

</details>

<details><summary><code>merged_to_default_branch_check</code></summary>

```json
{
 "ref": "origin/main",
 "ok": true,
 "present": {
  ".github/workflows/nirmana-m0-guards.yml": false,
  "platform/scripts/governance/check_asset_catalogue_contract.py": false,
  "platform/scripts/governance/check_asset_source_parity.py": false
 },
 "reason": null
}
```

</details>

<details><summary><code>github_run_evidence</code></summary>

```json
{
 "available": true,
 "reason": null,
 "workflows": {
  ".github/workflows/nirmana-m0-guards.yml": {
   "registered_on_default_branch": false,
   "run_count": 0,
   "detail": "HTTP 404: workflow nirmana-m0-guards.yml not found on the default branch (https://api.github.com/repos/Marsys-Technologies/Madhav/actions/workflows/nirmana-m0-guards.yml)"
  }
 }
}
```

</details>

<details><summary><code>guard_scripts</code></summary>

```json
[
 "platform/scripts/governance/check_asset_catalogue_contract.py",
 "platform/scripts/governance/check_asset_source_parity.py"
]
```

</details>

<details><summary><code>workflow_invocations</code></summary>

```json
[
 {
  "workflow": ".github/workflows/nirmana-m0-guards.yml",
  "script": "platform/scripts/governance/check_asset_catalogue_contract.py"
 },
 {
  "workflow": ".github/workflows/nirmana-m0-guards.yml",
  "script": "platform/scripts/governance/check_asset_source_parity.py"
 },
 {
  "workflow": ".github/workflows/nirmana-m0-guards.yml",
  "script": "(inline marker)"
 }
]
```

</details>

---

### 11 · every asset carrying `domain` and `rung` *(v4.1)*

**Status: BLOCKED → PASS**  
**Measured value:** `None` → `0`  
**Durability of this reading: NON-DURABLE** — projected forward: constituent rule(s) ['C-18'] start firing once asset_registry_seed.ts restores the columns it owns  
**Coverage caveat:** Columns ['domain', 'rung'] are absent from the seed's INSERT column list and have no NOT NULL / DEFAULT / trigger behind them, so any asset the seed newly inserts lands with them NULL and re-breaks this criterion. Today's rows are safe; the criterion's coverage of FUTURE rows is not enforced by anything.  

**Detector**

```
C-18 + C-19 detection SQL
```

**Where the number came from:** this script's own live query. A sibling artifact — ASSET_CATALOGUE_CONTRACT §6 rules C-18/C-19 (M0-T2) — reports: 128 / 128 (columns do not exist).

<details><summary><code>components</code></summary>

```json
{
 "C-18_domain": 0,
 "C-19_rung": 0
}
```

</details>

<details><summary><code>rows</code></summary>

```json
{
 "C-18": [],
 "C-19": []
}
```

</details>

---

### 12 · the §11 CI domain-coherence assertion green *(v4.1)*

**Status: FAIL → FAIL**  
**Measured value:** `None` → `{"assertion_exists": true, "assertion_wired_to_a_workflow": true, "invocation_is_blocking": false, "merged_to_default_branch": false, "live_violations": 0}`  

**Detector**

```
rule `X-04` in platform/scripts/governance/check_asset_catalogue_contract.py — `domain coherence: a shared asset depends only on shared assets`, severity BLOCKING, origin `plan §11 (CI shape guard addition)`. PASS requires the assertion to EXIST, to be invoked from a workflow, for that invocation to be blocking and merged to `origin/main` (criterion 10's two halves), and for the underlying condition to measure zero here.
```

**Note:** Criterion 12 reduces to criterion 10. The assertion (X-04) exists and returns 0 live; what is missing is a RUN of it that gates — the same `continue-on-error: true` and the same absence from `origin/main` that hold criterion 10 at FAIL. `has_ever_run_in_ci` is null, not false: nothing in this generator queries GitHub run history for a verdict (github_run_evidence is corroboration only). Shortfall: the carrying guard/workflow is NOT on `origin/main` (criterion 10's `merged` half); the invocation is NOT blocking, so no run of it can gate anything (criterion 10's `blocking` half)

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>shortfall</code></summary>

```json
[
 "the carrying guard/workflow is NOT on `origin/main` (criterion 10's `merged` half)",
 "the invocation is NOT blocking, so no run of it can gate anything (criterion 10's `blocking` half)"
]
```

</details>

<details><summary><code>underlying_condition_measured_here</code></summary>

```json
{
 "what": "shared-domain asset depending on a chart-domain asset",
 "measured_via": "`domain` column",
 "violations": 0,
 "rows": []
}
```

</details>

<details><summary><code>plan_named_suspects</code></summary>

```json
[
 "ka_graha_sancara",
 "ka_muhurta_seva",
 "mi_kula",
 "mi_vistara"
]
```

</details>

<details><summary><code>domain_coherence_ci_scripts</code></summary>

```json
[
 "platform/scripts/governance/check_asset_catalogue_contract.py"
]
```

</details>

<details><summary><code>domain_coherence_workflow_invocations</code></summary>

```json
[
 {
  "workflow": ".github/workflows/nirmana-m0-guards.yml",
  "script": "platform/scripts/governance/check_asset_catalogue_contract.py"
 }
]
```

</details>

<details><summary><code>corrected_claim</code></summary>

```json
{
 "readings_1_and_2_said": "THE ASSERTION DOES NOT EXIST.",
 "verdict": "FALSE \u2014 and false when written.",
 "correcting_task": "M0-T32",
 "correcting_ts": "2026-08-23",
 "evidence": [
  "platform/scripts/governance/check_asset_catalogue_contract.py Rule(\"X-04\", BLOCKING, \"domain coherence: a shared asset depends only on shared assets\", x04, origin=\"plan \u00a711 (CI shape guard addition)\")",
  "M0-T31 live guard run 2026-08-23T06:58:51Z: X-04 pass, 0 violations",
  "WORK_QUEUE M0-T9 measured_live: X-04 = 0; green_now_list includes X-04"
 ],
 "root_cause": "this generator's `domain_markers` tuple matched none of the guard's wording, so its absence-detector could only ever return absent \u2014 a constant wearing a detector's clothes (CLAUDE.md \u00a7N.8), inside the scorecard built to catch that class.",
 "what_is_actually_true": "the assertion exists and measures zero; it has never RUN in CI, for exactly criterion 10's reasons. Criterion 12 therefore reduces to criterion 10."
}
```

</details>

<details><summary><code>reduces_to</code></summary>

```json
"10_ci_guard_merged_and_blocking"
```

</details>

---

## 2 — Contract rule detail (criterion 2's constituents)

| rule | assertion | severity | then | now | violations then → now | durability |
|---|---|---|---|---|--:|---|
| `C-01` | asset_id prefix matches layer | BLOCKING | FAIL | **FAIL** | 1 → 1 | n/a — not passing |
| `C-02` | layer_index is ^L[0-5]$ and agrees with layer | BLOCKING | FAIL | **FAIL** | 21 → 1 | n/a — not passing |
| `C-03` | layer_name is the exact lexicon spelling | BLOCKING | FAIL | **FAIL** | 20 → 1 | n/a — not passing |
| `C-04` | data/artifact => target_table exists | BLOCKING | FAIL | **FAIL** | 11 → 9 | n/a — not passing |
| `C-05` | data/artifact => count_sql NOT NULL | BLOCKING | FAIL | **PASS** | 2 → 0 | **NON-DURABLE** |
| `C-06` | chart-domain count_sql is chart-scoped ($1) | BLOCKING | FAIL | **FAIL** | 1 → 1 | n/a — not passing |
| `C-07` | service rows carry no data-asset fields | BLOCKING | FAIL | **FAIL** | 4 → 4 | n/a — not passing |
| `C-08` | RETIRED => data_disposition NOT NULL | BLOCKING | BLOCKED | **FAIL** | None → 1 | n/a — not passing |
| `C-09` | superseded_by resolves | BLOCKING | BLOCKED | **PASS** | None → 0 | durable |
| `C-10` | data_disposition only on RETIRED rows | BLOCKING | BLOCKED | **PASS** | None → 0 | durable |
| `C-11` | CURRENT depends only on CURRENT/source | BLOCKING | FAIL | **FAIL** | 3 → 3 | n/a — not passing |
| `C-12` | every depends_on element resolves | BLOCKING | PASS | **PASS** | 0 → 0 | durable |
| `C-13a` | no self-edge | BLOCKING | PASS | **PASS** | 0 → 0 | durable |
| `C-14` | asset_kind / asset_type coherent | BLOCKING | FAIL | **PASS** | 6 → 0 | **NON-DURABLE** |
| `C-15` | service => health_probe AND provides_apis | BLOCKING | FAIL | **FAIL** | 6 → 6 | n/a — not passing |
| `C-16` | non-service => service_health IS NULL | BLOCKING | PASS | **PASS** | 0 → 0 | **EXPOSED** |
| `C-17` | no graded service_health without a probe | BLOCKING | FAIL | **FAIL** | 4 → 4 | n/a — not passing |
| `C-18` | domain present and derived from scope | BLOCKING | BLOCKED | **PASS** | None → 0 | **NON-DURABLE** |
| `C-19` | rung present and derived from layer | BLOCKING | BLOCKED | **PASS** | None → 0 | **EXPOSED** |
| `C-20` | CURRENT data/artifact carries a floor | BLOCKING | FAIL | **FAIL** | 5 → 3 | n/a — not passing |
| `C-21` | target_floor = 0 => volume_explanation | BLOCKING | FAIL | **FAIL** | 19 → 19 | n/a — not passing |
| `C-24` | clear_tables exist and include target_table | BLOCKING | PASS | **PASS** | 0 → 0 | durable |
| `C-28` | estimated_seconds NOT NULL where a successful build exists (DATA_KINDS-scoped estimate rule; D-94 defines this as the authoritative C-28 — the all-asset-kind question is check_asset_catalogue_contract.py's X-06, not this rule) | BLOCKING | FAIL | **FAIL** | 112 → 31 | n/a — not passing |
| `C-13b` | depends_on graph acyclic | — | — | **PASS** | — → 0 | — |
| `C-22` | rung-frozen data assets carry integrity_check_sql | — | — | **NOT-MEASURABLE** | — → — | — |
| `C-23` | has_substeps equals the writer-class truth | — | — | **PASS** | — → 0 | — |
| `C-25` | co-written target_table => every co-writer declares its partition | — | — | **NOT-MEASURABLE** | — → — | — |
| `C-26` | generation-bearing asset declares its authority pointer | — | — | **NOT-MEASURABLE** | — → — | — |
| `C-27` | writer_timeout_seconds set from telemetry p95 | — | — | **NOT-MEASURABLE** | — → — | — |

### Rules that must NEVER read green

- **`C-22`** — rung-frozen data assets carry integrity_check_sql. vacuous today: 0 rungs frozen. Reported as vacuous, not as a pass.
- **`C-25`** — co-written target_table => every co-writer declares its partition. NO COLUMN EXISTS. Contract §4.9/§10.3. §N.8: null, never green.
- **`C-26`** — generation-bearing asset declares its authority pointer. NO COLUMN EXISTS. Contract §4.11/§10.3. §N.8: null, never green.
- **`C-27`** — writer_timeout_seconds set from telemetry p95. ADVISORY; not checkable until M2 telemetry. §N.8: null, never green.

---

## 2b — Disagreement register

Where another artifact states a figure for a quantity measured here, both are shown. **Nothing below is averaged.** Two angles disagreeing is a finding.

| quantity | this script (measured) | other source | its figure | disagree? |
|---|--:|---|---|:-:|
| C-04 — data/artifact rows failing the target_table rule | `9` | ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-04 | 10 | **YES** |
| C-17 — graded service_health with no health_probe | `4` | ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-17 | 3 | **YES** |
| 0.6a — has_substeps false negatives (C-23) | `0` | NIRMANA_ELEVATION_PLAN v3.0 §0.6a / v4.0 (states 14) vs DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md §4 (M0-T8, states 12) | plan 14 · M0-T8 12 | **YES** |
| criterion 9 — zero-consumer findings | `0` | NIRMANA_ELEVATION_PLAN §1 (states 13) · the plan's own per-asset annotations (7) · ZERO_CONSUMER_EVIDENCE_v1_0.md (23 packets) · DECISIONS.jsonl D-38 part 3 (2026-08-23T09:24:48Z, adjudicates all 23 by reading class) | plan-summary 13 · plan-annotations 7 · M0-T6 packets 23 · D-38 unresolved 0 | **YES** |
| target_table NULL rows (all kinds) | `None` | CENSUS_REPORT.md §5 (M0-T1) states 14; contract §6 C-04 states 10 | census 14 (all rows) · contract 10 (data/artifact only) | no |

- **C-04 — data/artifact rows failing the target_table rule** — Both are right about different things. 10 is the count of data/artifact rows with target_table NULL. The rule as written (and as its own §8 SQL executes) ALSO fails a row whose target_table names a table that does not exist — `bg_sky_calendar` → `bg_sky_events`, which is absent from information_schema.tables. The contract's §6 count reported the NULL half only. 11 is the rule's full result.
- **C-17 — graded service_health with no health_probe** — The contract's §6 cell names 3 assets, all `healthy` (ka_dasha_kala, ka_muhurta_seva, ka_tulana). Its own §8 SQL matches `IN ('healthy','degraded','unhealthy')`, which also catches `ka_graha_sancara` ('unhealthy', no probe). The contract's stated count disagrees with the contract's own SQL. 4 is the SQL's result.
- **0.6a — has_substeps false negatives (C-23)** — This script's detector and M0-T8's are INDEPENDENT and differ in rule — M0-T8 uses (defines plan_substeps AND defines run_substep); this one uses (overrides plan_substeps OR sets the class attribute has_substeps=True), in both cases EXCLUDING WriterBase's own default. Two independent detectors returning 12 against the plan's 14 is corroboration; the plan's figure is the outlier and is not measured.
- **criterion 9 — zero-consumer findings** — This script counts the M0-T6 packet set and subtracts packets whose reading class carries a D-38 disposition; D-38 covers all 23, so unresolved = 0. Prior readings of this scorecard (through M0-T36) reported unresolved = packets because no G1 ruling had yet named a disposition; D-38 supplies it. The plan's 13 still has no per-asset list behind it and does not reconcile with the plan's own annotations — that disagreement is unchanged and not averaged.
- **target_table NULL rows (all kinds)** — Not a disagreement once scoped: 14 counts every registry row, 10 counts only the data/artifact rows the rule applies to. Recorded so the two figures are not read as a conflict.

---

## 3 — Source scans behind criterion 1 and criterion 8

```json
{
 "decorators": {
  "roots": [
   "platform/python-sidecar"
  ],
  "files_scanned": 1033,
  "production_ids": 123,
  "test_only_ids": [
   "bad_infra_writer",
   "fixture.asset_a",
   "fixture.crashing",
   "fixture.success",
   "test_infra_asset_1",
   "test_infra_asset_dup"
  ],
  "unresolved_sites": [],
  "parse_errors": []
 },
 "seed_ts": {
  "path": "platform/scripts/seed/asset_registry_seed.ts",
  "ok": true,
  "ids": 127,
  "reason": null
 },
 "ci": {
  "guard_scripts": [
   "platform/scripts/governance/check_asset_catalogue_contract.py",
   "platform/scripts/governance/check_asset_source_parity.py"
  ],
  "workflow_invocations": [
   {
    "workflow": ".github/workflows/nirmana-m0-guards.yml",
    "script": "platform/scripts/governance/check_asset_catalogue_contract.py"
   },
   {
    "workflow": ".github/workflows/nirmana-m0-guards.yml",
    "script": "platform/scripts/governance/check_asset_source_parity.py"
   },
   {
    "workflow": ".github/workflows/nirmana-m0-guards.yml",
    "script": "(inline marker)"
   }
  ],
  "domain_coherence_scripts": [
   "platform/scripts/governance/check_asset_catalogue_contract.py"
  ],
  "domain_coherence_workflow_invocations": [
   {
    "workflow": ".github/workflows/nirmana-m0-guards.yml",
    "script": "platform/scripts/governance/check_asset_catalogue_contract.py"
   }
  ],
  "workflows_scanned": [
   ".github/workflows/chat-v2-ci.yml",
   ".github/workflows/ci.yml",
   ".github/workflows/deploy.yml",
   ".github/workflows/ekv-lints.yml",
   ".github/workflows/elev-serving-gates.yml",
   ".github/workflows/fresh_chart_smoke.yml",
   ".github/workflows/gochara-smoke-probe.yml",
   ".github/workflows/iac-apply.yml",
   ".github/workflows/icr_weekly_scan.yml",
   ".github/workflows/judgment-integration-nightly.yml",
   ".github/workflows/nirmana-m0-guards.yml",
   ".github/workflows/pariprashna-ci.yml",
   ".github/workflows/pariprashna-post-deploy-smoke.yml",
   ".github/workflows/reconciliation-cadence.yml",
   ".github/workflows/samiksha-daily.yml",
   ".github/workflows/shad-darshana-ci-skeletons.yml",
   ".github/workflows/shad-darshana-circularity-guard.yml",
   ".github/workflows/tap-ci.yml",
   ".github/workflows/verification-invariant.yml"
  ]
 }
}
```

---

## 3a — Falsifiability: could each PASSing detector have returned non-zero?

for every contract rule reading PASS, the shipped SQL re-run with one deliberate mutation that must make it fire. A zero from a query that cannot return non-zero is not evidence (CLAUDE.md §N.8). Read-only; the mutant is never used for a verdict.

| rule | mutation | mutant rows | proved falsifiable |
|---|---|--:|:-:|
| `C-05` | invert the NULL test: every data/artifact row that HAS a count_sql must fire | 120 | **yes** |
| `C-09` | invert the NOT NULL test: rows with no supersession must fire, since NOT EXISTS(... = NULL) is true for all of them | 128 | **yes** |
| `C-10` | invert the NULL test: non-RETIRED rows without a disposition must fire | 127 | **yes** |
| `C-12` | invert the existence test: every edge that DOES resolve must fire | 284 | **yes** |
| `C-13a` | invert the self-edge test: every row without a self-edge must fire | 128 | **yes** |
| `C-14` | invert the membership test: every LEGAL (kind,type) pair must fire | 128 | **yes** |
| `C-16` | invert the NULL test: non-service rows with no service_health must fire | 120 | **yes** |
| `C-18` | swap the scope→domain mapping: with the expectation inverted every row must fire | 128 | **yes** |
| `C-19` | mis-map one layer: every brahmagyan row must fire | 40 | **yes** |
| `C-24` | invert the first arm's existence test: every clear_tables entry that DOES name a real table must fire | 15 | **yes** |

**Every PASSing rule fired under its mutant.** No zero in this reading comes from a query that could not have returned non-zero.

---

## 3b — Durability: which greens a re-seed would undo

A repair written straight to asset_registry survives only if its column is absent from asset_registry_seed.ts's `ON CONFLICT (asset_id) DO UPDATE SET` list. Columns in that list are restored from EXCLUDED on the next seed run. A green resting on such a column is a green a re-seed silently undoes, which is strictly worse than a red.

Parsed from `platform/scripts/seed/asset_registry_seed.ts` **as text** (never imported — D-9 / D-13): parse ok = `True`.

| question | answer |
|---|---|
| columns the seed **overwrites** on every re-run (`DO UPDATE SET`) | `asset_kind, asset_type, catalog_status, count_sql, depends_on, english_description, english_name, expected_volume_formula, expected_volume_inputs, health_probe, is_active, layer, layer_index, layer_name, provides_apis, sanskrit_name, scope, size_sql, sort_order, storage_type, target_table, volume_explanation` |
| columns the seed **never inserts** (a new seed row lands NULL/default) | `clear_tables, created_at, data_disposition, dead_flag, domain, has_substeps, has_writer, integrity_check_sql, last_invoked_at, last_selftest_at, natural_key_partition, rebuild_on_probe_fail, rung, selftest_detail, service_health, superseded_by, target_floor, writer_timeout_seconds` |
| live cells that already differ from what the seed would write | **9** across 9 asset(s) |

**Divergence detector**

```
for each seed-overwritten column this script can model (['asset_kind', 'asset_type', 'layer', 'scope']), compare the LIVE value against the literal the seed declares for that asset (or the seed's own `?? 'data'` default when the key is absent). A difference means the next seed run changes that cell.
```

| asset | column | live now | seed would write | seed declares it? |
|---|---|---|---|:-:|
| `bg_ephemeris_engine` | `asset_kind` | `service` | `data` | no — seed default |
| `bg_panchanga` | `asset_kind` | `service` | `data` | no — seed default |
| `ka_dasha_kala` | `asset_type` | `service` | `data` | no — seed default |
| `ka_graha_sancara` | `asset_type` | `service` | `data` | no — seed default |
| `ka_muhurta_seva` | `asset_type` | `service` | `data` | no — seed default |
| `ka_tulana` | `asset_type` | `service` | `data` | no — seed default |
| `mi_abhilekha` | `asset_type` | `service` | `data` | no — seed default |
| `mi_jivanaghatana` | `scope` | `per_chart` | `global` | yes |
| `mi_seva` | `asset_type` | `service` | `data` | no — seed default |

### Rules whose improvement rests on a reverted repair

_None: no rule that newly passes had all of its former violating rows land in the seed-divergent set._

### Projected forward: what a re-seed would actually break

each PASSing rule re-run against a CTE that shadows asset_registry with the values asset_registry_seed.ts would write, for the columns this script can model (['asset_kind', 'asset_type', 'layer', 'scope']). Read-only; never used as a reported status. Columns the script cannot model are left at their live values, so this is a LOWER BOUND on what a re-seed would break.

| rule | violations now | violations after a re-seed | breaks? |
|---|--:|--:|:-:|
| `C-05` | 0 | 2 | **YES** |
| `C-09` | 0 | 0 | no |
| `C-10` | 0 | 0 | no |
| `C-12` | 0 | 0 | no |
| `C-13a` | 0 | 0 | no |
| `C-14` | 0 | 8 | **YES** |
| `C-16` | 0 | 0 | no |
| `C-18` | 0 | 1 | **YES** |
| `C-19` | 0 | 0 | no |
| `C-24` | 0 | 0 | no |

**Rules that stop passing after a re-seed: `C-05, C-14, C-18`.**

### Per-criterion durability

| # | status | durability | columns read that the seed overwrites | why |
|---|---|---|---|---|
| 1 | FAIL | n/a — not passing | `—` | — |
| 2 | NOT-MEASURABLE | n/a — not passing | `asset_kind, asset_type, catalog_status, count_sql, depends_on, health_probe, layer, layer_index, layer_name, provides_apis, scope, target_table, volume_explanation` | — |
| 3 | FAIL | n/a — not passing | `asset_kind, layer` | — |
| 4 | FAIL | n/a — not passing | `asset_kind, catalog_status, depends_on` | — |
| 5 | NOT-MEASURABLE | n/a — not passing | `—` | — |
| 6 | BLOCKED | n/a — not passing | `—` | — |
| 7 | FAIL | n/a — not passing | `catalog_status` | — |
| 8 | NOT-MEASURABLE | n/a — not passing | `asset_kind, catalog_status, is_active` | — |
| 9 | PASS | durable | `—` | criterion is not sourced from asset_registry columns the seed writes |
| 10 | FAIL | n/a — not passing | `—` | — |
| 11 | PASS | **NON-DURABLE** | `asset_kind, layer, scope` | projected forward: constituent rule(s) ['C-18'] start firing once asset_registry_seed.ts restores the columns it owns |
| 12 | FAIL | n/a — not passing | `—` | — |

<details><summary><code>durability — full record</code></summary>

```json
{
 "post_reseed_projection": {
  "what_it_is": "each PASSing rule re-run against a CTE that shadows asset_registry with the values asset_registry_seed.ts would write, for the columns this script can model (['asset_kind', 'asset_type', 'layer', 'scope']). Read-only; never used as a reported status. Columns the script cannot model are left at their live values, so this is a LOWER BOUND on what a re-seed would break.",
  "modelled_columns": [
   "asset_kind",
   "asset_type",
   "layer",
   "scope"
  ],
  "seed_rows_projected": 127,
  "rules": {
   "C-05": {
    "violations_now": 0,
    "violations_after_a_reseed": 2,
    "would_break": true,
    "verdict": "this rule STOPS PASSING once the seed restores its columns"
   },
   "C-09": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-10": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-12": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-13a": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-14": {
    "violations_now": 0,
    "violations_after_a_reseed": 8,
    "would_break": true,
    "verdict": "this rule STOPS PASSING once the seed restores its columns"
   },
   "C-16": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-18": {
    "violations_now": 0,
    "violations_after_a_reseed": 1,
    "would_break": true,
    "verdict": "this rule STOPS PASSING once the seed restores its columns"
   },
   "C-19": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   },
   "C-24": {
    "violations_now": 0,
    "violations_after_a_reseed": 0,
    "would_break": false,
    "verdict": "this rule still passes after the seed restores its columns"
   }
  },
  "rules_that_would_break": [
   "C-05",
   "C-14",
   "C-18"
  ]
 },
 "why_this_exists": "A repair written straight to asset_registry survives only if its column is absent from asset_registry_seed.ts's `ON CONFLICT (asset_id) DO UPDATE SET` list. Columns in that list are restored from EXCLUDED on the next seed run. A green resting on such a column is a green a re-seed silently undoes, which is strictly worse than a red.",
 "seed_upsert_parse": {
  "ok": true,
  "reason": null,
  "insert_columns": [
   "asset_id",
   "asset_kind",
   "asset_type",
   "catalog_status",
   "count_sql",
   "depends_on",
   "english_description",
   "english_name",
   "estimated_seconds",
   "expected_volume_formula",
   "expected_volume_inputs",
   "health_probe",
   "is_active",
   "layer",
   "layer_index",
   "layer_name",
   "provides_apis",
   "sanskrit_name",
   "scope",
   "size_sql",
   "sort_order",
   "storage_type",
   "target_table",
   "volume_explanation"
  ],
  "do_update_columns": [
   "asset_kind",
   "asset_type",
   "catalog_status",
   "count_sql",
   "depends_on",
   "english_description",
   "english_name",
   "expected_volume_formula",
   "expected_volume_inputs",
   "health_probe",
   "is_active",
   "layer",
   "layer_index",
   "layer_name",
   "provides_apis",
   "sanskrit_name",
   "scope",
   "size_sql",
   "sort_order",
   "storage_type",
   "target_table",
   "volume_explanation"
  ],
  "path": "platform/scripts/seed/asset_registry_seed.ts"
 },
 "columns_the_seed_overwrites_on_reseed": [
  "asset_kind",
  "asset_type",
  "catalog_status",
  "count_sql",
  "depends_on",
  "english_description",
  "english_name",
  "expected_volume_formula",
  "expected_volume_inputs",
  "health_probe",
  "is_active",
  "layer",
  "layer_index",
  "layer_name",
  "provides_apis",
  "sanskrit_name",
  "scope",
  "size_sql",
  "sort_order",
  "storage_type",
  "target_table",
  "volume_explanation"
 ],
 "columns_the_seed_never_inserts": [
  "clear_tables",
  "created_at",
  "data_disposition",
  "dead_flag",
  "domain",
  "has_substeps",
  "has_writer",
  "integrity_check_sql",
  "last_invoked_at",
  "last_selftest_at",
  "natural_key_partition",
  "rebuild_on_probe_fail",
  "rung",
  "selftest_detail",
  "service_health",
  "superseded_by",
  "target_floor",
  "writer_timeout_seconds"
 ],
 "live_vs_seed_divergence": {
  "detector": "for each seed-overwritten column this script can model (['asset_kind', 'asset_type', 'layer', 'scope']), compare the LIVE value against the literal the seed declares for that asset (or the seed's own `?? 'data'` default when the key is absent). A difference means the next seed run changes that cell.",
  "modelled_columns": [
   "asset_kind",
   "asset_type",
   "layer",
   "scope"
  ],
  "divergent_cells": 9,
  "divergent_assets": [
   "bg_ephemeris_engine",
   "bg_panchanga",
   "ka_dasha_kala",
   "ka_graha_sancara",
   "ka_muhurta_seva",
   "ka_tulana",
   "mi_abhilekha",
   "mi_jivanaghatana",
   "mi_seva"
  ],
  "rows": [
   {
    "asset_id": "bg_ephemeris_engine",
    "column": "asset_kind",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "bg_panchanga",
    "column": "asset_kind",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "ka_dasha_kala",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "ka_graha_sancara",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "ka_muhurta_seva",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "ka_tulana",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "mi_abhilekha",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   },
   {
    "asset_id": "mi_jivanaghatana",
    "column": "scope",
    "live_value": "per_chart",
    "seed_would_write": "global",
    "seed_declares_it": true
   },
   {
    "asset_id": "mi_seva",
    "column": "asset_type",
    "live_value": "service",
    "seed_would_write": "data",
    "seed_declares_it": false
   }
  ]
 },
 "per_rule": {
  "C-01": {
   "status": "FAIL",
   "violations": 1,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "layer"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "layer"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-02": {
   "status": "FAIL",
   "violations": 1,
   "columns_referenced": [
    "asset_id",
    "layer",
    "layer_index"
   ],
   "seed_overwritable_columns": [
    "layer",
    "layer_index"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-03": {
   "status": "FAIL",
   "violations": 1,
   "columns_referenced": [
    "asset_id",
    "layer",
    "layer_name"
   ],
   "seed_overwritable_columns": [
    "layer",
    "layer_name"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-04": {
   "status": "FAIL",
   "violations": 9,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "target_table"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "target_table"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-05": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "count_sql"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "count_sql"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "NON-DURABLE",
   "attribution": null,
   "non_durable_proof": {
    "source": "post_reseed_projection",
    "violations_now": 0,
    "violations_after_a_reseed": 2,
    "verdict": "this rule reads 0 today and 2 once asset_registry_seed.ts restores the columns it owns. Its zero is a repair the next seed run reverts, not a fixed defect.",
    "reverted_by": [
     "bg_ephemeris_engine",
     "bg_panchanga"
    ]
   }
  },
  "C-06": {
   "status": "FAIL",
   "violations": 1,
   "columns_referenced": [
    "asset_id",
    "count_sql",
    "scope"
   ],
   "seed_overwritable_columns": [
    "count_sql",
    "scope"
   ],
   "seed_divergent_assets_among_them": [
    "mi_jivanaghatana"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-07": {
   "status": "FAIL",
   "violations": 4,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "clear_tables",
    "count_sql",
    "target_floor",
    "target_table"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "count_sql",
    "target_table"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-08": {
   "status": "FAIL",
   "violations": 1,
   "columns_referenced": [
    "asset_id",
    "catalog_status",
    "data_disposition"
   ],
   "seed_overwritable_columns": [
    "catalog_status"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-09": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "superseded_by"
   ],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "durability": "durable",
   "attribution": null
  },
  "C-10": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "catalog_status",
    "data_disposition"
   ],
   "seed_overwritable_columns": [
    "catalog_status"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "durable",
   "attribution": null
  },
  "C-11": {
   "status": "FAIL",
   "violations": 3,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "catalog_status",
    "depends_on"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "catalog_status",
    "depends_on"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-12": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "depends_on"
   ],
   "seed_overwritable_columns": [
    "depends_on"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "durable",
   "attribution": null
  },
  "C-13a": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "depends_on"
   ],
   "seed_overwritable_columns": [
    "depends_on"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "durable",
   "attribution": null
  },
  "C-14": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "asset_type"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "asset_type"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga",
    "ka_dasha_kala",
    "ka_graha_sancara",
    "ka_muhurta_seva",
    "ka_tulana",
    "mi_abhilekha",
    "mi_seva"
   ],
   "durability": "NON-DURABLE",
   "attribution": null,
   "non_durable_proof": {
    "source": "post_reseed_projection",
    "violations_now": 0,
    "violations_after_a_reseed": 8,
    "verdict": "this rule reads 0 today and 8 once asset_registry_seed.ts restores the columns it owns. Its zero is a repair the next seed run reverts, not a fixed defect.",
    "reverted_by": [
     "bg_ephemeris_engine",
     "bg_panchanga",
     "ka_dasha_kala",
     "ka_graha_sancara",
     "ka_muhurta_seva",
     "ka_tulana",
     "mi_abhilekha",
     "mi_seva"
    ]
   }
  },
  "C-15": {
   "status": "FAIL",
   "violations": 6,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "health_probe",
    "provides_apis"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "health_probe",
    "provides_apis"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-16": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "service_health"
   ],
   "seed_overwritable_columns": [
    "asset_kind"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "EXPOSED",
   "attribution": null
  },
  "C-17": {
   "status": "FAIL",
   "violations": 4,
   "columns_referenced": [
    "asset_id",
    "health_probe",
    "service_health"
   ],
   "seed_overwritable_columns": [
    "health_probe"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-18": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "domain",
    "scope"
   ],
   "seed_overwritable_columns": [
    "scope"
   ],
   "seed_divergent_assets_among_them": [
    "mi_jivanaghatana"
   ],
   "durability": "NON-DURABLE",
   "attribution": null,
   "non_durable_proof": {
    "source": "post_reseed_projection",
    "violations_now": 0,
    "violations_after_a_reseed": 1,
    "verdict": "this rule reads 0 today and 1 once asset_registry_seed.ts restores the columns it owns. Its zero is a repair the next seed run reverts, not a fixed defect.",
    "reverted_by": [
     "mi_jivanaghatana"
    ]
   }
  },
  "C-19": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "layer",
    "rung"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "layer"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "EXPOSED",
   "attribution": null
  },
  "C-20": {
   "status": "FAIL",
   "violations": 3,
   "columns_referenced": [
    "asset_id",
    "asset_kind",
    "catalog_status",
    "target_floor"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "catalog_status"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-21": {
   "status": "FAIL",
   "violations": 19,
   "columns_referenced": [
    "asset_id",
    "target_floor",
    "volume_explanation"
   ],
   "seed_overwritable_columns": [
    "volume_explanation"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  },
  "C-24": {
   "status": "PASS",
   "violations": 0,
   "columns_referenced": [
    "asset_id",
    "clear_tables",
    "target_table"
   ],
   "seed_overwritable_columns": [
    "target_table"
   ],
   "seed_divergent_assets_among_them": [],
   "durability": "durable",
   "attribution": null
  },
  "C-28": {
   "status": "FAIL",
   "violations": 31,
   "columns_referenced": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "durability": "n/a \u2014 not passing",
   "attribution": null
  }
 },
 "per_criterion": {
  "1_three_way_diff": {
   "status": "FAIL",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "2_contract_violations_per_kind": {
   "status": "NOT-MEASURABLE",
   "columns_read": [
    "asset_id",
    "asset_kind",
    "asset_type",
    "catalog_status",
    "clear_tables",
    "count_sql",
    "data_disposition",
    "depends_on",
    "domain",
    "health_probe",
    "layer",
    "layer_index",
    "layer_name",
    "provides_apis",
    "rung",
    "scope",
    "service_health",
    "superseded_by",
    "target_floor",
    "target_table",
    "volume_explanation"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "asset_type",
    "catalog_status",
    "count_sql",
    "depends_on",
    "health_probe",
    "layer",
    "layer_index",
    "layer_name",
    "provides_apis",
    "scope",
    "target_table",
    "volume_explanation"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga",
    "ka_dasha_kala",
    "ka_graha_sancara",
    "ka_muhurta_seva",
    "ka_tulana",
    "mi_abhilekha",
    "mi_jivanaghatana",
    "mi_seva"
   ],
   "constituent_rules": [
    "C-01",
    "C-02",
    "C-03",
    "C-04",
    "C-05",
    "C-06",
    "C-07",
    "C-08",
    "C-09",
    "C-10",
    "C-11",
    "C-12",
    "C-13a",
    "C-14",
    "C-15",
    "C-16",
    "C-17",
    "C-18",
    "C-19",
    "C-20",
    "C-21",
    "C-24",
    "C-28"
   ],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [
    "clear_tables",
    "data_disposition",
    "domain",
    "rung",
    "service_health",
    "superseded_by",
    "target_floor"
   ],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [
    "C-05",
    "C-14",
    "C-18"
   ],
   "rules_whose_projection_failed": []
  },
  "3_prefix_mismatches": {
   "status": "FAIL",
   "columns_read": [
    "asset_id",
    "asset_kind",
    "layer"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "layer"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "constituent_rules": [
    "C-01"
   ],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "4_dangling_or_draft_edges": {
   "status": "FAIL",
   "columns_read": [
    "asset_id",
    "asset_kind",
    "catalog_status",
    "depends_on"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "catalog_status",
    "depends_on"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "constituent_rules": [
    "C-11",
    "C-12"
   ],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "5_multi_producer_partitions": {
   "status": "NOT-MEASURABLE",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "6_throughput_on_inactive_assets": {
   "status": "BLOCKED",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "7_retired_without_disposition": {
   "status": "FAIL",
   "columns_read": [
    "asset_id",
    "catalog_status",
    "data_disposition"
   ],
   "seed_overwritable_columns": [
    "catalog_status"
   ],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [
    "C-08"
   ],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [
    "data_disposition"
   ],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "8_active_without_coverage_or_dead_flag": {
   "status": "NOT-MEASURABLE",
   "columns_read": [
    "asset_id",
    "asset_kind",
    "catalog_status",
    "has_writer",
    "is_active"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "catalog_status",
    "is_active"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga"
   ],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [
    "has_writer"
   ],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "9_unresolved_zero_consumer": {
   "status": "PASS",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "durable",
   "why": "criterion is not sourced from asset_registry columns the seed writes",
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "10_ci_guard_merged_and_blocking": {
   "status": "FAIL",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  },
  "11_domain_and_rung_present": {
   "status": "PASS",
   "columns_read": [
    "asset_id",
    "asset_kind",
    "domain",
    "layer",
    "rung",
    "scope"
   ],
   "seed_overwritable_columns": [
    "asset_kind",
    "layer",
    "scope"
   ],
   "seed_divergent_assets_among_them": [
    "bg_ephemeris_engine",
    "bg_panchanga",
    "mi_jivanaghatana"
   ],
   "constituent_rules": [
    "C-18",
    "C-19"
   ],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [
    "domain",
    "rung"
   ],
   "durability": "NON-DURABLE",
   "why": "projected forward: constituent rule(s) ['C-18'] start firing once asset_registry_seed.ts restores the columns it owns",
   "rules_that_break_after_a_reseed": [
    "C-18"
   ],
   "rules_whose_projection_failed": []
  },
  "12_ci_domain_coherence_green": {
   "status": "FAIL",
   "columns_read": [],
   "seed_overwritable_columns": [],
   "seed_divergent_assets_among_them": [],
   "constituent_rules": [],
   "non_durable_constituent_rules": [],
   "columns_the_seed_never_inserts": [],
   "durability": "n/a \u2014 not passing",
   "why": null,
   "rules_that_break_after_a_reseed": [],
   "rules_whose_projection_failed": []
  }
 }
}
```

</details>

---

## 4 — What this scorecard does NOT establish

- It does not certify M0. It measures. Certification is PARĪKṢAKA's (I16 / H7), and the freeze is M0-T10's.
- A **PASS** here means one detector returned zero at one instant against one database. It is not a claim that the underlying property is guaranteed going forward — that is what criterion 10's CI guard would be for, and criterion 10 does not pass.
- **NOT-MEASURABLE is not a soft PASS.** Criteria 5 and 8 have no detector at all, and criterion 2 carries three rules (C-25/C-26/C-27) the contract itself marks un-checkable. Any dashboard that renders those green is itself the defect this campaign exists to remove.
- Criterion 6 is neither PASS nor FAIL. Its single offender is the charter's named unrecoverable asset; resolving it is a reserved power (P1) and rung R3's work. This task recorded the collision and did not touch it. **Criterion 7 has the same single offender** (`ka_gochara_sweep`, the one RETIRED row, now measurably missing a `data_disposition`): it reads FAIL because a detector ran and returned 1, and that is the honest status, but the row behind it is equally reserved and equally untouched.
- A **durable** green in §3b means only that no column the criterion reads is overwritten by the seed. It is not a guarantee: the seed is one write path among several, and a migration or a writer can still move the same cell.
- Criterion 10's detector was REPAIRED in this reading. Its predecessor computed `PASS if a guard file exists and some workflow names it` while asserting 'merged AND blocking' — the word *blocking* had no code path, so no input could make that half false. Against the current tree that constant would have reported PASS. It now parses `continue-on-error` / `|| true` and checks presence on `origin/main`, and reads FAIL. The correction is recorded here rather than quietly applied, because a detector that changed its own answer is exactly the thing a reader must be able to audit.
- The decorator scan follows no imports: a writer base class defined outside `platform/python-sidecar` is invisible to the C-23 derivation. Stated, not hidden.
- The seed `.ts` is regex-parsed as text, never imported (D-9 / D-13). A seed entry whose `asset_id:` is written on a continuation line would be missed.

