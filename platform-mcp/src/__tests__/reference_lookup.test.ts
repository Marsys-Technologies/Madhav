/**
 * reference_lookup.test.ts — brahmagyan.reference asset tests.
 *
 * Tests:
 * T1: registerReferenceLookup registers tool named 'reference_lookup' on McpServer.
 * T2: FORENSIC assertion — vara_id=1 (native birth day: Sunday) = lord 'Sun', name 'Ravivara'.
 * T3: FORENSIC assertion — nakshatra_id=25 (native Moon: Purva Bhadrapada) = lord 'Jupiter'.
 * T4: Tool returns ok:false with clear remediation on DB error.
 * T5: (live, requires DATABASE_URL) — DB row counts meet floor assertions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Mock pg Pool ───────────────────────────────────────────────────────────────

// We mock 'pg' before importing the tool so Pool is intercepted.
const mockQuery = vi.fn()
vi.mock('pg', () => {
  return {
    Pool: vi.fn().mockImplementation(() => ({
      query: mockQuery,
    })),
  }
})

// Import AFTER mock is in place
const { registerReferenceLookup } = await import('../tools/reference_lookup.js')

// ── Mock McpServer ─────────────────────────────────────────────────────────────

function createMockServer() {
  const registered: Record<string, unknown> = {}
  const toolHandlers: Record<string, (input: unknown) => Promise<unknown>> = {}
  return {
    server: {
      tool: vi.fn((name: string, _desc: string, _schema: unknown, handler: (input: unknown) => Promise<unknown>) => {
        registered[name] = true
        toolHandlers[name] = handler
      }),
    } as unknown as McpServer,
    registered,
    toolHandlers,
  }
}

const MOCK_PRINCIPAL: Principal = { user_uid: 'test-uid', key_id: 'test-key' }

// ── T1: Tool registration ──────────────────────────────────────────────────────

describe('T1 — registerReferenceLookup', () => {
  it('registers tool named reference_lookup', () => {
    const { server, registered } = createMockServer()
    registerReferenceLookup(server, () => MOCK_PRINCIPAL)
    expect(registered['reference_lookup']).toBe(true)
  })
})

// ── T2: FORENSIC — vara_id=1 (Sunday, native birth weekday) ───────────────────

describe('T2 — FORENSIC vara assertion (native birth: Sunday = vara_id 1)', () => {
  beforeEach(() => {
    vi.stubEnv('DATABASE_URL', 'postgresql://mock/db')
    mockQuery.mockResolvedValue({
      rows: [{
        id: 1,
        vara_id: 1,
        name_sanskrit: 'Ravivara',
        name_english: 'Sunday',
        lord: 'Sun',
        color: 'red',
        rahu_kalam_part: 8,
        yamagandam_part: 5,
        gulika_part: 7,
        source_citation: 'VS; MC §1; DP (Drik Panchang) published tables',
      }],
    })
  })

  it('returns lord=Sun and name_sanskrit=Ravivara for vara_id=1', async () => {
    const { server, toolHandlers } = createMockServer()
    registerReferenceLookup(server, () => MOCK_PRINCIPAL)
    const handler = toolHandlers['reference_lookup']
    expect(handler).toBeDefined()

    const result = await handler({ table: 'vara_attrs', key: 1 }) as { content: Array<{ text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.ok).toBe(true)
    const row = parsed.result.rows[0]
    expect(row.vara_id).toBe(1)
    expect(row.lord).toBe('Sun')
    expect(row.name_sanskrit).toBe('Ravivara')
    expect(row.source_citation).toBeTruthy()
  })
})

// ── T3: FORENSIC — nakshatra_id=25 (native Moon: Purva Bhadrapada) ─────────────

describe('T3 — FORENSIC nakshatra assertion (native Moon nakshatra_id=25)', () => {
  beforeEach(() => {
    vi.stubEnv('DATABASE_URL', 'postgresql://mock/db')
    mockQuery.mockResolvedValue({
      rows: [{
        id: 25,
        nakshatra_id: 25,
        name: 'Purva Bhadrapada',
        deity: 'Aja Ekapad',
        lord: 'Jupiter',
        source_citation: 'BS §2; MC §3; Parasara Hora Shastra (Vimshottari Dasha chapter)',
      }],
    })
  })

  it('returns lord=Jupiter and deity=Aja Ekapad for nakshatra_id=25', async () => {
    const { server, toolHandlers } = createMockServer()
    registerReferenceLookup(server, () => MOCK_PRINCIPAL)
    const handler = toolHandlers['reference_lookup']

    const result = await handler({ table: 'nakshatra_attrs', key: 25 }) as { content: Array<{ text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.ok).toBe(true)
    const row = parsed.result.rows[0]
    expect(row.nakshatra_id).toBe(25)
    expect(row.lord).toBe('Jupiter')
    expect(row.deity).toBe('Aja Ekapad')
    expect(row.source_citation).toBeTruthy()
  })
})

// ── T4: Error path ────────────────────────────────────────────────────────────

describe('T4 — Error path', () => {
  it('returns ok:false with remediation on DB error', async () => {
    vi.stubEnv('DATABASE_URL', 'postgresql://mock/db')
    mockQuery.mockRejectedValue(new Error('connection refused'))
    const { server, toolHandlers } = createMockServer()
    registerReferenceLookup(server, () => MOCK_PRINCIPAL)
    const handler = toolHandlers['reference_lookup']

    const result = await handler({ table: 'nakshatra_attrs', key: 1 }) as { content: Array<{ text: string }> }
    const parsed = JSON.parse(result.content[0]!.text)
    expect(parsed.ok).toBe(false)
    expect(parsed.error.class).toBe('reference_lookup_error')
    expect(parsed.error.remediation).toContain('migration 002')
  })
})

// ── T5: Live DB smoke (skipped without DATABASE_URL) ─────────────────────────

describe('T5 — Live DB row-count floor assertions (skipped without DATABASE_URL)', () => {
  const DB_URL = process.env['DATABASE_URL']

  it.skipIf(!DB_URL)('nakshatra_attrs ≥ 27 rows, all have source_citation', async () => {
    // Use pg directly for live assertions
    const { Pool } = await import('pg')
    const pool = new Pool({ connectionString: DB_URL })
    try {
      const { rows } = await pool.query('SELECT COUNT(*) AS cnt FROM reference_nakshatra_attrs')
      expect(Number(rows[0]!.cnt)).toBeGreaterThanOrEqual(27)

      const { rows: nullRows } = await pool.query(
        "SELECT COUNT(*) AS cnt FROM reference_nakshatra_attrs WHERE source_citation IS NULL OR source_citation = ''"
      )
      expect(Number(nullRows[0]!.cnt)).toBe(0)

      // FORENSIC: nakshatra_id=25 in DB
      const { rows: forensic } = await pool.query(
        'SELECT * FROM reference_nakshatra_attrs WHERE nakshatra_id = 25'
      )
      expect(forensic.length).toBe(1)
      expect(forensic[0]!.lord).toBe('Jupiter')
      expect(forensic[0]!.deity).toBe('Aja Ekapad')
    } finally {
      await pool.end()
    }
  })

  it.skipIf(!DB_URL)('vara_attrs ≥ 7 rows — FORENSIC: vara_id=1 is Sun/Ravivara', async () => {
    const { Pool } = await import('pg')
    const pool = new Pool({ connectionString: DB_URL })
    try {
      const { rows } = await pool.query('SELECT COUNT(*) AS cnt FROM reference_vara_attrs')
      expect(Number(rows[0]!.cnt)).toBeGreaterThanOrEqual(7)

      const { rows: forensic } = await pool.query(
        'SELECT * FROM reference_vara_attrs WHERE vara_id = 1'
      )
      expect(forensic.length).toBe(1)
      expect(forensic[0]!.lord).toBe('Sun')
      expect(forensic[0]!.name_sanskrit).toBe('Ravivara')
    } finally {
      await pool.end()
    }
  })

  it.skipIf(!DB_URL)('all reference tables meet row-count floors', async () => {
    const { Pool } = await import('pg')
    const pool = new Pool({ connectionString: DB_URL })
    const floors: Record<string, number> = {
      reference_nakshatra_attrs:      27,
      reference_tithi_attrs:          30,
      reference_yoga_attrs:           27,
      reference_karana_attrs:         11,
      reference_vara_attrs:            7,
      reference_sign_attrs:           12,
      reference_hora_cycle:            7,
      reference_combustion_orbs:       7,
      reference_event_quality:        18,
      reference_inauspicious_periods:  7,
    }
    try {
      for (const [table, floor] of Object.entries(floors)) {
        const { rows } = await pool.query(`SELECT COUNT(*) AS cnt FROM ${table}`)
        expect(Number(rows[0]!.cnt), `${table} row count`).toBeGreaterThanOrEqual(floor)
      }
    } finally {
      await pool.end()
    }
  })
})
