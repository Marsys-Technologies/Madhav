-- Migration 624: bind bg_ephemeris_engine to the real registry probe inputs.
-- The legacy registry JD decodes to 1984-01-02, while the probe substituted a
-- hard-coded 1984-02-05 JD. This corrects the immutable input contract, pins the
-- bundled Swiss file corpus, and removes the unverified DE441/range claim.
-- Transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_description constant text :=
    'Swiss Ephemeris (pyswisseph) with DE441 JPL file providing sidereal planetary positions from 9999 BCE to 9999 CE. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).';
  canonical_description constant text :=
    'Swiss Ephemeris (pyswisseph) with the pinned SHA-256-verified sepl_18/semo_18/seas_18 corpus for file-backed sidereal planetary positions. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).';
  legacy_probe constant jsonb := $json$
    {
      "probe_type": "ephemeris_engine",
      "forensic_jd": 2445701.948264,
      "expected_sun_approximate_sign": 10,
      "note": "JD = 1984-02-05 10:43 IST → UTC. Sun in Makara (sign 10) sidereal Lahiri."
    }
  $json$::jsonb;
  canonical_probe constant jsonb := $json$
    {
      "probe_type": "ephemeris_engine",
      "forensic_jd": 2445735.717361111,
      "expected_sun_sign": 10,
      "expected_mean_node_rahu_sign": 2,
      "ayanamsha": "lahiri",
      "node_mode": "mean",
      "allowed_ephemeris_backends": ["swiss_ephemeris_file"],
      "ephemeris_file_sha256": {
        "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
        "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
        "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2"
      },
      "note": "JD = 1984-02-05 10:43 IST = 05:13 UTC. Sun in Makara; mean-node Rahu in Vrishabha under sidereal Lahiri."
    }
  $json$::jsonb;
  canonical_apis constant jsonb := $json$
    [
      {
        "api": "swisseph.calc_ut",
        "description": "Planetary longitude at Julian Day (UT) — wraps pyswisseph swe.calc_ut"
      },
      {
        "api": "swisseph.houses_ex",
        "description": "House cusps + Lagna at JD with geographic coordinates"
      }
    ]
  $json$::jsonb;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_ephemeris_engine'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 14
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'service'
    AND registry_row.asset_type = 'service'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS FALSE
    AND registry_row.target_table IS NULL
    AND registry_row.count_sql IS NULL
    AND registry_row.target_floor IS NULL
    AND registry_row.depends_on = '{}'::text[]
    AND registry_row.natural_key_partition IS NULL
    AND registry_row.data_disposition IS NULL
    AND registry_row.integrity_check_sql IS NULL
    AND registry_row.rebuild_on_probe_fail IS FALSE
    AND registry_row.provides_apis = canonical_apis
    AND (
      (registry_row.english_description = legacy_description
       AND registry_row.health_probe = legacy_probe)
      OR (registry_row.english_description = canonical_description
          AND registry_row.health_probe = canonical_probe)
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 624 refuses unknown bg_ephemeris_engine registry contract';
  END IF;

  UPDATE asset_registry
  SET english_description = canonical_description,
      health_probe = canonical_probe
  WHERE asset_id = 'bg_ephemeris_engine';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 624 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_ephemeris_engine'
      AND english_description = canonical_description
      AND health_probe = canonical_probe
      AND provides_apis = canonical_apis
  ) THEN
    RAISE EXCEPTION 'migration 624 postflight registry mismatch';
  END IF;
END $$;
