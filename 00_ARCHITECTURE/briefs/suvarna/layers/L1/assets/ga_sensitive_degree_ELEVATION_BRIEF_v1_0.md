---
asset_id: ga_sensitive_degree
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
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-26, I-22]
ledger_gap_ids: [ga_sensitive_degree-Idem.pattern, ga_sensitive_degree-Earn.build_record, ga_sensitive_degree-Cost.baseline, ga_sensitive_degree-Complete.depth, ga_sensitive_degree-Build.history, ga_sensitive_degree-Carr.detector]
---
# ga_sensitive_degree — Sensitive-degree checks per graha (mṛtyu-bhāga, neecha-bhaṅga, kartarī, gaṇḍānta, …) and Yogi system

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Computes, per graha and ayanamsha, nine facets each by a cited classical rule (`ga_writers/ga_sensitive_degree_writer.py:1-45`): mṛtyu-bhāga (degree table delegated 1:1 from PyJHora constants), neecha-bhaṅga (reuses `ga_yoga_writer.detect_neecha_bhanga`), kartarī, Sarvatobhadra vedha, khareśvara, puṣkara, krānti (β = 0, flagged), gaṇḍānta, and a separate Yogi/Avayogi/Duplicate-Yogi/Sahayogi family. The Yogi family runs a two-pass function (`_yogi_point_two_pass`, `:427`; Avayogi `:449`) and stamps `two_pass_verified` or `divergent_flagged` from it (`:506-524`); the second pass re-evaluates the same formula in integer arcseconds (`:518-522`). Idempotency: `replace_prior_chart_facts`.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields undeclared (null) | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1249` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_sensitive_degree.py:8` (heavy: `build_ga_sensitive_degree_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (categories `sensitive_degree_check` and `sensitive_point_yogi`, `ga_sensitive_degree_writer.py:82,86`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 335 / 335 (Δ +0); `asset_throughput` lit / 335; seed floor literal 335 (derivation in the seed comment: (5 facets × 9 grahas + neecha_bhanga × 7 + 3 chart-level + 12 yogi) × 5) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions` (live and seed); the writer also reads the L0 table `reference_nakshatra` (`ga_sensitive_degree_writer.py:415`, MF-L1-006; L0 reads are exempt on main) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 0; census (2026-09-30, pre-1210): direct 0 / transitive 0; seed + 1210 reconstruction names 0 direct dependent(s): none | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_sensitive_degrees.ts:110` (declarations `read_evidence`); table-level 34 modules; declared dependents 0 / 0 | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | per-graha sensitive-degree facts the canon calls for (REMEDIATION_PLAN WP-2.5 / LCA-10); no declared L2+ consumer | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 4 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 15402831 complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 15402831 complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: reading_checklist.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree NO_DETECTOR; checkable NO_DETECTOR; fidelity_test NO_DETECTOR; lint NO_DETECTOR; schema_default NO_DETECTOR; blank_rows NO_DETECTOR.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: dual authority for the Yogi point (with `ga_sensitive`) | Vocab/Ldgr | SS question | see `ga_sensitive` gap 2: this asset's `sensitive_point_yogi` rows and `ga_sensitive`'s `esoteric_point_yogi_system` rows both state Sun + Moon + 93°20′; CLAUDE.md §N.5 |
| brief: seed `count_sql` lags the live registry | Count | information | migration 650 (F-B12) already set the live `count_sql` to `fact_category IN ('sensitive_degree_check', 'sensitive_point_yogi')` (`650_nirmana_l1_w3_registry_truth.sql:70-75`); only the seed literal (`asset_registry_seed.ts:1249-1262`) still counts one category; refresh the seed (CF-03); no migration is needed |
| brief: `prose_fields` undeclared although `citation_human` is composed | Null, Narr | real | declarations `prose_fields: null`; `_row(... citation ...)` writes `citation_human` (`:676-677`); candidate `["citation_human"]`; CF-06 |
| brief: second pass is the same formula | Carr/Earn | SS question | the Yogi two-pass compares Sun + Moon + 93°20′ in degrees against the same sum in integer arcseconds; this proves arithmetic consistency, not an independent method; CF-19 asks whether that earns `two_pass_verified` |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: referenced by code, no served SELECT attributable; CF-04, CF-18 |
| ga_sensitive_degree-Build.history | Build | history | PARTIAL: 0 errors / 4 aborts, latest run complete; CF-10 |
| brief: documented approximation | information | information | krānti uses β = 0 (celestial latitude is not in L1), flagged in the writer header (`:1-45`); the `documented_approximation` tier (1,020 `chart_facts` rows on the chart, layer instance §2.6) is where such rows would sit; not attributed to this asset |
| ga_sensitive_degree-Complete.depth / Earn / Cost / Carr / Idem | Complete, Earn, Cost, Carr, Idem | information / detector / stale | CF-18, CF-05, CF-07; the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — a sourced, deterministic set of per-graha facets (each rule cited, tables delegated to the library) with a real second-pass design on the Yogi family; every applicable census cell is PASS but the history record. The two questions (dual Yogi authority, what counts as a second pass) are SS rulings, not defects to fix unilaterally. No declared consumer is a valuation question, not a retirement reason in a contribution layer without an ablation instrument.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare `prose_fields` for `citation_human`

- **Answers:** CF-06
- **Change:** declare `["citation_human"]` with `evidence.prose_fields` citing `ga_sensitive_degree_writer.py:676-677` and the INSERT `:824-841`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** declarations validation; mutation as CF-06
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-2 · Refresh the seed `count_sql` to the live registry

- **Answers:** CF-03
- **Change:** set the seed `count_sql` to the two-category form migration 650 already applied to the live registry
- **Files / declaration / migration:** `platform/scripts/seed/asset_registry_seed.ts:1249-1262`
- **Failing-first test and mutation:** `scripts/__tests__/asset_registry_seed_dag_parity.test.ts` and the registry parity gate stay green
- **Output change:** none
- **Blast radius:** none (seed hygiene; an existing row is never rewritten by the seed)
- **Rebuild:** none
- **Gate it moves:** Count (information)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Yogi-point authority parity (with `ga_sensitive`)

- **Answers:** dual authority
- **Change:** an interim parity check of the two Yogi categories to the arcsecond; the authority decision is SS's
- **Files / declaration / migration:** read-only query / tooling
- **Failing-first test and mutation:** as `ga_sensitive` FD-2
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Vocab
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent for the parity check

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* FD-1: undeclared; candidate `["citation_human"]`
- **CF-19** — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8). *This asset:* the Yogi second pass: arithmetic consistency of one formula
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D3: the Yogi two-pass and the mṛtyu-bhāga table (delegated 1:1 from PyJHora constants: D1 against the cited text)
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 0/4: history
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline NO_DETECTOR: shared table
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* literals: status strings are computed (`"two_pass_verified" if ok else "divergent_flagged"`, `:508-524`): 7 quoted tier strings (indicative)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* not among the eight: no `_telemetry` call (LG-L1-001)
- **CF-03** — Registry correction batch (live registry vs seed literals: floors, edges, status) in one surgical migration plus seed literals. *This asset:* FD-2: seed `count_sql` lags migration 650
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of seven declared producers: `natural_key_partition` by migration 870; two-category `count_sql` by migration 650

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over `sensitive_degree_check` and `sensitive_point_yogi`; the per-graha facets are keyed by `(graha, facet)`. `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the nine cited facets with their delegated tables, the explicit β = 0 flag, and the earned-or-divergent Yogi stamp.
- **Carriage check chosen (T4 §4.1; one only):** D1 for the delegated mṛtyu-bhāga/puṣkara tables against their cited text, D3 for the Yogi point (a second derivation, once the independence question is ruled).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Which Yogi-point category is the authority (shared with `ga_sensitive`)?
2. Is re-evaluating one formula in integer arcseconds a second derivation for `two_pass_verified` (CF-19)?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-03: `ga_sensitive_degree` reads the Yogi point from `ga_sensitive` (bphs_93_20) instead of re-deriving it; its arithmetic re-check earns `classical_match`, not `two_pass_verified` (I-26).
- A-4: `check_gandanta` moves to the shared L0 module and is imported back (I-22).
