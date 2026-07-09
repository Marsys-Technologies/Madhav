/**
 * L1 retrieval: chart_snapshot — compact chat-renderable D1 (+D9 on request) grid
 * ===================================================================================
 * Tool: marsys://tool/L1/chart_snapshot
 *
 * R5.1 C2 item 7 ("the 'show me the chart' answer"): a 12-rashi text grid showing every
 * graha's sign + degree-in-sign, with the Lagna sign marked, hard-capped at <=2KB for direct
 * display in a chat client (MCP channel). D9 (navamsa) is available ONLY when explicitly
 * requested via `include_navamsa: true` — never on by default.
 *
 * Source data: `chart_divisionals` (fact_category='varga_position'), the same table
 * get_divisionals.ts reads — sign/sign_number/degree_in_sign per graha per varga. D1 rows in
 * this table agree with chart_facts.graha_position (cross-checked during implementation:
 * native Sun=Capricorn 22.195 deg, Moon=Aquarius 29.772 deg (nakshatra Purva Bhadrapada),
 * Lagna=Aries 12.431 deg — all match the FORENSIC anchors). No new computation — pure
 * read + render of already-computed L1 positions (B.10: formatting, not fabrication).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { ZODIAC_SIGNS, type ZodiacSign } from '../../../address_resolver'
import { DEFAULT_AYANAMSHA } from '../../constants'

// Compact 2-3 letter graha abbreviations for the grid (distinct from the SUN/MOON/MAR/...
// fact_subject codes used elsewhere — these are the short display labels of the grid itself).
const GRAHA_ABBREV: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju',
  Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

const SIGN_ABBREV: Record<string, string> = {
  Aries: 'Ari', Taurus: 'Tau', Gemini: 'Gem', Cancer: 'Can', Leo: 'Leo', Virgo: 'Vir',
  Libra: 'Lib', Scorpio: 'Sco', Sagittarius: 'Sag', Capricorn: 'Cap', Aquarius: 'Aqu', Pisces: 'Pis',
}

const MAX_SNAPSHOT_BYTES = 2048

function degToDms(deg: number): string {
  const d = Math.floor(deg)
  const mFloat = (deg - d) * 60
  const m = Math.floor(mFloat)
  return `${d}°${String(m).padStart(2, '0')}'`
}

type VargaRow = { graha: string; sign: string; degree_in_sign: string }

/** Build the compact 12-rashi grid for one varga (D1 or D9). Returns both the text grid and
 *  a structured per-rashi array (for callers that want to render their own UI). */
function buildGrid(rows: VargaRow[], varga: string): { text: string; rashis: Array<{ sign: string; lagna: boolean; occupants: Array<{ graha: string; degree_in_sign: number }> }> } {
  const bySign = new Map<string, Array<{ graha: string; degree_in_sign: number }>>()
  let lagnaSign: string | null = null
  for (const r of rows) {
    if (r.graha === 'Lagna') {
      lagnaSign = r.sign
      continue // Lagna is marked on its sign line, not listed as an "occupant"
    }
    const abbrev = GRAHA_ABBREV[r.graha] ?? r.graha.slice(0, 2)
    if (!bySign.has(r.sign)) bySign.set(r.sign, [])
    bySign.get(r.sign)!.push({ graha: abbrev, degree_in_sign: Number(r.degree_in_sign) })
  }

  const rashis = ZODIAC_SIGNS.map((sign: ZodiacSign) => ({
    sign,
    lagna: sign === lagnaSign,
    occupants: (bySign.get(sign) ?? []).sort((a, b) => a.degree_in_sign - b.degree_in_sign),
  }))

  const lines: string[] = [`${varga}${lagnaSign ? ` — Lagna ${SIGN_ABBREV[lagnaSign] ?? lagnaSign}` : ''}`]
  rashis.forEach((r, i) => {
    const marker = r.lagna ? '[L]' : '   '
    const occStr = r.occupants.length
      ? r.occupants.map(o => `${o.graha} ${degToDms(o.degree_in_sign)}`).join(', ')
      : '-'
    lines.push(`${String(i + 1).padStart(2, ' ')} ${SIGN_ABBREV[r.sign] ?? r.sign} ${marker} ${occStr}`)
  })

  return {
    text: lines.join('\n'),
    rashis,
  }
}

export const getChartSnapshotCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/chart_snapshot',
  type: 'tool',
  layer: 'L1',
  name: 'chart_snapshot',
  scope: 'per_chart',
  description: [
    'The compact "show me the chart" answer: a 12-rashi D1 (rashi/D1 chart) text grid --',
    'every graha\'s sign + degree-in-sign, Lagna sign clearly marked -- sized for direct display',
    'in a chat client (hard-capped at 2KB). Pass include_navamsa:true to ALSO get the D9',
    '(navamsa) grid in the same response -- D9 is never included by default, only on explicit',
    'request. Renders already-computed chart_divisionals positions (varga_position category);',
    'no new computation.',
  ].join(' '),
  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:    { type: 'string', description: "Ayanamsha (default: 'lahiri_chitrapaksha')" },
    include_navamsa: { type: 'boolean', description: 'Also include the D9 (navamsa) grid. Default: false (D1 only).' },
  },
  required_inputs: ['chart_id'],
  archetype: 'flat_fact',
  traversal_level: 'L-ORIENT',
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
      const chart_id = args.chart_id as string
      if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }
      const ayanamsha_id = (args.ayanamsha_id as string | undefined) ?? DEFAULT_AYANAMSHA
      const includeNavamsa = args.include_navamsa === true

      const vargas = includeNavamsa ? ['D1', 'D9'] : ['D1']

      const result = await query<VargaRow & { varga: string; id: string }>(
        `SELECT DISTINCT ON (varga, graha) varga, graha, sign, degree_in_sign, id
         FROM chart_divisionals
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'varga_position'
           AND varga = ANY($3::text[]) AND graha <> 'ALL'
         ORDER BY varga, graha`,
        [chart_id, ayanamsha_id, vargas],
      )

      const grounding_ids: string[] = []
      const gridsByVarga = new Map<string, VargaRow[]>()
      for (const row of result.rows) {
        if (!gridsByVarga.has(row.varga)) gridsByVarga.set(row.varga, [])
        gridsByVarga.get(row.varga)!.push(row)
        grounding_ids.push(row.id)
      }

      const snapshots: Record<string, ReturnType<typeof buildGrid>> = {}
      for (const varga of vargas) {
        const rows = gridsByVarga.get(varga) ?? []
        snapshots[varga] = buildGrid(rows, varga)
      }

      const combinedText = vargas.map(v => snapshots[v]!.text).join('\n\n')
      const byteLength = Buffer.byteLength(combinedText, 'utf8')

      return {
        content: {
          chart_id,
          ayanamsha_id,
          vargas,
          snapshot_text: combinedText,
          byte_length: byteLength,
          within_budget: byteLength <= MAX_SNAPSHOT_BYTES,
          grids: Object.fromEntries(vargas.map(v => [v, snapshots[v]!.rashis])),
          grounding: { fact_ids: grounding_ids, table: 'chart_divisionals', fact_category: 'varga_position' },
          provenance: {
            note: 'Positions rendered verbatim from chart_divisionals (varga_position); no new computation. ' +
              'D9 included only when include_navamsa=true was explicitly passed.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
