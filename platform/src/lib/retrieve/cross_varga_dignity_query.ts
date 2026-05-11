/**
 * MARSYS-JIS — Tool: cross_varga_dignity_query
 *
 * VARGA-ETL-FULL-S1-CPA D8 — Surfaces the §3.15 CSI cross-divisional dignity
 * ledger as a structured per-planet result (D1 / D9 / D10 sign + dignity +
 * vargottama). The CSI rows in chart_facts (`fact_id LIKE 'CSI.%'`) already
 * carry d1_sign / d9_sign / d10_sign / d10_house and (selectively)
 * d{1,9,10}_dignity in value_json — for cells that don't, dignity is derived
 * from the classical exaltation/own-sign/debilitation lookup table.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'cross_varga_dignity_query'
const TOOL_VERSION = '1.0.0'

export type Dignity =
  | 'exalted'
  | 'debilitated'
  | 'own_sign'
  | 'mooltrikona'
  | 'neutral'
  | 'shadow_node'

export interface CrossVargaDignityInput {
  /** Filter by planet name (case-insensitive). Empty/undefined = all 9 planets. */
  planets?: string[]
}

export interface CrossVargaDignityResult {
  planet: string
  d1_sign: string | null
  d1_dignity: Dignity | null
  d9_sign: string | null
  d9_dignity: Dignity | null
  d10_sign: string | null
  d10_house: number | null
  d10_dignity: Dignity | null
  vargottama: boolean
  fact_ids: string[]
}

// Classical Jyotish dignity lookup (sidereal). Rahu/Ketu treated as shadow nodes.
// Mooltrikona is shown only when distinct from own_sign per Parashara — Sun Leo
// 0–20° is the canonical case but coarse sign-only lookup treats it as own_sign.
const DIGNITY_TABLE: Record<string, { exalted?: string; debilitated?: string; own?: string[] }> = {
  sun:     { exalted: 'Aries',      debilitated: 'Libra',     own: ['Leo'] },
  moon:    { exalted: 'Taurus',     debilitated: 'Scorpio',   own: ['Cancer'] },
  mars:    { exalted: 'Capricorn',  debilitated: 'Cancer',    own: ['Aries', 'Scorpio'] },
  mercury: { exalted: 'Virgo',      debilitated: 'Pisces',    own: ['Gemini', 'Virgo'] },
  jupiter: { exalted: 'Cancer',     debilitated: 'Capricorn', own: ['Sagittarius', 'Pisces'] },
  venus:   { exalted: 'Pisces',     debilitated: 'Virgo',     own: ['Taurus', 'Libra'] },
  saturn:  { exalted: 'Libra',      debilitated: 'Aries',     own: ['Capricorn', 'Aquarius'] },
  rahu:    {},
  ketu:    {},
}

function normalisePlanet(name: string): string {
  return name.trim().toLowerCase()
}

function deriveDignity(planet: string, sign: string | null | undefined): Dignity | null {
  if (!sign) return null
  const key = normalisePlanet(planet)
  if (key === 'rahu' || key === 'ketu') return 'shadow_node'
  const entry = DIGNITY_TABLE[key]
  if (!entry) return null
  const s = sign.trim()
  if (entry.exalted === s) return 'exalted'
  if (entry.debilitated === s) return 'debilitated'
  if (entry.own?.includes(s)) return 'own_sign'
  return 'neutral'
}

function dignityFromValueJson(
  raw: unknown,
  field: 'd1_dignity' | 'd9_dignity' | 'd10_dignity'
): Dignity | null {
  if (!raw || typeof raw !== 'object') return null
  const v = (raw as Record<string, unknown>)[field]
  if (typeof v !== 'string') return null
  // Map known YAML strings to canonical Dignity values.
  const lower = v.toLowerCase()
  if (lower.includes('exalt')) return 'exalted'
  if (lower.includes('debil')) return 'debilitated'
  if (lower.includes('own') || lower === 'own_sign' || lower === 'own_sign_dusthana') return 'own_sign'
  if (lower.includes('mooltrikona') || lower === 'mt') return 'mooltrikona'
  if (lower === 'neutral' || lower === 'angular' || lower === 'trine') return 'neutral'
  return null
}

interface CsiRow {
  fact_id: string
  divisional_chart: string
  value_json: Record<string, unknown> | null
}

interface DivRow {
  fact_id: string
  divisional_chart: string
  value_text: string | null
  value_json: Record<string, unknown> | null
}

const PLANETS_CANONICAL = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

function planetFromFactId(factId: string): string | null {
  // CSI.SATURN, D9.SATURN, D10.SATURN → Saturn
  const parts = factId.split('.')
  if (parts.length < 2) return null
  const raw = parts[parts.length - 1].toLowerCase()
  for (const p of PLANETS_CANONICAL) {
    if (p.toLowerCase() === raw) return p
  }
  return null
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'FORENSIC',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as CrossVargaDignityInput
  const planetFilter = (input.planets ?? []).map(normalisePlanet).filter(Boolean)

  // Pull §3.15 CSI rows + D9.* / D10.* per-planet rows (for fact_id provenance and dignity backfill).
  const sql = `
    SELECT fact_id, divisional_chart, value_text, value_json
    FROM chart_facts
    WHERE is_stale = false
      AND (
        fact_id LIKE 'CSI.%'
        OR fact_id LIKE 'D9.%'
        OR fact_id LIKE 'D10.%'
      )
    ORDER BY fact_id
  `.trim()

  const { rows } = await getStorageClient().query<DivRow>(sql, [])

  // Bucket by planet name extracted from fact_id.
  const byPlanet = new Map<
    string,
    { csi: CsiRow | null; d9: DivRow | null; d10: DivRow | null; factIds: string[] }
  >()

  for (const row of rows) {
    const planet = planetFromFactId(row.fact_id)
    if (!planet) continue
    const bucket = byPlanet.get(planet) ?? { csi: null, d9: null, d10: null, factIds: [] }
    bucket.factIds.push(row.fact_id)
    if (row.fact_id === `CSI.${planet.toUpperCase()}`) bucket.csi = row
    else if (row.fact_id === `D9.${planet.toUpperCase()}`) bucket.d9 = row
    else if (row.fact_id === `D10.${planet.toUpperCase()}`) bucket.d10 = row
    byPlanet.set(planet, bucket)
  }

  // Build results in canonical planet order.
  const results: CrossVargaDignityResult[] = []
  for (const planet of PLANETS_CANONICAL) {
    if (planetFilter.length > 0 && !planetFilter.includes(normalisePlanet(planet))) continue
    const bucket = byPlanet.get(planet)
    if (!bucket || !bucket.csi) {
      // Skip if there's no CSI row for this planet — represents missing v1.1 data.
      continue
    }
    const csi = bucket.csi.value_json ?? {}
    const d1Sign = (csi.d1_sign as string | undefined) ?? null
    const d9Sign = (csi.d9_sign as string | undefined) ?? null
    const d10Sign = (csi.d10_sign as string | undefined) ?? null
    const d10HouseRaw = csi.d10_house
    const d10House =
      typeof d10HouseRaw === 'number'
        ? d10HouseRaw
        : typeof d10HouseRaw === 'string'
          ? Number(d10HouseRaw)
          : null
    const vargottama = csi.vargottama === true

    results.push({
      planet,
      d1_sign: d1Sign,
      d1_dignity: dignityFromValueJson(csi, 'd1_dignity') ?? deriveDignity(planet, d1Sign),
      d9_sign: d9Sign,
      d9_dignity: dignityFromValueJson(csi, 'd9_dignity') ?? deriveDignity(planet, d9Sign),
      d10_sign: d10Sign,
      d10_house: Number.isFinite(d10House as number) ? (d10House as number) : null,
      d10_dignity: dignityFromValueJson(csi, 'd10_dignity') ?? deriveDignity(planet, d10Sign),
      vargottama,
      fact_ids: bucket.factIds,
    })
  }

  const bundleResults: ToolBundleResult[] = results.map((r) => ({
    content: JSON.stringify(r),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.95,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map((r) => `${r.planet}:${r.d1_sign}|${r.d9_sign}|${r.d10_sign}`).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      planets: input.planets ?? [],
    },
    results: bundleResults,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: bundleResults.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: bundleResults.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(bundleResults).length / 4),
    data_asset_id: 'FORENSIC',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
    raw_result_count: rows.length,
    kept_result_count: bundleResults.length,
    dropped_items: [],
    kept_items: bundleResults.slice(0, 200).map((r) => ({
      item_id: r.signal_id ?? r.source_canonical_id,
      score: r.confidence ?? null,
      contribution_tokens: null,
    })),
    tool_input_payload: bundle.invocation_params,
    error_class: 'OK',
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Returns the §3.15 CSI cross-divisional dignity ledger — per-planet D1/D9/D10 dignity states and vargottama status. ' +
    'Use for any query about cross-varga strength, dignity transitions, or "how does X planet behave across charts". ' +
    'Priority-1 for any query mentioning "navamsha comparison", "strength across charts", "vargottama", or "three-state". ' +
    'Always schedule alongside divisional_query for D9 and D10.',
  retrieve,
}
