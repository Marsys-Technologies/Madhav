/**
 * l1_context_fetcher.ts — BA-P2 L1 context loader for composite ranking.
 * ========================================================================
 * Fetches (per chart, per ayanamsha):
 *   1. Graha shadbala_total + D1 dignity + D1 house occupancy from chart_facts
 *   2. Current Mahadasha + Antardasha lord from chart_dashas
 *
 * Two DB queries per cache miss; results cached with COMPOSITE_CACHE_TTL_MS.
 * chart_dashas is the authoritative source for timing (kala bypass — L3 fills P5A).
 *
 * MUST NOT: write to bodha_* tables or call any L2+ handler.
 */

import { query } from '@/lib/db/client'
import type { L1ChartContext, GrahaStrength } from './composite_ranker'
import { COMPOSITE_CACHE_TTL_MS } from './priors_config'

// Ranking-layer cache (separate from 60s retrieval cache — needs 30d TTL)
const _rankingCache = new Map<string, { data: unknown; expiresAt: number }>()

function rankingCacheKey(chart_id: string, ayanamsha_id: string, as_of_date: string): string {
  return `l1ctx::${chart_id}::${ayanamsha_id}::${as_of_date}`
}
function rankingCacheGet(key: string): unknown {
  const e = _rankingCache.get(key)
  if (!e || Date.now() > e.expiresAt) { _rankingCache.delete(key); return undefined }
  return e.data
}
function rankingCacheSet(key: string, data: unknown, ttl_ms = COMPOSITE_CACHE_TTL_MS) {
  // Evict stale entries if cache grows large
  if (_rankingCache.size >= 200) {
    const now = Date.now()
    for (const [k, v] of _rankingCache) { if (v.expiresAt < now) _rankingCache.delete(k) }
  }
  _rankingCache.set(key, { data, expiresAt: Date.now() + ttl_ms })
}

// Standard graha codes in the L1 chart_facts data
const GRAHA_CODES = ['SU','MO','MA','ME','JU','VE','SA','RA','KE'] as const

/**
 * Fetch L1 context for composite ranking.
 * @param chart_id - chart UUID
 * @param ayanamsha_id - ayanamsha filter (default: lahiri_chitrapaksha)
 * @param as_of_date - ISO date string to resolve current dasha period (default: today)
 */
export async function fetchL1Context(
  chart_id: string,
  ayanamsha_id: string,
  as_of_date: string
): Promise<L1ChartContext> {
  const ck = rankingCacheKey(chart_id, ayanamsha_id, as_of_date)
  const cached = rankingCacheGet(ck)
  if (cached !== undefined) return cached as L1ChartContext

  // ── Query 1: graha strength + dignity + house from chart_facts ────────────
  // Uses chart_facts (the L1 canonical source for all graha data).
  // We need three fact_categories:
  //   graha_shadbala_total   → fact_value_numeric = total shadbala in rupas
  //   graha_sign_attributes  → fact_value_text = dignity classification
  //   graha_in_house         → derived from sign/house mapping (or graha position)
  //
  // For D1 dignity: query graha_dignity_per_varga with varga='D1'
  // For shadbala: query graha_shadbala_total with fact_key like '%.total'
  // For house: query graha_sthana_per_varga fact_category or use chart_facts

  let strengthRows: Array<Record<string, unknown>> = []
  let dignityRows: Array<Record<string, unknown>> = []
  let houseRows: Array<Record<string, unknown>> = []

  try {
    // Shadbala total — one row per graha (fact_key = '{graha}.shadbala_total')
    const shadbalaResult = await query(
      `SELECT fact_key, fact_value_numeric
       FROM chart_facts
       WHERE chart_id = $1
         AND ayanamsha_id = $2
         AND fact_category = 'graha_shadbala_total'
       LIMIT 20`,
      [chart_id, ayanamsha_id]
    )
    strengthRows = shadbalaResult.rows

    // Dignity per D1 — one row per graha
    const dignityResult = await query(
      `SELECT fact_key, fact_value_text
       FROM chart_facts
       WHERE chart_id = $1
         AND ayanamsha_id = $2
         AND fact_category = 'graha_dignity_per_varga'
         AND fact_key LIKE '%.D1.%'
       LIMIT 20`,
      [chart_id, ayanamsha_id]
    )
    dignityRows = dignityResult.rows

    // House occupancy D1 — graha_sthana_bhava or graha position fact
    const houseResult = await query(
      `SELECT fact_key, fact_value_numeric
       FROM chart_facts
       WHERE chart_id = $1
         AND ayanamsha_id = $2
         AND fact_category IN ('graha_sthana_per_varga', 'graha_bhava_per_varga')
         AND fact_key LIKE '%.D1.%'
       LIMIT 20`,
      [chart_id, ayanamsha_id]
    )
    houseRows = houseResult.rows
  } catch {
    // Non-fatal: if L1 data unavailable, return empty context (composite will use fallbacks)
  }

  // Parse shadbala (expect fact_key = 'SU.shadbala_total' or similar)
  const shadbalaMap: Record<string, number> = {}
  for (const row of strengthRows) {
    const key = String(row['fact_key'] ?? '')
    const graha = key.split('.')[0]?.toUpperCase() ?? ''
    const val = Number(row['fact_value_numeric'] ?? 0)
    if (graha && val > 0) shadbalaMap[graha] = val
  }

  // Parse dignity D1 (expect fact_key = 'SU.D1.dignity' or 'SU.D1')
  const dignityMap: Record<string, string> = {}
  for (const row of dignityRows) {
    const key = String(row['fact_key'] ?? '')
    const parts = key.split('.')
    const graha = parts[0]?.toUpperCase() ?? ''
    const val = String(row['fact_value_text'] ?? '').toLowerCase()
    if (graha && val) dignityMap[graha] = val
  }

  // Parse house (expect fact_key = 'SU.D1.bhava' or 'SU.D1')
  const houseMap: Record<string, number> = {}
  for (const row of houseRows) {
    const key = String(row['fact_key'] ?? '')
    const parts = key.split('.')
    const graha = parts[0]?.toUpperCase() ?? ''
    const val = Number(row['fact_value_numeric'] ?? 0)
    if (graha && val >= 1 && val <= 12) houseMap[graha] = val
  }

  // Build graha_map
  const graha_map: Record<string, GrahaStrength> = {}
  for (const g of GRAHA_CODES) {
    graha_map[g] = {
      graha:          g,
      shadbala_total: shadbalaMap[g] ?? 300,  // 300 = neutral fallback (average ≈ 450 rupa)
      dignity:        dignityMap[g] ?? null,
      house:          houseMap[g] ?? null,
    }
  }

  // ── Query 2: current dasha lords from chart_dashas ────────────────────────
  // Find the active Mahadasha + Antardasha as of as_of_date.
  // chart_dashas has columns: chart_id, ayanamsha_id, level (1=MD,2=AD,3=PD,...),
  //   dasha_lord, start_date, end_date
  let current_md_lord: string | null = null
  let current_ad_lord: string | null = null

  try {
    const dashaResult = await query(
      `SELECT level, dasha_lord
       FROM chart_dashas
       WHERE chart_id = $1
         AND ayanamsha_id = $2
         AND level IN (1, 2)
         AND start_date <= $3::date
         AND end_date > $3::date
       ORDER BY level ASC
       LIMIT 2`,
      [chart_id, ayanamsha_id, as_of_date]
    )
    for (const row of dashaResult.rows) {
      const lvl = Number(row['level'])
      const lord = String(row['dasha_lord'] ?? '')
      if (lvl === 1) current_md_lord = lord.toUpperCase()
      if (lvl === 2) current_ad_lord = lord.toUpperCase()
    }
  } catch {
    // Non-fatal: dasha lookup failure means temporal_activation stays at 1.0
  }

  const ctx: L1ChartContext = {
    graha_map, current_md_lord, current_ad_lord, as_of_date,
  }

  rankingCacheSet(ck, ctx)
  return ctx
}
