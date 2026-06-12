-- Migration 224: Rename all 23 L2–L5 dotted asset_ids to underscore form
-- bodha.*→bo_*  kala.*→ka_*  phala.*→ph_*  mimamsa.*→mi_*
-- Also fixes all depends_on arrays referencing the old dotted ids.
-- Reversible DOWN block at bottom (as SQL comments).

-- ── Safety guards ─────────────────────────────────────────────────────────────

DO $$
DECLARE
  _count int;
  _lit_count int;
BEGIN
  -- Guard 1: all 23 old ids must exist
  SELECT count(*) INTO _count
  FROM asset_registry
  WHERE asset_id IN (
    'bodha.laksana','bodha.karanajala','bodha.bimba','bodha.samskara',
    'bodha.sangati','bodha.upaya','bodha.samvada','bodha.pramana_mapa',
    'kala.kalasutra','kala.sangam','kala.vighnakara','kala.transit_almanac',
    'phala.nimitta','phala.muhurta','phala.sodhana','phala.pratikara','phala.suddha_sodhana',
    'mimamsa.jivanaghatana','mimamsa.bhavisya','mimamsa.pramana',
    'mimamsa.gunanaka','mimamsa.pariksha','mimamsa.vistara'
  );
  IF _count <> 23 THEN
    RAISE EXCEPTION 'Migration 224 guard failed: expected 23 L2-L5 dotted rows, found %', _count;
  END IF;

  -- Guard 2: none may have built data in asset_throughput
  SELECT count(*) INTO _lit_count
  FROM asset_throughput
  WHERE asset_id IN (
    'bodha.laksana','bodha.karanajala','bodha.bimba','bodha.samskara',
    'bodha.sangati','bodha.upaya','bodha.samvada','bodha.pramana_mapa',
    'kala.kalasutra','kala.sangam','kala.vighnakara','kala.transit_almanac',
    'phala.nimitta','phala.muhurta','phala.sodhana','phala.pratikara','phala.suddha_sodhana',
    'mimamsa.jivanaghatana','mimamsa.bhavisya','mimamsa.pramana',
    'mimamsa.gunanaka','mimamsa.pariksha','mimamsa.vistara'
  );
  IF _lit_count > 0 THEN
    RAISE EXCEPTION 'Migration 224 guard failed: % asset_throughput rows exist for L2-L5 placeholder assets — these must be empty before renaming', _lit_count;
  END IF;
END $$;

-- ── Rename asset_ids ───────────────────────────────────────────────────────────

-- bodha → bo_*
UPDATE asset_registry SET asset_id = 'bo_laksana'        WHERE asset_id = 'bodha.laksana';
UPDATE asset_registry SET asset_id = 'bo_karanajala'     WHERE asset_id = 'bodha.karanajala';
UPDATE asset_registry SET asset_id = 'bo_bimba'          WHERE asset_id = 'bodha.bimba';
UPDATE asset_registry SET asset_id = 'bo_samskara'       WHERE asset_id = 'bodha.samskara';
UPDATE asset_registry SET asset_id = 'bo_sangati'        WHERE asset_id = 'bodha.sangati';
UPDATE asset_registry SET asset_id = 'bo_upaya'          WHERE asset_id = 'bodha.upaya';
UPDATE asset_registry SET asset_id = 'bo_samvada'        WHERE asset_id = 'bodha.samvada';
UPDATE asset_registry SET asset_id = 'bo_pramana_mapa'   WHERE asset_id = 'bodha.pramana_mapa';

-- kala → ka_*
UPDATE asset_registry SET asset_id = 'ka_kalasutra'        WHERE asset_id = 'kala.kalasutra';
UPDATE asset_registry SET asset_id = 'ka_sangam'           WHERE asset_id = 'kala.sangam';
UPDATE asset_registry SET asset_id = 'ka_vighnakara'       WHERE asset_id = 'kala.vighnakara';
UPDATE asset_registry SET asset_id = 'ka_transit_almanac'  WHERE asset_id = 'kala.transit_almanac';

-- phala → ph_*
UPDATE asset_registry SET asset_id = 'ph_nimitta'          WHERE asset_id = 'phala.nimitta';
UPDATE asset_registry SET asset_id = 'ph_muhurta'          WHERE asset_id = 'phala.muhurta';
UPDATE asset_registry SET asset_id = 'ph_sodhana'          WHERE asset_id = 'phala.sodhana';
UPDATE asset_registry SET asset_id = 'ph_pratikara'        WHERE asset_id = 'phala.pratikara';
UPDATE asset_registry SET asset_id = 'ph_suddha_sodhana'   WHERE asset_id = 'phala.suddha_sodhana';

-- mimamsa → mi_*
UPDATE asset_registry SET asset_id = 'mi_jivanaghatana'    WHERE asset_id = 'mimamsa.jivanaghatana';
UPDATE asset_registry SET asset_id = 'mi_bhavisya'         WHERE asset_id = 'mimamsa.bhavisya';
UPDATE asset_registry SET asset_id = 'mi_pramana'          WHERE asset_id = 'mimamsa.pramana';
UPDATE asset_registry SET asset_id = 'mi_gunanaka'         WHERE asset_id = 'mimamsa.gunanaka';
UPDATE asset_registry SET asset_id = 'mi_pariksha'         WHERE asset_id = 'mimamsa.pariksha';
UPDATE asset_registry SET asset_id = 'mi_vistara'          WHERE asset_id = 'mimamsa.vistara';

-- ── Fix depends_on arrays ──────────────────────────────────────────────────────

UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'bo_karanajala';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'bo_bimba';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'bo_samskara';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'bo_sangati';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana', 'bo_sangati']::text[]        WHERE asset_id = 'bo_upaya';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'bo_samvada';
UPDATE asset_registry SET depends_on = ARRAY['ka_kalasutra']::text[]                    WHERE asset_id = 'ka_sangam';
UPDATE asset_registry SET depends_on = ARRAY['ka_kalasutra', 'ga_sensitive']::text[]    WHERE asset_id = 'ka_vighnakara';
UPDATE asset_registry SET depends_on = ARRAY['bg_ephemeris', 'ka_kalasutra']::text[]    WHERE asset_id = 'ka_transit_almanac';
UPDATE asset_registry SET depends_on = ARRAY['ka_sangam']::text[]                       WHERE asset_id = 'ph_nimitta';
UPDATE asset_registry SET depends_on = ARRAY['ka_kalasutra', 'ga_panchanga']::text[]    WHERE asset_id = 'ph_muhurta';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana']::text[]                      WHERE asset_id = 'ph_sodhana';
UPDATE asset_registry SET depends_on = ARRAY['bo_upaya', 'ka_vighnakara']::text[]       WHERE asset_id = 'ph_pratikara';
UPDATE asset_registry SET depends_on = ARRAY['ph_sodhana']::text[]                      WHERE asset_id = 'ph_suddha_sodhana';
UPDATE asset_registry SET depends_on = ARRAY['bo_laksana', 'ka_kalasutra']::text[]      WHERE asset_id = 'mi_bhavisya';
UPDATE asset_registry SET depends_on = ARRAY['mi_bhavisya']::text[]                     WHERE asset_id = 'mi_pramana';
UPDATE asset_registry SET depends_on = ARRAY['mi_pramana']::text[]                      WHERE asset_id = 'mi_gunanaka';

-- ── DOWN (reverse — apply ONLY if rolling back this migration) ────────────────

-- UPDATE asset_registry SET asset_id = 'bodha.laksana'           WHERE asset_id = 'bo_laksana';
-- UPDATE asset_registry SET asset_id = 'bodha.karanajala'        WHERE asset_id = 'bo_karanajala';
-- UPDATE asset_registry SET asset_id = 'bodha.bimba'             WHERE asset_id = 'bo_bimba';
-- UPDATE asset_registry SET asset_id = 'bodha.samskara'          WHERE asset_id = 'bo_samskara';
-- UPDATE asset_registry SET asset_id = 'bodha.sangati'           WHERE asset_id = 'bo_sangati';
-- UPDATE asset_registry SET asset_id = 'bodha.upaya'             WHERE asset_id = 'bo_upaya';
-- UPDATE asset_registry SET asset_id = 'bodha.samvada'           WHERE asset_id = 'bo_samvada';
-- UPDATE asset_registry SET asset_id = 'bodha.pramana_mapa'      WHERE asset_id = 'bo_pramana_mapa';
-- UPDATE asset_registry SET asset_id = 'kala.kalasutra'          WHERE asset_id = 'ka_kalasutra';
-- UPDATE asset_registry SET asset_id = 'kala.sangam'             WHERE asset_id = 'ka_sangam';
-- UPDATE asset_registry SET asset_id = 'kala.vighnakara'         WHERE asset_id = 'ka_vighnakara';
-- UPDATE asset_registry SET asset_id = 'kala.transit_almanac'    WHERE asset_id = 'ka_transit_almanac';
-- UPDATE asset_registry SET asset_id = 'phala.nimitta'           WHERE asset_id = 'ph_nimitta';
-- UPDATE asset_registry SET asset_id = 'phala.muhurta'           WHERE asset_id = 'ph_muhurta';
-- UPDATE asset_registry SET asset_id = 'phala.sodhana'           WHERE asset_id = 'ph_sodhana';
-- UPDATE asset_registry SET asset_id = 'phala.pratikara'         WHERE asset_id = 'ph_pratikara';
-- UPDATE asset_registry SET asset_id = 'phala.suddha_sodhana'    WHERE asset_id = 'ph_suddha_sodhana';
-- UPDATE asset_registry SET asset_id = 'mimamsa.jivanaghatana'   WHERE asset_id = 'mi_jivanaghatana';
-- UPDATE asset_registry SET asset_id = 'mimamsa.bhavisya'        WHERE asset_id = 'mi_bhavisya';
-- UPDATE asset_registry SET asset_id = 'mimamsa.pramana'         WHERE asset_id = 'mi_pramana';
-- UPDATE asset_registry SET asset_id = 'mimamsa.gunanaka'        WHERE asset_id = 'mi_gunanaka';
-- UPDATE asset_registry SET asset_id = 'mimamsa.pariksha'        WHERE asset_id = 'mi_pariksha';
-- UPDATE asset_registry SET asset_id = 'mimamsa.vistara'         WHERE asset_id = 'mi_vistara';
-- Restore depends_on arrays (reverse each of the UPDATE SET depends_on statements above using the original values)
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'bo_karanajala';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'bo_bimba';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'bo_samskara';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'bo_sangati';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana', 'bodha.sangati']::text[]     WHERE asset_id = 'bo_upaya';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'bo_samvada';
-- UPDATE asset_registry SET depends_on = ARRAY['kala.kalasutra']::text[]                     WHERE asset_id = 'ka_sangam';
-- UPDATE asset_registry SET depends_on = ARRAY['kala.kalasutra', 'ga_sensitive']::text[]     WHERE asset_id = 'ka_vighnakara';
-- UPDATE asset_registry SET depends_on = ARRAY['bg_ephemeris', 'kala.kalasutra']::text[]     WHERE asset_id = 'ka_transit_almanac';
-- UPDATE asset_registry SET depends_on = ARRAY['kala.sangam']::text[]                        WHERE asset_id = 'ph_nimitta';
-- UPDATE asset_registry SET depends_on = ARRAY['kala.kalasutra', 'ga_panchanga']::text[]     WHERE asset_id = 'ph_muhurta';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana']::text[]                      WHERE asset_id = 'ph_sodhana';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.upaya', 'kala.vighnakara']::text[]     WHERE asset_id = 'ph_pratikara';
-- UPDATE asset_registry SET depends_on = ARRAY['phala.sodhana']::text[]                      WHERE asset_id = 'ph_suddha_sodhana';
-- UPDATE asset_registry SET depends_on = ARRAY['bodha.laksana', 'kala.kalasutra']::text[]    WHERE asset_id = 'mi_bhavisya';
-- UPDATE asset_registry SET depends_on = ARRAY['mimamsa.bhavisya']::text[]                   WHERE asset_id = 'mi_pramana';
-- UPDATE asset_registry SET depends_on = ARRAY['mimamsa.pramana']::text[]                    WHERE asset_id = 'mi_gunanaka';
