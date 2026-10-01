---
asset_id: ga_medical
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS"
track_i_items: []
ledger_gap_ids: [ga_medical-Idem.pattern, ga_medical-Earn.build_record, ga_medical-Cost.baseline, ga_medical-Build.history, ga_medical-Carr.detector]
---
# ga_medical — Jyotish medical indications per graha (not a diagnosis)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Per-chart Ayurvedic Jyotish indications: loads graha condition scores from `ga_condition_composite` (already built), loads dosha/organ/body-part mappings and the classical citation from the L0 `bg_medical_mappings`, grades `indication_strength` from the score (`< 0.4` strong, `0.4–0.6` moderate, `> 0.6` mild, NULL → `unknown`), looks up the Moon's `nakshatra_body_part` from `bg_nakshatra_medical`, and inserts with the disclaimer fields (`ga_writers/ga_medical_writer.py:1-37`). FORENSIC guards (Sun, Moon, Saturn) are non-fatal since F-E5 corrected a false classical rationale (the Sun is in an enemy sign in Capricorn and debilitates in Libra; `:26-29, 102`). Idempotency: `DELETE WHERE (chart_id, ayanamsha_id)` then INSERT (`:289`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1546` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_medical.py:25` (heavy: `build_ga_medical_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_medical` (own table; 9 grahas × 5 ayanamshas = 45 rows) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 45 / 45 (Δ +0); `asset_throughput` lit / 45; seed floor literal 45 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_condition`, `ga_positions` (live and seed); the writer also reads the L0 tables `bg_medical_mappings` and `bg_nakshatra_medical` (`ga_medical_writer.py:172`, MF-L1-006; L0 reads exempt on main) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 0; census (2026-09-30, pre-1210): direct 0 / transitive 0; seed + 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_medical_indications.ts:86` (declarations `read_evidence`; 13 of 15 built columns selected; contract declared); declared dependents 0 / 0 | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | medical application (layer instance §2.4: "medical and vāstu applications"); every row carries `indication_tier = 'jyotish_indication'` and `not_diagnosis = TRUE` (non-negotiable per the writer header) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 9 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): BLOCKED: upstream dependency(ies) ga_condition did not complete in this run; skipped to avoid building on incomplete data |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 9eb07d35 complete/skip_no_delta (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 9eb07d35 complete/skip_no_delta (2026-09-08) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/15 built column(s) (86.7%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PASS** — STRUCTURAL: 2 module(s) reach it by code: L1_ganita/get_medical_indications.ts, platform-mcp/src/tools/register_p1_aliases.ts; 1 capability(ies) declare density_contract AND select a tier column from it (indication_tier) in: L1_ganita/get_medical_indications.ts (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: a graded label from a number with writer-local cut points | Narr/Null | SS question | `indication_strength` is derived from `condition_score` by thresholds 0.4 / 0.6 stated only in the writer; `ga_vastu` grades the same score with 0.4 / 0.7. Whether a fixed-vocabulary grade is "narration" under the 2026-10-01 SS ruling (a composed string that states or grades a computed value) decides whether `prose_fields` is `["indication_strength"]` or `[]`; CF-20, CF-06. The NULL case returns `unknown` (an honest value, not an invented neutral) |
| brief: `prose_fields` undeclared | Null, Narr | real | declarations `prose_fields: null`; the writer forwards L0 text (`classical_citation`, dosha/organ lists) and falls back to a constant (`MEDICAL_GA_CITATION`, `:365`) — forwarded or constant text, not composed; candidate declaration depends on the grade question above; CF-06 |
| ga_medical-Build.history | Build | history | PARTIAL: 9 errors / 7 aborts; latest error 2026-07-16 `BLOCKED: upstream ga_condition did not complete` (a cascade); latest run `skip_no_delta` 2026-09-08; CF-10 |
| brief: undeclared L0 reads | Build.dag | information | `bg_medical_mappings` and `bg_nakshatra_medical` are read but not declared; L0 bedrock reads are exempt on main (SS 2026-10-01, provisional pending J1); CF-13 |
| brief: Dens (offline rev 4) | Dens | PASS | rev 4 reads PASS offline (one of three L1 assets that do): contract declared and a tier-carrying served select |
| ga_medical-Earn / Cost / Carr / Idem | Earn, Cost, Carr, Idem | detector / stale | CF-05, CF-07 (D1: the classical citation each row forwards vs the cited text; the mapping rows are L0's `bg_medical_mappings`); the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — a small, conformant, disclaimer-carrying asset whose census cells are PASS except the history record; the F-E5 W2 MUST fix is on main. The one question is the status of its graded label, an SS ruling.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Rule on the grade label, then declare `prose_fields`

- **Answers:** Null/Narr NO_DETECTOR; CF-06, CF-20
- **Change:** if SS rules the grade label narration: declare `["indication_strength"]` with writer evidence `ga_medical_writer.py` (`indication_strength_from_score`) and add a golden test of the three cut points (CF-15 pattern); else declare `[]` with evidence at `:365-381`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`; a test beside the writer tests
- **Failing-first test and mutation:** declarations validation; mutation: shift a threshold and the golden test fails
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only (+ test); **buildable before J1:** tier-independent once the ruling is made
- **Question for SS:** Is a fixed-vocabulary grade from a threshold "narration" for Null/Narr?

### FD-2 · One authority for the `condition_score` cut points

- **Answers:** CF-20
- **Change:** the 0.4/0.6 (medical) and 0.4/0.7 (vāstu) cut points are writer-local constants over the same score; declare one shared, cited cut-point set (where the score is defined: `ga_condition`) and read it from both writers, or record why the two scales differ (a medical vs a vāstu reading is a legitimate difference only if stated and sourced)
- **Files / declaration / migration:** `ga_medical_writer.py` (`indication_strength_from_score`), `ga_vastu_writer.py:52-67`; the authority location is SS's call
- **Failing-first test and mutation:** both writers grade a boundary score through the one authority; mutation: change a cut point once and both move
- **Output change:** none if the shared set equals today's values; yes if the two are reconciled
- **Blast radius:** none for data unless reconciled
- **Rebuild:** none unless values change (then REVIEW)
- **Gate it moves:** Narr/Null (the grading claim)
- **Fix class:** writer code; **buildable before J1:** tier-dependent: no tier defines the cut points
- **Question for SS:** Where do the condition-score cut points live?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-20** — Grade labels derived from `condition_score` with writer-local thresholds (ga_vastu 0.4/0.7, ga_medical 0.4/0.6): one authority for the cut points. *This asset:* FD-2: thresholds 0.4/0.6
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-1: undeclared; candidate depends on the ruling
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* L0 reads: exempt
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 9/7: cascade history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D1: forwarded classical citation
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PASS: one of three
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: none

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, graha)`; volatile: surrogate id, `computed_at`; array columns (`dosha_aggravated`, `organ_watch`, `body_part_watch`) are order-sensitive and should be fingerprinted sorted unless the order carries meaning (not read); the rows depend on `ga_condition_composite.condition_score` (a change upstream moves the grade).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the disclaimer fields (`indication_tier`, `not_diagnosis`), the L0-mapped dosha/organ/body-part lists and citations, the Moon nakṣatra body part, and the NULL → `unknown` honesty.
- **Carriage check chosen (T4 §4.1; one only):** D1 — each row forwards a classical citation from `bg_medical_mappings`; check the forwarded citation against the cited passage (L0 owns the corpus).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Is `indication_strength` (a threshold grade of a computed score) narration under the SS Null/Narr ruling?
2. Where should the `condition_score` cut points live, and may the vāstu and medical scales differ?
