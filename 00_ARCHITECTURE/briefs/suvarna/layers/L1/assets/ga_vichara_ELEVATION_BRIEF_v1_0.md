---
asset_id: ga_vichara
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
ledger_gap_ids: [ga_vichara-Idem.pattern, ga_vichara-Earn.build_record, ga_vichara-Cost.baseline, ga_vichara-Build.history, ga_vichara-Carr.detector]
---
# ga_vichara — Vicāra (judged structure): valence, varga ratification, varga consistency, leverage index

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

A new L1 sibling to `ga_structural` for judgment (`ga_writers/ga_vichara_writer.py:1-48`), consuming `ga_structural`'s `bhava_significance_link`/`graha_dignity_per_varga`/`graha_functional_class_per_ascendant`, `ga_strength`'s `graha_shadbala_total`, `ga_yoga`'s firings and `ga_dashas`' `chart_dashas` read-only, deriving four row families into `chart_vichara`: `valence_pass`, `varga_ratification` (+ divergence), `varga_consistency`, `leverage_index`. No new positional computation (gaps are logged in `value_jsonb.known_gaps`, not computed); constants come from `brahma_vichara_constants`; idempotency `DELETE FROM chart_vichara WHERE chart_id, ayanamsha_id` then INSERT (`:165`). `chart_vichara` carries the union of two consumers' column vocabularies (`actor`/`subject`, `target`/`domain`, `varga`/`varga_id`, `constituent_facts_array`/`constituent_fact_ids`) and the writer populates both sides (migration 435).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1422` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_vichara.py:11` (heavy: `build_ga_vichara_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_vichara` (own table; four families; migration 435) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 8,524 / 8,249 (Δ +275); `asset_throughput` lit / 8,524; seed floor literal 8240 (live floor 8,249); `catalog_status` CURRENT (W2 recorded DRAFT; corrected) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_structural`, `ga_strength`, `ga_dashas`, `ga_yoga` (live and seed; the wrapper comment names the same four); the writer reads constants from the L0 table `brahma_vichara_constants` (never Python literals, `:30-33`; exempt) | layer instance §2.5 |
| blast radius | census (pre-1210): direct 1 / transitive 49; seed + migration 1210 reconstruction names 3 direct dependent(s): `bo_karanajala`, `bo_laksana`, `bo_laksana_rerank` | census `blocking_radius`; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry in either direction) |
| code readers / served surface | `get_vichara.ts:187` (declarations `read_evidence`), `get_dasha_lord_capability.ts`, `query_remedies.ts` (L2), `register_d9_judgment.ts`, `reading_checklist.ts` (census: 2 modules, 2 declaring `density_contract`); `bo_laksana` (1 direct, census) plus `bo_karanajala` and `bo_laksana_rerank` (migration 1210); read back by `ga_structural` (see gaps) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | "judged structure" (T2 §3.3): L1 includes judged structure, but being in L1 "does not make every field an equally verified numerical fact"; epistemic typing of each output is TG-L1-020 | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 14 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-05): BLOCKED: upstream dependency(ies) ga_dashas, ga_structural, ga_yoga did not complete in this run; skipped to avoid building on incomplete data |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run bc1755d5 complete/build (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run bc1755d5 complete/build (2026-09-08) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 16/20 built column(s) (80.0%) selected by 4 capability module(s); dark: ['actor', 'constituent_facts_array', 'target', 'varga']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L1/rollup_saved_L1.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 8 module(s) reach it by code: L0_brahmagyan/query_vichara_constants.ts, L1_ganita/get_dasha_lord_capability.ts, L1_ganita/get_vichara.ts, L2_bodha/query_remedies.ts, reading_checklist.ts, register_d9_judgment.ts (+2 more); a referencing capability declares density_contract but L1_ganita… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`/Users/Dev/suvarna-evidence/A_L1/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: duplicated column pairs can diverge | Vocab | real | migration 435 left two vocabularies side by side ("reconciliation-pending"); the writer fills both so both consumers see rows, but nothing detects a disagreement between the two sides (§N.5: one value, one place). A parity check (per row, the two sides equal) is the detector; collapsing to one vocabulary is an output/readers change for SS; CF-02/CF-08 family |
| brief: back-read by `ga_structural` | Build.dag | real | `ga_structural` reads `chart_vichara` for the wealth ratification (`ga_structural_writer.py:2761-2770`) though `ga_vichara` depends on it; see `ga_structural` FD-1 (the proposed home for the daridra-cancellation pass is this asset); CF-13 |
| brief: `prose_fields` undeclared | Null, Narr | detector | declarations `prose_fields: null`; `source_citation` carries design-document references (constants such as `DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11`, `:648,680,750,904`) or a `citation` variable (`:437,519`); `value_jsonb.known_gaps` holds gap statements; candidate: `[]` for `source_citation` if every site is a constant, plus a JSON path for `known_gaps` if composed (neither read in full); CF-06 |
| brief: epistemic type of each output | Carr/Narr | SS question | valence, ratification factor and leverage index are judgments built on stored facts; the layer instance (TG-L1-020) leaves the typing open; a row-level type field or a declared output class would let consumers tell judged from computed |
| ga_vichara-Build.history | Build | history | PARTIAL: 14 errors / 3 aborts; latest error 2026-08-05 `BLOCKED: upstream ga_dashas, ga_structural, ga_yoga did not complete` (cascade); CF-10 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_dasha_lord_capability.ts` and `get_vichara.ts` carry no tier column in their served selects; CF-04 |
| brief: Carr | Carr | detector | D3 applies to the recomputable parts (ratification and consistency are functions of stored dignities and constants): recompute from the stored `chart_facts` and the constants table and compare; CF-07 |
| ga_vichara-Complete.depth / Ldgr / Vocab | all | PASS | 13 of 20 columns fully populated, none never-populated; `source_citation` populated; Vocab key `(id)`; the integrity contract (migration 747) and the output digest spec (920) exist |
| ga_vichara-Earn / Cost / Idem | Earn, Cost, Idem | detector / stale | CF-05; the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — the W2 finding (F-D9: `catalog_status = DRAFT` on an asset with 8,249 exact rows and three production consumers) is closed (CURRENT); the writer reads, never restates, and takes its constants from L0. Open items are a duplicated-vocabulary parity check, a back-read owned by another asset's brief, and detectors.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Parity detector for the duplicated column pairs

- **Answers:** brief gap "duplicated columns"; §N.5
- **Change:** a read-only check that for every `chart_vichara` row `actor = subject`, `target = domain`, `varga = varga_id` and the two fact-id arrays hold the same ids where both sides are populated; PASS only on zero disagreements; report rows where one side is NULL separately
- **Files / declaration / migration:** Track E inspector tooling (or an integrity conjunct on `ga_vichara`, `integrity_check_sql`, migration 747 precedent)
- **Failing-first test and mutation:** failing-first: a seeded row with differing sides is reported; mutation: align the sides and the check passes
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Vocab
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent

### FD-2 · Receive the daridra-cancellation family (design, SS)

- **Answers:** back-read; `ga_structural` FD-1; CF-13
- **Change:** add the cancellation evaluation as a fifth `chart_vichara` family reading `ga_yoga_firings` (dhana-family firings that intersect the wealth-house lords + Jupiter) and the asset's own `varga_ratification` (wealth), so the dependency runs structural → vichara only
- **Files / declaration / migration:** `ga_vichara_writer.py` (new family), `chart_vichara` unchanged (additive rows)
- **Failing-first test and mutation:** see `ga_structural` FD-1
- **Output change:** yes (additive rows; SS R5)
- **Blast radius:** `bo_laksana`, `bo_karanajala`, `bo_laksana_rerank` read the table
- **Rebuild:** **needs production rebuild**: REVIEW
- **Gate it moves:** Build (dag)
- **Fix class:** writer code + data (output change); **buildable before J1:** tier-dependent: which asset owns a cancellation

### FD-3 · Declare `prose_fields` after reading the composition sites

- **Answers:** Null/Narr NO_DETECTOR; CF-06
- **Change:** read `ga_vichara_writer.py:437, 519` (the `citation` variable) and the `known_gaps` writers; declare `[]` with evidence if all text is constant, else the column/JSON-path list
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation as CF-06
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* FD-2: back-read by `ga_structural`; sink of the DAG
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-3: undeclared
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D3: recompute ratification/consistency
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: tier column absent in two served selects
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 14/3: cascade history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: none
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* literals: none found (no tier string in the module)
- **CF-16** — `ga_vargas` restore and downstream re-earn: `chart_divisionals` empty for the canonical chart under a `lit` record. *This asset:* indirect: reads `ga_structural`/`ga_yoga` rows that read `chart_divisionals`

## 5 · Semantic fingerprint contract (for E5.5)

natural key not read in full (the table has a surrogate `id`; rows are identified by `(chart_id, ayanamsha_id, vichara_family, subject, actor, target, varga)` per the INSERT, `:933`); volatile: `id`, `build_id`, `computed_at`; the duplicated column pairs must be fingerprinted on both sides.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the four judgment families with constants from `brahma_vichara_constants`, the read-only discipline (no new positional computation; gaps logged), and the resolving `constituent_fact_ids`.
- **Carriage check chosen (T4 §4.1; one only):** D3 — recompute ratification and consistency from stored dignities and the constants table; D1 for the doctrine references (`DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §§4, 8, 11`) is a design reference, not a classical text.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Should `ga_vichara` receive the daridra-cancellation family from `ga_structural` (see `ga_structural` FD-1)?
2. Is a per-row epistemic-type field (judged vs computed) wanted on `chart_vichara` (TG-L1-020)?
