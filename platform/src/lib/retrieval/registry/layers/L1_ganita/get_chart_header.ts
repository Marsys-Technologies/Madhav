/**
 * L1 retrieval: chart_header (D1 data-plane addition, design §10.1 / §12)
 * ==========================================================================
 * The ~40-token frame-safety block every instrument's v3 envelope carries:
 * {chart_id_short, name, lagna_sign, lagna_deg, moon_sign, sun_sign, ayanamsha,
 * current_maha_antar}. Exists as its own capability so platform-mcp (a separate
 * process with no direct DB access — it proxies over HTTP) can fetch it the same
 * way it fetches every other L1 fact family, via callRegistryCapability().
 * Tool: marsys://tool/L1/get_chart_header
 */
import type { CapabilityDescriptor } from '../../types'
import { fetchChartHeaderResolution } from '../../../chart_header'
import { DEFAULT_AYANAMSHA } from '../../constants'

export const getChartHeaderCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_chart_header',
  type: 'tool',
  layer: 'L1',
  name: 'get_chart_header',
  description:
    'Retrieve the mandatory chart_header frame-safety block for a chart: identity (name), ' +
    'Lagna sign + degree, Moon sign, Sun sign, ayanamsha, and current Vimshottari Maha/Antar ' +
    'dasha lords. Every v3-format envelope carries this block — cross-check any positional ' +
    'claim against it before asserting; a body that contradicts its own header is a served-data ' +
    'bug (design §10.1). ~40 tokens; cheap and cacheable.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default: 'lahiri_chitrapaksha')" },
    as_of_date:   { type: 'string', description: 'ISO date (YYYY-MM-DD) for current_maha_antar resolution. Default: today.' },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-ORIENT',
  tool_role: 'leaf',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 100, always_include: true },
  },
  async handler(args, _ctx) {
    try {
      const chart_id = args.chart_id as string
      if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }
      const ayanamsha_id = (args.ayanamsha_id as string | undefined) ?? DEFAULT_AYANAMSHA
      const as_of_date = args.as_of_date as string | undefined
      // W3-L1 (GT-47 / W-9): resolve via the flags-carrying path so a DB-level failure
      // (fields nulled, `flags` non-empty) is visible to the caller via `metadata.flags`
      // instead of silently indistinguishable from "this chart genuinely has no header
      // data". `is_error` stays false — the header is still best-effort content, never a
      // hard failure of this capability call.
      const { header, flags } = await fetchChartHeaderResolution(chart_id, ayanamsha_id, as_of_date)
      return { content: header, is_error: false, ...(flags.length > 0 ? { metadata: { flags } } : {}) }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
