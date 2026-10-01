---
asset_id: bg_remedies
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
disposition: "enrich (E)"
disposition_proposal_approver: "Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)"
decisions_applied: "SS answers to INDEX section 7, 2026-10-01 (items marked R are PROVISIONAL until the J1 review); disposition accepted as proposed"
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-09, TI-L0-13]
ledger_gap_ids: [bg_remedies-Idem.pattern, bg_remedies-Earn.build_record, bg_remedies-Cost.baseline, bg_remedies-Dens.served, bg_remedies-Carr.detector, bg_remedies-Build.history]
---
# bg_remedies — Classical remedy corpus (341 rows)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

Registry description: 'Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral'. `brahma_remedy_corpus`, 341 rows, built from hardcoded sources in `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py` (a 108-row planet matrix, 102 doṣa remedies, 54 legacy rows, 27 nakshatra-mantra rows, plus a corpus sweep that stores ≤ 400-character slices of source chunks via `l0_remedy_loader.py`; ON CONFLICT upserts at `l0_remedy_corpus.py:3462`, `l0_remedy_loader.py:188`; deletes at `:3551` and loader `:274`), zero LLM. Depends on `bg_texts`; the registry declares 0 dependents although 20 non-test files reference `brahma_remedy_corpus` (a declared-vs-actual gap). **Provenance (layer instance CH-05):** 341/341 carry `source_canonical_id`; 52 resolve exactly to a `text` ontology row; 204 more resolve case-insensitively (`BPHS` vs `bphs`); 85 do not (`classical_tradition` ×80, Tajaka ×3, nadi_navamsa_patel ×1, bphs_jaimini ×1), so 289 do not resolve exactly. **Composed prose:** the declarations record that `prescription_text` (108 + 27 rows) and `charity_action` are composed by f-string from structured data (`l0_remedy_corpus.py:247-424,309,2236`), so the Narr gate applies. The only L0 table with a tier-like column (`cost_tier`, a cost tier, not a verification tier).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:300` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_remedies.py:42`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_remedy_corpus`; count_sql tables: `brahma_remedy_corpus` | census CEN-R |
| live rows / floor | 341 / 341 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_texts` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 0 / transitive 0 (every layer) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_remedy_corpus`: 20 non-test py/ts/tsx files reference it (15 outside brahmagyan/ and bg_*.py writers): `bo_upaya.py`, `route.ts`, `route.ts`, `route.ts`, `coverage_matrix.ts` +10 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_remedy_corpus.ts`, `register_d7_channel.ts`, `register_gochara_windows.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_remedy_corpus.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 21df3b6a complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = ['prescription_text', 'charity_action'] (declared) |

**PASS cells (compact):** Ldgr.source_presence (source_citation populated on 341/341 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): brahma_remedy_corpus (brahmagyan/l0_remedy_corpu…); Vocab.identity (declared key (remedy_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (2 executed run(s) of 3 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.registered (@register in bg_remedies.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_remedies-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_remedies-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_remedies-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_remedies-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 1 module(s): query_remedy_corpus.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_remedies-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_remedies-Build.history | Build | history | 1 abort on record, 0 errors; latest run complete; CF-10 \| ledger: measured: latest run complete, but 0 error(s) and 1 abort(s) on record. / required: the Build gate's claim |
| layer instance CH-05 / Q-05 | Ldgr (qualification), Vocab | real | 289 of 341 `source_canonical_id` do not resolve exactly (204 case-only, 85 not even case-folded); CF-09 |
| layer instance Q-05 | Ldgr (qualification) | real (decided SS Q3: token not accepted; state `unsourced`) | 80 rows cite `classical_tradition` (`l0_remedy_corpus.py:263,507,526,…`); CF-11 |
| declarations `prose_fields` | Narr, Null | real (test absent) | `prescription_text` and `charity_action` are composed by f-string; no fidelity test exists in the saved census (Narr registered at rev 5) |

## 3 · Disposition

**enrich (E)** — agreed with the carried E for the normalisation of the 289 source ids (additive, no row removed); the `classical_tradition` rows get the explicit state `unsourced` (token not accepted as provenance, SS 2026-10-01); the composed prose needs its fidelity test. Output changes need SS.

Approver under Track A brief §10: **Steward (G16) for the disposition; the output changes it names need SS (Track A §10, R5)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Normalise the source ids at the authority (289 → predicted)

- **Answers:** layer instance CH-05; ledger `bg_ontology-G08`; CF-09
- **Change:** do not edit the 341 rows’ meaning: resolve `source_canonical_id` through the normalisation declared once at the authority (CF-09 b), so the 204 case-only ids resolve; the 85 that do not resolve split into 80 `classical_tradition` (explicit state, next fix) and 5 whose texts are missing from the ontology `text` class (Tajaka ×3, nadi_navamsa_patel, bphs_jaimini: resolved by the `text` reconciliation in bg_ontology). Predicted unresolved count after both: 80 (the tradition rows), stated before the change. **Decided (SS 2026-10-01, Q4, follows normalisation at the authority): resolve at read time through the authority’s rule; no stored rewrite unless REVIEW to SS.** After normalisation the predicted unresolved count is 80 (the `unsourced` rows), not 0, because those rows carry no source.
- **Files / declaration / migration:** `brahmagyan/l0_remedy_corpus.py` / the resolver at read time; depends on the ontology change
- **Failing-first test and mutation:** failing-first: unresolved count 289 → 80 after normalisation + text reconciliation, → 0 only if the 80 are given the explicit state; mutation: break the rule → the count moves
- **Output change:** none
- **Blast radius:** a read-time resolution change: no stored row changes; the same readers (listed in the attribution-state fix) see resolved source ids where they used to see unresolved ones.
- **Rebuild:** needs production rebuild of bg_remedies only if the stored ids are rewritten; a read-time resolver needs none
- **Gate it moves:** Ldgr (qualification), Vocab (rule 3)
- **Fix class:** data (output change) or writer code; **buildable before J1:** tier-dependent: TGH-T2-12
- **Decision:** ANSWERED by SS 2026-10-01 (follows Q4, normalisation at the authority): resolve source ids through the authority's normalisation at read time; no stored rewrite unless REVIEW to SS. Not separately asked.

### FD-2 · Explicit attribution state `sourced | unsourced | refuted`

- **Answers:** layer instance Q-05; CF-11
- **Change:** decided (SS 2026-10-01, Q3): the token is not accepted as provenance (B.3): add `attribution_state` ∈ `sourced | unsourced | refuted`; the 80 `classical_tradition` rows read `unsourced`; neither `unsourced` nor `refuted` is a PASS. No citation is replaced; the 80 largest instance of the policy documented in `l0_doshas.py:18-21`.
- **Files / declaration / migration:** a migration (additive column) + `l0_remedy_corpus.py`
- **Failing-first test and mutation:** count of `unsourced` rows = 80, citations unchanged
- **Output change:** one additive column
- **Blast radius:** the rebuild deletes and re-inserts the 341 corpus rows (`l0_remedy_corpus.py:3551`, loader `:274`); `remedy_id` is the census key. Readers outside the L0 writers (14 non-test files incl.): L2 `bo_upaya.py`, three API routes, MCP `remedy_tools.ts`, `upaya.ts`, `ritual.ts`, `register_gochara_windows.ts`, `kala_ritual_resonance.ts`, `coverage_matrix.ts`.
- **Rebuild:** needs production rebuild: bg_remedies (after the migration)
- **Gate it moves:** Ldgr (qualification), Carr
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state
- **Decision:** ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.

### FD-3 · Narr golden tests for the composed remedy text

- **Answers:** declarations `prose_fields = [prescription_text, charity_action]`; Narr.* (rev 5)
- **Change:** for each f-string family (mantra, gemstone, charity, vrata, puja, yantra, homa, behavioral, japa at `l0_remedy_corpus.py:247-424`; the nakshatra-mantra family at `:2236`), a golden test that the text restates the row’s structured fields (item, day, deity, count) and does not state a value the row lacks; `Null.blank_rows`: no blank string stands in for NULL.
- **Files / declaration / migration:** a test next to the seed module; the writer is unchanged
- **Failing-first test and mutation:** golden-value test per family; mutation: change the f-string template → the golden fails
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference.
- **Rebuild:** none (test only)
- **Gate it moves:** Narr (fidelity_test), Null
- **Fix class:** writer code (test only); **buildable before J1:** tier-independent (N.7 item 5)

### FD-4 · Carr detector — D1 on the sourced rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for rows with `source_canonical_id` resolving to a corpus text, test the remedy’s anchor terms against the cited chunk; hardcoded rows citing `classical_tradition` are outside D1 (the explicit state marks them).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 1 module: `query_remedy_corpus.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 0 / transitive 0 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* the 289 unresolved source ids
- **CF-11** — `classical_tradition` is not provenance: explicit attribution state `sourced | unsourced | refuted` (no invented citations). *This asset:* 80 tradition-rooted rows
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 1 module
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 abort; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `remedy_id` (census, 0 duplicates). Fingerprint over `(remedy_id, remedy_type, source_canonical_id, prescription_text, charity_action, …)`; volatile: `created_at`, the corpus sweep’s chunk slices if they embed build-time ids.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 341 remedies as authored, their `remedy_type` vocabulary and the hardcoded-source discipline (zero LLM).
- **Carriage check chosen (T4 §4.1; one only):** D1 (sourced rows); tradition-rooted rows are explicitly outside it.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (follows Q4, normalisation at the authority): resolve source ids through the authority's normalisation at read time; no stored rewrite unless REVIEW to SS. Not separately asked.
2. ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.
3. CF-09: ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
4. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
5. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
6. CF-10: ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-09, TI-L0-13.
