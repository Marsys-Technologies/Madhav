---
artifact: L0_BRAHMAGYAN_HOLISTIC_DESIGN
canonical_id: L0_BRAHMAGYAN_HOLISTIC_DESIGN
version: 1.1
status: CURRENT
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE (multi-session execution)
native: Abhisek Mohanty
supersedes: implicit prior structure documented in L0FR_SEALED v1.0 + BRAHMA_L0_FOUNDATION_REBUILD v1.2
v1.1_changes:
  - REMOVED all LLM use from L0 construction (native decision 2026-06-08)
  - Embeddings (Vertex AI text-multilingual-embedding-002) PRESERVED as deterministic transform
  - All synonym discovery, topic-tag classification, rule extraction, remedy scaffolding, concordance stance generation, chapter summarization → pure Python / native authoring
  - Row-count targets revised downward 30-50% on content assets (see §3 per-asset deltas)
  - LLM cost budget: $0 (was $150-300 in v1.0)
  - Provenance simplified: no derived_by=llm_*, no llm_prompt_hash, no temperature concerns; every row has Python writer + source citation
  - bg_concordance becomes slow-grow (native-authored per topic over time) rather than batch-populate
locked_decisions:
  - ZERO LLM use anywhere in L0 construction (embeddings as deterministic transform are the only Vertex AI call permitted)
  - bg_reference uses many specialized tables (per concept type); ~15-20 tables
  - All 12 assets locked in this design pass; some seeded thin, grow per writer
  - bg_text_index is a measurement metric, not a separate data store; retrieval tools point at bg_texts
  - bg_ephemeris stays 1900-2150 single-ayanamsha; no expansion
  - Don't break existing structure; enhance/tweak only
---

# L0 Brahma Jñāna — Holistic Design v1.0

## §0 — Mission

L0 is the **classical knowledge foundation** of the entire instrument. It is **global** (not per-chart) — every chart in the system reads from L0. It must be:

- **Comprehensive** — every astrological concept finds a place
- **Consistent** — no duplication, no conflict between assets
- **High-integrity** — every row source-cited, every cross-reference resolvable
- **Maximally retrievable** — code optimized for fast, structured access from L1+ and retrieval adapters
- **Reproducibly built** — the entire layer can be deleted and rebuilt deterministically by the orchestrator

L0 is sealed (L0FR_SEALED_v1_0.md) but only partially populated. This design enriches it to its full intended state. After this design is built, native triggers a clean rebuild as the proof of integrity.

## §1 — Locked Asset Registry — 12 L0 assets

| # | sort | Asset ID | Sanskrit | English | Layer purpose | Backing | Status |
|---|------|----------|----------|---------|---------------|---------|--------|
| 1 | 1 | `bg_ephemeris` | Graha-sphuṭa | Ephemeris | Raw astronomical positions | `ephemeris_daily` | EXISTING — extend date range |
| 2 | 2 | `bg_reference` | Sāraṇī | Reference Library | Structured properties of every concept | 15-20 typed tables | EXISTING — massively expand |
| 3 | 3 | `bg_texts` | Śāstrapāṭha | Classical Texts | Verse chunks from classical texts | `classical_text_chunks` | EXISTING — ingest 10 more texts |
| 4 | 4 | `bg_ontology` | Nāmasaṃgraha | Ontology | Names + synonyms + class typing | `brahma_ontology` | EXISTING — expand vocabulary |
| 5 | 5 | `bg_text_index` | Śabdakośa | Text Index | **Measurement** of retrieval index quality | `classical_text_chunks` (filtered) | EXISTING — fix metric |
| 6 | 6 | `bg_rules` | Sūtravālī | Rule Base | Extracted classical rules with antecedent/predicate | `sutravali_rules` | EXISTING — expand 5-8× |
| 7 | 7 | `bg_remedies` | Upāya-kośa | Remedy Corpus | Classical remedies (mantra/yantra/gem/etc.) | `brahma_remedy_corpus` | EXISTING — expand 10× |
| 8 | 8 | `bg_concordance` | Samanvaya | Concordance | Cross-school agreement/divergence per topic | `classical_attributions` | DORMANT — populate |
| 9 | 9 | `bg_yogas` | Yoga-saṅgraha | Yoga Catalog | Classical yoga definitions | `brahma_yoga_catalog` (NEW) | NEW |
| 10 | 10 | `bg_dasha_systems` | Daśā-paddhati | Dasha Systems | Dasha system definitions + rules | `brahma_dasha_systems` (NEW) | NEW |
| 11 | 11 | `bg_doshas` | Doṣa-kośa | Dosha Catalog | Classical dosha definitions | `brahma_dosha_catalog` (NEW) | NEW |
| 12 | 12 | `bg_compendium_index` | Anukrama | Compendium Index | Master cross-reference index | `brahma_compendium_index` (NEW) | NEW |

**Renamed concepts** (these were ambiguous before; now sharpened):
- `bg_text_index` is now a **measurement asset** — its count reflects retrieval index health, not data volume
- All retrieval tools point at `bg_texts` (the data) via embedding/tsvector columns; never at `bg_text_index`

## §2 — Architectural separation rules (no duplication, no conflict)

The cardinal rule preventing duplication: **each fact lives in exactly one table.** When concept X has property Y, it lives in `reference_X`; when concept X has names/synonyms, it lives in `brahma_ontology`; when concept X is the antecedent of a classical rule, the rule (not X) lives in `sutravali_rules` and references X via canonical_id.

### §2.1 — bg_reference vs bg_ontology (THE clean line)

| Concern | bg_reference | bg_ontology |
|---|---|---|
| Answers | "What are the properties/attributes?" | "What names refer to this entity?" |
| Schema | Typed columns per concept (e.g. `exaltation_sign INT, dasha_years NUMERIC`) | Generic shape: (entity_class, canonical_id, name_en, name_sa, synonyms[], one_line_description) |
| Rule | All classical doctrinal data | Identity resolution only |
| When in doubt | Property data → reference | Name/synonym → ontology |

**Ontology's `description` field is restricted to ONE LINE for disambiguation purposes only** (e.g. "the planet Saturn" vs "the asteroid Saturn"). All doctrinal description goes to reference tables.

### §2.2 — bg_texts vs bg_text_index (FIXED)

`bg_text_index` no longer counts chunks. Its new `count_sql`:

```sql
-- bg_text_index NEW count_sql: number of distinct retrieval-quality topic tags
SELECT count(DISTINCT topic_tag) AS count
FROM classical_text_chunks
WHERE embedding IS NOT NULL
  AND tsvector IS NOT NULL
  AND topic_tag IS NOT NULL
```

This measures retrieval index health — how many distinct topics the index can disambiguate. Realistic floor: 400-600 topic tags after full corpus ingestion. **All retrieval tools point at `classical_text_chunks` via `bg_texts`**; `bg_text_index` exists as a measurement-only asset surfaced in cockpit.

Schema change required: add `topic_tag TEXT` column to `classical_text_chunks` (set by the ingest writer using Gemini Flash to classify each chunk into one of ~500 canonical topic tags, e.g. "saturn_in_houses", "marriage_indicators_7th", "vimshottari_dasha_rules", etc.). The topic tag set itself lives in a new mini-reference table `reference_topic_tags` (under bg_reference).

### §2.3 — bg_yogas vs bg_rules

Yogas are **named patterns** (Gajakesari = "Jupiter in kendra from Moon"). Rules are **extracted classical statements** (any verse-form prediction). 

- `bg_yogas` is the **catalog**: each yoga has a definition (the pattern) + significations (what it produces) + classical citations
- `bg_rules` is **extracted text**: each rule is a templated rule from a specific verse with antecedent/predicate/prediction

When a classical text describes a yoga in a verse, the verse extraction produces a `bg_rules` row, AND the yoga itself (as a named concept) is also a `bg_yogas` row. They cross-reference via `bg_rules.yoga_canonical_id` → `bg_yogas.canonical_id`. No duplicated data; the rule cites the yoga by ID.

### §2.4 — bg_doshas vs bg_yogas

Doshas are afflictions (Manglik, Kala-sarpa, Kemadruma, Pitru, etc.). Yogas are favorable combinations (Raja, Dhana, Pancha-Maha-Purusha, etc.). Some traditions class doshas as a subset of yogas (negative yogas); we keep them separate for retrieval clarity. A dosha row in `bg_doshas` MAY reference a yoga row in `bg_yogas` via `inverse_yoga_id` if there's a known counterpart, but the two tables are distinct.

### §2.5 — bg_remedies vs bg_concordance

Remedies are **prescriptions** for an affliction or goal. Concordance is **cross-school agreement** on a topic. A remedy may have a concordance row (e.g. "Manglik dosha remedy" — BPHS says X, Phaladeepika says Y, KP says Z); the remedies live in `bg_remedies`, the school-level consensus/divergence in `bg_concordance`. Concordance refers to remedies via `remedy_id[]`; remedies reference concordance via `concordance_topic_id`. Bidirectional cross-link, no data duplicated.

### §2.6 — bg_dasha_systems vs everything else

Dasha system definitions (period lengths, sequence rules, computation method) live here. Per-chart dasha computations live at L1 `ga_dashas`. Classical rule statements about a dasha (e.g. "during Saturn dasha if Saturn is debilitated, X happens") live in `bg_rules` with `dasha_system_id` cross-reference. No overlap.

### §2.7 — bg_compendium_index — what makes it different

This is a **search-acceleration meta-asset**. For every text in `bg_texts`, it indexes:
- Topic → text → chapter → verse range
- Concept → all chunks mentioning it (across all texts)
- Cross-text concept agreement scores (pre-computed from concordance)
- Chapter summaries (LLM-generated, native-reviewed, source-cited)

Query "where does BPHS cover Saturn's effects?" hits `bg_compendium_index` and returns chapter-verse pointers; user then fetches the actual chunks via `bg_texts`. Eliminates whole-corpus scans. Realistic size: ~3,000-5,000 index rows.

## §3 — Per-asset detailed design

### §3.1 — bg_ephemeris (locked, no change)

- **Date range:** 1900-01-01 to 2150-12-31 (~91,500 days)
- **Bodies:** 9 grahas (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu)
- **Single ayanamsha:** Lahiri (no Raman/KP-Old/Yukteshwar/Surya-Siddhanta — explicitly rejected)
- **Floor:** ~825,000 rows (current state is correct)
- **Backing:** `ephemeris_daily` (existing)
- **Writer:** existing `l0_ephemeris.py` (no change needed)
- **Action this design:** none beyond verifying date range coverage on rebuild

### §3.2 — bg_reference (holy grail; 15 specialized tables)

The structural model: each concept class gets its own normalized table, all linked to `brahma_ontology` via canonical_id foreign keys.

| Table | Purpose | Realistic rows | Source |
|---|---|---|---|
| `reference_planets` | 9 grahas + 2 nodes — exaltation, debilitation, mooltrikona, friendships, karakas, dasha years, aspects, dignities | 11 | BPHS Ch.3, 4, 26 |
| `reference_nakshatras` | 27 nakshatras — deity, ruler, pada lords, nature, guna, padas, animal, gana | 27 | BPHS Ch.4, Taittiriya |
| `reference_signs` | 12 zodiac signs — element, mode, lord, exaltation graha, mooltrikona graha, debilitation, gender, body part, direction, color | 12 | BPHS Ch.6 |
| `reference_houses` | 12 bhavas — full karakas, lordship doctrine, classical significations across schools | 12 | BPHS Ch.7, Phaladeepika Ch.4 |
| `reference_aspects` | All aspect rules — natural (planet → houses), graha drishti table, sign-aspect (Jaimini) | 50-100 | BPHS Ch.26 |
| `reference_vargas` | 16 shodasha vargas — divisor, computation rule, significations, classical use | 16 | BPHS Ch.7 |
| `reference_strength_systems` (NEW) | Shadbala 6 + Ashtakavarga + Bhava-bala — formulas, max values, classical interpretation | 30-50 | BPHS Ch.27 |
| `reference_karakas` (NEW) | Sthira karakas (per house, per concept) + Chara karakas (Jaimini Atma/Amatya/etc.) | 60-100 | BPHS Ch.27, Jaimini Ch.1 |
| `reference_yogas` (NEW — see also bg_yogas) | Index/summary of every yoga; full data in bg_yogas | 200+ rows = pointers | derived from bg_yogas |
| `reference_doshas` (NEW — pointer to bg_doshas) | Index of every dosha; full data in bg_doshas | 50+ pointers | derived from bg_doshas |
| `reference_upagrahas` (NEW) | Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indra-chapa, Upaketu + computation rules | 8-11 | BPHS Ch.3 |
| `reference_dasha_systems` (NEW — pointer to bg_dasha_systems) | Index of every dasha system; full data in bg_dasha_systems | 15+ pointers | derived from bg_dasha_systems |
| `reference_constants` (NEW) | All numerical constants (vimshopaka points, ashtakavarga bindus, shadbala maxes, ayanamsha values per year, etc.) | 200-500 | BPHS various |
| `reference_topic_tags` (NEW) | Canonical topic tag vocabulary for text classification | 400-600 | Authored from text corpus |
| `reference_glossary` (NEW) | Technical Jyotish terms with classical definitions (distinct from ontology synonyms) | 300-500 | Multiple texts |

**Total realistic rows: ~1,500-2,500** across 15 specialized tables. The count_sql for `bg_reference` sums them all.

**Foreign-key discipline:** every `reference_*` row's `canonical_id` field MUST exist in `brahma_ontology`. Writers enforce this. Validation runs in `parity_check.ts`.

**Code work:**
- Extend `l0_reference.py` to cover all 15 tables (currently only handles 5)
- Author 10 new seed datasets — pure Python data (no LLM needed for properties; LLM-assisted curation acceptable for description text but with verification gate)
- Migration: 5 existing tables + 10 new = add CREATE TABLE statements
- Update `count_sql` to `SELECT (SELECT count(*) FROM reference_planets) + ... + (SELECT count(*) FROM reference_glossary) AS count`

### §3.3 — bg_texts (ingest all 15 source-data texts)

Current: 5 texts, 8,432 chunks. Target: 15 texts per `L0FR_SOURCE_DATA_v1_0.md` §3, ~14,500 chunks.

| # | Text | Tier | Manual upload? | Expected chunks |
|---|---|---|---|---|
| 1 | BPHS | 1 | NO | ~2,100 ✓ (have) |
| 2 | Phaladeepika | 1 | NO | ~640 ✓ (have) |
| 3 | Jataka Parijata | 1 | NO | ~1,000 ✓ (have) |
| 4 | Uttara Kalamrita | 1 | NO | ~340 ✓ (have) |
| 5 | Jaimini Sutram (in BPHS edition) | 1 | NO | ~200 ✓ (have) |
| 6 | Brihat Jataka (Varahamihira) | 1 | NO | ~700 NEW |
| 7 | Saravali (Kalyana Varma) | 1 | NO | ~1,800 NEW |
| 8 | Hora Sara (Prithuyasas) | 1 | NO | ~400 NEW |
| 9 | Sarvartha Chintamani | 2 | NO | ~600 NEW |
| 10 | Brihat Samhita | 2 | NO | ~2,000 NEW |
| 11 | Tajaka Neelakanthi | 2 | MANUAL | ~400 NEW |
| 12 | Yavana Jataka | 3 | MANUAL | ~600 NEW |
| 13 | Bhrigu Samhita (extracts) | 3 | MANUAL | ~300 NEW |
| 14 | Muhurta Chintamani | 3 | NO | ~700 NEW |
| 15 | Lal Kitab | 3 | NO | ~700 NEW |

**Total target: ~14,500 chunks.**

**Schema addition:** add `topic_tag TEXT` column to `classical_text_chunks`. Ingest writer (extended) classifies each chunk into one of ~500 canonical topic tags using Gemini Flash with `temperature=0` + canonical prompt + result verified against `reference_topic_tags`.

**Code work:**
- Author or extend `l0_texts_ingest.py` to handle the 10 new texts (already has the architecture per Stream C; just add new text entries to TEXTS array + run delta-ingest)
- Author topic_tag classifier with deterministic LLM call (temperature=0, fixed prompt, result must match a canonical tag in `reference_topic_tags` or row goes to review queue)
- Migration: ALTER TABLE classical_text_chunks ADD COLUMN topic_tag TEXT
- Manual uploads for texts 11/12/13: native uploads PDFs to GCS; writer detects + ingests

### §3.4 — bg_ontology (significantly expanded)

Current: 150 entries (9 grahas + 2 nodes + ASC + 27 nakshatras + 12 signs + ~99 other). Target: ~700-1,000 entries.

**New entity classes to add:**

| Entity class | Approximate count | Examples |
|---|---|---|
| `planet` (existing) | 11 | Sun, Moon, ..., Rahu, Ketu |
| `nakshatra` (existing) | 27 | Ashwini ... Revati |
| `sign` (existing) | 12 | Aries ... Pisces |
| `house` (existing) | 12 | 1st through 12th |
| `dasha_system` (existing — promote) | 15-20 | Vimshottari, Yogini, Chara, Ashtottari, Kalachakra, Shoola, etc. |
| `yoga` (NEW) | 200-300 | Gajakesari, Raja, Dhana, Pancha-Maha-Purusha (5), Adhi, Subha, Asubha, etc. |
| `dosha` (NEW) | 50-80 | Manglik, Kala-sarpa, Kemadruma, Pitru, Gana, Nadi, Bhakoot, etc. |
| `karaka` (NEW) | 60-100 | Sthira-karakas per house + Chara-karakas per Jaimini |
| `upagraha` (NEW) | 8-11 | Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indra-chapa, Upaketu |
| `domain` (existing — expand) | 30-50 | career, marriage, health + finer subdomains |
| `concept` (existing — expand) | 100-200 | Drishti types, Vargas, Bhava, Hora, dignities, etc. |
| `aspect_type` (NEW) | 10-15 | parashari_7th, mars_4th, mars_8th, jupiter_5th, jupiter_9th, saturn_3rd, saturn_10th, jaimini_sign_aspects, KP-sub-lord, etc. |
| `remedy_type` (NEW) | 10-15 | mantra, yantra, gemstone, charity, vrata, puja, fasting, tantric, ayurvedic, vastu, behavioral |
| `school` (NEW) | 6-10 | parashari, jaimini, kp, tajaka, lal-kitab, nadi, etc. |
| `text` (NEW) | 15 | BPHS, Phaladeepika, ... (mirror of bg_texts identity) |

**Total realistic: ~700-1,000 ontology entries.**

**Cardinal rule reinforced:** ontology stores ONLY name + synonyms + one_line_description. ALL doctrinal/property data lives in `bg_reference` typed tables.

**Code work:**
- Extend `l0_ontology.py` ENTITIES list with new classes (pure Python data; LLM-assisted for synonym discovery only with deterministic verification)
- LLM use: for each new entity, prompt "what are all the Sanskrit/transliteration/regional synonyms for X?" with temperature=0; the LLM result is verified by checking each synonym appears in at least one `classical_text_chunks` row (deterministic grounding gate)

### §3.5 — bg_text_index (re-defined as measurement)

See §2.2 for the fix. Realistic floor: 400-600 distinct topic tags once corpus ingestion completes.

**Code work:**
- Update `count_sql` in asset_registry migration
- Author `reference_topic_tags` seed table
- Add `topic_tag` column to `classical_text_chunks` via migration
- Extend ingest writer to populate topic_tag during ingest (deterministic LLM call as in §3.3)

### §3.6 — bg_rules (significantly expanded — 1,213 → 8,000-12,000)

**Levers (apply all):**

1. **Pattern library expansion:** current 9 templates → 40-60 templates. New pattern families:
   - Sanskrit-named patterns: `{SA_PLANET}\s+(?:bhave|sthane|gata)\s+...` for chunks with Sanskrit
   - Compound antecedent: "Saturn in 7th AND Mars in 8th gives X"
   - Conjunction patterns: "Saturn with Mars in 7th"
   - Exchange-of-lords (parivartana): "Lord of 7th in 10th and Lord of 10th in 7th"
   - Aspect-from-house: "Saturn aspecting 7th from 1st"
   - Yoga-cited rules: "When Gajakesari Yoga forms, X happens"
   - Dasha-period rules: "During Saturn's Mahadasha if X, then Y"
   - Transit rules: "When Saturn transits over natal Moon, X"
   - Karaka-based rules: "Atmakaraka in 7th gives X"
   - Conditional negation: "Saturn in 7th, unless aspected by Jupiter, gives X"

2. **Ingest the 10 new texts** (from §3.3) — each text adds extractable rules. Estimated: +3,000-5,000 rules just from texts 6-15.

3. **LLM-assisted extraction with verification gate:** for chunks where Python regex extracts ZERO rules, run a single Gemini Flash pass with prompt "extract any predictive rules in this verse, in {antecedent, predicate, prediction} JSON form, with verbatim citation". Result goes to `sutravali_review`. Native batch-reviews; approved rows promote to `sutravali_rules`. LLM rows carry `extracted_by='gemini_flash_v1'` + `llm_prompt_hash` + `source_chunk_id` for reproducibility.

4. **Iterative pattern discovery loop:** after each extraction pass, generate a "missed coverage report" showing chunks with ZERO extractions. Native (or LLM-assisted) analyzes these for unrecognized phrasing families → adds patterns → re-runs. Two-three iterations to convergence.

5. **Rule quality scoring:** each rule gets a deterministic quality score:
   - antecedent.planet exists in bg_ontology (1/0)
   - antecedent.house in 1-12 (1/0)
   - predicate non-empty, contains noun (1/0)
   - source verse_ref exists in bg_texts (1/0)
   - prediction contains time/place/event marker (1/0)
   Sum >= 4 → live; 3 → review; <3 → reject.

**Code work:**
- Author `l0_sutravali_extractor.py` (currently missing — Stream D files don't exist in repo)
- Author pattern library file (separate Python module — easier to extend)
- Author LLM-assisted-extraction module with deterministic gate
- Author iterative coverage report
- Migration: add columns to `sutravali_rules` for new fields (extracted_by, llm_prompt_hash, quality_score, yoga_canonical_id, dasha_system_id, transit_marker)

### §3.7 — bg_remedies (significantly expanded — 200 → 2,000-3,000)

**Levers (apply all):**

1. **Ingest Mantra Mahodadhi** (Sanjay Rath edition; native uploads). ~1,500 mantra-verses → ~1,000 remedy rows after extraction (each verse = potentially multiple mantras for different deities/purposes).

2. **Sweep BPHS Ch.91-94** (dedicated upayas chapter) — currently extracts incidentally; targeted sweep yields ~100-150 remedy rows.

3. **Sweep Phaladeepika Ch.27** (remedial section) — ~50-80 remedy rows.

4. **Per-planet × per-category matrix scaffolding:** 9 planets × 11 remedy types = 99 cells minimum × 5 remedies per cell average = ~500 remedy floor coverage.

5. **Ingest Lal Kitab** (already in source data §92) — Lal Kitab is structured remedy-per-affliction; format is friendlier to deterministic extraction. ~300-500 remedy rows.

6. **LLM-assisted YAML scaffolder:** for each `bg_texts` chunk where the regex detects a remedy marker (mantra/yantra/dāna/vrata/japa), Gemini Flash produces a YAML-stub with extracted prescription_text + classical_attestation + planet/domain/category. Stub goes to `remedy_review_queue`; native approves → live `brahma_remedy_corpus`. Same deterministic gate as §3.6.

7. **Tantric careful-inclusion gate** (existing per Stream F §3): tantric remedies must trace to one of the acceptable source list (per `L0FR_SOURCE_DATA_v1_0.md §168-181`). Strictly enforced.

**Code work:**
- Extend `l0_remedy_corpus.py` REMEDIES list
- Author `l0_remedy_yaml_scaffolder.py` (LLM-assisted, deterministic gate, native review)
- Migration: brahma_remedy_corpus may need additional columns (classical_attestation_text, llm_prompt_hash, scaffold_status)

### §3.8 — bg_concordance (build from scratch — 0 → 300-500 topic rows)

This is the cross-school agreement/divergence index. Structure:

```sql
CREATE TABLE classical_attributions (
  attribution_id BIGSERIAL PRIMARY KEY,
  topic_id TEXT NOT NULL,                    -- e.g. 'saturn_7th_house_marriage'
  topic_canonical_name TEXT NOT NULL,         -- 'Effect of Saturn in 7th house on marriage'
  topic_category TEXT NOT NULL,               -- 'house_placement' | 'yoga' | 'dosha' | 'remedy' | 'dasha' | 'transit'
  school TEXT NOT NULL,                       -- 'parashari' | 'jaimini' | 'kp' | 'tajaka' | 'lal-kitab' | 'phaladeepika'
  stance TEXT NOT NULL,                       -- 'affirms' | 'denies' | 'qualifies' | 'silent'
  stance_text TEXT NOT NULL,                  -- the school's actual position
  classical_attestation TEXT,                 -- verbatim quote where possible
  source_text_id TEXT REFERENCES classical_texts(text_id),
  source_chunk_ids BIGINT[],                  -- references to bg_texts rows
  rule_ids UUID[],                            -- references to bg_rules rows
  confidence NUMERIC(4,3),                    -- 0.0 to 1.0
  derived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  derived_by TEXT,                            -- 'manual' | 'llm_gemini_pro_v1'
  llm_prompt_hash TEXT,
  CONSTRAINT uq_topic_school UNIQUE (topic_id, school)
);
```

**Build strategy:**

1. **Topic discovery:** start from the top ~200 most-queried topics (planet × house combinations, top yogas, top doshas, key dasha rules). Each topic gets a canonical_id and lives in `reference_topic_tags`.

2. **Per topic, per school:** LLM-assisted (Gemini Pro for quality). Prompt: "For topic X, what does {school} say? Cite source verse(s) from these provided chunks. If silent, return 'silent'. Output JSON {stance, stance_text, classical_attestation, source_chunk_ids}." Run per (topic × school) pair. Deterministic gate: source_chunk_ids must resolve to bg_texts rows; classical_attestation must appear verbatim in cited chunk.

3. **Synthesis stance generation:** for each topic, after collecting per-school positions, compute agreement_score (deterministic — fraction of schools that affirm) and produce a 1-line concordance note.

4. **Native review loop:** topics in unfamiliar territory are queued for native review before lighting.

**Realistic floor: 200 topics × 4-6 schools each = 800-1,200 rows. Concordance "topic count" surfaced in cockpit = ~200.**

**Code work:**
- Author `l0_concordance_builder.py` (new file)
- Author topic curation script (LLM-assisted from corpus mining)
- Migration: replace stub `classical_attributions` with full schema above

### §3.9 — bg_yogas (NEW; ~250-350 yogas)

**Schema:**
```sql
CREATE TABLE brahma_yoga_catalog (
  canonical_id TEXT PRIMARY KEY,                   -- 'gajakesari', 'raja_kahala', etc.
  name_sa TEXT NOT NULL,                            -- 'Gajakeśarī'
  name_en TEXT NOT NULL,                            -- 'Gajakesari Yoga'
  category TEXT NOT NULL,                           -- 'raja' | 'dhana' | 'pancha_mahapurusha' | 'aristha' | 'sannyasa' | 'other'
  formation_rule_jsonb JSONB NOT NULL,              -- structured: {requires: [{planet, house}, ...], aspects: [...]}
  formation_text TEXT NOT NULL,                     -- "Jupiter in a kendra from the Moon"
  significations_jsonb JSONB NOT NULL,              -- {wealth: true, fame: true, intelligence: true, ...}
  significations_text TEXT NOT NULL,                -- "Gives wealth, fame, intelligence, longevity"
  cancellation_conditions JSONB,                    -- conditions that nullify the yoga
  classical_citations JSONB,                        -- [{text_id, chapter, verse}, ...]
  source_chunk_ids BIGINT[],                        -- pointers to bg_texts
  school TEXT NOT NULL,                             -- which school primarily defines this
  rare BOOLEAN NOT NULL DEFAULT false,
  computed_strength_formula TEXT,                   -- how to score this yoga's strength in a chart
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Content sources:** BPHS Ch.30-35 (yogas), Saravali (extensive yoga catalog — ~120 yogas), Phaladeepika Ch.7, Jaimini, Brihat Jataka. Target ~250-350 distinct yogas.

**Code work:**
- Author `l0_yogas.py` (data + writer)
- Migration: CREATE TABLE brahma_yoga_catalog
- Cross-link: every yoga ALSO appears in `brahma_ontology` as entity_class='yoga'; bg_yogas owns the doctrinal data

### §3.10 — bg_dasha_systems (NEW; 15-20 systems)

**Schema:**
```sql
CREATE TABLE brahma_dasha_systems (
  canonical_id TEXT PRIMARY KEY,                   -- 'vimshottari', 'yogini', 'chara_jaimini', 'kalachakra', etc.
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  total_cycle_years NUMERIC NOT NULL,              -- 120 for Vimshottari, 36 for Yogini
  base_unit TEXT NOT NULL,                          -- 'nakshatra_lord' | 'sign_lord' | 'special'
  sequence_jsonb JSONB NOT NULL,                    -- ordered sequence of {ruler, years}
  computation_method TEXT NOT NULL,                 -- 'nakshatra_remainder' | 'rashi_kendra' | 'jaimini_chara'
  computation_pseudocode TEXT NOT NULL,             -- explicit derivation steps
  conditions_for_use TEXT,                          -- when to use this system
  school TEXT NOT NULL,
  classical_citations JSONB,
  source_chunk_ids BIGINT[],
  python_impl_module TEXT,                          -- pointer to PyJHora/PyHora module implementing this
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Content:** Vimshottari, Yogini, Chara (Jaimini), Ashtottari, Kalachakra, Shoola, Shashti-hayani, Dwadasottari, Panchottari, Shatabdika, Chaturshiti-Sama, Dwisaptati-Sama, Sthira, Tara, Yogardha. ~15-20 systems.

**Code work:**
- Author `l0_dasha_systems.py`
- Migration: CREATE TABLE brahma_dasha_systems
- Cross-link: ontology entries promoted to entity_class='dasha_system'

### §3.11 — bg_doshas (NEW; 50-80 doshas)

**Schema:**
```sql
CREATE TABLE brahma_dosha_catalog (
  canonical_id TEXT PRIMARY KEY,                   -- 'manglik', 'kala_sarpa', 'kemadruma', 'pitru', etc.
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL,                           -- 'graha_placement' | 'rashi_combination' | 'nakshatra_compatibility' | 'tithi'
  formation_rule_jsonb JSONB NOT NULL,
  formation_text TEXT NOT NULL,
  effects_text TEXT NOT NULL,
  severity_grades JSONB,                            -- {mild, moderate, severe} conditions
  cancellation_conditions JSONB,
  classical_citations JSONB,
  source_chunk_ids BIGINT[],
  associated_remedies UUID[],                       -- references to bg_remedies
  school TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Content:** Manglik (Kuja), Kala-sarpa, Kala-amrita, Kemadruma, Pitru, Gana (8-fold), Nadi (3-fold), Bhakoot (compatibility), Daridra, Vish (Visha), Mrityu, Sade-sati, Dhaiya, Punarphoo, etc. Target 50-80.

**Code work:**
- Author `l0_doshas.py`
- Migration: CREATE TABLE brahma_dosha_catalog
- Cross-link: ontology entries entity_class='dosha'; references bg_remedies for remedies-per-dosha

### §3.12 — bg_compendium_index (NEW; ~3,000-5,000 index rows)

**Schema:**
```sql
CREATE TABLE brahma_compendium_index (
  index_id BIGSERIAL PRIMARY KEY,
  text_id TEXT NOT NULL REFERENCES classical_texts(text_id),
  chapter_num INT,
  chapter_title_en TEXT,
  chapter_title_sa TEXT,
  topic_id TEXT REFERENCES reference_topic_tags(canonical_id),
  verse_start INT,
  verse_end INT,
  chunk_ids BIGINT[],                              -- pointers to bg_texts
  summary_text TEXT,                                -- chapter or section summary
  significance TEXT,                                -- why this section matters
  classical_significance_score NUMERIC(4,3),       -- 0.0 to 1.0
  derived_by TEXT,                                  -- 'manual' | 'llm_gemini_pro_v1'
  llm_prompt_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Content:** for each of 15 texts, index every chapter (15 × ~20 chapters = 300 chapter rows); plus topic-coverage map (every topic_tag × every text where it appears = ~500 × 8 average = ~4,000 rows). Total ~3,000-5,000.

**LLM use:** chapter summaries via Gemini Pro (temperature=0, fixed prompt, summary must cite specific chunks). Topic-coverage map generated deterministically by querying chunks' topic_tags grouped by text + chapter.

**Code work:**
- Author `l0_compendium_index.py`
- Migration: CREATE TABLE brahma_compendium_index
- Depends on bg_texts complete + reference_topic_tags seeded

## §4 — Integrity rules (the "no duplication / no conflict / high integrity" guarantee)

These rules are enforced by `parity_check.ts` (existing — extend it) AND by writer code (insert-time validation).

### §4.1 — Foreign-key integrity

- Every `reference_*` row's `canonical_id` MUST exist in `brahma_ontology`
- Every `bg_rules` row's antecedent.planet/sign/house MUST be valid ontology canonical_id (or 1-12 for house)
- Every `bg_yogas`/`bg_doshas`/`bg_dasha_systems` row MUST have a corresponding `brahma_ontology` row
- Every `bg_remedies` row's planet/domain/source_text_id MUST resolve in their respective tables
- Every `bg_concordance.source_chunk_ids` MUST resolve to `bg_texts` rows
- Every `bg_compendium_index` row's text_id + topic_id MUST resolve

### §4.2 — Single-source-of-truth rules

- An entity's NAMES live in `bg_ontology` and nowhere else
- An entity's CLASSICAL DOCTRINAL PROPERTIES live in the appropriate `reference_*` table and nowhere else
- An entity's NAMED YOGA PATTERNS live in `brahma_yoga_catalog` (referenced by ID elsewhere)
- An entity's NAMED DOSHA PATTERNS live in `brahma_dosha_catalog`
- An entity's REMEDIES live in `brahma_remedy_corpus`
- A SCHOOL'S POSITION on a topic lives in `classical_attributions` (concordance)
- Per-chart computations DO NOT live in L0 — they live at L1+

If asked "where does Saturn's exaltation degree go?" → `reference_planets.exaltation_degree`. NOT in ontology description, NOT in yogas, NOT in concordance. One place.

### §4.3 — Source-citation completeness

Every L0 row MUST have at least one of:
- `source_citation` (free text)
- `source_chunk_ids[]` (pointers to bg_texts)
- `classical_citations` jsonb (structured chapter/verse refs)

Insert-time validation enforces this. Rows without source citation → writer raises ValueError.

### §4.4 — LLM-generated content provenance

Every LLM-generated row carries:
- `derived_by` = `'llm_<model>_<version>'` (e.g. `'llm_gemini_flash_v1'`)
- `llm_prompt_hash` = sha256 of the deterministic prompt used
- `source_chunk_ids` = the input chunks the LLM was grounded in
- `temperature` field on the source-truth metadata (always 0 for L0 work)

This guarantees a given input + model + prompt produces a reproducible output on rebuild.

### §4.5 — Deterministic rebuild guarantee

The entire L0 layer can be rebuilt from:
- Source PDFs in GCS (15 texts)
- Pure-Python seed data files (reference, ontology, yogas, doshas, dasha-systems initial data)
- Deterministic LLM calls (temperature=0, fixed prompts, fixed model versions)
- Stored topic_tag and concordance topic_id canonical lists

Two clean rebuilds with no source change MUST produce identical row counts and identical content hashes per asset. `parity_check.ts` verifies this on every rebuild.

## §5 — Code architecture (don't break what's built)

This design **extends** the existing structure; it does NOT rebuild it.

### §5.1 — Existing pieces preserved

- `platform/python-sidecar/brahmagyan/l0_*.py` files (l0_ephemeris, l0_reference, l0_ontology, l0_texts, l0_text_index, l0_remedy_corpus, l0_almanac) — EXTEND, don't replace
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` — EXTEND with new asset registrations
- `platform/src/lib/jyotish/asset_names.ts` — ADD new bg_yogas/dashas/doshas/compendium-index entries
- `platform/scripts/seed/asset_registry_seed.ts` — ADD new entries; update bg_text_index count_sql
- Cockpit DataAssetsView + LayerPanel — render whatever the registry returns; auto-handles new assets

### §5.2 — New files (additive)

- `platform/python-sidecar/brahmagyan/l0_yogas.py`
- `platform/python-sidecar/brahmagyan/l0_dasha_systems.py`
- `platform/python-sidecar/brahmagyan/l0_doshas.py`
- `platform/python-sidecar/brahmagyan/l0_compendium_index.py`
- `platform/python-sidecar/brahmagyan/l0_sutravali_extractor.py` (currently missing per investigation)
- `platform/python-sidecar/brahmagyan/l0_concordance_builder.py`
- `platform/python-sidecar/brahmagyan/l0_remedy_yaml_scaffolder.py`
- `platform/python-sidecar/brahmagyan/llm_helpers.py` (shared deterministic LLM call wrapper with prompt hashing)
- 10+ new seed-data Python files under `platform/python-sidecar/brahmagyan/data/`
- Migration files for new tables + new columns (numbered sequentially after current main)

### §5.3 — Retrieval registry extensions

New L0 capabilities to register (extends Stream A's 5 capabilities):

| Capability | What |
|---|---|
| `query_yogas(name=null, category=null, planet=null)` | Filter brahma_yoga_catalog |
| `read_yoga(canonical_id)` | Single yoga full record |
| `query_doshas(name=null, category=null)` | Filter brahma_dosha_catalog |
| `read_dosha(canonical_id)` | Single dosha |
| `query_dasha_systems(canonical_id=null)` | List or read dasha system |
| `query_compendium(topic_id=null, text_id=null)` | Compendium index lookup |
| `query_concordance(topic_id, school=null)` | Cross-school positions on a topic |
| `resolve_topic(query_text)` | LLM-assisted topic_id resolution from natural-language query |
| `query_reference(table_name, filter_jsonb)` | Generic reference table query (for all 15 reference_* tables) |
| `query_remedies_by_dosha(dosha_id)` | Remedies indexed by dosha |
| `query_yogas_by_chart_pattern(planet_placements_jsonb)` | "Which yogas does this chart form?" — pure pattern matching against bg_yogas formation_rule_jsonb |

### §5.4 — Cockpit display

Adding 4 new tiles means the Brahma Jñāna section grows from 8 to 12 cards. Existing cockpit code (DataAssetsView + LayerPanel) renders registry contents — no UI code change needed for the new assets.

## §6 — Build phases (the work program)

Phase structure preserved from the L0FR pattern (streams + Vimarśaka gates) but adapted to "design enrichment" rather than "first build".

| Phase | Scope | Sessions | Streams (parallel possible) |
|---|---|---|---|
| **α — Foundation** | Migrations for new tables/columns + asset_registry updates + retrieval registry scaffolding + Vimarśaka-α review (architecture sanity) | 2-3 | one stream |
| **β — Reference enrichment** | bg_reference 15-table expansion + bg_ontology expansion | 4-6 | parallel: REF + ONT |
| **γ — New asset content** | bg_yogas + bg_dasha_systems + bg_doshas content | 4-6 | parallel: YOG + DASH + DOSH |
| **δ — Text corpus completion** | Ingest 10 missing texts + topic_tag classification | 3-5 | one stream (depends on PDF uploads) |
| **ε — Extraction enrichment** | bg_rules pattern expansion + LLM-assisted extraction + bg_remedies expansion + Mantra Mahodadhi ingestion | 5-8 | parallel: RULES + REMEDIES |
| **ζ — Concordance + Compendium** | bg_concordance topic discovery + per-school positions + bg_compendium_index | 4-6 | sequential: CONC → COMP |
| **η — Vimarśaka-Ω seal + rebuild proof** | Full integrity check + native deletion of all L0 data + autonomous rebuild via orchestrator + bit-for-bit verification | 1-2 | seal |

**Total estimate:** 23-36 sessions. Some highly parallel; some sequential.

Each phase produces its own brief, its own session queue, its own Vimarśaka review. The seal at η is the proof of complete L0.

## §7 — Cost model (LLM spend)

LLM usage authorized by native 2026-06-08; deterministic-first preserved via temperature=0 + prompt-hashing + verification gates.

| Phase | LLM use | Est. cost |
|---|---|---|
| α | None | $0 |
| β (ref + ont) | Synonym discovery for ontology (Gemini Flash); description writing for reference (Flash) | $5-10 |
| γ (yogas + dasha + dosha) | Significations text generation (Pro); cross-checked against text chunks | $20-40 |
| δ (text ingestion + topic_tag) | Topic-tag classification for ~14,500 chunks (Flash) | $10-20 |
| ε (rules + remedies expansion) | LLM-assisted rule extraction (Flash) for ~3,000 chunks; remedy YAML scaffolding (Flash) for ~500 chunks | $30-60 |
| ζ (concordance + compendium) | Per-school stance extraction (Pro) for ~200 topics × 6 schools = 1,200 calls; chapter summaries (Pro) for ~300 chapters | $80-150 |
| η (rebuild proof) | None | $0 |
| **Total L0 LLM budget** | | **~$150-300** |

Plus minor Cloud Run compute (~$20-40).

**Per-call discipline:** every LLM call MUST use `temperature=0`, fixed `seed`, fixed model version (e.g. `gemini-2.5-pro-2026-06-01`). The `prompt_hash` + `model_id` + `temperature` are stored per generated row.

## §8 — What this design does NOT do

- Does NOT touch L1+ assets (Ganita, Bodha, Kala, Phala, Mimamsa) — each gets its own design pass when its turn comes
- Does NOT change `bg_ephemeris` (locked per native: 1900-2150, Lahiri only)
- Does NOT rebuild any existing tables — only adds columns and adds new tables
- Does NOT change cockpit UI (registry-driven; auto-handles new assets)
- Does NOT change MCP OAuth or retrieval adapter substrate (Stream A's work preserved)
- Does NOT introduce a new authentication or authorization scheme
- Does NOT change branch/PR/CI process (continues per existing patterns)
- Does NOT pre-build for L1+ phases — the L0 design is self-contained

## §9 — Sealing definition

L0 is sealed (truly, finally) when:

1. All 12 assets registered, lit (or intentionally dormant), and surfaced in cockpit
2. Every asset meets its realistic floor per §3
3. parity_check.ts passes all §4 integrity rules
4. Native deletes all L0 data from prod
5. Orchestrator triggered for full rebuild
6. Rebuild completes; all 12 assets back at expected row counts within ±0.5%; content hashes match prior expected values
7. Vimarśaka-Ω attempt 1: SEAL

This is the long-term completion native asked for. After this, L0 is done — fully, comprehensively, with integrity proven by reproducibility.

## §10 — Next step

Author **Phase α brief** (foundation — migrations + asset_registry updates + retrieval registry scaffolding) as the first executable artifact. Phase α is small (~2-3 sessions), purely structural, no content writing. It lights up the 4 new tiles in the cockpit (initially with state=`dormant` or rows=0). Subsequent phases populate them.

After Phase α lands, phases β through η can largely run in parallel streams under the conductor pattern.

---

*End of L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md*
