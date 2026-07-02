/**
 * L1 retrieval: Vimshottari (+ multi-system) dasha periods
 * Source: chart_dashas table (not chart_facts)
 * Tool: marsys://tool/L1/get_dashas
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getDashasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dashas',
  type: 'tool',
  layer: 'L1',
  name: 'get_dashas',
  description:
    'Retrieve dasha period data for a chart from the chart_dashas table. ' +
    'Includes all 7 dasha systems built by L1: Vimshottari, Yogini, Ashtottari, ' +
    'Chara (Jaimini), Narayana, Shoola, and Kalachakra. ' +
    'Returns period boundaries (start/end dates), lord graha, level (Maha/Antar/Pratyantar/etc.), ' +
    'and the dasha system identifier. ' +
    'Use date filters to retrieve the dasha running on a specific date (e.g. today). ' +
    'Contains 536,471 rows for the native across all systems and ayanamshas.',
  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:  { type: 'string', description: 'Filter by ayanamsha_id (e.g. LAHIRI). Omit for all.' },
    dasha_system:  {
      type: 'string',
      description: 'Dasha system name: VIMSHOTTARI | YOGINI | ASHTOTTARI | CHARA | NARAYANA | SHOOLA | KALACHAKRA. Default: VIMSHOTTARI.',
    },
    level:         { type: 'number', description: 'Dasha level (1=Maha, 2=Antar, 3=Pratyantar). Omit for all.' },
    date_contains: { type: 'string', description: 'ISO date (YYYY-MM-DD). Returns dashas active on this date.' },
    date_from:     { type: 'string', description: 'ISO date (YYYY-MM-DD). Filters to dashas whose end_date >= this date. Pass the birth date to exclude pre-birth rows.' },
    lord_graha:    { type: 'string', description: 'Filter by lord graha abbreviation (e.g. SU, MO, MA).' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, limit, offset]
      let sql = `SELECT * FROM chart_dashas WHERE chart_id = $1`

      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      if (args.dasha_system) {
        sql += ` AND system_id = $${params.length + 1}`
        params.push(args.dasha_system as string)
      }
      if (args.level !== undefined) {
        sql += ` AND level_n = $${params.length + 1}`
        params.push(args.level as number)
      }
      if (args.lord_graha) {
        sql += ` AND lord_graha = $${params.length + 1}`
        params.push(args.lord_graha as string)
      }
      if (args.date_contains) {
        sql += ` AND start_date <= $${params.length + 1}::date AND end_date >= $${params.length + 2}::date`
        params.push(args.date_contains as string)
        params.push(args.date_contains as string)
      }
      if (args.date_from) {
        // Exclude dashas that ended before date_from. The dasha running AT
        // date_from is included even if it started before (end_date >= date_from).
        sql += ` AND end_date >= $${params.length + 1}::date`
        params.push(args.date_from as string)
      }
      sql += ` ORDER BY system_id, ayanamsha_id, start_date LIMIT $2 OFFSET $3`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // ── Shadbala enrichment (graceful: failures return rows with null shadbala)
      // lord_natal_shadbala_total is not stored in chart_dashas; join with
      // chart_facts at query time. Planet codes in chart_dashas lord_graha use
      // 2-letter abbreviations (SU, MO, MA, ME, JU, VE, SA, RA, KE).
      const GRAHA_TO_FACT_SUBJECT: Record<string, string> = {
        SU: 'SUN',
        MO: 'MOON',
        MA: 'MAR',
        ME: 'MER',
        JU: 'JUP',
        VE: 'VEN',
        SA: 'SAT',
        RA: 'RAH_MEAN',
        KE: 'KET_MEAN',
      }

      let shadbalMap: Record<string, number | null> = {}
      try {
        const uniqueLords = [...new Set(rows.map(r => r['lord_graha'] as string).filter(Boolean))]
        // Use the ayanamsha_id from the first row (or from args) for the shadbala lookup.
        const ayanamshaForShadbala =
          (args.ayanamsha_id as string | undefined) ??
          (rows[0]?.['ayanamsha_id'] as string | undefined)

        const factSubjects = uniqueLords
          .map(g => GRAHA_TO_FACT_SUBJECT[g])
          .filter(Boolean)

        if (factSubjects.length > 0 && ayanamshaForShadbala) {
          const placeholders = factSubjects.map((_, i) => `$${i + 3}`).join(', ')
          const shadbalaSql = `
            SELECT fact_subject, fact_value_num
            FROM chart_facts
            WHERE chart_id = $1
              AND ayanamsha_id = $2
              AND fact_category = 'graha_shadbala_total'
              AND fact_key = 'rupa'
              AND fact_subject IN (${placeholders})
          `
          const shadbalaResult = await query<{ fact_subject: string; fact_value_num: number | null }>(
            shadbalaSql,
            [chartId, ayanamshaForShadbala, ...factSubjects]
          )
          // Build reverse map: fact_subject → value, then re-key by lord_graha code
          const subjectToValue: Record<string, number | null> = {}
          for (const r of shadbalaResult.rows ?? []) {
            subjectToValue[r.fact_subject] = r.fact_value_num
          }
          for (const [grahaCode, factSubject] of Object.entries(GRAHA_TO_FACT_SUBJECT)) {
            if (factSubject in subjectToValue) {
              shadbalMap[grahaCode] = subjectToValue[factSubject]
            }
          }
        }
      } catch {
        // Non-blocking: shadbala enrichment failure leaves null values
        shadbalMap = {}
      }

      const enrichedRows = rows.map(row => ({
        ...row,
        lord_natal_shadbala_total:
          shadbalMap[(row['lord_graha'] as string) ?? ''] ?? null,
      }))

      return {
        content: {
          chart_id: chartId,
          source_table: 'chart_dashas',
          rows: enrichedRows,
          total: enrichedRows.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
