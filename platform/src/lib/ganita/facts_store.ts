/**
 * ganita/facts_store.ts — Gaṇita L1 Fact Store: composite query + typed aggregation
 *
 * Implements the `query_chart_facts(chart_id)` composite query that returns the
 * full GanitaFactStore for a chart, aggregating all L1 domain slices from the
 * chart_facts table.
 *
 * This is the read-path for GA-1-8: ganita.facts_store.
 * The write path is the Python pipeline writers (pyjhora → JSONL → DB upsert).
 *
 * The function is pure TypeScript and works offline with an injected DB client
 * to allow unit testing without a live Postgres connection.
 *
 * [BRAHMA-GA-1-8]
 */

import type {
  ChartFactRow,
  GanitaFactStore,
  MetadataSection,
  PlanetPlacementRow,
  HouseRow,
  DivisionalChartRow,
  DashaRow,
  StrengthRow,
  SensitivePointRow,
  PanchangaRow,
  YogaRow,
  AspectRow,
  QueryChartFactsInput,
  FactProvenance,
} from './types'
import { CHART_FACTS_CATEGORIES, FORENSIC_V8_REQUIRED_DOMAINS } from './types'
import { grahaCodeOf, GRAHA_CODE_TO_NAME } from '@/lib/retrieval/address_resolver'

// ─── DB client interface (injected; avoids hard coupling to pg Pool) ──────────

export interface DbClient {
  query<T = unknown>(sql: string, params?: unknown[]): Promise<{ rows: T[] }>
}

// ─── Internal raw row type from the DB query ─────────────────────────────────

interface RawFactRow {
  id: string
  fact_id: string
  chart_id: string | null
  ayanamsha_id: string | null
  category: string
  divisional_chart: string
  fact_category: string | null
  fact_key: string | null
  fact_subject: string | null
  value_text: string | null
  value_number: string | null   // Postgres NUMERIC comes as string
  value_json: unknown | null
  source_section: string
  build_id: string
  provenance: unknown
  is_stale: boolean
  created_at: string
  engine_version: string | null
  verification_pass_status: string | null
  citation_ref: string | null
  citation_human: string | null
  unit: string | null
}

// ─── Helper: coerce RawFactRow → ChartFactRow ─────────────────────────────────

function coerceRow(raw: RawFactRow): ChartFactRow {
  let prov: FactProvenance
  if (typeof raw.provenance === 'string') {
    try { prov = JSON.parse(raw.provenance) as FactProvenance } catch { prov = { source_uri: '', source_version: '', source_canonical_id: '', extracted_at: '', extraction_method: '' } }
  } else {
    prov = (raw.provenance as FactProvenance) ?? { source_uri: '', source_version: '', source_canonical_id: '', extracted_at: '', extraction_method: '' }
  }
  let valueJson: Record<string, unknown> | null = null
  if (raw.value_json !== null && raw.value_json !== undefined) {
    if (typeof raw.value_json === 'string') {
      try { valueJson = JSON.parse(raw.value_json) as Record<string, unknown> } catch { valueJson = null }
    } else {
      valueJson = raw.value_json as Record<string, unknown>
    }
  }
  return {
    id: raw.id,
    fact_id: raw.fact_id,
    chart_id: raw.chart_id ?? undefined,
    ayanamsha_id: raw.ayanamsha_id ?? undefined,
    category: raw.category,
    divisional_chart: raw.divisional_chart,
    fact_category: raw.fact_category ?? undefined,
    fact_key: raw.fact_key ?? undefined,
    fact_subject: raw.fact_subject ?? undefined,
    value_text: raw.value_text,
    value_number: raw.value_number !== null ? parseFloat(raw.value_number) : null,
    value_json: valueJson,
    source_section: raw.source_section,
    build_id: raw.build_id,
    provenance: prov,
    is_stale: raw.is_stale,
    created_at: raw.created_at,
    engine_version: raw.engine_version ?? undefined,
    verification_pass_status: (raw.verification_pass_status as ChartFactRow['verification_pass_status']) ?? undefined,
    citation_ref: raw.citation_ref ?? undefined,
    citation_human: raw.citation_human ?? undefined,
    unit: raw.unit ?? undefined,
  }
}

// ─── Helper: groupBy category ─────────────────────────────────────────────────

export function groupByCategory(rows: ChartFactRow[]): Record<string, ChartFactRow[]> {
  const grouped: Record<string, ChartFactRow[]> = {}
  for (const row of rows) {
    const cat = row.category
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(row)
  }
  return grouped
}

// ─── Domain parsers ───────────────────────────────────────────────────────────

function parseMetadata(rows: ChartFactRow[]): MetadataSection {
  const get = (key: string) => rows.find(r => r.fact_id === key || r.fact_key === key.replace('MET.', ''))?.value_text ?? null
  return {
    birth_date: get('MET.BIRTH.DATE'),
    birth_time: get('MET.BIRTH.TIME'),
    birth_place: get('MET.BIRTH.PLACE'),
    latitude: get('MET.BIRTH.LAT'),
    longitude: get('MET.BIRTH.LON'),
    timezone: get('MET.BIRTH.TZ'),
    ayanamsha: get('MET.AYANAMSHA.NAME'),
    ayanamsha_value: get('MET.AYANAMSHA.VALUE'),
    house_system: get('MET.HOUSE_SYSTEM'),
    lagna_sign: get('MET.LAGNA.SIGN') ?? get('LAGNA_SIGN'),
    lagna_degree: get('MET.LAGNA.DEG') ?? get('LAGNA_DEG'),
    lagna_nakshatra: get('MET.LAGNA.NAK'),
    lagna_pada: get('MET.LAGNA.PADA'),
  }
}

function parsePlanets(rows: ChartFactRow[]): PlanetPlacementRow[] {
  const PLANETS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU']
  // Values sourced from the graha SSoT (address_resolver.grahaCodeOf +
  // GRAHA_CODE_TO_NAME) rather than hardcoded literals — ADHIṢṬHĀNA Lane A2.
  const PLANET_DISPLAY: Record<string, string> = Object.fromEntries(
    PLANETS.map(p => [p, GRAHA_CODE_TO_NAME[grahaCodeOf(p)]]),
  )

  return PLANETS.map(planet => {
    const prefix = `PLN.${planet}.`
    const get = (key: string) => rows.find(r => r.fact_id === `${prefix}${key}`)
    return {
      planet: PLANET_DISPLAY[planet] ?? planet,
      sign: get('SIGN')?.value_text ?? '',
      house_rashi: get('HOUSE_RASHI')?.value_number ?? 0,
      house_chalit: get('HOUSE_CHALIT')?.value_number ?? null,
      degree_dms: get('LON_DMS')?.value_text ?? null,
      degree_decimal: get('LON_DEG')?.value_number ?? null,
      nakshatra: get('NAK')?.value_text ?? null,
      nakshatra_pada: get('NAK_PADA')?.value_number ?? null,
      nakshatra_lord: get('NAK_LORD')?.value_text ?? null,
      sub_lord: get('KP_SUB_LORD')?.value_text ?? null,
      dignity: get('DIGNITY')?.value_text ?? null,
      retrograde: get('RETROGRADE')?.value_text === 'true' || get('RETROGRADE')?.value_number === 1,
      combusted: get('COMBUSTED')?.value_text !== null ? get('COMBUSTED')?.value_text === 'true' : null,
    }
  }).filter(p => p.sign !== '')
}

function parseHouses(rows: ChartFactRow[]): HouseRow[] {
  const houses: HouseRow[] = []
  for (let h = 1; h <= 12; h++) {
    const prefix = `HSE.${h}.`
    const get = (key: string) => rows.find(r => r.fact_id === `${prefix}${key}`)
    const sign = get('SIGN')?.value_text ?? null
    if (!sign) continue
    const planetsRashi = rows
      .filter(r => r.fact_id === `${prefix}PLANETS_RASHI`)
      .map(r => r.value_text ?? '')
      .filter(Boolean)
    const planetsChalit = rows
      .filter(r => r.fact_id === `${prefix}PLANETS_CHALIT`)
      .map(r => r.value_text ?? '')
      .filter(Boolean)
    houses.push({
      house: h,
      sign,
      cusp_degree: get('CUSP_DMS')?.value_text ?? null,
      cusp_nakshatra: get('CUSP_NAK')?.value_text ?? null,
      cusp_lord: get('LORD')?.value_text ?? null,
      sub_lord: get('KP_SUB_LORD')?.value_text ?? null,
      planets_rashi: planetsRashi,
      planets_chalit: planetsChalit,
    })
  }
  return houses
}

function parseDivisionals(rows: ChartFactRow[]): DivisionalChartRow[] {
  return rows
    .filter(r => r.category === 'divisional' && r.divisional_chart !== 'D1' && r.divisional_chart !== 'INVARIANT')
    .map(r => ({
      varga: r.divisional_chart,
      planet: r.fact_subject ?? (r.fact_id.split('.')[1] ?? ''),
      sign: r.value_text ?? '',
      house: r.value_number ?? null,
      lord: r.value_json?.['lord'] as string | null ?? null,
    }))
}

function parseDashas(rows: ChartFactRow[]): DashaRow[] {
  const dashaCategories = ['dasha_vimshottari', 'dasha_yogini', 'dasha_jaimini', 'dasha_kalachakra', 'dasha_balance']
  return rows
    .filter(r => dashaCategories.includes(r.category))
    .map(r => {
      const json = r.value_json as Record<string, unknown> | null
      return {
        system: r.category.replace('dasha_', ''),
        level: (r.fact_key?.split('.')[0] ?? 'MD') as DashaRow['level'],
        lord: r.fact_subject ?? r.value_text ?? '',
        start_date: (json?.['start'] as string | undefined) ?? (json?.['start_date'] as string | undefined) ?? '',
        end_date: (json?.['end'] as string | undefined) ?? (json?.['end_date'] as string | undefined) ?? '',
        duration_days: json?.['duration_days'] as number | null ?? null,
      }
    })
    .filter(d => d.lord !== '')
}

function parseStrengths(rows: ChartFactRow[]): StrengthRow[] {
  const strengthCategories = ['shadbala', 'ashtakavarga', 'bhava_bala', 'vimsopaka']
  return rows
    .filter(r => strengthCategories.includes(r.category))
    .map(r => ({
      planet: r.fact_subject ?? r.fact_id.split('.')[1] ?? '',
      system: r.category,
      value: r.value_number,
      unit: r.unit ?? null,
      category: r.fact_key ?? null,
    }))
}

function parseSensitivePoints(rows: ChartFactRow[]): SensitivePointRow[] {
  const spCategories = ['upagraha', 'special_lagna', 'saham', 'arudha', 'karaka', 'sensitive_point']
  return rows
    .filter(r => spCategories.includes(r.category))
    .map(r => ({
      type: r.category,
      name: r.fact_subject ?? r.fact_id.split('.')[1] ?? '',
      sign: r.value_text,
      house: r.value_json?.['house'] as number | null ?? null,
      degree: r.value_json?.['degree'] as string | null ?? null,
      lord: r.value_json?.['lord'] as string | null ?? null,
    }))
}

function parsePanchanga(rows: ChartFactRow[]): PanchangaRow[] {
  return rows
    .filter(r => r.category === 'panchanga')
    .map(r => {
      const json = r.value_json as Record<string, unknown> | null
      return {
        component: r.fact_subject ?? r.fact_key ?? r.fact_id.split('.').slice(1).join('.'),
        value: r.value_text,
        lord: json?.['lord'] as string | null ?? null,
        pada: json?.['pada'] as number | null ?? null,
        start_iso: json?.['start_iso'] as string | null ?? null,
        end_iso: json?.['end_iso'] as string | null ?? null,
      }
    })
}

function parseYogas(rows: ChartFactRow[]): YogaRow[] {
  return rows
    .filter(r => r.category === 'yoga')
    .map(r => {
      const json = r.value_json as Record<string, unknown> | null
      return {
        yoga_name: r.fact_subject ?? r.value_text ?? '',
        type: r.fact_key ?? 'yoga',
        planets_involved: (json?.['planets'] as string[] | undefined) ?? [],
        houses_involved: (json?.['houses'] as number[] | undefined) ?? [],
        strength: json?.['strength'] as string | null ?? null,
        source_rule: json?.['rule'] as string | null ?? null,
      }
    })
}

function parseAspects(rows: ChartFactRow[]): AspectRow[] {
  return rows
    .filter(r => r.category === 'aspect')
    .map(r => {
      const parts = r.fact_id.split('.')
      const json = r.value_json as Record<string, unknown> | null
      return {
        aspector: parts[1] ?? '',
        aspected_body: parts[2] ?? '',
        aspect_type: r.fact_key ?? json?.['type'] as string ?? 'full',
        orb_degrees: r.value_number,
        strength: json?.['strength'] as string | null ?? null,
      }
    })
}

// ─── Coverage scoring ─────────────────────────────────────────────────────────

function computeCoverage(rowsByCategory: Record<string, ChartFactRow[]>): {
  coverage_score: number
  domains_present: string[]
  domains_missing: string[]
} {
  const present: string[] = []
  const missing: string[] = []
  for (const domain of FORENSIC_V8_REQUIRED_DOMAINS) {
    // map domain names to category keys
    const catKey = domain === 'metadata' ? 'metadata'
      : domain === 'planet' ? 'planet'
      : domain === 'house' ? 'house'
      : domain === 'divisional' ? 'divisional'
      : domain === 'dasha_vimshottari' ? 'dasha_vimshottari'
      : domain === 'shadbala' ? 'shadbala'
      : domain === 'ashtakavarga' ? 'ashtakavarga'
      : domain === 'upagraha' ? 'upagraha'
      : domain === 'saham' ? 'saham'
      : domain === 'special_lagna' ? 'special_lagna'
      : domain === 'arudha' ? 'arudha'
      : domain === 'karaka' ? 'karaka'
      : domain === 'yoga' ? 'yoga'
      : domain === 'aspect' ? 'aspect'
      : domain === 'panchanga' ? 'panchanga'
      : domain === 'sade_sati' ? 'sade_sati'
      : domain === 'varshphal' ? 'varshphal'
      : domain === 'kp' ? 'kp'
      : domain
    const rows = rowsByCategory[catKey]
    if (rows && rows.length > 0) {
      present.push(domain)
    } else {
      missing.push(domain)
    }
  }
  return {
    coverage_score: present.length / FORENSIC_V8_REQUIRED_DOMAINS.length,
    domains_present: present,
    domains_missing: missing,
  }
}

// ─── Main: query_chart_facts ──────────────────────────────────────────────────

/**
 * query_chart_facts — composite query returning the full GanitaFactStore for a chart.
 *
 * Accepts an optional chart_id; when omitted, falls back to the native's canonical
 * chart (Abhisek Mohanty) for single-native environments.
 *
 * The DB client is injected to allow unit testing without a live Postgres connection.
 */
export async function query_chart_facts(
  input: QueryChartFactsInput,
  db: DbClient,
): Promise<GanitaFactStore> {
  const {
    chart_id,
    ayanamsha_id = 'lahiri',
    category,
    categories,
    planet,
    house,
    divisional_chart,
    limit = 5000,
  } = input

  // Build WHERE clauses
  const conditions: string[] = ['cf.is_stale = false']
  const params: unknown[] = []
  let paramIdx = 1

  if (chart_id) {
    conditions.push(`cf.chart_id = $${paramIdx++}`)
    params.push(chart_id)
  }

  if (ayanamsha_id) {
    // Include INVARIANT rows (ayanamsha-independent facts) plus the requested ayanamsha
    conditions.push(`(cf.ayanamsha_id = $${paramIdx++} OR cf.ayanamsha_id = 'INVARIANT' OR cf.ayanamsha_id IS NULL)`)
    params.push(ayanamsha_id)
  }

  // Handle batched category query
  const effectiveCategories: string[] = []
  if (categories && categories.length > 0) {
    effectiveCategories.push(...categories)
  } else if (Array.isArray(category)) {
    effectiveCategories.push(...category)
  } else if (typeof category === 'string') {
    effectiveCategories.push(category)
  }

  if (effectiveCategories.length > 0) {
    conditions.push(`cf.category = ANY($${paramIdx++}::text[])`)
    params.push(effectiveCategories)
  }

  if (planet) {
    conditions.push(`(cf.fact_id LIKE $${paramIdx++} OR cf.fact_subject = $${paramIdx++})`)
    params.push(`PLN.${planet.toUpperCase()}.%`)
    params.push(planet)
    paramIdx  // already bumped above
  }

  if (house) {
    conditions.push(`cf.fact_id LIKE $${paramIdx++}`)
    params.push(`HSE.${house}.%`)
  }

  if (divisional_chart) {
    conditions.push(`cf.divisional_chart = $${paramIdx++}`)
    params.push(divisional_chart)
  }

  const sql = `
    SELECT
      cf.id,
      cf.fact_id,
      cf.chart_id,
      cf.ayanamsha_id,
      cf.category,
      cf.divisional_chart,
      cf.fact_category,
      cf.fact_key,
      cf.fact_subject,
      cf.value_text,
      cf.value_number::text AS value_number,
      cf.value_json,
      cf.source_section,
      cf.build_id,
      cf.provenance,
      cf.is_stale,
      cf.created_at,
      cf.engine_version,
      cf.verification_pass_status,
      cf.citation_ref,
      cf.citation_human,
      cf.unit
    FROM chart_facts cf
    WHERE ${conditions.join(' AND ')}
    ORDER BY cf.category, cf.fact_id
    LIMIT ${Number(limit)}
  `

  const result = await db.query<RawFactRow>(sql, params)
  const rows = result.rows.map(coerceRow)

  // Determine build metadata from rows
  const buildId = rows[0]?.build_id ?? 'unknown'
  const chartIdResolved = rows[0]?.chart_id ?? chart_id ?? null

  // Group by category for domain parsing
  const rowsByCategory = groupByCategory(rows)

  // Parse each domain section
  const metaRows = rowsByCategory['metadata'] ?? []
  const planetRows = rowsByCategory['planet'] ?? []
  const houseRows = rowsByCategory['house'] ?? []
  const divisionalRows = [...(rowsByCategory['divisional'] ?? []), ...(rowsByCategory['varga'] ?? [])]
  const allDashaRows = [
    ...(rowsByCategory['dasha_vimshottari'] ?? []),
    ...(rowsByCategory['dasha_yogini'] ?? []),
    ...(rowsByCategory['dasha_jaimini'] ?? []),
    ...(rowsByCategory['dasha_kalachakra'] ?? []),
    ...(rowsByCategory['dasha_balance'] ?? []),
  ]
  const strengthRows = [
    ...(rowsByCategory['shadbala'] ?? []),
    ...(rowsByCategory['ashtakavarga'] ?? []),
    ...(rowsByCategory['bhava_bala'] ?? []),
    ...(rowsByCategory['vimsopaka'] ?? []),
  ]
  const spRows = [
    ...(rowsByCategory['upagraha'] ?? []),
    ...(rowsByCategory['special_lagna'] ?? []),
    ...(rowsByCategory['saham'] ?? []),
    ...(rowsByCategory['arudha'] ?? []),
    ...(rowsByCategory['karaka'] ?? []),
    ...(rowsByCategory['sensitive_point'] ?? []),
  ]

  const { coverage_score, domains_present, domains_missing } = computeCoverage(rowsByCategory)

  return {
    chart_id: chartIdResolved,
    ayanamsha_id,
    build_id: buildId,
    generated_at: new Date().toISOString(),
    coverage_score,
    metadata: parseMetadata(metaRows),
    planets: parsePlanets(planetRows),
    houses: parseHouses(houseRows),
    divisionals: parseDivisionals(divisionalRows),
    dashas: parseDashas(allDashaRows),
    strengths: parseStrengths(strengthRows),
    sensitive_points: parseSensitivePoints(spRows),
    panchanga: parsePanchanga(rowsByCategory['panchanga'] ?? []),
    yogas: parseYogas(rowsByCategory['yoga'] ?? []),
    aspects: parseAspects(rowsByCategory['aspect'] ?? []),
    sade_sati: rowsByCategory['sade_sati'] ?? [],
    varshphal: rowsByCategory['varshphal'] ?? [],
    rows_by_category: rowsByCategory,
    domains_present,
    domains_missing,
  }
}

// ─── Exported category list (re-export for MCP tool registration) ─────────────
export { CHART_FACTS_CATEGORIES } from './types'
