-- Migration 317: clear stale error on ga_pyjhora_engine asset_throughput
--
-- Root cause: the `pyjhora_engine` probe_type handler was missing from
-- service_probes.py when the probe ran on 2026-06-12, producing the error
-- "unknown probe_type: pyjhora_engine". The handler has since been added.
-- The underlying pyjhora_adapter service is healthy (all L1 ga_* writers
-- that depend on it are in `lit` state).
-- This migration clears the stale error so the next Rebuild regenerates a
-- clean probe run. state reset to 'dormant' (column default, NOT NULL).

UPDATE asset_throughput
SET
    state      = 'dormant',
    last_error = NULL
WHERE asset_id = 'ga_pyjhora_engine';
