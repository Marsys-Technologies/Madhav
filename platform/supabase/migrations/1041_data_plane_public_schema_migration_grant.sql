-- Migration 1041: restore the ordinary migration route after the protected
-- data-plane ownership handoff made data_plane_schema_owner the public-schema
-- owner. amjis_app is intentionally a member of that owner role and remains
-- the deployment workflow's non-privileged migration login.
SET LOCAL ROLE data_plane_schema_owner;
GRANT USAGE, CREATE ON SCHEMA public TO amjis_app;
RESET ROLE;
