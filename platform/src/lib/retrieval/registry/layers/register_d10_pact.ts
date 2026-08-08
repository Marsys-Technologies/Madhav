/**
 * D10 — pact_query: THE PACT PROTOCOL AS ONE CHAINED INVESTIGATION
 * ===================================================================
 * GATE A compliance: per-wave registration file. Does NOT edit registry/index.ts or
 * registry/types.ts.
 *
 * R5 W4 (design §26 + §28.3, brief §3 W4 lane 1 "PACT protocol end-to-end").
 *
 * THE PACT CHAIN, AS THE DESIGN DOC DEFINES IT (§26, restated + operationalized §28.3):
 * "the tradition also fixes the predictive grammar: promise in the rashi → confirmation
 *  in the varga → activation in the dasha → trigger in the transit" — four classically
 *  FALSIFIABLE stages, in this order:
 *   1. PROMISE      — judgment_query's checklist verdict on the matter (bhava/bhāveśa/
 *                      kāraka condition, both frames). §28.1 / §28.3.
 *   2. CONFIRMATION — does the operative varga (e.g. D9 for marriage) CONFIRM the
 *                      promise, i.e. is the promise-carrying lord/kāraka well-disposed
 *                      (not debilitated/enemy-owned) IN that varga? §28.3 "varga check
 *                      via frame/varga facets".
 *   3. ACTIVATION   — which dasha period(s) carry the promise-carrying lord/kāraka,
 *                      and is one active now, upcoming, or already spent with none to
 *                      come? §28.3 "kala_query: which promise-carrier dashas, when".
 *   4. TRIGGER      — a transit-gate check for the activation window. §28.3 "transit
 *                      gates in-window".
 * (design §28.3 also names a fifth "posterior (phala_query anchors)" as a further,
 * optional next step past TRIGGER — not one of the four PACT-named stages themselves;
 * this instrument does not attempt it, consistent with the brief's "four stages" framing.)
 *
 * "Each stage can HALT the chain classically... a denied promise ends the investigation
 * in two calls, honestly" (§28.3) — THIS is the behavior this file implements: the
 * chain STOPS the moment a stage is classically denied, and says so, rather than
 * fabricating downstream stages (B.10). "Pending" (not yet denied, not yet confirmable)
 * is reported distinctly from "denied" — an inactive dasha window is not a broken promise.
 *
 * NEW CAPABILITY, NOT A PURE ALIAS (JL-019 ruling — see R5_JUDGMENT_LEDGER): design §29
 * counts the estate as "15 substrate + judgment_query + graha_portrait (17 total)" and
 * frames PACT as navigation delivered via "typed pointers" over those 17 — not a new
 * endpoint. §30's W4 acceptance class, however, requires grading "chain honesty (a
 * denied promise must halt, a delivered prediction must cite all four stages)" — a
 * property that can only be exercised end-to-end, live, if something actually WALKS
 * the chain and can halt mid-flight. Typed drill_pointers (this wave's `pact_stage`
 * field on DrillPointer, envelope.ts) deliver the NAVIGATION half faithfully as pure
 * routing metadata with NO new endpoint; this capability delivers the EXECUTABLE half
 * so the halting behavior is a real, gate-verifiable server property, not merely a
 * documented convention an LLM caller might or might not honor. Both halves reuse the
 * existing 17-tool estate — this file adds zero parallel data-fetch logic; every stage
 * calls straight into judgment_query / get_dashas / query_planet_transit's own handlers.
 *
 * REUSE, NOT REBUILD (design §19): stage 1 delegates entirely to `judgmentQueryCapability`
 * (already runs bhava/bhāveśa/kāraka/from-Moon/varga/yoga/timing — see register_d9_judgment.ts).
 * Stage 3 reuses the SAME `checklist.timing_hooks` judgment_query already computed — no
 * second get_dashas fetch for the current-window check. Stage 4 reuses
 * `query_planet_transit` (L0) unchanged.
 *
 * Tool: marsys://tool/L-PACT/pact_query
 */
import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { query } from '@/lib/db/client'
import type { DrillPointer, JudgmentFlagEntry } from '../../envelope'
import { judgmentFlag } from '../../envelope'
import { grahaCodeOf } from '../../address_resolver'

// ── Classical dignity weighting for the CONFIRMATION stage (design §28.1's own weighting
// discipline — deterministic, never an LLM judgment, never a fabricated probability;
// the same closed vocabulary judgment_query's gradeGraha() uses for D1). ──
const DIGNITY_WEIGHT: Record<string, number> = {
  exalted: 2, own: 1.5, moolatrikona: 1.5, great_friend: 1, friend: 0.5,
  neutral: 0, enemy: -0.5, great_enemy: -1, debilitated: -2,
}

interface VargaDignityRow {
  role: 'bhavesha' | 'karaka'
  graha: string
  varga: string
  dignity_state: string | null
  dignity_weight: number | null
  fact_id: string | null
}

async function gradeGrahaInVarga(
  chartId: string, ayanamshaId: string, varga: string, graha: string, grahaCode: string, role: 'bhavesha' | 'karaka',
): Promise<VargaDignityRow> {
  try {
    const res = await query<{ fact_id: string; fact_value_text: string | null }>(
      `SELECT fact_id, fact_value_text FROM chart_facts
       WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_dignity_per_varga'
         AND fact_subject = $3 AND fact_key = 'dignity_state'`,
      [chartId, ayanamshaId, `${varga}_${grahaCode}`],
    )
    const row = res.rows[0]
    if (!row) return { role, graha, varga, dignity_state: null, dignity_weight: null, fact_id: null }
    return {
      role, graha, varga,
      dignity_state: row.fact_value_text,
      dignity_weight: row.fact_value_text ? DIGNITY_WEIGHT[row.fact_value_text] ?? 0 : null,
      fact_id: row.fact_id,
    }
  } catch {
    return { role, graha, varga, dignity_state: null, dignity_weight: null, fact_id: null }
  }
}

// graha display name -> the 2-letter/mean code chart_facts uses in fact_subject.
// Values sourced from the graha SSoT (address_resolver.grahaCodeOf) rather than
// hardcoded literals — ADHIṢṬHĀNA Lane A2. Kept as a local Record (not a bare
// grahaCodeOf() call at the read site below) because grahaCodeOf() THROWS on an
// unrecognized name while this call site's contract is a graceful
// skip-with-judgment-flag for an unrecognized `name`; the 9 literal keys here
// are well-formed graha names so grahaCodeOf() never throws building this table.
const GRAHA_NAME_TO_CODE: Record<string, string> = Object.fromEntries(
  ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    .map(name => [name, grahaCodeOf(name)]),
)

const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
// CR-40 fix: forward the sidecar API key when configured — same WP-1.7 pattern as
// query_planet_position.ts (`if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY`).
// register_d10_pact.ts (commit d22c0c9c, 2026-07-09) predates WP-1.7 (commit 2385fb62,
// 2026-07-13) by 4 days and was never brought onto that fix. The sidecar's verify_api_key
// dependency 401s on a missing/mismatched x-api-key whenever PYTHON_SIDECAR_API_KEY is
// set (see main.py); this call's `if (res.ok)` check silently swallowed that 401 as an
// empty row set, indistinguishable from a genuinely unreachable sidecar — so TRIGGER
// reported 'unreachable'/'chain_incomplete_infra' even though the sidecar was reachable
// (confirmed live: the identical /brahmagyan/ephemeris/planet_transit route succeeds when
// called WITH the header, e.g. via ref_planet_transit_get / l0_ephemeris.ts's sidecarGet).
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

export const pactQueryCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L-PACT/pact_query',
  type: 'tool',
  layer: 'L2',
  name: 'pact_query',
  scope: 'per_chart',

  description: [
    'THE PACT PROTOCOL (design §26/§28.3) as one chained investigation for event/timing',
    'questions — the classical predictive grammar "promise in the rashi → confirmation in',
    'the varga → activation in the dasha → trigger in the transit", walked stage by stage,',
    'HALTING HONESTLY the moment a stage is classically denied rather than fabricating the',
    'stages after it (B.10). Stage 1 PROMISE runs judgment_query\'s full checklist verdict.',
    'Stage 2 CONFIRMATION checks the promise-carrying bhāveśa/kāraka\'s dignity IN the',
    'operative varga (e.g. D9 for marriage) — debilitated/enemy-owned with no cancellation',
    'check available denies the chain here. Stage 3 ACTIVATION locates which dasha period',
    'carries that lord/kāraka: active now, upcoming (pending — not a denial), or none found',
    'in the computed window (denied — "the rashi does not promise it, no dasha can deliver',
    'it"). Stage 4 TRIGGER, only reached when ACTIVATION is active now, fetches the',
    'transiting tropical position for the activating graha(s) as an honest partial gate',
    'check (full sidereal vedha/aspect gating is a documented data-plane gap, reported not',
    'fabricated). Pass either `domain` or `bhava` exactly as judgment_query accepts.',
    'chart_id is required — never defaulted (principle #14).',
  ].join(' '),

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID (<chart_uuid>). Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Ayanamsha to use (default: 'lahiri_chitrapaksha')." },
    domain: {
      type: 'string',
      description: 'Life-domain name, resolved via judgment_query\'s shastra map (design §28.5): ' +
        'marriage/relationship/partnership, career/vocation, wealth/finance, health/vitality, ' +
        'progeny/children, education, spirituality. Takes precedence over `bhava` if both given.',
    },
    bhava: { type: 'number', description: 'Bhava (house) number 1-12, same semantics as judgment_query.' },
    as_of_date: { type: 'string', description: 'Date (YYYY-MM-DD) to evaluate ACTIVATION/TRIGGER as-of. Default: today.' },
    response_format: {
      type: 'string',
      description: "Envelope shape: 'legacy' (default) or 'v3' (populated verdict/grounding/chart_header).",
      enum: ['legacy', 'v3'],
    },
    max_signals: { type: 'number', description: 'Forwarded to judgment_query for the PROMISE stage (default 15, max 50).' },
  },

  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true, l0_citation_ids: true },
  lel_capable: false,
  drill_children: [
    'marsys://tool/L-JUDGMENT/judgment_query',
    'marsys://tool/L1/get_divisionals',
    'marsys://tool/L1/get_dashas',
    'marsys://tool/L0/query_planet_transit',
  ],

  llm_hints: {
    agentic: { cost_class: 'expensive', cacheable: false },
    bulk_context: { pre_fetch_priority: 20 },
  },

  mcp_annotations: { readOnly: true, destructive: false },

  async handler(args: Record<string, unknown>, _ctx?: unknown) {
    const chart_id = args['chart_id'] as string | undefined
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = (args['ayanamsha_id'] as string | undefined) ?? 'lahiri_chitrapaksha'
    const domain = args['domain'] as string | undefined
    const bhava = args['bhava'] !== undefined ? Number(args['bhava']) : undefined
    const as_of_date = (args['as_of_date'] as string | undefined) ?? new Date().toISOString().slice(0, 10)
    const max_signals = Math.min(Number(args['max_signals'] ?? 15), 50)

    if (!domain && bhava === undefined) {
      return { content: { error: 'pact_query requires either `domain` or `bhava` (same as judgment_query).' }, is_error: true }
    }

    const judgment_flags: JudgmentFlagEntry[] = []
    const fact_ids = new Set<string>()
    const stages: Array<Record<string, unknown>> = []
    const drill_pointers: DrillPointer[] = []

    try {
      // ── Stage 1: PROMISE (delegates entirely to judgment_query — §28.1) ──
      const { judgmentQueryCapability } = await import('./register_d9_judgment')
      const jqRes = await judgmentQueryCapability.handler(
        { chart_id, ayanamsha_id, domain, bhava, max_signals }, undefined,
      )
      if (jqRes.is_error) {
        return { content: { error: 'PROMISE stage (judgment_query) failed', detail: jqRes.content, chart_id }, is_error: true }
      }
      const jq = jqRes.content as Record<string, unknown>
      ;((jq['fact_id_refs'] as string[]) ?? []).forEach(f => fact_ids.add(f))
      const about = jq['about'] as Record<string, unknown>
      const verdict = jq['verdict'] as Record<string, unknown>
      const receipt = jq['receipt'] as Record<string, unknown>
      const checklist = jq['checklist'] as Record<string, unknown>
      const verdictGrade = verdict['verdict_grade'] as string
      const operativeVarga = about['operative_varga'] as string
      const karakas = (about['karakas'] as string[]) ?? []
      const bhaveshaCondition = checklist['bhavesha_condition'] as Record<string, unknown>
      const bhaveshaLagna = bhaveshaCondition['from_lagna'] as Record<string, unknown>
      const lordGraha = bhaveshaLagna['graha'] as string

      const promiseDenied = verdictGrade === 'contested'
      stages.push({
        stage: 'PROMISE',
        status: promiseDenied ? 'denied' : (verdictGrade === 'mixed' ? 'promised_weak' : 'promised'),
        verdict_grade: verdictGrade,
        composite_score: verdict['composite_score'],
        bhava: about['bhava'], domain: about['domain'], label: about['label'],
        reason: promiseDenied
          ? 'The rashi checklist does not promise this matter (contested composite: hostile occupants/aspects and/or ' +
            'a weak, poorly-disposed bhāveśa outweigh supportive factors) — per the classical chain, no later stage ' +
            'can deliver what the rashi itself does not promise.'
          : `Rashi checklist supports the matter (${verdictGrade}) — bhāveśa ${lordGraha}, kāraka(s) ${karakas.join(', ') || 'none'}.`,
      })

      if (promiseDenied) {
        drill_pointers.push({
          instrument: 'judgment_query', hint: 'Re-examine bhanga/cancellation and karaka condition directly — the composite denial may still merit a manual bhaṅga check (unbuilt gap, judgment_query receipt.bhanga_checked=false).',
          pointer_type: 'check_bhanga', pact_stage: 'promise',
        })
        return {
          content: {
            chart_id, ayanamsha_id, as_of_date, about,
            pact_status: 'denied_at_promise',
            stages,
            judgment_flags: [
              ...((jq['judgment_flags'] as JudgmentFlagEntry[]) ?? []),
              judgmentFlag('pact_halted_at_promise', 'see stages[0].reason. Stages 2-4 (CONFIRMATION/ACTIVATION/TRIGGER) NOT attempted (B.10: no fabrication past a denied promise).'),
            ],
            drill_pointers,
            fact_id_refs: Array.from(fact_ids),
          },
          is_error: false,
        }
      }

      // ── Stage 2: CONFIRMATION — dignity of bhāveśa + kāraka(s) IN the operative varga ──
      const grahasToConfirm: Array<{ role: 'bhavesha' | 'karaka'; name: string }> =
        [{ role: 'bhavesha', name: lordGraha }, ...karakas.map(k => ({ role: 'karaka' as const, name: k }))]
      const vargaDignities: VargaDignityRow[] = []
      for (const { role, name } of grahasToConfirm) {
        const code = GRAHA_NAME_TO_CODE[name]
        if (!code) { judgment_flags.push(judgmentFlag('confirmation_graha_unrecognized', name)); continue }
        const row = await gradeGrahaInVarga(chart_id, ayanamsha_id, operativeVarga, name, code, role)
        if (row.fact_id) fact_ids.add(row.fact_id)
        vargaDignities.push(row)
      }
      const anyDignityData = vargaDignities.some(r => r.dignity_state !== null)
      const netWeight = vargaDignities.reduce((sum, r) => sum + (r.dignity_weight ?? 0), 0)
      // Honest three-way grade — a data gap ("no rows found") is NOT the same claim as
      // "confirmed debilitated" (design B.10: never fabricate a denial from missing data).
      let confirmationStatus: 'confirmed' | 'denied' | 'inconclusive'
      let confirmationReason: string
      if (!anyDignityData) {
        confirmationStatus = 'inconclusive'
        confirmationReason = `No ${operativeVarga} dignity_state rows found for bhāveśa/kāraka(s) — data gap, not a classical denial (never fabricated per B.10). varga_confirmed row-presence: ${receipt['varga_confirmed']}.`
      } else if (netWeight <= -2) {
        confirmationStatus = 'denied'
        confirmationReason = `${operativeVarga} dignity is net-hostile (weight ${netWeight}) for the promise-carrying graha(s) — the varga does not confirm the rashi's promise. (bhaṅga/cancellation unchecked — receipt.bhanga_checked=false, so this denial does not itself rule out a classical cancellation the instrument cannot yet see.)`
      } else {
        confirmationStatus = 'confirmed'
        confirmationReason = `${operativeVarga} dignity is net-supportive or neutral (weight ${netWeight}) for the promise-carrying graha(s).`
      }
      stages.push({
        stage: 'CONFIRMATION', status: confirmationStatus, operative_varga: operativeVarga,
        dignities: vargaDignities, net_dignity_weight: netWeight, reason: confirmationReason,
      })

      if (confirmationStatus === 'denied') {
        drill_pointers.push({
          instrument: 'ganita_chart_facts_get', hint: `divisional_chart=${operativeVarga}: full ${operativeVarga} placements for every graha — this call only checked bhāveśa/kāraka dignity_state. (SC-18: was 'get_divisionals', a non-existent MCP tool name.)`,
          pointer_type: 'confirm_in_varga', pact_stage: 'confirmation',
        })
        return {
          content: {
            chart_id, ayanamsha_id, as_of_date, about,
            pact_status: 'denied_at_confirmation',
            stages,
            judgment_flags: [...judgment_flags, judgmentFlag('pact_halted_at_confirmation', 'see stages[1].reason. Stages 3-4 (ACTIVATION/TRIGGER) NOT attempted.')],
            drill_pointers,
            fact_id_refs: Array.from(fact_ids),
          },
          is_error: false,
        }
      }

      // ── Stage 3: ACTIVATION — reuse judgment_query's OWN timing_hooks fetch, no re-query ──
      const timingHooks = checklist['timing_hooks'] as Record<string, unknown>
      const currentRows = (timingHooks['current'] as Array<Record<string, unknown>>) ?? []
      const relevantNames = new Set([lordGraha, ...karakas])
      const activeNow = currentRows.filter(r => relevantNames.has(r['lord_graha'] as string))
      let activationStatus: 'active_now' | 'pending' | 'denied'
      let activationReason: string
      let nextWindowStart: string | null = null
      if (activeNow.length > 0) {
        activationStatus = 'active_now'
        activationReason = `A dasha period of the promise-carrying graha(s) is running as of ${as_of_date}: ` +
          activeNow.map(r => `${r['lord_graha']} (level ${r['level_n']}, ${r['start_date']}–${r['end_date']})`).join('; ') + '.'
      } else {
        const windowsByGraha = (timingHooks['mahadasha_windows_by_graha'] as Record<string, Array<Record<string, unknown>>>) ?? {}
        const futureStarts: string[] = []
        for (const name of relevantNames) {
          for (const w of windowsByGraha[name] ?? []) {
            const start = w['start_date'] as string | undefined
            if (start && start > as_of_date) futureStarts.push(start)
          }
        }
        if (futureStarts.length > 0) {
          futureStarts.sort()
          nextWindowStart = futureStarts[0] ?? null
          activationStatus = 'pending'
          activationReason = `No promise-carrying dasha is running now, but a future mahadasha window begins ${nextWindowStart} — pending, NOT denied (an inactive-yet-to-come window is not a broken promise).`
        } else {
          activationStatus = 'denied'
          activationReason = 'No promise-carrying dasha found running now or upcoming in the computed window (1900-2100) — ' +
            'the rashi\'s promise has no dasha vehicle left to deliver it. (Classical formulation: "the rashi does not promise it — no dasha can deliver it", design §28.3, applied here to the ACTIVATION leg specifically.)'
        }
      }
      stages.push({ stage: 'ACTIVATION', status: activationStatus, reason: activationReason, active_periods: activeNow, next_window_start: nextWindowStart })

      if (activationStatus === 'denied') {
        drill_pointers.push({
          instrument: 'ganita_dashas_get', hint: 'Full multi-level, multi-system dasha timeline (this call only checked Vimshottari mahadasha windows for the promise-carrying graha(s)).',
          pointer_type: 'dasha_of_promise', pact_stage: 'activation',
        })
        return {
          content: {
            chart_id, ayanamsha_id, as_of_date, about,
            pact_status: 'denied_at_activation',
            stages,
            judgment_flags: [...judgment_flags, judgmentFlag('pact_halted_at_activation', 'see stages[2].reason. Stage 4 (TRIGGER) NOT attempted.')],
            drill_pointers,
            fact_id_refs: Array.from(fact_ids),
          },
          is_error: false,
        }
      }

      // ── Stage 4: TRIGGER — only meaningful when a dasha is active NOW; a 'pending'
      // activation has no window yet to gate, so TRIGGER is honestly reported 'not_yet'
      // rather than fabricated against a window that has not opened. ──
      if (activationStatus === 'pending') {
        stages.push({
          stage: 'TRIGGER', status: 'not_yet',
          reason: `ACTIVATION is pending (window opens ${nextWindowStart}) — no window is open yet to check a transit gate against. Re-run pact_query with as_of_date >= ${nextWindowStart}.`,
        })
        drill_pointers.push({
          instrument: 'pact_query', hint: `Re-run with as_of_date >= ${nextWindowStart} once the promise-carrying dasha window opens.`,
          pointer_type: 'dasha_of_promise', pact_stage: 'trigger',
        })
        return {
          content: {
            chart_id, ayanamsha_id, as_of_date, about,
            pact_status: 'chain_pending_activation',
            stages, judgment_flags, drill_pointers,
            fact_id_refs: Array.from(fact_ids),
          },
          is_error: false,
        }
      }

      const triggerRows: Array<Record<string, unknown>> = []
      let triggerStatus: 'gate_data_fetched' | 'unreachable' = 'unreachable'
      let triggerReason = ''
      try {
        // CR-40 fix: forward x-api-key (see SIDECAR_API_KEY comment above) — without it
        // every one of these calls 401s when the sidecar has an API key configured, and
        // the 401 was silently read as "no rows" (res.ok false → skip), not surfaced as
        // an auth failure, so this loop could never produce a row even though the route
        // itself was live and correct.
        const triggerHeaders: Record<string, string> = { 'Content-Type': 'application/json' }
        if (SIDECAR_API_KEY) triggerHeaders['x-api-key'] = SIDECAR_API_KEY
        for (const name of relevantNames) {
          const params = new URLSearchParams({ planet: name, start_date: as_of_date, end_date: as_of_date })
          const res = await fetch(`${SIDECAR_URL}/brahmagyan/ephemeris/planet_transit?${params}`, { headers: triggerHeaders })
          if (res.ok) {
            const body = await res.json() as { rows?: Array<Record<string, unknown>> }
            triggerRows.push(...(body.rows ?? []).map(r => ({ graha: name, ...r })))
          }
        }
        triggerStatus = triggerRows.length > 0 ? 'gate_data_fetched' : 'unreachable'
        triggerReason = triggerRows.length > 0
          ? `Transiting (tropical) position fetched for ${as_of_date}. HONEST GAP: this instrument does not convert to sidereal / cross-check the classical vedha or full aspect-gate rules against the natal ${about['bhava']}th bhava — that conversion is a documented data-plane gap (same discipline as judgment_query's bhanga_checked:false), not fabricated here as an "open"/"closed" gate verdict.`
          : 'Ephemeris sidecar unreachable or returned no rows for this window — transit-gate check not completed (honest gap, not fabricated).'
      } catch (e) {
        triggerReason = `Ephemeris sidecar call failed: ${String(e)} — transit-gate check not completed (honest gap, not fabricated).`
      }
      stages.push({ stage: 'TRIGGER', status: triggerStatus, reason: triggerReason, transiting_positions: triggerRows })
      drill_pointers.push({
        instrument: 'ref_planet_transit_get', hint: 'Full transit series across the activation window (this call fetched only the single as_of_date snapshot).',
        pointer_type: 'transit_gate', pact_stage: 'trigger',
      })

      // R-22 fix: TRIGGER 'unreachable' means the ephemeris sidecar could not be reached or
      // returned no rows for this window — an INFRASTRUCTURE failure, not a genuine four-stage
      // confirmation. Reporting `pact_status: 'chain_complete'` here was false: it told the
      // caller all four classical stages were checked and passed when TRIGGER was never
      // actually evaluated. `chain_incomplete_infra` distinguishes "we tried all four stages
      // but the last one failed for infra reasons" from the genuine `chain_complete` (all four
      // stages ran AND the transit gate data was actually fetched).
      if (triggerStatus === 'unreachable') {
        drill_pointers.push({
          instrument: 'pact_query', hint: 'Re-run once the ephemeris sidecar is reachable — TRIGGER could not be evaluated this call (infra failure, not a classical denial).',
          pointer_type: 'transit_gate', pact_stage: 'trigger',
        })
        return {
          content: {
            chart_id, ayanamsha_id, as_of_date, about,
            pact_status: 'chain_incomplete_infra',
            stages,
            judgment_flags: [...judgment_flags, judgmentFlag('pact_trigger_infra_incomplete', 'the ephemeris sidecar was unreachable/empty — the chain is NOT complete despite all four stages being attempted (infra gap, not a classical denial).')],
            drill_pointers,
            resolution_chains: jq['resolution_chains'],
            fact_id_refs: Array.from(fact_ids),
          },
          is_error: false,
        }
      }

      return {
        content: {
          chart_id, ayanamsha_id, as_of_date, about,
          pact_status: 'chain_complete',
          stages,
          judgment_flags,
          drill_pointers,
          resolution_chains: jq['resolution_chains'],
          fact_id_refs: Array.from(fact_ids),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}

/**
 * Register the D10 PACT-protocol capability.
 * GATE A: only registers a NEW file for this wave — does not edit registry/index.ts.
 */
export function registerD10PactCapabilities(): void {
  registerCapability(pactQueryCapability)
}

/** D10 capability URI roster (for Gate C reverse-citation checks and roster smoke tests). */
export const D10_CAPABILITY_URIS = [
  'marsys://tool/L-PACT/pact_query',
] as const

// Auto-register on import — consistent with the D5-D9 layer pattern.
registerD10PactCapabilities()
