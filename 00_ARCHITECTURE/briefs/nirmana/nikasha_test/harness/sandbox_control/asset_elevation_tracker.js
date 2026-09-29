window.ASSET_DATA={
 "generated": "2026-09-26T22:14:36+05:30",
 "gates": [
  {
   "key": "Ldgr",
   "label": "derivation ledger",
   "applies": "always",
   "claim": "every derived value names the upstream fact_id it reads, and those ids resolve"
  },
  {
   "key": "Idem",
   "label": "idempotency",
   "applies": "always",
   "claim": "a rebuild replaces its own rows; it never accretes (CLAUDE.md \u00a7N.3)"
  },
  {
   "key": "Earn",
   "label": "earned signal",
   "applies": "always",
   "claim": "every status/grade/PASS has a detector measuring that specific claim (\u00a7N.8)"
  },
  {
   "key": "Null",
   "label": "honest null",
   "applies": "always",
   "claim": "an underivable value is emitted as null, not as a plausible default (\u00a7N.7.6)"
  },
  {
   "key": "Vocab",
   "label": "vocabulary conformance",
   "applies": "always",
   "claim": "one canonical id per thing, one closed alias set, no free-text synonym"
  },
  {
   "key": "Carr",
   "label": "source carriage",
   "applies": "always",
   "claim": "what the asset restates from a source matches it; what it computes reproduces a second way; a witness disagreement is carried, not settled \u2014 ONE applicable check from CARRIAGE_MENU, run"
  },
  {
   "key": "Narr",
   "label": "narration fidelity",
   "applies": "emits prose",
   "claim": "prose restates cited facts and does not re-derive them (\u00a7N.7)"
  },
  {
   "key": "Dens",
   "label": "serving density",
   "applies": "is served",
   "claim": "confirmed vs catalog-only counted separately; dense layer survives a trim (\u00a7N.6)"
  },
  {
   "key": "Build",
   "label": "buildability",
   "applies": "always",
   "claim": "the orchestrator can dispatch the asset and a triggered rebuild produces the correct result \u2014 six static checks plus a dry-run proof"
  }
 ],
 "domain_menu": [
  {
   "key": "D1",
   "label": "source correspondence",
   "applies": "the asset restates a cited classical source",
   "check": "the restatement against the passage \u2014 prerequisites, exceptions, cancellations included"
  },
  {
   "key": "D2",
   "label": "witness carriage",
   "applies": "two admitted authorities cover the same claim",
   "check": "the disagreement is carried forward as school disagreement, never averaged or silently resolved"
  },
  {
   "key": "D3",
   "label": "independent re-derivation",
   "applies": "the value is computable a second way",
   "check": "compute it that way and compare within a declared tolerance"
  }
 ],
 "layers": {
  "L0": {
   "name": "Brahmagyan",
   "prefix": "bg_",
   "scoring": "fidelity",
   "instance": "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",
   "registry_reason": null,
   "n_assets": 40,
   "assets": [
    {
     "id": "bg_class_lifetime_counts",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_class_priors",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ghatana"
      ],
      "count_sql": "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='ne_v01' AND fact_kind='lifetime_count_per_100y'",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_kshetra"
      ],
      "table_exists": true,
      "columns": 13,
      "rows": 177
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_class_priors",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_class_priors",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM brahma_class_priors WHERE prior_version='1.0'",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "mi_kula"
      ],
      "table_exists": true,
      "columns": 13,
      "rows": 177
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_cohort",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_synthetic_cohort",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ephemeris_engine"
      ],
      "count_sql": "SELECT (SELECT COUNT(*) FROM bg_synthetic_cohort) + (SELECT COUNT(*) FROM bg_synthetic_cohort_md) AS count",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_kshetra"
      ],
      "table_exists": true,
      "columns": 11,
      "rows": 10000
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_compendium_index",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_compendium_index",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_reference",
       "bg_texts"
      ],
      "count_sql": "SELECT count(*) FROM brahma_compendium_index",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 13,
      "rows": 9571
     },
     "brief": null,
     "gaps_open": 7,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "7 gap(s), no certification yet"
    },
    {
     "id": "bg_concordance",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "classical_attributions",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_reference",
       "bg_rules",
       "bg_text_index",
       "bg_texts"
      ],
      "count_sql": "SELECT count(*) FROM classical_attributions",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 11,
      "rows": 721
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_dasha_systems",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_dasha_systems",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ontology"
      ],
      "count_sql": "SELECT\n  (SELECT count(*) FROM brahma_dasha_systems) +\n  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dasha_system') +\n  (SELECT count(*) FROM reference_dasha_systems) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_rules"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 14,
      "rows": 20
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_dignity_reference",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_dignity_reference",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT (SELECT COUNT(*) FROM bg_dignity_reference) + (SELECT COUNT(*) FROM bg_avastha_schemes) + (SELECT COUNT(*) FROM bg_combustion_orbs) + (SELECT COUNT(*) FROM bg_graha_naisargika_friendship) + (SELECT COUNT(*) FROM bg_motion_state_thresholds) AS count",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_vighnakara"
      ],
      "table_exists": true,
      "columns": 13,
      "rows": 9
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_doshas",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_dosha_catalog",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ontology"
      ],
      "count_sql": "SELECT\n  (SELECT count(*) FROM brahma_dosha_catalog) +\n  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'dosha') +\n  (SELECT count(*) FROM reference_doshas) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_parihara_rules"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 14,
      "rows": 79
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_ephemeris",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "ephemeris_daily",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT count(*) FROM ephemeris_daily",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_gochara_arcs"
      ],
      "consumers_cross_layer": [
       "ka_gochara",
       "ka_graha_sancara",
       "ka_kota_chakra",
       "ka_moorti_nirnaya",
       "ka_vedha_gochara"
      ],
      "table_exists": true,
      "columns": 15,
      "rows": 41260
     },
     "brief": {
      "path": "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_EPHEMERIS_ELEVATION_BRIEF_v1_0.md",
      "version": "1.0",
      "status": "PILOT_DRAFT",
      "shape": {
       "identity": true,
       "inputs / DAG": true,
       "correctness": true,
       "data sufficiency": true,
       "consumers": true,
       "value / target": true,
       "synergy": true,
       "knowledge-time": true,
       "change packet": true,
       "evidence": true
      },
      "shape_present": 10,
      "shape_total": 10,
      "shape_complete": true,
      "shape_missing": []
     },
     "gaps_open": 12,
     "opps_open": 4,
     "gaps_total": 16,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "12 gap(s), no certification yet"
    },
    {
     "id": "bg_ephemeris_engine",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": null,
      "storage_type": "service",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": false,
      "depends_on": [],
      "count_sql": null,
      "integrity_check": false,
      "consumers_in_layer": [
       "bg_cohort"
      ],
      "consumers_cross_layer": [],
      "table_exists": false,
      "columns": null,
      "rows": null
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_formula_constants",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_formula_constants",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT count(*) FROM brahma_formula_constants",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "mi_gunanaka",
       "mi_pariksha",
       "mi_pramana"
      ],
      "table_exists": true,
      "columns": 9,
      "rows": 17
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_ghatana",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_event_ontology",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT (SELECT count(*) FROM brahma_event_ontology) + (SELECT count(*) FROM brahma_activity_ontology) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_class_lifetime_counts"
      ],
      "consumers_cross_layer": [
       "ka_avadhi",
       "ka_taranga",
       "ka_yojaka",
       "mi_jivanaghatana",
       "mi_pramana"
      ],
      "table_exists": true,
      "columns": 19,
      "rows": 27
     },
     "brief": null,
     "gaps_open": 3,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "3 gap(s), no certification yet"
    },
    {
     "id": "bg_gochara_arcs",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_gochara_arcs",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ephemeris"
      ],
      "count_sql": "SELECT COUNT(*) FROM bg_gochara_arcs",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 16,
      "rows": 33933
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_gochara_citation_resolution",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_gochara_citation_resolution",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": false,
      "depends_on": [
       "bg_texts"
      ],
      "count_sql": "SELECT COUNT(*) FROM bg_gochara_citation_resolution",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 9,
      "rows": 14
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_kota_chakra_rings",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_kota_chakra_rings",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_kota_chakra_rings",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_kota_chakra"
      ],
      "table_exists": true,
      "columns": 9,
      "rows": 27
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_kp_sublord_division",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_kp_sublord_division",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_nakshatra"
      ],
      "count_sql": "SELECT COUNT(*) FROM bg_kp_sublord_division",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ga_nakshatra"
      ],
      "table_exists": true,
      "columns": 14,
      "rows": 249
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_medical_mappings",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_medical_mappings",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_medical_mappings",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 8,
      "rows": 21
     },
     "brief": null,
     "gaps_open": 2,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "2 gap(s), no certification yet"
    },
    {
     "id": "bg_muhurta_lattice",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_muhurta_lattice",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_muhurta_lattice",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 16,
      "rows": 8579
     },
     "brief": null,
     "gaps_open": 6,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "6 gap(s), no certification yet"
    },
    {
     "id": "bg_nakshatra",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "reference_nakshatra",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT (SELECT COUNT(*) FROM reference_nakshatra) + (SELECT COUNT(*) FROM reference_nakshatra_pada) + (SELECT COUNT(*) FROM reference_nakshatra_matrix) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_kp_sublord_division"
      ],
      "consumers_cross_layer": [
       "ga_nakshatra"
      ],
      "table_exists": true,
      "columns": 46,
      "rows": 28
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_nakshatra_medical",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_nakshatra_medical",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_nakshatra_medical",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 6,
      "rows": 27
     },
     "brief": null,
     "gaps_open": 0,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 9,
     "certs_total": 9,
     "required": 9,
     "state": "ELEVATED",
     "why": "every gate certified or disposed; no open gap"
    },
    {
     "id": "bg_ontology",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_ontology",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT count(*) FROM brahma_ontology",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_dasha_systems",
       "bg_doshas",
       "bg_reference",
       "bg_yogas"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 9,
      "rows": 742
     },
     "brief": {
      "path": "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md",
      "version": "1.0",
      "status": "PILOT_DRAFT",
      "shape": {
       "identity": true,
       "inputs / DAG": true,
       "correctness": true,
       "data sufficiency": true,
       "consumers": true,
       "value / target": true,
       "synergy": false,
       "knowledge-time": true,
       "change packet": true,
       "evidence": true
      },
      "shape_present": 9,
      "shape_total": 10,
      "shape_complete": false,
      "shape_missing": [
       "synergy"
      ]
     },
     "gaps_open": 15,
     "opps_open": 6,
     "gaps_total": 23,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "15 gap(s), no certification yet"
    },
    {
     "id": "bg_panchanga",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": null,
      "storage_type": "service",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": false,
      "depends_on": [],
      "count_sql": null,
      "integrity_check": false,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ga_panchanga"
      ],
      "table_exists": false,
      "columns": null,
      "rows": null
     },
     "brief": {
      "path": "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md",
      "version": "1.0",
      "status": "PILOT_DRAFT",
      "shape": {
       "identity": true,
       "inputs / DAG": true,
       "correctness": true,
       "data sufficiency": true,
       "consumers": true,
       "value / target": true,
       "synergy": false,
       "knowledge-time": true,
       "change packet": true,
       "evidence": true
      },
      "shape_present": 9,
      "shape_total": 10,
      "shape_complete": false,
      "shape_missing": [
       "synergy"
      ]
     },
     "gaps_open": 8,
     "opps_open": 2,
     "gaps_total": 10,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "8 gap(s), no certification yet"
    },
    {
     "id": "bg_parihara_rules",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_parihara_rules",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_doshas",
       "bg_texts"
      ],
      "count_sql": "SELECT (SELECT COUNT(*) FROM bg_parihara_rules) + (SELECT COUNT(*) FROM bg_muhurta_activity_rules) + (SELECT COUNT(*) FROM bg_muhurta_factor_census)",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 14,
      "rows": 60
     },
     "brief": null,
     "gaps_open": 7,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "7 gap(s), no certification yet"
    },
    {
     "id": "bg_phaladeepika_latta",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_phaladeepika_latta",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_phaladeepika_latta",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_vedha_gochara"
      ],
      "table_exists": true,
      "columns": 9,
      "rows": 8
     },
     "brief": null,
     "gaps_open": 3,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "3 gap(s), no certification yet"
    },
    {
     "id": "bg_prashna_rules",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": null,
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT (SELECT COUNT(*) FROM bg_prashna_lagna_methods) + (SELECT COUNT(*) FROM bg_prashna_tajik_yogas) + (SELECT COUNT(*) FROM bg_prashna_significators) + (SELECT COUNT(*) FROM bg_prashna_fructification_rules) + (SELECT COUNT(*) FROM bg_prashna_special_techniques) AS count",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ga_prashna"
      ],
      "table_exists": false,
      "columns": null,
      "rows": null
     },
     "brief": null,
     "gaps_open": 3,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "3 gap(s), no certification yet"
    },
    {
     "id": "bg_reference",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "reference_planets",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ontology"
      ],
      "count_sql": "SELECT (SELECT count(*) FROM reference_planets) + (SELECT count(*) FROM reference_signs) + (SELECT count(*) FROM reference_aspects) + (SELECT count(*) FROM reference_vargas) + (SELECT count(*) FROM reference_houses) + (SELECT count(*) FROM reference_strength_systems) + (SELECT count(*) FROM reference_karakas) + (SELECT count(*) FROM reference_upagrahas) + (SELECT count(*) FROM reference_constants) + (SELECT count(*) FROM reference_topic_tags) + (SELECT count(*) FROM reference_glossary) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_compendium_index",
       "bg_concordance",
       "bg_text_index"
      ],
      "consumers_cross_layer": [
       "ga_sensitive"
      ],
      "table_exists": true,
      "columns": 14,
      "rows": 11
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_remedies",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_remedy_corpus",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_texts"
      ],
      "count_sql": "SELECT count(*) FROM brahma_remedy_corpus",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 26,
      "rows": 341
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_rules",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "sutravali_rules",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_dasha_systems",
       "bg_texts",
       "bg_yogas"
      ],
      "count_sql": "SELECT count(*) FROM sutravali_rules",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_concordance"
      ],
      "consumers_cross_layer": [
       "bo_laksana",
       "mi_kula"
      ],
      "table_exists": true,
      "columns": 14,
      "rows": 3002
     },
     "brief": {
      "path": "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_RULES_ELEVATION_BRIEF_v1_0.md",
      "version": "1.0",
      "status": "PILOT_DRAFT",
      "shape": {
       "identity": true,
       "inputs / DAG": true,
       "correctness": true,
       "data sufficiency": true,
       "consumers": true,
       "value / target": true,
       "synergy": false,
       "knowledge-time": true,
       "change packet": true,
       "evidence": true
      },
      "shape_present": 9,
      "shape_total": 10,
      "shape_complete": false,
      "shape_missing": [
       "synergy"
      ]
     },
     "gaps_open": 12,
     "opps_open": 4,
     "gaps_total": 17,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "12 gap(s), no certification yet"
    },
    {
     "id": "bg_sarvatobhadra_grid",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_sarvatobhadra_grid",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": false,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_sarvatobhadra_grid",
      "integrity_check": false,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_vedha_gochara"
      ],
      "table_exists": true,
      "columns": 10,
      "rows": 0
     },
     "brief": {
      "path": "00_ARCHITECTURE/briefs/nirmana/l0_assets/BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF_v1_0.md",
      "version": "1.0",
      "status": "PILOT_DRAFT",
      "shape": {
       "identity": true,
       "inputs / DAG": true,
       "correctness": true,
       "data sufficiency": true,
       "consumers": true,
       "value / target": true,
       "synergy": false,
       "knowledge-time": true,
       "change packet": true,
       "evidence": true
      },
      "shape_present": 9,
      "shape_total": 10,
      "shape_complete": false,
      "shape_missing": [
       "synergy"
      ]
     },
     "gaps_open": 6,
     "opps_open": 2,
     "gaps_total": 8,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "6 gap(s), no certification yet"
    },
    {
     "id": "bg_sign_medical",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_sign_medical",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_sign_medical",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 7,
      "rows": 12
     },
     "brief": null,
     "gaps_open": 2,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "2 gap(s), no certification yet"
    },
    {
     "id": "bg_sky_calendar",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_sky_calendar",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_sky_calendar",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_gochara_v3_century_materialize"
      ],
      "table_exists": true,
      "columns": 17,
      "rows": 31081
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_text_index",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "classical_text_chunks",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_reference",
       "bg_texts"
      ],
      "count_sql": "SELECT count(DISTINCT topic_tag) AS count FROM classical_text_chunks WHERE embedding IS NOT NULL AND topic_tag IS NOT NULL",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_concordance"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 26,
      "rows": 10651
     },
     "brief": null,
     "gaps_open": 7,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "7 gap(s), no certification yet"
    },
    {
     "id": "bg_texts",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "classical_text_chunks",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT count(*) FROM classical_text_chunks",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_compendium_index",
       "bg_concordance",
       "bg_gochara_citation_resolution",
       "bg_parihara_rules",
       "bg_remedies",
       "bg_rules",
       "bg_text_index",
       "bg_yogas"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 26,
      "rows": 10651
     },
     "brief": null,
     "gaps_open": 6,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "6 gap(s), no certification yet"
    },
    {
     "id": "bg_transit_engine",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_transit_engine",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": false,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_transit_engine",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 6,
      "rows": 9
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_transit_rules",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_transit_rules",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_transit_rules",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_gochara",
       "ka_gochara_resonance",
       "ka_moorti_nirnaya",
       "ka_sangam",
       "ka_vedha_gochara",
       "ka_yojaka"
      ],
      "table_exists": true,
      "columns": 8,
      "rows": 76
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 5,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_vastu_directions",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_vastu_directions",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT (SELECT COUNT(*) FROM bg_vastu_directions) + (SELECT COUNT(*) FROM bg_vastu_direction_remedials) AS count",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 8,
      "rows": 8
     },
     "brief": null,
     "gaps_open": 5,
     "opps_open": 0,
     "gaps_total": 6,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "5 gap(s), no certification yet"
    },
    {
     "id": "bg_vedha_malefic_scale",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "bg_vedha_malefic_scale",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "SELECT COUNT(*) FROM bg_vedha_malefic_scale",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [
       "ka_vedha_gochara"
      ],
      "table_exists": true,
      "columns": 7,
      "rows": 5
     },
     "brief": null,
     "gaps_open": 3,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "3 gap(s), no certification yet"
    },
    {
     "id": "bg_vidhi_floors",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "vidhi_floor_items",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "DRAFT",
      "has_writer": true,
      "depends_on": [
       "bg_vidhi_primitives"
      ],
      "count_sql": "SELECT\n  (SELECT count(*) FROM vidhi_intent_floors) +\n  (SELECT count(*) FROM vidhi_floor_items) AS count",
      "integrity_check": true,
      "consumers_in_layer": [],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 7,
      "rows": 409
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_vidhi_primitives",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "vidhi_primitives",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [],
      "count_sql": "(SELECT COUNT(*) FROM vidhi_primitives)",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_vidhi_floors"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 11,
      "rows": 60
     },
     "brief": null,
     "gaps_open": 4,
     "opps_open": 0,
     "gaps_total": 4,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "4 gap(s), no certification yet"
    },
    {
     "id": "bg_yogas",
     "layer": "L0",
     "scoring": "fidelity",
     "registry": {
      "target_table": "brahma_yoga_catalog",
      "storage_type": "postgres_table",
      "scope": "global",
      "is_active": true,
      "catalog_status": "CURRENT",
      "has_writer": true,
      "depends_on": [
       "bg_ontology",
       "bg_texts"
      ],
      "count_sql": "SELECT\n  (SELECT count(*) FROM brahma_yoga_catalog) +\n  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +\n  (SELECT count(*) FROM reference_yogas) +\n  (SELECT count(*) FROM brahma_yoga_source_chunks) AS count",
      "integrity_check": true,
      "consumers_in_layer": [
       "bg_rules"
      ],
      "consumers_cross_layer": [],
      "table_exists": true,
      "columns": 19,
      "rows": 233
     },
     "brief": null,
     "gaps_open": 6,
     "opps_open": 0,
     "gaps_total": 7,
     "certified": 0,
     "certs_total": 0,
     "required": 9,
     "state": "GAPS_REGISTERED",
     "why": "6 gap(s), no certification yet"
    }
   ]
  }
 },
 "ledger_bad_lines": 0,
 "gaps_path": "00_ARCHITECTURE/briefs/nirmana/nikasha_test/harness/sandbox_control/asset_gaps.jsonl",
 "certs_path": "00_ARCHITECTURE/briefs/nirmana/nikasha_test/harness/sandbox_control/asset_certs.jsonl"
};
window.dispatchEvent(new Event('asset-data'));
