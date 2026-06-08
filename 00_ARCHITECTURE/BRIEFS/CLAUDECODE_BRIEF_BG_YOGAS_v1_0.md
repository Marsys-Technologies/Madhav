---
artifact: CLAUDECODE_BRIEF_BG_YOGAS_v1_0
canonical_id: L0_BG_YOGAS_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_yogas writer
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 250  # brahma_yoga_catalog rows
dependencies: [bg_ontology, bg_texts]  # embedded core needs bg_ontology; corpus supplement needs bg_texts — see §0.2
llm_cost: $0
document_number: 11 of 15
---

# bg_yogas — Writer Brief (classical yoga catalog)

> **The largest content catalog.** Each row is a NAMED classical yoga — its formation rule (structured JSON the engine can pattern-match + prose), significations, cancellation conditions, and citations. Yogas are favourable/named patterns; raw verse-rules live in `bg_rules` and cross-reference a yoga via `bg_rules.yoga_canonical_id` (holistic design §2.3). ZERO LLM — the engine pattern-matches `formation_rule_jsonb`; it does not "interpret".

## §0 — Asset summary

- **Asset ID:** `bg_yogas`. **Backing:** `brahma_yoga_catalog`. **Scope:** `global`. **Target floor:** **≥250** (design §3.9 says 250-350).
- **Source category:** embedded classical data (authored canonical core) + deterministic extraction from the ingested Saravali/BPHS/Phaladeepika corpus (the design's named sources).

### §0.1 — Cross-brief contract (same as Doc 12/13 §0.1)

Per dosha/dasha pattern: every `brahma_yoga_catalog` insert is accompanied (same transaction) by a `brahma_ontology` row (`entity_class='yoga'`, matching id) and a `reference_yogas` pointer row `(canonical_id, name_en, category)` — both `ON CONFLICT (canonical_id) DO NOTHING`, catalog row first (FK `fk_ref_yoga`). bg_yogas is the sole author of every yoga id's name, doctrine, and index.

### §0.2 — Two-source floor strategy (honest about the 250)

The ≥250 floor is reached from TWO deterministic, non-fabricating sources:

1. **Authored canonical core (~130 yogas), §3.** The yogas every acharya knows — Pancha Mahapurusha, the lunar/solar yogas, the Nabhasa families, the major Raja/Dhana/Viparita yogas, etc. — embedded inline with full doctrine. This is the Tier-1 pure-embedded pass (depends only on bg_ontology).
2. **Corpus-extracted named yogas (~120+), §3.9.** Saravali Ch.34-50 alone catalogs ~110 named yogas; BPHS Ch.30-40 and Phaladeepika Ch.6-7 add more. The writer's second pass deterministically extracts NAMED yoga definitions from the ingested `bg_texts` chunks (a yoga-name regex + the chunk that defines it → a catalog row citing that chunk). This depends on bg_texts (Tier 2).

> **Why this is not fabrication:** source 2 extracts real yogas from real ingested texts, each row `source_chunk_ids`-cited to the verse that defines it. It is the design's own §3.9 source. The writer NEVER invents a yoga. If sources 1+2 together fall short of 250, the writer reports the shortfall to native — it does NOT pad.

> **Tiering consequence:** bg_yogas runs in two phases — a Tier-1 embedded phase (immediately after bg_ontology) and a Tier-3 extraction phase (after bg_texts). The orchestrator handles this via `depends_on=['bg_ontology','bg_texts']` so the topo-sort places bg_yogas after bg_texts; the embedded core inserts first, the extraction supplement second, in one writer run. (If native prefers the core lit earlier, split into `bg_yogas` core + a `bg_yogas_extract` follow pass — but the single-writer-two-phase approach keeps one asset/one tile.)

## §1 — Schema reference (migration 176, verified)

```
brahma_yoga_catalog (
  canonical_id            TEXT PRIMARY KEY,
  name_sa                 TEXT NOT NULL,
  name_en                 TEXT NOT NULL,
  category                TEXT NOT NULL CHECK (category IN ('raja','dhana','pancha_mahapurusha','aristha','sannyasa','other')),
  formation_rule_jsonb    JSONB NOT NULL,           -- structured pattern: {requires:[{planet,house|sign|relation}], aspects:[...]}
  formation_text          TEXT NOT NULL,
  significations_jsonb    JSONB NOT NULL DEFAULT '{}',
  significations_text     TEXT NOT NULL,
  cancellation_conditions JSONB,
  classical_citations     JSONB,
  source_chunk_ids        BIGINT[] DEFAULT '{}',
  school                  TEXT NOT NULL,
  rare                    BOOLEAN NOT NULL DEFAULT false,
  computed_strength_formula TEXT,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

> `category` is constrained to 6 values. Yogas that aren't raja/dhana/PMP/aristha/sannyasa go to `'other'` (this includes Nabhasa, lunar, solar, and most named combinations). Store a finer sub-category in `significations_jsonb.subcategory` if wanted.

## §2 — Source references

| Yoga family | Source |
|---|---|
| Pancha Mahapurusha (5) | BPHS Ch.75 / Saravali Ch.27; Phaladeepika Ch.6 |
| Lunar yogas (Sunapha/Anapha/Durudhara/Kemadruma) + Chandra-adhi | BPHS Ch.30; Saravali Ch.10 |
| Solar yogas (Vesi/Vasi/Ubhayachari) | BPHS Ch.30; Saravali Ch.9 |
| Nabhasa yogas (~32 named families) | BPHS Ch.35; Saravali Ch.34-37; Brihat Jataka Ch.12 |
| Raja yogas (kendra-trikona, Dharma-Karmadhipati, neecha-bhanga, etc.) | BPHS Ch.36-40; Phaladeepika Ch.7 |
| Dhana yogas (wealth combinations) | BPHS Ch.41; Phaladeepika Ch.8 |
| Viparita Raja yogas (Harsha/Sarala/Vimala) | classical tradition; Phaladeepika |
| Named combination yogas (Gajakesari, Amala, Adhi, Chatussagara, Saraswati, Lakshmi, Kahala, ...) | Saravali; Phaladeepika; Jataka Parijata |

## §3 — Embedded classical content (authored canonical core, ~130)

Author into `platform/python-sidecar/brahmagyan/l0_yogas.py` as `YOGAS_CORE = [...]`. Representative full rows per family shown; the executor authors all named ids in each family with the same field completeness. `formation_rule_jsonb` uses a small structured grammar the L1 pattern-matcher reads.

### §3.1 — Pancha Mahapurusha (5, category=pancha_mahapurusha)

```python
YOGAS_CORE = [
  {"canonical_id":"ruchaka","name_sa":"Rucaka","name_en":"Ruchaka Yoga","category":"pancha_mahapurusha","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"planet":"mars","dignity":["own","exalted"],"house_class":"kendra"}]},
   "formation_text":"Mars in its own sign (Aries/Scorpio) or exaltation (Capricorn), placed in a kendra from lagna.",
   "significations_jsonb":{"gives":["courage","command","physical_strength","leadership","martial_success"],"subcategory":"mahapurusha"},
   "significations_text":"Bold, commanding, athletic, victorious over enemies; a leader/warrior nature.",
   "cancellation_conditions":{"weakened_if":["Mars combust","Mars aspected by malefics","Mars in dusthana from Moon"]},
   "classical_citations":[{"text_id":"bphs","chapter":75},{"text_id":"phaladeepika","chapter":6}],"rare":False,
   "computed_strength_formula":"mars_shadbala × kendra_factor"},
  {"canonical_id":"bhadra","name_sa":"Bhadra","name_en":"Bhadra Yoga","category":"pancha_mahapurusha","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"planet":"mercury","dignity":["own","exalted"],"house_class":"kendra"}]},
   "formation_text":"Mercury in own (Gemini/Virgo) or exaltation (Virgo) in a kendra from lagna.",
   "significations_jsonb":{"gives":["intelligence","eloquence","scholarship","business_acumen"],"subcategory":"mahapurusha"},
   "significations_text":"Sharp intellect, eloquent, learned, prosperous through wit and trade.",
   "cancellation_conditions":{"weakened_if":["Mercury combust","malefic aspect"]},
   "classical_citations":[{"text_id":"bphs","chapter":75}],"rare":False,"computed_strength_formula":"mercury_shadbala × kendra_factor"},
  {"canonical_id":"hamsa","name_sa":"Haṃsa","name_en":"Hamsa Yoga","category":"pancha_mahapurusha","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"planet":"jupiter","dignity":["own","exalted"],"house_class":"kendra"}]},
   "formation_text":"Jupiter in own (Sagittarius/Pisces) or exaltation (Cancer) in a kendra from lagna.",
   "significations_jsonb":{"gives":["wisdom","righteousness","respect","spiritual_inclination"],"subcategory":"mahapurusha"},
   "significations_text":"Virtuous, wise, respected, dharmic; fine features and noble conduct.",
   "cancellation_conditions":{"weakened_if":["Jupiter combust","malefic aspect"]},
   "classical_citations":[{"text_id":"bphs","chapter":75}],"rare":False,"computed_strength_formula":"jupiter_shadbala × kendra_factor"},
  {"canonical_id":"malavya","name_sa":"Mālavya","name_en":"Malavya Yoga","category":"pancha_mahapurusha","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"planet":"venus","dignity":["own","exalted"],"house_class":"kendra"}]},
   "formation_text":"Venus in own (Taurus/Libra) or exaltation (Pisces) in a kendra from lagna.",
   "significations_jsonb":{"gives":["beauty","luxury","artistic_talent","marital_happiness","wealth"],"subcategory":"mahapurusha"},
   "significations_text":"Charming, refined, comfortable life, artistic gifts, conjugal happiness.",
   "cancellation_conditions":{"weakened_if":["Venus combust","malefic aspect"]},
   "classical_citations":[{"text_id":"bphs","chapter":75}],"rare":False,"computed_strength_formula":"venus_shadbala × kendra_factor"},
  {"canonical_id":"sasa","name_sa":"Śaśa","name_en":"Sasa Yoga","category":"pancha_mahapurusha","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"planet":"saturn","dignity":["own","exalted"],"house_class":"kendra"}]},
   "formation_text":"Saturn in own (Capricorn/Aquarius) or exaltation (Libra) in a kendra from lagna.",
   "significations_jsonb":{"gives":["authority","endurance","leadership_of_masses","power"],"subcategory":"mahapurusha"},
   "significations_text":"Commanding over many, disciplined, powerful through perseverance; can be ruthless.",
   "cancellation_conditions":{"weakened_if":["Saturn combust","malefic aspect"]},
   "classical_citations":[{"text_id":"bphs","chapter":75}],"rare":False,"computed_strength_formula":"saturn_shadbala × kendra_factor"},
```

### §3.2 — Lunar & solar yogas (category=other; ~10)

```python
  {"canonical_id":"sunapha","name_sa":"Sunaphā","name_en":"Sunapha Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planet (not Sun) in 2nd from Moon"}]},
   "formation_text":"A planet other than the Sun occupies the 2nd from the Moon.","significations_jsonb":{"gives":["self_earned_wealth","intelligence","reputation"],"subcategory":"chandra_yoga"},
   "significations_text":"Self-made prosperity, good name, capable.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
  {"canonical_id":"anapha","name_sa":"Anaphā","name_en":"Anapha Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planet (not Sun) in 12th from Moon"}]},
   "formation_text":"A planet other than the Sun occupies the 12th from the Moon.","significations_jsonb":{"gives":["health","good_character","comforts","renunciation_tendency"],"subcategory":"chandra_yoga"},
   "significations_text":"Healthy, well-mannered, comfortable; can incline to detachment.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
  {"canonical_id":"durudhara","name_sa":"Durudharā","name_en":"Durudhara Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planets (not Sun) in both 2nd and 12th from Moon"}]},
   "formation_text":"Planets other than the Sun occupy BOTH the 2nd and 12th from the Moon.","significations_jsonb":{"gives":["wealth","generosity","comforts","fame"],"subcategory":"chandra_yoga"},
   "significations_text":"Wealthy, charitable, enjoys vehicles and comforts.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
  # kemadruma is the AFFLICTION counterpart — defined in bg_doshas; cross-reference, do not duplicate here.
  {"canonical_id":"vesi","name_sa":"Veśi","name_en":"Vesi Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planet (not Moon) in 2nd from Sun"}]},"formation_text":"A planet other than the Moon in the 2nd from the Sun.","significations_jsonb":{"gives":["balanced_nature","truthfulness","prosperity"],"subcategory":"surya_yoga"},"significations_text":"Just, truthful, comfortable.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
  {"canonical_id":"vasi","name_sa":"Vāsi","name_en":"Vasi Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planet (not Moon) in 12th from Sun"}]},"formation_text":"A planet other than the Moon in the 12th from the Sun.","significations_jsonb":{"gives":["skill","liberality","influence"],"subcategory":"surya_yoga"},"significations_text":"Skilful, generous, influential.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
  {"canonical_id":"ubhayachari","name_sa":"Ubhayacarī","name_en":"Ubhayachari Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planets (not Moon) in both 2nd and 12th from Sun"}]},"formation_text":"Planets other than the Moon in BOTH the 2nd and 12th from the Sun.","significations_jsonb":{"gives":["fame","wealth","eloquence","royal_favour"],"subcategory":"surya_yoga"},"significations_text":"Famous, well-spoken, prosperous, favoured by authority.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":30}],"rare":False},
```

### §3.3 — Major named combination yogas (category=raja/dhana/other; ~25)

```python
  {"canonical_id":"gajakesari","name_sa":"Gajakeśarī","name_en":"Gajakesari Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"Jupiter in a kendra (1/4/7/10) from the Moon"}]},
   "formation_text":"Jupiter in a kendra from the Moon (or both in mutual kendra), unafflicted.",
   "significations_jsonb":{"gives":["intelligence","fame","wealth","respect","longevity"],"subcategory":"named"},
   "significations_text":"Renowned, wise, prosperous, respected like an elephant-lion; resilient reputation.",
   "cancellation_conditions":{"weakened_if":["Jupiter or Moon debilitated/combust/in dusthana"]},
   "classical_citations":[{"text_id":"saravali"},{"text_id":"phaladeepika","chapter":6}],"rare":False},
  {"canonical_id":"amala","name_sa":"Amala","name_en":"Amala Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"a benefic in the 10th from lagna or Moon"}]},
   "formation_text":"Only a benefic occupies the 10th from lagna (or Moon).","significations_jsonb":{"gives":["lasting_fame","spotless_reputation","prosperity"],"subcategory":"named"},
   "significations_text":"Spotless reputation, virtuous fame, enduring honour.","cancellation_conditions":{},"classical_citations":[{"text_id":"phaladeepika","chapter":6}],"rare":False},
  {"canonical_id":"adhi_yoga","name_sa":"Adhi Yoga","name_en":"Adhi Yoga","category":"raja","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"benefics in the 6th, 7th and 8th from the Moon"}]},
   "formation_text":"Benefics (Mercury, Jupiter, Venus) occupy the 6th, 7th and 8th from the Moon.","significations_jsonb":{"gives":["leadership","wealth","health","command","royal_status"],"subcategory":"raja"},
   "significations_text":"Leader/minister/king, healthy, wealthy, commanding.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":36}],"rare":False},
  {"canonical_id":"chatussagara","name_sa":"Catuḥsāgara","name_en":"Chatussagara Yoga","category":"raja","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"planets in all four kendras (1/4/7/10)"}]},
   "formation_text":"All four kendras (1st, 4th, 7th, 10th) are occupied by planets.","significations_jsonb":{"gives":["fame_across_four_oceans","wealth","longevity","authority"],"subcategory":"raja"},
   "significations_text":"Renown to the four seas, prosperous, long-lived, commanding.","cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}],"rare":False},
  {"canonical_id":"saraswati","name_sa":"Sarasvatī","name_en":"Saraswati Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"Jupiter, Venus and Mercury in kendra/trikona/2nd, Jupiter strong"}]},
   "formation_text":"Mercury, Venus and Jupiter occupy kendras/trikonas/2nd, with Jupiter well-placed.","significations_jsonb":{"gives":["learning","eloquence","arts","fame","wealth"],"subcategory":"named"},
   "significations_text":"Gifted in arts and letters, eloquent, learned, prosperous.","cancellation_conditions":{},"classical_citations":[{"text_id":"saravali"}],"rare":False},
  {"canonical_id":"lakshmi_yoga","name_sa":"Lakṣmī","name_en":"Lakshmi Yoga","category":"dhana","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"9th lord in own/exaltation in kendra/trikona AND strong lagna lord"}]},
   "formation_text":"Lord of the 9th in own sign or exaltation in a kendra/trikona, with a strong lagna lord.","significations_jsonb":{"gives":["wealth","fortune","beauty","noble_character"],"subcategory":"dhana"},
   "significations_text":"Fortunate, wealthy, virtuous, blessed by Lakshmi.","cancellation_conditions":{},"classical_citations":[{"text_id":"phaladeepika"}],"rare":False},
  {"canonical_id":"kahala","name_sa":"Kāhala","name_en":"Kahala Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"4th and 9th lords in mutual kendra AND lagna lord strong"}]},
   "formation_text":"Lords of the 4th and 9th in mutual kendras, lagna lord strong.","significations_jsonb":{"gives":["courage","command_of_army","property"],"subcategory":"named"},
   "significations_text":"Bold, commands forces, holds lands.","cancellation_conditions":{},"classical_citations":[{"text_id":"saravali"}],"rare":False},
  # ... author the remaining named combination yogas with the same completeness:
  #   chandra_mangala (Moon+Mars → wealth/dhana), guru_mangala, budha_aditya (Sun+Mercury → intellect),
  #   parvata, kalanidhi, kusuma, sankha, bheri, mridanga, srinatha, matsya, kurma, khadga,
  #   chamara, dhwaja, trilochana, kulavardhana, gauri, vasumati, neecha_bhanga_raja_yoga,
  #   dharma_karmadhipati (9th+10th lords joined → strongest raja yoga), maha_bhagya, ...
```

### §3.4 — Nabhasa yogas (~32 named families, category=other)

The Nabhasa yogas are a fixed classical enumeration (BPHS Ch.35 / Saravali Ch.34-37): 3 Ashraya, 2 Dala, 20 Akriti, 7 Sankhya families. Author each named family with its formation pattern:

```python
  # Ashraya (3): rajju (all planets in movable signs), musala (all in fixed), nala (all in dual)
  {"canonical_id":"rajju","name_sa":"Rajju","name_en":"Rajju Yoga","category":"other","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"all_planets_in":"movable_signs"}]},"formation_text":"All planets occupy movable (chara) signs.","significations_jsonb":{"gives":["fondness_for_travel","wandering","industriousness"],"subcategory":"nabhasa_ashraya"},"significations_text":"Loves travel, restless, hard-working.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":35}],"rare":False},
  # ... musala, nala (Ashraya); gada, sakata, vihaga/pakshi, sringataka, hala, vajra, yava, kamala,
  #     vapi, yupa, sara/ishu, sakti, danda, nau/nauka, kuta, chatra, chapa/dhanus, ardhachandra,
  #     chakra, samudra (Akriti, ~20); golaka, yuga, sula, kedara, pasa, dama, vina (Sankhya, 7-by-count).
  #     Each: formation_rule_jsonb encodes the planetary-distribution geometry; all are BPHS Ch.35 / Saravali.
```

### §3.5 — Raja, Dhana, Viparita-Raja yogas (~50; category=raja/dhana/other)

```python
  {"canonical_id":"kendra_trikona_raja_yoga","name_sa":"Kendra-Trikoṇa Rāja Yoga","name_en":"Kendra-Trikona Raja Yoga","category":"raja","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"association (conjunction/aspect/exchange) of a kendra lord and a trikona lord"}]},
   "formation_text":"A lord of a kendra (1/4/7/10) and a lord of a trikona (1/5/9) associate by conjunction, mutual aspect, or exchange.",
   "significations_jsonb":{"gives":["status","power","success","prosperity"],"subcategory":"raja"},
   "significations_text":"The foundational raja yoga — rise in status, authority, success.","cancellation_conditions":{"weakened_if":["either lord debilitated/combust without bhanga"]},
   "classical_citations":[{"text_id":"bphs","chapter":39}],"rare":False},
  {"canonical_id":"vipareeta_harsha","name_sa":"Viparīta Rāja Yoga (Harṣa)","name_en":"Harsha Yoga","category":"raja","school":"parashari",
   "formation_rule_jsonb":{"requires":[{"relation":"6th lord in 6/8/12"}]},"formation_text":"Lord of the 6th placed in the 6th, 8th or 12th (dusthana exchange).","significations_jsonb":{"gives":["victory_over_enemies","health","sudden_rise"],"subcategory":"viparita_raja"},"significations_text":"Defeats enemies, robust health, unexpected gains.","cancellation_conditions":{},"classical_citations":[{"text_id":"phaladeepika"}],"rare":False},
  {"canonical_id":"vipareeta_sarala","name_sa":"Viparīta Rāja Yoga (Sarala)","name_en":"Sarala Yoga","category":"raja","school":"parashari","formation_rule_jsonb":{"requires":[{"relation":"8th lord in 6/8/12"}]},"formation_text":"Lord of the 8th in the 6th, 8th or 12th.","significations_jsonb":{"gives":["longevity","fearlessness","prosperity"],"subcategory":"viparita_raja"},"significations_text":"Long-lived, fearless, learned, prosperous.","cancellation_conditions":{},"classical_citations":[{"text_id":"phaladeepika"}],"rare":False},
  {"canonical_id":"vipareeta_vimala","name_sa":"Viparīta Rāja Yoga (Vimala)","name_en":"Vimala Yoga","category":"raja","school":"parashari","formation_rule_jsonb":{"requires":[{"relation":"12th lord in 6/8/12"}]},"formation_text":"Lord of the 12th in the 6th, 8th or 12th.","significations_jsonb":{"gives":["frugality","good_conduct","independence","happiness"],"subcategory":"viparita_raja"},"significations_text":"Thrifty, virtuous, independent, content.","cancellation_conditions":{},"classical_citations":[{"text_id":"phaladeepika"}],"rare":False},
  {"canonical_id":"dhana_yoga_2_11","name_sa":"Dhana Yoga","name_en":"Dhana Yoga (2nd-11th lords)","category":"dhana","school":"parashari","formation_rule_jsonb":{"requires":[{"relation":"association of 2nd, 5th, 9th and 11th lords"}]},"formation_text":"Association (conjunction/aspect/exchange) among the wealth-giving lords (2,5,9,11).","significations_jsonb":{"gives":["wealth","accumulation","financial_success"],"subcategory":"dhana"},"significations_text":"Accumulates wealth; strength of the combination scales the result.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs","chapter":41}],"rare":False},
  {"canonical_id":"neecha_bhanga_raja_yoga","name_sa":"Nīcabhaṅga Rāja Yoga","name_en":"Neecha Bhanga Raja Yoga","category":"raja","school":"parashari","formation_rule_jsonb":{"requires":[{"relation":"debilitated planet whose debilitation is cancelled (dispositor in kendra, exalted-planet swap, etc.)"}]},"formation_text":"A debilitated planet's debility is cancelled (neecha-bhanga) — e.g. its dispositor or the exaltation-lord of its sign is in a kendra from lagna/Moon.","significations_jsonb":{"gives":["rise_from_humble_origin","unexpected_elevation"],"subcategory":"raja"},"significations_text":"Rise from low to high — elevation after initial struggle.","cancellation_conditions":{},"classical_citations":[{"text_id":"bphs"}],"rare":False},
  # ... continue the raja/dhana/viparita families to the §3 core target.
```

> **§3 core target:** the families above (PMP 5 + lunar/solar ~6 + named ~25 + Nabhasa ~32 + raja/dhana/viparita ~50 + misc) total **~130 authored yogas**. Author every listed id with full field completeness. The elided ids in each comment are FIXED classical enumerations (Nabhasa families, viparita trio, named yogas) — mechanical transcription, not synthesis.

## §3.9 — Corpus-extraction supplement (to reach ≥250)

After the embedded core, the writer extracts additional named yogas from the ingested `bg_texts` chunks (Saravali Ch.34-50, BPHS Ch.30-40, Phaladeepika Ch.6-8):

```python
# Deterministic extraction (NO LLM):
#  1. Build a yoga-name lexicon: scan chunks for "<Name> yoga"/"<Name> Yoga"/"योग" patterns +
#     a curated allowlist of Saravali yoga names (the chapter is a yoga catalog).
#  2. For each detected named yoga NOT already in YOGAS_CORE:
#       - canonical_id = snake_case(name); name_en = "<Name> Yoga"
#       - formation_text = the sentence(s) of the defining chunk (verbatim)
#       - significations_text = the result-sentence(s) of the chunk (verbatim)
#       - formation_rule_jsonb = {"requires":[{"raw":"<defining clause>"}], "needs_structuring":true}
#         (leave structured matching to a later pass; the row is valid + cited now)
#       - source_chunk_ids = [chunk_id]; classical_citations = [{text_id, chapter, verse}]
#       - category = 'other' unless the name maps to raja/dhana
#  3. ON CONFLICT (canonical_id) DO NOTHING (don't overwrite a richer core row).
# Stop when total rows ≥ 250 OR the lexicon is exhausted. If exhausted below 250, REPORT to native.
```

> This extracts REAL yogas from REAL ingested verses, each `source_chunk_ids`-cited. `formation_rule_jsonb.needs_structuring=true` flags rows whose pattern-matching JSON a later enrichment pass (or native) refines — but the row is already floor-valid and source-cited. No fabrication.

## §4 — Writer implementation

`l0_yogas.py` (`YOGAS_CORE` + extraction fn + `seed_yogas(...)`), `pipeline/orchestrator/writers/bg_yogas.py` (`@register('bg_yogas')`). Per yoga (core and extracted): catalog row first, then `brahma_ontology` (`entity_class='yoga'`), then `reference_yogas` pointer — `ON CONFLICT (canonical_id) DO NOTHING`, JSONB via `Json(...)`. The embedded-core phase runs first; the extraction phase runs after (needs `bg_texts` lit — guaranteed by `depends_on`).

## §5 — FK validation logic

- `reference_yogas.canonical_id` FK → `brahma_yoga_catalog`: catalog-first order satisfies it.
- `brahma_ontology` `entity_class='yoga'` rows authored here (bg_ontology doesn't — Doc 5 §0.1).
- `source_chunk_ids` (extraction rows) must resolve to `classical_text_chunks` — validate before insert; skip+log any unresolved chunk id.
- **depends_on:** `UPDATE asset_registry SET depends_on = ARRAY['bg_ontology','bg_texts']::text[] WHERE asset_id='bg_yogas';` (migration 179 set only `['bg_ontology']` — this brief's migration ADDS `bg_texts`).

## §6 — Unit tests

`test_bg_yogas.py`: (1) ≥250 rows; (2) the 5 PMP present with category='pancha_mahapurusha'; (3) every row has non-empty `formation_text`, `significations_text`, `classical_citations` OR `source_chunk_ids`; (4) each id has matching ontology(`yoga`)+`reference_yogas` rows; (5) every category ∈ CHECK set; (6) extraction rows' `source_chunk_ids` resolve in `classical_text_chunks`; (7) idempotent.

## §7 — Vimarśaka check

APPROVE iff: ≥250 yogas; the 5 PMP + lunar/solar + Nabhasa families present; every row cited (citation OR chunk-id); ownership trio per id; idempotent. If the writer reports a below-250 shortfall (corpus exhausted), Vimarśaka REJECTS and the shortfall goes to native — the floor is sacred, but it is met by ship-attested, never by padding.

## §8 — Hard stops + scope discipline

- Core + extraction together fall below 250 → STOP, ship what is attested+extracted, REPORT the exact count + which sources were exhausted. Do NOT invent yogas. (Cardinal rule.)
- Extraction depends on bg_texts being lit → if the topo-sort runs bg_yogas before bg_texts, the embedded core (~130) lights and the extraction phase no-ops with a clear log; fix the `depends_on` so the full run completes. Do NOT fake the extracted rows.
- Do NOT duplicate kemadruma here (it's the affliction counterpart in bg_doshas).
- Do NOT author 'yoga' ontology rows in a separate pass (ride the catalog transaction, §0.1).
- Out of scope: per-chart yoga detection (L1 `query_yogas_by_chart_pattern`); raw verse-rules (bg_rules).

---

*End of bg_yogas brief (Document 11 of 15).*
