-- platform/migrations/038_observatory_schema_down.sql
-- Down migration for 038_observatory_schema.sql.
-- Drops the five Observatory tables in reverse dependency order:
--   - llm_usage_events FKs into llm_pricing_versions, so it must drop first.
--   - The other three tables (cost_reports, reconciliation, budget_rules) have
--     no inter-table FKs.
-- All DROPs are IF EXISTS so the down is idempotent and safe to run twice.

BEGIN;

DROP TABLE IF EXISTS llm_usage_events;
DROP TABLE IF EXISTS llm_budget_rules;
DROP TABLE IF EXISTS llm_cost_reconciliation;
DROP TABLE IF EXISTS llm_provider_cost_reports;
DROP TABLE IF EXISTS llm_pricing_versions;

COMMIT;
