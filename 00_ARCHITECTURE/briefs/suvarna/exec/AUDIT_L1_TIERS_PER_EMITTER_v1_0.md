---
canonical_id: AUDIT_L1_TIERS_PER_EMITTER
version: 1.1
status: ACCEPTED_BY_SS_WITH_RULINGS   # resulting-tier tables below are the SPEC for the tier-honesty writer lane
date: 2026-10-02
branch: suvarna/land/TI-l1-tier-audit-001   # PR #2852
code_base: bf6fe712bdc3c186a864d7de79f42fe8d64de0f0   # all file:line citations; origin/main has since moved by one docs/migration commit that touches none of the cited files
mode: READ-ONLY (no code change, no DB write, no build). DB reads as suvarna_reader only.
rule_audited: "SS N-62 / Q03 — two_pass_verified ONLY for an independent re-derivation compared through two_pass_verdict; bounds/ordering invariants and same-formula arithmetic re-checks = classical_match; the 1,780 zero-tolerance default rows = single"
changelog:
  - "1.0 (2026-10-02) — first issue (per-emitter audit, 6 open decisions D1-D6)."
  - "1.1 (2026-10-02) — SS rulings applied: saham = single; one-sentence second-path test applied to every emitter that keeps or earns TPV (ga_nakshatra moves to classical_match, KP stays); 85 valueless rows = floored; YAMAGANDA_SPHUTA = computed_extension; per-varga ashtakavarga = documented_approximation; per-row single_pass split (no alias swap); upagraha wired through two_pass_verdict; new columns 'second path differs because' and 'required test'; headline totals recomputed under the rulings."
---

# L1 verification tiers, per emitter (N-62 / Q03 audit) — v1.1

Charts: **canon** = `482012f1-710e-4a25-994a-93821f5871aa`; **abhi** = `1c826d5a-41cb-4450-b4dc-59d440e5f75a`; **cb73** = `cb73cd3d-9eba-4220-9902-0de91566e980`. "total" = canon + abhi + cb73. Counts read live on 2026-10-02 as `suvarna_reader`. Paths relative to `platform/python-sidecar/`.

## 0. SS rulings applied in this version

| # | ruling | where applied |
|---|---|---|
| R1 | Saham 2,800 = `single` (a guard that cannot fail is not a check). | §2.1 |
| R2 | Test for every emitter that keeps or earns `two_pass_verified`: *would a bug in the primary formula be caught by the second path?* Different algorithm or different inputs (table lookup vs arithmetic, cross-ayanamsha agreement) keeps TPV; same formula re-coded over the same inputs = `classical_match`; if the difference cannot be stated in one sentence, `classical_match`. The sentence is the column "second path differs because". | §2.2 (nakshatra moves, KP stays, upagraha earns, Vimshottari stays) |
| R3 | The 85 valueless ga_sensitive rows = `floored`; YAMAGANDA_SPHUTA = `computed_extension`. | §2.1 |
| R4 | Per-varga ashtakavarga (7,800) = `documented_approximation`. | §6 |
| R5 | `single_pass` rows: `classical_match` only for rows an invariant actually examined; rows that merely had a tier broadcast onto them = `single`; no blanket alias swap. Per-row split by emitter. | §6 |
| R6 | Upagraha cross-check wired through `two_pass_verdict` (round at the call site) so the 175 rows earn the tier. mudda, narayana, tajik year lords, sade sati, sensitive_degree = `classical_match`; Vimshottari stays. | §2.1, §2.2, §3 |

### 0.1 Vocabulary and constraint verification (for R3, R4)

- `floored`, `computed_extension` and `documented_approximation` are all members of `brahmagyan/verification_vocab.py` (entries at lines 116, 122, 128 of the tuple; `verified: False`), and of the mirror in `platform/src/lib/retrieval/envelope.ts:82-84`.
- Live constraint `chart_facts_verification_pass_status_check` (read from `pg_constraint`) lists all three plus `classical_match`, `single`, `single_pass` and the rest. It is **`convalidated = false`** (added `NOT VALID`, migration 539): it is enforced on every new insert/update but was never validated against existing rows. Zero live `chart_facts` rows are outside the 13 members (query: 0).
- `chart_dashas` and `chart_divisionals` accept only `{two_pass_verified, classical_match, divergent_flagged, single}` (+ `scope_cap_sentinel` on `chart_dashas`); nothing in the rulings writes `floored`, `computed_extension` or `documented_approximation` there.
- `floored` and the other four "no value" members are in `EXCLUDED_NO_VALUE_STATUSES` (`bodha_writers/formulas.py`): the 85 rows leave salience ranking (rescale 0.0). `computed_extension` weighs 0.75, `documented_approximation` 0.60, `classical_match` 0.90, `single` 0.85, TPV 1.00 (`formulas.py:535-542`).
- **New finding (not a ruling):** `ga_strength_writer.py:1437` stamps the string `"floored_sarva_mismatch"`, which is **not a vocabulary member**. The live table has no such row (the SARVA = 337 invariant has not failed), but the first time it fails the insert will be rejected by the constraint (or, if the constraint were ever dropped, stored as an illegal value). It belongs in the tier-honesty lane: emit `floored` (or halt).

## 1. Headline totals under the rulings

Population audited: every `chart_facts` row currently `two_pass_verified` or `single_pass` (canon 9,320 + 10,836 = 20,156; all charts 32,650 + 10,937 = 43,587). Other rows are unchanged.

| tier after rulings | canon, from TPV (9,320) | canon, from `single_pass` (10,836) | **canon, both populations** | **all three charts, both populations** |
|---|---:|---:|---:|---:|
| `two_pass_verified` | 265 | 0 | **265** | **705** |
| `classical_match` | 480 | 1,170 | **1,650** | **2,510** |
| `documented_approximation` | 0 | 7,800 | **7,800** | **7,800** |
| `computed_extension` | 35 | 0 | **35** | **105** |
| `floored` | 85 | 0 | **85** | **255** |
| `single` | 8,455 | 1,866 | **10,321** | **32,212** |
| total | 9,320 | 10,836 | **20,156** | **43,587** |

All-charts TPV population 32,650 → TPV 705, `classical_match` 1,340, `computed_extension` 105, `floored` 255, `single` 30,245. All-charts `single_pass` population 10,937 → `classical_match` 1,170, `documented_approximation` 7,800, `single` 1,967.

Whole canonical `chart_facts` (143,299 rows) after the rulings: `single` 126,128 · `documented_approximation` 8,820 · `computed_extension` 3,890 · `floored` 2,450 · `classical_match` 1,664 (incl. the 14 existing rows, see §8 open item) · `two_pass_verified` **265** (0.18%, down from 9,320 = 6.5%) · `pending_w3_verification` 50 · `not_defined_for_nodes` 32. No `single_pass` row remains once the emitters and a backfill land. All three charts (421,096 rows): `single` 388,498 · `documented_approximation` 10,210 · `computed_extension` 11,490 · `floored` 7,350 · `classical_match` 2,552 · `two_pass_verified` **705** · `pending_w3_verification` 150 · `not_defined_for_nodes` 96 · `divergent_flagged` 45.

Serve-layer effect: only TPV counts as grounding (`verification_pass_status` vocabulary `VERIFIED_STATUSES`), so canonical grounded `chart_facts` fall from 9,320 to 265 rows. Salience weight moves: TPV → `single` 1.00 → 0.85; TPV → `classical_match` 1.00 → 0.90; `single` → `classical_match` 0.85 → 0.90; `single` → `documented_approximation` 0.85 → 0.60.

Reading the audit's earlier shortcut, now settled by the data: positive `tolerance_arcsec` is not evidence of a second path. Of the 6,970 positive-tolerance rows only 140 (upagraha) have one; of the 1,780 zero-tolerance rows 35 (UPAKETU) have one and 85 carry no value.

## 2. `two_pass_verified` rows in `chart_facts`, per emitter (spec)

**Resulting** = the tier the writer must stamp. **Required test** names are defined in §5; every one is a mutation test (remove or stub the check, the tier must drop; or perturb the input, the tier must flip to `divergent_flagged`).

### 2.1 ga_sensitive (`ga_writers/ga_sensitive_writer.py`)

All rows are TPV today from the default `verification_pass_status: str = TWO_PASS_VERIFIED` at `_make_row` :373 (the four yogi-system rows from literals). Canon column shows canon rows (pos-tol / zero-tol).

| emitter (builder:line) | fact families | canon | total | 2nd path | resulting | second path differs because | evidence | required test |
|---|---|---:|---:|---|---|---|---|---|
| `_build_upagraha_rows`:551 (5 subjects) | upagraha_position DHUMA, VYATIPATA, PARIVESHA, INDRACHAPA, UPAKETU | 175 (140/35) | 525 | yes | **two_pass_verified**, once wired (today: unearned) | The primary is PyJHora's `solar_upagraha_longitudes`, computed inside the library from its own Sun position, and the second path is the BPHS Ch.3 algebra over the exported Sun longitude, a pair that already caught the V-6 Upaketu formula defect, so a wrong constant or sign in either surfaces as a diff. | :585-589 vs :613-621; stored diff 0.0012″ (4 subjects), 0 (UPAKETU) | TS-VERDICT |
| `_build_upagraha_rows`:551 (KALA) | upagraha_position KALA | 35 (0/35) | 105 | no | **single** | none: PyJHora native only, formula slot is `None` :601. | :623 | TS-DEFAULT |
| `_build_saturn_derived_rows`:654 | GULIKA_LAHIRI, MANDI, MAANDI | 105 (105/0) | 315 | no | **single** | none: PyJHora native value, tolerance 36″ is a declared constant; MAANDI re-emits MANDI's value. | :681-740 | TS-DEFAULT |
| `_build_saturn_derived_rows`:654 | YAMAGANDA_SPHUTA | 35 (0/35) | 105 | no | **computed_extension** (R3) | none: `Saturn + 240°`, its own provenance text says "computed_extension". | :755-766 | TS-EXT |
| `_build_bhrigu_bindu_rows`:772 | esoteric_point_bhrigu_bindu | 35 (35/0) | 105 | no (tautology) | **single** | none: `bb_verify` is the identical `_midpoint(moon, rahu)` call; `max(tol, 1.0)` manufactures the positive tolerance. | :781-790 | TS-DEFAULT |
| `_build_yogi_avayogi_rows`:794 | esoteric_point_yogi, _avayogi | 140 (140/0) | 420 | no | **single** | none: two convention variants emitted side by side; agreement with `sensitive_point_yogi` is test-only. | :822-849 | TS-DEFAULT |
| `_build_mrityu_rows`:854 | esoteric_point_mrityu | 105 (105/0) | 315 | no | **single** | none: three alternative formulas, not cross-checked. | :873-889 | TS-DEFAULT |
| `_build_pranapada_rows`:961 | esoteric_point_pranapada_sphuta | 35 (35/0) | 105 | no | **single** | none: PyJHora native only. | :979-1005 | TS-DEFAULT |
| `_build_brahma_vishnu_shiva_rows`:1071 | esoteric_point_brahma / vishnu / shiva | 220 (220/0) | 660 | no | **single** | none: AK + 120°/240°. | :1114-1129 | TS-DEFAULT |
| `_build_saham_rows`:1139 | saham_position | 2,800 (2,800/0) | 8,400 | no | **single** (R1) | none: the only check is a range guard after `% 360.0`, which cannot fail. | :1186-1196 | TS-DEFAULT |
| `_build_karaka_rows`:1208 | karaka_chara_position | 525 (525/0) | 1,575 | no | **single** | none: Parashari vs KN Rao are two schools, divergence only warns. | :1255-1263 | TS-DEFAULT |
| `_build_karakamsa_rows`:1311 | karakamsa_position | 15 (15/0) | 45 | no | **single** | none: D9 sign of AK. | :1332 | TS-DEFAULT |
| `_build_swamsa_rows`:1362 | swamsa_position | 120 (120/0) | 360 | no | **single** | none. | :1380-1404 | TS-DEFAULT |
| `_build_arudha_rows`:1408 | arudha_pada | 285 (285/0) | 855 | no | **single** | none: the same rule is copy-implemented in `_build_bhava_arudha_rows` and never compared (a free `classical_match` candidate, not taken). | :1449-1464 | TS-DEFAULT |
| `_build_bhava_arudha_rows`:1548 | bhava_arudha | 210 (210/0) | 630 | no | **single** | none. | :1589-1650 | TS-DEFAULT |
| `_build_midpoint_rows`:1653 | midpoint | 1,080 (1,080/0) | 3,240 | no | **single** | none: arithmetic on upstream longitudes; MC from Swiss Ephemeris once. | :1673-1747 | TS-DEFAULT |
| `_build_kp_ruling_planets_rows`:1752 | kp_ruling_planets_natal | 50 (50/0) | 150 | no | **single** | none: lookups, day lord from a weekday table. | :1790-1797 | TS-DEFAULT |
| `_build_kp_cuspal_rows`:1820 | kp_cuspal_significators | 300 (300/0) | 900 | no | **single** | none here (the cross-check exists only in `ga_kp_significators`). | :1886 | TS-DEFAULT |
| `_build_aprakasha_rows`:1955 | aprakasha_position | 175 (175/0) | 525 | no | **single** | none. | :1983-2028 | TS-DEFAULT |
| `_build_hadda_rows`:2045 | tajik_hadda_lord | 1,200 (0/1,200) | 3,600 | no | **single** | none: constant-table emission, nothing compared. | :126-, :2068 | TS-DEFAULT |
| `_build_triraashipathi_rows`:2088 | tajik_triraashipathi | 10 (10/0) | 30 | no | **single** | none. | :2097 | TS-DEFAULT |
| `_build_tajik_vargottama_rows`:2119 | tajik_vargottama_specific | 15 (15/0) | 45 | no | **single** | none. | :2126 | TS-DEFAULT |
| `_build_lal_kitab_floored_rows`:2155 | lal_kitab_special_point: `house` (NULL value) | 50 | 150 | no | **floored** (R3) | none: prerequisite absent, no value was computed. | :2174-2180 | TS-FLOOR |
| | `absent_prerequisite_flag` (value "true") | 50 | 150 | no | **single** | none: the flag is a stated absence, not a verified value. | :2181-2187 | TS-DEFAULT |
| `_build_maharsi_floored_rows`:2192 | maharsi_specific_point: `longitude_sidereal` (NULL) | 35 | 105 | no | **floored** (R3) | none. | :2207-2213 | TS-FLOOR |
| | `absent_prerequisite_flag` | 35 | 105 | no | **single** | none. | :2214-2220 | TS-DEFAULT |
| `_build_bhrigu_nadi_rows`:2225 | bhrigu_nadi_point | 280 (280/0) | 840 | no | **single** | none: derived from the bhrigu_bindu tautology. | :2237-2246 | TS-DEFAULT |
| `_build_nakshatra_pada_sensitive_rows`:2251 | nakshatra_pada_sensitive | 80 (80/0) | 240 | no | **single** | none (the independent derivation lives in ga_nakshatra, not compared here). | :2279 | TS-DEFAULT |
| `_build_gulika_mandi_sensitive_rows`:2392 | sensitive_point_gulika_mandi | 70 (0/70) | 210 | no | **single** | none. | :2408-2422 | TS-DEFAULT |
| `_build_sun_derived_upagrahas_rows`:2467 | sun_derived_upagraha | 140 (0/140) | 420 | no | **single** | none. | :2482-2485 | TS-DEFAULT |
| `_build_special_lagnas_rows`:2506 | special_lagna | 245 (245/0) | 735 | no | **single** | none: all delegated to PyJHora. | :2544-2584 | TS-DEFAULT |
| `_build_sphuta_completion_rows`:2588 | esoteric_point_sphuta_fertility | 70 (0/70) | 210 | no | **single** | none. | :2614-2615 | TS-DEFAULT |
| `_build_yogi_system_completion_rows`:2636 | esoteric_point_yogi_system | 25 (0/25) | 75 | no | **single** | none: lookups; four literal `"two_pass_verified"` strings. | :2657,2662,2667,2678 | TS-DEFAULT |
| **ga_sensitive, canon** | | **8,750** | **26,250** | | TPV 175 · floored 85 · computed_extension 35 · **single 8,455** | | | |

All-charts for the same split: TPV 525 · floored 255 · computed_extension 105 · single 25,365.

### 2.2 Other emitters carrying TPV in `chart_facts`

| emitter | fact families | canon | total | resulting | second path differs because | evidence | required test |
|---|---|---:|---:|---|---|---|---|
| ga_nakshatra `_nakshatra_pada_verdicts` (pipeline/orchestrator/writers/ga_nakshatra.py:108) | graha_nakshatra_join `nakshatra_id_ref`; graha_pada_join `pada_number_ref` | 100 | 200 | **classical_match** (moves from TPV) | It cannot be stated: the first path `drik.nakshatra_pada` is itself `int(longitude / (360/27))` plus a remainder division, and the second path `_derive_nakshatra_pada` is the same floor division over the same exported longitude, so a bug in the shared formula would not be caught. | `jhora/panchanga/drik.py` `nakshatra_pada` vs ga_nakshatra.py:92-105; verdict call :147 | TS-NAK |
| ga_kp_significators `emit_kp_significators` (ga_writers/ga_kp_significators.py:169) | kp_planet_significations `star_lord`, `sub_lord` | 90 | 180 | **two_pass_verified** (keep) | One path locates the lord in the L0 table of precomputed exact-rational boundaries (`bg_kp_sublord_division`, with rāśi cuts) and the other walks a float arcminute accumulation in `compute_kp_lords`, so a rounding, boundary-tie or accumulation bug in either surfaces as a mismatch (the shared Vimśottarī rule and the test-pinned equal year constants are not independently checked). | :215 vs :223; verdict :224-227; `brahmagyan/l0_kp_sublord_division.py:196` (`build_divisions`), `ga_nakshatra_compute.py:38-71` | TS-KP |
| ga_sensitive_degree `build_yogi_points_rows` (ga_writers/ga_sensitive_degree_writer.py:473) | sensitive_point_yogi | 60 | 180 | **classical_match** | Not different: Pass B is the same sum in integer arcseconds over the same Sun and Moon longitudes. | :427-462; literals :508,512,524 | TS-YOGI |
| ga_sade_sati `_emit_cycle_rows` (ga_writers/ga_sade_sati_writer.py:851) | sade_sati_cycle and sade_sati_phase, keys `cycle_start_iso`, `cycle_end_iso`, `phase_start_iso`, `phase_end_iso`, `duration_days`, `duration_years` | 320 | 5,840 | **classical_match** (the six keys); every other key stays `single` | Not different: the check is a ±600-day duration bound and date-ordering over the engine's own output. | :632-659, :78, :893-907, :957-971 | TS-SADE |

Check: canon 8,750 + 100 + 90 + 60 + 320 = 9,320. After rulings: TPV 175 + 90 = 265; classical_match 100 + 60 + 320 = 480; floored 85; computed_extension 35; single 8,455.

## 3. Other L1 tables

| table / emitter | canon TPV | total TPV | resulting | second path differs because | evidence | required test |
|---|---:|---:|---|---|---|---|
| `chart_dashas` `vimshottari` (ga_dashas_writer.py:735) | 45,664 | 114,055 | **two_pass_verified** (stays, R6) | The verifier rebuilds all four levels separately in Julian-day space with a closed-form 120-year cycle jump and its own transcribed lord/year tables, whereas the engine walks date-based periods iteratively, and it is discrimination-tested against wrong-lord and boundary-shifted inputs (the inputs `moon_sid`/`birth_jd` and the recursion rule are shared). | `_vimshottari_independent_verifier.py:684`; `compare_row` :1097-1147 → `two_pass_verdict(all_agree, True)`; applied :803-846 | TD-VIM |
| `chart_dashas` `mudda` (`_verify_mudda`:931) | 240 | 780 | **classical_match** (R6) | Not different: a transcribed copy of PyJHora's nakshatra→lord tables plus a 9-year periodicity invariant, and only the varsha-1 row is re-derived. | :927-928, :969-976 | TD-MUD |
| `chart_dashas` `narayana` (`_verify_narayana`:2181) | 105 | 345 | **classical_match** (R6) | Not different: a non-overlap ordering check. | :2195-2201 | TD-NAR |
| `l1_tajik_varsha_year_lords` (ga_tajaka_writer.py:594) | 240 | 475 | **classical_match** (R6) | Not different: `muntha_ok` repeats the same `+1` arithmetic, `year_lord_ok` is a non-empty test, `sr_ok` is the root-finder's own residual. | :511-515, :593-594, :238-300 | TD-TAJ |
| `chart_dashas` yogini / ashtottari / chara / naisargika | 0 | 0 (existing `classical_match`: canon 386) | unchanged | membership checks (2026-08-02 §6.18 ruling) | ga_dashas_writer.py:863,879,898,910 | TD-MEMB |
| `chart_divisionals` (ga_vargas_writer.py) | **0** | 26,344 (abhi 13,172, cb73 13,172) | no code change | current writer emits `single`; the TPV rows are stale 2026-07-26/27 builds | e.g. :1144, :1433 | none (stale data, rebuild) |
| `kala_tithi_pravesha` (L3, services/ka_tithi_pravesha/writer.py:208) | 120 | 240 | not ruled; recommended `classical_match` | Not different: a root-find residual through the same position engine. | :207-212 | TK-TIT |
| `bodha_msr_signals` (L2) | 4,216 | 14,663 | follows L1 on rebuild | n/a | bo_bimba.py:494-521 | n/a |

## 4. Stale rows (not reproducible by current code)

- `chart_divisionals`: 26,344 TPV rows on abhi/cb73 from July builds; canon (rebuilt 2026-09-07) has 0.
- `chart_facts` sade_sati on cb73: 5,200 TPV rows (`ga9/1.0.0`, 2026-07-27). Of these, 320 sit in the six examined keys (→ `classical_match` under the spec) and 4,880 sit in keys and categories the current writer emits as `single` (→ `single`). Canon and abhi sade_sati rows are current-code rows.
- A writer change moves no stored value until a rebuild or targeted backfill runs; the existing `platform/scripts/backfill/drain_prohibited_verification_status.py` (dry-run by default) only rewrites the spellings `PASS`, `pass`, `single_pass` to `single`, so it must not be run on the ga_strength rows before the per-row split in §6 is applied.

## 5. Required tests (named once, referenced above)

Each fails if the tier is stamped without the check having run.

| id | test | mutation that must fail it |
|---|---|---|
| TS-DEFAULT | Build every ga_sensitive builder over a fixed fixture chart; assert the status set per category equals §2.1 and that only the upagraha five-subject family, TS-FLOOR and TS-EXT rows differ from `single`. Assert `_make_row()` with no status returns `UNVERIFIED_DEFAULT`. | Restore the `TWO_PASS_VERIFIED` default at :373 (or a literal in `_build_yogi_system_completion_rows`): fixture assertions fail. |
| TS-VERDICT | Perturb the PyJHora native upagraha longitude by 1″ and by 1°: status must be `divergent_flagged`; unperturbed: `two_pass_verified`. | Replace the comparison with a constant (or call `two_pass_verdict(x, x)`): the perturbed case must stop returning `divergent_flagged`, failing the test; delete the comparison: the tier must drop to `single`. |
| TS-FLOOR | Every ga_sensitive row whose `fact_value_num`, `fact_value_text` and `fact_value_jsonb` are all NULL has status `floored`. | Stamp such a row `single` or TPV: fails. |
| TS-EXT | YAMAGANDA_SPHUTA rows are `computed_extension`. | Revert to default: fails. |
| TS-NAK | With the check stubbed to a no-op, `graha_nakshatra_join`/`graha_pada_join` rows are `single`; with `engine_nakshatra_id` perturbed by 1 the rows are `divergent_flagged`; with the check run and agreeing they are `classical_match`. | Return `classical_match` without calling `_derive_nakshatra_pada`: the stub case fails. |
| TS-KP | Perturb one boundary in the injected `divisions` so `lookup_division` and `compute_kp_lords` disagree at a test longitude: `star_lord`/`sub_lord` rows are `divergent_flagged`; agreement: `two_pass_verified`. | Replace the second path with the first (`live = div`): the perturbed case no longer diverges and the test fails. |
| TS-YOGI | Force Pass A and Pass B apart by monkeypatching the offset constant in one path: rows are `divergent_flagged`; stub the comparison: rows are `single`. | Stamp `classical_match` unconditionally: fails. |
| TS-SADE | Feed `two_pass_verify_cycles` a cycle with a 900-day duration and a cycle with `janma_entry <= vishakha_entry`: build halts; stub the function to `[]` returning without running: the six keys must be `single`. | Remove the call or the halt: fails. |
| TD-VIM | Existing discrimination tests in `ga_writers/__tests__/test_vimshottari_independent_verifier.py`, plus: an engine row with a swapped lord is stamped `divergent_flagged` in the real write path (`_apply_vimshottari_independent_verification`). | Skip the apply call: every Vimshottari row must drop to `single`. |
| TD-MUD / TD-NAR / TD-TAJ / TD-MEMB / TK-TIT | For each verifier: input that violates the invariant raises (build halts); stub the verifier to return without checking: stamped rows must be `single`. | Hard-code the tier return: fails. |
| TS-STR-1 | `_verify_shadbala` / `_verify_ashtakavarga` return the tier only after the checks have run; with them stubbed to `UNVERIFIED_DEFAULT`, the examined categories in §6 drop to `single`; corrupting one sub-bala (negative magnitude) or SARVA total (≠ 337) halts the build. | Return `classical_match` from the stub: fails. |
| TS-STR-2 | A fixture ashtakavarga per-varga set with SARVA ≠ 337 yields a legal vocabulary member (not `floored_sarva_mismatch`); all per-varga rows carry `documented_approximation`. | Reintroduce the non-member string: `assert_legal` fails. |
| TS-STR-3 | Rows of the unexamined categories in §6 (vimsopaka, ratio, ishta/kashta, nodal, per-varga sthana, derived shodhana, pinda_*, kakshya) are `single` regardless of the verifier's return. | Broadcast the verifier tier onto them again: fails. |
| TS-PAN / TS-STRUCT | Every row from the 11 `_emit_*` functions in ga_panchanga and the three `verif=` sites in ga_structural is `single`; a repo grep test fails on any new bare `single_pass` literal in `ga_writers/` and `pipeline/orchestrator/writers/`. | Re-add `"single_pass"`: grep test fails. |

## 6. `single_pass` rows, per-row split (chart_facts: canon 10,836; total 10,937)

| emitter | fact families | canon | total | resulting | why | emission sites |
|---|---|---:|---:|---|---|---|
| ga_strength | graha_shadbala_sthana / dig / kala / cheshta / drik / total (`compute_shadbala`) | 210 | 210 | **classical_match** | Examined: `_verify_shadbala` runs non-negativity, finiteness, total > 0 and `sum(sub-balas) ≈ total` over exactly these seven grahas' values (:665-701). | `_verify_shadbala`:643 returns at :721 |
| ga_strength | ashtakavarga_bindu, ashtakavarga_bindu_sign | 960 | 960 | **classical_match** | Examined: both are emitted verbatim from the checked `bav` arrays (:1090-1098), and `_verify_ashtakavarga` checks SARVA = 337 ± 2 and SARVA = house-wise sum of the seven arrays (:735-752). | `_verify_ashtakavarga`:724 returns at :767 |
| ga_strength | ashtakavarga_bindu_per_varga 7,200; ashtakavarga_pinda_sarva_per_varga 600 | 7,800 | 7,800 | **documented_approximation** (R4) | `source_calculation` is `python_heuristic_approximation.ashtakavarga_per_varga`; the SARVA = 337 check is real but does not make the values exact. | `_build_ashtakavarga_per_varga_rows`:1444 |
| ga_strength | graha_shadbala_total ratio `achieved_total_div_required_rupa` | 35 | 35 | **single** | Not examined: a derived division. | `_build_shadbala_rows`:772 (`verif_status` broadcast) |
| ga_strength | nodal rows (drik, sthana, total; `nodal_dignity_and_drik_bphs`) | 30 | 30 | **single** | Not examined: nodes are outside the `shadbala` dict the verifier reads. | same |
| ga_strength | graha_ishta_phala, graha_kashta_phala | 70 | 70 | **single** | Not examined: derived `sqrt(uchcha × cheshta)`. | same |
| ga_strength | graha_vimsopaka_{dasavarga, saptavarga, shadvarga, shodasavarga} | 140 | 140 | **single** | Not examined. | same |
| ga_strength | graha_sthana_bala_per_varga (`classical_dignity_table`) | 210 | 210 | **single** | Not examined: table lookup. | `_build_positional_components_per_varga_rows`:1526 |
| ga_strength | ashtakavarga_ekadhipathya_shodhana 420, trikona_shodhana 420, kakshya_boundary 120, pinda_bhinna 40, pinda_raasi 40, pinda_sarva 40, pinda_sodhita 40 | 1,120 | 1,120 | **single** | Not examined: the check reads the raw bindus only; the code's own comment says shodhana correctness is unchecked (:758-767). | `_build_ashtakavarga_rows`:998 |
| ga_panchanga | panchanga_* derived angas, bhadra_flag, panchaka_flag and classification, eclipse_proximity_natal | 176 | 176 | **single** | No check of any kind. | `_single_pass_verif`:151-152; callers `_emit_disha_shul`:651, `_emit_tithi_shoonya`:692, `_emit_nakshatra_shoonya`:743, `_emit_agni_vasa`:788, `_emit_inauspicious_window`:862, `_emit_auspicious_window`:923, `_emit_bhadra_flag`:980, `_emit_special_yoga_combinations`:1052, `_emit_panchaka_classification`:1094, `_emit_panchaka_flag`:1140, `_emit_eclipse_proximity`:1166 |
| ga_structural | yoga_label 34, dosha_label 6, graha_composite_state_classification 45 | 85 | 186 (abhi 101) | **single** | Catalog-rule evaluation, no second path. | `_build_yoga_rows` ga_structural_writer.py:2485; `_build_dosha_rows`:3257; `_build_structural_relationship_rows`:4464 |
| **total** | | **10,836** | **10,937** | classical_match 1,170 · documented_approximation 7,800 · single 1,866 (all charts 1,967) | | |

Note: the 35 `graha_shadbala_total` rows in the "ratio" line and the 35 in the "examined" line are distinct (`source_calculation` `achieved_total_div_required_rupa` vs `compute_shadbala`), so the split is per row, not per category.

### 6.1 Q16(a): every site that emits or depends on the `single_pass` spelling

- L1 emitters: `ga_writers/ga_panchanga_writer.py:151-152`; `ga_writers/ga_structural_writer.py:2485, 3257, 4464`; `ga_writers/ga_strength_writer.py:721, 767, 1444` (and the tier-rank key at :1855).
- L2 emitters (same alias; canon / total rows: bodha_cgm_edges 370 / 1,115, bodha_cgm_nodes 355 / 951, bodha_msr_signals 3,186 / 3,262): `pipeline/orchestrator/writers/bo_karanajala.py:706, 783, 1022, 1670, 1730`; `bo_bimba.py:349, 404, 454` and the default at :494. `bo_pramana_mapa.py:433` reads the spelling (a tier table) and must change with them.
- Coupled, not emitters: `brahmagyan/verification_vocab.py` (alias entry, lines 105-112); `platform/supabase/migrations/539_chart_facts_verification_pass_status_check.sql` (CHECK includes `single_pass`, so moving emitters needs no migration); the drain script above; `scripts/governance/drift_detector.py:892` and `check_earned_signal.py:146,679` (comments and patterns naming it); `bodha_writers/formulas.py:519-538` (alias resolved through `canonical()`); `services/gochara_rules/registry.py:298`, `ashtakavarga.py:15,22,30,39` (text "tier single_pass verbatim", not a stored status); `ga_sade_sati_writer.py:1799-1808` (docstring only). Tests asserting the spelling were not enumerated.
- Hygiene (N.4 named constants): bare `"single"` literals remain in ga_positions_writer.py:343,393,426; ga_panchanga_writer.py (e.g. :360-604); ga_vargas_writer.py:408,410,1250,1294,1867,2375; ga_structural_writer.py:1281 (from `grep`, not exhaustive).

### 6.2 Q16(b): the eight `_telemetry.update_asset_throughput` call sites (LG-L1-001)

| # | asset | direct call | reached from | guard |
|---|---|---|---|---|
| 1 | ga_dashas | ga_dashas_writer.py:3078 (in :3067) | :3307, :3575 | :3307 under `if owns_conn` (:3306); :3575 inside `build_ga_dashas` (def :3492), the CLI entry, behind `if not skip_db` only |
| 2 | ga_panchanga | ga_panchanga_writer.py:1315 | :1481 | `if owns_conn` :1480 |
| 3 | ga_positions | ga_positions_writer.py:693 | :668 | `if owns_conn` :667 |
| 4 | ga_sade_sati | ga_sade_sati_writer.py:1876 | :2152 | `if owns_conn` :2151 |
| 5 | ga_sensitive | ga_sensitive_writer.py:3038 | :3240 | `if owns_conn` :3239 |
| 6 | ga_strength | ga_strength_writer.py:1961 | :1941 | `if owns_conn` :1940 |
| 7 | ga_structural | ga_structural_writer.py:8143 | :6896 | `if owns_conn` :6895 |
| 8 | ga_tajaka | ga_tajaka_writer.py:835 (direct) | n/a | `if owns_conn` :833 |

A ninth `_update_asset_throughput` at ga_vargas_writer.py:2779 (calls :3053, :3177) is a documented no-op that does not import `_telemetry`. No grep guard exists today (only function tests: `tests/test_a1_telemetry_upsert_guard.py`, `tests/test_a1_duration_rate.py`, `scripts/governance/__tests__/test_a4_d6_engine_conformance.py:207`, and a monkeypatch in `tests/test_ga_orchestrator_conformance.py:237`). The guard for "keep the eight, declared CLI-only": an allowlist of these eight call lines by (file, enclosing function), a rule that each sits under `owns_conn` (or is #1's :3575 in `build_ga_dashas`), and failure on any ninth call from `ga_writers/`.

## 7. Writers needing a code change (spec for the tier-honesty lane; none made here)

| # | writer / site | change | rows (canon / total) |
|---|---|---|---:|
| 1 | ga_sensitive_writer.py:373 | default → `UNVERIFIED_DEFAULT`; replace literals :2657, 2662, 2667, 2678; docstring :9, :23-28; add `FLOORED` / `COMPUTED_EXTENSION` stamping for the 85 NULL-valued rows and YAMAGANDA_SPHUTA (named constants in `verification_vocab.py`) | 8,750 / 26,250 |
| 2 | ga_sensitive_writer.py:613-650 (upagraha) | compute `two_pass_verdict(round(native, 6), round(bphs, 6))` per subject (identity helper, so round at the call site; the stored diff is 0.0012″ because BPHS constant is written `133.333333`), pass via `_long_rows(verification_pass_status=…)`; KALA unchanged | 175 / 525 earn TPV |
| 3 | ga_nakshatra.py:147 | stamp `CLASSICAL_MATCH` on agreement (still `DIVERGENT_FLAGGED` on disagreement) instead of the verdict's TPV | 100 / 200 |
| 4 | ga_sensitive_degree_writer.py:508, 512, 524 | literal conditionals → `CLASSICAL_MATCH` / `DIVERGENT_FLAGGED` | 60 / 180 |
| 5 | ga_sade_sati_writer.py:893-907, 957-971 | `TWO_PASS_VERIFIED` → `CLASSICAL_MATCH` | 320 / 5,840 (960 examined-key rows, of which 320 are stale cb73 rows; plus 4,880 stale cb73 rows that become `single` on rebuild) |
| 6 | ga_dashas_writer.py:976, 2201 | `_verify_mudda`, `_verify_narayana` return `CLASSICAL_MATCH` | chart_dashas 345 / 1,125 |
| 7 | ga_tajaka_writer.py:594 | literal conditional → `CLASSICAL_MATCH` | 240 / 475 |
| 8 | ga_strength_writer.py:721, 767, 1437, 1444, 1855 | `_verify_*` return `CLASSICAL_MATCH`, applied only to the §6 examined categories; per-varga rows `DOCUMENTED_APPROXIMATION`; every other category `UNVERIFIED_DEFAULT` (no `verif_status` broadcast); replace `"floored_sarva_mismatch"` with a vocabulary member | 10,575 canon: 1,170 / 7,800 / 1,605 |
| 9 | ga_panchanga_writer.py:151-152 | `_single_pass_verif()` returns `UNVERIFIED_DEFAULT` | 176 |
| 10 | ga_structural_writer.py:2485, 3257, 4464 | → `UNVERIFIED_DEFAULT` | 85 / 186 |
| 11 | bo_karanajala.py (5), bo_bimba.py (3 + :494), bo_pramana_mapa.py:433 | alias → constant (L2) | see §6.1 |
| 12 | services/ka_tithi_pravesha/writer.py:208 | → `CLASSICAL_MATCH` (L3, not ruled) | 120 / 240 |
| 13 | brahmagyan/verification_vocab.py | add named constants `FLOORED`, `COMPUTED_EXTENSION`, `DOCUMENTED_APPROXIMATION` (only `CLASSICAL_MATCH`, `TWO_PASS_VERIFIED`, `DIVERGENT_FLAGGED`, `UNVERIFIED_DEFAULT` exist today); keep the `single_pass` alias entry as read-only legacy | n/a |

No change: ga_kp_significators (keeps TPV), ga_dashas Vimshottari (keeps TPV), ga_vargas (already `single`).

## 8. Open items and caveats

- **Unruled, flagged:** the 14 existing canon `classical_match` rows (ga_strength `naisargika` 7 and `required_rupa` 7; 42 across charts) are stamped by hard-coded assignment (ga_strength_writer.py:800, 849) with no comparison run; by the same test they are `single` unless SS rules the table-constant emission as a relay match. `ka_tithi_pravesha` (120 / 240 TPV, L3) was not ruled.
- **Same-formula limit of KP.** The KP verdict keeps TPV on SS's "table lookup vs arithmetic" test, but both paths implement the same Vimśottarī rule with year constants pinned equal by `tests/test_bg_kp_sublord_division.py`; the second path catches implementation and boundary bugs, not a wrong rule.
- **Not verified here.** All judgments are from code reading; no mutation test was run (read-only). The Vimshottari second-path sentence rests on the verifier's own docstring and test names; I did not re-run its discrimination tests. The bodha MSR inheritance mechanism, the count of bare `"single"` literals, the tests asserting `single_pass`, and the L3 `ka_tithi_pravesha` path were not fully traced. Chart `cb73cd3d`'s identity was not looked up.

## 9. Method

`chart_facts` grouped by `verification_pass_status`, `fact_category`, `fact_subject`, `tolerance_arcsec` (positive / zero), per chart; `chart_dashas` by `system_id`; `chart_divisionals`, `l1_tajik_varsha_year_lords`, `kala_tithi_pravesha`, three `bodha_*` tables; `pg_constraint` for the three tables' CHECKs. Sums reconcile: 9,320 / 8,750 / 6,970 / 1,780 / 32,650 / 10,836 / 10,937; after rulings 20,156 canon and 43,587 all-charts; whole-table canonical 143,299 and all-charts 421,096. Code: `grep` for `two_pass_verdict|TWO_PASS_VERIFIED|UNVERIFIED_DEFAULT|single_pass|classical_match|CLASSICAL_MATCH|two_pass_verified` over `platform/python-sidecar`, then each emitter read at the cited lines, and PyJHora's `drik.nakshatra_pada` source read directly for the nakshatra ruling.
