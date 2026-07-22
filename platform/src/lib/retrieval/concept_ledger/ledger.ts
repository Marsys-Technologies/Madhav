/**
 * ledger.ts — concept_ledger typed access layer
 * ================================================================================
 * Retrieval Plane Elevation, W1 Lane L1a (W-24, RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-1,
 * the "Concept Spine" doctrine). concept_ledger (migration 461) is the SINGLE WRITABLE
 * inventory-truth surface for data-plane concepts — a chart_facts fact_category, a
 * bodha/kala/phala/mimamsa signal-type-class, or a service endpoint. Every other
 * concept-inventory surface (census JSON, docs resources, CI reports) is a GENERATED
 * PROJECTION over this table, never a second hand-authored source.
 *
 * Scope of this module (W1): the typed insert/upsert/query access layer only. The
 * table is empty after migration 461 applies — the W-25 harvest pipeline (extractors
 * E1–E4, cross-diff, adjudication queue, a LATER wave / R-1.5) is what populates it.
 * This module is what that pipeline will write through; it does not itself harvest
 * anything.
 */
import { query } from '@/lib/db/client'

// ── Domain types (mirror the migration 461 CHECK constraints exactly) ──────────

export type ConceptKind = 'fact_category' | 'signal_class' | 'service_endpoint'

export type SourceLayer = 'L0' | 'L1' | 'L2' | 'L3' | 'L4' | 'L5'

/**
 * Lifecycle states — the W-20 SERVED / NAVIGABLE / PLANNER-KNOWN three-way doctrine,
 * widened to a practical state machine for the ledger (see migration 461 header for
 * the meaning of each state).
 */
export type LifecycleState =
  | 'DISCOVERED'
  | 'SERVED'
  | 'PLANNER_KNOWN'
  | 'INTERNAL_BY_DESIGN'
  | 'RETIRED'
  | 'DARK'

export interface ConceptLedgerRow {
  concept_id: string
  concept_kind: ConceptKind
  source_layer: SourceLayer
  owning_asset_id: string | null
  lifecycle_state: LifecycleState
  disposition_rationale: string | null
  serving_capability_uri: string | null
  created_at: string
  updated_at: string
}

/** Input shape for insert/upsert — created_at/updated_at are server-assigned. */
export interface ConceptLedgerWriteInput {
  concept_id: string
  concept_kind: ConceptKind
  source_layer: SourceLayer
  owning_asset_id?: string | null
  lifecycle_state: LifecycleState
  disposition_rationale?: string | null
  serving_capability_uri?: string | null
}

export interface ConceptLedgerFilter {
  concept_kind?: ConceptKind
  source_layer?: SourceLayer
  lifecycle_state?: LifecycleState
  owning_asset_id?: string
}

/** One row of the (lifecycle_state × source_layer) aggregate the census generator consumes. */
export interface LifecycleLayerCount {
  lifecycle_state: LifecycleState
  source_layer: SourceLayer
  concept_count: number
}

// ── Writes ───────────────────────────────────────────────────────────────────

/**
 * Insert a new concept row. Throws (unique-violation) if concept_id already exists —
 * use upsertConcept for idempotent harvest-pipeline writes.
 */
export async function insertConcept(input: ConceptLedgerWriteInput): Promise<ConceptLedgerRow> {
  const result = await query<ConceptLedgerRow>(
    `INSERT INTO concept_ledger
       (concept_id, concept_kind, source_layer, owning_asset_id, lifecycle_state,
        disposition_rationale, serving_capability_uri)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     RETURNING *`,
    [
      input.concept_id,
      input.concept_kind,
      input.source_layer,
      input.owning_asset_id ?? null,
      input.lifecycle_state,
      input.disposition_rationale ?? null,
      input.serving_capability_uri ?? null,
    ],
  )
  return result.rows[0]
}

/**
 * Idempotent upsert by concept_id — the primary write path for the (future) harvest
 * pipeline. Re-harvesting an already-known concept updates its declared fields and
 * bumps updated_at; it never silently drops fields the caller didn't pass (each field
 * is written explicitly, not merged).
 */
export async function upsertConcept(input: ConceptLedgerWriteInput): Promise<ConceptLedgerRow> {
  const result = await query<ConceptLedgerRow>(
    `INSERT INTO concept_ledger
       (concept_id, concept_kind, source_layer, owning_asset_id, lifecycle_state,
        disposition_rationale, serving_capability_uri, updated_at)
     VALUES ($1, $2, $3, $4, $5, $6, $7, now())
     ON CONFLICT (concept_id) DO UPDATE SET
       concept_kind            = EXCLUDED.concept_kind,
       source_layer            = EXCLUDED.source_layer,
       owning_asset_id         = EXCLUDED.owning_asset_id,
       lifecycle_state         = EXCLUDED.lifecycle_state,
       disposition_rationale   = EXCLUDED.disposition_rationale,
       serving_capability_uri  = EXCLUDED.serving_capability_uri,
       updated_at              = now()
     RETURNING *`,
    [
      input.concept_id,
      input.concept_kind,
      input.source_layer,
      input.owning_asset_id ?? null,
      input.lifecycle_state,
      input.disposition_rationale ?? null,
      input.serving_capability_uri ?? null,
    ],
  )
  return result.rows[0]
}

/**
 * Bulk convenience wrapper — sequential upserts in a single caller-visible call.
 * Not a multi-row VALUES optimization (v1; the harvest pipeline that will call this
 * at scale is a later wave — see W-25). Returns the count written.
 */
export async function upsertConcepts(inputs: ConceptLedgerWriteInput[]): Promise<number> {
  let written = 0
  for (const input of inputs) {
    await upsertConcept(input)
    written++
  }
  return written
}

// ── Reads ────────────────────────────────────────────────────────────────────

export async function getConcept(concept_id: string): Promise<ConceptLedgerRow | null> {
  const result = await query<ConceptLedgerRow>(
    `SELECT * FROM concept_ledger WHERE concept_id = $1`,
    [concept_id],
  )
  return result.rows[0] ?? null
}

/** Filtered list — every filter field is optional; an empty filter returns all rows. */
export async function listConcepts(filter: ConceptLedgerFilter = {}): Promise<ConceptLedgerRow[]> {
  const clauses: string[] = []
  const params: unknown[] = []

  if (filter.concept_kind !== undefined) {
    params.push(filter.concept_kind)
    clauses.push(`concept_kind = $${params.length}`)
  }
  if (filter.source_layer !== undefined) {
    params.push(filter.source_layer)
    clauses.push(`source_layer = $${params.length}`)
  }
  if (filter.lifecycle_state !== undefined) {
    params.push(filter.lifecycle_state)
    clauses.push(`lifecycle_state = $${params.length}`)
  }
  if (filter.owning_asset_id !== undefined) {
    params.push(filter.owning_asset_id)
    clauses.push(`owning_asset_id = $${params.length}`)
  }

  const where = clauses.length > 0 ? `WHERE ${clauses.join(' AND ')}` : ''
  const result = await query<ConceptLedgerRow>(
    `SELECT * FROM concept_ledger ${where} ORDER BY concept_id`,
    params,
  )
  return result.rows
}

/**
 * The (lifecycle_state × source_layer) count aggregate — what the projection
 * generator (platform/scripts/manifest/generate_concept_projections.ts) consumes to
 * emit concept_census.json. Runs correctly (returns zero rows, no error) against an
 * empty table.
 */
export async function getLifecycleLayerCounts(): Promise<LifecycleLayerCount[]> {
  const result = await query<{ lifecycle_state: LifecycleState; source_layer: SourceLayer; concept_count: string }>(
    `SELECT lifecycle_state, source_layer, count(*)::text AS concept_count
     FROM concept_ledger
     GROUP BY lifecycle_state, source_layer
     ORDER BY lifecycle_state, source_layer`,
  )
  return result.rows.map((row) => ({
    lifecycle_state: row.lifecycle_state,
    source_layer: row.source_layer,
    concept_count: parseInt(row.concept_count, 10),
  }))
}

/** Total row count — cheap existence/health check, correct at zero rows. */
export async function countConcepts(): Promise<number> {
  const result = await query<{ count: string }>(`SELECT count(*)::text AS count FROM concept_ledger`)
  return parseInt(result.rows[0]?.count ?? '0', 10)
}

// ── W3-L8 (RETRIEVAL_PLANE_ELEVATION_PLAN §9.6-3/4, W-26): ledger_version ──────

/**
 * The single monotonic staleness signal for the concept ledger, mirroring the EXACT
 * pattern `provenance_stamp.ts#getLatestChartBuild` already uses for `build_id` (per-chart
 * build_runs staleness) — a comparable value derived from the source-of-truth table's
 * own state, never a separately-invented counter. `build_id` answers "has THIS CHART's
 * data changed"; `ledger_version` answers "has the SERVING CATALOG (which concepts are
 * SERVED/PLANNER_KNOWN/RETIRED/etc, independent of chart_id) changed" — the second axis
 * the W-28 cache key (uri, chart_id, build_id, ledger_version, args, projection, format)
 * needs, because a capability's lifecycle_state can change (e.g. RETIRED) without any
 * chart ever being rebuilt.
 *
 * Derivation: `count || ':' || max(updated_at)` over the whole table — count alone would
 * miss an UPDATE that changes a row's lifecycle_state without adding a row; max(updated_at)
 * alone would miss the (degenerate but possible) case of a delete+insert landing on the
 * exact same timestamp as a prior row. Together they're a cheap, honest fingerprint of
 * "did anything in this ledger change" — not a cryptographic hash, not a claim of global
 * uniqueness, just parity with the coarseness `build_id` already operates at (an opaque
 * per-build identifier, not a content hash either).
 *
 * Returns null when the ledger is empty (migration 461: starts empty, W-25 harvest
 * pipeline populates it in a later wave) — honest null per B.10, never a fabricated
 * version for a ledger that has no rows yet. Every caller (pin resolution, envelope
 * builder) must treat null as "no ledger signal available", exactly as they already
 * treat a null build_id.
 */
export async function getLedgerVersion(): Promise<string | null> {
  const result = await query<{ ledger_version: string | null }>(
    `SELECT CASE WHEN count(*) = 0 THEN NULL
                 ELSE count(*)::text || ':' || extract(epoch FROM max(updated_at))::text
            END AS ledger_version
       FROM concept_ledger`,
  )
  return result.rows[0]?.ledger_version ?? null
}
