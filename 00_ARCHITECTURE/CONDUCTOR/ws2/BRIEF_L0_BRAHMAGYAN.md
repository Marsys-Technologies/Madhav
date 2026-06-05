---
artifact: BRIEF_L0_BRAHMAGYAN.md
canonical_id: WS2_BRIEF_L0
version: 1.0
status: READY_FOR_EXECUTION
session_id: l0-brahmagyan
wave: ws2
authored_by: Conductor (Sutradhara) 2026-06-05
---

# WS-2 Sub-Agent Brief: l0-brahmagyan (L0 Brahmagyan Depth Build)

## §0 — Identity
You are executing session `l0-brahmagyan` of the WS-2 Depth Build.
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavWS2
Branch: feature/ws2-depth-build
Mode: AUTONOMOUS_MODE + RUNTIME_GUARDIAN_MODE

## §1 — Read first
1. /Users/Dev/Vibe-Coding/Apps/MadhavWS2/CLAUDE.md
2. /Users/Dev/Vibe-Coding/Apps/MadhavWS2/00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS2_AUTONOMOUS_ACTIVATION_v1_0.md
3. /Users/Dev/Vibe-Coding/Apps/MadhavWS2/00_ARCHITECTURE/BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md
4. /Users/Dev/Vibe-Coding/Apps/MadhavWS2/00_ARCHITECTURE/CONDUCTOR/brahma/L0_CONTRACT_REGISTRY_SEED_v1_0.md
5. /Users/Dev/Vibe-Coding/Apps/MadhavWS2/00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md

## §2 — Context: what exists and what's missing

**What the thin-slice build left (from brahma/smriti/build_state.yaml, Batches 1-11):**
- `ganita_positions`, `ganita_dashas` — tables created (brahma_ganita.sql), real data populated for Lahiri only
- `ephemeris_daily` — table dropped in baseline (legacy purge); no real ephemeris writer exists
- All L0 tables (reference, ontology, almanac, text_index, classical_texts) — NO writers, NO real data
- The `brahma_pipeline.py` just checks `ephemeris_daily` — does not build it

**The volume gap:**
- ephemeris_daily: 0 rows (table may not exist after the legacy purge — verify)
- reference tables: 0 rows (no writer)
- classical_texts/chunks: 0 rows (no writer)
- ontology: 0 rows (no writer)
- almanac: 0 rows (no writer)
- remedy_corpus: 0 rows (no writer)
- text_index vectors: 0 rows (no writer)

## §3 — Your mission: build each L0 asset to its volume floor

### brahmagyan.ephemeris
**Volume floor:** Daily ephemeris for 1900-01-01 to 2100-12-31 × 10 bodies minimum (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Ascendant) = ~73,000 rows minimum.
**Real minimum for the instrument:** at least the period 1980-01-01 to 2060-12-31 (native's full lifetime + 35 years ahead) = ~29,200 rows × 10 bodies.

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_ephemeris.py`
- Use `pyswisseph` (already in requirements) to compute tropical longitude, lat, speed for each body, each day
- Store in `ephemeris_daily` table — you must create this table (check if it exists first; the baseline dropped the old one)
- ayanamsha_id = "tropical" (tropical at source — ayanamsha derived at read time)
- Key columns: date, body, tropical_longitude, latitude, speed_dps, is_retrograde, computed_at
- Acceptance gate: COUNT(*) >= 29,200 × 10 bodies; spot-check native birth date 1984-02-05 Sun in Capricorn

### brahmagyan.reference
**Volume floor:** all classical lookup tables populated with source_citation on every row:
- Planetary dignities (exaltation/debilitation/mooltrikona) — 9 planets × attributes
- Nakshatra attributes (27 nakshatras × deity/ruler/pada_lords/nature/guna)
- Zodiac sign attributes (12 signs × element/mode/lord/natural_benefic/etc)
- Aspect patterns (classical aspects × orbs)
- Chakra/shodasha varga grid (16 vargas × rules)

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_reference.py`
- Populate from classical sources (BPHS-derived constants — hardcoded, no LLM)
- Create tables: `reference_planets`, `reference_nakshatras`, `reference_signs`, `reference_aspects`, `reference_vargas`
- Every row has `source_citation` = 'BPHS/<chapter>' or similar
- Acceptance: row counts ≥ expected per table; all non-null source_citations

### brahmagyan.ontology
**Volume floor:** all core entity classes with canonical IDs + synonyms:
- Planet entities (9 grahas + 2 nodes) with Sanskrit/English canonical names
- Nakshatra entities (27) with pada mapping
- Sign entities (12) with synonyms
- House entities (12 bhavas) with natural significations
- Dasha system entities (Vimshottari, Yogini, Chara)
- Domain entities (career, marriage, health, wealth, spirituality...)

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_ontology.py`
- Hardcode from classical vocabulary (no LLM generation)
- Create table `brahma_ontology` (entity_class, canonical_id, canonical_name_en, canonical_name_sa, synonyms_jsonb, source_citation)
- Acceptance: resolve('Shani') → Saturn; all 27 nakshatras resolve; COUNT >= 100 entities

### brahmagyan.almanac
**Volume floor:** location-parameterized panchang for the native's birth location (Bhubaneswar, 85.833°E, 20.283°N) for 1980-2060, or at minimum on-demand computation (check if `panchanga_daily` still has data from the Phase-4C build).
**Note:** Check `panchanga_daily` row count first — if the Phase-4C panchang data is still present (73,414 rows), REUSE it. Don't rebuild what's already there.

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_almanac.py`
- If `panchanga_daily` empty: use the existing `panchang_engine` to bootstrap (check `panchang_engine/` module)
- If `panchanga_daily` has rows: just verify + emit build_events
- Acceptance: native birth date 1984-02-05 → tithi=Shukla Tritiya, vara=Ravivara, nakshatra=Purva Bhadrapada

### brahmagyan.texts
**Volume floor:** at a minimum, scaffold the table + ingest 1 verse-addressable text (BPHS is publicly available; Parashara's classic is in public domain). Ingest at minimum 50 verse chunks with verse IDs.
**Licensing note:** Only ingest texts that are public domain or have clear open licensing. Flag any uncertain text in Smriti (Tier-2). For this pass: BPHS (public domain translation by Rishi Kumar Shastri) + Phaladeepika + Jataka Parijata.

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_texts.py`
- Create tables: `classical_texts` (text_id, title, author, school, tier, license) + `classical_text_chunks` (chunk_id, text_id, verse_ref, content_sa, content_en, source_citation)
- Acceptance: at least 50 chunks; each chunk has verse_ref; tool `text.read('BPHS', 'CH1:V1')` resolves

### brahmagyan.text_index
**Volume floor:** vector embeddings for all ingested text chunks.
**Gated sub-step:** The old brahma build ran a C4 embedding spike and used `text-multilingual-embedding-002`. Check if `bodha_signal_embeddings` or `classical_text_chunks` has any existing embeddings. If the embedding model works: bulk embed all chunks.
**Note:** Use Vertex AI `text-embedding-004` or `text-multilingual-embedding-002` (whichever is available in the project). If Vertex AI unavailable: use pgvector with any available embedding endpoint; STUB and park if none available.

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_text_index.py`
- Extend `classical_text_chunks` with `embedding vector(768)` column (or separate table)
- Acceptance: embedding row count = text chunk count; vector similarity search smoke test passes

### brahmagyan.remedy_corpus
**Volume floor:** at least 50 classical upaya (remedial) prescriptions from BPHS/Phala Deepika indexed with planet + domain + remedy_type + mantra/gemstone/charity.
**This is a NEW asset** not in the thin-slice build.

**Implementation:**
- Create `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py`
- Create table `brahma_remedy_corpus` (remedy_id, planet, domain, remedy_type, prescription_text, source_citation, confidence, mantra_text, gemstone, charity_action)
- Seed from classical texts (hardcode representative samples; no LLM generation)
- Acceptance: COUNT >= 50; all rows have source_citation; smoke test returns remedies for 'Saturn' domain 'career'

## §4 — Volume gate protocol

For each asset: compute `actual_rows`, compare to `volume_floor`. If:
- `actual_rows >= floor` → GREEN
- `actual_rows < floor AND actual_rows > 0` → AMBER (log to Smriti; still PASS, not a failure; note the gap)
- `actual_rows == 0 AND asset_buildable` → re-run writer until floor is reached (max 6 attempts per AUTONOMY_RESILIENCE_PATTERN §B.1)
- Licensing block → Tier-2 disposition: park the specific text; continue with others

## §5 — Schema + migration pattern

Check each table first with `psql` before creating a migration. If the table doesn't exist, create a migration file at:
`platform/migrations/ws2_l0_<asset_name>.sql`

Follow the pattern from `brahma_ganita.sql`:
- IF NOT EXISTS guards
- ROLLBACK comment block at top
- COMMENT ON TABLE

## §6 — Commit pattern

After each asset builds and passes its volume gate:
```bash
git -C /Users/Dev/Vibe-Coding/Apps/MadhavWS2 add platform/python-sidecar/brahmagyan/l0_<asset>.py platform/migrations/ws2_l0_<asset>.sql
git -C /Users/Dev/Vibe-Coding/Apps/MadhavWS2 commit -m "feat(ws2/l0): <asset> volume floor met [l0-brahmagyan]"
```

## §7 — Pipeline integration

After all L0 assets pass their volume gates, update `brahma_pipeline.py`'s `_l0_check()` to:
1. Call each L0 writer's `check_volume()` function (that returns actual_rows vs floor)
2. Bootstrap any missing data
3. Return a structured result per asset (not just a count)

## §8 — Final output block

Emit EXACTLY this block as your final message:
---FINAL_SUMMARY---
session_id: l0-brahmagyan
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha>
assets_passed: [brahmagyan.ephemeris, brahmagyan.reference, ...]
assets_parked: [brahmagyan.rules, ...]
volume_floors_met:
  - brahmagyan.ephemeris: actual/floor
  - brahmagyan.reference: actual/floor
  - brahmagyan.texts: actual/floor
  - brahmagyan.text_index: actual/floor
  - brahmagyan.ontology: actual/floor
  - brahmagyan.almanac: actual/floor
  - brahmagyan.remedy_corpus: actual/floor
notes_for_orchestrator: >
  <one paragraph>
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
