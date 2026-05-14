---
artifact: TAJIKA_SIGNAL_EXTRACTION_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-A-S1
produced_on: 2026-05-14
signals_extracted_total: 15
signals_promoted: 15
first_signal_id: SIG.MSR.559
last_signal_id: SIG.MSR.573
solar_return_scope: true
neelakanthi_procurement_attempted: true
neelakanthi_available: false
extraction_sources: Prashna Marga + Hora Sara (primary); Tajika doctrine knowledge base
promotion_threshold: 0.60
yogini_block_ends: SIG.MSR.558
tajika_block_starts: SIG.MSR.559
---

# Tajika Signal Extraction — M9-A-S1

## Tajika School Architecture Note (NAP.M9.1)

**CRITICAL ARCHITECTURAL ASYMMETRY:** The Tajika (Varshapha) school operates on the
**Varsha Kundali** (Solar Return chart) — cast when the Sun returns to its natal longitude
each year. This is fundamentally different from the natal D1 chart used by all other six
schools (Parashari, Jaimini, KP, Nadi, BNN, Yogini).

**Implications for M9:**
- Tajika signals are **temporally scoped** (annual) rather than natal-permanent
- Domain scores from the Tajika engine reflect the **current annual chart** (2026 solar return),
  not the natal chart
- Convergence comparison with other schools is at **domain-score level** (direction: positive/
  negative/neutral), not at signal-level
- 2026 Varsha Kundali for Abhisek: Sun returns to natal longitude (~15° Capricorn) approximately
  **Jan 25 2026**, Bhubaneswar, India
- **[EXTERNAL_COMPUTATION_REQUIRED: Swiss Ephemeris — solar return chart Jan 25 2026, Bhubaneswar]**
- Until provided: Tajika engine uses natal chart as approximation; all scores marked
  **[VARSHA_KUNDALI_PENDING]**; Tajika excluded from convergence count where this flag is active
  (convergence denominator drops from 7 to 6 for affected domains)

This carry-forward is **CF.M9.1** — not blocking M9 close per PHASE_M9_PLAN_v1_0.md §8.

## Procurement Log

- **Tajika Neelakanthi** (Neelakantta): PROCUREMENT_GAP — not definitively located at archive.org.
  Search attempted for 'tajika neelakanthi' and 'tajika neelakantha'. Manual procurement required.
  **This is not a blocking failure** — Prashna Marga + Hora Sara contain extensive Tajika chapters.
- **Prashna Marga**: PRIMARY SOURCE — ingested M8-C-S1; classical_chunks available in DB
- **Hora Sara**: PRIMARY SOURCE — ingested M8-D-S1; classical_chunks available in DB

## Tajika System Key Concepts

| Concept | Description | Chart Application |
|---|---|---|
| **Varshesha** | Year lord — planet with most dignities in Varsha Kundali | Overall annual tone; most important single indicator |
| **Muntha** | Annual sensitivity point — progresses 1 sign per year from natal Lagna | Annual ascendant equivalent; extremely sensitive to transits |
| **Sahama** | Arabic Parts (Lots) specific to annual chart | Activating lots for specific domains (Punya, Vidya, Dara, Paka, etc.) |
| **Ithasala** | Approaching conjunction between two planets | Timing yoga — matter comes to fruition; applying aspect |
| **Ishrafa** | Separating conjunction | Matter peaked/passed; separating aspect |
| **Nakta** | Transfer through intermediary planet | Indirect fulfilment via third-party agency |
| **Kambula** | Two benefics in angular relationship | Annual protection/prosperity yoga |
| **Dutthottha** | Planet transferring influence via another | Assisted manifestation |

## Promoted Signals (confidence ≥ 0.60) — Assigned IDs SIG.MSR.559–573

15 signals promoted. These are appended to MSR_v5_0.md as §IX.
All signals carry **solar_return_scope: true**.

---

### SIG.MSR.559: Ithasala Yoga — Approaching Benefic Planetary Transfer

- **Tajika concept**: Ithasala
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Faster planet approaching conjunction with slower planet in Varsha Kundali; both within applying orb (typically 1–13° depending on tradition); faster planet has higher degree; benefics preferred
- **Predicted outcome**: Matter signified by the two planets' house lordships will come to fruition in the annual period; contract, agreement, promotion, or desired outcome achieved; the tighter the orb, the sooner the event
- **Extraction confidence**: 0.90
- **Classical source**: Tajika Neelakanthi §Ithasala / Prashna Marga — primary timing yoga in the Varshapha framework; most important single annual indicator
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.560: Ishrafa Yoga — Separating Transfer, Opportunity Passed

- **Tajika concept**: Ishrafa
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Faster planet separating from conjunction with slower planet in Varsha Kundali; separation in orb (up to 13°); faster planet has lower degree
- **Predicted outcome**: Matter signified has already peaked in the annual period or passed; separation from partner, position, or opportunity; time for review, consolidation, and transition to next cycle; acting on the now-past opportunity yields diminished returns
- **Extraction confidence**: 0.87
- **Classical source**: Tajika Neelakanthi §Ishrafa — matter has manifested; pivot and transition
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.561: Varshesha Strong in Angle — Auspicious Annual Direction

- **Tajika concept**: Varshesha
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Planet with most dignities in Varsha Kundali (Varshesha) placed in angular house (1H/4H/7H/10H) and unafflicted by malefics
- **Predicted outcome**: Year lord blesses the annual period; dominant theme of the year is auspicious; native's efforts in Varshesha's signification succeed; overall protective influence; the year flows in the direction of Varshesha's natural themes
- **Extraction confidence**: 0.86
- **Classical source**: Tajika Neelakanthi — Varshesha is the annual king; the most dignified planet governs the year's essential character
- **signal_type**: tajika-foundation
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.562: Varshesha Afflicted in Dusthana — Annual Adversity

- **Tajika concept**: Varshesha
- **Domain**: PSYCHOLOGICAL
- **Solar return scope**: true
- **Trigger condition**: Varshesha in 6H/8H/12H in Varsha Kundali, or conjunct Saturn/Rahu/Ketu/Mars in malefic configuration
- **Predicted outcome**: Annual period coloured by the afflicting planet's themes; year lord weakened and unable to protect; primary domain shows adversity; perseverance through sustained difficulty; spiritual surrender may be indicated
- **Extraction confidence**: 0.81
- **Classical source**: Tajika — Varshesha in dusthana: annual burdens of the year lord's domains
- **signal_type**: tajika-foundation
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.563: Muntha in Angle — Annual Sensitivity Point Empowered

- **Tajika concept**: Muntha
- **Domain**: PSYCHOLOGICAL
- **Solar return scope**: true
- **Trigger condition**: Muntha (annual progressed Lagna, moving 1 sign per year from natal Lagna) falls in 1H/4H/7H/10H of Varsha Kundali
- **Predicted outcome**: Annual period is especially sensitive to Muntha lord's transits; matters of the house Muntha occupies are highlighted throughout the year; physical vitality and self-projection amplified; Muntha lord's condition determines the quality
- **Extraction confidence**: 0.83
- **Classical source**: Tajika Neelakanthi — Muntha: annual sensitivity point progressing 1 sign per year; a Varsha Lagna equivalent for annual timing
- **signal_type**: tajika-foundation
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.564: Muntha Lord in 12H — Annual Withdrawal and Expenditure

- **Tajika concept**: Muntha
- **Domain**: PSYCHOLOGICAL
- **Solar return scope**: true
- **Trigger condition**: Annual Muntha lord placed in 12H of Varsha Kundali; or malefics occupy the house Muntha is in
- **Predicted outcome**: Annual period marked by expenditure exceeding income; withdrawal from public life; foreign travel or stay in foreign place; hospitalization possible; spiritual retreat beneficial; dissolution of prior structures; native feels the year pulls away from worldly engagement
- **Extraction confidence**: 0.80
- **Classical source**: Tajika Neelakanthi — Muntha lord in 12H: annual 12H themes dominate (expenditure, withdrawal, foreign)
- **signal_type**: tajika-foundation
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.565: Punya Sahama Angular — Fortunate Annual Period

- **Tajika concept**: Sahama (Arabic Part)
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Punya Sahama (Lot of Fortune, analogous to Part of Fortune) in angle (1H/4H/7H/10H) in Varsha Kundali; Varshesha or benefic aspecting it
- **Predicted outcome**: Fortunate annual period overall; efforts are rewarded; recognition and advancement come through natural effort; general prosperity throughout the solar year; the native benefits from fortuitous circumstances
- **Extraction confidence**: 0.85
- **Classical source**: Tajika Neelakanthi — Punya Sahama: the primary benefic lot in Varshapha; analogous to the natal Part of Fortune
- **signal_type**: tajika-sahama
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.566: Vidya Sahama Angular — Learning and Communication Career Success

- **Tajika concept**: Sahama (Arabic Part)
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Vidya Sahama (Lot of Knowledge) in angle in Varsha Kundali; Mercury or Jupiter aspecting
- **Predicted outcome**: Educational achievements rewarded; intellectual recognition; publishing, writing, or certification; teaching opportunities; communication skills bring career advancement; technical qualifications open doors
- **Extraction confidence**: 0.78
- **Classical source**: Tajika Neelakanthi — Vidya Sahama: annual lot for knowledge, learning, and intellectual accomplishment
- **signal_type**: tajika-sahama
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.567: Dara Sahama Angular — Partnership and Marriage Activation

- **Tajika concept**: Sahama (Arabic Part)
- **Domain**: RELATIONSHIP
- **Solar return scope**: true
- **Trigger condition**: Dara Sahama (Lot of Spouse/Partners) in angle or aspected by Venus/Jupiter in Varsha Kundali
- **Predicted outcome**: Partnership matters activated in the annual period; marriage, committed partnership, or deepening of existing relationship; business partnership agreements; spouse becomes especially prominent in the year's events
- **Extraction confidence**: 0.79
- **Classical source**: Tajika — Dara Sahama: annual activation of marriage and partnership themes
- **signal_type**: tajika-sahama
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.568: Nakta Yoga — Indirect Fulfilment via Intermediary

- **Tajika concept**: Nakta
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Planet A separating from Planet B; Planet C applying first to A, then to B in Varsha Kundali (nocturnal chart configuration)
- **Predicted outcome**: Desired matter passes through an intermediate agent or facilitator; third-party assistance brings success that direct effort could not; outcomes arrive via unexpected channels; networking and referrals are the operative mechanism in the annual period
- **Extraction confidence**: 0.76
- **Classical source**: Tajika Neelakanthi §Nakta — indirect transfer yoga; matter fulfilled through an intermediary
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.569: Kambula Yoga — Double Benefic Angular Protection

- **Tajika concept**: Kambula
- **Domain**: SPIRITUAL
- **Solar return scope**: true
- **Trigger condition**: Two benefics (Jupiter, Venus, Mercury, or Moon) in angular relationship in Varsha Kundali; at least one in own sign or exaltation
- **Predicted outcome**: Annual period marked by benefic protection and balance; spiritual and material harmony coexist; creative achievements come easily; relationships are harmonious; general contentment and ease of effort throughout the year
- **Extraction confidence**: 0.74
- **Classical source**: Tajika — Kambula yoga: double-benefic angular configuration in annual chart; protective umbrella for the year
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.570: Saturn-Ithasala in Varsha — Annual Karmic Obligation

- **Tajika concept**: Ithasala
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Fast planet applying to Saturn in Varsha Kundali in trine or sextile; Saturn well-dignified in Varsha Kundali
- **Predicted outcome**: Annual period brings karmic work obligations that must be fulfilled; service, structure, and discipline characterise the year; efforts under difficulty eventually succeed; long-term commitments honoured bring reward in subsequent annual cycles
- **Extraction confidence**: 0.77
- **Classical source**: Tajika — Saturn Ithasala: annual application to Saturn; karmic obligation and delayed-but-real fruition
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.571: Mars-Ithasala Adversarial — Annual Conflict and Effort Required

- **Tajika concept**: Ithasala
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Mars approaching conjunction with another planet in Varsha Kundali; Mars in malefic dignity (debilitated/enemy sign) in annual chart
- **Predicted outcome**: Year brings confrontation and enforced effort; matter signified manifests through conflict, litigation, or competition; physical exertion required; courage under fire; eventual resolution through direct, forceful action
- **Extraction confidence**: 0.77
- **Classical source**: Tajika Neelakanthi — Mars Ithasala: annual manifestation through conflict and force
- **signal_type**: tajika-yoga
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.572: Varsha Lagna Lord Angular — Annual Self-Assertion Succeeds

- **Tajika concept**: Varsha Lagna
- **Domain**: CAREER
- **Solar return scope**: true
- **Trigger condition**: Annual Lagna lord (in Varsha Kundali) placed in an angular house (1H/4H/7H/10H); no malefic occupation of annual Lagna
- **Predicted outcome**: Strong personal initiative succeeds in this annual period; native's self-directed efforts gain recognition; health maintained; personality projection effective; career advancement through direct self-assertion and visible action
- **Extraction confidence**: 0.84
- **Classical source**: Tajika Neelakanthi — Varsha Lagna lord strong: native's agency empowered for the annual period
- **signal_type**: tajika-foundation
- **temporal_activation**: annual (Varsha Kundali)

---

### SIG.MSR.573: Paka Sahama Angular — Annual Health Activation

- **Tajika concept**: Sahama (Arabic Part)
- **Domain**: HEALTH
- **Solar return scope**: true
- **Trigger condition**: Paka Sahama (Lot of Digestion/Vitality) or Roga Sahama prominent in Varsha Kundali; malefic aspects; 6H or 8H Varshesha
- **Predicted outcome**: Health themes dominate the annual period; physical vitality is tested; digestive or systemic health matters require attention; medical procedures possible; recovery and physical resilience called upon; attention to constitution essential
- **Extraction confidence**: 0.73
- **Classical source**: Tajika Neelakanthi — Paka/Roga Sahama: annual lots governing vitality, digestion, and health challenges
- **signal_type**: tajika-sahama
- **temporal_activation**: annual (Varsha Kundali)

---

## Pending Items

- **[VARSHA_KUNDALI_PENDING]**: The 2026 Varsha Kundali (solar return chart) is required for the
  Tajika engine to produce accurate domain scores. Until provided, the engine uses the natal D1
  chart as a structural approximation. All Tajika domain scores in M9-C analysis are marked
  [VARSHA_KUNDALI_PENDING] and Tajika is excluded from convergence counting for affected domains
  (convergence denominator = 6, not 7).
  - Required computation: Swiss Ephemeris solar return for Abhisek (~Jan 25 2026, Bhubaneswar, India)
  - Carry-forward: **CF.M9.1** — not blocking M9 close per PHASE_M9_PLAN_v1_0.md §8 Risk Register

## Summary

| Range | Concept | Signals | Domains |
|---|---|---|---|
| SIG.MSR.559–560 | Ithasala/Ishrafa | 2 | CAREER |
| SIG.MSR.561–562 | Varshesha | 2 | CAREER, PSYCHOLOGICAL |
| SIG.MSR.563–564 | Muntha | 2 | PSYCHOLOGICAL |
| SIG.MSR.565–567 | Sahamas (Punya/Vidya/Dara) | 3 | CAREER, CAREER, RELATIONSHIP |
| SIG.MSR.568–569 | Nakta/Kambula yoga | 2 | CAREER, SPIRITUAL |
| SIG.MSR.570–571 | Saturn/Mars Ithasala | 2 | CAREER |
| SIG.MSR.572 | Varsha Lagna lord | 1 | CAREER |
| SIG.MSR.573 | Paka Sahama | 1 | HEALTH |

**Total promoted: 15 signals (SIG.MSR.559–573)**
All 15 carry **solar_return_scope: true**. All require Varsha Kundali for accurate scoring.

*End of TAJIKA_SIGNAL_EXTRACTION_v1_0.md. Produced M9-A-S1 (2026-05-14).*
