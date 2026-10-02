---
artifact: HOOKS_W7_HAND_READBACK
version: 1.1
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (integration-hooks worker, S-L1 phase 3)
decision: SS 2026-10-02 flip_detector condition 2 (W7 hand read-back for everything the tool cannot observe); W7 report = two parts, machine verdict plus hand checks each with expected and actual
scope: documentation only. Every query is a single read-only SELECT for a SELECT-only reader (suvarna_reader); nothing here writes, and no query reads birth data.
changelog:
  - "1.1 (2026-10-03): H22 (H-GP) and H23 (H-VIM) added: the ten canonical graha_position rows (fact_ids identical across the rebuild, build_id changes) and the vimshottari build id, ga_dashas run row and receipt, each with the 2026-10-02 22:10-22:17Z (2026-10-03 03:40-03:47 IST) baseline read as suvarna_reader; H6 note: chart_vichara constituent_fact_ids carry NEW ids on every row at S-L1 (id-change, N-91). The 'after' columns are to be filled at W7."
  - "1.0 (2026-10-02): first version. One entry per lane for what flip_detector.py cannot see (continuous numeric changes, columns it never reads, tables outside its four, the two tier tables, formula_id twins hidden by the sorted occurrence pairing). Before-values were read 2026-10-02 as suvarna_reader on the canonical chart; after-values are the lanes' own evidence."
---

# W7 hand read-back list

How to run (same discipline as FLIP_DETECTOR_README.md): run each query BEFORE the rebuild and save the output, run it again AFTER, compare with the "expected after" column. A subshell that sources the reader's own credentials, read-only, nothing written:

```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -c "<the SELECT>" )
```

The queries use the canonical chart `482012f1-710e-4a25-994a-93821f5871aa`. For another chart replace the UUID (the "expected" figures are canonical unless a row says otherwise). "Before" is production as read 2026-10-02.

## Part 1: the machine verdict

```
python3 platform/scripts/governance/flip_detector.py \
  --compare <PRE_REBUILD_SNAPSHOT.json.gz> \
  --hooks-dir 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks \
  --require-lanes <every top-level hook file stem in the folder> \
  --out <REPORT.json>
```

The lane list is the folder's file stems (`ls *.json` without the extension): argala, argala_other_charts, ashtakavarga_bindu_contributor, band_table, chandra_bala_birth_moon_sign, dasha_scope_cap, ga_condition_fallback, ga_strength_invariant_rows, ga_structural_chart_geometry, ga_vargas_invariant_sentinels, gandanta, karaka_dasha_roles, karaka_roles, karaka_web_order, karaka_web_order_other_charts, sade_sati_placeholder_null, special_lagna_offset, special_lagna_offset_other_charts, sun_required_rupa, tiers, tiers_other_charts, yamakantaka; plus `fa2_ga_vargas` when PR #2858 brings its hook in. With dashas and daily compared, the expected verdict on the canonical chart is NOT_CHECKED (the standing registry is never empty), never FAIL. `--allow-not-checked` only after Part 2 is done and recorded.

## Part 2: hand checks (each: what the detector cannot see, the SQL, before, expected after)

### H1. Sun required_rupa and the ratios (lane sun_required_rupa, #2893)

Not visible: `ratio` and `fact_value_num` of a continuous key change only as detector statistics; the required value 5 to 6.5 is the one class-level change the hook counts (exact 1), the ratios are not.

```sql
SELECT fact_subject, fact_value_num, verification_pass_status FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_shadbala_total' AND fact_key='required_rupa' ORDER BY fact_subject
```

Before: JUP 6.5, MAR 5, MER 7, MOON 6, SAT 5, **SUN 5**, VEN 5.5 (all classical_match). Expected after: **SUN 6.5**, the other six unchanged; tier of every row `single` (tiers lane).

```sql
SELECT r.ayanamsha_id, t.fact_value_num AS rupa, r.fact_value_num AS ratio, round(t.fact_value_num/6.5, 4) AS expected_ratio FROM chart_facts r JOIN chart_facts t ON t.chart_id=r.chart_id AND t.ayanamsha_id=r.ayanamsha_id AND t.fact_category='graha_shadbala_total' AND t.fact_subject=r.fact_subject AND t.fact_key='rupa' WHERE r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND r.fact_category='graha_shadbala_total' AND r.fact_key='ratio' AND r.fact_subject='SUN' ORDER BY 1
```

Before (rupa, ratio): krishnamurti 8.47 / 1.694, lahiri_chitrapaksha 8.47 / 1.694, raman 8.92 / 1.784, surya_siddhanta_classical 8.93 / 1.786, true_chitra 8.47 / 1.694. Expected after: rupa unchanged; ratio equals expected_ratio to 3 decimals (1.3031, 1.3031, 1.3723, 1.3738, 1.3031).

```sql
SELECT ayanamsha_id, fact_subject, citation_human FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_shadbala_total' AND fact_key='rupa' AND ayanamsha_id='lahiri_chitrapaksha' ORDER BY fact_subject
```

Before: all nine rows read "vs required 5.00 rupa". Expected after: each graha states its own required value (SUN 6.50, MOON 6.00, MAR 5.00, MER 7.00, JUP 6.50, VEN 5.50, SAT 5.00) and the two nodes state that no classical minimum exists. (citation_human is not a detector field.)

### H2. Node composite rows (lane sun_required_rupa)

Not visible: the 120 floored rows' NULL values are counted (exact 120) but their tier and the totals are best read directly.

```sql
SELECT fact_key, verification_pass_status, count(*) AS n, count(*) FILTER (WHERE fact_value_num IS NULL) AS n_null FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_in_house_composite_strength' AND (fact_subject LIKE 'RAH_MEAN_IN_HOUSE_%' OR fact_subject LIKE 'KET_MEAN_IN_HOUSE_%') GROUP BY 1,2 ORDER BY 1,2
```

Before: bphs_weighted single 120 (0 null); cross_formula_divergence computed_extension 120 (0 null); simple_multiplication single 120 (0 null). Expected after: bphs_weighted **floored 120, 120 null**; cross_formula_divergence and simple_multiplication **no rows**.

```sql
SELECT count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_in_house_composite_strength'
```

Before 1,620. Expected after **1,380**.

### H3. Tables the sun_required_rupa lane changes outside the detector's four (never read)

```sql
SELECT 'ga_yoga_firings' AS t, count(*) AS n FROM ga_yoga_firings WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' UNION ALL SELECT 'bodha_msr_signals', count(*) FROM bodha_msr_signals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' UNION ALL SELECT 'bodha_rm_resonances', count(*) FROM bodha_rm_resonances WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY 1
```

Before: ga_yoga_firings 53, bodha_msr_signals 50,678, bodha_rm_resonances 45. Expected after the L1 rebuild: row counts unchanged. `ga_yoga_firings.strength` (constituent_bala_v1) moves for the firings that involve the Sun's bala; `bodha_msr_signals.shadbala_norm` and `bodha_rm_resonances` change only when L2 is rebuilt (S-L2), not in S-L1. For the firing strengths:

```sql
SELECT yoga_canonical_id, ayanamsha_id, strength FROM ga_yoga_firings WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY yoga_canonical_id, ayanamsha_id
```

Save before and after; expected: strengths differ only on rows whose constituents include the Sun (see SUN_REQUIRED_RUPA_INTENT_v1_0.md).

### H4. Gandanta formula_id twins and the masked Abhinandan flips (lane gandanta, #2892)

Not visible: the canonical and strict_0_48 rows differ only in `formula_id` (the detector reads occurrence counts, 50, but not the id); an individual false-to-true flip on one of two occurrences is masked by the sorted pairing (README hand-check items 1 and 2).

```sql
SELECT ayanamsha_id, coalesce(formula_id,'<null>') AS formula_id, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_gandanta' AND fact_key='is_gandanta' GROUP BY 1,2 ORDER BY 1,2
```

Before: 10 per ayanamsha, all formula_id NULL (50). Expected after: per ayanamsha **10 with formula_id NULL and 10 with `strict_0_48`** (100 in all).

```sql
SELECT ayanamsha_id, fact_subject, coalesce(formula_id,'<null>') AS formula_id, fact_value_text FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_gandanta' AND fact_key='is_gandanta' ORDER BY 1,2,3
```

Expected after on the canonical chart: no `true` under either formula_id (0 readings flip; canonical Mars and the rest are not within 3 deg 20 min of a junction). On Abhinandan (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`) six NULL-formula readings flip false to true: Mars in krishnamurti, lahiri_chitrapaksha, raman, true_chitra; Venus in raman and surya_siddhanta_classical; the surya_siddhanta Mars reading is true before and after.

```sql
SELECT ayanamsha_id, fact_subject, fact_key, fact_value_text, fact_value_num FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='graha_gandanta' AND fact_key IN ('arc_minutes_from_junction','junction_type','side') ORDER BY 1,2,3
```

Expected after: no rows on the canonical chart (0 detail rows); Abhinandan 15 detail occurrences.

### H5. Special-lagna offset: boundary flags, provenance text, longitudes (lane special_lagna_offset, #2971)

Not visible: longitude is continuous; `near_nakshatra_boundary_flag` and `formula_provenance_text` are columns the detector never reads. The lane's own SELECT-only script covers all of it:

```
python3 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/special_lagna_offset_check.py --snapshot 482012f1-710e-4a25-994a-93821f5871aa --out <path outside the repo>      # BEFORE
python3 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/special_lagna_offset_check.py --compare <that path> 482012f1-710e-4a25-994a-93821f5871aa   # AFTER: must print PASS
```

Expected: 20 longitudes (BHAVA, HORA, GHATI, VIGHATI x 5 ayanamshas) each move by -0.23243 deg (tolerance 0.001); 5 flag flips (BHAVA surya_siddhanta_classical true to false; GHATI krishnamurti, lahiri_chitrapaksha, true_chitra false to true; VIGHATI raman true to false); formula_provenance_text changes on 140 rows and is unchanged on 105 (INDU, SREE, VARNADA untouched); sign, sign_lord, house_d1, nakshatra, nakshatra_lord, pada unchanged; 245 rows. The plain SQL behind the flag count:

```sql
SELECT ayanamsha_id, fact_subject, near_nakshatra_boundary_flag, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='special_lagna' AND fact_key='longitude_sidereal' GROUP BY 1,2,3 ORDER BY 1,2,3
```

### H6. chart_vichara (lane ga_vichara_writer, #2970: DECLARATION ONLY, not a hook)

AN EMPTY FLIP REPORT SAYS NOTHING ABOUT ga_vichara (chart_vichara is outside the detector's four tables; it is in the standing NOT CHECKED registry; the declaration stays at `evidence/ga_vichara_writer_HOOK_DECLARATION.json`). Run the acceptance file and require every row `ok = t`:

```
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; psql -X -A -t -F '|' -f 00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/ga_vichara_writer_ACCEPTANCE.sql )
```

Expected after (canonical): valence_pass **7,500** (1,500 per ayanamsha; before 1,650 each, 8,250); chart_vichara **7,774** (before 8,524); per ayanamsha 1,556 (krishnamurti, lahiri_chitrapaksha, true_chitra) and 1,553 (raman, surya_siddhanta_classical); exact-duplicate rows 0 (before 750); unsorted constituent_fact_ids 0 (before 5,133); orphan ids 0; leverage_index 175 rows all with `as_of`. Totals as a one-line check:

```sql
SELECT count(*) AS total, count(*) FILTER (WHERE vichara_family='valence_pass') AS valence_pass FROM chart_vichara WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
```

Before 8524 | 8250; expected after 7774 | 7500.

Note on `constituent_fact_ids` (corrected 2026-10-03, id-change, N-91 condition 6): the sort is not the only change. At S-L1 the `fact_id` formula drops `build_id`, so every id this lane cites (all of them non-`ga_positions`) is NEW: EVERY surviving row's `constituent_fact_ids` and `constituent_facts_array` change (7,774 canonical rows), not only the 4,773 that were stored unsorted. Membership is natural-key-equivalent (each id replaced by the new id of the same natural key; one-to-one, per-row count unchanged by construction), not id-identical. A8 (0 unsorted) and A9 (0 orphan ids) are the checks that still hold; the id formula match, zero uuid36 and zero orphans in `chart_vichara` and `ga_yoga_firings` are in `../S_L1_BETWEEN_STATE_v1_0.md` (the W7 id check).

### H7. leverage_index as-of equals the run date (lane ga_vichara_writer)

```sql
SELECT value_jsonb->>'as_of' AS as_of, value_jsonb->>'as_of_source' AS as_of_source, count(*) FROM chart_vichara WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND vichara_family='leverage_index' GROUP BY 1,2 ORDER BY 1,2
```

Before: one group with both keys NULL (175 rows, no as_of yet). Expected after: ONE group, 175 rows, `as_of` = the UTC date of the build run's creation (the date the S-L1 ga_vichara run was created: read it from the run record and write it next to this output), `as_of_source` = `build_run_created_at`. A different date, two dates, or a missing key fails the lane (the writer raises on a run without a resolvable date).

### H8. ga_structural argala cells (lane argala, #2851)

Not visible: README item 4 counts rows whose numeric AND text values are both NULL, which stays 0 after this lane (the NULL cells get the text `no_occupant`); read the two columns separately.

```sql
SELECT ayanamsha_id, count(*) AS n, count(*) FILTER (WHERE fact_value_num IS NULL) AS n_num_null, count(*) FILTER (WHERE fact_value_text = 'no_occupant') AS n_no_occupant FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='argala_natal_matrix' GROUP BY 1 ORDER BY 1
```

Before: 4,320 per ayanamsha, 0 and 0. Expected after: 4,320 per ayanamsha; n_num_null = n_no_occupant = krishnamurti 672, lahiri_chitrapaksha 700, raman 672, surya_siddhanta_classical 692, true_chitra 708 (3,444 in all).

```sql
SELECT ayanamsha_id, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='argala_graha_natal' GROUP BY 1 ORDER BY 1
```

Before: no rows. Expected after: krishnamurti 32, lahiri_chitrapaksha 32, raman 32, surya_siddhanta_classical 28, true_chitra 32 (156).

### H9. The two tier tables (lane tiers, #2941)

Use the two queries in FLIP_DETECTOR_README.md ("W7 hand read-back for the two NOT CHECKED tier changes") verbatim. Production counts re-read 2026-10-02 (these are the "before"):

```sql
SELECT ayanamsha_id, system_id, level_n, verification_pass_status AS tier, count(*) AS n, count(DISTINCT build_id) AS builds FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id IN ('mudda','narayana','yogini','ashtottari','chara_karaka','naisargika','vimshottari') AND level_n = 1 GROUP BY 1,2,3,4 ORDER BY 1,2,3,4
```

Before (canonical, all five ayanamshas summed): mudda 240 two_pass_verified, narayana 105 two_pass_verified, yogini 175 / ashtottari 65 / chara_karaka 106 / naisargika 40 classical_match, vimshottari 63 two_pass_verified. Expected after: **mudda classical_match; narayana, yogini, ashtottari, chara_karaka, naisargika single; vimshottari two_pass_verified**; the `n` per (ayanamsha, system) unchanged.

```sql
SELECT ayanamsha_id, verification_pass_status AS tier, count(*) AS n, count(DISTINCT build_id) AS builds FROM l1_tajik_varsha_year_lords WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1,2 ORDER BY 1,2
```

Before: 240 two_pass_verified (Abhinandan 235 two_pass_verified; Kiran 305 already single). Expected after: canonical 240 `single`.

### H10. Vimshottari non-KP levels 1-4 are all two_pass_verified (SS runbook addition, Pravaha dependency)

```sql
SELECT level_n, count(*) AS n, count(*) FILTER (WHERE verification_pass_status <> 'two_pass_verified') AS not_two_pass_verified FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'vimshottari' AND level_n BETWEEN 1 AND 4 GROUP BY 1 ORDER BY 1
```

Before (five ayanamshas summed): level 1 = 63, level 2 = 515, level 3 = 4,576, level 4 = 40,510 rows, 0 not two_pass_verified in each. Expected after: **0 not_two_pass_verified at every level** (row counts may move by a few at the window edges). If any is non-zero: STOP, tell SS before the window is declared complete, and NAME the rows:

```sql
SELECT ayanamsha_id, level_n, lord_graha, start_iso, verification_pass_status, verification_method FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id = 'vimshottari' AND level_n BETWEEN 1 AND 4 AND verification_pass_status <> 'two_pass_verified' ORDER BY 1,2,4 LIMIT 50
```

Expected after: no rows (a `divergent_flagged` row is a real disagreement between the two derivations).

### H11. Karaka dasha roles (lane karaka_dasha_roles, #2886): columns the detector never reads

```sql
SELECT system_id, count(*) AS n, count(*) FILTER (WHERE karaka_role_at_period IS NULL) AS role_null, count(*) FILTER (WHERE karakas_active_during_period IS NULL) AS active_null FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id IN ('vimshottari','vimshottari_kp','ashtottari','mudda','naisargika') GROUP BY 1 ORDER BY 1
```

Before: ashtottari 32,960 / 4,130 / 525; mudda 102,375 / 21,573 / 4,553; naisargika 21,945 / 2,720 / 335; vimshottari 45,664 / 10,126 / 2,261; vimshottari_kp 5,670 / 1,260 / 282. Expected after: n unchanged (row set is unchanged: the hook declares exact 0 appeared / disappeared); role_null falls because Rahu now carries a role (the offline estimate on the canonical chart: 26,708 rows go NULL to a value across the five systems; Ketu, sign lords and yogini names stay NULL); counts may differ by a few rows at the window edges. The distribution by role:

```sql
SELECT system_id, karaka_role_at_period, count(*) FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id IN ('vimshottari','vimshottari_kp','ashtottari','mudda','naisargika') GROUP BY 1,2 ORDER BY 1,2
```

Expected after: 185,883 canonical rows carry a different karaka_role_at_period than before (159,175 value to another value, 26,708 NULL to a value, 0 value to NULL); the roles follow the chart's own kn_rao assignments (H12), not the old fixed Sun-AK / Mars-AmK / ... map.

### H12. Karaka role labels (lane karaka_roles, #2878)

```sql
SELECT fact_subject, fact_key, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='karaka_chara_position' GROUP BY 1,2 ORDER BY 1,2
```

Before: AMATYAKARAKA, ATMAKARAKA, BHRATRIKARAKA, DARAKARAKA, GNATIKARAKA, MATRIKARAKA, PUTRAKARAKA 70 rows each, STRIKARAKA 35 (7 keys x 5 ayanamshas), no PITRIKARAKA, no strikaraka_alias. Expected after: **STRIKARAKA 0, PITRIKARAKA 35, one `strikaraka_alias` row per ayanamsha on DARAKARAKA (5)**; the parashari 7-scheme rows unchanged.

```sql
SELECT ayanamsha_id, fact_subject, fact_key, fact_value_text, fact_value_num FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='karaka_chara_position' AND fact_key IN ('assigned_graha','karaka_rank') AND fact_subject IN ('PITRIKARAKA','PUTRAKARAKA','GNATIKARAKA','DARAKARAKA','STRIKARAKA') ORDER BY 1,2,3
```

Expected after: the school with rank 5 is PITRIKARAKA, 6 PUTRAKARAKA, 7 GNATIKARAKA, 8 DARAKARAKA (each subject takes the next rank's graha), per ayanamsha; ranks 1-4 and every longitude unchanged.

### H13. Karaka web (lane karaka_web_order, #2883)

The detector counts the rows that appear; the per-ayanamsha split and the conjunction doubling are read here.

```sql
SELECT ayanamsha_id, count(*) AS n, count(*) FILTER (WHERE fact_key LIKE 'conjunction%') AS conj, count(*) FILTER (WHERE fact_key LIKE 'aspect%') AS asp FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='karaka_web_per_varga' GROUP BY 1 ORDER BY 1
```

Before: krishnamurti 221 (72 / 149), lahiri_chitrapaksha 219 (80 / 139), raman 226 (68 / 158), surya_siddhanta_classical 206 (74 / 132), true_chitra 228 (83 / 145); total 1,100. Expected after: rows only APPEAR (none disappear, no value changes). The lane's ESTIMATE (offline, on stored varga positions; it cannot be reproduced from stored data, the hook band is 950 to 1,300) is krishnamurti 429, lahiri_chitrapaksha 440, raman 425, surya_siddhanta_classical 424, true_chitra 456 (total 2,174, +1,074); on the rehearsal chart the delta was +1,139. Conjunction rows are now emitted on BOTH subjects, so `conj` doubles by design (Lahiri 80 to 160). The ACTUAL delta is read from the flip report and this query; the estimate is only the band.

### H14. Mudda row counts (chart-dependent, NOT a hook count)

```sql
SELECT ayanamsha_id, count(*) FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id='mudda' GROUP BY 1 ORDER BY 1
```

Before: krishnamurti 20,473; lahiri_chitrapaksha 20,474; raman 20,476; surya_siddhanta_classical 20,477; true_chitra 20,475. Expected after: read and record; the row set moves with the ephemeris lane, not with a hook of this folder (the karaka_dasha_roles hook declares only its own five systems, including mudda, as zero row-set change).

### H15. Placeholder to NULL (lane sade_sati_placeholder_null, #2965)

```sql
SELECT fact_category, count(*) FILTER (WHERE fact_value_text='PENDING_GA7_LOOKUP') AS pending, count(*) FILTER (WHERE fact_key='concurrent_mudda_lord' AND fact_value_text IS NULL) AS null_text, count(*) FILTER (WHERE citation_human LIKE '%no_ga7_period_covers_date%') AS reason_cited FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category IN ('sade_sati_phase','sade_sati_concurrent_dasha_overlay') GROUP BY 1 ORDER BY 1
```

Before: sade_sati_concurrent_dasha_overlay 10 | 0 | 0; sade_sati_phase 30 | 0 | 0. Expected after: overlay **0 | 10 | 10**; phase **0 | 30 | 30**; total row count of both categories unchanged (rows are not removed). Also at W7 (runbook, L1_MV_REFRESH_AFTER_REBUILD_v1_0.md): `mv_chart_sade_sati_lifetime_summary` is left stale by the builder and refreshed afterwards by its owner; record that the refresh happened.

### H16. Chandra Bala birth Moon sign (lane chandra_bala_birth_moon_sign, #2969)

```sql
SELECT fact_subject, fact_value_text FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='chandra_bala_natal_baseline' AND fact_key='classification' AND ayanamsha_id='surya_siddhanta_classical' ORDER BY 1
```

Before: DHANU favorable, KANYA unfavorable, KARKA favorable, KUMBHA favorable, MAKARA unfavorable, MEENA unfavorable, MESHA favorable, MITHUNA unfavorable, SIMHA favorable, TULA neutral, VRISHABHA unfavorable, VRISHCHIKA favorable (each subject is `TRANSIT_SIGN_<NAME>`). Expected after (birth Moon in Pisces): **MEENA favorable, MESHA unfavorable, VRISHABHA favorable, MITHUNA unfavorable, KARKA unfavorable, SIMHA favorable, KANYA favorable, TULA unfavorable, VRISHCHIKA neutral, DHANU favorable, MAKARA favorable, KUMBHA unfavorable**: 9 classification changes (MEENA, MESHA, VRISHABHA, KARKA, KANYA, TULA, VRISHCHIKA, MAKARA, KUMBHA), 3 unchanged (MITHUNA, SIMHA, DHANU).

```sql
SELECT ayanamsha_id, count(*) AS n, count(*) FILTER (WHERE citation_human LIKE '%birth Moon sign=Meena%') AS cites_meena, count(*) FILTER (WHERE citation_human LIKE '%birth Moon sign=Kumbha%') AS cites_kumbha FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='chandra_bala_natal_baseline' AND fact_key='classification' GROUP BY 1 ORDER BY 1
```

Before: 12 rows per ayanamsha, cites_kumbha 12 on every ayanamsha. Expected after: surya_siddhanta_classical **cites_meena 12, cites_kumbha 0**; the four other ayanamshas unchanged (cites_kumbha 12, 0 changed rows).

### H17. INVARIANT sentinels (lane ga_vargas_invariant_sentinels, ga_strength_invariant_rows; #2960 + F-A2)

```sql
SELECT ayanamsha_id, varga, graha, fact_subject, count(*) FROM chart_divisionals WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='scope_cap' GROUP BY 1,2,3,4 ORDER BY 1,2,3,4
```

Before: 2 rows (INVARIANT ALL_VARGAS 1, INVARIANT D81 1). Expected after: **6 rows** (ALL_VARGAS 5 distinct fact_subject values, D81 1), stored count equals what the writer reported (38,596 rows in chart_divisionals in all; before 24,392).

```sql
SELECT fact_category, fact_key, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND ayanamsha_id='INVARIANT' AND fact_category IN ('graha_shadbala_naisargika','graha_shadbala_total') GROUP BY 1,2 ORDER BY 1,2
```

Before and expected after (no change): graha_shadbala_naisargika rupa 9, graha_shadbala_total required_rupa 7 (16 rows).

### H18. Rows that appear for the first time (lanes ashtakavarga_bindu_contributor, dasha_scope_cap, yamakantaka, ga_structural_chart_geometry)

Counted by the detector (exact), listed here so the W7 report records them with their counts.

```sql
SELECT fact_category, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category IN ('ashtakavarga_bindu_contributor','dasha_scope_cap','bhava_chalit_rasi_divergence','combustion_relationship','graha_yuddha','parivartana_pairs','retrograde_aspect_modification') GROUP BY 1 ORDER BY 1
```

Before: no rows (none of the seven categories exists on the canonical chart). Expected after: ashtakavarga_bindu_contributor **3,360**, dasha_scope_cap **1**; the five chart-dependent categories are OPTIONAL (whichever appears, with its count; upper bounds 45 / 30 / 315 / 15 / 85 for bhava_chalit_rasi_divergence / combustion_relationship / graha_yuddha / parivartana_pairs / retrograde_aspect_modification). Record every one that appeared and its count in the W7 report.

```sql
SELECT fact_subject, count(*) FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category='sensitive_point_gulika_mandi' GROUP BY 1 ORDER BY 1
```

Before: GULIKA 35, MANDI 35. Expected after: GULIKA 35, MANDI 35, **YAMAKANTAKA 35**.

### H19. Band table and D1 fallback: outputs in tables the detector never reads (lanes band_table, ga_condition_fallback, #2890)

```sql
SELECT ayanamsha_id, indication_strength, count(*) FROM ga_medical WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1,2 ORDER BY 1,2
```

Before: every ayanamsha mild 4, moderate 4, strong 1. Expected after: 15 rows change `mild` to `moderate` (Saturn x5 ayanamshas, Rahu x5, Ketu x4, Jupiter raman x1): mild falls from 20 to 5 in all, moderate rises from 20 to 35, strong unchanged.

```sql
SELECT direction_impact, count(*) FROM ga_vastu_planet_direction_map WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1 ORDER BY 1
```

Before and expected after (no change): neutral 31, strengthened 4, weakened 5. `ga_condition_composite.condition_score` is expected unchanged on the canonical chart (the lane predicts NO composite change):

```sql
SELECT ayanamsha_id, graha, condition_score FROM ga_condition_composite WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' ORDER BY 1,2
```

### H20. Per-category counts before and after (README hand-check item 4, with the numbers this folder's hooks predict)

```sql
SELECT fact_category, count(*) AS n FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' GROUP BY 1 ORDER BY 1
```

Before: 219 categories, 143,299 rows. Expected after (changes this folder declares; everything else geometry- or ephemeris-driven is read, not predicted): argala_graha_natal +156; ashtakavarga_bindu_contributor +3,360; dasha_scope_cap +1; sensitive_point_gulika_mandi +35; graha_gandanta +50 (50 to 100); graha_in_house_composite_strength -240 (1,620 to 1,380); karaka_chara_position net +5 (525 to 530: PITRIKARAKA +35, STRIKARAKA -35, alias +5); karaka_web_per_varga about +1,074 (band 950 to 1,300); the five chart-dependent categories appear if the geometry produces them. `chart_divisionals` 24,392 to 38,596 (F-A2: varga_ashtakavarga +13,200, varga_house_lord +750, varga_d30_lord_per_amsa +250, scope_cap +4).

### H21. Other tables the detector never reads (README "Other tables the detector never reads")

Use the README count query for ga_yoga_firings, bodha_msr_signals, bodha_rm_resonances (H3 above) and repeat its shape for `ga_condition_composite`, `ga_medical`, the `ga_vastu_*` and `ga_prashna_*` tables and `prashna_charts` (confirm the chart column first). Expected: counts unchanged before and after except where a lane above says otherwise.

### H22. H-GP: the ten canonical graha_position rows keep their fact_id; build_id changes (lane: ga_positions, no hook; N-91 id-change)

Not visible: `flip_detector.py` never selects `fact_id` or `build_id` (FACTID_IMPACT_REPORT.md P1), so a stable or a changed id is invisible to Part 1. `ga_positions` ids are `sha256(category|subject|key|chart|ayanamsha)[:16]` with no `build_id` (`ga_positions_writer.py` `_fact_id`), and S-L1 re-runs `ga_positions`, so the five ga_positions categories (graha_position 430, bhava_cusps 360, house_chalit 225, graha_sign_attributes 100, sandhi_flag 90 = 1,205 rows) keep every id while the other 142,094 chart_facts ids change once. These ten are the lahiri_chitrapaksha `longitude_sidereal` rows (the ten ids are the `fact_id` column in the baseline below). Run BEFORE the rebuild (save), run AFTER (compare).

```sql
SELECT g.fact_subject, g.fact_id, g.fact_id = e.expected_id AS id_identical, g.fact_value_num, g.verification_pass_status AS tier, g.build_id FROM chart_facts g JOIN (VALUES ('JUP','b523f47085a3d9cd'),('KET_MEAN','091bba173f776012'),('LAGNA','456fd2e3322bf33f'),('MAR','e7864e4ce0a32c9f'),('MER','0e8654a3aa27a37c'),('MOON','722b207637ab1208'),('RAH_MEAN','c520713087b97470'),('SAT','ccc73ee023060a1d'),('SUN','bf1524f6ee813be0'),('VEN','7c6e178731526ea0')) AS e(subject, expected_id) ON e.subject = g.fact_subject WHERE g.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND g.fact_category='graha_position' AND g.fact_key='longitude_sidereal' AND g.ayanamsha_id='lahiri_chitrapaksha' ORDER BY g.fact_subject
```

Baseline (before S-L1), read 2026-10-02 22:10-22:17Z as suvarna_reader on the canonical chart. All ten rows: `id_identical` t, tier `single`, `build_id` `1c092ffb-72eb-4614-8422-552ca6eae985`.

| fact_subject | fact_id | fact_value_num (before) | tier | build_id (before) |
|---|---|---|---|---|
| JUP | b523f47085a3d9cd | 249.787497023181 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| KET_MEAN | 091bba173f776012 | 229.033044100281 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| LAGNA | 456fd2e3322bf33f | 12.4311495988431 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| MAR | e7864e4ce0a32c9f | 198.519187554622 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| MER | 0e8654a3aa27a37c | 270.838753918698 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| MOON | 722b207637ab1208 | 327.055230133129 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| RAH_MEAN | c520713087b97470 | 49.0330441002811 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| SAT | ccc73ee023060a1d | 202.431986059195 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| SUN | bf1524f6ee813be0 | 291.962617284992 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |
| VEN | 7c6e178731526ea0 | 259.172696089456 | single | 1c092ffb-72eb-4614-8422-552ca6eae985 |

Expected after: ten rows returned (ZERO rows means the ids changed: STOP and tell SS). **`fact_id` IDENTICAL on all ten and `id_identical` t on all ten**; **`build_id` CHANGES** to the build of the S-L1 `ga_positions` run (one value on all ten, different from `1c092ffb-...`; record it here: ______); `fact_value_num` and `tier` per the hooks' expectations, which declare NO change to `graha_position` (it is in no hook's `may_change`; the tiers lane's category list excludes it): values identical to the baseline and tier `single`. A different value or tier would also read UNDECLARED_CHANGE in Part 1. After-values: to be filled at W7.

The whole family, so the 1,205 is read as a count and not assumed:

```sql
SELECT fact_category, count(*) AS n, count(*) FILTER (WHERE fact_id = left(encode(sha256(convert_to(fact_category||'|'||fact_subject||'|'||fact_key||'|'||chart_id::text||'|'||ayanamsha_id,'UTF8')),'hex'),16)) AS n_formula_match, count(DISTINCT build_id) AS builds, min(build_id::text) AS build_id FROM chart_facts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND fact_category IN ('graha_position','bhava_cusps','house_chalit','graha_sign_attributes','sandhi_flag') GROUP BY 1 ORDER BY 1
```

Baseline (2026-10-02 22:10-22:17Z): bhava_cusps 360 | 360 | 1; graha_position 430 | 430 | 1; graha_sign_attributes 100 | 100 | 1; house_chalit 225 | 225 | 1; sandhi_flag 90 | 90 | 1; build_id `1c092ffb-72eb-4614-8422-552ca6eae985` on all five. Expected after: the same n and n_formula_match (1,205 in all), builds 1, build_id = the new `ga_positions` build id (same as above). `chart_fact_identity` (its `fact_id` foreign key is ON DELETE CASCADE, so the `ga_positions` rebuild empties it until the G-IDX refill):

```sql
SELECT count(*) AS identity_rows FROM chart_fact_identity i JOIN chart_facts f USING (fact_id) WHERE f.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
```

Baseline 1,205. Expected after: 0 between the `ga_positions` rebuild and the refill (`build_fact_identity_index.py`, immediately after W2), **1,205 after the refill**.

### H23. H-VIM: the new vimshottari build id, the ga_dashas run row and its receipt (lane: karaka_dasha_roles, tiers; SS Pravaha dependency, see H10)

Not visible: the machine verdict reads neither `build_id` nor the run tables. H10 above is the count check (vimshottari non-KP levels 1 to 4, `not_two_pass_verified` must be 0 after the rebuild; baseline 63 / 515 / 4,576 / 40,510 rows, all `two_pass_verified`, today 0 not two_pass_verified); H9 holds the level-1 tier of every system. H23 adds the identity of the build that produced them. Run BEFORE and AFTER.

```sql
SELECT ayanamsha_id, build_id, count(*) AS n, count(*) FILTER (WHERE verification_pass_status <> 'two_pass_verified') AS not_two_pass_verified FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND system_id='vimshottari' GROUP BY 1,2 ORDER BY 1,2
```

Baseline (2026-10-02 22:10-22:17Z, all levels of the non-KP `vimshottari` system, 45,664 rows = 63 + 515 + 4,576 + 40,510 for levels 1 to 4): krishnamurti 9,194; lahiri_chitrapaksha 9,205; raman 9,063; surya_siddhanta_classical 8,998; true_chitra 9,204; every group one `build_id` = `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb`, 0 not_two_pass_verified. Expected after: five groups, ONE new `build_id` (the S-L1 `ga_dashas` run id; record: ______) on all five, **0 not_two_pass_verified** in every group (non-zero: STOP, tell SS, name the rows with the H10 query; Pravaha's writer and inventory verifier refuse any vimshottari row that is not `two_pass_verified`); counts may move by a few rows at the window edges (the same note as H10).

```sql
SELECT r.id AS run_id, r.state AS run_state, r.created_at, a.state AS asset_state, a.output_changed, a.disposition FROM build_run_assets a JOIN build_runs r ON r.id = a.run_id WHERE r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND a.asset_id='ga_dashas' ORDER BY r.created_at DESC LIMIT 5
```

Baseline (the five newest ga_dashas run rows, 2026-10-02 22:10-22:17Z): `f2a62f44-eed7-4138-8b15-d57515a6f88a` completed 2026-09-07 20:14:00+00 complete / output_changed f / skip_no_delta; `a105a76f-1a9e-42a4-9149-c12358635e91` failed 2026-09-07 20:12:30+00 aborted; `bcae04a3-9e46-476b-944f-a985b46225c5` completed 2026-09-07 12:58:28+00 complete / f / skip_no_delta; `da74fbb1-84af-42f1-ae44-260608ffe615` completed 2026-09-07 12:56:18+00 complete / f / skip_no_delta; `1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb` completed 2026-09-07 09:44:10+00 complete / **t** / **build**. The data in `chart_dashas` is the build run `1f89fd4c-...` (run id = `build_id`); the four later rows are skip_no_delta (they wrote nothing). Expected after: a NEW newest row for the S-L1 run with asset_state `complete`, output_changed **t**, disposition **build** (a `skip_no_delta` disposition means nothing was rebuilt: the window has not rebuilt ga_dashas), and its `run_id` equals the new `build_id` of the first query. Its receipt:

```sql
SELECT asset_id, partition_key, receipt_state, observed_at, build_id, left(output_digest,12) AS output_digest_12 FROM asset_provenance_receipts WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ga_dashas' ORDER BY observed_at DESC LIMIT 5
```

Baseline: one row, `__whole_asset__`, `proven`, observed 2026-09-07 20:14:04+00, `build_id` `f2a62f44-eed7-4138-8b15-d57515a6f88a` (the latest skip_no_delta run, not the build run), output_digest `483dd7787c48`. Expected after: a `proven` receipt NEWER than that one (S-L1 acceptance: every rebuilt ga_* asset has a PROVEN receipt newer than its pre-window one) whose `output_digest_12` DIFFERS from `483dd7787c48` (expected: this lane set changes ga_dashas values by design, the karaka role columns and the tiers; across S-L1 a changed output digest is expected on the digest-spec'd assets by construction and is not by itself evidence of an unintended value change, see `../S_L1_BETWEEN_STATE_v1_0.md`). After-values: to be filled at W7.
