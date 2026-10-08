-- Migration 1333: grant verifier conflict-key reads for idempotent receipts.
-- PostgreSQL requires SELECT on a conflict target even when the verifier uses
-- ON CONFLICT DO NOTHING. This remains narrower than general candidate access.
GRANT SELECT (chart_id, generation)
ON TABLE public.kala_layer_verification TO verifier_principal;
