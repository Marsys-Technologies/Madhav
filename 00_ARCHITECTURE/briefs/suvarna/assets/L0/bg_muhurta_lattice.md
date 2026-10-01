---
asset_id: bg_muhurta_lattice
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
ledger_gap_ids: [bg_muhurta_lattice-Build.completion, bg_muhurta_lattice-Earn.build_record, bg_muhurta_lattice-Cost.baseline, bg_muhurta_lattice-Dens.served, bg_muhurta_lattice-Carr.detector]
---
# bg_muhurta_lattice — Muhūrta boundary/factor lattice (173,219 rows; rolling ~5-year horizon)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Global chart-independent muhūrta factor lattice: Agnivāsa states, combination-yoga spans (Sarvārtha-siddhi, Amṛta-siddhi, Ravi/Guru-Puṣya, Tripuṣkara/Dvipuṣkara, Siddha-yoga, Bhadra, Pañchaka), kālam periods, ghaṭīs and more, nine factor families, all computed by REUSING `panchang_engine` wholesale (`platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py:1-30`). **The horizon is rolling**: forward end = `today + 5y`, computed at run time (`:95-118,149,167-178`); the writer deletes nothing, so rows only accumulate, which is why live 173,219 exceeds the registry floor 164,575 by 8,644 (floor recorded earlier; the cause is the advancing horizon by reading, not verified). ON CONFLICT (factor_family, factor_key, start_utc) upsert (`:939-951`). Global but reference-location bound (T2 §4.4, L317). No declared dependents (census 0/0) although 14 non-test files reference the table; served by `query_muhurta_lattice.ts`, `query_sky_calendar.ts`, `index.ts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:854` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py:818`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_muhurta_lattice`; count_sql tables: `bg_muhurta_lattice` | census CEN-R |
| live rows / floor | 173219 / 164,575 (Δ +8644) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_muhurta_lattice`: 14 non-test py/ts/tsx files reference it (8 outside brahmagyan/ and bg_*.py writers): `tool_name_bridge.ts`, `producer_editorial_review.ts`, `source_query_availability.ts`, `elect.ts`, `kala_ritual_resonance.ts` +3 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_muhurta_lattice.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_muhurta_lattice.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record says rows_written=0 against live=173219 (global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 173219/173219 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_muhurta_lattice (bg_muhurta_lattice.py:939)); Vocab.identity (declared key (factor_family, factor_key, start_utc): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (3 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_muhurta_lattice.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_muhurta_lattice-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record says rows_written=0 against live=173219 / required: the Build gate's claim |
| bg_muhurta_lattice-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_muhurta_lattice-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_muhurta_lattice-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 3 module(s): index.ts, query_muhurta_lattice.ts, query_sky_calendar.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_muhurta_lattice-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — every applicable cell PASS except the changed-rows `rows_written = 0` reading (CF-01) and the Dens question. The wall-clock dependence of the content is a fingerprint design point, not a defect.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: converged rerun reports 0 changed rows

- **Answers:** census `Build.completion` FAIL ("rows_written=0 against live=…"); CF-01
- **Change:** apply CF-01 option A (or B after the ruling): the writer states the `ON CONFLICT … DO UPDATE` convention at `:115`; declaration + detector rule
- **Files / declaration / migration:** `platform/scripts/governance/asset_census.py` (Build.completion) + the asset’s declarations entry; option B instead edits the seed function’s returned counts
- **Failing-first test and mutation:** see CF-01
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** A: none. B: needs production rebuild of this asset (idempotent, no data change)
- **Gate it moves:** Build (completion)
- **Fix class:** detector/tooling (A) or writer code (B); **buildable before J1:** tier-dependent: T4 §4.2 check 6 wording
- **Question for SS:** CF-01: is a converged-rerun `rows_written = 0` on a declared changed-rows writer a PASS?

### FD-2 · Fingerprint contract for a rolling horizon

- **Answers:** Track A §5 (semantic fingerprint for E5.5); no census cell
- **Change:** a rebuild on a later date legitimately adds rows beyond the old horizon, so the fingerprint must be taken over a FIXED as-of window (`start_utc` within the intersection of the two runs’ horizons), not the whole table. Record the as-of date in the rebuild impact statement.
- **Files / declaration / migration:** the brief’s §5 contract and the B.L0 fingerprint query (no asset file changes)
- **Failing-first test and mutation:** a test that two builds one day apart have identical fingerprints over the shared window; mutation: include rows beyond the window → mismatch
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Build (rebuild correctness; E5.5)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Carr detector — D3 second route for sampled spans

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** recompute a stratified sample of Agnivāsa/Bhadra/combination-yoga spans from `ephemeris_daily` (Sun/Moon longitudes → tithi, nakshatra, vāra) by interpolation within a declared tolerance and compare the span edges; because the writer reuses `panchang_engine` wholesale, a rerun through the same engine is reproduction only and is labelled so.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_muhurta_lattice.py`, `panchang_engine.rich_topics` for any composed text column; declare `[]` if the `detail` JSON carries labels and numbers only; read `compute_vasa_family` output first
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 3 modules: `index.ts`, `query_muhurta_lattice.ts`, `query_sky_calendar.ts`; CF-04
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
- **CF-01** — Build.completion for converged reruns (rows_written = changed rows, not rows present). *This asset:* rows_written = 0 on a converged rerun
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 164,575 vs live 173,219 (optional refresh; information only)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D3 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 3 modules

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(factor_family, factor_key, start_utc)` (census, 0 duplicates). Semantic fingerprint over the fixed as-of window `(factor_family, factor_key, start_utc, end_utc, detail)`; volatile: surrogate id, `computed_at`/`created_at`. Rolling horizon: see FD-2.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the nine factor families and their definitions inherited from `panchang_engine`; chart-independence; the reference-location binding disclosed in T2 §4.4.
- **Carriage check chosen (T4 §4.1; one only):** D3 (a second route for sampled span edges; same-engine reruns labelled as reproduction).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Does the lattice's floor follow the achieved count (a refresh) or stay a historical figure? (information only)
