---
artifact: ORACLE_EXECUTION_MAP
version: 1.0
status: CURRENT
date: 2026-10-01
author: Pravāha Stream B (B5.5)
branch: pravaha/b5-oracle-tests
---

# ORACLE_EXECUTION_MAP v1.0 — the 36 `executable_at_A5.5` oracles, mapped to tests

Every `executable_at_A5.5` oracle of `GOCHARA_TEST_ORACLES_v1_4.json` (36 total) is
executed by a pytest on branch `pravaha/b5-oracle-tests`, under
`platform/python-sidecar/tests/l3/gochara_rules/` and `.../tests/l3/gochara/`.

**Status legend**
- `REAL` — every 'then' clause asserted on the OUTPUT of production code; mutation
  demonstrated RED (applied, run, reverted).
- `FINDING` (strict-xfail, `strict=True`) — the oracle's 'then' has no production
  output to assert on; the test calls the production seam the spec implies and
  XPASS-fails the moment Stream A lands the fix. Findings F1–F15 are consolidated
  below for routing to A5.2/A5.3/kernel.
- `NOT-BUILT` (xfail, `strict=False`) — the A5.2 substrate itself is not built; not
  a finding, flips when A5.2 lands.

Suite state at push `823eb921b`: **432 passed + 21 xfailed** across
`tests/l3/gochara_rules` + `tests/l3/gochara` (84 skipped = WP6 disposable-DB tests).

## Map

| Oracle | Guards / defects | Test | Status |
|---|---|---|---|
| O-TV-1 | §3 valence; #11,#12 | `gochara_rules/test_oracles_a55_tv_vi.py::test_o_tv_1` (+ P3 father-frame admission assert) | REAL |
| O-TV-2 | §3; #12,S-03 | same file `::test_o_tv_2` | REAL |
| O-TV-3 | §3; ADK-0026,#12 | same file `::test_o_tv_3` | REAL |
| O-VI-1 | §5 vedha; #17,E2 | same file `::test_o_vi_1` | REAL |
| O-VI-3 | §5; M-8-conformance | same file `::test_o_vi_3` | REAL |
| O-VI-5 | §5; #25 | same file `::test_o_vi_5` | REAL |
| O-BP-2 | §8; RQ-1,G-10,S-05 | `gochara_rules/test_oracles_a55_bp_p6.py` cases A/B/C | REAL |
| O-BP-3 | §8; N8 | same file `::test_o_bp_3` | REAL |
| O-BP-4 | §8/P5c; #19,T0-10 | same file — donor-key path REAL; fallback label `test_o_bp_4_fallback_label_emitted_by_real_path` | REAL + **F1** |
| O-P6-TARA | §2 P6; #5 | same file — tārā arithmetic REAL; name→index normaliser `test_o_p6_tara_name_to_index_normalisation` | REAL + **F2** |
| O-RR-4 | §1; #9,E3 | `gochara_rules/test_rr_oracles_a55.py::test_o_rr_4_negative_fact_no_object` REAL (R-1 writer path); qualifier landing `test_o_rr_4_negative_fact_lands_as_graha_qualifier` | REAL + **F3** |
| O-RR-5 | §1/§2; #22,NK-7 | same file `test_o_rr_5_yoga_admission_via_production_path` REAL (`_build_yoga_rows`, house_of pins kept); cancellation gate `test_o_rr_5_cancellation_blocks_admission` | REAL + **F4** |
| O-RR-6 | §1.2 inv 8; #23 | same file `test_o_rr_6_affliction_predicate` REAL (TRUE/FALSE/UNKNOWN); named- afflicter + orb `test_o_rr_6_afflicter_named_and_orb_enforced` | REAL + **F5** |
| O-RR-7 | §1.2 inv 2; S-04,D-PADMIT | same file `test_o_rr_7_testimony_row_bitwise_equal_scores` REAL; breakdown annotation `test_o_rr_7_testimony_annotation_in_breakdown` | REAL + **F6** |
| O-RP-1 | §2; union-not-cascade,#11 | `gochara_rules/test_rp_oracles_a55.py::test_o_rp_1_union_admission_no_cascade` | REAL |
| O-RP-3 | §2; P4-definition,R3-S02 | same file `test_o_rp_3_p4_admission_…` REAL; peak `test_o_rp_3_peak_is_argmax_min_activity_not_endpoint` | REAL + **F7** |
| O-RP-5b | §2/§3; S-03,R2-S05,S-04 | same file `test_o_rp_5b_sade_sati_testimony_zero_score_effect` | REAL |
| O-RP-6 | §2.3 inv 8; #1 | same file `test_o_rp_6_promise_strength_times_condition` | REAL |
| O-RP-7 | §2.2 P1; #20 | same file `test_o_rp_7_dignity_flip_flips_qualifier_sign` REAL (factor rows); one-qualifier flip `test_o_rp_7_one_production_qualifier_flips_with_dignity` | REAL + **F8** |
| O-RP-8 | §2.3 inv 7; #21 | same file `test_o_rp_8_only_qualified_set_enumerated` REAL (registry selectors); enumerator `test_o_rp_8_production_enumerator_row_count` | REAL + **F9** |
| O-SS-1 | §6 substrate; #27,E1 | `gochara/test_a55_substrate_oracles.py` — 12/27/96 exact counts (Swiss/Lahiri pinned) | REAL |
| O-SS-2 | §6; #14,N2,NK-7 | same file — case 1 direct Aries ingress REAL; case 2 retrograde 0°-seam root 63.3 s off | REAL + **F10** |
| O-SS-3 | §6; N3,NK-7 | same file — end-truncated contact + end-clipped span carry `truncated_at_horizon=None` | **F11**, **F12** |
| O-SS-4 | §6; Moon-on-demand | same file — moon-on-demand live legs REAL; global-substrate `count(*)=0` leg | REAL + NOT-BUILT |
| O-SM-3 | §7; stations,R2-S06 | same file — station `swiss_refined` audit | NOT-BUILT |
| O-RX-1 | §6.1; NK-2,R3-amendment-1 | same file — occurrence-ordinal identity | NOT-BUILT |
| O-CF-N5 | §10 conformance; N5,RQ-6 | `gochara/test_a55_conformance_oracles.py` — producer keeps both 60-day peaks | REAL |
| O-CF-N6 | §10; N6 | same file — birth_anchor raises + non-empty marriage control | REAL |
| O-CF-N7 | §10; N7,RQ-4 | same file — mūrti-testimony A/B bit-identical REAL; production row audit | REAL + NOT-BUILT |
| O-AO-1 | §9 annual; saham-year-mixing,S-07 | same file — year-join | NOT-BUILT |
| O-AO-2 | §9; saham-provenance,R2-S06 | same file — saham positive control | NOT-BUILT |
| O-AO-3 | §9; D-T2-gate,S-04 | same file — empty-P9 set + scored-P9 shape + testimony-P9 zero channels | REAL |
| O-RW-1 | §10 writer; lineage,S-02 | `gochara/test_a55_writer_oracles.py::test_o_rw_1_geometry_change_yields_new_convention_id_valence_cannot` REAL; invocation counter + invalidation `test_o_rw_1_solver_invocation_counter_and_invalidation_record` | REAL + **F13** |
| O-RW-2 | §10; §N.6,coverage-honesty | same file `test_o_rw_2_no_window_answer_carries_coverage_object` REAL; confirmed-vs-context `test_o_rw_2_window_set_counts_confirmed_vs_context_separately` | REAL + **F14** |
| O-RW-3 | §10; N-10,D-41 | same file `test_o_rw_3_provenance_names_ka_gochara_republish_from_manifest` | REAL |
| O-GR-PLATEAU | §2.3 inv 4; #24,E5 | same file `test_o_gr_plateau_grain_lineage_and_clipped_curve_flag` | **F15** |

## Consolidated FINDINGs (strict-xfail, XPASS-fails on fix) — routing list for Stream A

| # | Oracle | Finding | Evidence (file:line) | Owner |
|---|---|---|---|---|
| F1 | O-BP-4 | sign-level fallback label 'coarser P5a qualification' emitted by no code path | `services/gochara_rules/ashtakavarga.py:~110` (docstring-only) | A5.2/A5.3 |
| F2 | O-P6-TARA | nakṣatra name→index normaliser (case-mismatch defect #5) not built; `p6.nakshatra_index` absent | `services/gochara_rules/p6.py` | A5.2 |
| F3 | O-RR-4 | negative sensitive fact attaches nowhere as a graha qualifier — dropped with a report count only | `services/ka_gochara_resonance/writer.py:494-495` | A5.2/A5.3 |
| F4 | O-RR-5 | no production path evaluates yoga cancellation for admission; `bhanga_active` carried as qualifier string, never a gate; no cancellation report | `services/ka_gochara_resonance/writer.py:683-684` | A5.2/A5.3 |
| F5 | O-RR-6 | `afflicted()` returns bare TRUE — afflicter not named on output, no orb operands; Saturn at orb 6.0 > 5.0 still afflicts | `services/gochara_rules/records.py:108-121` | A5.2/A5.3 |
| F6 | O-RR-7 | `path_channel_scores` breakdown carries no per-record annotations (channel totals only) | `services/gochara_rules/score.py:68-83` | A5.2/A5.3 |
| F7 | O-RP-3 | no production peak = argmax min-activity; declared only as a `score_rule` string | `services/gochara_rules/registry.py:550` | A5.5 trajectory |
| F8 | O-RP-7 | no production function composes dignity into ONE P1 qualifier whose direction/valence flips | `services/gochara_rules/ashtakavarga.py:143` (P5-only qualifier) | A5.2 |
| F9 | O-RP-8 | no production record enumerator driven by qualified restrictions (only registry selector strings) | `services/gochara_rules/registry.py` | A5.2 |
| F10 | O-SS-2 | retrograde 0°-seam root found but 63.3 s off (outside δt < 60 s) | kernel (case-2 fixture) | kernel |
| F11 | O-SS-3 | end-truncated degree contact carries `truncated_at_horizon=None` — 'end' honesty not propagated | `services/gochara_kernel/episodes.py:671` | kernel |
| F12 | O-SS-3 | end-clipped residence span `truncated_at_horizon=None`, same site | `services/gochara_kernel/episodes.py:671` | kernel |
| F13 | O-RW-1 | no solver-invocation counter; no dependency-driven invalidation writer recording 'which fired and why' (§10.1) | grep `services/` — absent | A5.3 writer |
| F14 | O-RW-2 | served window set does not count confirmed vs context rows separately (§N.6) | `services/ka_gochara/service.py` (EpisodeBatch) | A5.3 serving |
| F15 | O-GR-PLATEAU | no per-row grain lineage (era/month/day → grain-operating path; day-only-P6; clipped-era-curve flag) | `services/gochara_v3/engine.py`, `ka_gochara_sweep/` | A5.3 writer lineage |

## Mutation evidence

Each REAL test's mutation was applied to production code, run RED, and reverted
(documented per batch in the B5.5 steward reports M20260930T180408-0d78,
…T180646-b5e3, …T181022-b694, …T181143-f58f, …T181424-4da7, …T181833-7cfd,
…T184018-b1fc): valence flips, silent defaults, attenuation-on-inactive,
donor/SAV absence, declaration-always-true, wrong contributor key, wrong
nine-fold class, cross-path cascade, AND-within-agent, testimony scored,
condition-independent promise, unrestricted Cartesian enumeration, sign grid
without 0° seam, minted Moon contact_id, producer-default 90-day trim,
birth_anchor mapped, scored P9 registered, constant convention_id, neutered
CoverageRecord invariants, skipped published-refusal.
