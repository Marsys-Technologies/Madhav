-- Migration 342: Retire ga_pyjhora_engine from asset_registry
-- ga_pyjhora_engine was inserted by supabase/migrations/205_ga1_pyjhora_service.sql
-- but was never added to the authoritative asset_registry_seed.ts superset.
-- L1 is SEALED; the PyJHora engine service asset is retired from the registry.
-- Companion code cleanup: service_probes.py probe removed, assetClearSpec.ts null entry removed.
-- Physical DROP of any related tables is not needed (service asset — no stored rows).

BEGIN;

DELETE FROM asset_registry WHERE asset_id = 'ga_pyjhora_engine';

-- Also clear any stale asset_throughput entry (migration 317 left it in error state)
DELETE FROM asset_throughput WHERE asset_id = 'ga_pyjhora_engine';

COMMIT;
