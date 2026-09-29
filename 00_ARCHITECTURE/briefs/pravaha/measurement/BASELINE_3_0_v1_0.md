---
artifact: BASELINE_3_0
canonical_id: BASELINE_3_0
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra)"
protocol: "measurement/EVALUATION_PROTOCOL_v1_0.md (PRE_DECLARED 2026-09-29); this is the B4.3 scoring pass for generation '3.0'"
chart: "482012f1-710e-4a25-994a-93821f5871aa"
access: "amjis (production), read-only SELECTs via the session MCP postgres tool; all queries run 2026-09-29; no writes, no pravaha CLI"
---

# Baseline '3.0' — held-out scoring of the served Gochara windows

One scoring pass, per protocol §5.1: served windows (`kala_gochara_windows`, generation `'3.0'`)
mapped to LEL classes; ranks, base rates, timing, false-positive burden per protocol §3.
Development events reported separately (§5) and never enter a median.

## §1 — Method, class mapping, predicates

### §1.1 What '3.0' actually serves (structure discovered, then measured)

Row inventory (`select event_class, resolution, count(*) ... group by 1,2`):

- **914 rows, 27 classes** for this chart (expected ~914 — confirmed).
- Three physical shapes coexist:
  1. **Era-only classes (13):** 10 rows each, `resolution IS NULL`, non-zero-width, ten ~10-year
     era windows spanning 1984-02-05 → 2084-01-31: `achievement_recognition, bereavement,
     birth_anchor, career_advancement, career_entry, childbirth, exam_outcome, illness_acute,
     marriage, property_acquisition, romantic_start, surgery, travel_event`.
  2. **Instant-only classes (5):** `resolution IS NULL` but **zero-width** (`window_start =
     window_end = peak_date`) candidate instants only — `business_launch` (30), `career_change`
     (30), `education_milestone` (40), `foreign_settlement` (30), `separation` (30). These
     classes serve **no interval windows at all**; the task brief's assumption that null
     resolution means "era-only" holds only for shape 1. This is the single most consequential
     structural finding of the baseline.
  3. **Three-tier classes (9):** 10 `era` + 30 `month` + 30 `day` rows — `career_setback,
     chronic_onset, financial_deception, major_gain, major_loss, parental_event,
     psychological_arc, relocation, spiritual_turn` (`psychological_arc`: 27 month/day rows).
     The `day` rows are also zero-width instants; only `era` and `month` rows are true intervals.

Formula verification (protocol E4 re-check):

```sql
select term_breakdown->>'formula' formula, count(*) from kala_gochara_windows
where chart_id='482012f1-…' and generation='3.0' and term_breakdown is not null group by 1;
-- "PROMISE × PERMISSION × activity × quality_gates" | 380
select count(*) filter (where suppression_state ? 'tara'), count(*)
from kala_gochara_windows where chart_id='482012f1-…' and generation='3.0';
-- 0 | 914
```

Confirmed: formula is `PROMISE × PERMISSION × activity × quality_gates` (380 rows carry
`term_breakdown`), no tārā term on any of the 914 rows. Matches the known expectation.

Date convention: all window boundaries are `::date`-cast in the DB session timezone
(timestamps are stored at 18:30 UTC = 00:00 IST next day); event dates are plain dates. All
comparisons below use the same cast on both sides, so comparisons are internally consistent.

### §1.2 LEL → engine class mapping (declared, used exactly)

| LEL class | engine `event_class` | held-out events (grain) |
|---|---|---|
| relationship_begin | `romantic_start` | 1998-02-16 (exact), 2004-01, 2012-10 (month) |
| separation + relationship_end | `separation` | 2026-04-17 (exact); 2022-10 (month) — non-marital end mapped to separation, disclosed |
| marriage | `marriage` | dev only (§5) |
| childbirth | `childbirth` | dev only (§5) |
| bereavement | `bereavement` | 2009-06 grandfather (month); father 2018-11-28 is dev (§5) |
| family_illness_onset | `parental_event` | 2013 (year-exact → year-grain only) |
| career_join | `career_entry` | 2007-06-10 (exact), 2013-05 (month) |
| career_exit / career_switch | `career_change` | 2008-06-09 (exact), 2017-03 (month) |
| career_setback | `career_setback` | 2016 (year-exact → year-grain) |
| business_launch | `business_launch` | 2023-07 (month), 2024-02-16, 2026-03-20, 2026-04-08 (exact) |
| education_admission/completion/selection | `education_milestone` | 2011-01, 2007-06, 2013-03, 2023-06 (month); 2004, 2021 (year-grain) |
| relocation_out | `foreign_settlement` | 2019-05 (month) |
| relocation_return | `relocation` | 2023-05 (month) |
| travel | `travel_event` | 2010-12 (month) |
| surgery | `surgery` | 2007-06 (month) |
| health_event | `illness_acute` | 2021-01 (month) |
| health_onset | `chronic_onset` | 1995, 2007 (year-grain) |
| financial_gain / financial_gain_family | `major_gain` | 2025-07 (month); 2010 (year-grain) |
| quarry acquisition | `property_acquisition` | 2021 (year-grain) |
| financial_deception | `financial_deception` | 2025-05 (month) |
| recognition_creative | `achievement_recognition` | 2012-09 (month) |
| spiritual_shift | `spiritual_turn` | 2025 (year-grain) |
| wellbeing_shift | `psychological_arc` | 2026-01 (month-approx → year-grain) |

**Excluded with honest note:** `health_resolution` (sleep-disorder resolution, 2025 year-approx)
— no engine class exists for it; not scored. Engine classes with no LEL events
(`birth_anchor, career_advancement, exam_outcome, major_loss`) enter base-rate/FP tables only.
36 held-out events scored (+3 dev in §5).

### §1.3 Scoring predicate (metric 1 + 3, one query)

Resolution tier per event: `month` if the class has month rows overlapping the event year, else
`era` (incl. null-resolution true windows), else `instant`. Candidate windows = rows of that tier
overlapping the event year, ranked by `signed_intensity` desc (ties: earliest `window_start`).
Percentile = `100·(hit_rank−1)/N` (0 = top). A hit requires the window to contain the event date
(exact), overlap the event month (month-exact), or — year-grain only — any window in the year
(proxy mid-year, disclosed; for instant tier, an instant inside the year). Timing error =
`|peak_date − event_date|` of the highest-ranked containing window; no containing window ⇒ miss
(error ∞, shown separately, never dropped).

```sql
with ev(class,eid,d,grain) as (values
 ('romantic_start','EVT.1998.02.16.01',date '1998-02-16','exact'),
 ('romantic_start','EVT.2004.01.XX.01',date '2004-01-01','month'),
 ('romantic_start','EVT.2012.10.XX.01',date '2012-10-01','month'),
 ('separation','EVT.CURRENT.01',date '2026-04-17','exact'),
 ('separation','EVT.2022.10.XX.01',date '2022-10-01','month'),
 ('bereavement','EVT.2009.06.XX.01',date '2009-06-01','month'),
 ('parental_event','EVT.2013.XX.XX.01',date '2013-07-01','year'),
 ('career_entry','EVT.2007.06.10.01',date '2007-06-10','exact'),
 ('career_entry','EVT.2013.05.XX.01',date '2013-05-01','month'),
 ('career_change','EVT.2008.06.09.01',date '2008-06-09','exact'),
 ('career_change','EVT.2017.03.XX.01',date '2017-03-01','month'),
 ('career_setback','EVT.2016.XX.XX.01',date '2016-07-01','year'),
 ('business_launch','EVT.2023.07.XX.01',date '2023-07-01','month'),
 ('business_launch','EVT.2024.02.16.01',date '2024-02-16','exact'),
 ('business_launch','EVT.2026.03.20.01',date '2026-03-20','exact'),
 ('business_launch','EVT.2026.04.08.01',date '2026-04-08','exact'),
 ('education_milestone','EVT.2011.01.XX.01',date '2011-01-01','month'),
 ('education_milestone','EVT.2007.06.XX.02',date '2007-06-01','month'),
 ('education_milestone','EVT.2013.03.XX.01',date '2013-03-01','month'),
 ('education_milestone','EVT.2023.06.XX.01',date '2023-06-01','month'),
 ('education_milestone','EVT.2004.XX.XX.02',date '2004-07-01','year'),
 ('education_milestone','EVT.2021.XX.XX.02',date '2021-07-01','year'),
 ('foreign_settlement','EVT.2019.05.XX.01',date '2019-05-01','month'),
 ('relocation','EVT.2023.05.XX.01',date '2023-05-01','month'),
 ('travel_event','EVT.2010.12.XX.01',date '2010-12-01','month'),
 ('surgery','EVT.2007.06.XX.01',date '2007-06-01','month'),
 ('illness_acute','EVT.2021.01.XX.01',date '2021-01-01','month'),
 ('chronic_onset','EVT.1995.XX.XX.01',date '1995-07-01','year'),
 ('chronic_onset','EVT.2007.XX.XX.03',date '2007-07-01','year'),
 ('major_gain','EVT.2025.07.XX.01',date '2025-07-01','month'),
 ('major_gain','EVT.2010.XX.XX.01',date '2010-07-01','year'),
 ('property_acquisition','EVT.2021.XX.XX.03',date '2021-07-01','year'),
 ('financial_deception','EVT.2025.05.XX.01',date '2025-05-01','month'),
 ('achievement_recognition','EVT.2012.09.XX.01',date '2012-09-01','month'),
 ('spiritual_turn','EVT.2025.XX.XX.01',date '2025-07-01','year'),
 ('psychological_arc','EVT.2026.01.XX.01',date '2026-07-01','year')
), w as (
 select event_class class, resolution, window_start::date ws, window_end::date we,
        peak_date::date pd, signed_intensity::float si
 from kala_gochara_windows
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0'
), tier as (
 select e.*, case
   when exists (select 1 from w where w.class=e.class and w.resolution='month'
                and w.ws <= make_date(extract(year from e.d)::int,12,31)
                and w.we >= make_date(extract(year from e.d)::int,1,1)) then 'month'
   when exists (select 1 from w where w.class=e.class and (w.resolution='era'
                or (w.resolution is null and w.we>w.ws))
                and w.ws <= make_date(extract(year from e.d)::int,12,31)
                and w.we >= make_date(extract(year from e.d)::int,1,1)) then 'era'
   else 'instant' end as tier
 from ev e
), cand as (
 select t.eid, t.class, t.d, t.grain, t.tier, w.ws, w.we, w.pd, w.si
 from tier t join w on w.class=t.class
   and ((t.tier='month' and w.resolution='month')
     or (t.tier='era' and (w.resolution='era' or (w.resolution is null and w.we>w.ws)))
     or (t.tier='instant'))
   and w.ws <= make_date(extract(year from t.d)::int,12,31)
   and w.we >= make_date(extract(year from t.d)::int,1,1)
), ranked as (
 select *, row_number() over (partition by eid order by si desc, ws) rn,
          count(*) over (partition by eid) n
 from cand
), hit as (
 select r.*, case
   when r.tier='instant' and r.grain='exact' and r.ws=r.d then true
   when r.tier='instant' and r.grain='month' and date_trunc('month',r.ws)=date_trunc('month',r.d) then true
   when r.tier='instant' and r.grain='year' and extract(year from r.ws)=extract(year from r.d) then true
   when r.tier in ('month','era') and r.grain='exact' and r.ws<=r.d and r.we>=r.d then true
   when r.tier in ('month','era') and r.grain='month'
        and r.ws <= (date_trunc('month',r.d)+interval '1 month -1 day')::date
        and r.we >= date_trunc('month',r.d)::date then true
   when r.tier in ('month','era') and r.grain='year' then true
   else false end as contains_event
 from ranked r
)
select eid, class, grain, tier, d, min(n) n_windows_in_year,
       min(rn) filter (where contains_event) hit_rn,
       round((100.0*(min(rn) filter (where contains_event)-1)/min(n))::numeric,1) percentile,
       (array_agg(pd order by case when contains_event then rn end)
          filter (where contains_event))[1] hit_peak,
       (array_agg(si order by case when contains_event then rn end)
          filter (where contains_event))[1] hit_si
from hit group by eid, class, grain, tier, d order by class, d;
```

Events absent from this query's result have **zero candidate windows in their year** (inner join
drops them) — they are the coverage misses, enumerated in §2 and §6.

## §2 — Per-event rank and timing table (all 36 held-out events)

Percentile 0 = top-ranked. `N` = candidate windows in the event year. "—" = no containing window
(miss). "∅ cand" = zero candidate windows in the event year.

| event | class | grain | tier | N | hit rank | pct | peak of hit | timing err |
|---|---|---|---|---|---|---|---|---|
| EVT.2012.09.XX.01 (modeling) | achievement_recognition | month | era | 1 | 1 | 0 | 2013-04-07 | n/a |
| EVT.2009.06.XX.01 (grandfather) | bereavement | month | era | 1 | 1 | 0 | 2005-04-27 | n/a |
| EVT.2023.07.XX.01 (Marsys founded) | business_launch | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2024.02.16.01 (sand mines) | business_launch | exact | instant | 3 | — | — | — | **miss ∞** (nearest instant 11 d) |
| EVT.2026.03.20.01 (project wrap) | business_launch | exact | — | ∅ cand | — | — | — | **miss ∞** (nearest 654 d) |
| EVT.2026.04.08.01 (quarry hearing) | business_launch | exact | — | ∅ cand | — | — | — | **miss ∞** (nearest 673 d) |
| EVT.2007.06.10.01 (Cognizant) | career_entry | exact | era | 1 | 1 | 0 | 2004-09-15 | **998 d** |
| EVT.2013.05.XX.01 (Mahindra Retail) | career_entry | month | era | 1 | 1 | 0 | 2004-09-15 | n/a |
| EVT.2008.06.09.01 (Cognizant exit) | career_change | exact | — | ∅ cand | — | — | — | **miss ∞** (nearest 1526 d) |
| EVT.2017.03.XX.01 (TechM switch) | career_change | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2016.XX.XX.01 (Retail crash) | career_setback | year | month | 1 | 1 | 0 | 2016-08-23 | n/a |
| EVT.1995.XX.XX.01 (headaches) | chronic_onset | year | era | 1 | 1 | 0 | 2003-04-08 | n/a |
| EVT.2007.XX.XX.03 (sleep disorder) | chronic_onset | year | era | 1 | 1 | 0 | 2004-09-15 | n/a |
| EVT.2011.01.XX.01 (XIMB admit) | education_milestone | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2007.06.XX.02 (B.Tech) | education_milestone | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2013.03.XX.01 (MBA grad) | education_milestone | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2023.06.XX.01 (Tepper) | education_milestone | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2004.XX.XX.02 (CMU declined) | education_milestone | year | instant | 3 | 1 | 0 | 2004-02-05 | n/a |
| EVT.2021.XX.XX.02 (Tepper select) | education_milestone | year | — | ∅ cand | — | — | — | **miss** |
| EVT.2025.05.XX.01 (scam) | financial_deception | month | era | 1 | 1 | 0 | 2030-08-14 | n/a |
| EVT.2019.05.XX.01 (US move) | foreign_settlement | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2021.01.XX.01 (panic episode) | illness_acute | month | era | 1 | 1 | 0 | 2017-05-10 | n/a |
| EVT.2025.07.XX.01 (first contract) | major_gain | month | month | 1 | — | — | — | **miss** (2025 month window is Mar 31–Apr 30, peak 2025-04-20) |
| EVT.2010.XX.XX.01 (family windfall) | major_gain | year | era | 1 | 1 | 0 | 2013-06-21 | n/a |
| EVT.2013.XX.XX.01 (father kidney) | parental_event | year | era | 1 | 1 | 0 | 2007-07-24 | n/a |
| EVT.2021.XX.XX.03 (quarry) | property_acquisition | year | era | 1 | 1 | 0 | 2021-11-03 | n/a |
| EVT.2026.01.XX.01 (focus shift) | psychological_arc | year | month | 1 | 1 | 0 | 2026-05-31 | n/a |
| EVT.2023.05.XX.01 (India return) | relocation | month | era | 1 | 1 | 0 | 2017-12-20 | n/a |
| EVT.1998.02.16.01 (R#1 start) | romantic_start | exact | era | 1 | 1 | 0 | 2000-01-03 | **686 d** |
| EVT.2004.01.XX.01 (R#2 start) | romantic_start | month | era | 2 | 2 | 50.0 | 2000-01-03 | n/a |
| EVT.2012.10.XX.01 (R#3 start) | romantic_start | month | era | 1 | 1 | 0 | 2012-01-17 | n/a |
| EVT.CURRENT.01 (separation) | separation | exact | — | ∅ cand | — | — | — | **miss ∞** (nearest 262 d) |
| EVT.2022.10.XX.01 (R#3 end) | separation | month | — | ∅ cand | — | — | — | **miss** |
| EVT.2025.XX.XX.01 (Vishnu shift) | spiritual_turn | year | era | 1 | 1 | 0 | 2028-03-04 | n/a |
| EVT.2007.06.XX.01 (knee surgery) | surgery | month | era | 1 | 1 | 0 | 2009-10-20 | n/a |
| EVT.2010.12.XX.01 (Thailand) | travel_event | month | era | 1 | 1 | 0 | 2004-02-05 | n/a |

Nearest-instant distances for exact-date misses:

```sql
with ev(class,eid,d) as (values
 ('separation','EVT.CURRENT.01',date '2026-04-17'),
 ('career_change','EVT.2008.06.09.01',date '2008-06-09'),
 ('business_launch','EVT.2024.02.16.01',date '2024-02-16'),
 ('business_launch','EVT.2026.03.20.01',date '2026-03-20'),
 ('business_launch','EVT.2026.04.08.01',date '2026-04-08'))
select e.eid, min(abs(w.window_start::date - e.d)) nearest_row_days
from ev e join kala_gochara_windows w on w.event_class=e.class
 and w.chart_id='482012f1-…' and w.generation='3.0'
group by e.eid;
-- CURRENT.01: 262 · 2008.06.09: 1526 · 2024.02.16: 11 · 2026.03.20: 654 · 2026.04.08: 673
```

Timing-error predicate for the two hits:

```sql
select abs((select peak_date::date from kala_gochara_windows
  where chart_id='482012f1-…' and generation='3.0' and event_class='romantic_start'
    and window_start::date <= date '1998-02-16' and window_end::date >= date '1998-02-16')
  - date '1998-02-16');  -- 686
-- identical shape for career_entry / 2007-06-10 → 998
```

**Reading of §2:** 22 of 36 events scored a rank; 21 of those 22 are percentile 0 — but **20 of
the 22 scored events had N = 1 candidate window in the year**, so percentile 0 is structurally
guaranteed, not earned. The one non-degenerate case (R#2, N = 2 eras overlapping 2004) landed at
percentile 50. The rank metric on '3.0' is near-uninformative; the informative metrics are
coverage (14 of 36 events have no containing window at all) and timing.

## §3 — Base rate and false-positive burden

Interval-union SQL (gaps-and-islands merge per class-year over the scored horizon
1998-01-01 → 2026-12-31; event years per the §1.2 mapping incl. dev events):

```sql
with w as (
 select event_class, window_start::date ws, window_end::date we
 from kala_gochara_windows
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa' and generation='3.0'
), ys as (select generate_series(1998,2026) y),
clip as (
 select w.event_class, ys.y, greatest(w.ws,(ys.y||'-01-01')::date) s,
        least(w.we,(ys.y||'-12-31')::date) e
 from w cross join ys
 where w.ws <= (ys.y||'-12-31')::date and w.we >= (ys.y||'-01-01')::date
), mark as (
 select event_class, y, s, e,
   max(e) over (partition by event_class,y order by s
                rows between unbounded preceding and 1 preceding) prev_max
 from clip
), isl as (
 select event_class, y, s, e,
   sum(case when prev_max is null or s > prev_max then 1 else 0 end)
     over (partition by event_class,y order by s) g
 from mark
), peryear as (
 select event_class, y, sum(e-s+1) cov
 from (select event_class,y,g,min(s) s,max(e) e from isl group by event_class,y,g) z
 group by event_class, y
), evy(class,y) as (values
 ('romantic_start',1998),('romantic_start',2004),('romantic_start',2012),
 ('separation',2022),('separation',2026),('marriage',2013),('childbirth',2022),
 ('bereavement',2009),('bereavement',2018),('parental_event',2013),
 ('career_entry',2007),('career_entry',2013),('career_change',2008),('career_change',2017),
 ('career_setback',2016),('business_launch',2023),('business_launch',2024),('business_launch',2026),
 ('education_milestone',2004),('education_milestone',2007),('education_milestone',2011),
 ('education_milestone',2013),('education_milestone',2021),('education_milestone',2023),
 ('foreign_settlement',2019),('relocation',2023),('travel_event',2010),('surgery',2007),
 ('illness_acute',2021),('chronic_onset',1995),('chronic_onset',2007),
 ('major_gain',2010),('major_gain',2025),('property_acquisition',2021),
 ('financial_deception',2025),('achievement_recognition',2012),('spiritual_turn',2025),
 ('psychological_arc',2026)
), allyears as (
 select c.event_class, ys.y, coalesce(p.cov,0) cov,
        ((ys.y||'-12-31')::date-(ys.y||'-01-01')::date+1) ydays,
   exists(select 1 from evy where evy.class=c.event_class and evy.y=ys.y) has_event
 from (select distinct event_class from w) c cross join ys
 left join peryear p on p.event_class=c.event_class and p.y=ys.y
)
select event_class,
 round((100.0*sum(cov)/sum(ydays))::numeric,2) base_rate_pct,
 round((100.0*sum(cov) filter (where not has_event)
        /sum(ydays) filter (where not has_event))::numeric,2) fp_burden_pct,
 count(*) filter (where has_event) event_years
from allyears group by event_class order by event_class;
```

| class | base rate % | FP burden % (negative years) | event years |
|---|---|---|---|
| achievement_recognition | 99.88 | 99.87 | 1 |
| bereavement | 99.88 | 99.87 | 2 |
| birth_anchor (no LEL events) | 99.88 | 99.88 | 0 |
| business_launch | 0.08 | 0.06 | 3 |
| career_advancement (no LEL events) | 99.88 | 99.88 | 0 |
| career_change | 0.08 | 0.09 | 2 |
| career_entry | 99.88 | 99.87 | 2 |
| career_setback | 99.88 | 99.87 | 1 |
| childbirth | 99.88 | 99.87 | 1 |
| chronic_onset | 99.88 | 99.87 | 1 |
| education_milestone | 0.11 | 0.11 | 6 |
| exam_outcome (no LEL events) | 99.88 | 99.88 | 0 |
| financial_deception | 99.88 | 99.87 | 1 |
| foreign_settlement | 0.08 | 0.09 | 1 |
| illness_acute | 99.88 | 99.87 | 1 |
| major_gain | 99.88 | 99.87 | 2 |
| major_loss (no LEL events) | 99.88 | 99.88 | 0 |
| marriage | 99.88 | 99.87 | 1 |
| parental_event | 99.88 | 99.87 | 1 |
| property_acquisition | 99.88 | 99.87 | 1 |
| psychological_arc | 99.88 | 99.87 | 1 |
| relocation | 99.88 | 99.87 | 1 |
| romantic_start | 99.88 | 99.91 | 3 |
| separation | 0.08 | 0.09 | 2 |
| spiritual_turn | 99.88 | 99.87 | 1 |
| surgery | 99.88 | 99.87 | 1 |
| travel_event | 99.88 | 99.87 | 1 |

Base rate and FP burden agree within rounding on every class (protocol §3.4 consistency check) —
expected, since event years are 1–6 of 29. The 0.12 % gap from 100 % on era classes is the first
~5 weeks of 1998 before the 1994-era closes on 1998-02-05… i.e. the era mosaic tiles the whole
century except a boundary sliver.

## §4 — Medians vs protocol thresholds (report only; no pass/fail for the baseline)

Protocol §4 thresholds: T-rank ≤ 25, T-time ≤ 45 d, T-FP, T-honesty. '3.0' numbers:

| metric | '3.0' value | notes |
|---|---|---|
| Median rank percentile (held-out) | **0.0** (22 scored events) | Degenerate: 20/22 scored events have N = 1 candidate in-year; percentile 0 is structural. Base rate ~99.88 % on all era classes — "a class that admits everything ranks nothing" (protocol §3.2). |
| Median timing error, exact events (7) | **∞** — 5 of 7 exact events are misses (no window contains the event). Median over the 2 hits only: **842 d** (686 d, 998 d) | Misses counted separately, never dropped, per protocol §3.3. |
| FP burden, adverse classes | bereavement 99.87 %, career_setback 99.87 %, chronic_onset 99.87 %, financial_deception 99.87 %, illness_acute 99.87 %, parental_event 99.87 %, separation 0.09 % | The separation class is the mirror-image failure: it admits ~nothing, and still misses the native's actual separation (nearest instant 262 d away). |
| Base rate, gain classes | major_gain 99.88 %, business_launch 0.08 %, achievement_recognition 99.88 % | Both failure modes present. |
| Coverage | 22/36 events have a containing window; **14/36 (39 %) are coverage misses**; 13/36 have zero candidate windows in their year | Classes `business_launch, career_change, education_milestone, foreign_settlement, separation` serve zero-width instants only. |

## §5 — Calibration view (development events — never in medians)

Same predicate, era tier (all three classes are era-only), N = 1 candidate era in the event year
for each:

| dev event | class | N | hit rank | pct | peak of hit | timing err |
|---|---|---|---|---|---|---|
| EVT.2013.12.11.01 (marriage) | marriage | 1 | 1 | 0 | 2012-01-17 | **694 d** |
| EVT.2018.11.28.01 (father's passing) | bereavement | 1 | 1 | 0 | 2023-04-08 | **1592 d** |
| EVT.2022.01.03.01 (twin daughters) | childbirth | 1 | 1 | 0 | 2015-12-06 | **2220 d** |

Query: identical to §1.3 with `ev` restricted to the three dev events and the containing-window
test `ws <= d and we >= d`; timing errors from `abs(peak_date::date − d)` on the containing era.

The three events the '3.0' doctrine was developed on sit inside containing eras (base rate
~99.9 % makes that near-certain), with peaks 1.9 / 4.4 / 6.1 years from the event dates.

## §6 — Diagnostics

### §6.1 Valence sanity (E5 re-check)

E5 records that all 1,435 era rows of generation **'4.0'** read `favourable`. For **'3.0'**:

```sql
select valence, count(*) from kala_gochara_windows
where chart_id='482012f1-…' and generation='3.0' group by 1 order by 1;
-- gain 270 · loss 330 · mixed 134 · neutral 180
select resolution, valence, count(*) ... group by 1,2;
-- null: gain 130, loss 50, neutral 110 · day: gain 60, loss 120, mixed 57, neutral 30
-- era:  gain 20,  loss 40, mixed 20, neutral 10 · month: gain 60, loss 120, mixed 57, neutral 30
```

Verified and quoted: **'3.0' has no `favourable` valence values at all** — its vocabulary is
{gain, loss, mixed, neutral}, and adverse-marked rows (`is_adverse = true`) are exactly the
`loss` rows. E5's all-favourable observation is specific to '4.0' and does **not** carry over to
the '3.0' baseline. Reported as found.

### §6.2 Cross-class window-set correlation

Era-tier signature check (md5 of each class's ordered era boundary list):

```sql
with era as (
 select event_class, window_start::date ws, window_end::date we
 from kala_gochara_windows
 where chart_id='482012f1-…' and generation='3.0'
   and (resolution='era' or (resolution is null and window_end>window_start))
), sig as (
 select event_class, md5(string_agg(ws||'>'||we, ',' order by ws)) s, count(*) n
 from era group by event_class
)
select s, count(*) classes_sharing_set, string_agg(event_class,', ') from sig group by s;
-- one signature, 22 classes, 10 rows each
```

**All 22 era-bearing classes share the identical 10 era windows** (1984-02-05 → 2084-01-31,
decade boundaries at Feb-05). Overlap coefficient between any two classes at era tier —
including **marriage vs bereavement = 1.000**. The era scaffolding is class-independent; only
`signed_intensity` and `peak_date` vary by class.

Month/day tier (same md5-signature method): `financial_deception` and `major_loss` share
**identical month and day window sets** (30/30 shared at both tiers, overlap coefficient 1.000);
other pairs are lower:

```sql
-- pairwise: shared window_starts / n(a), resolution in ('day','month')
-- career_setback↔financial_deception: 3/30 day (0.100), 5/30 month (0.167)
-- career_setback↔major_loss:          3/30 day (0.100), 5/30 month (0.167)
-- chronic_onset↔career_setback:       2/30 day (0.067), 5/30 month (0.167)
-- relocation↔parental_event:          6/30 day (0.200), 6/30 month (0.200)
-- financial_deception↔major_loss:    30/30 day (1.000), 30/30 month (1.000)
```

A generation that fires the same windows for `financial_deception` and `major_loss` (and one
shared era mosaic for marriage and bereavement) has learned nothing class-specific at those
tiers — reported as a diagnostic per protocol §6, not a threshold.

### §6.3 Coverage detail

Zero-width instant classes and their instants 1984–2030 (session-TZ dates):

```sql
select event_class, string_agg(window_start::date::text, ', ' order by window_start)
from kala_gochara_windows
where chart_id='482012f1-…' and generation='3.0' and resolution is null
  and window_end=window_start and window_start::date <= date '2030-12-31'
group by event_class;
```

- `business_launch`: 1984-02-05, 03-21, 06-04 … same 3 dates each decade (1994, 2004, 2014, 2024). Nothing 2025–2033.
- `career_change`: 1984-02-05, 03-06, 04-05 … same 3 dates each decade through 2024.
- `education_milestone`: 1984-02-05, 04-05, 07-04, 1986-02-04 … same 4 per decade; next after 2026-02-04 is 2034.
- `foreign_settlement`: 1984-02-05, 02-06, 1985-02-04 … same 3 per decade through 2025-02-04.
- `separation`: 1984-02-05, 08-03, 1985-07-29 … same 3 per decade; latest before 2034 is 2025-07-29.

These 5 classes cover 0.06–0.11 % of the scored horizon and miss every held-out event in their
classes except one year-grain hit (CMU-declined 2004, which contains the 2004-02-05 instant).
Per protocol T-honesty these classes are effectively `unqualified` on timing grounds (coverage
far below 50 % of the horizon); they are reported, not silently scored as zero.

## §7 — Honest limits

1. **Rank metric degeneracy on '3.0'.** With era classes admitting ~99.88 % of the horizon and
   N = 1 candidate window in nearly every event year, the primary endpoint (median rank
   percentile 0.0) carries almost no information about discrimination. The baseline's real
   content is: era classes admit everything (FP burden ~99.87 %), five classes admit almost
   nothing (base rate ~0.1 %) and still miss the events. Any '4.1'/'5.0' comparison on the
   identical event set must therefore lean on timing error, FP burden, and coverage, not only
   the rank median — flagged for B4.4/B5.4 interpretation, not a protocol change.
2. **Year-grain hits are weak evidence.** For year-exact/approx events a "hit" only requires
   some window in the calendar year; with 10-year eras this is automatic where era rows exist.
3. **Single chart, 36 held-out events (7 exact-date)** — medians, no significance claims, per
   protocol §6.
4. **Session-timezone date casts.** All boundaries were compared as `::date` in the DB session
   timezone on both sides; reproduced exactly by the printed SQL. Absolute dates quoted for
   peaks/boundaries follow the same cast.
5. **Negative years assume LEL completeness** for the major classes (protocol §6).
6. **`major_loss` placebo.** It has no LEL events, 99.88 % base rate, and an identical window
   set to `financial_deception` — the clearest single exhibit of class-indiscriminate windowing.
7. **Known-collapsed windows.** Per protocol §6 and sealed v3.0 §1, '3.0''s windows are
   known-collapsed; this baseline is the honest floor of what is served today, not a straw man.

*End of BASELINE_3_0 v1.0. One scoring pass, protocol v1.0, generation '3.0', read-only.*
