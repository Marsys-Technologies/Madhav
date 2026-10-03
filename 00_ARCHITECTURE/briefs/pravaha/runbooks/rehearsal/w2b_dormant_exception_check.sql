-- READ-ONLY re-verification of the ONE named dormant exception to W2(b) (steward ST-W2B-DORMANT-1; Suvarṇa: role_orchestrator is the APPLICATION orchestrator role, not theirs).
-- Run in checklist row 3 and again before row 8; record the output in the evidence. EXPECT exactly one row: f | 0 | 0 | 0 | 0 — otherwise the exception is VOID and W2(b) STOPs for that role.
SELECT r.rolcanlogin                                                                                                   AS can_login,        -- expect f (NOLOGIN)
       (SELECT count(*) FROM pg_auth_members m WHERE m.roleid = r.oid)                                                 AS has_members,      -- expect 0
       (SELECT count(*) FROM pg_auth_members m WHERE m.member = r.oid)                                                 AS member_of,        -- expect 0 (member of nothing)
       (SELECT count(*) FROM pg_shdepend d WHERE d.refclassid = 'pg_authid'::regclass AND d.refobjid = r.oid AND d.deptype = 'o') AS owned_objects, -- expect 0 (owns nothing, any database)
       (SELECT count(*) FROM pg_stat_activity a WHERE a.usename = r.rolname)                                           AS live_sessions     -- expect 0
  FROM pg_roles r WHERE r.rolname = 'role_orchestrator';
