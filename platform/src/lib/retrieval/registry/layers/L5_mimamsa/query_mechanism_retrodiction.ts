/**
 * query_mechanism_retrodiction — mechanism_retrodiction surface (L5 Mīmāṃsā)
 * ===========================================================================
 * DOCTRINE-WAVES D-4b, Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6, unchanged content).
 *
 * "LEL events joined to the mechanism that predicts them, served as CONFIRMATION
 * ('this chart's 2H mechanism has fired N times: …') — never as prediction input.
 * Feeds L5 honestly; gives readings their retrodictive-evidence section."
 *   — BRIEF_D4B.md §1 B-5
 *
 * WHAT "MECHANISM" MEANS HERE (scoped independently of B-1's bakeoff):
 * B-1 (Grand bakeoff) is still resolving which PEAK-TIMING model wins among several
 * contenders (transit-kernel, pratyantar-lord, ensemble, …) — see BRIEF_D4B.md §1 B-1
 * / bakeoff_results/B1_BAKEOFF_STATUS_v1_0.md (BLOCKED as of this lane's open: most
 * contenders lack a real curve() implementation, zero events scored). B-5 does NOT
 * wait on that resolution and does NOT reuse an unselected bakeoff model — its own
 * spec text (both BRIEF_D4 v2.0 and BRIEF_D4B) predates the bakeoff apparatus and
 * names a narrower, already-classically-defined, already-computed mechanism:
 *
 *   The classical dasha-lord/house-activation mechanism (BPHS bhāva-dasha doctrine):
 *   a house's significations are said to manifest while that house's LORD runs as
 *   Vimshottari Mahādasha (MD) or Antardasha (AD) lord. This is WHETHER a house's
 *   lord governs the moment, not WHEN within a dasha an effect peaks (the bakeoff's
 *   question) — a coarser, independent, classically well-established join.
 *
 * GROUNDING (B.3 — every claim cites its L1 facts):
 *   - House-N's sign is derived from the LAGNA sign chart_facts row (fact_subject=
 *     'LAGNA', fact_key='sign') via the fixed whole-sign zodiacal order — a universal
 *     astronomical/astrological convention (not fabricated per-chart data), applied to
 *     a real, cited L1 fact. lagna_fact_id is echoed on every response for audit.
 *   - Domain→house significations are classical Parashari doctrine (BPHS), hardcoded
 *     as a DOCUMENTED, PARTIAL table below — only unambiguous single/dual-house
 *     significations are mapped; every other LEL domain prefix is honestly reported
 *     as unmapped (never guessed) — §N.6 density discipline (no silent flattening).
 *   - Dasha lord/period comes from chart_dashas (system_id='vimshottari', L1 Gaṇita
 *     ga_dashas asset) — each firing cites its dasha_row_id.
 *
 * SEALED TEST SPLIT (ESCALATION_POLICY §4 — gate-runner/anti-gaming territory only):
 *   This surface hard-excludes any life_events row with event_date >= 2020-01-01.
 *   The cutoff is NOT a caller-controllable parameter — it is baked into the SQL
 *   unconditionally, always, regardless of any date_from/date_to the caller supplies.
 *
 * NO-LEAKAGE: CONFIRMATION ONLY. This tool reads only events strictly in the past
 * (pre-2020) and reports historical dasha-lord/house overlaps. It emits no forward
 * projection, no probability, no future window — it must never be treated as
 * prediction input (mirrors life_events' own no-leakage contract, mimamsa_lel_intake.ts).
 * `calibration_context_only: true` + `lel_capable: true` keep it out of every
 * planner-selectable / prashna_ask surface per the NO-LEAKAGE arms 2 & 4 policy.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { DEFAULT_AYANAMSHA } from '../../constants'

/** Hard cap on served events — bounded serving (mirrors query_life_events.ts). */
const MAX_LIMIT = 50

/** Sealed test split (ESCALATION_POLICY §4). NEVER caller-overridable. */
const SEALED_TEST_SPLIT_DATE = '2020-01-01'

// ── Classical reference data (universal convention, not per-chart computation) ──

/** Fixed zodiacal order, Aries-first — used only to walk houses FROM the real LAGNA fact. */
const ZODIAC_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

/** Classical sign rulership (fixed; every tradition this codebase serves agrees on it). */
const SIGN_LORD: Record<string, string> = {
  Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
  Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
  Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn', Pisces: 'Jupiter',
}

/**
 * Domain-prefix (life_events.domain, text before '/') → classical house significations
 * (BPHS bhāva-signification doctrine). DELIBERATELY PARTIAL — only mappings with
 * low classical ambiguity are included. Any life_events domain prefix NOT in this
 * table is reported as unmapped (see `unmapped_events` in the response), never guessed.
 */
const DOMAIN_TO_HOUSES: Record<string, number[]> = {
  wealth: [2, 11],
  finance: [2, 11],
  career: [10],
  relationship: [7],
  health: [6, 8],
  spiritual: [9, 12],
  spirituality: [9, 12],
  education: [4, 5],
  family: [2, 4],
  travel: [3, 9, 12],
  loss: [8],
}

type DashaLevel = 'md' | 'ad' | 'both'

interface DashaHit {
  lord_graha: string
  level_n: number
  dasha_row_id: string
  start_date: string
  end_date: string
}

interface EventRow {
  event_id: string
  event_date: string
  domain: string | null
  description: string
  significance: string | null
  dasha_hits: DashaHit[]
}

export const queryMechanismRetrodictionCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/mechanism_retrodiction_get',
  type:  'tool',
  layer: 'L5',
  name:  'mechanism_retrodiction_get',

  description: [
    'CONFIRMATION-ONLY retrodictive evidence surface (never prediction input). Joins the',
    "chart's pre-2020 Life Event Log entries to the classical house-lord/Vimshottari-dasha",
    'activation mechanism: for each domain-mapped LEL event, reports whether that house\'s',
    'sign lord was running as Mahādasha (MD) or Antardasha (AD) lord on the event date.',
    'Returns per-house firing counts ("this chart\'s 2nd-house mechanism has fired N times"),',
    'the confirming events, events where the mapped house\'s lord was NOT active (honest',
    'non-firing), and events whose domain has no classical house mapping (honest gap — never',
    'silently dropped). Hard-excludes any event on/after 2020-01-01 (sealed test split) —',
    'not a caller-settable parameter. Feeds L5 mimamsa\'s retrodictive-evidence section.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID. Required.',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: "Ayanamsha filter (default: 'lahiri_chitrapaksha').",
      required: false,
    },
    domain: {
      type: 'string',
      description: "Filter to one domain prefix (e.g. 'wealth', 'career', 'health'). Omit for all mapped domains.",
      required: false,
    },
    house: {
      type: 'number',
      description: 'Filter to one house number (1-12). Omit to report all houses with any mapped event.',
      required: false,
    },
    dasha_level: {
      type: 'string',
      description: "Which dasha level counts as a firing: 'md', 'ad', or 'both' (default: 'both').",
      required: false,
    },
    limit: {
      type: 'number',
      description: `Max LEL events considered (default: ${MAX_LIMIT}, max: ${MAX_LIMIT}).`,
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: true,
  calibration_context_only: true,
  data_source: 'stored',

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: true,
    },
    bulk_context: {
      pre_fetch_priority: 4,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : DEFAULT_AYANAMSHA
    const domainFilter  = args['domain'] ? String(args['domain']).toLowerCase() : null
    const houseFilter   = args['house'] !== undefined && args['house'] !== null ? Number(args['house']) : null
    const dashaLevel: DashaLevel = (['md', 'ad', 'both'].includes(String(args['dasha_level'])) ? args['dasha_level'] : 'both') as DashaLevel
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    if (houseFilter !== null && (!Number.isInteger(houseFilter) || houseFilter < 1 || houseFilter > 12)) {
      return { content: { error: 'house must be an integer 1-12' }, is_error: true }
    }

    try {
      // Step 1: LAGNA sign — the real L1 fact everything else derives from. Fetched
      // separately (not CROSS JOINed) so a missing-fact condition is never confused
      // with an honest "no events" empty result.
      const lagnaRows = await query<{ lagna_sign: string; lagna_fact_id: string }>(
        `SELECT fact_value_text AS lagna_sign, fact_id AS lagna_fact_id
         FROM chart_facts
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_subject = 'LAGNA' AND fact_key = 'sign'
         LIMIT 1`,
        [chart_id, ayanamsha_id],
      )
      const lagnaSign = lagnaRows.rows[0]?.lagna_sign
      const lagnaFactId = lagnaRows.rows[0]?.lagna_fact_id
      if (!lagnaSign || !ZODIAC_SIGNS.includes(lagnaSign as typeof ZODIAC_SIGNS[number])) {
        return {
          content: {
            error: `LAGNA sign not resolvable from chart_facts for chart_id=${chart_id}, ayanamsha_id=${ayanamsha_id} — cannot derive house-lord mapping.`,
            chart_id, ayanamsha_id,
          },
          is_error: true,
        }
      }

      // Step 2: pre-2020 events + all overlapping vimshottari MD/AD spans, one round-trip.
      // SEALED_TEST_SPLIT_DATE is bound as a parameter (never string-concatenated from
      // caller input) — there is no code path through which a caller can widen it.
      const levelFilter = dashaLevel === 'md' ? 'AND d.level_n = 1' : dashaLevel === 'ad' ? 'AND d.level_n = 2' : 'AND d.level_n IN (1, 2)'

      const sql = `
        WITH events AS (
          SELECT event_id, to_char(event_date, 'YYYY-MM-DD') AS event_date_str, event_date,
                 domain, description, significance
          FROM life_events
          WHERE chart_id = $1 AND event_date < $3::date
          ORDER BY event_date ASC
          LIMIT $4
        )
        SELECT e.event_id, e.event_date_str AS event_date, e.domain, e.description, e.significance,
               d.lord_graha, d.level_n, d.dasha_row_id,
               to_char(d.start_date, 'YYYY-MM-DD') AS dasha_start,
               to_char(d.end_date, 'YYYY-MM-DD')   AS dasha_end
        FROM events e
        LEFT JOIN chart_dashas d
          ON d.chart_id = $1 AND d.ayanamsha_id = $2 AND d.system_id = 'vimshottari'
          ${levelFilter}
          AND d.start_date <= e.event_date AND d.end_date >= e.event_date
        ORDER BY e.event_date ASC, d.level_n ASC
      `
      const rows = await query<Record<string, unknown>>(sql, [chart_id, ayanamsha_id, SEALED_TEST_SPLIT_DATE, limit])

      if (rows.rows.length === 0) {
        return {
          content: {
            chart_id,
            ayanamsha_id,
            lagna_sign: lagnaSign,
            mechanisms: [],
            unmapped_events: [],
            not_confirmed_events: [],
            usage_note: 'CONFIRMATION ONLY — historical retrodictive evidence. Never use as prediction input.',
            sealed_test_split_note: `Events on/after ${SEALED_TEST_SPLIT_DATE} are excluded from this surface unconditionally (sealed test split, ESCALATION_POLICY §4) — gate-runner/anti-gaming territory only.`,
            empty_reason: 'no_pre_2020_life_events_for_chart',
          },
          is_error: false,
        }
      }

      const lagnaIdx = ZODIAC_SIGNS.indexOf(lagnaSign as typeof ZODIAC_SIGNS[number])
      const houseSign = (h: number) => ZODIAC_SIGNS[(lagnaIdx + h - 1) % 12]
      const houseLord = (h: number) => SIGN_LORD[houseSign(h)]

      // Group flattened rows back into one entry per event.
      const eventMap = new Map<string, EventRow>()
      for (const row of rows.rows as Array<Record<string, unknown>>) {
        const event_id = String(row['event_id'])
        if (!eventMap.has(event_id)) {
          eventMap.set(event_id, {
            event_id,
            event_date: String(row['event_date']),
            domain: (row['domain'] as string | null) ?? null,
            description: String(row['description']),
            significance: (row['significance'] as string | null) ?? null,
            dasha_hits: [],
          })
        }
        if (row['lord_graha']) {
          eventMap.get(event_id)!.dasha_hits.push({
            lord_graha: String(row['lord_graha']),
            level_n: Number(row['level_n']),
            dasha_row_id: String(row['dasha_row_id']),
            start_date: String(row['dasha_start']),
            end_date: String(row['dasha_end']),
          })
        }
      }

      type MechanismAgg = {
        house: number
        house_sign: string
        house_lord: string
        domains_signified: string[]
        fired_count: number
        fired_events: Array<{
          event_id: string; event_date: string; domain: string | null
          dasha_level: 'MD' | 'AD'; dasha_lord: string; dasha_row_id: string
        }>
      }
      const mechanisms = new Map<number, MechanismAgg>()
      const unmapped_events: Array<{ event_id: string; event_date: string; domain: string | null; reason: string }> = []
      const not_confirmed_events: Array<{ event_id: string; event_date: string; domain: string | null; mapped_houses: number[]; reason: string }> = []

      for (const ev of eventMap.values()) {
        const domainPrefix = (ev.domain ?? '').split('/')[0]?.toLowerCase() ?? ''
        if (domainFilter && domainPrefix !== domainFilter) continue

        const mappedHouses = (DOMAIN_TO_HOUSES[domainPrefix] ?? []).filter(
          (h) => houseFilter === null || h === houseFilter,
        )

        if (mappedHouses.length === 0) {
          if (!(domainPrefix in DOMAIN_TO_HOUSES)) {
            unmapped_events.push({
              event_id: ev.event_id, event_date: ev.event_date, domain: ev.domain,
              reason: `no classical house mapping for domain prefix '${domainPrefix}'`,
            })
          }
          continue
        }

        let confirmedAny = false
        for (const house of mappedHouses) {
          const lord = houseLord(house)
          const hit = ev.dasha_hits.find((d) => d.lord_graha === lord)
          if (hit) {
            confirmedAny = true
            if (!mechanisms.has(house)) {
              mechanisms.set(house, {
                house, house_sign: houseSign(house), house_lord: lord,
                domains_signified: Object.entries(DOMAIN_TO_HOUSES).filter(([, hs]) => hs.includes(house)).map(([d]) => d),
                fired_count: 0, fired_events: [],
              })
            }
            const m = mechanisms.get(house)!
            m.fired_count += 1
            m.fired_events.push({
              event_id: ev.event_id, event_date: ev.event_date, domain: ev.domain,
              dasha_level: hit.level_n === 1 ? 'MD' : 'AD', dasha_lord: hit.lord_graha,
              dasha_row_id: hit.dasha_row_id,
            })
          }
        }
        if (!confirmedAny) {
          not_confirmed_events.push({
            event_id: ev.event_id, event_date: ev.event_date, domain: ev.domain,
            mapped_houses: mappedHouses,
            reason: `neither MD nor AD lord matched house ${mappedHouses.join('/')}'s lord (${mappedHouses.map(houseLord).join('/')}) on this date`,
          })
        }
      }

      return {
        content: {
          chart_id,
          ayanamsha_id,
          lagna_sign: lagnaSign,
          mechanisms: Array.from(mechanisms.values()).sort((a, b) => b.fired_count - a.fired_count),
          unmapped_events,
          not_confirmed_events,
          usage_note: 'CONFIRMATION ONLY — historical retrodictive evidence from dasha-lord/house-activation overlap with observed LEL events. Never use as prediction input; feeds L5 retrodictive-evidence section only.',
          sealed_test_split_note: `Events on/after ${SEALED_TEST_SPLIT_DATE} are excluded from this surface unconditionally (sealed test split, ESCALATION_POLICY §4) — gate-runner/anti-gaming territory only.`,
          mechanism_scope_note: "Reports the classical dasha-lord/house-activation mechanism only (BPHS bhāva-dasha doctrine) — independent of B-1's still-resolving peak-timing bakeoff. domains_signified lists ALL DOMAIN_TO_HOUSES prefixes mapped to that house, not just the domain(s) observed in this response.",
          provenance: {
            tables: ['life_events', 'chart_dashas', 'chart_facts'],
            lagna_fact_id: lagnaFactId,
            grounding: 'house_sign = whole-sign walk from chart_facts LAGNA sign (lagna_fact_id); house_lord = classical fixed sign rulership; dasha spans = chart_dashas (system_id=vimshottari), each firing cites dasha_row_id.',
            no_leakage_note: 'life_events is a calibration corpus only — must not feed prediction generation. This tool is CONFIRMATION-ONLY.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
