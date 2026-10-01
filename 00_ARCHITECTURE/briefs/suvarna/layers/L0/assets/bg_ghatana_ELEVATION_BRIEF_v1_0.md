---
asset_id: bg_ghatana
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
ledger_gap_ids: [bg_ghatana-Idem.pattern, bg_ghatana-Earn.build_record, bg_ghatana-Cost.baseline, bg_ghatana-Carr.detector]
---
# bg_ghatana — Life-event and electional-activity ontology (27 + 12 classes)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Registry description: 'Global life-event + electional-activity ontology — 27 life-event classes (`brahma_event_ontology`) and 12 electional activity classes (`brahma_activity_ontology`), including DR-13 temporal-shape and evidence fields'. ON CONFLICT upserts at `platform/python-sidecar/brahmagyan/l0_ghatana.py:878,923`; 39 rows. `data_disposition = RETAINED_AS_CAPITAL`. This is the L0 vocabulary the life-event switch rests on (T2 §9.2 ON row names 'L0 event vocabulary'): neither table carries a per-subject column. Widely read: declared dependents `bg_class_lifetime_counts`, `ka_avadhi`, `ka_taranga`, `ka_yojaka`, `mi_jivanaghatana`, `mi_pramana` (census direct 6 / transitive 33); modules in L4, L5 and platform-mcp read it. The saved reach record shows 13 of 19 built columns not selected by any module (`adjacency`, `base_rate_by_age`, `citations`, `duration_prior`, `kill_switch_criteria`, `matching_rules`, `signature_model` …): information, not a blocker.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:531` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_ghatana.py:21`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_event_ontology`; count_sql tables: `brahma_event_ontology`, `brahma_activity_ontology` | census CEN-R |
| live rows / floor | 39 / 39 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 6 / transitive 33 (every layer); named: `bg_class_lifetime_counts`, `ka_avadhi`, `ka_taranga`, `ka_yojaka`, `mi_jivanaghatana`, `mi_pramana` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_activity_ontology`: 9 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `ph_muhurta.py`, `engine.py`, `route.ts`, `register_p1_synthesis.ts`, `kala_ritual_resonance.ts` +1; `brahma_event_ontology`: 58 non-test py/ts/tsx files reference it (53 outside brahmagyan/ and bg_*.py writers): `ka_yojaka.py`, `bo_pratijna_karyatva.py`, `ph_nimitta.py`, `mi_pramana.py`, `ka_taranga.py` +48 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_prospective_ledger.ts`, `lel_intake_checklist.ts`, `prediction_lifecycle_sweep.ts`, `reading_checklist.ts`, `register_gochara_windows.ts`, `ahead_autofile.ts`, `intervention_filing.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_event_ontology (brahmagyan/l0_ghatana.py:…); Vocab.identity (declared key (event_class_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.exercised (4 executed run(s) of 4 build_run_assets row(s), scope(s): asset_set, layer, last executed 2026-09-04); Build.history; Build.registered (@register in bg_ghatana.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_ghatana-Idem.pattern | Idem | stale | saved census Idem.pattern reads PASS (ON CONFLICT upsert at `l0_ghatana.py:878,923`) \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_ghatana-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_ghatana-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_ghatana-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — every applicable census cell is PASS; the open items are detectors and declarations. Retained capital with six declared and several actual consumers.

Approver under Track A brief §10: **Steward (G16)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr detector — D1 on the `citations` column

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** the `citations` column is built but never selected by a module (dark); where a class cites a source, resolve it to the corpus and test anchor terms; classes with no citation are listed as unattributed, not passed.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-2 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_ghatana.py` for any composed text column; read `l0_ghatana.py` for composed text (`milestone_template`, `matching_rules`, `evidence_requirements`) and declare `[]` or the list
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-3 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `citations` (JSON column; built, dark) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* `citations`
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration; `milestone_template` is a candidate to read first
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert over two tables, no DELETE found

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `event_class_id` (census, 0 duplicates) for `brahma_event_ontology`; the activity table has its own key (to be read at design time). Upsert; fingerprint over all 19 built columns except `created_at` and `version` if surrogate.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 27 + 12 class definitions with their temporal shapes, evidence requirements and kill-switch criteria; the absence of any per-subject column.
- **Carriage check chosen (T4 §4.1; one only):** D1 on the cited classes only.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2
