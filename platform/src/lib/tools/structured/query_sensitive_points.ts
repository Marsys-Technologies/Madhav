/**
 * query_sensitive_points.ts
 *
 * BRAHMA GA-1-6 — Retrieval tool for ganita.sensitive_points
 *
 * Queries chart_facts for sensitive-point categories:
 *   upagraha      — Gulika, Mandi, Dhuma, Vyatipata, etc.
 *   special_lagna — Hora Lagna, Ghati Lagna, Bhava Lagna, etc.
 *   saham         — 36 Tajika sahams (Fortune, Marriage, Disease, etc.)
 *   arudha        — AL, UL (Upapada), Darapada (A7), A2–A12
 *
 * B.11 compliance: use this as the L1 retrieval step before L2.5 synthesis.
 *
 * FORENSIC source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §11–§13
 * JH authority:    JHORA_TRANSCRIPTION_v8_0_SOURCE.md §2
 */

import { tool } from 'ai'
import { z } from 'zod'
import { query } from '@/lib/db/client'

export const query_sensitive_points = tool({
  description:
    'Query L1 sensitive points from the FORENSIC chart fact store. ' +
    'Covers: upagrahas (Gulika, Mandi, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, ' +
    'Yamaghantaka, Ardhaprahara), special lagnas (Hora, Ghati, Bhava, Vighati, Varnada, ' +
    'Shree, Pranapada, Indu, Bhrigu Bindu), 36 Tajika sahams (Punya, Vivaha, Karma, ' +
    'Roga, Mrityu, etc.), and arudha padas (AL, UL/Upapada, Darapada/A7, A2, A6, A10, A11). ' +
    'All values are JH-authoritative (v8.0 corrections applied — v6.0 errors in Hora Lagna, ' +
    'Ghati Lagna, Roga Saham, Vivaha Saham are corrected). ' +
    'Use when the user asks about: Gulika position, Mandi placement, sahams, arudha padas, ' +
    'special lagnas, Upapada Lagna spouse significator, Darapada, Fortune point. ' +
    'Returns fact rows with fact_id, category, sign, house, nakshatra, and source_section.',
  inputSchema: z.object({
    category: z
      .enum(['upagraha', 'special_lagna', 'saham', 'arudha', 'all'])
      .optional()
      .default('all')
      .describe(
        'Filter by category: upagraha (Gulika, Mandi, Dhuma, etc.), ' +
        'special_lagna (Hora, Ghati, Bhrigu Bindu, etc.), ' +
        'saham (Tajika Fortune, Marriage, Disease points), ' +
        'arudha (AL, UL, A7/Darapada, A2–A11), or all.'
      ),
    point_name: z
      .string()
      .optional()
      .describe(
        'Filter by point name substring (case-insensitive). ' +
        'Examples: "Gulika", "Hora", "Punya", "Upapada", "AL", "UL", "Vivaha".'
      ),
    sign: z
      .string()
      .optional()
      .describe('Filter by zodiac sign (e.g. "Gemini", "Cancer", "Capricorn").'),
    house: z
      .number()
      .int()
      .min(1)
      .max(12)
      .optional()
      .describe('Filter by house number (1–12, Aries Lagna whole-sign system).'),
    divisional_chart: z
      .string()
      .optional()
      .describe('Filter by divisional chart (D1, D9, D10). Defaults to all.'),
    limit: z
      .number()
      .int()
      .min(1)
      .max(100)
      .default(50)
      .describe('Maximum rows to return (default 50).'),
  }),
  execute: async ({ category, point_name, sign, house, divisional_chart, limit }) => {
    try {
      const conditions: string[] = []
      const params: (string | number)[] = []
      let idx = 1

      // Category filter
      if (category && category !== 'all') {
        conditions.push(`category = $${idx++}`)
        params.push(category)
      } else {
        // Default to all sensitive-point categories
        conditions.push(`category = ANY($${idx++})`)
        params.push(['upagraha', 'special_lagna', 'saham', 'arudha'] as unknown as string)
      }

      // Point name substring filter (on value_text or value_json->>'name')
      if (point_name) {
        conditions.push(
          `(value_text ILIKE $${idx} OR value_json->>'name' ILIKE $${idx})`
        )
        params.push(`%${point_name}%`)
        idx++
      }

      // Sign filter (via value_json)
      if (sign) {
        conditions.push(`value_json->>'sign' ILIKE $${idx++}`)
        params.push(`%${sign}%`)
      }

      // House filter (via value_json)
      if (house !== undefined) {
        conditions.push(`(value_json->>'house')::int = $${idx++}`)
        params.push(house)
      }

      // Divisional chart filter
      if (divisional_chart) {
        conditions.push(`divisional_chart = $${idx++}`)
        params.push(divisional_chart)
      }

      const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : ''

      const sql = `
        SELECT
          fact_id,
          category,
          divisional_chart,
          value_text,
          value_json->>'name'       AS point_name,
          value_json->>'sign'       AS sign,
          value_json->>'house'      AS house,
          value_json->>'nakshatra'  AS nakshatra,
          value_json->>'type'       AS upg_type,
          value_json->>'meaning'    AS saham_meaning,
          value_json->>'note'       AS correction_note,
          source_section
        FROM chart_facts
        ${where}
        ORDER BY category ASC, fact_id ASC
        LIMIT $${idx}
      `
      params.push(limit)

      const { rows } = await query(sql, params)

      // Format into a structured summary
      const byCategory: Record<string, typeof rows> = {}
      for (const row of rows) {
        const cat = row.category as string
        if (!byCategory[cat]) byCategory[cat] = []
        byCategory[cat].push(row)
      }

      return {
        count: rows.length,
        source: 'FORENSIC_ASTROLOGICAL_DATA_v8_0.md §11–§13 (JH authoritative)',
        by_category: {
          upagraha: byCategory['upagraha'] ?? [],
          special_lagna: byCategory['special_lagna'] ?? [],
          saham: byCategory['saham'] ?? [],
          arudha: byCategory['arudha'] ?? [],
        },
        rows,
      }
    } catch (e) {
      return { error: e instanceof Error ? e.message : String(e) }
    }
  },
})
