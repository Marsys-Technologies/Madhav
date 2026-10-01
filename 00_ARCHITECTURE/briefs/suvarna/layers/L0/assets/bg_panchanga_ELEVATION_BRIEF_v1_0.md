---
asset_id: bg_panchanga
layer: L0 Brahmagyan (bg_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
base_commit: "main 0250cbade"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [bg_panchanga-G01, bg_panchanga-G02, bg_panchanga-G03, bg_panchanga-G04, bg_panchanga-O1, bg_panchanga-O2, bg_panchanga-Earn.build_record, bg_panchanga-Cost.baseline, bg_panchanga-Dens.served, bg_panchanga-Carr.detector, bg_panchanga-Earn.service_state, bg_panchanga-G01, bg_panchanga-Carr.D3, bg_panchanga-G02, bg_panchanga-Carr.detector]
---
# bg_panchanga — Panchanga engine (service; no table)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

A registered service, not a table: 'Deterministic panchang computation service (swisseph DE441, Lahiri ayanamsha, Drik-parity). Exposes `panchanga_instant(instant,lat,lon,tz_offset)` and `panchanga_day(date,lat,lon,tz_offset)`. Zero LLM. Floor: 5 angas + timing windows + 9 graha states.' `has_writer = false`, no table, `count_sql`, integrity SQL or floor by design; its status is `asset_throughput.state = lit` with `rows_written = 0`. Backed by `platform/python-sidecar/panchang_engine/` (it calls pyswisseph directly: `panchang_engine/__init__.py:59-71,149-150,241`, not the `ephemeris_daily` table) and served through `call_panchanga_service.ts`. Declared dependent `ga_panchanga` (census direct 1 / transitive 57): L1's panchanga facts rest on it. The registry declares 0 dependencies for it (ledger `bg_panchanga-G04`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | service | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:418` | seed (live may differ by migration) |
| writer / `@register` | none registered in code; registry `has_writer` = False | writers dir, census `Build.registered` |
| target table(s) | `None`; count_sql tables: — | census CEN-R |
| live rows / floor | None / — (Δ —) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 57 (every layer); named: `ga_panchanga` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | no table (service) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 759b43c7 complete/no disposition (2026-08-27) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): call_panchanga_service.ts; declaring density_contract: 0 |
| Build | Build.completion | N/A | no count_sql and nothing to count: has_writer=False, asset_kind='service', no target_table; build state='lit' |
| Build | Build.contract | N/A | no writer, and the registry agrees (has_writer=false) — nothing to scan |
| Build | Build.count_integrity | N/A | count_sql=no, integrity_check_sql=no |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Build | Build.registered | N/A | no writer, and the registry agrees (service or static) |
| Build | Build.target † | N/A | no target_table; asset_kind='service', has_writer=False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 759b43c7 complete/no disposition (2026-08-27) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.dag †; Build.exercised (1 executed run(s) of 1 build_run_assets row(s), scope(s): asset_set, last executed 2026-08-27); Build.history.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem NO_DETECTOR · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_panchanga-G01 | Earn | detector | the only status is `lit` with 0 rows: identical to a service that produced nothing; no probe can read false \| ledger: measured: the asset's only status is asset_throughput state='lit' with rows_written=0 — identical to what a writer that produced nothing would write; no liveness or corr… |
| bg_panchanga-G02 | Carr | detector | no limb is recomputed a second way |
| bg_panchanga-G03 | Complete / Reach | information | no census of the response fields (five limbs with convention, boundary, precision; fields exposed ÷ returned) \| ledger: measured: no census of the service's response fields — completeness (five limbs, each with convention, boundary, precision) and reachability both unmeasured / required: … |
| bg_panchanga-G04 | Build (dag) | real (registry) | declared 0 dependencies; the service computes with swisseph, so the edge (if declared) belongs on the engine; see FD-3 \| ledger: measured: the registry gives bg_panchanga 0 dependencies while the service cannot compute without ephemeris positions / required: the DAG matches the actual computation … |
| bg_panchanga-O1 | NONE | opportunity | a service kind the build system can judge \| ledger: a service kind the build system can judge, for every service asset in the plane (2 in L0, more above) |
| bg_panchanga-O2 | NONE | opportunity | a declared edge where a real one exists \| ledger: a declared edge where a real one exists |
| bg_panchanga-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_panchanga-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_panchanga-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | 1 module: `call_panchanga_service.ts`; CF-04 \| ledger: measured: 1 module(s): call_panchanga_service.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_panchanga-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_panchanga-Earn.service_state | Earn | detector | duplicate of G01 after folding \| ledger: measured: the asset's only status is asset_throughput state='lit' with rows_written=0 — identical to what a writer that produced nothing would write; no liveness or corr… |
| bg_panchanga-Carr.D3 | Carr | detector | duplicate of G02 after folding |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — a service whose output feeds L1; the open items are a probe that can fail, an independent re-derivation of a limb and a missing registry edge. T4's storage/completeness clauses assume a table (TGH-T4-02).

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Service probe

- **Answers:** ledger `bg_panchanga-G01` / O1; CF-05
- **Change:** a probe that answers a pinned instant (and location) and compares the five angas to a stored expected set held as a fixture; `lit` is then backed by a check that can return false. The fixture must be derived once from a recorded service answer, not hand-typed, and its provenance stated.
- **Files / declaration / migration:** a probe in Track E tooling + a fixture under `platform/python-sidecar/panchang_engine/tests/`
- **Failing-first test and mutation:** failing-first: a service with a wrong ayanāṃśa convention fails the probe; mutation: change the expected tithi → fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Earn
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T4-02

### FD-2 · Carr detector — D3 tithi/vāra a second way

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** recompute tithi and vāra for pinned instants from the Sun–Moon elongation computed through a second route (the analytic Moshier mode, or `ephemeris_daily` interpolation) and compare; a seeded wrong convention (e.g. a different ayanāṃśa) must be caught. Ledger `bg_panchanga-G02`.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-3 · Registry edge

- **Answers:** ledger `bg_panchanga-G04` / O2; CF-03
- **Change:** declare the dependency the computation actually has. The ledger proposes `bg_panchanga → bg_ephemeris`, but the engine calls swisseph directly, so the candidate edge is `bg_panchanga → bg_ephemeris_engine` (the pinned-corpus service); confirm by reading the service wiring before the migration. Adding an edge moves DAG order and the upstream hash; Track I’s migration 1210 excluded L0 bedrock edges, so this needs its own review.
- **Files / declaration / migration:** a surgical migration (`depends_on`) + seed literal
- **Failing-first test and mutation:** failing-first: a topological read places the service after its dependency; the dag reads-match scan agrees; mutation: remove the edge → the reads-match detector names it
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none for the edge; the changed upstream hash may mark `ga_panchanga` stale: confirm in the review (REVIEW item)
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (needs review)
- **Question for SS:** Which asset should `bg_panchanga` depend on: `bg_ephemeris_engine` (code shows swisseph) or `bg_ephemeris` (ledger)?

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `panchang_engine/serialize.py` for any composed text column; declare `[]` expected (numeric/label service output) after reading the service module
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `call_panchanga_service.ts`; CF-04
- **Change:** per CF-04: declare `density_contract` where the module paginates or facets, after the applicability ruling
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 + N-22 applicability
- **Question for SS:** Does Dens apply to this reference table at all (it carries no verification tier)?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* the registry edge
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 1 module

## 5 · Semantic fingerprint contract (for E5.5)

No table. Contract: for a pinned `(instant, lat, lon, tz_offset)` the five angas, timing windows and nine graha states are identical across rebuilds of the engine; the probe fixture is the fingerprint.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the engine behind the service, its Lahiri default and the `panchanga_instant`/`panchanga_day` interfaces.
- **Carriage check chosen (T4 §4.1; one only):** D3 (a second-route recomputation of tithi/vāra).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Edge target: `bg_ephemeris_engine` or `bg_ephemeris`?
