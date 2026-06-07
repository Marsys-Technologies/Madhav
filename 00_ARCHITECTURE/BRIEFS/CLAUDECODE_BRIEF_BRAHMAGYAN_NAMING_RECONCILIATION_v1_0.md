---
artifact: CLAUDECODE_BRIEF_BRAHMAGYAN_NAMING_RECONCILIATION_v1_0.md
canonical_id: BRAHMAGYAN_NAMING_RECONCILIATION
version: 1.0
status: READY_FOR_AUTONOMOUS_EXECUTION
authored_by: Cowork (planning) 2026-06-07
authored_for: Claude Code in Antigravity IDE
scope: L0 Brahmagyan canonical naming — DB + code + tests + briefs + governance docs
delivery_model: 3 sequenced CC pastes, plan-then-execute, no synchronous gates
---

# Brahmagyan Naming Reconciliation — Master Plan v1.0

## §0 — Why this brief exists

Investigating the cockpit Brahma Jñāna state revealed **three coordinated naming inconsistencies** across the project:

1. **Asset ID style mismatch.** DB `asset_registry` uses long-form `brahmagyan.kalapancanga`; source `asset_names.ts` uses short-form `bg_ephemeris`. They never reconciled. Cockpit reads from DB; tests + UI read from source. Result: rename + drift risk on every seed re-run.

2. **Samanvaya/Ontology conceptual collision.** `asset_names.ts` correctly defines TWO assets — `bg_ontology` (Nāmasaṃgraha, canonical entity IDs) and `bg_concordance` (Samanvaya, cross-school agreement). DB registry merged them into one row labeled "Concordance" pointing at the (non-existent) `classical_attributions` table. Stream A authored a `brahma_ontology` table but never registered it.

3. **Stale entries in registry.** `sensitive_point_catalog` (chart-specific, not global L0) and `panchanga_almanac` (now a service, not a stored asset) shouldn't be in the L0 layer at all.

Plus 4 wiring errors (count_sql pointing at wrong tables) surfaced during Vimarśaka-Z review.

This brief reconciles all of it in one coherent rename arc. **After completion:** the 8 canonical L0 assets exist under stable short-form IDs across DB + code + tests + briefs + governance docs. Cockpit reflects truth. Future seed re-runs are idempotent.

## §1 — Locked canonical naming

These 8 assets ARE the L0 Brahmagyan layer. No more, no less.

| # | sort | Sanskrit | English | asset_id | backing | scope | active? | notes |
|---|------|----------|---------|----------|---------|-------|---------|-------|
| 1 | 1 | **Graha-sphuṭa** | Ephemeris (Graha Sphuṭa) | `bg_ephemeris` | `ephemeris_daily` | global | ✓ | lit |
| 2 | 2 | **Sāraṇī** | Reference Library | `bg_reference` | sum-of-5-ref-tables | global | ✓ | seed in Phase 1 |
| 3 | 3 | **Śāstrapāṭha** | Classical Texts | `bg_texts` | `classical_text_chunks` | global | ✓ | lit |
| 4 | 4 | **Nāmasaṃgraha** | Ontology | `bg_ontology` | `brahma_ontology` | global | ✓ | seed in Phase 1 |
| 5 | 5 | **Śabdakośa** | Text Index | `bg_text_index` | `classical_text_chunks WHERE embedding IS NOT NULL` | global | ✓ | lit |
| 6 | 6 | **Sūtravālī** | Rule Base | `bg_rules` | `sutravali_rules` | global | ✓ | building (1,213) |
| 7 | 7 | **Upāya-kośa** | Remedy Corpus | `bg_remedies` | `brahma_remedy_corpus` | global | ✓ | building (200) |
| 8 | 8 | **Samanvaya** | Concordance | `bg_concordance` | `classical_attributions` | global | ⊘ | dormant placeholder; build later |

**Notes on naming choices:**
- **`bg_ephemeris`** (NOT `bg_kalapancanga`): "Kālapañcāṅga" was a misleading name — it implied panchang/almanac functionality. The asset is purely ephemeris (raw astronomical positions). Renamed Sanskrit to **Graha-sphuṭa** (literally "planetary positions") to match the actual content.
- **`bg_ontology` + `bg_concordance` as SEPARATE assets**: design intent in `asset_names.ts` was correct. Ontology = canonical entity vocabulary (resolve "Shani" → "saturn"). Concordance = cross-school agreement/divergence index (BPHS vs Jaimini vs Tajaka on a topic). Different problems, different tables.
- **`bg_rules`** (NOT `bg_sutravali`): the layer-prefix-plus-concept-noun convention matches `ga_dashas`, `bo_signals`, `ka_timeline` etc. across the 6 layers. Sanskrit is preserved as the display name; the asset_id is the English concept.
- **`bg_remedies`** (NOT `bg_upaya_kosha` or `bg_remedy_corpus`): same convention.
- **`bg_concordance` STAYS as dormant placeholder**: it's a real future-build, not vapor. The classical_attributions table doesn't exist yet. Registry shows it as planned/dormant; we build it when the cross-school divergence work begins (post-M5).

## §2 — Drops from L0 Brahmagyan layer

| asset_id (current) | reason | future home |
|---|---|---|
| `brahmagyan.sensitive_point_catalog` | Chart-specific (per-chart upagraha/special-lagna positions) | L1 Gaṇita — already exists as `ga_sensitive` |
| `brahmagyan.panchanga_almanac` | Replaced by Pañcāṅga service (compute on-demand, not stored) | Not an asset; surface in cockpit as a service health tile (Phase 4, deferred) |
| `bg_almanac` (in asset_names.ts only) | Same as above — was a stale entry | Remove from asset_names.ts in Phase 2 |

After drops, L0 has exactly 8 assets. L0 count in `asset_names.test.ts` stays at 8 (the test already expects 8 keys, just with `bg_almanac` swapped out — net zero).

## §3 — File inventory (categorized)

### §3.1 — Database (Phase 1)

| File | Edit type |
|------|-----------|
| `platform/supabase/migrations/<NEXT>_brahmagyan_naming_reconciliation.sql` | NEW — DELETE 8 old rows + INSERT 8 canonical rows + UPDATE seed_safe (see §4.1) |
| `platform/python-sidecar/brahmagyan/l0_reference_library.py` | NEW — pure-Python seeder for 5 ref tables (~96 rows total) |
| `platform/python-sidecar/brahmagyan/l0_ontology.py` | NEW (or update existing) — pure-Python seeder for brahma_ontology (~100 rows) |
| `platform/supabase/migrations/<NEXT+1>_classical_attributions_placeholder.sql` | NEW — CREATE TABLE classical_attributions stub (empty; allows dormant registration without error) |

### §3.2 — Source code (Phase 2)

| File | Edit type |
|------|-----------|
| `platform/src/lib/jyotish/asset_names.ts` | EDIT — remove `bg_almanac`; rename `bg_ephemeris` english to "Ephemeris (Graha Sphuṭa)" + sanskrit to "Graha-sphuṭa" |
| `platform/src/lib/jyotish/__tests__/asset_names.test.ts` | EDIT — remove `bg_almanac` from l0Keys list (8 still equals 8 after `bg_almanac` removal — wait, l0Keys currently has 8 including bg_almanac; removing makes it 7. Update test minimum to 7 OR add bg_concordance which is already there). Verify: test currently lists `['bg_ephemeris','bg_reference','bg_texts','bg_ontology','bg_text_index','bg_rules','bg_almanac','bg_concordance']` = 8 keys; after removing bg_almanac = 7 keys. Change l0Keys array. |
| `platform/scripts/seed/asset_registry_seed.ts` | REWRITE — replace the 8 brahmagyan entries with the canonical 8 (bg_* IDs, correct sanskrit/english/count_sql/target_table/sort_order). Drop sensitive_point_catalog + panchanga_almanac entries. |
| Any consumer reading `brahmagyan.kalapancanga` etc. | EDIT — grep + replace with `bg_ephemeris` form. See §3.4 inventory. |

### §3.3 — Briefs + governance (Phase 3)

| File | Edit type |
|------|-----------|
| `00_ARCHITECTURE/BRAHMA_L0_FOUNDATION_REBUILD_v1_0.md` | EDIT — replace asset_id references with bg_* form; remove sensitive_point/almanac mentions from §3 corpus + §13 state schema |
| `00_ARCHITECTURE/BRAHMA_L0_FOUNDATION_REBUILD_v1_1.md` | EDIT — same as v1.0 |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_A_v1_0.md` | EDIT — replace asset_id references with bg_* form |
| `00_ARCHITECTURE/L0FR_VIMARSAKA_SPECS_v1_0.md` | EDIT — replace asset_id references in checks |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_COCKPIT_V2_IMPL_v1_0.md` | EDIT — replace asset_id references |
| `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_D_v1_0.md` | EDIT — replace `brahma_ontology` table references if any need bg_ontology display |
| `CLAUDE.md` | EDIT — §D snapshot table needs a new canonical artifact entry for BRAHMAGYAN_NAMING_RECONCILIATION; no other changes |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | EDIT — append §2 state block update noting the reconciliation closure |
| `00_ARCHITECTURE/SESSION_LOG.md` | APPEND — session entry for the reconciliation arc |

### §3.4 — Inventory commands (run at Phase 1 open)

```bash
# Long-form asset_id usage
grep -rn "brahmagyan\.\(kalapancanga\|sarani\|sutravali\|samanvaya\|sensitive_point\|shastra\|upaya_kosha\|panchanga_almanac\)" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.md" --include="*.sql" --include="*.yaml" --include="*.json" /Users/Dev/Vibe-Coding/Apps/Madhav | grep -v node_modules | grep -v ".next/" | grep -v "_archive" > /tmp/longform_usage.txt

# Short-form bg_* usage
grep -rn "bg_\(ephemeris\|reference\|texts\|ontology\|text_index\|rules\|almanac\|concordance\|remedies\)" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.md" /Users/Dev/Vibe-Coding/Apps/Madhav | grep -v node_modules | grep -v ".next/" | grep -v "_archive" > /tmp/shortform_usage.txt

# Target table classical_attributions usage
grep -rn "classical_attributions" --include="*.ts" --include="*.tsx" --include="*.py" --include="*.md" --include="*.sql" /Users/Dev/Vibe-Coding/Apps/Madhav | grep -v node_modules | grep -v ".next/" | grep -v "_archive" > /tmp/attributions_usage.txt
```

These three inventories are appendix A of this plan. Phase 1 must regenerate them at open and act on the regenerated list (file set has likely shifted since this brief was authored).

## §4 — Phase 1 — DB reconciliation (today)

**Goal:** prod cockpit reflects the correct 8 L0 assets with truthful names and counts. No source-code or brief edits yet — those land in Phase 2 + 3.

### §4.1 — DB migration

Author `platform/supabase/migrations/<NEXT>_brahmagyan_naming_reconciliation.sql`:

```sql
-- Brahmagyan naming reconciliation — drop legacy long-form rows, install 8 canonical bg_* rows.
-- Reversible via the down-migration at the bottom.
BEGIN;

-- Step 1: Remove legacy entries (long-form IDs + dropped concepts)
DELETE FROM asset_registry WHERE layer = 'brahmagyan' AND asset_id IN (
  'brahmagyan.kalapancanga',
  'brahmagyan.sarani',
  'brahmagyan.sutravali',
  'brahmagyan.samanvaya',
  'brahmagyan.sensitive_point_catalog',
  'brahmagyan.shastra',
  'brahmagyan.upaya_kosha',
  'brahmagyan.panchanga_almanac'
);

-- Step 2: Install 8 canonical bg_* rows
INSERT INTO asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula, volume_explanation, depends_on, scope, is_active) VALUES
  ('bg_ephemeris', 'brahmagyan', 1, 'Graha-sphuṭa', 'Ephemeris (Graha Sphuṭa)',
   'Swiss Ephemeris DE441 — raw astronomical positions for all grahas',
   'postgres_table', 'ephemeris_daily',
   'SELECT count(*) FROM ephemeris_daily',
   'SELECT pg_total_relation_size(''ephemeris_daily'')',
   29200, 'GRAHAS * DATE_RANGE_DAYS',
   '9 grahas × date-range days — structural, no upstream dependency',
   ARRAY[]::text[], 'global', true),

  ('bg_reference', 'brahmagyan', 2, 'Sāraṇī', 'Reference Library',
   'Five reference tables: planets, nakshatras, signs, aspects, vargas — classical constants',
   'postgres_table', 'reference_nakshatras',
   'SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_nakshatras) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas)',
   'SELECT pg_total_relation_size(''reference_nakshatras'')',
   NULL, NULL,
   'Sum of 5 reference table row counts — established at seed; static thereafter',
   ARRAY[]::text[], 'global', true),

  ('bg_texts', 'brahmagyan', 3, 'Śāstrapāṭha', 'Classical Texts',
   'Indexed verse chunks from BPHS, Jaimini Sutram, KP Reader, Tajaka, Phaladeepika, etc.',
   'postgres_table', 'classical_text_chunks',
   'SELECT count(*) FROM classical_text_chunks',
   'SELECT pg_total_relation_size(''classical_text_chunks'')',
   NULL, NULL,
   'Empirical writer output from text ingestion (Stream C); first ingest establishes the count',
   ARRAY[]::text[], 'global', true),

  ('bg_ontology', 'brahmagyan', 4, 'Nāmasaṃgraha', 'Ontology',
   'Canonical entity vocabulary — grahas, signs, houses, nakshatras, dashas, domains + synonyms',
   'postgres_table', 'brahma_ontology',
   'SELECT count(*) FROM brahma_ontology',
   'SELECT pg_total_relation_size(''brahma_ontology'')',
   NULL, NULL,
   'Static vocabulary — count established at seed; used by resolve_entity retrieval tool',
   ARRAY[]::text[], 'global', true),

  ('bg_text_index', 'brahmagyan', 5, 'Śabdakośa', 'Text Index',
   'Embedded subset of classical_text_chunks for hybrid retrieval (vector + lexical + rerank)',
   'postgres_table', 'classical_text_chunks',
   'SELECT count(*) FROM classical_text_chunks WHERE embedding IS NOT NULL',
   'SELECT pg_total_relation_size(''classical_text_chunks'')',
   NULL, NULL,
   'Subset of bg_texts where embedding column is populated — count grows with ingestion',
   ARRAY['bg_texts']::text[], 'global', true),

  ('bg_rules', 'brahmagyan', 6, 'Sūtravālī', 'Rule Base',
   'Classical rules extracted from text chunks via Python regex patterns — verse-traceable',
   'postgres_table', 'sutravali_rules',
   'SELECT count(*) FROM sutravali_rules',
   'SELECT pg_total_relation_size(''sutravali_rules'')',
   NULL, NULL,
   'Empirical writer output from Stream D (regex extraction); count grows with pattern library',
   ARRAY['bg_texts']::text[], 'global', true),

  ('bg_remedies', 'brahmagyan', 7, 'Upāya-kośa', 'Remedy Corpus',
   'Classical remedies: mantras, gemstones, charity, vrata, yantras, puja, tantric, ayurvedic, vastu, behavioral',
   'postgres_table', 'brahma_remedy_corpus',
   'SELECT count(*) FROM brahma_remedy_corpus',
   'SELECT pg_total_relation_size(''brahma_remedy_corpus'')',
   NULL, NULL,
   'YAML-curated corpus loaded via Python; grows with native authoring',
   ARRAY[]::text[], 'global', true),

  ('bg_concordance', 'brahmagyan', 8, 'Samanvaya', 'Concordance',
   'Cross-school agreement/divergence index (BPHS vs Jaimini vs Tajaka vs KP per topic) — DORMANT placeholder',
   'postgres_table', 'classical_attributions',
   'SELECT count(*) FROM classical_attributions',
   'SELECT pg_total_relation_size(''classical_attributions'')',
   NULL, NULL,
   'Future build — registered as dormant. The classical_attributions table is a stub until cross-school divergence work begins.',
   ARRAY['bg_texts']::text[], 'global', true);

COMMIT;

-- Down migration (manual; preserves prior state for rollback)
-- DELETE FROM asset_registry WHERE layer='brahmagyan' AND asset_id LIKE 'bg_%';
-- (Then re-run the prior seed script to restore long-form entries.)
```

### §4.2 — Stub table for dormant Concordance

Author `platform/supabase/migrations/<NEXT+1>_classical_attributions_stub.sql`:

```sql
-- classical_attributions stub — allows bg_concordance to register dormant without count_sql errors
CREATE TABLE IF NOT EXISTS classical_attributions (
  attribution_id BIGSERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  school TEXT NOT NULL,
  stance TEXT NOT NULL,
  source_citation TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (topic, school)
);
CREATE INDEX IF NOT EXISTS idx_classical_attributions_topic ON classical_attributions(topic);
COMMENT ON TABLE classical_attributions IS 'Cross-school agreement/divergence index. DORMANT until cross-school workstream opens.';
```

### §4.3 — Reference library seeder (pure Python)

Author `platform/python-sidecar/brahmagyan/l0_reference_library.py` — see §5 of [[BRAHMAGYAN_NAMING_RECONCILIATION_PHASE1_PASTE]] for the full file body. ~250 lines, BPHS-sourced classical constants, idempotent (ON CONFLICT DO NOTHING).

### §4.4 — Ontology seeder (pure Python)

Author `platform/python-sidecar/brahmagyan/l0_ontology.py` — full file body in the same paste. ~150 lines covering 9 grahas + 27 nakshatras + 12 signs + 12 houses + 5 dashas + 10 domains = ~75 canonical entities with synonyms.

### §4.5 — Verification

After all migrations apply + both seeders run:

```bash
# Cockpit API
curl -s -b "__session=$NATIVE_SESSION" "https://madhav.marsys.in/api/cockpit/stats?chart_id=$CHART_ID" \
  | jq '.data.assets[] | select(.layer == "brahmagyan") | {id: .asset_id, state, rows: .actual_rows}'
```

Expected output:
```
bg_ephemeris   | lit      | 825,084
bg_reference   | lit      | ~96
bg_texts       | lit      | 8,432
bg_ontology    | lit      | ~75
bg_text_index  | lit      | 8,432
bg_rules       | building | 1,213
bg_remedies    | building | 200
bg_concordance | dormant  | 0
```

No `sensitive_point_catalog`. No `panchanga_almanac`. Eight rows. Naming consistent with `asset_names.ts`.

## §5 — Phase 2 — Source-code rename

Author after Phase 1 lands. Concise paste:
- Rewrite `asset_registry_seed.ts` brahmagyan block to match the 8 canonical rows (so future re-runs don't drift)
- Edit `asset_names.ts`: remove `bg_almanac`, rename `bg_ephemeris` sanskrit to "Graha-sphuṭa" + english to "Ephemeris (Graha Sphuṭa)"
- Edit `asset_names.test.ts`: remove `bg_almanac` from l0Keys array, change minimum-key assertion if applicable
- Grep + replace consumer files (output of §3.4 inventory): rename every `brahmagyan.kalapancanga` → `bg_ephemeris` form, etc.

This is mechanical refactor work. ~20-30 file edits. Standard fixup workflow.

## §6 — Phase 3 — Brief + governance rewrites

Author after Phase 2 lands. Concise paste:
- Edit BRAHMA_L0_FOUNDATION_REBUILD_v1_*, Stream A brief, Vimarśaka specs, Cockpit V2 brief, Stream D brief — replace long-form IDs with bg_* form
- Append to CLAUDE.md §D snapshot table (new canonical artifact)
- Append to CURRENT_STATE_v1_0.md §2 state block
- Append to SESSION_LOG.md

Smaller scope — ~10 file edits, no code changes.

## §7 — Rollback strategy

Each phase has a clean rollback:
- **Phase 1 rollback:** run the down-migration block in the SQL file (DELETE bg_* rows) + re-run prior seed script. Cockpit reverts to prior state. ~5 min.
- **Phase 2 rollback:** `git revert` the source-code commit. Tests will fail until DB rolls back too. Prefer rolling back both.
- **Phase 3 rollback:** `git revert` the docs commit. No runtime impact.

Atomic boundaries: never deploy Phase 2 without Phase 1; never deploy Phase 3 without Phase 2.

## §8 — Out of scope

- Sūtravalī expansion (1,213 → 3,000+) — separate workstream
- Upāya-kośa expansion (200 → 500+) — separate workstream
- Building the actual classical_attributions content (cross-school divergence index) — future workstream
- M5-A scope (existing concurrent workstream) — unchanged
- HF1 (pipeline image rebuild) + HF2 (migration 174 apply) — separate delta_deploy

## §9 — Branch + delivery

- Branch: `feature/brahmagyan-naming-reconciliation` (cut from main)
- 3 commits — one per phase
- 1 PR; merge after Phase 3 verifies green
- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavNaming` (operator pre-creates before starting)
- Estimated total: ~3 sessions × 30-45 min each, all autonomous; no synchronous gates

---

*End of brief.*
