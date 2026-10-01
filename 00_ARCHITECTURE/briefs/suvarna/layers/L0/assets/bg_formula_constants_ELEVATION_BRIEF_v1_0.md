---
asset_id: bg_formula_constants
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
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-21, TI-L0-22, TI-L0-25, TI-L0-27]
ledger_gap_ids: [bg_formula_constants-Idem.pattern, bg_formula_constants-Earn.build_record, bg_formula_constants-Cost.baseline, bg_formula_constants-Dens.served, bg_formula_constants-Carr.detector, bg_formula_constants-Build.history, bg_formula_constants-Build.completion]
---
# bg_formula_constants — Canonical formula-constants registry (17 rows; 10 seeded by the writer, 7 by migrations)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Registry description: 'Canonical formula constants registry — combustion orbs, obstruction thresholds, dignity scores, house weights, attention budget, and calibration constants'. The writer upserts the 10 constants in `CONSTANTS` (`platform/python-sidecar/brahmagyan/l0_formula_constants.py:26-205`; ON CONFLICT (constant_id) DO UPDATE at `:238-262`); the table holds 17 because `platform/supabase/migrations/400_mimamsa_p6_schema.sql:68` and `424_ba_lel_r2_2_calibration_state_persistence.sql:30` insert further constants. Classes: 1 `classical` (combustion_orbs), 8 `native_judgment` and `calibratable = true`, 1 `engineering` (holdout_partition) among the writer-seeded ten. `data_disposition = RETAINED_AS_CAPITAL`. Declared dependents: `mi_gunanaka`, `mi_pariksha`, `mi_pramana` (census direct 3 / transitive 7); `consumer_assets` inside the rows also names `ga_condition`, `ka_vighnakara`, `ph_sodhana`, `ph_nimitta`, `ph_pramana`, `mi_outcome`, `assess_*` tools. **Rebuild consequence:** the upsert overwrites `value_jsonb` and `bounds` of the ten seeded constants with the seed literals, including the 8 calibratable ones. No code path that writes a calibrated value back was found (`grep 'UPDATE brahma_formula_constants'` over python-sidecar, platform/src, platform-mcp/src: none), so the exposure is latent: any hand or registry tuning of those 8 values would be reverted by a rebuild.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:768` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_formula_constants.py:22`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_formula_constants`; count_sql tables: `brahma_formula_constants` | census CEN-R |
| live rows / floor | 17 / 17 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 3 / transitive 7 (every layer); named: `mi_gunanaka`, `mi_pariksha`, `mi_pramana` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_formula_constants`: 11 non-test py/ts/tsx files reference it (8 outside brahmagyan/ and bg_*.py writers): `__init__.py`, `mi_pramana.py`, `mi_gunanaka.py`, `mi_pariksha.py`, `lel_calibration.py` +3 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_formula_constants.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 10182981 complete/skip_no_delta (2026-09-07) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_formula_constants.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=10 disagrees with live=17 (count_sql over the target table; global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 10182981 complete/skip_no_delta (2026-09-07) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_formula_constants (brahmagyan/l0_formula_…); Vocab.identity (declared key (constant_id): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (6 executed run(s) of 7 build_run_assets row(s), scope(s): asset_set, layer, last executed 2026-09-07); Build.registered (@register in bg_formula_constants.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_formula_constants-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_formula_constants-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_formula_constants-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_formula_constants-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 1 module(s): query_formula_constants.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_formula_constants-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_formula_constants-Build.history | Build | history | CF-10: a record of past errors/aborts; the latest run completed \| ledger: measured: latest run complete, but 0 error(s) and 1 abort(s) on record. / required: the Build gate's claim |
| bg_formula_constants-Build.completion | Build | real (T4 §4.2 check 6) | see the fix design \| ledger: measured: build record rows_written=10 disagrees with live=17 (count_sql over the target table; global) / required: the Build gate's claim |
| census: Ldgr (no reading) | Ldgr | detector | no recognised citation column on the target table; CF-08 |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |

## 3 · Disposition

**keep (P)** — the table is retained capital with live consumers; the open items are build-record attribution (CF-02: 10 written vs 17 present) and the rebuild-revert hazard, neither of which changes the data today.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: scope count_sql to the ten writer rows

- **Answers:** census `Build.completion` FAIL (10 vs 17); ledger `bg_formula_constants-Build.completion`; CF-02
- **Change:** decided (SS 2026-10-01, Q8): scope the asset’s `count_sql` to the ten writer-seeded constants (`constant_id IN (…)`); the 7 migration-seeded rows (migrations 400, 424) are not this asset’s producer output.
- **Files / declaration / migration:** registry row (`count_sql`) via a surgical migration + `asset_registry_seed.ts` literal
- **Failing-first test and mutation:** failing-first: `rows_written` of a rebuild (10 changed or 0 on a converged rerun) equals the scoped count_sql; mutation: delete one seeded constant → count and integrity fail
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none for the registry scope
- **Gate it moves:** Build (completion), Earn (count_sql scope)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent; the multi-producer vocabulary is tier-dependent (TGH-T2-05)
- **Decision:** ANSWERED by SS 2026-10-01 (Q8): L0 holds seeds only; calibrated values belong to L5 storage later and the L0 upsert must never overwrite them; scope `count_sql` to the ten writer rows.

### FD-2 · Seed-only L0: the upsert must never overwrite a calibrated value

- **Answers:** no census cell and no ledger row (no detector); read from `l0_formula_constants.py:238-262` and the `calibratable` flags in `CONSTANTS`; N-29 (destructive operations need a rebuild plan, a serving guard and a recorded fingerprint)
- **Change:** decided (SS 2026-10-01, Q8): L0 holds seeds only; calibrated values belong to L5 storage later and the L0 upsert must never overwrite them. Make the upsert seed-once for the 8 calibratable constants (`DO NOTHING`, or `DO UPDATE` only where the live value still equals the previous seed) and test it; the pre-rebuild fingerprint of calibratable rows goes in the B.L0 impact statement.
- **Files / declaration / migration:** `brahmagyan/l0_formula_constants.py` (ON CONFLICT clause) and a test next to the writer
- **Failing-first test and mutation:** failing-first: set a calibratable constant to a non-seed value in a fixture, rebuild, assert the value survives; mutation: revert the guard → the test fails
- **Output change:** none on first install; a rebuild no longer reverts calibrated values
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none to land the guard (it only changes what a future rebuild does); the fingerprint check belongs to the B.L0 impact statement.
- **Gate it moves:** Build (rebuild correctness)
- **Fix class:** writer code; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q8): L0 holds seeds only; calibrated values belong to L5 storage later and the L0 upsert must never overwrite them; scope `count_sql` to the ten writer rows.

### FD-3 · Carr detector — D1 on the classical row and ratification check on the others

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** D1 applies to `combustion_orbs` (class classical, cites Sārāvalī ch.6 / BPHS ch.3; after the Q15 consolidation it references `bg_combustion_orbs`); the 8 native_judgment and the engineering row are ratified judgments and get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, SS Q13, PROVISIONAL until the J1 review).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Ldgr: make the source column readable

- **Answers:** census `Ldgr.source_presence` has no reading; CF-08
- **Change:** declare that the source of each row is carried in `citation_or_ratification` (the table’s source column) so the inspector can read it; if the table has no source column the gap is real and is an output change (added by migration + writer)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (`carriage`) and, only if no column exists, the writer + a migration
- **Failing-first test and mutation:** inspector reads PASS/FAIL on the declared column; a blank source must read FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration); a data fix would be a separate design
- **Gate it moves:** Ldgr (no reading → PASS/FAIL)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source is undefined in the gate map)

### FD-5 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_formula_constants.py` for any composed text column; declare `[]` expected (values and ratification strings are literals)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-6 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_formula_constants.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### FD-7 · One authority for combustion orbs (Track I consolidation)

- **Answers:** SS Q15; TI-L0-22; see the `bg_dignity_reference` brief
- **Change:** decided (SS 2026-10-01, Q15): `bg_combustion_orbs` holds the values; replace the `combustion_orbs` constant’s `value_jsonb` by a reference to it and repoint the consumers `ga_condition`, `ka_vighnakara`, `ph_sodhana`.
- **Files / declaration / migration:** `brahmagyan/l0_formula_constants.py:28-48`, the three consumers, a parity test until the consolidation lands
- **Failing-first test and mutation:** failing-first: the three consumers read the orbs from `bg_combustion_orbs`; a test that no second copy of the values exists; mutation: reintroduce a literal → test fails
- **Output change:** the `combustion_orbs` constant becomes a reference
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild of bg_formula_constants after the reference lands (one constant changes representation)
- **Gate it moves:** Carr (single authority), Vocab (rule 6)
- **Fix class:** writer code; **buildable before J1:** tier-independent (decided)

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* 10 written vs 17 present; two producers
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 for the classical row only
- **CF-08** — Ldgr: assets with no recognised citation column (16 "no reading"). *This asset:* `citation_or_ratification`
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 1 module
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 abort on record; latest run complete
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* upsert, no DELETE found; 7 further rows are migration-seeded and must not be pruned

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `constant_id` (census, 0 duplicates). Fingerprint over `(constant_id, value_jsonb, class, consumer_assets, calibratable, bounds, version)` as canonical JSON; volatile: `created_at`. The semantic fingerprint of the calibratable rows is the one the rebuild-revert guard records.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 17 constants with their classes, bounds and ratification strings; the seed-once behaviour for calibratable values (to be made explicit).
- **Carriage check chosen (T4 §4.1; one only):** D1 on the classical row (`combustion_orbs`, which after the Q15 consolidation references `bg_combustion_orbs`); the native-judgment and engineering rows are ratified judgments: check-level N/A by cause `ratified_judgment` from a declared fact (R).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q8): L0 holds seeds only; calibrated values belong to L5 storage later and the L0 upsert must never overwrite them; scope `count_sql` to the ten writer rows.
2. CF-02: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch. ANSWERED by SS 2026-10-01 (Q19): scope `count_sql` to the primary table and declare the asset multi-table.
3. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
4. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
5. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.
6. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-21, TI-L0-22, TI-L0-25, TI-L0-27.
