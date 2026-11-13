/** Physical reads for the legacy global remedy reference tools.
 * Preserve DATABASE_URL-only/default pg role, max5 and one owned pool per read.
 * Shared db/client has different fallback, retry, parser and lifecycle behavior.
 * No chart scope, session role/GUC, transaction, cache or provider is introduced.
 */
import type { Pool as PgPool } from 'pg'

type RemedyRows = Record<string, unknown>[]

async function queryDb(sql: string, params: unknown[]): Promise<RemedyRows> {
  let pool: PgPool | undefined
  let result: { rows: unknown } | undefined
  let failed = false
  let failure: unknown
  try {
    const { Pool } = await import('pg')
    const url = process.env.DATABASE_URL
    if (!url) throw new Error('DATABASE_URL not set')
    pool = new Pool({ connectionString: url, max: 5 })
    result = await pool.query(sql, params)
  } catch (error) {
    failed = true
    failure = error
  } finally {
    if (pool) {
      try {
        await pool.end()
      } catch (error) {
        // Preserve the original query failure when cleanup also fails. An end
        // failure after a successful query still rejects, as the legacy did.
        if (!failed) {
          failed = true
          failure = error
        }
      }
    }
  }
  if (failed) throw new Error(`remedy_tools queryDb failed: ${String(failure)}`)
  try {
    // The legacy reads result.rows only after end() completes. Preserve that
    // order, including the precedence of end failures over accessor failures.
    return result!.rows as RemedyRows
  } catch (error) {
    throw new Error(`remedy_tools queryDb failed: ${String(error)}`)
  }
}

const LIVE_REMEDY_CONDITION = "scaffold_status = 'live'"

function normalizePlanet(planet: string): string {
  return planet.trim().toLowerCase()
}


export async function readRemedies(planet: string | undefined, domain: string | undefined, category: string | undefined, topK: number): Promise<RemedyRows> {
    const conditions: string[] = [LIVE_REMEDY_CONDITION]
    const values: unknown[] = []

    if (planet) {
      values.push(normalizePlanet(planet))
      conditions.push(`LOWER(planet) = $${values.length}`)
    }
    if (domain) {
      values.push(domain)
      conditions.push(`domain = $${values.length}`)
    }
    if (category) {
      values.push(category)
      conditions.push(`category = $${values.length}`)
    }

    const where = `WHERE ${conditions.join(' AND ')}`
    values.push(topK)
    const sql = `
      SELECT remedy_id, planet, domain, category, deity,
             prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
             cost_tier, contraindications, source_canonical_id, source_citation,
             classical_attestation_text, classical_ref
      FROM brahma_remedy_corpus
      ${where}
      ORDER BY confidence DESC NULLS LAST
      LIMIT $${values.length}
    `
    const rows = await queryDb(sql, values)
    return rows
}

export async function readRemediesForAffliction(affliction: string, topK: number): Promise<RemedyRows> {
    const sql = `
      SELECT remedy_id, planet, domain, category, deity,
             prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
             cost_tier, contraindications, source_canonical_id, source_citation,
             classical_attestation_text
      FROM brahma_remedy_corpus
      WHERE ${LIVE_REMEDY_CONDITION} AND (planet ILIKE $1 OR domain ILIKE $1)
      ORDER BY confidence DESC NULLS LAST, cost_tier ASC
      LIMIT $2
    `
    const rows = await queryDb(sql, [`%${affliction}%`, topK])
    return rows
}

export async function readRemediesByCategory(category: string): Promise<RemedyRows> {
    const sql = `
      SELECT remedy_id, planet, domain, category, deity,
             prescription_text, mantra_text, mantra_sanskrit,
             cost_tier, source_canonical_id, classical_attestation_text
      FROM brahma_remedy_corpus
      WHERE ${LIVE_REMEDY_CONDITION} AND category = $1
      ORDER BY planet, remedy_id
    `
    const rows = await queryDb(sql, [category])
    return rows
}

export async function readRemedyById(remedyId: string): Promise<RemedyRows> {
    const sql = `
      SELECT *
      FROM brahma_remedy_corpus
      WHERE ${LIVE_REMEDY_CONDITION} AND remedy_id = $1
    `
    const rows = await queryDb(sql, [remedyId])
    return rows
}

export async function readTantricRemedies(deity: string | undefined, planet: string | undefined): Promise<RemedyRows> {
    const conditions: string[] = [LIVE_REMEDY_CONDITION, "category = 'tantric'"]
    const values: unknown[] = []

    if (deity) {
      values.push(`%${deity}%`)
      conditions.push(`deity ILIKE $${values.length}`)
    }
    if (planet) {
      values.push(normalizePlanet(planet))
      conditions.push(`LOWER(planet) = $${values.length}`)
    }

    const sql = `
      SELECT remedy_id, planet, domain, deity,
             prescription_text, mantra_sanskrit, mantra_transliteration,
             ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications,
             source_canonical_id, source_citation, classical_attestation_text
      FROM brahma_remedy_corpus
      WHERE ${conditions.join(' AND ')}
      ORDER BY planet, remedy_id
    `
    const rows = await queryDb(sql, values)
    return rows
}

export async function readRemediesByPlanet(planet: string): Promise<RemedyRows> {
    const sql = `
      SELECT remedy_id, planet, domain, category, deity,
             prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
             cost_tier, contraindications, source_canonical_id, classical_attestation_text
      FROM brahma_remedy_corpus
      WHERE ${LIVE_REMEDY_CONDITION} AND LOWER(planet) = $1
      ORDER BY category, remedy_id
    `
    const rows = await queryDb(sql, [normalizePlanet(planet)])
    return rows
}

export async function readMantraRemedies(planet: string | undefined): Promise<RemedyRows> {
    const conditions: string[] = [LIVE_REMEDY_CONDITION, "category = 'mantras'"]
    const values: unknown[] = []

    if (planet) {
      values.push(normalizePlanet(planet))
      conditions.push(`LOWER(planet) = $${values.length}`)
    }

    const sql = `
      SELECT remedy_id, planet, deity,
             mantra_sanskrit, mantra_transliteration, mantra_text,
             prescription_text, timing_rules_jsonb,
             source_canonical_id, classical_attestation_text, classical_ref
      FROM brahma_remedy_corpus
      WHERE ${conditions.join(' AND ')}
      ORDER BY planet, remedy_id
    `
    const rows = await queryDb(sql, values)
    return rows
}
