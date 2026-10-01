---
asset_id: bo_pratijna
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); the edge removal needs SS review (DAG change)"
nirmana_freeze: "t1, 2026-09-09"
ledger_gap_ids: [bo_pratijna-Earn.build_record, bo_pratijna-Cost.baseline, bo_pratijna-Build.history, bo_pratijna-Carr.detector]
---
# bo_pratijna — Promise Register (pratijñā v4.1.0): per-event-class promise and denial grading

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Grades 27 event classes × 5 ayanamshas = 135 rows of `bodha_pratijna` with a v4 scoring engine (`bo_pratijna_v4_engine.py`, PRATIJÑĀ v4.1.0, ruling R22): occurrence [0,1] and condition [0,10] grades from classical significator maps (`bo_pratijna_karyatva.py`) applied to L1 dignity/placement/aspect facts read through `brahmagyan.chart_reader_v4.ChartReaderV4` (`chart_divisionals`, `chart_facts`, `chart_fact_identity`); `grade = round(occurrence × 10, 3)` is kept for the legacy consumers `ph_nimitta`, `ka_taranga`, `ka_yojaka` (`bo_pratijna.py:121-131`), and `varga_confirmation` is a cross-ayanamsha consensus summary. **The v4 engine "never reads `bodha_msr_signals` at all"** (`bo_pratijna.py:133-134`), so `supporting_signal_ids`/`contradicting_signal_ids` are always NULL by disclosed design. `@register("bo_pratijna")` at `bo_pratijna.py:435`, chart delete at `:458`, `ON CONFLICT (chart_id, ayanamsha_id, event_class_id) DO UPDATE` insert (`:216-231`). Declared dependencies `bo_laksana`, `bo_sangati` (and, from migration 1210, `ga_vargas`); the registry description still says "reads bodha_msr_signals + brahma_event_ontology" and the volume formula 22 classes × 5 = 110 (`asset_registry_seed.ts:1657-1672`). Direct dependents (5): `ka_avadhi`, `ka_kshetra`, `ka_taranga`, `ka_yojaka`, `mi_darshana`. Frozen under the t1 definition (2026-09-09). Its 1210 gate preview found it NOT lit-and-fresh ("stale"), which is why the `ph_nimitta → bo_pratijna` edge is held in migration 1211.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1657` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py:435`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_pratijna`; count_sql tables: `bodha_pratijna` | census CEN-R |
| live rows / floor | 135 / 0 (chart 482012f1, count_sql scope) — 135 = 27 event classes × 5 ayanamshas; seed floor 110 (22 classes) is stale, live floor 0 | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_sangati`, `ga_vargas` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 5 / transitive 31; seed-derived closure (post-1210): direct 5 / transitive 31; direct dependents: `ka_avadhi`, `ka_kshetra`, `ka_taranga`, `ka_yojaka`, `mi_darshana` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_pratijna`: 16 non-test py/ts/tsx files reference it (15 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_yojaka.py`, `ph_nimitta.py`, `ka_taranga.py`, `mi_darshana.py`, `ka_avadhi.py`, `stage2_promise.py` +9 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_pratijna.ts`; `density_contract` declared on 1 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_pratijna (bo_pratijna.py:458) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 25 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-06): BLOCKED: upstream dependency(ies) bo_laksana, bo_sangati did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Count (information) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=135) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 11/16 built column(s) (68.8%) selected by 1 capability module(s); dark: ['build_id', 'chart_id', 'condition_grade', 'engine_version', 'occurrence_grade']; depth 100.0% (a capability query rea… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (chart_id, ayanamsha_id, event_class_id): 0 duplicate(s)); Dens.served† (1 module(s): query_pratijna.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=135 = live=135 (count_sql over the target table; chart 482012f1)); Build.exercised (45 executed run(s) of 119 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-0…); Build.dep_liveness; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **PARTIAL** — 3 module(s) reach it by code: L2_bodha/query_pratijna.ts, L4_phala/query_predictive_anchors.ts, platform-mcp/src/tools/register_p1_aliases.ts; a referencing capability declares density_contract but L2_bodha/query_pratijna.ts: no tier column in its served select; Idem.pattern rev 2 reads **PASS**.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| code `bo_pratijna.py:133-134` vs seed `depends_on: ['bo_laksana','bo_sangati','ga_vargas']`; layer instance §3.4 (reads no L2 table) | Build (dag) | real (declared edges not read) | the writer reads no L2 table, yet declares `bo_laksana` and `bo_sangati`. Concrete effect on record: the latest error is `BLOCKED: upstream dependency(ies) bo_laksana, bo_sangati did not complete in this run` (2026-08-06): a build this writer does not need was blocked by upstreams it never reads. Migration 1210 added the one edge the E6 reads-match detector requires (`ga_vargas`, `chart_divisionals`); the over-declaration is the converse and is invisible to that detector. CF-15. |
| seed text `asset_registry_seed.ts:1657-1672` | Complete (information) | real (registry truth) | description ("reads bodha_msr_signals"), `expected_volume_formula` (`EVENT_CLASSES * AYANAMSHAS`, `EVENT_CLASSES: 22`) and `target_floor: 110` describe the retired v3 engine; the code and the live table are 27 × 5 = 135 (`bo_pratijna.py` docstring: "27 event classes"). Census Count.floor reads N/A (floor 0). CF-03. |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | the target table has no recognised citation column in `CITATION_COLUMNS`, so the gate has no reading; the provenance lives in the `derivation` jsonb ledger. Declare the carrying column. CF-08. |
| census cell Dens.served † (offline rev 4 PARTIAL) | Dens | detector (rev 4 PARTIAL) | saved rev-1 PASS (1 module declaring a contract, `query_pratijna.ts:131`); the offline rev-4 scan reads PARTIAL: the contract is declared but "no tier column in its served select". The v4-native `occurrence_grade` and `condition_grade` are dark (not selected) while the legacy `grade` is served. FD-1; CF-04. |
| census: Null/Narr | Null, Narr | detector | `prose_fields` = three jsonb paths declared (`derivation.$.factor_ledger[*].detail`, `…denials[*].reason`, `…connections[*].reason`): the ledger strings are composed by f-string from computed L1 values (`bo_pratijna_v4_engine.py:310`, `:410`, `:425`, `:945`). CF-14. |
| `bo_pratijna-Build.history` | Build (history) | history | latest run complete; 25 errors and 8 aborts on record (latest error 2026-08-06, the BLOCKED cascade above). CF-10. |
| `bo_pratijna-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — a sound v4 engine whose own census cells are clean (completion equals live, idempotent, populated); the real shortfalls are registry truth (stale description, floor, volume formula) and two declared-but-unread edges that cause avoidable build blocking. None changes the asset. The edge removal changes the DAG and the frozen manifest, so it is parked for SS review.

Approver under Track A brief §10: **Steward (G16); the edge removal needs SS review (DAG change)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Remove the two declared-but-unread edges and correct the registry text

- **Answers:** the declared-edges gap and the registry-truth gap; CF-15, CF-03
- **Change:** remove `bo_laksana` and `bo_sangati` from `depends_on` (keep `ga_vargas`), rewrite `english_description`, `expected_volume_formula` and `volume_explanation` to the v4 engine (27 event classes × 5 ayanamshas = 135), set `target_floor` to the achieved count after a build
- **Files / declaration / migration:** one surgical migration (number = max+1 across origin heads at execution time) with an `AND <old value>` guard and an in-migration check, plus the same literals in `platform/scripts/seed/asset_registry_seed.ts:1657-1672`; verify by production structure, never by the runner's report
- **Failing-first test and mutation:** failing-first: the E6 reads-match and an over-declaration check (CF-15) read PASS for the asset and its declared set equals what `ChartReaderV4` reads (chart_facts, chart_divisionals); mutation: re-add `bo_sangati` → the over-declaration check flags it
- **Output change:** none
- **Blast radius:** the DAG: `bo_pratijna` no longer waits for `bo_laksana`/`bo_sangati`; its upstream hash (`compute_upstream_hash` hashes DECLARED deps) changes once; its five direct dependents are unaffected in order. Acyclic by construction (edges only removed)
- **Rebuild:** none for the migration; the next dispatch sees a changed upstream set (one-time rebuild signal)
- **Gate it moves:** Build (dag), Count
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent in content, but a DAG change: needs its own review (Track I's 1210 deliberately scoped to additions)
- **Question for SS:** May a declared edge that the writer provably never reads be removed (the converse of 1210)?

### FD-2 · Let Dens read a tier on the served select

- **Answers:** offline rev-4 Dens PARTIAL; CF-04
- **Change:** select a tier column the table carries (or serve `occurrence_grade`/`condition_grade` with the tier) in `query_pratijna.ts` so the rev-4 detector can establish tier carriage; the contract is already declared (`:131`)
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_pratijna.ts`
- **Failing-first test and mutation:** the rev-4 scan reads PASS; mutation: remove the tier column → PARTIAL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: Dens rule (TGH-T3-26) and N-22

### FD-3 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a graded event class with a known L1 dignity (exaltation sign, naisargika/tatkalika relation with house numbers) → the `factor_ledger[*].detail`, `denials[*].reason` and `connections[*].reason` strings (`bo_pratijna_v4_engine.py:310/410/425/945`) state exactly the sign, house and relation values of the cited L1 facts; the rubric's hand-worked case (`RUNG_P3_HAND_WORKED_v1_0.md`, reproduced by Rung P5) is a ready golden source
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-4 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): re-run the engine on the L1 facts for a stratified sample of event classes and compare occurrence and condition grades to the stored rows (the engine is deterministic and has a hand-worked reproduction); plus resolution of the cited L1 `fact_id`s in the ledger.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* FD-1: two declared edges not read
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* stale description, volume formula and floor
- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-2
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared ledger prose paths
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL (a BLOCKED cascade from edges it does not read)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, event_class_id)` (the writer's own conflict target). Fingerprint: `status`, `grade`, `occurrence_grade`, `condition_grade`, `varga_confirmation` (cross-ayanamsha consensus), the `derivation` ledger with its prose, the engine version (`bo_pratijna_v4.1.0`, part of the contract). **Volatile:** row ids, `build_id`, `computed_at`. `supporting_signal_ids`/`contradicting_signal_ids` are NULL by design. Expected 135 rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the PRATIJÑĀ v4.1.0 grading from L1 through the chart reader, the 5-band occurrence mapping onto the 4-value `status` check, the legacy-scale `grade`.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-4)
- **Opportunities (never blocking):** serve `occurrence_grade`/`condition_grade` (dark); re-point `supporting_signal_ids` once a signal-level reading is wanted (a design choice, the v4 engine disclaims it).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 (applied; Track I) added this row's direct edge(s) `ga_vargas`, so its frozen manifest is stale against the registry fingerprint (1210 header, CONSEQUENCES 1: `assertManifestMatchesRegistryIdentity` throws on any `depends_on` change; its `asset_analysis_accepted` evidence no longer matches). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`ka_avadhi`, `ka_kshetra`, `ka_taranga`, `ka_yojaka`, `mi_darshana`) re-run after it in DAG order; seed-derived transitive closure 31 assets. If FD-1 lands the DAG order changes only by removing waits. Its legacy `grade` is read by `ph_nimitta` (held edge in 1211), `ka_taranga` and `ka_yojaka`.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: may declared edges the writer provably never reads be removed (needs SS review: a DAG change)?
2. CF-03: floor after a coherent rebuild at the achieved count (135), not the stale 110?
3. Is the held `ph_nimitta → bo_pratijna` edge (migration 1211) to wait until this asset is lit and fresh, and does the removal in FD-1 help that?
