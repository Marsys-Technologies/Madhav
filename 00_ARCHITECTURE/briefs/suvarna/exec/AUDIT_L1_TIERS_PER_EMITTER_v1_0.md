---
canonical_id: AUDIT_L1_TIERS_PER_EMITTER
version: 1.0
status: DRAFT_FOR_SS_REVIEW
date: 2026-10-02
branch: suvarna/land/TI-l1-tier-audit-001
base_head: bf6fe712bdc3c186a864d7de79f42fe8d64de0f0   # origin/main at audit time
mode: READ-ONLY (no code change, no DB write, no build). DB reads as suvarna_reader only.
rule_audited: "SS N-62 / Q03 — two_pass_verified ONLY for an independent re-derivation compared through two_pass_verdict; bounds/ordering invariants and same-formula arithmetic re-checks = classical_match; the 1,780 zero-tolerance default rows = single"
changelog:
  - "1.0 (2026-10-02) — first issue."
---

# L1 verification tiers, per emitter (N-62 / Q03 audit)

Charts: **canon** = `482012f1-710e-4a25-994a-93821f5871aa`; **abhi** = `1c826d5a-41cb-4450-b4dc-59d440e5f75a`; **cb73** = `cb73cd3d-9eba-4220-9902-0de91566e980`. "total" = canon + abhi + cb73. Counts were read live on 2026-10-02 as `suvarna_reader`. Code citations are at base HEAD `bf6fe712b`, paths relative to `platform/python-sidecar/`.

## 1. Headline

- **`chart_facts`, canon.** `two_pass_verified` (TPV) = **9,320** = ga_sensitive **8,750** (6,970 positive tolerance + 1,780 zero tolerance) + ga_sade_sati 320 + ga_nakshatra/ga_kp_significators 190 + ga_sensitive_degree 60. ga_strength emits **no** TPV. All three charts: 32,650 TPV.
- **Only two L1 emitters in `chart_facts` run a second derivation that is compared through `two_pass_verdict`**: `ga_nakshatra._nakshatra_pada_verdicts` (ga_nakshatra.py:108-156, verdict at :147) and `ga_kp_significators.emit_kp_significators` (ga_kp_significators.py:223-227). Canon rows: 100 + 90 = **190 of 9,320 (2.0%)**.
- **`ga_sensitive` has no call to `two_pass_verdict` anywhere.** Its 8,750 canon TPV rows get the tier from the *default argument* `verification_pass_status: str = TWO_PASS_VERIFIED` in `_make_row` (ga_sensitive_writer.py:373), plus four literal strings at :2657/2662/2667/2678. A positive `tolerance_arcsec` is **not** evidence of a second path: it is a declared constant (1.0, 30.0, 36.0, 60.0) on 6,830 of the 6,970 rows.
- **Exactly one `ga_sensitive` family has a real independent second path: `upagraha_position` (DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA, UPAKETU; 175 canon rows).** PyJHora native vs in-writer BPHS algebra (ga_sensitive_writer.py:585-589 vs :615-621). Its diff is stored as `tolerance_arcsec` but never compared to a threshold and never routed through `two_pass_verdict`, so even these 175 rows are unearned as coded. 35 of the 175 (UPAKETU) sit in the *zero*-tolerance group (stored diff = 0), so the "1,780 zero tolerance = single" shortcut and the "positive tolerance = has a second path" shortcut are both wrong for them.
- **Tier changes on canon `chart_facts` TPV rows, rule applied to code as written:** 190 stay TPV; 380 → `classical_match` (60 + 320); 8,750 → `single` (of which 175 upagraha rows return to TPV if the verdict is wired, see §4).
- **`single_pass` alias, canon 10,836** (all three charts 10,937): emitted by ga_strength 10,575, ga_panchanga 176, ga_structural 85 (canon). Mechanical alias → `single` changes no salience weight (`formulas.py:538`, `canonical()` already resolves it). Applying N-62 literally moves 8,970 of the ga_strength rows to `classical_match` (an invariant did run over them) and leaves 1,866 as `single`.

## 2. `two_pass_verified` rows in `chart_facts`, per emitter

Legend. **2nd path**: a different code path / formula / library whose output is compared to the primary and could disagree. "via verdict" = routed through `brahmagyan.verification_vocab.two_pass_verdict`. **Resulting** = tier under N-62 for the code as it stands. Sensitivity flags D1-D6 are in §7.

### 2.1 ga_sensitive (`ga_writers/ga_sensitive_writer.py`; all rows `source_calculation = pyjhora_adapter.sensitive/…`)

All rows: current tier TPV from the default at :373 (the 4 yogi-system rows from literals). Canon pos/zero = canon rows with `tolerance_arcsec` > 0 / = 0.

| emitter (builder:line) | fact families | canon | total | 2nd path | resulting | evidence | notes |
|---|---|---:|---:|---|---|---|---|
| `_build_upagraha_rows`:551 (5 subjects) | upagraha_position DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA, UPAKETU | 175 (140 pos / 35 zero) | 525 | **yes, not gated** | single as coded; TPV once wired | PyJHora `sensitive_points` :592 vs BPHS algebra :585-589; diff → `tolerance_arcsec` :620-621; status never set (default :373) | stored diff 0.0012 arcsec for 4 subjects, 0 for UPAKETU. Only family with a true cross-library path. Verdict must be wired (D6). |
| `_build_upagraha_rows`:551 (KALA) | upagraha_position KALA | 35 (0/35) | 105 | no | single | formula slot is `None` :601; `tolerance = 0.0` :623 | PyJHora native only. |
| `_build_saturn_derived_rows`:654 | saturn_derived_point GULIKA_LAHIRI, MANDI, MAANDI | 105 (105/0) | 315 | no | single | native `gulika`/`maandi` :681-684; `tolerance=36.0` constant :697,732,739 | MAANDI is the same value as MANDI :734-740 (not a second derivation). |
| `_build_saturn_derived_rows`:654 | saturn_derived_point YAMAGANDA_SPHUTA | 35 (0/35) | 105 | no | single | `sat+240` :755; own provenance text says "computed_extension" :761 | honest tier is `computed_extension` (D4). |
| `_build_bhrigu_bindu_rows`:772 | esoteric_point_bhrigu_bindu | 35 (35/0) | 105 | **no (tautology)** | single | `bb_verify = _midpoint(moon, rahu)` :783 is the same call as :781; `tol = max(0, 1.0)` :784,790 | the positive tolerance is manufactured by `max(tol, 1.0)`. |
| `_build_yogi_avayogi_rows`:794 | esoteric_point_yogi, _avayogi (bphs_93_20, alt_96_40) | 140 (140/0) | 420 | no | single | two formula variants emitted side by side :822-849; `tolerance=1.0` constant | variants are alternative conventions, not a check. Agreement with `sensitive_point_yogi` is test-only (`__tests__/test_ga_sensitive_degree.py`), not runtime. |
| `_build_mrityu_rows`:854 | esoteric_point_mrityu (3 formulas) | 105 (105/0) | 315 | no | single | :873-889, `tolerance=30.0` | |
| `_build_pranapada_rows`:961 | esoteric_point_pranapada_sphuta | 35 (35/0) | 105 | no | single | PyJHora `pranapada_lagna` only :979-1005, tol 1.0 | |
| `_build_brahma_vishnu_shiva_rows`:1071 | esoteric_point_brahma / vishnu / shiva | 220 (220/0) | 660 | no | single | AK + 120/240 :1114-1116, tol 30.0 :1129 | |
| `_build_saham_rows`:1139 | saham_position (70+ sahams) | 2,800 (2,800/0) | 8,400 | no | single (D1: classical_match on a literal reading) | the former "two-pass" was a tautology and was replaced by a range assertion :1186-1193; tol 1.0 is "a precision declaration" :1194-1196 | `% 360.0` precedes the range guard, so it cannot fail. Largest single family (32% of canon TPV). |
| `_build_karaka_rows`:1208 | karaka_chara_position | 525 (525/0) | 1,575 | no | single | Parashari vs KN Rao are two *schools* emitted as rows; AK divergence only warns :1255-1263; tol 1.0 :1283 | |
| `_build_karakamsa_rows`:1311 | karakamsa_position | 15 (15/0) | 45 | no | single | D9 sign of AK :1332; tol 1.0 | |
| `_build_swamsa_rows`:1362 | swamsa_position | 120 (120/0) | 360 | no | single | :1380-1404 | |
| `_build_arudha_rows`:1408 | arudha_pada | 285 (285/0) | 855 | no | single | `_arudha_sign` :1449-1464 | the same rule is re-implemented by copy in `_build_bhava_arudha_rows` :1589-1602 and the two are never compared (a free same-formula check, `classical_match` at best). |
| `_build_bhava_arudha_rows`:1548 | bhava_arudha | 210 (210/0) | 630 | no | single | :1589-1650 | |
| `_build_midpoint_rows`:1653 | midpoint (54 midpoints) | 1,080 (1,080/0) | 3,240 | no | single | `_midpoint` :1705,1716,1738; MC from `chart_data["midheaven"]` :1673-1684 | |
| `_build_kp_ruling_planets_rows`:1752 | kp_ruling_planets_natal | 50 (50/0) | 150 | no | single | table lookups :1790-1797; day lord from `_WEEKDAY_LORDS` :98-101 | |
| `_build_kp_cuspal_rows`:1820 | kp_cuspal_significators | 300 (300/0) | 900 | no | single | `compute_kp_lords` :1886 once; the cross-check exists only in the sibling `ga_kp_significators` | |
| `_build_aprakasha_rows`:1955 | aprakasha_position | 175 (175/0) | 525 | no | single | formulas :1983-1991, tol 30.0 | |
| `_build_hadda_rows`:2045 | tajik_hadda_lord (60 zones) | 1,200 (0/1,200) | 3,600 | no | single | constant table `_HADDA_LORDS_BY_SIGN` :126-; `tolerance=0.0` :2068 | table emission; nothing is compared. |
| `_build_triraashipathi_rows`:2088 | tajik_triraashipathi | 10 (10/0) | 30 | no | single | :2097-2098 | |
| `_build_tajik_vargottama_rows`:2119 | tajik_vargottama_specific | 15 (15/0) | 45 | no | single | :2126 | |
| `_build_lal_kitab_floored_rows`:2155 | lal_kitab_special_point | 100 (0/100) | 300 | no | single (D4: `floored`) | prerequisite absent, value NULL :2174-2187; 50 canon rows carry no value | a "verified" row with no value. |
| `_build_maharsi_floored_rows`:2192 | maharsi_specific_point | 70 (0/70) | 210 | no | single (D4: `floored`) | :2207-2220; 35 canon rows carry no value | same. |
| `_build_bhrigu_nadi_rows`:2225 | bhrigu_nadi_point | 280 (280/0) | 840 | no | single | BB + n×45° :2241; tol 60.0 | derived from the bhrigu_bindu tautology. |
| `_build_nakshatra_pada_sensitive_rows`:2251 | nakshatra_pada_sensitive | 80 (80/0) | 240 | no | single | `_long_to_nakshatra_pada` :2279; the independent nakshatra derivation lives in `ga_nakshatra`, not compared here | |
| `_build_gulika_mandi_sensitive_rows`:2392 | sensitive_point_gulika_mandi | 70 (0/70) | 210 | no | single | native + day-segment fallback :2408-2422 | |
| `_build_sun_derived_upagrahas_rows`:2467 | sun_derived_upagraha | 140 (0/140) | 420 | no | single | Sun+k·30° :2482-2485 | |
| `_build_special_lagnas_rows`:2506 | special_lagna (7 lagnas) | 245 (245/0) | 735 | no | single | all delegated to PyJHora :2544-2584; tol 1.0 | |
| `_build_sphuta_completion_rows`:2588 | esoteric_point_sphuta_fertility | 70 (0/70) | 210 | no | single | sums :2614-2615 | |
| `_build_yogi_system_completion_rows`:2636 | esoteric_point_yogi_system | 25 (0/25) | 75 | no | single | **literal** `"two_pass_verified"` :2657,2662,2667,2678; table lookups (nak lord, Dagdha rashi) | literals evade the M-22 constant discipline. |
| **ga_sensitive subtotal** | | **8,750 (6,970 / 1,780)** | **26,250** | 175 of 8,750 | 8,750 → single (175 return to TPV when wired) | | |

### 2.2 Other emitters carrying TPV in `chart_facts`

| emitter | fact families | canon | total | 2nd path | current | resulting | evidence | notes |
|---|---|---:|---:|---|---|---|---|---|
| ga_nakshatra `_nakshatra_pada_verdicts` (pipeline/orchestrator/writers/ga_nakshatra.py:108) | graha_nakshatra_join `nakshatra_id_ref`; graha_pada_join `pada_number_ref` | 100 | 200 (abhi 100, cb73 0) | **yes, via verdict** | TPV | **TPV (keep)** | independent 360/27 division `_derive_nakshatra_pada` :92-105 vs PyJHora `nakshatra_id`/`pada`; `two_pass_verdict(engine_i, derived_i)` :147; only the `_ATTRIBUTION_ROWS` keys inherit it :83-86, other rows `single` :203-206 | Same input longitude on both sides; library vs inline code. This is the model the rule describes. |
| ga_kp_significators `emit_kp_significators` (ga_writers/ga_kp_significators.py:169) | kp_planet_significations `star_lord`, `sub_lord` | 90 | 180 | **yes, via verdict (borderline D2)** | TPV | **TPV (keep)** | L0 table `lookup_division` :215 vs `compute_kp_lords` :223; `two_pass_verdict(tuple, tuple)` :224-227 | Two implementations of the same Vimshottari proportional rule (exact-rational L0 table with sign cuts, `brahmagyan/l0_kp_sublord_division.py`, vs iterative float, `ga_nakshatra_compute.py:38-71`). Ruled `classical_match` if SS reads "same formula" strictly. |
| ga_sensitive_degree `build_yogi_points_rows` (ga_writers/ga_sensitive_degree_writer.py:473) | sensitive_point_yogi (YOGI, AVAYOGI, DUPLICATE_YOGI, SAHAYOGI) | 60 | 180 | no | TPV via literals :508,512,524 | **classical_match** | Pass A float vs Pass B integer-arcsecond arithmetic of the same formula and inputs :427-462; `agrees = divergence <= 1.0` computed locally, not via verdict | A same-formula arithmetic re-check; divergence is genuinely possible, so `classical_match`, not `single`. |
| ga_sade_sati `_emit_cycle_rows` (ga_writers/ga_sade_sati_writer.py:851) | sade_sati_cycle (`cycle_start_iso`, `cycle_end_iso`, `duration_days`, `duration_years`); sade_sati_phase (`phase_start_iso`, `phase_end_iso`, `duration_days`, `duration_years`) | 320 | 5,840 (canon 320, abhi 320, cb73 5,200) | no | TPV via `TWO_PASS_VERIFIED` at :893-907, :957-971 | **classical_match** | `two_pass_verify_cycles` :632-659 = duration within ±600 d of 7.5 y (`CYCLE_DAYS_TOLERANCE` :78; the docstring says ±30 d) + date-ordering checks | Bounds/ordering invariants, named as `classical_match` in the rule. cb73's 5,200 are stale rows (see §6). |

Check: 8,750 + 100 + 90 + 60 + 320 = 9,320 canon; all-charts 26,250 + 200 + 180 + 180 + 5,840 = 32,650.

## 3. `two_pass_verified` and other tiers in the other L1 tables

| table / emitter | canon TPV | total TPV | 2nd path | resulting | evidence / notes |
|---|---:|---:|---|---|---|
| `chart_dashas` system `vimshottari` (ga_dashas_writer.py:735 `_apply_vimshottari_independent_verification`) | 45,664 | 114,055 (abhi 49,768; cb73 18,623) | **yes, via verdict** | TPV (keep) | separately coded 4-level recursion `compute_independent_vimshottari_tree` (`_vimshottari_independent_verifier.py:684`); per-row `compare_row` :1097-1147 → `two_pass_verdict(all_agree, True)`; every level 1-4 non-KP row stamped individually (:803-846). Caveat in the module itself: same `moon_sid`/`birth_jd` inputs as the engine (:762-776). |
| `chart_dashas` `mudda` (`_verify_mudda`, :931) | 240 | 780 | partly | **classical_match** | varsha-1 lord vs a transcribed nakshatra→lord table (:927-928, copied from PyJHora constants) + 9-year periodicity invariant :969-975; returns TPV unconditionally at :976, not via verdict. Only the varsha-1 row has any re-derivation. |
| `chart_dashas` `narayana` (`_verify_narayana`, :2181) | 105 | 345 | no | **classical_match** | non-overlap ordering check only :2195-2201; returns TPV at :2201. |
| `chart_dashas` yogini / ashtottari / chara_karaka / naisargika | 0 | 0 (already `classical_match`: canon 386) | no | unchanged | membership checks; `classical_match` per the 2026-08-02 §6.18 ruling (:863,879,898,910). |
| `chart_divisionals` (ga_vargas_writer.py) | **0** | 26,344 (abhi 13,172; cb73 13,172) | n/a | no code change | current writer emits `single` (e.g. :1144, :1433); the TPV rows are stale 2026-07-26/27 builds. Canon was rebuilt 2026-09-07 with zero TPV. |
| `l1_tajik_varsha_year_lords` (ga_tajaka_writer.py:594) | 240 | 475 | no | **classical_match** | `muntha_ok` re-derives with a `+1` loop of the same formula :511-515; `year_lord_ok = bool(tc_winner) and bool(pv_winner)` is a non-empty check :593; `sr_ok` is the root-finder's own residual :238-300. Conditional **literal** `"two_pass_verified"`. The year-lord itself is unexamined (a stricter reading says `single`). |
| `kala_tithi_pravesha` (L3; services/ka_tithi_pravesha/writer.py:208) | 120 | 240 | no | classical_match (not deeply audited) | root-find vs `compute_chart` Moon longitude through the same position engine; a residual bound. Outside L1; listed for completeness. |
| `bodha_msr_signals` (L2) | 4,216 | 14,663 | n/a | follows L1 on rebuild | inherits `verification_pass_status` from the facts it consumes (bo_bimba.py:494-521; mechanism not traced to the last line, see §8). |

## 4. Resulting tier counts (canon `chart_facts` TPV, 9,320 rows)

| outcome | rows | share | source |
|---|---:|---:|---|
| stay `two_pass_verified` | 190 | 2.0% | ga_nakshatra 100, ga_kp_significators 90 |
| → `classical_match` | 380 | 4.1% | ga_sade_sati 320, ga_sensitive_degree 60 |
| → `single` | 8,750 | 93.9% | all ga_sensitive builders |
| of which return to TPV if the upagraha verdict is wired | (175) | | upagraha 5-subject family |

All three charts (32,650 TPV): 380 stay; 6,020 → `classical_match` (sensitive_degree 180, sade_sati 5,840, of which 5,200 are stale cb73 rows); 26,250 → `single` (525 return to TPV when wired).

Splitting ga_sensitive by the tolerance cut in the brief: of **6,970 positive-tolerance** rows, 140 have a real second path (upagraha), 6,830 have none (6,830 → single). Of **1,780 zero-tolerance** rows, 35 have one (UPAKETU), 1,745 have none. 85 of the 1,780 (lal_kitab 50, maharsi 35) carry no value at all.

Downstream (`bodha_writers/formulas.py:535-542`): TPV 1.00 → `single` 0.85 or `classical_match` 0.90; `single` → `classical_match` 0.85 → 0.90. The serve layer counts only TPV as grounding (`verification_vocab.py:VERIFIED_STATUSES`), so canon grounded share of `chart_facts` falls from 9,320/143,299 (6.5%) to 190/143,299 (0.13%), or 365/143,299 (0.25%) with upagraha wired.

## 5. `single_pass` alias rows (chart_facts: canon 10,836; total 10,937)

All emitted as the literal `"single_pass"`. No emitter has a second path.

| emitter | fact families (canon rows) | current | resulting (N-62) | emission sites |
|---|---|---|---|---|
| ga_strength (10,575 canon; 0 on abhi/cb73) | graha_shadbala_sthana/dig/kala/cheshta/drik/total from `compute_shadbala` (210); ashtakavarga_bindu 480 + bindu_sign 480; ashtakavarga_bindu_per_varga 7,200 + pinda_sarva_per_varga 600 | single_pass | **classical_match** (8,970): a bounds/sum invariant ran over exactly these rows | `_verify_shadbala`:643 returns `"single_pass"` at :721 (non-negativity, finiteness, `sum(sub-balas) ≈ total`, "NOT a second independent recomputation" :661); `_verify_ashtakavarga`:724 at :767 (SARVA = 337 ±2; SARVA = sum of 7 PyJHora arrays); `_build_ashtakavarga_per_varga_rows`:1444 (SARVA = 337 per varga) |
| ga_strength (rest of its 10,575) | graha_shadbala_total ratio `achieved_total_div_required_rupa` 35; nodal computed_extension drik/sthana/total 30; ishta_phala 35, kashta_phala 35; vimsopaka ×4 = 140; sthana_bala_per_varga 210; derived ashtakavarga: ekadhipathya 420, trikona 420, kakshya_boundary 120, pinda_bhinna/raasi/sarva/sodhita 160 | single_pass | **single** (1,605): unexamined, the writer broadcasts `verif_status` = min(sb_verif, av_verif) (:1855-1859) onto them, and the vocabulary's own earnedness rule says a verdict over a subset earns only the rows examined | row builders `_build_shadbala_rows`:772, `_build_ashtakavarga_rows`:998, `_build_positional_components_per_varga_rows`:1526 all take `verif_status` |
| ga_panchanga (176) | panchanga_* derived angas, bhadra_flag, panchaka_flag/classification, eclipse_proximity_natal | single_pass | **single** | `_single_pass_verif`:151-152 (def); callers `_emit_disha_shul`:651, `_emit_tithi_shoonya`:692, `_emit_nakshatra_shoonya`:743, `_emit_agni_vasa`:788, `_emit_inauspicious_window`:862, `_emit_auspicious_window`:923, `_emit_bhadra_flag`:980, `_emit_special_yoga_combinations`:1052, `_emit_panchaka_classification`:1094, `_emit_panchaka_flag`:1140, `_emit_eclipse_proximity`:1166 |
| ga_structural (85 canon; 101 abhi) | yoga_label 34, dosha_label 6, graha_composite_state_classification 45 | single_pass | **single** | `_build_yoga_rows`: ga_structural_writer.py:2485; `_build_dosha_rows`:3257; `_build_structural_relationship_rows`:4464 |

Totals: canon 10,836 = 8,970 `classical_match` + 1,866 `single`. All charts 10,937 = 8,970 + 1,967. D5 applies to the 7,800 per-varga rows.

### 5.1 Q16(a) — every site that emits or depends on the `single_pass` spelling

Emitters in L1 (above): ga_panchanga.py:151-152; ga_structural_writer.py:2485, 3257, 4464; ga_strength_writer.py:721, 767, 1444 (and the tier-rank key at :1855). L2 emitters (same alias, `bodha_*` tables; counts canon / total: bodha_cgm_edges 370/1,115, bodha_cgm_nodes 355/951, bodha_msr_signals 3,186/3,262): `pipeline/orchestrator/writers/bo_karanajala.py:706, 783, 1022, 1670, 1730`; `bo_bimba.py:349, 404, 454` and the default at :494. `bo_pramana_mapa.py:433` lists `("single_pass", 2)` in its tier-count table (a reader, must be updated with the emitters).
Not emitters but coupled: `brahmagyan/verification_vocab.py:105-112` (the alias entry); `supabase/migrations/539_chart_facts_verification_pass_status_check.sql` (CHECK includes `single_pass`; the table accepts `single`, so no migration is needed to move emitters); `platform/scripts/backfill/drain_prohibited_verification_status.py` (existing data drain, `single_pass → single`, dry-run by default); `platform/scripts/governance/drift_detector.py:892` and `check_earned_signal.py:146,679` (comments/patterns that name `single_pass`); `bodha_writers/formulas.py:519-538` (alias resolved through `canonical()`); `services/gochara_rules/registry.py:298`, `ashtakavarga.py:15,22,30,39` (the string "tier single_pass verbatim" describes an extract's tier in text, not a stored status); `ga_sade_sati_writer.py:1799-1808` (docstring only, the function returns `UNVERIFIED_DEFAULT`). Tests that assert the spelling were not enumerated.
Related hygiene (N.4: named constants, never bare literals): bare `"single"` literals remain in ga_positions_writer.py:343,393,426; ga_panchanga_writer.py (e.g. :360-604 `vp = "single"`); ga_vargas_writer.py:408,410,1250,1294,1867,2375; ga_structural_writer.py:1281. Counted from `grep`, not exhaustive.

### 5.2 Q16(b) — the eight `_telemetry.update_asset_throughput` call sites (LG-L1-001, R34 residual)

Re-checked at `bf6fe712b`; line numbers match the earlier L1 tier-gap table (taken at `e2352f881`).

| # | asset | direct call | reached from | guard |
|---|---|---|---|---|
| 1 | ga_dashas | ga_dashas_writer.py:3078 (in `_update_asset_throughput`:3067) | :3307 and :3575 | :3307 under `if owns_conn` (:3306); :3575 inside `build_ga_dashas` (def :3492), the CLI-shaped entry, guarded by `if not skip_db` only |
| 2 | ga_panchanga | ga_panchanga_writer.py:1315 | :1481 | `if owns_conn` :1480 |
| 3 | ga_positions | ga_positions_writer.py:693 | :668 | `if owns_conn` :667 (comment :665-666 "legacy standalone CLI") |
| 4 | ga_sade_sati | ga_sade_sati_writer.py:1876 | :2152 | `if owns_conn` :2151 |
| 5 | ga_sensitive | ga_sensitive_writer.py:3038 | :3240 | `if owns_conn` :3239 |
| 6 | ga_strength | ga_strength_writer.py:1961 | :1941 | `if owns_conn` :1940 |
| 7 | ga_structural | ga_structural_writer.py:8143 | :6896 | `if owns_conn` :6895 (comment :6893-6894) |
| 8 | ga_tajaka | ga_tajaka_writer.py:835 (direct) | n/a | `if owns_conn` :833; import comment :48 "legacy CLI path only" |

A ninth `_update_asset_throughput` exists at ga_vargas_writer.py:2779 (calls :3053, :3177), a documented no-op that does not import `_telemetry`. **No grep guard exists today**: the only references to `update_asset_throughput` outside the writers are function tests (`tests/test_a1_telemetry_upsert_guard.py`, `tests/test_a1_duration_rate.py`, `scripts/governance/__tests__/test_a4_d6_engine_conformance.py:207`) and a monkeypatch (`tests/test_ga_orchestrator_conformance.py:237`). To realise "keep the eight, declared CLI-only, with the grep guard" the guard needs an allowlist of these eight call lines (file + enclosing function) and a rule that each is under `owns_conn` (or is #1's :3575 in `build_ga_dashas`); any ninth call from `ga_writers/` fails.

## 6. Stale rows (not reproducible by current code)

- `chart_divisionals`: abhi and cb73 hold 26,344 TPV rows from 2026-07-26/27; current ga_vargas emits none; canon (rebuilt 2026-09-07) has 0.
- `chart_facts` sade_sati: cb73's 5,200 TPV rows span 12 categories current ga_sade_sati emits as `single` (dhaiya_period, kantaka/ashtama/ardha_ashtama/janma/vishakha/anumukha periods, cancellation_check, modifier_overlay, phase_quarter, retrograde_subset, downstream_cross_reference) plus extra cycle/phase keys; all `ga9/1.0.0`, computed 2026-07-27.
- ga_sade_sati's rows on canon and abhi are current-code rows. A tier change in code needs a rebuild (or a targeted backfill) before the stored values move; the existing drain script covers only the `single_pass` spelling.

## 7. Writers that would need a code change (not made)

| # | writer / site | change | rows affected (canon / total) |
|---|---|---|---:|
| 1 | ga_sensitive_writer.py:373 | default `TWO_PASS_VERIFIED` → `UNVERIFIED_DEFAULT`; replace literals :2657,2662,2667,2678; update docstring :9,:23-28 ("every row two-pass verified") | 8,750 / 26,250 |
| 2 | ga_sensitive_writer.py:617-623 (upagraha) | route the PyJHora-vs-BPHS comparison through `two_pass_verdict` (coerce at the call site, e.g. round to 1e-6 deg; the helper is identity-comparison) and pass the result via `_long_rows(verification_pass_status=…)`; KALA stays `single` | 175 / 525 return to TPV |
| 3 | ga_sensitive_degree_writer.py:508,512,524 | literal conditional → `CLASSICAL_MATCH` / `DIVERGENT_FLAGGED` constants | 60 / 180 |
| 4 | ga_sade_sati_writer.py:893-907, 957-971 | `TWO_PASS_VERIFIED` → `CLASSICAL_MATCH` for the 8 bounds/ordering-backed keys | 320 / 5,840 (640 current-code rows + 5,200 stale) |
| 5 | ga_dashas_writer.py:976 (`_verify_mudda`), :2201 (`_verify_narayana`) | return `CLASSICAL_MATCH`; optional: route mudda's varsha-1 anchor through `two_pass_verdict` for that one row | `chart_dashas` 345 / 1,125 |
| 6 | ga_tajaka_writer.py:594 | literal conditional → `CLASSICAL_MATCH` | `l1_tajik_varsha_year_lords` 240 / 475 |
| 7 | ga_strength_writer.py:721,767,1444 + :1855 | `_verify_*` return `CLASSICAL_MATCH`; stop broadcasting `verif_status` to unexamined categories (assign `UNVERIFIED_DEFAULT` to vimsopaka, ratio, ishta/kashta, nodal, per-varga sthana, derived shodhana rows); `_TIER_RANK` key | `single_pass` 10,575 → 8,970 classical_match + 1,605 single |
| 8 | ga_panchanga_writer.py:151-152 | `_single_pass_verif()` returns `UNVERIFIED_DEFAULT` (the 11 callers unchanged) | 176 |
| 9 | ga_structural_writer.py:2485, 3257, 4464 | `verif="single_pass"` → `UNVERIFIED_DEFAULT` | 85 / 186 |
| 10 | bo_karanajala.py (5 sites), bo_bimba.py (3 + default :494), bo_pramana_mapa.py:433 | `single_pass` → constant (L2; Q16(a) covers "tier constants in the L0 module") | bodha tables, see §5.1 |
| 11 | services/ka_tithi_pravesha/writer.py:208 | literal conditional → `CLASSICAL_MATCH` (L3) | 120 / 240 |
| 12 | brahmagyan/verification_vocab.py | none required for the tiers; once no emitter uses it, the `single_pass` alias can stay as read-only legacy | n/a |

**No change needed:** ga_nakshatra, ga_kp_significators (both earn TPV), ga_dashas vimshottari, ga_vargas (already `single`).

## 8. Decisions and caveats for SS

- **D1 (saham, 2,800 canon).** Rated `single` because the only check is a range guard placed after `% 360.0`, which cannot fail. A literal reading of "bounds invariant = classical_match" would give `classical_match` and move 2,800 rows from 0.85 to 0.90.
- **D2 (KP significations, 90 canon).** Kept TPV because the two paths are structurally different (an exact-rational L0 table with sign cuts vs iterative float accumulation) and the verdict goes through `two_pass_verdict`. Both implement the same Vimshottari proportion rule; a strict same-formula reading would make them `classical_match`.
- **D3 (nakshatra/pada joins, 100 canon).** Kept TPV: PyJHora vs an inline division of the same longitude. Same classical division, different implementation.
- **D4 (honest tiers outside N-62).** `floored` for lal_kitab/maharsi (85 canon rows with no value; `floored` is excluded from salience ranking), `computed_extension` for YAMAGANDA_SPHUTA (35) and the strength nodal/ishta-kashta rows. N-62 names only three tiers; these are the more accurate members of the existing vocabulary.
- **D5 (ashtakavarga per-varga, 7,800 canon).** `source_calculation` says `python_heuristic_approximation`; `documented_approximation` (0.60) may fit better than `classical_match` (0.90). Rated `classical_match` only because the SARVA = 337 invariant runs on them.
- **D6 (verdict semantics).** `two_pass_verdict` is an identity comparison. The upagraha comparison needs a tolerance, so the call site must coerce (round) first; the stored diff is 0.0012 arcsec on four subjects because the BPHS constant is written `133.333333`.
- **Not verified here.** All second-path judgments are from code reading, with no mutation test run (read-only task). The ashtakavarga builder was read only to its row-construction preamble (:998-1075), so the claim that `bindu_sign` derives from the examined `bav` rests on the CR-99a docstring (:1033-1040) saying it uses "the SAME bindu values". The bodha MSR inheritance mechanism, the count of bare `"single"` literals, the tests asserting `single_pass`, and the L3 `ka_tithi_pravesha` audit were not completed. Identity of chart `cb73cd3d` was not looked up.

## 9. Method

Per-category counts: `chart_facts` grouped by `verification_pass_status`, `fact_category`, `fact_subject`, with `tolerance_arcsec` split, per chart, 2026-10-02; the sums reconcile (9,320 / 8,750 / 6,970 / 1,780 / 32,650 / 10,836 / 10,937). Other tables: `chart_dashas` by `system_id`, `chart_divisionals`, `l1_tajik_varsha_year_lords`, `kala_tithi_pravesha`, three `bodha_*` tables. Code: `grep` for `two_pass_verdict|TWO_PASS_VERIFIED|UNVERIFIED_DEFAULT|single_pass|classical_match|CLASSICAL_MATCH|two_pass_verified` over `platform/python-sidecar`, then each emitter read at the cited lines.
