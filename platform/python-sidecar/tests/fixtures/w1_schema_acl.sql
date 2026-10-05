ALTER SCHEMA public OWNER TO data_plane_schema_owner;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_schema_owner;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_l1_owner;
GRANT USAGE, CREATE ON SCHEMA public TO data_plane_l2_owner;
GRANT USAGE ON SCHEMA public TO data_plane_migrator, data_plane_builder, data_plane_verifier, amjis_app, role_web_serve, purna_inquiry_owner, suvarna_reader;
