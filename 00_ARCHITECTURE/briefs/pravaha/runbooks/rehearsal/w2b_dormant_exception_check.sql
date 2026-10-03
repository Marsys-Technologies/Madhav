-- RECORDED CONTEXT ONLY — NOT A GATE (steward ST-R23-AMEND, Codex round 23): the dormant exception this script re-verified is SUPERSEDED by the routine revoke migration (checklist row 3).
-- READ-ONLY. Describes role_orchestrator (the APPLICATION orchestrator role, not Suvarṇa's). Expected on production 2026-10-03: f | 0 | 0 | 0 | 0.
-- The fifth column counts DIRECT-LOGIN backends (pg_stat_activity.usename). It is NOT proof of zero EFFECTIVE sessions: a backend that did SET ROLE role_orchestrator keeps usename = its login.
SELECT r.rolcanlogin                                                                                                   AS can_login,        -- expect f (NOLOGIN)
       (SELECT count(*) FROM pg_auth_members m WHERE m.roleid = r.oid)                                                 AS has_members,      -- expect 0
       (SELECT count(*) FROM pg_auth_members m WHERE m.member = r.oid)                                                 AS member_of,        -- expect 0 (member of nothing)
       (SELECT count(*) FROM pg_shdepend d WHERE d.refclassid = 'pg_authid'::regclass AND d.refobjid = r.oid AND d.deptype = 'o') AS owned_objects, -- expect 0 (owns nothing, any database)
       (SELECT count(*) FROM pg_stat_activity a WHERE a.usename = r.rolname)                                           AS direct_login_backends -- expect 0 (zero DIRECT-LOGIN backends; effective SET ROLE sessions are not visible here)
  FROM pg_roles r WHERE r.rolname = 'role_orchestrator';
