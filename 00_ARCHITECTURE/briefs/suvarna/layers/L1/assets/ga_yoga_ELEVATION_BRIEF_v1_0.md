---
asset_id: ga_yoga
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 at the base commit (7 on origin/main 066c58587: the revision note names a NA_CAUSES addition for Carr; the criterion bodies were not diffed beyond that) and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "enrich (E)"
disposition_proposal_approver: "Strategic Suvarṇa (output change, R5)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS"
track_i_items: [I-11]
ledger_gap_ids: [ga_yoga-Idem.pattern, ga_yoga-Earn.build_record, ga_yoga-Cost.baseline, ga_yoga-Count.floor, ga_yoga-Complete.depth, ga_yoga-Build.history, ga_yoga-Carr.detector]
---
# ga_yoga — Yoga firings (rule evaluation against L1 facts; 233 catalogue yogas) with cancellation (bhaṅga) where a rule is implemented

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Evaluates classical yoga formation rules against L1 `chart_facts` (from `ga_structural`, `ga_positions`) for each ayanamsha and writes one row per fired yoga into `ga_yoga_firings` (`ga_writers/ga_yoga_writer.py:1-33`): no LLM in the data path, strength NULL unless resolvable by the single ratified `constituent_bala_v1` derivation (normalised ṣaḍbala of constituent grahas), `bhanga_active` NULL-with-reason where no classical cancellation rule is implemented (Neecha-Bhaṅga Rāja Yoga has five, one floored), classical citations inherited from `brahma_yoga_catalog`, `constituent_fact_ids` resolving to real `chart_facts.fact_id` values. Idempotency: delete-then-insert scoped to `(chart_id, ayanamsha_id)`. D9 findings anchor to the same grahas' D1 facts because `chart_divisionals` rows carry no `fact_id` to cite (documented in `citation_human` via `@D9` rule tags, `:2512-2516`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1504` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_yoga.py:11` (heavy: `build_ga_yoga_substep` per ayanamsha); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_yoga_firings` (own table; `count_sql` over the chart) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 53 / 63 (**Δ −10**); `asset_throughput` lit / 53; seed floor literal 63 (migration 650: "measured minimum across the three built charts") | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_structural`, `ga_dashas` (live and seed); the writer also reads `brahma_yoga_catalog` (`ga_yoga_writer.py:166`, MF-L1-006; exempt) and `chart_divisionals` for D9 through `ga_structural_writer._load_varga_positions` (`ga_yoga_writer.py:2435-2441`) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 4; census (2026-09-30, pre-1210): direct 3 / transitive 51; seed + 1210 reconstruction names 4 direct dependent(s): `bo_grounding`, `ga_vichara`, `ka_gochara`, `ka_yojaka` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_yoga_firings.ts:213` (declarations `read_evidence`; a run-time select list so tier carriage is not established), `get_yoga_dosha.ts` (no tier column in its served select), `query_planet.ts`, `reading_checklist.ts`, `register_d8_assess_domain.ts`, `register_d9_judgment.ts`; 4 direct (live incl. 1210; census pre-1210: 3) / 51 transitive dependents, `ka_yojaka` (migration 1210) among them | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | DP05 clause results (layer instance §1.4): `partial_formation_pct` and `activation_dasha_periods` are the DP05 fields it never populates | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 15 error(s) and 9 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-05): BLOCKED: upstream dependency(ies) ga_dashas, ga_structural did not complete in this run; skipped to avoid building on incomplete data |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 6a7efd45 complete/skip_no_delta (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 6a7efd45 complete/skip_no_delta (2026-09-08) |
| Count | Count.floor | FAIL | live=53, floor=63, delta=-10 |
| Complete | Complete.depth | PARTIAL | 202 rows, 24 cols; fully populated 15; NEVER populated ['partial_formation_pct', 'activation_dasha_periods'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width ≥ 0/22 built column(s) (0.0%), a lower bound: L1_ganita/get_yoga_firings.ts select(s) a run-time column list selected by 2 capability module(s); dark: ['ayanamsha_id', 'bhanga_active', 'bhanga_na_reason', 'bhanga_rule_fired', 'bui…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 7 module(s) reach it by code: L1_ganita/get_yoga_dosha.ts, L1_ganita/get_yoga_firings.ts, L1_ganita/query_planet.ts, reading_checklist.ts, register_d8_assess_domain.ts, register_d9_judgment.ts (+1 more); a referencing capability declares density_contract but L1_ganita/get_yoga_dosha.ts:… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PARTIAL; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PASS; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_yoga-Count.floor | Count | SS question | FAIL: live 53 vs floor 63 (Δ −10), and the last build also wrote 53. The floor was set by migration 650 on 2026-09-05 as the measured minimum across three charts; the canonical chart now has 10 fewer firings. Cause not determined offline. Candidates: (a) the corrected F-A1 D9 positions can LEGITIMATELY change D9-dependent firings (about 22% of varga sign assignments changed, notice #1747; the detectors load D9 through `chart_divisionals`, `:2435-2441`), so the lower count may be the right one; (b) a rule change after 09-05 (the writer's only commit since is the label fix #1979, 09-06); (c) an upstream `ga_structural` change. Not supported: "the table was empty at build time" — I-11 shows the last `ga_yoga` build (2026-09-08 07:42) ran after `ga_vargas` repopulated (2026-09-07 11:03). Floors are information (D3). Diagnose read-only: compare `yoga_canonical_id` per ayanamsha between the last two builds (generation history, MF-L1-012) |
| ga_yoga-Complete.depth | Complete | real | PARTIAL: `partial_formation_pct` (set to None where a relation is floored, `:1096`; never populated as a percentage in this table) and `activation_dasha_periods` (a DDL column from migration 240; the writer never sets it) are never populated over the 202-row whole table — both are DP05 fields (layer instance §1.4) |
| brief: `prose_fields` declaration is incomplete | Null, Narr | real | declared `["citation_human"]` only; the INSERT also binds `derivation`, `strength_label` and `bhanga_na_reason` (`:2523-2526`); the offline grader flags `derivation` as an undeclared prose-vocabulary column (Narr.agree PARTIAL); `strength_label` grades `strength` and `bhanga_na_reason` states a reason — to be read before the declaration is corrected; CF-06 |
| brief: D9 constituents have no `fact_id` | Ldgr | real | D9-anchored firings cite the same grahas' D1 facts and name D9 only in `citation_human` (`:2512-2516`) because `chart_divisionals` has no `fact_id`; the lineage of a D9 clause is therefore prose, not a resolvable id; a lineage column or a `chart_divisionals` fact id is the fix; CF-08 |
| brief: missing direct edge to `ga_vargas` (Track I §D) | Build.dag | real | `ga_yoga` → `ga_vargas` (table `chart_divisionals`, via `ga_structural`'s loader): the transitive path through `ga_structural` exists, the direct edge is not declared; CF-13 |
| brief: back-read by `ga_structural` | Build.dag | real | `ga_structural` reads `ga_yoga_firings` (`ga_structural_writer.py:2800-2806`) although `ga_yoga` depends on it; see `ga_structural` FD-1; CF-13 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_yoga_dosha.ts` has no tier column in its served select and `get_yoga_firings.ts` selects a run-time column set (tier carriage not established); this is the CLAUDE.md §N.6 catalog-vs-confirmed surface; CF-04 |
| ga_yoga-Build.history | Build | history | PARTIAL: 15 errors / 9 aborts; latest error 2026-08-05 `BLOCKED: upstream ga_dashas, ga_structural did not complete` (cascade); CF-10 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | offline: fidelity PARTIAL (9 test files call the builder and assert in the same test function; none grades the sentence), lint PASS; CF-15 |
| ga_yoga-Earn / Cost / Carr / Idem | Earn, Cost, Carr, Idem | detector / stale | CF-05, CF-07 (D1: each firing's citation against the cited yoga text; the catalogue is L0's `brahma_yoga_catalog`, verse-level grounding is L0-owned, W2 F-D7/D8); the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**enrich (E)** — a deterministic, cited rule evaluator whose census cells are PASS except Count/Complete and the history record; what a senior acharya would add is the DP05 clause detail the table does not carry (`partial_formation_pct`, `activation_dasha_periods`) and a D9 lineage. Those are output changes, so the disposition is enrich with a small, additive must-add list; the 10-row shortfall is first a diagnosis.

Approver under Track A brief §10: **Strategic Suvarṇa (output change, R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Diagnose the 63 → 53 shortfall (read-only), then decide re-floor vs fix

- **Answers:** census Count.floor FAIL; MF-L1-010
- **Change:** compare per-ayanamsha `yoga_canonical_id` sets between the last two builds and against the catalogue; check whether the missing firings are the D9-dependent detectors (`:2435-2441`) and whether they are explained by the corrected F-A1 D9 positions (a legitimate change). If so, re-declare the floor by a registry migration with the reason (floors are aspirational and equal the achieved count after a build: CLAUDE.md §N.4); if firings were genuinely lost, fix the cause and rebuild
- **Files / declaration / migration:** read-only; then possibly a registry migration (`target_floor`; number = max+1 at execution time)
- **Failing-first test and mutation:** failing-first: the firing set after the fix equals the expected set for the chart (a seeded missing firing must be reported); mutation: drop D9 positions from a fixture and the D9-dependent firings disappear
- **Output change:** none
- **Blast radius:** readers of firings (`ka_yojaka`, `ga_vichara`, `ga_structural`'s back-read, `bo_laksana`); a re-floor changes no data
- **Rebuild:** none for a re-floor; **needs production rebuild** (small) only if firings were genuinely lost: REVIEW
- **Gate it moves:** Count (information), Complete
- **Fix class:** diagnosis + registry/declaration or data; **buildable before J1:** tier-independent for the diagnosis
- **Question for SS:** May SS authorise the read-only per-yoga comparison?

### FD-2 · Populate `partial_formation_pct` and `activation_dasha_periods`, with D9 lineage (the enrichment)

- **Answers:** Complete.depth PARTIAL; DP05; brief gap "D9 constituents"
- **Change:** (1) set `partial_formation_pct` from the formation clauses actually satisfied where the writer already tracks `is_partial` (the variable exists, `:457, :1096`); (2) set `activation_dasha_periods` from the `chart_dashas` periods whose lords are the yoga's constituents — read from stored L1 rows (`ga_dashas`), never recomputed (§N.5); (3) carry D9 lineage as a resolvable id (a `chart_divisionals` row id column) instead of prose. Additive columns/values only; existing firings unchanged
- **Files / declaration / migration:** `ga_writers/ga_yoga_writer.py:1086-1114, 2512-2530`; possibly an additive migration for the lineage column; the served tool `get_yoga_firings.ts`
- **Failing-first test and mutation:** failing-first: for a partially formed yoga the percentage is between 0 and 100 and equals the satisfied/total clause ratio; `activation_dasha_periods` resolve to `chart_dashas` rows; mutation: shift a clause and the percentage moves
- **Output change:** yes (additive; SS R5)
- **Blast radius:** readers of `ga_yoga_firings` see new non-NULL fields; `ka_yojaka` reads constituent planets (Track I)
- **Rebuild:** **needs production rebuild** of `ga_yoga` (small): REVIEW
- **Gate it moves:** Complete (information), Ldgr
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-dependent: T2 §7.1 DP05 field list and TG-L1-012 (which DP05 fields L1 carries)
- **Question for SS:** Are `partial_formation_pct`, `activation_dasha_periods` and a D9 lineage id in the first L1 wave (DP05)?

### FD-3 · Complete the `prose_fields` declaration

- **Answers:** Narr.agree PARTIAL; CF-06
- **Change:** read `strength_label` and `bhanga_na_reason` production (`:2694`, the `R6A2_FLOOR_REASONS` table) and extend the declaration to the text columns that state or grade a value (`derivation`, `strength_label`, `bhanga_na_reason`), with writer evidence at the INSERT (`:2523-2526`)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation: remove `derivation` and Narr.agree must flag the writer
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-4 · Declare the direct `ga_vargas` edge (design only) and make the served select tier-carrying

- **Answers:** Build.dag; Dens PARTIAL; CF-13, CF-04
- **Change:** see `ga_dashas` FD-1 for the edge; for Dens select `verification_pass_status`-equivalent (`strength_formula_version`/tier) explicitly in `get_yoga_dosha.ts` and replace the run-time select list in `get_yoga_firings.ts` with a fixed one
- **Files / declaration / migration:** registry migration (consumer row); `platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts`, `get_yoga_firings.ts`
- **Failing-first test and mutation:** Build.dag and Dens read verdicts; response-shape test for the tier field
- **Output change:** none
- **Blast radius:** additive response fields; edge changes ordering
- **Rebuild:** none (served surface); the edge: REVIEW as in `ga_dashas`
- **Gate it moves:** Build (dag), Dens
- **Fix class:** registry/declaration + served surface (TS); **buildable before J1:** tier-dependent: N-22 Dens applicability; the edge is tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* FD-1: D9 detectors read `chart_divisionals`; relevant only if the builder is RLS-blind (I-11); not the cause of the 63 → 53 shortfall (the last build followed the ga_vargas build)
- **CF-03** — Registry correction batch (live registry vs seed literals: floors, edges, status) in one surgical migration plus seed literals. *This asset:* FD-1 (re-floor option): floor 63 may be re-declared by a registry migration if the diagnosis shows it was set high
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* FD-4: missing direct edge; back-read by `ga_structural`
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-3: declaration incomplete (`derivation`, `strength_label`, `bhanga_na_reason`)
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* Narr: declared; fidelity PARTIAL
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* FD-4: PARTIAL
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* D9 lineage: Ldgr PASS on `citation_ref`, but the D9 clause lineage is prose
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 15/9: history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D1: citation vs yoga text
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: none
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* literals: 4 quoted tier strings (indicative); the module does not import the vocabulary

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, yoga_canonical_id)` (census Vocab key); volatile: surrogate `id`, `build_id`, `computed_at`; the firing SET is the meaning — a fingerprint over the set of fired `yoga_canonical_id` per ayanamsha plus `strength` and `bhanga_active` is the check that detects a lost firing (53 vs 63).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the rule-evaluation design (no LLM, strength NULL unless the ratified derivation resolves it, honest NULL-with-reason for unimplemented cancellations, constituent `fact_id` resolution) and the Neecha-Bhaṅga evaluator.
- **Carriage check chosen (T4 §4.1; one only):** D1 — each firing inherits its citation from `brahma_yoga_catalog`; check the firing's prerequisites and exceptions against the cited yoga text (verse-level grounding is L0-owned).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. May SS authorise the read-only per-yoga comparison of the last two builds (the 63 → 53 shortfall)?
2. Are `partial_formation_pct`, `activation_dasha_periods` and a D9 lineage id in scope for the first L1 wave, and by what source-grounded rule?
