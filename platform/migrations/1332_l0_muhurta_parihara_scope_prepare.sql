-- 1332_l0_muhurta_parihara_scope_prepare.sql
--
-- KĀLA-YANTRA L0-M bounded preparation (KYD-45).  The existing reference
-- table already contains natal and muhūrta rows.  ALGO 3.17 step 3 requires
-- locator-backed rules to be recorded with the narrower undertaking scopes
-- marriage and upanayana, plus the explicitly general clause.  This migration
-- changes only the scope domain: it neither inserts extracted rules nor moves
-- the coordinated count/hash pin.  Those actions require the separate
-- Strategic Suvarṇa reseal recorded by the item brief.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

ALTER TABLE bg_parihara_rules
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_scope_check;

ALTER TABLE bg_parihara_rules
  ADD CONSTRAINT bg_parihara_rules_scope_check
    CHECK (scope IN ('natal', 'muhurta', 'marriage', 'upanayana', 'general'));

COMMENT ON COLUMN bg_parihara_rules.scope IS
  'Rule applicability: natal and muhūrta retain their established meanings; '
  'marriage, upanayana and general are the bounded L0-M extraction scopes from '
  'Muhūrta Cintāmaṇi locators.  This migration admits no new rule rows and does '
  'not classify any existing row.';
