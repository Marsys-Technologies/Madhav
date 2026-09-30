---
artifact: EVENT_REGISTRY
canonical_id: EVENT_REGISTRY
version: "2.3"
status: ACCEPTED — per D-PROTO_DECISION_v1_0 (ACCEPT_WITH_CONDITIONS); steward condition verification passed 2026-09-30 (B4.6)
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "EVENT_REGISTRY_v2_2.md (sha256 1a7a627e…; kept as history — a decided file is never edited; the v2.2 re-run stands as its own record)"
machine_readable: "measurement/event_registry_v2_3.json — the scorer's actual input (R2-M06); this MD is the review copy of the same rows. A count or content mismatch between the two triggers the source-reconciliation invariant (protocol v2.3 §9.2), never an automatic verdict against either side"
source_of_truth: "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md (read-only; every row cites its LEL anchor; per-row verification state carried in the JSON)"
observation_mask: "events after 2026-04-17 are excluded from scoring (LEL coverage closes 2026-04-17)"
reason: >
  v2.3 (D-PROTO_DECISION_v1_0 §6 condition 5 — riding corrections only; no row, grain, tier,
  span or count changes): three mapping_reasons gain one disclosed clause each (F10:
  EVT.2012.XX.XX.02, EVT.2010.XX.XX.01, EVT.2022.10.XX.01) and the 2007–08 interval length is
  stated as 731 d (2008 is a leap year; the scorer and materialised controls already used 731).
  v2.2 reason, retained: Round-3 rework (Codex R2-M01 residuals, D-PROTO amendment 1): the two expressly identified
  multi-year uncertainties are no longer flattened — EVT.2007.XX.XX.03 (sleep-disorder onset,
  LEL:429/435 "2007 or 2008") and EVT.2021.XX.XX.03 (quarry, LEL:1106 "2021 or 2022") become
  grain-interval rows over their 2-year spans and move from year-grain to timing-usable
  (M = 32, T-rank floor floor(32/2)+1 = 17; year-grain 15). Vertigo's exam-prep peak becomes a
  separate UNSCORED exacerbation annotation (obs_type=exacerbation) distinct from the onset
  row. Per-row verification state added (R2-M06). The v2.1 §6 "table is infallible" rule is
  replaced by the source-reconciliation invariant. Pre-declared before the v2.2 re-run of the
  '3.0' baseline; the re-run counts from the JSON and no other source.
---

# Event registry v2.2

## 0. Conventions

- **Horizon:** 1998-01-01 → 2026-04-17 (observation mask end), H = 10,334 days.
- **obs_type:** `point` (dated onset), `interval` (onset known only as a date range),
  `status` (ongoing condition, not a dated onset), `exacerbation` (peak/worsening of an
  existing condition — annotation, **never scored**; onset ≠ exacerbation), `period_summary` /
  `chronic_pattern` (LEL §4/§5 aggregates — never registry rows).
- **date_grain:** `exact` | `month` | `year` | `interval` (explicit range). Timing-error
  semantics per grain are defined in EVALUATION_PROTOCOL_v2_2 §5.
- **class:** one of the fixed 27-class universe (protocol v2.2 §2, full table). The
  `mapping_reason` column is mandatory; where it overturns an earlier mapping it says so.
- **tier:** `dev` | `held_out_timing` (grain exact/month/interval) | `held_out_year` (grain
  year) | `excluded` | `annotation` (never scored).
- **verification:** every row carries `lel_anchor_verified` in the JSON (R2-M06); rows are
  built only from LEL v1.2 line anchors read by Stream B.

## 1. Dev tier (calibration only; never a held-out numerator or denominator)

| event_id | LEL | obs_type | date | grain | class | mapping_reason |
|---|---|---|---|---|---|---|
| EVT.2013.12.11.01 | LEL:886 | point | 2013-12-11 | exact | marriage | direct; calibration pre-`3.0` |
| EVT.2018.11.28.01 | LEL:983 | point | 2018-11-28 | exact | bereavement | direct (father); dev per original partition |
| EVT.2022.01.03.01 | LEL:1134 | point | 2022-01-03 | exact | childbirth | direct (twins); dev per original partition |

## 2. Held-out — timing-usable (M = 32)

| # | event_id | LEL | obs_type | date | grain | class | mapping_reason |
|---|---|---|---|---|---|---|---|
| 1 | EVT.1998.02.16.01 | LEL:212 | point | 1998-02-16 | exact | romantic_start | direct (R#1) |
| 2 | EVT.2001.03.XX.01 | LEL:271 | point | 2001-03 | month | education_milestone | IIT prep began — structured education onset |
| 3 | EVT.2003.06.XX.01 | LEL:301 | point | 2003-06 | month | education_milestone | SRM admission |
| 4 | EVT.2004.01.XX.01 | LEL:334 | point | 2004-01 | month | romantic_start | direct (R#2) |
| 5 | EVT.2007.06.XX.01 | LEL:396 | point | 2007-06 | month | surgery | knee arthroscopy |
| 6 | EVT.2007.06.XX.02 | LEL:456 | point | 2007-06 | month | education_milestone | BTech completion |
| 7 | EVT.2007.06.10.01 | LEL:487 | point | 2007-06-10 | exact | career_entry | Cognizant join |
| 8 | EVT.2008.06.09.01 | LEL:517 | point | 2008-06-09 | exact | career_change | Cognizant exit, exactly 1y after entry |
| 9 | EVT.2009.06.XX.01 | LEL:548 | interval | [2009-06-01, 2009-07-31] | interval | bereavement | grandfather, "June or July 2009" — interval semantics (protocol §5) |
| 10 | EVT.2010.12.XX.01 | LEL:612 | point | 2010-12 | month | travel_event | direct |
| 11 | EVT.2011.01.XX.01 | LEL:643 | point | 2011-01 | month | education_milestone | XIMB admission (distinct from enrolment per LEL:670) |
| 12 | EVT.2011.06.XX.01 | LEL:674 | point | 2011-06 | month | education_milestone | XIMB enrolment — **restored** (v1.0 scoring omitted it; Codex M-01/M-02) |
| 13 | EVT.2012.09.XX.01 | LEL:705 | point | 2012-09 | month | achievement_recognition | modelling recognition |
| 14 | EVT.2012.10.XX.01 | LEL:763 | point | 2012-10 | month | romantic_start | direct (R#3) |
| 15 | EVT.2013.03.XX.01 | LEL:793 | point | 2013-03 | month | education_milestone | XIMB graduation |
| 16 | EVT.2013.05.XX.01 | LEL:824 | point | 2013-05 | month | career_entry | Mahindra Retail |
| 17 | EVT.2017.03.XX.01 | LEL:950 | point | 2017-03 | month | career_change | Tech Mahindra transition |
| 18 | EVT.2019.05.XX.01 | LEL:1014 | point | 2019-05 | month | foreign_settlement | US move (dual-tagged travel per LEL v1.6; scored under foreign_settlement) |
| 19 | EVT.2021.01.XX.01 | LEL:1045 | point | 2021-01 | month | illness_acute | panic episode |
| 20 | EVT.2022.10.XX.01 | LEL:1194 | point | 2022-10 | month | separation | R#3 end — a concurrent-relationship end mapped to the adverse class `separation`; the class name reads as marital but the mapping of any significant relationship end to this class is deliberate and disclosed (D-PROTO F10). **Disclosure:** month estimated from duration; grain kept `month` and flagged `estimated` |
| 21 | EVT.2023.05.XX.01 | LEL:1226 | point | 2023-05 | month | relocation | US→India return (dual-tagged per LEL v1.6; scored under relocation) |
| 22 | EVT.2023.06.XX.01 | LEL:1257 | point | 2023-06 | month | education_milestone | Tepper MBA completion |
| 23 | EVT.2023.07.XX.01 | LEL:1288 | point | 2023-07 | month | business_launch | Marsys founded |
| 24 | EVT.2024.02.16.01 | LEL:1319 | point | 2024-02-16 | exact | business_launch | sand-mine launch |
| 25 | EVT.2025.05.XX.01 | LEL:1350 | point | 2025-05 | month | financial_deception | direct |
| 26 | EVT.2025.06.XX.01 | LEL:1824 | point | 2025-06 | month | spiritual_turn | SPR.F — regrained from v2.0's `year`: LEL:1824 is month-approx (June 2025) |
| 27 | EVT.2025.07.XX.01 | LEL:1381 | point | 2025-07 | month | major_gain | first Marsys contract |
| 28 | EVT.2025.11.XX.01 | LEL:1854 | point | 2025-11 | month | spiritual_turn | SPR.G — regrained from v2.0's `year`: LEL:1854 is month-approx (November 2025) |
| 29 | EVT.2026.01.XX.01 | LEL:1472 | interval | [2026-01-01, 2026-02-28] | interval | psychological_arc | LEL:1472 "January to February 2026" — explicit two-month interval |
| 30 | EVT.2026.03.20.01 | LEL:1500 | point | 2026-03-20 | exact | major_gain | remapped from v1.0's business_launch: the dated point is a realised gain (disclosed judgment call, Codex M-01 fix #2) |
| 31 | EVT.2007.XX.XX.03 | LEL:427 | interval | [2007-01-01, 2008-12-31] | interval | chronic_onset | **v2.2 (R2-M01):** LEL:429 "during or shortly after knee surgery; native confirmed 2007–2008" and LEL:435 "2007 or 2008" — a two-year uncertainty, no longer flattened to 2007; scored span = the 2-year interval |
| 32 | EVT.2021.XX.XX.03 | LEL:1105 | interval | [2021-01-01, 2022-12-31] | interval | property_acquisition | **v2.2 (R2-M01):** LEL:1106 "native said 2021 or 2022" — a two-year uncertainty, no longer flattened to 2021; v1.0's business_launch rejected (no operations began; the dated point is acquisition of an asset) |

**Exact-date cohort (T-time primary set), n = 5:** rows 1, 7, 8, 24, 30 (unchanged from v2.1).

## 3. Held-out — year-grain (15 rows; T-cover and T-FP only)

| # | event_id | LEL | obs_type | date | grain | class | mapping_reason |
|---|---|---|---|---|---|---|---|
| 33 | EVT.1998.XX.XX.02 | LEL:1650 | point | 1998 | year | spiritual_turn | SPR.A |
| 34 | EVT.2000.XX.XX.01 | LEL:243 | point | 2000 | year | education_milestone | Aptech course — structured education onset |
| 35 | EVT.2002.XX.XX.01 | LEL:1679 | point | 2002 | year | chronic_onset | vertigo (PSY.A) **onset** row — LEL:1683–87: onset "likely earlier (teen years)"; 2002 marks the condition entering the dated record. The exam-prep **peak** is the separate unscored exacerbation annotation (§4a) — onset ≠ exacerbation (v2.2, R2-M01) |
| 36 | EVT.2002.XX.XX.02 | LEL:1708 | point | 2002 | year | spiritual_turn | SPR.B (Shani) |
| 37 | EVT.2004.XX.XX.02 | LEL:367 | point | 2004 | year | education_milestone | CMU offer received (declined — the *event* is the offer) |
| 38 | EVT.2010.XX.XX.01 | LEL:581 | point | 2010 | year | major_gain | windfall — family-level gain (LEL:586, 608) mapped to major_gain; the native benefited directly but the event was not solely personal (D-PROTO F10) |
| 39 | EVT.2010.XX.XX.02 | LEL:1737 | point | 2010 | year | spiritual_turn | SPR.C (Ugratara) |
| 40 | EVT.2012.XX.XX.02 | LEL:735 | point | 2012 | year | achievement_recognition | IRC recognition — LEL:737 "during XIMB MBA 2011–2013; likely second year ~2012": 2012 kept (faithful to the LEL `date:` field); the residual ~1-year uncertainty is surfaced here (D-PROTO F10) |
| 41 | EVT.2013.XX.XX.01 | LEL:855 | point | 2013 | year | parental_event | father's kidney illness onset |
| 42 | EVT.2015.XX.XX.01 | LEL:1766 | point | 2015 | year | spiritual_turn | SPR.D, devata adoption — restored (omitted from v2.0; Kimi NK-1, Codex R2-M01) |
| 43 | EVT.2016.XX.XX.01 | LEL:919 | point | 2016 | year | career_setback | Mahindra Retail crash |
| 44 | EVT.2021.XX.XX.02 | LEL:1076 | point | 2021 | year | education_milestone | Tepper selection — the dated point is an educational award; sponsorship is the mechanism, not the class |
| 45 | EVT.2022.XX.XX.02 | LEL:1165 | point | 2022 | year | romantic_start | affair onset (consequence CURRENT.01 kept separate) |
| 46 | EVT.2024.XX.XX.01 | LEL:1795 | point | 2024 | year | spiritual_turn | SPR.E |
| 47 | EVT.2025.XX.XX.01 | LEL:1441 | point | 2025 | year | spiritual_turn | Vishnu/Venkateshwara shift |

**Held-out total: 47** (32 timing-usable + 15 year-grain). Header arithmetic:
**57 logged = 3 dev + 47 held-out + 7 excluded** — EVT.CURRENT.01 sits inside the 7 excluded
(as a status, not a dated event) and is not subtracted a second time. The exacerbation
annotation (§4a) is not a logged event and sits outside the 57.

## 4. Excluded, with reasons (Codex M-01: exclusions must be explicit)

| event_id | LEL | reason |
|---|---|---|
| EVT.1984.02.05.01 | LEL:146 | the birth itself — not a life event for scoring |
| EVT.1993.XX.XX.01 | LEL:1592 | pre-horizon (< 1998-01-01) |
| EVT.1995.XX.XX.01 | LEL:179 | pre-horizon (headache onset; pattern lives in §4) |
| EVT.1995.XX.XX.02 | LEL:1621 | pre-horizon (stammer, PSY.B) |
| EVT.2025.XX.XX.02 | LEL:1412 | sleep-disorder resolution — no engine class maps a *resolution*; recorded, unscored |
| EVT.2026.04.08.01 | LEL:1529 | public-hearing clearance — regulatory waypoint, no engine class; quarry operation expected ~late Oct 2026, post-mask |
| EVT.CURRENT.01 | LEL:1558 | **status, not onset** — ongoing marital separation as of 2026-04-17; retained only as a status annotation. Counted exactly once, here |

### 4a. Annotations (never scored)

| annotation | of event | LEL | span | note |
|---|---|---|---|---|
| EVT.2002.XX.XX.01.EXAC | EVT.2002.XX.XX.01 | LEL:1683–1687 | [2001-01-01, 2004-12-31] | vertigo exam-prep **peak** (debilitating bouts ~2001–2004, direct academic impact; fear persisted ~a decade) — obs_type `exacerbation`; an annotation on the onset row, never a scored event (v2.2, R2-M01) |

LEL period summaries (§4) and chronic patterns (§5) are not events and are never registry rows.

## 5. Adverse-class census (drives T-FP per-class budgets, protocol v2.2 §6)

Frozen adverse classes: bereavement, career_setback, chronic_onset, financial_deception,
illness_acute, parental_event, separation, surgery, major_loss. (spiritual_turn and
psychological_arc are not adverse classes.)

| class | n_c (held-out, in-horizon) | budget 3·n_c·90/H, H = 10,334 | capped |
|---|---|---|---|
| bereavement | 1 | 270/10,334 = 2.61 % | 2.61 % |
| career_setback | 1 | 2.61 % | 2.61 % |
| chronic_onset | 2 | 540/10,334 = 5.23 % | 5.23 % |
| financial_deception | 1 | 2.61 % | 2.61 % |
| illness_acute | 1 | 2.61 % | 2.61 % |
| parental_event | 1 | 2.61 % | 2.61 % |
| separation | 1 | 2.61 % | 2.61 % |
| surgery | 1 | 2.61 % | 2.61 % |
| major_loss | 0 | **single-event allowance rule:** budgeted as if n_c = 1 → 2.61 % (a generation may not blanket-claim a class the registry cannot falsify) | 2.61 % |

The v2.2 re-graining moves the sleep-disorder row inside `chronic_onset` from year-grain to
timing-usable — its n_c (2) is unchanged, so every budget above is unchanged from v2.1.
Policy statement (per Codex R2-M02): the factor-3 slack, the 90-day window, and the n_c = 0
allowance are **declared engineering allowances** (evaluation policy), not quantities derived
from event density.

## 6. Counts the v2.2 re-run must reproduce

- Held-out: 47. Timing-usable: **32** (T-rank floor = floor(32/2)+1 = **17** of 32).
- Exact-date cohort: 5. Interval-date: **4** (grandfather 61 d; 2026.01 interval 59 d;
  2007–08 sleep disorder **731 d** (2008 is a leap year); 2021–22 quarry 730 d). Month-grain: 23. Year-grain: **15**.
- **Source-reconciliation invariant (replaces v2.1's "table is infallible"):** if a scorer's
  registry-derived counts differ from this table, that triggers a documented
  registry-vs-scorer diff reconciliation — each differing count is traced to its registry row
  and its scorer predicate, the side in error is fixed with the diff recorded, and neither
  side is presumed correct by rule (Codex R2-M01).
