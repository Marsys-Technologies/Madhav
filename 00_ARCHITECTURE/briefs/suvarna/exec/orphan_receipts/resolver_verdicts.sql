-- resolver_verdicts.sql  (READ-ONLY; one SELECT; no writes)
--
-- Per-asset served-generation verdict for ONE chart: a SQL port of RESOLVER_SQL + classifyAssetGeneration in
-- platform/src/lib/retrieval/registry/generation/served_generation.ts (origin/main). Parameter: the psql variable
-- `chart` (a chart uuid), written below as :'chart'. The executor (orphan_receipts_exec.py) loads THIS file and
-- substitutes :'chart' with a bound query parameter, so the executor and the standing check share one definition.
--
-- Run as suvarna_reader (see README.md):
--   psql -X -A -t -v chart=482012f1-710e-4a25-994a-93821f5871aa -f resolver_verdicts.sql
-- Output rows: asset_id | verdict | partitions
--
-- Fidelity: validated only against a reading of served_generation.ts (design review section 5). It is NOT the deployed
-- code. The executor uses it as a before/after DIFF (nothing else may change), not as an absolute oracle.
-- Every relation is schema-qualified so the file also runs under the executor's `search_path = pg_catalog, pg_temp`.
WITH base AS (
  SELECT receipt.asset_id, receipt.partition_key, receipt.receipt_state, freshness.freshness_state,
         receipt.build_id::text AS receipt_build_id,
         EXISTS (SELECT 1 FROM public.asset_output_digest_specs s WHERE s.asset_id = receipt.asset_id AND s.spec_sha256 = receipt.output_digest_spec_sha256 AND s.retired_at IS NULL) AS spec_active,
         receipt_run.state AS run_state, (receipt_asset.run_id IS NOT NULL) AS asset_present, receipt_asset.disposition AS disp,
         (CASE
      WHEN receipt_asset.run_id IS NULL THEN NULL
      WHEN receipt_asset.disposition = 'skip_no_delta' THEN (
        SELECT writer_asset.run_id FROM public.build_run_assets writer_asset JOIN public.build_runs writer_run ON writer_run.id = writer_asset.run_id
         WHERE writer_run.chart_id = receipt.chart_id AND writer_asset.asset_id = receipt.asset_id AND writer_asset.state = 'complete'
           AND (writer_asset.disposition IS NULL OR writer_asset.disposition = 'build')
           AND COALESCE(writer_asset.ended_at, writer_run.ended_at) <= COALESCE(receipt_asset.started_at, receipt_run.started_at, receipt.observed_at)
         ORDER BY COALESCE(writer_asset.ended_at, writer_run.ended_at) DESC, writer_asset.run_id DESC LIMIT 1)
      WHEN (receipt_asset.disposition IS NULL OR receipt_asset.disposition = 'build') AND receipt_asset.state = 'complete' THEN receipt.build_id
      ELSE NULL END) AS writer
    FROM public.asset_provenance_receipts receipt
    LEFT JOIN public.asset_freshness freshness ON freshness.asset_id = receipt.asset_id AND freshness.scope_key = receipt.scope_key AND freshness.partition_key = receipt.partition_key AND freshness.receipt_version = receipt.receipt_version
    LEFT JOIN public.build_runs receipt_run ON receipt_run.id = receipt.build_id AND receipt_run.chart_id = receipt.chart_id
    LEFT JOIN public.build_run_assets receipt_asset ON receipt_asset.run_id = receipt.build_id AND receipt_asset.asset_id = receipt.asset_id
   WHERE receipt.chart_id = :'chart'::uuid
), r AS (
 SELECT b.*, (CASE WHEN EXISTS (
        SELECT 1 FROM public.build_run_assets attempt JOIN public.build_runs attempt_run ON attempt_run.id = attempt.run_id
         WHERE attempt_run.chart_id = :'chart'::uuid AND attempt.asset_id = b.asset_id AND attempt.run_id <> b.writer
           AND attempt.started_at IS NOT NULL AND attempt.state IN ('building','error','aborted','complete')
           AND attempt.disposition IS DISTINCT FROM 'skip_no_delta'
           AND COALESCE(attempt.ended_at, attempt_run.ended_at, 'infinity'::timestamptz) > (
             SELECT COALESCE(wd.ended_at, wdr.ended_at) FROM public.build_run_assets wd JOIN public.build_runs wdr ON wdr.id = wd.run_id WHERE wd.run_id = b.writer AND wd.asset_id = b.asset_id))
     THEN NULL ELSE b.writer END) AS rows_build
 FROM base b)
SELECT asset_id,
  CASE WHEN bool_or(receipt_state <> 'proven') THEN 'receipt_not_proven'
       WHEN bool_or(freshness_state IS DISTINCT FROM 'fresh') THEN 'receipt_not_fresh'
       WHEN bool_or(NOT spec_active) THEN 'receipt_spec_retired'
       WHEN bool_or(run_state IS DISTINCT FROM 'completed') THEN 'receipt_run_not_completed'
       WHEN bool_or(NOT asset_present) THEN 'receipt_run_asset_missing'
       WHEN bool_or(rows_build IS NULL) THEN 'intervening_or_writer_missing'
       WHEN count(DISTINCT rows_build) <> 1 THEN 'partition_generation_split'
       ELSE 'RESOLVED' END AS verdict, count(*) AS partitions
FROM r GROUP BY asset_id ORDER BY 2, 1
