-- orphan_count.sql  (READ-ONLY standing check; one SELECT; no writes; returns metadata only, no row content)
--
-- A chart-scoped receipt row is an ORPHAN when its partition_key differs from the partition the registry declares for
-- its asset now: coalesce(nullif(btrim(asset_registry.natural_key_partition), ''), '__whole_asset__'). Provenance writes
-- the `__whole_asset__` key while the registry declares none; declaring a partition later orphans that row (it is never
-- deleted by anything) and the served-generation resolver then refuses the whole asset (receipt_not_proven).
-- Source: DESIGN_REVIEW_LEGACY_WHOLE_ASSET_RECEIPTS section 4.6.
--
-- EXPECTED: ZERO rows. Run it as an S-L1/S-L2 exit check and before any registry edit that adds a
-- natural_key_partition:
--   psql -X -A -t -f orphan_count.sql | wc -l          # the orphan count (0 = clean)
-- Columns: asset_id | chart_id | orphan_partition_key | registry_declares_partition | orphans_total
SELECT r.asset_id, r.chart_id, r.partition_key AS orphan_partition_key,
       (nullif(btrim(ar.natural_key_partition), '') IS NOT NULL) AS registry_declares_partition,
       count(*) OVER () AS orphans_total
  FROM public.asset_provenance_receipts r
  JOIN public.asset_registry ar USING (asset_id)
 WHERE r.chart_id IS NOT NULL
   AND r.partition_key <> coalesce(nullif(btrim(ar.natural_key_partition), ''), '__whole_asset__')
 ORDER BY r.asset_id, r.chart_id;
