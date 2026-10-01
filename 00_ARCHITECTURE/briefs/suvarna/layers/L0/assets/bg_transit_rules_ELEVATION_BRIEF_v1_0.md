---
asset_id: bg_transit_rules
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
track_i_items: [TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-09, TI-L0-10, TI-L0-32]
ledger_gap_ids: [bg_transit_rules-Idem.pattern, bg_transit_rules-Earn.build_record, bg_transit_rules-Cost.baseline, bg_transit_rules-Dens.served, bg_transit_rules-Carr.detector, bg_transit_rules-Build.completion]
---
# bg_transit_rules — Classical Gochara rules (76 rows; 69 writer-seeded + 7 migration-owned)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. SS answered the open questions on 2026-10-01: decisions are recorded in §4 and §7 (items marked (R) are PROVISIONAL until the J1 review).

## 0 · Identity — what the asset is

'76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit' (seed description, `platform/scripts/seed/asset_registry_seed.ts:683`). The writer seeds the engine, rule and moorti tables (`BgTransitRulesWriter`, `…/writers/bg_transit_rules.py:11-44`; `brahmagyan/l0_transit.py:964-1215`): the module’s own volume line says 9 engine + 68 writer-owned rules + 7 migration-owned + 27 moorti (`:19-20`), but the rule list imports as 69 rules (43 favourable + 26 unfavourable) which with the 7 migration rows gives the registry’s 76: the docstring’s 68 is off by one against its own list (or one list rule is not writer-owned; not established); the 7 `double_transit` rows are owned by migration 397 and deliberately outside the writer’s retirement filter (`:985-1010`, `_owned_row_filter`). Retirement is ownership-scoped because `bg_transit_rules.id` is SERIAL and `gochara_resonance_map.source_rule_id` references it (migration 459). **Citation state after the 2026-09 L0 repair, stated in the registry row:** 36 favourable-with-vedha rows carry page-anchored Phaladīpikā Adh. XXVI citations; 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED; **19 rows (18 unfavourable + 1 favourable with no vedha pair) still carry the refuted 'BPHS Ch.29'** and were deliberately not re-cited on an unverified basis; the remaining 15 cite Phaladīpikā Ch.26, Sārāvalī or Jātaka Pārijāta. The recorded `rows_written` of 104 spans three tables (CF-02). Declared dependents `ka_gochara`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_yojaka` and one not identified offline (census direct 6 / transitive 34); 41 non-test files reference `bg_transit_rules`. Served by `query_transit_engine.ts`, `query_transit_vedha.ts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:678` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_transit_rules.py:11`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bg_transit_rules`; count_sql tables: `bg_transit_rules` | census CEN-R |
| live rows / floor | 76 / 76 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | none | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 6 / transitive 34 (every layer); named: `ka_gochara`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_yojaka` (named 5 of 6 direct; the rest not identified offline) | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `bg_transit_rules`: 41 non-test py/ts/tsx files reference it (36 outside brahmagyan/ and bg_*.py writers): `runner.py`, `ka_sangam.py`, `ka_moorti_nirnaya.py`, `ka_vedha_gochara.py`, `step04_apply_verify.py` +31 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `register_p1_reference.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 1 module(s): query_transit_vedha.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=104 disagrees with live=76 (count_sql over the target table; global) |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 440c1ae6 complete/build (2026-09-04) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Ldgr.source_presence (classical_citation populated on 76/76 rows); Idem.pattern † (INSERT … ON CONFLICT into the asset's own table(s) (upsert): bg_transit_rules (brahmagyan/l0_transit.py:938 v…); Vocab.identity (declared key (graha, rule_type, primary_house): 0 duplicate(s)); Build.contract; Build.count_integrity; Build.dag †; Build.exercised (2 executed run(s) of 2 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-04); Build.history; Build.registered (@register in bg_transit_rules.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_transit_rules-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_transit_rules-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_transit_rules-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_transit_rules-Dens.served | Dens | real as measured at rev 1 (Dens applies per SS Q2; offline re-measure in INDEX section 9.1) | CF-04 \| ledger: measured: 2 module(s): query_transit_engine.ts, query_transit_vedha.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_transit_rules-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_transit_rules-Build.completion | Build | real (T4 check 6) with a producer-attribution cause | 104 = 9 engine + 68 rules + 27 moorti rows reported by one writer; live 76 includes 7 migration-owned rows; CF-02 \| ledger: measured: build record rows_written=104 disagrees with live=76 (count_sql over the target table; global) / required: the Build gate's claim |
| census: Null/Narr (declarations) | Null, Narr | detector | `prose_fields` undeclared; CF-06 |
| registry description (seed L683) | Ldgr (qualification), Carr | real (declared provenance state) | 19 rows still cite the refuted "BPHS Ch.29"; 6 Rahu/Ketu rows UNSOURCED; the saved `Ldgr.source_presence` reads PASS 76/76 (presence, not qualification) |

## 3 · Disposition

**keep (P)** — the table is complete and its registry row states its own provenance gaps honestly; the 19 refuted citations are a known, declared provenance limit that only a row-by-row verified re-citation can close (a domain act, not an invention). Gochara consumers are the Pravāha campaign’s: any output change is analysed here and its rebuild waits for SS.

Approver under Track A brief §10: **Steward (G16)**. Disposition accepted as proposed (SS 2026-10-01, Q10).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Build.completion: one writer, three tables, two producers

- **Answers:** census `Build.completion` FAIL (104 vs 76); ledger `bg_transit_rules-Build.completion`; CF-02
- **Change:** report this asset’s own rows (`counts["bg_transit_rules"]`) rather than the three-table total, and scope count_sql/declarations to state the 7 migration-owned rows as a second producer; add `bg_transit_moorti` to a declared produced-table set (it is written by this writer and counted by no asset).
- **Files / declaration / migration:** `bg_transit_rules.py` (WriterResult) and the registry/declarations
- **Failing-first test and mutation:** failing-first: `rows_written` equals the changed rows of the writer-owned rules; mutation: revert → mismatch
- **Output change:** none
- **Blast radius:** record-only: `rows_written` and the declared produced-table set change; no row changes. The same 41 readers see no difference.
- **Rebuild:** registry part: none; writer part: needs production rebuild to refresh the record (idempotent; R9-adjacent consumers read the table, so notify via the B.L0 statement)
- **Gate it moves:** Build (completion), Earn (count_sql scope)
- **Fix class:** writer code + registry/declaration; **buildable before J1:** tier-independent; vocabulary tier-dependent (TGH-T2-05)

### FD-2 · Attribution state `sourced | unsourced | refuted`; the 19 refuted citations

- **Answers:** registry description (19 + 6 rows); CF-11
- **Change:** decided (SS 2026-10-01, Q3): add `attribution_state`; the 19 rows citing the refuted "BPHS Ch.29" are `refuted`, the 6 Rahu/Ketu rows `unsourced`, the 51 verse-cited `sourced`; neither `unsourced` nor `refuted` is a PASS. Re-sourcing the 19 from the `bg_texts` corpus, row by row with the verified predicate that produced the 36, is a Track I research item spot-checked at the milestone review.
- **Files / declaration / migration:** a migration (additive column) + `l0_transit.py`
- **Failing-first test and mutation:** counts: 19 `refuted`, 6 `unsourced`, 51 `sourced` (76 − 25) stated in advance; mutation: re-cite one row with verification → its state flips
- **Output change:** one additive column
- **Blast radius:** additive column on `bg_transit_rules`; the writer upserts and retires only owned rows, so the SERIAL `id` (FK-referenced by `gochara_resonance_map.source_rule_id`, migration 459) is stable. Readers (41 non-test files): `ka_sangam.py`, `ka_moorti_nirnaya.py`, `ka_vedha_gochara.py`, the Gochara kernel and resonance rebuild scripts. Gochara consumers are the Pravāha campaign’s: notify via SS (R9-adjacent) before the rebuild.
- **Rebuild:** needs production rebuild: bg_transit_rules (after the migration; idempotent)
- **Gate it moves:** Ldgr (qualification), Carr
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state
- **Decision:** ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.

### FD-3 · Carr detector — D1 on the verse-cited rows

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for the 51 rows with a verse citation, resolve to the named chunk (Phaladīpikā PG322/PG323 etc.) and test the rule’s house/graha anchor terms; the 19 refuted rows must be reported as mismatches (the detector should find them non-zero: a true positive), the 6 unsourced as unverifiable.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 6 / transitive 34 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Declare `prose_fields` (Null and Narr gates)

- **Answers:** census Null/Narr cells NO_DETECTOR (declarations `prose_fields: null`); CF-06
- **Change:** Read `brahmagyan/l0_transit.py` for any composed text column; declare `[]` expected (`rule_notes` and `phala_brief` are literals) after reading `l0_transit.py`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` entry for this asset (`prose_fields` + `evidence.prose_fields` as `path:line`)
- **Failing-first test and mutation:** declarations validation test; mutation: a wrongly declared `[]` must be flagged by Narr.agree/Narr.lint
- **Output change:** none
- **Blast radius:** no row, id or served field of this asset changes; declared dependents direct 6 / transitive 34 and the readers in the §0 row see no difference (the change lives in the inspector, the declarations file or a registry row).
- **Rebuild:** none (declaration only)
- **Gate it moves:** Null, Narr (NO_DETECTOR → measured or N/A)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01)

### FD-5 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `query_transit_engine.ts`, `query_transit_vedha.ts`; CF-04
- **Change:** decided (SS 2026-10-01, Q2): Dens applies because this asset reaches a served surface. Declare `density_contract` facets (`paginated`, `facets`, `empty_reason`) on the module(s); if the table is a uniform-authority vocabulary also declare `uniform_authority: true` in the declarations (R, PROVISIONAL until the J1 review); a mixed-authority table needs a real tier column.
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` module(s) named above; `platform/src/lib/retrieval/registry/types.ts` (descriptor, unchanged)
- **Failing-first test and mutation:** response-shape test for `empty_reason` and the trim; mutation: drop the declaration → census FAIL
- **Output change:** none
- **Blast radius:** no row changes (test or code-side only); declared dependents direct 6 / transitive 34 and the readers in the §0 row see no difference.
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent for the facets (decided); the `uniform_authority` detector support is an (R) item for the E6 work
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn.build_record / Cost.baseline NO_DETECTOR (instrument absent); no change to this asset.
- **CF-02** — Producer attribution: rider ids, multi-table writers and multi-producer tables. *This asset:* 104 vs 76
- **CF-11** — `classical_tradition` is not provenance: explicit attribution state `sourced | unsourced | refuted` (no invented citations). *This asset:* 19 refuted + 6 unsourced citations
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 above (expected non-zero on the 19)
- **CF-06** — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates). *This asset:* prose declaration
- **CF-04** — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R). *This asset:* 2 modules

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(graha, rule_type, primary_house)` (census, 0 duplicates). The fingerprint excludes the SERIAL `id` (renumbering is forbidden by migration 459’s FK) and covers `(graha, rule_type, primary_house, effect, citation, …)`; the 7 migration-owned rows are fingerprinted separately. Ownership-scoped retirement must not touch them.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 76 rules with their declared citation states, the ownership-scoped retirement (`_owned_row_filter`) and the SERIAL-id/FK discipline.
- **Carriage check chosen (T4 §4.1; one only):** D1 (verse-cited rows); the refuted rows are expected detector positives.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Decisions applied (SS answered INDEX section 7 on 2026-10-01; no question is open in this brief)

Disposition accepted as proposed (Q10). Items marked (R) are PROVISIONAL until the J1 review.

1. ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.
2. CF-02: ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch. ANSWERED by SS 2026-10-01 (Q19): scope `count_sql` to the primary table and declare the asset multi-table.
3. CF-07: ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
4. CF-04: ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

**Track I items arising (see INDEX section 8):** TI-L0-03, TI-L0-05, TI-L0-06, TI-L0-09, TI-L0-10, TI-L0-32.
