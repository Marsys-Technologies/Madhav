---
artifact: L0_FINDINGS_ADDENDUM
version: "1.1"
status: "LIVING; findings recorded as given; items marked (R) are provisional until the J1 independent review. v1.1 = v1.0 (UNEDITED, still cited as evidence; F-L0-01..04 stay there) + F-L0-08"
produced_by: exec-suvarna
produced_on: 2026-10-02
scope: "docs only; read-only database reads as suvarna_reader; no database write"
---

# L0 Brahmagyan findings addendum, v1.1 (delta over v1.0)

## F-L0-08 · Stored TRUE Ketu `speed_dps` and `is_retrograde` are inverted relative to Rahu on every date (R)

**Finding (measured 2026-10-02, read-only).** In `public.ephemeris_daily` (asset `bg_ephemeris`, L0) the TRUE-node rows carry, for Ketu, a `speed_dps` that is the NEGATION of Rahu's and an `is_retrograde` flag that is the opposite of Rahu's, on ALL 91,676 paired dates. Ketu's longitude is exactly Rahu + 180° (checked: 0 pairs off by more than 1e-6°), so Ketu's angular speed and its retrograde flag must EQUAL Rahu's; the stored Ketu values are wrong on every row.

Aggregate (one `ayanamsha_id` value, `tropical`; 183,352 Rahu+Ketu rows; no zero-speed row, so "negated" and "different" coincide):
```sql
SELECT r.node_mode,
       count(*)                                                                  AS paired_dates,
       count(*) FILTER (WHERE k.speed_dps IS DISTINCT FROM r.speed_dps)          AS speed_differs,
       count(*) FILTER (WHERE k.speed_dps = -r.speed_dps AND r.speed_dps <> 0)   AS speed_negated,
       count(*) FILTER (WHERE k.is_retrograde IS DISTINCT FROM r.is_retrograde)  AS flag_differs,
       count(*) FILTER (WHERE abs(((k.tropical_longitude - r.tropical_longitude - 180) % 360 + 540) % 360 - 180) > 0.000001) AS lon_not_180
FROM public.ephemeris_daily r
JOIN public.ephemeris_daily k ON k.date = r.date AND k.ayanamsha_id = r.ayanamsha_id AND k.node_mode IS NOT DISTINCT FROM r.node_mode AND k.body = 'Ketu'
WHERE r.body = 'Rahu' GROUP BY 1;
-- true | 91676 | 91676 | 91676 | 91676 | 0
SELECT body, node_mode, count(*) AS n, count(*) FILTER (WHERE is_retrograde) AS retrograde, count(*) FILTER (WHERE is_retrograde IS NOT TRUE) AS not_retrograde
FROM public.ephemeris_daily WHERE body IN ('Rahu','Ketu') GROUP BY 1,2 ORDER BY 1,2;
-- Ketu | true | 91676 | 23732 | 67944
-- Rahu | true | 91676 | 67944 | 23732
```
Rahu is retrograde on 67,944 of 91,676 days (**74.1%**: the TRUE node reverses direction about 26% of the days; it is not "always retrograde", which is a mean-node property), Ketu on 23,732. Example 2026-11-25: Rahu speed −0.1791 retrograde (t), Ketu +0.1791 direct (f); 2026-11-26 (stored): Rahu −0.1415931 t, Ketu +0.1415931 f; 2026-11-30: Rahu +0.0030703 f (a TRUE-node station), Ketu −0.0030703 t.
**Credit:** Pravāha measured the paired-date aggregate first (91,676 pairs; Ketu speed = −Rahu speed on all; flags inverted on all) and SS accepted the verification; the SQL above is Exec Suvarṇa's re-read, with the same result.

**Cause.** `brahmagyan/l0_ephemeris.py:309-312` (`_compute_positions_for_date`, origin/main d674284cf): `lon = (rahu_result[0][0] + 180.0) % 360.0`, `speed = -rahu_result[0][3]  # Ketu mirrors Rahu speed` (the comment says "mirrors", the code negates), and `:326-327`: `"speed_dps": round(speed, 7)`, `"is_retrograde": speed < 0.0` (the flag follows the negated speed). Introduced in commit `e7b5758bc` (Brahma Depth Build, #211). The orchestrator writer `pipeline/orchestrator/writers/bg_ephemeris.py` computes nothing itself (it calls this function at :117 and upserts at :126-150), so it carries the defect. The same negation exists in `platform/scripts/temporal/compute_transits.py:199` (the live PATH-B of `ka_graha_sancara`, with `is_retrograde=False` forced at :200); `pipeline/transit_search.py:253-256` and `routers/ephemeris.py:50,163-167` do it correctly (same speed). No test pins Ketu's speed or flag.

**Effect (summary; the full reader table with owners is in `exec/node_series/REVIEW_TRUE_KETU_SPEED_FLAG_v1_0.md`).** SERVED now, for every chart: Ketu `speed_dps` and `is_retrograde` from `query_planet_position`, `query_planet_transit`, `ephemeris_cache_year`, `query_current_transit_snapshot`, `kala_now_get` (Ketu is in its fixed nine), `pact_query` (Ketu is a karaka for education/spirituality/moksha), `get_av_transit_gating` (free-text planet) and, if called with Ketu, `query_retrograde_periods` (start/end labels swap). STORED: Ketu kinematics in `kala_field_kinematics` (the Hermite tangent is the stored speed: canonical chart 482012f1 has 5,503 Ketu rows with mean |velocity| 0.18-0.23 dps against 0.12-0.13 for Rahu) and the Ketu `station_band` primitives built on them (5,020 on the canonical chart); the Ketu `intensity_qualifier = 'retrograde_malefic'` stamp in `kala_vedha_gochara` when Ketu is the obstructor. Not affected: L1 and L2 (they read PyJHora `chart_facts`, `KET_MEAN`), `bg_gochara_arcs`, `ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_graha_sancara` (its flag is masked to False for the nodes and its speed is unconsumed).

**Consequence for the MEAN series (design v1.2).** The MEAN Ketu rows must NOT copy it: MEAN Ketu `speed_dps` = Rahu's and `is_retrograde` = Rahu's (TRUE on every mean row). The v1.0/v1.1 design text "speed = −Rahu speed, same as the TRUE rows" is withdrawn. A golden test asserts per-date equality; the step-2 acceptance counts the dates where mean Ketu differs from Rahu (expected 0).

**Disposition.** Owner: Suvarṇa/L0. Correct the TRUE Ketu rows (computed data; a wrong fact must not stay served), with the writer fixed first so no rebuild re-introduces it; timing, route and cost are in the REVIEW. Disclose meanwhile: "stored TRUE Ketu `speed_dps` and `is_retrograde` are inverted (F-L0-08); use Rahu's, which are correct". Pravāha's step 3 already reads Ketu's retrograde days from Rahu's rows of the same series, so the correction is not urgent for them.
