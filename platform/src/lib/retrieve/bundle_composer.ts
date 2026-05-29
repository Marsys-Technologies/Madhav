/**
 * INF7-S1: Chart Bundle Composer
 * compose_chart_bundle(chart_id, ayanamshas) → ChartBundle
 *
 * Fetches a structured, token-budgeted snapshot of a chart from chart_facts
 * for use as Layer-1 prompt context in the Consume Hybrid agentic loop.
 * No prose — structured data only. Target: ≤8 000 tokens.
 *
 * Data model: queries BOTH old model (category col) and new A3+ model
 * (fact_category col) so builds from both eras are covered.
 *
 * [BUILD-ORCH-J-02] INF7-S1
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Constants ─────────────────────────────────────────────────────────────────

const CANONICAL_AYANAMSHAS = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

const TOKEN_BUDGET = 8_000

// ── Public types ──────────────────────────────────────────────────────────────

export interface PlanetSnapshot {
  planet: string
  sign: string | null
  house: number | null
  longitude_deg: number | null
  nakshatra: string | null
  pada: number | null
  retro: boolean
  dignity: string | null
}

export interface HouseCusp {
  house: number
  sign: string | null
  cusp_deg: number | null
  lord: string | null
}

export interface DashaNode {
  level: 'maha' | 'antar' | 'pratyantar'
  lord: string
  start_date: string | null
  end_date: string | null
}

export interface ActiveYoga {
  yoga_name: string
  status: string | null
  strength: number | null
  planets_involved: string | null
}

export interface BirthPanchanga {
  tithi: string | null
  tithi_num: number | null
  paksha: string | null
  vara: string | null
  moon_nakshatra: string | null
  yoga: string | null
  karana: string | null
  sunrise_iso: string | null
  sunset_iso: string | null
}

export interface CrossAyanamshaEntry {
  ayanamsha_1: string
  ayanamsha_2: string
  divergence_score: number | null
  max_delta_deg: number | null
}

export interface AyanamshaSlice {
  ayanamsha_id: string
  planets: PlanetSnapshot[]
  houses: HouseCusp[]
  dasha_chain: DashaNode[]
}

export interface ChartBundle {
  chart_id: string
  ayanamshas_requested: string[]
  ayanamshas_found: string[]
  birth_panchanga: BirthPanchanga
  active_yogas: ActiveYoga[]
  ayanamsha_slices: AyanamshaSlice[]
  cross_ayanamsha: CrossAyanamshaEntry[]
  token_estimate: number
  generated_at: string
}

// ── DB row shapes ─────────────────────────────────────────────────────────────

interface OldFactRow {
  category: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
}

interface NewFactRow {
  fact_category: string
  fact_subject: string
  fact_key: string
  ayanamsha_id: string
  fact_value_text: string | null
  fact_value_num: number | null
}

interface AyanamshaReportRow {
  ayanamsha_id_1: string
  ayanamsha_id_2: string
  divergence_score: number | null
  max_position_delta_deg: number | null
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function compose_chart_bundle(
  chart_id: string,
  ayanamshas: string[],
): Promise<ChartBundle> {
  const now = new Date().toISOString()

  // Clamp to known canonical ayanamshas; default to all 5 if empty
  const requested =
    ayanamshas.length > 0
      ? ayanamshas.filter((a) => (CANONICAL_AYANAMSHAS as readonly string[]).includes(a))
      : [...CANONICAL_AYANAMSHAS]

  const today = now.split('T')[0]!

  const [oldRows, newRows, panchangaRows, crossRows] = await Promise.all([
    fetchOldModel(chart_id, requested),
    fetchNewModel(chart_id, requested, today),
    fetchPanchanga(chart_id),
    fetchCrossAyanamsha(chart_id),
  ])

  const ayanamsha_slices = buildSlices(requested, oldRows, newRows, today)
  const found = ayanamsha_slices
    .filter((s) => s.planets.length > 0 || s.houses.length > 0)
    .map((s) => s.ayanamsha_id)

  const active_yogas = extractYogas(oldRows)
  const birth_panchanga = extractPanchanga(panchangaRows, oldRows)
  const cross_ayanamsha = crossRows.map((r) => ({
    ayanamsha_1: r.ayanamsha_id_1,
    ayanamsha_2: r.ayanamsha_id_2,
    divergence_score: r.divergence_score,
    max_delta_deg: r.max_position_delta_deg,
  }))

  const bundle: ChartBundle = {
    chart_id,
    ayanamshas_requested: requested,
    ayanamshas_found: found,
    birth_panchanga,
    active_yogas: active_yogas.slice(0, 20),
    ayanamsha_slices,
    cross_ayanamsha,
    token_estimate: 0,
    generated_at: now,
  }

  bundle.token_estimate = estimateTokens(bundle)
  return trimTobudget(bundle)
}

// ── Fetchers ──────────────────────────────────────────────────────────────────

async function fetchOldModel(chart_id: string, ayanamshas: string[]): Promise<OldFactRow[]> {
  const CATEGORIES = ['planet', 'house', 'dasha_vimshottari', 'yoga', 'panchang', 'shadbala']
  const { rows } = await query<OldFactRow>(
    `SELECT category, value_text, value_number, value_json
       FROM chart_facts
      WHERE chart_id = $1
        AND (ayanamsha_id = ANY($2::text[]) OR ayanamsha_id = 'INVARIANT')
        AND category = ANY($3::text[])
        AND is_stale = false
      LIMIT 500`,
    [chart_id, ayanamshas, CATEGORIES],
  )
  return rows
}

async function fetchNewModel(
  chart_id: string,
  ayanamshas: string[],
  today: string,
): Promise<NewFactRow[]> {
  const FACT_CAT_PREFIXES = [
    'planet_positions',
    'house_positions',
    'dasha_vimshottari',
    'dasha_chara',
    'panchanga_',
    'yoga_',
    'dosha_',
  ]
  const likeConditions = FACT_CAT_PREFIXES.map(
    (_, i) => `fact_category LIKE $${i + 3}`,
  ).join(' OR ')

  const params: unknown[] = [
    chart_id,
    [...ayanamshas, 'INVARIANT'],
    ...FACT_CAT_PREFIXES.map((p) => `${p}%`),
  ]

  const { rows } = await query<NewFactRow>(
    `SELECT fact_category, fact_subject, fact_key, ayanamsha_id,
            fact_value_text, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1
        AND (ayanamsha_id = ANY($2::text[]) OR ayanamsha_id = 'INVARIANT')
        AND (${likeConditions})
        AND is_stale = false
      LIMIT 800`,
    params,
  )
  return rows
}

async function fetchPanchanga(chart_id: string): Promise<NewFactRow[]> {
  const { rows } = await query<NewFactRow>(
    `SELECT fact_category, fact_subject, fact_key, ayanamsha_id,
            fact_value_text, fact_value_num
       FROM chart_facts
      WHERE chart_id = $1
        AND fact_category LIKE 'panchanga_%'
        AND is_stale = false
      LIMIT 100`,
    [chart_id],
  )
  return rows
}

async function fetchCrossAyanamsha(chart_id: string): Promise<AyanamshaReportRow[]> {
  try {
    const { rows } = await query<AyanamshaReportRow>(
      `SELECT ayanamsha_id_1, ayanamsha_id_2, divergence_score, max_position_delta_deg
         FROM chart_ayanamsha_reports
        WHERE chart_id = $1
        ORDER BY divergence_score DESC NULLS LAST
        LIMIT 10`,
      [chart_id],
    )
    return rows
  } catch {
    // Table may not exist in older deployments
    return []
  }
}

// ── Builders ──────────────────────────────────────────────────────────────────

function buildSlices(
  ayanamshas: string[],
  oldRows: OldFactRow[],
  newRows: NewFactRow[],
  today: string,
): AyanamshaSlice[] {
  return ayanamshas.map((aya) => {
    const planets = extractPlanets(aya, oldRows, newRows)
    const houses = extractHouses(aya, oldRows, newRows)
    const dasha_chain = extractDasha(aya, oldRows, newRows, today)
    return { ayanamsha_id: aya, planets, houses, dasha_chain }
  })
}

function extractPlanets(
  aya: string,
  oldRows: OldFactRow[],
  newRows: NewFactRow[],
): PlanetSnapshot[] {
  const map = new Map<string, PlanetSnapshot>()

  // Old model: category='planet', value_json has planet data
  for (const r of oldRows) {
    if (r.category !== 'planet' || !r.value_json) continue
    const j = r.value_json
    const name = (j['planet'] as string | undefined) ?? ''
    if (!name) continue
    if (!map.has(name)) {
      map.set(name, {
        planet: name,
        sign: (j['sign'] as string | null) ?? null,
        house: asInt(j['house']),
        longitude_deg: asFloat(j['longitude']),
        nakshatra: (j['nakshatra'] as string | null) ?? null,
        pada: asInt(j['pada']),
        retro: Boolean(j['retro'] ?? j['retrograde']),
        dignity: (j['dignity'] as string | null) ?? null,
      })
    }
  }

  // New model: fact_category='planet_positions', fact_subject=PLANET_NAME
  const newPlanetRows = newRows.filter(
    (r) =>
      r.fact_category === 'planet_positions' &&
      (r.ayanamsha_id === aya || r.ayanamsha_id === 'INVARIANT'),
  )
  const grouped = groupBy(newPlanetRows, (r) => r.fact_subject)
  for (const [planet, rows] of grouped) {
    if (map.has(planet)) continue
    const kv = toKV(rows)
    map.set(planet, {
      planet,
      sign: kv['sign'] ?? null,
      house: kv['house'] ? parseInt(kv['house'], 10) : null,
      longitude_deg: kv['longitude'] ? parseFloat(kv['longitude']) : null,
      nakshatra: kv['nakshatra'] ?? null,
      pada: kv['pada'] ? parseInt(kv['pada'], 10) : null,
      retro: kv['retro'] === 'true' || kv['retrograde'] === 'true',
      dignity: kv['dignity'] ?? null,
    })
  }

  return [...map.values()]
}

function extractHouses(
  aya: string,
  oldRows: OldFactRow[],
  newRows: NewFactRow[],
): HouseCusp[] {
  const map = new Map<number, HouseCusp>()

  for (const r of oldRows) {
    if (r.category !== 'house' || !r.value_json) continue
    const j = r.value_json
    const h = asInt(j['house'])
    if (!h) continue
    if (!map.has(h)) {
      map.set(h, {
        house: h,
        sign: (j['sign'] as string | null) ?? null,
        cusp_deg: asFloat(j['cusp_deg'] ?? j['longitude']),
        lord: (j['lord'] as string | null) ?? null,
      })
    }
  }

  const newHouseRows = newRows.filter(
    (r) =>
      r.fact_category === 'house_positions' &&
      (r.ayanamsha_id === aya || r.ayanamsha_id === 'INVARIANT'),
  )
  const grouped = groupBy(newHouseRows, (r) => r.fact_subject)
  for (const [subj, rows] of grouped) {
    const hNum = parseInt(subj.replace(/\D/g, ''), 10)
    if (!hNum || map.has(hNum)) continue
    const kv = toKV(rows)
    map.set(hNum, {
      house: hNum,
      sign: kv['sign'] ?? null,
      cusp_deg: kv['cusp_deg'] ? parseFloat(kv['cusp_deg']) : null,
      lord: kv['lord'] ?? null,
    })
  }

  return [...map.values()].sort((a, b) => a.house - b.house)
}

function extractDasha(
  aya: string,
  oldRows: OldFactRow[],
  newRows: NewFactRow[],
  today: string,
): DashaNode[] {
  const chain: DashaNode[] = []

  // Old model: category='dasha_vimshottari', value_json with level/lord/start/end
  for (const r of oldRows) {
    if (r.category !== 'dasha_vimshottari' || !r.value_json) continue
    const j = r.value_json
    const start = (j['start_date'] as string | null) ?? null
    const end = (j['end_date'] as string | null) ?? null
    if (start && end && today >= start && today < end) {
      chain.push({
        level: (j['level'] as DashaNode['level']) ?? 'maha',
        lord: (j['lord'] as string) ?? '',
        start_date: start,
        end_date: end,
      })
    }
  }

  if (chain.length === 0) {
    // New model fallback
    const dashaRows = newRows.filter(
      (r) =>
        r.fact_category.startsWith('dasha_') &&
        (r.ayanamsha_id === aya || r.ayanamsha_id === 'INVARIANT'),
    )
    const bySubj = groupBy(dashaRows, (r) => r.fact_subject)
    for (const [subj, rows] of bySubj) {
      const kv = toKV(rows)
      const start = kv['start_date'] ?? null
      const end = kv['end_date'] ?? null
      if (!start || !end) continue
      if (today >= start && today < end) {
        chain.push({
          level: (kv['level'] as DashaNode['level']) ?? 'maha',
          lord: kv['lord'] ?? subj,
          start_date: start,
          end_date: end,
        })
      }
    }
  }

  // Sort by level depth: maha < antar < pratyantar
  const ORDER: Record<string, number> = { maha: 0, antar: 1, pratyantar: 2 }
  return chain.sort((a, b) => (ORDER[a.level] ?? 9) - (ORDER[b.level] ?? 9))
}

function extractYogas(oldRows: OldFactRow[]): ActiveYoga[] {
  const yogas: ActiveYoga[] = []
  for (const r of oldRows) {
    if (r.category !== 'yoga' || !r.value_json) continue
    const j = r.value_json
    yogas.push({
      yoga_name: (j['yoga_name'] as string) ?? (j['name'] as string) ?? '',
      status: (j['status'] as string | null) ?? null,
      strength: asFloat(j['strength'] ?? j['score']),
      planets_involved: (j['planets'] as string | null) ?? null,
    })
  }
  return yogas
    .filter((y) => y.yoga_name)
    .sort((a, b) => (b.strength ?? 0) - (a.strength ?? 0))
}

function extractPanchanga(
  panchangaRows: NewFactRow[],
  oldRows: OldFactRow[],
): BirthPanchanga {
  const kv: Record<string, string> = {}
  for (const r of panchangaRows) {
    if (r.fact_value_text) kv[r.fact_key] = r.fact_value_text
    else if (r.fact_value_num != null) kv[r.fact_key] = String(r.fact_value_num)
  }

  // Fallback: old model category='panchang'
  if (!kv['tithi']) {
    for (const r of oldRows) {
      if (r.category !== 'panchang' || !r.value_json) continue
      const j = r.value_json
      if (j['tithi']) kv['tithi'] = String(j['tithi'])
      if (j['vara']) kv['vara'] = String(j['vara'])
      if (j['nakshatra']) kv['nakshatra'] = String(j['nakshatra'])
      if (j['yoga']) kv['yoga'] = String(j['yoga'])
      if (j['karana']) kv['karana'] = String(j['karana'])
    }
  }

  return {
    tithi: kv['tithi_name'] ?? kv['tithi'] ?? null,
    tithi_num: kv['tithi_number'] ? parseInt(kv['tithi_number'], 10) : null,
    paksha: kv['paksha'] ?? null,
    vara: kv['vara_name'] ?? kv['vara'] ?? null,
    moon_nakshatra: kv['moon_nakshatra'] ?? kv['nakshatra'] ?? null,
    yoga: kv['yoga_name'] ?? kv['yoga'] ?? null,
    karana: kv['karana_name'] ?? kv['karana'] ?? null,
    sunrise_iso: kv['sunrise_iso'] ?? kv['sunrise'] ?? null,
    sunset_iso: kv['sunset_iso'] ?? kv['sunset'] ?? null,
  }
}

// ── Token budget ──────────────────────────────────────────────────────────────

function estimateTokens(bundle: ChartBundle): number {
  return Math.ceil(JSON.stringify(bundle).length / 4)
}

function trimTobudget(bundle: ChartBundle): ChartBundle {
  if (bundle.token_estimate <= TOKEN_BUDGET) return bundle

  // Trim: reduce planets per slice to essentials (9 grahas), cap yogas at 10
  const trimmed: ChartBundle = {
    ...bundle,
    active_yogas: bundle.active_yogas.slice(0, 10),
    ayanamsha_slices: bundle.ayanamsha_slices.map((s) => ({
      ...s,
      planets: s.planets.slice(0, 12),
      houses: s.houses.slice(0, 12),
      dasha_chain: s.dasha_chain.slice(0, 3),
    })),
    cross_ayanamsha: bundle.cross_ayanamsha.slice(0, 5),
  }
  trimmed.token_estimate = estimateTokens(trimmed)
  return trimmed
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function asInt(v: unknown): number | null {
  if (v == null) return null
  const n = parseInt(String(v), 10)
  return isNaN(n) ? null : n
}

function asFloat(v: unknown): number | null {
  if (v == null) return null
  const n = parseFloat(String(v))
  return isNaN(n) ? null : n
}

function groupBy<T>(arr: T[], key: (item: T) => string): Map<string, T[]> {
  const m = new Map<string, T[]>()
  for (const item of arr) {
    const k = key(item)
    if (!m.has(k)) m.set(k, [])
    m.get(k)!.push(item)
  }
  return m
}

function toKV(rows: NewFactRow[]): Record<string, string> {
  const kv: Record<string, string> = {}
  for (const r of rows) {
    if (r.fact_value_text != null) kv[r.fact_key] = r.fact_value_text
    else if (r.fact_value_num != null) kv[r.fact_key] = String(r.fact_value_num)
  }
  return kv
}
