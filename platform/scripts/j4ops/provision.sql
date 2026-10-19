-- Independent effective ACL capture. SELECT only; no credential values.
-- Whole-row L1 digests need SELECT on ALL columns, not selected column grants.
-- Include column-level write grants: table-level has_table_privilege alone misses them.
WITH wanted AS (
  SELECT role_name, table_name, privilege
  FROM (VALUES ('gochara_verifier'), ('gochara_sealer')) r(role_name)
  CROSS JOIN (VALUES ('chart_facts'), ('chart_dashas')) t(table_name)
  CROSS JOIN (VALUES ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'),
                     ('TRUNCATE'), ('REFERENCES'), ('TRIGGER')) p(privilege)
  UNION ALL
  SELECT 'data_plane_builder', table_name, privilege
  FROM (VALUES ('ka_gochara_eval_window_verification'),
               ('ka_gochara_search_inventory_verification')) t(table_name)
  CROSS JOIN (VALUES ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE')) p(privilege)
), cells AS (
  SELECT w.role_name AS role, w.table_name AS "table", w.privilege,
    CASE WHEN r.oid IS NULL OR c.oid IS NULL THEN NULL
         WHEN w.privilege IN ('INSERT', 'UPDATE', 'REFERENCES') THEN
           has_table_privilege(r.oid, c.oid, w.privilege)
           OR has_any_column_privilege(r.oid, c.oid, w.privilege)
         ELSE has_table_privilege(r.oid, c.oid, w.privilege) END AS present
  FROM wanted w
  LEFT JOIN pg_roles r ON r.rolname = w.role_name
  LEFT JOIN pg_class c ON c.oid = to_regclass('public.' || w.table_name)
)
SELECT jsonb_agg(to_jsonb(cells) ORDER BY role COLLATE "C", "table" COLLATE "C", privilege COLLATE "C") FROM cells;
