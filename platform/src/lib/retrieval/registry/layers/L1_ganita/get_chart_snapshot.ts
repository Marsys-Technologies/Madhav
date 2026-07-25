/**
 * L1 retrieval: chart_snapshot — compact chat-renderable D1 (+D9 on request, +vargas[] on
 * request) grid
 * ===================================================================================
 * Tool: marsys://tool/L1/chart_snapshot
 *
 * R5.1 C2 item 7 ("the 'show me the chart' answer"): a 12-rashi text grid showing every
 * graha's sign + degree-in-sign, with the Lagna sign marked, hard-capped at <=2KB for direct
 * display in a chat client (MCP channel). D9 (navamsa) is available ONLY when explicitly
 * requested via `include_navamsa: true` — never on by default.
 *
 * EL-48 (Elevation Campaign v2.1, Lane A): `vargas: string[]` (e.g. ["D2","D10","D11"])
 * additively assembles any number of further vargas server-side, on top of D1 (+D9 if
 * include_navamsa). This is purely a wider fan-out over the SAME per-varga lookup mechanism
 * D9 already used (one parameterized SELECT against chart_divisionals filtered by
 * `varga = ANY($3::text[])`, reusing `buildGrid` per varga) — no new astrological computation
 * (B.10). Requested vargas beyond D1/D9 are served in the additive `additional_vargas` array
 * (self-contained per-varga objects — safe for the response-budget trimmer to drop wholesale
 * entries from without corrupting an individual grid's 12-rashi structure); `vargas`/`grids`/
 * `snapshot_text` keep their pre-EL-48 shape (D1, +D9 if requested) for backward compatibility.
 * A requested varga that yields zero rows (unrecognized code, or a real varga with no data for
 * this chart) is named honestly in `unresolved_vargas` rather than rendered as a silent
 * empty-but-plausible-looking grid (Absence Protocol, EL-07).
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

// The 19 standard vargas this table is populated for (matches get_divisionals.ts's
// documented list). Used only for the honest `unresolved_vargas` distinction below — a
// requested varga NOT in this list is flagged as an unrecognized code (resolver-miss), never
// silently rendered as an empty-but-plausible-looking 12-rashi grid (Absence Protocol, EL-07).
const KNOWN_VARGA_CODES = new Set([
  'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10',
  'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60',
])

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
    'in a chat client (hard-capped at 2KB for D1 alone). Pass include_navamsa:true to ALSO get',
    'the D9 (navamsa) grid in the same response -- D9 is never included by default, only on',
    'explicit request. Pass vargas:["D2","D10",...] to ADDITIVELY assemble any number of further',
    'divisional-chart grids server-side (EL-48) -- served in the `additional_vargas` array,',
    'alongside the unchanged D1(+D9) `grids`/`snapshot_text` shape. A requested varga this chart',
    'has no data for is named honestly in `unresolved_vargas`, never silently rendered as an',
    'empty-looking grid. Renders already-computed chart_divisionals positions (varga_position',
    'category); no new computation.',
  ].join(' '),
  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:    { type: 'string', description: "Ayanamsha (default: 'lahiri_chitrapaksha')" },
    include_navamsa: { type: 'boolean', description: 'Also include the D9 (navamsa) grid. Default: false (D1 only).' },
    vargas: {
      type: 'array',
      description: 'Additional varga codes to assemble (e.g. ["D2","D10","D11"]). Additive to D1 (and D9 if include_navamsa is set) -- served in `additional_vargas`, never replacing the D1/D9 default. Standard codes: D1-D10, D12, D16, D20, D24, D27, D30, D40, D45, D60.',
      items: { type: 'string' },
    },
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

      // Pre-EL-48 default set — UNCHANGED shape/semantics (backward compatibility).
      const vargas = includeNavamsa ? ['D1', 'D9'] : ['D1']

      // EL-48: `vargas` request param (additional divisional charts) is ADDITIVE on top of
      // the default set above, never a replacement — served separately in
      // `additional_vargas`, so a caller relying on the pre-EL-48 `grids`/`snapshot_text`
      // shape sees byte-for-byte identical output when it omits the new param.
      const requestedExtra = Array.isArray(args.vargas)
        ? Array.from(new Set(
            (args.vargas as unknown[])
              .filter((v): v is string => typeof v === 'string' && v.trim().length > 0)
              .map(v => v.trim().toUpperCase()),
          )).filter(v => !vargas.includes(v))
        : []

      // Single query covers both the default set and any additional requested vargas — the
      // SAME per-varga lookup mechanism (parameterized `varga = ANY($3::text[])` against
      // chart_divisionals) D9 already used; no new astrological computation (B.10).
      const allVargas = [...vargas, ...requestedExtra]

      const result = await query<VargaRow & { varga: string; id: string }>(
        `SELECT DISTINCT ON (varga, graha) varga, graha, sign, degree_in_sign, id
         FROM chart_divisionals
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'varga_position'
           AND varga = ANY($3::text[]) AND graha <> 'ALL'
         ORDER BY varga, graha`,
        [chart_id, ayanamsha_id, allVargas],
      )

      const grounding_ids: string[] = []
      const gridsByVarga = new Map<string, VargaRow[]>()
      for (const row of result.rows) {
        if (!gridsByVarga.has(row.varga)) gridsByVarga.set(row.varga, [])
        gridsByVarga.get(row.varga)!.push(row)
        grounding_ids.push(row.id)
      }

      const snapshots: Record<string, ReturnType<typeof buildGrid>> = {}
      for (const varga of allVargas) {
        const rows = gridsByVarga.get(varga) ?? []
        snapshots[varga] = buildGrid(rows, varga)
      }

      const combinedText = vargas.map(v => snapshots[v]!.text).join('\n\n')
      const byteLength = Buffer.byteLength(combinedText, 'utf8')

      // EL-48 additive payload: one self-contained object per requested extra varga — safe
      // for the response-budget trimmer (platform-mcp/src/lib/response_budget.ts) to drop
      // whole entries from without corrupting any individual grid's fixed 12-rashi shape
      // (unlike shrinking a `rashis` array in place, which would silently drop signs).
      const additionalVargas = requestedExtra.map(varga => {
        const snap = snapshots[varga]!
        return {
          varga,
          text: snap.text,
          byte_length: Buffer.byteLength(snap.text, 'utf8'),
          rashis: snap.rashis,
        }
      })

      // Absence Protocol (EL-07): a requested extra varga that produced zero rows is named
      // honestly here, distinguishing "not a recognized varga code" (resolver miss against
      // KNOWN_VARGA_CODES) from "a recognized varga with no varga_position data for this
      // chart/ayanamsha" (a real, if unusual, data gap) — never rendered as an
      // indistinguishable empty-but-plausible-looking 12-rashi grid.
      const unresolvedVargas = requestedExtra
        .filter(v => (gridsByVarga.get(v) ?? []).length === 0)
        .map(v => ({
          varga: v,
          reason: KNOWN_VARGA_CODES.has(v)
            ? `"${v}" is a recognized varga code, but no varga_position rows were found in chart_divisionals for this chart_id/ayanamsha_id — not a rendering error, an honest data gap.`
            : `"${v}" is not among the standard varga codes this table is populated for (${Array.from(KNOWN_VARGA_CODES).join(', ')}) — checked chart_divisionals directly and found none; likely a resolver miss (typo or non-standard code), not confirmed absent from the chart.`,
        }))

      return {
        content: {
          chart_id,
          ayanamsha_id,
          vargas,
          snapshot_text: combinedText,
          byte_length: byteLength,
          within_budget: byteLength <= MAX_SNAPSHOT_BYTES,
          grids: Object.fromEntries(vargas.map(v => [v, snapshots[v]!.rashis])),
          additional_vargas: additionalVargas,
          unresolved_vargas: unresolvedVargas,
          grounding: { fact_ids: grounding_ids, table: 'chart_divisionals', fact_category: 'varga_position' },
          provenance: {
            note: 'Positions rendered verbatim from chart_divisionals (varga_position); no new computation. ' +
              'D9 included only when include_navamsa=true was explicitly passed. Any vargas requested via ' +
              'the `vargas` param are served additively in `additional_vargas`, never replacing D1/D9.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
