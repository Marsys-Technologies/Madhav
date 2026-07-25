/**
 * query_planet — canonical assembled-entity face for a graha (EL-31, Task 3)
 * ================================================================================
 * Elevation Campaign v2.1, STREAM α Lane-H. ONE assembled object per planet, combining:
 * sign, house, nakshatra+pada, dignity chain, shadbala, avasthas, aspects in/out,
 * functional nature, yogas, and dispositor.
 *
 * B.10 compliance: this capability performs ZERO new astrological computation. Every facet
 * is gathered by calling the EXISTING already-registered capability handlers in this same
 * directory (get_positions / get_dignity / get_strength / get_avasthas / get_aspects /
 * get_yoga_dosha / get_yoga_firings / get_dispositors) IN-PROCESS — same module graph, same
 * `@/lib/db/client` pool, no HTTP hop, no re-derivation. This file only ASSEMBLES what those
 * handlers already serve, plus a best-effort text-match filter (documented per facet below)
 * to narrow multi-subject facets (aspects/yogas/dispositors) down to the requested graha —
 * filtering already-served rows is not computation.
 *
 * GENUINE GAPS (reported honestly, not papered over — see each facet's `note` when empty):
 *  - "functional nature" is served as part of get_dignity's graha_functional_class_per_ascendant
 *    category — present for the 9 classical grahas only (not Rahu/Ketu upagraha variants).
 *  - "aspects in/out" and "yogas"/"dispositor" facets are matched via a fact_key/fact_value
 *    text-containment heuristic (these underlying capabilities do not expose a `fact_subject`
 *    column or a `graha` filter param of their own) — a miss here does not mean the graha has
 *    no aspects/yogas/dispositor chain, only that this heuristic didn't find a row; the raw
 *    underlying tool (get_aspects/get_yoga_dosha/get_yoga_firings/get_dispositors) remains the
 *    authoritative drill-down.
 */
import type { CapabilityDescriptor } from '../../types'
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '../../../address_resolver'
import { getPositionsCapability } from './get_positions'
import { getDignityCapability } from './get_dignity'
import { getStrengthCapability } from './get_strength'
import { getAvasthsCapability } from './get_avasthas'
import { getAspectsCapability } from './get_aspects'
import { getYogaDoshaCapability } from './get_yoga_dosha'
import { getYogaFiringsCapability } from './get_yoga_firings'
import { getDispositorsCapability } from './get_dispositors'

type FactRow = Record<string, unknown>

/** Best-effort: does this already-served row plausibly concern the given graha? Checks
 *  fact_subject (when present), fact_key, fact_value_text, and a stringified fact_value_jsonb
 *  for the graha's code or full name. Documented heuristic, not a computation (B.10). */
function rowMentionsGraha(row: FactRow, code: string, name: string): boolean {
  const needleCode = code.toLowerCase()
  const needleName = name.toLowerCase()
  const haystackParts: string[] = []
  for (const key of ['fact_subject', 'fact_key', 'fact_value_text']) {
    const v = row[key]
    if (typeof v === 'string') haystackParts.push(v.toLowerCase())
  }
  if (row['fact_value_jsonb'] != null) {
    try { haystackParts.push(JSON.stringify(row['fact_value_jsonb']).toLowerCase()) } catch { /* ignore */ }
  }
  const haystack = haystackParts.join(' | ')
  return haystack.includes(needleCode) || haystack.includes(needleName)
}

async function callHandler(cap: CapabilityDescriptor, args: FactRow): Promise<{ rows: FactRow[]; error?: string }> {
  const result = await cap.handler(args)
  if (result.is_error) return { rows: [], error: typeof result.content === 'string' ? result.content : JSON.stringify(result.content) }
  const content = result.content as FactRow
  const rows = Array.isArray(content?.['rows']) ? (content['rows'] as FactRow[]) : []
  return { rows }
}

export const queryPlanetCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/query_planet',
  type: 'tool',
  layer: 'L1',
  name: 'query_planet',
  description: [
    'Canonical assembled-entity face for ONE graha: sign, house (D1), nakshatra+pada, degree,',
    'retrograde/combustion state, dignity chain (exalted/own/friend/neutral/enemy/debilitated +',
    'functional class for this Aries lagna), shadbala (6 components + total), avasthas (baladi/',
    'deepta/jagrad/lajjitadi/sayanadi), aspects given/received (best-effort matched), yogas this',
    'graha participates in (firings-authoritative + catalog-label, both flagged separately),',
    'and its dispositor chain. Gathers ALL of this from already-served L1 capabilities in one',
    'call (get_positions/get_dignity/get_strength/get_avasthas/get_aspects/get_yoga_dosha/',
    'get_yoga_firings/get_dispositors) — no new computation. Use this instead of chaining',
    '7+ individual EAV tool calls for an entity-shaped ("tell me about Saturn") question.',
  ].join(' '),
  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID', required: true },
    planet: { type: 'string', description: 'Graha name (English, Sanskrit, or 2-3 letter code), e.g. "Saturn", "shani", "SAT".', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for default.' },
  },
  required_inputs: ['chart_id', 'planet'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 92, always_include: false },
  },
  density_contract: {
    paginated: false,
    facets: ['planet', 'ayanamsha_id'],
    empty_reason: true,
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const planetInput = args.planet as string
      if (!chartId) return { content: { error: 'chart_id is required' }, is_error: true }
      if (!planetInput) return { content: { error: 'planet is required' }, is_error: true }

      let code: string
      try {
        code = grahaCodeOf(planetInput)
      } catch (e) {
        // Honest resolver miss (Absence Protocol, Task 2/EL-07) — not a silent empty result.
        return {
          content: {
            resolved: false,
            planet: planetInput,
            empty_reason: `"${planetInput}" did not resolve to a known graha via grahaCodeOf (checked GRAHA_CODE_TO_NAME + GRAHA_ALIASES, address_resolver.ts): ${String(e)}. Known names: ${Object.values(GRAHA_CODE_TO_NAME).join(', ')} (plus Sanskrit aliases and 2-letter shorthand).`,
          },
          is_error: false,
        }
      }
      const name = GRAHA_CODE_TO_NAME[code] ?? planetInput
      const baseArgs: FactRow = { chart_id: chartId, ...(args.ayanamsha_id ? { ayanamsha_id: args.ayanamsha_id } : {}) }

      const [positions, dignity, strength, avasthas, aspects, yogaDosha, yogaFirings, dispositors] = await Promise.all([
        callHandler(getPositionsCapability, { ...baseArgs, planet: planetInput, categories: ['graha_position'] }),
        callHandler(getDignityCapability, baseArgs),
        callHandler(getStrengthCapability, { ...baseArgs, graha_key: code }),
        callHandler(getAvasthsCapability, baseArgs),
        callHandler(getAspectsCapability, baseArgs),
        callHandler(getYogaDoshaCapability, { ...baseArgs, type: 'yoga' }),
        callHandler(getYogaFiringsCapability, { chart_id: chartId, fired: true }),
        callHandler(getDispositorsCapability, baseArgs),
      ])

      const dignityRows = dignity.rows.filter(r => rowMentionsGraha(r, code, name))
      const avasthaRows = avasthas.rows.filter(r => rowMentionsGraha(r, code, name))
      const aspectRows = aspects.rows.filter(r => rowMentionsGraha(r, code, name))
      const yogaLabelRows = yogaDosha.rows.filter(r => rowMentionsGraha(r, code, name))
      const yogaFiringRows = yogaFirings.rows.filter(r => {
        const cp = r['constituent_planets']
        if (Array.isArray(cp)) return cp.some(p => typeof p === 'string' && (p.toUpperCase() === code || p.toLowerCase() === name.toLowerCase()))
        return rowMentionsGraha(r, code, name)
      })
      const dispositorRows = dispositors.rows.filter(r => rowMentionsGraha(r, code, name))

      const sourceErrors = [
        positions.error, dignity.error, strength.error, avasthas.error,
        aspects.error, yogaDosha.error, yogaFirings.error, dispositors.error,
      ].filter((e): e is string => Boolean(e))

      return {
        content: {
          chart_id: chartId,
          planet: { input: planetInput, code, name },
          position: {
            rows: positions.rows,
            note: positions.rows.length === 0 ? 'no graha_position row found for this planet' : undefined,
          },
          dignity: {
            rows: dignityRows,
            note: dignityRows.length === 0 ? 'no dignity rows matched this graha by fact_subject/text heuristic — see get_dignity directly' : undefined,
          },
          shadbala: {
            rows: strength.rows,
            note: strength.rows.length === 0 ? 'no shadbala rows found for this planet (graha_key filter)' : undefined,
          },
          avasthas: {
            rows: avasthaRows,
            note: avasthaRows.length === 0 ? 'no avastha rows matched this graha by fact_subject/text heuristic — see get_avasthas directly' : undefined,
          },
          aspects: {
            rows: aspectRows,
            note: 'best-effort text-match filter over get_aspects rows (that capability does not expose a fact_subject column) — a miss here does not prove the graha has no aspects; see get_aspects for the unfiltered set.' + (aspectRows.length === 0 ? ' No rows matched.' : ''),
          },
          functional_nature: {
            note: 'included within the dignity facet above (graha_functional_class_per_ascendant category, when present in dignity.rows).',
          },
          yogas: {
            firings_authoritative: yogaFiringRows,
            catalog_label: yogaLabelRows,
            note: 'firings_authoritative rows come from get_yoga_firings (fired=true, constituent_planets match); catalog_label rows are single-pass chart_facts yoga_label matches from get_yoga_dosha (§N.6 point 1 — never conflate the two counts).' +
              (yogaFiringRows.length === 0 && yogaLabelRows.length === 0 ? ' No rows matched either source for this graha.' : ''),
          },
          dispositor: {
            rows: dispositorRows,
            note: dispositorRows.length === 0 ? 'no dispositor-chain rows matched this graha by text heuristic — see get_dispositors directly' : undefined,
          },
          ...(sourceErrors.length > 0 ? { judgment_flags: ['partial_source_error'], source_errors: sourceErrors } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
