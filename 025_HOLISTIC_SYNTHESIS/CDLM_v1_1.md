---
artifact: CDLM_v1_1.md
version: 1.3
canonical_id: CDLM
status: CURRENT
session: M4-D-P1-CDLM-PATCH
date_opened: 2026-04-18
native: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
primary_inputs: [MSR_v1_0.md, CGM_v1_0.md, MATRIX_HOUSES.md, MATRIX_PLANETS.md, FORENSIC_ASTROLOGICAL_DATA_v8_0.md]
architecture_ref: "§C.3.3 (CDLM specification)"
parent_facts_version: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
supersedes: CDLM_v1_0.md
corrections_applied: 9
correction_basis: "FORENSIC_ASTROLOGICAL_DATA_v8_0.md — Special Lagna positions corrected (Hora Lagna→3H Gemini, Ghati→9H Sagittarius, Varnada→4H Cancer, Shree→7H Libra); Saham Roga confirmed in 2H Taurus (NOT 7H Libra)"
v1_2_changelog: "Corrective text stripped 2026-04-19 per corpus cleanup brief. See 00_ARCHITECTURE/AUDIT_REPORT_v1_0.md for history."
v1_3_changelog: "CF.LL7.1 Pancha-MP msr_anchors patch (M4-D-P1-CDLM-PATCH 2026-05-02) — appended MSR.117 (Saturn/Sasha-Kendra) to CDLM.D1.D1; MSR.118 (Venus/Malavya) to CDLM.D5.D5; MSR.119 (Mars/Ruchaka) to CDLM.D5.D6; MSR.143 (Jupiter/Hamsa) to CDLM.D5.D7. MSR.145 (Mercury/Bhadra) status per OPEN_ITEM.P1.1 — Mercury Bhadra cell does not exist in CDLM (no planet-specific cells; 81-cell domain-pair structure); MSR.145 cannot be anchored at this surgical pass; carried to M5 CDLM expansion. Brief assumed file at v1.1 → v1.2; actual current internal version was 1.2 from 2026-04-19 corpus cleanup pass; patch took next clean version 1.3. No re-run of LL.N computation; LL.7 JSON outputs untouched (substrate corrected for future runs only)."
layer: "L2.5"
expose_to_chat: true
native_id: "abhisek"
---

# CDLM_v1_1 — Cross-Domain Linkage Matrix
## Abhisek Mohanty Jyotish Intelligence System
### v1.3 — Cross-Domain Linkage Matrix

### Purpose

The CDLM maps the structural interdependencies between the 9 life domains. Each cell (Row → Column) answers: "How does the Row domain structurally affect, feed, or constrain the Column domain in this native's chart?" This is not general astrology — every cell is grounded in specific MSR signals, CGM edges, and L1 facts.

The CDLM is the primary input to:
- UCN (Unified Chart Narrative) for domain-integration writing
- Domain Reports (L3) for cross-domain context
- Query interface (Phase 6) for multi-domain questions

### Nine Domains

| ID | Domain | Primary House | Primary Planet |
|---|---|---|---|
| D1 | Career | 10H Capricorn | Saturn (AmK), Sun, Mercury |
| D2 | Wealth | 2H Taurus, 11H Aquarius | Rahu (2H), Moon (11H), Venus (2L) |
| D3 | Relationships | 7H Libra | Saturn (exalted), Mars, UL (3H) |
| D4 | Health | 6H Virgo, 8H Scorpio | Ketu (8H), Mandi (4H) |
| D5 | Children | 5H Leo | Jupiter (5L from Aries, = 12L... wait: from Aries Lagna, 5H = Leo; 5L = Sun; Jupiter = 9L+12L) |
| D6 | Spirit | 9H Sagittarius, 12H Pisces | Jupiter, Ketu, Yogi Point |
| D7 | Parents | 9H (father), 4H (mother) | Sun (pitru), Moon (matru), Jupiter (9H) |
| D8 | Mind | 4H Cancer, Moon | Moon (AK), Mercury (DK, intelligence) |
| D9 | Travel | 9H, 12H, 3H | Rahu (12H driver), Saham Paradesa (1H) |

### CDLM Schema (per cell)

```yaml
CDLM.Dx.Dy:
  row_domain: "source domain name"
  col_domain: "target domain name"
  linkage_type: [feeds | constrains | mirrors | amplifies | compensates | contradicts]
  primary_mechanism: "the specific astrological mechanism creating this linkage"
  msr_anchors: [list of MSR signal IDs most relevant]
  strength: 0.00-1.00  # how strong is this cross-domain link
  direction: [bidirectional | row→col | col→row]
  valence: [benefic | malefic | mixed | neutral]
  key_finding: "one-sentence distillation of the cross-domain relationship"
```

### Linkage Type Definitions

- **feeds**: Domain A's activities directly produce inputs to Domain B (e.g., career produces wealth)
- **constrains**: Domain A's state limits or shapes what Domain B can achieve
- **mirrors**: Domain A reflects the same underlying planetary energy as Domain B (same planet governs both)
- **amplifies**: When Domain A is active, Domain B's results are magnified
- **compensates**: Domain A's weakness is offset by Domain B's strength
- **contradicts**: Domain A and Domain B are in structural tension in this chart

### Directional Asymmetry Convention (added 2026-04-18 FIX_SESSION_002)

CDLM cells can carry asymmetric strengths across the diagonal — i.e., `CDLM.Dx.Dy.strength` ≠ `CDLM.Dy.Dx.strength` for some pairs. This is by design, not error. The asymmetry reflects genuine mechanistic differences in directional flow:

- `Dx → Dy` strength quantifies how strongly the row-domain influences the column-domain
- `Dy → Dx` strength quantifies the reverse flow
- These can legitimately differ when the underlying mechanism is asymmetric

**Example**: CDLM.D1.D2 (Career → Wealth) = 0.92; CDLM.D2.D1 (Wealth → Career) = 0.88. Career drives wealth more directly than wealth drives career — the asymmetry captures the primacy of the Career→Wealth mechanism in this chart.

**Reading convention**:
- If `direction: row→col` on both sides (D1.D2 and D2.D1), the cells are two independent directional links, not redundant
- If `direction: bidirectional`, strengths should be identical (any divergence indicates transcription error)
- 27 of 36 off-diagonal pairs exhibit asymmetry in this CDLM (Δ ∈ [0.01, 0.06]) per AUDIT_REPORT_v1_0 WS-3a

**Validation**: CONTRADICTION_REGISTRY §5 (as of 2026-04-18) lists the specific asymmetric pairs. Future CDLM v2.0 may normalize to strict symmetry if practitioners prefer, but v1.1 preserves directional fidelity.

---

## THE 81-CELL CDLM

---

### ROW D1: CAREER → [All Domains]

CDLM.D1.D1:
  row_domain: Career
  col_domain: Career (self-reference)
  linkage_type: mirrors
  primary_mechanism: "10H Capricorn = AL (Arudha Lagna) + Sun + Mercury Vargottama + Saturn AmK (7L disposits to Saturn) + KP cusp 10 sub=Saturn + Jaimini Rashi Drishti from Rahu+Ketu on 10H = the career domain is the chart's self-amplifying apex; every major system designates 10H as primary delivery point"
  msr_anchors: [MSR.390, MSR.413, MSR.339, MSR.349, MSR.117]
  strength: 1.00
  direction: bidirectional
  valence: benefic
  key_finding: "Career is this chart's primary domain — AL, natal planets, Jaimini aspects, and KP all designate 10H as the supreme delivery point; career is not one of nine domains but the organizing axis of all nine."

CDLM.D1.D2:
  row_domain: Career
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "10H Sun+Mercury (career planets) → 2H wealth house: Mercury (10H) Jaimini-aspects Sagittarius (9H) but also Vimshottari MD delivers gains through Mercury period; AL=10H = career is how the native is perceived = career reputation drives wealth; Venus as 2L is in 9H (career-dharma house) = the wealth lord lives in the dharma-adjacent career zone"
  msr_anchors: [MSR.413, MSR.264, MSR.311]
  strength: 0.92
  direction: row→col
  valence: benefic
  key_finding: "Career directly feeds wealth — the native's income is inseparable from his professional reputation and Mercury-driven career delivery."

CDLM.D1.D3:
  row_domain: Career
  col_domain: Relationships
  linkage_type: mirrors
  primary_mechanism: "Saturn is simultaneously exalted AmK (career) in 7H (relationships) = the career-significator and the relationship-house are the SAME PLANET in the SAME HOUSE; AL=Capricorn 10H (career) vs UL=Gemini 3H (spouse-quality) both have Mercury as their connecting link (AL lord = Saturn, UL lord = Mercury, and Mercury is MD lord = career); the 7H is both the relationship house AND where the career's primary planet (Saturn AmK) lives"
  msr_anchors: [MSR.335, MSR.338, MSR.400]
  strength: 0.91
  direction: bidirectional
  valence: mixed
  key_finding: "Career and relationships share Saturn as their structural backbone; the native's professional life and partnership life are karmically inseparable — Saturn exalted in 7H means career-discipline IS relationship-karma."

CDLM.D1.D4:
  row_domain: Career
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "Saturn (AmK, career) rules 10H and 11H from Aries Lagna = career-pressure through Saturn's demanding nature; Muntha at Virgo 6H (age 42 Varshaphal) = the annual career-cycle sensitive point falls in the health house at age 42; Mercury = 6L (health house lord) AND 10H career planet = the health-house lord IS the career planet; when career demand on Mercury is at peak, health-domain resources are simultaneously stretched; Saturn's perfectionistic career standards create the primary health cost through overwork and nervous-system load"
  msr_anchors: [MSR.377, MSR.253, MSR.385]
  strength: 0.78
  direction: row→col
  valence: malefic
  key_finding: "Career pressure (Saturn's demanding quality + Mercury as 6L-10L dual-lord) structurally constrains health — professional intensity drains Mercury's health-domain resources; the 2026 Muntha in 6H is the primary career-health constraint window."

CDLM.D1.D5:
  row_domain: Career
  col_domain: Children
  linkage_type: constrains
  primary_mechanism: "PK Mars (children-significator) in 7H Libra = Mars is the Avayogi (fortune-reducer) AND the PK (children) AND is in the same house as Saturn (career-AmK); career-relationship domain (7H) competes with children-domain energy (PK Mars) = time and focus invested in career-building may delay children; 5H Leo (children house) is empty = children domain has no natal planet, only Jupiter's Jaimini Dual-sign aspect as compensator"
  msr_anchors: [MSR.343, MSR.398, MSR.333]
  strength: 0.72
  direction: row→col
  valence: malefic
  key_finding: "Career directly constrains children — the Avayogi PK Mars in the career-partnership zone means children-domain energy competes with professional focus; children come after and through career stabilization."

CDLM.D1.D6:
  row_domain: Career
  col_domain: Spirit
  linkage_type: feeds
  primary_mechanism: "AL=10H Capricorn; Shree Lagna=7H Libra = Lakshmi's grace-point is in the relationship house, and both the career (10H) and the Shree Lagna (7H) are in cardinal signs sharing Saturn as their governing energy; the native's career (10H) is in Capricorn = Saturn-domain; Saturn = Dharma Devata (Venkateswara) = the career IS a spiritual discipline; Jupiter+Venus in 9H (dharma) Jaimini-aspect all four fixed signs = the spirit domain's benefics supervise the fixed-sign wealth-career axis; Mercury as Yogi (career planet) AND fortune-activator = career and spiritual fortune are the SAME channel"
  msr_anchors: [MSR.397, MSR.407, MSR.388]
  strength: 0.89
  direction: bidirectional
  valence: benefic
  key_finding: "Career and spirit are mutually feeding — the native's professional excellence IS his dharmic practice (Saturn = Dharma Devata); career feeds spiritual evolution and spiritual depth feeds career quality."

CDLM.D1.D7:
  row_domain: Career
  col_domain: Parents
  linkage_type: mirrors
  primary_mechanism: "Sun (career house 10H) = BK (Bhratri Karaka siblings but also = pitru-karaka in Parashari tradition for father); Pitri Saham in Capricorn 10H = the father-sensitive-point is in the career house; Sunday birth (Sun's day) = the career-timing is on the father-deity's day; 9H (father's house) = Jupiter+Venus = dharmic father; the native's career-excellence and his father's domain share 10H as their axis"
  msr_anchors: [MSR.344, MSR.359, MSR.241]
  strength: 0.76
  direction: bidirectional
  valence: mixed
  key_finding: "Career mirrors the father's domain — Pitri Saham in 10H means the father-karma is encoded in the career house; the native's professional identity partly reflects and partly reacts to paternal legacy."

CDLM.D1.D8:
  row_domain: Career
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "Mercury (10H career planet) = Yogi Planet + DK + Vargottama = the career is Mercury-driven; Mercury governs both the career domain (10H, natal) AND the mental domain (Mercury = intelligence, analysis, communication = the primary mental faculties); Sun+Mercury in 10H = the mind's two primary planets (Sun = ego, Mercury = intelligence) are both in the career house = career amplifies mental engagement; when career is active, the mind is at its most productive"
  msr_anchors: [MSR.388, MSR.413, MSR.190]
  strength: 0.91
  direction: row→col
  valence: benefic
  key_finding: "Career directly amplifies mental functioning — Mercury in 10H means professional engagement activates the native's highest mental faculties; the native thinks best when working on career problems."

CDLM.D1.D9:
  row_domain: Career
  col_domain: Travel
  linkage_type: feeds
  primary_mechanism: "AL=10H Capricorn; Saham Paradesa (foreign travel) in 1H within 3° of Lagna = the identity (Lagna) carries foreign-travel encoding; the native's career (10H, AL) is executed in a foreign land (Singapore) = career is the mechanism through which the foreign-travel destiny (Saham Paradesa) is fulfilled; 12H Pisces (foreign lands) = Yogi Point + Pranapada = the fortune-activation point (Yogi) is in the foreign domain = career fortune comes through the foreign location"
  msr_anchors: [MSR.399, MSR.392, MSR.381]
  strength: 0.90
  direction: row→col
  valence: benefic
  key_finding: "Career feeds travel — the native's professional excellence requires and is enabled by foreign residence; the career IS the mechanism through which the Saham Paradesa foreign-destiny is lived."

---

### ROW D2: WEALTH → [All Domains]

CDLM.D2.D1:
  row_domain: Wealth
  col_domain: Career
  linkage_type: feeds
  primary_mechanism: "2H Rahu (exalted) = the wealth accumulation driver is Rahu (ambition, innovation, disruption) = the wealth drive fuels career ambition; A6 (enemies/competitors) in 2H with Rahu = the native's wealth competition occurs in his strongest domain; 11H Moon-AK = the gains-fulfillment house (wealth) hosts the soul-planet = financial gains and career fulfillment are the same act; KP cusp 2 sub=Rahu = the wealth gate is Rahu-operated = unconventional ambition"
  msr_anchors: [MSR.401, MSR.337, MSR.311]
  strength: 0.88
  direction: row→col
  valence: benefic
  key_finding: "Wealth ambition (Rahu 2H exalted) directly fuels career drive — the native's financial goals and career ambition are the same force expressed in different domains."

CDLM.D2.D2:
  row_domain: Wealth
  col_domain: Wealth (self-reference)
  linkage_type: amplifies
  primary_mechanism: "2H Rahu (wealth accumulation) + 11H Moon-AK (gains/fulfillment) + Venus as 2L (wealth lord in 9H dharma) + Shree Lagna in 7H Libra (Lakshmi-grace in the relationship domain = wealth through partnerships) + KP cusp 11 sub=Mercury (Yogi = fortune-activator governs gains) = the wealth domain has four self-amplifying mechanisms; Rahu-2H ambition, Moon-11H soul-fulfillment, Shree Lagna Lakshmi-partnership-wealth, and Mercury Yogi gains; Shree Lagna in 7H specifically indicates wealth materializes through partnerships and collaborative relationships rather than solo enterprise"
  msr_anchors: [MSR.407, MSR.409, MSR.401]
  strength: 0.91
  direction: bidirectional
  valence: benefic
  key_finding: "The wealth domain is internally amplified — four independent wealth-mechanisms (Rahu 2H, Shree Lagna 7H, Moon 11H gains, Mercury Yogi) all confirm material abundance potential; Shree Lagna in 7H means Lakshmi's grace flows specifically through partnership channels."

CDLM.D2.D3:
  row_domain: Wealth
  col_domain: Relationships
  linkage_type: feeds
  primary_mechanism: "Venus = 2L (wealth lord) AND 7L (relationship lord) = the same planet governs both wealth and relationships = wealth generation and partnership quality are structurally fused; A7 (spouse-image) in 11H (gains house) = the spouse-image is in the wealth-gains domain = the spouse contributes to gains; Shree Lagna in 7H Libra = Lakshmi's grace-point is DIRECTLY in the relationship house = wealth (D2) and relationships (D3) are connected at the Lakshmi-grace level; the Shree Lagna placement in 7H makes D2.D3 a stronger link than previously quantified — the relationship house literally contains the Lakshmi-wealth-grace point"
  msr_anchors: [MSR.403, MSR.336, MSR.391]
  strength: 0.89
  direction: bidirectional
  valence: benefic
  key_finding: "Wealth and relationships are structurally fused — Venus (2L+7L) makes them the same planetary energy; Shree Lagna in 7H Libra places Lakshmi's grace directly in the relationship house, confirming that wealth and relationship quality advance through the same Lakshmi channel."

CDLM.D2.D4:
  row_domain: Wealth
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "Rahu (2H, wealth) = kama-desire that can create excess (Rahu = overindulgence in sensory-material domain Rohini/Taurus = food, pleasure, luxury); classical: wealth excess through Rahu creates health challenges (Pitta excess = overindulgence in Taurus domain = digestive issues, sensory overstimulation); Ketu (8H, health/transformation) = the 2H-8H Rahu-Ketu axis = the native's wealth accumulation energy (Rahu 2H) is in tension with the health-transformation energy (Ketu 8H)"
  msr_anchors: [MSR.393, MSR.369]
  strength: 0.68
  direction: row→col
  valence: malefic
  key_finding: "Wealth accumulation patterns (Rahu 2H's sensory excess tendency) can constrain health — Rohini-Taurus's sensory-richness energy, if unchecked, creates health challenges through overindulgence."

CDLM.D2.D5:
  row_domain: Wealth
  col_domain: Children
  linkage_type: feeds
  primary_mechanism: "5H Leo (children house) is empty; 5L = Sun (from Aries Lagna, 5H=Leo, 5L=Sun) = Sun in 10H career-house; but Venus as 2L (wealth) is Jupiter's dispositor-chain; Jupiter aspects 5H via Jaimini Dual-sign aspect (Sagittarius→Leo) = Jupiter (GK, dharma) provides the 5H with benefic Jaimini aspect; wealth-stability provides the platform for children; classical: 2H (family wealth/speech) stability is prerequisite for 5H (children) flourishing"
  msr_anchors: [MSR.333, MSR.407]
  strength: 0.72
  direction: row→col
  valence: benefic
  key_finding: "Wealth stability (2H Rahu, Venus 2L) feeds the children domain — financial grounding enables the 5H's creative/children potential to manifest; Jupiter's 9H-to-5H Jaimini aspect ensures dharmic wealth supports children."

CDLM.D2.D6:
  row_domain: Wealth
  col_domain: Spirit
  linkage_type: feeds
  primary_mechanism: "Shree Lagna = 7H Libra = the Lakshmi-grace point is in the partnership/relationship house; the spirit-wealth path: Venus as Ishta Devata (Mahalakshmi = wealth-goddess) in 9H = the spiritual fortune-deity IS a wealth deity; the formula: spirit (dharma) → Venus (Ishta Devata, 2L) → wealth activation = the native's wealth comes through spiritual/dharmic channels; bidirectional because material wealth (Venus) also facilitates spiritual practice (Venus in 9H = devotion+wealth); the Shree Lagna in 7H means wealth through relationships is the Lakshmi-mechanism, and Venus (2L in 9H) remains the direct spirit-wealth Venus-Mahalakshmi link"
  msr_anchors: [MSR.407, MSR.403, MSR.397]
  strength: 0.87
  direction: bidirectional
  valence: benefic
  key_finding: "Wealth and spirit feed each other — Venus as Ishta Devata (Mahalakshmi) in 9H is the direct spirit-wealth channel; Shree Lagna in 7H means Lakshmi's grace flows through the partnership domain; wealth comes from spirit and spirit is supported by wealth."

CDLM.D2.D7:
  row_domain: Wealth
  col_domain: Parents
  linkage_type: mirrors
  primary_mechanism: "9H (father's house) = Jupiter+Venus = the father's domain and the dharmic-wealth domain share 9H; Venus (MK, Jaimini mother) = Ishta Devata (Mahalakshmi) = the mother-significator is the fortune-deity = the mother's blessing IS the native's wealth-fortune activation; Jupiter in 9H (father's domain) = the father's dharmic wisdom is the seed of the native's wealth-generation approach; Shree Lagna now in 7H Libra (not 9H) — the direct Lakshmi-grace is in the relationship domain, but the parental 9H still contains Jupiter+Venus which are the primary wealth-enablers"
  msr_anchors: [MSR.403, MSR.407, MSR.342]
  strength: 0.70
  direction: bidirectional
  valence: benefic
  key_finding: "Wealth and parents mirror each other through the 9H — Jupiter+Venus (parental significators) are in the dharma-wealth house; parental dharmic values are the seed of the native's wealth approach; the mother-significator (Venus-MK) as Ishta Devata (Mahalakshmi) encodes parental blessing as wealth-fortune activation."

CDLM.D2.D8:
  row_domain: Wealth
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "Mercury (mind/intelligence) = Yogi Planet AND 10H career planet = when career (which feeds wealth) is active, Mercury is active = mental engagement amplifies wealth delivery; Rahu (2H, wealth) Jaimini-aspects Cancer+Libra+Capricorn (10H = career/mind) = the wealth drive (Rahu) has a Jaimini aspect on the career-mind domain; Mercury's analytical precision (mental domain) IS the mechanism through which wealth is created (tech + AI career = Mercury-mind = wealth production)"
  msr_anchors: [MSR.388, MSR.401, MSR.413]
  strength: 0.86
  direction: row→col
  valence: benefic
  key_finding: "Wealth amplifies mental engagement — financial goals (Rahu 2H ambition) activate Mercury's intelligence (the Yogi), creating a wealth→mind→career→wealth feedback loop."

CDLM.D2.D9:
  row_domain: Wealth
  col_domain: Travel
  linkage_type: feeds
  primary_mechanism: "12H Pisces = Yogi Point + Pranapada = the foreign/isolation domain hosts the fortune-activation point; Venus (2L, wealth lord) in 9H (dharma/long-journeys) = wealth comes through foreign/dharmic long-journeys; the native's wealth is specifically generated in Singapore (foreign land) = travel IS the mechanism of wealth generation; Saham Paradesa (1H, near Lagna) = foreign-travel encoded in identity = the wealth-generating foreign career is structurally mandated from birth"
  msr_anchors: [MSR.392, MSR.399, MSR.381]
  strength: 0.88
  direction: row→col
  valence: benefic
  key_finding: "Wealth feeds travel (and travel feeds wealth) — the native's wealth is generated specifically in a foreign context; the Yogi Point in 12H means fortune itself is in the domain of foreign lands."

---

### ROW D3: RELATIONSHIPS → [All Domains]

CDLM.D3.D1:
  row_domain: Relationships
  col_domain: Career
  linkage_type: mirrors
  primary_mechanism: "7H = Saturn (AmK, career-significator) = the relationship house literally contains the career-planet; UL lord = Mercury (10H, career house) = the marriage-quality indicator's lord is in the career house; AK (Moon 11H) + A7 (11H) = soul and spouse-image in the gains-fulfillment house = relationships and career-gains are in the same house; the native's business partnerships (7H in entrepreneurial charts = business partners) are structurally part of his career"
  msr_anchors: [MSR.391, MSR.338, MSR.400]
  strength: 0.91
  direction: bidirectional
  valence: mixed
  key_finding: "Relationships mirror career — Saturn (AmK) in 7H means the career-force and relationship-karma are the same planet; every significant relationship in this native's life has career implications and vice versa."

CDLM.D3.D2:
  row_domain: Relationships
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "Venus = 7L (relationship) AND 2L (wealth) = relationship quality and wealth generation are structurally the same energy; A7 (spouse) in 11H (gains) = the spouse is in the gains house = the spouse directly contributes to wealth accumulation; Bhrigu Bindu natal in 7H = the chart's most sensitive fortune-timing point is in the relationship house = fortuitous relationship timing = wealth; UL in Gemini 3H = UL lord = Mercury = Yogi = marriage-quality feeds fortune; Shree Lagna in 7H Libra = Lakshmi's grace is directly in the relationship domain = relationships are a direct wealth-activation mechanism"
  msr_anchors: [MSR.403, MSR.236, MSR.338]
  strength: 0.87
  direction: row→col
  valence: benefic
  key_finding: "Relationships feed wealth — Venus as 2L+7L means partnership quality directly determines financial outcomes; the spouse (A7 in 11H) is structurally embedded in the gains domain; Shree Lagna in 7H confirms Lakshmi's grace flows through the relationship domain."

CDLM.D3.D3:
  row_domain: Relationships
  col_domain: Relationships (self-reference)
  linkage_type: amplifies
  primary_mechanism: "7H five-layer convergence: Saturn exalted (quality and discipline) + Mars Avayogi (friction and intensity) + Bhrigu Bindu (fortune-timing sensitivity) + Shree Lagna 7H Libra (Lakshmi-grace) + KP sub=Saturn (KP signature). The relationship domain is self-reinforcing through these five simultaneous systems."
  msr_anchors: [MSR.391, MSR.411, MSR.254]
  strength: 0.93
  direction: bidirectional
  valence: mixed
  key_finding: "The relationship domain is internally amplifying through five systems — Saturn exalted (quality), Mars Avayogi (friction), Bhrigu Bindu (sensitivity), Shree Lagna 7H (Lakshmi-grace), and KP sub=Saturn; 7H remains the chart's primary karmic processing zone."

CDLM.D3.D4:
  row_domain: Relationships
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "Mars (Avayogi) in 7H = the fortune-reducer is in the relationship house; Mars-Saturn conjunction in 7H creates relationship tension that manifests as Vata-Pitta health stress (Mars=Pitta, Saturn=Vata, both in the cardinal 7H creates chronic low-grade tension); Mercury as 6L (health house lord) = health-domain resources are governed by the same planet as the career (Mercury dual-role 6L-10L); relationship friction peaks during Mars/Saturn dashas and Sade Sati periods = these same periods create health challenges; the connection is through shared planetary agents (Mars-Saturn as both relationship and health stressors) rather than through the previously cited Roga Saham in 7H (Roga confirmed in 2H Taurus per v8.0)"
  msr_anchors: [MSR.253, MSR.391, MSR.398]
  strength: 0.68
  direction: row→col
  valence: malefic
  key_finding: "Relationship friction (Mars Avayogi + Saturn conjunction in 7H) constrains health through shared planetary stressors — Mars-Saturn's dual role as both relationship and health stressors (Vata-Pitta imbalance) creates a structural relationship-health link; this link is real but indirect, not through direct Roga Saham placement."

CDLM.D3.D5:
  row_domain: Relationships
  col_domain: Children
  linkage_type: feeds
  primary_mechanism: "PK Mars (children-significator) in 7H (relationship house) = the children-karaka is housed in the marriage domain = children come through and after the relationship; classical: PK in 7H = the children domain is unlocked through the marriage relationship; Saturn (exalted in 7H) = children may be delayed until the relationship is mature and structured (Saturn = delayed-but-certain); once relationship is stable, children follow"
  msr_anchors: [MSR.343, MSR.398]
  strength: 0.78
  direction: row→col
  valence: mixed
  key_finding: "Relationship stability feeds the children domain — PK Mars in 7H means children are unlocked through marriage; relationship maturity is the prerequisite for children-domain fulfillment."

CDLM.D3.D6:
  row_domain: Relationships
  col_domain: Spirit
  linkage_type: mirrors
  primary_mechanism: "AK Moon (soul) + A7 (spouse-image) both in 11H = the soul's domain and the spouse-image are in the same house; AK-DK connection (Moon + Mercury in adjacent houses) = the soul (AK) and spouse-significator (DK) are closely linked = marriage is a soul-expression; Jaimini: AK-DK in trikona = the soul and spouse are in a dharmic (trikona) relationship; the native's spouse mirrors the soul = spiritual depth IS the relationship depth; Shree Lagna in 7H Libra = Lakshmi's grace in the relationship domain further confirms the spiritual-relational fusion"
  msr_anchors: [MSR.330, MSR.336, MSR.340]
  strength: 0.86
  direction: bidirectional
  valence: benefic
  key_finding: "Relationships mirror spiritual depth — the AK-DK soul-spouse connection means the native's marriage is a soul-mirror; Shree Lagna in 7H confirms Lakshmi's grace is in the relationship domain; spiritual evolution and relationship quality advance together."

CDLM.D3.D7:
  row_domain: Relationships
  col_domain: Parents
  linkage_type: constrains
  primary_mechanism: "7H (marriage) vs 4H (mother) and 9H (father) = the 7H-4H relationship = the 4th house from the 4th = the 7H is structurally in tension with the 4H (kendra opposition); Mars in 7H (Avayogi) = relationship friction can spill into family-of-origin contexts; UL in 3H (Gemini) = the marriage-quality indicator is in the 3H = short-journeys/communication/siblings house which is in tension with the parental houses (4H and 9H)"
  msr_anchors: [MSR.338, MSR.343]
  strength: 0.60
  direction: row→col
  valence: mixed
  key_finding: "Relationships partially constrain the parental domain — the 7H's Mars-friction (Avayogi) can create family-of-origin tensions when relationship stress is high; moderate link, not a primary structural constraint."

CDLM.D3.D8:
  row_domain: Relationships
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "Moon (AK, mind-emotion planet) + A7 (spouse-image) both in 11H = the emotional-mind domain and the spouse-image share the same house; Mercury (DK, spouse-significator) = Mercury governs the mind (intelligence) AND is the spouse-significator (DK) = the spouse amplifies mental functioning; when relationships are harmonious, Mercury-quality mind is at full power; when disrupted, Mercury (Avayogi-adjacent through Mars-connection) creates mental agitation"
  msr_anchors: [MSR.330, MSR.388]
  strength: 0.82
  direction: bidirectional
  valence: benefic
  key_finding: "Relationships amplify mental functioning — Mercury as DK (spouse) and Yogi (fortune/mind) means a harmonious marriage directly amplifies the native's mental clarity and analytical power."

CDLM.D3.D9:
  row_domain: Relationships
  col_domain: Travel
  linkage_type: feeds
  primary_mechanism: "UL = Gemini 3H = the marriage-quality indicator is in the 3H (short journeys, communication) = the spouse's domain is connected to travel; 7H Saturn (AmK) Jaimini-aspects 3H (dual sign: Libra movable → Gemini dual) = the relationship planet has a Jaimini aspect on the travel-communication domain; the native's spouse (Gemini UL) is likely associated with travel or communication domains"
  msr_anchors: [MSR.338, MSR.335]
  strength: 0.68
  direction: row→col
  valence: benefic
  key_finding: "Relationships feed travel — UL in Gemini 3H (short-journey house) and Saturn's Jaimini aspect on 3H suggests spouse and relationships are connected to the native's travel and communication patterns."

---
### ROW D4: HEALTH → [All Domains]

CDLM.D4.D1:
  row_domain: Health
  col_domain: Career
  linkage_type: constrains
  primary_mechanism: "6H (service/health) = Virgo; 6L = Mercury (from Aries Lagna, 6H=Virgo, 6L=Mercury); Mercury = 10H career planet = the health house lord IS the career planet = health domain and career domain share Mercury as their linking planet; when health challenges emerge (6H activated), Mercury's career delivery is disrupted; Muntha at 6H (age 42) = the annual chart's most sensitive timing point is in the health house at this age = career has a health-sector constraint window in 2026"
  msr_anchors: [MSR.377, MSR.334]
  strength: 0.76
  direction: row→col
  valence: malefic
  key_finding: "Health directly constrains career — 6L Mercury (health house lord) = career planet; health disruptions pull Mercury's energy away from career delivery; the 2026 Muntha in 6H is the primary annual health-career constraint window."

CDLM.D4.D2:
  row_domain: Health
  col_domain: Wealth
  linkage_type: constrains
  primary_mechanism: "8H Scorpio (Ketu, exalted) = sudden health events can create unexpected financial demands; classical 8H = sudden expenditures, medical costs, hidden financial drains; Ketu in 8H = past-life health patterns that may manifest as unexpected medical events; Mandi in Cancer 4H (malefic, inauspicious upagraha) = health challenges in the 4H domain (home/mental) can create financial pressure; A6 (enemies) in 2H (wealth) = financial competition can emerge from health-related disputes"
  msr_anchors: [MSR.248, MSR.393]
  strength: 0.68
  direction: row→col
  valence: malefic
  key_finding: "Health challenges constrain wealth — 8H Ketu's sudden transformation energy + Mandi in 4H create a structural risk that health events can drain financial resources unexpectedly."

CDLM.D4.D3:
  row_domain: Health
  col_domain: Relationships
  linkage_type: constrains
  primary_mechanism: "Saturn in 7H (exalted AmK) = Saturn is the simultaneous Sade Sati trigger — when Saturn transits Aquarius/Pisces (Sade Sati Setting 2025-2028), it creates concurrent health-adjustment and relationship-domain Saturn themes; these are not mechanically linked by a shared house but by a shared planetary agent (Saturn); Rahu co-tenant with Roga Saham in 2H Taurus = health challenges emerge from the 2H domain (speech, family-wealth, Vata constitution) rather than 7H; Venus as 7L (relationship lord) governs digestive/hormonal channels in Ayurvedic astrology = when health challenges activate Venus-domain (2H Rahu-Rohini = sensory/appetite patterns), the relationship domain (Venus 7L) is also touched; the connection is real but indirect — health affects relationships through Saturn's simultaneous presence and Venus's dual 2L-7L governance; the direct Roga-in-7H mirror basis has been removed"
  msr_anchors: [MSR.253, MSR.391, MSR.291]
  strength: 0.61
  direction: row→col
  valence: mixed
  key_finding: "Health constrains relationships through indirect mechanisms — Saturn's Sade Sati creates simultaneous health-adjustment and relationship-domain stress; Rahu-Roga co-tenancy in 2H Taurus channels health challenges through the Vata/speech/family domain which reaches the relationship sphere via Venus's 2L-7L dual role; this is a real but indirect constraint, not a direct mirror."

CDLM.D4.D4:
  row_domain: Health
  col_domain: Health (self-reference)
  linkage_type: compensates
  primary_mechanism: "8H Ketu (exalted, transformation) = health challenges are met with Ketu's capacity for complete dissolution and rebirth; Jupiter+Venus (9H) Jaimini Dual-sign aspects Scorpio 8H = the benefics supervise the health-transformation domain from 9H; Ketu (exalted) = any health challenges are navigated with maximum Ketu-strength (past-life healing capacity, intuitive health awareness); the health domain compensates its own challenges through Ketu's exalted regeneration"
  msr_anchors: [MSR.402, MSR.333, MSR.347]
  strength: 0.80
  direction: bidirectional
  valence: mixed
  key_finding: "The health domain is self-compensating — Ketu exalted in 8H means health challenges are met with extraordinary regenerative capacity; Jupiter+Venus's Jaimini supervision of 8H provides dharmic protection."

CDLM.D4.D5:
  row_domain: Health
  col_domain: Children
  linkage_type: constrains
  primary_mechanism: "5H Leo (children) = 10th from 8H (health/transformation) = the classical child-health connection; PK Mars (children) is in 7H (Avayogi = fortune-reducer) = the children-significator is not at full strength; Gulika in Gemini 3H (inauspicious upagraha) = a background health/obstacle signature in the communication domain; classical: the health of the native and the children are correlated (8H to 5H is a 9H relationship = dharmic connection)"
  msr_anchors: [MSR.343, MSR.247, MSR.398]
  strength: 0.62
  direction: row→col
  valence: malefic
  key_finding: "Health challenges weakly constrain the children domain — PK Mars's Avayogi status + Gulika's presence create background friction; health needs to be attended before children-domain energy can fully manifest."

CDLM.D4.D6:
  row_domain: Health
  col_domain: Spirit
  linkage_type: feeds
  primary_mechanism: "8H Ketu (health-transformation house) = moksha-karaka = the transformation/health house is simultaneously the liberation house; health challenges in this chart push the native toward spiritual depth; Ketu exalted in 8H = health events are spiritually catalytic rather than merely physically difficult; the native's Vishnu devotional shift (EVT.2025) may partly be catalyzed by health/transformation awareness from 8H Ketu's themes activating during Sade Sati Setting"
  msr_anchors: [MSR.402, MSR.408, MSR.297]
  strength: 0.82
  direction: row→col
  valence: benefic
  key_finding: "Health feeds spirit — Ketu (exalted, 8H) transforms health challenges into spiritual catalysts; the moksha-house and health-house are structurally the same in this chart."

CDLM.D4.D7:
  row_domain: Health
  col_domain: Parents
  linkage_type: mirrors
  primary_mechanism: "4H = mother's domain AND home AND emotional security; Mandi in Cancer 4H (malefic upagraha in mother's house) = a background health/obstacle signature in the mother's domain; Moon (AK, mother-karaka in classical Parashari) in 11H = the mother's significator is in the gains domain (potentially away from native = mother is in a different location from the native's gains-zone); MK Venus (Jaimini mother-significator) in 9H = the mother is in the dharma-foreign domain; health of parents is a concern through Mandi-4H"
  msr_anchors: [MSR.248, MSR.342]
  strength: 0.65
  direction: bidirectional
  valence: mixed
  key_finding: "Health and parents share a weak structural link through Mandi in 4H — the mother's domain has a background malefic upagraha; parental health and the native's home-emotional security are mildly linked."

CDLM.D4.D8:
  row_domain: Health
  col_domain: Mind
  linkage_type: constrains
  primary_mechanism: "Moon (mind-emotion planet) in 11H Aquarius; 4H = emotional security (Moon's natural domain); Mandi in Cancer 4H = emotional-mental challenge in the native's emotional home; Purva Bhadrapada (Moon's nakshatra) = Ugra (fierce) = the emotional-mental nature is intense by default; health challenges in the emotional/4H domain (Mandi, Sade Sati mental effects) directly constrain mental clarity; classical: Moon = mind = when Moon-related domains are under stress (Sade Sati), mental functioning is taxed"
  msr_anchors: [MSR.295, MSR.369, MSR.371]
  strength: 0.78
  direction: row→col
  valence: malefic
  key_finding: "Health constrains mind — emotional health (4H/Moon domain) directly determines mental functioning; Sade Sati periods and Mandi-4H activations reduce the native's mental clarity."

CDLM.D4.D9:
  row_domain: Health
  col_domain: Travel
  linkage_type: constrains
  primary_mechanism: "Health challenges naturally limit travel; 6H (health/service) and 12H (foreign lands/isolation) are in a 7th-axis relationship (6H-12H = the health-isolation axis); when health is challenged (6H active), the 12H foreign domain is co-activated = health challenges can occur in foreign contexts or be related to foreign-environment health demands; the native lives in Singapore (12H foreign context) = health management must account for the foreign-living context"
  msr_anchors: [MSR.392, MSR.381]
  strength: 0.60
  direction: row→col
  valence: mixed
  key_finding: "Health weakly constrains travel — the health-isolation axis (6H-12H) means health challenges can limit foreign travel capacity; the native's Singapore residence makes health management in a foreign environment a structural concern."

---

### ROW D5: CHILDREN → [All Domains]

CDLM.D5.D1:
  row_domain: Children
  col_domain: Career
  linkage_type: constrains
  primary_mechanism: "5L = Sun (5H Leo from Aries Lagna, 5L=Sun) = Sun in 10H career house = the children-lord is in the career house = children-energy and career compete for the same planetary energy (Sun in 10H); PK Mars (Avayogi) in 7H = the children-significator is the fortune-reducer; classical: when PK is with or influenced by the Avayogi (Mars IS PK AND Avayogi), children-energy timing conflicts with fortune activation"
  msr_anchors: [MSR.398, MSR.343]
  strength: 0.70
  direction: row→col
  valence: malefic
  key_finding: "Children domain constrains career — the children-lord (Sun) shares the career house; child-rearing phases require career-energy redistribution; the Avayogi PK Mars creates a structural children-career tension."

CDLM.D5.D2:
  row_domain: Children
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "5H = creativity and intelligence (not just literal children); Jupiter Jaimini-aspects 5H (Leo) from 9H (Sagittarius dual) = the dharmic-wealth benefic (Jupiter, GK own-sign) supervises the creativity-children domain = creative outputs (5H) produce wealth; the native's 5H Leo (creativity-intelligence) receives Jupiter's aspect = intellectual creativity IS a wealth-generator; Mercury (intelligence) in 10H = the 5H intellectual products → 10H career delivery → wealth"
  msr_anchors: [MSR.333, MSR.413]
  strength: 0.74
  direction: row→col
  valence: benefic
  key_finding: "Creative/children energy feeds wealth — the 5H (creativity, intelligence) receives Jupiter's benefic supervision; creative intellectual output (the native's AI/tech work = Mercury-5H-Jupiter-intelligence) is a direct wealth-source."

CDLM.D5.D3:
  row_domain: Children
  col_domain: Relationships
  linkage_type: feeds
  primary_mechanism: "PK Mars in 7H = the children-significator is in the relationship house = children come through relationships; classical: children (5H) are the natural fruit of marriage (7H); the 7H-5H trine relationship (5th from 7H = 11H; 9th from 5H = 1H) = the marriage domain and children domain are in a trikona-ish support structure; when relationships mature and stabilize (Saturn exalted in 7H = long-term structural stability), children domain follows"
  msr_anchors: [MSR.343, MSR.391]
  strength: 0.76
  direction: row→col
  valence: benefic
  key_finding: "Children feed through relationships — PK Mars in 7H makes children the natural continuation of the marriage relationship; relationship maturity is the prerequisite for children-domain activation."

CDLM.D5.D4:
  row_domain: Children
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "5H Leo (children) = the 12th house from the 6H health house = 5H and 6H are adjacent = children-domain activation can affect the health domain through adjacent house energy; PK Mars (Avayogi) in 7H = Mars-activation periods reduce fortune AND are related to children karma = these same periods have health implications (Avayogi Mars = health-fortune connection)"
  msr_anchors: [MSR.398, MSR.253]
  strength: 0.58
  direction: row→col
  valence: mixed
  key_finding: "Children weakly constrain health — the adjacent 5H-6H relationship and Mars Avayogi's dual role (children-PK + health-stress-creator) create a mild children-health structural link; this is not a primary constraint."

CDLM.D5.D5:
  row_domain: Children
  col_domain: Children (self-reference)
  linkage_type: compensates
  primary_mechanism: "5H Leo = empty (no natal planet) = a seeming weakness; BUT: Jupiter (GK, own sign 9H) Jaimini Dual-sign aspects Leo 5H = the most dharmic planet (Jupiter own-sign = maximum strength) provides Jaimini Rashi Drishti to the children-house; this compensates for the 5H's emptiness with Jupiter's maximum-strength wisdom-aspect; Leo 5H = Sun-ruled = Sun in 10H (career) = the 5H lord is strong; the children domain compensates its natal emptiness through Jupiter's supervision and Sun's 10H strength"
  msr_anchors: [MSR.333, MSR.341, MSR.118]
  strength: 0.75
  direction: bidirectional
  valence: benefic
  key_finding: "The children domain compensates its natal emptiness — Jupiter's maximum-strength Jaimini aspect on Leo 5H provides the missing planet's energy; children-domain results come through dharmic effort (Jupiter-quality) rather than spontaneous ease."

CDLM.D5.D6:
  row_domain: Children
  col_domain: Spirit
  linkage_type: mirrors
  primary_mechanism: "5H = creativity + intelligence + past-life merit (purva punya); in Jyotish, 5H is also the house of mantras, spiritual practices, and devotion; Jupiter (5L by its own reckoning as the natural 5H significator = Jupiter is karka of 5H in Parashari) is the GK and own-sign in 9H = the spiritual benefic is the children-domain natural karaka; Jupiter-5H-9H = the children and spiritual domains share Jupiter as their common benefic energy"
  msr_anchors: [MSR.333, MSR.341, MSR.406, MSR.119]
  strength: 0.78
  direction: bidirectional
  valence: benefic
  key_finding: "Children and spirit mirror each other through Jupiter — both the 5H (purva punya, spiritual merit) and 9H (dharma, spiritual wisdom) are Jupiter-domain expressions; spiritual depth produces the merit that enables children, and children inspire spiritual growth."

CDLM.D5.D7:
  row_domain: Children
  col_domain: Parents
  linkage_type: feeds
  primary_mechanism: "5H (children, next generation) and 4H (mother, previous generation) = the generational flow; 5H Leo lord = Sun; 9H (father) = Jupiter+Venus; classical: the trinal houses (1H, 5H, 9H) form the dharmic-purva-punya axis = the ancestors (9H father-dharma) feed the progeny (5H children) through the native (1H); the native is the middle link in the generational dharmic chain; parental blessings (9H) enable children-fulfillment (5H)"
  msr_anchors: [MSR.394, MSR.407, MSR.143]
  strength: 0.72
  direction: row→col
  valence: benefic
  key_finding: "The children domain feeds the parental legacy — as the middle link in the 1H-5H-9H dharmic axis, the native's children fulfillment completes the dharmic chain from parents (9H) through self (1H) to next generation (5H)."

CDLM.D5.D8:
  row_domain: Children
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "5H = intelligence and discrimination (buddhi) in classical Jyotish; Mercury (mind-planet par excellence) in 10H with Mercury's Vargottama = the intelligence domain's highest expression; 5H Purva Punya and intellectual capacity → Moon (mind, AK) = the native's intelligence IS his emotional-mind's primary expression tool; Jupiter's Jaimini aspect on 5H (Leo) from 9H = wisdom amplifies the children-intelligence domain"
  msr_anchors: [MSR.333, MSR.388]
  strength: 0.78
  direction: row→col
  valence: benefic
  key_finding: "Children/creativity amplify the mind — the 5H (intelligence, purva punya) and Mercury (10H mind-planet) share Jupiter's supervisory energy; intellectual creativity (5H) and analytical mind (Mercury) amplify each other."

CDLM.D5.D9:
  row_domain: Children
  col_domain: Travel
  linkage_type: constrains
  primary_mechanism: "Children (5H) and travel (9H, 12H) compete for the same 9H domain — 5H and 9H are in a 5-9 trikona (same dharmic axis) but 9H is shared between spiritual dharma AND father AND foreign travel; when foreign travel (12H) or long-distance dharmic journeys (9H) consume energy, the 5H trikona partner may be deprioritized; classical: heavy travel/foreign commitments can delay family expansion"
  msr_anchors: [MSR.394, MSR.381]
  strength: 0.60
  direction: row→col
  valence: mixed
  key_finding: "Children and travel share the 5-9 dharmic axis — heavy foreign travel commitments (the native's Singapore career = ongoing 9H-12H demand) may structurally compete with children-domain fulfillment."

---

### ROW D6: SPIRIT → [All Domains]

CDLM.D6.D1:
  row_domain: Spirit
  col_domain: Career
  linkage_type: feeds
  primary_mechanism: "Shree Lagna = 7H Libra = Lakshmi's grace-point is in the relationship house (Libra); the spirit-career connection: Saturn (AmK, career) is in 7H = the career-planet is in the same house as the Shree Lagna = career excellence and Lakshmi's grace share the same astrological space; Saturn (Libra movable) Jaimini-aspects Sagittarius (Dual) = the career-planet (Saturn AmK) has a Jaimini aspect ON the spirit-domain (Sagittarius 9H); bidirectional spiritual-career feed; Mercury = Palana Devata (sustaining deity) AND career planet (10H) = career AS spiritual sustenance; Jupiter+Venus in 9H (spirit-dharma) provide the spiritual depth that feeds the career"
  msr_anchors: [MSR.325, MSR.397, MSR.407]
  strength: 0.89
  direction: bidirectional
  valence: benefic
  key_finding: "Spirit feeds career and career feeds spirit — Saturn (AmK, career) in 7H shares the house with Shree Lagna (Lakshmi-grace); Palana Devata Mercury IS the career deliverer; the native's career excellence IS his dharmic-spiritual practice."

CDLM.D6.D2:
  row_domain: Spirit
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "Shree Lagna = 7H Libra = the Lakshmi-grace point is in the partnership/relationship domain rather than the dharmic-spiritual 9H; the direct spirit-wealth channel is now through Venus: Venus as Ishta Devata (Mahalakshmi = wealth-goddess) in 9H = the spiritual fortune-deity IS a wealth deity AND is in the spirit domain; the formula: dharmic spiritual practice → Venus Ishta Devata (Mahalakshmi 9H) → Venus as 2L (wealth lord) → wealth; Shree Lagna in 7H means the Lakshmi-grace flows through the relationship domain first (D6→D3→D2 indirect path) rather than directly (D6→D2 via 9H Shree Lagna); Jupiter (9H, own sign) + Venus (9H) = the 9H spirit domain remains very well-resourced for generating wealth, but via Venus-Mahalakshmi channel rather than Shree Lagna"
  msr_anchors: [MSR.407, MSR.403, MSR.397]
  strength: 0.84
  direction: row→col
  valence: benefic
  key_finding: "Spirit feeds wealth — Venus as Ishta Devata (Mahalakshmi) in 9H is the primary spirit-wealth channel; Shree Lagna in 7H means Lakshmi's grace flows through partnerships rather than directly through the spirit domain; the spirit→wealth path is real but now mediated through Venus-Mahalakshmi and partnership channels."

CDLM.D6.D3:
  row_domain: Spirit
  col_domain: Relationships
  linkage_type: mirrors
  primary_mechanism: "AK Moon (soul/spirit) + A7 (spouse-image) both in 11H = soul and spouse-image share the same domain; AK-DK (Moon-Mercury) connection = the soul and spouse-significator are adjacent and mutually reinforcing; D9 Moon in Gemini (Karakamsa = Mercury's sign) = in the soul's D9 map, the soul IS in the spouse-significator's territory; the spouse (DK Mercury) and the soul (AK Moon) are structurally linked = the marriage IS a spiritual relationship in this chart's architecture; Shree Lagna in 7H Libra = Lakshmi's grace-point is directly in the relationship domain, confirming the spirit-relationship structural fusion"
  msr_anchors: [MSR.330, MSR.336, MSR.348]
  strength: 0.86
  direction: bidirectional
  valence: benefic
  key_finding: "Spirit and relationships mirror each other — AK-DK adjacency, A7-AK co-location in 11H, D9 Karakamsa, and Shree Lagna in 7H all confirm the native's marriage is a soul-level spiritual relationship; Lakshmi's grace is directly in the relationship domain."

CDLM.D6.D4:
  row_domain: Spirit
  col_domain: Health
  linkage_type: compensates
  primary_mechanism: "Ketu (exalted, 8H) = moksha-liberation energy in the health-transformation house = spiritual depth compensates health challenges; Jupiter+Venus (9H) Jaimini-aspects Scorpio 8H (health-transformation) = the spiritual benefics provide dharmic protection to the health domain; the native's spiritual evolution (Vishnu devotion, 2025) activates the Palana Devata (Mercury = sustaining) and Dharma Devata (Saturn = Venkateswara) = spiritual alignment with the devatas sustains health through dharmic protection"
  msr_anchors: [MSR.402, MSR.397, MSR.347]
  strength: 0.80
  direction: row→col
  valence: benefic
  key_finding: "Spirit compensates health challenges — Ketu exalted in 8H means health transformations are spiritually guided; Jupiter+Venus's 9H-to-8H Jaimini supervision provides dharmic protection for health."

CDLM.D6.D5:
  row_domain: Spirit
  col_domain: Children
  linkage_type: feeds
  primary_mechanism: "5H = purva punya (past-life merit) = the result of spiritual practice across lifetimes; Jupiter (5H natural karaka) is the GK in own sign 9H (spirit-domain) = the spirit-domain's own planet IS the 5H natural karaka; when spiritual merit (9H, Jupiter) is cultivated, 5H results (children, creative intelligence, purva punya benefits) naturally flow; classical: the 9H (dharma) → 5H (purva punya) axis is the dharmic-trikona; spiritual practice in this life activates past-life merit for children/creativity"
  msr_anchors: [MSR.333, MSR.341, MSR.406]
  strength: 0.78
  direction: row→col
  valence: benefic
  key_finding: "Spirit feeds children/creativity — Jupiter as 9H GK (own-sign) directly supervises the 5H; spiritual practice activates purva punya (5H) which manifests as children-blessings and creative intelligence."

CDLM.D6.D6:
  row_domain: Spirit
  col_domain: Spirit (self-reference)
  linkage_type: amplifies
  primary_mechanism: "The spiritual domain in this chart is comprehensively resourced through six confirmed mechanisms (v8.0 corrected): (1) Ketu (exalted, 8H = moksha-house) — liberation and past-life spiritual depth; (2) Jupiter (own sign, 9H dharma) — maximum wisdom and dharmic authority; (3) Venus (own nakshatra, 9H devotion) — devotional practice and Mahalakshmi connection; (4) Shree Lagna in 7H Libra (Lakshmi-grace in the partnership domain = spiritual wealth through relationships); (5) Yogi Point (12H spiritual-fortune) + Pranapada (12H life-breath) = fortune and life-breath in the moksha domain; (6) Devatas system: Vishnu=Mercury=Karakamsa, Venkateswara=Saturn=Dharma, Mahalakshmi=Venus=Ishta = three-deity personal spiritual architecture; Ghati Lagna is now confirmed in 9H Sagittarius (not 8H Scorpio) and Varnada Lagna in 4H Cancer (not 8H Scorpio) per FORENSIC v8.0; these two lagnas reinforce the 9H and 4H spiritual dimensions rather than 8H"
  msr_anchors: [MSR.408, MSR.402, MSR.397, MSR.407]
  strength: 0.94
  direction: bidirectional
  valence: benefic
  key_finding: "The spirit domain is the chart's most self-amplifying domain after career — six confirmed spiritual mechanisms (Ketu exalted 8H, Jupiter own-sign 9H, Venus devotional 9H, Shree Lagna 7H, Yogi+Pranapada 12H, Devata system) all reinforce each other; spiritual evolution is structurally unstoppable; Ghati and Varnada lagnas reinforce the 9H dharma and 4H emotional foundation dimensions."

CDLM.D6.D7:
  row_domain: Spirit
  col_domain: Parents
  linkage_type: feeds
  primary_mechanism: "9H = father's house AND dharma/spirit house; Jupiter+Venus in 9H = the father's domain and the spirit domain share the same house; the native's father (9H Jupiter = GK, dharma, wisdom) = the father is a dharmic-spiritual figure; parental dharmic values (9H) are the seed of the native's spiritual evolution; MK Venus (Jaimini mother) in 9H with Jupiter = the mother-significator is in the spiritual domain = the mother's influence is spiritual/dharmic in nature"
  msr_anchors: [MSR.342, MSR.394, MSR.374]
  strength: 0.82
  direction: bidirectional
  valence: benefic
  key_finding: "Spirit and parents are structurally fused in 9H — the father's house (9H) is the same house as the spirit domain; both parents (Jupiter-GK for father, Venus-MK for mother) are in the spiritual domain; the native's spiritual orientation is seeded by parental dharmic influence."

CDLM.D6.D8:
  row_domain: Spirit
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "Moon (AK, soul/spirit) = the mind-planet in Jyotish = the spirit-domain's primary planet IS the mind-planet; when the soul (Moon, AK) is spiritually active, the mind follows; Purva Bhadrapada (Ugra, Jupiter-ruled) = the janma nakshatra is spiritually intense = the spiritual intensity of the birth nakshatra infuses the mind's natural operating mode; Aja Ekapada (devata) = threshold-deity = the mind's guardian is a liminal deity = the mind naturally operates near spiritual thresholds"
  msr_anchors: [MSR.374, MSR.406, MSR.353]
  strength: 0.88
  direction: bidirectional
  valence: benefic
  key_finding: "Spirit amplifies mind — Moon (AK/soul) = the mind-planet; spiritual depth and mental clarity are the same energy in this chart; Purva Bhadrapada's fierce spiritual quality infuses the mind's natural operating mode."

CDLM.D6.D9:
  row_domain: Spirit
  col_domain: Travel
  linkage_type: feeds
  primary_mechanism: "12H (foreign lands/isolation) = Yogi Point + Pranapada = the spiritual-fortune and life-breath points are in the foreign domain; 9H (dharma/spirit/long-journeys) = Jupiter+Venus = the spirit domain and the long-journey/pilgrimage domain are the same house; the native's foreign living (Singapore = 12H) is simultaneously a spiritual domain (12H = moksha/spiritual retreat) and a fortune-activation domain (Yogi Point); pilgrimage and spiritual travel are built into the chart's 9H-12H spiritual-travel axis"
  msr_anchors: [MSR.392, MSR.394, MSR.407]
  strength: 0.85
  direction: bidirectional
  valence: benefic
  key_finding: "Spirit feeds travel and travel feeds spirit — the 9H (spirit/long-journeys) and 12H (foreign/isolation) are the spiritual and travel domains simultaneously; the native's foreign residence is a living spiritual practice, not just a career choice."

---

### ROW D7: PARENTS → [All Domains]

CDLM.D7.D1:
  row_domain: Parents
  col_domain: Career
  linkage_type: feeds
  primary_mechanism: "Sun (pitru-karaka, father-significator) in 10H career house = the father's energy is in the career house; Pitri Saham in Capricorn 10H = the father-sensitive-point is literally in the career domain; the Sunday birth (Surya vara) = the father's planetary day is the birth-day = the father's energy inaugurates the life's panchang = a paternal-career imprint at the birth-level; Sunday + 10H Sun = the father's planetary energy and the career house are structurally fused"
  msr_anchors: [MSR.344, MSR.359, MSR.252]
  strength: 0.80
  direction: row→col
  valence: benefic
  key_finding: "Parental energy (especially father) feeds career — Sun (father-significator) in 10H career house + Pitri Saham in 10H = the father's domain and the career domain are in the same house; paternal dharmic values and career are structurally connected."

CDLM.D7.D2:
  row_domain: Parents
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "9H (father's house) = Jupiter+Venus = the father's domain contains the primary wealth-enablers; Venus (MK, Jaimini mother) = Ishta Devata (Mahalakshmi) = the mother-significator is the fortune-deity = the mother's blessing IS the native's wealth-fortune activation; Jupiter in 9H (father's domain) = the father's dharmic wisdom is the seed of the native's wealth-generation approach; Shree Lagna is now in 7H Libra (not 9H) — parental domain (9H) no longer contains the Shree Lagna, but Jupiter+Venus in 9H remain powerful wealth-enablers through their own dignities"
  msr_anchors: [MSR.403, MSR.407, MSR.342]
  strength: 0.76
  direction: row→col
  valence: benefic
  key_finding: "Parents feed wealth — Jupiter+Venus in the father's domain (9H) and Venus-MK as Ishta Devata (Mahalakshmi) encode parental blessings as wealth-activation mechanisms; paternal dharmic values are the seed of the native's wealth approach."

CDLM.D7.D3:
  row_domain: Parents
  col_domain: Relationships
  linkage_type: constrains
  primary_mechanism: "4H (mother's house) = Cancer, empty; Mandi in Cancer 4H (malefic upagraha in mother's domain); the 4H is the 10th from the 7H (relationship house) = the mother's domain is the 'career' of the relationship domain = parental approval and home-stability affect relationship outcomes; MK Venus (mother) in 9H = the mother is in a foreign/dharmic domain = the mother may be physically distant from the native's relationship context (Singapore = 12H foreign, the mother is in a different country)"
  msr_anchors: [MSR.342, MSR.248]
  strength: 0.62
  direction: row→col
  valence: mixed
  key_finding: "Parental domain weakly constrains relationships — Mandi in 4H (mother's house) creates background friction; physical distance of parents from the native's relationship context (foreign residence) is a mild structural constraint."

CDLM.D7.D4:
  row_domain: Parents
  col_domain: Health
  linkage_type: mirrors
  primary_mechanism: "4H (mother) = home = emotional foundation; emotional security (4H) and health (6H, 8H) are classically linked; when the mother's domain (4H) is stable, emotional health follows; Mandi in 4H (Cancer) = background health/obstacle in the mother-home domain; the native lives abroad (12H) = the 4H home-stability has a structural fracture (not living in the native's home country); this fracture has emotional-health implications"
  msr_anchors: [MSR.248, MSR.392]
  strength: 0.65
  direction: bidirectional
  valence: mixed
  key_finding: "Parents and health mirror each other through the 4H — the mother's domain (4H) and emotional health are the same house; Mandi's presence in 4H creates a background health-home tension; the foreign residence creates a 4H-12H emotional fracture."

CDLM.D7.D5:
  row_domain: Parents
  col_domain: Children
  linkage_type: feeds
  primary_mechanism: "Classical dharmic axis: 4H (mother) → 1H (self) → 5H (children) = the generational chain; 9H (father) and 5H (children) are in a trikona (5th from 9H = 1H; 9th from 5H = 1H = the native is the link); parental dharmic legacy (9H Jupiter = wisdom, 4H mother's nourishment) seeds the next generation (5H children); the native's parents' dharmic values (9H) become the foundation for his children's purva punya (5H)"
  msr_anchors: [MSR.394, MSR.407]
  strength: 0.73
  direction: row→col
  valence: benefic
  key_finding: "Parents feed children — the 4H-1H-5H generational axis means parental dharmic values flow through the native to the children domain; grandparental dharma becomes grandchildren's purva punya."

CDLM.D7.D6:
  row_domain: Parents
  col_domain: Spirit
  linkage_type: mirrors
  primary_mechanism: "9H = father's house AND dharma/spirit domain = same house; Jupiter (9L, own sign, GK) = the father's planetary significator (9H lord = Jupiter from Sagittarius) = Jupiter governs both the father's domain AND the spirit domain = the father IS a spiritual figure for this native; MK Venus (mother) = Ishta Devata (Mahalakshmi) = the mother IS the fortune-deity's embodiment; parental figures = spiritual archetypes in this chart"
  msr_anchors: [MSR.342, MSR.394, MSR.397]
  strength: 0.83
  direction: bidirectional
  valence: benefic
  key_finding: "Parents mirror the spirit domain — the father's house (9H) IS the spirit-dharma domain; both parents (Jupiter for father, Venus/Mahalakshmi for mother) are spiritual archetypes; parental relationships are the first spiritual relationships in this native's life."

CDLM.D7.D7:
  row_domain: Parents
  col_domain: Parents (self-reference)
  linkage_type: compensates
  primary_mechanism: "Jupiter (GK, own sign 9H) + Venus (MK, own nakshatra, 9H) = both parental significators at maximum strength in the same house; the parents' domain compensates any challenges (Mandi in 4H, foreign-living distance) through the extraordinary 9H strength; Jupiter-GK own-sign = even parental challenges are overcome by Jupiter's own-sign dharmic force; Shree Lagna now in 7H Libra (not 9H) — the 9H remains the most benefic-dense house in the chart even without Shree Lagna"
  msr_anchors: [MSR.394, MSR.407, MSR.341]
  strength: 0.82
  direction: bidirectional
  valence: benefic
  key_finding: "The parents domain self-compensates — Jupiter (GK, own-sign) and Venus (MK, own-nakshatra) both at maximum strength in 9H; any parental challenges (Mandi 4H) are compensated by the extraordinary 9H benefic density."

CDLM.D7.D8:
  row_domain: Parents
  col_domain: Mind
  linkage_type: feeds
  primary_mechanism: "4H (mother) = emotional foundation and security = the emotional-mental platform; Moon (mind-planet, AK) in 11H Aquarius = the mind's primary planet is in gains-fulfillment; the 4H emotional security (mother's nourishment) is the foundation on which the Moon's 11H mental-emotional expression rests; a secure 4H foundation (mother's domain stable) enables the Moon (mind) to operate from 11H gains rather than from 4H-deficiency anxiety"
  msr_anchors: [MSR.406, MSR.353]
  strength: 0.72
  direction: row→col
  valence: benefic
  key_finding: "Parental security feeds mental functioning — the 4H emotional foundation (mother's domain) is the platform for Moon's (mind's) 11H operation; parental stability enables higher-level mental functioning."

CDLM.D7.D9:
  row_domain: Parents
  col_domain: Travel
  linkage_type: constrains
  primary_mechanism: "The native lives in Singapore (abroad, 12H foreign) = physically distant from parents (who are in India = native's 4H/9H parental home); this creates a recurring constraint: foreign living (travel domain, 12H) competes with parental proximity (4H home, 9H father); Saham Paradesa (foreign travel, 1H near Lagna) = the foreign-travel destiny is natal = the parents-travel tension is structural and ongoing; the native's career destiny requires foreign residence which creates a permanent parental-proximity constraint"
  msr_anchors: [MSR.399, MSR.381]
  strength: 0.78
  direction: row→col
  valence: malefic
  key_finding: "Parental proximity constrains (and is constrained by) the foreign travel domain — the native's Singapore career (12H foreign) permanently separates him from parents (4H/9H = India); this is the chart's primary intergenerational structural tension."

---

### ROW D8: MIND → [All Domains]

CDLM.D8.D1:
  row_domain: Mind
  col_domain: Career
  linkage_type: amplifies
  primary_mechanism: "Mercury (mind = intelligence, analytical precision) in 10H career house = the mind-planet IS the career planet; when the native's mind is engaged (Mercury activated), career delivery amplifies; Vargottama Mercury = the mind's career-expression is at D9-level maximum; Mercury as Yogi = the mind IS the fortune-activator; the native's career is fundamentally a mental exercise (AI, technology, data = Mercury-domain professional activities)"
  msr_anchors: [MSR.413, MSR.388, MSR.190]
  strength: 0.94
  direction: row→col
  valence: benefic
  key_finding: "Mind directly amplifies career — Mercury (mind-planet) in 10H means mental engagement IS career engagement; the native's most powerful career asset is his Mercury-quality intelligence; mind and career are the same energy."

CDLM.D8.D2:
  row_domain: Mind
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "Mercury = Yogi Planet (fortune-activator) AND 10H career planet AND mind-planet; when the mind (Mercury) is active, fortune is activated (Yogi function); the native's mental work (AI, data analysis = Mercury activities) produces wealth through the Mercury-Yogi channel; Mercury Vargottama = the mind's wealth-generating capacity is at D9-level maximum; KP cusp 11 sub=Mercury = gains are directly governed by Mercury (mind) = mental excellence = financial gains"
  msr_anchors: [MSR.311, MSR.413, MSR.388]
  strength: 0.92
  direction: row→col
  valence: benefic
  key_finding: "Mind feeds wealth — Mercury (Yogi Planet + 10H + Vargottama) means the native's mental excellence is the primary wealth-generation mechanism; every unit of Mercury-quality mental engagement activates the Yogi fortune channel."

CDLM.D8.D3:
  row_domain: Mind
  col_domain: Relationships
  linkage_type: feeds
  primary_mechanism: "Mercury = DK (spouse-significator) = the mind-planet IS the spouse-significator; the native's mental quality and intelligence are what the Jaimini spouse-karaka represents = the spouse is Mercury-quality (intelligent, communicative); UL = Gemini 3H (Mercury-ruled) = the marriage-quality indicator is in Mercury's sign; when the native's mind (Mercury) is clear and active, relationship quality (DK Mercury) is at its best"
  msr_anchors: [MSR.330, MSR.338, MSR.334]
  strength: 0.85
  direction: row→col
  valence: benefic
  key_finding: "Mind feeds relationships — Mercury as DK (spouse-significator) means mental clarity and intelligence are the primary relationship-quality indicators; the native's intellectual engagement directly affects relationship harmony."

CDLM.D8.D4:
  row_domain: Mind
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "Moon (AK, mind-emotion) = Purva Bhadrapada Pada 3 = Ugra (fierce) = the native's mental-emotional nature is intensely active; over-mental engagement (Mercury-dominant chart = the native's mind rarely rests) can create Vata imbalance (Prana Nadi = air/Vata constitutional tendency); classical: Mercury-type minds = over-thinking, anxiety, nervous system overload = health constraints from mental intensity; Mandi in 4H = the emotional-mental sphere has a background malefic upagraha creating background noise"
  msr_anchors: [MSR.369, MSR.248, MSR.353]
  strength: 0.72
  direction: row→col
  valence: malefic
  key_finding: "Mental intensity constrains health — the native's Mercury-dominant, Purva-Bhadrapada-fierce mind creates Vata constitutional tendency (over-thinking, nervous system stress); mental engagement must be balanced with grounding for health."

CDLM.D8.D5:
  row_domain: Mind
  col_domain: Children
  linkage_type: amplifies
  primary_mechanism: "5H = intelligence, discrimination (buddhi) = the children house IS the intelligence house; Mercury (mind) Jaimini-aspects Sagittarius 9H (not 5H Leo directly — Capricorn Movable → Dual signs, which includes Gemini, Virgo, Sagittarius, Pisces — Leo is Fixed, not Dual) = Mercury's Jaimini aspect does NOT reach 5H Leo; BUT: Sun (5L from Aries Lagna) in 10H = the children-lord is in the career-mind domain; the mind's clarity amplifies the 5H intelligence-discrimination function"
  msr_anchors: [MSR.334, MSR.413]
  strength: 0.75
  direction: row→col
  valence: benefic
  key_finding: "Mind amplifies children/creativity — Mercury's analytical precision and 5H's intelligence (buddhi) are the same energy expressed at different scales; mental clarity amplifies creative and intellectual output."

CDLM.D8.D6:
  row_domain: Mind
  col_domain: Spirit
  linkage_type: feeds
  primary_mechanism: "Moon (AK, soul/spirit) = the mind-planet in Jyotish = mind and spirit use the same instrument (Moon); Purva Bhadrapada's fierce-transformational quality = the mind's intensity is spiritually directed; the native's mental engagement with philosophy, AI ethics, complex systems = Mercury (mind) oriented toward Jupiter-domain (wisdom, meaning) = mind feeds spiritual inquiry; Karakamsa = Gemini (Mercury's sign) = the soul's highest expression domain is Mercury = the mind IS the soul's vehicle"
  msr_anchors: [MSR.348, MSR.406, MSR.374]
  strength: 0.88
  direction: bidirectional
  valence: benefic
  key_finding: "Mind feeds spirit — Moon (mind) = AK (soul) = the native's mind IS his soul's primary vehicle; mental engagement with deep questions naturally becomes spiritual inquiry; Karakamsa in Gemini (Mercury = mind) confirms the soul expresses through mental activity."

CDLM.D8.D7:
  row_domain: Mind
  col_domain: Parents
  linkage_type: feeds
  primary_mechanism: "4H = emotional security and mental foundation = the house of the mind's home; Moon (mind, AK) aspects the 4H via Jaimini Rashi Drishti (Aquarius Fixed → Aries+Cancer+Libra, with Cancer 4H = YES, Moon aspects 4H via Jaimini) = the soul-mind (Moon-AK from 11H) has a Jaimini aspect on the mother's house (4H Cancer); the mind's quality is shaped by the mother's (4H) emotional foundation; the father's domain (9H) = Jupiter = wisdom = the mind's philosophical framework comes from paternal dharmic influence"
  msr_anchors: [MSR.332, MSR.342]
  strength: 0.70
  direction: row→col
  valence: benefic
  key_finding: "Mind feeds the parents domain through Jaimini — Moon (mind/soul) has a Jaimini aspect on Cancer 4H (mother's house); the native's mental and spiritual clarity positively influences the mother-home domain; philosophical mind quality has roots in paternal dharmic wisdom (9H Jupiter)."

CDLM.D8.D8:
  row_domain: Mind
  col_domain: Mind (self-reference)
  linkage_type: amplifies
  primary_mechanism: "Mercury (Vargottama, Yogi, DK, 10H, MD lord, Karakamsa sign lord) = the mind-planet at maximum cross-system designation; Moon (AK, Purva Bhadrapada, Jupiter-ruled) = the emotional-intuitive mind layer; together Mercury + Moon = the two mind-planets; Mercury = analytical precision; Moon-AK = intuitive soul-intelligence; in this chart, both mind-planets are at extraordinary dignity (Mercury = eight-system designee per v8.0, Moon = AK = soul's own planet) = the mind is doubly resourced and internally self-amplifying"
  msr_anchors: [MSR.413, MSR.406, MSR.388]
  strength: 0.95
  direction: bidirectional
  valence: benefic
  key_finding: "The mind domain is the chart's second most self-amplifying domain — Mercury (eight-system per v8.0) and Moon (AK, soul's own) together provide both analytical and intuitive intelligence at extraordinary levels; the native's mental capacity is structurally exceptional."

CDLM.D8.D9:
  row_domain: Mind
  col_domain: Travel
  linkage_type: amplifies
  primary_mechanism: "Mercury (mind, 10H) Jaimini-aspects Sagittarius 9H (long-journeys, foreign travel) from Capricorn (Movable → Dual includes Sagittarius) = YES, Mercury has a Jaimini aspect on the 9H travel domain; the mind's clarity and analytical quality amplify the native's ability to navigate and thrive in foreign environments; Singapore as a knowledge-economy hub = Mercury-mind thrives in a Mercury-quality environment (cosmopolitan, multilingual, tech-forward = Mercury's optimal environment)"
  msr_anchors: [MSR.334, MSR.381]
  strength: 0.78
  direction: row→col
  valence: benefic
  key_finding: "Mind amplifies travel outcomes — Mercury's Jaimini aspect on the 9H travel domain + the native's Mercury-quality skills are optimally suited for Singapore's knowledge-economy environment; mental excellence amplifies the value of foreign living."

---

### ROW D9: TRAVEL → [All Domains]

CDLM.D9.D1:
  row_domain: Travel
  col_domain: Career
  linkage_type: feeds
  primary_mechanism: "Saham Paradesa (foreign travel) in 1H near Lagna = the native's identity IS a traveler-abroad; 12H Yogi Point = fortune activates in foreign domain = the career (10H) is built in the foreign domain = travel feeds career directly; EVT.2007 (Singapore move) = the career-defining move = the single biggest career-enabling event was a geographic travel event; Rahu (2H, career-ambition-driver) + foreign career = Rahu's ambition is realized through foreign travel"
  msr_anchors: [MSR.399, MSR.392, MSR.381]
  strength: 0.90
  direction: row→col
  valence: benefic
  key_finding: "Travel directly feeds career — the Singapore move (EVT.2007) was the native's most career-defining event; the Saham Paradesa in 1H and Yogi Point in 12H confirm that foreign residence is the mechanism through which career excellence is achieved."

CDLM.D9.D2:
  row_domain: Travel
  col_domain: Wealth
  linkage_type: feeds
  primary_mechanism: "12H (foreign/isolation) = Yogi Point + Pranapada = the fortune-activation and life-breath points are in the foreign domain = living abroad activates the Yogi (fortune); the native's Singapore career (foreign = 12H) = the wealth-generating context; Venus (2L, wealth lord) in 9H (foreign/long-journeys) = the wealth lord is in the foreign-travel domain = wealth and travel are the same Venus-domain expression; Rahu (2H, wealth accumulator) Argala on Lagna from 2H = the wealth accumulation is Rahu-foreign (Rahu = foreign element)"
  msr_anchors: [MSR.392, MSR.403, MSR.401]
  strength: 0.89
  direction: row→col
  valence: benefic
  key_finding: "Travel feeds wealth — the Yogi Point in 12H means fortune itself resides in the foreign domain; living abroad (Singapore) is the most powerful wealth-activation mechanism available to this native."

CDLM.D9.D3:
  row_domain: Travel
  col_domain: Relationships
  linkage_type: constrains
  primary_mechanism: "Foreign residence (12H) = permanent physical distance from native's home-country relationships (parents, siblings, extended family); UL in Gemini 3H = the marriage-quality indicator is in the 3H (short journeys, local communication) = the ideal marital context is closer-in, not maximally foreign; the native's foreign career (Singapore = far from both UL's 3H energy and the natal family's 4H/9H base) creates ongoing relationship-maintenance demands"
  msr_anchors: [MSR.338, MSR.381, MSR.399]
  strength: 0.70
  direction: row→col
  valence: mixed
  key_finding: "Foreign travel constrains relationship maintenance — the 12H foreign residence vs UL's 3H (local communication quality) creates a structural relationship-at-a-distance challenge; travel excellence comes at a relationship-proximity cost."

CDLM.D9.D4:
  row_domain: Travel
  col_domain: Health
  linkage_type: constrains
  primary_mechanism: "12H (foreign isolation) = a health challenge domain in classical Jyotish (12H = hospitalization in some readings); the 6H-12H health-isolation axis = when 12H is very active (ongoing foreign residence), the health domain (6H) is co-activated; the foreign environment adds health complexity (different climate, food patterns, support systems)"
  msr_anchors: [MSR.392, MSR.377]
  strength: 0.62
  direction: row→col
  valence: malefic
  key_finding: "Foreign travel weakly constrains health — the 12H (foreign/isolation) domain's structural connection to 6H (health) means extended foreign residence requires active health management; climate, diet, and social support differences add health complexity."

CDLM.D9.D5:
  row_domain: Travel
  col_domain: Children
  linkage_type: constrains
  primary_mechanism: "Foreign residence (12H) vs children (5H): the geographic distance from family support systems makes child-rearing more demanding; 5L Sun in 10H (career house) + the native's career being in a foreign land = the career's foreign-location requirement competes with the child-rearing support that proximity to family (4H/9H = parental domain) would provide; the 5H-12H relationship = 5H is 6th from 12H = children and foreign-residence are in a service/challenge relationship"
  msr_anchors: [MSR.381, MSR.399]
  strength: 0.65
  direction: row→col
  valence: malefic
  key_finding: "Foreign travel constrains children — extended foreign residence means child-rearing happens without the parental support systems that would be available in the native's home country; a structural tradeoff between 12H foreign-career and 5H children-support."

CDLM.D9.D6:
  row_domain: Travel
  col_domain: Spirit
  linkage_type: feeds
  primary_mechanism: "12H (foreign/isolation) = the moksha-liberation domain in classical Jyotish; Yogi Point and Pranapada in 12H = the fortune-breath-spirit points are in the foreign domain; living abroad (Singapore) = living in the moksha domain = the native's geographic choice IS a spiritual location; 9H (long journeys, pilgrimage) = Jupiter+Venus = dharmic travel IS spiritual practice for this native; pilgrimage is encoded in the 9H spirit domain"
  msr_anchors: [MSR.392, MSR.407, MSR.374]
  strength: 0.86
  direction: row→col
  valence: benefic
  key_finding: "Travel feeds spirit — living in the 12H foreign-moksha domain means the native's geographic choice is spiritually activating; the Yogi Point in 12H makes foreign residence a continuous fortune-spiritual activation."

CDLM.D9.D7:
  row_domain: Travel
  col_domain: Parents
  linkage_type: constrains
  primary_mechanism: "The native's foreign residence (Singapore, 12H) = permanent distance from parents (India, 4H home-country/9H parental domain); this is the chart's most structurally clear parent-travel tension; Saham Paradesa (foreign-travel) in 1H = the foreign-destiny is natal and permanent = the distance from parents is not a temporary phase but a structural life-condition; classical: 12H vs 4H (home/mother) = the foreign domain and the home domain are in opposition (12H is 9th from 4H = dharmic distance)"
  msr_anchors: [MSR.399, MSR.342]
  strength: 0.78
  direction: row→col
  valence: malefic
  key_finding: "Foreign travel structurally constrains parental proximity — Saham Paradesa in 1H confirms the native's foreign destiny is permanent; the 12H foreign residence and 4H/9H parental domains are in structural opposition."

CDLM.D9.D8:
  row_domain: Travel
  col_domain: Mind
  linkage_type: amplifies
  primary_mechanism: "Singapore as a cosmopolitan, multilingual, high-intellectual-density city = Mercury-optimal environment = the native's Mercury-mind (10H, Vargottama, Yogi) thrives in Singapore's environment; cross-cultural exposure (12H foreign) amplifies Mercury's ability to synthesize diverse inputs; the Gemini-quality (dual, synthesizing, multiple-perspective) of the native's UL (Gemini 3H) = travel amplifies the native's mental synthesis capacity; foreign living = continuous novelty input = Mercury-mind is continuously stimulated"
  msr_anchors: [MSR.338, MSR.381, MSR.413]
  strength: 0.82
  direction: row→col
  valence: benefic
  key_finding: "Travel amplifies mind — Singapore's Mercury-optimal intellectual environment amplifies the native's Vargottama Mercury; cross-cultural exposure continuously feeds Mercury's synthesis-hunger."

CDLM.D9.D9:
  row_domain: Travel
  col_domain: Travel (self-reference)
  linkage_type: amplifies
  primary_mechanism: "The travel domain is comprehensively confirmed: Saham Paradesa (1H, near Lagna) = identity encoded with foreign-travel; Yogi Point (12H) = fortune in foreign domain; Pranapada (12H) = life-breath in foreign domain; 9H (long journeys) = Jupiter+Venus = dharmic wealth through travel; Venus (2L+7L) in 9H = wealth AND marriage both in the long-journey/foreign domain; EVT.2007 (Singapore move) = career-defining foreign move; KP cusp 12 sub=Saturn = the foreign domain is KP-governed by the exalted AmK = career-force governs foreign domain; the travel domain is self-amplifying because every living from Singapore confirms and amplifies the natal Paradesa-Yogi-Pranapada cluster"
  msr_anchors: [MSR.392, MSR.399, MSR.381]
  strength: 0.91
  direction: bidirectional
  valence: benefic
  key_finding: "The travel domain is self-amplifying — six distinct travel-foreign mechanisms (Saham Paradesa, Yogi Point, Pranapada, 9H Jupiter+Venus, KP cusp 12, EVT.2007) all reinforce that foreign residence is this native's destiny, fortune-activation zone, and spiritual practice ground simultaneously."

---

## CDLM SUMMARY TABLE

| From\To | Career | Wealth | Relationships | Health | Children | Spirit | Parents | Mind | Travel |
|---|---|---|---|---|---|---|---|---|---|
| **Career** | 1.00✓ | 0.92→ | 0.91↔ | 0.78→ | 0.72→ | 0.89↔ | 0.76↔ | 0.91→ | 0.90→ |
| **Wealth** | 0.88→ | 0.91✓ | 0.89↔ | 0.68→ | 0.72→ | 0.87↔ | 0.70↔ | 0.86→ | 0.88→ |
| **Relationships** | 0.91↔ | 0.87→ | 0.93✓ | 0.68→ | 0.78→ | 0.86↔ | 0.62→ | 0.82↔ | 0.68→ |
| **Health** | 0.76→ | 0.68→ | 0.61→ | 0.80✓ | 0.62→ | 0.82→ | 0.65↔ | 0.78→ | 0.60→ |
| **Children** | 0.70→ | 0.74→ | 0.76→ | 0.58→ | 0.75✓ | 0.78↔ | 0.72→ | 0.78→ | 0.60→ |
| **Spirit** | 0.89↔ | 0.84→ | 0.86↔ | 0.80→ | 0.78→ | 0.94✓ | 0.82↔ | 0.88↔ | 0.85↔ |
| **Parents** | 0.80→ | 0.76→ | 0.62→ | 0.65↔ | 0.73→ | 0.83↔ | 0.82✓ | 0.70→ | 0.78→ |
| **Mind** | 0.94→ | 0.92→ | 0.85→ | 0.72→ | 0.75→ | 0.88↔ | 0.70→ | 0.95✓ | 0.78→ |
| **Travel** | 0.90→ | 0.89→ | 0.70→ | 0.62→ | 0.65→ | 0.86→ | 0.78→ | 0.82→ | 0.91✓ |

**Legend**: → = row feeds col (directional) | ↔ = bidirectional | ✓ = self-reference

**v1.1 changes from v1.0**: D3.D3: 0.95→0.93; D3.D4: 0.76→0.68; D4.D3: 0.78↔→0.61→; D6.D2: 0.88→0.84→; D6.D6: 0.96→0.94

### Highest-Strength Cross-Domain Links (≥0.88)

1. **Mind → Career (0.94)**: Mercury in 10H = mind IS career
2. **Mind → Mind (0.95)**: Mercury eight-system (v8.0) + Moon-AK double-mind resource
3. **Spirit → Spirit (0.94)**: Six confirmed spiritual mechanisms self-amplifying
4. **Relationships → Relationships (0.93)**: 7H five-layer convergence
5. **Career → Career (1.00)**: Chart's primary domain = self-organizing apex
6. **Mind → Wealth (0.92)**: Mercury Yogi = mental excellence = financial gains
7. **Career → Wealth (0.92)**: AL in 10H = career reputation drives wealth
8. **Wealth → Relationships (0.89)**: Venus as 2L+7L = same energy; Shree Lagna in 7H adds Lakshmi-grace
9. **Career → Spirit (0.89)**: Palana Devata = Mercury = career IS dharmic practice
10. **Travel → Career (0.90)**: Singapore move = career-defining travel

### Lowest-Strength Cross-Domain Links (≤0.62)

1. **Children → Health (0.58)**: Weak secondary link through adjacent houses
2. **Children → Travel (0.60)**: Structural competition for 9H energy
3. **Health → Travel (0.60)**: Mild 6H-12H axis constraint
4. **Health → Relationships (0.61)**: Indirect via Saturn Sade Sati + Venus dual-role
5. **Relationships → Parents (0.62)**: Mild parental-proximity constraint

### Structural Reading: The Chart's Primary Flow

**Primary current**: Career ← → Mind ← → Wealth (0.94, 0.92, 0.92) = the career-mind-wealth triangle is the chart's primary energy loop; all three domains feed each other with ≥0.92 strength

**Secondary current**: Spirit ← → Career ← → Travel → Wealth = the spiritual-career-travel-wealth chain explains the native's entire adult life architecture (dharmic career in a foreign land producing wealth)

**Karmic vortex**: Relationships (0.93 self-amplifying, five-layer) = the 7H five-layer convergence means relationship-karma is the chart's deepest karmic processing zone; Shree Lagna in 7H adds a wealth-through-relationship channel to the karmic vortex

**Generational axis**: Parents → Spirit → Children = the dharmic generational chain; parental wisdom (9H) feeds spiritual practice (9H same house) which seeds children's purva punya (5H)

**v1.1 structural revision**: Health→Relationships link reduced from 0.78 mirror to 0.61 constrains (unidirectional); the 7H karmic vortex is now primarily Saturn+Mars+Bhrigu Bindu+Shree Lagna+KP rather than the previously assumed Hora Lagna+Roga/Mahatmya configuration; Shree Lagna's move from 9H to 7H strengthens D2↔D3 (wealth-relationship fusion) while reducing D6.D2 (spirit→wealth directness)

---

## CDLM ARTIFACT FOOTER

```yaml
artifact: CDLM_v1_1.md
version: 1.2
status: CURRENT
date_closed: 2026-04-18
session: FIX_SESSION_003_deferred
cells_completed: 81 of 81
cells_corrected: 9
domains: 9
linkage_types_used: [feeds, constrains, mirrors, amplifies, compensates, contradicts]
highest_strength_cell: CDLM.D1.D1 (Career self-reference, 1.00)
lowest_strength_cell: CDLM.D5.D4 (Children → Health, 0.58)
primary_flow_identified: Career ↔ Mind ↔ Wealth triangle (≥0.92)
karmic_vortex: Relationships (D3.D3 = 0.93 self-amplifying, five-layer corrected)
supersedes: CDLM_v1_0.md
parent_facts: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
changelog:
  - "D1.D4: removed Roga Saham 7H mechanism; rebuilt via Mercury 6L-10L dual-role"
  - "D2.D2: Shree Lagna corrected 9H→7H Libra; mechanism updated"
  - "D2.D3: Shree Lagna corrected 9H→7H; strength maintained 0.89 (link actually strengthened)"
  - "D3.D3: six-layer→five-layer; Hora Lagna removed (→3H); Roga/Mahatmya removed (→2H/9H); Shree Lagna 7H added; strength 0.95→0.93"
  - "D3.D4: Roga in 7H mechanism removed; rebuilt via Mars-Saturn Vata-Pitta; strength 0.76→0.68"
  - "D4.D3: PRIMARY FIX — type mirrors→constrains; direction bidirectional→row→col; strength 0.78→0.61; mechanism rebuilt sans Roga-in-7H"
  - "D6.D1: Shree Lagna corrected 9H→7H; mechanism updated; strength maintained 0.89"
  - "D6.D2: Shree Lagna corrected 9H→7H; strength 0.88→0.84 (path more indirect)"
  - "D6.D6: seven→six mechanisms; Ghati (→9H) and Varnada (→4H) removed from 8H count; Shree Lagna 7H added; strength 0.96→0.94"
next_artifact: RM_v2_0.md (Resonance Map v2.0 with same v8.0 corrections)
feeds_into: [RM_v2_0.md, UCN_v1_0.md, Domain Reports L3]
author: Claude Sonnet 4.6 (MARSYS-JIS FIX_SESSION_003_deferred)
native: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
```
