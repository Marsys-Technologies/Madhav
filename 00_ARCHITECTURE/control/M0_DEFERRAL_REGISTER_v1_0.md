---
canonical_id: M0_DEFERRAL_REGISTER
version: 1.0
status: LIVE-CLASSIFICATION
task: M0-T31
generated: 2026-08-23T07:15:01.326149+00:00
generator: 00_ARCHITECTURE/control/m0_deferral_register.py
authored_by: KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T31)
certified_by: null   # I16 / charter H7 — a KĀRAKA never certifies its own work
satisfies: DECISIONS.jsonl D-24 part 3 (the precondition for the CI blocking switch)
---

# NIRMĀṆA M0 — Deferral Register v1.0

**The question this document exists to answer**, verbatim from ADHIKĀRIN ruling D-24 part 3:

> *The switch flips when T17's exit scorecard shows each criterion either at zero or explicitly deferred with a recorded reason — **never on a criterion that is merely unexamined**.*

The scorecard measures; it does not separate *non-zero and repairable* from *non-zero and cannot reach zero, for a stated reason*. This register performs that separation and — the actual work product — names what nobody has yet established either way.

**This document decides nothing, flips nothing, and certifies nothing.** No guard file, no `.github/` file and no `asset_registry` row was written by the task that produced it. Classification is evidence for ADHIKĀRIN (charter G7/G9); certification is PARĪKṢAKA's (I16 / charter H7).

## 0 — The tally

| bucket | criteria | contract rules | total | meaning |
|---|--:|--:|--:|---|
| **REPAIRABLE-IN-M0** | 3 | 3 | **6** | a known repair takes it to zero; nobody has done it. The repair and its blocker are named per entry. |
| **DEFERRED-WITH-REASON** | 2 | 10 | **12** | it cannot reach zero inside M0, and a **ruling, plan assignment, contract mandate or measured structural fact** says why. |
| **RESERVED** | 1 | 1 | **2** | it collides with a charter prohibition. Not the campaign's to resolve, and untouched by this task. |
| **UNEXAMINED** | 5 | 6 | **11** | **nobody has established which of the above it is.** D-24 part 3 forbids flipping the switch on any of these. This bucket is the deliverable. |
| **AT-ZERO-WITH-EXPOSURE** | 1 | 0 | **1** | reads zero, with a named exposure that makes that zero conditional (§5). |
| | **12** | **20** | **32** | |

**11 of 32 entries are UNEXAMINED**, and they reduce to **9 decisions**, not 11 — §6 is that list in order. The largest single lever is the *named-field test* (§6 step 2): one ruling reclassifies six rules and two criteria.

**The one fact that stops the flip even after every ruling lands** is mechanical and is §6 step 10. Exactly **one** rule in the guard — `X-02`, the RESERVED one — carries both an itemised disclosure the guard reads and a severity (`RESIDUAL`) that does not gate. **None of the ten DEFERRED rules has either**, and eight of those ten (`C-01` `C-02` `C-03` `C-08` `C-20` `C-21` `C-25` `C-26`) are `BLOCKING` in the rule table. The guard read live at 06:58:51Z returns **15 BLOCKING failures** (16 failing rules in all, `X-02` being the sixteenth and non-gating). Flipping today reds the branch on all fifteen — several of which could only be made green by touching a charter-P1 asset or by pre-building R5 work.

### What counts as a reason

A reason is only a reason if it names one of these. *"Not yet done"*, *"probably fine"* and *"an analogous ruling exists for a different column"* are **UNEXAMINED**, not deferred — that distinction is the whole point of the exercise, and this register files six rules UNEXAMINED that a looser reading would have called deferred.

| reason kind | what it must cite |
|---|---|
| `ruling` | a line of state/DECISIONS.jsonl, cited by id and part |
| `plan-assignment` | a specific assignment of this exact item to a named rung or phase in NIRMANA_ELEVATION_PLAN (a specific assignment governs a general exit criterion — D-12 part 4) |
| `contract-mandate` | ASSET_CATALOGUE_CONTRACT_v1_0.md states in its own text that the rule has no detector and must never read as passing |
| `structural-fact` | a measured property of the schema, the code or the charter that makes zero unreachable inside M0 — stated with the measurement that shows it |
| `charter-prohibition` | charter §2 reserves the operation, or §3 prohibits it outright |

## 1 — Provenance: every number below was re-measured, not inherited

**Database access:** READ-ONLY throughout (SET default_transaction_read_only=on; SELECT only). Nothing was written to asset_registry, asset_throughput or any guard file.

| reading | at (UTC) | how |
|---|---|---|
| live asset_registry — criterion/rule re-measurement by this task | `2026-08-23T06:55:57Z` | psycopg, read-only, DATABASE_URL read from platform/.env.local as measure_assets.py does (never printed — charter P4) |
| live asset_registry — second pass (C-04/C-06/C-07/C-15/C-17/C-20/C-21 detail) | `2026-08-23T06:56:30Z` | same connection method |
| seed projection — live vs asset_registry_seed.ts, 5 modelled columns | `2026-08-23T06:57:16Z` | 00_ARCHITECTURE/control/seed_durability/extract_seed_projection.mjs (stdout only; writes nothing; the seed module is never imported — D-13, and D-28 part 5 for the inertness-proof method) |
| check_asset_catalogue_contract.py --live --json (C-01…C-28, X-01…X-05) | `2026-08-23T06:58:51Z` | the shipped guard, run READ-ONLY. NOT edited by this task — a sibling task holds the C-23 guard and the workbook generator. |
| check_asset_source_parity.py --live --json (P-01…P-06) | `2026-08-23T07:02:39Z` | the shipped guard, run READ-ONLY |
| C-28 residual measurement (lit assets with no completed build_run_assets row) | `2026-08-23T07:06Z` | read-only SQL, quoted in the C-28 entry |
| origin/main presence of the two guards and the workflow | `2026-08-23T07:03Z` | git fetch origin main; git ls-tree -r --name-only origin/main @ 2670e61e2 |

Files **read and not written** by this task (a sibling task holds `writer_substep_census.py`, `build_asset_control_workbook.py` and the C-23 guard):

- `platform/scripts/governance/check_asset_catalogue_contract.py (mtime 2026-08-23 11:32 local)`
- `platform/scripts/governance/check_asset_source_parity.py (mtime 2026-08-23 10:43 local)`
- `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`
- `platform/scripts/governance/asset_source_parity_allowlist.json`
- `platform/scripts/governance/asset_catalogue_declared_cowriters.json`
- `.github/workflows/nirmana-m0-guards.yml`

**The scorecard moved under this task while it ran, and that is reported rather than smoothed:** M0-T26 landed the Phase 0.5a repair at ~06:51–06:54Z, between the scorecard's reading 2 (06:20:44Z) and this register's measurements (06:55:57Z onward). C-02 and C-03 moved 21→1 and 20→1 in that window. Both readings are stated with their timestamps in §7; neither is averaged.

## 2 — The twelve exit criteria

| # | criterion | reads now | bucket | owner |
|---|---|---|---|---|
| 1 | three-way diff (registry vs @register vs seed) = 0 | `scorecard_detector_2026-08-23T06:20Z=5; shipped_parity_guard_P-01…P-06_2026-08-23T07:02:39Z=0` | **UNEXAMINED** | ADHIKĀRIN (G9) — then whichever rung the surviving ids belong to |
| 2 | contract violations per kind = 0 | `scorecard_2026-08-23T06:20Z_violations_by_kind={'data': 136, 'service': 16, 'artifact': 0, 'source': 0}; guard` | **UNEXAMINED** | ADHIKĀRIN (G9) |
| 3 | prefix mismatches = 0 | `live_2026-08-23T06:55:57Z=1; guard_C-01_2026-08-23T06:58:51Z=1` | **DEFERRED-WITH-REASON** | R5 (Mīmāṃsā rung), stage 2 Conform |
| 4 | dangling or DRAFT-targeted edges = 0 | `dangling_C-12=0; CURRENT→DRAFT_C-11=3; at=2026-08-23T06:58:51Z` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (G1 + the bound reconciliation); execution is a KĀRAKA task |
| 5 | multi-producer partitions = 0 | `C-25=not_checkable — no schema column; X-01_undeclared_collisions_2026-08-23T06:58:51Z=0; co_written_target_ta` | **UNEXAMINED** | ADHIKĀRIN (G9, and P5 if a column is involved) |
| 6 | throughput rows on inactive assets = 0 | `live_2026-08-23T06:55:57Z={'assets': 1, 'rows': 3, 'states': ['error']}` | **RESERVED** | R3 (Kāla rung) for the lifecycle exit; the native for anything P1 reaches |
| 7 | retired assets without a data_disposition = 0 | `live_2026-08-23T06:55:57Z=1; guard_C-08_2026-08-23T06:58:51Z=1; note=moved BLOCKED → FAIL when migration 590 s` | **DEFERRED-WITH-REASON** | R3 (Kāla rung), lifecycle exit |
| 8 | active assets with neither build coverage nor a dead flag = 0 | `scorecard_2026-08-23T06:20Z=NOT-MEASURABLE (no dead-flag field is defined); guard_X-03_2026-08-23T06:58:51Z=2` | **UNEXAMINED** | ADHIKĀRIN (G9; P5 if a new column is the answer) |
| 9 | unresolved zero-consumer findings = 0 | `packets=23; dispositions_recorded=0; at=2026-08-23T06:58:51Z` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (G1 ×23); recording them is a KĀRAKA task |
| 10 | CI guard merged and blocking | `guard_scripts_found=2; workflow_invocations=4; merged_to_origin_main_2026-08-23T07:03Z=False; invocation_is_bl` | **UNEXAMINED** | ADHIKĀRIN (G9 for both halves) |
| 11 | every asset carrying domain and rung (v4.1) | `C-18_domain_null_or_wrong=0; C-19_rung_null_or_wrong=0; at=2026-08-23T06:55:57Z` | **AT-ZERO-WITH-EXPOSURE** | ADHIKĀRIN for the scope/domain ownership fix (D-27's divergence-report mandate); the column-level backfill is done |
| 12 | the §11 CI domain-coherence assertion green (v4.1) | `assertion_exists=True; guard_X-04_2026-08-23T06:58:51Z=0; has_ever_run_in_CI=False; note=the scorecard's readi` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (via criterion 10) |

### crit-1 · three-way diff (registry vs @register vs seed) = 0

**Bucket: UNEXAMINED**

**Reads now**

```json
{
 "scorecard_detector_2026-08-23T06:20Z": 5,
 "shipped_parity_guard_P-01…P-06_2026-08-23T07:02:39Z": 0
}
```

THE CRITERION HAS TWO DETECTORS AND THEY DISAGREE BY CONSTRUCTION, AND NOBODY HAS RULED WHICH ONE IS THE CRITERION. The scorecard counts every id not present in all three sources (5). The shipped guard — the thing a blocking flip would actually gate on — does NOT treat 'in registry and in seed but with no production @register' as a violation at all: check_asset_source_parity.py:254 reports those four ids (bg_ephemeris_engine, bg_panchanga, bg_sarvatobhadra_grid, lel_events) as a DETAIL under P-03, on the reasoning that a service row and a source row legitimately have no writer. The fifth (bg_gochara_citation_resolution) is excused by a disclosure naming R0 as its owner. So the same criterion reads 5 and 0 depending on which detector is asked, and 'zero' means two different things. That is not a repair question; it is a definition question, and it is unasked.

**Owner:** ADHIKĀRIN (G9) — then whichever rung the surviving ids belong to  
**Closes when:** ADHIKĀRIN rules which detector expresses the criterion. Under the guard's reading it is already at zero. Under the scorecard's reading it needs 4 service/source exemptions ruled and 1 R0 disposition (G1).

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "bg_gochara_citation_resolution",
  "rung": "R0",
  "class": "registry_only",
  "sub_bucket": "DEFERRED-WITH-REASON",
  "note": "CURRENT, is_active, has_writer=false, in NEITHER the writer tree NOR the seed, never built. Its disposition (provision / demote / retire) is charter G1, whose bound is 'only assets in the current rung' and no rung is open. Recorded in ASSET_CATALOGUE_CONTRACT §7 and in asset_source_parity_allowlist.json as R0-owned. REASON RECORDED BY A KĀRAKA DISCLOSURE, NOT BY A RULING — ADHIKĀRIN has never countersigned it (`certified_by: null` in that file)."
 },
 {
  "asset_id": "bg_ephemeris_engine",
  "rung": "R0",
  "class": "registry+seed_not_decorator",
  "sub_bucket": "UNEXAMINED",
  "note": "asset_kind='service' since the M0-T21 kind repair. A service has no writer by definition; whether the criterion should exempt services has never been ruled."
 },
 {
  "asset_id": "bg_panchanga",
  "rung": "R0",
  "class": "registry+seed_not_decorator",
  "sub_bucket": "UNEXAMINED",
  "note": "same as bg_ephemeris_engine."
 },
 {
  "asset_id": "bg_sarvatobhadra_grid",
  "rung": "R0",
  "class": "registry+seed_not_decorator",
  "sub_bucket": "UNEXAMINED",
  "note": "asset_kind='data', CURRENT, has_writer=false — a CURRENT data asset nothing builds, which contract §7 names as the thing never to leave standing. Same G1 shape as bg_gochara_citation_resolution but with NO disclosure and no ruling."
 },
 {
  "asset_id": "lel_events",
  "rung": "R5",
  "class": "registry+seed_not_decorator",
  "sub_bucket": "DEFERRED-WITH-REASON",
  "note": "D-23: the SOURCE reclassification is R5, not M0."
 }
]
```

</details>

**Evidence**

- 00_ARCHITECTURE/control/M0_EXIT_SCORECARD_v1_0.md §1 criterion 1 (reading 2)
- check_asset_source_parity.py --live 2026-08-23T07:02:39Z: P-01…P-06 all pass; P-03 detail registry_and_seed_not_decorator = the 4 ids
- platform/scripts/governance/asset_source_parity_allowlist.json (bg_gochara_citation_resolution, class registry_only, owner 'R0 — NOT M0', certified_by null)
- CHARTER.md §1 G1 bound; DECISIONS.jsonl D-23

---

### crit-2 · contract violations per kind = 0

**Bucket: UNEXAMINED**

**Reads now**

```json
{
 "scorecard_2026-08-23T06:20Z_violations_by_kind": {
  "data": 136,
  "service": 16,
  "artifact": 0,
  "source": 0
 },
 "guard_live_2026-08-23T06:58:51Z": {
  "pass": 13,
  "fail": 16,
  "not_checkable": 4
 }
}
```

COMPOSITE — its 33 constituent rules are classified individually in §4, and the criterion as a whole is UNEXAMINED FOR A REASON THAT IS NOT ABOUT ANY OF THEM: as written ('violations per kind = 0') it can NEVER be satisfied, because C-25, C-26 and C-27 have no detector and the contract forbids reporting them as passing. A criterion that cannot read zero needs either a column (making the rules checkable) or a re-wording ('every CHECKABLE rule at zero, the un-checkable ones reported not_checkable with their reason'). Neither has been decided, so the criterion is not deferrable — its own terms are undecided.

**Owner:** ADHIKĀRIN (G9)  
**Closes when:** the wording question is ruled AND every constituent rule in §4 is at zero or carries a recorded deferral the guard can read.

**Evidence**

- ASSET_CATALOGUE_CONTRACT_v1_0.md §6 closing paragraph and §8
- check_asset_catalogue_contract.py:1069-1109 (C-25/26/27 hard-wired NOT_CHECKABLE)
- M0_EXIT_SCORECARD_v1_0.md §1 criterion 2

---

### crit-3 · prefix mismatches = 0

**Bucket: DEFERRED-WITH-REASON** · reason kind: `ruling`

**Reads now**

```json
{
 "live_2026-08-23T06:55:57Z": 1,
 "guard_C-01_2026-08-23T06:58:51Z": 1
}
```

The single offender is `lel_events` (prefix 'lel', layer 'mimamsa'). C-01 exempts `asset_kind='source'` rows, so the mismatch disappears the moment lel_events is reclassified SOURCE — and D-23 REVERSED D-21 and assigned that reclassification to R5 by name, on plan §8.4's R5 row ('LEL_EVENTS RECLASSIFIED SOURCE'), holding additionally that widening the asset_kind CHECK now would be pre-building infrastructure for a later phase. This criterion therefore cannot reach zero inside M0 by any authorised route.

**Owner:** R5 (Mīmāṃsā rung), stage 2 Conform  
**Closes when:** R5 opens, the asset_kind CHECK is widened to admit the contract's SOURCE token, and lel_events is reclassified by a G1 exercise on census evidence.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "lel_events",
  "rung": "R5",
  "sub_bucket": "DEFERRED-WITH-REASON",
  "note": "live: layer=mimamsa, asset_kind=data, catalog_status=DRAFT, target_table NULL"
 }
]
```

</details>

**Evidence**

- DECISIONS.jsonl D-23 (reverses D-21)
- NIRMANA_ELEVATION_PLAN_v4_0.md:862 §8.4 R5 row
- ASSET_CATALOGUE_CONTRACT_v1_0.md §7 and §10.1
- live query 2026-08-23T06:55:57Z returned exactly this one row

---

### crit-4 · dangling or DRAFT-targeted edges = 0

**Bucket: REPAIRABLE-IN-M0**

**Reads now**

```json
{
 "dangling_C-12": 0,
 "CURRENT→DRAFT_C-11": 3,
 "at": "2026-08-23T06:58:51Z"
}
```

THE REPAIR IS NAMED AND NOBODY HAS DONE IT. Plan Phase 0.8b — an M0 step — reads '34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced'. Each of the three edges closes by promoting the DRAFT dependency to CURRENT (charter G1) or by recording why it stays DRAFT. Both are catalogue dispositions on evidence M0 already holds (DRAFT_INVENTORY / CONSUMER_MAP).

**What blocks it:** G1's charter bound reads 'Only assets in the current rung, on M0 census evidence' and NO RUNG IS OPEN. Phase 0.8b assigns the work to M0; G1's bound appears to withhold the power that performs it. That collision must be ruled before any promotion is written — it is the same collision criterion 9 sits behind, so one ruling clears both.

**Owner:** ADHIKĀRIN (G1 + the bound reconciliation); execution is a KĀRAKA task  
**Closes when:** three dispositions are ruled and written: ga_vichara (R1), ka_dasha_kala (R3), ka_sangam (R3) — promoted, or the dependants justified.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "bo_laksana",
  "dep": "ga_vichara",
  "dep_status": "DRAFT",
  "dep_rung": "R1"
 },
 {
  "asset_id": "ka_kshetra",
  "dep": "ka_dasha_kala",
  "dep_status": "DRAFT",
  "dep_rung": "R3"
 },
 {
  "asset_id": "ka_taranga",
  "dep": "ka_sangam",
  "dep_status": "DRAFT",
  "dep_rung": "R3"
 }
]
```

</details>

**Evidence**

- guard C-11 live 2026-08-23T06:58:51Z (3 rows, class current_depends_on_draft)
- NIRMANA_ELEVATION_PLAN_v3_0.md §Phase 0 step 0.8b (the 15-step table §14.4 maps to M0)
- CHARTER.md §1 G1 bound

---

### crit-5 · multi-producer partitions = 0

**Bucket: UNEXAMINED**

**Reads now**

```json
{
 "C-25": "not_checkable — no schema column",
 "X-01_undeclared_collisions_2026-08-23T06:58:51Z": 0,
 "co_written_target_tables": 5
}
```

THE TEMPTING ANSWER IS 'DEFERRED — NO COLUMN EXISTS', AND IT IS WRONG. The absence of a partition column is a real structural fact and it is what makes C-25 permanently not_checkable (§4). But the CRITERION is not the rule: plan Phase 0.4 — an M0 step — reads '(table × generation × partition) invariant; correct the gochara attribution; DECLARE CO-WRITER PARTITIONS'. M0 is the phase the plan assigns this work to. Under D-4's own reasoning ('a criterion that cannot be met without a change has NAMED that change even where it numbers no migration') a partition-declaration column is arguably already authorised; under D-23's correction it may instead belong to each rung. Nobody has asked, so this is not deferred — it is undecided. What exists today is X-01, which passes and means only 'no multi-producer table that nobody declared' — its own docstring refuses the stronger reading.

**Owner:** ADHIKĀRIN (G9, and P5 if a column is involved)  
**Closes when:** either a partition-declaration column is authorised and the 16 co-writer rows across 5 tables declare their partitions, or the item is deferred to the owning rungs with the reason recorded.

<details><summary>rows</summary>

```json
[
 {
  "target_table": "bodha_msr_signals",
  "producers": 7
 },
 {
  "target_table": "chart_facts",
  "producers": 5
 },
 {
  "target_table": "brahma_class_priors",
  "producers": 2
 },
 {
  "target_table": "classical_text_chunks",
  "producers": 2
 },
 {
  "target_table": "kala_gochara_windows",
  "producers": 2,
  "note": "ka_gochara (CURRENT) + ka_gochara_sweep (RETIRED, charter P1)"
 }
]
```

</details>

**Evidence**

- ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9, §10.3; rule C-25
- platform/scripts/governance/asset_catalogue_declared_cowriters.json _README ('Listing a table here means these producers are known and expected, never that these producers are correct')
- NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.4
- DECISIONS.jsonl D-4, D-23

---

### crit-6 · throughput rows on inactive assets = 0

**Bucket: RESERVED** · reason kind: `charter-prohibition`

**Reads now**

```json
{
 "live_2026-08-23T06:55:57Z": {
  "assets": 1,
  "rows": 3,
  "states": [
   "error"
  ]
 }
}
```

The only offender is `ka_gochara_sweep` — charter §2 P1's NAMED unrecoverable asset (38,287 v1 gochara rows whose only recovery path is the 2026-08-23 snapshot). Any operation on it is a reserved power: parked, never decided by an agent. D-12 part 4 additionally dissolves the apparent M0-vs-P1 collision without needing P1 at all — plan §14.2 assigns these exact rows to R3 by name, and 'a specific assignment governs a general exit criterion' — and rules that M0 CLOSES WITH THIS CRITERION EXPLICITLY UNMET AND RECORDED AS DEFERRED-TO-R3, never silently green. THIS REGISTER DID NOT TOUCH THE ROWS, AND NOTHING IN M0 MAY.

**Owner:** R3 (Kāla rung) for the lifecycle exit; the native for anything P1 reaches  
**Closes when:** R3 opens and completes ka_gochara_sweep's lifecycle exit. Not in M0, on any reading.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "ka_gochara_sweep",
  "rung": "R3",
  "catalog_status": "RETIRED",
  "is_active": false,
  "throughput_rows": 3,
  "states": [
   "error"
  ],
  "note": "state='error' is at least not a false green (D-12 part 4). The guard reports it as X-02 with severity RESIDUAL and an itemised disclosure, and the disclosure deliberately DOES NOT turn the rule green."
 }
]
```

</details>

**Evidence**

- CHARTER.md §2 P1
- DECISIONS.jsonl D-12 part 4
- NIRMANA_ELEVATION_PLAN_v4_0.md §14.2
- platform/scripts/governance/asset_catalogue_disclosed_residuals.json disclosed_additions
- live query 2026-08-23T06:55:57Z: 1 asset, 3 rows, all state='error'

---

### crit-7 · retired assets without a data_disposition = 0

**Bucket: DEFERRED-WITH-REASON** · reason kind: `plan-assignment`

**Reads now**

```json
{
 "live_2026-08-23T06:55:57Z": 1,
 "guard_C-08_2026-08-23T06:58:51Z": 1,
 "note": "moved BLOCKED → FAIL when migration 590 supplied the data_disposition column at 2026-08-23T05:36:13Z; the detector now exists and returns 1"
}
```

One RETIRED row exists and it is `ka_gochara_sweep`. Plan §14.2 names its data_disposition explicitly among R3's outstanding items — 'the zombie throughput rows behind its standing no-writer-registered red, AND ITS data_disposition, are still outstanding' — and D-12 part 4 quotes that sentence in ruling the same asset's items R3-owned. A specific assignment governs a general exit criterion.

**Machinery gap:** THE DEFERRAL IS RECORDED IN THE LEDGER BUT NOT IN THE GUARD. Only X-02 has an entry in asset_catalogue_disclosed_residuals.json and only X-02 carries severity RESIDUAL. C-08 is BLOCKING with no disclosure, so a blocking flip today reds the branch on this criterion — and the only way to make it green would be to touch a P1 asset, which is exactly the pressure charter H3 exists to refuse.

**Owner:** R3 (Kāla rung), lifecycle exit  
**Closes when:** R3 writes the disposition. NOTE THE SECOND-ORDER QUESTION NOBODY HAS ASKED: writing data_disposition touches the REGISTRY ROW, not the corpus. Whether charter P1 reaches an asset's registry metadata or only its data has never been ruled; it does not change this deferral (R3 owns it either way) but it will matter the moment R3 opens.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "ka_gochara_sweep",
  "rung": "R3",
  "catalog_status": "RETIRED",
  "data_disposition": null,
  "reserved_asset": true
 }
]
```

</details>

**Evidence**

- DECISIONS.jsonl D-12 part 4
- NIRMANA_ELEVATION_PLAN_v4_0.md §14.2
- live query 2026-08-23T06:55:57Z: the one RETIRED row, data_disposition NULL
- _migrations_applied: 590_nirmana_m0_catalogue_contract_columns.sql @ 2026-08-23T05:36:13Z

---

### crit-8 · active assets with neither build coverage nor a dead flag = 0

**Bucket: UNEXAMINED**

**Reads now**

```json
{
 "scorecard_2026-08-23T06:20Z": "NOT-MEASURABLE (no dead-flag field is defined)",
 "guard_X-03_2026-08-23T06:58:51Z": 2
}
```

THE TWO DETECTORS DISAGREE ABOUT WHETHER THE CRITERION IS MEASURABLE AT ALL. The scorecard says NOT-MEASURABLE: asset_registry has no column designating a registered-but-dead asset, the contract defines none, and has_writer — the only candidate — was itself wrong on 2 rows (D-25). The shipped guard's X-03 reads has_writer as the proxy anyway and returns 2 violations. Meanwhile plan Phase 0.8a — an M0 step — reads 'Registered-but-dead FLAGGED (bg_gochara_citation_resolution)', i.e. M0 is asked to produce a flag that has nowhere to live. Defining the flag, ruling the proxy sufficient, or deferring the whole criterion are three different answers and none has been given.

**Owner:** ADHIKĀRIN (G9; P5 if a new column is the answer)  
**Closes when:** the flag question is ruled, and then the two rows below are dispositioned by whoever owns them.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "bg_gochara_citation_resolution",
  "rung": "R0",
  "catalog_status": "CURRENT",
  "sub_bucket": "DEFERRED-WITH-REASON",
  "note": "disclosed R0-owned in the parity allowlist; not countersigned"
 },
 {
  "asset_id": "lel_events",
  "rung": "R5",
  "catalog_status": "DRAFT",
  "sub_bucket": "DEFERRED-WITH-REASON",
  "note": "D-23 — R5"
 }
]
```

</details>

**Evidence**

- M0_EXIT_SCORECARD_v1_0.md §1 criterion 8
- guard X-03 live 2026-08-23T06:58:51Z
- NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.8a
- DECISIONS.jsonl D-25

---

### crit-9 · unresolved zero-consumer findings = 0

**Bucket: REPAIRABLE-IN-M0**

**Reads now**

```json
{
 "packets": 23,
 "dispositions_recorded": 0,
 "at": "2026-08-23T06:58:51Z"
}
```

THE REPAIR IS NAMED, THE MACHINERY IS BUILT, AND THE RULINGS HAVE NOT BEEN MADE. Plan Phase 0.8c — an M0 step — reads '13 assets: record the consumer or retire with a disposition' (the measured packet count is 23; the plan's 13 has no per-asset list behind it and its own annotations count 7 — the 23 is the measured figure and the one the guard reduces). asset_catalogue_disclosed_residuals.json already carries the `zero_consumer_dispositions` block, and X-05 resolves a packet ONLY on an entry carrying a decision_ref into DECISIONS.jsonl — disposition is charter G1 and no KĀRAKA may self-serve one. The block is empty; 23 rulings are outstanding.

**What blocks it:** the same G1 rung-bound collision as criterion 4: 0.8c assigns the work to M0 while G1's bound reads 'only assets in the current rung' and no rung is open. One ruling clears both criteria.

**Owner:** ADHIKĀRIN (G1 ×23); recording them is a KĀRAKA task  
**Closes when:** each of the 23 packets carries either a recorded consumer or a retire-with-disposition ruling, referenced by decision id in the residuals file.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "bg_cohort",
  "rung": "R0"
 },
 {
  "asset_id": "bg_concordance",
  "rung": "R0"
 },
 {
  "asset_id": "bg_ephemeris_engine",
  "rung": "R0"
 },
 {
  "asset_id": "bg_gochara_arcs",
  "rung": "R0"
 },
 {
  "asset_id": "bg_kota_chakra_rings",
  "rung": "R0"
 },
 {
  "asset_id": "bg_kp_sublord_division",
  "rung": "R0"
 },
 {
  "asset_id": "bg_panchanga",
  "rung": "R0"
 },
 {
  "asset_id": "bg_phaladeepika_latta",
  "rung": "R0"
 },
 {
  "asset_id": "bg_reference",
  "rung": "R0"
 },
 {
  "asset_id": "bg_sarvatobhadra_grid",
  "rung": "R0"
 },
 {
  "asset_id": "bg_sky_calendar",
  "rung": "R0"
 },
 {
  "asset_id": "bg_vedha_malefic_scale",
  "rung": "R0"
 },
 {
  "asset_id": "bg_vidhi_floors",
  "rung": "R0"
 },
 {
  "asset_id": "bg_vidhi_primitives",
  "rung": "R0"
 },
 {
  "asset_id": "bo_cdlm_summary",
  "rung": "R2"
 },
 {
  "asset_id": "bo_samskara",
  "rung": "R2"
 },
 {
  "asset_id": "ka_dasha_kala",
  "rung": "R3"
 },
 {
  "asset_id": "ka_gochara_v3_century_materialize",
  "rung": "R3"
 },
 {
  "asset_id": "ka_graha_sancara",
  "rung": "R3"
 },
 {
  "asset_id": "ka_kshetra",
  "rung": "R3"
 },
 {
  "asset_id": "ka_muhurta_seva",
  "rung": "R3"
 },
 {
  "asset_id": "ka_tulana",
  "rung": "R3"
 },
 {
  "asset_id": "mi_jivanaghatana",
  "rung": "R5"
 }
]
```

</details>

**Evidence**

- guard X-05 live 2026-08-23T06:58:51Z: 23 packets, 0 dispositions recorded
- 00_ARCHITECTURE/control/ZERO_CONSUMER_EVIDENCE_v1_0.md (M0-T6/T7, 23 packets)
- platform/scripts/governance/asset_catalogue_disclosed_residuals.json _README (2)
- NIRMANA_ELEVATION_PLAN_v3_0.md Phase 0 step 0.8c

---

### crit-10 · CI guard merged and blocking

**Bucket: UNEXAMINED**

**Reads now**

```json
{
 "guard_scripts_found": 2,
 "workflow_invocations": 4,
 "merged_to_origin_main_2026-08-23T07:03Z": false,
 "invocation_is_blocking": false,
 "workflow_runs_ever": 0
}
```

TWO HALVES, AND THE HARD ONE IS NOT THE ONE EVERYONE IS LOOKING AT.

(a) BLOCKING — circular, and the circle resolves cleanly once named. This criterion asks whether the guards are blocking; D-24 part 3 makes the switch conditional on every criterion being at zero or explicitly deferred; and THIS REGISTER IS THAT PRECONDITION. If criterion 10 is inside its own precondition, the precondition is unsatisfiable: the switch can never flip, because the thing it waits for is itself. THE RESOLUTION IS NOT TO IGNORE THE CIRCLE BUT TO EXCLUDE THE SWITCH FROM ITS OWN CONDITION — D-24 part 3 quantifies over the criteria the guards would GATE ON, and criterion 10 is not one of those; it is the gate. ADHIKĀRIN should record that carve-out explicitly rather than leave it implicit, because an implicit exception to a stated precondition is exactly the shape of the 'weaken a criterion to get moving' pressure D-24 part 3 warned about. With the carve-out recorded, this half is REPAIRABLE-IN-M0 and is satisfied BY the flip.

(b) MERGED — unexamined, and it collides with a HARD PROHIBITION. 'Merged' means present on the default branch: verified ABSENT from origin/main at 2026-08-23T07:03Z for all three files (git ls-tree @ 2670e61e2), and the workflow has never run (0 runs; the API reports 404 on the default branch). Getting there means merging campaign work into `main` — and charter H2 reads 'Force-push, history rewrite, OR ANY WRITE TO MAIN. All work is on the campaign branch.' Whether a reviewed PR merge is inside H2's prohibition or outside it has never been asked. It is not a KĀRAKA's question and this register does not answer it; it names it, because criterion 10 cannot be satisfied without an answer.

**Owner:** ADHIKĀRIN (G9 for both halves)  
**Closes when:** (a) the self-reference carve-out is recorded and the two `continue-on-error: true` lines are removed by ADHIKĀRIN's own act; (b) H2's reach is ruled, the guards reach origin/main by whatever route that ruling permits, and at least one run executes and reports — a workflow that has never run is not evidence of anything (D-28 part 4: 'a guard that has never had to choose is not yet a detector').

**Evidence**

- git ls-tree -r origin/main @ 2670e61e2, 2026-08-23T07:03Z: nirmana-m0-guards.yml, check_asset_catalogue_contract.py, check_asset_source_parity.py — all ABSENT
- .github/workflows/nirmana-m0-guards.yml:48,87 — `continue-on-error: true` on both jobs
- M0_EXIT_SCORECARD_v1_0.md §1 criterion 10 (github_run_evidence: run_count 0, HTTP 404)
- DECISIONS.jsonl D-24 part 3; CHARTER.md §3 H2, H3

---

### crit-11 · every asset carrying domain and rung (v4.1)

**Bucket: AT-ZERO-WITH-EXPOSURE** · reason kind: `structural-fact`

**Reads now**

```json
{
 "C-18_domain_null_or_wrong": 0,
 "C-19_rung_null_or_wrong": 0,
 "at": "2026-08-23T06:55:57Z"
}
```

AT ZERO, AND NOT THE SAME THING AS BEING AT ZERO. Migration 590 added and backfilled `domain` and `rung`, and neither column is written by the seed at all — so the backfill itself is durable (SEED_DURABILITY_REGISTER §3.3). TWO EXPOSURES SURVIVE ANYWAY. (i) THE PAIR, NOT THE COLUMN: 590 derived `domain` FROM `scope`, and `scope` IS seed-owned. mi_jivanaghatana is live scope='per_chart' → domain='chart', while the seed declares scope='global' → the same row would imply domain='shared'. A re-seed moves one half of the pair and leaves the other, and the row then answers 'which domain am I' two different ways while C-18 still counts it as present. Re-measured independently here at 06:57:16Z: it is the ONLY such row. (ii) COVERAGE OF FUTURE ROWS: both columns are absent from the seed's INSERT list with no NOT NULL / DEFAULT / trigger behind them, so any asset the seed newly inserts lands with both NULL and re-breaks the criterion silently.

**Owner:** ADHIKĀRIN for the scope/domain ownership fix (D-27's divergence-report mandate); the column-level backfill is done  
**Closes when:** the seed-vs-DB divergence report D-27(2b) mandates exists and treats a NULL→value transition as its own category (D-28 part 1), and mi_jivanaghatana's scope is reconciled on the merits in one surface rather than by whoever runs last.

<details><summary>rows</summary>

```json
[
 {
  "asset_id": "mi_jivanaghatana",
  "rung": "R5",
  "live_scope": "per_chart",
  "seed_scope": "global",
  "live_domain": "chart",
  "domain_implied_by_seed_scope": "shared"
 }
]
```

</details>

**Evidence**

- live 2026-08-23T06:55:57Z: domain NULL 0, rung NULL 0, 0 scope→domain mismatches
- seed projection 2026-08-23T06:57:16Z: mi_jivanaghatana scope live per_chart vs seed global
- SEED_DURABILITY_REGISTER_v1_0.md §3.3
- DECISIONS.jsonl D-27, D-28 part 1

---

### crit-12 · the §11 CI domain-coherence assertion green (v4.1)

**Bucket: REPAIRABLE-IN-M0**

**Reads now**

```json
{
 "assertion_exists": true,
 "guard_X-04_2026-08-23T06:58:51Z": 0,
 "has_ever_run_in_CI": false,
 "note": "the scorecard's reading 2 (06:20Z) says 'THE ASSERTION DOES NOT EXIST'. That is stale: X-04 ('domain coherence: a shared asset depends only on shared assets', origin 'plan §11') is implemented in check_asset_catalogue_contract.py and returns 0 violations live."
}
```

REDUCES ENTIRELY TO CRITERION 10. The assertion now exists and passes; what it does not do is RUN — the workflow is not on origin/main, is non-blocking, and has executed zero times. 'Green' cannot be read off a check that has never run (CLAUDE.md §N.8), so the criterion is honestly not-green today for a reason that has nothing to do with domain coherence itself.

**What blocks it:** criterion 10, both halves.

**Owner:** ADHIKĀRIN (via criterion 10)  
**Closes when:** criterion 10 closes and one run reports X-04 green.

**Evidence**

- guard X-04 live 2026-08-23T06:58:51Z: pass, 0 violations
- M0_EXIT_SCORECARD_v1_0.md §1 criterion 12 (reading 2, 06:20Z — superseded on the 'assertion does not exist' clause)

---

## 3 — Contract and extension rules reading non-zero, `not_checkable` or blocked

Rule statuses are the shipped guard's own output — `check_asset_catalogue_contract.py --live --json` at `2026-08-23T06:58:51Z` (13 pass · 16 fail · 4 not_checkable) and `check_asset_source_parity.py --live --json` at `2026-08-23T07:02:39Z` (P-01…P-06 all pass). Rules reading `pass` are listed in §4; §5 covers the ones whose zero is conditional.

| rule | severity | assertion | reads now | bucket | owner |
|---|---|---|---|---|---|
| `C-01` | BLOCKING | asset_id prefix matches layer, non-source rows | `1` | **DEFERRED-WITH-REASON** | R5 |
| `C-02` | BLOCKING | layer_index is ^L[0-5]$ and agrees with layer | `1` | **DEFERRED-WITH-REASON** | R5 |
| `C-03` | BLOCKING | layer_name is the exact lexicon spelling | `1` | **DEFERRED-WITH-REASON** | R5 |
| `C-04` | BLOCKING | data/artifact ⇒ target_table NOT NULL and the table exists | `9` | **UNEXAMINED** | ADHIKĀRIN (the named-field test); then R0/R1/R2 Conform |
| `C-06` | BLOCKING | chart-domain count_sql contains $1 | `1` | **UNEXAMINED** | ADHIKĀRIN (the named-field test); then R5 Conform |
| `C-07` | BLOCKING | service ⇒ target_table / count_sql / target_floor / clear_tables all NULL | `4` | **UNEXAMINED** | ADHIKĀRIN (the named-field test); then R3/R5 Conform |
| `C-08` | BLOCKING | RETIRED ⇒ data_disposition NOT NULL | `1` | **DEFERRED-WITH-REASON** | R3 |
| `C-11` | BLOCKING | CURRENT depends only on CURRENT (or source) | `3` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (G1) |
| `C-15` | BLOCKING | service ⇒ health_probe AND provides_apis NOT NULL | `6` | **UNEXAMINED** | ADHIKĀRIN (the named-field test); then R3/R5 Conform |
| `C-17` | BLOCKING | graded service_health ⇒ health_probe NOT NULL | `4` | **UNEXAMINED** | ADHIKĀRIN (to correct the rung and cover the fourth row); then R3 stage-1 intake |
| `C-20` | BLOCKING | CURRENT data/artifact ⇒ target_floor NOT NULL | `3` | **DEFERRED-WITH-REASON** | R0, stage 2 Conform |
| `C-21` | BLOCKING | target_floor = 0 ⇒ volume_explanation NOT NULL | `19` | **DEFERRED-WITH-REASON** | each row's own rung, stage 2 Conform |
| `C-22` | RUNG | rung-frozen data/artifact ⇒ integrity_check_sql NOT NULL | `not_checkable (vacuous — 0 rungs frozen)` | **DEFERRED-WITH-REASON** | each rung, stage 2 Conform |
| `C-25` | BLOCKING | co-written target_table ⇒ every co-writer declares its partition | `not_checkable` | **DEFERRED-WITH-REASON** | ADHIKĀRIN (§10.3 is an explicitly unsettled fork) |
| `C-26` | BLOCKING | generation-bearing asset declares its authority pointer | `not_checkable` | **DEFERRED-WITH-REASON** | ADHIKĀRIN (§10.3 fork) |
| `C-27` | ADVISORY | writer_timeout_seconds set from telemetry where p95 ≥ 0.5× the value | `not_checkable` | **DEFERRED-WITH-REASON** | M2 (telemetry) |
| `C-28` | BLOCKING | estimated_seconds NOT NULL where a successful build exists | `105` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (confirm D-12 part 5 discharges the flag), then a KĀRAKA executes T-1…T-5 |
| `X-02` | RESIDUAL | no asset_throughput rows on inactive/RETIRED assets | `1` | **RESERVED** | R3 / the native |
| `X-03` | BLOCKING | no active asset with neither build coverage nor a dead flag | `2` | **UNEXAMINED** | ADHIKĀRIN (G9) |
| `X-05` | BLOCKING | no unresolved zero-consumer finding | `23` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (G1 ×23) |

### `C-01` — asset_id prefix matches layer, non-source rows

**Severity BLOCKING · reads `1` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

Same single row and same reason as criterion 3: lel_events, whose SOURCE reclassification D-23 assigned to R5. C-01 exempts source rows, so the reclassification IS the repair and it is not M0's.

**Owner:** R5

Rows: `lel_events`

Evidence: DECISIONS.jsonl D-23 · guard C-01 live 06:58:51Z

---

### `C-02` — layer_index is ^L[0-5]$ and agrees with layer

**Severity BLOCKING · reads `1` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

MOVED 21 → 1 WHILE THIS TASK WAS RUNNING. The scorecard's reading 2 (06:20:44Z) records 21; M0-T26 landed the Phase 0.5a repair at ~06:51–06:54Z; this task measured 1 at 06:55:57Z and the guard measured 1 at 06:58:51Z. The single remaining row is lel_events, whose layer_index is NULL DELIBERATELY: D-28 part 1 rules that this NULL is 'THE ONLY PLACE IN THE REGISTRY WHERE THE OPENNESS OF A RESERVED DECISION IS WRITTEN DOWN' — the correct value is NULL-if-source but L5-if-data, and D-23 reserved that choice to R5. Filling it in M0 would answer a reserved question by default.

**Durability:** DURABLE BY AGREEMENT, measured not assumed: layer_index is seed-owned (DO UPDATE SET), so the repair survives only if it wrote exactly what the seed writes. Compared live-vs-seed at 06:57:16Z across all 127 seed entries: ZERO divergent layer_index cells except lel_events (live NULL, seed 'L5'). The repair agrees with the seed everywhere it touched — and note the corollary D-28 part 1 names: a re-seed would FILL lel_events's deliberate NULL with 'L5', silently answering the reserved question.

**Owner:** R5

Rows: `lel_events`

Evidence: M0_EXIT_SCORECARD_v1_0.md reading 2 (21) · live 06:55:57Z (1) · guard C-02 live 06:58:51Z (1, class layer_index_null) · seed projection 06:57:16Z · DECISIONS.jsonl D-23, D-28 part 1

---

### `C-03` — layer_name is the exact lexicon spelling

**Severity BLOCKING · reads `1` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

Same movement and same reason as C-02: 20 → 1 between the scorecard's reading 2 and this measurement. The surviving row is lel_events (layer_name NULL, deliberate). Live spellings now carry the §N.1 LOCKED diacritics on every populated row — Gaṇita, Kāla, Mīmāṃsā — which D-28 part 6 records as a real §N.1 violation caught PRE-write by a codepoint pin.

**Durability:** DURABLE BY AGREEMENT — measured: zero divergent layer_name cells live-vs-seed at 06:57:16Z other than lel_events (live NULL, seed 'Mīmāṃsā').

**Owner:** R5

Rows: `lel_events`

Evidence: live 06:56:30Z: layer/layer_name distinct pairs — bodha/Bodha 22, brahmagyan/Brahmagyan 40, ganita/Gaṇita 19, kala/Kāla 23, mimamsa/Mīmāṃsā 14, phala/Phala 9, mimamsa/NULL 1 · DECISIONS.jsonl D-28 parts 1 and 6

---

### `C-04` — data/artifact ⇒ target_table NOT NULL and the table exists

**Severity BLOCKING · reads `9` · bucket UNEXAMINED**

NINE ROWS, THREE DIFFERENT SITUATIONS, AND ONLY TWO OF THEM HAVE A REASON ON RECORD. (i) lel_events — DEFERRED to R5 with the rest of its cluster (D-23). (ii) bg_sky_calendar — DEFERRED: its target_table names `bg_sky_events`, a relation ABSENT from production; D-28 part 4 ruled it 'L0 → R0 → not open → UNTOUCHED (I13)' and recorded it as a TRIGGER-BEARING defect for R0 intake (a re-seed's to_regclass pre-flight would switch the asset off). (iii) THE OTHER SEVEN have target_table NULL and no ruling of any kind: bg_prashna_rules (R0), bo_cdlm_summary and bo_chart_gestalt (R2), ga_sade_sati, ga_sensitive, ga_strength, ga_structural (R1). Four of those seven are chart_facts co-writers, where a NULL target_table might be deliberate rather than missing — nobody has established which, and 'probably fine' is not a reason. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** ADHIKĀRIN (the named-field test); then R0/R1/R2 Conform

Rows: `bg_prashna_rules`, `bg_sky_calendar`, `bo_cdlm_summary`, `bo_chart_gestalt`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `lel_events`

Evidence: guard C-04 live 06:58:51Z: 8 × target_table_null + 1 × target_table_missing · DECISIONS.jsonl D-28 part 4, D-23 · DECISIONS.jsonl D-24, D-25 part 2b

---

### `C-06` — chart-domain count_sql contains $1

**Severity BLOCKING · reads `1` · bucket UNEXAMINED**

The single row is mi_seva, whose count_sql should not exist at all: mi_seva is asset_kind='service', and C-07 says a service carries no count_sql. So C-06 is a shadow of C-07 and closes with it. It inherits C-07's bucket for the same reason. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** ADHIKĀRIN (the named-field test); then R5 Conform

Rows: `mi_seva`

Evidence: guard C-06 live 06:58:51Z (1 row, domain=chart, domain_provenance=column) · guard C-07 live 06:58:51Z (mi_seva carries count_sql, target_floor, target_table)

---

### `C-07` — service ⇒ target_table / count_sql / target_floor / clear_tables all NULL

**Severity BLOCKING · reads `4` · bucket UNEXAMINED**

Four service rows carry data-asset fields: ka_dasha_kala and ka_tulana (target_floor), mi_abhilekha and mi_seva (count_sql + target_floor + target_table). The repair is mechanical — NULL four fields — and that is exactly why it must not be done on a KĀRAKA's own reading: none of those columns is named by any Phase 0 step, all four assets are R3/R5, and three of the four columns are SEED-OWNED, so a DB-only NULLing is reverted by the next re-seed anyway. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** ADHIKĀRIN (the named-field test); then R3/R5 Conform

Rows: `ka_dasha_kala`, `ka_tulana`, `mi_abhilekha`, `mi_seva`

Evidence: guard C-07 live 06:58:51Z · SEED_DURABILITY_REGISTER_v1_0.md §1.2 (count_sql, target_floor, target_table all in the seed's DO UPDATE SET)

---

### `C-08` — RETIRED ⇒ data_disposition NOT NULL

**Severity BLOCKING · reads `1` · bucket DEFERRED-WITH-REASON** · reason kind `plan-assignment`

criterion 7's rule. Plan §14.2 names ka_gochara_sweep's data_disposition as R3 work; D-12 part 4 quotes that sentence. Reserved asset (charter P1) — untouched by this task.

**Machinery gap:** BLOCKING severity, no disclosure entry. See criterion 7.

**Owner:** R3

Rows: `ka_gochara_sweep`

Evidence: guard C-08 live 06:58:51Z · DECISIONS.jsonl D-12 part 4

---

### `C-11` — CURRENT depends only on CURRENT (or source)

**Severity BLOCKING · reads `3` · bucket REPAIRABLE-IN-M0**

criterion 4's rule; see that entry. Named by Phase 0.8b; blocked on the G1 rung-bound reconciliation, not on evidence.

**Owner:** ADHIKĀRIN (G1)

Rows: `bo_laksana→ga_vichara`, `ka_kshetra→ka_dasha_kala`, `ka_taranga→ka_sangam`

Evidence: guard C-11 live 06:58:51Z

---

### `C-15` — service ⇒ health_probe AND provides_apis NOT NULL

**Severity BLOCKING · reads `6` · bucket UNEXAMINED**

All six DRAFT service rows (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva) carry NULL for both. Worth noting because it corrects the contract's own §6 cell: that cell says '6 (all 6 service rows)', but there are EIGHT service rows live since the M0-T21 kind repair, and the two new ones (bg_ephemeris_engine, bg_panchanga) DO carry both fields — so the count is unchanged for a different reason than the contract states. Neither health_probe nor provides_apis is named by any Phase 0 step. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** ADHIKĀRIN (the named-field test); then R3/R5 Conform

Rows: `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`, `mi_abhilekha`, `mi_seva`

Evidence: guard C-15 live 06:58:51Z · live 06:56:30Z: 8 service rows, 6 failing C-15 · ASSET_CATALOGUE_CONTRACT_v1_0.md §6 C-15 cell

---

### `C-17` — graded service_health ⇒ health_probe NOT NULL

**Severity BLOCKING · reads `4` · bucket UNEXAMINED**

SPLIT, AND THE SPLIT IS THE POINT. THREE of the four rows are covered by a ruling: D-13 part 2 recorded 'three service assets read service_health=healthy with no health_probe … a status with no detector — H4/§N.8', declined to repair it, and routed it to a rung's stage-1 intake as pre-measured input. Those three are ka_dasha_kala, ka_muhurta_seva, ka_tulana. THE FOURTH — ka_graha_sancara, service_health='unhealthy', no probe — is covered by NO ruling: D-13 counted three because the contract's §6 cell counted three, while the contract's own §8 SQL matches ('healthy','degraded','unhealthy') and returns four. A rule is not classified until every row under it is, so C-17 is UNEXAMINED on one row. TWO CORRECTIONS THIS REGISTER OWES THE LEDGER: (i) D-13 part 2 says 'It is R0 substrate and R0 IS NOT OPEN'. All three assets are ka_* / layer=kala, and their live `rung` column — backfilled by migration 590 from layer, per contract §5.2 — reads R3, not R0. The deferral stands (a rung owns it, not M0); the rung it names is wrong. (ii) the same slip would misroute the intake, so it is worth fixing in a ruling rather than in prose.

**Owner:** ADHIKĀRIN (to correct the rung and cover the fourth row); then R3 stage-1 intake

Rows: `ka_dasha_kala (D-13 part 2)`, `ka_muhurta_seva (D-13 part 2)`, `ka_tulana (D-13 part 2)`, `ka_graha_sancara (NO RULING — unhealthy, no probe)`

Evidence: guard C-17 live 06:58:51Z: 4 rows · live 06:56:30Z: same 4 rows with rung=R3 · DECISIONS.jsonl D-13 part 2 · ASSET_CATALOGUE_CONTRACT_v1_0.md §6 C-17 cell vs its own §8 SQL · M0_EXIT_SCORECARD_v1_0.md §2b disagreement register (records the 3-vs-4 discrepancy)

---

### `C-20` — CURRENT data/artifact ⇒ target_floor NOT NULL

**Severity BLOCKING · reads `3` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

Three R0 rows: bg_class_priors, bg_formula_constants, bg_ghatana. target_floor is the one column whose ownership the campaign HAS already ruled, twice. D-19 part 1: a floor is the MEASURED ACHIEVED COUNT (I7), 'a declarative source file structurally CANNOT hold a measured value', and measured values belong to the campaign, written at §8.6 stage 2 Conform — per rung. D-27 part 2a re-affirms it with a number behind it. So the floors are R0's to set when R0 opens, not M0's.

**Durability:** THE DEFERRAL HAS A PRECONDITION NOBODY HAS DISCHARGED. target_floor is in the seed's `ON CONFLICT DO UPDATE SET`, and D-19 part 2 REQUIRED it to be removed or MR-06-guarded before any campaign-set floor can survive. That change has not been made (verified in the seed text at 06:57:16Z), and a re-seed would move 27 target_floor cells today, 10 of them between two non-NULL values. A floor written at R0 Conform into an unguarded column is a floor with an expiry date nobody is told about.

**Owner:** R0, stage 2 Conform  
**Closes when:** R0 opens, the three assets are measured, and G2 sets each floor to the measured achieved count — AFTER the durability precondition below is met.

Rows: `bg_class_priors`, `bg_formula_constants`, `bg_ghatana`

Evidence: guard C-20 live 06:58:51Z · DECISIONS.jsonl D-19 parts 1-2, D-27 part 2a · SEED_DURABILITY_REGISTER_v1_0.md §1.2 and §3.6(b) · CLAUDE.md §N.4 / invariant I7

---

### `C-21` — target_floor = 0 ⇒ volume_explanation NOT NULL

**Severity BLOCKING · reads `19` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

Nineteen rows across four rungs (R0 ×2, R1 ×2, R2 ×2, R3 ×12, R5 ×1). A volume_explanation on a zero floor is precisely a G4 by-design classification, and D-19 part 1 names it in the campaign-owned set — 'volume_explanation WHERE IT RECORDS A G4 BY-DESIGN CLASSIFICATION' — written at the owning rung's Conform. G4 also requires a WRITTEN by-design justification per asset, which is a per-asset judgment on that asset's data: exactly what I14 keeps out of Track M. Same durability precondition as C-20: volume_explanation is seed-owned and would move on 47 cells at the next re-seed.

**Owner:** each row's own rung, stage 2 Conform

Rows: `bg_class_lifetime_counts`, `bg_sarvatobhadra_grid`, `bo_cgm_motifs`, `bo_pratijna`, `ga_ayurdaya`, `ga_sensitive_degree`, `ka_avadhi`, `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_sweep`, `ka_gochara_v3_century_materialize`, `ka_kota_chakra`, `ka_kshetra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`, `ka_vedha_gochara`, `lel_events`

Evidence: guard C-21 live 06:58:51Z: 19 rows · DECISIONS.jsonl D-19 part 1, D-27 part 2a · CHARTER.md §1 G4 · SEED_DURABILITY_REGISTER_v1_0.md §1.2

---

### `C-22` — rung-frozen data/artifact ⇒ integrity_check_sql NOT NULL

**Severity RUNG · reads `not_checkable (vacuous — 0 rungs frozen)` · bucket DEFERRED-WITH-REASON** · reason kind `structural-fact`

VACUOUS TODAY AND HONESTLY REPORTED AS SUCH RATHER THAN AS A PASS. The rule's antecedent is 'rung-frozen', and no rung has frozen — R0 has not opened. Measured separately and worth stating plainly: 0 of 128 live assets carry an integrity_check_sql at all (06:55:57Z). The column is not seed-written, so checks authored at Conform are durable; authoring them is each rung's stage-2 work per the plan's per-asset 'Add integrity_check_sql' lines.

**Owner:** each rung, stage 2 Conform  
**Closes when:** a rung freezes, at which point the rule stops being vacuous for that rung's assets. It is a RUNG-severity rule, not a BLOCKING one, so it is not an M0 exit condition.

Evidence: guard C-22 live 06:58:51Z: not_checkable · live 06:55:57Z: integrity_check_sql NOT NULL on 0 of 128 rows

---

### `C-25` — co-written target_table ⇒ every co-writer declares its partition

**Severity BLOCKING · reads `not_checkable` · bucket DEFERRED-WITH-REASON** · reason kind `contract-mandate`

THE MODEL ENTRY — a deferral whose reason is written into the specification itself. ASSET_CATALOGUE_CONTRACT §4.9/§10.3: no schema column exists for a natural-key partition declaration, and §6 states 'Rules C-25, C-26 and C-27 must never be reported as passing… a CI guard implementing this document emits them as not_checkable with the reason, and a dashboard that renders that as a pass is itself a defect.' The shipped guard hard-wires exactly that (check_asset_catalogue_contract.py:1105, `_no_detector`) and its own cross-check FAILS if the guard and the contract ever disagree about which rules are not_checkable. This is what a well-formed deferral looks like: a named structural fact, a specification that records it, a detector that refuses to report green, and a guard test that would catch the two drifting apart.

**Owner:** ADHIKĀRIN (§10.3 is an explicitly unsettled fork)  
**Closes when:** a partition-declaration column exists and every co-writer fills it. NOTE THE ASYMMETRY WITH CRITERION 5: this RULE's deferral is well-formed; the WORK it stands in for is named as M0 content by Phase 0.4 and is UNEXAMINED. The rule being honestly null does not make the work deferred.

Evidence: ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9, §6, §8, §10.3 · check_asset_catalogue_contract.py:1069-1109 and the §cross_check spec comparison · guard C-25 live 06:58:51Z: not_checkable

---

### `C-26` — generation-bearing asset declares its authority pointer

**Severity BLOCKING · reads `not_checkable` · bucket DEFERRED-WITH-REASON** · reason kind `contract-mandate`

Same shape as C-25: no schema column for an authority pointer / protected_generations (§4.11, §10.3); the contract forbids reporting it as passing; the guard hard-wires not_checkable with that reason. Unlike C-25 there is NO Phase 0 step that names an authority pointer as M0 content, so both the rule and the work are deferred.

**Owner:** ADHIKĀRIN (§10.3 fork)  
**Closes when:** the §10.3 fork is settled and a column exists.

Evidence: ASSET_CATALOGUE_CONTRACT_v1_0.md §4.11, §10.3 · guard C-26 live 06:58:51Z

---

### `C-27` — writer_timeout_seconds set from telemetry where p95 ≥ 0.5× the value

**Severity ADVISORY · reads `not_checkable` · bucket DEFERRED-WITH-REASON** · reason kind `contract-mandate`

ADVISORY by the contract's own severity column, and not checkable until Track M2 produces cleaned telemetry (§4.8) — the p95 the rule compares against does not exist yet. Recorded, explicitly not green.

**Owner:** M2 (telemetry)  
**Closes when:** M2 produces the cleaned telemetry the rule reads.

Evidence: ASSET_CATALOGUE_CONTRACT_v1_0.md §4.8, §6 · guard C-27 live 06:58:51Z

---

### `C-28` — estimated_seconds NOT NULL where a successful build exists

**Severity BLOCKING · reads `105` · bucket REPAIRABLE-IN-M0**

REPAIRABLE — BUT NOT TO ZERO, AND THIS REGISTER MEASURED THE FLOOR RATHER THAN ASSUMING ONE. Phase 0.9 names the backfill as M0 content and D-6 GRANTED it conditionally; M0-T3 produced the proposal and executed NOTHING (`writes_executed: NONE`). Its statement T-5 backfills estimated_seconds from the median of completed build_run_assets rows, affecting 93 rows. THE RESIDUAL: 31 assets are `lit` in asset_throughput and have NO completed build_run_assets row at all, so no measured duration exists for them — and D-6 condition 4 forbids inventing one ('an asset with no clean telemetry gets NULL, not a plausible number', H6). Measured read-only at 07:06Z: C-28 = 105 now, 31 after the authorised repair, ALL 31 in R0. So the criterion's rule reaches 31, not 0, by any authorised route, and the residual 31 is DEFERRED to whenever those assets next build.

**What blocks it:** M0-T3's proposal §10 records a genuine open condition: D-6 condition 5 says 'scoped to asset_throughput', while D-6's own subject names medians and estimated_seconds, which live in build_run_assets and asset_registry. The proposal flags the contradiction and states T-3/T-4/T-5 should not execute until ADHIKĀRIN confirms condition 5 is scoped to the repair's CONTENT rather than the single table named. D-12 part 5 corrects condition 5 in exactly that direction ('may touch asset_throughput, build_run_assets telemetry aggregates, and asset_registry.estimated_seconds') — so the correction appears already made and the proposal predates it. Someone should confirm that reading rather than assume it; it is one sentence of ADHIKĀRIN's time.

**Owner:** ADHIKĀRIN (confirm D-12 part 5 discharges the flag), then a KĀRAKA executes T-1…T-5  
**Closes when:** T-5 runs (93 rows) and the residual 31 is recorded as deferred with this measurement attached.

Rows: `31 residual assets, all R0 — bg_class_lifetime_counts, bg_cohort, bg_compendium_index, bg_concordance, bg_dasha_systems, bg_dignity_reference, bg_doshas, bg_ephemeris, bg_gochara_arcs, bg_kota_chakra_rings, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra, bg_nakshatra_medical, bg_ontology, bg_parihara_rules, bg_phaladeepika_latta, bg_prashna_rules, bg_reference, bg_remedies, bg_rules, bg_sarvatobhadra_grid, bg_sign_medical, bg_sky_calendar, bg_text_index, bg_texts, bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_vedha_malefic_scale, bg_yogas`

Evidence: guard C-28 live 06:58:51Z: 105 violations (the scorecard's reading 2 says 112 at 06:20Z — two detectors, both stated, neither averaged) · read-only SQL 07:06Z: c28_now=105, c28_residual_after_T5=31 · TELEMETRY_REPAIR_PROPOSAL_v1_0.md §T-5 and §10 condition 5 · DECISIONS.jsonl D-6 conditions 1 and 4, D-12 part 5

---

### `X-02` — no asset_throughput rows on inactive/RETIRED assets

**Severity RESIDUAL · reads `1` · bucket RESERVED** · reason kind `charter-prohibition`

criterion 6's rule. Charter P1 asset; deferred to R3 by plan §14.2 and D-12 part 4. It is the ONLY rule in the guard that already carries both an itemised disclosure and RESIDUAL severity, and its disclosure deliberately does not turn it green — the model the other deferrals need and do not have.

**Owner:** R3 / the native

Rows: `ka_gochara_sweep`

Evidence: guard X-02 live 06:58:51Z (fail, disclosed:true, does_not_turn_the_rule_green:true) · asset_catalogue_disclosed_residuals.json

---

### `X-03` — no active asset with neither build coverage nor a dead flag

**Severity BLOCKING · reads `2` · bucket UNEXAMINED**

criterion 8's rule; see that entry. Both rows have plausible owners (R0 and R5); what is unexamined is the criterion itself — there is no dead-flag column, the guard uses has_writer as a proxy, and Phase 0.8a asks M0 to produce a flag with nowhere to live.

**Owner:** ADHIKĀRIN (G9)

Rows: `bg_gochara_citation_resolution`, `lel_events`

Evidence: guard X-03 live 06:58:51Z

---

### `X-05` — no unresolved zero-consumer finding

**Severity BLOCKING · reads `23` · bucket REPAIRABLE-IN-M0**

criterion 9's rule; see that entry. 23 packets, 0 dispositions recorded, machinery built and waiting on G1 rulings.

**Owner:** ADHIKĀRIN (G1 ×23)

Rows: `23 packets — listed under criterion 9`

Evidence: guard X-05 live 06:58:51Z

---

## 4 — Rules reading `pass`, for completeness

`C-05` `C-09` `C-10` `C-12` `C-13` `C-14` `C-16` `C-18` `C-19` `C-23` `C-24` `X-01` `X-04` (contract guard, 06:58:51Z) and `P-01`…`P-06` (parity guard, 07:02:39Z).

Two cautions the §0 tally deliberately does not fold in. **A pass is one detector returning zero at one instant against one database** — the scorecard's §3a proved each passing rule falsifiable under a deliberate mutation, which is the right standard, but falsifiable is not permanent. And `X-01`'s pass means *'no multi-producer table that nobody declared'*, never *'the partitions are correct'* — its own docstring and the declared-co-writers file both say so, and C-25 is the rule that would say the stronger thing if it had a column.

## 5 — At zero, and not the same thing as being at zero

D-24 part 3 asks for criteria *at zero*. A zero that the next routine `asset_registry_seed.ts` run silently reverts is worse than a red, because nothing announces its expiry (SEED_DURABILITY_REGISTER §0). Every zero below was re-checked against the seed projection at `06:57:16Z` rather than inherited.

| rule | status | durability | violations after a re-seed |
|---|---|---|--:|
| `C-05` | pass (0) | NON-DURABLE — REVERTED BY A RE-SEED | 2 |
| `C-14` | pass (0) | NON-DURABLE — REVERTED BY A RE-SEED ON EIGHT ROWS | 8 |
| `C-18 / criterion 11` | pass (0) | EXPOSED — the COLUMN is durable, the PAIR is not | 1 |
| `C-02 / C-03` | fail (1 each, lel_events) | DURABLE BY AGREEMENT — measured, not assumed | 0 |
| `C-23 / has_substeps` | pass (0) | DURABLE for today's rows; UNENFORCED for future rows | 0 |

**`C-05` — NON-DURABLE — REVERTED BY A RE-SEED**

C-05 reads zero only because bg_ephemeris_engine and bg_panchanga are now asset_kind='service' (the M0-T21 kind repair), which takes them out of the rule's scope. Neither seed entry declares asset_kind, and asset_registry_seed.ts:3268 supplies `asset.asset_kind ?? 'data'` — SO THE DEFAULT IS AN ACTIVE WRITE OF 'data', NOT A NO-OP. The next seed run puts both rows back inside C-05's scope with count_sql still NULL, and the rule fails again with 2. Re-measured independently here at 06:57:16Z: both cells still diverge live-vs-seed.

**`C-14` — NON-DURABLE — REVERTED BY A RE-SEED ON EIGHT ROWS**

The M0-T21 repair wrote 'service' into asset_kind on 2 rows and asset_type on 6. Both columns are in the seed's unconditional `DO UPDATE SET`, and NOT ONE of the eight seed entries declares the key — so all eight are re-written to the `?? 'data'` default. Re-measured at 06:57:16Z: 8 divergent cells, exactly the eight rows the repair touched (bg_ephemeris_engine, bg_panchanga on asset_kind; ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva on asset_type).

**`C-18 / criterion 11` — EXPOSED — the COLUMN is durable, the PAIR is not**

See criterion 11. domain and rung are absent from both seed column lists, so migration 590's backfill cannot be reverted; but `scope` is seed-owned and domain was DERIVED from scope, so a re-seed moves one half of the pair on mi_jivanaghatana and leaves the other. C-18 keeps counting it as present while the value it presents becomes wrong.

**`C-02 / C-03` — DURABLE BY AGREEMENT — measured, not assumed**

Both columns ARE seed-owned, so the M0-T26 repair was durable only if it wrote exactly what the seed writes. Compared across all 127 seed entries at 06:57:16Z: zero divergent cells on either column except lel_events, where live is NULL and the seed would write 'L5' / 'Mīmāṃsā'. So the repair agrees with the seed everywhere it touched — and the one place they disagree is the deliberate NULL D-28 part 1 protects.

**`C-23 / has_substeps` — DURABLE for today's rows; UNENFORCED for future rows**

has_substeps is in neither seed column list, so the M0-T20 repair of 12 rows cannot be reverted by a re-seed (SEED_DURABILITY_REGISTER §3.1). The caveat is coverage, not durability: an asset the seed NEWLY INSERTS lands with has_substeps NULL, and NULL is falsy at asset_runner.py's `if has_substeps:` — so a new heavy writer silently arrives with the substep-plan-completeness detector switched off, which is §N.8 instance 4 all over again. Nothing enforces this. Live rows with has_substeps IS TRUE at 06:55:57Z: 26.

**The through-line:** the campaign's durable repairs are durable because their columns are absent from the seed's column lists (`has_substeps`, `domain`, `rung`, `integrity_check_sql`), and its fragile ones are fragile because they are not (`asset_kind`, `asset_type`, `scope`, `target_floor`, `volume_explanation`). That is structural, not incidental: **before the switch flips, ADHIKĀRIN should decide whether a green resting on a seed-owned column may count as 'at zero' at all.** This register's view — offered as a recommendation, not a ruling — is that it may not, and that D-19 part 2's required seed change is therefore a precondition of the flip rather than a follow-on from it.

## 6 — What would have to be true to flip the switch

In order. Steps 1–9 are rulings only ADHIKĀRIN can make; step 10 is mechanical and is the one that actually stops the flip; steps 11–13 are execution and verification.

| # | kind | what | unblocks |
|---|---|---|---|
| 1 | RULING | **Record the self-reference carve-out for criterion 10** | crit-10 |
| 2 | RULING | **Rule the NAMED-FIELD TEST** | C-04 (7 rows), C-06, C-07, C-15, C-17 (1 row), crit-1 (partly) |
| 3 | RULING | **Rule what criterion 1 means** | crit-1 |
| 4 | RULING | **Rule Phase 0.4 — the partition declaration** | crit-5, crit-2 (partly) |
| 5 | RULING | **Rule Phase 0.8a — the dead flag** | crit-8, X-03 |
| 6 | RULING | **Rule criterion 2's wording** | crit-2 |
| 7 | RULING | **Reconcile G1's rung bound with Phase 0.8b / 0.8c** | crit-4, crit-9, C-11, X-05 |
| 8 | RULING | **Rule H2's reach — is a PR merge to main a 'write to main'?** | crit-10, crit-12 |
| 9 | RULING | **Correct D-13 part 2's rung, and cover its fourth row** | C-17 |
| 10 | MECHANISM | **Give every DEFERRED item a disclosure the guard can actually read** | crit-10 in practice |
| 11 | EXECUTION | **Execute the repairs that are already authorised** | C-28, crit-4, crit-9, C-20 durability |
| 12 | EXECUTION | **Merge, flip, and make it RUN once** | crit-10, crit-12 |
| 13 | VERIFICATION | **Re-measure, then let PARĪKṢAKA certify** | M0 freeze (M0-T10) |

**1. [RULING] Record the self-reference carve-out for criterion 10**

D-24 part 3 conditions the flip on every criterion being at zero or explicitly deferred. Criterion 10 IS the flip. Unless ADHIKĀRIN records that criterion 10 is excluded from its own precondition — satisfied BY the flip, not before it — the precondition is unsatisfiable and the switch can never legitimately move.

**2. [RULING] Rule the NAMED-FIELD TEST**

Does M0 repair registry columns that none of Phase 0's fifteen steps names (target_table, count_sql, health_probe, provides_apis, service_health), or does each go to its owning rung's stage-2 Conform? D-24 says registry metadata is Track-M work; D-25 part 2b says an UNNAMED field has 'no named M0 mandate' and pinned it to the rung. ONE RULING RECLASSIFIES SIX RULES AND TWO CRITERIA. Either answer is workable; the absence of an answer is what blocks the flip.

**3. [RULING] Rule what criterion 1 means**

Is the three-way diff the scorecard's reading (every registry row needs a production @register — 5 violations) or the shipped guard's (P-01…P-06 — 0 violations, with services and source rows legitimately writerless)? The guard is what a blocking flip gates on, so this decides whether criterion 1 is already satisfied or has four exemptions and one G1 disposition still to make.

**4. [RULING] Rule Phase 0.4 — the partition declaration**

Phase 0.4 names 'declare co-writer partitions' as M0 content, but no schema column exists to declare them in. Authorise a column under D-4's reasoning, or defer the work to the owning rungs with the reason recorded. C-25 itself stays not_checkable either way — that part is already well-formed; what is undecided is the WORK.

**5. [RULING] Rule Phase 0.8a — the dead flag**

Define a registered-but-dead flag, rule the guard's has_writer proxy sufficient, or defer the criterion. Today the scorecard calls criterion 8 NOT-MEASURABLE and the guard returns 2 violations from a proxy the contract never designated.

**6. [RULING] Rule criterion 2's wording**

'contract violations per kind = 0' cannot be satisfied while C-25/C-26/C-27 have no detector and must never read green. Re-word it to 'every CHECKABLE rule at zero, the un-checkable ones reported not_checkable with their reason', or make them checkable.

**7. [RULING] Reconcile G1's rung bound with Phase 0.8b / 0.8c**

G1's charter bound reads 'only assets in the current rung' and no rung is open, while Phase 0.8b and 0.8c assign 3 promotions and 23 zero-consumer dispositions to M0. One ruling clears both criteria; without it, the two largest REPAIRABLE items cannot be executed by anyone.

**8. [RULING] Rule H2's reach — is a PR merge to main a 'write to main'?**

Criterion 10's 'merged' half requires the guards to reach origin/main (verified absent at 07:03Z). Charter H3 forbids weakening a gate; charter H2 forbids 'any write to main'. Whether a reviewed PR merge is inside H2 has never been asked. It is not a KĀRAKA's question. Until it is answered criterion 10 cannot be satisfied by any route.

**9. [RULING] Correct D-13 part 2's rung, and cover its fourth row**

D-13 part 2 defers three unearned service_health greens to 'R0'; all three are layer=kala and their live rung column reads R3. And a fourth row (ka_graha_sancara, 'unhealthy', no probe) is covered by no ruling because the contract's §6 cell undercounted its own §8 SQL by one.

**10. [MECHANISM] Give every DEFERRED item a disclosure the guard can actually read**

THIS IS THE STEP THAT ACTUALLY STOPS THE FLIP, AND IT IS MECHANICAL. Twelve entries are deferred with reasons — ten of them rules — and NOT ONE of the ten has an entry in asset_catalogue_disclosed_residuals.json. The only rule that has one is X-02, which is RESERVED rather than deferred, and it is also the only rule carrying a severity (RESIDUAL) that does not gate. Eight of the ten deferred rules — C-01, C-02, C-03, C-08, C-20, C-21, C-25, C-26 — are BLOCKING in the guard's rule table with no disclosure attached (C-22 is RUNG and C-27 ADVISORY, so those two do not gate). FLIPPING BLOCKING TODAY REDS THE BRANCH ON THE 15 BLOCKING FAILURES THE GUARD RETURNED LIVE AT 06:58:51Z, several of which can only be made green by touching a P1 asset or by pre-building R5 work — which is precisely the 'weaken a criterion to get moving' pressure D-24 part 3 named. A deferral that lives only in a markdown file is not a deferral the CI gate can honour. NOTE: the disclosure must not turn a rule green — X-02's `does_not_turn_the_rule_green: true` is the pattern, and per D-12 part 4 an unmet criterion is recorded unmet.

**11. [EXECUTION] Execute the repairs that are already authorised**

(a) telemetry T-1…T-5 under D-6 + D-12 part 5 → C-28 from 105 to its measured floor of 31; (b) the 3 C-11 dispositions and the 23 zero-consumer dispositions, once step 7 lands; (c) D-19 part 2 / D-27 part 2a's seed change for target_floor — WITHOUT which C-20's eventual repair expires silently, and whose model (the MR-06 guard) D-28 part 4 warns has never had to choose and must be proven by fixture rather than inherited.

**12. [EXECUTION] Merge, flip, and make it RUN once**

Per step 8's ruling: get the two guards and the workflow onto origin/main, delete the two `continue-on-error: true` lines (ADHIKĀRIN's own act — charter G9, and explicitly not a KĀRAKA's), and confirm at least one real run reports. Zero runs have ever executed; a workflow that has never run is not evidence.

**13. [VERIFICATION] Re-measure, then let PARĪKṢAKA certify**

Re-run m0_exit_scorecard.py (it appends a reading rather than replacing one) and both guards, and hand the result to PARĪKṢAKA. No agent that performed any of the above may sign it (I16 / charter H7), and this register — authored by a KĀRAKA — certifies nothing.

**What this list is not.** It is not a claim that M0 exits when the thirteen are done — M0's freeze is M0-T10's and its certification is PARĪKṢAKA's. It is the answer to one narrower question: what has to become true before D-24 part 3's precondition is honestly satisfied, so the switch can be flipped without weakening anything to get there.

## 7 — Disagreements and corrections found while classifying

Nothing below is averaged. Two angles disagreeing is a finding (the discipline the scorecard's own §2b established).

**C-02 / C-03 violation counts**

- A — M0_EXIT_SCORECARD_v1_0.md reading 2 (06:20:44Z): 21 and 20
- B — this task's live query (06:55:57Z) and the shipped guard (06:58:51Z): 1 and 1
- **Resolution** — NOT A CONFLICT — A CLOCK. M0-T26 landed the Phase 0.5a repair between the two readings (WORK_QUEUE: done_pending_verification 06:51:24Z, commit_recorded 06:52:23Z). Both figures are true of their instant. The scorecard's own §0 note that filesystem- and database-sourced criteria move between runs is exactly this. Anyone reading the scorecard as current on these two rules will overstate the remaining work by 39 rows.

**criterion 12 — does the domain-coherence assertion exist?**

- A — M0_EXIT_SCORECARD_v1_0.md reading 2: 'THE ASSERTION DOES NOT EXIST'
- B — check_asset_catalogue_contract.py implements X-04 ('domain coherence: a shared asset depends only on shared assets', origin 'plan §11') and it returns 0 violations live
- **Resolution** — The scorecard's clause is stale. What remains true is the operative half: the assertion has never RUN in CI. Criterion 12 is therefore not-green for criterion 10's reasons, not for its own.

**criterion 8 — measurable or not?**

- A — scorecard: NOT-MEASURABLE (no dead-flag field is defined)
- B — guard X-03: fail, 2 violations, using has_writer as the proxy
- **Resolution** — Both are honest and they are answering different questions. The scorecard asks whether the criterion AS WRITTEN has a detector (it does not — nothing defines a dead flag); the guard asks whether any active asset has no registered writer (2 do). Recorded as a disagreement rather than reconciled, because reconciling it is ADHIKĀRIN's step 5.

**C-28 violation count**

- A — scorecard reading 2 (06:20Z): 112
- B — shipped guard (06:58:51Z): 105
- **Resolution** — Two independent detectors, 35 minutes apart, over a table nothing repaired in between. Both are reported; neither is averaged. This register's own residual measurement (31 after the authorised repair) was computed from the same definition the guard uses, so it is comparable to 105, not to 112.

**C-17 row count — the contract disagrees with its own SQL**

- A — ASSET_CATALOGUE_CONTRACT §6 cell: 3 (ka_dasha_kala, ka_muhurta_seva, ka_tulana)
- B — the contract's own §8 SQL, and the guard: 4 — it also matches 'unhealthy', catching ka_graha_sancara
- **Resolution** — The §8 SQL is the detector, so 4 is the rule's result. It matters beyond bookkeeping: D-13 part 2's deferral was written for 'three service assets', so the fourth row inherits no ruling. Already noted in the scorecard's §2b; carried here because it changes a classification.

**D-13 part 2 names the wrong rung**

- A — D-13 part 2: 'It is R0 substrate and R0 IS NOT OPEN'
- B — all three assets are ka_* / layer='kala'; their live `rung` column, backfilled by migration 590 per contract §5.2, reads R3
- **Resolution** — The deferral stands — a rung owns it and M0 does not — but the rung named is wrong, and the ruling routes the finding to R0's stage-1 intake where R3 will need it. Reported, not corrected: correcting a ruling is ADHIKĀRIN's (charter §4).

**ASSET_CATALOGUE_CONTRACT §11 says migration 590 is not applied**

- A — contract §11: 'That migration is AUTHORED AND NOT APPLIED. … No DDL or DML from it has been executed against any database.'
- B — _migrations_applied carries 590_nirmana_m0_catalogue_contract_columns.sql at 2026-08-23T05:36:13.833986+00:00, and all four columns are live
- **Resolution** — The contract's §11 is stale, not wrong-at-authoring. Flagged because §11 is the sentence a later reader would use to decide whether the columns exist, and it now says the opposite of the database. Fixing it is a documentation task, not this one's.

**zero-consumer count: plan 13 vs measured 23**

- A — NIRMANA_ELEVATION_PLAN §1 states 13; the plan's own per-asset annotations count 7
- B — ZERO_CONSUMER_EVIDENCE_v1_0.md and the guard: 23 packets
- **Resolution** — The 23 is the measured figure with a per-asset list behind it and is what X-05 reduces. The plan's 13 reconciles with nothing, including the plan. Not averaged, not adopted — recorded, as the scorecard also recorded it.

## 8 — What this register does NOT establish

- **It does not certify M0, and it does not certify itself.** A KĀRAKA authored it; PARĪKṢAKA decides what it means (I16 / charter H7).
- **It does not flip the switch, wire any guard blocking, or edit `.github/`.** That is ADHIKĀRIN's and it is explicitly reserved.
- **A bucket is a classification, not a verdict.** Where this register says DEFERRED it means a reason of the declared kinds is on record — not that the deferral is wise.
- **UNEXAMINED is not an accusation and not a soft FAIL.** Eleven entries are unexamined because the campaign has been moving fast and honestly; the register's only claim is that no one has yet decided them, and D-24 part 3 says the switch may not move until someone does.
- **The classification of `RESERVED` items ends at the label.** Criterion 6 and `X-02` were read, counted and left exactly as they were.
- **Where a ruling covers only some rows of a rule, the rule is filed by its weakest row** (C-17 is UNEXAMINED on one row of four, C-04 on seven of nine). A rule is not classified until every row under it is.
- **The measurements expire.** They are timestamped to the minute for that reason; a sibling task moved 39 rows out from under the scorecard while this register was being written. Re-run the generator rather than trusting this snapshot.

