-- Migration 1417: record the qualified CDLM canonical achieved floor.
-- Created: 2026-11-14. Transaction owned by platform/scripts/migrate.ts.
-- CLAUDE N.4: floors are aspirational achieved counts, never data gates.
-- Evidence: canonical run8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f completed
-- 2026-11-14T10:33:57Z on sourcebc43fd6579401d3f4fcdeeece803f6f522153190.
-- Execution brahma-build-pipeline-job-xq8lt used immutable Pipeline image
-- fc6b592f3107179d808a5dd0d9746a59cc4a6e004131d176a88590d9dc2dc085.
-- WriterResult/log/throughput/count_sql agree:5summary+60rollups+5clusters=70.
-- The three-table receipt is proven and fresh under spec635258ec..., with
-- output digest0a1fc095ff5c09728008631d8ba52cb8993d0151b591434191bad9733f67bdb8.
-- This is ONE chart's achieved count, NOT a universal minimum for sparse charts.
-- Both reviewed358 baselines (applied1/disclosed-source replay5) are accepted.
-- Historical358/986/987/1416 SQL, applied ledger identities and all receipts
-- remain untouched. No output row is inserted, deleted or updated here.
-- Trigger596 intentionally stales ALL bo_cdlm_summary freshness projections:
-- observed before apply:3rows/2charts; one current canonical row fresh, two
-- historical-partition rows already stale. The necessary canonical governed
-- recovery build alone may restore its current partition; historical rows stay.
-- This statement never promotes freshness, rewrites a receipt or dispatches work.
-- A later reversal requires a new reviewed forward migration, not replay of358.

SET LOCAL lock_timeout = '5s';

DO $floor$
DECLARE f bigint; c text; p text; part text;
BEGIN
  SELECT target_floor, md5(count_sql), md5(natural_key_partition), natural_key_partition
    INTO f, c, p, part FROM asset_registry
   WHERE asset_id = 'bo_cdlm_summary' FOR UPDATE;
  IF NOT FOUND OR f IS NULL OR f NOT IN (1, 5, 70)
     OR c IS DISTINCT FROM '436138f8ef007f232680cf2673233019'
     OR p IS DISTINCT FROM '92288d671a134367e47f9e02f87cecdd' THEN
    RAISE EXCEPTION '1417: CDLM floor/count/partition is not the reviewed contract';
  END IF;
  IF (SELECT count(*) FROM asset_output_digest_specs
       WHERE asset_id='bo_cdlm_summary' AND retired_at IS NULL) <> 1
     OR NOT EXISTS (SELECT 1 FROM asset_output_digest_specs
       WHERE asset_id='bo_cdlm_summary' AND retired_at IS NULL
         AND spec_sha256='635258ecb9fbfd137a048875e5a5b3a53d5179b3ac9ed64481a60fe5b402ac8e'
         AND jsonb_array_length(spec->'components')=3) THEN
    RAISE EXCEPTION '1417: reviewed full-three-table spec is not current';
  END IF;
  IF f=70 THEN
    -- Idempotent after application or normal recovery: no fresh/stale mutation.
    RAISE NOTICE '1417: qualified achieved floor70 already recorded';
    RETURN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM build_runs b
      WHERE b.id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f'
        AND b.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
        AND b.state='completed' AND b.ended_at IS NOT NULL
        AND b.scope='asset' AND b.scope_target='bo_cdlm_summary' AND b.action='rebuild'
        AND b.plan='["bo_cdlm_summary"]'::jsonb
        AND b.plan_manifest_digest='f6ac1ea8c170c8aeb2908addd38943e8720496ad26ce470f13288dd84e41ff91'
        AND b.plan_manifest->>'version'='nirmana-run-manifest/v1'
        AND jsonb_array_length(b.plan_manifest->'assets')=1
        AND b.plan_manifest->'assets'->0->>'asset_id'='bo_cdlm_summary'
        AND b.plan_manifest->'assets'->0->>'expected_code_digest'=
          '63d1f579b801538512901674f56277d1f31b47c8fbffb2de1c4442131ce4439f')
     OR EXISTS (SELECT 1 FROM build_runs newer JOIN build_runs qualified
          ON qualified.id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f'
       WHERE newer.chart_id=qualified.chart_id AND newer.id<>qualified.id
         AND newer.created_at>=qualified.created_at
         AND newer.plan @> '["bo_cdlm_summary"]'::jsonb) THEN
    RAISE EXCEPTION '1417: completed single-asset achieved run is missing or superseded';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM asset_provenance_receipts r
      JOIN asset_freshness af ON af.asset_id=r.asset_id AND af.chart_id=r.chart_id
                            AND af.partition_key=r.partition_key
      JOIN asset_throughput t ON t.asset_id=r.asset_id AND t.chart_id=r.chart_id
      WHERE r.asset_id='bo_cdlm_summary'
        AND r.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
        AND r.partition_key=part AND r.build_id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f'
        AND r.code_digest='63d1f579b801538512901674f56277d1f31b47c8fbffb2de1c4442131ce4439f'
        AND r.output_digest_spec_sha256='635258ecb9fbfd137a048875e5a5b3a53d5179b3ac9ed64481a60fe5b402ac8e'
        AND r.receipt_state='proven' AND r.unknown_reasons='[]'::jsonb
        AND r.output_digest ~ '^[a-f0-9]{64}$' AND r.config_digest ~ '^[a-f0-9]{64}$'
        AND r.upstream_digest ~ '^[a-f0-9]{64}$'
        AND af.freshness_state='fresh' AND af.reasons='[]'::jsonb
        AND t.state='lit' AND t.rows_written=70 AND t.last_error IS NULL
        AND t.built_against_writer_hash=r.code_digest
        AND t.built_against_upstream_hash=r.upstream_digest) THEN
    RAISE EXCEPTION '1417: current writer/receipt/freshness/throughput proof is incomplete';
  END IF;
  IF EXISTS (
    WITH stats AS (
      SELECT 5 expected, count(*) n,
        count(*) FILTER (WHERE build_id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f' AND snapshot_type='static_natal') current_n,
        count(DISTINCT (chart_id,ayanamsha_id,snapshot_type)) keys,
        count(*) FILTER (WHERE ayanamsha_id IS NULL OR snapshot_type IS NULL) nulls,
        array_agg(DISTINCT ayanamsha_id ORDER BY ayanamsha_id) ayas
      FROM bodha_cdlm_chart_summary WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
      UNION ALL SELECT 60,count(*),
        count(*) FILTER (WHERE build_id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f' AND snapshot_type='static_natal'),
        count(DISTINCT (chart_id,ayanamsha_id,snapshot_type,domain)),
        count(*) FILTER (WHERE ayanamsha_id IS NULL OR snapshot_type IS NULL OR domain IS NULL),
        array_agg(DISTINCT ayanamsha_id ORDER BY ayanamsha_id)
      FROM bodha_cdlm_domain_rollups WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
      UNION ALL SELECT 5,count(*),
        count(*) FILTER (WHERE build_id='8a5ef75c-7b57-437c-acb9-0cf08a7b6d6f' AND snapshot_type='static_natal'),
        count(DISTINCT (chart_id,ayanamsha_id,snapshot_type,pattern_marker_type)),
        count(*) FILTER (WHERE ayanamsha_id IS NULL OR snapshot_type IS NULL OR pattern_marker_type IS NULL),
        array_agg(DISTINCT ayanamsha_id ORDER BY ayanamsha_id)
      FROM bodha_cdlm_pattern_clusters WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
    ) SELECT 1 FROM stats WHERE n<>expected OR current_n<>expected OR keys<>expected OR nulls<>0
       OR ayas IS DISTINCT FROM ARRAY['krishnamurti','lahiri_chitrapaksha','raman','surya_siddhanta_classical','true_chitra']::text[]
  ) THEN
    RAISE EXCEPTION '1417: three-table achieved70 counts/keys/AYA/build proof changed';
  END IF;

  UPDATE asset_registry SET target_floor=70 WHERE asset_id='bo_cdlm_summary';
  IF NOT EXISTS (SELECT 1 FROM asset_registry WHERE asset_id='bo_cdlm_summary'
                  AND target_floor=70 AND md5(count_sql)=c AND natural_key_partition=part)
     OR EXISTS (SELECT 1 FROM asset_freshness WHERE asset_id='bo_cdlm_summary'
                  AND (freshness_state<>'stale' OR NOT (reasons ? 'registry_changed'))) THEN
    RAISE EXCEPTION '1417: floor or honest trigger596 invalidation postcondition failed';
  END IF;
END
$floor$;
