# Kāla migrations parked for a protected public-schema window

The routine production migrator (`amjis_app`) has USAGE but not CREATE on schema `public`
(verified 2026-10-08: `has_schema_privilege('amjis_app','public','CREATE') = false`; schema owner
`data_plane_schema_owner`). Migrations that create tables in `public` must apply through a protected
window in `deploy.yml` (as the Gochara contracts did via `gochara_contracts_schema_migration=true`),
never through the routine runner — otherwise every production deploy fails
(deploy 37749113939, 2026-10-08 08:19Z: `1330_kala_layer_manifest_candidates.sql` → permission denied for schema public).

Parked here, never applied in production:
- `1330_kala_layer_manifest_candidates.sql` (K0a-3) — four tables + table grants (the schema-level grant line must be dropped)
- `1334_kala_layer_verifier_conflict_read_grant.sql` (K0a-3) — grants on 1330's tables

They return to `platform/migrations/` together with a Kāla protected window, numbers unchanged (§2 reservations stand).
