-- Migration 610: install the executable bg_texts integrity contract.
--
-- The accepted disposition preserves the 10,651 canonical chunks, repairs the
-- 15 classical_texts metadata rows in place, and pins every rebuild input to
-- the immutable GCS generations in bg_texts_source_manifest_v1.json. The
-- destructive full-rebuild path remains quarantined until staged per-text
-- replacement exists. A one-time immutable baseline records the exact ordered
-- key and semantic-content digests observed under these structural gates.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

CREATE TABLE IF NOT EXISTS nirmana_bg_texts_integrity_baselines (
  contract_revision text PRIMARY KEY,
  identity_sha256 text NOT NULL CHECK (identity_sha256 ~ '^[0-9a-f]{64}$'),
  content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
  row_count bigint NOT NULL CHECK (row_count = 10651),
  recorded_at timestamptz NOT NULL DEFAULT now()
);

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  legacy_count_sql constant text :=
    'SELECT' || E'\n'
    || '  (SELECT count(*) FROM classical_texts) +' || E'\n'
    || '  (SELECT count(*) FROM classical_text_chunks) AS count';
  canonical_count_sql constant text :=
    'SELECT count(*) FROM classical_text_chunks';
  legacy_inputs constant jsonb :=
    '{"corpus_texts":13,"embedding_model":"text-multilingual-embedding-002","actual_build_date":"2026-06-09"}'::jsonb;
  canonical_inputs constant jsonb :=
    '{"corpus_texts":15,"source_objects":20,"chunk_count":10651,"embedding_model":"text-multilingual-embedding-002","source_manifest":"platform/python-sidecar/brahmagyan/bg_texts_source_manifest_v1.json","source_manifest_sha256":"bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36","corpus_identity_sha256":"44b067b48544af32df4b2f4d8b13cc7c269aa029e236a0af3d2e8d7347d7d30e","corpus_content_sha256":"b81fb9c098847ecafc2072fd49d706f1a6bb811ab3fcc169d8753010ea6e17e2"}'::jsonb;
  legacy_explanation constant text :=
    '10,651 chunks across 13 classical texts (deterministic rebuild from GCS PDFs, pinned text-multilingual-embedding-002). Complete corpus; honest count from actual build.';
  canonical_explanation constant text :=
    '10,651 preserved chunks across 15 canonical texts. Twenty immutable GCS source-object generations are pinned by bg_texts_source_manifest_v1.json (SHA-256 bfcf536e16fb219d5f6faf1f01b6bd6a3a89830a96c997afb71d46eff32d1c36); metadata-only repair is the accepted disposition and destructive full rebuild is quarantined until staged per-text replacement exists.';
  canonical_partition constant text :=
    'canonical text_id set (15); chunk_id';
  -- Independently measured read-only from Cloud SQL on 2026-08-26, then
  -- replayed against a local production-shaped clone before registration.
  audited_identity_sha256 constant text :=
    '44b067b48544af32df4b2f4d8b13cc7c269aa029e236a0af3d2e8d7347d7d30e';
  audited_content_sha256 constant text :=
    'b81fb9c098847ecafc2072fd49d706f1a6bb811ab3fcc169d8753010ea6e17e2';
  canonical_translation_provenance constant text :=
    'machine_translation_supervised_2026-08; commissioned per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE CONFIRMATIONS; source edition per translator field';
  texts_check text;
  baseline_eligible boolean;
  computed_identity_sha256 text;
  computed_content_sha256 text;
  stored_identity_sha256 text;
  stored_content_sha256 text;
  stored_row_count bigint;
BEGIN
  texts_check := format($integrity$
WITH metadata_summary AS (
  SELECT
    count(*) AS total,
    count(DISTINCT text_id) AS distinct_ids,
    array_agg(text_id ORDER BY text_id COLLATE "C") AS text_ids,
    md5(COALESCE(string_agg(
      jsonb_build_array(
        text_id, title_en, title_sa, author, school, tradition, tier, license,
        license_cleared, total_chapters, total_verses, source_edition
      )::text,
      E'\n' ORDER BY text_id COLLATE "C"
    ), '')) AS metadata_md5
  FROM classical_texts
  WHERE text_id IN (
    'bhrigu_nandi_nadi','bphs','bphs_jaimini','brihat_jataka',
    'brihat_samhita','hora_sara','jataka_parijata','muhurta_chintamani',
    'nadi_navamsa_patel','phaladeepika','saravali','sarvartha_chintamani',
    'tajaka_neelakanthi','uttara_kalamrita','yavana_jataka'
  )
), chunk_facts AS (
  SELECT
    chunk.*,
    content_sha256 = encode(
      sha256(convert_to(text_id || '::' || content_en, 'UTF8')),
      'hex'
    ) AS hash_matches
  FROM classical_text_chunks AS chunk
), chunk_summary AS (
  SELECT
    count(*) AS total,
    count(DISTINCT chunk_id) AS distinct_ids,
    count(DISTINCT text_id) AS text_ids,
    count(*) FILTER (WHERE hash_matches IS TRUE) AS matching_hashes,
    count(*) FILTER (WHERE hash_matches IS NOT TRUE) AS mismatching_hashes,
    count(*) FILTER (
      WHERE hash_matches IS NOT TRUE
        AND text_id = 'muhurta_chintamani'
        AND translation_status = 'machine_translated_supervised'
        AND translation_provenance = %L
    ) AS accepted_supervised_mismatches,
    count(*) FILTER (
      WHERE hash_matches IS NOT TRUE AND low_confidence_flag IS TRUE
    ) AS mismatch_low_confidence,
    count(*) FILTER (
      WHERE hash_matches IS NOT TRUE AND low_confidence_flag IS FALSE
    ) AS mismatch_not_low_confidence
  FROM chunk_facts
), text_counts AS (
  SELECT COALESCE(jsonb_object_agg(text_id, row_count), '{}'::jsonb) AS value
  FROM (
    SELECT text_id, count(*) AS row_count
    FROM classical_text_chunks
    GROUP BY text_id
  ) AS counted
), exact_digests AS (
  SELECT
    encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(
        text_id, chunk_id, verse_ref, chapter, verse_start, verse_end
      )::text,
      E'\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
    ), ''), 'UTF8')), 'hex') AS identity_sha256,
    encode(sha256(convert_to(COALESCE(string_agg(
      jsonb_build_array(
        text_id, chunk_id, content_sa, content_en, source_citation, translator,
        tradition_school, content_sha256, md5(embedding::text),
        translation_status, translation_provenance, low_confidence_flag
      )::text,
      E'\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
    ), ''), 'UTF8')), 'hex') AS content_sha256
  FROM classical_text_chunks
), baseline AS (
  SELECT identity_sha256, content_sha256, row_count
  FROM nirmana_bg_texts_integrity_baselines
  WHERE contract_revision = 'bg-texts-integrity-v1'
)
SELECT (
  metadata_summary.total = 15
  AND metadata_summary.distinct_ids = 15
  AND metadata_summary.text_ids = ARRAY[
    'bhrigu_nandi_nadi','bphs','bphs_jaimini','brihat_jataka',
    'brihat_samhita','hora_sara','jataka_parijata','muhurta_chintamani',
    'nadi_navamsa_patel','phaladeepika','saravali','sarvartha_chintamani',
    'tajaka_neelakanthi','uttara_kalamrita','yavana_jataka'
  ]::text[]
  AND metadata_summary.metadata_md5 = '0d6618a39632bd560741782f84415210'
  AND chunk_summary.total = 10651
  AND chunk_summary.distinct_ids = 10651
  AND chunk_summary.text_ids = 15
  AND text_counts.value = '{
    "bhrigu_nandi_nadi":608,
    "bphs":1459,
    "bphs_jaimini":264,
    "brihat_jataka":607,
    "brihat_samhita":1171,
    "hora_sara":460,
    "jataka_parijata":704,
    "muhurta_chintamani":274,
    "nadi_navamsa_patel":1850,
    "phaladeepika":564,
    "saravali":471,
    "sarvartha_chintamani":342,
    "tajaka_neelakanthi":290,
    "uttara_kalamrita":289,
    "yavana_jataka":1298
  }'::jsonb
  AND chunk_summary.matching_hashes = 10563
  AND chunk_summary.mismatching_hashes = 88
  AND chunk_summary.accepted_supervised_mismatches = 88
  AND chunk_summary.mismatch_low_confidence = 78
  AND chunk_summary.mismatch_not_low_confidence = 10
  AND (SELECT count(*) = 1 FROM baseline)
  AND exact_digests.identity_sha256 = (SELECT identity_sha256 FROM baseline)
  AND exact_digests.content_sha256 = (SELECT content_sha256 FROM baseline)
  AND (SELECT row_count = 10651 FROM baseline)
  AND NOT EXISTS (
    SELECT 1
    FROM classical_text_chunks
    WHERE COALESCE(btrim(text_id), '') = ''
       OR COALESCE(btrim(chunk_id), '') = ''
       OR chunk_id <> text_id || '_pg' || lpad(chapter::text, 4, '0') || '_c'
            || CASE WHEN verse_start < 10
                    THEN '0' || verse_start::text
                    ELSE verse_start::text END
       OR COALESCE(btrim(verse_ref), '') = ''
       OR chapter IS NULL OR chapter < 1
       OR verse_start IS NULL OR verse_start < 1
       OR verse_end IS NULL OR verse_end < verse_start
       OR COALESCE(btrim(content_en), '') = ''
       OR COALESCE(btrim(source_citation), '') = ''
       OR COALESCE(btrim(translator), '') = ''
       OR COALESCE(btrim(tradition_school), '') = ''
       OR embedding IS NULL
       OR content_sha256 IS NULL
       OR content_sha256 !~ '^[0-9a-f]{64}$'
  )
) AS bg_texts_integrity
FROM metadata_summary, chunk_summary, text_counts, exact_digests
$integrity$, canonical_translation_provenance);

  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_texts'
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 610 requires bg_texts registry row';
  END IF;

  IF (
    registry_row.layer = 'brahmagyan'
    AND registry_row.sort_order = 3
    AND registry_row.scope = 'global'
    AND registry_row.asset_kind = 'data'
    AND registry_row.catalog_status = 'CURRENT'
    AND registry_row.is_active IS TRUE
    AND registry_row.has_writer IS TRUE
    AND registry_row.target_table = 'classical_text_chunks'
    AND registry_row.target_floor = 10651
    AND registry_row.depends_on = ARRAY[]::text[]
    AND (
      (
        registry_row.count_sql IN (legacy_count_sql, canonical_count_sql)
        AND registry_row.expected_volume_inputs = legacy_inputs
        AND registry_row.volume_explanation = legacy_explanation
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      )
      OR (
        registry_row.count_sql = canonical_count_sql
        AND registry_row.expected_volume_inputs = canonical_inputs
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition IS NULL
        AND registry_row.data_disposition IS NULL
        AND registry_row.integrity_check_sql IS NULL
      )
      OR (
        registry_row.count_sql = canonical_count_sql
        AND registry_row.expected_volume_inputs = canonical_inputs
        AND registry_row.volume_explanation = canonical_explanation
        AND registry_row.natural_key_partition = canonical_partition
        AND registry_row.data_disposition = 'RETAINED_AS_CAPITAL'
        AND registry_row.integrity_check_sql = texts_check
      )
    )
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 610 refuses unknown bg_texts registry contract';
  END IF;

  WITH chunk_facts AS (
    SELECT
      chunk.*,
      content_sha256 = encode(
        sha256(convert_to(text_id || '::' || content_en, 'UTF8')),
        'hex'
      ) AS hash_matches
    FROM classical_text_chunks AS chunk
  ), chunk_summary AS (
    SELECT
      count(*) AS total,
      count(DISTINCT chunk_id) AS distinct_ids,
      count(DISTINCT text_id) AS text_ids,
      count(*) FILTER (WHERE hash_matches IS TRUE) AS matching_hashes,
      count(*) FILTER (WHERE hash_matches IS NOT TRUE) AS mismatching_hashes,
      count(*) FILTER (
        WHERE hash_matches IS NOT TRUE
          AND text_id = 'muhurta_chintamani'
          AND translation_status = 'machine_translated_supervised'
          AND translation_provenance = canonical_translation_provenance
      ) AS accepted_supervised_mismatches,
      count(*) FILTER (
        WHERE hash_matches IS NOT TRUE AND low_confidence_flag IS TRUE
      ) AS mismatch_low_confidence,
      count(*) FILTER (
        WHERE hash_matches IS NOT TRUE AND low_confidence_flag IS FALSE
      ) AS mismatch_not_low_confidence
    FROM chunk_facts
  ), text_counts AS (
    SELECT COALESCE(jsonb_object_agg(text_id, row_count), '{}'::jsonb) AS value
    FROM (
      SELECT text_id, count(*) AS row_count
      FROM classical_text_chunks
      GROUP BY text_id
    ) AS counted
  ), exact_digests AS (
    SELECT
      encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(
          text_id, chunk_id, verse_ref, chapter, verse_start, verse_end
        )::text,
        E'\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
      ), ''), 'UTF8')), 'hex') AS identity_sha256,
      encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(
          text_id, chunk_id, content_sa, content_en, source_citation, translator,
          tradition_school, content_sha256, md5(embedding::text),
          translation_status, translation_provenance, low_confidence_flag
        )::text,
        E'\n' ORDER BY text_id COLLATE "C", chunk_id COLLATE "C"
      ), ''), 'UTF8')), 'hex') AS content_sha256
    FROM classical_text_chunks
  )
  SELECT (
    chunk_summary.total = 10651
    AND chunk_summary.distinct_ids = 10651
    AND chunk_summary.text_ids = 15
    AND text_counts.value = '{
      "bhrigu_nandi_nadi":608,
      "bphs":1459,
      "bphs_jaimini":264,
      "brihat_jataka":607,
      "brihat_samhita":1171,
      "hora_sara":460,
      "jataka_parijata":704,
      "muhurta_chintamani":274,
      "nadi_navamsa_patel":1850,
      "phaladeepika":564,
      "saravali":471,
      "sarvartha_chintamani":342,
      "tajaka_neelakanthi":290,
      "uttara_kalamrita":289,
      "yavana_jataka":1298
    }'::jsonb
    AND chunk_summary.matching_hashes = 10563
    AND chunk_summary.mismatching_hashes = 88
    AND chunk_summary.accepted_supervised_mismatches = 88
    AND chunk_summary.mismatch_low_confidence = 78
    AND chunk_summary.mismatch_not_low_confidence = 10
    AND NOT EXISTS (
      SELECT 1
      FROM classical_text_chunks
      WHERE COALESCE(btrim(text_id), '') = ''
         OR COALESCE(btrim(chunk_id), '') = ''
         OR chunk_id <> text_id || '_pg' || lpad(chapter::text, 4, '0') || '_c'
              || CASE WHEN verse_start < 10
                      THEN '0' || verse_start::text
                      ELSE verse_start::text END
         OR COALESCE(btrim(verse_ref), '') = ''
         OR chapter IS NULL OR chapter < 1
         OR verse_start IS NULL OR verse_start < 1
         OR verse_end IS NULL OR verse_end < verse_start
         OR COALESCE(btrim(content_en), '') = ''
         OR COALESCE(btrim(source_citation), '') = ''
         OR COALESCE(btrim(translator), '') = ''
         OR COALESCE(btrim(tradition_school), '') = ''
         OR embedding IS NULL
         OR content_sha256 IS NULL
         OR content_sha256 !~ '^[0-9a-f]{64}$'
    )
  ), exact_digests.identity_sha256, exact_digests.content_sha256
  INTO baseline_eligible, computed_identity_sha256, computed_content_sha256
  FROM chunk_summary, text_counts, exact_digests;

  IF baseline_eligible IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 610 refuses unverified bg_texts corpus baseline';
  END IF;

  IF computed_identity_sha256 <> audited_identity_sha256
     OR computed_content_sha256 <> audited_content_sha256 THEN
    RAISE EXCEPTION 'migration 610 refuses unaudited bg_texts corpus baseline';
  END IF;

  INSERT INTO nirmana_bg_texts_integrity_baselines
    (contract_revision, identity_sha256, content_sha256, row_count)
  VALUES
    ('bg-texts-integrity-v1', audited_identity_sha256, audited_content_sha256, 10651)
  ON CONFLICT (contract_revision) DO NOTHING;

  SELECT identity_sha256, content_sha256, row_count
  INTO stored_identity_sha256, stored_content_sha256, stored_row_count
  FROM nirmana_bg_texts_integrity_baselines
  WHERE contract_revision = 'bg-texts-integrity-v1'
  FOR UPDATE;

  IF NOT FOUND
     OR stored_identity_sha256 <> computed_identity_sha256
     OR stored_content_sha256 <> computed_content_sha256
     OR stored_row_count <> 10651 THEN
    RAISE EXCEPTION 'migration 610 refuses bg_texts baseline drift';
  END IF;

  UPDATE asset_registry
  SET count_sql = canonical_count_sql,
      expected_volume_inputs = canonical_inputs,
      volume_explanation = canonical_explanation,
      depends_on = ARRAY[]::text[],
      natural_key_partition = canonical_partition,
      data_disposition = 'RETAINED_AS_CAPITAL',
      integrity_check_sql = texts_check
  WHERE asset_id = 'bg_texts';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 610 expected to update bg_texts once, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM asset_registry
    WHERE asset_id = 'bg_texts'
      AND count_sql = canonical_count_sql
      AND target_floor = 10651
      AND expected_volume_inputs = canonical_inputs
      AND volume_explanation = canonical_explanation
      AND depends_on = ARRAY[]::text[]
      AND natural_key_partition = canonical_partition
      AND data_disposition = 'RETAINED_AS_CAPITAL'
      AND integrity_check_sql = texts_check
  ) THEN
    RAISE EXCEPTION 'migration 610 failed bg_texts postflight';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM nirmana_bg_texts_integrity_baselines
    WHERE contract_revision = 'bg-texts-integrity-v1'
      AND identity_sha256 = computed_identity_sha256
      AND content_sha256 = computed_content_sha256
      AND row_count = 10651
  ) THEN
    RAISE EXCEPTION 'migration 610 failed exact baseline postflight';
  END IF;
END $$;

-- Forward reversal: append a new migration after proving that no accepted
-- campaign receipt depends on this detector, then install its replacement.
