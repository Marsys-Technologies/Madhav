---
artifact: LEL_CANDIDATES_STAGED
version: 1.0
status: STAGED_FOR_NATIVE_REVIEW
produced_by: W4.6 (GOCHARA-UTKARSA campaign)
produced_at: 2026-08-10
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
native: Abhisek Mohanty
---

# LEL Mining — Staged Candidates for Native Review

## Header Summary

| Field | Value |
|---|---|
| Events currently in lel_train_events.json | 36 (TRAIN split only, event_date <= 2019-12-31) |
| Total events logged in LIFE_EVENT_LOG_v1_2.md | 57 point events + EVT.CURRENT.01 (status event, not scoreable) |
| New candidates staged in this document | 20 |
| Abhinandan event candidates | 0 (no dated Abhinandan events found in corpus) |

**IMPORTANT — Native review required.** This document is a mining output only. Every candidate below is extracted from source files with a verbatim quote. Only the native (Abhisek Mohanty) can attest which entries represent genuine lived events suitable for LEL DB loading. No entries have been inserted into the database. No source files have been modified.

**Train/Test split boundary:** The sealed test split is `event_date >= 2020-01-01`. Events on or after 2020-01-01 are flagged as **TEST split candidates** in a separate section below. Events before 2020-01-01 that are not yet in the DB go to the **TRAIN split** section.

---

## Why These Candidates Exist

`lel_train_events.json` contains 36 events with `event_date <= 2019-12-31` (the TRAIN slice fetched on 2026-07-18). The full `LIFE_EVENT_LOG_v1_2.md` documents 57 point events total. The 21-event gap is split as follows:

- 20 events have `date >= 2020-01-01` and are therefore in the TEST split — they have never been loaded into the cache used by the CRPS scoring harness.
- 1 event (`EVT.CURRENT.01`) is a status/ongoing-state entry explicitly excluded from point-event counting in the LEL frontmatter ("EVT.CURRENT.01 not counted as a point event").

All 36 TRAIN-split events in `lel_train_events.json` appear to correspond to events in the LEL. There are no TRAIN-split LEL events discovered that are missing from the DB.

---

## Section A — TRAIN Split Candidates (event_date < 2020-01-01)

*No new TRAIN split candidates found. All 36 pre-2020 LEL events are already present in lel_train_events.json. The 36 loaded events match the LEL's pre-2020 event count exactly.*

---

## Section B — TEST Split Candidates (event_date >= 2020-01-01)

These 20 events are documented in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` but have NOT been loaded into the LEL DB. They would be placed in the TEST split (scoring reserved for calibration, not training). Native attestation required before any DB insertion.

---

## Candidate: Panic/anxiety episode (January 2021)

| Field | Value |
|---|---|
| date | 2021-01-15 (proxy — native said "Jan 2021"; mid-month proxy used in LEL) |
| category | health |
| description | Health episode with jitters and sweating — panic/anxiety episode in January 2021. Native was in US stint, approximately 1 year before twins' birth. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2021.01.XX.01) |
| source_quote | "Health issue - Jitters, sweating, panic episode in Jan 2021" |
| confidence | high |
| confidence_note | Month-exact precision confirmed by native in Session 2 v1.1 correction (original was Jan 2022, corrected to Jan 2021). |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Tepper/CMU Executive MBA selection by Mahindra (2021)

| Field | Value |
|---|---|
| date | 2021-04-01 (proxy — native said "selected in 2021"; proxy per M4-A-T1-SWISS-EPHEMERIS pass) |
| category | career |
| description | Selected as one of the top employees across the Mahindra Group and sponsored for a 1-year Executive MBA at Tepper School of Business, Carnegie Mellon University. Program ran 2022–2023. Native experienced this as a "deja vu" — CMU had been offered and declined in 2004; 17 years later it arrived as a sponsored award. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2021.XX.XX.02) |
| source_quote | "I was selected as one of the top employees of the Mahindra group and they sponsored me for a one-year executive MBA. It was a deja vu incident for me because the university I really wished to be part of but could not because of issues at that point in time came back to me and fell in my lap." |
| confidence | medium |
| confidence_note | Year-exact; exact month not specified by native. Proxy date (April 2021) used in LEL. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Second sand quarry acquisition attempted (2021–2022)

| Field | Value |
|---|---|
| date | 2021-09-01 (proxy — native said "2021 or 2022"; proxy per M4-A-T1-SWISS-EPHEMERIS pass) |
| category | career |
| description | A second sand quarry was acquired and attempted for operationalisation ~2021–2022 but could not be made operational due to public hearing requirements. Multiple attempts to bypass or resolve the public hearing were unsuccessful over ~4–5 years until April 2026. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2021.XX.XX.03) |
| source_quote | "We had one in 2021 or 2022, we had not made it operational because of a public hearing which was a complicated thing. Lots of things we tried to avoid public hearing, but didn't happen." |
| confidence | medium |
| confidence_note | Year ambiguous (native said "2021 or 2022"). LEL uses 2021 proxy. Scorability may be low due to date uncertainty. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Twin daughters born (3 January 2022)

| Field | Value |
|---|---|
| date | 2022-01-03 |
| category | family |
| description | Twin daughters born on 3 January 2022. Native's only children. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2022.01.03.01) |
| source_quote | "Twin daughters born on 3 January 2022." |
| confidence | high |
| confidence_note | Exact date. Day-level precision confirmed. Highest-confidence event in the TEST cohort. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Serious affair during CMU Tepper Executive MBA (2022)

| Field | Value |
|---|---|
| date | 2022-06-01 (proxy — native said "during the CMU Tepper Executive MBA period 2022–2023"; proxy per M4-A-T1-SWISS-EPHEMERIS pass) |
| category | relationship |
| description | A serious affair during the CMU Tepper Executive MBA period (2022–2023). Distinct from R#3 (ended October 2022). This affair generated significant marital tension and is cited by native as a direct contributing cause of the current marital separation. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2022.XX.XX.02) |
| source_quote | "I had a pretty serious affair at that point in time which resulted in a lot of issues in my marriage and for which I am in a separated state today." |
| confidence | medium |
| confidence_note | Year-approx. Exact month not specified. Sensitive category; native should confirm scorability and comfort before loading. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Relationship #3 ended (~October 2022)

| Field | Value |
|---|---|
| date | 2022-10-15 (proxy — estimated from "10 years" duration from Oct 2012 start) |
| category | relationship |
| description | Relationship #3 ended (approximately October 2022, 10-year duration from start Oct 2012). Coincides with Mercury-Jupiter AD transition (Sep 2022) and start of "2022-2024 mix" inner period. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2022.10.XX.01) |
| source_quote | "Oct 2012 (10 years)" (native's statement about R#3 duration, from which Oct 2022 end is derived) |
| confidence | medium |
| confidence_note | End date inferred from stated duration, not directly confirmed. GAP.RELATIONSHIP_3_END.01 flagged for exact confirmation. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Returned to India from US / career pivot to entrepreneurship (May 2023)

| Field | Value |
|---|---|
| date | 2023-05-15 (proxy — native said "May 2023"; mid-month proxy) |
| category | residential+travel |
| description | Returned to India from United States (May 2023) after 4-year stint. Concurrent with US job loss (exact date unclear). Pivotal transition from salaried corporate employment to entrepreneurship. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2023.05.XX.01) |
| source_quote | "I lost my job in the US moved to India in fact was a pivotal point where I completely changed my life from salary job to business which I couldn't have done otherwise was primarily driven by turn of events and my own decision." |
| confidence | high |
| confidence_note | Month-exact. Cited as "the single most transformative turning point of the adult life per native's own narrative." |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Tepper School of Business Executive MBA completed (June 2023)

| Field | Value |
|---|---|
| date | 2023-06-15 (proxy — native said "June 2023"; mid-month proxy) |
| category | education |
| description | Tepper School of Business (Carnegie Mellon University) Executive MBA completed (June 2023). Sponsored by Tech Mahindra. Recognized as top performer. Closes the 17-year CMU deja vu arc from 2004. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2023.06.XX.01) |
| source_quote | "That was Tepper School... June 2023." |
| confidence | high |
| confidence_note | Month-exact. LEL notes exact start/completion dates may differ (admit year vs. completion year) — native should confirm. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Founded Marsys Group (July 2023)

| Field | Value |
|---|---|
| date | 2023-07-15 (proxy — native said "July 2023"; mid-month proxy) |
| category | career |
| description | Founded Marsys Group (July 2023). Spans mining, AI, technology, and exports (notably with Russia). Strategic focus: system building, automation, strategic patience. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2023.07.XX.01) |
| source_quote | "Founded Marcy's in July 2023." |
| confidence | high |
| confidence_note | Month-exact. Native's own business — directly confirmed. Life-altering magnitude. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Launched Kotadwara sand mining operation at Bhanti (16 February 2024)

| Field | Value |
|---|---|
| date | 2024-02-16 |
| category | career |
| description | Launched Kotadwara (riverbed sand) mining operation at Bhanti on 16 February 2024. Major concrete step in Marsys Group's mining vertical. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2024.02.16.01) |
| source_quote | "Starting the Kotadwara [Kotadwara] sand mines in Bhanti in February 16, 2024 was a big event." |
| confidence | high |
| confidence_note | Exact date. Day-level precision confirmed. Described as "arguably the single most chart-coherent business launch date in the log." |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Spiritual practice intensification — daily abhisheka, yajna, panchang (2024)

| Field | Value |
|---|---|
| date | 2024-07-01 (proxy — native said "for the last two years" as of ~2026; ~2024 onset; mid-year proxy per M5-A-S1) |
| category | spiritual |
| description | From ~2024: daily pouring of water on shivalinga (abhisheka); independent yajna execution (self-conducted without a pandit); systematic panchang study (transit, muhurta, tithi); identification and planning of yajna timings using astrological data. Highest concentration of new spiritual practices in native's life. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2024.XX.XX.01) |
| source_quote | "For the last two years I have been pouring water on the shiveling almost every day... I have been doing enormous amount of yajna. Now I have developed a skill that I do a yajna on my own... I have been following astrological data, looking at the panchang." |
| confidence | medium |
| confidence_note | Year-approx. Onset period approximated from "last two years" statement (as of ~mid-2026). |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Major deception/scam event (May 2025)

| Field | Value |
|---|---|
| date | 2025-05-15 (proxy — native said "last year in May 2025"; mid-month proxy) |
| category | finance |
| description | Major deception / scam event (May 2025). Native was deceived / defrauded in a significant matter. Details not further elaborated. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.05.XX.01) |
| source_quote | "One of the big scams that I got into, deceived, flawed happened last year in May 2025." |
| confidence | high |
| confidence_note | Month-exact. Native's own statement. Sensitivity note: details not elaborated per native's comfort. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Yantra mandala established in bedroom (June 2025)

| Field | Value |
|---|---|
| date | 2025-06-01 (proxy — native said "~1.5–2 years running as of 2026"; approximate onset June 2025; month-proxy per M5-A-S1) |
| category | spiritual |
| description | Native established a personal yantra mandala in his bedroom — a permanent ritual space. Prayers offered almost daily, sometimes more than once. Formalization of private ritual life begun in ~2024. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.06.XX.01) |
| source_quote | "I have my own yantra mandala established in my bedroom, which I offer prayers almost every day, sometimes more than once. There is a daily ritual that I follow." |
| confidence | medium |
| confidence_note | Month-approx; onset inferred from "1.5–2 years running as of 2026" statement. Native should confirm exact month of establishment. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: First major Marsys Technology contract (July 2025)

| Field | Value |
|---|---|
| date | 2025-07-15 (proxy — native said "July 2025"; mid-month proxy) |
| category | finance |
| description | First major Marsys business contract (Marsys Technology — July 2025). Described by native as "big one." Windfall-class revenue event; first concrete large-scale win for the business. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.07.XX.01) |
| source_quote | "First major contract with Marcy is July 2025. The Marcy's technology contract was a big one." |
| confidence | high |
| confidence_note | Month-exact. Described as "the single event that does more to calibrate the chart's forecasting capacity than any other post-2023 event." Strong retrodictive match to RPT.DSH.01. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Ma Kamlatmika (tantric Mahalakshmi) devotion began (November 2025)

| Field | Value |
|---|---|
| date | 2025-11-01 (proxy — native said "over the last six months" as of ~mid-2026; month-proxy per M5-A-S1) |
| category | spiritual |
| description | Native began praying intensely to the tantric form of Mahalakshmi — Ma Kamlatmika (one of the Dasha Mahavidyas). Coincides with financial recovery and business intensification. A Lakshmi-form alongside existing Ugratara (Shakti) and Mahadev (Shiva) lineages — three tantric streams active simultaneously. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.11.XX.01) |
| source_quote | "Over the last six months, I have started praying a lot to Mahalakshmi the tantric form of Mahalakshmi that is Ma Kamlatmika." |
| confidence | medium |
| confidence_note | Month-approx; onset inferred from "last six months" statement (as of ~mid-2026). |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Spiritual gravitation toward Lord Vishnu / Venkateshwara Balaji (2025)

| Field | Value |
|---|---|
| date | 2025-07-01 (proxy — native said "started naturally gravitating"; year-approx 2025; mid-year proxy) |
| category | spiritual |
| description | Spiritual shift toward Lord Vishnu / Lord Venkateshwara Balaji of Tirupati. Occurred "naturally" per native. Continues alongside long-term Maa Ugratara (Tantric Shakti) and Mahadev (Shiva) devotions. Directly matches CTR.02 prediction from Deep Analysis v1.2.1 — "strongest retrodictive match of any 2025 event." |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.XX.XX.01) |
| source_quote | "Started naturally gravitating towards Lord Vishnu and currently praying to Lord Venkateshwara Balaji of Tirupati." |
| confidence | medium |
| confidence_note | Year-approx; exact month unknown. LEL marks date_confidence as year-approx. Proxy date (mid-2025) used. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Chronic sleep disorder resolved via Lemborexant/Dayvigo (2025)

| Field | Value |
|---|---|
| date | 2025-06-01 (proxy — native said "2025 or 2026"; LEL logs as 2025; mid-year proxy per M4-A-T1-SWISS-EPHEMERIS) |
| category | health |
| description | Chronic sleep disorder (onset EVT.2007.XX.XX.03, ~18 years) resolved via Lemborexant (brand name: Dayvigo), discovered through an astrology consultation. First medication to work without debilitating drowsiness side effects. Native had tried half a dozen doctors and multiple drugs across India and the US without success. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2025.XX.XX.02) |
| source_quote | "I found the solution to my sleeping disorder in 2025 when I was consulting astrology and the astrological pharmaceutical remedy was Dayvigo drug, which is the generic name Lemborexant. I pop a pill and know without the negative impacts of drowsiness of the other drugs." |
| confidence | medium |
| confidence_note | Year-approx; native said "2025 or 2026". LEL adopted 2025. Proxy date June 2025 used. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Focused one-pointed attention shift toward business (January–February 2026)

| Field | Value |
|---|---|
| date | 2026-01-15 (proxy — native said "between January to February 2026"; mid-month proxy per M4-A-T1-SWISS-EPHEMERIS) |
| category | psychological |
| description | Between January and February 2026, native experienced a marked and sustained shift to focused, one-pointed attention directed entirely at business. Long-standing distractions (relational, psychological, otherwise) described as "wiped out." Native characterises this as an entirely new operational mode — chronic distraction replaced by sustained focus. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2026.01.XX.01) |
| source_quote | "Between January to February 2026, I found an enormous amount of focus and one-pointed approach, where a lot of things that have distracted me for most part of my life have been wiped out and I'm completely focusing on business." |
| confidence | high |
| confidence_note | Month-approx (Jan or Feb 2026). Native directly described this as a marked shift. Psychological category. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Marsys Technology primary project wrapped up with profits (20 March 2026)

| Field | Value |
|---|---|
| date | 2026-03-20 |
| category | finance |
| description | Marsys Technology (IT company co-founded with a MasterCard executive) wrapped up its primary project on 20 March 2026 with "enormous profits." Revenue generated steadily from 2023 through 2026. Project completion ends the revenue stream; profits accumulated represent a meaningful financial buffer. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2026.03.20.01) |
| source_quote | "The project got wrapped up on March 20, 2026, with enormous amount of profits. Unfortunately it got wrapped up so we won't be able to make money out of it, but it's significantly helped us during the difficult times with the money that we made out of it." |
| confidence | high |
| confidence_note | Exact date. Day-level precision confirmed by native. Second exact-date TEST event alongside twins' birth and sand mine launch. |
| test_split | YES (>= 2020-01-01) |

---

## Candidate: Second sand quarry public hearing cleared (8 April 2026)

| Field | Value |
|---|---|
| date | 2026-04-08 |
| category | career |
| description | Public hearing for the second sand quarry (pre-history EVT.2021.XX.XX.03) successfully closed on 8 April 2026, clearing the primary regulatory obstacle after ~4–5 years. Quarry expected to become operational by late October 2026. |
| already_in_lel_db | false |
| source_file | `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (EVT.2026.04.08.01) |
| source_quote | "Eventually, on April 8, 2026, we closed the public hearing for that sand quarry and it should be operational in late October 2026." |
| confidence | high |
| confidence_note | Exact date. Day-level precision confirmed by native. |
| test_split | YES (>= 2020-01-01) |

---

## Section C — EVT.CURRENT.01 (Not Staged — Status Event)

`EVT.CURRENT.01` (current marital separation status as of 2026-04-17) is explicitly marked in the LEL frontmatter as "not counted as a point event." It is an ongoing-state entry, not a discrete scoreable event. It is NOT staged here.

---

## Section D — Abhinandan Event Candidates (chart_id: 1c826d5a-41cb-4450-b4dc-59d440e5f75a)

**No Abhinandan event candidates found.** A search of the corpus (SESSION_LOG.md, LIFE_EVENT_LOG_v1_2.md, MSR_v5_0.md, CGM_v9_0.md, CDLM_v1_1.md) found no dated life events for the Abhinandan Mohanty chart documented in source files with sufficient specificity for LEL loading. The Abhinandan chart is referenced only as a build/test chart for the orchestrator pipeline, not as a subject with a documented event biography.

---

## Section E — Corpus Anomaly Note

During mining, the `CDLM_v1_1.md` file at line 925 contains the following passage:

> "EVT.2007 (Singapore move) = the career-defining move = the single biggest career-enabling event was a geographic travel event"

This refers to "Singapore move" but the canonical LEL records the 2019 US move (EVT.2019.05.XX.01), not a 2007 Singapore move. The 2007 events in the LEL are the knee surgery, engineering graduation, and Cognizant join — all in India/Chennai, with no Singapore move recorded. This appears to be an editorial artifact in the CDLM (perhaps a placeholder or drafting error), not an actual dated Singapore move event. It is NOT staged as a candidate because no source quote in the LEL or any other corpus file corroborates a 2007 Singapore move. Flagged here for native review / CDLM correction.

---

## Section F — Gap Register Items Referenced in LEL §6

The following items from the LEL §6 Gap Register describe potential events that have been mentioned in source material but are NOT yet dated with enough precision to stage as candidates. They are noted here for completeness but NOT staged as LEL candidates.

| Gap ID | Description | Status |
|---|---|---|
| GAP.TEPPER.DATES.01 | Tepper MBA exact start + completion dates | Month-approx staged above (EVT.2023.06.XX.01); exact start date still unknown |
| GAP.US_JOB_LOSS.01 / GAP.US_JOB_LOSS_PRECISE.01 | US job loss exact date (before May 2023) | Not staged — date unknown; confirmed only as "before May 2023 India return" |
| GAP.SADE_SATI_CYCLE_1.01 | Cycle 1 Sade Sati dates (~1993-2000) | Not a discrete event; astrological computation gap, not an LEL candidate |
| GAP.RELATIONSHIP_3_END.01 | R#3 exact end month (estimated Oct 2022) | Staged above with medium confidence |
| GAP.IIT_OUTCOME.01 | Whether native sat IIT JEE and its outcome | No date available; undatable at this stage |
| GAP.HEALTH_EPISODES.01 | Other health events beyond logged ones | Nothing found in corpus with date + quote |
| GAP.FINANCIAL_LOSSES.01 | Other significant financial losses besides May 2025 scam | Nothing found in corpus with date + quote |
| GAP.TRAVEL_MISC.01 | Other foreign travel (Russia trips etc.) | Nothing found with date + quote |
| GAP.GRANDMOTHER.01 | Paternal grandmother life events | Nothing found with date + quote |
| GAP.MOTHER_STATUS.01 | Mother-related events | Nothing found with date + quote |
| GAP.BROTHER_STATUS.01 | Younger brother events (career, marriage etc.) | Nothing found with date + quote |

---

## Scoring Note for CRPS Harness

If the native attests all 20 TEST split candidates, the total scoreable event pool would grow from 36 (TRAIN only) to 56 (36 TRAIN + 20 TEST), representing the full 57-event LEL minus the status event. The CRPS harness would gain 20 additional scoring opportunities across:

- 5 high-value exact-date events: twins born (2022-01-03), sand mine launch (2024-02-16), Marsys Technology project wrapped (2026-03-20), sand quarry hearing cleared (2026-04-08), plus the proxy-for-exact scam (2025-05)
- 6 month-exact events (sufficient for ±30d CRPS scoring tier)
- 9 year-approx events (eligible for domain/category scoring only under Option B rubric)

*End of LEL_CANDIDATES_STAGED.md v1.0*
