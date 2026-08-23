---
canonical_id: M0_DEFERRAL_REGISTER
version: 1.2
status: LIVE-CLASSIFICATION
task: M0-T46 (v1.0 authored by M0-T31; v1.1 by M0-T36 applied D-30; v1.2 applies D-38/D-39/D-40/D-41/D-42)
generated: 2026-08-23T12:25:28.883759+00:00
generator: 00_ARCHITECTURE/control/m0_deferral_register.py
authored_by: KĀRAKA — v1.0 by M0-T31, v1.1 by M0-T36, v1.2 by M0-T46 (Nirmāṇa autonomous campaign)
filename_note: the file keeps its v1_0 path deliberately — canonical_id and every pointer to it are stable; the frontmatter `version` field is the version (§B.8). A v1_0 filename carrying version 1.2 is an in-place update, not registry drift.
certified_by: null   # I16 / charter H7 — a KĀRAKA never certifies its own work
satisfies: DECISIONS.jsonl D-24 part 3 AS AMENDED BY D-30 part 2(a)+part 4, THEN BY D-39 part 1 (withdrawn) AND D-40 part 1 (final): the switch flips when every criterion is at zero or explicitly deferred AND the disclosure mechanism is demonstrably in effect (a two-direction fixture: a disclosed rule still reports its violation and only stops gating; an undisclosed rule still blocks) AND CI detects and refuses a stale baseline (NOT 'CI gates live' — D-40 withdrew that as impossible, no DB credential in CI Actions)
applies: DECISIONS.jsonl D-30 part 1 (named-field test), part 3 (C-28 residual), D-29, D-38 (0.8b REMAIN DRAFT, 0.8c per-packet adjudication), D-39 (X-03/crit-8/crit-5 confirmed M0's, not P5), D-40 (flip condition's CI clause, final form), D-42 (C-28 reframed; build_run_assets ranking)
---

# NIRMĀṆA M0 — Deferral Register v1.2

**The question this document exists to answer**, verbatim from ADHIKĀRIN ruling D-24 part 3:

> *The switch flips when T17's exit scorecard shows each criterion either at zero or explicitly deferred with a recorded reason — **never on a criterion that is merely unexamined**.*

The scorecard measures; it does not separate *non-zero and repairable* from *non-zero and cannot reach zero, for a stated reason*. This register performs that separation and — the actual work product — names what nobody has yet established either way.

**This document decides nothing, flips nothing, and certifies nothing.** No guard file, no `.github/` file and no `asset_registry` row was written by the task that produced it. Classification is evidence for ADHIKĀRIN (charter G7/G9); certification is PARĪKṢAKA's (I16 / charter H7).

## 0 — The tally

| bucket | criteria | contract rules | total | meaning |
|---|--:|--:|--:|---|
| **REPAIRABLE-IN-M0** | 3 | 2 | **5** | a known repair takes it to zero; nobody has done it. The repair and its blocker are named per entry. |
| **DEFERRED-WITH-REASON** | 3 | 16 | **19** | it cannot reach zero inside M0, and a **ruling, plan assignment, contract mandate or measured structural fact** says why. |
| **RESERVED** | 1 | 1 | **2** | it collides with a charter prohibition. Not the campaign's to resolve, and untouched by this task. |
| **UNEXAMINED** | 3 | 0 | **3** | **nobody has established which of the above it is.** D-24 part 3 forbids flipping the switch on any of these. This bucket is the deliverable. |
| **AT-ZERO-WITH-EXPOSURE** | 2 | 1 | **3** | reads zero, with a named exposure that makes that zero conditional (§5). |
| | **12** | **20** | **32** | |

**3 of 32 entries remain UNEXAMINED** after D-30 — down from 11 in v1.0. The named-field test, which v1.0 named as the largest single lever and D-30 part 1 then adopted as a rule, has been applied: it moved five rules to DEFERRED-WITH-REASON and it REACHED three further entries nobody expected it to reach. §9 is the application; §9.2 is the count reconciliation, which does not come out where the ledger says it does.

**The one fact that stops the flip even after every ruling lands** is mechanical, and v1.1 finds it is worse than v1.0 reported. v1.0: of ten DEFERRED rules none carried a disclosure and eight were `BLOCKING`. After D-30 there are **fifteen** DEFERRED rules and **thirteen** carry `BLOCKING` severity — the deferrals grew, the disclosures did not. D-30 part 4 amended the flip condition to require every deferred rule to carry its disclosure entry, and §10 drafts all fifteen. **They are inert** (finding `F-T36-3`): the guard reads `disclosed_additions` in exactly one function, `x02()`, and severity is a hardcoded constant in the rule table — X-02 is non-gating because someone typed `RESIDUAL`, not because it carries a disclosure. And a third prerequisite nobody has recorded (`F-T36-2`): CI does not run `--live` at all. It runs `--baseline` against a snapshot frozen at 05:09:17Z, which returns **17** BLOCKING failures including three rules that pass in production today.

**v1.2 (M0-T46) applies six further ADHIKĀRIN rulings — D-37 through D-42 — three of which move a bucket here.** D-38 decided Phase 0.8b (REMAIN DRAFT — a decision, not a promotion) and adjudicated all 23 Phase 0.8c packets per reading class, moving **crit-4 and C-11 to DEFERRED-WITH-REASON** (deferred to R1/R3, not repairable in M0 by promotion) and **crit-9 and X-05 to AT-ZERO-WITH-EXPOSURE** (all 23 packets adjudicated; unresolved = 0; 6 carry follow-on rung work). D-39 confirmed X-03, criterion 8 and criterion 5 as M0's and settled that their columns are authorised under D-4, not reserved by charter P5, moving **crit-5, crit-8 and X-03 to REPAIRABLE-IN-M0** (a known repair — add the column, backfill, verify — now exists; nobody has executed it). D-42 reframes C-28's residual ('31 assets read `lit` with no completed `build_run_assets` record', not '31 missing an estimate') and ranks `build_run_assets` authoritative wherever a surface asks 'was this asset built' — recorded on the C-28 entry and on criterion 8; **the bucket does not move**, and D-42 explicitly forbids re-pointing C-28's detector at `build_run_assets` to close it (that would be H3). D-40 additionally WITHDRAWS part of D-39's amended flip condition — 'CI must gate against live state' is impossible, CI Actions carries no database credential — and replaces it with a detect-and-refuse-stale-baseline requirement; §10 restates the final condition. D-37 and D-41 are read but change no bucket here (D-37 corrects D-12 part 3 on assets outside this register's scope and clarifies the named-field test's refinement (b); D-41 authorises the deploy.yml edit and a CI-edit-by-direction rule, and no 'awaiting a ruling on CI edit scope' flag was found anywhere in this file, the scorecard, or M0_CLOSE_READINESS_v1_0.md for it to resolve). See §12 for the full application and the before/after tally.

### What counts as a reason

A reason is only a reason if it names one of these. *"Not yet done"*, *"probably fine"* and *"an analogous ruling exists for a different column"* are **UNEXAMINED**, not deferred — that distinction is the whole point of the exercise. v1.0 filed six rules UNEXAMINED that a looser reading would have called deferred; D-30's closing paragraph adopted that asymmetry as standing policy (*"an UNEXAMINED entry costs me a minute; a wrongly-DEFERRED one costs the gate its meaning"*), and v1.1 applies it again in §9.3 — three entries the test REACHES are narrowed and left UNEXAMINED rather than closed, because the test settles whose they are and not what to do about them.

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
| 4 | dangling or DRAFT-targeted edges = 0 | `dangling_C-12=0; CURRENT→DRAFT_C-11=3; at=2026-08-23T06:58:51Z` | **DEFERRED-WITH-REASON** | R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam) — each at its own §8.6 stage-2 Conform |
| 5 | multi-producer partitions = 0 | `C-25=not_checkable — no schema column; X-01_undeclared_collisions_2026-08-23T06:58:51Z=0; co_written_target_ta` | **REPAIRABLE-IN-M0** | ADHIKĀRIN confirmed M0 (D-39); execution (author migration, backfill, verify) is a KĀRAKA task |
| 6 | throughput rows on inactive assets = 0 | `live_2026-08-23T06:55:57Z={'assets': 1, 'rows': 3, 'states': ['error']}` | **RESERVED** | R3 (Kāla rung) for the lifecycle exit; the native for anything P1 reaches |
| 7 | retired assets without a data_disposition = 0 | `live_2026-08-23T06:55:57Z=1; guard_C-08_2026-08-23T06:58:51Z=1; note=moved BLOCKED → FAIL when migration 590 s` | **DEFERRED-WITH-REASON** | R3 (Kāla rung), lifecycle exit |
| 8 | active assets with neither build coverage nor a dead flag = 0 | `scorecard_2026-08-23T06:20Z=NOT-MEASURABLE (no dead-flag field is defined); guard_X-03_2026-08-23T06:58:51Z=2` | **REPAIRABLE-IN-M0** | ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task |
| 9 | unresolved zero-consumer findings = 0 | `packets=23; dispositions_recorded=0; at=2026-08-23T06:58:51Z` | **AT-ZERO-WITH-EXPOSURE** | ADHIKĀRIN (G1 ×23); recording them is a KĀRAKA task |
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

**D-30 PART 1 APPLIED (M0-T36).** v1.0's §6 step 2 listed 'crit-1 (partly)' among the test's beneficiaries, and 'partly' is right but smaller than it sounds. The test disposes of two of the five diverging ids by clause (a) failing on `has_writer`: bg_sarvatobhadra_grid (R0) and, redundantly with D-23, lel_events (R5). It does NOT touch the other three, and it does NOT touch the criterion's actual blocker, WHICH IS NOT A COLUMN QUESTION AT ALL: the scorecard's detector and the shipped parity guard disagree by construction about what the three-way diff MEANS — 5 violations versus 0 — and no ruling says which detector expresses the criterion. A rule about who owns a column cannot answer a question about what a criterion counts. Recorded so that 'the named-field test landed' is not mistaken for 'criterion 1 moved'.

— — — v1.0 (M0-T31) classification, preserved — — —

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

**Bucket: DEFERRED-WITH-REASON** · reason kind: `ruling`

**Reads now**

```json
{
 "dangling_C-12": 0,
 "CURRENT→DRAFT_C-11": 3,
 "at": "2026-08-23T06:58:51Z"
}
```

**D-38 APPLIED (M0-T46).** Phase 0.8b's disposition is now RULED, not merely blocked on a G1 rung-bound reconciliation. D-38 part 1 decided the DRAFT-but-served set's general disposition is REMAIN DRAFT — 'a G1 decision, not a deferral' — and part 2 confirmed bulk promotion in M0 is refused outright: only where a specific rung clause names an asset for promote-or-retire (R2's nine, R3's ka_graha_sancara/ka_muhurta_seva, R4's nine, R5's lel_events) does that rung decide it; otherwise REMAIN DRAFT stands until the owning rung's own §8.6 stage-2 Conform revisits it with real integrity evidence behind it. None of this criterion's three DRAFT dependencies — ga_vichara (R1), ka_dasha_kala (R3), ka_sangam (R3) — is named by any rung-specific promotion clause, so REMAIN DRAFT is their disposition too. THE THREE C-11 EDGES THEREFORE CANNOT BE REPAIRED IN M0 BY PROMOTION: D-38 states plainly that promoting on servedness alone 'would be writing a status from a proxy rather than from its detector's verdict' — precisely H4/§N.8 — and I13 forbids the only other route (asset-lifecycle work on a dependency outside the open rung). Moved from REPAIRABLE-IN-M0 to DEFERRED-WITH-REASON: the reason is D-38 itself, the destination is each dependency's own rung, and Phase 0.8b's own 'promoted or justified' is satisfied by the justified half — REMAIN DRAFT, decided, not silently unexamined.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

THE REPAIR IS NAMED AND NOBODY HAS DONE IT. Plan Phase 0.8b — an M0 step — reads '34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced'. Each of the three edges closes by promoting the DRAFT dependency to CURRENT (charter G1) or by recording why it stays DRAFT. Both are catalogue dispositions on evidence M0 already holds (DRAFT_INVENTORY / CONSUMER_MAP).

**What blocks it:** G1's charter bound reads 'Only assets in the current rung, on M0 census evidence' and NO RUNG IS OPEN. Phase 0.8b assigns the work to M0; G1's bound appears to withhold the power that performs it. That collision must be ruled before any promotion is written — it is the same collision criterion 9 sits behind, so one ruling clears both.

**Owner:** R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam) — each at its own §8.6 stage-2 Conform  
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

**Bucket: REPAIRABLE-IN-M0**

**Reads now**

```json
{
 "C-25": "not_checkable — no schema column",
 "X-01_undeclared_collisions_2026-08-23T06:58:51Z": 0,
 "co_written_target_tables": 5
}
```

**D-39 APPLIED (M0-T46).** Criterion 5's entry additionally flagged a (b)-clause collision the other two did not carry — whether §8.6 stage 2's generic 'partitions declared' overrides Phase 0.4's specific naming. D-39 part 4 confirms criterion 5 M0's OUTRIGHT, alongside X-03 and criterion 8, resolving that collision in M0's favour rather than leaving it open. The column question is settled the same way: authorised under D-4, not reserved by P5. Moved from UNEXAMINED to REPAIRABLE-IN-M0. C-25 itself stays permanently `not_checkable` for the separate structural reason already recorded — no column exists YET — which is exactly the repair this bucket names as not yet done.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

**D-30 PART 1 APPLIED (M0-T36).** **THE TEST REACHES THIS ENTRY TOO, AND IT WAS NOT ON D-30's LIST EITHER** (v1.0 §6 step 4 files it as a separate ruling). Clause (a) is satisfied: Phase 0.4 names 'DECLARE CO-WRITER PARTITIONS' and §14.1's M0 content line names 'semantic de-duplication with declared co-writer partitions'. Clause (b) is where this differs from X-03 and where it is genuinely harder: §8.6 stage 2 lists 'partitions declared' among each rung's Conform work, so the SAME collision documented above for has_substeps applies here — and here it is NOT forced by the verification property, because no prior ruling pins partitions either way. The working reading (§8.6 stage 2 general, Phase 0.4 specific) gives the work to M0; the opposite reading gives it to the rungs. Under either, C-25 stays permanently `not_checkable` for the same structural reason — no schema column — and that part of v1.0's entry was already well-formed. What the test changes is that the undecided question is now narrower: not 'is this M0's or the rungs'' but 'does §8.6 stage 2 override Phase 0.4, and if not, is the column authorised under D-4's reasoning or reserved under P5'.

— — — v1.0 (M0-T31) classification, preserved — — —

THE TEMPTING ANSWER IS 'DEFERRED — NO COLUMN EXISTS', AND IT IS WRONG. The absence of a partition column is a real structural fact and it is what makes C-25 permanently not_checkable (§4). But the CRITERION is not the rule: plan Phase 0.4 — an M0 step — reads '(table × generation × partition) invariant; correct the gochara attribution; DECLARE CO-WRITER PARTITIONS'. M0 is the phase the plan assigns this work to. Under D-4's own reasoning ('a criterion that cannot be met without a change has NAMED that change even where it numbers no migration') a partition-declaration column is arguably already authorised; under D-23's correction it may instead belong to each rung. Nobody has asked, so this is not deferred — it is undecided. What exists today is X-01, which passes and means only 'no multi-producer table that nobody declared' — its own docstring refuses the stronger reading.

**Owner:** ADHIKĀRIN confirmed M0 (D-39); execution (author migration, backfill, verify) is a KĀRAKA task  
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

**Bucket: REPAIRABLE-IN-M0**

**Reads now**

```json
{
 "scorecard_2026-08-23T06:20Z": "NOT-MEASURABLE (no dead-flag field is defined)",
 "guard_X-03_2026-08-23T06:58:51Z": 2
}
```

**D-39 APPLIED (M0-T46).** Criterion 8 is X-03's criterion and inherits D-39's finding exactly: ownership to M0 confirmed, the dead-flag column authorised under D-4 and not reserved by P5. Moved from UNEXAMINED to REPAIRABLE-IN-M0. The scorecard's own disagreement with the guard about whether this criterion is measurable at all is unaffected — no column exists yet, so the scorecard still reads NOT-MEASURABLE until the repair is executed. Separately, D-42 (2026-08-23T11:04:17Z) ranks build_run_assets as authoritative wherever a surface asks 'was this asset built' — bearing on this criterion's BUILD-COVERAGE half, not the dead-flag half D-39 just settled: has_writer and asset_throughput.state='lit' both remain proxies for 'built', and the dead-flag column D-39 authorises does not by itself decide which proxy the criterion's other half should read.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

**D-30 PART 1 APPLIED (M0-T36).** Criterion 8 is X-03's criterion and inherits its finding exactly: Phase 0.8a and the criterion's own text both name the dead flag, so clause (a) is satisfied and the work is M0's — a result D-30 routed to a separate ruling and did not expect the named-field test to produce. What remains undecided is the mechanism (a P5 column, the `has_writer` proxy ruled sufficient, or the criterion deferred), and beneath it the fact the scorecard has recorded from its first reading: the two detectors disagree about whether this criterion is MEASURABLE at all — NOT-MEASURABLE from the scorecard, 2 violations from the guard's proxy.

— — — v1.0 (M0-T31) classification, preserved — — —

THE TWO DETECTORS DISAGREE ABOUT WHETHER THE CRITERION IS MEASURABLE AT ALL. The scorecard says NOT-MEASURABLE: asset_registry has no column designating a registered-but-dead asset, the contract defines none, and has_writer — the only candidate — was itself wrong on 2 rows (D-25). The shipped guard's X-03 reads has_writer as the proxy anyway and returns 2 violations. Meanwhile plan Phase 0.8a — an M0 step — reads 'Registered-but-dead FLAGGED (bg_gochara_citation_resolution)', i.e. M0 is asked to produce a flag that has nowhere to live. Defining the flag, ruling the proxy sufficient, or deferring the whole criterion are three different answers and none has been given.

**Owner:** ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task  
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

**Bucket: AT-ZERO-WITH-EXPOSURE** · reason kind: `ruling`

**Reads now**

```json
{
 "packets": 23,
 "dispositions_recorded": 0,
 "at": "2026-08-23T06:58:51Z"
}
```

**D-38 APPLIED (M0-T46).** Phase 0.8c is now RULED per packet, per reading class, rather than left open pending 23 individual G1 dispositions. D-38 part 3 adjudicates each of the five reading classes ZERO_CONSUMER_EVIDENCE_v1_0.md kept apart: INPUT-ONLY -> no action, closed (the absence of a serving consumer is the design); NO CONSUMER FOUND -> recorded as a retirement candidate, NOT retired, routed to the owning rung; METHOD-BLIND -> no action, and explicitly NOT a retirement candidate (this is UNKNOWN, not zero — retiring on a method-blind absence would be H6); SHADOWED -> a real defect, routed to the owning rung; BY DESIGN EMPTY / CATEGORY MISMATCH -> no action, closed, mismatch recorded. Applied to the 23 measured packets: 8 INPUT-ONLY and 2 BY-DESIGN close with no action; 7 METHOD-BLIND close as genuinely unknown, not as retirement candidates; 1 NO-CONSUMER-FOUND (bg_concordance, R0) is recorded as a retirement candidate and routed to R0; 5 SHADOWED (bg_vidhi_floors, bg_vidhi_primitives — R0; ka_dasha_kala, ka_muhurta_seva, ka_tulana — R3) are recorded as real defects and routed to their rungs. D-38's own words govern the count: 'RESOLVED MEANS ADJUDICATED, NOT MUTATED … a finding adjudicated against its evidence with a recorded determination IS resolved. Reading that criterion to require status changes would force asset-lifecycle work on six closed rungs to satisfy a catalogue step, which I13 forbids.' ALL 23 PACKETS NOW CARRY A RECORDED DETERMINATION, so unresolved = 0 by the ruling's own definition of resolved. THE ZERO IS CONDITIONAL, NOT UNCONDITIONAL: 6 of the 23 (1 retirement candidate, 5 SHADOWED defects) carry follow-on asset-lifecycle work at their owning rung that this ruling explicitly does not perform, and 7 more are closed as UNKNOWN rather than confirmed-absent. Moved from REPAIRABLE-IN-M0 to AT-ZERO-WITH-EXPOSURE — the same shape as criterion 11 — rather than to a plain settled bucket, because the underlying rows are adjudicated, not fixed.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

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
| `C-04` | BLOCKING | data/artifact ⇒ target_table NOT NULL and the table exists | `9` | **DEFERRED-WITH-REASON** | the rung that owns each row — R0 (bg_prashna_rules, bg_sky_calendar), R1 (ga_sade_sati, ga_sensitive, ga_strength, ga_structural), R2 (bo_cdlm_summary, bo_chart_gestalt), R5 (lel_events) — at that rung's §8.6 stage-2 Conform |
| `C-06` | BLOCKING | chart-domain count_sql contains $1 | `1` | **DEFERRED-WITH-REASON** | R5 (Mīmāṃsā rung), §8.6 stage-2 Conform — inherited from C-07, of which this rule is a shadow |
| `C-07` | BLOCKING | service ⇒ target_table / count_sql / target_floor / clear_tables all NULL | `4` | **DEFERRED-WITH-REASON** | R3 (ka_dasha_kala, ka_tulana) and R5 (mi_abhilekha, mi_seva), §8.6 stage-2 Conform |
| `C-08` | BLOCKING | RETIRED ⇒ data_disposition NOT NULL | `1` | **DEFERRED-WITH-REASON** | R3 |
| `C-11` | BLOCKING | CURRENT depends only on CURRENT (or source) | `3` | **DEFERRED-WITH-REASON** | R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam) |
| `C-15` | BLOCKING | service ⇒ health_probe AND provides_apis NOT NULL | `6` | **DEFERRED-WITH-REASON** | R3 (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) and R5 (mi_abhilekha, mi_seva) — §8.6 stage-2 Conform for provides_apis; the probe itself is tier-S rung work (§9) |
| `C-17` | BLOCKING | graded service_health ⇒ health_probe NOT NULL | `4` | **DEFERRED-WITH-REASON** | R3 (Kāla rung) stage-1 intake — all four rows, per D-13 part 2 AS CORRECTED BY D-29 |
| `C-20` | BLOCKING | CURRENT data/artifact ⇒ target_floor NOT NULL | `3` | **DEFERRED-WITH-REASON** | R0, stage 2 Conform |
| `C-21` | BLOCKING | target_floor = 0 ⇒ volume_explanation NOT NULL | `19` | **DEFERRED-WITH-REASON** | each row's own rung, stage 2 Conform |
| `C-22` | RUNG | rung-frozen data/artifact ⇒ integrity_check_sql NOT NULL | `not_checkable (vacuous — 0 rungs frozen)` | **DEFERRED-WITH-REASON** | each rung, stage 2 Conform |
| `C-25` | BLOCKING | co-written target_table ⇒ every co-writer declares its partition | `not_checkable` | **DEFERRED-WITH-REASON** | ADHIKĀRIN (§10.3 is an explicitly unsettled fork) |
| `C-26` | BLOCKING | generation-bearing asset declares its authority pointer | `not_checkable` | **DEFERRED-WITH-REASON** | ADHIKĀRIN (§10.3 fork) |
| `C-27` | ADVISORY | writer_timeout_seconds set from telemetry where p95 ≥ 0.5× the value | `not_checkable` | **DEFERRED-WITH-REASON** | M2 (telemetry) |
| `C-28` | BLOCKING | estimated_seconds NOT NULL where a successful build exists | `105` | **REPAIRABLE-IN-M0** | ADHIKĀRIN (confirm D-12 part 5 discharges the flag), then a KĀRAKA executes T-1…T-5 |
| `X-02` | RESIDUAL | no asset_throughput rows on inactive/RETIRED assets | `1` | **RESERVED** | R3 / the native |
| `X-03` | BLOCKING | no active asset with neither build coverage nor a dead flag | `2` | **REPAIRABLE-IN-M0** | ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task |
| `X-05` | BLOCKING | no unresolved zero-consumer finding | `23` | **AT-ZERO-WITH-EXPOSURE** | ADHIKĀRIN (G1 ×23) |

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

**Severity BLOCKING · reads `9` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-30 PART 1 APPLIED (M0-T36).** `target_table` is named by NO Phase-0 step and by NO M0 acceptance criterion. Phase 0.2 — the only step that names registry columns at all — names `integrity_check_sql` and `target_floor`, and not this one. Clause (a) therefore FAILS and the column belongs to the rung that owns the asset; repairing it in M0 would be the I13 breach D-30 names. Clause (b) independently confirms the same destination for two of the nine rows: plan §15's per-asset entries for bo_cdlm_summary and bo_chart_gestalt each carry the bullet 'Declare `target_table` (or `clear_tables` if it writes several)', and both assets are R2. The two rows that already had a reason keep it (lel_events → R5 by D-23; bg_sky_calendar → R0 by D-28 part 4, whose `bg_sky_events` relation is genuinely absent from production and is a trigger-bearing R0 intake defect). The seven that had none now have one: not 'probably fine', but 'no clause of the plan gives this column to M0'. NOTE, because it is the honest residual: this settles WHOSE the column is, not WHETHER a NULL target_table on the four chart_facts co-writers is deliberate. That question travels to R1 with the rows.

— — — v1.0 (M0-T31) classification, preserved — — —

NINE ROWS, THREE DIFFERENT SITUATIONS, AND ONLY TWO OF THEM HAVE A REASON ON RECORD. (i) lel_events — DEFERRED to R5 with the rest of its cluster (D-23). (ii) bg_sky_calendar — DEFERRED: its target_table names `bg_sky_events`, a relation ABSENT from production; D-28 part 4 ruled it 'L0 → R0 → not open → UNTOUCHED (I13)' and recorded it as a TRIGGER-BEARING defect for R0 intake (a re-seed's to_regclass pre-flight would switch the asset off). (iii) THE OTHER SEVEN have target_table NULL and no ruling of any kind: bg_prashna_rules (R0), bo_cdlm_summary and bo_chart_gestalt (R2), ga_sade_sati, ga_sensitive, ga_strength, ga_structural (R1). Four of those seven are chart_facts co-writers, where a NULL target_table might be deliberate rather than missing — nobody has established which, and 'probably fine' is not a reason. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** the rung that owns each row — R0 (bg_prashna_rules, bg_sky_calendar), R1 (ga_sade_sati, ga_sensitive, ga_strength, ga_structural), R2 (bo_cdlm_summary, bo_chart_gestalt), R5 (lel_events) — at that rung's §8.6 stage-2 Conform

Rows: `bg_prashna_rules`, `bg_sky_calendar`, `bo_cdlm_summary`, `bo_chart_gestalt`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `lel_events`

Evidence: guard C-04 live 06:58:51Z: 8 × target_table_null + 1 × target_table_missing · DECISIONS.jsonl D-28 part 4, D-23 · DECISIONS.jsonl D-24, D-25 part 2b

---

### `C-06` — chart-domain count_sql contains $1

**Severity BLOCKING · reads `1` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-30 PART 1 APPLIED (M0-T36).** `count_sql` is named by no Phase-0 step and no M0 acceptance criterion; clause (a) FAILS. The single row is mi_seva (R5), and C-06 closes when C-07 does because mi_seva's count_sql should not exist at all on a service row. Same destination by two independent routes.

— — — v1.0 (M0-T31) classification, preserved — — —

The single row is mi_seva, whose count_sql should not exist at all: mi_seva is asset_kind='service', and C-07 says a service carries no count_sql. So C-06 is a shadow of C-07 and closes with it. It inherits C-07's bucket for the same reason. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** R5 (Mīmāṃsā rung), §8.6 stage-2 Conform — inherited from C-07, of which this rule is a shadow

Rows: `mi_seva`

Evidence: guard C-06 live 06:58:51Z (1 row, domain=chart, domain_provenance=column) · guard C-07 live 06:58:51Z (mi_seva carries count_sql, target_floor, target_table)

---

### `C-07` — service ⇒ target_table / count_sql / target_floor / clear_tables all NULL

**Severity BLOCKING · reads `4` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-30 PART 1 APPLIED (M0-T36).** THIS IS THE ONE RULE WHERE CLAUSE (a) IS PARTLY SATISFIED, AND IT IS WORTH SAYING SO RATHER THAN REPORTING A CLEAN DEFERRAL. Of the four columns C-07 asserts NULL on a service row, three (`target_table`, `count_sql`, `clear_tables`) are named nowhere in Phase 0 — clause (a) fails flatly. The fourth, `target_floor`, IS named — by Phase 0.2. But 0.2 names it as a REQUIRED FIELD OF THE CONTRACT SPECIFICATION being authored, not as a population M0 performs; the clause that assigns the work of setting and correcting floors is §8.6 stage 2 ('floors set to achieved (I7)'), per rung, which is refinement (b) firing. That is not a novel reading: D-19 part 1 already held that 'a declarative source file structurally CANNOT hold a measured value' and placed floors at §8.6 stage 2 Conform, and D-27 part 2a re-affirmed it with a measurement. So all four columns reach the same destination, three by (a) and one by (b). All four assets are R3/R5. Three of the four columns are additionally SEED-OWNED, so a DB-only NULLing in M0 would be reverted by the next re-seed — a durability fact that makes the deferral not merely correct but load-bearing.

— — — v1.0 (M0-T31) classification, preserved — — —

Four service rows carry data-asset fields: ka_dasha_kala and ka_tulana (target_floor), mi_abhilekha and mi_seva (count_sql + target_floor + target_table). The repair is mechanical — NULL four fields — and that is exactly why it must not be done on a KĀRAKA's own reading: none of those columns is named by any Phase 0 step, all four assets are R3/R5, and three of the four columns are SEED-OWNED, so a DB-only NULLing is reverted by the next re-seed anyway. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** R3 (ka_dasha_kala, ka_tulana) and R5 (mi_abhilekha, mi_seva), §8.6 stage-2 Conform

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

**Severity BLOCKING · reads `3` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-38 APPLIED (M0-T46).** Criterion 4's rule; see that entry. D-38 part 1 rules the general DRAFT-but-served disposition REMAIN DRAFT, and none of ga_vichara, ka_dasha_kala or ka_sangam is named by a rung-specific promotion clause, so all three stay DRAFT and these three edges cannot be closed by promotion in M0. Moved to DEFERRED-WITH-REASON.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

criterion 4's rule; see that entry. Named by Phase 0.8b; blocked on the G1 rung-bound reconciliation, not on evidence.

**Owner:** R1 (ga_vichara) and R3 (ka_dasha_kala, ka_sangam)

Rows: `bo_laksana→ga_vichara`, `ka_kshetra→ka_dasha_kala`, `ka_taranga→ka_sangam`

Evidence: guard C-11 live 06:58:51Z

---

### `C-15` — service ⇒ health_probe AND provides_apis NOT NULL

**Severity BLOCKING · reads `6` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-30 PART 1 APPLIED (M0-T36).** Neither `health_probe` nor `provides_apis` is named by any Phase-0 step or M0 acceptance criterion; clause (a) FAILS for both and the columns belong to the rungs. Note the shape of what is being deferred: `provides_apis` is a declaration, but `health_probe` is a DETECTOR, and §8.4's R3 row already assigns 'a real known-answer probe with an SLO' to R3 by name for two of these six assets — so refinement (b) fires there too. Writing a probe in M0 to clear C-15 would be manufacturing a detector to satisfy a criterion, which is the H3 shape D-29 part 5 named for the sibling rule C-17. The v1.0 entry's correction of the contract's §6 cell stands unchanged: there are EIGHT service rows live since the M0-T21 kind repair, not six, and the two new ones (bg_ephemeris_engine, bg_panchanga) DO carry both fields.

— — — v1.0 (M0-T31) classification, preserved — — —

All six DRAFT service rows (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva) carry NULL for both. Worth noting because it corrects the contract's own §6 cell: that cell says '6 (all 6 service rows)', but there are EIGHT service rows live since the M0-T21 kind repair, and the two new ones (bg_ephemeris_engine, bg_panchanga) DO carry both fields — so the count is unchanged for a different reason than the contract states. Neither health_probe nor provides_apis is named by any Phase 0 step. THE NAMED-FIELD TEST — the one question that decides six of these rules at once. D-24 established that repairing registry METADATA in M0 trespasses no rung (it is I14 Track-M work, and no rung is open to be trespassed). D-25 part 2b then drew the line: has_writer 'is NOT among the derived fields M0's Phase 0.6a names … so unlike D-24 I have no named M0 mandate to write them', and the row repair was pinned to R0 stage 2 Conform. Read together, the operative test is: A REGISTRY COLUMN IS M0'S TO REPAIR IF AND ONLY IF ONE OF PHASE 0'S FIFTEEN STEPS NAMES IT. Phase 0 names layer_index/layer_name (0.5a), has_substeps (0.6a), asset_kind/asset_type (0.6b), the lifecycle columns (0.3), partitions (0.4), the consumer map (0.7), estimated_seconds (0.9). IT NAMES NONE OF: target_table, count_sql, health_probe, provides_apis, service_health. Applying that test to those columns is an inference from precedent, not a ruling anyone has made — so this register REFUSES to record it as a deferral and files the affected rules UNEXAMINED. One ADHIKĀRIN ruling on the test itself reclassifies all six.

**Owner:** R3 (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) and R5 (mi_abhilekha, mi_seva) — §8.6 stage-2 Conform for provides_apis; the probe itself is tier-S rung work (§9)

Rows: `ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`, `mi_abhilekha`, `mi_seva`

Evidence: guard C-15 live 06:58:51Z · live 06:56:30Z: 8 service rows, 6 failing C-15 · ASSET_CATALOGUE_CONTRACT_v1_0.md §6 C-15 cell

---

### `C-17` — graded service_health ⇒ health_probe NOT NULL

**Severity BLOCKING · reads `4` · bucket DEFERRED-WITH-REASON** · reason kind `ruling`

**D-30 PART 1 APPLIED (M0-T36).** TWO RULINGS CLOSE THIS ENTRY AND THE SECOND ONE ANSWERED THE EXACT DEFECT v1.0 FILED IT FOR. v1.0 filed C-17 UNEXAMINED on ONE ROW: three of the four were covered by D-13 part 2, the fourth (ka_graha_sancara, service_health='unhealthy', no probe) by nothing, because the contract's §6 cell undercounted its own §8 SQL by one. D-29 has since (i) corrected D-13 part 2's destination from 'R0 substrate' to R3 — the rung the live `rung` column actually carries for every ka_* row — and (ii) extended it from three rows to four, characterising the fourth as A RED WITH NO DETECTOR BEHIND IT rather than a false green: §N.8 in its other direction, failing safe, and explicitly NOT to be 'fixed' by clearing it to healthy or NULL when R3 opens. So every row now carries a ruling. Independently, the named-field test reaches the same place: `health_probe` and `service_health` are named by no Phase-0 step and no M0 criterion, so clause (a) fails and the columns are the owning rung's. Two routes, one destination, and the register's own §6 step 9 ('correct D-13 part 2's rung, and cover its fourth row') is discharged.

— — — v1.0 (M0-T31) classification, preserved — — —

SPLIT, AND THE SPLIT IS THE POINT. THREE of the four rows are covered by a ruling: D-13 part 2 recorded 'three service assets read service_health=healthy with no health_probe … a status with no detector — H4/§N.8', declined to repair it, and routed it to a rung's stage-1 intake as pre-measured input. Those three are ka_dasha_kala, ka_muhurta_seva, ka_tulana. THE FOURTH — ka_graha_sancara, service_health='unhealthy', no probe — is covered by NO ruling: D-13 counted three because the contract's §6 cell counted three, while the contract's own §8 SQL matches ('healthy','degraded','unhealthy') and returns four. A rule is not classified until every row under it is, so C-17 is UNEXAMINED on one row. TWO CORRECTIONS THIS REGISTER OWES THE LEDGER: (i) D-13 part 2 says 'It is R0 substrate and R0 IS NOT OPEN'. All three assets are ka_* / layer=kala, and their live `rung` column — backfilled by migration 590 from layer, per contract §5.2 — reads R3, not R0. The deferral stands (a rung owns it, not M0); the rung it names is wrong. (ii) the same slip would misroute the intake, so it is worth fixing in a ruling rather than in prose.

**Owner:** R3 (Kāla rung) stage-1 intake — all four rows, per D-13 part 2 AS CORRECTED BY D-29

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

**D-42 APPLIED (M0-T46).** ADHIKĀRIN ruling D-42 reclassifies this residual's FRAMING and forbids both available 'fixes'. THE OLD FRAME WAS WRONG: this is not '31 assets missing an estimated_seconds'. D-42's authoritative framing: '31 ASSETS READ lit WITH NO COMPLETED RUN RECORD BEHIND THEM' — the missing estimate is a symptom, the unearned `lit` is the finding (D-13's telemetry pollution meeting §N.8's no-op-completion class). RANKING ESTABLISHED FOR THE WHOLE REGISTER, NOT JUST THIS RULE: 'build_run_assets IS AUTHORITATIVE. asset_throughput.state="lit" IS A CLAIM ABOUT A BUILD, NOT EVIDENCE OF ONE' — applying wherever a surface asks 'was this asset built', including criterion 8's build-coverage half (see that entry). TWO FIXES ARE EXPLICITLY FORBIDDEN, NOT MERELY DISCOURAGED: backfilling estimates for the 31 (H6 — a number on a build nothing witnessed), and RE-POINTING c28()'s detector at build_run_assets to close it — 'under the authoritative definition C-28 would report zero violations and a BLOCKING failure would pass — while all 31 unearned lit states remain exactly as they are. That is a weakening under D-41 part 2 and presumptively H3.' NEITHER FIX IS THIS TASK'S TO MAKE AND NEITHER WAS MADE — no detector in m0_exit_scorecard.py or check_asset_catalogue_contract.py was re-pointed by M0-T46; a future re-pointing found inconsistent with this ruling is a finding for a separate task, not a repair for this one. THE BUCKET DOES NOT MOVE — the deferral for the 31 stands (D-30 part 3), now grounded on the definitional finding rather than the absence of estimates — and the 31 unearned lit states are additionally understood as ROUTED TO THEIR OWNING RUNGS (all R0), since D-42 holds 'each rung's own build is the only thing that can earn or refute a lit'.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

**D-30 PART 3 APPLIED (M0-T36).** ADHIKĀRIN granted the residual deferral under G7 and D-31 part 2 indexes it as one of the three G7 deferrals on the record. M0-T36 re-measured the split read-only at 2026-08-23T08:0xZ rather than inherit it, and it reproduces exactly: of the 105 data/artifact rows the shipped guard reports, **74 are backfillable** from the median of their completed `build_run_assets` rows (D-6's authorised statement T-5) and **31 have no completed build_run_assets row at all**, so no measured duration exists and D-6 condition 4 forbids inventing one (H6). All 31 are R0. THE BUCKET DOES NOT MOVE, and that is deliberate: the rule is genuinely repairable-in-M0 for 74 rows and genuinely deferred for 31, and collapsing it to one bucket would lose whichever half was collapsed. What the flip needs from this rule is therefore TWO things, not one — T-5 executed (nothing has executed; M0-T3 produced the proposal with `writes_executed: NONE`), and the 31-row residual disclosed. Until T-5 runs, C-28 reads 105, not 31, and any statement that 'C-28 is deferred' is premature by 74 rows.

— — — v1.0 (M0-T31) classification, preserved — — —

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

**Severity BLOCKING · reads `2` · bucket REPAIRABLE-IN-M0**

**D-39 APPLIED (M0-T46).** M0-T36's own re-derivation of the named-field test (independent of D-30's assertion) reached X-03 and found clause (a) satisfied — Phase 0.8a names the dead flag AND the asset — but left it UNEXAMINED because 'the register's definition of REPAIRABLE-IN-M0 requires a KNOWN repair; none is known', the open question being whether a new column is authorised under D-4's reasoning or reserved under charter P5. D-39 part 4 CONFIRMS ownership to M0 independently and SETTLES the P5 question: the column is 'inside the plan's naming and NOT reserved by P5 … subject to D-4's standing conditions (additive only, mechanical backfill only, NULL where not derivable, verify applied, never edit after, PARĪKṢAKA verifies)'. With ownership confirmed and the column authorised rather than reserved, a KNOWN repair now exists — even though nothing has executed it. Moved from UNEXAMINED to REPAIRABLE-IN-M0. What remains undone: authoring the migration, running the backfill, and PARĪKṢAKA's verification — none of which this task performs.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

**D-30 PART 1 APPLIED (M0-T36).** **THE TEST REACHES THIS ENTRY AND D-30 DID NOT ANTICIPATE THAT IT WOULD.** D-30 listed X-03 and criterion 8 under a SEPARATE ruling (v1.0 §6 step 5, 'Rule Phase 0.8a — the dead flag'), not among the named-field test's reclassifications. But clause (a) is satisfied here twice over and more explicitly than in any of the five verification cases: Phase 0.8a reads 'Registered-but-dead FLAGGED (`bg_gochara_citation_resolution`)' — naming the work AND the asset — and M0 acceptance criterion 8 names 'active assets with neither build coverage nor a dead flag'. Clause (b) does not fire: no rung clause claims a dead flag. So the rule's output is unambiguous — THE DEAD FLAG IS M0's, NOT A RUNG's, and deferring it to R0/R5 would be the error in the opposite direction. WHAT THE TEST DOES NOT DECIDE, and why this entry does not move to a settled bucket: there is no column for the flag to live in. Creating one is charter P5 (a schema change outside the migrations this plan names) unless D-4's reasoning extends — 'a criterion that cannot be met without a change has NAMED that change even where it numbers no migration'. Ruling the guard's self-designated `has_writer` proxy sufficient is the other available answer, and D-25 already found that column wrong on 2 rows. The register's definition of REPAIRABLE-IN-M0 requires 'a KNOWN repair'; none is known. So the entry stays UNEXAMINED — but the question left is narrower and different in kind: not 'whose is it' (answered: M0's) but 'what is the flag'.

— — — v1.0 (M0-T31) classification, preserved — — —

criterion 8's rule; see that entry. Both rows have plausible owners (R0 and R5); what is unexamined is the criterion itself — there is no dead-flag column, the guard uses has_writer as a proxy, and Phase 0.8a asks M0 to produce a flag with nowhere to live.

**Owner:** ADHIKĀRIN confirmed M0 (D-39); execution is a KĀRAKA task

Rows: `bg_gochara_citation_resolution`, `lel_events`

Evidence: guard X-03 live 06:58:51Z

---

### `X-05` — no unresolved zero-consumer finding

**Severity BLOCKING · reads `23` · bucket AT-ZERO-WITH-EXPOSURE** · reason kind `ruling`

**D-38 APPLIED (M0-T46).** Criterion 9's rule; see that entry. D-38 part 3 adjudicates all 23 packets by reading class; unresolved = 0. Moved to AT-ZERO-WITH-EXPOSURE: 6 packets (1 retirement candidate, 5 SHADOWED defects) are routed to their owning rungs rather than closed outright, and 7 METHOD-BLIND packets are closed as unknown, not as confirmed-zero.

— — — v1.1 (M0-T36, D-30 applied) classification, preserved — — —

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

| # | kind | what | unblocks | resolved? |
|---|---|---|---|---|
| 1 | RULING | **Record the self-reference carve-out for criterion 10** | crit-10 | open |
| 2 | RULING | **Rule the NAMED-FIELD TEST** | C-04 (7 rows), C-06, C-07, C-15, C-17 (1 row), crit-1 (partly) | open |
| 3 | RULING | **Rule what criterion 1 means** | crit-1 | open |
| 4 | RULING | **Rule Phase 0.4 — the partition declaration** | crit-5, crit-2 (partly) | YES — see below |
| 5 | RULING | **Rule Phase 0.8a — the dead flag** | crit-8, X-03 | YES — see below |
| 6 | RULING | **Rule criterion 2's wording** | crit-2 | open |
| 7 | RULING | **Reconcile G1's rung bound with Phase 0.8b / 0.8c** | crit-4, crit-9, C-11, X-05 | YES — see below |
| 8 | RULING | **Rule H2's reach — is a PR merge to main a 'write to main'?** | crit-10, crit-12 | open |
| 9 | RULING | **Correct D-13 part 2's rung, and cover its fourth row** | C-17 | open |
| 10 | MECHANISM | **Give every DEFERRED item a disclosure the guard can actually read** | crit-10 in practice | open |
| 11 | EXECUTION | **Execute the repairs that are already authorised** | C-28, crit-4, crit-9, C-20 durability | open |
| 12 | EXECUTION | **Merge, flip, and make it RUN once** | crit-10, crit-12 | open |
| 13 | VERIFICATION | **Re-measure, then let PARĪKṢAKA certify** | M0 freeze (M0-T10) | open |

**1. [RULING] Record the self-reference carve-out for criterion 10**

D-24 part 3 conditions the flip on every criterion being at zero or explicitly deferred. Criterion 10 IS the flip. Unless ADHIKĀRIN records that criterion 10 is excluded from its own precondition — satisfied BY the flip, not before it — the precondition is unsatisfiable and the switch can never legitimately move.

**2. [RULING] Rule the NAMED-FIELD TEST**

Does M0 repair registry columns that none of Phase 0's fifteen steps names (target_table, count_sql, health_probe, provides_apis, service_health), or does each go to its owning rung's stage-2 Conform? D-24 says registry metadata is Track-M work; D-25 part 2b says an UNNAMED field has 'no named M0 mandate' and pinned it to the rung. ONE RULING RECLASSIFIES SIX RULES AND TWO CRITERIA. Either answer is workable; the absence of an answer is what blocks the flip.

**3. [RULING] Rule what criterion 1 means**

Is the three-way diff the scorecard's reading (every registry row needs a production @register — 5 violations) or the shipped guard's (P-01…P-06 — 0 violations, with services and source rows legitimately writerless)? The guard is what a blocking flip gates on, so this decides whether criterion 1 is already satisfied or has four exemptions and one G1 disposition still to make.

**4. [RULING] Rule Phase 0.4 — the partition declaration**

Phase 0.4 names 'declare co-writer partitions' as M0 content, but no schema column exists to declare them in. Authorise a column under D-4's reasoning, or defer the work to the owning rungs with the reason recorded. C-25 itself stays not_checkable either way — that part is already well-formed; what is undecided is the WORK.

**RESOLVED (M0-T46 records; ruled by ADHIKĀRIN):** D-39 (2026-08-23T09:25:50Z) — CONFIRMED M0's; the column is authorised under D-4's reasoning, NOT reserved by P5. crit-5 moved UNEXAMINED → REPAIRABLE-IN-M0. The remaining work is execution (author the migration, backfill, verify), not a further ruling.

**5. [RULING] Rule Phase 0.8a — the dead flag**

Define a registered-but-dead flag, rule the guard's has_writer proxy sufficient, or defer the criterion. Today the scorecard calls criterion 8 NOT-MEASURABLE and the guard returns 2 violations from a proxy the contract never designated.

**RESOLVED (M0-T46 records; ruled by ADHIKĀRIN):** D-39 (2026-08-23T09:25:50Z) — CONFIRMED M0's for both crit-8 and X-03; the dead-flag column is authorised under D-4's reasoning, NOT reserved by P5. Both moved UNEXAMINED → REPAIRABLE-IN-M0. The remaining work is execution — no column has been created yet.

**6. [RULING] Rule criterion 2's wording**

'contract violations per kind = 0' cannot be satisfied while C-25/C-26/C-27 have no detector and must never read green. Re-word it to 'every CHECKABLE rule at zero, the un-checkable ones reported not_checkable with their reason', or make them checkable.

**7. [RULING] Reconcile G1's rung bound with Phase 0.8b / 0.8c**

G1's charter bound reads 'only assets in the current rung' and no rung is open, while Phase 0.8b and 0.8c assign 3 promotions and 23 zero-consumer dispositions to M0. One ruling clears both criteria; without it, the two largest REPAIRABLE items cannot be executed by anyone.

**RESOLVED (M0-T46 records; ruled by ADHIKĀRIN):** D-38 (2026-08-23T09:24:48Z) — 0.8b's disposition is REMAIN DRAFT (a decision, not a promotion): none of ga_vichara/ka_dasha_kala/ka_sangam is named by a rung-specific promotion clause, so crit-4/C-11 move to DEFERRED-WITH-REASON (R1/R3), not repaired in M0. 0.8c's 23 packets are adjudicated per reading class (INPUT-ONLY/BY-DESIGN closed, METHOD-BLIND closed-as-unknown, NO-CONSUMER-FOUND/SHADOWED routed to rung); crit-9/X-05 move to AT-ZERO-WITH-EXPOSURE, unresolved = 0.

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

---

## 9 — D-30 part 1 applied: the named-field test

v1.0 named this test as the single largest lever and REFUSED to apply it, on the grounds that inferring a rule from precedent is not the same as being given one. ADHIKĀRIN ruling **D-30 part 1** then adopted it as a rule and instructed it be applied. This section is that application. It is arithmetic on a ruling, not a ruling.

> A REGISTRY COLUMN IS M0's TO REPAIR IF AND ONLY IF **(a)** a Phase-0 step OR M0's own acceptance criteria NAME IT — acceptance criteria count, per D-4 — AND **(b)** no more-specific plan clause assigns it to a later rung, in which case the specific governs the general. Absent (a), the column belongs to the rung that owns the asset, and repairing it in M0 is the I13 breach.

*(D-30's own wording governs; the above is the operative sentence quoted, not a paraphrase to be relied on in its place.)*

### 9.0 — The left-hand side, transcribed

The whole rule turns on whether a column appears in these fifteen steps, so they are transcribed from `NIRMANA_ELEVATION_PLAN_v3_0.md` §Phase 0 — carried to M0 verbatim by v4.0 §14.4 (*"Phase 0 — all 15 steps | M0"*) — rather than summarised.

| step | what it names |
|---|---|
| `0.1  Six-source census` | asset_registry · @register() · asset_registry_seed.ts · migrations · asset_throughput · CAPABILITY_MANIFEST.json |
| `0.2  Author the contract` | §3 as an enforceable per-kind specification — including `integrity_check_sql` and `target_floor` AS REQUIRED FIELDS |
| `0.3  Lifecycle + tombstone` | §3.2; `superseded_by`, `data_disposition`; no DELETEs (I6) |
| `0.4  Semantic de-duplication` | (table × generation × partition) invariant; correct the gochara attribution; DECLARE CO-WRITER PARTITIONS |
| `0.5a Layer position` | 14 null + 6 malformed `layer_index` → `Lx`; `layer_name` derived |
| `0.5b SOURCE classification` | `lel_events` → `SOURCE` |
| `0.6a has_substeps` | 14 false negatives — derive from the writer class |
| `0.6b Kind reconciliation` | `asset_kind` authoritative; 6 disagreements resolved |
| `0.7  Consumer map` | Asset → serving-surface index as a required field |
| `0.8a Build coverage audit` | Registered-but-dead FLAGGED (`bg_gochara_citation_resolution`) |
| `0.8b catalog_status drift` | 34 DRAFT-but-served promoted or justified; CURRENT-may-not-depend-on-DRAFT enforced |
| `0.8c Zero-consumer review` | 13 assets: record the consumer or retire with a disposition |
| `0.9  Telemetry repair` | close orphaned rows; recompute medians; backfill `estimated_seconds`; schedule the refresh |
| `0.10 CI enforcement` | three-way guard + contract conformance + prefix + edge + DRAFT-dependency invariants, merged and BLOCKING |
| `0.11 Freeze the baseline` | tag the reconciled catalogue; later phases measure drift against it |

**M0's own acceptance criteria (v4.0 §14.1):** v3.0 Phase 0's ten exit criteria verbatim, PLUS 'every asset carrying `domain` and `rung`', PLUS 'the CI domain-coherence assertion (§11) green'. The domain/rung clause is the only place either column is named anywhere in Phase 0 or M0 — which is exactly why D-4 could authorise migration 590 and why D-30 had to add this half to the rule.

### 9.1 — The rule verified against the case law it was derived from

D-30 states it verified this itself. M0-T36 re-derived it independently from the plan text rather than accept the claim — a rule that failed to reproduce its own precedents would be a worse instrument than no rule.

| case | ruling | held | clause (a) | clause (b) | rule output | reproduces? |
|---|---|---|---|---|---|:--:|
| **has_substeps** | D-24 | `M0` | SATISFIED — Phase 0.6a names `has_substeps` by column name, and §14.1's M0 content line names '`has_substeps` repair' again. | DOES NOT FIRE — §8.6 stage 2 (Conform) lists 'has_substeps corrected' among each rung's registry-metadata work, but that is the GENERAL per-rung stage description; 0.6a + §14.1 are the SPECIFIC clauses and the specific governs. See the §8.6 collision note below — this is the one place the rule's two halves pull against each other, and the tiebreak is forced: read the other way, the rule would not reproduce D-24 and D-30's own verification claim would be false. | `M0` | ✅ |
| **has_writer (row repair)** | D-25 part 2(b) | `R0` | FAILS — no Phase-0 step names `has_writer`; M0's acceptance criteria do not name it. Criterion 8 names 'build coverage' and 'a dead flag', not this column; the guard's X-03 uses `has_writer` only as a PROXY it designated itself. | not reached (a already fails) | `the rung that owns the asset = R0` | ✅ |
| **domain / rung** | D-4 | `M0` | SATISFIED via the acceptance-criteria half ONLY — no Phase-0 step names either column; §14.1's 'every asset carrying `domain` and `rung`' does. This case is why refinement (a) cannot be 'a Phase-0 step' alone. | DOES NOT FIRE — no rung clause claims either column; migration 590 derived both centrally. | `M0` | ✅ |
| **layer_index / layer_name** | D-24 / executed at M0-T26, certified V-10 | `M0` | SATISFIED — Phase 0.5a names both columns explicitly. | DOES NOT FIRE — the §15 per-asset bullets that mention layer position cite '(Phase 0.5a)' by name, i.e. they point AT the M0 step rather than claiming the work for a rung. | `M0` | ✅ |
| **SOURCE reclassification (lel_events)** | D-23 | `R5` | SATISFIED — Phase 0.5b names it, and names the asset: '`lel_events` → `SOURCE`'. | FIRES — §8.4's R5 row names the same asset for the same work ('`lel_events` reclassified `SOURCE`'). The specific governs the general. | `R5` | ✅ |

**Verdict.** 5 of 5 REPRODUCED, re-derived independently by M0-T36 from the plan text rather than inherited from D-30's assertion. Two structural observations that the verification produced and that a bare PASS would have hidden. FIRST: refinement (b) is load-bearing in exactly one of the five cases (lel_events). Refinement (a)'s acceptance-criteria half is load-bearing in exactly one other (domain/rung). Neither refinement is decoration; drop either and the rule contradicts a ruling ADHIKĀRIN has already made. SECOND, and this one is a finding rather than a confirmation — see §9.1.1: plan §8.6 stage 2 assigns SIX kinds of registry metadata to every rung's Conform stage BY NAME, one of which is `has_substeps`, and closes with 'Stage 2 is deliberately inside the rung rather than in Track M'. Read as a (b)-firing clause it would send has_substeps to the rungs and D-24 would not be reproduced — so it must be read as the general and Phase 0.6a as the specific. That reading is forced by the rule's own verification property, not chosen for convenience, but it is nowhere written down and the next agent to read §8.6 will not know it.

#### 9.1.1 — The §8.6 stage-2 collision

> Conform — complete the §3 registration for this layer's assets only: floors set to achieved (I7), `integrity_check_sql` authored per asset, timeouts derived, `has_substeps` corrected, partitions declared, consumers recorded. Registry metadata only — no writer runs. … Stage 2 is deliberately inside the rung rather than in Track M.
> — *NIRMANA_ELEVATION_PLAN_v4_0.md §8.6 stage 2 + its closing paragraph*

That one paragraph names **six** kinds of registry metadata as each rung's Conform work: `target_floor`, `integrity_check_sql`, `writer_timeout_seconds`, `has_substeps`, `partition declaration`, `consumer map`.

| field | collision, and how it resolves |
|---|---|
| `has_substeps` | Phase 0.6a + §14.1 M0 content line. RESOLVED IN FAVOUR OF M0 — forced, because the opposite reading breaks D-24, which D-30 asserts the rule reproduces. CONSEQUENCE IF READ THE OTHER WAY: the has_substeps repair executed at M0-T26 and certified by PARĪKṢAKA at V-9 would retroactively be an I13 breach on 12 rows spanning five rungs. It is not — but the reading that makes it one is available to any agent who reads §8.6 and not this note. |
| `partition declaration` | Phase 0.4 + §14.1 M0 content line ('semantic de-duplication with declared co-writer partitions'). SAME SHAPE, NOT YET RULED — see crit-5 below, which the named-field test reaches and D-30 did not anticipate it reaching. |
| `consumer map` | Phase 0.7. Not currently a failing rule, so nothing turns on it today; recorded so it is not rediscovered. |
| `target_floor / integrity_check_sql / writer_timeout_seconds` | NO COLLISION. Phase 0.2 names `integrity_check_sql` and `target_floor` only as REQUIRED FIELDS OF THE CONTRACT SPECIFICATION — the authoring of §3, which M0 did. It does not assign the POPULATION of either. §8.6 stage 2 is therefore the only clause assigning that work, and it assigns it per rung. This is independently confirmed by D-19 part 1 and D-27 part 2a for floors, and it is why C-20/C-21/C-22/C-27 were already correctly DEFERRED in v1.0 — the named-field test does not move them, it explains them. |

**Disposition.** RECORDED, NOT RESOLVED. Reading §8.6 stage 2 as general rather than specific is forced for has_substeps and is the working assumption for partitions and the consumer map. Whether ADHIKĀRIN wants that written into the case law is ADHIKĀRIN's; M0-T36 states it as the reading the rule requires and does not rule it.

### 9.2 — What moved, and the count that does not reconcile

| entry | before (M0-T31) | after (D-30 applied) |
|---|---|---|
| `C-04` | UNEXAMINED | **DEFERRED-WITH-REASON** |
| `C-06` | UNEXAMINED | **DEFERRED-WITH-REASON** |
| `C-07` | UNEXAMINED | **DEFERRED-WITH-REASON** |
| `C-15` | UNEXAMINED | **DEFERRED-WITH-REASON** |
| `C-17` | UNEXAMINED | **DEFERRED-WITH-REASON** |

| bucket | rules before | rules after | criteria before | criteria after |
|---|--:|--:|--:|--:|
| REPAIRABLE-IN-M0 | 3 | 3 | 3 | 3 |
| DEFERRED-WITH-REASON | 10 | 15 | 2 | 2 |
| RESERVED | 1 | 1 | 1 | 1 |
| UNEXAMINED | 6 | 1 | 5 | 5 |
| AT-ZERO-WITH-EXPOSURE | 0 | 0 | 1 | 1 |

**The count reconciliation — a finding, not a quibble.** D-30's question field says the test 'moves 6 rules + 2 criteria', a figure it inherited verbatim from SUTRADHĀRA's escalation, which inherited it from v1.0 §0 of this file. THAT FIGURE IS NOT ITEMISABLE AND M0-T36 COULD NOT REPRODUCE IT. v1.0's own §6 step 2 lists six 'unblocks' entries — C-04, C-06, C-07, C-15, C-17, crit-1 — which is FIVE RULES AND ONE CRITERION, not six and two; and the shared NAMED_FIELD_TEST reason text is attached to only FOUR rules (C-04, C-06, C-07, C-15) while asserting in its own last sentence that 'one ADHIKĀRIN ruling on the test itself reclassifies all six'. So v1.0 disagrees with itself in two places and the disagreement propagated into the ledger unchallenged. THE MEASURED ANSWER: applied strictly, the test moves FIVE rules to DEFERRED-WITH-REASON; it additionally REACHES three entries D-30 did not list (X-03, crit-8, crit-5) and narrows them without moving them; and it partly disposes crit-1. This is not a quibble about arithmetic — the three unanticipated entries are the finding, and they were invisible while the count was believed.

### 9.3 — What the test REACHED that nobody expected it to

D-30 routed each of these to a *separate* ruling in v1.0's §6 checklist. Applied honestly the named-field test lands on them anyway, and settles their **ownership** while leaving their **mechanism** open. Per D-30's own adopted asymmetry they are narrowed, not closed — they stay `UNEXAMINED`.

| entry | v1.0 routed it to | what the test decides |
|---|---|---|
| `X-03` | §6 step 5 — a separate 'dead flag' ruling | OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED. Stays UNEXAMINED. |
| `crit-8` | §6 step 5 — a separate 'dead flag' ruling | OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED. Stays UNEXAMINED. |
| `crit-5` | §6 step 4 — a separate 'Phase 0.4 partition' ruling | OWNERSHIP SETTLED TO M0 BY CLAUSE (a) — MECHANISM STILL UNDECIDED, AND (b) COLLIDES. Stays UNEXAMINED. |
| `crit-1` | §6 step 2 — listed as 'crit-1 (partly)' | PARTLY DISPOSED — 2 of 5 rows settled by the test; the criterion's own blocker is untouched. Stays UNEXAMINED. |
| `C-28` | §6 step 11 — execution, not a ruling | RESIDUAL DEFERRAL GRANTED BY D-30 PART 3 (G7) — bucket unchanged, residual now recorded. |

## 10 — The disclosure entries, drafted

**D-30 part 4** amends D-24 part 3: the switch flips when every criterion is at zero or deferred **and every deferred rule carries its disclosure entry**, itemised and dated, in the discipline D-10 part 3 granted for the migration-number allowlist.

M0-T36 drafts all of them. They are written into a **new, inert** top-level block `deferred_rule_disclosures` in `platform/scripts/governance/asset_catalogue_disclosed_residuals.json` — deliberately NOT merged into `disclosed_additions`, which `x02()` reads and validates. **Nothing is wired blocking, no severity is changed, no `.github/` file was touched, and no rule is turned green:** every entry carries `does_not_turn_the_rule_green: true`, per D-12 part 4's *never silently green*.

**They are also inert, and that is finding `F-T36-3`** — see §11. Writing them satisfies D-30 part 4's letter and changes nothing the guard does, because the guard has no code path that reads a disclosure for any rule but `X-02`.

**v1.2 (M0-T46) — THE FLIP CONDITION HAS BEEN AMENDED TWICE SINCE THE ABOVE WAS WRITTEN, AND THE FINAL FORM IS DIFFERENT FROM D-30 part 4's.** D-39 part 1 first amended D-30 part 4: an existing disclosure entry is not evidence the mechanism does anything — the switch flips only when the disclosure mechanism is 'DEMONSTRABLY IN EFFECT, PROVEN BY A FIXTURE THAT SHOWS BOTH DIRECTIONS — a disclosed rule's violation is still REPORTED while no longer GATING, and an UNDISCLOSED rule still BLOCKS'; D-39 also added 'CI MUST GATE AGAINST LIVE STATE, NOT A SNAPSHOT'. D-40 part 1 WITHDREW that CI clause as an impossibility M0-T40 root-caused: CI Actions carries no database credential, so `--live` is a job that cannot run there at all. D-40 replaces it: **CI need not gate against live state — it must DETECT AND REFUSE A STALE BASELINE**, with rule results still printed in full so only the exit changes. THE FINAL CONDITION, as amended twice, supersedes D-30 part 4 for this document's own §0/frontmatter: every criterion at zero or explicitly deferred, AND the disclosure mechanism demonstrably in effect (the two-direction fixture), AND CI's baseline check detects and refuses staleness. Neither half of the mechanism half is discharged by this task; both remain open per §12.

**A tension this task found and does not resolve.** D-39's characterisation of `F-T36-3` as still-inert rests on SUTRADHĀRA's mailbox escalation timestamped `20260823T082157Z` (from M0-T36's own close-readiness pass). This file's own `_write_disclosure_block()` docstring and README text (below, and unchanged by this task) assert that a LATER task, M0-T40, closed `F-T36-3` by making the guard read `deferred_rule_disclosures` BY RULE ID and compute `effective_severity` from it — and M0-T46 verified, read-only, that `check_asset_catalogue_contract.py` does contain exactly that code path (`effective_severity`, a rule-id-keyed reader). D-39 is timestamped *after* that M0-T40 work would have landed but cites *pre*-M0-T40 evidence for its F-T36-3 finding. This is recorded as an open question for ADHIKĀRIN, not settled here: a KĀRAKA does not adjudicate whether a ruling used stale evidence (I13/I16). See the mailbox finding this task files alongside its report.

| rule | severity | gates today | deferred to | ruling / mandate cited |
|---|---|:--:|---|---|
| `C-01` | BLOCKING | YES | R5 | DECISIONS.jsonl D-23 (ADHIKĀRIN, 2026-08-23T05:04:21Z) — reverses D-21 and assigns the SOURCE reclassification to R5, no |
| `C-02` | BLOCKING | YES | R5 | DECISIONS.jsonl D-28 part 1 (deliberate-NULL category) + D-23; write certified by PARĪKṢAKA V-10 |
| `C-03` | BLOCKING | YES | R5 | DECISIONS.jsonl D-28 part 1 + D-23; write certified by PARĪKṢAKA V-10 |
| `C-04` | BLOCKING | YES | the owning rung's §8.6 stage-2 Conform | DECISIONS.jsonl D-30 part 1 (the named-field test) — applied by M0-T36; plus D-23 (lel_events) and D-28 part 4 (bg_sky_c |
| `C-06` | BLOCKING | YES | R5 | DECISIONS.jsonl D-30 part 1 — applied by M0-T36 |
| `C-07` | BLOCKING | YES | the owning rung's §8.6 stage-2 Conform | DECISIONS.jsonl D-30 part 1 (named-field test) — applied by M0-T36; and D-19 part 1 + D-27 part 2a for the target_floor  |
| `C-08` | BLOCKING | YES | R3 | DECISIONS.jsonl D-12 part 4 (ADHIKĀRIN, 2026-08-23T04:46:23Z), quoting plan §14.2 by name |
| `C-15` | BLOCKING | YES | the owning rung — §8.6 stage-2 Conform for provides_apis; tier-S probe work (§9) for health_probe | DECISIONS.jsonl D-30 part 1 — applied by M0-T36; §8.4's R3 row for the probe half |
| `C-17` | BLOCKING | YES | R3 | DECISIONS.jsonl D-13 part 2 AS CORRECTED AND EXTENDED BY D-29 (ADHIKĀRIN, 2026-08-23T07:44:26Z) |
| `C-20` | BLOCKING | YES | R0 | DECISIONS.jsonl D-19 part 1 and D-27 part 2a |
| `C-21` | BLOCKING | YES | the owning rung's §8.6 stage-2 Conform | DECISIONS.jsonl D-19 part 1 (volume_explanation named in the campaign-owned set) + charter G4 |
| `C-22` | RUNG | no | each rung in turn | structural fact, measured; plan §8.6 stage 2 ('integrity_check_sql authored per asset') and the closing paragraph ('Stag |
| `C-25` | BLOCKING | no | undecided — M0 under Phase 0.4, or each rung under §8.6 stage 2 | ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9 / §6 / §10.3 (contract-mandate: 'Rules C-25, C-26 and C-27 must never be reported  |
| `C-26` | BLOCKING | no | the owning rung | ASSET_CATALOGUE_CONTRACT_v1_0.md §4.11 / §6 / §10.3 (contract-mandate) |
| `C-27` | ADVISORY | no | M2 | ASSET_CATALOGUE_CONTRACT_v1_0.md §6 severity column + plan §4.8 |
| `C-28_residual` | BLOCKING | YES | R0's own build (only a real build can retire it) | DECISIONS.jsonl D-30 part 3 (G7 deferral, ADHIKĀRIN, 2026-08-23T07:46:10Z), indexed as a G7 by D-31 part 2 |

**12 of 16** drafted entries cover a rule that gates the exit code today.

**Deliberately NOT drafted:**

- `C-11` — NEWLY DEFERRED-WITH-REASON BY D-38 (2026-08-23T09:24:48Z), NOT REPAIRABLE-IN-M0 any more — see the C-11 entry above. Phase 0.8b's disposition is REMAIN DRAFT for all three of this rule's DRAFT dependencies, deferred to R1/R3. A disclosure entry for this rule has NOT been drafted by M0-T46: this task is scoped to `00_ARCHITECTURE/control/` and does not write `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`. Drafting one, in the same shape as the other DEFERRED rules above, is follow-up work for a task with that file in scope.
- `X-05` — RESOLVED BY D-38 part 3 (2026-08-23T09:24:48Z), NOT REPAIRABLE-IN-M0 and NOT deferred — see the X-05 entry above. All 23 zero-consumer packets are adjudicated per reading class; unresolved = 0. A disclosure is the wrong instrument for a resolved (not deferred) rule. The guard's `zero_consumer_dispositions` block remains empty per-packet, which is correct: D-38's adjudication is by CLASS, not by writing a `decision_ref` into that per-packet block, and no KĀRAKA may write one there regardless (catalogue disposition is G1).
- `X-02` — ALREADY DISCLOSED, in `disclosed_additions`, and is the pattern every entry above follows. Untouched by M0-T36 or M0-T46.
- `X-03` — REPAIRABLE-IN-M0 (D-39, 2026-08-23T09:25:50Z), NOT deferred any more — see the X-03 entry above. Ownership to M0 is confirmed and the column is authorised under D-4, not reserved by P5; the repair (add the column, backfill, verify) is known but unexecuted. A disclosure would be the wrong instrument: this needs the repair, not a reason it cannot happen.

### disclosure · C-01

```json
{
 "C-01": {
  "rule": "C-01",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R5 (Mīmāṃsā rung), stage 2 Conform",
  "deferred_to": "R5",
  "landed_at": "pre-campaign (the row predates the campaign; prefix has never matched)",
  "disclosed_via": "DECISIONS.jsonl D-23 (ADHIKĀRIN, 2026-08-23T05:04:21Z) — reverses D-21 and assigns the SOURCE reclassification to R5, not M0",
  "reason": "One row: lel_events, prefix 'lel' against layer 'mimamsa'. C-01 EXEMPTS source rows, so the SOURCE reclassification IS the repair — there is nothing separate to fix. D-23 assigned that reclassification to R5 (§8.4's R5 row names the asset: 'lel_events reclassified SOURCE'), reversing D-21 which had briefly placed it in M0. Repairing it in M0 would re-commit the error D-23 corrected.",
  "measured": {
   "violations": 1,
   "rows": [
    "lel_events"
   ],
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-02

```json
{
 "C-02": {
  "rule": "C-02",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R5 (Mīmāṃsā rung), stage 2 Conform",
  "deferred_to": "R5",
  "landed_at": "2026-08-23T06:51-06:54Z (M0-T26 repaired 20 of 21 rows; this one was held back deliberately)",
  "disclosed_via": "DECISIONS.jsonl D-28 part 1 (deliberate-NULL category) + D-23; write certified by PARĪKṢAKA V-10",
  "reason": "One row: lel_events, layer_index NULL. THE NULL IS DELIBERATE AND MUST NOT BE FILLED. D-28 part 1 rules it 'THE ONLY PLACE IN THE REGISTRY WHERE THE OPENNESS OF A RESERVED DECISION IS WRITTEN DOWN': the correct value is NULL-if-source but L5-if-data, and D-23 reserved that choice to R5. Filling it in M0 would answer a reserved question by default. V-10 confirmed the row held NULL through the 39-cell layer repair, which is the deliberate NULL surviving contact with a real write.",
  "measured": {
   "violations": 1,
   "rows": [
    "lel_events"
   ],
   "was": 21,
   "repaired_by": "M0-T26 (V-10)",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-03

```json
{
 "C-03": {
  "rule": "C-03",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R5 (Mīmāṃsā rung), stage 2 Conform",
  "deferred_to": "R5",
  "landed_at": "2026-08-23T06:51-06:54Z (M0-T26 repaired 19 of 20 rows; this one was held back deliberately)",
  "disclosed_via": "DECISIONS.jsonl D-28 part 1 + D-23; write certified by PARĪKṢAKA V-10",
  "reason": "One row: lel_events, layer_name NULL. Identical reason to C-02 and the same reserved decision: the lexicon spelling that belongs here depends on whether the row is SOURCE or L5 data, which is R5's to decide. Every other populated row now carries the §N.1 LOCKED diacritics (Gaṇita, Kāla, Mīmāṃsā), a real §N.1 violation caught PRE-write by a codepoint pin (D-28 part 6).",
  "measured": {
   "violations": 1,
   "rows": [
    "lel_events"
   ],
   "was": 20,
   "repaired_by": "M0-T26 (V-10)",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-04

```json
{
 "C-04": {
  "rule": "C-04",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "per row: R0 (bg_prashna_rules, bg_sky_calendar) · R1 (ga_sade_sati, ga_sensitive, ga_strength, ga_structural) · R2 (bo_cdlm_summary, bo_chart_gestalt) · R5 (lel_events)",
  "deferred_to": "the owning rung's §8.6 stage-2 Conform",
  "landed_at": "pre-campaign for all nine rows",
  "disclosed_via": "DECISIONS.jsonl D-30 part 1 (the named-field test) — applied by M0-T36; plus D-23 (lel_events) and D-28 part 4 (bg_sky_calendar) for the two rows that already had a reason",
  "reason": "`target_table` is named by NO Phase-0 step and NO M0 acceptance criterion. Phase 0.2 — the only step naming registry columns — names `integrity_check_sql` and `target_floor`, not this one. Clause (a) of the named-field test fails, so the column belongs to the rung that owns the asset and repairing it in M0 is the I13 breach D-30 names. Clause (b) confirms two rows independently: plan §15's per-asset entries for bo_cdlm_summary and bo_chart_gestalt each carry 'Declare target_table', and both are R2. bg_sky_calendar is separately trigger-bearing — its target_table names `bg_sky_events`, a relation ABSENT from production — and D-28 part 4 routed it to R0 intake. WHAT THIS DOES NOT SETTLE: whether a NULL target_table on the four chart_facts co-writers is deliberate. That question travels to R1 with the rows; it is not answered here and must not be read as answered.",
  "measured": {
   "violations": 9,
   "rows": [
    "bg_prashna_rules",
    "bg_sky_calendar",
    "bo_cdlm_summary",
    "bo_chart_gestalt",
    "ga_sade_sati",
    "ga_sensitive",
    "ga_strength",
    "ga_structural",
    "lel_events"
   ],
   "classes": {
    "target_table_null": 8,
    "target_table_missing": 1
   },
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-06

```json
{
 "C-06": {
  "rule": "C-06",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R5 (Mīmāṃsā rung), stage 2 Conform",
  "deferred_to": "R5",
  "landed_at": "pre-campaign",
  "disclosed_via": "DECISIONS.jsonl D-30 part 1 — applied by M0-T36",
  "reason": "One row: mi_seva. `count_sql` is named by no Phase-0 step and no M0 acceptance criterion — clause (a) fails. C-06 is additionally a shadow of C-07: mi_seva is asset_kind='service' and a service carries no count_sql at all, so the row disappears when C-07's row does. Same destination (R5) by two independent routes.",
  "measured": {
   "violations": 1,
   "rows": [
    "mi_seva"
   ],
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-07

```json
{
 "C-07": {
  "rule": "C-07",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R3 (ka_dasha_kala, ka_tulana) and R5 (mi_abhilekha, mi_seva)",
  "deferred_to": "the owning rung's §8.6 stage-2 Conform",
  "landed_at": "pre-campaign",
  "disclosed_via": "DECISIONS.jsonl D-30 part 1 (named-field test) — applied by M0-T36; and D-19 part 1 + D-27 part 2a for the target_floor half",
  "reason": "Four service rows carrying data-asset fields. THE HONEST SHAPE: three of the four columns (`target_table`, `count_sql`, `clear_tables`) are named nowhere in Phase 0, so clause (a) fails flatly. The fourth, `target_floor`, IS named by Phase 0.2 — but as a REQUIRED FIELD OF THE CONTRACT SPECIFICATION being authored, not as a population M0 performs; the clause assigning the work of setting floors is §8.6 stage 2 ('floors set to achieved (I7)'), per rung, which is refinement (b) firing. D-19 part 1 already held floors rung-owned ('a declarative source file structurally CANNOT hold a measured value') and D-27 part 2a re-affirmed it. DURABILITY, which makes the deferral load-bearing rather than merely correct: three of the four columns are SEED-OWNED, so a DB-only NULLing in M0 would be reverted by the next re-seed.",
  "measured": {
   "violations": 4,
   "rows": {
    "ka_dasha_kala": [
     "target_floor"
    ],
    "ka_tulana": [
     "target_floor"
    ],
    "mi_abhilekha": [
     "count_sql",
     "target_floor",
     "target_table"
    ],
    "mi_seva": [
     "count_sql",
     "target_floor",
     "target_table"
    ]
   },
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-08

```json
{
 "C-08": {
  "rule": "C-08",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R3 (Kāla rung), lifecycle exit",
  "deferred_to": "R3",
  "landed_at": "2026-08-12T16:30:19Z (the asset's last build; RETIRED since)",
  "disclosed_via": "DECISIONS.jsonl D-12 part 4 (ADHIKĀRIN, 2026-08-23T04:46:23Z), quoting plan §14.2 by name",
  "reason": "One row: ka_gochara_sweep, RETIRED with data_disposition NULL. Plan §14.2 names this exact asset's data_disposition as R3 work; D-12 part 4 quotes that sentence and defers it. THE ASSET IS CHARTER P1 — its 38,287 v1 gochara rows are recoverable only from the 2026-08-23 snapshot — so any operation on it is reserved to the native, not merely deferred. H6 was respected under real temptation here: migration 590's own header says the disposition is 'almost certainly' known, and D-31 records that leaving it NULL was right, because 'almost certainly' is not a detector. THE SAME ASSET IS THE SUBJECT OF X-02, which is already disclosed and already non-gating; C-08 is the identical situation one column over, and is BLOCKING.",
  "measured": {
   "violations": 1,
   "rows": [
    "ka_gochara_sweep"
   ],
   "catalog_status": "RETIRED",
   "is_active": false,
   "charter": "P1 — unrecoverable asset",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-15

```json
{
 "C-15": {
  "rule": "C-15",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R3 (ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana) and R5 (mi_abhilekha, mi_seva)",
  "deferred_to": "the owning rung — §8.6 stage-2 Conform for provides_apis; tier-S probe work (§9) for health_probe",
  "landed_at": "pre-campaign",
  "disclosed_via": "DECISIONS.jsonl D-30 part 1 — applied by M0-T36; §8.4's R3 row for the probe half",
  "reason": "Six DRAFT service rows with health_probe and provides_apis both NULL. Neither column is named by any Phase-0 step or M0 acceptance criterion — clause (a) fails for both. THE TWO HALVES ARE NOT THE SAME KIND OF THING and the deferral matters more for one: `provides_apis` is a declaration, but `health_probe` is a DETECTOR, and §8.4's R3 row already assigns 'a real known-answer probe with an SLO' to R3 by name for two of these assets (clause (b) firing). Authoring a probe in M0 to clear C-15 would be manufacturing a detector to satisfy a criterion — the H3 shape D-29 part 5 named for the sibling rule C-17. CORRECTION TO THE CONTRACT'S OWN §6 CELL, carried from v1.0: that cell reads '6 (all 6 service rows)'. There are EIGHT service rows live since the M0-T21 kind repair; the count is unchanged for a different reason than the contract states, because the two new ones (bg_ephemeris_engine, bg_panchanga) DO carry both fields.",
  "measured": {
   "violations": 6,
   "rows": [
    "ka_dasha_kala",
    "ka_graha_sancara",
    "ka_muhurta_seva",
    "ka_tulana",
    "mi_abhilekha",
    "mi_seva"
   ],
   "live_service_rows": 8,
   "contract_s6_cell_says": 6,
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-17

```json
{
 "C-17": {
  "rule": "C-17",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R3 (Kāla rung), stage-1 intake",
  "deferred_to": "R3",
  "landed_at": "the three 'healthy' rows were last written by a self-test on 2026-08-02; health_probe has always been NULL on all four",
  "disclosed_via": "DECISIONS.jsonl D-13 part 2 AS CORRECTED AND EXTENDED BY D-29 (ADHIKĀRIN, 2026-08-23T07:44:26Z)",
  "reason": "Four rows, and D-29 is the reason all four are now covered where v1.0 could cover only three. THREE are false greens: ka_dasha_kala, ka_muhurta_seva and ka_tulana read service_health='healthy' with no health_probe — a status with no detector, H4 / CLAUDE.md §N.8, the campaign's founding defect sitting live in the registry. THE FOURTH IS DIFFERENT IN KIND and D-29 part 3 insists it not be folded in: ka_graha_sancara reads 'unhealthy' with no probe, which is A RED WITH NO DETECTOR BEHIND IT — §N.8 in its other direction. It FAILS SAFE (it understates confidence rather than overstating it) and it must NOT be 'fixed' by clearing it to healthy or NULL when R3 opens; only a real probe may retire it. D-29 also corrected D-13's destination from R0 to R3: all four assets are ka_* / layer=kala, and ZERO ka_* assets carry rung='R0'. Independently, the named-field test reaches the same place — neither `health_probe` nor `service_health` is named by any Phase-0 step. NOTE THE DOUBLE REPORT (D-29 part 4): ka_graha_sancara also has a SERVING-side defect ruled separately at D-26 (deriveState() returns service_ok, overriding the stored 'unhealthy'). Different defects, different layers, different owners; fixing one leaves the other.",
  "measured": {
   "violations": 4,
   "rows": {
    "ka_dasha_kala": "healthy",
    "ka_graha_sancara": "unhealthy",
    "ka_muhurta_seva": "healthy",
    "ka_tulana": "healthy"
   },
   "health_probe": "NULL on all four",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-20

```json
{
 "C-20": {
  "rule": "C-20",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R0 (Brahmagyan rung), §8.6 stage-2 Conform",
  "deferred_to": "R0",
  "landed_at": "pre-campaign",
  "disclosed_via": "DECISIONS.jsonl D-19 part 1 and D-27 part 2a",
  "reason": "Three R0 rows with target_floor NULL: bg_class_priors, bg_formula_constants, bg_ghatana. THIS IS THE ONE COLUMN THE CAMPAIGN HAS RULED TWICE. D-19 part 1: a floor is the MEASURED ACHIEVED COUNT (I7), 'a declarative source file structurally CANNOT hold a measured value', and measured values are written at §8.6 stage 2 Conform, per rung. D-27 part 2a re-affirmed it with a number behind it. Setting a floor in M0 would also collide with charter G2's bound — to the measured achieved count only, never an invented number — and the measurement that would justify it is R0's intake, which has not run.",
  "measured": {
   "violations": 3,
   "rows": [
    "bg_class_priors",
    "bg_formula_constants",
    "bg_ghatana"
   ],
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-21

```json
{
 "C-21": {
  "rule": "C-21",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "four rungs — R0 ×2, R1 ×2, R2 ×2, R3 ×12, R5 ×1",
  "deferred_to": "the owning rung's §8.6 stage-2 Conform",
  "landed_at": "pre-campaign",
  "disclosed_via": "DECISIONS.jsonl D-19 part 1 (volume_explanation named in the campaign-owned set) + charter G4",
  "reason": "Nineteen rows with target_floor = 0 and volume_explanation NULL. A volume_explanation on a zero floor is precisely a charter G4 by-design classification, and G4 requires a WRITTEN by-design justification PER ASSET — a per-asset judgment about that asset's data, which is exactly what I14 keeps out of Track M. D-19 part 1 names it in the campaign-owned set ('volume_explanation WHERE IT RECORDS A G4 BY-DESIGN CLASSIFICATION') and places it at the owning rung's Conform. Same durability precondition as C-20: the column is seed-owned and would move on 47 cells at the next re-seed. Plan §8.4's R5 row independently names this work for its own layer ('zero-row-by-design assets recorded honestly with target_floor = 0 and a volume_explanation'), which is clause (b) firing for at least that rung.",
  "measured": {
   "violations": 19,
   "by_rung": {
    "R0": 2,
    "R1": 2,
    "R2": 2,
    "R3": 12,
    "R5": 1
   },
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-22

```json
{
 "C-22": {
  "rule": "C-22",
  "severity_in_the_rule_table": "RUNG",
  "gates_the_exit_code_today": false,
  "owner": "every rung, at its own §8.6 stage-2 Conform",
  "deferred_to": "each rung in turn",
  "landed_at": "n/a — the rule has never had a satisfiable antecedent",
  "disclosed_via": "structural fact, measured; plan §8.6 stage 2 ('integrity_check_sql authored per asset') and the closing paragraph ('Stage 2 is deliberately inside the rung rather than in Track M')",
  "reason": "VACUOUS TODAY AND REPORTED AS VACUOUS RATHER THAN AS A PASS. The antecedent is 'rung-frozen' and no rung has frozen — R0 has not opened. Measured separately and worth stating plainly: 0 of 128 live assets carry an integrity_check_sql at all. The column is NOT seed-written, so checks authored at Conform are durable. Severity RUNG, so it does not gate today; it is disclosed anyway because D-30 part 4 says every deferred rule carries its entry, and because a rule that is vacuous now will stop being vacuous the moment R0 freezes.",
  "measured": {
   "status": "not_checkable (vacuous — 0 rungs frozen)",
   "assets_with_integrity_check_sql": 0,
   "of": 128,
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-25

```json
{
 "C-25": {
  "rule": "C-25",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": false,
  "owner": "UNDECIDED — the named-field test reaches it (Phase 0.4 names partition declaration) but §8.6 stage 2 assigns 'partitions declared' to every rung; see crit-5 and §9.3",
  "deferred_to": "undecided — M0 under Phase 0.4, or each rung under §8.6 stage 2",
  "landed_at": "n/a — no column has ever existed",
  "disclosed_via": "ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9 / §6 / §10.3 (contract-mandate: 'Rules C-25, C-26 and C-27 must never be reported as passing')",
  "reason": "THE MODEL DEFERRAL — a reason written into the specification itself. No schema column exists for a natural-key partition declaration. The contract states in its own §6 that these rules must never be reported as passing, 'a CI guard implementing this document emits them as not_checkable with the reason, and a dashboard that renders that as a pass is itself a defect'. The shipped guard hard-wires exactly that (check_asset_catalogue_contract.py, `_no_detector`) and its own cross-check FAILS if the guard and the contract ever disagree about which rules are not_checkable. This is what a well-formed deferral looks like: a named structural fact, a specification that records it, a detector that refuses to report green, and a guard test that catches the two drifting apart. IT DOES NOT GATE TODAY because not_checkable is excluded from the exit code — but note that its severity is BLOCKING, so if a column ever appears the rule gates immediately. WHAT IS UNDECIDED IS THE WORK, NOT THE RULE: the rule's not_checkable status is correct and permanent-until-a-column-exists; whether M0 or the rungs should create that column is crit-5's open question.",
  "measured": {
   "status": "not_checkable",
   "co_written_target_tables": 5,
   "co_writer_rows": 16,
   "X-01_undeclared_collisions": 0,
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-26

```json
{
 "C-26": {
  "rule": "C-26",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": false,
  "owner": "the rung that owns each generation-bearing asset",
  "deferred_to": "the owning rung",
  "landed_at": "n/a — no column has ever existed",
  "disclosed_via": "ASSET_CATALOGUE_CONTRACT_v1_0.md §4.11 / §6 / §10.3 (contract-mandate)",
  "reason": "Same shape as C-25 — no schema column for an authority pointer / protected_generations, the contract forbids reporting it as passing, the guard hard-wires not_checkable with that reason. ONE DIFFERENCE FROM C-25 AND IT IS THE DECISIVE ONE: no Phase-0 step names an authority pointer as M0 content, so unlike C-25 BOTH the rule and the work are deferred, and the named-field test settles it cleanly rather than leaving it open.",
  "measured": {
   "status": "not_checkable",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-27

```json
{
 "C-27": {
  "rule": "C-27",
  "severity_in_the_rule_table": "ADVISORY",
  "gates_the_exit_code_today": false,
  "owner": "Track M2 (cleaned telemetry), then each rung's Conform",
  "deferred_to": "M2",
  "landed_at": "n/a",
  "disclosed_via": "ASSET_CATALOGUE_CONTRACT_v1_0.md §6 severity column + plan §4.8",
  "reason": "ADVISORY by the contract's own severity column, and not checkable until Track M2 produces cleaned telemetry — the p95 the rule compares against does not exist yet. Recorded, explicitly not green. Does not gate today on two independent grounds (ADVISORY severity AND not_checkable status), and is disclosed anyway for completeness with D-30 part 4.",
  "measured": {
   "status": "not_checkable",
   "blocked_on": "M2 cleaned telemetry",
   "measured_at": "2026-08-23T08:00:51Z"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

### disclosure · C-28_residual

```json
{
 "C-28_residual": {
  "rule": "C-28",
  "severity_in_the_rule_table": "BLOCKING",
  "gates_the_exit_code_today": true,
  "owner": "R0 (Brahmagyan rung) — all 31 residual rows are R0",
  "deferred_to": "R0's own build (only a real build can retire it)",
  "landed_at": "n/a — these assets have never completed a tracked build",
  "disclosed_via": "DECISIONS.jsonl D-30 part 3 (G7 deferral, ADHIKĀRIN, 2026-08-23T07:46:10Z), indexed as a G7 by D-31 part 2",
  "reason": "PARTIAL DISCLOSURE — THIS COVERS 31 OF C-28's 105 ROWS AND NOT THE OTHER 74, AND THAT DISTINCTION IS THE POINT. Re-measured read-only by M0-T36: 74 rows are backfillable from the median of their completed build_run_assets rows, which is D-6's authorised statement T-5 and is REPAIRABLE-IN-M0, not deferred. The remaining 31 have NO completed build_run_assets row at all, so no measured duration exists and D-6 condition 4 forbids inventing one ('an asset with no clean telemetry gets NULL, not a plausible number', H6). There is no path to zero for those 31 that does not pass through either a real build or a fabrication. All 31 are R0, so R0's freeze inherits this rather than rediscovering it. NOTHING HAS BEEN EXECUTED: M0-T3 produced the T-5 proposal with `writes_executed: NONE`, so C-28 reads 105 today, not 31, and any statement that C-28 is deferred is premature by 74 rows.",
  "measured": {
   "guard_violations_total": 105,
   "backfillable_by_T5": 74,
   "deferred_residual": 31,
   "residual_by_rung": {
    "R0": 31
   },
   "T5_executed": false,
   "note_scorecard_disagrees": "the scorecard's C-28 SQL returns 112 because it does not filter by asset_kind; the 7 extra rows are all services — finding F-T36-1",
   "measured_at": "2026-08-23T08:0xZ"
  },
  "disclosed_at": "2026-08-23",
  "disclosed_by": "KĀRAKA (Nirmāṇa autonomous campaign, WORK_QUEUE id M0-T36)",
  "certified_by": null,
  "wired_into_the_guard": true,
  "gating_effect": "none",
  "gating_effect_reason": "recorded, read and validated by the guard; NOT demoting. Only ADHIKĀRIN may add `gating_effect=\"non_gating\"` + `authorised_by=<D-n>` + an itemised `covers` list, and even then the rule still reports every violation — a disclosure makes a residual visible and non-gating, never invisible (D-12 part 4, D-10 part 3).",
  "does_not_turn_the_rule_green": true
 }
}
```

## 11 — Re-measurement (M0-T36)

**At:** `2026-08-23T08:00:51Z (contract guard, --live --json, READ-ONLY) and 08:0xZ (direct read-only SQL)`

NOTHING MOVED. Every contract-rule count is IDENTICAL to the 06:58:51Z reading v1.0 recorded — 13 pass / 16 fail / 4 not_checkable, the same 15 BLOCKING ids, the same per-rule violation counts. Criterion readings are unchanged too, including origin/main (re-verified @ 2670e61e2: all three guard/workflow files still ABSENT). THE REASON IS WORTH STATING, because 'four verdicts landed and nothing changed' reads like a null result and is not one: V-8, V-9 and V-10 certified writes that had ALREADY LANDED before v1.0 measured — migration 590 at 05:36:13Z, has_substeps before 06:20Z, the layer repair at ~06:51–06:54Z, and v1.0's first reading is 06:55:57Z. The certifications changed those writes' EVIDENTIARY STATUS, not the registry. V-11 certified this register itself and wrote nothing. D-29 and D-30 are rulings, which move buckets, not rows. So the correct reading is: the register's numbers were already post-repair when they were taken, and four verdicts later they still are.

**Scorecard:** reading 4 appended to m0_exit_scorecard.json's `_meta.reading_history` (append-only; readings 1–3 preserved byte-for-byte). Tally unchanged from reading 3: PASS 1, FAIL 7, NOT-MEASURABLE 3, BLOCKED 1.

### New findings

#### `F-T36-1` · MEDIUM · The two C-28 detectors disagree by 7, and the 7 are all services

The shipped guard reports C-28 = 105; the scorecard's SQL reports 112. Neither is wrong — they are different rules wearing one id. `c28()` in check_asset_catalogue_contract.py:860-861 skips any row whose `asset_kind` is not in DATA_KINDS; the scorecard's SQL (m0_exit_scorecard.py:743-747) does not filter by kind. The 7 rows in the gap are ALL `asset_kind='service'`: bg_panchanga, ka_dasha_kala, ka_graha_sancara, ka_muhurta_seva, ka_tulana, mi_abhilekha, mi_seva. This is the SAME defect class as crit-1's — one criterion, two detectors, two different meanings of zero — and it had not been named for C-28. It matters for the flip because the residual D-30 part 3 deferred (31) was measured under the guard's definition; under the scorecard's it would be 31 plus however many of those 7 services never complete a build. NOT RULED, NOT FIXED — neither file was edited to reconcile them.

#### `F-T36-2` · HIGH · CI never runs the guard against production — it runs --baseline against a frozen 05:09:17Z snapshot

Every number in this register, in the scorecard, in V-11 and in D-30 comes from `--live`. THE WORKFLOW DOES NOT RUN `--live`. .github/workflows/nirmana-m0-guards.yml invokes `--self-test` and `--baseline`, and `--baseline` is a shorthand for `--snapshot asset_catalogue_baseline_20260823.json`, a file captured at 2026-08-23T05:09:17Z — BEFORE migration 590 applied (05:36:13Z) and before the Phase 0.5a layer repair (~06:51Z). Run today it exits 1 with pass=6 fail=18 not_checkable=9 and **17 BLOCKING failures**, not 15: it still fails C-05, C-14 and C-23, all three of which PASS live, and it reports C-08/C-09/C-10/C-18/C-19 as not_checkable because migration 590's columns do not exist in the snapshot. CONSEQUENCE FOR THE FLIP: removing `continue-on-error` today would gate the branch on a detector reading a three-hour-old file, not on production — a signal that does not measure the claim it makes (CLAUDE.md §N.8), and one that would red the branch on three rules the campaign has already repaired and PARĪKṢAKA has already certified. Refreshing the snapshot, or changing what CI invokes, is a THIRD prerequisite for the flip that no ledger line has recorded. NOT FIXED: no .github/ file and no baseline snapshot was written by M0-T36.

#### `F-T36-3` · HIGH · A disclosure entry cannot be honoured for any rule except X-02 — the guard has no code path that reads one

D-30 part 4's amended flip condition requires that 'EVERY DEFERRED RULE CARRIES ITS DISCLOSURE ENTRY'. M0-T36 drafted them (see §9). THEY ARE INERT, and that must be said plainly rather than discovered at flip time. Two mechanical facts: (i) `disclosed_additions` is keyed by ASSET_ID and is read in exactly one place, check_asset_catalogue_contract.py:951 inside `x02()`; no other rule function opens the residuals file except `x05()`, which reads a different block (`zero_consumer_dispositions`). (ii) Severity is a hardcoded constant in the RULES table (line 1142: `Rule("X-02", RESIDUAL, …)`); a disclosure cannot demote a rule from BLOCKING, and X-02's docstring is explicit that a disclosure does NOT turn a rule green — 'what the disclosure buys is that the severity is RESIDUAL'. X-02 is non-gating because someone TYPED `RESIDUAL` in the rule table, not because it carries a disclosure. SO: writing the fifteen entries satisfies D-30 part 4's letter and changes nothing the guard does. Making them honourable requires a guard code change — a per-rule disclosure reader and a disclosure-conditioned severity — and that change is a demotion of thirteen BLOCKING gates, which is exactly the shape H3 exists to scrutinise. IT IS NOT A KĀRAKA's CHANGE AND M0-T36 DID NOT MAKE IT. The guard was run read-only and not edited.

---

## 12 — D-38 / D-39 / D-40 / D-41 / D-42 applied (M0-T46)

Six ADHIKĀRIN rulings landed after v1.1 (M0-T36) closed §§0–11 above. This section documents what each did to this register; §§0–11 are left exactly as v1.1 wrote them (history), and the per-entry sections above carry the new addenda prefixed to the preserved v1.1 text, in the same discipline v1.1 used for D-30.

### 12.1 — Before / after tally

| | REPAIRABLE-IN-M0 | DEFERRED-WITH-REASON | RESERVED | UNEXAMINED | AT-ZERO-WITH-EXPOSURE |
|---|--:|--:|--:|--:|--:|
| criteria — before | 3 | 2 | 1 | 5 | 1 |
| criteria — after | 3 | 3 | 1 | 3 | 2 |
| rules — before | 3 | 15 | 1 | 1 | 0 |
| rules — after | 2 | 16 | 1 | 0 | 1 |

**Moved:**

- crit-4 REPAIRABLE-IN-M0→DEFERRED-WITH-REASON (D-38)
- C-11 REPAIRABLE-IN-M0→DEFERRED-WITH-REASON (D-38)
- crit-9 REPAIRABLE-IN-M0→AT-ZERO-WITH-EXPOSURE (D-38)
- X-05 REPAIRABLE-IN-M0→AT-ZERO-WITH-EXPOSURE (D-38)
- crit-5 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)
- crit-8 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)
- X-03 UNEXAMINED→REPAIRABLE-IN-M0 (D-39)

**Reframed, bucket held:**

- C-28 — D-42 corrects the framing ('lit with no completed build_run_assets record', not 'missing estimated_seconds'); bucket held at REPAIRABLE-IN-M0, the D-30 part 3 deferral for the 31-row residual is unchanged and now better grounded

6 of 32 entries were UNEXAMINED after v1.1 (M0-T36): crit-1, crit-2, crit-5, crit-8, crit-10, X-03. D-39 resolves 3 of those 6 to REPAIRABLE-IN-M0 (crit-5, crit-8, X-03). The other 3 (crit-1, crit-2, crit-10) are untouched by these six rulings and stay UNEXAMINED — 3 of 32 entries remain UNEXAMINED after v1.2.

### 12.2 — D-38: Phase 0.8b and 0.8c decided

**0.8b — REMAIN DRAFT, a decision not a deferral.** Neither ga_vichara (R1) nor ka_dasha_kala / ka_sangam (R3) is named by a rung-specific promote-or-retire clause (only R2's nine, R3's ka_graha_sancara/ka_muhurta_seva, R4's nine and R5's lel_events are named), so the general REMAIN-DRAFT disposition governs all three and criterion 4 / C-11 move to DEFERRED-WITH-REASON.

**0.8c — all 23 packets adjudicated by reading class:**

| reading class | n | D-38 disposition | assets |
|---|--:|---|---|
| INPUT-ONLY | 8 | no action, closed | bg_cohort, bg_gochara_arcs, bg_kota_chakra_rings, bg_kp_sublord_division, bg_phaladeepika_latta, bg_reference, bg_vedha_malefic_scale, ka_gochara_v3_century_materialize |
| NO CONSUMER FOUND | 1 | retirement candidate, NOT retired — routed to owning rung | bg_concordance |
| METHOD-BLIND | 7 | no action, closed as UNKNOWN — explicitly NOT a retirement candidate | bg_panchanga, bg_sky_calendar, bo_cdlm_summary, bo_samskara, ka_graha_sancara, ka_kshetra, mi_jivanaghatana |
| SHADOWED | 5 | a real defect — routed to owning rung | bg_vidhi_floors, bg_vidhi_primitives, ka_dasha_kala, ka_muhurta_seva, ka_tulana |
| BY DESIGN EMPTY / CATEGORY MISMATCH | 2 | no action, closed, mismatch recorded | bg_ephemeris_engine, bg_sarvatobhadra_grid |

**23 of 23 packets adjudicated; 0 unresolved.** **6 of 23** (1 retirement candidate + 5 SHADOWED defects) carry follow-on asset-lifecycle work routed to their owning rung — a recorded determination, not an open question, per D-38's own holding that adjudication IS resolution. Criterion 9 / X-05 move to AT-ZERO-WITH-EXPOSURE.

### 12.3 — D-39: X-03, criterion 8 and criterion 5 confirmed M0's, the P5 question settled

D-39 part 4, independently re-deriving the named-field test rather than inheriting D-30's assertion of it, CONFIRMS ownership of X-03, criterion 8 and criterion 5 to M0 and settles that their columns are 'inside the plan's naming and NOT reserved by P5 … subject to D-4's standing conditions'. What v1.1 filed as UNEXAMINED ('ownership settled to M0, mechanism still undecided') has its mechanism question resolved: the column is authorised, not reserved. All three move to REPAIRABLE-IN-M0 — a known repair (add the column under D-4's conditions, backfill, verify) now exists; nobody has executed it.

### 12.4 — D-40: the flip condition's CI clause, final form

D-39 part 1 added 'CI MUST GATE AGAINST LIVE STATE' to the flip condition. D-40 part 1 WITHDREW that clause as an impossibility M0-T40 root-caused: CI Actions carries no database credential (`platform/.env.local` does not exist there), so `--live` cannot run. D-40 replaces it: CI must DETECT AND REFUSE A STALE BASELINE instead — two DB-free detectors (age, and schema-behind: declared columns minus baseline columns) that can run without a credential. This register's own frontmatter and §10 now state the final condition; no criterion or rule bucket in this register turns on the CI clause itself, so nothing in §§0–9 moves because of D-40 — only the STATEMENT of the condition changes.

### 12.5 — D-42: C-28 reframed; the build_run_assets ranking

**D-42 APPLIED (M0-T46).** ADHIKĀRIN ruling D-42 reclassifies this residual's FRAMING and forbids both available 'fixes'. THE OLD FRAME WAS WRONG: this is not '31 assets missing an estimated_seconds'. D-42's authoritative framing: '31 ASSETS READ lit WITH NO COMPLETED RUN RECORD BEHIND THEM' — the missing estimate is a symptom, the unearned `lit` is the finding (D-13's telemetry pollution meeting §N.8's no-op-completion class). RANKING ESTABLISHED FOR THE WHOLE REGISTER, NOT JUST THIS RULE: 'build_run_assets IS AUTHORITATIVE. asset_throughput.state="lit" IS A CLAIM ABOUT A BUILD, NOT EVIDENCE OF ONE' — applying wherever a surface asks 'was this asset built', including criterion 8's build-coverage half (see that entry). TWO FIXES ARE EXPLICITLY FORBIDDEN, NOT MERELY DISCOURAGED: backfilling estimates for the 31 (H6 — a number on a build nothing witnessed), and RE-POINTING c28()'s detector at build_run_assets to close it — 'under the authoritative definition C-28 would report zero violations and a BLOCKING failure would pass — while all 31 unearned lit states remain exactly as they are. That is a weakening under D-41 part 2 and presumptively H3.' NEITHER FIX IS THIS TASK'S TO MAKE AND NEITHER WAS MADE — no detector in m0_exit_scorecard.py or check_asset_catalogue_contract.py was re-pointed by M0-T46; a future re-pointing found inconsistent with this ruling is a finding for a separate task, not a repair for this one. THE BUCKET DOES NOT MOVE — the deferral for the 31 stands (D-30 part 3), now grounded on the definitional finding rather than the absence of estimates — and the 31 unearned lit states are additionally understood as ROUTED TO THEIR OWNING RUNGS (all R0), since D-42 holds 'each rung's own build is the only thing that can earn or refute a lit'.

### 12.6 — D-37 and D-41: read, no bucket change

**D-37** corrects D-12 part 3's premise (the three orphaned throughput rows belong to ka_kota_chakra / ka_vedha_gochara / mi_sankalpa, not ka_gochara_sweep) and clarifies the named-field test's refinement (b) fires only on a clause naming a specific asset or a specific field at a specific rung. None of the three assets or the clarified refinement changes any entry this register classifies.

**D-41** authorises the deploy.yml sentinel-assertion edit and states a CI-edit-by-direction rule (strengthening changes proceed without a ruling; weakening changes are presumptively H3). M0-T46 searched this file, M0_EXIT_SCORECARD_v1_0.md and M0_CLOSE_READINESS_v1_0.md for an open 'awaiting a ruling on CI edit scope' flag and found none — D-41 has nothing to resolve in these three instruments. D-41's standing mutation-testing requirements (structural assertion + inverse-direction mutation, per part 3) bear on future guard-code changes, not on this classification register.

### 12.7 — What this task did not do

No `asset_registry` row was written (this generator has never queried the database directly — every `measured` value is a frozen figure from when M0-T17/M0-T36 or the guard last measured it live; the fresh live re-measurement for this task ran through `m0_exit_scorecard.py`, whose own reading 5 shows criterion 4 unchanged at 3 and criterion 9's packet count unchanged at 23). No guard file was edited — `c28()` and every other detector in `check_asset_catalogue_contract.py` and `check_asset_source_parity.py` are unchanged. No `.github/` file was touched. No new entry was added to `DISCLOSURE_DRAFT` (C-11's newly-deferred status has no disclosure drafted for it — see `DISCLOSURE_NOT_DRAFTED`), so a re-run of this generator's `_write_disclosure_block()` should not change `platform/scripts/governance/asset_catalogue_disclosed_residuals.json`'s content; if it does, M0-T46 reverted that file to keep this task's footprint inside `00_ARCHITECTURE/control/`, per its own scope instruction. No `DECISIONS.jsonl` or `state/*.jsonl` line was edited. `ka_gochara_sweep` (charter P1) was not touched. No UNEXAMINED entry this task did not name was resolved, and nothing here is certified — that is PARĪKṢAKA's (I16 / H7).

