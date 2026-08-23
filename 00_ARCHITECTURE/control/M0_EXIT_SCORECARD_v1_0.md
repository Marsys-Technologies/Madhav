---
artifact: M0_EXIT_SCORECARD
version: 1.0
status: LIVE-MEASUREMENT
task: M0-T17
generated: 2026-08-23T05:05:59.484414+00:00
generator: 00_ARCHITECTURE/control/m0_exit_scorecard.py
---

# NIRMĀṆA M0 — Exit-Criteria Scorecard v1.0

**Measured:** 2026-08-23T05:05:53.330487+00:00 → 2026-08-23T05:05:59.484414+00:00 (UTC)  
**Branch / commit:** `campaign/nirmana-autonomous` @ `01397f9216de`  
**Database access:** READ-ONLY (default_transaction_read_only=on; SELECT only)  
**Regenerate:** `python3 00_ARCHITECTURE/control/m0_exit_scorecard.py`  
**Status:** measurement only. This document certifies nothing and closes nothing (I16 / charter H7). PARĪKṢAKA decides; M0-T10 re-runs the generator at freeze time rather than trusting this snapshot.

## 0 — Tally

| status | count | meaning |
|---|--:|---|
| PASS | 0 | a detector ran and returned zero |
| FAIL | 6 | a detector ran and returned non-zero |
| NOT-MEASURABLE | 3 | **no detector exists that could return non-zero. Not a pass** (CLAUDE.md §N.8) |
| BLOCKED | 3 | a detector exists but cannot run yet; the blocker is named per row |

**0 of 12 criteria are satisfied by a detector's output.** The other 12 are not, and none of them is green.

### At a glance

| # | criterion | measured | status | blocker |
|---|---|--:|---|---|
| 1 | three-way diff (registry vs `@register` vs seed) = 0 | `5` | **FAIL** | — |
| 2 | contract violations per kind = 0 | `227` | **NOT-MEASURABLE** | rules C-08, C-09, C-10, C-18, C-19 cannot run (migration 590 columns absent); rules C-25, C-26, C-27 have NO d… |
| 3 | prefix mismatches = 0 | `1` | **FAIL** | — |
| 4 | dangling or DRAFT-targeted edges = 0 | `3` | **FAIL** | — |
| 5 | multi-producer partitions = 0 | `—` | **NOT-MEASURABLE** | NO DETECTOR EXISTS. The criterion asserts that no two producers write the same (table × generation × partition… |
| 6 | throughput rows on inactive assets = 0 | `3` | **BLOCKED** | CHARTER §2 P1 COLLISION — the only offender is `ka_gochara_sweep`, the charter's named unrecoverable asset. An… |
| 7 | retired assets without a `data_disposition` = 0 | `—` | **BLOCKED** | column(s) ['data_disposition'] do not exist in asset_registry (migration 590 not applied) |
| 8 | active assets with neither build coverage nor a dead flag = 0 | `—` | **NOT-MEASURABLE** | NO 'DEAD FLAG' FIELD IS DEFINED. asset_registry has no column that designates a registered-but-dead asset. `ha… |
| 9 | unresolved zero-consumer findings = 0 | `23` | **FAIL** | — |
| 10 | CI guard merged and **blocking** | `{"guard_scripts_found": 1, "workflow_invocations_found": 0}` | **FAIL** | — |
| 11 | every asset carrying `domain` and `rung` *(v4.1)* | `—` | **BLOCKED** | columns `domain` and/or `rung` do not exist in asset_registry (migration 590 not applied). Present: {'domain':… |
| 12 | the §11 CI domain-coherence assertion green *(v4.1)* | `—` | **FAIL** | THE ASSERTION DOES NOT EXIST. Plan §11 requires the CI shape guard to assert domain coherence (a shared asset … |

### Did anything move while this ran?

A migration wave was running concurrently, so every load-bearing quantity was read again at the end of the run:

| quantity | at start | at end |
|---|--:|--:|
| `asset_registry` rows | 128 | 128 |
| throughput rows on inactive assets | 3 | 3 |
| contract columns added/removed mid-run | — | none |

**Anything moved: no.** Contract columns present at end of run: `{'domain': False, 'rung': False, 'data_disposition': False, 'superseded_by': False}`.

### What changed since the previous run of this generator

Previous run: `2026-08-23T05:05:31.301710+00:00`. no criterion changed status or value since the previous run.

Filesystem-sourced criteria (10 and 12) can move between runs without any database change, because sibling tasks are authoring the guards they look for. The block above is where that shows up; the table above it covers database movement inside a single run.

Most recent rows of `_migrations_applied`:

- `588_samiksha_digest_journal.sql` — 2026-08-22 23:42:20.550183+00:00
- `587_llm_usage_events_interpretation_sets_stage.sql` — 2026-08-22 03:31:21.363948+00:00
- `586_f152_asset_throughput_state_audit.sql` — 2026-08-22 02:29:47.385503+00:00
- `585_mi_gunanaka_count_sql_accretion_fix.sql` — 2026-08-22 01:16:12.777849+00:00
- `584_remedy_review_queue_remedy_id_unique.sql` — 2026-08-21 23:28:39.856003+00:00

---

## 1 — The twelve criteria

### 1 · three-way diff (registry vs `@register` vs seed) = 0

**Status: FAIL**  
**Measured value:** `5`  

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

**Status: NOT-MEASURABLE**  
**Measured value:** `227`  

**Detector**

```
this script: every §8 detection SQL of 00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md, run live; plus C-13b (DFS) and C-23 (AST) implemented here.
```

**Blocked by / why this is not a pass:** rules C-08, C-09, C-10, C-18, C-19 cannot run (migration 590 columns absent); rules C-25, C-26, C-27 have NO detector at all (contract §8) and must never read green

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>violations_by_asset_kind</code></summary>

```json
{
 "data": 144,
 "artifact": 0,
 "service": 19,
 "source": 0
}
```

</details>

<details><summary><code>failing_rules</code></summary>

```json
[
 "C-01=1",
 "C-02=21",
 "C-03=20",
 "C-04=11",
 "C-05=2",
 "C-06=1",
 "C-07=4",
 "C-11=3",
 "C-14=6",
 "C-15=6",
 "C-17=4",
 "C-20=5",
 "C-21=19",
 "C-23=12",
 "C-28=112"
]
```

</details>

<details><summary><code>blocked_rules</code></summary>

```json
[
 "C-08",
 "C-09",
 "C-10",
 "C-18",
 "C-19"
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

**Status: FAIL**  
**Measured value:** `1`  

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

**Status: FAIL**  
**Measured value:** `3`  

**Detector**

```
C-12 (dangling: dep with no registry row) + C-11 (CURRENT depending on a non-CURRENT, non-source asset), both run live
```

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

**Status: NOT-MEASURABLE**  
**Measured value:** `None`  

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

**Status: BLOCKED**  
**Measured value:** `3`  

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

**Status: BLOCKED**  
**Measured value:** `None`  

**Detector**

```
SELECT asset_id FROM asset_registry WHERE catalog_status='RETIRED' AND data_disposition IS NULL ORDER BY asset_id
```

**Blocked by / why this is not a pass:** column(s) ['data_disposition'] do not exist in asset_registry (migration 590 not applied)

**Note:** `data_disposition` does not exist as a column; migration 590 (platform/migrations/590_nirmana_m0_catalogue_contract_columns.sql) introduces it. Until it applies this criterion has no detector that could return non-zero. An unmeasurable criterion is not a satisfied one.

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

**Status: NOT-MEASURABLE**  
**Measured value:** `None`  

**Detector**

```
SELECT asset_id, catalog_status, asset_kind, has_writer FROM asset_registry WHERE is_active  -- minus the AST @register set
```

**Blocked by / why this is not a pass:** NO 'DEAD FLAG' FIELD IS DEFINED. asset_registry has no column that designates a registered-but-dead asset. `has_writer` (boolean) is the only candidate, and the contract (ASSET_CATALOGUE_CONTRACT_v1_0.md) does not designate it as the dead flag — nor does it define one. The criterion's second half therefore has no detector, so the criterion as a whole cannot return a non-zero answer honestly. Its FIRST half is measured below.

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
   "asset_kind": "data",
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
   "asset_kind": "data",
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

**Status: FAIL**  
**Measured value:** `23`  

**Detector**

```
count of zero-consumer packets in 00_ARCHITECTURE/control/zero_consumer_evidence.json, minus those with a recorded ADHIKĀRIN G1 disposition naming them in 00_ARCHITECTURE/autonomy/state/DECISIONS.jsonl
```

**Where the number came from:** this script's own live query. A sibling artifact — ZERO_CONSUMER_EVIDENCE_v1_0.md §0/§2 (M0-T6) — reports: 23 packets found live; plan §1 states 13; the plan's own per-asset annotations count 7.

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

**Status: FAIL**  
**Measured value:** `{"guard_scripts_found": 1, "workflow_invocations_found": 0}`  

**Detector**

```
filesystem scan: does a guard implementing the Asset Catalogue Contract exist under platform/scripts/{governance,ci}; is it invoked from a .github/workflows job; is that step blocking
```

**Note:** WORK_QUEUE id M0-T9 ('CI guards, merged and BLOCKING (0.10)') is queued_not_dispatched. Nothing has been built yet, so this reads FAIL — a real detector returning a real non-zero-shortfall, not a block.

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>guard_scripts</code></summary>

```json
[
 "platform/scripts/governance/check_asset_catalogue_contract.py"
]
```

</details>

---

### 11 · every asset carrying `domain` and `rung` *(v4.1)*

**Status: BLOCKED**  
**Measured value:** `None`  

**Detector**

```
C-18 + C-19 detection SQL
```

**Blocked by / why this is not a pass:** columns `domain` and/or `rung` do not exist in asset_registry (migration 590 not applied). Present: {'domain': False, 'rung': False, 'data_disposition': False, 'superseded_by': False}

**Where the number came from:** this script's own live query. A sibling artifact — ASSET_CATALOGUE_CONTRACT §6 rules C-18/C-19 (M0-T2) — reports: 128 / 128 (columns do not exist).

<details><summary><code>would_be_derived_from</code></summary>

```json
{
 "domain": "scope: global->shared, per_chart->chart (contract \u00a75.1)",
 "rung": "layer: brahmagyan->R0 ... mimamsa->R5 (contract \u00a75.2)"
}
```

</details>

---

### 12 · the §11 CI domain-coherence assertion green *(v4.1)*

**Status: FAIL**  
**Measured value:** `None`  

**Detector: NONE.** See the blocker below. An unmeasurable criterion is not a satisfied one.

**Blocked by / why this is not a pass:** THE ASSERTION DOES NOT EXIST. Plan §11 requires the CI shape guard to assert domain coherence (a shared asset may depend only on shared assets). No CI job asserts it: 0 workflow invocations found. 'Green' cannot be read off a check that does not run — CLAUDE.md §N.8. Status FAIL is the honest reading of 'the assertion is green': it is not, because it is not.

**Where the number came from:** this script's own live measurement. No sibling artifact states a figure for this quantity.

<details><summary><code>underlying_condition_measured_here</code></summary>

```json
{
 "what": "shared-domain asset depending on a chart-domain asset",
 "measured_via": "`scope` column (pre-590 equivalent: global<->shared, per_chart<->chart, contract \u00a75.1 is 1:1)",
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

---

## 2 — Contract rule detail (criterion 2's constituents)

| rule | assertion | severity | status | violations |
|---|---|---|---|--:|
| `C-01` | asset_id prefix matches layer | BLOCKING | **FAIL** | 1 |
| `C-02` | layer_index is ^L[0-5]$ and agrees with layer | BLOCKING | **FAIL** | 21 |
| `C-03` | layer_name is the exact lexicon spelling | BLOCKING | **FAIL** | 20 |
| `C-04` | data/artifact => target_table exists | BLOCKING | **FAIL** | 11 |
| `C-05` | data/artifact => count_sql NOT NULL | BLOCKING | **FAIL** | 2 |
| `C-06` | chart-domain count_sql is chart-scoped ($1) | BLOCKING | **FAIL** | 1 |
| `C-07` | service rows carry no data-asset fields | BLOCKING | **FAIL** | 4 |
| `C-08` | RETIRED => data_disposition NOT NULL | BLOCKING | **BLOCKED** | — |
| `C-09` | superseded_by resolves | BLOCKING | **BLOCKED** | — |
| `C-10` | data_disposition only on RETIRED rows | BLOCKING | **BLOCKED** | — |
| `C-11` | CURRENT depends only on CURRENT/source | BLOCKING | **FAIL** | 3 |
| `C-12` | every depends_on element resolves | BLOCKING | **PASS** | 0 |
| `C-13a` | no self-edge | BLOCKING | **PASS** | 0 |
| `C-14` | asset_kind / asset_type coherent | BLOCKING | **FAIL** | 6 |
| `C-15` | service => health_probe AND provides_apis | BLOCKING | **FAIL** | 6 |
| `C-16` | non-service => service_health IS NULL | BLOCKING | **PASS** | 0 |
| `C-17` | no graded service_health without a probe | BLOCKING | **FAIL** | 4 |
| `C-18` | domain present and derived from scope | BLOCKING | **BLOCKED** | — |
| `C-19` | rung present and derived from layer | BLOCKING | **BLOCKED** | — |
| `C-20` | CURRENT data/artifact carries a floor | BLOCKING | **FAIL** | 5 |
| `C-21` | target_floor = 0 => volume_explanation | BLOCKING | **FAIL** | 19 |
| `C-24` | clear_tables exist and include target_table | BLOCKING | **PASS** | 0 |
| `C-28` | estimated_seconds NOT NULL where a successful build exists | BLOCKING | **FAIL** | 112 |
| `C-13b` | depends_on graph acyclic | — | **PASS** | 0 |
| `C-22` | rung-frozen data assets carry integrity_check_sql | — | **NOT-MEASURABLE** | — |
| `C-23` | has_substeps equals the writer-class truth | — | **FAIL** | 12 |
| `C-25` | co-written target_table => every co-writer declares its partition | — | **NOT-MEASURABLE** | — |
| `C-26` | generation-bearing asset declares its authority pointer | — | **NOT-MEASURABLE** | — |
| `C-27` | writer_timeout_seconds set from telemetry p95 | — | **NOT-MEASURABLE** | — |

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
| C-04 — data/artifact rows failing the target_table rule | `11` | ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-04 | 10 | **YES** |
| C-17 — graded service_health with no health_probe | `4` | ASSET_CATALOGUE_CONTRACT_v1_0.md §6, rule C-17 | 3 | **YES** |
| 0.6a — has_substeps false negatives (C-23) | `12` | NIRMANA_ELEVATION_PLAN v3.0 §0.6a / v4.0 (states 14) vs DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md §4 (M0-T8, states 12) | plan 14 · M0-T8 12 | **YES** |
| criterion 9 — zero-consumer findings | `23` | NIRMANA_ELEVATION_PLAN §1 (states 13) · the plan's own per-asset annotations (7) · ZERO_CONSUMER_EVIDENCE_v1_0.md (23 packets) | plan-summary 13 · plan-annotations 7 · M0-T6 packets 23 | **YES** |
| target_table NULL rows (all kinds) | `None` | CENSUS_REPORT.md §5 (M0-T1) states 14; contract §6 C-04 states 10 | census 14 (all rows) · contract 10 (data/artifact only) | no |

- **C-04 — data/artifact rows failing the target_table rule** — Both are right about different things. 10 is the count of data/artifact rows with target_table NULL. The rule as written (and as its own §8 SQL executes) ALSO fails a row whose target_table names a table that does not exist — `bg_sky_calendar` → `bg_sky_events`, which is absent from information_schema.tables. The contract's §6 count reported the NULL half only. 11 is the rule's full result.
- **C-17 — graded service_health with no health_probe** — The contract's §6 cell names 3 assets, all `healthy` (ka_dasha_kala, ka_muhurta_seva, ka_tulana). Its own §8 SQL matches `IN ('healthy','degraded','unhealthy')`, which also catches `ka_graha_sancara` ('unhealthy', no probe). The contract's stated count disagrees with the contract's own SQL. 4 is the SQL's result.
- **0.6a — has_substeps false negatives (C-23)** — This script's detector and M0-T8's are INDEPENDENT and differ in rule — M0-T8 uses (defines plan_substeps AND defines run_substep); this one uses (overrides plan_substeps OR sets the class attribute has_substeps=True), in both cases EXCLUDING WriterBase's own default. Two independent detectors returning 12 against the plan's 14 is corroboration; the plan's figure is the outlier and is not measured.
- **criterion 9 — zero-consumer findings** — This script counts the M0-T6 packet set and subtracts recorded ADHIKĀRIN G1 dispositions; there are none, so unresolved = packets. The plan's 13 has no per-asset list behind it and does not reconcile with the plan's own annotations. Not averaged, not adopted.
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
   "platform/scripts/governance/check_asset_catalogue_contract.py"
  ],
  "workflow_invocations": [],
  "domain_coherence_scripts": [
   "platform/scripts/governance/check_asset_catalogue_contract.py"
  ],
  "domain_coherence_workflow_invocations": [],
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
   ".github/workflows/pariprashna-ci.yml",
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

## 4 — What this scorecard does NOT establish

- It does not certify M0. It measures. Certification is PARĪKṢAKA's (I16 / H7), and the freeze is M0-T10's.
- A **PASS** here means one detector returned zero at one instant against one database. It is not a claim that the underlying property is guaranteed going forward — that is what criterion 10's CI guard would be for, and criterion 10 does not pass.
- **NOT-MEASURABLE is not a soft PASS.** Criteria 5 and 8 have no detector at all, and criterion 2 carries three rules (C-25/C-26/C-27) the contract itself marks un-checkable. Any dashboard that renders those green is itself the defect this campaign exists to remove.
- Criterion 6 is neither PASS nor FAIL. Its single offender is the charter's named unrecoverable asset; resolving it is a reserved power (P1) and rung R3's work. This task recorded the collision and did not touch it.
- The decorator scan follows no imports: a writer base class defined outside `platform/python-sidecar` is invisible to the C-23 derivation. Stated, not hidden.
- The seed `.ts` is regex-parsed as text, never imported (D-9 / D-13). A seed entry whose `asset_id:` is written on a continuation line would be missed.

