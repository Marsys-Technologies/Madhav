-- Migration 1041: tracked compatibility boundary after the protected
-- data-plane ownership handoff. The routine login must not receive public
-- schema CREATE or membership in data_plane_schema_owner; migrate.ts now skips
-- tracker creation when the established tracker is already present.
SELECT 1041;
