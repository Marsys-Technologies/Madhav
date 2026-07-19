-- Migration 461: concept_ledger — Retrieval Plane Elevation W1 Lane L1a (W-24, plan §9.6-1)
-- Created: 2026-07-20
--
-- Numbering note: highest numbered file across BOTH migration dirs combined is 460
-- (platform/migrations/460_kala_gochara_windows.sql, D-5 Lane G-4). 461 is the next
-- free number per platform/supabase/migrations/README.md's guidance.
--
-- Context: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md / RETRIEVAL_PLANE_ELEVATION_PLAN
-- §9.6 "Concept Spine" doctrine (W-24). This is the SINGLE WRITABLE ledger the doctrine
-- requires: "inventory truth is EXTRACTED (harvest pipeline, W-25/W1b) or GENERATED
-- (this table + its projections), never hand-authored." One row per data-plane CONCEPT —
-- a chart_facts fact_category, a bodha/kala/phala/mimamsa signal-type-class, or a service
-- endpoint (sidecar router route).
--
-- Scope of THIS migration (W1 lane L1a): schema only. The table starts and stays EMPTY
-- after this migration applies — population is W-25's harvest-pipeline job (R-1.5), a
-- LATER wave. No backfill, no seed rows here.
--
-- lifecycle_state enum: mirrors the plan's W-20 three-way SERVED / NAVIGABLE /
-- PLANNER-KNOWN doctrine, widened to a practical state machine for the ledger itself:
--   DISCOVERED       — harvested by an extractor, not yet adjudicated
--   SERVED           — reachable via a live registry capability (serving_capability_uri set)
--   PLANNER_KNOWN     — referenced by a Vidhi floor/primitive but not directly served
--   INTERNAL_BY_DESIGN — deliberately unserved (e.g. calibration_context_only, F-R7)
--   RETIRED           — dead-superseded, disposition recorded in disposition_rationale
--   DARK              — exists in the data plane, not yet wired to any serving path
--
-- owning_asset_id is a SOFT reference to asset_registry.asset_id — deliberately NOT an
-- FK. Fact-category and signal-class concepts map cleanly to one asset_registry row, but
-- service_endpoint concepts (sidecar router routes, W-22) often have no asset_registry
-- row of their own. Enforcing an FK here would either reject legitimate service-endpoint
-- rows or require inventing asset_registry rows for services that aren't build assets —
-- both wrong. Referential integrity for the populated case is a W-25/harvest-pipeline
-- adjudication concern, not a schema constraint.
--
-- serving_capability_uri is similarly unconstrained free text (the marsys:// URI format
-- used by the TS retrieval registry, platform/src/lib/retrieval/registry/types.ts
-- CapabilityUri) — the registry itself lives in TypeScript, not the DB, so no FK is
-- possible here.
--
-- Idempotency: per §N.4 "surgical migrations only" — CREATE TABLE IF NOT EXISTS,
-- CREATE INDEX IF NOT EXISTS throughout. Safe to re-run.

BEGIN;

CREATE TABLE IF NOT EXISTS concept_ledger (
  concept_id             text PRIMARY KEY,
  concept_kind            text NOT NULL CHECK (concept_kind IN ('fact_category', 'signal_class', 'service_endpoint')),
  source_layer            text NOT NULL CHECK (source_layer IN ('L0', 'L1', 'L2', 'L3', 'L4', 'L5')),
  owning_asset_id          text,
  lifecycle_state          text NOT NULL CHECK (lifecycle_state IN (
                             'DISCOVERED', 'SERVED', 'PLANNER_KNOWN', 'INTERNAL_BY_DESIGN', 'RETIRED', 'DARK'
                           )),
  disposition_rationale    text,
  serving_capability_uri   text,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_concept_ledger_kind ON concept_ledger(concept_kind);
CREATE INDEX IF NOT EXISTS idx_concept_ledger_layer ON concept_ledger(source_layer);
CREATE INDEX IF NOT EXISTS idx_concept_ledger_lifecycle ON concept_ledger(lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_concept_ledger_owning_asset ON concept_ledger(owning_asset_id);

COMMENT ON TABLE concept_ledger IS
  'W-24 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-1, Concept Spine doctrine): the single '
  'writable inventory-truth ledger for data-plane concepts (fact categories, signal '
  'classes, service endpoints). All other concept surfaces (census JSON, docs resources, '
  'CI reports) are GENERATED projections of this table — never hand-authored '
  'independently. Starts empty; populated by the W-25 harvest pipeline (later wave).';

COMMIT;

-- DOWN:
-- BEGIN;
-- DROP TABLE IF EXISTS concept_ledger;
-- COMMIT;
