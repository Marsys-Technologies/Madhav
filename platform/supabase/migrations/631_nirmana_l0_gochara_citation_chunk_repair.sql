-- Migration 631: fail closed on the absent BPHS Ch.26 citation passage.
-- Created: 2026-08-27
--
-- Migration 630 exposes the fact that the two Graha Dṛṣṭi rows point to a
-- chunk which is not in the frozen 10,651-row bg_texts corpus. Do not invent
-- a 10,652nd chunk here: that would violate the immutable corpus contract,
-- source-manifest provenance, and accepted digest. Instead, retain the
-- citations as explicit corpus gaps until canonical corpus ingestion supplies
-- the source passage through its own governed revision.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

DO $$
DECLARE
  plain_row bg_gochara_citation_resolution%ROWTYPE;
  rasi_row bg_gochara_citation_resolution%ROWTYPE;
  changed_rows integer := 0;
  integrity_ok boolean;
  citation_check constant text := $check$
SELECT count(*) = 14
  AND count(DISTINCT constant_name) = 14
  AND count(*) FILTER (WHERE status='resolved') = 1
  AND count(*) FILTER (WHERE status='unresolved') = 13
  AND count(*) FILTER (WHERE status='unresolved'
    AND chunk_id NOT LIKE 'CORPUS_GAP:%') = 0
  AND NOT EXISTS (
    SELECT 1 FROM bg_gochara_citation_resolution citation
    WHERE citation.status='resolved' AND NOT EXISTS (
      SELECT 1 FROM classical_text_chunks chunk
      WHERE chunk.chunk_id=citation.chunk_id
    )
  )
  AND encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(citation_string,chunk_id,text_id,verse_ref,status,
      source_citation,constant_name,note)::text,
    E'\n' ORDER BY citation_string COLLATE "C",chunk_id COLLATE "C"
  ),''),'UTF8')),'hex') =
    'f87cfce86ed03e45c166977d4ded62a0a530b6ea8844c4e22f6d5340b9b961be'
FROM bg_gochara_citation_resolution
$check$;
BEGIN
  IF EXISTS (
    SELECT 1 FROM classical_text_chunks WHERE chunk_id='bphs_ch26_v001'
  ) THEN
    RAISE EXCEPTION
      'migration 631 refuses to alter a corpus that already contains bphs_ch26_v001';
  END IF;

  SELECT * INTO plain_row FROM bg_gochara_citation_resolution
  WHERE constant_name='GRAHA_DRISHTI_BPHS_26' FOR UPDATE;
  SELECT * INTO rasi_row FROM bg_gochara_citation_resolution
  WHERE constant_name='GRAHA_DRISHTI_RASI_BPHS_26' FOR UPDATE;

  IF NOT FOUND
     OR plain_row.constant_name IS NULL
     OR EXISTS (
       SELECT 1 FROM bg_gochara_citation_resolution
       WHERE constant_name IN ('GRAHA_DRISHTI_BPHS_26','GRAHA_DRISHTI_RASI_BPHS_26')
       GROUP BY constant_name HAVING count(*) <> 1
     ) THEN
    RAISE EXCEPTION 'migration 631 requires exactly the two known Graha Drishti citation rows';
  END IF;

  IF (
    plain_row.chunk_id='bphs_ch26_v001'
    AND plain_row.text_id='bphs'
    AND plain_row.verse_ref='CH26:V1-V4'
    AND plain_row.status='resolved'
    AND rasi_row.chunk_id='bphs_ch26_v001'
    AND rasi_row.text_id='bphs'
    AND rasi_row.verse_ref='CH26:V1-V4'
    AND rasi_row.status='resolved'
  ) THEN
    UPDATE bg_gochara_citation_resolution
    SET chunk_id = CASE constant_name
          WHEN 'GRAHA_DRISHTI_BPHS_26' THEN 'CORPUS_GAP:bphs_ch26_graha_drishti'
          WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN 'CORPUS_GAP:bphs_ch26_graha_drishti_rasi'
        END,
        verse_ref = 'CH26 exact graha-drishti passage not ingested',
        status = 'unresolved',
        source_citation = CASE constant_name
          WHEN 'GRAHA_DRISHTI_BPHS_26' THEN
            'BPHS Ch.26 Graha Drishti citation; the exact passage is absent from the current immutable classical_text_chunks corpus.'
          WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN
            'BPHS Ch.26 Graha Drishti rasi-rendering citation; the exact passage is absent from the current immutable classical_text_chunks corpus.'
        END,
        note = CASE constant_name
          WHEN 'GRAHA_DRISHTI_BPHS_26' THEN
            'The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this citation remains an explicit corpus gap until canonical ingestion restores the exact passage.'
          WHEN 'GRAHA_DRISHTI_RASI_BPHS_26' THEN
            'The prior bphs_ch26_v001 mapping is absent from the immutable corpus; this rasi-rendering citation remains an explicit corpus gap until canonical ingestion restores the exact passage.'
        END
    WHERE constant_name IN ('GRAHA_DRISHTI_BPHS_26','GRAHA_DRISHTI_RASI_BPHS_26');
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 2 THEN
      RAISE EXCEPTION 'migration 631 changed % citation rows, expected 2', changed_rows;
    END IF;
  ELSIF NOT (
    plain_row.chunk_id='CORPUS_GAP:bphs_ch26_graha_drishti'
    AND plain_row.text_id='bphs'
    AND plain_row.verse_ref='CH26 exact graha-drishti passage not ingested'
    AND plain_row.status='unresolved'
    AND rasi_row.chunk_id='CORPUS_GAP:bphs_ch26_graha_drishti_rasi'
    AND rasi_row.text_id='bphs'
    AND rasi_row.verse_ref='CH26 exact graha-drishti passage not ingested'
    AND rasi_row.status='unresolved'
  ) THEN
    RAISE EXCEPTION 'migration 631 refuses unknown Graha Drishti citation state';
  END IF;

  UPDATE asset_registry
  SET volume_explanation =
        '14 governed citation mappings: 1 exact resolved chunk link and 13 honest corpus gaps. Same-chapter proximity is never treated as source evidence.',
      integrity_check_sql = citation_check
  WHERE asset_id='bg_gochara_citation_resolution'
    AND target_floor=14
    AND natural_key_partition='bg_gochara_citation_resolution.(citation_string,chunk_id)'
    AND data_disposition='RETAINED_AS_CAPITAL'
    AND (
      encode(sha256(convert_to(integrity_check_sql,'UTF8')),'hex')=
        '6ea8c824cd9e51b258d58eea7814491372027d7356c207f62d18eb76477f5b3b'
      OR (
        integrity_check_sql=citation_check
        AND volume_explanation=
          '14 governed citation mappings: 1 exact resolved chunk link and 13 honest corpus gaps. Same-chapter proximity is never treated as source evidence.'
      )
    );
  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 631 refuses unknown gochara citation registry contract';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id='bg_gochara_citation_resolution'
      AND integrity_check_sql=citation_check
      AND volume_explanation=
        '14 governed citation mappings: 1 exact resolved chunk link and 13 honest corpus gaps. Same-chapter proximity is never treated as source evidence.'
  ) THEN
    RAISE EXCEPTION 'migration 631 citation-integrity contract postflight failed';
  END IF;

  EXECUTE citation_check INTO integrity_ok;
  IF integrity_ok IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 631 citation-integrity detector postflight failed';
  END IF;
END $$;
