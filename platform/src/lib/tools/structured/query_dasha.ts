import { tool } from 'ai'
import { z } from 'zod'
import { query } from '@/lib/db/client'

const CATEGORY_MAP: Record<string, string> = {
  vimshottari: 'dasha_vimshottari',
  yogini: 'dasha_yogini',
  chara: 'dasha_chara',
}

export const query_dasha = tool({
  description:
    'Query Vimshottari, Yogini, or Jaimini Chara dasha periods from the chart_facts table. ' +
    'Use this when the user asks: "what is the current mahadasha?", ' +
    '"when does Ketu mahadasha start?", ' +
    '"show all antardasha periods under Mercury mahadasha", ' +
    '"what dasha was running in 2019?", ' +
    '"get Vimshottari dasha sequence from 2024 onward". ' +
    'Returns rows with fact_id and value_json containing start_date, end_date, md_lord, ad_lord. ' +
    'For ephemeris date-by-date queries use query_planet_position instead.',
  inputSchema: z.object({
    system: z.enum(['vimshottari', 'yogini', 'chara']).optional().describe(
      'Dasha system to query. Defaults to vimshottari.'
    ),
    md_lord: z.string().optional().describe(
      'Filter to a specific Mahadasha lord (e.g. Mercury, Saturn, Ketu). Case-insensitive.'
    ),
    as_of_date: z.string().optional().describe(
      'ISO date (YYYY-MM-DD). Returns the single dasha period active on that date.'
    ),
    limit: z.number().int().min(1).max(100).default(30).describe(
      'Maximum rows to return (default 30).'
    ),
  }),
  execute: async ({ system, md_lord, as_of_date, limit }) => {
    try {
      const category = CATEGORY_MAP[system ?? 'vimshottari']
      const conditions: string[] = [`category = $1`]
      const params: (string | number)[] = [category]
      let idx = 2

      if (md_lord) {
        conditions.push(
          `(value_json->>'md_lord' ILIKE $${idx} OR value_json->>'ruler' ILIKE $${idx} OR value_json->>'md_sign' ILIKE $${idx})`
        )
        params.push(`%${md_lord}%`)
        idx++
      }

      if (as_of_date) {
        conditions.push(
          `(value_json->>'start_date')::date <= $${idx} AND (value_json->>'end_date')::date > $${idx + 1}`
        )
        params.push(as_of_date, as_of_date)
        idx += 2
      }

      const sql = `
        SELECT fact_id, value_json, source_section
        FROM chart_facts
        WHERE ${conditions.join(' AND ')}
        ORDER BY (value_json->>'start_date')::date ASC
        LIMIT $${idx}
      `
      params.push(limit)
      const { rows } = await query(sql, params)
      return { count: rows.length, dasha_periods: rows }
    } catch (e) {
      return { error: e instanceof Error ? e.message : String(e) }
    }
  },
})
