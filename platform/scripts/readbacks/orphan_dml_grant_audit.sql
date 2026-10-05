-- orphan_dml_grant_audit.sql — READ-ONLY audit (C51, role_orchestrator follow-through).
--
-- Lists every NOLOGIN role that has NO members (no role holds it through pg_auth_members)
-- and yet holds INSERT / UPDATE / DELETE / TRUNCATE on any table in schema public, with the
-- table owner and the grantor — so the owner can see whether role_orchestrator's leftover
-- grants (revoked by 1302 on the windows tables) are a one-off or a pattern.
--
-- Emits TSV: role, table, table_owner, grantor, privileges (comma-joined, only the DML four).
-- A role's OWN implicit owner rights never appear (owner rights are not grant entries; a NULL
-- relacl yields no aclexplode rows). SELECT-only grants, LOGIN roles, and roles with members
-- are out of scope by design. Every statement is a SELECT; the runner forces a read-only session.

SELECT r.rolname AS role,
       c.relname AS table_name,
       pg_get_userbyid(c.relowner) AS table_owner,
       pg_get_userbyid(a.grantor) AS grantor,
       string_agg(DISTINCT a.privilege_type, ',' ORDER BY a.privilege_type) AS privileges
  FROM pg_roles r
  JOIN pg_class c
    ON c.relnamespace = 'public'::regnamespace
   AND c.relkind IN ('r', 'p')                       -- ordinary and partitioned tables
  JOIN LATERAL aclexplode(c.relacl) a
    ON a.grantee = r.oid
 WHERE r.rolcanlogin = false
   AND NOT EXISTS (SELECT 1 FROM pg_auth_members m WHERE m.roleid = r.oid)
   AND a.privilege_type IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE')
 GROUP BY r.rolname, c.relname, c.relowner, a.grantor
 ORDER BY 1, 2, 4;
