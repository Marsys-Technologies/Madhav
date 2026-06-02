---
artifact: LIFE_EVENT_LOG_FACTS_ONLY_v1_0
document: LIFE EVENT LOG (FACTS ONLY) — ABHISEK MOHANTY
project: MARSYS-JIS / Project Brahma
layer: L1 (Facts Layer) — pure-event log
canonical_id: LEL_FACTS_ONLY
status: DERIVED from LIFE_EVENT_LOG_v1_2.md (content v1.7); lived-reality facts retained, all astrological annotation stripped
derived_from: 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md (v1.7)
stripped: chart_state_at_event blocks; retrodictive_match blocks; per-period vimshottari/yogini/chara/sade_sati/retrodictive_note keys; §4 likely_astrological_basis; §7 retrodictive aggregate; §8 changelog; §9 prospective predictions
retained: events (date, date_confidence, category, subcategory, description, magnitude, valence, native_reflection, notes) + §4 chronic patterns + §5 inner turning-point periods (facts) + §6 gap register
total_events: 57
date_range_covered: 1984-02-05 to 2026-04-17
principle: pure-event LEL — lived-reality facts only; no chart-state, no dasha tables, no signals, no predictions, no interpretation
generated_by: Claude (Cowork) 2026-06-02
---

# Life Event Log (Facts Only) — Abhisek Mohanty

> **Pure-event version.** The life events as lived-reality facts, with the astrological apparatus removed —
> chart-state blocks, dasha/transit tables, signal-matching, retrodictive analysis, and prospective
> predictions. Derived from `LIFE_EVENT_LOG_v1_2.md` (v1.7). Clean ground-truth corpus (57 events) for the
> Brahma rebuild's LEL intake — isolated from anything generated.

## §1 — How to read
- **§3** chronological event log (57 events across 8 eras + the M5-A enrichment).
- **§4** chronic patterns / undated traits · **§5** inner turning-point periods · **§6** gap register.
- Event ID: `EVT.YYYY.MM.DD.XX` (XX = placeholder where a date component is unknown).
- Per-event fact fields: `date · date_confidence · category · subcategory · description · magnitude · valence · native_reflection · notes`.

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
EVT.2001.03.XX.01:
  date: 2001-03-XX
  date_confidence: month-exact (approx)
  category: education
  subcategory: entrance_exam_preparation
  description: Began IIT preparation around March 2001 (age 17, during 12th standard). Continued intensive preparation through June 2003.
  magnitude: significant
  valence: mixed
  native_reflection: "I started my IIT preparation about March 2001 or maybe earlier, March 2000, and continued till June 2003." (March 2001 adopted as most probable start; 2000 may be conflated with 11th std year at BJP College.)
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
EVT.2012.10.XX.01:
  date: 2012-10-XX
  date_confidence: month-exact
  category: relationship
  subcategory: romantic_concurrent
  description: Relationship #3 started (October 2012, 10-year duration → ended ~October 2022). Concurrent with primary long-term relationship (R#1) through marriage year (2013) and into marriage years.
  magnitude: major
  valence: mixed
  native_reflection: "Oct 2012 (10 years)."
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
EVT.2026.03.20.01:
  date: 2026-03-20
  date_confidence: exact
  category: career
  subcategory: business_project_closed
  description: Marsys Technology (IT company co-founded with a MasterCard executive) wrapped up its primary project on 20 March 2026 with "enormous profits." Revenue generated steadily from 2023 through 2026, significantly supporting the native and Marsys Group through the difficult post-US-return period. Project completion ends the revenue stream; profits accumulated represent a meaningful financial buffer.
  magnitude: significant
  valence: mixed
  native_reflection: "The project got wrapped up on March 20, 2026, with enormous amount of profits. Unfortunately it got wrapped up so we won't be able to make money out of it, but it's significantly helped us during the difficult times with the money that we made out of it."
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
  notes: Ongoing state. To be updated with trajectory as v1.1+ evolves.
```

### Era M5A Enrichment — Spiritual, Creative, Psychological (M5-A-S1 additions, 2026-05-13)

*10 events approved by native in Cowork session 2026-05-13. Inserted at end of §3 for this session; should be merged into appropriate era sections in a future maintenance pass. Chart states marked `pending_computation` where year-approx; proxy dates used per established convention.*

```yaml
EVT.1993.XX.XX.01:
  date: 1993-XX-XX
  date_confidence: year-approx
  category: creative
  subcategory: award
  description: Mother enrolled native in painting classes at early age; native excelled and won multiple awards in childhood painting competitions. Creative visual skill established early. Subsequently moved away from painting; creative output shifted to digital/professional domains (presentations, brand design). The visual-spatial gift persisted as a latent trait activated selectively in professional/entrepreneurial contexts.
  magnitude: moderate
  valence: positive
  native_reflection: "At an early age my mother had put me to learn painting and I was pretty good at it. I won several awards in my childhood in painting competitions."
  notes: "CRE.A from M5-A-S1 enrichment batch."
```

```yaml
EVT.1995.XX.XX.02:
  date: 1995-XX-XX
  date_confidence: year-approx
  category: psychological
  subcategory: speech_pattern_arc
  description: Stammering onset in childhood (anchor: ~1995, school years). Three-phase arc: Phase 1 (childhood ~1995–2006): significant stammering; nickname 'sacca' given by friend. Phase 2 (engineering/MBA ~2007–2024): sustained practice substantially overcame it — contemporaries unaware native stammered. Phase 3 (resurgence ~2025–present): stammering has resurfaced after approximately one year; diagnosis unknown (psychological, neural, or genetic). Native manages but carries psychological impact. NOTE: three phases described; this EVT anchors the onset; phases 2+3 can be split into separate EVTs if warranted.
  magnitude: moderate
  valence: negative (phases 1+3); positive (phase 2 overcome)
  native_reflection: "In my childhood I used to stammer quite a bit. I practiced a lot and during my engineering days and my MBA days I significantly got over it... That stammering has resurfaced over the last one year and I'm struggling with it."
  notes: "PSY.B from M5-A-S1 enrichment batch. PATTERN.STAMMER.01 in §4 captures the ongoing pattern; this EVT captures the onset anchor."
```

```yaml
EVT.1998.XX.XX.02:
  date: 1998-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: transmission
  description: Father (Late Shri Soumya Ranjan Mohanty) held late-night spiritual dialogues with close friends; native joined in limited capacity during teens (~1997–2001). These conversations planted the seed of spirituality. Father's approach intermingled Hinduism and spirituality — became the native's foundational spiritual orientation. Astrologically significant: father as transmitter of Saturn-discipline (Saturn rules native's Arudha Lagna, Capricorn, 10H).
  magnitude: significant
  valence: positive
  native_reflection: "My father was a very spiritual person. I would join late night conversation between my father and one or two specific friends of his who might be staying over in these spiritual conversations in a limited way."
  notes: "SPR.A from M5-A-S1 enrichment batch."
```

```yaml
EVT.2002.XX.XX.01:
  date: 2002-XX-XX
  date_confidence: year-approx
  category: psychological
  subcategory: chronic_episode
  description: Inherited vertigo/head reeling (maternal line — mother and maternal grandmother both affected) reached peak debilitation during engineering competitive exam preparation (~2001–2004). Bouts were described as 'debilitating' and directly impacted academic performance. The fear of recurrence persisted for approximately one decade. Onset likely earlier (teen years); peak impact on career trajectory was during exam prep.
  magnitude: significant
  valence: negative
  native_reflection: "The period between 2001 to 2004 especially 2001 to 2002 when I was preparing for my competitive exams, engineering exams. I was hit hard by vertigo and that left a deep mark, psychological mark and I've feared it with all my life for close to a decade."
  notes: "PSY.A from M5-A-S1 enrichment batch."
```

```yaml
EVT.2002.XX.XX.02:
  date: 2002-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: sadhana_initiation
  description: Father instructed native (age ~18–19) to perform Shani Puja nightly. Native read Shani Shtotram every night for approximately 7–10 years. This became the first formal sustained sadhana practice. Father as transmitter of Saturn-discipline is astrologically significant: Saturn rules native's Arudha Lagna (Capricorn, 10th house). Shani Puja directly invokes the chart's most powerful planet — a father-directed dharma initiation.
  magnitude: significant
  valence: positive
  native_reflection: "My father asked me to do Shani Puja. So every night I used to read Shani Shtotram for a good seven, eight years or ten years."
  notes: "SPR.B from M5-A-S1 enrichment batch."
```

```yaml
EVT.2010.XX.XX.02:
  date: 2010-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: devata_adoption
  description: Began regular devotion to Maa Ugratara at the Ugratara Shakti pitha near Bhubaneswar (~15 years running as of 2026). A tantric Shakti form. This is the native's longest-sustained single devata relationship. Commenced during mid-to-late twenties (Mercury MD transition coincides). Ugratara = fierce, solar, transformative Shakti — astrologically aligned with this chart's Aries Lagna + Saturn-Venus axis.
  magnitude: significant
  valence: positive
  native_reflection: "During my mid-twenties and until today, I became a devout devotee of Mah Ugratara. Near to Bhubaneswar, there is a Ugratara Shakti peat, which I have been visiting for the last ten years or more, close to about fifteen years."
  notes: "SPR.C from M5-A-S1 enrichment batch."
```

```yaml
EVT.2015.XX.XX.01:
  date: 2015-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: devata_adoption
  description: In early thirties (~2014–2016), native began gravitating toward Mahadev/Shiva. This deepened over the following decade to the point of daily abhisheka (see EVT.2024.XX.XX.01). Concurrent with Ugratara devotion; no conflict perceived until Krishna re-emerged. Shiva = Mahadeva, primordial; astrologically associated with Saturn, Ketu, moksha themes — all strongly placed in this chart.
  magnitude: significant
  valence: positive
  native_reflection: "In my early thirties I started gravitating towards Mahadev or Shiv, and until today, I am a devout devotee of Mahadev."
  notes: "SPR.D from M5-A-S1 enrichment batch."
```

```yaml
EVT.2024.XX.XX.01:
  date: 2024-XX-XX
  date_confidence: year-approx
  category: spiritual
  subcategory: practice_intensification
  description: From ~2024: daily pouring of water on shivalinga (abhisheka); independent yajna execution (fire ritual, self-conducted without a pandit); systematic panchang study (transit, muhurta, tithi); identification and planning of yajna timings using astrological data. Simultaneous with entrepreneurial transition and dharma-embrace (self-described 'I must align my life to Dharma'). Highest concentration of new spiritual practices in native's life. Coincides with Mercury-Saturn AD start (Dec 2024) and Sade Sati peak.
  magnitude: major
  valence: positive
  native_reflection: "For the last two years I have been pouring water on the shiveling almost every day... I have been doing enormous amount of yajna. Now I have developed a skill that I do a yajna on my own... I have been following astrological data, looking at the panchang."
  notes: "SPR.E from M5-A-S1 enrichment batch."
```

```yaml
EVT.2025.06.XX.01:
  date: 2025-06-XX
  date_confidence: month-approx
  category: spiritual
  subcategory: ritual_infrastructure
  description: Native established a personal yantra mandala in his bedroom — a permanent ritual space. Prayers offered almost daily, sometimes more than once. Combined with daily ritual routine (~1.5–2 years running as of 2026). Represents formalization of the private ritual life begun in ~2024. The yantra mandala is a physical spatial commitment to the tantric stream running through Ugratara, Mahadev, and now Ma Kamlatmika devotions.
  magnitude: significant
  valence: positive
  native_reflection: "I have my own yantra mandala established in my bedroom, which I offer prayers almost every day, sometimes more than once. There is a daily ritual that I follow."
  notes: "SPR.F from M5-A-S1 enrichment batch."
```

```yaml
EVT.2025.11.XX.01:
  date: 2025-11-XX
  date_confidence: month-approx
  category: spiritual
  subcategory: devata_adoption
  description: Native began praying intensely to the tantric form of Mahalakshmi — Ma Kamlatmika (one of the Dasha Mahavidyas). Coincides with financial recovery and business intensification. A Lakshmi-form alongside the existing Ugratara (Shakti) and Mahadev lineages — now three tantric streams active simultaneously. Ma Kamlatmika = tantric Mahalakshmi, the tenth Mahavidya; governs wealth, abundance, sovereignty under transformation.
  magnitude: significant
  valence: positive
  native_reflection: "Over the last six months, I have started praying a lot to Mahalakshmi the tantric form of Mahalakshmi that is Ma Kamlatmika."
  notes: "SPR.G from M5-A-S1 enrichment batch."
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
```

```yaml
PATTERN.PHYSIQUE.01:
  trait: Height 6'3", lean-muscular build in peak (2012-2013), currently good/well-maintained at 42
  onset: peak physique 2012-2013 (overlaps XIMB period)
  native_reflection: "Previously possessed a very lean, muscular body and gained some modeling experience. Currently the physique has evolved from that peak muscular phase, it remains good and well-maintained."
```

```yaml
PATTERN.SPORTS_LUCK.01:
  trait: Sports participation directly correlates with better luck and prosperity
  native_reflection: "Physically active by nature; sports participation directly correlates with better luck and prosperity." / "Luck, productivity, and social magnetism peak during active sports phases."
```

```yaml
PATTERN.SLEEP_IRREGULARITY.01:
  trait: Sleep irregularities; undisciplined sleep impacts schedule and productivity; night hours boost creativity
  native_reflection: "Suffers from sleep irregularities; lack of discipline in sleep impacts schedule and productivity." / "Night hours boost creativity and work output, though they disrupt health and schedule."
```

```yaml
PATTERN.HEADACHES.01:
  trait: Severe headaches since ~1995; screen-time as trigger
  onset: circa 1995 (captured as EVT.1995.XX.XX.01 — the onset event; pattern is the persistence)
  native_reflection: "Suffered from severe headaches since around 1995, a major part of early life."
```

```yaml
PATTERN.COMPUTER_APTITUDE.01:
  trait: Exceptional computer/programming aptitude from teenage onward; recognized early; returned to it recently
  native_reflection: "Was a 'successful geek' and extremely proficient with computers at a young age, achieving recognition." / "Back to it now."
```

```yaml
PATTERN.COCKROACH_PHOBIA.01:
  trait: Cockroach phobia — early childhood onset, persists to present
  onset: early childhood (likely triggered by village environment with high cockroach density)
  trajectory: Lifelong; mildly subdued over time but not resolved. Psychological fear response without known exposure therapy.
  native_reflection: Not verbatim captured; characterized as childhood environmental trigger persisting.
  notes: "M5-A-S1 chronic pattern addition from native Cowork-M5-S2 disclosure."
```

```yaml
PATTERN.MANASA_PUJA.01:
  trait: Manasa puja (visualized inner ritual) — lifelong capacity for deep internalized puja
  onset: unknown; appears constitutional
  trajectory: Lifelong, selectively applied. Distinct from seated meditation. Used during bead-counting, physical puja sessions, and independent visualization exercises.
  native_reflection: Not verbatim captured; described as capacity for elaborate emotional and visual detail in internalized ritual — offering prayers, small rituals, and puja entirely in the mind.
  notes: "M5-A-S1 chronic pattern addition from native Cowork-M5-S2 disclosure."
```

---

## §5 — INNER TURNING-POINT PERIODS (Native's Self-Characterization)

```yaml
PERIOD.2007:
  dates: 2007 (calendar year)
  native_reflection: "I don't think [2007] was in any way significant, only thing was I completed my BTEC, my engineering and started my first job."
  dominant_events_in_period: [EVT.2007.06.XX.01 (knee surgery), EVT.2007.06.XX.02 (engineering), EVT.2007.06.10.01 (Cognizant join)]
```

```yaml
PERIOD.2012_2013:
  dates: 2012 through 2013 (calendar years)
  native_reflection: "2012-13 was the best period of my life. I played basketball, enjoyed my time with the opposite sex. I had a lot of partying so it was an ace in everything. I can't forget that period."
  dominant_events_in_period: [EVT.2012.09.XX.01 (modeling), EVT.2012.10.XX.01 (R#3 start), EVT.2013.03.XX.01 (XIMB graduation), EVT.2013.05.XX.01 (Mahindra Retail), EVT.2013.12.11.01 (marriage)]
```

```yaml
PERIOD.2016:
  dates: 2016 (calendar year)
  native_reflection: "2016 was a bit stressful when I was looking for a job outside Mahindra Retail as the company had crashed and that's when I decided to switch over to Tech Mahindra."
  dominant_events_in_period: [EVT.2016.XX.XX.01 (Mahindra Retail crash)]
```

```yaml
PERIOD.2018_2021:
  dates: 2018 through 2021
  native_reflection: "I lost my father, so it was a mentally traumatic time running a lot of the hospitals, running from Hyderabad to Neshwar. So but 2019 to 21 was in the US exciting."
  dominant_events_in_period: [EVT.2018.11.28.01 (father passed), EVT.2019.05.XX.01 (US move), EVT.2021.01.XX.01 (panic episode — moved here in v1.1 from 2022)]
```

```yaml
PERIOD.2022_2024:
  dates: 2022 through 2024
  native_reflection: "22 to 24 was a mix, it was new relationships and rupture of old success in professional career in my job but I lost my job in the US moved to India in fact was a pivotal point where I completely changed my life from salary job to business which I couldn't have done otherwise was primarily driven by turn of events and my own decision."
  dominant_events_in_period: [EVT.2022.01.03.01 (twins), EVT.2022.10.XX.01 (R#3 end), EVT.2023.05.XX.01 (US return + pivot), EVT.2023.06.XX.01 (Tepper), EVT.2023.07.XX.01 (Marsys founded), EVT.2024.02.16.01 (sand mines)]
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

GAP.RELATIONSHIP_3_END.01:
  issue: R#3 end date ~Oct 2022 is estimated from "10 years" duration + Oct 2012 start
  resolution_path: Confirm exact end month in next session

GAP.IIT_OUTCOME.01:
  issue: Whether native sat IIT JEE exam and its outcome — implicit "did not crack" from doc's "A1-tier not secured"
  resolution_path: Confirm in next session — did he attempt JEE? What rank/outcome?

GAP.INFIDELITY_TEMPORAL_PRECISION.01:
  issue: Native confirmed R#2 + R#3 capture physical infidelity timespans, but specific episodes within those spans not enumerated

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


---

*Facts-only projection of LIFE_EVENT_LOG_v1_2.md (v1.7), generated 2026-06-02. The source's chart-state, dasha, signal-matching, retrodictive and prospective-prediction content is excluded. The source file remains the full annotated record.*
