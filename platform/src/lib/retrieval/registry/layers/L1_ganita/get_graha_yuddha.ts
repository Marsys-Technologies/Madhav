/**
 * L1 retrieval: graha_yuddha (planetary war) winner — JL-027 Option A serve-time overlay
 * =========================================================================================
 * Tool: marsys://tool/L1/get_graha_yuddha
 *
 * BACKGROUND (JL-027, BA_JUDGMENT_LEDGER_v1_0.md; ruling doc
 * 00_ARCHITECTURE/JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md):
 * `ga_structural_writer._build_graha_yuddha_rows` (a BUILD-TIME writer — must_not_touch per
 * this brief's scope) detects graha yuddha (two classical grahas within orb <=1.0 deg, same
 * sign) and stores winner=NULL, loser=NULL, reason='no_ratified_classical_rule',
 * floored:true on every row, because the ratified classical method (Option A — Parasari
 * northern-latitude rule) needs Swiss Ephemeris ecliptic latitude, which was not available
 * to the writer at build time. The uncited "lower/higher longitude wins" proxy was REMOVED
 * and is FORBIDDEN from ever being reintroduced (canonical-or-floor doctrine).
 *
 * THIS CAPABILITY (R5.1 C2 item 6) implements Option A at SERVE TIME, as a read-only overlay:
 * - chart_facts.graha_yuddha rows (the floor) are read but NEVER written back to (read-only
 *   on L0-L5 chart data, per this brief's must_not_touch).
 * - The two combatants' ecliptic latitude at the chart's birth date is read from
 *   `ephemeris_daily.latitude` — an L0 (Brahmagyan) column ALREADY computed and stored by the
 *   bg_ephemeris writer (1900-01-01 .. 2150-12-31, 9 bodies). Exposing it here does not
 *   require any new build-time asset; it is a plain additional SELECT on existing data.
 * - Where both combatants have a latitude row for the birth date AND at least one of them is
 *   a tara-graha-eligible pair, Option A is applied and a winner/loser is surfaced --
 *   OVERLAID on the response, not written into chart_facts.
 * - Where the pair is NOT eligible (Sun/Moon/Rahu/Ketu never fight per classical doctrine) or
 *   ephemeris_daily has no row for the birth date (pre-1900 / post-2150), the floor is
 *   returned UNCHANGED with its original reason -- the uncited longitude proxy is never
 *   substituted, per doctrine.
 *
 * CITATION (Option A, "Parasari northern-latitude rule"):
 * - Brhat Parasara Hora Sastra, graha-yuddha treatment: "Venus is the conqueror whether in
 *   North or South; among the other four [Mars, Mercury, Jupiter, Saturn] the one in the
 *   North is the conqueror, that in the South is defeated."
 * - Brhat Samhita (Varahamihira), Grahayuddhadhyaya ch. 17: the northern/brighter planet is
 *   jayin (victor); the southern is parajita (defeated).
 * (Exact chapter/verse numbers flagged in JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md §5
 * as owing critical-edition verification before ledger-final citation; the RULE SUBSTANCE
 * above is what is applied here, per the native's 2026-07-08 ratification of Option A.)
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '../../../address_resolver'

const OPTION_A_CITATION =
  'Brhat Parasara Hora Sastra (graha-yuddha sloka): Venus is conqueror whether North or South; ' +
  'among Mars/Mercury/Jupiter/Saturn the one further North is conqueror. Corroborated by ' +
  'Brhat Samhita (Varahamihira), Grahayuddhadhyaya ch.17 (northern/brighter = jayin, southern ' +
  '= parajita). Verse numbers pending critical-edition verification ' +
  '(JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md §5).'

// Tara-graha eligibility for graha yuddha (BPHS): only these five ever fight. Sun/Moon/Rahu/Ketu
// are never combatants, regardless of what the (must_not_touch) writer floored.
const TARA_GRAHA_SUBJECTS = new Set(['MAR', 'MER', 'JUP', 'VEN', 'SAT'])

// fact_subject code -> ephemeris_daily.body name. Values sourced from the
// graha SSoT (address_resolver.grahaCodeOf + GRAHA_CODE_TO_NAME) rather
// than hardcoded literals — ADHIṢṬHĀNA Lane A2.
const SUBJECT_TO_EPHEMERIS_BODY: Record<string, string> = Object.fromEntries(
  ['MAR', 'MER', 'JUP', 'VEN', 'SAT'].map(code => [code, GRAHA_CODE_TO_NAME[grahaCodeOf(code)]]),
)

function splitPairKey(pairKey: string): [string, string] | null {
  const parts = pairKey.split('_v_')
  if (parts.length !== 2 || !parts[0] || !parts[1]) return null
  return [parts[0], parts[1]]
}

/** Option A winner resolution given each combatant's ecliptic latitude (degrees, +north/-south). */
function resolveOptionAWinner(
  subjA: string, latA: number,
  subjB: string, latB: number,
): { winner: string; loser: string; note: string } | null {
  // Venus wins regardless of direction, by exceptional brilliance (BPHS).
  if (subjA === 'VEN' && subjB !== 'VEN') {
    return { winner: subjA, loser: subjB, note: 'Venus is held to conquer regardless of North/South (BPHS).' }
  }
  if (subjB === 'VEN' && subjA !== 'VEN') {
    return { winner: subjB, loser: subjA, note: 'Venus is held to conquer regardless of North/South (BPHS).' }
  }
  // Otherwise the more-northern latitude wins (north positive, south negative — "greater"
  // correctly ranks north-over-south, and among two souths the less-southern one).
  if (latA > latB) {
    return { winner: subjA, loser: subjB, note: `${subjA} is more Northern (${latA.toFixed(4)} deg vs ${latB.toFixed(4)} deg).` }
  }
  if (latB > latA) {
    return { winner: subjB, loser: subjA, note: `${subjB} is more Northern (${latB.toFixed(4)} deg vs ${latA.toFixed(4)} deg).` }
  }
  return null // exactly equal latitude — indeterminate; leave floored
}

export const getGrahaYuddhaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_graha_yuddha',
  type: 'tool',
  layer: 'L1',
  name: 'get_graha_yuddha',
  scope: 'per_chart',
  description: [
    'Graha yuddha (planetary war): pairs of tara-grahas (Mars/Mercury/Jupiter/Venus/Saturn) within',
    '1 deg orb in the same sign, and their winner per JL-027 Option A (Parasari northern-latitude',
    'rule -- Venus always wins; else the more-northern ecliptic latitude wins), computed at serve',
    'time from ephemeris_daily.latitude (already-computed L0 data, chart-agnostic by date) joined',
    "against the chart's birth date. chart_facts.graha_yuddha itself remains FLOORED",
    '(winner=NULL, reason=no_ratified_classical_rule) -- this tool overlays the ratified,',
    'cited winner for presentation without writing back to chart data. Where the pair is not',
    'tara-graha-eligible, or ephemeris_daily has no row for the birth date (outside 1900-2150),',
    'the floor is returned unchanged and the uncited longitude proxy is never substituted.',
  ].join(' '),
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all ayanamshas present.' },
  },
  required_inputs: ['chart_id'],
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chart_id = args.chart_id as string
      if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }
      const ayanamsha_id = args.ayanamsha_id as string | undefined

      const params: unknown[] = [chart_id]
      let where = `chart_id = $1 AND fact_category = 'graha_yuddha'`
      if (ayanamsha_id) {
        params.push(ayanamsha_id)
        where += ` AND ayanamsha_id = $${params.length}`
      }

      const [factRows, chartRows] = await Promise.all([
        query<{
          fact_id: string; fact_subject: string; fact_key: string;
          ayanamsha_id: string; fact_value_jsonb: Record<string, unknown> | null;
        }>(
          `SELECT fact_id, fact_subject, fact_key, ayanamsha_id, fact_value_jsonb
           FROM chart_facts WHERE ${where}
           ORDER BY ayanamsha_id, fact_subject, fact_key`,
          params,
        ),
        query<{ birth_date: string }>(
          `SELECT birth_date::text AS birth_date FROM charts WHERE id = $1`,
          [chart_id],
        ),
      ])

      const birthDate = chartRows.rows[0]?.birth_date ?? null

      // Group by (ayanamsha_id, pair_key)
      type PairGroup = {
        ayanamsha_id: string; pair_key: string;
        orb_deg: number | null; sign: string | null;
        floor_fact_ids: string[];
      }
      const groups = new Map<string, PairGroup>()
      for (const row of factRows.rows) {
        const key = `${row.ayanamsha_id}::${row.fact_subject}`
        if (!groups.has(key)) {
          groups.set(key, {
            ayanamsha_id: row.ayanamsha_id, pair_key: row.fact_subject,
            orb_deg: null, sign: null, floor_fact_ids: [],
          })
        }
        const g = groups.get(key)!
        g.floor_fact_ids.push(row.fact_id)
        const jsonb = row.fact_value_jsonb ?? {}
        if (typeof jsonb['orb_deg'] === 'number') g.orb_deg = jsonb['orb_deg'] as number
        if (typeof jsonb['sign'] === 'string') g.sign = jsonb['sign'] as string
      }

      // Resolve ephemeris bodies we need to look up (dedup across all pairs)
      const bodiesNeeded = new Set<string>()
      for (const g of groups.values()) {
        const pair = splitPairKey(g.pair_key)
        if (!pair) continue
        for (const subj of pair) {
          if (TARA_GRAHA_SUBJECTS.has(subj)) bodiesNeeded.add(SUBJECT_TO_EPHEMERIS_BODY[subj]!)
        }
      }

      const latByBody = new Map<string, number>()
      let ephemerisNote: string | null = null
      if (birthDate && bodiesNeeded.size > 0) {
        const ephResult = await query<{ body: string; latitude: string | null }>(
          `SELECT body, latitude FROM ephemeris_daily
           WHERE date = $1::date AND ayanamsha_id = 'tropical' AND body = ANY($2::text[])`,
          [birthDate, Array.from(bodiesNeeded)],
        )
        for (const r of ephResult.rows) {
          if (r.latitude !== null) latByBody.set(r.body, Number(r.latitude))
        }
        if (latByBody.size < bodiesNeeded.size) {
          ephemerisNote = 'ephemeris_daily has no row for one or more bodies at this birth date ' +
            '(outside 1900-01-01..2150-12-31 coverage) — floor retained for those pairs.'
        }
      } else if (!birthDate) {
        ephemerisNote = 'chart birth_date not found — floor retained for all pairs.'
      }

      const pairs = Array.from(groups.values()).map(g => {
        const pair = splitPairKey(g.pair_key)
        const base = {
          pair_key: g.pair_key,
          ayanamsha_id: g.ayanamsha_id,
          sign: g.sign,
          orb_deg: g.orb_deg,
          floor_fact_ids: g.floor_fact_ids,
        }
        if (!pair) {
          return { ...base, winner: null, loser: null, method: 'floored', reason: 'unparseable_pair_key' }
        }
        const [subjA, subjB] = pair
        const eligible = TARA_GRAHA_SUBJECTS.has(subjA) && TARA_GRAHA_SUBJECTS.has(subjB)
        if (!eligible) {
          return {
            ...base, winner: null, loser: null, method: 'floored',
            reason: 'no_ratified_classical_rule',
            note: 'Not a tara-graha pair — Sun/Moon/Rahu/Ketu never fight per classical doctrine; Option A inapplicable.',
          }
        }
        const bodyA = SUBJECT_TO_EPHEMERIS_BODY[subjA]!
        const bodyB = SUBJECT_TO_EPHEMERIS_BODY[subjB]!
        const latA = latByBody.get(bodyA)
        const latB = latByBody.get(bodyB)
        if (latA === undefined || latB === undefined) {
          return {
            ...base, winner: null, loser: null, method: 'floored',
            reason: 'no_ratified_classical_rule',
            note: 'Ecliptic latitude unavailable for one or both combatants at this birth date — floor retained (canonical-or-floor; no proxy substitution).',
          }
        }
        const resolved = resolveOptionAWinner(subjA, latA, subjB, latB)
        if (!resolved) {
          return {
            ...base, winner: null, loser: null, method: 'floored',
            reason: 'latitude_tie_indeterminate',
            note: `Latitudes exactly equal (${latA} deg) — indeterminate under Option A.`,
          }
        }
        return {
          ...base,
          winner: resolved.winner,
          loser: resolved.loser,
          method: 'option_a_northern_latitude',
          citation: OPTION_A_CITATION,
          note: resolved.note,
          derivation_ledger: {
            rule: 'JL-027 Option A (Parasari northern-latitude)',
            constituent_facts: [
              { subject: subjA, ecliptic_latitude_deg: latA, source: `ephemeris_daily(date=${birthDate}, body=${bodyA}, ayanamsha_id=tropical)` },
              { subject: subjB, ecliptic_latitude_deg: latB, source: `ephemeris_daily(date=${birthDate}, body=${bodyB}, ayanamsha_id=tropical)` },
            ],
            floored_source_fact_ids: g.floor_fact_ids,
          },
        }
      })

      return {
        content: {
          chart_id,
          birth_date: birthDate,
          pairs,
          total: pairs.length,
          provenance: {
            note: 'chart_facts.graha_yuddha remains FLOORED at rest (winner=NULL); this is a serve-time, ' +
              'read-only overlay per JL-027 Option A. No chart data was written.',
            ephemeris_note: ephemerisNote,
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
