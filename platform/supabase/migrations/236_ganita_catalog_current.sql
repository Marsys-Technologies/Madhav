-- 236_ganita_catalog_current.sql
-- Promote all Gaṇita (L1) assets from DRAFT → CURRENT in asset_registry.
-- L1 is SEALED (L1_GANITA_CLOSURE_v1_0.md); red dots on lit assets are wrong.
-- L2–L5 assets remain DRAFT — they are NOT sealed.
-- Companion to seed fix: asset_registry_seed.ts ga_* rows now carry catalog_status='CURRENT'.

UPDATE asset_registry
SET    catalog_status = 'CURRENT'
WHERE  layer = 'ganita';
