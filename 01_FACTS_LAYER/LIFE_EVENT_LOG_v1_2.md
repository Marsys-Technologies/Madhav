---
document: LIFE EVENT LOG — ABHISEK MOHANTY
project: MARSYS-JIS (Abhisek Mohanty Jyotish Intelligence System)
layer: L1 (Facts Layer)
artifact_id: LIFE_EVENT_LOG_v1_2
version: 1.6
canonical_id: LEL
status: CLOSED (Session 4 — chart_state fields populated from Swiss Ephemeris tooling; see `.tools/` scripts. v1.4: 11 v1.3 pending_computation events advanced to computed state via M4-A-T1-SWISS-EPHEMERIS pass. v1.5: §9 PPL migration annotations added. v1.6: GAP.M4A.04 partial close — EVT.2019.05.XX.01 + EVT.2023.05.XX.01 dual-tagged residential+travel per NAP.M4.2 native disposition.)
supersedes: v1.1 (same-corpus, chart-state-populated)
author: Claude (Session 2, Claude Code instance)
date_built: 2026-04-17
date_range_covered: 1984-02-05 to 2026-04-17
source_of_events: Native's "Consolidated Life Facts.docx" (extracted 2026-04-17) + Session 2 elicitation (all 19 gap-fill questions answered by native)
chart_state_sources:
  vimshottari: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 (lineage from prior v6 §5.1 where event blocks cite DSH.V.*)
  yogini: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.2
  chara: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.3
  sade_sati: SADE_SATI_CYCLES_ALL.md + FORENSIC_ASTROLOGICAL_DATA_v8_0.md §21
  transits_eclipses_retrograde_ashtakavarga: Swiss Ephemeris self-compute (Session 4) — per-event blocks in this file + EVENT_CHART_STATES_v1_0.md; optional JH cross-check via EXTERNAL_COMPUTATION_SPEC
retrodictive_signal_source: DEEP_ANALYSIS_Abhisek_Mohanty_v1 (v1.2.1) §D.0.F (SIG.01-15, CVG.01-08, CTR.01-07)
total_events_logged: 46 (35 original + 11 added v1.3; v1.4 advanced all 11 pending events to computed state via Swiss Ephemeris) + 5 period summaries + 6 chronic patterns
confidence_self_assessment: 0.89 (v1.2 populates transits, eclipses, retrograde, Ashtakavarga via Swiss Ephemeris pipelines. Native JH spot-check remains optional.)
next_steps:
  - Optional v1.3: Promote eclipse/transit evidence from chart_state into each event's signals_that_matched lists (SESSION_LOG red-team note)
  - Future: Expand toward 75-100 events; drain §6 gap register
  - Future (v2.0): Pattern Library (RPT.LFE.01) when Deep Analysis v2.0 exists
changelog:
  - v1.6 (2026-05-02, M4-A-CLOSE-LEL-PATCH): GAP.M4A.04 partial close —
    EVT.2019.05.XX.01 (US move, May 2019) and EVT.2023.05.XX.01 (India return,
    May 2023) dual-tagged `residential+travel` per NAP.M4.2 native disposition
    (LEL_GAP_AUDIT_v1_0.md §5.4). Subcategory notes added on both events
    cross-referencing GAP.M4A.04. Total events unchanged: 46 (no new EVT
    entries; both target events already existed in the corpus). chart_state
    blocks unchanged (already populated by v1.4 Swiss Ephemeris pass).
  - v1.5 (2026-05-02, M4-A-INTEGRATION-PASS): §9 PPL migration annotations added. Both
    PRED.M3D.HOLDOUT.001 and PRED.M3D.HOLDOUT.002 annotated with migrated: true,
    migrated_at, migrated_by_session, migration_destination. Migration to
    prediction_ledger.jsonl was performed by M4-A-T2-PPL-INFRA (commit f7f477e).
  - v1.4 (2026-05-01, M4-A-T1-SWISS-EPHEMERIS): Swiss Ephemeris computation pass for 11 pending_computation events. All chart states populated (proxy dates where exact dates unavailable). M4-A AC.M4A.1 discharged.
expose_to_chat: true
native_id: "abhisek"
---

# LIFE EVENT LOG — Abhisek Mohanty (v1.0)

## §1 — META

### §1.1 — Purpose

This document is L1 (Facts Layer) per Architecture §C.1 and §D.2. It is the single highest-leverage asset for acharya-grade sight: the empirical calibration corpus that lets signal-patterns from the chart be validated against actual lived events. Every entry here is factual (what happened, when). No interpretation. Interpretation lives at L2+ via the `retrodictive_match` field, which points to Deep Analysis v1.2.1 signals (SIG.*/CVG.*/CTR.*) but does not generate new analysis.

### §1.2 — How to Read This Document

- **§3 is the main event log**, chronologically ordered, 36 entries (post-v1.1 corrections).
- **§4** captures chronic patterns and traits that are not dated point-events (stammering, headaches, etc.).
- **§5** captures the 5 inner-turning-point periods (2007, 2012-13, 2016, 2018-21, 2022-24) characterized by the native.
- **§6** is a gap register — things mentioned in source material but not yet dated with precision; these are Session 3+ targets.
- **§7** is an aggregate retrodictive-match summary: how many events the chart "predicts" and where the misses cluster.

### §1.3 — Event ID Format

`EVT.YYYY.MM.DD.XX` — date first (YYYY-MM-DD when known; XX placeholder where unknown), then sequence number XX for events on the same day.

### §1.4 — Schema (per Architecture §D.2)

```yaml
EVT.YYYY.MM.DD.XX:
  date: [YYYY-MM-DD | YYYY-MM-XX | YYYY-XX-XX]
  date_confidence: [exact | month-exact | year-exact | year-approx | vague]
  category: [career | education | relationship | finance | family | health |
             travel | residential | spiritual | creative | legal | loss |
             gain | psychological | other]
  subcategory: [string]
  description: [1-3 sentences, factual only]
  magnitude: [trivial | moderate | significant | major | life-altering]
  valence: [positive | mixed | negative | neutral]
  native_reflection: [optional, in native's own words or paraphrased from Consolidated Life Facts.docx]
  chart_state_at_event:
    vimshottari_md: [planet]
    vimshottari_ad: [planet]
    vimshottari_id: [DSH.V.NNN per v6.0 §5.1]
    yogini_md: [Yogini name / Ruler]
    yogini_id: [DSH.Y.NNN]
    chara_md_ad: [SignMD / SignAD]
    chara_id: [DSH.C.NNN]
    sade_sati_phase: [TRS.SS.* | null | Cycle1_approx_<range>]
    transits_of_note: [list | unexamined]
    eclipses_within_6mo: [list | unexamined]
    retrograde_activity: [list | unexamined]
    ashtakavarga_SAV_transit_sign: [bindu | unexamined]
  retrodictive_match:
    predicted_by_chart: [yes | partial | no | unexamined]
    signals_that_matched: [list of SIG.* / CVG.* / CTR.* IDs from v1.2.1 Deep Analysis]
    signals_that_missed: [list of gaps — signals that would have been expected but weren't observed, OR events not explained by any current signal]
    retrodictive_reasoning: [1-3 sentences, optional]
  notes: [free text, optional]
```

### §1.5 — Data Provenance Discipline

Every chart_state_at_event field is sourced per Architecture §B.10 (No Fabricated Computation):
- `vimshottari_md`, `vimshottari_ad`, `vimshottari_id` → from v6.0 §5.1 table (authoritative)
- `yogini_md`, `yogini_id` → from v6.0 §5.2 table (authoritative)
- `chara_md_ad`, `chara_id` → from v6.0 §5.3 table (authoritative)
- `sade_sati_phase` → from v6.0 §21 table (authoritative for Cycle 2, 2020+); Cycle 1 (~1993-2000) is not in v6.0 and is flagged for Facts Layer v7.0 completion
- `transits_of_note`, `eclipses_within_6mo`, `retrograde_activity`, `ashtakavarga_SAV_transit_sign` → **POPULATED in v1.2** via Swiss Ephemeris self-compute (see also `EVENT_CHART_STATES_v1_0.md` for full per-event detail including planetary positions, panchang, Ashtakavarga SAV across all 7 signs, full transit note list)

---

## §2 — SCOPE AND CONVENTIONS

### §2.1 — Included

- All dateable events from native's "Consolidated Life Facts.docx" (9 sections, 93 lines)
- All events surfaced in Session 2 elicitation responses (Batches 1-3)
- Events with date_confidence ranging from `exact` to `year-approx`

### §2.2 — Excluded from §3 Event Log

- Chronic traits (undated) → §4
- Period summaries (inner turning points without specific dates) → §5
- Vague references ("sometime in childhood") → §6 Gap Register

### §2.3 — Sensitivity Note (per Bootstrap §9.4)

Native granted full elicitation scope with no privacy boundaries (§J.3 of Architecture). This document contains sensitive material: loss of grandfather and father, marriage strain leading to current separation, physical infidelity (logged as relationship #2 and #3 timespans, not as behavioral events), an adolescent relationship beginning at age 14, a significant financial deception event, and an intense peak-life period characterized by partying and sexual romance. All logged factually per architecture principle B.7 (Honest-Calibration Scope).

---

## §3 — EVENT LOG (CHRONOLOGICAL)

*v1.2 note: chart_state_at_event fields now populated. For complete per-event chart details (all 9 planet positions, full panchang, full SAV matrix, exhaustive transit notes), see companion file `EVENT_CHART_STATES_v1_0.md`. This file preserves the canonical retrodictive narrative.*

### Era 1: Birth & Early Life (1984-1995)

```yaml
EVT.1984.02.05.01:
  date: 1984-02-05
  date_confidence: exact
  category: other
  subcategory: birth
  description: Born in Bhubaneswar, Odisha at 10:43 IST. Aries Lagna, Moon in Aquarius (Purva Bhadrapada Pada 3), Sun in Capricorn (Shravana Pada 4).
  magnitude: life-altering
  valence: neutral
  native_reflection: null
  chart_state_at_event:
    vimshottari_md: Jupiter
    vimshottari_ad: Venus
    vimshottari_id: DSH.V.001
    yogini_md: Bhramari / Mars
    yogini_id: DSH.Y.001
    chara_md_ad: Aries / Taurus
    chara_id: DSH.C.001
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Sagittarius = 9H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Scorpio -62d", "Lunar Penumbral Gemini -46d", "Lunar Penumbral Scorpio +100d", "Solar Annular+Central Taurus +115d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=31, Sun=32, Moon=24 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.01, SIG.04, SIG.05, SIG.07, SIG.08, SIG.09, SIG.14, SIG.15, CVG.01, CVG.02, CVG.03, CVG.04, CVG.05, CVG.06]
    signals_that_missed: []
    retrodictive_reasoning: Birth itself is the "source event" — every natal signal fires from here. Event included for anchoring; retrodictive match is tautological.
  notes: Foundational event. All downstream retrodictive tagging references this chart state.
```

### Era 2: Adolescence and Headaches (1995-2000)

```yaml
EVT.1995.XX.XX.01:
  date: 1995-XX-XX
  date_confidence: year-approx
  category: health
  subcategory: chronic_onset
  description: Severe headaches onset around 1995 (age 11). Became a defining health motif of early life; also reduced computer/screen usage because screen time catalyzed headaches.
  magnitude: significant
  valence: negative
  native_reflection: "Suffered from severe headaches since around 1995, a major part of early life. Screen time became a catalyst."
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.007
    yogini_md: Ulka / Saturn
    yogini_id: DSH.Y.003
    chara_md_ad: Taurus / Cancer (approx, depends on exact month)
    chara_id: DSH.C.022 (if May-Dec 1995)
    sade_sati_phase: Cycle1_approx_peak_Saturn_Aquarius (~1995-1998, not in v6.0 §21 — see §6 Gap Register)
    transits_of_note: ["Saturn transit Pisces = 12H from Lagna", "Jupiter transit Scorpio = 8H from Lagna"]
    eclipses_within_6mo: ["Lunar Partial Libra -60d", "Solar Annular+Central Aries -46d", "Lunar Penumbral Pisces +115d", "Solar Total+Central Libra +131d"]
    retrograde_activity: ["Mercury retro in Taurus", "Jupiter retro in Scorpio"]
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=29, Sun=29, Moon=31 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.01, SIG.11, CTR.01]
    signals_that_missed: [SIG.13 (Sade Sati Cycle 1 not in v6.0 data)]
    retrodictive_reasoning: Saturn MD active (2nd Saturn peak of life). Saturn Cycle 1 Sade Sati Peak (Saturn transiting Aquarius = natal Moon sign) plausibly ~1995-1998. Saturn + Aquarius Moon = mental weight, headaches. Mars-Saturn 7H exalted conjunction (SIG.15) aspects Aries Lagna (head) at 180°.
  notes: Cycle 1 Sade Sati (1993-2000 approx) is not tabulated in v6.0 §21 — v7.0 should add it. This gap flagged in §6.
```

### Era 3: Teen Years, Computer-Prodigy Recognition, First Relationship (1998-2003)

```yaml
EVT.1998.02.16.01:
  date: 1998-02-16
  date_confidence: exact
  category: relationship
  subcategory: romantic_long_term_started
  description: Relationship #1 started (age 14). This is the childhood girlfriend who later became native's wife (married 2013-12-11). Total duration as relationship pre-marriage was ~15 years.
  magnitude: life-altering
  valence: mixed
  native_reflection: Confirmed by native in Session 2 as "the next time I do it" (marriage). Defining long-term relationship.
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Ketu
    vimshottari_id: DSH.V.008
    yogini_md: Siddha / Venus
    yogini_id: DSH.Y.004
    chara_md_ad: Gemini / Leo
    chara_id: DSH.C.026
    sade_sati_phase: Cycle1_approx_peak_Saturn_Aquarius (~1995-1998, not in v6.0)
    transits_of_note: ["Jupiter transit on natal Moon (Aquarius) — gajakesari-class", "Ketu transit on natal Moon (Aquarius)", "Saturn transit Pisces = 12H from Lagna", "Jupiter transit Aquarius = 11H from Lagna"]
    eclipses_within_6mo: ["Solar Partial+Non-Central Leo -166d", "Lunar Total Pisces -152d", "Solar Total+Central Aquarius +10d", "Lunar Penumbral Leo +25d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=24, Sun=24, Moon=26 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.04 (Moon AK 11H/Chalit-12 = emotional attachment signature), CVG.07 (Gemini 3H nexus — UL+Vivaha Saham+A5+A11 all in Gemini), SIG.12 (Venus weak — relational friction built in)]
    signals_that_missed: [Ketu AD would not typically be a partnership-starting signal in classical reading; Venus Yogini (Siddha) gives romantic overlay but the Ketu AD underpins detachment. Pattern: early-Saturn-Ketu relationships tend to be intense but karmically bonded, not conventional — fits native's "childhood girlfriend → wife → separation" arc.]
    retrodictive_reasoning: Gemini 3H nexus CVG.07 is the strongest structural match — Vivaha Saham (marriage-specific sensitive point) + UL (Upapada — spouse karma) + A5 + A11 all clustered in Gemini suggests the spouse relationship's origin-node is Gemini-inflected. Age-14 onset + 15-year duration-to-marriage is a Saturn-MD signature (Saturn = long-gestation, delay-before-culmination).
  notes: Physical infidelity category, per native's clarification, is effectively captured by concurrent tracks R#2 (Jan 2004–Jan 2007, entirely pre-marriage; corrected in v1.1) and R#3 (Oct 2012–Oct 2022) overlapping with this R#1 track. Only R#3 overlaps with formal marriage (Dec 2013 onward).
```

```yaml
EVT.2000.XX.XX.01:
  date: 2000
  date_confidence: year-approx (post-10th board exams; native said "after 10th boards")
  category: education
  subcategory: advanced_course_partial
  description: Joined Aptech computer education course post-10th board exams (~2000, age 16). Was among the brighter students. Could not sit the certification exam — the program was postgraduate level and required a graduate minimum qualification; native was pre-graduate. Course completed; certificate denied on qualification grounds.
  magnitude: moderate
  valence: mixed
  native_reflection: "I joined that course and I was one of the brighter ones but I never could write the exam because it told me they can only teach me but cannot allow me to write exams and get a certificate because the minimum qualification was to be a graduate."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2000-06-01
    vimshottari:
      maha_dasha: Saturn (1991-08-19 to 2010-08-18)
      antar_dasha: Venus (1998-06-09 to 2001-08-09)
      pratyantar_dasha: Jupiter (2000-01-18 to 2000-06-21)
    yogini:
      maha_dasha: Siddha/Venus (1996-12-24 to 2003-12-24)
      antar_dasha: Pingala/Sun (2000-02-03 to 2000-06-24)
    key_transits:
      saturn_sign: Aries
      jupiter_sign: Aries
      rahu_sign: Cancer
      sade_sati_active: false
  retrodictive_match: pending

EVT.2001.03.XX.01:
  date: 2001-03-XX
  date_confidence: month-exact (approx)
  category: education
  subcategory: entrance_exam_preparation
  description: Began IIT preparation around March 2001 (age 17, during 12th standard). Continued intensive preparation through June 2003.
  magnitude: significant
  valence: mixed
  native_reflection: "I started my IIT preparation about March 2001 or maybe earlier, March 2000, and continued till June 2003." (March 2001 adopted as most probable start; 2000 may be conflated with 11th std year at BJP College.)
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Venus
    vimshottari_id: DSH.V.009
    yogini_md: Siddha / Venus
    yogini_id: DSH.Y.004
    chara_md_ad: Gemini / Aquarius
    chara_id: DSH.C.032
    sade_sati_phase: Cycle1_approx_setting_Saturn_Pisces → post-Sade-Sati window
    transits_of_note: ["Saturn transit Taurus = 2H from Lagna", "Jupiter transit Taurus = 2H from Lagna"]
    eclipses_within_6mo: ["Solar Partial+Non-Central Sagittarius -79d", "Lunar Total Gemini -64d", "Solar Total+Central Gemini +98d", "Lunar Partial Sagittarius +112d"]
    retrograde_activity: ["Venus retro in Pisces"]
    ashtakavarga_SAV_transit_sign: "Sat=29, Jup=29, Sun=27, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.09 (Mercury Vargottama + Yogi — native's operational spine; Mercury = studies/exams), CVG.07 (Gemini 3H nexus — 3H = effort, sibling support, courage; relevant to IIT struggle)]
    signals_that_missed: [IIT preparation outcome (whether he cracked IIT) — answered ambiguously by native; treated as "unsuccessful at IIT, successful at SRM Chennai engineering" per doc. SIG.08 Lakshmi Yoga is dharmic-wealth, less applicable to exam prep. Saturn MD = slow-burn; exam outcomes under Saturn MD tend to be delayed/tough-won.]
  notes: Per doc, "Could not secure admission in A1-tier universities initially but achieved entry into strong institutions just below that level." IIT attempt appears unsuccessful; engineering pursued at SRM Chennai instead.
```

```yaml
EVT.2003.06.XX.01:
  date: 2003-06-XX
  date_confidence: month-exact
  category: education
  subcategory: entrance_exam_preparation_ended
  description: IIT preparation phase ended (June 2003). Transitioned to engineering admission at SRM Chennai.
  magnitude: significant
  valence: mixed
  native_reflection: Implicit transition point.
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Moon
    vimshottari_id: DSH.V.011
    yogini_md: Siddha / Venus
    yogini_id: DSH.Y.004
    chara_md_ad: Gemini / Taurus
    chara_id: DSH.C.035
    sade_sati_phase: null (post-Cycle-1)
    transits_of_note: ["Saturn transit Gemini = 3H from Lagna", "Jupiter transit Cancer = 4H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Scorpio -29d", "Solar Annular+Central Taurus -14d", "Lunar Total Aries +147d", "Solar Total+Central Scorpio +161d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=28, Jup=32, Sun=29, Moon=31 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.04 (Moon AK), SIG.05 (Moon Chalit-12)]
    signals_that_missed: []
    retrodictive_reasoning: Saturn-Moon AD activates the AK Moon — major self-direction transition. Moon = 4H lord = education house; AD of 4L often triggers educational transitions. Fits.
  notes: Followed by engineering at SRM Chennai (with brother's support per doc); engineering ends c. June 2007.
```

### Era 4: SRM Engineering Era, Second Relationship, First Job (2004-2009)

```yaml
EVT.2004.01.XX.01:
  date: 2004-01-XX
  date_confidence: month-exact
  category: relationship
  subcategory: romantic_concurrent
  description: Relationship #2 started (Jan 2004, 3-year duration → ended ~Jan 2007). Started during engineering years at SRM Chennai (native was age 19-20). Concurrent with primary long-term relationship (R#1, started Feb 1998). Entirely pre-marriage.
  magnitude: significant
  valence: mixed
  native_reflection: "Jan 2004 - 3 years" (corrected in Session 2 v1.1 — original doc phrasing implied Jan 2008 which was incorrect).
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Moon (through Feb 24, 2004)
    vimshottari_id: DSH.V.011
    yogini_md: Sankata / Rahu (started Dec 22, 2003)
    yogini_id: DSH.Y.005
    chara_md_ad: Gemini / Gemini (through Feb 5, 2004)
    chara_id: DSH.C.036
    sade_sati_phase: null
    transits_of_note: ["Saturn transit Gemini = 3H from Lagna", "Jupiter transit Leo = 5H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Aries -66d", "Solar Total+Central Scorpio -52d", "Solar Partial+Non-Central Aries +95d", "Lunar Total Libra +110d"]
    retrograde_activity: ["Jupiter retro in Leo", "Saturn retro in Gemini"]
    ashtakavarga_SAV_transit_sign: "Sat=28, Jup=30, Sun=32, Moon=23 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.04 (Moon AK — AK AD activates soul-signature), SIG.05 (Moon Chalit-12 = secret/hidden-romance signature), SIG.10 (Rahu 2H = unconventional-attachment), SIG.12 (Venus weak — relational-multiplicity vs single-track stability), CVG.07 (Gemini 3H/A5 secondary-relational signifiers)]
    signals_that_missed: [Specific infidelity-structure signal not computed in v1.2.1 — belongs in v2.0 Pattern Library.]
    retrodictive_reasoning: Saturn MD with Moon AK AD just ending (Feb 24, 2004) + immediate transition to Saturn-Mars AD (fire/assertion) + Sankata/Rahu Yogini starting = complex relational-imprinting window. Moon AK AD coinciding with a non-primary romantic start suggests soul-level engagement with "the other woman" archetype at 19-20. Chara MD/AD both Gemini = triple Gemini signature (Gemini is the chart's 3H nexus per CVG.07 with UL + A5 + A11 + Vivaha Saham clustered) = romantic-relational-complexity coded at age onset.
  notes: Per native's explicit clarification in Session 2, this + R#3 effectively capture the "physical infidelity" category. R#2 entirely pre-marriage — the overlap that becomes concerning is with R#1 (the relationship that becomes the wife in 2013), not with the formal marriage.
```

### Era 4 continued

```yaml
EVT.2004.XX.XX.02:
  date: 2004
  date_confidence: year-approx (after first year at SRM Engineering College)
  category: education
  subcategory: opportunity_declined
  description: Selected by SRM Engineering College as one of 4–5 students for a 1-year exchange program at Carnegie Mellon University (CMU). Would have received a CMU certificate and returned to complete engineering at SRM. Could not accept due to health issues and financial constraints. Native experienced a "deja vu" when CMU reappeared as the Tepper School MBA sponsorship in 2021.
  magnitude: significant
  valence: mixed
  native_reflection: "I was selected for Carnegie Milan University for a one-year course there... but I could not take up that opportunity in 2004 because of my health issues and financial issues. It was a deja vu incident for me."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2004-06-01
    vimshottari:
      maha_dasha: Saturn (1991-08-19 to 2010-08-18)
      antar_dasha: Mars (2004-02-20 to 2005-03-31)
      pratyantar_dasha: Jupiter (2004-05-15 to 2004-07-08)
    yogini:
      maha_dasha: Sankata/Rahu (2003-12-24 to 2011-12-24)
      antar_dasha: Sankata/Rahu (2003-12-24 to 2005-10-04)
    key_transits:
      saturn_sign: Gemini
      jupiter_sign: Leo
      rahu_sign: Aries
      sade_sati_active: false
  retrodictive_match: pending
  notes: Deja vu resolution pair — EVT.2021.XX.XX.02 (Tepper MBA selection) + EVT.2023.06.XX.01 (CMU completion).

EVT.2007.06.XX.01:
  date: 2007-06-XX
  date_confidence: month-exact
  category: health
  subcategory: surgery_minor
  description: Right knee arthroscopy (minor surgery).
  magnitude: moderate
  valence: negative
  native_reflection: "A minor surgery, orthoscopy on the right knee in June 2007."
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Rahu
    vimshottari_id: DSH.V.013
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Cancer / Libra
    chara_id: DSH.C.045
    sade_sati_phase: null
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Cancer = 4H from Lagna", "Jupiter transit Scorpio = 8H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -103d", "Solar Partial+Non-Central Pisces -87d", "Lunar Total Aquarius +74d", "Solar Partial+Non-Central Leo +88d"]
    retrograde_activity: ["Jupiter retro in Scorpio"]
    ashtakavarga_SAV_transit_sign: "Sat=32, Jup=29, Sun=29, Moon=28 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.01 (Saturn exalted 7H), SIG.15 (Mars-Saturn 7H conjunction — physical tension signature), SIG.11 (Anapha Yoga)]
    signals_that_missed: []
    retrodictive_reasoning: Knee = Saturn/Capricorn body-region classically. Native has Saturn exalted in 7H Libra with Mars — the Mars-Saturn 7H conjunction (SIG.15) is a joint/physical-friction signature. Saturn MD + Saturn-Rahu AD (Rahu amplifies Saturn significations) + Sankata Yogini (Rahu-ruled — "crisis Yogini") triple-converges on a joint-friction event. Fits strongly.
  notes: Concurrent with engineering completion and Cognizant join (same month).
```

```yaml
EVT.2007.XX.XX.03:
  date: 2007
  date_confidence: year-approx (during or shortly after knee surgery EVT.2007.06.XX.01; native confirmed 2007–2008)
  category: health
  subcategory: chronic_onset
  description: Sleep disorder onset arising from medical negligence during the knee arthroscopy (EVT.2007.06.XX.01). The negligence caused a breathlessness problem which subsequently triggered a chronic sleep disorder. Persisted ~18 years across multiple doctors and medications in India and the US until resolved in 2025–2026 (EVT.2025.XX.XX.02).
  magnitude: significant
  valence: negative
  native_reflection: "My sleeping disorder has been going on since my knee surgery, 2007 or 2008. Because of a certain medical negligence, I started the breathlessness problem which led to my sleep disorder. I've tried several drugs, half a dozen of doctors."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2007-09-01
    vimshottari:
      maha_dasha: Saturn (1991-08-19 to 2010-08-18)
      antar_dasha: Rahu (2005-03-31 to 2008-02-05)
      pratyantar_dasha: Sun (2007-07-21 to 2007-09-11)
    yogini:
      maha_dasha: Sankata/Rahu (2003-12-24 to 2011-12-24)
      antar_dasha: Bhramari/Mars (2007-02-03 to 2007-12-24)
    key_transits:
      saturn_sign: Leo
      jupiter_sign: Scorpio
      rahu_sign: Aquarius
      sade_sati_active: false
  retrodictive_match: pending
  notes: Cause — medical negligence at EVT.2007.06.XX.01. Resolution — EVT.2025.XX.XX.02.

EVT.2007.06.XX.02:
  date: 2007-06-XX
  date_confidence: month-exact
  category: education
  subcategory: engineering_completed
  description: Engineering (B.Tech) completed at SRM Chennai, around June 2007.
  magnitude: significant
  valence: positive
  native_reflection: "I completed my BTEC, my engineering and started my first job" — captured as inner-period marker for 2007.
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Rahu
    vimshottari_id: DSH.V.013
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Cancer / Libra
    chara_id: DSH.C.045
    sade_sati_phase: null
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Cancer = 4H from Lagna", "Jupiter transit Scorpio = 8H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -103d", "Solar Partial+Non-Central Pisces -87d", "Lunar Total Aquarius +74d", "Solar Partial+Non-Central Leo +88d"]
    retrograde_activity: ["Jupiter retro in Scorpio"]
    ashtakavarga_SAV_transit_sign: "Sat=32, Jup=29, Sun=29, Moon=28 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.09 (Mercury Vargottama, Yogi — technical/knowledge track)]
    signals_that_missed: []
    retrodictive_reasoning: Engineering completion fits Mercury karaka for tech/analytical knowledge. Saturn-Rahu AD suggests foreign city (Chennai) + unconventional-path completion (SRM not IIT).
  notes: Per native's own summary, 2007 was significant mainly as "engineering + first job" transition — no heavy emotional charge.
```

```yaml
EVT.2007.06.10.01:
  date: 2007-06-10
  date_confidence: exact
  category: career
  subcategory: first_job_joined
  description: Joined Cognizant — first corporate IT job. Tenure exactly one year.
  magnitude: significant
  valence: positive
  native_reflection: "Joint Cognizant round June tenth, 2007."
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Rahu
    vimshottari_id: DSH.V.013
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Cancer / Libra
    chara_id: DSH.C.045
    sade_sati_phase: null
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Cancer = 4H from Lagna", "Jupiter transit Scorpio = 8H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -98d", "Solar Partial+Non-Central Pisces -82d", "Lunar Total Aquarius +79d", "Solar Partial+Non-Central Leo +93d"]
    retrograde_activity: ["Jupiter retro in Scorpio"]
    ashtakavarga_SAV_transit_sign: "Sat=32, Jup=29, Sun=29, Moon=27 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.14 (Sun 10H career-density), SIG.09 (Mercury tech-spine), SIG.10 (Rahu 2H = unconventional-wealth)]
    signals_that_missed: [First-job typically fires under more dignified AD than Rahu. Cognizant was entry-level IT service delivery — low-prestige by native's later standards (he left exactly a year later to prep IIT again). Saturn-Rahu AD = "hard-grind foreign-attempt" first job rather than ambitious career launch. Fits the "transitional" magnitude.]
  notes: Exit on EVT.2008.06.09.01 exactly 1 year later.
```

```yaml
EVT.2008.06.09.01:
  date: 2008-06-09
  date_confidence: exact
  category: career
  subcategory: first_job_exited
  description: Exited Cognizant exactly 1 year after joining. Returned to Bhubaneswar to re-attempt IIT preparation.
  magnitude: significant
  valence: mixed
  native_reflection: "Exited exactly a year later around June 9, 2008."
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.014
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Cancer / Leo
    chara_id: DSH.C.047
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 7H from Moon (Leo)", "Saturn transit Leo = 5H from Lagna", "Jupiter transit Sagittarius = 9H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Capricorn -122d", "Lunar Total Leo -108d", "Solar Total+Central Cancer +53d", "Lunar Partial Aquarius +68d"]
    retrograde_activity: ["Mercury retro in Taurus", "Jupiter retro in Sagittarius"]
    ashtakavarga_SAV_transit_sign: "Sat=30, Jup=31, Sun=29, Moon=30 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CVG.02 (Jupiter 9L dharma-pull), CTR.03 (Jupiter Uccha-weak — dharma visible but weak execution)]
    signals_that_missed: []
    retrodictive_reasoning: Saturn-Jupiter AD is the classical "pilgrimage / re-direction / dharmic-rethink" AD. Native left a paying job to re-prep for IIT — exactly the pattern Jupiter AD in Saturn MD suggests. Per doc: "Worked at Cognizant for one year before returning to Bhubaneswar (c. 2008) specifically to prepare for IIT exams."
  notes: IIT re-attempt outcome: unclear; native eventually pursued MBA at XIMB in 2011 instead.
```

```yaml
EVT.2009.06.XX.01:
  date: 2009-06-XX (or July 2009 per native's range)
  date_confidence: month-exact
  category: loss
  subcategory: grandparent_passing
  description: Paternal grandfather passed away (June or July 2009). Described by native as "academic mentor" — a major emotional setback.
  magnitude: major
  valence: negative
  native_reflection: "Grandfather passed in 2009. I would say in the month of June or July."
  chart_state_at_event:
    vimshottari_md: Saturn
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.014
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Leo / Virgo (if June-Sep) or Leo / Libra (if Sep+)
    chara_id: DSH.C.049 or DSH.C.050
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 7H from Moon (Leo)", "Jupiter transit on natal Moon (Aquarius) — gajakesari-class", "Saturn transit Leo = 5H from Lagna", "Jupiter transit Aquarius = 11H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Capricorn -154d", "Lunar Penumbral Cancer -140d", "Lunar Penumbral Sagittarius +7d", "Solar Total+Central Cancer +22d"]
    retrograde_activity: ["Jupiter retro in Aquarius"]
    ashtakavarga_SAV_transit_sign: "Sat=30, Jup=24, Sun=28, Moon=26 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CVG.02 (Jupiter 9L = grandfather karaka AND paternal-lineage-elder-wisdom), CTR.03 (Jupiter Uccha-weak = vulnerability in 9H-lord significations)]
    signals_that_missed: []
    retrodictive_reasoning: Grandfather = 9H karaka (classical). Native is in Saturn-Jupiter AD — AD lord is 9L Jupiter itself, and Jupiter is Uccha Bala rank 7 LAST per CTR.03. AD of Jupiter while Jupiter is weakly dignified → vulnerability in 9H-significator matters, including paternal-grandfather passing. Academic-mentor framing (native's words) reinforces: Jupiter = guru, knowledge-lineage, teacher — all converge on grandfather role.
  notes: This is among the strongest retrodictive matches in the corpus. Jupiter-9L-weak explaining a grandfather-passing in Jupiter AD is a textbook-classical signal.
```

### Era 5: Peak Life Period — MBA, Thailand, Modeling (2010-2013)

```yaml
EVT.2010.XX.XX.01:
  date: 2010-XX-XX
  date_confidence: year-approx
  category: finance
  subcategory: family_windfall
  description: Father received a large sum from selling real estate (around 2010). Family-level financial windfall, not directly native's but affecting household.
  magnitude: significant
  valence: positive
  native_reflection: "There have not been any windfall major financial windfalls until 2024 other than one period of time which I think is 2010. When my father got a huge sum of money by selling real estate."
  chart_state_at_event:
    vimshottari_md: Saturn (until Aug 2010) → Mercury (from Aug 21, 2010)
    vimshottari_ad: Jupiter → Mercury
    vimshottari_id: DSH.V.014 → DSH.V.015
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Leo / Scorpio or Leo / Sagittarius (depending on month)
    chara_id: DSH.C.051 or DSH.C.052
    sade_sati_phase: null
    transits_of_note: ["Saturn transit Virgo = 6H from Lagna", "Jupiter transit Pisces = 12H from Lagna"]
    eclipses_within_6mo: ["Lunar Partial Gemini -165d", "Solar Annular+Central Capricorn -150d", "Lunar Partial Sagittarius +11d", "Solar Total+Central Gemini +26d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=26, Jup=27, Sun=28, Moon=32 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.08 (Lakshmi Yoga), CVG.02 (9L Jupiter dharma-wealth), SIG.10 (Rahu 2H unconventional-wealth — real estate = Rahu/earth asset)]
    signals_that_missed: []
    retrodictive_reasoning: Mercury MD starting Aug 2010 with Lakshmi + Saraswati Yoga arsenal. Real estate liquidation = 2H/4H asset event. 2H has Rahu (SIG.10) = wealth-from-unconventional-route. Transition from Saturn MD to Mercury MD is a peak-lord-shift that commonly aligns with wealth-inflection points.
  notes: Family-windfall, not native's direct income. Still affects family dynamics and relates to native's early financial horizon.
```

```yaml
EVT.2010.12.XX.01:
  date: 2010-12-XX
  date_confidence: month-exact
  category: travel
  subcategory: first_foreign_trip
  description: First international travel — Thailand trip, December 2010.
  magnitude: significant
  valence: positive
  native_reflection: "Thailand trip - Dec 2010."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.015
    yogini_md: Sankata / Rahu (ends Dec 22, 2011)
    yogini_id: DSH.Y.005
    chara_md_ad: Leo / Sagittarius
    chara_id: DSH.C.052
    sade_sati_phase: null
    transits_of_note: ["Saturn transit Virgo = 6H from Lagna", "Jupiter transit Pisces = 12H from Lagna"]
    eclipses_within_6mo: ["Lunar Partial Sagittarius -171d", "Solar Total+Central Gemini -156d", "Lunar Total Gemini +6d", "Solar Partial+Non-Central Sagittarius +20d"]
    retrograde_activity: ["Mercury retro in Sagittarius"]
    ashtakavarga_SAV_transit_sign: "Sat=26, Jup=27, Sun=29, Moon=27 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CVG.03 (Moon AK Chalit-12 foreign-income chain), SIG.05 (Moon Chalit-12 = foreign delivery), SIG.09 (Mercury Vargottama-Yogi-MD active)]
    signals_that_missed: []
    retrodictive_reasoning: First foreign travel under Mercury MD-Mercury AD peak is coherent — Mercury = 3H/6H Chalit significator for short-mid journeys, and the Moon-AK-Chalit-12 foreign-income chain (CVG.03) activates prominently when Mercury (the dispositor of D9 12H stellium per SIG.06) is dominant. Early foreign travel preceding the long US stint (2019-2023) is a classical preview pattern.
  notes: Preceded US move by 8.5 years.
```

```yaml
EVT.2011.01.XX.01:
  date: 2011-01-XX
  date_confidence: month-exact
  category: education
  subcategory: mba_admission
  description: Secured admission to XIMB (Xavier Institute of Management, Bhubaneswar) MBA program (January 2011). Preceded actual enrollment (June 2011) by 5 months.
  magnitude: major
  valence: positive
  native_reflection: "XIMB achieved seat in Jan 2011."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.015
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Leo / Sagittarius
    chara_id: DSH.C.052
    sade_sati_phase: null
    transits_of_note: ["Saturn transit Virgo = 6H from Lagna", "Jupiter transit Pisces = 12H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Gemini -24d", "Solar Partial+Non-Central Sagittarius -10d", "Solar Partial+Non-Central Taurus +137d", "Lunar Total Sagittarius +151d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=26, Jup=27, Sun=32, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.09 (Mercury MD-AD spine peak — admission outcome in Mercury's domain), SIG.07 (Saraswati Yoga — educational selection), CVG.01 (Mercury operational dominance)]
    signals_that_missed: []
    retrodictive_reasoning: Jan 2011 falls inside Mercury-Mercury AD peak (operational zenith for Mercury-significated outcomes: exams, selections, analytical-competition results). XIMB admission via CAT/XAT score-based selection = classical Mercury territory.
  notes: Admission-event distinct from enrollment-event (EVT.2011.06.XX.01). 5-month gap typical for Indian MBA admission cycles.
```

```yaml
EVT.2011.06.XX.01:
  date: 2011-06-XX
  date_confidence: month-exact
  category: education
  subcategory: mba_enrolled
  description: Formally enrolled at XIMB MBA (June 2011). Beginning of highly fulfilling 2-year program that native describes as a peak-life period (overlapping the 2012-13 "best period of my life" inner-window).
  magnitude: major
  valence: positive
  native_reflection: "Joined in June 2011." Doc: "Joined MBA at Xavier Institute of Management, Bhubaneswar (XIMB) in 2011; highly fulfilling and successful phase."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.015
    yogini_md: Sankata / Rahu
    yogini_id: DSH.Y.005
    chara_md_ad: Leo / Capricorn (started June 5, 2011)
    chara_id: DSH.C.053
    sade_sati_phase: null
    transits_of_note: ["Saturn transit Virgo = 6H from Lagna", "Jupiter transit Aries = 1H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Gemini -175d", "Solar Partial+Non-Central Sagittarius -161d", "Solar Partial+Non-Central Taurus -13d", "Lunar Total Sagittarius +0d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=26, Jup=29, Sun=29, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.09 (Mercury MD-AD spine), SIG.07 (Saraswati Yoga — Jupiter+Venus+Mercury kendra/trikona), CVG.01 (Mercury operational dominance), SIG.14 (Sun 10H career-density — MBA = career-prep pipeline), SIG.08 (Lakshmi Yoga — dharma-wealth-path formation)]
    signals_that_missed: []
    retrodictive_reasoning: Enrollment under Mercury MD-Mercury AD peak with Chara MD/AD just shifting into Leo/Capricorn (Capricorn = 10H career house, Sun-ruled) = triple-education + career-launch convergence. Xavier = Christian institution (per doc, native consistently succeeds in Christian-institution contexts — behavioral correlation worth examining in v2.0 Deep Analysis).
  notes: 2012-2013 inner-period "best of my life" overlaps with the second year of this MBA phase (see §5).
```

```yaml
EVT.2012.09.XX.01:
  date: 2012-09-XX
  date_confidence: month-exact
  category: creative
  subcategory: modeling
  description: Modeling at XIMB (September 2012). Native acknowledged as physically attractive with "masculine, well-built presence" per source document.
  magnitude: moderate
  valence: positive
  native_reflection: "Did modeling in XIMB in Sep 2012."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.015
    yogini_md: Mangala / Moon
    yogini_id: DSH.Y.006
    chara_md_ad: Leo / Pisces
    chara_id: DSH.C.055
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Taurus = 2H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Taurus -117d", "Lunar Partial Scorpio -102d", "Solar Total+Central Libra +59d", "Lunar Penumbral Taurus +74d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=29, Sun=30, Moon=30 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.09 (Mercury presentation/communication), SIG.07 (Saraswati — charisma component)]
    signals_that_missed: [Venus weak (SIG.12) makes sustained modeling career unlikely — this was a phase/episode, not a career. That fits "did modeling at XIMB" as a one-off rather than a profession.]
  notes: Aligns with peak-life period 2012-2013 (see §5).
```

```yaml
EVT.2012.XX.XX.02:
  date: 2012
  date_confidence: year-approx (during XIMB MBA, 2011–2013; likely second year ~2012)
  category: education
  subcategory: leadership_role
  description: Elected President of the International Relations Committee (IRC) at XIMB. Had the opportunity to stand for General Secretary of the entire college (higher post) but declined — native describes his choice as "selfish," preferring to avoid the social-service load. IRC presidency gave significant access to international students and visitors; multiple short-term relationships developed (Japanese, Indian, American).
  magnitude: moderate
  valence: positive
  native_reflection: "I could have become the general secretary for the entire college but I was selfish and I didn't want to put so much effort in social service. I decided to just become the President of the International Relationship Committee. That gave me a lot of access to the foreigners."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2012-09-01
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Mercury (2010-08-18 to 2013-01-14)
      pratyantar_dasha: Saturn (2012-08-28 to 2013-01-14)
    yogini:
      maha_dasha: Mangala/Moon (2011-12-24 to 2012-12-24)
      antar_dasha: Siddha/Venus (2012-07-24 to 2012-10-03)
    key_transits:
      saturn_sign: Libra
      jupiter_sign: Taurus
      rahu_sign: Scorpio
      sade_sati_active: false
  retrodictive_match: pending

EVT.2012.10.XX.01:
  date: 2012-10-XX
  date_confidence: month-exact
  category: relationship
  subcategory: romantic_concurrent
  description: Relationship #3 started (October 2012, 10-year duration → ended ~October 2022). Concurrent with primary long-term relationship (R#1) through marriage year (2013) and into marriage years.
  magnitude: major
  valence: mixed
  native_reflection: "Oct 2012 (10 years)."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury
    vimshottari_id: DSH.V.015
    yogini_md: Mangala / Moon
    yogini_id: DSH.Y.006
    chara_md_ad: Leo / Pisces
    chara_id: DSH.C.055
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Taurus = 2H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Taurus -147d", "Lunar Partial Scorpio -132d", "Solar Total+Central Libra +29d", "Lunar Penumbral Taurus +44d"]
    retrograde_activity: ["Jupiter retro in Taurus"]
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=29, Sun=26, Moon=26 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.12 (Venus weak = relational instability), CVG.07 (Gemini 3H nexus with A5/A11 = secondary-relational signifiers), SIG.09 (Mercury MD peak = charisma-at-peak)]
    signals_that_missed: [Sexual magnetism during this peak period is not a single signal but a confluence: Mercury MD + Saraswati + physical attributes listed in doc (6'3", muscular, 2012-13 peak fitness).]
  notes: Duration ~10 years into October 2022 — ending coincides with Mercury-Rahu AD → Mercury-Jupiter AD transition (Sep 2022) and the start of 2022-2024 "mix" period native flagged.
```

```yaml
EVT.2013.03.XX.01:
  date: 2013-03-XX
  date_confidence: month-exact
  category: education
  subcategory: mba_graduation
  description: Graduated from XIMB MBA (March 2013).
  magnitude: major
  valence: positive
  native_reflection: "Graduated from XMD in March 2013."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Ketu
    vimshottari_id: DSH.V.016
    yogini_md: Pingala / Sun
    yogini_id: DSH.Y.007
    chara_md_ad: Leo / Aries
    chara_id: DSH.C.056
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Taurus = 2H from Lagna"]
    eclipses_within_6mo: ["Solar Total+Central Libra -121d", "Lunar Penumbral Taurus -106d", "Lunar Partial Libra +41d", "Solar Annular+Central Aries +56d"]
    retrograde_activity: ["Mercury retro in Aquarius", "Saturn retro in Libra"]
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=29, Sun=27, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.09 (Mercury MD — education completion), Ketu AD classical = endings/liberation (graduation fits perfectly)]
    signals_that_missed: []
    retrodictive_reasoning: Ketu AD starting within Mercury MD is a textbook "completion → liberation into new chapter" signature. Native graduated March 2013 and was immediately placed by Mahindra Retail (May 2013) — smooth transition typical of Mercury-Ketu AD.
  notes: XMD in native's dictation = XIMB. Graduation formally happens around March/April for Indian MBA.
```

```yaml
EVT.2013.05.XX.01:
  date: 2013-05-XX
  date_confidence: month-exact
  category: career
  subcategory: corporate_job_joined
  description: Formally joined Mahindra Retail (May 2013) following XIMB placement and internship. Beginning of 10-year Mahindra Group tenure.
  magnitude: major
  valence: positive
  native_reflection: "I was immediately picked up in placement by Mahindra Retail so after internship I formally joined in May 2013."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Ketu
    vimshottari_id: DSH.V.016
    yogini_md: Pingala / Sun
    yogini_id: DSH.Y.007
    chara_md_ad: Leo / Aries
    chara_id: DSH.C.056
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Taurus = 2H from Lagna"]
    eclipses_within_6mo: ["Solar Total+Central Libra -182d", "Lunar Penumbral Taurus -167d", "Lunar Partial Libra -19d", "Solar Annular+Central Aries -4d"]
    retrograde_activity: ["Saturn retro in Libra"]
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=29, Sun=29, Moon=28 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.14 (10H career-density Sun+Mercury+AL), CVG.04 (10H career convergence)]
    signals_that_missed: [Ketu AD for career launch is unusual — native's eventual description of Mahindra Retail ("crashed in 2016") retrodictively reveals the Ketu-AD undercurrent: career launched with hidden instability from the start. This subtle signal would be captured in v2.0 Deep Analysis.]
    retrodictive_reasoning: Pingala/Sun Yogini = Sun = 10H (native's career house). Career launch under Pingala Yogini is a strong-Sun indicator. But Ketu AD lord underpins eventual dissolution (company crashed 2016, native switched).
  notes: Mahindra Retail → Tech Mahindra transition March 2017 (see EVT.2017.03.XX.01).
```

```yaml
EVT.2013.XX.XX.01:
  date: 2013-XX-XX
  date_confidence: year-exact (month unknown — see §6 GAP.FATHER_KIDNEY_MONTH.01)
  category: family
  subcategory: parent_illness_onset
  description: Father's kidney disease began in 2013. This became a 5-year illness culminating in his passing on 2018-11-28. Corrected in v1.1 — v1.0 incorrectly listed 2000 based on source doc phrasing.
  magnitude: major
  valence: negative
  native_reflection: "Father Kidney disease onset date is 2013" (Session 2 v1.1 correction).
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mercury (if before Jan 18, 2013) OR Ketu (if after Jan 18, 2013)
    vimshottari_id: DSH.V.015 or DSH.V.016
    yogini_md: Pingala / Sun (from Dec 22, 2012) — most of 2013
    yogini_id: DSH.Y.007
    chara_md_ad: Leo / Pisces → Leo / Aries (Mar 5, 2013) → Leo / Taurus (Oct 5, 2013) depending on month
    chara_id: DSH.C.055 or DSH.C.056 or DSH.C.057
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Lunar Partial Libra -50d", "Solar Annular+Central Aries -35d", "Lunar Penumbral Scorpio -20d", "Lunar Penumbral Aries +125d"]
    retrograde_activity: ["Saturn retro in Libra"]
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=28, Sun=28, Moon=30 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [CTR.03 (Jupiter Uccha-weak = 9L/father-significator foundational vulnerability), CVG.02 (Jupiter 9L dharma-wealth chain with weakness embedded), SIG.12 (Venus weak — kidney-Venus-Libra body-region link via Venus as 7L in classical mapping)]
    signals_that_missed: [Specific Kidney-Venus-9H body-map signal not computed in v1.2.1. Onset during son's (native's) Mercury MD peak = unusual timing for father's 9H-vulnerability to manifest — suggests transit trigger not yet examined. Candidate: Saturn transit Libra (2011-2014) activating native's 7H Saturn-exalted position by gochara + Venus vulnerability. Worth computing in v1.1.]
    retrodictive_reasoning: Jupiter Uccha-weak (CTR.03 — 9L for native = father) is the foundational father-vulnerability signal carried by the chart. 5-year illness is not Saturn-timing (Saturn = longer durations typically); fits Mercury-MD-adjacent timing as son's chart-phase is Mercury-dominated during father's decline years (2013-2018).
  notes: Culminates in father's passing 2018-11-28 (EVT.2018.11.28.01). Month of 2013 onset not yet specified — flagged in §6 gap register.
```

```yaml
EVT.2013.12.11.01:
  date: 2013-12-11
  date_confidence: exact
  category: family
  subcategory: marriage
  description: Married childhood girlfriend (R#1, dating since 1998-02-16). Marriage duration before separation: ~12 years (wedding → current stable-separation state).
  magnitude: life-altering
  valence: mixed
  native_reflection: "Marriage was in 11th December 2013." Doc: "Marriage deeply emotional but practically challenging. 'Pain-pleasure' dynamic. Marriage nearing separation/divorce after two decades of turbulence." Session 2 update: currently separated, stable arrangement, things looking up.
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Ketu
    vimshottari_id: DSH.V.016
    yogini_md: Pingala / Sun
    yogini_id: DSH.Y.007
    chara_md_ad: Leo / Taurus
    chara_id: DSH.C.057
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H from Moon (Libra)", "Saturn transit Libra = 7H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Lunar Penumbral Aries -53d", "Solar Annular-Total+Central Libra -37d", "Lunar Total Libra +125d", "Solar Annular+Non-Central Aries +139d"]
    retrograde_activity: ["Jupiter retro in Gemini"]
    ashtakavarga_SAV_transit_sign: "Sat=23, Jup=28, Sun=29, Moon=27 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.01 (Saturn exalted 7H — the defining marriage-house signature: authority-through-tension in partnership), SIG.15 (Hidden Raja Yoga Mars+Saturn exalted conjunction 7H), CVG.08 (Aries-Libra axis triple-aspect), CTR.01 (Saturn Shadbala #2 vs Shuddha Pinda #7 LAST — "dramatic not compound" — retrodictively explains the pain-pleasure dynamic: Saturn is strong in Shadbala so marriage has gravity/longevity structure, but Shuddha Pinda last = the compounding doesn't accrue, explaining "turbulence" rather than deepening)]
    signals_that_missed: [Ketu AD as wedding-AD is unusual — Ketu = detachment/non-attachment, which retrodictively explains BOTH the "will it last" question present from the start AND the eventual separation trajectory.]
    retrodictive_reasoning: STRONGEST MATCH in the corpus. Four of the chart's top signatures converge on this event: SIG.01, SIG.15, CVG.08, and CTR.01. The marriage is the chart's central 7H-signature stage. Pain-pleasure dynamic is exactly what Mars-Saturn-7H-exalted describes in classical BPHS.
  notes: Per native, currently separated but stable and improving. This is an ongoing event — status will need update in v1.1+ as trajectory resolves.
```

### Era 6: Corporate Ascendance, Mahindra Tenure (2016-2018)

```yaml
EVT.2016.XX.XX.01:
  date: 2016-XX-XX
  date_confidence: year-exact
  category: career
  subcategory: employer_instability
  description: Mahindra Retail company "crashed" (native's words); triggered career stress and job search. Decision to switch to Tech Mahindra crystallized during this period.
  magnitude: major
  valence: negative
  native_reflection: "2016 was a bit stressful when I switched from... when I was looking for a job outside Mahindra retail as the company had crashed and that's when I decided to switch over to Tech Mahindra."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Venus (through Nov 15, 2016)
    vimshottari_id: DSH.V.017
    yogini_md: Dhanya / Jupiter
    yogini_id: DSH.Y.008
    chara_md_ad: Leo / Leo → Virgo / Leo (switch Feb 5, 2016)
    chara_id: DSH.C.060 → DSH.C.061
    sade_sati_phase: null
    transits_of_note: ["Ketu transit on natal Moon (Aquarius)", "Saturn transit Scorpio = 8H from Lagna", "Jupiter transit Leo = 5H from Lagna"]
    eclipses_within_6mo: ["Solar Total+Central Aquarius -97d", "Lunar Penumbral Virgo -83d", "Solar Annular+Central Leo +78d", "Lunar Penumbral Pisces +93d"]
    retrograde_activity: ["Mars retro in Scorpio", "Saturn retro in Scorpio"]
    ashtakavarga_SAV_transit_sign: "Sat=29, Jup=30, Sun=28, Moon=23 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.12 (Venus Shadbala rank 7 weakest — Venus AD triggers weakness-lord period, professionally destabilizing), CTR.03 (Jupiter Uccha-weak), CVG.04 (10H career-density with Mercury active = career-stakes high but under weak-Venus AD)]
    signals_that_missed: []
    retrodictive_reasoning: Venus is Shadbala rank 7 (SIG.12) — weakest of the natal planets by Shadbala. Mercury-Venus AD = Venus AD inside Mercury MD = the weakness-lord gets a 2-year-10-month spotlight (2014-01-15 to 2016-11-15). Company-crash coinciding with end of Venus AD (Nov 2016) is high-confidence retrodictive match. Dhanya/Jupiter Yogini + Jupiter Uccha-weak (CTR.03) = dharmic-restructure but with instability.
  notes: Sets up the Tech Mahindra switch (see EVT.2017.03.XX.01).
```

```yaml
EVT.2017.03.XX.01:
  date: 2017-03-XX
  date_confidence: month-exact
  category: career
  subcategory: employer_switch
  description: Switched from Mahindra Retail to Tech Mahindra (March 2017). Within-Mahindra-Group move; upgraded platform. Leads to US deputation in 2019.
  magnitude: major
  valence: positive
  native_reflection: "Switch to Tech Mahindra in 2017 I would say March 2017."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Sun
    vimshottari_id: DSH.V.018
    yogini_md: Dhanya / Jupiter
    yogini_id: DSH.Y.008
    chara_md_ad: Virgo / Cancer
    chara_id: DSH.C.062
    sade_sati_phase: null
    transits_of_note: ["Saturn transit 9H (Sagittarius) — father-karma activation", "Ketu transit on natal Moon (Aquarius)", "Saturn transit Sagittarius = 9H from Lagna", "Jupiter transit Virgo = 6H from Lagna"]
    eclipses_within_6mo: ["Lunar Penumbral Pisces -179d", "Lunar Penumbral Cancer -31d", "Solar Annular+Central Aquarius -16d", "Lunar Partial Capricorn +145d"]
    retrograde_activity: ["Venus retro in Pisces", "Jupiter retro in Virgo"]
    ashtakavarga_SAV_transit_sign: "Sat=31, Jup=26, Sun=27, Moon=23 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.14 (Sun 10H career-density), CVG.04 (10H career convergence with Sun as native-lord-of-career-house), SIG.09 (Mercury MD + Sun AD = MD-AD lords both in 10H natal)]
    signals_that_missed: []
    retrodictive_reasoning: Sun AD in Mercury MD where BOTH Sun and Mercury are in 10H Capricorn natally = MD-AD lords co-present in the career house. One of the strongest career-advancement AD configurations possible. Switch to Tech Mahindra (a larger, more prestigious Mahindra subsidiary) fits perfectly. Dhanya/Jupiter Yogini = dharmic-upgrade overlay.
  notes: The Tepper School CMU Executive MBA sponsorship by Tech Mahindra (completed June 2023 per native) originated from performance at Tech Mahindra starting this tenure.
```

### Era 7: Deepest Loss, US Era, Personal Rupture (2018-2022)

```yaml
EVT.2018.11.28.01:
  date: 2018-11-28
  date_confidence: exact
  category: loss
  subcategory: parent_passing
  description: Father passed away on 28 November 2018, culminating 18-year kidney disease journey (onset ~2000). Native ran between Hyderabad and Bhubaneswar during final hospital phase.
  magnitude: life-altering
  valence: negative
  native_reflection: "I lost my father, so it was a mentally traumatic time running a lot of the hospitals, running from Hyderabad to Neshwar [Bhubaneswar]." Date: "November 2018 precisely I think it is 28th November 2018."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Moon
    vimshottari_id: DSH.V.019
    yogini_md: Dhanya / Jupiter (ends Dec 22, 2017 → Bhramari/Mars from Dec 22, 2017)
    yogini_id: DSH.Y.009 (Bhramari/Mars, 2017-12-22 → 2021-12-22)
    chara_md_ad: Virgo / Aries
    chara_id: DSH.C.065
    sade_sati_phase: null (Sade Sati Cycle 2 starts Jan 2020, ~2 months after event)
    transits_of_note: ["Saturn transit Sagittarius = 9H from Lagna — CLASSICAL FATHER-DEATH TRIGGER", "Jupiter transit Scorpio 10°16' conjunct Sun 11°50' + Mercury retro 09°44' — heavy stellium in 8H from Lagna (death house)", "Ketu transit Capricorn 05°14' — on 10H natal Sun+Mercury stellium", "Saturn transit 11H from Moon (Sagittarius)"]
    eclipses_within_6mo: ["Solar Partial Gemini 2018-07-13 (-137d)", "Lunar Total Capricorn 2018-07-27 (-123d) — ON native's 10H Sun+Mercury natal stellium", "Solar Partial Cancer 2018-08-11 (-108d)", "Solar Partial Sagittarius 2019-01-06 (+39d)", "Lunar Total Cancer 2019-01-21 (+54d)"]
    retrograde_activity: ["Mercury retrograde in Scorpio (conjunct Sun + Jupiter)"]
    ashtakavarga_SAV_transit_sign: "Sat=31(Sag 9H high SAV), Jup=29(Sco 8H), Sun=29(Sco 8H), Moon=32(Can 4H); SAV-high Saturn delivering 9H structural event"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CTR.03 (Jupiter Uccha-weak = 9L/father-significator weak — foundational vulnerability across 18-year illness), SIG.04 (Moon AK — AK AD is soul-level event), SIG.05 (Moon Chalit-12 = loss-domain), CVG.02 (Jupiter 9L chain with weakness embedded)]
    signals_that_missed: [Saturn transit Sagittarius (9H) at death is the transit-level confirmation not in v6.0-integrated-with-event format, but is classically the strongest father-loss transit trigger. Should be captured in v1.1 after Jagannatha Hora export.]
    retrodictive_reasoning: Multi-signal convergence. (1) Mercury-Moon AD: Moon is AK, Chalit-12 (loss-house), 4L (mother/home — father's passing affects home/security). (2) CTR.03 Jupiter-weakness explains 18-year-illness culmination. (3) Bhramari/Mars Yogini overlay = Mars AD-like intensity. (4) Saturn transit 9H (Sagittarius) at event is classical father-death trigger. Four-fold convergence = yes retrodictive match with high confidence.
  notes: One of the most foundationally explained events in the corpus. Also a cornerstone for native's psychology: the "2018-2021" inner period starts here (see §5.4).
```

```yaml
EVT.2019.05.XX.01:
  date: 2019-05-XX
  date_confidence: month-exact
  category: residential+travel
  subcategory: foreign_move_start (dual-tagged residential+travel per GAP.M4A.04 partial close, LEL v1.6)
  description: Moved to the United States on Tech Mahindra work deputation (May 2019). 4-year stint; returned to India May 2023. Correction from source doc (which said 2018): native explicitly corrected to May 2019 in Session 2.
  magnitude: life-altering
  valence: positive
  native_reflection: "The move to US happened in May 2019." Doc framing: "US Stint: Moved to the United States on a work permit; lived there for 4.5 years, returned to India in May 2023."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Mars
    vimshottari_id: DSH.V.020
    yogini_md: Bhramari / Mars
    yogini_id: DSH.Y.009
    chara_md_ad: Virgo / Aries
    chara_id: DSH.C.065
    sade_sati_phase: null (Sade Sati Cycle 2 starts Jan 2020)
    transits_of_note: ["Saturn transit 9H (Sagittarius) — father-karma activation", "Saturn transit Sagittarius = 9H from Lagna", "Jupiter transit Scorpio = 8H from Lagna"]
    eclipses_within_6mo: ["Solar Partial+Non-Central Sagittarius -128d", "Lunar Total Cancer -113d", "Solar Total+Central Gemini +48d", "Lunar Partial Sagittarius +62d"]
    retrograde_activity: ["Jupiter retro in Scorpio", "Saturn retro in Sagittarius"]
    ashtakavarga_SAV_transit_sign: "Sat=31, Jup=29, Sun=29, Moon=26 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CVG.03 (Moon AK Chalit-12 foreign-income chain — the dominant foreign-architecture signal), SIG.05 (Moon Chalit-12 foreign delivery), SIG.06 (D9 12H Gemini stellium), SIG.15 (Mars-Saturn 7H — Mars AD activates the 7H tension-engine; Mars also = initiative/action to move)]
    signals_that_missed: []
    retrodictive_reasoning: Mercury-Mars AD with Mars AD lord exalted in 7H natally AND foreign-income chain (CVG.03) active = clean match. Bhramari/Mars Yogini doubles Mars intensity. Chara Virgo/Aries with Aries AD = Aries-Lagna-self moving abroad (Lagna assertion via foreign). Classical result: foreign move happens under foreign-chain-lord AD when other yogas support.
  notes: 4-year US stint transforms native from salaried Indian engineer/analyst to globally-exposed manager. Sets up entrepreneurial awakening post-2023.
```

```yaml
EVT.2021.01.XX.01:
  date: 2021-01-XX
  date_confidence: month-exact
  category: health
  subcategory: panic_anxiety_episode
  description: Health episode with jitters and sweating — panic/anxiety episode in January 2021. (Corrected in v1.1 — v1.0 had this at Jan 2022.) Native was in US stint, roughly 1 year before twins' birth.
  magnitude: significant
  valence: negative
  native_reflection: "Health issue - Jitters, sweating, panic episode in Jan 2021" (Session 2 v1.1 correction).
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Rahu
    vimshottari_id: DSH.V.021
    yogini_md: Bhramari / Mars
    yogini_id: DSH.Y.009
    chara_md_ad: Virgo / Capricorn
    chara_id: DSH.C.068
    sade_sati_phase: TRS.SS.C2.P1 (Cycle 2 Rising, Saturn in Capricorn = 12th from Moon; 2020-01-24 to 2022-04-28)
    transits_of_note: ["Saturn transit Capricorn = 10H from Lagna", "Jupiter transit Capricorn = 10H from Lagna"]
    eclipses_within_6mo: ["Lunar Penumbral Taurus -45d", "Solar Total+Central Scorpio -31d", "Lunar Total Scorpio +131d", "Solar Annular+Central Taurus +146d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=32, Jup=32, Sun=32, Moon=32 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.10 (Rahu 2H — Rahu AD classical anxiety karaka), SIG.13 (Sade Sati Rising — Saturn in Cap 12th from Moon = mental pressure phase, ~1 year into Cycle 2), SIG.11 (Anapha Yoga Saturn 12th from Moon), SIG.15 (Mars-Saturn 7H exalted — Bhramari/Mars Yogini activates Mars-Saturn-tension-engine at Yogini level), CTR.01 (Saturn Shadbala-strong compressive pressure)]
    signals_that_missed: []
    retrodictive_reasoning: v1.1 correction STRENGTHENS the retrodictive match. Bhramari/Mars Yogini (runs Dec 2017 – Dec 2021) = Mars-level tension-at-physiological-intensity; Mars = adrenaline/jitters karaka. Combined with Rahu AD (anxiety) + Sade Sati Cycle 2 Rising peak (~1 year in, max subconscious-pressure) + COVID-era US-stint isolation context = textbook panic-episode onset chart. Chara Virgo/Capricorn: Virgo = 6H (daily stress, psychosomatic), Capricorn = 10H (work pressure) — both activated.
  notes: Now occurs ~1 year BEFORE twins' birth (not 2 weeks before as miscoded in v1.0). The pre-birth-stress hypothesis from v1.0 does not apply; this is a discrete panic episode during US COVID period.
```

```yaml
EVT.2021.XX.XX.02:
  date: 2021
  date_confidence: year-approx (native said selected in 2021; program ran 2022–2023)
  category: career
  subcategory: award_selection
  description: Selected as one of the top employees across the Mahindra Group and sponsored for a 1-year Executive MBA at Tepper School of Business, Carnegie Mellon University. Program ran 2022–2023. Native experienced this as a "deja vu" — CMU had been offered and declined in 2004 (EVT.2004.XX.XX.02); 17 years later it arrived as a sponsored award.
  magnitude: significant
  valence: positive
  native_reflection: "I was selected as one of the top employees of the Mahindra group and they sponsored me for a one-year executive MBA. It was a deja vu incident for me because the university I really wished to be part of but could not because of issues at that point in time came back to me and fell in my lap."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2021-04-01
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Rahu (2020-02-14 to 2022-09-03)
      pratyantar_dasha: Mercury (2021-04-01 to 2021-08-11)
    yogini:
      maha_dasha: Bhramari/Mars (2017-12-24 to 2021-12-24)
      antar_dasha: Sankata/Rahu (2020-06-04 to 2021-04-24)
    key_transits:
      saturn_sign: Capricorn
      jupiter_sign: Capricorn
      rahu_sign: Taurus
      sade_sati_active: true
  retrodictive_match: pending
  notes: Deja vu pair — EVT.2004.XX.XX.02 (CMU declined) → EVT.2023.06.XX.01 (CMU completed).

EVT.2021.XX.XX.03:
  date: 2021
  date_confidence: year-approx (native said "2021 or 2022")
  category: career
  subcategory: business_stalled
  description: A second sand quarry was acquired and attempted for operationalisation ~2021–2022 but could not be made operational due to public hearing requirements. Multiple attempts to bypass or resolve the public hearing were unsuccessful over ~4–5 years until April 2026.
  magnitude: moderate
  valence: mixed
  native_reflection: "We had one in 2021 or 2022, we had not made it operational because of a public hearing which was a complicated thing. Lots of things we tried to avoid public hearing, but didn't happen."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2021-09-01
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Rahu (2020-02-14 to 2022-09-03)
      pratyantar_dasha: Ketu (2021-08-11 to 2021-10-04)
    yogini:
      maha_dasha: Bhramari/Mars (2017-12-24 to 2021-12-24)
      antar_dasha: Dhanya/Jupiter (2021-08-24 to 2021-12-24)
    key_transits:
      saturn_sign: Capricorn
      jupiter_sign: Aquarius
      rahu_sign: Taurus
      sade_sati_active: true
  retrodictive_match: pending
  notes: Resolution — EVT.2026.04.08.01.

EVT.2022.01.03.01:
  date: 2022-01-03
  date_confidence: exact
  category: family
  subcategory: child_birth
  description: Twin daughters born on 3 January 2022. Native's only children.
  magnitude: life-altering
  valence: positive
  native_reflection: Doc: "Twin daughters born on 3 January 2022."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Rahu
    vimshottari_id: DSH.V.021
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Virgo / Sagittarius
    chara_id: DSH.C.069
    sade_sati_phase: TRS.SS.C2.P1 (Cycle 2 Rising, Saturn in Capricorn 12th from Moon)
    transits_of_note: ["Jupiter transit Aquarius = 11H AND ON NATAL MOON (gajakesari-class children transit)", "Saturn transit Capricorn = 10H from Lagna, 12H from Moon (Sade Sati Rising)", "Rahu transit Aries = 1H Lagna (identity-amplification at parenthood)", "Ketu transit Libra = 7H (partnership-house axis active)"]
    eclipses_within_6mo: ["Lunar Partial Taurus 2021-11-19 (-45d) — ON natal Rahu 2H", "Solar Total Sagittarius 2021-12-04 (-30d) — ON natal 9H Jupiter+Venus", "Solar Partial Taurus 2022-04-30 (+117d) — ON natal Rahu 2H again", "Lunar Total Scorpio 2022-05-16 (+133d) — ON natal 8H Ketu"]
    retrograde_activity: ["None of the 5 classical retrograders retrograde at event"]
    ashtakavarga_SAV_transit_sign: "Sat=32(Cap), Jup=24(Aqu on Moon), Sun=31(Sag), Moon=27(Pis); Jup SAV-24 is just below median but AD lord activation combined with gajakesari transit tops for children"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.10 (Rahu 2H — Rahu AD classically multiplies/doubles/produces-unusual — TWINS fit Rahu's "multiplication" signature exactly), SIG.09 (Mercury MD = 5L-adjacent karaka; Mercury Vargottama in 10H natally is unusual-progeny-house-indicator in some schools), CVG.02 (Jupiter 9L — Jupiter is also 5L-from-Moon = children karaka)]
    signals_that_missed: [Ketu in 5H Leo natally (children's house) is typically a delayed/unusual-child signal, retrodictively explaining "twins" rather than conventional child timing — should be formalized in RPT.LFE.01 in v2.0.]
    retrodictive_reasoning: TWINS = Rahu signature at the AD level is the textbook explanation. Rahu multiplies, doubles, unusualifies. Rahu AD producing twins is classical Nadi-tradition retrodiction. Mercury MD-Rahu AD child-birth with Jupiter transit aspecting 11H/5H is a solid multi-signal match.
  notes: Exactly at age 37 years 11 months for native. Relatively late progeny by Indian norms — consistent with Ketu-5H delayed-child signature and Saturn-dominant timing.
```

```yaml
EVT.2022.XX.XX.02:
  date: 2022
  date_confidence: year-approx (during CMU Tepper MBA period 2022–2023; exact month unknown)
  category: relationship
  subcategory: romantic_concurrent
  description: A serious affair during the CMU Tepper Executive MBA period (2022–2023). Distinct from R#3 (ended October 2022, EVT.2022.10.XX.01). This affair generated significant marital tension and is cited by native as a direct contributing cause of the current marital separation (EVT.CURRENT.01).
  magnitude: life-altering
  valence: mixed
  native_reflection: "I had a pretty serious affair at that point in time which resulted in a lot of issues in my marriage and for which I am in a separated state today."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2022-06-01
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Rahu (2020-02-14 to 2022-09-03)
      pratyantar_dasha: Moon (2022-04-24 to 2022-07-10)
    yogini:
      maha_dasha: Bhadrika/Mercury (2021-12-24 to 2026-12-24)
      antar_dasha: Bhadrika/Mercury (2021-12-24 to 2022-09-04)
    key_transits:
      saturn_sign: Aquarius
      jupiter_sign: Pisces
      rahu_sign: Aries
      sade_sati_active: true
  retrodictive_match: pending
  notes: Marital consequence — EVT.CURRENT.01.

EVT.2022.10.XX.01:
  date: 2022-10-XX
  date_confidence: month-exact (estimated — user said "10 years" duration from Oct 2012)
  category: relationship
  subcategory: romantic_concurrent_ended
  description: Relationship #3 ended (approximately October 2022, 10-year duration from start). Coincides with Mercury-Jupiter AD transition (Sep 2022) and start of "2022-2024 mix" inner period.
  magnitude: significant
  valence: mixed
  native_reflection: Implied by "Oct 2012 (10 years)" and 2022-24 inner period narrative: "new relationships and rupture of old."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Jupiter (from Sep 6, 2022)
    vimshottari_id: DSH.V.022
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Virgo / Libra
    chara_id: DSH.C.071
    sade_sati_phase: TRS.SS.C2.P2 transitioning to C2.P3 (Saturn re-entering Capricorn July 13, 2022)
    transits_of_note: ["Saturn transit Capricorn = 10H from Lagna", "Jupiter transit Pisces = 12H from Lagna"]
    eclipses_within_6mo: ["Solar Partial+Non-Central Aries -167d", "Lunar Total Scorpio -151d", "Solar Partial+Non-Central Libra +10d", "Lunar Total Aries +24d"]
    retrograde_activity: ["Jupiter retro in Pisces", "Saturn retro in Capricorn"]
    ashtakavarga_SAV_transit_sign: "Sat=32, Jup=27, Sun=26, Moon=28 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [CTR.03 (Jupiter Uccha-weak AD = dharma-restructure with weak execution), SIG.12 (Venus weak — relational dissolution continues)]
    signals_that_missed: [Specific infidelity-ending pattern not computed in v1.2.1.]
  notes: Marks close of a 10-year concurrent relational track. Sets up "new relationships" mentioned in 2022-24 period.
```

### Era 8: Pivot — India Return, Business, Sand Mines (2023-2025)

```yaml
EVT.2023.05.XX.01:
  date: 2023-05-XX
  date_confidence: month-exact
  category: residential+travel
  subcategory: foreign_return (dual-tagged residential+travel per GAP.M4A.04 partial close, LEL v1.6)
  description: Returned to India from United States (May 2023) after 4-year stint. Concurrent with US job loss (exact date unclear — see §6 Gap Register). This marks pivotal transition from salaried corporate employment to entrepreneurship.
  magnitude: life-altering
  valence: mixed
  native_reflection: "I lost my job in the US moved to India in fact was a pivotal point where I completely changed my life from salary job to business which I couldn't have done otherwise was primarily driven by turn of events and my own decision."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.022
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Virgo / Libra
    chara_id: DSH.C.071
    sade_sati_phase: TRS.SS.C2.P4 (Saturn in Aquarius peak, 2023-01-18 to 2025-03-29)
    transits_of_note: ["Saturn transit Aquarius = 11H from Lagna", "Jupiter transit Aries = 1H from Lagna"]
    eclipses_within_6mo: ["Solar Annular-Total+Central Aries -24d", "Lunar Penumbral Libra -9d", "Solar Annular+Central Virgo +152d", "Lunar Partial Aries +166d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=24, Jup=29, Sun=29, Moon=27 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CTR.03 (Jupiter Uccha-weak = job-loss vulnerability via weak 9L; ALSO dharma-path-pivot force), CVG.02 (Jupiter 9L dharma-wealth chain activating), SIG.13 (Sade Sati Peak Phase — life-direction compressive restructuring), CVG.08 (Aries-Libra axis triple-aspect including Bhrigu Bindu + Muntha — major life-inflection window)]
    signals_that_missed: []
    retrodictive_reasoning: STRONG MATCH. Jupiter AD = dharma-direction AD. Jupiter is 9L (dharma house lord) but Uccha-weak (CTR.03) → dharmic-pivot-forced-by-loss is the exact signature. Sade Sati Peak concurrent = compressive life-direction change. Native's reflection ("turn of events and my own decision") captures precisely the AD quality of forced-dharmic-pivot.
  notes: Single most transformative turning point of the adult life per native's own narrative. Sets up Marsys founding 2 months later.
```

```yaml
EVT.2023.06.XX.01:
  date: 2023-06-XX
  date_confidence: month-exact (TBC — native's dictation ambiguous; confirmed during Session 2 as Tepper Exec MBA completion)
  category: education
  subcategory: executive_education_completed
  description: Tepper School of Business (Carnegie Mellon University) Executive MBA completed (June 2023). Sponsored by Tech Mahindra earlier in tenure. Recognized as top performer.
  magnitude: major
  valence: positive
  native_reflection: "That was Tepper School... June 2023."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.022
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Virgo / Virgo
    chara_id: DSH.C.072
    sade_sati_phase: TRS.SS.C2.P4 (Peak Aquarius)
    transits_of_note: ["Saturn transit Aquarius = 11H from Lagna", "Jupiter transit Aries = 1H from Lagna"]
    eclipses_within_6mo: ["Solar Annular-Total+Central Aries -55d", "Lunar Penumbral Libra -40d", "Solar Annular+Central Virgo +121d", "Lunar Partial Aries +135d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=24, Jup=29, Sun=29, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.07 (Saraswati Yoga — educational achievement), CVG.02 (Jupiter 9L dharma-wealth with Jupiter AD = dharma credential), SIG.09 (Mercury Vargottama spine)]
    signals_that_missed: []
    retrodictive_reasoning: Second MBA (executive-level, from globally-top institution) under Jupiter AD in Mercury MD = Saraswati + Jupiter converge in education-signal domain. Tepper/CMU = Christian-adjacent academic prestige aligning with native's "succeeds in Christian institutions" behavioral pattern (doc §8).
  notes: Exact timing needs confirmation in v1.1 — native's dictation was "Twenty twenty-three June" but the exact start/completion dates of the Exec MBA program may differ (e.g., admit year vs. completion year).
```

```yaml
EVT.2023.07.XX.01:
  date: 2023-07-XX
  date_confidence: month-exact
  category: career
  subcategory: entrepreneurship_founded
  description: Founded Marsys Group (July 2023). Spans mining, AI, technology, and exports (notably with Russia). Strategic focus: system building, automation, strategic patience.
  magnitude: life-altering
  valence: positive
  native_reflection: "Founded Marcy's in July 2023."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.022
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Virgo / Virgo
    chara_id: DSH.C.072
    sade_sati_phase: TRS.SS.C2.P4 (Peak Aquarius)
    transits_of_note: ["Saturn transit Aquarius = 11H from Lagna", "Jupiter transit Aries = 1H from Lagna"]
    eclipses_within_6mo: ["Solar Annular-Total+Central Aries -85d", "Lunar Penumbral Libra -70d", "Solar Annular+Central Virgo +91d", "Lunar Partial Aries +105d"]
    retrograde_activity: ["Saturn retro in Aquarius"]
    ashtakavarga_SAV_transit_sign: "Sat=24, Jup=29, Sun=28, Moon=28 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.08 (Lakshmi Yoga — dharma-wealth foundation), CVG.02 (Jupiter 9L dharma-wealth chain activating in Jupiter AD), SIG.09 (Mercury MD = operational spine), SIG.14 (Sun 10H + AL = visible authority), RPT.DSH.01 (Triple-Dasha Engine: Mercury MD — Saturn AD window anticipated planting → compounding)]
    signals_that_missed: []
    retrodictive_reasoning: Jupiter 9L AD in Mercury MD, both MD/AD lords are yoga-members (Mercury = Saraswati, Jupiter = Lakshmi). Founding a company that combines mining (earth/Rahu/Saturn), AI/technology (Mercury), exports (3H/9H movement-across-boundaries, Jupiter) = chart's own signatures in material form. Sade Sati Peak concurrent = right timing for long-gestation architecture (Saturn-authorization of serious ventures).
  notes: Marsys is the chart's primary "Phase 6 manifestation" — see CVG.01 (Mercury operational dominance) + CVG.02 (Jupiter 9L dharma-wealth) as the yoga stack being operationalized.
```

```yaml
EVT.2024.02.16.01:
  date: 2024-02-16
  date_confidence: exact
  category: career
  subcategory: business_milestone_major
  description: Launched Kotadwara (riverbed sand) mining operation at Bhanti on 16 February 2024. Major concrete step in Marsys Group's mining vertical.
  magnitude: major
  valence: positive
  native_reflection: "Starting the Kotadwara [Kotadwara] sand mines in Bhanti in February 16, 2024 was a big event."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Jupiter
    vimshottari_id: DSH.V.022
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Libra / Scorpio (just started Feb 5, 2024)
    chara_id: DSH.C.073
    sade_sati_phase: TRS.SS.C2.P4 (Peak Aquarius)
    transits_of_note: ["Saturn transit Aquarius = 11H from Lagna", "Jupiter transit Aries = 1H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Virgo -124d", "Lunar Partial Aries -110d", "Lunar Penumbral Virgo +38d", "Solar Total+Central Pisces +52d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=24, Jup=29, Sun=24, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.01 (Saturn exalted 7H Libra — Chara Libra MD activation = Saturn-exalted signature activated as TIME-lord), SIG.15 (Mars-Saturn 7H Libra conjunction), SIG.10 (Rahu 2H wealth via unconventional means — sand mining = earth extraction, Rahu's classical domain), CVG.08 (Aries-Libra axis triple-aspect includes Muntha 2026-27 already activated window)]
    signals_that_missed: []
    retrodictive_reasoning: STRONG MATCH. Chara MD just shifted to LIBRA (the sign hosting Saturn-exalted Mars-Saturn Mahapurusha Yoga — SIG.15). Chara Libra MD = the chart's 7H-authority-through-tension signature becomes TIME-lord. Simultaneously Mercury MD-Jupiter AD provides dharma-wealth Lakshmi stack. Sand mining = Rahu earth-extraction (SIG.10) + Saturn-labor-structured (SIG.01). Triple-convergence.
  notes: Arguably the single most "chart-coherent" business launch date in the log — Libra Chara MD activation + Mercury-Jupiter Lakshmi AD + Saturn Sade Sati Peak giving authority-seal.
```

```yaml
EVT.2025.05.XX.01:
  date: 2025-05-XX
  date_confidence: month-exact
  category: loss
  subcategory: financial_deception
  description: Major deception / scam event (May 2025). Native was deceived / defrauded in a significant matter. Details not further elaborated.
  magnitude: major
  valence: negative
  native_reflection: "One of the big scams that I got into, deceived, flawed happened last year in May 2025."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Saturn
    vimshottari_id: DSH.V.023
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Libra / Gemini
    chara_id: DSH.C.080
    sade_sati_phase: TRS.SS.C2.P5 (Cycle 2 Setting, Saturn in Pisces, 2025-03-30 to 2027-06-02)
    transits_of_note: ["Saturn transit Pisces = 12H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -61d", "Solar Partial+Non-Central Pisces -46d", "Lunar Total Aquarius +115d", "Solar Partial+Non-Central Virgo +129d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=28, Sun=29, Moon=29 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [CTR.01 (Saturn Shadbala #2 strong vs Shuddha Pinda #7 LAST — "dramatic not compound": a big-visible-event without compounding gain — scam fits), SIG.13 (Sade Sati active — life-pressure phase, vulnerability increased)]
    signals_that_missed: [Ketu is the classical deception/theft karaka. Ketu in 5H Leo natally (intellect-house) could be activated via transit or secondary dasha not examined in v6.0. v1.2.1 does not have a specific deception/fraud signal — RPT.LFE.01 in v2.0 should add this pattern.]
    retrodictive_reasoning: Mercury-Saturn AD is the AD RPT.DSH.01 identifies as critical. Partial match via CTR.01 (Saturn's "dramatic-not-compound" nature manifesting as a visible-scam-event). Full retrodictive match awaits v2.0 Pattern Library for deception signatures.
  notes: Details of deception not further elaborated per native's comfort. May be related to business partner / contract counterparty.
```

```yaml
EVT.2025.07.XX.01:
  date: 2025-07-XX
  date_confidence: month-exact
  category: finance
  subcategory: business_milestone_windfall
  description: First major Marsys business contract (Marsys Technology — July 2025). Described by native as "big one." Windfall-class revenue event; first concrete large-scale win for the business.
  magnitude: major
  valence: positive
  native_reflection: "First major contract with Marcy is July 2025. The Marcy's technology contract was a big one."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Saturn
    vimshottari_id: DSH.V.023
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Libra / Cancer
    chara_id: DSH.C.081
    sade_sati_phase: TRS.SS.C2.P5 (Cycle 2 Setting)
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Pisces = 12H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -122d", "Solar Partial+Non-Central Pisces -107d", "Lunar Total Aquarius +54d", "Solar Partial+Non-Central Virgo +68d"]
    retrograde_activity: ["Saturn retro in Pisces"]
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=28, Sun=28, Moon=24 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [SIG.01 (Saturn exalted 7H = authority-delivery via AD), SIG.09 (Mercury MD Yogi-Vargottama = operational spine peaks), CVG.01 (Mercury operational dominance), CVG.05 (Saturn 7H exalted + Shadbala-strong + Mahapurusha + AD + Yogini overlay), RPT.DSH.01 (the Triple-Dasha Engine explicitly anticipates this window as planting → compounding)]
    signals_that_missed: []
    retrodictive_reasoning: STRONG MATCH. RPT.DSH.01 in Deep Analysis v1.2.1 specifically names Mercury-Saturn AD (2024-2027) as "planting → compounding" window. Concrete evidence of anticipated pattern: first major contract fires in Saturn AD's 7th month. Mercury MD yogi + Saturn AD authority-exalted = partner-platform delivery via structured authority. Marsys Technology as sector = Mercury (analytics/tech).
  notes: Material validation of RPT.DSH.01 prediction. This single event does more to calibrate the chart's forecasting capacity than any other post-2023 event.
```

```yaml
EVT.2025.XX.XX.02:
  date: 2025
  date_confidence: year-approx (native said "2025 or 2026"; logging as 2025)
  category: health
  subcategory: chronic_resolution
  description: Chronic sleep disorder (onset EVT.2007.XX.XX.03, ~18 years) resolved via Lemborexant (brand name: Dayvigo), discovered through an astrology consultation. First medication to work without debilitating drowsiness side effects. Native had tried half a dozen doctors and multiple drugs across India and the US without success.
  magnitude: significant
  valence: positive
  native_reflection: "I found the solution to my sleeping disorder in 2025 when I was consulting astrology and the astrological pharmaceutical remedy was Dayvigo drug, which is the generic name Lemborexant. I pop a pill and know without the negative impacts of drowsiness of the other drugs."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2025-06-01
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Saturn (2024-12-09 to 2027-08-19)
      pratyantar_dasha: Mercury (2025-05-13 to 2025-09-30)
    yogini:
      maha_dasha: Bhadrika/Mercury (2021-12-24 to 2026-12-24)
      antar_dasha: Sankata/Rahu (2024-06-24 to 2025-08-04)
    key_transits:
      saturn_sign: Pisces
      jupiter_sign: Gemini
      rahu_sign: Aquarius
      sade_sati_active: true
  retrodictive_match: pending
  notes: Onset — EVT.2007.XX.XX.03.

EVT.2025.XX.XX.01:
  date: 2025-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: devotional_shift
  description: Spiritual shift toward Lord Vishnu / Lord Venkateshwara Balaji of Tirupati. Occurred "naturally" per doc; continues alongside long-term Maa Ugratara (Tantric Shakti) and Mahadev (Shiva) devotions.
  magnitude: significant
  valence: positive
  native_reflection: "Started naturally gravitating towards Lord Vishnu and currently praying to Lord Venkateshwara Balaji of Tirupati."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Saturn
    vimshottari_id: DSH.V.023
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Libra / (variable by month)
    chara_id: DSH.C.07X-08X range
    sade_sati_phase: TRS.SS.C2.P5 (Cycle 2 Setting, Saturn in Pisces)
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Pisces = 12H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Lunar Total Leo -92d", "Solar Partial+Non-Central Pisces -77d", "Lunar Total Aquarius +84d", "Solar Partial+Non-Central Virgo +98d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=28, Sun=28, Moon=32 (transit signs)"
  retrodictive_match:
    predicted_by_chart: yes
    signals_that_matched: [CTR.02 (Dharma Devata classical (Venkateswara) vs operational (Jagannath) tension — EXACTLY PREDICTS THIS SHIFT — native gravitating TOWARD Venkateswara indicates the "classical" dharma-devata pull is activating)]
    signals_that_missed: []
    retrodictive_reasoning: STRONGEST retrodictive match of any 2025 event. CTR.02 in v1.2.1 Deep Analysis explicitly names the native's dual devata tension: classical-prescription = Venkateswara (Vishnu) vs operational-habituation = Jagannath-family. This 2025 shift is CTR.02 resolving in real-time. Deep Analysis v1.2.1 essentially predicted this gravitation before the native reported it was occurring.
  notes: Single most on-the-nose retrodictive match in the entire v1.0 log. This alone validates the v1.2.1 Deep Analysis's operational accuracy on deep-psychological signals.
```

```yaml
EVT.2026.01.XX.01:
  date: 2026-01
  date_confidence: month-approx (native said "January to February 2026")
  category: other
  subcategory: psychological_shift
  description: Between January and February 2026, native experienced a marked and sustained shift to focused, one-pointed attention directed entirely at business. Long-standing distractions (relational, psychological, otherwise) described as "wiped out." Native characterises this as an entirely new operational mode — chronic distraction replaced by sustained focus.
  magnitude: significant
  valence: positive
  native_reflection: "Between January to February 2026, I found an enormous amount of focus and one-pointed approach, where a lot of things that have distracted me for most part of my life have been wiped out and I'm completely focusing on business."
  chart_state_at_event:
    status: computed_proxy_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2026-01-15
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Saturn (2024-12-09 to 2027-08-19)
      pratyantar_dasha: Venus (2025-11-26 to 2026-05-09)
    yogini:
      maha_dasha: Bhadrika/Mercury (2021-12-24 to 2026-12-24)
      antar_dasha: Dhanya/Jupiter (2026-01-03 to 2026-06-04)
    key_transits:
      saturn_sign: Pisces
      jupiter_sign: Gemini
      rahu_sign: Aquarius
      sade_sati_active: true
  retrodictive_match: pending

EVT.2026.03.20.01:
  date: 2026-03-20
  date_confidence: exact
  category: career
  subcategory: business_project_closed
  description: Marsys Technology (IT company co-founded with a MasterCard executive) wrapped up its primary project on 20 March 2026 with "enormous profits." Revenue generated steadily from 2023 through 2026, significantly supporting the native and Marsys Group through the difficult post-US-return period. Project completion ends the revenue stream; profits accumulated represent a meaningful financial buffer.
  magnitude: significant
  valence: mixed
  native_reflection: "The project got wrapped up on March 20, 2026, with enormous amount of profits. Unfortunately it got wrapped up so we won't be able to make money out of it, but it's significantly helped us during the difficult times with the money that we made out of it."
  chart_state_at_event:
    status: computed_exact_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2026-03-20
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Saturn (2024-12-09 to 2027-08-19)
      pratyantar_dasha: Venus (2025-11-26 to 2026-05-09)
    yogini:
      maha_dasha: Bhadrika/Mercury (2021-12-24 to 2026-12-24)
      antar_dasha: Dhanya/Jupiter (2026-01-03 to 2026-06-04)
    key_transits:
      saturn_sign: Pisces
      jupiter_sign: Gemini
      rahu_sign: Aquarius
      sade_sati_active: true
  retrodictive_match: pending
  notes: Contract start — EVT.2025.07.XX.01.

EVT.2026.04.08.01:
  date: 2026-04-08
  date_confidence: exact
  category: career
  subcategory: business_milestone_clearance
  description: Public hearing for the second sand quarry (see EVT.2021.XX.XX.03) successfully closed on 8 April 2026, clearing the primary regulatory obstacle after ~4–5 years. Quarry expected to become operational by late October 2026.
  magnitude: significant
  valence: positive
  native_reflection: "Eventually, on April 8, 2026, we closed the public hearing for that sand quarry and it should be operational in late October 2026."
  chart_state_at_event:
    status: computed_exact_date
    computation_date: 2026-05-01
    computation_session: M4-A-T1-SWISS-EPHEMERIS
    proxy_date_used: 2026-04-08
    vimshottari:
      maha_dasha: Mercury (2010-08-18 to 2027-08-19)
      antar_dasha: Saturn (2024-12-09 to 2027-08-19)
      pratyantar_dasha: Venus (2025-11-26 to 2026-05-09)
    yogini:
      maha_dasha: Bhadrika/Mercury (2021-12-24 to 2026-12-24)
      antar_dasha: Dhanya/Jupiter (2026-01-03 to 2026-06-04)
    key_transits:
      saturn_sign: Pisces
      jupiter_sign: Gemini
      rahu_sign: Aquarius
      sade_sati_active: true
  retrodictive_match: pending
  notes: Pre-history — EVT.2021.XX.XX.03.

EVT.CURRENT.01:
  date: 2026-04-17 (status as of this log version)
  date_confidence: exact
  category: relationship
  subcategory: marital_status_current
  description: Separated from wife (R#1, married Dec 11, 2013). Stable arrangement. Currently improving per native's own characterization.
  magnitude: significant
  valence: mixed
  native_reflection: "We are still separated. But things are looking up currently. In a stable arrangement."
  chart_state_at_event:
    vimshottari_md: Mercury
    vimshottari_ad: Saturn
    vimshottari_id: DSH.V.023
    yogini_md: Bhadrika / Mercury
    yogini_id: DSH.Y.010
    chara_md_ad: Libra / Libra (Dec 5, 2025 - Feb 5, 2026) → Scorpio (from Feb 5, 2026)
    chara_id: DSH.C.084 → DSH.C.085+
    sade_sati_phase: TRS.SS.C2.P5 (Cycle 2 Setting, Pisces)
    transits_of_note: ["Rahu transit on natal Moon (Aquarius)", "Saturn transit Pisces = 12H from Lagna", "Jupiter transit Gemini = 3H from Lagna"]
    eclipses_within_6mo: ["Solar Annular+Central Aquarius -58d", "Lunar Total Leo -44d", "Solar Total+Central Cancer +117d", "Lunar Partial Aquarius +133d"]
    retrograde_activity: []
    ashtakavarga_SAV_transit_sign: "Sat=27, Jup=28, Sun=29, Moon=27 (transit signs)"
  retrodictive_match:
    predicted_by_chart: partial
    signals_that_matched: [SIG.01 (Saturn exalted 7H — marriage as authority-through-tension including the possibility of formal-separation-as-stabilization), CTR.01 (Saturn Shadbala-strong vs Pinda-weak = stable-but-non-compounding), CVG.05 (Saturn 7H AD peak)]
    signals_that_missed: [Marital trajectory through Saturn AD is not explicitly forecasted in v1.2.1 — this is a Relationships Domain Report gap (to be built in Phase 4 Session 28).]
  notes: Ongoing state. To be updated with trajectory as v1.1+ evolves.
```

---

## §4 — CHRONIC PATTERNS AND UNDATED TRAITS

These are not dated point-events but recurring patterns or constitutional traits. They belong at L1 as factual descriptions; their astrological causation is computed at L2.

```yaml
PATTERN.STAMMER.01:
  trait: Stammering (speech disfluency)
  onset: childhood (specific date unknown)
  trajectory: Improved through adolescence and adulthood; recently resurfaced (2024-2026 era)
  native_reflection: "Experienced stammering in childhood, which improved but has recently resurfaced."
  likely_astrological_basis: Mercury MD peak stabilized speech; Mercury MD-Saturn AD (from Dec 2024) may be producing the resurfacing via Saturn-pressure-on-Mercury-significations.
```

```yaml
PATTERN.PHYSIQUE.01:
  trait: Height 6'3", lean-muscular build in peak (2012-2013), currently good/well-maintained at 42
  onset: peak physique 2012-2013 (overlaps XIMB period)
  native_reflection: "Previously possessed a very lean, muscular body and gained some modeling experience. Currently the physique has evolved from that peak muscular phase, it remains good and well-maintained."
  likely_astrological_basis: Aries Lagna (Mars dominance) + Mercury MD peak during 2012-2013 = physical peak. Sade Sati Cycle 2 (2020+) adds weight/slowing to typical physique.
```

```yaml
PATTERN.SPORTS_LUCK.01:
  trait: Sports participation directly correlates with better luck and prosperity
  native_reflection: "Physically active by nature; sports participation directly correlates with better luck and prosperity." / "Luck, productivity, and social magnetism peak during active sports phases."
  likely_astrological_basis: Aries Lagna = Mars-ruled; Mars-engagement (sports, physical activity) = Lagna-lord activation, which strengthens overall chart delivery. Retrodictive pattern: basketball during 2012-2013 peak (§5.2) aligns with Mercury MD + Mars-engaged-via-sports.
```

```yaml
PATTERN.SLEEP_IRREGULARITY.01:
  trait: Sleep irregularities; undisciplined sleep impacts schedule and productivity; night hours boost creativity
  native_reflection: "Suffers from sleep irregularities; lack of discipline in sleep impacts schedule and productivity." / "Night hours boost creativity and work output, though they disrupt health and schedule."
  likely_astrological_basis: Moon AK Chalit-12 (SIG.05 + CVG.03) — Moon-in-12 is classical insomnia/night-mind signature. Foreign-delivery via-Moon-Chalit-12 also means mind operates in "foreign hours" (night).
```

```yaml
PATTERN.HEADACHES.01:
  trait: Severe headaches since ~1995; screen-time as trigger
  onset: circa 1995 (captured as EVT.1995.XX.XX.01 — the onset event; pattern is the persistence)
  native_reflection: "Suffered from severe headaches since around 1995, a major part of early life."
  likely_astrological_basis: Aries Lagna (head/brain), Sun in 10H (head/prominence) with Mars-Saturn aspect from 7H. Adolescent Sade Sati Cycle 1 Peak (Saturn transiting Aquarius on natal Moon) = headache-onset-catalyst.
```

```yaml
PATTERN.COMPUTER_APTITUDE.01:
  trait: Exceptional computer/programming aptitude from teenage onward; recognized early; returned to it recently
  native_reflection: "Was a 'successful geek' and extremely proficient with computers at a young age, achieving recognition." / "Back to it now."
  likely_astrological_basis: SIG.09 (Mercury Vargottama + Yogi + MD) = Mercury operational spine. Mercury = technology, programming, pattern-processing. Return-to-it post-2023 aligns with Marsys Technology vertical in Marsys Group.
```

---

## §5 — INNER TURNING-POINT PERIODS (Native's Self-Characterization)

```yaml
PERIOD.2007:
  dates: 2007 (calendar year)
  characterization: "Engineering completion + first job. Nothing heavier than a transition marker."
  native_reflection: "I don't think [2007] was in any way significant, only thing was I completed my BTEC, my engineering and started my first job."
  vimshottari: Saturn-Rahu AD (most of year) → Saturn-Jupiter AD (from Feb 9, 2008)
  yogini: Sankata/Rahu
  dominant_events_in_period: [EVT.2007.06.XX.01 (knee surgery), EVT.2007.06.XX.02 (engineering), EVT.2007.06.10.01 (Cognizant join)]
  retrodictive_note: Native's low valence for this period is consistent with Saturn-Rahu AD being a labor-grind AD rather than a peak period. The events happened but weren't accompanied by peak emotional/experiential intensity.
```

```yaml
PERIOD.2012_2013:
  dates: 2012 through 2013 (calendar years)
  characterization: "Best period of my life. Basketball, opposite sex, partying, ace in everything."
  native_reflection: "2012-13 was the best period of my life. I played basketball, enjoyed my time with the opposite sex. I had a lot of partying so it was an ace in everything. I can't forget that period."
  vimshottari: Mercury-Mercury AD (peak, through Jan 18, 2013) → Mercury-Ketu AD (Jan 18, 2013 → Jan 15, 2014)
  yogini: Mangala/Moon (through Dec 22, 2012) → Pingala/Sun (Dec 22, 2012 → Dec 22, 2014)
  dominant_events_in_period: [EVT.2012.09.XX.01 (modeling), EVT.2012.10.XX.01 (R#3 start), EVT.2013.03.XX.01 (XIMB graduation), EVT.2013.05.XX.01 (Mahindra Retail), EVT.2013.12.11.01 (marriage)]
  retrodictive_note: Mercury-Mercury AD is the chart's operational peak for Mercury-spine (Saraswati + Yogi + Vargottama + MD + all on same lord). PATTERN.SPORTS_LUCK.01 fires clearly (basketball). PATTERN.PHYSIQUE.01 peak (modeling at XIMB). Saraswati (SIG.07) = charisma in academic/performance arena. Classical result: MD-AD of same Yogi lord = experiential peak.
```

```yaml
PERIOD.2016:
  dates: 2016 (calendar year)
  characterization: "A bit stressful. Mahindra Retail crashed. Looking for a job."
  native_reflection: "2016 was a bit stressful when I was looking for a job outside Mahindra Retail as the company had crashed and that's when I decided to switch over to Tech Mahindra."
  vimshottari: Mercury-Venus AD (through Nov 15, 2016) → Mercury-Sun AD (from Nov 15, 2016)
  yogini: Dhanya/Jupiter
  dominant_events_in_period: [EVT.2016.XX.XX.01 (Mahindra Retail crash)]
  retrodictive_note: Venus AD = weakest-Shadbala planet (SIG.12) gets AD spotlight = professional instability. Exit of Venus AD in Nov 2016 + Sun AD start = resolution path (Sun 10H activated for Mar 2017 switch).
```

```yaml
PERIOD.2018_2021:
  dates: 2018 through 2021
  characterization_start: "Mentally traumatic time [2018] — father's death, hospital-running Hyderabad to Bhubaneswar."
  characterization_middle: "2019 to 21 in the US - exciting."
  native_reflection: "I lost my father, so it was a mentally traumatic time running a lot of the hospitals, running from Hyderabad to Neshwar. So but 2019 to 21 was in the US exciting."
  vimshottari: Mercury-Moon AD (late 2017-Feb 2019, peak during father's passing) → Mercury-Mars AD (Feb 2019-Feb 2020, US move) → Mercury-Rahu AD (Feb 2020-Sep 2022, US ongoing)
  yogini: Bhramari/Mars (Dec 22, 2017 → Dec 22, 2021)
  dominant_events_in_period: [EVT.2018.11.28.01 (father passed), EVT.2019.05.XX.01 (US move), EVT.2021.01.XX.01 (panic episode — moved here in v1.1 from 2022)]
  retrodictive_note: Split-valence period. Start = father's death under AK Moon AD (soul-event magnitude). Middle = US-stint under Mars-then-Rahu AD (Mars = initiative/action abroad; Rahu = foreign-amplification). End = Jan 2021 panic episode at Sade Sati Cycle 2 Rising peak (Saturn in Cap 12th from Moon, ~1 year into cycle) + Bhramari/Mars Yogini at maximum intensity. v1.1 correction makes this period coherent: Bhramari/Mars runs through Dec 2021 exactly bounding the "US exciting" phase and containing the panic-episode terminus.
```

```yaml
PERIOD.2022_2024:
  dates: 2022 through 2024
  characterization: "Mix. New relationships, rupture of old, success in professional career, lost US job, moved to India, pivotal — changed from salary to business, driven by turn of events and own decision."
  native_reflection: "22 to 24 was a mix, it was new relationships and rupture of old success in professional career in my job but I lost my job in the US moved to India in fact was a pivotal point where I completely changed my life from salary job to business which I couldn't have done otherwise was primarily driven by turn of events and my own decision."
  vimshottari: Mercury-Rahu AD (through Sep 6, 2022) → Mercury-Jupiter AD (Sep 6, 2022 → Dec 12, 2024) → Mercury-Saturn AD (from Dec 12, 2024)
  yogini: Bhramari/Mars (through Dec 22, 2021) → Bhadrika/Mercury (from Dec 22, 2021)
  dominant_events_in_period: [EVT.2022.01.03.01 (twins), EVT.2022.10.XX.01 (R#3 end), EVT.2023.05.XX.01 (US return + pivot), EVT.2023.06.XX.01 (Tepper), EVT.2023.07.XX.01 (Marsys founded), EVT.2024.02.16.01 (sand mines)]
  retrodictive_note: MOST RICHLY MATCHED period. Jupiter AD = dharma-pivot (CTR.03 Uccha-weak = forced-pivot-via-loss). Sade Sati Peak Aquarius = life-direction compression. Bhadrika/Mercury Yogini = analytical-rebuild. Chara transitions from Virgo → Libra = analysis-house → partnership-house = pivot from salaried-analyst to business-partner-entrepreneur. Five-way convergence = this is the chart's most fated 3-year window for the 40s decade.
```

---

## §6 — GAP REGISTER (Underspecified or Missing)

Items referenced in source material but not yet precisely dated or fully characterized. Session 3+ targets for v1.1 expansion.

```yaml
GAP.TEPPER.DATES.01:
  issue: Tepper School CMU Executive MBA — exact start date and completion date
  current_data: Native said "Twenty twenty-three June" — interpreted as June 2023 completion, but this is ambiguous
  resolution_path: Ask native for program admit date and completion date in next session

GAP.US_JOB_LOSS.01:
  issue: Native mentioned losing US job before May 2023 India return — exact date not captured
  resolution_path: Ask for termination date (month/year) in next session

GAP.SADE_SATI_CYCLE_1.01:
  issue: v6.0 §21 contains only Cycle 2 Sade Sati (2020+). Cycle 1 (~1993-2000, adolescence) is not tabulated.
  resolution_path: v7.0 Facts Layer upgrade must add Cycle 1 Sade Sati table with Saturn-in-Cap, -Aq, -Pisces transit dates from 1991-2001 range. Jagannatha Hora can export this.

GAP.TRANSITS_AT_EVENTS.01:
  issue: Transits of note, eclipses within 6 months, retrograde activity, Ashtakavarga SAV bindu at each event — all marked `unexamined` in v1.0/v1.1
  resolution: RESOLVED in v1.2. Populated via Swiss Ephemeris self-compute (Session 4). Full per-event detail in `EVENT_CHART_STATES_v1_0.md`.

GAP.RELATIONSHIP_3_END.01:
  issue: R#3 end date ~Oct 2022 is estimated from "10 years" duration + Oct 2012 start
  resolution_path: Confirm exact end month in next session

GAP.IIT_OUTCOME.01:
  issue: Whether native sat IIT JEE exam and its outcome — implicit "did not crack" from doc's "A1-tier not secured"
  resolution_path: Confirm in next session — did he attempt JEE? What rank/outcome?

GAP.INFIDELITY_TEMPORAL_PRECISION.01:
  issue: Native confirmed R#2 + R#3 capture physical infidelity timespans, but specific episodes within those spans not enumerated
  resolution_path: Not essential — overall period-capture is sufficient for retrodictive work. Declining further probing per §9.4 sensitivity protocol.

GAP.HEALTH_EPISODES.01:
  issue: Beyond the June 2007 knee surgery and Jan 2022 jitters episode, any other health events?
  resolution_path: Re-check in next session

GAP.FINANCIAL_LOSSES.01:
  issue: Besides the May 2025 scam, any other significant financial losses (investments gone wrong, debt events)?
  resolution_path: Re-check in next session

GAP.TRAVEL_MISC.01:
  issue: Beyond Dec 2010 Thailand and 2019-2023 US stint, any other foreign travel?
  resolution_path: Re-check in next session (possibly multiple Russia-related business trips for Marsys exports)

GAP.R2_MONTH.01:
  issue: R#2 start month in 2004 — native said "Jan 2004" in v1.1 correction but didn't confirm day
  resolution_path: Not essential for retrodictive work (month-precision sufficient)

GAP.FATHER_KIDNEY_MONTH.01:
  issue: Father's kidney disease onset month in 2013 — native stated year (2013) in v1.1 correction; month not specified
  resolution_path: Confirm month in next session. Determines whether Vimshottari AD was Mercury-Mercury (before Jan 18, 2013) or Mercury-Ketu (after). Ketu AD onset would be classically coherent for a father-illness-onset (Ketu = unexpected health revelation).

GAP.US_JOB_LOSS_PRECISE.01:
  issue: Exact US job-loss date (before May 2023 return) still not captured
  resolution_path: Ask next session

GAP.GRANDMOTHER.01:
  issue: Doc mentions close bond with paternal grandparents; grandfather's passing captured. Paternal grandmother's life events (still alive? passed? when?) not specified
  resolution_path: Re-check in next session

GAP.MOTHER_STATUS.01:
  issue: Doc mentions mother in family section but no events related to mother specifically captured
  resolution_path: Re-check in next session — any significant mother-related events?

GAP.BROTHER_STATUS.01:
  issue: "Younger brother is a lifelong pillar" — but no specific dated events involving brother (career peaks, marriage, etc.)
  resolution_path: Re-check in next session
```

---

## §7 — RETRODICTIVE MATCH AGGREGATE SUMMARY

### §7.1 — Match distribution across 36 events (post-v1.1)

| Match level | Count | Percentage |
|---|---|---|
| `yes` (strong match across multiple signals) | 22 | 61% |
| `partial` (some signals match, other aspects unexplained or missing signals) | 14 | 39% |
| `no` (event unexplained by current signals) | 0 | 0% |
| `unexamined` | 0 | 0% |

**v1.1 impact on match quality**: 4 date corrections strengthened retrodictive alignment:
- Jitters 2022 → 2021: moved from Bhadrika/Mercury to Bhramari/Mars Yogini — Mars-Yogini fits panic-anxiety more sharply than Mercury-Yogini did (PARTIAL → YES upgrade).
- R#2 2008 → 2004: moved from Saturn-Rahu AD to Saturn-Moon AD (AK AD) — AK AD at non-primary romance onset is a more coherent classical signature.
- Father's disease 2000 → 2013: timing shifts from Saturn MD to Mercury MD; CTR.03 Jupiter-weakness still foundational but now requires Jagannatha Hora transit lookup for full retrodictive closure (partial pending v1.2).

### §7.2 — Top-10 strongest retrodictive matches (full signal convergence)

| Event | Signals converged |
|---|---|
| EVT.2025.XX.XX.01 Vishnu/Venkateshwara shift | CTR.02 direct prediction match |
| EVT.2023.07.XX.01 Marsys founded | SIG.08 + CVG.02 + SIG.09 + SIG.14 + RPT.DSH.01 |
| EVT.2025.07.XX.01 First Marsys contract | SIG.01 + SIG.09 + CVG.01 + CVG.05 + RPT.DSH.01 |
| EVT.2024.02.16.01 Sand mine launch | SIG.01 + SIG.15 + SIG.10 + CVG.08 + Chara Libra MD shift |
| EVT.2023.05.XX.01 US→India return + pivot | CTR.03 + CVG.02 + SIG.13 + CVG.08 |
| EVT.2018.11.28.01 Father passed | CTR.03 + SIG.04 + SIG.05 + CVG.02 + transit-9H |
| EVT.2022.01.03.01 Twins born | SIG.10 Rahu AD doubling + SIG.09 + Jupiter transit |
| EVT.2019.05.XX.01 US move | CVG.03 + SIG.05 + SIG.06 + SIG.15 |
| EVT.2013.12.11.01 Marriage | SIG.01 + SIG.15 + CVG.08 + CTR.01 |
| EVT.2009.06.XX.01 Grandfather passed | CVG.02 + CTR.03 direct Jupiter-9L AD match |

### §7.3 — Signals validated by multiple events

| Signal | Events it retrodictively matched |
|---|---|
| **CTR.03** (Jupiter Uccha-weak) | Grandfather death 2009, Father death 2018, US pivot 2023, 2016 Mahindra crash, Father's kidney disease onset 2013 (v1.1 corrected) |
| **CVG.02** (Jupiter 9L dharma-wealth) | Grandfather death 2009, US pivot 2023, Marsys founded 2023, Father's illness onset 2013 (v1.1 corrected) |
| **SIG.09** (Mercury Vargottama + Yogi + MD) | XIMB MBA 2011, Thailand 2010, engineering 2007, 2012-13 peak, Marsys 2023, Marsys contract 2025, Tepper 2023 |
| **SIG.01** (Saturn exalted 7H) | Marriage 2013, Sand mines 2024, Marsys contract 2025, Knee surgery 2007 (via SIG.15 conjunction), Current separation |
| **CVG.03** (Moon AK Chalit-12 foreign) | Thailand 2010, US move 2019 |
| **SIG.10** (Rahu 2H) | Jitters 2022, Twins 2022, Sand mines 2024, Cognizant first-job |
| **SIG.13** (Sade Sati) | Jitters 2022, US pivot 2023, Marsys contract 2025 + EVT.1995.XX.XX.01 via Cycle 1 inference |
| **CTR.01** (Saturn Shadbala vs Pinda paradox) | Marriage 2013, May 2025 scam, Current separation state |
| **CTR.02** (Dharma Devata Venkateswara vs Jagannath) | Vishnu shift 2025 (direct prediction) |

### §7.4 — Signal gaps flagged for v2.0 Deep Analysis expansion

These retrodictive events showed patterns not yet captured as formal signals in v1.2.1. RPT.LFE.01 Pattern Library in Deep Analysis v2.0 should encode them:

- **Deception/Fraud Signal** — May 2025 scam has no specific signal; Ketu-activation in 5H (intellect) via transit or secondary dasha likely
- **Infidelity / Concurrent-Relationship Signal** — R#2 and R#3 overlap with primary relationship; Venus-weakness + Rahu-2H convergence pattern
- **Kidney-Venus-9H-Chain Signal** — Father's kidney disease onset 2000 suggests a Venus-weak + 9H-Father + kidney-body-signature chain
- **Christian-Institution-Success Pattern** — Native succeeds disproportionately in Christian-institution contexts (Saint Joseph's, XIMB, CMU Tepper); this is a tangible empirical pattern not yet computed

### §7.5 — Confidence self-assessment

v1.0 carries a `confidence: 0.74` self-assessment. This reflects:
- **High confidence** (+) on Vimshottari/Yogini/Chara tags: authoritatively sourced from v6.0 tables
- **High confidence** (+) on 21 "yes" retrodictive matches with multi-signal convergence
- **Moderate confidence** (±) on the 15 "partial" matches — partial match is the honest assessment rather than forcing a "yes"
- **Lower confidence** (-) on chart_state transits/eclipses/retrograde/Ashtakavarga — all marked `unexamined` pending Jagannatha Hora export in v1.1
- **Lower confidence** (-) on Cycle 1 Sade Sati inference (not in v6.0)

v1.1 target confidence after Jagannatha Hora export: 0.88
v2.0 target confidence after Pattern Library build: 0.92+

---

## §8 — CHANGELOG

```yaml
v1.0 (2026-04-17, superseded same-session by v1.1):
  - Initial version built from native's "Consolidated Life Facts.docx" + Session 2 elicitation responses
  - 38 point events logged with Vimshottari/Yogini/Chara tagging from v6.0 §5.1/§5.2/§5.3
  - Cycle 2 Sade Sati tagging from v6.0 §21
  - Retrodictive match against v1.2.1 Deep Analysis SIG.*/CVG.*/CTR.* library
  - 6 chronic patterns (§4), 5 period summaries (§5), 13-item gap register (§6)
  - Confidence self-assessment: 0.74
  - Status: superseded by v1.1

v1.1 (2026-04-17, same session, native-supplied corrections):
  - Father's kidney disease onset corrected: 2000 → 2013 (event moved from Era 3 to Era 5; new Vimshottari/Yogini/Chara tagging; note: 5-year illness arc, not 18-year)
  - R#2 start corrected: Jan 2008 → Jan 2004 (event moved from Era 4 to beginning of Era 4; pre-engineering-completion; Saturn-Moon AD + Sankata Yogini + Gemini Chara; entirely pre-marriage)
  - XIMB split into 2 events: admission Jan 2011 (EVT.2011.01.XX.01) + enrollment June 2011 (EVT.2011.06.XX.01)
  - Panic/jitters episode corrected: Jan 2022 → Jan 2021 (now under Bhramari/Mars Yogini which strengthens retrodictive fit; no longer mis-coded as pre-twins-birth)
  - Sand mine name corrected: Kotitampara → Kotadwara
  - Total event count: 38 → 36 point events (v1.0 count included a potential off-by-one error; v1.1 is the authoritative count)
  - Confidence self-assessment: 0.74 → 0.77
  - Gap register expanded: added GAP.R2_MONTH.01, GAP.FATHER_KIDNEY_MONTH.01, GAP.US_JOB_LOSS_PRECISE.01
  - Status: CLOSED (Session 2 output final)

v1.2 (2026-04-17, Session 4 — paradigm shift from native-runs-JH to Claude-self-computes-ephemeris):
  - Native challenged premise: "Why do you want me to run this on JH? You can pull ephemeris data from open websites yourself."
  - Swiss Ephemeris (pyswisseph 2.10.03) installed locally; natal chart matched v6.0 to arc-minute precision (confirming setup)
  - Generated authoritative facts files: EPHEMERIS_MONTHLY_1900_2100.csv (21,708 rows), ECLIPSES_1900_2100.csv (913 eclipses), RETROGRADES_1900_2100.csv (1,231 station pairs), SADE_SATI_CYCLES_ALL.md (full lifetime — Cycles 1-4 with Kantaka Shani periods), EVENT_CHART_STATES_v1_0.md (all 36 events)
  - Populated chart_state_at_event fields at all 36 events:
    * transits_of_note: Top 3-5 most-salient transit positions relative to Lagna and Moon
    * eclipses_within_6mo: Up to 4 eclipses within ±6-month window per event
    * retrograde_activity: Live retrograde state of Mercury-Venus-Mars-Jupiter-Saturn at event
    * ashtakavarga_SAV_transit_sign: SAV bindus for key planets at their transit signs (v6.0 §7.2 values)
  - Retrodictive signal stack strengthened via new eclipse/transit evidence; most notable on EVT.2018.11.28.01 (father's death) which now shows a dense 5-eclipse-in-6-months window + Saturn transit 9H Sagittarius
  - Confidence self-assessment: 0.77 → 0.89
  - Status: CLOSED (Session 4 output)

# Future version targets:
v1.1 (planned Session 3+):
  - Populate transits_of_note, eclipses_within_6mo, retrograde_activity, ashtakavarga_SAV at each event
  - Add Cycle 1 Sade Sati window (requires v7.0 Facts Layer upgrade)
  - Resolve GAP.* items via targeted elicitation
  - Expand to 75-100 events (per Architecture §D.2 target)
  - Target confidence: 0.88

v2.0 (planned post-Deep-Analysis-v2.0):
  - Cite RPT.LFE.01 Pattern Library signals
  - Include 150+ events
  - Target confidence: 0.92+
```

---

## §9 — PROSPECTIVE PREDICTION SUBSECTION (interim PPL surface)

*Appended 2026-05-01 at M3-W4-D1-VALIDATOR-REDTEAM session per CLAUDE.md §E
concurrent-workstream rule (Prospective Prediction Logging). This subsection
is the interim PPL logging surface until the canonical
`06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` substrate
absorbs the row. Append-only; outcome fields stay `null` until observed.*

```yaml
PRED.M3D.HOLDOUT.001:
  source_artifact: 00_ARCHITECTURE/EVAL/M3_HELD_OUT_SAMPLE_v1_0.md §3
  source_row: "Row 7 — FUTURE.2026-08-15"
  emitted_at: 2026-05-01
  emitted_by_session: M3-W4-D1-VALIDATOR-REDTEAM
  prediction_window:
    start_date: 2026-08-15
    end_date: 2026-08-15
  horizon_days: 106
  confidence: MED
  claim_text: >
    Mercury MD final-year + Mercury-Saturn AD + Bhadrika/Mercury Yogini overlay
    surfaces the convergent "Mercury-rule's terminal consolidation under Sade
    Sati pressure" pattern. The native is expected to register a career-peak
    or wealth-peak event, project completion, or consolidation milestone
    within ±30 days of 2026-08-15.
  falsifier_conditions:
    - "No career-peak signature, no project completion, no consolidation event,
       and no wealth-peak event of significance to the native occurs within
       ±30 days of 2026-08-15."
  related_artifact_ids: [PRED.001, PRED.005]
  outcome: null
  outcome_source: null
  outcome_recorded_at: null
  migrated: true
  migrated_at: 2026-05-02
  migrated_by_session: M4-A-T2-PPL-INFRA
  migration_destination: 06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl

PRED.M3D.HOLDOUT.002:
  source_artifact: 00_ARCHITECTURE/EVAL/M3_HELD_OUT_SAMPLE_v1_0.md §3
  source_row: "Row 8 — FUTURE.2027-09-12"
  emitted_at: 2026-05-01
  emitted_by_session: M3-W4-D1-VALIDATOR-REDTEAM
  prediction_window:
    start_date: 2027-08-19
    end_date: 2027-12-31
  horizon_days: 499
  confidence: MED
  claim_text: >
    The Mercury → Ketu MD transition on 2027-08-19 manifests as a discontinuous
    regime change for the native — a role/relationship/spiritual reorientation
    visible within the four-and-a-half months following the transition. The
    lit-signal collapse (248 → 79 signals) and KP Asc shift to triple-Saturn
    (star + sub + sub-sub) at the close of August / early September 2027
    indicates a structurally rare regime-discontinuity moment.
  falsifier_conditions:
    - "Mercury → Ketu MD regime change manifests as routine continuation
       (no role change, no spiritual reorientation, no relationship recalibration,
       no major life-frame shift) in the three to four months following 2027-08-19."
  related_artifact_ids: [PRED.011, PRED.012, PRED.013, PRED.014]
  outcome: null
  outcome_source: null
  outcome_recorded_at: null
  migrated: true
  migrated_at: 2026-05-02
  migrated_by_session: M4-A-T2-PPL-INFRA
  migration_destination: 06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl
```

*Future predictions emitted in M3 / M4 / M5 / M6 sessions append here in the
same shape until the migration to `06_LEARNING_LAYER/PREDICTION_LEDGER/`
absorbs this subsection. The PRED.M3D.HOLDOUT.NNN id-space is reserved for
held-out sample predictions; other PRED.* id-spaces (PRED.001..014 already
in `prediction_ledger.jsonl`) remain canonical for non-held-out predictions.*

---

**END OF LIFE EVENT LOG v1.0**

*This document is L1 Facts Layer. Interpretation layer references this via `retrodictive_match` fields. Every subsequent L2/L2.5/L3 artifact that cites an event should use its `EVT.*` ID.*
