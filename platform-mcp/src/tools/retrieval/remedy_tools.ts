/**
 * retrieval/remedy_tools.ts — Stream F Brahmagyan Remedy tools for MCP server
 *
 * Registers 7 tools against brahma_remedy_corpus:
 *   1. query_remedies
 *   2. query_remedies_for_chart
 *   3. list_remedies_by_category
 *   4. read_remedy
 *   5. query_tantric_remedies
 *   6. query_remedies_by_planet
 *   7. query_mantras
 *
 * ZERO LLM — all retrieval is deterministic SQL.
 * Source: BPHS Ch.91-94, Phaladeepika Ch.27-28, Brihat Samhita Ch.53
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool ───────────────────────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool | null {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) return null
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

async function queryDb(sql: string, params: unknown[]): Promise<Record<string, unknown>[]> {
  const pool = getPool()
  if (!pool) throw new Error('DATABASE_URL not configured — cannot query remedy corpus')
  const result = await pool.query(sql, params)
  return result.rows as Record<string, unknown>[]
}

// ── Registration helper ────────────────────────────────────────────────────────

export function registerRemedyTools(server: McpServer): void {

  // ── 1. query_remedies ──────────────────────────────────────────────────────

  server.tool(
    'query_remedies',
    'Query brahma_remedy_corpus by planet, domain, and/or category. Returns classical remedy prescriptions with mantra and source attestation.',
    {
      planet: z.string().optional().describe('Planet name e.g. Saturn, Moon, Venus'),
      domain: z.string().optional().describe('Domain e.g. career, health, marriage, spirituality'),
      category: z.string().optional().describe('Category: mantras | gemstones | charity | vrata | yantras | puja | tantric | ayurvedic | vastu | behavioral'),
      top_k: z.number().int().min(1).max(50).default(10).describe('Max rows to return'),
    },
    async ({ planet, domain, category, top_k }) => {
      const conditions: string[] = []
      const values: unknown[] = []

      if (planet) { values.push(planet); conditions.push(`planet = $${values.length}`) }
      if (domain) { values.push(domain); conditions.push(`domain = $${values.length}`) }
      if (category) { values.push(category); conditions.push(`category = $${values.length}`) }

      const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
      values.push(top_k)
      const rows = await queryDb(
        `SELECT remedy_id, planet, domain, category, deity,
                prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
                cost_tier, contraindications, source_canonical_id, source_citation,
                classical_attestation_text, classical_ref
         FROM brahma_remedy_corpus ${where}
         ORDER BY confidence DESC NULLS LAST LIMIT $${values.length}`,
        values,
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ query_remedies: rows, count: rows.length }) }],
      }
    },
  )

  // ── 2. query_remedies_for_chart ───────────────────────────────────────────

  server.tool(
    'query_remedies_for_chart',
    'Return remedies relevant to a chart affliction. Pass affliction as planet name or domain keyword.',
    {
      affliction: z.string().describe('Planet name or domain keyword e.g. "Saturn", "health"'),
      top_k: z.number().int().min(1).max(20).default(5),
    },
    async ({ affliction, top_k }) => {
      const rows = await queryDb(
        `SELECT remedy_id, planet, domain, category, deity,
                prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
                cost_tier, contraindications, source_canonical_id, classical_attestation_text
         FROM brahma_remedy_corpus
         WHERE planet ILIKE $1 OR domain ILIKE $1
         ORDER BY confidence DESC NULLS LAST, cost_tier ASC LIMIT $2`,
        [`%${affliction}%`, top_k],
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ query_remedies_for_chart: rows, affliction, count: rows.length }) }],
      }
    },
  )

  // ── 3. list_remedies_by_category ─────────────────────────────────────────

  server.tool(
    'list_remedies_by_category',
    'List all remedies in one category. 10 categories: mantras | gemstones | charity | vrata | yantras | puja | tantric | ayurvedic | vastu | behavioral',
    {
      category: z.enum([
        'mantras', 'gemstones', 'charity', 'vrata', 'yantras',
        'puja', 'tantric', 'ayurvedic', 'vastu', 'behavioral',
      ]).describe('Remedy category'),
    },
    async ({ category }) => {
      const rows = await queryDb(
        `SELECT remedy_id, planet, domain, category, deity,
                prescription_text, mantra_text, mantra_sanskrit,
                cost_tier, source_canonical_id, classical_attestation_text
         FROM brahma_remedy_corpus
         WHERE category = $1
         ORDER BY planet, remedy_id`,
        [category],
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ list_remedies_by_category: rows, category, count: rows.length }) }],
      }
    },
  )

  // ── 4. read_remedy ────────────────────────────────────────────────────────

  server.tool(
    'read_remedy',
    'Fetch full remedy record by remedy_id, including ingredients_jsonb and timing_rules_jsonb.',
    {
      remedy_id: z.string().describe('The unique remedy identifier e.g. man_sun_gayatri_001'),
    },
    async ({ remedy_id }) => {
      const rows = await queryDb(
        `SELECT * FROM brahma_remedy_corpus WHERE remedy_id = $1`,
        [remedy_id],
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ read_remedy: rows[0] ?? null, found: rows.length > 0 }) }],
      }
    },
  )

  // ── 5. query_tantric_remedies ─────────────────────────────────────────────

  server.tool(
    'query_tantric_remedies',
    'Query tantric remedies only. All rows have passed the tantric careful-inclusion gate (BPHS/Phaladeepika sources only). Optional filter by deity or planet.',
    {
      deity: z.string().optional().describe('Deity name e.g. Shiva, Durga'),
      planet: z.string().optional().describe('Planet name e.g. Saturn, Rahu'),
    },
    async ({ deity, planet }) => {
      const conditions: string[] = ["category = 'tantric'"]
      const values: unknown[] = []

      if (deity) { values.push(`%${deity}%`); conditions.push(`deity ILIKE $${values.length}`) }
      if (planet) { values.push(planet); conditions.push(`planet = $${values.length}`) }

      const rows = await queryDb(
        `SELECT remedy_id, planet, domain, deity,
                prescription_text, mantra_sanskrit, mantra_transliteration,
                ingredients_jsonb, timing_rules_jsonb, cost_tier, contraindications,
                source_canonical_id, source_citation, classical_attestation_text
         FROM brahma_remedy_corpus
         WHERE ${conditions.join(' AND ')}
         ORDER BY planet, remedy_id`,
        values,
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ query_tantric_remedies: rows, count: rows.length }) }],
      }
    },
  )

  // ── 6. query_remedies_by_planet ───────────────────────────────────────────

  server.tool(
    'query_remedies_by_planet',
    'Return all remedies for a given planet across all categories — a complete upaya profile.',
    {
      planet: z.enum(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'])
        .describe('Planet name'),
    },
    async ({ planet }) => {
      const rows = await queryDb(
        `SELECT remedy_id, planet, domain, category, deity,
                prescription_text, mantra_text, mantra_sanskrit, mantra_transliteration,
                cost_tier, contraindications, source_canonical_id, classical_attestation_text
         FROM brahma_remedy_corpus
         WHERE planet = $1
         ORDER BY category, remedy_id`,
        [planet],
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ query_remedies_by_planet: rows, planet, count: rows.length }) }],
      }
    },
  )

  // ── 7. query_mantras ──────────────────────────────────────────────────────

  server.tool(
    'query_mantras',
    'Return all mantra remedies (category=mantras) for a planet with Sanskrit mantra and classical source.',
    {
      planet: z.string().optional().describe('Planet name; omit to return all mantras'),
    },
    async ({ planet }) => {
      const conditions: string[] = ["category = 'mantras'"]
      const values: unknown[] = []

      if (planet) { values.push(planet); conditions.push(`planet = $${values.length}`) }

      const rows = await queryDb(
        `SELECT remedy_id, planet, deity,
                mantra_sanskrit, mantra_transliteration, mantra_text,
                prescription_text, timing_rules_jsonb,
                source_canonical_id, classical_attestation_text, classical_ref
         FROM brahma_remedy_corpus
         WHERE ${conditions.join(' AND ')}
         ORDER BY planet, remedy_id`,
        values,
      )
      return {
        content: [{ type: 'text' as const, text: JSON.stringify({ query_mantras: rows, planet: planet ?? 'all', count: rows.length }) }],
      }
    },
  )
}
