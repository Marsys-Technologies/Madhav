/**
 * graha_portrait — the mirror recipe for graha-questions (design §28.2, R5 W3)
 * ==============================================================================
 * "How is my Saturn?" — one call assembling the acharya's full first working-through
 * of a single graha, per design §28.2's exact field list:
 *   dignity chain across operative vargas · shadbala decomposition · avasthas ·
 *   yogas it participates in · its dasha periods (past/next) · its CGM neighborhood ·
 *   functional nature for this lagna.
 * Plus (this lane's addition, cheap and load-bearing for the "mirror" framing):
 * current position (sign/house/nakshatra/pada) — the thing a graha question almost
 * always needs first, and free to fold in since get_positions is already a one-shot
 * leaf call.
 *
 * SYNTHESIS, NOT A NEW DATA SOURCE (per the W3 brief): every section below is produced
 * by calling the ALREADY-BUILT L1/L2 capability handlers in-process (direct function
 * calls on the exported `*Capability.handler`, not a second HTTP round-trip — this
 * runs inside the same platform process) and filtering/organizing their rows around
 * one graha. No new SQL against chart_facts/bodha_msr_signals/bodha_cgm_* is written
 * here beyond what those capabilities already run. Design §29 explicitly keeps
 * graha_portrait + judgment_query as the two sanctioned cross-layer synthesizers
 * (the "entity re-architecture" was rejected everywhere else in the estate).
 *
 * WHY CLIENT-SIDE GRAHA FILTERING (not a new SQL WHERE clause): chart_facts's
 * fact_subject naming is NOT uniform across categories — bare 3-letter codes
 * ("SAT"), full names ("SATURN"), varga-prefixed ("D9_SAT"), or house-suffixed
 * ("SAT_IN_HOUSE_5") depending on which L1 writer produced the category (verified
 * live against both canonical charts before writing this). `subjectMatchesGraha`
 * below is the one place that variance is normalized, matching the single-source
 * mandate (design §19) — every section reuses this one matcher rather than each
 * writing its own ad hoc subject-string logic.
 *
 * A REAL DEFECT FOUND AND FIXED IN THIS LANE (not just filtered around): get_strength's
 * `graha_key` param filtered `fact_key ILIKE` — but fact_key is a GENERIC component name
 * shared by every graha ("rupa", "score", "bphs_weighted"); the graha identity lives in
 * `fact_subject`. The old filter silently matched zero rows for every category live
 * against both canonical charts. Fixed at the source (get_strength.ts) rather than
 * worked around here, since any other caller passing graha_key had the same silent-empty
 * bug (the exact P1/P3 failure class this run has been hunting).
 *
 * HONESTY ON "YOGAS IT PARTICIPATES IN" (design §28.2): L1 yoga_fires/dosha_fires are
 * 0 rows for both canonical charts (JL-004, restated at every wave since) — they are a
 * requires_pass CATALOG, not confirmed firings. The L2 bodha_msr_signals 'yoga'/'dosha'
 * signal_type_class rows carry the SAME catalog/requires_pass shape (verified live) —
 * they are not a working substitute either. The one MSR signal_type_class that IS
 * genuinely chart-specific and graha-attributed is 'parivartana' (structural exchange
 * yogas, real planet_a/planet_b pairs, verified live and populated for the native
 * chart). This section serves parivartana matches as real data, restates the
 * yoga_fires/dosha_fires emptiness with its reason (E-3 empty-with-reason) rather than
 * padding the section with catalog rows dressed as findings, and cites JL-004.
 */

import type { CapabilityDescriptor } from '../../types'
import { DEFAULT_AYANAMSHA } from '../../constants'
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '../../../address_resolver'
import { getPositionsCapability } from '../L1_ganita/get_positions'
import { getDignityCapability } from '../L1_ganita/get_dignity'
import { getStrengthCapability } from '../L1_ganita/get_strength'
import { getAvasthsCapability } from '../L1_ganita/get_avasthas'
import { getYogaDoshaCapability } from '../L1_ganita/get_yoga_dosha'
import { getDashasCapability } from '../L1_ganita/get_dashas'
import { querySignalsCapability } from './query_signals'
import { traverseChartGraphCapability } from './traverse_chart_graph'

const OPERATIVE_VARGAS = ['D1', 'D9', 'D10', 'D60'] as const

type FactRow = Record<string, unknown>

/** Unwrap a capability handler's { content, is_error } return, tolerating both the
 *  raw shape and the double-wrapped shape some L2 handlers use internally. */
function unwrap(raw: unknown): { content: FactRow; is_error: boolean } {
  const r = raw as { content?: unknown; is_error?: boolean }
  const content = (r?.content ?? {}) as FactRow
  return { content, is_error: Boolean(r?.is_error) }
}

/**
 * The single-source subject matcher (see file header). `subject` is a chart_facts
 * fact_subject or a bodha_cgm_nodes node_subject value. Matches bare code/name,
 * varga-prefixed ("D9_SAT"), and house/suffix-annotated ("SAT_IN_HOUSE_5") forms —
 * every naming convention observed live across the categories this portrait reads.
 */
function subjectMatchesGraha(subject: string | null | undefined, code: string, name: string): boolean {
  if (!subject) return false
  const s = subject.toUpperCase()
  const c = code.toUpperCase()
  const n = name.toUpperCase()
  if (s === c || s === n) return true
  if (s.startsWith(`${c}_`) || s.startsWith(`${n}_`)) return true
  if (s.endsWith(`_${c}`) || s.endsWith(`_${n}`)) return true
  return false
}

/** Broad match over an MSR signal's configuration_jsonb + headline text for graha
 *  attribution. MSR configuration_jsonb shape varies by signal_type_class (verified
 *  live); this checks every key observed to carry a graha value, plus a headline-text
 *  substring fallback (defensive — never the ONLY match path for a row we present as
 *  "found", but catches real parivartana/karaka rows whose keys don't match the list). */
function signalMatchesGraha(signal: FactRow, code: string, name: string): boolean {
  const cfg = (signal['configuration_jsonb'] as FactRow | null) ?? {}
  const candidates = [
    cfg['graha'], cfg['primary_graha'], cfg['lord_graha'], cfg['planet'], cfg['graha_key'],
    cfg['karaka_graha'], cfg['graha_subject'], cfg['graha1'], cfg['planet_a'], cfg['planet_b'],
    cfg['to_graha'], cfg['aspecting_graha'],
  ]
  const upperName = name.toUpperCase()
  const upperCode = code.toUpperCase()
  for (const v of candidates) {
    if (typeof v === 'string' && (v.toUpperCase() === upperName || v.toUpperCase() === upperCode)) return true
  }
  const headline = String(signal['signal_headline_text'] ?? '')
  if (headline && headline.toUpperCase().includes(upperName)) return true
  return false
}

export const grahaPortraitCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L2/graha_portrait',
  type: 'tool',
  layer: 'L2',
  name: 'graha_portrait',
  scope: 'per_chart',

  description: [
    'The mirror recipe for graha-questions (design §28.2) — "how is my Saturn?" as ONE call.',
    'Assembles: current position (sign/house/nakshatra/pada), dignity chain across the',
    'operative vargas (D1/D9/D10/D60 highlighted, full varga list included), shadbala',
    'decomposition (6 components + total + vimsopaka + ishta/kashta), avasthas (baladi/',
    'jagrad/deepta/lajjitadi/sayanadi), yogas/configurations it participates in (parivartana',
    'exchanges — real chart-specific data; yoga_fires/dosha_fires honestly reported empty',
    'with reason, JL-004), its dasha periods across the lifetime (past/next Mahadashas by',
    'default), its CGM neighborhood (direct graph neighbors + edges), and its functional',
    'nature for this lagna (benefic/malefic/yoga-karaka classification). Every section is a',
    'synthesis over the already-built L1/L2 capability handlers — no new data source.',
    'chart_id and graha are required; graha accepts English/Sanskrit names, 2-letter',
    'shorthand, or the stored fact_subject code (e.g. "Saturn", "shani", "sa", "SAT").',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha: {
      type: 'string',
      description: 'The graha to portray (e.g. "Saturn", "shani", "sa", "SAT"). Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha (default: 'lahiri_chitrapaksha').",
    },
    operative_vargas: {
      type: 'array',
      description: 'Which vargas to call out as "operative" in the dignity chain (default: D1, D9, D10, D60). The full dignity row set across ALL vargas is always included regardless.',
      items: { type: 'string' },
    },
    include: {
      type: 'array',
      description: 'Subset of sections to compute (default: all). One or more of: position, dignity, strength, avasthas, yogas, dashas, cgm_neighborhood.',
      items: {
        type: 'string',
        enum: ['position', 'dignity', 'strength', 'avasthas', 'yogas', 'dashas', 'cgm_neighborhood'],
      },
    },
  },

  required_inputs: ['chart_id', 'graha'],
  archetype: 'cross_domain',
  traversal_level: 'L-SYNTH',
  tool_role: 'synthesizer',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },
  lel_capable: false,

  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args, ctx) {
    const chart_id = args['chart_id'] as string
    const grahaInput = args['graha'] as string
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }
    if (!grahaInput) return { content: { error: 'graha is required' }, is_error: true }

    let grahaCode: string
    try {
      grahaCode = grahaCodeOf(grahaInput)
    } catch (e) {
      return { content: { error: String(e) }, is_error: true }
    }
    const grahaName = GRAHA_CODE_TO_NAME[grahaCode] ?? grahaInput

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? DEFAULT_AYANAMSHA
    const operativeVargas = (args['operative_vargas'] as string[] | undefined) ?? [...OPERATIVE_VARGAS]
    const include = (args['include'] as string[] | undefined) ?? [
      'position', 'dignity', 'strength', 'avasthas', 'yogas', 'dashas', 'cgm_neighborhood',
    ]
    const want = (section: string) => include.includes(section)

    const sections: Record<string, unknown> = {}
    const notes: string[] = []
    const errors: Record<string, string> = {}

    // ── position ─────────────────────────────────────────────────────────────
    if (want('position')) {
      try {
        const { content } = unwrap(await getPositionsCapability.handler(
          { chart_id, ayanamsha_id, categories: ['graha_position'] }, ctx,
        ))
        const rows = ((content['rows'] as FactRow[]) ?? [])
          .filter(r => subjectMatchesGraha(r['fact_subject'] as string, grahaCode, grahaName))
        sections['position'] = { rows, count: rows.length }
      } catch (e) { errors['position'] = String(e) }
    }

    // ── dignity (across all vargas; operative_vargas highlighted) + functional nature ──
    if (want('dignity')) {
      try {
        const { content } = unwrap(await getDignityCapability.handler({ chart_id, ayanamsha_id }, ctx))
        const rows = ((content['rows'] as FactRow[]) ?? [])
          .filter(r => subjectMatchesGraha(r['fact_subject'] as string, grahaCode, grahaName))
        const dignityRows = rows.filter(r => r['fact_category'] === 'graha_dignity_per_varga')
        const functionalRows = rows.filter(r => r['fact_category'] === 'graha_functional_class_per_ascendant')
        const operativeRows = dignityRows.filter(r => {
          const varga = (r['fact_value_jsonb'] as FactRow | null)?.['varga']
          return typeof varga === 'string' && operativeVargas.includes(varga)
        })
        sections['dignity'] = {
          operative_vargas: operativeVargas,
          operative_varga_rows: operativeRows,
          all_varga_rows: dignityRows,
          other_rows: rows.filter(r =>
            r['fact_category'] !== 'graha_dignity_per_varga' &&
            r['fact_category'] !== 'graha_functional_class_per_ascendant'),
          count: rows.length,
        }
        sections['functional_nature'] = { rows: functionalRows, count: functionalRows.length }
      } catch (e) { errors['dignity'] = String(e) }
    }

    // ── strength (shadbala decomposition) ───────────────────────────────────
    if (want('strength')) {
      try {
        const { content } = unwrap(await getStrengthCapability.handler(
          { chart_id, ayanamsha_id, graha_key: grahaCode }, ctx,
        ))
        const rows = (content['rows'] as FactRow[]) ?? []
        sections['strength'] = { rows, count: rows.length }
      } catch (e) { errors['strength'] = String(e) }
    }

    // ── avasthas ─────────────────────────────────────────────────────────────
    if (want('avasthas')) {
      try {
        const { content } = unwrap(await getAvasthsCapability.handler({ chart_id, ayanamsha_id }, ctx))
        const rows = ((content['rows'] as FactRow[]) ?? [])
          .filter(r => subjectMatchesGraha(r['fact_subject'] as string, grahaCode, grahaName))
        sections['avasthas'] = { rows, count: rows.length }
      } catch (e) { errors['avasthas'] = String(e) }
    }

    // ── yogas / configurations it participates in ───────────────────────────
    if (want('yogas')) {
      try {
        // L1 honest empty-with-reason check (JL-004: yoga_fires/dosha_fires are a
        // requires_pass catalog, 0 confirmed firings for both canonical charts).
        const { content: l1Content } = unwrap(await getYogaDoshaCapability.handler(
          { chart_id, ayanamsha_id, type: 'yoga', categories: ['yoga_fires'] }, ctx,
        ))
        const firesRows = (l1Content['rows'] as FactRow[]) ?? []

        // L2 real substitute: parivartana (structural exchange yogas) is genuinely
        // chart-specific and graha-attributed (verified live) — the yoga/dosha
        // signal_type_class rows are NOT (same requires_pass catalog shape as L1).
        const [parivartanaRes, yogaClassRes, doshaClassRes] = await Promise.all([
          querySignalsCapability.handler({ chart_id, ayanamsha_id, signal_type_class: 'parivartana', top_k: 500 }, ctx),
          querySignalsCapability.handler({ chart_id, ayanamsha_id, signal_type_class: 'yoga', top_k: 500 }, ctx),
          querySignalsCapability.handler({ chart_id, ayanamsha_id, signal_type_class: 'dosha', top_k: 500 }, ctx),
        ])
        const parivartanaSignals = ((unwrap(parivartanaRes).content['signals'] as FactRow[]) ?? [])
          .filter(s => signalMatchesGraha(s, grahaCode, grahaName))
        const yogaClassSignals = ((unwrap(yogaClassRes).content['signals'] as FactRow[]) ?? [])
          .filter(s => signalMatchesGraha(s, grahaCode, grahaName))
        const doshaClassSignals = ((unwrap(doshaClassRes).content['signals'] as FactRow[]) ?? [])
          .filter(s => signalMatchesGraha(s, grahaCode, grahaName))

        sections['yogas'] = {
          parivartana_exchanges: parivartanaSignals,
          parivartana_count: parivartanaSignals.length,
          catalog_yoga_matches: yogaClassSignals,
          catalog_dosha_matches: doshaClassSignals,
          // `count` drives the completeness receipt below — real (parivartana) matches
          // AND catalog matches both count as "section populated" (the catalog rows are
          // real MSR data, just not confirmed firings; see the note's caveat).
          count: parivartanaSignals.length + yogaClassSignals.length + doshaClassSignals.length,
          note: [
            `L1 yoga_fires: ${firesRows.length} confirmed-firing row(s) for this graha`,
            '(0 is EXPECTED — yoga_fires/dosha_fires are 0 rows for both canonical charts;',
            'they are a requires_pass CATALOG, not confirmed firings — JL-004, restated here',
            'rather than re-litigated). parivartana_exchanges is real chart-specific data',
            '(structural planetary exchanges). catalog_yoga_matches/catalog_dosha_matches are',
            'signal_type_class=yoga/dosha MSR rows mentioning this graha — same catalog shape',
            'as L1, served for completeness but NOT confirmed firings; treat as candidate',
            'classifications to verify, not findings.',
          ].join(' '),
        }
      } catch (e) { errors['yogas'] = String(e) }
    }

    // ── dasha periods (past/next Mahadashas by default; wide window so lifetime
    // MD occurrences of this graha aren't clipped by the ±5y default window) ──
    if (want('dashas')) {
      try {
        // chart_dashas.lord_graha stores the FULL classical name ("Saturn"), not the
        // chart_facts fact_subject code ("SAT") — verified live against both canonical
        // charts. Passing grahaName here (not grahaCode) is required for a non-empty match.
        const { content } = unwrap(await getDashasCapability.handler(
          {
            chart_id, ayanamsha_id, system: 'vimshottari', level: 1, lord_graha: grahaName,
            window_start: '1900-01-01', window_end: '2100-01-01', fields: 'compact', limit: 200,
          }, ctx,
        ))
        const rows = (content['rows'] as FactRow[]) ?? []
        sections['dashas'] = {
          system: 'vimshottari', level: 'maha', rows, count: rows.length,
          note: 'Mahadasha-level (level=1) periods where this graha is lord, across a wide ' +
            '1900-2100 window (not the tool\'s ±5y default) so past AND next occurrences ' +
            'both surface. Pass include without "dashas" + call get_dashas directly with a ' +
            'narrower window/level for Antardasha-level detail.',
        }
      } catch (e) { errors['dashas'] = String(e) }
    }

    // ── CGM neighborhood ─────────────────────────────────────────────────────
    if (want('cgm_neighborhood')) {
      try {
        const raw = await traverseChartGraphCapability.handler(
          {
            chart_id, ayanamsha_id, mode: 'neighbors', depth: 1, direction: 'both',
            about: [{ type: 'graha', graha: grahaName }],
          }, ctx,
        )
        const { content } = unwrap(raw)
        sections['cgm_neighborhood'] = {
          nodes: content['nodes'] ?? [],
          edges: content['edges'] ?? [],
          node_count: content['node_count'] ?? 0,
          edge_count: content['edge_count'] ?? 0,
          about_resolution: content['about_resolution'] ?? null,
        }
      } catch (e) { errors['cgm_neighborhood'] = String(e) }
    }

    // ── completeness receipt (design §28.6's classical-units vocabulary, applied
    // to the graha_portrait recipe rather than judgment_query's bhava recipe) ──
    const completeness: Record<string, string> = {}
    for (const key of ['position', 'dignity', 'functional_nature', 'strength', 'avasthas', 'yogas', 'dashas', 'cgm_neighborhood']) {
      if (!want(key === 'functional_nature' ? 'dignity' : key)) { completeness[key] = 'not_requested'; continue }
      if (errors[key === 'functional_nature' ? 'dignity' : key]) { completeness[key] = 'error'; continue }
      const section = sections[key]
      const count = (section as { count?: number } | undefined)?.count
        ?? (section as { node_count?: number } | undefined)?.node_count
      completeness[key] = (count ?? 0) > 0 ? '✓' : 'zero_rows'
    }

    if (Object.keys(errors).length > 0) {
      notes.push(`Section errors (partial portrait): ${JSON.stringify(errors)}`)
    }

    return {
      content: {
        chart_id,
        graha: grahaName,
        graha_code: grahaCode,
        ayanamsha_id,
        ...sections,
        completeness,
        notes,
        errors: Object.keys(errors).length > 0 ? errors : undefined,
        provenance: {
          synthesis_of: [
            'marsys://tool/L1/get_positions', 'marsys://tool/L1/get_dignity',
            'marsys://tool/L1/get_strength', 'marsys://tool/L1/get_avasthas',
            'marsys://tool/L1/get_yoga_dosha', 'marsys://tool/L1/get_dashas',
            'marsys://tool/L2/query_signals', 'marsys://tool/L2/traverse_chart_graph',
          ],
          design_ref: 'RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md §28.2',
        },
      },
      is_error: false,
    }
  },
}
