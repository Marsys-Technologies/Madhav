---
artifact: RM_v2_0.md
artifact_type: Resonance Map
layer: L2.5 — Holistic Synthesis
version: 2.2
status: CURRENT
date_opened: 2026-04-18
supersedes: RM_v1_1.md
session: FIX_SESSION_003_deferred
parent_artifacts: [MSR_v1_0.md, CDLM_v1_1.md, CGM_v1_0.md, FORENSIC_ASTROLOGICAL_DATA_v8_0.md]
feeds_into: [Domain Reports L3, future UCN v2.0]
native: Abhisek Mohanty, b. 1984-02-05, 10:43 IST, Bhubaneswar
schema_ref: Architecture §C.3.4, §D.4.D, §G.4.D
v2_1_changelog: "Corrective text stripped 2026-04-19 per corpus cleanup brief. See 00_ARCHITECTURE/AUDIT_REPORT_v1_0.md for history."
v2_2_changelog: "VARGA-ETL-FULL-S1 D14 (2026-05-10): added RM.31–RM.35 — five cross-varga resonances anchored in MSR.500–514 (vargottama Mercury, Saturn three-state, Venus three-state, D9 12H stellium, D10 career triad). Brief specified RM.30–34 but RM.30 already occupied by v2.0 Chart's Central Paradox Stack; new entries indexed RM.31–RM.35 to avoid collision."
expose_to_chat: true
native_id: "abhisek"
---

# MARSYS-JIS — Resonance Map v2.1
## Abhisek Mohanty Jyotish Intelligence System
### 2026-04-18 | FIX_SESSION_003_deferred

---

## §0 — LAGNA AND SAHAM FOUNDATION

All RM v2.1 element blocks use the Special Lagna and Saham architecture from FORENSIC_ASTROLOGICAL_DATA_v8_0.md.

**Special Lagnas**:
- Vighati Lagna: Leo 5H Purva Phalguni Pada 3
- Pranapada Lagna: Leo 5H Purva Phalguni Pada 3
- Indu Lagna: Scorpio 8H Jyeshtha Pada 4

**Sahams**:
- Saham Roga: Taurus 2H Mrigashira
- Saham Mahatmya: Sagittarius 9H
- Saham Vivaha: Cancer 4H

**Planetary aspect foundation (unchanged from v1.1)**:
- Jupiter (Sagittarius 9H): 5th→1H, 7th→3H, 9th→5H (does NOT aspect 4H/8H/10H/12H)
- Saturn (Libra 7H): 3rd→9H, 7th→1H, 10th→4H
- Mars (Libra 7H): 4th→10H, 7th→1H, 8th→2H
- Mercury (Capricorn 10H): 7th→4H
- Sun (Capricorn 10H): 7th→4H
- Moon (Aquarius 11H): 7th→5H
- Rahu (Taurus 2H): 5th→6H, 7th→8H, 9th→10H
- Ketu (Scorpio 8H): 5th→12H, 7th→2H, 9th→4H
- Venus (Sagittarius 9H): 7th→3H

---

## §1 — ELEMENT BLOCKS (32 ENTRIES)

32 elements: 30 from v1.1 (23 unchanged + 7 corrected), plus 2 new elements (Ghati Lagna 9H, Varnada Lagna 4H) replacing the invalidated RM.21.

---

### RM.01 — Mercury 10H Capricorn (Primary Instrument) [v2.0: eight-system updated]

```yaml
element: "Mercury Eight-System Convergence — chart's primary operational instrument"
domains_primary: [D1, D2, D3, D8, D9]
msr_anchors: [MSR.413, MSR.190]
cdlm_anchors: [D8.D8=0.95 self-amp, D8.D1=0.94, D8.D2=0.92]
constructive_resonance:
  - Vargottama (D1 Cap = D9 Cap) = maximum dignity consistency
  - Yogi Planet (Pisces Revati ruler) = fortune-activator
  - DK Chara Karaka = spouse/partnership signifier
  - Karakamsa Gemini lord
  - KP cusp 11 sub-lord
  - MD lord 2010-2027 (current activation window)
  - AL 10H co-location (identity = career)
  - Siva Yoga Lord (8th from Lagna lord Mars = 8th from Mars = Scorpio; Mercury governs the Siva Yoga channel — per FORENSIC v8.0 §15.1)
destructive_resonance:
  - 6L dual-governance — career deployment simultaneously activates 6H disease
  - Susupta/Mrat/Shant avastha — internalized operation (low visibility of effort)
  - Naisargika Bala rank 7 (weakest natural-strength of seven planets)
net_resonance: "STRONGLY AMPLIFIED during Mercury MD; protect 6L boundary"
interpretive_note: "Eight independent systems designate Mercury as primary (updated from seven per FORENSIC v8.0: Siva Yoga Lord added as 8th system). Deploy fully; protect against 6L cognitive-overload manifestation."
```

### RM.02 — Saturn 7H Libra Exalted (Career Lord)

```yaml
element: "Saturn exalted 7H + AmK + Sasha Mahapurusha + 10L+11L + AD lord"
domains_primary: [D1, D3]
msr_anchors: [MSR.391, MSR.052]
constructive_resonance:
  - Exaltation at 22°27' Libra (Uccha Bala 59.18/60 — near-maximum exaltation)
  - AmK (Atmakaraka-bhratru — career-minister soul-election)
  - Sasha Mahapurusha Yoga (Saturn exalted Kendra from Lagna)
  - 10L (career) + 11L (gains) — dual rulership
  - Current AD lord 2024-12-12 → 2027-08-21
  - 7th aspect on 1H Lagna = Saturn-quality structures native's identity
  - 10th aspect on 4H Cancer = Saturn organizes inner sanctuary
  - Co-tenant with Shree Lagna 7H (Lakshmi-grace in same house as career-AmK — v2.0 new finding)
destructive_resonance:
  - BVB 7H rank 12 of 12 (structurally weakest-container house)
  - Conjunct Mars (Avayogi) within 3°56' = ATT tension-architecture
  - 3rd aspect on 9H can dampen dharmic-expansiveness
net_resonance: "STRONGLY AMPLIFIED — quintessential authority architecture (ATT)"
interpretive_note: "Saturn's structural authority is the chart's authority delivery mechanism. Pressure is the medium, not the obstacle. v2.0: Saturn now shares 7H with Shree Lagna — career-AmK and Lakshmi-grace co-reside in the relationship house."
```

### RM.03 — Jupiter 9H Sagittarius Own Sign (Dharma Lord)

```yaml
element: "Jupiter 9L own sign + 12L + GK Chara Karaka"
domains_primary: [D6, D1, D2, D7]
msr_anchors: [MSR.089 (Moolatrikona-band variance), MSR.407 (9H Laxmi-Narayana-adjacent)]
constructive_resonance:
  - Own sign (swakshetra) in own house (swabhava) = purest classical dignity
  - 9L (dharma-lord) + 12L (moksha-lord) dual rulership
  - 5th special aspect on 1H Lagna = Jupiter blesses identity directly
  - 7th full aspect on 3H = Jupiter blesses UL-house / partnership-image domain
  - 9th special aspect on 5H Leo = Jupiter blesses creativity/children house
  - GK Chara Karaka — resources/rivals-through-wisdom
  - Conjunct Venus (2L+7L+MK) within 10° = Jupiter-Venus 9H dharmic-wealth-aesthetic cluster
  - Ghati Lagna in 9H = Ghati Lagna co-tenancy with Jupiter+Venus = power-timing point in dharma house
destructive_resonance:
  - Uccha Bala rank 7 of 7 (maximum zodiacal distance from Cancer 5° exaltation point)
  - GK Chara role classically carries "rival/obstacle" quality
  - Moola nakshatra Pada 3 (Ketu-ruled, transformational destabilization)
  - Naisargika Bala weakest in chart
net_resonance: "STRONGLY AMPLIFIED by dignity; Uccha-Bala weakness requires active dharmic engagement"
interpretive_note: "Dignity-strong-by-sign; Uccha-Bala-weak-by-metric. Ghati Lagna in 9H Sagittarius adds temporal-power dimension to Jupiter's dharmic authority."
```

### RM.04 — Venus 9H Sagittarius (Relational Significator)

```yaml
element: "Venus 2L+7L+MK in 9H with Jupiter"
domains_primary: [D3, D2, D7]
msr_anchors: [MSR.342, MSR.407]
cdlm_anchors: [D3.D2=0.87, D2.D3=0.89]
constructive_resonance:
  - In Jupiter's sign Sagittarius (dharmic-host)
  - 7L = relationship-lord with 2L = wealth-lord dual rulership
  - MK Chara Karaka — mother-significator
  - Conjunct Jupiter within 10° = Laxmi-Narayana-adjacent
  - Purva Ashadha Pada 2 (Venus's own nakshatra pada)
  - Saham Mahatmya in 9H (confirmed in v8.0) = fame/honor saham in same house as Venus
destructive_resonance:
  - D9 Virgo debilitation (confirmed GAP.02b via JHora)
  - 6L wife's-health nadir in D9
  - Paksha Bala low (Krishna Paksha waxing phase)
net_resonance: "BENEFIC BUT D9-DEBILITATED — dharmic alignment compensates D9 weakness"
interpretive_note: "Relationships require dharmic framing and active structural effort. Saham Mahatmya (honor/fame) in 9H with Venus — the fame dimension is dharmic-spiritual, not career-only."
```

### RM.05 — Moon 11H Aquarius Purva Bhadrapada (Soul/AK)

```yaml
element: "Moon AK + 4L Cancer-lord-from-distance + Purva Bhadrapada Pada 3"
domains_primary: [D8, D6, D7]
msr_anchors: [MSR.374, MSR.406]
cdlm_anchors: [D8.D8=0.95, D6.D8=0.88]
constructive_resonance:
  - AK (Atmakaraka) — soul's primary significator
  - Highest longitude among 7 planets (27°02' Aquarius)
  - Jaimini Rashi Drishti from fixed-sign Aquarius → 1H Aries + 4H Cancer + 7H Libra (all relational cardinal)
  - Purva Bhadrapada Pada 3 (Jupiter-ruled nakshatra) = philosophical-intuitive depth
  - A7 co-location in same 11H = soul-partnership alignment
destructive_resonance:
  - 4L in 11H = mother-significator far from mother's house
  - Mandi shadow on 4H sanctuary
  - Susupta/Mrat/Shant avastha — deep-sleep internalization
  - Saham Labha in 9H (gains-wealth ideation in dharmic house)
  - Shadbala rank 4 (moderate strength)
net_resonance: "STRONGLY AMPLIFIED — soul and mind co-identified in Moon"
interpretive_note: "The soul inhabits the community-gains house. Purposeful community is the soul's nourishment; casual social is insufficient."
```

### RM.06 — Mars 7H Libra (Avayogi + Lagna Lord)

```yaml
element: "Mars Lagna-lord + PK + Avayogi in 7H enemy-sign"
domains_primary: [D3, D1, D4]
msr_anchors: [MSR.391, MSR.398]
cdlm_anchors: [D3.D3=0.93, D3.D4=0.68]
constructive_resonance:
  - Lagna-lord in 7H = self-identity-through-relationship
  - PK Chara Karaka — children signifier
  - Swati Pada 4 (Mars-own-pada in Rahu-nakshatra)
  - 4th aspect on 10H = Mars drives career (Lagna-lord acting on career-house)
  - 7th aspect on 1H = Mars reinforces Lagna-lord-bhava
destructive_resonance:
  - Libra enemy-sign (Mars debilitation is Cancer; Libra is Mars's enemy-sign Venus-ruled)
  - Avayogi (fortune-reducer) designation
  - Conjunct exalted Saturn (ATT tension)
  - 8th aspect on 2H Rahu = triggers financial-disruption potential
net_resonance: "TENSION-BEARING — ATT's productive tension mechanism"
interpretive_note: "Most tension-bearing element in the chart. Not eliminable. Channel via physical-discipline; hold tension within Saturn's structural frame."
```

### RM.07 — Sun 10H Capricorn (Career-Authority)

```yaml
element: "Sun Shadbala #1 + Dig Bala max + Budh-Aditya Yoga + 5L"
domains_primary: [D1, D5, D7]
msr_anchors: [MSR.019, MSR.025]
cdlm_anchors: [D1.D5=0.72, D7.D1=0.80]
constructive_resonance:
  - Shadbala rank 1 total strength (8.51 rupas) per FORENSIC engine
  - Dig Bala maximum 60 virupa (Sun in 10H Kendra = optimal directional strength)
  - Budh-Aditya Yoga with Mercury (non-combust)
  - 5L = creativity/intelligence-lord
  - Shravana Pada 4 (Moon-nakshatra, gives emotional-communicative quality)
destructive_resonance:
  - Capricorn = Saturn's sign = Sun's enemy-sign
  - Uccha Bala rank 2 (closer to debilitation point Libra 10° than to exaltation Aries 10°)
  - Dual-engine Shadbala variance (GAP.07 — JHora ranks Sun #2, Saturn #1)
net_resonance: "AMPLIFIED via Dig Bala + Budh-Aditya; Saturnized expression"
interpretive_note: "Solar authority via Saturnian structure — earned through discipline, not natural radiance."
```


```yaml
element: "Rahu in 2H Venus-sign + Rohini Pada 3 + Roga Saham co-tenancy"
domains_primary: [D2, D3, D9]
msr_anchors: [MSR.053, MSR.369]
cdlm_anchors: [D2.D9=0.88]
constructive_resonance:
  - Taurus = Venus-ruled = Rahu comfortable in material-wealth sign (some classical: Rahu's exaltation)
  - 2H = family/wealth/speech learning frontier
  - Rohini Pada 3 (high-craving intensification)
  - 5th aspect on 6H (Virgo) Mercury-sign — karmic lesson visible in 6H service domain
  - 9th aspect on 10H — ambition feeds career
  - Saham Roga in 2H Taurus (co-tenant with Rahu): health challenges emerge from 2H domain (speech, diet, Vata constitution) not from 7H relationship context
destructive_resonance:
  - Nodal-Moon-Rahu axis (Bhrigu Bindu from Moon+Rahu midpoint)
  - Rahu-Roga co-tenancy in 2H = Vata/nervous-system/diet health channel is Rahu-amplified
  - Rahu-Ketu axis amplifies both node-themes
net_resonance: "AMPLIFIED karmic-learning intensity in 2H material accumulation"
interpretive_note: "Rahu 2H = patient material-foundation as this-life curriculum. Saham Roga in 2H Taurus routes health challenges through the Vata-constitution-diet-speech channel, co-amplified by Rahu. Avoid speculation AND address dietary/Vata patterns."
```

### RM.09 — Ketu 8H Scorpio (Moksha-Karaka)

```yaml
element: "Ketu exalted 8H Scorpio + Jyeshtha Pada 1 + Indu Lagna"
domains_primary: [D6, D8, D4]
msr_anchors: [MSR.335, MSR.402]
cdlm_anchors: [D6.D8=0.88, D4.D6=0.82]
constructive_resonance:
  - Scorpio (Mars-ruled) = Ketu's exaltation per most traditions
  - 8H transformation-house = Ketu's natural domain
  - Jyeshtha Pada 1 (Mercury-nakshatra)
  - 5th aspect on 12H moksha-house = moksha-karaka aspects moksha-house
  - 7th aspect on 2H Rahu = nodal axis cross-aspect
  - 9th aspect on 4H Cancer = moksha-quality touches sanctuary
  - Indu Lagna in 8H Scorpio (new in v8.0) = wealth-from-Moon indicator in transformation house
destructive_resonance:
  - Nodal-axis inherent retrograde
  - 8H as longevity-house carries inherent stress
  - Gandanta-proximal at Jyeshtha end
net_resonance: "STRONGLY AMPLIFIED — hidden-pinnacle moksha architecture"
interpretive_note: "Ketu MD 2031-2038 is the chart's deepest authority activation. v2.0: Indu Lagna (Moon-based wealth indicator) confirmed in 8H Jyeshtha — wealth through transformation/hidden channels is an additional 8H theme."
```

### RM.10 — Ascendant Aries 12°23'55" Ashwini Pada 4

```yaml
element: "Lagna Aries Ashwini Pada 4"
domains_primary: [D1, D4, D8]
msr_anchors: [MSR.001, MSR.015]
cdlm_anchors: [D1.D1=1.00]
constructive_resonance:
  - Aries = Mars-ruled fire-sign (Lagna-lord Mars in 7H)
  - Ashwini Pada 4 (Ketu-nakshatra) = transformation-initiator
  - Jupiter 5th aspect from 9H = dharmic blessing on identity
  - Saturn 7th aspect from 7H = structural-discipline shaping identity
  - Mars 7th aspect from 7H = Lagna-lord self-aspect
destructive_resonance:
  - Lagna-lord displaced to 7H = identity depends on relationship-axis
  - Mandi shadow reaches via Saturn-aspect
net_resonance: "STRONGLY STRUCTURED — identity co-built by Mars-Saturn-Jupiter"
interpretive_note: "Empty Lagna but triply-aspected by Mars+Saturn+Jupiter. Identity is architecturally co-constituted by the chart's most significant planets."
```

### RM.11 — Arudha Lagna (AL) Capricorn 10H

```yaml
element: "AL at Capricorn 10H (co-location with Sun+Mercury stellium)"
domains_primary: [D1, D8]
msr_anchors: [MSR.023, MSR.019]
cdlm_anchors: [D1.D8=0.91]
constructive_resonance:
  - Projected-image = career-house = identity perceived as career
  - Co-location with Sun+Mercury = solar-authority + analytical-precision perception
  - Saturn 10th aspect (from 7H Libra) = Saturn-quality external perception
destructive_resonance:
  - Can produce excessive career-identity fusion; risk of over-identification with role
  - Saturn's heavy aspect adds gravitas but also rigidity
net_resonance: "STRONGLY AMPLIFIED — public identity fused with career"
interpretive_note: "The world sees what the career shows. Career shift = identity shift perceptually."
```

### RM.12 — Upapada Lagna (UL) Gemini 3H

```yaml
element: "UL at Gemini 3H + triple-Arudha (UL + A11 + A5) co-location + Hora Lagna"
domains_primary: [D3, D8]
msr_anchors: [MSR.338, MSR.236]
cdlm_anchors: [D3.D3=0.93]
constructive_resonance:
  - Mercury-ruled sign = DK-spouse-karaka resonance (Mercury = DK)
  - Jupiter 7th full aspect from 9H = UL blessed by dharma lord
  - Venus 7th aspect from 9H = UL blessed by Venus Mahalakshmi
  - BB progression at age 42 = Gemini 20°02' (Sensitive-point activation)
  - Hora Lagna in 3H Gemini (v2.0 confirmed) = annual-finance-power point in UL-house
destructive_resonance:
  - 3H effort/agitation house = spouse domain carries activity-intensity
  - Ardra-Pada overlay (Rahu-nakshatra) introduces karmic complication
net_resonance: "STRONGLY AMPLIFIED in 2026 BB-UL convergence window"
```

### RM.13 — 4H Cancer (Mother / Sanctuary / Varnada Lagna)

```yaml
element: "4H Cancer untenanted + Mandi shadow + Moon lord in 11H + Varnada Lagna"
domains_primary: [D7, D8]
msr_anchors: [MSR.225, MSR.022]
cdlm_anchors: [D7.D4=0.65]
constructive_resonance:
  - Cancer = Moon's own sign (though Moon lives elsewhere)
  - Ketu 9th aspect from 8H = moksha-karaka touches sanctuary
  - Mercury + Sun 7th aspect from 10H = analytical-solar light on sanctuary
  - Saturn 10th aspect from 7H = structural-discipline stabilizes sanctuary
  - Varnada Lagna in 4H Cancer (v2.0 corrected) = the 'path-activator' special lagna is in the emotional-home domain; Varnada in 4H suggests the path of dharmic activation runs through emotional-home grounding and maternal connection
  - Saham Vivaha in 4H Cancer (v2.0 confirmed) = marriage-saham in the home-sanctuary domain
destructive_resonance:
  - Mandi upagraha present (background Saturn-shadow malefic)
  - Lord Moon far in 11H = mother-significator displaced
  - Rank 8 Bhavabala (mid-low house strength)
net_resonance: "MIXED — sanctuary structurally supported by aspects; Mandi shadow creates background difficulty; Varnada and Vivaha Saham add home-grounding importance"
```


```yaml
element: "7H Libra + Saturn exalted + Mars + BB + Shree Lagna + KP sub-lord Saturn"
domains_primary: [D3, D1]
msr_anchors: [MSR.391 (recalibrated post-v8.0 corrections), MSR.411]
cdlm_anchors: [D3.D3=0.93]
constructive_resonance:
  - Five-layer convergence:
    1. Saturn exalted (quality and structural discipline in relationship)
    2. Mars Avayogi + PK (friction and children-karma)
    3. Bhrigu Bindu natal (fortune-timing sensitivity — natal 8°04')
    4. Shree Lagna in 7H Vishakha Pada 1 (Lakshmi-grace directly in relationship domain — new positive addition per v8.0)
    5. KP sub-lord = Saturn (relationship-house KP governance by the exalted AmK)
  - Bhavabala weakest (rank 12) but yoga-density strongest
  - Jaimini Rashi Drishti receives from Moon (Aquarius fixed-sign)
  - Shree Lagna in 7H: Lakshmi's grace-point now directly in the relationship domain = wealth-through-relationship dimension added to the 7H karmic vortex
destructive_resonance:
  - BVB rank 12 = structurally fragile house
  - Avayogi Mars = fortune-reducer in relationship house
  - Hora Lagna removed (now confirmed in 3H Gemini per v8.0 — not a 7H element)
  - Saham Roga removed (now confirmed in 2H Taurus per v8.0 — not a 7H element)
  - Saham Mahatmya removed (now confirmed in 9H Sagittarius per v8.0 — not a 7H element)
net_resonance: "STRONGLY AMPLIFIED (yoga density, enhanced by Shree Lagna) AND TENSION-BEARING (fragile container)"
interpretive_note: "Chart's most yoga-dense relationship house. Five-layer convergence: Saturn exalted AmK + Mars Lagna lord PK + Bhrigu Bindu + Shree Lagna (Lakshmi's grace point) + KP sub-lord Saturn. The karmic vortex gains a Lakshmi-wealth dimension from Shree Lagna in 7H Libra — conscious relational investment is a direct wealth-activation mechanism. Tend deliberately with Saturn-discipline."
```

### RM.15 — 9H Sagittarius (Dharma Trine)

```yaml
element: "9H Sag + Jupiter own-sign + Venus + Ghati Lagna + Saham Mahatmya"
domains_primary: [D6, D7, D9, D2]
msr_anchors: [MSR.407, MSR.089, MSR.320]
cdlm_anchors: [D6.D6=0.94 self-amp, D6.D2=0.84]
constructive_resonance:
  - Jupiter own-sign tenancy (9L in own 9H = dharma-lord in dharma-house)
  - Venus co-tenant (2L+7L+MK) in dharmic host-sign
  - Saturn 3rd aspect from 7H = Saturn-quality discipline in dharma house
  - Jupiter-Venus conjunction within 10° = Laxmi-Narayana-adjacent
  - Ghati Lagna in 9H Purva Ashadha Pada 1 = power-timing lagna in the dharma house = temporal power expression routes through dharmic practice
  - Saham Mahatmya in 9H Sagittarius (confirmed v8.0) = honor/fame saham in dharma house = fame through dharmic channels
destructive_resonance:
  - SAV 25 (moderate-low sign activation)
  - Moola-Pada-3 (Ketu-nakshatra transformational undercurrent)
net_resonance: "STRONGLY AMPLIFIED — 9H is the chart's dharmic-wealth anchor"
```

### RM.16 — 10H Capricorn (Career Chamber)

```yaml
element: "10H Cap + Sun + Mercury + AL"
domains_primary: [D1, D5, D7]
msr_anchors: [MSR.413, MSR.019]
cdlm_anchors: [D1.D1=1.00]
constructive_resonance:
  - Stellium of Sun + Mercury
  - AL co-located (karma-arudha)
  - Mars 4th aspect from 7H = executive drive
  - Bhavabala rank 3 (one of strongest houses)
  - Dual-sign-Saturn-lord (10L Saturn exalted 7H — Raja Yoga component)
destructive_resonance:
  - Saturn's own-sign rulership means career expresses through Saturnian structure (patient, slow)
net_resonance: "STRONGLY AMPLIFIED — chart's career delivery mechanism"
interpretive_note: "Career chamber is multi-layered (Sun + Mercury + AL + Mars-aspect) but Jupiter-authorization operates via lordship, not direct aspect."
```

### RM.17 — Mercury MD (2010-2031)

```yaml
element: "Mercury Mahadasha — chart's primary operational 21-year window"
domains_primary: [D1, D2, D3, D8]
msr_anchors: [MSR.413, MSR.396]
cdlm_anchors: [D8.D8=0.95]
constructive_resonance:
  - MD lord is the chart's eight-system-convergence planet (updated from seven per v2.0)
  - Overlaps with Mercury's natal Vargottama
  - Saturn AD within Mercury MD (2024-2027) = highest-density peak
  - BB-UL 2026 convergence lands within Mercury MD
destructive_resonance:
  - Mercury 6L = 21 years of cognitive-health interface stress
  - Susupta avastha = internalized operation (effort may be invisible)
net_resonance: "STRONGLY AMPLIFIED — peak operational window in life-arc"
interpretive_note: "Current active window. Deploy Mercury fully; protect 6L boundary."
```

### RM.18 — Saturn AD 2024-12-12 → 2027-08-21

```yaml
element: "Saturn Antardasha within Mercury MD"
domains_primary: [D1, D3]
msr_anchors: [MSR.396, MSR.391]
cdlm_anchors: [D1.D3=0.91]
constructive_resonance:
  - AD lord = exalted AmK Saturn
  - Coincides with BB-UL 2026 convergence
  - Coincides with Chara Scorpio MD / Libra AD (7H-activation)
  - Triple temporal alignment in 2026
destructive_resonance:
  - Saturn's classical heaviness/delays
  - Health-risk window Nov 2026 - Mar 2027 (Saturn approaching Lagna degree)
net_resonance: "STRONGLY AMPLIFIED — institutional consolidation + relational crystallization peak"
interpretive_note: "Chart's most authority-productive window. Decisions here carry disproportionate structural permanence."
```

### RM.19 — Bhrigu Bindu Libra 8°04' (natal) → Gemini 20°02' (age 42)

```yaml
element: "Bhrigu Bindu — destiny-sensitive point"
domains_primary: [D3, D8]
msr_anchors: [MSR.236, MSR.404]
cdlm_anchors: [D3.D3=0.93]
constructive_resonance:
  - Natal BB in 7H Libra = destiny-point in relational axis
  - Now also co-located with Shree Lagna in 7H Libra (v2.0) = destiny-point and Lakshmi-grace in same position
  - Age 42 progression to Gemini 3H (per v7.0 §V7.F, 6°/year rate)
  - Gemini 3H = UL house = partnership-image domain
  - Jupiter 7th full aspect on 3H = BB-progression receives Jupiter blessing
destructive_resonance:
  - Moola-Pada transformational undercurrent in original 7H position
  - Rahu-Moon midpoint (nodal sensitivity)
net_resonance: "STRONGLY AMPLIFIED NOW (current year 2026 active)"
interpretive_note: "FALSIFIER WINDOW ACTIVE (2026-04 to 2026-10). Empirical test window for MSR.404. v2.0: Natal BB in 7H now also shares the house with Shree Lagna — the destiny-sensitive point and Lakshmi-grace co-reside in the relationship axis."
```

### RM.20 — Shree Lagna 7H Libra Vishakha Pada 1 [v2.0 FULLY REWRITTEN]

```yaml
element: "Shree Lagna — Lakshmi-fortune-anchor in 7H Libra"
domains_primary: [D3, D2, D6]
msr_anchors: [MSR.407, MSR.254]
cdlm_anchors: [D6.D2=0.84, D3.D2=0.87, D3.D3=0.93]
constructive_resonance:
  - In Libra 7H — Lakshmi's grace-point is in the RELATIONSHIP domain (not dharma house)
  - Vishakha Pada 1 (Jupiter-ruled pada of Indra-Agni nakshatra) = Lakshmi-via-Jupiter-quality
  - Co-tenant with Saturn exalted (AmK) and Mars (PK) = Lakshmi in the same house as the career-planet and children-significator
  - Co-location with natal Bhrigu Bindu (8°04' Libra) = destiny-sensitive point and Lakshmi-grace share the same location
  - Meaning: wealth materializes specifically THROUGH partnerships and relationships; collaborative enterprise is the Lakshmi channel
  - Relationships (7H) → Lakshmi-grace (Shree Lagna) → wealth (Venus 2L in 9H) = the wealth path runs through relational quality
destructive_resonance:
  - 7H BVB rank 12 = fragile container for Lakshmi's grace
  - Shree Lagna in enemy-sign of Venus (Libra is Saturn's sign; Venus rules Libra so this is Venus's own sign — actually BENEFIC; correction: Libra IS Venus's own sign, so this is a benefic placement for Shree Lagna)
net_resonance: "STRONGLY AMPLIFIED — wealth-through-relationship Lakshmi mechanism"
interpretive_note: "Lakshmi's grace routes through the RELATIONSHIP domain (7H Shree Lagna) — not through the dharma house. Wealth and Lakshmi are accessed via relationship quality, partnership investment, and collaborative enterprise. Conscious relational investment is a direct wealth-activation mechanism in this chart."
```

### RM.21A — Ghati Lagna 9H Sagittarius Purva Ashadha Pada 1 [v2.0 NEW — replaces old RM.21]

```yaml
element: "Ghati Lagna — temporal-power-timing lagna in 9H Sagittarius"
domains_primary: [D6, D1]
msr_anchors: [MSR.407]
cdlm_anchors: [D6.D1=0.89, D6.D6=0.94]
constructive_resonance:
  - Ghati Lagna in 9H Sagittarius = the lagna that marks peak temporal-power windows is in the dharma house
  - Co-tenant with Jupiter (own sign), Venus (Purva Ashadha) = Ghati Lagna receives maximum benefic support
  - Purva Ashadha Pada 1 (Sun-pada) = solar-authority quality to the power-timing
  - Classical: Ghati Lagna activation marks periods of heightened executive authority and social visibility
  - 9H placement means: peak power periods are accessed through dharmic/spiritual engagement, not through career aggression
destructive_resonance:
  - Ghati Lagna in a dual/mutable sign (Sagittarius) = power windows may be episodic rather than sustained
net_resonance: "STRONGLY AMPLIFIED — dharmic route to temporal power"
interpretive_note: "v2.0 NEW ELEMENT: Ghati Lagna confirmed in 9H Sagittarius per FORENSIC v8.0 (was incorrectly cited in 8H Scorpio in v1.1 RM.21). The power-timing lagna is in the dharma house — the native's windows of maximum temporal authority are triggered by dharmic alignment, not career-aggression. This is structurally coherent with Saturn = Dharma Devata = career-force. Ghati MD / Ghati-Lagna transit activations can be tracked for peak authority windows."
```

### RM.21B — Varnada Lagna 4H Cancer Pushya Pada 3 [v2.0 NEW — replaces old RM.21]

```yaml
element: "Varnada Lagna — path/dharma-direction lagna in 4H Cancer"
domains_primary: [D7, D8, D6]
msr_anchors: [MSR.225]
cdlm_anchors: [D7.D8=0.72, D6.D4=0.80]
constructive_resonance:
  - Varnada Lagna in 4H Cancer = the lagna that indicates the native's path (varna/dharma-direction) is in the home-mother-emotional domain
  - Pushya Pada 3 (Saturn-pada) = emotional-home domain is structured and Saturn-governed
  - Classical: Varnada Lagna's sign indicates the native's core dharmic-professional orientation
  - 4H placement: the path of dharmic development runs through emotional security, home stability, and inner sanctuary cultivation
  - Saturn's 10th aspect on 4H from 7H = the career-planet also structures the Varnada domain
destructive_resonance:
  - Mandi in 4H = background malefic in the Varnada domain
  - 4H BVB rank 8 (mid-low)
net_resonance: "BENEFIC — emotional-home as dharmic path anchor"
interpretive_note: "v2.0 NEW ELEMENT: Varnada Lagna confirmed in 4H Cancer per FORENSIC v8.0 (was incorrectly cited in 8H Scorpio in v1.1 RM.21). The path-indicator lagna is in the home-emotional domain. The native's dharmic path is rooted in emotional foundation, home cultivation, and inner sanctuary — not in the transformation/hidden domain as previously thought. Mandi's presence in 4H is an obstacle within the very domain that holds the path-indicator; emotional security work is therefore not optional but structurally necessary."
```

### RM.22 — Yogi Point 12H Pisces Revati

```yaml
element: "Yogi Point at 12H Pisces 22°20' Revati (Mercury-nakshatra-lord)"
domains_primary: [D6, D9]
msr_anchors: [MSR.392, MSR.413]
cdlm_anchors: [D9.D6=0.86]
constructive_resonance:
  - In Jupiter's sign (Pisces)
  - Mercury = Yogi Planet (Revati's lord)
  - 12H = foreign/moksha house
  - Ketu 5th aspect from 8H reaches 12H
  - Pranapada Lagna in 12H Pisces (confirmed v8.0) = life-breath also in fortune-moksha domain
destructive_resonance:
  - 12H SAV 23 (lowest in chart with Aquarius)
net_resonance: "STRONGLY AMPLIFIED — fortune-point in foreign/moksha domain"
interpretive_note: "Fortune crystallizes in foreign domain via Mercury activation. Singapore residence is Yogi-Point-activation. v2.0: Pranapada confirmed in 12H Pisces (consistent with v1.1)."
```

### RM.23 — UL-Jupiter Aspect [v1.1 ACCURATE]

```yaml
element: "Jupiter's 7th full aspect from 9H → UL in 3H Gemini"
domains_primary: [D3, D6]
msr_anchors: [MSR.338, MSR.407]
cdlm_anchors: [D3.D6=0.86]
constructive_resonance:
  - Jupiter in own sign 9H casts full 7th aspect on 3H = UL house
  - Partnership-image domain receives dharma-lord's direct gaze
  - Jupiter = natural 9H benefic authority-on-dharma
  - Hora Lagna also in 3H (v2.0) = UL house now has Hora Lagna as additional benefic element alongside Jupiter's aspect
destructive_resonance:
  - Ardra nakshatra overlay on UL
net_resonance: "STRONGLY AMPLIFIED — dharmic partner-image"
interpretive_note: "Jupiter's 7th aspect from 9H lands on UL 3H Gemini. v2.0: Hora Lagna confirmed in 3H (not 7H as previously cited in CDLM v1.0) — the 3H partnership-communication domain now holds UL + Hora Lagna + Jupiter-Venus aspects simultaneously."
```

### RM.24 — Saturn-Mars 7H Conjunction (ATT Architecture)

```yaml
element: "Saturn + Mars in 7H Libra, orb 3°56' — ATT pattern"
domains_primary: [D3, D1, D4]
msr_anchors: [MSR.052, MSR.398]
cdlm_anchors: [D3.D3=0.93]
constructive_resonance:
  - Saturn exalted + Mars own-pada = both at high dignity levels despite conjunction
  - Orb 3°56' > 1° threshold (not Graha Yuddha)
  - Productive-tension mechanism classically described
destructive_resonance:
  - Natural enemies (Saturn's enemy = Mars)
  - Mars Avayogi compounds Saturn's structural heaviness
net_resonance: "TENSION-BEARING — chart's primary ATT engine"
interpretive_note: "Tension IS the mechanism. Attempting to 'resolve' it diminishes Saturn-authority. v2.0: D3.D3 anchor updated from 0.95 to 0.93."
```

### RM.25 — AK Moon + A7 both in 11H Aquarius

```yaml
element: "Moon AK + A7 (spouse-image arudha) in same 11H sign"
domains_primary: [D8, D3]
msr_anchors: [MSR.338, MSR.330]
cdlm_anchors: [D3.D8=0.82]
constructive_resonance:
  - Soul's primary planet co-located with partner-image arudha
  - Aquarius = Saturn's sign (aligns with 10L Saturn career)
  - 11H = gains/social community
destructive_resonance:
  - Saturn-rulership introduces delay-temperament
net_resonance: "STRONGLY AMPLIFIED — soul-partnership structural alignment"
interpretive_note: "Soul and spouse-image in same sign = partnerships structurally aligned with soul's orientation."
```


```yaml
element: "8H threefold-stack (Ketu exalted + Scorpio transformation-house + Indu Lagna)"
domains_primary: [D6, D4, D8]
msr_anchors: [MSR.335, MSR.402]
cdlm_anchors: [D6.D6=0.94]
constructive_resonance:
  - Ketu exalted in own-themed house (Scorpio = Ketu's exaltation)
  - 8H = transformation, longevity, hidden depths, moksha gateway
  - Indu Lagna in 8H Jyeshtha (v2.0 confirmed per FORENSIC v8.0) = Moon-based wealth indicator in transformation house
  - Jyeshtha/Anuradha nakshatras bordering
destructive_resonance:
  - 8H classical shadow
  - [v2.0]: Varnada Lagna now confirmed in 4H Cancer (NOT 8H); Ghati Lagna confirmed in 9H Sagittarius (NOT 8H); 8H fourfold-stack from v1.1 corrected to threefold
net_resonance: "STRONGLY AMPLIFIED HIDDEN-PINNACLE (threefold stack)"
interpretive_note: "Chart's deepest-authority architecture. Ketu MD 2031-2038 activates this entire stack. v2.0: Varnada and Ghati Lagnas corrected out of 8H (both were wrong in v1.1 RM.21); 8H is now a cleaner Ketu-exalted + Indu Lagna stack — still the hidden-pinnacle domain but with a different lagna architecture than previously thought. The 8H's authority is Ketu-exalted + transformation-purification, not the compound of four special lagnas. Ketu MD 2031-2038 remains the activation window."
```

### RM.27 — Ketu MD 2031-2038 (Future)

```yaml
element: "Ketu Mahadasha 7-year window, age 47-54"
domains_primary: [D6, D8]
msr_anchors: [MSR.335, MSR.402]
cdlm_anchors: [D6.D6=0.94]
constructive_resonance:
  - Aligns with hidden-pinnacle 8H architecture (Ketu exalted + Indu Lagna)
  - Moksha-karaka activates moksha-house themes
  - Ketu exalted natal → MD delivery at maximum dignity
  - Ghati Lagna (9H) and Varnada Lagna (4H) will be active dharmic-home dimensions during Ketu MD — these route through different domains than the 8H themes
destructive_resonance:
  - Mercury MD identity-investment must release (transition stress)
  - Double-nodal Ketu-Rahu AD in 2030-2031 (Rahu transit on natal Ketu) = nodal-intensity peak
net_resonance: "STRONGLY AMPLIFIED FUTURE — transformation-depth activation window"
interpretive_note: "Chart's central moksha-turn. Begin preparation in Ketu AD (2027-2028). v2.0: Ghati Lagna in 9H means Ketu MD dharmic-power windows activate through the dharma house; Varnada in 4H means the emotional-home domain also plays in Ketu MD's path-direction themes."
```

### RM.28 — Saraswati-Lakshmi-Raja Yoga Stack

```yaml
element: "Saraswati + Lakshmi + Triple-Raja yoga stack"
domains_primary: [D1, D2, D8]
msr_anchors: [MSR.143, MSR.146]
cdlm_anchors: [D8.D8=0.95]
constructive_resonance:
  - Saraswati: Mercury Kendra 10H + Jupiter Trikona 9H + Venus Trikona 9H = Kendra-Trikona yoga intact
  - Lakshmi: Shree Lagna in 7H Libra + Venus 2L in 9H + Jupiter 9L in 9H (own-sign)
  - Lakshmi Yoga reinterpretation: Shree Lagna in 7H means Lakshmi-yoga activates through relationship channels, not directly through the 9H dharma domain; Venus 2L in 9H remains the direct wealth-dharma link
  - Raja Yoga 1: Jupiter 9L in own-sign 9H (Bhagya Yoga variant)
  - Raja Yoga 2: Sun 5L in 10H Kendra (classical Trikona-in-Kendra)
  - Raja Yoga 3: Saturn 10L exalted in 7H Kendra (Sasha Mahapurusha)
destructive_resonance:
  - Mercury 6L co-governance adds dual-edge
  - All yogas fire during Mercury MD only (conditional, not natal-permanent)
net_resonance: "STRONGLY AMPLIFIED during Mercury MD (current)"
interpretive_note: "Lakshmi Yoga Shree Lagna in 7H Libra. The Lakshmi-path routes through relationships (7H Shree Lagna) and dharmic-wealth (Venus 2L in 9H). Three-yoga stack — Saraswati, Lakshmi, Raja — classically formed. All three fire simultaneously during Mercury MD."
```

### RM.29 — Vishnu/Venkateshwara Devata Triple-Lock

```yaml
element: "Karakamsa-derived Devata system"
domains_primary: [D6, D7]
msr_anchors: [MSR.397 (0.91)]
cdlm_anchors: [D6.D7=0.82]
constructive_resonance:
  - Karakamsa = Gemini = Mercury (Palana Devata = Vishnu)
  - 9th from Karakamsa = Aquarius = Saturn (Dharma Devata = Venkateshwara — form of Vishnu)
  - 12th from Karakamsa = Taurus = Venus (Ishta Devata = Mahalakshmi)
  - Retrodictively confirmed by 2025 pivot (LEL)
destructive_resonance:
  - None structural
net_resonance: "STRONGLY AMPLIFIED — devata alignment triple-locked"
interpretive_note: "Vishnu-form devotion is chart-aligned. Venkateshwara specifically recommended."
```

### RM.30 — Chart's Central Paradox Stack (Meta-Resonance)

```yaml
element: "Seven architectural contradictions (UCN §IX)"
domains_primary: [all]
msr_anchors: [MSR.419, MSR.420]
cdlm_anchors: [all]
constructive_resonance:
  - Mercury as both 10L (career) and 6L (disease) = integration through boundary-discipline
  - Saturn malefic-by-nature but fortune-delivering-by-chart
  - 7H weakest-container + highest-yoga-density (with Shree Lagna as new positive element per v2.0)
  - Jupiter own-sign but Uccha-Bala-weak
  - Aries Lagna fire-principle but career in Saturnian Capricorn
  - Venus D1-strong but D9-debilitated
  - Moon AK in gains-house (11H) not private-moksha house (12H)
destructive_resonance:
  - If native tries to resolve rather than hold tension, architecture underperforms
net_resonance: "TENSION-BEARING CURRICULUM"
interpretive_note: "Seven paired truths to hold simultaneously. Not errors. The curriculum IS the practice. v2.0: Seventh paradox (7H weakest + highest-yoga-density) now additionally contains Shree Lagna — the weakest container also holds Lakshmi's grace; this is the chart's most poignant paradox restatement."
```

---

### RM.31 — Vargottama Mercury Resonance (Cross-Varga Anchor)

```yaml
element: "Mercury D1 Capricorn = D9 Capricorn — sole vargottama planet; disposits D9 12H stellium and NBRY-Venus"
domains_primary: [career, wealth, mind, dharma]
msr_anchors: [SIG.MSR.514, SIG.MSR.500, SIG.MSR.002, SIG.MSR.001]
cdlm_anchors: [career×mind, career×wealth]
constructive_resonance:
  - "Vargottama Mercury is the chart's single most stable cross-varga element — D1 = D9 = Capricorn"
  - "Mercury disposits the D9 12H stellium (Moon + Jupiter + Rahu in Gemini) via Mercury-ruled Gemini"
  - "Mercury cancels Venus's D9 debilitation (NBRY) via Kendra placement in D9 7th"
  - "Mercury anchors D10 2H (own sign Virgo), D24 3H (Cancer — disposited by Moon at D24 exalted lagna), and D60 Lagna lord (Gemini)"
destructive_resonance:
  - "If Mercury's transit/dasha state weakens, the cross-varga stability propagates as ambient drift across all Mercury-routed dispositor chains"
net_resonance: "STRUCTURAL ANCHOR — chart's stability surface"
interpretive_note: "Where everything else moves between D1 and D9 (six of seven planets shift dignity per CSI), Mercury stays. Every dispositor chain that touches Mercury inherits this stability; every dharmic move that routes through Mercury-ruled signs (Gemini, Virgo) is structurally reliable. Operationally this is why Mercury MD (2010–2031) and Mercury-AD windows show signal density and predictability above the chart's baseline."
strength: 0.88
```

---

### RM.32 — Saturn Three-State Resonance (Career-Delivered-Through-Challenge)

```yaml
element: "Saturn D1 Libra exaltation (Sasha MPY) → D9 Aries debilitation (NBRY via Sun in D9 Lagna) → D10 Taurus 10th (angular delivery)"
domains_primary: [career, wealth, dharma, mind]
msr_anchors: [SIG.MSR.501, SIG.MSR.003, SIG.MSR.001]
cdlm_anchors: [career×relationships, career×wealth]
constructive_resonance:
  - "Three-state arc: foundation (D1 Sasha) + dissolution (D9 debilitated, then cancelled by NBRY) + delivery (D10 angular)"
  - "Each state is structurally distinct: the chart deliberately routes Saturn through challenge to extract authority"
  - "Sun is the cancellation agent for D9 NBRY (Sun rules Aries; Sun in D9 Lagna Cancer = Kendra) — note Sun-Saturn relationship is also D1 Capricorn co-presence (mutual reception via opposition lord)"
destructive_resonance:
  - "If the native reads any single state in isolation (only Sasha, or only D9 debility), the architecture misfires — the three states are one structural unit"
net_resonance: "DELIVERY-THROUGH-CONTRACTION — Saturn earns authority by undergoing depletion"
interpretive_note: "The chart's career architecture is not Saturn-as-strong (Sasha alone) and not Saturn-as-weak (D9 alone). It is Saturn-as-passed-through. The D10 10th-house angular placement is the resolved residue — what remains after Saturn has been ground through D9 debilitation. Acharya reading: Sasha is the seed, D9 debility is the test, D10 angularity is the harvest."
strength: 0.87
```

---

### RM.33 — Venus Three-State Resonance (Relational-Delivery-Through-Mercury)

```yaml
element: "Venus D1 Sagittarius (neutral, 9H joined Jupiter) → D9 Virgo debilitation (NBRY via vargottama Mercury Kendra) → D10 Gemini 11H (gains, Mercury-sign)"
domains_primary: [relationships, wealth, spirit]
msr_anchors: [SIG.MSR.502, SIG.MSR.002, SIG.MSR.514]
cdlm_anchors: [relationships×wealth, relationships×mind]
constructive_resonance:
  - "Mirror of RM.32 Saturn architecture, in relational register: three-state arc with NBRY at D9 and angular/gains-house delivery"
  - "Both ends of the arc route through Mercury: D9 cancellation via Mercury-vargottama dispositor, D10 placement in Mercury-sign Gemini"
  - "Relational delivery is not Venus-direct (debilitation in D9 blocks that path); it is Venus-mediated-by-Mercury"
destructive_resonance:
  - "If Mercury weakens, Venus's relational delivery loses its anchor — both NBRY cancellation and D10 dispositor support require Mercury"
net_resonance: "MEDIATED RELATIONAL DELIVERY — partnership comes via Mercury significations (commerce, communication, dispositor strength)"
interpretive_note: "The chart routes relational wealth (Venus + 7H Shree Lagna) through Mercury-mediated channels — partnership-as-communication, partnership-as-commerce. Venus alone does not carry the load; Mercury (D9 dispositor, D10 sign-lord) carries it for her. Compare with RM.31 — same Mercury-anchor surface, different domain face."
strength: 0.80
```

---

### RM.34 — D9 12H Stellium Resonance (Moksha Routed Through Vargottama Mercury)

```yaml
element: "D9 12H Gemini holds Moon + Jupiter + Rahu, disposited by vargottama Mercury in D9 7H Capricorn (Kendra)"
domains_primary: [spirit, dharma, mind]
msr_anchors: [SIG.MSR.500, SIG.MSR.514, SIG.MSR.026, SIG.MSR.027]
cdlm_anchors: [spirit×mind, spirit×relationships]
constructive_resonance:
  - "Three planets concentrated in the moksha-house of the dharma varga (D9) — high signal density for dissolution/moksha trajectories"
  - "All three planets (Moon, Jupiter, Rahu) are in Gemini = Mercury-ruled, and the dispositor (Mercury) is vargottama in Kendra — moksha pathway anchored in the chart's most stable planetary surface"
  - "Stellium is anchored: the 12H concentration does not dissipate because its dispositor is structurally fixed across D1/D9"
destructive_resonance:
  - "Stellium intensity is read as ungrounded by readings that miss the vargottama anchor — those readings interpret it as scattered moksha-tension rather than anchored moksha-architecture"
net_resonance: "ANCHORED MOKSHA — dissolution path routes through the chart's most stable signification (Mercury)"
interpretive_note: "Classical readings of a D9 12H stellium often flag it as dharma-loss or relationship dissolution. In this chart that reading is incomplete: the dispositor (vargottama Mercury) gives the stellium structural ground. The moksha trajectory is not chaotic — it is mediated through Mercury significations (intellect, dispositor chains, communication). Read alongside RM.31 (vargottama anchor) and SIG.MSR.500 (six-shift backdrop)."
strength: 0.82
```

---

### RM.35 — D10 Career Architectural Triad (Mars 9H + Saturn 10H + Mercury 2H)

```yaml
element: "D10 Mars Aries 9H (own sign) + D10 Saturn Taurus 10th (angular) + D10 Mercury Virgo 2H (own sign)"
domains_primary: [career, wealth, dharma]
msr_anchors: [SIG.MSR.501, SIG.MSR.514, SIG.MSR.001]
cdlm_anchors: [career×wealth, career×dharma]
constructive_resonance:
  - "Three dignified placements form a 2-9-10 architecture in the career varga: own-sign Mars in dharma-trine, angular Saturn in career-house, own-sign Mercury in wealth/speech-house"
  - "Saturn's D10 angularity is the resolved residue of the three-state arc (see RM.32) — career delivery is exactly where the Sasha-NBRY-Angular cascade terminates"
  - "Mercury's D10 own-sign placement extends the vargottama anchor (RM.31) into career — the same Mercury that disposits D9 12H stellium owns the D10 wealth-chamber"
  - "D10 Lagna is Leo (Sun-ruled) with D10 Sun also in 9H Aries (Mars sign) — the Sun-Mars exchange via Aries reinforces the 9H dharma anchor"
destructive_resonance:
  - "Reading career via D1 alone misses the architecture — D1 10H is empty in many senses, D10 10H is the actual career-house"
net_resonance: "CAREER ARCHITECTURE FULLY VISIBLE IN D10 — three dignified planets across 2/9/10 trine-angle axis"
interpretive_note: "The chart's career signature crystallises in D10, not D1. D1 gives the Sasha foundation (Saturn 7H exalted) and the Mercury 10H placement; D10 gives the delivery topology: dharma-trine Mars, angular Saturn, wealth-house Mercury. Read this triad as the single most important career-axis fact in the divisional layer. Compare with SIG.MSR.501 (Saturn three-state) and SIG.MSR.514 (Mercury anchor)."
strength: 0.83
```

---

## §2 — META-PATTERNS (v2.0 updated)

| Pattern | Description | Primary Elements |
|---|---|---|
| Dharmic-Wealth Architecture | 9H Jupiter-Venus-Ghati-Saham Mahatmya cluster → power and honor via dharma | RM.03, RM.04, RM.15, RM.21A |
| Lakshmi-Through-Relationship | Shree Lagna 7H = Lakshmi's grace routes through partnership quality | RM.14, RM.19, RM.20, RM.28 |
| ATT Tension Architecture | Saturn-Mars 7H → authority-through-productive-tension | RM.02, RM.06, RM.14, RM.24 |
| Mercury Octagram | Mercury governs career+mind+wealth+UL-lord+Karakamsa-lord+Yogi+DK+Siva Yoga Lord | RM.01, RM.16, RM.17, RM.22 |
| Hidden-Pinnacle Moksha | Ketu-8H-Indu Lagna → Ketu MD 2031 | RM.09, RM.26, RM.27 |
| Dharmic-Path Architecture | Ghati (9H), Varnada (4H), Hora (3H) = power/path/finance all in dharmic-home-communication triad | RM.21A, RM.21B, RM.12 |
| 2026 Triple-Timing Convergence | Mercury MD + Saturn AD + Chara Libra AD + BB-UL | RM.17, RM.18, RM.19, RM.23 |
| Venkateshwara Devata Triple-Lock | Mercury-Vishnu + Saturn-Venkateshwara + Venus-Lakshmi | RM.29 |

---

## §3 — RESONANCE SUMMARY STATISTICS

- **Total elements**: 37 (32 from v2.1 + 5 new in v2.2: RM.31–RM.35 cross-varga resonances)
- **STRONGLY AMPLIFIED**: 23 elements (20 prior + RM.31, RM.34, RM.35)
- **TENSION-BEARING (productive)**: 6 elements (RM.06, RM.14, RM.24, RM.30, RM.32, RM.33)
- **MIXED / COMPENSATED**: 3 elements (RM.04, RM.13, RM.07 partial)
- **Elements with v2.0 corrections from v1.1**: 8 (RM.01, RM.02, RM.03, RM.08, RM.14, RM.15, RM.20, RM.21 split + RM.26, RM.28)
- **Elements carried forward verbatim from v1.1**: 22
- **v2.2 cross-varga additions (VARGA-ETL-FULL-S1 D14)**: 5 (RM.31 vargottama anchor, RM.32 Saturn three-state, RM.33 Venus three-state, RM.34 D9 12H stellium, RM.35 D10 career triad)

### v2.1 Key Structural Features

1. **Shree Lagna in 7H Libra**: Lakshmi's grace routes through partnership quality; impacts RM.14 (7H), RM.15 (9H), RM.19 (BB), RM.20, RM.28 (Lakshmi Yoga)
2. **Ghati Lagna in 9H Sagittarius**: power-timing lagna in dharma house; impacts RM.03 (Jupiter), RM.21A (new), RM.15 (9H elements)
3. **Varnada Lagna in 4H Cancer**: path-direction lagna in home-emotional domain; impacts RM.21B (new), RM.13 (4H elements)
4. **Saham Roga in 2H Taurus**: health challenges emerge from 2H domain; impacts RM.08 (Rahu), RM.14 (7H layer count)
5. **8H threefold architecture**: Ketu-exalted + Indu Lagna stack; retains transformation authority with clarified lagna architecture

---
