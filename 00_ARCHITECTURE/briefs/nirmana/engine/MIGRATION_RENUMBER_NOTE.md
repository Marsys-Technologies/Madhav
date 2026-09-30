---
artifact: NIRMANA_ENGINE_MIGRATION_RENUMBER_NOTE
status: RECORD
landed_by: suvarna E3.2
---

# Engine migrations were renumbered at landing

The engine's STATE, DECISIONS, EVENTS, measurements and reviews in this directory were written on
branch `campaign/nirmana-engine` and refer to its three migrations by the numbers they had there.
Those numbers had already been overtaken on `main` (max 1152 across `platform/migrations/` and
`platform/supabase/migrations/`), so the migrations landed under new numbers and in `platform/migrations/`.
The records above are left verbatim, as historical evidence; read them through this table.

| Engine-branch name (as cited in these records) | Landed as | Packet |
|---|---|---|
| `platform/supabase/migrations/1094_asset_throughput_duration_seconds.sql` | `platform/migrations/1200_asset_throughput_duration_seconds.sql` | A1 |
| `platform/supabase/migrations/1095_build_run_assets_blocked_dependency.sql` | `platform/migrations/1201_build_run_assets_blocked_dependency.sql` | B1 |
| `platform/supabase/migrations/1096_vw_asset_downstream_dependents.sql` | `platform/migrations/1202_vw_asset_downstream_dependents.sql` | B2 |

The three old numbers were never applied to any environment (checked read-only against
`_migrations_applied` on 2026-09-30: no row for any 1094/1095/1096 file, and none of the objects they
create exist), so this is a rename of unapplied files, not of applied ones. SQL is unchanged.
