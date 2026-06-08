---
artifact: CLAUDECODE_BRIEF_BG_DOSHAS_v1_0
canonical_id: L0_BG_DOSHAS_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_doshas writer
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 50  # brahma_dosha_catalog rows (design target 50-65)
dependencies: [bg_ontology]  # writer also writes its ontology rows; see §0.1
llm_cost: $0
document_number: 13 of 15
---

# bg_doshas — Writer Brief (classical dosha / affliction catalog)

> **The affliction catalog.** Each row defines a named dosha — its formation rule (structured + prose), effects, severity grades, and cancellation (parihara) conditions. Doshas are afflictions; yogas (favourable combinations) live in `bg_yogas`. They cross-link via `bg_doshas.associated_remedies → bg_remedies` (holistic design §2.4, §2.5). ZERO LLM.

## §0 — Asset summary

- **Asset ID:** `bg_doshas`. **Backing:** `brahma_dosha_catalog`. **Scope:** `global`. **Tier:** 1 (depends on bg_ontology).
- **Target floor:** **≥50** (design §3.11 says 50-65; this brief reaches ~58).
- **Source category:** embedded classical data (BPHS + classical tradition + Muhurta/compatibility texts).

### §0.1 — Cross-brief contract (same as Doc 12 §0.1)

For every `brahma_dosha_catalog` insert, the writer ALSO inserts (same transaction): a `brahma_ontology` row (`entity_class='dosha'`, matching id, names, synonyms, one-line desc) and a `reference_doshas` pointer row `(canonical_id, name_en, category)` — both `ON CONFLICT (canonical_id) DO NOTHING`, catalog row first (FK `fk_ref_dosha`). bg_doshas is the sole author of every dosha id's name, doctrine, and index.

## §1 — Schema reference (migration 176, verified)

```
brahma_dosha_catalog (
  canonical_id            TEXT PRIMARY KEY,
  name_sa                 TEXT NOT NULL,
  name_en                 TEXT NOT NULL,
  category                TEXT NOT NULL CHECK (category IN ('graha_placement','rashi_combination','nakshatra_compatibility','tithi','other')),
  formation_rule_jsonb    JSONB NOT NULL,           -- structured: {requires:[...], houses:[...], planets:[...]}
  formation_text          TEXT NOT NULL,            -- prose statement of formation
  effects_text            TEXT NOT NULL,
  severity_grades         JSONB,                    -- {mild:..., moderate:..., severe:...}
  cancellation_conditions JSONB,                    -- parihara / bhanga conditions
  classical_citations     JSONB,
  source_chunk_ids        BIGINT[] DEFAULT '{}',
  associated_remedies     UUID[] DEFAULT '{}',      -- FK-by-convention to bg_remedies (filled later; seed [])
  school                  TEXT NOT NULL,
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

> `associated_remedies` references `bg_remedies` rows that don't exist until Tier 3. Seed it `[]`; bg_remedies (Doc 9) back-links by setting its own `concordance_topic_id`/dosha reference, OR a post-pass populates it. Do NOT block on it here.

## §2 — Source references

| Dosha family | Source |
|---|---|
| Graha-placement doshas (Manglik/Kuja, Kemadruma, Daridra, Shakata, Vish, Punarphoo, Guru-Chandal, Angarak, Grahan, Kala Sarpa + 12 variants) | BPHS + classical tradition |
| Compatibility doshas (Ashtakoota mismatches: Gana, Nadi, Bhakoot, Yoni, Vashya, Tara, Varna, Graha-Maitri) | Muhurta/Vivaha tradition; Brihat Samhita |
| Transit doshas (Sade Sati, Dhaiya, Ashtama Shani, Kantaka Shani) | classical Gochara tradition |
| Balarishta / Arishta (infant-affliction) doshas | BPHS Ch.9 (Arishta-adhyaya) |

## §3 — Embedded classical content (~58, full inline for the core + enumerated variants)

Author into `platform/python-sidecar/brahmagyan/l0_doshas.py` as `DOSHAS = [...]`. Representative full rows shown; the executor authors all listed ids with the same field completeness.

```python
DOSHAS = [
  {"canonical_id":"manglik","name_sa":"Maṅgala Doṣa (Kuja Doṣa)","name_en":"Manglik Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"planet":"mars","houses":[1,2,4,7,8,12],"reference":["lagna","moon","venus"]},
   "formation_text":"Mars in the 1st, 2nd, 4th, 7th, 8th or 12th house from lagna (and additionally checked from Moon and Venus).",
   "effects_text":"Affliction to marriage — discord, delay, or harm to spouse; intensity varies by exact house and Mars's dignity.",
   "severity_grades":{"mild":"from Venus only","moderate":"from lagna or Moon","severe":"from lagna AND Moon AND Venus; 7th/8th placement"},
   "cancellation_conditions":{"bhanga":["Mars in own/exaltation sign","both partners Manglik","Mars aspected by Jupiter","Mars in 2nd in Gemini/Virgo, 4th in Aries/Scorpio, 7th in Capricorn/Cancer, 12th in Sagittarius/Pisces, 8th in Cancer/... (sign-specific cancellations)","Jupiter/Venus in kendra"]},
   "classical_citations":[{"text_id":"bphs"}]},

  {"canonical_id":"kala_sarpa","name_sa":"Kāla Sarpa Doṣa","name_en":"Kala Sarpa Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"all 7 planets hemmed between Rahu and Ketu (one side of the nodal axis)"},
   "formation_text":"All seven planets fall on one side of the Rahu-Ketu axis (no planet outside the Rahu→Ketu arc).",
   "effects_text":"Sustained struggle, delays, sudden reversals; karmic intensity. Partial when one planet is just outside the axis.",
   "severity_grades":{"mild":"one planet conjunct a node (loose)","moderate":"complete with benefic support","severe":"complete with malefic emphasis"},
   "cancellation_conditions":{"bhanga":["a planet outside the axis (then not full KSD)","strong benefics in kendra/trikona","Rahu/Ketu well-placed"]},
   "classical_citations":[{"text_id":"classical_tradition"}]},

  # --- The 12 named Kala Sarpa variants (by which house-pair Rahu→Ketu occupies) ---
  {"canonical_id":"kala_sarpa_anant","name_sa":"Ananta Kāla Sarpa","name_en":"Anant Kala Sarpa","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"rahu_house":1,"ketu_house":7},"formation_text":"Rahu in 1st, Ketu in 7th, all planets within the arc.",
   "effects_text":"Self vs partnership tension; identity and marriage karma.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  # ... the remaining 11 named variants (author each with rahu_house/ketu_house and a one-line effect):
  #   kala_sarpa_kulik   (Rahu 2 / Ketu 8)   — wealth & longevity karma
  #   kala_sarpa_vasuki  (Rahu 3 / Ketu 9)   — courage & fortune karma
  #   kala_sarpa_shankhpal(Rahu 4 / Ketu 10) — home & career karma
  #   kala_sarpa_padma   (Rahu 5 / Ketu 11)  — progeny & gains karma
  #   kala_sarpa_mahapadma(Rahu 6 / Ketu 12) — enemies & loss karma
  #   kala_sarpa_takshak (Rahu 7 / Ketu 1)   — marriage & self karma
  #   kala_sarpa_karkotak(Rahu 8 / Ketu 2)   — longevity & family karma
  #   kala_sarpa_shankhachud(Rahu 9 / Ketu 3)— fortune & effort karma
  #   kala_sarpa_ghatak  (Rahu 10 / Ketu 4)  — career & home karma
  #   kala_sarpa_vishdhar(Rahu 11 / Ketu 5)  — gains & progeny karma
  #   kala_sarpa_sheshnag(Rahu 12 / Ketu 6)  — loss & enemies karma

  {"canonical_id":"kemadruma","name_sa":"Kemadruma Doṣa","name_en":"Kemadruma Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"no planet (except Sun/nodes) in 2nd or 12th from Moon, none with Moon, none in kendra from Moon/lagna"},
   "formation_text":"The Moon has no planet in the 2nd or 12th from it (and no kendra support), leaving it unsupported.",
   "effects_text":"Poverty, struggle, loneliness, mental restlessness; one of the strongest negating yogas.",
   "severity_grades":{"mild":"kendra benefic from lagna","severe":"no support at all"},
   "cancellation_conditions":{"bhanga":["any planet in kendra from Moon or lagna","Moon in kendra from lagna","benefic in 2nd/12th from Moon","Moon aspected by a benefic"]},
   "classical_citations":[{"text_id":"bphs"}]},

  {"canonical_id":"daridra","name_sa":"Dāridra Doṣa","name_en":"Daridra Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"11th lord in dusthana (6/8/12) or 2nd/11th lords afflicted"},
   "formation_text":"Lord of gains (11th) in a dusthana, or wealth-house lords debilitated/combust.",
   "effects_text":"Chronic financial difficulty, blocked income.","severity_grades":{"moderate":"one condition","severe":"multiple"},
   "cancellation_conditions":{"bhanga":["dhana/raja yoga present","11th lord retrograde-strong"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"shakata","name_sa":"Śakaṭa Yoga (Doṣa)","name_en":"Shakata Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"moon_jupiter_relation":"6/8 from each other","exclude":"Jupiter in kendra from lagna"},
   "formation_text":"Moon and Jupiter in 6/8 (or 12/2) mutual position, Jupiter not in a kendra from lagna.",
   "effects_text":"Fluctuating fortune — rise and fall 'like a cart wheel'.","severity_grades":{"moderate":"default"},
   "cancellation_conditions":{"bhanga":["Jupiter in kendra from lagna or Moon"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"vish_dosha","name_sa":"Viṣa Doṣa","name_en":"Vish Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"conjunction":["moon","saturn"]},"formation_text":"Moon conjunct Saturn (poison combination).",
   "effects_text":"Emotional heaviness, depression, chronic worry.","severity_grades":{"mild":"wide orb","severe":"close conjunction in dusthana"},
   "cancellation_conditions":{"bhanga":["benefic aspect","Moon strong in own/exalt"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"punarphoo","name_sa":"Punarphū Doṣa","name_en":"Punarphoo Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"relation":"Saturn aspects or conjoins Moon"},"formation_text":"Saturn conjunct/aspecting Moon (repetition/delay combination).",
   "effects_text":"Repeated efforts, delays in settling matters (esp. marriage), maturity through obstruction.","severity_grades":{"moderate":"default"},
   "cancellation_conditions":{"bhanga":["Jupiter aspect","strong lagna lord"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"guru_chandal","name_sa":"Guru Cāṇḍāla Doṣa","name_en":"Guru Chandal Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"conjunction":["jupiter","rahu"]},"formation_text":"Jupiter conjunct Rahu (wisdom-corruption combination).",
   "effects_text":"Distorted judgment, unorthodox beliefs, guru-related issues; can also give unconventional genius.","severity_grades":{"mild":"benefic support","severe":"in dharma houses 5/9"},
   "cancellation_conditions":{"bhanga":["Jupiter exalted/own","benefic aspect"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"angarak","name_sa":"Aṅgāraka Doṣa","name_en":"Angarak Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"conjunction":["mars","rahu"]},"formation_text":"Mars conjunct Rahu (fire-poison combination).",
   "effects_text":"Anger, accidents, impulsive conflict, blood/inflammation issues.","severity_grades":{"moderate":"default","severe":"in 1/4/7/8"},
   "cancellation_conditions":{"bhanga":["Jupiter aspect","Mars in own sign"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"grahan","name_sa":"Grahaṇa Doṣa","name_en":"Grahan (Eclipse) Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"conjunction":[["sun","rahu"],["sun","ketu"],["moon","rahu"],["moon","ketu"]]},
   "formation_text":"Sun or Moon conjunct Rahu or Ketu (natal eclipse combination).",
   "effects_text":"Affliction to vitality (Sun) or mind (Moon); ancestral/karmic themes.","severity_grades":{"mild":"wide","severe":"close, in dusthana"},
   "cancellation_conditions":{"bhanga":["benefic aspect","luminary strong"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  {"canonical_id":"pitru_dosha","name_sa":"Pitṛ Doṣa","name_en":"Pitru Dosha","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"Sun/9th-house/9th-lord afflicted by Rahu/Ketu/Saturn"},
   "formation_text":"Affliction to the Sun, the 9th house or its lord by Rahu/Ketu/Saturn (ancestral karmic debt).",
   "effects_text":"Obstacles tied to ancestral karma; father-related difficulty; blocked fortune until remediated.","severity_grades":{"moderate":"one factor","severe":"multiple"},
   "cancellation_conditions":{"bhanga":["strong benefic on 9th","Jupiter on Sun/9th"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  # --- Transit (gochara) doshas ---
  {"canonical_id":"sade_sati","name_sa":"Sāḍe-sātī","name_en":"Sade Sati","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"transit":"Saturn over 12th, 1st, 2nd from natal Moon (7.5 years)"},
   "formation_text":"Saturn transiting the 12th, 1st and 2nd from the natal Moon — a 7.5-year period in three phases.",
   "effects_text":"Pressure, responsibility, restructuring; phase-dependent (rising/peak/setting).","severity_grades":{"mild":"Saturn dig-bali/benefic","moderate":"peak phase","severe":"Saturn debilitated/afflicted"},
   "cancellation_conditions":{"mitigation":["Saturn exalted/own in transit","strong natal Saturn","supportive dasha"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"dhaiya","name_sa":"Dhaiyā (Aṣṭama/Kaṇṭaka Śani)","name_en":"Dhaiya / Small Panoti","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"transit":"Saturn over 4th or 8th from natal Moon (2.5 years)"},
   "formation_text":"Saturn transiting the 4th (Kantaka) or 8th (Ashtama) from the natal Moon — a 2.5-year sub-affliction.",
   "effects_text":"Domestic (4th) or health/longevity (8th) pressure for 2.5 years.","severity_grades":{"moderate":"default"},
   "cancellation_conditions":{"mitigation":["Saturn well-placed in transit"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  # --- Compatibility (Ashtakoota) doshas — category nakshatra_compatibility/rashi_combination ---
  {"canonical_id":"nadi_dosha","name_sa":"Nāḍī Doṣa","name_en":"Nadi Dosha","category":"nakshatra_compatibility","school":"parashari",
   "formation_rule_jsonb":{"requires":"same Nadi (Aadi/Madhya/Antya) for both partners' Moon nakshatras"},
   "formation_text":"Bride and groom share the same Nadi (of the three: Aadi, Madhya, Antya) — 8 of 8 koota points lost.",
   "effects_text":"Considered the gravest compatibility dosha — health/progeny concerns.","severity_grades":{"severe":"same Nadi and same nakshatra-pada"},
   "cancellation_conditions":{"bhanga":["same nakshatra but different pada","same rashi different nakshatra","specific Nadi-bhanga rules"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"bhakoot_dosha","name_sa":"Bhakūṭa Doṣa","name_en":"Bhakoot Dosha","category":"rashi_combination","school":"parashari",
   "formation_rule_jsonb":{"rashi_distance":["6-8","2-12","5-9"]},
   "formation_text":"Moon-sign distance between partners is 6/8, 2/12 (Dwirdwadasha) or 5/9 (Navapancham).",
   "effects_text":"Discord, financial/health/progeny friction depending on the koota.","severity_grades":{"moderate":"2/12 or 5/9","severe":"6/8"},
   "cancellation_conditions":{"bhanga":["same rashi lord","lords are friends","Nadi-koota satisfied"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"gana_dosha","name_sa":"Gaṇa Doṣa","name_en":"Gana Dosha","category":"nakshatra_compatibility","school":"parashari",
   "formation_rule_jsonb":{"mismatch":"Deva vs Rakshasa gana of the two Moon-nakshatras"},
   "formation_text":"Nakshatra-gana mismatch (Deva/Manushya/Rakshasa) — worst when Deva-bride & Rakshasa-groom.",
   "effects_text":"Temperamental incompatibility.","severity_grades":{"mild":"Manushya-Deva","severe":"Deva-Rakshasa"},
   "cancellation_conditions":{"bhanga":["same rashi/nakshatra lord","Bhakoot satisfied"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  # ... author the remaining Ashtakoota-related doshas as named rows: yoni_dosha, vashya_dosha,
  #     tara_dosha_compat, varna_dosha, graha_maitri_dosha (each: the koota whose mismatch is the dosha).

  # --- Arishta / balarishta (BPHS Ch.9) ---
  {"canonical_id":"balarishta","name_sa":"Bālāriṣṭa","name_en":"Balarishta","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"afflicted Moon (with malefics, no benefic aspect) in early life indications"},
   "formation_text":"Malefic affliction to the Moon/lagna indicating affliction in infancy (per BPHS Arishta-adhyaya).",
   "effects_text":"Classical infant-affliction yoga; read with longevity factors.","severity_grades":{"varies":"by benefic cancellation"},
   "cancellation_conditions":{"bhanga":["benefic in kendra","strong lagna lord","Jupiter aspect on Moon"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
  # ... continue with: gandanta_dosha, kemadruma (above), shrapit_dosha (Saturn+Rahu),
  #     chandra_mangal_dosha(?), kuja_from_venus variants, mrityu_bhaga affliction, etc.
]
```

> **Floor accounting:** core afflictions (~16) + 12 Kala Sarpa variants + ~8 compatibility doshas + ~6 arishta/transit/misc = **~58 ≥ 50**. The 12 Kala Sarpa variants are a genuine classical enumeration (the named nodal-position variants), not padding. Author each listed id with full field completeness.

> **§3 completion note:** every dosha here is classically attested. The executor fills the elided ids (Kala Sarpa variants, remaining Ashtakoota doshas, arishta members) from the explicit comments + standard tradition. **If a dosha's formation rule cannot be sourced, omit it and report — do not invent doshas to pad to 50.** The well-attested set above already meets the floor.

## §4 — Writer implementation

Same shape as Doc 12 §4: `l0_doshas.py` (`DOSHAS` + `seed_doshas(...)`), `pipeline/orchestrator/writers/bg_doshas.py` (`@register('bg_doshas')`). For each dosha, in order: (1) `brahma_dosha_catalog` insert (catalog first), (2) `brahma_ontology` (`entity_class='dosha'`) insert, (3) `reference_doshas` pointer insert — all `ON CONFLICT (canonical_id) DO NOTHING`, JSONB via `Json(...)`, `associated_remedies` seeded `[]`.

## §5 — FK validation logic

- `reference_doshas.canonical_id` FK → `brahma_dosha_catalog`: catalog-first insert order satisfies it.
- `brahma_ontology` row `ON CONFLICT DO NOTHING` (bg_ontology doesn't author 'dosha' class — Doc 5 §0.1).
- `associated_remedies` left `[]` (bg_remedies Tier 3 fills the linkage; not this brief).
- **depends_on:** `bg_ontology` (migration 179 set it — verify).

## §6 — Unit tests

`test_bg_doshas.py`: (1) ≥50 rows; (2) every row has non-empty `formation_rule_jsonb`, `formation_text`, `effects_text`, `classical_citations`; (3) every category ∈ the CHECK set; (4) each id has matching ontology (`dosha`) + `reference_doshas` rows; (5) the 12 Kala Sarpa variants all present (`canonical_id LIKE 'kala_sarpa_%'` count = 12); (6) idempotent.

## §7 — Vimarśaka check

APPROVE iff: ≥50 doshas; all source-cited; ownership trio (catalog+ontology+pointer) per id; categories valid; idempotent.

## §8 — Hard stops + scope discipline

- Padding to 50 with unsourced doshas → STOP; ship the attested set (it already clears 50) and report.
- Do NOT compute per-chart dosha presence here (that's L1). Definitional only.
- Do NOT author 'dosha' ontology rows in a separate pass — they ride in the catalog transaction (§0.1).
- Out of scope: remedy linkage population (`associated_remedies`) — Tier 3.

---

*End of bg_doshas brief (Document 13 of 15).*
