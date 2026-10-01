---
asset_id: ga_positions
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
ledger_gap_ids: [ga_positions-Idem.pattern, ga_positions-Earn.build_record, ga_positions-Cost.baseline, ga_positions-Complete.depth, ga_positions-Build.history, ga_positions-Carr.detector]
---
# ga_positions — Natal graha positions per ayanamsha (the L1 root)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Per-chart, per-ayanamsha graha positions: 5 canonical ayanamshas × 9 grahas + Lagna, one atomic row per fact key (longitude, sign, nakshatra, pada, house), with dual citations (`citation_ref`, `citation_human`) on every row, written to `chart_facts` (`ga_writers/ga_positions_writer.py:1-20`). Computation is delegated to `pyjhora_adapter.compute.compute_chart` (`:29`); a FORENSIC gate (`forensic_gate`, `:163`; Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries) must pass before any insert; idempotency is `replace_prior_chart_facts(conn, rows)` (`:533`, `_insert_chart_facts_rows`) over the categories present in the rows about to be written.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1076` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_positions.py:4` (`run`, light); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (partition: `graha_position`, `graha_sign_attributes`, `bhava_cusps`, `house_chalit`, `sandhi_flag`, per the seed `count_sql`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 1,205 / 1,205 (Δ +0); `asset_throughput` lit / 1,205; seed floor literal 1205 (matches) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | none (layer root) | layer instance §2.5 |
| blast radius | census (pre-1210): direct 31 / transitive 79; seed + migration 1210 reconstruction names 19 direct dependent(s): `bo_karanajala`, `bo_laksana`, `ga_condition`, `ga_dashas`, `ga_medical`, `ga_nakshatra`, `ga_panchanga`, `ga_prashna`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_transit_anchors`, `ga_vargas`, `ka_sangam`, `ka_vighnakara`, `mi_adhilepa`, `ph_muhurta` | census `blocking_radius`; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry in either direction) |
| code readers / served surface | table-level: 39 capability modules read `chart_facts`, 34 attributed in `Dens.served` (identical for the seven declared producers, MF-L1-002); asset-specific read `platform/src/lib/retrieval/registry/layers/L1_ganita/get_positions.ts:193` (declarations `read_evidence`); 11 of 24 built `chart_facts` columns are dark (selected by no module) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the root every other L1 and most L2-L5 assets stand on (layer instance §2.5: 31 direct / 79 transitive); supplies what manifestation and time rest on | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.history | FAIL | most recent run aborted (2026-09-19); 1 error(s), 5 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-09-05): provenance: Object of type UUID is not JSON serializable |
| Build | Build.dep_liveness | N/A | no declared dependencies |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0ac321ee complete/skip_no_delta (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0ac321ee complete/skip_no_delta (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 421096 rows, 25 cols; fully populated 17; NEVER populated ['salience_formula_ver'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Build.completion; Count.floor; Vocab.identity; Ldgr.source_presence; Dens.served †; Build.exercised.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 13/24 built column(s) (54.2%) selected by 39 capability module(s); dark: ['build_id', 'chart_id', 'citation_human', 'computed_at', 'cross_ayanamsha_divergence_arcsec', 'engine_version', 'near_nakshatra_boundary_flag', 'near_sign_b…; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L1/rollup_saved_L1.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 1 module(s) reach it by code: reading_checklist.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`/Users/Dev/suvarna-evidence/A_L1/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint NO_DETECTOR; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_positions-Build.history | Build | history | FAIL: most recent run aborted (2026-09-19); 1 error (2026-09-05 `provenance: Object of type UUID is not JSON serializable`, fixed by #1861 per `git log` of `pipeline/orchestrator/provenance.py:27`), 5 aborts. The abort cause is not in the census; no edit changes a history record; CF-10 |
| brief: verification tier written as bare literal `"single"` | Vocab/Earn | real | `ga_positions_writer.py:343, 393, 426` emit `"verification_pass_status": "single"`; CLAUDE.md §N.4 requires `verification_vocab.UNVERIFIED_DEFAULT`; only `ga_dashas` has a guard test (`tests/test_ga_dashas_f_a17_bare_tier_literals.py`); CF-17 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared prose field `citation_human` composed at `ga_positions_writer.py:132, 469, 487`; offline Narr.fidelity_test PARTIAL: 3 test files call the builder and assert in the same test function but nothing shows the sentence is graded (`test_bhava_chalit.py`, `test_ga3_writers.py`, `test_ga_orchestrator_conformance.py`); CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: `chart_facts` is shared by the seven declared producers, so the served surface cannot be attributed to this asset; saved rev-1 PASS was a table-level reading; CF-04, CF-18 |
| brief: legacy `_telemetry` call site | Earn | information | `ga_positions_writer.py:693` calls `update_asset_throughput` under `owns_conn` (`:667`); the orchestrated wrapper passes `conn=ctx.db_conn` (`ga_positions.py:33`) so by code reading it does not execute under the orchestrator; CF-14 |
| ga_positions-Complete.depth | Complete | information | `salience_formula_ver` never populated over the whole 421,096-row `chart_facts` (all charts); attributed identically to every producer; CF-18 |
| ga_positions-Earn.build_record / Cost.baseline / Carr.detector | Earn, Cost, Carr | detector | instrument absent (CF-05); no D1/D2/D3 detector (CF-07) |
| ga_positions-Idem.pattern | Idem | stale | ledger row says no pattern found in the writer's own SQL; the saved census reads PASS via `_idempotency.py:66` (delegated delete). CF-12 records what the static PASS does not test |
| census: Null/Narr (declarations) | Null, Narr | detector | declared `prose_fields: ["citation_human"]` (declarations 1.6.0); Null.blank_rows and Narr.checkable INCONCLUSIVE until row data is read |

## 3 · Disposition

**keep (P)** — every applicable census cell is PASS except `Build.history` (a record) and detector gaps; the writer is the layer root with a FORENSIC gate and a delete-then-insert pattern; the Nirmāṇa W2 route for this asset was `rebuild_only` (`L1_W2_DECIDE_v1_0.md` §2: "layer canary") and its registry findings (count_sql omitting 315 rows, floor) are already on main (seed `count_sql` lists `bhava_cusps`, `house_chalit`, `sandhi_flag`; floor 1205). Two small real gaps remain (tier literals, a fidelity test that grades the sentence).

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Emit the verification tier through the named constant

- **Answers:** brief gap "bare literal"; CF-17; CLAUDE.md §N.4 last bullet
- **Change:** replace the three `"single"` literals with `verification_vocab.UNVERIFIED_DEFAULT` (value is `"single"`, `verification_vocab.py:180`); extend the `test_ga_dashas_f_a17_bare_tier_literals.py` pattern to this writer
- **Files / declaration / migration:** `platform/python-sidecar/ga_writers/ga_positions_writer.py:343,393,426`; a test beside `test_ga_dashas_f_a17_bare_tier_literals.py`
- **Failing-first test and mutation:** failing-first: the new test fails on the current literals and passes after; mutation: reintroduce one literal and the test fails
- **Output change:** none
- **Blast radius:** none for data (the string is identical). The writer source hash changes (`get_writer_source_hash` walks the local-import closure, `ga_dashas_writer.py:54-72` comment), so the next dispatch may re-evaluate this asset; a no-delta skip is expected where the output digest is unchanged (not verified here)
- **Rebuild:** none required; needs production rebuild only if SS wants the freshness record refreshed
- **Gate it moves:** Earn (claim: the emitted tier), part of CF-17
- **Fix class:** writer code; **buildable before J1:** tier-independent (a ruling already in CLAUDE.md §N.4)

### FD-2 · Narr golden test that names `citation_human`

- **Answers:** brief gap "Narr fidelity"; CF-15; offline Narr.fidelity_test PARTIAL
- **Change:** add one test that builds the canonical-chart rows for one ayanamsha and asserts the exact `citation_human` sentence for the Sun, Moon and Lagna rows against the FORENSIC anchors already in the writer's own gate (Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries), so the sentence is graded, not only the builder
- **Files / declaration / migration:** new test under `platform/python-sidecar/ga_writers/__tests__/` (sibling of `test_bhava_chalit.py`)
- **Failing-first test and mutation:** failing-first: assert the sentence names the longitude, sign and pada the row stores; mutation: change a sign name in `_citation_human_position` and the test fails
- **Output change:** none
- **Blast radius:** none (test only)
- **Rebuild:** none
- **Gate it moves:** Narr (Narr.fidelity_test PARTIAL -> a test that names the declared field)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS Narr ruling 2026-10-01 defines narration)

### FD-3 · Carr D3: re-derive a stratified sample of positions a second way

- **Answers:** census Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (layer hint, T4 "Adapting per layer"): recompute a sample of `graha_position` longitudes with a second Swiss Ephemeris call (different flags) and compare within a declared tolerance; the FORENSIC gate (`:163`) already covers three anchors only; `cross_ayanamsha_divergence_arcsec` is stored on all rows (layer instance §2.7) and is a consistency input, not a second derivation
- **Files / declaration / migration:** Track E inspector tooling (a registered check for this asset); no asset file changes
- **Failing-first test and mutation:** a seeded corrupted copy must report a non-zero mismatch count; zero on the real table
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR -> measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D3 assignment is TGH-T3-02; the detector needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* `Build.history` FAIL (latest run aborted 2026-09-19): the only FAIL on this gate in the layer; a clean asset-set rerun is the way to move it (production run = SS REVIEW), or the history definition changes
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-1: three literals, `ga_positions_writer.py:343,393,426`
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-2: declared `citation_human`
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* one of the seven declared `chart_facts` producers: its `count_sql` is partition-scoped (five categories) and matches `rows_written` (1,205 = 1,205); the shared-table attribution of Complete/Ldgr/Vocab/Reach/Dens cells is the open part
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline Dens rev 4 NO_DETECTOR: shared-table attribution; see INDEX
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* FD-3: D3
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope = categories present in the rows: `_idempotency.replace_prior_chart_facts` (`:533`): a rebuild that stops emitting a category leaves earlier rows
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of the eight call sites: `ga_positions_writer.py:693`
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change to this asset
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: already declared `["citation_human"]` with `evidence.prose_fields` (declarations 1.6.0)
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* `Complete.depth` over the whole table: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition; the five categories above. `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer). A rebuild that changes only `build_id`/`computed_at` must leave the fingerprint unchanged. Prior writers disagree on whether ordering is by `fact_id`; the fingerprint orders by the natural key.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 5 × 10 body positions and their atomic key set; the FORENSIC gate; the dual citation on every row; the delete-then-insert scope.
- **Carriage check chosen (T4 §4.1; one only):** D3 (second derivation of a sample of longitudes) — the layer hint says D3 dominates; no D1 applies (no classical-text restatement).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Is the 2026-09-19 abort on `ga_positions` a failure attributable to the asset (CF-10 option: Build.history reads only runs since the last change to the asset's writer or registry row), or does the asset need a clean asset-set rerun before its Build gate can read PASS? (A rerun is a production build: SS REVIEW.)
2. May named constants for the other `verification_vocab` members be added to the shared L0 module (CF-17), given that an edit to it shifts every importing writer's source hash (~24 L1+L2 writers per the `ga_dashas_writer.py:54-72` comment)?
