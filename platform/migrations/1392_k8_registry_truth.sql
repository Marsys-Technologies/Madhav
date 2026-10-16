-- Migration 1392: K8-REG registry truth (pre-build, SR-A4-01).
-- UPDATE existing ka_* rows only; no activation, output deletion or lifecycle cutover.
-- Number reserved above origin/main and all 188 advertised kalayantra/* heads
-- inspected 2026-10-16 (highest 1386); no public CREATE/ALTER is required.
-- Source contracts: KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §§7–9;
-- writers and source-bound tests pin the corrected read edges and substep shapes.
-- (I) INTERPRETATION: retain service/runtime ordering edges for compatible legacy
-- dispatch; add direct SQL reads, remove the already-retired grid (1360).
-- (I) INTERPRETATION: preserve accepted integrity SQL and generation selection.
-- K6 counts below equal 1356; Avadhi equals 1341. Mixed-generation completion
-- and the Kshetra -> mi_bhara calibration back-read remain disclosed gaps;
-- no constant integrity PASS, all-generation SUM or cyclic dependency is invented.
-- Century, 4.1, resonance and 2.0 lifecycle cutovers wait for their real gates.
SET LOCAL lock_timeout = '5s';
DO $k8$
DECLARE
  corrections constant jsonb := $k8_rows$[
  {
    "asset_id": "ka_gochara",
    "depends_on": [
      "bg_ephemeris",
      "bg_transit_rules",
      "ka_gochara_resonance",
      "ka_vedha_gochara",
      "ka_moorti_nirnaya",
      "ga_positions",
      "ga_dashas",
      "ga_yoga",
      "bg_gochara_arcs",
      "bg_ghatana",
      "bg_reference"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_gochara_resonance",
    "depends_on": [
      "bg_transit_rules",
      "ga_positions",
      "ga_dashas",
      "ga_yoga",
      "bg_ghatana",
      "bg_reference",
      "ka_yojaka"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_gochara_sweep",
    "depends_on": [
      "ka_gochara_resonance"
    ],
    "has_writer": false,
    "has_substeps": false
  },
  {
    "asset_id": "ka_gochara_v3_century_materialize",
    "depends_on": [
      "ka_gochara_resonance",
      "ka_vedha_gochara",
      "ka_moorti_nirnaya",
      "ka_kota_chakra",
      "ka_tithi_pravesha",
      "bg_sky_calendar",
      "bg_ghatana",
      "ga_positions",
      "bg_vedha_malefic_scale",
      "bg_reference",
      "ga_dashas",
      "bg_transit_rules"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_gochara_v4_41_candidate",
    "depends_on": [
      "ka_moorti_nirnaya",
      "ka_vedha_gochara",
      "bg_transit_rules",
      "bg_vedha_malefic_scale"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_gochara_v5",
    "depends_on": [
      "ga_positions",
      "ga_dashas",
      "bg_transit_rules"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_graha_sancara",
    "depends_on": [
      "bg_ephemeris"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_dasha_kala",
    "depends_on": [
      "ga_dashas"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_muhurta_seva",
    "depends_on": [
      "ka_graha_sancara"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_kalasutra",
    "depends_on": [
      "ka_yojaka",
      "ka_sangam",
      "bo_laksana",
      "ga_dashas"
    ],
    "has_writer": true,
    "has_substeps": false,
    "count_sql": "SELECT COUNT(*) FROM (\n  SELECT chart_id,'legacy'::text generation FROM public.kala_activation\n  UNION ALL SELECT chart_id,generation FROM public.kala_activation_candidate\n) model_rows WHERE chart_id = $1 AND generation=COALESCE((\n  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END\n  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c\n    ON c.chart_id=b.chart_id AND c.build_id=b.id\n  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1\n),'legacy')"
  },
  {
    "asset_id": "ka_sangam",
    "depends_on": [
      "ka_yojaka",
      "ka_dasha_kala",
      "ka_gochara",
      "ka_muhurta_seva",
      "bo_laksana",
      "ga_dashas",
      "ga_strength",
      "ga_positions",
      "ga_tajaka",
      "bg_transit_rules",
      "ka_vedha_gochara"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_vighnakara",
    "depends_on": [
      "ka_sangam",
      "ka_gochara",
      "ka_muhurta_seva",
      "ga_positions",
      "ga_dashas",
      "bg_dignity_reference",
      "ka_yojaka"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_avadhi",
    "depends_on": [
      "ga_positions",
      "ga_dashas",
      "ka_yojaka",
      "ka_dasha_kala"
    ],
    "has_writer": true,
    "has_substeps": false,
    "count_sql": "SELECT COUNT(*) FROM kala_avadhi WHERE chart_id=$1 AND generation=COALESCE((SELECT generation FROM kala_layer_head WHERE chart_id=$1),'legacy')"
  },
  {
    "asset_id": "ka_yojaka",
    "depends_on": [
      "bo_laksana",
      "bg_transit_rules",
      "ga_dashas",
      "bo_bimba",
      "bo_sangati",
      "bo_pratijna",
      "bg_ghatana",
      "ga_yoga",
      "ga_positions",
      "bg_yogas",
      "bg_text_index",
      "bo_karanajala"
    ],
    "has_writer": true,
    "has_substeps": true
  },
  {
    "asset_id": "ka_kala_darshana",
    "depends_on": [
      "ka_sangam",
      "ka_vighnakara",
      "ka_kalasutra",
      "ka_gochara_v3_century_materialize"
    ],
    "has_writer": true,
    "has_substeps": false,
    "count_sql": "SELECT COUNT(*) FROM (\n  SELECT chart_id,'legacy'::text generation FROM public.kala_darshana\n  UNION ALL SELECT chart_id,generation FROM public.kala_darshana_candidate\n) model_rows WHERE chart_id = $1 AND generation=COALESCE((\n  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END\n  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c\n    ON c.chart_id=b.chart_id AND c.build_id=b.id\n  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1\n),'legacy')"
  },
  {
    "asset_id": "ka_jivana_parva",
    "depends_on": [
      "ka_kala_darshana",
      "ka_dasha_kala",
      "ka_sangam",
      "ka_yojaka",
      "ga_dashas"
    ],
    "has_writer": true,
    "has_substeps": false,
    "count_sql": "SELECT COUNT(*) FROM (\n  SELECT chart_id,'legacy'::text generation FROM public.kala_jivana_parva\n  UNION ALL SELECT chart_id,generation FROM public.kala_jivana_parva_candidate\n) model_rows WHERE chart_id = $1 AND generation=COALESCE((\n  SELECT CASE WHEN c.conventions->>'fixture'='true' THEN c.generation ELSE 'legacy' END\n  FROM public.build_runs b LEFT JOIN public.kala_layer_candidate c\n    ON c.chart_id=b.chart_id AND c.build_id=b.id\n  WHERE b.chart_id=$1 ORDER BY b.created_at DESC,b.id DESC LIMIT 1\n),'legacy')"
  },
  {
    "asset_id": "ka_bhavishya_lekha",
    "depends_on": [
      "ka_kala_darshana",
      "ka_vighnakara",
      "ka_sangam",
      "bo_laksana"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_tulana",
    "depends_on": [
      "ka_sangam",
      "ka_vighnakara",
      "ka_kala_darshana"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_taranga",
    "depends_on": [
      "ka_avadhi",
      "bo_pratijna",
      "ka_sangam",
      "ga_dashas",
      "bg_ghatana"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_kota_chakra",
    "depends_on": [
      "ga_positions",
      "bg_ephemeris",
      "bg_kota_chakra_rings"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_sudarshana_varsha",
    "depends_on": [
      "ga_positions"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_tithi_pravesha",
    "depends_on": [
      "ga_positions"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_moorti_nirnaya",
    "depends_on": [
      "ga_positions",
      "bg_ephemeris",
      "bg_transit_rules"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_vedha_gochara",
    "depends_on": [
      "ga_positions",
      "bg_ephemeris",
      "bg_transit_rules",
      "bg_vedha_malefic_scale",
      "bg_phaladeepika_latta"
    ],
    "has_writer": true,
    "has_substeps": false
  },
  {
    "asset_id": "ka_kshetra",
    "depends_on": [
      "ka_dasha_kala",
      "ka_gochara_resonance",
      "ga_panchanga",
      "bo_pratijna",
      "bo_sangati",
      "bo_upaya",
      "bg_cohort",
      "bg_class_lifetime_counts",
      "bg_ghatana",
      "ka_gochara",
      "ka_gochara_v3_century_materialize",
      "bo_laksana",
      "bo_karanajala",
      "bo_bimba"
    ],
    "has_writer": true,
    "has_substeps": true
  }
]$k8_rows$::jsonb;
  correction jsonb;
  missing_id text;
BEGIN
  IF jsonb_array_length(corrections) <> 25 OR EXISTS (
    SELECT 1 FROM jsonb_array_elements(corrections) r
    WHERE r->>'asset_id' NOT LIKE 'ka\_%' ESCAPE '\'
  ) OR (SELECT count(DISTINCT r->>'asset_id') FROM jsonb_array_elements(corrections) r) <> 25 THEN
    RAISE EXCEPTION 'K8: malformed correction identities';
  END IF;
  IF EXISTS (
    SELECT 1 FROM jsonb_array_elements(corrections) r
    WHERE jsonb_typeof(r->'has_writer') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(r->'has_substeps') IS DISTINCT FROM 'boolean'
       OR (r ? 'count_sql' AND jsonb_typeof(r->'count_sql') IS DISTINCT FROM 'string')
       OR CASE WHEN jsonb_typeof(r->'depends_on')='array' THEN EXISTS (
            SELECT 1 FROM jsonb_array_elements(r->'depends_on') d
            WHERE jsonb_typeof(d) IS DISTINCT FROM 'string'
          ) ELSE true END
  ) THEN
    RAISE EXCEPTION 'K8: malformed correction shape';
  END IF;
  -- Lock all addressed rows before checking/applying. Missing identities refuse,
  -- rather than turning an incomplete catalog into a successful migration.
  PERFORM 1 FROM public.asset_registry a
    WHERE a.asset_id IN (SELECT r->>'asset_id' FROM jsonb_array_elements(corrections) r)
    ORDER BY a.asset_id FOR UPDATE;
  SELECT r->>'asset_id' INTO missing_id FROM jsonb_array_elements(corrections) r
    LEFT JOIN public.asset_registry a ON a.asset_id=r->>'asset_id'
    WHERE a.asset_id IS NULL ORDER BY r->>'asset_id' LIMIT 1;
  IF missing_id IS NOT NULL THEN
    RAISE EXCEPTION 'K8: missing asset identity %', missing_id;
  END IF;
  SELECT d.value INTO missing_id FROM jsonb_array_elements(corrections) r
    CROSS JOIN LATERAL jsonb_array_elements_text(r->'depends_on') d(value)
    LEFT JOIN public.asset_registry a ON a.asset_id=d.value
    WHERE a.asset_id IS NULL ORDER BY d.value LIMIT 1;
  IF missing_id IS NOT NULL THEN
    RAISE EXCEPTION 'K8: unknown dependency %', missing_id;
  END IF;
  FOR correction IN SELECT * FROM jsonb_array_elements(corrections) LOOP
    UPDATE public.asset_registry a SET
      depends_on = ARRAY(SELECT jsonb_array_elements_text(correction->'depends_on')),
      has_writer = (correction->>'has_writer')::boolean,
      has_substeps = (correction->>'has_substeps')::boolean,
      count_sql = CASE WHEN correction ? 'count_sql' THEN correction->>'count_sql' ELSE a.count_sql END
    WHERE a.asset_id=correction->>'asset_id'
      AND (a.depends_on IS DISTINCT FROM ARRAY(SELECT jsonb_array_elements_text(correction->'depends_on'))
        OR a.has_writer IS DISTINCT FROM (correction->>'has_writer')::boolean
        OR a.has_substeps IS DISTINCT FROM (correction->>'has_substeps')::boolean
        OR (correction ? 'count_sql' AND a.count_sql IS DISTINCT FROM correction->>'count_sql'));
  END LOOP;
  -- This sweep was already retired by 563. Retain its data; do not infer any
  -- new retirement or successor cutover from the presence of newer code.
  UPDATE public.asset_registry SET data_disposition='RETAINED_AS_CAPITAL'
    WHERE asset_id='ka_gochara_sweep' AND catalog_status='RETIRED'
      AND data_disposition IS DISTINCT FROM 'RETAINED_AS_CAPITAL';
END
$k8$;
