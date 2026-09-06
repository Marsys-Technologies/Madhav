-- 731_nirmana_l3_f_conc_7_size_sql_proportional.sql
--
-- NIRMĀṆA L3 Kāla — W3 (continuation range, ruled by the Conductor for L3: 730-739 —
-- see #1942/#1878, the previous 670-679 range fully consumed by migrations 670-679).
--
-- Discharges F-CONC-7 (L3_W1_ANALYSIS_BATCH_E.md PART 3, cross-cutting): all six of L3's
-- temporal-arbiter-adjacent assets (`ka_sangam`, `ka_vighnakara`, `ka_kalasutra`,
-- `ka_kala_darshana`, `ka_jivana_parva`, `ka_bhavishya_lekha`) had `asset_registry.size_sql`
-- = a bare `SELECT pg_total_relation_size('<table>')` — the WHOLE table's physical size,
-- with no chart scoping, on `scope='per_chart'` assets. With 3 charts resident, the cockpit
-- over-reported each chart's own footprint ~3x.
--
-- This was filed as adjudication #1956 rather than fixed unilaterally, because the root
-- cause was shared cockpit infrastructure, not L3's own registry rows: `platform/src/app/
-- api/cockpit/stats/route.ts` called `size_sql` with zero parameters, unlike `count_sql`,
-- which conditionally binds `$1` via `/\$1/.test(asset.count_sql) ? [chartId] : []`. Adding
-- `$1` to `size_sql` alone (this migration, without that fix) would have done nothing.
--
-- CONDUCTOR ruling (#1956, closed 2026-09-06): (a) the calling-code half shipped in PR
-- #1958 (merged 2026-09-06T04:25:49Z) — `stats/route.ts` now conditionally binds `$1` into
-- `size_sql` exactly mirroring `count_sql`'s pattern, plus derives `size_is_estimate =
-- /\$1/.test(asset.size_sql)` mechanically (no new registry column, can't drift
-- independently of the query's own shape); (b) the proportional-share estimate formula
-- proposed in the filing is APPROVED, with the disclosure requirement satisfied by (a)'s
-- `size_is_estimate` flag. This migration is the L3-side half the ruling authorized: "You're
-- clear to author the migration for L3's six rows... using the proportional-share formula
-- from your own filing, once #1958 merges."
--
-- FORMULA (this chart's proportional share of the table's total physical size — the only
-- honest option; Postgres has no cheap way to measure one chart's exact physical disk bytes
-- out of a shared table): total_size × (this chart's row count / total row count). Division
-- by zero guarded via GREATEST(..., 1) on the denominator, matching the filing's own text
-- verbatim. Table names verified live against each asset's own `count_sql` (same target
-- table in both queries — never assumed from the analysis batch alone):
--
--   ka_sangam            -> kala_convergence
--   ka_vighnakara         -> kala_obstruction
--   ka_kalasutra          -> kala_activation
--   ka_kala_darshana      -> kala_darshana
--   ka_jivana_parva       -> kala_jivana_parva
--   ka_bhavishya_lekha    -> kala_bhavishya
--
-- ADDITIONAL DEFECT FOUND WHILE WRITING THIS MIGRATION (fixed here, in scope, not a
-- separate escalation): `stats/route.ts` reads `sizeResult.rows[0]?.size` — a column
-- literally named `size`. Every one of the 77 existing `size_sql` values campaign-wide
-- (grepped live: zero contain `AS size`) is a bare `SELECT pg_total_relation_size(...)`,
-- which Postgres names `pg_total_relation_size`, not `size` — so `size_bytes` silently
-- reads `undefined`/null today for every asset in every layer, not just these six.
-- `count_sql`'s parallel bare `SELECT count(*) FROM ...` happens to work only because
-- Postgres names an unaliased `count(*)` column `count`, matching `.count` by
-- coincidence, not by the same convention. This migration's own SQL — proposed with an
-- explicit `AS size` alias in the original filing (#1956) and approved by the Conductor's
-- ruling as-is — is written correctly from the start rather than copying the campaign-wide
-- bare pattern forward; it does NOT touch any other layer's rows, so no other layer's
-- (pre-existing, silently-null) size_bytes is affected either way. Not re-escalated: this
-- is a genuinely separate, lower-severity defect (a missing/null informational field, not
-- a ~3x over-report) than F-CONC-7 itself, and fixing every layer's alias is out of this
-- migration's scope — noted here for the record per §N.7/§N.8 (an honest finding, not
-- silently absorbed), should a future session want to pick it up campaign-wide.
--
-- Purely a size_sql UPDATE — count_sql, depends_on, catalog_status and every other column
-- untouched. Idempotent: a deterministic overwrite of the same six rows' size_sql column,
-- re-running this migration produces byte-identical text (no random/timestamp component).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_convergence'')::float8 * ' ||
  '(SELECT count(*) FROM kala_convergence WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_convergence), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_sangam';

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_obstruction'')::float8 * ' ||
  '(SELECT count(*) FROM kala_obstruction WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_obstruction), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_vighnakara';

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_activation'')::float8 * ' ||
  '(SELECT count(*) FROM kala_activation WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_activation), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_kalasutra';

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_darshana'')::float8 * ' ||
  '(SELECT count(*) FROM kala_darshana WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_darshana), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_kala_darshana';

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_jivana_parva'')::float8 * ' ||
  '(SELECT count(*) FROM kala_jivana_parva WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_jivana_parva), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_jivana_parva';

UPDATE asset_registry SET size_sql =
  'SELECT (pg_total_relation_size(''kala_bhavishya'')::float8 * ' ||
  '(SELECT count(*) FROM kala_bhavishya WHERE chart_id = $1)::float8 / ' ||
  'GREATEST((SELECT count(*) FROM kala_bhavishya), 1)::float8)::bigint AS size'
WHERE asset_id = 'ka_bhavishya_lekha';
