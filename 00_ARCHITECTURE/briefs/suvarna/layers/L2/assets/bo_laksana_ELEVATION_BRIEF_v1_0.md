---
asset_id: bo_laksana
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); FD-1's output change needs SS (R5)"
nirmana_freeze: "t1, 2026-09-08"
ledger_gap_ids: [bo_laksana-Idem.pattern, bo_laksana-Earn.build_record, bo_laksana-Cost.baseline, bo_laksana-Count.floor, bo_laksana-Build.history, bo_laksana-Carr.detector]
---
# bo_laksana — MSR signal store: the root writer of `bodha_msr_signals`

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

The root of Bodha: a category-agnostic projection of every `chart_facts` row into `bodha_msr_signals` (`bo_laksana.py` module docstring, lines 1-30: "Queries chart_facts with NO category whitelist — every fact is a candidate signal"). `@register("bo_laksana")` at `bo_laksana.py:3355`; the class owns 15 `signal_type_class` values (`:145-161`; 12 present on the canonical chart, layer instance §6.1), INSERTs at `:3067` and replaces its prior rows through `replace_prior_msr_for_chart` at `:3595`. Signals are deterministic (`salience_formula_v1`, `bodha_writers/formulas.py`), `lel_origin` is False on every chart row (`:11`: "LEL data is L3-gated; L2 is timeless structural"), the L3 hook columns are written NULL, and the WP-2.4 flood cap (9b-1) collapses per-varga aspect/matrix families to one rollup signal per category × varga. It owns 50,529 of the chart's 50,678 MSR rows, has the layer's widest radius (22 direct dependents in the saved census, 24 in the seed-derived post-1210 closure) and feeds the whole L2 DAG. Its `bo_laksana_rerank` sibling shares this file (`:3821`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1609` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:3355`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_msr_signals`; count_sql tables: `bodha_msr_signals` | census CEN-R |
| live rows / floor | 50529 / 60000 (chart 482012f1, count_sql scope) — Count.floor FAIL: floor 60,000 vs live 50,529 (-9,471); the seed literal says 66,738 (`asset_registry_seed.ts:1623`) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bg_rules`, `ga_positions`, `ga_strength`, `ga_sensitive`, `ga_panchanga`, `ga_sade_sati`, `ga_structural`, `ga_nakshatra`, `ga_condition`, `ga_vargas`, `ga_vichara` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 22 / transitive 48; seed-derived closure (post-1210): direct 24 / transitive 48; direct dependents: `bo_anveshana`, `bo_bimba`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_upaya`, `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_sangam`, `ka_yojaka`, `mi_adhilepa`, `mi_bhavisya`, `mi_darshana`, `mi_pariksha`, `ph_nimitta`, `ph_phaladesa`, `ph_sodhana` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_msr_signals`: 89 non-test py/ts/tsx files reference it (65 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ka_yojaka.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ph_nimitta.py` +59 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 9 capability module(s): `L2_bodha/query_domain_reading.ts`, `L2_bodha/query_signals.ts`, `L2_bodha/query_ucd.ts`, `L2_bodha/traverse_chart_graph.ts`, `L3_kala/call_service_wrappers.ts`, `L3_kala/query_temporal_activation.ts`, `reading_checklist.ts`, `register_d8_assess_domain.ts`, `register_d9_judgment.ts`; `density_contract` declared on 3 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-08; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a7c45a8b complete/build (2026-09-08) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_msr_signals (bodha_writers/_idempotency.py:209 via bo_laksana.py → bodha_writers/_idempotency.py:replace_prior_msr_for_chart) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 39 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-08): TypeError: list indices must be integers or slices, not str Traceback (most recent call last):   File "/app/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 1043, in _run_data_writ |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a7c45a8b complete/build (2026-09-08) |
| Count (information) | Count.floor | FAIL | live=50529, floor=60000, delta=-9471 |
| Complete (information) | Complete.depth | PARTIAL | 150724 rows, 85 cols; fully populated 40; NEVER populated ['varga_provenance_jsonb', 'source_corroboration_count_by_verse', 'divisional_corroboration_count', 'dasha_activation_proximity_score', 'aspect_modifier', 'argala_modifier', 'salience_confidence_interval_jsonb', 'shared_factor_keys_jsonb', 'cross_domain_shared_factor_count', 'graph_edge_pattern_jsonb', 'graha_weakness_indicators_jsonb', 'recurring_pattern_mark… |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width ≥ 19/67 built column(s) (28.4%), a lower bound: L2_bodha/query_signals.ts, L3_kala/call_service_wrappers.ts select(s) a run-time column list selected by 9 capability module(s); dark: ['active… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 150724/150724 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb): 0 duplicate(s)); Dens.served† (6 module(s): query_discoveries.ts, query_domain_reading.ts, query_pratijna.ts, query_signals.ts, query_ucd.ts,…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=50529 = live=50529 (count_sql over the target table; chart 482012f1)); Build.exercised (74 executed run(s) of 131 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 20…); Build.dep_liveness.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 serving-root file(s) naming bodha_msr_signals lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_synthesis.ts; its served select and density_contract cannot be read — neve; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** FAIL — missing edge `bo_laksana → ga_yoga` (reads `ga_yoga_firings` at `bo_laksana.py:2712`; the producer is reachable transitively via `ga_vichara`, so ordering holds but the edge is undeclared). **Migration 1210 deliberately did NOT add it** (`TrackI/edges_evidence.md:90-91`: "left for a later, separately ruled migration"), so this FAIL remains. The saved census cell Build.dag PASS † above is the rev-1 reading.

**MSR group.** This asset is one of the seven producers that target `bodha_msr_signals`; the group reading is in `INDEX.md` §3 (per-asset attribution is dark in the default projection because `producer_asset_id` is not served, so the per-asset cells above are the producer-scoped `count_sql` partitions, and Narr declarations attribute through the served `signal_type_class` facet). Chart rows: 50,678 = 45 + 14 + 20 + 25 + 45 + 50,529; table-wide 150,724 rows (MF-L2-004: never compare the two populations).

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_laksana-Count.floor` | Count (information) | information | live 50,529 vs floor 60,000 (-9,471). CLAUDE.md §N.4: a floor equals the achieved count after a build and rows are never fabricated to meet it. The cause of the shortfall against the seed's 66,738 is not attributed here (the WP-2.4 flood cap is one candidate; not measured). CF-03 (refresh after a coherent rebuild; not now). |
| `bo_laksana-Idem.pattern` / census cell Idem.pattern PASS † | Idem | other (R243 annotation) + stale ledger row | saved census reads PASS (delete-then-insert via `replace_prior_msr_for_chart`) with no annotation (MF-L2-006); the PASS must be emitted with `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a` (R243; W2-3_REVIEW's per-asset chart list differs for some assets, MF-L2-011: both readings are in layer instance §6.3, neither chosen). The ledger row (`ON CONFLICT where the layer convention is delete-then-insert`) is from the 2026-09-27 run and is stale. CF-13. |
| code: `bo_laksana.py:1423`, `:2969`; `bodha_writers/bhavat_bhavam_amplifier.py:345` | Null | real-or-SS-question | three emit sites (varga-divergence signals, the D1/D9 dignity cross-check and the Bhāvat-Bhāvam amplifier) store the literal `source_corroboration_count_by_text = 2`, while the main path computes it (`_corroboration_count_by_text(classical_sources_jsonb)`, `:2513`) and the satellite emitters store NULL (`arudha_emitter.py:163`). At these sites the value does not feed `salience_formula_v1` (they do not call it): `computed_salience` is set directly (divergence `round(1.2 * 1.0, 6)`, `:1456`; D9 cross-check hand-set `salience_base` 1.6/1.8/2.0 by branch, `:2861-2884`; the amplifier clamps below its primary, `bhavat_bhavam_amplifier.py:49-138`) and `salience_inputs_complete` is False (`:1460`, `:3008`). So the constant 2 is a stored value with no computation behind it (CLAUDE.md §N.7 item 6 / §N.8), and the hand-set salience constants raise a separate question against "salience is formula-driven" (L2 handoff §6 trap 2). The census has no Null check on either. FD-1; question 2. |
| `bo_laksana` Build.dag rev 2 (E6gh recompute; `TrackI/edges_evidence.md:90`) | Build (dag) | real (missing edge) | reads `ga_yoga_firings` at `bo_laksana.py:2712` (the `neecha_bhanga_raja_yoga` cancellation lookup) with no declared `bo_laksana → ga_yoga` edge; the producer is reachable only transitively via `ga_vichara`. Migration 1210 left it out deliberately ("a later, separately ruled migration"), so the rev-2 FAIL remains. Effect: `compute_upstream_hash` (declared deps) does not see a `ga_yoga` rebuild, and the cockpit blast radius of `ga_yoga` omits `bo_laksana`. FD-2; CF-15. |
| `bo_laksana-Complete.depth` (census) | Complete (information) | information | table-wide NEVER populated include `aspect_modifier`, `argala_modifier`, `shared_factor_keys_jsonb`, `cross_domain_shared_factor_count`, `source_corroboration_count_by_verse`, `varga_provenance_jsonb`, `divisional_corroboration_count`, `dasha_activation_proximity_score` (the last is an L3 hook, NULL by design). `argala_modifier` is a salience term whose L1 authority the writer does not read (prior-campaign finding N-01, L2_W2_DECIDE 2026-09-05; status on main not re-verified). CF-16, CF-17. |
| `bo_laksana-Carr.detector` | Carr | detector | no D1/D2/D3 detector exists; CF-07 |
| `bo_laksana-Build.history` | Build (history) | history | latest run complete; 39 errors and 7 aborts on record (latest error 2026-09-08, `TypeError: list indices must be integers or slices, not str`). CF-10 |
| census: Null/Narr (declarations 1.6.0) | Null, Narr | detector | `prose_fields` is declared (see the declaration evidence); the Narr agree/checkable/fidelity/lint and Null checks have not run (NO_DETECTOR in the offline rollup); CF-14 |
| census cell Dens.served † | Dens | detector (attribution) | saved rev-1 PASS; offline rev-4 static scan NO_DETECTOR (shared table, no producer attribution by code); CF-04 |
| census cell Complete.depth | Complete (information) | information | table-wide never-populated columns, identical under all seven MSR assets; CF-17 / CF-16 |

## 3 · Disposition

**keep (P)** — no cell is a measured defect of the asset: Count.floor is aspirational information, the Idem PASS is real and only needs its R243 annotation, the rest are absent detectors. One code observation (FD-1) needs a ruling but does not change the disposition. The preserved kernel is the deterministic projection of L1 into the signal register every later Bodha asset reads.

Approver under Track A brief §10: **Steward (G16); FD-1's output change needs SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Store NULL, not a literal 2, in `source_corroboration_count_by_text` on the three constant sites

- **Answers:** code observation (Null gate NO_DETECTOR); CLAUDE.md §N.7 item 6 / §N.8
- **Change:** at `bo_laksana.py:1423`, `:2969` and `bhavat_bhavam_amplifier.py:345` write NULL (the table already accepts it: the satellite emitters store NULL, `arudha_emitter.py:163`). These three sites do not call `salience_formula_v1` (salience is set directly there), so the NULL cannot reach `math.log(1 + count)`; do NOT pass NULL into the formula anywhere (`formulas.py:132` types it `int = 1` and `:162` takes `math.log(1 + count)`, so a None would raise). The alternative is to ratify the 2 as a documented approximation with a decision id (no code change)
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py`, `platform/python-sidecar/bodha_writers/bhavat_bhavam_amplifier.py`; no migration, no formulas.py change
- **Failing-first test and mutation:** failing-first: a fixture divergence/D9/amplifier signal stores NULL in the column and an unchanged `computed_salience`; mutation: restore the literal 2 on one site → the Null test (CF-14 family) flags it
- **Output change:** yes if NULL is chosen: the stored column changes on the affected signal rows (their `computed_salience` does not): SS (R5); none if the constant is ratified
- **Blast radius:** output change: this asset's registry dependents see new values after the rebuild (direct 24: `bo_anveshana`, `bo_bimba`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_upaya`, `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_sangam`, `ka_yojaka`, `mi_adhilepa`, `mi_bhavisya`, `mi_darshana`, `mi_pariksha`, `ph_nimitta`, `ph_phaladesa`, `ph_sodhana`; transitive 48)
- **Rebuild:** needs production rebuild of `bo_laksana` and the whole downstream chain (REVIEW item for SS; the F-3 invariant applies) if NULL is chosen; none for the ratify-only option
- **Gate it moves:** Null (NO_DETECTOR → measured)
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent: waits on the Null-gate rule for a constant standing for a measured value (SS 2026-10-01) and on the ruling
- **Question for SS:** Is a literal 2 on a signal that cites one fact an accepted documented approximation, or must the column be NULL?

### FD-2 · Declare the `bo_laksana → ga_yoga` edge

- **Answers:** Build.dag rev-2 FAIL (missing edge); CF-15
- **Change:** append `ga_yoga` to `bo_laksana.depends_on` (the same shape as migration 1210: append-only, idempotent, guarded). `ga_yoga` was previewed lit and fresh as the producer of 1210's `ka_yojaka → ga_yoga` edge (1210 header, SPLIT), and `bo_laksana` already follows it transitively via `ga_vichara`, so the edge is acyclic and adds no wait
- **Files / declaration / migration:** one surgical migration (number = max+1 across origin heads at execution time) and the seed literal `asset_registry_seed.ts:1609-1622`; verify by production structure
- **Failing-first test and mutation:** failing-first: the rev-2 Build.dag reads-match reads PASS for `bo_laksana` (it reads FAIL on the missing edge today); mutation: remove the edge → FAIL
- **Output change:** none
- **Blast radius:** the DAG gains one direct edge: `ga_yoga`'s direct radius +1; `compute_upstream_hash` for `bo_laksana` changes once (one-time rebuild signal, and the F-3 order invariant makes any `bo_laksana` rebuild a REVIEW item); the identity check on the frozen t1 manifest throws (`plan_adaptation_required`)
- **Rebuild:** none for the migration; the next dispatch sees a changed upstream set
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent in content; a DAG change that 1210 deliberately deferred: needs its own ruling
- **Question for SS:** May the deferred `bo_laksana → ga_yoga` (and `bo_upaya → bo_bimba`) edges now be added in a second migration?

### FD-3 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** for each of the three emit sites (fact path `_build_summary_text`/`_build_headline_text`, the D1/D9 cross-check strings, the varga-ratification divergence strings) a golden fixture of L1 facts whose expected headline and summary are written out by hand; the test asserts every numeric or graded token in the string equals the cited fact's value (`constituent_facts_array`), and that no raw token (`check_no_raw_token_in_narrative.py`) leaks
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 24: `bo_anveshana`, `bo_bimba`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_upaya`, `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_sangam`, `ka_yojaka`, `mi_adhilepa`, `mi_bhavisya`, `mi_darshana`, `mi_pariksha`, `ph_nimitta`, `ph_phaladesa`, `ph_sodhana`; transitive 48); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-4 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute `computed_salience` and `signature_tier` from each sampled signal's stored inputs with `salience_formula_v1` and compare, plus the existing §N.5 resolver `msr_referential_integrity.py` (self-test is the CI gate; live mode runs only at W3 rebuild verification) as the reference-resolution leg. Anchor: MSR_COMPUTED_VALUE_DRIFT_HANDOFF (a signal must reference the L1 `fact_id`, never restate its value).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 24: `bo_anveshana`, `bo_bimba`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_upaya`, `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_sangam`, `ka_yojaka`, `mi_adhilepa`, `mi_bhavisya`, `mi_darshana`, `mi_pariksha`, `ph_nimitta`, `ph_phaladesa`, `ph_sodhana`; transitive 48); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-13** — MSR replacement: R243 annotation and F-3 cascade-key retirement. *This asset:* the largest MSR producer: its PASS carries the R243 annotation; its rebuild deletes the most dependants (embeddings 50,678 rows, contradictions) and runs against the live guard
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose columns `signal_headline_text`, `signal_summary_text`, `citation_human` at three emit sites (declaration evidence: `bo_laksana.py:2414/2425`, `:2920/2924`, `:1394`); no fidelity test measured
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* Count.floor refresh and seed-literal alignment (seed 66,738, live floor 60,000, achieved 50,529) after a coherent rebuild
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens: part of the MSR attribution rule
- **CF-16** — Shared-root carriers (T1 3.4): the empty columns and their counting rule. *This asset:* shared-root carrier columns are NEVER populated (`shared_factor_keys_jsonb`, `cross_domain_shared_factor_count`)
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns listed above
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage: D3 (§6)
- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* FD-2: missing `ga_yoga` edge
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, signal_type_id, configuration_jsonb)` (the census `Vocab.identity` key adds `build_id`, a generation id, excluded here as volatile). Fingerprint over the signal's own columns for the rows this asset owns (`producer_asset_id = 'bo_laksana'`, the 15 owned classes): `signal_type_class`, `constituent_facts_array`, `valence`/`valence_source` as written at insert, `computed_salience` and its inputs, `signature_tier`, `signal_headline_text`, `signal_summary_text`, `citation_ref`, `citation_human`. **Excluded as volatile:** `signal_id`, `build_id`, `computed_at`, `engine_version`, and every column the rerank updates (`graph_node_strength_contribution_jsonb`, `system_convergence_count`, `cross_system_consensus_count`, `contradicts_signals_array`, and `valence`/`valence_source` for `ga_vichara_v1` rows), which belong to `bo_laksana_rerank`'s fingerprint. A rebuild must keep 50,529 chart rows unless an input L1 fact changes.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the deterministic fact-to-signal projection, the 15 owned classes, `constituent_facts_array` resolving to `chart_facts.fact_id` (CLAUDE.md §N.5; guard `platform/scripts/governance/msr_referential_integrity.py`), formula-driven salience, the flood cap, `lel_origin = false`.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-4)
- **Opportunities (never blocking):** argala as a stored salience term from the L1 authority; the 15-class universe is undeclared (`Complete.width`); a Dens attribution rule so the 50,529 rows' served layering can be measured.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-08. Migration 1210 (applied; verified live 2026-10-01 14:37Z per the coordinator): it added no edge to this row; a `depends_on` edit (CF-15) would make the identity check throw, while `count_sql`/`natural_key_partition`/`catalog_status` edits (CF-03) only require an evidence refresh. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3). **A production rebuild of any MSR producer (SS REVIEW):** `replace_prior_msr_for_chart` deletes the writer's owned classes AND the `bodha_contradictions` rows whose `signal_a_id`/`signal_b_id` fall in them (`_idempotency.py:200-206`) and, through the three L2 keys still in force, `bodha_signal_embeddings`; the live guard refuses on non-canonical charts while Kāla dependants exist (R243) until 1214 is deployed. After the replacement `bo_samskara` (registry level 7), `bo_karanajala` (8), `bo_laksana_rerank` (9) and everything downstream re-run in DAG order. **F-3 and I-6 (read-only context; `F3_MSR_FK_DROP_v1_0.md` v1.1, DRAFT_FOR_REVIEW, branch `suvarna/land/F3-msr-fk-drop-001`, PR #2828; migration 1214 is not on main at this lane's fetch).** I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 (reproduced on a disposable Postgres) and erased the canonical chart's five Kāla tables on 2026-09-08 (1214 header). Migration 1214 drops FIVE `kala_*` keys only; the three L2 keys (`bodha_contradictions` signal_a/b, `bodha_signal_embeddings`) are not in it and go through an owner-path REVIEW (BUILDER_GRANT_PLAN); SS DECLINED removing the `assert_l2_msr_delete_safe` refusal (it stays and re-arms only if a cross-layer key is re-added). After 1214 the refusal no longer fires on Kāla dependants and nothing errors if a later MSR regeneration leaves them dangling. **Mandatory rebuild-order invariant (F3 `plan_invariant.md`):** the six MSR writers (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`) run strictly BEFORE the five Kāla assets (`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`), `ka_yojaka`, the seven Phala assets reached through `kala_convergence`/`phala_anchors` (`ph_nimitta`, `ph_pratikara`, `ph_muhurta`, `ph_pramana`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`) and the L2 consumers (`bo_karanajala`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `bo_cdlm_summary`, `bo_pratijna`), and none of them is rebuilt again later in the same window. **Charts 1c826d5a and cb73cd3d have ALL-v4 signal ids (50,171 and 49,875 signals): the first v5 regeneration of either strands every one of their Kāla rows (1c826d5a: 336,093 `kala_activation` rows) with no error, so the order guard (`msr_rebuild_order_guard.py`, PF-1/PF-2) and the dangling-reference detector are MANDATORY for those two charts; the canonical chart's 50,678 ids are all v5.** Rebuilding `bo_laksana` is the longest chain in the layer: it is the root (registry level 6 in the instance table) and 24 direct dependents follow.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: is `source_corroboration_count_by_text = 2` on single-fact signals an accepted approximation, or must it be NULL (output change)? And are the hand-set salience constants on the D9 cross-check (1.6/1.8/2.0) and divergence (1.2) signals acceptable design defaults against the formula-driven rule?
2. FD-2: may the deferred `bo_laksana → ga_yoga` edge be added?
3. CF-13: the annotation lists `1c826d5a` only for this asset and W2-3_REVIEW agrees (MF-L2-011 concerns the other five). Is that list final?
4. CF-03: refresh the 60,000 floor to the achieved count only after a coherent L2 rebuild (recommended), or now?
