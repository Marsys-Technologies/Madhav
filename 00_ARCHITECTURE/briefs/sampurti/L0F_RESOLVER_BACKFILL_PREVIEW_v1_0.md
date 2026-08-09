---
artifact_id: L0F_RESOLVER_BACKFILL_PREVIEW
version: "1.0"
status: CURRENT
campaign: SAMPURTI
lane: L0f
mission: G14a — L6 LEL→event_class resolver + 64-event classification preview
resolver_version: l0f_v1.0
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
run_date: 2026-08-10
total_rows: 64
classified: 63
ambiguous: 1
coverage_assertion: "63 + 1 == 64 (PASS)"
---

# L0F RESOLVER — BACKFILL PREVIEW (READ-ONLY)

SAMPURTI Campaign · Lane L0f · G14a · 2026-08-10

Resolver: `brahmagyan/lel_event_class_resolver.py` (RESOLVER_VERSION=`l0f_v1.0`)
Migration claimed: **553** (`platform/supabase/migrations/553_lel_event_class_resolution.sql`)
Mode: READ-ONLY (no rows written to DB; persist executes at Wave-0 gate/deploy via `--persist` flag)

## Coverage assertion

`classified (63) + ambiguous (1) == total (64)` — PASS
No silent drops.

---

## Full 64-row classification table

| # | event_id (truncated) | event_date | category | domain | event_class | confidence | rule_matched | matched_tokens |
|---|---|---|---|---|---|---|---|---|
| 1 | 3e96c6da-…-corr-congenital | 1984-02-05 | psychological | psychological/speech_pattern_arc | psychological_arc | EXACT | tier1_domain_exact | psychological/speech_pattern_arc |
| 2 | 5d039007-… | 1984-02-05 | other | other/birth | birth_anchor | EXACT | tier1_domain_exact | other/birth |
| 3 | 0d03e02a-… | 1993-07-01 | creative | creative/award | achievement_recognition | EXACT | tier1_domain_exact | creative/award |
| 4 | 3e96c6da-… | 1995-07-01 | psychological | psychological/speech_pattern_arc | psychological_arc | EXACT | tier1_domain_exact | psychological/speech_pattern_arc |
| 5 | 64c475da-… | 1995-07-01 | health | health/chronic_onset | chronic_onset | EXACT | tier1_domain_exact | health/chronic_onset |
| 6 | 3a37fa76-… | 1998-02-16 | relationship | relationship/romantic_long_term_started | romantic_start | EXACT | tier1_domain_exact | relationship/romantic_long_term_started |
| 7 | d5db1b9a-… | 1998-07-01 | spiritual | spiritual/transmission | spiritual_turn | EXACT | tier1_domain_exact | spiritual/transmission |
| 8 | 39f8395f-… | 2000-06-01 | education | education/advanced_course_partial | education_milestone | EXACT | tier1_domain_exact | education/advanced_course_partial |
| 9 | d5db1b9a-…-corr-2001-initiation | 2001-01-01 | spiritual | spiritual/transmission | spiritual_turn | EXACT | tier1_domain_exact | spiritual/transmission |
| 10 | 359944e3-… | 2001-03-15 | education | education/entrance_exam_preparation | education_milestone | EXACT | tier1_domain_exact | education/entrance_exam_preparation |
| 11 | 62f0460d-… | 2002-07-01 | spiritual | spiritual/sadhana_initiation | spiritual_turn | EXACT | tier1_domain_exact | spiritual/sadhana_initiation |
| 12 | 123eee97-… | 2002-07-01 | psychological | psychological/chronic_episode | psychological_arc | EXACT | tier1_domain_exact | psychological/chronic_episode |
| 13 | 4a1b1dc0-… | 2003-06-15 | education | education/entrance_exam_preparation_ended | education_milestone | EXACT | tier1_domain_exact | education/entrance_exam_preparation_ended |
| 14 | 45ba996d-… | 2004-01-15 | relationship | relationship/romantic_concurrent | romantic_start | EXACT | tier1_domain_exact | relationship/romantic_concurrent |
| 15 | cd68bc5c-… | 2004-06-01 | education | education/opportunity_declined | education_milestone | EXACT | tier1_domain_exact | education/opportunity_declined |
| 16 | fd04fecc-… | 2007-06-10 | career | career/first_job_joined | career_entry | EXACT | tier1_domain_exact | career/first_job_joined |
| 17 | 8573c0ca-…-corr-day-lock | 2007-06-14 | health | health/chronic_onset | chronic_onset | EXACT | tier1_domain_exact | health/chronic_onset |
| 18 | 4e09e1e1-… | 2007-06-15 | health | health/surgery_minor | surgery | EXACT | tier1_domain_exact | health/surgery_minor |
| 19 | 71af4f61-… | 2007-06-15 | education | education/engineering_completed | education_milestone | EXACT | tier1_domain_exact | education/engineering_completed |
| 20 | 8573c0ca-… | 2007-09-01 | health | health/chronic_onset | chronic_onset | EXACT | tier1_domain_exact | health/chronic_onset |
| 21 | aed78f94-… | 2008-06-09 | career | career/first_job_exited | career_change | EXACT | tier1_domain_exact | career/first_job_exited |
| 22 | 1dc207bc-… | 2009-06-15 | loss | loss/grandparent_passing | bereavement | EXACT | tier1_domain_exact | loss/grandparent_passing |
| 23 | bd7f5711-… | 2010-07-01 | finance | finance/family_windfall | major_gain | EXACT | tier1_domain_exact | finance/family_windfall |
| 24 | 132b61e0-… | 2010-07-01 | spiritual | spiritual/devata_adoption | spiritual_turn | EXACT | tier1_domain_exact | spiritual/devata_adoption |
| 25 | a1ef10c2-… | 2010-12-15 | travel | travel/first_foreign_trip | travel_event | EXACT | tier1_domain_exact | travel/first_foreign_trip |
| 26 | 4e96f4b9-… | 2011-01-15 | education | education/mba_admission | education_milestone | EXACT | tier1_domain_exact | education/mba_admission |
| 27 | 95138517-… | 2011-06-15 | education | education/mba_enrolled | education_milestone | EXACT | tier1_domain_exact | education/mba_enrolled |
| 28 | cf0c918d-… | 2012-09-01 | education | education/leadership_role | achievement_recognition | EXACT | tier1_domain_exact | education/leadership_role |
| 29 | 852d1420-… | 2012-09-15 | creative | creative/modeling | achievement_recognition | EXACT | tier1_domain_exact | creative/modeling |
| 30 | aa591eb5-… | 2012-10-15 | relationship | relationship/romantic_concurrent | romantic_start | EXACT | tier1_domain_exact | relationship/romantic_concurrent |
| 31 | c143ce2a-… | 2013-03-15 | education | education/mba_graduation | education_milestone | EXACT | tier1_domain_exact | education/mba_graduation |
| 32 | 6f5ee9cb-… | 2013-05-15 | career | career/corporate_job_joined | career_entry | EXACT | tier1_domain_exact | career/corporate_job_joined |
| 33 | 72fad18c-… | 2013-07-01 | family | family/parent_illness_onset | parental_event | EXACT | tier1_domain_exact | family/parent_illness_onset |
| 34 | b72f40f7-… | 2013-12-11 | family | family/marriage | marriage | EXACT | tier1_domain_exact | family/marriage |
| 35 | 56a1222d-… | 2015-07-01 | spiritual | spiritual/devata_adoption | spiritual_turn | EXACT | tier1_domain_exact | spiritual/devata_adoption |
| 36 | b5ea6a4d-… | 2016-07-01 | career | career/employer_instability | career_setback | EXACT | tier1_domain_exact | career/employer_instability |
| 37 | e3b2f1d5-… | 2017-03-15 | career | career/employer_switch | career_change | EXACT | tier1_domain_exact | career/employer_switch |
| 38 | b75c63f4-… | 2018-11-28 | loss | loss/parent_passing | bereavement | EXACT | tier1_domain_exact | loss/parent_passing |
| 39 | 928a1f56-… | 2019-05-15 | residential+travel | residential+travel/foreign_move_start | foreign_settlement | EXACT | tier1_domain_exact | residential+travel/foreign_move_start |
| 40 | 928a1f56-…-fs | 2019-05-15 | residential+travel | NULL | **AMBIGUOUS** | AMBIGUOUS | tier2_ambiguous_no_keyword_match | (null domain) |
| 41 | 974651b2-… | 2021-01-15 | health | health/panic_anxiety_episode | illness_acute | EXACT | tier1_domain_exact | health/panic_anxiety_episode |
| 42 | 56a1222d-…-corr-2021-04 | 2021-04-01 | spiritual | spiritual/devata_adoption | spiritual_turn | EXACT | tier1_domain_exact | spiritual/devata_adoption |
| 43 | b8884cbe-… | 2021-07-01 | career | career/award_selection | achievement_recognition | EXACT | tier1_domain_exact | career/award_selection |
| 44 | 74e527bb-… | 2021-07-01 | career | career/business_stalled | career_setback | EXACT | tier1_domain_exact | career/business_stalled |
| 45 | 25a0f2ec-… | 2022-01-03 | family | family/child_birth | childbirth | EXACT | tier1_domain_exact | family/child_birth |
| 46 | 86cbb042-… | 2022-07-01 | relationship | relationship/romantic_concurrent | romantic_start | EXACT | tier1_domain_exact | relationship/romantic_concurrent |
| 47 | 021e49f5-…-corr-2022-07-14 | 2022-07-14 | relationship | relationship/romantic_concurrent_ended | separation | EXACT | tier1_domain_exact | relationship/romantic_concurrent_ended |
| 48 | 021e49f5-… | 2022-10-15 | relationship | relationship/romantic_concurrent_ended | separation | EXACT | tier1_domain_exact | relationship/romantic_concurrent_ended |
| 49 | 7f29458f-… | 2023-05-15 | residential+travel | residential+travel/foreign_return | relocation | EXACT | tier1_domain_exact | residential+travel/foreign_return |
| 50 | d506f3e6-… | 2023-06-15 | education | education/executive_education_completed | education_milestone | EXACT | tier1_domain_exact | education/executive_education_completed |
| 51 | 661c8535-… | 2023-07-15 | career | career/entrepreneurship_founded | business_launch | EXACT | tier1_domain_exact | career/entrepreneurship_founded |
| 52 | 836bb274-… | 2024-02-16 | career | career/business_milestone_major | career_advancement | EXACT | tier1_domain_exact | career/business_milestone_major |
| 53 | 63e90113-… | 2024-07-01 | spiritual | spiritual/practice_intensification | spiritual_turn | EXACT | tier1_domain_exact | spiritual/practice_intensification |
| 54 | d81fae4e-… | 2025-05-15 | loss | loss/financial_deception | financial_deception | EXACT | tier1_domain_exact | loss/financial_deception |
| 55 | 275b0c18-… | 2025-06-15 | spiritual | spiritual/ritual_infrastructure | spiritual_turn | EXACT | tier1_domain_exact | spiritual/ritual_infrastructure |
| 56 | a95552d7-… | 2025-07-01 | health | health/chronic_resolution | chronic_onset | EXACT | tier1_domain_exact | health/chronic_resolution |
| 57 | acb209c7-… | 2025-07-01 | spiritual | spiritual/devotional_shift | spiritual_turn | EXACT | tier1_domain_exact | spiritual/devotional_shift |
| 58 | 4018cc05-… | 2025-07-15 | finance | finance/business_milestone_windfall | major_gain | EXACT | tier1_domain_exact | finance/business_milestone_windfall |
| 59 | 3ea3a2fc-… | 2025-11-15 | spiritual | spiritual/devata_adoption | spiritual_turn | EXACT | tier1_domain_exact | spiritual/devata_adoption |
| 60 | 2bfb5b17-… | 2026-01-15 | other | other/psychological_shift | psychological_arc | EXACT | tier1_domain_exact | other/psychological_shift |
| 61 | 153d920e-… | 2026-03-20 | career | career/business_project_closed | career_setback | EXACT | tier1_domain_exact | career/business_project_closed |
| 62 | 732a4119-… | 2026-04-08 | career | career/business_milestone_clearance | career_advancement | EXACT | tier1_domain_exact | career/business_milestone_clearance |
| 63 | 1f9c6775-… | 2026-04-17 | relationship | relationship/marital_status_current | separation | EXACT | tier1_domain_exact | relationship/marital_status_current |
| 64 | 5278d97c-… | 2026-08-01 | travel_event | travel (domain=`travel`) | travel_event | KEYWORD | tier2_single_candidate | category='travel_event' |

---

## AMBIGUOUS rows (1) — reasons listed; conductor to PARK

| # | event_id | category | domain | candidates | reason |
|---|---|---|---|---|---|
| 1 | 928a1f56-…-fs | residential+travel | NULL | relocation, foreign_settlement | R15 shadow row: domain is NULL (no domain string provided for this synthetic row). The two candidate classes are both legitimate for a `residential+travel` category event. With no domain text to inspect, the resolver cannot deterministically choose between relocation (4th/3rd house; temporary return) and foreign_settlement (12th/9th; established abroad). The native's actual US stint is classified as `foreign_settlement` on the primary row (row 39); this shadow row's class assignment awaits native clarification or conductor ledgering as PARKED. |

---

## Coverage assertion verification

```
classified (63) + ambiguous (1) = 64 total rows
assert_coverage() passed (no silent drops)
63 == 64 - 1 AMBIGUOUS
```

---

## Resolver design summary

**Module:** `platform/python-sidecar/brahmagyan/lel_event_class_resolver.py`
**Version:** `l0f_v1.0`
**Type:** Deterministic rule/lookup — NO LLM calls, NO fuzzy matching.

### Two-tier rule architecture

**Tier 1 — domain exact match (`DOMAIN_TO_EVENT_CLASS`):**
50 evidence-cited domain strings mapped to event_class_ids. Each entry cites the classical reasoning (BPHS chapter, ontology adjacency, or documented ruling). Example: `"family/marriage" → "marriage"` (the F-1 documented category mismatch from `event_class_resolution.ts`, resolved here by domain not category).

**Tier 2 — category + keyword disambiguation:**
Falls through when domain is NULL or not in the tier-1 table. Two sub-steps:
- Single-candidate: if the category maps to only one event class (e.g. `spiritual` → only `spiritual_turn`), resolves with `confidence=KEYWORD`.
- Keyword-assisted: substring search against domain for ordered, specific-first keywords. Keywords are plain substring (not `\b`-bounded) because domain values use underscores which are Python word-chars.

### Circularity guard (R16 / CRITICAL RAIL)

This resolver feeds SCORING only. It is explicitly not wired into:
- `ka_kshetra` or any bodha-layer field inputs
- `chart_facts` (L1 is sealed, R19)
- Any interpretive layer table

---

## Migration number claimed

**553** (`platform/supabase/migrations/553_lel_event_class_resolution.sql`)

Side table `lel_event_class_resolution(chart_id, event_id, resolved_event_class, confidence, rule_matched, matched_tokens, candidates, resolver_version, audit_trail, resolved_at)`.
Unique on `(chart_id, event_id)`. ON CONFLICT DO UPDATE.
CHECK constraints: confidence IN ('EXACT','KEYWORD','AMBIGUOUS'); resolved_event_class NULL iff AMBIGUOUS.

---

## Test suite

`platform/python-sidecar/tests/test_lel_event_class_resolver.py` — 53 tests, all PASS.

| Test class | Coverage |
|---|---|
| TestTier1DomainExactMatch | All DOMAIN_TO_EVENT_CLASS keys resolve EXACT; all values valid |
| TestTier2SingleCandidate | Single-candidate categories resolve KEYWORD without domain |
| TestTier2KeywordDisambiguation | Keyword rules disambiguate within multi-candidate categories |
| TestUnknownCategoryIsAmbiguous | Unknown/empty category → AMBIGUOUS, not a guess |
| TestNullDomainFallthrough | NULL domain falls through to tier-2 correctly |
| TestAuditTrail | Audit trail dict has all required keys |
| TestOutputClassesExistInOntology | All resolved classes exist in EVENT_CLASSES |
| TestCoverageAssertion | assert_coverage raises on count mismatch or missing event_id |
| TestResolveBatch | Length/order preserved; ambiguous rows don't raise |
| Canonical chart fixture tests | 64-row fixture; coverage assertion; all classes valid; AMBIGUOUS listed |

---

*End of L0F_RESOLVER_BACKFILL_PREVIEW_v1_0.md*
