-- 1273_builder_execute_bodha_identity_functions.sql  (S-L2 precondition B4)
--
-- HELD. NEVER RUN BY migrate.ts (executor-owned folder, outside the two directories migrate.ts reads; the number is allocated for history). Applied ONLY by
-- dp_builder_privileges_exec.py, in the same gated transaction as 1272, as amjis_app (the OWNER of these eight functions, read from production pg_proc 2026-10-03; they
-- are NOT owned by data_plane_l2_owner). A routine migration applied as amjis_app would also work for these grants (the owner grants); the executor carries them so the
-- two preconditions are one approved, verified, reversible step.
--
-- data_plane_builder (the pipeline login) has no EXECUTE on the identity functions used by bo_laksana, the five MSR satellites, bo_bimba and bo_karanajala:
-- `permission denied for function bodha_signal_identity`. Nothing else about the functions changes.
--
-- STATEMENTS (run as amjis_app):
GRANT EXECUTE ON FUNCTION public.bodha_cgm_edge_identity(uuid,text,text,text,uuid,uuid) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_cgm_edge_identity_namespace() TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_cgm_node_identity(uuid,text,text,text) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_cgm_node_identity_namespace() TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_contradiction_identity(uuid,text,uuid,uuid) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_contradiction_identity_namespace() TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_signal_identity(uuid,text,text,text,jsonb) TO data_plane_builder;
GRANT EXECUTE ON FUNCTION public.bodha_signal_identity_namespace() TO data_plane_builder;

-- exact inverse (rollback leg):
-- REVOKE EXECUTE ON FUNCTION public.bodha_cgm_edge_identity(uuid,text,text,text,uuid,uuid) FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_cgm_edge_identity_namespace() FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_cgm_node_identity(uuid,text,text,text) FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_cgm_node_identity_namespace() FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_contradiction_identity(uuid,text,uuid,uuid) FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_contradiction_identity_namespace() FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_signal_identity(uuid,text,text,text,jsonb) FROM data_plane_builder;
-- REVOKE EXECUTE ON FUNCTION public.bodha_signal_identity_namespace() FROM data_plane_builder;
