---
asset_id: ga_transit_anchors
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
disposition_proposal_approver: "Steward (G16); the integration question goes to SS if raised"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-34]
ledger_gap_ids: [ga_transit_anchors-Earn.build_record, ga_transit_anchors-Cost.baseline, ga_transit_anchors-Build.history, ga_transit_anchors-Carr.detector]
---
# ga_transit_anchors — Natal anchors for gochara (natal sign, house from Moon, absolute degree)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

For each ayanamsha, deletes `(chart_id, ayanamsha_id)` then inserts, per graha, the natal sign, `natal_house_from_moon` and `natal_degree_absolute` read from `chart_facts` (the `ga_positions` rows) (`ga_transit_anchors.py:1-12, 182-215`). It refuses partial output ("refusing partial/house-1 fallback output", `:176-181`), and for the canonical chart asserts Moon's nakṣatra = Pūrva Bhādrapadā — the ayanamsha-invariant anchor — after the F-D22 fix replaced a sign-based assertion that was build-fatal under `surya_siddhanta_classical` (`:12-16, 145-160`). The table carries no verification-tier column, no citation column and no source `fact_id` back to the `ga_positions` rows it restates.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1585` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_transit_anchors.py:77` (heavy: one substep per ayanamsha; the module is the writer: 226 lines, no `ga_writers/` module); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_transit_anchors` (own table; 9 grahas × 5 ayanamshas = 45 rows) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 45 / 45 (Δ +0); `asset_throughput` lit / 45; seed floor literal 45 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions` (live and seed) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 0; census (2026-09-30, pre-1210): direct 0 / transitive 0; seed + 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_transit_anchors.ts:74` (declarations `read_evidence`) and `platform-mcp/src/tools/register_p1_ganita.ts`; no L2–L5 asset declares an edge; no other writer reads the table (grep of `python-sidecar`, `src`, `platform-mcp/src`) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | event-time/transit foundation (layer instance §2.4 row 3.10, DP07 clocks); W2 recorded "zero data-plane consumers" (F-D23) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 6 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 54ba6f77 complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 54ba6f77 complete/build (2026-09-07) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Complete.depth; Vocab.identity; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 8/9 built column(s) (88.9%) selected by 1 capability module(s); dark: ['build_id']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 1 module(s) reach it by code: L1_ganita/get_transit_anchors.ts; a referencing capability declares density_contract but L1_ganita/get_transit_anchors.ts: no tier column in its served select (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: restated facts carry no lineage | Ldgr | real | the table restates `chart_facts` position facts (sign, absolute degree) and derives `natal_house_from_moon` from them, but stores no `source_fact_id`/`fact_id` and no tier; CLAUDE.md B.3 / §N.5 ("a signal never restates an L1 value as its own truth: it references the L1 `fact_id`"); census Ldgr has no cell for it (MF-L1-003); CF-08 |
| ga_transit_anchors-Build.history | Build | history | PARTIAL: 0 errors / 6 aborts, latest run complete; CF-10 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_transit_anchors.ts` has no tier column in its served select (the table has none); CF-04 |
| brief: no consumer beyond the served tool | value | SS question | no writer or declared asset reads the table; a join of facts already in `chart_facts` with 0/0 radius; consolidate/integrate needs a proven shared authority (T2 §10.1) and is SS's ruling, not made here |
| brief: Null/Narr | Null, Narr | detector | no prose column in the INSERT (`:200-215`: only numeric/relational columns); declaration `prose_fields: null`; a positive `[]` declaration with writer evidence `:200-215` is candidate; CF-06 |
| ga_transit_anchors-Earn / Cost / Carr | Earn, Cost, Carr | detector | CF-05, CF-07 (D3: recompute `house_from_moon` from the stored signs by the 1-based modular rule) |
| ga_transit_anchors-Idem.pattern | Idem | stale | census PASS (`DELETE … WHERE chart_id, ayanamsha_id` then INSERT, `:183-188`) |

## 3 · Disposition

**keep (P)** — a small, deterministic table whose writer is conformant (delete-then-insert, FORENSIC assertion fixed, refuses partial output). Its value is the served tool and the tier-named transit foundation; "no declared consumer" is not a retirement reason without an ablation instrument (layer instance §1.5). The real gap is lineage, a declaration/column fix.

Approver under Track A brief §10: **Steward (G16); the integration question goes to SS if raised**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carry the source facts (lineage) for the restated positions

- **Answers:** brief gap "no lineage"; B.3 / §N.5; CF-08
- **Change:** add a `source_fact_ids` (array of `chart_facts.fact_id` for the sign and degree rows used) column and write it in the INSERT; or, if SS prefers, record the lineage in the declarations file as `carriage` and leave the table unchanged
- **Files / declaration / migration:** a migration adding the column (additive; number = max+1 at execution time), `ga_transit_anchors.py:194-215` (SELECT the `fact_id`s; INSERT), the data-plane field mapping if `ga_transit_anchors` is in `CONTRACTED_L1_ASSETS` (it is, `ga_writers/data_plane_runtime.py`) — not re-read for the column list
- **Failing-first test and mutation:** failing-first: every row's `source_fact_ids` resolve to existing `chart_facts` rows of the same chart and ayanamsha; mutation: point one at another chart and the resolution test fails
- **Output change:** yes: an additive column (SS approval, R5, because it changes the table)
- **Blast radius:** the served tool `get_transit_anchors.ts` selects explicit columns (not re-read for `SELECT *`); no other reader
- **Rebuild:** **needs production rebuild** of the asset (45 rows) after the migration: REVIEW
- **Gate it moves:** Ldgr (no reading → measured)
- **Fix class:** data (output change) + migration + writer code; **buildable before J1:** tier-dependent: TGH-T3-01 (the Ldgr source definition for an L1 asset) and TG-L1-021
- **Question for SS:** Lineage by a new `source_fact_ids` column, by a declaration only, or by integrating the asset into `chart_facts`?

### FD-2 · Declare `prose_fields: []` with writer evidence

- **Answers:** Null/Narr NO_DETECTOR; CF-06
- **Change:** declare `[]` with `evidence.prose_fields` = `ga_transit_anchors.py:200-215` (the INSERT binds no text column except `graha`, `natal_sign`, `ayanamsha_id`)
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation: add a composed text column and Narr.agree must flag it
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Carr D3: recompute `natal_house_from_moon` from the stored signs

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** a detector recomputing `((planet_sign − moon_sign) mod 12) + 1` from `chart_facts` signs and comparing to the stored value for all 45 rows
- **Files / declaration / migration:** Track E inspector tooling
- **Failing-first test and mutation:** a seeded wrong house must be reported
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: TGH-T3-02

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* FD-1: no `Ldgr` cell and no lineage column
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-2: candidate `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-3: D3
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 0/6: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: contract without tier column
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: no `_telemetry` call
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: `(chart_id, ayanamsha_id)` exact — no orphan risk beyond a removed ayanamsha
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, graha)`; volatile: `build_id` and any surrogate id/timestamp (columns not read in full); the per-row values are pure functions of the `ga_positions` rows, so the fingerprint moves exactly when those do.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 45-row natal anchor set, the refusal of partial output and the nakṣatra-based FORENSIC assertion.
- **Carriage check chosen (T4 §4.1; one only):** D3 — recompute house-from-Moon from the stored signs.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Lineage by a new `source_fact_ids` column, a declaration only, or integration into `chart_facts`?
2. Is a table with no declared consumer beyond a served tool retained as capital (reference-layer rule does not apply to L1)?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-13 accepted, OPTIONAL: stored `source_fact_ids` column written from the rows the writer read; served tool reads it (I-34). Rides S-L1 only if ready.
