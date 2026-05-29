---
artifact: A17_A21_SUPPLEMENTARY_SPEC_v1_0.md
document: A17–A21 — Supplementary Per-Chart Assets Specification
status: LOCKED
version: 1.0
date: 2026-05-29
authored_by: Cowork (native-confirmed: original A15-A20 supplementary coverage audit; gaps locked as A17-A21 with renumbering to deconflict with magical nuggets at A15/A16)
intended_for: Claude Code sub-agents implementing the supplementary writers
prime_directive: Only computed facts. Vedha + Chakra + Bhrigu Bindu + Tajik + next-exact-aspect tables that classical Jyotish references but no current asset materializes. No narrative.
depends_on: A1 (engine), A3 (chart_facts), A4 (panchanga), A5 (sensitive points — Bhrigu Bindu natal position), A7 (chart_dashas — Mudda/Tajik), A8 (T1 structural — Argala already folded), A15 (Time-Synchronicity — consumes these feeders)
technology_stack: Cloud SQL Postgres + native PG range partitioning (where temporal) + pgvector (where embeddings useful). No new infra.
---

# A17–A21 — Supplementary Per-Chart Assets Specification

## §0 — Mission

Close the supplementary-asset gaps surfaced by coverage audit. Four new writer assets + one A8 amendment. Each one is a small focused asset materializing classical reference data that no current asset captures.

## §1 — Renumbering note + cumulative asset map

Because A15 was reused for Time-Synchronicity Stack and A16 for Phase-Locked Event Anchors (the magical-nugget arc), the original A15-A20 supplementary numbering shifts. **Definitive asset map**:

| ID | Asset | Status |
|---|---|---|
| A1–A13 | per-chart base assets | LOCKED |
| A14 | UCN — RETIRED → UCD | RETIRED |
| A15 | Time-Synchronicity Stack | LOCKED |
| A16 | Phase-Locked Event Anchor Map | LOCKED |
| A17 | Chakras (Sarvatobhadra / Sapta-shalaka / Kalanala / Kota) | LOCKED in this spec |
| A18 | Vedha calculations | LOCKED in this spec |
| A19 | Bhrigu Bindu lifetime transit table | LOCKED in this spec |
| A20 | Tajik per-chart extensions (Hadda + varsha year-lord) — folded into A8 amendment | LOCKED via A8 amendment |
| A21 | Per-graha next-exact-aspect lifetime table | LOCKED in this spec |

Total per-chart writer assets: **18 active (A1-A13 + A15-A21; A14 retired; A20 folded into A8).**

## §2 — A17 — Chakras (Geometric reference chakras)

### §2.A — Mission

Materialize the classical geometric chakras used for vedha and transit timing:
- **Sarvatobhadra Chakra** (28 nakshatras in a 9×9 grid + corners) — used for nakshatra vedha
- **Sapta-shalaka Chakra** (7-line cross of 28 nakshatras + 12 rasis + 9 grahas) — used for "from where to where" obstruction
- **Kalanala Chakra** (planetary fire-arrow chakra) — used for transit malefic timing
- **Kota Chakra** (fort chakra) — used for war/conflict timing per Tajik
- **Chandra Kala Nadi Chakra** (lunar-phase chakra) — Nadi-style timing

Each is a STRUCTURAL REFERENCE: positions of grahas/houses/nakshatras within the geometric chakra grid + classical vedha rules per chakra.

### §2.B — Storage

```sql
CREATE TABLE l1_chakras (
  chakra_position_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  chakra_type TEXT NOT NULL,                          -- 'sarvatobhadra' | 'sapta_shalaka' | 'kalanala' | 'kota' | 'chandra_kala_nadi'
  position_subject TEXT NOT NULL,                     -- 'SUN' | 'NAK_ROHINI' | 'HOUSE_7' | etc.
  grid_position_jsonb JSONB NOT NULL,                 -- {row, col, ring, corner, axis} as appropriate per chakra type
  position_role TEXT,                                 -- 'fixed_natal' | 'transit_overlay' | 'fort_keeper' | 'arrow_tip' | etc.
  vedha_rules_applicable_array TEXT[],                -- which vedha rule classes apply at this position
  classical_source_citation TEXT NOT NULL,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, chakra_type, position_subject)
);

CREATE INDEX chakras_chart_idx ON l1_chakras (chart_id, ayanamsha_id);
CREATE INDEX chakras_type_idx ON l1_chakras (chart_id, ayanamsha_id, chakra_type);
```

Per chart × ayanamsha: ~500 position rows (28 nakshatras + 12 rasis + 9 grahas + 12 houses across 5 chakra types). × 5 ayanamshas = ~2,500 per chart.

### §2.C — Retrieval

- `query_chakra_positions(chart_id, ayanamsha_id, chakra_type?)` → positions
- `query_chakra_vedha_candidates(chart_id, ayanamsha_id, chakra_type, source_position?)` → vedha lookups

## §3 — A18 — Vedha Calculations

### §3.A — Mission

Vedha = obstruction. Materialize all classical vedha types:

1. **Nakshatra vedha** (Sarvatobhadra-based) — when transit graha occupies a nakshatra that blocks a natal-significant nakshatra per the Sarvatobhadra grid
2. **Tajik vedha** (year-lord vedha) — when year-lord conditions obstruct annual prediction
3. **Dasha vedha** (sub-lord obstruction) — when one dasha lord obstructs another's results
4. **Transit vedha** (chakra-based) — when transit position blocks expected timing per A17 chakras
5. **Sapta-shalaka vedha** — line-based obstruction
6. **Argala vedha** — extension of A8 argala for obstruction patterns
7. **Vedha resolution** — when one vedha is cancelled by another

### §3.B — Storage

```sql
CREATE TABLE l25_vedha_calculations (
  vedha_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  vedha_type TEXT NOT NULL,                           -- 'nakshatra' | 'tajik_year_lord' | 'dasha_sub_lord' | 'transit_chakra' | 'sapta_shalaka' | 'argala_extension'
  source_position TEXT NOT NULL,                      -- graha/house/nakshatra causing the obstruction
  blocked_position TEXT NOT NULL,                     -- graha/house/nakshatra being obstructed
  vedha_severity_class TEXT,                          -- 'total' | 'partial' | 'mitigated'
  active_during_class TEXT,                           -- 'lifelong' | 'dasha_bounded' | 'transit_bounded' | 'year_bounded'
  active_iso_window_array JSONB,                      -- when this vedha is active
  cancellation_chain_jsonb JSONB,                     -- when other rules cancel this vedha
  associated_chakra_id UUID,                          -- FK to l1_chakras row
  associated_dasha_window_jsonb JSONB,
  classical_source_citation TEXT NOT NULL,
  vedha_rule_id_g_catalog TEXT,                       -- reference to G-catalog vedha rule
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX vedha_chart_idx ON l25_vedha_calculations (chart_id, ayanamsha_id);
CREATE INDEX vedha_type_idx ON l25_vedha_calculations (chart_id, ayanamsha_id, vedha_type);
CREATE INDEX vedha_severity_idx ON l25_vedha_calculations (chart_id, ayanamsha_id, vedha_severity_class);
CREATE INDEX vedha_chakra_fk_idx ON l25_vedha_calculations (associated_chakra_id);
```

Per chart × ayanamsha: ~1,000 vedha rows (per chakra type × source positions × blocked positions). × 5 ayanamshas = ~5,000 per chart.

### §3.C — Retrieval

- `query_vedhas(chart_id, ayanamsha_id, vedha_type?, severity?, active_only?, date?)` → vedha rows
- `query_vedhas_on_position(chart_id, ayanamsha_id, blocked_position)` → all vedhas obstructing a target

### §3.D — Feeds A15

Active vedhas at any date contribute to A15 Time-Synchronicity convergence_intensity (vedha activation is a cosmic resonance signal).

## §4 — A19 — Bhrigu Bindu Lifetime Transit Table

### §4.A — Mission

Bhrigu Bindu = (longitude(Moon) + longitude(Rahu)) / 2. Nadi-derived high-value point. Transit hits to Bhrigu Bindu = major life events classically. Materialize lifetime transit hit table.

### §4.B — Storage

```sql
CREATE TABLE l1_bhrigu_bindu_transits (
  transit_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  natal_bhrigu_bindu_longitude_deg NUMERIC NOT NULL,  -- natal Bhrigu Bindu position
  transit_graha TEXT NOT NULL,                        -- which graha is hitting
  transit_hit_iso TIMESTAMPTZ NOT NULL,               -- exact moment of conjunction (within orb)
  transit_orb_arcsec NUMERIC,
  transit_aspect_class TEXT,                          -- 'exact_conjunction' | 'within_1deg' | 'within_3deg'
  transit_direction TEXT,                             -- 'direct' | 'retrograde'
  transit_severity_score NUMERIC,                     -- weighted by graha class (Saturn > Jupiter > Mars > etc.)
  active_dasha_at_transit_jsonb JSONB,                -- which Vim/Chara/Yogini lord is active at hit moment
  panchanga_at_transit_jsonb JSONB,                   -- panchanga of the hit
  classical_significance_class TEXT,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, transit_graha, transit_hit_iso)
) PARTITION BY RANGE (transit_hit_iso);

CREATE TABLE l1_bhrigu_bindu_transits_y1950_y2000 PARTITION OF l1_bhrigu_bindu_transits FOR VALUES FROM ('1950-01-01') TO ('2000-01-01');
CREATE TABLE l1_bhrigu_bindu_transits_y2000_y2050 PARTITION OF l1_bhrigu_bindu_transits FOR VALUES FROM ('2000-01-01') TO ('2050-01-01');
CREATE TABLE l1_bhrigu_bindu_transits_y2050_y2100 PARTITION OF l1_bhrigu_bindu_transits FOR VALUES FROM ('2050-01-01') TO ('2100-01-01');

CREATE INDEX bb_chart_idx ON l1_bhrigu_bindu_transits (chart_id, ayanamsha_id);
CREATE INDEX bb_graha_idx ON l1_bhrigu_bindu_transits (chart_id, ayanamsha_id, transit_graha);
CREATE INDEX bb_severity_idx ON l1_bhrigu_bindu_transits (chart_id, ayanamsha_id, transit_severity_score DESC);
```

Per chart × ayanamsha: ~200 hits (slow planet hits over 150 years). × 5 = ~1,000 per chart.

### §4.C — Retrieval

- `query_bhrigu_bindu_transits(chart_id, ayanamsha_id, start_iso?, end_iso?, transit_graha?, min_severity?)` → rows
- `query_next_bhrigu_bindu_hit(chart_id, ayanamsha_id, from_date)` → next hit

### §4.D — Feeds A15

Bhrigu Bindu hits are first-class A15 synchronicity events (when active, contribute to convergence_intensity).

## §5 — A20 — Tajik per-chart extensions (folded into A8)

### §5.A — A8 Amendment

Add to A8 spec / chart_summary:

```sql
ALTER TABLE l1_a8_chart_summary
  ADD COLUMN tajik_hadda_lords_jsonb JSONB,           -- Hadda lord per sign (Tajik-specific dignity system; 5 Haddas per sign)
  ADD COLUMN tajik_hadda_classifications_jsonb JSONB; -- {graha → hadda lord context}

CREATE TABLE l1_tajik_varsha_year_lords (
  varsha_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  varsha_year INT NOT NULL,                           -- birth-year-relative (year 1, year 2, ..., year 150)
  varsha_start_iso TIMESTAMPTZ NOT NULL,
  varsha_end_iso TIMESTAMPTZ NOT NULL,
  year_lord_method TEXT NOT NULL,                     -- 'tajik_classical' | 'panchavargiya'
  year_lord TEXT NOT NULL,                            -- the Tajik year-lord for this varsha
  candidate_lord_jsonb JSONB,                         -- 5 candidate lords + their scores
  muntha_position_jsonb JSONB,                        -- Muntha position for this varsha
  applicable_tajik_yogas_array TEXT[],
  classical_source_citation TEXT NOT NULL,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, varsha_year)
);
```

Per chart × ayanamsha: ~150 varsha rows. × 5 = ~750.

### §5.B — Retrieval

- `query_tajik_hadda_lords(chart_id, ayanamsha_id)` → hadda lord table
- `query_tajik_year_lord_for_varsha(chart_id, ayanamsha_id, varsha_year_or_date)` → year-lord row
- `query_tajik_year_lord_range(chart_id, ayanamsha_id, start_year, end_year)` → range

## §6 — A21 — Per-graha next-exact-aspect lifetime table

### §6.A — Mission

For each (natal_graha × transit_graha × aspect_type), pre-compute every exact-aspect moment 1950-2100. Materialized lookup so A15 Time-Synchronicity + LLM retrievers don't recompute at query time.

### §6.B — Storage

```sql
CREATE TABLE l1_exact_aspect_lifetime (
  aspect_event_id UUID PRIMARY KEY,
  chart_id, ayanamsha_id, build_id,
  natal_graha TEXT NOT NULL,
  transit_graha TEXT NOT NULL,
  aspect_type TEXT NOT NULL,                          -- 'conjunction_0' | 'sextile_60' | 'square_90' | 'trine_120' | 'opposition_180' | 'parashari_3' | 'parashari_7' | 'parashari_10' | 'tajik_ithasala' | etc.
  exact_aspect_iso TIMESTAMPTZ NOT NULL,
  pre_exact_window_start_iso TIMESTAMPTZ,             -- when transit graha enters orb (±3°)
  post_exact_window_end_iso TIMESTAMPTZ,              -- when transit graha leaves orb
  transit_direction TEXT,                             -- 'direct' | 'retrograde' | 'stationary'
  transit_speed_dps NUMERIC,                          -- arc-degrees per day at exact moment
  is_retrograde_aspect_flag BOOLEAN,
  aspect_intensity_class TEXT,                        -- 'instant' | 'lingering' (retrograde returns), 'tight_orb' | 'wide_orb'
  active_dasha_at_aspect_jsonb JSONB,                 -- which lords are active at exact moment
  panchanga_at_aspect_jsonb JSONB,
  classical_significance_class TEXT,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, natal_graha, transit_graha, aspect_type, exact_aspect_iso)
) PARTITION BY RANGE (exact_aspect_iso);

CREATE TABLE l1_exact_aspect_lifetime_y1950_y2000 PARTITION OF l1_exact_aspect_lifetime FOR VALUES FROM ('1950-01-01') TO ('2000-01-01');
CREATE TABLE l1_exact_aspect_lifetime_y2000_y2050 PARTITION OF l1_exact_aspect_lifetime FOR VALUES FROM ('2000-01-01') TO ('2050-01-01');
CREATE TABLE l1_exact_aspect_lifetime_y2050_y2100 PARTITION OF l1_exact_aspect_lifetime FOR VALUES FROM ('2050-01-01') TO ('2100-01-01');

CREATE INDEX exact_aspect_chart_idx ON l1_exact_aspect_lifetime (chart_id, ayanamsha_id);
CREATE INDEX exact_aspect_natal_idx ON l1_exact_aspect_lifetime (chart_id, ayanamsha_id, natal_graha);
CREATE INDEX exact_aspect_transit_idx ON l1_exact_aspect_lifetime (chart_id, ayanamsha_id, transit_graha);
CREATE INDEX exact_aspect_pair_idx ON l1_exact_aspect_lifetime (chart_id, ayanamsha_id, natal_graha, transit_graha);
CREATE INDEX exact_aspect_type_idx ON l1_exact_aspect_lifetime (chart_id, ayanamsha_id, aspect_type);
```

Volume: per (natal_graha × transit_graha × aspect_type), ~30-200 exact events over 150 years. 9 natal × 9 transit grahas × ~5 aspect types × ~50 events × 5 ayanamshas = ~10,000 per chart (largely dominated by fast-moving graha events; slow-graha aspect events are far fewer).

### §6.C — Retrieval

- `query_exact_aspects_in_range(chart_id, ayanamsha_id, start_iso, end_iso, natal_graha?, transit_graha?, aspect_type?)` → events
- `query_next_exact_aspect(chart_id, ayanamsha_id, from_date, natal_graha, transit_graha, aspect_type?)` → next exact event
- `query_aspect_pair_lifetime_count(chart_id, ayanamsha_id, natal_graha, transit_graha)` → count per pair

### §6.D — Feeds A15

A21 is the precise feeder for A15's "transit calculations" — A15 enumerates key dates that include A21 exact-aspect events.

## §7 — Cross-asset linkage (A15 amendment)

A15 Time-Synchronicity now treats as precise feeders:
- A18 active vedhas → contribute to convergence_intensity
- A19 Bhrigu Bindu hits → first-class synchronicity events
- A21 exact aspects → precise transit_hit enumeration

A15 spec amendment recommended: add `feeder_assets_array TEXT[]` to convergence_intensity_decomposition_jsonb so the LLM knows which downstream assets contributed.

## §8 — Volume summary

| Asset | Rows per chart |
|---|---|
| A17 Chakras | ~2,500 |
| A18 Vedha | ~5,000 |
| A19 Bhrigu Bindu transits | ~1,000 |
| A20 Tajik extensions (in A8) | ~750 |
| A21 Exact aspect lifetime | ~10,000 |
| **Subtotal** | **~19,250 per chart** |
| × 20 charts | **~385K** |

Trivial relative to A7 chart_dashas (5.4M/chart).

## §9 — Retrieval Interface Register integration

All A17-A21 + A20 amendment retrieval tools registered per `RETRIEVAL_INTERFACE_REGISTER_v1_0.md` standards:
- Standard input envelope (chart_id, ayanamsha_id, tier, channel)
- Standard output envelope (rows + citations + derivation_trail_pointers + tier_filtered + channel_adapter_applied + meta)
- 5 channel adapters
- 3-tier filtering
- Cross-asset FK exposure (chakra_id → vedha_chakra_fk; bhrigu_bindu transits + exact_aspect_lifetime feed A15)
- LLM-facing tool descriptions per standard

Additional retrieval-surface count: ~12 new tools (A17 × 2, A18 × 2, A19 × 2, A20 × 3, A21 × 3).

## §10 — Final locked surface

1. A17 Chakras — 5 geometric chakras (Sarvatobhadra / Sapta-shalaka / Kalanala / Kota / Chandra Kala Nadi) — NEW asset
2. A18 Vedha calculations — 6 vedha types — NEW asset, depends on A17 + A8 argala
3. A19 Bhrigu Bindu lifetime transit table — NEW asset, feeds A15
4. A20 Tajik per-chart extensions (Hadda lords + varsha year-lords) — A8 amendment + new l1_tajik_varsha_year_lords table
5. A21 Per-graha next-exact-aspect lifetime — NEW asset, feeds A15
6. A15 amendment — `feeder_assets_array` added to convergence decomposition
7. ~19K additional rows per chart
8. ~12 new retrieval tools added to interface register

## §11 — Tracker reference

Original A15-A20 supplementary tracker entries (track id `A_supplementary` in state.json) updated to point to this consolidated spec. Renumbering note added to tracker meta.

---

*End of A17_A21_SUPPLEMENTARY_SPEC_v1_0.md — LOCKED 2026-05-29.*
