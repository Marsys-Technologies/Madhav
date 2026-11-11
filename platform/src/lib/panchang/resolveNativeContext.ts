import 'server-only'

import { authorizeChartAccess, type Principal } from '@/lib/auth/authorizeChartAccess'
import { withTransaction } from '@/lib/db/client'
import { resolveAyanamshaArg, STORED_AYANAMSHA_IDS } from '@/lib/retrieval/chart_facts_helpers'
import {
  resolveChartServedGeneration,
  resolvedRowsBuildId,
} from '@/lib/retrieval/registry/generation/served_generation'
import type { NativeContext } from './sidecar_mapper'

const UNAVAILABLE = {
  native_context: null,
  native_context_error: 'Chart overlay unavailable',
} as const

interface StoredNativeContext extends NativeContext {
  ayanamsha_id: string
  fact_ids: {
    birth_nakshatra_id: string
    birth_nakshatra_name: string
    moon_sign_id: string
    moon_sign_name: string
  }
}

interface ChartRow {
  id: string
  name: string | null
  ayanamsa: string | null
}

interface FactRow {
  chart_id: string
  ayanamsha_id: string
  build_id: string
  fact_id: string
  fact_category: string
  fact_subject: string
  fact_key: string
  fact_value_num: number | null
  fact_value_text: string | null
}

function singleStoredFrame(value: unknown): string | null {
  const frame = resolveAyanamshaArg(value)
  return frame.ok && frame.source === 'explicit' && STORED_AYANAMSHA_IDS.includes(frame.ayanamsha_id)
    ? frame.ayanamsha_id
    : null
}

function isStoredIndex(value: unknown, max: number): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 1 && value <= max
}

/**
 * The caller must resolve the principal from authenticated server context.
 * Chart permission and the stored generation are read afresh on every call.
 */
export async function resolveNativeContext({
  principal,
  chartId,
  requestedFrame,
}: {
  principal: Principal
  chartId: string
  requestedFrame?: unknown
}): Promise<typeof UNAVAILABLE | { native_context: StoredNativeContext; native_context_error: null }> {
  try {
    return await withTransaction(async (db) => {
      // Keep chart settings, producer receipts and facts in the same snapshot.
      await db.query('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
      const permission = await authorizeChartAccess({ principal, chartId, db })
      if (permission === 'deny') return UNAVAILABLE

      const { rows: [chart] } = await db.query<ChartRow>(
        'SELECT id, name, ayanamsa FROM charts WHERE id = $1',
        [chartId],
      )
      if (!chart || chart.id !== chartId.toLowerCase()) return UNAVAILABLE

      // An omitted frame can use a single stored chart selection. A comma-separated
      // selection of multiple frames does not designate a primary.
      const frame = singleStoredFrame(requestedFrame === undefined ? chart.ayanamsa : requestedFrame)
      if (!frame) return UNAVAILABLE

      // Resolve chart-wide receipts so another co-writer can disqualify a shared
      // build. Use each producer's own rows build when selecting its keys.
      const generation = await resolveChartServedGeneration(chart.id, null, (sql, params) => db.query(sql, params))
      const panchangaBuild = resolvedRowsBuildId(generation, 'ga_panchanga')
      const positionsBuild = resolvedRowsBuildId(generation, 'ga_positions')
      if (!panchangaBuild || !positionsBuild
        || !generation.served_build_ids.includes(panchangaBuild)
        || !generation.served_build_ids.includes(positionsBuild)) return UNAVAILABLE

      const { rows } = await db.query<FactRow>(
        `SELECT chart_id, ayanamsha_id, build_id, fact_id, fact_category, fact_subject,
                fact_key, fact_value_num, fact_value_text
           FROM chart_facts
          WHERE chart_id = $1 AND ayanamsha_id = $2
            AND ((build_id = $3 AND fact_category = 'panchanga_nakshatra_moon'
                  AND fact_subject = 'NAKSHATRA_MOON_BIRTH' AND fact_key IN ('number', 'name'))
              OR (build_id = $4 AND fact_subject = 'MOON'
                  AND ((fact_category = 'graha_position' AND fact_key = 'sign')
                    OR (fact_category = 'graha_sign_attributes' AND fact_key = 'sign_num'))))
          ORDER BY fact_category, fact_subject, fact_key, fact_id`,
        [chart.id, frame, panchangaBuild, positionsBuild],
      )
      if (rows.length !== 4
        || rows.some((row) => row.chart_id !== chart.id || row.ayanamsha_id !== frame || !row.fact_id.trim())
        || new Set(rows.map((row) => row.fact_id)).size !== 4) return UNAVAILABLE

      const nakshatraRows = rows.filter((row) => row.build_id === panchangaBuild
        && row.fact_category === 'panchanga_nakshatra_moon' && row.fact_subject === 'NAKSHATRA_MOON_BIRTH')
      const moonRows = rows.filter((row) => row.build_id === positionsBuild && row.fact_subject === 'MOON')
      const nakshatraId = nakshatraRows.find((row) => row.fact_key === 'number')
      const nakshatraName = nakshatraRows.find((row) => row.fact_key === 'name')
      const moonSignId = moonRows.find((row) => row.fact_category === 'graha_sign_attributes' && row.fact_key === 'sign_num')
      const moonSignName = moonRows.find((row) => row.fact_category === 'graha_position' && row.fact_key === 'sign')

      if (!nakshatraId || !isStoredIndex(nakshatraId.fact_value_num, 27)
        || !moonSignId || !isStoredIndex(moonSignId.fact_value_num, 12)
        || !nakshatraName?.fact_value_text?.trim() || !moonSignName?.fact_value_text?.trim()) return UNAVAILABLE

      return {
        native_context: {
          chart_id: chart.id,
          native_name: chart.name ?? '',
          ayanamsha_id: frame,
          birth_nakshatra_id: nakshatraId.fact_value_num,
          birth_nakshatra_name: nakshatraName.fact_value_text,
          moon_sign_id: moonSignId.fact_value_num,
          moon_sign_name: moonSignName.fact_value_text,
          active_dasha_lord: null,
          fact_ids: {
            birth_nakshatra_id: nakshatraId.fact_id,
            birth_nakshatra_name: nakshatraName.fact_id,
            moon_sign_id: moonSignId.fact_id,
            moon_sign_name: moonSignName.fact_id,
          },
        },
        native_context_error: null,
      }
    })
  } catch {
    return UNAVAILABLE
  }
}
