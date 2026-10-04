-- disposable cluster: roles mirroring production topology (read from prod catalog)
CREATE ROLE amjis_app LOGIN;
CREATE ROLE data_plane_schema_owner NOLOGIN;
CREATE ROLE data_plane_l1_owner NOLOGIN;
CREATE ROLE data_plane_l2_owner NOLOGIN;
CREATE ROLE data_plane_builder LOGIN NOINHERIT;
CREATE ROLE data_plane_verifier LOGIN NOINHERIT;
CREATE ROLE data_plane_migrator LOGIN NOINHERIT;
CREATE ROLE role_orchestrator NOLOGIN INHERIT;
CREATE ROLE role_web_serve NOLOGIN;
CREATE ROLE role_jobs NOLOGIN;
CREATE ROLE role_sidecar NOLOGIN;
GRANT data_plane_l1_owner, data_plane_l2_owner, data_plane_schema_owner TO data_plane_migrator;
