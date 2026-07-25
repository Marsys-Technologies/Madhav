/**
 * L1 retrieval: divisional charts (chart_divisionals)
 * Source: chart_divisionals table (not chart_facts)
 * Tool: marsys://tool/L1/get_divisionals
 *
 * EL-47 serving leg (house_from_varga_lagna): the stored `house` column is only populated
 * for the `formula_provenance_text = 'whole_sign'` rows (the canonical placement row per
 * chart/ayanamsha/varga/graha — see address_resolver.ts `fetchVargaGrahaPlacement`'s comment
 * for the same finding). Every other formula-annotation row (dignity tables, Pushkara bhaga,
 * saptavargaja weights, Jaimini karaka labels, etc.) carries `sign` but NOT `house` — live-
 * verified against chart 482012f1: only ~2,465/21,635 rows have `house` populated. This
 * handler computes `house_from_varga_lagna` server-side (compute-on-read, B.10-safe — no new
 * astrological value invented, purely a sign→house re-count using the SAME `houseCountedFrom`
 * convention `get_positions.ts`'s `house_from_frame` facet already uses) for every row whose
 * `sign` is a valid zodiac sign, using THAT ROW'S OWN VARGA lagna sign (not the D1 lagna — a
 * D9 sign must be counted from the D9 lagna, per classical varga-lagna practice) fetched from
 * the same table's `graha = 'Lagna' AND formula_provenance_text = 'whole_sign'` rows.
 * Persistence of this value is explicitly out of scope (serving leg only).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { houseCountedFrom, ZODIAC_SIGNS, type ZodiacSign } from '../../../address_resolver'

function isZodiacSign(v: unknown): v is ZodiacSign {
  return typeof v === 'string' && (ZODIAC_SIGNS as readonly string[]).includes(v)
}

export const getDivisionalsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_divisionals',
  type: 'tool',
  layer: 'L1',
  name: 'get_divisionals',
  description:
    'Retrieve divisional chart (varga) placements for a chart from the chart_divisionals table. ' +
    'Contains graha positions in each of the 16 standard vargas (D1–D60 including D1, D2, D3, D4, D5, ' +
    'D6, D7, D8, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60). ' +
    'Each row: graha, varga, sign, sign_number, degree_in_sign, house, vargottama. ' +
    'EL-47: every row whose `sign` is resolvable also carries a server-computed ' +
    '`house_from_varga_lagna` (1-indexed count from THAT VARGA\'S OWN lagna sign — not D1 — ' +
    'matching the house_from_frame/houseCountedFrom convention used elsewhere in this registry). ' +
    'Contains a large, paginated row set per chart.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    varga:        { type: 'string', description: 'Varga code (e.g. D9, D10, D12). Omit for all.' },
    graha:        { type: 'string', description: 'Graha abbreviation (e.g. SU, MO). Omit for all.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 300 },
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
    bulk_context: { pre_fetch_priority: 80, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 300, 2000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, limit, offset]
      let sql = `SELECT * FROM chart_divisionals WHERE chart_id = $1`

      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      if (args.varga) {
        sql += ` AND varga = $${params.length + 1}`
        params.push(args.varga as string)
      }
      if (args.graha) {
        sql += ` AND graha = $${params.length + 1}`
        params.push(args.graha as string)
      }
      sql += ` ORDER BY varga, ayanamsha_id, graha LIMIT $2 OFFSET $3`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // EL-47: compute house_from_varga_lagna for every row with a resolvable sign, using
      // that row's OWN (varga, ayanamsha_id) lagna sign. Single lookup query covers every
      // varga/ayanamsha the canonical Lagna/whole_sign rows carry (bounded, cheap — ~1
      // row per varga per ayanamsha) rather than one lookup per served row.
      const needsLagna = rows.some(r => isZodiacSign(r['sign']))
      let rowsWithHouse = rows
      if (needsLagna) {
        const lagnaResult = await query<{ varga: string; ayanamsha_id: string; sign: string | null }>(
          `SELECT varga, ayanamsha_id, sign FROM chart_divisionals
           WHERE chart_id = $1 AND graha = 'Lagna' AND formula_provenance_text = 'whole_sign'`,
          [chartId],
        )
        const vargaLagnaSign = new Map<string, ZodiacSign>()
        for (const r of lagnaResult.rows ?? []) {
          if (isZodiacSign(r.sign)) vargaLagnaSign.set(`${r.varga}::${r.ayanamsha_id}`, r.sign)
        }
        rowsWithHouse = rows.map(r => {
          const sign = r['sign']
          if (!isZodiacSign(sign)) return r
          const lagnaSign = vargaLagnaSign.get(`${r['varga']}::${r['ayanamsha_id']}`)
          if (!lagnaSign) return r
          return { ...r, house_from_varga_lagna: houseCountedFrom(lagnaSign, sign) }
        })
      }

      return {
        content: { chart_id: chartId, source_table: 'chart_divisionals', rows: rowsWithHouse, total: rowsWithHouse.length },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
