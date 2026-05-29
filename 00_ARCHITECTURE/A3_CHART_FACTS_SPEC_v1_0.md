---
artifact: A3_CHART_FACTS_SPEC_v1_0.md
document: A3 — chart_facts Table Schema Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed across 4 rounds of clarification)
intended_for: Claude Code sub-agents implementing A3 + downstream A4-A14 writers
prime_directive: Only computed facts. No narrative, no opinion, no judgement. Schema enforces.
---

# A3 — chart_facts Table Schema Specification

## §0 — Prime directive (above all else)

**Only computed facts. No narrative, no opinion, no judgement.**

Every cell in `chart_facts` is a deterministic projection of an L1 atom or a deterministic derivation of an L1 set. There is no `interpretation_text` column, no `meaning` column, no `narrative` column. If a value cannot be computed deterministically from inputs, it does not enter chart_facts.

**Retrieval accuracy is the primary optimization axis.** Storage cost, performance, and operational complexity are subordinate to whether the right row is returned for the right query.

## §1 — Row schema

```sql
CREATE TABLE chart_facts (
  fact_id                  TEXT PRIMARY KEY,        -- sha256(category|subject|key|chart_id|ayanamsha_id|build_id)[:16]
  chart_id                 UUID NOT NULL,
  ayanamsha_id             TEXT NOT NULL,           -- 'lahiri_chitrapaksha' | 'true_chitra' | 'krishnamurti' | 'raman' | 'surya_siddhanta_classical' (or 'INVARIANT' for ayanamsha-independent facts)
  build_id                 UUID NOT NULL,
  fact_category            TEXT NOT NULL,           -- enum (§3)
  fact_subject             TEXT NOT NULL,           -- UPPER_SNAKE, e.g., 'SUN', 'HOUSE_7', 'VARGA_D9', 'SUN-MARS'
  fact_key                 TEXT NOT NULL,           -- snake_case, e.g., 'longitude_sidereal', 'sign', 'shadbala_total'
  fact_value_text          TEXT,
  fact_value_num           NUMERIC,
  fact_value_jsonb         JSONB,                   -- ONLY for irreducible composites
  unit                     TEXT,                    -- 'deg', 'rupa', 'bindu', 'years', etc.
  citation_ref             TEXT NOT NULL,           -- machine-stable, slug form
  citation_human           TEXT NOT NULL,           -- human-readable sentence, LLM-citable
  source_calculation       TEXT NOT NULL,           -- engine submodule that wrote this
  verification_pass_status TEXT NOT NULL,           -- 'single' | 'two_pass_verified' | 'classical_match' | 'divergent_flagged'
  engine_version           TEXT NOT NULL,
  salience_formula_ver     TEXT,                    -- where relevant (L2.5 writers)
  computed_at              TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
);
```

**Atomicity rule**: every queryable sub-value = its own row. JSONB is reserved for irreducible composites only (e.g., chart_output provenance metadata). Shadbala's 6 sub-balas = 6 separate rows. Ashtakavarga bindus per house = 12 separate rows.

## §2 — fact_id derivation

```
fact_id = sha256(f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}")[:16]
```

Stable for a given build. New build = new fact_ids. Old build's rows retained (subject to retention §10) for derivation_ledger reference stability.

## §3 — fact_category enum (~131 categories across 11 super-groups)

**Birth + ayanamsha context (4):**
`birth_metadata`, `ayanamsha_value_at_birth`, `ayanamsha_cross_comparison`, `birth_astronomical_state`

**Lagna + Special Lagnas + Cusps (16):**
- Main: `lagna_position`, `lagna_pada`, `lagna_nakshatra_attributes`, `lagna_kp_chain`, `mc_position`, `ic_position`, `descendant_position`
- Special lagnas (11 individual categories per native decision): `lagna_stira`, `lagna_hora`, `lagna_ghati`, `lagna_vighati`, `lagna_bhava`, `lagna_yama`, `lagna_varnada`, `lagna_nakshatra_alt`, `lagna_sree`, `lagna_indu`, `lagna_pranapada`
- Cusps: `house_cusp_per_system` (Sripati/Equal/WholeSign/Placidus/Porphyry)

**Per-graha core (×23 bodies — 9 grahas + 2 nodes × 2 + 2 Liliths + 10 asteroids/outer) (28):**
`graha_position`, `graha_heliocentric`, `graha_declination`, `graha_RA`, `graha_altaz_at_birth`, `graha_speed_state`, `graha_retrogression_state`, `graha_combustion_state`, `graha_eclipsing_state`, `graha_declination_parallels`, `graha_sign_attributes`, `graha_decanate_position`, `graha_dwadasamsa_position`, `graha_mooltrikona_state`, `graha_dignity_per_varga`, `graha_vargottama_flag`, `graha_pushkara_state`, `graha_gandanta_state`, `graha_mrityubhaga_state`, `graha_neecha_bhanga_state`, `graha_avastha_baladi`, `graha_avastha_jagrad`, `graha_avastha_deepta`, `graha_avastha_lajjitadi`, `graha_avastha_sayanadi`, `graha_friendship_composite`, `graha_kp_lord_chain`, `graha_nadiamsa_position`

**Per-graha strength + relationship (14):**
`graha_shadbala_sthana`, `graha_shadbala_dig`, `graha_shadbala_kala`, `graha_shadbala_cheshta`, `graha_shadbala_naisargika`, `graha_shadbala_drik`, `graha_shadbala_total`, `graha_vimsopaka_shadvarga`, `graha_vimsopaka_saptavarga`, `graha_vimsopaka_dasavarga`, `graha_vimsopaka_shodasavarga`, `graha_ishta_phala`, `graha_kashta_phala`, `graha_karaka_role`

**Aspects + conjunctions (6):**
`aspect_parashari_given`, `aspect_parashari_received`, `aspect_jaimini`, `aspect_tajik`, `conjunction_within_orb`, `aspect_matrix_summary`

**Per-house (×12) (11):**
`house_position`, `house_lord_placement`, `house_occupant`, `house_aspect_received`, `house_classification`, `house_functional_class`, `house_arudha`, `house_bhava_bala_subscore`, `house_bhava_bala_total`, `house_natural_karaka`, `bhavat_bhavam`

**Per-varga (×30+ vargas) (7):**
`varga_position`, `varga_dignity`, `varga_vargottama_flag`, `varga_pushkara_flag`, `varga_aspect`, `varga_ashtakavarga`, `varga_house_lord`

**Ashtakavarga (7):**
`ashtakavarga_bindu`, `ashtakavarga_pinda_sodhita`, `ashtakavarga_pinda_bhinna`, `ashtakavarga_pinda_sarva`, `ashtakavarga_kakshya`, `ashtakavarga_trikona_shodhana`, `ashtakavarga_ekadhipathya_shodhana`

**Panchanga (birth-day) (15):**
`panchanga_tithi`, `panchanga_vara`, `panchanga_nakshatra_moon`, `panchanga_yoga`, `panchanga_karana`, `panchanga_hora_birth`, `panchanga_choghadiya_birth`, `panchanga_rahu_kalam`, `panchanga_yamaganda_kalam`, `panchanga_gulika_kalam`, `panchanga_abhijit_muhurta`, `panchanga_brahma_muhurta`, `panchanga_special_yoga_combinations`, `panchanga_solar_context`, `panchanga_calendrical`

**Esoteric + sensitive points (13):**
`upagraha_position`, `saturn_derived_point`, `esoteric_point_bhrigu_bindu`, `esoteric_point_yogi`, `esoteric_point_avayogi`, `esoteric_point_mrityu`, `esoteric_point_trisphuta`, `esoteric_point_chatushphuta`, `esoteric_point_panchasphuta`, `saham_position`, `karakamsa_position`, `swamsa_position`, `midpoint`

**Yogas + Doshas + special states (8):**
`yoga_fires`, `dosha_fires`, `tara_bala_natal_baseline`, `chandra_bala_natal_baseline`, `panchaka_flag`, `bhadra_flag`, `eclipse_proximity_natal`, `sade_sati_natal_baseline`

**Chakras + Nadi + Tajik (6):**
`chakra_position`, `nadiamsa_d150`, `nadiamsa_d2700`, `tajik_natal_baseline`, `bhinashtakavarga_per_graha`, `argala_natal_matrix`

**Total: ~131 categories**

Per-chart row projection: ~15K-22K per (chart, ayanamsha) × 5 ayanamshas = **75K-110K rows per chart**. Comfortable in Postgres at internal scale.

## §4 — Ayanamsha keying

`ayanamsha_id` is part of the uniqueness contract.

- **Ayanamsha-dependent categories** (most — anything involving longitude or nakshatra): 5 rows per (chart, category, subject, key, build_id) — one per ayanamsha.
- **Ayanamsha-invariant categories** (Sun-Moon-separation-based — `panchanga_tithi`, `panchanga_vara`, `panchanga_yoga`, `panchanga_karana`): single row with `ayanamsha_id = 'INVARIANT'`.

`CHART_FACTS_SCHEMA.json` declares `ayanamsha_dependent: bool` per category.

## §5 — Subject naming convention

UPPER_SNAKE with hyphenated compounds:

| Pattern | Example |
|---|---|
| Single graha | `SUN`, `MOON`, `MAR`, `MER`, `JUP`, `VEN`, `SAT`, `RAH_MEAN`, `KET_MEAN`, `RAH_TRUE`, `KET_TRUE` |
| Lilith / asteroids | `LIL_MEAN`, `LIL_TRUE`, `CER`, `PAL`, `JUN`, `VES`, `CHI`, `URA`, `NEP`, `PLU`, `SED`, `ERI` |
| House | `HOUSE_1` through `HOUSE_12` |
| Varga | `VARGA_D9`, `VARGA_D60`, `VARGA_D150` |
| Compound (aspect/conjunction/relation) | `SUN-MARS`, `SAT-MOON`, `JUP-HOUSE_7` |
| Sign | `ARI`, `TAU`, `GEM`, ... `PIS` |
| Nakshatra | `ASH`, `BHA`, `KRI`, ... `REV` |

## §6 — Citation strings (dual form)

Every row stores BOTH:

```
citation_ref     TEXT NOT NULL   -- technical, slug, machine-stable
citation_human   TEXT NOT NULL   -- complete-sentence, LLM-citable in user-facing prose
```

**Format:**

```
citation_ref     = "{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={engine_version}"
citation_human   = (per render_template declared in CHART_FACTS_SCHEMA.json §category)
```

**Examples:**

| Row | citation_ref | citation_human |
|---|---|---|
| Sun nakshatra (Lahiri) | `graha_position.SUN.nakshatra@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Sun is in Shravana nakshatra (Lahiri ayanamsha)." |
| Saturn total shadbala (KP) | `graha_shadbala_total.SAT.rupa@chart=362f9f17:ay=krishnamurti:eng=natal_engine/0.2.0` | "Saturn's total shadbala is 4.19 rupa, surplus 0.40 vs the 3.79 rupa required (KP)." |
| 7H lord placement (True Chitra) | `house_lord_placement.HOUSE_7.placed_in@chart=362f9f17:ay=true_chitra:eng=natal_engine/0.2.0` | "The 7th house lord (Mercury) is placed in the 8th house (True Chitra)." |
| Sade Sati Phase 2 window | `sade_sati_natal_baseline.CYCLE_3.peak_window@chart=362f9f17:ay=lahiri_chitrapaksha:eng=natal_engine/0.2.0` | "Third Sade Sati cycle, peak phase: 2034-09-15 through 2037-04-22 (Lahiri)." |

Human form: complete sentences, sentence case, units shown, ayanamsha parenthesized, terminated with period. LLM panels drop directly into prose.

## §7 — L2.5 separation (separate tables)

L2.5 synthesis outputs do **NOT** live in chart_facts. They live in:

| Table | Contents |
|---|---|
| `l25_msr_signals` | Every observable signal as a row with `{deterministic_strength, verification_certainty, computed_salience, salience_formula_version, domains_affected, constituent_facts_array}` |
| `l25_cdlm_cells` | 9×9 = 81 cells per (chart, ayanamsha) with shared-factor counts + linkage strength |
| `l25_cgm_nodes` + `l25_cgm_edges` | Graph nodes (grahas/houses/signs/configs) + structural edges (aspect/dispositor/lordship/karaka/conjunction/parivartana) with weights |
| `l25_rm_resonances` | Weakest grahas → remedy candidates (joins G27 remedy library) |
| `l25_ucn_digests` | Computed signature: top configurations by salience, dominant grahas, dasha context, system-convergence counts |

L2.5 rows carry `constituent_facts_array` of `fact_id` references back to chart_facts. Cleanest architectural separation.

## §8 — chart_dashas (separate table — depth Prana, two-pass mandatory)

```sql
CREATE TABLE chart_dashas (
  dasha_row_id              UUID PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL,
  build_id                  UUID NOT NULL,
  system_id                 TEXT NOT NULL,         -- 'vimshottari' | 'ashtottari' | 'yogini' | 'chara' | 'kalachakra' | ... (32 systems)
  level_n                   INT NOT NULL,          -- 1=Maha, 2=Antar, 3=Pratyantar, 4=Sookshma, 5=Prana
  parent_row_id             UUID,                  -- self-FK; NULL at level 1
  lord_graha                TEXT NOT NULL,
  lord_sign                 TEXT,                  -- for Jaimini sign-based systems
  start_date                DATE NOT NULL,
  end_date                  DATE NOT NULL,
  start_iso                 TIMESTAMPTZ NOT NULL,  -- precision to second at deepest level
  end_iso                   TIMESTAMPTZ NOT NULL,
  duration_days             NUMERIC NOT NULL,
  sandhi_flag               BOOLEAN NOT NULL,      -- within last 5% of period
  karaka_role_at_period     TEXT,                  -- Jaimini chara karaka of lord_graha at this period
  verification_pass_status  TEXT NOT NULL CHECK (verification_pass_status IN ('two_pass_verified', 'classical_match', 'divergent_flagged')),
  verification_method       TEXT NOT NULL,
  citation_ref              TEXT NOT NULL,
  citation_human            TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL,
  engine_version            TEXT NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)
);

CREATE INDEX cd_temporal_lookup_idx ON chart_dashas (chart_id, ayanamsha_id, system_id, level_n, start_date, end_date);
CREATE INDEX cd_lord_lookup_idx ON chart_dashas (chart_id, ayanamsha_id, lord_graha, system_id);
CREATE INDEX cd_parent_idx ON chart_dashas (parent_row_id);
```

**Depth: Prana (5 levels)** — Maha → Antar → Pratyantar → Sookshma → Prana. Sookshma queries (`WHERE level_n ≤ 4`) and Prana queries (`WHERE level_n ≤ 5`) both supported from same storage.

**Two-pass verification — MANDATORY** (`verification_pass_status` CHECK constraint disallows `single`):

| Pass | Method |
|---|---|
| Primary | Engine's `dashas.py` computation from nakshatra-elapsed (nakshatra-based systems) or sign-progression (Jaimini sign-based) |
| Secondary | Independent re-derivation via classical-rule reconstruction |
| Tertiary | Algebraic invariants: sum of mahadasha years = system total cycle; durations proportional per classical table |
| Halt | Pass 1 ≠ Pass 2 beyond ±1 day at deepest level → halt build, write CONDUCTOR_HALT_LOG, escalate |

Row count per chart per ayanamsha at Prana depth: ~58K per system × 32 systems = ~1.86M per (chart, ayanamsha). × 5 ayanamshas = ~9.3M per chart. HASH(chart_id) partitioning when threshold hits.

Tool surface: `query_dasha_branch_at_date(chart_id, ayanamsha_id, system_id, date)` returns full hierarchical branch — 5 indexed lookups, no MV needed.

## §9 — Index strategy

```sql
PRIMARY KEY (fact_id)
UNIQUE (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)

INDEX chart_facts_chart_aya_cat_idx ON chart_facts (chart_id, ayanamsha_id, fact_category);
INDEX chart_facts_chart_aya_sub_idx ON chart_facts (chart_id, ayanamsha_id, fact_subject);
INDEX chart_facts_chart_cat_sub_key_idx ON chart_facts (chart_id, fact_category, fact_subject, fact_key);
INDEX chart_facts_build_idx ON chart_facts (build_id);  -- for supersedence
INDEX chart_facts_verification_idx ON chart_facts (verification_pass_status) WHERE verification_pass_status != 'single';
GIN INDEX chart_facts_jsonb_gin ON chart_facts USING gin (fact_value_jsonb);
```

`CHART_FACTS_INDEX_INVENTORY.md` documents every retrieval tool's index dependency. `drift_detector.py` verifies indexes exist on every build close.

## §10 — Materialized views (natal-fixed only)

**Rule (locked):** Materialized views in chart_facts are ONLY for time-invariant natal data. Time-varying queries (parametric on query_date or transit position) query underlying tables directly without MV intermediation.

**MVs KEPT** (refresh synchronous at build close — `builds.status` doesn't flip to 'complete' until MVs refresh):

| MV | Granularity |
|---|---|
| `mv_chart_planet_summary` | one row per (chart, ayanamsha, graha) |
| `mv_chart_house_summary` | one row per (chart, ayanamsha, house) |
| `mv_chart_yogas_active_at_birth` | one row per fired yoga |
| `mv_chart_vargas_summary` | one row per (chart, ayanamsha, graha, varga) |
| `mv_chart_sahams` | one row per Tajik saham |
| `mv_chart_arudhas` | one row per arudha (A1..A12 + UL + GL + DP + 7 graha arudhas) |
| `mv_chart_shadbala_summary` | one row per (chart, ayanamsha, graha) joining all shadbala subscores + total |
| `mv_chart_bhava_bala_summary` | one row per (chart, ayanamsha, house) joining all bhava_bala subscores + total |
| `mv_chart_ashtakavarga_summary` | per-graha + sarvashtakavarga rollups |
| `mv_cross_ayanamsha_consensus` | per (chart, category, subject, key) — agreement/divergence across 5 ayanamshas |

**No MV for** (compute at query time from underlying tables):
- Current dasha at date X → direct query on `chart_dashas`
- Transit positions → G2 `ephemeris_daily`
- Current panchanga → G7 `panchanga_daily`
- Tara bala / Chandra bala for transit Moon → on-the-fly function
- Bhrigu Bindu transit → G49 timeline
- Next exact aspect from natal X to transit Y → on-the-fly via G2 scan
- Eclipses upcoming → G4 × natal positions overlay
- Sade Sati current phase at date X → query `chart_facts.sade_sati_natal_baseline` precomputed lifetime windows

## §11 — Self-describing schema (`CHART_FACTS_SCHEMA.json`)

Single machine-readable contract every retrieval channel reads:

```json
{
  "schema_version": "1.0",
  "categories": {
    "<category_name>": {
      "ayanamsha_dependent": true|false,
      "applies_to_subjects": ["..."],
      "allowed_keys": {
        "<key>": {
          "value_type": "num" | "text" | "text_enum" | "bool" | "jsonb_atomic",
          "unit": "deg" | "rupa" | "bindu" | ...,
          "enum": ["..."] (if text_enum),
          "range": [min, max] (if num),
          "precision": N (if num),
          "verification_min": "single" | "two_pass_verified" | "classical_match"
        }
      },
      "since_engine_version": "natal_engine/0.X.X",
      "retrieval_hints": {
        "common_query_patterns": ["pinpoint", "graha_summary", "house_summary", ...],
        "mv_preferred": "mv_chart_X" (if applicable)
      },
      "render_template": "<human-readable sentence with {placeholders}>"
    }
  },
  "channels": {
    "mcp_sidecar_agentic": { "default_mode": "bundle", "max_rows_per_response": 200, "include_citation_ref": true, "include_citation_human": true, "prefer_mv": true },
    "internal_portal_agentic": { "default_mode": "bundle", "max_rows_per_response": 500, "include_citation_ref": true, "include_citation_human": true, "prefer_mv": true, "bundle_cache_strategy": "prompt_cache_layer_1" },
    "internal_portal_vanilla_llm": { "default_mode": "specific", "max_rows_per_response": 50, "include_citation_ref": false, "include_citation_human": true, "prefer_mv": true, "structured_output_template": "claude_xml" },
    "mcp_sidecar_api": { "default_mode": "specific", "max_rows_per_response": 1000, "include_citation_ref": true, "include_citation_human": false, "output_format": "raw_json" }
  }
}
```

Schema is the source of truth. Retrieval tools read from it dynamically — never hard-code. Adding a fact_category = adding a JSON entry; no code change required. `drift_detector.py` verifies schema ↔ DB at every build close.

## §12 — Tool variants per channel

Four adapters reading the same underlying truth (`chart_facts` + `chart_dashas` + `l25_*`), responding per `CHART_FACTS_SCHEMA.json §channels`:

| Adapter | Client | Optimization |
|---|---|---|
| `mcp_sidecar_agentic` | External Claude Code / Antigravity user, agentic loop | Bundle mode, large row caps, both citations, MV-preferred |
| `internal_portal_agentic` | `/consume` chat with R11.F bounded loop hybrid | Bundle mode, prompt-cache Layer 1, broad row counts, intent-classifier seed |
| `internal_portal_vanilla_llm` | `/consume` chat with non-agentic provider | Specific mode, structured XML output, smaller row caps, human citation only |
| `mcp_sidecar_api` | Programmatic API (cron jobs, batch analysis) | Specific mode, raw JSON, large row caps, no human citation |

## §13 — Verification status semantics

Per-category default declared in `CHART_FACTS_SCHEMA.json`. Retrieval tools' `verification_min` parameter defaults to the schema's per-category value.

| Status | Meaning |
|---|---|
| `single` | Computed once by primary algorithm. Acceptable for Swiss Ephemeris-authoritative categories (positions, signs, nakshatras) |
| `two_pass_verified` | Computed via two independent algorithms; matched. **MANDATORY** for dashes, ashtakavarga, sensitive points (Gulika/Mandi/Yogi/Avayogi/Bhrigu Bindu), shadbala |
| `classical_match` | Matched a classical textbook example (one-time at engine release, not per-build) |
| `divergent_flagged` | Computed two ways; disagreed. Halt-worthy; manual disposition required |

## §14 — Backfill policy

**Wipe and rebuild fresh.** Existing pre-A3 chart_facts rows (~2,717 from the dead YAML-extraction pipeline) are deleted, not archived. First rebuild under the new schema populates fresh per-chart per-ayanamsha rows from the engine.

```sql
TRUNCATE chart_facts;
TRUNCATE chart_dashas;
TRUNCATE chart_facts_history;
TRUNCATE chart_facts_supersedence;
-- All L2.5 tables also truncated
```

## §15 — Audit + history tables

- **`chart_facts_history`** — append-only INSERT audit. Every chart_facts INSERT/UPDATE fires a copy here. **Retention: 30 days, then purge.** Cron job nightly.
- **`chart_facts_supersedence`** — when a new build supersedes an old build's rows for the same (chart_id, ayanamsha_id, category, subject, key), log the transition with both build_ids + value-deltas. Retention: same as `chart_facts_history`.

## §16 — Partitioning policy

**Deferred** until 1,000+ charts. At threshold: HASH(chart_id) 8 buckets. Migration 121 (pre-drafted) gets applied.

For internal scale (you + ~10 users with <100 charts): single unpartitioned table is comfortable.

## §17 — "Only facts" enforcement (architectural prime directive — implementation)

Concrete mechanisms preventing prose/opinion from entering chart_facts:

1. **Schema enforcement at write time** — `CHART_FACTS_SCHEMA.json` declares per-key `value_type` ∈ {`num`, `text_enum`, `bool`, `jsonb_atomic`}. NO `value_type: prose`. Writers fail on mismatch.
2. **`fact_value_text` enum-validation** — for categorical keys (sign, nakshatra, dignity, etc.), values must match declared enum in schema. No free-form text.
3. **No-narration linter** (extends INF8) — scans `fact_value_text` for forbidden patterns: "indicates", "suggests", "implies", "means", "denotes", "yields", "results in", "leads to". Halt build on violation.
4. **No `interpretation` / `meaning` / `narrative` columns** exist on chart_facts. The schema literally cannot store opinion.
5. **`drift_detector` audit** — samples random rows at every build close, verifies values match schema declarations. Halts on drift.
6. **New hard gate G7_only_facts** — runs nightly + per-build, scans chart_facts text values against forbidden patterns + per-category render_template parsing.

## §18 — What A3 LOCKS (final committed surface)

1. Row schema + dual citation (`citation_ref` + `citation_human`)
2. `fact_id` derivation including `build_id`
3. ~131 fact_category enum
4. Atomic-by-default storage (JSONB only for irreducible composites)
5. Ayanamsha-keyed primary key; ayanamsha-invariant categories use `ayanamsha_id='INVARIANT'`
6. UPPER_SNAKE subject naming; hyphenated compounds (`SUN-MARS`)
7. L2.5 separation into `l25_*` tables
8. `chart_dashas` separate table, depth Prana (5 levels), two-pass MANDATORY
9. MV scope: natal-fixed only; refresh synchronous at build close; time-varying queries underlying tables
10. `CHART_FACTS_SCHEMA.json` self-describing with 4 channel adapters
11. Verification min per-category; `two_pass_verified` mandatory for dashes/ashtakavarga/sensitive_points
12. Backfill: wipe + rebuild fresh; no archive
13. `chart_facts_history` retention 30 days
14. Partitioning deferred until 1,000+ charts
15. Special Lagnas as 11 individual categories
16. Prime directive enforcement via 6 mechanisms (§17)

After A3 locks, A4-A14 writers are mechanical extensions — each emits a defined subset of the fact_category enum into `chart_facts` (or its dedicated table for dashes/L2.5).

---

*End of A3_CHART_FACTS_SPEC_v1_0.md — LOCKED 2026-05-29. Native sign-off complete across 4 clarification rounds.*
