/**
 * chart_facts_ingester.ts — Shared idempotent INSERT helper for chart_facts
 *
 * v3.3-S1 MCPT Depth Backfill session
 * Pattern: ON CONFLICT (fact_id) DO UPDATE — re-runs are always safe.
 *
 * Matches the schema in platform/migrations/014_chart_facts.sql:
 *   id, fact_id (UNIQUE), category, divisional_chart, value_text,
 *   value_number, value_json, source_section, build_id, provenance, is_stale, created_at
 */

import { Pool, PoolClient } from 'pg'

export interface ChartFactRow {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
  build_id: string
  provenance: {
    source_uri: string
    source_version: string
    source_canonical_id: string
    extracted_at: string
    extraction_method: string
  }
}

export interface BuildManifestRow {
  build_id: string
  triggered_by: string
  registry_fingerprint: string
  pipeline_image_uri: string
  embedding_model: string
  embedding_dim: number
  chunk_count: number
  embedding_count: number
  status: 'staging' | 'live' | 'rolled_back' | 'failed'
  manifest_uri: string
  notes?: string
}

/**
 * Upsert a batch of chart_fact rows.
 * Uses ON CONFLICT (fact_id) DO UPDATE so re-runs are idempotent.
 */
export async function upsertChartFacts(
  client: PoolClient | Pool,
  rows: ChartFactRow[]
): Promise<number> {
  if (rows.length === 0) return 0

  let inserted = 0
  for (const row of rows) {
    await client.query(
      `INSERT INTO chart_facts
         (fact_id, category, divisional_chart, value_text, value_number, value_json,
          source_section, build_id, provenance, is_stale)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false)
       ON CONFLICT (fact_id) DO UPDATE SET
         value_text      = EXCLUDED.value_text,
         value_number    = EXCLUDED.value_number,
         value_json      = EXCLUDED.value_json,
         source_section  = EXCLUDED.source_section,
         build_id        = EXCLUDED.build_id,
         provenance      = EXCLUDED.provenance,
         is_stale        = false`,
      [
        row.fact_id,
        row.category,
        row.divisional_chart,
        row.value_text,
        row.value_number,
        row.value_json !== null ? JSON.stringify(row.value_json) : null,
        row.source_section,
        row.build_id,
        JSON.stringify(row.provenance),
      ]
    )
    inserted++
  }
  return inserted
}

/**
 * Insert a build_manifests row for audit trail.
 * Per v1.3 carry-forward item — do NOT skip this step.
 * Uses ON CONFLICT DO NOTHING so partial re-runs don't fail.
 */
export async function insertBuildManifest(
  client: PoolClient | Pool,
  row: BuildManifestRow
): Promise<void> {
  await client.query(
    `INSERT INTO build_manifests
       (build_id, triggered_by, registry_fingerprint, pipeline_image_uri,
        embedding_model, embedding_dim, chunk_count, embedding_count,
        status, manifest_uri, notes)
     VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
     ON CONFLICT (build_id) DO NOTHING`,
    [
      row.build_id,
      row.triggered_by,
      row.registry_fingerprint,
      row.pipeline_image_uri,
      row.embedding_model,
      row.embedding_dim,
      row.chunk_count,
      row.embedding_count,
      row.status,
      row.manifest_uri,
      row.notes ?? null,
    ]
  )
}

/**
 * Create a Pool from DATABASE_URL env var (with dotenv fallback).
 */
export function makePool(): Pool {
  const url = process.env.DATABASE_URL
  if (!url) {
    throw new Error(
      'DATABASE_URL not set. Ensure Cloud SQL Auth Proxy is running and .env.local is loaded.'
    )
  }
  return new Pool({ connectionString: url, max: 5 })
}
