/**
 * l1_context_fetcher.ts — BA-P2 L1 context loader for composite ranking.
 * ========================================================================
 * Fetches (per chart, per ayanamsha):
 *   1. Graha shadbala_total (rupas) + D1 dignity + D1 house occupancy from chart_facts
 *   2. Current Mahadasha + Antardasha lord from chart_dashas
 *
 * Two DB queries per cache miss; results cached with COMPOSITE_CACHE_TTL_MS.
 *
 * L1 schema (confirmed against live DB 2026-07-03):
 *   graha_shadbala_total:
 *     fact_subject = graha key (SUN/MOON/MAR/MER/JUP/VEN/SAT/RAH_MEAN/KET_MEAN)
 *     fact_key = 'rupa'
 *     fact_value_num = shadbala in rupas (range ~0.4–5.0 for real charts)
 *
 *   graha_dignity_per_varga:
 *     fact_subject = '{VARGA}_{GRAHA}' (e.g. 'D1_SAT', 'D1_SUN')
 *     fact_key = 'dignity_state'
 *     fact_value_text = dignity classification ('exalted'|'own'|'neutral'|'debilitated'|...)
 *     fact_value_jsonb = {varga, house, sign, ayanamsha_id, uncatalogued}
 *
 * MUST NOT: write to bodha_* tables or call any L2+ handler.
 */

import { query } from '@/lib/db/client'
import type { L1ChartContext, GrahaStrength } from './composite_ranker'
import { COMPOSITE_CACHE_TTL_MS } from './priors_config'
import { grahaCodeOf } from '@/lib/retrieval/address_resolver'

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
  if (_rankingCache.size >= 200) {
    const now = Date.now()
    for (const [k, v] of _rankingCache) { if (v.expiresAt < now) _rankingCache.delete(k) }
  }
  _rankingCache.set(key, { data, expiresAt: Date.now() + ttl_ms })
}

// L1 graha key → canonical 2-char code used in graha_map. Derived from the
// graha SSoT (address_resolver.grahaCodeOf) rather than hardcoded literals —
// ADHIṢṬHĀNA Lane A2: the SSoT's own canonical short code's first 2
// characters always yield this file's established 2-char L1 convention.
const L1_GRAHA_TO_CODE: Record<string, string> = Object.fromEntries(
  ['SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN']
    .map(code => [code, grahaCodeOf(code).slice(0, 2)]),
)

/**
 * Fetch L1 context for composite ranking.
 * @param chart_id - chart UUID
 * @param ayanamsha_id - ayanamsha filter
 * @param as_of_date - ISO date string to resolve current dasha period
 */
export async function fetchL1Context(
  chart_id: string,
  ayanamsha_id: string,
  as_of_date: string
): Promise<L1ChartContext> {
  const ck = rankingCacheKey(chart_id, ayanamsha_id, as_of_date)
  const cached = rankingCacheGet(ck)
  if (cached !== undefined) return cached as L1ChartContext

  // Build empty graha_map as fallback
  const graha_map: Record<string, GrahaStrength> = {}
  for (const code of ['SU','MO','MA','ME','JU','VE','SA','RA','KE']) {
    graha_map[code] = { graha: code, shadbala_total: 2.5, dignity: null, house: null }
  }

  try {
    // ── Query 1: shadbala + D1 dignity + D1 house ────────────────────────────
    // Single query covering both shadbala and D1 dignity facts.
    //   graha_shadbala_total: fact_subject=GRAHA, fact_value_num=rupas
    //   graha_dignity_per_varga: fact_subject='D1_GRAHA', fact_value_text=dignity,
    //                             fact_value_jsonb.house = house number (1-12)
    const l1Result = await query(
      `SELECT fact_category, fact_subject, fact_value_num, fact_value_text, fact_value_jsonb
       FROM chart_facts
       WHERE chart_id = $1
         AND ayanamsha_id = $2
         AND fact_category IN ('graha_shadbala_total', 'graha_dignity_per_varga')
         AND (
           (fact_category = 'graha_shadbala_total')
           OR (fact_category = 'graha_dignity_per_varga' AND fact_subject LIKE 'D1_%')
         )
       LIMIT 100`,
      [chart_id, ayanamsha_id]
    )

    for (const row of l1Result.rows) {
      const cat = String(row['fact_category'] ?? '')
      const subj = String(row['fact_subject'] ?? '')

      if (cat === 'graha_shadbala_total') {
        // fact_subject = 'SAT' | 'SUN' | 'MAR' etc.
        const code = L1_GRAHA_TO_CODE[subj]
        if (code) {
          graha_map[code] ??= { graha: code, shadbala_total: 2.5, dignity: null, house: null }
          graha_map[code].shadbala_total = Number(row['fact_value_num'] ?? 2.5)
        }
      } else if (cat === 'graha_dignity_per_varga') {
        // fact_subject = 'D1_SAT' | 'D1_SUN' etc. — strip 'D1_' prefix
        const l1Key = subj.replace(/^D1_/, '')
        const code = L1_GRAHA_TO_CODE[l1Key]
        if (code) {
          graha_map[code] ??= { graha: code, shadbala_total: 2.5, dignity: null, house: null }
          graha_map[code].dignity = String(row['fact_value_text'] ?? '').toLowerCase() || null
          // House from fact_value_jsonb.house (confirmed schema)
          const jsonb = row['fact_value_jsonb'] as Record<string, unknown> | null
          if (jsonb && typeof jsonb['house'] === 'number') {
            graha_map[code].house = jsonb['house']
          }
        }
      }
    }
  } catch {
    // Non-fatal: if L1 data unavailable, composite will use fallback values
  }

  // ── Query 2: current dasha lords from chart_dashas ──────────────────────────
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
      const lord = String(row['dasha_lord'] ?? '').toUpperCase()
      if (lvl === 1) current_md_lord = L1_GRAHA_TO_CODE[lord] ?? lord
      if (lvl === 2) current_ad_lord = L1_GRAHA_TO_CODE[lord] ?? lord
    }
  } catch {
    // Non-fatal: temporal_activation stays at 1.0
  }

  const ctx: L1ChartContext = { graha_map, current_md_lord, current_ad_lord, as_of_date }
  rankingCacheSet(ck, ctx)
  return ctx
}
