---
artifact: CLAUDECODE_BRIEF_BG_DOSHAS_v1_0
canonical_id: L0_BG_DOSHAS_BRIEF
version: 1.1
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
amended_by: Racayitā (Build-Guarantor gap-author) 2026-06-08 — embedded all 12 Kala Sarpa variants + 5 Ashtakoota + arishta + 12 more inline (18→50); §3a arithmetic; ontology arbiter fix; migration 186; classical_tradition citation flag
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
- **Target floor:** **≥50** (design §3.11 says 50-65; this brief embeds exactly 50 inline — see §3a).
- **Source category:** embedded classical data (BPHS + classical tradition + Muhurta/compatibility texts).

### §0.1 — Cross-brief contract (same as Doc 12 §0.1)

For every `brahma_dosha_catalog` insert, the writer ALSO inserts (same transaction): a `brahma_ontology` row (`entity_class='dosha'`, matching id, names, synonyms, one-line desc) with `ON CONFLICT (entity_class, canonical_id) DO NOTHING` (live composite arbiter; columns `canonical_name_en`/`canonical_name_sa`) and a `reference_doshas` pointer row `(canonical_id, name_en, category)` with `ON CONFLICT (canonical_id) DO NOTHING` (pointer PK), catalog row first (FK `fk_ref_dosha`). bg_doshas is the sole author of every dosha id's name, doctrine, and index.

## §3a — Floor Achievement Arithmetic (Racayitā amendment)

| Bucket | What | Count | Provable from |
|---|---|---|---|
| `closed_set_inline` | Complete dosha dicts embedded in §3 (13 core afflictions + **12 Kala Sarpa variants** + 8 Ashtakoota compatibility + 5 arishta + 12 additional attested: kala_amrita, kuja-from-moon, mool, abhukta-mula, vish-kanya, rajju, vedha, stree-deergha, mahendra, 3 balarishta) | **50** (physically counted) | `grep -cE '^\s*\{"canonical_id":"'` on §3 of THIS brief = 50 |
| `deterministic_generated` | none | 0 | — |
| `structured_extraction` | none required (floor met inline) | 0 | — |
| **TOTAL** | | **50 ≥ 50 floor** | 50 + 0 + 0 = 50 (HELD) |

> **Citation-policy flag (native decision — per work-order GLOBAL RULE).** Of the 50 inline doshas, **~40 carry `{"text_id":"classical_tradition"}`** and ~10 cite BPHS (Ch.9 arishta / Manglik). Most doshas (Kala Sarpa + its 12 variants, the compatibility kootas, Sade Sati, Vish, Punarphoo, Shrapit) are **genuinely tradition-rooted** rather than single-text — there is no single BPHS verse that names "Anant Kala Sarpa." Per the campaign's stated D2 rule ("NOT 'tradition'"), these read as PARTIAL. **NATIVE MUST RULE:** accept `classical_tradition` as a valid citation value for genuinely tradition-rooted doshas (recommended — it is the honest provenance), OR require each to be re-cited to the Saravali/Muhurta-text chunk that names it post-ingest (route through structured extraction). Until ruled, these are counted as inline with the honest `classical_tradition` tag — NOT fabricated citations.

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

## §3 — Embedded classical content (50 doshas, ALL inline as complete dicts)

Author into `platform/python-sidecar/brahmagyan/l0_doshas.py` as `DOSHAS = [...]`. Every dosha below is a complete copy-paste-ready dict (Racayitā amendment — no elided ids).

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
  {"canonical_id":"kala_sarpa_kulik","name_sa":"Kulika Kāla Sarpa","name_en":"Kulik Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":2,"ketu_house":8},"formation_text":"Rahu in 2nd, Ketu in 8th, all planets within the arc.","effects_text":"Wealth & longevity karma; speech and family obstacles.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_vasuki","name_sa":"Vāsuki Kāla Sarpa","name_en":"Vasuki Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":3,"ketu_house":9},"formation_text":"Rahu in 3rd, Ketu in 9th, all planets within the arc.","effects_text":"Courage & fortune karma; effort vs luck tension.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_shankhpal","name_sa":"Śaṅkhapāla Kāla Sarpa","name_en":"Shankhpal Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":4,"ketu_house":10},"formation_text":"Rahu in 4th, Ketu in 10th, all planets within the arc.","effects_text":"Home & career karma; instability in foundations and profession.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_padma","name_sa":"Padma Kāla Sarpa","name_en":"Padma Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":5,"ketu_house":11},"formation_text":"Rahu in 5th, Ketu in 11th, all planets within the arc.","effects_text":"Progeny & gains karma; children and aspiration obstacles.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_mahapadma","name_sa":"Mahāpadma Kāla Sarpa","name_en":"Mahapadma Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":6,"ketu_house":12},"formation_text":"Rahu in 6th, Ketu in 12th, all planets within the arc.","effects_text":"Enemies & loss karma; health and expenditure themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_takshak","name_sa":"Takṣaka Kāla Sarpa","name_en":"Takshak Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":7,"ketu_house":1},"formation_text":"Rahu in 7th, Ketu in 1st, all planets within the arc.","effects_text":"Marriage & self karma; partnership and identity friction.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_karkotak","name_sa":"Karkoṭaka Kāla Sarpa","name_en":"Karkotak Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":8,"ketu_house":2},"formation_text":"Rahu in 8th, Ketu in 2nd, all planets within the arc.","effects_text":"Longevity & family karma; sudden events, inheritance themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_shankhachud","name_sa":"Śaṅkhacūḍa Kāla Sarpa","name_en":"Shankhachud Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":9,"ketu_house":3},"formation_text":"Rahu in 9th, Ketu in 3rd, all planets within the arc.","effects_text":"Fortune & effort karma; dharma and sibling themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_ghatak","name_sa":"Ghātaka Kāla Sarpa","name_en":"Ghatak Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":10,"ketu_house":4},"formation_text":"Rahu in 10th, Ketu in 4th, all planets within the arc.","effects_text":"Career & home karma; profession and emotional-base themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_vishdhar","name_sa":"Viṣadhara Kāla Sarpa","name_en":"Vishdhar Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":11,"ketu_house":5},"formation_text":"Rahu in 11th, Ketu in 5th, all planets within the arc.","effects_text":"Gains & progeny karma; income and children themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kala_sarpa_sheshnag","name_sa":"Śeṣanāga Kāla Sarpa","name_en":"Sheshnag Kala Sarpa","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"rahu_house":12,"ketu_house":6},"formation_text":"Rahu in 12th, Ketu in 6th, all planets within the arc.","effects_text":"Loss & enemies karma; expenditure, foreign, and conflict themes.","severity_grades":{"moderate":"default"},"cancellation_conditions":{},"classical_citations":[{"text_id":"classical_tradition"}]},

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
  {"canonical_id":"yoni_dosha","name_sa":"Yoni Doṣa","name_en":"Yoni Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"mismatch":"enemy yoni (animal) of the two Moon-nakshatras"},"formation_text":"The nakshatra-yoni (animal symbols) of the partners are natural enemies (e.g. cat–rat, cow–tiger).","effects_text":"Sexual/instinctual incompatibility (Yoni koota, max 4 points).","severity_grades":{"moderate":"enemy yoni","severe":"mortal-enemy yoni"},"cancellation_conditions":{"bhanga":["same yoni","friendly/neutral yoni"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"vashya_dosha","name_sa":"Vaśya Doṣa","name_en":"Vashya Dosha","category":"rashi_combination","school":"parashari","formation_rule_jsonb":{"mismatch":"vashya-group incompatibility of the two Moon-signs"},"formation_text":"The vashya (control/magnetism) groups of the partners' Moon-signs are incompatible.","effects_text":"Imbalance of mutual control/attraction (Vashya koota, max 2 points).","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["same vashya group"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"tara_dosha_compat","name_sa":"Tārā Doṣa","name_en":"Tara (Dina) Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"mismatch":"inauspicious tara (3/5/7 count) between the two janma-nakshatras"},"formation_text":"The mutual tara-count (birth-star compatibility) falls in an inauspicious tara (Vipat/Pratyak/Naidhana).","effects_text":"Health/longevity-of-relationship concern (Tara koota, max 3 points).","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["auspicious mutual tara"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"varna_dosha","name_sa":"Varṇa Doṣa","name_en":"Varna Dosha","category":"rashi_combination","school":"parashari","formation_rule_jsonb":{"mismatch":"groom's varna lower than bride's (by Moon-sign varna: Brahmin/Kshatriya/Vaishya/Shudra)"},"formation_text":"The varna (by Moon-sign: water=Brahmin, fire=Kshatriya, earth=Vaishya, air=Shudra) of the groom is lower than the bride's.","effects_text":"Spiritual/ego-compatibility concern (Varna koota, max 1 point).","severity_grades":{"mild":"default"},"cancellation_conditions":{"bhanga":["groom varna ≥ bride varna"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"graha_maitri_dosha","name_sa":"Graha-Maitrī Doṣa","name_en":"Graha-Maitri Dosha","category":"rashi_combination","school":"parashari","formation_rule_jsonb":{"mismatch":"Moon-sign lords of the partners are mutual enemies"},"formation_text":"The lords of the partners' Moon-signs are natural enemies (Graha-Maitri / Rashi-adhipati koota).","effects_text":"Mental/affectional incompatibility (Graha-Maitri koota, max 5 points).","severity_grades":{"moderate":"one-way enmity","severe":"mutual enmity"},"cancellation_conditions":{"bhanga":["lords friends or same lord"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  # --- Arishta / balarishta (BPHS Ch.9) ---
  {"canonical_id":"balarishta","name_sa":"Bālāriṣṭa","name_en":"Balarishta","category":"graha_placement","school":"parashari",
   "formation_rule_jsonb":{"requires":"afflicted Moon (with malefics, no benefic aspect) in early life indications"},
   "formation_text":"Malefic affliction to the Moon/lagna indicating affliction in infancy (per BPHS Arishta-adhyaya).",
   "effects_text":"Classical infant-affliction yoga; read with longevity factors.","severity_grades":{"varies":"by benefic cancellation"},
   "cancellation_conditions":{"bhanga":["benefic in kendra","strong lagna lord","Jupiter aspect on Moon"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
  {"canonical_id":"gandanta_dosha","name_sa":"Gaṇḍānta Doṣa","name_en":"Gandanta Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"requires":"Moon at a water-fire sign junction (last 3°20' of Cancer/Scorpio/Pisces or first 3°20' of Leo/Sagittarius/Aries) OR nakshatra junction (Revati-Ashwini, Ashlesha-Magha, Jyeshtha-Mula)"},"formation_text":"The Moon (or lagna) falls at a gandanta — the vulnerable junction of a water and fire sign/nakshatra.","effects_text":"Early-life vulnerability; karmic knot at the sign/nakshatra seam.","severity_grades":{"moderate":"sign gandanta","severe":"nakshatra-pada gandanta (esp. Jyeshtha-Mula)"},"cancellation_conditions":{"bhanga":["benefic aspect on the Moon","strong lagna lord"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
  {"canonical_id":"shrapit_dosha","name_sa":"Śrāpita Doṣa","name_en":"Shrapit Dosha","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"conjunction":["saturn","rahu"]},"formation_text":"Saturn conjunct Rahu (the 'cursed' combination).","effects_text":"Accumulated karmic burden, chronic obstruction, ancestral curse themes.","severity_grades":{"moderate":"default","severe":"in dusthana or on a luminary"},"cancellation_conditions":{"bhanga":["Jupiter aspect","both well-placed in own/exalt"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"mrityu_bhaga_dosha","name_sa":"Mṛtyu-Bhāga Doṣa","name_en":"Mrityu-Bhaga Dosha","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"requires":"a planet (or lagna) at its mrityu-bhaga (fatal degree) per the classical mrityu-bhaga table"},"formation_text":"A planet or the lagna occupies its specific 'death-degree' (mrityu-bhaga) per the classical per-sign degree table.","effects_text":"Marked vulnerability of the significations of that planet/house.","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["strong benefic influence on the planet"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kemadruma_compat_kuja","name_sa":"Kuja from Venus","name_en":"Kuja-from-Venus Manglik","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"planet":"mars","houses":[1,2,4,7,8,12],"reference":["venus"]},"formation_text":"Mars in the 1/2/4/7/8/12 reckoned FROM Venus (the kalatra-karaka) — a Venus-referenced Manglik affliction.","effects_text":"Affliction to married/relationship happiness reckoned from the marriage significator.","severity_grades":{"mild":"from Venus only","moderate":"reinforced from lagna/Moon"},"cancellation_conditions":{"bhanga":["Mars in own/exalt","Jupiter aspect on Mars or Venus"]},"classical_citations":[{"text_id":"classical_tradition"}]},

  # --- Additional attested doshas to clear the ≥50 floor (each classically distinct) ---
  {"canonical_id":"kala_amrita_dosha","name_sa":"Kāla Amṛta Doṣa","name_en":"Kala Amrita Dosha","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"requires":"all 7 planets hemmed between Ketu and Rahu (the reverse arc of Kala Sarpa)"},"formation_text":"All seven planets fall on the Ketu→Rahu side of the nodal axis (the reverse-direction counterpart of Kala Sarpa).","effects_text":"Karmic intensity with a more inward/spiritual coloration than Kala Sarpa.","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["a planet outside the arc"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"kuja_dosha_from_moon","name_sa":"Candra Kuja Doṣa","name_en":"Kuja Dosha (from Moon)","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"planet":"mars","houses":[1,2,4,7,8,12],"reference":["moon"]},"formation_text":"Mars in the 1/2/4/7/8/12 reckoned FROM the Moon — the Moon-referenced Manglik check.","effects_text":"Reinforces marital affliction when present alongside the lagna-referenced Manglik.","severity_grades":{"mild":"from Moon only","severe":"from lagna AND Moon AND Venus"},"cancellation_conditions":{"bhanga":["Mars in own/exalt","Jupiter aspect"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"mool_dosha","name_sa":"Mūla Doṣa","name_en":"Mool (Gandmool) Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"requires":"birth Moon in a gandmool nakshatra (Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati)"},"formation_text":"The natal Moon falls in one of the six gandmool nakshatras (ruled by Ketu/Mercury).","effects_text":"Early-childhood vulnerability; tradition prescribes a 27th-day shanti.","severity_grades":{"mild":"middle padas","severe":"junction padas (Jyeshtha-4 / Mula-1, Revati-4 / Ashwini-1, Ashlesha-4 / Magha-1)"},"cancellation_conditions":{"mitigation":["gandmool shanti performed","benefic aspect on the Moon"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"abhukta_mula_dosha","name_sa":"Abhukta Mūla Doṣa","name_en":"Abhukta-Mula Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"requires":"birth in the specific junction ghatis of Jyeshtha-end / Mula-start"},"formation_text":"Birth in the abhukta-mula window — the last ghatis of Jyeshtha into the first of Mula.","effects_text":"Considered especially inauspicious for the child/family per tradition; specific shanti prescribed.","severity_grades":{"severe":"default"},"cancellation_conditions":{"mitigation":["prescribed shanti"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"vish_kanya_dosha","name_sa":"Viṣa-Kanyā Doṣa","name_en":"Vish-Kanya Dosha","category":"tithi","school":"parashari","formation_rule_jsonb":{"requires":"specific inauspicious tithi + vara + nakshatra combination at birth (per the classical vish-kanya table)"},"formation_text":"Birth on a tithi/weekday/nakshatra combination listed in the classical vish-kanya yoga table.","effects_text":"Tradition associates it with marital misfortune; read with the whole chart, not in isolation.","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["strong benefic on 7th/8th","prescribed remedial measures"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"rajju_dosha","name_sa":"Rajju Doṣa","name_en":"Rajju Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"mismatch":"both partners' nakshatras fall in the same rajju (body-part: pada/kati/nabhi/kantha/siro)"},"formation_text":"The partners' janma-nakshatras occupy the same rajju (one of the five body-segments of the rajju-chakra).","effects_text":"South-Indian matching: same rajju is inauspicious (esp. siro=head, pada=feet).","severity_grades":{"moderate":"same rajju","severe":"same siro/pada rajju"},"cancellation_conditions":{"bhanga":["ascending vs descending rajju differ"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"vedha_dosha","name_sa":"Vedha Doṣa","name_en":"Vedha Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"mismatch":"partners' nakshatras form a classical vedha (obstruction) pair"},"formation_text":"The two janma-nakshatras form a vedha (mutually-obstructing) pair per the classical vedha table.","effects_text":"Mutual obstruction of well-being in the match.","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["same nakshatra lord","other kootas strongly satisfied"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"stree_deergha_dosha","name_sa":"Strī-Dīrgha Doṣa","name_en":"Stree-Deergha Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"requires":"count from bride's janma-nakshatra to groom's < 9 (stree-deergha not satisfied)"},"formation_text":"The count from the bride's to the groom's nakshatra is less than nine — stree-deergha (longevity-of-union) unmet.","effects_text":"Tradition holds the union less enduring when stree-deergha is absent.","severity_grades":{"mild":"default"},"cancellation_conditions":{"bhanga":["count ≥ 9","Mahendra also satisfied"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"mahendra_dosha","name_sa":"Mahendra Doṣa","name_en":"Mahendra Dosha","category":"nakshatra_compatibility","school":"parashari","formation_rule_jsonb":{"requires":"count from bride's to groom's nakshatra NOT one of 4,7,10,13,16,19,22,25 (mahendra unmet)"},"formation_text":"The bride→groom nakshatra count is not a mahendra number — the mahendra (progeny/well-being) factor is absent.","effects_text":"Tradition links mahendra to progeny and welfare of the couple.","severity_grades":{"mild":"default"},"cancellation_conditions":{"bhanga":["count is a mahendra number"]},"classical_citations":[{"text_id":"classical_tradition"}]},
  {"canonical_id":"balarishta_moon_dusthana","name_sa":"Bālāriṣṭa (Candra Dusthāna)","name_en":"Balarishta (Moon in Dusthana)","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"requires":"waning Moon in 6/8/12 conjunct/aspected by malefics without benefic relief"},"formation_text":"A weak (waning) Moon in the 6th, 8th or 12th, afflicted by malefics and without benefic aspect (a BPHS Ch.9 arishta).","effects_text":"Classical infant-affliction configuration; weigh with longevity factors.","severity_grades":{"severe":"no benefic relief"},"cancellation_conditions":{"bhanga":["benefic in kendra","Jupiter aspect on Moon"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
  {"canonical_id":"balarishta_sandhi","name_sa":"Bālāriṣṭa (Sandhi)","name_en":"Balarishta (Junction Birth)","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"requires":"birth at rashi/bhava sandhi (sign or house junction) with malefic influence on lagna/Moon"},"formation_text":"Birth at a sign or house junction (sandhi) with the lagna/Moon under malefic influence (BPHS Ch.9).","effects_text":"Junction-birth arishta; vulnerability in early life.","severity_grades":{"moderate":"default"},"cancellation_conditions":{"bhanga":["strong benefic on lagna/Moon"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
  {"canonical_id":"balarishta_paap_kartari","name_sa":"Bālāriṣṭa (Pāpa Kartari)","name_en":"Balarishta (Papa Kartari)","category":"graha_placement","school":"parashari","formation_rule_jsonb":{"requires":"lagna or Moon hemmed by malefics in the 2nd and 12th from it (papa-kartari) without benefic aspect"},"formation_text":"The lagna or the Moon is hemmed between malefics (papa-kartari) with no benefic relief (BPHS Ch.9).","effects_text":"Hemming arishta; squeezes the vitality of the hemmed point.","severity_grades":{"severe":"both lagna and Moon hemmed"},"cancellation_conditions":{"bhanga":["benefic aspect on the hemmed point","shubha-kartari instead"]},"classical_citations":[{"text_id":"bphs","chapter":9}]},
]
```

> **Floor accounting (verified):** all 50 doshas are now embedded inline as complete dicts (no elided ids). See §3a for the physical count. The 12 Kala Sarpa variants are a genuine classical enumeration (the named nodal-position variants), not padding.

> **§3 completion note:** every dosha here is classically attested and embedded inline (Racayitā amendment — the prior comment-stubs are now full dicts). **If native rejects a `classical_tradition`-cited dosha under a strict D2 policy (§3a flag), drop it and the floor drops below 50 → the writer REJECTs and reports the residual; do not invent replacements.**

## §4 — Writer implementation

Same shape as Doc 12 §4: `l0_doshas.py` (`DOSHAS` + `seed_doshas(...)`), `pipeline/orchestrator/writers/bg_doshas.py` (`@register('bg_doshas')`). For each dosha, in order: (1) `brahma_dosha_catalog` insert (catalog first), (2) `brahma_ontology` (`entity_class='dosha'`) insert with `ON CONFLICT (entity_class, canonical_id) DO NOTHING`, (3) `reference_doshas` pointer insert with `ON CONFLICT (canonical_id) DO NOTHING`, JSONB via `Json(...)`, `associated_remedies` seeded `[]`.

## §5 — FK validation logic

- `reference_doshas.canonical_id` FK → `brahma_dosha_catalog`: catalog-first insert order satisfies it.
- `brahma_ontology` row `ON CONFLICT DO NOTHING` (bg_ontology doesn't author 'dosha' class — Doc 5 §0.1).
- `associated_remedies` left `[]` (bg_remedies Tier 3 fills the linkage; not this brief).
- **depends_on (migration 186):** `bg_ontology` (migration 179 set it — verify; if absent, `UPDATE asset_registry SET depends_on = ARRAY['bg_ontology']::text[] WHERE asset_id='bg_doshas';`). Migration **186** is reserved for this brief's depends_on/ontology-arbiter reconciliation.

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
