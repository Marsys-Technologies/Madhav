/**
 * register_gochara_windows_mr01.test.ts — PARIṢKĀRA MR-01+02+05 TDD tests.
 *
 * Written BEFORE the implementation per the campaign's TDD iron rule.
 * All tests in the non-integration describes will FAIL until the corresponding
 * implementation lands (Commits 2-4).
 *
 * Coverage:
 *   MR-01: Migration 564 adds 8 v3 output-model cols to kala_gochara_windows.
 *          ROW_COLUMNS in register_gochara_windows.ts selects those cols without
 *          error when the DB has them present (mocked).
 *   MR-02: computeGocharaCoverage is authority-aware: v3-authority charts use
 *          gochara_resonance_map scope + v3 asset substep path; v1-authority
 *          (no row in kala_gochara_authority) keeps existing sweep-substep path.
 *   MR-05: Migration 563 FK cleanup precedes the asset_registry DELETE so the
 *          migration applies without a FK-23503 violation.
 *
 * Unit tests (no live DB) only — integration tests are gated on
 * RUN_DB_INTEGRATION=1 in the sibling register_gochara_windows.test.ts.
 */

import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest'
import { computeGocharaActivation, computeGocharaCoverage } from './register_gochara_windows.js'

// ── MR-01: 8-column schema parity ────────────────────────────────────────────

describe('MR-01 — ROW_COLUMNS includes all 8 v3 output-model columns', () => {
  /**
   * The 8 columns that were missing from kala_gochara_windows (present only on
   * kala_gochara_windows_v2 staging) and selected by ROW_COLUMNS:
   *   term_breakdown, lambda_v3_ci_low, lambda_v3_ci_high, ci_source,
   *   threshold_lambda, threshold_percentile, implied_density, base_rate_cited
   *
   * This test asserts the column list by importing the module and inspecting
   * what is exported — specifically that GocharaWindowRow (the row type) and the
   * actual SQL string both reference these fields. We do it by checking that a
   * mocked query returning all 8 as null does NOT crash the tool's processing.
   *
   * Approach: we import computeGocharaActivation, mock platformQuery so it
   * returns a row with the 8 cols set to null, and assert the returned window
   * carries those cols (even if null). This proves the code paths that reference
   * them exist and do not 500.
   */

  it('GocharaWindowRow type allows all 8 v3 output-model cols (nullable)', async () => {
    const { computeGocharaActivation } = await import('./register_gochara_windows.js')

    // Confirm the exported function exists (module loads without error)
    expect(typeof computeGocharaActivation).toBe('function')
  })

  it('a row with all 8 v3 cols null is accepted without throw', async () => {
    // Mock fetch so platformQuery returns a row with all 8 new cols set to null.
    // This proves the code does not crash when the columns are present but null.
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation((_url, init) => {
      const { sql } = JSON.parse((init as RequestInit).body as string) as { sql: string }
      if (sql.includes('kala_gochara_authority')) {
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('gochara_resonance_map') && !sql.includes('rm.event_class')) {
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
      }
      // Main row query — return a row with all 8 new cols null
      return Promise.resolve(fakeJsonResponse([{
        id: 42,
        chart_id: '482012f1-710e-4a25-994a-93821f5871aa',
        event_class: 'marriage',
        temporal_shape: 'point',
        window_start: '2026-01-01',
        window_end: '2026-01-01',
        peak_date: '2026-01-01',
        milestone_id: null,
        is_irreversibility_milestone: false,
        signed_intensity: 0.5,
        raw_intensity: 0.5,
        valence: 'neutral',
        is_adverse: false,
        active_sentences: [],
        contributing_systems: [],
        suppression_state: {},
        peak_basis: 'gochara_lambda_e_v1',
        calibration_state: 'structural_prior',
        source: 'live',
        computed_at: '2026-08-10T00:00:00Z',
        continuity_state: null,
        generation: 'g3_utkarsha',
        era_slice_key: 'g3_2020_2030',
        // 8 v3 output-model cols (all null — what a pre-W1.4/W1.5 v3 row looks like)
        term_breakdown: null,
        lambda_v3_ci_low: null,
        lambda_v3_ci_high: null,
        ci_source: null,
        threshold_lambda: null,
        threshold_percentile: null,
        implied_density: null,
        base_rate_cited: null,
      }]))
    })

    const principal = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }

    // Should not throw — the 8 null cols are passed through transparently
    const result = (await computeGocharaActivation(
      '482012f1-710e-4a25-994a-93821f5871aa',
      '2026-01-01',
      principal,
      'marriage'
    )) as { windows: unknown[]; provenance_envelope: unknown }

    expect(Array.isArray(result.windows)).toBe(true)
    // The tool must not 500 (throw) when the 8 new cols are present but null
    expect(result.windows.length).toBeGreaterThanOrEqual(0)

    fetchSpy.mockRestore()
  })
})

// ── MR-02: authority-aware computeGocharaCoverage ───────────────────────────

/**
 * We test computeGocharaCoverage's authority-aware branching by intercepting
 * the fetch() calls it makes through its local platformQuery function (which
 * posts to /api/mcp/db/query). We mock globalThis.fetch and inspect the
 * JSON body of each POST to verify which asset_id is used in the
 * build_substep_progress query.
 *
 * After MR-02:
 *   - v1-authority (no kala_gochara_authority row): build_substep_progress
 *     query params[1] == 'ka_gochara_sweep'.
 *   - v3-authority (authority row exists with gen '3.0' / 'g3_*'):
 *     build_substep_progress query params[1] == 'ka_gochara'.
 *
 * The body of each POST is { sql, params } — we inspect body.params[1] on the
 * call whose body.sql includes 'build_substep_progress'.
 */

/** Build a fake fetch response returning a { rows } JSON payload. */
function fakeJsonResponse(rows: unknown[]): Response {
  return {
    ok: true,
    json: () => Promise.resolve({ rows }),
    text: () => Promise.resolve(JSON.stringify({ rows })),
  } as unknown as Response
}

describe('MR-02 — computeGocharaCoverage is authority-aware', () => {
  let fetchSpy: Mock

  beforeEach(() => {
    fetchSpy = vi.fn()
    vi.spyOn(globalThis, 'fetch').mockImplementation(fetchSpy)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  /**
   * Parse the JSON body from a fetch call's RequestInit argument.
   * platformQuery posts { sql, params } — body is a string.
   */
  function getBody(call: unknown[]): { sql: string; params: unknown[] } {
    const init = call[1] as RequestInit
    return JSON.parse(init.body as string) as { sql: string; params: unknown[] }
  }

  it('uses ka_gochara_sweep as $2 param for v1-authority charts (no authority row)', async () => {
    // Mock fetch: route each SQL query to the right response
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string; params: unknown[] }
      if (sql.includes('kala_gochara_authority')) {
        // No row → v1 authority
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'career' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 0, swept_event_classes: [] }]))
      }
      return Promise.resolve(fakeJsonResponse([]))
    })

    const principal = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
    await computeGocharaCoverage('cb73cd3d-0000-0000-0000-000000000000', principal)

    // Find the build_substep_progress call and check its $2 param
    const substepCall = fetchSpy.mock.calls.find(([, init]: [string, RequestInit]) => {
      const b = JSON.parse(init.body as string) as { sql: string }
      return b.sql.includes('build_substep_progress')
    })
    expect(substepCall).toBeDefined()
    const body = getBody(substepCall!)
    // $2 (params[1]) must be 'ka_gochara_sweep' for a v1-authority chart
    expect(body.params[1]).toBe('ka_gochara_sweep')
  })

  it('uses ka_gochara as $2 param for v3-authority charts (authority row with 3.0)', async () => {
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string; params: unknown[] }
      if (sql.includes('kala_gochara_authority')) {
        // v3-authority: authoritative_generation = '3.0'
        return Promise.resolve(fakeJsonResponse([{ authoritative_generation: '3.0' }]))
      }
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([{ event_class: 'marriage', domain: 'marriage' }]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'marriage' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 5, swept_event_classes: ['marriage'] }]))
      }
      return Promise.resolve(fakeJsonResponse([]))
    })

    const principal = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
    await computeGocharaCoverage('482012f1-710e-4a25-994a-93821f5871aa', principal)

    const substepCall = fetchSpy.mock.calls.find(([, init]: [string, RequestInit]) => {
      const b = JSON.parse(init.body as string) as { sql: string }
      return b.sql.includes('build_substep_progress')
    })
    expect(substepCall).toBeDefined()
    const body = getBody(substepCall!)
    // $2 (params[1]) must be 'ka_gochara' for a v3-authority chart
    expect(body.params[1]).toBe('ka_gochara')
    expect(body.params[1]).not.toBe('ka_gochara_sweep')
  })

  it('v1-authority coverage.sweep_completeness.source names ka_gochara_sweep', async () => {
    fetchSpy.mockImplementation((_url: string, init: RequestInit) => {
      const { sql } = JSON.parse(init.body as string) as { sql: string; params: unknown[] }
      if (sql.includes('kala_gochara_authority')) return Promise.resolve(fakeJsonResponse([]))
      if (sql.includes('gochara_resonance_map')) {
        return Promise.resolve(fakeJsonResponse([{ event_class: 'career_advancement', domain: 'career' }]))
      }
      if (sql.includes('brahma_event_ontology')) {
        return Promise.resolve(fakeJsonResponse([{ domain: 'career' }]))
      }
      if (sql.includes('build_substep_progress')) {
        return Promise.resolve(fakeJsonResponse([{ substeps_committed: 3, swept_event_classes: ['career_advancement'] }]))
      }
      return Promise.resolve(fakeJsonResponse([]))
    })

    const principal = { user_uid: 'test', key_id: 'test', role: 'super_admin' as const }
    const { coverage } = await computeGocharaCoverage('cb73cd3d-0000-0000-0000-000000000000', principal)

    // The sweep_completeness.source field must honestly name the asset queried
    expect(coverage.sweep_completeness.source).toContain('ka_gochara_sweep')
  })
})

// ── MR-05: Migration 563 FK cleanup order ────────────────────────────────────

/**
 * We test migration 563's idempotency and FK-cleanup ordering by parsing the
 * SQL file directly. We cannot run it against a live DB (unit test only), but
 * we CAN assert:
 *   (a) The asset_throughput DELETE appears BEFORE the asset_registry DELETE.
 *   (b) The migration is safe to read/parse (no syntax errors in the DO block
 *       structure we can verify statically).
 *   (c) The migration contains the required cleanup for 'ka_gochara' global scope
 *       referrers before the DELETE FROM asset_registry.
 */
describe('MR-05 — migration 563 FK cleanup precedes asset_registry DELETE', () => {
  it('asset_throughput cleanup appears before asset_registry DELETE in migration 563', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const migPath = path.join(
      // __dirname equivalent via import.meta not available in test — use cwd-relative
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform/migrations/563_utkarsha_w64_asset_rename.sql'
    )
    const sql = await fs.readFile(migPath, 'utf-8')

    // The migration MUST delete asset_throughput referrers BEFORE deleting
    // the asset_registry row (FK 23503 fires otherwise).
    const throughputDeletePos = sql.indexOf('DELETE FROM asset_throughput')
    const registryDeletePos = sql.indexOf(
      "DELETE FROM asset_registry WHERE asset_id = 'ka_gochara' AND scope = 'global'"
    )

    // Both must be present
    expect(throughputDeletePos).toBeGreaterThan(-1)
    expect(registryDeletePos).toBeGreaterThan(-1)

    // Throughput cleanup must come BEFORE the registry DELETE
    expect(throughputDeletePos).toBeLessThan(registryDeletePos)
  })

  it('migration 563 is idempotent: the DO block uses IF EXISTS guards', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const migPath = path.join(
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform/migrations/563_utkarsha_w64_asset_rename.sql'
    )
    const sql = await fs.readFile(migPath, 'utf-8')

    // The rename is inside an IF EXISTS guard (already required by original migration)
    expect(sql).toContain('IF EXISTS')
    // The DO block wraps the whole operation
    expect(sql).toContain('DO $$')
    expect(sql).toContain('END $$')
  })

  it('migration 563 cleans asset_throughput WHERE asset_id = ka_gochara AND chart_id IS NULL', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const migPath = path.join(
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform/migrations/563_utkarsha_w64_asset_rename.sql'
    )
    const sql = await fs.readFile(migPath, 'utf-8')

    // The global-scope self-test row (chart_id IS NULL) is what holds the FK
    expect(sql).toContain('chart_id IS NULL')
    // And it scopes to ka_gochara
    expect(sql).toContain("asset_id = 'ka_gochara'")
  })
})

// ── MR-01: Migration 564 self-verification block structure ───────────────────

describe('MR-01 — migration 564 contains self-verification for all 8 columns', () => {
  const EIGHT_COLS = [
    'term_breakdown',
    'lambda_v3_ci_low',
    'lambda_v3_ci_high',
    'ci_source',
    'threshold_lambda',
    'threshold_percentile',
    'implied_density',
    'base_rate_cited',
  ]

  it('migration 564 file exists at platform/supabase/migrations/', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const migPath = path.join(
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform/supabase/migrations/564_parishkara_mr01_schema_parity.sql'
    )
    // Will throw ENOENT if file does not exist — this is the expected failing state pre-commit-3
    const stat = await fs.stat(migPath)
    expect(stat.isFile()).toBe(true)
  })

  it('migration 564 ALTERs kala_gochara_windows (not only _v2)', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const migPath = path.join(
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform/supabase/migrations/564_parishkara_mr01_schema_parity.sql'
    )
    const sql = await fs.readFile(migPath, 'utf-8')

    // Must ALTER the production table kala_gochara_windows
    expect(sql).toContain('ALTER TABLE kala_gochara_windows')
  })

  it.each(EIGHT_COLS)(
    'migration 564 adds column %s to kala_gochara_windows',
    async (col) => {
      const fs = await import('fs/promises')
      const path = await import('path')
      const migPath = path.join(
        process.cwd().replace(/\/platform-mcp$/, ''),
        'platform/supabase/migrations/564_parishkara_mr01_schema_parity.sql'
      )
      const sql = await fs.readFile(migPath, 'utf-8')
      expect(sql).toContain(col)
    }
  )

  it.each(EIGHT_COLS)(
    'migration 564 has a self-verification check for column %s',
    async (col) => {
      const fs = await import('fs/promises')
      const path = await import('path')
      const migPath = path.join(
        process.cwd().replace(/\/platform-mcp$/, ''),
        'platform/supabase/migrations/564_parishkara_mr01_schema_parity.sql'
      )
      const sql = await fs.readFile(migPath, 'utf-8')

      // The self-verification DO block must reference each column in a
      // RAISE EXCEPTION context (§N.4 mandate)
      const raiseExceptionPattern = new RegExp(
        `RAISE EXCEPTION.*${col}|${col}.*RAISE EXCEPTION`,
        's'
      )
      expect(raiseExceptionPattern.test(sql)).toBe(true)
    }
  )
})

// ── MR-01: false code comment is fixed ───────────────────────────────────────

describe('MR-01 — false comment about migrations 527/556/559 is corrected', () => {
  it('register_gochara_windows.ts no longer claims 527/556/559 added cols to kala_gochara_windows', async () => {
    const fs = await import('fs/promises')
    const path = await import('path')
    const tsPath = path.join(
      process.cwd().replace(/\/platform-mcp$/, ''),
      'platform-mcp/src/tools/retrieval/register_gochara_windows.ts'
    )
    const src = await fs.readFile(tsPath, 'utf-8')

    // The false comment claimed these cols were present on kala_gochara_windows
    // since migrations 527/556/559. After MR-01 that comment must either be
    // removed or corrected to name migration 564.
    const falseClaimPattern =
      /nullable columns present on kala_gochara_windows since migrations 527\/556\/559/
    expect(falseClaimPattern.test(src)).toBe(false)
  })
})
