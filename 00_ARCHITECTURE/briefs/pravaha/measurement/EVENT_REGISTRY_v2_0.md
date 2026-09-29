---
artifact: EVENT_REGISTRY
canonical_id: EVENT_REGISTRY
version: "2.0"
status: PRE_DECLARED
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
supersedes: "the implicit event lists inside EVALUATION_PROTOCOL_v1_0/v1_1 (those remain as history)"
source_of_truth: "01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md (read-only; every row below cites its LEL anchor)"
observation_mask: "events after 2026-04-17 are excluded from scoring (LEL coverage closes 2026-04-17)"
reason: >
  Codex M-01 (both reviews treated as REWORK; native's B3.6 priority 6): the protocol must carry a
  row-level event registry — observation type, onset vs status, class mapping with reasons, date
  uncertainty, explicit exclusions — instead of an event list embedded in prose. This file is that
  registry. It is pre-declared before the v2.0 re-run of the '3.0' baseline; the re-run counts its
  numerators and denominators from this table and no other source.
---

# Event registry v2.0

## 0. Conventions

- **Horizon:** 1998-01-01 → 2026-04-17 (observation mask end), H = 10,334 days. Events before
  1998-01-01 are outside the scored horizon; events after 2026-04-17 are outside the mask.
- **obs_type:** `point` (dated onset), `interval` (onset known only as a date range),
  `status` (ongoing condition, not a dated onset), `period_summary` / `chronic_pattern`
  (LEL §4/§5 aggregates — never scored as events).
- **date_grain:** `exact` (YYYY-MM-DD) | `month` (YYYY-MM) | `year` (YYYY) | `interval`
  (explicit range). Timing-error semantics per grain are defined in EVALUATION_PROTOCOL_v2_0 §5.
- **class:** one of the fixed 27-class universe (protocol v2.0 §2). The `mapping_reason` column
  is mandatory; where it overturns a v1.0-era mapping it says so explicitly.
- **tier:** `dev` (calibration only — never counted in held-out metrics) | `held_out_timing`
  (grain exact/month/interval — enters T-cover, T-time, T-rank, T-FP) | `held_out_year`
  (grain year — enters T-cover and T-FP only, never T-time/T-rank numerators) | `excluded`.

## 1. Dev tier (calibration only; never a held-out numerator or denominator)

| event_id | LEL | obs_type | date | grain | class | mapping_reason |
|---|---|---|---|---|---|---|
| EVT.2013.12.11.01 | LEL:886 | point | 2013-12-11 | exact | marriage | direct; used to calibrate window shapes pre-`3.0` |
| EVT.2018.11.28.01 | LEL:983 | point | 2018-11-28 | exact | bereavement | direct (father); dev per original partition |
| EVT.2022.01.03.01 | LEL:1134 | point | 2022-01-03 | exact | childbirth | direct (twins); dev per original partition |

## 2. Held-out — timing-usable (M = 27)

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
| 9 | EVT.2009.06.XX.01 | LEL:548 | interval | [2009-06-01, 2009-07-31] | interval | bereavement | grandfather, "June or July 2009" — interval semantics (protocol §5.4) |
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
| 20 | EVT.2022.10.XX.01 | LEL:1194 | point | 2022-10 | month | separation | R#3 end. **Disclosure:** month estimated from duration; grain kept `month` and flagged `estimated` |
| 21 | EVT.2023.05.XX.01 | LEL:1226 | point | 2023-05 | month | relocation | US→India return (dual-tagged per LEL v1.6; scored under relocation) |
| 22 | EVT.2023.06.XX.01 | LEL:1257 | point | 2023-06 | month | education_milestone | Tepper MBA completion |
| 23 | EVT.2023.07.XX.01 | LEL:1288 | point | 2023-07 | month | business_launch | Marsys founded |
| 24 | EVT.2024.02.16.01 | LEL:1319 | point | 2024-02-16 | exact | business_launch | sand-mine launch |
| 25 | EVT.2025.05.XX.01 | LEL:1350 | point | 2025-05 | month | financial_deception | direct |
| 26 | EVT.2025.07.XX.01 | LEL:1381 | point | 2025-07 | month | major_gain | first Marsys contract |
| 27 | EVT.2026.03.20.01 | LEL:1500 | point | 2026-03-20 | exact | major_gain | **remapped** from v1.0's business_launch: LEL describes project closure with "enormous profits" — mixed valence but the dated point is a realised gain (disclosed judgment call, Codex M-01 fix #2) |

**Exact-date cohort (T-time primary set), n = 5:** rows 1, 7, 8, 24, 27.

## 3. Held-out — year-grain (19 rows; T-cover and T-FP only)

| # | event_id | LEL | obs_type | date | grain | class | mapping_reason |
|---|---|---|---|---|---|---|---|
| 28 | EVT.1998.XX.XX.02 | LEL:1650 | point | 1998 | year | spiritual_turn | SPR.A |
| 29 | EVT.2000.XX.XX.01 | LEL:243 | point | 2000 | year | education_milestone | Aptech course — structured education onset |
| 30 | EVT.2002.XX.XX.01 | LEL:1679 | point | 2002 | year | chronic_onset | vertigo onset (PSY.A) |
| 31 | EVT.2002.XX.XX.02 | LEL:1708 | point | 2002 | year | spiritual_turn | SPR.B (Shani) |
| 32 | EVT.2004.XX.XX.02 | LEL:367 | point | 2004 | year | education_milestone | CMU offer received (declined — the *event* is the offer) |
| 33 | EVT.2007.XX.XX.03 | LEL:427 | point | 2007 | year | chronic_onset | sleep-disorder onset (year-approx per LEL:429) |
| 34 | EVT.2010.XX.XX.01 | LEL:581 | point | 2010 | year | major_gain | windfall |
| 35 | EVT.2010.XX.XX.02 | LEL:1737 | point | 2010 | year | spiritual_turn | SPR.C (Ugratara) |
| 36 | EVT.2012.XX.XX.02 | LEL:735 | point | 2012 | year | achievement_recognition | IRC recognition |
| 37 | EVT.2013.XX.XX.01 | LEL:855 | point | 2013 | year | parental_event | father's kidney illness onset |
| 38 | EVT.2016.XX.XX.01 | LEL:919 | point | 2016 | year | career_setback | Mahindra Retail crash |
| 39 | EVT.2021.XX.XX.02 | LEL:1076 | point | 2021 | year | education_milestone | Tepper selection — v1.0 mapping retained, reason: the dated point is an educational award; sponsorship is the mechanism, not the class |
| 40 | EVT.2021.XX.XX.03 | LEL:1105 | point | 2021 | year | property_acquisition | quarry — **v1.0's business_launch rejected**: no operations began; the dated point is acquisition of an asset (Codex M-01) |
| 41 | EVT.2022.XX.XX.02 | LEL:1165 | point | 2022 | year | romantic_start | affair onset (consequence CURRENT.01 kept separate) |
| 42 | EVT.2024.XX.XX.01 | LEL:1795 | point | 2024 | year | spiritual_turn | SPR.E |
| 43 | EVT.2025.06.XX.01 | LEL:1824 | point | 2025 | year | spiritual_turn | SPR.F |
| 44 | EVT.2025.11.XX.01 | LEL:1854 | point | 2025 | year | spiritual_turn | SPR.G |
| 45 | EVT.2025.XX.XX.01 | LEL:1441 | point | 2025 | year | spiritual_turn | Vishnu/Venkateshwara shift |
| 46 | EVT.2026.01.XX.01 | LEL:1472 | point | 2026 | year | psychological_arc | direct |

**Held-out total: 46** (27 timing-usable + 19 year-grain). Matches LEL:22 (57 logged − 3 dev −
7 excluded − 1 status; see §4).

## 4. Excluded, with reasons (Codex M-01: exclusions must be explicit)

| event_id | LEL | reason |
|---|---|---|
| EVT.1984.02.05.01 | LEL:146 | the birth itself — not a life event for scoring |
| EVT.1993.XX.XX.01 | LEL:1592 | pre-horizon (< 1998-01-01) |
| EVT.1995.XX.XX.01 | LEL:179 | pre-horizon (headache onset; pattern lives in §4) |
| EVT.1995.XX.XX.02 | LEL:1621 | pre-horizon (stammer, PSY.B) |
| EVT.2025.XX.XX.02 | LEL:1412 | sleep-disorder resolution — no engine class (no adverse/gain class maps a *resolution*); recorded, unscored |
| EVT.2026.04.08.01 | LEL:1529 | public-hearing clearance — regulatory waypoint, no engine class; quarry operation expected ~late Oct 2026, post-mask |
| EVT.CURRENT.01 | LEL:1558 | **status, not onset** — ongoing marital separation as of 2026-04-17. Removed as a *dated* separation event (Codex M-01); retained only as a status annotation |

LEL period summaries (§4) and chronic patterns (§5) are not events and are never registry rows.

## 5. Adverse-class census (drives T-FP per-class budgets, protocol v2.0 §6)

Frozen adverse classes: bereavement, career_setback, chronic_onset, financial_deception,
illness_acute, parental_event, separation, surgery, major_loss.

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
| major_loss | 0 | **single-event allowance rule:** a class with n_c = 0 held-out events is budgeted as if n_c = 1 → 2.61 % (a generation may not blanket-claim a class the registry cannot falsify) | 2.61 % |

Derivation stated (steward item 3): each adverse event can, at worst, legitimately occupy a
±45-day window (the T-time tolerance) around itself — 3·n_c·90 days is a factor-3 slack over
that legitimate footprint, normalised by the in-horizon class day-count denominator H. The bar
is derived from event density, not from '3.0''s degenerate 99.87 % figure.

## 6. Counts the re-run must reproduce

- Held-out: 46. Timing-usable: 27 (T-rank floor = floor(27/2)+1 = **14** of 27).
- Exact-date cohort: 5. Interval-date: 1 (grandfather). Month-grain: 21. Year-grain: 19.
- Any scorer whose registry-derived counts differ from this table has a bug; the table is
  authoritative and was built directly from LEL v1.2 line anchors.
