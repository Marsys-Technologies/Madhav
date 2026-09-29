---
artifact: FABLE_REVIEW_EVIDENCE_APPENDIX
canonical_id: FABLE_REVIEW_EVIDENCE_APPENDIX
version: "1.0"
status: EVIDENCE_RECORD
date: 2026-09-29
purpose: "Publishes, with the exact predicate, every production measurement the FABLE astrological review (v1.0/v2.0/v3.0) cites as [L] and that the external reviewers could not reproduce from packet artifacts (Kimi K3 amendment 5: 'a sealed plan cannot rest on numbers its own evidence base does not contain'). Predicate, not number (DVA Ruling 16 / GOCHARA_NATIVE_RULINGS §7.7)."
access: "amjis (production), role amjis_app, read-only, via the session's MCP postgres tool; queries run 2026-09-29 between 23:05 and 01:10 UTC (re-run of E1–E3 at ~01:05 UTC gave identical figures)"
chart: "482012f1-710e-4a25-994a-93821f5871aa unless stated; E1 uses the only chart carrying '4.0' contacts at query time (1c826d5a — structurally identical build, counts within 1 row of chart 1's deleted candidate per step06_evidence.md) as a structural proxy"
---

# Evidence appendix — production measurements behind the FABLE Gochara review

## E1 — '4.0' contact ledger composition (finding #6, #7, #27)

```sql
select relation, target_type, count(*) n, sum(case when t_in = t_out then 1 else 0 end) zero_span
from kala_gochara_contacts where generation='4.0' group by relation, target_type order by 1,2;
```

| relation | target_type | n | zero_span |
|---|---|---|---|
| conjunction | dasha_lord_portfolio / karaka / sensitive_degree | 253 each | 0 |
| drishti_contact | dasha_lord_portfolio / karaka / sensitive_degree | 369 each | 0 |
| return | dasha_lord_portfolio / karaka / sensitive_degree | 29 each | 0 |
| kakshya_cell_crossing | dasha_lord_portfolio / karaka / sensitive_degree | 31,401 each | 31,401 |
| nakshatra_ingress | dasha_lord_portfolio / karaka / sensitive_degree | 9,774 each | 9,774 |
| sign_ingress | dasha_lord_portfolio / karaka / sensitive_degree | 4,167 each | 4,167 |
| sign_ingress | arudha | 356 | 356 |
| sign_ingress | bhava | 361 | 361 |
| sign_ingress | mechanism_node | 140 | 140 |

Derived: total 138,836; zero-width 136,887 (**98.6 %**); non-zero-width rows 1,953 = 759 conjunction + 1,107
dṛṣṭi + 87 return, i.e. **253 / 369 / 29 physical contacts** each carried under three target types (the same
graha degrees resolve as kāraka, daśā-portfolio and sensitive-degree targets). Every bhāva, ārūḍha and
mechanism-node target appears only as a zero-width `sign_ingress` row. The identical per-target-type
counts (e.g. 31,401 × 3) show boundary crossings are enumerated once per target rather than once per body.

## E2 — house-vedha overlay composition and horizon (finding #17, #25)

```sql
select graha, count(*) n, min(window_start), max(window_end),
       sum(case when (detail->>'obstruction_active')='false' then 1 else 0 end) inactive,
       sum(case when (detail->>'cancelled')='true' then 1 else 0 end) cancelled
from kala_vedha_gochara where chart_id='482012f1-…' and vedha_kind='house_vedha' group by graha;
```

| graha | n | window span | inactive | cancelled |
|---|---|---|---|---|
| Moon | 99 | 2026-08-05 → 2027-11-01 | 53 | 27 |
| Venus | 13 | 2026-08-01 → 2027-10-27 | 1 | 7 |
| Sun | 5 | 2026-07-29 → 2027-08-16 | 0 | 4 |
| Mercury | 4 | 2026-09-07 → 2027-11-01 | 1 | 3 |
| Mars | 2 | 2026-09-18 → 2027-04-25 | 0 | 2 |
| Jupiter | 2 | 2026-10-31 → 2027-11-01 | 0 | 2 |
| Saturn | 1 | 2027-06-03 → 2027-10-19 | 0 | 0 |
| Ketu | 1 | 2026-11-26 → 2027-11-01 | 0 | 1 |

Derived: 127 house-vedha rows, **99 Moon**; 55 with no active obstruction; 46 vipareeta-cancelled; the
overlay exists only inside 2026-07-29 → 2027-11-01 (the plan's own "1.26 % of the served century",
GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §2.1). The gate reads only `detail.malefic_count`
(legacy_semantics.py:724-772), so the 55 inactive and 46 cancelled rows attenuate.

## E3 — resonance map: negative-result sensitive checks still targets (finding #9)

```sql
select m.target_type, count(*) n_rows,
       sum(case when f.fact_value_text in ('not_gandanta','not_pushkara','not_fired','none') then 1 else 0 end) negative_result_rows,
       count(distinct m.event_class) classes
from gochara_resonance_map m left join chart_facts f on f.fact_id = m.target_ref
where m.chart_id='482012f1-…' group by 1;
```

| target_type | rows | negative-result rows | classes |
|---|---|---|---|
| sensitive_degree | 176 | **154** | 27 |
| yoga_constituent | 220 | 0 | 27 |
| mechanism_node | 93 | 0 | 25 |
| bhava / arudha | 68 / 68 | 0 | 27 |
| lord | 52 | 0 | 27 |
| karaka / dasha_lord_portfolio | 44 / 44 | 0 | 27 |

Derived: the production map is the pre-WP3c build (F-19/R-1 not applied); `ardhachandra` and `chatra`
(F-21) are still present (verified by row listing for marriage/childbirth/separation, 2026-09-29).
`max(computed_at)` on the map = 2026-09-10.

## E4 — served '3.0' windows carry no tārā term (finding #5)

```sql
select jsonb_object_keys(term_breakdown) k, count(*) from kala_gochara_windows
where chart_id='482012f1-…' and generation='3.0' and term_breakdown is not null group by 1;
```
Keys present (380 rows): `activity`, `activity_terms`, `formula`, `lambda_v3`, `permission`, `promise`,
`quality_gates`. The stored `formula` string is `PROMISE × PERMISSION × activity × quality_gates` — no
tārā, no w30. `suppression_state->'tara'` is absent on all 914 rows.

## E5 — '4.0' per-class plateau (finding #24), from `.run/wp10_tranche2/prod_link3_delta_report_482012f1.md`

Era-tier rows per class and the share at the modal peak value (grep over the per-window table):

| class | era rows | modal peak value | rows at modal |
|---|---|---|---|
| childbirth | 41 | 0.627200 | 27 |
| marriage | 50 | 0.519400 | 32 |
| financial_deception | 66 | 0.558600 | 39 |
| major_gain | 53 | 0.754600 | 23 |
| business_launch | 53 | 0.833000 | 23 |

Modal value = permission × 0.98 (a single exact contact saturates activity at 1.0; quality_gates 0.98
outside the overlay window). v2.0 quoted "13 peaks at 0.6272 in 2020–22" — a subset; the whole-decade
figure is 27 of 41. All 1,435 era rows carry `valence = favourable`.

## E6 — per-class permission constants ('4.0'), from `.run/wp10_tranche2/link3_class_context_482012f1.json`

One boolean per (class, system), union over the class's candidate instants in 2020–2030. Example: marriage
`{vimshottari: false, yogini: false, ashtottari: false, chara_karaka: false, naisargika: true, mudda: true,
kalachakra: true, narayana: true, sade_sati: true, guru_shani_double_transit: true, av_threshold: true,
planetary_return: false}` → permission 0.53 for the whole decade. `sade_sati: true` on all 27 classes.

## E7 — authority, publication and windows state (2026-09-29 23:05 UTC)

`kala_gochara_authority`: both charts `'3.0'` (482012f1 flipped_at 2026-09-28 19:29:06 UTC — the F-0
reversal). `kala_gochara_publication`: 482012f1 `'4.0'/rolled_back`; 1c826d5a `'4.0'/candidate`.
`kala_gochara_windows`: `'v1'` 38,287; `'3.0'` 1,830; no `'4.x'` rows.

## E8 — L0 positions for the worked events (`ref_planet_position_get`, Lahiri sidereal)

| date | Sun | Moon | Mars | Mercury | Jupiter | Venus | Saturn | Rahu | Ketu |
|---|---|---|---|---|---|---|---|---|---|
| 2013-12-11 | 235.56 | 348.50 | 157.81 | 225.78 | 84.57 R | 272.87 | 204.25 | 192.99 | 12.99 |
| 2018-11-28 | 222.07 | 112.22 | 313.75 | 219.43 R | 220.31 | 183.83 | 253.43 | 93.92 | 273.92 |
| 2022-01-03 | 258.91 | 269.14 | 230.71 | 277.45 | 306.87 | 267.83 R | 288.01 | 36.87 | 216.87 |

Natal (`chart_facts`, lahiri_chitrapaksha, build 1c092ffb): Lagna 12.43 · Sun 291.96 · Moon 327.06 ·
Mars 198.52 · Mercury 270.84 · Jupiter 249.79 · Venus 259.17 · Saturn 202.43 · Rahu 49.03 · Ketu 229.03.

## E9 — corpus checks performed on the OCR subset (2026-09-29, after the Kimi K3 review)

- `KP_Reader/vol5/kp_reader_5_transits_djvu.txt:1330-1337`: Venus favourable 1,2,3,4,5,8,9,11,12 with vedha
  8,7,1,10,9,5,11,6,3 → **11→6, 12→3**. Seed `brahmagyan/l0_transit.py:646,655` has 11→3, 12→6. Secondary
  transcription; the served Phaladīpikā PG323 chunk must be counted before the seed is corrected.
- `BPHS/bphs_vol1_rsanthanam_djvu.txt:16496-16502`: ordinary aspects graduated ¼/½/¾/full at 3-10 / 5-9 /
  4-8 / 7; "All planets aspect the 7th fully. Saturn, Jupiter and Mars have special aspects" — specials full.
- `BPHS/bphs_vol2_rsanthanam_djvu.txt:3256-3262` (Aṣṭottarī: Rahu, not in lagna, in a kendra or trikoṇa from
  the lagna lord) and `:3593-3596` (day birth in kṛṣṇa-pakṣa / night birth in śukla-pakṣa).
- `bphs_vol2:42332-42335`: SAV >30 favourable, 25–30 medium, <25 adverse. `:41956-41959`: Saturn's transit
  through rāśis with more rekhas in Saturn's aṣṭakavarga is favourable.
