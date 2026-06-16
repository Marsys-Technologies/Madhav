---
brief_id: EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES
version: 1.1
status: COMPLETE
amended_at: 2026-04-28 — v1.1: GCS path corrections (L1/facts, L1/ephemeris, L1/sources per GCS_LAYOUT_v1_0); added Stream D.0 CSV pre-sync
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code (multi-session — see Execution model)
trigger_phrase: "Read EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md and execute it."
phase: 14C
phase_name: L1 Structured Tables — chart_facts, ephemeris_daily, eclipses, retrogrades, life_events, sade_sati_phases
risk_classification: HIGH (six new tables; structured extraction from markdown; Swiss Ephemeris bootstrap of ~73K daily rows; tool surface added to runtime — extraction errors and timezone bugs are silent and consequential)
parallelizable_with: [14D, 14E (execution — disjoint table sets); 14F.2 if any]
must_complete_before: [14G]
depends_on:
  - EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md (COMPLETE — writer abstraction + staging-then-swap discipline must be in place)
output_artifacts:
  - 00_ARCHITECTURE/L1_STRUCTURED_LAYER_v1_0.md (NEW canonical spec)
  - 00_ARCHITECTURE/PHASE_14C_L1_STRUCTURED_TABLES_REPORT_v1_0.md (NEW execution report)
  - 01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml (NEW canonical structured projection of FORENSIC v8.0)
---

# EXEC_BRIEF — Phase 14C — L1 Structured Tables

## Mission

Project the L1 Facts Layer from markdown-only into structured Postgres tables that the LLM router can query as deterministic tools. After 14C, queries like "what was Saturn's longitude on 2018-03-15?" or "find every life event in the 7th-house transit windows of 2019–2022" stop relying on embedding-search guesses and start hitting indexed tables with provenance. Six tables, one canonical YAML extraction of the natal chart, six new pipeline writers, and seven new LLM-callable tools.

This is the largest brief in the Phase 14 modernization. **It is intended to be executed across multiple Claude Code sessions** — each Stream is a session boundary. The brief is a single document so you can see the whole scope; the executor opens fresh sessions per Stream rather than bundling.

Three architectural commitments:

1. **Markdown stays canonical for authoring; Postgres becomes canonical for runtime.** The `01_FACTS_LAYER/*.md` files remain the source-of-truth that humans edit. The `01_FACTS_LAYER/STRUCTURED/*.yaml` extracts and the Postgres tables are *projections* of that truth. The pipeline (14B) rebuilds projections from authored markdown on every run.

2. **Swiss Ephemeris is the authority for ephemeris data.** The 1900–2100 monthly CSV at `01_FACTS_LAYER/EPHEMERIS_MONTHLY_1900_2100.csv` is reduced to a verification check, NOT the source. `ephemeris_daily` is computed by `pyswisseph` (or `swisseph`) at daily resolution for 1900-01-01 through 2100-12-31, ~73K rows × 9 graha = ~660K row-events. CSV becomes the spot-check.

3. **Tools are versioned + provenance-tagged.** Every tool returns rows with `source_uri`, `source_version`, `derivation`, `computed_at`. The runtime can show the LLM "this number came from FORENSIC v8.0 §4.1 row 12" or "this was computed via Swiss Ephemeris at build_id=build-...". B.10 (no fabricated computation) becomes structurally enforced.

This brief explicitly does NOT alter `platform/src/**` UI components beyond adding tool dispatchers to the existing tool-registry. No feature-flag changes. Runtime keeps reading from `rag_chunks`; new tool calls are additive surfaces, opt-in via router selection.

## Pre-flight gate

1. Verify Phase 14B is COMPLETE — frontmatter check on `EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md`. Confirm `IBuildWriter` interface exists at `platform/python-sidecar/pipeline/writers/base.py`.
2. Verify `marsys-build-pipeline-job` exists in Cloud Run and at least one successful build manifest exists in `gs://madhav-marsys-build-artifacts/`.
3. Verify `pyswisseph` (or `swisseph`) is installable in the pipeline image — check current `requirements.txt` doesn't conflict.
4. Verify the canonical L1 sources are present in GCS. **Path scheme is layer-prefix per `00_ARCHITECTURE/GCS_LAYOUT_v1_0.md`, NOT the legacy directory-prefix:**
   - `gs://madhav-marsys-sources/L1/facts/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`
   - `gs://madhav-marsys-sources/L1/facts/LIFE_EVENT_LOG_v1_2.md`
   - `gs://madhav-marsys-sources/L1/facts/SADE_SATI_CYCLES_ALL.md`
   - `gs://madhav-marsys-sources/L1/sources/EVENT_CHART_STATES_v1_0.md`
   - `gs://madhav-marsys-sources/L1/sources/JHORA_TRANSCRIPTION_v8_0_SOURCE.md`
   - The three CSVs at `L1/ephemeris/*` are **expected to be empty/missing** at this point — they are coverage gaps. Stream D.0 below uploads them. Do NOT halt pre-flight on missing CSVs; they're not in the CURRENT-asset set.
5. Verify Cloud SQL `amjis-postgres` migrations through 013 (14B's migration) are applied.
6. Confirm git working tree clean.

If any fail, halt with actionable message.

## Scope

**`may_touch` (filesystem / git):**
- `platform/supabase/migrations/014_chart_facts.sql`
- `platform/supabase/migrations/015_ephemeris_daily.sql`
- `platform/supabase/migrations/016_eclipses_retrogrades.sql`
- `platform/supabase/migrations/017_life_events_and_sade_sati.sql`
- `platform/python-sidecar/pipeline/writers/chart_facts_writer.py` (NEW)
- `platform/python-sidecar/pipeline/writers/ephemeris_writer.py` (NEW)
- `platform/python-sidecar/pipeline/writers/eclipses_writer.py` (NEW)
- `platform/python-sidecar/pipeline/writers/retrogrades_writer.py` (NEW)
- `platform/python-sidecar/pipeline/writers/life_events_writer.py` (NEW)
- `platform/python-sidecar/pipeline/writers/sade_sati_writer.py` (NEW)
- `platform/python-sidecar/pipeline/extractors/forensic_extractor.py` (NEW — markdown → YAML)
- `platform/python-sidecar/pipeline/extractors/life_event_extractor.py` (NEW)
- `platform/python-sidecar/pipeline/extractors/sade_sati_extractor.py` (NEW)
- `platform/python-sidecar/pipeline/bootstrap_ephemeris.py` (NEW — one-time Swiss Ephemeris compute)
- `platform/src/lib/tools/structured/` (NEW directory):
  - `query_chart_fact.ts`, `query_planet_position.ts`, `query_eclipse_window.ts`, `query_retrograde_window.ts`, `query_life_events.ts`, `query_sade_sati.ts`, `query_dasha.ts`
- `platform/src/lib/tools/registry.ts` (additive — register the 7 new tools)
- `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` (NEW — canonical structured projection of FORENSIC v8.0; native-validated)
- `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json` (NEW — JSON Schema for the YAML)
- `01_FACTS_LAYER/CLAUDE.md` (additive update — STRUCTURED/ subdirectory pointer)
- `00_ARCHITECTURE/L1_STRUCTURED_LAYER_v1_0.md` (NEW — canonical spec)
- `00_ARCHITECTURE/PHASE_14C_L1_STRUCTURED_TABLES_REPORT_v1_0.md` (NEW — execution report)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (additive — six new table entries; YAML extraction entry; tool registry entries; STATUS: TRANSITIONAL until 14G lockdown)

**`must_not_touch`:**
- `platform/python-sidecar/pipeline/main.py` orchestrator (14C plugs in writers via the registry pattern, does NOT modify orchestrator core).
- `platform/python-sidecar/rag/chunkers/*.py`, `rag/embed.py` — owned by 14B, unchanged.
- `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — markdown stays canonical authoring source; only an *extraction* gets created in STRUCTURED/. If FORENSIC needs a content fix, that's a separate brief.
- `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`, `SADE_SATI_CYCLES_ALL.md`, the CSVs — read-only inputs.
- Existing rag_chunks/rag_embeddings tables — schema unchanged (14B owns those).
- Any feature flag.
- Any L2/L2.5/L3 governance doc.

## Execution model — multi-session

Streams A–H map roughly 1:1 to Claude Code sessions. **Do NOT attempt all eight in one session.** Recommended order (sequential where dependencies exist; parallel where noted):

| Order | Stream | Session # | Parallel-safe with |
|---|---|---|---|
| 1 | A — Schema migrations 014–017 | 1 | (none — foundation) |
| 2 | B — FORENSIC structured extraction → YAML | 2 | C, D, E (no shared files) |
| 2 | C — Ephemeris bootstrap via Swiss Ephemeris | 3 | B, D, E |
| 2 | D — Eclipses + retrogrades CSV ingest | 4 | B, C, E |
| 2 | E — Life events + sade sati extraction | 5 | B, C, D |
| 3 | F — Pipeline writers plugged into 14B | 6 | (gated on A–E done) |
| 4 | G — Tool implementations + router registry | 7 | (gated on F done) |
| 5 | H — End-to-end verification + close report | 8 | (final) |

Each session opens, reads this brief + the relevant Stream, executes, commits, closes. The 14C report at Stream H is the umbrella close.

## Sub-streams

### Stream A — Schema migrations 014–017

Author four migrations. All wrapped in `BEGIN ... COMMIT`. Each table includes `build_id` (FK to `build_manifests`) and `provenance` JSONB so every row knows which build produced it.

**`014_chart_facts.sql`** (chart_facts is a key-value-with-context store; flexible enough for natal chart + KP cusps + sahams + yogas + special lagnas):

```sql
BEGIN;
CREATE TABLE IF NOT EXISTS chart_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fact_id TEXT UNIQUE NOT NULL,           -- 'PLN.JUP.LON_DEG' | 'CUSP.07.STAR_LORD' | 'SAHAM.PUNYA' | 'YOGA.GAJAKESARI'
  category TEXT NOT NULL,                 -- 'planet'|'house'|'cusp'|'saham'|'yoga'|'special_lagna'|'dasha_balance'
  divisional_chart TEXT NOT NULL DEFAULT 'D1', -- 'D1'|'D9'|'D10'|'D60'|'D7'|'D12'|... (28 standard varga)
  value_text TEXT,                        -- string value (e.g., 'Sagittarius', 'Jupiter')
  value_number NUMERIC,                   -- numeric value (e.g., 87.456789 for longitude)
  value_json JSONB,                       -- structured value (e.g., {sign:'Sgr', degree:27, minute:24})
  source_section TEXT NOT NULL,           -- '§4.1 row 12' | '§12.1' | '§26'
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL,              -- {source_uri, source_version, source_hash, extracted_at, extraction_method}
  is_stale BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chart_facts_category ON chart_facts(category, divisional_chart);
CREATE INDEX idx_chart_facts_fact_id ON chart_facts(fact_id);
CREATE TABLE IF NOT EXISTS chart_facts_staging (LIKE chart_facts INCLUDING ALL);
COMMIT;
```

**`015_ephemeris_daily.sql`** (Swiss Ephemeris computed; one row per (date, planet)):

```sql
BEGIN;
CREATE TABLE IF NOT EXISTS ephemeris_daily (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  planet TEXT NOT NULL,                   -- 'sun'|'moon'|'mars'|'mercury'|'jupiter'|'venus'|'saturn'|'rahu'|'ketu'
  longitude_deg NUMERIC(11,7) NOT NULL,   -- 0.0000000 - 359.9999999, sidereal Lahiri
  latitude_deg NUMERIC(11,7),
  speed_deg_per_day NUMERIC(11,7) NOT NULL,
  is_retrograde BOOLEAN NOT NULL,
  sign TEXT NOT NULL,                     -- derived: 'Aries'|'Taurus'|...
  sign_degree NUMERIC(11,7) NOT NULL,     -- 0-30
  nakshatra TEXT NOT NULL,                -- 'Ashwini'|...
  nakshatra_pada SMALLINT NOT NULL,       -- 1-4
  ayanamsha TEXT NOT NULL DEFAULT 'lahiri',
  ephemeris_version TEXT NOT NULL,        -- 'pyswisseph-2.10.03.2' or similar
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(date, planet)
);
CREATE INDEX idx_ephemeris_date ON ephemeris_daily(date);
CREATE INDEX idx_ephemeris_planet_date ON ephemeris_daily(planet, date);
CREATE INDEX idx_ephemeris_retro ON ephemeris_daily(planet, date) WHERE is_retrograde = TRUE;
CREATE TABLE IF NOT EXISTS ephemeris_daily_staging (LIKE ephemeris_daily INCLUDING ALL);
COMMIT;
```

**`016_eclipses_retrogrades.sql`**:

```sql
BEGIN;
CREATE TABLE IF NOT EXISTS eclipses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL,
  type TEXT NOT NULL,                     -- 'solar_total'|'solar_partial'|'solar_annular'|'lunar_total'|'lunar_penumbral'|'lunar_partial'
  longitude_deg NUMERIC(11,7),            -- node longitude at maximum
  sign TEXT,
  nakshatra TEXT,
  visibility_region TEXT,                 -- free-text geographic note from CSV
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  source_uri TEXT NOT NULL,
  UNIQUE(date, type)
);
CREATE INDEX idx_eclipses_date ON eclipses(date);
CREATE TABLE IF NOT EXISTS eclipses_staging (LIKE eclipses INCLUDING ALL);

CREATE TABLE IF NOT EXISTS retrogrades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  planet TEXT NOT NULL,
  station_type TEXT NOT NULL CHECK (station_type IN ('retrograde_start', 'retrograde_end')),
  date DATE NOT NULL,
  longitude_deg NUMERIC(11,7),
  sign TEXT,
  nakshatra TEXT,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  source_uri TEXT NOT NULL,
  UNIQUE(planet, station_type, date)
);
CREATE INDEX idx_retrogrades_date ON retrogrades(date);
CREATE INDEX idx_retrogrades_planet_date ON retrogrades(planet, date);
CREATE TABLE IF NOT EXISTS retrogrades_staging (LIKE retrogrades INCLUDING ALL);
COMMIT;
```

**`017_life_events_and_sade_sati.sql`**:

```sql
BEGIN;
CREATE TABLE IF NOT EXISTS life_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id TEXT UNIQUE NOT NULL,          -- 'EVT.MARRIAGE_2014_05', 'EVT.JOB_CHANGE_2019_03'
  event_date DATE NOT NULL,
  category TEXT NOT NULL,                 -- 'marriage'|'career'|'health'|'family'|'spiritual'|'travel'|'finance'
  description TEXT NOT NULL,
  significance TEXT,                      -- 'major'|'moderate'|'minor'
  chart_state JSONB NOT NULL,             -- pre-computed transit + dasha state at event time (Swiss Ephemeris from LEL v1.2)
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  provenance JSONB NOT NULL
);
CREATE INDEX idx_life_events_date ON life_events(event_date);
CREATE INDEX idx_life_events_category ON life_events(category, event_date);
CREATE TABLE IF NOT EXISTS life_events_staging (LIKE life_events INCLUDING ALL);

CREATE TABLE IF NOT EXISTS sade_sati_phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_number SMALLINT NOT NULL,         -- 1, 2, 3 (lifetime cycles)
  phase TEXT NOT NULL CHECK (phase IN ('pre_birth', 'rising', 'peak', 'setting', 'gap')),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  saturn_sign_at_start TEXT NOT NULL,
  notes TEXT,
  source_section TEXT NOT NULL,
  build_id TEXT NOT NULL REFERENCES build_manifests(build_id),
  UNIQUE(cycle_number, phase, start_date)
);
CREATE INDEX idx_sade_sati_dates ON sade_sati_phases(start_date, end_date);
CREATE TABLE IF NOT EXISTS sade_sati_phases_staging (LIKE sade_sati_phases INCLUDING ALL);
COMMIT;
```

Apply all four. Record migration timestamps + checksums.

### Stream B — FORENSIC v8.0 → CHART_FACTS_EXTRACTION_v1_0.yaml

**This is the highest-risk stream in the brief.** FORENSIC v8.0 is 11,394 lines of dense markdown with 32 sections covering natal chart, KP cusps, all dasha systems, sahams, yogas, special lagnas. Manual extraction is impossibly slow; pure regex will miss things; pure LLM-extract will hallucinate. Use a hybrid:

1. **LLM-assisted draft extraction.** Run `forensic_extractor.py` over each section. Use Claude Sonnet 4.6 with a strict JSON-schema-validated prompt that emits one fact per response. Schema enforced via Pydantic.
2. **Validation pass.** Every extracted fact must:
   - Have `source_section` resolvable (line range in FORENSIC must contain a quoted snippet matching value).
   - Pass type checks (numbers parseable; signs in canonical list of 12; nakshatras in canonical 27).
3. **Diff-against-known.** Cross-check every extracted natal-chart fact against `01_FACTS_LAYER/SOURCES/EVENT_CHART_STATES_v1_0.md` (which has Swiss Ephemeris natal computation). Mismatch >0.001° = halt; surface as finding.
4. **Native validation gate.** Output a side-by-side "FORENSIC text snippet | extracted fact" report at `verification_artifacts/PHASE_14C/forensic_extraction_review.html`. Open in browser, native validates. Any disagreement marked → re-extract.
5. **Freeze.** Once native confirms, the YAML at `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` is committed and treated as canonical (extraction does NOT re-run on every pipeline build; it runs only on FORENSIC version bumps).

YAML structure:
```yaml
schema_version: 1.0
source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md
extracted_at: 2026-04-28
extracted_by: forensic_extractor.py v1.0 + native validation
facts:
  - fact_id: PLN.SUN.LON_DEG
    category: planet
    divisional_chart: D1
    value_number: 322.84
    value_json: {sign: Aquarius, degree: 22, minute: 50}
    source_section: "§3.1 row 1"
    extraction_method: regex+llm
  - fact_id: CUSP.07.STAR_LORD
    category: cusp
    divisional_chart: D1
    value_text: Mercury
    source_section: "§4.1 row 7"
    ...
```

Author the JSON Schema at `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_SCHEMA_v1_0.json` describing this shape.

### Stream C — Ephemeris bootstrap (Swiss Ephemeris)

Author `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`. One-time job that:

1. Initializes `pyswisseph` with sidereal Lahiri ayanamsha (`swe.set_sid_mode(swe.SIDM_LAHIRI)`).
2. Iterates 1900-01-01 → 2100-12-31 daily.
3. For each date, computes for each of 9 graha (sun, moon, mars, mercury, jupiter, venus, saturn, rahu — true node — , ketu — derived as rahu + 180°):
   - longitude_deg, latitude_deg, speed_deg_per_day
   - is_retrograde (speed < 0; rahu/ketu always retrograde by convention — use `True`)
   - Derived: sign (1-12), sign_degree (0-30), nakshatra (1-27), nakshatra_pada (1-4)
4. Writes to `ephemeris_daily_staging` in batches of 10K rows.
5. Verification step: read the monthly CSV at `gs://madhav-marsys-sources/L1/ephemeris/EPHEMERIS_MONTHLY_1900_2100.csv` (uploaded in Stream D.0 below) and spot-check 100 random month-start dates. Any longitude delta >0.01° = halt; surface as finding (Swiss Ephemeris vs CSV authority disagreement). If CSV is genuinely empty/missing because Stream D.0 hasn't run yet, skip the cross-check, mark it as a residual for Stream H, and proceed (Swiss Ephemeris remains the authority).
6. After verification passes: log row count, manifest entry, exit.

Total compute: ~73,050 days × 9 planets = ~657K rows. Swiss Ephemeris is fast (~10-20K computations/sec); whole job is single-digit minutes.

Cloud Run Job tuning: this job is compute-heavy, not memory-heavy. Bump `--cpu=4 --memory=2Gi` for this specific run. The standard pipeline doesn't need this; it's a one-shot bootstrap.

Run idempotency: if `ephemeris_daily` already has rows for `build_id`, skip and exit 0. If different build_id, refuse and surface (ephemeris is computed once and is derivation-stable; rebuilding is a manual decision).

### Stream D — Eclipses + retrogrades CSV ingest

**Stream D.0 — CSV pre-sync** (runs before D proper).

Per `GCS_LAYOUT_v1_0.md`, `gs://madhav-marsys-sources/L1/ephemeris/` is reserved but empty — the three CSVs (`EPHEMERIS_MONTHLY_1900_2100.csv`, `ECLIPSES_1900_2100.csv`, `RETROGRADES_1900_2100.csv`) exist locally at the legacy path `01_FACTS_LAYER/` but were not synced because they were tagged DEAD_DATA in `VALIDATED_ASSET_REGISTRY_v1_0.json`. 14C re-classifies them as TRANSITIONAL (authority sources for `eclipses_daily`/`retrogrades` tables) and uploads.

Steps:
1. Update `VALIDATED_ASSET_REGISTRY_v1_0.json`: flip the 3 CSV entries from `status: DEAD_DATA` to `status: TRANSITIONAL`, add `gcs_uri: gs://madhav-marsys-sources/L1/ephemeris/<filename>`, and add a `phase_14c_promotion_note: "Promoted to TRANSITIONAL — authority source for eclipses + retrogrades tables. Phase 14C Stream D.0 2026-04-28"`.
2. Re-run `gcs_sync.py` (from Phase 14A) — idempotent; uploads the 3 newly-CURRENT/TRANSITIONAL CSVs to `gs://madhav-marsys-sources/L1/ephemeris/`.
3. Verify upload: `gcloud storage ls gs://madhav-marsys-sources/L1/ephemeris/` returns 3 entries.
4. Commit the registry update separately from the writers (smaller blast radius).

**Stream D proper** — Author `eclipses_writer.py` and `retrogrades_writer.py`. Each:

1. Fetches the source CSV from GCS sources bucket at `gs://madhav-marsys-sources/L1/ephemeris/`.
2. Parses with Pandas; validates column types via Pydantic models.
3. Writes to staging table with `build_id` + provenance.

Eclipse CSV schema: date, type (parse free-text → enum), longitude (parse degree string → numeric), sign (12-list), nakshatra (27-list), visibility note.

Retrograde CSV schema: planet, station date, station type, longitude, sign, nakshatra. CSV may not have all columns — handle gracefully with NULL where missing.

Sanity gates:
- Eclipse count: expect ~400-500 eclipses across 1900-2100 (2-5/year). >1000 or <300 = halt and surface.
- Retrograde count: expect ~5-7 retrograde stations/planet/year × 5 planets × 200 years = ~5K-7K stations. >10K or <3K = halt.

### Stream E — Life events + sade sati extraction

**Life events** (`life_event_extractor.py`):
1. Parse `LIFE_EVENT_LOG_v1_2.md` frontmatter + structured event blocks. Each event has frontmatter `event_id`, `date`, `category`, `description` (per LEL v1.2 schema).
2. For each event, extract `chart_state` from the corresponding entry in `SOURCES/EVENT_CHART_STATES_v1_0.md` (Swiss Ephemeris snapshot).
3. Validate: 36 events expected (per LEL v1.2 close).
4. Write to `life_events_staging`.

**Sade sati** (`sade_sati_extractor.py`):
1. Parse `SADE_SATI_CYCLES_ALL.md`. The file describes 4 cycle blocks (pre-birth + 3 lifetime cycles), each with rising/peak/setting phases.
2. Extract start_date, end_date for each phase.
3. Compute Saturn's sign at the start of each phase (cross-check via ephemeris_daily once Stream C is done; if Stream E runs before C, use the value asserted in the markdown and flag for cross-check in Stream H).
4. Write to `sade_sati_phases_staging`.

### Stream F — Pipeline writers plugged into 14B

For each table-and-source pair, implement a writer at `platform/python-sidecar/pipeline/writers/<name>_writer.py` that:

1. Inherits `IBuildWriter` from 14B's `writers/base.py`.
2. Overrides `write_chunks` (renamed `write_rows` for non-chunk writers — extend the interface in 14C to support both).
3. Implements:
   - `read_source(source_uri) → list[Row]` (reads YAML/CSV/markdown extraction)
   - `validate(rows) → ValidationResult` (Pydantic validation)
   - `write_to_staging(rows, build_id) → WriteResult` (INSERT to *_staging table)
   - `validate_staging(build_id) → ValidationResult` (row count, FK integrity)
   - `swap_to_live(build_id) → SwapResult` (transactional DELETE+INSERT, fingerprint update)
4. Gets registered in `pipeline/main.py`'s writer registry: `{'chart_facts': ChartFactsWriter, 'ephemeris_daily': EphemerisWriter, ...}`

Note: extending `IBuildWriter` to handle non-chunk rows requires a small interface evolution. Document it; do NOT break existing `RAGChunksWriter`. Pattern:
```python
class IBuildWriter(ABC):
    @abstractmethod
    def write_to_staging(self, rows: list[Any], build_id: str) -> WriteResult: ...
    @abstractmethod
    def validate_staging(self, build_id: str) -> ValidationResult: ...
    @abstractmethod
    def swap_to_live(self, build_id: str) -> SwapResult: ...
```
14B's `RAGChunksWriter` is refactored (minor) to fit this signature; the existing chunks-and-embeddings combo becomes the rows.

Apply same 0.5× swap threshold from 14B to each new writer's swap.

### Stream G — Tool implementations + router registry

Author seven tools at `platform/src/lib/tools/structured/`:

| Tool | Inputs | Returns |
|---|---|---|
| `query_chart_fact` | `fact_id` OR `(category, divisional_chart)` | matching rows from chart_facts |
| `query_planet_position` | `date`, `planet` | one row from ephemeris_daily |
| `query_eclipse_window` | `start_date, end_date, type?` | rows from eclipses |
| `query_retrograde_window` | `start_date, end_date, planet?` | rows from retrogrades |
| `query_life_events` | `category?`, `date_range?` | rows from life_events |
| `query_sade_sati` | `date` | active sade_sati_phases rows |
| `query_dasha` | `date`, `system?` ('vimsottari'|'yogini'|'ashtottari') | active dasha levels (mahadasha/antardasha/pratyantardasha) — note: this requires dasha tables which are `chart_facts` rows where category='dasha_balance', PLUS computed propagation from natal balance to query date. Simple wrapper around vimsottari math; reuse existing if present in `platform/python-sidecar/rag/` or implement minimally. |

Each tool:
- Validates inputs via zod.
- Queries Cloud SQL with parameterized SQL.
- Returns rows + provenance metadata.
- Logs the call with audit_id (so audit replay can reconstruct).

Register all seven in `platform/src/lib/tools/registry.ts`. The router (Phase 11A onward) gets visibility automatically. Tool descriptions matter: write them so an LLM can choose the right tool from a query like "what was Saturn doing on 2018-03-15?" → `query_planet_position(date=2018-03-15, planet=saturn)`.

### Stream H — End-to-end verification + close report

1. Trigger a full pipeline run end-to-end:
   ```bash
   gcloud run jobs execute marsys-build-pipeline-job \
     --args=--triggered-by=manual:phase-14c-eod-verification \
     --region=asia-south1 --wait
   ```
2. Verify all six staging tables populated; counts:
   - `chart_facts_staging`: ~500-1500 rows (depends on FORENSIC density)
   - `ephemeris_daily_staging`: ~657K rows (don't re-run if Stream C was already a one-shot — check existing live count)
   - `eclipses_staging`: 400-700 rows
   - `retrogrades_staging`: 4K-8K rows
   - `life_events_staging`: 36 rows exactly
   - `sade_sati_phases_staging`: 8-12 rows (4 cycles × 2-3 phases)
3. Swap to live; verify each `*_staging` is empty post-swap and `*` has the staged counts.
4. Run each new tool against a known query; compare to truth:
   - `query_chart_fact('PLN.SUN.LON_DEG')` → matches FORENSIC §3.1
   - `query_planet_position(date='1984-02-05', planet='saturn')` → matches the natal Saturn longitude in FORENSIC §3.1
   - `query_life_events(category='marriage')` → returns 1 row matching LEL EVT.MARRIAGE
   - `query_sade_sati(date='2020-06-15')` → returns Cycle 2 peak phase
5. Run validators: `schema_validator`, `drift_detector`, `mirror_enforcer`. Capture exit codes; compare against 14F.1 baseline (70 / 136 / 0). New violations = surface as finding for 14G.
6. Author `00_ARCHITECTURE/L1_STRUCTURED_LAYER_v1_0.md` covering schemas, tool surface, extraction methodology, runbook for re-extraction (when FORENSIC bumps), idempotency rules.
7. Author `00_ARCHITECTURE/PHASE_14C_L1_STRUCTURED_TABLES_REPORT_v1_0.md` covering Stream-by-Stream outcomes, row counts, validator deltas, native validation results from Stream B, residuals.
8. Update `01_FACTS_LAYER/CLAUDE.md` to point at `STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` as the structured projection.
9. Update `CAPABILITY_MANIFEST.json` with all new entries; rotate fingerprint.
10. Atomic commit per Stream; final umbrella commit at H. Title: `Phase 14C: L1 Structured Tables — chart_facts, ephemeris, eclipses, retrogrades, life_events, sade_sati`.

## Done criteria

1. Migrations 014–017 applied and reflected in `pg_migrations`.
2. `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` exists; passes `CHART_FACTS_SCHEMA_v1_0.json`; native-validated.
3. `ephemeris_daily` has ~657K rows spanning 1900–2100 daily for 9 planets; Lahiri sidereal; Swiss Ephemeris-computed; CSV cross-check ≤0.01° delta on 100 spot-checks.
4. `eclipses` and `retrogrades` populated within sanity ranges.
5. `life_events` has exactly 36 rows; chart_state hydrated from EVENT_CHART_STATES.
6. `sade_sati_phases` has 8–12 rows across 4 cycles.
7. All six writers integrated into the 14B pipeline; full pipeline run produces all six tables with manifest tracking.
8. Seven LLM tools implemented, registered, and unit-tested against the four spot-check queries listed in Stream H step 4.
9. `L1_STRUCTURED_LAYER_v1_0.md` + `PHASE_14C_L1_STRUCTURED_TABLES_REPORT_v1_0.md` exist.
10. Validator deltas vs 14F.1 baseline are documented (no silent drift).
11. CAPABILITY_MANIFEST.json updated and fingerprint rotated.
12. All commits land on the working branch.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM-assisted FORENSIC extraction hallucinates a fact | Medium | HIGH | Native validation gate in Stream B 4 + cross-check against EVENT_CHART_STATES truth in Stream B 3. Halt on >0.001° natal mismatch. |
| Ayanamsha mismatch (Lahiri vs another) between Swiss Ephemeris and CSV | Medium | HIGH | Stream C 5 spot-checks 100 dates against CSV; halt on >0.01° delta; if delta is ayanamsha-systematic, surface and force native decision before swap. |
| Timezone bug in life_events extraction (LEL has IST + UTC; chart_state typed in UTC) | Medium | Medium | Pydantic models enforce explicit timezone on every datetime; raise on ambiguous parse. EVT.* with no timezone = surface. |
| Ephemeris job times out at 30m on Cloud Run Job | Low | Low | Bump task-timeout to 60m for this one-shot via `--task-timeout=60m` in the Cloud Run Job execute command. |
| `IBuildWriter` interface evolution breaks 14B's `RAGChunksWriter` | Medium | Medium | Stream F mandates a refactor of `RAGChunksWriter` to the new signature; unit tests for it run before any 14C writer is wired. |
| Tool descriptions are too generic; router can't choose the right tool | Medium | Medium | Stream G includes test queries (Stream H step 4) that exercise router selection; if the wrong tool is chosen, descriptions get sharpened in a follow-up. |
| Sade sati phase boundaries differ between markdown and ephemeris (Saturn sign computation) | Medium | Medium | Stream H step 4 cross-checks; if mismatch, prefer ephemeris-computed boundaries and flag the markdown for native review (a separate brief). |
| 657K-row ephemeris swap stalls the HNSW reindex on `rag_embeddings` (unrelated table — should not interact) | Low | Low | They're separate tables with separate indices. Verify in Stream H. |
| Stream B's extraction takes longer than one Claude Code session can hold | Medium | Low | Decompose Stream B into sub-sections (one per FORENSIC §) if a single session can't hold it. Each sub-section commits independently. |

## Concurrency declaration

**Parallel-with**:
- Streams B/C/D/E within 14C — disjoint files, can run in 4 parallel Claude Code sessions after Stream A completes.
- 14D execution (L2.5 parity) — disjoint Postgres tables, disjoint writers.
- 14E execution (L3 registers) — disjoint Postgres tables, disjoint writers.

**Must complete before**:
- 14G lockdown — needs all six L1 structured tables populated and all seven tools registered.

**Shared-file vigilance**:
- `pipeline/main.py` writer registry — 14C, 14D, 14E all add entries. Edits are append-only; rebase if conflict.
- `CAPABILITY_MANIFEST.json` — additive; rebase if conflict.
- `IBuildWriter` interface in `writers/base.py` — Stream F evolves the interface; 14D/14E will inherit. Land Stream F before 14D/14E start.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md and execute it."

## Notes for the executor

- **This is a multi-session brief.** Do not attempt all 8 streams in one session. Open a fresh session per stream after committing the previous one. The brief is a single doc for legibility, not a single execution unit.
- **Stream B is where the project's discipline gets tested.** LLM extraction is fast but unverifiable without the cross-check + native validation gates. Do NOT skip Stream B step 4 (native review) — even if the extraction "looks right," the cross-check + manual review is what makes the YAML canonical. A wrong fact in chart_facts becomes a wrong tool result becomes a wrong LLM answer at runtime; we cannot afford that.
- **Stream C produces the largest data artifact in the project to date** (~657K rows). Verify the table fits comfortably in Cloud SQL's allocated storage before committing.
- **Tool descriptions matter more than tool implementations.** A correct tool with a vague description = the router won't call it. Spend time on each tool's description string in `registry.ts`.
- **Phase 14D and 14E build on 14C's writer pattern.** Resist the urge to special-case writers in 14C; the abstraction should generalize. Stream F's interface evolution is load-bearing.
- **The EXTERNAL_COMPUTATION_REQUIRED markers throughout FORENSIC** — many of these resolve once `query_planet_position` exists (transit-position queries) and `query_dasha` exists (dasha-state queries). Stream H should trial-run these queries against a few flagged FORENSIC sections to confirm the marker is now resolvable.
