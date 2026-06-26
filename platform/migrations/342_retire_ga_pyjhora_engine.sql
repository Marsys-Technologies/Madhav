-- Migration 342: Retire ga_pyjhora_engine from asset_registry
-- ga_pyjhora_engine was inserted by supabase/migrations/205_ga1_pyjhora_service.sql
-- but was never added to the authoritative asset_registry_seed.ts superset.
-- L1 is SEALED; the PyJHora engine service asset is retired from the registry.
-- Companion code cleanup: service_probes.py probe removed, assetClearSpec.ts null entry removed.
-- Physical DROP of any related tables is not needed (service asset — no stored rows).

BEGIN;

-- Delete throughput first (FK asset_throughput_asset_id_fkey references asset_registry.asset_id;
-- deleting asset_registry before throughput violates the FK at statement level)
DELETE FROM asset_throughput WHERE asset_id = 'ga_pyjhora_engine';

DELETE FROM asset_registry WHERE asset_id = 'ga_pyjhora_engine';

COMMIT;
