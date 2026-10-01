---
asset_id: bg_yogas
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
disposition: "enrich (narrowed after Q20; pending)"
disposition_proposal_approver: "Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-09, TI-L0-31]
ledger_gap_ids: [bg_yogas-Idem.pattern, bg_yogas-Earn.build_record, bg_yogas-Cost.baseline, bg_yogas-Complete.depth, bg_yogas-Dens.served, bg_yogas-Carr.detector, bg_yogas-Build.history]
---
# bg_yogas — Classical yoga catalogue (233 yogas; 784 rows over four tables)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

'Classical yoga definitions — formation rules, significations, classical citations'. `seed_yogas` replaces `brahma_yoga_source_chunks`, `reference_yogas`, `brahma_yoga_catalog` (233) and the 233 `yoga` ontology rows by delete-then-insert (`platform/python-sidecar/brahmagyan/l0_yogas.py:2244-2247`); `formation_text` is a verbatim source clause or, when none exists, a provenance-pointer f-string (`:2140`), `source_citation` a provenance f-string (`:2156`); declarations record `prose_fields = []` (no composed grading). 1 of 233 rows cites `classical_tradition` (`:946`). **Four catalogue columns are never populated:** `bhanga_rules_jsonb`, `partial_formation_threshold`, `strength_formula_ref`, `result_class` (census `Complete.depth`; layer instance §2.3 DP05, L0's half of formation testing). Depends on `bg_ontology` and `bg_texts`; declared dependent `bg_rules` (census direct 1 / transitive 52). Actual readers are far wider and undeclared: `ga_yoga`, `ga_structural_writer`, `bo_laksana`, `routers/yoga_formation_band.py`, L1 modules `get_yoga_firings.ts`, `coverage_matrix.ts` (upper-layer reads of L0 are `bedrock_exempt` in the DAG detector, provisional pending J1). Served by `list_entities.ts` and `query_yoga_catalog.ts`, the CLAUDE.md §N.6 catalog-only surface.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:340` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_yogas.py:23`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_yoga_catalog`; count_sql tables: `brahma_yoga_catalog`, `brahma_ontology`, `reference_yogas`, `brahma_yoga_source_chunks` | census CEN-R |
| live rows / floor | 784 / 784 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ontology`, `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 52 (every layer); named: `bg_rules` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_ontology`: 17 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `parity_check.ts`, `source_query_availability.ts`, `l0_brahmagyan.ts`, `kala_sky_pattern.ts`; `brahma_yoga_catalog`: 14 non-test py/ts/tsx files reference it (10 outside brahmagyan/ and bg_*.py writers): `yoga_formation_band.py`, `bo_laksana.py`, `ga_yoga.py`, `ga_yoga_writer.py`, `ga_structural_writer.py` +5; `brahma_yoga_source_chunks`: 1 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers); `reference_yogas`: 2 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_yoga_catalog.ts`, `get_yoga_firings.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 376c21b7 complete/build (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_yoga_catalog.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-06): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 376c21b7 complete/build (2026-09-06) |
| Complete (information, D3) | Complete.depth | PARTIAL | 233 rows, 19 cols; fully populated 14; NEVER populated ['bhanga_rules_jsonb', 'partial_formation_threshold', 'strength_formula_ref', 'result_class'] |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = [] (declared no generated prose) |

**PASS cells (compact):** Ldgr.source_presence (classical_citations populated on 233/233 rows); Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: brahma_yoga_source_chunks (brahmagyan/l0_yogas.py:22…); Vocab.identity (declared key (canonical_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (4 executed run(s) of 5 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.registered (@register in bg_yogas.py; registry agrees); Build.target †; Count.floor.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_yogas-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_yogas-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_yogas-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_yogas-Complete.depth | Complete | information | columns never populated (D3: information, not a blocker) \| ledger: measured: 233 rows, 19 cols; fully populated 14; NEVER populated ['bhanga_rules_jsonb', 'partial_formation_threshold', 'strength_formula_ref', 'result_class'] / required… |
| bg_yogas-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 2 module(s): list_entities.ts, query_yoga_catalog.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_yogas-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_yogas-Build.history | Build | history | 3 errors (`post-write integrity check failed`, latest 2026-09-06) and 1 abort; latest run complete; CF-10 \| ledger: measured: latest run complete, but 3 error(s) and 1 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| layer instance §1.2 / Q-04 | Ldgr (qualification) | real (decided SS Q3: token not accepted; state `unsourced`) | 1 of 233 yoga rows cites `classical_tradition` (`l0_yogas.py:946`); CF-11 |
| census Complete.depth (information) | Complete | information; real for DP05 | `bhanga_rules_jsonb`, `partial_formation_threshold`, `strength_formula_ref`, `result_class` never populated across 233 rows |

## 3 · Disposition

**enrich (narrowed after Q20; pending)** — SS accepted the disposition (Q10) and then deferred the four DP05 columns (Q20), so the original justification is gone. What remains: an explicit `attribution_state` column on all 233 catalogue rows (one `unsourced`; an added qualified field, T2 E) and declared null reasons for the four empty columns. That is a modest enrichment; if SS reads it as too thin for E, the honest alternative is keep with the same two fixes. Recorded as "enrich pending" for that reason; no change to the fixes either way.

Approver under Track A brief §10: **Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Explicit attribution state `sourced | unsourced | refuted` for the one token row

- **Answers:** layer instance Q-04; CF-11
- **Change:** decided (SS 2026-10-01, Q3): the token is not accepted as provenance: the single `classical_tradition` row reads `unsourced`, the other 232 `sourced`; neither `unsourced` nor `refuted` is a PASS. No citation is replaced.
- **Files / declaration / migration:** a migration (additive column on `brahma_yoga_catalog`) + `l0_yogas.py`
- **Failing-first test and mutation:** count of `unsourced` rows = 1, the other 232 `sourced`
- **Output change:** one additive column
- **Blast radius:** the rebuild deletes and re-inserts `brahma_yoga_source_chunks`, `reference_yogas`, `brahma_yoga_catalog` (233) and the 233 `yoga` rows of `brahma_ontology` in one transaction (`l0_yogas.py:2243-2249`). DB cascades: only `reference_yogas` and `brahma_yoga_source_chunks` reference the catalogue (ON DELETE CASCADE, migrations 178 and 630), both wholly owned by bg_yogas. Readers of the catalogue outside the L0 writers: L1 `ga_yoga.py`, `ga_yoga_writer.py`, `ga_structural_writer.py`, L2 `bo_laksana.py`, `routers/yoga_formation_band.py`, L1 modules `get_yoga_firings.ts`, `coverage_matrix.ts`, `workspaceSummary.ts` (edges undeclared, `bedrock_exempt`). Readers of the ontology rows: `resolve_entity.ts`, `list_entities.ts`. An additive state column leaves canonical ids unchanged, so downstream fact ids citing yoga ids still resolve; `bg_rules` need not be rebuilt for it.
- **Rebuild:** needs production rebuild: bg_yogas (after the migration; global delete-then-insert of four tables)
- **Gate it moves:** Ldgr (qualification), Carr
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state
- **Decision:** ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.

### FD-2 · Declared nulls for the four unpopulated formation columns

- **Answers:** census `Complete.depth`; layer instance §2.3 (DP05)
- **Change:** decided (SS 2026-10-01, Q20): the four DP05 columns are OUT of the first wave unless a source-grounded extraction already exists (none was found); declare each column’s null reason now; populating them is an opportunity.
- **Files / declaration / migration:** `asset_declarations.json` (null reasons)
- **Failing-first test and mutation:** declarations validation; mutation: remove a reason → Null reads NO_DETECTOR
- **Output change:** none
- **Blast radius:** declaration only: no row, id or served field changes; readers of the catalogue (listed above) see no change.
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null; Complete (information)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (decided)
- **Decision:** ANSWERED by SS 2026-10-01 (Q20): the four DP05 columns are out of the first wave unless a source-grounded extraction already exists; an opportunity otherwise.

### FD-3 · Carr detector — D1 on the yoga definitions

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for each yoga with a verse citation, resolve to the chunk and test the yoga’s name and formation anchor terms; the rows whose `formation_text` is the provenance-pointer fallback (`l0_yogas.py:2140`) carry no clause to compare and are reported separately as pointer-only, not as passes.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 1 / transitive 52 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `list_entities.ts`, `query_yoga_catalog.ts` (the §N.6 catalog-only surface: confirm `catalog_only` flags are served); CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 1 / transitive 52 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* the `yoga` ontology rows are co-written here (alias/identity contract, ledger O6)
- **CF-11** — `classical_tradition` is not provenance: explicit attribution state `sourced | unsourced | refuted` (no invented citations). *This asset:* 1 tradition-rooted row
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 2 modules
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 3 errors, 1 abort; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `canonical_id` (census, 0 duplicates) for `brahma_yoga_catalog`; `(entity_class='yoga', canonical_id)` for the ontology rows. Delete-then-insert: fingerprint over `(canonical_id, formation_text, significations, citations)`; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 233 yoga definitions with their formation text and citations; the co-written ontology identities.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence on cited, non-pointer rows).
- **Opportunities (never blocking):** DP05 depth: populate `bhanga_rules_jsonb`, `partial_formation_threshold`, `strength_formula_ref`, `result_class` where extractable (deferred by SS).

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.
2. ANSWERED by SS 2026-10-01 (Q20): the four DP05 columns are out of the first wave unless a source-grounded extraction already exists; an opportunity otherwise.
3. CF-09: ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
4. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
5. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
6. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-09, TI-L0-31.
