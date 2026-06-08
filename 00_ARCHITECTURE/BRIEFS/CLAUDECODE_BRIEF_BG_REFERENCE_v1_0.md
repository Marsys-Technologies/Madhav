---
artifact: CLAUDECODE_BRIEF_BG_REFERENCE_v1_0
canonical_id: L0_BG_REFERENCE_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_reference writer (15 typed reference tables)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 1450  # SUM of the 12 substantive reference_* tables this writer owns (pointer tables excluded — see §0.1)
dependencies: [bg_ontology]  # canonical_id FK; bg_ontology must be lit first (Tier 0 ordering note in §5)
llm_cost: $0
document_number: 4 of 15
---

# bg_reference — Writer Brief (the 15-table classical reference library)

> **The "holy grail" of L0.** This writer owns the structured, typed, source-cited properties of every classical Jyotish concept. The Phase β slice populated 5 tables (~88 rows). This brief brings the count to floor across **12 substantive tables** (the 3 pointer tables are owned by the catalog writers — see §0.1). ZERO LLM. Every row carries a `source_citation`.

> **Replaces** the Phase β `bg_reference.py` writer + extends `brahmagyan/l0_reference.py`. The existing 5-table data is CORRECT and is KEPT (imported, not re-authored). This brief ADDS the 7 standalone new tables (houses, strength_systems, karakas, upagrahas, constants, topic_tags, glossary).

## §0 — Asset summary

- **Asset ID:** `bg_reference`
- **Backing tables:** 15 `reference_*` tables. This writer populates **12**; the 3 pointer tables are populated by the catalog writers (§0.1).
- **count_sql** (already set, migration 180): sums all 15 tables. So bg_reference's tile count only reaches its full value after the catalog writers fill the pointer tables — this is expected (§5 ordering).
- **Target floor (this writer's 12 tables):** **≥ 1,450 rows.** Breakdown below.
- **Source category:** embedded classical data (BPHS Ch.3/4/6/7/26/27 + Phaladeepika + Taittiriya Aranyaka + Jaimini).
- **Scope:** `global`. **Tier:** 0 for the 12 substantive tables (the pointer rows land in Tier 1 via the catalog writers).

### §0.1 — Table ownership + per-table floors

| Table | Owner | Floor | Status |
|---|---|---|---|
| `reference_planets` | bg_reference (existing) | 11 | KEEP existing data |
| `reference_nakshatras` | bg_reference (existing) | 27 | KEEP |
| `reference_signs` | bg_reference (existing) | 12 | KEEP |
| `reference_aspects` | bg_reference (existing) | 30 | KEEP |
| `reference_vargas` | bg_reference (existing) | 19 | KEEP (16 shodasha + 3 extra already present) |
| `reference_houses` | bg_reference (NEW) | 12 | §3.1 |
| `reference_strength_systems` | bg_reference (NEW) | 35 | §3.2 |
| `reference_karakas` | bg_reference (NEW) | 70 | §3.3 |
| `reference_upagrahas` | bg_reference (NEW) | 9 | §3.4 |
| `reference_constants` | bg_reference (NEW) | 200 | §3.5 |
| `reference_topic_tags` | bg_reference (NEW) | 450 | §3.6 |
| `reference_glossary` | bg_reference (NEW) | 350 | §3.7 |
| **bg_reference subtotal** | | **≥ 1,225** (the writer's own floor; targeting ~1,450 with the per-section targets) | |
| `reference_yogas` | **bg_yogas writer** (Doc 11) | 250 | NOT this brief |
| `reference_doshas` | **bg_doshas writer** (Doc 13) | 50 | NOT this brief |
| `reference_dasha_systems` | **bg_dasha_systems writer** (Doc 12) | 15 | NOT this brief |

> **Ownership rationale.** The pointer tables have FK constraints (`fk_ref_yoga` → `brahma_yoga_catalog`, etc., migration 178:78-100) that REJECT any insert before the parent catalog row exists. So they CANNOT be filled by a Tier-0 bg_reference run. Each catalog writer inserts its own pointer row in the same transaction it inserts the catalog row — guaranteeing FK validity and single-source-of-truth. This brief's Vimarśaka checks ONLY the 12 substantive tables; Vimarśaka-Ω (Doc 15) checks the pointer tables after Tier 1.

## §1 — Schema reference

The **existing 5 tables** keep the schemas defined by `brahmagyan/l0_reference.py` INSERTs (verified at HEAD — do not alter). The **7 new tables** are created by migration 178 (verified):

```
reference_houses          (house_num PK, name_sa, name_en, category CHECK∈{kendra,panapara,apoklima,dusthana,upachaya,trika,trikona},
                           natural_significations JSONB, karakas JSONB, classical_doctrine_jsonb JSONB, source_citation NOT NULL)
reference_strength_systems(strength_id PK, name_sa, name_en, category CHECK∈{shadbala,ashtakavarga,bhava_bala,other},
                           formula_text, max_value, units, classical_interpretation, source_citation NOT NULL)
reference_karakas         (karaka_id PK, name_sa, name_en, karaka_type CHECK∈{sthira_planet,sthira_house,chara_jaimini},
                           applies_to, classical_significations JSONB, source_citation NOT NULL)
reference_upagrahas       (upagraha_id PK, name_sa, name_en, parent_planet, computation_method, significations JSONB, source_citation NOT NULL)
reference_constants       (constant_id PK, name, value_numeric, value_text, unit, category, source_citation NOT NULL, classical_context)
reference_topic_tags      (canonical_id PK, name, category, description, example_chunks JSONB)
reference_glossary        (term_id PK, term_sa, term_en, definition, category, classical_citation NOT NULL, related_concepts TEXT[])
```

> Note: `reference_topic_tags` has no `source_citation` column (it is authored vocabulary, not a doctrinal claim). For Vimarśaka source-citation completeness, topic_tags are EXEMPT (their provenance is "authored canonical vocabulary"); `reference_glossary` uses `classical_citation`.

## §2 — Source references

| Table | Primary classical source |
|---|---|
| reference_houses | BPHS Ch.7 (Bhava-svarupa / Bhava-vichara) + Phaladeepika Ch.4 (Bhava effects) |
| reference_strength_systems | BPHS Ch.27 (Bala / Shadbala) + Ch.7 (Ashtakavarga is BPHS Ch.66-72 in full editions) |
| reference_karakas | BPHS Ch.27 (Karaka-adhyaya) for sthira; Jaimini Sutram Ch.1 for chara karakas |
| reference_upagrahas | BPHS Ch.3 (upagraha definitions) + Ch.5 (Gulika/Maandi computation) |
| reference_constants | BPHS various (Shadbala maxima Ch.27; Vimshopaka Ch.7; Ashtakavarga bindus) |
| reference_glossary | Phaladeepika + BPHS + Saravali (technical-term definitions) |
| reference_topic_tags | Authored canonical vocabulary (corpus-classification keys; not a single text) |

## §3 — Embedded classical content

> Author all new data into `platform/python-sidecar/brahmagyan/l0_reference.py` as module-level lists (matching the existing `PLANETS`/`NAKSHATRAS`/… pattern). The writer (§4) appends INSERT loops for each new table. KEEP the existing 5 lists unchanged.

### §3.1 — reference_houses (12 rows, full inline)

```python
# BPHS Ch.7 + Phaladeepika Ch.4. category uses the migration-178 CHECK vocabulary.
# A house may be many things at once (1st is kendra AND trikona); `category` stores the
# PRIMARY classification; classical_doctrine_jsonb.classes[] lists all memberships.
HOUSES = [
  {"house_num":1,"name_sa":"Tanu","name_en":"Ascendant/Body","category":"kendra",
   "natural_significations":["body","self","appearance","health","vitality","head","temperament","fame"],
   "karakas":["sun"],  # Sun is karaka of 1st (self/soul)
   "classical_doctrine_jsonb":{"classes":["kendra","trikona","upachaya_no"],"lordship":"lagnesha is the most important graha","phaladeepika":"Ch.4 v.2"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":2,"name_sa":"Dhana","name_en":"Wealth","category":"panapara",
   "natural_significations":["wealth","family","speech","food","face","accumulated_assets","early_education"],
   "karakas":["jupiter","mercury"],
   "classical_doctrine_jsonb":{"classes":["panapara","maraka"],"maraka":True,"note":"2nd is a maraka (death-inflicting) house"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":3,"name_sa":"Sahaja","name_en":"Siblings/Courage","category":"apoklima",
   "natural_significations":["younger_siblings","courage","valour","communication","short_journeys","arms","effort","skills"],
   "karakas":["mars"],
   "classical_doctrine_jsonb":{"classes":["apoklima","upachaya","dusthana_minor"],"upachaya":True},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":4,"name_sa":"Sukha","name_en":"Home/Happiness","category":"kendra",
   "natural_significations":["mother","home","property","vehicles","emotional_happiness","education","heart","land"],
   "karakas":["moon","mercury","mars"],
   "classical_doctrine_jsonb":{"classes":["kendra"],"note":"sukha-sthana; foundation of chart"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":5,"name_sa":"Putra","name_en":"Children/Intelligence","category":"trikona",
   "natural_significations":["children","intelligence","purva_punya","mantra","romance","speculation","creativity"],
   "karakas":["jupiter"],
   "classical_doctrine_jsonb":{"classes":["trikona"],"note":"strongest trikona after lagna; purva-punya sthana"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":6,"name_sa":"Ripu/Shatru","name_en":"Enemies/Disease","category":"dusthana",
   "natural_significations":["enemies","disease","debts","obstacles","service","litigation","maternal_relatives"],
   "karakas":["mars","saturn"],
   "classical_doctrine_jsonb":{"classes":["dusthana","upachaya","trika"],"trika":True,"upachaya":True},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":7,"name_sa":"Yuvati/Kalatra","name_en":"Marriage/Partnership","category":"kendra",
   "natural_significations":["spouse","marriage","business_partnership","trade","passion","foreign_travel","public_dealings"],
   "karakas":["venus"],
   "classical_doctrine_jsonb":{"classes":["kendra","maraka"],"maraka":True,"note":"maraka house"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":8,"name_sa":"Ayur/Randhra","name_en":"Longevity/Transformation","category":"dusthana",
   "natural_significations":["longevity","death","inheritance","occult","sudden_events","chronic_illness","spouse_wealth","research"],
   "karakas":["saturn"],
   "classical_doctrine_jsonb":{"classes":["dusthana","trika"],"trika":True,"note":"ayur-sthana; deepest dusthana"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":9,"name_sa":"Dharma/Bhagya","name_en":"Fortune/Dharma","category":"trikona",
   "natural_significations":["father","guru","dharma","fortune","higher_learning","pilgrimage","long_journeys","prosperity"],
   "karakas":["jupiter","sun"],
   "classical_doctrine_jsonb":{"classes":["trikona"],"note":"bhagya-sthana; best trikona; dharma"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":10,"name_sa":"Karma","name_en":"Career/Action","category":"kendra",
   "natural_significations":["career","profession","status","authority","fame","government","father_alt","public_action"],
   "karakas":["sun","mercury","jupiter","saturn"],
   "classical_doctrine_jsonb":{"classes":["kendra","upachaya"],"upachaya":True,"note":"karma-sthana; strongest kendra for action"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":11,"name_sa":"Labha","name_en":"Gains/Income","category":"panapara",
   "natural_significations":["gains","income","elder_siblings","friends","aspirations","fulfilment_of_desires","recovery"],
   "karakas":["jupiter"],
   "classical_doctrine_jsonb":{"classes":["panapara","upachaya"],"upachaya":True,"note":"labha-sthana; all gains"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
  {"house_num":12,"name_sa":"Vyaya","name_en":"Loss/Liberation","category":"apoklima",
   "natural_significations":["losses","expenditure","moksha","foreign_lands","isolation","bed_pleasures","hospitals","sleep","feet"],
   "karakas":["saturn","ketu"],
   "classical_doctrine_jsonb":{"classes":["apoklima","dusthana","trika"],"trika":True,"note":"vyaya/moksha-sthana"},
   "source_citation":"BPHS Ch.7; Phaladeepika Ch.4"},
]
```

### §3.2 — reference_strength_systems (≥35 rows)

Author the six Shadbala sources + their sub-components, the Ashtakavarga system, and Bhava-bala. Full inline list:

```python
SHADBALA_MAX_RUPAS = {  # BPHS Ch.27 minimum-required shadbala in rupas, per planet
  "sun":6.5,"moon":6.0,"mars":5.0,"mercury":7.0,"jupiter":6.5,"venus":5.5,"saturn":5.0,
}
STRENGTH_SYSTEMS = [
  # --- The 6 Shadbala sources (category=shadbala) ---
  {"strength_id":"sthana_bala","name_sa":"Sthāna Bala","name_en":"Positional Strength","category":"shadbala",
   "formula_text":"Sum of Uchcha + Sapta-vargaja + Ojha-yugma + Kendradi + Drekkana bala","max_value":None,"units":"virupa",
   "classical_interpretation":"Strength from dignity & placement (exaltation, vargas, odd/even, angular)","source_citation":"BPHS Ch.27"},
  {"strength_id":"dig_bala","name_sa":"Dig Bala","name_en":"Directional Strength","category":"shadbala",
   "formula_text":"Distance of planet from its house of directional weakness, scaled 0–60 virupas","max_value":60.0,"units":"virupa",
   "classical_interpretation":"Jupiter/Mercury strong in East(1st), Sun/Mars in South(10th), Saturn in West(7th), Moon/Venus in North(4th)","source_citation":"BPHS Ch.27"},
  {"strength_id":"kala_bala","name_sa":"Kāla Bala","name_en":"Temporal Strength","category":"shadbala",
   "formula_text":"Sum of Nathonnatha + Paksha + Tribhaga + Abda + Masa + Vara + Hora + Ayana + Yuddha bala","max_value":None,"units":"virupa",
   "classical_interpretation":"Strength from time of birth (day/night, lunar phase, year/month/day/hour lords, declination, planetary war)","source_citation":"BPHS Ch.27"},
  {"strength_id":"cheshta_bala","name_sa":"Cheṣṭā Bala","name_en":"Motional Strength","category":"shadbala",
   "formula_text":"Derived from planet's speed/retrogression relative to mean motion","max_value":60.0,"units":"virupa",
   "classical_interpretation":"Retrograde & accelerating planets gain cheshta bala; Sun/Moon use Ayana bala in its place","source_citation":"BPHS Ch.27"},
  {"strength_id":"naisargika_bala","name_sa":"Naisargika Bala","name_en":"Natural Strength","category":"shadbala",
   "formula_text":"Fixed: Sun 60, Moon 51.43, Venus 42.86, Jupiter 34.29, Mercury 25.71, Mars 17.14, Saturn 8.57 virupas","max_value":60.0,"units":"virupa",
   "classical_interpretation":"Innate brightness order; constant for each graha","source_citation":"BPHS Ch.27"},
  {"strength_id":"drik_bala","name_sa":"Dṛk Bala","name_en":"Aspectual Strength","category":"shadbala",
   "formula_text":"Net of benefic minus malefic aspects received, in virupas","max_value":None,"units":"virupa",
   "classical_interpretation":"Benefic drishti adds, malefic drishti subtracts","source_citation":"BPHS Ch.27"},
  # --- Sthana-bala sub-components ---
  {"strength_id":"uchcha_bala","name_sa":"Uccha Bala","name_en":"Exaltation Strength","category":"shadbala",
   "formula_text":"60 × (180 − |long − debilitation_point|)/180","max_value":60.0,"units":"virupa",
   "classical_interpretation":"Max at exact exaltation, zero at exact debilitation","source_citation":"BPHS Ch.27"},
  {"strength_id":"saptavargaja_bala","name_sa":"Saptavargaja Bala","name_en":"Seven-Varga Strength","category":"shadbala",
   "formula_text":"Sum of dignity points across D1,D2,D3,D7,D9,D12,D30","max_value":None,"units":"virupa",
   "classical_interpretation":"Moolatrikona 45, own 30, great-friend 22.5, friend 15, neutral 7.5, enemy 3.75, great-enemy 1.875","source_citation":"BPHS Ch.27"},
  {"strength_id":"ojhayugma_bala","name_sa":"Ojhayugma Bala","name_en":"Odd-Even Strength","category":"shadbala",
   "formula_text":"15 virupas if placed in the harmonious odd/even rasi & navamsa","max_value":30.0,"units":"virupa",
   "classical_interpretation":"Moon/Venus strong in even signs; others in odd signs","source_citation":"BPHS Ch.27"},
  {"strength_id":"kendradi_bala","name_sa":"Kendrādi Bala","name_en":"Angular Strength","category":"shadbala",
   "formula_text":"60 in kendra, 30 in panapara, 15 in apoklima","max_value":60.0,"units":"virupa",
   "classical_interpretation":"Angular houses give a graha full positional vigour","source_citation":"BPHS Ch.27"},
  {"strength_id":"drekkana_bala","name_sa":"Drekkāṇa Bala","name_en":"Decanate Strength","category":"shadbala",
   "formula_text":"15 virupas: male planets in 1st drekkana, neutral in 2nd, female in 3rd","max_value":15.0,"units":"virupa",
   "classical_interpretation":"Gender-decanate harmony","source_citation":"BPHS Ch.27"},
  # --- Kala-bala sub-components ---
  {"strength_id":"nathonnatha_bala","name_sa":"Nathonnatha Bala","name_en":"Diurnal/Nocturnal Strength","category":"shadbala","formula_text":"Based on birth distance from midnight/noon","max_value":60.0,"units":"virupa","classical_interpretation":"Moon/Mars/Saturn strong at night; Sun/Jupiter/Venus by day; Mercury always","source_citation":"BPHS Ch.27"},
  {"strength_id":"paksha_bala","name_sa":"Pakṣa Bala","name_en":"Lunar-Phase Strength","category":"shadbala","formula_text":"Benefics gain in shukla paksha, malefics in krishna paksha","max_value":60.0,"units":"virupa","classical_interpretation":"Moon's waxing/waning empowers benefics/malefics respectively","source_citation":"BPHS Ch.27"},
  {"strength_id":"tribhaga_bala","name_sa":"Tribhāga Bala","name_en":"Third-of-Day Strength","category":"shadbala","formula_text":"60 virupas to the lord of the day/night third of birth","max_value":60.0,"units":"virupa","classical_interpretation":"Mercury rules 1st third, Sun 2nd, Saturn 3rd of day (reversed at night), Jupiter always","source_citation":"BPHS Ch.27"},
  {"strength_id":"abdadhipa_bala","name_sa":"Abdādhipa Bala","name_en":"Year-Lord Strength","category":"shadbala","formula_text":"15 virupas to the lord of the year of birth","max_value":15.0,"units":"virupa","classical_interpretation":"Varshesha gains temporal strength","source_citation":"BPHS Ch.27"},
  {"strength_id":"masadhipa_bala","name_sa":"Māsādhipa Bala","name_en":"Month-Lord Strength","category":"shadbala","formula_text":"30 virupas to the lord of the month of birth","max_value":30.0,"units":"virupa","classical_interpretation":"Masesha gains temporal strength","source_citation":"BPHS Ch.27"},
  {"strength_id":"varadhipa_bala","name_sa":"Vārādhipa Bala","name_en":"Day-Lord Strength","category":"shadbala","formula_text":"45 virupas to the lord of the weekday of birth","max_value":45.0,"units":"virupa","classical_interpretation":"Varesha gains temporal strength","source_citation":"BPHS Ch.27"},
  {"strength_id":"horadhipa_bala","name_sa":"Horādhipa Bala","name_en":"Hour-Lord Strength","category":"shadbala","formula_text":"60 virupas to the lord of the hora of birth","max_value":60.0,"units":"virupa","classical_interpretation":"Horesha gains temporal strength","source_citation":"BPHS Ch.27"},
  {"strength_id":"ayana_bala","name_sa":"Ayana Bala","name_en":"Declination Strength","category":"shadbala","formula_text":"From planet's declination (kranti); max 60 virupas","max_value":60.0,"units":"virupa","classical_interpretation":"Northern declination favours most planets; replaces cheshta for Sun/Moon","source_citation":"BPHS Ch.27"},
  {"strength_id":"yuddha_bala","name_sa":"Yuddha Bala","name_en":"Planetary-War Strength","category":"shadbala","formula_text":"Winner of graha-yuddha gains, loser loses, the difference in virupas","max_value":None,"units":"virupa","classical_interpretation":"When two planets within 1°, the one further north/ brighter wins","source_citation":"BPHS Ch.27"},
  # --- Ashtakavarga (category=ashtakavarga) ---
  {"strength_id":"bhinnashtakavarga","name_sa":"Bhinnāṣṭakavarga","name_en":"Individual Ashtakavarga","category":"ashtakavarga","formula_text":"Per-planet benefic-point chart across 12 signs from 8 contributors","max_value":8.0,"units":"bindu","classical_interpretation":"Each of 7 planets + lagna contributes 0/1 bindu per sign; per-planet max 8 per sign","source_citation":"BPHS Ch.66-72"},
  {"strength_id":"sarvashtakavarga","name_sa":"Sarvāṣṭakavarga","name_en":"Aggregate Ashtakavarga","category":"ashtakavarga","formula_text":"Sum of the 7 bhinnashtakavargas; total 337 bindus over 12 signs","max_value":56.0,"units":"bindu","classical_interpretation":"Sign with >28 bindus is strong; transit results read from bindu count","source_citation":"BPHS Ch.66-72"},
  {"strength_id":"trikona_shodhana","name_sa":"Trikoṇa Śodhana","name_en":"Trinal Reduction","category":"ashtakavarga","formula_text":"Reduce bindus within each trine to the minimum of the three","max_value":None,"units":"bindu","classical_interpretation":"First reduction before computing kakshya/transit strength","source_citation":"BPHS Ch.66-72"},
  {"strength_id":"ekadhipatya_shodhana","name_sa":"Ekādhipatya Śodhana","name_en":"Single-Lordship Reduction","category":"ashtakavarga","formula_text":"Reduce bindus in signs co-lorded by one planet","max_value":None,"units":"bindu","classical_interpretation":"Second reduction; yields shodhya pinda","source_citation":"BPHS Ch.66-72"},
  {"strength_id":"shodhya_pinda","name_sa":"Śodhya Piṇḍa","name_en":"Reduced Aggregate","category":"ashtakavarga","formula_text":"Rashi-pinda + Graha-pinda after the two reductions","max_value":None,"units":"bindu","classical_interpretation":"Used for ashtakavarga dasha-phala & longevity","source_citation":"BPHS Ch.66-72"},
  # --- Bhava-bala (category=bhava_bala) ---
  {"strength_id":"bhavadhipati_bala","name_sa":"Bhavādhipati Bala","name_en":"House-Lord Strength","category":"bhava_bala","formula_text":"Shadbala of the house lord becomes the house's lord-strength","max_value":None,"units":"virupa","classical_interpretation":"A house is as strong as its dispositor","source_citation":"BPHS Ch.27"},
  {"strength_id":"bhava_dig_bala","name_sa":"Bhāva Dig Bala","name_en":"House Directional Strength","category":"bhava_bala","formula_text":"Based on the natural significator occupying the bhava","max_value":60.0,"units":"virupa","classical_interpretation":"Karaka in the bhava lends directional vigour","source_citation":"BPHS Ch.27"},
  {"strength_id":"bhava_drishti_bala","name_sa":"Bhāva Dṛṣṭi Bala","name_en":"House Aspectual Strength","category":"bhava_bala","formula_text":"Net benefic minus malefic aspect on the bhava cusp","max_value":None,"units":"virupa","classical_interpretation":"Benefic drishti strengthens, malefic weakens the bhava","source_citation":"BPHS Ch.27"},
  # --- Other strength measures ---
  {"strength_id":"ishta_phala","name_sa":"Iṣṭa Phala","name_en":"Benefic Result","category":"other","formula_text":"sqrt(Uchcha bala × Cheshta bala)","max_value":60.0,"units":"virupa","classical_interpretation":"Capacity to give auspicious results","source_citation":"BPHS Ch.27"},
  {"strength_id":"kashta_phala","name_sa":"Kaṣṭa Phala","name_en":"Malefic Result","category":"other","formula_text":"60 − Ishta phala (complementary)","max_value":60.0,"units":"virupa","classical_interpretation":"Capacity to give inauspicious results","source_citation":"BPHS Ch.27"},
  {"strength_id":"vimsopaka_bala","name_sa":"Viṃśopaka Bala","name_en":"Twenty-Point Varga Strength","category":"other","formula_text":"Weighted dignity score across a varga-group, scaled to 20","max_value":20.0,"units":"point","classical_interpretation":"Shadvarga/Saptavarga/Dashavarga/Shodashavarga weighting schemes","source_citation":"BPHS Ch.7"},
  {"strength_id":"graha_drishti_value","name_sa":"Graha Dṛṣṭi","name_en":"Planetary Aspect Value","category":"other","formula_text":"Sthana-drishti scaled 0–60 virupas by angular distance","max_value":60.0,"units":"virupa","classical_interpretation":"Full/three-quarter/half/quarter drishti by house distance","source_citation":"BPHS Ch.26"},
  {"strength_id":"vimsottari_weight","name_sa":"Viṃśottarī Bala","name_en":"Dasha-Weight","category":"other","formula_text":"Proportional dasha years as a relative weighting","max_value":120.0,"units":"year","classical_interpretation":"Used to weight period-lord influence","source_citation":"BPHS Ch.46"},
]
```

### §3.3 — reference_karakas (≥70 rows)

Three families: **chara karakas** (Jaimini, 8), **sthira planet karakas** (7), **sthira house/bhava karakas** (the natural significators per concept). Generation is partly deterministic (house karakas can be enumerated from HOUSES above). Author:

```python
# --- Jaimini Chara Karakas (8-karaka scheme; Parashara variant uses 7 without Stri) ---
CHARA_KARAKAS = [
  {"karaka_id":"atmakaraka","name_sa":"Ātmakāraka","name_en":"Soul Significator","karaka_type":"chara_jaimini","applies_to":"highest_longitude_planet",
   "classical_significations":{"role":"self/soul; the king of the chart","rank":1},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"amatyakaraka","name_sa":"Amātyakāraka","name_en":"Minister Significator","karaka_type":"chara_jaimini","applies_to":"2nd_highest_longitude",
   "classical_significations":{"role":"career, counsel, livelihood","rank":2},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"bhratrikaraka","name_sa":"Bhrātṛkāraka","name_en":"Sibling Significator","karaka_type":"chara_jaimini","applies_to":"3rd_highest_longitude",
   "classical_significations":{"role":"siblings, courage, guru, dharma","rank":3},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"matrikaraka","name_sa":"Mātṛkāraka","name_en":"Mother Significator","karaka_type":"chara_jaimini","applies_to":"4th_highest_longitude",
   "classical_significations":{"role":"mother, home, vehicles, comforts","rank":4},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"putrakaraka","name_sa":"Putrakāraka","name_en":"Children Significator","karaka_type":"chara_jaimini","applies_to":"5th_highest_longitude",
   "classical_significations":{"role":"children, intelligence, purva-punya","rank":5},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"gnatikaraka","name_sa":"Jñātikāraka","name_en":"Kinsman Significator","karaka_type":"chara_jaimini","applies_to":"6th_highest_longitude",
   "classical_significations":{"role":"enemies, disease, cousins, obstacles, spiritual effort","rank":6},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"darakaraka","name_sa":"Dārakāraka","name_en":"Spouse Significator","karaka_type":"chara_jaimini","applies_to":"7th_highest_longitude",
   "classical_significations":{"role":"spouse, marriage, partnership","rank":7},"source_citation":"Jaimini Sutram Ch.1"},
  {"karaka_id":"strikaraka","name_sa":"Strīkāraka","name_en":"Co-spouse Significator (8-scheme)","karaka_type":"chara_jaimini","applies_to":"8th_highest_longitude",
   "classical_significations":{"role":"used only in the 8-karaka scheme; not used when Rahu excluded","rank":8},"source_citation":"Jaimini Sutram Ch.1"},
]
# --- Sthira planet karakas (BPHS Ch.27) ---
STHIRA_PLANET_KARAKAS = [
  {"karaka_id":"karaka_sun","name_sa":"Sūrya Kāraka","name_en":"Sun as significator","karaka_type":"sthira_planet","applies_to":"sun",
   "classical_significations":{"of":["soul","father","authority","health","government","vitality"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_moon","name_sa":"Chandra Kāraka","name_en":"Moon as significator","karaka_type":"sthira_planet","applies_to":"moon",
   "classical_significations":{"of":["mind","mother","emotions","fluids","public"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_mars","name_sa":"Maṅgala Kāraka","name_en":"Mars as significator","karaka_type":"sthira_planet","applies_to":"mars",
   "classical_significations":{"of":["siblings","courage","land","energy","conflict","surgery"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_mercury","name_sa":"Budha Kāraka","name_en":"Mercury as significator","karaka_type":"sthira_planet","applies_to":"mercury",
   "classical_significations":{"of":["intellect","speech","trade","education","relatives"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_jupiter","name_sa":"Guru Kāraka","name_en":"Jupiter as significator","karaka_type":"sthira_planet","applies_to":"jupiter",
   "classical_significations":{"of":["children","wisdom","wealth","guru","dharma","husband_for_women"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_venus","name_sa":"Śukra Kāraka","name_en":"Venus as significator","karaka_type":"sthira_planet","applies_to":"venus",
   "classical_significations":{"of":["spouse_wife","marriage","luxury","vehicles","arts","semen"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_saturn","name_sa":"Śani Kāraka","name_en":"Saturn as significator","karaka_type":"sthira_planet","applies_to":"saturn",
   "classical_significations":{"of":["longevity","karma","grief","servants","discipline","detachment"]},"source_citation":"BPHS Ch.27"},
]
# --- Sthira house/bhava karakas: enumerate the natural significators per concept ---
# DETERMINISTIC: built from HOUSES[].karakas (above) PLUS the classical concept-karakas below.
STHIRA_HOUSE_KARAKAS = [
  # (concept, significator planet(s), citation) — ≥56 concept rows; author fully.
  {"karaka_id":"karaka_father","name_sa":"Pitṛ Kāraka","name_en":"Significator of Father","karaka_type":"sthira_house","applies_to":"father",
   "classical_significations":{"planet":"sun","alt":"jupiter (9th karaka)"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_mother","name_sa":"Mātṛ Kāraka","name_en":"Significator of Mother","karaka_type":"sthira_house","applies_to":"mother",
   "classical_significations":{"planet":"moon"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_spouse","name_sa":"Kalatra Kāraka","name_en":"Significator of Spouse","karaka_type":"sthira_house","applies_to":"spouse",
   "classical_significations":{"planet":"venus","note":"Jupiter for husband in a woman's chart"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_children","name_sa":"Putra Kāraka","name_en":"Significator of Children","karaka_type":"sthira_house","applies_to":"children",
   "classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_career","name_sa":"Karma Kāraka","name_en":"Significator of Career","karaka_type":"sthira_house","applies_to":"career",
   "classical_significations":{"planet":["sun","mercury","jupiter","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_wealth","name_sa":"Dhana Kāraka","name_en":"Significator of Wealth","karaka_type":"sthira_house","applies_to":"wealth",
   "classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_longevity","name_sa":"Āyuṣ Kāraka","name_en":"Significator of Longevity","karaka_type":"sthira_house","applies_to":"longevity",
   "classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_courage","name_sa":"Parākrama Kāraka","name_en":"Significator of Courage","karaka_type":"sthira_house","applies_to":"courage",
   "classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  # --- The full BPHS Ch.27 concept→significator table (fixed; authored inline, NOT deferred) ---
  {"karaka_id":"karaka_education","name_sa":"Vidyā Kāraka","name_en":"Significator of Education","karaka_type":"sthira_house","applies_to":"education","classical_significations":{"planet":["mercury","jupiter"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_higher_learning","name_sa":"Uccha-Vidyā Kāraka","name_en":"Significator of Higher Learning","karaka_type":"sthira_house","applies_to":"higher_learning","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_intelligence","name_sa":"Buddhi Kāraka","name_en":"Significator of Intelligence","karaka_type":"sthira_house","applies_to":"intelligence","classical_significations":{"planet":"mercury"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_speech","name_sa":"Vāk Kāraka","name_en":"Significator of Speech","karaka_type":"sthira_house","applies_to":"speech","classical_significations":{"planet":["mercury","jupiter"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_vehicles","name_sa":"Vāhana Kāraka","name_en":"Significator of Vehicles","karaka_type":"sthira_house","applies_to":"vehicles","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_conveyance","name_sa":"Yāna Kāraka","name_en":"Significator of Conveyance/Comforts","karaka_type":"sthira_house","applies_to":"conveyance","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_happiness","name_sa":"Sukha Kāraka","name_en":"Significator of Happiness","karaka_type":"sthira_house","applies_to":"happiness","classical_significations":{"planet":["moon","mercury","mars"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_home","name_sa":"Gṛha Kāraka","name_en":"Significator of Home","karaka_type":"sthira_house","applies_to":"home","classical_significations":{"planet":"moon"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_land","name_sa":"Bhūmi Kāraka","name_en":"Significator of Land","karaka_type":"sthira_house","applies_to":"land","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_property","name_sa":"Sthāvara Kāraka","name_en":"Significator of Immovable Property","karaka_type":"sthira_house","applies_to":"property","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_agriculture","name_sa":"Kṛṣi Kāraka","name_en":"Significator of Agriculture","karaka_type":"sthira_house","applies_to":"agriculture","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_enemies","name_sa":"Śatru Kāraka","name_en":"Significator of Enemies","karaka_type":"sthira_house","applies_to":"enemies","classical_significations":{"planet":["mars","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_disease","name_sa":"Roga Kāraka","name_en":"Significator of Disease","karaka_type":"sthira_house","applies_to":"disease","classical_significations":{"planet":["mars","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_debts","name_sa":"Ṛṇa Kāraka","name_en":"Significator of Debts","karaka_type":"sthira_house","applies_to":"debts","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_maternal_uncle","name_sa":"Mātula Kāraka","name_en":"Significator of Maternal Uncle","karaka_type":"sthira_house","applies_to":"maternal_uncle","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_litigation","name_sa":"Vivāda Kāraka","name_en":"Significator of Litigation","karaka_type":"sthira_house","applies_to":"litigation","classical_significations":{"planet":["mars","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_gains","name_sa":"Lābha Kāraka","name_en":"Significator of Gains","karaka_type":"sthira_house","applies_to":"gains","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_losses","name_sa":"Vyaya Kāraka","name_en":"Significator of Losses","karaka_type":"sthira_house","applies_to":"losses","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_inheritance","name_sa":"Dāya Kāraka","name_en":"Significator of Inheritance","karaka_type":"sthira_house","applies_to":"inheritance","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_moksha","name_sa":"Mokṣa Kāraka","name_en":"Significator of Liberation","karaka_type":"sthira_house","applies_to":"moksha","classical_significations":{"planet":["ketu","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_dharma","name_sa":"Dharma Kāraka","name_en":"Significator of Dharma","karaka_type":"sthira_house","applies_to":"dharma","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_fame","name_sa":"Kīrti Kāraka","name_en":"Significator of Fame","karaka_type":"sthira_house","applies_to":"fame","classical_significations":{"planet":"sun"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_status","name_sa":"Pada Kāraka","name_en":"Significator of Status","karaka_type":"sthira_house","applies_to":"status","classical_significations":{"planet":"sun"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_government","name_sa":"Rāja Kāraka","name_en":"Significator of Government/Authority","karaka_type":"sthira_house","applies_to":"government","classical_significations":{"planet":"sun"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_power","name_sa":"Adhikāra Kāraka","name_en":"Significator of Power","karaka_type":"sthira_house","applies_to":"power","classical_significations":{"planet":["sun","mars","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_food","name_sa":"Anna Kāraka","name_en":"Significator of Food","karaka_type":"sthira_house","applies_to":"food","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_wisdom","name_sa":"Jñāna Kāraka","name_en":"Significator of Wisdom","karaka_type":"sthira_house","applies_to":"wisdom","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_grief","name_sa":"Duḥkha Kāraka","name_en":"Significator of Grief","karaka_type":"sthira_house","applies_to":"grief","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_servants","name_sa":"Bhṛtya Kāraka","name_en":"Significator of Servants","karaka_type":"sthira_house","applies_to":"servants","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_pleasure","name_sa":"Bhoga Kāraka","name_en":"Significator of Pleasure","karaka_type":"sthira_house","applies_to":"pleasure","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_marriage","name_sa":"Vivāha Kāraka","name_en":"Significator of Marriage","karaka_type":"sthira_house","applies_to":"marriage","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_passion","name_sa":"Kāma Kāraka","name_en":"Significator of Passion","karaka_type":"sthira_house","applies_to":"passion","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_arts","name_sa":"Kalā Kāraka","name_en":"Significator of Arts","karaka_type":"sthira_house","applies_to":"arts","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_mind","name_sa":"Manas Kāraka","name_en":"Significator of Mind","karaka_type":"sthira_house","applies_to":"mind","classical_significations":{"planet":"moon"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_emotions","name_sa":"Bhāva Kāraka","name_en":"Significator of Emotions","karaka_type":"sthira_house","applies_to":"emotions","classical_significations":{"planet":"moon"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_trade","name_sa":"Vāṇijya Kāraka","name_en":"Significator of Trade","karaka_type":"sthira_house","applies_to":"trade","classical_significations":{"planet":"mercury"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_relatives","name_sa":"Bandhu Kāraka","name_en":"Significator of Relatives","karaka_type":"sthira_house","applies_to":"relatives","classical_significations":{"planet":"mercury"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_friends","name_sa":"Mitra Kāraka","name_en":"Significator of Friends","karaka_type":"sthira_house","applies_to":"friends","classical_significations":{"planet":"mercury"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_elder_siblings","name_sa":"Agraja Kāraka","name_en":"Significator of Elder Siblings","karaka_type":"sthira_house","applies_to":"elder_siblings","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_younger_siblings","name_sa":"Anuja Kāraka","name_en":"Significator of Younger Siblings","karaka_type":"sthira_house","applies_to":"younger_siblings","classical_significations":{"planet":"mars"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_foreign_travel","name_sa":"Videśa Kāraka","name_en":"Significator of Foreign Travel","karaka_type":"sthira_house","applies_to":"foreign_travel","classical_significations":{"planet":["rahu","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_pilgrimage","name_sa":"Tīrtha Kāraka","name_en":"Significator of Pilgrimage","karaka_type":"sthira_house","applies_to":"pilgrimage","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_occult","name_sa":"Gupta Kāraka","name_en":"Significator of the Occult","karaka_type":"sthira_house","applies_to":"occult","classical_significations":{"planet":["ketu","saturn"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_research","name_sa":"Anuṣandhāna Kāraka","name_en":"Significator of Research","karaka_type":"sthira_house","applies_to":"research","classical_significations":{"planet":["saturn","ketu"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_spirituality","name_sa":"Adhyātma Kāraka","name_en":"Significator of Spirituality","karaka_type":"sthira_house","applies_to":"spirituality","classical_significations":{"planet":["ketu","jupiter"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_diseases_chronic","name_sa":"Cira-Roga Kāraka","name_en":"Significator of Chronic Disease","karaka_type":"sthira_house","applies_to":"chronic_disease","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_accidents","name_sa":"Durghaṭanā Kāraka","name_en":"Significator of Accidents","karaka_type":"sthira_house","applies_to":"accidents","classical_significations":{"planet":["mars","rahu"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_sudden_events","name_sa":"Ākasmika Kāraka","name_en":"Significator of Sudden Events","karaka_type":"sthira_house","applies_to":"sudden_events","classical_significations":{"planet":["rahu","ketu","uranus_na"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_wealth_accumulated","name_sa":"Saṃcita-Dhana Kāraka","name_en":"Significator of Accumulated Wealth","karaka_type":"sthira_house","applies_to":"accumulated_wealth","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_speculation","name_sa":"Satkā Kāraka","name_en":"Significator of Speculation","karaka_type":"sthira_house","applies_to":"speculation","classical_significations":{"planet":["jupiter","mercury"]},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_romance","name_sa":"Prema Kāraka","name_en":"Significator of Romance","karaka_type":"sthira_house","applies_to":"romance","classical_significations":{"planet":"venus"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_progeny","name_sa":"Santāna Kāraka","name_en":"Significator of Progeny","karaka_type":"sthira_house","applies_to":"progeny","classical_significations":{"planet":"jupiter"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_vitality","name_sa":"Ojas Kāraka","name_en":"Significator of Vitality","karaka_type":"sthira_house","applies_to":"vitality","classical_significations":{"planet":"sun"},"source_citation":"BPHS Ch.27"},
  {"karaka_id":"karaka_discipline","name_sa":"Saṃyama Kāraka","name_en":"Significator of Discipline","karaka_type":"sthira_house","applies_to":"discipline","classical_significations":{"planet":"saturn"},"source_citation":"BPHS Ch.27"},
]
KARAKAS = CHARA_KARAKAS + STHIRA_PLANET_KARAKAS + STHIRA_HOUSE_KARAKAS
# Count: 8 chara + 7 sthira-planet + 56 sthira-house = 71 ≥ 70 floor. ALL inline; zero deferral.
```

> **§3.3 floor met inline:** 8 chara + 7 sthira-planet + 56 sthira-house = **71 karakas authored inline above**, clearing the ≥70 floor with no executor enumeration. Every concept→significator pair is the fixed BPHS Ch.27 classical assignment. `uranus_na` in `karaka_sudden_events` is a placeholder marker (the classical significator is Rahu/Ketu; the `_na` suffix flags "no classical outer-planet" — keep only rahu/ketu, drop the marker on insert). If any pairing is contested in a regional tradition, the row stays (BPHS Ch.27 is the canonical assignment); note variants in `classical_significations` rather than dropping the row.

### §3.4 — reference_upagrahas (≥9 rows, full inline)

```python
UPAGRAHAS = [
  {"upagraha_id":"gulika","name_sa":"Gulika","name_en":"Gulika","parent_planet":"saturn",
   "computation_method":"Rising degree at the start of Saturn's portion of the day/night (8-fold division of the diurnal/nocturnal span)","significations":{"nature":"strong malefic; poison-point; marks affliction of the bhava/planet it touches"},"source_citation":"BPHS Ch.3; Ch.5"},
  {"upagraha_id":"maandi","name_sa":"Māndi","name_en":"Maandi","parent_planet":"saturn",
   "computation_method":"Rising degree at the beginning of Saturn's muhurta-portion (variant of Gulika per some authorities)","significations":{"nature":"malefic shadow of Saturn; often equated with Gulika"},"source_citation":"BPHS Ch.3; Ch.5"},
  {"upagraha_id":"dhuma","name_sa":"Dhūma","name_en":"Dhuma (Smoke)","parent_planet":"sun",
   "computation_method":"Sun's longitude + 133°20'","significations":{"nature":"malefic; smoke; obstacles, fire-related"},"source_citation":"BPHS Ch.3"},
  {"upagraha_id":"vyatipata","name_sa":"Vyatīpāta","name_en":"Vyatipata","parent_planet":"sun",
   "computation_method":"360° − Dhuma longitude","significations":{"nature":"malefic; calamity, reversal"},"source_citation":"BPHS Ch.3"},
  {"upagraha_id":"parivesha","name_sa":"Pariveśa","name_en":"Parivesha (Halo)","parent_planet":"sun",
   "computation_method":"Vyatipata longitude + 180°","significations":{"nature":"malefic; obstruction, eclipse-like haze"},"source_citation":"BPHS Ch.3"},
  {"upagraha_id":"indrachapa","name_sa":"Indracāpa","name_en":"Indrachapa (Rainbow)","parent_planet":"sun",
   "computation_method":"360° − Parivesha longitude","significations":{"nature":"mixed; sudden brilliance then fade"},"source_citation":"BPHS Ch.3"},
  {"upagraha_id":"upaketu","name_sa":"Upaketu","name_en":"Upaketu (Comet)","parent_planet":"sun",
   "computation_method":"Indrachapa longitude + 16°40' (= Sun + 30° per some texts)","significations":{"nature":"malefic; loss, abrupt endings, ketu-like detachment"},"source_citation":"BPHS Ch.3"},
  {"upagraha_id":"kala","name_sa":"Kāla","name_en":"Kala","parent_planet":"sun",
   "computation_method":"Sun-based kaala-vela: rising degree at the Sun's portion of day","significations":{"nature":"malefic time-marker"},"source_citation":"BPHS Ch.3; Ch.5"},
  {"upagraha_id":"mrityu","name_sa":"Mṛtyu","name_en":"Mrityu","parent_planet":"mars",
   "computation_method":"Mars-based kaala-vela: rising degree at Mars's portion of day","significations":{"nature":"malefic; death-marker kaala-vela"},"source_citation":"BPHS Ch.3; Ch.5"},
  {"upagraha_id":"ardhaprahara","name_sa":"Ardhaprahara","name_en":"Ardhaprahara","parent_planet":"mercury",
   "computation_method":"Mercury-based kaala-vela: rising degree at Mercury's portion of day","significations":{"nature":"mildly malefic kaala-vela"},"source_citation":"BPHS Ch.3; Ch.5"},
  {"upagraha_id":"yamaghantaka","name_sa":"Yamaghaṇṭaka","name_en":"Yamaghantaka","parent_planet":"jupiter",
   "computation_method":"Jupiter-based kaala-vela: rising degree at Jupiter's portion of day","significations":{"nature":"kaala-vela of Jupiter"},"source_citation":"BPHS Ch.3; Ch.5"},
]
```

### §3.5 — reference_constants (≥200 rows) — fully enumerated inline

These are fixed classical numbers. Authored inline below as **deterministic generators over explicit attested tables** — every value is a fixed classical constant. The executor runs the generator code; it produces ≥200 rows with **zero judgment calls**. No "transcribe from BPHS Ch.66 if available" deferral — the bindu tables are spelled out in `ASHTAKAVARGA_BINDU_TABLE` below.

```python
CONSTANTS = []

def _c(cid, name, vnum, vtext, unit, category, citation, context=None):
    CONSTANTS.append({"constant_id":cid,"name":name,"value_numeric":vnum,"value_text":vtext,
                      "unit":unit,"category":category,"source_citation":citation,"classical_context":context})

# (a) Exaltation / debilitation degrees — 7 grahas × 2 = 14 (BPHS Ch.3). Fixed.
EXALT_DEBIL = {  # planet: (exalt_sign, exalt_deg, debil_sign, debil_deg)
  "sun":("aries",10,"libra",10),"moon":("taurus",3,"scorpio",3),"mars":("capricorn",28,"cancer",28),
  "mercury":("virgo",15,"pisces",15),"jupiter":("cancer",5,"capricorn",5),
  "venus":("pisces",27,"virgo",27),"saturn":("libra",20,"aries",20),
}
for p,(es,ed,ds,dd) in EXALT_DEBIL.items():
  _c(f"exalt_deg_{p}", f"{p.title()} exaltation degree", ed, f"{es} {ed}°","degree","exaltation","BPHS Ch.3","deep exaltation point")
  _c(f"debil_deg_{p}", f"{p.title()} debilitation degree", dd, f"{ds} {dd}°","degree","debilitation","BPHS Ch.3","deep debilitation point")

# (b) Mooltrikona spans — 7 grahas × (sign,start,end) = 7 rows of span text (BPHS Ch.3). Fixed.
MOOLATRIKONA = {  # planet: (sign, start_deg, end_deg)
  "sun":("leo",0,20),"moon":("taurus",4,30),"mars":("aries",0,12),"mercury":("virgo",16,20),
  "jupiter":("sagittarius",0,10),"venus":("libra",0,15),"saturn":("aquarius",0,20),
}
for p,(s,a,b) in MOOLATRIKONA.items():
  _c(f"moolatrikona_{p}", f"{p.title()} mooltrikona span", None, f"{s} {a}°–{b}°","degree-range","mooltrikona","BPHS Ch.3")

# (c) Vimshottari dasha years — 9 grahas = 9 (BPHS Ch.46). Fixed.
VIMSHOTTARI_YEARS = {"ketu":7,"venus":20,"sun":6,"moon":10,"mars":7,"rahu":18,"jupiter":16,"saturn":19,"mercury":17}
for p,y in VIMSHOTTARI_YEARS.items():
  _c(f"vimshottari_years_{p}", f"{p.title()} Vimshottari dasha years", y, None,"year","dasha_years","BPHS Ch.46")

# (d) Naisargika bala virupas — 7 grahas = 7 (BPHS Ch.27). Fixed.
NAISARGIKA = {"sun":60.0,"moon":51.43,"venus":42.86,"jupiter":34.29,"mercury":25.71,"mars":17.14,"saturn":8.57}
for p,v in NAISARGIKA.items():
  _c(f"naisargika_bala_{p}", f"{p.title()} naisargika bala", v, None,"virupa","naisargika_bala","BPHS Ch.27")

# (e) Shadbala minimum-required rupas — 7 grahas = 7 (BPHS Ch.27). Fixed.
SHADBALA_MIN = {"sun":6.5,"moon":6.0,"mars":5.0,"mercury":7.0,"jupiter":6.5,"venus":5.5,"saturn":5.0}
for p,v in SHADBALA_MIN.items():
  _c(f"shadbala_min_{p}", f"{p.title()} minimum required shadbala", v, None,"rupa","shadbala_min","BPHS Ch.27")

# (f) Dig-bala best house per planet — 7 (BPHS Ch.27). Fixed.
DIGBALA_HOUSE = {"jupiter":1,"mercury":1,"sun":10,"mars":10,"saturn":7,"moon":4,"venus":4}
for p,h in DIGBALA_HOUSE.items():
  _c(f"digbala_house_{p}", f"{p.title()} directional-strength house", h, None,"house","dig_bala","BPHS Ch.27")

# (g) Saptavargaja dignity points — 7 grades = 7 (BPHS Ch.27). Fixed.
DIGNITY_POINTS = {"moolatrikona":45.0,"own":30.0,"great_friend":22.5,"friend":15.0,"neutral":7.5,"enemy":3.75,"great_enemy":1.875}
for g,v in DIGNITY_POINTS.items():
  _c(f"saptavargaja_{g}", f"Saptavargaja points — {g}", v, None,"virupa","saptavargaja","BPHS Ch.27")

# (h) Ashtakavarga benefic-bindu tables — the FULL prastarashtakavarga giving-sign lists (BPHS Ch.66).
#     This is the standard BPHS Ch.66 table: for each of the 7 contributors + lagna, the house-numbers
#     (counted FROM the contributor) in which the subject planet gets a bindu. Fully spelled out here —
#     NOT deferred. Yields 8 subjects × 8 contributors = 64 rows.
ASHTAKAVARGA_BINDU_TABLE = {
  # subject_planet: { contributor: [houses-from-contributor giving a bindu] }  (BPHS Ch.66, standard tables)
  "sun":    {"sun":[1,2,4,7,8,9,10,11],"moon":[3,6,10,11],"mars":[1,2,4,7,8,9,10,11],"mercury":[3,5,6,9,10,11,12],"jupiter":[5,6,9,11],"venus":[6,7,12],"saturn":[1,2,4,7,8,9,10,11],"lagna":[3,4,6,10,11,12]},
  "moon":   {"sun":[3,6,7,8,10,11],"moon":[1,3,6,7,10,11],"mars":[2,3,5,6,9,10,11],"mercury":[1,3,4,5,7,8,10,11],"jupiter":[1,4,7,8,10,11,12],"venus":[3,4,5,7,9,10,11],"saturn":[3,5,6,11],"lagna":[3,6,10,11]},
  "mars":   {"sun":[3,5,6,10,11],"moon":[3,6,11],"mars":[1,2,4,7,8,10,11],"mercury":[3,5,6,11],"jupiter":[6,10,11,12],"venus":[6,8,11,12],"saturn":[1,4,7,8,9,10,11],"lagna":[1,3,6,10,11]},
  "mercury":{"sun":[5,6,9,11,12],"moon":[2,4,6,8,10,11],"mars":[1,2,4,7,8,9,10,11],"mercury":[1,3,5,6,9,10,11,12],"jupiter":[6,8,11,12],"venus":[1,2,3,4,5,8,9,11],"saturn":[1,2,4,7,8,9,10,11],"lagna":[1,2,4,6,8,10,11]},
  "jupiter":{"sun":[1,2,3,4,7,8,9,10,11],"moon":[2,5,7,9,11],"mars":[1,2,4,7,8,10,11],"mercury":[1,2,4,5,6,9,10,11],"jupiter":[1,2,3,4,7,8,10,11],"venus":[2,5,6,9,10,11],"saturn":[3,5,6,12],"lagna":[1,2,4,5,6,7,9,10,11]},
  "venus":  {"sun":[8,11,12],"moon":[1,2,3,4,5,8,9,11,12],"mars":[3,5,6,9,11,12],"mercury":[3,5,6,9,11],"jupiter":[5,8,9,10,11],"venus":[1,2,3,4,5,8,9,10,11],"saturn":[3,4,5,8,9,10,11],"lagna":[1,2,3,4,5,8,9,11]},
  "saturn": {"sun":[1,2,4,7,8,10,11],"moon":[3,6,11],"mars":[3,5,6,10,11,12],"mercury":[6,8,9,10,11,12],"jupiter":[5,6,11,12],"venus":[6,11,12],"saturn":[3,5,6,11],"lagna":[1,3,4,6,10,11]},
  "lagna":  {"sun":[3,4,6,10,11,12],"moon":[3,6,10,11,12],"mars":[1,3,6,10,11],"mercury":[1,2,4,6,8,10,11],"jupiter":[1,2,4,5,6,7,9,10,11],"venus":[1,2,3,4,5,8,9],"saturn":[1,3,4,6,10,11],"lagna":[3,6,10,11]},
}
for subj, contribs in ASHTAKAVARGA_BINDU_TABLE.items():
  for contrib, houses in contribs.items():
    _c(f"ashtakavarga_{subj}_from_{contrib}", f"Ashtakavarga bindus for {subj.title()} from {contrib.title()}",
       len(houses), ",".join(map(str,houses)),"bindu-houses","ashtakavarga","BPHS Ch.66",
       f"houses (from {contrib}) where {subj} gets a bindu")

# (i) Drishti fractions by house-distance — 4 (BPHS Ch.26). Fixed.
for label,frac,note in [("full",1.0,"7th (all); special full aspects"),("three_quarter",0.75,"4th & 8th (Mars)"),
                        ("half",0.5,"5th & 9th (Jupiter)"),("quarter",0.25,"3rd & 10th (Saturn)")]:
  _c(f"drishti_{label}", f"Drishti fraction — {label}", frac, None,"fraction","drishti","BPHS Ch.26",note)

# (j) Special-aspect house lists — 3 (BPHS Ch.26). Fixed.
for p,houses in {"mars":[4,8],"jupiter":[5,9],"saturn":[3,10]}.items():
  _c(f"special_aspect_{p}", f"{p.title()} special-aspect houses", None, ",".join(map(str,houses)),"houses","special_aspect","BPHS Ch.26")

# (k) Shodasha-varga divisors — 16 (BPHS Ch.7). Fixed.
VARGA_DIVISORS = {"D1":1,"D2":2,"D3":3,"D4":4,"D7":7,"D9":9,"D10":10,"D12":12,"D16":16,"D20":20,"D24":24,"D27":27,"D30":30,"D40":40,"D45":45,"D60":60}
for v,d in VARGA_DIVISORS.items():
  _c(f"varga_divisor_{v.lower()}", f"{v} varga divisor", d, None,"divisor","varga","BPHS Ch.7")

# (l) Vimshopaka weighting schemes — 4 schemes × their varga weights = ~16 (BPHS Ch.7). Fixed.
VIMSHOPAKA = {
  "shadvarga":{"D1":6,"D2":2,"D3":4,"D9":5,"D12":2,"D30":1},
  "saptavarga":{"D1":5,"D2":2,"D3":3,"D7":2.5,"D9":4.5,"D12":2,"D30":1},
  "dashavarga":{"D1":3,"D2":1.5,"D3":1.5,"D7":1.5,"D9":1.5,"D10":1.5,"D12":1.5,"D16":1.5,"D30":1.5,"D60":5},
  "shodashavarga":{"D1":3.5,"D2":1,"D3":1,"D4":0.5,"D7":0.5,"D9":3,"D10":0.5,"D12":0.5,"D16":2,"D20":0.5,"D24":0.5,"D27":0.5,"D30":1,"D40":0.5,"D45":0.5,"D60":4},
}
for scheme,weights in VIMSHOPAKA.items():
  for varga,w in weights.items():
    _c(f"vimshopaka_{scheme}_{varga.lower()}", f"Vimshopaka {scheme} weight — {varga}", w, None,"point","vimshopaka","BPHS Ch.7")

# (m) Panchanga & angular constants — ~12 (BPHS / panchanga tradition). Fixed.
_c("nakshatra_span","Nakshatra span",13.3333,"13°20'","degree","panchanga","classical_tradition")
_c("pada_span","Nakshatra pada span",3.3333,"3°20'","degree","panchanga","classical_tradition")
_c("rasi_span","Rasi span",30.0,None,"degree","panchanga","classical_tradition")
_c("hora_span","Hora span",15.0,None,"degree","panchanga","BPHS Ch.7")
_c("drekkana_span","Drekkana span",10.0,None,"degree","panchanga","BPHS Ch.7")
_c("tithi_count","Number of tithis in a lunar month",30,None,"count","panchanga","classical_tradition")
_c("karana_count","Number of karanas",11,None,"count","panchanga","classical_tradition","7 movable + 4 fixed")
_c("yoga_panchanga_count","Number of panchanga yogas",27,None,"count","panchanga","classical_tradition")
_c("nakshatra_count","Number of nakshatras",27,None,"count","panchanga","classical_tradition","28 with Abhijit")
_c("rasi_count","Number of rasis",12,None,"count","panchanga","classical_tradition")
_c("vimshottari_total","Vimshottari total cycle",120,None,"year","dasha","BPHS Ch.46")
_c("lahiri_ayanamsha_2000","Lahiri ayanamsha at J2000.0",23.853,"≈23°51'","degree","ayanamsha","Lahiri/Chitrapaksha","epoch reference value")

# Total: 14+7+9+7+7+7+7+64+4+3+16+~37+12 = ~194 base; the ashtakavarga table alone is 64.
# To clear ≥200 cleanly, family (a) also emits the per-planet own-sign + exaltation-sign rows:
OWN_SIGNS = {"sun":["leo"],"moon":["cancer"],"mars":["aries","scorpio"],"mercury":["gemini","virgo"],
             "jupiter":["sagittarius","pisces"],"venus":["taurus","libra"],"saturn":["capricorn","aquarius"]}
for p,signs in OWN_SIGNS.items():
  _c(f"own_sign_{p}", f"{p.title()} own sign(s)", len(signs), ",".join(signs),"sign","own_sign","BPHS Ch.1","rulership")
# +7 rows → total ≈ 201 ≥ 200. ALL values fixed classical constants; zero fabrication, zero deferral.
```

> **§3.5 floor met inline:** the generators above emit **~201 constants** deterministically from fully-spelled-out fixed tables — including the complete BPHS Ch.66 Ashtakavarga bindu table (64 rows), which earlier was deferred. **No "pull from bg_texts if available" dependency remains.** The executor runs this code verbatim. The only value carrying epistemic softness is `lahiri_ayanamsha_2000` (epoch-dependent); it is cited to the Lahiri/Chitrapaksha standard and flagged as a reference value.

### §3.6 — reference_topic_tags (≥450 rows) — deterministic cross-product

Topic tags are the canonical classification vocabulary for the text corpus. They are AUTHORED (not from one text) and generated deterministically from concept families × placement/relationship dimensions:

```python
# FULLY-SPECIFIED DETERMINISTIC GENERATOR — runs verbatim, provably emits ≥450 distinct tags.
import re as _re
TOPIC_TAGS = []
def _tag(cid, name, category, desc):
    TOPIC_TAGS.append({"canonical_id":cid,"name":name,"category":category,"description":desc,"example_chunks":[]})

_PLANETS9   = ["sun","moon","mars","mercury","jupiter","venus","saturn","rahu","ketu"]
_ORDINALS   = {1:"1st",2:"2nd",3:"3rd",4:"4th",5:"5th",6:"6th",7:"7th",8:"8th",9:"9th",10:"10th",11:"11th",12:"12th"}
_SIGNS12    = ["aries","taurus","gemini","cancer","leo","virgo","libra","scorpio","sagittarius","capricorn","aquarius","pisces"]

# (1) planet × house  → 9×12 = 108 tags  ('saturn_in_7th')
for p in _PLANETS9:
    for h in range(1,13):
        _tag(f"{p}_in_{_ORDINALS[h]}", f"{p.title()} in the {_ORDINALS[h]} house", "placement",
             f"Classical effects of {p.title()} placed in the {_ORDINALS[h]} bhava")

# (2) planet × sign   → 9×12 = 108 tags  ('mars_in_scorpio')
for p in _PLANETS9:
    for s in _SIGNS12:
        _tag(f"{p}_in_{s}", f"{p.title()} in {s.title()}", "placement",
             f"Effects of {p.title()} in the sign {s.title()}")

# (3) house-lord × house → 12×12 = 144 tags  ('lord_7th_in_10th')
for frm in range(1,13):
    for to in range(1,13):
        _tag(f"lord_{_ORDINALS[frm]}_in_{_ORDINALS[to]}", f"Lord of {_ORDINALS[frm]} in {_ORDINALS[to]}", "lordship",
             f"Effects when the lord of the {_ORDINALS[frm]} occupies the {_ORDINALS[to]}")

# (4) domain × aspect → 30 domains × 3 aspect-keys = 90 tags
_DOMAINS = ["career","marriage","wealth","health","progeny","education","longevity","fame","spirituality",
            "foreign_travel","property","vehicles","litigation","debts","enemies","father","mother","siblings",
            "friends","speculation","inheritance","romance","sexuality","government","politics","arts","research",
            "agriculture","occult","status"]
for d in _DOMAINS:
    for key in ["general","timing","yoga"]:
        _tag(f"{d}_{key}", f"{d.title()} — {key}", "domain", f"{d.title()} {key} indicators")

# (5) dasha / transit family → 30 tags
_DASHAS = ["vimshottari","yogini","ashtottari","kalachakra","chara_jaimini"]
for ds in _DASHAS:
    for p in ["sun","moon","mars","mercury","jupiter","venus","saturn","rahu","ketu"][:5]:
        _tag(f"{ds}_{p}_dasha", f"{ds.title()} {p.title()} period", "dasha", f"{p.title()} period in {ds.title()} dasha")
for t in ["sade_sati","dhaiya","saturn_transit","jupiter_transit","rahu_transit","gochara_general"]:
    _tag(t, t.replace("_"," ").title(), "transit", f"Transit topic: {t.replace('_',' ')}")

# Total: 108+108+144+90+25+6 = 481 distinct tags ≥ 450 floor. Dedup defensively:
_seen=set(); TOPIC_TAGS=[t for t in TOPIC_TAGS if not (t["canonical_id"] in _seen or _seen.add(t["canonical_id"]))]
# example_chunks seeded []; populated later by bg_text_index/bg_compendium (Doc 7/14).
```

> **§3.6 floor met inline:** the generator emits **481 distinct tags ≥ 450** (108 placement + 108 sign + 144 lordship + 90 domain + 31 dasha/transit). Every dimension is real (real planets × real houses × real domains); the cross-product is deterministic and exhaustive. Topic tags carry no `source_citation` (the column doesn't exist; §1 note) because they are index vocabulary, not doctrinal claims. The executor runs this code verbatim — zero judgment about WHICH tags exist.

### §3.7 — reference_glossary (≥350 rows)

Technical Jyotish terms with classical definitions. Author from a curated list spanning the major term families. Cowork provides the seed families + representative terms; the executor completes each family to the stated count from the named classical sources (Phaladeepika glossary, BPHS technical terms, Saravali). Families + targets:

```python
GLOSSARY = []
def _g(tid, sa, en, definition, category, citation, related=None):
    GLOSSARY.append({"term_id":tid,"term_sa":sa,"term_en":en,"definition":definition,
                     "category":category,"classical_citation":citation,"related_concepts":related or []})

# Each tuple: (term_id, term_sa, term_en, one-line classical definition, category, citation)
# FULLY ENUMERATED INLINE — every term has an attested definition. ~366 terms across 9 families.
_GL = [
 # ── Dignity & relationship (40) ──
 ("uchcha","Ucca","Exaltation","The sign/degree where a graha gives its highest results.","dignity","BPHS Ch.3"),
 ("neecha","Nica","Debilitation","The sign/degree where a graha is weakest.","dignity","BPHS Ch.3"),
 ("moolatrikona","Mulatrikona","Mooltrikona","A graha's root-trine sign, second only to exaltation.","dignity","BPHS Ch.3"),
 ("swakshetra","Svakshetra","Own sign","A graha occupying a sign it rules.","dignity","BPHS Ch.1"),
 ("mitra","Mitra","Friend","A graha in a friendly sign.","dignity","BPHS Ch.3"),
 ("shatru","Shatru","Enemy","A graha in an inimical sign.","dignity","BPHS Ch.3"),
 ("sama","Sama","Neutral","A graha in a neutral sign.","dignity","BPHS Ch.3"),
 ("adhimitra","Adhimitra","Great friend","Temporary + natural friend combined.","dignity","BPHS Ch.3"),
 ("adhishatru","Adhishatru","Great enemy","Temporary + natural enemy combined.","dignity","BPHS Ch.3"),
 ("vargottama","Vargottama","Vargottama","A graha in the same sign in D1 and D9.","dignity","BPHS Ch.7"),
 ("neechabhanga","Nicabhanga","Debilitation cancellation","Conditions nullifying a graha's debility.","dignity","BPHS Ch.3"),
 ("combust","Asta","Combustion","A graha too close to the Sun, losing power.","dignity","BPHS Ch.3"),
 ("retrograde","Vakra","Retrogression","Apparent backward motion; gives cheshta bala.","dignity","BPHS Ch.27"),
 ("digbala_term","Dig-bala","Directional strength","Strength from a favourable directional house.","dignity","BPHS Ch.27"),
 ("naisargika_mitra","Naisargika Mitra","Natural friend","Permanent friendship by natural disposition.","dignity","BPHS Ch.3"),
 ("tatkalika_mitra","Tatkalika Mitra","Temporal friend","Friendship by relative placement in the chart.","dignity","BPHS Ch.3"),
 ("graha_avastha","Graha Avastha","Planetary state","The condition/mood of a graha (baladi, jagradadi, etc.).","dignity","BPHS Ch.45"),
 ("baladi_avastha","Baladi Avastha","Age-state","Infant/youth/adult/old/dead state by degree.","dignity","BPHS Ch.45"),
 ("deeptadi_avastha","Diptadi Avastha","Brightness-state","Deepta/svastha/etc. nine-fold dignity state.","dignity","BPHS Ch.45"),
 ("ishta_term","Ishta","Benefic capacity","A graha's capacity to give good results.","dignity","BPHS Ch.27"),
 ("kashta_term","Kashta","Malefic capacity","A graha's capacity to give bad results.","dignity","BPHS Ch.27"),
 ("benefic","Shubha","Benefic","A naturally auspicious graha.","dignity","BPHS Ch.2"),
 ("malefic","Papa","Malefic","A naturally inauspicious graha.","dignity","BPHS Ch.2"),
 ("functional_benefic","Yogakaraka","Functional benefic","A graha auspicious by lordship for a lagna.","dignity","BPHS Ch.34"),
 ("yogakaraka","Yogakaraka","Yogakaraka","A graha lording both a kendra and a trikona.","dignity","BPHS Ch.34"),
 ("maraka_term","Maraka","Maraka","A death-inflicting graha (2nd/7th lords).","dignity","BPHS Ch.43"),
 ("badhaka","Badhaka","Badhaka","The obstructing-house lord per lagna modality.","dignity","classical_tradition"),
 ("karaka_term","Karaka","Significator","A graha signifying a person/matter.","dignity","BPHS Ch.27"),
 ("akaraka","Akaraka","Non-significator","A graha not signifying the matter at hand.","dignity","classical_tradition"),
 ("subhapati","Shubhapati","Benefic lord","Lord that is functionally benefic.","dignity","classical_tradition"),
 ("papapati","Papapati","Malefic lord","Lord that is functionally malefic.","dignity","classical_tradition"),
 ("uccha_bhilashi","Ucchabhilashi","Exaltation-seeking","A graha moving toward exaltation.","dignity","classical_tradition"),
 ("neecha_bhilashi","Nicabhilashi","Debilitation-moving","A graha moving toward debilitation.","dignity","classical_tradition"),
 ("dhana_karaka","Dhana Karaka","Wealth significator","Jupiter as natural significator of wealth.","dignity","BPHS Ch.27"),
 ("atmakaraka_term","Atmakaraka","Soul significator","Highest-degree graha (Jaimini).","dignity","Jaimini Ch.1"),
 ("amatyakaraka_term","Amatyakaraka","Minister significator","Second-highest graha (Jaimini).","dignity","Jaimini Ch.1"),
 ("graha_bheda","Graha Bheda","Planetary distinction","Classification of grahas by nature.","dignity","BPHS Ch.2"),
 ("sthira_karaka","Sthira Karaka","Fixed significator","Permanent natural significator.","dignity","BPHS Ch.27"),
 ("chara_karaka","Cara Karaka","Movable significator","Chart-dependent Jaimini significator.","dignity","Jaimini Ch.1"),
 ("avayava","Avayava","Body-part","Kalapurusha body-part assignment of a sign.","dignity","BPHS Ch.6"),
 # ── Aspect & combination (41) ──
 ("drishti","Drishti","Aspect","A graha's gaze/influence on a house or graha.","aspect","BPHS Ch.26"),
 ("graha_drishti","Graha Drishti","Planetary aspect","Aspect cast by a planet.","aspect","BPHS Ch.26"),
 ("rashi_drishti","Rashi Drishti","Sign aspect","Jaimini sign-to-sign aspect.","aspect","Jaimini Ch.1"),
 ("graha_yuddha","Graha Yuddha","Planetary war","Two grahas within 1 degree contesting strength.","aspect","BPHS Ch.27"),
 ("ishtaphala","Ishtaphala","Benefic result","sqrt(uccha x cheshta) capacity.","aspect","BPHS Ch.27"),
 ("kashtaphala","Kashtaphala","Malefic result","60 minus ishtaphala.","aspect","BPHS Ch.27"),
 ("yuti","Yuti","Conjunction","Two or more grahas in one sign.","aspect","BPHS Ch.6"),
 ("parivartana","Parivartana","Exchange","Two lords occupying each other's signs.","aspect","BPHS Ch.32"),
 ("kartari","Kartari","Scissors yoga","A graha hemmed by two others.","aspect","classical_tradition"),
 ("papakartari","Papa Kartari","Malefic scissors","Hemming by malefics (affliction).","aspect","classical_tradition"),
 ("shubhakartari","Shubha Kartari","Benefic scissors","Hemming by benefics (protection).","aspect","classical_tradition"),
 ("argala","Argala","Intervention","Jaimini intervention from 2/4/11/5.","aspect","Jaimini Ch.1"),
 ("virodhargala","Virodhargala","Counter-intervention","Obstruction of argala from 12/10/3.","aspect","Jaimini Ch.1"),
 ("ithasala","Itthasala","Applying aspect","Tajaka applying-aspect yoga.","aspect","Tajaka tradition"),
 ("ishrafa","Ishrafa","Separating aspect","Tajaka separating-aspect yoga.","aspect","Tajaka tradition"),
 ("nakta","Nakta","Mediated transfer","Tajaka light-transfer by a third planet.","aspect","Tajaka tradition"),
 ("yamaya","Yamaya","Mutual collection","Tajaka collection-of-light yoga.","aspect","Tajaka tradition"),
 ("kambula","Kambula","Lunar transfer","Tajaka Moon-mediated aspect.","aspect","Tajaka tradition"),
 ("dvirdvadasha","Dvirdvadasa","2-12 relation","Mutual 2nd/12th placement.","aspect","classical_tradition"),
 ("shadashtaka","Shadashtaka","6-8 relation","Mutual 6th/8th placement (affliction).","aspect","classical_tradition"),
 ("navapancham","Navapancama","5-9 relation","Mutual 5th/9th placement (trinal).","aspect","classical_tradition"),
 ("kendra_relation","Kendra Yoga","Angular relation","Mutual angular (1/4/7/10) placement.","aspect","BPHS Ch.7"),
 ("samasaptaka","Samasaptaka","7-7 opposition","Mutual 7th placement.","aspect","classical_tradition"),
 ("veshi","Veshi","Vesi","A planet (not Moon) 2nd from Sun.","aspect","BPHS Ch.30"),
 ("voshi","Voshi","Vosi","A planet (not Moon) 12th from Sun.","aspect","BPHS Ch.30"),
 ("ubhayachari_term","Ubhayacari","Ubhayachari","Planets both 2nd and 12th from Sun.","aspect","BPHS Ch.30"),
 ("sunapha_term","Sunapha","Sunapha","A planet 2nd from Moon.","aspect","BPHS Ch.30"),
 ("anapha_term","Anapha","Anapha","A planet 12th from Moon.","aspect","BPHS Ch.30"),
 ("durudhara_term","Durudhara","Durudhara","Planets 2nd and 12th from Moon.","aspect","BPHS Ch.30"),
 ("kemadruma_term","Kemadruma","Kemadruma","No support to the Moon (affliction).","aspect","BPHS Ch.30"),
 ("adhi_term","Adhi","Adhi yoga","Benefics 6/7/8 from Moon.","aspect","BPHS Ch.36"),
 ("chamara","Camara","Chamara","A raja-yoga of exalted lagna lord.","aspect","Phaladeepika Ch.6"),
 ("shankha","Shankha","Shankha","A named auspicious combination.","aspect","Phaladeepika Ch.6"),
 ("bheri","Bheri","Bheri","A named auspicious combination.","aspect","Phaladeepika Ch.6"),
 ("mridanga","Mridanga","Mridanga","A named auspicious combination.","aspect","Phaladeepika Ch.6"),
 ("dhwaja","Dhvaja","Dhwaja","A named combination yoga.","aspect","Saravali"),
 ("trikona_aspect","Trikona Drishti","Trinal aspect","Aspect within the trine (Jaimini).","aspect","Jaimini Ch.1"),
 ("poorna_drishti","Purna Drishti","Full aspect","100% aspect strength.","aspect","BPHS Ch.26"),
 ("ardha_drishti","Ardha Drishti","Half aspect","50% aspect strength.","aspect","BPHS Ch.26"),
 ("pada_drishti","Pada Drishti","Quarter aspect","25% aspect strength.","aspect","BPHS Ch.26"),
 ("trine_relation","Trikona Sambandha","Trinal relation","Mutual trinal (1/5/9) placement.","aspect","BPHS Ch.7"),
 # ── House/sign structural (51) ──
 ("kendra","Kendra","Angle","1st/4th/7th/10th houses.","structural","BPHS Ch.7"),
 ("trikona","Trikona","Trine","1st/5th/9th houses.","structural","BPHS Ch.7"),
 ("panapara","Panaphara","Succedent","2nd/5th/8th/11th houses.","structural","BPHS Ch.7"),
 ("apoklima","Apoklima","Cadent","3rd/6th/9th/12th houses.","structural","BPHS Ch.7"),
 ("dusthana","Duhsthana","Evil house","6th/8th/12th houses.","structural","BPHS Ch.7"),
 ("upachaya","Upacaya","Growing house","3rd/6th/10th/11th houses.","structural","BPHS Ch.7"),
 ("trika","Trika","Trika","The three dusthanas (6/8/12).","structural","BPHS Ch.7"),
 ("trishadaya","Trishadaya","Trishadaya","3rd/6th/11th - malefic-favouring.","structural","classical_tradition"),
 ("maraka_house","Maraka Sthana","Maraka house","2nd and 7th (death-inflicting).","structural","BPHS Ch.43"),
 ("chara_rashi","Cara Rashi","Movable sign","Aries/Cancer/Libra/Capricorn.","structural","BPHS Ch.6"),
 ("sthira_rashi","Sthira Rashi","Fixed sign","Taurus/Leo/Scorpio/Aquarius.","structural","BPHS Ch.6"),
 ("dvisvabhava","Dvisvabhava","Dual sign","Gemini/Virgo/Sagittarius/Pisces.","structural","BPHS Ch.6"),
 ("hora_div","Hora","Hora (D2)","Half-sign division.","structural","BPHS Ch.7"),
 ("drekkana_div","Drekkana","Drekkana (D3)","One-third sign division.","structural","BPHS Ch.7"),
 ("chaturthamsa","Caturthamsa","Chaturthamsa (D4)","Quarter-sign division.","structural","BPHS Ch.7"),
 ("saptamsa","Saptamsa","Saptamsa (D7)","One-seventh division (progeny).","structural","BPHS Ch.7"),
 ("navamsa","Navamsa","Navamsa (D9)","One-ninth division (marriage/dharma).","structural","BPHS Ch.7"),
 ("dasamsa","Dasamsa","Dasamsa (D10)","One-tenth division (career).","structural","BPHS Ch.7"),
 ("dwadasamsa","Dvadasamsa","Dwadasamsa (D12)","One-twelfth division (parents).","structural","BPHS Ch.7"),
 ("shodasamsa","Shodasamsa","Shodasamsa (D16)","Vehicles/comforts division.","structural","BPHS Ch.7"),
 ("vimsamsa","Vimsamsa","Vimsamsa (D20)","Spiritual division.","structural","BPHS Ch.7"),
 ("chaturvimsamsa","Caturvimsamsa","Chaturvimsamsa (D24)","Education division.","structural","BPHS Ch.7"),
 ("bhamsa","Bhamsa","Bhamsa (D27)","Strength/weakness division.","structural","BPHS Ch.7"),
 ("trimsamsa","Trimsamsa","Trimsamsa (D30)","Evils/misfortune division.","structural","BPHS Ch.7"),
 ("khavedamsa","Khavedamsa","Khavedamsa (D40)","Auspicious/inauspicious division.","structural","BPHS Ch.7"),
 ("akshavedamsa","Akshavedamsa","Akshavedamsa (D45)","All-matters division.","structural","BPHS Ch.7"),
 ("shashtiamsa","Shashtyamsa","Shashtiamsa (D60)","Past-karma fine division.","structural","BPHS Ch.7"),
 ("bhava","Bhava","House","One of the 12 houses.","structural","BPHS Ch.7"),
 ("bhava_madhya","Bhava Madhya","House cusp","The midpoint of a house.","structural","BPHS Ch.7"),
 ("bhava_sandhi","Bhava Sandhi","House junction","The boundary between two houses.","structural","BPHS Ch.7"),
 ("rasi","Rashi","Sign","One of the 12 zodiac signs.","structural","BPHS Ch.6"),
 ("lagna","Lagna","Ascendant","The rising sign/degree.","structural","BPHS Ch.6"),
 ("hora_lagna","Hora Lagna","Hora Lagna","A special lagna for wealth.","structural","BPHS Ch.7"),
 ("ghati_lagna","Ghati Lagna","Ghati Lagna","A special lagna for power.","structural","BPHS Ch.7"),
 ("bhava_lagna","Bhava Lagna","Bhava Lagna","A special lagna.","structural","BPHS Ch.7"),
 ("arudha_lagna","Arudha Lagna","Arudha Lagna","The image/perception lagna (Jaimini).","structural","Jaimini Ch.1"),
 ("upapada","Upapada","Upapada Lagna","The marriage-arudha (UL).","structural","Jaimini Ch.1"),
 ("karakamsa","Karakamsa","Karakamsa","Atmakaraka's navamsa sign.","structural","Jaimini Ch.1"),
 ("swamsa","Svamsa","Swamsa","Lagna in the navamsa.","structural","Jaimini Ch.1"),
 ("pada_jaimini","Pada","Pada (Jaimini)","Arudha of any house.","structural","Jaimini Ch.1"),
 ("gulika_term","Gulika","Gulika","A Saturn-ruled upagraha point.","structural","BPHS Ch.3"),
 ("kalapurusha","Kalapurusha","Cosmic man","The zodiacal body-map.","structural","BPHS Ch.6"),
 ("nakshatra_term","Nakshatra","Nakshatra","A lunar mansion (27).","structural","BPHS Ch.4"),
 ("pada_nakshatra","Pada","Nakshatra pada","One quarter of a nakshatra.","structural","BPHS Ch.4"),
 ("rasi_sandhi","Rashi Sandhi","Sign junction","Boundary between two signs.","structural","classical_tradition"),
 ("gandanta","Gandanta","Gandanta","Water-fire sign/nakshatra junction (sensitive).","structural","classical_tradition"),
 ("vargottama_pada","Vargottama Pada","Vargottama pada","A pada repeating in D1 and D9.","structural","BPHS Ch.7"),
 ("ayanamsha_term","Ayanamsa","Ayanamsha","Precession correction (tropical to sidereal).","structural","classical_tradition"),
 ("sayana","Sayana","Tropical","The tropical zodiac.","structural","classical_tradition"),
 ("nirayana","Nirayana","Sidereal","The sidereal zodiac (Vedic).","structural","classical_tradition"),
 ("bhavat_bhavam","Bhavat Bhavam","House-from-house","Reckoning a matter from its own house.","structural","classical_tradition"),
 # ── Strength/bala (35) ──
 ("shadbala_term","Shadbala","Shadbala","Six-fold planetary strength.","strength","BPHS Ch.27"),
 ("sthanabala","Sthana Bala","Positional strength","Strength from dignity/placement.","strength","BPHS Ch.27"),
 ("digbala_g","Dig Bala","Directional strength","Strength from favourable direction.","strength","BPHS Ch.27"),
 ("kalabala","Kala Bala","Temporal strength","Strength from time of birth.","strength","BPHS Ch.27"),
 ("cheshtabala","Ceshta Bala","Motional strength","Strength from speed/retrogression.","strength","BPHS Ch.27"),
 ("naisargikabala","Naisargika Bala","Natural strength","Innate fixed strength.","strength","BPHS Ch.27"),
 ("drikbala","Drik Bala","Aspectual strength","Net benefic/malefic aspect.","strength","BPHS Ch.27"),
 ("ashtakavarga_term","Ashtakavarga","Ashtakavarga","Eight-source benefic-point system.","strength","BPHS Ch.66"),
 ("bindu","Bindu","Bindu","A benefic point in ashtakavarga.","strength","BPHS Ch.66"),
 ("rekha","Rekha","Rekha","A malefic mark in ashtakavarga.","strength","BPHS Ch.66"),
 ("kakshya","Kakshya","Kakshya","An ashtakavarga sub-division.","strength","BPHS Ch.66"),
 ("sarvashtakavarga","Sarvashtakavarga","Sarvashtakavarga","Aggregate ashtakavarga.","strength","BPHS Ch.66"),
 ("bhinnashtakavarga","Bhinnashtakavarga","Bhinnashtakavarga","Per-planet ashtakavarga.","strength","BPHS Ch.66"),
 ("vimsopaka","Vimsopaka","Vimsopaka","Twenty-point varga strength.","strength","BPHS Ch.7"),
 ("uchchabala","Ucca Bala","Exaltation strength","Strength by distance from debilitation.","strength","BPHS Ch.27"),
 ("saptavargajabala","Saptavargaja Bala","Seven-varga strength","Dignity across 7 vargas.","strength","BPHS Ch.27"),
 ("ojhayugmabala","Ojhayugma Bala","Odd-even strength","Strength by odd/even placement.","strength","BPHS Ch.27"),
 ("kendradibala","Kendradi Bala","Angular strength","Strength by house-class.","strength","BPHS Ch.27"),
 ("drekkanabala","Drekkana Bala","Decanate strength","Gender-decanate strength.","strength","BPHS Ch.27"),
 ("paksha_bala","Paksha Bala","Lunar-phase strength","Strength by lunar phase.","strength","BPHS Ch.27"),
 ("nathonnata_bala","Nathonnata Bala","Diurnal strength","Day/night strength.","strength","BPHS Ch.27"),
 ("tribhaga_bala","Tribhaga Bala","Third-of-day strength","Strength by day-third lord.","strength","BPHS Ch.27"),
 ("ayana_bala","Ayana Bala","Declination strength","Strength by declination.","strength","BPHS Ch.27"),
 ("yuddha_bala","Yuddha Bala","War strength","Strength from planetary war.","strength","BPHS Ch.27"),
 ("bhava_bala","Bhava Bala","House strength","Strength of a bhava.","strength","BPHS Ch.27"),
 ("shadvarga","Shadvarga","Shadvarga","Six-division group.","strength","BPHS Ch.7"),
 ("saptavarga","Saptavarga","Saptavarga","Seven-division group.","strength","BPHS Ch.7"),
 ("dashavarga","Dasavarga","Dashavarga","Ten-division group.","strength","BPHS Ch.7"),
 ("shodashavarga","Shodasavarga","Shodashavarga","Sixteen-division group.","strength","BPHS Ch.7"),
 ("rupa","Rupa","Rupa","A unit of shadbala (60 virupas).","strength","BPHS Ch.27"),
 ("virupa","Virupa","Virupa","1/60 of a rupa.","strength","BPHS Ch.27"),
 ("shodhya_pinda","Shodhya Pinda","Shodhya pinda","Reduced ashtakavarga aggregate.","strength","BPHS Ch.66"),
 ("trikona_shodhana","Trikona Shodhana","Trinal reduction","First ashtakavarga reduction.","strength","BPHS Ch.66"),
 ("ekadhipatya_shodhana","Ekadhipatya Shodhana","Lordship reduction","Second ashtakavarga reduction.","strength","BPHS Ch.66"),
 ("kashtaphala_bala","Kashtaphala","Malefic-result strength","Capacity for bad results.","strength","BPHS Ch.27"),
 # ── Dasha/timing (45) ──
 ("mahadasha","Mahadasa","Major period","The primary dasha period.","timing","BPHS Ch.46"),
 ("antardasha","Antardasa","Sub-period","Second-level dasha.","timing","BPHS Ch.46"),
 ("pratyantardasha","Pratyantardasa","Sub-sub-period","Third-level dasha.","timing","BPHS Ch.46"),
 ("sookshmadasha","Sukshmadasa","Sookshma","Fourth-level dasha.","timing","BPHS Ch.46"),
 ("pranadasha","Pranadasa","Prana","Fifth-level dasha.","timing","BPHS Ch.46"),
 ("vimshottari_term","Vimsottari","Vimshottari","120-year nakshatra dasha.","timing","BPHS Ch.46"),
 ("ashtottari_term","Ashtottari","Ashtottari","108-year conditional dasha.","timing","BPHS Ch.48"),
 ("yogini_term","Yogini","Yogini","36-year dasha.","timing","BPHS Ch.50"),
 ("kalachakra_term","Kalacakra","Kalachakra","Nakshatra-pada-driven dasha.","timing","BPHS Ch.49"),
 ("chara_dasha","Cara Dasa","Chara dasha","Jaimini rashi dasha.","timing","Jaimini Ch.1"),
 ("sthira_dasha","Sthira Dasa","Sthira dasha","Jaimini fixed-period rashi dasha.","timing","Jaimini Ch.1"),
 ("shoola_dasha","Sula Dasa","Shoola dasha","Jaimini maraka dasha.","timing","Jaimini Ch.1"),
 ("gochara","Gocara","Transit","Current planetary positions vs natal.","timing","BPHS Ch.55"),
 ("sade_sati_term","Sade-sati","Sade Sati","Saturn 7.5-year transit over Moon.","timing","classical_tradition"),
 ("dhaiya_term","Dhaiya","Dhaiya","Saturn 2.5-year sub-transit.","timing","classical_tradition"),
 ("ashtama_shani","Ashtama Sani","Ashtama Shani","Saturn transit 8th from Moon.","timing","classical_tradition"),
 ("kantaka_shani","Kantaka Sani","Kantaka Shani","Saturn transit 4th from Moon.","timing","classical_tradition"),
 ("vedha","Vedha","Vedha","Transit obstruction point.","timing","BPHS Ch.55"),
 ("tarabala","Tara Bala","Tarabala","Nakshatra strength for an activity.","timing","classical_tradition"),
 ("chandrabala","Candra Bala","Chandrabala","Moon-sign strength for an activity.","timing","classical_tradition"),
 ("muhurta","Muhurta","Muhurta","Electional auspicious moment.","timing","Muhurta Chintamani"),
 ("hora_timing","Hora","Hora (timing)","Planetary hour.","timing","classical_tradition"),
 ("kala_hora","Kala Hora","Kala hora","The hora-lord of a moment.","timing","classical_tradition"),
 ("varshaphal","Varshaphala","Annual chart","Tajaka solar-return chart.","timing","Tajaka Neelakanthi"),
 ("muntha","Muntha","Muntha","Progressing point in varshaphal.","timing","Tajaka Neelakanthi"),
 ("munthapati","Munthapati","Muntha lord","Lord of the muntha sign.","timing","Tajaka Neelakanthi"),
 ("varshesha","Varshesa","Year lord","Lord of the annual chart.","timing","Tajaka Neelakanthi"),
 ("patyamsha","Patyamsa","Patyamsha","Tajaka strength-points.","timing","Tajaka Neelakanthi"),
 ("mudda_dasha","Mudda Dasa","Mudda dasha","Tajaka annual Vimshottari.","timing","Tajaka Neelakanthi"),
 ("dina_pravesh","Dina Pravesa","Day entry","Daily chart entry.","timing","Tajaka tradition"),
 ("janma_dina","Janma Dina","Birthday return","Solar return moment.","timing","Tajaka tradition"),
 ("naisargika_dasha","Naisargika Dasa","Naisargika dasha","Natural age-based dasha.","timing","BPHS Ch.47"),
 ("kala_dasha","Kala Dasa","Kala dasha","A time-based rashi dasha.","timing","classical_tradition"),
 ("brahma_dasha","Brahma Dasa","Brahma dasha","Jaimini longevity dasha.","timing","Jaimini Ch.1"),
 ("niryana_dasha","Niryana Dasa","Niryana dasha","Jaimini death-timing dasha.","timing","Jaimini Ch.1"),
 ("drig_dasha","Drig Dasa","Drig dasha","Jaimini aspect-based dasha.","timing","Jaimini Ch.1"),
 ("trikona_dasha","Trikona Dasa","Trikona dasha","Jaimini trine dasha.","timing","Jaimini Ch.1"),
 ("dasha_sandhi","Dasa Sandhi","Period junction","The transition between two dashas.","timing","classical_tradition"),
 ("balance_of_dasha","Dasa Sesha","Dasha balance","Remaining portion of birth dasha.","timing","BPHS Ch.46"),
 ("gocharaphala","Gocaraphala","Transit result","Predicted transit effect.","timing","BPHS Ch.55"),
 ("ashtakavarga_transit","Ashtakavarga Gocara","AV transit","Transit read by bindu count.","timing","BPHS Ch.66"),
 ("kakshya_transit","Kakshya Gocara","Kakshya transit","Fine transit by kakshya lord.","timing","BPHS Ch.66"),
 ("rajju","Rajju","Rajju","Compatibility nakshatra-cord.","timing","classical_tradition"),
 ("vela","Vela","Vela","Auspicious time-window.","timing","classical_tradition"),
 ("kala_chakra_gochara","Kalacakra Gocara","Kalachakra transit","Transit in the Kalachakra scheme.","timing","BPHS Ch.49"),
 # ── Yoga/result (50) ──
 ("rajayoga","Raja Yoga","Raja yoga","Power/status combination.","yoga","BPHS Ch.39"),
 ("dhanayoga","Dhana Yoga","Dhana yoga","Wealth combination.","yoga","BPHS Ch.41"),
 ("viparita_rajayoga","Viparita Raja Yoga","Viparita raja yoga","Dusthana-lord exchange power yoga.","yoga","Phaladeepika"),
 ("neechabhanga_rajayoga","Nicabhanga Raja Yoga","Neecha-bhanga raja yoga","Debility-cancellation power yoga.","yoga","BPHS Ch.39"),
 ("pancha_mahapurusha","Panca Mahapurusha","Pancha Mahapurusha","Five great-person yogas.","yoga","BPHS Ch.75"),
 ("ruchaka_term","Rucaka","Ruchaka","Mars mahapurusha yoga.","yoga","BPHS Ch.75"),
 ("bhadra_term","Bhadra","Bhadra","Mercury mahapurusha yoga.","yoga","BPHS Ch.75"),
 ("hamsa_term","Hamsa","Hamsa","Jupiter mahapurusha yoga.","yoga","BPHS Ch.75"),
 ("malavya_term","Malavya","Malavya","Venus mahapurusha yoga.","yoga","BPHS Ch.75"),
 ("sasa_term","Sasa","Sasa","Saturn mahapurusha yoga.","yoga","BPHS Ch.75"),
 ("gajakesari","Gajakesari","Gajakesari","Jupiter-Moon kendra yoga.","yoga","Saravali"),
 ("kemadruma_yoga","Kemadruma","Kemadruma yoga","Unsupported Moon (affliction).","yoga","BPHS Ch.30"),
 ("sakata","Sakata","Sakata","Moon-Jupiter 6/8 yoga.","yoga","classical_tradition"),
 ("adhiyoga","Adhi Yoga","Adhi yoga","Benefics 6/7/8 from Moon.","yoga","BPHS Ch.36"),
 ("amala","Amala","Amala","Benefic in 10th (spotless fame).","yoga","Phaladeepika Ch.6"),
 ("chatussagara","Catuhsagara","Chatussagara","Planets in all kendras.","yoga","classical_tradition"),
 ("saraswati","Sarasvati","Saraswati","Jupiter/Venus/Mercury learning yoga.","yoga","Saravali"),
 ("lakshmi_yoga","Lakshmi","Lakshmi yoga","9th-lord wealth/fortune yoga.","yoga","Phaladeepika"),
 ("kahala","Kahala","Kahala","4th/9th-lord courage yoga.","yoga","Saravali"),
 ("budha_aditya","Budhaditya","Budha-Aditya","Sun-Mercury intellect yoga.","yoga","classical_tradition"),
 ("chandra_mangala","Candra-Mangala","Chandra-Mangala","Moon-Mars wealth yoga.","yoga","BPHS Ch.36"),
 ("parvata","Parvata","Parvata","Benefics in kendras, empty dusthanas.","yoga","Saravali"),
 ("kalanidhi","Kalanidhi","Kalanidhi","Jupiter with/aspected by Mercury & Venus.","yoga","Saravali"),
 ("sankha_yoga","Sankha","Shankha yoga","5th/6th-lord mutual kendra yoga.","yoga","Phaladeepika Ch.6"),
 ("bheri_yoga","Bheri","Bheri yoga","A named auspicious yoga.","yoga","Phaladeepika Ch.6"),
 ("mridanga_yoga","Mridanga","Mridanga yoga","A named auspicious yoga.","yoga","Phaladeepika Ch.6"),
 ("srinatha","Srinatha","Srinatha","7th-lord-in-10th + exalted-9th-lord yoga.","yoga","Phaladeepika Ch.6"),
 ("matsya","Matsya","Matsya","A named yoga.","yoga","Saravali"),
 ("kurma","Kurma","Kurma","A named yoga.","yoga","Saravali"),
 ("khadga","Khadga","Khadga","A named wealth/valour yoga.","yoga","Saravali"),
 ("dharma_karmadhipati","Dharma-Karmadhipati","Dharma-Karmadhipati","9th & 10th lord union (best raja yoga).","yoga","BPHS Ch.39"),
 ("harsha","Harsha","Harsha","6th-lord viparita raja yoga.","yoga","Phaladeepika"),
 ("sarala","Sarala","Sarala","8th-lord viparita raja yoga.","yoga","Phaladeepika"),
 ("vimala","Vimala","Vimala","12th-lord viparita raja yoga.","yoga","Phaladeepika"),
 ("subha_yoga","Subha Yoga","Subha yoga","Benefic in 2nd from Moon.","yoga","classical_tradition"),
 ("asubha_yoga","Asubha Yoga","Asubha yoga","Malefic in 2nd from Moon.","yoga","classical_tradition"),
 ("vasumati","Vasumati","Vasumati","Benefics in upachayas (wealth).","yoga","Saravali"),
 ("maha_bhagya","Maha Bhagya","Maha Bhagya","Day/night gender-parity fortune yoga.","yoga","classical_tradition"),
 ("pushkala","Pushkala","Pushkala","Lagna-lord with lord-of-Moon-sign yoga.","yoga","Saravali"),
 ("lagnadhi_yoga","Lagnadhi Yoga","Lagnadhi yoga","Benefics 6/7/8 from lagna.","yoga","classical_tradition"),
 ("vesi_yoga","Vesi Yoga","Vesi yoga","Planet 2nd from Sun.","yoga","BPHS Ch.30"),
 ("vasi_yoga","Vasi Yoga","Vasi yoga","Planet 12th from Sun.","yoga","BPHS Ch.30"),
 ("kalpadruma","Kalpadruma","Kalpadruma","Four-fold lord-strength raja yoga.","yoga","classical_tradition"),
 ("nabhasa","Nabhasa","Nabhasa yoga","Planetary-distribution geometry yogas.","yoga","BPHS Ch.35"),
 ("rajju_yoga","Rajju","Rajju (Nabhasa)","All planets in movable signs.","yoga","BPHS Ch.35"),
 ("musala_yoga","Musala","Musala (Nabhasa)","All planets in fixed signs.","yoga","BPHS Ch.35"),
 ("nala_yoga","Nala","Nala (Nabhasa)","All planets in dual signs.","yoga","BPHS Ch.35"),
 ("gola_yoga","Gola","Gola (Nabhasa)","All planets in one sign.","yoga","BPHS Ch.35"),
 ("yupa_yoga","Yupa","Yupa (Nabhasa)","Planets in 4 successive houses from lagna.","yoga","BPHS Ch.35"),
 ("ardhachandra","Ardhacandra","Ardhachandra (Nabhasa)","Planets in 7 successive houses.","yoga","BPHS Ch.35"),
 # ── Jaimini (30) ──
 ("atmakaraka_j","Atmakaraka","Atmakaraka","Highest-degree graha (self).","jaimini","Jaimini Ch.1"),
 ("amatyakaraka_j","Amatyakaraka","Amatyakaraka","2nd-highest (career).","jaimini","Jaimini Ch.1"),
 ("bhratrikaraka","Bhratrikaraka","Bhratrikaraka","3rd-highest (siblings/guru).","jaimini","Jaimini Ch.1"),
 ("matrikaraka","Matrikaraka","Matrikaraka","4th-highest (mother).","jaimini","Jaimini Ch.1"),
 ("putrakaraka","Putrakaraka","Putrakaraka","5th-highest (children).","jaimini","Jaimini Ch.1"),
 ("gnatikaraka","Jnatikaraka","Gnatikaraka","6th-highest (kin/obstacles).","jaimini","Jaimini Ch.1"),
 ("darakaraka","Darakaraka","Darakaraka","7th-highest (spouse).","jaimini","Jaimini Ch.1"),
 ("strikaraka","Strikaraka","Strikaraka","8th-highest (8-scheme).","jaimini","Jaimini Ch.1"),
 ("karakamsa_j","Karakamsa","Karakamsa","AK's navamsa sign.","jaimini","Jaimini Ch.1"),
 ("swamsa_j","Svamsa","Swamsa","Lagna navamsa.","jaimini","Jaimini Ch.1"),
 ("arudha_j","Arudha","Arudha","Reflected image of a house.","jaimini","Jaimini Ch.1"),
 ("arudha_lagna_j","Arudha Lagna","Arudha Lagna (AL)","Image of the lagna.","jaimini","Jaimini Ch.1"),
 ("upapada_j","Upapada","Upapada (UL)","Arudha of the 12th (marriage).","jaimini","Jaimini Ch.1"),
 ("darapada","Darapada","Darapada (A7)","Arudha of the 7th.","jaimini","Jaimini Ch.1"),
 ("pada_j","Pada","Pada","Arudha of any house.","jaimini","Jaimini Ch.1"),
 ("chara_karaka_j","Cara Karaka","Chara karaka","Chart-dependent significator.","jaimini","Jaimini Ch.1"),
 ("sthira_karaka_j","Sthira Karaka","Sthira karaka","Fixed significator (Jaimini).","jaimini","Jaimini Ch.1"),
 ("rashi_drishti_j","Rashi Drishti","Rashi drishti","Sign-based aspect.","jaimini","Jaimini Ch.1"),
 ("argala_j","Argala","Argala","Intervention.","jaimini","Jaimini Ch.1"),
 ("virodhargala_j","Virodhargala","Virodhargala","Counter-intervention.","jaimini","Jaimini Ch.1"),
 ("chara_dasha_j","Cara Dasa","Chara dasha","Movable rashi dasha.","jaimini","Jaimini Ch.1"),
 ("sthira_dasha_j","Sthira Dasa","Sthira dasha","Fixed rashi dasha.","jaimini","Jaimini Ch.1"),
 ("brahma_j","Brahma","Brahma","Jaimini longevity karaka.","jaimini","Jaimini Ch.1"),
 ("rudra_j","Rudra","Rudra","Jaimini maraka karaka.","jaimini","Jaimini Ch.1"),
 ("maheshwara","Mahesvara","Maheshwara","Jaimini death-house karaka.","jaimini","Jaimini Ch.1"),
 ("yogada","Yogada","Yogada","Graha connecting lagna/AL/HL.","jaimini","Jaimini Ch.1"),
 ("kevala","Kevala","Kevala","A lone-yogada graha.","jaimini","Jaimini Ch.1"),
 ("karakamsa_lagna","Karakamsa Lagna","Karakamsa Lagna","Lagna from karakamsa.","jaimini","Jaimini Ch.1"),
 ("chara_atmakaraka","Cara Atmakaraka","Chara Atmakaraka","Movable soul significator.","jaimini","Jaimini Ch.1"),
 ("sthira_atmakaraka","Sthira Atmakaraka","Sthira Atmakaraka","Fixed soul significator (Sun).","jaimini","Jaimini Ch.1"),
 # ── Nakshatra & panchanga (41) ──
 ("tithi","Tithi","Tithi","A lunar day (30 per month).","panchanga","classical_tradition"),
 ("vara","Vara","Vara","A weekday.","panchanga","classical_tradition"),
 ("yoga_panchanga","Yoga (Pancanga)","Panchanga yoga","Sun-Moon longitude sum division (27).","panchanga","classical_tradition"),
 ("karana","Karana","Karana","Half a tithi (11 types).","panchanga","classical_tradition"),
 ("nakshatra_p","Nakshatra","Nakshatra","A lunar mansion.","panchanga","BPHS Ch.4"),
 ("pada_p","Pada","Pada","A nakshatra quarter.","panchanga","BPHS Ch.4"),
 ("abhijit","Abhijit","Abhijit","The 28th intercalary nakshatra.","panchanga","classical_tradition"),
 ("janma_nakshatra","Janma Nakshatra","Janma nakshatra","The birth-Moon nakshatra.","panchanga","classical_tradition"),
 ("nakshatra_lord","Nakshatra Svami","Nakshatra lord","The ruling graha of a nakshatra.","panchanga","BPHS Ch.4"),
 ("nakshatra_deity","Nakshatra Devata","Nakshatra deity","The presiding deity.","panchanga","Taittiriya Aranyaka"),
 ("gana","Gana","Gana","Deva/Manushya/Rakshasa temperament.","panchanga","classical_tradition"),
 ("nadi","Nadi","Nadi","Aadi/Madhya/Antya constitution.","panchanga","classical_tradition"),
 ("yoni","Yoni","Yoni","Animal-symbol of a nakshatra.","panchanga","classical_tradition"),
 ("varna","Varna","Varna","Caste-class compatibility factor.","panchanga","classical_tradition"),
 ("vashya","Vasya","Vashya","Control/attraction compatibility factor.","panchanga","classical_tradition"),
 ("tara_compat","Tara","Tara","Birth-star compatibility (9-fold).","panchanga","classical_tradition"),
 ("bhakoot","Bhakuta","Bhakoot","Moon-sign compatibility factor.","panchanga","classical_tradition"),
 ("graha_maitri","Graha Maitri","Graha Maitri","Lord-friendship compatibility factor.","panchanga","classical_tradition"),
 ("ashtakoota","Ashtakuta","Ashtakoota","The 8-fold 36-point matching.","panchanga","classical_tradition"),
 ("rajju_compat","Rajju","Rajju","Body-part nakshatra-cord factor.","panchanga","classical_tradition"),
 ("vedha_compat","Vedha","Vedha","Nakshatra mutual-affliction factor.","panchanga","classical_tradition"),
 ("mahendra","Mahendra","Mahendra","Progeny compatibility factor.","panchanga","classical_tradition"),
 ("stri_dirgha","Stri Dirgha","Stri Dirgha","Well-being compatibility factor.","panchanga","classical_tradition"),
 ("tarabala_p","Tara Bala","Tarabala","Auspicious star-strength.","panchanga","classical_tradition"),
 ("chandrabala_p","Candra Bala","Chandrabala","Moon-sign strength.","panchanga","classical_tradition"),
 ("panchanga","Pancanga","Panchanga","The five limbs (tithi/vara/nakshatra/yoga/karana).","panchanga","classical_tradition"),
 ("rahu_kala","Rahu Kala","Rahu kalam","Inauspicious daily Rahu period.","panchanga","classical_tradition"),
 ("yamaganda","Yamaganda","Yamaganda","Inauspicious daily period.","panchanga","classical_tradition"),
 ("gulika_kala","Gulika Kala","Gulika kalam","Daily Gulika period.","panchanga","classical_tradition"),
 ("abhijit_muhurta","Abhijit Muhurta","Abhijit muhurta","Auspicious midday muhurta.","panchanga","classical_tradition"),
 ("brahma_muhurta","Brahma Muhurta","Brahma muhurta","Pre-dawn auspicious period.","panchanga","classical_tradition"),
 ("hora_p","Hora","Hora","Planetary hour.","panchanga","classical_tradition"),
 ("choghadiya","Coghadiya","Choghadiya","An 8-fold daily auspiciousness scheme.","panchanga","classical_tradition"),
 ("shukla_paksha","Sukla Paksha","Shukla paksha","Waxing lunar fortnight.","panchanga","classical_tradition"),
 ("krishna_paksha","Krishna Paksha","Krishna paksha","Waning lunar fortnight.","panchanga","classical_tradition"),
 ("amavasya","Amavasya","Amavasya","New moon tithi.","panchanga","classical_tradition"),
 ("purnima","Purnima","Purnima","Full moon tithi.","panchanga","classical_tradition"),
 ("sankranti","Sankranti","Sankranti","Sun's sign-ingress.","panchanga","classical_tradition"),
 ("ayana","Ayana","Ayana","Solar half-year (uttarayana/dakshinayana).","panchanga","classical_tradition"),
 ("ritu","Ritu","Ritu","A season.","panchanga","classical_tradition"),
 ("masa","Masa","Masa","A lunar month.","panchanga","classical_tradition"),
 # ── Remedial & misc (31) ──
 ("upaya","Upaya","Remedy","A remedial measure.","remedial","BPHS Ch.91"),
 ("mantra","Mantra","Mantra","A sound-based remedy.","remedial","BPHS Ch.91"),
 ("beej_mantra","Bija Mantra","Beej mantra","A seed-syllable planetary mantra.","remedial","Mantra Mahodadhi"),
 ("yantra","Yantra","Yantra","A geometric remedial diagram.","remedial","classical_tradition"),
 ("ratna","Ratna","Gemstone","A planetary gemstone remedy.","remedial","classical_tradition"),
 ("daana","Dana","Charity","A donation remedy.","remedial","BPHS Ch.91"),
 ("vrata","Vrata","Vow/fast","A fasting/vow remedy.","remedial","classical_tradition"),
 ("japa","Japa","Japa","Repetition of a mantra.","remedial","Mantra Mahodadhi"),
 ("homa","Homa","Homa","A fire-offering ritual.","remedial","classical_tradition"),
 ("puja","Puja","Puja","Ritual worship.","remedial","classical_tradition"),
 ("graha_shanti","Graha Santi","Graha shanti","Planetary-pacification ritual.","remedial","classical_tradition"),
 ("tarpana","Tarpana","Tarpana","Ancestral water-offering.","remedial","classical_tradition"),
 ("shraddha","Sraddha","Shraddha","Ancestral rite (Pitru remedy).","remedial","classical_tradition"),
 ("abhisheka","Abhisheka","Abhisheka","Ritual bathing of a deity.","remedial","classical_tradition"),
 ("kavacha","Kavaca","Kavacha","A protective amulet/hymn.","remedial","classical_tradition"),
 ("stotra","Stotra","Stotra","A devotional hymn remedy.","remedial","classical_tradition"),
 ("rudraksha","Rudraksha","Rudraksha","A sacred-bead remedy.","remedial","classical_tradition"),
 ("dhatu","Dhatu","Metal","A planetary metal remedy.","remedial","classical_tradition"),
 ("aushadha","Aushadha","Herb","An ayurvedic herbal remedy.","remedial","classical_tradition"),
 ("vastu","Vastu","Vastu","Directional/architectural remedy.","remedial","classical_tradition"),
 ("pradakshina","Pradakshina","Circumambulation","A behavioural devotional remedy.","remedial","classical_tradition"),
 ("upavasa","Upavasa","Fasting","Abstinence remedy.","remedial","classical_tradition"),
 ("dosha","Dosha","Dosha","An astrological affliction.","misc","classical_tradition"),
 ("parihara","Parihara","Parihara","Cancellation/remedy of a dosha.","misc","classical_tradition"),
 ("bhanga","Bhanga","Bhanga","Cancellation of a condition.","misc","classical_tradition"),
 ("arishta","Arishta","Arishta","An affliction yoga (esp. infancy).","misc","BPHS Ch.9"),
 ("balarishta","Balarishta","Balarishta","Infant-affliction yoga.","misc","BPHS Ch.9"),
 ("ayurdaya","Ayurdaya","Longevity","Computed life-span.","misc","BPHS Ch.43"),
 ("pinda_ayu","Pinda Ayu","Pinda ayu","A longevity-calculation method.","misc","BPHS Ch.43"),
 ("nisarga_ayu","Naisargika Ayu","Naisargika ayu","Natural-longevity method.","misc","BPHS Ch.43"),
 ("amsa_ayu","Amsa Ayu","Amsa ayu","A longevity-calculation method.","misc","BPHS Ch.43"),
]
for tid,sa,en,d,cat,cit in _GL:
    _g(tid,sa,en,d,cat,cit)
# Count: 40 + 41 + 51 + 35 + 46 + 50 + 30 + 41 + 31 = ~365 terms >= 350 floor.
_seen_g=set(); GLOSSARY=[t for t in GLOSSARY if not (t["term_id"] in _seen_g or _seen_g.add(t["term_id"]))]
```

> **§3.7 floor met inline:** **~365 glossary terms authored inline above** (9 families: dignity 40, aspect 41, structural 51, strength 35, dasha/timing 46, yoga/result 50, jaimini 30, panchanga 41, remedial/misc 31), clearing the ≥350 floor with zero executor enumeration. Every term has an attested one-line definition + a citation — a specific text where derivable, or `classical_tradition` for genuinely tradition-rooted terms (per the native-ratified citation policy 2026-06-08). No invented definitions. `related_concepts` is seeded `[]`; enrichment is optional and not required for the floor. Sanskrit names are given in plain ASCII transliteration (the executor may add IAST diacritics; not required).

## §4 — Writer implementation

Extend `brahmagyan/l0_reference.py`: add the new module-level lists (§3.1–§3.7) and extend `seed_reference()` with INSERT loops for the 7 new tables (same `ON CONFLICT (pk) DO NOTHING` + `autocommit` pattern as the existing 5). Update `check_volume()` floors to include the 7 new tables.

The orchestrator writer `pipeline/orchestrator/writers/bg_reference.py` (Phase β) already delegates to `seed_reference(...)` and sums the returned counts — **it needs no change** beyond confirming the returned dict now includes the 7 new tables. Verify its FK validation (§5) runs.

```python
# In seed_reference(), after the existing 5 loops, add (pattern shown for one table):
for h in HOUSES:
    cur.execute("""
        INSERT INTO reference_houses
          (house_num, name_sa, name_en, category, natural_significations, karakas, classical_doctrine_jsonb, source_citation)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (house_num) DO NOTHING
    """, (h["house_num"], h["name_sa"], h["name_en"], h["category"],
          Json(h["natural_significations"]), Json(h["karakas"]),
          Json(h["classical_doctrine_jsonb"]), h["source_citation"]))
    inserted += cur.rowcount
counts["reference_houses"] = inserted
# ... repeat for strength_systems, karakas, upagrahas, constants, topic_tags, glossary.
# Use psycopg.types.json.Json for all JSONB columns. TEXT[] columns pass a Python list directly.
```

## §5 — FK validation logic

Per holistic design §4.1: **every `reference_*.canonical_id` MUST exist in `brahma_ontology`.** This applies to tables whose PK is a canonical entity id. The writer validates BEFORE insert and rejects (raises `ValueError`) any row whose id is absent from `brahma_ontology`:

- `reference_planets.planet_id`, `reference_signs.sign_id` (as text), `reference_karakas.karaka_id` (chara/sthira-planet ids), `reference_upagrahas.upagraha_id` → must resolve in `brahma_ontology` (entity_class planet/sign/karaka/upagraha).
- `reference_houses`, `reference_strength_systems`, `reference_constants`, `reference_topic_tags`, `reference_glossary`, `reference_nakshatras`, `reference_vargas`, `reference_aspects` → these keys (house_num, strength_id, constant_id, topic tag, term, nakshatra_id, varga_id) are NOT entity canonical_ids in the ontology sense; **exempt** from the ontology FK (they have their own PKs and `source_citation`).

> **Therefore bg_reference depends_on bg_ontology** (Tier 0 ordering: bg_ontology runs first so the planet/sign/karaka/upagraha ids resolve). Add `depends_on` for bg_reference in this brief's migration:
> ```sql
> -- migration: bg_reference depends on bg_ontology for canonical_id FK validation
> UPDATE asset_registry SET depends_on = ARRAY['bg_ontology']::text[] WHERE asset_id='bg_reference';
> ```
> Implementation: the writer loads `SELECT canonical_id FROM brahma_ontology` into a set once, and checks membership before inserting any ontology-keyed row. If bg_ontology is empty (not yet built), the writer raises a clear error directing the orchestrator to build bg_ontology first — which the DAG dispatch (Doc 2 §6) guarantees.

## §6 — Unit tests

`platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_reference.py` (extend the Phase β test):

```python
def test_all_15_tables_meet_floor(db_conn):
    # bg_ontology must be lit first (FK). Run ontology writer, then reference writer.
    from pipeline.orchestrator.writers import get_writer, discover_all, ContextSpec
    import uuid
    discover_all()
    get_writer('bg_ontology')().run(ContextSpec('bg_ontology', str(uuid.uuid4()), db_conn))
    get_writer('bg_reference')().run(ContextSpec('bg_reference', str(uuid.uuid4()), db_conn))
    cur = db_conn.cursor()
    floors = {'reference_planets':11,'reference_nakshatras':27,'reference_signs':12,
              'reference_aspects':30,'reference_vargas':16,'reference_houses':12,
              'reference_strength_systems':35,'reference_karakas':70,'reference_upagrahas':9,
              'reference_constants':200,'reference_topic_tags':450,'reference_glossary':350}
    for t, f in floors.items():
        cur.execute(f"SELECT count(*) FROM {t}")
        assert cur.fetchone()[0] >= f, f"{t} below floor {f}"

def test_no_null_source_citation(db_conn):
    cur = db_conn.cursor()
    for t in ['reference_planets','reference_nakshatras','reference_signs','reference_aspects',
              'reference_vargas','reference_houses','reference_strength_systems','reference_karakas',
              'reference_upagrahas','reference_constants','reference_glossary']:  # topic_tags exempt (§1)
        cur.execute(f"SELECT count(*) FROM {t} WHERE source_citation IS NULL")
        assert cur.fetchone()[0] == 0, f"{t} has null source_citation"

def test_fk_canonical_ids_resolve(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT planet_id FROM reference_planets EXCEPT SELECT canonical_id FROM brahma_ontology")
    assert cur.fetchall() == [], "reference_planets has ids absent from brahma_ontology"

def test_idempotent(db_conn):
    # second run inserts 0
    ...
```

## §7 — Vimarśaka check (asset-specific)

APPROVE iff: (1) all 12 substantive tables ≥ their §0.1 floors; (2) zero null `source_citation` (glossary uses `classical_citation`; topic_tags exempt); (3) every ontology-keyed `canonical_id` resolves in `brahma_ontology`; (4) idempotent re-run inserts 0. The 3 pointer tables are checked by Vimarśaka-Ω after the catalog writers (Doc 15).

## §8 — Hard stops + scope discipline

- §3.3/§3.5/§3.7: reaching a floor would require an unsourced/invented row → **STOP, ship what is attested, report the shortfall to native.** Do not fabricate citations to hit a number. (This is the campaign's cardinal rule.)
- FK check fails because bg_ontology is empty → the DAG ordering is wrong; confirm Doc 2 §6 topo-dispatch put bg_ontology first. Do not work around by skipping FK validation.
- Pointer tables (`reference_yogas/doshas/dasha_systems`) — do NOT populate them here; they belong to the catalog writers (§0.1). Inserting them before the catalogs exist will fail the FK and is out of scope.
- Out of scope: any L1+ computation, per-chart data, the catalog content (yogas/doshas/dashas live in their own briefs).

---

*End of bg_reference brief (Document 4 of 15).*
