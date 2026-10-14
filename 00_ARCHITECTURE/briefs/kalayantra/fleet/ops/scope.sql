-- Reviewed read-only preflight input for all four wrappers. Execute only via the governed readback path.
SELECT json_build_object('schema', 'ky.ops_scope/1',
 'registry', (SELECT json_agg(r) FROM (
SELECT asset_id, layer_index, scope, is_active, has_writer,
 COALESCE(depends_on, '{}') AS depends_on, target_table, count_sql,
 integrity_check_sql, target_floor FROM asset_registry ORDER BY asset_id
) r),
 'tables', (SELECT json_agg(t) FROM (
SELECT n.nspname AS schema, c.relname AS name,
 COALESCE((SELECT json_agg(DISTINCT rn.nspname || '.' || rc.relname ORDER BY rn.nspname || '.' || rc.relname)
 FROM pg_constraint fk JOIN pg_class rc ON rc.oid=fk.confrelid
 JOIN pg_namespace rn ON rn.oid=rc.relnamespace
 WHERE fk.conrelid=c.oid AND fk.contype='f'), '[]'::json) AS depends_on
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE n.nspname='public' AND c.relkind IN ('r','p') ORDER BY c.relname
) t));
