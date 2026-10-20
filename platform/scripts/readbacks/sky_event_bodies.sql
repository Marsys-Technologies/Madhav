WITH
-- sky_event_bodies.sql — READ-ONLY readback for J-3c-a52 (substrate proof).
-- One SELECT/WITH accepted by executor readback_sql (fleet/readback_sql.sh: single statement, no backslash).
--
-- What it proves: which bodies and event kinds ka_gochara_sky_event actually holds, and whether any Moon
-- row exists. The brief says "all bodies but the Moon; Moon on demand"; only a total (50124) was ever
-- read, and moon_non_event_class_coverage reads kala_gochara_coverage, never this table.
--
-- Columns are those of public.ka_gochara_sky_event in migration 1153 (body, event_kind, created_at).
-- The table is GLOBAL (shared sky substrate): it carries no chart_id, so no chart scoping applies.
-- kgse_body_domain_ck admits only sun, mars, mercury, jupiter, venus, saturn, rahu, ketu; the Moon is
-- ephemeral (moon_on_demand.py) — the 'moon' section row below must therefore read 0.
--
-- Output sections (ORDER BY section, body, event_kind is total — the triple is unique per row):
--   1  one row per (body, event_kind): count, first and last created_at
--   2  the Moon: every row whose body is 'moon' in any letter case (0 expected; never a missing row)
--   3  the whole table: total row count and created_at span
-- No personal data: counts, body/kind names and timestamps only.
per_body_kind AS (
  SELECT body, event_kind, count(*) AS n, min(created_at) AS first_created_at, max(created_at) AS last_created_at
    FROM ka_gochara_sky_event
   GROUP BY body, event_kind
)
SELECT 1 AS section, body, event_kind, n, first_created_at, last_created_at
  FROM per_body_kind
UNION ALL
SELECT 2, 'moon', '(all kinds)', count(*), min(created_at), max(created_at)
  FROM ka_gochara_sky_event
 WHERE lower(body) = 'moon'
UNION ALL
SELECT 3, '(all bodies)', '(all kinds)', count(*), min(created_at), max(created_at)
  FROM ka_gochara_sky_event
 ORDER BY 1, 2, 3
