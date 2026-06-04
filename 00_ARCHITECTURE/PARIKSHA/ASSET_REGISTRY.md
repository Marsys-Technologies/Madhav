---
artifact: ASSET_REGISTRY.md
version: 1.0
status: LIVE
authored_at: 2026-05-31
role: Detailed per-asset spec Pramana-Drashta uses to verify quality.
---

# Asset Registry v1.0

Every asset Pariksha may verify, with its mission, schema target, expected
data, dependencies, and quality criteria. Updates here drive
EXPECTED_ROW_COUNTS.yaml and Pramana's invariant battery.

## Asset card legend

```
sanskrit · english (id, layer)
  Mission        — what this asset computes
  Target tables  — where rows land in the DB
  Reads from     — upstream assets it depends on
  Writers        — source files in python-sidecar
  Expected rows  — per ayanamsha (or total if chart-independent)
  Schema invariants — NOT NULL, CHECK, FK rules to verify
  Cross-asset    — structural invariants involving other assets
  Pramana checks — what gets verified post-build
```

---

## L1 · Adhara · Foundation (8 assets)

### Pratyaksha · Direct perception (pratyaksha, L1)
- **Mission.** Compute the forensic chart — planet positions, lagna, houses, and divisional summaries — from birth coordinates + selected ayanamsha. The single source of truth all downstream synthesis reads.
- **Target tables.** `chart_facts` (category prefix `forensic.*`).
- **Reads from.** charts row (birth coords, time, tz) + ayanamsha registry.
- **Writers.** `pipeline/writers/forensic_writer.py`.
- **Expected rows.** ~2,717 per ayanamsha (per MCPT close).
- **Schema invariants.** Every row has chart_id, ayanamsha_id, category, value. Category matches a known taxonomy.
- **Cross-asset.** All downstream L2.5 + L3 assets join on (chart_id, ayanamsha_id) — primary key integrity required.
- **Pramana checks.** Row count ±1%; planet count = 9; Lagna sign matches house 1 sign; aspects internally symmetric; nakshatra ↔ degree formula consistency.

### Panchanga · Five limbs (panchanga, L1)
- **Mission.** Daily almanac of tithi/vara/nakshatra/yoga/karana plus enrichment (special yogas, choghadiya, hora, inauspicious/auspicious windows) for every date 1900-2100.
- **Target tables.** `panchanga_daily`.
- **Reads from.** Nothing chart-specific; this is a calendar precompute.
- **Writers.** `pipeline/writers/panchanga_writer.py`, `panchanga_writer_a4.py`.
- **Expected rows.** **73,414 rows total** (chart-independent — built once, served all charts).
- **Schema invariants.** 5 JSONB enrichment columns populated; GIN indexes present; date unique.
- **Cross-asset.** A2 panchanga referenced by A14 Kala Yoga, A20 Tajik Varsha for time-of-event lookups.
- **Pramana checks.** Total row count = 73,414 exact; first row = 1900-01-01; last = 2100-12-31; every date present (no gaps); native birth date row has correct tithi/vara per JH-derived FORENSIC ground truth IF a native_oracle.yaml exists.

### Drishti Lakshana · Sensitive points (drishti_lakshana, L1)
- **Mission.** Compute ARMC, ASC, MC, Vertex, Equatorial Ascendant, Equatorial Point, plus Sripati bhava-madhyas.
- **Target tables.** `chart_facts` (category `sensitive_point.*`).
- **Reads from.** Birth coords + time + ayanamsha.
- **Writers.** `pipeline/writers/sensitive_points_writer.py`.
- **Expected rows.** ~340 per ayanamsha.
- **Schema invariants.** Every point has latitude + longitude in valid range; bhava-madhyas sum to 360° mod arithmetic.
- **Cross-asset.** Bhava-madhyas used by A5 Bhava Vibhaga to derive house boundaries.
- **Pramana checks.** Sripati 'S' returns sandhis NOT madhyas (per memory); madhyas computed as equal-arc quadrant thirds. ASC sign equals Lagna sign.

### Graha Sthana · Planet positions (graha_sthana, L1)
- **Mission.** Nine grahas' longitudes per ayanamsha, with sign/house/nakshatra assignments.
- **Target tables.** `chart_facts` (category `planet.*`).
- **Reads from.** Birth coords + ephemeris + ayanamsha.
- **Writers.** Part of `forensic_writer.py`.
- **Expected rows.** 9 per ayanamsha (one per graha).
- **Schema invariants.** Longitude in [0, 360); sign = floor(longitude/30); nakshatra = floor(longitude/(360/27)).
- **Cross-asset.** A9 MSR signal IDs cite planet IDs from here; A10 CGM edges reference these.
- **Pramana checks.** Standard 9-planet set present (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu); Rahu ↔ Ketu always 180° apart; aspects internally symmetric.

### Bhava Vibhaga · House divisions (bhava_vibhaga, L1)
- **Mission.** 12 house cusps + lords + sign assignments.
- **Target tables.** `chart_facts` (category `house.*`).
- **Reads from.** A3 Drishti Lakshana (bhava-madhyas) + A4 Graha Sthana (planet positions).
- **Writers.** Part of `forensic_writer.py`.
- **Expected rows.** 12 per ayanamsha.
- **Schema invariants.** House numbers 1-12; cusps in [0, 360); house 1 sign = lagna sign.
- **Cross-asset.** A8 Yoga Sambandha reads house occupancy.
- **Pramana checks.** Houses tile to 360° with no overlap; lord of house N is the planet ruling the sign occupying house N.

### Varga · Divisional charts (varga, L1)
- **Mission.** Compute D1 through D60 divisionals — Hora, Drekkana, Chaturthamsa, Saptamsa, Navamsa, Dasamsa, etc.
- **Target tables.** `chart_facts`, `divisional_charts`.
- **Reads from.** A4 Graha Sthana.
- **Writers.** `pipeline/writers/vargas_writer.py`.
- **Expected rows.** TBD per writer audit. Documented divisionals count × 9 planets × ayanamsha.
- **Schema invariants.** Divisional name matches a known set; sign assignments use the divisional's specific computation rule.
- **Cross-asset.** Atmakaraka derivation reads D9 (Navamsa).
- **Pramana checks.** D9 Atmakaraka = planet with highest D1 longitude mod 30°; D1 + D9 consistency for every planet.

### Dasha Krama · Period sequence (dasha_krama, L1)
- **Mission.** Vimshottari + Yogini + Chara dasha periods over the chart's lifetime.
- **Target tables.** `dasha_periods`.
- **Reads from.** A4 Graha Sthana (Moon nakshatra for Vimshottari seed).
- **Writers.** `pipeline/writers/dashas_writer.py`.
- **Expected rows.** TBD per dasha system. Vimshottari ~9 mahadasha × ~9 antardasha × ~9 pratyantar × levels deep.
- **Schema invariants.** Each period has dasha_system, lord, start_date, end_date; periods non-overlapping per system.
- **Cross-asset.** A15 Bandha references dasha boundaries for event anchoring.
- **Pramana checks.** Vimshottari mahadasha total = 120 years exactly; each level sums to parent; lord rotation matches classical sequence.

### Yoga Sambandha · Yoga relationships (yoga_sambandha, L1)
- **Mission.** Detect classical yogas — Raja, Dhana, Pancha-Mahapurusha, Gajakesari, etc. — based on planet placements.
- **Target tables.** `chart_facts` (category `yoga.*`).
- **Reads from.** A4 Graha Sthana + A5 Bhava Vibhaga.
- **Writers.** `pipeline/writers/yoga_register_writer.py`.
- **Expected rows.** TBD. Conditional on chart configuration; varies per chart.
- **Schema invariants.** Each yoga has name, is_active (bool), strength (where applicable), participating planets.
- **Cross-asset.** A9 MSR signals derive yoga-presence flags.
- **Pramana checks.** Yoga definitions match classical authority (BPHS or PMS); strength bounded [0,1].

---

## L2.5 · Sambandha · Synthesis (5 assets)

### Lakshana Kosha · Treasury of indicators (lakshana_kosha, L2.5)
- **Mission.** The Master Signal Register — 573 grounded signals derived from Adhara assets, each citing its L1 source.
- **Target tables.** `msr_signals`.
- **Reads from.** All L1 assets.
- **Writers.** `pipeline/writers/msr_writer.py`.
- **Expected rows.** **573 exact** per ayanamsha.
- **Schema invariants.** Every signal has `source_citation` NOT NULL containing FORENSIC/LEL references (per GISMCP-S2 confirmation).
- **Cross-asset.** A10 CGM edges + A11 CDLM cells reference signal IDs.
- **Pramana checks.** Exactly 573 rows; 0 rows with NULL source_citation; signal IDs immutable across rebuilds.

### Karana Jala · Net of causes (karana_jala, L2.5)
- **Mission.** Conditional Graph Map — directed edges expressing "if A then B" conditional relationships between MSR signals + planet/house entities.
- **Target tables.** `cgm_edges`, `cgm_nodes` (or `l25_cgm_*` keyed by chart_id).
- **Reads from.** A9 MSR + A4 Graha Sthana + A5 Bhava Vibhaga.
- **Writers.** `pipeline/writers/cgm_writer.py`.
- **Expected rows.** ~3,400 edges per ayanamsha (±5%).
- **Schema invariants.** Every edge has from_node, to_node, edge_kind, confidence ∈ [0,1].
- **Cross-asset.** Edge endpoints must exist in A9 MSR or A4 Graha Sthana.
- **Pramana checks.** No cycles in edge graph (it's a DAG); confidence values valid; all referenced node IDs exist.

### Anubandha Mandala · Matrix of linkages (anubandha_mandala, L2.5)
- **Mission.** Cross-Domain Linkage Matrix — cell-based linkages relating signal pairs to domain outcomes.
- **Target tables.** `cdlm_cells` (or `l25_cdlm_*`).
- **Reads from.** A9 MSR.
- **Writers.** `pipeline/writers/cdlm_writer.py`.
- **Expected rows.** ~400 cells per ayanamsha (±5%).
- **Schema invariants.** Every cell has (row_signal_id, col_signal_id, strength); strength ∈ [0,1].
- **Cross-asset.** Cell coordinates must map to valid MSR signal IDs.
- **Pramana checks.** Coordinates valid; strength bounded.

### Upaya Kosha · Treasury of remedies (upaya_kosha, L2.5)
- **Mission.** Remedial Matrix — 6 traditions × 18 categories of remedies tied to chart afflictions.
- **Target tables.** `rm_remedies` (or `l25_rm_*`).
- **Reads from.** A9 MSR (affliction signals).
- **Writers.** `pipeline/writers/rm_writer.py`.
- **Expected rows.** ~108 per ayanamsha (6 × 18; varies by affliction count).
- **Schema invariants.** Every remedy has tradition (∈ {classical, tantric, ayurvedic, kp, jaimini, tajaka}); category; affliction_signal_id.
- **Cross-asset.** affliction_signal_id must exist in A9 MSR.
- **Pramana checks.** Tradition values valid; affliction references resolvable.

### Sangam · Confluence (sangam, L2.5)
- **Mission.** Universal Convergence Diagram — materialized view rolling up A10 Karana Jala + A11 Anubandha Mandala into a single confluence surface.
- **Target tables.** `ucd_view` (view, not table).
- **Reads from.** A10, A11.
- **Writers.** Materialized via SQL view definition; refreshed on dependency change.
- **Expected rows.** Derived; no fixed count.
- **Schema invariants.** View definition references current versions of A10, A11 tables.
- **Cross-asset.** Stale-view detection: if A10 or A11 were rebuilt, A13 must refresh.
- **Pramana checks.** View is fresh (timestamp ≥ max(A10, A11) write time); cardinality consistent with upstream.

---

## L3 · Sutra · Meta-threads (8 assets)

### Kala Yoga · Time-synchronicity (kala_yoga, L3)
- **Mission.** Convergence map identifying time windows when multiple cycles (dashas, transits, panchanga events) align.
- **Target tables.** `time_synchronicity`.
- **Reads from.** A7 Dasha Krama + A2 Panchanga + transit ephemeris.
- **Writers.** `pipeline/writers/time_synchronicity_writer.py`.
- **Expected rows.** ~1,580 per ayanamsha.
- **Schema invariants.** Each window has start_date, end_date, convergence_strength, contributing_cycles[].
- **Cross-asset.** Cycle references must resolve to A7 dasha periods.
- **Pramana checks.** Windows chronologically ordered; strength bounded [0,1].

### Bandha · Phase-locked anchors (bandha, L3)
- **Mission.** Predicted event lattice — anchor dates derived from dasha boundaries + chakra activations + transit hits. The M6 ground truth substrate.
- **Target tables.** `phase_locked_anchors`.
- **Reads from.** A7 Dasha Krama + A14 Kala Yoga.
- **Writers.** TBD writer file.
- **Expected rows.** ~340 per ayanamsha.
- **Schema invariants.** Each anchor has predicted_date, anchor_kind, strength, source_assets[].
- **Cross-asset.** source_assets references must resolve.
- **Pramana checks.** Strength bounded; dates valid.

### Chakra Vichara · Chakra analysis (chakra_vichara, L3)
- **Mission.** Sarvatobhadra Chakra + supplementary chakras (Surya Kalanala, Chandra Kalanala, etc.) for transit interpretation.
- **Target tables.** `sarvatobhadra_chakra`, `supplementary_chakras`.
- **Reads from.** A4 Graha Sthana.
- **Writers.** TBD per chakra type.
- **Expected rows.** TBD per writer audit.
- **Schema invariants.** Chakra type ∈ known set; cell assignments valid.
- **Cross-asset.** Cell-to-planet mappings consistent across chakras.
- **Pramana checks.** Chakra completeness; no missing cells.

### Vedha Drishti · Vedha aspect analysis (vedha_drishti, L3)
- **Mission.** Vedha (obstruction) aspects extended with anchor interactions.
- **Target tables.** `vedha_extended`, `vedha_anchor_interactions`.
- **Reads from.** A4 Graha Sthana + A15 Bandha.
- **Writers.** TBD.
- **Expected rows.** TBD per writer audit.
- **Schema invariants.** Aspect type valid; participants resolvable.
- **Pramana checks.** Vedha symmetry where definitional.

### Bhrigu Kshetra · Bhrigu transit field (bhrigu_kshetra, L3)
- **Mission.** Bhrigu Bindu transits across the chart's lifetime.
- **Target tables.** `bhrigu_bindu_transits`.
- **Reads from.** A4 Graha Sthana + transit ephemeris.
- **Writers.** TBD.
- **Expected rows.** TBD.
- **Schema invariants.** Transit dates valid; Bhrigu Bindu position bounded.
- **Pramana checks.** Bhrigu Bindu = (Moon + Rahu) / 2; same formula across rebuilds.

### Tajik Varsha · Annual revolution (tajik_varsha, L3)
- **Mission.** Tajik annual chart computation including year lords (Muntha, Munthadhipati, etc.).
- **Target tables.** `tajik_varsha_year_lords`, `varsha_digest`.
- **Reads from.** A1 Pratyaksha + transit ephemeris.
- **Writers.** `pipeline/writers/tajik_varsha_year_lords_writer.py`.
- **Expected rows.** TBD per writer audit; ~one row per year of lifetime.
- **Schema invariants.** Year lords ∈ known set; Muntha Libra 7H case correctly handled (per DIS.013 resolution).
- **Pramana checks.** Muntha computation matches MSR.377 corrected version (Libra 7H, not Aries 1H).

### Sphurana · Aspect ignition (sphurana, L3)
- **Mission.** Exact aspect events across the chart's lifetime — when transiting planets form exact aspects to natal positions.
- **Target tables.** `graha_aspects_lifetime`.
- **Reads from.** A4 Graha Sthana + transit ephemeris.
- **Writers.** TBD.
- **Expected rows.** TBD.
- **Schema invariants.** Event date valid; aspect type valid; participants resolvable.
- **Pramana checks.** Aspect formulas match classical defs.

### Kala Smriti · Per-varsha digest (kala_smriti, L3)
- **Mission.** Year-by-year digest summarizing each annual chart's key features.
- **Target tables.** `varsha_digest`.
- **Reads from.** A20 Tajik Varsha.
- **Writers.** TBD.
- **Expected rows.** TBD per year of lifetime.
- **Schema invariants.** Year sequence complete; no gaps.
- **Pramana checks.** Digest summary fields populated; references back to A20 resolve.

---

## META · Synthesis layer (built atop L3)

### Meta-α (UTEE Unified Temporal Event Envelope)
- **Mission.** Roll up all L3 temporal assets into a unified lattice queryable by date.
- **Target tables.** `temporal_unified_lattice_view`.
- **Pramana checks.** View is fresh; covers all L3 temporal contributors.

### Meta-β/γ/δ/ε (Pattern catalog, Divergence ledger, Negative space, Derivation trail)
- **Target tables.** `chart_lattice_mv`.
- **Pramana checks.** Each meta layer has expected aggregate cardinality; provenance traceable.

---

## L4 · Vyavahara · Interface (3 surfaces — NOT built assets)

These are end-user surfaces, not data assets. Pariksha covers them in
Yantra-Drashta (cockpit) only. Prashna (consume) is out of scope per
master plan.

- **Prashna** · /consume chat surface — out of scope for Pariksha
- **Yantra MCP** · tool surface — out of scope (separate tooling QA)
- **Marga** · API surface — covered by Aapti-Drashta for the chart-creation endpoint

---

## How to extend this registry

When a new asset is added to the build (new writer + new build_dependencies entry):
1. Add a card here following the template above
2. Add a row to `EXPECTED_ROW_COUNTS.yaml`
3. Pramana automatically picks it up on next run

When an existing asset's expected count changes:
1. Update both this file and `EXPECTED_ROW_COUNTS.yaml`
2. Commit with a clear reason — Pariksha will use the new value on next run
