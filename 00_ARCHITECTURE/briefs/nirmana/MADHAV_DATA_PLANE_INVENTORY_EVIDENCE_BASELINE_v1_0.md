---
artifact: MADHAV_DATA_PLANE_INVENTORY_EVIDENCE_BASELINE
version: "1.0"
status: REVISION_PINNED_BASELINE
produced_on: 2026-09-13
observed_at: 2026-09-13T12:30:00+05:30
session_id: MADHAV-DATA-PLANE-EXECUTION-FOUNDATION-20260913
source_revision: 9c497f3a7d500c18565e7bf0cde6d5bb56abb7fa
writer_digest_source: platform/src/generated/nirmana-writer-digests.json
writer_digest_sha256: eeda56018985b18994aae0b6802e7db8988cb4257a9a7e96956497ef184edb7a
layer_pin_source: platform/src/generated/nirmana-analysis-layer-pins.json
layer_pin_sha256: 2bdbdd753cc30d3f6c2168a6d9778f1a710c87f1089eef963d57bc3e39cc1650
scope: "Generated identity and receipt metadata only; no live population, private-row, deployment, source-rights, serving or empirical certification."
changelog:
  - "1.0: Re-measured 123 generated writers plus six generated non-writers, reconciled the 129 operational identities with the frozen 128 formal receipt denominator, and recorded additional answer authorities outside both counts."
---

# Madhav data-plane inventory and evidence baseline

## 1. Measurement boundary

This baseline directly observes the two checked-in generated files at the pinned source revision. Counts and names below are deterministic measurements of those files, not database population, deployed state, health, consumer use, value, source rights or empirical performance. No private row was inspected.

The source files report schema versions `nirmana-writer-digest-inventory/v1` and `nirmana-analysis-layer-pins/v1`. The writer file contains 123 unique keys. The layer-pin file contains six non-writer identities and per-layer formal receipt counts totaling 128.

## 2. Reconciled census

| Layer | Writer identities | Non-writer identities | Operational identities | Formal receipt count | Direct observation |
|---|---:|---:|---:|---:|---|
| L0 Brahmagyan | 36 | 4 | 40 | 40 | Generated digest keys + L0 pin |
| L1 Gaṇita | 19 | 0 | 19 | 19 | Generated digest keys + L1 pin |
| L2 Bodha | 23 | 0 | 23 | 22 | Generated digest keys + L2 pin; `bo_grounding` is supporting status |
| L3 Kāla | 22 | 1 | 23 | 23 | Generated digest keys + L3 pin |
| L4 Phala | 9 | 0 | 9 | 9 | Generated digest keys + L4 pin |
| L5 Mīmāṃsā | 14 | 1 | 15 | 15 | Generated digest keys + L5 pin |
| **Total** | **123** | **6** | **129** | **128** | Recomputed totals |

`bo_grounding` is an operational generated writer, but it is support outside the frozen formal L2 denominator of 22. Therefore `123 + 6 = 129` is the current operational identity census while `40 + 19 + 22 + 23 + 9 + 15 = 128` is the formal campaign receipt denominator. Neither is a value score, health statement or reopening of a historical seal.

## 3. Complete generated writer identities

### L0 Brahmagyan — 36

`bg_class_lifetime_counts`, `bg_class_priors`, `bg_cohort`, `bg_compendium_index`, `bg_concordance`, `bg_dasha_systems`, `bg_dignity_reference`, `bg_doshas`, `bg_ephemeris`, `bg_formula_constants`, `bg_ghatana`, `bg_gochara_arcs`, `bg_kota_chakra_rings`, `bg_kp_sublord_division`, `bg_medical_mappings`, `bg_muhurta_lattice`, `bg_nakshatra`, `bg_nakshatra_medical`, `bg_ontology`, `bg_parihara_rules`, `bg_phaladeepika_latta`, `bg_prashna_rules`, `bg_reference`, `bg_remedies`, `bg_rules`, `bg_sign_medical`, `bg_sky_calendar`, `bg_text_index`, `bg_texts`, `bg_transit_engine`, `bg_transit_rules`, `bg_vastu_directions`, `bg_vedha_malefic_scale`, `bg_vidhi_floors`, `bg_vidhi_primitives`, `bg_yogas`.

### L1 Gaṇita — 19

`ga_ayurdaya`, `ga_condition`, `ga_dashas`, `ga_medical`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_prashna`, `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_transit_anchors`, `ga_vargas`, `ga_vastu`, `ga_vichara`, `ga_yoga`.

### L2 Bodha — 23 including support

`bo_anveshana`, `bo_arudha`, `bo_bimba`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_karanajala`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_special_lagna`, `bo_sudarshana`, `bo_upaya`, `bo_vargottama_dhana`, `bo_yantra_mechanism`.

### L3 Kāla — 22

`ka_avadhi`, `ka_bhavishya_lekha`, `ka_dasha_kala`, `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_v3_century_materialize`, `ka_graha_sancara`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_kota_chakra`, `ka_kshetra`, `ka_moorti_nirnaya`, `ka_muhurta_seva`, `ka_sangam`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`, `ka_tulana`, `ka_vedha_gochara`, `ka_vighnakara`, `ka_yojaka`.

### L4 Phala — 9

`ph_muhurta`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`, `ph_pratikara`, `ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`.

### L5 Mīmāṃsā — 14

`mi_abhilekha`, `mi_adhilepa`, `mi_bhara`, `mi_bhavisya`, `mi_darshana`, `mi_gunanaka`, `mi_jivanaghatana`, `mi_kula`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`, `mi_sankalpa`, `mi_seva`, `mi_vistara`.

## 4. Generated non-writer identities — six

| Layer | Identity | Generated classification |
|---|---|---|
| L0 | `bg_ephemeris_engine` | non-writer service |
| L0 | `bg_gochara_citation_resolution` | non-writer/migration-owned resolver |
| L0 | `bg_panchanga` | non-writer service |
| L0 | `bg_sarvatobhadra_grid` | non-writer source/geometry asset |
| L3 | `ka_gochara_sweep` | non-writer service/interface |
| L5 | `lel_events` | non-writer observation/source asset |

## 5. Generated convergence pins

| Layer | Convergence commit | Writer inventory SHA-256 | Receipt count |
|---|---|---|---:|
| L0 | `49bb5c98b864a2cb2fee037cdb7f14f6892a8263` | `5125cccb68715ebc6054c3ce47bc4c047684445249503a4c4dabd85e0d036178` | 40 |
| L1 | `d56bb9fd50d42c1045c7aac2cee19478f216b174` | `55984558527e9c1b95da608839b69a4dde255b3855ac6839980c26b24c2b17e0` | 19 |
| L2 | `a3da94d408e64a3b01f965340833dd46b377b5f3` | `863a3e6e6b67320fd5de7d00c6093307a9f2c816e39af09c4b4bc9341af8169b` | 22 |
| L3 | `7ddaeaa55768732189135cfc97b7bf12e55a8386` | `3cfdd5df83f47b7969db8e98bc5305f50841a7ef3ebacbf0d80e9d5aae94396c` | 23 |
| L4 | `be470cb8fa289c65fe4e273abe1cd1210e96f805` | `486959b1df74015873b326c2b5d58aa00865a47e6116b3b0c39f479f978d66f9` | 9 |
| L5 | `fd4c102e3ce5b4f23782bdce12c84b84a4fe9ba5` | `df295e3ac158980ee69a210ecfd6252ffa2a4cb2db1ae8e732af7814240883bc` | 15 |

These are generated evidence pins, not proof that the commits are deployed or that every identity is populated, healthy, integrated or valuable.

## 6. Additional answer authorities outside the 129 denominator

These categories are directly observed in the proposed asset register and source anchors, but are not promoted into writer/non-writer membership by this baseline:

1. numerical/on-demand authorities: `ga_chart_service`, Ganita engine, PyJHora compute, ephemeris/PyHora routes;
2. capability/field discovery: retrieval registry types/catalog, Vidhi registry/parity;
3. L2 query projections and hydration such as `query_signals.ts`;
4. deterministic D8 assessment, D9 judgment and D10 pact operators;
5. synergy, aggregation and whole-chart spine bundles;
6. Paripraśna adaptive pipeline, synthesis, reading-part assembly, persistence and continuation;
7. managed MCP inquiry/status, raw MCP tools/resources/prompts and response budgeting;
8. L4 domain and L5 discovery/insight/retrodiction retrieval authorities;
9. observation intake adapters including MCP LEL writer, admin/timeline/creation/chat paths;
10. protected claim authorities `brahma_prospective_ledger` and `brahma_mimamsa_prediction_ledger`;
11. model registries/pins, snapshots, scorecard and qualification services;
12. calendar/profile/source-reader/export/share/operator consumers.

Their inclusion would require an approved inventory schema and exact identity/owner audit. They remain explicit supporting authorities, not an invented expanded denominator.

## 7. Historical-count reconciliation

Historical seals retain their exact claims: the L1 closure describes a 15-asset picture, the historical L3 close describes 12, and the L5 seal describes 12. The current generated inventory is broader: L1 19 writers, L3 22 writers plus one non-writer, and L5 14 writers plus one non-writer. These are scope/revision differences, not proof that either historical record was false. Historical closures remain receipts for the assets, tests and revisions they actually covered; the generated census is the planning/execution baseline at `9c497f3a7`.

The formal campaign denominator remains 128 despite the 129 operational identities because the frozen L2 receipt count excludes supporting `bo_grounding`. Future audits may identify additional services or historical authorities; they must state whether they are inside or outside the formal denominator and may not change it by implication.

## 8. Evidence classification and limitations

| Claim | Evidence class | Confidence and limit |
|---|---|---|
| 123 writer keys and per-prefix counts | Direct generated-file measurement | Exact for pinned file/revision; not live runtime |
| Six non-writer IDs and receipt counts | Direct generated-file measurement | Exact for pinned file/revision; not health/population |
| 129 operational vs 128 formal | Deterministic reconciliation | Depends on `bo_grounding` support classification recorded by proposal/strategy; no denominator mutation |
| Additional answer authorities | Direct source/register observation with grouped inference | Category-level only; not a complete caller/runtime census |
| Historical/current count differences | Historical receipt comparison | Exact only for cited seal scope; no current certification |

