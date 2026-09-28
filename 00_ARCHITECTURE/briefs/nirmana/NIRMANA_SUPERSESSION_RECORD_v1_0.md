---
artifact: NIRMANA_SUPERSESSION_RECORD
canonical_id: NIRMANA_SUPERSESSION_RECORD
version: "1.0"
status: RULED — native decision, 2026-09-28
produced_on: 2026-09-28
decision_owner: Native (Abhisek Mohanty)
supersedes_campaign: nirmana-elevation (NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md; NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md)
successor: the Nikaṣa engine (campaign/nikasha-test, PR #2736), then an elevation campaign built on it (name to be chosen)
changelog:
  - "1.0 (2026-09-28): first record. Decision, reason, what is kept, what is off, stop switch, evidence queries."
---

# Nirmāṇa supersession record

## 1 · The decision

- **The Nirmāṇa elevation campaign is off.** It is not paused; it will not resume.
- **Reason (native, 2026-09-28):** it did not meet the quality, depth and efficiency criteria.
- **Successor:** Nikaṣa. First the Nikaṣa engine is completed and frozen (inspector, tracker,
  ledgers, four-tier template chain). Then a new elevation campaign, built on that engine,
  elevates every asset L0 → L5. The two are sequential, never concurrent.
- **One elevation definition.** Nikaṣa's nine gates are the core, for every asset. Asset-specific
  requirements may add to the core; they never replace it. A core gate that does not apply reads
  N/A with a written reason — never a silent skip.

## 2 · What is kept

- **Nirmāṇa's elevation work on assets is kept as the starting point.** Its code and data
  improvements are real and live in production; they are not reverted.
- **It is not certification.** A Nirmāṇa freeze is prior work. Every kept asset is judged afresh
  against the nine gates in the successor campaign, which fixes only the gaps it finds.
- **Evidence that this is right:** 97 of the 98 frozen assets carry at least one open Nikaṣa gap
  (572 open gaps, production ledger at `f6b1d3c5…`, 2026-09-28). The one exception,
  `ka_gochara_sweep`, is retired and inactive.
- **A second caution:** 72 of the 98 freezes were recorded under definition revision `t0`, which
  Nirmāṇa itself superseded three times (`t1`, `t2`, `t3`). Only 8 were recorded under the final
  definition `t3`. Most freezes were never re-affirmed against Nirmāṇa's own final standard.

### 2.1 · Coverage

| Layer | Frozen by Nirmāṇa | Active assets | Note |
|---|---|---|---|
| L0 Brahmagyan | 40 | 40 | all |
| L1 Gaṇita | 19 | 19 | all |
| L2 Bodha | 22 | 23 | all of Nirmāṇa's 22-asset manifest |
| L3 Kāla | 13 | 21 | includes `ka_gochara_sweep`, since retired |
| L4 Phala | 0 | 9 | none |
| L5 Mīmāṃsā | 4 | 15 | early, simple assets |
| **Total** | **98** | **127** | |

### 2.2 · Known Nikaṣa findings on kept assets (non-exhaustive)

- `bo_upaya` (L2) — rebuild fails on a foreign key, every chart (R244; owner handoff written).
- `bo_laksana`, `bo_arudha`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`,
  `bo_vargottama_dhana` (L2) — rebuild is refused by a database guard on two non-canonical charts (R243).
- `ka_gochara` (L3) — registry declares one table, the writer writes another (R240).
- `lel_events` (L5) — active, no writer (R236).
- `bg_sarvatobhadra_grid` (L0) — marked lit with no build ever; "by design" label unverified (R250).

### 2.3 · The full list

Format: `asset` (definition revision of its last freeze, date).

**L0** (40): `bg_class_lifetime_counts` (t0, 2026-09-04), `bg_class_priors` (t0, 2026-09-04), `bg_cohort` (t0, 2026-09-07), `bg_compendium_index` (t0, 2026-09-06), `bg_concordance` (t0, 2026-09-06), `bg_dasha_systems` (t0, 2026-09-06), `bg_dignity_reference` (t0, 2026-09-04), `bg_doshas` (t0, 2026-09-06), `bg_ephemeris` (t0, 2026-09-04), `bg_ephemeris_engine` (t0, 2026-09-04), `bg_formula_constants` (t0, 2026-09-04), `bg_ghatana` (t0, 2026-09-04), `bg_gochara_arcs` (t0, 2026-09-06), `bg_gochara_citation_resolution` (t0, 2026-09-04), `bg_kota_chakra_rings` (t0, 2026-09-04), `bg_kp_sublord_division` (t0, 2026-09-04), `bg_medical_mappings` (t0, 2026-09-04), `bg_muhurta_lattice` (t0, 2026-09-04), `bg_nakshatra` (t0, 2026-09-04), `bg_nakshatra_medical` (t0, 2026-09-04), `bg_ontology` (t0, 2026-09-04), `bg_panchanga` (t0, 2026-09-04), `bg_parihara_rules` (t0, 2026-09-06), `bg_phaladeepika_latta` (t0, 2026-09-04), `bg_prashna_rules` (t0, 2026-09-04), `bg_reference` (t0, 2026-09-04), `bg_remedies` (t0, 2026-09-04), `bg_rules` (t0, 2026-09-06), `bg_sarvatobhadra_grid` (t0, 2026-09-04), `bg_sign_medical` (t0, 2026-09-04), `bg_sky_calendar` (t0, 2026-09-04), `bg_text_index` (t0, 2026-09-06), `bg_texts` (t0, 2026-09-04), `bg_transit_engine` (t0, 2026-09-04), `bg_transit_rules` (t0, 2026-09-04), `bg_vastu_directions` (t0, 2026-09-04), `bg_vedha_malefic_scale` (t0, 2026-09-03), `bg_vidhi_floors` (t0, 2026-09-05), `bg_vidhi_primitives` (t0, 2026-09-04), `bg_yogas` (t0, 2026-09-06)

**L1** (19): `ga_ayurdaya` (t0, 2026-09-07), `ga_condition` (t0, 2026-09-07), `ga_dashas` (t0, 2026-09-07), `ga_medical` (t0, 2026-09-08), `ga_nakshatra` (t0, 2026-09-07), `ga_panchanga` (t0, 2026-09-07), `ga_positions` (t0, 2026-09-07), `ga_prashna` (t0, 2026-09-07), `ga_sade_sati` (t0, 2026-09-08), `ga_sensitive` (t0, 2026-09-07), `ga_sensitive_degree` (t0, 2026-09-07), `ga_strength` (t0, 2026-09-07), `ga_structural` (t0, 2026-09-08), `ga_tajaka` (t0, 2026-09-08), `ga_transit_anchors` (t0, 2026-09-07), `ga_vargas` (t0, 2026-09-07), `ga_vastu` (t0, 2026-09-08), `ga_vichara` (t0, 2026-09-08), `ga_yoga` (t0, 2026-09-08)

**L2** (22): `bo_anveshana` (t2, 2026-09-10), `bo_arudha` (t1, 2026-09-10), `bo_bimba` (t3, 2026-09-11), `bo_cdlm_summary` (t1, 2026-09-09), `bo_cgm_motifs` (t1, 2026-09-09), `bo_cgm_paths` (t1, 2026-09-09), `bo_chart_gestalt` (t2, 2026-09-10), `bo_drishti` (t1, 2026-09-09), `bo_karanajala` (t3, 2026-09-11), `bo_laksana` (t1, 2026-09-08), `bo_laksana_rerank` (t3, 2026-09-11), `bo_nakshatra_semantic` (t3, 2026-09-11), `bo_pramana_mapa` (t2, 2026-09-10), `bo_pratijna` (t1, 2026-09-09), `bo_samskara` (t3, 2026-09-11), `bo_samvada` (t2, 2026-09-11), `bo_sangati` (t3, 2026-09-11), `bo_special_lagna` (t3, 2026-09-11), `bo_sudarshana` (t1, 2026-09-10), `bo_upaya` (t1, 2026-09-10), `bo_vargottama_dhana` (t3, 2026-09-11), `bo_yantra_mechanism` (t1, 2026-09-09)

**L3** (13): `ka_dasha_kala` (t0, 2026-09-07), `ka_gochara` (t1, 2026-09-10), `ka_gochara_resonance` (t0, 2026-09-07), `ka_gochara_sweep` (t1, 2026-09-08), `ka_graha_sancara` (t0, 2026-09-06), `ka_kota_chakra` (t0, 2026-09-07), `ka_moorti_nirnaya` (t0, 2026-09-07), `ka_muhurta_seva` (t0, 2026-09-06), `ka_sudarshana_varsha` (t0, 2026-09-07), `ka_tithi_pravesha` (t0, 2026-09-07), `ka_tulana` (t2, 2026-09-10), `ka_vedha_gochara` (t0, 2026-09-07), `ka_yojaka` (t2, 2026-09-10)

**L5** (4): `lel_events` (t0, 2026-09-06), `mi_jivanaghatana` (t0, 2026-09-06), `mi_kula` (t0, 2026-09-06), `mi_vistara` (t0, 2026-09-06)

## 3 · What is off

- **The campaign:** no autonomous conductor or layer supervisor may run.
- **Stop switch set (2026-09-28):** a `NIRMANA_HOLD` file at the root of every worktree Nirmāṇa's
  sessions ran from — `/Users/Dev/nirmana-s/{conductor,l0,l1,l2,l3,l4,l5,l5-*}` and the main
  checkout `/Users/Dev/Vibe-Coding/Apps/Madhav`. These are local, uncommitted files (the root-file
  policy forbids committing them); this record is their durable counterpart.
- **Its governing documents** are marked SUPERSEDED in place (plan, execution prompt, campaign state).
  Their bodies are unchanged, kept as history.
- **Not changed, deliberately:** the database row
  `nirmana_evidence.nirmana_elevation_campaign_definitions` for revision `t3-2026-09-11-8b884eac`
  still reads `frozen`. This session is read-only against production. If the native wants the
  database to say "superseded" as well, that is a separate, authorized write.

## 4 · What is NOT affected

- **The engine campaign** (`campaign/nirmana-engine`, `/Users/Dev/madhav-engine`) — named "Nirmāṇa"
  but a different campaign; Nikaṣa depends on it. It does not read `NIRMANA_HOLD`.
- **L3 Gochara** (`l3/gochara-autonomous-wp0-7`), **L0 execution**, **Pūrṇa**, **Jātaka** — separate
  campaigns with their own switches; untouched.

## 5 · Evidence (re-runnable, read-only)

```sql
-- frozen assets per layer (latest freeze per asset)
with f as (select distinct on (entity_id) entity_id, layer, definition_revision, recorded_at
           from nirmana_evidence.nirmana_elevation_campaign_events
           where event_type = 'asset_frozen' order by entity_id, recorded_at desc)
select layer, count(*) from f group by layer order by layer;

-- campaign definition revisions
select definition_revision, definition_status, created_at, superseded_at
from nirmana_evidence.nirmana_elevation_campaign_definitions order by created_at;
```

- Last Nirmāṇa commit: `badc3f9bc`, 2026-09-09 04:20 IST. Last evidence event: 2026-09-11 17:25 UTC.
- Session worktrees idle since 2026-09-11 at the latest.
