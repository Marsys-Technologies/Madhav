---
asset_id: ga_vastu
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
ledger_gap_ids: [ga_vastu-Idem.pattern, ga_vastu-Earn.build_record, ga_vastu-Cost.baseline, ga_vastu-Build.history, ga_vastu-Carr.detector]
---
# ga_vastu — Vāstu planet–direction map with a condition-based direction impact

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Maps each classical graha to its ruling Vāstu direction (Mayamata Ch. 6; Bṛhat Saṃhitā Ch. 53) and grades a `direction_impact` from the graha's `condition_score` in `ga_condition_composite` (`ga_writers/ga_vastu_writer.py:1-20`). The mapping is a writer-local dict `GRAHA_TO_DIRECTION` (`:36-45`, Ketu omitted) and the citation a literal `VASTU_CITATION` (`:47`); `compute_direction_impact` returns `weakened` (< 0.4), `neutral` (0.4–0.7), `strengthened` (≥ 0.7) and **`neutral` when the score is NULL** (`:52-67`). Idempotency: `DELETE WHERE (chart_id, ayanamsha_id)` then INSERT (`:95`, `:135`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1526` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_vastu.py:13` (heavy: `build_ga_vastu_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_vastu_planet_direction_map` (own table; up to 9 × 5 = 45 rows; Ketu skipped) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 40 / 40 (Δ +0); `asset_throughput` lit / 40; seed floor literal 40 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_condition` (live and seed); it does not declare the L0 table `bg_vastu_directions` it should be reading | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 0; census (2026-09-30, pre-1210): direct 0 / transitive 0; seed + 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_vastu_directions.ts:98` (declarations `read_evidence`; contract declared); W2 F-E10/F-E11 (zero routed consumers; L1 directions not joined to L0's 24 per-direction remedies) are addressed on main: a vidhi primitive gives the surface a planner-citable face and the serving surface is joined to the L0 remedies (`platform/src/lib/vidhi/registry_data.ts:695-705`); floor-forced inclusion awaits a property-domain floor (a shared retrieval-plane change outside this asset); declared dependents 0 / 0 | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | vāstu application (layer instance §2.4); `indication_tier = 'traditional_vastu'` | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 10 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-08): post-write integrity check failed: integrity_check_sql → False |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0b0901df complete/build (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0b0901df complete/build (2026-09-08) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 9/11 built column(s) (81.8%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PASS** — STRUCTURAL: 2 module(s) reach it by code: L1_ganita/get_vastu_directions.ts, platform-mcp/src/tools/register_p1_aliases.ts; 1 capability(ies) declare density_contract AND select a tier column from it (indication_tier) in: L1_ganita/get_vastu_directions.ts (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: wrapper-local constant shadows the L0 authority (Nirmāṇa F-E12, still open) | Ldgr/Vocab | real | `GRAHA_TO_DIRECTION` (`ga_vastu_writer.py:36-45`) duplicates the L0 table `bg_vastu_directions` (`brahmagyan/l0_vastu_directions.py`: 8 rows with `ruling_graha`); the two agree on all eight pairs today (North Mercury, South Mars, East Sun, West Saturn, Northeast Jupiter, Southeast Venus, Northwest Moon, Southwest Rahu; read from the seed module), so the defect is the shadow (CLAUDE.md §N.7 item 3: a constant can drift from its source; a reference cannot), not a wrong value |
| brief: NULL score becomes `neutral` (an invented judgment) | Null | real | `compute_direction_impact(None)` returns `"neutral"` (`:52-67`); the sibling `ga_medical` returns `unknown` for the same input. CLAUDE.md §N.7 item 6: an honest null beats an invented judgment; `neutral` here is chosen for how it reads. Whether any live row is affected is not measured (ga_condition scores are present for 135 rows) |
| brief: writer-local cut points (with `ga_medical`) | Narr/Null | SS question | thresholds 0.4 / 0.7 here vs 0.4 / 0.6 in `ga_medical` over the same score; CF-20 |
| brief: `prose_fields` undeclared | Null, Narr | detector | declarations `prose_fields: null`; the writer composes no free text (a label from a threshold, a constant citation); candidate `[]` or `["direction_impact"]` depending on the same grade ruling as `ga_medical`; CF-06 |
| ga_vastu-Build.history | Build | history | PARTIAL: 10 errors / 7 aborts; latest error 2026-09-08 `post-write integrity check failed` (the integrity contract, migration 741, passed on live production when written); CF-10 |
| brief: Dens (offline rev 4) | Dens | PASS | rev 4 reads PASS offline (one of three L1 assets that do) |
| ga_vastu-Carr / Earn / Cost / Idem | Carr, Earn, Cost, Idem | detector / stale | CF-05, CF-07 (D1: the mapping against the cited text — the corpus lacks Mayamata, L0 question 18); the Idem ledger row is stale (census PASS) |
| ga_vastu (no cell) | Ldgr | information | `Ldgr.source_presence` reads PASS on `classical_citation` (a constant string on every row) |

## 3 · Disposition

**keep (P)** — a small conformant asset whose real defects are two §N.7 items (a shadow constant, an invented neutral); both are code fixes with no stored-value change in the first case. The W2 consumer findings (F-E10/E11) are already addressed on main (vidhi primitive, join to the L0 remedies).

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Read the direction map from the L0 table

- **Answers:** brief gap F-E12; CLAUDE.md §N.7 item 3
- **Change:** replace `GRAHA_TO_DIRECTION` with a read of `bg_vastu_directions.ruling_graha` (8 rows), keep Ketu omitted by rule, and cite through the table's own source field instead of `VASTU_CITATION` where the table carries one; add a golden test that the eight pairs equal today's dict so no stored value changes
- **Files / declaration / migration:** `ga_writers/ga_vastu_writer.py:36-47, 95-145`; the edge to `bg_vastu_directions` is L0 bedrock (exempt on main), so `depends_on` need not change; a registry note only
- **Failing-first test and mutation:** failing-first: delete a row from a fixture `bg_vastu_directions` and the build must fail loudly (not fall back to the dict); mutation: change a `ruling_graha` and the output moves
- **Output change:** none (the eight pairs are identical today)
- **Blast radius:** none (0/0); the served tool `get_vastu_directions.ts` is unchanged
- **Rebuild:** none required; the writer source hash changes (a no-delta skip is expected where the output digest is unchanged: not verified)
- **Gate it moves:** Ldgr, Vocab (no shadow constant)
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-2 · Return NULL, not `neutral`, when the score is missing

- **Answers:** brief gap "invented neutral"; §N.7 item 6
- **Change:** `compute_direction_impact(None)` → `None` (the column must allow NULL; check the table DDL, migration 286) or a named `unknown` state, and make the integrity contract (migration 741, direction vocabulary conjunct) accept it
- **Files / declaration / migration:** `ga_vastu_writer.py:52-67`; migration 286/741 only if the vocabulary check forbids it
- **Failing-first test and mutation:** failing-first: a missing score yields NULL/`unknown`; mutation: restore `neutral` and the test fails
- **Output change:** only for rows built with a missing score (none known)
- **Blast radius:** none (0/0)
- **Rebuild:** none unless such rows exist (a small rebuild, 40 rows: REVIEW)
- **Gate it moves:** Null
- **Fix class:** writer code; **buildable before J1:** tier-independent

### FD-3 · One authority for the cut points (with `ga_medical`)

- **Answers:** CF-20
- **Change:** see `ga_medical` FD-2
- **Files / declaration / migration:** `ga_vastu_writer.py:52-67`
- **Failing-first test and mutation:** as ga_medical
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none unless values change
- **Gate it moves:** Narr/Null
- **Fix class:** writer code; **buildable before J1:** tier-dependent
- **Question for SS:** Where do the condition-score cut points live?

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-20** — Grade labels derived from `condition_score` with writer-local thresholds (ga_vastu 0.4/0.7, ga_medical 0.4/0.6): one authority for the cut points. *This asset:* FD-3: 0.4/0.7
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declaration: candidate `[]` or `["direction_impact"]`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 10/7: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PASS: one of three
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* L0 read to declare/exempt: `bg_vastu_directions` (bedrock)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D1: mapping vs cited text
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: none

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, graha)`; volatile: surrogate id, `computed_at`; `direction_impact` depends on `ga_condition_composite.condition_score` (a change in `ga_condition` moves it).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the graha → direction rule with Ketu omitted by classical silence, the `indication_tier` constant, and the condition-based impact.
- **Carriage check chosen (T4 §4.1; one only):** D1 — the graha–direction mapping against the cited Vāstu passages (Mayamata is not in the corpus: L0 question 18).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Where do the `condition_score` cut points live, and may `ga_vastu` and `ga_medical` differ?
2. Is a NULL-score row better stored as NULL or as a named `unknown` state (the sibling `ga_medical` uses `unknown`)?
