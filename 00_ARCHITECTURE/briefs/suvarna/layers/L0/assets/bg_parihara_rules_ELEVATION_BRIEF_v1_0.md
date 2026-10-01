---
asset_id: bg_parihara_rules
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
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-07, TI-L0-25]
ledger_gap_ids: [bg_parihara_rules-Earn.build_record, bg_parihara_rules-Cost.baseline, bg_parihara_rules-Count.floor, bg_parihara_rules-Complete.depth, bg_parihara_rules-Dens.served, bg_parihara_rules-Carr.detector, bg_parihara_rules-Build.history]
---
# bg_parihara_rules — Parihāra rule graph and muhūrta factor census (3 tables, 440 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Registry description: 'Global chart-independent parihāra (doṣa-cancellation) graph, per-activity muhūrta factor-quality rules, and the Muhūrta Factor Census + corpus-gap register; directly queries `brahma_dosha_catalog` and materializes `panchang_engine.shastra_tables.EVENT_TABLES`'. Three tables: `bg_parihara_rules` 60, `bg_muhurta_activity_rules` 329, `bg_muhurta_factor_census` 51 (= 440), upserted by `platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py:623,653,675`. Depends on `bg_doshas` and `bg_texts`; no declared dependents (census 0/0); read by `query_parihara_graph.ts`. **Floor 449 against live 440 (Δ −9) is a stale registry floor, not lost data:** migration 644 set 449 over 61 + 329 + 59 rows; migration 703 (applied 2026-09-06) deleted 9 orphans (1 + 8) and re-pinned the integrity check but left the floor (layer instance CH-04). That migration is also the documented instance of upsert accretion: the writer is upsert-only and did not remove the orphans.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:873` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py:555`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_parihara_rules`; count_sql tables: `bg_parihara_rules`, `bg_muhurta_activity_rules`, `bg_muhurta_factor_census` | census CEN-R |
| live rows / floor | 440 / 449 (Δ -9) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_doshas`, `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_muhurta_activity_rules`: 9 non-test py/ts/tsx files reference it (6 outside brahmagyan/ and bg_*.py writers): `tool_name_bridge.ts`, `source_query_availability.ts`, `elect.ts`, `ritual.ts`, `kala_ritual_resonance.ts` +1; `bg_muhurta_factor_census`: 9 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `tool_name_bridge.ts`, `source_query_availability.ts`, `kala_lattice_query.ts`, `kala_sky_pattern.ts`; `bg_parihara_rules`: 10 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `tool_name_bridge.ts`, `producer_editorial_review.ts`, `source_query_availability.ts`, `elect.ts`, `kala_lattice_query.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_parihara_graph.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fe14f22a complete/build (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_parihara_graph.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 0 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-06): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run fe14f22a complete/build (2026-09-06) |
| Count (information, D3) | Count.floor | FAIL | count_sql total=440, floor=449, delta=-9 |
| Complete (information, D3) | Complete.depth | PARTIAL | 60 rows, 14 cols; fully populated 12; NEVER populated ['extraction_context'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 60/60 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_parihara_rules (bg_parihara_rules.py:623), bg…); Vocab.identity (declared key (dosha_canonical_id, cancellation_index): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (4 executed run(s) of 4 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.registered (@register in bg_parihara_rules.py; registry agrees); Build.target †.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_parihara_rules-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_parihara_rules-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_parihara_rules-Count.floor | Count | real (registry) / information (D3) | live 440 vs floor 449; stale floor, cause established (migration 703); CF-03 \| ledger: measured: live=440, floor=449, delta=-9 / required: the Count gate's claim |
| bg_parihara_rules-Complete.depth | Complete | information | `extraction_context` never populated (60 rows, 14 cols) \| ledger: measured: 60 rows, 14 cols; fully populated 12; NEVER populated ['extraction_context'] / required: the Complete gate's claim |
| bg_parihara_rules-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 2 module(s): index.ts, query_parihara_graph.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_parihara_rules-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_parihara_rules-Build.history | Build | history | 3 errors (`post-write integrity check failed`, latest 2026-09-06) and 0 aborts; latest run complete; CF-10 \| ledger: measured: latest run complete, but 3 error(s) and 0 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |
| layer instance CH-04 / §5.2 | Idem | real (a PASS that does not test accretion) | the upsert-only writer left 9 orphans that migration 703 removed by hand; CF-12 |

## 3 · Disposition

**keep (P)** — no content defect; the registry floor is stale and the writer's idempotency claim is untested against orphans. Both fixes are small and neither changes output.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Registry floor 449 → 440

- **Answers:** census `Count.floor` FAIL (information); ledger `bg_parihara_rules-Count.floor`; layer instance C-5/C-14; CF-03
- **Change:** set `target_floor = 440` (the achieved count after migration 703; CLAUDE.md §N.4: floor = achieved count, never fabricate rows to hit a number).
- **Files / declaration / migration:** a surgical migration (`UPDATE asset_registry SET target_floor = 440 WHERE asset_id = 'bg_parihara_rules' AND target_floor = 449`, with an in-migration check) + `asset_registry_seed.ts`; number = max+1 across all origin heads and both migration directories at execution time
- **Failing-first test and mutation:** failing-first: `Count.floor` reads PASS; mutation: restore 449 → FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none
- **Gate it moves:** Count (information); removes the only FAIL outside Build/Dens
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-2 · Orphan census and prune for the three tables

- **Answers:** layer instance CH-04; CF-12
- **Change:** add the orphan census of CF-12 (dry-run produced keys vs live keys) for the three tables, and give the writer a prune scoped to its own natural keys: `(dosha_canonical_id, cancellation_index)` for the rule graph, and the keys of the two sibling tables. Live rows are clean today, so the prune changes nothing now and prevents a repeat.
- **Files / declaration / migration:** `pipeline/orchestrator/writers/bg_parihara_rules.py` (after the upserts at `:623,653,675`) + a test
- **Failing-first test and mutation:** failing-first: a fixture with one extra row in each table → rebuild removes it; mutation: broaden the prune to the whole table → the sibling-table test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none to land; exercised by the next rebuild
- **Gate it moves:** Idem (accretion)
- **Fix class:** writer code; **buildable before J1:** tier-dependent: TGH-T3-18 (meaning of Idem for upsert writers)

### FD-3 · Carr detector — D1 on the parihāra rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** each rule cites a source (`source_citation` 60/60): resolve to the corpus and test the doṣa/cancellation anchor terms; rules materialised from `panchang_engine.shastra_tables.EVENT_TABLES` are checked against that table’s own entries (referential D1).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `bg_parihara_rules.py` for any composed text column; declare `[]` or the composed column after reading the writer (`extraction_context` is never populated; check for composed rule text)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `index.ts`, `query_parihara_graph.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor 449 → 440
- **CF-12** — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion). *This asset:* the documented orphan instance
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 2 modules
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 3 errors, 0 aborts; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(dosha_canonical_id, cancellation_index)` for `bg_parihara_rules` (census, 0 duplicates); the other two tables have their own keys (read at design time). Upsert; volatile: `id`, `build_id`, `computed_at` (dark columns in the saved reach record).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 60 cancellation rules, 329 per-activity muhūrta rules and 51 census rows as they stand after migration 703.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence, plus referential D1 against `EVENT_TABLES`).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. CF-03: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.
2. CF-12: ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.
3. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
4. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
5. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-07, TI-L0-25.
