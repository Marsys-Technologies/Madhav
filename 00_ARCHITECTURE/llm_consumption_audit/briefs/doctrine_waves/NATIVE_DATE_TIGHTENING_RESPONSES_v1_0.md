---
artifact: NATIVE_DATE_TIGHTENING_RESPONSES
type: NATIVE GROUND-TRUTH SUBMISSION (answers to NATIVE_DATE_TIGHTENING_QUESTIONNAIRE)
version: 1.0
status: PARTIAL SUBMISSION — recorded verbatim-faithful by Cowork (Fable) from the native's
  dictated answers, 2026-07-19. Ingestion target: D-4a Lane A-1 (LEL schema v2 migration).
  One mapping ambiguity flagged (item #3) — do NOT ingest that row until native confirms.
firewall: pure LEL ground-truth data entry per TEMPORAL_ENGINE_ARC_PLAN §11 — no model output
  was shown to the native before or during this submission (blind-tightening discipline held).
authored_by: native (dictated) via Cowork session 2026-07-19
---

# Native Date-Tightening Responses (partial, 2026-07-19)

## Part 1 answers

| # | event | native's answer (faithful record) | proposed DR-13 encoding |
|---|---|---|---|
| 1 | Headaches chronic_onset (rec. 1995-07-01) | "No single date. Started around 1995, continued ACTIVELY till 2010, then gradually subsided; past it by 2021." | shape=**chain/interval hybrid**: active interval [~1995 → ~2010]; subsiding tail [2010 → 2021]; resolution milestone ~2021 (year-confidence). Onset year-confidence 1995. |
| 2 | Stammering arc (rec. onset ~1995) | "No onset date can be given — present SINCE BIRTH, continues till date." | **CORRECTION to recorded data**: onset = congenital (birth), not ~1995. shape=chronic trait (lifelong interval, open-ended). Candidate for reclassification to LEL §4 chronic-pattern rather than dated event; phase-transition dates not available. |
| 3 | Father's spiritual dialogues (rec. ~1997–2001) | RESOLVED (native, 2026-07-19): "1997 is not correct. The late-night discussions with my father started in 2001. That was the INITIATION of my spiritual journey — the seeds were planted, and till date I am on that journey." | **CORRECTION + chain**: milestone-1 = dialogues/initiation begin ~2001 (year-confidence; supersedes recorded ~1997 start); milestone-2 = open-ended lifelong spiritual-journey arc [2001 → present], of which items #6 (Shani sadhana ~2002), #10 (Mahadev 2021-04/05), #14 (intensification ~2024), #15 (mandala chain) are later milestones — encode the arc linkage. |
| 4 | Aptech course (rec. ~2000-06) | "Stick with my response; tentative dates; I did it for SIX MONTHS from the start date." | shape=interval: [~2000-06 → ~2000-12], start month-confidence tentative, duration ~6 months (native-stated). |
| 5 | Vertigo/chronic episode (rec. ~2002) | "The health issues from item 1 PEAKED around this time; at its peak for at least three years." | shape=interval (peak phase of the item-1 arc): [~2001/2002 → ~2004/2005], year-confidence. Links to item 1 as its peak sub-interval — encode as related_event. |
| 6 | Shani Puja initiation (rec. ~2002) | "During the psychological/chronic episode I was driven toward spiritualism, which has only grown over time — far more spiritual now than then. No exact time." | shape=interval, open-ended: onset within the item-5 peak window (~2002, year-confidence), monotonic-growth arc to present. No tighter anchor. |
| 7 | Sleep-disorder onset (rec. 2007-09) | AMENDED (native, 2026-07-19): "ON THE DAY of the arthroscopy I started my breathlessness — that's why the two dates coincide." | shape=chain with **irreversibility_moment = the arthroscopy day itself** (EVT.2007.06.XX.01, on file at month-confidence June 2007) — breathlessness onset SAME DAY; sleep-disorder arc follows from it; subsided-then-resolved counterpart a95552d7 (2025). Onset anchor upgraded from year- to month-confidence, day-locked to the arthroscopy event whenever that date tightens. Encode hard event-link onset↔arthroscopy. |
| 8 | Grandfather's passing (rec. 2009-06-15) | "Between 2009-06-15 and 2009-07-15, mostly around June 30th, 2009." | shape=point; interval_bounds [2009-06-15 → 2009-07-15], best_estimate 2009-06-30, month-confidence. Meaningful tightening. |
| 9 | Family windfall (rec. 2010-07-01) | "Father received a large sum, we were beneficiaries. A period of six months or a little more: from 2010 July to ~March 2011." | shape=**interval** (per approved reclassification): [2010-07 → 2011-03], month-confidence bounds. HIGH-VALUE tightening for the named §G anchor event. |
| 10 | Mahadev/Shiva adoption (rec. 2015-07-01) | "Date not accurate. I gravitated toward Mahadev in 2021, April–May." | **CORRECTION to recorded data**: onset [2021-04 → 2021-05], month-confidence — supersedes the recorded ~2015 estimate. (Note for LEL maintainers: the prior "early thirties ~2014–2016" description came from an earlier disclosure; the native's direct correction governs. Keep both in provenance per append-only discipline.) |
| 11 | Second quarry acquired/stalled (rec. 2021) | "Date is tentative." | No tighter data — remains year-confidence; chain membership with #16 stands (Part 2A additional milestones not provided). |
| 12 | Tepper-period affair (rec. 2022-07-01) | "Date is correct; exact date I would say August 15th — or let's say August 20th, 2022." | shape=point (start milestone); interval_bounds [2022-08-15 → 2022-08-20], best_estimate 2022-08-20, week-confidence. |
| 13 | Relationship #3 ended (rec. 2022-10-15) | "Change the date: 2022 July 14th." | **CORRECTION**: 2022-07-14, day-confidence (was ~2022-10-15). Note: this re-orders it BEFORE the #12 affair-start milestone — chronology now internally consistent per native. |
| 14 | Practice intensification (rec. ~2024) | — not addressed — | leave as recorded (no tighter data claimed). |
| 15 | Yantra mandala (rec. 2025-06-15) | "Tentative. A smaller mandala existed EARLIER than the recorded date; the peak/enhanced mandala was tentatively at the date already mentioned." | shape=**chain**: milestone-1 initial mandala (undated, earlier); milestone-2 enhanced/peak mandala ~2025-06-15 (month-confidence, tentative). |
| 16 | Quarry hearing cleared (rec. 2026-04-08) | "Perfectly correct." | confirmed, day-confidence. |

## Part 2 answers
- **A (quarry chain intermediates):** not provided — chain remains #11 (tentative 2021) → #16 (2026-04-08).
- **B (windfall bounds):** ANSWERED — see #9: [2010-07 → 2011-03].
- **C (arthroscopy date as onset anchor):** not recalled — see #7.
- **D (Mahindra crash / Tepper selection tighter dates):** Mahindra Retail crash CONFIRMED
  accurate by native (2026-07-19 — "that's correct, the Mahindra Retail crash, that's the exact
  company"); no tighter month offered, remains year-confidence 2016. Tepper selection date not
  addressed — remains as recorded.
- **E (XIMB dates):** not addressed — stand as recorded.

## Part 3
Not addressed this pass. (Two implicit Part-3-class corrections were supplied inside Part 1
anyway: #2 congenital stammering, #10 Mahadev-2021, #13 relationship-end July.)

## Ingestion notes for A-1 (D-4a)
1. Three rows are CORRECTIONS, not just tightenings (#2, #10, #13) — LEL is append-only: record
   as v2 correction entries with provenance, never overwrite the original rows.
2. Item #3 is QUARANTINED pending native confirmation.
3. Items #1+#5 are linked (peak sub-interval of the same arc) — encode the relation.
4. The #9 windfall interval [2010-07→2011-03] should flow into the re-scoring of the named
   anchor event under DR-13 interval semantics at the next harness run (D-4a A-5 dry-run).
5. Confidence vocabulary used: day / week / month / year — maps to DR-13(d) tolerance tiers.
