-- Migration 1203: allow receipt foreign-key checks to lock attempt keys
-- Created: 2026-10-01
-- The migration runner wraps this file in a transaction.
-- When amjis_app owns ai_metering_attempts, PostgreSQL checks the receipt FK
-- with SELECT ... FOR KEY SHARE as that owner. Migration 1202 revoked UPDATE
-- from the owner, so every terminal receipt fell back to durable recovery.
-- Grant only the referenced key column; the append-only trigger still rejects
-- every attempted UPDATE or DELETE of metering evidence.

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'amjis_app') THEN
    GRANT UPDATE (attempt_id) ON ai_metering_attempts TO amjis_app;
  END IF;
END $$;
