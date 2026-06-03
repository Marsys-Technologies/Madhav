/**
 * reference_lookup.ts — MCP surgical primitive: classical reference table lookup.
 *
 * brahmagyan.reference asset tool. Queries the reference_* DB tables populated
 * by pipeline/writers/reference_writer.py. All tables carry source_citation on
 * every row (classical text references: MC, BS, VS, DP, PHS).
 *
 * Input:
 *   table  — one of: nakshatra_attrs | tithi_attrs | yoga_attrs | karana_attrs |
 *             vara_attrs | sign_attrs | hora_cycle | combustion_orbs |
 *             event_quality | inauspicious_periods
 *   key    — optional integer key (nakshatra_id, tithi_id, yoga_id, karana_id,
 *             vara_id, sign_id). For event_quality: use event_type string instead.
 *   event_type — required only when table=event_quality
 *                (vivah|griha_pravesh|vyapara|yatra|property_purchase|mantra_initiation)
 *   factor_type — optional when table=event_quality (tithi|nakshatra|vara)
 *
 * Output:
 *   {ok: true, result: {table, rows: Row[], count: number}, epistemics: {surgical: true, ...}}
 *
 * Example: reference_lookup({table: "nakshatra_attrs", key: 25}) →
 *   {ok: true, result: {rows: [{nakshatra_id: 25, name: "Purva Bhadrapada", lord: "Jupiter", ...}]}}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { Pool } from 'pg'
import type { Principal } from '../types.js'

// ── DB pool ────────────────────────────────────────────────────────────────────

let _pool: Pool | null = null
function getPool(): Pool {
  if (!_pool) {
    const url = process.env['DATABASE_URL']
    if (!url) throw new Error('DATABASE_URL not set')
    _pool = new Pool({ connectionString: url, max: 5 })
  }
  return _pool
}

// ── Valid table names ──────────────────────────────────────────────────────────

const VALID_TABLES = [
  'nakshatra_attrs',
  'tithi_attrs',
  'yoga_attrs',
  'karana_attrs',
  'vara_attrs',
  'sign_attrs',
  'hora_cycle',
  'combustion_orbs',
  'event_quality',
  'inauspicious_periods',
] as const

type TableName = typeof VALID_TABLES[number]

const TABLE_PK: Record<TableName, string | null> = {
  nakshatra_attrs:       'nakshatra_id',
  tithi_attrs:           'tithi_id',
  yoga_attrs:            'yoga_id',
  karana_attrs:          'karana_id',
  vara_attrs:            'vara_id',
  sign_attrs:            'sign_id',
  hora_cycle:            'vara_id',
  combustion_orbs:       null,   // key by planet name string, not int
  event_quality:         null,   // key by event_type + factor_type
  inauspicious_periods:  'vara_id',
}

// ── Zod input schema ───────────────────────────────────────────────────────────

const InputSchema = z.object({
  table: z.enum(VALID_TABLES).describe(
    'Reference table to query. One of: ' + VALID_TABLES.join(' | ')
  ),
  key: z.number().int().optional().describe(
    'Integer primary key (nakshatra_id 1-27, tithi_id 1-30, yoga_id 1-27, ' +
    'karana_id 1-11, vara_id 1-7, sign_id 1-12). Omit to return all rows.'
  ),
  planet: z.string().optional().describe(
    'Planet name for combustion_orbs lookup (e.g. "Saturn", "Venus", "Rahu").'
  ),
  event_type: z.enum([
    'vivah', 'griha_pravesh', 'vyapara', 'yatra',
    'property_purchase', 'mantra_initiation',
  ]).optional().describe(
    'Required when table=event_quality.'
  ),
  factor_type: z.enum(['tithi', 'nakshatra', 'vara']).optional().describe(
    'Optional filter when table=event_quality.'
  ),
})

type Input = z.infer<typeof InputSchema>

// ── Query builder ──────────────────────────────────────────────────────────────

async function queryTable(input: Input): Promise<unknown[]> {
  const pool = getPool()
  const tableName = `reference_${input.table}` as const

  if (input.table === 'event_quality') {
    const conditions: string[] = []
    const values: unknown[] = []
    let idx = 1
    if (input.event_type) {
      conditions.push(`event_type = $${idx++}`)
      values.push(input.event_type)
    }
    if (input.factor_type) {
      conditions.push(`factor_type = $${idx++}`)
      values.push(input.factor_type)
    }
    if (input.key !== undefined) {
      conditions.push(`factor_id = $${idx++}`)
      values.push(input.key)
    }
    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
    const { rows } = await pool.query(
      `SELECT * FROM public.${tableName} ${where} ORDER BY event_type, factor_type, factor_id`,
      values
    )
    return rows
  }

  if (input.table === 'combustion_orbs') {
    if (input.planet) {
      const { rows } = await pool.query(
        `SELECT * FROM public.${tableName} WHERE planet = $1`,
        [input.planet]
      )
      return rows
    }
    const { rows } = await pool.query(
      `SELECT * FROM public.${tableName} ORDER BY planet`
    )
    return rows
  }

  const pk = TABLE_PK[input.table]
  if (pk && input.key !== undefined) {
    const { rows } = await pool.query(
      `SELECT * FROM public.${tableName} WHERE ${pk} = $1`,
      [input.key]
    )
    return rows
  }

  const { rows } = await pool.query(
    `SELECT * FROM public.${tableName} ORDER BY id`
  )
  return rows
}

// ── Register function ──────────────────────────────────────────────────────────

export const REFERENCE_LOOKUP_DESCRIPTION = `
Looks up a row or set of rows from the brahmagyan.reference classical tables.
Tables: nakshatra_attrs (27 rows), tithi_attrs (30), yoga_attrs (27),
karana_attrs (11), vara_attrs (7), sign_attrs (12), hora_cycle (7),
combustion_orbs (8), event_quality (muhurat quality by event×factor),
inauspicious_periods (7). Every row carries source_citation.
Surgical: true — no LLM, no synthesis, direct DB read.
`.trim()

export function registerReferenceLookup(
  server: McpServer,
  _getPrincipal: () => Principal
): void {
  server.tool(
    'reference_lookup',
    REFERENCE_LOOKUP_DESCRIPTION,
    InputSchema.shape,
    async (input: Input) => {
      try {
        const rows = await queryTable(input)

        // Collect unique source citations from returned rows for the provenance envelope.
        // Every reference row carries source_citation; the provenance envelope surfaces
        // them so the host LLM can cite classical authority without fabricating references.
        const sourceCitations: string[] = []
        for (const row of rows as Record<string, unknown>[]) {
          const cite = row['source_citation']
          if (typeof cite === 'string' && cite && !sourceCitations.includes(cite)) {
            sourceCitations.push(cite)
          }
        }

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: true,
                result: {
                  table: input.table,
                  rows,
                  count: rows.length,
                },
                provenance_envelope: {
                  source: sourceCitations,
                  school: 'classical',
                  tier: 'L0_reference',
                  confidence: 1.0,
                },
                epistemics: {
                  surgical: true,
                  confidence_band: 'high',
                  horizon_days: null,
                  falsifier: null,
                },
              }),
            },
          ],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify({
                ok: false,
                error: {
                  class: 'reference_lookup_error',
                  message: msg,
                  remediation: 'Check DATABASE_URL, confirm migration 002 applied, and that reference_writer.py was run.',
                },
              }),
            },
          ],
        }
      }
    }
  )
}
