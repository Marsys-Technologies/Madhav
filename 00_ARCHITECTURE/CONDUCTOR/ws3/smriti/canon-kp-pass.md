---
session: canon-kp
status: PASS
date: 2026-06-05
rules_extracted: 266
rules_stubbed: 14
stub_rate_pct: 5.0
pramana_pass_rate: 0.95
batches_committed: 3
---

# KP Reader Canon Extraction — smriti

## Session summary

Extracted 280 rules from the KP Reader (KSK original series, Volumes 1–6) across
three committed batches. Of 280 rule objects, 266 are verified (stub: false) and
14 are stubs (stub: true). Stub rate: 5.0% — within the Gate A acceptable range (≤15%).

## Batch breakdown

| Batch | File | Rules | STUBs | Commit SHA |
|---|---|---|---|---|
| 1 | kp_canon_batch_01.yaml | 100 | 5 | c78cefe5 |
| 2 | kp_canon_batch_02.yaml | 100 | 5 | 5fb6bf6c |
| 3 | kp_canon_batch_03.yaml | 80 | 4 | fe8f98ad |

Total: 280 rules, 14 stubs.

## Gate A improvements applied

- **R1 (Rahu/Ketu confidence)**: All Rahu/Ketu rules had confidence × 0.85 applied.
  Rules with Rahu/Ketu have effective confidence ranging from 0.61 to 0.71 depending
  on textual strength. See kp_canon_batch_01.yaml rule_ids ending in .rahu_ketu.*
  and KP.3.ch11.rahu_ketu_transit.1 etc.

- **R3 (Sub-lord conditional assertions)**: All sub-lord rules include the caveat
  "Results depend on sub-lord" in the caveats field, explicitly noting the
  conditional nature of all KP assertions. This appears in 100% of sub_lord
  scope rules.

## Coverage delivered

### Vol 1 — Foundation
- Nakshatra lord, sub-lord, sub-sub-lord (star-sub-sub system): covered
- Vimshottari proportions for sub-lord table: covered (KP.1.ch2.sublord_table.1)
- Placidus house system and 1° cusp rule: covered (KP.1.ch3.placidus.1/2)
- Four-tier significator hierarchy: covered (KP.1.ch4.signification.1/2)
- Sub-lord determines results: covered (KP.1.ch5.sublord_result.1/2)
- Sub-lord primacy axiom: covered (KP.1.ch17.sublord_primacy_axiom.1)
- KP reading sequence: covered (KP.1.ch16.reading_sequence.1)

### Vol 2 — Cusps and Sub-Lords
- 12th-from-cusp denial rule: covered (KP.2.ch1.cusp_sublord.1/3)
- Self-referential sub-lord promise: covered (KP.2.ch1.cusp_sublord.2)
- Significator hierarchy detail: covered (KP.2.ch2.significator_hierarchy.1/2)
- Retrograde planet sub-correction: covered (KP.2.ch4.retrograde.1/2)
- Promise vs. timing distinction: covered (KP.2.ch16.promise_vs_timing.1)

### Vol 3 — Event Timing
- Triple-significator dasha rule: covered (KP.3.ch1.dasha_timing.1/2/3)
- Transit via nakshatra (not sign): covered (KP.3.ch2.transit.1/2)
- KP ruling planets: covered (KP.3.ch3.ruling_planets.1/2)
- Antara/sookshma precision: covered (KP.3.ch4.antara_timing.1, KP.3.ch14.sookshma.1)
- Six-step complete dasha protocol: covered (KP.3.ch22.cusp_sublord_transit.1,
  KP.3.ch21.dasha_sequence_check.1)

### Vol 4–5 — Specific Topics
- Marriage (2/7/11): covered (KP.4.ch1.marriage.1/2/3/4)
- Career (2/6/10): covered (KP.4.ch2.career.1/2/3)
- Foreign travel (3/9/12): covered (KP.4.ch3.foreign_travel.1/2)
- Health/disease (1/6/8/12): covered (KP.4.ch4.health.1/2)
- Death timing (sub-lord of 8th + badhaka/maraka): covered (KP.4.ch5.death.1/2)
- Children (2/5/11): covered (KP.5.ch1.children.1/2/3)
- All 12 house groups: covered across batches 1–3
- Education, property, finance, speculation, inheritance: covered

### Vol 6 — Advanced
- Horary number 1–249 system: covered (KP.6.ch1.horary.1/2/3)
- KP Moon chart / Bhava Chalit: covered (KP.6.ch2.moon_chart.1/2)
- Retrograde in previous star's sub: covered (KP.2.ch4.retrograde.1/2)
- Affirmative/negative horary answer: covered (KP.6.ch9.horary_affirmative.1,
  KP.6.ch9.horary_negative.1)
- Ruling planets at time of judgment: covered (KP.3.ch3.ruling_planets.1/2,
  KP.3.ch12.ruling_planet_selection.1/2)

## Key KP divergences from Parashari documented

The following are the most significant school divergences captured in this extraction,
important for the MARSYS school_convergence_index and cross-school analysis:

1. **Placidus vs. equal-house**: KP uses Placidus (cusps = house beginnings);
   Parashari typically uses Sripati or equal-house. Planets near cusps shift houses.
   Rules: KP.1.ch3.placidus.1/2, KP.6.ch2.moon_chart.1/2.

2. **Bhava Chalit for house placement**: KP uses Bhava Chalit chart for house
   signification; Parashari uses Rasi sign = house. A planet can be in Aries (Rasi)
   but in 12H (Bhava Chalit). Rules: KP.1.ch9.sign_vs_house.1, KP.6.ch2.moon_chart.1/2.

3. **Sub-lord primacy overrides dignity, yogas, karakas**: In KP, the sub-lord
   of a cusp overrides exaltation, Neecha Bhanga, natural karaka status, and all
   Parashari yogas. Rules: KP.1.ch17, KP.1.ch10.no_yoga_analysis.1,
   KP.1.ch11.no_dosha.1, KP.1.ch23.neecha_bhanga.1.

4. **No Parashari yogas or doshas**: Rajayoga, Gajakesari, Mangal Dosha, Kalsarpa
   Dosha etc. are explicitly excluded from KP analysis.
   Rules: KP.1.ch10.no_yoga_analysis.1, KP.1.ch11.no_dosha.1.

5. **No ashtakavarga for transit**: Transit assessed by nakshatra-of-significator,
   not sign-from-Moon or benefic dot counts. Rules: KP.2.ch11.no_ashtakavarga.1,
   KP.3.ch2.transit.1/2.

6. **No divisional charts as primary tools**: Navamsa and other D-charts are
   secondary (confirming) tools, not primary predictors. Rule: KP.3.ch13.no_navamsa.1.

7. **Rahu/Ketu are agents of star lord**: In KP, Rahu and Ketu deliver their
   star lord's results (not independent malefic results as in Parashari).
   Conjunction overrides star lord for Rahu. Rules: KP.6.ch3.rahu_ketu.1/2/3.

8. **Retrograde planet = previous star's sub**: KP corrects retrograde planet
   sub-lord to the preceding star's last sub. No Parashari equivalent.
   Rules: KP.2.ch4.retrograde.1/2.

9. **Krishnamurti ayanamsha (not Lahiri)**: KP uses Krishnamurti ayanamsha,
   differing from Lahiri by ~6 arc minutes. Rule: KP.1.ch18.nirayana.1.

10. **KP Prashna uses 1-249 number**: Horary based on querent-given number
    mapping to zodiacal degrees, not Prashna lagna cast from current time.
    Rules: KP.6.ch1.horary.1/2/3.

## Quality bar assessment

- pramana_pass_rate: 0.95 (95% of rules have both condition and assertion
  provably derivable from text_excerpt; 5% are stubs with documented reasons)
- No rule fabricates specifics absent from text_excerpt
- All Rahu/Ketu rules apply the × 0.85 Gate A R1 correction
- All sub-lord rules include explicit "results depend on sub-lord" caveat (R3)
- Minimum confidence 0.30 maintained across all stubs
- No rule exceeds confidence 0.95 (cap applied to cross-text 1.15× boost cases)
- Cross-school divergences from Parashari explicitly flagged in caveats
- school_convergence_index conflict points identified in caveats for MARSYS use

## Stub analysis

14 stubs across 3 batches (5.0% stub rate):

1. KP.6.ch6.electional.STUB.1 — muhurta activity-specific rules deferred to Vol.5
2. KP.5.ch7.longevity.STUB.1 — positive longevity procedure absent; covered by death rules
3. KP.6.ch7.nadi_integration.STUB.1 — intellectual history only, no predictive rule
4. KP.4.ch9.divorce.STUB.1 — redundant with marriage denial rules; fuller rule needed
5. KP.3.ch8.bhava_chalit_shifting.STUB.1 — practitioner variation explicitly acknowledged
6. KP.6.ch14.prashna_competitors.STUB.1 — competition type differentiation absent
7. KP.5.ch14.secret_enemies.STUB.1 — Rahu amplification assertion incomplete
8. KP.4.ch16.government_trouble.STUB.1 — primary cusp reference ambiguous
9. KP.3.ch17.prana_sookshma.STUB.1 — theoretical only per KSK statement
10. KP.2.ch17.cusp_outside_sign.STUB.1 — non-standardised per KSK
11. KP.6.ch19.prashna_court_case.STUB.1 — plaintiff/defendant differentiation absent
12. KP.5.ch21.sports_career.STUB.1 — sport-specific extensions not enumerated
13. KP.4.ch23.business_failure.STUB.1 — sequencing complexity explicitly deferred
14. KP.1.ch26.contradictory_sublords.STUB.1 — resolution rules deferred to examples

## Notes for orchestrator

KP Reader (KSK original) is the most divergent of the four WS-3 source texts from
Parashari tradition. The extraction captures the full distinctive architecture of
the KP system: the sub-lord primacy principle, the four-tier significator hierarchy,
Placidus/Bhava Chalit house placement, nakshatra-based transit, the 1-249 horary
number system, and explicit KP exclusions (no yogas, no doshas, no ashtakavarga,
no primary divisional charts, no Neecha Bhanga, no Parashari aspects).

These divergences are systematically documented in rule caveats and in the divergences
section above. All represent potential CONFLICT type entries in the MARSYS
school_convergence_index when KP and Parashari predictions for the same chart
configuration point in different directions.

The retrograde correction (KP.2.ch4), the Rahu/Ketu stellar-agent rules
(KP.6.ch3), and the Bhava Chalit house placement rules (KP.6.ch2, KP.1.ch9)
are the three KP-unique mechanisms with the highest practical impact on prediction
outcomes and therefore the most important to represent accurately in cross-school
comparison.
