---
asset_id: ga_prashna
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16); any enrichment or go-live is SS (and the native's R-1)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS"
track_i_items: []
ledger_gap_ids: [ga_prashna-Idem.pattern, ga_prashna-Earn.build_record, ga_prashna-Cost.baseline, ga_prashna-Complete.depth, ga_prashna-Vocab.identity, ga_prashna-Build.history, ga_prashna-Carr.detector]
---
# ga_prashna — Praśna (horary) lagna and judgment — dormant by native ruling R-1

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

For each ayanamsha: if `chart_id` is in `prashna_charts`, read `question_class` and `prashna_lagna_method`, read the prashna chart's positions (`ga_positions`), read `bg_prashna_significators` for the class, decide the faster of querent/quesited, compute Ithasala/Eesarpha and fructification timing, and store `ga_prashna_lagna` and `ga_prashna_judgment` (`ga_writers/ga_prashna_writer.py:1-22`); on a natal chart it returns 0 rows (the docstring, `:9-10`; wrapper `ga_prashna.py:12`). The registry records the dormancy: migration 650 PART 5 set `data_disposition = 'RETAINED_AS_CAPITAL'` and a `volume_explanation` reading "DORMANT BY DESIGN (native ruling R-1 …) 0 rows is the CORRECT outcome … Do not 'fix' the zero count"; migration 651 removed 5 orphaned served rows and added a real FK to `charts`. Idempotency: `DELETE WHERE chart_id, ayanamsha_id` then INSERT.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1565` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_prashna.py:7` (heavy: one substep per ayanamsha; early returns 0 rows if the chart is not a prashna chart); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_prashna_judgment` and `ga_prashna_lagna` (count_sql total over both; `data_disposition = RETAINED_AS_CAPITAL`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | **0** / 0 (floor 0 declares zero rows complete); `asset_throughput` lit / 0 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `bg_prashna_rules` (live and seed) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 0; census (2026-09-30, pre-1210): direct 0 / transitive 0; seed + 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_prashna_lagna.ts` (served; contract declared) and `platform-mcp/src/tools/register_p1_synthesis.ts:1011` selecting 1 of 17 columns of `ga_prashna_lagna` (census reach 5.9%); the MCP tool `prashna_undertaking_get` reads `ga_prashna_judgment` (W2 §4); declared dependents 0 / 0 | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the horary facility: question-moment charts only (`prashna_charts`); a natal build legitimately writes 0 rows | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | PARTIAL | rows_written=0 = live=0 (count_sql total over 2 table(s): ga_prashna_lagna, ga_prashna_judgment; chart 482012f1); target_floor=0 declares zero rows complete, but this is a writer-backed data asset (has_writer=true) with no layer-plan claim that the emptiness is by design — indistinguishable from a writer that has never produced… |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 6 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 9a9e4bf3 complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 9a9e4bf3 complete/build (2026-09-07) |
| Count | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=0) |
| Complete | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 17 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (chart_id, ayanamsha_id) is vacuous on 0 rows |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 1/17 built column(s) (5.9%) selected by 1 capability module(s); dark: ['ayanamsha_id', 'classical_citation', 'fructification_rule_id', 'fructification_unit', 'fructification_value', 'id', 'is_applying', 'judgment_text', 'lagna_ras…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 1 module(s) reach it by code: L1_ganita/get_prashna_lagna.ts; a referencing capability declares density_contract but L1_ganita/get_prashna_lagna.ts: no tier column in its served select (the saved rev-1 reading was N/A); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| census: Build.completion PARTIAL (rows_written 0 = live 0, "emptiness not declared by design") | Build | detector | the claim is already machine-recorded in the registry (`data_disposition`, `volume_explanation`, migration 650:156-177) but the inspector does not read it and no N-22 rule exists (`NA_RULE_DECISIONS` is empty on main; TG-L1-008 "empty by design" is not a declarable state); the cell is a detector/definition gap, not a build failure; CF-18 |
| ga_prashna-Complete.depth / ga_prashna-Vocab.identity | Complete, Vocab | detector | NO_DETECTOR because the tables are empty for the canonical (natal) chart: uniqueness and column population cannot be measured on 0 rows; a measurement needs a prashna chart |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_prashna_lagna.ts` has no tier column in its served select (saved rev-1 reading N/A: "0 modules"; the census `reach.modules` already listed one MCP reader); CF-04 |
| brief: no machine-readable "applies only to question-moment charts" | Build/Carr | SS question | correctness of the judgment cannot be measured on the canonical chart at all (no prashna chart); a measurement needs a declared test prashna chart and is outside the R-1 dormancy (go-live rehearsal is on the deferred register, NIRMANA plan §7.3) |
| ga_prashna-Build.history | Build | history | PARTIAL: 0 errors / 6 aborts, latest run complete; CF-10 |
| brief: Null/Narr | Null, Narr | detector | `classical_citation` is composed (`ga_prashna_writer.py:273`); declaration `prose_fields: null`; candidate `["classical_citation"]` (the composed column is not `citation_human`); CF-06 |
| ga_prashna-Idem.pattern / Earn / Cost / Carr | Idem, Earn, Cost, Carr | stale / detector | Idem ledger row stale (census PASS: `DELETE … WHERE chart_id, ayanamsha_id`); CF-05, CF-07 |

## 3 · Disposition

**qualify (Q)** — the native ruling R-1 keeps the facility dormant and recorded; the asset is retained capital with a conformant writer whose natal-chart output is correctly empty. It is neither a build failure nor a candidate for retire/consolidate without the native's decision. The disposition qualifies it: valid and measurable only for question-moment charts.

Approver under Track A brief §10: **Steward (G16); any enrichment or go-live is SS (and the native's R-1)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make "empty by design (R-1)" a declared state the inspector can read

- **Answers:** Build.completion PARTIAL; TG-L1-008; Complete/Vocab NO_DETECTOR on an empty table
- **Change:** SS rules an N-22 rule keyed to the registry fact the migration already recorded (`data_disposition = RETAINED_AS_CAPITAL` together with a declared "dormant" reason), so that Build.completion reads N/A with a decision id for a writer-backed asset that is deliberately unbuilt; the Complete/Vocab cells read N/A for the same cause. Nothing about the writer or the facility changes
- **Files / declaration / migration:** the inspector rule table / declarations file (Track E; `NA_RULE_DECISIONS` in `platform/scripts/governance/asset_census.py:243`) — no asset file
- **Failing-first test and mutation:** failing-first: an asset with the declared state and 0 rows reads N/A (decision id); an asset without it and 0 rows stays PARTIAL; mutation: remove the declaration and the cell flips back
- **Output change:** none
- **Blast radius:** none for the asset (census inputs only)
- **Rebuild:** none
- **Gate it moves:** Build (completion), Complete, Vocab
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: N-22 per-gate applicability rules; TG-L1-008
- **Question for SS:** Is a registry-recorded dormancy a sufficient basis for a Build.completion N/A rule?

### FD-2 · Declare `prose_fields` for `classical_citation`

- **Answers:** CF-06
- **Change:** declare `["classical_citation"]` with writer evidence `ga_prashna_writer.py:273` and the INSERTs `:314,:337`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation as CF-06
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* FD-1: empty-table cells
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-2: candidate `["classical_citation"]`
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 0/6: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: tier column absent
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* no Ldgr cell: one of six L1 assets with no `Ldgr.source_presence` reading (MF-L1-003)
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: none
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* NO_DETECTOR: D3 needs a prashna chart; outside R-1

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id[, lagna_method])` for `ga_prashna_lagna` and `(chart_id, ayanamsha_id)` for `ga_prashna_judgment` (keys not read in full); on a natal chart the fingerprint of both tables is the empty set and must stay empty; volatile: `build_id`, `computed_at`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the facility as retained capital: writer, cast module (`ga_prashna_cast.py`), L0 `bg_prashna_rules` joins, the early-return for natal charts, and the R-1 registry record.
- **Carriage check chosen (T4 §4.1; one only):** NO_DETECTOR with reason: carriage cannot be checked on the canonical chart (no prashna chart); D1 against `bg_prashna_rules` once a test prashna chart is declared (outside R-1).
- **Opportunities (never blocking):** go-live rehearsal with its 7 named prerequisites is on the deferred register (NIRMANA plan §7.3) — not a Suvarṇa item.

## 7 · Questions for Strategic Suvarṇa

1. Is a registry-recorded dormancy (`data_disposition = RETAINED_AS_CAPITAL` + R-1 reference) the basis for an N-22 N/A rule on Build.completion/Complete/Vocab?
2. Is `qualify` the right disposition letter for a facility that is valid only for question-moment charts and dormant by native ruling?
