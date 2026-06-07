-- classical_attributions note migration
-- The table already exists (MSR signal attribution table from prior workstream).
-- bg_concordance points to it as dormant placeholder (0 rows) — count_sql is valid.
-- This migration is a no-op; it exists to keep the migration sequence contiguous.
-- The cross-school concordance build will add a new table when that workstream opens.
DO $$ BEGIN
  COMMENT ON TABLE classical_attributions IS
    'MSR signal-to-text attribution table. Also registered as bg_concordance dormant '
    'placeholder in asset_registry. Cross-school divergence content deferred to future workstream.';
END $$;
