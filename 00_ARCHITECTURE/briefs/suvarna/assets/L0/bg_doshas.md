---
asset_id: bg_doshas
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
disposition_proposal_approver: "Steward (G16) for the disposition; the output change it names needs SS (Track A §10, R5)"
ledger_gap_ids: [bg_doshas-Idem.pattern, bg_doshas-Earn.build_record, bg_doshas-Cost.baseline, bg_doshas-Dens.served, bg_doshas-Carr.detector, bg_doshas-Build.history]
---
# bg_doshas — Classical dosha catalogue (79 rows over three tables)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Registry description: 'Classical dosha definitions — formation rules, effects, severity, cancellation conditions'. `seed_doshas` replaces `reference_doshas`, `brahma_dosha_catalog` (79) and the 79 `dosha` rows of `brahma_ontology` by delete-then-insert (`platform/python-sidecar/brahmagyan/l0_doshas.py:1942-1944`), binding a hand-authored inline corpus verbatim (the declarations record: stores source text, composes none). **Citation policy, stated in the module and attributed to a native decision (`:18-21`):** about 40 entries cite `'classical_tradition'` as honest provenance where no single BPHS verse names the doṣa, 'NOT fabricated citations'; live 53 of 79 carry the token (layer instance Q-04). The header's '50 definitions / floor ≥ 50' is stale against the live 79. **The 79 ontology rows are written with `[]` synonyms** (`:1989-2002`, comment 'empty for doshas'), which is the census `Vocab.alias` FAIL (`dosha` 79/79 empty) recorded on `bg_ontology`. Depends on `bg_ontology`; declared dependent `bg_parihara_rules`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:381` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_doshas.py:15`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `brahma_dosha_catalog`; count_sql tables: `brahma_dosha_catalog`, `brahma_ontology`, `reference_doshas` | census CEN-R |
| live rows / floor | 237 / 237 (Δ +0) | census `live_rows`; floor from layer instance §1.1 table |
| catalog_status | CURRENT | census |
| depends_on (intra-L0, live) | `bg_ontology` | layer instance §2.5 (Q-02) |
| blast radius | declared dependents (live, saved census blocking_radius): direct 1 / transitive 1 (every layer); named: `bg_parihara_rules` | census `blocking_radius`; names from seed + migrations (reconstruction) |
| code readers (declared-vs-actual) | `brahma_dosha_catalog`: 11 non-test py/ts/tsx files reference it (5 outside brahmagyan/ and bg_*.py writers): `bo_laksana.py`, `ga_structural_writer.py`, `coverage_matrix.ts`, `parity_check.ts`, `source_query_availability.ts`; `brahma_ontology`: 17 non-test py/ts/tsx files reference it (4 outside brahmagyan/ and bg_*.py writers): `parity_check.ts`, `source_query_availability.ts`, `l0_brahmagyan.ts`, `kala_sky_pattern.ts`; `reference_doshas`: 2 non-test py/ts/tsx files reference it (0 outside brahmagyan/ and bg_*.py writers) | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx, paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | `query_dosha_catalog.ts`, `query_parihara_graph.ts`; `density_contract` declared on 0 of 46 L0 capability modules (layer instance §1.4) | census reach |
| role / scoring mode | neither (supplies what manifestation and time rest on); fidelity (reference layer: never retired for want of a reader) | layer instance §0.2, §4.4 |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 1c44df29 complete/skip_no_delta (2026-09-06) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served † | FAIL | 2 module(s): query_dosha_catalog.ts, query_parihara_graph.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 1 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-04): post-write integrity check failed: integrity_check_sql → False |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at any chart (global build record): run 1c44df29 complete/skip_no_delta (2026-09-06) |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = [] (declared no generated prose) |

**PASS cells (compact):** Ldgr.source_presence (classical_citations populated on 79/79 rows); Idem.pattern † (the asset's own table(s) replaced by delete-then-insert: reference_doshas (brahmagyan/l0_doshas.py:1942 via b…); Vocab.identity (declared key (canonical_id): 0 duplicate(s)); Build.completion; Build.contract; Build.count_integrity; Build.dag †; Build.dep_liveness; Build.exercised (3 executed run(s) of 4 build_run_assets row(s), scope(s): asset_set, last executed 2026-09-06); Build.registered (@register in bg_doshas.py; registry agrees); Build.target †; Count.floor; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3).

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell) | gate | class | note |
|---|---|---|---|
| bg_doshas-Idem.pattern | Idem | stale | ledger row from an earlier run; saved census Idem.pattern reads PASS \| ledger: measured: no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there / required: the Idem gate's claim |
| bg_doshas-Earn.build_record | Earn | detector | instrument absent (migration 1094); CF-05; no asset change |
| bg_doshas-Cost.baseline | Cost | information | same absent instrument; CF-05 |
| bg_doshas-Dens.served | Dens | real as measured at rev 1; applicability and re-measure pending | CF-04 \| ledger: measured: 2 module(s): query_dosha_catalog.ts, query_parihara_graph.ts; declaring density_contract: 0 / required: the Dens gate's claim |
| bg_doshas-Carr.detector | Carr | detector | no D1/D2/D3 detector exists for this asset; CF-07 |
| bg_doshas-Build.history | Build | history | 1 error 2026-09-04 (`post-write integrity check failed`) and 1 abort; latest run complete; CF-10 \| ledger: measured: latest run complete, but 1 error(s) and 1 abort(s) on record. post-write integrity check failed: integrity_check_sql → False / required: the Build gate's claim |
| census: Vocab.alias (recorded on bg_ontology) | Vocab | real | `dosha` 79/79 empty alias sets; the code that writes them is THIS asset (`l0_doshas.py:2002`); CF-09 |
| layer instance Q-04 / §1.2 | Ldgr (qualification) | real or accepted provenance: SS question | 53 of 79 rows cite `classical_tradition`; `Ldgr.source_presence` reads PASS (presence, not qualification); CF-11 |

## 3 · Disposition

**enrich (E)** — the carried E stands for the alias sets (an additive output change in the ontology rows this writer owns). The citation half is narrower than the layer instance said: the token is a documented native decision, so the proposal is an explicit attribution state, not re-sourcing.

Approver under Track A brief §10: **Steward (G16) for the disposition; the output change it names needs SS (Track A §10, R5)**. 

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Closed alias sets for the 79 doṣa ontology rows

- **Answers:** census `Vocab.alias` FAIL (on bg_ontology); ledger `bg_ontology-G07`, `bg_ontology-Vocab.alias`; CF-09
- **Change:** replace the `[]` at `l0_doshas.py:2002` by a closed alias set per doṣa. Step 1: read how the 15 complete classes compose `synonyms` (convention) and apply the same to doṣa; step 2: take names only from fields the module’s own DOSHAS entries already carry (Sanskrit/English names, listed alternates); a row with no alternate gets the conventional minimal set, never an invented alias; step 3: add a test that no `dosha` row has an empty set. Additive class (T2 §4.4 display/alias correction): it must not recompute any chart.
- **Files / declaration / migration:** `platform/python-sidecar/brahmagyan/l0_doshas.py` (the INSERT near L1989-2002 and the DOSHAS entries); no migration
- **Failing-first test and mutation:** failing-first: count of `dosha` rows with empty `synonyms` = 79 now, 0 after; `count(*) = count(DISTINCT (entity_class, canonical_id))` unchanged (741); `resolve_entity` on a doṣa alias returns exactly one row. Mutation: blank one set → test fails
- **Output change:** 79 `brahma_ontology` rows gain synonyms; `bg_doshas` row counts unchanged
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild: bg_doshas (global delete-then-insert of 3 tables, ~237 rows), then no dependent rebuild is strictly required for an additive alias (readers resolve at query time)
- **Gate it moves:** Vocab (alias FAIL → PASS on bg_ontology)
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent for the sets; the release/normalisation clause is tier-dependent (TGH-T2-12)
- **Question for SS:** Which alias convention does SS accept for doṣa (derive from the 15 complete classes)?

### FD-2 · Explicit attribution state for tradition-rooted rows

- **Answers:** layer instance Q-04 (53 of 79); `l0_doshas.py:18-21`; CF-11
- **Change:** add `attribution_state` (`verse_cited` | `tradition_rooted`) derived from the existing token; do NOT replace the token with a verse (B.10). Any row-by-row re-sourcing is a domain decision outside this design.
- **Files / declaration / migration:** a migration adding the column to `brahma_dosha_catalog` + `l0_doshas.py` (derive from `classical_citations`)
- **Failing-first test and mutation:** count of `tradition_rooted` rows = 53, citations unchanged; mutation: change a token to a verse → state flips
- **Output change:** one additive column on `brahma_dosha_catalog`
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** needs production rebuild: bg_doshas (after the migration)
- **Gate it moves:** Ldgr (qualification), Carr
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state
- **Question for SS:** Is `classical_tradition` an accepted provenance value (native decision cited in the module)?

### FD-3 · Carr detector — D1 on the verse-cited subset

- **Answers:** census `Carr.detector` NO_DETECTOR; CF-07
- **Change:** for the 26 rows (79 − 53) that cite a verse, resolve the citation and test the doṣa’s name/anchor terms against the chunk; the 53 tradition-rooted rows have no passage to correspond to, so they report as unresolvable by construction, not as passes (the gate is PARTIAL until SS rules on them).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents; the change is local to this asset’s record or declaration unless the output change says otherwise)
- **Rebuild:** none (detector only)
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no clause

### FD-4 · Dens: declare density on the served module(s)

- **Answers:** census `Dens.served` FAIL (saved, rev 1): 2 modules: `query_dosha_catalog.ts`, `query_parihara_graph.ts`; CF-04
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
- **CF-09** — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers). *This asset:* owns the code for the doṣa alias sets
- **CF-11** — `classical_tradition` provenance made an explicit queryable state (no invented citations). *This asset:* 53 tradition-rooted rows
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D1 on the verse-cited subset
- **CF-04** — Dens (serving density) on the L0 served modules. *This asset:* 2 modules
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* 1 error, 1 abort; latest run complete

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `canonical_id` (census: 0 duplicates) for `brahma_dosha_catalog`; `(entity_class='dosha', canonical_id)` for the ontology rows. Delete-then-insert: fingerprint over `(canonical_id, formation_text, effects_text, severity, cancellation, citations, synonyms)`; volatile: `created_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 79 doṣa definitions with their formation rules, effects and cancellation conditions as authored; the citation policy; the ontology rows' canonical ids.
- **Carriage check chosen (T4 §4.1; one only):** D1 (source correspondence) on the verse-cited subset; the tradition-rooted rows are explicitly outside it.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Accept `classical_tradition` as a provenance value (add an explicit state), or re-source the 53 rows from the corpus?
