-- Migration 630: Nirmana L0 wave-1 correctness and provenance contracts.
-- Created: 2026-08-26
--
-- Transaction ownership belongs to platform/scripts/migrate.ts. This migration
-- does not rebuild any asset; exact detectors remain false until the governed
-- wave-1 writers replay from their frozen source snapshot.

DO $$
DECLARE
  relation_oid oid := to_regclass('brahma_yoga_source_chunks');
  exact_schema boolean;
BEGIN
  IF relation_oid IS NULL THEN
    RETURN;
  END IF;

  SELECT
    (SELECT count(*) = 2
       AND count(*) FILTER (
         WHERE attname='canonical_id' AND format_type(atttypid,atttypmod)='text'
           AND attnotnull
       ) = 1
       AND count(*) FILTER (
         WHERE attname='source_chunk_id' AND format_type(atttypid,atttypmod)='uuid'
           AND attnotnull
       ) = 1
     FROM pg_attribute
     WHERE attrelid=relation_oid AND attnum>0 AND NOT attisdropped)
    AND
    (SELECT count(*) = 3
       AND count(*) FILTER (
         WHERE contype='p' AND convalidated
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id','source_chunk_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE contype='f' AND convalidated
           AND confrelid='brahma_yoga_catalog'::regclass AND confdeltype='c'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id']::text[]
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(confkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=confrelid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE contype='f' AND convalidated
           AND confrelid='classical_text_chunks'::regclass AND confdeltype='r'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['source_chunk_id']::text[]
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(confkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=confrelid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['id']::text[]
       ) = 1
     FROM pg_constraint WHERE conrelid=relation_oid)
    AND
    (SELECT count(*) = 2
       AND count(*) FILTER (
         WHERE indisprimary AND indisunique AND indisvalid AND indisready
           AND indpred IS NULL AND indexprs IS NULL
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(indkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             WHERE key.attnum>0 ORDER BY key.position
           ) = ARRAY['canonical_id','source_chunk_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE indexrelid=to_regclass('idx_brahma_yoga_source_chunks_chunk')
           AND NOT indisprimary AND NOT indisunique AND indisvalid AND indisready
           AND indpred IS NULL AND indexprs IS NULL
           AND (SELECT amname FROM pg_am
                WHERE oid=(SELECT relam FROM pg_class WHERE oid=indexrelid))='btree'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(indkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             WHERE key.attnum>0 ORDER BY key.position
           ) = ARRAY['source_chunk_id']::text[]
       ) = 1
     FROM pg_index WHERE indrelid=relation_oid)
  INTO exact_schema;

  IF exact_schema IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 630 refuses pre-existing noncanonical brahma_yoga_source_chunks';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS brahma_yoga_source_chunks (
  canonical_id TEXT NOT NULL
    REFERENCES brahma_yoga_catalog(canonical_id) ON DELETE CASCADE,
  source_chunk_id UUID NOT NULL
    REFERENCES classical_text_chunks(id) ON DELETE RESTRICT,
  PRIMARY KEY (canonical_id, source_chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_brahma_yoga_source_chunks_chunk
  ON brahma_yoga_source_chunks(source_chunk_id);

DO $$
DECLARE
  relation_oid oid := 'brahma_yoga_source_chunks'::regclass;
  exact_schema boolean;
BEGIN
  SELECT
    (SELECT count(*) = 2
       AND count(*) FILTER (
         WHERE attname='canonical_id' AND format_type(atttypid,atttypmod)='text'
           AND attnotnull
       ) = 1
       AND count(*) FILTER (
         WHERE attname='source_chunk_id' AND format_type(atttypid,atttypmod)='uuid'
           AND attnotnull
       ) = 1
     FROM pg_attribute
     WHERE attrelid=relation_oid AND attnum>0 AND NOT attisdropped)
    AND
    (SELECT count(*) = 3
       AND count(*) FILTER (
         WHERE contype='p' AND convalidated
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id','source_chunk_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE contype='f' AND convalidated
           AND confrelid='brahma_yoga_catalog'::regclass AND confdeltype='c'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id']::text[]
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(confkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=confrelid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['canonical_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE contype='f' AND convalidated
           AND confrelid='classical_text_chunks'::regclass AND confdeltype='r'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(conkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['source_chunk_id']::text[]
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(confkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=confrelid AND attribute.attnum=key.attnum
             ORDER BY key.position
           ) = ARRAY['id']::text[]
       ) = 1
     FROM pg_constraint WHERE conrelid=relation_oid)
    AND
    (SELECT count(*) = 2
       AND count(*) FILTER (
         WHERE indisprimary AND indisunique AND indisvalid AND indisready
           AND indpred IS NULL AND indexprs IS NULL
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(indkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             WHERE key.attnum>0 ORDER BY key.position
           ) = ARRAY['canonical_id','source_chunk_id']::text[]
       ) = 1
       AND count(*) FILTER (
         WHERE indexrelid='idx_brahma_yoga_source_chunks_chunk'::regclass
           AND NOT indisprimary AND NOT indisunique AND indisvalid AND indisready
           AND indpred IS NULL AND indexprs IS NULL
           AND (SELECT amname FROM pg_am
                WHERE oid=(SELECT relam FROM pg_class WHERE oid=indexrelid))='btree'
           AND ARRAY(
             SELECT attribute.attname::text
             FROM unnest(indkey) WITH ORDINALITY key(attnum,position)
             JOIN pg_attribute attribute
               ON attribute.attrelid=relation_oid AND attribute.attnum=key.attnum
             WHERE key.attnum>0 ORDER BY key.position
           ) = ARRAY['source_chunk_id']::text[]
       ) = 1
     FROM pg_index WHERE indrelid=relation_oid)
  INTO exact_schema;

  IF exact_schema IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 630 brahma_yoga_source_chunks schema postflight failed';
  END IF;
END $$;

COMMENT ON TABLE brahma_yoga_source_chunks IS
  'Typed provenance links owned by bg_yogas. Legacy BIGINT[] source_chunk_ids '
  'cannot represent classical_text_chunks.id UUID values and remains empty; '
  'this normalized relation is the authoritative exact source link.';

-- The historical VAKRA row was only the closest same-chapter chunk and its
-- content is karaka doctrine, not vakra/cheshta-bala. Preserve the citation as
-- an explicit corpus gap until the exact passage is ingested.
DO $$
DECLARE
  vakra_row bg_gochara_citation_resolution%ROWTYPE;
  changed_rows integer := 0;
BEGIN
  SELECT * INTO vakra_row
  FROM bg_gochara_citation_resolution
  WHERE constant_name = 'VAKRA_RETROGRADE_BPHS_27' FOR UPDATE;

  IF NOT FOUND OR EXISTS (
    SELECT 1 FROM bg_gochara_citation_resolution
    WHERE constant_name='VAKRA_RETROGRADE_BPHS_27'
    OFFSET 1
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown VAKRA citation mapping';
  END IF;

  IF (
    vakra_row.citation_string='BPHS Ch.27 — Vakra (retrogression; cheshta bala)'
    AND vakra_row.chunk_id='bphs_ch27_v001'
    AND vakra_row.text_id='bphs'
    AND vakra_row.verse_ref='CH27:V1-V3'
    AND vakra_row.status='resolved'
    AND vakra_row.source_citation=
      'BPHS Ch.27 v1-3 (chunk bphs_ch27_v001) — the cheshta bala / vakra (retrograde) doctrine that VAKRA_RETROGRADE_BPHS_27 cites is in BPHS Ch.27.'
    AND vakra_row.note=
      'citations.py constant VAKRA_RETROGRADE_BPHS_27. Chunk bphs_ch27_v001 confirmed in l0_texts.py SEED_CHUNKS (chapter 27, verse_start 1). Honest disclosure: the SEED_CHUNKS content for this chunk covers karakas (the chapter''s primary topic); the cheshta-bala/vakra doctrine is in the same chapter per l0_reference.py citation ''BPHS Ch.27''.'
    AND vakra_row.created_at IS NOT NULL
  ) THEN
    UPDATE bg_gochara_citation_resolution
    SET chunk_id='CORPUS_GAP:bphs_ch27_vakra',
        text_id='bphs',
        verse_ref='CH27 exact vakra passage not ingested',
        status='unresolved',
        source_citation=
          'BPHS Ch.27 vakra/cheshta-bala citation; the exact passage is absent from the current classical_text_chunks corpus.',
        note=
          'The prior bphs_ch27_v001 mapping was same-chapter proximity only; that chunk contains karaka doctrine and cannot ground this claim.'
    WHERE constant_name='VAKRA_RETROGRADE_BPHS_27';
    GET DIAGNOSTICS changed_rows = ROW_COUNT;
    IF changed_rows <> 1 THEN
      RAISE EXCEPTION 'migration 630 VAKRA transition updated % rows',changed_rows;
    END IF;
  ELSIF NOT (
    vakra_row.citation_string='BPHS Ch.27 — Vakra (retrogression; cheshta bala)'
    AND vakra_row.chunk_id='CORPUS_GAP:bphs_ch27_vakra'
    AND vakra_row.text_id='bphs'
    AND vakra_row.verse_ref='CH27 exact vakra passage not ingested'
    AND vakra_row.status='unresolved'
    AND vakra_row.source_citation=
      'BPHS Ch.27 vakra/cheshta-bala citation; the exact passage is absent from the current classical_text_chunks corpus.'
    AND vakra_row.note=
      'The prior bphs_ch27_v001 mapping was same-chapter proximity only; that chunk contains karaka doctrine and cannot ground this claim.'
    AND vakra_row.created_at IS NOT NULL
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown VAKRA citation mapping';
  END IF;
END $$;

-- Install exact structural detectors. Semantic identity remains additionally
-- bound by each asset's current output-digest specification and receipt.
DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  metadata_sha text;
  integrity_sha text;
  yoga_count_sql constant text := $count$SELECT
  (SELECT count(*) FROM brahma_yoga_catalog) +
  (SELECT count(*) FROM brahma_ontology WHERE entity_class = 'yoga') +
  (SELECT count(*) FROM reference_yogas) +
  (SELECT count(*) FROM brahma_yoga_source_chunks) AS count$count$;
  yoga_explanation constant text :=
    '784 owned rows = 233 deterministic yoga definitions × 3 reconciled '
    'projections plus 85 typed UUID source-chunk links for the corpus-extracted definitions.';
  yoga_partition constant text :=
    'brahma_yoga_catalog.canonical_id; brahma_ontology.(entity_class=yoga,canonical_id); '
    'reference_yogas.canonical_id; brahma_yoga_source_chunks.(canonical_id,source_chunk_id)';
  yoga_check constant text := $check$
SELECT
  (SELECT count(*) = 233 FROM brahma_yoga_catalog)
  AND (SELECT count(*) = 233 FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT count(*) = 233 FROM reference_yogas)
  AND (SELECT count(*) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(DISTINCT canonical_id) = 85 FROM brahma_yoga_source_chunks)
  AND (SELECT count(*) FILTER (WHERE cardinality(source_chunk_ids)=0) = 233
       FROM brahma_yoga_catalog)
  AND NOT EXISTS (
    SELECT 1 FROM brahma_yoga_catalog AS catalog
    FULL JOIN brahma_ontology AS ontology
      ON ontology.entity_class='yoga' AND ontology.canonical_id=catalog.canonical_id
    FULL JOIN reference_yogas AS reference
      ON reference.canonical_id=COALESCE(catalog.canonical_id,ontology.canonical_id)
    WHERE catalog.canonical_id IS NULL OR ontology.canonical_id IS NULL
       OR reference.canonical_id IS NULL
       OR ontology.canonical_name_en IS DISTINCT FROM catalog.name_en
       OR ontology.canonical_name_sa IS DISTINCT FROM catalog.name_sa
       OR reference.name_en IS DISTINCT FROM catalog.name_en
       OR reference.category IS DISTINCT FROM catalog.category
  )
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_sa,name_en,category,formation_rule_jsonb,
      formation_text,significations_jsonb,significations_text,
      cancellation_conditions,classical_citations,source_chunk_ids,school,rare,
      computed_strength_formula,bhanga_rules_jsonb,partial_formation_threshold,
      strength_formula_ref,result_class)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '4d4cd60f7cffe728f2d01c3146f9bf54279e5c747973ab60b2e69b7921023fa8'
   FROM brahma_yoga_catalog)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(entity_class,canonical_id,canonical_name_en,
      canonical_name_sa,synonyms,description,source_citation)::text,
    E'\n' ORDER BY entity_class COLLATE "C",canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '7af1d138c492bd16bbca93b06faab6b3ff781d87aa91f8573fce6378f968fdab'
   FROM brahma_ontology WHERE entity_class='yoga')
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(canonical_id,name_en,category)::text,
    E'\n' ORDER BY canonical_id COLLATE "C"),''),'UTF8')),'hex') =
    '1c79af1127b8e624e12c95afecf09e73f23546fe87272f5dff8146ed30d6f564'
   FROM reference_yogas)
$check$;
  kp_check constant text := $check$
SELECT count(*) = 249
  AND count(DISTINCT table_version) = 1
  AND min(table_version) = 'kp_sublord_division_v01'
  AND min(division_index) = 1 AND max(division_index) = 249
  AND abs(sum(end_longitude_deg-start_longitude_deg)-360.0) < 0.00000001
  AND count(*) FILTER (WHERE btrim(source_citation)='') = 0
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT division_index,row_number() OVER (ORDER BY division_index) AS expected
      FROM bg_kp_sublord_division
    ) ordered WHERE division_index <> expected
  )
FROM bg_kp_sublord_division
$check$;
  arcs_check constant text := $check$
SELECT count(*) = 34553
  AND count(DISTINCT substrate_version) = 1
  AND min(substrate_version) = 'arcs_v01'
  AND count(DISTINCT body) = 9
  AND count(DISTINCT (body,arc_fingerprint)) = 9
  AND count(*) FILTER (WHERE engine_version <> 'w2g_arcs_v01'
    OR ayanamsha_id <> 'tropical') = 0
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT body,count(*) AS n,min(arc_index) AS lo,max(arc_index) AS hi,
             count(DISTINCT arc_fingerprint) AS fingerprints
      FROM bg_gochara_arcs GROUP BY body
    ) actual
    FULL JOIN (VALUES
      ('Saturn',503),('Jupiter',494),('Rahu',13544),('Ketu',13553),
      ('Mars',376),('Sun',252),('Mercury',1894),('Venus',580),('Moon',3357)
    ) expected(body,n)
      ON expected.body=actual.body
    WHERE actual.body IS NULL OR expected.body IS NULL OR actual.n<>expected.n
       OR actual.lo<>0 OR actual.hi<>actual.n-1 OR actual.fingerprints<>1
  )
FROM bg_gochara_arcs
$check$;
  vidhi_count_sql constant text := $count$SELECT
  (SELECT count(*) FROM vidhi_intent_floors) +
  (SELECT count(*) FROM vidhi_floor_items) AS count$count$;
  vidhi_check constant text := $check$
SELECT
  (SELECT count(*) = 14 FROM vidhi_intent_floors)
  AND (SELECT count(*) = 409 FROM vidhi_floor_items)
  AND NOT EXISTS (
    SELECT 1 FROM (
      SELECT intent,count(*) AS n,min(item_order) AS lo,max(item_order) AS hi,
             count(DISTINCT item_order) AS distinct_orders
      FROM vidhi_floor_items GROUP BY intent
    ) grouped
    WHERE lo<>1 OR hi<>n OR distinct_orders<>n
  )
  AND NOT EXISTS (
    SELECT 1 FROM vidhi_floor_items item
    LEFT JOIN vidhi_intent_floors floor USING(intent)
    LEFT JOIN vidhi_primitives primitive USING(primitive_id)
    WHERE floor.intent IS NULL OR primitive.primitive_id IS NULL
  )
$check$;
  citation_check constant text := $check$
SELECT count(*) = 14
  AND count(DISTINCT constant_name) = 14
  AND count(*) FILTER (WHERE status='resolved') = 3
  AND count(*) FILTER (WHERE status='unresolved') = 11
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
    '4e65ee68012bd20dd2b328a5c31da24fbd1670a6129a0b8aab0eaf5c539a7721'
FROM bg_gochara_citation_resolution
$check$;
BEGIN
  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_text_index' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_text_index registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  integrity_sha := encode(sha256(convert_to(
    COALESCE(registry_row.integrity_check_sql,''),'UTF8')),'hex');
  IF NOT (
    metadata_sha IN (
      '30dc390e0f00f34958df69d63cd8d9c0192bc3dd023d508cea228ce40150ac94',
      'b85b9e75f8a0a55bdeb5d3159ebb62d1efdca505f51af61b1e6eb2087e2c43f2'
    )
    AND integrity_sha='93446a84cceda0809a1e58c2d703329a26f9141242d17dc5a3046ab1184a1ed0'
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_text_index registry contract';
  END IF;
  UPDATE asset_registry SET depends_on=ARRAY['bg_texts','bg_reference']::text[]
  WHERE asset_id='bg_text_index';

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_rules registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  integrity_sha := encode(sha256(convert_to(
    COALESCE(registry_row.integrity_check_sql,''),'UTF8')),'hex');
  IF NOT (
    metadata_sha IN (
      '449fb76fb56a4301a53dfc896baef9a3d5ecf2b434a127aceb3fedcf80f1fc8a',
      '638a4b891bc41c30f87c40c11f2126d7f8e39e2d3d8c4ced8b1afa470a416dd0'
    )
    AND integrity_sha='bbc85c5f1ee64688e2fd932c5ff6563ae829cf7e9e03c43e42609d85b916de6f'
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_rules registry contract';
  END IF;
  UPDATE asset_registry
  SET depends_on=ARRAY['bg_texts','bg_yogas','bg_dasha_systems']::text[]
  WHERE asset_id='bg_rules';

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id='bg_yogas' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_yogas registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  IF NOT (
    (metadata_sha='6f6d27090e3cd6ec4f21a19c7fe7f22c72124c63b2b2ee351234c027fe524f5e'
      AND encode(sha256(convert_to(
        COALESCE(registry_row.integrity_check_sql,''),'UTF8')),'hex')=
        '49c26b8c2514a2bcc47fcdf882732bdbaf4a017e11bfbac1da62d49789834554')
    OR
    (metadata_sha='f4adc4d444334af48a831ed9dbdceec3adab5ba27013c6c53db3a2f61771410a'
      AND registry_row.integrity_check_sql=yoga_check)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_yogas registry contract';
  END IF;
  UPDATE asset_registry SET target_floor=784,count_sql=yoga_count_sql,
    volume_explanation=yoga_explanation,natural_key_partition=yoga_partition,
    depends_on=ARRAY['bg_texts','bg_ontology']::text[],
    integrity_check_sql=yoga_check WHERE asset_id='bg_yogas';

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_kp_sublord_division' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_kp_sublord_division registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  IF NOT (
    (metadata_sha='942be622a1dfb96b2128554374492b3da3fd376f918dc928e9ae06c62343d82d'
      AND registry_row.integrity_check_sql IS NULL)
    OR
    (metadata_sha='4e4524584a3860747707aef35a9ee5bc02693fd1512211ebcbd47c6ccb2fef50'
      AND registry_row.integrity_check_sql=kp_check)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_kp_sublord_division registry contract';
  END IF;
  UPDATE asset_registry SET natural_key_partition='bg_kp_sublord_division.(table_version,division_index)',
    integrity_check_sql=kp_check WHERE asset_id='bg_kp_sublord_division';

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id='bg_gochara_arcs' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_gochara_arcs registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  IF NOT (
    (metadata_sha='f42756b2a497cf804628d94fa1a96b02846917e5ac083efb70081ff157ada5c6'
      AND registry_row.integrity_check_sql IS NULL)
    OR
    (metadata_sha='6bc7ed2f54cd008566c98987edcdf337f57dcccd443ee88a8367b10906dc07fc'
      AND registry_row.integrity_check_sql=arcs_check)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_gochara_arcs registry contract';
  END IF;
  UPDATE asset_registry SET natural_key_partition='bg_gochara_arcs.(substrate_version,body,arc_index)',
    integrity_check_sql=arcs_check WHERE asset_id='bg_gochara_arcs';

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id='bg_vidhi_floors' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_vidhi_floors registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  IF NOT (
    (metadata_sha='667012f44b7a3f32cb15b341c428ae603d196f037324b2d4df7ea7271bba8c40'
      AND registry_row.integrity_check_sql IS NULL)
    OR
    (metadata_sha='78ca618f910577c6a5da76cbf2efb8bcabf3841369c2caab1623e084a4a00706'
      AND registry_row.integrity_check_sql=vidhi_check)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_vidhi_floors registry contract';
  END IF;
  UPDATE asset_registry SET target_floor=423,count_sql=vidhi_count_sql,
    volume_explanation='423 owned rows = 14 current intent floors + 409 ordered floor items from the canonical Vidhi registry.',
    natural_key_partition='vidhi_intent_floors.intent; vidhi_floor_items.(intent,item_order)',
    integrity_check_sql=vidhi_check WHERE asset_id='bg_vidhi_floors';

  SELECT * INTO registry_row FROM asset_registry
  WHERE asset_id='bg_gochara_citation_resolution' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 630 requires bg_gochara_citation_resolution registry row';
  END IF;
  metadata_sha := encode(sha256(convert_to(jsonb_build_array(
    registry_row.layer,registry_row.sort_order,registry_row.scope,
    registry_row.asset_kind,registry_row.catalog_status,registry_row.is_active,
    registry_row.has_writer,registry_row.target_table,registry_row.count_sql,
    registry_row.target_floor,registry_row.depends_on,
    registry_row.english_description,registry_row.volume_explanation,
    registry_row.natural_key_partition,registry_row.data_disposition
  )::text,'UTF8')),'hex');
  IF NOT (
    (metadata_sha='a36cf55e4e879f31b7874c7367975b589b35cc74d8b63afac152f82e08fd2ad9'
      AND registry_row.integrity_check_sql IS NULL)
    OR
    (metadata_sha='9189699f8f72f40c9bff35e030be10beea517fa3dbe86f51ae08ab24ad1f7139'
      AND registry_row.integrity_check_sql=citation_check)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown bg_gochara_citation_resolution registry contract';
  END IF;
  UPDATE asset_registry SET target_floor=14,
    volume_explanation='14 governed citation mappings: 3 exact resolved chunk links and 11 honest corpus gaps. Same-chapter proximity is never treated as source evidence.',
    natural_key_partition='bg_gochara_citation_resolution.(citation_string,chunk_id)',
    data_disposition='RETAINED_AS_CAPITAL',integrity_check_sql=citation_check
  WHERE asset_id='bg_gochara_citation_resolution';

  IF EXISTS (
    SELECT 1
    FROM (VALUES
      ('bg_text_index','b85b9e75f8a0a55bdeb5d3159ebb62d1efdca505f51af61b1e6eb2087e2c43f2',
       '93446a84cceda0809a1e58c2d703329a26f9141242d17dc5a3046ab1184a1ed0'),
      ('bg_rules','638a4b891bc41c30f87c40c11f2126d7f8e39e2d3d8c4ced8b1afa470a416dd0',
       'bbc85c5f1ee64688e2fd932c5ff6563ae829cf7e9e03c43e42609d85b916de6f'),
      ('bg_yogas','f4adc4d444334af48a831ed9dbdceec3adab5ba27013c6c53db3a2f61771410a',
       encode(sha256(convert_to(yoga_check,'UTF8')),'hex')),
      ('bg_kp_sublord_division',
       '4e4524584a3860747707aef35a9ee5bc02693fd1512211ebcbd47c6ccb2fef50',
       encode(sha256(convert_to(kp_check,'UTF8')),'hex')),
      ('bg_gochara_arcs',
       '6bc7ed2f54cd008566c98987edcdf337f57dcccd443ee88a8367b10906dc07fc',
       encode(sha256(convert_to(arcs_check,'UTF8')),'hex')),
      ('bg_vidhi_floors',
       '78ca618f910577c6a5da76cbf2efb8bcabf3841369c2caab1623e084a4a00706',
       encode(sha256(convert_to(vidhi_check,'UTF8')),'hex')),
      ('bg_gochara_citation_resolution',
       '9189699f8f72f40c9bff35e030be10beea517fa3dbe86f51ae08ab24ad1f7139',
       encode(sha256(convert_to(citation_check,'UTF8')),'hex'))
    ) expected(asset_id,metadata_sha,integrity_sha)
    LEFT JOIN asset_registry registry USING(asset_id)
    WHERE registry.asset_id IS NULL
       OR encode(sha256(convert_to(jsonb_build_array(
         registry.layer,registry.sort_order,registry.scope,registry.asset_kind,
         registry.catalog_status,registry.is_active,registry.has_writer,
         registry.target_table,registry.count_sql,registry.target_floor,
         registry.depends_on,registry.english_description,
         registry.volume_explanation,registry.natural_key_partition,
         registry.data_disposition
       )::text,'UTF8')),'hex') IS DISTINCT FROM expected.metadata_sha
       OR encode(sha256(convert_to(
         COALESCE(registry.integrity_check_sql,''),'UTF8')),'hex')
         IS DISTINCT FROM expected.integrity_sha
  ) THEN
    RAISE EXCEPTION 'migration 630 exact registry postflight failed';
  END IF;
END $$;

-- Append-only digest-spec revision for the newly owned yoga source-link table.
DO $$
DECLARE
  old_sha constant text :=
    '8a8b0f591ae397fc52198d1753e7858906dd3f30e2bef4e6cbdd33950dc57469';
  new_sha constant text :=
    '6d5ecdfe2f6b7e094d48c9d4863e783018f4a3ffb2121a0b69006ad5cb01ae7c';
  old_spec constant jsonb :=
    '{"components":[{"key_columns":["canonical_id"],"name":"yoga_catalog","relation":"brahma_yoga_catalog","value_columns":["canonical_id","name_sa","name_en","category","formation_rule_jsonb","formation_text","significations_jsonb","significations_text","cancellation_conditions","classical_citations","source_chunk_ids","school","rare","computed_strength_formula","bhanga_rules_jsonb","partial_formation_threshold","strength_formula_ref","result_class"]},{"key_columns":["entity_class","canonical_id"],"name":"yoga_ontology","relation":"brahma_ontology","value_columns":["entity_class","canonical_id","canonical_name_en","canonical_name_sa","synonyms","description","source_citation"],"where_equals":{"entity_class":"yoga"}},{"key_columns":["canonical_id"],"name":"reference_yogas","relation":"reference_yogas","value_columns":["canonical_id","name_en","category"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  new_spec constant jsonb :=
    '{"components":[{"key_columns":["canonical_id"],"name":"yoga_catalog","relation":"brahma_yoga_catalog","value_columns":["canonical_id","name_sa","name_en","category","formation_rule_jsonb","formation_text","significations_jsonb","significations_text","cancellation_conditions","classical_citations","source_chunk_ids","school","rare","computed_strength_formula","bhanga_rules_jsonb","partial_formation_threshold","strength_formula_ref","result_class"]},{"key_columns":["entity_class","canonical_id"],"name":"yoga_ontology","relation":"brahma_ontology","value_columns":["entity_class","canonical_id","canonical_name_en","canonical_name_sa","synonyms","description","source_citation"],"where_equals":{"entity_class":"yoga"}},{"key_columns":["canonical_id"],"name":"reference_yogas","relation":"reference_yogas","value_columns":["canonical_id","name_en","category"]},{"key_columns":["canonical_id","source_chunk_id"],"name":"yoga_source_chunks","relation":"brahma_yoga_source_chunks","value_columns":["canonical_id","source_chunk_id"]}],"version":"nirmana-output-digest-spec-v1"}'::jsonb;
  current_sha text;
  current_spec jsonb;
BEGIN
  SELECT spec_sha256,spec INTO current_sha,current_spec
  FROM asset_output_digest_specs
  WHERE asset_id='bg_yogas' AND retired_at IS NULL FOR UPDATE;
  IF NOT FOUND OR NOT (
    (current_sha=old_sha AND current_spec=old_spec)
    OR (current_sha=new_sha AND current_spec=new_spec)
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses unknown current bg_yogas digest spec: %',current_sha;
  END IF;
  IF current_sha=old_sha AND EXISTS (
    SELECT 1 FROM asset_output_digest_specs
    WHERE asset_id='bg_yogas' AND spec_sha256=new_sha
  ) THEN
    RAISE EXCEPTION 'migration 630 refuses pre-existing non-current yoga replacement';
  END IF;
  UPDATE asset_output_digest_specs SET retired_at=COALESCE(retired_at,now())
  WHERE asset_id='bg_yogas' AND spec_sha256=old_sha AND spec=old_spec
    AND retired_at IS NULL;
  INSERT INTO asset_output_digest_specs(asset_id,spec_sha256,spec)
  VALUES('bg_yogas',new_sha,new_spec)
  ON CONFLICT(asset_id,spec_sha256) DO NOTHING;
  IF NOT EXISTS (SELECT 1 FROM asset_output_digest_specs
      WHERE asset_id='bg_yogas' AND spec_sha256=new_sha
        AND spec=new_spec AND retired_at IS NULL) THEN
    RAISE EXCEPTION 'migration 630 yoga digest replacement postflight failed';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_output_digest_specs
      WHERE asset_id='bg_yogas' AND spec_sha256=old_sha
        AND spec=old_spec AND retired_at IS NOT NULL) THEN
    RAISE EXCEPTION 'migration 630 failed to retain exact retired yoga predecessor';
  END IF;
END $$;
