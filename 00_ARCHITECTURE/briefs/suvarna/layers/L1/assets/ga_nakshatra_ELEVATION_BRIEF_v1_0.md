---
asset_id: ga_nakshatra
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
ledger_gap_ids: [ga_nakshatra-Idem.pattern, ga_nakshatra-Earn.build_record, ga_nakshatra-Cost.baseline, ga_nakshatra-Complete.depth, ga_nakshatra-Build.history, ga_nakshatra-Carr.detector]
---
# ga_nakshatra — Nakṣatra chart, KP lords and cross-ayanamsha agreement (15 categories)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

A per-chart nakṣatra chart: static attributes JOINED from the L0 authority `bg_nakshatra` ("JOIN, cite, never restate"), KP sub-lord boundaries READ from `bg_kp_sublord_division` (never re-derived), gaṇḍānta flags, dispositor graph, tārā-bala, statistics, KP significators, and a cross-ayanamsha agreement category (`ga_nakshatra.py:1-12`). It is the best-conformed L1 writer on the verification tier: it imports `UNVERIFIED_DEFAULT`, `assert_legal` and `two_pass_verdict` (`:25`) and computes a real second pass (`compute_cross_ayanamsha_agreement`, `:143-147`, int-coercion kept at the call site by design). Idempotency: `replace_prior_chart_facts(ctx.db_conn, all_rows)` (`:353`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1452` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py:393` (heavy: five ayanamsha substeps + one cross-ayanamsha step; the module is the writer: 532 lines; emitters in `ga_nakshatra_emitters.py`, `ga_nakshatra_compute.py`, `ga_kp_significators.py`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (15 fact categories; migration 878 corrected the module's category list; `natural_key_partition` set by migration 872) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 2,847 / 1,813 (Δ +1,034); `asset_throughput` lit / 2,847; seed floor literal 1813 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `bg_nakshatra`, `ga_positions`, `bg_kp_sublord_division` (live and seed) | layer instance §2.5 |
| blast radius | census (pre-1210): direct 4 / transitive 56; seed + migration 1210 reconstruction names 3 direct dependent(s): `bo_laksana`, `ga_sade_sati`, `ga_structural` | census `blocking_radius`; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry in either direction) |
| code readers / served surface | `get_nakshatra.ts:91` (declarations `read_evidence`) and `platform-mcp/src/lib/kp_school_voice.ts`; table-level 34 modules; 4 direct / 56 transitive dependents (`ga_structural`, `ga_sade_sati` among them) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | nakṣatra, pada and KP foundation (layer instance §2.4 row 3.8); the L0 authorities are joined and cited, never restated | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 5 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-07): provenance receipt: output digest spec where_in values must be unique and sorted |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a1702479 complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a1702479 complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L1/rollup_saved_L1.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 1 serving-root file(s) naming chart_facts lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/registry_bridge.ts; its served select and density_contract cannot be read — never FAIL, nev… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`/Users/Dev/suvarna-evidence/A_L1/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PASS; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_nakshatra-Build.history | Build | history | PARTIAL: 1 error / 5 aborts; latest error 2026-09-07 `provenance receipt: output digest spec where_in values must be unique and sorted` (`output_digest.py`; migration 889 is the ga_nakshatra output-digest spec); the latest run completed; CF-10 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared (`citation_human`, composed at `ga_nakshatra.py:215`); offline Narr.agree PASS, Narr.lint PASS, Narr.fidelity_test PARTIAL (tests do not name the declared field); CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: referenced by code, no served SELECT found for the asset's own partition (offline Dens re-scan, §1) — shared table; CF-04, CF-18 |
| brief: undeclared reads | Build.dag | information | the writer imports `brahmagyan.l0_kp_sublord_division.load_divisions` (`:36`, L0 bedrock) and reads `bg_nakshatra`; both are declared edges (`bg_nakshatra`, `bg_kp_sublord_division`); L0 reads are exempt on main (SS 2026-10-01) so no change is owed |
| ga_nakshatra-Complete.depth | Complete | information | `salience_formula_ver` never populated (whole table); CF-18 |
| ga_nakshatra-Carr.detector | Carr | detector | a real D3 pass exists in the writer (`two_pass_verdict`); the census cannot read it; CF-07 |
| ga_nakshatra-Idem.pattern | Idem | stale | the earlier skeleton's PARTIAL (ON CONFLICT) is gone at inspector 2a78ec64d (TG-L1-006); census reads PASS (`_idempotency.py`); CF-12 |
| ga_nakshatra-Earn / Cost | Earn, Cost | detector | CF-05 |

## 3 · Disposition

**keep (P)** — every applicable census cell is PASS except the history record; the asset already carries a real second derivation and joins its L0 authorities instead of restating them. The open items are detectors and one test that names the declared prose field. (The W2 serving findings F-B18/F-B19 appear in code comments on main; not re-verified here.)

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carr D3 reader for the existing cross-ayanamsha pass

- **Answers:** Carr NO_DETECTOR; CF-07
- **Change:** a detector that reports, per claim, the share of rows stamped `two_pass_verified` by `two_pass_verdict` (agreement of the engine value with the independently derived value) and PASSES only on that subset; divergent rows (`divergent_flagged`) are listed, never passed
- **Files / declaration / migration:** Track E inspector tooling
- **Failing-first test and mutation:** seed a divergent copy; it must be listed; mutation: coerce both values to equal and the detector must show the lost evidence (call sites with identical arguments are greppable, `verification_vocab.py:268-273`)
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset assignment (TGH-T3-02)

### FD-2 · Narr golden test naming `citation_human`

- **Answers:** Narr.fidelity_test PARTIAL; CF-15
- **Change:** assert the exact sentence for one nakṣatra join row and one KP-lord row of the canonical chart (Moon in Purva Bhadrapada is a FORENSIC anchor)
- **Files / declaration / migration:** a test beside the existing ga_nakshatra tests
- **Failing-first test and mutation:** mutation: change the pada in the composed string and the test fails
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-2: declared; fidelity PARTIAL
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-1: D3 exists in code
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 1/5: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: partition-scoped `count_sql`; `natural_key_partition` by migration 872 (+878 for `nakshatra_cross_ayanamsha`)
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: already declared `["citation_human"]`
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* conformant: uses `UNVERIFIED_DEFAULT`/`two_pass_verdict`; the model for CF-17
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the 15 categories; volatile columns as `ga_positions`; the KP sub-lord rows depend on `bg_kp_sublord_division` (L0): a fingerprint across an L0 change is expected to move.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the L0-joined static attributes (never restated), the KP significator emitters that read the L0 boundary authority, and the cross-ayanamsha two-pass comparison.
- **Carriage check chosen (T4 §4.1; one only):** D3 — a second derivation already exists (`compute_cross_ayanamsha_agreement` / `two_pass_verdict`); D1 for the KP boundaries is L0 `bg_kp_sublord_division`'s own check (its brief).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Is `two_pass_verified` from `two_pass_verdict` (an agreement of two ayanamsha-independent derivations) sufficient evidence for the L1 D3 reading, with divergent rows listed?
