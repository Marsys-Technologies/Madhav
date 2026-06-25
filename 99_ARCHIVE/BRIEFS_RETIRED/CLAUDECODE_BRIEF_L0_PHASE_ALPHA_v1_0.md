---
artifact: CLAUDECODE_BRIEF_L0_PHASE_ALPHA_v1_0
canonical_id: L0_PHASE_ALPHA_BRIEF
version: 1.1
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan holistic build — Phase α (Foundation)
phase: α (foundation; structural only — no content)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1 — deterministic-only)
branch: feature/l0-phase-alpha
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavL0Alpha (pre-create with `git worktree add`)
estimated_sessions: 2-3
estimated_time: 60-90 min total
llm_cost: $0
v1.1_changes:
  - REMOVED LLM provenance columns from migrations (no derived_by, no llm_prompt_hash) — L0 is now fully deterministic per native decision 2026-06-08
  - classical_attributions schema simplified to chunk-pointer-index model (no stance_text; L1+ synthesizes per query)
  - bg_rules.prediction confirmed verbatim-only (no normalization)
  - Embeddings (Vertex AI text-multilingual-embedding-002) remain PERMITTED as deterministic transform
  - All other scope unchanged
---

# L0 Phase α — Asset Registration + Infrastructure Provisioning

> **Scope discipline:** this brief registers + provisions structure only. Zero writer code. Zero data writes. Zero LLM. The result is: cockpit shows 12 L0 tiles, the 4 new ones surface as `dormant` (0 rows), the 8 existing ones keep their current state, and the database has tables ready for subsequent phases (β-ζ) to populate.

## §0 — Pre-read

REQUIRED reading before opening the worktree:
1. `00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md` — full parent design
2. `00_ARCHITECTURE/L0FR_SEALED_v1_0.md` — current sealed state
3. Memory `[[brahmagyan-naming-reconciliation]]` — naming conventions in force
4. Memory `[[cockpit-v1-v2-split]]` — how the cockpit renders the registry

If anything in the design surprises you, STOP and ask the native. Do not improvise.

## §1 — Scope summary

| Deliverable | What | Files touched |
|---|---|---|
| 1.1 — Migration: 4 new tables | `brahma_yoga_catalog`, `brahma_dasha_systems`, `brahma_dosha_catalog`, `brahma_compendium_index` + schema for new reference tables | 1 new migration file under `platform/supabase/migrations/` |
| 1.2 — Migration: schema changes to existing tables | ADD topic_tag TEXT column to classical_text_chunks; expand classical_attributions schema per design §3.8; add new columns to sutravali_rules + brahma_remedy_corpus + brahma_ontology per design §3.6/3.7/3.4 | 1 new migration file |
| 1.3 — Migration: 10 new reference_* tables | reference_houses, reference_strength_systems, reference_karakas, reference_upagrahas, reference_constants, reference_topic_tags, reference_glossary + 3 pointer tables (reference_yogas, reference_doshas, reference_dasha_systems) | 1 new migration file |
| 1.4 — asset_registry updates | (a) Update bg_text_index `count_sql` to new metric. (b) INSERT 4 new asset rows: bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index. (c) Update `count_sql` for bg_reference to sum all 15 reference tables. | 1 new migration file |
| 1.5 — asset_names.ts | Add 4 new L0 entries; preserve existing 8 | 1 source edit |
| 1.6 — asset_registry_seed.ts | Add 4 new brahmagyan entries; update bg_text_index + bg_reference count_sql; the seed file becomes idempotent and matches prod | 1 source edit |
| 1.7 — Run seed against prod | Apply migrations, then run `npx tsx scripts/seed/asset_registry_seed.ts` against prod DB | shell |
| 1.8 — Update parity_check.ts | Add validation rules for the 4 new asset_ids and the new FK constraints | 1 source edit |
| 1.9 — Vimarśaka-α review | Programmatic verification: 12 assets registered, 4 dormant, cockpit renders | shell |

## §2 — Setup

```bash
# Pre-create the worktree (one-time)
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune
git worktree add -b feature/l0-phase-alpha /Users/Dev/Vibe-Coding/Apps/MadhavL0Alpha main

cd /Users/Dev/Vibe-Coding/Apps/MadhavL0Alpha
git log --oneline -3  # verify on main HEAD

# DB proxy
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_alpha.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }

# Sanity checks against prod
psql_prod -c "SELECT count(*) AS l0_count FROM asset_registry WHERE layer='brahmagyan'"  # expect 8
psql_prod -c "SELECT asset_id FROM asset_registry WHERE layer='brahmagyan' ORDER BY sort_order"  # expect 8 bg_* rows
```

**CHECKPOINT setup:** worktree on `feature/l0-phase-alpha`; DB proxy live; prod shows the expected 8 L0 assets.

## §3 — Migration 1: 4 new content tables (yogas, dashas, doshas, compendium)

Author `platform/supabase/migrations/<NEXT_N>_l0_phase_alpha_new_content_tables.sql`:

```sql
-- L0 Phase α: 4 new content tables for bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index
-- Per design §3.9, §3.10, §3.11, §3.12
BEGIN;

-- §3.9 — Yoga catalog
CREATE TABLE IF NOT EXISTS brahma_yoga_catalog (
  canonical_id          TEXT PRIMARY KEY,
  name_sa               TEXT NOT NULL,
  name_en               TEXT NOT NULL,
  category              TEXT NOT NULL CHECK (category IN ('raja','dhana','pancha_mahapurusha','aristha','sannyasa','other')),
  formation_rule_jsonb  JSONB NOT NULL,
  formation_text        TEXT NOT NULL,
  significations_jsonb  JSONB NOT NULL DEFAULT '{}'::jsonb,
  significations_text   TEXT NOT NULL,
  cancellation_conditions JSONB,
  classical_citations   JSONB,
  source_chunk_ids      BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  school                TEXT NOT NULL,
  rare                  BOOLEAN NOT NULL DEFAULT false,
  computed_strength_formula TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_yoga_category ON brahma_yoga_catalog(category);
CREATE INDEX IF NOT EXISTS idx_yoga_school ON brahma_yoga_catalog(school);
CREATE INDEX IF NOT EXISTS idx_yoga_formation ON brahma_yoga_catalog USING gin(formation_rule_jsonb);
COMMENT ON TABLE brahma_yoga_catalog IS 'L0 bg_yogas — classical yoga definitions per design §3.9 (deterministic-only; no LLM provenance columns per v1.1)';

-- §3.10 — Dasha systems
CREATE TABLE IF NOT EXISTS brahma_dasha_systems (
  canonical_id          TEXT PRIMARY KEY,
  name_sa               TEXT NOT NULL,
  name_en               TEXT NOT NULL,
  total_cycle_years     NUMERIC NOT NULL,
  base_unit             TEXT NOT NULL CHECK (base_unit IN ('nakshatra_lord','sign_lord','special')),
  sequence_jsonb        JSONB NOT NULL,
  computation_method    TEXT NOT NULL,
  computation_pseudocode TEXT NOT NULL,
  conditions_for_use    TEXT,
  school                TEXT NOT NULL,
  classical_citations   JSONB,
  source_chunk_ids      BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  python_impl_module    TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dasha_school ON brahma_dasha_systems(school);
COMMENT ON TABLE brahma_dasha_systems IS 'L0 bg_dasha_systems — classical dasha system definitions per design §3.10 (deterministic-only)';

-- §3.11 — Dosha catalog
CREATE TABLE IF NOT EXISTS brahma_dosha_catalog (
  canonical_id          TEXT PRIMARY KEY,
  name_sa               TEXT NOT NULL,
  name_en               TEXT NOT NULL,
  category              TEXT NOT NULL CHECK (category IN ('graha_placement','rashi_combination','nakshatra_compatibility','tithi','other')),
  formation_rule_jsonb  JSONB NOT NULL,
  formation_text        TEXT NOT NULL,
  effects_text          TEXT NOT NULL,
  severity_grades       JSONB,
  cancellation_conditions JSONB,
  classical_citations   JSONB,
  source_chunk_ids      BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  associated_remedies   UUID[] DEFAULT ARRAY[]::UUID[],
  school                TEXT NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dosha_category ON brahma_dosha_catalog(category);
CREATE INDEX IF NOT EXISTS idx_dosha_school ON brahma_dosha_catalog(school);
COMMENT ON TABLE brahma_dosha_catalog IS 'L0 bg_doshas — classical dosha definitions per design §3.11 (deterministic-only)';

-- §3.12 — Compendium index
CREATE TABLE IF NOT EXISTS brahma_compendium_index (
  index_id              BIGSERIAL PRIMARY KEY,
  text_id               TEXT NOT NULL,
  chapter_num           INT,
  chapter_title_en      TEXT,
  chapter_title_sa      TEXT,
  topic_id              TEXT,
  verse_start           INT,
  verse_end             INT,
  chunk_ids             BIGINT[] DEFAULT ARRAY[]::BIGINT[],
  summary_text          TEXT,  -- mechanical first-N-chunks synopsis (deterministic; no LLM)
  significance          TEXT,
  classical_significance_score NUMERIC(4,3),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compendium_text ON brahma_compendium_index(text_id);
CREATE INDEX IF NOT EXISTS idx_compendium_topic ON brahma_compendium_index(topic_id);
CREATE INDEX IF NOT EXISTS idx_compendium_chapter ON brahma_compendium_index(text_id, chapter_num);
COMMENT ON TABLE brahma_compendium_index IS 'L0 bg_compendium_index — cross-reference index per design §3.12 (deterministic-only; summary_text is mechanical first-N-chunks synopsis, not LLM-generated)';

COMMIT;
```

**CHECKPOINT 3:** apply migration; verify 4 tables exist with expected columns.

```bash
NEXT_N=$(ls platform/supabase/migrations/ | grep -E '^[0-9]+_' | sed -E 's/^([0-9]+).*/\1/' | sort -n | tail -1 | awk '{print $1+1}')
MIG_FILE="platform/supabase/migrations/${NEXT_N}_l0_phase_alpha_new_content_tables.sql"
# Author the migration with the SQL above
psql_prod -f "$MIG_FILE"

# Verify
psql_prod -c "\d brahma_yoga_catalog" | head -10
psql_prod -c "\d brahma_dasha_systems" | head -10
psql_prod -c "\d brahma_dosha_catalog" | head -10
psql_prod -c "\d brahma_compendium_index" | head -10
```

## §4 — Migration 2: schema changes to existing tables

Author `platform/supabase/migrations/<NEXT_N+1>_l0_phase_alpha_existing_table_schema.sql`:

```sql
-- L0 Phase α: schema changes to existing tables per design §3.3, §3.4, §3.6, §3.7, §3.8
BEGIN;

-- §3.3 — Add topic_tag to classical_text_chunks (for bg_text_index new metric)
-- topic_tag is set by deterministic Python keyword-rule classifier per design v1.1; NOT by LLM
ALTER TABLE classical_text_chunks ADD COLUMN IF NOT EXISTS topic_tag TEXT;
CREATE INDEX IF NOT EXISTS idx_text_chunks_topic_tag ON classical_text_chunks(topic_tag);

-- §3.4 — brahma_ontology: NO LLM provenance columns needed (v1.1 deterministic-only)
-- ontology entries are 100% Python-authored from native + curated synonym lists
-- (no migration changes to brahma_ontology in v1.1)

-- §3.6 — Add columns to sutravali_rules (deterministic-extraction quality scoring + cross-refs)
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS quality_score NUMERIC(4,3);
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS yoga_canonical_id TEXT;
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS dasha_system_id TEXT;
ALTER TABLE sutravali_rules ADD COLUMN IF NOT EXISTS transit_marker BOOLEAN;
-- extracted_by already exists from Stream D schema (will only ever take values like 'python_regex_v1' — no llm_*)

-- §3.7 — Add columns to brahma_remedy_corpus
ALTER TABLE brahma_remedy_corpus ADD COLUMN IF NOT EXISTS classical_attestation_text TEXT;
ALTER TABLE brahma_remedy_corpus ADD COLUMN IF NOT EXISTS scaffold_status TEXT
  DEFAULT 'live' CHECK (scaffold_status IN ('live','review','rejected'));
-- No llm_prompt_hash; remedies are 100% native-authored YAML (Python loader; no LLM)

-- §3.8 — classical_attributions reshaped to chunk-pointer-index per v1.1 refinement
-- Drop stub and rebuild with the new model: per (topic_id, school), store chunk_ids only.
-- Synthesis of "what does school X say about topic Y" happens at L1+ query-time over the retrieved chunks.
DROP TABLE IF EXISTS classical_attributions;
CREATE TABLE classical_attributions (
  attribution_id        BIGSERIAL PRIMARY KEY,
  topic_id              TEXT NOT NULL,                                       -- e.g. 'saturn_7th_marriage'
  topic_canonical_name  TEXT NOT NULL,                                        -- 'Effect of Saturn in 7th house on marriage'
  topic_category        TEXT NOT NULL,                                        -- 'house_placement' | 'yoga' | 'dosha' | 'remedy' | 'dasha' | 'transit'
  school                TEXT NOT NULL,                                        -- 'parashari' | 'jaimini' | 'kp' | 'tajaka' | 'lal-kitab' | 'phaladeepika'
  source_text_ids       TEXT[] DEFAULT ARRAY[]::TEXT[],                       -- texts where this school's stance appears
  source_chunk_ids      BIGINT[] NOT NULL DEFAULT ARRAY[]::BIGINT[],          -- chunks for L1+ to synthesize over
  rule_ids              UUID[] DEFAULT ARRAY[]::UUID[],                       -- if rules already extracted
  match_method          TEXT NOT NULL,                                        -- 'keyword' | 'topic_tag' | 'manual' | 'cross_ref'
  match_confidence      NUMERIC(4,3),                                         -- deterministic score from keyword overlap or topic-tag exact match
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_topic_school UNIQUE (topic_id, school)
);
CREATE INDEX IF NOT EXISTS idx_concordance_topic ON classical_attributions(topic_id);
CREATE INDEX IF NOT EXISTS idx_concordance_school ON classical_attributions(school);
CREATE INDEX IF NOT EXISTS idx_concordance_category ON classical_attributions(topic_category);
COMMENT ON TABLE classical_attributions IS 'L0 bg_concordance — chunk-pointer index per (topic, school). Stores WHICH chunks contain each school'\''s discussion of each topic; SYNTHESIS of stance happens at L1+ query-time per design v1.1 §2.5 refinement.';

COMMIT;
```

**CHECKPOINT 4:** apply migration; verify column additions + classical_attributions schema.

```bash
NEXT_N=$((NEXT_N + 1))
MIG_FILE="platform/supabase/migrations/${NEXT_N}_l0_phase_alpha_existing_table_schema.sql"
# Author the migration with the SQL above
psql_prod -f "$MIG_FILE"

# Verify
psql_prod -c "SELECT column_name FROM information_schema.columns WHERE table_name='classical_text_chunks' AND column_name='topic_tag'"
psql_prod -c "\d classical_attributions" | head -20
psql_prod -c "SELECT column_name FROM information_schema.columns WHERE table_name='brahma_remedy_corpus' AND column_name='scaffold_status'"
```

## §5 — Migration 3: 10 new reference_* tables

Author `platform/supabase/migrations/<NEXT_N+1>_l0_phase_alpha_reference_tables.sql`:

```sql
-- L0 Phase α: 10 new reference_* tables per design §3.2
BEGIN;

CREATE TABLE IF NOT EXISTS reference_houses (
  house_num INT PRIMARY KEY CHECK (house_num >= 1 AND house_num <= 12),
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('kendra','panapara','apoklima','dusthana','upachaya','trika','trikona')),
  natural_significations JSONB NOT NULL,
  karakas JSONB NOT NULL,
  classical_doctrine_jsonb JSONB NOT NULL,
  source_citation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_strength_systems (
  strength_id TEXT PRIMARY KEY,
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('shadbala','ashtakavarga','bhava_bala','other')),
  formula_text TEXT NOT NULL,
  max_value NUMERIC,
  units TEXT,
  classical_interpretation TEXT,
  source_citation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_karakas (
  karaka_id TEXT PRIMARY KEY,
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  karaka_type TEXT NOT NULL CHECK (karaka_type IN ('sthira_planet','sthira_house','chara_jaimini')),
  applies_to TEXT,
  classical_significations JSONB NOT NULL,
  source_citation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_upagrahas (
  upagraha_id TEXT PRIMARY KEY,
  name_sa TEXT NOT NULL,
  name_en TEXT NOT NULL,
  parent_planet TEXT,
  computation_method TEXT NOT NULL,
  significations JSONB NOT NULL,
  source_citation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reference_constants (
  constant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  value_numeric NUMERIC,
  value_text TEXT,
  unit TEXT,
  category TEXT NOT NULL,
  source_citation TEXT NOT NULL,
  classical_context TEXT
);

CREATE TABLE IF NOT EXISTS reference_topic_tags (
  canonical_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  example_chunks JSONB
);

CREATE TABLE IF NOT EXISTS reference_glossary (
  term_id TEXT PRIMARY KEY,
  term_sa TEXT NOT NULL,
  term_en TEXT,
  definition TEXT NOT NULL,
  category TEXT,
  classical_citation TEXT NOT NULL,
  related_concepts TEXT[]
);

-- Pointer tables (lightweight index into the major content catalogs)
CREATE TABLE IF NOT EXISTS reference_yogas (
  canonical_id TEXT PRIMARY KEY,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL,
  CONSTRAINT fk_ref_yoga FOREIGN KEY (canonical_id) REFERENCES brahma_yoga_catalog(canonical_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reference_doshas (
  canonical_id TEXT PRIMARY KEY,
  name_en TEXT NOT NULL,
  category TEXT NOT NULL,
  CONSTRAINT fk_ref_dosha FOREIGN KEY (canonical_id) REFERENCES brahma_dosha_catalog(canonical_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reference_dasha_systems (
  canonical_id TEXT PRIMARY KEY,
  name_en TEXT NOT NULL,
  school TEXT NOT NULL,
  CONSTRAINT fk_ref_dasha_sys FOREIGN KEY (canonical_id) REFERENCES brahma_dasha_systems(canonical_id) ON DELETE CASCADE
);

COMMIT;
```

**CHECKPOINT 5:** apply migration; verify 10 tables exist.

```bash
NEXT_N=$((NEXT_N + 1))
MIG_FILE="platform/supabase/migrations/${NEXT_N}_l0_phase_alpha_reference_tables.sql"
psql_prod -f "$MIG_FILE"

for t in reference_houses reference_strength_systems reference_karakas reference_upagrahas reference_constants reference_topic_tags reference_glossary reference_yogas reference_doshas reference_dasha_systems; do
  psql_prod -c "SELECT '$t' AS tbl, count(*) AS rows FROM $t"
done
# All should return 0 rows (tables exist, no data yet)
```

## §6 — Migration 4: asset_registry updates

Author `platform/supabase/migrations/<NEXT_N+1>_l0_phase_alpha_asset_registry.sql`:

```sql
-- L0 Phase α: asset_registry updates per design §1
BEGIN;

-- §2.2 — Fix bg_text_index count_sql to measure topic-tag coverage (not chunk count)
UPDATE asset_registry SET
  count_sql = 'SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL',
  english_description = 'Measurement of retrieval index health — distinct topic tags across embedded + indexed chunks. Retrieval tools point at bg_texts; this asset reports the index coverage metric.',
  volume_explanation = 'Distinct topic_tag count from embedded chunks. Per design §2.2: retrieval tools never reference bg_text_index directly; they go through bg_texts.'
WHERE asset_id = 'bg_text_index';

-- §3.2 — Update bg_reference count_sql to sum all 15 reference_* tables
UPDATE asset_registry SET
  count_sql = 'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) + (SELECT count(*) FROM reference_yogas) + (SELECT count(*) FROM reference_doshas) + (SELECT count(*) FROM reference_dasha_systems) AS count',
  english_description = 'The holy grail of L0 — structured properties of every classical Jyotish concept across 15 specialized typed tables.',
  volume_explanation = 'Sum of 15 reference_* tables (per design §3.2). Each table is normalized + typed; ontology resolves names, reference holds properties.'
WHERE asset_id = 'bg_reference';

-- Register 4 new L0 assets
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula, expected_volume_inputs, volume_explanation, depends_on, scope, is_active, estimated_seconds) VALUES
  ('bg_yogas', 'brahmagyan', 9, 'Yoga-saṅgraha', 'Yoga Catalog',
   'Classical yoga definitions — formation rules, significations, classical citations',
   'postgres_table', 'brahma_yoga_catalog',
   'SELECT count(*) FROM brahma_yoga_catalog',
   'SELECT pg_total_relation_size(''brahma_yoga_catalog'')',
   200, NULL, NULL,
   'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_dasha_systems', 'brahmagyan', 10, 'Daśā-paddhati', 'Dasha Systems',
   'Classical dasha system definitions — sequence rules, computation methods, conditions for use',
   'postgres_table', 'brahma_dasha_systems',
   'SELECT count(*) FROM brahma_dasha_systems',
   'SELECT pg_total_relation_size(''brahma_dasha_systems'')',
   15, NULL, NULL,
   '15-20 named dasha systems (Vimshottari, Yogini, Chara, Kalachakra, etc.) per design §3.10',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_doshas', 'brahmagyan', 11, 'Doṣa-kośa', 'Dosha Catalog',
   'Classical dosha definitions — formation rules, effects, severity, cancellation conditions',
   'postgres_table', 'brahma_dosha_catalog',
   'SELECT count(*) FROM brahma_dosha_catalog',
   'SELECT pg_total_relation_size(''brahma_dosha_catalog'')',
   50, NULL, NULL,
   'Catalog of named dosha patterns (Manglik, Kala-sarpa, Kemadruma, etc.) per design §3.11',
   ARRAY['bg_ontology']::text[], 'global', true, NULL),

  ('bg_compendium_index', 'brahmagyan', 12, 'Anukrama', 'Compendium Index',
   'Cross-reference index over the 15 classical texts — chapter summaries, topic-coverage map, significance scores',
   'postgres_table', 'brahma_compendium_index',
   'SELECT count(*) FROM brahma_compendium_index',
   'SELECT pg_total_relation_size(''brahma_compendium_index'')',
   3000, NULL, NULL,
   '~3,000-5,000 index rows: per-text-per-chapter + per-text-per-topic-tag per design §3.12',
   ARRAY['bg_texts','reference_topic_tags']::text[], 'global', true, NULL);

COMMIT;
```

**CHECKPOINT 6:** apply migration; verify 12 L0 rows.

```bash
NEXT_N=$((NEXT_N + 1))
MIG_FILE="platform/supabase/migrations/${NEXT_N}_l0_phase_alpha_asset_registry.sql"
psql_prod -f "$MIG_FILE"

psql_prod -c "SELECT asset_id, sanskrit_name, english_name, sort_order FROM asset_registry WHERE layer='brahmagyan' ORDER BY sort_order"
# Expect 12 rows
```

## §7 — asset_names.ts update

Edit `platform/src/lib/jyotish/asset_names.ts` — add 4 new entries in the L0 block (after `bg_concordance`):

```typescript
  // ── L0 Brahmagyan — Global Foundation ────────────────────────────────────
  bg_ephemeris:    { sanskrit: 'Graha Sphuṭa',   english: 'Ephemeris',          subtitle: 'Swiss Ephemeris DE441 — raw astronomical positions', layer: 'L0' },
  bg_reference:    { sanskrit: 'Sāraṇī',         english: 'Reference Library',  subtitle: '15 specialized typed tables — every classical concept', layer: 'L0' },
  bg_texts:        { sanskrit: 'Śāstrapāṭha',    english: 'Classical Texts',    subtitle: 'BPHS + 14 more — verse chunks',                       layer: 'L0' },
  bg_ontology:     { sanskrit: 'Nāmasaṃgraha',   english: 'Ontology',           subtitle: 'Canonical names + synonyms — resolve_entity source',   layer: 'L0' },
  bg_text_index:   { sanskrit: 'Śabdakośa',      english: 'Text Index',         subtitle: 'Retrieval index health — distinct topic tags',         layer: 'L0' },
  bg_rules:        { sanskrit: 'Sūtravālī',      english: 'Rule Base',          subtitle: 'Extracted classical rules, verse-traceable',           layer: 'L0' },
  bg_remedies:     { sanskrit: 'Upāya-kośa',     english: 'Remedy Corpus',      subtitle: 'Mantras, gemstones, charity, vrata, yantras, …',     layer: 'L0' },
  bg_concordance:  { sanskrit: 'Samanvaya',      english: 'Concordance',        subtitle: 'Cross-school agreement / divergence per topic',       layer: 'L0' },
  bg_yogas:        { sanskrit: 'Yoga-saṅgraha',  english: 'Yoga Catalog',       subtitle: 'Classical yoga definitions — Raja, Dhana, Pancha-Mahapurusha, …', layer: 'L0' },
  bg_dasha_systems:{ sanskrit: 'Daśā-paddhati',  english: 'Dasha Systems',      subtitle: 'Vimshottari, Yogini, Chara, Kalachakra, …',           layer: 'L0' },
  bg_doshas:       { sanskrit: 'Doṣa-kośa',      english: 'Dosha Catalog',      subtitle: 'Manglik, Kala-sarpa, Kemadruma, …',                   layer: 'L0' },
  bg_compendium_index: { sanskrit: 'Anukrama',   english: 'Compendium Index',   subtitle: 'Cross-text chapter index + topic-coverage map',       layer: 'L0' },
```

Also update the test at `platform/src/lib/jyotish/__tests__/asset_names.test.ts` if it has a specific L0 key list — extend the array to 12 keys.

**CHECKPOINT 7:** tsc + vitest pass.

```bash
cd platform
npx tsc --noEmit src/lib/jyotish/asset_names.ts src/lib/jyotish/__tests__/asset_names.test.ts 2>&1 | tail -10
npx vitest run src/lib/jyotish/__tests__/asset_names.test.ts 2>&1 | tail -10
cd ..
```

## §8 — asset_registry_seed.ts update

Edit `platform/scripts/seed/asset_registry_seed.ts` — add 4 new brahmagyan entries to the ASSETS array (after `bg_concordance`):

```typescript
  {
    asset_id: 'bg_yogas',
    layer: 'brahmagyan', sort_order: 9,
    sanskrit_name: 'Yoga-saṅgraha',
    english_name: 'Yoga Catalog',
    english_description: 'Classical yoga definitions — formation rules, significations, classical citations',
    storage_type: 'postgres_table',
    target_table: 'brahma_yoga_catalog',
    count_sql: 'SELECT count(*) FROM brahma_yoga_catalog',
    size_sql: "SELECT pg_total_relation_size('brahma_yoga_catalog')",
    target_floor: 200,
    expected_volume_formula: null,
    expected_volume_inputs: null,
    volume_explanation: 'Catalog of named yoga patterns from BPHS / Saravali / Phaladeepika / Jaimini per design §3.9',
    depends_on: ['bg_ontology'],
    scope: 'global', is_active: true, estimated_seconds: null,
  },
  // ... similar for bg_dasha_systems, bg_doshas, bg_compendium_index
```

Also update the seed entries for `bg_text_index` and `bg_reference` count_sql to match the migration 4 values (so future re-runs of the seed match prod, idempotent).

**CHECKPOINT 8:** running the seed against prod produces ZERO diffs (idempotent).

```bash
cd platform
# Dry-run: capture what the seed would change
DATABASE_URL=$PROD_DB_URL DRY_RUN=1 npx tsx scripts/seed/asset_registry_seed.ts 2>&1 | head -30
# Should report 0 inserts, 0 updates (everything already matches)

# If clean: do a real run (no-op, just confirms idempotency)
DATABASE_URL=$PROD_DB_URL npx tsx scripts/seed/asset_registry_seed.ts 2>&1 | tail -10
cd ..

# Verify post-seed prod state
psql_prod -c "SELECT asset_id, count_sql FROM asset_registry WHERE layer='brahmagyan' ORDER BY sort_order"
```

## §9 — parity_check.ts update

Extend `platform/src/lib/retrieval/registry/parity_check.ts` to recognize the 4 new asset_ids + the FK constraints from design §4.1:

```typescript
const L0_BRAHMAGYAN_ASSETS = [
  'bg_ephemeris', 'bg_reference', 'bg_texts', 'bg_ontology',
  'bg_text_index', 'bg_rules', 'bg_remedies', 'bg_concordance',
  'bg_yogas', 'bg_dasha_systems', 'bg_doshas', 'bg_compendium_index',
] as const

// Add FK integrity assertions (run against prod periodically; not blocking):
//   - every brahma_yoga_catalog.canonical_id appears in brahma_ontology (entity_class='yoga')
//   - every brahma_dosha_catalog.canonical_id appears in brahma_ontology (entity_class='dosha')
//   - every brahma_dasha_systems.canonical_id appears in brahma_ontology (entity_class='dasha_system')
//   - every brahma_compendium_index.text_id resolves in classical_texts
//   - every brahma_compendium_index.topic_id resolves in reference_topic_tags
```

**CHECKPOINT 9:** tsc passes; parity_check exports the new constants.

```bash
cd platform
npx tsc --noEmit src/lib/retrieval/registry/parity_check.ts 2>&1 | tail -10
cd ..
```

## §10 — Commit + push + open PR

```bash
git add -A
git status
# Should show: 4 new migrations, asset_names.ts edit, asset_registry_seed.ts edit, parity_check.ts edit

git commit -m "feat(l0/phase-alpha): register 12 L0 assets + provision infrastructure

Implements L0_BRAHMAGYAN_HOLISTIC_DESIGN v1.0 Phase α (Foundation).

Migrations:
- _l0_phase_alpha_new_content_tables.sql: brahma_yoga_catalog, brahma_dasha_systems,
  brahma_dosha_catalog, brahma_compendium_index (per design §3.9, §3.10, §3.11, §3.12)
- _l0_phase_alpha_existing_table_schema.sql: topic_tag column on classical_text_chunks;
  LLM provenance columns on brahma_ontology + sutravali_rules + brahma_remedy_corpus;
  classical_attributions stub replaced with full schema (per design §3.8)
- _l0_phase_alpha_reference_tables.sql: 10 new reference_* tables for bg_reference
  expansion (per design §3.2)
- _l0_phase_alpha_asset_registry.sql: bg_text_index count_sql fixed to topic-tag metric;
  bg_reference count_sql expanded to sum all 15 reference tables; 4 new asset rows
  registered (bg_yogas, bg_dasha_systems, bg_doshas, bg_compendium_index)

Source:
- asset_names.ts: 4 new L0 entries
- asset_registry_seed.ts: 4 new brahmagyan entries + bg_text_index/bg_reference count_sql update
- parity_check.ts: L0_BRAHMAGYAN_ASSETS extended to 12; FK integrity assertions documented

Result: cockpit shows 12 L0 tiles; 4 new are dormant (0 rows); existing 8 unchanged
except bg_text_index displays new metric. NO writer code, NO data writes, NO LLM.

Subsequent phases (β-ζ) populate the new tables; phase η is the rebuild proof.

Parent design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md"

git push -u origin feature/l0-phase-alpha

gh pr create \
  --title "feat(l0/phase-alpha): register 12 L0 assets + provision infrastructure" \
  --body "Phase α of L0_BRAHMAGYAN_HOLISTIC_DESIGN v1.0. Structural-only: 4 migrations, asset_registry updates, source-file updates. Zero writer code, zero data writes, zero LLM cost.

After merge + deploy:
- Cockpit L0 section shows 12 tiles (was 8)
- 4 new tiles (yogas, dasha-systems, doshas, compendium-index) show dormant / 0 rows
- bg_text_index metric updated (topic-tag count, not chunk count) — will show 0 until phase δ populates topic_tag column
- bg_reference count rolls up 15 reference tables — will show 88 (existing 5 tables) until phase β populates the 10 new ones

Subsequent phases (β-ζ) populate the new tables; phase η is the autonomous-rebuild proof.

Parent design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md" \
  --base main --head feature/l0-phase-alpha
```

## §11 — Vimarśaka-α (autonomous review)

After merge, before declaring Phase α complete, run programmatic verification:

```bash
psql_prod -c "SELECT count(*) FROM asset_registry WHERE layer='brahmagyan'"
# Expect: 12

psql_prod -c "SELECT asset_id, count_sql FROM asset_registry WHERE asset_id IN ('bg_text_index','bg_reference')"
# bg_text_index must reference 'topic_tag'; bg_reference must reference all 15 tables

for t in brahma_yoga_catalog brahma_dasha_systems brahma_dosha_catalog brahma_compendium_index classical_attributions reference_houses reference_strength_systems reference_karakas reference_upagrahas reference_constants reference_topic_tags reference_glossary reference_yogas reference_doshas reference_dasha_systems; do
  exists=$(psql_prod -At -c "SELECT to_regclass('$t')")
  echo "$t: $exists"
done
# All must return their name (not NULL)

psql_prod -c "SELECT column_name FROM information_schema.columns WHERE table_name='classical_text_chunks' AND column_name='topic_tag'"
# Must return 'topic_tag'

# Cockpit smoke test (Chrome MCP)
# Navigate to /clients/482012f1-710e-4a25-994a-93821f5871aa/build
# Confirm: 12 L0 tiles render; 4 new show "dormant" or 0 rows
```

**CHECKPOINT 11:** all checks PASS → Phase α SEALED. Subsequent phases unblock.

## §12 — Hard stops

- Migration 1/2/3/4 fails to apply → STOP, do not proceed; report
- `npx tsc --noEmit` fails after asset_names.ts or parity_check.ts edits → STOP, fix
- `npx vitest run asset_names.test.ts` fails → STOP, fix
- Seed `DRY_RUN=1` reports unexpected diffs → STOP, the seed file drifted from migration intent
- Vimarśaka-α §11 checks fail any item → STOP, halt before declaring Phase α complete
- Any unexpected error → STOP, report

## §13 — What this brief does NOT do

- Does NOT seed any data into the new tables (Phase β-ζ work)
- Does NOT author writers for any of the new assets
- Does NOT make any LLM calls
- Does NOT touch L1+ assets
- Does NOT modify the cockpit UI (registry-driven; auto-handles 12 vs 8)
- Does NOT delete any data
- Does NOT trigger any build / orchestrator runs
- Does NOT change MCP OAuth or retrieval adapter substrate

## §14 — Scope discipline

The temptation will be to seed initial data into the new tables "while we're here." DO NOT. Phase α is structural only. Data work is Phase β onwards and is its own brief with its own review gates.

## §15 — v1.1 amendments summary (for the executor reading this brief)

**Deterministic-only stance locked.** Per native decision 2026-06-08:
- NO LLM use anywhere in L0 construction
- Embeddings (text-multilingual-embedding-002) PERMITTED — pure deterministic transform
- All LLM provenance columns (`derived_by`, `llm_prompt_hash`) STRIPPED from Phase α migrations
- `topic_tag` is populated by a deterministic Python keyword-rule classifier (subsequent phase), NOT by LLM
- `bg_concordance` schema reshaped to chunk-pointer-index — store WHICH chunks; SYNTHESIS happens at L1+ query-time
- `bg_rules.prediction` field will be verbatim verse fragments only (no normalization)
- `bg_compendium_index.summary_text` is mechanical first-N-chunks synopsis (no LLM)
- bg_remedies will be 100% YAML hand-curation (Python loader; no LLM scaffolder)

**What this means for Phase α executor:** the migrations in §3-§5 above already reflect v1.1 (no LLM provenance columns). Just apply them. Subsequent phases (β-ζ) will be authored with deterministic-only writers.

Begin §2 setup.

---

*End of CLAUDECODE_BRIEF_L0_PHASE_ALPHA_v1_0.md*
