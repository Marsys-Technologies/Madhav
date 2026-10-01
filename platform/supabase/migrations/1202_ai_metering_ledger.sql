-- Migration 1202: immutable AI attempt ledger and rate evidence
-- Created: 2026-09-29. Apply only through the exact protected deploy window.
-- Transaction belongs to the migration runner, including tracking.

CREATE TABLE IF NOT EXISTS ai_metering_attempts (
  attempt_id uuid PRIMARY KEY,
  user_id text NOT NULL,
  conversation_id text,
  turn_id text NOT NULL,
  operation_id text NOT NULL,
  parent_operation_id text,
  channel text NOT NULL CHECK (channel IN ('web','mcp','api','backend','scheduled','unknown')),
  purpose text NOT NULL CHECK (purpose IN ('customer','admin_test','validation','evaluation','background','legacy')),
  payer text NOT NULL CHECK (payer IN ('user','platform','subscription','unknown')),
  provider text NOT NULL,
  model text NOT NULL,
  role text NOT NULL,
  connection_id text,
  snapshot_id text,
  test_run_id text,
  requested_model text,
  aggregation text NOT NULL CHECK (aggregation IN ('transport','cli_aggregate','legacy_aggregate')),
  started_at timestamptz NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ai_metering_attempts_owner_time ON ai_metering_attempts(user_id,started_at DESC,attempt_id DESC);
CREATE INDEX IF NOT EXISTS ai_metering_attempts_conversation ON ai_metering_attempts(user_id,conversation_id,turn_id);
CREATE INDEX IF NOT EXISTS ai_metering_attempts_operation ON ai_metering_attempts(operation_id);

CREATE TABLE IF NOT EXISTS ai_metering_rate_cards (
  id uuid PRIMARY KEY,
  provider text NOT NULL,
  model text NOT NULL,
  effective_from timestamptz NOT NULL,
  observed_at timestamptz NOT NULL,
  source_url text NOT NULL,
  card jsonb NOT NULL CHECK (jsonb_typeof(card)='object'),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(provider,model,effective_from)
);
CREATE INDEX IF NOT EXISTS ai_metering_rates_lookup ON ai_metering_rate_cards(provider,model,effective_from DESC);

CREATE TABLE IF NOT EXISTS ai_metering_receipts (
  attempt_id uuid PRIMARY KEY REFERENCES ai_metering_attempts(attempt_id),
  finished_at timestamptz NOT NULL,
  status text NOT NULL CHECK (status IN ('success','error','timeout','cancelled','incomplete')),
  usage jsonb NOT NULL CHECK (jsonb_typeof(usage)='object'),
  provider_request_id text,
  finish_reason text,
  first_token_at timestamptz,
  provider_cost_usd numeric(30,12) CHECK (provider_cost_usd >= 0),
  computed_cost_usd numeric(30,12) CHECK (computed_cost_usd >= 0),
  pricing_status text NOT NULL CHECK (pricing_status IN ('priced','usage_unavailable','usage_inconsistent','rate_unavailable','rate_inapplicable','partial_rate')),
  pricing_snapshot jsonb NOT NULL CHECK (jsonb_typeof(pricing_snapshot)='object'),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((pricing_status = 'priced') = (computed_cost_usd IS NOT NULL))
);

CREATE OR REPLACE FUNCTION ai_metering_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN
  RAISE EXCEPTION 'AI metering evidence is append-only' USING ERRCODE='55000';
END $$;
DROP TRIGGER IF EXISTS ai_metering_attempts_immutable ON ai_metering_attempts;
CREATE TRIGGER ai_metering_attempts_immutable BEFORE UPDATE OR DELETE ON ai_metering_attempts
  FOR EACH ROW EXECUTE FUNCTION ai_metering_reject_mutation();
DROP TRIGGER IF EXISTS ai_metering_receipts_immutable ON ai_metering_receipts;
CREATE TRIGGER ai_metering_receipts_immutable BEFORE UPDATE OR DELETE ON ai_metering_receipts
  FOR EACH ROW EXECUTE FUNCTION ai_metering_reject_mutation();
DROP TRIGGER IF EXISTS ai_metering_rates_immutable ON ai_metering_rate_cards;
CREATE TRIGGER ai_metering_rates_immutable BEFORE UPDATE OR DELETE ON ai_metering_rate_cards
  FOR EACH ROW EXECUTE FUNCTION ai_metering_reject_mutation();
DROP TRIGGER IF EXISTS ai_metering_attempts_no_truncate ON ai_metering_attempts;
CREATE TRIGGER ai_metering_attempts_no_truncate BEFORE TRUNCATE ON ai_metering_attempts
  FOR EACH STATEMENT EXECUTE FUNCTION ai_metering_reject_mutation();
DROP TRIGGER IF EXISTS ai_metering_receipts_no_truncate ON ai_metering_receipts;
CREATE TRIGGER ai_metering_receipts_no_truncate BEFORE TRUNCATE ON ai_metering_receipts
  FOR EACH STATEMENT EXECUTE FUNCTION ai_metering_reject_mutation();
DROP TRIGGER IF EXISTS ai_metering_rates_no_truncate ON ai_metering_rate_cards;
CREATE TRIGGER ai_metering_rates_no_truncate BEFORE TRUNCATE ON ai_metering_rate_cards
  FOR EACH STATEMENT EXECUTE FUNCTION ai_metering_reject_mutation();

-- Firebase ownership is enforced by server APIs. Browser database roles get no access.
REVOKE ALL ON ai_metering_attempts, ai_metering_receipts, ai_metering_rate_cards FROM PUBLIC;
DO $$ DECLARE t text; role_name text; BEGIN
  FOREACH t IN ARRAY ARRAY['ai_metering_attempts','ai_metering_receipts','ai_metering_rate_cards'] LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    FOREACH role_name IN ARRAY ARRAY['amjis_app','service_role'] LOOP
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=role_name) THEN
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', 'metering_' || role_name, t);
        EXECUTE format('CREATE POLICY %I ON %I TO %I USING (true) WITH CHECK (true)', 'metering_' || role_name, t, role_name);
        EXECUTE format('GRANT SELECT, INSERT ON %I TO %I', t, role_name);
        EXECUTE format('REVOKE UPDATE, DELETE, TRUNCATE ON %I FROM %I', t, role_name);
      END IF;
    END LOOP;
  END LOOP;
END $$;
