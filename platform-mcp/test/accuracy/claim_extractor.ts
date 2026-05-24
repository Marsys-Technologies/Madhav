/**
 * claim_extractor.ts — Deterministic (no LLM) claim extractor for cross-scenario
 * equivalence testing in MCPT v3.2 Phase 9a.
 *
 * Pulls structured claims from tool output envelopes (rows_by_category or flat rows[]).
 * Claims are keyed by (subject, predicate) so they can be compared across two
 * invocation paths that both read from the same chart_facts DB table.
 *
 * Design: works on the structured DB rows, not on LLM-synthesized text.
 * All extraction is pure, synchronous, and deterministic.
 *
 * MCPT v3.2 Phase 9a — Cross-Scenario Equivalence
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export type ClaimType =
  | 'planet_placement'
  | 'yoga'
  | 'karakas'
  | 'dasha_period'
  | 'arudha_house'
  | 'house_lord'
  | 'sensitive_point'
  | 'birth_metadata'
  | 'generic'

export interface Claim {
  /** Semantic type of the claim. */
  type: ClaimType
  /** Primary subject of the claim (e.g. "Saturn", "Hamsa Yoga", "MD-Moon"). */
  subject: string
  /** Relationship predicate (e.g. "placed_in", "active_from", "lord_of"). */
  predicate: string
  /** Object of the predicate (e.g. "Capricorn 10H", "2026-05-01", "7H"). */
  object: string
  /**
   * Source DB category (e.g. "planet", "yoga", "dasha_vimshottari").
   * Used as a secondary grouping key when comparing claim sets.
   */
  source_category: string
  /**
   * Confidence in the claim.
   * 1.0 for structured DB rows (no inference).
   */
  confidence: number
}

export type ClaimSet = Claim[]

/** Result of comparing two ClaimSets. */
export interface ClaimDiffResult {
  agreement_pct: number
  total_compared: number
  matching: number
  disagreements: Array<{
    path: string
    a: unknown
    b: unknown
  }>
}

// ── Row type helpers ──────────────────────────────────────────────────────────

type ChartFactRow = Record<string, unknown>

// ── Extraction helpers by category ───────────────────────────────────────────

/**
 * Extract claims from a single planet row.
 * Row fields: fact_id, category, divisional_chart, value_text, planet_name,
 *   house, sign, longitude, data.{nakshatra, pada, retrograde, dignity, ...}
 */
function extractPlanetClaims(row: ChartFactRow): Claim[] {
  const planet = String(row['planet_name'] ?? row['planet'] ?? row['subject'] ?? '')
  if (!planet) return []

  const claims: Claim[] = []
  const divChart = String(row['divisional_chart'] ?? 'D1')
  const sign = String(row['sign'] ?? row['rasi'] ?? '')
  const house = row['house'] !== undefined ? String(row['house']) : ''
  const valueText = String(row['value_text'] ?? '')

  // Placement claim: Saturn placed_in Capricorn 10H (D1)
  const locationParts = [sign, house ? `${house}H` : '', divChart !== 'D1' ? divChart : ''].filter(Boolean)
  const location = locationParts.length > 0 ? locationParts.join(' ') : valueText
  if (location || valueText) {
    claims.push({
      type: 'planet_placement',
      subject: planet,
      predicate: 'placed_in',
      object: location || valueText,
      source_category: 'planet',
      confidence: 1.0,
    })
  }

  // House lord claim: if row carries lord_of field
  const lordOf = row['lord_of'] !== undefined ? String(row['lord_of']) : ''
  if (lordOf) {
    claims.push({
      type: 'house_lord',
      subject: planet,
      predicate: 'lord_of',
      object: lordOf,
      source_category: 'planet',
      confidence: 1.0,
    })
  }

  return claims
}

/**
 * Extract claims from a single house row.
 * Row fields: fact_id, category, house_number, sign, lord, occupants, ...
 */
function extractHouseClaims(row: ChartFactRow): Claim[] {
  const houseNum = row['house_number'] ?? row['house'] ?? row['bhava']
  if (houseNum === undefined) return []
  const houseLabel = `${String(houseNum)}H`
  const claims: Claim[] = []

  const sign = String(row['sign'] ?? row['rasi'] ?? '')
  if (sign) {
    claims.push({
      type: 'house_lord',
      subject: houseLabel,
      predicate: 'in_sign',
      object: sign,
      source_category: 'house',
      confidence: 1.0,
    })
  }

  const lord = String(row['lord'] ?? row['house_lord'] ?? '')
  if (lord) {
    claims.push({
      type: 'house_lord',
      subject: houseLabel,
      predicate: 'lorded_by',
      object: lord,
      source_category: 'house',
      confidence: 1.0,
    })
  }

  return claims
}

/**
 * Extract claims from a single yoga row.
 * Row fields: fact_id, category, yoga_name, is_active, strength, ...
 */
function extractYogaClaims(row: ChartFactRow): Claim[] {
  const yogaName = String(row['yoga_name'] ?? row['name'] ?? row['value_text'] ?? row['fact_id'] ?? '')
  if (!yogaName) return []

  const isActive = row['is_active'] !== undefined
    ? String(row['is_active'])
    : row['active'] !== undefined
    ? String(row['active'])
    : 'unknown'

  return [
    {
      type: 'yoga',
      subject: yogaName,
      predicate: 'is_active',
      object: isActive,
      source_category: 'yoga',
      confidence: 1.0,
    },
  ]
}

/**
 * Extract claims from a single dasha row.
 * Row fields: fact_id, category, dasha_lord, start_date, end_date, level, ...
 */
function extractDashaClaims(row: ChartFactRow, sourceCategory: string): Claim[] {
  const lord = String(
    row['dasha_lord'] ?? row['lord'] ?? row['planet'] ?? row['subject'] ?? ''
  )
  if (!lord) return []

  const startDate = String(row['start_date'] ?? row['from'] ?? '')
  const endDate = String(row['end_date'] ?? row['to'] ?? '')

  const claims: Claim[] = []

  if (startDate) {
    claims.push({
      type: 'dasha_period',
      subject: `MD-${lord}`,
      predicate: 'active_from',
      object: startDate,
      source_category: sourceCategory,
      confidence: 1.0,
    })
  }

  if (endDate) {
    claims.push({
      type: 'dasha_period',
      subject: `MD-${lord}`,
      predicate: 'active_to',
      object: endDate,
      source_category: sourceCategory,
      confidence: 1.0,
    })
  }

  return claims
}

/**
 * Extract claims from an arudha row.
 * Row fields: fact_id, category, arudha_name, house_number, sign, ...
 */
function extractArudhaClaims(row: ChartFactRow): Claim[] {
  const name = String(
    row['arudha_name'] ?? row['name'] ?? row['arudha'] ?? row['value_text'] ?? row['fact_id'] ?? ''
  )
  if (!name) return []

  const houseNum = row['house_number'] ?? row['house']
  if (houseNum === undefined) return []

  return [
    {
      type: 'arudha_house',
      subject: name,
      predicate: 'falls_in_house',
      object: String(houseNum),
      source_category: 'arudha',
      confidence: 1.0,
    },
  ]
}

/**
 * Extract claims from a birth_metadata row.
 * Row fields: fact_id, category, key, value_text, value_number, ...
 */
function extractBirthMetadataClaims(row: ChartFactRow): Claim[] {
  const key = String(row['key'] ?? row['fact_id'] ?? row['name'] ?? '')
  const value = String(row['value_text'] ?? row['value_number'] ?? '')
  if (!key || !value) return []

  return [
    {
      type: 'birth_metadata',
      subject: key,
      predicate: 'equals',
      object: value,
      source_category: 'birth_metadata',
      confidence: 1.0,
    },
  ]
}

/**
 * Extract claims from a sensitive_point row.
 */
function extractSensitivePointClaims(row: ChartFactRow): Claim[] {
  const name = String(row['point_name'] ?? row['name'] ?? row['value_text'] ?? row['fact_id'] ?? '')
  if (!name) return []

  const sign = String(row['sign'] ?? row['rasi'] ?? '')
  const house = row['house'] !== undefined ? `${String(row['house'])}H` : ''
  const location = [sign, house].filter(Boolean).join(' ')

  if (!location) return []

  return [
    {
      type: 'generic',
      subject: name,
      predicate: 'placed_in',
      object: location,
      source_category: 'sensitive_point',
      confidence: 1.0,
    },
  ]
}

/**
 * Generic fallback extractor for categories without dedicated logic.
 * Uses fact_id as subject and value_text as object.
 */
function extractGenericClaims(row: ChartFactRow, category: string): Claim[] {
  const subject = String(row['fact_id'] ?? row['name'] ?? row['key'] ?? '')
  const predicate = 'has_value'
  const object = String(row['value_text'] ?? row['value_number'] ?? '')

  if (!subject || !object) return []

  return [
    {
      type: 'generic',
      subject,
      predicate,
      object,
      source_category: category,
      confidence: 1.0,
    },
  ]
}

/**
 * Dispatch row extraction to the right handler based on category.
 */
function extractRowClaims(row: ChartFactRow, category: string): Claim[] {
  switch (category) {
    case 'planet':
      return extractPlanetClaims(row)
    case 'house':
      return extractHouseClaims(row)
    case 'yoga':
      return extractYogaClaims(row)
    case 'dasha_vimshottari':
    case 'dasha_chara':
    case 'dasha_yogini':
      return extractDashaClaims(row, category)
    case 'arudha':
    case 'arudha_occupancy':
      return extractArudhaClaims(row)
    case 'birth_metadata':
      return extractBirthMetadataClaims(row)
    case 'sensitive_point':
      return extractSensitivePointClaims(row)
    default:
      return extractGenericClaims(row, category)
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Extract a ClaimSet from a tool output envelope.
 *
 * Handles both shapes:
 *   - { rows_by_category: { planet: row[], yoga: row[], ... } }
 *   - { rows: row[] }                          ← flat rows with category field
 *   - An envelope wrapper: { ok, result: { rows_by_category | rows } }
 *
 * Also handles the chart_summary outer envelope:
 *   { ok, chart_id, rows_by_category: {...}, ... }
 */
export function extractClaims(toolOutput: unknown): ClaimSet {
  if (!toolOutput || typeof toolOutput !== 'object') return []

  const output = toolOutput as Record<string, unknown>

  // Unwrap MCP content array if present (tool handler return value)
  if (Array.isArray(output['content'])) {
    const first = (output['content'] as Array<{ type: string; text: string }>)[0]
    if (first?.type === 'text' && typeof first.text === 'string') {
      try {
        return extractClaims(JSON.parse(first.text))
      } catch {
        return []
      }
    }
    return []
  }

  // Unwrap result envelope: { ok, result: { rows_by_category | rows } }
  if ('result' in output && typeof output['result'] === 'object' && output['result'] !== null) {
    const result = output['result'] as Record<string, unknown>
    const merged = { ...output, ...result }
    delete merged['result']
    return extractClaims(merged)
  }

  const claims: Claim[] = []

  // Shape 1: rows_by_category (batched response from chart_summary or batched query_chart_facts)
  if (output['rows_by_category'] && typeof output['rows_by_category'] === 'object') {
    const byCategory = output['rows_by_category'] as Record<string, unknown[]>
    for (const [category, rows] of Object.entries(byCategory)) {
      if (!Array.isArray(rows)) continue
      for (const row of rows) {
        if (!row || typeof row !== 'object') continue
        const extracted = extractRowClaims(row as ChartFactRow, category)
        claims.push(...extracted)
      }
    }
    return claims
  }

  // Shape 2: flat rows[] with category field on each row
  if (Array.isArray(output['rows'])) {
    for (const row of output['rows']) {
      if (!row || typeof row !== 'object') continue
      const r = row as ChartFactRow
      const category = String(r['category'] ?? 'unknown')
      const extracted = extractRowClaims(r, category)
      claims.push(...extracted)
    }
    return claims
  }

  return claims
}

/**
 * Compare two ClaimSets for agreement.
 *
 * Matching strategy:
 *   - Key = (source_category, subject, predicate)
 *   - Two claims agree if their `object` field is identical (string equality).
 *   - Claims that exist in one set but not the other count as disagreements.
 *
 * Returns agreement_pct as 0–100 (100 = fully equivalent).
 */
export function diffClaims(a: ClaimSet, b: ClaimSet): ClaimDiffResult {
  if (a.length === 0 && b.length === 0) {
    return { agreement_pct: 100, total_compared: 0, matching: 0, disagreements: [] }
  }

  // Build lookup map for set A: key → claim
  const mapA = new Map<string, Claim>()
  for (const claim of a) {
    const key = `${claim.source_category}|${claim.subject}|${claim.predicate}`
    mapA.set(key, claim)
  }

  // Build lookup map for set B: key → claim
  const mapB = new Map<string, Claim>()
  for (const claim of b) {
    const key = `${claim.source_category}|${claim.subject}|${claim.predicate}`
    mapB.set(key, claim)
  }

  // Union of all keys
  const allKeys = new Set([...mapA.keys(), ...mapB.keys()])
  const disagreements: ClaimDiffResult['disagreements'] = []
  let matching = 0

  for (const key of allKeys) {
    const claimA = mapA.get(key)
    const claimB = mapB.get(key)

    if (claimA && claimB) {
      if (claimA.object === claimB.object) {
        matching++
      } else {
        disagreements.push({
          path: key,
          a: claimA.object,
          b: claimB.object,
        })
      }
    } else if (claimA && !claimB) {
      disagreements.push({
        path: key,
        a: claimA.object,
        b: undefined,
      })
    } else if (!claimA && claimB) {
      disagreements.push({
        path: key,
        a: undefined,
        b: claimB!.object,
      })
    }
  }

  const total = matching + disagreements.length
  const agreement_pct = total === 0 ? 100 : Math.round((matching / total) * 100 * 100) / 100

  return {
    agreement_pct,
    total_compared: total,
    matching,
    disagreements,
  }
}
